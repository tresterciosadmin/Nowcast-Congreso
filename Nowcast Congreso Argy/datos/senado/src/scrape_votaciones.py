"""Scraper de votaciones nominales del Senado (senado.gob.ar/votaciones/actas).

Objetivo: tapar el hueco de la canónica **Senado 2015-2023** (y opcionalmente
re-scrapear 2024+ para resolver el "SIN BLOQUE" de argentinadatos).

Fuente oficial, dos niveles:
  • LISTADO por año: https://www.senado.gob.ar/votaciones/actas
    (formulario POST `busqueda_actas[anio]`; devuelve TODAS las actas del año
    en una sola tabla, la paginación es client-side).
  • DETALLE por acta: https://www.senado.gob.ar/votaciones/detalleActa/<id>
    (voto nominal por senador CON bloque y provincia, más totales,
    tipo de mayoría, resultado y expediente).

Salida (contrato estable, esquema canónico schema_version=1):
  data/clean/senado_actas.parquet   (una fila por acta)
  data/clean/senado_votos.parquet   (una fila por senador x acta)
  acta_id = "senado:<detalle_id>"   fuente = "senado"

Uso (PC con internet; el sandbox de Claude no llega a senado.gob.ar):
  python scrape_votaciones.py                 # años 2015..2023
  python scrape_votaciones.py 2018 2020       # rango de años
  python scrape_votaciones.py --ids 900 2100  # plan B: barrer detalleActa/<id>
                                              # directo (si el form cambiara)
Variables de entorno:
  OUT=/dir      salida parquet   (default: datos/senado/data/clean)
  CACHE=/dir    caché HTML crudo (default: Archivos_Borrar/senado_html)
  SLEEP=0.5     pausa entre requests (cortesía con el servidor)
  REFRESH=1     ignora la caché y re-descarga

Las 4 directivas de resiliencia del proyecto:
  - errores específicos (no `except: pass` ciego),
  - reintentos con backoff en red,
  - parsing DEFENSIVO: la tabla nominal se encuentra por la FIRMA de sus
    encabezados ({SENADOR, BLOQUE, PROVINCIA}), no por posición; campos
    faltantes quedan None y se sigue,
  - logging estructurado.

Control de calidad incorporado: por cada acta se comparan las filas nominales
contra los totales publicados (afirmativos+negativos+abstenciones); si no
cuadran se loguea WARNING (no se aborta). Los AUSENTES pueden no estar listados
nominalmente en actas viejas: se preserva el total en n_ausentes.

LIMITACIÓN CONOCIDA (verificada en vivo, corrida 2018 del 2026-07-01): el campo
`bloque` del detalle NO es contemporáneo al voto; el sitio pinta el ÚLTIMO
bloque conocido del senador (ej.: "FRENTE DE TODOS" en actas de 2018, bloque
que nació en 2019). Sirve para resolución de entidades, NO para baseline de
disciplina por bloque. El bloque time-aware se resuelve aparte
(padrón histórico -> bloque por fecha), igual que hizo argentinadatos
con Diputados.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    _HAS_TENACITY = True
except ImportError:  # tenacity es opcional; sin ella no hay reintentos
    _HAS_TENACITY = False

logger = logging.getLogger("senado.votaciones")

SV = 1
BASE = "https://www.senado.gob.ar"
LISTADO_URL = f"{BASE}/votaciones/actas"
DETALLE_URL = f"{BASE}/votaciones/detalleActa/{{id}}"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/senado)"}
TIMEOUT = 60

_RETRYABLE = (requests.ConnectionError, requests.Timeout, requests.HTTPError)


def _norm(s: str) -> str:
    """MAYÚSCULAS sin tildes ni espacios repetidos (para comparar headers)."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def _voto(x: str) -> str:
    v = _norm(x)
    if "AFIRMATIV" in v or v == "SI":
        return "AFIRMATIVO"
    if "NEGATIV" in v or v == "NO":
        return "NEGATIVO"
    if "ABSTEN" in v:
        return "ABSTENCION"
    return "AUSENTE"  # incluye 'ausente', 'presidente', 'no votó', etc.


# ---------------------------------------------------------------- red / caché
def _fetch(session: requests.Session, url: str, cache_file: Path,
           method: str = "GET", data: Optional[dict] = None) -> str:
    if cache_file.exists() and not os.environ.get("REFRESH"):
        return cache_file.read_text(encoding="utf-8")

    def _do() -> str:
        r = session.request(method, url, data=data, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text

    if _HAS_TENACITY:
        _do = retry(
            retry=retry_if_exception_type(_RETRYABLE),
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=2, max=30),
            reraise=True,
        )(_do)
    html = _do()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")
    time.sleep(float(os.environ.get("SLEEP", "0.5")))
    return html


def _resultado_lista(txt: str) -> Optional[str]:
    """La celda "Resultado" del listado concatena signo + detalle
    ("POSITIVO AFIRMATIVO", "NEGATIVO CANCELADA LEV.VOT."). Normaliza:
    AFIRMATIVO / NEGATIVO a secas, o "NEGATIVO - <detalle>" si hay más info."""
    t = _norm(txt)
    if not t:
        return None
    parts = t.split()
    signo = {"POSITIVO": "AFIRMATIVO", "NEGATIVO": "NEGATIVO"}.get(parts[0])
    if signo is None:
        return t
    resto = " ".join(parts[1:])
    if not resto or resto == signo:
        return signo
    return f"{signo} - {resto}"


# ------------------------------------------------------------------- listado
def _form_payload(soup: BeautifulSoup, anio: int) -> tuple[str, dict]:
    """Encuentra el form del buscador y arma el POST con TODOS sus campos
    (incluye hidden/_token si los hubiera), pisando solo el año."""
    anio_field = soup.find(["select", "input"],
                           attrs={"name": re.compile(r"anio", re.I)})
    if anio_field is None:
        raise ValueError("no encontré el campo 'anio' en el formulario del listado")
    form = anio_field.find_parent("form")
    if form is None:
        raise ValueError("el campo 'anio' no está dentro de un <form>")
    payload: dict = {}
    for el in form.find_all(["input", "select", "textarea"]):
        name = el.get("name")
        if not name:
            continue
        if el.name == "select":
            opt = el.find("option", selected=True) or el.find("option")
            payload[name] = opt.get("value", "") if opt else ""
        else:
            payload[name] = el.get("value", "")
    payload[anio_field.get("name")] = str(anio)
    action = urljoin(LISTADO_URL, form.get("action") or LISTADO_URL)
    return action, payload


def _parse_listado(html: str) -> list[dict]:
    """Filas del listado anual. Tabla ubicada por firma de encabezados."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    for table in soup.find_all("table"):
        heads = {_norm(th.get_text()) for th in table.find_all("th")}
        if not ({"FECHA DE SESION", "TITULO"} <= heads or
                any("ACTA" in h for h in heads) and "TITULO" in heads):
            continue
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue
            texts = [" ".join(td.get_text(" ", strip=True).split()) for td in tds]
            det = tr.find("a", href=re.compile(r"detalleActa/(\d+)"))
            pdf = tr.find("a", href=re.compile(r"verActaVotacion/(\d+)"))
            m_fecha = re.search(r"\d{2}/\d{2}/\d{4}", texts[0])
            row = {
                "detalle_id": (re.search(r"detalleActa/(\d+)", det["href"]).group(1)
                               if det else None),
                "pdf_id": (re.search(r"verActaVotacion/(\d+)", pdf["href"]).group(1)
                           if pdf else None),
                "fecha_lista": m_fecha.group(0) if m_fecha else None,
                "nro_acta_lista": texts[1] or None,
                "titulo_lista": texts[2] or None,
                "tipo_lista": texts[3] or None,
                "resultado_lista": texts[4] or None,
                "mayoria_lista": texts[6] if len(texts) > 6 and texts[6] else None,
            }
            if row["detalle_id"] or row["pdf_id"]:
                out.append(row)
        if out:
            break
    return out


def listar_anio(session: requests.Session, anio: int, cache: Path) -> list[dict]:
    """POST del buscador para un año. Verifica que las fechas correspondan."""
    base_html = _fetch(session, LISTADO_URL, cache / "form.html")
    action, payload = _form_payload(BeautifulSoup(base_html, "html.parser"), anio)
    html = _fetch(session, action, cache / f"listado_{anio}.html",
                  method="POST", data=payload)
    rows = _parse_listado(html)
    anios_vistos = {r["fecha_lista"][-4:] for r in rows if r["fecha_lista"]}
    if rows and anios_vistos and str(anio) not in anios_vistos:
        # el form no filtró (¿cambió el sitio?): no confiar en este listado
        raise ValueError(
            f"listado {anio}: el form devolvió años {sorted(anios_vistos)}; "
            "revisar el formulario o usar el plan B --ids")
    logger.info("listado %s: %d actas", anio, len(rows))
    return rows


# ------------------------------------------------------------------- detalle
_RE_TOTAL = re.compile(
    r"(\d+)\s*(AFIRMATIVOS?|NEGATIVOS?|ABSTENCION(?:ES)?|AUSENTES?)", re.I)


def parse_detalle(html: str, detalle_id: str) -> tuple[dict, list[dict]]:
    """Devuelve (acta, votos) del detalle nominal. Tolerante a faltantes."""
    soup = BeautifulSoup(html, "html.parser")
    text = _norm(soup.get_text(" ", strip=True))

    m = re.search(r"ACTA NRO[.:]?\s*(\d+)", text)
    nro_acta = int(m.group(1)) if m else None
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
    fecha = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None

    tipo_mayoria = next((t for t in
                         ("DOS TERCIOS", "MAYORIA ABSOLUTA", "MAYORIA ESPECIAL",
                          "SIMPLE") if t in text), None)
    resultado = next((t for t in
                      ("AFIRMATIVO", "NEGATIVO", "EMPATE", "LEVANTADA")
                      if re.search(rf"\b{t}\b", text)), None)
    instancia = ("EN PARTICULAR" if "EN PARTICULAR" in text
                 else "EN GENERAL" if "EN GENERAL" in text else None)

    totales = {}
    for n, k in _RE_TOTAL.findall(text):
        k = _norm(k)
        key = ("n_afirmativos" if k.startswith("AFIRMATIV") else
               "n_negativos" if k.startswith("NEGATIV") else
               "n_abstenciones" if k.startswith("ABSTEN") else "n_ausentes")
        totales.setdefault(key, int(n))

    exp = soup.find("a", href=re.compile(r"/verExp/"))
    expediente = " ".join(exp.get_text(strip=True).split()) if exp else None

    # título: primer bloque de texto significativo después de "Acta Nro"
    titulo = None
    h_acta = soup.find(string=re.compile(r"Acta\s+Nro", re.I))
    if h_acta:
        for sib in h_acta.parent.find_all_next(["p", "div", "h2", "h3", "a"]):
            t = " ".join(sib.get_text(" ", strip=True).split())
            if len(t) > 12 and "ACTA NRO" not in _norm(t):
                titulo = t
                break

    votos: list[dict] = []
    for table in soup.find_all("table"):
        heads = {_norm(th.get_text()) for th in table.find_all("th")}
        if not {"SENADOR", "BLOQUE", "PROVINCIA"} <= heads:
            continue
        cols = [_norm(th.get_text()) for th in table.find_all("th")]
        i_sen, i_blo = cols.index("SENADOR"), cols.index("BLOQUE")
        i_pro = cols.index("PROVINCIA")
        i_vot = next((i for i, c in enumerate(cols) if "VOT" in c), len(cols) - 1)
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(i_sen, i_blo, i_pro, i_vot):
                continue
            nombre = " ".join(tds[i_sen].get_text(" ", strip=True).split())
            if not nombre:
                continue
            votos.append({
                "schema_version": SV,
                "acta_id": f"senado:{detalle_id}",
                "legislador_id": None,
                "legislador_nombre": nombre,
                "bloque": " ".join(tds[i_blo].get_text(" ", strip=True).split())
                          or "SIN BLOQUE",
                "distrito": " ".join(tds[i_pro].get_text(" ", strip=True).split())
                            or None,
                "voto": _voto(tds[i_vot].get_text(" ", strip=True)),
                "fuente": "senado",
            })
        break

    # instancia (EN GENERAL / EN PARTICULAR) va plegada al título: el esquema
    # canónico tiene additionalProperties=false y una columna extra rompe build.
    titulo = titulo or "(sin titulo)"
    if instancia and _norm(instancia) not in _norm(titulo):
        titulo = f"{titulo} [{instancia}]"
    acta = {
        "schema_version": SV,
        "acta_id": f"senado:{detalle_id}",
        "camara": "senado",
        "fecha": fecha,
        "periodo": None,
        "titulo": titulo,
        "expediente": expediente,
        "tipo_mayoria": tipo_mayoria,
        "resultado": resultado,
        **{k: totales.get(k) for k in
           ("n_afirmativos", "n_negativos", "n_abstenciones", "n_ausentes")},
        "fuente": "senado",
    }

    # control de calidad: nominal vs totales publicados
    emitidos = sum(totales.get(k) or 0 for k in
                   ("n_afirmativos", "n_negativos", "n_abstenciones"))
    nominales = sum(1 for v in votos if v["voto"] != "AUSENTE")
    if emitidos and nominales and emitidos != nominales:
        logger.warning("acta senado:%s: nominal=%d != totales=%d",
                       detalle_id, nominales, emitidos)
    return acta, votos


# ---------------------------------------------------------------------- main
def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("anios", nargs="*", type=int, default=[2015, 2023],
                    help="año inicial [y final] (default 2015 2023)")
    ap.add_argument("--ids", nargs=2, type=int, metavar=("DESDE", "HASTA"),
                    help="plan B: barrer detalleActa/<id> por rango de ids")
    args = ap.parse_args()
    y0 = args.anios[0] if args.anios else 2015
    y1 = args.anios[1] if len(args.anios) > 1 else (2023 if not args.anios else y0)

    root = Path(__file__).resolve()
    repo = root.parents[3]
    out = Path(os.environ.get("OUT", root.parents[1] / "data" / "clean"))
    cache = Path(os.environ.get("CACHE",
                                repo / "datos" / "Archivos_Borrar" / "senado_html"))
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    actas_rows, votos_rows, fallidas = [], [], []

    meta: dict[str, dict] = {}  # detalle_id -> fila del listado (metadata)
    if args.ids:  # ---- plan B: barrido directo por id
        ids = [str(i) for i in range(args.ids[0], args.ids[1] + 1)]
    else:  # ---- plan A: listado oficial por año
        ids = []
        for anio in range(y0, y1 + 1):
            try:
                for r in listar_anio(session, anio, cache):
                    if r["detalle_id"]:
                        ids.append(r["detalle_id"])
                        meta.setdefault(r["detalle_id"], r)
            except (ValueError, requests.RequestException) as e:
                logger.error("listado %s falló: %s", anio, e)
                fallidas.append(f"listado:{anio}")
        ids = list(dict.fromkeys(ids))  # dedup preservando orden

    logger.info("actas a bajar: %d", len(ids))
    for i, did in enumerate(ids, 1):
        try:
            html = _fetch(session, DETALLE_URL.format(id=did),
                          cache / "detalle" / f"{did}.html")
            acta, votos = parse_detalle(html, did)
            # el listado es la fuente confiable de resultado/mayoría: en el
            # detalle esas palabras se confunden con la tabla nominal.
            m = meta.get(did)
            if m:
                if m.get("resultado_lista"):
                    acta["resultado"] = _resultado_lista(m["resultado_lista"])
                if m.get("mayoria_lista"):
                    acta["tipo_mayoria"] = _norm(m["mayoria_lista"])
            if args.ids and acta["fecha"] and not (y0 <= int(acta["fecha"][:4]) <= y1):
                continue  # en plan B filtramos por año acá
            actas_rows.append(acta)
            votos_rows.extend(votos)
            if not votos:
                logger.warning("acta senado:%s sin filas nominales "
                               "(¿a mano alzada?)", did)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                continue  # ids salteados: normal en plan B
            logger.error("detalle %s: %s", did, e)
            fallidas.append(did)
        except (requests.RequestException, ValueError) as e:
            logger.error("detalle %s: %s", did, e)
            fallidas.append(did)
        if i % 25 == 0:
            logger.info("progreso: %d/%d", i, len(ids))

    actas = pd.DataFrame(actas_rows)
    votos = pd.DataFrame(votos_rows)
    if not actas.empty:
        for c in ("n_afirmativos", "n_negativos", "n_abstenciones", "n_ausentes"):
            actas[c] = pd.to_numeric(actas[c], errors="coerce").astype("Int64")
        actas.to_parquet(out / "senado_actas.parquet", index=False)
        votos.to_parquet(out / "senado_votos.parquet", index=False)
    print(f"OK actas={len(actas)} votos={len(votos)} fallidas={len(fallidas)} -> {out}")
    if not actas.empty:
        print("  por año:", actas["fecha"].str[:4].value_counts().sort_index().to_dict())
        print("  sin nominal:", int((~actas["acta_id"].isin(votos["acta_id"])).sum())
              if not votos.empty else len(actas))
    if fallidas:
        print("  FALLIDAS (reintentar):", fallidas[:20])


if __name__ == "__main__":
    main()
