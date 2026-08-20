# MAPA — Nowcast Congreso Argy

<!-- GENERADO por indexar.py. No editar: los cambios se pierden. -->
<!-- La prosa vive en el README.md de cada modulo (seccion `Buscar aca si`). -->
<!-- 2026-08-20 15:30 UTC · 121 archivos · 22,829 LOC -->

## Como usar este archivo

Es el unico archivo del proyecto que hace falta leer para empezar. Para ubicar algo concreto: `python3 .mapa/buscar.py "<termino>"` devuelve archivo y linea sin abrir nada. Recien despues abrir los archivos que salgan, y solo esos.

## Donde buscar que

| Si la consulta es sobre... | Ir a |
|---|---|
| el tablero ejecutivo del proyecto (`TABLERO-CONTROL.html`; se edita SOLO `tablero_datos.js`) | `./` |
| los KPIs, hitos o el estado de una pieza de la plataforma | `./` |
| los paneles HTML de coyuntura o el informe bicameral (los generadores estan en `casos/`) | `./` |
| por donde empezar a leer el repo | `./` |
| el informe o el HTML de una ley concreta (Ganancias, lobby, ...) | `casos/` |
| proyectar un proyecto por las DOS camaras (origen + revisora) | `casos/` |
| por que un caso da un numero distinto al del ensemble | `casos/` |
| el generador de los paneles HTML que estan en la raiz del repo | `casos/` |
| que hay que resolver antes de empezar a trabajar (`URGENTE.md`, siempre primero) | `coordinacion/` |
| que se hizo y cuando (`ESTADO-DEL-PROYECTO.md`, entrada mas reciente arriba) | `coordinacion/` |
| lo mismo contado sin tecnicismos (`EN-HUMANO.md`) | `coordinacion/` |
| que modulo esta tomado y por quien (`TABLERO.md`) | `coordinacion/` |
| por que se decidio algo (`DECISIONES/`, los ADR) | `coordinacion/` |
| como ramificar y mergear sin conflictos (`PROTOCOLO-GIT.md`) | `coordinacion/` |
| que hacer y en que orden, por modulo y fase (`PLAN-DE-TRABAJO.md`) | `coordinacion/` |
| votaciones 2020-2025 que faltan o llegan mal | `datos/argentinadatos/` |
| senadores sin bloque en esos anios (se resuelve con el padron del Senado) | `datos/argentinadatos/` |
| el modelo no ve los proyectos de las ultimas semanas | `datos/bot_recoleccion/` |
| el bot diario fallo, no commiteo, o abrio un issue | `datos/bot_recoleccion/` |
| scraping de Tramite Parlamentario (Diputados) o DAE (Senado) | `datos/bot_recoleccion/` |
| hasta que fecha llega lo que el bot entrego | `datos/bot_recoleccion/` |
| de donde sale un voto, un acta o un legislador (la tabla madre) | `datos/canonica/` |
| cuantos votos/actas hay en total, o desde/hasta que fecha llega la base | `datos/canonica/` |
| reconstruir la base de cero (`run_pipeline.py`, ~20 min con internet) | `datos/canonica/` |
| un legislador que aparece dos veces con nombres distintos (resolucion de entidades) | `datos/canonica/` |
| el hueco de Diputados 2020-23, o que fuente cubre que periodo | `datos/canonica/` |
| votaciones de Diputados 2011-2020 | `datos/ckan_diputados/` |
| el formato crudo de CKAN HCDN | `datos/ckan_diputados/` |
| de donde salen las votaciones anteriores a 2011 | `datos/decada_votada/` |
| por que hay codigo en R en un repo de Python | `datos/decada_votada/` |
| que se presento en el Congreso y en que quedo | `datos/expedientes/` |
| el enlace entre un acta de votacion y su expediente | `datos/expedientes/` |
| giros iniciales a comision, dictamenes, o si un expediente llego a ley | `datos/expedientes/` |
| el backfill de CKAN, o por que HCDN publica con ~5 semanas de atraso | `datos/expedientes/` |
| la ingesta trae menos/mas de lo esperado (`REFRESH=1`: por defecto usa CACHE) | `datos/expedientes/` |
| abrir las votaciones en Excel o consultarlas con SQL | `datos/export/` |
| que significa una votacion 'disputada' (margen +-5% de los emitidos) | `datos/export/` |
| la columna `periodo`, `gobierno` o `desvio` de la base consultable | `datos/export/` |
| el export salio sin desvio (falta correr antes `disciplina.py`) | `datos/export/` |
| votaciones de 2026 que no vinieron por API | `datos/manual_2026/` |
| el bloque del Senado en el periodo vigente | `datos/manual_2026/` |
| cuantas bancas tiene un bloque a una fecha, o quien estaba en el recinto | `datos/padron/` |
| el cuerpo aparece inflado o desinflado (contar votantes vs. roster real) | `datos/padron/` |
| recambio del 10-dic, reemplazos, renuncias, bancas vacantes | `datos/padron/` |
| el padron cambio y hay que revisarlo (`vigilar_padron.py`, corre los lunes) | `datos/padron/` |
| el padron historico del Senado (reconstruido de nomina oficial + Wikipedia) | `datos/padron/` |
| cuantos proyectos de ley hay, o si uno existe en la base | `datos/proyectos/` |
| autores, cofirmantes, giros a comision o taxonomias de un proyecto | `datos/proyectos/` |
| la base de proyectos no cuadra / se cargo mal (`verificar.py`, 14 invariantes) | `datos/proyectos/` |
| una fila rara que no hay que dejar entrar (cuarentena, base aparte) | `datos/proyectos/` |
| rehacer `proyectos.db` (no viaja a git: `migrar_ckan.py` + `upsert_bot.py`, ~1 min) | `datos/proyectos/` |
| el control de cohorte (`verificar.py`): la MIDE `variables/embudo` como proceso y aca se controla el resultado | `datos/proyectos/` |
| en que etapa esta un expediente concreto | `datos/seguimiento/` |
| giros a comision o movimientos de tramite de un proyecto | `datos/seguimiento/` |
| el PDF del texto de un proyecto | `datos/seguimiento/` |
| votaciones del Senado que faltan, o el hueco 2015-2023 | `datos/senado/` |
| que bloque tenia un senador en el momento de votar | `datos/senado/` |
| scraping del Senado (cachea HTML; la primera corrida tarda ~20 min) | `datos/senado/` |
| filas REVISAR del padron manual de bloques del Senado | `datos/senado/` |
| que columnas y tipos tiene que tener un parquet de la canonica | `docs/schemas/` |
| cambiar un contrato de datos (requiere ADR + aviso en TABLERO) | `docs/schemas/` |
| que temas existen y como se llaman | `docs/taxonomias/` |
| agregar, renombrar o fusionar una taxonomia | `docs/taxonomias/` |
| el prompt con el que se clasifica un proyecto por titulo | `docs/taxonomias/` |
| un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta) | `docs/taxonomias/` |
| validacion temporal o fuga de informacion del futuro | `evaluacion/backtesting/` |
| cuanto acierta la regla de bloque (~0,99 en direccion del voto individual) | `evaluacion/baseline/` |
| contra que se compara un modelo nuevo | `evaluacion/baseline/` |
| como se mide si el modelo es bueno | `evaluacion/metricas/` |
| de donde sale el 0,99 del baseline de bloque | `fase0/` |
| por que el proyecto NO apunta a predecir la direccion del voto individual | `fase0/` |
| el codigo original de ingesta, anterior a `datos/` | `fase0/` |
| si un proyecto junta los votos: quorum, mayoria simple/absoluta/dos tercios | `modelo/agregador_institucional/` |
| simular una votacion con un escenario de bloques dado | `modelo/agregador_institucional/` |
| por que sin condicionar por tema y origen todos los bloques quedan 'a favor' | `modelo/agregador_institucional/` |
| el numero final de P(sancion) de un proyecto | `modelo/ensemble/` |
| el backtest de la cadena completa, Brier, skill o calibracion | `modelo/ensemble/` |
| la Puerta D / camara revisora en el circuito bicameral | `modelo/ensemble/` |
| condicionar la postura por el origen del proyecto | `modelo/ensemble/` |
| P(mayoria) que da 0% o 100% (hay piso y techo por pedido de Valle) | `modelo/ensemble/` |
| quien se desvia de su bloque, discolos, bisagras o pivotes | `modelo/voto_individual/` |
| separar INDISCIPLINA de AUSENTISMO (son dos tasas distintas) | `modelo/voto_individual/` |
| el indice de disciplina por legislador y por periodo | `modelo/voto_individual/` |
| presidentes de camara excluidos del calculo | `modelo/voto_individual/` |
| servir el nowcast por HTTP (todavia no existe) | `producto/api/` |
| los paneles que se abren con doble clic (estan en la raiz, no aca) | `producto/dashboard/` |
| el tablero ejecutivo `TABLERO-CONTROL.html` (se edita solo `tablero_datos.js`) | `producto/dashboard/` |
| los informes bicamerales por caso (los generadores estan en `casos/`) | `producto/dashboard/` |
| dos modulos tienen una copia de la misma funcion y hay que ver si siguen de acuerdo | `tests/` |
| una definicion compartida (periodo parlamentario, tipo de mayoria, bancas por camara) cambio en un lado | `tests/` |
| un test falla y no pertenece a ningun modulo en particular | `tests/` |
| quien falta a las votaciones, presentismo por periodo | `variables/asistencia_quorum/` |
| quorum, o si una votacion se cae por ausencias | `variables/asistencia_quorum/` |
| OJO: alimentar el motor con presentismo PROMEDIO lo empeora — se usa la posicion del bloque entre PRESENTES | `variables/asistencia_quorum/` |
| que postura toma un bloque en un tema, o cuan cohesionado esta | `variables/bloque/` |
| un bloque que se parte (fractura, indice de Rice) | `variables/bloque/` |
| linajes de bloque (peronismo federal, progresismo) y como se agrupan | `variables/bloque/` |
| proyectar la alineacion de bloques a una fecha (point-in-time) | `variables/bloque/` |
| OJO: su columna `periodo` es un ANIO legislativo, no el periodo de dos anios del resto del repo | `variables/bloque/` |
| senal de prensa o clima politico como variable (todavia no existe) | `variables/contexto/` |
| por que la mayoria de los proyectos nunca se votan | `variables/embudo/` |
| P(llega al recinto), cohorte, o proyectos maduros vs. en curso | `variables/embudo/` |
| escenarios y contrafactuales (`escenarios.py`) — los coeficientes de la logistica NO son efectos | `variables/embudo/` |
| el skill del embudo o su backtest temporal | `variables/embudo/` |
| leer de `proyectos.db` vs. del parquet (`EMBUDO_FUENTE=parquet`) | `variables/embudo/` |
| medir la cohorte por las DOS rutas (parquet vs `proyectos.db`): `src/cohorte_dos_rutas.py`, que consume `datos/proyectos` | `variables/embudo/` |
| el historial completo de un diputado o senador | `variables/legislador/` |
| por que bloques paso un legislador | `variables/legislador/` |
| presentismo o perfil de voto individual | `variables/legislador/` |
| armar el Mapa de Influencia o fichas para el producto | `variables/legislador/` |
| de que tema es un proyecto (clasificador de taxonomias contra `taxonomias.json`) | `variables/proyecto/` |
| quien impulsa un proyecto: EJECUTIVO / OFICIALISMO / ALIADOS / OPOSICION | `variables/proyecto/` |
| el ICG (indice de confianza en el gobierno) y el gamma que modula el desvio | `variables/proyecto/` |
| el efecto lider / jefe de bloque (1,25x, no el 7x que se creia) | `variables/proyecto/` |
| postura del gobierno frente a un proyecto | `variables/proyecto/` |
| carpeta grande: 17 archivos — buscar por simbolo con `.mapa/buscar.py` antes de abrir | `variables/proyecto/` |

## Carpetas

| Carpeta | Que es | Arch. | LOC | Bitacora |
|---|---|---:|---:|---|
| `variables/proyecto/` _(src+tests)_ | Feature store por proyecto: tema/materia, origen (Ejecutivo/oficialismo/aliados/oposicion), jefe de bloque, mayoria requerida, texto, y el ICG como modulador de coyuntura. | 26 | 4,951 | ok |
| `modelo/ensemble/` _(src+tests)_ | La composicion final: el nowcast end-to-end de un proyecto. Compone P(llega al recinto) x P(mayoria dado recinto) y corre el backtest de la cadena completa. | 7 | 2,074 | ok |
| `datos/proyectos/` _(src+tests)_ | Base de Proyectos de Ley (`proyectos.db`): una fila por proyecto identificado por denominador NNNN-X-AAAA. Fuente de verdad del universo de proyectos y denominador del embudo (ADR-0009). | 10 | 2,073 | ok |
| `datos/expedientes/` _(src+tests)_ | Registro de todo lo PRESENTADO (no solo lo votado): titulo, autor, tipo, fecha y cadena de vida del expediente. Denominador del embudo y enlace acta -> expediente. | 7 | 1,697 | ok |
| `datos/padron/` _(src+tests)_ | Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72). | 6 | 1,511 | ok |
| `variables/bloque/` _(src+tests)_ | Cohesion, tamano, postura y fracturas de cada bloque en el tiempo, y el proyector point-in-time que arma el escenario por bloque que consume el ensemble. | 6 | 1,238 | ok |
| `variables/embudo/` _(src+tests)_ | Supervivencia del proyecto: presentado -> comision -> dictamen -> recinto -> sancion. Estima P(llega al recinto), la mitad de P(aprobacion). Es el diferencial del nowcast. | 5 | 1,222 | ok |
| `datos/senado/` _(src+tests)_ | Ingesta de votaciones nominales del Senado desde senado.gob.ar + reconstruccion del bloque historico contemporaneo a cada voto. Tapa el hueco 2015-2023. | 5 | 930 | ok |
| `datos/bot_recoleccion/` _(src+tests)_ | El bot diario que trae lo nuevo de ambas camaras (proyectos con firmantes y giros, y votaciones) con upsert idempotente. Corre solo en GitHub Actions. | 7 | 869 | ok |
| `coordinacion/` | Las bitacoras y el protocolo: que bloquea a otros, que se hizo, quien tomo que modulo y por que se decidio cada cosa. Aca NO hay codigo del producto. | 8 | 680 | ok |
| `modelo/voto_individual/` _(src+tests)_ | No predice el voto medio (eso lo resuelve la regla de bloque ~0,99): modela el DESVIO del legislador respecto de su bloque y detecta pivotes (ADR-0003). | 2 | 613 | ok |
| `./` | La raiz del proyecto: los paneles que se abren con doble clic, el tablero ejecutivo y su unica fuente de datos (`tablero_datos.js`). | 2 | 558 | ok |
| `datos/seguimiento/` _(src+tests)_ | Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. Insumo del embudo. NO descubre proyectos nuevos. | 2 | 512 | ok |
| `datos/argentinadatos/` _(src+tests)_ | Ingesta de Diputados 2020-2025 y Senado 2024-2025 desde la API argentinadatos.com, normalizada al mismo esquema que CKAN. | 3 | 469 | ok |
| `modelo/agregador_institucional/` _(src+tests)_ | Traduce posturas de bloque + asistencia en un resultado institucional: cuenta bancas, quorum, umbrales de mayoria y bandas. Mide la estructura, no la politica. | 2 | 452 | ok |
| `casos/` | Aplicaciones del nowcast a un caso real (una ley concreta): el scoring, el informe en HTML y la proyeccion bicameral. Consumen los contratos de `modelo/` y `variables/`; no definen modelo propio. | 2 | 426 | ok |
| `tests/` | Tests que cruzan modulos y por eso no pueden vivir dentro de ninguno. Cada modulo tiene sus propios tests en `<modulo>/tests/`; acá van solo los que verifican acuerdos ENTRE modulos. | 2 | 410 | ok |
| `datos/export/` _(src+tests)_ | La canonica armonizada en formatos consultables: un SQLite unico para el programa y Excel por gobierno para humanos. Solo LEE la canonica. | 2 | 404 | ok |
| `datos/canonica/` _(src)_ | La base propia y unica de votaciones nominales: todas las fuentes unificadas, deduplicadas y con entidades resueltas. Fuente de verdad de la que leen `variables/` y `modelo/`. | 3 | 393 | ok |
| `variables/legislador/` _(src+tests)_ | Una ficha por legislador que voto alguna vez: identidad, camara, distrito, periodos, trayectoria de bloques, presentismo, perfil de voto y tasa de desvio. | 2 | 392 | ok |
| `fase0/` _(src)_ | La Fase 0, cerrada: medir cuanto acierta predecir el voto individual mirando al bloque. Resultado ~0,99, y ese resultado ordena todo el proyecto. Se conserva como registro; no se desarrolla mas. | 3 | 297 | ok |
| `datos/decada_votada/` _(src)_ | Semilla historica de un solo uso: el dataset de Andy Tow ('La Decada Votada') exportado una vez y normalizado. No se depende de el en vivo (ADR-0002). | 2 | 170 | ok |
| `docs/taxonomias/` | La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, su cargador y el prompt del clasificador. Es un CATALOGO, no un modelo. | 3 | 160 | ok |
| `variables/asistencia_quorum/` _(src)_ | Modelo de asistencia/ausencia/abstencion por legislador. Es donde vive la incertidumbre que el bloque no explica. | 1 | 104 | ok |
| `evaluacion/baseline/` _(src)_ | El piso a superar: el baseline de bloque, ya medido. Cualquier modelo nuevo se compara contra esto. | 1 | 83 | ok |
| `datos/manual_2026/` _(src)_ | El Excel curado a mano por Franco (2025-2027) integrado al esquema canonico: votos 2026 de ambas camaras, con bloque del Senado, provincia y mandato. | 1 | 72 | ok |
| `datos/ckan_diputados/` _(src)_ | Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle). | 1 | 69 | ok |
| `docs/schemas/` | Los contratos de datos del repo (schema_version). Es lo unico compartido y fragil: cambiarlo exige un ADR. | 0 | 0 | ok |
| `evaluacion/backtesting/` | Validacion walk-forward (entrenar en t, validar en t+1) con test de no-leakage. PENDIENTE. | 0 | 0 | ok |
| `evaluacion/metricas/` | Metricas comunes: Brier, calibracion, accuracy en votos cruzados, cobertura de bandas. PENDIENTE. | 0 | 0 | ok |
| `producto/api/` | API de servicio (FastAPI) para la fase nube. FUTURO: no abrir sin pagador validado. | 0 | 0 | ok |
| `producto/dashboard/` | Tablero interno: radar de traccion, mapa de pivotes y escenarios. La v1 se entrego como paneles HTML sueltos en la RAIZ del repo, no como app. | 0 | 0 | ok |
| `variables/contexto/` | Senal cualitativa de prensa y contexto politico (factor mu). FUTURO: no bloquea el MVP. | 0 | 0 | ok |

## Puntos de entrada

- `casos/nowcast_bicameral_html.py`
- `casos/proyeccion_hipotetica_bicameral.py`
- `datos/argentinadatos/src/explorar_campos.py`
- `datos/argentinadatos/src/to_canonical.py`
- `datos/argentinadatos/tests/test_padron_senado.py`
- `datos/bot_recoleccion/src/dae_senado.py`
- `datos/bot_recoleccion/src/tp_diputados.py`
- `datos/bot_recoleccion/src/votaciones.py`
- `datos/canonica/src/build.py`
- `datos/canonica/src/entity_resolution.py`

## Archivos centrales

Ordenados por cuantos otros archivos dependen de ellos. Tocar uno de arriba tiene mas radio de impacto.

| Archivo | LOC | Lo usan | Simbolos |
|---|---:|---:|---|
| `variables/bloque/src/bloque.py` | 633 | 8 | `_canon_linaje`, `_norm_nombre`, `_cargar_padron_linaje_senado`, `_enriquecer_linaje_senado` |
| `variables/embudo/src/embudo.py` | 730 | 6 | `cargar_icg`, `_mes_rezagado`, `cargar`, `cargar_sqlite` |
| `modelo/ensemble/src/ensemble.py` | 444 | 5 | `_cargar_simulador`, `_cargar_proyector`, `componer`, `_root` |
| `variables/proyecto/src/origen_lider.py` | 395 | 3 | `_norm`, `_linaje_code`, `oficialista_por_fecha`, `clase_oficialismo` |
| `modelo/agregador_institucional/src/agregador.py` | 345 | 3 | `normalizar_mayoria`, `umbral_aprobacion`, `_prob_conductas`, `simular_votacion` |
| `variables/proyecto/src/modulador_icg.py` | 255 | 3 | `_cargar_tramos`, `encoger_desvio`, `_gamma_tramo`, `gamma_fondo` |
| `datos/proyectos/src/verificar.py` | 237 | 3 | `Control`, `_abrir`, `controles_base`, `control_cohorte` |
| `datos/proyectos/src/cuarentena.py` | 192 | 3 | `Avalancha`, `_ahora`, `Cuarentena`, `resumen` |
| `variables/proyecto/src/agente_taxonomias.py` | 495 | 2 | `Asignacion`, `ResultadoClasificacion`, `_lista_y_reglas`, `construir_prompt` |
| `datos/proyectos/src/upsert_bot.py` | 310 | 2 | `_norm`, `_ahora`, `catalogo_comisiones`, `separar_giros_tp` |
| `datos/canonica/src/entity_resolution.py` | 243 | 2 | `_strip`, `_name_key`, `_leg_id`, `_bloque_norm` |
| `modelo/ensemble/src/puerta_d.py` | 217 | 2 | `camara_revisora`, `_padron_de`, `_clip01`, `_logit` |

## Flujo interno

- `variables/proyecto/tests/` → `variables/proyecto/src/` (10)
- `datos/proyectos/tests/` → `datos/proyectos/src/` (5)
- `variables/bloque/tests/` → `variables/bloque/src/` (4)
- `datos/bot_recoleccion/tests/` → `datos/bot_recoleccion/src/` (3)
- `modelo/ensemble/tests/` → `modelo/ensemble/src/` (3)
- `casos/` → `variables/bloque/src/` (2)
- `casos/` → `modelo/ensemble/src/` (2)
- `datos/expedientes/tests/` → `datos/expedientes/src/` (2)
- `datos/padron/src/` → `datos/canonica/src/` (2)
- `datos/padron/tests/` → `datos/padron/src/` (2)
- `modelo/ensemble/src/` → `modelo/agregador_institucional/src/` (2)
- `variables/embudo/tests/` → `variables/embudo/src/` (2)

## Fuentes externas

- `datos.hcdn.gob.ar` — `datos/ckan_diputados/src/to_canonical.py`, `datos/expedientes/src/explorar_ckan.py`, `datos/expedientes/src/ingesta_ckan.py`
- `senado.gob.ar` — `datos/bot_recoleccion/src/dae_senado.py`, `datos/seguimiento/src/giros.py`, `datos/seguimiento/tests/fixtures/senado_1091.26.html`
- `hcdn.gob.ar` — `datos/bot_recoleccion/src/explorar_tp.py`, `datos/bot_recoleccion/src/tp_diputados.py`, `datos/proyectos/tests/test_store.py`
- `api.argentinadatos.com` — `datos/argentinadatos/README.md`, `datos/argentinadatos/src/explorar_campos.py`, `datos/argentinadatos/src/to_canonical.py`
- `hcdn.gov.ar` — `datos/proyectos/tests/test_store.py`, `datos/seguimiento/src/giros.py`
- `utdt.edu` — `variables/proyecto/README.md`, `variables/proyecto/src/ingesta_icg.py`
- `rest.hcdn.gob.ar` — `datos/bot_recoleccion/tests/fixtures/tp_87_144.html`
- `cloud.r-project.org` — `datos/decada_votada/export_seed.R`
- `proyectos2.senado.gov.ar` — `datos/senado/muestras/Senado_2002-03-05_muestra.html`
- `es.wikipedia.org` — `datos/senado/src/bajar_anexos_wiki.py`
- `votaciones.hcdn.gob.ar` — `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`
- `argentinadatos.com` — `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`

## Configuracion requerida

- `ANTHROPIC_API_KEY` — `variables/proyecto/src/agente_taxonomias.py`
- `ASIST` — `modelo/agregador_institucional/src/agregador.py`
- `BORRAR` — `datos/canonica/src/entity_resolution.py`
- `CACHE` — `datos/expedientes/src/ingesta_ckan.py`, `datos/senado/src/scrape_votaciones.py`
- `CAMARA` — `modelo/ensemble/validar_condicionamiento_votos.py`
- `CANON` — `datos/canonica/src/entity_resolution.py`, `datos/export/src/export_base.py`, `modelo/agregador_institucional/src/agregador.py`
- `CLEAN` — `datos/canonica/src/build.py`, `variables/embudo/src/cohorte_dos_rutas.py`
- `CSV` — `datos/decada_votada/src/from_csv.py`
- `DISC` — `modelo/agregador_institucional/src/agregador.py`
- `DISCIPLINA` — `modelo/ensemble/src/ensemble.py`
- `EMBUDO_FUENTE` — `variables/embudo/src/embudo.py`
- `EXPEDIENTES` — `modelo/ensemble/src/ensemble.py`
- `EXPORT_CACHE` — `datos/export/src/export_base.py`
- `EXP_CLEAN` — `variables/embudo/src/embudo.py`, `variables/proyecto/src/origen_lider.py`
- `FINO` — `modelo/ensemble/validar_condicionamiento_votos.py`
