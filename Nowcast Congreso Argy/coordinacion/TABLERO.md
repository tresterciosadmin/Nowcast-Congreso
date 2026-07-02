# TABLERO — claim de tareas (anti-colisión)

> Antes de empezar a trabajar un módulo, **reclamalo acá**: movelo a "En curso" con tu nombre/ID y fecha. Al terminar, movelo a "Hecho" y liberá el módulo. Regla: **un módulo lo trabaja una sola persona/Claude a la vez.**

Cómo reclamar: editá este archivo en tu rama, agregá la fila, y mencioná en el PR "claim: <módulo>".

---

## Disponible (libre para reclamar)

Prioridad alta — datos (estrategia semilla → canónica → bot, ver ADR-0002):

- [ ] **datos/canonica** — base propia única: unificar todas las fuentes, deduplicar solapamientos y resolver entidades. Fuente de verdad del proyecto. _Necesita al menos una fuente cargada (semilla o CKAN)._
- [ ] **datos/argentinadatos** — ingestar Diputados 2020–2025 y Senado 2024–2025, normalizado al esquema canónico.
- [ ] **datos/expedientes** — ingestar proyectos presentados; medir % que llega a votación nominal (sesgo de selección).

Prioridad alta — modelo (gate de Fase 0):

- [ ] **variables/embudo** — P(proyecto llega al recinto): comisión→dictamen→tratamiento. _Diferencial del nowcast._
- [ ] **variables/asistencia_quorum** — modelar asistencia/ausencia/abstención (el ~19% que el bloque no explica).
- [x] ~~**modelo/voto_individual**~~ → reclamado 2026-07-01 (ver "En curso"). ADR-0003 formaliza el cambio de rumbo.

Prioridad media:

- [ ] **datos/senado** — Senado: **huecos 2014–2023 y 2001–2003** + resolver bloque (padrón→bloque por fecha).
- [ ] **datos/diputados_oficial** — completar Diputados 2020–2023 desde `votaciones.hcdn.gob.ar` (argentinadatos está incompleto).
- [x] ~~**variables/legislador**~~ → reclamado 2026-07-01 (ver "En curso").
- [ ] **variables/proyecto** — feature store por proyecto (tema, autor, mayoría, NLP de texto).
- [ ] **variables/bloque** — cohesión/posición/fracturas por bloque en el tiempo.
- [ ] **modelo/agregador_institucional** — reglas de quórum y mayorías.
- [ ] **evaluacion/metricas** — Brier, calibración, accuracy en votos cruzados.

Depende de otros (no empezar hasta que su dependencia esté HECHA):

- [ ] **datos/bot_recoleccion** — bot que trae votaciones nuevas a la canónica. Necesita `datos/canonica` cargada.
- [ ] **modelo/ensemble** — necesita embudo + agregador.
- [ ] **evaluacion/backtesting** — necesita al menos un modelo nuevo.
- [ ] **producto/dashboard** — necesita ensemble.

## En curso

| Módulo | Quién | Desde | Rama |
|---|---|---|---|
| datos/decada_votada | Claude+Franco | 2026-06-25 | export_seed.R listo; falta correrlo en R |
| datos/canonica | Claude+Franco | 2026-06-25 | cubre Diputados 2011–2025 + Senado 2024–2025 |
| datos/argentinadatos | Claude+Franco | 2026-06-25 | integrado; falta bloque del Senado |
| datos/seguimiento | Claude+Valle | 2026-06-29 | extractor de giros/trámite Dip+Sen — VALIDADO EN VIVO |
| datos/proyectos | Claude+Valle | 2026-06-29 | base SQLite de PdL + export Excel; upsert idempotente por denominador |
| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías (LLM/Claude API): PDF→etiquetas en proyecto_taxonomias |
| modelo/voto_individual | Claude+Valle | 2026-07-01 | índice de disciplina individual + dimensionamiento del set pivote (gate 1 de 1B.4) |
| variables/legislador | Claude+Valle | 2026-07-01 | ficha individual por legislador (identidad, bloques, presentismo, perfil de voto, desvío) |

## Hecho

| Módulo | Quién | Fecha | Nota |
|---|---|---|---|
| docs/schemas | Claude+Franco | 2026-06-25 | Esquema canónico schema_version=1 (acta + voto) |
| docs/taxonomias | Claude+Valle | 2026-06-29 | Vocabulario controlado v1 (74 ids, id estable, multi-etiqueta) |
| evaluacion/baseline | Claude+Franco | 2026-06-25 | Baseline ~0,99 dirección / ~0,81 con asistencia |
| datos/ckan_diputados | Claude+Franco | 2026-06-25 | En `fase0/`, pendiente migrar a su carpeta |

## Congelado / no abrir aún

- ~~**modelo/voto_individual** — baseline cerrado, no invertir más esfuerzo.~~ **DESCONGELADO 2026-06-30:** reformulado (desvío individual + pivotes); movido a "Disponible". Lo cerrado era predecir el voto MEDIO; el valor está en el desvío del parlamentario y en los pivotes.
- **variables/contexto**, **producto/api** — futuros; no abrir sin cerrar prioridades / sin pagador.
