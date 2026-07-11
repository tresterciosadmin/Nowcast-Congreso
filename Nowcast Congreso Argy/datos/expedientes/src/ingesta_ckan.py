"""Ingesta masiva de PROYECTOS PRESENTADOS desde el CKAN de Diputados.

El registro de todo lo que entró al Congreso por Diputados (o en revisión),
con su cadena de vida: giros a comisión, dictámenes, movimientos, resultados
y leyes sancionadas. Es el DENOMINADOR del embudo, el insumo del enlace
acta→expediente y la semilla de la red de autorías (Módulos B/C).

Datasets (estado verificado 2026-07-11, ver Archivos_Borrar/expedientes_ckan/inventario.json):
  VIVOS (se actualizan ~mensual):  proyectos-parlamentarios, giro-a-comisiones,
    dictamenes, movimientos-de-proyectos, resultado-proyectos, leyes-sancionadas,
    comisiones (integrantes).
  CONGELADO (2019): expedientes períodos 129-137 = enlace acta_id↔expediente
    hecho por la propia HCDN (cubre las votaciones CKAN 2011-2019).

Salida (contrato estable, data/clean/):
  expedientes.parquet            proyecto_id, titulo, fecha_publicacion, publicacion_id,
                                 camara_origen, exp_diputados, exp_senado, tipo, autor
  expedientes_giros.parquet      proyecto_id, comision, orden
  expedientes_dictamenes.parquet proyecto_id, giro, orden, tipo, observaciones, numero, fecha
  expedientes_movimientos.parquet proyecto_id, fecha, movimiento, orden
  expedientes_resultados.parquet proyecto_id, cabecera, dictamen_tipo, od_numero,
                                 od_publicacion, fecha, resultado
  expedientes_leyes.parquet      proyecto_id, camara, tipo, numero, anio, fecha, ley
  acta_expediente.parquet        acta_id (formato canónico ckan_diputados:<id>),
                                 expediente, origen, anio, titulo, od
  comisiones_integrantes.parquet (nice-to-have para Committee Overlap)

LIMITACIÓN CONOCIDA: `autor` es solo el firmante PRIMARIO (el CKAN no publica
cofirmantes). La red completa de co-firmas es fase 2 (scraping dirigido o
datos/seguimiento en lote).

Correr en PC con internet (~75 MB de descarga la 1ª vez; caché en Archivos_Borrar):
  python datos/expedientes/src/ingesta_ckan.py
Variables: OUT=/dir  CACHE=/dir  REFRESH=1

Las 4 directivas de resiliencia: errores específicos, backoff en red,
parsing defensivo (columnas por nombre, tolerante a NA/filas rotas),
logging estructurado.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger("expedientes.ingesta")

CKAN = "https://datos.hcdn.gob.ar/api/3/action/"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/expedientes)"}
TIMEOUT = 180

# (dataset, nombre_recurso_contiene, archivo_cache)
RECURSOS = [
    ("proyectos-parlamentarios", "proyectos parlamentarios", "proyectos.csv"),
    ("giro-a-comisiones", "giro a comisiones", "giros.csv"),
    ("dictamenes", "dictamenes", "dictamenes.csv"),
    ("movimientos-de-proyectos", "movimientos", "movimientos.csv"),
    ("resultado-proyectos", "resultado proyectos", "resultados.csv"),
    ("leyes-sancionadas", "leyes sancionadas", "leyes.csv"),
    ("expedientes", "períodos 129 a 137", "acta_expediente.csv"),
    ("comisiones", "integrantes", "comisiones_integrantes.csv"),
]


def _get(url: str, **kw) -> requests.Response:
    ultimo = None
    for i in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kw)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            ultimo = e
            logger.warning("reintento %d %s (%s)", i + 1, url[:80], e)
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"GET {url}: {ultimo}")


def _url_recurso(dataset: str, contiene: str) -> str:
    pkg = _get(CKAN + "package_show", params={"id": dataset}).json()["result"]
    for res in pkg["resources"]:
        if res.get("format", "").upper() == "CSV" and contiene in (res.get("name") or "").lower():
            return res["url"]
    raise ValueError(f"{dataset}: no encontré recurso CSV con '{contiene}'")


def _descargar(dataset: str, contiene: str, destino: Path) -> Path:
    if destino.exists() and not os.environ.get("REFRESH"):
        logger.info("caché: %s", destino.name)
        return destino
    url = _url_recurso(dataset, contiene)
    logger.info("bajando %s <- %s", destino.name, url[:90])
    r = _get(url, stream=True)
    with destino.open("wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)
    return destino


def _csv(p: Path) -> pd.DataFrame:
    """Lectura defensiva: encoding con BOM, filas rotas se saltean y reportan."""
    df = pd.read_csv(p, dtype=str, encoding="utf-8-sig", engine="python",
                     on_bad_lines=lambda l: logger.warning("fila rota en %s (descartada)", p.name) or None)  # noqa: E731
    df.columns = [c.strip().lower().replace(" ", "_").replace("ó", "o").replace("í", "i") for c in df.columns]
    return df.replace({"NA": pd.NA, "": pd.NA})


def _fecha(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d")


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = Path(__file__).resolve()
    out = Path(os.environ.get("OUT", root.parents[1] / "data" / "clean"))
    cache = Path(os.environ.get("CACHE", root.parents[3] / "datos" / "Archivos_Borrar" / "expedientes_ckan"))
    out.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    crudos: dict[str, pd.DataFrame] = {}
    for dataset, contiene, nombre in RECURSOS:
        try:
            crudos[nombre] = _csv(_descargar(dataset, contiene, cache / nombre))
        except (RuntimeError, ValueError, pd.errors.ParserError) as e:
            logger.error("%s FALLÓ: %s (sigo con el resto)", nombre, e)

    # --- maestro ---
    p = crudos["proyectos.csv"].rename(columns={
        "proyecto_id": "proyecto_id", "titulo": "titulo",
        "publicacion_fecha": "fecha_publicacion", "publicacion_id": "publicacion_id",
        "camara_origen": "camara_origen", "exp_diputados": "exp_diputados",
        "exp_senado": "exp_senado", "tipo": "tipo", "autor": "autor"})
    p["fecha_publicacion"] = _fecha(p["fecha_publicacion"])
    p = p.dropna(subset=["proyecto_id"]).drop_duplicates("proyecto_id")
    p.to_parquet(out / "expedientes.parquet", index=False)

    # --- tablas de la cadena de vida (mismo id) ---
    tablas = {
        "giros.csv": ("expedientes_giros.parquet", {"comision": "comision", "orden": "orden"}),
        "dictamenes.csv": ("expedientes_dictamenes.parquet", None),
        "movimientos.csv": ("expedientes_movimientos.parquet", None),
        "resultados.csv": ("expedientes_resultados.parquet", None),
        "leyes.csv": ("expedientes_leyes.parquet", None),
        "comisiones_integrantes.csv": ("comisiones_integrantes.parquet", None),
    }
    for nombre, (salida, _) in tablas.items():
        if nombre not in crudos:
            continue
        df = crudos[nombre].rename(columns={"expediente": "proyecto_id", "expediente_id": "proyecto_id"})
        for c in df.columns:
            if c.startswith("fecha") or c.endswith("fecha") or c == "od_publicacion":
                df[c] = _fecha(df[c])
        df.to_parquet(out / salida, index=False)

    # --- enlace acta↔expediente (congelado 129-137), acta_id al formato canónico ---
    if "acta_expediente.csv" in crudos:
        ae = crudos["acta_expediente.csv"].dropna(subset=["acta_id", "expediente"])
        ae["acta_id"] = "ckan_diputados:" + ae["acta_id"].astype(str).str.strip()
        ae.drop_duplicates(["acta_id", "expediente"]).to_parquet(
            out / "acta_expediente.parquet", index=False)

    # --- reporte ---
    print(f"\nOK expedientes={len(p)}")
    anios = p["fecha_publicacion"].dropna().str[:4]
    if len(anios):
        print(f"  cobertura: {anios.min()} -> {anios.max()}")
        print("  por tipo:", p["tipo"].value_counts().head(6).to_dict())
    for nombre, (salida, _) in tablas.items():
        if nombre in crudos:
            print(f"  {salida}: {len(crudos[nombre]):,} filas")
    if "acta_expediente.csv" in crudos:
        print(f"  acta_expediente: {len(crudos['acta_expediente.csv']):,} filas (períodos 129-137)")
    # embudo grueso v1: proyectos de LEY presentados vs sancionados
    # (ojo: la tabla resultados tiene una fila por proyecto aunque resultado sea
    #  nulo; el dato duro es leyes-sancionadas. Rechazos explícitos casi no
    #  existen: el Congreso deja morir, no rechaza — eso ES el embudo.)
    if "leyes.csv" in crudos:
        leyes = p[p["tipo"].str.contains("LEY", na=False)]
        sanc = crudos["leyes.csv"]["proyecto_id"].nunique() if "proyecto_id" in crudos["leyes.csv"] else len(crudos["leyes.csv"])
        print(f"  EMBUDO v1: {len(leyes):,} proyectos de ley presentados -> "
              f"{sanc:,} sancionados = {100*sanc/max(len(leyes),1):.2f}%")


if __name__ == "__main__":
    main()
