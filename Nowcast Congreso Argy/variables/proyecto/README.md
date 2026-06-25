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
