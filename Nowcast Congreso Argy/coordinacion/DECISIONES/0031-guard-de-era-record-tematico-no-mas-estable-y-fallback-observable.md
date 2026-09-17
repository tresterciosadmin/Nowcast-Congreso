# ADR-0031 — El récord temático NO es más estable entre gobiernos que el general (la objeción de Franco al guard de era se testeó y no se sostiene); el fallback silencioso deja de serlo

**Fecha:** 2026-09-17 · **Estado:** FASE 1 — objeción testeada, NO SOSTENIDA (guard de
era sin cambios). FASE 3 — IMPLEMENTADA Y PRENDIDA (observabilidad, no cambia ninguna
predicción) · **Decide:** Claude, sesión delegada por Franco
(`coordinacion/PROMPT-GUARD-DE-ERA-POR-TEMA.md`) · **Toca:**
`modelo/ensemble/src/nowcast_puertas.py` (`alineacion_individual_por_area`, `nowcast()`),
`modelo/ensemble/tests/test_record_por_tema.py`, `evaluacion/baseline/src/
medir_estabilidad_record_por_tema.py` (nuevo) · **Se relaciona con:** ADR-0018 (guard de
era, sin cambios — este ADR lo confirma con una prueba nueva), ADR-0026 (récord por tema),
ADR-0030 (el 0,0% que motivó esta sesión)

## Resumen ejecutivo

**FASE 1 mide, con criterio escrito antes de medir, si la objeción de Franco se sostiene
— y no se sostiene.** El récord POR TEMA no correlaciona más entre gobiernos que el
récord GENERAL: pooled sobre los 3 recambios de la canónica (2015, 2019, 2023),
correlación temática **−0,12** (n≥5) contra general **−0,02** — la temática es, si
acaso, **peor**, no mejor (brecha −0,10, cuando la hipótesis predecía ≥+0,15). **No se
implementa el diseño B ni C. El guard de era queda exactamente como estaba (ADR-0018).**

Con eso, **ADR-0030 queda confirmado como cierre definitivo, no "suspendido"**: la línea
de pivotes por capítulo no se reabre por este camino (el camino que sigue abierto es
PRUEBA 2 de ADR-0030, la reconstrucción por rango de artículos — no relacionado con el
guard). Y la decisión de cobertura de ADR-0030 (97,26% del universo vivo sin tema) queda
igual: el guard no estaba escondiendo valor en los datos ya clasificados.

**FASE 3 sí se implementó, sí se prendió, y es independiente del resultado de FASE 1**
(aprobado así por Franco): `alineacion_individual_por_area` dejó de degradar en
silencio. Cada salida de la función ahora loguea cuántos legisladores resolvió con dato
real, y `nowcast()` expone esa fracción en su payload (`record_por_tema.
frac_condicionado_real`). El **0,0%** de ADR-0030 hoy se vería en el momento, no
después de una sesión entera de diagnóstico.

## FASE 1 — ¿El récord temático es más estable entre recambios de gobierno?

### Metodología

`evaluacion/baseline/src/medir_estabilidad_record_por_tema.py`. Para cada uno de los 3
recambios que reconoce `definiciones.GOBIERNOS` (2015-12-10, 2019-12-10, 2023-12-10 —
antes de 2015 la canónica entera cae en una sola era "KIRCHNER", no hay un cuarto
recambio que medir) y para cada legislador que **atraviesa** el recambio
(continuador, con voto a los dos lados):

- **Temática:** por (legislador, área), tasa afirmativa ANTES vs. DESPUÉS del recambio.
- **General (contraste):** por legislador, tasa afirmativa ANTES vs. DESPUÉS, sin área.
- **Encogimiento Empirical-Bayes (k=5) antes de correlacionar**, cada lado hacia el
  promedio de SU PROPIA ventana (no un promedio global mezclando eras) — sin esto la
  correlación queda atenuada por ruido de muestra chica, como avisaba el prompt.
- **Pares (legislador, área), no promedios agregados** — promediar primero borra
  exactamente la variación que se quiere medir.
- Tres umbrales de n mínimo **a los dos lados** (≥3, ≥5, ≥10), reportados todos, no uno
  elegido a mano.

### Resultado — pooled (los 3 recambios juntos)

| | n≥3 | n≥5 | n≥10 |
|---|---:|---:|---:|
| **correlación TEMÁTICA** | −0,073 | **−0,116** | −0,185 |
| correlación general (contraste) | −0,017 | −0,018 | −0,021 |
| pares evaluados (temática) | 4.230 | 3.123 | 1.909 |

**La temática es NEGATIVA en los tres umbrales, y empeora (más negativa) cuanto más
exigente el umbral de muestra** — no es ruido que se diluye con más datos, es una
tendencia que se sostiene con más datos. La correlación general, en cambio, está cerca
de cero pero más estable. **Brecha (temática − general) en n≥5: −0,098** — la
hipótesis predecía ≥+0,15. Falla por el lado contrario al esperado, no por poco margen.

### Por recambio (heterogeneidad temporal)

| recambio | temática n≥5 | general n≥5 | continuadores |
|---|---:|---:|---:|
| 2015-12-10 (K→Macri) | −0,128 | −0,155 | 221/1.440 (15,4%) |
| 2019-12-10 (Macri→AF) | −0,125 | **+0,200** | 214/464 (46,1%) |
| **2023-12-10 (AF→Milei)** | **+0,053** | −0,206 | 210/469 (44,8%) |

**2023, la era que importa para el producto, es la ÚNICA donde la temática le gana a la
general** (+0,053 vs. −0,206) — pero **ninguna de las dos** se acerca a 0,30, y menos a
0,50. Ganarle a un contraste que está en terreno claramente negativo no es lo mismo que
tener señal real: la temática en 2023 es, en el mejor de los tres recambios, apenas
distinguible de cero.

### Por área (heterogeneidad sustantiva — el resultado más interesante, sin cambiar el veredicto)

Sobre 2023 específicamente (n≥5, muestras chicas por área — 25 a 91 pares, **leer como
color, no como conclusión**):

| estables (correlación > 0,45) | inestables o invertidas (< −0,40) |
|---|---|
| SALUD +0,58 · TRAB +0,55 · EDU +0,45 | JUST −0,55 · POLINST −0,54 · DEF −0,51 · DESREG −0,42 |

**Patrón coherente, no ruido puro:** las áreas que se politizan directamente con la
agenda del gobierno de turno (justicia, instituciones, desregulación, defensa) son las
que MÁS se invierten entre gobiernos — exactamente lo contrario de lo que predecía la
objeción para esas áreas. Las áreas de política social (salud, trabajo, educación)
muestran algo de persistencia real. **Esto no cambia el veredicto pooled** (la mayoría
de las áreas y de los recambios no muestran el patrón fuerte que haría falta), pero es
un cabo suelto legítimo para una revisión futura MÁS FINA que un diseño global — no se
persigue en esta sesión, el criterio de decisión era sobre el agregado.

### Composición del universo — sesgo de supervivencia, medido y declarado

Los continuadores **no** son una muestra al azar de la cámara: en el recambio 2015,
28,1% de los continuadores viene de bloques `OTRO / PROVINCIAL` contra 70,8% de TODOS
los activos antes del recambio — o sea, los continuadores están **subrepresentados**
en bloques provinciales respecto del universo general en ese corte (2015 tuvo un
recambio de cámara muy grande, 1.440 activos "antes" contra sólo 221 continuadores,
15,4%). En 2019 y 2023 la composición es casi idéntica entre continuadores y universo
general (15-17% en ambos casos) — el sesgo de 2015 es un caso particular de ESE
recambio (una cámara mucho más golpeada por el recambio), no un patrón general.

### Caso Pichetto (spot check, no parte del criterio de decisión)

`leg:5daaefa4774c` — 22 años activo, ambas cámaras, 3.027 votos. En el recambio
2015-12-10 (el único con datos suficientes en su historia para este corte), sus 13
áreas medidas muestran **share_despues = 1,0 en 12 de las 13** (2 a 20 votos por área
en la ventana corta post-recambio) — casi todo afirmativo, sin distinguir área, en una
ventana todavía chica. No alcanza para sacar una conclusión individual (es 1 persona,
la pregunta la responde el agregado), pero tampoco contradice el resultado pooled: no
hay una persistencia temática distintiva visible ni siquiera en el caso que motivó la
objeción.

### ✅ Veredicto FASE 1 (criterio escrito antes de medir)

| | resultado | umbral | veredicto |
|---|---:|---|---|
| correlación temática (pooled, n≥5) | **−0,116** | ≥0,50 | **NO CUMPLE** |
| correlación general — contraste | −0,018 | — | — |
| brecha (temática − general) | **−0,098** | ≥0,15 | **NO CUMPLE (signo contrario)** |

**Temática < 0,30 en los tres umbrales y en el pooled → "el guard tiene razón también
para el tema" (tercera fila del criterio). La objeción no se sostiene — con los datos
que hay hoy.** No se implementa el diseño B (nunca resetear) ni C (resetear sólo a los
nuevos). El guard de era (ADR-0018) queda **exactamente como estaba**, sin ninguna
enmienda de diseño.

## Qué esperaba y salió distinto

Se esperaba, en el peor caso, una correlación temática baja pero **positiva** y
parecida a la general (guard "también tiene razón, sin sorpresas"). Salió **negativa**
en casi todos los cortes, y en dos de los tres recambios **peor** que el contraste
general — lo opuesto a lo que predecía la objeción, no simplemente "sin evidencia a
favor". La heterogeneidad por área (positiva en salud/trabajo/educación, fuertemente
negativa en justicia/institucional/desregulación/defensa) tampoco estaba anticipada
con esa nitidez, y sugiere que la posición de un legislador en las áreas más
"politizadas por el gobierno de turno" es, si acaso, MENOS estable que su relación
general con el Ejecutivo — un resultado interesante en sí mismo, ortogonal al guard.

## FASE 2 — no se ejecuta

FASE 1 falló el criterio de entrada; por diseño del prompt, FASE 2 (implementar B o C,
backtest sobre el censo) no corresponde. Nada del motor cambia de comportamiento
predictivo en esta sesión.

## FASE 3 — el fallback silencioso, implementado y prendido

`alineacion_individual_por_area` (`modelo/ensemble/src/nowcast_puertas.py`) tenía
**cuatro** puntos de salida que degradaban a `dict(ind_general)` (récord general puro,
sin condicionar por tema) sin loguear nada — el mismo patrón que ya costó una sesión
completa: `_ContadorAvisos` existe para el parser del Senado, `combinar_temas` avisa
cuando cae a incondicional, pero esta función no avisaba nunca.

**Qué cambió:**
1. **Cada salida logea una línea agregada** (`logger.info`, no una por fila —
   `"X/Y legisladores con dato condicionado real (Z%) -- <motivo>, caigo a récord
   general"`), con un motivo distinto por cada uno de los 4 puntos de fallback (sin
   áreas objetivo válidas; sin votos en la ventana; `cond_por_acta` sin `todas_ids`;
   cero actas de la ventana matchean las áreas) más una quinta línea en el camino de
   éxito (parcial o total) reportando la fracción real.
2. **`devolver_stats=True`** (nuevo parámetro, default `False`, retrocompatible byte a
   byte con todo caller existente): devuelve `(dict, stats)` con
   `{n_con_dato_real, n_total, frac_condicionado_real}`.
3. **`nowcast()` expone `record_por_tema`** en su payload: `{activo, areas_objetivo,
   frac_condicionado_real, n_con_dato_real, n_total}` cuando `RECORD_POR_TEMA` está
   prendido y el proyecto tiene multietiqueta resuelta; `{"activo": False}` si no aplica.
   **Observable desde afuera, no sólo desde un script de diagnóstico** — el pedido
   explícito del prompt.

**Otros fallbacks revisados en el mismo camino** (petición explícita: "buscalo, no
esperes a que muerda de nuevo"): `perfil_legislador` YA es observable —cada perfil
lleva `fuente_direccion` ("bloque" / "record_individual" / "record_individual_encogido")
en el payload de `armar_roster`, no degrada en silencio—; `alineacion_individual`
(récord general) ya está cubierto por el warning existente de `_alineacion_base` cuando
la ventana queda vacía. No se encontraron otros puntos de fallback silencioso en
`nowcast_puertas.py` ni en `ensemble.py`.

**No cambia ninguna predicción.** Es 100% aditivo: nuevo campo de diagnóstico, nuevos
logs, ningún valor de `p_afirma_si_vota` ni de `p_aprobacion` se mueve. Por ADR-0015,
`FORMULA-COMPLETA.md` se actualiza en el mismo commit con una nota (§II.5): la fórmula
en sí **no cambia**, sólo su observabilidad.

## Verificación

`modelo/ensemble/tests/test_record_por_tema.py` — 5 tests nuevos: fallback total
reporta `0/N` explícito (no lo esconde); dato real reporta la fracción correcta;
`cond_por_acta=None` también devuelve stats cuando se piden; `devolver_stats=False`
sigue devolviendo sólo el dict (retrocompatible); **caso Pichetto** — un legislador con
20 actas ECON reales TODAS antes de un recambio no cuenta como dato condicionado
DESPUÉS del recambio, con el guard prendido (confirma el diseño A vigente, no lo
cambia). **18/18 OK.** `test_nowcast_puertas.py` (49/49) y `test_tema_auto.py` (9/9)
sin regresión.

## Qué habilita y qué cierra esto

- **Capítulos (ADR-0030): queda CERRADO, ya no "suspendido detrás del guard".** El
  guard no estaba cortando información válida — no hay historia recuperable de
  Pichetto ni de nadie por este camino. Sigue abierto, sin relación con este ADR, el
  único camino que ADR-0030 dejó concreto: PRUEBA 2 (reconstrucción por rango de
  artículos, 23 proyectos).
- **Cobertura de temas: sin cambios respecto de ADR-0030.** El guard no estaba
  escondiendo valor en los 273 proyectos del universo vivo ya clasificados — la
  decisión de ampliar cobertura (97,26% sin tema) sigue pendiente de Franco, con el
  mismo número que ya tenía.
- **Nuevo, no anticipado:** la heterogeneidad por área (persistencia en salud/trabajo/
  educación, inversión en justicia/institucional/desregulación/defensa) queda anotada
  como pista para una eventual revisión de diseño MÁS FINA — no se persigue ahora, no
  hay pedido de Franco para hacerlo, y el criterio de esta sesión era sobre el agregado.
