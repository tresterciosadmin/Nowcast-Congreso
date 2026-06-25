# Módulo: modelo/agregador_institucional

**Propósito.** Convierte votos individuales en resultado aplicando reglas de quórum y mayorías (simple, absoluta, 2/3).

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** modelo/voto_individual, variables/asistencia_quorum
- **Salida (contrato estable):** P(mayoría | recinto) por proyecto
- **Depende de:** variables/asistencia_quorum
- **Gate de pase:** Reglas validadas contra resultados históricos reales

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/agregador-institucional-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
