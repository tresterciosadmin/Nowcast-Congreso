# ADR-0015 — Todo cambio al motor se presenta en la fórmula completa

**Fecha:** 2026-08-25 · **Estado:** Aceptada · **Quién:** Franco (decisión), Claude (registro)

## Contexto

La revisión metodológica del 25-08 encontró cuatro problemas de modelo que llevaban
semanas en producción sin que nadie los viera. Ninguno era un bug de programación:
eran **supuestos** —independencia entre cámaras, simetría del logaritmo, el quórum sin
abstenciones, el épsilon como clip— y los supuestos no se ven leyendo un diff.

El patrón que los hizo invisibles es el mismo en los cuatro casos: cada cambio se
presentó, se revisó y se aprobó **como una función aislada**. `ajuste_paso_origen`
funciona bien. `_prob_conductas` funciona bien. `simular_votacion` funciona bien. Lo
que nadie miraba era **qué le hace cada una a la fórmula general**, y ahí es donde
vivían los problemas.

Un ejemplo concreto de esta misma sesión: la eliminación del mecanismo 2 del ICG
(11-08) fue correcta —duplicaba la señal— y se presentó como tal. Pero **se llevó
puesta la asimetría de la teoría prospectiva**, que vivía adentro. Nadie lo notó
durante dos semanas porque el cambio se discutió a nivel del módulo del ICG, no a
nivel de qué produce el motor.

## Decisión

**Todo cambio que toque el motor se presenta en TRES niveles, en este orden.**

Motor = `modelo/ensemble`, `modelo/agregador_institucional`, `modelo/voto_individual`,
`variables/bloque`, `variables/proyecto` (modulador y origen) y `variables/embudo`.

### Nivel 1 — la función

Qué hace ahora, qué hacía antes, y por qué. Es lo que ya se venía haciendo.

### Nivel 2 — el motor en su conjunto

Qué otras piezas consumen lo que cambió, y qué les pasa. Como mínimo:

- **quién lee** la salida modificada (`.mapa/buscar.py --archivo <ruta>` lo responde);
- si el cambio **mueve el número publicado** o sólo el desagregado;
- si algún **contrato** cambia de forma (columnas, rangos, semántica);
- qué **supuesto** se agrega, se saca o se modifica sin querer.

### Nivel 3 — la fórmula

**Cómo queda la fórmula general después del cambio**, escrita completa, con el
término tocado señalado. Referencia: `coordinacion/FORMULA-COMPLETA.md`.

Si el cambio no se puede ubicar en la fórmula, **es señal de que no se entiende del
todo qué se está cambiando** — y ese es justamente el momento de frenar, no de
mergear.

## Por qué así

- **Los supuestos sólo se ven en la fórmula.** "El quórum descarta las abstenciones"
  es invisible en `agregador.py:154` y evidente cuando se escribe
  `Presentes = A + N` al lado de la definición de quórum.
- **Obliga a mirar el radio de impacto.** Los cuatro hallazgos del 25-08 aparecieron
  al recorrer la cadena entera, no al leer un archivo.
- **Deja el rastro que el proyecto ya valora.** Igual que `URGENTE.md` para lo que
  bloquea y los ADR para lo que se decide, la fórmula es el registro de **qué está
  midiendo el sistema**.
- **Cuesta poco.** Tres párrafos y una fórmula. Contra semanas de un supuesto falso en
  producción, es barato.

## Consecuencias

1. `coordinacion/FORMULA-COMPLETA.md` es el documento vivo de la fórmula. **Quien
   cambia el motor lo actualiza en el mismo commit**, igual que `ESTADO` y el tablero.
2. Si la fórmula queda desactualizada, vale la regla de las bitácoras vencidas del
   mapa: **una fórmula que miente es peor que no tenerla**, porque se le cree.
3. Un cambio que no altera la fórmula igual declara el Nivel 3, con una línea: *"la
   fórmula no cambia"*. Es información, no trámite.
4. Aplica también a los cambios que **apagan** algo (coeficientes en cero, banderas en
   `False`): el término sigue en la fórmula, marcado como inactivo. Así no se pierde
   —como pasó con la asimetría del ICG— lo que se sacó y por qué.
