# ADR-0030 — Cierre de la línea de capítulos (pivotes y P_k), camino de reapertura medido, y diagnóstico para el Senado

**Fecha:** 2026-09-17 · **Estado:** CERRADA (pivotes por capítulo, esta ronda) ·
**Decide:** Claude, sesión de veredicto explícitamente delegada por Franco
(`coordinacion/PROMPT-DECIDIR-CAPITULOS.md`: *"Si vale la pena, se arma, se
prende y lo cerramos. Si no, pasamos al Senado y lo mejoramos con lo que
falte."*) · **Toca:** ningún archivo de motor — sesión de medición pura, tres
scripts nuevos en `evaluacion/baseline/src/` · **Se relaciona con:** ADR-0016
(doctrina de la parte al todo), ADR-0018 (guard de era), ADR-0026 (récord por
tema, el mecanismo validado del que colgaba la idea de pivotes), ADR-0027
(composición por capítulos), ADR-0029 y sus cuatro addenda (los tres
intentos previos de validar P_k, todos "no alcanza para concluir")

## Resumen ejecutivo

Tres pruebas, criterios de decisión escritos ANTES de medir. **PRUEBA 1
(pivotes por capítulo) FALLA** en su primer filtro (1.1): la heterogeneidad
entre capítulos es **100% fallback silencioso**, no señal real — Ley Bases se
votó demasiado cerca del recambio de gobierno para que el récord individual
por era tenga con qué condicionar. **No se construyen los pivotes por
capítulo.** `tema_por_capitulo.parquet` y `composicion_capitulos` **quedan en
el repo, construidos y apagados** (decisión ya tomada, no se revierte: no se
publica lo que no se puede respaldar, y no se tira el trabajo).

**PRUEBA 2 (reconstrucción por rango de artículos) PASA, y es el hallazgo
real de esta sesión**: cruzando el artículo que declara el acta de votación
contra el rango de artículos de cada capítulo en el PDF de la Orden del Día,
aparecen **23 proyectos con resultado real por capítulo** (146 tramos
cruzados), contra 1 solo (Ley Bases) que había hasta ahora. **Es el camino
concreto para reabrir esta línea** — no se ejecuta en esta sesión (no
corresponde: el veredicto de hoy es sobre los pivotes, y "no tocar el motor"
sigue vigente hasta que Franco decida si vale la pena rehacer la validación
de $P_k$ con este dato nuevo).

**PRUEBA 3 (cobertura del universo vivo) da CONVIENE_AMPLIAR**: 97,26% de
los 9.962 proyectos con `fecha_ingreso ≥ 2025-01-01` no tiene tema. Es una
decisión de producto, no de este ADR (Franco la tiene pendiente desde
ADR-0029).

| prueba | umbral | resultado | veredicto |
|---|---|---:|---|
| 1.1 heterogeneidad real | ≥ 50% | **0,0%** | **FALLA** |
| 1.2 listas distintas | ≥ 30% específicos | 0,0% (consecuencia de 1.1) | FALLA |
| 1.3 acierta capítulos cortados | evidencia, no bloqueante | sin señal (consecuencia de 1.1) | n/a |
| 2 — reconstrucción por rango | ≥ 5 proyectos | **23 proyectos** | **PASA** |
| 3 — cobertura universo vivo | ≥ 40% sin tema | **97,26%** | **CONVIENE_AMPLIAR** |

## PRUEBA 1 — Pivotes por capítulo

### Qué se construyó

Sobre Ley Bases (`HCDN272347`), roster real de Diputados walk-forward a
`2024-02-01` (misma función que `nowcast_puertas.nowcast()` usa en
producción — `bloque.proyectar_postura`, `ensemble.roster_nominal`,
`nowcast_puertas.alineacion_individual_por_area`/`armar_roster`, sin
reimplementar nada):

- **Lista A:** $P_i$ con la multietiqueta del proyecto entero
  (`_resolver_multietiqueta('HCDN272347')` → `[('POLINST',0.95),
  ('DESREG',0.85), ('ECON',0.75)]`).
- **Lista B:** para cada uno de los 63 capítulos clasificados
  (`tema_por_capitulo.parquet`, clave `(proyecto_id, titulo_num,
  capitulo_num)`), $P_i$ condicionada SOLO al área de ese capítulo.

Único grado de libertad entre A y cada capítulo de B: la postura de BLOQUE
se dejó **incondicional** en las dos listas (`TEMA_AUTO` sigue apagado,
ADR-0024/0028 — no se reabre acá); lo único que cambia es qué récord
INDIVIDUAL usa `alineacion_individual_por_area`.

Script: `evaluacion/baseline/src/prueba1_pivotes_por_capitulo.py`. Salida:
`evaluacion/baseline/outputs/prueba1_pivotes_por_capitulo_2026-09-17.json`.

### 1.1 — La heterogeneidad es fallback, no señal (esto mandó)

**Resultado: 0,0% de los 16.254 pares (legislador, capítulo) tuvo
$n_i^{\text{área}} \geq 1$ real.** No un poco bajo: CERO, exacto. Umbral 50%,
falla por el peor margen posible.

**Por qué, verificado a mano (no se asumió, se midió):** `_alineacion_base`
(la ventana walk-forward del récord INDIVIDUAL, distinta de la ventana de 730
días que usa la postura de BLOQUE) usa el **guard de era** (ADR-0018):
para `hasta='2024-02-01'`, la era vigente arranca el **2023-12-10**
(recambio presidencial). En esos 53 días, el Congreso recién arrancado tiene
**una sola acta con votos individuales registrados** en la canónica antes de
esa fecha (`argentinadatos:diputados:5100`, 2024-01-31). Con un solo acta de
base para las 257 bancas, la chance de que además esa acta esté clasificada
con la MISMA área que se está pidiendo es prácticamente nula — y salió,
efectivamente, nula: tanto Lista A como los 63 capítulos de Lista B caen,
los 258 legisladores, al récord general sin ninguna excepción.

**No es un bug — es exactamente el modo de falla que 1.1 existe para
atrapar**, y además confirma algo más general y más importante que el caso
puntual de Ley Bases: **`alineacion_individual_por_area` no loguea ni avisa
cuando cae a fallback completo** (a diferencia de `bloque.combinar_temas`,
que si loguea "0 actas en ventana; caigo a incondicional" — el mismo patrón
que ya delató el capítulo AUX de Ley Bases en ADR-0029). Cualquier nowcast
de un proyecto votado **cerca de un recambio** (los primeros 2-3 meses de
cada gobierno) está corriendo `RECORD_POR_TEMA` sin efecto real, en
silencio. Esto no cambia la decisión de activación de ADR-0026 (el censo
completo mide POSITIVO en el agregado, incluida la era "desde 2023"), pero
es un hueco de observabilidad real que vale la pena cerrar — ver
"Pendiente" abajo.

**Con 1.1 en 0%, el criterio del prompt aplica literal: la prueba FALLA y no
hace falta seguir.** 1.2 y 1.3 se corrieron igual (para el reporte
completo) y, como se esperaba, no muestran nada: Jaccard(A, ∪B) = 1,0 (A y
los 63 capítulos son TODOS el mismo roster, porque todos cayeron al mismo
fallback) y $P_i$ medio idéntico bit a bit entre capítulos que se cortaron y
capítulos que sobrevivieron (0,7344 los dos). No es que el mecanismo no
discrimine: es que no hay dos mecanismos corriendo, hay uno solo repetido
64 veces.

### Lo que esto NO dice

No dice que "récord por tema no sirve" (ADR-0026 sigue en pie, validado y
prendido, con datos reales de TODO el censo). Dice que **Ley Bases —el caso
que motivó toda esta línea— es un mal caso de prueba en un eje más: además
del problema de granularidad de ADR-0029 (título/capítulo mezclados) y del
problema de las dos rondas, ahora se suma que se votó demasiado pronto
dentro de su propia era** para que el término que se quería probar
(condicionamiento individual por tema) tuviera con qué trabajar. Tres
problemas independientes, en el mismo proyecto, cada uno suficiente por sí
solo para invalidar la prueba puntual — no es sospechoso, es lo esperable de
elegir el caso más grande y más mediático en vez del más representativo.

## PRUEBA 2 — Reconstrucción por rango de artículos

`evaluacion/baseline/src/prueba2_reconstruccion_por_rango.py`. Salida:
`evaluacion/baseline/outputs/prueba2_reconstruccion_por_rango_2026-09-17.json`.

**Paso 1** — de los 1.423 tramos `es_particular`, **591 (148 proyectos)**
declaran al menos un número de artículo parseable en el propio título del
acta (`"Artículo N"`/`"Art. N"`). *Nota: el regex usado exige la forma larga
"ARTÍCULO"/"ARTÍCULOS"; Ley Bases usa la abreviatura "ARTS." y por eso NO
entra en este conteo — es una cota INFERIOR, el universo real de tramos con
artículo declarado es más grande.*

**Paso 2** — de los PDF de Orden del Día que cubren esos 148 proyectos (33
archivos, todos en caché local, `Archivos_Borrar/od_pdf/`), **32/33**
produjeron al menos un capítulo con su artículo de arranque parseado: el
primer `"Art. N"` que sigue al encabezado `"CAPÍTULO X"` en el texto (antes
del próximo encabezado) es el artículo con el que arranca ese capítulo — se
verificó a mano sobre el PDF original de Ley Bases (Capítulo III→Art.9,
IV→Art.14, V→Art.20, VI→Art.22: secuencia creciente y consistente) antes de
aplicarlo en general.

**Paso 3** — cruzando (1) contra (2): **146/591 tramos (25%) cayeron dentro
del rango de un capítulo, en 23 proyectos distintos.** Muy por encima del
umbral de 5 → **PASA**.

**Caveat honesto, no escondido:** la calidad del cruce varía por formato de
PDF. Se revisó un caso (`HCDN099025`, ley de presupuesto) donde varios
artículos muy separados (8 a 48) cayeron todos en "Capítulo I" — el regex
de capítulos no encontró suficientes encabezados intermedios en ese PDF
particular (formato distinto al de Ley Bases), así que el rango de ese
capítulo quedó demasiado ancho. **Esto no invalida el veredicto** (23 ≥ 5
con margen amplio, y el caso verificado a mano —Ley Bases mismo— funciona
bien) pero sí significa que una validación real con este dato necesitaría
una pasada de control de calidad por proyecto antes de confiar ciegamente en
cada rango.

**Qué haría falta para usarlo:** (a) ampliar el regex del paso 1 para cubrir
abreviaturas ("ARTS.", "ARTÍCS.") — más tramos recuperables; (b) una
verificación de sanidad por PDF (¿la secuencia de artículos de arranque es
monótona creciente y sin saltos absurdos?) antes de confiar en un rango; (c)
recién con eso, rehacer `validar_piloto_capitulos.py`/
`validar_leybases_por_capitulos.py` sobre el universo ampliado. Ninguno de
los tres pasos se hizo en esta sesión — es la definición de "lo que queda
pendiente", no un trabajo completado.

## PRUEBA 3 — Cobertura del universo vivo

`evaluacion/baseline/src/prueba3_cobertura_universo_vivo.py`. Salida:
`evaluacion/baseline/outputs/prueba3_cobertura_universo_vivo_2026-09-17.json`.

⚠️ Medido, no sólo `estado`: **`proyectos.estado` Y `proyectos.
ultimo_movimiento`/`ultimo_movimiento_fecha` están 100% NULOS** (los tres
campos, no sólo el que avisaba el prompt) — ninguno sirve de filtro de
"universo vivo". Se usó `fecha_ingreso ≥ 2025-01-01` (mismo corte que la
tarea de cobertura pausada), el único campo de recencia con datos reales
(0 nulos).

- **Universo vivo:** 9.962 proyectos. **Con tema: 273 (2,74%). Sin tema:
  9.689 (97,26%).** Muy por encima del umbral de 40% → **CONVIENE_AMPLIAR**.
- **Descuento AUX:** de lo ya clasificado en el universo vivo, **16,9%**
  salió `AUX.*` (no condiciona nada — esa fracción del gasto futuro también
  compraría cero, como en el resto del registro).
- **Votado vs. no votado, el dato que cambia la pregunta:** de los 9.962,
  sólo **49 ya se votaron** — y esos 49 **ya están clasificados al 100%**.
  **Cero cobertura faltante del lado votado ⇒ cero mejora de Brier
  disponible por este camino ahora mismo.** Los 9.689 proyectos sin tema
  son, los 9.689, del lado NO VOTADO — exactamente el que el prompt advertía
  que no puede mover ningún backtest. Medir esto con Brier habría dado "0%
  de mejora esperada", un número que parece riguroso y es la pregunta
  equivocada: la pregunta real es de **capacidad de respuesta** ("si alguien
  pregunta por uno de estos 9.689 proyectos hoy, el motor no tiene tema para
  él"), no de precisión retrospectiva.
- **Costo, parametrizado** (no se verificó el precio vigente de
  `claude-haiku-4-5-20251001`): 9.689 llamados necesarios, ~1.288 tokens de
  entrada y ~120 de salida estimados por llamado (medidos sobre el prompt
  REAL de `agente_taxonomias.construir_prompt`, no inventados) → ~12,5M
  tokens de entrada + ~1,16M de salida en total. La corrida real de 437
  capítulos de esta sesión costó "centavos de dólar" (orden de magnitud, sin
  cifra exacta) — consistente con que este gasto ronde las decenas de
  dólares, no cientos, pero **es una referencia, no una cifra confirmada**.

**Esto es una decisión de producto pendiente de Franco, no algo que este
ADR resuelva** — la tarea (`tema_por_proyecto.py clasificar --desde-fecha
2025-01-01`) sigue **pausada** por instrucción explícita anterior; este ADR
sólo deja el número (97,26%, no un estimado) para que la decisión se tome
con el dato completo.

## Decisión

**La línea de "pivotes por capítulo" se cierra en esta ronda.** No se activa
ninguna bandera, no se toca `nowcast_puertas.py` ni `FORMULA-COMPLETA.md` —
no hay término nuevo que documentar en la fórmula, porque no se activó
ninguno.

`tema_por_capitulo.parquet` (471 filas, 105 proyectos) y
`modelo/ensemble/src/composicion_capitulos.py` **quedan en el repo,
construidos y apagados** — decisión explícita de Franco, ya tomada, que este
ADR no revierte: no se publica lo que no se puede respaldar, y no se tira el
trabajo.

## Qué haría falta para reabrir la línea

No es "una ley futura bien documentada" únicamente (lo que decía ADR-0029
antes de esta sesión) — **PRUEBA 2 encontró un camino más rápido**: ampliar
la reconstrucción por rango de artículos (23 proyectos ya, potencialmente
más con el regex de abreviaturas) y rehacer la validación de $P_k$ sobre ese
universo. Es trabajo real (control de calidad por PDF, no gratis en tiempo
aunque sí en API), pero es concreto y ya tiene un piso medido.

Separado de eso: si se quisiera reabrir específicamente los PIVOTES POR
TEMA (no $P_k$), hace falta un proyecto votado lejos de un recambio de
gobierno (no en los primeros 2-3 meses de una era) — Ley Bases falló 1.1 por
esto específicamente, y el problema no es del proyecto sino de CUALQUIER
nowcast tan temprano en una era.

## Pendiente (no se hizo en esta sesión, queda anotado)

1. **Observabilidad de `alineacion_individual_por_area`**: agregar un log
   cuando cae a fallback COMPLETO (0% de legisladores con dato real), mismo
   patrón que ya tiene `bloque.combinar_temas`. Hoy es silencioso — esta
   sesión lo encontró por accidente, corriendo una prueba que lo medía a
   propósito; en producción, nadie se entera.
2. **Ampliar el regex de PRUEBA 2** para capturar abreviaturas ("ARTS.",
   "ARTÍCS.") — subestima el universo real de tramos reconstruibles.
3. **Control de calidad por PDF** antes de confiar en los rangos de PRUEBA 2
   (ver el caso HCDN099025 arriba).
4. **La decisión de PRUEBA 3** (ampliar cobertura al universo vivo) sigue
   pendiente de Franco — el número está, la decisión no.

## Diagnóstico para el Senado (preparado, no ejecutado — así lo pidió el prompt)

Lista corta de lo que le falta al Senado, con lo ya medido (verificado
contra archivo antes de repetirlo, no copiado del prompt tal cual: el skill
que cita el prompt, 0,072, es el número PRE guard-de-era; el vigente HOY,
con `GUARD_ERA=1` por defecto desde ADR-0018, es **0,120**):

1. **Skill bajo, pero no por mal ajuste — por poco margen sobre la tasa
   base.** Diputados 0,130 (post guard-era **0,158**, ver ADR-0018) vs.
   Senado **0,072 → 0,120** (+67% con el guard de era, ya aplicado). El
   Brier del Senado es MEJOR en términos absolutos (0,0997 vs 0,1491): la
   tasa base del Senado (87,8% afirmativo) ya predice casi todo sola — la
   pregunta correcta no es "por qué erra más" sino "por qué aporta menos
   sobre lo trivial".
2. **Saturación — confirmada, con causa identificada.** 68,8% de los votos
   del Senado vienen de un linaje con desvío EN EL PISO (≤0,02), 47,0% de
   las $P_i$ son extremas (<0,05 o >0,95), 58% de las predicciones cae en el
   bin superior. `DESVIO_MIN_INDIVIDUAL = 0,02` está tuneado para Diputados
   — en el Senado ES la estimación para dos tercios de los casos, no un
   piso de seguridad.
3. **Valle de era propio.** El valle de skill del Senado es **2019-2023**
   (skill −0,069); el de Diputados es 2015-2019 y desde-2023 — no coinciden
   porque el Senado se renueva por TERCIOS, no completo cada elección. El
   guard de era (ADR-0018) ya usa fechas propias por cámara, así que este
   punto está mitigado, no abierto — se deja igual en la lista porque explica
   POR QUÉ el Senado necesitaba su propio guard, no como pendiente.
4. **Dictamen por legislador, casi sin señal calificada.** ADR-0017 (leídos
   193 OD reales del Senado, 2008-2026): el Senado rotula "mayoría/minoría"
   en el SUMARIO sólo el 1,6% de las veces (3/193) — casi siempre dictamen
   único genérico. `BETA_DICTAMEN` (ADR-0016, apagado por defecto) tiene,
   estructuralmente, mucho menos con qué condicionar en el Senado que en
   Diputados. Estado del ADR: **Aceptada, a revisar por Franco** — no se
   verificó en esta sesión si sigue así.

Ninguno de estos cuatro puntos se trabajó en esta sesión — es exactamente
el diagnóstico ordenado que pidió el prompt, para la próxima.
