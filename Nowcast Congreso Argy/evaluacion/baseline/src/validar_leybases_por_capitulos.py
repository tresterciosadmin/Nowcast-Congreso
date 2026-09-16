# -*- coding: utf-8 -*-
"""Plausibilidad de `composicion_capitulos` sobre un caso REAL: Ley Bases.

Pregunta de Franco: "¿podemos usar lo que tenemos hasta ahora para recorrer
el modelo y sacar conclusiones?" — sí, sobre Ley Bases: sus 63 capítulos
reales (clave `(titulo_num, capitulo_num)`, ADR-0029 addendum) están
clasificados de punta a punta.

⚠️ La CLAVE de todo este script es `(titulo_num, capitulo_num)`, NO
`capitulo_num` solo — la primera versión (16-09, antes del fix) agrupaba mal
y mezclaba capítulos de partes distintas de la ley (ver ADR-0029).

QUÉ HACE
--------
Para cada capítulo de Ley Bases (con su tema real, `tema_por_capitulo.parquet`),
arma el roster de Diputados de la MISMA forma que `nowcast_puertas.nowcast()`
—`bloque.proyectar_postura(tema=área)` + `ensemble.roster_nominal` +
`nowcast_puertas.armar_roster` (con `RECORD_POR_TEMA` si está prendido)—, a una
fecha ANTERIOR a la primera ronda de votación (walk-forward, sin leakage:
2024-02-01, cinco días antes del 06-02-2024). Simula cada capítulo con
`composicion_capitulos.simular_capitulos` (shock compartido η_j) y compara
`P_k` contra lo que REALMENTE pasó en la ronda 1 (¿el capítulo tuvo algún
tramo NEGATIVO?).

NO ES UNA VALIDACIÓN ESTADÍSTICA (con la clave corregida, sólo 3 de los 63
capítulos de Ley Bases tuvieron tramo en la RONDA 1 — la mayoría de la
votación particular pasó en la ronda 2, después del retiro y recorte) — es
exactamente lo que se pidió: ¿el mecanismo da resultados PLAUSIBLES sobre el
caso real que motivó todo esto? Con n=3 no se puede concluir nada con
confianza; sirve para ver si el mecanismo es COHERENTE (nada roto, nada
absurdo), no para validar la hipótesis. Esa validación real necesita más
casos — ver "Lo que este script NO responde" en el reporte de ADR-0029.

NO TOCA EL REPO: sólo lee y simula. Imprime el reporte y lo guarda en JSON.

    python evaluacion/baseline/src/validar_leybases_por_capitulos.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("validar_leybases_por_capitulos")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO, CANONICA_CLEAN  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "agregador_institucional" / "src"))

PROYECTO_ID = "HCDN272347"  # Ley Bases
CAMARA = "diputados"
FECHA_CORTE = "2024-02-01"  # walk-forward: 5 días ANTES de la ronda 1 (2024-02-06)
FECHA_RONDA1 = "2024-02-06"


def construir_roster_capitulo(area: str, votos, cond, fecha: str):
    from bloque import proyectar_postura
    from ensemble import roster_nominal
    from nowcast_puertas import (alineacion_individual, alineacion_individual_por_area,
                                 armar_roster, RECORD_POR_TEMA)

    bloques = proyectar_postura(votos, fecha, CAMARA, tema=area, cond_por_acta=cond)
    _, _, det = roster_nominal(CAMARA, fecha, bloques)
    ind = alineacion_individual(votos, {}, None, hasta=fecha)
    if RECORD_POR_TEMA:
        ind = alineacion_individual_por_area(votos, cond, {}, None, [(area, 1.0)], ind, hasta=fecha)
    lineas, desvios, presentes, perfiles = armar_roster(CAMARA, bloques, ind, det, None)
    return lineas, desvios


def resultado_real_por_capitulo(v: pd.DataFrame) -> dict:
    """{(titulo_num, capitulo_num): (paso_bool, n_tramos)} de la RONDA 1 real
    (2024-02-06): un capítulo "pasa" si NINGUNO de sus tramos dio NEGATIVO.
    Agrupa por el PAR, no por capitulo_num solo (ver el aviso del módulo)."""
    r1 = v[(v["proyecto_id"] == PROYECTO_ID) & (v["camara"] == CAMARA) &
          (v["fecha"] == FECHA_RONDA1) & (v["es_particular"])]
    out = {}
    for (tit, cap), g in r1.groupby(["titulo_num", "capitulo_num"]):
        out[(tit, cap)] = (bool((g["resultado_clase"] != "NEGATIVO").all()), int(len(g)))
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    from bloque import cargar as cargar_bloque, cargar_tema_por_acta
    from nowcast_puertas import EPSILON0, TAU, INCERTIDUMBRE_LEGISLADOR, RECORD_POR_TEMA
    from composicion_capitulos import simular_capitulos

    logger.info("RECORD_POR_TEMA=%s INCERTIDUMBRE_LEGISLADOR=%s (eps0=%.3f tau=%.2f)",
               RECORD_POR_TEMA, INCERTIDUMBRE_LEGISLADOR, EPSILON0, TAU)

    temas = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_capitulo.parquet")
    temas_lb_df = temas[temas["proyecto_id"] == PROYECTO_ID]
    temas_lb = {(r.titulo_num, r.capitulo_num): r.tema_area for r in temas_lb_df.itertuples()}
    logger.info("capítulos de Ley Bases con tema clasificado: %d -> %s",
               len(temas_lb), temas_lb)

    v = pd.read_parquet(REPO / "datos/expedientes/data/clean/votacion_por_articulo.parquet")
    reales = resultado_real_por_capitulo(v)
    logger.info("resultado REAL ronda 1 (2024-02-06), %d capítulos con tramo: %s",
               len(reales), reales)

    votos = cargar_bloque(CANONICA_CLEAN)
    cond = cargar_tema_por_acta()

    capitulos_sim = {}
    for clave, area in temas_lb.items():
        if clave not in reales:
            logger.info("Título %s / Capítulo %s clasificado pero sin tramo en ronda 1 "
                        "(probablemente sólo tuvo tramos en ronda 2): se excluye", *clave)
            continue
        try:
            lineas, desvios = construir_roster_capitulo(area, votos, cond, FECHA_CORTE)
        except (ValueError, KeyError) as e:
            logger.warning("Título %s / Capítulo %s (tema=%s) no se pudo armar: %s",
                           *clave, area, e)
            continue
        n_tramos = reales[clave][1]
        etiqueta = f"T{clave[0]}C{clave[1]}"
        capitulos_sim[etiqueta] = {"lineas": lineas, "desvios": desvios,
                                   "tipo_mayoria": "SIMPLE", "camara": CAMARA,
                                   "n_articulos": n_tramos, "_clave": clave}

    if not capitulos_sim:
        raise RuntimeError("no se pudo armar ningún capítulo: revisar datos/temas")

    claves_por_etiqueta = {k: v["_clave"] for k, v in capitulos_sim.items()}
    for c in capitulos_sim.values():
        del c["_clave"]

    r = simular_capitulos(capitulos_sim, n_sims=3000, seed=0,
                          epsilon0=EPSILON0 if EPSILON0 > 0 else 0.035,
                          tau=TAU if TAU > 0 else 1.19)

    filas = []
    for etq in sorted(capitulos_sim.keys()):
        clave = claves_por_etiqueta[etq]
        paso_real, n_tramos = reales[clave]
        filas.append({
            "titulo": clave[0], "capitulo": clave[1], "tema": temas_lb[clave],
            "n_tramos_reales": n_tramos,
            "paso_real_ronda1": paso_real,
            "P_k_simulado": round(r["P_por_capitulo"][etq], 4),
        })
    tabla = pd.DataFrame(filas).sort_values("P_k_simulado")

    cayeron = tabla[~tabla["paso_real_ronda1"]]
    pasaron = tabla[tabla["paso_real_ronda1"]]
    reporte = {
        "fecha_corte_walkforward": FECHA_CORTE,
        "flags": {"RECORD_POR_TEMA": RECORD_POR_TEMA,
                 "INCERTIDUMBRE_LEGISLADOR": INCERTIDUMBRE_LEGISLADOR,
                 "epsilon0": EPSILON0, "tau": TAU},
        "P_todo": r["P_todo"], "P_algo": r["P_algo"],
        "E_supervivencia": r["E_supervivencia"],
        "min_P_k": r["min_P_k"], "cercania_a_peor_tema": r["cercania_a_peor_tema"],
        "tabla_por_capitulo": tabla.to_dict("records"),
        "P_k_medio_capitulos_que_CAYERON_en_la_realidad": (
            round(float(cayeron["P_k_simulado"].mean()), 4) if len(cayeron) else None),
        "P_k_medio_capitulos_que_PASARON_en_la_realidad": (
            round(float(pasaron["P_k_simulado"].mean()), 4) if len(pasaron) else None),
        "n_capitulos_evaluados": len(tabla),
        "n_cayeron_realidad": int(len(cayeron)), "n_pasaron_realidad": int(len(pasaron)),
    }

    print("\n" + tabla.to_string(index=False))
    print(f"\nP_todo={r['P_todo']:.4f}  P_algo={r['P_algo']:.4f}  "
         f"E[supervivencia]={r['E_supervivencia']:.4f}  min_P_k={r['min_P_k']:.4f}")
    print(f"P_k medio -- cayeron en la realidad: {reporte['P_k_medio_capitulos_que_CAYERON_en_la_realidad']}  "
         f"| pasaron en la realidad: {reporte['P_k_medio_capitulos_que_PASARON_en_la_realidad']}")

    out = REPO / "evaluacion/baseline/outputs/validacion_leybases_capitulos_2026-09-16.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
