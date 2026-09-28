# ADR-0033 — El récord por ORIGEN relabelado atraviesa el recambio (es la primera memoria que lo hace), pero es memoria de LINAJE y el motor ya la tiene: no mejora, el guard sigue. Y el harness filtra votos del mismo día.

**Fecha:** 2026-09-27/28 · **Estado:** MEDIDO, sin cambios en el motor · **Decide:** Claude, sesión
delegada por Franco (`coordinacion/PROMPT-RECORD-POR-ORIGEN.md`) · **Toca:**
`evaluacion/baseline/src/{record_por_origen,record_por_origen_brazos,censo_detalle_paralelo}.py`
(nuevos), `evaluacion/baseline/src/baseline_voto_individual.py` (aditivo: parámetro `hasta` y
columnas de insumo en el detalle; el resumen no cambia), `evaluacion/baseline/tests/
test_record_por_origen.py` (nuevo) · **Se relaciona con:** ADR-0018 (guard, **nota agregada**),
ADR-0026 (récord por tema — su medición queda **en revisión**, ver URGENTE), ADR-0031, ADR-0032

**Fórmula (ADR-0015 nivel 3): la fórmula no cambia.** El término probado queda escrito en
§II.5 de `FORMULA-COMPLETA.md` como **probado e inactivo**, con la discrepancia abierta.

## Veredicto

1. **La hipótesis de Franco se sostiene como descripción de la realidad:** *"cuánto más acompaña
   a lo que manda el Ejecutivo que a lo que trae la oposición"* ($\rho_i$) **no se da vuelta
   con el cambio de gobierno: se relabela.** Es la primera de seis codificaciones que atraviesa
   el recambio.
2. **Pero lo que persiste es el LINAJE, no la persona.** Restado el $\rho$ del linaje en su
   cámara, el residuo individual no persiste (≈0 en todos los cortes), aunque dentro de una era
   es muy estable.
3. **Y eso el motor ya lo tiene**: condiciona el récord individual por origen dentro de la era
   y la postura de bloque por origen dentro del mismo gobierno. Sumar el $\rho$ heredado no
   mejora nada en el censo (Δ Brier ≤ 0,4% en lo que toca, IC incluye 0).
4. **La versión "realista" —no borrar la historia, anclarla a la relación propio/ajeno—
   predice PEOR** (+3,9% de Brier global, +44% en los primeros 180 días de cada era). **El guard
   sigue aportando.** Queda como discrepancia abierta en `FORMULA-COMPLETA.md`, por la regla
   acordada: no se prende, no se esconde.
5. **Hallazgo colateral, más grande que la pregunta:** el harness del censo cuenta como
   "historia" las actas del **mismo día** (los artículos de la misma ley, en orden arbitrario).
   Con historia estrictamente anterior, el skill publicado **0,161 cae a 0,092**. Ver URGENTE.

## FASE 0 — insumos y celdas

`origen_por_acta`: EJECUTIVO 1.744 / OPOSICIÓN 1.006 / OFICIALISMO 588 (no confiable, no se usa
para concluir) / ALIADOS 78 / DESCONOCIDO 2.582 actas. Cobertura EJEC∪OPOS por era: Kirchner
34–35% · Macri 70–81% · Fernández 55–83% · Milei 70–75%. **Todas** las actas EJEC/OPOS tienen
expediente o proyecto: se puede clusterizar por ley. Actas por expediente: 1,3 (AF) · 2,0 (K) ·
2,1 (Macri) · **3,4 (Milei)**.

Universo del test principal (las dos categorías a ambos lados del recambio):

| recambio | n≥5 | n≥10 | n≥20 | continuadores |
|---|---:|---:|---:|---:|
| 2015 | 206 | 190 | 126 | 221 |
| 2019 | 109 | 59 | 52 | 214 |
| 2023 | 139 | 48 | 24 | 210 |

**Sesgo de supervivencia, medido:** récord general de los que atraviesan 0,81–0,82 contra
0,74–0,76 de todos los activos. En 2023 el universo es 60% kirchnerismo (83 de 139). La era
2019-23 es un agujero conocido (296 actas; sólo 52 de Diputados): con n≥10 en 2019/2023 el
universo es casi sólo Senado.

## FASE 1 — ¿$\rho$ atraviesa el recambio?

$r_{i,o}$ encogido EB (k=5) hacia el récord general del legislador en la era;
$\rho_i=r_{i,E}-r_{i,O}$; pares antes/después de cada recambio. IC 95% con el **más ancho** de
dos bootstraps: Poisson por **expediente** (recalcula $\rho$, el lado y los pares) y por
legislador. El de expediente fue hasta **5×** más ancho: acá también la unidad efectiva es la ley.

### Dos desvíos del prompt, declarados, los dos por un cruce roto

1. **El lado se mide por cámara.** Juntando las dos cámaras, los senadores peronistas
   dialoguistas de 2015-19 heredaban el lado de los diputados K: el residuo del Senado entre eras
   daba −0,85, un número imposible.
2. **El lado se centra en la tasa de la cámara**, no en ½. El criterio de `estimar_psi_arrastre`
   (tasa del linaje en actas EJECUTIVO − ½), agregado a una era, marca como **ambiguos al
   radicalismo bajo Kirchner (−0,04) y a LLA bajo Fernández (+0,03)**: lo que el Ejecutivo lleva
   al recinto es mayormente de consenso y la oposición lo acompaña más de la mitad de las
   veces. El criterio ψ crudo se reporta como sensibilidad (va en la misma dirección).

### Resultado (pooled, n≥5 salvo indicación)

| medición | r | IC 95% | n |
|---|---:|---|---:|
| **mismo lado** — persistencia de $\rho$ | +0,41 | [−0,28; 0,75] | 43 |
| **cambio de lado** — $\rho$ antes vs después | **−0,60** | [−0,82; −0,27] | 210 |
| → $\rho$ heredado (invertido) vs después | **+0,60** | [0,27; 0,82] | 210 |
| relabelado, todos los no ambiguos | **+0,54** | [0,30; 0,76] | 253 |
| relabelado, n≥20 | +0,80 | [0,60; 0,87] | 69 |
| **crudo** mezclando los dos grupos | −0,35 | [−0,45; −0,10] | 454 |
| residuo individual (ρ − ρ del linaje), relabelado, cambio de lado | −0,03 | [−0,16; 0,22] | 210 |
| residuo individual, mismo lado | −0,12 | [−0,42; 0,24] | 43 |

Por recambio (relabelado): 2015 **+0,81** [0,59; 0,86] · 2019 +0,77 [−0,33; 0,89] · 2023 **+0,60**
[−0,26; 0,87]. 2019 y 2023 no alcanzan significancia con la partición por expediente (133 y 136
expedientes). **Por cámara:** en Diputados el patrón es claro (cambio de lado +0,62 heredado); en
el **Senado el lado casi no se identifica** (118 de 125 "ambiguos": en el recinto del Senado casi
todo lo del Ejecutivo sale por consenso). Criterio ψ crudo: mismo lado +0,15, cambio de lado
heredado +0,63, relabelado +0,34.

**Dentro de la era, $\rho$ es un rasgo real** (y no agrupamiento por ley, a diferencia de la
firma temática de ADR-0032): confiabilidad split-half partiendo por expediente 0,86–0,94; el
residuo intra-linaje 0,65–0,83; cronológica 0,67–0,69 en Macri y Milei. **Entre eras, lo
individual se pierde.** Mismo patrón que el desvío en ADR-0032.

**Caso Pichetto** (`leg:5daaefa4774c`): Kirchner (Senado, FdT) $\rho$=+0,08, lado +1; Macri
(Senado) $\rho$=0,00, lado ambiguo; Milei (Diputados, OTRO/PROVINCIAL) $\rho$=**−0,18** con
lado +1 — acompañó más lo de la oposición (universidades, jubilaciones) que lo del Ejecutivo. No
es el caso limpio que motivó la hipótesis.

## FASE 2 — censo, voto a voto

`censo_detalle_paralelo.py` corre el harness partido por fechas (**13,8 min**, 691.893 votos —
mismos que el censo del 16-09) y guarda share y desvío del linaje por voto; los brazos se
recomputan offline. A1 recomputado = `p` del harness (error máx. 2e-16).

| brazo | qué es |
|---|---|
| A1 | harness hoy: récord de la era, sin origen |
| **A2** | **espejo del motor**: récord de la era condicionado por el origen del acta (`alineacion_individual`) |
| A0 / A0o | guard off (historia completa), sin / con origen |
| **B1** | A2 + λ·w·$\rho_{\text{heredado}}$·$s_o$ (el término del prompt); w=1 o k/(n+k); λ **dejando una era afuera** |
| **B2** | guard off + récord condicionado por la **relación** propio/ajeno (memoria anclada al rol) |

El lado de hoy se estima walk-forward (actas EJECUTIVO de la era anteriores a la fecha, mínimo
3); cobertura: lado definido 80% de los votos EJEC/OPOS, $\rho$ heredado no nulo 14,7%, relación
definida 40,8%. Se loguea y un test falla si cae a 0%.

### Resultado con historia ESTRICTA (sólo fechas anteriores; el que vale)

ΔBrier relativo contra A2, IC por expediente:

| corte | A1 (harness hoy) | A0o (guard off) | **B1** (ρ heredado) | **B2** (guard off + relación) |
|---|---:|---:|---:|---:|
| global | +9,8% | +3,6% | **−0,03%** [ns] | **+3,9%** |
| desde 2023 | +27,6% | +4,4% [ns] | −0,05% [ns] | +10,9% [ns] |
| primeros 180 días de era | +9,5% | +20,3% [ns] | −0,29% [ns] | **+43,9%** [ns] |
| lo que toca ρ heredado | +41,6% | +30,4% | −0,42% [ns] | +24,5% |

skill: A1 0,092 · **A2 0,173** · A0o 0,143 · B1 0,173 · B2 0,141. Desde 2023: A1 −0,029 · **A2 0,193**.
Con la historia del harness (con fuga) la conclusión es la misma: B1 ±0,0%, B2 +3,2%.

**B1 sobre A1 (el harness) sí "gana"** (λ=3–4, −0,6%): es la ganancia espuria que se
anticipó — tapa que el harness no condiciona por origen. Por eso la comparación válida es
contra A2.

### El 2×2 que pedía el prompt

| | origen off | origen on |
|---|---|---|
| **guard on** | A2 — skill 0,173 | B1 — 0,173 (no aporta) |
| **guard off** | A0o — 0,143 | B2 — 0,141 |

**El récord por origen no hace que el guard deje de aportar.** Sin guard se pierde ~3,6–3,9%
de Brier con o sin memoria relabelada.

## Por qué no mejora (la lectura)

Lo que persiste entre eras es el comportamiento del **linaje** frente al Ejecutivo, relabelado.
Dentro de la era nueva el motor lo reaprende rápido por dos vías que ya existen: el share de
bloque condicionado por origen (mismo gobierno) y el récord individual condicionado por origen.
Lo único que el motor no puede reaprender es lo individual — y eso es justo lo que no persiste.

## Registro de codificaciones descartadas (sumadas a las de ADR-0018/0031/0032)

| codificación | motivo |
|---|---|
| $\rho_i$ heredado relabelado como término aditivo en logit (B1) | persiste (+0,54) pero es memoria de linaje; sobre el espejo del motor Δ≈0, IC incluye 0 |
| récord sin guard condicionado por la relación propio/ajeno (B2) | predice peor que el guard (+3,9%; +44% al arranque de era) |
| residuo individual de $\rho$ (ρ − ρ del linaje) | no persiste entre eras (≈0), aunque es estable dentro de la era |
| lado por criterio ψ crudo (tasa − ½) agregado a la era | clasifica mal a oposiciones claras (UCR bajo K, LLA bajo AF) |
| lado calculado juntando las dos cámaras | asigna a senadores el lado de los diputados de su linaje |

## Siguiente candidata

**El prior del share de BLOQUE al arranque de la era**, no el récord individual. Visto en el censo:
en Ley Bases (abril 2024) la postura condicionada a EJECUTIVO tenía 2 actas del gobierno nuevo y
se encogía hacia el share **incondicional de 730 días, que mezcla eras**: LLA salía con 0,615 de
share sobre un proyecto de su propio Ejecutivo. La candidata es encoger el share condicionado
hacia el comportamiento **relabelado** del linaje en la era anterior (propio/ajeno), en vez de
hacia la ventana incondicional. Es donde la FASE 1 dice que está la señal (linaje) y donde el
motor hoy tiene un hueco. Riesgo: ADR-0016 pide que los términos nuevos entren al legislador; éste
cambia un prior que ya es de bloque.

## Qué dato haría falta

1. **Linaje del Senado 2015-2023 por bloque real**, no por familia: el lado no se identifica en el
   Senado (118/125 ambiguos) y en parte es porque "FdT" junta al interbloque de Pichetto con el K.
2. **Arreglar el agujero de Diputados 2019-2023** (52 actas en cuatro años).
3. **La etiqueta OFICIALISMO confiable** (separar PRO de LLA, deduplicar multi-artículo): hoy el
   30% de las actas con origen conocido no entra al test.

## Colateral — el harness filtra el mismo día (va a URGENTE)

| | historia del harness | estricta |
|---|---:|---:|
| skill global (A1) | **0,161** | **0,092** |
| 2019-2023 | 0,331 | 0,009 |
| desde 2023 | 0,063 | −0,029 |

El mismo `shift(1)` está en `medir_rec_por_tema.py` y `fase1_rec_por_tema.py`, que midieron el
**11,1% que justificó prender `RECORD_POR_TEMA`**. Los artículos de una ley comparten tema, así
que esa medición es probablemente la más expuesta. Y el motor tiene la misma forma de fuga en modo
backtest: `_alineacion_base` corta con `fecha <= hasta` (inclusive), mientras que
`proyectar_postura` corta con `<`. Ninguno de los dos se tocó en esta sesión: son decisiones de
Franco.

Reproducir: `python evaluacion/baseline/src/record_por_origen.py` (FASE 0-1, ~5 min) ·
`python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 3` (~14 min) ·
`python evaluacion/baseline/src/record_por_origen_brazos.py --historia {estricta,harness}`.
Salidas en `evaluacion/baseline/outputs/record_por_origen_*_2026-09-27.json`.
