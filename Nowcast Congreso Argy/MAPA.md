# MAPA — Nowcast Congreso Argy

<!-- GENERADO por indexar.py. No editar: los cambios se pierden. -->
<!-- La prosa vive en el README.md de cada modulo (seccion `Buscar aca si`). -->
<!-- 2026-09-08 01:45 UTC · 162 archivos · 38,865 LOC -->

## Como usar este archivo

Es el unico archivo del proyecto que hace falta leer para empezar. Para ubicar algo concreto: `python3 .mapa/buscar.py "<termino>"` devuelve archivo y linea sin abrir nada. Recien despues abrir los archivos que salgan, y solo esos.

Rama `main` — ultimo commit: 2026-09-07 bc26bf7 aaa · **hay cambios sin commitear**

## Donde buscar que

| Si la consulta es sobre... | Ir a |
|---|---|
| el tablero ejecutivo, los KPIs, los hitos o el estado de una pieza de la plataforma (`TABLERO-CONTROL.html`; se edita SOLO `tablero_datos.js`) | `./` |
| por donde empezar a leer el repo | `./` |
| que significa "periodo parlamentario", que mayoria exige un proyecto o cuantas bancas tiene una camara (`definiciones.py`) | `./` |
| el informe o el HTML de una ley concreta (Ganancias, lobby, ...), y el generador de los paneles que estan en la RAIZ | `casos/` |
| proyectar un proyecto por las DOS camaras (origen + revisora) | `casos/` |
| por que un caso da un numero distinto al del ensemble, o por que un generador de esta carpeta esta neutralizado y cual lo reemplaza | `casos/` |
| que hay que resolver antes de empezar a trabajar (`URGENTE.md`, siempre primero) | `coordinacion/` |
| la FORMULA del numero abierta hasta la ultima variable (`FORMULA-COMPLETA.md`; se actualiza al tocar el motor, ADR-0015) | `coordinacion/` |
| por que se decidio algo, y que se hizo cuando (`DECISIONES/` + `ESTADO-DEL-PROYECTO.md`; sin tecnicismos, `EN-HUMANO.md`) | `coordinacion/` |
| votaciones 2020-2025 que faltan o llegan mal | `datos/argentinadatos/` |
| senadores sin bloque en esos anios (se resuelve con el padron del Senado) | `datos/argentinadatos/` |
| el modelo no ve los proyectos de las ultimas semanas, o hasta que fecha llega lo que el bot entrego | `datos/bot_recoleccion/` |
| el bot diario fallo, no commiteo, o abrio un issue | `datos/bot_recoleccion/` |
| scraping de Tramite Parlamentario (Diputados) o DAE (Senado) | `datos/bot_recoleccion/` |
| de donde sale un voto, un acta o un legislador (la tabla madre), y hasta que fecha llega | `datos/canonica/` |
| reconstruir la base de cero (`run_pipeline.py`, ~20 min con internet) | `datos/canonica/` |
| un legislador que aparece dos veces con nombres distintos (resolucion de entidades; el censo de duplicados esta en `outputs/`) | `datos/canonica/` |
| el hueco de Diputados 2020-23, o que fuente cubre que periodo | `datos/canonica/` |
| votaciones de Diputados 2011-2020 | `datos/ckan_diputados/` |
| el formato crudo de CKAN HCDN | `datos/ckan_diputados/` |
| de donde salen las votaciones anteriores a 2011 | `datos/decada_votada/` |
| por que hay codigo en R en un repo de Python | `datos/decada_votada/` |
| giros iniciales a comision, dictamenes, o si un expediente llego a ley | `datos/expedientes/` |
| el enlace acta -> expediente: la tabla es `acta_expediente_todas.parquet` (las DOS camaras, con `proyecto_id` resuelto); `acta_expediente.parquet` es el volcado crudo de CKAN y solo tiene Diputados | `datos/expedientes/` |
| el backfill de CKAN, o por que HCDN publica con ~5 semanas de atraso | `datos/expedientes/` |
| la ingesta trae menos/mas de lo esperado (`REFRESH=1`: por defecto usa CACHE) | `datos/expedientes/` |
| QUIEN firmo un dictamen, si hubo disidencias y de que bloque es cada firma | `datos/expedientes/` |
| como se arma la URL del PDF de una Orden del Dia de HCDN | `datos/expedientes/` |
| los dictamenes del Senado (otra fuente y otro scraper: `ingesta_od_senado.py`), y por que casi no tiene mayoria/minoria: es real, no es el parser (ADR-0017), su desacuerdo va como DISIDENCIA | `datos/expedientes/` |
| que significa `dictamen_clase = "desconocido"` (no se encontro el rotulo; NO es "despacho unico") | `datos/expedientes/` |
| comparar comisiones: SIEMPRE matchear contra el catalogo (los nombres tienen comas; partir por separadores rompe) | `datos/expedientes/` |
| `expedientes_giros` mezcla las DOS camaras: filtrar por camara antes de contar cobertura | `datos/expedientes/` |
| cuantas ODs faltan bajar (2.523 de ley identificadas, 1.722 parseadas) y como reanudar `ingesta_od.py` | `datos/expedientes/` |
| abrir las votaciones en Excel o consultarlas con SQL; la columna `periodo`, `gobierno` o `desvio` | `datos/export/` |
| que significa una votacion 'disputada' (margen +-5% de los emitidos) | `datos/export/` |
| el export salio sin desvio (falta correr antes `disciplina.py`) | `datos/export/` |
| por que el Excel salio del pipeline (sus 17 actas eran gemelas de argentinadatos) | `datos/manual_2026/` |
| cuantas bancas tiene un bloque a una fecha, o quien estaba en el recinto | `datos/padron/` |
| el cuerpo aparece inflado o desinflado; un anio da mas de 257 bancas (son duplicados de entity resolution) | `datos/padron/` |
| recambio del 10-dic, reemplazos, renuncias, bancas vacantes | `datos/padron/` |
| el padron cambio y hay que revisarlo (`vigilar_padron.py`, corre los lunes en CI; local escribe a `Archivos_Borrar/`) | `datos/padron/` |
| el padron HISTORICO (Senado: nomina oficial + Wikipedia; Diputados: reconstruido de la canonica, porque la nomina oficial solo cubre la foto vigente — 81 de 257 bancas en 2008) | `datos/padron/` |
| cuantos proyectos de ley hay, si uno existe, y sus autores, cofirmantes o giros | `datos/proyectos/` |
| la base de proyectos no cuadra / se cargo mal (`verificar.py`, 14 invariantes), o una fila rara que no hay que dejar entrar (cuarentena, base aparte) | `datos/proyectos/` |
| rehacer `proyectos.db` (no viaja a git: `migrar_ckan.py` + `upsert_bot.py`, ~1 min) | `datos/proyectos/` |
| en que etapa esta un expediente concreto | `datos/seguimiento/` |
| giros a comision o movimientos de tramite de un proyecto | `datos/seguimiento/` |
| el PDF del texto de un proyecto | `datos/seguimiento/` |
| votaciones del Senado que faltan, o el hueco 2015-2023 | `datos/senado/` |
| que bloque tenia un senador en el momento de votar, y las filas REVISAR del padron manual | `datos/senado/` |
| scraping del Senado (cachea HTML; la primera corrida tarda ~20 min) | `datos/senado/` |
| que tema tiene un acta o un proyecto, y de donde salio esa asignacion | `datos/taxonomias/` |
| por que las taxonomias no aparecian: estaban repartidas en cuatro lugares | `datos/taxonomias/` |
| que columnas y tipos tiene que tener un parquet de la canonica | `docs/schemas/` |
| cambiar un contrato de datos (requiere ADR + aviso en TABLERO) | `docs/schemas/` |
| que temas existen, como se llaman, y como se agrega, renombra o fusiona uno | `docs/taxonomias/` |
| el prompt con el que se clasifica un proyecto por titulo | `docs/taxonomias/` |
| un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta) | `docs/taxonomias/` |
| cuanto acierta la regla de bloque (~0,99 en direccion del voto individual) | `evaluacion/baseline/` |
| contra que se compara un modelo nuevo | `evaluacion/baseline/` |
| cuanto pierde el record individual en cada era, y cuanto lo arregla el guard | `evaluacion/baseline/` |
| de donde sale el 0,99 del baseline de bloque, y por que el proyecto NO apunta a predecir la direccion del voto individual | `fase0/` |
| el codigo original de ingesta, anterior a `datos/` | `fase0/` |
| si un proyecto junta los votos: quorum, mayoria simple/absoluta/dos tercios | `modelo/agregador_institucional/` |
| simular una votacion con un escenario de bloques dado | `modelo/agregador_institucional/` |
| por que sin condicionar por tema y origen todos los bloques quedan 'a favor' | `modelo/agregador_institucional/` |
| el quorum y las abstenciones: `presentes = afirm + neg` por defecto; el arreglo esta implementado detras de `QUORUM_ABSTENCIONES=1` y medido (hoy mueve 0,0000) | `modelo/agregador_institucional/` |
| por que la ausencia NO sale del desvio sino de `p_presente`, y por que el epsilon es un CLIP y no un modelo de riesgo sistemico | `modelo/agregador_institucional/` |
| el numero final de P(sancion) de un proyecto | `modelo/ensemble/` |
| el backtest de la cadena completa, Brier, skill o calibracion | `modelo/ensemble/` |
| la Puerta D / camara revisora en el circuito bicameral | `modelo/ensemble/` |
| P(mayoria) que da 0% o 100% (hay piso y techo por pedido de Valle) | `modelo/ensemble/` |
| REVISION 25-08: multiplicar P_B x P_D supone INDEPENDENCIA entre camaras y es falsa; y `P(B|A)` es notacion enganosa (A y C son un corrimiento en logit, no un condicional bayesiano) | `modelo/ensemble/` |
| el sobre tablas: 12,5% de las leyes se sancionan SIN dictamen y el modelo no lo contempla | `modelo/ensemble/` |
| diferencia entre la BANDA (p5-p95, agregada) y los PIVOTES (P individual en [0,35;0,65]) | `modelo/ensemble/` |
| quien se desvia de su bloque, discolos, bisagras o pivotes | `modelo/voto_individual/` |
| separar INDISCIPLINA de AUSENTISMO (son dos tasas distintas) | `modelo/voto_individual/` |
| el indice de disciplina por legislador y por periodo; presidentes de camara excluidos | `modelo/voto_individual/` |
| por que el desvio tiene piso (0,02) y no techo: ningun legislador llega a 1,0 (max observado 0,944) | `modelo/voto_individual/` |
| los paneles y el tablero ejecutivo que se abren con doble clic (estan en la RAIZ, no aca; se edita solo `tablero_datos.js`) | `producto/dashboard/` |
| de donde sale el numero: el mapa de la maquinaria (`MAPA-MODELO.html`), que script transforma que dato y que piezas estan parqueadas | `producto/dashboard/` |
| como se dibuja el circuito bicameral, y regenerar los datos de un panel sin tocar su HTML | `producto/dashboard/` |
| una definicion compartida (periodo parlamentario, tipo de mayoria, bancas por camara) cambio en un lado, o alguien volvio a pegarla adentro de un modulo en vez de usar `definiciones.py` | `tests/` |
| dos modulos tienen una copia de la misma funcion y hay que ver si siguen de acuerdo | `tests/` |
| un test falla y no pertenece a ningun modulo en particular | `tests/` |
| quien falta a las votaciones, presentismo por periodo | `variables/asistencia_quorum/` |
| quorum, o si una votacion se cae por ausencias | `variables/asistencia_quorum/` |
| OJO: alimentar el motor con presentismo PROMEDIO lo empeora — se usa la posicion del bloque entre PRESENTES | `variables/asistencia_quorum/` |
| que postura toma un bloque en un tema, cuan cohesionado esta, o si se parte (fractura, indice de Rice) | `variables/bloque/` |
| linajes de bloque (peronismo federal, progresismo) y como se agrupan | `variables/bloque/` |
| proyectar la alineacion de bloques a una fecha (point-in-time) | `variables/bloque/` |
| OJO: su columna `periodo` es un ANIO legislativo, no el periodo de dos anios del resto del repo | `variables/bloque/` |
| por que la mayoria de los proyectos nunca se votan; P(llega al recinto), cohorte, maduros vs. en curso | `variables/embudo/` |
| escenarios y contrafactuales (`escenarios.py`) — los coeficientes de la logistica NO son efectos | `variables/embudo/` |
| el skill del embudo o su backtest temporal | `variables/embudo/` |
| leer de `proyectos.db` vs. del parquet (`EMBUDO_FUENTE=parquet`), y medir la cohorte por las DOS rutas (`src/cohorte_dos_rutas.py`) | `variables/embudo/` |
| el historial completo de un diputado o senador, y por que bloques paso | `variables/legislador/` |
| presentismo o perfil de voto individual | `variables/legislador/` |
| armar el Mapa de Influencia o fichas para el producto | `variables/legislador/` |
| de que tema es un proyecto, quien lo impulsa (EJECUTIVO / OFICIALISMO / ALIADOS / OPOSICION) y cual es la postura del gobierno | `variables/proyecto/` |
| el ICG (indice de confianza en el gobierno) y el gamma que modula el desvio | `variables/proyecto/` |
| el efecto lider / jefe de bloque (1,25x, no el 7x que se creia) | `variables/proyecto/` |
| carpeta grande: 17 archivos — buscar por simbolo con `.mapa/buscar.py` antes de abrir | `variables/proyecto/` |
| REVISION 25-08: el log del ICG es SIMETRICO y la politica no — la asimetria existia en el mecanismo eliminado el 11-08 | `variables/proyecto/` |
| por que el promedio del gobierno no tiene leakage (`shift(1)` + `expanding`) | `variables/proyecto/` |

## Carpetas

| Carpeta | Que es | Arch. | LOC | Bitacora |
|---|---|---:|---:|---|
| `./` | La raiz del proyecto: los paneles que se abren con doble clic, el tablero ejecutivo y su unica fuente de datos (`tablero_datos.js`). | 6 | 5,878 | **vencida** |
| `variables/proyecto/` _(src+tests)_ | Feature store por proyecto: tema/materia, origen (Ejecutivo/oficialismo/aliados/oposicion), jefe de bloque, mayoria requerida, texto, y el ICG como modulador de coyuntura. | 26 | 5,024 | **vencida** |
| `modelo/ensemble/` _(src+tests)_ | La composicion final: el nowcast end-to-end de un proyecto. Compone P(llega al recinto) x P(mayoria dado recinto) y corre el backtest de la cadena completa. | 16 | 4,933 | **vencida** |
| `datos/expedientes/` _(src+tests)_ | Registro de todo lo PRESENTADO (no solo lo votado): titulo, autor, tipo, fecha y cadena de vida del expediente. Denominador del embudo y enlace acta -> expediente. | 15 | 4,499 | **vencida** |
| `datos/padron/` _(src+tests)_ | Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72). | 11 | 2,645 | **vencida** |
| `datos/proyectos/` _(src+tests)_ | Base de Proyectos de Ley (`proyectos.db`): una fila por proyecto identificado por denominador NNNN-X-AAAA. Fuente de verdad del universo de proyectos y denominador del embudo (ADR-0009). | 10 | 2,073 | **vencida** |
| `variables/bloque/` _(src+tests)_ | Cohesion, tamano, postura y fracturas de cada bloque en el tiempo, y el proyector point-in-time que arma el escenario por bloque que consume el ensemble. | 6 | 1,238 | **vencida** |
| `variables/embudo/` _(src+tests)_ | Supervivencia del proyecto: presentado -> comision -> dictamen -> recinto -> sancion. Estima P(llega al recinto), la mitad de P(aprobacion). Es el diferencial del nowcast. | 5 | 1,222 | **vencida** |
| `evaluacion/baseline/` _(src+tests)_ | El piso a superar: el baseline de bloque, ya medido. Cualquier modelo nuevo se compara contra esto. | 5 | 1,118 | **vencida** |
| `datos/canonica/` _(src+tests)_ | La base propia y unica de votaciones nominales: todas las fuentes unificadas, deduplicadas y con entidades resueltas. Fuente de verdad de la que leen `variables/` y `modelo/`. | 7 | 990 | **vencida** |
| `datos/senado/` _(src+tests)_ | Ingesta de votaciones nominales del Senado desde senado.gob.ar + reconstruccion del bloque historico contemporaneo a cada voto. Tapa el hueco 2015-2023. | 5 | 940 | **vencida** |
| `datos/bot_recoleccion/` _(src+tests)_ | El bot diario que trae lo nuevo de ambas camaras (proyectos con firmantes y giros, y votaciones) con upsert idempotente. Corre solo en GitHub Actions. | 7 | 880 | **vencida** |
| `casos/` | Aplicaciones del nowcast a un caso real (una ley concreta): el scoring, el informe en HTML y la proyeccion bicameral. Consumen los contratos de `modelo/` y `variables/`; no definen modelo propio. | 3 | 842 | **vencida** |
| `tests/` | Tests que cruzan modulos y por eso no pueden vivir dentro de ninguno. Cada modulo tiene sus propios tests en `<modulo>/tests/`; acá van solo los que verifican acuerdos ENTRE modulos. | 4 | 836 | ok |
| `coordinacion/` | Las bitacoras y el protocolo: que bloquea a otros, que se hizo, quien tomo que modulo y por que se decidio cada cosa. Aca NO hay codigo del producto. | 8 | 680 | **vencida** |
| `modelo/voto_individual/` _(src+tests)_ | No predice el voto medio (eso lo resuelve la regla de bloque ~0,99): modela el DESVIO del legislador respecto de su bloque y detecta pivotes (ADR-0003). | 2 | 597 | **vencida** |
| `modelo/agregador_institucional/` _(src+tests)_ | Traduce posturas de bloque + asistencia en un resultado institucional: cuenta bancas, quorum, umbrales de mayoria y bandas. Mide la estructura, no la politica. | 2 | 589 | **vencida** |
| `producto/dashboard/` _(src)_ | Tablero interno: radar de traccion, mapa de pivotes y escenarios, y el MAPA DEL MODELO: el diagrama de flujo BICAMERAL de como se calcula P(sancion) -dos bloques espejo, origen y revisora, con el condicionamiento entre camaras dibujado-, generado desde el indice del repo. Los entregables se abren con doble clic desde la RAIZ; el codigo del generador vive aca. | 1 | 563 | ok |
| `datos/seguimiento/` _(src+tests)_ | Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. Insumo del embudo. NO descubre proyectos nuevos. | 2 | 512 | **vencida** |
| `datos/argentinadatos/` _(src+tests)_ | Ingesta de Diputados 2020-2025 y Senado 2024-2025 desde la API argentinadatos.com, normalizada al mismo esquema que CKAN. | 3 | 469 | **vencida** |
| `datos/taxonomias/` _(src+tests)_ | El registro unico de taxonomias asignadas: una fila por (objeto, taxonomia), en CSV versionado, consolidado desde todas las fuentes que existian sueltas. | 2 | 435 | **vencida** |
| `variables/legislador/` _(src+tests)_ | Una ficha por legislador que voto alguna vez: identidad, camara, distrito, periodos, trayectoria de bloques, presentismo, perfil de voto y tasa de desvio. | 2 | 387 | **vencida** |
| `datos/export/` _(src+tests)_ | La canonica armonizada en formatos consultables: un SQLite unico para el programa y Excel por gobierno para humanos. Solo LEE la canonica. | 2 | 386 | **vencida** |
| `datos/manual_2026/` _(src+tests)_ | El Excel curado a mano por Franco (2025-2027). FUERA DEL PIPELINE desde el 06-09: sus 17 actas eran las mismas votaciones que ya trae argentinadatos, con fecha y expediente. | 2 | 331 | **vencida** |
| `fase0/` _(src)_ | La Fase 0, cerrada: medir cuanto acierta predecir el voto individual mirando al bloque. Resultado ~0,99, y ese resultado ordena todo el proyecto. Se conserva como registro; no se desarrolla mas. | 3 | 297 | **vencida** |
| `datos/decada_votada/` _(src)_ | Semilla historica de un solo uso: el dataset de Andy Tow ('La Decada Votada') exportado una vez y normalizado. No se depende de el en vivo (ADR-0002). | 2 | 170 | **vencida** |
| `docs/taxonomias/` | La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, su cargador y el prompt del clasificador. Es un CATALOGO, no un modelo. | 3 | 160 | **vencida** |
| `variables/asistencia_quorum/` _(src)_ | Modelo de asistencia/ausencia/abstencion por legislador. Es donde vive la incertidumbre que el bloque no explica. | 1 | 102 | **vencida** |
| `datos/ckan_diputados/` _(src)_ | Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle). | 1 | 69 | **vencida** |
| `docs/schemas/` | Los contratos de datos del repo (schema_version). Es lo unico compartido y fragil: cambiarlo exige un ADR. | 0 | 0 | ok |
| `evaluacion/backtesting/` | Validacion walk-forward (entrenar en t, validar en t+1) con test de no-leakage. PENDIENTE. | 0 | 0 | ok |
| `evaluacion/metricas/` | Metricas comunes: Brier, calibracion, accuracy en votos cruzados, cobertura de bandas. PENDIENTE. | 0 | 0 | ok |
| `producto/api/` | API de servicio (FastAPI) para la fase nube. FUTURO: no abrir sin pagador validado. | 0 | 0 | ok |
| `variables/contexto/` | Senal cualitativa de prensa y contexto politico (factor mu). FUTURO: no bloquea el MVP. | 0 | 0 | ok |

## Inventario de datos

140 archivos de datos · 195.2 MB · 105 viajan por git, **35 no**.

Buscar uno sin abrir nada: `python .mapa/buscar.py --dato <termino>`. Columna **git**: `si` = esta versionado, o sea que quien clone lo tiene; `NO` = vive solo en el disco de quien lo genero, que es el modo de falla mas repetido de este repo (seis veces, ver `.gitignore`). **Escribe/Lee**: quien lo produce y quien lo consume, deducido del codigo; sin lector, sobra — sin escritor, no se regenera.

| Archivo | Forma | Peso | git | Escribe | Lee |
|---|---|---:|:---:|---|---|
| `casos/2026-07-31_ley-de-lobby_scoring.json` | objeto: scoring, observado | 2 KB | si | — | — |
| `datos/bot_recoleccion/data/clean/tp_entradas.parquet` _BOT_TP_ENTRADAS_ | 3,426×11 | 460 KB | si | `tp_diputados.py` | `giros_iniciales.py`, `upsert_bot.py`, `verificar.py` |
| `datos/bot_recoleccion/data/clean/dae_entradas.parquet` | 1,072×8 | 124 KB | si | `dae_senado.py`, `test_verificar.py` | `upsert_bot.py`, `verificar.py` |
| `datos/bot_recoleccion/data/clean/votaciones_nuevas.parquet` | 542×11 | 37 KB | si | `votaciones.py` | — |
| `datos/bot_recoleccion/data/estado_bot.json` | objeto: dae_normal, tp_diputados, actas_ | 19 KB | si | `dae_senado.py`, `tp_diputados.py` | — |
| `datos/canonica/data/clean/_decada_csv/votaciones-diputados.csv` | 383,744×4 | 4.9 MB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/votos_resuelto.parquet` _CANONICA_VOTOS_RESUELTO_ | 948,488×12 | 2.0 MB | si | `entity_resolution.py`, `asistencia.py` | `export_base.py`, `padron_diputados_historico.py`, `baseline_canonico.py` +5 |
| `datos/canonica/data/clean/_decada_csv/votaciones-senado.csv` | 144,792×4 | 1.8 MB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/votos_canonico.parquet` _CANONICA_VOTOS_ | 948,488×8 | 1.2 MB | si | `build.py`, `entity_resolution.py` | _(2 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/asuntos-senado.csv` | 2,011×19 | 1.0 MB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/asuntos-diputados.csv` | 1,499×18 | 651 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/actas_canonico.parquet` _CANONICA_ACTAS_ | 5,946×14 | 475 KB | si | `build.py`, `asistencia.py` | `entity_resolution.py`, `enlace_senado.py`, `export_base.py` +11 |
| `datos/canonica/data/clean/_sources/decada_votada_actas.parquet` | 3,153×14 | 309 KB | **NO** | — | — |
| `datos/canonica/data/clean/_sources/decada_votada_votos.parquet` | 437,144×8 | 258 KB | **NO** | — | — |
| `datos/canonica/data/clean/_sources/ckan_diputados_votos.parquet` | 256,581×8 | 251 KB | **NO** | `to_canonical.py` | — |
| `datos/canonica/outputs/actas_gemelas_2026-09-06.csv` | 1,076×8 | 158 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/argentinadatos_votos.parquet` | 84,311×8 | 123 KB | **NO** | `to_canonical.py` | — |
| `datos/canonica/data/clean/_sources/senado_actas.parquet` | 749×14 | 70 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/ckan_diputados_actas.parquet` | 999×14 | 43 KB | **NO** | `to_canonical.py` | — |
| `datos/canonica/outputs/legislador_id_duplicados_2026-09-04.csv` | 153×22 | 43 KB | **NO** | — | — |
| `datos/canonica/data/clean/_decada_csv/diputados.csv` | 1,037×3 | 40 KB | **NO** | `padron_diputados_historico.py`, `test_ingesta_padron.py` | `to_canonical.py`, `comparar_vias_icg.py` |
| `datos/canonica/data/clean/_sources/senado_votos.parquet` | 53,910×8 | 39 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/argentinadatos_actas.parquet` | 415×14 | 29 KB | **NO** | `to_canonical.py` | — |
| `datos/canonica/outputs/legislador_id_merge_aprobado_2026-09-04.csv` | 114×11 | 22 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/manual_2026_votos.parquet` | 3,072×8 | 18 KB | **NO** | `to_canonical.py` | _(1 lo nombran)_ |
| `datos/canonica/data/alias_legislador_id.csv` | 184×1 | 16 KB | si | — | `alias_legislador.py` |
| `datos/canonica/data/clean/_sources/manual_2026_actas.parquet` | 17×14 | 9 KB | **NO** | `to_canonical.py` | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/senadores.csv` | 176×3 | 7 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/bloques-diputados.csv` | 183×3 | 5 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/baseline_canonico.json` | objeto: n_votos_sustantivos, por_nivel,  | 2 KB | **NO** | — | — |
| `datos/canonica/data/clean/_decada_csv/bloques-senado.csv` | 52×3 | 1 KB | **NO** | — | _(1 lo nombran)_ |
| `datos/decada_votada/data/clean/decada_votada_votos.parquet` | 6,425×8 | 23 KB | **NO** | `export_seed.R`, `from_csv.py` | — |
| `datos/decada_votada/data/clean/decada_votada_actas.parquet` | 25×14 | 8 KB | **NO** | `export_seed.R`, `from_csv.py` | — |
| `datos/expedientes/data/clean/expedientes.parquet` | 113,177×9 | 10.5 MB | si | `enlace_senado.py`, `ingesta_ckan.py` | `actas_ley.py`, `construir_firmas.py`, `giros_iniciales.py` +6 |
| `datos/expedientes/data/clean/expedientes_giros.parquet` | 422,939×3 | 2.1 MB | si | `ingesta_ckan.py`, `migrar_ckan.py` | `giros_iniciales.py`, `upsert_bot.py`, `verificar.py` +1 |
| `datos/expedientes/data/clean/expedientes_movimientos.parquet` | 141,550×4 | 1.6 MB | si | `ingesta_ckan.py`, `migrar_ckan.py` | `giros_iniciales.py`, `verificar.py` |
| `datos/expedientes/data/clean/expedientes_resultados.parquet` _EXPEDIENTES_RESULTADOS_ | 117,412×7 | 946 KB | si | `enlace_senado.py`, `ingesta_ckan.py` | `ingesta_od.py`, `origen_por_acta.py` |
| `datos/expedientes/data/clean/dictamenes_firmas.parquet` _EXPEDIENTES_FIRMAS_ | 125,561×28 | 921 KB | si | `construir_firmas.py` | `verificar_regeneracion.py` |
| `datos/expedientes/data/clean/acta_expediente_todas.parquet` _EXPEDIENTES_ACTA_EXP_TODAS_ | 5,004×13 | 421 KB | si | `enlace_senado.py`, `tema_por_acta.py` | `actas_ley.py`, `verificar_regeneracion.py` |
| `datos/expedientes/data/clean/expedientes_dictamenes.parquet` | 23,891×8 | 372 KB | si | `ingesta_ckan.py`, `migrar_ckan.py` | _(2 lo nombran)_ |
| `datos/expedientes/data/clean/dictamenes_firmas_senado.parquet` _EXPEDIENTES_FIRMAS_SENADO_ | 18,163×30 | 207 KB | si | `construir_firmas.py` | _(4 lo nombran)_ |
| `datos/expedientes/data/clean/acta_expediente.parquet` _EXPEDIENTES_ACTA_EXP_ | 1,849×7 | 164 KB | si | `enlace_senado.py`, `ingesta_ckan.py` | `baseline_voto_individual.py`, `estimar_beta_dictamen.py`, `origen_por_acta.py` |
| `datos/expedientes/data/clean/cadena_camaras.parquet` | 1,166×17 | 150 KB | si | `enlace_senado.py` | `estimar_psi_arrastre.py` |
| `datos/expedientes/data/clean/dictamenes_comisiones.parquet` _EXPEDIENTES_DICTAMENES_COMISIONES_ | 10,031×8 | 88 KB | si | `construir_firmas.py` | — |
| `datos/expedientes/data/clean/expedientes_leyes.parquet` | 1,340×7 | 38 KB | si | — | `origen_lider.py` |
| `datos/expedientes/data/clean/giros_iniciales.parquet` | 2,927×4 | 23 KB | si | `giros_iniciales.py` | `embudo.py` |
| `datos/expedientes/data/clean/comisiones_integrantes.parquet` | 1,477×3 | 9 KB | si | — | `origen_lider.py` |
| `datos/expedientes/data/clean/comisiones_autoridades.parquet` | 141×5 | 7 KB | si | — | `origen_lider.py` |
| `datos/export/data/votaciones_2003-2007_Kirchner.xlsx` | 3 hoja(s) | 15.8 MB | si | — | — |
| `datos/export/data/votaciones_2015-2019_Macri.xlsx` | 3 hoja(s) | 9.8 MB | si | — | — |
| `datos/export/data/votaciones_2007-2011_CFK-1.xlsx` | 3 hoja(s) | 8.3 MB | si | — | — |
| `datos/export/data/votaciones_2011-2015_CFK-2.xlsx` | 3 hoja(s) | 8.1 MB | si | — | — |
| `datos/export/data/votaciones_2023-2027_Milei.xlsx` | 3 hoja(s) | 4.6 MB | si | — | — |
| `datos/export/data/votaciones_2019-2023_Fernandez.xlsx` | 3 hoja(s) | 1.8 MB | si | — | — |
| `datos/export/data/votaciones_2002-2003_Duhalde.xlsx` | 3 hoja(s) | 766 KB | si | — | — |
| `datos/export/data/votaciones_1999-2001_DeLaRua.xlsx` | 3 hoja(s) | 377 KB | si | — | — |
| `datos/manual_2026/Congreso_25-27.xlsx` _MANUAL_2026_XLSX_ | 4 hoja(s) | 52 KB | si | — | _(3 lo nombran)_ |
| `datos/padron/data/padron_diputados_historico.csv` _PADRON_DIPUTADOS_HISTORICO_ | 7,323×12 | 2.0 MB | si | `padron_diputados_historico.py` | `resolver_firmantes.py` |
| `datos/padron/data/padron_diputados.csv` _PADRON_DIPUTADOS_ | 1,454×12 | 260 KB | si | `test_ingesta_padron.py`, `test_ensemble.py` | `resolver_firmantes.py`, `to_canonical.py`, `comparar_vias_icg.py` |
| `datos/padron/data/nomina_diputados.csv` | 1,454×6 | 103 KB | si | `test_ingesta_padron.py` | _(3 lo nombran)_ |
| `datos/padron/data/padron_senado_historico.csv` _PADRON_SENADO_HISTORICO_ | 243×12 | 45 KB | si | `test_guardas_confianza.py`, `test_puerta_d.py` | `resolver_firmantes.py` |
| `datos/padron/data/raw/nomina_senado.csv` | 72×15 | 16 KB | si | — | _(2 lo nombran)_ |
| `datos/padron/data/padron_senado.csv` _PADRON_SENADO_ | 72×12 | 13 KB | si | `test_bloque_linaje_senado.py` | `to_canonical.py`, `test_padron_senado.py`, `resolver_firmantes.py` +2 |
| `datos/padron/data/senado_linaje_manual.csv` _PADRON_SENADO_LINAJE_MANUAL_ | 25×7 | 2 KB | si | `test_bloque_linaje_senado.py` | `padron_senado_historico.py`, `bloque.py` |
| `datos/padron/data/estado_vigilancia.json` | objeto: diputados, senado | 445 B | si | — | _(2 lo nombran)_ |
| `datos/proyectos/data/proyectos.db` _PROYECTOS_DB_ | — | 85.7 MB | si | `schema.sql`, `store.py` | `verificar.py`, `test_store.py` |
| `datos/proyectos/data/cuarentena.db` _PROYECTOS_CUARENTENA_DB_ | 0×1 | 20 KB | si | — | `cuarentena.py` |
| `datos/proyectos/data/taxonomias.csv` | 0×6 | 65 B | si | `taxonomias_backup.py` | `test_store.py` |
| `datos/senado/data/clean/senado_actas.parquet` | 749×14 | 70 KB | **NO** | `scrape_votaciones.py` | `aplicar_bloques.py`, `padron_bloques.py` |
| `datos/senado/data/padron_bloques_senado.csv` _SENADO_PADRON_BLOQUES_ | 291×8 | 39 KB | si | `padron_bloques.py` | `to_canonical.py`, `padron_senado_historico.py`, `aplicar_bloques.py` |
| `datos/senado/data/clean/senado_votos.parquet` | 53,910×8 | 39 KB | **NO** | `aplicar_bloques.py`, `scrape_votaciones.py` | `padron_bloques.py` |
| `datos/senado/data/padron_manual_2015_2017.csv` | 131×8 | 23 KB | si | `padron_bloques.py` | `to_canonical.py`, `aplicar_bloques.py` |
| `datos/senado/data/_diag_sin_cobertura.csv` | 7×3 | 266 B | **NO** | `aplicar_bloques.py` | — |
| `datos/taxonomias/data/asignaciones.csv` | 6,772×8 | 563 KB | si | `registro.py` | _(2 lo nombran)_ |
| `docs/schemas/acta.schema.json` | objeto: $schema, $id, title, description | 2 KB | si | `build.py` | — |
| `docs/schemas/voto.schema.json` | objeto: $schema, $id, title, description | 1 KB | si | `build.py` | — |
| `docs/taxonomias/taxonomias.json` | objeto: schema_version, actualizado, not | 7 KB | si | — | `registro.py`, `loader.py` |
| `evaluacion/baseline/outputs/guard_era_medicion.json` | objeto: _que_es, _n_votos, resultados, m | 4 KB | si | `medir_guard_era.py` | — |
| `evaluacion/baseline/outputs/diagnostico_senado.json` | objeto: senado | 4 KB | si | `diagnostico_senado.py` | — |
| `evaluacion/baseline/outputs/baseline_voto_individual.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | `baseline_voto_individual.py` | `verificar_regeneracion.py` |
| `evaluacion/baseline/outputs/baseline_guard_shrink.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_guard_off.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/record_por_tema_2026-09-04.json` | objeto: _que_es, _como_se_reproduce, el_ | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/merge_ids_medicion_2026-09-04.json` | objeto: _que_es, _como_se_midio, _alias, | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_canonico.json` | objeto: n_votos_sustantivos, por_nivel,  | 2 KB | si | `baseline_canonico.py` | — |
| `fase0/data/raw/detalle_129_137.csv` | 231,043×7 | 17.6 MB | **NO** | — | `ingesta.py` |
| `fase0/data/clean/detalle.parquet` | 231,043×7 | 1.4 MB | **NO** | `ingesta.py` | `baseline_bloque.py` |
| `fase0/data/raw/cabecera_129_137.csv` | 899×20 | 183 KB | **NO** | — | `ingesta.py` |
| `fase0/data/clean/cabecera.parquet` | 899×20 | 45 KB | **NO** | `ingesta.py` | `baseline_bloque.py` |
| `fase0/outputs/baseline_resultados.json` | objeto: fuente, n_actas_total, n_votos_s | 701 B | si | `baseline_bloque.py` | — |
| `modelo/agregador_institucional/outputs/backtest_agregador_asistencia.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_agregador.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_agregador_dir_presentes.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/ensemble/outputs/beta_dictamen.json` | objeto: M0_crudo, M1_offset, M2_offset_t | 5 KB | si | `estimar_beta_dictamen.py` | `verificar_regeneracion.py` |
| `modelo/ensemble/outputs/epsilon_tau.json` | objeto: n_votos, n_actas, epsilon, tau_s | 4 KB | si | `estimar_epsilon_tau.py` | — |
| `modelo/ensemble/outputs/beta_dictamen_senado.json` | objeto: M0_crudo, M1_offset, M2_offset_t | 4 KB | si | — | `verificar_regeneracion.py` |
| `modelo/ensemble/outputs/beta_dictamen_ab_2026-09-04.json` | objeto: _que_es, _como_se_reproduce, cor | 3 KB | si | — | — |
| `modelo/ensemble/outputs/psi_arrastre.json` | objeto: P1_psi_unico, P1b_psi_con_tema_o | 3 KB | si | `estimar_psi_arrastre.py` | — |
| `modelo/ensemble/outputs/nowcast_HIP-SALUD-OPO.json` | objeto: proyecto_id, proyecto_id_interno | 3 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_1167-D-2025.json` | objeto: proyecto_id, proyecto_id_interno | 3 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_HIP-ECON-PE.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_HIP.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_HIPOTETICO-ECON-PE.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/backtest_cadena.json` | objeto: n_evaluados, tasa_base_sancion,  | 2 KB | si | — | — |
| `modelo/ensemble/outputs/backtest_cadena_fina.json` | objeto: n_evaluados, version, tasa_base_ | 2 KB | si | — | — |
| `modelo/ensemble/outputs/theta_sobre_tablas.json` | objeto: A_theta_vs_resto, B_solo_sobre_t | 1 KB | si | `estimar_theta_sobre_tablas.py` | — |
| `modelo/voto_individual/outputs/desvios_por_voto.parquet` _DESVIOS_POR_VOTO_ | 955,025×6 | 1.3 MB | **NO** | `disciplina.py` | `export_base.py` |
| `modelo/voto_individual/outputs/disciplina_por_anio.csv` | 9,474×7 | 647 KB | si | `disciplina.py`, `ficha.py` | — |
| `modelo/voto_individual/outputs/disciplina_por_periodo.csv` | 4,847×10 | 474 KB | si | `disciplina.py`, `ficha.py` | — |
| `modelo/voto_individual/outputs/disciplina_individual.csv` _DISCIPLINA_INDIVIDUAL_ | 1,960×23 | 344 KB | si | `test_ensemble.py`, `disciplina.py` | `agregador.py`, `comparar_vias_icg.py`, `estimar_gamma_individual.py` |
| `modelo/voto_individual/outputs/set_pivote.json` | objeto: definicion, min_votos, legislado | 1 KB | si | `disciplina.py` | — |
| `producto/dashboard/data/mapa_modelo_semantica.json` | objeto: _comentario, version, meta, etap | 72 KB | si | — | `generar_mapa_modelo.py` |
| `variables/bloque/outputs/serie_bloque.parquet` | 304×9 | 16 KB | si | `COMMITEAR-2026-09-08.ps1`, `bloque.py` | _(2 lo nombran)_ |
| `variables/embudo/outputs/p_embudo.parquet` | 42,141×5 | 432 KB | si | `embudo.py` | `backtest_cadena.py` |
| `variables/embudo/outputs/backtest_embudo.json` | objeto: sancionado, sancionado_sin_orige | 151 KB | si | `embudo.py` | _(1 lo nombran)_ |
| `variables/embudo/outputs/embudo_por_comision.csv` | 65×4 | 3 KB | si | `embudo.py` | — |
| `variables/embudo/outputs/embudo_por_anio.csv` | 19×5 | 539 B | si | `embudo.py` | — |
| `variables/embudo/outputs/embudo_etapas.csv` | 1×12 | 263 B | si | `embudo.py` | _(1 lo nombran)_ |
| `variables/embudo/outputs/embudo_por_origen.csv` | 4×5 | 200 B | si | — | — |
| `variables/embudo/outputs/embudo_por_camara.csv` | 2×5 | 139 B | si | `embudo.py` | — |
| `variables/embudo/outputs/embudo_por_lider.csv` | 2×5 | 125 B | si | — | — |
| `variables/legislador/data/legisladores.xlsx` | 5 hoja(s) | 1.0 MB | si | `ficha.py` | — |
| `variables/legislador/data/legisladores.csv` | 1,972×22 | 397 KB | si | `ficha.py` | `origen_lider.py`, `origen_por_acta.py` |
| `variables/legislador/data/legisladores.parquet` | 1,972×22 | 168 KB | **NO** | `export_base.py`, `ficha.py` | — |
| `variables/legislador/data/legislador_periodo.parquet` | 4,795×10 | 133 KB | **NO** | `export_base.py`, `ficha.py` | — |
| `variables/legislador/data/legislador_anio.parquet` | 9,287×8 | 102 KB | **NO** | `ficha.py` | — |
| `variables/legislador/data/legislador_bloques.parquet` | 3,232×7 | 52 KB | **NO** | `ficha.py` | `origen_lider.py`, `origen_por_acta.py` |
| `variables/proyecto/data/features_proyecto.parquet` _PROYECTO_FEATURES_ | 41,470×10 | 327 KB | si | `origen_lider.py` | `backtest_cadena.py` |
| `variables/proyecto/data/origen_por_acta.parquet` _PROYECTO_ORIGEN_POR_ACTA_ | 6,231×9 | 89 KB | si | `origen_por_acta.py` | `nowcast_puertas.py`, `bloque.py`, `estimar_gamma.py` +2 |
| `variables/proyecto/data/tema_por_acta.parquet` _PROYECTO_TEMA_POR_ACTA_ | 3,083×8 | 78 KB | si | `tema_por_acta.py` | `registro.py`, `bloque.py` |
| `variables/proyecto/data/icg_contexto.parquet` | 297×18 | 34 KB | si | — | `estimar_gamma.py`, `estimar_gamma_individual.py`, `modulador_icg.py` |
| `variables/proyecto/outputs/muestra_manual_taxonomias.csv` | 88×6 | 24 KB | si | — | _(2 lo nombran)_ |
| `variables/proyecto/data/jefes_bloque.csv` _PROYECTO_JEFES_BLOQUE_ | 108×2 | 14 KB | si | `origen_lider.py` | `estimar_beta_dictamen.py` |
| `variables/proyecto/data/icg_mensual.csv` _PROYECTO_ICG_MENSUAL_ | 297×5 | 11 KB | si | `embudo.py`, `test_ingesta_icg.py` | `nowcast_puertas_html.py`, `icg_contexto.py` |
| `variables/proyecto/data/jefes_bloque_oficial.csv` | 58×2 | 7 KB | si | `scrape_jefes_bloque.py` | `estimar_beta_dictamen.py`, `origen_lider.py` |
| `variables/proyecto/outputs/gamma_icg_dos_capas.json` | objeto: modelo, ma_fondo, ma_corto, nota | 2 KB | si | `estimar_gamma_individual.py` | _(1 lo nombran)_ |
| `variables/proyecto/data/curva_ciclo_presidencial.csv` _PROYECTO_CURVA_CICLO_ | 47×6 | 2 KB | si | — | `comparar_vias_icg.py` |
| `variables/proyecto/data/calendario_electoral.csv` | 30×3 | 2 KB | si | `COMMITEAR-2026-09-08.ps1` | `icg_contexto.py` |
| `variables/proyecto/outputs/gamma_icg_individual.json` | objeto: umbral_pivote, con_vol, resultad | 838 B | si | `estimar_gamma_individual.py` | — |
| `variables/proyecto/outputs/gamma_icg.json` | objeto: n_actas, n_meses, con_vol, boot | 649 B | si | `estimar_gamma.py` | — |

**Lo que el inventario marca**

- No viajan por git y pesan (>100 KB): `fase0/data/raw/detalle_129_137.csv`, `datos/canonica/data/clean/_decada_csv/votaciones-diputados.csv`, `datos/canonica/data/clean/_decada_csv/votaciones-senado.csv`, `fase0/data/clean/detalle.parquet`, `modelo/voto_individual/outputs/desvios_por_voto.parquet`, `datos/canonica/data/clean/_decada_csv/asuntos-senado.csv`, `datos/canonica/data/clean/_decada_csv/asuntos-diputados.csv`, `datos/canonica/data/clean/_sources/decada_votada_actas.parquet` _+8_. Cada uno vive en un solo disco.
- Tienen productor y **ningun consumidor** (42): `votaciones_nuevas.parquet`, `estado_bot.json`, `argentinadatos_actas.parquet`, `argentinadatos_votos.parquet`, `ckan_diputados_actas.parquet`, `ckan_diputados_votos.parquet`, `manual_2026_actas.parquet`, `manual_2026_votos.parquet` _+34_. Es lo esperable en un entregable para humanos; en un intermedio significa que sobra.
- **Ningun archivo de codigo los nombra** (30, 50.3 MB): `votaciones_2003-2007_Kirchner.xlsx`, `votaciones_2015-2019_Macri.xlsx`, `votaciones_2007-2011_CFK-1.xlsx`, `votaciones_2011-2015_CFK-2.xlsx`, `votaciones_2023-2027_Milei.xlsx`, `votaciones_2019-2023_Fernandez.xlsx`, `votaciones_2002-2003_Duhalde.xlsx`, `votaciones_1999-2001_DeLaRua.xlsx` _+22_. Ojo: un output con nombre armado por f-string cae aca y esta vivo. Lo que hay que mirar de verdad son los pesados.

## Puntos de entrada

- `casos/nowcast_bicameral_html.py`
- `casos/nowcast_puertas_html.py`
- `casos/proyeccion_hipotetica_bicameral.py`
- `datos/argentinadatos/src/explorar_campos.py`
- `datos/argentinadatos/src/to_canonical.py`
- `datos/argentinadatos/tests/test_padron_senado.py`
- `datos/bot_recoleccion/src/dae_senado.py`
- `datos/bot_recoleccion/src/tp_diputados.py`
- `datos/bot_recoleccion/src/votaciones.py`
- `datos/canonica/src/build.py`

## Archivos centrales

Ordenados por cuantos otros archivos dependen de ellos. Tocar uno de arriba tiene mas radio de impacto.

| Archivo | LOC | Lo usan | Simbolos |
|---|---:|---:|---|
| `variables/bloque/src/bloque.py` | 633 | 17 | `_canon_linaje`, `_norm_nombre`, `_cargar_padron_linaje_senado`, `_enriquecer_linaje_senado` |
| `rutas.py` | 209 | 12 | `_env`, `inventario` |
| `definiciones.py` | 216 | 10 | `periodo_parlamentario`, `gobierno_por_fecha`, `era_de`, `normalizar_mayoria_valor` |
| `modelo/ensemble/src/ensemble.py` | 396 | 7 | `_cargar_simulador`, `_cargar_proyector`, `componer`, `_root` |
| `variables/embudo/src/embudo.py` | 730 | 6 | `cargar_icg`, `_mes_rezagado`, `cargar`, `cargar_sqlite` |
| `modelo/ensemble/src/nowcast_puertas.py` | 580 | 5 | `_bloque`, `era_de`, `alineacion_individual`, `perfil_legislador` |
| `evaluacion/baseline/src/baseline_voto_individual.py` | 469 | 5 | `_hallar_repo`, `_norm_cond`, `_ContadorAvisos`, `perfil` |
| `modelo/ensemble/src/puerta_d.py` | 236 | 5 | `camara_revisora`, `_padron_de`, `_clip01`, `_logit` |
| `modelo/agregador_institucional/src/agregador.py` | 418 | 4 | `umbral_aprobacion`, `_prob_conductas`, `simular_votacion`, `_linea_bloque_por_acta` |
| `datos/canonica/src/entity_resolution.py` | 319 | 4 | `_strip`, `_name_key`, `_leg_id`, `_aplicar_alias` |
| `variables/proyecto/src/origen_lider.py` | 405 | 3 | `_norm`, `_linaje_code`, `oficialista_por_fecha`, `clase_oficialismo` |
| `variables/proyecto/src/modulador_icg.py` | 255 | 3 | `_cargar_tramos`, `encoger_desvio`, `_gamma_tramo`, `gamma_fondo` |

## Flujo interno

- `variables/proyecto/tests/` → `variables/proyecto/src/` (10)
- `modelo/ensemble/tests/` → `modelo/ensemble/src/` (7)
- `modelo/ensemble/src/` → `variables/bloque/src/` (6)
- `datos/padron/tests/` → `datos/padron/src/` (5)
- `datos/proyectos/tests/` → `datos/proyectos/src/` (5)
- `datos/expedientes/src/` → `./` (4)
- `datos/expedientes/tests/` → `datos/expedientes/src/` (4)
- `modelo/ensemble/src/` → `evaluacion/baseline/src/` (4)
- `variables/bloque/tests/` → `variables/bloque/src/` (4)
- `casos/` → `modelo/ensemble/src/` (3)
- `datos/bot_recoleccion/tests/` → `datos/bot_recoleccion/src/` (3)
- `datos/canonica/tests/` → `datos/canonica/src/` (3)

## Se tocan juntos

Segun el historial de git. Si vas a cambiar uno, mira el otro.

- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` (34 commits)
- `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` + `Nowcast Congreso Argy/tablero_datos.js` (28 commits)
- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/tablero_datos.js` (26 commits)
- `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` + `Nowcast Congreso Argy/coordinacion/TABLERO.md` (22 commits)
- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/coordinacion/TABLERO.md` (20 commits)
- `Nowcast Congreso Argy/coordinacion/TABLERO.md` + `Nowcast Congreso Argy/tablero_datos.js` (16 commits)
- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/coordinacion/URGENTE.md` (9 commits)
- `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` + `Nowcast Congreso Argy/coordinacion/URGENTE.md` (9 commits)
- `Nowcast Congreso Argy/datos/padron/data/estado_vigilancia.json` + `Nowcast Congreso Argy/datos/padron/outputs/vigilancia_padron.md` (8 commits)
- `Nowcast Congreso Argy/coordinacion/URGENTE.md` + `Nowcast Congreso Argy/tablero_datos.js` (8 commits)

## Fuentes externas

- `senado.gob.ar` — `datos/bot_recoleccion/src/dae_senado.py`, `datos/expedientes/src/ingesta_od_senado.py`, `datos/seguimiento/src/giros.py`
- `datos.hcdn.gob.ar` — `datos/ckan_diputados/src/to_canonical.py`, `datos/expedientes/src/explorar_ckan.py`, `datos/expedientes/src/ingesta_ckan.py`
- `hcdn.gob.ar` — `datos/bot_recoleccion/src/explorar_tp.py`, `datos/bot_recoleccion/src/tp_diputados.py`, `datos/proyectos/tests/test_store.py`
- `www3.hcdn.gob.ar` — `coordinacion/ESTADO-DEL-PROYECTO.md`, `coordinacion/PROMPT-3-Formulacion-unica-y-nombres.md`, `coordinacion/TABLERO.md`
- `api.argentinadatos.com` — `datos/argentinadatos/README.md`, `datos/argentinadatos/src/explorar_campos.py`, `datos/argentinadatos/src/to_canonical.py`
- `hcdn.gov.ar` — `datos/proyectos/tests/test_store.py`, `datos/seguimiento/src/giros.py`
- `utdt.edu` — `variables/proyecto/README.md`, `variables/proyecto/src/ingesta_icg.py`
- `rest.hcdn.gob.ar` — `datos/bot_recoleccion/tests/fixtures/tp_87_144.html`
- `cloud.r-project.org` — `datos/decada_votada/export_seed.R`
- `proyectos2.senado.gov.ar` — `datos/senado/muestras/Senado_2002-03-05_muestra.html`
- `es.wikipedia.org` — `datos/senado/src/bajar_anexos_wiki.py`
- `votaciones.hcdn.gob.ar` — `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`

## Configuracion requerida

- `ANTHROPIC_API_KEY` — `variables/proyecto/src/agente_taxonomias.py`
- `ASIST` — `modelo/agregador_institucional/src/agregador.py`
- `BORRAR` — `datos/canonica/src/entity_resolution.py`
- `CACHE` — `datos/expedientes/src/ingesta_ckan.py`, `datos/senado/src/scrape_votaciones.py`
- `CAMARA` — `modelo/ensemble/validar_condicionamiento_votos.py`
- `CANON` — `datos/canonica/src/entity_resolution.py`, `datos/export/src/export_base.py`, `modelo/agregador_institucional/src/agregador.py`
- `CI` — `datos/padron/tests/test_vigilar_padron.py`
- `CLEAN` — `datos/canonica/src/build.py`, `variables/embudo/src/cohorte_dos_rutas.py`
- `CSV` — `datos/decada_votada/src/from_csv.py`
- `DISC` — `modelo/agregador_institucional/src/agregador.py`
- `DISCIPLINA` — `modelo/ensemble/src/ensemble.py`
- `EMBUDO_FUENTE` — `variables/embudo/src/embudo.py`
- `EXPEDIENTES` — `modelo/ensemble/src/ensemble.py`
- `EXPORT_CACHE` — `datos/export/src/export_base.py`
- `EXP_CLEAN` — `datos/expedientes/src/ingesta_od.py`, `variables/embudo/src/embudo.py`, `variables/proyecto/src/origen_lider.py`

## Frescura

- Bitacoras vencidas: `./`, `casos/`, `coordinacion/`, `datos/argentinadatos/`, `datos/bot_recoleccion/`, `datos/canonica/`, `datos/ckan_diputados/`, `datos/decada_votada/`, `datos/expedientes/`, `datos/export/`, `datos/manual_2026/`, `datos/padron/`, `datos/proyectos/`, `datos/seguimiento/`, `datos/senado/`, `datos/taxonomias/`, `docs/taxonomias/`, `evaluacion/baseline/`, `fase0/`, `modelo/agregador_institucional/`, `modelo/ensemble/`, `modelo/voto_individual/`, `variables/asistencia_quorum/`, `variables/bloque/`, `variables/embudo/`, `variables/legislador/`, `variables/proyecto/`
