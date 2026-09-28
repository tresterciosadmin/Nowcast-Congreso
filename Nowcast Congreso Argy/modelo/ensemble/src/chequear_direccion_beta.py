# -*- coding: utf-8 -*-
"""FASE 4.2-4.3 de `coordinacion/PROMPT-CIERRE-DE-ETAPA.md` (ADR-0034) — ¿el sesgo del
offset contaminado va en la dirección que dice el razonamiento?

El razonamiento: un offset que conoce parte de la respuesta deja menos residuo, así que
los coeficientes de los términos que se estiman ENCIMA de él (β, δ, θ, ψ) salen
atenuados: serían CONSERVADORES. No se pide re-estimarlos; esto es sólo el chequeo de
la dirección, sobre β (el único de los cuatro que está PRENDIDO).

Mismo panel (`estimar_beta_dictamen.construir_panel`: mismas actas, mismos F_i y
lealtad×jefe), misma especificación (M6, la de producción), tres offsets:

  - `p_motor` del panel         la copia que usó la estimación (shift(1), sin guard,
                                sin encoger, sin origen) — tiene que reproducir M6
  - `p` del censo del 27-09     el harness con fuga (shift(1), con guard y encogido)
  - `p` del censo del 28-09     el MOTOR con historia estricta (el limpio)

Si β sube con el offset limpio, el razonamiento se sostiene. Si baja, está mal y hay
que decirlo. NO cambia los coeficientes de producción.

    python modelo/ensemble/src/chequear_direccion_beta.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estimar_beta_dictamen import REPO, _logit, construir_panel  # noqa: E402

logger = logging.getLogger("chequear_direccion_beta")
NUEVO = "evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet"
VIEJO = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"
SALIDA = "modelo/ensemble/outputs/chequeo_direccion_beta_2026-09-28.json"


def m6(d: pd.DataFrame, col: str) -> dict:
    import statsmodels.api as sm
    X = sm.add_constant(d[["F_i", "lealtad_x_jefe"]].astype(float), has_constant="add")
    r = sm.GLM(d["y"].astype(float), X, family=sm.families.Binomial(),
               offset=_logit(d[col]).astype(float)).fit(cov_type="cluster",
                                                        cov_kwds={"groups": d["_ley"]})
    return {"n": int(r.nobs),
            "coef": {k: round(float(v), 4) for k, v in r.params.items()},
            "se_cluster_ley": {k: round(float(v), 4) for k, v in r.bse.items()}}


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    d = construir_panel()
    d["lealtad_x_jefe"] = (1 - d["d_i"]) * d["J_l"]
    nuevo = pd.read_parquet(REPO / NUEVO)[["acta_id", "legislador", "p", "ley"]].rename(
        columns={"legislador": "legislador_id", "p": "p_limpio", "ley": "_ley"})
    viejo = pd.read_parquet(REPO / VIEJO)[["acta_id", "legislador", "p"]].rename(
        columns={"legislador": "legislador_id", "p": "p_harness_viejo"})
    m = d.merge(nuevo, on=["acta_id", "legislador_id"], how="inner").merge(
        viejo, on=["acta_id", "legislador_id"], how="inner")
    m["_ley"] = m["_ley"].fillna("acta:" + m["acta_id"].astype(str))
    rep = {"n_panel": int(len(d)), "n_comun": int(len(m)),
           "produccion_M6_publicado": {"F_i": 2.0877, "lealtad_x_jefe": 1.75},
           "clusters": "ley (ADR-0032); la estimación original clusterizó por acta"}
    for nom, col in (("offset_de_la_estimacion", "p_motor"),
                     ("harness_viejo_con_fuga", "p_harness_viejo"),
                     ("motor_limpio", "p_limpio")):
        rep[nom] = m6(m, col)
        logger.info("%s: %s", nom, rep[nom]["coef"])
    rep["brier_offsets"] = {c: round(float(((m[c] - m["y"]) ** 2).mean()), 5)
                            for c in ("p_motor", "p_harness_viejo", "p_limpio")}
    out = REPO / SALIDA
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
