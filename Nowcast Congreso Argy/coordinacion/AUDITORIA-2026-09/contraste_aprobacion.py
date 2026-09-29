# -*- coding: utf-8 -*-
"""Contraste P(aprobación) contra el resultado REAL de cada acta (auditoría 2026-09).

QUÉ MIDE. El paso P_i → P(aprobación de la cámara) que ESTADO-REAL-DEL-MOTOR.md (§3) dice
"nunca se contrastó contra resultados en walk-forward con P_i pronosticadas". Toma las P_i
LIMPIAS del censo (`p__estricta__general`: motor real, fecha estricta y otra ley), corre la
simulación del motor (`ensemble.simular_con_guardas`) con la configuración de producción
sobre los legisladores que efectivamente votaron cada acta, y compara P(aprobación) con el
resultado oficial de esa acta (`actas_canonico.resultado`), con el TIPO DE MAYORÍA REAL del acta.

QUÉ NO MIDE. Condiciona a quienes votaron (`p_presente = 1`): la asistencia, que en producción
sí entra a la simulación, sigue sin medirse. Y el resultado de una acta no es la sanción de una ley.

USO:  python coordinacion/AUDITORIA-2026-09/contraste_aprobacion.py [--detalle RUTA] [--n-sims 2000]
Salida: Archivos_Borrar/auditoria/contraste_aprobacion{.json,_actas.parquet} (gitignored).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(RAIZ / "modelo" / "agregador_institucional" / "src"))
import nowcast_puertas as NP  # noqa: E402
from agregador import umbral_aprobacion  # noqa: E402
from definiciones import normalizar_mayoria_valor  # noqa: E402
from ensemble import simular_con_guardas  # noqa: E402

DETALLE = RAIZ / "evaluacion" / "baseline" / "outputs" / "censo_detalle_2026-09-28.parquet"
SALIDA = RAIZ / "Archivos_Borrar" / "auditoria" / "contraste_aprobacion.json"
COL = "p__estricta__general"
N_BOOT = 2000
SI, NO = {"afirmativo", "afirmativa"}, {"negativo", "negativa"}


def resultado_binario(txt) -> float:
    t = str(txt).strip().lower()
    return 1.0 if t in SI else (0.0 if t in NO else np.nan)


def metricas(p: np.ndarray, y: np.ndarray, ley: np.ndarray) -> dict:
    """Brier / log-loss / skill contra la tasa base de aprobación, con IC 95% Poisson-bootstrap sobre LEYES."""
    p = np.clip(p, 1e-4, 1 - 1e-4)
    cod, uniq = pd.factorize(ley)
    k = len(uniq)
    W = np.random.default_rng(11).poisson(1.0, (N_BOOT, k)).astype(float)
    n = np.bincount(cod, minlength=k).astype(float)
    sy = np.bincount(cod, weights=y, minlength=k)
    sb = np.bincount(cod, weights=(p - y) ** 2, minlength=k)
    sl = np.bincount(cod, weights=-(y * np.log(p) + (1 - y) * np.log(1 - p)), minlength=k)
    N, b = n.sum(), y.mean()
    brier, ll, bb = sb.sum() / N, sl.sum() / N, b * (1 - b)
    Nb, Yb = W @ n, W @ sy
    bbb = (Yb / Nb) * (1 - Yb / Nb)
    sk = 1 - ((W @ sb) / Nb) / bbb
    cal = []
    for lo, hi in ((0, .05), (.05, .2), (.2, .5), (.5, .8), (.8, .95), (.95, 1.0001)):
        m = (p >= lo) & (p < hi)
        cal.append({"bin": f"[{lo:.2f},{min(hi, 1):.2f})", "n": int(m.sum()),
                    "p_medio": round(float(p[m].mean()), 4) if m.any() else None,
                    "frec_real": round(float(y[m].mean()), 4) if m.any() else None})
    return {"n_actas": int(N), "n_leyes": int(k), "tasa_base_aprobacion": round(float(b), 4),
            "brier": round(float(brier), 5), "logloss": round(float(ll), 5),
            "skill_vs_tasa_base": round(float(1 - brier / bb), 4),
            "skill_ic95_ley": [round(float(np.percentile(sk, 2.5)), 4), round(float(np.percentile(sk, 97.5)), 4)],
            "seguras_y_equivocadas": {"P>0.95_y_rechazada": int(((p > 0.95) & (y == 0)).sum()),
                                      "P<0.05_y_aprobada": int(((p < 0.05) & (y == 1)).sum())},
            "calibracion": cal}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalle", default=str(DETALLE))
    ap.add_argument("--n-sims", type=int, default=2000)
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    for nm in ("agregador", "ensemble", "nowcast_puertas"):
        logging.getLogger(nm).setLevel(logging.WARNING)

    d = pd.read_parquet(a.detalle, columns=["acta_id", "camara", "ley", "y", COL])
    d["acta_id"] = d["acta_id"].astype(str)
    ac = pd.read_parquet(RAIZ / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet",
                         columns=["acta_id", "tipo_mayoria", "resultado"])
    ac["acta_id"] = ac["acta_id"].astype(str)
    ac = ac.drop_duplicates("acta_id").set_index("acta_id")

    configs = {"produccion_eps0_0.035_tau_1.19": {"epsilon0": NP.EPSILON0, "tau": NP.TAU},
               "sin_incertidumbre_legislador(clip_agregado_0.01)": {"epsilon0": 0.0, "tau": 0.0}}
    filas, t0 = [], time.time()
    for k, (aid, g) in enumerate(d.groupby("acta_id", sort=False), 1):
        if len(g) < 20:
            continue
        cam = str(g["camara"].iloc[0])
        tipo_raw = ac["tipo_mayoria"].get(aid)
        tipo = normalizar_mayoria_valor(tipo_raw) if pd.notna(tipo_raw) else "SIMPLE"
        lin, des = zip(*(NP.a_linea_y_desvio(p) for p in g[COL].to_numpy(float)))
        fila = {"acta_id": aid, "camara": cam, "ley": g["ley"].iloc[0], "n_votantes": len(g),
                "af_real": int(g["y"].sum()), "tipo_raw": tipo_raw, "tipo_norm": tipo,
                "resultado_oficial": ac["resultado"].get(aid)}
        for nom, kw in configs.items():
            s = simular_con_guardas(np.array(lin), np.array(des, float), tipo, cam, n_sims=a.n_sims, seed=0,
                                    p_presente=np.ones(len(g)), reparto_desvio=NP.REPARTO_DESVIO, **kw)
            fila["p__" + nom] = float(s["p_aprobacion"])
        emit = len(g)
        fila["aprobada_por_los_votos"] = float(fila["af_real"] >= umbral_aprobacion(tipo, emit, cam))
        filas.append(fila)
        if k % 500 == 0:
            print(f"  {k} actas · {(time.time() - t0) / 60:.1f} min", flush=True)
    r = pd.DataFrame(filas)
    r["y_oficial"] = r["resultado_oficial"].map(resultado_binario)
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    r.to_parquet(str(a.salida).replace(".json", "_actas.parquet"), index=False)

    res: dict = {"detalle": str(a.detalle), "n_sims": a.n_sims, "n_actas_simuladas": int(len(r)),
                 "acuerdo_resultado_oficial_vs_recontado_de_los_votos": None, "salidas": {}}
    ok = r.dropna(subset=["y_oficial"])
    res["acuerdo_resultado_oficial_vs_recontado_de_los_votos"] = round(float((ok["y_oficial"] == ok["aprobada_por_los_votos"]).mean()), 4)
    res["n_actas_con_resultado_oficial_binario"] = int(len(ok))
    disputada = (np.minimum(ok["af_real"], ok["n_votantes"] - ok["af_real"]) / ok["n_votantes"]) >= 0.10
    for nom in configs:
        c = "p__" + nom
        res["salidas"][nom] = {
            "resultado_oficial__todas": metricas(ok[c].to_numpy(), ok["y_oficial"].to_numpy(), ok["ley"].to_numpy()),
            "resultado_oficial__disputadas(>=10%_en_contra)": metricas(ok.loc[disputada, c].to_numpy(), ok.loc[disputada, "y_oficial"].to_numpy(), ok.loc[disputada, "ley"].to_numpy()),
            "recontado_de_los_votos__todas": metricas(r[c].to_numpy(), r["aprobada_por_los_votos"].to_numpy(), r["ley"].to_numpy())}
    Path(a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: {kk: {x: v[x] for x in ("n_actas", "tasa_base_aprobacion", "brier", "skill_vs_tasa_base", "seguras_y_equivocadas")}
                          for kk, v in vv.items()} for k, vv in res["salidas"].items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
