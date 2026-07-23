"""variables/proyecto - TEMA POR ACTA VOTADA (puente taxonomías → v2 de bloque).

Clasifica por TEXTO el TÍTULO de cada acta VOTADA (las de datos/expedientes/
acta_expediente.parquet, que sí traen un título DESCRIPTIVO del proyecto, a
diferencia del título del acta que sólo dice "expediente X, votación"). Produce el
contrato acta_id → tema que consume el v2 de variables/bloque para condicionar la
DIRECCIÓN del bloque al tema de la votación.

POR QUÉ ESTO Y NO EL BATCH DE 112k PDFs: para alimentar el v2 sólo hacen falta los
temas de las ~1.849 actas que EFECTIVAMENTE se votaron (el resto de expedientes
muere en comisión y no entra al agregador). Clasificar 1.849 títulos por TEXTO es
barato (Haiku, sin descargar PDFs) y directo. La corrida masiva de PDFs sigue su
curso aparte en el bot; esto es el subconjunto que desbloquea el v2 HOY.

CONSUME (contratos de otros módulos; no edita su código):
  datos/expedientes/data/clean/acta_expediente.parquet  (acta_id, titulo, expediente, origen, anio)
  variables/proyecto/src/agente_taxonomias.clasificar_texto  (interfaz pública del agente)
PRODUCE (contrato estable):
  variables/proyecto/data/tema_por_acta.parquet
    acta_id, expediente, tema_id, tema_area, confianza, todas_ids, via, clasificado_en

Idempotente (no reclasifica actas ya resueltas salvo --todos). Resiliente (un título
roto no corta el lote). Logging estructurado. La única parte que necesita red + API
key es la llamada al LLM dentro del agente; el resto corre offline y es testeable con
un clasificador inyectado.

4 directivas: errores específicos, backoff (lo aporta el SDK de la API en el agente),
parsing defensivo, logging estructurado.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger("proyecto.tema_por_acta")

_RAIZ = Path(__file__).resolve().parents[3]
DEFAULT_ACTA_EXP = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "acta_expediente.parquet"
DEFAULT_ACTAS_CANON = _RAIZ / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet"
OUT_DEFAULT = _RAIZ / "variables" / "proyecto" / "data" / "tema_por_acta.parquet"

# auxiliares: no son TEMA sustantivo (trámite/homenaje/sin clasificar) -> no sirven
# para condicionar la dirección política del bloque, pero se guardan igual.
_AUX_PREFIX = "AUX"


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Clasificador por defecto: la interfaz pública del agente (necesita API key)   #
# --------------------------------------------------------------------------- #
def _clasificador_agente() -> Callable[[str], list[tuple[str, float]]]:
    """Devuelve fn(titulo) -> [(tema_id, confianza), ...] usando el agente real.
    Import perezoso: sólo se necesita la API key cuando se llama de verdad."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agente_taxonomias import clasificar_texto  # type: ignore

    def _fn(titulo: str) -> list[tuple[str, float]]:
        res = clasificar_texto(titulo)
        return [(a.taxonomia_id, float(a.confianza)) for a in res.asignaciones]

    return _fn


def _elegir_primaria(asigs: list[tuple[str, float]]) -> tuple[Optional[str], Optional[str], Optional[float]]:
    """De las asignaciones, elige el TEMA primario: mayor confianza NO auxiliar.
    Si todas son auxiliares, devuelve la auxiliar de mayor confianza. Devuelve
    (tema_id, tema_area, confianza)."""
    if not asigs:
        return None, None, None
    sustantivas = [(i, c) for (i, c) in asigs if not str(i).startswith(_AUX_PREFIX)]
    pool = sustantivas or list(asigs)
    tema_id, conf = max(pool, key=lambda t: (t[1] if t[1] is not None else 0.0))
    area = str(tema_id).split(".")[0]
    return tema_id, area, conf


# --------------------------------------------------------------------------- #
# Carga del universo de actas votadas (contrato de expedientes)               #
# --------------------------------------------------------------------------- #
def cargar_actas(acta_exp: Path = DEFAULT_ACTA_EXP) -> pd.DataFrame:
    """Lee acta_expediente y devuelve las actas votadas con título utilizable.
    Una fila por acta_id (si un acta cruza varios expedientes, toma el título más largo,
    que suele ser el más descriptivo)."""
    acta_exp = Path(acta_exp)
    if not acta_exp.exists():
        raise FileNotFoundError(f"falta contrato de expedientes: {acta_exp}")
    df = pd.read_parquet(acta_exp)
    need = {"acta_id", "titulo"}
    faltan = need - set(df.columns)
    if faltan:
        raise KeyError(f"acta_expediente sin columnas {faltan}; hay {list(df.columns)}")
    df = df.copy()
    df["titulo"] = df["titulo"].astype("string").str.strip()
    df = df[df["titulo"].notna() & df["titulo"].str.len().ge(8)]
    if df.empty:
        raise ValueError("no hay actas con título utilizable")
    df["_len"] = df["titulo"].str.len()
    df = df.sort_values("_len", ascending=False).drop_duplicates("acta_id", keep="first")
    cols = [c for c in ("acta_id", "expediente", "titulo", "origen", "anio") if c in df.columns]
    return df[cols].reset_index(drop=True)


def cargar_actas_canonica(actas_canon: Path = DEFAULT_ACTAS_CANON,
                          desde_anio=None, hasta_anio=None) -> pd.DataFrame:
    """Fuente para actas RECIENTES: el título DESCRIPTIVO ya vive en la canónica
    (argentinadatos 2020+ trae título con el tema, a diferencia de las viejas que sólo
    referencian el expediente → por eso ésas van por acta_expediente/CKAN). Devuelve
    una fila por acta_id con título utilizable, filtrable por año."""
    actas_canon = Path(actas_canon)
    if not actas_canon.exists():
        raise FileNotFoundError(f"falta la canónica: {actas_canon}")
    df = pd.read_parquet(actas_canon)
    need = {"acta_id", "titulo"}
    faltan = need - set(df.columns)
    if faltan:
        raise KeyError(f"actas_canonico sin columnas {faltan}; hay {list(df.columns)}")
    df = df.copy()
    if "fecha" in df.columns:
        df["anio"] = pd.to_datetime(df["fecha"], errors="coerce").dt.year
    if desde_anio is not None and "anio" in df.columns:
        df = df[df["anio"] >= int(desde_anio)]
    if hasta_anio is not None and "anio" in df.columns:
        df = df[df["anio"] <= int(hasta_anio)]
    df["titulo"] = df["titulo"].astype("string").str.strip()
    df = df[df["titulo"].notna() & df["titulo"].str.len().ge(8)]
    df = df[~df["titulo"].str.lower().str.fullmatch(r"\(?sin ?t[ií]tulo\)?")]
    if df.empty:
        raise ValueError("no hay actas de la canónica con título utilizable en el rango")
    df["expediente"] = df.get("expediente")
    cols = [c for c in ("acta_id", "expediente", "titulo", "camara", "anio") if c in df.columns]
    return df.drop_duplicates("acta_id").reset_index(drop=True)[cols]


# --------------------------------------------------------------------------- #
# Batch                                                                        #
# --------------------------------------------------------------------------- #
def clasificar_actas(actas: pd.DataFrame,
                     clasificar: Optional[Callable[[str], list[tuple[str, float]]]] = None,
                     previas: Optional[pd.DataFrame] = None,
                     todos: bool = False,
                     limite: Optional[int] = None, out: Optional[Path] = None,
                     checkpoint_cada: int = 50) -> pd.DataFrame:
    """Clasifica cada acta por su título. Idempotente contra `previas` (no reclasifica
    salvo todos=True). Resiliente: un error por fila no corta el lote. Si `out` se pasa,
    hace CHECKPOINT cada `checkpoint_cada` clasificaciones (corrida larga a prueba de
    cortes). `clasificar` se inyecta en tests; por defecto usa el agente (API key)."""
    if clasificar is None:
        clasificar = _clasificador_agente()

    def _merge(base, filas_):
        nv = pd.DataFrame(filas_)
        if base is not None and not base.empty:
            b = base
            if todos and not nv.empty:
                b = b[~b["acta_id"].astype(str).isin(nv["acta_id"].astype(str))]
            return pd.concat([b, nv], ignore_index=True)
        return nv

    def _guardar(filas_):
        if out is None:
            return
        try:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            _merge(previas, filas_).to_parquet(out, index=False)
        except OSError as e:
            logger.warning("checkpoint no pudo escribir %s: %s", out, e)

    ya: set = set()
    if previas is not None and not previas.empty and "acta_id" in previas.columns and not todos:
        ya = set(previas["acta_id"].astype(str))

    pend = actas[~actas["acta_id"].astype(str).isin(ya)]
    if limite is not None:
        pend = pend.head(int(limite))
    logger.info("actas a clasificar: %d (ya resueltas: %d)", len(pend), len(ya))

    filas, ok, err = [], 0, 0
    for _, r in pend.iterrows():
        aid = str(r["acta_id"])
        titulo = str(r["titulo"])
        try:
            asigs = clasificar(titulo)
            tema_id, area, conf = _elegir_primaria(asigs)
            filas.append({
                "acta_id": aid,
                "expediente": r.get("expediente"),
                "tema_id": tema_id,
                "tema_area": area,
                "confianza": conf,
                "todas_ids": ";".join(i for i, _ in asigs) if asigs else None,
                "via": "texto",
                "clasificado_en": _ahora(),
            })
            ok += 1
            if out is not None and ok % int(checkpoint_cada) == 0:
                _guardar(filas)
                logger.info("checkpoint: %d clasificadas -> %s", ok, out)
        except Exception as e:  # resiliencia: seguir con el lote
            logger.warning("acta %s sin clasificar (%s): %s", aid, type(e).__name__, e)
            err += 1
    logger.info("clasificadas OK=%d, error=%d", ok, err)
    return _merge(previas, filas)


def _leer_previas(out: Path) -> Optional[pd.DataFrame]:
    if Path(out).exists():
        try:
            return pd.read_parquet(out)
        except Exception as e:
            logger.warning("no pude leer salida previa %s: %s", out, e)
    return None


def correr(acta_exp: Path = DEFAULT_ACTA_EXP, out: Path = OUT_DEFAULT,
           clasificar=None, todos: bool = False, limite: Optional[int] = None,
           fuente: str = "expedientes", desde_anio=None) -> pd.DataFrame:
    if fuente == "canonica":
        actas = cargar_actas_canonica(DEFAULT_ACTAS_CANON, desde_anio=desde_anio)
    else:
        actas = cargar_actas(acta_exp)
    previas = _leer_previas(out)
    res = clasificar_actas(actas, clasificar=clasificar, previas=previas,
                           todos=todos, limite=limite, out=out)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out, index=False)
    logger.info("tema_por_acta: %d filas -> %s", len(res), out)
    if "tema_area" in res.columns and not res.empty:
        top = res["tema_area"].value_counts().head(10).to_dict()
        logger.info("top áreas: %s", top)
    return res


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Clasifica el tema de cada acta votada por su título.")
    p.add_argument("--acta-exp", default=str(DEFAULT_ACTA_EXP))
    p.add_argument("--out", default=str(OUT_DEFAULT))
    p.add_argument("--limite", type=int, default=None, help="clasificar sólo N (prueba)")
    p.add_argument("--todos", action="store_true", help="reclasificar aunque ya estén")
    p.add_argument("--fuente", choices=["expedientes", "canonica"], default="expedientes",
                   help="expedientes = puente CKAN (viejas 2011-19); canonica = título del acta (recientes 2020+)")
    p.add_argument("--desde-anio", type=int, default=None, help="sólo actas desde ese año (fuente canonica)")
    args = p.parse_args(argv)
    try:
        correr(Path(args.acta_exp), Path(args.out), todos=args.todos, limite=args.limite,
               fuente=args.fuente, desde_anio=args.desde_anio)
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error("%s: %s", type(e).__name__, e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
