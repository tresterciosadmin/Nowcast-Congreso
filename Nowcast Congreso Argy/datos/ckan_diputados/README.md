# Módulo: datos/ckan_diputados

**Propósito.** Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle).

**Estado:** HECHO (migrar desde fase0/)
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** API CKAN datos.hcdn.gob.ar
- **Salida (contrato estable):** data/clean/diputados_cabecera.parquet, data/clean/diputados_detalle.parquet
- **Depende de:** -
- **Gate de pase:** Parquet generado y validado contra docs/schemas

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/ckan-diputados-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
