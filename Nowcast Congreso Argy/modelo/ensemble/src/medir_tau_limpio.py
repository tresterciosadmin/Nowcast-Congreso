# -*- coding: utf-8 -*-
"""FASE 4.2 de `coordinacion/PROMPT-CIERRE-DE-ETAPA.md` (ADR-0034) — τ con el offset
limpio, y la prueba que el razonamiento necesita: ¿las bandas quedaban angostas?

El razonamiento a verificar: un offset contaminado (que conoce parte de la respuesta)
deja menos residuo, así que τ —la dispersión que el motor no explica— sale SUBESTIMADO
y las bandas quedan angostas. Tres cosas, sobre el MISMO conjunto de votos:

1. ε0 y τ con el estimador de siempre (`estimar_epsilon_tau.estimar_epsilon/estimar_tau`,
   importados) sobre tres offsets:
     - `p_viejo`                  el harness con fuga (lo que se venía usando, 27-09)
     - `p__dia_incluido__general` el motor con su `<=` (la fuga del motor)
     - `p__estricta__general`     el motor con historia estricta (el limpio, como queda)
2. Cobertura REAL de la banda [p5, p95] del recuento de afirmativos, con la simulación
   DEL MOTOR (`ensemble.simular_con_guardas`, la misma que usa `nowcast`), entre los
   que efectivamente votaron. ADR-0025 reportó 99,88%, pero ese backtest
   (`agregador.backtest`) le da al agregador la línea de bloque OBSERVADA en la misma
   acta: mide la mecánica con un oráculo, no la banda de un pronóstico.
3. La misma cobertura con τ viejo (1,19) y con el τ re-estimado.

No cambia ningún default: el TAU del motor queda en 1,19 hasta que Franco decida.

    python modelo/ensemble/src/medir_tau_limpio.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estimar_epsilon_tau import REPO, estimar_epsilon, estimar_tau  # noqa: E402
import nowcast_puertas as NP  # noqa: E402

logger = logging.getLogger("medir_tau_limpio")

NUEVO = "evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet"
VIEJO = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"
SALIDA = "modelo/ensemble/outputs/tau_limpio_2026-09-28.json"
# el motor como queda desde el 28-09 (RECORD_POR_TEMA apagado, ADR-0034)
OFFSETS = {"harness_viejo_con_fuga": "p_viejo",
           "motor_dia_incluido": "p__dia_incluido__general",
           "motor_limpio": "p__estricta__general"}
N_SIMS = 1000


def cobertura(d: pd.DataFrame, col: str, eps0: float, tau: float, n_sims: int = N_SIMS,
              seed: int = 0) -> dict:
    """Fracción de actas donde el recuento REAL de afirmativos (entre los que votaron)
    cae en la banda [p5, p95] que declara la simulación del motor."""
    from ensemble import simular_con_guardas
    dentro, n, anchos, z = 0, 0, [], []
    for (aid, cam), g in d.groupby(["acta_id", "camara"], sort=False):
        if len(g) < 20:
            continue
        lin, des = zip(*(NP.a_linea_y_desvio(p) for p in g[col].to_numpy(float)))
        sim = simular_con_guardas(np.array(lin), np.array(des, float), "SIMPLE", cam,
                                  n_sims=n_sims, seed=seed, p_presente=np.ones(len(g)),
                                  reparto_desvio=NP.REPARTO_DESVIO, epsilon0=eps0, tau=tau)
        real = int(g["y"].sum())
        lo, hi = float(sim["afirm_p5"]), float(sim["afirm_p95"])
        dentro += int(lo <= real <= hi)
        n += 1
        anchos.append(hi - lo)
        z.append(real - float(sim["afirm_medio"]))
    z = np.asarray(z)
    return {"n_actas": n, "cobertura_banda_90": round(dentro / n, 4) if n else None,
            "ancho_mediano_votos": round(float(np.median(anchos)), 1) if n else None,
            "sesgo_medio_votos": round(float(z.mean()), 2) if n else None}


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("agregador").setLevel(logging.WARNING)
    logging.getLogger("ensemble").setLevel(logging.WARNING)
    d = pd.read_parquet(REPO / NUEVO)
    v = pd.read_parquet(REPO / VIEJO)[["acta_id", "legislador", "p"]].rename(columns={"p": "p_viejo"})
    d = d.merge(v, on=["acta_id", "legislador"], how="inner", validate="1:1")
    rep: dict = {"n_votos": int(len(d)), "n_actas": int(d["acta_id"].nunique()),
                 "tau_motor_hoy": NP.TAU, "eps0_motor_hoy": NP.EPSILON0,
                 "tau_publicado_2026_09_03": 1.197, "tau_reestimado_2026_09_16": 1.190}
    est = {}
    for nom, col in OFFSETS.items():
        dd = d[["acta_id", "camara", "fecha", "y"]].assign(p_motor=d[col].astype(float))
        e = estimar_epsilon(dd)
        t0 = estimar_tau(dd, 0.0)
        te = estimar_tau(dd, e["eps0_optimo_logloss"])
        est[nom] = {"eps0_optimo_logloss": e["eps0_optimo_logloss"],
                    "eps0_optimo_brier": e["eps0_optimo_brier"],
                    "tau_sin_epsilon": t0["tau_mediana"], "tau_IQR": t0["tau_IQR"],
                    "tau_con_epsilon": te["tau_mediana"],
                    "sobredispersion": t0["sobredispersion_observada"],
                    "fraccion_error_sesgo": t0["fraccion_del_error_que_es_sesgo"],
                    "n_actas_tau": t0["n_actas"],
                    "por_camara": {c: {"tau": estimar_tau(g.assign(p_motor=g[col].astype(float))
                                                          [["acta_id", "camara", "fecha", "y", "p_motor"]],
                                                          0.0)["tau_mediana"]}
                                   for c, g in d.groupby("camara")}}
        logger.info("%s: eps0=%.3f tau=%.3f", nom, e["eps0_optimo_logloss"], t0["tau_mediana"])
    rep["estimaciones"] = est

    limpio = est["motor_limpio"]
    cob = {}
    for nom, col, eps0, tau in (
            ("limpio__tau_1.19_eps_0.035", OFFSETS["motor_limpio"], NP.EPSILON0, NP.TAU),
            ("limpio__tau_reestimado", OFFSETS["motor_limpio"], limpio["eps0_optimo_logloss"], limpio["tau_sin_epsilon"]),
            ("limpio__sin_tau", OFFSETS["motor_limpio"], NP.EPSILON0, 0.0),
            ("harness_viejo__tau_1.19", "p_viejo", NP.EPSILON0, NP.TAU)):
        logger.info("cobertura %s ...", nom)
        cob[nom] = cobertura(d, col, eps0, tau)
        cob[nom].update({"eps0": eps0, "tau": tau})
        logger.info("   %s", cob[nom])
    rep["cobertura_banda"] = cob
    out = REPO / SALIDA
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps({"estimaciones": {k: {x: v[x] for x in ("eps0_optimo_logloss", "tau_sin_epsilon")}
                                       for k, v in est.items()},
                      "cobertura": {k: v["cobertura_banda_90"] for k, v in cob.items()}},
                     ensure_ascii=False, indent=1))
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
