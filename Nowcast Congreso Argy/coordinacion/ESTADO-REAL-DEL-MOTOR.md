# Estado real del motor — el inventario para la revisión

**Fecha:** 2026-09-28 · **Origen:** ADR-0034 (cierre de etapa: la fuga y el espejo) ·
**Para qué:** que la revisión intensiva de Franco arranque de hechos ordenados. Una fila por
término del tablero de `FORMULA-COMPLETA.md`, prendidos y apagados, con la evidencia que lo
sostiene y si esa evidencia sigue en pie después de esta sesión.

**Qué se arregló antes de armar esto.** El harness que mide al motor (1) contaba como historia
los artículos anteriores de la misma ley, votados el mismo día, y (2) tenía su propia copia del
récord, que no condicionaba por origen como el motor. Las dos cosas están arregladas en la raíz:
el harness importa el motor (un test lo compara contra `nowcast()` legislador por legislador,
238/238) y la historia es estricta — fecha anterior y **otra ley**. El motor, además, cortaba
su récord con `<=` en backtest, y ahora corta con `<`.

**El número que mide todo esto:** skill **0,1333** [0,057; 0,198] en el voto individual, sobre
691.845 votos y 3.731 leyes. **En la era vigente, 0,010 [−0,26; 0,25]**: no se distingue de
predecir la tasa base. El publicado hasta hoy era 0,1611 y estaba inflado por fuga.

**Cómo leer las columnas.** *Contaminado* = la medición que lo justificó usó el harness con
fuga, un offset con fuga, o un espejo que no era el motor. *Número limpio* = lo que da hoy con el
harness arreglado; "no re-medido" cuando esta sesión no lo re-midió. Todos los IC re-muestrean
leyes enteras, no actas (ADR-0032).

## El inventario

| # | término | ¿prendido? | número que lo justificó | cómo se midió | ¿contaminado? | número limpio | ¿la evidencia sigue en pie? |
|---|---|---|---|---|---|---|---|
| 1 | $s_\ell$ — share del bloque | ✅ | Fase 0: el bloque acierta ≈0,99 la dirección del voto | con la línea de bloque **observada** en la misma acta, no proyectada | no por esta fuga, pero es un techo con oráculo, no un pronóstico | en el censo actúa sólo en la rama de bloque (4,7% de los votos): skill **−0,380** [−0,67; 0,14]; y como ancla del encogimiento del récord | ⚠️ **como pronóstico, nunca estuvo medido.** Donde se usa solo, predice peor que la tasa base |
| 2 | $d_i$ — desvío / lealtad | ✅ | disciplina 96,4% en disputadas (descriptivo) | agregado sobre toda la historia | la ficha (`disciplina_individual.csv`) **no es walk-forward**: se calcula con toda la historia | no re-medido; en $P_i$ sólo entra en la rama de bloque y en β | ⚠️ descriptivo, no predictivo; en backtest de `nowcast()` mira el futuro |
| 3 | $\pi_i$ — presencia | ✅ | — | — | — | el censo evalúa votos emitidos: no la mide | ❌ **nunca medido** como predictor |
| 4 | $\text{rec}_i$ — récord propio (era, origen, encogido, $n\ge1$) | ✅ | skill 0,1304 → **0,1611** (guard + encoger + $n\ge1$) | censo del harness | **sí**: `shift(1)` por fila (misma ley, mismo día) y sin condicionar por origen | **0,1333** [0,057; 0,198]; desde 2023 **0,010**. Encoger vs cortar: cortar +2,8% peor [1,8; 4,2]. $n\ge8$ vs $n\ge1$: +0,5% [−0,01; 1,26]. Guard de era: ADR-0033, con historia por fecha, sin guard +3,6% peor | ✅ el término sostiene el número entero. ⚠️ **el nivel era un 20% menor de lo publicado, y en la era vigente es ≈0** |
| 5 | umbrales y quórum | ✅ | reglamento | — | — | no aplica | ✅ son reglas; el bug de las abstenciones es la fila 8 |
| 6 | Monte Carlo (2.000 sims) | ✅ | — | — | — | no aplica | ✅ mecánica |
| 7 | ε — clip agregado | ⚪ se apaga solo con la fila 13 | — | — | — | — | reemplazado |
| 8 | quórum con abstenciones | ⚪ bandera apagada | Δ = 0,0000 en el panel | `nowcast()` directo | no | — | ✅ (no mueve nada hoy) |
| 9 | δ agregado del dictamen | ⚪ en 0 | −2,29 logit (disputado vs único) | GLM con offset | **sí** (offset del espejo viejo) | no re-medido | no sostiene nada: está en 0 y lo reemplazó β |
| 10 | ICG — clima | ⚪ desconectado | γ ≈ 1,0 en desvío ≥ 0,10 | bootstrap por legislador, otra cadena | no depende del harness | — | ✅ como medición; ❌ nunca probado como predictor en el censo |
| 11 | $\mathcal{C}_c$ — gate del dictamen | ⚪ bandera apagada | — | aproximación del dato | — | — | ❌ nunca medido |
| 12 | β — dictamen por legislador | ✅ **PRENDIDO** | M6: $F_i$ **+2,09**, lealtad×jefe **+1,75**; walk-forward Brier 0,1725 → 0,1591 | GLM con offset + validación 70/30 por tiempo | **sí**: el offset es el espejo viejo (`shift(1)`, sin guard, sin encoger, sin origen) | mismo panel y especificación con el offset del motor limpio: $F_i$ **2,05** (SE por ley 0,43), lealtad×jefe **1,29** (0,33). Los SE por ley son 3-4× los publicados por acta | ⚠️ **a medias.** $F_i$ se sostiene (2,09 → 2,05); lealtad×jefe baja 26% (1,75 → 1,29). El walk-forward que lo prendió usó el mismo offset viejo y no se re-corrió. Y el skill publicado **no lo incluye** |
| 13 | $\varepsilon_0 + \tau\eta_j$ — incertidumbre | ✅ **PRENDIDO** | τ = 1,197 (1,190 el 16-09); banda [p5,p95] cubre el **99,88%** | τ: sobredispersión con offset del espejo viejo. Cobertura: `agregador.backtest` | τ: **sí**. Cobertura: **con oráculo** (le da al agregador la línea de bloque observada) | τ limpio **1,197** (1,186 con el offset viejo sobre los mismos votos; Diputados 1,23 → 1,32). ε₀ óptimo 0,015 → **0,055**. **Cobertura real de la banda: 63,6%** (90% declarado); el recuento esperado sale 6,9 votos por debajo del real | ❌ **la justificación cae**: la banda no es conservadora, es angosta y sesgada. El valor de τ casi no cambia: el problema no es τ subestimado |
| 14 | ψ — arrastre entre cámaras | ⚪ estimado, no implementado | +7,2 | GLM con offset, 239 proyectos | **sí** (offset del espejo viejo) | no re-medido | ⚠️ no citar como limpio; ver "dirección del sesgo" abajo |
| 15 | sobre tablas θ | ⚪ descartado | θ_D −2,05; satura en walk-forward | GLM con offset + walk-forward | **sí** (offset) | no re-medido | ✅ el descarte (satura, no discrimina) no depende del nivel del offset |
| 16 | proximidad electoral | 🔲 propuesto | — | — | — | — | ❌ nunca medido |
| 17 | asimetría del ICG | 🔲 propuesto | — | se acuerda, no se estima | — | — | ❌ nunca medido |
| 18 | $\text{rec}_i^{\text{tema}}$ — récord por tema | ⚪ **APAGADO hoy** (estaba prendido) | **11,06%** menos Brier | censo con `shift(1)` y contra un récord "general" que no era el del motor | **sí, las dos cosas** | misma metodología, historia estricta: **−2,91%** (IC en mejora [−8,6; +2,1]). Contra el motor, en el censo limpio: **empeora 2,1%** [0,8; 3,5], 6,4% donde actúa | ❌ **la evidencia era fuga.** Apagado con el criterio simétrico |
| 19 | multietiqueta en $s_\ell$ / `TEMA_AUTO` | ⚪ cerrado | Δ indistinguible de 0 entre reglas | brazos del harness viejo | sí (el récord de todos los brazos tenía fuga) | no re-medido | ✅ probablemente: la fuga era común a los brazos y la conclusión es "no hay diferencia" |
| 20 | $\hat\rho_i^{\text{her}}\,s_o$ — récord por origen heredado | ⚪ inactivo | Δ −0,03% (ns) | brazos con historia por fecha estricta | parcial (fecha sí; misma ley no) | — | ✅ el "no mejora" se midió ya sin la fuga del mismo día |

## 1. Qué sabemos con confianza

- **El récord propio es lo único que sostiene el número**, y sobrevive al arreglo: skill 0,164
  en los votos donde actúa (95,3%). El condicionamiento por **origen** del proyecto vale: el
  harness limpio con su récord sin origen daba 0,074; el motor, 0,133.
- **Encoger el récord hacia el bloque le gana a cortarlo** (+2,8% de Brier sin encoger, IC que
  excluye 0). El **guard de era** también (ADR-0033, ya con historia por fecha).
- **La era 2011-2015 es la mejor predicha** (0,277) y es robusta a todos los arreglos.
- **El sobre tablas no discrimina** (fila 15): su descarte no dependía del nivel del offset.
- **La unidad efectiva es la ley**: 5.856 actas son 3.731 leyes (el 15,3% de los votos cae en
  actas sin ley identificable). Todo IC de este inventario la respeta.
- **El harness mide al motor**: 238/238 legisladores iguales a `nowcast()`; si divergen, un
  test falla.

## 2. Qué creíamos y ya no

| creíamos | número viejo | número nuevo |
|---|---:|---:|
| el skill del motor en el voto individual | 0,1611 | **0,1333** |
| el skill en la era vigente | 0,063 (harness) / 0,19 (espejo del motor, ADR-0033) | **0,010**, IC [−0,26; 0,25] |
| el récord por tema mejora 11% | +11,06% | **−2,9%** con su metodología; **+2,1% de error** contra el motor |
| la banda del recuento es conservadora | cubre el 99,88% | **cubre el 63,6%** (y sesgada: −6,9 votos) |
| τ estaba subestimado por el offset | — | sí, pero **1%**: 1,186 → 1,197 |
| los coeficientes de β eran conservadores | lealtad×jefe 1,75 | **1,29** con offset limpio (baja); $F_i$ 2,09 → 2,05 |
| los SE de β eran chicos | 0,10–0,17 (cluster por acta) | **0,33–0,43** (cluster por ley) |
| el motor le gana al harness en la era vigente por 0,22 | 0,19 vs −0,03 | 0,01 vs −0,11: la diferencia sigue, **el nivel era fuga** |
| la rama de bloque es marginal | 0,38% (proxy del 06-09) · 2,7% con skill −0,10 (censo publicado) | **4,7%**, con skill **−0,38** |
| el backtest del motor es walk-forward | `fecha <= hasta` | veía el día entero, **incluida el acta a predecir** (skill 0,326) |

## 3. Qué nunca estuvo medido

Están en la fórmula por argumento, no por evidencia de pronóstico:

- **La presencia $\pi_i$** (fila 3): el censo sólo evalúa votos emitidos.
- **El share del bloque como pronóstico** (fila 1): el ≈0,99 de la Fase 0 usa la línea
  observada. Donde se usa solo, da −0,38.
- **El desvío individual** (fila 2): descriptivo, y la ficha no es walk-forward.
- **El paso de $P_i$ a la probabilidad de la cámara**: el número que ve el usuario
  ($P_{\text{aprob}}$) nunca se contrastó contra resultados en walk-forward con $P_i$
  pronosticadas; el único backtest agregado usa la línea observada.
- **β en el censo**: el harness no lo aplica, así que el skill publicado no incluye el término
  prendido del dictamen.
- **El gate $\mathcal{C}_c$, la proximidad electoral y la asimetría del ICG** (filas 11, 16, 17).
- **El ICG como predictor** (fila 10): medida su elasticidad, nunca su aporte al pronóstico.

## Dirección del sesgo en los parámetros estimados con offset contaminado

El argumento del prompt: un offset que conoce parte de la respuesta deja menos residuo, así que
(a) los coeficientes estimados encima (β, δ, θ, ψ) salen **atenuados** — conservadores — y (b)
τ sale **subestimado**. Lo que se verificó:

- **τ:** la dirección se confirma (1,146 con el motor con fuga → 1,186 con el harness viejo →
  1,197 limpio), pero el tamaño es de 1%. Lo que sí se mueve es ε₀ (0,015 → 0,055).
- **β:** mismo panel, misma especificación (M6), tres offsets. $F_i$: 2,09 (offset de la
  estimación) · 1,92 (harness con fuga) · **2,05 (limpio)**. Lealtad×jefe: 1,75 · 1,42 ·
  **1,29**. $F_i$ se porta como dice el argumento; **lealtad×jefe no: baja** con el offset
  limpio. Y el offset de la estimación **no era "demasiado bueno"**: tenía fuga, pero también le
  faltaban guard, encogimiento y origen, y su Brier (0,143) es peor que el limpio (0,135). **El
  razonamiento sobre la dirección del sesgo no se sostiene como regla**: depende de qué más le
  faltaba a cada offset. Por eso δ, θ y ψ no pueden darse por conservadores.
- δ, θ y ψ **no se re-midieron**.
