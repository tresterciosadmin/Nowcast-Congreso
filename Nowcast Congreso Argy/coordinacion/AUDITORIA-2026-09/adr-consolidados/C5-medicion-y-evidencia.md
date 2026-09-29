# C5 — Medición y evidencia

**BORRADOR** (auditoría 2026-09; no sustituye a ningún ADR hasta el OK de Franco) · **Absorbe:** 0015, 0032, 0034 · **Métodos heredados de:** 0028, 0031, 0033 (viven en C6 como historia)

## 1. La regla

> **Ningún término, constante o bandera afecta el número publicado sin una medición vigente:** hecha con el motor real (importado, no copiado), con historia de **fecha anterior y de otra ley**, con IC que **re-muestrea leyes**, comparada **de a pares** contra el estado anterior; y esa medición **se re-corre sola** cuando cambia el motor o un insumo. Lo que no se puede medir se declara *sin medición* y queda apagado (o en su valor neutro).

## 2. Por qué

En septiembre, tres mediciones distintas sostenían decisiones y las tres estaban rotas. **(a)** El skill del voto individual bajó de 0,1611 a **0,1333** [0,057; 0,198]: el harness armaba el récord con `shift(1)` por fila y era una copia del motor. **(b)** La banda [p5,p95] "cubría el 99,88%"; cubre el **63,6%** (5.851 actas): el backtest alimentaba al agregador con la línea que cada bloque tuvo *en esa misma acta*, un oráculo. **(c)** `RECORD_POR_TEMA` "mejoraba 11,06%"; con historia estricta da −2,9% y contra el motor empeora 2,1% [0,8; 3,5]. Además, el brazo `primaria` del cierre multitema (0028) era **idéntico a "sin tema"**: nunca le pasaba `tema` al motor, así que el efecto de un tema simple no se midió (las comparaciones multitema contra ninguno sí informan, pero con el harness con fuga) (`fa4c572`, diferencia pareada 0,0 exacto en 232 actas). Son **al menos tres mecanismos independientes**, no uno.

Los procesos no lo frenaron: los tres commits que prendieron términos (`ec5fd05`, `64ff248`, `0a7a03f`) cumplieron ADR-0015 —tocaron FORMULA, ESTADO, ADR y tablero— porque esa regla exige *presentar* el cambio, no *verificar la medición*; y FORMULA §IV.4 prescribía el idioma con fuga ("`shift(1)` + `expanding`").

Control que sostiene la regla: un récord propio armado **desde el voto crudo, sin importar el motor**, con origen, fecha estricta y otra ley, da **0,1335** (el motor, 0,1333), y **0,204** si se lo deja filtrar a propósito. El 0,1333 no es un artefacto del harness, y el propio control detecta fugas (`control_independiente.py`).

## 3. Cómo se verifica

| qué | dónde | estado |
|---|---|---|
| la historia no trae la respuesta (sintético) | `evaluacion/baseline/tests/test_historia_sin_fuga.py` | existe, pasa |
| el harness **es** el motor (238/238) | `evaluacion/baseline/tests/test_harness_es_el_motor.py` | existe, pasa |
| invariancia al futuro sobre actas reales (con control positivo) | `invariancia_al_futuro.py` → moverlo a `evaluacion/baseline/tests/` | propuesto |
| el motor no pierde contra un récord de 30 líneas | `control_independiente.py` | propuesto |
| todo parámetro que afecta el panel está en el registro con medición vigente | test contra el registro generado (`05` §5.3) | propuesto |
| una mejora no explicada es una alarma | gate pareado por ley (`05` §5.3) | propuesto |

## 4. Qué la invalida

- Un cambio en `ley_por_acta` (hoy **15,3% de los votos** caen en actas sin clave: cada acta es su propia ley; fuga residual estimada en **≈0,003** de skill si la tasa de leyes de varios días fuese la misma [I]).
- Que un insumo derivado con toda la historia (`disciplina_individual.csv`) entre al camino medido.
- Un cambio de Python o pandas que mueva resultados (esta PC corre 3.14 / pandas 3.0; el CI, 3.11).
- Un IC por ley que quede angosto frente al IC por fecha de sesión o por mes (medido: hasta **+29%** más ancho por mes en un efecto chico).

## 5. Estado real hoy (verificado)

- **Cumple:** el harness importa el motor (`baseline_voto_individual.py:535-536`), historia estricta (`:497-505`), IC por ley (`:402,422`). Pero con **300 réplicas y semilla fija** (`n_boot=300, seed=7`), y sin sensibilidad por fecha.
- **Sin medición vigente que dependa del motor real:** β (coeficientes con offset contaminado; el censo no lo aplica), ε₀ y τ (estimados sobre el mismo panel; ε₀ óptimo limpio **0,055** contra 0,035 en producción), la presencia, la ficha de desvío (toda la historia; acotada en ≤0,002 de Brier) y el guard de era con el **motor completo** (la medición independiente lo deja en +2% de Brier a favor [incluye 0], cero en la era vigente).
- **Diez scripts de estimación** con offset espejo declarado (`estimar_*`, `validar_*`, `diagnostico_senado`, `fase1_*`, `medir_rec_por_tema`, `medir_guard_era`).
- **Ningún test fija el valor** de `RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0` ni `TAU`.
- **`tests/test_insumos_del_motor_viajan.py` falla en `HEAD`:** el detalle del censo, que produce el 0,1333 y τ, existe sólo en un disco.
- **Documentos:** el panel HTML publicado dice 98,01% (= 0,99², el techo del clip) y su titular lo calcula un JavaScript aparte (regenerado da 98,0%; el motor, 61,3%); `tablero_datos.js` afirma a la vez 63,6% y 99,88%. Los controles "el número publicado no se movió (0,9801)" **no podían fallar**.

**Lo que esta regla reemplaza:** ADR-0015 (presentar el cambio en tres niveles) pasa a ser *una entrada en el registro con medición*; FORMULA §IV.4 y §IV.6 se reescriben con "fecha estricta y otra ley; IC por ley" y sin `shift(1)`.

*Historia:* 0015 (25-08, Claude/Franco) → tres niveles; 0032 (21-09, Claude delegado) → la unidad es el expediente; 0034 (28-09, Claude delegado) → la fuga y el espejo. **Se pierde:** los "tres niveles" como texto obligatorio; el "~1,7×" de 0032, que no está derivado en ninguna medición encontrada [N].
