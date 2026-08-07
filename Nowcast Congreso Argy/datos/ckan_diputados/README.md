# Módulo: datos/ckan_diputados

**Propósito.** Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle).

**Estado:** HECHO. **La migración desde `fase0/` ya se hizo** (`src/to_canonical.py`
vive acá y `run_pipeline.py` lo invoca en el paso 2). El texto "migrar desde fase0/"
quedó de arrastre y se corrigió el 2026-08-06.
**Owner actual:** _(cerrado — no requiere dueño; si hay que tocarlo, reclamalo en `coordinacion/TABLERO.md`)_

> **Nota:** la fuente CKAN está **congelada en 2020**. De ahí en adelante cubre
> `datos/argentinadatos`. Este módulo no se vuelve a correr salvo para reconstruir
> la canónica de cero.

## Contrato
- **Entradas:** API CKAN datos.hcdn.gob.ar
- **Salida (contrato estable):** `<OUT>/ckan_diputados_actas.parquet` y `<OUT>/ckan_diputados_votos.parquet` (nombres reales; el README decía `diputados_cabecera/detalle`, que nunca existieron). `OUT` lo fija `run_pipeline.py`.
- **Depende de:** -
- **Gate de pase:** Parquet generado y validado contra docs/schemas

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/ckan-diputados-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
