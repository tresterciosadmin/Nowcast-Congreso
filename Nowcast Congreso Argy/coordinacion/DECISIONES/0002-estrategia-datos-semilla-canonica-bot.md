# ADR 0002 — Estrategia de datos: semilla histórica → base canónica propia → bot incremental

**Fecha:** 2026-06-25 · **Estado:** Aceptada

## Contexto
La carpeta "Aportes sobre dataset congreso" suma el trabajo de Andy Tow ("La Década Votada") y el paquete R **legislAr**, con votos individuales por bloque desde 1998 e historia de Senado 2004–2013. Nuestras otras fuentes: CKAN (Diputados 2011–2020, congelado), argentinadatos (Diputados 2020–2025, Senado 2024–2025). Decisión del equipo: **no copiar ni depender en vivo de Andy Tow**, sino usar su trabajo para arrancar y luego perfeccionar y mantener nuestra propia base.

## Decisión
1. **Andy Tow / legislAr = semilla de un solo uso.** Se exporta una vez a parquet (`datos/decada_votada`) y no se vuelve a depender de su actualización.
2. **Base canónica propia (`datos/canonica`).** Una sola tabla normalizada que unifica todas las fuentes, deduplica los solapamientos y resuelve entidades (legislador/bloque). Es la fuente de verdad del proyecto.
3. **Bot incremental (`datos/bot_recoleccion`).** Proceso programado e idempotente que detecta votaciones nuevas en las fuentes oficiales y las agrega a la canónica. Es lo que nos vuelve autónomos hacia adelante.
4. **Límite R↔Python.** legislAr corre en **R**, solo para el export semilla. Todo el resto (canónica, bot, variables, modelos) en **Python**. No se reimplementa el scraping de legislAr; no se mezclan stacks dentro de un módulo.

## Cobertura resultante y hueco conocido
| Cámara | Semilla (Andy Tow) | CKAN | argentinadatos | Combinado |
|---|---|---|---|---|
| Diputados | 1998–2019 | 2011–2020 | 2020–2025 | ~2001–2025 |
| Senado | 2004–2013 | — | 2024–2025 | **hueco 2014–2023** |

El **hueco de Senado 2014–2023** queda como tarea de búsqueda/scraping aparte (`datos/senado`).

## Consecuencias
- Más profundidad histórica ⇒ mejor backtesting sobre varios recambios y rupturas de bloque.
- Trabajo nuevo: deduplicación entre fuentes solapadas (Diputados 2011–2019 aparece en semilla y CKAN) y entity resolution — concentrado en `datos/canonica`.
- Dependencia operativa pasa de "que Andy Tow actualice" a "que el bot corra"; hay que monitorear caídas de las fuentes oficiales.
