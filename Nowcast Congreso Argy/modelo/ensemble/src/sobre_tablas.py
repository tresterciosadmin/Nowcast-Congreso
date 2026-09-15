# -*- coding: utf-8 -*-
"""El sobre tablas como VOTACION, no como mezcla de probabilidades (ADR-0015,
S:III.A.1 y S:III.A.5 de FORMULA-COMPLETA.md).

    P_c^total = C_c * P_c + (1 - C_c) * P^tablas_c * P_c
    logit(P_i^tablas) = logit(P_i^bloque) + theta_camara

24,4% de los proyectos de ley votados en recinto NO TIENEN DICTAMEN EN NINGUN
LADO (medido 03-09 sobre 1.496 proyectos de Diputados). La unica via que les
queda es el articulo reglamentario del tratamiento "sobre tablas", que exige
el voto AFIRMATIVO de dos tercios de los presentes: una votacion mas, con su
propio umbral -- no un descuento gradual sobre la via normal.

THETA, ESTIMADO 03-09 (`estimar_theta_sobre_tablas.py`, salida en
`outputs/theta_sobre_tablas.json`): 186 actas de sobre tablas contra 1.420
actas normales del mismo mes y camara, offset = logit(P_i^bloque) SIN el
atajo al record propio. Dos hallazgos que corrigieron la hipotesis original:

  1. Acompanar sobre tablas es MAS caro, no mas barato -- theta>0 (la
     hipotesis original) queda refutada por los datos: la tasa afirmativa cae
     de 86,1% a 64,5% sobre tablas, y el motor sin theta predice practicamente
     lo mismo en los dos regimenes (0,802 vs 0,816). Theta llena ese hueco.
  2. Es un fenomeno de DIPUTADOS. theta_D=-2,047 (p<0,0001). En el SENADO no
     se distingue de cero (p=0,157) y por eso entra en 0 -- no con el
     coeficiente crudo (-0,262) -- ver `_theta()`.

FRANCO PROPUSO que el legislador sin dictamen decide con su RECORD PROPIO por
tema, desacoplado del bloque -- "falto de informacion". Medido (26-08): al
reves. Con el UNICO record que existe hoy (el general, no el tematico), la
linea de BLOQUE acierta 95,4% contra 45,0% del record propio (Brier 0,435,
peor que decir 0,50 y listo). El legislador sin dictamen no cae en si mismo:
cae en su bloque, mas fuerte. La propuesta de Franco sigue SIN TESTEAR en su
forma correcta -- el record POR TEMA (rho, S:III.B.3) no tiene tabla todavia
-- asi que P_i^bloque es lo unico que hay, y es lo que la medicion respalda.

EL GATE (C_c) ES UNA APROXIMACION, no la regla reglamentaria completa
(dictamen de mayoria en TODAS las comisiones giradas, o un plenario de
todas). Construir eso exige cruzar los giros por proyecto (`datos/
expedientes`) contra que comisiones efectivamente dictaminaron, y ese cruce
no esta armado. Lo que SI existe es el estado de tres valores que ya produce
`puerta_a.caracter_de`: `con_caracter` / `sin_dictamen` / `sin_dato`. Se usa
`sin_dictamen` CONFIRMADO como la senal de que la via normal no esta
disponible. `sin_dato` (no se sabe si hay dictamen) sigue tomando la via
normal, SIN cambio de comportamiento -- es la eleccion conservadora bajo
incertidumbre, igual que en el resto de `puerta_a`.

APAGADA POR DEFECTO: `SOBRE_TABLAS=1` para prenderla (o `activo=True` en
`ajustar_via`). A diferencia de `beta_dictamen`, esto TODAVIA no tiene
backtest walk-forward propio -- correrlo antes de proponer prenderla es la
misma disciplina que salvo a `beta_dictamen` de quedar con el termino de
caracter que no generalizaba.
"""
from __future__ import annotations

import json
import logging
import math
import os
import sys
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("sobre_tablas")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

# APAGADA POR DEFECTO -- ver el docstring del modulo: falta el backtest walk-forward
# que S:III.A.5 todavia no tiene. `SOBRE_TABLAS=0` para forzarla apagada.
SOBRE_TABLAS = os.environ.get("SOBRE_TABLAS", "0") != "0"

SALIDA = RAIZ / "modelo" / "ensemble" / "outputs" / "theta_sobre_tablas.json"

# theta_S no se distingue de cero (p=0,157, S:III.A.5): entra en 0, no en el
# coeficiente crudo. Es una DECISION registrada en la formula, no una lectura
# automatica del p-valor -- por eso el corte vive aca y no se generaliza a
# "cualquier coeficiente no significativo se apaga solo".
P_MINIMO_SIGNIFICATIVO = 0.05


@lru_cache(maxsize=1)
def _theta() -> dict:
    """{camara: theta} de `C_por_camara`. {} si falta el archivo o no ajusto."""
    if not SALIDA.exists():
        logger.warning("no encontre %s: corre estimar_theta_sobre_tablas.py. "
                       "El sobre tablas queda sin corrimiento (theta=0).", SALIDA)
        return {}
    d = json.loads(SALIDA.read_text(encoding="utf-8"))
    por_camara = d.get("C_por_camara", {})
    theta: dict[str, float] = {}
    for cam, res in por_camara.items():
        if "error" in res or not res.get("coef") or "tab" not in res["coef"]:
            continue
        p = res.get("p", {}).get("tab", 1.0)
        theta[cam] = float(res["coef"]["tab"]) if p < P_MINIMO_SIGNIFICATIVO else 0.0
    return theta


def theta_de(camara: str) -> float:
    """El corrimiento en logit para `camara`. 0.0 si no hay estimacion o no es
    significativo (ver `_theta`)."""
    return float(_theta().get(str(camara).strip().lower(), 0.0))


def es_admisible(caracter: dict) -> bool:
    """C_c: True si la via normal (con dictamen) sigue disponible para esta camara.

    Aproximacion (ver docstring del modulo): False SOLO si `puerta_a.caracter_de`
    devolvio `sin_dictamen` CONFIRMADO. `sin_dato` y `con_caracter` son admisibles.
    """
    return caracter.get("estado") != "sin_dictamen"


def _logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(float(p), eps), 1 - eps)
    return math.log(p / (1 - p))


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def p_afirma_tablas(p_afirma: float, camara: str) -> float:
    """P(este legislador vote AFIRMATIVO) si el proyecto se trata sobre tablas.

    Corre la MISMA P_i^bloque que ya calculo `armar_roster` (con beta_dictamen
    aplicado si esa bandera tambien esta prendida) desplazada por theta en logit
    -- S:III.A.5. Sin estimacion o camara sin theta significativo, devuelve
    `p_afirma` sin tocar.
    """
    th = theta_de(camara)
    if th == 0.0:
        return float(p_afirma)
    return _sigmoide(_logit(p_afirma) + th)
