# TABLERO — claim de tareas (anti-colisión)

> Antes de empezar a trabajar un módulo, **reclamalo acá**: movelo a "En curso" con tu nombre/ID y fecha. Al terminar, movelo a "Hecho" y liberá el módulo. Regla: **un módulo lo trabaja una sola persona/Claude a la vez.**

Cómo reclamar: editá este archivo en tu rama, agregá la fila, y mencioná en el PR "claim: <módulo>". Si dos PRs reclaman lo mismo, gana el que mergea primero; el otro reelige.

---

## Disponible (libre para reclamar)

Prioridad alta (desbloquean el valor según el gate de Fase 0):

- [ ] **datos/argentinadatos** — ingestar Diputados 2020–2025 y Senado 2024–2025, normalizado al esquema CKAN. _Desbloquea el cross-check de drift y todo lo reciente._
- [ ] **datos/expedientes** — ingestar proyectos presentados; medir % que llega a votación nominal (sesgo de selección).
- [ ] **variables/embudo** — P(proyecto llega al recinto): comisión→dictamen→tratamiento. _Diferencial del nowcast._
- [ ] **variables/asistencia_quorum** — modelar asistencia/ausencia/abstención (el ~19% que el bloque no explica).
- [ ] **docs/schemas** — definir el contrato de datos (schema_version) por tipo. _Transversal; hacelo temprano para que nadie improvise esquemas._

Prioridad media:

- [ ] **variables/legislador** — feature store por legislador (point-in-time).
- [ ] **variables/proyecto** — feature store por proyecto (tema, autor, mayoría, NLP de texto).
- [ ] **variables/bloque** — cohesión/posición/fracturas por bloque en el tiempo.
- [ ] **modelo/agregador_institucional** — reglas de quórum y mayorías.
- [ ] **evaluacion/metricas** — Brier, calibración, accuracy en votos cruzados.

Depende de otros (no empezar hasta que su dependencia esté HECHA):

- [ ] **modelo/ensemble** — necesita embudo + agregador.
- [ ] **evaluacion/backtesting** — necesita al menos un modelo nuevo.
- [ ] **producto/dashboard** — necesita ensemble.

## En curso

| Módulo | Quién | Desde | Rama |
|---|---|---|---|
| _(vacío)_ | | | |

## Hecho

| Módulo | Quién | Fecha | Nota |
|---|---|---|---|
| evaluacion/baseline | Claude+Franco | 2026-06-25 | Baseline ~0,99 dirección / ~0,81 con asistencia |
| datos/ckan_diputados | Claude+Franco | 2026-06-25 | En `fase0/`, pendiente migrar a su carpeta |

## Congelado / no abrir aún

- **modelo/voto_individual** — baseline cerrado, no invertir más esfuerzo.
- **variables/contexto**, **producto/api** — futuros; no abrir sin cerrar prioridades / sin pagador.
