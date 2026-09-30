# -*- coding: utf-8 -*-
"""Piloto sustantivo — plausibilidad a nivel TÍTULO (camino 1 del addendum de
`validar_piloto_capitulos.py`, ADR-0029).

POR QUÉ NIVEL TÍTULO Y NO CAPÍTULO
------------------------------------
`validar_piloto_capitulos.py` midió que el resultado real por CAPÍTULO sólo
existe para Ley Bases (el título del acta declara título+capítulo en sólo 1
proyecto de los 160 con votación en particular en Diputados). El TÍTULO sí
se declara en 9 proyectos. Este script usa esa granularidad: agrupa los
capítulos clasificados de cada título (`tema_por_capitulo.parquet`, fuente
PDF de la Orden del Día) y los combina en UN roster por título — no compone
capítulos por separado (eso es `composicion_capitulos`, para cuando el
resultado real SÍ baja a capítulo) — usa la MISMA maquinaria ya construida y
validada en FASE 0/FASE 1 para "varios temas, un solo evento":

  - `bloque.proyectar_postura(temas=[(area, confianza), ...],
    combinar_temas="ponderada_logit")` — la postura de CADA BLOQUE combina en
    LOGIT los temas de los capítulos del título, ponderada por la confianza
    de cada clasificación (ADR-0028, FASE 0 — ya probado, no se reinventa).
  - `nowcast_puertas.alineacion_individual_por_area(areas_objetivo=[(area,
    confianza), ...])` — el registro histórico DEL LEGISLADOR (RECORD_POR_TEMA,
    ADR-0026) hace la misma combinación a nivel individuo.

El título queda representado por UN roster (líneas + desvíos), simulado con
`agregador.simular_votacion` normal (no hace falta el shock η_j COMPARTIDO
de `composicion_capitulos`: acá no se componen varios eventos correlacionados
en una sola corrida, cada título es su propia simulación independiente,
comparada contra su propio resultado real).

Fuente del resultado real: `votacion_por_articulo.py::extraer_titulo_capitulo`
(el propio título del acta), agrupando por `titulo_num` SOLO (ignora
`capitulo_num`: acá no se necesita, el título "pasa" si NINGÚN tramo suyo, de
NINGUNA fecha, dio NEGATIVO). `fecha_corte` walk-forward = la fecha MÁS
TEMPRANA de los tramos de ese título, menos 5 días (evita leakage aunque el
título se haya terminado de votar en una ronda posterior).

Universo: intersección entre (a) proyectos/títulos con `titulo_num` propio
en el acta y (b) proyectos/títulos con al menos un capítulo clasificado en
`tema_por_capitulo.parquet` — 25 pares (proyecto, título) en 5 proyectos
(incluye Ley Bases, agregado a nivel título en vez de capítulo: más N que
los 3 capítulos de `validar_leybases_por_capitulos.py`).

NO TOCA EL REPO: sólo lee y simula. Imprime el reporte y lo guarda en JSON.

    python evaluacion/baseline/src/validar_piloto_titulos.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("validar_piloto_titulos")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO, CANONICA_CLEAN  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "agregador_institucional" / "src"))

CAMARA = "diputados"
MARGEN_WALKFORWARD_DIAS = 5


def construir_roster_titulo(temas_pesos: list[tuple[str, float]], votos, cond, fecha: str):
    from bloque import proyectar_postura
    from ensemble import roster_nominal
    from nowcast_puertas import (alineacion_individual, alineacion_individual_por_area,
                                 armar_roster, RECORD_POR_TEMA)

    bloques = proyectar_postura(votos, fecha, CAMARA, temas=temas_pesos,
                                combinar_temas="ponderada_logit", cond_por_acta=cond)
    _, _, det = roster_nominal(CAMARA, fecha, bloques)
    ind = alineacion_individual(votos, {}, None, hasta=fecha)
    if RECORD_POR_TEMA:
        ind = alineacion_individual_por_area(votos, cond, {}, None, temas_pesos, ind, hasta=fecha)
    lineas, desvios, presentes, perfiles = armar_roster(CAMARA, bloques, ind, det, None)
    return lineas, desvios


def resultado_real_por_titulo(v: pd.DataFrame, proyecto_id: str) -> dict:
    """{titulo_num: (paso_bool, n_tramos, fecha_mas_temprana)} — agrupa SOLO por
    título (ignora capítulo, ignora ronda): un título "pasa" si NINGUNO de sus
    tramos, en NINGUNA fecha, dio NEGATIVO."""
    r = v[(v["proyecto_id"] == proyecto_id) & (v["camara"] == CAMARA) &
         (v["es_particular"]) & (v["titulo_num"].notna())]
    out = {}
    for tit, g in r.groupby("titulo_num"):
        out[tit] = (bool((g["resultado_clase"] != "NEGATIVO").all()), int(len(g)),
                   str(g["fecha"].min()))
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    from bloque import cargar as cargar_bloque, cargar_tema_por_acta
    from nowcast_puertas import EPSILON0, TAU, INCERTIDUMBRE_LEGISLADOR, RECORD_POR_TEMA
    from agregador import simular_votacion

    logger.info("RECORD_POR_TEMA=%s INCERTIDUMBRE_LEGISLADOR=%s (eps0=%.3f tau=%.2f)",
               RECORD_POR_TEMA, INCERTIDUMBRE_LEGISLADOR, EPSILON0, TAU)

    temas = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_capitulo.parquet")
    v = pd.read_parquet(REPO / "datos/expedientes/data/clean/votacion_por_articulo.parquet")
    votos = cargar_bloque(CANONICA_CLEAN)
    cond = cargar_tema_por_acta()

    eps = EPSILON0 if EPSILON0 > 0 else 0.035
    tau = TAU if TAU > 0 else 1.19

    proyectos = sorted(set(v.loc[v["titulo_num"].notna(), "proyecto_id"].unique()) &
                       set(temas["proyecto_id"].unique()))
    logger.info("proyectos con titulo_num en acta Y algún capítulo clasificado: %s", proyectos)

    filas = []
    saltados = []
    for proyecto_id in proyectos:
        reales = resultado_real_por_titulo(v, proyecto_id)
        temas_p = temas[temas["proyecto_id"] == proyecto_id]

        for titulo_num, (paso_real, n_tramos, fecha_min) in sorted(reales.items()):
            caps_titulo = temas_p[temas_p["titulo_num"] == titulo_num]
            if caps_titulo.empty:
                continue  # título real sin ningún capítulo clasificado: no armable
            temas_pesos = [(r.tema_area, float(r.confianza) if r.confianza else 1.0)
                          for r in caps_titulo.itertuples()]
            fecha_corte = str((pd.Timestamp(fecha_min) -
                              pd.Timedelta(days=MARGEN_WALKFORWARD_DIAS)).date())
            try:
                lineas, desvios = construir_roster_titulo(temas_pesos, votos, cond, fecha_corte)
                r_sim = simular_votacion(lineas, desvios, "SIMPLE", CAMARA,
                                        n_sims=3000, seed=0, epsilon0=eps, tau=tau)
            except (ValueError, KeyError) as e:
                logger.warning("%s T%s (temas=%s) no se pudo armar/simular: %s",
                               proyecto_id, titulo_num, temas_pesos, e)
                saltados.append({"proyecto_id": proyecto_id, "titulo": titulo_num,
                                 "motivo": str(e)})
                continue

            filas.append({
                "proyecto_id": proyecto_id, "titulo": titulo_num,
                "n_capitulos_clasificados": len(caps_titulo),
                "temas": ";".join(f"{a}:{p:.2f}" for a, p in temas_pesos),
                "n_tramos_reales": n_tramos, "paso_real": paso_real,
                "P_titulo_simulado": round(r_sim["p_aprobacion"], 4),
            })

    if not filas:
        raise RuntimeError("no se pudo armar ningún título en todo el piloto")

    tabla = pd.DataFrame(filas).sort_values(["proyecto_id", "P_titulo_simulado"])
    cayeron = tabla[~tabla["paso_real"]]
    pasaron = tabla[tabla["paso_real"]]
    corr = tabla["P_titulo_simulado"].corr(tabla["paso_real"].astype(float))

    reporte = {
        "margen_walkforward_dias": MARGEN_WALKFORWARD_DIAS,
        "flags": {"RECORD_POR_TEMA": RECORD_POR_TEMA,
                 "INCERTIDUMBRE_LEGISLADOR": INCERTIDUMBRE_LEGISLADOR,
                 "epsilon0": eps, "tau": tau},
        "n_proyectos": len(proyectos),
        "n_titulos_evaluados": len(tabla),
        "n_titulos_saltados": len(saltados), "titulos_saltados": saltados,
        "n_cayeron_realidad": int(len(cayeron)), "n_pasaron_realidad": int(len(pasaron)),
        "P_titulo_medio_CAYERON_en_la_realidad": (
            round(float(cayeron["P_titulo_simulado"].mean()), 4) if len(cayeron) else None),
        "P_titulo_medio_PASARON_en_la_realidad": (
            round(float(pasaron["P_titulo_simulado"].mean()), 4) if len(pasaron) else None),
        "correlacion_P_titulo_vs_paso_real": (round(float(corr), 4) if pd.notna(corr) else None),
        "tabla_por_titulo": tabla.to_dict("records"),
    }

    print("\n" + tabla.to_string(index=False))
    print(f"\nn_titulos={len(tabla)}  cayeron={len(cayeron)}  pasaron={len(pasaron)}")
    print(f"P_titulo medio -- cayeron: {reporte['P_titulo_medio_CAYERON_en_la_realidad']}  "
         f"| pasaron: {reporte['P_titulo_medio_PASARON_en_la_realidad']}")
    print(f"correlación P_titulo vs paso_real: {reporte['correlacion_P_titulo_vs_paso_real']}")
    if saltados:
        print(f"\ntítulos saltados ({len(saltados)}): {saltados}")

    out = REPO / "evaluacion/baseline/outputs/validacion_piloto_titulos_2026-09-16.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
