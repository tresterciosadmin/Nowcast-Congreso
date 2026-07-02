"""Construye el PADRÓN HISTÓRICO de bloques del Senado (2017-2025) desde los
anexos de Wikipedia, y un BORRADOR curable a mano para 2015-2017 (período sin
anexo en Wikipedia).

Contexto (decisión 2026-07-01, Franco): el sitio del Senado pinta el ÚLTIMO
bloque conocido de cada senador, no el contemporáneo al voto. Fuente elegida
para reconstruirlo: anexos de Wikipedia por período + validación contra
snapshots propios. Los anexos existen para 2017-2019 … 2023-2025; el tramo
2015-2017 se genera como borrador (sugerencia = bloque del período siguiente)
y lo revisa un humano.

Entradas:  datos/Archivos_Borrar/wiki_senadores/anexo_<periodo>.html
           (bajados con bajar_anexos_wiki.py)
           data/clean/senado_votos.parquet (para saber qué senadores
           necesitan cobertura 2015-2017)
Salidas:   data/padron_bloques_senado.csv       (regenerable, NO editar)
           data/padron_manual_2015_2017.csv     (se crea UNA vez; curar a mano,
                                                 nunca se pisa)

Correr:    python datos/senado/src/padron_bloques.py

Parsing defensivo: la fila se interpreta por CONTENIDO, no por posición
(las celdas de fecha se detectan por regex; bloque = última celda con texto
antes de la primera fecha; senador = celda con link anterior al bloque;
provincia con rowspan se arrastra). Sobrevive a colspan/rowspan cambiantes.
"""
from __future__ import annotations

import csv
import logging
import re
import unicodedata
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger("senado.padron")

PERIODOS = ["2017-2019", "2019-2021", "2021-2023", "2023-2025"]
ROOT = Path(__file__).resolve().parents[3]
WIKI = ROOT / "datos" / "Archivos_Borrar" / "wiki_senadores"
DATA = Path(__file__).resolve().parents[1] / "data"

_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_PARTICULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "E", "VAN", "VON", "DI", "DA"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def clave(nombre: str) -> str:
    """Clave de matching invariante al orden Apellido/Nombre y a partículas
    (mismo criterio que datos/canonica/entity_resolution)."""
    toks = [t for t in re.split(r"[^A-ZÑ]+", _norm(nombre)) if t and t not in _PARTICULAS]
    return " ".join(sorted(set(toks)))


def _fecha_iso(txt: str) -> str | None:
    m = _DATE.search(txt)
    if not m:
        return None  # "En el cargo" u otro texto
    d, mo, y = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def parse_anexo(html: str, periodo: str) -> list[dict]:
    """Extrae (senador, provincia, bloque, desde, hasta) del anexo, acotado a
    la ventana del período (10/12/año0 → 9/12/año2)."""
    y0, y2 = periodo.split("-")
    w_ini, w_fin = f"{y0}-12-10", f"{int(y2)}-12-09"
    soup = BeautifulSoup(html, "html.parser")
    tablas = [t for t in soup.find_all("table") if "sortable" in (t.get("class") or [])]
    if not tablas:
        raise ValueError(f"anexo {periodo}: no encontré la tabla sortable")
    prov, out = None, []
    for tr in tablas[0].find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        texts = [td.get_text(" ", strip=True) for td in tds]
        idx_fechas = [i for i, x in enumerate(texts)
                      if _DATE.search(x) or "EN EL CARGO" in _norm(x)]
        if len(idx_fechas) < 3:
            continue  # fila rara: mejor saltear que inventar
        i0 = idx_fechas[0]
        blo_i = next((j for j in range(i0 - 1, -1, -1) if texts[j].strip()), None)
        if blo_i is None:
            continue
        sen_i = next((j for j in range(blo_i - 1, -1, -1)
                      if tds[j].find("a") and texts[j].strip()), None)
        if sen_i is None:
            continue
        a = tds[sen_i].find_all("a")[-1]
        nombre = a.get_text(" ", strip=True) or a.get("title", "")
        p = next((texts[j] for j in range(sen_i) if texts[j].strip()), None)
        if p:
            prov = p
        # mandato real = últimas dos celdas-fecha de la fila
        real_ini = _fecha_iso(texts[idx_fechas[-2]])
        real_fin = _fecha_iso(texts[idx_fechas[-1]])
        out.append({
            "senador": nombre,
            "clave": clave(nombre),
            "provincia": _norm(prov or ""),
            "bloque": texts[blo_i].upper(),
            "desde": max(real_ini or w_ini, w_ini),
            "hasta": min(real_fin or w_fin, w_fin),
            "fuente": f"wikipedia:{periodo}",
            "nota": "",
        })
    if not (60 <= len(out) <= 90):
        logger.warning("anexo %s: %d filas (esperaba ~72)", periodo, len(out))
    return out


def _borrador_2015_2017(padron: list[dict]) -> list[dict]:
    """Senadores que votaron en 2015-01-01…2017-12-09 según la base scrapeada,
    con bloque SUGERIDO desde el período 2017-2019 (¡puede estar mal: el
    peronismo se partió a fines de 2017!). Revisa un humano."""
    import pandas as pd
    votos = pd.read_parquet(DATA / "clean" / "senado_votos.parquet")
    actas = pd.read_parquet(DATA / "clean" / "senado_actas.parquet")
    f = votos.merge(actas[["acta_id", "fecha"]], on="acta_id")
    f = f[(f.fecha >= "2015-01-01") & (f.fecha <= "2017-12-09")]
    sugerencias = {r["clave"]: r for r in padron if r["fuente"] == "wikipedia:2017-2019"}
    out = []
    for (nombre, prov), _ in f.groupby(["legislador_nombre", "distrito"]):
        k = clave(nombre)
        sug = sugerencias.get(k)
        out.append({
            "senador": nombre,
            "clave": k,
            "provincia": _norm(prov or ""),
            "bloque": (sug["bloque"] if sug else ""),
            "desde": "2015-01-01",
            "hasta": "2017-12-09",
            "fuente": "BORRADOR",
            "nota": ("sugerido desde 2017-2019, REVISAR (el PJ se partió fines de 2017)"
                     if sug else "SIN SUGERENCIA: completar a mano"),
        })
    return sorted(out, key=lambda r: (r["provincia"], r["senador"]))


CAMPOS = ["senador", "clave", "provincia", "bloque", "desde", "hasta", "fuente", "nota"]


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    padron: list[dict] = []
    for p in PERIODOS:
        f = WIKI / f"anexo_{p}.html"
        if not f.exists():
            logger.error("falta %s (correr bajar_anexos_wiki.py)", f.name)
            continue
        filas = parse_anexo(f.read_text(encoding="utf-8"), p)
        logger.info("anexo %s: %d senadores", p, len(filas))
        padron += filas

    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "padron_bloques_senado.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(padron)
    print(f"OK padrón: {len(padron)} filas -> {out}")

    manual = DATA / "padron_manual_2015_2017.csv"
    if manual.exists():
        print(f"ya existe {manual.name}: NO lo piso (curado a mano)")
    else:
        filas = _borrador_2015_2017(padron)
        with manual.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(filas)
        sin = sum(1 for r in filas if not r["bloque"])
        print(f"OK borrador 2015-2017: {len(filas)} senadores ({sin} sin sugerencia) "
              f"-> {manual} — REVISAR A MANO")


if __name__ == "__main__":
    main()
