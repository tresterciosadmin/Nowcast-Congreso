# Módulo: variables/asistencia_quorum

**Propósito.** Modelo de asistencia/ausencia/abstención por legislador. Es donde vive la incertidumbre (el ~19% que el bloque NO explica).

**Estado:** PENDIENTE — PRIORITARIO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** datos/* (detalle), variables/legislador
- **Salida (contrato estable):** P(asiste), P(abstiene) por legislador-acta
- **Depende de:** variables/legislador
- **Gate de pase:** Supera baseline de presentismo histórico por legislador

## Plan de construcción (acordado con Valle, 2026-07-10 — arrancar 2026-07-11)
La asistencia YA está en los datos: cada voto trae `AUSENTE` por legislador-acta (no hay que
scrapear nada). Se construye en 3 escalones, de simple a fino:

1. **Presentismo histórico (baseline + arreglo del sesgo).** P(presente) = tasa histórica de
   presentismo del legislador (ya calculada en `variables/legislador`, columna presentismo).
   Uso inmediato: alimentar `modelo/agregador_institucional` con los PRESENTES esperados por
   bloque, en vez de todas las bancas. Esto corrige el sesgo pesimista detectado en el backtest
   (el motor daba por perdidas votaciones peleadas que se aprobaron, porque contaba a los
   ausentes como "no acompaña" y borraba afirmativos reales). **Validar re-corriendo el backtest
   del agregador** y comparando contra el estado actual (Brier 0,011 pero mal calibrado en las
   ~350 disputadas). Es el gate del módulo: superar el baseline de presentismo por legislador.
2. **Asistencia condicionada.** Modelar P(presente | saliencia/qué tan peleada, oficialismo vs
   oposición, año electoral, legislador, bloque). La asistencia no es al azar: sube en las
   votaciones importantes y con el oficialismo movilizando.
3. **Quórum como jugada de bloque.** Ausencia estratégica: la oposición falta a propósito para
   que no haya quórum y la sesión se caiga sin votarse. Es lo que hace único al Nowcast
   (no solo "¿cuántos votos?" sino "¿va a haber sesión?").

Empezar por el **escalón 1** (barato, ataca el problema concreto, se ve en una vuelta).

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/asistencia-quorum-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
