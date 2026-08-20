# TABLERO — claim de tareas (anti-colisión)

> Antes de empezar a trabajar un módulo, **reclamalo acá**: movelo a "En curso" con tu nombre/ID y fecha. Al terminar, movelo a "Hecho" y liberá el módulo. Regla: **un módulo lo trabaja una sola persona/Claude a la vez.**

Cómo reclamar: editá este archivo en tu rama, agregá la fila, y mencioná en el PR "claim: <módulo>".

---

## Disponible (libre para reclamar)

Prioridad alta — datos (estrategia semilla → canónica → bot, ver ADR-0002):

- [x] ~~**datos/canonica**~~ → reclamado 2026-06-25 por Claude+Franco (ver "En curso"). **NO está libre:** es la fuente de verdad del proyecto y ya tiene 1.016.632 votos. Figuraba como disponible por un error de arrastre, corregido el 06-08.
- [x] ~~**datos/argentinadatos**~~ → HECHO 2026-07-11 (ver "Hecho"). **Reabierto el 2026-08-06** por el bloque del Senado en la ingesta (ver la sesión abierta, abajo).
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

## Sesion 2026-08-20 (Valle+Claude) — CERRADA, estructura del repo: MAPA.md, router en los README y `rutas.py`. NADA RECLAMADO.

| Modulo | Quien | Desde | Que se hizo |
|---|---|---|---|
| **(transversal — estructura)** | Claude (con Valle) | 2026-08-20 | **HECHO.** Auditoria de las conexiones entre carpetas + cuatro entregas: (1) `MAPA.md` en la raiz, generado, con `.mapa/` (indice, `buscar.py`, `indexar.py` forkeado, hook de pre-commit); (2) router `**Resumen:**` + `## Buscar aca si` **dentro de los 27 README de modulo** (+5 README nuevos: `coordinacion/`, `casos/`, `tests/`, `docs/taxonomias/`, `fase0/`) — **no** se crearon `BITACORA.md` aparte, ver ADR-0010; (3) `rutas.py` en la raiz con las 52 rutas que cruzan entre modulos; (4) `tests/` de raiz con dos controles entre modulos. Ver ADR-0010 y la entrada del 20-08 en ESTADO. |
| **datos/proyectos** | Claude (con Valle) | 2026-08-20 | **HECHO, modulo LIBRE.** `verificar.py` deja de hacer `sys.path.insert` + `import embudo` (dependencia hacia arriba, capa 1 -> capa 2). Ahora invoca `variables/embudo/src/cohorte_dos_rutas.py` **como proceso** y consume su JSON. Mismos controles, misma severidad: si el medidor no corre, el control FALLA (no se saltea en silencio). Migrado a `rutas.py`. Tests del modulo: 10 pasan / 6 skip (los que necesitan `proyectos.db`). |
| **variables/embudo** | Claude (con Valle) | 2026-08-20 | **HECHO, modulo LIBRE.** Archivo NUEVO y aditivo: `src/cohorte_dos_rutas.py` — mide la cohorte por las dos rutas (parquet vs SQLite) e imprime JSON. **No se toco `embudo.py`.** Es el entrypoint publicado que consume `datos/proyectos`. |
| **evaluacion/baseline** | Claude (con Valle) | 2026-08-20 | **HECHO, modulo LIBRE** (owner estaba vacante). Migrado a `rutas.py` como segundo ejemplo de la migracion; `CANON` sigue mandando si esta seteada. |
| **datos/proyectos** (2do claim) | Claude (con Valle) | 2026-08-20 | **HECHO, modulo LIBRE.** `tests/test_taxonomias_backup.py` estaba escrito como script (cuerpo a nivel de modulo + `raise SystemExit`) y **abortaba toda la corrida de pytest con INTERNALERROR**, sin ejecutar un solo test. Su cuerpo paso a `_correr()`: sigue andando como script Y ahora corre bajo pytest (14 chequeos que antes no corrian en ninguna suite). Hallazgo asociado: **casi toda la suite del repo son scripts, no modulos de pytest** — es una convencion, no un error; queda escrita en `tests/README.md` con los comandos correctos. NO se convirtio ningun otro archivo. |

**Pendiente de Valle (no lo puedo hacer yo):** correr `bash "Nowcast Congreso Argy/.mapa/instalar-hook.sh"` desde la raiz git — los hooks no viajan en git — y `python -m pytest tests/ datos/proyectos/tests -q` en su PC. Lo del sandbox no cuenta como prueba.

**Migracion a `rutas.py`: va 2 de ~30 modulos, a proposito.** Los demas tienen claim abierto; se migran de a uno, reclamando el modulo. `tests/test_rutas.py` ya cubre el inventario completo aunque los modulos no esten migrados, asi que el valor no depende de terminarla.

## Sesion 2026-08-14 (Valle+Claude) — ABIERTA, condicionar la postura por ORIGEN FINO del proyecto

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **modelo/ensemble** | Claude (con Valle) | 2026-08-14 | **Claim a coordinar con Franco.** (1) `backtest_cadena.py` gana `--origen-por-proyecto`: condiciona la postura por el ORIGEN FINO del proyecto (leido de `features_proyecto`), memoiza por `(camara, mes, origen)`; opt-in, sin el flag = v1. (2) `ensemble.nowcast_proyecto`: P(mayoria) nunca 0%/100% (piso de desvio por legislador + techo de confianza; pedido de Valle). (3) control nuevo `validar_condicionamiento_votos.py`. Medido vs votos reales era-Milei: condicionar sube el acierto del voto de 59% a 76%. `proyectar_postura` (Franco) NO se toca: ya condiciona. Tests 53 (backtest) + 36 (ensemble). |
| **variables/proyecto** | Claude (con Valle) | 2026-08-14 | **Claim a coordinar con Franco.** Nueva categoria **ALIADOS** en el clasificador de origen (separa el partido de gobierno de sus aliados: PRO en Milei, UCR/CC en Macri) — arregla la contaminacion de OFICIALISMO. Aditivo: lista `NUCLEO` paralela + `clase_oficialismo`; `origen_lider`/`origen_por_acta`/`postura_gobierno` emiten ALIADOS. Test stale de PRO-Milei corregido. Tests 30 (origen_lider) + 20 (postura). **Regen pendiente (Valle, PowerShell):** `origen_por_acta.py` + `origen_lider.py`. |
| **casos/ (Parte B)** | Claude (con Valle) | 2026-08-14 | **HECHO.** Los dos informes bicamerales (`proyeccion_hipotetica_bicameral.py`, `nowcast_bicameral_html.py`) ya usan `proyectar_postura` CONDICIONADO por el origen fino del proyecto (antes `proyectar_lineas_alineacion`, que promediaba todo). Se agrego `ORIGEN` como parametro; el record individual del HTML se condiciona por origen; techo de confianza (nunca 0%/100%) tambien en el JS. Verificado en sandbox. `proyectar_lineas_alineacion` queda sin consumidores en casos/. |

**Decisiones de Valle (2026-08-14):** condicionar por CUATRO categorias — EJECUTIVO (mensajes del PE) / OFICIALISMO (partido propio) / **ALIADOS** (PRO y otros) / OPOSICION —; UNIFICAR hacia `proyectar_postura`; y que P(mayoria) nunca de 0%/100%. Evidencia en `validar_condicionamiento_votos.py`. **OJO: la etiqueta ALIADOS recien existe tras regenerar los parquet (corrida de Valle); hasta entonces el conditioning ve las 3 categorias viejas.**

## Sesion 2026-08-13 (Valle+Claude) — CERRADA, backtest de la cadena completa (modelo/ensemble). MODULO LIBRE.

| Modulo | Quien | Desde | Que se hizo |
|---|---|---|---|
| **modelo/ensemble** | Claude (con Valle) | 2026-08-13 | **Harness ENTREGADO** (`src/backtest_cadena.py` + `tests/test_backtest_cadena.py`, 31 checks / dos backends). Backtest de la CADENA COMPLETA (opcion B): sobre la cohorte etiquetada y MADURA del embudo, compone `p_llega x p_mayoria` (nowcast_auto, postura proyectada point-in-time + roster de conducta) y mide Brier/skill/calibracion contra `sancionado`, con el `p_sancion` del embudo como baseline. Consume contratos, no reimplementa. **Alcance v1 = DIPUTADOS** (Senado historico no rosteable con el padron por defecto; hueco Dip 2020-23). **Corrida real pendiente en la PC de Valle** (ver ESTADO). Claim liberado. |

## Sesion 2026-08-13 (Valle+Claude) — ABIERTA, separar INDISCIPLINA de AUSENTISMO (URGENTE 1)

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **modelo/voto_individual** | Claude (con Valle) | 2026-08-13 | `disciplina.py`: columnas ADITIVAS `tasa_desvio_conducta` (desvio votando ESTANDO PRESENTE), `tasa_desvio_ausencia`, `n_presente`, `tasa_desvio_disputadas_conducta`, `pct_ausente`, `ausentista_outlier` (umbral mu+2sigma). Fix de fuga: excluir placeholder "a Designar". NO se renombra ninguna columna consumida. |
| **variables/proyecto** | Claude (con Valle) | 2026-08-13 | Consumidor: `estimar_gamma_individual.py` lee `tasa_desvio_disputadas_conducta` (fallback a la actual) y QUITA los `ausentista_outlier` de la muestra del gamma. Corrida oficial con bootstrap la corre Valle en su PC. |
| **modelo/ensemble** | Valle (con Claude) | 2026-08-13 | **Claim a coordinar con Franco.** `roster_nominal` ahora lee la columna de CONDUCTA (`tasa_desvio_reciente_conducta` / `tasa_desvio_conducta`) con fallback a la mezclada, para que la PROYECCIÓN también use conducta (antes leía la mezclada con ausentismo). Aditivo, no rompe el contrato de salida. 3 tests nuevos (prefiere conducta / fallback / NaN), 32 OK. |

**Decisiones de Valle (2026-08-13):** vara de outlier = **2 sigma** (>~61% ausencia). Los outliers **sin mandato vigente se quitan** del analisis; **Schiaretti** (vigente, 63% ausente en su mandato) queda **marcado para revision de Valle**, no se borra. **Menem** (presidente de Diputados) ya esta excluido por `PRESIDENCIAS_DIPUTADOS` y en la proyeccion entra como LLA/gobierno via padron — NO queda como indisciplinado. El Senado no necesita la exclusion (preside la vicepresidenta, que no es senadora). **Coordinar con Franco (ensemble):** que `roster_nominal` lea la columna de conducta y que a los presidentes de camara se les de desvio ~0 (voto-ancla de su lado en desempates).

## Sesion 2026-08-11 (Valle+Claude) — ABIERTA, re-tratamiento del ICG (2 horizontes)

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **variables/proyecto** | Claude (con Valle) | 2026-08-11 | Claim a pedido de Valle (toca modulo de Franco, cambios ADITIVOS). Re-estimacion del gamma del ICG: se suaviza la senal en 2 capas point-in-time DENTRO de cada gobierno (fondo 6m + sacudon 3m) para sacar el sesgo de atenuacion del ICG mensual crudo; se ELIMINA la capa 2 global del analista (doble conteo). Toca icg_contexto.py, estimar_gamma_individual.py, modulador_icg.py + consumidores. Corrida oficial con IC la corre Valle. |

## Sesion 2026-08-07 (Valle+Claude) — CERRADA, el upsert del bot (ADR-0009). MODULOS LIBRES.

**Decision de Valle: Opcion B directa, con el Senado en la misma tanda.**
`proyectos.db` pasa a ser la fuente de verdad de los proyectos y el embudo lee de ahi.
Contrato y precedencia por campo en `DECISIONES/0009-proyectos-db-fuente-de-verdad-de-proyectos.md`.

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **datos/proyectos** | Claude (con Valle) | 2026-08-07 | Crear `proyectos.db` + capa de MERGE (no dos upserts: `upsert_proyecto` reemplaza las hijas completas y cargar dos fuentes seguidas pierde datos en cualquier orden). Migrar los 112.793 de CKAN. |
| **datos/bot_recoleccion** | Claude (con Valle) | 2026-08-07 | Upsert `tp_entradas` + `dae_entradas` -> `proyectos.db`, con cofirmantes completos y normalizacion del expediente del Senado (`S-2/26-PL` vs `4014-S-2013`). |
| **variables/embudo** | Claude (con Valle) | 2026-08-07 | Ruta de lectura desde SQLite dejando la de parquet viva como fallback. **No se apaga la vieja hasta que las dos den skill 0,3647 identico al cuarto decimal.** |

✅ **CERRADA el 07-08. Los tres modulos quedan LIBRES.** La condicion de aceptacion se cumplio:
cohorte identica celda por celda entre las dos rutas, y backtest 0,3643 / 0,4195 por ambas.
`proyectos.db` es la fuente de verdad; la ruta de parquet queda como fallback (`EMBUDO_FUENTE=parquet`).

## Sesion 2026-08-06 (Valle+Claude) — CERRADA, auditoria general del repo

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **coordinacion** | Claude (con Valle) | 2026-08-06 | Control general: armonizar bitacoras, cifras, memorias y READMEs; barrido archivo por archivo |
| **variables/proyecto** | Claude (con Valle) | 2026-08-06 | Precedencia de fuentes del ICG (Excel > informe) + escritura estable del CSV |
| **datos/argentinadatos** | Claude (con Valle) | 2026-08-06 | Ingesta del Senado: apuntarla al padron vigente para que el 2026 deje de entrar SIN BLOQUE (URGENTE 2) |

**✅ Los tres pendientes de esa lista se HICIERON el 07-08:**

| Modulo | Que era | Estado |
|---|---|---|
| `datos/bot_recoleccion` + `datos/proyectos` | el upsert que faltaba | **HECHO** — ADR-0009. `proyectos.db` existe (114.708 proyectos) y el bot entrega |
| `variables/proyecto` | auditoria de `n_giros` (sospecha de leakage) | **HECHO** por Franco el 07-08 — la sospecha se DESCARTO con evidencia |
| `variables/embudo` | regenerar `p_embudo.parquet` | **HECHO** — regenerado con 42.141 proyectos y el modelo sano |

## Sesion 2026-08-04 (Valle+Claude) — CERRADA, modulos liberados

| Modulo | Que se hizo | Estado |
|---|---|---|
| variables/embudo | ICG enchufado + ablacion; bug del one-hot de comisiones corregido | LIBRE |
| datos/padron | vigilar_padron.py (padron vivo) + padron a 257 | LIBRE |
| datos/bot_recoleccion | 2 workflows nuevos (padron lunes, ICG dia 5) — ⚠️ escritos pero **NO corriendo**: quedaron en la subcarpeta, ver URGENTE 4 | LIBRE |
| variables/proyecto | **ICG como modulador de coyuntura (ADR-0008)** + 3 paneles HTML | LIBRE |
| coordinacion | memorias consolidadas, CLAUDE.md destruncado, reglas nuevas en el PLAN | LIBRE |

## En curso

| Módulo | Quién | Desde | Rama |
|---|---|---|---|
| datos/decada_votada | Claude+Franco | 2026-06-25 | export_seed.R listo; falta correrlo en R |
| datos/canonica | Claude+Franco | 2026-06-25 | cubre Diputados 2011–2025 + Senado 2024–2025 |
| datos/seguimiento | Claude+Valle | 2026-06-29 | extractor de giros/trámite Dip+Sen — VALIDADO EN VIVO |
| datos/proyectos | Claude+Valle | 2026-06-29 | **FUENTE DE VERDAD de los proyectos (ADR-0009, 07-08)**: `proyectos.db` con 114.708 = CKAN + bot, con cofirmantes. El embudo lee de aca. + cuarentena aparte y 14 controles de integridad |
| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + ICG + origen/líder + tema_por_acta (1537). origen_por_acta.py = quién impulsa + gobierno POR ACTA (4 vías: código/embebido/O.D./título); 20 tests. Cobertura (2026-07-23): 59% global / 54,5% Senado (vía código embebido tapa el hueco 2004-2014). HALLAZGO: el nowcast del Senado a hoy se traba en la atribución de linaje de votos recientes (todo cae en OTRO/PROVINCIAL) = entity_resolution/Franco, no origen |
| modelo/voto_individual | Claude+Valle | 2026-07-01 | índice de disciplina individual + dimensionamiento del set pivote (gate 1 de 1B.4) |
| variables/legislador | Claude+Valle | 2026-07-01 | ficha individual por legislador (identidad, bloques, presentismo, perfil de voto, desvío) |
| datos/export | Claude+Valle | 2026-07-02 | base unificada: SQLite completo + Excel por gobierno; disputada = ±5% del umbral de mayoría |
| modelo/agregador_institucional | Claude+Valle | 2026-07-10 | motor de recuento como distribución (P aprobación con banda); tests 12 OK; falta backtest a escala |
| producto/dashboard | Claude+Valle | 2026-07-10 | PANEL-NOWCAST.html (raíz, doble clic): estado del sistema + simulador de votación (motor JS) |
| variables/asistencia_quorum | Claude+Valle | 2026-07-11 | escalón 1: presentismo por legislador + modo asistencia del agregador (arreglo del sesgo pesimista); falta backtest a escala |
| datos/expedientes | Claude+Franco | 2026-07-11 | backfill CKAN REFRESCADO 07-08 (113.177 proyectos, hasta 30-jun-2026; ojo: usa cache salvo REFRESH=1); embudo bruto 3,22%); fase 2 = cofirmantes vía bot. **08-08: enlace_senado.py** — acta↔expediente entre cámaras vía `exp_senado` (59,7%; Senado 80,4%), 39 proyectos con votación en las DOS cámaras. Cuello de botella: sólo 8,1% de las actas del Senado traen expediente |
| datos/bot_recoleccion | Claude+Franco | 2026-07-11 | bot diario BICAMERAL en GitHub Actions: DAE Senado (1.004 exp.) + TP Diputados con COFIRMANTES completos (13+13 tests) |
| variables/embudo | Claude+Valle | 2026-07-12 | supervivencia del proyecto de ley: embudo por etapas + modelo v1 (rasgos al presentar, sin leakage) + backtest temporal; consume contrato de datos/expedientes |
| modelo/ensemble | Claude+Valle | 2026-07-12 | P(aprob)=P(llega)×P(mayoría). ROSTER NOMINAL (2026-07-22): nowcast_auto simula UNA FILA POR LEGISLADOR (padrón vigente + desvío individual, escalera reciente→global→bloque); se eliminó _expandir_roster/demo. Dirección de bloque condicionable por tema/origen (consume tema_por_acta + origen_por_acta). Con --origen GOBIERNO el caso testigo 1167-D-2025 se endereza (LLA 0,33→0,88; kirchnerismo 0,85→0,44). Falta backtest de la cadena y automatizar el --origen del propio proyecto |
| variables/bloque | Claude+Valle | 2026-07-12 | dirección condicionada por tema/origen (shrinkage + guard de gobierno). NUEVO (2026-07-23): _enriquecer_linaje_senado recupera el linaje real de los votos del Senado 2024+ (llegaban SIN BLOQUE→OTRO/PROVINCIAL) contra el padrón mandate-aware → el nowcast del Senado YA CONDICIONA (n_cond 0→16-18). 37 tests. Override manual del Senado COMPLETO 22/22 (OTRO/PROVINCIAL 53%→26%). NUEVO: la postura EXCLUYE actas AUX (homenajes/trámite/tratados = consenso) para no inflar el share afirmativo; se nota en Diputados, en el Senado espera más actas contenciosas + multitema |
| datos/padron | Valle | 2026-07-14 | nómina oficial individual: Diputados 257 + Senado 72 vigentes (mandato desde-hasta, clave canónica, linaje). Composición a la fecha; enchufada al proyector (roster 375→257). **08-08: padrón HISTÓRICO del Senado** (243 tramos / 176 senadores / 2017→2031, wiki + oficial reconciliadas por apellido). Ya se puede backtestear la cadena entre cámaras |

## Hecho

| Módulo | Quién | Fecha | Nota |
|---|---|---|---|
| docs/schemas | Claude+Franco | 2026-06-25 | Esquema canónico schema_version=1 (acta + voto) |
| datos/senado | Claude+Franco | 2026-07-02 | 2015–2023 completo: 749 actas / 53.910 votos, validado vs nahuelhds (0 discrepancias), bloque histórico 100% / 0 anacronismos. **Padrón AUDITADO 11-07: 17/17 filas validadas, cero errores** (los desvíos altos son fractura real del FpV-PJ 2016-17). Pendiente de otros módulos: integrar a run_pipeline (canonica) + 2 ADRs |
| datos/argentinadatos | Claude+Franco | 2026-07-11 | Integrado con bloque del Senado 24-25 resuelto vía padrón versionado (SIN BLOQUE=0 en Senado; residuo menor en Dip) |
| docs/taxonomias | Claude+Valle | 2026-06-29 | Vocabulario controlado v1 (74 ids, id estable, multi-etiqueta) |
| evaluacion/baseline | Claude+Franco | 2026-06-25 | Baseline ~0,99 dirección / ~0,81 con asistencia |
| datos/ckan_diputados | Claude+Franco | 2026-06-25 | **Migración CUMPLIDA**: vive en `datos/ckan_diputados/src/to_canonical.py` y `run_pipeline.py` lo invoca (paso 2). El "pendiente migrar" era de arrastre, corregido el 06-08. Fuente congelada en 2020. |

## Congelado / no abrir aún

- ~~**modelo/voto_individual** — baseline cerrado, no invertir más esfuerzo.~~ **DESCONGELADO 2026-06-30:** reformulado por ADR-0003. El voto-dirección por bloque acierta ~0,99, pero ese número es un **promedio** que tapa a los díscolos: la varianza del conteo la cargan **10-20 bisagras** cuya (in)disciplina mueve la P(aprobación) en las votaciones ajustadas. El objetivo dejó de ser predecir el voto medio y pasó a ser **separar el comportamiento partidario del individual**. Reclamado por Claude+Valle el 2026-07-01 (ver "En curso").

- **datos/diputados_oficial** — PAUSADO 2026-07-10 por decisión de Valle (priorizar la puesta en marcha). No está congelado por técnica: se reanuda cuando el nowcast end-to-end esté cerrado.

<!-- Reparado el 2026-08-06: este archivo estaba TRUNCADO en disco, cortado a mitad
     de la palabra "reformulado". Es el tercer archivo dañado por el truncado del
     mount, después de CLAUDE.md (04-08) y PLAN-DE-TRABAJO.md (06-08). El texto se
     reconstruyó a partir de ADR-0003 y de la sección 1B.4 del PLAN.
     ⚠️ VERIFICAR CONTRA TU DISCO: ver la nota al final de este archivo. -->

---

## Nota de integridad (2026-08-06) — VERIFICADA, el truncado es viejo

Dos archivos de `coordinacion/` aparecen **cortados a mitad de una frase**: este
(`TABLERO.md`, reparado arriba) y `ESTADO-DEL-PROYECTO.md`, cuya última entrada
de la bitácora (29-06, `datos/seguimiento`) termina en "Tests offline contra
fixtures:" sin las tres líneas de cierre que llevan todas las demás.

**Se verificó con `git diff` antes de commitear.** Resultado: 115 inserciones
contra 12 borrados, y **los 12 borrados son ediciones intencionales** de la
sesión del 06-08 (las filas de la tabla de módulos con las cifras viejas y el
párrafo del Senado marcado como superado). **Ninguna línea de bitácora se
perdió en esta sesión.**

El detalle que lo confirma: el archivo terminaba **sin salto de línea final**,
mitad de palabra y sin newline es la firma clásica de una escritura truncada, y
por eso git mostró esa última línea como modificada al agregarle contenido
detrás. Un archivo que corta a viene de una sesión anterior — el mismo daño que
sufrieron `CLAUDE.md` (reparado el 04-08) y `PLAN-DE-TRABAJO.md`.

### Si querés recuperar el texto perdido de ESTADO (opcional, 1 minuto)

El corte está en el histórico, así que alguna revisión vieja puede tener la
entrada completa. Desde la raíz del repo:

```powershell
$ruta = "Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md"
git log --format="%h %ad" --date=short -- $ruta | ForEach-Object {
  $h = ($_ -split ' ')[0]
  $fin = (git show "${h}:$ruta") | Select-Object -Last 1
  "{0}  ->  ...{1}" -f $_, $fin.Substring([Math]::Max(0, $fin.Length - 55))
}
```

**Qué mirar:** la lista muestra en qué terminaba el archivo en cada commit. Si
alguna revisión NO termina en "Tests offline contra fixtures:", ahí está la
versión completa y se copia de `git show <hash>:<ruta>`. Si **todas** terminan
igual, el texto se perdió antes del primer commit y no hay nada que recuperar —
lo que falta es el cierre de una entrada de junio sobre `datos/seguimiento`, y
ese contenido está en `datos/seguimiento/README.md`.

No es bloqueante para nada. Esta sección se borra cuando lo resuelvas.
