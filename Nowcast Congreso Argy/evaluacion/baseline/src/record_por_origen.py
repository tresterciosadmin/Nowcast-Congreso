# -*- coding: utf-8 -*-
"""FASE 0 y FASE 1 de `coordinacion/PROMPT-RECORD-POR-ORIGEN.md` — ¿el récord del
legislador condicionado por ORIGEN (lo que manda el Ejecutivo vs. lo que trae la
oposición) atraviesa el recambio de gobierno?

El objeto, por legislador i y era e:

    r_{i,o} = afirmativos / emitidos de i en actas de origen o,  o in {EJECUTIVO, OPOSICION}
    encogido EB (k=5) hacia el récord general de i en esa era
    rho_i   = r_{i,EJEC} - r_{i,OPOS}

El "lado" de i en la era e sale del DATO, con el criterio de `estimar_psi_arrastre.py`
(tasa afirmativa del linaje menos 1/2), agregado a la era: tasa afirmativa de SU linaje
en las actas de origen EJECUTIVO de esa era, menos 1/2. Signo = lado; |lado| < 0,10 es
ambiguo y se reporta aparte.

La persistencia de rho se mide SEPARADA entre los que no cambiaron de lado y los que
sí: mezclar los dos grupos da ~0 aunque ambos sean predecibles (el error de ADR-0031).

HIGIENE. Unidad efectiva = la ley (ADR-0032): IC por bootstrap de Poisson sobre
EXPEDIENTES (se recalcula rho, el lado y la correlación en cada réplica), además del
bootstrap por legislador; se reporta el más ancho. Y el chequeo que destapó la "firma
temática": confiabilidad split-half dentro de la era partiendo por acta, por
expediente y por sesión.

CERO API. NO TOCA EL MOTOR: sólo lee.

    python evaluacion/baseline/src/record_por_origen.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("record_por_origen")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
from definiciones import GOBIERNOS, era_de  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))

K_SHRINK = 5.0
UMBRAL_LADO = 0.10
UMBRALES_N = (5, 10, 20)
ORIGENES = ("EJECUTIVO", "OPOSICION")
ERAS = [g[0] for g in GOBIERNOS]
RECAMBIOS = [(ERAS[i], ERAS[i + 1], GOBIERNOS[i + 1][1]) for i in range(len(ERAS) - 1)]
PID_PICHETTO = "leg:5daaefa4774c"
N_BOOT = 400
SEED = 7

ORIGEN_POR_ACTA = "variables/proyecto/data/origen_por_acta.parquet"
ENLACE_TODAS = "datos/expedientes/data/clean/acta_expediente_todas.parquet"


# ───────────────────────────── objetos (testeados) ─────────────────────────────

def encoger(af, n, prior, k: float = K_SHRINK):
    return (np.asarray(af, float) + k * np.asarray(prior, float)) / (np.asarray(n, float) + k)


def rho_encogido(af_e, n_e, af_o, n_o, r_general, k: float = K_SHRINK):
    """rho = r_EJEC - r_OPOS, cada uno encogido hacia el récord general del propio
    legislador. Sin votos de un origen, ese lado queda en el general: rho -> 0."""
    return encoger(af_e, n_e, r_general, k) - encoger(af_o, n_o, r_general, k)


def signo_lado(lado, umbral: float = UMBRAL_LADO):
    """+1 del lado del Ejecutivo, -1 enfrente, 0 ambiguo (|lado| < umbral) o sin dato."""
    lado = np.asarray(lado, float)
    s = np.sign(lado)
    s[np.isnan(lado) | (np.abs(lado) < umbral)] = 0
    return s.astype(int)


def rho_heredado(rho_antes, lado_antes, lado_ahora):
    """El rho de la era anterior, relabelado al lado de hoy: si el legislador cambió de
    lado se invierte, si no se conserva. Sin lado conocido en alguna de las dos eras no
    se hereda nada (0), y quien llama tiene que avisar cuántos cayeron ahí."""
    sa, sb = np.asarray(lado_antes), np.asarray(lado_ahora)
    factor = np.where((sa == 0) | (sb == 0), 0, sa * sb)
    return np.asarray(rho_antes, float) * factor


# ───────────────────────────── carga ─────────────────────────────

def cargar() -> pd.DataFrame:
    from bloque import cargar as cargar_bloque

    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(np.int8)
    inicio_a_era = {g[1]: g[0] for g in GOBIERNOS}
    mapa = {f: inicio_a_era[era_de(f)] for f in pd.unique(v["fecha"])}
    v["era"] = v["fecha"].map(mapa)

    opa = pd.read_parquet(REPO / ORIGEN_POR_ACTA)[["acta_id", "origen", "proyecto_id", "expediente"]]
    ae = pd.read_parquet(REPO / ENLACE_TODAS)[["acta_id", "proyecto_id"]].rename(
        columns={"proyecto_id": "pid_enlace"}).drop_duplicates("acta_id")
    v = v.merge(opa.drop_duplicates("acta_id"), on="acta_id", how="left").merge(
        ae, on="acta_id", how="left")
    v["origen"] = v["origen"].fillna("DESCONOCIDO")
    clu = v["proyecto_id"].fillna(v["pid_enlace"]).fillna(v["expediente"])
    sin = clu.isna()
    v["cluster"] = clu.where(~sin, "acta:" + v["acta_id"].astype(str))
    v["sesion"] = v["camara"].astype(str) + ":" + v["fecha"].dt.strftime("%Y-%m-%d")
    v["legislador_id"] = v["legislador_id"].astype(str)
    v["bloque_linaje"] = v["bloque_linaje"].astype(str)
    return v.drop(columns=["proyecto_id", "pid_enlace", "expediente"])


def perfil_era(v: pd.DataFrame) -> pd.DataFrame:
    """Por (legislador, era): récord general, linaje y cámara modales."""
    g = v.groupby(["legislador_id", "era"])
    base = g["af"].agg(n_all="size", af_all="sum")
    base["r_all"] = base["af_all"] / base["n_all"]
    lin = (v.groupby(["legislador_id", "era", "bloque_linaje"]).size()
           .reset_index(name="k").sort_values("k").drop_duplicates(["legislador_id", "era"], keep="last")
           .set_index(["legislador_id", "era"])["bloque_linaje"])
    cam = (v.groupby(["legislador_id", "era", "camara"]).size()
           .reset_index(name="k").sort_values("k").drop_duplicates(["legislador_id", "era"], keep="last")
           .set_index(["legislador_id", "era"])["camara"])
    return base.join(lin.rename("linaje")).join(cam.rename("camara_modal"))


# ───────────────────────────── FASE 0 ─────────────────────────────

def fase0(v: pd.DataFrame, pe: pd.DataFrame) -> dict:
    actas = v.drop_duplicates("acta_id")[["acta_id", "era", "camara", "origen", "cluster"]]
    cobertura = {}
    for (era, cam), g in actas.groupby(["era", "camara"]):
        vc = g["origen"].value_counts()
        cobertura[f"{era}|{cam}"] = {
            "actas": int(len(g)),
            **{o: int(vc.get(o, 0)) for o in ["EJECUTIVO", "OPOSICION", "OFICIALISMO", "ALIADOS", "DESCONOCIDO"]},
            "frac_ejec_u_opos": round(float(g["origen"].isin(ORIGENES).mean()), 4),
        }
    eo = actas[actas["origen"].isin(ORIGENES)]
    clusters = {era: {"actas_EO": int(len(g)), "expedientes_EO": int(g["cluster"].nunique()),
                      "actas_por_expediente": round(len(g) / max(g["cluster"].nunique(), 1), 2)}
                for era, g in eo.groupby("era")}

    cnt = (v[v["origen"].isin(ORIGENES)].groupby(["legislador_id", "era", "origen"]).size()
           .unstack("origen", fill_value=0))
    celdas = {}
    for ea, eb, fecha in RECAMBIOS:
        a = cnt.xs(ea, level="era") if ea in cnt.index.get_level_values("era") else cnt.iloc[:0]
        b = cnt.xs(eb, level="era") if eb in cnt.index.get_level_values("era") else cnt.iloc[:0]
        j = a.join(b, how="inner", lsuffix="_a", rsuffix="_b")
        act_a = set(pe.xs(ea, level="era").index)
        act_b = set(pe.xs(eb, level="era").index)
        cont = act_a & act_b
        fila = {"activos_antes": len(act_a), "activos_despues": len(act_b), "continuadores": len(cont)}
        for u in UMBRALES_N:
            fila[f"n>={u}"] = {
                "EJEC_ambos_lados": int(((j["EJECUTIVO_a"] >= u) & (j["EJECUTIVO_b"] >= u)).sum()),
                "OPOS_ambos_lados": int(((j["OPOSICION_a"] >= u) & (j["OPOSICION_b"] >= u)).sum()),
                "UNIVERSO_las_dos_a_ambos_lados": int(((j[["EJECUTIVO_a", "OPOSICION_a", "EJECUTIVO_b",
                                                          "OPOSICION_b"]] >= u).all(axis=1)).sum()),
            }
        # composición (n>=5): sesgo de supervivencia
        univ = j[(j[["EJECUTIVO_a", "OPOSICION_a", "EJECUTIVO_b", "OPOSICION_b"]] >= 5).all(axis=1)].index
        pa = pe.xs(ea, level="era")
        fila["composicion_linaje_universo_n5"] = pa.reindex(univ)["linaje"].value_counts().to_dict()
        fila["composicion_linaje_activos_antes"] = pa["linaje"].value_counts().head(8).to_dict()
        fila["r_all_medio"] = {"universo_n5": round(float(pa.reindex(univ)["r_all"].mean()), 4)
                               if len(univ) else None,
                               "activos_antes": round(float(pa["r_all"].mean()), 4)}
        fila["camara_universo_n5"] = pa.reindex(univ)["camara_modal"].value_counts().to_dict()
        celdas[fecha] = fila
    return {"cobertura_origen_por_era_camara": cobertura, "expedientes_por_era": clusters,
            "celdas_por_recambio": celdas}


# ───────────────────────────── FASE 1 ─────────────────────────────

class Panel:
    """Conteos (legislador, era, origen, cluster) de actas EJEC/OPOS, para poder
    recomputar todo con pesos por expediente (bootstrap de Poisson) sin volver a
    tocar los 950k votos."""

    def __init__(self, v: pd.DataFrame, pe: pd.DataFrame):
        eo = v[v["origen"].isin(ORIGENES)]
        agg = eo.groupby(["legislador_id", "era", "origen", "cluster"], observed=True)["af"].agg(
            n="size", af="sum").reset_index()
        self.agg = agg
        self.clusters, self.cod_cluster = np.unique(agg["cluster"].to_numpy(), return_inverse=True)
        le = agg["legislador_id"] + "|" + agg["era"]
        self.le_keys, self.cod_le = np.unique(le.to_numpy(), return_inverse=True)
        self.es_ejec = (agg["origen"] == "EJECUTIVO").to_numpy()
        self.n = agg["n"].to_numpy(float)
        self.af = agg["af"].to_numpy(float)
        idx = pd.MultiIndex.from_tuples([tuple(k.split("|", 1)) for k in self.le_keys],
                                        names=["legislador_id", "era"])
        info = pe.reindex(idx)
        self.leg = idx.get_level_values(0).to_numpy()
        self.era = idx.get_level_values(1).to_numpy()
        self.r_all = info["r_all"].to_numpy(float)
        self.linaje = info["linaje"].to_numpy()
        self.camara = info["camara_modal"].to_numpy()

    def tabla(self, w_cluster: np.ndarray | None = None, criterio_lado: str = "centrado") -> pd.DataFrame:
        """`criterio_lado`: 'centrado' = tasa afirmativa del linaje en actas EJECUTIVO
        menos la de TODA la cámara en la era; 'psi' = la misma tasa menos 1/2, tal cual
        `estimar_psi_arrastre.py`. El 'psi' agregado a una era marca como ambiguos al
        radicalismo bajo Kirchner (-0,04) y a LLA bajo Fernández (+0,03): los proyectos
        del Ejecutivo que llegan al recinto son mayormente de consenso y la oposición
        también los acompaña más de la mitad de las veces."""
        w = np.ones(len(self.clusters)) if w_cluster is None else w_cluster
        wr = w[self.cod_cluster]
        m = len(self.le_keys)
        nE = np.bincount(self.cod_le, weights=self.n * wr * self.es_ejec, minlength=m)
        aE = np.bincount(self.cod_le, weights=self.af * wr * self.es_ejec, minlength=m)
        nO = np.bincount(self.cod_le, weights=self.n * wr * ~self.es_ejec, minlength=m)
        aO = np.bincount(self.cod_le, weights=self.af * wr * ~self.es_ejec, minlength=m)
        t = pd.DataFrame({"legislador_id": self.leg, "era": self.era, "linaje": self.linaje,
                          "camara": self.camara, "r_all": self.r_all,
                          "nE": nE, "aE": aE, "nO": nO, "aO": aO})
        t["rho"] = rho_encogido(aE, nE, aO, nO, self.r_all)
        # lado y rho del linaje POR CÁMARA: juntar las dos cámaras le daba a los
        # senadores peronistas dialoguistas de 2015-19 el lado de los diputados K
        # (residuo del Senado entre eras: -0,85, imposible).
        claves = ["era", "camara", "linaje"]
        gl = t.groupby(claves)[["aE", "nE", "aO", "nO"]].sum()
        tasa_e = gl["aE"] / gl["nE"].replace(0, np.nan)
        gc = t.groupby(["era", "camara"])[["aE", "nE"]].sum()
        tasa_cam = (gc["aE"] / gc["nE"].replace(0, np.nan)).reindex(
            gl.index.droplevel("linaje")).to_numpy()
        if criterio_lado == "centrado":
            gl["lado"] = tasa_e - tasa_cam
        elif criterio_lado == "psi":
            gl["lado"] = tasa_e - 0.5
        else:
            raise ValueError(f"criterio_lado invalido: {criterio_lado!r}")
        gl["rho_lin"] = tasa_e - (gl["aO"] / gl["nO"].replace(0, np.nan))
        t = t.join(gl[["lado", "rho_lin"]], on=claves)
        t["s"] = signo_lado(t["lado"].to_numpy())
        t["resid"] = t["rho"] - t["rho_lin"].fillna(0)
        return t


def _corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def pares(t: pd.DataFrame, ea: str, eb: str) -> pd.DataFrame:
    a = t[t["era"] == ea].set_index("legislador_id")
    b = t[t["era"] == eb].set_index("legislador_id")
    return a.join(b, how="inner", lsuffix="_a", rsuffix="_b")


def _grupo(p: pd.DataFrame) -> pd.Series:
    amb = (p["s_a"] == 0) | (p["s_b"] == 0)
    return pd.Series(np.where(amb, "ambiguo", np.where(p["s_a"] == p["s_b"], "mismo_lado", "cambio_lado")),
                     index=p.index)


def metricas_pares(p: pd.DataFrame, u: int) -> dict:
    """Todas las cantidades de la tabla de cierre, para UN conjunto de pares."""
    m = (p[["nE_a", "nO_a", "nE_b", "nO_b"]] >= u).all(axis=1)
    p = p[m]
    g = _grupo(p)
    out = {"n": int(len(p))}
    for nombre, sub in [("mismo_lado", p[g == "mismo_lado"]), ("cambio_lado", p[g == "cambio_lado"]),
                        ("ambiguo", p[g == "ambiguo"]), ("crudo_todos", p)]:
        her = rho_heredado(sub["rho_a"], sub["s_a"], sub["s_b"])
        out[nombre] = {
            "n": int(len(sub)),
            "r_rho": _corr(sub["rho_a"], sub["rho_b"]),
            # ¿se invierte predeciblemente? el rho heredado (relabelado) contra el de después
            "r_rho_heredado": _corr(her, sub["rho_b"]) if nombre != "crudo_todos" else np.nan,
            "acuerdo_signo_crudo": float((np.sign(sub["rho_a"]) == np.sign(sub["rho_b"])).mean())
            if len(sub) else np.nan,
            # lo que el bloque NO explica: rho menos el rho del linaje en la era
            "r_resid_crudo": _corr(sub["resid_a"], sub["resid_b"]),
            "r_resid_relabelado": _corr(sub["resid_a"] * sub["s_a"], sub["resid_b"] * sub["s_b"])
            if nombre in ("mismo_lado", "cambio_lado") else np.nan,
        }
    her_all = rho_heredado(p["rho_a"], p["s_a"], p["s_b"])
    ok = (p["s_a"] != 0) & (p["s_b"] != 0)
    out["relabelado_todos_no_ambiguos"] = {"n": int(ok.sum()),
                                           "r_rho_heredado": _corr(her_all[ok], p.loc[ok, "rho_b"])}
    return out


def medir(t: pd.DataFrame) -> dict:
    res = {}
    todos = []
    for ea, eb, fecha in RECAMBIOS:
        p = pares(t, ea, eb)
        p["recambio"] = fecha
        todos.append(p)
    pooled = pd.concat(todos)
    for u in UMBRALES_N:
        res[f"pooled|n>={u}"] = metricas_pares(pooled, u)
        for p in todos:
            res[f"{p['recambio'].iloc[0]}|n>={u}"] = metricas_pares(p, u)
    # cortes con n>=5
    for cam in ["diputados", "senado"]:
        res[f"camara={cam}|pooled|n>=5"] = metricas_pares(
            pooled[(pooled["camara_a"] == cam) & (pooled["camara_b"] == cam)], 5)
    res["cambio_camara|pooled|n>=5"] = metricas_pares(pooled[pooled["camara_a"] != pooled["camara_b"]], 5)
    for nombre, mask in [("mismo_linaje", pooled["linaje_a"] == pooled["linaje_b"]),
                         ("cambio_linaje", pooled["linaje_a"] != pooled["linaje_b"])]:
        res[f"{nombre}|pooled|n>=5"] = metricas_pares(pooled[mask], 5)
    sin_bolsa = (pooled["linaje_a"] != "OTRO / PROVINCIAL") & (pooled["linaje_b"] != "OTRO / PROVINCIAL")
    res["sin_OTRO_PROVINCIAL|pooled|n>=5"] = metricas_pares(pooled[sin_bolsa], 5)
    return res


def _aplanar(d: dict, pref: str = "") -> dict:
    out = {}
    for k, val in d.items():
        kk = f"{pref}.{k}" if pref else k
        if isinstance(val, dict):
            out.update(_aplanar(val, kk))
        else:
            out[kk] = val
    return out


def _desaplanar(flat: dict) -> dict:
    out: dict = {}
    for k, val in flat.items():
        partes = k.split(".")
        cur = out
        for p_ in partes[:-1]:
            cur = cur.setdefault(p_, {})
        cur[partes[-1]] = val
    return out


def bootstrap(panel: Panel, punto: dict, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """IC 95% de cada correlación con DOS bootstraps: Poisson por EXPEDIENTE (recalcula
    rho, lado y pares) y por LEGISLADOR (re-muestrea los pares). Se reporta el ancho de
    cada uno y el IC que se usa es el más ancho."""
    rng = np.random.default_rng(seed)
    flat_p = {k: v for k, v in _aplanar(punto).items() if k.split(".")[-1].startswith("r_")}
    reps_exp = {k: [] for k in flat_p}
    for b in range(n_boot):
        w = rng.poisson(1.0, len(panel.clusters)).astype(float)
        fb = _aplanar(medir(panel.tabla(w)))
        for k in flat_p:
            reps_exp[k].append(fb.get(k, np.nan))
        if (b + 1) % 50 == 0:
            logger.info("  bootstrap expediente %d/%d", b + 1, n_boot)
    t0 = panel.tabla()
    ps = []
    for ea, eb, fecha in RECAMBIOS:
        p = pares(t0, ea, eb)
        p["recambio"] = fecha
        ps.append(p)
    base_pares = ps
    reps_leg = {k: [] for k in flat_p}
    for b in range(n_boot):
        rs = [p.iloc[rng.integers(0, len(p), len(p))] for p in base_pares]
        fb = _aplanar(_medir_desde_pares(rs))
        for k in flat_p:
            reps_leg[k].append(fb.get(k, np.nan))
    ic = {}
    for k, val in flat_p.items():
        e = np.array(reps_exp[k], float)
        lg = np.array(reps_leg[k], float)
        e, lg = e[~np.isnan(e)], lg[~np.isnan(lg)]
        ie = [float(np.percentile(e, 2.5)), float(np.percentile(e, 97.5))] if len(e) > 20 else [np.nan, np.nan]
        il = [float(np.percentile(lg, 2.5)), float(np.percentile(lg, 97.5))] if len(lg) > 20 else [np.nan, np.nan]
        ancho_e, ancho_l = ie[1] - ie[0], il[1] - il[0]
        usar = ie if (np.nan_to_num(ancho_e) >= np.nan_to_num(ancho_l)) else il
        ic[k] = {"r": val, "ic95": usar, "ic_expediente": ie, "ic_legislador": il,
                 "razon_anchos_exp_sobre_leg": (ancho_e / ancho_l) if ancho_l else np.nan}
    return ic


def _medir_desde_pares(ps: list[pd.DataFrame]) -> dict:
    """`medir` pero partiendo de pares ya armados (para el bootstrap por legislador)."""
    res = {}
    pooled = pd.concat(ps)
    for u in UMBRALES_N:
        res[f"pooled|n>={u}"] = metricas_pares(pooled, u)
        for p in ps:
            res[f"{p['recambio'].iloc[0]}|n>={u}"] = metricas_pares(p, u)
    for cam in ["diputados", "senado"]:
        res[f"camara={cam}|pooled|n>=5"] = metricas_pares(
            pooled[(pooled["camara_a"] == cam) & (pooled["camara_b"] == cam)], 5)
    res["cambio_camara|pooled|n>=5"] = metricas_pares(pooled[pooled["camara_a"] != pooled["camara_b"]], 5)
    for nombre, mask in [("mismo_linaje", pooled["linaje_a"] == pooled["linaje_b"]),
                         ("cambio_linaje", pooled["linaje_a"] != pooled["linaje_b"])]:
        res[f"{nombre}|pooled|n>=5"] = metricas_pares(pooled[mask], 5)
    sin_bolsa = (pooled["linaje_a"] != "OTRO / PROVINCIAL") & (pooled["linaje_b"] != "OTRO / PROVINCIAL")
    res["sin_OTRO_PROVINCIAL|pooled|n>=5"] = metricas_pares(pooled[sin_bolsa], 5)
    return res


def split_half(v: pd.DataFrame, pe: pd.DataFrame, reps: int = 20, seed: int = SEED) -> dict:
    """Confiabilidad de rho DENTRO de la era, partiendo las actas al azar por ACTA, por
    EXPEDIENTE entero y por SESIÓN, y cronológicamente. Si por acta da alto y por
    expediente cae, lo que se ve es agrupamiento por ley (ADR-0032)."""
    rng = np.random.default_rng(seed)
    eo = v[v["origen"].isin(ORIGENES)]
    out = {}
    for era, g in eo.groupby("era"):
        r_all = pe.xs(era, level="era")["r_all"]
        fila = {}
        for unidad in ["acta_id", "cluster", "sesion", "cronologica"]:
            rs, rs_res = [], []
            for _ in range(reps if unidad != "cronologica" else 1):
                if unidad == "cronologica":
                    med = g["fecha"].median()
                    mitad = (g["fecha"] > med).to_numpy()
                else:
                    uu = g[unidad].unique()
                    asign = dict(zip(uu, rng.random(len(uu)) < 0.5))
                    mitad = g[unidad].map(asign).to_numpy()
                ts = []
                for h in (False, True):
                    s = g[mitad == h]
                    c = s.groupby(["legislador_id", "origen"])["af"].agg(["size", "sum"]).unstack(
                        "origen", fill_value=0)
                    c.columns = [f"{a}_{b}" for a, b in c.columns]
                    for col in ["size_EJECUTIVO", "size_OPOSICION", "sum_EJECUTIVO", "sum_OPOSICION"]:
                        if col not in c:
                            c[col] = 0
                    ra = r_all.reindex(c.index).to_numpy(float)
                    c["rho"] = rho_encogido(c["sum_EJECUTIVO"], c["size_EJECUTIVO"],
                                            c["sum_OPOSICION"], c["size_OPOSICION"], ra)
                    ts.append(c)
                j = ts[0].join(ts[1], how="inner", lsuffix="_1", rsuffix="_2")
                ok = (j[["size_EJECUTIVO_1", "size_OPOSICION_1", "size_EJECUTIVO_2",
                         "size_OPOSICION_2"]] >= 5).all(axis=1)
                rs.append(_corr(j.loc[ok, "rho_1"], j.loc[ok, "rho_2"]))
                # residual contra el linaje: le saco la media del linaje en cada mitad
                lin = pe.xs(era, level="era")["linaje"].reindex(j.index)
                res1 = j["rho_1"] - j["rho_1"].groupby(lin).transform("mean")
                res2 = j["rho_2"] - j["rho_2"].groupby(lin).transform("mean")
                rs_res.append(_corr(res1[ok], res2[ok]))
            fila[unidad] = {"r_rho": round(float(np.nanmean(rs)), 4),
                            "r_resid_intra_linaje": round(float(np.nanmean(rs_res)), 4),
                            "n_legisladores": int(ok.sum())}
        out[era] = fila
    return out


def pichetto(t: pd.DataFrame) -> list[dict]:
    s = t[t["legislador_id"] == PID_PICHETTO]
    cols = ["era", "linaje", "camara", "nE", "nO", "rho", "lado", "s", "rho_lin", "resid"]
    return [{k: (round(float(r[k]), 4) if isinstance(r[k], (float, np.floating)) else
                 (int(r[k]) if isinstance(r[k], (np.integer,)) else r[k])) for k in cols}
            for _, r in s[cols].iterrows()]


def _limpiar(o):
    if isinstance(o, dict):
        return {str(k): _limpiar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpiar(x) for x in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    return o


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--salida", default=str(REPO / "evaluacion/baseline/outputs/record_por_origen_fase0_1_2026-09-27.json"))
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")

    v = cargar()
    logger.info("%d votos AF/NE; eras %s", len(v), v["era"].value_counts().to_dict())
    pe = perfil_era(v)
    rep = {"k_shrink": K_SHRINK, "umbral_lado": UMBRAL_LADO, "recambios": RECAMBIOS}
    rep["FASE0"] = fase0(v, pe)
    logger.info("FASE 0 lista")

    panel = Panel(v, pe)
    t = panel.tabla()
    punto = medir(t)
    rep["FASE1_punto"] = punto
    t_psi = panel.tabla(criterio_lado="psi")
    rep["FASE1_punto_criterio_psi_sensibilidad"] = medir(t_psi)
    rep["lado_por_linaje_era"] = (
        t.assign(lado_psi=t_psi["lado"]).groupby(["era", "camara", "linaje"])
        .agg(lado=("lado", "first"), lado_psi=("lado_psi", "first"), rho_lin=("rho_lin", "first"),
             n_leg=("rho", "size")).reset_index().to_dict("records"))
    grupos = []
    for ea, eb, fecha in RECAMBIOS:
        p = pares(t, ea, eb)
        m = (p[["nE_a", "nO_a", "nE_b", "nO_b"]] >= 5).all(axis=1)
        grupos.append({"recambio": fecha, **_grupo(p[m]).value_counts().to_dict()})
    rep["reparto_grupos_n5"] = grupos
    rep["caso_pichetto"] = pichetto(t)
    logger.info("split-half...")
    rep["split_half_intra_era"] = split_half(v, pe)
    logger.info("bootstrap (%d reps x 2)...", args.n_boot)
    rep["FASE1_ic"] = bootstrap(panel, punto, n_boot=args.n_boot)

    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_limpiar(rep), ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("-> %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
