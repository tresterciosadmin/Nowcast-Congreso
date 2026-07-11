"""BOT DIARIO — adaptador DIPUTADOS: Trámite Parlamentario (TP).

El TP es el diario oficial de ingresos de Diputados: cada número publica los
proyectos presentados con la LISTA COMPLETA DE FIRMANTES (autor + cofirmantes
— el dato que el CKAN no da), tipo, sumario, expediente (link al PDF) y GIROS
a comisiones. Numeración secuencial por PERÍODO parlamentario (144 = mar-2026
a feb-2027; histórico disponible desde el 137).

Fuente (estructura verificada sobre muestras reales, 11-07-2026):
  índice:  hcdn.gob.ar/secparl/dsecretaria/s_t_parlamentario/tramites-parlamentarios.html
  por TP:  .../tp.html?periodo=<P>&numero=<NNN>
  Markup: h1.tituloSeccion (nº + fecha) · h3.titTP (sección: DIPUTADOS /
  PODER EJECUTIVO / SENADO…) · un <p> por proyecto con firmantes en <strong>,
  expediente como <a>(PDF) y giros en <strong> después del link.

Estado local:  data/estado_bot.json  {"tp_diputados": {"periodo": P, "numero": N}}
Salida:        data/clean/tp_entradas.parquet (append + dedup por expediente+tp)
  columnas: periodo, tp_numero, fecha, seccion, expediente, firmantes,
            n_firmantes, tipo, sumario, giros, pdf_url

Correr:  python datos/bot_recoleccion/src/tp_diputados.py            # lo nuevo
         python datos/bot_recoleccion/src/tp_diputados.py 87 144     # un TP puntual
Tests:   python datos/bot_recoleccion/tests/test_tp.py

Las 4 directivas de resiliencia aplican (ver dae_senado.py).
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False

logger = logging.getLogger("bot.tp_diputados")

BASE = "https://www.hcdn.gob.ar/secparl/dsecretaria/s_t_parlamentario/"
INDICE = BASE + "tramites-parlamentarios.html"
TP_URL = BASE + "tp.html?periodo={p}&numero={n:03d}"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/bot_recoleccion)"}
TIMEOUT = 60
_RETRYABLE = (requests.ConnectionError, requests.Timeout, requests.HTTPError)

DATA = Path(__file__).resolve().parents[1] / "data"
ESTADO = DATA / "estado_bot.json"
SALIDA = DATA / "clean" / "tp_entradas.parquet"

MESES = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
         "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10,
         "NOVIEMBRE": 11, "DICIEMBRE": 12}
RE_EXP = re.compile(r"^\d{1,4}-[A-Z]{1,3}-\d{4}$")


def _pedir(session: requests.Session, url: str) -> str:
    def _do() -> str:
        r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    if _HAS_TENACITY:
        _do = retry(retry=retry_if_exception_type(_RETRYABLE), stop=stop_after_attempt(4),
                    wait=wait_exponential(multiplier=2, max=30), reraise=True)(_do)
    html = _do()
    time.sleep(float(os.environ.get("SLEEP", "0.5")))
    return html


# ------------------------------------------------------------------- parsing
def _fecha_iso(txt: str) -> Optional[str]:
    m = re.search(r"(\d{1,2})\s+DE\s+([A-ZÁÉÍÓÚÑ]+)\s+DE\s+(\d{4})", txt.upper())
    if not m or m.group(2) not in MESES:
        return None
    return f"{m.group(3)}-{MESES[m.group(2)]:02d}-{int(m.group(1)):02d}"


def _limpiar(s: str) -> str:
    return " ".join(str(s).split())


def _firmantes(strongs_txt: str) -> list[str]:
    """'RUIZ, YAMILA; VANCSIK, DANIEL Y HERRERA AHUAD, OSCAR A.:' -> lista."""
    s = _limpiar(strongs_txt).rstrip(":").strip()
    partes = re.split(r";", s)
    out: list[str] = []
    for p in partes:
        # el último puede venir como 'X Y APELLIDO, NOMBRE' -> separar por ' Y ' solo
        # si ambos lados parecen 'APELLIDO, NOMBRE' (defensivo con nombres con Y)
        sub = re.split(r"\s+Y\s+(?=[A-ZÁÉÍÓÚÑ' ]+,)", p.strip())
        out += [x.strip() for x in sub if x.strip()]
    return out


def parse_tp(html: str) -> tuple[Optional[dict], list[dict]]:
    """Devuelve (identidad, filas). Identidad={numero, fecha}. Cada <p> con un
    <a> cuyo texto es un expediente NNNN-X-AAAA es un proyecto."""
    soup = BeautifulSoup(html, "html.parser")
    ident = None
    h1 = soup.find(class_="tituloSeccion") or soup.find("h1")
    if h1:
        m = re.search(r"N[°º]?\s*(\d+)", h1.get_text(" ", strip=True))
        ident = {"numero": int(m.group(1)) if m else None,
                 "fecha": _fecha_iso(h1.get_text(" ", strip=True))}

    filas: list[dict] = []
    seccion = None
    raiz = soup.find(id="obleas") or soup
    for el in raiz.find_all(["h3", "p"]):
        if el.name == "h3":
            seccion = _limpiar(el.get_text(" ", strip=True)).upper() or seccion
            continue
        a = next((x for x in el.find_all("a")
                  if RE_EXP.match(_limpiar(x.get_text()))), None)
        if a is None:
            continue
        # firmantes: strongs ANTES del link · giros: strongs DESPUÉS del link
        antes, despues = [], []
        for st in el.find_all("strong"):
            if _antes_de(st, a):
                antes.append(st.get_text(" ", strip=True))
            else:
                despues.append(st.get_text(" ", strip=True))
        texto_p = el.get_text(" ", strip=True)
        firmantes = _firmantes(" ".join(antes))
        # tipo + sumario = texto entre el ':' de los firmantes y '(EXPEDIENTE'
        cuerpo = texto_p
        if antes:
            idx = cuerpo.find(antes[-1])
            if idx >= 0:
                cuerpo = cuerpo[idx + len(antes[-1]):]
        cuerpo = cuerpo.split("(" + _limpiar(a.get_text()))[0]
        cuerpo = _limpiar(cuerpo).lstrip(":").strip()
        m_tipo = re.match(r"(DE\s+[A-ZÁÉÍÓÚÑ ]+?)\.", cuerpo)
        tipo = _limpiar(m_tipo.group(1)) if m_tipo else None
        sumario = _limpiar(cuerpo[m_tipo.end():]) if m_tipo else cuerpo
        giros = _limpiar(" ".join(despues))
        filas.append({
            "tp_numero": (ident or {}).get("numero"),
            "fecha": (ident or {}).get("fecha"),
            "seccion": seccion,
            "expediente": _limpiar(a.get_text()),
            "firmantes": "; ".join(firmantes) if firmantes else None,
            "n_firmantes": len(firmantes) or None,
            "tipo": tipo,
            "sumario": sumario or None,
            "giros": giros or None,
            "pdf_url": a.get("href"),
        })
    return ident, filas


def _antes_de(el1, el2) -> bool:
    """True si el1 aparece antes que el2 en el orden del documento."""
    for x in el2.previous_elements:
        if x is el1:
            return True
    return False


def ultimo_tp(session: requests.Session) -> tuple[int, int]:
    """(periodo, numero) más reciente según el índice oficial."""
    html = _pedir(session, INDICE)
    pares = re.findall(r"tp\.html\?periodo=(\d+)&(?:amp;)?numero=(\d+)", html)
    if not pares:
        raise RuntimeError("índice TP sin links (¿cambió la página?)")
    periodo = max(int(p) for p, _ in pares)
    numero = max(int(n) for p, n in pares if int(p) == periodo)
    return periodo, numero


# ---------------------------------------------------------------------- main
def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    (DATA / "clean").mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    if len(sys.argv) == 3:  # debug puntual: numero periodo
        _, filas = parse_tp(_pedir(session, TP_URL.format(p=int(sys.argv[2]), n=int(sys.argv[1]))))
        print(json.dumps(filas[:5], indent=2, ensure_ascii=False))
        print(f"({len(filas)} proyectos en total)")
        return

    periodo, ultimo = ultimo_tp(session)
    logger.info("último TP publicado: %s (período %s)", ultimo, periodo)

    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    visto = estado.get("tp_diputados", {"periodo": periodo, "numero": 0})
    if visto["periodo"] != periodo:  # cambio de período: arrancar de cero
        visto = {"periodo": periodo, "numero": 0}

    nuevas: list[dict] = []
    for n in range(visto["numero"] + 1, ultimo + 1):
        try:
            ident, filas = parse_tp(_pedir(session, TP_URL.format(p=periodo, n=n)))
        except requests.RequestException as e:
            logger.warning("TP %s/%s falló (%s); reintento mañana", n, periodo, e)
            ultimo = n - 1  # no avanzar el estado más allá de lo logrado
            break
        for f in filas:
            f["periodo"] = periodo
        nuevas += filas
        logger.info("TP %03d/%s: %d proyectos", n, periodo, len(filas))

    if nuevas:
        df = pd.DataFrame(nuevas)
        if SALIDA.exists():
            df = pd.concat([pd.read_parquet(SALIDA), df], ignore_index=True)
        df = df.drop_duplicates(["expediente", "tp_numero", "periodo"], keep="first")
        df.to_parquet(SALIDA, index=False)
    estado["tp_diputados"] = {"periodo": periodo, "numero": ultimo}
    ESTADO.write_text(json.dumps(estado, indent=2))
    print(f"OK: {len(nuevas)} proyectos nuevos (hasta TP {ultimo}/período {periodo}) "
          f"-> {SALIDA if nuevas else '(sin cambios)'}")


if __name__ == "__main__":
    main()
