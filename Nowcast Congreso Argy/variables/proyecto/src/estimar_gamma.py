"""variables/proyecto/src/estimar_gamma.py — ¿existe el modulador del ICG?

Estima los dos parámetros del modulador que planteó Valle:

    odds' = odds x k        k = (ICG_c / ICG_0) ^ (gamma * s)
    gamma(t) = gamma_0 * (1 + lambda * vol6_z)

Como el modulador vive en el logit, `gamma` es LITERALMENTE el coeficiente de
`s * log_rel` en una regresión logística. Eso hace que el mismo ajuste que lo
implementa lo ponga a prueba: **si gamma no se distingue de cero, los datos
dicen que el clima no mueve el recinto.**

## Diseño

- **Unidad:** el acta votada. Resultado = share de afirmativos sobre emitidos,
  como binomial ponderada por votos (no aprobada/rechazada: el 93% de lo que
  llega al recinto se aprueba y esa variable casi no tiene varianza).
- **`s`** = +1 si lo impulsa el gobierno, −1 si la oposición. Sólo actas con
  origen resuelto (`origen_por_acta`, 59% de cobertura).
- **Efectos fijos por gobierno.** Es el control que hace válido todo esto: sin
  él, el ajuste compara presidencias y termina midiendo bancas, no clima
  (Milei tiene el 2º ICG más alto de 25 años y la peor conversión).
- **Sólo meses `apto_ajuste`**: se excluyen traspasos presidenciales (el índice
  califica al que viene, no al que está) y el período fuera de escala 2002-03.
- **Intervalos por bootstrap de bloque POR MES.** El ICG es mensual: las actas
  del mismo mes comparten el valor y no son observaciones independientes.
  Remuestrear actas sueltas inflaría la precisión de manera artificial.

Uso:
    python variables/proyecto/src/estimar_gamma.py
    python variables/proyecto/src/estimar_gamma.py --boot 400

4 directivas: errores específicos, sin red, parsing defensivo, logging.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("icg.gamma")

_HERE = Path(__file__).resolve()
RAIZ = _HERE.parents[3]
DATA = _HERE.parents[1] / "data"
OUT = _HERE.parents[1] / "outputs"


def cargar() -> pd.DataFrame:
    ctx = pd.read_parquet(DATA / "icg_contexto.parquet")
    act = pd.read_parquet(RAIZ / "datos/canonica/data/clean/actas_canonico.parquet")
    ori = pd.read_parquet(DATA / "origen_por_acta.parquet")

    act["f"] = pd.to_datetime(act["fecha"], errors="coerce")
    act = act.dropna(subset=["f"])
    act["mes_key"] = act["f"].values.astype("datetime64[M]")

    d = act.merge(ori[["acta_id", "origen_lado"]].drop_duplicates("acta_id"),
                  on="acta_id", how="inner")
    d = d[d["origen_lado"].isin(["GOBIERNO", "OPOSICION"])]

    ctx["mes_key"] = ctx["fecha"].values.astype("datetime64[M]")
    d = d.merge(ctx[["mes_key", "log_rel", "vol6_z", "gobierno", "apto_ajuste"]],
                on="mes_key", how="inner")

    for c in ("n_afirmativos", "n_negativos", "n_abstenciones"):
        d[c] = pd.to_numeric(d.get(c), errors="coerce").fillna(0)
    d["emitidos"] = d[["n_afirmativos", "n_negativos", "n_abstenciones"]].sum(axis=1)
    d = d[d["emitidos"] >= 20]                      # actas con cuerpo real
    d["s"] = np.where(d["origen_lado"] == "GOBIERNO", 1.0, -1.0)
    d = d[d["apto_ajuste"] & d["log_rel"].notna() & d["vol6_z"].notna()]
    return d


def matriz(d: pd.DataFrame, con_vol: bool) -> tuple[pd.DataFrame, list]:
    X = pd.DataFrame(index=d.index)
    X["s_logrel"] = d["s"] * d["log_rel"]           # <- su coeficiente ES gamma_0
    if con_vol:
        X["s_logrel_vol"] = X["s_logrel"] * d["vol6_z"]
    X["s"] = d["s"]                                 # nivel base de cada lado
    X["senado"] = d["camara"].astype(str).str.contains("SEN", case=False, na=False).astype(float)
    for g in sorted(d["gobierno"].dropna().unique())[1:]:   # FE por gobierno (una base)
        X[f"gob_{g}"] = (d["gobierno"] == g).astype(float)
    return X, list(X.columns)


def ajustar(d: pd.DataFrame, con_vol: bool):
    """Binomial ponderada: cada acta aporta n_afirmativos éxitos y el resto fracasos."""
    from sklearn.linear_model import LogisticRegression
    X, cols = matriz(d, con_vol)
    Xd = np.vstack([X.values, X.values])
    y = np.r_[np.ones(len(X)), np.zeros(len(X))]
    w = np.r_[d["n_afirmativos"].values, (d["emitidos"] - d["n_afirmativos"]).values]
    m = LogisticRegression(max_iter=2000, C=1e6)     # sin regularizacion efectiva
    m.fit(Xd, y, sample_weight=w)
    return pd.Series(m.coef_[0], index=cols)


def bootstrap(d: pd.DataFrame, con_vol: bool, n: int, semilla: int = 7) -> pd.DataFrame:
    """Bloque por MES: se remuestrean meses enteros, no actas sueltas."""
    rng = np.random.default_rng(semilla)
    meses = d["mes_key"].unique()
    filas = []
    for _ in range(n):
        elegidos = rng.choice(meses, size=len(meses), replace=True)
        muestra = pd.concat([d[d.mes_key == m] for m in elegidos], ignore_index=True)
        if muestra["s"].nunique() < 2:
            continue
        try:
            filas.append(ajustar(muestra, con_vol))
        except (ValueError, np.linalg.LinAlgError):
            continue
    return pd.DataFrame(filas)


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--con-vol", action="store_true", help="incluir la interaccion con volatilidad")
    a = ap.parse_args(argv)

    d = cargar()
    logger.info("actas utilizables: %d (%d meses, %d gobiernos)",
                len(d), d.mes_key.nunique(), d.gobierno.nunique())
    print(d.groupby("origen_lado").agg(n=("s", "size"), share=("n_afirmativos", "sum")).to_string())

    coef = ajustar(d, a.con_vol)
    b = bootstrap(d, a.con_vol, a.boot)
    print(f"\n=== ESTIMACION (bootstrap de bloque por mes, {len(b)} replicas) ===")
    res = {}
    for k in ("s_logrel", "s_logrel_vol"):
        if k not in coef.index:
            continue
        lo, hi = b[k].quantile(.025), b[k].quantile(.975)
        signif = "SI" if (lo > 0 or hi < 0) else "no"
        etq = "gamma_0" if k == "s_logrel" else "gamma_0*lambda"
        print(f"  {etq:16s} = {coef[k]:+.4f}   IC95% [{lo:+.4f}, {hi:+.4f}]   distinto de cero: {signif}")
        res[etq] = {"punto": round(float(coef[k]), 4), "ic95": [round(float(lo), 4), round(float(hi), 4)],
                    "significativo": signif == "SI"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gamma_icg.json").write_text(json.dumps(
        {"n_actas": int(len(d)), "n_meses": int(d.mes_key.nunique()),
         "con_vol": bool(a.con_vol), "boot": int(len(b)), "resultado": res,
         "coeficientes": {k: round(float(v), 4) for k, v in coef.items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
