"""BOT DIARIO — adaptador SENADO: Diario de Asuntos Entrados (DAE Digital).

El DAE publica cada proyecto que entra al Senado (de senadores, del PE y de
Diputados en revisión) con: fecha de mesa de entradas, expediente (con tipo y
cámara), GIROS a comisiones y extracto. Numeración SECUENCIAL por año y tipo
(NORMAL | ACUERDOS) → el bot solo recuerda el último número visto y trae los
que faltan. Idempotente: correr dos veces no duplica.

Fuente (verificada en vivo 2026-07-11):
  https://www.senado.gob.ar/parlamentario/DAEDIGITAL/
  - GET base: muestra el último DAE cargado + su tabla completa.
  - DAE específico: formulario (número/año/tipo); el POST devuelve la misma
    página con la tabla de ese DAE. Plan B: rutas GET tipo generarPdf/N/A/T.

Estado local:  data/estado_bot.json   {"dae_normal": {"anio": X, "numero": N}, ...}
Salida:        data/clean/dae_entradas.parquet  (append + dedup por expediente+dae)
               columnas: fecha_mesa, dae_numero, dae_anio, dae_tipo, expediente,
                         expediente_url, giros, extracto, texto_url

Correr (PC con internet):
  python datos/bot_recoleccion/src/dae_senado.py            # trae lo nuevo
  python datos/bot_recoleccion/src/dae_senado.py 30 2026    # un DAE puntual (debug)
Tests offline:  python datos/bot_recoleccion/tests/test_dae.py

Las 4 directivas de resiliencia: errores específicos, backoff, parsing
defensivo (tabla por firma de encabezados), logging estructurado.
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
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False

logger = logging.getLogger("bot.dae_senado")

BASE = "https://www.senado.gob.ar"
DAE_URL = f"{BASE}/parlamentario/DAEDIGITAL/"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/bot_recoleccion)"}
TIMEOUT = 60
_RETRYABLE = (requests.ConnectionError, requests.Timeout, requests.HTTPError)

DATA = Path(__file__).resolve().parents[1] / "data"
ESTADO = DATA / "estado_bot.json"
SALIDA = DATA / "clean" / "dae_entradas.parquet"


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


# Sitios gob.ar suelen servir la cadena TLS incompleta (falta el intermedio):
# en un entorno limpio (CI) la verificación falla con "unable to get local
# issuer certificate". Se intenta SIEMPRE con verificación y, solo si falla por
# SSL, se reintenta sin verificar (plan B defensivo). Forzar con TLS_VERIFY=0.
_VERIFY = os.environ.get("TLS_VERIFY", "1") != "0"


def _pedir(session: requests.Session, url: str, method: str = "GET",
           data: Optional[dict] = None) -> str:
    def _do() -> str:
        try:
            r = session.request(method, url, data=data, headers=HEADERS,
                                timeout=TIMEOUT, verify=_VERIFY)
        except requests.exceptions.SSLError:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL verify falló en %s; reintento con verify=False", url)
            r = session.request(method, url, data=data, headers=HEADERS,
                                timeout=TIMEOUT, verify=False)
        r.raise_for_status()
        return r.text
    if _HAS_TENACITY:
        _do = retry(retry=retry_if_exception_type(_RETRYABLE), stop=stop_after_attempt(4),
                    wait=wait_exponential(multiplier=2, max=30), reraise=True)(_do)
    html = _do()
    time.sleep(float(os.environ.get("SLEEP", "0.5")))
    return html


# ------------------------------------------------------------------- parsing
def parse_dae(html: str) -> tuple[Optional[dict], list[dict]]:
    """Devuelve (identidad_del_dae, filas). Identidad = {numero, anio} del DAE
    mostrado; filas = expedientes de su tabla. Tolerante a faltantes."""
    soup = BeautifulSoup(html, "html.parser")
    ident = None
    m = re.search(r"generarPdf/(\d+)/(\d{4})", html)
    if m:
        ident = {"numero": int(m.group(1)), "anio": int(m.group(2))}

    filas: list[dict] = []
    for table in soup.find_all("table"):
        heads = {_norm(th.get_text()) for th in table.find_all("th")}
        if not ({"EXPEDIENTE", "EXTRACTO"} <= heads):
            continue
        cols = [_norm(th.get_text()) for th in table.find_all("th")]
        def idx(clave, defecto):  # columna por nombre, no por posición
            return next((i for i, c in enumerate(cols) if clave in c), defecto)
        i_fec, i_dae = idx("FECHA", 0), idx("NUMERO", 1)
        i_exp, i_gir = idx("EXPEDIENTE", 2), idx("GIROS", 3)
        i_ext = idx("EXTRACTO", 4)
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(i_exp, i_ext):
                continue
            a_exp = tds[i_exp].find("a", href=re.compile(r"/verExp/"))
            exp_txt = " ".join(tds[i_exp].get_text(" ", strip=True).split())
            if not exp_txt:
                continue
            a_txt = tr.find("a", href=re.compile(r"verPDFdaedigital"))
            m_dae = re.search(r"(\d+)\s*/\s*(\d{4})",
                              tds[i_dae].get_text(" ", strip=True)) if len(tds) > i_dae else None
            m_fec = re.search(r"(\d{2})/(\d{2})/(\d{4})",
                              tds[i_fec].get_text(" ", strip=True)) if len(tds) > i_fec else None
            filas.append({
                "fecha_mesa": (f"{m_fec.group(3)}-{m_fec.group(2)}-{m_fec.group(1)}"
                               if m_fec else None),
                "dae_numero": int(m_dae.group(1)) if m_dae else (ident or {}).get("numero"),
                "dae_anio": int(m_dae.group(2)) if m_dae else (ident or {}).get("anio"),
                "expediente": exp_txt.replace(" ", ""),
                "expediente_url": urljoin(BASE, a_exp["href"].split("?")[0]) if a_exp else None,
                "giros": " ".join(tds[i_gir].get_text(" ", strip=True).split())
                         if len(tds) > i_gir else None,
                "extracto": " ".join(tds[i_ext].get_text(" ", strip=True).split()),
                "texto_url": urljoin(BASE, a_txt["href"]) if a_txt else None,
            })
        break
    return ident, filas


def _form_dae(soup: BeautifulSoup, numero: int, anio: int) -> Optional[tuple[str, dict]]:
    """Arma el POST del buscador de DAE (todos los campos del form, pisando
    número y año). None si el form no está donde esperamos."""
    campo = soup.find(["input", "select"], attrs={"name": re.compile(r"numero|nro", re.I)})
    if campo is None:
        return None
    form = campo.find_parent("form")
    if form is None:
        return None
    payload: dict = {}
    for el in form.find_all(["input", "select"]):
        name = el.get("name")
        if not name:
            continue
        if el.name == "select":
            opt = el.find("option", selected=True) or el.find("option")
            payload[name] = opt.get("value", "") if opt else ""
        else:
            payload[name] = el.get("value", "")
    for name in payload:
        low = name.lower()
        if "numero" in low or "nro" in low:
            payload[name] = str(numero)
        elif "anio" in low or "ano" in low or "año" in name.lower():
            payload[name] = str(anio)
    return urljoin(DAE_URL, form.get("action") or DAE_URL), payload


def traer_dae(session: requests.Session, numero: int, anio: int,
              base_html: Optional[str] = None) -> list[dict]:
    """Trae un DAE puntual: primero por form POST; plan B, rutas GET conocidas."""
    if base_html is None:
        base_html = _pedir(session, DAE_URL)
    intento = _form_dae(BeautifulSoup(base_html, "html.parser"), numero, anio)
    if intento:
        ident, filas = parse_dae(_pedir(session, intento[0], "POST", intento[1]))
        if filas and ident and ident.get("numero") == numero:
            return filas
    for ruta in (f"{DAE_URL}index/{numero}/{anio}/1", f"{DAE_URL}{numero}/{anio}/1"):
        try:
            ident, filas = parse_dae(_pedir(session, ruta))
            if filas and ident and ident.get("numero") == numero:
                return filas
        except requests.RequestException:
            continue
    logger.warning("DAE %s/%s: no pude traerlo (form y rutas fallaron)", numero, anio)
    return []


# ---------------------------------------------------------------------- main
def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    (DATA / "clean").mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    if len(sys.argv) == 3:  # debug puntual
        filas = traer_dae(session, int(sys.argv[1]), int(sys.argv[2]))
        print(json.dumps(filas, indent=2, ensure_ascii=False)[:3000])
        return

    base_html = _pedir(session, DAE_URL)
    ident, filas_ult = parse_dae(base_html)
    if not ident:
        raise RuntimeError("no pude identificar el último DAE (¿cambió la página?)")
    logger.info("último DAE publicado: %s/%s", ident["numero"], ident["anio"])

    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    visto = estado.get("dae_normal", {"anio": ident["anio"], "numero": 0})
    if visto["anio"] != ident["anio"]:  # cambio de año: arrancar de cero
        visto = {"anio": ident["anio"], "numero": 0}

    nuevas: list[dict] = []
    for n in range(visto["numero"] + 1, ident["numero"] + 1):
        filas = filas_ult if n == ident["numero"] else traer_dae(session, n, ident["anio"], base_html)
        nuevas += filas
        logger.info("DAE %s/%s: %d expedientes", n, ident["anio"], len(filas))

    if nuevas:
        df = pd.DataFrame(nuevas)
        if SALIDA.exists():
            df = pd.concat([pd.read_parquet(SALIDA), df], ignore_index=True)
        df = df.drop_duplicates(["expediente", "dae_numero", "dae_anio"], keep="first")
        df.to_parquet(SALIDA, index=False)
    estado["dae_normal"] = {"anio": ident["anio"], "numero": ident["numero"]}
    ESTADO.write_text(json.dumps(estado, indent=2))
    print(f"OK: {len(nuevas)} expedientes nuevos (hasta DAE {ident['numero']}/{ident['anio']}) "
          f"-> {SALIDA if nuevas else '(sin cambios)'}")


if __name__ == "__main__":
    main()
