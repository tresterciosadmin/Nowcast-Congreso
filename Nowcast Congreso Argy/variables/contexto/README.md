# Módulo: variables/contexto

<!-- huella: e3b0c44298fc -->

**Propósito.** Señal cualitativa de prensa/contexto político (factor μ). Futuro, no bloquea el MVP.

**Estado:** FUTURO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

**Resumen:** Senal cualitativa de prensa y contexto politico (factor mu). FUTURO: no bloquea el MVP.

## Buscar acá si

- senal de prensa o clima politico como variable (todavia no existe)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entradas:** prensa, fuentes externas
- **Salida (contrato estable):** context_shift score
- **Depende de:** -
- **Gate de pase:** No abrir hasta cerrar embudo + asistencia

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/contexto-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
