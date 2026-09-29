# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

r = pd.read_parquet(r"C:\Users\Franco\OneDrive\Desktop\TresTercios\Nowcast Congreso\Nowcast Congreso Argy\Archivos_Borrar\auditoria\contraste_aprobacion_actas.parquet")
r = r.dropna(subset=["y_oficial"]).copy()
PA = "p__produccion_eps0_0.035_tau_1.19"
PB = "p__sin_incertidumbre_legislador(clip_agregado_0.01)"
s = r[r["tipo_norm"] == "SIMPLE"].copy()
rng = np.random.default_rng(3)


def auc(p, y):
    p, y = np.asarray(p), np.asarray(y)
    if y.min() == y.max():
        return np.nan
    o = pd.Series(p).rank().to_numpy()
    n1, n0 = y.sum(), (1 - y).sum()
    return (o[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def recal_cv(g, col, k=5):
    """Recalibración logística p' = sigma(a + b*logit(p)), ajustada fuera de muestra (k pliegues por LEY)."""
    from scipy.optimize import minimize
    leyes = g["ley"].unique()
    rng.shuffle(leyes)
    pliegue = {l: i % k for i, l in enumerate(leyes)}
    f = g["ley"].map(pliegue).to_numpy()
    x, y = logit(g[col].to_numpy()), g["y_oficial"].to_numpy()
    out = np.zeros(len(g))
    for j in range(k):
        tr, te = f != j, f == j

        def nll(w):
            z = w[0] + w[1] * x[tr]
            return np.mean(np.log1p(np.exp(-z)) * y[tr] + np.log1p(np.exp(z)) * (1 - y[tr]))

        w = minimize(nll, [0.0, 1.0], method="Nelder-Mead").x
        out[te] = 1 / (1 + np.exp(-(w[0] + w[1] * x[te])))
    return out


print("MAYORÍA SIMPLE — por cámara (resultado oficial). base = tasa de aprobación en esa cámara")
print(f"{'cámara':<10}{'subconjunto':<18}{'n':>5}{'base':>7}{'Brier const':>12}{'Brier prod':>11}{'AUC prod':>9}{'Brier recal(CV)':>16}{'Brier sin ε₀+τη':>16}{'logloss prod':>13}{'logloss sin':>12}")
for cam, g0 in s.groupby("camara"):
    for nom, g in (("todas", g0), ("disputadas(>=10%)", g0[(np.minimum(g0["af_real"], g0["n_votantes"] - g0["af_real"]) / g0["n_votantes"]) >= 0.10])):
        y = g["y_oficial"].to_numpy()
        b = y.mean()
        bc = b * (1 - b)
        pa, pb = g[PA].clip(1e-4, 1 - 1e-4).to_numpy(), g[PB].clip(1e-4, 1 - 1e-4).to_numpy()
        brier = ((pa - y) ** 2).mean()
        ll = lambda p: -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()
        rec = recal_cv(g, PA)
        print(f"{cam:<10}{nom:<18}{len(g):>5}{b:>7.3f}{bc:>12.4f}{brier:>11.4f}{auc(pa, y):>9.3f}{((rec - y) ** 2).mean():>16.4f}{((pb - y) ** 2).mean():>16.4f}{ll(pa):>13.4f}{ll(pb):>12.4f}")
g = s
y = g["y_oficial"].to_numpy()
pa, pb = g[PA].clip(1e-4, 1 - 1e-4).to_numpy(), g[PB].clip(1e-4, 1 - 1e-4).to_numpy()
print("\nSIMPLE, ambas cámaras juntas:")
print(f"  n={len(g)} base={y.mean():.3f}  Brier const={y.mean()*(1-y.mean()):.4f}  Brier prod={((pa-y)**2).mean():.4f}  AUC={auc(pa, y):.3f}  Brier sin ε₀+τη={((pb-y)**2).mean():.4f}")
print(f"  logloss prod={-(y*np.log(pa)+(1-y)*np.log(1-pa)).mean():.4f}  logloss sin ε₀+τη={-(y*np.log(pb)+(1-y)*np.log(1-pb)).mean():.4f}")
print("\nRechazadas en mayoría simple:", int((y == 0).sum()), "| P(aprob) mediana asignada:", round(float(np.median(pa[y == 0])), 3), "| con P>0.8:", int((pa[y == 0] > 0.8).sum()))
