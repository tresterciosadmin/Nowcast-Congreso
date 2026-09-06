# Módulo: evaluacion/baseline

<!-- huella: e3b0c44298fc -->

**Propósito.** Baseline de bloque (HECHO). Documenta el piso a superar por cualquier modelo.

**Estado:** HECHO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

**Resumen:** El piso a superar: el baseline de bloque, ya medido. Cualquier modelo nuevo se compara contra esto.

## Buscar acá si

- cuanto acierta la regla de bloque (~0,99 en direccion del voto individual)
- contra que se compara un modelo nuevo
- cuanto pierde el record individual en cada era, y cuanto lo arregla el guard

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## El guard de era (URGENTE 9 / ADR-0018)

`baseline_voto_individual.py --guard-era {off,corte,shrink}` cambia como se acumula el
record individual: `off` es toda la historia (lo de siempre), `corte` lo reinicia en cada
era —que es lo que el motor YA hace, con fecha fija— y `shrink` agrega Empirical-Bayes
contra el record del linaje en la misma era.

**OJO con lo que este harness es y no es.** `perfil()` se documenta como espejo exacto de
`perfil_legislador`, y en el reparto de ramas lo es; en el **record** no lo era. El motor
corta por era y condiciona por origen, este harness acumulaba toda la historia sin
condicionar. Mediana de la diferencia 0,004, pero 12,2% por encima de 0,10 y peor caso
0,73. Un espejo que no refleja produce numeros sobre un modelo que no existe.

`src/medir_guard_era.py` es el **proxy** que mide los tres modos en 11 segundos aislando la
rama del record (el baseline completo son ~1,5 min cada 150 actas). Sirve para la
DIFERENCIA entre modos, no para el nivel absoluto. Tests en `tests/test_guard_era.py`, que
verifican ademas los dos atajos de rendimiento contra la version lenta.

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
