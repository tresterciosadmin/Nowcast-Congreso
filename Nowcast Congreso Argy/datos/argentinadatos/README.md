# Módulo: datos/argentinadatos

**Propósito.** Ingesta de Diputados 2020-2025 y Senado 2024-2025 desde la API argentinadatos.com, normalizada al MISMO esquema que CKAN.

**Estado:** HECHO (integrado 2026-07-11) · reabierto 2026-08-06 por el bloque del Senado
**Owner actual:** Claude (con Valle), desde 2026-08-06

## Contrato
- **Entradas:** https://api.argentinadatos.com (endpoints `/diputados/actas/` y `/senado/actas/`)
- **Salida (contrato estable):** `ckan`-compatible: `<OUT>/argentinadatos_actas.parquet` y `argentinadatos_votos.parquet`, con `schema_version`. `OUT` lo fija `datos/canonica/src/run_pipeline.py`.
- **Depende de:** `docs/schemas`, y para resolver el bloque: `datos/senado/data/padron_*.csv` + `datos/padron/data/padron_senado.csv`
- **Gate de pase:** Esquema idéntico al de ckan_diputados; rango de fechas continuo sin huecos

## Cómo se resuelve el BLOQUE (lo delicado de este módulo)

La fuente **no trae el bloque** en el detalle del voto. Se reconstruye por nombre
+ fecha del acta:

- **Diputados:** contra `/diputados/diputados` (campo `periodoBloque` con fechas).
  Misma fuente que el padrón, así que quedan consistentes por construcción.
- **Senado:** contra padrones CSV versionados, en este orden de precedencia
  (gana el primero que matchea la fecha):
  1. `datos/senado/data/padron_manual_2015_2017.csv` — curado a mano
  2. `datos/senado/data/padron_bloques_senado.csv` — histórico, **termina 2025-12-09**
  3. `datos/padron/data/padron_senado.csv` — nómina oficial **vigente** (72 senadores)

  El (3) se sumó el **2026-08-06**. Sin él, todo voto posterior al recambio del
  10-dic-2025 entraba `SIN BLOQUE` — 6.192 votos de 2026, o sea el nowcast del
  Senado ciego. Va último a propósito: en el tramo solapado (mandatos 2021-2027,
  que figuran en los dos archivos) sigue mandando el padrón curado.

**Regla que aplica acá (30-07):** los huecos se tapan en la ENTRADA, no en cada
consumidor. Si aparece un tramo sin bloque, el arreglo va en este módulo.

**Tests:** `tests/test_padron_senado.py` (8, offline). El que importa es el de
cobertura: verifica que los **72 senadores vigentes** resuelvan bloque a una
fecha de 2026. Esta falla es silenciosa — no rompe nada, sólo degrada una cámara
entera — así que el test es la única alarma.

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/argentinadatos-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
