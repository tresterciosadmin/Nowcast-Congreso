# Módulo: evaluacion/metricas

<!-- huella: e3b0c44298fc -->

**Propósito.** Métricas comunes: Brier, calibración, accuracy en votos cruzados, cobertura de bandas.

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

**Resumen:** Metricas comunes: Brier, calibracion, accuracy en votos cruzados, cobertura de bandas. PENDIENTE.

## Buscar acá si

- como se mide si el modelo es bueno

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entradas:** todos los modelos
- **Salida (contrato estable):** módulo de métricas reutilizable
- **Depende de:** -
- **Gate de pase:** API de métricas estable y testeada

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/metricas-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
