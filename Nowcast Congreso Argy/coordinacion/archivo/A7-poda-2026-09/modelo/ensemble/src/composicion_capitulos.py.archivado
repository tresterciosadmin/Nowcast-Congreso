# -*- coding: utf-8 -*-
"""modelo/ensemble — COMPOSICIÓN de P(proyecto) a partir de sus CAPÍTULOS,
por SIMULACIÓN con shock compartido (FASE 2, `coordinacion/PROMPT-MULTITEMA-V2.md`;
insumos de B1/B2, `coordinacion/DECISIONES/0023-...md`).

PROBLEMA QUE RESUELVE
----------------------
Una ley ómnibus (Ley Bases es el caso de manual) no es una ley "multitema": son
VARIAS leyes, cada una probablemente mono-tema, encuadernadas juntas por
capítulo. El error que ADR-0024 midió (y que costó tres intentos fallidos) fue
tratar de mezclar temas a nivel de TODA la ley. Este módulo no mezcla nada: le
da a CADA capítulo su propia simulación, con su propia postura de bloque
(condicionada a SU tema dominante), y compone los resultados.

**"La P del proyecto" no es un evento: son varios.** No se puede promediar ni
multiplicar las P de los capítulos:
  - Promediar ignora que un capítulo que se cae no es "medio proyecto perdido":
    depende de cuántos artículos tiene y si el resto sobrevive.
  - Multiplicar SUPONE INDEPENDENCIA entre capítulos, y ya sabemos que es falsa:
    si el bloque que sostenía el capítulo laboral se da vuelta, arrastra al
    económico — es la misma sobredispersión que η_j (ADR-0025, §III.A.3) mide
    en 37-41× sobre el voto individual.

**La forma correcta: simular con el MISMO shock η_j compartido ENTRE
CAPÍTULOS**, no sólo entre legisladores de una misma votación. Consecuencia
práctica (ver `agregador.simular_votacion(devolver_crudo=True)`): dos llamadas
con el MISMO `seed`/`n_sims`/`epsilon0`/`tau` dibujan el MISMO `eta_j` —es el
PRIMER draw del generador, antes de cualquier muestreo de roster— así que sus
resultados por-simulación quedan alineados sim a sim sin tener que simular los
capítulos juntos en una sola llamada.

Con eso, CUATRO números —no uno—, todos derivados de las MISMAS simulaciones:

    P_k          = P(capítulo k pasa)
    P_todo       = P(TODOS los capítulos pasan)      -> "la ley se sanciona igual"
    P_algo       = P(AL MENOS UN capítulo pasa)       -> "se sanciona algo"
    E[superviv.] = E[fracción de ARTÍCULOS que sobreviven]  (ponderado por a_k)

Y la revancha de `peor_tema` (ADR-0024: la peor de las tres reglas probadas a
nivel proyecto, con un estimador sesgado): acá se mide DIRECTO de la
simulación, sin estimar ningún mínimo de shares ruidosos —
`P_todo` vs `min_k P_k` sale de contar, no de una fórmula que puede sesgarse.

APAGADO POR DISEÑO, NO POR BANDERA: este módulo no se engancha a
`nowcast_puertas.nowcast()`. Cambia la SEMÁNTICA del número publicado
(P(algo)/P(sobrevive) no son "P(aprobación)" de siempre) — activar cualquiera
de los dos números en producción es una decisión de Franco (ver el prompt: "Los
dos números publicados... van apagados hasta que Franco los revise").

CONSUME: nada del contrato B1/B2 directamente (ese cableado -qué capítulo tiene
qué postura de bloque- lo arma el LLAMADOR con `votacion_por_articulo.parquet` +
`variables/bloque/proyectar_postura` + `datos/padron`; ver
`evaluacion/baseline` o los tests para un ejemplo de armado). Este módulo sólo
simula y compone, dado el roster por capítulo ya resuelto.

4 directivas: errores específicos, parsing defensivo, logging estructurado.
(No hay I/O de red.)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

logger = logging.getLogger("ensemble.composicion_capitulos")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agregador_institucional" / "src"))
from agregador import simular_votacion  # noqa: E402


def simular_capitulos(capitulos: dict, n_sims: int = 2000, seed: int = 0,
                      epsilon0: float = 0.0, tau: float = 0.0,
                      reparto_desvio: float = 1.0) -> dict:
    """Simula cada capítulo con el MISMO shock η_j y compone P_k/P_todo/P_algo/
    E[supervivencia].

    `capitulos`: {capitulo_id: {"lineas": array[str], "desvios": array[float],
    "tipo_mayoria": str, "camara": str, "n_articulos": int (>=1, default 1 si
    falta)}}. Todos los capítulos de un mismo proyecto DEBEN compartir cámara
    (la ley se vota completa en una cámara antes de pasar a la otra) — no se
    valida el roster fila a fila (cada capítulo puede tener su propio roster:
    el padrón point-in-time es el mismo, pero la LÍNEA de cada bloque puede
    variar por capítulo, que es justamente el punto).

    epsilon0/tau: OBLIGATORIO que al menos uno sea > 0. Sin shock compartido,
    simular capítulo por capítulo y componer es exactamente el error de
    independencia que este módulo existe para evitar — mejor romper temprano
    y claro que devolver un número que parece válido y no lo es.
    """
    if not capitulos:
        raise ValueError("simular_capitulos necesita al menos un capítulo")
    if epsilon0 <= 0.0 and tau <= 0.0:
        raise ValueError(
            "simular_capitulos necesita epsilon0>0 o tau>0 (el shock compartido, "
            "ADR-0025): sin eso los capítulos se simulan INDEPENDIENTES entre sí, "
            "que es el supuesto falso que este módulo existe para no repetir "
            "(ver Nivel 0 de FORMULA-COMPLETA.md y la sobredispersión 37-41x medida "
            "sobre el voto individual)")

    ids = list(capitulos.keys())
    aprob_por_cap: dict[str, np.ndarray] = {}
    n_articulos: dict[str, float] = {}
    p_puntual: dict[str, float] = {}
    for cid in ids:
        c = capitulos[cid]
        for campo in ("lineas", "desvios", "tipo_mayoria", "camara"):
            if campo not in c:
                raise KeyError(f"capítulo {cid!r} sin {campo!r}")
        r = simular_votacion(c["lineas"], c["desvios"], c["tipo_mayoria"], c["camara"],
                             n_sims=n_sims, seed=seed, epsilon0=epsilon0, tau=tau,
                             reparto_desvio=reparto_desvio, devolver_crudo=True)
        aprob_por_cap[cid] = r["aprob_por_sim"]
        p_puntual[cid] = r["p_aprobacion"]
        na = c.get("n_articulos", 1)
        if na is None or na <= 0:
            logger.warning("capítulo %s sin n_articulos válido (%s); uso 1", cid, na)
            na = 1
        n_articulos[cid] = float(na)

    M = np.vstack([aprob_por_cap[k] for k in ids])         # n_capitulos x n_sims
    p_todo = M.all(axis=0)
    p_algo = M.any(axis=0)
    pesos = np.array([n_articulos[k] for k in ids], dtype=float)
    frac_superviv = (M.astype(float) * pesos[:, None]).sum(axis=0) / pesos.sum()

    min_p_k = min(p_puntual.values())
    p_todo_medio = float(p_todo.mean())
    return {
        "capitulos": ids,
        "n_sims": int(n_sims), "seed": int(seed),
        "epsilon0": float(epsilon0), "tau": float(tau),
        "P_por_capitulo": p_puntual,
        "P_todo": p_todo_medio,
        "P_algo": float(p_algo.mean()),
        "E_supervivencia": float(frac_superviv.mean()),
        "min_P_k": float(min_p_k),
        # la revancha de peor_tema (ADR-0024, medida directo de la simulación,
        # no de un estimador sesgado): cuánto se acerca P_todo al mínimo -- 1.0
        # significa "el proyecto se cae exactamente cuando se cae su capítulo
        # más resistido" (correlación perfecta entre capítulos); 0.0 sería
        # independencia total (P_todo == producto, mucho menor que el mínimo).
        "cercania_a_peor_tema": (float(p_todo_medio / min_p_k) if min_p_k > 0 else None),
    }
