# MAPA — Nowcast Congreso Argy

<!-- GENERADO por indexar.py. No editar: los cambios se pierden. -->
<!-- La prosa vive en el README.md de cada modulo (seccion `Buscar aca si`). -->
<!-- 2026-10-05 19:35 UTC · 191 archivos · 44,288 LOC -->

## Como usar este archivo

Es el unico archivo del proyecto que hace falta leer para empezar. Para ubicar algo concreto: `python3 .mapa/buscar.py "<termino>"` devuelve archivo y linea sin abrir nada. Recien despues abrir los archivos que salgan, y solo esos.

Rama `main` — ultimo commit: 2026-10-05 3b7caf0 Merge branch 'main' of https://github.com/tresterciosadmin/Nowcast-Congreso

## Donde buscar que

| Si la consulta es sobre... | Ir a |
|---|---|
| por que ya no hay tableros ni paneles HTML, y donde se ve el numero del motor (`modelo/ensemble/outputs/panel_regresion.json`; `python modelo/ensemble/src/nowcast_puertas.py ...`) | `./` |
| el estado del proyecto y de la auditoria (`coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`, `coordinacion/QUE-SE-MIDE.md`) | `./` |
| por donde empezar a leer el repo | `./` |
| que significa "periodo parlamentario", que mayoria exige un proyecto o cuantas bancas tiene una camara (`definiciones.py`) | `./` |
| el informe de una ley concreta (Ganancias, lobby, ...) | `casos/` |
| proyectar un proyecto por las DOS camaras (origen + revisora): eso lo hace `modelo/ensemble/src/puerta_d.py`, no esta carpeta | `casos/` |
| por que un caso da un numero distinto al del ensemble | `casos/` |
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
| que se cae de una ley entre la votacion en general y la votacion en particular, articulo por articulo (`votacion_por_articulo.py`, B0/B1 del prompt multietiqueta): NO reemplaza `elegir_votacion`, agrega el resto de las actas que esa funcion descarta | `datos/expedientes/` |
| a que TITULO/CAPITULO pertenece un tramo votado (B2, 16-09): `titulo_num`/`capitulo_num` salen del propio titulo del acta, sin bajar PDF -- cobertura 9,8% (solo los omnibus complejos declaran capitulo) | `datos/expedientes/` |
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
| por que `proyecto_taxonomias` tiene pocas filas (16-09): la via PDF (`clasificar_lote`) solo alcanza al 0,06% de los proyectos (71/115.495 con `pdf_url`); la via barata por TITULO (`variables/proyecto/src/tema_por_proyecto.py::clasificar_por_titulo`) cubre el universo VOTADO (1.182 denominadores) -- ver ADR-0024 | `datos/proyectos/` |
| si corriste `migrar_ckan.py` y perdiste clasificaciones: NO se pierden, `main()` las restaura solo desde `taxonomias_backup.py` -- pero corré `exportar` despues de clasificar para que el respaldo este al dia | `datos/proyectos/` |
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
| nivel=proyecto en el registro sale vacio (ADR-0024): la fuente viva es `proyecto_taxonomias` en `datos/proyectos/data/proyectos.db`, hoy sin filas porque nadie corrio `agente_taxonomias.clasificar_lote` (necesita red + API key) | `datos/taxonomias/` |
| que columnas y tipos tiene que tener un parquet de la canonica | `docs/schemas/` |
| cambiar un contrato de datos (requiere ADR + aviso en TABLERO) | `docs/schemas/` |
| que temas existen, como se llaman, y como se agrega, renombra o fusiona uno | `docs/taxonomias/` |
| el prompt con el que se clasifica un proyecto: esta en `variables/proyecto/src/agente_taxonomias.py`, no aca | `docs/taxonomias/` |
| un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta) | `docs/taxonomias/` |
| el numero publicado del motor (skill del voto individual) y como se reproduce: `censo_detalle_paralelo.py` + `resumen_censo_limpio.py` | `evaluacion/baseline/` |
| la **metrica de verdad** (skill por era y camara con IC por ley de 2.000 replicas, DBrier pareado, procedencia y certificado de que el motor de hoy da esas P_i), con UN comando que no pisa ningun numero versionado: `src/metrica_de_verdad.py` -> `outputs/metrica_de_verdad.json` (`tests/test_metrica_de_verdad.py`; auditoria C1) | `evaluacion/baseline/` |
| la **calibracion declarada** de P(aprobacion) y de la banda, en mayoria simple y por camara (Brier contra una constante con IC pareado, AUC, recalibrado, cobertura de la banda al 90%), desde un JSON por acta que viaja por git, con UN comando que no pisa ningun numero versionado: `src/calibracion_declarada.py` -> `outputs/calibracion_declarada.json` (`--simular` regenera el JSON por acta con el motor de hoy, 6 min; `tests/test_calibracion_declarada.py`; auditoria C2) | `evaluacion/baseline/` |
| el **guard de era** sin cortar (brazo `era_desde` del harness, el motor no cambia) y su veredicto medido (primario: actas desde 2015-12-10; NO SE DISTINGUE): `src/medir_sin_corte_por_era.py` -> `outputs/guard_era_sin_corte.json` y `outputs/censo_estadisticos_sin_corte_era_2026-10-01.json` (el de C3, sobre el censo del 28-09) y `outputs/censo_estadisticos_sin_corte_era_2026-10-02.json` (re-corrido sobre el motor de D1.0: el insumo de D1) (`--censo` corre el censo del brazo, 14 min; `tests/test_guard_era_sin_corte.py`; auditoria C3) | `evaluacion/baseline/` |
| los **brazos del harness** (argumento `brazo` de `Contexto`/`correr`: k y ventana de la postura, origen por lado, `era_desde`; un valor o uno por año; default = el motor de hoy, que no se toca) y el **walk-forward de D1** (los siete hiperparámetros de P_i contra V0: selección anual, compuesto, IC por ley y por mes, Holm y el árbol del protocolo, desde una tabla por acta que viaja por git): `src/medir_d1_parametros_pi.py` (`--censo`, `--controles`, `--panel`, `--medir`; `tests/test_d1_parametros_pi.py`; auditoria D1) | `evaluacion/baseline/` |
| los estadisticos del censo que SI viajan por git (skill + IC por ley, tau, eps0) y como se regeneran: `censo_estadisticos.py` -> `outputs/censo_estadisticos_*.json` (el detalle voto a voto es un parquet ignorado; `tests/test_censo_estadisticos.py`) | `evaluacion/baseline/` |
| la regla del EXPEDIENTE: que cuenta como historia de un voto, y como se agrupan actas en leyes (`ley_por_acta`, `historia=estricta`) | `evaluacion/baseline/` |
| IC que re-muestrean leyes, no actas (`skill_ic_por_ley`, `dif_brier_ic_por_ley`) | `evaluacion/baseline/` |
| la fuga del harness viejo (shift(1) por fila) y cuanto pesaba: `medir_fuga_historia.py` (0,161 -> 0,092 -> 0,074) | `evaluacion/baseline/` |
| de donde salia el 11,06% de RECORD_POR_TEMA: `medir_record_por_tema_limpio.py` | `evaluacion/baseline/` |
| que el harness mide al motor y no una copia: `tests/test_harness_es_el_motor.py` (desde el 2026-10-02 también en la rama de bloque, con la ficha de desvío AL DÍA del motor: auditoría D1.0; el detalle del censo guarda sus componentes en las columnas `ficha_*`) | `evaluacion/baseline/` |
| el record por ORIGEN entre gobiernos (ADR-0033): **archivado en A7** (`coordinacion/archivo/A7-poda-2026-09/evaluacion/baseline/src/`); sus resultados siguen en `outputs/record_por_origen_*.json` | `evaluacion/baseline/` |
| las reglas de combinacion de temas de la POSTURA (ADR-0024/0028): `--combinar-temas`, experimento cerrado | `evaluacion/baseline/` |
| de donde sale el 0,99 del baseline de bloque, y por que el proyecto NO apunta a predecir la direccion del voto individual | `fase0/` |
| el codigo original de ingesta, anterior a `datos/` | `fase0/` |
| si un proyecto junta los votos: quorum, mayoria simple/absoluta/dos tercios | `modelo/agregador_institucional/` |
| simular una votacion con un escenario de bloques dado | `modelo/agregador_institucional/` |
| por que sin condicionar por tema y origen todos los bloques quedan 'a favor' | `modelo/agregador_institucional/` |
| el quorum y las abstenciones: `presentes = afirm + neg` por defecto; el arreglo esta implementado detras de `QUORUM_ABSTENCIONES=1` y medido (hoy mueve 0,0000) | `modelo/agregador_institucional/` |
| por que la ausencia NO sale del desvio sino de `p_presente`, y por que el epsilon es un CLIP y no un modelo de riesgo sistemico | `modelo/agregador_institucional/` |
| la alternativa al clip (ADR-0025, 16-09): `simular_votacion(..., epsilon0=.035, tau=1.19)` mueve la incertidumbre al LEGISLADOR (encogimiento afin + shock comun por simulacion). Apagado por defecto (`epsilon0=0, tau=0`), se prende con `INCERTIDUMBRE_LEGISLADOR=1` en `nowcast_puertas.py` | `modelo/agregador_institucional/` |
| el numero final de P(sancion) de un proyecto | `modelo/ensemble/` |
| por que un nowcast sale SIN numero (mayorias especiales apagadas, A5): `MAYORIAS_CON_NUMERO` en `nowcast_puertas.py` y `tests/test_mayorias_especiales_apagadas.py` | `modelo/ensemble/` |
| el backtest de la cadena completa, Brier, skill o calibracion (ARCHIVADO en A7; sus JSON siguen en `outputs/`) | `modelo/ensemble/` |
| la Puerta D / camara revisora en el circuito bicameral | `modelo/ensemble/` |
| P(mayoria) que da 0% o 100% (hay piso y techo por pedido de Valle) | `modelo/ensemble/` |
| REVISION 25-08: multiplicar P_B x P_D supone INDEPENDENCIA entre camaras y es falsa; y `P(B|A)` es notacion enganosa (A y C son un corrimiento en logit, no un condicional bayesiano) | `modelo/ensemble/` |
| la incertidumbre a nivel legislador que reemplaza al clip agregado (ADR-0025, 16-09): `INCERTIDUMBRE_LEGISLADOR=1` en `nowcast_puertas.py` -- implementado y medido, evidencia favorable, apagado por defecto a la espera de que Franco decida activarlo | `modelo/ensemble/` |
| el sobre tablas: 24,4% de los proyectos votados en recinto no tienen dictamen; `sobre_tablas.py` implementa el gate + la votación de dos tercios, pero θ SATURA en Diputados (predice 0,01 siempre) y atenuarlo por grilla (opción A) no lo arregla — el mecanismo no discrimina ni sin θ — APAGADA, no se recomienda prender | `modelo/ensemble/` |
| Diputados dejó de titular "sobre tablas" en 2020 y desde 2024 usa "HABILITACIÓN DEL TRATAMIENTO..." (mismo mecanismo, otro nombre) — matching corregido en `estimar_theta_sobre_tablas.py` | `modelo/ensemble/` |
| diferencia entre la BANDA (p5-p95, agregada) y los PIVOTES (P individual en [0,35;0,65]) | `modelo/ensemble/` |
| el dictamen POR LEGISLADOR (quién firmó, si firmó su jefe): `beta_dictamen.py`, PRENDIDA por defecto desde el 14-09 (`BETA_DICTAMEN=0` apaga; validada walk-forward) | `modelo/ensemble/` |
| qué parámetros tiene el motor, con qué default y cuáles mueven el número (auditoría B1): el registro generado desde el código `outputs/registro_parametros.json` (`src/registro_parametros.py`; `src/perturbar_panel.py` mide `afecta_panel`) y `tests/test_defaults_fijados.py`, que falla si un default cambia sin regenerarlo | `modelo/ensemble/` |
| quien se desvia de su bloque, discolos, bisagras o pivotes | `modelo/voto_individual/` |
| separar INDISCIPLINA de AUSENTISMO (son dos tasas distintas) | `modelo/voto_individual/` |
| el indice de disciplina por legislador y por periodo; presidentes de camara excluidos | `modelo/voto_individual/` |
| por que el desvio tiene piso (0,02) y no techo: ningun legislador llega a 1,0 (max observado 0,944) | `modelo/voto_individual/` |
| la ficha de desvío AL DÍA (point-in-time, auditoría 2026-09 D1.0): `disciplina.FichaAlDia` / `ficha_al_dia(fecha)`, la misma regla del CSV sólo con los votos anteriores a la fecha; es la que usa el motor (`ensemble.roster_nominal`) y el harness del censo. El CSV `disciplina_individual.csv` es la ficha de HOY (toda la historia) y ya no entra al número (`tests/test_ficha_al_dia.py`) | `modelo/voto_individual/` |
| el significado, escrito a mano, de cada script y de cada dato de la maquinaria del cálculo (`data/mapa_modelo_semantica.json`) | `producto/dashboard/` |
| por qué ya no hay paneles ni tablero HTML: `README.md` de la raíz («Los paneles HTML») y `coordinacion/QUE-SE-MIDE.md` | `producto/dashboard/` |
| cómo era el generador del mapa: `git log -- producto/dashboard/src/generar_mapa_modelo.py` | `producto/dashboard/` |
| una definicion compartida (periodo parlamentario, tipo de mayoria, bancas por camara) cambio en un lado, o alguien volvio a pegarla adentro de un modulo en vez de usar `definiciones.py` | `tests/` |
| dos modulos tienen una copia de la misma funcion y hay que ver si siguen de acuerdo | `tests/` |
| un test falla y no pertenece a ningun modulo en particular | `tests/` |
| un archivo que el motor lee dejo de viajar por git, o una ruta citada en un docstring quedo rota | `tests/` |
| quien falta a las votaciones, presentismo por periodo | `variables/asistencia_quorum/` |
| quorum, o si una votacion se cae por ausencias | `variables/asistencia_quorum/` |
| OJO: alimentar el motor con presentismo PROMEDIO lo empeora — se usa la posicion del bloque entre PRESENTES | `variables/asistencia_quorum/` |
| que postura toma un bloque en un tema, cuan cohesionado esta, o si se parte (fractura, indice de Rice) | `variables/bloque/` |
| linajes de bloque (peronismo federal, progresismo) y como se agrupan | `variables/bloque/` |
| proyectar la alineacion de bloques a una fecha (point-in-time) | `variables/bloque/` |
| OJO: su columna `periodo` es un ANIO legislativo, no el periodo de dos anios del resto del repo | `variables/bloque/` |
| un proyecto con VARIOS temas a la vez (ADR-0024, 15-09): `proyectar_postura(..., combinar_temas="union"|"ponderada", temas=[...])` — default `"primaria"` (una sola etiqueta, de siempre), retrocompatible | `variables/bloque/` |
| por que la mayoria de los proyectos nunca se votan; P(llega al recinto), cohorte, maduros vs. en curso | `variables/embudo/` |
| escenarios y contrafactuales (`escenarios.py`) — los coeficientes de la logistica NO son efectos | `variables/embudo/` |
| el skill del embudo o su backtest temporal | `variables/embudo/` |
| leer de `proyectos.db` vs. del parquet (`EMBUDO_FUENTE=parquet`), y medir la cohorte por las DOS rutas (`src/cohorte_dos_rutas.py`) | `variables/embudo/` |
| el historial completo de un diputado o senador, y por que bloques paso | `variables/legislador/` |
| presentismo o perfil de voto individual | `variables/legislador/` |
| armar el Mapa de Influencia o fichas para el producto | `variables/legislador/` |
| de que tema es un proyecto y quien lo impulsa (EJECUTIVO / OFICIALISMO / ALIADOS / OPOSICION) | `variables/proyecto/` |
| el ICG (indice de confianza en el gobierno) y el gamma que modula el desvio | `variables/proyecto/` |
| el efecto lider / jefe de bloque (1,25x, no el 7x que se creia) | `variables/proyecto/` |
| carpeta grande: 13 archivos en `src/` — buscar por simbolo con `.mapa/buscar.py` antes de abrir | `variables/proyecto/` |
| REVISION 25-08: el log del ICG es SIMETRICO y la politica no — la asimetria existia en el mecanismo eliminado el 11-08 | `variables/proyecto/` |
| por que el promedio del gobierno no tiene leakage (`shift(1)` + `expanding`) | `variables/proyecto/` |
| el tema de un proyecto REAL (no de un acta ya votada), para que el motor lo use solo (`tema_por_proyecto.py`, ADR-0024): lee `proyecto_taxonomias`, hoy vacia porque nadie corrio `agente_taxonomias.clasificar_lote` (necesita red + API key) | `variables/proyecto/` |

## Carpetas

| Carpeta | Que es | Arch. | LOC | Bitacora |
|---|---|---:|---:|---|
| `evaluacion/baseline/` _(src+tests)_ | El censo del motor sobre el voto individual. Desde el 28-09 (ADR-0034) el harness NO reimplementa nada del legislador: importa `record_legisladores`, `proyectar_postura` y `perfil_legislador` del motor y solo decide que votos existian (historia estricta: fecha anterior y OTRA ley). Un test lo compara contra `nowcast()` legislador por legislador. El baseline de BLOQUE -el ~0,99- se midio en `fase0/` y ahi quedo. | 25 | 7,849 | **vencida** |
| `modelo/ensemble/` _(src+tests)_ | La composicion final: el nowcast end-to-end de un proyecto. El punto de entrada vivo es `nowcast_puertas.py`, que corre la CADENA DE PUERTAS y devuelve un numero condicional a que las camaras voten. La formulacion v1 -P(llega al recinto) x P(mayoria dado recinto)- se dio de BAJA el 2026-08-22 (ADR-0012), junto con su backtest: los stubs de la v1 (`ensemble.componer` y compania) y `backtest_cadena.py` se eliminaron/archivaron en la auditoria 2026-09 (A7: su codigo esta en `coordinacion/archivo/A7-poda-2026-09/`). Desde el 2026-09-30 (auditoria A5) `nowcast()` da numero SOLO para mayoria simple: con una mayoria especial devuelve `p_aprobacion = None` y `motivo_sin_numero`, sin simular. | 30 | 7,691 | **vencida** |
| `variables/proyecto/` _(src+tests)_ | Feature store por proyecto: tema/materia, origen (Ejecutivo/oficialismo/aliados/oposicion), jefe de bloque, mayoria requerida, texto, y el ICG como modulador de coyuntura. La postura del gobierno por acta se midio aca y su modulo se archivo el 2026-09-10 sin consumidor: la medicion quedo en el ADR-0021 y en ESTADO. | 23 | 5,160 | **vencida** |
| `datos/expedientes/` _(src+tests)_ | Registro de todo lo PRESENTADO (no solo lo votado): titulo, autor, tipo, fecha y cadena de vida del expediente. Denominador del embudo y enlace acta -> expediente. | 17 | 4,922 | **vencida** |
| `datos/padron/` _(src+tests)_ | Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72). | 11 | 2,645 | ok |
| `datos/proyectos/` _(src+tests)_ | Base de Proyectos de Ley (`proyectos.db`): una fila por proyecto identificado por denominador NNNN-X-AAAA. Fuente de verdad del universo de proyectos y denominador del embudo (ADR-0009). | 10 | 2,073 | ok |
| `variables/bloque/` _(src+tests)_ | Cohesion, tamano, postura y fracturas de cada bloque en el tiempo, y el proyector point-in-time que arma el escenario por bloque que consume el ensemble. | 6 | 1,588 | **vencida** |
| `tests/` | Tests que no pertenecen a ningun modulo: los que verifican acuerdos ENTRE modulos (definiciones y rutas compartidas) y los que vigilan INVARIANTES del repo — que las bases y los insumos del motor viajen por git, que la regla del caracter del dictamen no se reimplemente, y que las rutas que el codigo nombra en sus docstrings existan. Cada modulo tiene sus propios tests en `<modulo>/tests/`. | 9 | 1,581 | **vencida** |
| `variables/embudo/` _(src+tests)_ | Supervivencia del proyecto: presentado -> comision -> dictamen -> recinto -> sancion. Estima P(llega al recinto). OJO: eso era 'la mitad de P(aprobacion)' en la formulacion v1, que se dio de baja el 2026-08-22 (ADR-0012) justamente porque medir la mortandad en el cajon es agenda politica y se decidio no modelarla; hoy el numero publicado NO la multiplica. | 5 | 1,222 | ok |
| `datos/canonica/` _(src+tests)_ | La base propia y unica de votaciones nominales: todas las fuentes unificadas, deduplicadas y con entidades resueltas. Fuente de verdad de la que leen `variables/` y `modelo/`. | 7 | 1,032 | **vencida** |
| `datos/senado/` _(src+tests)_ | Ingesta de votaciones nominales del Senado desde senado.gob.ar + reconstruccion del bloque historico contemporaneo a cada voto. Tapa el hueco 2015-2023. | 5 | 940 | ok |
| `modelo/voto_individual/` _(src+tests)_ | No predice el voto medio (eso lo resuelve la regla de bloque ~0,99): modela el DESVIO del legislador respecto de su bloque y detecta pivotes (ADR-0003). | 3 | 910 | **vencida** |
| `datos/bot_recoleccion/` _(src+tests)_ | El bot diario que trae lo nuevo de ambas camaras (proyectos con firmantes y giros, y votaciones) con upsert idempotente. Corre solo en GitHub Actions. | 7 | 880 | ok |
| `./` | La raiz del proyecto: `CLAUDE.md`, `rutas.py`, `definiciones.py`, los scripts de regeneracion (`REGENERAR.ps1`, `verificar_*.py`) y este README. Los paneles HTML (tablero ejecutivo, mapa del modelo, panel de puertas) y sus `*_datos.js` se eliminaron en la auditoria 2026-09 (ítem A6): el estado vive en `coordinacion/`. | 4 | 827 | **vencida** |
| `coordinacion/` _(AUDITORIA-2026-09)_ | Las bitacoras y el protocolo: que bloquea a otros, que se hizo, quien tomo que modulo y por que se decidio cada cosa. Aca NO hay codigo del producto. | 5 | 815 | **vencida** |
| `modelo/agregador_institucional/` _(src+tests)_ | Traduce posturas de bloque + asistencia en un resultado institucional: cuenta bancas, quorum, umbrales de mayoria y bandas. Mide la estructura, no la politica. | 2 | 757 | **vencida** |
| `datos/seguimiento/` _(src+tests)_ | Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. Insumo del embudo. NO descubre proyectos nuevos. | 2 | 512 | ok |
| `datos/taxonomias/` _(src+tests)_ | El registro unico de taxonomias asignadas: una fila por (objeto, taxonomia), en CSV versionado, consolidado desde todas las fuentes que existian sueltas. | 2 | 501 | **vencida** |
| `datos/argentinadatos/` _(src+tests)_ | Ingesta de Diputados desde 2020 y Senado desde 2024 (hasta hoy: la API sirve tambien 2026) desde argentinadatos.com, normalizada al mismo esquema que CKAN. OJO: la API NO publica el expediente -- medido el 09-09, URGENTE P. | 3 | 496 | ok |
| `variables/legislador/` _(src+tests)_ | Una ficha por legislador que voto alguna vez: identidad, camara, distrito, periodos, trayectoria de bloques, presentismo, perfil de voto y tasa de desvio. | 2 | 387 | ok |
| `datos/export/` _(src+tests)_ | La canonica armonizada en formatos consultables: un SQLite unico para el programa y Excel por gobierno para humanos. Solo LEE la canonica. | 2 | 386 | ok |
| `datos/manual_2026/` _(src+tests)_ | El Excel curado a mano por Franco (2025-2027). FUERA DEL PIPELINE desde el 06-09: sus 17 actas eran las mismas votaciones que ya trae argentinadatos, con fecha y expediente. | 2 | 331 | ok |
| `fase0/` _(src)_ | La Fase 0, cerrada: medir cuanto acierta predecir el voto individual mirando al bloque. Resultado ~0,99, y ese resultado ordena todo el proyecto. Se conserva como registro; no se desarrolla mas. | 3 | 297 | ok |
| `datos/decada_votada/` _(src)_ | Semilla historica de un solo uso: el dataset de Andy Tow ('La Decada Votada') exportado una vez y normalizado. No se depende de el en vivo (ADR-0002). | 2 | 170 | ok |
| `docs/taxonomias/` | La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, y su cargador. Es un CATALOGO, no un modelo. El PROMPT del clasificador NO vive aca: es `SYSTEM_PROMPT` en `variables/proyecto/src/agente_taxonomias.py`, y es el unico lugar donde se toca. | 2 | 138 | ok |
| `variables/asistencia_quorum/` _(src)_ | Modelo de asistencia/ausencia/abstencion por legislador. Es donde vive la incertidumbre que el bloque no explica. | 1 | 109 | ok |
| `datos/ckan_diputados/` _(src)_ | Ingesta de votaciones nominales de Diputados 2011-2020 desde CKAN HCDN (cabecera + detalle). | 1 | 69 | ok |
| `casos/` | Casos reales del nowcast (una ley concreta), escritos a mano: hoy, el caso testigo de la ley de lobby con su scoring. Consume los contratos de `modelo/` y `variables/`; no define modelo propio. **Ya no hay generadores:** el último, `nowcast_puertas_html.py` (el panel de puertas en HTML), se eliminó en la auditoría 2026-09 (A6); los otros dos —bicameral y proyección hipotética— estaban neutralizados desde agosto y se archivaron el 2026-09-10. | 0 | 0 | **vencida** |
| `docs/schemas/` | Los contratos de datos del repo (schema_version). Es lo unico compartido y fragil: cambiarlo exige un ADR. | 0 | 0 | ok |
| `evaluacion/backtesting/` | Validacion walk-forward (entrenar en t, validar en t+1) con test de no-leakage. PENDIENTE. | 0 | 0 | ok |
| `evaluacion/metricas/` | Metricas comunes: Brier, calibracion, accuracy en votos cruzados, cobertura de bandas. PENDIENTE. | 0 | 0 | ok |
| `producto/api/` | API de servicio (FastAPI) para la fase nube. FUTURO: no abrir sin pagador validado. | 0 | 0 | ok |
| `producto/dashboard/` | Módulo sin código: conserva `data/mapa_modelo_semantica.json`, la capa CURADA del mapa del modelo (qué calcula cada script en castellano, qué significa cada parquet, qué puertas están parqueadas y por qué). Su generador y los tres paneles HTML se eliminaron en la auditoría 2026-09. | 0 | 0 | **vencida** |
| `variables/contexto/` | Senal cualitativa de prensa y contexto politico (factor mu). FUTURO: no bloquea el MVP. | 0 | 0 | ok |

## Inventario de datos

225 archivos de datos · 622.9 MB · 225 viajan por git, **0 no**.

Buscar uno sin abrir nada: `python .mapa/buscar.py --dato <termino>`. Columna **git**: `si` = esta versionado, o sea que quien clone lo tiene; `NO` = vive solo en el disco de quien lo genero, que es el modo de falla mas repetido de este repo (seis veces, ver `.gitignore`). **Escribe/Lee**: quien lo produce y quien lo consume, deducido del codigo; sin lector, sobra — sin escritor, no se regenera.

| Archivo | Forma | Peso | git | Escribe | Lee |
|---|---|---:|:---:|---|---|
| `casos/2026-07-31_ley-de-lobby_scoring.json` | objeto: scoring, observado | 2 KB | si | — | — |
| `coordinacion/AUDITORIA-2026-09/resultados/invariancia_al_futuro.json` | objeto: resumen, detalle | 77 KB | si | — | _(1 lo nombran)_ |
| `coordinacion/AUDITORIA-2026-09/resultados/control_independiente.json` | objeto: independiente_por_AST, n_evaluad | 27 KB | si | — | _(2 lo nombran)_ |
| `coordinacion/AUDITORIA-2026-09/resultados/cobertura_canonica.json` | 51 filas | 18 KB | si | `cobertura_canonica.py` | — |
| `coordinacion/AUDITORIA-2026-09/resultados/verificar_bots.json` | objeto: punto_de_partida, head, eliminad | 12 KB | si | `verificar_bots.py` | — |
| `coordinacion/AUDITORIA-2026-09/resultados/contraste_aprobacion.json` | objeto: detalle, n_sims, n_actas_simulad | 7 KB | si | — | _(1 lo nombran)_ |
| `coordinacion/AUDITORIA-2026-09/resultados/ficha_al_dia_D1_0.json` | objeto: censo_nuevo, censo_viejo, pares_ | 4 KB | si | — | _(1 lo nombran)_ |
| `datos/bot_recoleccion/data/clean/tp_entradas.parquet` _BOT_TP_ENTRADAS_ | 3,970×11 | 531 KB | si | `tp_diputados.py` | `giros_iniciales.py`, `upsert_bot.py`, `verificar.py` |
| `datos/bot_recoleccion/data/clean/dae_entradas.parquet` | 1,133×8 | 132 KB | si | `dae_senado.py`, `test_verificar.py` | `upsert_bot.py`, `verificar.py` |
| `datos/bot_recoleccion/data/clean/votaciones_nuevas.parquet` | 587×11 | 38 KB | si | `votaciones.py` | _(1 lo nombran)_ |
| `datos/bot_recoleccion/data/estado_bot.json` | objeto: dae_normal, tp_diputados, actas_ | 21 KB | si | `dae_senado.py`, `tp_diputados.py` | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/votaciones-diputados.csv` | 383,744×4 | 4.9 MB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/votos_resuelto.parquet` _CANONICA_VOTOS_RESUELTO_ | 959,815×12 | 2.1 MB | si | `entity_resolution.py`, `test_ficha_al_dia.py` | `cobertura_canonica.py`, `export_base.py`, `padron_diputados_historico.py` +7 |
| `datos/canonica/data/clean/_decada_csv/votaciones-senado.csv` | 144,792×4 | 1.8 MB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/votos_canonico.parquet` _CANONICA_VOTOS_ | 959,815×8 | 1.2 MB | si | `build.py`, `entity_resolution.py` | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/asuntos-senado.csv` | 2,011×19 | 1.0 MB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/asuntos-diputados.csv` | 1,499×18 | 651 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/argentinadatos_votos.parquet` | 349,690×8 | 489 KB | si | `to_canonical.py` | — |
| `datos/canonica/data/clean/actas_canonico.parquet` _CANONICA_ACTAS_ | 5,998×14 | 479 KB | si | `build.py`, `test_control_independiente.py` | `cobertura_canonica.py`, `contraste_aprobacion.py`, `entity_resolution.py` +13 |
| `datos/canonica/data/clean/_sources/decada_votada_actas.parquet` | 3,153×14 | 309 KB | si | — | — |
| `datos/canonica/data/clean/_sources/decada_votada_votos.parquet` | 437,144×8 | 258 KB | si | — | — |
| `datos/canonica/data/clean/_sources/ckan_diputados_votos.parquet` | 256,581×8 | 251 KB | si | `to_canonical.py` | — |
| `datos/canonica/outputs/actas_gemelas_2026-09-06.csv` | 1,076×8 | 158 KB | si | — | — |
| `datos/canonica/data/clean/_sources/argentinadatos_actas.parquet` | 1,649×14 | 93 KB | si | `to_canonical.py` | — |
| `datos/canonica/data/clean/_sources/senado_actas.parquet` | 749×14 | 70 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/ckan_diputados_actas.parquet` | 999×14 | 43 KB | si | `to_canonical.py` | — |
| `datos/canonica/outputs/legislador_id_duplicados_2026-09-04.csv` | 153×22 | 43 KB | si | — | — |
| `datos/canonica/data/clean/_decada_csv/diputados.csv` | 1,037×3 | 40 KB | si | `padron_diputados_historico.py`, `test_ingesta_padron.py` | `to_canonical.py`, `comparar_vias_icg.py` |
| `datos/canonica/data/clean/_sources/senado_votos.parquet` | 53,910×8 | 39 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/outputs/legislador_id_merge_aprobado_2026-09-04.csv` | 114×11 | 22 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/manual_2026_votos.parquet` | 3,072×8 | 18 KB | si | `to_canonical.py` | _(1 lo nombran)_ |
| `datos/canonica/data/alias_legislador_id.csv` | 184×1 | 16 KB | si | — | `alias_legislador.py` |
| `datos/canonica/data/clean/_sources/manual_2026_actas.parquet` | 17×14 | 9 KB | si | `to_canonical.py` | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/senadores.csv` | 176×3 | 7 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_decada_csv/bloques-diputados.csv` | 183×3 | 5 KB | si | — | _(1 lo nombran)_ |
| `datos/canonica/data/clean/_sources/baseline_canonico.json` | objeto: n_votos_sustantivos, por_nivel,  | 2 KB | si | — | — |
| `datos/canonica/data/clean/_decada_csv/bloques-senado.csv` | 52×3 | 1 KB | si | — | _(1 lo nombran)_ |
| `datos/decada_votada/data/clean/decada_votada_votos.parquet` | 6,425×8 | 23 KB | si | `export_seed.R`, `from_csv.py` | — |
| `datos/decada_votada/data/clean/decada_votada_actas.parquet` | 25×14 | 8 KB | si | `export_seed.R`, `from_csv.py` | — |
| `datos/expedientes/data/clean/expedientes.parquet` | 114,365×9 | 10.6 MB | si | `enlace_senado.py`, `ingesta_ckan.py` | `actas_ley.py`, `construir_firmas.py`, `giros_iniciales.py` +7 |
| `datos/expedientes/data/clean/expedientes_giros.parquet` | 425,411×3 | 2.1 MB | si | `ingesta_ckan.py`, `migrar_ckan.py` | `giros_iniciales.py`, `upsert_bot.py`, `verificar.py` +1 |
| `datos/expedientes/data/clean/expedientes_movimientos.parquet` | 143,677×4 | 1.7 MB | si | `ingesta_ckan.py`, `migrar_ckan.py` | `giros_iniciales.py`, `verificar.py` |
| `datos/expedientes/data/clean/expedientes_resultados.parquet` _EXPEDIENTES_RESULTADOS_ | 118,623×7 | 953 KB | si | `enlace_senado.py`, `ingesta_ckan.py` | `ingesta_od.py`, `origen_por_acta.py` |
| `datos/expedientes/data/clean/dictamenes_firmas.parquet` _EXPEDIENTES_FIRMAS_ | 125,561×28 | 921 KB | si | `construir_firmas.py` | `verificar_regeneracion.py` |
| `datos/expedientes/data/clean/acta_expediente_todas.parquet` _EXPEDIENTES_ACTA_EXP_TODAS_ | 5,043×13 | 424 KB | si | `enlace_senado.py`, `votacion_por_articulo.py` | `actas_ley.py`, `tema_por_proyecto.py`, `verificar_regeneracion.py` |
| `datos/expedientes/data/clean/expedientes_dictamenes.parquet` | 24,053×8 | 373 KB | si | `ingesta_ckan.py`, `migrar_ckan.py` | _(1 lo nombran)_ |
| `datos/expedientes/data/clean/dictamenes_firmas_senado.parquet` _EXPEDIENTES_FIRMAS_SENADO_ | 18,256×30 | 208 KB | si | `construir_firmas.py` | _(4 lo nombran)_ |
| `datos/expedientes/data/clean/votacion_por_articulo.parquet` | 2,361×13 | 168 KB | si | `votacion_por_articulo.py` | — |
| `datos/expedientes/data/clean/acta_expediente.parquet` _EXPEDIENTES_ACTA_EXP_ | 1,849×7 | 164 KB | si | `enlace_senado.py`, `ingesta_ckan.py` | `baseline_voto_individual.py`, `estimar_beta_dictamen.py`, `origen_por_acta.py` |
| `datos/expedientes/data/clean/cadena_camaras.parquet` | 1,182×17 | 151 KB | si | `enlace_senado.py` | `estimar_psi_arrastre.py` |
| `datos/expedientes/data/clean/dictamenes_comisiones.parquet` _EXPEDIENTES_DICTAMENES_COMISIONES_ | 10,031×8 | 88 KB | si | `construir_firmas.py` | — |
| `datos/expedientes/data/clean/expedientes_leyes.parquet` | 1,347×7 | 38 KB | si | — | `origen_lider.py` |
| `datos/expedientes/data/clean/giros_iniciales.parquet` | 4,070×4 | 31 KB | si | `giros_iniciales.py` | `embudo.py` |
| `datos/expedientes/data/clean/capitulos_nombre.parquet` | 546×5 | 15 KB | si | — | — |
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
| `datos/manual_2026/Congreso_25-27.xlsx` _MANUAL_2026_XLSX_ | 4 hoja(s) | 52 KB | si | — | _(2 lo nombran)_ |
| `datos/padron/data/padron_diputados_historico.csv` _PADRON_DIPUTADOS_HISTORICO_ | 6,124×12 | 1.6 MB | si | `padron_diputados_historico.py` | `resolver_firmantes.py` |
| `datos/padron/data/padron_diputados.csv` _PADRON_DIPUTADOS_ | 1,454×12 | 260 KB | si | `test_ingesta_padron.py`, `test_ensemble.py` | `resolver_firmantes.py`, `to_canonical.py`, `comparar_vias_icg.py` |
| `datos/padron/data/nomina_diputados.csv` | 1,454×6 | 103 KB | si | `test_ingesta_padron.py` | _(3 lo nombran)_ |
| `datos/padron/data/padron_senado_historico.csv` _PADRON_SENADO_HISTORICO_ | 243×12 | 45 KB | si | `test_guardas_confianza.py`, `test_puerta_d.py` | `resolver_firmantes.py` |
| `datos/padron/data/raw/nomina_senado.csv` | 72×15 | 16 KB | si | — | _(3 lo nombran)_ |
| `datos/padron/data/padron_senado.csv` _PADRON_SENADO_ | 72×12 | 13 KB | si | `test_bloque_linaje_senado.py` | `to_canonical.py`, `test_padron_senado.py`, `resolver_firmantes.py` +2 |
| `datos/padron/data/gobernadores.csv` | 96×10 | 13 KB | si | — | — |
| `datos/padron/data/senado_linaje_manual.csv` _PADRON_SENADO_LINAJE_MANUAL_ | 25×7 | 2 KB | si | `test_bloque_linaje_senado.py` | `padron_senado_historico.py`, `bloque.py` |
| `datos/padron/data/estado_vigilancia.json` | objeto: diputados, senado | 445 B | si | — | _(2 lo nombran)_ |
| `datos/proyectos/data/proyectos.db` _PROYECTOS_DB_ | 610,403×6 | 87.3 MB | si | `schema.sql`, `store.py` | `verificar.py`, `test_store.py`, `tema_por_proyecto.py` |
| `datos/proyectos/data/taxonomias.csv` | 3,339×6 | 327 KB | si | `taxonomias_backup.py` | `test_store.py` |
| `datos/proyectos/data/cuarentena.db` _PROYECTOS_CUARENTENA_DB_ | 0×1 | 20 KB | si | — | `cuarentena.py` |
| `datos/senado/data/clean/senado_actas.parquet` | 749×14 | 70 KB | si | `scrape_votaciones.py` | `aplicar_bloques.py`, `padron_bloques.py` |
| `datos/senado/data/padron_bloques_senado.csv` _SENADO_PADRON_BLOQUES_ | 291×8 | 39 KB | si | `padron_bloques.py` | `to_canonical.py`, `padron_senado_historico.py`, `aplicar_bloques.py` |
| `datos/senado/data/clean/senado_votos.parquet` | 53,910×8 | 39 KB | si | `aplicar_bloques.py`, `scrape_votaciones.py` | `padron_bloques.py` |
| `datos/senado/data/padron_manual_2015_2017.csv` | 131×8 | 23 KB | si | `padron_bloques.py` | `to_canonical.py`, `aplicar_bloques.py` |
| `datos/senado/data/_diag_sin_cobertura.csv` | 7×3 | 266 B | si | `aplicar_bloques.py` | — |
| `datos/taxonomias/data/asignaciones.csv` | 10,111×8 | 842 KB | si | `registro.py` | _(2 lo nombran)_ |
| `docs/schemas/acta.schema.json` | objeto: $schema, $id, title, description | 2 KB | si | `build.py` | — |
| `docs/schemas/voto.schema.json` | objeto: $schema, $id, title, description | 1 KB | si | `build.py` | — |
| `docs/taxonomias/taxonomias.json` | objeto: schema_version, actualizado, not | 7 KB | si | — | `registro.py`, `loader.py` |
| `evaluacion/baseline/outputs/record_por_origen_fase2_detalle_harness_2026-09-27.parquet` | 691,893×21 | 53.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_2026-10-03.parquet` | 692,715×47 | 41.4 MB | si | — | `test_control_independiente.py` |
| `evaluacion/baseline/outputs/censo_detalle_2026-10-02.parquet` | 691,845×47 | 41.0 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet` | 691,845×40 | 35.2 MB | si | — | `cobertura_canonica.py`, `medir_ficha_al_dia.py`, `medir_d1_parametros_pi.py` |
| `evaluacion/baseline/outputs/record_por_origen_fase2_detalle_estricta_2026-09-27.parquet` | 691,893×21 | 32.8 MB | si | — | — |
| `evaluacion/baseline/outputs/d1_parametros_pi.json` | no contado (pesado) | 12.6 MB | si | `medir_d1_parametros_pi.py` | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-1460_sobre_2026-10-02.parquet` | 692,713×20 | 11.6 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-2190_sobre_2026-10-02.parquet` | 692,715×20 | 11.6 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-1095_sobre_2026-10-02.parquet` | 692,121×20 | 11.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_k_postura-20_sobre_2026-10-02.parquet` | 691,845×20 | 11.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_k_postura-40_sobre_2026-10-02.parquet` | 691,845×20 | 11.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_k_postura-10_sobre_2026-10-02.parquet` | 691,845×20 | 11.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_k_postura-2.5_sobre_2026-10-02.parquet` | 691,845×20 | 11.5 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-548_sobre_2026-10-02.parquet` | 691,845×20 | 11.4 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_origen-lado_sobre_2026-10-02.parquet` | 691,845×20 | 11.4 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_k_postura-1_sobre_2026-10-02.parquet` | 691,845×20 | 11.4 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-365_sobre_2026-10-02.parquet` | 691,607×20 | 11.4 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_d1_ventana_postura-182_sobre_2026-10-02.parquet` | 691,206×20 | 11.3 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet` | 691,893×14 | 9.9 MB | si | — | _(4 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_detalle_sin_corte_era_2026-10-03.parquet` | 692,715×11 | 6.6 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_detalle_sin_corte_era_2026-10-02.parquet` | 691,845×11 | 6.5 MB | si | — | — |
| `evaluacion/baseline/outputs/d2_curvas.json` | no contado (pesado) | 6.3 MB | si | `medir_d2_capa2.py` | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_detalle_sin_corte_era_2026-10-01.parquet` | 691,845×11 | 6.2 MB | si | — | — |
| `evaluacion/baseline/outputs/fase0_detalle_ponderada_logit.parquet` | 691,869×9 | 6.1 MB | si | — | — |
| `evaluacion/baseline/outputs/fase0_detalle_union.parquet` | 691,869×9 | 6.1 MB | si | — | — |
| `evaluacion/baseline/outputs/fase0_detalle_primaria.parquet` | 691,893×9 | 6.0 MB | si | — | — |
| `evaluacion/baseline/outputs/fase0_detalle_sin_tema.parquet` | 691,460×9 | 6.0 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_estadisticos_sin_corte_era_2026-10-03.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_estadisticos_sin_corte_era_2026-10-02.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | — |
| `evaluacion/baseline/outputs/censo_estadisticos_2026-10-03.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | _(3 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_estadisticos_sin_corte_era_2026-10-01.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_estadisticos_2026-10-02.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/censo_estadisticos_2026-09-28.json` | objeto: formato, generado, generador, mo | 1.2 MB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/calibracion_actas_2026-09-28.json` | objeto: formato, generador, generado, mo | 734 KB | si | — | _(2 lo nombran)_ |
| `evaluacion/baseline/outputs/calibracion_actas_2026-10-03.json` | objeto: formato, generador, generado, mo | 731 KB | si | — | _(2 lo nombran)_ |
| `evaluacion/baseline/outputs/calibracion_actas_2026-10-02.json` | objeto: formato, generador, generado, mo | 729 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/d2_panel_primario.json` | objeto: formato, generador, generado, le | 422 KB | si | `medir_d2_capa2.py` | — |
| `evaluacion/baseline/outputs/record_por_origen_fase0_1_2026-09-27.json` | objeto: k_shrink, umbral_lado, recambios | 131 KB | si | — | — |
| `evaluacion/baseline/outputs/record_por_origen_fase2_censo_estricta_2026-09-27.json` | objeto: n_votos, k, umbral_lado, min_act | 69 KB | si | — | — |
| `evaluacion/baseline/outputs/record_por_origen_fase2_censo_harness_2026-09-27.json` | objeto: n_votos, k, umbral_lado, min_act | 69 KB | si | — | — |
| `evaluacion/baseline/outputs/firma_tematica_fase1_2_2026-09-21.json` | objeto: k_shrink, filtro, FASE1, FASE1_c | 23 KB | si | — | — |
| `evaluacion/baseline/outputs/censo_limpio_2026-09-28.json` | objeto: censo, n_votos, n_actas, n_leyes | 19 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/prueba1_pivotes_por_capitulo_2026-09-17.json` | objeto: proyecto_id, fecha_corte, rango_ | 13 KB | si | — | — |
| `evaluacion/baseline/outputs/d1_panel_primario.json` | objeto: formato, generador, generado, le | 12 KB | si | `medir_d1_parametros_pi.py` | — |
| `evaluacion/baseline/outputs/medir_estabilidad_record_por_tema_2026-09-17.json` | objeto: k_shrink, umbrales_n, recambios, | 12 KB | si | — | — |
| `evaluacion/baseline/outputs/prueba2_reconstruccion_por_rango_2026-09-17.json` | objeto: paso1_tramos_con_articulo_en_act | 10 KB | si | — | — |
| `evaluacion/baseline/outputs/calibracion_declarada.json` | objeto: formato, generador, generado, me | 9 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/guard_era_sin_corte.json` | objeto: formato, generador, generado, me | 7 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/medir_record_por_tema_limpio_2026-09-28.json` | objeto: fila, estricta, n_comun, reprodu | 7 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/validacion_piloto_titulos_2026-09-16.json` | objeto: margen_walkforward_dias, flags,  | 7 KB | si | — | — |
| `evaluacion/baseline/outputs/fase0_control_temas_censo.json` | objeto: arms, n_boot, seed, muestra | 6 KB | si | — | — |
| `evaluacion/baseline/outputs/metrica_de_verdad.json` | objeto: formato, generador, generado, me | 5 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/baseline_voto_individual.json` | objeto: columna, global, calibracion, po | 5 KB | si | `baseline_voto_individual.py` | `test_censo_estadisticos.py`, `verificar_regeneracion.py` |
| `evaluacion/baseline/outputs/firma_tematica_fase0_celdas_2026-09-21.json` | objeto: por_filtro, cobertura_tema | 5 KB | si | — | — |
| `evaluacion/baseline/outputs/guard_era_medicion.json` | objeto: _que_es, _n_votos, resultados, m | 5 KB | si | `medir_guard_era.py` | — |
| `evaluacion/baseline/outputs/diagnostico_senado.json` | objeto: senado | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_combinar_temas_ponderada_2026-09-15.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_combinar_temas_primaria_2026-09-15.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_combinar_temas_peor_tema_2026-09-16.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_combinar_temas_union_2026-09-15.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_guard_shrink.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/baseline_guard_off.json` | objeto: n_actas_evaluadas, n_actas_salta | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/record_por_tema_2026-09-04.json` | objeto: _que_es, _como_se_reproduce, el_ | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/merge_ids_medicion_2026-09-04.json` | objeto: _que_es, _como_se_midio, _alias, | 4 KB | si | — | — |
| `evaluacion/baseline/outputs/d2_controles.json` | objeto: formato, generador, generado, si | 3 KB | si | `medir_d2_capa2.py` | — |
| `evaluacion/baseline/outputs/medir_fuga_historia_2026-09-28.json` | objeto: detalle, n_votos, votos_con_ley_ | 3 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/baseline_canonico.json` | objeto: n_votos_sustantivos, por_nivel,  | 2 KB | si | `baseline_canonico.py` | — |
| `evaluacion/baseline/outputs/medir_rec_por_tema_2026-09-16.json` | objeto: cobertura_tema_por_acta, curva_s | 2 KB | si | — | _(1 lo nombran)_ |
| `evaluacion/baseline/outputs/d1_controles_brazos.json` | objeto: formato, generador, generado, a_ | 2 KB | si | `medir_d1_parametros_pi.py` | — |
| `evaluacion/baseline/outputs/fase1_rec_por_tema_censo.json` | objeto: camara_filtro, global_subconjunt | 2 KB | si | `fase1_rec_por_tema.py` | _(2 lo nombran)_ |
| `evaluacion/baseline/outputs/d2_seleccion.json` | objeto: formato, generador, generado, an | 2 KB | si | `medir_d2_capa2.py` | — |
| `evaluacion/baseline/outputs/prueba3_cobertura_universo_vivo_2026-09-17.json` | objeto: definicion_universo_vivo, n_univ | 2 KB | si | — | — |
| `evaluacion/baseline/outputs/validacion_leybases_capitulos_2026-09-16.json` | objeto: fecha_corte_walkforward, flags,  | 1020 B | si | — | — |
| `fase0/data/raw/detalle_129_137.csv` | 231,043×7 | 17.6 MB | si | — | `ingesta.py` |
| `fase0/data/clean/detalle.parquet` | 231,043×7 | 1.4 MB | si | `ingesta.py` | `baseline_bloque.py` |
| `fase0/data/raw/cabecera_129_137.csv` | 899×20 | 183 KB | si | — | `ingesta.py` |
| `fase0/data/clean/cabecera.parquet` | 899×20 | 45 KB | si | `ingesta.py` | `baseline_bloque.py` |
| `fase0/outputs/baseline_resultados.json` | objeto: fuente, n_actas_total, n_votos_s | 701 B | si | `baseline_bloque.py` | — |
| `modelo/agregador_institucional/outputs/backtest_detalle.csv` | 4,858×9 | 304 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_calibracion_epsilon0_tau_2026-09-16.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_agregador_asistencia.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_agregador.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/agregador_institucional/outputs/backtest_agregador_dir_presentes.json` | objeto: n_actas, brier, brier_baseline_t | 1 KB | si | — | — |
| `modelo/ensemble/outputs/panel_regresion.json` | objeto: proyecto_id, fecha, camara_orige | 199 KB | si | `test_panel_regresion.py` | `perturbar_panel.py`, `verificar_regeneracion.py` |
| `modelo/ensemble/outputs/registro_parametros.json` | objeto: formato, generado_por, entrada,  | 140 KB | si | `registro_parametros.py` | _(2 lo nombran)_ |
| `modelo/ensemble/outputs/validacion_sobre_tablas_walkforward_corte50.json` | objeto: resumen, detalle | 36 KB | si | — | — |
| `modelo/ensemble/outputs/validacion_sobre_tablas_walkforward.json` | objeto: resumen, detalle | 25 KB | si | `validar_sobre_tablas_walkforward.py` | — |
| `modelo/ensemble/outputs/beta_dictamen.json` | objeto: M0_crudo, M1_offset, M2_offset_t | 6 KB | si | `estimar_beta_dictamen.py` | `verificar_regeneracion.py` |
| `modelo/ensemble/outputs/beta_dictamen_senado.json` | objeto: M0_crudo, M1_offset, M2_offset_t | 5 KB | si | — | `verificar_regeneracion.py` |
| `modelo/ensemble/outputs/epsilon_tau_2026-09-16.json` | objeto: n_votos, n_actas, epsilon, tau_s | 5 KB | si | — | — |
| `modelo/ensemble/outputs/epsilon_tau.json` | objeto: n_votos, n_actas, epsilon, tau_s | 4 KB | si | `estimar_epsilon_tau.py` | — |
| `modelo/ensemble/outputs/beta_dictamen_ab_2026-09-04.json` | objeto: _que_es, _como_se_reproduce, cor | 3 KB | si | — | — |
| `modelo/ensemble/outputs/psi_arrastre.json` | objeto: P1_psi_unico, P1b_psi_con_tema_o | 3 KB | si | `estimar_psi_arrastre.py` | — |
| `modelo/ensemble/outputs/nowcast_HIP-SALUD-OPO.json` | objeto: proyecto_id, proyecto_id_interno | 3 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_1167-D-2025.json` | objeto: proyecto_id, proyecto_id_interno | 3 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_HIP-ECON-PE.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/tau_limpio_2026-09-28.json` | objeto: n_votos, n_actas, tau_motor_hoy, | 2 KB | si | — | _(1 lo nombran)_ |
| `modelo/ensemble/outputs/nowcast_HIP.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/nowcast_HIPOTETICO-ECON-PE.json` | objeto: proyecto_id, proyecto_id_interno | 2 KB | si | — | — |
| `modelo/ensemble/outputs/backtest_cadena.json` | objeto: n_evaluados, tasa_base_sancion,  | 2 KB | si | — | — |
| `modelo/ensemble/outputs/backtest_cadena_fina.json` | objeto: n_evaluados, version, tasa_base_ | 2 KB | si | — | — |
| `modelo/ensemble/outputs/theta_sobre_tablas.json` | objeto: A_theta_vs_resto, B_solo_sobre_t | 1 KB | si | `estimar_theta_sobre_tablas.py` | _(3 lo nombran)_ |
| `modelo/ensemble/outputs/chequeo_direccion_beta_2026-09-28.json` | objeto: n_panel, n_comun, produccion_M6_ | 1001 B | si | — | _(1 lo nombran)_ |
| `modelo/voto_individual/outputs/desvios_por_voto.parquet` _DESVIOS_POR_VOTO_ | 900,572×6 | 1.2 MB | si | `disciplina.py` | `export_base.py` |
| `modelo/voto_individual/outputs/disciplina_por_anio.csv` | 9,302×7 | 636 KB | si | `disciplina.py`, `ficha.py` | — |
| `modelo/voto_individual/outputs/disciplina_por_periodo.csv` | 4,718×10 | 462 KB | si | `disciplina.py`, `ficha.py` | — |
| `modelo/voto_individual/outputs/disciplina_individual.csv` _DISCIPLINA_INDIVIDUAL_ | 1,851×23 | 328 KB | si | `test_ensemble.py`, `disciplina.py` | `agregador.py`, `comparar_vias_icg.py`, `estimar_gamma_individual.py` |
| `modelo/voto_individual/outputs/set_pivote.json` | objeto: definicion, min_votos, legislado | 1 KB | si | `disciplina.py` | — |
| `producto/dashboard/data/mapa_modelo_semantica.json` | objeto: _comentario, version, meta, etap | 72 KB | si | — | — |
| `variables/bloque/outputs/serie_bloque.parquet` | 304×9 | 16 KB | si | `COMMITEAR-2026-09-08.ps1`, `bloque.py` | _(2 lo nombran)_ |
| `variables/embudo/outputs/p_embudo.parquet` | 42,141×5 | 432 KB | si | `embudo.py` | _(1 lo nombran)_ |
| `variables/embudo/outputs/backtest_embudo.json` | objeto: sancionado, sancionado_sin_orige | 151 KB | si | `embudo.py` | — |
| `variables/embudo/outputs/embudo_por_comision.csv` | 65×4 | 3 KB | si | `embudo.py` | — |
| `variables/embudo/outputs/embudo_por_anio.csv` | 19×5 | 539 B | si | `embudo.py` | — |
| _+25 mas_ | | | | | |

**Lo que el inventario marca**

- Tienen productor y **ningun consumidor** (56): `cobertura_canonica.json`, `verificar_bots.json`, `votaciones_nuevas.parquet`, `estado_bot.json`, `argentinadatos_actas.parquet`, `argentinadatos_votos.parquet`, `ckan_diputados_actas.parquet`, `ckan_diputados_votos.parquet` _+48_. Es lo esperable en un entregable para humanos; en un intermedio significa que sobra.
- **Ningun archivo de codigo los nombra** (79, 313.1 MB): `record_por_origen_fase2_detalle_harness_2026-09-27.parquet`, `record_por_origen_fase2_detalle_estricta_2026-09-27.parquet`, `votaciones_2003-2007_Kirchner.xlsx`, `censo_detalle_d1_ventana_postura-1460_sobre_2026-10-02.parquet`, `censo_detalle_d1_ventana_postura-2190_sobre_2026-10-02.parquet`, `censo_detalle_d1_ventana_postura-1095_sobre_2026-10-02.parquet`, `censo_detalle_d1_k_postura-20_sobre_2026-10-02.parquet`, `censo_detalle_d1_k_postura-40_sobre_2026-10-02.parquet` _+71_. Ojo: un output con nombre armado por f-string cae aca y esta vivo. Lo que hay que mirar de verdad son los pesados.

## Puntos de entrada

- `coordinacion/AUDITORIA-2026-09/cobertura_canonica.py`
- `coordinacion/AUDITORIA-2026-09/contraste_aprobacion.py`
- `coordinacion/AUDITORIA-2026-09/medir_ficha_al_dia.py`
- `coordinacion/AUDITORIA-2026-09/verificar_bots.py`
- `datos/argentinadatos/src/explorar_campos.py`
- `datos/argentinadatos/src/to_canonical.py`
- `datos/argentinadatos/tests/test_padron_senado.py`
- `datos/bot_recoleccion/src/dae_senado.py`
- `datos/bot_recoleccion/src/tp_diputados.py`
- `datos/bot_recoleccion/src/votaciones.py`

## Archivos centrales

Ordenados por cuantos otros archivos dependen de ellos. Tocar uno de arriba tiene mas radio de impacto.

| Archivo | LOC | Lo usan | Simbolos |
|---|---:|---:|---|
| `rutas.py` | 212 | 43 | `_env`, `inventario` |
| `evaluacion/baseline/src/baseline_voto_individual.py` | 968 | 20 | `_norm_cond`, `_ContadorAvisos`, `perfil`, `_metricas` |
| `variables/bloque/src/bloque.py` | 847 | 20 | `_canon_linaje`, `_norm_nombre`, `_cargar_padron_linaje_senado`, `_enriquecer_linaje_senado` |
| `modelo/ensemble/src/nowcast_puertas.py` | 1020 | 19 | `_resolver_multietiqueta`, `_tema_auto`, `_bloque`, `era_de` |
| `definiciones.py` | 261 | 16 | `periodo_parlamentario`, `gobierno_por_fecha`, `era_de`, `normalizar_mayoria_valor` |
| `evaluacion/baseline/src/censo_estadisticos.py` | 370 | 12 | `skill_ic_desde_sumas`, `dif_brier_ic_desde_sumas`, `_sha16`, `_git_head` |
| `modelo/ensemble/src/ensemble.py` | 389 | 11 | `_cargar_simulador`, `_cargar_proyector`, `_root`, `_padron_csv` |
| `modelo/agregador_institucional/src/agregador.py` | 496 | 6 | `umbral_aprobacion`, `_prob_conductas`, `simular_votacion`, `_linea_bloque_por_acta` |
| `evaluacion/baseline/src/metrica_de_verdad.py` | 307 | 6 | `DestinoProtegido`, `cortes_de`, `_skill`, `_dif_brier` |
| `modelo/ensemble/src/puerta_d.py` | 244 | 6 | `camara_revisora`, `_padron_de`, `_clip01`, `_logit` |
| `variables/embudo/src/embudo.py` | 730 | 4 | `cargar_icg`, `_mes_rezagado`, `cargar`, `cargar_sqlite` |
| `modelo/voto_individual/src/disciplina.py` | 535 | 4 | `_sin_acentos`, `excluir_no_medibles`, `actas_disputadas`, `cargar` |

## Flujo interno

- `evaluacion/baseline/tests/` → `evaluacion/baseline/src/` (18)
- `modelo/ensemble/tests/` → `modelo/ensemble/src/` (18)
- `modelo/ensemble/src/` → `./` (15)
- `evaluacion/baseline/src/` → `./` (13)
- `variables/proyecto/tests/` → `variables/proyecto/src/` (10)
- `evaluacion/baseline/tests/` → `./` (9)
- `evaluacion/baseline/src/` → `modelo/ensemble/src/` (8)
- `evaluacion/baseline/src/` → `variables/bloque/src/` (6)
- `modelo/ensemble/src/` → `variables/bloque/src/` (6)
- `datos/expedientes/tests/` → `datos/expedientes/src/` (5)
- `datos/padron/tests/` → `datos/padron/src/` (5)
- `datos/proyectos/tests/` → `datos/proyectos/src/` (5)

## Se tocan juntos

Segun el historial de git. Si vas a cambiar uno, mira el otro.

- `Nowcast Congreso Argy/.mapa/mapa.json` + `Nowcast Congreso Argy/MAPA.md` (70 commits)
- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` (56 commits)
- `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` + `Nowcast Congreso Argy/tablero_datos.js` (50 commits)
- `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` + `Nowcast Congreso Argy/tablero_datos.js` (47 commits)
- `Nowcast Congreso Argy/.mapa/mapa.json` + `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` (33 commits)
- `Nowcast Congreso Argy/MAPA.md` + `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` (33 commits)
- `Nowcast Congreso Argy/coordinacion/ESTADO-DEL-PROYECTO.md` + `Nowcast Congreso Argy/coordinacion/TABLERO.md` (25 commits)
- `Nowcast Congreso Argy/.mapa/mapa.json` + `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` (24 commits)
- `Nowcast Congreso Argy/.mapa/mapa.json` + `Nowcast Congreso Argy/tablero_datos.js` (24 commits)
- `Nowcast Congreso Argy/MAPA.md` + `Nowcast Congreso Argy/coordinacion/EN-HUMANO.md` (24 commits)

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
- `es.wikipedia.org` — `datos/senado/src/bajar_anexos_wiki.py`
- `votaciones.hcdn.gob.ar` — `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`
- `argentinadatos.com` — `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`

## Configuracion requerida

- `ANTHROPIC_API_KEY` — `variables/proyecto/src/agente_taxonomias.py`
- `ASIST` — `modelo/agregador_institucional/src/agregador.py`
- `BANDERA_NUEVA` — `modelo/ensemble/tests/test_defaults_fijados.py`
- `BETA_DICTAMEN` — `modelo/ensemble/src/beta_dictamen.py`, `modelo/ensemble/tests/test_beta_dictamen.py`
- `BORRAR` — `datos/canonica/src/entity_resolution.py`
- `CACHE` — `datos/expedientes/src/ingesta_ckan.py`, `datos/senado/src/scrape_votaciones.py`
- `CAMARA` — `modelo/ensemble/validar_condicionamiento_votos.py`
- `CANON` — `datos/canonica/src/entity_resolution.py`, `datos/export/src/export_base.py`, `modelo/agregador_institucional/src/agregador.py`
- `CI` — `datos/padron/tests/test_vigilar_padron.py`
- `CLEAN` — `datos/canonica/src/build.py`, `variables/embudo/src/cohorte_dos_rutas.py`
- `COMBINAR_TEMAS` — `modelo/ensemble/src/nowcast_puertas.py`
- `CSV` — `datos/decada_votada/src/from_csv.py`
- `DISC` — `modelo/agregador_institucional/src/agregador.py`
- `DISCIPLINA` — `modelo/ensemble/src/ensemble.py`
- `EMBUDO_FUENTE` — `variables/embudo/src/embudo.py`

## Frescura

- Bitacoras vencidas: `./`, `casos/`, `coordinacion/`, `datos/canonica/`, `datos/expedientes/`, `datos/taxonomias/`, `evaluacion/baseline/`, `modelo/agregador_institucional/`, `modelo/ensemble/`, `modelo/voto_individual/`, `producto/dashboard/`, `tests/`, `variables/bloque/`, `variables/proyecto/`
