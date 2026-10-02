# -*- coding: utf-8 -*-
"""La calibración de lo que el motor declara, en mayoría simple y por cámara (auditoría 2026-09, ítem C2; pieza 2 del anclaje).

    python evaluacion/baseline/src/calibracion_declarada.py              # → outputs/calibracion_declarada.json (segundos)
    python evaluacion/baseline/src/calibracion_declarada.py --simular    # regenera el JSON por acta con el motor de hoy (PC, ≈ 15 min)

QUÉ DA. (a) P(aprobación) contra el RESULTADO OFICIAL de cada acta de mayoría simple, por cámara y en «ambas»: Brier del
modelo contra el de una CONSTANTE (la tasa base del subconjunto), AUC, Brier recalibrado fuera de muestra (regresión
logística, 5 pliegues por ley), Brier y log-loss sin ε₀+τη, y —lo que faltaba para el objetivo 3 del §9.4— el IC PAREADO
de Δ = Brier(modelo) − Brier(constante) re-muestreando LEYES (la constante es la tasa base de cada réplica); más la
tabla de confiabilidad y las «seguras y equivocadas». (b) La COBERTURA de la banda [p5, p95] del recuento de
afirmativos, declarada al 90%, con IC re-muestreando leyes: en todas las actas (la población del 63,6%) y en mayoría
simple por cámara. Las definiciones son las de `coordinacion/AUDITORIA-2026-09/simple_por_camara.py`,
`contraste_aprobacion.py` y `modelo/ensemble/src/medir_tau_limpio.py` (que no se tocan): la regla es reproducirlos.

DE DÓNDE SALE. Todo se calcula desde un JSON POR ACTA que viaja por git (`outputs/calibracion_actas_2026-09-28.json`:
la P(aprobación) de producción y sin ε₀+τη, el recuento real, el resultado oficial y la banda), así que corre en el CI y
en un clon. Ese JSON lo produce `--simular`: re-corre `ensemble.simular_con_guardas` —con ε₀, τ y `reparto_desvio`
EXPLÍCITOS, no los defaults de esa función— sobre las P_i del censo (`p__estricta__general` del detalle de 37 MB, que no
viaja por git). Antes de simular verifica que `EPSILON0`, `TAU` y `QUORUM_ABSTENCIONES` no estén en el entorno.

NO PISA NADA (como `metrica_de_verdad.py`). Si un destino existe, falla (salida 3) salvo `--reemplazar`; y aun con
`--reemplazar` se niega a escribir sobre un archivo sin la marca `generador` de este comando.

LÍMITES (declarados de antemano): la constante es la tasa base de la MUESTRA (una vara dura: conoce lo que el motor tiene
que adivinar); «disputada» se define con el margen ya votado, así que no es un subconjunto pronosticable; la banda y
P(aprobación) están condicionadas a los presentes (`p_presente = 1`); una semilla y 1.000 simulaciones por acta para la
banda; el AUC no trae IC; el resultado de un acta no es la sanción de una ley. No cambia ningún término del motor ni
implementa el «más de 5 pp = rojo» de la pieza 2 (es del gate, E3).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_estadisticos as ce  # noqa: E402
import metrica_de_verdad as MV  # noqa: E402

GENERADOR = "evaluacion/baseline/src/calibracion_declarada.py"
# El JSON por acta del motor de HOY (auditoría D1.0, censo del 2026-10-02; re-anclado a propósito) y el del
# 28-09 (el de C2: reproduce la tabla del §9.2 y queda en git como continuidad; no se pisa).
ACTAS = Path(ce.ESTADISTICOS).with_name("calibracion_actas_2026-10-02.json")
ACTAS_2026_09_28 = Path(ce.ESTADISTICOS).with_name("calibracion_actas_2026-09-28.json")
SALIDA = Path(ce.ESTADISTICOS).with_name("calibracion_declarada.json")
FORMATO = 1
COL = "p__estricta__general"          # las P_i del motor de hoy en el censo
N_SIMS_P, N_SIMS_BANDA, SEMILLA_SIM = 2000, 1000, 0   # los de contraste_aprobacion.py y medir_tau_limpio.py
MIN_VOTANTES = 20
N_BOOT, SEMILLA = 2000, 7             # el IC de los dos (igual que la métrica de verdad)
SEMILLA_RECAL = 3                     # `default_rng(3)` de simple_por_camara.py
DECLARADA = 0.90
CLIP = 1e-4
COLUMNAS = ["acta_id", "camara", "ley", "fecha", "tipo", "n", "af", "y", "p", "p_sin", "b_lo", "b_hi", "b_medio"]
ENV_PROHIBIDAS = ("EPSILON0", "TAU", "QUORUM_ABSTENCIONES")
CAMBIOS_DE_HOY = "evaluacion/baseline/src/calibracion_declarada.py"
SI, NO = {"afirmativo", "afirmativa"}, {"negativo", "negativa"}


# ──────────────────────────────────────── la simulación (PC) ────────────────────────────────────────

def _resultado_binario(txt):
    t = str(txt).strip().lower()
    return 1 if t in SI else (0 if t in NO else None)


def simular_actas(detalle: Path) -> dict:
    """Re-corre la simulación del motor sobre cada acta de ≥ 20 votos emitidos del censo y devuelve el JSON por acta."""
    sucias = [k for k in ENV_PROHIBIDAS if os.environ.get(k) not in (None, "")]
    if sucias:
        raise RuntimeError(f"variables de entorno que cambian el motor: {sucias}; sacarlas antes de simular")
    for sub in ("modelo/ensemble/src", "modelo/agregador_institucional/src"):
        sys.path.insert(0, str(REPO / sub))
    import agregador as AG  # noqa: E402
    import ensemble as ENS  # noqa: E402
    import nowcast_puertas as NP  # noqa: E402
    from definiciones import normalizar_mayoria_valor  # noqa: E402
    for nm in ("agregador", "ensemble", "nowcast_puertas"):
        logging.getLogger(nm).setLevel(logging.WARNING)

    t0 = time.time()
    d = pd.read_parquet(detalle, columns=["acta_id", "fecha", "camara", "ley", "y", COL])
    d["acta_id"] = d["acta_id"].astype(str)
    ac = pd.read_parquet(REPO / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet",
                         columns=["acta_id", "tipo_mayoria", "resultado"])
    ac["acta_id"] = ac["acta_id"].astype(str)
    ac = ac.drop_duplicates("acta_id").set_index("acta_id")
    par = {"epsilon0": NP.EPSILON0, "tau": NP.TAU, "reparto_desvio": NP.REPARTO_DESVIO,
           "desvio_min_individual": ENS.DESVIO_MIN_INDIVIDUAL, "p_incertidumbre": ENS.P_INCERTIDUMBRE,
           "quorum_cuenta_abstenciones": AG.QUORUM_CUENTA_ABSTENCIONES,
           "n_sims_p_aprobacion": N_SIMS_P, "n_sims_banda": N_SIMS_BANDA, "semilla_simulacion": SEMILLA_SIM,
           "p_presente": 1.0}
    filas = []
    for k, (aid, g) in enumerate(d.groupby("acta_id", sort=False), 1):
        if len(g) < MIN_VOTANTES:
            continue
        cam = str(g["camara"].iloc[0])
        tipo_raw = ac["tipo_mayoria"].get(aid)
        tipo = normalizar_mayoria_valor(tipo_raw) if pd.notna(tipo_raw) else "SIMPLE"
        lin, des = zip(*(NP.a_linea_y_desvio(p) for p in g[COL].to_numpy(float)))
        lin, des, pres = np.array(lin), np.array(des, float), np.ones(len(g))
        kw = dict(seed=SEMILLA_SIM, p_presente=pres, reparto_desvio=NP.REPARTO_DESVIO)
        # la banda, como `medir_tau_limpio.cobertura`: tipo «SIMPLE», 1.000 simulaciones, producción
        b = ENS.simular_con_guardas(lin, des, "SIMPLE", cam, n_sims=N_SIMS_BANDA, epsilon0=NP.EPSILON0, tau=NP.TAU, **kw)
        p = p_sin = None
        if tipo == "SIMPLE":   # P(aprobación), como `contraste_aprobacion.py`: 2.000 simulaciones, tipo real
            p = float(ENS.simular_con_guardas(lin, des, tipo, cam, n_sims=N_SIMS_P, epsilon0=NP.EPSILON0,
                                              tau=NP.TAU, **kw)["p_aprobacion"])
            p_sin = float(ENS.simular_con_guardas(lin, des, tipo, cam, n_sims=N_SIMS_P, epsilon0=0.0,
                                                  tau=0.0, **kw)["p_aprobacion"])
        ley = g["ley"].iloc[0]
        filas.append([aid, cam, ley if isinstance(ley, str) and ley else "acta:" + aid,
                      pd.Timestamp(g["fecha"].iloc[0]).strftime("%Y-%m-%d"), tipo, int(len(g)), int(g["y"].sum()),
                      _resultado_binario(ac["resultado"].get(aid)), p, p_sin,
                      float(b["afirm_p5"]), float(b["afirm_p95"]), float(b["afirm_medio"])])
        if k % 500 == 0:
            print(f"  {k} actas · {(time.time() - t0) / 60:.1f} min", flush=True)
    return {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
            "motor_head_sha": MV.git_head(), "motor_modificado_sin_commitear": MV.motor_modificado(),
            "parametros": par,
            "fuente": {"detalle": detalle.relative_to(REPO).as_posix() if REPO in detalle.resolve().parents
                       else detalle.as_posix(),
                       "detalle_sha256_16": ce._sha16(detalle), "columna_p": COL, "n_actas": len(filas),
                       "poblacion": f"actas de >= {MIN_VOTANTES} votos emitidos del censo, en el orden del detalle"},
            "actas": {"columnas": COLUMNAS, "filas": filas}, "minutos": round((time.time() - t0) / 60, 1)}


def escribir_actas(est: dict, ruta: Path) -> Path:
    """Un renglón por acta (el diff de git sirve y se lee a ojo); LF en todos los sistemas."""
    cab = {k: v for k, v in est.items() if k != "actas"}
    filas = ",\n".join(json.dumps(f, ensure_ascii=False, separators=(",", ":")) for f in est["actas"]["filas"])
    partes = [f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in cab.items()]
    partes.append(f' "actas": {{"columnas": {json.dumps(est["actas"]["columnas"])},\n"filas": [\n{filas}\n]}}')
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(("{\n" + ",\n".join(partes) + "\n}\n").encode("utf-8"))
    return ruta


def cargar_actas(ruta: Path | None = None) -> tuple[dict, pd.DataFrame]:
    ruta = Path(ruta) if ruta else REPO / ACTAS
    if not ruta.is_file():
        raise FileNotFoundError(f"falta {ruta}: se regenera con `calibracion_declarada.py --simular` (PC, ≈ 15 min) "
                                "o con `git checkout`")
    est = json.loads(ruta.read_text(encoding="utf-8"))
    if est.get("formato") != FORMATO:
        raise ValueError(f"formato {est.get('formato')!r} != {FORMATO}")
    return est, pd.DataFrame(est["actas"]["filas"], columns=est["actas"]["columnas"])


# ───────────────────────────────────────────── la métrica ─────────────────────────────────────────────

def auc(p, y):
    p, y = np.asarray(p), np.asarray(y)
    if y.min() == y.max():
        return float("nan")
    o = pd.Series(p).rank().to_numpy()
    n1, n0 = y.sum(), (1 - y).sum()
    return float((o[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _logit(p):
    p = np.clip(p, CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def recalibrar_cv(g: pd.DataFrame, rng, k: int = 5) -> np.ndarray:
    """p' = σ(a + b·logit p), ajustada fuera de muestra (k pliegues por LEY). Consume `rng` como simple_por_camara.py."""
    from scipy.optimize import minimize
    leyes = np.array(g["ley"].unique(), dtype=object)   # array de numpy: da la misma permutación que el ArrowStringArray, sin el aviso de pandas
    rng.shuffle(leyes)
    pliegue = {l: i % k for i, l in enumerate(leyes)}
    f = g["ley"].map(pliegue).to_numpy()
    x, y = _logit(g["p"].to_numpy(float)), g["y"].to_numpy(float)
    out = np.zeros(len(g))
    for j in range(k):
        tr, te = f != j, f == j

        def nll(w):
            z = w[0] + w[1] * x[tr]
            return np.mean(np.log1p(np.exp(-z)) * y[tr] + np.log1p(np.exp(z)) * (1 - y[tr]))

        w = minimize(nll, [0.0, 1.0], method="Nelder-Mead").x
        out[te] = 1 / (1 + np.exp(-(w[0] + w[1] * x[te])))
    return out


def _por_ley(ley, **cols):
    """Códigos de ley (orden de texto, como `ce.sumas_por_ley`) y las sumas por ley de cada columna."""
    _, cod = np.unique(np.asarray(ley).astype(str), return_inverse=True)
    k = int(cod.max()) + 1
    return {n: np.bincount(cod, np.asarray(v, float), k) for n, v in cols.items()} | {
        "n": np.bincount(cod, minlength=k).astype(float)}


def _pesos(k: int, n_boot: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)


def ic_pareado(y, p, ley, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """Δ = Brier(modelo, con P recortada) − Brier(constante), la constante = tasa base del subconjunto RECALCULADA en
    cada réplica; bootstrap de Poisson sobre leyes. Absoluto y relativo a la Brier de la constante."""
    y, p = np.asarray(y, float), np.clip(np.asarray(p, float), CLIP, 1 - CLIP)
    s = _por_ley(ley, y=y, sb=(p - y) ** 2)
    n, sy, sb = s["n"], s["y"], s["sb"]
    b0 = sy.sum() / n.sum()
    bb0 = b0 * (1 - b0)
    delta0 = sb.sum() / n.sum() - bb0
    W = _pesos(len(n), n_boot, seed)
    N, Y, SB = W @ n, W @ sy, W @ sb
    with np.errstate(divide="ignore", invalid="ignore"):
        bb = (Y / N) * (1 - Y / N)
        d, rel = SB / N - bb, (SB / N - bb) / bb
    d, rel = d[np.isfinite(d)], rel[np.isfinite(rel)]
    q = lambda x: [round(float(np.percentile(x, 2.5)), 5), round(float(np.percentile(x, 97.5)), 5)]  # noqa: E731
    return {"delta": round(float(delta0), 5), "ic95_ley": q(d),
            "delta_rel_%": round(100 * float(delta0 / bb0), 2), "ic95_rel_%_ley": [round(100 * v, 2) for v in q(rel)],
            "n_leyes": int(len(n))}


def _disputada(g: pd.DataFrame) -> np.ndarray:
    return (np.minimum(g["af"], g["n"] - g["af"]) / g["n"]).to_numpy() >= 0.10


def _fila(g: pd.DataFrame, rng, n_boot: int, seed: int) -> dict:
    y = g["y"].to_numpy(float)
    pa = g["p"].clip(CLIP, 1 - CLIP).to_numpy(float)
    pb = g["p_sin"].clip(CLIP, 1 - CLIP).to_numpy(float)
    b = y.mean()
    ll = lambda p: -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()  # noqa: E731
    f = {"n": int(len(g)), "tasa_base": round(float(b), 4), "brier_constante": round(float(b * (1 - b)), 4),
         "brier_modelo": round(float(((pa - y) ** 2).mean()), 4), "auc": round(auc(pa, y), 3),
         "brier_recalibrado_cv": (round(float(((recalibrar_cv(g, rng) - y) ** 2).mean()), 4) if rng is not None else None),
         "brier_sin_eps0_tau": round(float(((pb - y) ** 2).mean()), 4),
         "logloss_modelo": round(float(ll(pa)), 4), "logloss_sin_eps0_tau": round(float(ll(pb)), 4),
         "modelo_menos_constante": ic_pareado(y, pa, g["ley"], n_boot, seed)}
    return f


def tabla_simple(a: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """La tabla del §9.2: por cámara (todas / disputadas) y «ambas», en mayoría simple con resultado oficial."""
    s = a[(a["tipo"] == "SIMPLE") & a["y"].notna()]
    rng = np.random.default_rng(SEMILLA_RECAL)    # el orden de consumo importa: Dip-todas, Dip-disp, Sen-todas, Sen-disp
    out: dict = {}
    for cam, g0 in s.groupby("camara"):
        out[cam] = {"todas": _fila(g0, rng, n_boot, seed), "disputadas": _fila(g0[_disputada(g0)], rng, n_boot, seed)}
    out["ambas"] = {"todas": _fila(s, None, n_boot, seed)}
    pa = s["p"].clip(CLIP, 1 - CLIP).to_numpy(float)
    rech = s["y"].to_numpy(float) == 0
    out["rechazadas_en_simple"] = {"n": int(rech.sum()), "p_mediana": round(float(np.median(pa[rech])), 3),
                                   "n_con_p_mayor_0_8": int((pa[rech] > 0.8).sum())}
    return out


def confiabilidad(a: pd.DataFrame) -> dict:
    """Tabla de confiabilidad (6 clases) y «seguras y equivocadas», en mayoría simple por cámara."""
    s = a[(a["tipo"] == "SIMPLE") & a["y"].notna()]
    out = {}
    for cam, g in s.groupby("camara"):
        p, y = g["p"].clip(CLIP, 1 - CLIP).to_numpy(float), g["y"].to_numpy(float)
        cal = []
        for lo, hi in ((0, .05), (.05, .2), (.2, .5), (.5, .8), (.8, .95), (.95, 1.0001)):
            m = (p >= lo) & (p < hi)
            cal.append({"clase": f"[{lo:.2f},{min(hi, 1):.2f})", "n": int(m.sum()),
                        "p_medio": round(float(p[m].mean()), 4) if m.any() else None,
                        "frec_real": round(float(y[m].mean()), 4) if m.any() else None})
        out[cam] = {"clases": cal, "p_mayor_0_95_y_rechazada": int(((p > 0.95) & (y == 0)).sum()),
                    "p_menor_0_05_y_aprobada": int(((p < 0.05) & (y == 1)).sum())}
    return out


def cobertura(g: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """Cobertura de la banda [p5, p95] declarada al 90% (el recuento real, entre los que votaron, cae adentro), con IC
    re-muestreando leyes; ancho mediano y sesgo (real − media simulada) en votos."""
    dentro = ((g["b_lo"] <= g["af"]) & (g["af"] <= g["b_hi"])).to_numpy(float)
    s = _por_ley(g["ley"], dentro=dentro)
    n, dn = s["n"], s["dentro"]
    W = _pesos(len(n), n_boot, seed)
    c = (W @ dn) / (W @ n)
    c0 = dn.sum() / n.sum()
    return {"n_actas": int(len(g)), "cobertura_banda_90": round(float(c0), 4),
            "ic95_ley": [round(float(np.percentile(c, 2.5)), 4), round(float(np.percentile(c, 97.5)), 4)],
            "observada_menos_declarada_pp": round(100 * float(c0 - DECLARADA), 1),
            "ic95_pp": [round(100 * (float(np.percentile(c, q)) - DECLARADA), 1) for q in (2.5, 97.5)],
            "ancho_mediano_votos": round(float(np.median(g["b_hi"] - g["b_lo"])), 1),
            "sesgo_medio_votos": round(float((g["af"] - g["b_medio"]).mean()), 2), "n_leyes": int(len(n))}


def banda(a: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    out = {}
    for nom, pob in (("todas_las_actas", a), ("mayoria_simple", a[a["tipo"] == "SIMPLE"])):
        out[nom] = {"ambas": cobertura(pob, n_boot, seed)}
        for cam, g in pob.groupby("camara"):
            out[nom][cam] = cobertura(g, n_boot, seed)
    return out


def objetivos(tabla: dict, bnd: dict) -> dict:
    """Los objetivos 2 y 3 del §9.4 con la regla fijada en el pre-registro de C2."""
    o3 = {cam: {"delta": tabla[cam]["todas"]["modelo_menos_constante"]["delta"],
                "extremo_superior_ic": tabla[cam]["todas"]["modelo_menos_constante"]["ic95_ley"][1],
                "cumple": bool(tabla[cam]["todas"]["modelo_menos_constante"]["ic95_ley"][1] < 0)}
          for cam in ("diputados", "senado")}
    o3["cumple"] = all(v["cumple"] for v in o3.values() if isinstance(v, dict))
    c = bnd["mayoria_simple"]
    o2 = {cam: {"cobertura": c[cam]["cobertura_banda_90"], "en_85_95": bool(0.85 <= c[cam]["cobertura_banda_90"] <= 0.95)}
          for cam in ("diputados", "senado")}
    o2["en_85_95"] = all(v["en_85_95"] for v in o2.values() if isinstance(v, dict))
    o2["nota"] = "medida con p_presente = 1 (sin asistencia real): aunque cayera en el rango, el objetivo exige asistencia real"
    return {"3_brier_menor_que_la_constante_con_ic_pareado_que_excluya_0": o3, "2_cobertura_85_95_con_asistencia_real": o2}


def medir(a: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    t = tabla_simple(a, n_boot, seed)
    b = banda(a, n_boot, seed)
    return {"tabla_simple": t, "confiabilidad": confiabilidad(a), "banda": b, "objetivos_9_4": objetivos(t, b)}


# ────────────────────────────────────────────────── E/S ──────────────────────────────────────────────────

def proteger(destino: Path, reemplazar: bool) -> None:
    """Antes de calcular nada: un número versionado no se pisa por descuido."""
    if not destino.exists():
        return
    if not reemplazar:
        raise MV.DestinoProtegido(f"{destino} ya existe: no se pisa (pasar --reemplazar si es de este comando)")
    try:
        propio = json.loads(destino.read_text(encoding="utf-8")).get("generador") == GENERADOR
    except (OSError, ValueError, AttributeError):
        propio = False
    if not propio:
        raise MV.DestinoProtegido(f"{destino} existe y no es de este comando (falta su marca `generador`): "
                                  "no se pisa ni con --reemplazar")


def procedencia(est: dict, ruta: Path, argv: list) -> dict:
    try:
        rel = ruta.resolve().relative_to(REPO).as_posix()
    except ValueError:
        rel = ruta.as_posix()
    return {"head_sha_al_correr": MV.git_head(), "motor_modificado_sin_commitear": MV.motor_modificado(),
            "comando": ["calibracion_declarada.py", *argv],
            "actas": {"ruta": rel, "sha256_lf": MV._sha256_lf(ruta), "escrito_el": est.get("generado"),
                      "motor_head_sha_al_simular": est.get("motor_head_sha"), "parametros": est.get("parametros"),
                      "fuente": est.get("fuente")}}


def imprimir(res: dict) -> None:
    t = res["tabla_simple"]
    print("P(aprobación) en mayoría simple contra el resultado oficial · Δ = Brier(modelo) − Brier(constante)")
    for cam in ("diputados", "senado"):
        for sub in ("todas", "disputadas"):
            f = t[cam][sub]
            d = f["modelo_menos_constante"]
            print(f"  {cam:<10}{sub:<11} n {f['n']:>5}  base {f['tasa_base']:.3f}  const {f['brier_constante']:.4f}  "
                  f"modelo {f['brier_modelo']:.4f}  AUC {f['auc']:.3f}  recal {f['brier_recalibrado_cv']:.4f}  "
                  f"Δ {d['delta']:+.4f} {d['ic95_ley']}")
    f = t["ambas"]["todas"]
    print(f"  ambas      todas       n {f['n']:>5}  base {f['tasa_base']:.3f}  const {f['brier_constante']:.4f}  "
          f"modelo {f['brier_modelo']:.4f}  AUC {f['auc']:.3f}  Δ {f['modelo_menos_constante']['delta']:+.4f} "
          f"{f['modelo_menos_constante']['ic95_ley']}")
    print("banda declarada al 90%:")
    for pob, v in res["banda"].items():
        for cam, c in v.items():
            print(f"  {pob:<17}{cam:<10} {c['n_actas']:>5} actas  cobertura {c['cobertura_banda_90']:.4f} {c['ic95_ley']}  "
                  f"({c['observada_menos_declarada_pp']:+.1f} pp)  ancho {c['ancho_mediano_votos']}  sesgo {c['sesgo_medio_votos']:+.2f}")
    print("objetivos del §9.4:", json.dumps(res["objetivos_9_4"], ensure_ascii=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--simular", action="store_true",
                    help="regenerar el JSON por acta con el motor de hoy (necesita el detalle del censo; ≈ 15 min)")
    ap.add_argument("--detalle", default=None, help=f"parquet del censo para --simular (default: {ce.DETALLE})")
    ap.add_argument("--actas", default=None, help=f"JSON por acta (default: {ACTAS})")
    ap.add_argument("--salida", default=None, help=f"default: {SALIDA}")
    ap.add_argument("--reemplazar", action="store_true", help="regenerar archivos de este comando (nunca uno ajeno)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    args = ap.parse_args(argv)
    raw = sys.argv[1:] if argv is None else list(argv)

    ruta_actas = Path(args.actas) if args.actas else REPO / ACTAS
    salida = Path(args.salida) if args.salida else REPO / SALIDA
    try:
        proteger(salida, args.reemplazar)
        if args.simular:
            proteger(ruta_actas, args.reemplazar)
    except MV.DestinoProtegido as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    if args.simular:
        detalle = Path(args.detalle) if args.detalle else REPO / ce.DETALLE
        if not detalle.is_file():
            print(f"ERROR: --simular necesita el detalle del censo y no está: {detalle}", file=sys.stderr)
            return 4
        escribir_actas(simular_actas(detalle), ruta_actas)
        print(f"-> {ruta_actas}")
    est, a = cargar_actas(ruta_actas)
    res = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "metodo": {"n_boot": args.n_boot, "semilla": args.semilla, "semilla_recalibracion": SEMILLA_RECAL,
                      "unidad_de_remuestreo": "ley (bootstrap de Poisson, ADR-0032)",
                      "mayoria_simple": "tipo normalizado SIMPLE (lo desconocido cuenta como simple) con resultado oficial "
                                        "afirmativo/negativo; la banda usa todas las actas SIMPLE",
                      "constante": "tasa base del subconjunto (recalculada en cada réplica del bootstrap)",
                      "disputada": "min(afirmativos, votantes − afirmativos) / votantes >= 0,10",
                      "modelo_menos_constante": "Brier(modelo, P recortada a [1e-4, 1−1e-4]) − Brier(constante); negativo = "
                                                "el modelo le gana a la constante",
                      "banda": "el recuento real de afirmativos (entre los que votaron) cae en [p5, p95] simulado",
                      "declarada": DECLARADA},
           "procedencia": procedencia(est, ruta_actas, raw)}
    res.update(medir(a, args.n_boot, args.semilla))
    MV.escribir(res, salida)
    imprimir(res)
    print(f"-> {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
