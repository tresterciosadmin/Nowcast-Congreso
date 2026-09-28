# -*- coding: utf-8 -*-
"""FASE 3 y 4.1 de `coordinacion/PROMPT-CIERRE-DE-ETAPA.md` (ADR-0034) — el número
publicado con el harness limpio, la descomposición del arreglo, y RECORD_POR_TEMA
re-medido. Todo sobre el MISMO conjunto de votos y con IC re-muestreando LEYES.

Lee:
  - el censo nuevo (`censo_detalle_paralelo.py`, 28-09): P_i del MOTOR voto a voto, en
    cinco variantes calculadas en la misma pasada:
        estricta__tema     historia estricta, RECORD_POR_TEMA prendido (el motor hoy)
        estricta__general  historia estricta, RECORD_POR_TEMA apagado
        fecha__tema        sin excluir la misma ley
        dia_incluido__*    el corte `<=` que tenía el motor (la fuga del motor)
  - el censo viejo (27-09): el `p` del harness con fuga (shift(1), sin origen) — el
    número que estaba publicado —, para la comparación sobre los mismos votos.

    python evaluacion/baseline/src/resumen_censo_limpio.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_voto_individual  # noqa: E402,F401  (pone modelo/ensemble/src en el path)
from baseline_voto_individual import (REPO, ERA_BINS, ERA_LABELS, _metricas,  # noqa: E402
                                      dif_brier_ic_por_ley, resumir, skill_ic_por_ley)

logger = logging.getLogger("resumen_censo_limpio")

NUEVO = "evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet"
VIEJO = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"
SALIDA = "evaluacion/baseline/outputs/censo_limpio_2026-09-28.json"
PUBLICADO = "evaluacion/baseline/outputs/baseline_voto_individual.json"

COLS = {"viejo_publicado": "p_viejo",                       # harness con fuga (shift(1), sin origen)
        "motor_dia_incluido__tema": "p__dia_incluido__tema",  # motor con su `<=`
        "motor_dia_incluido__general": "p__dia_incluido__general",
        "motor_fecha__tema": "p__fecha__tema",                # motor `<`, sin excluir la ley
        "motor_estricta__tema": "p__estricta__tema",          # limpio, RECORD_POR_TEMA prendido
        "motor_estricta__general": "p__estricta__general"}    # limpio, RECORD_POR_TEMA apagado


def columna_publicada() -> str:
    """La variante que ES el motor hoy: historia estricta y RECORD_POR_TEMA según su
    bandera (apagada desde el 28-09, ADR-0034)."""
    import nowcast_puertas as NP
    return f"p__estricta__{'tema' if NP.RECORD_POR_TEMA else 'general'}"


def _skill(p, y) -> float:
    y = np.asarray(y, float)
    bb = float(((y.mean() - y) ** 2).mean())
    return round(1 - float(((np.asarray(p, float) - y) ** 2).mean()) / bb, 4) if bb > 0 else None


def tabla_skill(d: pd.DataFrame, cols: dict) -> dict:
    """skill (con IC por ley) de cada columna, global / por era / por cámara."""
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)
    cortes = {"global": np.ones(len(d), bool),
              **{f"era={e}": (era == e).to_numpy() for e in ERA_LABELS},
              **{f"camara={c}": (d["camara"] == c).to_numpy() for c in ("diputados", "senado")}}
    out = {}
    for nom, m in cortes.items():
        fila = {"n_votos": int(m.sum()), "n_leyes": int(d.loc[m, "ley"].nunique())}
        for k, c in cols.items():
            fila[k] = {"skill": _skill(d.loc[m, c], d.loc[m, "y"]),
                       "ic95_ley": skill_ic_por_ley(d.loc[m, c], d.loc[m, "y"], d.loc[m, "ley"])}
        out[nom] = fila
    return out


def record_por_tema(d: pd.DataFrame, con: str, sin: str) -> dict:
    """ΔBrier relativo (tema − general), IC por ley. En el total y en lo que TOCA (votos
    donde las dos columnas difieren: actas con áreas sustantivas y dato por área)."""
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)
    toca = (d[con] - d[sin]).abs().to_numpy() > 1e-12
    cortes = {"global": np.ones(len(d), bool), "toca": toca,
              **{f"toca&camara={c}": toca & (d["camara"] == c).to_numpy()
                 for c in ("diputados", "senado")},
              **{f"toca&era={e}": toca & (era == e).to_numpy() for e in ERA_LABELS}}
    out = {"frac_votos_que_toca": round(float(toca.mean()), 4)}
    for nom, m in cortes.items():
        if m.sum() == 0:
            continue
        r = dif_brier_ic_por_ley(d.loc[m, con], d.loc[m, sin], d.loc[m, "y"], d.loc[m, "ley"])
        r.update({"n_votos": int(m.sum()), "n_leyes": int(d.loc[m, "ley"].nunique()),
                  "brier_general": round(float(((d.loc[m, sin] - d.loc[m, "y"]) ** 2).mean()), 5),
                  "brier_tema": round(float(((d.loc[m, con] - d.loc[m, "y"]) ** 2).mean()), 5),
                  "mejora_relativa_%": round(-r["dBrier_rel_%"], 2)})
        out[nom] = r
    return out


def reevaluar_adr0018(d: pd.DataFrame, sufijo: str) -> dict:
    """Las dos decisiones del 06-09 (ADR-0018) que se tomaron con el harness con fuga:
    ENCOGER el récord hacia el bloque (vs. cortarlo) y bajar MIN_HIST de 8 a 1. Se
    recalculan con `perfil_legislador` del motor sobre los insumos que el censo guardó
    voto a voto (share, desvío, récord, n): la misma P_i, cambiando sólo ese parámetro."""
    import nowcast_puertas as NP
    s, dv = d[f"share{sufijo}"].to_numpy(float), d[f"desvio{sufijo}"].to_numpy(float)
    r, n = d[f"record{sufijo}"].to_numpy(object), d[f"n_prev{sufijo}"].to_numpy(float)

    def _p(**kw):
        return np.array([NP.perfil_legislador(a, b, record=(None if c is None or c != c else c),
                                              n_emitidos=int(e), **kw)["p_afirma_si_vota"]
                         for a, b, c, e in zip(s, dv, r, n)])
    base = d[f"p{sufijo}"].to_numpy(float)
    chk = _p()
    if np.abs(chk - base).max() > 1e-12:
        raise RuntimeError("perfil_legislador no reproduce la P del censo: los insumos no cierran")
    brazos = {"motor (encoge, n>=1)": base, "corta sin encoger (n>=1)": _p(shrink=False),
              "encoge, n>=8": _p(min_hist=8)}
    y, ley = d["y"].to_numpy(float), d["ley"]
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)
    out = {}
    for nom, p in brazos.items():
        fila = {"skill": _skill(p, y), "skill_desde_2023": _skill(p[(era == "desde 2023").to_numpy()],
                                                                   y[(era == "desde 2023").to_numpy()])}
        if nom != "motor (encoge, n>=1)":
            fila["vs_motor"] = dif_brier_ic_por_ley(p, base, y, ley)
        out[nom] = fila
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    d = pd.read_parquet(REPO / NUEVO)
    viejo = pd.read_parquet(REPO / VIEJO)[["acta_id", "legislador", "p", "y"]].rename(
        columns={"p": "p_viejo", "y": "y_viejo"})
    d["ley"] = d["ley"].fillna("acta:" + d["acta_id"].astype(str))
    rep: dict = {"censo": NUEVO, "n_votos": int(len(d)), "n_actas": int(d["acta_id"].nunique()),
                 "n_leyes": int(d["ley"].nunique()),
                 "frac_votos_sin_ley": round(float(d["ley"].str.startswith("acta:").mean()), 4)}

    # ── FASE 3: el número publicado nuevo (el motor como está, historia estricta) ──
    col_pub = columna_publicada()
    rep["publicado_nuevo"] = resumir(d, col_pub)
    rep["publicado_nuevo"]["variante"] = col_pub

    # ── la comparación antes/después sobre los MISMOS votos ──
    m = d.merge(viejo, on=["acta_id", "legislador"], how="inner", validate="1:1")
    rep["mismos_votos"] = {"n_votos_nuevo": int(len(d)), "n_votos_viejo": int(len(viejo)),
                           "n_en_comun": int(len(m)),
                           "y_coincide": bool((m["y"] == m["y_viejo"]).all())}
    if not rep["mismos_votos"]["y_coincide"]:
        raise RuntimeError("el voto real difiere entre los dos censos: no son los mismos votos")
    rep["descomposicion"] = tabla_skill(m, COLS)
    rep["por_fuente_direccion_mismos_votos"] = {
        k: {f: _metricas(g[c].values, g["y"].values) for f, g in m.groupby("fuente")}
        for k, c in COLS.items() if c != "p_viejo"}
    for k, c in COLS.items():
        if c != "p_viejo":
            f = "fuente" + c[1:] if "fuente" + c[1:] in m else "fuente"   # la principal
            rep["por_fuente_direccion_mismos_votos"][k] = {
                fu: _metricas(g[c].values, g["y"].values)
                for fu, g in m.groupby(m[f].map(lambda x: "bloque" if x == "bloque" else "record"))}
    rep["viejo_publicado_por_su_fuente"] = resumir(m.assign(fuente="record"), "p_viejo")["global"]

    # ── FASE 4.1: RECORD_POR_TEMA con el harness limpio, y en el mundo con fuga ──
    rep["record_por_tema"] = {
        "limpio (estricta)": record_por_tema(d, "p__estricta__tema", "p__estricta__general"),
        "con la fuga del motor (dia_incluido)": record_por_tema(
            d, "p__dia_incluido__tema", "p__dia_incluido__general"),
    }
    # ── ADR-0018 (fila 4 del tablero) re-evaluado con el harness limpio ──
    rep["adr0018_reevaluado"] = {"record_general": reevaluar_adr0018(d, "__estricta__general")}
    out = REPO / SALIDA
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # lo que va al pie del censo (lo que lee el MAPA y cualquiera que abra outputs/)
    pub = dict(rep["publicado_nuevo"])
    pub["_nota"] = ("ADR-0034 (28-09-2026): censo con el harness que IMPORTA el motor, historia "
                    "estricta (fecha anterior y otra ley). Reemplaza al 0,1611 publicado, que "
                    "estaba inflado por fuga. Detalle: " + SALIDA)
    (REPO / PUBLICADO).write_text(json.dumps(pub, ensure_ascii=False, indent=1, default=str),
                                  encoding="utf-8")

    g = rep["descomposicion"]
    print("publicado:", col_pub, rep["publicado_nuevo"]["global"]["skill"])
    for corte in ("global", "era=desde 2023", "era=2019-2023", "camara=diputados", "camara=senado"):
        print(corte, {k: g[corte][k]["skill"] for k in COLS})
    rt = rep["record_por_tema"]
    for k, v in rt.items():
        print(k, {c: (v[c]["mejora_relativa_%"], v[c]["ic95_rel_%_ley"])
                  for c in ("global", "toca") if c in v})
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
