# fase0/ — el baseline ya ejecutado (CERRADO)

<!-- huella: 9dc68d15827d -->

**Resumen:** La Fase 0, cerrada: medir cuanto acierta predecir el voto individual mirando al bloque. Resultado ~0,99, y ese resultado ordena todo el proyecto. Se conserva como registro; no se desarrolla mas.

## Buscar acá si

- de donde sale el 0,99 del baseline de bloque
- por que el proyecto NO apunta a predecir la direccion del voto individual
- el codigo original de ingesta, anterior a `datos/`

## Trampas

- **Esta cerrado.** La ingesta de CKAN que empezo acá ya vive en `datos/ckan_diputados/src/to_canonical.py`; si algun texto dice "migrar desde fase0/", quedo viejo (se corrigio el 06-08-2026).
- El resultado de Fase 0 es el gate del proyecto: el valor no esta en la direccion del voto individual sino en **asistencia/quorum**, **embudo**, **postura de bloque** y las **10-20 bisagras**.
