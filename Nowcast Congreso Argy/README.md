# Nowcast Legislativo Argentino

Sistema que estima la probabilidad de sanción de proyectos de ley en el Congreso argentino.

## Empezar acá (lectura obligatoria)
1. **`CLAUDE.md`** — bootstrap para trabajar en paralelo sin pisarse.
2. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — qué se hizo hasta ahora (documento vivo).
3. **`coordinacion/PLAN-DE-TRABAJO.md`** — qué hacer y cómo, por módulo y fase.
4. **`coordinacion/TABLERO.md`** — reclamá tu tarea antes de empezar.
5. **`coordinacion/PROTOCOLO-GIT.md`** — ramas, PRs, cómo evitar conflictos.

## Estructura
```
datos/          ingesta por fuente (ckan_diputados, argentinadatos, senado, expedientes)
variables/      una carpeta por variable: legislador, proyecto, bloque,
                asistencia_quorum, embudo, contexto
modelo/         voto_individual (baseline), agregador_institucional, ensemble
evaluacion/     baseline, backtesting, metricas
producto/       dashboard, api
docs/schemas/   contratos de datos (schema_version)
docs/contexto/  documentos de negocio, metodología y diseño (referencia)
coordinacion/   plan, estado vivo, tablero, protocolo git, decisiones (ADR)
fase0/          baseline ya ejecutado (Fase 0 cerrada)
```
Cada carpeta de módulo tiene su `README.md` con el contrato (entradas, salida, dependencias, gate).

## Estado
Fase 0 cerrada: el baseline de bloque predice la dirección del voto individual ≈ 0,99; el valor del producto está en **asistencia/quórum**, **embudo** y **posición de bloque**. Detalle en `coordinacion/ESTADO-DEL-PROYECTO.md`.

## Contexto de negocio y metodología
En `docs/contexto/`: `INSTRUCTIVO-MAESTRO.md`, `Nowcast-Congreso_viabilidad_y_plan.md`, `Nowcast-Congreso_informe_validacion.docx`, el premortem validado y los documentos de diseño v2.1 (referencia histórica).
