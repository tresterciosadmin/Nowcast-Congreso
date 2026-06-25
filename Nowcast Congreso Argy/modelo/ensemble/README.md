# Módulo: modelo/ensemble

**Propósito.** Composición final: P(aprobación) = P(llega al recinto) x P(mayoría | recinto).

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** variables/embudo, modelo/agregador_institucional
- **Salida (contrato estable):** P(aprobación) calibrada por proyecto
- **Depende de:** variables/embudo, modelo/agregador_institucional
- **Gate de pase:** Calibración (Brier/reliability) dentro de tolerancia

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/ensemble-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
