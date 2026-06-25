# Módulo: variables/embudo

**Propósito.** Supervivencia del proyecto: comisión -> dictamen -> tratamiento -> recinto. El diferencial del nowcast.

**Estado:** PENDIENTE — PRIORITARIO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** datos/expedientes, variables/proyecto
- **Salida (contrato estable):** P(llega al recinto) por proyecto
- **Depende de:** datos/expedientes, variables/proyecto
- **Gate de pase:** Backtesting temporal mejora sobre predecir solo el voto final

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/embudo-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
