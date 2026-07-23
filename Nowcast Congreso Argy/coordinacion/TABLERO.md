# TABLERO — claim de tareas (anti-colisión)

> Antes de empezar a trabajar un módulo, **reclamalo acá**: movelo a "En curso" con tu nombre/ID y fecha. Al terminar, movelo a "Hecho" y liberá el módulo. Regla: **un módulo lo trabaja una sola persona/Claude a la vez.**

Cómo reclamar: editá este archivo en tu rama, agregá la fila, y mencioná en el PR "claim: <módulo>".

---

## Disponible (libre para reclamar)

Prioridad alta — datos (estrategia semilla → canónica → bot, ver ADR-0002):

- [ ] **datos/canonica** — base propia única: unificar todas las fuentes, deduplicar solapamientos y resolver entidades. Fuente de verdad del proyecto. _Necesita al menos una fuente cargada (semilla o CKAN)._
- [x] ~~**datos/argentinadatos**~~ → HECHO 2026-07-11 (ver "Hecho").
- [x] ~~**datos/expedientes**~~ → reclamado 2026-07-11 por Claude+Franco (ver "En curso").
- [ ] **datos/licencias_suspensiones** — registro + notificador de licencias y suspensiones de legisladores (decisión ADR-0004: se excluyen del índice de indisciplina; hoy solo los suspendidos son detectables).
- [x] ~~**datos/padron**~~ → NUEVO, reclamado 2026-07-14 por Valle (ver "En curso"). Nómina oficial individual = composición de la cámara a la fecha.

Prioridad alta — modelo (gate de Fase 0):

- [x] ~~**variables/embudo**~~ → reclamado 2026-07-12 por Valle (ver "En curso"). Diferencial del nowcast.
- [x] ~~**variables/asistencia_quorum**~~ → reclamado 2026-07-11 (ver "En curso"). Escalón 1: presentismo → alimentar el agregador.
- [x] ~~**modelo/voto_individual**~~ → reclamado 2026-07-01 (ver "En curso"). ADR-0003 formaliza el cambio de rumbo.

Prioridad media:

- [ ] **datos/diputados_oficial** — completar Diputados 2020–2023 desde `votaciones.hcdn.gob.ar`. **PAUSADO 2026-07-10** (decisión de Valle: priorizar puesta en marcha; se reanuda después).
- [x] ~~**variables/legislador**~~ → reclamado 2026-07-01 (ver "En curso").
- [ ] **variables/proyecto** — feature store por proyecto (tema, autor, mayoría, NLP de texto).
- [x] ~~**variables/bloque**~~ → reclamado 2026-07-12 por Valle, REGISTRADO 2026-07-14 (ver "En curso").
- [x] ~~**modelo/agregador_institucional**~~ → reclamado 2026-07-10 (ver "En curso").
- [ ] **evaluacion/metricas** — Brier, calibración, accuracy en votos cruzados.

Depende de otros (no empezar hasta que su dependencia esté HECHA):

- [x] ~~**datos/bot_recoleccion**~~ → reclamado 2026-07-11 por Claude+Franco (dependencia cumplida; ver "En curso").
- [x] ~~**modelo/ensemble**~~ → reclamado 2026-07-12 por Valle (ver "En curso"). Dependencias cumplidas: embudo v1 + agregador.
- [ ] **evaluacion/backtesting** — necesita al menos un modelo nuevo.
- [ ] **producto/dashboard** — necesita ensemble.

## En curso

| Módulo | Quién | Desde | Rama |
|---|---|---|---|
| datos/decada_votada | Claude+Franco | 2026-06-25 | export_seed.R listo; falta correrlo en R |
| datos/canonica | Claude+Franco | 2026-06-25 | cubre Diputados 2011–2025 + Senado 2024–2025 |
| datos/seguimiento | Claude+Valle | 2026-06-29 | extractor de giros/trámite Dip+Sen — VALIDADO EN VIVO |
| datos/proyectos | Claude+Valle | 2026-06-29 | base SQLite de PdL + export Excel; upsert idempotente por denominador |
| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + ICG + origen/líder + tema_por_acta (1537). origen_por_acta.py = quién impulsa + gobierno POR ACTA (4 vías: código/embebido/O.D./título); 20 tests. Cobertura (2026-07-23): 59% global / 54,5% Senado (vía código embebido tapa el hueco 2004-2014). HALLAZGO: el nowcast del Senado a hoy se traba en la atribución de linaje de votos recientes (todo cae en OTRO/PROVINCIAL) = entity_resolution/Franco, no origen |
| modelo/voto_individual | Claude+Valle | 2026-07-01 | índice de disciplina individual + dimensionamiento del set pivote (gate 1 de 1B.4) |
| variables/legislador | Claude+Valle | 2026-07-01 | ficha individual por legislador (identidad, bloques, presentismo, perfil de voto, desvío) |
| datos/export | Claude+Valle | 2026-07-02 | base unificada: SQLite completo + Excel por gobierno; disputada = ±5% del umbral de mayoría |
| modelo/agregador_institucional | Claude+Valle | 2026-07-10 | motor de recuento como distribución (P aprobación con banda); tests 12 OK; falta backtest a escala |
| producto/dashboard | Claude+Valle | 2026-07-10 | PANEL-NOWCAST.html (raíz, doble clic): estado del sistema + simulador de votación (motor JS) |
| variables/asistencia_quorum | Claude+Valle | 2026-07-11 | escalón 1: presentismo por legislador + modo asistencia del agregador (arreglo del sesgo pesimista); falta backtest a escala |
| datos/expedientes | Claude+Franco | 2026-07-11 | backfill CKAN HECHO (112.793 proyectos; embudo bruto 3,22%); fase 2 = cofirmantes vía bot |
| datos/bot_recoleccion | Claude+Franco | 2026-07-11 | bot diario BICAMERAL en GitHub Actions: DAE Senado (1.004 exp.) + TP Diputados con COFIRMANTES completos (13+13 tests) |
| variables/embudo | Claude+Valle | 2026-07-12 | supervivencia del proyecto de ley: embudo por etapas + modelo v1 (rasgos al presentar, sin leakage) + backtest temporal; consume contrato de datos/expedientes |
| modelo/ensemble | Claude+Valle | 2026-07-12 | P(aprob)=P(llega)×P(mayoría). ROSTER NOMINAL (2026-07-22): nowcast_auto simula UNA FILA POR LEGISLADOR (padrón vigente + desvío individual, escalera reciente→global→bloque); se eliminó _expandir_roster/demo. Dirección de bloque condicionable por tema/origen (consume tema_por_acta + origen_por_acta). Con --origen GOBIERNO el caso testigo 1167-D-2025 se endereza (LLA 0,33→0,88; kirchnerismo 0,85→0,44). Falta backtest de la cadena y automatizar el --origen del propio proyecto |
| variables/bloque | Claude+Valle | 2026-07-12 | dirección condicionada por tema/origen (shrinkage + guard de gobierno). NUEVO (2026-07-23): _enriquecer_linaje_senado recupera el linaje real de los votos del Senado 2024+ (llegaban SIN BLOQUE→OTRO/PROVINCIAL) contra el padrón mandate-aware → el nowcast del Senado YA CONDICIONA (n_cond 0→16-18). 37 tests. Override manual del Senado COMPLETO 22/22 (OTRO/PROVINCIAL 53%→26%). NUEVO: la postura EXCLUYE actas AUX (homenajes/trámite/tratados = consenso) para no inflar el share afirmativo; se nota en Diputados, en el Senado espera más actas contenciosas + multitema |
| datos/padron | Valle | 2026-07-14 | nómina oficial individual: Diputados 257 + Senado 72 vigentes (mandato desde-hasta, clave canónica, linaje). Composición a la fecha; enchufada al proyector (roster 375→257). Falta histórico de mandatos |

## Hecho

| Módulo | Quién | Fecha | Nota |
|---|---|---|---|
| docs/schemas | Claude+Franco | 2026-06-25 | Esquema canónico schema_version=1 (acta + voto) |
| datos/senado | Claude+Franco | 2026-07-02 | 2015–2023 completo: 749 actas / 53.910 votos, validado vs nahuelhds (0 discrepancias), bloque histórico 100% / 0 anacronismos. **Padrón AUDITADO 11-07: 17/17 filas validadas, cero errores** (los desvíos altos son fractura real del FpV-PJ 2016-17). Pendiente de otros módulos: integrar a run_pipeline (canonica) + 2 ADRs |
| datos/argentinadatos | Claude+Franco | 2026-07-11 | Integrado con bloque del Senado 24-25 resuelto vía padrón versionado (SIN BLOQUE=0 en Senado; residuo menor en Dip) |
| docs/taxonomias | Claude+Valle | 2026-06-29 | Vocabulario controlado v1 (74 ids, id estable, multi-etiqueta) |
| evaluacion/baseline | Claude+Franco | 2026-06-25 | Baseline ~0,99 dirección / ~0,81 con asistencia |
| datos/ckan_diputados | Claude+Franco | 2026-06-25 | En `fase0/`, pendiente migrar a su carpeta |

## Congelado / no abrir aún

- ~~**modelo/voto_individual** — baseline cerrado, no invertir más esfuerzo.~~ **DESCONGELADO 2026-06-30:** re