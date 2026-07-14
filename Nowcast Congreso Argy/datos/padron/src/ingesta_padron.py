"""datos/padron/src/ingesta_padron.py
Padron OFICIAL de bancas -- a nivel LEGISLADOR (no bloque).

Toma la nomina oficial (Apellido, Nombre, Distrito, IniciaMandato, FinalizaMandato,
Bloque) y produce el contrato padron_<camara>.csv: una fila por legislador-mandato,
con clave canonica (join con la canonica / voto_individual), distrito, bloque crudo,
bloque_norm, bloque_linaje (reusa datos/canonica/entity_resolution para ser
consistente) y mandato desde-hasta.

Es la "composicion de la camara a la fecha": para una fecha F, los legisladores con
desde <= F <= hasta son las bancas vigentes. Reemplaza el conteo por ventana movil
del proyector (que inflaba el roster con el recambio del 10-dic).

Uso:
  python datos/padron/src/ingesta_padron.py diputados [nomina.csv] [salida.csv]

4 directivas: errores especificos, parsing defensivo, logging estructurado.
(Sin I/O de red: la nomina se baja aparte; aca solo se normaliza.)
"""
from __future__ import annotations

import logging
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

logger = logging.getLogger("padron")

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[3]
_CANON_SRC = _ROOT / "datos" / "canonica" / "src"
if str(_CANON_SRC) not in sys.path:
    sys.path.insert(0, str(_CANON_SRC))
try:
    from entity_resolution import _name_key, _leg_id, _bloque_norm, _linaje_vec
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        f"no pude importar entity_resolution desde {_CANON_SRC}: {e}") from e

# alias de columnas (tolerante a mayus/acentos/espacios)
_ALIAS = {
    "apellido": "apellido", "nombre": "nombre",
    "distrito": "distrito", "provincia": "distrito",
    "iniciamandato": "desde", "inicia_mandato": "desde", "iniciomandato": "desde",
    "desde": "desde", "iniciodemandato": "desde",
    "finalizamandato": "hasta", "finaliza_mandato": "hasta", "finmandato": "hasta",
    "hasta": "hasta", "findemandato": "hasta",
    "designacionlegal": "desde", "designaciones": "desde",
    "ceselegal": "hasta", "cese": "hasta",
    "bloque": "bloque", "interbloque": "bloque",
    "leyenda": "nota", "nota": "nota",
    "legislador": "legislador", "senador": "legislador", "diputado": "legislador",
}


def _norm_col(c: str) -> str:
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
    k = re.sub(r"[^a-z]", "", c.lower())
    return _ALIAS.get(k, k)


def _fecha_iso(s) -> str | None:
    """dd/mm/YYYY -> YYYY-MM-DD (formato del padron oficial)."""
    s = str(s).strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return m.group(0) if m else None


def _limpiar_nombre(s: str) -> str:
    # arregla comillas internas mal escapadas ('Ernesto Pipi""')
    return re.sub(r'"+', "", str(s)).strip()


def cargar_nomina(ruta: Path) -> pd.DataFrame:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"no existe la nomina: {ruta}")
    df = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    df.columns = [_norm_col(c) for c in df.columns]
    # nombre completo: 'legislador' directo, o 'apellido' + 'nombre'
    if "legislador" in df.columns:
        df["legislador"] = df["legislador"].map(_limpiar_nombre)
    elif "apellido" in df.columns and "nombre" in df.columns:
        df["legislador"] = (df["apellido"].map(_limpiar_nombre) + ", "
                            + df["nombre"].map(_limpiar_nombre)).str.strip(", ")
    else:
        raise KeyError(f"la nomina no trae 'legislador' ni 'apellido'+'nombre': {list(df.columns)}")
    for req in ("bloque", "desde"):
        if req not in df.columns:
            raise KeyError(f"la nomina no trae columna '{req}'; tiene {list(df.columns)}")
    if "distrito" not in df.columns:
        df["distrito"] = ""
    if "hasta" not in df.columns:
        df["hasta"] = ""
    if "nota" not in df.columns:
        df["nota"] = ""
    return df


def construir_padron(df: pd.DataFrame, camara: str, fuente: str) -> pd.DataFrame:
    out = pd.DataFrame()
    out["legislador"] = df["legislador"]
    out["clave"] = df["legislador"].map(_name_key)
    out["legislador_id"] = out["clave"].map(_leg_id)
    out["camara"] = camara
    out["distrito"] = df["distrito"].str.strip()
    out["bloque"] = df["bloque"].str.strip()
    out["bloque_norm"] = out["bloque"].map(_bloque_norm)
    out["desde"] = df["desde"].map(_fecha_iso)
    out["hasta"] = df["hasta"].map(_fecha_iso)
    # linaje: consistente con la canonica; la fecha de referencia es el inicio de mandato
    out["bloque_linaje"] = _linaje_vec(out["bloque_norm"], pd.to_datetime(out["desde"], errors="coerce"))
    out["fuente"] = fuente
    out["nota"] = df["nota"].str.strip()

    # --- validaciones defensivas ---
    n0 = len(out)
    sin_fecha = out["desde"].isna().sum()
    if sin_fecha:
        logger.warning("%d filas sin fecha de inicio parseable", sin_fecha)
    dups = out["legislador_id"].duplicated().sum()
    if dups:
        logger.warning("%d legislador_id duplicados (posibles homonimos/reemplazos)", dups)
    logger.info("padron %s: %d legisladores", camara, n0)
    return out.sort_values(["bloque_linaje", "legislador"]).reset_index(drop=True)


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    argv = list(sys.argv[1:] if argv is None else argv)
    camara = argv[0] if argv else "diputados"
    data = _HERE.parents[1] / "data"
    default_in = data / "raw" / f"nomina_{camara}.csv"
    ruta = Path(argv[1]) if len(argv) > 1 else default_in
    salida = Path(argv[2]) if len(argv) > 2 else data / f"padron_{camara}.csv"
    fuente = f"oficial:nomina_{camara}"
    try:
        df = cargar_nomina(ruta)
        pad = construir_padron(df, camara, fuente)
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error("%s: %s", type(e).__name__, e)
        return 1
    salida.parent.mkdir(parents=True, exist_ok=True)
    pad.to_csv(salida, index=False, encoding="utf-8-sig")
    logger.info("-> %s (%d filas)", salida, len(pad))
    print("\n=== bancas por bloque_linaje ===")
    print(pad["bloque_linaje"].value_counts().to_string())
    print(f"\nTOTAL: {len(pad)}")
    # bloques crudos que cayeron a OTRO/PROVINCIAL (candidatos a revisar mapeo)
    otro = pad[pad["bloque_linaje"] == "OTRO / PROVINCIAL"]["bloque"].value_counts()
    if len(otro):
        print("\n=== bloques crudos -> OTRO / PROVINCIAL (revisar si alguno debe mapearse) ===")
        print(otro.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
