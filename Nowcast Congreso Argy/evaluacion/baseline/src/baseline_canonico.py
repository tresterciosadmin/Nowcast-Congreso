"""evaluacion/baseline/baseline_canonico.py
Baseline 'votá con tu grupo' (leave-one-out) sobre la base canónica resuelta.
Compara niveles de agrupación (bloque_norm / linaje / coalicion), por cámara y por año.
Mide solo votos sustantivos (AFIRMATIVO/NEGATIVO). Excluye 'SIN BLOQUE' (Senado reciente sin bloque resuelto).
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, pandas as pd

SUST = ["AFIRMATIVO", "NEGATIVO"]
CONT = 0.10  # disputada: minoría >=10% de los sustantivos del acta

def loo_acc(df, group):
    d = df[df["voto"].isin(SUST)].copy()
    if d.empty: return float("nan"), 0
    cnt = (d.groupby(["acta_id", group, "voto"], observed=True).size()
             .unstack(fill_value=0).reindex(columns=SUST, fill_value=0))
    d = d.merge(cnt, left_on=["acta_id", group], right_index=True, how="left")
    # copy=True: pandas con Copy-on-Write puede devolver arrays de solo-lectura
    mat = d[SUST].to_numpy(dtype=float, copy=True)
    own = d["voto"].map({c: i for i, c in enumerate(SUST)}).to_numpy()
    mat[np.arange(len(d)), own] -= 1
    valid = mat.sum(1) > 0
    pred = np.array(SUST)[mat.argmax(1)]
    n = int(valid.sum())
    return (float(((pred == d["voto"].to_numpy()) & valid).sum() / n) if n else float("nan")), n

def contested(df):
    sub = df[df["voto"].isin(SUST)]
    pa = (sub.groupby("acta_id")["voto"].value_counts().unstack(fill_value=0)
            .reindex(columns=SUST, fill_value=0))
    tot, mino = pa.sum(axis=1), pa.min(axis=1)
    return set(((mino / tot).where(tot > 0, 0) >= CONT).loc[lambda s: s].index)

def main():
    src = Path(os.environ.get("CANON", Path(__file__).resolve().parents[3] / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", Path(__file__).resolve().parents[1] / "outputs"))
    v = pd.read_parquet(src / "votos_resuelto.parquet")
    a = pd.read_parquet(src / "actas_canonico.parquet")[["acta_id", "camara"]]
    v = v.merge(a, on="acta_id", how="left")
    v["anio"] = pd.to_datetime(v["fecha"], errors="coerce").dt.year
    v = v[v["bloque_norm"] != "SIN BLOQUE"]   # sin bloque resoluble -> fuera del baseline

    res = {"n_votos_sustantivos": int(v["voto"].isin(SUST).sum())}
    disp = contested(v)
    vd = v[v["acta_id"].isin(disp)]

    # 1) por nivel de agrupación (todas vs disputadas)
    res["por_nivel"] = {}
    for g in ["bloque_norm", "bloque_linaje", "coalicion"]:
        at, nt = loo_acc(v, g); ad, nd = loo_acc(vd, g)
        res["por_nivel"][g] = {"todas": round(at, 4), "n_todas": nt,
                                "disputadas": round(ad, 4), "n_disputadas": nd}
    # 2) por cámara (bloque_norm)
    res["por_camara"] = {}
    for cam in ["diputados", "senado"]:
        sub = v[v["camara"] == cam]
        subd = sub[sub["acta_id"].isin(contested(sub))]
        at, nt = loo_acc(sub, "bloque_norm"); ad, nd = loo_acc(subd, "bloque_norm")
        res["por_camara"][cam] = {"todas": round(at, 4), "n_todas": nt,
                                   "disputadas": round(ad, 4), "n_disputadas": nd}
    # 3) por año (bloque_norm, disputadas) -> drift
    res["por_anio_disputadas"] = {}
    for yr, sub in v.dropna(subset=["anio"]).groupby("anio"):
        subd = sub[sub["acta_id"].isin(contested(sub))]
        ad, nd = loo_acc(subd, "bloque_norm")
        if nd > 200: res["por_anio_disputadas"][int(yr)] = {"acc": round(ad, 4), "n": nd}

    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline_canonico.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
