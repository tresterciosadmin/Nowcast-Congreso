# -*- coding: utf-8 -*-
"""FASE 1 de `coordinacion/PROMPT-GUARD-DE-ERA-POR-TEMA.md` — ¿el récord
INDIVIDUAL POR TEMA es más estable entre recambios de GOBIERNO que el récord
general? Objeción de Franco al guard de era (ADR-0018): el guard resetea
TODO el récord individual en cada recambio, con el argumento de que "votar
afirmativo" cambia de significado según quién gobierna — correcto para la
relación con el Ejecutivo (récord GENERAL), pero el récord POR TEMA
("¿está a favor de la desregulación laboral?") es una posición sustantiva
que debería persistir más allá de qué gobierno esté. Caso testigo: Pichetto
(22 años activo, ambas cámaras) llegó a votar Ley Bases con el récord
reseteado a cero, pese a tener historia real.

LA PREGUNTA, MEDIBLE: para cada legislador que ATRAVIESA un recambio de
gobierno (2015-12-10, 2019-12-10, 2023-12-10 — los tres que hay en la
canónica; antes de 2015-12-10 todo es una sola era "KIRCHNER" en
`definiciones.GOBIERNOS`, no hay más recambios que medir), y para cada
(legislador, área) con muestra a ambos lados: ¿su tasa afirmativa ANTES del
recambio correlaciona con la de DESPUÉS? Contraste: la MISMA pregunta para
el récord GENERAL (sin área). La hipótesis de Franco predice
temática ALTA, general BAJA.

CERO GASTO DE API: usa `tema_por_acta.parquet` tal como está hoy. NO TOCA
EL MOTOR: sólo lee y mide.

    python evaluacion/baseline/src/medir_estabilidad_record_por_tema.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("medir_estabilidad_record_por_tema")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))

K_SHRINK = 5.0
UMBRALES_N = [3, 5, 10]
_AUX_PREFIX = "AUX"

# límites de era de `definiciones.py::GOBIERNOS` (raíz del repo) -- los
# ÚNICOS recambios que el guard de era (ADR-0018) trata como tales. Antes de
# 2015-12-10 la canónica entera cae en la era "KIRCHNER" (1900-2015-12-10):
# no hay un cuarto recambio que medir ahí, es una sola era larga por diseño.
RECAMBIOS = ["2015-12-10", "2019-12-10", "2023-12-10"]


def _areas_de(todas_ids) -> list[str]:
    if not todas_ids or (isinstance(todas_ids, float) and pd.isna(todas_ids)):
        return []
    vistas: list[str] = []
    for i in str(todas_ids).split(";"):
        i = i.strip()
        if not i or i.upper().startswith(_AUX_PREFIX):
            continue
        area = i.split(".")[0].upper()
        if area not in vistas:
            vistas.append(area)
    return vistas


def cargar_votos_con_area() -> pd.DataFrame:
    from bloque import cargar as cargar_bloque

    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)

    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    tpa = tpa[["acta_id", "todas_ids"]].drop_duplicates("acta_id")
    v = v.merge(tpa, on="acta_id", how="left")
    v["areas"] = v["todas_ids"].map(_areas_de)
    return v


def _ventanas(fechas_ordenadas: list[str]) -> list[tuple[str, str]]:
    """[(desde, hasta_exclusivo), ...] -- una por era, desde el génesis de la
    canónica hasta 'infinito' (hoy)."""
    bordes = ["1900-01-01"] + fechas_ordenadas + ["2100-01-01"]
    return [(bordes[i], bordes[i + 1]) for i in range(len(bordes) - 1)]


def _shrink(n: np.ndarray, share: np.ndarray, prior: float, k: float = K_SHRINK) -> np.ndarray:
    return (n * share + k * prior) / (n + k)


def _corr_por_umbral(antes: pd.Series, despues: pd.Series, n_antes: pd.Series,
                     n_despues: pd.Series, prior_antes: float, prior_despues: float) -> dict:
    """Encoge cada lado hacia el prior de SU PROPIA ventana (EB, k=5) y
    correlaciona -- para varios umbrales de n mínimo a AMBOS lados."""
    s_antes = _shrink(n_antes.to_numpy(float), antes.to_numpy(float), prior_antes)
    s_despues = _shrink(n_despues.to_numpy(float), despues.to_numpy(float), prior_despues)
    out = {}
    for u in UMBRALES_N:
        mask = (n_antes >= u) & (n_despues >= u)
        if mask.sum() < 3:
            out[f"n>={u}"] = {"n_pares": int(mask.sum()), "correlacion": None}
            continue
        r = float(np.corrcoef(s_antes[mask], s_despues[mask])[0, 1])
        out[f"n>={u}"] = {"n_pares": int(mask.sum()), "correlacion": round(r, 4)}
    return out


def medir_recambio(v: pd.DataFrame, ventana_antes: tuple[str, str],
                   ventana_despues: tuple[str, str], recambio: str) -> dict:
    a_desde, a_hasta = ventana_antes
    d_desde, d_hasta = ventana_despues
    antes = v[(v["fecha"] >= a_desde) & (v["fecha"] < a_hasta)]
    despues = v[(v["fecha"] >= d_desde) & (v["fecha"] < d_hasta)]

    # ---- récord GENERAL (contraste): por legislador, sin área ----
    g_a = antes.groupby("legislador_id")["af"].agg(n_antes="size", share_antes="mean")
    g_d = despues.groupby("legislador_id")["af"].agg(n_despues="size", share_despues="mean")
    g = g_a.join(g_d, how="inner")  # sólo continuadores: dato a AMBOS lados
    prior_g_antes = float(antes["af"].mean()) if len(antes) else 0.5
    prior_g_despues = float(despues["af"].mean()) if len(despues) else 0.5
    corr_general = _corr_por_umbral(g["share_antes"], g["share_despues"],
                                    g["n_antes"], g["n_despues"], prior_g_antes, prior_g_despues)

    # ---- récord por ÁREA (la hipótesis) ----
    ax = antes[antes["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
    dx = despues[despues["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
    a_agg = ax.groupby(["legislador_id", "area"])["af"].agg(n_antes="size", share_antes="mean")
    d_agg = dx.groupby(["legislador_id", "area"])["af"].agg(n_despues="size", share_despues="mean")
    t = a_agg.join(d_agg, how="inner").reset_index()
    prior_por_area_antes = ax.groupby("area")["af"].mean().to_dict()
    prior_por_area_despues = dx.groupby("area")["af"].mean().to_dict()
    t["prior_antes"] = t["area"].map(prior_por_area_antes)
    t["prior_despues"] = t["area"].map(prior_por_area_despues)
    t = t.dropna(subset=["prior_antes", "prior_despues"])

    # correlación temática POOLED (usa el prior de CADA área, no uno global)
    corr_tematica = {}
    t["s_antes"] = t.apply(lambda r: (r["n_antes"] * r["share_antes"] + K_SHRINK * r["prior_antes"])
                           / (r["n_antes"] + K_SHRINK), axis=1)
    t["s_despues"] = t.apply(lambda r: (r["n_despues"] * r["share_despues"] + K_SHRINK * r["prior_despues"])
                             / (r["n_despues"] + K_SHRINK), axis=1)
    for u in UMBRALES_N:
        sub = t[(t["n_antes"] >= u) & (t["n_despues"] >= u)]
        if len(sub) < 3:
            corr_tematica[f"n>={u}"] = {"n_pares": int(len(sub)), "correlacion": None}
            continue
        r = float(np.corrcoef(sub["s_antes"], sub["s_despues"])[0, 1])
        corr_tematica[f"n>={u}"] = {"n_pares": int(len(sub)), "correlacion": round(r, 4)}

    # heterogeneidad por área (umbral fijo n>=5, el del medio)
    por_area = {}
    for area, sub in t.groupby("area"):
        sub5 = sub[(sub["n_antes"] >= 5) & (sub["n_despues"] >= 5)]
        if len(sub5) < 5:
            por_area[area] = {"n_pares": int(len(sub5)), "correlacion": None}
            continue
        r = float(np.corrcoef(sub5["s_antes"], sub5["s_despues"])[0, 1])
        por_area[area] = {"n_pares": int(len(sub5)), "correlacion": round(r, 4)}

    # composición del universo de continuadores -- sesgo de supervivencia
    activos_antes = set(antes["legislador_id"].unique())
    activos_despues = set(despues["legislador_id"].unique())
    continuadores = activos_antes & activos_despues
    linaje_antes = antes.drop_duplicates("legislador_id").set_index("legislador_id")["bloque_linaje"]
    frac_provincial_todos = float(linaje_antes.eq(
        "OTRO / PROVINCIAL").mean()) if len(linaje_antes) else None
    linaje_continuadores = linaje_antes.reindex(list(continuadores))
    frac_provincial_continuadores = (float(linaje_continuadores.eq("OTRO / PROVINCIAL").mean())
                                     if len(linaje_continuadores) else None)

    return {
        "recambio": recambio,
        "ventana_antes": ventana_antes, "ventana_despues": ventana_despues,
        "n_legisladores_activos_antes": len(activos_antes),
        "n_legisladores_activos_despues": len(activos_despues),
        "n_continuadores": len(continuadores),
        "frac_continuadores_sobre_activos_antes": (
            round(len(continuadores) / len(activos_antes), 4) if activos_antes else None),
        "composicion_bloque_linaje_OTRO_o_PROVINCIAL": {
            "todos_los_activos_antes": round(frac_provincial_todos, 4) if frac_provincial_todos is not None else None,
            "solo_continuadores": (round(frac_provincial_continuadores, 4)
                                   if frac_provincial_continuadores is not None else None),
        },
        "correlacion_GENERAL_por_umbral": corr_general,
        "correlacion_TEMATICA_por_umbral": corr_tematica,
        "correlacion_tematica_por_area_n5": por_area,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    logger.info("cargando votos + área explotada...")
    v = cargar_votos_con_area()
    logger.info("%d votos AFIRM/NEG totales, rango %s a %s", len(v), v["fecha"].min(), v["fecha"].max())

    ventanas = _ventanas(RECAMBIOS)  # una ventana MÁS que recambios (la primera, sin recambio previo)
    resultados = []
    for i, recambio in enumerate(RECAMBIOS):
        ventana_antes = ventanas[i]
        ventana_despues = ventanas[i + 1]
        logger.info("recambio %s: antes=%s despues=%s", recambio, ventana_antes, ventana_despues)
        resultados.append(medir_recambio(v, ventana_antes, ventana_despues, recambio))

    # pooled: concatenar los pares (legislador, área, recambio) de los 3 recambios
    ax_list, dx_list = [], []
    for i, recambio in enumerate(RECAMBIOS):
        a_desde, a_hasta = ventanas[i]
        d_desde, d_hasta = ventanas[i + 1]
        antes = v[(v["fecha"] >= a_desde) & (v["fecha"] < a_hasta)]
        despues = v[(v["fecha"] >= d_desde) & (v["fecha"] < d_hasta)]
        ax = antes[antes["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
        dx = despues[despues["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
        a_agg = ax.groupby(["legislador_id", "area"])["af"].agg(n_antes="size", share_antes="mean")
        d_agg = dx.groupby(["legislador_id", "area"])["af"].agg(n_despues="size", share_despues="mean")
        t = a_agg.join(d_agg, how="inner").reset_index()
        t["recambio"] = recambio
        prior_a = ax.groupby("area")["af"].mean().to_dict()
        prior_d = dx.groupby("area")["af"].mean().to_dict()
        t["prior_antes"] = t["area"].map(prior_a)
        t["prior_despues"] = t["area"].map(prior_d)
        t = t.dropna(subset=["prior_antes", "prior_despues"])
        ax_list.append(t)
    pooled = pd.concat(ax_list, ignore_index=True)
    pooled["s_antes"] = (pooled["n_antes"] * pooled["share_antes"] + K_SHRINK * pooled["prior_antes"]) / (pooled["n_antes"] + K_SHRINK)
    pooled["s_despues"] = (pooled["n_despues"] * pooled["share_despues"] + K_SHRINK * pooled["prior_despues"]) / (pooled["n_despues"] + K_SHRINK)
    corr_pooled_tematica = {}
    for u in UMBRALES_N:
        sub = pooled[(pooled["n_antes"] >= u) & (pooled["n_despues"] >= u)]
        r = float(np.corrcoef(sub["s_antes"], sub["s_despues"])[0, 1]) if len(sub) >= 3 else None
        corr_pooled_tematica[f"n>={u}"] = {"n_pares": int(len(sub)), "correlacion": round(r, 4) if r is not None else None}

    # pooled general
    g_list = []
    for i, recambio in enumerate(RECAMBIOS):
        a_desde, a_hasta = ventanas[i]
        d_desde, d_hasta = ventanas[i + 1]
        antes = v[(v["fecha"] >= a_desde) & (v["fecha"] < a_hasta)]
        despues = v[(v["fecha"] >= d_desde) & (v["fecha"] < d_hasta)]
        g_a = antes.groupby("legislador_id")["af"].agg(n_antes="size", share_antes="mean")
        g_d = despues.groupby("legislador_id")["af"].agg(n_despues="size", share_despues="mean")
        g = g_a.join(g_d, how="inner").reset_index()
        g["prior_antes"] = float(antes["af"].mean())
        g["prior_despues"] = float(despues["af"].mean())
        g_list.append(g)
    g_pooled = pd.concat(g_list, ignore_index=True)
    g_pooled["s_antes"] = (g_pooled["n_antes"] * g_pooled["share_antes"] + K_SHRINK * g_pooled["prior_antes"]) / (g_pooled["n_antes"] + K_SHRINK)
    g_pooled["s_despues"] = (g_pooled["n_despues"] * g_pooled["share_despues"] + K_SHRINK * g_pooled["prior_despues"]) / (g_pooled["n_despues"] + K_SHRINK)
    corr_pooled_general = {}
    for u in UMBRALES_N:
        sub = g_pooled[(g_pooled["n_antes"] >= u) & (g_pooled["n_despues"] >= u)]
        r = float(np.corrcoef(sub["s_antes"], sub["s_despues"])[0, 1]) if len(sub) >= 3 else None
        corr_pooled_general[f"n>={u}"] = {"n_pares": int(len(sub)), "correlacion": round(r, 4) if r is not None else None}

    # caso Pichetto (leg:5daaefa4774c) -- spot check, no forma parte del veredicto
    PID_PICHETTO = "leg:5daaefa4774c"
    pichetto = pooled[pooled["legislador_id"] == PID_PICHETTO].to_dict("records")

    reporte = {
        "k_shrink": K_SHRINK, "umbrales_n": UMBRALES_N, "recambios": RECAMBIOS,
        "por_recambio": resultados,
        "POOLED_temática": corr_pooled_tematica,
        "POOLED_general_contraste": corr_pooled_general,
        "brecha_pooled_n5": (
            round(corr_pooled_tematica["n>=5"]["correlacion"] - corr_pooled_general["n>=5"]["correlacion"], 4)
            if corr_pooled_tematica["n>=5"]["correlacion"] is not None
            and corr_pooled_general["n>=5"]["correlacion"] is not None else None),
        "caso_pichetto_leg_5daaefa4774c": pichetto,
    }

    # precedencia explícita (el prompt da 3 filas que se pueden superponer si se
    # leen como elif sueltos): 1) el umbral duro >=0.50 y brecha>=0.15 primero;
    # 2) el piso <0.30 es un DESCALIFICADOR propio, se chequea ANTES que la zona
    # gris (si la temática ya es baja en términos absolutos, la brecha con la
    # general no la salva); 3) lo que queda en el medio es zona gris.
    corr_n5 = corr_pooled_tematica["n>=5"]["correlacion"]
    brecha = reporte["brecha_pooled_n5"]
    if corr_n5 is not None and corr_n5 >= 0.50 and brecha is not None and brecha >= 0.15:
        veredicto = "EL_GUARD_CORTA_INFORMACION_VALIDA"
    elif corr_n5 is not None and corr_n5 < 0.30:
        veredicto = "EL_GUARD_TIENE_RAZON_TAMBIEN_PARA_EL_TEMA"
    else:
        veredicto = "ZONA_GRIS"
    reporte["VEREDICTO_FASE_1"] = veredicto

    print("\n" + json.dumps(reporte, ensure_ascii=False, indent=1))
    print(f"\n=== VEREDICTO FASE 1: {veredicto} ===")
    print(f"correlación temática (n>=5, pooled): {corr_n5}")
    print(f"correlación general  (n>=5, pooled): {corr_pooled_general['n>=5']['correlacion']}")
    print(f"brecha: {brecha}")

    out = REPO / "evaluacion/baseline/outputs/medir_estabilidad_record_por_tema_2026-09-17.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
