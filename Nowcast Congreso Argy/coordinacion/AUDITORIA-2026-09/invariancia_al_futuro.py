# -*- coding: utf-8 -*-
"""Prueba de INVARIANCIA AL FUTURO (auditoría 2026-09, Fase 2).

Idea: si el motor + harness no ven el futuro ni la misma ley, entonces CORROMPER en memoria
todo voto de fecha >= la del acta y todo voto de su misma ley no puede mover ninguna P_i.
Es una prueba metamórfica: no depende de cómo se implementó el corte, sólo de que no haya
información que se filtre.

Se hace sobre actas REALES (N por era, mitad Diputados y mitad Senado), no sobre un caso
sintético como `test_historia_sin_fuga.py`.  Cada voto corrompido cambia SIEMPRE de conducta
(AFIRMATIVO -> NEGATIVO; cualquier otra -> AFIRMATIVO).

CONTROL POSITIVO (que la prueba misma detecta una fuga): con `historia="dia_incluido"` (el corte
viejo del motor: ve el día entero) y con `historia="fecha"` (no excluye la misma ley), las P_i
SÍ tienen que moverse en las actas que tienen votos ese mismo día / de esa misma ley.

NO CUBRE: dictámenes ni taxonomías posteriores (β, TEMA_AUTO, RECORD_POR_TEMA no entran al harness),
la ficha de desvío (`disciplina_individual.csv`, toda la historia) ni la presencia.

USO: python coordinacion/AUDITORIA-2026-09/invariancia_al_futuro.py [--por-era 30]
Salida: Archivos_Borrar/auditoria/invariancia_al_futuro.json
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
for sub in ("", "modelo/ensemble/src", "variables/bloque/src", "evaluacion/baseline/src"):
    sys.path.insert(0, str(RAIZ / sub) if sub else str(RAIZ))
import nowcast_puertas as NP  # noqa: E402
from baseline_voto_individual import Contexto, ERA_BINS, ERA_LABELS, silenciar_avisos_del_motor  # noqa: E402

SALIDA = RAIZ / "Archivos_Borrar" / "auditoria" / "invariancia_al_futuro.json"


def corromper(votos: pd.DataFrame, fecha: pd.Timestamp, ley: str) -> pd.DataFrame:
    v = votos.copy()
    m = (v["fecha"] >= fecha) | (v["_ley"] == ley)
    v.loc[m, "conducta"] = np.where(v.loc[m, "conducta"] == "AFIRMATIVO", "NEGATIVO", "AFIRMATIVO")
    return v, int(m.sum())


def comparar(a: dict | None, b: dict | None) -> tuple[int, float, int]:
    """(n comparados, max |dP|, n con diferencia > 1e-12)."""
    if a is None or b is None:
        return 0, 0.0, 0
    ks = set(a) & set(b)
    d = np.array([abs(a[k][0] - b[k][0]) for k in ks]) if ks else np.zeros(1)
    return len(ks), float(d.max()), int((d > 1e-12).sum())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--por-era", type=int, default=30)
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    silenciar_avisos_del_motor()
    ctx0 = Contexto.desde_repo()
    v = ctx0.votos
    emit = v[v["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    actas = (emit[["acta_id", "fecha", "camara", "_ley"]].drop_duplicates("acta_id")
             .sort_values(["fecha", "acta_id"]))
    actas = actas[actas["fecha"] >= v["fecha"].min() + pd.Timedelta(days=730)]
    actas["era"] = pd.cut(actas["fecha"], ERA_BINS, labels=ERA_LABELS)
    partes = [g.sample(min(len(g), max(1, a.por_era // 2)), random_state=7)
              for _, g in actas.groupby(["era", "camara"], observed=True)]
    muestra = pd.concat(partes).sort_values(["fecha", "acta_id"])
    por_acta = {k: g for k, g in emit.groupby("acta_id", sort=False)}

    filas, t0 = [], time.time()
    for k, r in enumerate(muestra.itertuples(), 1):
        sub = por_acta[r.acta_id]
        votantes = sub[["legislador_id", "bloque_linaje"]]
        f = pd.Timestamp(r.fecha)
        base = ctx0.p_legisladores(r.acta_id, r.camara, f, votantes, "estricta", False)
        vc, n_cor = corromper(v, f, r._4)
        ctx1 = Contexto(vc, ctx0.ley_de_acta, ctx0.origen_map, ctx0.cond, ctx0.conf_area)
        fila = {"acta_id": r.acta_id, "era": str(r.era), "camara": r.camara, "fecha": str(f.date()),
                "votos_corrompidos": n_cor,
                "n_mismo_dia_otras_actas": int(((v["fecha"] == f) & (v["acta_id"] != r.acta_id)).sum()),
                "n_misma_ley_otras_actas": int(((v["_ley"] == r._4) & (v["acta_id"] != r.acta_id)).sum())}
        for nom, hist in (("estricta", "estricta"), ("CONTROL_dia_incluido", "dia_incluido"), ("CONTROL_fecha", "fecha")):
            n, mx, nd = comparar(base, ctx1.p_legisladores(r.acta_id, r.camara, f, votantes, hist, False))
            fila[nom] = {"n": n, "max_abs_dP": mx, "n_distintos": nd}
        filas.append(fila)
        if k % 15 == 0:
            print(f"  {k}/{len(muestra)} actas · {(time.time() - t0) / 60:.1f} min", flush=True)

    d = pd.DataFrame(filas)
    res = {"n_actas": int(len(d)), "por_era": a.por_era,
           "estricta_max_abs_dP_global": float(d["estricta"].map(lambda x: x["max_abs_dP"]).max()),
           "estricta_actas_con_diferencia": int(d["estricta"].map(lambda x: x["n_distintos"] > 0).sum()),
           "por_era_estricta": {e: {"actas": int(len(g)), "con_diferencia": int(g["estricta"].map(lambda x: x["n_distintos"] > 0).sum()),
                                    "max_abs_dP": float(g["estricta"].map(lambda x: x["max_abs_dP"]).max())}
                                for e, g in d.groupby("era")}}
    for ctrl, cond in (("CONTROL_dia_incluido", d["n_mismo_dia_otras_actas"] > 0),
                       ("CONTROL_fecha", d["n_misma_ley_otras_actas"] > 0)):
        sel = d[cond]
        res[ctrl] = {"actas_donde_deberia_detectar": int(len(sel)),
                     "actas_donde_detecta": int(sel[ctrl].map(lambda x: x["n_distintos"] > 0).sum()),
                     "max_abs_dP": float(sel[ctrl].map(lambda x: x["max_abs_dP"]).max()) if len(sel) else None}
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(json.dumps({"resumen": res, "detalle": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
