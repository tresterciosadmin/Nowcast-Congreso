"""Postura del gobierno por acta, y alineación de cada bloque con el gobierno.

EL PROBLEMA QUE RESUELVE (Valle, 2026-08-09)
--------------------------------------------
La dirección cruda del voto (AFIRMATIVO/NEGATIVO) NO es la postura política: en
un "Rechazo del DNU", votar AFIRMATIVO es ir CONTRA el gobierno. Ejemplo real:
Parrilli (kirchnerista) vota afirmativo la Ley de Movilidad Previsional —una
iniciativa opositora que Milei vetó—: afirmativo, pero oposición pura. Por eso
"share afirmativo" mezcla apoyar al gobierno con apoyar a la oposición y da
señales ambiguas (el kirchnerismo salía ~55% afirmativo, indistinguible).

LA SOLUCIÓN
    Para cada acta, definir QUÉ VOTA EL GOBIERNO PARA GANAR (`postura_gobierno`),
    combinando el tipo de moción con el origen del proyecto. Después, la señal
    que usa el modelo es la ALINEACIÓN de cada bloque con esa postura — estable y
    comparable entre cualquier tipo de acta.

    Medido en el Senado, era Milei (alineación con el gobierno):
      LLA 84% · PRO/Radicalismo 57% · OTRO/PROVINCIAL 47% (la BISAGRA) ·
      Peronismo Federal 28% · kirchnerismo 24% (oposición nítida).

TIPO DE MOCIÓN (por el título)
    RECHAZO_GOB : "Rechazo del decreto/DNU/facultades delegadas" -> el gobierno
                  quiere NEGATIVO (que no se rechace su acto).
    INSISTENCIA : "Insistencia" sobre un veto -> el gobierno quiere NEGATIVO.
    PROC        : mociones de orden, apartamientos, vueltas a comisión, homenajes
                  -> sin postura sustantiva (None; se excluyen).
    ESTANDAR    : aprobar un proyecto -> la postura sale del ORIGEN:
                  EJECUTIVO/OFICIALISMO -> AFIRMATIVO ; OPOSICION -> NEGATIVO ;
                  DESCONOCIDO -> None (no se sabe).

CONSUME (contratos): datos/canonica actas_canonico · variables/proyecto
    origen_por_acta.parquet (que ya trae el gobierno del día y PRO oficialista en
    Milei desde 2026-08-09).
PRODUCE (contrato): variables/proyecto/data/postura_gobierno_por_acta.parquet
    acta_id, motion, postura_gobierno  (postura ∈ {AFIRMATIVO, NEGATIVO, None})

CLI:  python variables/proyecto/src/postura_gobierno.py
Módulo: variables/proyecto · creado 2026-08-09 (reconstrucción por puertas).
Additivo; toca el módulo de Franco a pedido de Valle.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger("proyecto.postura_gobierno")

_RAIZ = Path(__file__).resolve().parents[3]
ACTAS = _RAIZ / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet"
ORIGEN = _RAIZ / "variables" / "proyecto" / "data" / "origen_por_acta.parquet"
OUT = _RAIZ / "variables" / "proyecto" / "data" / "postura_gobierno_por_acta.parquet"

_RE_RECHAZO_GOB = re.compile(r"RECHAZ.*(DECRETO|DNU|D\.N\.U|DELEGAD)", re.I)
_RE_INSIST = re.compile(r"INSIST", re.I)
_RE_PROC = re.compile(
    r"MOCI[OÓ]N DE ORDEN|APARTAMIENTO|VUELTA A COMISI|CUESTI[OÓ]N DE PRIVILEGIO"
    r"|HOMENAJE|PLAN DE LABOR|PREFERENCIA\b", re.I)

GOBIERNO_QUIERE = {"EJECUTIVO": "AFIRMATIVO", "OFICIALISMO": "AFIRMATIVO",
                   "ALIADOS": "AFIRMATIVO",  # bill de aliado: origen del lado del gobierno
                   "OPOSICION": "NEGATIVO"}


def tipo_mocion(titulo: object) -> str:
    """Clasifica la moción por el título. Default ESTANDAR (aprobar el proyecto)."""
    t = "" if titulo is None or (isinstance(titulo, float) and pd.isna(titulo)) else str(titulo)
    if _RE_RECHAZO_GOB.search(t):
        return "RECHAZO_GOB"
    if _RE_INSIST.search(t):
        return "INSISTENCIA"
    if _RE_PROC.search(t):
        return "PROC"
    return "ESTANDAR"


def postura_gobierno(motion: str, origen: object) -> Optional[str]:
    """Qué vota el gobierno para GANAR en esa acta. None si no aplica/no se sabe."""
    if motion in ("RECHAZO_GOB", "INSISTENCIA"):
        return "NEGATIVO"          # el gobierno no quiere que se rechace / se insista
    if motion == "PROC":
        return None                # procedimental: sin postura sustantiva
    return GOBIERNO_QUIERE.get(str(origen).upper()) if origen is not None else None


def construir(actas: pd.DataFrame, origen: pd.DataFrame) -> pd.DataFrame:
    faltan = {"acta_id", "titulo"} - set(actas.columns)
    if faltan:
        raise KeyError(f"actas sin columnas {faltan}")
    if "origen" not in origen.columns:
        raise KeyError("origen_por_acta sin columna 'origen'")
    cols = ["acta_id", "origen"] + (["gobierno"] if "gobierno" in origen.columns else [])
    df = actas[["acta_id", "titulo"]].merge(origen[cols], on="acta_id", how="left")
    df["motion"] = df["titulo"].map(tipo_mocion)
    df["postura_gobierno"] = [postura_gobierno(m, o)
                              for m, o in zip(df["motion"], df["origen"])]
    keep = ["acta_id", "motion", "postura_gobierno"]
    if "gobierno" in df.columns:
        keep.append("gobierno")
    return df[keep]


# --------------------------------------------------------------------------- #
# PROYECCIÓN DE LÍNEAS por ALINEACIÓN — el cierre de la Puerta D               #
# --------------------------------------------------------------------------- #
def _opuesto(postura: str) -> str:
    return "NEGATIVO" if postura == "AFIRMATIVO" else "AFIRMATIVO"


def proyectar_lineas_alineacion(
    votos: pd.DataFrame,
    fecha,
    camara: str,
    postura_por_acta: pd.DataFrame,
    postura_target: str,
    ventana_dias: int = 1095,
    min_actas: int = 2,
    k_shrink: float = 4.0,
    desvio_neutro: float = 0.15,
) -> list[dict]:
    """Línea proyectada de cada linaje para un voto en `fecha`/`camara`, vía
    ALINEACIÓN CON EL GOBIERNO (resuelve polaridad + era en un solo número).

    Cómo: se toma la ventana de actas ANTERIORES a `fecha`, **del MISMO gobierno**
    que la fecha objetivo (evita mezclar eras: un bloque que era oficialismo antes
    no contamina), con `postura_gobierno` definida. Por linaje se mide su
    ALINEACIÓN (fracción de actas donde su dirección coincidió con la del
    gobierno), encogida hacia 0.5 (neutral) por poca muestra. Luego, dado lo que
    el gobierno vota en el proyecto objetivo (`postura_target`):
        alineación > 0.5  -> el bloque vota con el gobierno  (postura_target)
        alineación < 0.5  -> vota en contra                  (lo opuesto)

    Devuelve [{bloque, linea, desvio, alineacion, n_actas}] para roster_nominal.
    """
    if postura_target not in ("AFIRMATIVO", "NEGATIVO"):
        raise ValueError(f"postura_target inválida: {postura_target!r}")
    fecha = pd.to_datetime(fecha)
    desde = fecha - pd.Timedelta(days=int(ventana_dias))

    pmap = dict(zip(postura_por_acta["acta_id"], postura_por_acta["postura_gobierno"]))
    gmap = (dict(zip(postura_por_acta["acta_id"], postura_por_acta["gobierno"]))
            if "gobierno" in postura_por_acta.columns else {})

    d = votos[(votos["camara"] == camara) &
              (votos["fecha"] < fecha) & (votos["fecha"] >= desde)].copy()
    d["pg"] = d["acta_id"].map(pmap)
    d = d[d["pg"].notna()]
    # MISMO gobierno que la fecha objetivo (la clave anti-era)
    if gmap:
        d["gob"] = d["acta_id"].map(gmap)
        gob_obj = _gobierno_de_fecha(fecha)
        if gob_obj is not None:
            d = d[d["gob"] == gob_obj]
    if d.empty:
        raise ValueError(f"sin actas con postura del mismo gobierno en "
                         f"[{desde.date()}, {fecha.date()}) para {camara}")

    d["v2"] = d["voto"].astype(str).str.upper().str[:2].map(
        {"AF": "AFIRMATIVO", "NE": "NEGATIVO"})
    # dirección del bloque POR ACTA = mayoría de sus votos emitidos
    da = (d[d["v2"].notna()]
          .groupby(["acta_id", "bloque_linaje"])
          .agg(af=("v2", lambda s: (s == "AFIRMATIVO").mean()),
               pg=("pg", "first"), n=("v2", "size")))
    da["dir"] = da["af"].map(lambda x: "AFIRMATIVO" if x >= 0.5 else "NEGATIVO")
    da["alineado"] = (da["dir"] == da["pg"]).astype(int)
    # desvío por acta = fracción del bloque que se aparta de su propia mayoría
    da["desvio_acta"] = da["af"].map(lambda x: min(x, 1 - x))

    out = []
    for linaje, g in da.groupby(level="bloque_linaje"):
        n = int(g["alineado"].size)
        if n < min_actas:
            continue
        alin_cruda = float(g["alineado"].mean())
        # encogimiento hacia 0.5 (neutral): pocas actas -> menos confianza
        alin = (n * alin_cruda + k_shrink * 0.5) / (n + k_shrink)
        linea = postura_target if alin > 0.5 else _opuesto(postura_target)
        out.append({
            "bloque": linaje,
            "linea": linea,
            "desvio": float(min(max(g["desvio_acta"].mean(), 0.0), 1.0)) or desvio_neutro,
            "alineacion": round(alin, 3),
            "n_actas": n,
        })
    return out


def _gobierno_de_fecha(fecha):
    """Nombre del gobierno vigente a la fecha, reutilizando las ventanas
    canónicas de origen_lider (no se define una 4ª copia de las fechas)."""
    try:
        from origen_lider import GOBIERNOS  # mismas ventanas
    except ImportError:
        return None
    nombres = ("KIRCHNER", "MACRI", "AF", "MILEI")
    f = pd.to_datetime(fecha, errors="coerce")
    if pd.isna(f):
        return None
    for (desde, hasta, _), nombre in zip(GOBIERNOS, nombres):
        if pd.Timestamp(desde) <= f < pd.Timestamp(hasta):
            return nombre
    return None


def alineacion_por_bloque(votos: pd.DataFrame, postura: pd.DataFrame,
                          linaje_col: str = "bloque_linaje") -> pd.DataFrame:
    """Fracción de votos de cada linaje que coinciden con la postura del gobierno.
    Es la señal estable: 0 = oposición dura, ~0.5 = bisagra, 1 = oficialismo."""
    mp = dict(zip(postura["acta_id"], postura["postura_gobierno"]))
    d = votos.copy()
    d["pg"] = d["acta_id"].map(mp)
    d["voto2"] = d["voto"].astype(str).str.upper().str[:2].map(
        {"AF": "AFIRMATIVO", "NE": "NEGATIVO"})
    d = d[d["pg"].notna() & d["voto2"].notna()]
    d["alineado"] = d["voto2"] == d["pg"]
    g = d.groupby(linaje_col)["alineado"].agg(n="size", alineacion="mean")
    return g.reset_index()


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    for p, q in ((ACTAS, "la canónica de actas"), (ORIGEN, "origen_por_acta")):
        if not p.exists():
            logger.error("falta %s: %s", q, p)
            return 2
    df = construir(pd.read_parquet(ACTAS), pd.read_parquet(ORIGEN))
    n_def = int(df["postura_gobierno"].notna().sum())
    logger.info("actas: %d | con postura_gobierno: %d (%.1f%%) | mociones: %s",
                len(df), n_def, 100 * n_def / len(df),
                df["motion"].value_counts().to_dict())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    logger.info("-> %s (%d filas)", args.out, len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
