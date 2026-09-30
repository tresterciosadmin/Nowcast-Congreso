# -*- coding: utf-8 -*-
"""PRUEBA 1 de `coordinacion/PROMPT-DECIDIR-CAPITULOS.md` — pivotes por
capítulo: ¿la lista de bisagras (legisladores cerca de 50/50) cambia algo
útil cuando se condiciona por el TEMA DE CADA CAPÍTULO, en vez de por el
tema del proyecto entero?

POR QUÉ ESTO NO HEREDA EL PROBLEMA DE VALIDACIÓN DE ADR-0029
--------------------------------------------------------------
Las tres validaciones anteriores (ADR-0029 y sus cuatro addenda) intentaron
probar que P_k (la probabilidad AGREGADA del capítulo) está calibrada — eso
choca con un techo estructural: sólo Ley Bases tiene resultado real a nivel
capítulo (n=3 en ronda 1). Acá la pregunta es otra: los pivotes salen de
P_i (la probabilidad INDIVIDUAL de cada legislador), y P_i condicionada por
tema SÍ está validada — es `alineacion_individual_por_area` (ADR-0026,
FASE 1: -11,06% de Brier en el censo completo, positivo en todos los
cortes, EN PRODUCCIÓN). Lo no validado es la COMPOSICIÓN a P_k; la lista de
pivotes no la usa.

CERO GASTO DE API: todo lo que hace falta ya está clasificado (Ley Bases,
63/63 capítulos, `tema_por_capitulo.parquet`). NO SE TOCA EL MOTOR: este
script sólo LEE y reusa las funciones de producción
(`nowcast_puertas.alineacion_individual_por_area`/`armar_roster`,
`bloque.proyectar_postura`, `ensemble.roster_nominal`) — no reimplementa el
roster.

QUÉ CONSTRUYE
--------------
Sobre Ley Bases (HCDN272347), roster real de Diputados walk-forward a
2024-02-01 (antes de la ronda 1, 2024-02-06):

- **Lista A**: P_i con las áreas del PROYECTO ENTERO
  (`nowcast_puertas._resolver_multietiqueta`, lo mismo que usaría
  `nowcast()` en producción hoy).
- **Lista B**: para cada uno de los 63 capítulos clasificados, P_i
  condicionada SÓLO al área de ESE capítulo (mismo mecanismo, área distinta
  — un solo grado de libertad respecto de Lista A: el resto del roster
  —postura de bloque incondicional, detalle nominal— es IDÉNTICO).

PRUEBA 1.3 usa un dato que ADR-0029 nunca miró: existen DOS Órdenes del Día
de Ley Bases en el repo — `141-1.pdf` (OD 1, publicada 2024-01-26, el texto
ORIGINAL antes de la ronda 1) y `142-7.pdf` (OD 7, publicada 2024-04-26, el
texto RECORTADO antes de la ronda 2, 2024-04-30). Comparar sus capítulos da,
GRATIS, qué capítulos SOBREVIVIERON y cuáles se CAYERON del proyecto entre
rondas — 43 cortados + 16 sobrevivientes, n=59, mucho más rico que el n=3 de
ronda 1.

    python evaluacion/baseline/src/prueba1_pivotes_por_capitulo.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("prueba1_pivotes_por_capitulo")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO, CANONICA_CLEAN  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))

PROYECTO_ID = "HCDN272347"
CAMARA = "diputados"
FECHA_CORTE = "2024-02-01"
PIVOTE_LO, PIVOTE_HI = 0.35, 0.65

OD_ORIGINAL = "141-1.pdf"   # OD 1, publicada 2024-01-26 -- texto antes de ronda 1
OD_RECORTADA = "142-7.pdf"  # OD 7, publicada 2024-04-26 -- texto antes de ronda 2


def n_area_por_legislador(votos, cond, area: str, hasta: str) -> dict:
    """{(camara, legislador_id): n_area REAL} -- mismo filtro/join que usa
    `alineacion_individual_por_area` internamente (ADR-0026), expuesto acá
    sólo para DIAGNÓSTICO (PRUEBA 1.1): cuántos votos propios tiene cada
    legislador en esta área específica, antes del encogimiento."""
    from nowcast_puertas import _alineacion_base, _areas_de_todas_ids

    d = _alineacion_base(votos, {}, None, hasta=hasta)
    if d is None or cond is None or cond.empty:
        return {}
    tpa_col = cond.columns[0]
    tpa = cond[[tpa_col, "todas_ids"]].rename(columns={tpa_col: "acta_id"}) \
        if "todas_ids" in cond.columns else None
    if tpa is None:
        return {}
    tpa = tpa.drop_duplicates("acta_id")
    tpa["areas"] = tpa["todas_ids"].map(_areas_de_todas_ids)
    d = d.merge(tpa[["acta_id", "areas"]], on="acta_id", how="left")
    mask = d["areas"].map(lambda xs: area in xs if isinstance(xs, list) else False)
    g = d[mask].groupby(["camara", "legislador_id"]).size()
    return {idx: int(n) for idx, n in g.items()}


def pivotes(p_i: dict) -> set:
    return {lid for lid, p in p_i.items() if PIVOTE_LO <= p <= PIVOTE_HI}


def construir_listas():
    from bloque import cargar as cargar_bloque, cargar_tema_por_acta, proyectar_postura
    from ensemble import roster_nominal
    from nowcast_puertas import (alineacion_individual, alineacion_individual_por_area,
                                 armar_roster, _resolver_multietiqueta)

    votos = cargar_bloque(CANONICA_CLEAN)
    cond = cargar_tema_por_acta()

    # Postura de BLOQUE incondicional (tema=None): el ÚNICO grado de libertad
    # entre Lista A y cada capítulo de Lista B es el RECORD del legislador
    # (alineacion_individual_por_area) -- TEMA_AUTO sigue apagado (ADR-0024/
    # 0028, negativo a nivel bloque), no se reabre acá.
    bloques = proyectar_postura(votos, FECHA_CORTE, CAMARA, cond_por_acta=cond)
    _, _, det = roster_nominal(CAMARA, FECHA_CORTE, bloques)
    ind_general = alineacion_individual(votos, {}, None, hasta=FECHA_CORTE)

    areas_A = _resolver_multietiqueta(PROYECTO_ID)
    logger.info("Lista A -- multietiqueta del proyecto entero: %s", areas_A)
    ind_A = alineacion_individual_por_area(votos, cond, {}, None, areas_A, ind_general,
                                           hasta=FECHA_CORTE)
    _, _, _, perfiles_A = armar_roster(CAMARA, bloques, ind_A, det, None)
    p_i_A = {p["legislador_id"]: p["p_afirma_si_vota"] for p in perfiles_A}

    temas = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_capitulo.parquet")
    temas_lb = temas[temas["proyecto_id"] == PROYECTO_ID]

    listas_B = {}
    n_area_B = {}
    for r in temas_lb.itertuples():
        clave = (r.titulo_num, r.capitulo_num)
        area = str(r.tema_area).upper()
        conf = float(r.confianza) if r.confianza else 1.0
        ind_c = alineacion_individual_por_area(votos, cond, {}, None, [(area, conf)],
                                               ind_general, hasta=FECHA_CORTE)
        _, _, _, perfiles_c = armar_roster(CAMARA, bloques, ind_c, det, None)
        p_i_c = {p["legislador_id"]: p["p_afirma_si_vota"] for p in perfiles_c}
        n_area_c = n_area_por_legislador(votos, cond, area, FECHA_CORTE)
        listas_B[clave] = {"area": area, "confianza": conf, "p_i": p_i_c}
        n_area_B[clave] = {lid: n for (cam, lid), n in n_area_c.items() if cam == CAMARA}

    return p_i_A, listas_B, n_area_B


def prueba_1_1(listas_B: dict, n_area_B: dict) -> dict:
    """¿La heterogeneidad entre capítulos es REAL (datos condicionados
    propios) o es el encogimiento cayendo en silencio al récord general?"""
    ns = []
    con_dato_real = 0
    total = 0
    for clave, info in listas_B.items():
        n_area = n_area_B.get(clave, {})
        for lid in info["p_i"]:
            total += 1
            n = n_area.get(lid, 0)
            ns.append(n)
            if n >= 1:
                con_dato_real += 1
    frac = con_dato_real / total if total else 0.0
    serie = pd.Series(ns)
    return {
        "fraccion_con_n_area_real_ge_1": round(frac, 4),
        "total_pares_legislador_capitulo": total,
        "distribucion_n_area": {
            "media": round(float(serie.mean()), 3), "mediana": float(serie.median()),
            "p25": float(serie.quantile(0.25)), "p75": float(serie.quantile(0.75)),
            "max": int(serie.max()), "pct_cero": round(float((serie == 0).mean()), 4),
        },
        "UMBRAL": 0.50, "PASA": frac >= 0.50,
    }


def prueba_1_2(p_i_A: dict, listas_B: dict) -> dict:
    piv_A = pivotes(p_i_A)
    piv_por_capitulo = {clave: pivotes(info["p_i"]) for clave, info in listas_B.items()}
    union_B = set().union(*piv_por_capitulo.values()) if piv_por_capitulo else set()
    union_AB = piv_A | union_B
    interseccion_AB = piv_A & union_B
    jaccard = (len(interseccion_AB) / len(union_AB)) if union_AB else None

    # "específicos": pivote de capítulo que la lista A NO marca en absoluto,
    # o cuyo estatus de pivote VARÍA entre capítulos (pivote en unos, no en
    # otros) -- en cualquiera de los dos casos, Lista A sola no lo hubiera
    # mostrado.
    n_capitulos = len(piv_por_capitulo)
    especificos = set()
    variacion = {}
    for lid in union_AB:
        capitulos_pivote = {c for c, s in piv_por_capitulo.items() if lid in s}
        variacion[lid] = len(capitulos_pivote)
        if lid not in piv_A or (0 < len(capitulos_pivote) < n_capitulos):
            especificos.add(lid)
    especificos_estricto = union_B - piv_A  # sólo "no está en la lista única"

    return {
        "n_pivotes_lista_A": len(piv_A),
        "n_capitulos_con_lista_B": n_capitulos,
        "n_pivotes_union_B": len(union_B),
        "jaccard_A_vs_union_B": round(jaccard, 4) if jaccard is not None else None,
        "especificos_amplio_pct": round(len(especificos) / len(union_AB), 4) if union_AB else None,
        "especificos_estricto_pct_sobre_union_B": (
            round(len(especificos_estricto) / len(union_B), 4) if union_B else None),
        "n_especificos_amplio": len(especificos), "n_union_AB": len(union_AB),
        "n_especificos_estricto_sobre_union_B": len(especificos_estricto),
        "UMBRAL": 0.30,
        "PASA": (len(especificos_estricto) / len(union_B) >= 0.30) if union_B else False,
    }


def prueba_1_3(listas_B: dict) -> dict:
    cn = pd.read_parquet(REPO / "datos/expedientes/data/clean/capitulos_nombre.parquet")
    mask = cn["proyecto_ids"].str.contains(PROYECTO_ID, na=False)
    sub = cn[mask]
    s_orig = set(zip(sub[sub["archivo"] == OD_ORIGINAL]["titulo_num"],
                     sub[sub["archivo"] == OD_ORIGINAL]["capitulo_num"]))
    s_recort = set(zip(sub[sub["archivo"] == OD_RECORTADA]["titulo_num"],
                       sub[sub["archivo"] == OD_RECORTADA]["capitulo_num"]))
    if not s_orig or not s_recort:
        return {"dato_existe": False,
               "motivo": f"falta {OD_ORIGINAL if not s_orig else OD_RECORTADA} en capitulos_nombre.parquet"}

    cortados = s_orig - s_recort
    sobrevivieron = s_orig & s_recort

    filas = []
    for clave in cortados | sobrevivieron:
        info = listas_B.get(clave)
        if info is None:
            continue
        p_i = list(info["p_i"].values())
        n_piv = len(pivotes(info["p_i"]))
        filas.append({
            "titulo": clave[0], "capitulo": clave[1], "area": info["area"],
            "cortado": clave in cortados,
            "p_i_medio": round(sum(p_i) / len(p_i), 4) if p_i else None,
            "n_legisladores": len(p_i),
            "n_pivotes": n_piv, "frac_pivotes": round(n_piv / len(p_i), 4) if p_i else None,
        })
    tabla = pd.DataFrame(filas)
    if tabla.empty:
        return {"dato_existe": True, "n_cortados": len(cortados),
               "n_sobrevivieron": len(sobrevivieron), "n_clasificados_en_comparacion": 0}

    g_cortado = tabla[tabla["cortado"]]
    g_sobrevive = tabla[~tabla["cortado"]]
    corr_pi = tabla["p_i_medio"].corr(tabla["cortado"].astype(float))
    corr_pivotes = tabla["frac_pivotes"].corr(tabla["cortado"].astype(float))

    return {
        "dato_existe": True,
        "fuente": f"{OD_ORIGINAL} (original, OD1 26-01-2024) vs {OD_RECORTADA} "
                  f"(recortada, OD7 26-04-2024)",
        "n_cortados_total": len(cortados), "n_sobrevivieron_total": len(sobrevivieron),
        "n_clasificados_en_comparacion": len(tabla),
        "n_cortados_clasificados": int(g_cortado.shape[0]),
        "n_sobrevivieron_clasificados": int(g_sobrevive.shape[0]),
        "P_i_medio__cortados": round(float(g_cortado["p_i_medio"].mean()), 4),
        "P_i_medio__sobrevivieron": round(float(g_sobrevive["p_i_medio"].mean()), 4),
        "frac_pivotes_medio__cortados": round(float(g_cortado["frac_pivotes"].mean()), 4),
        "frac_pivotes_medio__sobrevivieron": round(float(g_sobrevive["frac_pivotes"].mean()), 4),
        "correlacion_P_i_medio_vs_cortado": round(float(corr_pi), 4) if pd.notna(corr_pi) else None,
        "correlacion_frac_pivotes_vs_cortado": (
            round(float(corr_pivotes), 4) if pd.notna(corr_pivotes) else None),
        "tabla": tabla.sort_values("p_i_medio").to_dict("records"),
    }


def main() -> int:
    logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    logger.setLevel(logging.INFO)

    logger.info("construyendo Lista A y Lista B (roster real, walk-forward a %s)...", FECHA_CORTE)
    p_i_A, listas_B, n_area_B = construir_listas()
    logger.info("Lista A: %d legisladores. Lista B: %d capítulos.", len(p_i_A), len(listas_B))

    r11 = prueba_1_1(listas_B, n_area_B)
    r12 = prueba_1_2(p_i_A, listas_B)
    r13 = None
    if r11["PASA"]:
        r13 = prueba_1_3(listas_B)
    else:
        logger.warning("PRUEBA 1.1 no pasa el umbral -- igual se corren 1.2/1.3 para el "
                       "reporte, pero el veredicto de la PRUEBA 1 ya está decidido.")
        r13 = prueba_1_3(listas_B)  # se corre igual, para el reporte completo

    reporte = {
        "proyecto_id": PROYECTO_ID, "fecha_corte": FECHA_CORTE,
        "rango_pivote": [PIVOTE_LO, PIVOTE_HI],
        "1.1_heterogeneidad_real": r11,
        "1.2_listas_distintas": r12,
        "1.3_acierta_capitulos_cortados": r13,
        "veredicto_prueba_1": bool(r11["PASA"] and r12["PASA"]),
    }

    print("\n=== PRUEBA 1.1 — heterogeneidad real vs. fallback ===")
    print(json.dumps({k: v for k, v in r11.items() if k != "distribucion_n_area"}, indent=1,
                     ensure_ascii=False))
    print("distribución n_area:", r11["distribucion_n_area"])

    print("\n=== PRUEBA 1.2 — ¿las listas son distintas? ===")
    print(json.dumps({k: v for k, v in r12.items() if k != "tabla"}, indent=1, ensure_ascii=False))

    print("\n=== PRUEBA 1.3 — ¿señala los capítulos que se cayeron? ===")
    if r13.get("dato_existe"):
        print(json.dumps({k: v for k, v in r13.items() if k != "tabla"}, indent=1,
                         ensure_ascii=False))
    else:
        print(json.dumps(r13, indent=1, ensure_ascii=False))

    print(f"\n=== VEREDICTO PRUEBA 1: {'PASA' if reporte['veredicto_prueba_1'] else 'FALLA'} ===")

    out = REPO / "evaluacion/baseline/outputs/prueba1_pivotes_por_capitulo_2026-09-17.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
