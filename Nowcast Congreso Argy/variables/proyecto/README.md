# Módulo: variables/proyecto

**Propósito.** Features por proyecto: tema/materia, autor, cámara de origen, tipo de mayoría requerida, parsing de texto (NLP).

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** datos/expedientes, cabecera
- **Salida (contrato estable):** feature store proyecto (parquet, una fila por proyecto)
- **Depende de:** datos/expedientes
- **Gate de pase:** Tema asignado y validado en muestra etiquetada

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/proyecto-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.

## Nota (2026-06-25): clasificación por TEMA — prioridad confirmada
El usuario confirmó que hay que **separar/clasificar por tema del proyecto** (materia del expediente: económico, penal, laboral, salud, etc.). Es una feature central de este módulo: a partir del `titulo`/texto del expediente, asignar una taxonomía de temas (reglas + NLP), validada en una muestra etiquetada. Habilita análisis y modelos por materia.
