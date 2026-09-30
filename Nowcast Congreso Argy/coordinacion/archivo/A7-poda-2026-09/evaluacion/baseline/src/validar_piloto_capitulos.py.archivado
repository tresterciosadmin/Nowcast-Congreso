# -*- coding: utf-8 -*-
"""Piloto sustantivo de `composicion_capitulos` sobre 20 proyectos REALES.

Por qué existe (a diferencia de `validar_leybases_por_capitulos.py`): Ley
Bases resultó un mal caso de prueba por una razón AJENA a la clasificación —
es uno de sólo 3 proyectos (de 160 con votación en particular en Diputados)
votados en DOS rondas separadas, así que sólo 3 de sus 63 capítulos eran
comparables contra la ronda 1 real (n=3, insuficiente).

⚠️ INTENTO 1 (fallido, honesto): la primera versión de este piloto eligió los
20 proyectos de una sola ronda con MÁS TRAMOS según el PDF de la Orden del Día
(`capitulos_nombre.parquet`) y clasificó 160 capítulos ahí. Al correr la
validación, 0/20 tenían resultado real por capítulo utilizable: el
`titulo_num`/`capitulo_num` que permite agrupar el resultado real NO sale del
PDF — sale del propio TÍTULO DEL ACTA (`votacion_por_articulo.py`,
`extraer_titulo_capitulo`), que sólo lo declara explícitamente
("TITULO VIII. CAPITULO VIII...") en 9 proyectos de TODOS los que tienen
votación particular en Diputados. La riqueza de capítulos del PDF no implica
riqueza de resultado real verificable — son dos extracciones independientes.
Los 160 capítulos clasificados NO se perdieron (quedan en
`tema_por_capitulo.parquet` como insumo futuro de `composicion_capitulos` en
producción) pero no sirven para ESTA validación puntual.

INTENTO 2 (éste): universo correcto = proyectos con `titulo_num` propio en
`votacion_por_articulo.parquet` (9 en total; 7 de una sola ronda). De esos, 3
ya tenían sus capítulos 100% clasificados (HCDN289082: 26 tramos,
HCDN287440: 2, HCDN101088: 1) y a un cuarto (HCDN285290) le faltaban 4
capítulos, clasificados ahora (costo trivial). Los otros 3 (HCDN293348,
HCDN293445, HCDN096679) no tienen ni el PDF de capítulos parseado — se
excluyen (no se justifica el trabajo de scrapear+parsear PDF por 1-4 tramos
cada uno; queda anotado como expansión posible).

QUÉ HACE
--------
Por cada proyecto del piloto, arma el roster por capítulo (igual método que
`validar_leybases_por_capitulos.py`: `bloque.proyectar_postura(tema=área)` +
`nowcast_puertas.armar_roster`, walk-forward con `fecha_corte` = fecha real
de la votación menos 5 días), simula con `composicion_capitulos.simular_capitulos`
(shock η_j compartido, pero DENTRO de cada proyecto — no se comparte el shock
ENTRE proyectos distintos, son eventos separados) y compara el `P_k` de cada
capítulo contra si ese capítulo tuvo o no algún tramo NEGATIVO en la realidad.

NO ES SUFICIENTE PARA VALIDAR LA HIPÓTESIS DE FORMA ESTRICTA (el objetivo acá
es cobertura n>>3 y una primera mirada a la DISCRIMINACIÓN del mecanismo, no
un backtest con banda de confianza) pero, a diferencia de Ley Bases, cada
capítulo clasificado SÍ tiene un resultado real comparable.

NO TOCA EL REPO: sólo lee y simula. Imprime el reporte y lo guarda en JSON.

    python evaluacion/baseline/src/validar_piloto_capitulos.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("validar_piloto_capitulos")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO, CANONICA_CLEAN  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "agregador_institucional" / "src"))

CAMARA = "diputados"
MARGEN_WALKFORWARD_DIAS = 5

# Proyectos con titulo_num/capitulo_num declarado en el propio título del
# acta (votacion_por_articulo.py::extraer_titulo_capitulo) Y de una sola
# ronda de votación particular en Diputados — el único universo donde el
# resultado real por capítulo es directamente verificable (ver docstring).
PROYECTOS_PILOTO = ["HCDN289082", "HCDN287440", "HCDN101088", "HCDN285290"]


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


def resultado_real_por_capitulo(v: pd.DataFrame, proyecto_id: str) -> tuple[dict, str]:
    """{(titulo_num, capitulo_num): (paso_bool, n_tramos)} — proyectos de UNA
    SOLA fecha de votación en particular, así que no hace falta filtrar por
    ronda: TODO tramo real de ese proyecto es comparable. Devuelve también
    la fecha real (para el walk-forward)."""
    r = v[(v["proyecto_id"] == proyecto_id) & (v["camara"] == CAMARA) & (v["es_particular"])]
    fechas = r["fecha"].unique()
    if len(fechas) != 1:
        raise ValueError(f"{proyecto_id}: se esperaba 1 sola fecha de votación particular, "
                         f"hay {len(fechas)}: {sorted(fechas)}")
    fecha_real = str(fechas[0])
    out = {}
    for (tit, cap), g in r.groupby(["titulo_num", "capitulo_num"]):
        out[(tit, cap)] = (bool((g["resultado_clase"] != "NEGATIVO").all()), int(len(g)))
    return out, fecha_real


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    from bloque import cargar as cargar_bloque, cargar_tema_por_acta
    from nowcast_puertas import EPSILON0, TAU, INCERTIDUMBRE_LEGISLADOR, RECORD_POR_TEMA
    from composicion_capitulos import simular_capitulos

    logger.info("RECORD_POR_TEMA=%s INCERTIDUMBRE_LEGISLADOR=%s (eps0=%.3f tau=%.2f)",
               RECORD_POR_TEMA, INCERTIDUMBRE_LEGISLADOR, EPSILON0, TAU)

    temas = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_capitulo.parquet")
    v = pd.read_parquet(REPO / "datos/expedientes/data/clean/votacion_por_articulo.parquet")
    votos = cargar_bloque(CANONICA_CLEAN)
    cond = cargar_tema_por_acta()

    eps = EPSILON0 if EPSILON0 > 0 else 0.035
    tau = TAU if TAU > 0 else 1.19

    filas = []
    saltados = []
    for proyecto_id in PROYECTOS_PILOTO:
        try:
            reales, fecha_real = resultado_real_por_capitulo(v, proyecto_id)
        except ValueError as e:
            logger.warning("%s: %s (se excluye)", proyecto_id, e)
            saltados.append({"proyecto_id": proyecto_id, "motivo": str(e)})
            continue

        fecha_corte = str((pd.Timestamp(fecha_real) -
                           pd.Timedelta(days=MARGEN_WALKFORWARD_DIAS)).date())

        temas_p = temas[temas["proyecto_id"] == proyecto_id]
        temas_map = {(r.titulo_num, r.capitulo_num): r.tema_area for r in temas_p.itertuples()}

        capitulos_sim = {}
        claves_por_etiqueta = {}
        for clave, area in temas_map.items():
            if clave not in reales:
                continue
            try:
                lineas, desvios = construir_roster_capitulo(area, votos, cond, fecha_corte)
            except (ValueError, KeyError) as e:
                logger.warning("%s T%sC%s (tema=%s) no se pudo armar: %s",
                               proyecto_id, *clave, area, e)
                continue
            n_tramos = reales[clave][1]
            etiqueta = f"T{clave[0]}C{clave[1]}"
            capitulos_sim[etiqueta] = {"lineas": lineas, "desvios": desvios,
                                       "tipo_mayoria": "SIMPLE", "camara": CAMARA,
                                       "n_articulos": n_tramos}
            claves_por_etiqueta[etiqueta] = clave

        if not capitulos_sim:
            logger.warning("%s: ningún capítulo armable (tema sin clasificar o roster vacío); "
                           "se excluye", proyecto_id)
            saltados.append({"proyecto_id": proyecto_id, "motivo": "ningún capítulo armable"})
            continue

        r_sim = simular_capitulos(capitulos_sim, n_sims=2000, seed=0, epsilon0=eps, tau=tau)

        for etq, clave in claves_por_etiqueta.items():
            paso_real, n_tramos = reales[clave]
            filas.append({
                "proyecto_id": proyecto_id, "titulo": clave[0], "capitulo": clave[1],
                "tema": temas_map[clave], "n_tramos_reales": n_tramos,
                "paso_real": paso_real, "P_k_simulado": round(r_sim["P_por_capitulo"][etq], 4),
            })
        logger.info("%s: %d capítulos simulados, P_todo=%.3f min_P_k=%.3f",
                   proyecto_id, len(capitulos_sim), r_sim["P_todo"], r_sim["min_P_k"])

    if not filas:
        raise RuntimeError("no se pudo armar ningún capítulo en todo el piloto")

    tabla = pd.DataFrame(filas).sort_values(["proyecto_id", "P_k_simulado"])
    cayeron = tabla[~tabla["paso_real"]]
    pasaron = tabla[tabla["paso_real"]]

    corr = tabla["P_k_simulado"].corr(tabla["paso_real"].astype(float))

    reporte = {
        "margen_walkforward_dias": MARGEN_WALKFORWARD_DIAS,
        "flags": {"RECORD_POR_TEMA": RECORD_POR_TEMA,
                 "INCERTIDUMBRE_LEGISLADOR": INCERTIDUMBRE_LEGISLADOR,
                 "epsilon0": eps, "tau": tau},
        "n_proyectos_piloto": len(PROYECTOS_PILOTO),
        "n_proyectos_excluidos": len(saltados),
        "proyectos_excluidos": saltados,
        "n_capitulos_evaluados": len(tabla),
        "n_cayeron_realidad": int(len(cayeron)), "n_pasaron_realidad": int(len(pasaron)),
        "P_k_medio_capitulos_que_CAYERON_en_la_realidad": (
            round(float(cayeron["P_k_simulado"].mean()), 4) if len(cayeron) else None),
        "P_k_medio_capitulos_que_PASARON_en_la_realidad": (
            round(float(pasaron["P_k_simulado"].mean()), 4) if len(pasaron) else None),
        "correlacion_P_k_vs_paso_real": (round(float(corr), 4) if pd.notna(corr) else None),
        "tabla_por_capitulo": tabla.to_dict("records"),
    }

    print("\n" + tabla.to_string(index=False))
    print(f"\nn_capitulos={len(tabla)}  cayeron={len(cayeron)}  pasaron={len(pasaron)}")
    print(f"P_k medio -- cayeron: {reporte['P_k_medio_capitulos_que_CAYERON_en_la_realidad']}  "
         f"| pasaron: {reporte['P_k_medio_capitulos_que_PASARON_en_la_realidad']}")
    print(f"correlación P_k vs paso_real: {reporte['correlacion_P_k_vs_paso_real']}")
    if saltados:
        print(f"\nproyectos excluidos ({len(saltados)}): {[s['proyecto_id'] for s in saltados]}")

    out = REPO / "evaluacion/baseline/outputs/validacion_piloto_capitulos_2026-09-16.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
