"""Ingesta Fase 0: votaciones nominales Diputados (periodos 129-137) desde CKAN HCDN.

Baja cabecera (una fila por acta/votacion) y detalle (una fila por diputado-voto),
los valida y guarda en parquet en data/clean.

Uso: python src/ingesta.py
"""
from __future__ import annotations

import io

import pandas as pd

from common import CLEAN, RAW, download_to, log

# Recursos CSV "PERIODOS 129 A 137" (historico completo).
RES_CABECERA = "28bdc184-d8e3-4d50-b5b5-e2151f902ac7"
RES_DETALLE = "262cc543-3186-401b-b35e-dcdb2635976d"

COLS_CAB_MIN = {"acta_id", "fecha", "titulo", "resultado", "tipo_mayoria", "base_mayoria"}
COLS_DET_MIN = {"acta_id", "diputado_nombre", "bloque", "distrito_nombre", "voto"}


def _read_csv(path) -> pd.DataFrame:
    """Lectura defensiva: detecta separador, tolera encoding latino."""
    raw = path.read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=enc)
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            log.warning("csv_read_retry", file=path.name, encoding=enc, error=str(exc))
    raise ValueError(f"No se pudo parsear {path.name} con utf-8 ni latin-1")


def _validate(df: pd.DataFrame, required: set, name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name}: faltan columnas requeridas {missing}")
    if df.empty:
        raise ValueError(f"{name}: dataframe vacio")


def main() -> None:
    cab_csv = download_to(RES_CABECERA, RAW / "cabecera_129_137.csv")
    det_csv = download_to(RES_DETALLE, RAW / "detalle_129_137.csv")

    cab = _read_csv(cab_csv)
    det = _read_csv(det_csv)
    _validate(cab, COLS_CAB_MIN, "cabecera")
    _validate(det, COLS_DET_MIN, "detalle")

    # Normalizacion defensiva de strings clave.
    for col in ("resultado", "tipo_mayoria", "base_mayoria"):
        cab[col] = cab[col].astype("string").str.strip()
    for col in ("bloque", "voto", "distrito_nombre", "diputado_nombre"):
        det[col] = det[col].astype("string").str.strip()
    det["voto"] = det["voto"].str.upper()
    cab["fecha"] = pd.to_datetime(cab["fecha"], errors="coerce")

    cab.to_parquet(CLEAN / "cabecera.parquet", index=False)
    det.to_parquet(CLEAN / "detalle.parquet", index=False)

    log.info(
        "ingesta_ok",
        actas=int(cab["acta_id"].nunique()),
        filas_detalle=len(det),
        rango_fechas=f"{cab['fecha'].min().date()}..{cab['fecha'].max().date()}",
        votos_distintos=sorted(det["voto"].dropna().unique().tolist()),
        bloques=int(det["bloque"].nunique()),
    )


if __name__ == "__main__":
    main()
