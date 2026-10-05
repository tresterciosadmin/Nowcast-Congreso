# -*- coding: utf-8 -*-
"""D2 de la auditoría 2026-09: piso 0,02, ε₀ y τ (capa 2), walk-forward contra V0 (el motor después del lote de D1).

    python evaluacion/baseline/src/medir_d2_capa2.py                  # el veredicto, desde los JSON de git
    python evaluacion/baseline/src/medir_d2_capa2.py --curvas         # curvas de ε₀ y momentos por acta (PC, el detalle)
    python evaluacion/baseline/src/medir_d2_capa2.py --brazos grilla  # los brazos del piso (PC, ≈ 3 min cada uno)
    python evaluacion/baseline/src/medir_d2_capa2.py --seleccion      # la selección anual (sólo entrenamiento) y el borde
    python evaluacion/baseline/src/medir_d2_capa2.py --brazos wf      # los brazos WF de ε₀, τ y el mecanismo, y el clip
    python evaluacion/baseline/src/medir_d2_capa2.py --controles      # controles de los brazos y de la selección (PC)
    python evaluacion/baseline/src/medir_d2_capa2.py --panel          # el panel primario, SIN leer `y`
    python evaluacion/baseline/src/medir_d2_capa2.py --medir          # Δ, Holm y veredicto (PC)

LA REGLA es el pre-registro de D2 y el protocolo de la fase D (`ESTADO-EJECUCION.md`); este archivo la ejecuta y no la
cambia. Cinco contrastes primarios (Holm, m = 5) en la capa 2 (P(aprobación) y banda del recuento, en mayoría simple):
  piso      WF contra V0 (0,02)            Brier de P(aprobación)
  epsilon0  WF contra V0 (0,035)           Brier de P(aprobación)
  tau       WF contra V0 (1,19)            error de cobertura |c − 0,90| (pp)
  mec_i     mecanismo WF contra el clip    Brier de P(aprobación)
  mec_i2    mecanismo WF contra el clip    error de cobertura
Para cada año Y de test (Diputados 2006–2026, Senado 2007–2026) el valor se elige o estima con las actas de fecha
< 1-ene-Y, sin las de las leyes con actas de test en Y; un valor por año para las dos cámaras; empate < 1e-12 relativo →
V0 (si V0 no está entre los empatados, el más bajo). El piso se elige por la suma de Brier de P(aprobación) en las actas
SIMPLE con resultado; ε₀ por la log-loss de los votos del censo (todas las actas: la población del estimador de V0); τ con
`tau_mediana` sin ε₀ (la variante que produjo 1,19) sobre las actas de ≥ 20 votos de todos los tipos.

UN SOLO CAMINO DE CÁLCULO. En la PC se arman dos tablas por acta que viajan por git: las CURVAS (5.862 actas del censo:
n, A, Σp, Σp², la suma de log-loss de sus votos en cada ε₀ de 0 a 0,50 cada 0,005, y el desvío mínimo de sus P_i) y la
TABLA de la capa 2 (5.858 actas de ≥ 20 votos: tipo, resultado, recuento, y la P y la banda de cada brazo). Selección,
compuesto, IC, p, Holm y veredicto salen de esas dos tablas; el test del CI los recalcula sin el detalle.

LOS BRAZOS los simula `calibracion_declarada.py --simular` con argumentos (columna, ε₀, τ, piso; un valor o uno por año),
semilla 0 en todos (números aleatorios comunes). Sus JSON por acta van a `Archivos_Borrar/d2/brazos/` (se regeneran en
minutos; su sha256 queda en la procedencia). V0 es el JSON versionado `calibracion_actas_2026-10-03.json`. Nada pisa
números versionados: destino que existe → salida 3 salvo `--reemplazar`, y sólo sobre archivos de este comando.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
import censo_estadisticos as ce  # noqa: E402
import calibracion_declarada as CD  # noqa: E402
from estimar_epsilon_tau import estimar_tau_actas  # noqa: E402
from medir_d1_parametros_pi import boot, holm  # noqa: E402  (el bootstrap y Holm de D1: una sola copia)

GENERADOR = "evaluacion/baseline/src/medir_d2_capa2.py"
OUT = REPO / "evaluacion" / "baseline" / "outputs"
V0_TAG = "2026-10-03"
DETALLE_V0 = OUT / f"censo_detalle_{V0_TAG}.parquet"            # ignorado por git; no se borra
ACTAS_V0 = OUT / f"calibracion_actas_{V0_TAG}.json"              # V0 de D2 (versionado)
ACTAS_ORIG = OUT / "calibracion_actas_2026-09-28.json"           # V0 original (continuidad)
BRAZOS_DIR = REPO / "Archivos_Borrar" / "d2" / "brazos"
SALIDA_CURVAS = OUT / "d2_curvas.json"
SALIDA_SELECCION = OUT / "d2_seleccion.json"
SALIDA_CONTROLES = OUT / "d2_controles.json"
SALIDA_PANEL = OUT / "d2_panel_primario.json"
SALIDA = OUT / "d2_capa2.json"
COL = CD.COL
OOS = {"diputados": "2006-01-01", "senado": "2007-01-01"}
ERA_VIGENTE = "2023-12-10"
DESDE_2010 = "2010-01-01"
ERAS = pd.to_datetime(["1990-01-01", "2011-12-10", "2015-12-10", "2019-12-10", "2023-12-10", "2030-01-01"])
ERA_LAB = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]
N_BOOT, SEMILLA, ALFA, M_HOLM = 2000, 7, 0.05, 5
MARGEN = {"brier": 1.0, "cobertura": 1.0}                       # ±1% relativo · ±1 pp
DECLARADA = 0.90
EMPATE = 1e-12
CLIP_P = CD.CLIP                                                 # P recortada a [1e-4, 1 − 1e-4], como C2
CLIP_LL = 1e-9                                                   # el de `estimar_epsilon_tau._logloss`
ANIOS_BRAZO = range(1990, 2031)                                  # el `{año: valor}` de un brazo cubre todos los años
FORMATO = 1

V0 = {"piso": 0.02, "epsilon0": 0.035, "tau": 1.19}
GRILLA_PISO = [0.0, 0.01, 0.02, 0.04]
EXT_PISO = 0.08                                                  # arriba; abajo (0) no hay extensión
GRILLA_EPS = [round(x, 3) for x in np.arange(0.0, 0.5001, 0.005)]  # 0–0,50: la base es 0–0,30, la extensión hasta 0,50
EPS_BASE_MAX, EPS_EXT_MAX = 0.30, 0.50
CONTRASTES = {   # nombre: (pérdida, brazo alternativo, brazo base, tipo de término)
    "piso":     ("brier", "piso_wf", "v0", "hiper"),
    "epsilon0": ("brier", "eps_wf", "v0", "coef_ii"),
    "tau":      ("cobertura", "tau_wf", "v0", "coef_ii"),
    "mec_i":    ("brier", "mec_wf", "clip", "mec_i"),
    "mec_i2":   ("cobertura", "mec_wf", "clip", "mec_i"),
}


def etiqueta(v: float) -> str:
    return f"{v:g}"


# ══════════════════════════════════════════════════════════════════ E/S
def proteger(destino: Path, reemplazar: bool) -> None:
    if destino.exists() and not reemplazar:
        raise FileExistsError(f"{destino} ya existe: no se pisa (pasar --reemplazar si es de este comando)")
    if destino.exists() and destino.suffix == ".json":
        try:
            propio = json.loads(destino.read_text(encoding="utf-8")).get("generador") in (GENERADOR, CD.GENERADOR)
        except (OSError, ValueError, AttributeError):
            propio = False
        if not propio:
            raise FileExistsError(f"{destino} existe y no es de este comando: no se pisa")


def escribir_json(obj: dict, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes((json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))


def leer_json(ruta: Path) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def es_oos(camara, fecha) -> np.ndarray:
    camara, fecha = np.asarray(camara).astype(str), pd.to_datetime(pd.Series(fecha)).to_numpy()
    lim = np.array([np.datetime64(OOS.get(c, "2100-01-01")) for c in camara])
    return fecha >= lim


def _anio(fecha) -> np.ndarray:
    return pd.to_datetime(pd.Series(fecha)).dt.year.to_numpy()


# ══════════════════════════════════════════════════════════════════ las curvas (PC) — lo único que sale del voto a voto
def curvas_desde_detalle(d: pd.DataFrame) -> pd.DataFrame:
    """Por acta del censo: fecha, cámara, ley, n, A, Σp, Σp², desvío mínimo de sus P_i y la suma de log-loss en cada ε₀."""
    d = d.reset_index(drop=True)
    cod, actas = pd.factorize(d["acta_id"].astype(str), sort=False)
    k = len(actas)
    p, y = d[COL].to_numpy(float), d["y"].to_numpy(float)
    meta = d.groupby(cod, sort=True).agg(fecha=("fecha", "first"), camara=("camara", "first"), ley=("ley", "first"))
    t = pd.DataFrame({"acta_id": actas.astype(str)})
    t["fecha"] = pd.to_datetime(meta["fecha"].to_numpy()).strftime("%Y-%m-%d")
    t["camara"] = meta["camara"].astype(str).to_numpy()
    ley = meta["ley"].to_numpy()
    t["ley"] = [x if isinstance(x, str) and x else "acta:" + a for x, a in zip(ley, t["acta_id"])]
    t["n"] = np.bincount(cod, minlength=k).astype(int)
    t["A"] = np.bincount(cod, y, k)
    t["sp"] = np.bincount(cod, p, k)
    t["sp2"] = np.bincount(cod, p * p, k)
    dmin = np.full(k, np.inf)
    np.minimum.at(dmin, cod, np.minimum(p, 1 - p))
    t["dmin"] = dmin
    ll = {}
    for e in GRILLA_EPS:
        q = np.clip(e + (1 - 2 * e) * p, CLIP_LL, 1 - CLIP_LL)
        ll[f"ll::{etiqueta(e)}"] = np.bincount(cod, -(y * np.log(q) + (1 - y) * np.log(1 - q)), k)
    return pd.concat([t, pd.DataFrame(ll)], axis=1)


def redondear_curvas(t: pd.DataFrame) -> pd.DataFrame:
    """Lo que viaja por git (y de lo que se calcula todo, también en la PC): sumas a 1e-6, Σp y Σp² a 1e-9."""
    t = t.copy()
    for c in t.columns:
        if c.startswith("ll::"):
            t[c] = t[c].round(6)
    for c in ("A", "sp", "sp2", "dmin"):
        t[c] = t[c].round(9 if c != "A" else 0)
    return t


def correr_curvas(reemplazar: bool) -> int:
    proteger(SALIDA_CURVAS, reemplazar)
    t0 = time.time()
    d = pd.read_parquet(DETALLE_V0, columns=["acta_id", "fecha", "camara", "ley", "y", COL])
    t = redondear_curvas(curvas_desde_detalle(d))
    escribir_json({"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
                   "detalle": DETALLE_V0.name, "detalle_sha256_16": ce._sha16(DETALLE_V0), "columna_p": COL,
                   "grilla_eps": GRILLA_EPS, "tabla": tabla_a_json(t)}, SALIDA_CURVAS)
    print(f"curvas: {len(t)} actas, {int(t['n'].sum())} votos ({time.time() - t0:.0f} s) -> {SALIDA_CURVAS}")
    return 0


def tabla_a_json(t: pd.DataFrame) -> dict:
    cols = {}
    for c in t.columns:
        x = t[c]
        if x.dtype.kind == "f":
            cols[c] = [None if not np.isfinite(v) else float(v) for v in x]
        elif x.dtype.kind in "iub":
            cols[c] = [int(v) for v in x]
        else:
            cols[c] = [None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v) for v in x]
    return cols


def tabla_de_json(cols: dict) -> pd.DataFrame:
    t = pd.DataFrame(cols)
    if "oos" in t:   # viaja como 0/1: como máscara tiene que ser booleana (un 0/1 entero indexa por posición)
        t["oos"] = t["oos"].astype(bool)
    return t


def cargar_curvas(ruta: Path = SALIDA_CURVAS) -> pd.DataFrame:
    return tabla_de_json(leer_json(ruta)["tabla"])


# ══════════════════════════════════════════════════════════════════ la selección anual (sólo entrenamiento)
def anios_de_test(fecha, camara) -> list[int]:
    return sorted(set(_anio(fecha)[es_oos(camara, fecha)].tolist()))


def leyes_de_test(curvas: pd.DataFrame) -> dict[int, set]:
    """Las leyes con actas de test en Y: las de TODAS las actas OOS del censo de ese año (un superconjunto de las que la
    capa 2 evalúa), para respetar «otra ley» también al elegir."""
    oos, anio, ley = es_oos(curvas["camara"], curvas["fecha"]), _anio(curvas["fecha"]), curvas["ley"].to_numpy()
    return {Y: set(ley[oos & (anio == Y)]) for Y in anios_de_test(curvas["fecha"], curvas["camara"])}


def entrenamiento(fecha, ley, Y: int, test_leyes: set) -> np.ndarray:
    f = pd.to_datetime(pd.Series(fecha)).to_numpy()
    return (f < np.datetime64(f"{Y}-01-01")) & ~np.isin(np.asarray(ley), list(test_leyes))


def elegir(valores: list, perdidas: np.ndarray, v0: float):
    """El de menor pérdida; empate < 1e-12 relativo con V0 → V0; si V0 no está entre los empatados, el más bajo."""
    s = np.asarray(perdidas, float)
    best = s.min()
    if v0 in valores and s[valores.index(v0)] - best <= EMPATE * max(abs(best), 1e-300):
        return v0
    return valores[int(np.argmin(s))]


def elegir_eps(curvas: pd.DataFrame, mask: np.ndarray, tope: float) -> float:
    vals = [e for e in GRILLA_EPS if e <= tope + 1e-12]
    s = np.array([curvas.loc[mask, f"ll::{etiqueta(e)}"].sum() for e in vals])
    return elegir(vals, s, V0["epsilon0"])


def tau_de(curvas: pd.DataFrame, mask: np.ndarray, eps0: float = 0.0):
    """`tau_mediana` (variante sin ε₀ si eps0 = 0) sobre las actas de `mask`; None si el estimador no ajusta."""
    a = curvas.loc[mask, ["acta_id", "n", "A", "sp", "sp2"]]
    r = estimar_tau_actas(a, eps0)
    return None if "error" in r else float(r["tau_mediana"])


def elegir_piso(tabla: pd.DataFrame, mask: np.ndarray, valores: list) -> float:
    s = np.array([tabla.loc[mask, f"e::piso={etiqueta(v)}"].sum() for v in valores])
    return elegir(valores, s, V0["piso"])


def seleccion(curvas: pd.DataFrame, tabla_piso: pd.DataFrame | None, piso_valores: list, eps_tope: float,
              solo: list | None = None) -> dict:
    """La selección anual de los tres parámetros (y la trayectoria descriptiva de τ con ε₀_Y). `tabla_piso`: por acta
    SIMPLE con resultado, la suma de Brier de P(aprobación) de cada piso (`e::piso=v`)."""
    lt = leyes_de_test(curvas)
    out = {"anios": {}, "apagados": {"epsilon0": [], "tau": [], "piso": []}}
    for Y, tl in lt.items():
        if solo is not None and Y not in solo:
            continue
        r = {}
        m = entrenamiento(curvas["fecha"], curvas["ley"], Y, tl)
        if m.sum() < 20:
            r["epsilon0"], r["tau"], r["tau_con_eps"] = 0.0, 0.0, None
            out["apagados"]["epsilon0"].append(Y)
            out["apagados"]["tau"].append(Y)
        else:
            r["epsilon0"] = elegir_eps(curvas, m, eps_tope)
            t = tau_de(curvas, m, 0.0)
            if t is None:
                out["apagados"]["tau"].append(Y)
            r["tau"] = 0.0 if t is None else t
            r["tau_con_eps"] = tau_de(curvas, m, r["epsilon0"])
        if tabla_piso is not None:
            mp = entrenamiento(tabla_piso["fecha"], tabla_piso["ley"], Y, tl)
            if mp.sum() < 20:
                r["piso"] = None
                out["apagados"]["piso"].append(Y)
            else:
                r["piso"] = elegir_piso(tabla_piso, mp, piso_valores)
        out["anios"][int(Y)] = r
    todo = np.ones(len(curvas), bool)
    out["final"] = {"epsilon0": elegir_eps(curvas, todo, eps_tope), "tau": tau_de(curvas, todo, 0.0)}
    if tabla_piso is not None:
        out["final"]["piso"] = elegir_piso(tabla_piso, np.ones(len(tabla_piso), bool), piso_valores)
    return out


# ══════════════════════════════════════════════════════════════════ los brazos (PC)
def ruta_brazo(nombre: str) -> Path:
    return BRAZOS_DIR / f"d2_{nombre.replace('=', '-')}.json"


def por_anio(valores: dict, v0: float) -> dict:
    """El `{año: valor}` de un brazo WF: el valor elegido para cada año de test; V0 en los años que sólo entrenan (esas
    actas no se evalúan)."""
    return {str(a): float(valores.get(a, v0)) for a in ANIOS_BRAZO}


def argumentos_brazo(nombre: str, sel: dict | None) -> list[str]:
    if nombre.startswith("piso="):
        return ["--piso", nombre.split("=")[1], "--partes", "p"]
    if nombre == "clip":
        return ["--epsilon0", "0", "--tau", "0", "--partes", "p,banda"]
    anios = {int(a): r for a, r in sel["anios"].items()}
    eps = json.dumps(por_anio({a: r["epsilon0"] for a, r in anios.items()}, V0["epsilon0"]))
    tau = json.dumps(por_anio({a: r["tau"] for a, r in anios.items()}, V0["tau"]))
    if nombre == "eps_wf":
        return ["--epsilon0", eps, "--partes", "p,banda"]
    if nombre == "tau_wf":
        return ["--tau", tau, "--partes", "p,banda"]
    if nombre == "mec_wf":
        return ["--epsilon0", eps, "--tau", tau, "--partes", "p,banda"]
    raise ValueError(nombre)


def correr_brazos(nombres: list[str], procesos: int, reemplazar: bool) -> int:
    sel = leer_json(SALIDA_SELECCION) if any(not n.startswith("piso=") and n != "clip" for n in nombres) else None
    pend = []
    for n in nombres:
        r = ruta_brazo(n)
        if r.exists() and not reemplazar:
            print(f"{n}: ya está ({r.name})", flush=True)
            continue
        pend.append(n)
    BRAZOS_DIR.mkdir(parents=True, exist_ok=True)
    corriendo, fallos = [], []
    env = dict(os.environ, PYTHONUTF8="1")
    while pend or corriendo:
        while pend and len(corriendo) < procesos:
            n = pend.pop(0)
            cmd = [sys.executable, str(REPO / CD.GENERADOR), "--simular", "--actas", str(ruta_brazo(n))]
            cmd += (["--reemplazar"] if ruta_brazo(n).exists() else []) + argumentos_brazo(n, sel)
            log = open(BRAZOS_DIR / f"d2_{n.replace('=', '-')}.log", "w", encoding="utf-8")
            corriendo.append((n, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(REPO)), log))
            print(f"{n}: lanzado", flush=True)
        time.sleep(2)
        for item in list(corriendo):
            n, pr, log = item
            if pr.poll() is not None:
                log.close()
                corriendo.remove(item)
                print(f"{n}: código {pr.returncode}", flush=True)
                if pr.returncode != 0:
                    fallos.append(n)
    return 1 if fallos else 0


def brazos_grilla(piso_valores: list) -> list[str]:
    return [f"piso={etiqueta(v)}" for v in piso_valores if v != V0["piso"]]


# ══════════════════════════════════════════════════════════════════ la tabla de la capa 2
def _actas(ruta: Path) -> pd.DataFrame:
    return CD.cargar_actas(ruta)[1]


def _dentro(a: pd.DataFrame) -> np.ndarray:
    lo, hi, af = (a[c].to_numpy(float) for c in ("b_lo", "b_hi", "af"))
    out = np.where(np.isnan(lo), np.nan, ((lo <= af) & (af <= hi)).astype(float))
    return out


def tabla_capa2(brazos: list[str], con_y: bool) -> pd.DataFrame:
    """Por acta de ≥ 20 votos (el orden de V0): la P y la banda (b_lo, b_hi) de cada brazo, y —con `con_y`— el resultado,
    el recuento y el «dentro de la banda». Los brazos tienen que traer las mismas actas que V0 en el mismo orden."""
    v0 = _actas(ACTAS_V0)
    t = v0[["acta_id", "camara", "ley", "fecha", "tipo", "n"]].copy()
    if con_y:
        t["af"] = v0["af"].to_numpy(float)
        t["y"] = v0["y"].to_numpy(float)
    fuentes = {"v0": v0} | {b: _actas(ruta_brazo(b)) for b in brazos}
    for b, a in fuentes.items():
        if len(a) != len(v0) or not (a["acta_id"].to_numpy() == v0["acta_id"].to_numpy()).all():
            raise RuntimeError(f"el brazo {b} no trae las mismas actas que V0 en el mismo orden")
        t[f"p::{b}"] = a["p"].to_numpy(float)
        t[f"lo::{b}"] = a["b_lo"].to_numpy(float)
        t[f"hi::{b}"] = a["b_hi"].to_numpy(float)
        if con_y:
            t[f"in::{b}"] = _dentro(a.assign(af=v0["af"]))
    t["oos"] = es_oos(t["camara"], t["fecha"])
    return t


def con_e_piso(t: pd.DataFrame, piso_valores: list) -> pd.DataFrame:
    """Las columnas `e::piso=v` (Brier de P recortada) que usa la selección del piso, en las actas SIMPLE con resultado."""
    s = t[(t["tipo"] == "SIMPLE") & t["y"].notna()].copy()
    for v in piso_valores:
        b = "v0" if v == V0["piso"] else f"piso={etiqueta(v)}"
        s[f"e::piso={etiqueta(v)}"] = (np.clip(s[f"p::{b}"].to_numpy(float), CLIP_P, 1 - CLIP_P) - s["y"]) ** 2
    return s


# ══════════════════════════════════════════════════════════════════ selección y borde (PC o CI)
def piso_valores_presentes() -> list:
    return sorted(set(GRILLA_PISO) | ({EXT_PISO} if ruta_brazo(f"piso={etiqueta(EXT_PISO)}").exists() else set()))


def correr_seleccion(reemplazar: bool) -> int:
    proteger(SALIDA_SELECCION, reemplazar)
    curvas = cargar_curvas()
    valores = piso_valores_presentes()
    t = tabla_capa2(brazos_grilla(valores), con_y=True)
    tp = con_e_piso(t, valores)
    sel = seleccion(curvas, tp, valores, EPS_BASE_MAX)
    borde = {"epsilon0_toca_030": any(r["epsilon0"] >= EPS_BASE_MAX - 1e-12 for r in sel["anios"].values()),
             "piso_toca_004": any(r["piso"] == 0.04 for r in sel["anios"].values()),
             "piso_toca_0_no_extensible": any(r["piso"] == 0.0 for r in sel["anios"].values()),
             "epsilon0_toca_0_no_extensible": any(r["epsilon0"] == 0.0 for r in sel["anios"].values())}
    if borde["epsilon0_toca_030"]:
        sel = seleccion(curvas, tp, valores, EPS_EXT_MAX)
        borde["epsilon0_extendido_a"] = EPS_EXT_MAX
        borde["epsilon0_vuelve_a_tocar"] = any(r["epsilon0"] >= EPS_EXT_MAX - 1e-12 for r in sel["anios"].values())
    if borde["piso_toca_004"] and EXT_PISO not in valores:
        print(f"el piso toca el borde 0,04: falta el brazo piso={etiqueta(EXT_PISO)} (correr --brazos piso={etiqueta(EXT_PISO)} "
              "y repetir --seleccion)", file=sys.stderr)
        return 4
    if EXT_PISO in valores:
        borde["piso_extendido_a"] = EXT_PISO
        borde["piso_vuelve_a_tocar"] = any(r["piso"] == EXT_PISO for r in sel["anios"].values())
    sel["borde"] = borde
    sel["piso_valores"] = valores
    sel["eps_tope"] = EPS_EXT_MAX if borde.get("epsilon0_extendido_a") else EPS_BASE_MAX
    escribir_json({"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(), **sel},
                  SALIDA_SELECCION)
    for Y, r in sel["anios"].items():
        print(f"  {Y}: piso {r['piso']}  ε₀ {r['epsilon0']}  τ {r['tau']}  (τ con ε₀_Y {r['tau_con_eps']})")
    print("final:", sel["final"], "borde:", borde)
    return 0


# ══════════════════════════════════════════════════════════════════ el panel primario (sin `y`)
def compuesto_piso(t: pd.DataFrame, sel: dict) -> pd.Series:
    """La P del compuesto WF del piso: en cada acta OOS, la del brazo del piso elegido para su año."""
    anio = _anio(t["fecha"])
    p = t["p::v0"].copy()
    for Y, r in sel["anios"].items():
        if r.get("piso") is None:
            continue
        b = "v0" if r["piso"] == V0["piso"] else f"piso={etiqueta(r['piso'])}"
        m = t["oos"].to_numpy(bool) & (anio == int(Y))
        p[m] = t.loc[m, f"p::{b}"]
    return p


def poblaciones(t: pd.DataFrame) -> dict:
    simple = (t["tipo"] == "SIMPLE").to_numpy(bool) & t["oos"].to_numpy(bool)
    out = {"cobertura": simple}
    if "y" in t:
        out["brier"] = simple & t["y"].notna().to_numpy()
    else:   # el panel se fija sin leer `y`: el resultado oficial existe o no (no su valor)
        res = _actas(ACTAS_V0)["y"].notna().to_numpy()
        out["brier"] = simple & res
    return out


def _distinto(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return ~((a == b) | (np.isnan(a) & np.isnan(b)))


def panel_de(t: pd.DataFrame, sel: dict) -> dict:
    """Por contraste: en qué actas de su población OOS la alternativa (o, para el piso, alguna de la grilla final) da
    distinto que la base. No usa `y`."""
    pob = poblaciones(t)
    banda = lambda b: (t[f"lo::{b}"].to_numpy(float), t[f"hi::{b}"].to_numpy(float))  # noqa: E731
    out = {}
    for c, (perd, alt, base, _) in CONTRASTES.items():
        if c == "piso":
            dif = np.zeros(len(t), bool)
            for v in sel["piso_valores"]:
                if v != V0["piso"]:
                    dif |= _distinto(t[f"p::piso={etiqueta(v)}"].to_numpy(float), t["p::v0"].to_numpy(float))
        elif perd == "brier":
            dif = _distinto(t[f"p::{alt}"].to_numpy(float), t[f"p::{base}"].to_numpy(float))
        else:
            (la, ha), (lb, hb) = banda(alt), banda(base)
            dif = _distinto(la, lb) | _distinto(ha, hb)
        out[c] = dif & pob[perd]
    return out


def resumen_panel(t: pd.DataFrame, m: np.ndarray) -> dict:
    f = pd.to_datetime(t["fecha"]).to_numpy()
    return {"actas": int(m.sum()), "leyes": int(t.loc[m, "ley"].nunique()),
            "diputados": int((m & (t["camara"] == "diputados").to_numpy()).sum()),
            "senado": int((m & (t["camara"] == "senado").to_numpy()).sum()),
            "era_vigente": int((m & (f >= np.datetime64(ERA_VIGENTE))).sum())}


def brazos_wf() -> list[str]:
    return ["eps_wf", "tau_wf", "mec_wf", "clip"]


def correr_panel(reemplazar: bool) -> int:
    proteger(SALIDA_PANEL, reemplazar)
    sel = leer_json(SALIDA_SELECCION)
    t = tabla_capa2(brazos_grilla(sel["piso_valores"]) + brazos_wf(), con_y=False)
    pan = panel_de(t, sel)
    pob = poblaciones(t)
    out = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(), "lee_y": False,
           "poblaciones_oos": {k: resumen_panel(t, v) for k, v in pob.items()},
           "panel_primario": {c: resumen_panel(t, m) for c, m in pan.items()},
           "actas_del_panel": {c: t.loc[m, "acta_id"].astype(str).tolist() for c, m in pan.items()}}
    escribir_json(out, SALIDA_PANEL)
    for c, r in out["panel_primario"].items():
        print(f"  {c:<9} {r}")
    return 0


# ══════════════════════════════════════════════════════════════════ los contrastes (desde la tabla: PC o CI)
def boot_cobertura(n: np.ndarray, d1: np.ndarray, d0: np.ndarray, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """Δ = |c1 − 0,90| − |c0 − 0,90| en pp, con las DOS coberturas recalculadas en cada réplica (bootstrap de Poisson sobre
    grupos); IC 95% y p con la fórmula del protocolo."""
    k = len(n)
    W = np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        N = W @ n
        dd = 100 * (np.abs((W @ d1) / N - DECLARADA) - np.abs((W @ d0) / N - DECLARADA))
    dd = dd[np.isfinite(dd)]
    p = min(1.0, 2 * min(1 + (dd <= 0).sum(), 1 + (dd >= 0).sum()) / (1 + n_boot))
    c1, c0 = d1.sum() / n.sum(), d0.sum() / n.sum()
    return {"delta": round(float(100 * (abs(c1 - DECLARADA) - abs(c0 - DECLARADA))), 4),
            "cobertura_alt_%": round(100 * float(c1), 3), "cobertura_base_%": round(100 * float(c0), 3),
            "ic95": [round(float(np.percentile(dd, 2.5)), 4), round(float(np.percentile(dd, 97.5)), 4)],
            "p": float(p), "se": round(float(dd.std(ddof=1)), 4), "grupos": int(k)}


def boot_brier(d: np.ndarray, b0: np.ndarray) -> dict:
    r = boot(d, b0)
    return {"delta": r["dBrier_rel_%"], "ic95": r["ic95"], "p": r["p"], "se": r["se_%"], "grupos": r["grupos"]}


def contraste(t: pd.DataFrame, perdida: str, p1: np.ndarray | None, p0: np.ndarray | None,
              in1: np.ndarray | None, in0: np.ndarray | None, mask: np.ndarray) -> dict:
    """Un contraste sobre las actas de `mask`, con IC por ley y por mes. Brier: Δ relativo (%) de P recortada; cobertura:
    Δ del error en pp."""
    if not mask.any():
        return {"actas": 0}
    out = {"actas": int(mask.sum()), "leyes": int(t.loc[mask, "ley"].nunique())}
    for nom, grupo in (("por_ley", t["ley"].astype(str)), ("por_mes", t["fecha"].astype(str).str[:7])):
        g = grupo.to_numpy()[mask]
        if perdida == "brier":
            y = t["y"].to_numpy(float)[mask]
            e1 = (np.clip(p1[mask], CLIP_P, 1 - CLIP_P) - y) ** 2
            e0 = (np.clip(p0[mask], CLIP_P, 1 - CLIP_P) - y) ** 2
            s = pd.DataFrame({"g": g, "d": e1 - e0, "b0": e0}).groupby("g", sort=True).sum()
            out[nom] = boot_brier(s["d"].to_numpy(), s["b0"].to_numpy())
        else:
            s = pd.DataFrame({"g": g, "n": 1.0, "d1": in1[mask], "d0": in0[mask]}).groupby("g", sort=True).sum()
            out[nom] = boot_cobertura(s["n"].to_numpy(), s["d1"].to_numpy(), s["d0"].to_numpy())
    out["p_estrella"] = max(out["por_ley"]["p"], out["por_mes"]["p"])
    out["mde"] = round(2.8 * max(out["por_ley"]["se"], out["por_mes"]["se"]), 4)
    return out


def serie(t: pd.DataFrame, brazo: str, sel: dict) -> tuple[np.ndarray, np.ndarray | None]:
    """(P, dentro) de un brazo; `piso_wf` es el compuesto de los brazos del piso."""
    if brazo == "piso_wf":
        return compuesto_piso(t, sel).to_numpy(float), None
    return t[f"p::{brazo}"].to_numpy(float), (t[f"in::{brazo}"].to_numpy(float) if f"in::{brazo}" in t else None)


def medir_contraste(t: pd.DataFrame, c: str, sel: dict, panel: np.ndarray) -> dict:
    perd, alt, base, tipo = CONTRASTES[c]
    p1, in1 = serie(t, alt, sel)
    p0, in0 = serie(t, base, sel)
    f = pd.to_datetime(t["fecha"]).to_numpy()
    pob = poblaciones(t)[perd]
    r = {"contraste": c, "perdida": perd, "alternativa": alt, "base": base, "tipo": tipo,
         "identico_en_el_panel": bool(not panel.any()), "primario": contraste(t, perd, p1, p0, in1, in0, panel)}
    if c == "piso":
        r["trayectoria"] = {str(Y): v["piso"] for Y, v in sel["anios"].items()}
        r["valor_wf_final"], r["v0"] = sel["final"]["piso"], V0["piso"]
    elif c in ("epsilon0", "tau"):
        r["trayectoria"] = {str(Y): v[c] for Y, v in sel["anios"].items()}
        r["valor_wf_final"], r["v0"] = sel["final"][c], V0[c]
    r["subgrupos"] = {"era_vigente": contraste(t, perd, p1, p0, in1, in0, panel & (f >= np.datetime64(ERA_VIGENTE)))}
    for cam in ("diputados", "senado"):
        r["subgrupos"][cam] = contraste(t, perd, p1, p0, in1, in0, panel & (t["camara"] == cam).to_numpy())
    r["descriptivo"] = {"poblacion_oos": contraste(t, perd, p1, p0, in1, in0, pob),
                        "desde_2010": contraste(t, perd, p1, p0, in1, in0, panel & (f >= np.datetime64(DESDE_2010)))}
    era = pd.cut(pd.to_datetime(t["fecha"]), ERAS, labels=ERA_LAB).astype(str).to_numpy()
    for e in ERA_LAB:
        r["descriptivo"][f"era={e}"] = contraste(t, perd, p1, p0, in1, in0, panel & (era == e))
    if "p::orig" in t:   # contra V0 original (el censo del 28-09), sobre la intersección: mide el offset, no el parámetro
        po, ino = t["p::orig"].to_numpy(float), (t["in::orig"].to_numpy(float) if "in::orig" in t else None)
        inter = panel & ~np.isnan(po if perd == "brier" else ino)
        r["descriptivo"]["contra_v0_original"] = contraste(t, perd, p1, po, in1, ino, inter)
    return r


def accion_cambia(tipo: str, lado: str, r: dict) -> bool:
    """¿La acción que implica esta dirección es un cambio del motor? (el veto E sólo se evalúa entonces)."""
    if tipo == "mec_i":
        return lado == "malo"                      # B → apagar la bandera; A → sigue prendido (no cambia)
    return lado == "bueno" and r.get("valor_wf_final") != r.get("v0")   # A → recalibrar (si el final no es V0)


def arbol(r: dict, rechaza: bool) -> dict:
    """El árbol del punto 6 del protocolo (sin F: es de la capa 1) para un contraste."""
    pr, tipo = r["primario"], r["tipo"]
    if r["identico_en_el_panel"] or not pr.get("actas"):
        return {"salida": "Z"}
    il, im = pr["por_ley"]["ic95"], pr["por_mes"]["ic95"]
    mg = MARGEN[r["perdida"]]
    if all(-mg <= x <= mg for x in il + im):
        return {"salida": "C"}
    d = pr["por_ley"]["delta"]
    bueno, malo = il[1] < 0 and im[1] < 0, il[0] > 0 and im[0] > 0
    if rechaza and (bueno or (malo and d > 0)):
        lado = "bueno" if bueno else "malo"
        if accion_cambia(tipo, lado, r):
            # daña: el subgrupo empeora con la acción, con IC por ley que excluye 0 (recalibrar: Δ > 0; apagar: Δ < 0,
            # porque el mecanismo es mejor ahí)
            danio = [k for k, s in r["subgrupos"].items() if s.get("actas") and
                     (s["por_ley"]["ic95"][0] > 0 if lado == "bueno" else s["por_ley"]["ic95"][1] < 0)]
            if danio:
                return {"salida": "E", "danio_en": danio}
        return {"salida": "A" if lado == "bueno" else "B"}
    return {"salida": "D"}


def salida_mecanismo(s1: str, s2: str) -> str:
    """Fijado en el pre-registro (3.8): la salida del mecanismo a partir de sus dos contrastes."""
    s = {s1, s2}
    if "E" in s or s == {"A", "B"}:
        return "E"
    if "A" in s:
        return "A"
    if "B" in s:
        return "B"
    if s == {"C"}:
        return "C"
    if s == {"Z"}:
        return "Z"
    return "D"


def veredicto(res: dict) -> dict:
    ps = {c: (1.0 if r["identico_en_el_panel"] or not r["primario"].get("actas") else r["primario"]["p_estrella"])
          for c, r in res.items()}
    rech = holm(ps, ALFA, M_HOLM)
    por = {c: {"p_estrella_holm": ps[c], "holm_rechaza": rech[c], **arbol(r, rech[c])} for c, r in res.items()}
    mec = salida_mecanismo(por["mec_i"]["salida"], por["mec_i2"]["salida"])
    acc = {}
    if mec == "E":
        acc = {k: "no se aplica: el mecanismo terminó en E; todo va a Franco" for k in ("piso", "epsilon0", "tau", "mecanismo")}
    else:
        acc["mecanismo"] = {"A": "sigue prendido", "B": "apagar la bandera INCERTIDUMBRE_LEGISLADOR",
                            "C": "conservar V0; se le presenta a Franco que es equivalente a apagado",
                            "D": "conservar V0: no se distingue de apagado", "Z": "sin cambio"}[mec]
        for k in ("epsilon0", "tau"):
            s = por[k]["salida"]
            if mec == "A" and s == "A" and res[k].get("valor_wf_final") != V0[k]:
                acc[k] = f"recalibrar a {res[k]['valor_wf_final']}"
            elif s == "E":
                acc[k] = "no se cambia; va a Franco"
            else:
                acc[k] = "conservar V0"
        s = por["piso"]["salida"]
        acc["piso"] = ({"A": f"recalibrar a {res['piso'].get('valor_wf_final')}" if res["piso"].get("valor_wf_final") != V0["piso"]
                        else "conservar (el WF final es V0; el óptimo cambió en el tiempo)",
                        "E": "no se cambia; va a Franco"}.get(s, "conservar V0"))
    cambian = [k for k in ("piso", "epsilon0", "tau") if isinstance(acc.get(k), str) and acc[k].startswith("recalibrar")]
    return {"por_contraste": por, "m_holm": M_HOLM, "mecanismo": mec, "acciones": acc,
            "confirmacion_conjunta_necesaria": len(cambian) > 1, "cambian": cambian}


def medir_desde_tablas(t: pd.DataFrame, sel: dict, panel_ids: dict) -> dict:
    ids = t["acta_id"].astype(str).to_numpy()
    res = {c: medir_contraste(t, c, sel, np.isin(ids, panel_ids[c])) for c in CONTRASTES}
    return {"resultados": res, "veredicto": veredicto(res)}


def auc_de(t: pd.DataFrame, brazo: str, sel: dict) -> dict:
    p, _ = serie(t, brazo, sel)
    out = {}
    pob = poblaciones(t)["brier"]
    for cam in ("diputados", "senado"):
        m = pob & (t["camara"] == cam).to_numpy()
        out[cam] = round(CD.auc(p[m], t["y"].to_numpy(float)[m]), 4)
    return out


def capa1_eps(sel: dict) -> dict:
    """Informativo (no decide): Brier y log-loss de los VOTOS OOS con ε₀_Y contra 0,035, con IC por ley. PC (el detalle)."""
    d = pd.read_parquet(DETALLE_V0, columns=["acta_id", "fecha", "camara", "ley", "y", COL])
    oos = es_oos(d["camara"], d["fecha"])
    d = d[oos].reset_index(drop=True)
    anio = _anio(d["fecha"])
    e = np.array([sel["anios"][str(a)]["epsilon0"] if str(a) in sel["anios"] else V0["epsilon0"] for a in anio])
    p, y = d[COL].to_numpy(float), d["y"].to_numpy(float)
    out = {}
    for nom, f in (("brier", lambda q: (q - y) ** 2),
                   ("logloss", lambda q: -(y * np.log(np.clip(q, CLIP_LL, 1 - CLIP_LL))
                                           + (1 - y) * np.log(np.clip(1 - q, CLIP_LL, 1 - CLIP_LL))))):
        e1, e0 = f(e + (1 - 2 * e) * p), f(V0["epsilon0"] + (1 - 2 * V0["epsilon0"]) * p)
        ley = d["ley"].astype(str).where(d["ley"].notna(), "acta:" + d["acta_id"].astype(str))
        s = pd.DataFrame({"g": ley, "d": e1 - e0, "b0": e0}).groupby("g", sort=True).sum()
        out[nom] = boot_brier(s["d"].to_numpy(), s["b0"].to_numpy())
    out["votos"] = int(len(d))
    return out


def correr_medir(reemplazar: bool) -> int:
    proteger(SALIDA, reemplazar)
    sel = leer_json(SALIDA_SELECCION)
    panel = leer_json(SALIDA_PANEL)
    brazos = brazos_grilla(sel["piso_valores"]) + brazos_wf()
    t = tabla_capa2(brazos, con_y=True)
    orig = _actas(ACTAS_ORIG).set_index("acta_id")
    t["p::orig"] = t["acta_id"].map(orig["p"]).astype(float)
    o = orig.assign(af=orig["af"].astype(float))
    t["in::orig"] = t["acta_id"].map(pd.Series(_dentro(o.reset_index()), index=o.index)).astype(float)
    t["af_orig"] = t["acta_id"].map(orig["af"]).astype(float)
    t.loc[t["af_orig"] != t["af"], ["p::orig", "in::orig"]] = np.nan    # misma acta con otro recuento: no es comparable
    t = t.drop(columns="af_orig")
    r = medir_desde_tablas(t, sel, panel["actas_del_panel"])
    r["informativo"] = {"auc": {b: auc_de(t, b, sel) for b in ("v0", "piso_wf", "eps_wf", "mec_wf", "clip")},
                        "capa1_epsilon0": capa1_eps(sel),
                        "tau_con_eps_trayectoria": {Y: v["tau_con_eps"] for Y, v in sel["anios"].items()}}
    usados = [DETALLE_V0, ACTAS_V0, ACTAS_ORIG, SALIDA_CURVAS] + [ruta_brazo(b) for b in brazos]
    sucio = subprocess.run(["git", "--no-optional-locks", "status", "--porcelain", "--", "modelo", "variables",
                            "definiciones.py", "rutas.py", "evaluacion/baseline/src"],
                           cwd=str(REPO), capture_output=True, text=True).stdout.splitlines()
    out = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "procedencia": {"head_sha_al_medir": ce._git_head(), "motor_o_runner_sin_commitear": sucio,
                           "insumos_sha256_16": {p.name: ce._sha16(p) for p in usados}},
           "metodo": {"n_boot": N_BOOT, "semilla": SEMILLA, "alfa": ALFA, "m_holm": M_HOLM, "margen": MARGEN,
                      "oos": OOS, "empate_relativo": EMPATE, "clip_p": CLIP_P, "declarada": DECLARADA},
           "seleccion": sel, "panel": {k: v for k, v in panel.items() if k != "actas_del_panel"},
           **r, "tabla": tabla_a_json(t)}
    escribir_json(out, SALIDA)
    for c, v in r["veredicto"]["por_contraste"].items():
        pr = r["resultados"][c]["primario"]
        print(f"  {c:<9} {v['salida']}  Δ {pr.get('por_ley', {}).get('delta')} ley {pr.get('por_ley', {}).get('ic95')} "
              f"mes {pr.get('por_mes', {}).get('ic95')} p* {v['p_estrella_holm']:.4f} Holm {v['holm_rechaza']}")
    print("mecanismo:", r["veredicto"]["mecanismo"], "· acciones:", r["veredicto"]["acciones"])
    return 0


def recalcular_desde_json(ruta: Path = SALIDA, curvas: Path = SALIDA_CURVAS, panel: Path = SALIDA_PANEL) -> dict:
    """Lo que hace el CI: rehace la selección (desde las curvas y la tabla), los contrastes y el veredicto."""
    j = leer_json(ruta)
    t = tabla_de_json(j["tabla"])
    sel_g = j["seleccion"]
    tp = con_e_piso(t, sel_g["piso_valores"])
    sel = seleccion(cargar_curvas(curvas), tp, sel_g["piso_valores"], sel_g["eps_tope"])
    sel = json.loads(json.dumps(sel))              # las claves de año como texto, como en el JSON
    sel["piso_valores"], sel["eps_tope"] = sel_g["piso_valores"], sel_g["eps_tope"]
    ids = leer_json(panel)["actas_del_panel"]      # el panel viaja como lista de actas (fijado sin leer `y`)
    return {"seleccion": sel, **medir_desde_tablas(t, sel, ids), "guardado": j}


# ══════════════════════════════════════════════════════════════════ controles (PC)
def comparar_actas(ref: Path, nuevo: Path, cols: list, mapa: dict | None = None) -> dict:
    a, b = _actas(ref), _actas(nuevo)
    mapa = mapa or {}
    res = {"ref": ref.name, "nuevo": nuevo.name, "n_ref": len(a), "n_nuevo": len(b)}
    m = a.merge(b, on="acta_id", how="outer", suffixes=("_ref", "_nuevo"), indicator=True)
    res["solo_ref"], res["solo_nuevo"] = int((m["_merge"] == "left_only").sum()), int((m["_merge"] == "right_only").sum())
    m = m[m["_merge"] == "both"]
    dif = {}
    for c in cols:
        x, y = m[f"{c}_ref"], m[f"{mapa.get(c, c)}_nuevo"]
        if x.dtype.kind in "fiu" or y.dtype.kind in "fiu":
            xx, yy = pd.to_numeric(x).to_numpy(float), pd.to_numeric(y).to_numpy(float)
            dist = _distinto(xx, yy)
            dif[c] = {"distintos": int(dist.sum()), "max_abs": float(np.nanmax(np.abs(xx - yy))) if dist.any() else 0.0}
        else:
            dif[c] = {"distintos": int((x.astype(str) != y.astype(str)).sum())}
    res["columnas"] = dif
    res["ok"] = res["solo_ref"] == 0 and res["solo_nuevo"] == 0 and all(v["distintos"] == 0 for v in dif.values())
    return res


def invariancia_seleccion(curvas_de, tabla_piso: pd.DataFrame, valores: list, eps_tope: float) -> dict:
    """Corromper `y` en las actas de test del año Y (fecha ≥ 1-ene-Y) y en las de las leyes con actas de test en Y no
    puede cambiar el valor elegido para Y; control positivo: corromperla en el entrenamiento tiene que cambiar algo.
    `curvas_de(mascara_de_actas_a_corromper)` devuelve las curvas recalculadas con `y` → 1 − y en esas actas."""
    base_c = curvas_de(None)
    base = seleccion(base_c, tabla_piso, valores, eps_tope)
    lt = leyes_de_test(base_c)
    fallas, revisados = [], 0
    for Y, tl in lt.items():
        f = pd.to_datetime(base_c["fecha"]).to_numpy()
        m = (f >= np.datetime64(f"{Y}-01-01")) | np.isin(base_c["ley"].to_numpy(), list(tl))
        cc = curvas_de(m)
        fp = pd.to_datetime(tabla_piso["fecha"]).to_numpy()
        mp = (fp >= np.datetime64(f"{Y}-01-01")) | np.isin(tabla_piso["ley"].to_numpy(), list(tl))
        tp = corromper_piso(tabla_piso, mp, valores)
        s = seleccion(cc, tp, valores, eps_tope, solo=[Y])["anios"][Y]
        revisados += 1
        for k in ("epsilon0", "tau", "piso", "tau_con_eps"):
            if s[k] != base["anios"][Y][k]:
                fallas.append({"anio": Y, "parametro": k, "base": base["anios"][Y][k], "corrompido": s[k]})
    # control positivo: y corrompida en TODO lo anterior a 2012 → algún año desde 2012 tiene que cambiar, en cada estimador
    f = pd.to_datetime(base_c["fecha"]).to_numpy()
    cc = curvas_de(f < np.datetime64("2012-01-01"))
    tp = corromper_piso(tabla_piso, pd.to_datetime(tabla_piso["fecha"]).to_numpy() < np.datetime64("2012-01-01"), valores)
    pos = seleccion(cc, tp, valores, eps_tope)
    cambia = {k: [Y for Y in pos["anios"] if Y >= 2012 and pos["anios"][Y][k] != base["anios"][Y][k]]
              for k in ("epsilon0", "tau", "piso")}
    return {"anios_revisados": revisados, "fallas": fallas, "ok": not fallas,
            "control_positivo": {"cambia_en": cambia, "ok": all(bool(v) for v in cambia.values())}}


def corromper_piso(tp: pd.DataFrame, m: np.ndarray, valores: list) -> pd.DataFrame:
    tp = tp.copy()
    tp.loc[m, "y"] = 1 - tp.loc[m, "y"]
    for v in valores:   # el Brier se rehace con la `y` corrompida (la P del brazo no depende de `y`)
        b = "v0" if v == V0["piso"] else f"piso={etiqueta(v)}"
        tp[f"e::piso={etiqueta(v)}"] = (np.clip(tp[f"p::{b}"].to_numpy(float), CLIP_P, 1 - CLIP_P) - tp["y"]) ** 2
    return tp


def correr_controles(reemplazar: bool) -> int:
    proteger(SALIDA_CONTROLES, reemplazar)
    ctl = REPO / "Archivos_Borrar" / "d2"
    sim = {
        "A_defaults_reproducen_el_03_10": comparar_actas(ACTAS_V0, ctl / "ctrl_A_v0_1003.json", CD.COLUMNAS[1:]),
        "B_defaults_reproducen_el_28_09": comparar_actas(ACTAS_ORIG, ctl / "ctrl_B_v0_0928.json", CD.COLUMNAS[1:]),
        "C_v0_explicito_por_anio": comparar_actas(ACTAS_V0, ctl / "ctrl_C_anio.json", CD.COLUMNAS[1:]),
        "D_v0_explicito_escalar": comparar_actas(ACTAS_V0, ctl / "ctrl_D_escalar.json", CD.COLUMNAS[1:]),
        "E_clip_es_p_sin": comparar_actas(ACTAS_V0, ctl / "ctrl_E_clip.json", ["tipo", "y", "p_sin"], {"p_sin": "p"}),
    }
    sel = leer_json(SALIDA_SELECCION)
    valores = sel["piso_valores"]
    curvas = cargar_curvas()
    t = tabla_capa2(brazos_grilla(valores) + brazos_wf(), con_y=True)
    # el piso no puede actuar donde todas las P_i tienen desvío ≥ máx(v; 0,02)
    dmin = t["acta_id"].map(curvas.set_index("acta_id")["dmin"]).to_numpy(float)
    no_actua, anti = {}, {}
    for v in valores:
        if v == V0["piso"]:
            continue
        b = f"piso={etiqueta(v)}"
        m = dmin >= max(v, V0["piso"])
        p1, p0 = t[f"p::{b}"].to_numpy(float), t["p::v0"].to_numpy(float)
        no_actua[b] = {"actas_donde_no_puede_actuar": int(m.sum()), "distintas_ahi": int(_distinto(p1[m], p0[m]).sum())}
        anti[b] = int(_distinto(p1, p0).sum())
    for b in brazos_wf():
        anti[b] = int((_distinto(t[f"p::{b}"].to_numpy(float), t["p::v0"].to_numpy(float))
                       | _distinto(t[f"lo::{b}"].to_numpy(float), t["lo::v0"].to_numpy(float))).sum())
    # la selección desde las curvas reproduce el estimador de V0 con todo el panel (0,035 y 1,1882)
    todo = seleccion(curvas, None, valores, sel["eps_tope"])["final"]
    # invariancia de la selección: las curvas se rehacen desde el detalle con `y` corrompida
    d = pd.read_parquet(DETALLE_V0, columns=["acta_id", "fecha", "camara", "ley", "y", COL])
    aid = d["acta_id"].astype(str).to_numpy()
    orden = curvas["acta_id"].astype(str).to_numpy()

    def curvas_de(mask_actas):
        if mask_actas is None:
            return curvas
        malas = set(orden[mask_actas])
        dd = d.copy()
        m = np.isin(aid, list(malas))
        dd.loc[m, "y"] = 1 - dd.loc[m, "y"]
        return redondear_curvas(curvas_desde_detalle(dd))

    tp = con_e_piso(t, valores)
    inv = invariancia_seleccion(curvas_de, tp, valores, sel["eps_tope"])
    out = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "simulador": sim, "piso_no_actua": no_actua, "anti_vacuidad_actas_distintas_de_v0": anti,
           "estimador_con_todo": {"epsilon0": todo["epsilon0"], "tau_sin_eps": todo["tau"],
                                  "esperado": {"epsilon0": 0.035, "tau_sin_eps": 1.1882}},
           "invariancia_seleccion": inv}
    ok = (all(v["ok"] for v in sim.values()) and all(v["distintas_ahi"] == 0 for v in no_actua.values())
          and all(v > 0 for v in anti.values()) and todo["epsilon0"] == 0.035 and abs(todo["tau"] - 1.1882) < 1e-4
          and inv["ok"] and inv["control_positivo"]["ok"])
    out["todos_ok"] = bool(ok)
    escribir_json(out, SALIDA_CONTROLES)
    print(json.dumps({k: v for k, v in out.items() if k != "simulador"}, ensure_ascii=False)[:3000])
    for k, v in sim.items():
        print(f"  {k}: {'OK' if v['ok'] else 'FALLA'}  {v['columnas']}")
    print("TODOS OK" if ok else "HAY FALLAS")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--curvas", action="store_true")
    ap.add_argument("--brazos", nargs="+", default=None, help="'grilla', 'wf' o nombres (piso=0.08, eps_wf, clip, …)")
    ap.add_argument("--seleccion", action="store_true")
    ap.add_argument("--controles", action="store_true")
    ap.add_argument("--panel", action="store_true")
    ap.add_argument("--medir", action="store_true")
    ap.add_argument("--procesos", type=int, default=3)
    ap.add_argument("--reemplazar", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.curvas:
            return correr_curvas(a.reemplazar)
        if a.brazos:
            nombres = []
            for n in a.brazos:
                nombres += brazos_grilla(GRILLA_PISO) if n == "grilla" else brazos_wf() if n == "wf" else [n]
            return correr_brazos(nombres, a.procesos, a.reemplazar)
        if a.seleccion:
            return correr_seleccion(a.reemplazar)
        if a.controles:
            return correr_controles(a.reemplazar)
        if a.panel:
            return correr_panel(a.reemplazar)
        if a.medir:
            return correr_medir(a.reemplazar)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    r = recalcular_desde_json()
    for c, v in r["veredicto"]["por_contraste"].items():
        print(f"{c:<9} {v['salida']}")
    print("mecanismo:", r["veredicto"]["mecanismo"], r["veredicto"]["acciones"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
