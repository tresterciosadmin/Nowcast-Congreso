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
import csv
import re
from datetime import date
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
    """dd/mm/YYYY -> YYYY-MM-DD (formato del padron oficial). Si no existe, None.

    Valida contra el calendario (URGENTE 7, 04-09-2026): un "31/02/2026" armado
    a mano sale como "2026-02-31", y despues `pd.to_datetime(errors="coerce")`
    lo convierte en `NaT` EN SILENCIO. En este repo ese es el modo de fallar mas
    caro: no da error, da una columna vacia. `giros.py` ya lo hacia asi.
    """
    s = str(s).strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        try:
            return date(int(y), int(mo), int(d)).isoformat()
        except ValueError:
            return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    y, mo, d = m.groups()
    try:
        return date(int(y), int(mo), int(d)).isoformat()
    except ValueError:
        return None


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


# Cuanto puede ENCOGER una salida sin que el control la frene. 0,90 = se tolera
# perder hasta un 10%: bajas, renuncias y correcciones se mueven en ese orden.
# La corrida que motivo el control pasaba de 1.454 filas a 257 (-82%).
TOLERANCIA_ENCOGIMIENTO = 0.90
FLAG_ACHICAR = "--permitir-achicar"


def _filas_de_csv(ruta: Path) -> int:
    """Cuenta filas de datos de un CSV ya escrito, sin cargar pandas encima."""
    try:
        with ruta.open("r", encoding="utf-8-sig", newline="") as fh:
            return max(0, sum(1 for _ in csv.reader(fh)) - 1)
    except OSError:
        return 0


def control_de_encogimiento(salida: Path, filas_nuevas: int,
                            permitir: bool = False) -> str | None:
    """Devuelve el motivo por el que NO hay que escribir, o None si se puede.

    **Por que existe (URGENTE 3).** La entrada por defecto de este script es
    `data/raw/nomina_diputados.csv`, que tiene 257 filas: la foto vigente. La
    nomina acumulada, con 18 anios de mandatos, es `data/nomina_diputados.csv`
    y tiene 1.454. Correr el script sin argumentos pisaba el padron con las 257
    y **se llevaba puesta la historia, sin error ni aviso**. Se detecto el
    2026-08-22 comparando antes/despues, no porque algo fallara.

    Se eligio el control que se NIEGA a escribir por sobre corregir el default,
    y el motivo esta escrito en URGENTE: el mismo patron —dos archivos con el
    mismo nombre, contenido distinto, el pipeline toma uno y nadie se entera—
    aparecio DOS veces en el repo (aca y en el dump de La Decada Votada). Un
    default corregido arregla un caso; un control que puede decir que no
    arregla la forma de fallar.
    """
    if permitir or not salida.exists():
        return None
    filas_viejas = _filas_de_csv(salida)
    if filas_viejas == 0 or filas_nuevas >= filas_viejas * TOLERANCIA_ENCOGIMIENTO:
        return None
    return (f"la salida que voy a escribir tiene {filas_nuevas} filas y la que "
            f"esta en disco tiene {filas_viejas} "
            f"({filas_nuevas / filas_viejas:.0%} del original). NO escribo: casi "
            f"seguro estas corriendo con la nomina de `data/raw/` (la foto "
            f"vigente) en vez de la acumulada. El comando correcto suele ser:\n"
            f"    python datos/padron/src/ingesta_padron.py diputados "
            f"datos/padron/data/nomina_diputados.csv\n"
            f"Si de verdad querias achicarla, repetilo con {FLAG_ACHICAR}.")


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    argv = list(sys.argv[1:] if argv is None else argv)
    permitir_achicar = FLAG_ACHICAR in argv
    argv = [a for a in argv if a != FLAG_ACHICAR]
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
    motivo = control_de_encogimiento(salida, len(pad), permitir_achicar)
    if motivo:
        logger.error("%s", motivo)
        return 2
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
