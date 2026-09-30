# -*- coding: utf-8 -*-
"""FASES 1 y 2 de PROMPT-FIRMA-TEMATICA-DEL-DESVIO — persistencia de la firma temática
(individual, FASE 1) y de la cohesión de bloque por área (FASE 2) entre recambios.
    python evaluacion/baseline/src/firma_tematica_fase1_2.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import firma_tematica_desvio as f  # noqa: E402

K = f.K_SHRINK
UM = [3, 5, 10]
RNG = np.random.default_rng(20260921)
NOMBRE = {0: "2015", 1: "2019", 2: "2023"}


def _r(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _corr_boot(df, cx, cy, B=300):
    """Correlación + IC95 por bootstrap de LEGISLADORES (las celdas de un mismo
    legislador no son independientes)."""
    r = _r(df[cx], df[cy])
    if r is None:
        return {"n": int(len(df)), "r": None}
    grupos = [g[[cx, cy]].to_numpy() for _, g in df.groupby("legislador_id")]
    rs = []
    for _ in range(B):
        idx = RNG.integers(0, len(grupos), len(grupos))
        m = np.vstack([grupos[i] for i in idx])
        rr = _r(m[:, 0], m[:, 1])
        if rr is not None:
            rs.append(rr)
    lo, hi = np.percentile(rs, [2.5, 97.5]) if rs else (None, None)
    return {"n": int(len(df)), "n_leg": int(df.legislador_id.nunique()), "r": round(r, 4),
            "ic95": [round(float(lo), 3), round(float(hi), 3)] if lo is not None else None}


def armar_pares(d: pd.DataFrame, filtro="contestada") -> pd.DataFrame:
    """Pares (legislador, área, recambio) con las medidas antes/después:
       d_raw   : d_ik encogido hacia el propio d̄_i, SIN centrar       (control negativo)
       d_cen   : d_ik encogido − d̄_i                                   (la firma)
       d_cen2  : d_cen − media de (área, era) entre legisladores        (firma neta de efecto-área)
       rec_s   : tasa afirmativa por (leg, área), encogida a la media del área (ADR-0031)."""
    c = f.celdas(d, filtro)
    t = f.totales(d, filtro)
    c = c.merge(t, on=["legislador_id", "era"], how="left")
    c["d_raw"] = (c.n * c.d + K * c.dbar) / (c.n + K)
    c["d_cen"] = c.d_raw - c.dbar
    c["d_cen2"] = c.d_cen - c.groupby(["area", "era"])["d_cen"].transform("mean")

    x = f._filtrar(d, filtro)
    x = x[x.areas.map(len) > 0].explode("areas").rename(columns={"areas": "area"})
    x = x[x.voto.isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    x["af"] = (x.voto == "AFIRMATIVO").astype(int)
    rc = x.groupby(["legislador_id", "area", "era"])["af"].agg(n_af="size", rec="mean").reset_index()
    pri = x.groupby(["area", "era"])["af"].mean().rename("pri").reset_index()
    rc = rc.merge(pri, on=["area", "era"])
    rc["rec_s"] = (rc.n_af * rc.rec + K * rc.pri) / (rc.n_af + K)
    c = c.merge(rc[["legislador_id", "area", "era", "n_af", "rec_s"]],
                on=["legislador_id", "area", "era"], how="left")

    m = (d[d.presente].groupby(["legislador_id", "era"])
           .agg(bloque=("bloque_norm", lambda s: s.mode().iat[0]),
                linaje=("bloque_linaje", lambda s: s.mode().iat[0]),
                camara=("camara", lambda s: s.mode().iat[0])).reset_index())
    c = c.merge(m, on=["legislador_id", "era"], how="left")
    out = []
    for e in (0, 1, 2):
        a = c[c.era == e].drop(columns="era")
        b = c[c.era == e + 1].drop(columns="era")
        p = a.merge(b, on=["legislador_id", "area"], suffixes=("_a", "_b"))
        p["recambio"] = NOMBRE[e]
        out.append(p)
    p = pd.concat(out, ignore_index=True)
    p["mismo_bloque"] = p.bloque_a == p.bloque_b
    p["mismo_linaje"] = p.linaje_a == p.linaje_b
    p["camara"] = p.camara_b
    return p


def medir(p: pd.DataFrame, u: int) -> dict:
    q = p[(p.n_a >= u) & (p.n_b >= u)]
    res = {}
    for nombre, ca, cb in [("d_sin_centrar", "d_raw_a", "d_raw_b"), ("d_CENTRADA", "d_cen_a", "d_cen_b"),
                           ("d_centrada_neta_area", "d_cen2_a", "d_cen2_b")]:
        res[nombre] = _corr_boot(q, ca, cb)
    qr = q[(q.n_af_a >= u) & (q.n_af_b >= u)].dropna(subset=["rec_s_a", "rec_s_b"])
    res["record_afirmativo"] = _corr_boot(qr, "rec_s_a", "rec_s_b")
    return res


def cortes(p: pd.DataFrame, u: int = 3) -> dict:
    out = {}

    def m(df):
        q = df[(df.n_a >= u) & (df.n_b >= u)]
        return {"sin_centrar": _corr_boot(q, "d_raw_a", "d_raw_b", 200),
                "CENTRADA": _corr_boot(q, "d_cen_a", "d_cen_b", 200)}

    out["por_recambio"] = {r: m(p[p.recambio == r]) for r in NOMBRE.values()}
    out["por_camara"] = {c: m(p[p.camara == c]) for c in ("diputados", "senado")}
    q = p[(p.n_a >= u) & (p.n_b >= u)].copy()
    lv = q.groupby(["legislador_id", "recambio"])["dbar_a"].transform("first")
    q["_lv"] = lv
    t1, t2 = q.drop_duplicates(["legislador_id", "recambio"])["_lv"].quantile([1 / 3, 2 / 3])
    tr = {"bajo (disciplinados)": q[q._lv <= t1], "medio": q[(q._lv > t1) & (q._lv <= t2)],
          "alto (díscolos)": q[q._lv > t2]}
    out["por_tercil_dbar"] = {k: {"dbar_rango": [round(float(v._lv.min()), 4), round(float(v._lv.max()), 4)],
                                  "sin_centrar": _corr_boot(v, "d_raw_a", "d_raw_b", 200),
                                  "CENTRADA": _corr_boot(v, "d_cen_a", "d_cen_b", 200)} for k, v in tr.items()}
    out["por_continuidad_bloque"] = {"mismo_bloque": m(p[p.mismo_bloque]), "cambio_de_bloque": m(p[~p.mismo_bloque]),
                                     "mismo_linaje": m(p[p.mismo_linaje]), "cambio_de_linaje": m(p[~p.mismo_linaje])}
    return out


def validar_top_areas(p: pd.DataFrame, u: int = 3, tope: int = 2) -> dict:
    """¿Las áreas de mayor d~ ANTES son las de mayor d~ DESPUÉS? Por (legislador, recambio)
    con >=3 áreas con muestra a ambos lados; el azar exacto es k/m."""
    q = p[(p.n_a >= u) & (p.n_b >= u)]
    hits, esp, dif = [], [], []
    for (_, _), g in q.groupby(["legislador_id", "recambio"]):
        m = len(g)
        if m < 3:
            continue
        k = min(tope, m - 1)
        # desempate ALEATORIO: los díscolos-cero tienen muchos empates y `nlargest` desempata
        # por orden de fila (el mismo antes y después) -> inflaba la coincidencia.
        ga = g.assign(_j=RNG.random(m)).sort_values(["d_cen_a", "_j"], ascending=False)
        gb = g.assign(_j=RNG.random(m)).sort_values(["d_cen_b", "_j"], ascending=False)
        top_a = set(ga.area.iloc[:k])
        top_b = set(gb.area.iloc[:k])
        hits.append(len(top_a & top_b) / k)
        esp.append(k / m)
        ia = g.area.isin(top_a)
        dif.append(g[ia].d_cen_b.mean() - g[~ia].d_cen_b.mean())
    if not hits:
        return {"n_leg_recambio": 0}
    hits, esp, dif = np.array(hits), np.array(esp), np.array(dif)
    bs = [(hits[i] - esp[i]).mean() for i in (RNG.integers(0, len(hits), len(hits)) for _ in range(500))]
    return {"n_leg_recambio": int(len(hits)), "tope": tope,
            "coincidencia_top_antes_vs_despues": round(float(hits.mean()), 4),
            "esperada_por_azar": round(float(esp.mean()), 4),
            "exceso_sobre_azar": round(float((hits - esp).mean()), 4),
            "ic95_exceso": [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
            "d_cen_despues_top_menos_resto": round(float(dif.mean()), 4)}


# ---------------------------------------------------------------- FASE 2
def cohesion_por_area(d: pd.DataFrame, min_miembros: int = 5) -> pd.DataFrame:
    """c_{ℓ,k,e}: dispersión intra-LINAJE = 1 − (fracción del linaje que vota la conducta
    modal), promediada sobre actas contestadas del área k en la era e; sólo actas donde el
    linaje tiene >= min_miembros presentes con voto AF/NEG (control de tamaño)."""
    x = d[d.presente & d.contestada & d.voto.isin(["AFIRMATIVO", "NEGATIVO"]) & (d.areas.map(len) > 0)]
    g = x.groupby(["acta_id", "bloque_linaje", "era"]).agg(
        n=("voto", "size"), af=("voto", lambda s: (s == "AFIRMATIVO").sum()),
        areas=("areas", "first")).reset_index()
    g = g[g.n >= min_miembros].copy()
    g["disp"] = 1 - np.maximum(g.af, g.n - g.af) / g.n
    g = g.explode("areas").rename(columns={"areas": "area"})
    return (g.groupby(["bloque_linaje", "area", "era"])
             .agg(n_actas=("disp", "size"), c=("disp", "mean"), tam=("n", "mean")).reset_index())


def fase2(d: pd.DataFrame) -> dict:
    c = cohesion_por_area(d)
    c["c_cen"] = c.c - c.groupby(["bloque_linaje", "era"])["c"].transform("mean")
    out = {"n_celdas": int(len(c)),
           "correlacion_tamano_vs_dispersion": round(float(np.corrcoef(c.tam, c.c)[0, 1]), 4)}
    pares = []
    for e in (0, 1, 2):
        a = c[c.era == e].drop(columns="era")
        b = c[c.era == e + 1].drop(columns="era")
        p = a.merge(b, on=["bloque_linaje", "area"], suffixes=("_a", "_b"))
        p["recambio"] = NOMBRE[e]
        pares.append(p)
    p = pd.concat(pares, ignore_index=True)

    def cr(q, x, y):
        r = _r(q[x], q[y])
        return {"n_pares": int(len(q)), "r": None if r is None else round(r, 4)}

    def cr_boot(q, x, y, B=500):
        r = _r(q[x], q[y])
        if r is None:
            return {"n_pares": int(len(q)), "r": None}
        gs = [g[[x, y]].to_numpy() for _, g in q.groupby("bloque_linaje")]
        rs = []
        for _ in range(B):
            m = np.vstack([gs[i] for i in RNG.integers(0, len(gs), len(gs))])
            rr = _r(m[:, 0], m[:, 1])
            if rr is not None:
                rs.append(rr)
        return {"n_pares": int(len(q)), "n_linajes": len(gs), "r": round(r, 4),
                "ic95_boot_por_linaje": [round(float(np.percentile(rs, 2.5)), 3), round(float(np.percentile(rs, 97.5)), 3)]}

    bolsa = "OTRO / PROVINCIAL"
    for u in (3, 5):
        q = p[(p.n_actas_a >= u) & (p.n_actas_b >= u)]
        qs = q[q.bloque_linaje != bolsa]
        out[f"n_actas>={u}_SIN_bolsa_OTRO"] = {"sin_centrar": cr_boot(qs, "c_a", "c_b"),
                                                "CENTRADA": cr_boot(qs, "c_cen_a", "c_cen_b"),
                                                "por_recambio_CENTRADA": {r: cr(g, "c_cen_a", "c_cen_b") for r, g in qs.groupby("recambio")}}
        out[f"n_actas>={u}"] = {
            "sin_centrar": cr(q, "c_a", "c_b"), "CENTRADA": cr(q, "c_cen_a", "c_cen_b"),
            "por_recambio": {r: {"sin_centrar": cr(g, "c_a", "c_b"), "CENTRADA": cr(g, "c_cen_a", "c_cen_b")}
                             for r, g in q.groupby("recambio")}}
    e3 = c[(c.era == 3) & (c.n_actas >= 5)].copy()
    cols = ["bloque_linaje", "area", "n_actas", "c", "c_cen"]
    out["era_2023_mas_abiertas_que_su_promedio"] = e3.sort_values("c_cen", ascending=False).head(12)[cols].round(4).to_dict("records")
    out["era_2023_mas_cerradas"] = e3.sort_values("c_cen").head(6)[cols].round(4).to_dict("records")
    return out


def _mitades(xe: pd.DataFrame, mask: pd.Series, u: int) -> dict:
    sub = []
    for dd in (xe[mask], xe[~mask]):
        tot = dd.groupby("legislador_id")["desvio"].agg(nt="size", dbar="mean")
        ce = dd[dd.areas.map(len) > 0].explode("areas").rename(columns={"areas": "area"})
        ce = ce.groupby(["legislador_id", "area"])["desvio"].agg(n="size", d="mean").reset_index().merge(
            tot.reset_index(), on="legislador_id")
        ce["d_cen"] = (ce.n * ce.d + K * ce.dbar) / (ce.n + K) - ce.dbar
        sub.append((tot, ce))
    j = sub[0][0].join(sub[1][0], lsuffix="_a", rsuffix="_b", how="inner")
    j = j[(j.nt_a >= 10) & (j.nt_b >= 10)]
    pp = sub[0][1].merge(sub[1][1], on=["legislador_id", "area"], suffixes=("_a", "_b"))
    pp = pp[(pp.n_a >= u) & (pp.n_b >= u)]

    def rr(a, b):
        r = _r(a, b)
        return None if r is None else round(r, 4)
    return {"dbar_nivel_legislador": {"n": int(len(j)), "r": rr(j.dbar_a, j.dbar_b) if len(j) else None},
            "firma_d_CENTRADA_leg_area": {"n": int(len(pp)), "r": rr(pp.d_cen_a, pp.d_cen_b) if len(pp) else None}}


def split_half(d: pd.DataFrame, filtro="contestada", u: int = 3) -> dict:
    """Confiabilidad DENTRO de cada era. Tres particiones de las actas:
       - por_acta_al_azar        : ingenua; ACTAS de una misma ley caen en mitades opuestas
       - cronologica             : 1a vs 2a mitad de la era
       - por_expediente_entero   : cada LEY completa a una sola mitad (la que respeta que las
                                   actas de un mismo proyecto no son independientes)
       Si la firma existe sólo en la primera, es agrupamiento por ley, no perfil temático."""
    import zlib
    tpa = pd.read_parquet(f.REPO / "variables/proyecto/data/tema_por_acta.parquet")[["acta_id", "expediente"]]
    tpa = tpa.drop_duplicates("acta_id")
    x = f._filtrar(d, filtro).merge(tpa, on="acta_id", how="left")
    out = {}
    for e in range(4):
        xe = x[x.era == e].copy()
        res = {"actas_con_tema": int(xe[xe.areas.map(len) > 0].acta_id.nunique()),
               "expedientes_distintos_con_tema": int(xe[xe.areas.map(len) > 0].expediente.nunique())}
        fecha = xe.groupby("acta_id")["fecha"].first().sort_values(kind="stable")
        rank = {a: i for i, a in enumerate(fecha.index)}
        o = xe.acta_id.map(rank)
        res["por_acta_al_azar"] = _mitades(xe, xe.acta_id.map(lambda s: zlib.crc32(s.encode()) % 2 == 0), u)
        res["cronologica_1a_vs_2a_mitad"] = _mitades(xe, o <= o.max() / 2, u)
        con_tema = xe[xe.areas.map(len) > 0]
        if con_tema.expediente.notna().mean() < 0.5:
            # sin default silencioso: si no hay expediente, se dice
            res["por_expediente_entero"] = "n/d: las actas con tema de esta era no tienen expediente vinculado"
        else:
            res["por_expediente_entero"] = _mitades(
                xe, xe.expediente.map(lambda s: zlib.crc32(str(s).encode()) % 2 == 0), u)
        out[f"era{e}"] = res
    return out


def main() -> int:
    d = f.cargar_base_cache() if f.CACHE.exists() else f.construir_base()
    res = {"k_shrink": K, "filtro": "contestada (minoria>=10%)"}
    p = armar_pares(d)
    res["FASE1"] = {}
    for u in UM:
        res["FASE1"][f"n>={u}"] = {"pooled": medir(p, u),
                                   "por_recambio": {r: medir(p[p.recambio == r], u) for r in NOMBRE.values()}}
    res["FASE1_cortes_n>=3"] = cortes(p, 3)
    res["FASE1_cortes_n>=5"] = cortes(p, 5)
    res["FASE1_validacion_top_areas"] = {f"n>={u}": validar_top_areas(p, u) for u in (3, 5)}
    res["FASE1_composicion_universo"] = {
        "pares_n>=3": int(((p.n_a >= 3) & (p.n_b >= 3)).sum()),
        "dbar_antes_media_continuadores": round(float(p.dbar_a.mean()), 4),
        "dbar_media_todos_los_activos": round(float(f.totales(d).dbar.mean()), 4)}
    res["FASE1_split_half_dentro_de_era"] = split_half(d)
    res["FASE2"] = fase2(d)
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    print(txt)
    (f.REPO / "evaluacion/baseline/outputs/firma_tematica_fase1_2_2026-09-21.json").write_text(txt, encoding="utf-8")
    p.to_parquet(f.REPO / "Archivos_Borrar/firma_tematica_pares.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
