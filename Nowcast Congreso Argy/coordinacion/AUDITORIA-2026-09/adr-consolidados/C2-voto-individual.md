# C2 — Voto individual: el récord propio por origen, encogido hacia el linaje

**BORRADOR** · **Absorbe:** 0003, 0004, 0005, 0017, 0018, 0022 · **Referencias:** 0019 (C1), 0031 y 0033 (C6), 0034 (C5)

## 1. La regla

> **P(el legislador vota afirmativo) = su propio récord** —en la era del gobierno vigente, en proyectos **del mismo origen**, de fecha **anterior** y de **otra ley**— **encogido con pseudo-conteo k = 5 hacia el share proyectado de su linaje**. Sin ningún voto previo comparable, el share del linaje ajustado por el desvío. **El origen del proyecto es lo que carga la habilidad.**

## 2. Por qué

Skill del voto individual **0,1333** [0,057; 0,198] sobre 691.845 votos y 3.731 leyes (censo, motor importado, historia estricta; reproducido). El récord independiente hecho aparte da **0,1335** con origen y **0,048** [−0,014; 0,104] sin él: **todo el poder predictivo viene de condicionar por origen**. La diferencia pareada entre ese récord de 30 líneas y el motor completo es −0,00002 [−0,004; +0,003]: la postura por acta, la ventana de 730 días y el guard de era **no se distinguen** de no tenerlos, salvo en el arranque de cada era (2019-2023: el motor le gana por 0,037 de Brier [0,002; 0,069]). Encoger le gana a cortar (+2,8% de Brier sin encoger, IC [1,8; 4,2]). **En la era vigente el skill es 0,010 [−0,26; 0,25]** (312 leyes): no se distingue de predecir la tasa base.

## 3. Cómo se verifica

- `python evaluacion/baseline/src/resumen_censo_limpio.py` (necesita el detalle del censo; hoy no viaja por git).
- `python coordinacion/AUDITORIA-2026-09/control_independiente.py` → el motor no puede perder contra el récord de 30 líneas (propuesto para `evaluacion/baseline/tests/`).
- `evaluacion/baseline/tests/test_harness_es_el_motor.py` (238/238) y `test_historia_sin_fuga.py`.

## 4. Qué la invalida

- Que el skill de la era vigente siga siendo ≈ 0 cuando se acumulen leyes (con IC ±0,25 hacen falta del orden de 2.000 leyes para ±0,10).
- Que la etiqueta de **origen** sea mala: es el insumo más influyente del modelo y **nadie validó sus etiquetas** contra una muestra a mano (fuera de esta auditoría). Hoy 43% de las actas tienen origen `DESCONOCIDO` (2.582 de 5.998) y ahí el récord es incondicional.
- Que una medición con el motor completo (un brazo "sin corte por era", que hoy no existe) muestre que el guard no ayuda: el control independiente lo deja en +2% [incluye 0].

## 5. Estado real hoy (verificado)

| pieza | estado | dónde |
|---|---|---|
| récord propio, era, origen, `<`, `n ≥ 1` | ON; el origen sólo actúa **si el llamador pasa `origen`** | `nowcast_puertas.py:293-330,317-319`, `MIN_HIST_INDIVIDUAL=1` (`:97`) |
| encogimiento k=5 | ON, sin test que fije la bandera ni el valor; **no ajustado** (mismo k del bloque) | `:131,574` |
| guard de era | ON; su evidencia (0,1304 → 0,1611) salió del harness con fuga. **Medido acá con el control independiente** (sólo se quita el corte por era): ayuda **+0,0028 de Brier [−0,0006; +0,0066]**, ≈ 2%, incluye 0 (Senado sí lo excluye); **en la era vigente no hace nada** (−0,0003). Con el motor completo no se puede medir con la bandera: `GUARD_ERA=0` deja sin récord todo lo anterior a 2023 | `:119` |
| desvío individual | la **ficha** `disciplina_individual.csv` usa toda la historia; en $P_i$ entra sólo sin récord (4,7% de los votos, skill −0,38) y en β; el censo no ejercita ese código | `ensemble.py:204-252`, `disciplina.py` |
| β (dictamen por legislador) | ON, pero **no actúa en el panel** (sin `proyecto_id`); coeficientes con offset contaminado (lealtad×jefe 1,75 → 1,29 con offset limpio); `contexto_de` no corta por fecha | `beta_dictamen.py:71,124` |
| linajes (0005) | 10 linajes; ventanas por fecha; Proyecto Sur pasó a IZQUIERDA | `variables/bloque/src/bloque.py` |
| dictamen (0017, 0022) | el rotulado y el carácter alimentan `puerta_a` (identidad) y β; 0017 sigue "a revisar por Franco" desde el 04-09; hoy hay **tres** nociones de "carácter" (`definiciones`, `puerta_a`, `parser_od`) | `puerta_a.py:101` |

**Historia (una línea por ADR):** 0003 (07-01, Valle + Claude) el desvío se modela respecto del bloque · 0004 (07-02) desvío v2 por conducta (el archivo está truncado a mitad de palabra desde su primer commit) · 0005 (07-10, Franco) linajes v2 · 0017 (09-04, Claude en sesión autónoma) rotulado del dictamen y tabla de enlace · 0018 (09-06, Franco) guard de era, en el commit "aaa" · 0022 (09-14, Franco) disidencia = minoría en el Senado y linaje de Daer.

**Se pierde:** el plan de cuatro piezas de 0003 (defección, pivotes: ADR-0030 los cerró); la "indisciplina total" (el motor consume la variante *conducta*, 0,073 de media contra 0,179); las cifras de 0018; la cifra "205 actas" de 0022 (son 205 *firmas* en 57 proyectos).
