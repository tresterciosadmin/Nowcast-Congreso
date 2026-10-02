# -*- coding: utf-8 -*-
"""Auditoría 2026-09, D1.0 — qué cambió en el censo al pasar a la ficha de desvío AL DÍA (criterios 4 y 5a del
pre-registro de D1.0 en `ESTADO-EJECUCION.md`). Mide; no decide nada (D1.0 es una corrección decidida por Franco).

Compara el detalle del censo nuevo (motor con la ficha al día) contra el del 28-09 (el harness ponía el desvío del
linaje en la rama de bloque), voto por voto:

  4a. los mismos pares (acta, legislador);
  4b. en la RAMA DEL RÉCORD, max|Δp| = 0 en las cinco variantes con nombre; sólo cambian votos de la rama de bloque;
  4c. con MIN_HIST = 1 y MIN_VOTOS_FICHA = 20, recalcular la P_i desde las columnas guardadas (`share`, `record`,
      `n_prev`, `ficha_*`) da max|Δp| = 0 contra la `p` del censo nuevo (lo que D1 va a hacer con otras grillas);
  5a. ΔBrier relativo pareado (nuevo − 28-09, positivo = el nuevo empeora) en la variante del motor
      (`p__estricta__general`), sobre los votos de la rama de bloque del panel fuera de muestra (Diputados desde 2006,
      Senado desde 2007: el del protocolo de la fase D) y sobre el global de ese panel, con IC por ley y por mes
      (2.000 réplicas, semilla 7), y por era y por cámara (descriptivo).

    python coordinacion/AUDITORIA-2026-09/medir_ficha_al_dia.py --nuevo <detalle del censo nuevo> [--salida <json>]
    (el resultado de D1.0 está en la carpeta `resultados/` de la auditoría, `ficha_al_dia_D1_0.json`)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import censo_estadisticos as ce  # noqa: E402

VIEJO = RAIZ / "evaluacion" / "baseline" / "outputs" / "censo_detalle_2026-09-28.parquet"
VARIANTES = ("estricta__general", "estricta__tema", "fecha__tema", "dia_incluido__tema", "dia_incluido__general")
OOS = {"diputados": "2006-01-01", "senado": "2007-01-01"}     # el panel fuera de muestra del protocolo de D
ERAS = pd.to_datetime(["1990-01-01", "2011-12-10", "2015-12-10", "2019-12-10", "2023-12-10", "2030-01-01"])
ERA_LAB = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]
N_BOOT, SEMILLA = 2000, 7
MIN_HIST, MIN_VOTOS_FICHA, K = 1, 20, 5.0


def escalera(t: pd.DataFrame, min_votos: int) -> np.ndarray:
    """`ensemble.desvio_de_ficha`, vectorizada sobre las columnas `ficha_*` del detalle."""
    rec = t["ficha_tasa_desvio_reciente_conducta"].where(t["ficha_tasa_desvio_reciente_conducta"].notna(),
                                                         t["ficha_tasa_desvio_reciente"])
    glo = t["ficha_tasa_desvio_conducta"].where(t["ficha_tasa_desvio_conducta"].notna(), t["ficha_tasa_desvio"])
    usa_rec = rec.notna() & (t["ficha_n_reciente"].fillna(0) >= min_votos)
    usa_glo = ~usa_rec & glo.notna() & (t["ficha_n_votos"].fillna(0) >= min_votos)
    d = np.where(usa_rec, rec, np.where(usa_glo, glo, t["ficha_desvio_linaje"]))
    return np.clip(d.astype(float), 0.0, 1.0)


def recalcular(t: pd.DataFrame, min_hist: int, min_votos: int, k: float) -> np.ndarray:
    """`nowcast_puertas.perfil_legislador` vectorizada (encogimiento prendido), desde las columnas del detalle."""
    s = t["share"].clip(0, 1).values
    d = escalera(t, min_votos)
    n = t["n_prev"].fillna(0).values.astype(float)
    rec = t["record"].astype(float).values
    usa = ~np.isnan(rec) & (n >= min_hist)
    p_rec = (n * np.clip(np.nan_to_num(rec), 0, 1) + k * s) / (n + k)
    p_blo = s * (1 - d) + (1 - s) * d / 2
    return np.where(usa, p_rec, p_blo)


def dbrier(p1, p0, y, grupo) -> dict:
    e1, e0 = (np.asarray(p1) - y) ** 2, (np.asarray(p0) - y) ** 2
    g = pd.DataFrame({"g": np.asarray(grupo), "d": e1 - e0, "b0": e0}).groupby("g", sort=True)
    s = g.agg(d=("d", "sum"), b0=("b0", "sum"), n=("d", "size"))
    return ce.dif_brier_ic_desde_sumas(s["d"].values, s["b0"].values, s["n"].values, N_BOOT, SEMILLA)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nuevo", required=True)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    nuevo = pd.read_parquet(a.nuevo)
    viejo = pd.read_parquet(VIEJO, columns=["acta_id", "legislador"] + [f"p__{v}" for v in VARIANTES])
    claves = ["acta_id", "legislador"]
    m = nuevo.merge(viejo, on=claves, how="outer", suffixes=("", "_viejo"), indicator=True)
    out: dict = {"censo_nuevo": Path(a.nuevo).name, "censo_viejo": VIEJO.name,
                 "pares_nuevo": int(len(nuevo)), "pares_viejo": int(len(viejo)),
                 "solo_en_uno": int((m["_merge"] != "both").sum())}
    m = m[m["_merge"] == "both"].copy()
    # 4b: la rama del récord no cambia; sólo la de bloque
    out["por_variante"] = {}
    for v in VARIANTES:
        fn = "fuente" if v == "estricta__general" else f"fuente__{v}"
        fuente_nueva = m[fn] if fn in m else m["fuente"]
        dp = (m[f"p__{v}"] - m[f"p__{v}_viejo"]).abs()
        bloque = fuente_nueva.eq("bloque")
        out["por_variante"][v] = {"max_abs_dp_rama_record": float(dp[~bloque].max()),
                                  "votos_rama_bloque": int(bloque.sum()),
                                  "votos_que_cambian": int((dp > 0).sum()),
                                  "votos_que_cambian_fuera_de_la_rama_de_bloque": int(((dp > 0) & ~bloque).sum()),
                                  "max_abs_dp": float(dp.max())}
    # 4c: el recálculo desde las columnas reproduce la p del censo nuevo
    p_hat = recalcular(nuevo, MIN_HIST, MIN_VOTOS_FICHA, K)
    out["recalculo_desde_columnas_max_abs_dp"] = float(np.abs(p_hat - nuevo["p"].values).max())
    # 5a: ΔBrier pareado, variante del motor, panel OOS
    m["fecha"] = pd.to_datetime(m["fecha"])
    corte = m["camara"].map(OOS).pipe(pd.to_datetime)
    oos = m[m["fecha"] >= corte]
    y = oos["y"].values.astype(float)
    ley = oos["ley"].fillna("acta:" + oos["acta_id"].astype(str)).values
    mes = oos["fecha"].dt.to_period("M").astype(str).values
    p1, p0 = oos["p__estricta__general"].values, oos["p__estricta__general_viejo"].values
    bloque = oos["fuente"].eq("bloque").values
    era = pd.cut(oos["fecha"], ERAS, labels=ERA_LAB).astype(str).values

    def corte_de(mask, nombre):
        if not mask.any():
            return {"votos": 0}
        r = {"votos": int(mask.sum()), "leyes": int(pd.Series(ley[mask]).nunique()),
             "por_ley": dbrier(p1[mask], p0[mask], y[mask], ley[mask]),
             "por_mes": dbrier(p1[mask], p0[mask], y[mask], mes[mask])}
        print(f"  {nombre}: {r['votos']} votos, {r['leyes']} leyes; ΔBrier {r['por_ley']['dBrier_rel_%']}% "
              f"IC ley {r['por_ley']['ic95_rel_%_ley']} IC mes {r['por_mes']['ic95_rel_%_ley']}", flush=True)
        return r

    print("5a. ΔBrier relativo pareado (nuevo − 28-09), p__estricta__general, panel OOS")
    out["dbrier_oos"] = {"rama_de_bloque": corte_de(bloque, "rama de bloque"),
                         "global": corte_de(np.ones(len(y), bool), "global")}
    for c in ("diputados", "senado"):
        out["dbrier_oos"][f"rama_de_bloque_{c}"] = corte_de(bloque & (oos["camara"].values == c), f"rama de bloque, {c}")
    for e in ERA_LAB:
        out["dbrier_oos"][f"rama_de_bloque_era={e}"] = corte_de(bloque & (era == e), f"rama de bloque, {e}")
    print(json.dumps({k: v for k, v in out.items() if k != "dbrier_oos"}, ensure_ascii=False, indent=1))
    if a.salida:
        Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {a.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
