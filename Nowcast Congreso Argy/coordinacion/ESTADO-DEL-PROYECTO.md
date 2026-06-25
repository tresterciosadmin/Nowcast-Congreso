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
| datos/ckan_diputados | HECHO (en `fase0/`, migrar) | — |
| datos/argentinadatos | PENDIENTE | — |
| datos/senado | PENDIENTE | — |
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
| docs/schemas | PENDIENTE (transversal) | — |

---

## Bitácora (más reciente arriba)

### [2026-06-25] coordinacion — Estructura para trabajo en paralelo
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** se creó la estructura de carpetas por variable/módulo y los documentos de coordinación (CLAUDE.md, PLAN-DE-TRABAJO, este ESTADO, TABLERO, PROTOCOLO-GIT, ADR-0001).
- **Cómo:** monorepo con un módulo por unidad de trabajo y contrato de salida; regla "un módulo, un dueño, una rama"; cada cambio registra entrada acá.
- **Archivos:** `CLAUDE.md`, `coordinacion/*`, `datos/*`, `variables/*`, `modelo/*`, `evaluacion/*`, `producto/*`, `docs/schemas/`.
- **Estado del módulo:** HECHO.
- **Próximo paso:** elegir prioridad de Fase 1 y reclamar módulos en TABLERO.

### [2026-06-25] evaluacion/baseline — Gate de Fase 0 medido
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** baseline "votá con tu bloque" sobre 231k votos (CKAN Diputados 2011–2020). Dirección sustantiva ≈ 0,989 (todas) / 0,984 (disputadas); 4 clases (incl. asistencia) ≈ 0,807 / 0,820.
- **Cómo:** leave-one-out por bloque; corte disputadas = minoría ≥10%. Reproducir: `python fase0/src/ingesta.py && python fase0/src/baseline_bloque.py`.
- **Archivos:** `fase0/src/{ingesta,baseline_bloque,common}.py`, `fase0/outputs/baseline_resultados.{json,md}`.
- **Estado del módulo:** HECHO. Redirige el producto: el voto-dirección es callejón sin salida; valor en asistencia/embudo/posición de bloque.
- **Próximo paso:** migrar el código a `datos/ckan_diputados/` y `evaluacion/baseline/`; abrir `variables/embudo` y `variables/asistencia_quorum`.

### [2026-06-25] (análisis) — Validación crítica + premortem v2
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** se validaron las afirmaciones del estudio de viabilidad contra fuentes; premortem actualizado a 11 modos de fallo; informe ejecutivo en Word.
- **Cómo:** WebSearch + inspección de CKAN/argentinadatos. Hallazgo: el dataset CKAN de votaciones está congelado en 2020.
- **Archivos:** `docs/contexto/Nowcast-Congreso_informe_validacion.docx`, `docs/contexto/premortem-*-20260625-validado.*` (el log de avances se consolidó en este ESTADO).
- **Estado del módulo:** HECHO (documentación).
- **Próximo paso:** ninguno; insumo para el plan.
