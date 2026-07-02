# ADR-0003 — modelo/voto_individual: de "predecir el voto" a "desvío individual + pivotes"

- **Fecha:** 2026-07-01
- **Estado:** aceptada
- **Decisores:** Valle (replanteo), Claude (implementación)
- **Contexto previo:** módulo CONGELADO desde Fase 0 (baseline "votá con tu bloque" ≈ 0,99 en dirección → callejón sin salida para ML).

## Contexto

El 0,99 del baseline es un **promedio** que tapa a los díscolos. El conteo agregado de una votación (p. ej. 120/257) es un punto, pero su varianza real la cargan 10–20 legisladores "bisagra" cuya (in)disciplina puede mover contundentemente la P(aprobación) en votaciones ajustadas. Además, en 2024–2025 la disciplina partidaria se afloja, lo que amplía el espacio útil para este modelo.

## Decisión

Se **descongela** `modelo/voto_individual` y se reformula su objetivo: NO predecir el voto medio (eso lo resuelve la regla de bloque), sino **separar dos comportamientos** y modelar el **desvío del legislador respecto de su bloque**.

Dos productos distintos (distinguir partido ≠ bloque ≠ parlamentario):

1. **Partidario/bloque** — posición esperada del bloque, para recuento agregado y análisis macro (ya medido en Fase 0).
2. **Individual/parlamentario** — cuatro piezas:
   - (a) **índice de disciplina individual** por legislador (tasa de desvío vs. bloque, global y por tema, time-aware);
   - (b) **modelo de defección** P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral);
   - (c) **recuento como distribución** — simular cada voto Bernoulli(pᵢ) = posición de bloque ajustada por desvío → distribución del conteo con intervalo, no número puntual;
   - (d) **detección de pivotes** — qué legisladores son bisagra para una ley y cuánto mueve cada uno la P(aprobación).

## Gates

1. Dimensionar el set pivote: cuántos legisladores superan un umbral de divergencia vs. su bloque (sobre la base canónica).
2. El recuento como distribución calibra mejor que el punto del baseline en votaciones ajustadas (backtesting walk-forward, sin leakage).

## Aclaración de alcance (2026-07-01, replanteo de Valle)

Los díscolos son el **ejemplo motivador**, no el objetivo completo. El objetivo es el **análisis individual de cada legislador**: una base de datos con la ficha de cada diputado/senador (identidad, trayectoria de bloques, presentismo, perfil de voto, y también su desvío). Esa base vive en `variables/legislador` y consume la salida de este módulo como un atributo más. Este ADR cubre solo la parte de modelado del desvío/pivotes.

## Consecuencias

- `modelo/voto_individual` vuelve a "Disponible/En curso" en TABLERO; README del módulo se actualiza (deja de decir CONGELADO).
- Depende de `datos/canonica`; consumirá `variables/legislador` y `variables/bloque` cuando existan.
- Lo que sigue cerrado es predecir la *dirección media* del voto: ese benchmark queda como referencia fija.
