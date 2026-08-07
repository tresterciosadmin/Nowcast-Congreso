"""datos/expedientes/src/giros_iniciales.py
GIROS AL INGRESAR — la versión sin contaminar de `n_giros`.

Por qué existe (2026-08-07). `n_giros` es el rasgo más fuerte del embudo (coef.
1,35 / 1,45, y sacarlo cuesta −0,057 de skill), pero se contaba sobre
`expedientes_giros`, que es el **acumulado de hoy**, no el giro original. Una
parte de los proyectos recibe **ampliación de giro** después de presentado, y
esos avanzan 1,6x más que el resto: el rasgo miraba, para ellos, un pedacito del
futuro.

La auditoría del 07-08 mostró que el problema es **acotado, no estructural**:
91,8% de los proyectos conserva sus giros originales, y limpiar la contaminación
sube el skill de 0,3628 a 0,3641. O sea: no había que tirar el rasgo, había que
descontaminarlo. Este módulo hace eso.

DOS FUENTES, por orden de calidad:

  1. **TP del bot** (`datos/bot_recoleccion/.../tp_entradas.parquet`) — el giro tal
     como se publicó en el Trámite Parlamentario, o sea **medido al ingresar**.
     Es la fuente buena, pero sólo cubre lo que el bot vio (2026 en adelante).
     Se cuenta matcheando contra el catálogo de comisiones: el campo `giros` viene
     **sin separadores** ("ASUNTOS CONSTITUCIONALES LEGISLACION PENAL PRESUPUESTO
     Y HACIENDA" son tres) y partirlo por espacios o comas da cualquier cosa —
     ese error dio 82% de ampliación donde hay 8%.

  2. **Reconstrucción histórica** — giros de hoy menos las comisiones agregadas por
     "RESOLUCIÓN DE PRESIDENCIA - AMPLIACIÓN DE GIRO..." en `expedientes_movimientos`.
     Cubre todo el histórico pero depende de que el movimiento esté registrado
     (72.061 de 140.903 filas tienen `movimiento` nulo), así que **subestima**:
     mide 1,45% de ampliación contra el 8,0% que ve el bot en 2026.

Salida (contrato estable): `datos/expedientes/data/clean/giros_iniciales.parquet`
    proyecto_id · n_giros_inicial · n_giros_hoy · fuente ∈ {tp_bot, movimientos}

Lo consume `variables/embudo` como hook opcional: si el archivo existe, usa
`n_giros_inicial`; si no, sigue con el acumulado (contrato intacto).

Correr:  python datos/expedientes/src/giros_iniciales.py

4 directivas: errores específicos, parsing defensivo (catálogo por contenido, no
por posición), logging estructurado.
"""
from __future__ import annotations

import logging
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

logger = logging.getLogger("expedientes.giros_iniciales")

RAIZ = Path(__file__).resolve().parents[3]
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"
TP_BOT = RAIZ / "datos" / "bot_recoleccion" / "data" / "clean" / "tp_entradas.parquet"
SALIDA = CLEAN / "giros_iniciales.parquet"

_RE_AMPLIA = re.compile(r"AMPLIACION\s+DE\s+GIRO", re.I)


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return " ".join(s.split())


def catalogo(giros: pd.DataFrame) -> list[str]:
    """Nombres de comisión conocidos, del más largo al más corto.

    El orden importa: 'LEGISLACION GENERAL' debe consumirse antes que
    'LEGISLACION', o una comisión larga se contaría como dos.
    """
    return sorted({_norm(c) for c in giros["comision"].dropna().unique()},
                  key=len, reverse=True)


def contar_en_texto(texto, cat: list[str]) -> int:
    """Cuántas comisiones del catálogo aparecen en un string sin separadores.

    Va consumiendo cada match para no contar dos veces un nombre contenido en otro.
    """
    t = _norm(texto)
    if not t:
        return 0
    n = 0
    for c in cat:
        if c and c in t:
            t = t.replace(c, " ")
            n += 1
    return n


def _desde_tp(cat: list[str], exp: pd.DataFrame) -> pd.DataFrame:
    """Giro medido al ingresar, desde el TP que capturó el bot."""
    if not TP_BOT.exists():
        logger.info("sin %s: no hay medición directa del giro inicial", TP_BOT.name)
        return pd.DataFrame(columns=["proyecto_id", "n_giros_inicial", "fuente"])
    tp = pd.read_parquet(TP_BOT)
    if not {"expediente", "giros"} <= set(tp.columns):
        logger.warning("tp_entradas sin las columnas esperadas; lo salteo")
        return pd.DataFrame(columns=["proyecto_id", "n_giros_inicial", "fuente"])
    tp = tp.dropna(subset=["expediente"]).copy()
    tp["n_giros_inicial"] = tp["giros"].map(lambda s: contar_en_texto(s, cat))
    tp = tp[tp["n_giros_inicial"] > 0]
    j = tp.merge(exp[["exp_diputados", "proyecto_id"]],
                 left_on="expediente", right_on="exp_diputados", how="inner")
    j = j.drop_duplicates("proyecto_id")
    logger.info("TP del bot: %d proyectos con giro medido al ingresar", len(j))
    return j.assign(fuente="tp_bot")[["proyecto_id", "n_giros_inicial", "fuente"]]


def _desde_movimientos(mov: pd.DataFrame, cat: list[str],
                       n_hoy: pd.Series) -> pd.DataFrame:
    """Reconstrucción: giros de hoy menos los agregados por ampliación."""
    if mov.empty or "movimiento" not in mov.columns:
        return pd.DataFrame(columns=["proyecto_id", "n_giros_inicial", "fuente"])
    amp = mov[mov["movimiento"].astype(str).str.contains(_RE_AMPLIA, na=False)].copy()
    if amp.empty:
        return pd.DataFrame(columns=["proyecto_id", "n_giros_inicial", "fuente"])
    # cuántas comisiones agrega cada resolución (puede nombrar más de una).
    # "SE SUPRIME EL GIRO A..." resta: esas comisiones ya no están en el acumulado
    # de hoy, así que no hay que descontarlas -> se corta el texto antes.
    amp["agregadas"] = amp["movimiento"].map(
        lambda s: contar_en_texto(re.split(r"SE SUPRIME", str(s), flags=re.I)[0], cat))
    agg = amp.groupby("proyecto_id")["agregadas"].sum()
    agg = agg[agg > 0]
    ini = (n_hoy.reindex(agg.index).fillna(0) - agg).clip(lower=1).astype(int)
    logger.info("movimientos: %d proyectos con ampliación de giro registrada", len(ini))
    return pd.DataFrame({"proyecto_id": ini.index, "n_giros_inicial": ini.values,
                         "fuente": "movimientos"})


def construir() -> pd.DataFrame:
    for f in ("expedientes.parquet", "expedientes_giros.parquet"):
        if not (CLEAN / f).exists():
            raise FileNotFoundError(f"falta {CLEAN / f}; correr la ingesta de expedientes")
    exp = pd.read_parquet(CLEAN / "expedientes.parquet")
    giros = pd.read_parquet(CLEAN / "expedientes_giros.parquet")
    try:
        mov = pd.read_parquet(CLEAN / "expedientes_movimientos.parquet")
    except (OSError, ValueError) as e:
        logger.warning("no pude leer movimientos (%s): sigo solo con el TP", e)
        mov = pd.DataFrame()

    cat = catalogo(giros)
    logger.info("catálogo de comisiones: %d nombres", len(cat))
    n_hoy = giros.groupby("proyecto_id").size()

    tp = _desde_tp(cat, exp)
    hist = _desde_movimientos(mov, cat, n_hoy)
    # el TP gana: es medición, no reconstrucción
    out = pd.concat([tp, hist[~hist["proyecto_id"].isin(set(tp["proyecto_id"]))]],
                    ignore_index=True)
    out["n_giros_hoy"] = out["proyecto_id"].map(n_hoy).fillna(0).astype(int)
    out["n_giros_inicial"] = out["n_giros_inicial"].astype(int).clip(lower=1)
    # nunca puede haber MÁS giros al ingresar que hoy (salvo supresiones, raras)
    excede = (out["n_giros_inicial"] > out["n_giros_hoy"]).sum()
    if excede:
        logger.info("%d proyectos con inicial > hoy (supresión de giro): los dejo como vienen", excede)
    return out[["proyecto_id", "n_giros_inicial", "n_giros_hoy", "fuente"]]


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    out = construir()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SALIDA, index=False)
    cambian = (out["n_giros_inicial"] != out["n_giros_hoy"]).sum()
    print(f"\ngiros iniciales: {len(out)} proyectos "
          f"({cambian} con giro distinto al de hoy)")
    print(out["fuente"].value_counts().to_string())
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
