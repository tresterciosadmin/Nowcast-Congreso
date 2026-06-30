"""Seguidor de GIROS y TRÁMITE de proyectos de ley (Diputados + Senado).

Qué hace
--------
Dado un expediente ya conocido (su "denominador"), arma la URL determinística de
su ficha en la web de la cámara correspondiente y devuelve, en una estructura
única para ambas cámaras:

  - giros a comisión (con orden y, en Senado, fechas de ingreso/egreso),
  - movimientos de trámite (lo que pasó: media sanción, dictamen, etc.),
  - un `estado` inferido de forma conservadora,
  - el link al PDF del texto original (para el agente de taxonomías).

Este módulo NO descubre proyectos nuevos: eso lo hace el monitor (proyectos_api /
senado_proyectos). Acá seguimos el estado de proyectos que YA conocemos.

Fuentes (verificadas jun-2026)
------------------------------
  Diputados: https://www.hcdn.gov.ar/diputados/<slug>/proyecto.html?exp=<EXP>
             (sirve la tabla de Giro a comisiones y la de Trámite; requiere el
             slug del autor, que se guarda en el dataset de parlamentarios)
  Senado:    https://www.senado.gob.ar/parlamentario/comisiones/verExp/<num>.<año>/S/PL
             (sirve Giros a Comisiones con fechas + Trámite Legislativo; la URL
             se arma sola desde el expediente, sin slug)

Directivas de resiliencia (CLAUDE.md): errores específicos, backoff en red,
parsing defensivo (anclado en el texto de los encabezados, no en clases CSS
frágiles), y "falla seguro": si la página parece bloqueada/cambiada, se lanza
FuenteSospechosa en vez de devolver "sin giros" silenciosamente.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("seguidor_giros")

HTTP_TIMEOUT = 25
BASE_DIP = "https://www.hcdn.gov.ar"
BASE_SEN = "https://www.senado.gob.ar"

# Marcadores de que la respuesta no es confiable (Cloudflare / JS wall / vacío).
_MARCADORES_BLOQUEO = (
    "checking your browser", "just a moment", "challenge-platform",
    "attention required", "/cdn-cgi/", "enable javascript and cookies",
)


class FuenteSospechosa(Exception):
    """La respuesta no es confiable; no afirmar 'sin giros'."""


# ─────────────────────────────────────────────────────────────────────────────
# Normalización del expediente
# ─────────────────────────────────────────────────────────────────────────────

# Diputados: NNNN-D-AAAA (la letra es el origen: D, S, PE, etc.)
_RX_DIP = re.compile(r"^\s*(\d{1,5})\s*-\s*([A-Za-z]{1,3})\s*-\s*(\d{4})\s*$")
# Senado: "S-1091/26", "1091/26", "1091/2026", "S 1091/26" …
_RX_SEN = re.compile(r"^\s*(?:S[-\s]?)?(\d{1,5})\s*/\s*(\d{2,4})\s*$", re.IGNORECASE)


def _strip_tildes(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def detectar_camara(expediente: str) -> str:
    """Devuelve 'diputados' o 'senado' a partir del formato del expediente."""
    if _RX_DIP.match(expediente or ""):
        return "diputados"
    if _RX_SEN.match(expediente or ""):
        return "senado"
    raise ValueError(f"No reconozco el formato de expediente: {expediente!r}")


def normalizar_dip(expediente: str) -> str:
    """'2832-d-2026' -> '2832-D-2026' (canónico para la query ?exp=)."""
    m = _RX_DIP.match(expediente or "")
    if not m:
        raise ValueError(f"Expediente de Diputados inválido: {expediente!r}")
    num, origen, anio = m.group(1), m.group(2).upper(), m.group(3)
    return f"{num}-{origen}-{anio}"


def normalizar_sen(expediente: str) -> tuple[str, str]:
    """'S-1091/26' -> ('1091', '26'). Conserva el año tal como viene (2 o 4 díg.),
    que es lo que usa la URL verExp (verExp/1091.26/S/PL)."""
    m = _RX_SEN.match(expediente or "")
    if not m:
        raise ValueError(f"Expediente de Senado inválido: {expediente!r}")
    return m.group(1), m.group(2)


# ─────────────────────────────────────────────────────────────────────────────
# Construcción de URLs
# ─────────────────────────────────────────────────────────────────────────────

def url_diputados(slug_autor: str, expediente: str) -> str:
    """Requiere el slug del autor (ej. 'sajmechet'), guardado en el dataset de
    parlamentarios. La ficha del proyecto cuelga de la página del diputado."""
    if not slug_autor:
        raise ValueError("Diputados necesita el slug del autor para armar la URL.")
    exp = normalizar_dip(expediente)
    slug = slug_autor.strip().strip("/").lower()
    return f"{BASE_DIP}/diputados/{slug}/proyecto.html?exp={exp}"


def url_senado(expediente: str) -> str:
    """Determinística desde el expediente; no necesita autor."""
    num, anio = normalizar_sen(expediente)
    return f"{BASE_SEN}/parlamentario/comisiones/verExp/{num}.{anio}/S/PL"


# ─────────────────────────────────────────────────────────────────────────────
# Estructura de salida (única para ambas cámaras)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Giro:
    comision: str
    orden: int | None = None          # orden de giro (Senado lo trae explícito)
    fecha_ingreso: str | None = None  # 'DD-MM-AAAA' (Senado)
    fecha_egreso: str | None = None
    primera_competencia: bool = False  # Diputados marca "(Primera Competencia)"


@dataclass
class Movimiento:
    camara: str
    descripcion: str
    fecha: str | None = None
    resultado: str | None = None


@dataclass
class Seguimiento:
    expediente: str
    camara: str
    url: str
    sumario: str | None = None
    fecha_ingreso: str | None = None
    pdf_url: str | None = None
    giros: list[Giro] = field(default_factory=list)
    movimientos: list[Movimiento] = field(default_factory=list)
    estado: str = "INGRESADO"

    def to_dict(self) -> dict[str, Any]:
        return {
            "expediente": self.expediente,
            "camara": self.camara,
            "url": self.url,
            "sumario": self.sumario,
            "fecha_ingreso": self.fecha_ingreso,
            "pdf_url": self.pdf_url,
            "giros": [g.__dict__ for g in self.giros],
            "movimientos": [m.__dict__ for m in self.movimientos],
            "estado": self.estado,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Inferencia de estado (conservadora, sobre el texto de los movimientos)
# ─────────────────────────────────────────────────────────────────────────────

# Orden de "avance": el estado final es el más avanzado que se detecte.
_PRIORIDAD = {
    "INGRESADO": 0,
    "EN_COMISION": 1,
    "CON_DICTAMEN": 2,
    "MEDIA_SANCION": 3,
    "SANCIONADO": 4,
    "RECHAZADO": 4,
    "RETIRADO": 5,
}


def inferir_estado(giros: list[Giro], movimientos: list[Movimiento]) -> str:
    """Devuelve el estado más avanzado detectado. Defensivo: ante la duda, el
    estado más conservador (no inventa una media sanción que no esté escrita)."""
    estado = "INGRESADO"
    if giros:
        estado = "EN_COMISION"

    def texto(m: Movimiento) -> str:
        return _strip_tildes(f"{m.descripcion} {m.resultado or ''}").upper()

    for m in movimientos:
        t = texto(m)
        cand = None
        if "RETIR" in t:
            cand = "RETIRADO"
        elif "MEDIA SANCION" in t or "MEDIA-SANCION" in t:
            # Chequear ANTES que "SANCION" a secas: "media sanción" no es sanción definitiva.
            cand = "MEDIA_SANCION"
        elif "SANCION DEFINITIVA" in t or "SANCIONADO" in t or "SANCION " in t:
            cand = "SANCIONADO"
        elif "RECHAZAD" in t or "RECHAZO" in t:
            cand = "RECHAZADO"
        elif "DICTAMEN" in t or "ORDEN DEL DIA" in t:
            cand = "CON_DICTAMEN"
        if cand and _PRIORIDAD[cand] > _PRIORIDAD[estado]:
            estado = cand
    return estado


# ─────────────────────────────────────────────────────────────────────────────
# Parsing — anclado en el texto de los encabezados (resistente a cambios de CSS)
# ─────────────────────────────────────────────────────────────────────────────

def _check_no_bloqueo(html_text: str) -> None:
    low = (html_text or "").lower()
    if len(low) < 800 or any(m in low for m in _MARCADORES_BLOQUEO):
        raise FuenteSospechosa("respuesta vacía o con muro anti-bot")


def _tabla_por_caption(soup, patron: str):
    """Busca una <table> cuyo caption/encabezado contenga `patron` (sin tildes)."""
    rx = re.compile(_strip_tildes(patron), re.IGNORECASE)
    for tabla in soup.find_all("table"):
        cap = tabla.find("caption")
        cap_txt = _strip_tildes(cap.get_text()) if cap else ""
        # Algunos sitios ponen el título en un <th> o en un <h*> previo.
        if rx.search(cap_txt):
            return tabla
    # Fallback: encabezado (h2/h3/h4/strong) seguido de tabla.
    rx2 = re.compile(_strip_tildes(patron), re.IGNORECASE)
    for h in soup.find_all(["h2", "h3", "h4", "strong", "b"]):
        if rx2.search(_strip_tildes(h.get_text())):
            t = h.find_next("table")
            if t is not None:
                return t
    return None


def parse_senado(html_text: str, expediente: str, url: str) -> Seguimiento:
    from bs4 import BeautifulSoup

    _check_no_bloqueo(html_text)
    soup = BeautifulSoup(html_text, "html.parser")
    seg = Seguimiento(expediente=expediente, camara="senado", url=url)

    # Sumario / extracto: primera tabla con encabezado "Extracto".
    cab = _tabla_por_caption(soup, "Extracto") or soup.find("table")
    if cab is not None:
        filas = cab.find_all("tr")
        if len(filas) >= 2:
            celdas = [_norm(td.get_text()) for td in filas[1].find_all(["td", "th"])]
            if celdas:
                seg.sumario = celdas[-1][:400]

    # Giros a comisiones (trae fechas de ingreso/egreso y orden de giro).
    gt = _tabla_por_caption(soup, "Giros del Expediente a Comisiones")
    if gt is not None:
        for tr in gt.find_all("tr")[1:]:
            tds = [_norm(td.get_text()) for td in tr.find_all("td")]
            if not tds or not tds[0]:
                continue
            comision_raw = tds[0]
            orden = None
            mo = re.search(r"ORDEN DE GIRO:\s*(\d+)", _strip_tildes(comision_raw), re.I)
            if mo:
                orden = int(mo.group(1))
            comision = _norm(re.split(r"ORDEN DE GIRO", comision_raw, flags=re.I)[0])
            seg.giros.append(Giro(
                comision=comision,
                orden=orden,
                fecha_ingreso=tds[1] if len(tds) > 1 and tds[1] else None,
                fecha_egreso=tds[2] if len(tds) > 2 and tds[2] else None,
            ))

    # Fecha de ingreso a Mesa de Entradas.
    me = _tabla_por_caption(soup, "Mesa de Entradas")
    if me is not None:
        for tr in me.find_all("tr")[1:]:
            tds = [_norm(td.get_text()) for td in tr.find_all("td")]
            if tds and re.match(r"\d{2}-\d{2}-\d{4}", tds[0] or ""):
                seg.fecha_ingreso = tds[0]
                break

    # Trámite legislativo (si ya avanzó).
    tl = _tabla_por_caption(soup, "Tramite Legislativo")
    if tl is not None:
        for tr in tl.find_all("tr")[1:]:
            tds = [_norm(td.get_text()) for td in tr.find_all("td")]
            if not any(tds):
                continue
            seg.movimientos.append(Movimiento(
                camara="senado",
                descripcion=" ".join(t for t in tds if t)[:300],
            ))

    # PDF del texto original: link cuyo href termina en /downloadPdf.
    a = soup.find("a", href=re.compile(r"downloadPdf", re.I))
    if a and a.get("href"):
        href = a["href"]
        seg.pdf_url = href if href.startswith("http") else BASE_SEN + href

    seg.estado = inferir_estado(seg.giros, seg.movimientos)
    return seg


def parse_diputados(html_text: str, expediente: str, url: str) -> Seguimiento:
    from bs4 import BeautifulSoup

    _check_no_bloqueo(html_text)
    soup = BeautifulSoup(html_text, "html.parser")
    seg = Seguimiento(expediente=expediente, camara="diputados", url=url)

    # Sumario.
    m = re.search(r"Sumario:\s*(.+)", soup.get_text("\n"), re.I)
    if m:
        seg.sumario = _norm(m.group(1))[:400]
    # Fecha.
    mf = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", soup.get_text(" "), re.I)
    if mf:
        seg.fecha_ingreso = mf.group(1)

    # Giro a comisiones (Diputados marca "(Primera Competencia)", sin fechas).
    gt = _tabla_por_caption(soup, "Giro a comisiones")
    if gt is not None:
        for tr in gt.find_all("tr")[1:]:
            tds = [_norm(td.get_text()) for td in tr.find_all("td")]
            if not tds or not tds[0]:
                continue
            raw = tds[0]
            pc = "PRIMERA COMPETENCIA" in _strip_tildes(raw).upper()
            comision = _norm(re.split(r"\(?Primera Competencia\)?", raw, flags=re.I)[0])
            seg.giros.append(Giro(comision=comision, primera_competencia=pc))

    # Trámite: tabla Cámara | Movimiento | Fecha | Resultado.
    tt = _tabla_por_caption(soup, "Tramite")
    if tt is not None:
        for tr in tt.find_all("tr")[1:]:
            tds = [_norm(td.get_text()) for td in tr.find_all("td")]
            if len(tds) < 2 or not any(tds):
                continue
            seg.movimientos.append(Movimiento(
                camara=tds[0] if tds[0] else "diputados",
                descripcion=tds[1] if len(tds) > 1 else "",
                fecha=tds[2] if len(tds) > 2 and tds[2] else None,
                resultado=tds[3] if len(tds) > 3 and tds[3] else None,
            ))

    # PDF: "Ver documento original" → detalle_tp_adjunto.
    a = soup.find("a", href=re.compile(r"detalle_tp_adjunto", re.I))
    if a and a.get("href"):
        seg.pdf_url = a["href"]

    seg.estado = inferir_estado(seg.giros, seg.movimientos)
    return seg


# ─────────────────────────────────────────────────────────────────────────────
# Descarga (red) — separada del parsing para poder testear el parsing sin red
# ─────────────────────────────────────────────────────────────────────────────

def _fetch(url: str, scraper=None) -> str:
    """GET con backoff. `scraper` opcional (cloudscraper) para el Senado, que a
    veces tiene muro anti-bot; si no se pasa, usa requests con reintentos."""
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(4),
           wait=wait_exponential(multiplier=1, min=2, max=20),
           reraise=True)
    def _go() -> str:
        cliente = scraper
        if cliente is None:
            import requests
            cliente = requests
        r = cliente.get(url, timeout=HTTP_TIMEOUT,
                        headers={"User-Agent": "Mozilla/5.0 (NowcastCongreso)"})
        r.raise_for_status()
        return r.text

    return _go()


def seguir(expediente: str, *, slug_autor: str | None = None, scraper=None,
           html_text: str | None = None) -> Seguimiento:
    """Punto de entrada. Devuelve un Seguimiento.

    - `expediente`: 'NNNN-D-AAAA' (Diputados) o 'S-NNNN/AA' / 'NNNN/AA' (Senado).
    - `slug_autor`: requerido SOLO para Diputados (viene del dataset de parlamentarios).
    - `scraper`: cliente HTTP opcional (cloudscraper) para el Senado.
    - `html_text`: si se pasa, NO se hace red y se parsea ese HTML (para tests).
    """
    camara = detectar_camara(expediente)
    if camara == "senado":
        url = url_senado(expediente)
        html = html_text if html_text is not None else _fetch(url, scraper=scraper)
        return parse_senado(html, expediente, url)
    else:
        url = url_diputados(slug_autor or "", expediente)
        html = html_text if html_text is not None else _fetch(url, scraper=scraper)
        return parse_diputados(html, expediente, url)


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("uso: python seguidor_giros.py <expediente> [slug_autor]")
        raise SystemExit(2)
    exp = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else None
    seg = seguir(exp, slug_autor=slug)
    print(json.dumps(seg.to_dict(), ensure_ascii=False, indent=2))
