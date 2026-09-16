# -*- coding: utf-8 -*-
"""El nowcast por PUERTAS — el punto de entrada único, hacia adelante.

QUÉ RESPONDE
    Entra un proyecto —uno real que acaba de presentarse, o uno hipotético— y esto
    dice, CON LA CONFIGURACIÓN ACTUAL DE LAS DOS CÁMARAS, qué chance tiene de
    aprobarse, y sobre todo **quién es quién adentro**: quién acompaña, quién no y
    sobre quién hay incógnita. Esa última lista es la que sirve para negociar.

    P(aprobación) = [A observada] · P(B | carácter de origen)
                  · [C observada] · P(D | carácter de la revisora)

    A y C **no son probabilidades**: son el carácter observado del dictamen en cada
    cámara. Colapsan a 1 cuando el hecho ocurrió y, cuando no hay dato —el caso
    normal de un proyecto recién presentado— su condicionante se encoge a 0 y queda
    la estimación sin condicionar. Contrato: `modelo/ensemble/PUERTA-D.md`.

EL NÚMERO ES CONDICIONAL Y HAY QUE DECIRLO
    Al sacar `p_llega_recinto` —que era la mortandad en el cajón, o sea agenda— este
    número deja de responder «¿va a ser ley?». Responde **«si las dos cámaras lo
    votan, ¿lo aprueban?»**. La salida trae `condicional_a` y `pasos[].estado` para
    que la interfaz lo diga, en vez de esconderlo en un README. Un proyecto con
    dictamen leído en las dos cámaras y otro sin ningún dictamen NO pueden mostrarse
    igual sólo porque los dos devuelven un número.

QUÉ REUSA (no reimplementa nada)
    roster point-in-time + escalera de desvío  -> ensemble.roster_nominal
    simulación con las guardas de confianza    -> ensemble.simular_con_guardas
    postura de bloque por tema/origen          -> bloque.proyectar_postura
    carácter del dictamen y su condicionante   -> puerta_a
    vía sobre tablas si no hay dictamen        -> sobre_tablas (bandera apagada, S:III.A.5)
    cámara revisora y su votación              -> puerta_d
    foto completa de la cámara a una fecha     -> datos/padron/padron_vigente

Módulo: modelo/ensemble · creado 2026-08-22 (Tarea 1 — una sola formulación)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("nowcast_puertas")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import CANONICA_CLEAN, PROYECTO_ORIGEN_POR_ACTA, RAIZ  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

# EL TABLERO SALE DEL MISMO CÁLCULO QUE EL NÚMERO. Esto no es un detalle: la primera
# versión clasificaba a cada legislador por su récord individual mientras B y D salían
# del simulador sobre línea+desvío — dos modelos distintos para lo mismo, y en la
# primera corrida real Diputados mostraba "acompañan 130" contra un umbral de 129 y al
# lado un 99%. Un número que su propia tabla no sostiene es peor que ningún número.
# Ahora la postura se lee de lo que ENTRA a la simulación: la línea de su bloque y su
# desvío individual.
#
# BISAGRA: desvío >= 0,20. La banda no es inventada — es una de las que el análisis del
# ICG ya usa (0,10 / 0,20 / 0,30), donde se midió que el clima mueve a los de desvío
# alto y no al núcleo duro. Es parámetro, no constante escondida.
DESVIO_BISAGRA = 0.20
# INCÓGNITA por INCERTIDUMBRE, no sólo por desvío: alguien con P(afirmativo) de 0,55 es
# una incógnita aunque su bloque sea disciplinado — y ese caso sólo se ve desde que el
# número del bloque dejó de redondearse a SÍ/NO. Se marca cuando P cae en [0,35; 0,65].
INCERTIDUMBRE_INCOGNITA = 0.35
# Por debajo de esta frecuencia de voto, la persona no se cuenta como votante: preside,
# está de licencia o directamente no aparece. Antes entraba como un voto entero.
PRESENCIA_MINIMA = 0.15
# El desvío es CAMBIO DE DIRECCIÓN, no ausencia. La ausencia va por `p_presente`.
# Ver a_linea_y_desvio: con el reparto por defecto se inventaban ausencias en masa.
REPARTO_DESVIO = 1.0
# Historia mínima para usar el récord individual antes de caer al promedio del bloque.
#
# ERA 8 HASTA EL 06-09-2026. Bajó a 1 (decisión de Franco) porque el ENCOGIMIENTO lo dejó
# sin trabajo. El umbral existía como única protección contra creerle a un récord de tres
# votos, y era binaria: o le creías entero o lo tirabas. Con Empirical-Bayes esa protección
# es continua — con n=1 el récord queda en 5/6 del share de su bloque, que es exactamente
# lo que el umbral quería conseguir, pero sin el escalón.
#
# Y medido sobre 741.275 votos, el umbral además COSTABA, de forma monótona:
#
#     n>=1   skill 0,1702   rama bloque 0,38%   desde 2023 0,0726
#     n>=8   skill 0,1665   rama bloque 3,00%   desde 2023 0,0616   <- lo que era
#     n>=40  skill 0,1502   rama bloque 13,22%  desde 2023 0,0109
#
# El baseline COMPLETO explica por qué: la rama de bloque tiene skill NEGATIVO (-0,10 sobre
# 19.923 votos). Mandar gente ahí no es un refugio conservador, es empeorarla.
#
# No se borra la constante: `evaluacion/baseline` y los tests la consumen como contrato, y
# con 1 sigue haciendo lo único que hay que hacer — sin NINGÚN voto previo en la era no hay
# récord que encoger, y ése sí cae al bloque.
MIN_HIST_INDIVIDUAL = 1
MIN_HIST_ANTERIOR = 8   # para el A/B; ver §II.5 de FORMULA-COMPLETA.md
# GUARD DE ERA — bandera APAGADA por defecto (URGENTE 9).
#
# El récord individual ya se corta por era, pero con una FECHA FIJA: 2023-12-10. Para
# cualquier nowcast del gobierno vigente eso es exactamente la era correcta, así que
# la bandera NO mueve el número publicado (medido: idéntico al 06-09-2026). Lo que
# arregla es lo de atrás: fechado en 2018 o en 2022, el filtro `fecha >= 2023-12-10`
# combinado con `fecha <= hasta` deja el conjunto VACÍO y los ~478 legisladores caen
# todos a la rama de bloque. Medido el 06-09:
#
#   nowcast al 2026-06-01 (MILEI)     -> 478 legisladores con récord propio
#   nowcast al 2022-06-01 (AF)        ->   0
#   nowcast al 2018-06-01 (MACRI)     ->   0
#   nowcast al 2013-06-01 (KIRCHNER)  ->   0
#
# O sea que el motor **no se puede backtestear fuera de la era vigente**: en cualquier
# fecha anterior mide otra cosa. Avisa por log, que en una corrida de backtest no lo
# lee nadie. Con la bandera prendida, la era se DEDUCE de la fecha del nowcast.
# 06-09-2026: PRENDIDO POR DEFECTO (decisión de Franco). Se apaga con GUARD_ERA=0.
# No mueve el número publicado: para el gobierno vigente la era deducida ES 2023-12-10,
# verificado sobre los 478 legisladores del nowcast al 2026-06-01.
GUARD_ERA = os.environ.get("GUARD_ERA", "1") != "0"
# La fecha fija que se usaba antes (y se sigue usando con la bandera apagada).
ERA_FIJA = "2023-12-10"
# ENCOGER, NO CORTAR (URGENTE 9, ADR-0018). Cortar por era deja a mucha gente con poca
# historia; en vez de tirarla, el récord se encoge hacia el share de su linaje con el
# MISMO Empirical-Bayes y el MISMO k=5 con que `proyectar_postura` encoge el share:
#
#     rec_encogido = (n·rec + k·share_linaje) / (n + k)
#
# Con n grande no cambia nada; con n chico se apoya en el bloque. Medido sobre 741.275
# votos: le gana a cortar en las CINCO eras (skill 0,1680 contra 0,1643).
K_SHRINK_RECORD = 5.0
SHRINK_RECORD = os.environ.get("SHRINK_RECORD", "1") != "0"

# TEMA AUTOMÁTICO (2026-09-15, Parte A de coordinacion/PROMPT-MULTIETIQUETA.md).
#
# Medido el 15-09: `tema` acá abajo es un parámetro CLI MANUAL — nunca se deriva
# de `proyecto_id`. No hay ningún enganche proyecto_id -> tema en la ruta de
# producción, así que la rama de condicionamiento por tema no dispara en NINGUNA
# corrida automatizada de hoy (`REGENERAR.ps1` paso 8 no pasa `--tema`). Sin este
# enganche, cualquier regla de combinación de temas construida en
# `variables/bloque` (union/ponderada) queda huérfana: nadie la llama en vivo.
#
# APAGADA POR DEFECTO. Motivo YA NO es "el dato no existe": desde el 16-09
# `proyecto_taxonomias` tiene 2.655 filas (1.182 proyectos, vía
# `tema_por_proyecto.clasificar_por_titulo` — ⚠️ CORRECCIÓN: sí había
# ANTHROPIC_API_KEY, cargada por `.env`; el chequeo directo de la sesión del
# 15-09 la había pasado por alto). El motivo de que siga apagada ahora es el
# de PASO 2 (ADR-0024): las tres reglas de combinación medidas —union,
# ponderada, peor_tema— empeoran la rama de bloque contra la que se las probó,
# así que `COMBINAR_TEMAS=primaria` (la que NO cambia nada frente al
# comportamiento manual de siempre) es la única combinación sin evidencia en
# contra. Prender `TEMA_AUTO` con `primaria` es seguro (usa sólo el área de
# mayor confianza, igual que pasar `tema=` a mano); prenderlo con cualquier
# otra regla de combinación no tiene evidencia a favor — ver el resumen para
# cowork en `coordinacion/RESUMEN-MULTIETIQUETA-COWORK.md`.
TEMA_AUTO = os.environ.get("TEMA_AUTO", "0") != "0"
# Con qué regla se combinan los temas cuando TEMA_AUTO encuentra multietiqueta.
# 'primaria' (default) usa sólo el área de mayor confianza -> single `tema=`,
# el camino MÁS PARECIDO al comportamiento manual de siempre. 'union'/'ponderada'
# (ver variables/bloque/src/bloque.py::proyectar_postura) necesitan su propia
# validación empírica antes de ser el default.
COMBINAR_TEMAS = os.environ.get("COMBINAR_TEMAS", "primaria")

# INCERTIDUMBRE A NIVEL LEGISLADOR (§III.A.3, ADR-0025). PRENDIDA POR DEFECTO
# desde el 16-09-2026 — decisión de Franco ("Hagamos el cambio"), después de
# que la evidencia (ver ADR-0025) apuntara a favor en los tres frentes donde
# se la puso a prueba y ningún backtest saliera en contra. CAMBIA EL NÚMERO
# PUBLICADO: las bandas se ensanchan y P_c deja de pegarse a 0%/100% en
# proyectos que hoy se ven "seguros". Se puede volver al comportamiento
# anterior con `INCERTIDUMBRE_LEGISLADOR=0` en el entorno.
#
# Reemplaza el clip AGREGADO (`ensemble.P_INCERTIDUMBRE`, que recorta P_c a
# [0,01; 0,99] DESPUÉS de simular — viola la doctrina, ADR-0016 §II.1) por dos
# piezas a nivel LEGISLADOR, ANTES de simular:
#   1. epsilon0: encogimiento AFÍN de cada P_i hacia [epsilon0, 1-epsilon0] —
#      preserva el orden entre legisladores, un clip no.
#   2. tau * eta_j: un shock COMPARTIDO por todos los legisladores de cada
#      simulación (eta_j ~ N(0,1) uno por corrida) — es la EXCEPCIÓN 2 del
#      ADR-0016 (shock correlacionado, no corrección al agregado) y es lo único
#      que arregla la sobreconcentración: 257 votos independientes concentran
#      pase lo que pase con los P_i, medido en 38,9x de sobredispersión real
#      contra la que predice independencia (`estimar_epsilon_tau.py`, 03-09).
#
# Los valores por defecto salen de la RE-ESTIMACIÓN del 16-09 (ver ADR-0025):
# no se reusa ciegamente la del 03-09 porque desde el 14-09 beta_dictamen está
# prendido y podría haber reducido la dispersión que tau mide — se re-midió
# ANTES de fijar el valor, no después (el orden que la propia FORMULA-COMPLETA
# pedía respetar). Re-estimado sobre 2.485 actas / 293.655 votos (5x la muestra
# del 03-09): epsilon0_logloss=0,035, tau_mediana=1,190 — CASI IDÉNTICO al
# 1,197 del 03-09 pese al cambio de motor: beta_dictamen no absorbió la
# dispersión que tau mide (esperable: el harness de este script, igual que
# baseline_voto_individual.py, no incluye beta_dictamen en su p_motor).
EPSILON0_DEFAULT = 0.035
TAU_DEFAULT = 1.19
INCERTIDUMBRE_LEGISLADOR = os.environ.get("INCERTIDUMBRE_LEGISLADOR", "1") != "0"
EPSILON0 = float(os.environ.get("EPSILON0", EPSILON0_DEFAULT))
TAU = float(os.environ.get("TAU", TAU_DEFAULT))

# RECORD POR TEMA (FASE 1, PROMPT-MULTITEMA-V2.md, URGENTE 8). PRENDIDA POR
# DEFECTO desde el 16-09-2026 — Franco delegó la activación explícitamente en
# este prompt ("podés prender banderas si el censo completo mejora y queda
# documentado en fórmula + ADR"), y el censo la respalda sin ambigüedad:
# 11,1% menos Brier que el récord general en el subconjunto que toca (votos de
# actas con >=1 área sustantiva), POSITIVO en las dos cámaras (11,6%
# Diputados, 7,7% Senado) y en las 5 eras medidas (5,6% a 12,8%) — a
# diferencia del multitema a nivel BLOQUE (ADR-0024), acá no hay ningún
# subconjunto negativo. Ver ADR-0026 y `evaluacion/baseline/outputs/
# fase1_rec_por_tema_censo.json`. `RECORD_POR_TEMA=0` en el entorno vuelve al
# récord general de siempre.
RECORD_POR_TEMA = os.environ.get("RECORD_POR_TEMA", "1") != "0"


def _resolver_multietiqueta(proyecto_id: Optional[str], db_path=None, expedientes=None):
    """La multietiqueta [(área,confianza),...] de un proyecto, vía
    `tema_por_proyecto.temas_de_proyecto`. [] si no hay proyecto_id o el
    proyecto no tiene taxonomías cargadas todavía. SIN gate de ninguna
    bandera a propósito: `TEMA_AUTO` (condiciona la POSTURA DE BLOQUE) y
    `RECORD_POR_TEMA` (condiciona el RÉCORD del legislador) son dos
    mecanismos independientes desde el 16-09 (ADR-0026) — uno sigue apagado
    (ADR-0024, negativo a nivel bloque) y el otro prendido (positivo a nivel
    legislador); cada llamador decide si usa esto, no esta función."""
    if not proyecto_id:
        return []
    src = RAIZ / "variables" / "proyecto" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from tema_por_proyecto import temas_de_proyecto  # type: ignore
    kwargs = {}
    if db_path is not None:
        kwargs["db_path"] = db_path
    if expedientes is not None:
        kwargs["expedientes"] = expedientes
    try:
        return temas_de_proyecto(proyecto_id=proyecto_id, **kwargs)
    except (FileNotFoundError, ValueError) as e:
        logger.warning("no pude resolver la multietiqueta de %s (%s)", proyecto_id, e)
        return []


def _tema_auto(proyecto_id: Optional[str], db_path=None, expedientes=None):
    """Si TEMA_AUTO está prendida y hay proyecto_id, resuelve su multietiqueta
    (`_resolver_multietiqueta`). Devuelve (tema, temas, combinar_temas) listo
    para pasarle a `proyectar_postura`. Degrada limpio (None, None, 'primaria')
    si la bandera está apagada, no hay proyecto_id, o el proyecto no tiene
    taxonomías cargadas todavía (el caso normal hoy). `db_path`/`expedientes`
    son sólo para tests: sin pasarlos usa los contratos reales del repo."""
    if not TEMA_AUTO or not proyecto_id:
        return None, None, "primaria"
    asigs = _resolver_multietiqueta(proyecto_id, db_path, expedientes)
    if not asigs:
        return None, None, "primaria"
    if COMBINAR_TEMAS == "primaria":
        return asigs[0][0], None, "primaria"  # área de mayor confianza, como tema= manual
    return None, asigs, COMBINAR_TEMAS


def _bloque():
    src = RAIZ / "variables" / "bloque" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from bloque import (cargar, cargar_tema_por_acta,  # type: ignore
                        proyectar_postura)
    return cargar, proyectar_postura, cargar_tema_por_acta


def era_de(fecha) -> str:
    """Inicio de la era (gobierno) que contiene `fecha`, como 'AAAA-MM-DD'.

    **No se reimplementa el calendario acá.** Sale de `definiciones.py` (ADR-0014), que
    es de donde salen también `variables/bloque` —el corte que hace `proyectar_postura`
    desde el 22-07— y `origen_lider`. Que el récord individual y la postura de bloque
    usen DOS calendarios distintos sería exactamente el bug que esto viene a cerrar; y
    ese cuarto consumidor es el que obligó a unificar las tres copias que había.

    OJO: `variables/proyecto/src/icg_contexto.py::GOBIERNOS` se parece y NO es esto —
    son mandatos presidenciales a resolución mensual (nueve ventanas, arranca en De la
    Rúa, parte CFK en I y II, cierra con el día anterior al recambio). Ver el comentario
    en `definiciones.GOBIERNOS`.
    """
    from definiciones import era_de as _e  # noqa: E402
    return _e(fecha)


def _alineacion_base(votos, origen_map: dict, origen: str | None,
                     era_desde: str | None = None, hasta=None,
                     guard_era: bool | None = None):
    """El filtro de ventana/era/origen que comparten `alineacion_individual` y
    `alineacion_individual_por_area` (FASE 1, PROMPT-MULTITEMA-V2.md) — una
    sola copia, para que los dos "récord del legislador" (general y por área)
    miren exactamente la misma ventana walk-forward. None si queda vacío
    (mismo aviso de siempre)."""
    if era_desde is None:
        guard = GUARD_ERA if guard_era is None else guard_era
        era_desde = era_de(hasta) if (guard and hasta is not None) else ERA_FIJA
    d = votos[votos["fecha"] >= pd.Timestamp(era_desde)].copy()
    # WALK-FORWARD. Sin este corte el récord mira el futuro: medido el 22-08, un
    # nowcast fechado 2024-06-01 usaba el 85% de sus votos de DESPUÉS de esa fecha.
    # `proyectar_postura` ya cortaba bien; esto no, y en el HTML anterior el récord
    # entraba directo al número.
    if hasta is not None:
        d = d[d["fecha"] <= pd.Timestamp(hasta)]
    if origen:
        d["_ori"] = d["acta_id"].map(origen_map)
        d = d[d["_ori"] == origen]
    if d.empty:
        logger.warning("sin votos entre %s y %s para origen=%s: los %d legisladores van "
                       "TODOS al fallback de bloque. Si la fecha del nowcast es anterior "
                       "a la era fija (%s), es el bug de URGENTE 9: probá GUARD_ERA=1.",
                       era_desde, hasta, origen,
                       int(votos["legislador_id"].nunique()), ERA_FIJA)
        return None
    V = d["conducta"].astype(str).str.upper().str[:2]
    d["_af"] = V.eq("AF")
    d["_emitio"] = V.isin(["AF", "NE"])
    return d


def alineacion_individual(votos, origen_map: dict, origen: str | None,
                          era_desde: str | None = None, hasta=None,
                          guard_era: bool | None = None) -> dict:
    """P(afirmativo) de CADA legislador sobre su PROPIO récord.

    Condicionada por el ORIGEN del proyecto cuando se pasa `origen` (el motor que
    llevó el acierto del voto individual de 59% a 76%): no es lo mismo cómo vota
    alguien un proyecto del Ejecutivo que uno de la oposición. Sin `origen`, mira
    todo el período. Ausente y abstención cuentan como NO afirmativo, a propósito:
    para juntar una mayoría, el que no está no suma.

    Levantada de `nowcast_bicameral_html.py` (archivado el 10-09) y parametrizada, para que no
    queden dos copias de la misma regla en el repo.

    Devuelve {(camara, legislador_id): (p_afirmativo, n_votos, presencia)}.
    """
    d = _alineacion_base(votos, origen_map, origen, era_desde, hasta, guard_era)
    if d is None:
        return {}
    g = d.groupby(["camara", "legislador_id"]).agg(
        n=("_af", "size"), n_emit=("_emitio", "sum"),
        n_af=("_af", "sum"), presencia=("_emitio", "mean"))
    # DOS preguntas separadas, no una. Antes se dividía por TODAS las votaciones, así
    # que faltar se leía como votar en contra: el presidente de la Cámara daba 0,01 y
    # el modelo lo mostraba EN CONTRA, cuando de las veces que votó acompañó el 100%.
    #   p_af  = acompañó / las que VOTÓ        -> de qué lado está
    #   presencia = las que votó / todas        -> con qué frecuencia aparece
    out = {}
    for idx, r in g.iterrows():
        n_emit = int(r["n_emit"])
        p_af = float(r["n_af"]) / n_emit if n_emit else 0.5
        out[idx] = (p_af, int(r["n"]), float(r["presencia"]), n_emit)
    return out


_AUX_PREFIX_RECORD = "AUX"


def _areas_de_todas_ids(todas_ids) -> list[str]:
    if not todas_ids or (isinstance(todas_ids, float) and pd.isna(todas_ids)):
        return []
    vistas: list[str] = []
    for i in str(todas_ids).split(";"):
        i = i.strip()
        if not i or i.upper().startswith(_AUX_PREFIX_RECORD):
            continue
        area = i.split(".")[0].upper()
        if area not in vistas:
            vistas.append(area)
    return vistas


def alineacion_individual_por_area(votos, cond_por_acta, origen_map: dict,
                                   origen: str | None, areas_objetivo: list,
                                   ind_general: dict, k_shrink: float = K_SHRINK_RECORD,
                                   era_desde: str | None = None, hasta=None,
                                   guard_era: bool | None = None) -> dict:
    """FASE 1 de PROMPT-MULTITEMA-V2.md (URGENTE 8): el récord del legislador
    CONDICIONADO por el/los tema(s) del proyecto — medido (censo completo,
    `evaluacion/baseline/outputs/fase1_rec_por_tema_censo.json`): 11,1% menos
    Brier que el récord general en el subconjunto que toca, consistente en las
    dos cámaras y en las 5 eras. Mueve el término adonde hay datos: a
    diferencia del multitema a nivel BLOQUE (ADR-0024, negativo en las 3
    reglas probadas), acá el insumo es individual, no un agregado ya chico.

    `areas_objetivo`: [(área, confianza), ...] — la multietiqueta del
    proyecto (mismo formato que `bloque._normalizar_temas_objetivo`).

    Para cada legislador, el récord de CADA área objetivo se calcula sobre la
    MISMA ventana walk-forward que `alineacion_individual` (`_alineacion_base`,
    una sola copia del filtro) y se encoge Empirical-Bayes (mismo k=5 de
    siempre) hacia el récord GENERAL de esa persona —información INDIVIDUAL,
    no el share del bloque: es la doctrina de FASE 1—. Los récords por área ya
    encogidos se combinan EN LOGIT, ponderados por la confianza de cada
    etiqueta (regla IV.2 de FORMULA-COMPLETA.md: nunca promediar en
    probabilidad).

    Devuelve {(camara, legislador_id): (p_afirmativo_combinado, n_votos,
    presencia, n_emit)} — n_votos/presencia/n_emit son los del récord GENERAL
    (`ind_general`), sin cambios: esto sólo cambia QUÉ récord se usa, no
    cuánto se confía en tener uno (un solo grado de libertad, como el brazo de
    control de FASE 0). Un legislador sin ningún voto en NINGUNA área objetivo
    cae a su propio récord general (mismo valor que ya tenía en `ind_general`)."""
    areas_norm = [(str(a).upper(), float(c)) for a, c in areas_objetivo if c and c > 0]
    if not areas_norm:
        return dict(ind_general)
    d = _alineacion_base(votos, origen_map, origen, era_desde, hasta, guard_era)
    if d is None or cond_por_acta is None or cond_por_acta.empty:
        return dict(ind_general)
    tpa_col = cond_por_acta.columns[0]
    tpa = cond_por_acta[[tpa_col, "todas_ids"]].rename(columns={tpa_col: "acta_id"}) \
        if "todas_ids" in cond_por_acta.columns else None
    if tpa is None:
        return dict(ind_general)
    tpa = tpa.drop_duplicates("acta_id")
    tpa["areas"] = tpa["todas_ids"].map(_areas_de_todas_ids)
    d = d.merge(tpa[["acta_id", "areas"]], on="acta_id", how="left")
    objetivo = {a for a, _ in areas_norm}
    d["areas_match"] = d["areas"].map(
        lambda xs: [a for a in (xs or []) if a in objetivo] if isinstance(xs, list) else [])
    dx = d[d["areas_match"].map(len) > 0].explode("areas_match").rename(
        columns={"areas_match": "area"})
    if dx.empty:
        return dict(ind_general)
    g = dx.groupby(["camara", "legislador_id", "area"]).agg(
        n_area=("_af", "size"), n_af_area=("_af", "sum"))
    por_area: dict = {}
    for (camara, lid, area), r in g.iterrows():
        por_area.setdefault((camara, lid), {})[area] = (float(r["n_af_area"]) / float(r["n_area"]),
                                                         int(r["n_area"]))

    out = dict(ind_general)
    for (camara, lid), areas_leg in por_area.items():
        base = ind_general.get((camara, lid))
        if base is None:
            continue
        p_general, n_tot, presencia, n_emit = base
        shares, pesos = [], []
        for area, peso in areas_norm:
            if area in areas_leg:
                s_area, n_area = areas_leg[area]
                s_encogido = (n_area * s_area + k_shrink * p_general) / (n_area + k_shrink)
            else:
                s_encogido = p_general
            shares.append(s_encogido)
            pesos.append(peso)
        num, den = 0.0, 0.0
        for s, w in zip(shares, pesos):
            p = float(min(max(s, 1e-9), 1.0 - 1e-9))
            num += w * np.log(p / (1.0 - p))
            den += w
        p_combinado = float(1.0 / (1.0 + np.exp(-(num / den)))) if den > 0 else p_general
        out[(camara, lid)] = (p_combinado, n_tot, presencia, n_emit)
    return out


def perfil_legislador(share_linaje: float, desvio: float, record=None,
                      n_emitidos: int = 0, presencia: float = 1.0,
                      min_hist: int = None, shrink: bool | None = None) -> dict:
    """Cómo se espera que vote esta persona. Devuelve p_afirma_si_vota y p_presente.

    DOS ARREGLOS respecto de cómo se calculaba hasta el 22-08-2026:

    1. **El número del bloque no se redondea a SÍ/NO.** Antes, `linea = AFIRMATIVO si
       share >= 0.5` y después `P = 1 - desvío`. Con eso la Coalición Cívica, que
       acompaña al Ejecutivo el 60,9% de las veces, salía con P = 0,967 — el 39% de
       chance de votar en contra desaparecía. Y Peronismo Federal, con desvío 0,000,
       salía **1,000 exacto**. Se reemplazaba la duda sobre QUÉ VOTA EL BLOQUE por la
       disciplina de sus miembros, que mide otra cosa. Ésa era la razón de que todas
       las votaciones dieran 99%.

       Ahora se componen las dos cosas, que es lo que son:

           P(afirma) = share·(1-d)  +  (1-share)·(d/2)
                       └ el bloque va a favor └ el bloque va en contra
                         y la sigue              y ella se desvía

    2. **Si tiene historial propio suficiente, manda su historial.** Antes la
       DIRECCIÓN salía siempre del linaje y sólo el DESVÍO era individual — y como el
       desvío se mide contra el bloque REAL mientras la línea viene del LINAJE, quien
       está en un bloque chico dentro de un linaje-bolsa se llevaba lo peor de los dos:
       De la Sota (Defendamos Córdoba, dentro de OTRO/PROVINCIAL) tenía desvío 0,000 y
       línea AFIRMATIVO, o sea **P = 1,00**, con un récord propio de 0,17.

    3. **El récord se ENCOGE hacia el bloque** (06-09-2026, ADR-0018). Al cortar el
       récord por era queda mucha gente con poca historia, y un récord de 9 votos no
       vale lo que uno de 900. En vez de elegir entre creerle del todo o tirarlo, se
       encoge con Empirical-Bayes contra el share de su linaje, con el mismo $k=5$ que
       usa `proyectar_postura`. Se apaga con `SHRINK_RECORD=0`.

    `presencia` sale aparte y va como `p_presente` al agregador: faltar no es votar en
    contra, es no votar.
    """
    min_hist = MIN_HIST_INDIVIDUAL if min_hist is None else min_hist
    encoger = SHRINK_RECORD if shrink is None else shrink
    d = float(min(max(desvio, 0.0), 1.0))
    share = float(min(max(share_linaje, 0.0), 1.0))
    if record is not None and n_emitidos >= min_hist:
        p = float(min(max(record, 0.0), 1.0))
        fuente = "record_individual"
        if encoger:
            n = float(max(n_emitidos, 0))
            p = (n * p + K_SHRINK_RECORD * share) / (n + K_SHRINK_RECORD)
            fuente = "record_individual_encogido"
    else:
        p, fuente = share * (1.0 - d) + (1.0 - share) * (d / 2.0), "bloque"
    return {"p_afirma_si_vota": float(p), "p_presente": float(min(max(presencia, 0.0), 1.0)),
            "fuente_direccion": fuente, "share_linaje": share, "desvio": d}


def a_linea_y_desvio(p_afirma: float) -> tuple[str, float]:
    """Traduce una P(afirmativo) al par (línea, desvío) que el agregador reproduce.

    El agregador no toma una probabilidad: toma una línea y un desvío, y arma
    `p(AFIRM) = 1-d` si la línea es AFIRMATIVO, o `d/2` si es NEGATIVO. Se invierte esa
    cuenta para no tener que tocar su código (es contrato de otro módulo).

    **Va con `reparto_desvio=1.0`, y eso no es un detalle.** Con el reparto por defecto
    (0,5) el desvío se parte entre "votar al revés" y "abstenerse", así que al invertir
    una P intermedia se inventaban abstenciones en masa: en la primera corrida el
    umbral de mayoría simple cayó a 112 sobre 257, o sea 45 ausentes por votación. No
    es creíble. Con reparto 1,0 el desvío es **cambio de dirección** y nada más, que es
    lo que significa; la ausencia viaja por su propio canal (`p_presente`). Las dos
    cosas quedan separadas, que es justamente lo que había que arreglar.
    """
    p = float(min(max(p_afirma, 0.0), 1.0))
    if p >= 0.5:
        return "AFIRMATIVO", 1.0 - p
    return "NEGATIVO", p


def _via_sobre_tablas(cond: dict, caracter: dict, camara: str, perfiles: list[dict],
                      presentes, *, n_sims: int, seed: int) -> dict:
    """Aplica la vía sobre tablas (S:III.A.5 de FORMULA-COMPLETA.md) sobre el
    resultado de `condicionar`, cuando la vía normal no está disponible.

    BANDERA APAGADA POR DEFECTO (`SOBRE_TABLAS`, ver `sobre_tablas.py`). Sin
    prender, o con la vía normal disponible (`es_admisible`), devuelve `cond` SIN
    TOCAR — mismo comportamiento que antes de que este módulo existiera.

    Reusa la MISMA simulación que B/D (`ensemble.simular_con_guardas`), sólo con
    el umbral de DOS TERCIOS y cada P_i^bloque corrida por θ_cámara — no
    reimplementa el recuento.
    """
    from ensemble import simular_con_guardas
    from sobre_tablas import SOBRE_TABLAS, es_admisible, p_afirma_tablas

    if not SOBRE_TABLAS or es_admisible(caracter):
        return cond
    import numpy as np
    p_tab = [p_afirma_tablas(f["p_afirma_si_vota"], camara) for f in perfiles]
    lin_tab, des_tab = zip(*(a_linea_y_desvio(p) for p in p_tab))
    sim_tab = simular_con_guardas(np.array(lin_tab), np.array(des_tab, dtype=float),
                                  "DOS_TERCIOS", camara, n_sims=n_sims, seed=seed,
                                  p_presente=presentes, reparto_desvio=REPARTO_DESVIO)
    p_tablas = float(sim_tab["p_aprobacion"])
    return {**cond, "p": float(p_tablas * cond["p"]), "p_tablas": p_tablas,
           "via": "sobre_tablas"}


def _p_afirmativo_del_simulador(linea: str, desvio: float) -> float:
    """P(este legislador vote AFIRMATIVO) según el MISMO modelo que simula la votación.

    Se pide al agregador (`_prob_conductas`) en vez de rehacer la cuenta acá: sigue su
    línea con (1-desvío) y el desvío se reparte entre las otras dos conductas. Es el
    número que la interfaz necesita para recalcular en vivo cuando se mueve el clima
    — y tiene que ser EL MISMO que usa la simulación, o el slider mostraría un modelo
    distinto del que produjo la probabilidad de arriba.
    """
    agg = RAIZ / "modelo" / "agregador_institucional" / "src"
    if str(agg) not in sys.path:
        sys.path.insert(0, str(agg))
    from agregador import CONDUCTAS, _prob_conductas  # type: ignore
    return float(_prob_conductas(linea, desvio)[list(CONDUCTAS).index("AFIRMATIVO")])


def armar_roster(camara: str, bloques: list[dict], ind: dict, detalle_roster: dict,
                 contexto_dictamen: dict | None = None):
    """Perfil de cada legislador -> los arrays que entran al agregador.

    Devuelve (lineas, desvios, p_presente, perfiles). Es el ÚNICO lugar donde se
    decide cómo vota cada uno: el tablero y la probabilidad salen los dos de acá, así
    que no se pueden contradecir.

    `contexto_dictamen`: BANDERA APAGADA POR DEFECTO (BETA_DICTAMEN, ver
    `beta_dictamen.py` / ADR-0016 / §III.A.2 de FORMULA-COMPLETA.md). `None` (el
    default) no importa el módulo ni toca nada — mismo comportamiento que antes de
    que existiera. Con contexto y la bandera prendida, el dictamen entra POR
    LEGISLADOR: quien firmó, si firmó su jefe (filtrado por lealtad) y el carácter
    del despacho corren la P ANTES de traducirla a (línea, desvío).
    """
    import numpy as np
    share = {b["bloque"]: float(b.get("_share_afirm", 0.5)) for b in bloques}
    ajustar_dictamen = None
    if contexto_dictamen is not None:
        from beta_dictamen import ajuste as ajustar_dictamen  # noqa: E402
    lineas, desvios, presentes, perfiles = [], [], [], []
    for f in detalle_roster["filas"]:
        lid = f["legislador_id"]
        rec = ind.get((camara, lid))
        p_rec, n_tot, presencia, n_emit = rec if rec else (None, 0, 1.0, 0)
        pf = perfil_legislador(share.get(f["bloque_linaje"], 0.5), float(f["desvio"]),
                               record=p_rec, n_emitidos=n_emit, presencia=presencia)
        p_afirma = pf["p_afirma_si_vota"]
        if ajustar_dictamen is not None:
            p_afirma = ajustar_dictamen(p_afirma, f["bloque_linaje"], lid,
                                        float(f["desvio"]), contexto_dictamen)
        linea, desv = a_linea_y_desvio(p_afirma)
        lineas.append(linea)
        desvios.append(desv)
        presentes.append(pf["p_presente"])
        perfiles.append({**f, **pf, "p_afirma_si_vota": p_afirma, "linea_efectiva": linea,
                         "n_votos": int(n_tot), "n_emitidos": int(n_emit),
                         "record_afirmativo": (round(float(p_rec), 4)
                                               if p_rec is not None else None)})
    return (np.array(lineas), np.array(desvios, dtype=float),
            np.array(presentes, dtype=float), perfiles)


def _tablero_camara(camara: str, fecha, perfiles: list[dict], sim: dict,
                    detalle_roster: dict,
                    desvio_bisagra: float = DESVIO_BISAGRA) -> dict:
    """Quién acompaña, quién no y sobre quién hay incógnita, en esa cámara.

    La postura sale de lo MISMO que alimenta la simulación —la línea de su bloque y
    su desvío individual—, así el conteo y la probabilidad no se pueden contradecir.
    El récord individual del legislador en proyectos de este origen va aparte, como
    CONTEXTO: sirve para discutir un caso, no para calcular el número.
    """
    legs = []
    for f in perfiles:
        # P efectiva = de qué lado está × con qué frecuencia aparece. Es exactamente
        # lo que entra al agregador (línea+desvío, escalado por p_presente).
        p_ef = f["p_afirma_si_vota"] * f["p_presente"]
        if f["p_presente"] < PRESENCIA_MINIMA:
            postura = "no_vota"
        elif INCERTIDUMBRE_INCOGNITA <= p_ef <= 1.0 - INCERTIDUMBRE_INCOGNITA:
            postura = "incognita"
        elif p_ef >= 0.5:
            postura = "acompana"
        else:
            postura = "no_acompana"
        legs.append({
            "legislador_id": f["legislador_id"],
            "legislador": f.get("legislador") or f["legislador_id"],
            "bloque": f["bloque_linaje"], "postura": postura,
            "linea_del_bloque": f["linea_efectiva"],
            "desvio": round(float(f["desvio"]), 4), "desvio_de": f["desvio_de"],
            "p_afirmativo": round(p_ef, 4),
            "p_si_vota": round(f["p_afirma_si_vota"], 4),
            "presencia": round(f["p_presente"], 3),
            "direccion_de": f["fuente_direccion"],
            "share_linaje": round(f["share_linaje"], 4),
            "record_afirmativo": f["record_afirmativo"],
            "n_votos": int(f["n_votos"]), "n_emitidos": int(f["n_emitidos"]),
        })
    n = len(legs)
    conteo = {k: sum(1 for x in legs if x["postura"] == k)
              for k in ("acompana", "no_acompana", "incognita", "no_vota")}
    # A quién ir a buscar: los de desvío más alto primero — son los que el clima y la
    # negociación mueven, y los que el análisis del ICG mostró que sí responden.
    #
    # La lista se arma SIEMPRE, crucen o no el umbral de bisagra. Medido el 22-08: en
    # el Senado NINGUNO de los 72 en ejercicio llega a 0,20 (su p90 de desvío es 0,114
    # contra 0,209 en Diputados), así que con el corte absoluto la lista quedaba vacía
    # justo en la cámara donde más se negocia. Bajar el umbral para que aparezcan
    # sería inventar bisagras; dejar la lista vacía sería inútil. Se ordena por desvío
    # y `hay_bisagras` dice si alguno cruza de verdad, para que la interfaz no los
    # presente como algo que no son.
    # Se ordena por lo INDECISO que está (qué tan cerca de 50/50), no por el desvío:
    # ahora que el número del bloque no se redondea, la duda real se ve en la P.
    orden = sorted((x for x in legs if x["postura"] != "no_vota"),
                   key=lambda x: (-min(x["p_afirmativo"], 1.0 - x["p_afirmativo"]),
                                  -x["desvio"], x["legislador"]))
    hay_bisagras = any(x["postura"] == "incognita" for x in legs)
    a_negociar = [x for x in orden if x["postura"] == "incognita"] or orden
    return {
        "camara": camara, "fecha": str(pd.to_datetime(fecha).date()),
        # `n // 2 + 1` es la mayoria ABSOLUTA (129 sobre 257), no la simple. Se
        # llamaba `umbral_mayoria_simple` y por eso el panel calculaba el margen
        # contra el numero equivocado: la barra se dibujaba contra
        # `umbral_simulado` (la mitad de los que efectivamente votan) y el margen
        # contra este. Renombrado el 04-09-2026 — URGENTE 6. El valor NO cambia:
        # cambia el nombre, que era el que mentia.
        "bancas": n, "umbral_mayoria_absoluta": n // 2 + 1,
        # Los afirmativos esperados salen de la MISMA simulación que la probabilidad.
        "afirmativos_esperados": round(float(sim["afirm_medio"]), 1),
        "afirmativos_banda_5_95": [round(float(sim["afirm_p5"]), 1),
                                   round(float(sim["afirm_p95"]), 1)],
        "umbral_simulado": round(float(sim["umbral_medio"]), 1),
        "conteo": conteo, "legisladores": legs,
        "a_negociar": [{"legislador_id": x["legislador_id"],
                        "legislador": x["legislador"], "bloque": x["bloque"],
                        "desvio": x["desvio"], "postura": x["postura"],
                        "p_afirmativo": x["p_afirmativo"]}
                       for x in a_negociar[:20]],
        "hay_bisagras": hay_bisagras,
        "desvio_maximo": round(max((x["desvio"] for x in legs), default=0.0), 4),
        "desvio_bisagra": desvio_bisagra,
        "padron": detalle_roster.get("padron"),
    }


def nowcast(camara_origen: str, fecha=None, *, proyecto_id: str | None = None,
            tipo_mayoria: str = "SIMPLE", origen: str | None = None,
            tema: str | None = None, n_sims: int = 2000, seed: int = 0,
            tabla_caracter=None) -> dict:
    """La cadena de puertas sobre la configuración de las cámaras a `fecha`.

    `proyecto_id` es OPCIONAL: sin él, el proyecto es hipotético y A y C quedan
    `sin_dato` —el condicionante se encoge a 0—, que es exactamente lo que
    corresponde para algo que todavía no pasó por comisión.
    """
    from ensemble import roster_nominal, simular_con_guardas
    from puerta_a import cargar_caracter, caracter_de, condicionar
    from puerta_d import camara_revisora, p_voto_revisora

    F = pd.to_datetime(fecha) if fecha is not None else pd.Timestamp.today().normalize()
    if pd.isna(F):
        raise ValueError(f"fecha inválida: {fecha!r}")
    cam_o = str(camara_origen).strip().lower()
    cam_r = camara_revisora(cam_o)

    # TEMA AUTOMÁTICO (TEMA_AUTO=1, apagado por defecto — ver el bloque de arriba).
    # Sólo actúa si el llamador NO pasó `tema` a mano: lo manual siempre gana.
    temas_multi, combinar_temas_activo = None, "primaria"
    if tema is None:
        tema_auto, temas_multi, combinar_temas_activo = _tema_auto(proyecto_id)
        tema = tema_auto

    # FASE 1 (RECORD_POR_TEMA, URGENTE 8): la multietiqueta para el récord del
    # legislador se resuelve INDEPENDIENTE de TEMA_AUTO (condiciona la POSTURA
    # DE BLOQUE, un mecanismo distinto, apagado desde ADR-0024). Manual `tema=`
    # sigue ganando siempre; si no hay nada manual y TEMA_AUTO ya la resolvió,
    # se reusa esa (no se pregunta dos veces); si TEMA_AUTO está apagado pero
    # RECORD_POR_TEMA está prendido, se resuelve acá igual.
    areas_objetivo_ind = temas_multi if temas_multi else ([(tema, 1.0)] if tema else None)
    if areas_objetivo_ind is None and RECORD_POR_TEMA and proyecto_id:
        asigs_record = _resolver_multietiqueta(proyecto_id)
        areas_objetivo_ind = asigs_record or None

    cargar, proyectar_postura, cargar_tema_por_acta = _bloque()
    votos = cargar(CANONICA_CLEAN)
    cond = cargar_tema_por_acta() if (tema or origen or temas_multi or areas_objetivo_ind) else None
    origen_map = {}
    if origen and Path(PROYECTO_ORIGEN_POR_ACTA).exists():
        opa = pd.read_parquet(PROYECTO_ORIGEN_POR_ACTA)
        origen_map = dict(zip(opa["acta_id"].astype(str), opa["origen"]))
    elif origen:
        logger.warning("no encontré %s: el récord individual no se puede condicionar "
                       "por origen", PROYECTO_ORIGEN_POR_ACTA)
    ind = alineacion_individual(votos, origen_map, origen, hasta=F)
    if RECORD_POR_TEMA and areas_objetivo_ind:
        ind = alineacion_individual_por_area(votos, cond, origen_map, origen,
                                             areas_objetivo_ind, ind, hasta=F)

    # ── A y C: el carácter OBSERVADO, si lo hay ────────────────────────────────
    tabla = tabla_caracter if tabla_caracter is not None else cargar_caracter()
    car_o = caracter_de(proyecto_id or "", cam_o, tabla, fecha_corte=F)
    car_r = caracter_de(proyecto_id or "", cam_r, tabla, fecha_corte=F)

    # ── B bis: el dictamen POR LEGISLADOR (ADR-0016). BANDERA APAGADA POR
    # DEFECTO: sin BETA_DICTAMEN=1 no se importa `beta_dictamen` y esto queda en
    # None, así que `armar_roster` no toca nada (ver su docstring).
    ctx_o = ctx_r = None
    if proyecto_id:
        from beta_dictamen import BETA_DICTAMEN, contexto_de
        if BETA_DICTAMEN:
            ctx_o = contexto_de(proyecto_id, cam_o, F)
            ctx_r = contexto_de(proyecto_id, cam_r, F)

    # ── B: la votación en la cámara de ORIGEN ──────────────────────────────────
    bloques_o = proyectar_postura(votos, F, cam_o, tema=tema, origen=origen,
                                  cond_por_acta=cond, temas=temas_multi,
                                  combinar_temas=combinar_temas_activo)
    _, _, det_o = roster_nominal(cam_o, F, bloques_o)
    lin_o, des_o, pre_o, perf_o = armar_roster(cam_o, bloques_o, ind, det_o, ctx_o)
    eps0_activo = EPSILON0 if INCERTIDUMBRE_LEGISLADOR else 0.0
    tau_activo = TAU if INCERTIDUMBRE_LEGISLADOR else 0.0
    sim_o = simular_con_guardas(lin_o, des_o, tipo_mayoria, cam_o, n_sims=n_sims,
                                seed=seed, p_presente=pre_o, reparto_desvio=REPARTO_DESVIO,
                                epsilon0=eps0_activo, tau=tau_activo)
    b = condicionar(sim_o["p_aprobacion"], car_o)
    b = _via_sobre_tablas(b, car_o, cam_o, perf_o, pre_o, n_sims=n_sims, seed=seed)

    # ── D: la votación en la cámara REVISORA ───────────────────────────────────
    bloques_r = proyectar_postura(votos, F, cam_r, tema=tema, origen=origen,
                                  cond_por_acta=cond, temas=temas_multi,
                                  combinar_temas=combinar_temas_activo)
    _, _, det_r = roster_nominal(cam_r, F, bloques_r)
    lin_r, des_r, pre_r, perf_r = armar_roster(cam_r, bloques_r, ind, det_r, ctx_r)
    d_raw = p_voto_revisora(cam_o, F, bloques_r, tipo_mayoria=tipo_mayoria,
                            n_sims=n_sims, seed=seed,
                            roster=(lin_r, des_r, pre_r, det_r),
                            reparto_desvio=REPARTO_DESVIO,
                            epsilon0=eps0_activo, tau=tau_activo)
    d = condicionar(d_raw["p_aprobacion"], car_r)
    d = _via_sobre_tablas(d, car_r, cam_r, perf_r, pre_r, n_sims=n_sims, seed=seed)
    # Sin fallback: si a `p_voto_revisora` le faltara un percentil, tiene que romper
    # acá y no rellenarse con la media — una banda inventada se lee igual que una real.
    sim_r = {k: d_raw[k] for k in ("afirm_medio", "afirm_p5", "afirm_p95", "umbral_medio")}

    p_final = float(b["p"] * d["p"])

    def _paso(letra, nombre, natur, car=None, prob=None):
        p = {"paso": letra, "nombre": nombre, "naturaleza": natur}
        if car is not None:
            p.update({"estado": car["estado"], "motivo": car.get("motivo", ""),
                      "n_firmantes": car.get("n_firmantes", 0),
                      "hay_minoria": car.get("hay_minoria", False),
                      "disidencia": bool(car.get("disidencia_parcial")
                                         or car.get("disidencia_total")),
                      "acumulado": car.get("acumulado", False)})
        if prob is not None:
            p.update({"p": round(prob["p"], 4), "p_sin_condicionar": round(prob["p0"], 4),
                      "condicionado_por_el_dictamen": prob["condicionado"],
                      "via": prob.get("via", "normal")})
            if "p_tablas" in prob:
                p["p_sobre_tablas"] = round(prob["p_tablas"], 4)
        return p

    return {
        "proyecto_id": proyecto_id or "(hipotético)",
        "fecha": str(F.date()),
        "camara_origen": cam_o, "camara_revisora": cam_r,
        "tipo_mayoria": tipo_mayoria, "origen": origen, "tema": tema,
        "p_aprobacion": round(p_final, 4),
        "condicional_a": ("que las dos cámaras lo voten. NO incluye la chance de que "
                          "el proyecto sea tratado: eso es agenda y no se estima."),
        "pasos": [
            _paso("A", "Dictamen en la cámara de origen", "observado", car=car_o),
            _paso("B", "Votación en la cámara de origen", "calculado", prob=b),
            _paso("C", "Dictamen en la cámara revisora", "observado", car=car_r),
            _paso("D", "Votación en la cámara revisora", "calculado", prob=d),
        ],
        "camaras": {
            "origen": _tablero_camara(cam_o, F, perf_o, sim_o, det_o),
            "revisora": _tablero_camara(cam_r, F, perf_r, sim_r, det_r),
        },
    }


def imprimir(nc: dict) -> None:
    print("\n" + "=" * 66)
    print(f"  NOWCAST POR PUERTAS — {nc['proyecto_id']}  ({nc['fecha']})")
    print(f"  origen: {nc['camara_origen']}  ->  revisora: {nc['camara_revisora']}")
    print("=" * 66)
    for p in nc["pasos"]:
        if p["naturaleza"] == "observado":
            extra = f"{p['n_firmantes']} firmantes" if p["estado"] == "con_caracter" else ""
            print(f"  {p['paso']}  {p['nombre']:<38} OBSERVADO  {p['estado']:<13} {extra}")
        else:
            marca = "condicionado" if p["condicionado_por_el_dictamen"] else "sin condicionar"
            print(f"  {p['paso']}  {p['nombre']:<38} {p['p']*100:6.1f}%    ({marca})")
    print(f"  {'-'*62}")
    print(f"  P(APROBACIÓN)  {nc['p_aprobacion']*100:5.1f}%   — {nc['condicional_a']}")
    for cual in ("origen", "revisora"):
        c = nc["camaras"][cual]
        k = c["conteo"]
        b95 = c["afirmativos_banda_5_95"]
        print(f"\n  {cual.upper()} ({c['camara']}): {c['bancas']} bancas, umbral "
              f"{c['umbral_simulado']} (mayoria absoluta {c['umbral_mayoria_absoluta']})"
              f" | afirmativos esperados {c['afirmativos_esperados']} "
              f"(banda {b95[0]}-{b95[1]})")
        print(f"    acompañan {k['acompana']} · no acompañan {k['no_acompana']} · "
              f"INCÓGNITA {k['incognita']}")
        if c["a_negociar"]:
            rot = ("a negociar (bisagras, más movibles primero)" if c["hay_bisagras"]
                   else f"nadie llega al umbral de bisagra ({c['desvio_bisagra']}); "
                        f"los de desvío más alto (máx {c['desvio_maximo']})")
            print(f"    {rot}:")
            for x in c["a_negociar"][:6]:
                print(f"      · {x['legislador']:<38} {x['bloque']:<22} desvío {x['desvio']:.3f}")
    print("=" * 66)


def main(argv: list[str]) -> None:
    import argparse
    import json
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Nowcast por puertas de un proyecto.")
    ap.add_argument("camara_origen", help="diputados | senado")
    ap.add_argument("--fecha", default=None, help="por defecto, hoy")
    ap.add_argument("--proyecto", default=None, help="proyecto_id; sin esto es hipotético")
    ap.add_argument("--tipo-mayoria", default="SIMPLE")
    ap.add_argument("--origen", default=None,
                    help="EJECUTIVO | OFICIALISMO | ALIADOS | OPOSICION")
    ap.add_argument("--tema", default=None)
    ap.add_argument("--n-sims", type=int, default=2000)
    ap.add_argument("--json", default=None, help="ruta donde escribir la salida completa")
    a = ap.parse_args(argv[1:])
    nc = nowcast(a.camara_origen, a.fecha, proyecto_id=a.proyecto,
                 tipo_mayoria=a.tipo_mayoria, origen=a.origen, tema=a.tema,
                 n_sims=a.n_sims)
    imprimir(nc)
    if a.json:
        Path(a.json).write_text(json.dumps(nc, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print(f"\n  -> {a.json}")


if __name__ == "__main__":
    main(sys.argv)
