# -*- coding: utf-8 -*-
"""FASE 4.1 de `coordinacion/PROMPT-CIERRE-DE-ETAPA.md` (ADR-0034) — ¿de dónde salía el
11,06% que justificó prender RECORD_POR_TEMA?

Hay dos cosas mezcladas en ese número, y se separan acá:

  (a) la FUGA: `fase1_rec_por_tema.py` arma los récords con `shift(1)` por fila, que
      cuenta como historia los artículos anteriores de la MISMA ley, votados el mismo
      día — y comparten tema, así que el récord por área es justo el más expuesto.
  (b) el ESPEJO: compara contra un récord "general" que no es el del motor (sin guard
      de era, sin encoger hacia el bloque, sin origen).

Este script reproduce la metodología de `fase1_rec_por_tema.py` tal cual (mismos
filtros, misma combinación en logit, mismas confianzas) cambiando SÓLO la historia:
"fila" (tiene que dar 11,06%) contra "estricta" (fecha anterior y otra ley). Eso aísla
(a). La medición contra el motor —(a) y (b) arreglados— sale del censo:
`resumen_censo_limpio.py`, sección `record_por_tema`.

    python evaluacion/baseline/src/medir_record_por_tema_limpio.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_voto_individual import (REPO, ERA_BINS, ERA_LABELS,  # noqa: E402
                                      cargar_confianza_por_area, dif_brier_ic_por_ley,
                                      ley_por_acta)
from fase1_rec_por_tema import K_SHRINK, _areas_de  # noqa: E402
from medir_fuga_historia import record_previo  # noqa: E402

logger = logging.getLogger("medir_record_por_tema_limpio")
SALIDA = "evaluacion/baseline/outputs/medir_record_por_tema_limpio_2026-09-28.json"


def preparar(historia: str) -> pd.DataFrame:
    """La misma tabla que `fase1_rec_por_tema.preparar`, con la historia elegida."""
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar as cargar_bloque
    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha").reset_index(drop=True)          # el mismo orden que fase1
    leyes = ley_por_acta(REPO)
    v["_ley"] = v["acta_id"].astype(str).map(leyes)
    sin = v["_ley"].isna()
    v.loc[sin, "_ley"] = "acta:" + v.loc[sin, "acta_id"].astype(str)
    n, a = record_previo(v, ["legislador_id"], historia)
    v["rec_general"] = np.where(n > 0, a / np.maximum(n, 1), np.nan)

    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    tpa = tpa[["acta_id", "todas_ids"]].drop_duplicates("acta_id")
    v = v.merge(tpa, on="acta_id", how="left")
    v["areas"] = v["todas_ids"].map(_areas_de)
    v = v[v["areas"].map(len) > 0].dropna(subset=["rec_general"]).reset_index(drop=True)
    v["_voto_id"] = v.index

    vx = v[["_voto_id", "acta_id", "legislador_id", "fecha", "_ley", "areas", "af",
            "rec_general"]].explode("areas").rename(columns={"areas": "area"})
    vx = vx.sort_values(["legislador_id", "area", "fecha"])    # el mismo orden que fase1
    n, a = record_previo(vx, ["legislador_id", "area"], historia)
    r_area = np.where(n > 0, a / np.maximum(n, 1), vx["rec_general"].to_numpy(float))
    rg = vx["rec_general"].to_numpy(float)
    vx["rec_area_encogido"] = (n * r_area + K_SHRINK * rg) / (n + K_SHRINK)
    conf = cargar_confianza_por_area(REPO)
    vx["peso"] = [conf.get(str(x), {}).get(ar, 1.0) for x, ar in zip(vx["acta_id"], vx["area"])]
    # combinar_logit de fase1, vectorizado: sigmoid(Σ w·logit(s) / Σ w)
    s = np.clip(vx["rec_area_encogido"].to_numpy(float), 1e-9, 1 - 1e-9)
    vx["_wl"] = vx["peso"] * np.log(s / (1 - s))
    g = vx.groupby("_voto_id").agg(num=("_wl", "sum"), den=("peso", "sum"))
    comb = pd.Series(np.where(g["den"] > 0, 1 / (1 + np.exp(-(g["num"] / g["den"]))), np.nan),
                     index=g.index)
    v["rec_tema_combinado"] = v["_voto_id"].map(comb).fillna(v["rec_general"])
    return v


def _brier(p, y) -> float:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return float(((p - np.asarray(y, float)) ** 2).mean())


def resumen(d: pd.DataFrame) -> dict:
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)
    cortes = {"global": np.ones(len(d), bool),
              **{f"camara={c}": (d["camara"] == c).to_numpy() for c in ("diputados", "senado")},
              **{f"era={e}": (era == e).to_numpy() for e in ERA_LABELS}}
    out = {}
    for nom, m in cortes.items():
        bg, bt = _brier(d.loc[m, "rec_general"], d.loc[m, "af"]), _brier(d.loc[m, "rec_tema_combinado"], d.loc[m, "af"])
        r = dif_brier_ic_por_ley(np.clip(d.loc[m, "rec_tema_combinado"], 1e-6, 1 - 1e-6),
                                 np.clip(d.loc[m, "rec_general"], 1e-6, 1 - 1e-6),
                                 d.loc[m, "af"], d.loc[m, "_ley"])
        out[nom] = {"n": int(m.sum()), "brier_general": round(bg, 5), "brier_tema": round(bt, 5),
                    "mejora_relativa_%": round(100 * (1 - bt / bg), 2),
                    "ic95_dBrier_rel_%_ley": r["ic95_rel_%_ley"]}
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    rep: dict = {}
    tablas = {}
    for h in ("fila", "estricta"):
        logger.info("historia=%s ...", h)
        tablas[h] = preparar(h)
        rep[h] = {"subconjunto_propio": resumen(tablas[h])}
    # el mismo conjunto de votos para las dos historias
    k = ["acta_id", "legislador_id"]
    comun = tablas["fila"][k].merge(tablas["estricta"][k], on=k)
    for h in ("fila", "estricta"):
        rep[h]["subconjunto_comun"] = resumen(tablas[h].merge(comun, on=k))
    rep["n_comun"] = int(len(comun))
    rep["reproduce_11_06"] = rep["fila"]["subconjunto_propio"]["global"]["mejora_relativa_%"]
    out = REPO / SALIDA
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for h in ("fila", "estricta"):
        print(h, {c: rep[h]["subconjunto_comun"][c]["mejora_relativa_%"]
                  for c in ("global", "camara=diputados", "camara=senado", "era=desde 2023")})
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
