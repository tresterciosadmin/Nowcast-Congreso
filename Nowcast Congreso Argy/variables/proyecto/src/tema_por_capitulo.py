# -*- coding: utf-8 -*-
"""variables/proyecto — TEMA POR CAPÍTULO (FASE 2, `PROMPT-MULTITEMA-V2.md`,
insumo que le faltaba a `modelo/ensemble/src/composicion_capitulos.py`, ADR-0027).

POR QUÉ EXISTE
---------------
`composicion_capitulos.simular_capitulos` sabe componer P(proyecto) a partir de
la simulación de cada capítulo por separado — pero necesita, por capítulo, SU
PROPIO tema para condicionar la postura de bloque (`bloque.proyectar_postura`).
Hoy la clasificación es por PROYECTO ENTERO (`tema_por_proyecto.py`) o por ACTA
completa (`tema_por_acta.py`); ninguna baja al nivel capítulo. Este módulo cierra
esa falta, con el MISMO patrón barato ya usado dos veces (clasificar por TEXTO,
sin PDF, sin visión): acá el texto es el NOMBRE del capítulo
(`datos/expedientes/data/clean/capitulos_nombre.parquet`, addendum de ADR-0023),
con el `sumario` del proyecto como contexto para desambiguar nombres cortos
("Del régimen", "Disposiciones generales") que solos no alcanzan.

Alcance de la primera corrida (16-09-2026, con permiso explícito de Franco):
Ley Bases + los 145 proyectos de Diputados con votación en particular que ya
identificó B0 — el mismo universo que `capitulos_nombre.parquet` ya cubre, no
una descarga/clasificación nueva y más grande.

CONSUME (contratos existentes, no reimplementa nada):
  datos/expedientes/data/clean/capitulos_nombre.parquet  (archivo, proyecto_ids,
    capitulo_num, nombre_capitulo)
  datos/proyectos/data/proyectos.db (tabla proyectos, columna sumario — CONTEXTO,
    no se pisa: esa tabla no se toca)
  datos/expedientes/data/clean/expedientes.parquet (crosswalk proyecto_id<->denominador,
    vía `tema_por_proyecto.cargar_crosswalk`, no reimplementado)
  variables/proyecto/src/agente_taxonomias.clasificar_texto (interfaz pública del agente)
PRODUCE (contrato nuevo, NO toca `proyecto_taxonomias` ni el registro único —
  es una granularidad nueva, capítulo, que esas tablas no tienen):
  variables/proyecto/data/tema_por_capitulo.parquet
    proyecto_id, titulo_num, capitulo_num, nombre_capitulo, tema_id, tema_area,
    confianza, todas_ids, via, clasificado_en

  ⚠️ La CLAVE es (proyecto_id, titulo_num, capitulo_num), NO (proyecto_id,
  capitulo_num): el numeral de capítulo se REINICIA en cada título — ver
  `capitulos_nombre.extraer_capitulos` y ADR-0029 (bug real encontrado
  corriendo `composicion_capitulos` sobre Ley Bases, corregido el 16-09).

Idempotente (no reclasifica lo ya resuelto salvo --todos). Resiliente (un
nombre roto no corta el lote). Checkpoint cada N filas.

    python variables/proyecto/src/tema_por_capitulo.py clasificar
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger("proyecto.tema_por_capitulo")

_RAIZ = Path(__file__).resolve().parents[3]
DEFAULT_CAPITULOS = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "capitulos_nombre.parquet"
DEFAULT_DB = _RAIZ / "datos" / "proyectos" / "data" / "proyectos.db"
DEFAULT_EXPEDIENTES = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "expedientes.parquet"
OUT_DEFAULT = _RAIZ / "variables" / "proyecto" / "data" / "tema_por_capitulo.parquet"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tema_por_proyecto import cargar_crosswalk  # noqa: E402

_AUX_PREFIX = "AUX"


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _elegir_primaria(asigs: list[tuple[str, float]]):
    if not asigs:
        return None, None, None
    sustantivas = [(i, c) for (i, c) in asigs if not str(i).startswith(_AUX_PREFIX)]
    pool = sustantivas or list(asigs)
    tema_id, conf = max(pool, key=lambda t: (t[1] if t[1] is not None else 0.0))
    area = str(tema_id).split(".")[0]
    return tema_id, area, conf


def _clasificador_agente() -> Callable[[str], list[tuple[str, float]]]:
    """fn(texto) -> [(tema_id, confianza), ...]. Import perezoso: la API key
    sólo hace falta cuando se llama de verdad (mismo patrón que
    tema_por_acta.py/tema_por_proyecto.py — no se reimplementa)."""
    from agente_taxonomias import clasificar_texto  # type: ignore

    def _fn(texto: str) -> list[tuple[str, float]]:
        res = clasificar_texto(texto)
        return [(a.taxonomia_id, float(a.confianza)) for a in res.asignaciones]

    return _fn


def cargar_capitulos(capitulos_nombre: Path = DEFAULT_CAPITULOS) -> pd.DataFrame:
    """Una fila por (proyecto_id, titulo_num, capitulo_num) — NO por
    (proyecto_id, capitulo_num) solo: el numeral de capítulo se REINICIA en
    cada título (bug real encontrado el 16-09 corriendo `composicion_capitulos`
    sobre Ley Bases: "Capítulo I" aparece bajo 6 títulos distintos ahí, y
    agrupar sin el título fusionaba capítulos de partes DISTINTAS de la ley
    — ver `capitulos_nombre.extraer_capitulos` y ADR-0029). Explota
    `proyecto_ids` (una OD puede cubrir varios proyectos) y, cuando el mismo
    (proyecto, título, capítulo) tiene más de un nombre candidato (varias ODs
    del mismo proyecto — limitación honesta anotada en ADR-0023, addendum del
    16-09), se queda con el más LARGO."""
    c = pd.read_parquet(capitulos_nombre)
    if c.empty:
        raise ValueError(f"{capitulos_nombre} está vacío")
    if "titulo_num" not in c.columns:
        raise KeyError(
            f"{capitulos_nombre} no tiene 'titulo_num' — es una versión vieja del contrato "
            "(de antes del fix de ADR-0029); correr de nuevo "
            "datos/expedientes/src/capitulos_nombre.py (gratis, usa el caché de PDFs)")
    cx = c.assign(proyecto_id=c["proyecto_ids"].str.split(";")).explode("proyecto_id")
    cx["_len"] = cx["nombre_capitulo"].str.len()
    cx = (cx.sort_values("_len", ascending=False)
            .drop_duplicates(["proyecto_id", "titulo_num", "capitulo_num"], keep="first"))
    return cx[["proyecto_id", "titulo_num", "capitulo_num", "nombre_capitulo"]].reset_index(drop=True)


def _sumarios(proyecto_ids: list[str], db_path: Path, expedientes: Path) -> dict[str, str]:
    """proyecto_id (HCDN) -> sumario del proyecto (CONTEXTO para desambiguar
    nombres de capítulo cortos; None si no se puede resolver — degrada limpio,
    el capítulo se clasifica solo con su propio nombre)."""
    cruce = cargar_crosswalk(expedientes)
    denoms = {pid: cruce["pid_a_denom"].get(str(pid)) for pid in proyecto_ids}
    faltantes = [pid for pid, d in denoms.items() if d is None]
    if faltantes:
        logger.info("%d/%d proyecto_id sin denominador cruzado: sin contexto de sumario",
                    len(faltantes), len(proyecto_ids))
    denoms_validos = {d for d in denoms.values() if d}
    if not denoms_validos or not Path(db_path).exists():
        return {}
    con = sqlite3.connect(str(db_path))
    try:
        placeholders = ",".join("?" * len(denoms_validos))
        filas = con.execute(
            f"SELECT denominador, sumario FROM proyectos WHERE denominador IN ({placeholders})",
            list(denoms_validos)).fetchall()
    finally:
        con.close()
    sumario_por_denom = {d: s for d, s in filas if s}
    return {pid: sumario_por_denom[d] for pid, d in denoms.items()
           if d and d in sumario_por_denom}


def clasificar_capitulos(capitulos: pd.DataFrame,
                         clasificar: Optional[Callable[[str], list[tuple[str, float]]]] = None,
                         previas: Optional[pd.DataFrame] = None, todos: bool = False,
                         limite: Optional[int] = None, out: Optional[Path] = None,
                         checkpoint_cada: int = 25,
                         db_path: Path = DEFAULT_DB,
                         expedientes: Path = DEFAULT_EXPEDIENTES) -> pd.DataFrame:
    if clasificar is None:
        clasificar = _clasificador_agente()

    def _clave(df):
        return set(zip(df["proyecto_id"].astype(str), df["titulo_num"].astype(str),
                       df["capitulo_num"].astype(str)))

    ya = _clave(previas) if (previas is not None and not previas.empty and not todos) else set()
    capitulos = capitulos.copy()
    capitulos["_ya"] = list(zip(capitulos["proyecto_id"].astype(str),
                                capitulos["titulo_num"].astype(str),
                                capitulos["capitulo_num"].astype(str)))
    pend = capitulos[~capitulos["_ya"].isin(ya)]
    if limite is not None:
        pend = pend.head(int(limite))
    logger.info("capítulos a clasificar: %d (ya resueltos: %d)", len(pend), len(ya))

    sumarios = _sumarios(pend["proyecto_id"].unique().tolist(), db_path, expedientes)

    def _merge(base, filas_):
        nv = pd.DataFrame(filas_)
        if base is not None and not base.empty:
            b = base
            if todos and not nv.empty:
                clave_nv = _clave(nv)
                clave_b = list(zip(b["proyecto_id"].astype(str), b["titulo_num"].astype(str),
                                   b["capitulo_num"].astype(str)))
                b = b[[k not in clave_nv for k in clave_b]]
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

    filas, ok, err = [], 0, 0
    for _, r in pend.iterrows():
        pid = str(r["proyecto_id"])
        tit = str(r["titulo_num"]) if r["titulo_num"] is not None else None
        cap = str(r["capitulo_num"])
        nombre = str(r["nombre_capitulo"])
        contexto = sumarios.get(pid)
        capitulo_txt = f"Título {tit}, Capítulo {cap}" if tit else f"Capítulo {cap}"
        texto = f"{contexto} — {capitulo_txt}: {nombre}" if contexto else f"{capitulo_txt}: {nombre}"
        try:
            asigs = clasificar(texto)
            tema_id, area, conf = _elegir_primaria(asigs)
            filas.append({
                "proyecto_id": pid, "titulo_num": tit, "capitulo_num": cap, "nombre_capitulo": nombre,
                "tema_id": tema_id, "tema_area": area, "confianza": conf,
                "todas_ids": ";".join(i for i, _ in asigs) if asigs else None,
                "via": "texto", "clasificado_en": _ahora(),
            })
            ok += 1
            if out is not None and ok % int(checkpoint_cada) == 0:
                _guardar(filas)
                logger.info("checkpoint: %d clasificados -> %s", ok, out)
        except Exception as e:  # resiliencia: un capítulo roto no corta el lote
            logger.warning("capítulo %s (proyecto %s, título %s) sin clasificar (%s): %s",
                           cap, pid, tit, type(e).__name__, e)
            err += 1
    logger.info("clasificados OK=%d, error=%d", ok, err)
    return _merge(previas, filas)


def _leer_previas(out: Path) -> Optional[pd.DataFrame]:
    if Path(out).exists():
        try:
            return pd.read_parquet(out)
        except Exception as e:
            logger.warning("no pude leer salida previa %s: %s", out, e)
    return None


def correr(capitulos_nombre: Path = DEFAULT_CAPITULOS, out: Path = OUT_DEFAULT,
          clasificar=None, todos: bool = False, limite: Optional[int] = None,
          proyecto_id: Optional[str | list[str]] = None,
          db_path: Path = DEFAULT_DB, expedientes: Path = DEFAULT_EXPEDIENTES) -> pd.DataFrame:
    capitulos = cargar_capitulos(capitulos_nombre)
    if proyecto_id:
        ids = {proyecto_id} if isinstance(proyecto_id, str) else set(proyecto_id)
        capitulos = capitulos[capitulos["proyecto_id"].isin(ids)]
        if capitulos.empty:
            raise ValueError(f"proyecto_id={proyecto_id!r} no tiene ningún capítulo en "
                             f"{capitulos_nombre}")
    previas = _leer_previas(out)
    res = clasificar_capitulos(capitulos, clasificar=clasificar, previas=previas,
                               todos=todos, limite=limite, out=out,
                               db_path=db_path, expedientes=expedientes)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out, index=False)
    logger.info("tema_por_capitulo: %d filas -> %s", len(res), out)
    return res


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    apc = sub.add_parser("clasificar")
    apc.add_argument("--todos", action="store_true")
    apc.add_argument("--limite", type=int, default=None)
    apc.add_argument("--proyecto-id", default=None,
                     help="acota a uno o varios proyectos (HCDN...; separados por coma "
                          "para varios); sin esto, TODOS los capítulos pendientes del "
                          "universo (145 proyectos de B0)")
    args = ap.parse_args(argv)
    if args.cmd == "clasificar":
        pid = args.proyecto_id.split(",") if args.proyecto_id else None
        res = correr(todos=args.todos, limite=args.limite, proyecto_id=pid)
        print(f"{len(res)} filas -> {OUT_DEFAULT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
