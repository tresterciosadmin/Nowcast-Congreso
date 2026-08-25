# Módulo: evaluacion/baseline

<!-- huella: e3b0c44298fc -->

**Propósito.** Baseline de bloque (HECHO). Documenta el piso a superar por cualquier modelo.

**Estado:** HECHO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

**Resumen:** El piso a superar: el baseline de bloque, ya medido. Cualquier modelo nuevo se compara contra esto.

## Buscar acá si

- cuanto acierta la regla de bloque (~0,99 en direccion del voto individual)
- contra que se compara un modelo nuevo

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entradas:** datos/* (detalle)
- **Salida (contrato estable):** outputs/baseline_resultados.{json,md}
- **Depende de:** datos/ckan_diputados
- **Gate de pase:** Benchmark publicado: dirección ~0.99 / 4-clases ~0.81

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/baseline-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
