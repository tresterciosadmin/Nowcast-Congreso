# MAPA — Nowcast Congreso Argy

<!-- GENERADO por indexar.py. No editar: los cambios se pierden. -->
<!-- La prosa vive en el README.md de cada modulo (seccion `Buscar aca si`). -->
<!-- 2026-09-06 13:25 UTC · 159 archivos · 38,195 LOC -->

## Como usar este archivo

Es el unico archivo del proyecto que hace falta leer para empezar. Para ubicar algo concreto: `python3 .mapa/buscar.py "<termino>"` devuelve archivo y linea sin abrir nada. Recien despues abrir los archivos que salgan, y solo esos.

Rama `main` — ultimo commit: 2026-09-05 8624839 bot: expedientes + votaciones 2026-09-05 [automatico] · **hay cambios sin commitear**

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
| votaciones 2020-2025 que faltan o llegan mal | `datos\argentinadatos/` |
| senadores sin bloque en esos anios (se resuelve con el padron del Senado) | `datos\argentinadatos/` |
| el modelo no ve los proyectos de las ultimas semanas, o hasta que fecha llega lo que el bot entrego | `datos\bot_recoleccion/` |
| el bot diario fallo, no commiteo, o abrio un issue | `datos\bot_recoleccion/` |
| scraping de Tramite Parlamentario (Diputados) o DAE (Senado) | `datos\bot_recoleccion/` |
| de donde sale un voto, un acta o un legislador (la tabla madre), y hasta que fecha llega | `datos\canonica/` |
| reconstruir la base de cero (`run_pipeline.py`, ~20 min con internet) | `datos\canonica/` |
| un legislador que aparece dos veces con nombres distintos (resolucion de entidades; el censo de duplicados esta en `outputs/`) | `datos\canonica/` |
| el hueco de Diputados 2020-23, o que fuente cubre que periodo | `datos\canonica/` |
| votaciones de Diputados 2011-2020 | `datos\ckan_diputados/` |
| el formato crudo de CKAN HCDN | `datos\ckan_diputados/` |
| de donde salen las votaciones anteriores a 2011 | `datos\decada_votada/` |
| por que hay codigo en R en un repo de Python | `datos\decada_votada/` |
| giros iniciales a comision, dictamenes, o si un expediente llego a ley | `datos\expedientes/` |
| el enlace acta -> expediente: la tabla es `acta_expediente_todas.parquet` (las DOS camaras, con `proyecto_id` resuelto); `acta_expediente.parquet` es el volcado crudo de CKAN y solo tiene Diputados | `datos\expedientes/` |
| el backfill de CKAN, o por que HCDN publica con ~5 semanas de atraso | `datos\expedientes/` |
| la ingesta trae menos/mas de lo esperado (`REFRESH=1`: por defecto usa CACHE) | `datos\expedientes/` |
| QUIEN firmo un dictamen, si hubo disidencias y de que bloque es cada firma | `datos\expedientes/` |
| como se arma la URL del PDF de una Orden del Dia de HCDN | `datos\expedientes/` |
| los dictamenes del Senado (otra fuente y otro scraper: `ingesta_od_senado.py`), y por que casi no tiene mayoria/minoria: es real, no es el parser (ADR-0017), su desacuerdo va como DISIDENCIA | `datos\expedientes/` |
| que significa `dictamen_clase = "desconocido"` (no se encontro el rotulo; NO es "despacho unico") | `datos\expedientes/` |
| comparar comisiones: SIEMPRE matchear contra el catalogo (los nombres tienen comas; partir por separadores rompe) | `datos\expedientes/` |
| `expedientes_giros` mezcla las DOS camaras: filtrar por camara antes de contar cobertura | `datos\expedientes/` |
| cuantas ODs faltan bajar (2.523 de ley identificadas, 1.722 parseadas) y como reanudar `ingesta_od.py` | `datos\expedientes/` |
| abrir las votaciones en Excel o consultarlas con SQL; la columna `periodo`, `gobierno` o `desvio` | `datos\export/` |
| que significa una votacion 'disputada' (margen +-5% de los emitidos) | `datos\export/` |
| el export salio sin desvio (falta correr antes `disciplina.py`) | `datos\export/` |
| votaciones de 2026 que no vinieron por API | `datos\manual_2026/` |
| el bloque del Senado en el periodo vigente | `datos\manual_2026/` |
| por que el distrito de este modulo sale del padron y no del Excel | `datos\manual_2026/` |
| cuantas bancas tiene un bloque a una fecha, o quien estaba en el recinto | `datos\padron/` |
| el cuerpo aparece inflado o desinflado; un anio da mas de 257 bancas (son duplicados de entity resolution) | `datos\padron/` |
| recambio del 10-dic, reemplazos, renuncias, bancas vacantes | `datos\padron/` |
| el padron cambio y hay que revisarlo (`vigilar_padron.py`, corre los lunes en CI; local escribe a `Archivos_Borrar/`) | `datos\padron/` |
| el padron HISTORICO (Senado: nomina oficial + Wikipedia; Diputados: reconstruido de la canonica, porque la nomina oficial solo cubre la foto vigente — 81 de 257 bancas en 2008) | `datos\padron/` |
| cuantos proyectos de ley hay, si uno existe, y sus autores, cofirmantes, giros o taxonomias | `datos\proyectos/` |
| la base de proyectos no cuadra / se cargo mal (`verificar.py`, 14 invariantes), o una fila rara que no hay que dejar entrar (cuarentena, base aparte) | `datos\proyectos/` |
| rehacer `proyectos.db` (no viaja a git: `migrar_ckan.py` + `upsert_bot.py`, ~1 min) | `datos\proyectos/` |
| el control de cohorte (`verificar.py`): la MIDE `variables/embudo` como proceso y aca se controla el resultado | `datos\proyectos/` |
| en que etapa esta un expediente concreto | `datos\seguimiento/` |
| giros a comision o movimientos de tramite de un proyecto | `datos\seguimiento/` |
| el PDF del texto de un proyecto | `datos\seguimiento/` |
| votaciones del Senado que faltan, o el hueco 2015-2023 | `datos\senado/` |
| que bloque tenia un senador en el momento de votar, y las filas REVISAR del padron manual | `datos\senado/` |
| scraping del Senado (cachea HTML; la primera corrida tarda ~20 min) | `datos\senado/` |
| que columnas y tipos tiene que tener un parquet de la canonica | `docs\schemas/` |
| cambiar un contrato de datos (requiere ADR + aviso en TABLERO) | `docs\schemas/` |
| que temas existen, como se llaman, y como se agrega, renombra o fusiona uno | `docs\taxonomias/` |
| el prompt con el que se clasifica un proyecto por titulo | `docs\taxonomias/` |
| un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta) | `docs\taxonomias/` |
| cuanto acierta la regla de bloque (~0,99 en direccion del voto individual) | `evaluacion\baseline/` |
| contra que se compara un modelo nuevo | `evaluacion\baseline/` |
| cuanto pierde el record individual en cada era, y cuanto lo arregla el guard | `evaluacion\baseline/` |
| de donde sale el 0,99 del baseline de bloque, y por que el proyecto NO apunta a predecir la direccion del voto individual | `fase0/` |
| el codigo original de ingesta, anterior a `datos/` | `fase0/` |
| si un proyecto junta los votos: quorum, mayoria simple/absoluta/dos tercios | `modelo\agregador_institucional/` |
| simular una votacion con un escenario de bloques dado | `modelo\agregador_institucional/` |
| por que sin condicionar por tema y origen todos los bloques quedan 'a favor' | `modelo\agregador_institucional/` |
| el quorum y las abstenciones: `presentes = afirm + neg` por defecto; el arreglo esta implementado detras de `QUORUM_ABSTENCIONES=1` y medido (hoy mueve 0,0000) | `modelo\agregador_institucional/` |
| por que la ausencia NO sale del desvio sino de `p_presente`, y por que el epsilon es un CLIP y no un modelo de riesgo sistemico | `modelo\agregador_institucional/` |
| el numero final de P(sancion) de un proyecto | `modelo\ensemble/` |
| el backtest de la cadena completa, Brier, skill o calibracion | `modelo\ensemble/` |
| la Puerta D / camara revisora en el circuito bicameral | `modelo\ensemble/` |
| P(mayoria) que da 0% o 100% (hay piso y techo por pedido de Valle) | `modelo\ensemble/` |
| REVISION 25-08: multiplicar P_B x P_D supone INDEPENDENCIA entre camaras y es falsa; y `P(B|A)` es notacion enganosa (A y C son un corrimiento en logit, no un condicional bayesiano) | `modelo\ensemble/` |
| el sobre tablas: 12,5% de las leyes se sancionan SIN dictamen y el modelo no lo contempla | `modelo\ensemble/` |
| diferencia entre la BANDA (p5-p95, agregada) y los PIVOTES (P individual en [0,35;0,65]) | `modelo\ensemble/` |
| quien se desvia de su bloque, discolos, bisagras o pivotes | `modelo\voto_individual/` |
| separar INDISCIPLINA de AUSENTISMO (son dos tasas distintas) | `modelo\voto_individual/` |
| el indice de disciplina por legislador y por periodo; presidentes de camara excluidos | `modelo\voto_individual/` |
| por que el desvio tiene piso (0,02) y no techo: ningun legislador llega a 1,0 (max observado 0,944) | `modelo\voto_individual/` |
| los paneles y el tablero ejecutivo que se abren con doble clic (estan en la RAIZ, no aca; se edita solo `tablero_datos.js`) | `producto\dashboard/` |
| de donde sale el numero: el mapa de la maquinaria (`MAPA-MODELO.html`), que script transforma que dato y que piezas estan parqueadas | `producto\dashboard/` |
| como se dibuja el circuito bicameral, y regenerar los datos de un panel sin tocar su HTML | `producto\dashboard/` |
| una definicion compartida (periodo parlamentario, tipo de mayoria, bancas por camara) cambio en un lado, o alguien volvio a pegarla adentro de un modulo en vez de usar `definiciones.py` | `tests/` |
| dos modulos tienen una copia de la misma funcion y hay que ver si siguen de acuerdo | `tests/` |
| un test falla y no pertenece a ningun modulo en particular | `tests/` |
| quien falta a las votaciones, presentismo por periodo | `variables\asistencia_quorum/` |
| quorum, o si una votacion se cae por ausencias | `variables\asistencia_quorum/` |
| OJO: alimentar el motor con presentismo PROMEDIO lo empeora — se usa la posicion del bloque entre PRESENTES | `variables\asistencia_quorum/` |
| que postura toma un bloque en un tema, cuan cohesionado esta, o si se parte (fractura, indice de Rice) | `variables\bloque/` |
| linajes de bloque (peronismo federal, progresismo) y como se agrupan | `variables\bloque/` |
| proyectar la alineacion de bloques a una fecha (point-in-time) | `variables\bloque/` |
| OJO: su columna `periodo` es un ANIO legislativo, no el periodo de dos anios del resto del repo | `variables\bloque/` |
| por que la mayoria de los proyectos nunca se votan; P(llega al recinto), cohorte, maduros vs. en curso | `variables\embudo/` |
| escenarios y contrafactuales (`escenarios.py`) — los coeficientes de la logistica NO son efectos | `variables\embudo/` |
| el skill del embudo o su backtest temporal | `variables\embudo/` |
| leer de `proyectos.db` vs. del parquet (`EMBUDO_FUENTE=parquet`), y medir la cohorte por las DOS rutas (`src/cohorte_dos_rutas.py`) | `variables\embudo/` |
| el historial completo de un diputado o senador, y por que bloques paso | `variables\legislador/` |
| presentismo o perfil de voto individual | `variables\legislador/` |
| armar el Mapa de Influencia o fichas para el producto | `variables\legislador/` |
| de que tema es un proyecto, quien lo impulsa (EJECUTIVO / OFICIALISMO / ALIADOS / OPOSICION) y cual es la postura del gobierno | `variables\proyecto/` |
| el ICG (indice de confianza en el gobierno) y el gamma que modula el desvio | `variables\proyecto/` |
| el efecto lider / jefe de bloque (1,25x, no el 7x que se creia) | `variables\proyecto/` |
| carpeta grande: 17 archivos — buscar por simbolo con `.mapa/buscar.py` antes de abrir | `variables\proyecto/` |
| REVISION 25-08: el log del ICG es SIMETRICO y la politica no — la asimetria existia en el mecanismo eliminado el 11-08 | `variables\proyecto/` |
| por que el promedio del gobierno no tiene leakage (`shift(1)` + `expanding`) | `variables\proyecto/` |

## Carpetas

| Carpeta | Que es | Arch. | LOC | Bitacora |
|---|---|---:|---:|---|
| `./` | La raiz del proyecto: los paneles que se abren con doble clic, el tablero ejecutivo y su unica fuente de datos (`tablero_datos.js`). | 6 | 5,843 | **vencida** |
| `variables\proyecto\src/` | _sin describir_ | 17 | 3,832 | — |
| `modelo\ensemble\src/` | _sin describir_ | 9 | 3,504 | — |
| `datos\expedientes\src/` | _sin describir_ | 11 | 3,261 | — |
| `datos\padron\src/` | _sin describir_ | 6 | 1,897 | — |
| `datos\proyectos\src/` | _sin describir_ | 7 | 1,609 | — |
| `modelo\ensemble\tests/` | _sin describir_ | 6 | 1,300 | — |
| `datos\expedientes\tests/` | _sin describir_ | 4 | 1,238 | — |
| `variables\proyecto\tests/` | _sin describir_ | 9 | 1,175 | — |
| `variables\embudo\src/` | _sin describir_ | 3 | 989 | — |
| `evaluacion\baseline\src/` | _sin describir_ | 4 | 972 | — |
| `casos/` | Aplicaciones del nowcast a un caso real (una ley concreta): el scoring, el informe en HTML y la proyeccion bicameral. Consumen los contratos de `modelo/` y `variables/`; no definen modelo propio. | 3 | 842 | **vencida** |
| `datos\senado\src/` | _sin describir_ | 4 | 832 | — |
| `datos\padron\tests/` | _sin describir_ | 5 | 748 | — |
| `datos\bot_recoleccion\src/` | _sin describir_ | 4 | 737 | — |
| `coordinacion/` | Las bitacoras y el protocolo: que bloquea a otros, que se hizo, quien tomo que modulo y por que se decidio cada cosa. Aca NO hay codigo del producto. | 8 | 680 | ok |
| `datos\canonica\src/` | _sin describir_ | 4 | 676 | — |
| `tests/` | Tests que cruzan modulos y por eso no pueden vivir dentro de ninguno. Cada modulo tiene sus propios tests en `<modulo>/tests/`; acá van solo los que verifican acuerdos ENTRE modulos. | 3 | 653 | **vencida** |
| `variables\bloque\src/` | _sin describir_ | 1 | 633 | — |
| `producto\dashboard\src/` | _sin describir_ | 1 | 563 | — |
| `variables\bloque\tests/` | _sin describir_ | 4 | 495 | — |
| `datos\proyectos\tests/` | _sin describir_ | 3 | 464 | — |
| `datos\seguimiento\src/` | _sin describir_ | 1 | 434 | — |
| `modelo\agregador_institucional\src/` | _sin describir_ | 1 | 418 | — |
| `modelo\voto_individual\src/` | _sin describir_ | 1 | 406 | — |
| `datos\canonica\tests/` | _sin describir_ | 3 | 314 | — |
| `datos\export\src/` | _sin describir_ | 1 | 298 | — |
| `fase0\src/` | _sin describir_ | 3 | 297 | — |
| `variables\legislador\src/` | _sin describir_ | 1 | 292 | — |
| `datos\argentinadatos\src/` | _sin describir_ | 2 | 290 | — |
| `variables\embudo\tests/` | _sin describir_ | 2 | 233 | — |
| `modelo\voto_individual\tests/` | _sin describir_ | 1 | 191 | — |
| `datos\manual_2026\src/` | _sin describir_ | 1 | 180 | — |
| `datos\argentinadatos\tests/` | _sin describir_ | 1 | 179 | — |
| `modelo\agregador_institucional\tests/` | _sin describir_ | 1 | 171 | — |
| `docs\taxonomias/` | La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, su cargador y el prompt del clasificador. Es un CATALOGO, no un modelo. | 3 | 160 | ok |
| `datos\manual_2026\tests/` | _sin describir_ | 1 | 151 | — |
| `evaluacion\baseline\tests/` | _sin describir_ | 1 | 146 | — |
| `datos\bot_recoleccion\tests/` | _sin describir_ | 3 | 143 | — |
| `modelo\ensemble/` | La composicion final: el nowcast end-to-end de un proyecto. Compone P(llega al recinto) x P(mayoria dado recinto) y corre el backtest de la cadena completa. | 1 | 129 | ok |
| `variables\bloque/` | Cohesion, tamano, postura y fracturas de cada bloque en el tiempo, y el proyector point-in-time que arma el escenario por bloque que consume el ensemble. | 1 | 110 | ok |
| `datos\senado\tests/` | _sin describir_ | 1 | 108 | — |
| `variables\asistencia_quorum\src/` | _sin describir_ | 1 | 102 | — |
| `variables\legislador\tests/` | _sin describir_ | 1 | 95 | — |
| `datos\decada_votada/` | Semilla historica de un solo uso: el dataset de Andy Tow ('La Decada Votada') exportado una vez y normalizado. No se depende de el en vivo (ADR-0002). | 1 | 94 | ok |
| `datos\export\tests/` | _sin describir_ | 1 | 88 | — |
| `datos\seguimiento\tests/` | _sin describir_ | 1 | 78 | — |
| `datos\decada_votada\src/` | _sin describir_ | 1 | 76 | — |
| `datos\ckan_diputados\src/` | _sin describir_ | 1 | 69 | — |
| `datos\argentinadatos/` | Ingesta de Diputados 2020-2025 y Senado 2024-2025 desde la API argentinadatos.com, normalizada al mismo esquema que CKAN. | 0 | 0 | ok |
| `datos\bot_recoleccion/` | El bot diario que trae lo nuevo de ambas camaras (proyectos con firmantes y giros, y votaciones) con upsert idempotente. Corre solo en GitHub Actions. | 0 | 0 | ok |
| `datos\canonica/` | La base propia y unica de votaciones nominales: todas las fuentes unificadas, deduplicadas y con entidades resueltas. Fuente de verdad de la que leen `variables/` y `modelo/`. | 0 | 0 | ok |
| `datos\ckan_diputados/` | Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle). | 0 | 0 | ok |
| `datos\expedientes/` | Registro de todo lo PRESENTADO (no solo lo votado): titulo, autor, tipo, fecha y cadena de vida del expediente. Denominador del embudo y enlace acta -> expediente. | 0 | 0 | ok |
| `datos\export/` | La canonica armonizada en formatos consultables: un SQLite unico para el programa y Excel por gobierno para humanos. Solo LEE la canonica. | 0 | 0 | ok |
| `datos\manual_2026/` | El Excel curado a mano por Franco (2025-2027) integrado al esquema canonico: aporta los VOTOS de 2026 de ambas camaras; el distrito lo resuelve el padron oficial y el bloque se reporta sin pisarse. | 0 | 0 | ok |
| `datos\padron/` | Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72). | 0 | 0 | ok |
| `datos\proyectos/` | Base de Proyectos de Ley (`proyectos.db`): una fila por proyecto identificado por denominador NNNN-X-AAAA. Fuente de verdad del universo de proyectos y denominador del embudo (ADR-0009). | 0 | 0 | ok |
| `datos\seguimiento/` | Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. Insumo del embudo. NO descubre proyectos nuevos. | 0 | 0 | ok |
| `datos\senado/` | Ingesta de votaciones nominales del Senado desde senado.gob.ar + reconstruccion del bloque historico contemporaneo a cada voto. Tapa el hueco 2015-2023. | 0 | 0 | ok |
| `docs\schemas/` | Los contratos de datos del repo (schema_version). Es lo unico compartido y fragil: cambiarlo exige un ADR. | 0 | 0 | ok |
| `evaluacion\backtesting/` | Validacion walk-forward (entrenar en t, validar en t+1) con test de no-leakage. PENDIENTE. | 0 | 0 | ok |
| `evaluacion\baseline/` | El piso a superar: el baseline de bloque, ya medido. Cualquier modelo nuevo se compara contra esto. | 0 | 0 | ok |
| `evaluacion\metricas/` | Metricas comunes: Brier, calibracion, accuracy en votos cruzados, cobertura de bandas. PENDIENTE. | 0 | 0 | ok |
| `fase0/` | La Fase 0, cerrada: medir cuanto acierta predecir el voto individual mirando al bloque. Resultado ~0,99, y ese resultado ordena todo el proyecto. Se conserva como registro; no se desarrolla mas. | 0 | 0 | ok |
| `modelo\agregador_institucional/` | Traduce posturas de bloque + asistencia en un resultado institucional: cuenta bancas, quorum, umbrales de mayoria y bandas. Mide la estructura, no la politica. | 0 | 0 | ok |
| `modelo\voto_individual/` | No predice el voto medio (eso lo resuelve la regla de bloque ~0,99): modela el DESVIO del legislador respecto de su bloque y detecta pivotes (ADR-0003). | 0 | 0 | ok |
| `producto\api/` | API de servicio (FastAPI) para la fase nube. FUTURO: no abrir sin pagador validado. | 0 | 0 | ok |
| `producto\dashboard/` | Tablero interno: radar de traccion, mapa de pivotes y escenarios, y el MAPA DEL MODELO: el diagrama de flujo BICAMERAL de como se calcula P(sancion) -dos bloques espejo, origen y revisora, con el condicionamiento entre camaras dibujado-, generado desde el indice del repo. Los entregables se abren con doble clic desde la RAIZ; el codigo del generador vive aca. | 0 | 0 | **vencida** |
| `variables\asistencia_quorum/` | Modelo de asistencia/ausencia/abstencion por legislador. Es donde vive la incertidumbre que el bloque no explica. | 0 | 0 | ok |
| `variables\contexto/` | Senal cualitativa de prensa y contexto politico (factor mu). FUTURO: no bloquea el MVP. | 0 | 0 | ok |
| `variables\embudo/` | Supervivencia del proyecto: presentado -> comision -> dictamen -> recinto -> sancion. Estima P(llega al recinto), la mitad de P(aprobacion). Es el diferencial del nowcast. | 0 | 0 | ok |
| `variables\legislador/` | Una ficha por legislador que voto alguna vez: identidad, camara, distrito, periodos, trayectoria de bloques, presentismo, perfil de voto y tasa de desvio. | 0 | 0 | ok |
| `variables\proyecto/` | Feature store por proyecto: tema/materia, origen (Ejecutivo/oficialismo/aliados/oposicion), jefe de bloque, mayoria requerida, texto, y el ICG como modulador de coyuntura. | 0 | 0 | ok |

## Puntos de entrada

- `casos\nowcast_bicameral_html.py`
- `casos\nowcast_puertas_html.py`
- `casos\proyeccion_hipotetica_bicameral.py`
- `datos\argentinadatos\src\explorar_campos.py`
- `datos\argentinadatos\src\to_canonical.py`
- `datos\argentinadatos\tests\test_padron_senado.py`
- `datos\bot_recoleccion\src\dae_senado.py`
- `datos\bot_recoleccion\src\tp_diputados.py`
- `datos\bot_recoleccion\src\votaciones.py`
- `datos\canonica\src\build.py`

## Archivos centrales

Ordenados por cuantos otros archivos dependen de ellos. Tocar uno de arriba tiene mas radio de impacto.

| Archivo | LOC | Lo usan | Simbolos |
|---|---:|---:|---|
| `variables\bloque\src\bloque.py` | 633 | 17 | `_canon_linaje`, `_norm_nombre`, `_cargar_padron_linaje_senado`, `_enriquecer_linaje_senado` |
| `rutas.py` | 209 | 12 | `_env`, `inventario` |
| `definiciones.py` | 216 | 10 | `periodo_parlamentario`, `gobierno_por_fecha`, `era_de`, `normalizar_mayoria_valor` |
| `modelo\ensemble\src\ensemble.py` | 396 | 7 | `_cargar_simulador`, `_cargar_proyector`, `componer`, `_root` |
| `variables\embudo\src\embudo.py` | 730 | 6 | `cargar_icg`, `_mes_rezagado`, `cargar`, `cargar_sqlite` |
| `modelo\ensemble\src\nowcast_puertas.py` | 580 | 5 | `_bloque`, `era_de`, `alineacion_individual`, `perfil_legislador` |
| `evaluacion\baseline\src\baseline_voto_individual.py` | 469 | 5 | `_hallar_repo`, `_norm_cond`, `_ContadorAvisos`, `perfil` |
| `modelo\ensemble\src\puerta_d.py` | 236 | 5 | `camara_revisora`, `_padron_de`, `_clip01`, `_logit` |
| `modelo\agregador_institucional\src\agregador.py` | 418 | 4 | `umbral_aprobacion`, `_prob_conductas`, `simular_votacion`, `_linea_bloque_por_acta` |
| `datos\canonica\src\entity_resolution.py` | 319 | 4 | `_strip`, `_name_key`, `_leg_id`, `_aplicar_alias` |
| `variables\proyecto\src\origen_lider.py` | 405 | 3 | `_norm`, `_linaje_code`, `oficialista_por_fecha`, `clase_oficialismo` |
| `variables\proyecto\src\modulador_icg.py` | 255 | 3 | `_cargar_tramos`, `encoger_desvio`, `_gamma_tramo`, `gamma_fondo` |

## Flujo interno

- `variables\proyecto\tests/` → `variables\proyecto\src/` (10)
- `modelo\ensemble\tests/` → `modelo\ensemble\src/` (7)
- `modelo\ensemble\src/` → `variables\bloque\src/` (6)
- `datos\padron\tests/` → `datos\padron\src/` (5)
- `datos\proyectos\tests/` → `datos\proyectos\src/` (5)
- `datos\expedientes\src/` → `./` (4)
- `datos\expedientes\tests/` → `datos\expedientes\src/` (4)
- `modelo\ensemble\src/` → `evaluacion\baseline\src/` (4)
- `variables\bloque\tests/` → `variables\bloque\src/` (4)
- `casos/` → `modelo\ensemble\src/` (3)
- `datos\bot_recoleccion\tests/` → `datos\bot_recoleccion\src/` (3)
- `datos\canonica\tests/` → `datos\canonica\src/` (3)

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
- `Nowcast Congreso Argy/coordinacion/URGENTE.md` + `Nowcast Congreso Argy/tablero_datos.js` (8 commits)
- `Nowcast Congreso Argy/datos/padron/data/estado_vigilancia.json` + `Nowcast Congreso Argy/datos/padron/outputs/vigilancia_padron.md` (7 commits)

## Fuentes externas

- `senado.gob.ar` — `datos\bot_recoleccion\src\dae_senado.py`, `datos\expedientes\src\ingesta_od_senado.py`, `datos\seguimiento\src\giros.py`
- `datos.hcdn.gob.ar` — `datos\ckan_diputados\src\to_canonical.py`, `datos\expedientes\src\explorar_ckan.py`, `datos\expedientes\src\ingesta_ckan.py`
- `hcdn.gob.ar` — `datos\bot_recoleccion\src\explorar_tp.py`, `datos\bot_recoleccion\src\tp_diputados.py`, `datos\proyectos\tests\test_store.py`
- `www3.hcdn.gob.ar` — `coordinacion\ESTADO-DEL-PROYECTO.md`, `coordinacion\PROMPT-3-Formulacion-unica-y-nombres.md`, `coordinacion\TABLERO.md`
- `api.argentinadatos.com` — `datos\argentinadatos\README.md`, `datos\argentinadatos\src\explorar_campos.py`, `datos\argentinadatos\src\to_canonical.py`
- `hcdn.gov.ar` — `datos\proyectos\tests\test_store.py`, `datos\seguimiento\src\giros.py`
- `utdt.edu` — `variables\proyecto\README.md`, `variables\proyecto\src\ingesta_icg.py`
- `rest.hcdn.gob.ar` — `datos\bot_recoleccion\tests\fixtures\tp_87_144.html`
- `cloud.r-project.org` — `datos\decada_votada\export_seed.R`
- `proyectos2.senado.gov.ar` — `datos\senado\muestras\Senado_2002-03-05_muestra.html`
- `es.wikipedia.org` — `datos\senado\src\bajar_anexos_wiki.py`
- `votaciones.hcdn.gob.ar` — `docs\contexto\Nowcast-Congreso_viabilidad_y_plan.md`

## Configuracion requerida

- `ANTHROPIC_API_KEY` — `variables\proyecto\src\agente_taxonomias.py`
- `ASIST` — `modelo\agregador_institucional\src\agregador.py`
- `BORRAR` — `datos\canonica\src\entity_resolution.py`
- `CACHE` — `datos\expedientes\src\ingesta_ckan.py`, `datos\senado\src\scrape_votaciones.py`
- `CAMARA` — `modelo\ensemble\validar_condicionamiento_votos.py`
- `CANON` — `datos\canonica\src\entity_resolution.py`, `datos\export\src\export_base.py`, `modelo\agregador_institucional\src\agregador.py`
- `CI` — `datos\padron\tests\test_vigilar_padron.py`
- `CLEAN` — `datos\canonica\src\build.py`, `variables\embudo\src\cohorte_dos_rutas.py`
- `CSV` — `datos\decada_votada\src\from_csv.py`
- `DISC` — `modelo\agregador_institucional\src\agregador.py`
- `DISCIPLINA` — `modelo\ensemble\src\ensemble.py`
- `EMBUDO_FUENTE` — `variables\embudo\src\embudo.py`
- `EXPEDIENTES` — `modelo\ensemble\src\ensemble.py`
- `EXPORT_CACHE` — `datos\export\src\export_base.py`
- `EXP_CLEAN` — `datos\expedientes\src\ingesta_od.py`, `variables\embudo\src\embudo.py`, `variables\proyecto\src\origen_lider.py`

## Frescura

- Bitacoras vencidas: `./`, `casos/`, `producto\dashboard/`, `tests/`
- Carpetas sin bitacora: `datos\argentinadatos\src/`, `datos\argentinadatos\tests/`, `datos\bot_recoleccion\src/`, `datos\bot_recoleccion\tests/`, `datos\canonica\src/`, `datos\canonica\tests/`, `datos\expedientes\src/`, `datos\expedientes\tests/`, `datos\export\src/`, `datos\export\tests/`, `datos\manual_2026\src/`, `datos\manual_2026\tests/`, `datos\padron\src/`, `datos\padron\tests/`, `datos\proyectos\src/`, `datos\proyectos\tests/`, `datos\seguimiento\src/`, `datos\senado\src/`, `datos\senado\tests/`, `evaluacion\baseline\src/`, `evaluacion\baseline\tests/`, `fase0\src/`, `modelo\agregador_institucional\src/`, `modelo\agregador_institucional\tests/`, `modelo\ensemble\src/`, `modelo\ensemble\tests/`, `modelo\voto_individual\src/`, `modelo\voto_individual\tests/`, `producto\dashboard\src/`, `variables\asistencia_quorum\src/`, `variables\bloque\src/`, `variables\bloque\tests/`, `variables\embudo\src/`, `variables\embudo\tests/`, `variables\legislador\src/`, `variables\legislador\tests/`, `variables\proyecto\src/`, `variables\proyecto\tests/`
