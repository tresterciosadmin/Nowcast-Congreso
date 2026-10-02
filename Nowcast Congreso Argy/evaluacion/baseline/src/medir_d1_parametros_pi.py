# -*- coding: utf-8 -*-
"""D1 de la auditoría 2026-09: los siete hiperparámetros de P_i, walk-forward contra V0 (el motor de D1.0).

    python evaluacion/baseline/src/medir_d1_parametros_pi.py                       # el veredicto, desde los JSON de git
    python evaluacion/baseline/src/medir_d1_parametros_pi.py --censo k_postura=10  # el censo de un brazo (PC, ≈ 16 min)
    python evaluacion/baseline/src/medir_d1_parametros_pi.py --censo todos         # los nueve brazos de la grilla
    python evaluacion/baseline/src/medir_d1_parametros_pi.py --controles           # controles de los brazos (PC, 60 actas)
    python evaluacion/baseline/src/medir_d1_parametros_pi.py --panel               # el panel primario, SIN leer `y` (PC)
    python evaluacion/baseline/src/medir_d1_parametros_pi.py --medir               # selección anual, Δ y veredicto (PC)

LA REGLA es el pre-registro de D1 y el protocolo de la fase D (`ESTADO-EJECUCION.md`); este archivo la ejecuta y no
la cambia. Resumen: para cada parámetro y cada año Y de test (Diputados 2006–2026, Senado 2007–2026) se elige el
valor de la grilla que minimiza la suma de Brier de los votos de ENTRENAMIENTO (actas < 1-ene-Y de las dos cámaras,
sin las leyes con actas de test en Y; empate < 1e-12 relativo → V0); el compuesto WF son las P_i del valor de cada
año; se contrasta contra V0 en el panel primario (votos OOS donde alguna alternativa de la grilla final da distinto),
con IC por ley y por mes (Poisson, 2.000 réplicas, semilla 7), p* = máx(p_ley; p_mes), Holm a 0,05 con m = 7, y el
árbol del punto 6 del protocolo (Z → F → C → E → A/B → D).

UN SOLO CAMINO DE CÁLCULO. En la PC (`--medir`) se arma, por parámetro, una TABLA POR ACTA (suma de Brier de cada
valor de la grilla sobre los votos del panel, suma de |Δp| contra V0, votos del panel, suma de Brier de V0 sobre
todos los votos del acta, y la del V0 original —el censo del 28-09— sobre el panel). Todo lo demás —selección,
compuesto, IC, p, Holm, veredicto— sale de esa tabla, que viaja por git; el test del CI recalcula el veredicto desde
ella sin el detalle del censo.

LOS BRAZOS. k y ventana de la postura y el origen por lado son brazos del HARNESS (`baseline_voto_individual`,
argumento `brazo`): el motor no se toca. k del récord, `MIN_HIST` y `MIN_VOTOS_FICHA` se recomponen desde las
columnas del detalle de V0 (`medir_ficha_al_dia.recalcular`). El guard usa el brazo «sin corte» ya corrido sobre V0
(`medir_sin_corte_por_era`). Nada pisa números versionados: destino que existe → salida 3 salvo `--reemplazar`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_estadisticos as ce  # noqa: E402

GENERADOR = "evaluacion/baseline/src/medir_d1_parametros_pi.py"
OUT = REPO / "evaluacion" / "baseline" / "outputs"
V0_TAG = "2026-10-02"                                     # el censo de V0 (el motor de D1.0)
DETALLE_V0 = REPO / ce.DETALLE                            # censo_detalle_2026-10-02.parquet (ignorado por git)
DETALLE_V0_ORIGINAL = OUT / "censo_detalle_2026-09-28.parquet"   # V0 original (continuidad)
DETALLE_GUARD = OUT / f"censo_detalle_sin_corte_era_{V0_TAG}.parquet"
SALIDA = OUT / "d1_parametros_pi.json"
SALIDA_PANEL = OUT / "d1_panel_primario.json"
SALIDA_CONTROLES = OUT / "d1_controles_brazos.json"
OOS = {"diputados": "2006-01-01", "senado": "2007-01-01"}
ERA_VIGENTE = "2023-12-10"
DESDE_2010 = "2010-01-01"
ERAS = pd.to_datetime(["1990-01-01", "2011-12-10", "2015-12-10", "2019-12-10", "2023-12-10", "2030-01-01"])
ERA_LAB = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]
N_BOOT, SEMILLA, ALFA, M_HOLM, MARGEN = 2000, 7, 0.05, 7, 1.0
EMPATE = 1e-12
FORMATO = 1

# ─── las grillas del pre-registro (tabla del punto 1). `ext`: el valor con que se extiende cada borde (None = no hay)
GRILLAS = {
    "k_record":        {"v0": 5.0, "grilla": [0.0, 1.0, 2.5, 5.0, 10.0, 20.0, 40.0], "ext": {"abajo": None, "arriba": 80.0},
                        "tipo": "sin_censo", "umbral_F": 2.0, "nombre": "k del récord (K_SHRINK_RECORD)"},
    "min_hist":        {"v0": 1, "grilla": [1, 2, 4, 8, 16], "ext": {"abajo": None, "arriba": 32},
                        "tipo": "sin_censo", "umbral_F": 2.0, "nombre": "MIN_HIST_INDIVIDUAL"},
    "min_votos_ficha": {"v0": 20, "grilla": [5, 10, 20, 40, 80], "ext": {"abajo": 2, "arriba": 160},
                        "tipo": "sin_censo", "umbral_F": 2.0, "nombre": "MIN_VOTOS_FICHA"},
    "k_postura":       {"v0": 5.0, "grilla": [1.0, 2.5, 5.0, 10.0, 20.0], "ext": {"abajo": 0.5, "arriba": 40.0},
                        "tipo": "censo", "clave": "k_postura", "umbral_F": 2.0, "nombre": "k de la postura"},
    "ventana_postura": {"v0": 730, "grilla": [365, 548, 730, 1095, 1460], "ext": {"abajo": 182, "arriba": 2190},
                        "tipo": "censo", "clave": "ventana_postura", "umbral_F": 2.0, "nombre": "ventana de la postura"},
    "origen":          {"v0": "fino", "grilla": ["fino", "lado"], "ext": {"abajo": None, "arriba": None},
                        "tipo": "censo", "clave": "origen", "umbral_F": 3.0, "nombre": "granularidad del origen"},
    "guard":           {"v0": "prendido", "grilla": ["prendido", "sin_corte"], "ext": {"abajo": None, "arriba": None},
                        "tipo": "guard", "umbral_F": 3.0, "nombre": "guard de era"},
}
COLS_ARM = ["acta_id", "fecha", "camara", "legislador", "y", "ley", "origen", "p", "fuente", "share", "desvio",
            "record", "n_prev", "ficha_n_votos", "ficha_n_reciente", "ficha_tasa_desvio", "ficha_tasa_desvio_conducta",
            "ficha_tasa_desvio_reciente", "ficha_tasa_desvio_reciente_conducta", "ficha_desvio_linaje"]
FICHA6 = ["ficha_n_votos", "ficha_n_reciente", "ficha_tasa_desvio", "ficha_tasa_desvio_conducta",
          "ficha_tasa_desvio_reciente", "ficha_tasa_desvio_reciente_conducta"]


def etiqueta(v) -> str:
    """El nombre de un valor de la grilla en los JSON (sin ceros sobrantes: 5.0 → '5', 2.5 → '2.5')."""
    return f"{v:g}" if isinstance(v, float) else str(v)


def nombre_brazo(par: str, v) -> str:
    return f"{GRILLAS[par]['clave']}={etiqueta(v)}"


def brazo_de(nombre: str) -> tuple[str, object, dict]:
    """'k_postura=10' → (parámetro, valor, brazo del harness)."""
    clave, _, txt = nombre.partition("=")
    par = next(p for p, g in GRILLAS.items() if g.get("clave") == clave)
    v0 = GRILLAS[par]["v0"]
    v = txt if isinstance(v0, str) else type(v0)(float(txt))
    return par, v, {clave: v}


def detalle_brazo(nombre: str) -> Path:
    return OUT / f"censo_detalle_d1_{nombre.replace('=', '-')}_sobre_{V0_TAG}.parquet"


def brazos_de_la_grilla() -> list[str]:
    return [nombre_brazo(p, v) for p, g in GRILLAS.items() if g["tipo"] == "censo" for v in g["grilla"] if v != g["v0"]]


def proteger(destino: Path, reemplazar: bool) -> None:
    if destino.exists() and not reemplazar:
        raise FileExistsError(f"{destino} ya existe: no se pisa (pasar --reemplazar si es de este comando)")
    if destino.exists() and destino.suffix == ".json":
        try:
            propio = json.loads(destino.read_text(encoding="utf-8")).get("generador") == GENERADOR
        except (OSError, ValueError, AttributeError):
            propio = False
        if not propio:
            raise FileExistsError(f"{destino} existe y no es de este comando: no se pisa")


def escribir_json(obj: dict, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes((json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"-> {destino}", flush=True)


# ═══════════════════════════════════════════════ el censo de un brazo (PC)
def _tramo(args):
    """Un tramo de fechas. El brazo viaja como ARGUMENTO (el pool usa `spawn`)."""
    desde, hasta, brazo = args
    import logging
    from baseline_voto_individual import correr, silenciar_avisos_del_motor
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=f"%(asctime)s [{desde}] %(message)s")
    silenciar_avisos_del_motor()
    t0 = time.time()
    res, d = correr(desde=desde, hasta=hasta, historia="estricta", record_por_tema=False, devolver_detalle=True,
                    brazo=brazo)
    logging.getLogger("censo").info("tramo %s..%s: %d votos en %.1f min · saltadas %d", desde, hasta, len(d),
                                    (time.time() - t0) / 60, res["n_actas_saltadas"])
    return d[COLS_ARM]


def correr_censo(nombre: str, procesos: int, tramos: int, reemplazar: bool) -> Path:
    if os.environ.get("GUARD_ERA") == "0":
        raise RuntimeError("GUARD_ERA=0 en el entorno: el brazo mediría otra cosa")
    destino = detalle_brazo(nombre)
    proteger(destino, reemplazar)
    _par, _v, brazo = brazo_de(nombre)
    from censo_detalle_paralelo import bordes
    t0 = time.time()
    print(f"censo del brazo {nombre} ({brazo}) …", flush=True)
    with get_context("spawn").Pool(procesos) as pool:
        partes = list(pool.imap_unordered(_tramo, [(a, b, brazo) for a, b in bordes(tramos)]))
    d = pd.concat(partes, ignore_index=True).sort_values(["fecha", "acta_id"]).reset_index(drop=True)
    if d.duplicated(["acta_id", "legislador"]).any():
        raise RuntimeError("votos duplicados entre tramos: los bordes se pisan")
    d.to_parquet(destino, index=False)
    print(f"-> {destino} ({len(d)} votos, {(time.time() - t0) / 60:.1f} min)", flush=True)
    return destino


# ═══════════════════════════════════════════════ los controles de los brazos (PC; punto 3 del pre-registro)
def _muestra_60(d: pd.DataFrame, n_actas: int = 60) -> pd.DataFrame:
    """Las actas de `metrica_de_verdad.py --verificar-motor 60`: estratificadas por era × cámara, misma semilla."""
    import metrica_de_verdad as MV
    from baseline_voto_individual import ERA_BINS, ERA_LABELS
    actas = d.drop_duplicates("acta_id")[["acta_id", "fecha", "camara"]].copy()
    actas["era"] = pd.cut(actas["fecha"], ERA_BINS, labels=ERA_LABELS)
    celdas = [g for _, g in actas.groupby(["era", "camara"], observed=True)]
    por_celda = max(1, n_actas // len(celdas))
    return pd.concat([g.sort_values("acta_id").sample(min(len(g), por_celda), random_state=MV.SEMILLA_VIGENCIA)
                      for g in celdas]).sort_values(["fecha", "acta_id"])


def _gobierno_por_regla(ctx, d: pd.DataFrame, ya: set, n: int = 3) -> pd.DataFrame:
    """Anti-vacuidad, regla fija: 3 actas de origen del lado del gobierno, en el orden de la semilla 7."""
    a = d.drop_duplicates("acta_id")[["acta_id", "fecha", "camara"]]
    gob = a["acta_id"].map(ctx.origen_map).isin(["EJECUTIVO", "OFICIALISMO", "ALIADOS"]) & ~a["acta_id"].isin(ya)
    return a[gob.to_numpy()].sort_values(["fecha", "acta_id"]).sample(n, random_state=SEMILLA)


def _p_harness(ctx, actas: pd.DataFrame, por_acta: dict) -> dict:
    out = {}
    for r in actas.itertuples():
        res = ctx.p_legisladores(r.acta_id, r.camara, r.fecha, por_acta[r.acta_id], "estricta", False)
        for lid, x in (res or {}).items():
            out[(r.acta_id, str(lid))] = (x[0], x[1])
    return out


def _comparar(a: dict, b: dict) -> dict:
    ks = set(a) & set(b)
    dp = np.array([abs(a[k][0] - b[k][0]) for k in ks]) if ks else np.zeros(0)
    return {"comparados": int(len(ks)), "solo_en_uno": int(len(set(a) ^ set(b))),
            "max_abs_dp": float(dp.max()) if len(dp) else None, "distintos": int((dp > 0).sum())}


def correr_controles(reemplazar: bool) -> int:
    """(a) la rama por defecto es el motor (`--verificar-motor 60`); (b) el brazo con los valores de V0 explícitos, uno
    solo y por año, reproduce V0 exacto; (c) anti-vacuidad: cada clave con un valor alternativo mueve alguna P_i; (d) el
    recálculo sin censo representa al motor con K = 20, MIN_HIST = 8 y MIN_VOTOS_FICHA = 80."""
    proteger(REPO / SALIDA_CONTROLES, reemplazar)
    import metrica_de_verdad as MV
    from baseline_voto_individual import Contexto, silenciar_avisos_del_motor   # primero: pone las rutas del motor
    import ensemble
    import nowcast_puertas as NP
    sys.path.insert(0, str(REPO / "coordinacion" / "AUDITORIA-2026-09"))
    from medir_ficha_al_dia import recalcular
    t0 = time.time()
    out: dict = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat()}
    print("(a) la rama por defecto es el motor …", flush=True)
    out["a_rama_por_defecto"] = MV.verificar_motor(DETALLE_V0, 60)
    silenciar_avisos_del_motor()
    d = _leer(DETALLE_V0, COLS_ARM)
    ctx0 = Contexto.desde_repo()
    emit = ctx0.votos[ctx0.votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    por_acta = {k: g for k, g in emit.groupby("acta_id", sort=False)}
    muestra = _muestra_60(d)

    def ctx(brazo):
        return Contexto(ctx0.votos, ctx0.ley_de_acta, ctx0.origen_map, ctx0.cond, ctx0.conf_area,
                        desvios=ctx0.desvios, brazo=brazo)

    ref = d[d["acta_id"].isin(muestra["acta_id"])]
    ref_p = {(a, str(l)): (p, None) for a, l, p in zip(ref["acta_id"], ref["legislador"], ref["p"])}
    v0_h = _p_harness(ctx(None), muestra, por_acta)
    out["muestra"] = {"actas": int(len(muestra)), "votos_v0": int(len(ref_p)), "harness_v0_contra_censo": _comparar(v0_h, ref_p)}
    anios = range(1990, 2031)
    explicito = {"k_postura": 5.0, "ventana_postura": 730, "origen": "fino"}
    print("(b) el brazo con los valores de V0 …", flush=True)
    out["b_v0_explicito"] = _comparar(_p_harness(ctx(explicito), muestra, por_acta), ref_p)
    out["b_v0_explicito_por_anio"] = _comparar(
        _p_harness(ctx({k: {y: v for y in anios} for k, v in explicito.items()}), muestra, por_acta), ref_p)
    print("(c) anti-vacuidad …", flush=True)
    out["c_anti_vacuidad"] = {}
    for brazo in ({"k_postura": 10.0}, {"ventana_postura": 365}, {"origen": "lado"}):
        c = _comparar(_p_harness(ctx(brazo), muestra, por_acta), v0_h)
        if c["distintos"] == 0:
            extra = _gobierno_por_regla(ctx0, d, set(muestra["acta_id"]))
            c = _comparar(_p_harness(ctx(brazo), extra, por_acta), _p_harness(ctx(None), extra, por_acta))
            c["actas_sumadas_por_regla"] = list(extra["acta_id"])
        out["c_anti_vacuidad"][json.dumps(brazo)] = c
    print("(d) el recálculo representa al motor …", flush=True)
    out["d_recalculo"] = {}
    cases = (("K_SHRINK_RECORD", 20.0, (1, 20, 20.0)), ("MIN_HIST_INDIVIDUAL", 8, (8, 20, 5.0)),
             ("MIN_VOTOS_FICHA", 80, (1, 80, 5.0)))
    for nombre, valor, args in cases:
        viejo_np = getattr(NP, nombre, None)
        viejo_def = ensemble.desvio_de_ficha.__defaults__
        try:
            if nombre == "MIN_VOTOS_FICHA":
                ensemble.desvio_de_ficha.__defaults__ = (valor,)
            else:
                setattr(NP, nombre, valor)
            h = _p_harness(ctx(None), muestra, por_acta)
        finally:
            ensemble.desvio_de_ficha.__defaults__ = viejo_def
            if nombre != "MIN_VOTOS_FICHA":
                setattr(NP, nombre, viejo_np)
        pr = recalcular(ref, *args)
        rec = {(a, str(l)): (p, None) for a, l, p in zip(ref["acta_id"], ref["legislador"], pr)}
        c = _comparar(h, rec)
        mov = _comparar(h, v0_h)
        c["p_i_que_el_valor_mueve"] = mov["distintos"]
        c["p_i_de_bloque_que_mueve"] = int(sum(1 for k in set(h) & set(v0_h) if h[k][0] != v0_h[k][0] and h[k][1] == "bloque"))
        out["d_recalculo"][f"{nombre}={valor}"] = c
    ok_b = all(out[k]["max_abs_dp"] == 0 and out[k]["solo_en_uno"] == 0 for k in ("b_v0_explicito", "b_v0_explicito_por_anio"))
    ok_c = all(c["distintos"] > 0 for c in out["c_anti_vacuidad"].values())
    ok_d = all(c["max_abs_dp"] == 0 and c["solo_en_uno"] == 0 and c["p_i_que_el_valor_mueve"] > 0
               for c in out["d_recalculo"].values()) and out["d_recalculo"]["MIN_VOTOS_FICHA=80"]["p_i_de_bloque_que_mueve"] > 0
    from baseline_voto_individual import LADO_DE
    from rutas import PROYECTO_ORIGEN_POR_ACTA
    opa = pd.read_parquet(PROYECTO_ORIGEN_POR_ACTA, columns=["origen", "origen_lado"])
    con = opa[opa["origen"].isin(list(LADO_DE))]
    out["lado_de_igual_a_origen_lado"] = bool((con["origen"].map(LADO_DE) == con["origen_lado"]).all()
                                              and opa.loc[~opa["origen"].isin(list(LADO_DE)), "origen_lado"].isna().all())
    out["cumple"] = {"a": bool(out["a_rama_por_defecto"]["vigente"]), "b": ok_b, "c": ok_c, "d": ok_d,
                     "lado": out["lado_de_igual_a_origen_lado"]}
    out["minutos"] = round((time.time() - t0) / 60, 1)
    escribir_json(out, REPO / SALIDA_CONTROLES)
    print(json.dumps(out["cumple"]), flush=True)
    return 0 if all(out["cumple"].values()) else 2


# ═══════════════════════════════════════════════ las P_i de cada valor de la grilla (PC)
def _leer(ruta: Path, cols: list[str]) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(f"falta {ruta}: correr el censo de ese brazo")
    d = pd.read_parquet(ruta, columns=cols)
    d["acta_id"] = d["acta_id"].astype(str)
    return d


def matriz(par: str, valores: list, con_y: bool) -> tuple[pd.DataFrame, dict]:
    """Los votos (intersección de todos los brazos del parámetro) con una columna `p::<valor>` por valor de la grilla.
    `con_y=False` (el paso del panel) no lee el voto real. Devuelve también los controles del brazo."""
    g = GRILLAS[par]
    base_cols = [c for c in COLS_ARM if c != "y" or con_y]
    v0 = _leer(DETALLE_V0, base_cols)
    ctl: dict = {"votos_v0": int(len(v0))}
    if g["tipo"] == "sin_censo":
        sys.path.insert(0, str(REPO / "coordinacion" / "AUDITORIA-2026-09"))
        from medir_ficha_al_dia import recalcular
        args = {"k_record": lambda v: (1, 20, float(v)), "min_hist": lambda v: (int(v), 20, 5.0),
                "min_votos_ficha": lambda v: (1, int(v), 5.0)}[par]
        for v in valores:
            v0[f"p::{etiqueta(v)}"] = recalcular(v0, *args(v))
        ctl["control_positivo_max_abs_dp"] = float(np.abs(v0[f"p::{etiqueta(g['v0'])}"] - v0["p"]).max())
        return v0, ctl
    keys = ["acta_id", "legislador"]
    m = v0.copy()
    m[f"p::{etiqueta(g['v0'])}"] = m["p"]
    for v in valores:
        if v == g["v0"]:
            continue
        if g["tipo"] == "guard":
            b = _leer(DETALLE_GUARD, keys + ["p"] + (["y"] if con_y else []))
        else:
            b = _leer(detalle_brazo(nombre_brazo(par, v)), [c for c in base_cols])
        lab = etiqueta(v)
        b = b.rename(columns={c: f"{c}::{lab}" for c in b.columns if c not in keys})
        antes = len(m)
        m = m.merge(b, on=keys, how="inner", validate="1:1")
        ctl[f"brazo {lab}"] = {"votos_del_brazo": int(len(b)), "votos_que_caen_de_la_interseccion": int(antes - len(m)),
                               "votos_que_el_brazo_agrega": int(len(b) - len(m))}
        if con_y:
            ctl[f"brazo {lab}"]["y_identico"] = bool((m[f"y::{lab}"] == m["y"]).all())
    ctl["votos_interseccion"] = int(len(m))
    ctl["leyes_que_caen"] = int(v0["ley"].fillna("acta:" + v0["acta_id"]).nunique()
                                - m["ley"].fillna("acta:" + m["acta_id"]).nunique())
    return m, ctl


def controles_no_actua(par: str, m: pd.DataFrame, valores: list) -> dict:
    """Donde el parámetro no puede actuar, max|Δp| = 0 (tabla del punto 3 del pre-registro)."""
    g, out = GRILLAS[par], {}
    p0 = m[f"p::{etiqueta(g['v0'])}"].to_numpy()
    oos = es_oos(m)
    for v in valores:
        if v == g["v0"]:
            continue
        lab = etiqueta(v)
        dp = np.abs(m[f"p::{lab}"].to_numpy() - p0)
        c: dict = {"votos_distintos": int((dp > 0).sum()), "votos_distintos_oos": int(((dp > 0) & oos).sum())}
        if par == "k_record":
            c["fuera_de_la_rama_del_record"] = int(((dp > 0) & ~rama_record(m)).sum())
        elif par == "min_hist":
            n = m["n_prev"].fillna(0).to_numpy()
            c["con_n_prev_mayor_o_igual_al_valor_o_en_bloque"] = int(((dp > 0) & ((n >= int(v)) | ~rama_record(m))).sum())
        elif par == "min_votos_ficha":
            c["en_la_rama_del_record"] = int(((dp > 0) & rama_record(m)).sum())
        elif par == "guard":
            c["antes_de_2015-12-10"] = int(((dp > 0) & (m["fecha"] < pd.Timestamp("2015-12-10")).to_numpy()).sum())
        else:
            desconocido = m["origen"].isna().to_numpy()
            c["origen_desconocido"] = int(((dp > 0) & desconocido).sum()) if par in ("k_postura", "origen") else None
            if par == "origen":
                c["origen_oposicion"] = int(((dp > 0) & (m["origen"] == "OPOSICION").to_numpy()).sum())
            if par in ("k_postura", "ventana_postura"):
                c["record_o_n_prev_distinto"] = int((~_igual(m["record"], m[f"record::{lab}"])
                                                     | ~_igual(m["n_prev"], m[f"n_prev::{lab}"])).sum())
            c["ficha6_distinta"] = int(sum((~_igual(m[f], m[f"{f}::{lab}"])).sum() for f in FICHA6))
            c["desvio_linaje_distinto"] = int((~_igual(m["ficha_desvio_linaje"], m[f"ficha_desvio_linaje::{lab}"])).sum())
        out[lab] = c
    return out


def _igual(a: pd.Series, b: pd.Series) -> np.ndarray:
    a, b = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
    return (a == b) | (np.isnan(a) & np.isnan(b))


def rama_record(m: pd.DataFrame) -> np.ndarray:
    return (~m["record"].isna() & (m["n_prev"].fillna(0) >= 1)).to_numpy()


def es_oos(m: pd.DataFrame) -> np.ndarray:
    corte = pd.to_datetime(m["camara"].map(OOS))
    return (pd.to_datetime(m["fecha"]) >= corte).to_numpy()


def ley_de(m: pd.DataFrame) -> pd.Series:
    return m["ley"].fillna("acta:" + m["acta_id"].astype(str))


def panel_de(m: pd.DataFrame, par: str, valores: list) -> np.ndarray:
    """Votos (todos los años) donde ALGUNA alternativa de la grilla da distinto que V0."""
    p0 = m[f"p::{etiqueta(GRILLAS[par]['v0'])}"].to_numpy()
    dif = np.zeros(len(m), bool)
    for v in valores:
        dif |= np.abs(m[f"p::{etiqueta(v)}"].to_numpy() - p0) > 0
    return dif


def resumen_panel(m: pd.DataFrame, dif: np.ndarray) -> dict:
    oos, ley = es_oos(m), ley_de(m).to_numpy()
    pp = dif & oos
    f = pd.to_datetime(m["fecha"]).to_numpy()
    cam = m["camara"].to_numpy()
    return {"votos_oos": int(pp.sum()), "fraccion_del_oos": round(float(pp.sum() / oos.sum()), 4),
            "leyes": int(pd.Series(ley[pp]).nunique()), "diputados": int((pp & (cam == "diputados")).sum()),
            "senado": int((pp & (cam == "senado")).sum()),
            "era_vigente": int((pp & (f >= np.datetime64(ERA_VIGENTE))).sum()),
            "votos_todos_los_anios": int(dif.sum()), "oos_total": int(oos.sum())}


def correr_panel(reemplazar: bool) -> int:
    """El paso del panel: SÓLO compara P_i (no lee `y`). Con la grilla base y, aparte, con las extensiones que ya
    tienen sus P_i (las de los parámetros sin censo siempre)."""
    proteger(REPO / SALIDA_PANEL, reemplazar)
    out = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "lee_y": False, "detalle_v0": DETALLE_V0.name, "parametros": {}}
    for par, g in GRILLAS.items():
        t0 = time.time()
        ext = [x for x in g["ext"].values() if x is not None]
        disp_ext = [x for x in ext if g["tipo"] == "sin_censo" or detalle_brazo(nombre_brazo(par, x)).exists()]
        m, ctl = matriz(par, g["grilla"] + disp_ext, con_y=False)
        r = {"grilla": [etiqueta(v) for v in g["grilla"]], "v0": etiqueta(g["v0"]), "controles_del_brazo": ctl,
             "donde_no_puede_actuar": controles_no_actua(par, m, g["grilla"] + disp_ext),
             "panel_grilla_base": resumen_panel(m, panel_de(m, par, g["grilla"]))}
        if disp_ext:
            r["panel_con_extension"] = {"valores": [etiqueta(x) for x in disp_ext],
                                        **resumen_panel(m, panel_de(m, par, g["grilla"] + disp_ext))}
        out["parametros"][par] = r
        print(f"{par}: panel {r['panel_grilla_base']['votos_oos']} votos OOS, {r['panel_grilla_base']['leyes']} leyes "
              f"({time.time() - t0:.0f} s)", flush=True)
    escribir_json(out, REPO / SALIDA_PANEL)
    return 0


# ═══════════════════════════════════════════════ la tabla por acta (PC) — lo único que sale del voto a voto
def tabla_por_acta(par: str, valores: list) -> tuple[pd.DataFrame, dict]:
    m, ctl = matriz(par, valores, con_y=True)
    y = m["y"].to_numpy(float)
    dif = panel_de(m, par, valores)
    p0 = m[f"p::{etiqueta(GRILLAS[par]['v0'])}"].to_numpy()
    orig = _leer(DETALLE_V0_ORIGINAL, ["acta_id", "legislador", "p__estricta__general"])
    m = m.merge(orig, on=["acta_id", "legislador"], how="left", validate="1:1")
    if m["p__estricta__general"].isna().any():
        raise RuntimeError("votos sin V0 original: el censo del 28-09 no tiene el mismo conjunto")
    g = pd.DataFrame({"acta_id": m["acta_id"].to_numpy()})
    g["n_panel"] = dif.astype(int)
    g["n_todos"] = 1
    g["e0_todos"] = (p0 - y) ** 2
    g["e_orig"] = np.where(dif, (m["p__estricta__general"].to_numpy() - y) ** 2, 0.0)
    for v in valores:
        lab = etiqueta(v)
        pv = m[f"p::{lab}"].to_numpy()
        g[f"e::{lab}"] = np.where(dif, (pv - y) ** 2, 0.0)
        g[f"a::{lab}"] = np.abs(pv - p0)
    t = g.groupby("acta_id", sort=False).sum()
    meta = m.drop_duplicates("acta_id").set_index("acta_id")[["fecha", "camara", "ley"]]
    t = meta.join(t).reset_index()
    t["fecha"] = pd.to_datetime(t["fecha"]).dt.strftime("%Y-%m-%d")
    t["ley"] = t["ley"].fillna("acta:" + t["acta_id"])
    return t.sort_values(["fecha", "acta_id"]).reset_index(drop=True), ctl


def tabla_a_json(t: pd.DataFrame) -> dict:
    cols = {}
    for c in t.columns:
        x = t[c]
        cols[c] = [round(float(v), 12) for v in x] if x.dtype.kind == "f" else (
            [int(v) for v in x] if x.dtype.kind in "iu" else [str(v) for v in x])
    return cols


def tabla_de_json(cols: dict) -> pd.DataFrame:
    return pd.DataFrame(cols)


# ═══════════════════════════════════════════════ el veredicto, desde la tabla por acta (lo que recalcula el CI)
def _anio(t: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(t["fecha"]).dt.year.to_numpy()


def oos_actas(t: pd.DataFrame) -> np.ndarray:
    return es_oos(t)


def seleccion_anual(t: pd.DataFrame, par: str, valores: list) -> dict:
    """{año de test: valor elegido con el entrenamiento} y el valor WF final (con todo)."""
    v0 = GRILLAS[par]["v0"]
    anio, oos, ley = _anio(t), oos_actas(t), t["ley"].to_numpy()
    fecha = pd.to_datetime(t["fecha"]).to_numpy()
    E = np.column_stack([t[f"e::{etiqueta(v)}"].to_numpy(float) for v in valores])

    def elegir(mask):
        s = E[mask].sum(axis=0)
        best = s.min()
        i0 = valores.index(v0)
        if s[i0] - best <= EMPATE * max(best, 1e-300):
            return v0, s
        return valores[int(np.argmin(s))], s

    sel, sumas = {}, {}
    for Y in sorted(set(anio[oos])):
        test_leyes = set(ley[oos & (anio == Y)])
        entr = (fecha < np.datetime64(f"{Y}-01-01")) & ~np.isin(ley, list(test_leyes))
        sel[int(Y)], s = elegir(entr)
        sumas[int(Y)] = {etiqueta(v): float(x) for v, x in zip(valores, s)}
    final, _ = elegir(np.ones(len(t), bool))
    return {"por_anio": sel, "final": final, "sumas_entrenamiento": sumas}


def toca_borde(par: str, sel: dict, valores: list) -> list[str]:
    """Los lados extensibles en los que algún año eligió el borde de la grilla."""
    g, lados = GRILLAS[par], []
    num = [v for v in valores if not isinstance(v, str)]
    if not num:
        return []
    for lado, borde in (("abajo", min(num)), ("arriba", max(num))):
        if g["ext"][lado] is not None and g["ext"][lado] not in valores and any(v == borde for v in sel["por_anio"].values()):
            lados.append(lado)
    return lados


def boot(d: np.ndarray, b0: np.ndarray, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """ΔBrier relativo (%) con IC 95% y p del bootstrap de Poisson sobre grupos (el de `censo_estadisticos`)."""
    k = len(d)
    W = np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = 100 * (W @ d) / (W @ b0)
    rel = rel[np.isfinite(rel)]
    p = min(1.0, 2 * min(1 + (rel <= 0).sum(), 1 + (rel >= 0).sum()) / (1 + n_boot))
    return {"dBrier_rel_%": round(float(100 * d.sum() / b0.sum()), 4), "ic95": [round(float(np.percentile(rel, 2.5)), 4),
            round(float(np.percentile(rel, 97.5)), 4)], "p": float(p), "se_%": round(float(rel.std(ddof=1)), 4),
            "grupos": int(k)}


def contraste(t: pd.DataFrame, e1: np.ndarray, e0: np.ndarray, mask: np.ndarray) -> dict:
    """Δ = (Σe1 − Σe0) / Σe0 sobre las actas de `mask`, con IC por ley y por mes."""
    if not mask.any() or e0[mask].sum() == 0:
        return {"actas": 0}
    out = {"actas": int(mask.sum()), "votos": int(t["n_panel"].to_numpy()[mask].sum()),
           "leyes": int(t.loc[mask, "ley"].nunique())}
    for nom, grupo in (("por_ley", t["ley"]), ("por_mes", t["fecha"].str[:7])):
        s = pd.DataFrame({"g": grupo.to_numpy()[mask], "d": (e1 - e0)[mask], "b0": e0[mask]}).groupby("g", sort=True).sum()
        out[nom] = boot(s["d"].to_numpy(), s["b0"].to_numpy())
    return out


def compuesto(t: pd.DataFrame, sel: dict) -> tuple[np.ndarray, np.ndarray]:
    """Suma de Brier del compuesto WF por acta (en las actas OOS) y su suma de |Δp| contra V0."""
    anio, oos = _anio(t), oos_actas(t)
    e = np.zeros(len(t))
    a = np.zeros(len(t))
    for Y, v in sel["por_anio"].items():
        m = oos & (anio == Y)
        e[m] = t.loc[m, f"e::{etiqueta(v)}"].to_numpy(float)
        a[m] = t.loc[m, f"a::{etiqueta(v)}"].to_numpy(float)
    return e, a


def medir_parametro(t: pd.DataFrame, par: str, valores: list) -> dict:
    g = GRILLAS[par]
    sel = seleccion_anual(t, par, valores)
    e_c, a_c = compuesto(t, sel)
    oos = oos_actas(t)
    e0 = t[f"e::{etiqueta(g['v0'])}"].to_numpy(float)
    prim = oos & (t["n_panel"].to_numpy() > 0)
    f = pd.to_datetime(t["fecha"]).to_numpy()
    res = {"parametro": par, "nombre": g["nombre"], "v0": etiqueta(g["v0"]), "grilla": [etiqueta(v) for v in valores],
           "trayectoria": {str(Y): etiqueta(v) for Y, v in sel["por_anio"].items()},
           "valor_wf_final": etiqueta(sel["final"]),
           "anios_en_v0": int(sum(v == g["v0"] for v in sel["por_anio"].values())),
           "identico_a_v0_en_el_panel": bool(a_c[prim].sum() == 0),
           "primario": contraste(t, e_c, e0, prim)}
    d_glob = (e_c - e0)[oos].sum()
    res["global_oos"] = {"dBrier_rel_%": round(float(100 * d_glob / t["e0_todos"].to_numpy()[oos].sum()), 4),
                         "votos": int(t["n_todos"].to_numpy()[oos].sum())}
    res["subgrupos"] = {"era_vigente": contraste(t, e_c, e0, prim & (f >= np.datetime64(ERA_VIGENTE)))}
    for cam in ("diputados", "senado"):
        res["subgrupos"][cam] = contraste(t, e_c, e0, prim & (t["camara"].to_numpy() == cam))
    res["descriptivo"] = {"desde_2010": contraste(t, e_c, e0, prim & (f >= np.datetime64(DESDE_2010))),
                          "contra_v0_original": contraste(t, e_c, t["e_orig"].to_numpy(float), prim)}
    era = pd.cut(pd.to_datetime(t["fecha"]), ERAS, labels=ERA_LAB).astype(str).to_numpy()
    for e in ERA_LAB:
        res["descriptivo"][f"era={e}"] = contraste(t, e_c, e0, prim & (era == e))
    pr = res["primario"]
    if pr.get("actas"):
        res["primario"]["p_estrella"] = max(pr["por_ley"]["p"], pr["por_mes"]["p"])
        res["primario"]["mde_%"] = round(2.8 * max(pr["por_ley"]["se_%"], pr["por_mes"]["se_%"]), 4)
    return res


def holm(ps: dict, alfa: float = ALFA, m: int = M_HOLM) -> dict:
    """{parámetro: rechaza} con Holm sobre `m` p* (los que faltan cuentan como p = 1)."""
    orden = sorted(ps.items(), key=lambda kv: kv[1])
    rech, sigue = {}, True
    for i, (k, p) in enumerate(orden):
        sigue = sigue and p <= alfa / (m - i)
        rech[k] = bool(sigue)
    return rech


def arbol(r: dict, rechaza: bool) -> dict:
    """El árbol del punto 6 del protocolo para un hiperparámetro (contraste compuesto WF contra V0)."""
    g = GRILLAS[r["parametro"]]
    pr = r["primario"]
    if r["identico_a_v0_en_el_panel"] or not pr.get("actas"):
        return {"salida": "Z", "accion": "conservar V0 (sin cambio)"}
    if r["global_oos"]["dBrier_rel_%"] < -max(g["umbral_F"], 0.0):
        return {"salida": "F", "accion": "en suspenso: invariancia por insumo y revisión del mecanismo"}
    il, im = pr["por_ley"]["ic95"], pr["por_mes"]["ic95"]
    if all(-MARGEN <= x <= MARGEN for x in il + im):
        return {"salida": "C", "accion": "conservar V0 (equivalente)"}
    d = pr["por_ley"]["dBrier_rel_%"]
    lado_bueno = il[1] < 0 and im[1] < 0
    lado_malo = il[0] > 0 and im[0] > 0
    if rechaza and lado_bueno:
        danios = [k for k, s in r["subgrupos"].items() if s.get("actas") and s["por_ley"]["ic95"][0] > 0]
        if danios:
            return {"salida": "E", "accion": "no se cambia; va a Franco", "danio_en": danios}
        return {"salida": "A", "accion": f"recalibrar al valor WF final ({r['valor_wf_final']})"
                + (" — es V0: se conserva y se dice que el óptimo cambió en el tiempo" if r["valor_wf_final"] == r["v0"] else "")}
    if rechaza and lado_malo and d > 0:
        return {"salida": "B", "accion": "conservar V0 (no generaliza)"}
    return {"salida": "D", "accion": f"conservar V0; MDE {pr.get('mde_%')}%"}


def veredicto(resultados: dict) -> dict:
    ps = {k: (1.0 if r["identico_a_v0_en_el_panel"] or not r["primario"].get("actas") else r["primario"]["p_estrella"])
          for k, r in resultados.items()}
    rech = holm(ps)
    out = {k: {"p_estrella_holm": ps[k], "holm_rechaza": rech[k], **arbol(r, rech[k])} for k, r in resultados.items()}
    en_a = [k for k, v in out.items() if v["salida"] == "A"]
    return {"por_parametro": out, "m_holm": M_HOLM, "faltan": [p for p in GRILLAS if p not in resultados],
            "en_A": en_a, "confirmacion_conjunta_necesaria": len(en_a) > 1}


def valores_de(par: str, tabla: pd.DataFrame) -> list:
    """Los valores de la grilla presentes en una tabla por acta (con la extensión si se usó), en el orden de la grilla."""
    g = GRILLAS[par]
    todos = sorted(set(g["grilla"]) | {x for x in g["ext"].values() if x is not None},
                   key=lambda v: (isinstance(v, str), v if not isinstance(v, str) else g["grilla"].index(v)))
    return [v for v in todos if f"e::{etiqueta(v)}" in tabla.columns]


def medir(reemplazar: bool) -> int:
    proteger(REPO / SALIDA, reemplazar)
    est, res, faltan_ext = {}, {}, {}
    for par, g in GRILLAS.items():
        t0 = time.time()
        valores = list(g["grilla"])
        t, ctl = tabla_por_acta(par, valores)
        sel = seleccion_anual(t, par, valores)
        lados = toca_borde(par, sel, valores)
        borde = {"grilla_base_toca": lados}
        if lados:
            ext = [g["ext"][l] for l in lados]
            faltan = [nombre_brazo(par, x) for x in ext
                      if g["tipo"] == "censo" and not detalle_brazo(nombre_brazo(par, x)).exists()]
            if faltan:
                faltan_ext[par] = faltan          # no se calcula ningún Δ OOS de este parámetro hasta tener la extensión
                print(f"{par}: toca el borde {lados}; faltan los brazos {faltan}: correr --censo y repetir", flush=True)
                continue
            valores = sorted(valores + ext) if not isinstance(valores[0], str) else valores + ext
            t, ctl = tabla_por_acta(par, valores)
            sel2 = seleccion_anual(t, par, valores)
            borde["con_extension"] = [etiqueta(x) for x in ext]
            # la extensión es el borde nuevo de su lado: si algún año la elige, se dice y no se extiende más
            borde["vuelve_a_tocar"] = bool(any(v in ext for v in sel2["por_anio"].values()))
        est[par] = {"valores": [etiqueta(v) for v in valores], "tabla": tabla_a_json(t)}
        r = medir_parametro(t, par, valores)
        r["borde"], r["controles_de_la_matriz"] = borde, ctl
        res[par] = r
        pr = r["primario"]
        print(f"{par}: WF final {r['valor_wf_final']}, {r['anios_en_v0']} años en V0; "
              f"Δ {pr.get('por_ley', {}).get('dBrier_rel_%')}% ley {pr.get('por_ley', {}).get('ic95')} "
              f"mes {pr.get('por_mes', {}).get('ic95')} ({time.time() - t0:.0f} s)", flush=True)
    if faltan_ext:
        print("FALTAN BRAZOS DE EXTENSIÓN:", faltan_ext, file=sys.stderr)
        return 4
    salida = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
              "detalle_v0": DETALLE_V0.name, "detalle_v0_sha256_16": ce._sha16(DETALLE_V0),
              "metodo": {"n_boot": N_BOOT, "semilla": SEMILLA, "alfa": ALFA, "m_holm": M_HOLM, "margen_%": MARGEN,
                         "oos": OOS, "empate_relativo": EMPATE},
              "resultados": res, "veredicto": veredicto(res), "estadisticos_por_acta": est}
    escribir_json(salida, REPO / SALIDA)
    return 0


def recalcular_desde_json(ruta: Path = REPO / SALIDA) -> dict:
    """Lo que hace el CI: rehace resultados y veredicto desde las tablas por acta del JSON."""
    j = json.loads(ruta.read_text(encoding="utf-8"))
    res = {}
    for par, e in j["estadisticos_por_acta"].items():
        t = tabla_de_json(e["tabla"])
        valores = [v for v in valores_de(par, t)]
        res[par] = medir_parametro(t, par, valores)
    return {"resultados": res, "veredicto": veredicto(res), "guardado": j}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--censo", nargs="+", default=None, help="brazos: 'k_postura=10', 'ventana_postura=365', 'origen=lado' o 'todos'")
    ap.add_argument("--controles", action="store_true")
    ap.add_argument("--panel", action="store_true")
    ap.add_argument("--medir", action="store_true")
    ap.add_argument("--procesos", type=int, default=7)
    ap.add_argument("--tramos", type=int, default=21)
    ap.add_argument("--reemplazar", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.censo:
            nombres = brazos_de_la_grilla() if a.censo == ["todos"] else a.censo
            for n in nombres:
                if a.censo == ["todos"] and detalle_brazo(n).exists() and not a.reemplazar:
                    print(f"{n}: ya está ({detalle_brazo(n).name})", flush=True)
                    continue
                correr_censo(n, a.procesos, a.tramos, a.reemplazar)
            return 0
        if a.controles:
            return correr_controles(a.reemplazar)
        if a.panel:
            return correr_panel(a.reemplazar)
        if a.medir:
            return medir(a.reemplazar)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    r = recalcular_desde_json()
    for par, v in r["veredicto"]["por_parametro"].items():
        print(f"{par:<16} {v['salida']}  {v['accion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
