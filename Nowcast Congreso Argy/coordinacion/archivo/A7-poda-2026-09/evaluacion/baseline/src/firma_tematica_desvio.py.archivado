# -*- coding: utf-8 -*-
"""Núcleo de `coordinacion/PROMPT-FIRMA-TEMATICA-DEL-DESVIO.md` (FASES 0-2).

Objeto: la FIRMA TEMÁTICA DEL DESVÍO. d_{i,k} = tasa de ruptura con la línea del bloque
del legislador i en actas disputadas del área k; se ENCOGE (EB, k=5) hacia el desvío del
propio legislador y se CENTRA (d~ = d_shrunk − d̄_i). Sin centrar sólo se recupera lealtad.

CERO GASTO DE API. NO TOCA EL MOTOR: sólo lee. El desvío es el v2 del motor
(`modelo/voto_individual/src/disciplina.py::marcar_desvios`), medido SÓLO estando
presente (desvío de conducta, no de ausentismo — ADR-0004).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("firma_tematica_desvio")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "modelo" / "voto_individual" / "src"))

K_SHRINK = 5.0
RECAMBIOS = ["2015-12-10", "2019-12-10", "2023-12-10"]
_AUX = "AUX"
MIN_MINORIA = 0.10   # "contestada": la minoría pesa >=10% de los emitidos (ver ADR: desvío del prompt)
CACHE = REPO / "Archivos_Borrar" / "firma_tematica_base.parquet"


def areas_de(todas_ids) -> list[str]:
    """Áreas (prefijo antes del '.') de `todas_ids`, sin AUX. Igual que ADR-0031."""
    if todas_ids is None or (isinstance(todas_ids, float) and pd.isna(todas_ids)):
        return []
    out: list[str] = []
    for i in str(todas_ids).split(";"):
        i = i.strip()
        if not i or i.upper().startswith(_AUX):
            continue
        a = i.split(".")[0].upper()
        if a not in out:
            out.append(a)
    return out


def era_de(fecha: pd.Series) -> pd.Series:
    """Índice de era: 0 = antes de 2015-12-10, 1 = 2015-19, 2 = 2019-23, 3 = 2023-hoy."""
    e = pd.Series(0, index=fecha.index)
    for r in RECAMBIOS:
        e += (fecha >= pd.Timestamp(r)).astype(int)
    return e


def construir_base(usar_cache: bool = False) -> pd.DataFrame:
    """Una fila por voto (con bloque): desvio, presente, disputada, areas, era."""
    if usar_cache and CACHE.exists():
        return pd.read_parquet(CACHE)
    import disciplina as dc
    src = REPO / "datos" / "canonica" / "data" / "clean"
    v, actas = dc.cargar(src)
    d = dc.marcar_desvios(v)
    disputadas = dc.actas_disputadas(actas, v)
    d["disputada"] = d["acta_id"].isin(disputadas)
    # "contestada" = hay desvío que medir (no unánime). La disputada estricta (±5%) deja
    # 92 actas con tema en toda la historia: sin muestra. Se reportan ambas.
    pres = d[d["presente"]]
    af = (pres["voto"] == "AFIRMATIVO").groupby(pres["acta_id"]).sum()
    ng = (pres["voto"] == "NEGATIVO").groupby(pres["acta_id"]).sum()
    minoria = (np.minimum(af, ng) / (af + ng).clip(lower=1))
    d["contestada"] = d["acta_id"].map(minoria).fillna(0) >= MIN_MINORIA
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    tpa = tpa[["acta_id", "todas_ids"]].drop_duplicates("acta_id")
    a2 = {r.acta_id: areas_de(r.todas_ids) for r in tpa.itertuples()}
    d["areas"] = d["acta_id"].map(a2)
    d["areas"] = d["areas"].map(lambda x: x if isinstance(x, list) else [])
    d = d[d["fecha"].notna()].copy()
    d["era"] = era_de(d["fecha"])
    cols = ["acta_id", "legislador_id", "camara", "fecha", "bloque_norm", "bloque_linaje",
            "voto", "presente", "desvio", "metodo", "disputada", "contestada", "areas", "era"]
    d = d[cols].reset_index(drop=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    d.assign(areas=d["areas"].map(";".join)).to_parquet(CACHE, index=False)
    return d


def cargar_base_cache() -> pd.DataFrame:
    d = pd.read_parquet(CACHE)
    d["areas"] = d["areas"].map(lambda s: s.split(";") if s else [])
    return d


def _filtrar(d: pd.DataFrame, filtro: str) -> pd.DataFrame:
    """filtro: 'contestada' (default del análisis), 'disputada' (±5%, estricta) o 'todas'."""
    if filtro not in ("contestada", "disputada", "todas"):
        raise ValueError(f"filtro desconocido: {filtro!r}")  # sin default silencioso
    x = d[d["presente"]]
    return x if filtro == "todas" else x[x[filtro]]


def celdas(d: pd.DataFrame, filtro: str = "contestada") -> pd.DataFrame:
    """Celdas (legislador, área, era): n actas y desvío medio, sobre presentes con área."""
    x = _filtrar(d, filtro)
    x = x[x["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
    return (x.groupby(["legislador_id", "area", "era"])["desvio"]
              .agg(n="size", d="mean").reset_index())


def totales(d: pd.DataFrame, filtro: str = "contestada") -> pd.DataFrame:
    """Desvío medio propio d̄_i por (legislador, era): sobre TODAS las actas del mismo
    conjunto (con o sin área) — es la referencia contra la que se encoge y se centra."""
    x = _filtrar(d, filtro)
    return x.groupby(["legislador_id", "era"])["desvio"].agg(n_tot="size", dbar="mean").reset_index()
