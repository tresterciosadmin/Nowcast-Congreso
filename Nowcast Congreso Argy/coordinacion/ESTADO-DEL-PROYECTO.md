# ESTADO DEL PROYECTO — documento vivo

> **Este archivo se actualiza en CADA modificación del repo.** Es la fuente de verdad de qué se hizo y cómo. Un PR que cambia algo y no agrega su entrada acá no se mergea.

## Cómo actualizarlo (obligatorio)
Agregá una entrada **arriba de todo** en la sección "Bitácora" con este formato exacto:

```
### [AAAA-MM-DD] <módulo> — <título corto>
- **Quién:** nombre o ID (ej. Claude-A / Franco)
- **Qué:** qué cambió, en una o dos frases.
- **Cómo:** enfoque técnico / decisiones clave / comando para reproducir.
- **Archivos:** rutas tocadas.
- **Estado del módulo:** PENDIENTE | EN CURSO | HECHO | CONGELADO.
- **Próximo paso:** qué queda, o "ninguno".
```

No borres entradas viejas. Si algo se revierte, agregá una entrada nueva explicándolo.

## Tablero de estado por módulo (resumen)
Mantené esta tabla sincronizada con la bitácora.

| Módulo | Estado | Owner |
|---|---|---|
| docs/schemas | HECHO (schema_version=1) | — |
| datos/decada_votada | EN CURSO (export_seed.R listo, falta correrlo en R) | — |
| datos/canonica | PENDIENTE (base propia, fuente de verdad) | — |
| datos/bot_recoleccion | PENDIENTE (depende de canonica) | — |
| datos/ckan_diputados | HECHO (en `fase0/`, migrar) | — |
| datos/argentinadatos | PENDIENTE | — |
| datos/senado | PENDIENTE (hueco 2014–2023) | — |
| datos/expedientes | PENDIENTE | — |
| variables/legislador | PENDIENTE | — |
| variables/proyecto | PENDIENTE | — |
| variables/bloque | PENDIENTE | — |
| variables/asistencia_quorum | PENDIENTE (prioritario) | — |
| variables/embudo | PENDIENTE (prioritario) | — |
| variables/contexto | FUTURO | — |
| modelo/voto_individual | CONGELADO (baseline ~0,99) | — |
| modelo/agregador_institucional | PENDIENTE | — |
| modelo/ensemble | PENDIENTE | — |
| evaluacion/baseline | HECHO | — |
| evaluacion/backtesting | PENDIENTE | — |
| evaluacion/metricas | PENDIENTE | — |
| producto/dashboard | PENDIENTE | — |
| producto/api | FUTURO | — |

---

## Bitácora (más reciente arriba)

### [2026-06-25] datos/argentinadatos + ckan_diputados — Cobertura 2011–2025
- **Quién:** Claude (sesión con Franco)
- **Qué:** integrado argentinadatos (Diputados 2020–2025, Senado 2024–2025) a la canónica y sumado el recurso CKAN período 137 para tapar 2019. Base: 1.414 actas, 340.892 votos.
- **Cómo:** bloque de Diputados resuelto cruzando el padrón (`periodoBloque` por fecha); Senado sin bloque en el detalle → "SIN BLOQUE" (a resolver). Reproducir: correr los dos `to_canonical.py` y `build.py`.
- **Archivos:** `datos/argentinadatos/src/to_canonical.py`, `datos/ckan_diputados/src/to_canonical.py`, `datos/canonica/COBERTURA.md`, `docs/schemas/acta.schema.json` (fecha pasó a opcional).
- **Estado del módulo:** argentinadatos EN CURSO (falta bloque Senado); canonica EN CURSO (2 fuentes).
- **Próximo paso:** semilla (pre-2011 y Senado 2004–2013), Diputados 2020–2023 oficial, Senado 2014–2023, entity resolution.

### [2026-06-25] datos/canonica + datos/ckan_diputados — Base canónica corriendo con CKAN
- **Quién:** Claude (sesión con Franco)
- **Qué:** CKAN Diputados normalizado al esquema canónico y base canónica construida y validada: 899 actas, 230.938 votos.
- **Cómo:** `datos/ckan_diputados/src/to_canonical.py` baja y traduce; `datos/canonica/src/build.py` une, deduplica (precedencia oficial>agregador>semilla), chequea FK y valida contra json-schema. Reproducir: correr to_canonical.py y luego build.py (deps en `datos/canonica/src/requirements.txt`).
- **Archivos:** `datos/ckan_diputados/src/to_canonical.py`, `datos/canonica/src/{build.py,requirements.txt}`.
- **Estado del módulo:** ckan_diputados→canónico HECHO; datos/canonica EN CURSO (corre con 1 fuente).
- **Próximo paso:** sumar la semilla (export R) y argentinadatos; resolución de entidades legislador/bloque.

### [2026-06-25] coordinacion/EN-HUMANO — Régimen de explicación en humano
- **Quién:** Claude (sesión con Franco)
- **Qué:** se creó `coordinacion/EN-HUMANO.md` (documento vivo que explica el sistema sin tecnicismos) y se volvió regla en `CLAUDE.md`: cada cambio se cuenta también en humano.
- **Cómo:** doc con analogías (semilla/huerta/bot, estaciones de cocina, idioma común). Se actualiza en cada cambio junto con este ESTADO.
- **Archivos:** `coordinacion/EN-HUMANO.md`, `CLAUDE.md`.
- **Estado del módulo:** HECHO (parte del régimen de trabajo).
- **Próximo paso:** mantenerlo actualizado en cada cambio.

### [2026-06-25] docs/schemas + datos/decada_votada — Esquema canónico v1 y export de la semilla
- **Quién:** Claude (sesión con Franco)
- **Qué:** definido el esquema canónico (schema_version=1) con tablas `acta` y `voto` + enum de voto; escrito `export_seed.R` que vuelca la semilla de Andy Tow (legislAr) al esquema canónico. Adoptado el régimen `Archivos_Borrar/` para descartables.
- **Cómo:** `docs/schemas/{README.md,acta.schema.json,voto.schema.json}`. El script R instala deps, itera `show_available_bills` → `get_bill_votes` por cámara, normaliza voto y escribe parquet. Correr local: `Rscript datos/decada_votada/export_seed.R 25` (prueba) o sin arg (completo).
- **Archivos:** `docs/schemas/*`, `datos/decada_votada/export_seed.R`, `Archivos_Borrar/README.md`, `CLAUDE.md`.
- **Estado del módulo:** docs/schemas HECHO; datos/decada_votada EN CURSO (falta correr el export en R).
- **Próximo paso:** correr el export, validar parquet contra schema, y arrancar `datos/canonica` (merge/dedup).

### [2026-06-25] datos — Estrategia semilla → canónica → bot (aportes Andy Tow)
- **Quién:** Claude (sesión con Franco)
- **Qué:** revisados los "Aportes sobre dataset congreso" (legislAr + Década Votada/towlandia). Andy Tow = semilla histórica de un solo uso; base canónica propia (`datos/canonica`) + bot (`datos/bot_recoleccion`). No se copia ni se depende en vivo.
- **Cómo:** legislAr (R) exporta parquet una vez; canónica unifica/deduplica/resuelve entidades; bot hace upsert idempotente. Límite R↔Python y cobertura en ADR-0002.
- **Archivos:** `datos/decada_votada/`, `datos/canonica/`, `datos/bot_recoleccion/`, `coordinacion/DECISIONES/0002-*.md`, `TABLERO.md`, `PLAN-DE-TRABAJO.md`, `CLAUDE.md`.
- **Estado del módulo:** los tres nuevos en PENDIENTE/EN CURSO.
- **Próximo paso:** schema + export (hecho); luego canónica.

### [2026-06-25] coordinacion — Estructura para trabajo en paralelo
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** estructura de carpetas por variable/módulo + documentos de coordinación (CLAUDE.md, PLAN, ESTADO, TABLERO, PROTOCOLO-GIT, ADR-0001).
- **Cómo:** monorepo, un módulo por unidad de trabajo; regla "un módulo, un dueño, una rama".
- **Archivos:** `CLAUDE.md`, `coordinacion/*`, `datos/*`, `variables/*`, `modelo/*`, `evaluacion/*`, `producto/*`, `docs/schemas/`.
- **Estado del módulo:** HECHO.
- **Próximo paso:** elegir prioridad de Fase 1 y reclamar módulos.

### [2026-06-25] evaluacion/baseline — Gate de Fase 0 medido
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** baseline "votá con tu bloque" sobre 231k votos (CKAN Diputados 2011–2020). Dirección sustantiva ≈ 0,989 (todas) / 0,984 (disputadas); 4 clases ≈ 0,807 / 0,820.
- **Cómo:** leave-one-out por bloque; corte disputadas = minoría ≥10%. Reproducir: `python fase0/src/ingesta.py && python fase0/src/baseline_bloque.py`.
- **Archivos:** `fase0/src/*`, `fase0/outputs/baseline_resultados.*`.
- **Estado del módulo:** HECHO. Redirige el producto a asistencia/embudo/posición de bloque.
- **Próximo paso:** migrar a `datos/ckan_diputados/` y `evaluacion/baseline/`.

### [2026-06-25] (análisis) — Validación crítica + premortem v2
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** validación de afirmaciones del estudio de viabilidad; premortem a 11 modos; informe Word.
- **Cómo:** WebSearch + inspección de fuentes. Hallazgo: CKAN de votaciones congelado en 2020.
- **Archivos:** `docs/contexto/Nowcast-Congreso_informe_validacion.docx`, `docs/contexto/premortem-*-validado.*`.
- **Estado del módulo:** HECHO (documentación).
- **Próximo paso:** ninguno; insumo para el plan.
