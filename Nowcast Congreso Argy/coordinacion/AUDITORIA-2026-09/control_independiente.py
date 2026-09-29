# -*- coding: utf-8 -*-
"""Control independiente de la auditoría 2026-09 (Fase 2).

QUÉ HACE. Reimplementa, desde el voto crudo y SIN importar el motor ni el harness
(`modelo/`, `variables/`, `evaluacion/`, `definiciones`, `rutas`: se verifica por AST al
final), un puñado de predictores del voto emitido y los mide sobre los MISMOS 691.845
votos del censo, con la misma métrica (skill contra la climatología en la muestra) y el
mismo IC (Poisson-bootstrap re-muestreando LEYES). Responde tres preguntas:

  1. ¿El motor le gana a un predictor trivial hecho aparte?
  2. ¿Un récord propio hecho aparte, con fecha estricta y otra ley, cae cerca del 0,13?
     (si sí, el 0,1333 no depende de la implementación del harness)
  3. ¿Este mismo código detecta una fuga si se la ponemos a propósito? (control positivo)

QUÉ NO HACE. No usa la ficha de desvío, β, ε₀, τ, la presencia ni las puertas.

USO:  python coordinacion/AUDITORIA-2026-09/control_independiente.py [--detalle RUTA] [--salida RUTA]
Escribe por defecto en Archivos_Borrar/auditoria/control_independiente.json (gitignored).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CLEAN = RAIZ / "datos" / "canonica" / "data" / "clean"
ORIGEN = RAIZ / "variables" / "proyecto" / "data" / "origen_por_acta.parquet"
DETALLE = RAIZ / "evaluacion" / "baseline" / "outputs" / "censo_detalle_2026-09-28.parquet"
SALIDA = RAIZ / "Archivos_Borrar" / "auditoria" / "control_independiente.json"

ERAS = pd.to_datetime(["1990-01-01", "2011-12-10", "2015-12-10", "2019-12-10", "2023-12-10", "2030-01-01"])
ERA_LAB = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]
K = 5.0            # pseudo-conteo del encogimiento (el mismo valor que usa el motor, a propósito)
N_BOOT = 2000
SEMILLA = 11
VACIOS = {"", "NAN", "NONE", "DESCONOCIDO", "SIN DATO", "S/D"}


def cargar(detalle_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(historia, evaluados). Historia = todos los votos emitidos; evaluados = los del censo."""
    v = pd.read_parquet(CLEAN / "votos_resuelto.parquet",
                        columns=["acta_id", "legislador_id", "bloque_linaje", "voto"])
    a = pd.read_parquet(CLEAN / "actas_canonico.parquet", columns=["acta_id", "fecha", "camara"])
    a["fecha"] = pd.to_datetime(a["fecha"], errors="coerce")
    v = v.merge(a, on="acta_id", how="left")
    v = v[v["voto"].isin(["AFIRMATIVO", "NEGATIVO"]) & v["fecha"].notna() & v["bloque_linaje"].notna()].copy()
    v["af"] = (v["voto"] == "AFIRMATIVO").astype(float)
    v["acta_id"] = v["acta_id"].astype(str)

    o = pd.read_parquet(ORIGEN, columns=["acta_id", "origen"])
    o["acta_id"] = o["acta_id"].astype(str)
    o["origen"] = o["origen"].astype(str).str.upper().where(lambda s: ~s.isin(VACIOS))
    v = v.merge(o, on="acta_id", how="left")

    # OJO: la columna `p` del detalle es la variante que la BANDERA RECORD_POR_TEMA dejaba al momento de
    # generarlo (con el detalle del 28-09 13:58, prendida = con récord por tema). El motor "de hoy" es
    # `p__estricta__general` (bandera apagada); es lo que usa `resumen_censo_limpio.columna_publicada()`.
    d = pd.read_parquet(detalle_path, columns=["acta_id", "legislador", "linaje", "ley", "y", "fecha", "camara",
                                               "p__estricta__general", "p__estricta__tema",
                                               "p__dia_incluido__general"])
    d["acta_id"] = d["acta_id"].astype(str)
    d = d.rename(columns={"legislador": "legislador_id"})

    # linaje y ley de los evaluados; para el resto, el crudo y "acta:<id>" (cada acta su propia ley)
    clave = d[["acta_id", "legislador_id", "linaje"]].drop_duplicates(["acta_id", "legislador_id"])
    v = v.merge(clave, on=["acta_id", "legislador_id"], how="left")
    v["linaje"] = v["linaje"].fillna(v["bloque_linaje"].astype(str))
    ley = d.drop_duplicates("acta_id").set_index("acta_id")["ley"]
    v["ley"] = v["acta_id"].map(ley).fillna("acta:" + v["acta_id"])
    v["era"] = pd.cut(v["fecha"], ERAS, labels=ERA_LAB, right=False).astype(str)

    e = d.merge(v[["acta_id", "legislador_id", "origen", "era"]].drop_duplicates(["acta_id", "legislador_id"]),
                on=["acta_id", "legislador_id"], how="left")
    return v, e


def _prev(v: pd.DataFrame, keys: list[str], inclusive: bool = False) -> pd.DataFrame:
    """(n, a) de emitidos y afirmativos de FECHAS ESTRICTAMENTE ANTERIORES dentro de `keys`.
    `inclusive=True` (sólo para el control positivo) suma también la fecha propia."""
    g = (v.groupby(keys + ["fecha"], sort=False)
          .agg(n=("af", "size"), a=("af", "sum")).reset_index().sort_values(keys + ["fecha"]))
    cs = g.groupby(keys, sort=False)[["n", "a"]].cumsum()
    if not inclusive:
        cs = cs - g[["n", "a"]]
    g[["n", "a"]] = cs
    return g


def historia(e: pd.DataFrame, v: pd.DataFrame, keys: list[str], ley: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """(n, a) de la historia estricta (y de OTRA ley si `ley`) para cada fila de `e`."""
    m = e[keys + ["fecha"]].merge(_prev(v, keys)[keys + ["fecha", "n", "a"]], on=keys + ["fecha"], how="left")
    n, a = m["n"].fillna(0).to_numpy(float), m["a"].fillna(0).to_numpy(float)
    if ley:
        k2 = keys + ["ley"]
        mm = e[k2 + ["fecha"]].merge(_prev(v, k2)[k2 + ["fecha", "n", "a"]], on=k2 + ["fecha"], how="left")
        n, a = n - mm["n"].fillna(0).to_numpy(float), a - mm["a"].fillna(0).to_numpy(float)
    return n, a


def predictores(e: pd.DataFrame, v: pd.DataFrame) -> dict:
    tiene_o = e["origen"].notna().to_numpy()
    e = e.copy()
    e["origen"] = e["origen"].fillna("_")
    v = v.copy()
    v["origen"] = v["origen"].fillna("_")
    v = v.dropna(subset=["era"])

    n_b, a_b = historia(e, v, ["camara", "era"])
    base = np.where(n_b > 0, a_b / np.maximum(n_b, 1), 0.5)
    n_l, a_l = historia(e, v, ["camara", "linaje", "era"])
    bloque = (a_l + K * base) / (n_l + K)
    n_r, a_r = historia(e, v, ["legislador_id", "era"])
    rec = np.where(n_r > 0, a_r / np.maximum(n_r, 1), np.nan)
    p1 = np.where(n_r > 0, rec, bloque)
    p4 = (a_r + K * bloque) / (n_r + K)

    # con ORIGEN (sólo donde se conoce; el resto cae a p4, como el motor cae a no condicionar)
    n_lo, a_lo = historia(e, v, ["camara", "linaje", "era", "origen"])
    bloque_o = (a_lo + K * bloque) / (n_lo + K)
    n_ro, a_ro = historia(e, v, ["legislador_id", "era", "origen"])
    p6 = np.where(tiene_o, (a_ro + K * bloque_o) / (n_ro + K), p4)

    # persistencia ingenua: cómo votó su última fecha anterior (NO excluye la ley: es un ingenuo)
    dia = v.groupby(["legislador_id", "fecha"], sort=False)["af"].mean().reset_index().sort_values(["legislador_id", "fecha"])
    dia["ult"] = dia.groupby("legislador_id", sort=False)["af"].shift(1)
    ult = e[["legislador_id", "fecha"]].merge(dia[["legislador_id", "fecha", "ult"]], on=["legislador_id", "fecha"], how="left")["ult"].to_numpy()
    p5 = np.where(np.isnan(ult), p4, np.clip(ult, 0.05, 0.95))

    # CONTROL POSITIVO: la misma cuenta que p4 pero dejando entrar a las otras actas de la MISMA FECHA
    inc = _prev(v, ["legislador_id", "era"], inclusive=True)
    mi = e[["legislador_id", "era", "fecha"]].merge(inc[["legislador_id", "era", "fecha", "n", "a"]],
                                                    on=["legislador_id", "era", "fecha"], how="left")
    n_f, a_f = mi["n"].fillna(0).to_numpy(float) - 1.0, mi["a"].fillna(0).to_numpy(float) - e["y"].to_numpy(float)
    p_fuga = (a_f + K * bloque) / (np.maximum(n_f, 0) + K)

    return {"climatologia_walkforward": base, "bloque_ingenuo": bloque, "record_puro": p1,
            "record_encogido_al_bloque": p4, "record_encogido_con_origen": p6,
            "persistencia_ultima_fecha": p5,
            "CONTROL_POSITIVO_record_con_fuga_del_mismo_dia": p_fuga}


def skill_y_ic(se: dict, y: np.ndarray, ley: np.ndarray, comparar: str | None = None) -> dict:
    """skill (1 − Brier/Brier climatología de la muestra) con IC 95% Poisson-bootstrap sobre LEYES;
    y, si `comparar`, ΔBrier pareado (predictor − comparar), IC sobre leyes."""
    cod, uniq = pd.factorize(ley)
    k = len(uniq)
    cnt = np.bincount(cod, minlength=k).astype(float)
    sy = np.bincount(cod, weights=y, minlength=k)
    agg = {c: np.bincount(cod, weights=s, minlength=k) for c, s in se.items()}
    W = np.random.default_rng(SEMILLA).poisson(1.0, (N_BOOT, k)).astype(float)
    Nb, Yb = W @ cnt, W @ sy
    bb = Yb / Nb
    bb = bb - bb ** 2
    N, Y = cnt.sum(), sy.sum()
    b = Y / N
    out = {}
    for c, s in agg.items():
        pt = 1 - (s.sum() / N) / (b - b ** 2)
        bs = 1 - ((W @ s) / Nb) / bb
        fila = {"skill": round(float(pt), 4), "ic95_ley": [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
                "brier": round(float(s.sum() / N), 5)}
        if comparar and c != comparar:
            d_pt = s.sum() / N - agg[comparar].sum() / N
            d_bs = (W @ s) / Nb - (W @ agg[comparar]) / Nb
            fila["dBrier_vs_" + comparar] = {"pt": round(float(d_pt), 5),
                                              "ic95_ley": [round(float(np.percentile(d_bs, 2.5)), 5), round(float(np.percentile(d_bs, 97.5)), 5)]}
        out[c] = fila
    return {"n_votos": int(N), "n_leyes": int(k), "tasa_base": round(float(b), 4), "predictores": out}


def verificar_independencia() -> list[str]:
    """Imports de ESTE archivo: ninguno puede ser del motor, del harness ni de rutas/definiciones."""
    prohibidos = {"modelo", "variables", "evaluacion", "definiciones", "rutas", "nowcast_puertas",
                  "baseline_voto_individual", "ensemble", "bloque", "agregador"}
    arbol = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    mal = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            mal += [a.name for a in nodo.names if a.name.split(".")[0] in prohibidos]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.split(".")[0] in prohibidos:
            mal.append(nodo.module)
    return mal


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalle", default=str(DETALLE))
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    mal = verificar_independencia()
    if mal:
        raise SystemExit(f"NO es independiente: importa {mal}")
    v, e = cargar(Path(a.detalle))
    e = e.dropna(subset=["era"]).reset_index(drop=True)
    pred = predictores(e, v)
    y = e["y"].to_numpy(float)
    cand = {"MOTOR (p__estricta__general, el de hoy)": e["p__estricta__general"].to_numpy(float),
            "motor con récord por tema (el de hasta el 28-09)": e["p__estricta__tema"].to_numpy(float),
            "motor con su corte viejo (día incluido, sin excluir ley)": e["p__dia_incluido__general"].to_numpy(float),
            **pred}
    se = {k: (p - y) ** 2 for k, p in cand.items()}
    cortes = {"global": np.ones(len(e), bool)}
    for era in ERA_LAB:
        cortes[f"era={era}"] = (e["era"] == era).to_numpy()
    for cam in ("diputados", "senado"):
        cortes[f"camara={cam}"] = (e["camara"] == cam).to_numpy()
    res = {"independiente_por_AST": True, "n_evaluados": int(len(e)), "n_boot": N_BOOT, "cortes": {}}
    for nom, m in cortes.items():
        res["cortes"][nom] = skill_y_ic({k: s[m] for k, s in se.items()}, y[m], e["ley"].to_numpy()[m],
                                        comparar="MOTOR (p__estricta__general, el de hoy)")
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    g = res["cortes"]["global"]
    print(f"votos={g['n_votos']:,} leyes={g['n_leyes']:,} tasa_base={g['tasa_base']}")
    for k, f in g["predictores"].items():
        print(f"  {k:<62} skill {f['skill']:>7}  IC {f['ic95_ley']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
