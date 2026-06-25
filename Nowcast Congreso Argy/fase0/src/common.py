"""Utilidades compartidas Fase 0: descarga resiliente y logging estructurado.

Directivas de resiliencia (no negociables):
1. Manejo de errores especifico (no except Exception generico).
2. Reintentos con backoff exponencial para todo lo que pueda fallar por red/429.
3. Parsing defensivo + validacion.
4. Logging estructurado (structlog), nunca print.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from requests.exceptions import (
    ConnectionError as ReqConnError,
    HTTPError,
    Timeout,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

try:
    import structlog

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )
    log = structlog.get_logger("fase0")
except ImportError:  # fallback minimo sin tapar el error de import real de otra cosa
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger("fase0")

CKAN_API = "https://datos.hcdn.gob.ar/api/3/action/"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (fase0 baseline)"}

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "outputs"
for _d in (RAW, CLEAN, OUT):
    _d.mkdir(parents=True, exist_ok=True)


@retry(
    retry=retry_if_exception_type((ReqConnError, Timeout, HTTPError)),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def http_get(url: str, *, timeout: int = 120, stream: bool = False) -> requests.Response:
    """GET con reintentos exponenciales. Reintenta solo errores de red/HTTP transitorios."""
    resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=stream, verify=True)
    # 429/5xx -> raise_for_status dispara HTTPError, que tenacity reintenta.
    if resp.status_code == 429 or resp.status_code >= 500:
        resp.raise_for_status()
    resp.raise_for_status()
    return resp


def ckan_resource_url(resource_id: str) -> str:
    """Resuelve la URL de descarga de un recurso CKAN por su id (parsing defensivo)."""
    resp = http_get(f"{CKAN_API}resource_show?id={resource_id}", timeout=30)
    payload = resp.json()
    if not isinstance(payload, dict) or not payload.get("success"):
        raise ValueError(f"CKAN resource_show sin success para {resource_id}")
    result = payload.get("result") or {}
    url = result.get("url")
    if not url:
        raise ValueError(f"Recurso {resource_id} sin url de descarga")
    return url


def download_to(resource_id: str, dest: Path) -> Path:
    """Descarga un recurso CKAN a disco si no existe (cache local)."""
    if dest.exists() and dest.stat().st_size > 0:
        log.info("cache_hit", file=dest.name, bytes=dest.stat().st_size)
        return dest
    url = ckan_resource_url(resource_id)
    log.info("download_start", file=dest.name, url=url)
    resp = http_get(url, timeout=300, stream=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with tmp.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            if chunk:
                fh.write(chunk)
    tmp.replace(dest)
    log.info("download_done", file=dest.name, bytes=dest.stat().st_size)
    return dest
