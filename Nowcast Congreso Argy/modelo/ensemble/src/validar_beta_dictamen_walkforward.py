# -*- coding: utf-8 -*-
"""Backtest WALK-FORWARD de `beta_dictamen.py`: ¿generaliza, o sobreajusta?

**Por qué existe.** `estimar_beta_dictamen.py` ajusta sobre TODA la muestra y mide
significancia (p-valor, error estándar cluster por acta) — eso dice si el
coeficiente es distinto de cero EN LA MUESTRA, no si sirve para predecir un voto
que el modelo todavía no vio. El 14-09-2026, con M5 (que incluía el carácter del
dictamen) prendida y medida sobre proyectos reales, P colapsaba de 0,98 a 0,01 en
la mayoría de los casos con dictamen no unánime — Franco pidió "miralo con más
casos antes de decidir". Este script es ESE más-casos, hecho bien: entrena con el
70% de actas MÁS VIEJO y mide Brier/accuracy sobre el 30% MÁS NUEVO, que el ajuste
nunca vio. Si un término sólo ayuda adentro de la muestra de entrenamiento, acá se
nota.

**Resultado del 14-09-2026** (el que decidió sacar el carácter de producción):

    HELD-OUT (81.450 votos, actas desde 2017-12-22)
                          Brier     skill    accuracy
    sólo motor (offset)   0,1725   0,1929    0,7549
    + F_i + lealtad_jefe   0,1591   0,2672    0,7558   <- generaliza, mejora
    + carácter también     0,1793   0,1611    0,7418   <- empeora, no generaliza

    por carácter (con el término de carácter incluido):
      DISPUTADO   brier_motor=0,1997  brier_con_caracter=0,2081  (peor)
      mayoria     brier_motor=0,1934  brier_con_caracter=0,2533  (mucho peor)
      solo_minoria brier_motor=0,2067 brier_con_caracter=0,2059  (~igual)
      UNICO       brier_motor=0,1382  brier_con_caracter=0,1275  (mejor -- pero
                   UNICO es la referencia: acá sólo actúan F_i/lealtad, no el
                   carácter)

Uso:
    python modelo/ensemble/src/validar_beta_dictamen_walkforward.py
    python modelo/ensemble/src/validar_beta_dictamen_walkforward.py --corte 0.7
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("validar_beta_dictamen_walkforward")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402


def _logit(p, eps=1e-4):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p / (1 - p))


def _metricas(p, y) -> dict:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    br = float(((p - y) ** 2).mean())
    bb = float(((y.mean() - y) ** 2).mean())
    return {"n": int(len(y)), "brier": round(br, 5),
           "skill_vs_tasa_base": round(1 - br / bb, 4) if bb > 0 else None,
           "accuracy": round(float(((p >= 0.5) == (y == 1)).mean()), 4)}


def correr(corte: float = 0.7, muestra: int = 0, seed: int = 7) -> dict:
    import statsmodels.api as sm
    from estimar_beta_dictamen import construir_panel

    d = construir_panel(muestra, seed)
    logger.info("panel: %d votos, %d actas, %s a %s", len(d), d.acta_id.nunique(),
               d.fecha.min().date(), d.fecha.max().date())

    actas = d[["acta_id", "fecha"]].drop_duplicates().sort_values("fecha")
    corte_fecha = actas.iloc[int(len(actas) * corte)]["fecha"]
    train, test = d[d.fecha < corte_fecha].copy(), d[d.fecha >= corte_fecha].copy()
    logger.info("corte %s: train %d actas (%d votos) | test %d actas (%d votos)",
               corte_fecha.date(), train.acta_id.nunique(), len(train),
               test.acta_id.nunique(), len(test))
    if train.empty or test.empty:
        raise SystemExit("corte deja un lado vacío: ajustá --corte")

    for parte in (train, test):
        parte["lealtad_x_jefe"] = (1 - parte["d_i"]) * parte["J_l"]
    dummies_tr = pd.get_dummies(train["caracter"], prefix="dict", drop_first=False)
    dummies_tr = dummies_tr.drop(columns=[c for c in ("dict_UNICO",) if c in dummies_tr])

    def _ajustar(cols_train: pd.DataFrame):
        X = sm.add_constant(cols_train.astype(float), has_constant="add")
        mod = sm.GLM(train["y"].astype(float), X, family=sm.families.Binomial(),
                    offset=_logit(train["p_motor"]))
        return mod.fit(cov_type="cluster", cov_kwds={"groups": train["acta_id"]})

    def _aplicar(params: pd.Series, cols_test: pd.DataFrame, con_const: bool) -> np.ndarray:
        cols = list(params.index) if con_const else [c for c in params.index if c != "const"]
        # .astype(float) antes de .values: get_dummies deja columnas bool, y una
        # matriz con bool + float mezclados da dtype object -- @ produce floats de
        # Python en un array object, y np.exp sobre eso intenta llamar .exp() en
        # cada elemento en vez de la funcion vectorizada (TypeError críptico).
        X = cols_test.reindex(columns=[c for c in cols if c != "const"], fill_value=0.0).astype(float)
        if con_const:
            X = sm.add_constant(X, has_constant="add")[cols]
        delta = X.values @ params[cols].values
        return 1 / (1 + np.exp(-(_logit(test["p_motor"].values) + delta)))

    r_fj = _ajustar(train[["F_i", "lealtad_x_jefe"]])
    r_car = _ajustar(pd.concat([train[["F_i", "lealtad_x_jefe"]], dummies_tr], axis=1))

    dummies_te = pd.get_dummies(test["caracter"], prefix="dict", drop_first=False)
    p_motor = test["p_motor"].values
    p_fj = _aplicar(r_fj.params, test[["F_i", "lealtad_x_jefe"]], con_const=False)
    p_car = _aplicar(r_car.params, pd.concat([test[["F_i", "lealtad_x_jefe"]], dummies_te], axis=1),
                     con_const=False)

    res = {
        "corte_fecha": str(corte_fecha.date()),
        "train_actas": int(train.acta_id.nunique()), "test_actas": int(test.acta_id.nunique()),
        "coef_train_sin_caracter": {k: round(float(v), 4) for k, v in r_fj.params.items()},
        "coef_train_con_caracter": {k: round(float(v), 4) for k, v in r_car.params.items()},
        "held_out": {
            "solo_motor": _metricas(p_motor, test["y"].values),
            "motor_mas_F_i_lealtad": _metricas(p_fj, test["y"].values),
            "motor_mas_caracter_tambien": _metricas(p_car, test["y"].values),
        },
        "held_out_por_caracter_con_caracter_incluido": {
            car: {"n": int(len(g)),
                 "brier_motor": _metricas(test.loc[g.index, "p_motor"].values, g["y"].values)["brier"],
                 "brier_con_caracter": _metricas(
                     p_car[test.index.get_indexer(g.index)], g["y"].values)["brier"]}
            for car, g in test.groupby("caracter")
        },
    }
    return res


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corte", type=float, default=0.7,
                    help="fraccion de actas (por fecha) que va a train; el resto a test")
    ap.add_argument("--muestra", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    res = correr(a.corte, a.muestra, a.seed)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    out = Path(a.salida) if a.salida else (
        REPO / "modelo/ensemble/outputs/beta_dictamen_walkforward.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
