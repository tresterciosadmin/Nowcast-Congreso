"""Ingesta del ICG (Índice de Confianza en el Gobierno, UTDT) — familia E del feature store.

Fuente primaria: página "Descarga de datos" del ICG
    https://www.utdt.edu/ver_contenido.php?id_contenido=17876&id_item_menu=28756
que publica el Excel "Evolución Mensual del ICG, 2001 - Presente". El nombre del
archivo (download.php?fname=_NNN.xls) CAMBIA con cada actualización mensual, por lo
que este script scrapea la página para encontrar el link vigente (mismo mecanismo
que el paquete R `opinAr` de PoliticaArgentina).

Fallback: microdatos .dta espejados en
    https://github.com/politicaargentina/data_warehouse/raw/master/opinAr/data_raw/icg.dta
(promediando el ICG por ola se reconstruye la serie mensual; puede estar desactualizado).

Salida (contrato): variables/proyecto/data/icg_mensual.csv
    columnas: fecha (YYYY-MM-01), anio, mes, icg (float, escala 0-5)

Uso:
    pip install -r requirements.txt   # requests, pandas, xlrd, (pyreadstat p/ fallback)
    python ingesta_icg.py             # serie completa: descarga el Excel y escribe el CSV
    python ingesta_icg.py ultimo      # actualización mensual liviana: scrapea la página
                                      # de INFORMES ("El ICG de junio fue de 2,07 puntos")
                                      # y agrega al CSV solo los meses que falten
    python ingesta_icg.py --fallback  # forzar la vía microdatos GitHub

Cita: Índice de Confianza en el Gobierno. Escuela de Gobierno.
Universidad Torcuato Di Tella. https://www.utdt.edu/icg
"""
from __future__ import annotations

import argparse
import io
import logging
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

LOG = logging.getLogger("ingesta_icg")

BASE = "https://www.utdt.edu"
PAGINA_DESCARGA = f"{BASE}/ver_contenido.php?id_contenido=17876&id_item_menu=28756"
PAGINA_INFORMES = f"{BASE}/ver_contenido.php?id_contenido=1439&id_item_menu=2964"
FALLBACK_DTA = (
    "https://github.com/politicaargentina/data_warehouse/raw/master/"
    "opinAr/data_raw/icg.dta"
)
SALIDA_DEFAULT = Path(__file__).resolve().parent.parent / "data" / "icg_mensual.csv"
# cache de crudos (régimen Archivos_Borrar: nada acá es fuente de verdad)
CACHE_DIR = (
    Path(__file__).resolve().parents[3] / "datos" / "Archivos_Borrar" / "icg_utdt"
)

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


class ICGError(Exception):
    """Error específico de la ingesta del ICG."""


def _get(url: str, intentos: int = 4, timeout: int = 60) -> requests.Response:
    """GET con backoff exponencial (directiva de resiliencia)."""
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "nowcast-congreso/1.0"})
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            ultimo = e
            espera = 2 ** i
            LOG.warning("GET %s falló (%s); reintento en %ss", url, e, espera)
            time.sleep(espera)
    raise ICGError(f"No se pudo descargar {url}: {ultimo}")


def encontrar_link_excel() -> str:
    """Scrapea la página de descarga y devuelve la URL vigente del .xls de la serie."""
    html = _get(PAGINA_DESCARGA).text
    # links tipo /download.php?fname=_177973895945919200.xls (el fname rota por mes)
    candidatos = re.findall(r'href="(/?download\.php\?fname=_[0-9]+\.xlsx?)"', html)
    if not candidatos:
        # a veces vienen con dominio absoluto
        candidatos = re.findall(
            r'href="https?://www\.utdt\.edu(/download\.php\?fname=_[0-9]+\.xlsx?)"', html
        )
    if not candidatos:
        raise ICGError(
            "La página de descarga no expone ningún .xls — ¿cambió el layout? "
            f"Revisar a mano: {PAGINA_DESCARGA}"
        )
    link = candidatos[0]
    if not link.startswith("/"):
        link = "/" + link
    LOG.info("Link vigente de la serie: %s", link)
    return BASE + link


def _normalizar_columna(c: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(c).strip().lower())


def parsear_excel(crudo: bytes) -> pd.DataFrame:
    """Normaliza el Excel de UTDT a (fecha, anio, mes, icg). Parsing defensivo.

    Layout REAL observado (2026-07): TRANSPUESTO y partido en dos hojas
    ('Evolución ICG 2001-2022' / 'Evolución ICG a partir de 2023'): una fila con
    las FECHAS (datetimes) y debajo una fila etiquetada 'ICG' con los valores
    (más una fila 'Variación ICG' que se ignora). Se soportan además, por si
    UTDT cambia el formato: largo (año/mes/icg en columnas) y ancho (filas=año,
    columnas=meses).
    """
    xl = pd.ExcelFile(io.BytesIO(crudo))
    piezas: list[pd.DataFrame] = []
    for hoja in xl.sheet_names:
        df = xl.parse(hoja, header=None)
        out = _extraer_transpuesto(df)
        if out is None:
            # layouts alternativos con encabezado por columnas
            for h in range(min(10, len(df))):
                fila = [_normalizar_columna(v) for v in df.iloc[h].tolist()]
                if any("icg" in v for v in fila) or any(k in fila for k in ("ano", "anio", "ao")):
                    out = _extraer(xl.parse(hoja, header=h))
                    if out is not None and len(out):
                        break
        if out is not None and len(out):
            piezas.append(out)
            LOG.info("hoja %r: %d meses", hoja, len(out))
    if not piezas:
        raise ICGError("No se reconoció el layout del Excel; revisar a mano el archivo cacheado")
    return _limpiar(pd.concat(piezas, ignore_index=True))


def _extraer_transpuesto(df: pd.DataFrame) -> pd.DataFrame | None:
    """Layout transpuesto: fila de fechas + fila 'ICG' con los valores."""
    import datetime as _dt

    def _es_fecha(v: object) -> bool:
        # SOLO datetimes nativos del Excel: un string "2002" o un float también
        # parsean con to_datetime y eligen la fila equivocada (bug visto en vivo)
        return isinstance(v, (pd.Timestamp, _dt.datetime, _dt.date))

    conteos = [(df.iloc[i].map(_es_fecha).sum(), i) for i in range(len(df))]
    mejor_n, fila_fechas = max(conteos)
    if mejor_n < 12:
        return None
    fechas = pd.to_datetime(
        df.iloc[fila_fechas].map(lambda v: v if _es_fecha(v) else None), errors="coerce"
    )
    # fila de valores: la siguiente etiquetada ICG (evitando 'variación')
    for j in range(fila_fechas + 1, min(fila_fechas + 6, len(df))):
        etiquetas = " ".join(_normalizar_columna(v) for v in df.iloc[j, :3].tolist())
        if "icg" in etiquetas and "variacion" not in etiquetas:
            valores = pd.to_numeric(df.iloc[j], errors="coerce")
            out = pd.DataFrame({"fecha_dt": fechas, "icg": valores}).dropna()
            if len(out) < 12:
                continue
            out["anio"] = out["fecha_dt"].dt.year
            out["mes"] = out["fecha_dt"].dt.month
            return out[["anio", "mes", "icg"]]
    return None


def _extraer(df: pd.DataFrame) -> pd.DataFrame | None:
    cols = {_normalizar_columna(c): c for c in df.columns}
    col_anio = next((cols[k] for k in cols if k in ("ano", "anio", "ao", "year")), None)
    col_mes = next((cols[k] for k in cols if k.startswith("mes") or k == "month"), None)
    col_icg = next((cols[k] for k in cols if "icg" in k or "indice" in k or "confianza" in k), None)

    # layout largo: año + mes + valor
    if col_anio is not None and col_mes is not None and col_icg is not None:
        out = df[[col_anio, col_mes, col_icg]].copy()
        out.columns = ["anio", "mes", "icg"]
        out["mes"] = out["mes"].map(
            lambda m: MESES.get(str(m).strip().lower(), None) if not str(m).strip().isdigit() else int(m)
        )
        return _limpiar(out)

    # layout ancho: filas=año, columnas=meses
    if col_anio is not None:
        meses_presentes = [c for c in df.columns if str(c).strip().lower() in MESES]
        if len(meses_presentes) >= 10:
            largo = df.melt(id_vars=[col_anio], value_vars=meses_presentes,
                            var_name="mes", value_name="icg")
            largo.columns = ["anio", "mes", "icg"]
            largo["mes"] = largo["mes"].map(lambda m: MESES[str(m).strip().lower()])
            return _limpiar(largo)

    # layout fecha única + valor
    col_fecha = next((cols[k] for k in cols if "fecha" in k or "date" in k or "periodo" in k), None)
    if col_fecha is not None and col_icg is not None:
        out = df[[col_fecha, col_icg]].copy()
        out.columns = ["fecha", "icg"]
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")
        out = out.dropna(subset=["fecha", "icg"])
        out["anio"] = out["fecha"].dt.year
        out["mes"] = out["fecha"].dt.month
        return _limpiar(out[["anio", "mes", "icg"]])
    return None


def _limpiar(out: pd.DataFrame) -> pd.DataFrame:
    out = out.dropna(subset=["anio", "mes", "icg"]).copy()
    out["anio"] = pd.to_numeric(out["anio"], errors="coerce")
    out["icg"] = pd.to_numeric(out["icg"], errors="coerce")
    out = out.dropna(subset=["anio", "mes", "icg"])
    out = out[(out["anio"] >= 2001) & (out["anio"] <= 2100)]
    out = out[(out["icg"] >= 0) & (out["icg"] <= 5)]  # escala documentada 0-5
    out["anio"] = out["anio"].astype(int)
    out["mes"] = out["mes"].astype(int)
    out["fecha"] = pd.to_datetime(dict(year=out["anio"], month=out["mes"], day=1))
    out = (
        out[["fecha", "anio", "mes", "icg"]]
        .drop_duplicates(subset=["fecha"])
        .sort_values("fecha")
        .reset_index(drop=True)
    )
    return out


def via_fallback() -> pd.DataFrame:
    """Reconstruye la serie mensual promediando los microdatos espejados en GitHub."""
    LOG.info("Vía fallback: microdatos .dta de data_warehouse (puede estar desactualizado)")
    crudo = _get(FALLBACK_DTA).content
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "icg_microdatos.dta").write_bytes(crudo)
    df = pd.read_stata(io.BytesIO(crudo))
    df.columns = [_normalizar_columna(c) for c in df.columns]
    col_anio = next((c for c in df.columns if c in ("ano", "anio", "ao", "year")), None)
    col_mes = next((c for c in df.columns if c.startswith("mes") or c == "month"), None)
    col_icg = next((c for c in df.columns if c == "icg" or "icg" in c), None)
    if not all((col_anio, col_mes, col_icg)):
        raise ICGError(f"Columnas inesperadas en microdatos: {list(df.columns)[:20]}")
    serie = (
        df.groupby([col_anio, col_mes])[col_icg].mean().reset_index()
        .rename(columns={col_anio: "anio", col_mes: "mes", col_icg: "icg"})
    )
    if not str(serie["mes"].iloc[0]).isdigit():
        serie["mes"] = serie["mes"].map(lambda m: MESES.get(str(m).strip().lower()))
    return _limpiar(serie)


def scrapear_informes(html: str | None = None) -> pd.DataFrame:
    """Extrae los ICG publicados en la página de INFORMES (texto de prensa).

    La página anuncia cada mes antes de que rote el Excel de la serie, con frases
    tipo "El ICG de junio fue de 2,07 puntos" (o, en informes viejos, "La medición
    de julio del ICG fue de 2,45 puntos") bajo un encabezado-link "Junio 2026".
    El año sale del encabezado MÁS CERCANO hacia atrás con el mismo mes.
    Devuelve DataFrame (fecha, anio, mes, icg) con lo que pudo parsear.
    """
    if html is None:
        r = _get(PAGINA_INFORMES)
        r.encoding = r.apparent_encoding or "iso-8859-15"
        html = r.text
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = re.sub(r"\s+", " ", texto)
    # los encabezados a veces vienen partidos por negritas ("Febrero 202" + "6"):
    texto = re.sub(r"(?<=\d) (?=\d)", "", texto)

    meses_re = "|".join(m for m in MESES if m != "setiembre")
    encabezados = [
        (m.start(), m.group(1).lower(), int(m.group(2)))
        for m in re.finditer(rf"\b({meses_re})\s*(?:de\s*)?(\d{{4}})\b", texto, re.I)
    ]
    patron_valor = re.compile(
        rf"(?:El ICG de|La medici\w+ de)\s+({meses_re})\s+(?:del ICG\s+)?fue de\s+([\d]+[.,]\d+)\s+puntos",
        re.I,
    )
    filas = []
    for m in patron_valor.finditer(texto):
        mes_nombre = m.group(1).lower()
        valor = float(m.group(2).replace(",", "."))
        # encabezado más cercano hacia atrás que mencione el mismo mes
        anio = next(
            (a for pos, mm, a in reversed(encabezados) if pos < m.start() and mm == mes_nombre),
            None,
        )
        if anio is None:
            LOG.warning("Informe de '%s' sin encabezado con año; se saltea", mes_nombre)
            continue
        filas.append({"anio": anio, "mes": MESES[mes_nombre], "icg": valor})
    if not filas:
        raise ICGError(
            f"No se pudo parsear ningún informe — ¿cambió la redacción? Revisar {PAGINA_INFORMES}"
        )
    return _limpiar(pd.DataFrame(filas))


def actualizar_ultimo(salida: Path) -> pd.DataFrame:
    """Modo liviano mensual: agrega a `salida` los meses de los informes que la
    serie todavía no tiene. No pisa valores existentes (el Excel oficial es más
    preciso: el informe redondea a 2 decimales)."""
    if not salida.exists():
        raise ICGError(f"No existe {salida}; corré primero la serie completa (sin argumentos)")
    base = pd.read_csv(salida, parse_dates=["fecha"])
    informes = scrapear_informes()
    nuevos = informes[informes["fecha"] > base["fecha"].max()]
    ult = informes.iloc[-1]
    LOG.info("Último informe publicado: %s = %.2f", ult["fecha"].strftime("%Y-%m"), ult["icg"])
    if nuevos.empty:
        LOG.info("La serie ya está al día (%s)", base["fecha"].max().strftime("%Y-%m"))
        print(f"Sin novedades: serie al día hasta {base['fecha'].max().strftime('%Y-%m')} "
              f"(último informe: {ult['fecha'].strftime('%Y-%m')} = {ult['icg']:.2f})")
        return base
    out = pd.concat([base, nuevos], ignore_index=True).sort_values("fecha").reset_index(drop=True)
    out.to_csv(salida, index=False, encoding="utf-8")
    for _, f in nuevos.iterrows():
        print(f"AGREGADO {f['fecha'].strftime('%Y-%m')}: ICG = {f['icg']:.2f}")
    LOG.info("Serie extendida a %s (%d meses)", out["fecha"].max().strftime("%Y-%m"), len(out))
    return out


def correr(salida: Path, forzar_fallback: bool = False) -> pd.DataFrame:
    if forzar_fallback:
        serie = via_fallback()
    else:
        try:
            url = encontrar_link_excel()
            crudo = _get(url).content
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            (CACHE_DIR / "icg_serie_mensual.xls").write_bytes(crudo)
            serie = parsear_excel(crudo)
        except ICGError as e:
            LOG.error("Vía primaria falló (%s); intento fallback GitHub", e)
            serie = via_fallback()

    # controles de sanidad
    if len(serie) < 250:  # nov-2001 → hoy son ~295 meses
        raise ICGError(f"Serie sospechosamente corta: {len(serie)} meses")
    huecos = pd.date_range(serie["fecha"].min(), serie["fecha"].max(), freq="MS").difference(serie["fecha"])
    if len(huecos):
        LOG.warning("Meses sin dato en la serie: %s", [d.strftime("%Y-%m") for d in huecos[:12]])

    salida.parent.mkdir(parents=True, exist_ok=True)
    serie.to_csv(salida, index=False, encoding="utf-8")
    LOG.info("OK: %d meses (%s → %s) escritos en %s", len(serie),
             serie["fecha"].min().strftime("%Y-%m"), serie["fecha"].max().strftime("%Y-%m"), salida)
    print(serie.tail(12).to_string(index=False))
    print("\n^ VALIDAR a ojo contra los informes de", "https://www.utdt.edu/ver_contenido.php?id_contenido=1439&id_item_menu=2964")
    print("  (jun-2026=2,07 / may-2026=1,99 / abr-2026=2,02 / mar-2026=2,30 según la página al 2026-07-11)")
    return serie


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("modo", nargs="?", choices=["serie", "ultimo"], default="serie",
                   help="serie = Excel completo 2001-hoy (default); "
                        "ultimo = scrapea la página de informes y agrega solo lo nuevo")
    p.add_argument("--out", type=Path, default=SALIDA_DEFAULT)
    p.add_argument("--fallback", action="store_true", help="forzar vía microdatos GitHub")
    args = p.parse_args()
    try:
        if args.modo == "ultimo":
            actualizar_ultimo(args.out)
        else:
            correr(args.out, forzar_fallback=args.fallback)
        return 0
    except ICGError as e:
        LOG.error("FALLO: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
