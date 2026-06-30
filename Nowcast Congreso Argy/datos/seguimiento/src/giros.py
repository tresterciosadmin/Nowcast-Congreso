"""Extractor de GIROS y TRÁMITE de proyectos de ley (Diputados + Senado).

Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de
avance: giros a comisiones, movimientos de trámite, fechas y link al PDF.
Es el insumo del EMBUDO (variables/embudo): "qué entró y en qué quedó".

Dos fuentes, una salida común (`FichaExpediente`):

  • Diputados — página del autor:
      https://www.hcdn.gov.ar/diputados/<slug>/proyecto.html?exp=<NNNN-D-AAAA>
    (requiere el `slug` del diputado autor, guardado en el dataset de
     parlamentarios). Trae firmantes, giro a comisiones y trámite.

  • Senado — ficha del expediente:
      https://www.senado.gob.ar/parlamentario/comisiones/verExp/<NRO>.<AA>/S/PL
    Una sola URL trae autor, fechas de mesa de entradas, giros con fecha de
    ingreso/egreso y orden, y link al PDF. No necesita slug.

Parsing DEFENSIVO: las tablas no se ubican por posición sino por la FIRMA de
sus encabezados (p.ej. una tabla con columnas {COMISIÓN, FECHA DE INGRESO} es
"giros"). Así sobrevive a cambios de layout. Toda extracción es tolerante a
campos faltantes: si algo no está, queda en None y se sigue.

Las 4 directivas de resiliencia del proyecto:
  - errores específicos (no `except: pass` ciego),
  - backoff en red (tenacity),
  - parsing defensivo (firma de encabezados, None ante ausencia),
  - logging estructurado.

NOTA: el sandbox de Claude no llega a las webs del Congreso. El test en vivo
(`python giros.py <exp>`) se corre en una PC con salida a internet.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

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

logger = logging.getLogger("seguimiento.giros")

UA = (
    "Mozilla/5.0 (compatible; NowcastCongreso/1.0; "
    "investigacion legislativa; +https://github.com/tresterciosadmin/Nowcast-Congreso)"
)
HTTP_TIMEOUT = 25

BASE_DIP = "https://www.hcdn.gov.ar/diputados/{slug}/proyecto.html"
BASE_SEN = "https://www.senado.gob.ar/parlamentario/comisiones/verExp/{nro}.{aa}/S/PL"


# ────────────────────────────────────────────────────────────────────────────
# Estructuras de salida
# ────────────────────────────────────────────────────────────────────────────
@dataclass
class Giro:
    comision: str
    orden: Optional[int] = None          # orden de giro (Senado lo trae explícito)
    competencia_primaria: bool = False   # Diputados marca "(Primera Competencia)"
    fecha_ingreso: Optional[str] = None  # ISO yyyy-mm-dd
    fecha_egreso: Optional[str] = None


@dataclass
class Movimiento:
    camara: Optional[str] = None
    movimiento: str = ""
    fecha: Optional[str] = None
    resultado: Optional[str] = None


@dataclass
class Firmante:
    nombre: str
    distrito: Optional[str] = None
    bloque: Optional[str] = None


@dataclass
class FichaExpediente:
    expediente: str                       # denominador canónico NNNN-X-AAAA
    camara: str                           # "diputados" | "senado"
    url: str
    sumario: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    firmantes: list[Firmante] = field(default_factory=list)
    giros: list[Giro] = field(default_factory=list)
    tramite: list[Movimiento] = field(default_factory=list)
    pdf_url: Optional[str] = None
    estado: Optional[str] = None          # derivado del trámite (best-effort)
    fuente_ok: bool = True                # False si la página no parece la esperada
    capturado_en: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# ────────────────────────────────────────────────────────────────────────────
# Helpers de texto / fecha
# ────────────────────────────────────────────────────────────────────────────
def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _sin_tildes_upper(s: str) -> str:
    nf = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in nf if not unicodedata.combining(c)).upper().strip()


def _fecha_iso(s: Optional[str]) -> Optional[str]:
    """'24-06-2026' o '24/06/2026' -> '2026-06-24'. Si no parsea, None."""
    s = _norm(s)
    if not s or _sin_tildes_upper(s) in {"SIN FECHA", "", "-"}:
        return None
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if not m:
        return None
    d, mth, y = (int(x) for x in m.groups())
    try:
        return datetime(y, mth, d).date().isoformat()
    except ValueError:
        return None


def _tabla_a_filas(table) -> tuple[list[str], list[list[str]]]:
    """Devuelve (encabezados_normalizados_UPPER, filas) de un <table>."""
    filas: list[list[str]] = []
    encabezados: list[str] = []
    for tr in table.find_all("tr"):
        celdas_h = tr.find_all("th")
        if celdas_h and not encabezados:
            encabezados = [_sin_tildes_upper(_norm(th.get_text())) for th in celdas_h]
            continue
        celdas = tr.find_all("td")
        if celdas:
            filas.append([_norm(td.get_text(" ", strip=True)) for td in celdas])
    # algunos sitios ponen los encabezados como primer <tr> de <td>
    if not encabezados and filas:
        posibles = [_sin_tildes_upper(x) for x in filas[0]]
        marcadores = {"COMISION", "FIRMANTE", "MOVIMIENTO", "CAMARA", "N", "ORIGEN"}
        if any(p in marcadores for p in posibles):
            encabezados = posibles
            filas = filas[1:]
    return encabezados, filas


def _firma(encabezados: list[str], *claves: str) -> bool:
    """True si TODAS las claves aparecen (como substring) en los encabezados."""
    joined = " | ".join(encabezados)
    return all(any(c in h for h in encabezados) or c in joined for c in claves)


# ────────────────────────────────────────────────────────────────────────────
# Denominadores
# ────────────────────────────────────────────────────────────────────────────
def normalizar_denominador_dip(exp: str) -> str:
    """'2832-D-2026' -> '2832-D-2026' (valida y normaliza)."""
    m = re.match(r"\s*(\d+)\s*-\s*([A-Za-z]+)\s*-\s*(\d{4})\s*$", exp)
    if not m:
        raise ValueError(f"Denominador Diputados inválido: {exp!r}")
    return f"{int(m.group(1))}-{m.group(2).upper()}-{m.group(3)}"


def denominador_senado(nro: int | str, anio: int | str) -> str:
    """nro=1091, anio=2026 -> '1091-S-2026'. Acepta año de 2 dígitos."""
    a = int(anio)
    if a < 100:
        a += 2000
    return f"{int(nro)}-S-{a}"


# ────────────────────────────────────────────────────────────────────────────
# HTTP
# ────────────────────────────────────────────────────────────────────────────
def _get(url: str, session: Optional[requests.Session] = None) -> str:
    sess = session or requests.Session()

    def _do() -> str:
        logger.info("GET %s", url)
        r = sess.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        r.encoding = r.encoding or "utf-8"
        return r.text

    if _HAS_TENACITY:
        _do = retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=15),
            retry=retry_if_exception_type(requests.RequestException),
        )(_do)
    return _do()


# ────────────────────────────────────────────────────────────────────────────
# Parser: Diputados
# ────────────────────────────────────────────────────────────────────────────
def parse_diputados(html: str, expediente: str, url: str) -> FichaExpediente:
    soup = BeautifulSoup(html, "html.parser")
    ficha = FichaExpediente(expediente=expediente, camara="diputados", url=url)

    texto = soup.get_text("\n", strip=True)

    m = re.search(r"Sumario:\s*(.+)", texto)
    if m:
        ficha.sumario = _norm(m.group(1))
    m = re.search(r"Fecha:\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{4})", texto)
    if m:
        ficha.fecha_ingreso = _fecha_iso(m.group(1))

    # PDF: enlace "Ver documento original"
    for a in soup.find_all("a", href=True):
        if "detalle_tp_adjunto" in a["href"] or "Ver documento" in _norm(a.get_text()):
            ficha.pdf_url = urljoin(url, a["href"])
            break

    # marca de página correcta
    ficha.fuente_ok = "PROYECTO" in _sin_tildes_upper(texto) and bool(
        re.search(r"\d+-[A-Z]+-\d{4}", texto)
    )

    for table in soup.find_all("table"):
        enc, filas = _tabla_a_filas(table)
        if _firma(enc, "FIRMANTE"):
            for f in filas:
                if not f or not f[0]:
                    continue
                ficha.firmantes.append(
                    Firmante(
                        nombre=f[0],
                        distrito=f[1] if len(f) > 1 else None,
                        bloque=f[2] if len(f) > 2 else None,
                    )
                )
        elif _firma(enc, "COMISION") and not _firma(enc, "MOVIMIENTO"):
            for f in filas:
                if not f or not f[0]:
                    continue
                texto_com = f[0]
                prim = "PRIMERA COMPETENCIA" in _sin_tildes_upper(texto_com)
                com = re.sub(r"\(?\s*primera competencia\s*\)?", "", texto_com,
                             flags=re.IGNORECASE).strip(" -")
                ficha.giros.append(Giro(comision=_norm(com), competencia_primaria=prim))
        elif _firma(enc, "MOVIMIENTO"):
            idx = {h: i for i, h in enumerate(enc)}

            def col(f, *names):
                for n in names:
                    for h, i in idx.items():
                        if n in h and i < len(f):
                            return f[i]
                return None

            for f in filas:
                if not any(f):
                    continue
                ficha.tramite.append(
                    Movimiento(
                        camara=col(f, "CAMARA"),
                        movimiento=col(f, "MOVIMIENTO") or "",
                        fecha=_fecha_iso(col(f, "FECHA")),
                        resultado=col(f, "RESULTADO"),
                    )
                )

    ficha.estado = _derivar_estado(ficha)
    return ficha


# ────────────────────────────────────────────────────────────────────────────
# Parser: Senado
# ────────────────────────────────────────────────────────────────────────────
def parse_senado(html: str, expediente: str, url: str) -> FichaExpediente:
    soup = BeautifulSoup(html, "html.parser")
    ficha = FichaExpediente(expediente=expediente, camara="senado", url=url)
    texto = soup.get_text("\n", strip=True)

    ficha.fuente_ok = "EXPEDIENTE" in _sin_tildes_upper(texto)

    # PDF "Texto Original ...../downloadPdf"
    for a in soup.find_all("a", href=True):
        if "downloadPdf" in a["href"]:
            ficha.pdf_url = urljoin(url, a["href"])
            break

    # Autores: la señal más robusta son los links al perfil del senador
    # (/senadores/senador/<id>). La tabla "Listado de Autores" arma su
    # encabezado distinto según la ficha, así que no dependemos de ella.
    vistos: set[str] = set()
    for a in soup.find_all("a", href=True):
        if re.search(r"/senadores/senador/\d+", a["href"]):
            nombre = re.sub(r"\s+,", ",", _norm(a.get_text()))
            if nombre and nombre.upper() not in vistos:
                vistos.add(nombre.upper())
                ficha.firmantes.append(Firmante(nombre=nombre))

    for table in soup.find_all("table"):
        enc, filas = _tabla_a_filas(table)

        # tabla cabecera del expediente: N° | Origen | Tipo | Extracto
        if _firma(enc, "EXTRACTO") or _firma(enc, "ORIGEN", "TIPO"):
            if filas and filas[0]:
                ficha.sumario = filas[0][-1]
            continue

        # mesa de entradas (fecha de ingreso)
        if _firma(enc, "MESA DE ENTRADAS"):
            if filas and filas[0]:
                ficha.fecha_ingreso = _fecha_iso(filas[0][0])
            continue

        # autores (fallback por tabla, por si no hubiera links de perfil)
        if _firma(enc, "LISTADO DE AUTORES") or _firma(enc, "AUTORES"):
            for f in filas:
                if f and f[0]:
                    nombre = re.sub(r"\s+,", ",", _norm(f[0]))
                    if nombre.upper() not in vistos:
                        vistos.add(nombre.upper())
                        ficha.firmantes.append(Firmante(nombre=nombre))
            continue

        # giros: COMISIÓN | FECHA DE INGRESO | FECHA DE EGRESO
        if _firma(enc, "COMISION") and _firma(enc, "INGRESO"):
            for f in filas:
                if not f or not f[0]:
                    continue
                cel = f[0]
                orden = None
                mo = re.search(r"ORDEN DE GIRO:?\s*(\d+)", _sin_tildes_upper(cel))
                if mo:
                    orden = int(mo.group(1))
                com = re.sub(r"orden de giro:?\s*\d+", "", cel, flags=re.IGNORECASE)
                com = _norm(com)
                ficha.giros.append(
                    Giro(
                        comision=com,
                        orden=orden,
                        fecha_ingreso=_fecha_iso(f[1]) if len(f) > 1 else None,
                        fecha_egreso=_fecha_iso(f[2]) if len(f) > 2 else None,
                    )
                )
            continue

    ficha.estado = _derivar_estado(ficha)
    return ficha


# ────────────────────────────────────────────────────────────────────────────
# Estado derivado (best-effort; se afinará al definir el embudo)
# ────────────────────────────────────────────────────────────────────────────
def _derivar_estado(ficha: FichaExpediente) -> Optional[str]:
    blob = " ".join(
        _sin_tildes_upper(m.movimiento + " " + (m.resultado or "")) for m in ficha.tramite
    )
    if any(k in blob for k in ("SANCIONADO", "SANCION DEFINITIVA")):
        return "sancionado"
    if "MEDIA SANCION" in blob:
        return "media_sancion"
    if any(k in blob for k in ("RECHAZAD", "DESESTIM")):
        return "rechazado"
    if any(g.fecha_egreso for g in ficha.giros):
        return "con_dictamen"
    if ficha.giros:
        return "en_comision"
    return "ingresado"


# ────────────────────────────────────────────────────────────────────────────
# API de alto nivel
# ────────────────────────────────────────────────────────────────────────────
def giros_diputados(expediente: str, slug: str,
                    session: Optional[requests.Session] = None) -> FichaExpediente:
    exp = normalizar_denominador_dip(expediente)
    url = f"{BASE_DIP.format(slug=slug)}?exp={exp}"
    return parse_diputados(_get(url, session), exp, url)


def giros_senado(nro: int | str, anio: int | str,
                 session: Optional[requests.Session] = None) -> FichaExpediente:
    a = int(anio)
    aa = a % 100
    url = BASE_SEN.format(nro=int(nro), aa=f"{aa:02d}")
    exp = denominador_senado(nro, anio)
    return parse_senado(_get(url, session), exp, url)


# ────────────────────────────────────────────────────────────────────────────
# CLI (test en vivo desde una PC con internet)
# ────────────────────────────────────────────────────────────────────────────
def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Extrae giros/trámite de un expediente.")
    sub = p.add_subparsers(dest="camara", required=True)

    pd = sub.add_parser("diputados", help="requiere exp y slug del autor")
    pd.add_argument("exp", help="ej: 2832-D-2026")
    pd.add_argument("slug", help="ej: sajmechet")

    ps = sub.add_parser("senado", help="requiere nro y año")
    ps.add_argument("nro", help="ej: 1091")
    ps.add_argument("anio", help="ej: 2026")

    args = p.parse_args()
    if args.camara == "diputados":
        ficha = giros_diputados(args.exp, args.slug)
    else:
        ficha = giros_senado(args.nro, args.anio)
    print(ficha.to_json())


if __name__ == "__main__":
    _main()
