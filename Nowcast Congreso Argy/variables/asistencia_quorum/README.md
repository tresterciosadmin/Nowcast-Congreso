# Módulo: variables/asistencia_quorum

**Propósito.** Modelo de asistencia/ausencia/abstención por legislador. Es donde vive la incertidumbre (el ~19% que el bloque NO explica).

**Estado:** PENDIENTE — PRIORITARIO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** datos/* (detalle), variables/legislador
- **Salida (contrato estable):** P(asiste), P(abstiene) por legislador-acta
- **Depende de:** variables/legislador
- **Gate de pase:** Supera baseline de presentismo histórico por legislador

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/asistencia-quorum-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
