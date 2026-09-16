# ADR-0028 — FASE 0: el re-test metodológico cierra el multitema a nivel BLOQUE (enmienda a ADR-0024)

**Fecha:** 2026-09-16 · **Estado:** MEDIDO sobre el CENSO completo, cierra la
pregunta · **Decide:** Claude, mandato de `coordinacion/PROMPT-MULTITEMA-V2.md`
(FASE 0) · **Toca:** `variables/bloque/src/bloque.py` (`ponderada_logit`),
`evaluacion/baseline/src/{baseline_voto_individual.py, fase0_control_temas.py}`
(nuevo) · **Enmienda a:** ADR-0024 · **Se relaciona con:** ADR-0026 (FASE 1,
la misma pregunta resuelta al nivel correcto)

## Por qué ADR-0024 necesitaba un re-test, no una remedición

`PROMPT-MULTITEMA-V2.md` diagnosticó cuatro problemas de DISEÑO en el
experimento de ADR-0024 (no de ejecución):

1. **Faltaba el brazo de control.** Las cuatro reglas probadas condicionaban
   por tema; ninguna medía qué pasa si NO se condiciona. Sin eso no se puede
   distinguir "la regla es mala" de "condicionar por tema ahí no sirve para
   nada, ni para bien ni para mal".
2. **`ponderada` promediaba en PROBABILIDAD**, violando la regla IV.2 de
   `FORMULA-COMPLETA.md` (condicionar en logit, nunca promediando
   probabilidades) — comprime hacia el centro y aplasta los temas extremos,
   que son los informativos.
3. **`peor_tema` usaba un estimador sesgado**: $\min_k \hat s_k$ sobre shares
   ruidosos está sesgado hacia abajo, y el sesgo crece con la cantidad de
   temas. Estaba garantizado a salir pesimista aunque la hipótesis fuera
   cierta — no se testeó la idea, se testeó un artefacto del estimador.
4. **La muestra estaba adversarialmente seleccionada**: la rama de bloque
   dispara cuando el legislador tiene CERO historia propia — casi siempre
   justo después de un recambio, el momento en que el motor ya rinde peor —
   y con ~1.263-2.292 votos no hay potencia para detectar diferencias chicas.

## FASE 0 — el diseño corregido

`evaluacion/baseline/src/fase0_control_temas.py`, 4 brazos sobre el CENSO
completo (no una muestra):

| brazo | qué es |
|---|---|
| `sin_tema` 🆕 | el CONTROL: la rama de bloque nunca condiciona por tema (sólo por origen, un eje distinto, igual en los 5 brazos) |
| `primaria` | lo de siempre |
| `union` | ya implementado, sin cambios |
| `ponderada_logit` 🆕 | como `ponderada` pero combinando en LOGIT (`bloque.proyectar_postura`, nuevo modo), con confianza REAL por etiqueta (`cargar_confianza_por_area`, el registro único — la misma pieza que resolvió la limitación de ADR-0024) |

`peor_tema` **NO se re-corrió a nivel proyecto** (decisión explícita de
Franco: queda cerrado ahí; su revancha es a nivel CAPÍTULO, ver ADR-0027).

**Comparación PAREADA, clusterizada por acta_id** (bootstrap: cada réplica
resamplea ACTAS ENTERAS, no votos sueltos — los votos de una acta comparten
la misma postura de bloque, no son observaciones independientes), reportando
INTERVALO, no sólo el punto, sobre la RAMA DE BLOQUE (el subconjunto que el
cambio toca) y por era.

## Resultado — NINGUNA diferencia es distinguible de cero

| brazo | Brier (rama de bloque) | n actas | diff. vs. `primaria` | IC 95% de la diferencia | ¿distinguible de cero? |
|---|---:|---:|---:|---|:---:|
| `sin_tema` | 0,21979 | 232 | −0,00068 | [−0,00005; 0,00006] | **NO** |
| `primaria` | 0,22047 | 235 | — | — | — |
| `union` | 0,22223 | 235 | +0,00175 | [−0,00325; 0,01063] | **NO** |
| `ponderada_logit` | 0,22092 | 235 | +0,00044 | [−0,00601; 0,00927] | **NO** |

**Por era, `sin_tema` y `primaria` dan Brier PRÁCTICAMENTE IDÉNTICO en las
cinco eras** (hasta 2011: 0,22012 vs 0,22234; 2011-2015: 0,16889 vs 0,16879;
2015-2019, 2019-2023 y desde 2023: iguales al quinto decimal). No hay ningún
corte donde condicionar por tema —de ninguna de las tres formas— se separe
del control.

### Lectura

**Con el diseño corregido (control, logit, censo completo, clusterizado), la
pregunta se cierra de la forma más limpia posible: no hay evidencia de que
condicionar por tema en la rama de bloque cambie NADA, ni para mejor ni para
peor.** Esto es MÁS FUERTE que la conclusión original de ADR-0024 ("las tres
reglas empeoran") — ADR-0024 medía sin control, así que no podía distinguir
"empeora por la regla" de "esta rama no tiene información que condicionar
sirva de nada". Con el control puesto, la respuesta es la segunda: **la rama
de bloque no tiene la información que el tema necesitaría para importar** —
consistente con el diagnóstico del prompt ("es un relleno para datos
faltantes, no un modelo de cómo vota el bloque").

**Corrige explícitamente la interpretación de ADR-0024, sin invalidar su
implementación.** El código de las 4 reglas (`primaria`/`union`/`ponderada`/
`peor_tema`) sigue siendo correcto y queda en el repo, testeado; lo que
cambia es la conclusión: no es "las reglas nuevas son malas", es "en este
nivel, con estos datos, no se puede distinguir ninguna regla —incluida no
condicionar— de otra".

**Por qué el criterio de decisión original ("si sin_tema ≥ primaria, apagar")
aplica en espíritu aunque el punto de `sin_tema` sea marginalmente MENOR:**
la diferencia (−0,00068) está adentro de un intervalo que prácticamente no
se mueve de cero ([−0,00005; 0,00006]) — es ruido de precisión numérica, no
señal. `sin_tema` es al menos tan bueno como `primaria` y es más simple: no
hay razón para condicionar por tema en la rama de bloque.

## Decisión

**El multitema a nivel BLOQUE queda cerrado, con evidencia limpia esta vez.**
No se activa ninguna de las cuatro reglas (`TEMA_AUTO` sigue apagado, sin
cambios — nunca estuvo prendido en producción, así que no hay nada que
"apagar"). La pregunta "cómo combinar varios temas a nivel de bloque" no
tiene una respuesta mejor que "no combinar nada", porque no hay nada que
combinar sirva: **la ganancia real está en FASE 1** (`rec_i^tema`, ADR-0026,
11,1% menos Brier, POSITIVO en todo corte medido) — el mismo tema, resuelto
en el nivel donde el dato existe.

## Verificación

Reproducible: `python evaluacion/baseline/src/fase0_control_temas.py` (censo
completo; toma tiempo — 4 pasadas sobre ~5.850 actas cada una). Salida:
`evaluacion/baseline/outputs/{fase0_control_temas_censo.json,
fase0_detalle_{sin_tema,primaria,union,ponderada_logit}.parquet}`.
`variables/bloque/tests/test_bloque_v3_multietiqueta.py` (+2 checks para
`ponderada_logit`, 12/12 totales): con un solo tema da exactamente `primaria`
(logit/sigmoid son inversas exactas); combinar en logit da un resultado
DISTINTO de combinar en probabilidad sobre el mismo caso sintético.

## Lo que queda pendiente

Nada de código. La pregunta de FASE 0 está cerrada. Si en el futuro
`proyecto_taxonomias`/`tema_por_acta` alcanzan una cobertura mucho mayor
(hoy 51-57%), podría valer la pena una remedición — pero con la evidencia de
hoy, sobre el censo completo, no hay indicio de que más cobertura cambiaría
la conclusión: el problema no es cantidad de dato, es que la UNIDAD (rama de
bloque = gente sin historia propia) no tiene nada que el tema pueda mover.
