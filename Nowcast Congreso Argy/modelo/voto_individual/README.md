# Módulo: modelo/voto_individual

**Propósito.** Baseline 'vota con tu bloque'. CERRADO: ~0.99 en dirección sustantiva. Se conserva como referencia, no se invierte más esfuerzo.

**Estado:** HECHO (congelado)
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** datos/* (detalle)
- **Salida (contrato estable):** predicción de voto individual + baseline de referencia
- **Depende de:** datos/ckan_diputados
- **Gate de pase:** Ya superado el gate; benchmark fijo

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/voto-individual-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
