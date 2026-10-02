# -*- coding: utf-8 -*-
"""CONTROL INDEPENDIENTE del motor (auditoría 2026-09: Fase 2 y, como test de regresión, ítem B3).

QUÉ HACE. Reimplementa, desde el voto crudo y SIN importar el motor ni el harness (`modelo/`, `variables/`,
`evaluacion/`, `definiciones`, `rutas`: se verifica por AST), un puñado de predictores del voto emitido y los mide
sobre los votos del censo con la misma métrica (skill contra la climatología de la muestra). Responde tres
preguntas: (1) ¿el motor le gana a un predictor trivial hecho aparte?; (2) ¿un récord propio, con fecha estricta y
otra ley, cae cerca del 0,13? (si sí, el 0,1333 no depende de la implementación del harness); (3) ¿este mismo
código detecta una fuga si se la ponemos a propósito? (control positivo). No usa la ficha de desvío, β, ε₀, τ, la
presencia ni las puertas.

DE LA AUDITORÍA AL TEST. Sin argumentos corre el TEST (lo que corre el CI, ≈ 1 minuto). Con `--auditoria` conserva
el modo de la fase 2 (el detalle del censo, el bootstrap de 2.000 réplicas y el JSON).

EL PROBLEMA QUE RESUELVE EL CARGADOR `cargar_desde_git`. El control exacto lee el detalle del censo
(`censo_detalle_*.parquet`, ≈ 40 MB, IGNORADO por git) para saber qué votos se evaluaron. Un test de la suite
no puede depender de un archivo que el CI no tiene. Con lo que SÍ viaja por git —la canónica, `origen_por_acta` y
el JSON de estadísticos de A2, que trae por acta la ley, el `n`, el Σy y las sumas del motor— se reconstruyen 696.792
votos contra los 691.845 del censo (el harness descarta ≈ 0,7% y sin el detalle no se sabe cuáles), y el récord
encogido con origen da 0,1353 contra 0,1335. Por eso en el CI el control se reproduce DENTRO DE 0,002 y contra su
propia ancla; **el 0,1335 exacto sólo se reproduce donde está el detalle** (sección 6, que se saltea si falta).

INDEPENDENCIA, ACOTADA. El control no comparte código con el motor. Comparte con el harness la AGRUPACIÓN de actas
en leyes (`ley_por_acta`, que llega por el JSON) y las sumas del motor (también del JSON): son entradas, no lógica.

    python evaluacion/baseline/tests/test_control_independiente.py                      # el test
    python evaluacion/baseline/tests/test_control_independiente.py --auditoria [--detalle RUTA] [--salida RUTA]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
CLEAN = RAIZ / "datos" / "canonica" / "data" / "clean"
ORIGEN = RAIZ / "variables" / "proyecto" / "data" / "origen_por_acta.parquet"
# El censo del motor de hoy (re-anclado a propósito en D1.0 de la auditoría: la ficha de desvío al día; antes, el
# del 28-09). El control no depende del motor: sus anclas no cambian; la del motor sí (ANCLA_MOTOR).
DETALLE = RAIZ / "evaluacion" / "baseline" / "outputs" / "censo_detalle_2026-10-02.parquet"
ESTADISTICOS = RAIZ / "evaluacion" / "baseline" / "outputs" / "censo_estadisticos_2026-10-02.json"
SALIDA = RAIZ / "Archivos_Borrar" / "auditoria" / "control_independiente.json"

ERAS = pd.to_datetime(["1990-01-01", "2011-12-10", "2015-12-10", "2019-12-10", "2023-12-10", "2030-01-01"])
ERA_LAB = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]
K = 5.0            # pseudo-conteo del encogimiento (el mismo valor que usa el motor, a propósito)
N_BOOT = 2000
SEMILLA = 11
VACIOS = {"", "NAN", "NONE", "DESCONOCIDO", "SIN DATO", "S/D"}
PROHIBIDOS = {"modelo", "variables", "evaluacion", "definiciones", "rutas", "nowcast_puertas",
              "baseline_voto_individual", "ensemble", "bloque", "agregador"}

# ── las anclas del test (fijadas en el pre-registro de B3, `ESTADO-EJECUCION.md`) ─────────────────────────────
PRINCIPAL = "record_encogido_con_origen"
ANCLA_GIT = 0.1353         # el control sobre lo que viaja por git (696.792 votos)
TOL_ANCLA_GIT = 0.0005
PUBLICADO = 0.1335         # el control exacto, con el detalle del censo (auditoría, 691.845 votos)
TOL_PUBLICADO = 0.005      # lo que puede separar a la reconstrucción del exacto
ANCLA_MOTOR = 0.1336       # el motor de hoy, recalculado desde las sumas del JSON (0,1333 hasta D1.0: medido el
                           # 2026-10-02 sobre el censo nuevo, ESTADO-EJECUCION.md D1.0)
TOL_ANCLA_MOTOR = 0.0002
TOL_MOTOR_CONTROL = 0.01   # cuánto pueden separarse el motor y el control independiente
SEPARACION_FUGA = 0.05     # cuánto más tiene que dar el récord con fuga que el limpio
N_EVALUADOS_GIT, N_LEYES = 696_792, 3_731


# ══════════════════════════════════════════════════════════════════════ los cargadores
def _historia_cruda() -> pd.DataFrame:
    """Todos los votos emitidos de la canónica, con fecha, cámara y origen (la historia del control)."""
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
    return v.merge(o, on="acta_id", how="left")


def cargar(detalle_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(historia, evaluados) EXACTOS: los evaluados son los votos del detalle del censo (691.845)."""
    v = _historia_cruda()
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


def cargar_desde_git() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(historia, evaluados, JSON) con SÓLO lo que viaja por git: la canónica, el origen y el JSON de estadísticos
    (la ley de cada acta). Los evaluados son los votos emitidos de las actas del JSON: 696.792, no 691.845."""
    j = json.loads(ESTADISTICOS.read_text(encoding="utf-8"))
    actas = pd.DataFrame(j["actas"]["filas"], columns=j["actas"]["columnas"])
    v = _historia_cruda()
    v["linaje"] = v["bloque_linaje"].astype(str)
    v["ley"] = v["acta_id"].map(actas.set_index("acta_id")["ley"]).fillna("acta:" + v["acta_id"])
    v["era"] = pd.cut(v["fecha"], ERAS, labels=ERA_LAB, right=False).astype(str)
    e = v[v["acta_id"].isin(set(actas["acta_id"]))].copy()
    e["y"] = e["af"]
    e = e.dropna(subset=["era"]).reset_index(drop=True)
    return v, e, j


# ═════════════════════════════════════════════════════════════════════ los predictores
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


def predictores(e: pd.DataFrame, v: pd.DataFrame, k: float = K, completo: bool = True) -> dict:
    """Los predictores del control. `k` es el pseudo-conteo del encogimiento; con `completo=False` sólo el
    principal (`record_encogido_con_origen`), que es lo que necesitan las derivas del test."""
    tiene_o = e["origen"].notna().to_numpy()
    e = e.copy()
    e["origen"] = e["origen"].fillna("_")
    v = v.copy()
    v["origen"] = v["origen"].fillna("_")
    v = v.dropna(subset=["era"])

    n_b, a_b = historia(e, v, ["camara", "era"])
    base = np.where(n_b > 0, a_b / np.maximum(n_b, 1), 0.5)
    n_l, a_l = historia(e, v, ["camara", "linaje", "era"])
    bloque = (a_l + k * base) / (n_l + k)
    n_r, a_r = historia(e, v, ["legislador_id", "era"])
    rec = np.where(n_r > 0, a_r / np.maximum(n_r, 1), np.nan)
    p1 = np.where(n_r > 0, rec, bloque)
    p4 = (a_r + k * bloque) / (n_r + k)

    # con ORIGEN (sólo donde se conoce; el resto cae a p4, como el motor cae a no condicionar)
    n_lo, a_lo = historia(e, v, ["camara", "linaje", "era", "origen"])
    bloque_o = (a_lo + k * bloque) / (n_lo + k)
    n_ro, a_ro = historia(e, v, ["legislador_id", "era", "origen"])
    p6 = np.where(tiene_o, (a_ro + k * bloque_o) / (n_ro + k), p4)
    if not completo:
        return {PRINCIPAL: p6}

    # SIN GUARD DE ERA: el mismo récord con origen, pero SIN cortar por era (usa todo el pasado del legislador)
    n_rg, a_rg = historia(e, v, ["legislador_id"])
    p4_ng = (a_rg + k * bloque) / (n_rg + k)
    n_rog, a_rog = historia(e, v, ["legislador_id", "origen"])
    p6_ng = np.where(tiene_o, (a_rog + k * bloque_o) / (n_rog + k), p4_ng)

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
    p_fuga = (a_f + k * bloque) / (np.maximum(n_f, 0) + k)

    return {"climatologia_walkforward": base, "bloque_ingenuo": bloque, "record_puro": p1,
            "record_encogido_al_bloque": p4, PRINCIPAL: p6,
            "record_con_origen_SIN_guard_de_era": p6_ng,
            "persistencia_ultima_fecha": p5,
            "CONTROL_POSITIVO_record_con_fuga_del_mismo_dia": p_fuga}


# ════════════════════════════════════════════════════════════════════ la métrica
def skill_puntual(p: np.ndarray, y: np.ndarray) -> float:
    """skill = 1 − Brier / Brier de la climatología de la muestra (b·(1−b))."""
    b = float(np.mean(y))
    return float(1 - np.mean((p - y) ** 2) / (b - b ** 2))


def skill_motor_desde_json(j: dict, factor: float = 1.0) -> float:
    """El skill del motor de hoy (`estricta__general`) recalculado desde las sumas por acta del JSON de A2.
    `factor` multiplica sus Σ(p−y)²: sirve para simular que el motor empeora o mejora (deriva sintética)."""
    c = {nombre: i for i, nombre in enumerate(j["actas"]["columnas"])}
    filas = j["actas"]["filas"]
    n = sum(f[c["n"]] for f in filas)
    sy = sum(f[c["sy"]] for f in filas)
    se = sum(f[c["se__estricta__general"]] for f in filas) * factor
    b = sy / n
    return float(1 - (se / n) / (b - b ** 2))


def skill_y_ic(se: dict, y: np.ndarray, ley: np.ndarray, comparar: str | None = None) -> dict:
    """skill (1 − Brier/Brier climatología de la muestra) con IC 95% Poisson-bootstrap sobre LEYES;
    y, si `comparar`, ΔBrier pareado (predictor − comparar), IC sobre leyes. (Modo de la auditoría.)"""
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


def diagnosticar(skill_control: float, skill_motor: float, skill_limpio: float | None = None,
                 skill_fuga: float | None = None) -> list[str]:
    """Las discrepancias (vacío = todo en orden) entre el control independiente, su ancla, lo publicado y el motor.
    Es la ÚNICA función que decide «hay desvío»: el test y las derivas sintéticas la comparten."""
    d = []
    if abs(skill_control - ANCLA_GIT) > TOL_ANCLA_GIT:
        d.append(f"el control se alejó de su ancla: {skill_control:.4f} contra {ANCLA_GIT} ± {TOL_ANCLA_GIT}")
    if abs(skill_control - PUBLICADO) > TOL_PUBLICADO:
        d.append(f"el control ya no reproduce el {PUBLICADO} de la auditoría: {skill_control:.4f} "
                 f"(tolerancia ± {TOL_PUBLICADO})")
    if abs(skill_motor - ANCLA_MOTOR) > TOL_ANCLA_MOTOR:
        d.append(f"el motor (sumas del JSON) se movió: {skill_motor:.4f} contra {ANCLA_MOTOR} ± {TOL_ANCLA_MOTOR}")
    if abs(skill_motor - skill_control) > TOL_MOTOR_CONTROL:
        d.append(f"el motor y el control independiente ya no coinciden: {skill_motor:.4f} contra {skill_control:.4f} "
                 f"(diferencia > {TOL_MOTOR_CONTROL})")
    if skill_limpio is not None and skill_fuga is not None and skill_fuga - skill_limpio < SEPARACION_FUGA:
        d.append(f"el control de fuga ya no separa: con fuga {skill_fuga:.4f}, limpio {skill_limpio:.4f} "
                 f"(tiene que dar al menos {SEPARACION_FUGA} más)")
    return d


# ════════════════════════════════════════════════════════════════ la independencia
def verificar_independencia(texto: str | None = None) -> list[str]:
    """Imports prohibidos (motor, harness, rutas, definiciones) en `texto`, o en ESTE archivo si no se da."""
    arbol = ast.parse(texto if texto is not None else Path(__file__).read_text(encoding="utf-8"))
    mal = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            mal += [a.name for a in nodo.names if a.name.split(".")[0] in PROHIBIDOS]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.split(".")[0] in PROHIBIDOS:
            mal.append(nodo.module)
    return mal


# ═════════════════════════════════════════════════════════════════════════ el test
def test(fallos: list[str]) -> int:
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    t0 = time.time()

    print("1. independencia por AST, con su control positivo")
    check(not verificar_independencia(), f"el control importa algo del motor o del harness: {verificar_independencia()}")
    for texto in ("import nowcast_puertas", "from rutas import RAIZ", "from evaluacion.baseline.src import x",
                  "import baseline_voto_individual as B"):
        check(bool(verificar_independencia(texto)), f"el verificador NO marcó «{texto}»: no podría detectar una dependencia")
    check(not verificar_independencia("import numpy as np\nfrom pathlib import Path"),
          "el verificador marcó imports que no son del motor")

    print("\n2. lo que viaja por git reconstruye los votos evaluados")
    v, e, j = cargar_desde_git()
    check(len(e) == N_EVALUADOS_GIT, f"votos evaluados {len(e):,} ≠ {N_EVALUADOS_GIT:,}")
    check(e["ley"].nunique() == N_LEYES, f"leyes {e['ley'].nunique():,} ≠ {N_LEYES:,}")
    print(f"  {len(e):,} votos, {e['ley'].nunique():,} leyes ({time.time() - t0:.0f} s)")

    print("\n3. el control reproduce el 0,1335 (en el CI, acotado) y coincide con el motor")
    pred = predictores(e, v)
    y = e["y"].to_numpy(float)
    skills = {k: skill_puntual(p, y) for k, p in pred.items()}
    skill_motor = skill_motor_desde_json(j)
    for k, s in skills.items():
        print(f"  {k:<50} skill {s:>7.4f}")
    print(f"  {'MOTOR (sumas del JSON de A2)':<50} skill {skill_motor:>7.4f}")
    fuga = skills["CONTROL_POSITIVO_record_con_fuga_del_mismo_dia"]
    dif = diagnosticar(skills[PRINCIPAL], skill_motor, skills[PRINCIPAL], fuga)
    check(not dif, "el control independiente y el motor ya no coinciden con lo anclado:\n      " + "\n      ".join(dif))

    print("\n4. control positivo de fuga: el récord con fuga del mismo día tiene que dar más que el limpio")
    check(fuga - skills[PRINCIPAL] >= SEPARACION_FUGA,
          f"con fuga {fuga:.4f}, limpio {skills[PRINCIPAL]:.4f}: el control no separa la fuga")
    print(f"  con fuga {fuga:.4f} contra limpio {skills[PRINCIPAL]:.4f} (separa {fuga - skills[PRINCIPAL]:.3f})")

    print("\n5. el control DETECTA el desvío (control positivo de la comparación)")
    # (a) deriva del motor: sus Σ(p−y)² × 0,88 lo llevan a un skill ≈ 0,2
    mov = skill_motor_desde_json(j, 0.88)
    d_a = diagnosticar(skills[PRINCIPAL], mov)
    check(bool(d_a), f"una deriva del motor (skill {mov:.3f}) NO se detectó")
    check(not diagnosticar(skills[PRINCIPAL], skill_motor_desde_json(j, 1.0)), "sin deriva, el diagnóstico marcó algo")
    print(f"  (a) motor con Σ(p−y)² × 0,88 → skill {mov:.3f}: {len(d_a)} discrepancias")
    # (b) deriva de los datos: el mismo predictor sin origen
    e_sin, v_sin = e.assign(origen=np.nan), v.assign(origen=np.nan)
    s_sin = skill_puntual(predictores(e_sin, v_sin, completo=False)[PRINCIPAL], y)
    d_b = diagnosticar(s_sin, skill_motor)
    check(bool(d_b), f"una deriva de los datos (sin origen, skill {s_sin:.3f}) NO se detectó")
    print(f"  (b) el mismo predictor sin origen → skill {s_sin:.3f}: {len(d_b)} discrepancias")
    # (c) deriva del parámetro: K del encogimiento 5 → 50
    s_k = skill_puntual(predictores(e, v, k=50.0, completo=False)[PRINCIPAL], y)
    d_c = diagnosticar(s_k, skill_motor)
    check(bool(d_c) and abs(s_k - skills[PRINCIPAL]) > 0.01,
          f"una deriva del parámetro (K = 50, skill {s_k:.3f}) NO se detectó")
    print(f"  (c) K del encogimiento 5 → 50 → skill {s_k:.3f}: {len(d_c)} discrepancias")

    print("\n6. el 0,1335 EXACTO, sólo donde está el detalle del censo")
    if DETALLE.is_file():
        v2, e2 = cargar(DETALLE)
        e2 = e2.dropna(subset=["era"]).reset_index(drop=True)
        p2 = predictores(e2, v2)
        y2 = e2["y"].to_numpy(float)
        ex = {k: skill_puntual(p, y2) for k, p in p2.items()}
        motor_ex = skill_puntual(e2["p__estricta__general"].to_numpy(float), y2)
        check(len(e2) == 691_845, f"el detalle tiene {len(e2):,} votos evaluados, no 691.845")
        check(abs(ex[PRINCIPAL] - PUBLICADO) <= 0.0001, f"el control exacto da {ex[PRINCIPAL]:.4f}, no {PUBLICADO}")
        check(abs(motor_ex - ANCLA_MOTOR) <= 0.0001, f"el motor sobre el detalle da {motor_ex:.4f}, no {ANCLA_MOTOR}")
        check(abs(ex["CONTROL_POSITIVO_record_con_fuga_del_mismo_dia"] - 0.2039) <= 0.0002,
              f"el control de fuga exacto da {ex['CONTROL_POSITIVO_record_con_fuga_del_mismo_dia']:.4f}, no 0,2039")
        print(f"  exacto: control {ex[PRINCIPAL]:.4f}, motor {motor_ex:.4f}, fuga "
              f"{ex['CONTROL_POSITIVO_record_con_fuga_del_mismo_dia']:.4f}")
    else:
        print(f"  SALTEADO: no está el detalle del censo ({DETALLE.name}, no viaja por git). "
              "Se regenera con `censo_detalle_paralelo.py` (43 min); el 0,1335 exacto se reproduce donde exista.")

    print(f"\n{corridos - len(fallos)}/{corridos} OK  ({time.time() - t0:.0f} s)")
    return corridos


# ═════════════════════════════════════════════════ el modo de la auditoría (exacto, con IC)
def auditoria(detalle: Path, salida: Path) -> int:
    mal = verificar_independencia()
    if mal:
        raise SystemExit(f"NO es independiente: importa {mal}")
    v, e = cargar(detalle)
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
    # ON/OFF del guard de era: ΔBrier pareado por ley de "sin guard" contra "con guard" (mismo récord con origen)
    G, N = PRINCIPAL, "record_con_origen_SIN_guard_de_era"
    res["guard_de_era_on_off"] = {
        nom: skill_y_ic({G: se[G][m], N: se[N][m]}, y[m], e["ley"].to_numpy()[m], comparar=G)["predictores"][N]["dBrier_vs_" + G]
        for nom, m in cortes.items()}
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    g = res["cortes"]["global"]
    print(f"votos={g['n_votos']:,} leyes={g['n_leyes']:,} tasa_base={g['tasa_base']}")
    for k, f in g["predictores"].items():
        print(f"  {k:<62} skill {f['skill']:>7}  IC {f['ic95_ley']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Control independiente: el test (sin argumentos) o el modo de la auditoría.")
    ap.add_argument("--auditoria", action="store_true", help="el modo de la fase 2: detalle del censo, IC y JSON")
    ap.add_argument("--detalle", default=str(DETALLE))
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    if a.auditoria:
        return auditoria(Path(a.detalle), Path(a.salida))
    fallos: list[str] = []
    test(fallos)
    if fallos:
        print(f"\n{len(fallos)} FALLAS:")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("todos los tests pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
