# -*- coding: utf-8 -*-
"""FASE 1 de `coordinacion/PROMPT-CIERRE-DE-ETAPA.md` — cuánto pesa cada parte del
arreglo de la fuga del HARNESS, con todo lo demás fijo.

Parte del detalle del censo del 27-09 (`censo_detalle_paralelo.py`, harness con fuga):
ahí están, voto por voto, el share y el desvío del linaje que proyectó
`proyectar_postura`. La postura NO cambia entre brazos; sólo cambia qué cuenta como
historia del récord (`baseline_voto_individual.record_previo`, la misma función que usa
el harness):

    fila      shift(1) por fila — el harness hasta el 28-09 (tiene que dar `p` exacto)
    fecha     sólo fechas anteriores
    estricta  fechas anteriores y OTRA ley (el default desde el 28-09)

El récord se encoge hacia el share con la función del harness (`perfil`), igual que
en el censo. Métricas por voto; IC por bootstrap de Poisson sobre LEYES (ADR-0032).

La fuga del MOTOR (`<=` en `_alineacion_base`) no se mide acá: el harness de hoy no
usa esa función. Se mide en el censo nuevo (FASE 3), donde el harness sí la importa.

    python evaluacion/baseline/src/medir_fuga_historia.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_voto_individual import (REPO, HISTORIAS, _eras_de, ley_por_acta,  # noqa: E402
                                      perfil, record_previo)

logger = logging.getLogger("medir_fuga_historia")

DETALLE = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"
SALIDA = "evaluacion/baseline/outputs/medir_fuga_historia_2026-09-28.json"
N_BOOT = 300
SEED = 7
ERA_BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
            pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
ERA_LABELS = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


def skill(p, y) -> float:
    y = np.asarray(y, float)
    b = float(((np.asarray(p, float) - y) ** 2).mean())
    bb = float(((y.mean() - y) ** 2).mean())
    return 1 - b / bb if bb > 0 else float("nan")


def skill_ic_por_ley(p, y, ley, n_boot: int = N_BOOT, seed: int = SEED) -> list[float]:
    """IC 95% del skill re-muestreando LEYES enteras (Poisson). La climatología se
    recalcula en cada réplica con la tasa base de esa réplica."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    _, cod = np.unique(np.asarray(ley).astype(str), return_inverse=True)
    k = cod.max() + 1
    se = np.bincount(cod, (p - y) ** 2, k)
    sy = np.bincount(cod, y, k)
    n = np.bincount(cod, minlength=k).astype(float)
    W = np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)
    N, SY, SE = W @ n, W @ sy, W @ se
    base = SY / N
    brier_clim = base - base ** 2          # y binaria: mean((base-y)^2) = base(1-base)
    s = 1 - (SE / N) / brier_clim
    return [round(float(np.percentile(s, 2.5)), 4), round(float(np.percentile(s, 97.5)), 4)]


def resumen(d: pd.DataFrame, col: str) -> dict:
    y = d["y"].to_numpy(float)
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)
    out = {"global": {"n": int(len(d)), "skill": round(skill(d[col], y), 4),
                      "ic95_ley": skill_ic_por_ley(d[col], y, d["_ley"])}}
    for e in ERA_LABELS:
        m = (era == e).to_numpy()
        out[f"era={e}"] = {"n": int(m.sum()), "skill": round(skill(d.loc[m, col], y[m]), 4),
                           "ic95_ley": skill_ic_por_ley(d.loc[m, col], y[m], d.loc[m, "_ley"])}
    for c in ("diputados", "senado"):
        m = (d["camara"] == c).to_numpy()
        out[f"camara={c}"] = {"n": int(m.sum()), "skill": round(skill(d.loc[m, col], y[m]), 4)}
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar

    det = pd.read_parquet(REPO / DETALLE)
    votos = cargar()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")                       # el mismo orden que el harness
    leyes = ley_por_acta(REPO)
    v["_ley"] = v["acta_id"].astype(str).map(leyes)
    sin = v["_ley"].isna()
    v.loc[sin, "_ley"] = "acta:" + v.loc[sin, "acta_id"].astype(str)
    v["_era"] = _eras_de(v["fecha"])
    for h in HISTORIAS:
        n, a = record_previo(v, ["legislador_id", "_era"], h)
        v[f"n_{h}"] = n
        v[f"r_{h}"] = np.where(n > 0, a / np.maximum(n, 1), np.nan)

    cols = ["acta_id", "legislador_id", "_ley"] + [f"{x}_{h}" for h in HISTORIAS for x in "nr"]
    d = det.merge(v[cols].rename(columns={"legislador_id": "legislador"}),
                  on=["acta_id", "legislador"], how="left", validate="1:1")
    if d["n_fila"].isna().any():
        raise RuntimeError("votos del censo sin récord: el cruce con la canónica está roto")
    for h in HISTORIAS:
        d[f"p_{h}"] = [perfil(s, dv, r, n, True) for s, dv, r, n in
                       zip(d["share"], d["desvio"], d[f"r_{h}"], d[f"n_{h}"])]

    rep: dict = {"detalle": DETALLE, "n_votos": int(len(d)),
                 "votos_con_ley_conocida": round(float((~d["_ley"].str.startswith("acta:")).mean()), 4),
                 "actas_evaluadas": int(d["acta_id"].nunique()),
                 "leyes_evaluadas": int(d["_ley"].nunique())}
    dif = (d["p_fila"] - d["p"]).abs()
    rep["fila_reproduce_el_censo"] = {"max_abs": float(dif.max()), "frac_>1e-9": float((dif > 1e-9).mean())}
    if float(dif.max()) > 1e-9:
        logger.warning("historia='fila' NO reproduce el `p` del censo (max %.3g)", float(dif.max()))
    for h in HISTORIAS:
        rep[h] = resumen(d, f"p_{h}")
        rep[h]["fraccion_de_votos_con_record"] = round(float((d[f"n_{h}"] >= 1).mean()), 4)
    # cuántos votos pierden historia por cada corte
    rep["historia_media_por_voto"] = {h: round(float(d[f"n_{h}"].mean()), 1) for h in HISTORIAS}
    out = REPO / SALIDA
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({h: {k: rep[h][k] for k in ("global", "era=desde 2023")} for h in HISTORIAS},
                     ensure_ascii=False, indent=1))
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
