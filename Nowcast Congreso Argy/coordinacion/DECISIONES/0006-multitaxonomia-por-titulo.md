# ADR-0006 — Multi-taxonomía por TÍTULO: la unidad de análisis no siempre es el proyecto

**Fecha:** 2026-07-31 · **Estado:** ACEPTADO (diseño) / PENDIENTE (implementación)
**Decisor:** Franco · **Registra:** Claude
**Disparador:** corrida del caso `casos/2026-07-31_ley-de-lobby.md`

---

## Contexto

Hoy el modelo asigna taxonomías **al proyecto entero** y calcula **una** probabilidad por
proyecto. Eso funciona para un proyecto monotemático como la Ley de Lobby (47 artículos,
todos sobre gestión de intereses → `POLINST.ETICA`).

**No funciona para las leyes ómnibus**, que bajo este gobierno son la forma habitual en que
el Ejecutivo manda las reformas grandes. Casos concretos que motivan el ADR:

- **Ley Bases (enero 2024):** los títulos de **reforma política** tuvieron una suerte
  distinta del resto de la ley. Se cayeron capítulos enteros mientras otros avanzaban.
- **Capítulos fiscales** insertos en proyectos cuyo tema principal es otro.
- **Presupuesto 2026:** los artículos sobre **universidades** se discutieron con una
  dinámica política propia, ajena al resto del presupuesto.

Un solo número para toda la ley oculta lo que importa: **qué partes sobreviven**. Y una
sola etiqueta temática es directamente falsa cuando la ley toca ocho áreas.

## Decisión

**La unidad de análisis pasa a ser jerárquica: proyecto → título/capítulo.**

1. **Taxonomía multi-nivel.** El proyecto conserva sus taxonomías agregadas (contrato
   actual, no se rompe), y se agrega un nivel por **título/capítulo** con su propio conjunto
   de ids del vocabulario controlado.
2. **Probabilidad por título.** Cada título puede recibir su propia `p_sancion`. La del
   proyecto deja de ser un escalar y pasa a ser la del *articulado que sobrevive*.
3. **El desglose es parte del output.** Un proyecto ómnibus se reporta como "la ley tiene
   X%, pero el título de reforma política tiene Y% y el fiscal Z%".

## Por qué así

- **Es donde está la política.** La negociación legislativa argentina no aprueba o rechaza
  paquetes: los **desguaza**. Modelar el paquete entero es modelar algo que no ocurre.
- **El dato existe.** Los textos del PE vienen estructurados en TÍTULO / CAPÍTULO /
  ARTÍCULO de forma regular y parseable (el PDF de la Ley de Lobby tiene 9 títulos
  perfectamente delimitados).
- **No rompe nada.** El nivel proyecto sigue existiendo; el nivel título se agrega.

## Trabajo pendiente (no estimado)

- Parser de estructura (TÍTULO/CAPÍTULO) sobre el texto del proyecto → tabla
  `proyecto_titulos`.
- Extender `agente_taxonomias.py` para clasificar por título además de por proyecto.
- **El problema difícil: el target.** Para entrenar "probabilidad por título" hace falta
  saber qué títulos sobrevivieron históricamente — comparar el texto presentado contra el
  sancionado. Es un problema de diff de textos legales, no de scraping. Ley Bases es el
  caso de prueba obvio: está el antes y el después.
- Mientras no exista ese target, el desglose por título puede entregarse igual de forma
  **cualitativa** (qué áreas toca cada título, cuál es más conflictivo por historia del
  área), que ya es más de lo que hay hoy.

## Consecuencias

- El contrato `features_proyecto.parquet` gana un hermano a nivel título.
- El output estándar (ADR-0007) debe contemplar el desglose cuando el proyecto es ómnibus.
- **Riesgo asumido:** sin target por título, la probabilidad desagregada sería una
  estimación no validada. **No se publica un número por título hasta tener con qué
  backtestearlo** — se publica el desglose temático y el análisis, no la cifra.
