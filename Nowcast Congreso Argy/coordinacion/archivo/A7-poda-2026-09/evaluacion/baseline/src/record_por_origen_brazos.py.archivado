# -*- coding: utf-8 -*-
"""FASE 2 de `coordinacion/PROMPT-RECORD-POR-ORIGEN.md` — el récord por origen en el
censo, voto a voto, walk-forward, pareado contra lo de hoy.

Parte del detalle que deja `censo_detalle_paralelo.py` (share y desvío del linaje ya
proyectados por `proyectar_postura`, igual que el harness) y recomputa P con cada brazo:

  A1  harness hoy       récord de la era (guard), encogido k=5 hacia el share. = `p` del censo.
  A2  espejo del motor  el récord de la era condicionado por el ORIGEN del acta, como
                        `nowcast_puertas.alineacion_individual` (el harness no lo hacía).
  A0  guard off         récord de toda la historia, encogido (A0o: condicionado por origen).
  B1  guard on + rho    logit(P_A2) + lambda * w * rho_heredado * s_o   (el término del prompt)
                        s_o = +1 EJECUTIVO, -1 OPOSICION, 0 si no; rho_heredado = rho de la
                        era anterior relabelado al lado de hoy; w = 1 ('const') o
                        k/(n_era_origen + k) ('decae'). lambda elegido dejando una era afuera.
  B2  guard off + relación  el récord SIN cortar por era, pero condicionado por la RELACIÓN
                        del legislador con quien trae el proyecto: 'propio' (s_o*s_i=+1) o
                        'ajeno' (-1). Es la memoria anclada al rol que no se mueve con el
                        recambio. Donde la relación no está definida: A0o (B2) o A2 (B2h).

El lado del legislador HOY se estima walk-forward: tasa afirmativa de su linaje en su
cámara sobre las actas EJECUTIVO de la era ANTERIORES a la fecha, menos la de la cámara;
hace falta un mínimo de actas, si no el lado es 0 y no se hereda nada (se cuenta y se
reporta: nada cae a un default mudo).

    python evaluacion/baseline/src/record_por_origen_brazos.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("record_por_origen_brazos")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_por_origen import (K_SHRINK, UMBRAL_LADO, ORIGENES, ERAS, GOBIERNOS, REPO,  # noqa: E402
                               ORIGEN_POR_ACTA, ENLACE_TODAS, Panel, perfil_era,
                               cargar as cargar_panel, rho_heredado, signo_lado)

DETALLE = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"
MIN_ACTAS_LADO = 3
LAMBDAS = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
DIAS_ARRANQUE = 180
N_BOOT = 300
SEED = 7
_ERA_BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
             pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
_ERA_LABELS = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sig(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, float)))


def signo_origen(origen) -> np.ndarray:
    o = pd.Series(origen).astype(str).str.upper().to_numpy()
    return np.where(o == "EJECUTIVO", 1, np.where(o == "OPOSICION", -1, 0))


def ajustar_rho(p_base, rho_her, s_o, lam: float, w=1.0):
    """El término de la FASE 2 en logit. Con s_o = 0 o rho_her = 0 no mueve nada."""
    return _sig(_logit(p_base) + lam * np.asarray(w, float) * np.asarray(rho_her, float)
                * np.asarray(s_o, float))


# ───────────────────────────── features walk-forward ─────────────────────────────

HISTORIA_ESTRICTA = False


def _previos(df: pd.DataFrame, llave: list[str], estricta: bool | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(n, afirmativos) ANTERIORES de cada fila dentro de `llave`, en el orden del frame
    (el mismo `sort_values('fecha')` que el harness: mismo orden, mismo récord).

    `estricta`: sólo votos de FECHA anterior. El harness cuenta también las actas previas
    del MISMO día —artículos de la misma ley, en un orden arbitrario dentro de la
    sesión—, información que un nowcast hecho antes de la sesión no tiene. Medido el
    27-09: esa fuga explica ~40% del skill publicado (0,161 -> 0,092)."""
    estricta = HISTORIA_ESTRICTA if estricta is None else estricta
    g = df.groupby(llave, sort=False, observed=True)["af"]
    n = g.cumcount().to_numpy(float)
    a = (g.cumsum() - df["af"]).to_numpy(float)
    if estricta:
        g2 = df.groupby(llave + ["fecha"], sort=False, observed=True)["af"]
        n = n - g2.cumcount().to_numpy(float)
        a = a - (g2.cumsum() - df["af"]).to_numpy(float)
    return n, a


def cargar_votos() -> pd.DataFrame:
    """Los votos en el MISMO orden que `baseline_voto_individual.correr`."""
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar as cargar_bloque
    from definiciones import era_de
    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")
    inicio_a_era = {g[1]: g[0] for g in GOBIERNOS}
    mapa = {f: inicio_a_era[era_de(f)] for f in pd.unique(v["fecha"])}
    v["era"] = v["fecha"].map(mapa)
    opa = pd.read_parquet(REPO / ORIGEN_POR_ACTA).drop_duplicates("acta_id")
    ae = pd.read_parquet(REPO / ENLACE_TODAS).drop_duplicates("acta_id")
    v["origen_f"] = v["acta_id"].map(dict(zip(opa["acta_id"], opa["origen"]))).fillna("DESCONOCIDO")
    clu = (v["acta_id"].map(dict(zip(opa["acta_id"], opa["proyecto_id"])))
           .fillna(v["acta_id"].map(dict(zip(ae["acta_id"], ae["proyecto_id"]))))
           .fillna(v["acta_id"].map(dict(zip(opa["acta_id"], opa["expediente"])))))
    v["cluster"] = clu.where(clu.notna(), "acta:" + v["acta_id"].astype(str))
    v["legislador_id"] = v["legislador_id"].astype(str)
    v["bloque_linaje"] = v["bloque_linaje"].astype(str)
    return v


def lado_walk_forward(v: pd.DataFrame, min_actas: int = MIN_ACTAS_LADO) -> pd.Series:
    """Lado (+1/-1/0) de cada voto: su linaje, en su cámara, sobre las actas EJECUTIVO de
    la era con fecha ESTRICTAMENTE anterior. Centrado en la tasa de la cámara."""
    e = v[v["origen_f"] == "EJECUTIVO"]
    lin = (e.groupby(["era", "camara", "bloque_linaje", "fecha"], observed=True)["af"]
           .agg(n="size", a="sum").reset_index().sort_values("fecha"))
    lin[["cn", "ca"]] = lin.groupby(["era", "camara", "bloque_linaje"])[["n", "a"]].cumsum()
    cam = (e.groupby(["era", "camara", "fecha"], observed=True)
           .agg(n=("af", "size"), a=("af", "sum"), k=("acta_id", "nunique")).reset_index().sort_values("fecha"))
    cam[["cn_cam", "ca_cam", "ck_cam"]] = cam.groupby(["era", "camara"])[["n", "a", "k"]].cumsum()

    q = v[["era", "camara", "bloque_linaje", "fecha"]].copy()
    q["_i"] = np.arange(len(q))
    q = q.sort_values("fecha")
    q = pd.merge_asof(q, lin[["era", "camara", "bloque_linaje", "fecha", "cn", "ca"]],
                      on="fecha", by=["era", "camara", "bloque_linaje"], allow_exact_matches=False)
    q = pd.merge_asof(q.sort_values("fecha"), cam[["era", "camara", "fecha", "cn_cam", "ca_cam", "ck_cam"]],
                      on="fecha", by=["era", "camara"], allow_exact_matches=False)
    lado = q["ca"] / q["cn"] - q["ca_cam"] / q["cn_cam"]
    lado[(q["ck_cam"].fillna(0) < min_actas) | (q["cn"].fillna(0) < 1)] = np.nan
    s = pd.Series(signo_lado(lado.to_numpy()), index=q["_i"].to_numpy()).sort_index()
    return pd.Series(s.to_numpy(), index=v.index)


def heredado(v: pd.DataFrame, s_now: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """rho de la ÚLTIMA era anterior con dato de cada legislador (era completa, encogida,
    lado centrado por cámara: el objeto de la FASE 1) relabelado con el lado de hoy.
    Devuelve (rho_heredado, rho_prev_crudo)."""
    vp = cargar_panel()
    t = Panel(vp, perfil_era(vp)).tabla()
    orden = {e: i for i, e in enumerate(ERAS)}
    t["_o"] = t["era"].map(orden)
    prev = {}
    for lid, g in t.groupby("legislador_id"):
        g = g.sort_values("_o")
        prev[lid] = list(zip(g["_o"], g["rho"], g["s"]))
    rho_p = np.zeros(len(v))
    s_p = np.zeros(len(v), int)
    eo = v["era"].map(orden).to_numpy()
    lids = v["legislador_id"].to_numpy()
    cache: dict = {}
    for i in range(len(v)):
        k = (lids[i], eo[i])
        if k not in cache:
            cand = [x for x in prev.get(lids[i], []) if x[0] < eo[i]]
            cache[k] = (cand[-1][1], cand[-1][2]) if cand else (0.0, 0)
        rho_p[i], s_p[i] = cache[k]
    return rho_heredado(rho_p, s_p, s_now.to_numpy()), rho_p


def features(v: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=v.index)
    f["n_era"], f["a_era"] = _previos(v, ["legislador_id", "era"])
    f["n_hist"], f["a_hist"] = _previos(v, ["legislador_id"])
    conocido = v["origen_f"] != "DESCONOCIDO"
    tmp = v.assign(_o=v["origen_f"])
    f["n_era_o"], f["a_era_o"] = _previos(tmp, ["legislador_id", "era", "_o"])
    f["n_hist_o"], f["a_hist_o"] = _previos(tmp, ["legislador_id", "_o"])
    f["origen_conocido"] = conocido.to_numpy()
    f["s_o"] = signo_origen(v["origen_f"])
    f["s_now"] = lado_walk_forward(v)
    rel = f["s_o"] * f["s_now"]
    f["rel"] = rel
    # la relación de CADA voto pasado se define con el lado de SU momento
    tmp2 = v.assign(_rel=rel.to_numpy())
    n_rel, a_rel = _previos(tmp2, ["legislador_id", "_rel"])
    f["n_rel"], f["a_rel"] = np.where(rel != 0, n_rel, 0), np.where(rel != 0, a_rel, 0)
    f["rho_her"], f["rho_prev"] = heredado(v, f["s_now"])
    f["acta_id"] = v["acta_id"].to_numpy()
    f["legislador"] = v["legislador_id"].to_numpy()
    f["cluster"] = v["cluster"].to_numpy()
    f["era_nom"] = v["era"].to_numpy()
    f["origen_f"] = v["origen_f"].to_numpy()
    return f


# ───────────────────────────── brazos ─────────────────────────────

def _enc(a, n, s):
    return (a + K_SHRINK * s) / (n + K_SHRINK)


def brazos(d: pd.DataFrame) -> pd.DataFrame:
    s, dv = d["share"].to_numpy(float), d["desvio"].to_numpy(float)
    s = np.clip(s, 0, 1)
    dv = np.clip(dv, 0, 1)
    p_bloque = s * (1 - dv) + (1 - s) * (dv / 2)
    out = pd.DataFrame(index=d.index)
    out["A1"] = np.where(d["n_era"] >= 1, _enc(d["a_era"], d["n_era"], s), p_bloque)
    out["A0_raw"] = np.where(d["n_hist"] >= 1, d["a_hist"] / d["n_hist"].clip(lower=1), p_bloque)
    out["A0"] = np.where(d["n_hist"] >= 1, _enc(d["a_hist"], d["n_hist"], s), p_bloque)
    oc = d["origen_conocido"].to_numpy(bool)
    out["A2"] = np.where(oc, np.where(d["n_era_o"] >= 1, _enc(d["a_era_o"], d["n_era_o"], s), p_bloque),
                         out["A1"])
    out["A0o"] = np.where(oc, np.where(d["n_hist_o"] >= 1, _enc(d["a_hist_o"], d["n_hist_o"], s), p_bloque),
                          out["A0"])
    hay_rel = (d["rel"] != 0).to_numpy()
    p_rel = np.where(d["n_rel"] >= 1, _enc(d["a_rel"], d["n_rel"], s), p_bloque)
    out["B2"] = np.where(hay_rel, p_rel, out["A0o"])
    out["B2h"] = np.where(hay_rel, p_rel, out["A2"])
    return out


def cobertura(d: pd.DataFrame) -> dict:
    """Cuánto del término se apoya en dato real y cuánto cae a 'no heredar'. Avisa si
    cae todo: un 0,0% mudo ya costó una sesión entera (ADR-0030)."""
    eo = d["s_o"] != 0
    c = {
        "lado_hoy_definido": float((d["s_now"] != 0).mean()),
        "lado_hoy_definido_en_EJEC_OPOS": float((d.loc[eo, "s_now"] != 0).mean()) if eo.any() else 0.0,
        "rho_heredado_no_nulo_en_EJEC_OPOS": float((d.loc[eo, "rho_her"] != 0).mean()) if eo.any() else 0.0,
        "relacion_definida": float((d["rel"] != 0).mean()),
    }
    for k, val in c.items():
        nivel = logging.WARNING if val == 0 else logging.INFO
        logger.log(nivel, "cobertura %s = %.1f%%%s", k, 100 * val,
                   " -- NADA usa dato real, todo cae a no heredar" if val == 0 else "")
    return c


def pesos(d: pd.DataFrame, modo: str) -> np.ndarray:
    if modo == "const":
        return np.ones(len(d))
    return K_SHRINK / (d["n_era_o"].to_numpy(float) + K_SHRINK)


def _brier(p, y):
    return float(((np.asarray(p) - np.asarray(y)) ** 2).mean())


def elegir_lambda(d: pd.DataFrame, base: np.ndarray, modo: str) -> dict:
    """lambda dejando UNA era afuera: se elige con las otras eras y se evalúa en ésa.
    Sólo actúa donde hay rho heredado (eras con era anterior)."""
    w = pesos(d, modo)
    toca = (d["rho_her"] != 0) & (d["s_o"] != 0)
    eras = [e for e in d.loc[toca, "era_nom"].unique()]
    y = d["y"].to_numpy(float)
    p_oos = base.copy()
    elegidos = {}
    for e in eras:
        tr = toca & (d["era_nom"] != e)
        te = toca & (d["era_nom"] == e)
        mejor = min(LAMBDAS, key=lambda lam: _brier(
            ajustar_rho(base[tr], d.loc[tr, "rho_her"], d.loc[tr, "s_o"], lam, w[tr]), y[tr]))
        elegidos[e] = mejor
        p_oos[te.to_numpy()] = ajustar_rho(base[te], d.loc[te, "rho_her"], d.loc[te, "s_o"], mejor, w[te])
    curva = {lam: _brier(ajustar_rho(base[toca], d.loc[toca, "rho_her"], d.loc[toca, "s_o"], lam, w[toca]),
                         y[toca]) for lam in (0.0,) + LAMBDAS}
    return {"lambda_por_era_evaluada": elegidos, "p_oos": p_oos,
            "curva_brier_en_lo_que_toca_in_sample": curva}


def _metricas(p, y) -> dict:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    if len(y) == 0:
        return {}
    br, bb = _brier(p, y), float(((y.mean() - y) ** 2).mean())
    return {"n": int(len(y)), "brier": round(br, 5), "skill": round(1 - br / bb, 4) if bb > 0 else None}


def resumen(d: pd.DataFrame, cols: list[str], ref: str, n_boot: int = N_BOOT) -> dict:
    y = d["y"].to_numpy(float)
    era5 = pd.cut(d["fecha"], bins=_ERA_BINS, labels=_ERA_LABELS)
    inicio = pd.Series([pd.Timestamp(g[1]) for g in GOBIERNOS[1:]])
    arr = np.zeros(len(d), bool)
    for f0 in inicio:
        arr |= ((d["fecha"] >= f0) & (d["fecha"] < f0 + pd.Timedelta(days=DIAS_ARRANQUE))).to_numpy()
    cortes = {"global": np.ones(len(d), bool),
              **{f"era={e}": (era5 == e).to_numpy() for e in _ERA_LABELS},
              **{f"camara={c}": (d["camara"] == c).to_numpy() for c in ["diputados", "senado"]},
              f"arranque_{DIAS_ARRANQUE}d_de_era": arr,
              "toca_rho_heredado": ((d["rho_her"] != 0) & (d["s_o"] != 0)).to_numpy(),
              "toca_relacion": (d["rel"] != 0).to_numpy(),
              "origen_EJEC_u_OPOS": (d["s_o"] != 0).to_numpy()}
    cortes["toca_rho_heredado&desde 2023"] = cortes["toca_rho_heredado"] & cortes["era=desde 2023"]
    cortes["toca_relacion&desde 2023"] = cortes["toca_relacion"] & cortes["era=desde 2023"]

    # bootstrap de Poisson por EXPEDIENTE para la diferencia de Brier contra `ref`
    clus, cod = np.unique(d["cluster"].to_numpy(), return_inverse=True)
    rng = np.random.default_rng(SEED)
    W = rng.poisson(1.0, (n_boot, len(clus))).astype(np.float32)
    out = {}
    for nombre, m in cortes.items():
        if m.sum() == 0:
            continue
        fila = {c: _metricas(d[c].to_numpy()[m], y[m]) for c in cols}
        e_ref = (d[ref].to_numpy()[m] - y[m]) ** 2
        cm = cod[m]
        for c in cols:
            if c == ref:
                continue
            dif = (d[c].to_numpy()[m] - y[m]) ** 2 - e_ref
            num = np.bincount(cm, weights=dif, minlength=len(clus))
            den = np.bincount(cm, minlength=len(clus)).astype(float)
            bs = (W @ num) / np.maximum(W @ den, 1)
            fila[c]["dBrier_vs_" + ref] = round(float(dif.mean()), 6)
            fila[c]["ic95_expediente"] = [round(float(np.percentile(bs, 2.5)), 6),
                                          round(float(np.percentile(bs, 97.5)), 6)]
            fila[c]["dBrier_rel_%"] = round(100 * float(dif.mean()) / float(e_ref.mean()), 2)
        out[nombre] = fila
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalle", default=str(REPO / DETALLE))
    ap.add_argument("--salida", default=None)
    ap.add_argument("--historia", choices=["harness", "estricta"], default="estricta",
                    help="harness = cuenta las actas previas del mismo día (como el harness); "
                         "estricta = sólo fechas anteriores")
    args = ap.parse_args(argv)
    global HISTORIA_ESTRICTA
    HISTORIA_ESTRICTA = args.historia == "estricta"
    if args.salida is None:
        args.salida = str(REPO / f"evaluacion/baseline/outputs/record_por_origen_fase2_censo_{args.historia}_2026-09-27.json")
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")

    det = pd.read_parquet(args.detalle)
    v = cargar_votos()
    logger.info("features walk-forward sobre %d votos...", len(v))
    f = features(v)
    dup = f.duplicated(["acta_id", "legislador"]).sum()
    if dup:
        raise RuntimeError(f"{dup} (acta, legislador) duplicados en la canónica: el cruce no es 1 a 1")
    d = det.merge(f, on=["acta_id", "legislador"], how="left", validate="1:1")
    sin = d["n_era"].isna().sum()
    if sin:
        raise RuntimeError(f"{sin} votos del censo sin features: el cruce con la canónica está roto")
    br = brazos(d)
    d = pd.concat([d, br], axis=1)

    rep = {"n_votos": int(len(d)), "k": K_SHRINK, "umbral_lado": UMBRAL_LADO,
           "min_actas_lado": MIN_ACTAS_LADO}
    rep["historia"] = args.historia
    # el espejo: con la historia del harness, A1 recomputado tiene que ser su `p`
    dif = np.abs(d["A1"] - d["p"])
    rep["A1_vs_harness"] = {"max_abs": float(dif.max()), "frac_>1e-3": float((dif > 1e-3).mean())}
    if not HISTORIA_ESTRICTA and float((dif > 1e-3).mean()) > 0.001:
        logger.warning("A1 recomputado NO coincide con el harness en %.2f%% de los votos",
                       100 * float((dif > 1e-3).mean()))
    d["A1_harness"] = d["p"]
    # origen: el que usa el harness (tema_por_acta) contra origen_por_acta
    ho = d["origen"].fillna("DESCONOCIDO").astype(str).str.upper()
    rep["origen_harness_vs_origen_por_acta_coincide"] = float((ho == d["origen_f"].str.upper()).mean())
    rep["cobertura"] = cobertura(d)
    lam = {}
    for modo in ("const", "decae"):
        r = elegir_lambda(d, d["A2"].to_numpy(float), modo)
        d[f"B1_{modo}"] = r.pop("p_oos")
        lam[modo] = r
        r1 = elegir_lambda(d, d["A1"].to_numpy(float), modo)
        d[f"B1_{modo}_sobreA1"] = r1.pop("p_oos")
        lam[f"{modo}_sobreA1"] = r1
    rep["lambda"] = lam
    cols = ["A1_harness", "A1", "A2", "A0_raw", "A0", "A0o", "B1_const", "B1_decae",
            "B1_const_sobreA1", "B1_decae_sobreA1", "B2", "B2h"]
    rep["contra_A1_harness_hoy"] = resumen(d, cols, "A1")
    rep["contra_A2_espejo_motor"] = resumen(d, cols, "A2")
    rep["dos_por_dos"] = {
        "guard_on__origen_off": "A2 (motor hoy)",
        "guard_on__origen_on": "B1_decae / B1_const (A2 + rho heredado)",
        "guard_off__origen_off": "A0o (historia completa, condicionada por origen)",
        "guard_off__origen_on": "B2 (historia completa condicionada por la RELACIÓN propio/ajeno)",
    }
    out = Path(args.salida)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    d[["acta_id", "legislador", "fecha", "camara", "y"] + cols + ["rho_her", "s_o", "s_now", "rel"]].to_parquet(
        REPO / f"evaluacion/baseline/outputs/record_por_origen_fase2_detalle_{args.historia}_2026-09-27.parquet",
        index=False)
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
