# -*- coding: utf-8 -*-
"""Backtest walk-forward MECANÍSTICO de la vía sobre tablas (S:III.A.5).

QUÉ MIDE, Y POR QUÉ ES DISTINTO DE `estimar_theta_sobre_tablas.py`

    Ese script mide theta con una regresión GLM offset, VOTO POR VOTO: ¿el
    corrimiento explica la tasa afirmativa individual? Eso ya está hecho y theta
    es significativo en Diputados. Lo que faltaba es la pregunta que Franco
    quiere antes de prender la bandera: corrido el MECANISMO QUE REALMENTE VA A
    PRODUCCIÓN —el roster de una cámara, desplazado por theta, simulado con
    `ensemble.simular_con_guardas` al umbral de DOS TERCIOS, tal cual
    `sobre_tablas.py`/`nowcast_puertas._via_sobre_tablas`—, ¿la P AGREGADA que
    sale predice si esa ACTA cruzó los dos tercios? Es la misma disciplina que
    salvó a `beta_dictamen` de un término que no generalizaba
    (`validar_beta_dictamen_walkforward.py`), aplicada acá al simulador en vez
    de a una regresión.

CORTE WALK-FORWARD, PARA NO MIRAR EL FUTURO

    theta se re-estima (GLM offset, igual que `estimar_theta_sobre_tablas.py`)
    SOLO sobre el `corte` (70% por defecto) de actas más VIEJO. Se mide sobre
    el resto —nunca visto al estimar theta— si esa acta era sobre tablas.

EL ROSTER QUE SE SIMULA ES EL DE VOTANTES REALES DE LA ACTA

    No se reconstruye el padrón histórico completo (el Senado no lo tiene tan
    atrás — ver §🚦 de CLAUDE.md): se usa a quienes efectivamente votaron esa
    acta, con su `p_bloque` YA point-in-time (sale de `proyectar_postura`
    dentro de `estimar_theta_sobre_tablas.panel()`, sin tocar). El umbral real
    de dos tercios se calcula sobre esos mismos emitidos, así la comparación es
    consistente con lo que se simula.

DOS SIMULACIONES POR ACTA, PARA AISLAR EL APORTE DE THETA

    `p_sim_con_theta`: el mecanismo completo (P_i^bloque desplazada por theta
    CRUDO, umbral de dos tercios).
    `p_sim_sin_theta`: el MISMO umbral de dos tercios, SIN el corrimiento —
    para separar "cuánto explica el umbral más duro, sólo por ser sobre
    tablas" de "cuánto agrega theta encima de eso".

CALIBRACIÓN POR ATENUACIÓN (15-09-2026, opción A tras el hallazgo de saturación)

    El primer backtest mostró que theta CRUDO —estimado voto por voto, GLM
    offset sobre 185k votos, la mayoría de motines que fracasan— SATURA al
    aplicarse por legislador y pasar por el umbral de dos tercios vía Monte
    Carlo: en Diputados, `p_sim_con_theta` daba 0,01 en el 100% de las actas
    held-out, sin importar el resultado real. El corrimiento está bien
    estimado PARA EL VOTO INDIVIDUAL; no sobrevive compuesto con un umbral tan
    exigente y un simulador que castiga la sobreconfianza.

    `_calibrar_factor` busca, SOLO sobre las actas de sobre tablas de TRAIN
    (nunca toca test), qué fracción de theta (grilla 0.0 a 1.0) minimiza el
    Brier del MECANISMO REAL —no de la regresión— al nivel de ACTA. Es
    calibrar el parámetro donde se va a usar, no donde se estimó. El factor
    elegido en train se aplica una sola vez sobre el test held-out, y se
    reporta junto a `sin theta` y `theta crudo` para ver qué aporta cada
    versión.

Uso:
    python modelo/ensemble/src/validar_sobre_tablas_walkforward.py
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("validar_sobre_tablas")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

P_MINIMO_SIGNIFICATIVO = 0.05
N_SIMS = 2000


def _logit(p, eps=1e-6):
    p = min(max(float(p), eps), 1 - eps)
    return math.log(p / (1 - p))


def _sigmoide(x):
    return 1.0 / (1.0 + math.exp(-x))


def _theta_de_train(res_train: dict) -> dict:
    """{camara: theta}, igual que `sobre_tablas._theta` pero sobre un resultado
    de `estimar_theta_sobre_tablas.estimar()` calculado SOLO con datos de train."""
    theta = {}
    for cam, r in res_train.get("C_por_camara", {}).items():
        if "error" in r or "tab" not in r.get("coef", {}):
            continue
        p = r.get("p", {}).get("tab", 1.0)
        theta[cam] = float(r["coef"]["tab"]) if p < P_MINIMO_SIGNIFICATIVO else 0.0
    return theta


def _p_tablas_de_acta(g: pd.DataFrame, theta: float, camara: str, *,
                      n_sims: int, seed: int) -> float:
    """P^tablas_c simulada para UNA acta: cada P_i^bloque desplazada por `theta`
    (0.0 = sin corrimiento), umbral de dos tercios, MISMO mecanismo que
    `nowcast_puertas._via_sobre_tablas`."""
    from ensemble import simular_con_guardas
    from nowcast_puertas import a_linea_y_desvio, REPARTO_DESVIO

    p_bloque = g["p_bloque"].astype(float).to_numpy()
    p = (np.array([_sigmoide(_logit(x) + theta) for x in p_bloque])
        if theta != 0.0 else p_bloque)
    lin, des = zip(*(a_linea_y_desvio(x) for x in p))
    sim = simular_con_guardas(np.array(lin), np.array(des, dtype=float),
                              "DOS_TERCIOS", camara, n_sims=n_sims, seed=seed,
                              reparto_desvio=REPARTO_DESVIO)
    return float(sim["p_aprobacion"])


def _outcome_de_acta(g: pd.DataFrame) -> tuple[int, int, int]:
    """(emitidos, afirm_real, cruzo_dos_tercios) — el resultado REAL de la acta."""
    emitidos = len(g)
    afirm_real = int(g["y"].sum())
    umbral_real = math.ceil(emitidos * 2 / 3)
    return emitidos, afirm_real, int(afirm_real >= umbral_real)


def _calibrar_factor(train_tab: pd.DataFrame, theta_crudo: dict, *,
                     n_sims: int, seed: int,
                     grid: tuple[float, ...] = tuple(round(x, 2) for x in np.arange(0, 1.01, 0.1))
                     ) -> dict:
    """Por cámara: la fracción de theta_crudo (0.0-1.0) que minimiza el Brier
    MACRO (promedio simple entre "cruzó" y "no cruzó", NO el Brier agregado)
    del MECANISMO REAL sobre las actas de sobre tablas de TRAIN — nunca toca
    test.

    Por qué MACRO y no el Brier plano: el Brier plano repite el mismo error
    que ya engañó a la primera lectura del backtest — la mayoría de las actas
    de sobre tablas NO cruza, así que minimizarlo sin ponderar empuja SIEMPRE
    hacia el factor más agresivo (predecir bajo para todo), que es
    literalmente la saturación que se está tratando de evitar. El macro-Brier
    le da el mismo peso a la clase minoritaria (las que SÍ cruzan, las que
    importan) sin importar cuántas actas tenga cada una.

    Devuelve {camara: {"factor":.., "theta_calibrado":.., "n":..,
    "n_por_clase":.., "brier_grid": {...}}}.
    """
    resultado = {}
    for cam, g_cam in train_tab.groupby("camara"):
        th0 = theta_crudo.get(str(cam), 0.0)
        actas = list(g_cam.groupby("acta_id", sort=False))
        if not actas or th0 == 0.0:
            resultado[str(cam)] = {"factor": 0.0, "theta_calibrado": 0.0, "n": len(actas),
                                   "brier_grid": {}}
            continue
        outcomes = {aid: _outcome_de_acta(g)[2] for aid, g in actas}
        n_pos = sum(outcomes.values())
        n_neg = len(outcomes) - n_pos
        if n_pos == 0 or n_neg == 0:
            logger.warning("calibración %s: train sin las dos clases (pos=%d, neg=%d) — "
                           "no se puede calibrar sin sesgo, factor=0.0", cam, n_pos, n_neg)
            resultado[str(cam)] = {"factor": 0.0, "theta_calibrado": 0.0, "n": len(actas),
                                   "n_por_clase": {"cruzo": n_pos, "no_cruzo": n_neg},
                                   "brier_grid": {}}
            continue
        brier_grid = {}
        for factor in grid:
            th = th0 * factor
            preds = {aid: _p_tablas_de_acta(g, th, str(cam), n_sims=n_sims, seed=seed)
                    for aid, g in actas}
            brier_pos = np.mean([(preds[a] - 1) ** 2 for a, y in outcomes.items() if y == 1])
            brier_neg = np.mean([(preds[a] - 0) ** 2 for a, y in outcomes.items() if y == 0])
            brier_grid[factor] = round(float((brier_pos + brier_neg) / 2), 4)
        mejor_factor = min(brier_grid, key=brier_grid.get)
        logger.info("calibración %s: n_train_tab=%d (cruzo=%d, no_cruzo=%d), "
                   "grilla_macro=%s -> factor=%.2f (theta=%.4f)",
                   cam, len(actas), n_pos, n_neg, brier_grid, mejor_factor, th0 * mejor_factor)
        resultado[str(cam)] = {"factor": float(mejor_factor),
                               "theta_calibrado": round(float(th0 * mejor_factor), 4),
                               "n_por_clase": {"cruzo": n_pos, "no_cruzo": n_neg},
                               "n": len(actas), "brier_grid": brier_grid}
    return resultado


def correr(corte: float = 0.7, n_sims: int = N_SIMS, seed: int = 7) -> dict:
    import estimar_theta_sobre_tablas as etst

    d = etst.panel()
    actas = d[["acta_id", "fecha"]].drop_duplicates().sort_values("fecha")
    n_train = int(len(actas) * corte)
    if n_train < 1 or n_train >= len(actas):
        raise SystemExit(f"corte {corte} deja train/test degenerado sobre {len(actas)} actas")
    fecha_corte = actas["fecha"].iloc[n_train]
    train = d[d["fecha"] < fecha_corte]
    test = d[d["fecha"] >= fecha_corte]
    logger.info("train: %d actas (hasta %s) · test: %d actas (desde %s)",
               train.acta_id.nunique(), fecha_corte, test.acta_id.nunique(), fecha_corte)

    res_train = etst.estimar(train)
    theta_crudo = _theta_de_train(res_train)
    logger.info("theta CRUDO (walk-forward, sólo train): %s", theta_crudo)

    train_tab = train[train.tab == 1]
    calibracion = _calibrar_factor(train_tab, theta_crudo, n_sims=n_sims, seed=seed)
    theta_calibrado = {cam: v["theta_calibrado"] for cam, v in calibracion.items()}
    logger.info("theta CALIBRADO (factor elegido sólo con train): %s", theta_calibrado)

    test_tab = test[test.tab == 1]
    filas = []
    for acta_id, g in test_tab.groupby("acta_id", sort=False):
        cam = str(g["camara"].iloc[0])
        emitidos, afirm_real, y_real = _outcome_de_acta(g)
        filas.append({
            "acta_id": acta_id, "camara": cam, "fecha": str(g["fecha"].iloc[0].date()),
            "n_votantes": emitidos, "afirm_real": afirm_real,
            "umbral_dos_tercios": math.ceil(emitidos * 2 / 3), "cruzo_dos_tercios": y_real,
            "theta_crudo": theta_crudo.get(cam, 0.0),
            "theta_calibrado": theta_calibrado.get(cam, 0.0),
            "p_sim_sin_theta": round(_p_tablas_de_acta(g, 0.0, cam, n_sims=n_sims, seed=seed), 4),
            "p_sim_con_theta": round(_p_tablas_de_acta(g, theta_crudo.get(cam, 0.0), cam,
                                                        n_sims=n_sims, seed=seed), 4),
            "p_sim_calibrado": round(_p_tablas_de_acta(g, theta_calibrado.get(cam, 0.0), cam,
                                                        n_sims=n_sims, seed=seed), 4),
        })

    if not filas:
        raise SystemExit("no quedaron actas de sobre tablas en el conjunto de test")
    df = pd.DataFrame(filas)

    def _brier(sub, col):
        return float(((sub[col] - sub["cruzo_dos_tercios"]) ** 2).mean())

    def _acc(sub, col, umbral=0.5):
        return float(((sub[col] >= umbral).astype(int) == sub["cruzo_dos_tercios"]).mean())

    cols = ("p_sim_sin_theta", "p_sim_con_theta", "p_sim_calibrado")
    resumen = {
        "n_actas_test_sobre_tablas": int(len(df)),
        "n_actas_train": int(train.acta_id.nunique()),
        "n_actas_test": int(test.acta_id.nunique()),
        "fecha_corte": str(fecha_corte.date()),
        "theta_crudo": theta_crudo,
        "calibracion_factor": calibracion,
        "tasa_real_cruza_dos_tercios": round(float(df["cruzo_dos_tercios"].mean()), 4),
        **{f"brier_{c.replace('p_sim_', '')}": round(_brier(df, c), 4) for c in cols},
        **{f"accuracy_{c.replace('p_sim_', '')}": round(_acc(df, c), 4) for c in cols},
        "por_camara": {
            cam: {
                "n": int(len(g)),
                "tasa_real": round(float(g["cruzo_dos_tercios"].mean()), 4),
                **{f"brier_{c.replace('p_sim_', '')}": round(_brier(g, c), 4) for c in cols},
            }
            for cam, g in df.groupby("camara")
        },
    }
    return {"resumen": resumen, "detalle": df.to_dict("records")}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corte", type=float, default=0.7)
    ap.add_argument("--n-sims", type=int, default=N_SIMS)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    res = correr(corte=args.corte, n_sims=args.n_sims, seed=args.seed)
    out = Path(args.salida) if args.salida else (
        RAIZ / "modelo/ensemble/outputs/validacion_sobre_tablas_walkforward.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res["resumen"], ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
