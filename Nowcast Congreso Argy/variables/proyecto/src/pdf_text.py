"""Bajar el PDF de un proyecto de ley y extraer su texto.

Entrada típica: el `pdf_url` que trae la ficha de `datos/seguimiento`.
Salida: el texto del proyecto (articulado + considerandos) para que el agente lo clasifique.

Detección de escaneados: si el PDF casi no tiene texto extraíble, es una imagen
(escaneo). Se marca `escaneado=True` y se conservan los bytes crudos en `datos`
para la RUTA DE VISIÓN: el agente manda el PDF como documento y Claude lo lee con
su visión nativa (OCR incorporado al modelo). No hace falta una librería de OCR
aparte. Ver `agente_taxonomias.clasificar_pdf` (modelo híbrido texto / PDF-documento).
"""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False

logger = logging.getLogger("proyecto.pdf_text")

UA = "Mozilla/5.0 (compatible; NowcastCongreso/1.0; +investigacion legislativa)"
HTTP_TIMEOUT = 30
# por debajo de esto, asumimos que el PDF es un escaneo (imagen) sin texto real
MIN_CHARS_TEXTO = 200


@dataclass
class TextoProyecto:
    texto: str
    paginas: int
    escaneado: bool
    fuente: str  # url o ruta de la que salió
    datos: Optional[bytes] = None  # bytes crudos del PDF (para la ruta de visión si es escaneado)


def _bajar(url: str, session: Optional[requests.Session] = None) -> bytes:
    sess = session or requests.Session()

    def _do() -> bytes:
        logger.info("GET PDF %s", url)
        r = sess.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.content

    if _HAS_TENACITY:
        _do = retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=15),
            retry=retry_if_exception_type(requests.RequestException),
        )(_do)
    return _do()


def _limpiar(texto: str) -> str:
    # normaliza espacios y saltos repetidos, conserva párrafos
    texto = texto.replace("\x00", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extraer_de_bytes(data: bytes, fuente: str = "bytes") -> TextoProyecto:
    """Extrae texto de un PDF en memoria (usa pypdf)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    partes: list[str] = []
    for pagina in reader.pages:
        try:
            partes.append(pagina.extract_text() or "")
        except Exception as e:  # una página rota no debe tirar todo
            logger.warning("página ilegible: %s", e)
    texto = _limpiar("\n".join(partes))
    escaneado = len(texto) < MIN_CHARS_TEXTO
    if escaneado:
        logger.warning("PDF con poco texto (%d chars) → probable escaneo (ruta de visión)", len(texto))
    return TextoProyecto(texto=texto, paginas=len(reader.pages), escaneado=escaneado,
                         fuente=fuente, datos=data)


def extraer_de_url(url: str, session: Optional[requests.Session] = None) -> TextoProyecto:
    return extraer_de_bytes(_bajar(url, session), fuente=url)


def extraer_de_archivo(ruta: str | Path) -> TextoProyecto:
    ruta = Path(ruta)
    return extraer_de_bytes(ruta.read_bytes(), fuente=str(ruta))


def recortar_para_prompt(texto: str, max_chars: int = 18000) -> str:
    """Acota el texto para el prompt. Conserva el inicio (articulado/considerandos)
    y, si hace falta cortar, agrega una marca. La mayoría de los proyectos entran enteros."""
    if len(texto) <= max_chars:
        return texto
    cabeza = texto[: int(max_chars * 0.8)]
    cola = texto[-int(max_chars * 0.2):]
    return f"{cabeza}\n\n[...texto recortado para clasificación...]\n\n{cola}"
