"""Scraper de JEFES DE BLOQUE de AMBAS CÁMARAS (fuentes OFICIALES).

HALLAZGO (2026-07-30): la página oficial `diputados-por-bloque.html` marca
"Presidente" junto al nombre del jefe de CADA bloque. Es dato oficial, cubre
TODOS los bloques (incl. monobloques) y evita curar el período vigente a mano.

LIMITACIÓN: publica solo la composición VIGENTE (no la serie histórica). Por eso
este script hace SNAPSHOTS con fecha y los ACUMULA: corriéndolo periódicamente
(el bot diario puede hacerlo 1×/mes) la serie se construye hacia adelante sola.
El histórico 2008-2025 sigue siendo curación manual (jefes_bloque.csv).

Salida: variables/proyecto/data/jefes_bloque_oficial.csv (append + dedup por
        nombre+bloque+snapshot) — columnas compatibles con jefes_bloque.csv.

Correr:  python variables/proyecto/src/scrape_jefes_bloque.py
Tests:   python variables/proyecto/tests/test_scrape_jefes.py
"""
from __future__ import annotations

import csv
import logging
import os
import re
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Los sitios gob.ar sirven la cadena TLS incompleta (falta el intermedio) →
# "unable to get local issuer certificate". Mismo criterio que el bot
# (datos/bot_recoleccion): se intenta SIEMPRE con verificación y solo ante
# SSLError se reintenta sin verificar. Forzar con TLS_VERIFY=0.
_VERIFY = os.environ.get("TLS_VERIFY", "1") != "0"


def _pedir(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=90, verify=_VERIFY)
    except requests.exceptions.SSLError:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.warning("SSL verify falló en %s; reintento con verify=False", url)
        r = requests.get(url, headers=HEADERS, timeout=90, verify=False)
    r.raise_for_status()
    return r.text

logger = logging.getLogger("proyecto.jefes")
URL = "https://www.hcdn.gob.ar/diputados/diputados-por-bloque.html"
URL_SEN = "https://www.senado.gob.ar/senadores/listados/agrupados-por-bloques"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (variables/proyecto)"}
SALIDA = Path(__file__).resolve().parents[1] / "data" / "jefes_bloque_oficial.csv"
CAMPOS = ["nombre", "camara", "bloque", "desde", "hasta", "periodo",
          "confianza", "fuente", "nota"]


def _limpiar(s: str) -> str:
    return " ".join(str(s).split())


def parse_jefes(html: str, snapshot: str) -> list[dict]:
    """Un dict por bloque cuyo listado marca 'Presidente'. Defensivo: si la
    página cambia y no hay marca, devuelve [] (no inventa)."""
    soup = BeautifulSoup(html, "html.parser")
    filas: list[dict] = []
    for h in soup.find_all(re.compile(r"^h[1-4]$")):
        titulo = _limpiar(h.get_text(" ", strip=True))
        m = re.match(r"(.+?)(\d+)$", titulo)          # "PRO12" -> ("PRO", 12)
        if not m:
            continue
        bloque, bancas = _limpiar(m.group(1)), int(m.group(2))
        # el jefe es el primer texto con "Presidente" dentro de la sección
        nodo, jefe = h.find_next(), None
        while nodo is not None and nodo.name not in ("h1", "h2", "h3", "h4"):
            txt = _limpiar(nodo.get_text(" ", strip=True)) if hasattr(nodo, "get_text") else ""
            if txt.endswith("Presidente"):
                jefe = _limpiar(txt[: -len("Presidente")])
                break
            nodo = nodo.find_next()
        if jefe:
            filas.append({
                "nombre": jefe.upper(), "camara": "diputados", "bloque": bloque,
                "desde": snapshot, "hasta": "", "periodo": f"snapshot-{snapshot}",
                "confianza": "ALTA", "fuente": "hcdn.gob.ar/diputados-por-bloque (oficial)",
                "nota": f"{bancas} bancas al {snapshot}",
            })
    return filas


def parse_jefes_senado(html: str, snapshot: str) -> list[dict]:
    """Senado: la tabla tiene columna PRESIDENTE explícita (Bloque | Presidente |
    Integrantes | Contacto), PERO anida sub-tablas de asesores/personal dentro de
    cada fila. Filtros para no tomar empleados como jefes (bug 2026-07-30):
      - la fila debe tener celda de INTEGRANTES con un número (los bloques la
        tienen; las filas de personal, no),
      - la celda de bloque no debe contener enlaces a fichas de senador (las
        filas anidadas listan a los integrantes con foto y link),
      - se descartan filas con textos de la sub-tabla ("Personal / asesores")."""
    soup = BeautifulSoup(html, "html.parser")
    filas: list[dict] = []
    for table in soup.find_all("table"):
        cols = [_limpiar(th.get_text()).upper() for th in table.find_all("th")]
        if not ("BLOQUE" in cols and any("PRESIDENT" in c for c in cols)):
            continue
        i_blo = cols.index("BLOQUE")
        i_pre = next(i for i, c in enumerate(cols) if "PRESIDENT" in c)
        i_int = next((i for i, c in enumerate(cols) if "INTEGRANTE" in c), None)
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(i_blo, i_pre) or i_int is None or len(tds) <= i_int:
                continue
            bancas_txt = _limpiar(tds[i_int].get_text(" ", strip=True))
            if not re.fullmatch(r"\d+", bancas_txt):      # sin nº de integrantes -> no es bloque
                continue
            bloque = _limpiar(tds[i_blo].get_text(" ", strip=True))
            jefe = _limpiar(tds[i_pre].get_text(" ", strip=True))
            if tds[i_blo].find("a", href=re.compile(r"/senadores/senador/")):
                continue                                   # fila anidada de integrantes
            if not bloque or not jefe or len(jefe) > 60 or len(bloque) > 60:
                continue
            if "PERSONAL" in bloque.upper() or "ASESOR" in bloque.upper():
                continue
            filas.append({
                "nombre": jefe.upper(), "camara": "senado", "bloque": bloque.upper(),
                "desde": snapshot, "hasta": "", "periodo": f"snapshot-{snapshot}",
                "confianza": "ALTA",
                "fuente": "senado.gob.ar/agrupados-por-bloques (oficial)",
                "nota": f"{bancas_txt} bancas al {snapshot}",
            })
        break
    return filas


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    snapshot = date.today().isoformat()
    filas = parse_jefes(_pedir(URL), snapshot)
    logger.info("Diputados: %d bloques con presidente", len(filas))
    try:
        sen = parse_jefes_senado(_pedir(URL_SEN), snapshot)
        logger.info("Senado: %d bloques con presidente", len(sen))
        filas += sen
    except (requests.RequestException, ValueError) as e:
        logger.error("Senado falló (%s): sigo solo con Diputados", e)
    if not filas:
        raise SystemExit("no encontré presidentes en ninguna cámara: ¿cambiaron las páginas?")

    previas: list[dict] = []
    if SALIDA.exists():
        with SALIDA.open(encoding="utf-8-sig") as f:
            previas = [r for r in csv.DictReader(f) if not str(r.get("nombre", "")).startswith("#")]
    vistos = {(r["nombre"], r["bloque"], r["desde"], r.get("camara", "")) for r in previas}
    nuevas = [r for r in filas
              if (r["nombre"], r["bloque"], r["desde"], r["camara"]) not in vistos]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(previas + nuevas)
    ndip = sum(1 for r in filas if r["camara"] == "diputados")
    print(f"OK jefes={len(filas)} (diputados {ndip} · senado {len(filas)-ndip}); "
          f"nuevos: {len(nuevas)}; snapshot={snapshot} -> {SALIDA}")
    for r in filas:
        if r["camara"] == "senado":
            print(f"   [SEN] {r['bloque'][:34]:34} {r['nombre'][:32]}")


if __name__ == "__main__":
    main()
