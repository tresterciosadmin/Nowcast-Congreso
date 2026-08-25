# TABLERO — claim de tareas (anti-colisión)

> Antes de empezar a trabajar un módulo, **reclamalo acá**: movelo a "En curso" con tu nombre/ID y fecha. Al terminar, movelo a "Hecho" y liberá el módulo. Regla: **un módulo lo trabaja una sola persona/Claude a la vez.**

Cómo reclamar: editá este archivo en tu rama, agregá la fila, y mencioná en el PR "claim: <módulo>".

---

## Sesion 2026-08-25 — INCIDENTE: marcadores de conflicto commiteados en los outputs de `vigilar_padron`

| Modulo | Quien | Desde | Estado |
|---|---|---|---|
| **datos/padron** | Claude (lo trajo Valle) | 2026-08-25 | **Dano REPARADO, modulo LIBRE.** La causa estructural queda en `URGENTE.md` 6. |

El commit `5aff5b0` subio `data/estado_vigilancia.json` y `outputs/vigilancia_padron.md` **con los marcadores `<<<<<<< Updated upstream` / `>>>>>>> Stashed changes` adentro**. El JSON dejo de parsear. Origen: esos dos archivos los escribe **el bot los lunes** (`bot-nowcast`, `131a698`, 24-08 11:15) **y tambien la corrida local**; el pull choco, se eligio *Stash changes and continue*, y al reaplicar el stash git dejo los marcadores.

**No da error, y ese es el problema.** `vigilar_padron.py:349` atrapa el `JSONDecodeError` y **lo trata como primera corrida**: se pierde `hash_visto_desde`, que mide hace cuantos dias el raw no cambia y dispara el aviso de rancio. El del Senado venia del **07-08** (18 dias).

**Reparado** trayendo los dos blobs del commit del bot con `GIT_OPTIONAL_LOCKS=0 git show <commit>:<ruta> > <ruta>` — `git show` NO toma `index.lock`, a diferencia de `git checkout --`. **Sin perdida:** huella y `n` eran identicos en las dos versiones (`00b85fe482afded8`/256 y `648d1abba448dcd0`/72); solo cambiaba `ultima_corrida`, y la del bot es mas nueva. Barrido de todo el repo: **ningun otro archivo con marcadores**.

⚠️ **PENDIENTE DE VALLE: commitear la restauracion.** Los dos archivos figuran modificados.

⚠️ **Causa estructural NO resuelta, en `URGENTE.md` 6:** dos escritores sobre un archivo generado y versionado. No se puede sacar de git (el workflow necesita el estado para comparar entre corridas): la salida es que **una corrida local no pueda escribir la ruta versionada**.

## Sesion 2026-08-25 (Valle+Claude) — anexo 2. MAPA-MODELO sin puntas de flecha, y nodos arrastrables

| Modulo | Quien | Desde | Estado |
|---|---|---|---|
| **producto/dashboard** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Sin `marker-end` en todo el diagrama + arrastre de nodos. |

**Fuera las puntas de flecha, en todo el diagrama.** Se dibujaban en el borde de la CAJA del nodo y no en el de su FORMA: en un ovalo eso las deja flotando en el hueco, y con varias aristas entrando por carriles distintos aparecian **apiladas y sueltas** (`Roster nominal`). Decision de Valle: sacarlas, no reanclarlas — el sentido lo da el layout (izquierda a derecha por columnas) y el camino vivo se distingue por color y grosor. **Como volver atras quedo escrito en el codigo:** anclar el final del camino a la forma, no a la caja. `marcadores()` quedo vacia y el `<defs>` como enganche.

**Los nodos se arrastran.** Las lineas, los recuadros de grupo y las bandas siguen al nodo. Captura del puntero sobre el `svg` (cada cuadro se redibuja el diagrama y el `<g>` del nodo deja de existir), umbral de 4 px para no correr un nodo al abrir su ficha, y `NODO_MOVIDO` para que el `click` posterior a un arrastre no abra la ficha.

**`encuadrar()` es funcion nueva, sacada de `colocar()`.** Los recuadros y el tamano del lienzo salen de donde quedaron los nodos, pero llamar a `colocar()` entero devolveria el nodo a su lugar. Una cuenta, dos usuarios: layout inicial y arrastre.

**NO persiste, a proposito** (decision de Valle): recargar devuelve el layout automatico y eso ES el deshacer; el uso previsto es desenredar una zona, sacar la captura y pedir la correccion. Si alguna vez hay que conservarlo, **las posiciones son DATOS y van a `mapa_modelo_datos.js`**, no al HTML.

**Verificado:** las puntas en Chromium headless sobre `file://` — 144 lineas, 0 con `marker-end`, 0 marcadores en `defs`, cero errores de consola, mas captura. **El arrastre lo confirmo Valle en su maquina** (la prueba de render se cayo porque el sandbox dejo de aceptar comandos de shell; la corrida de Valle es la que vale igual).

**NO es de este cambio y sigue pendiente:** el dibujo arranca encajado abajo y *Ajustar* no lo recentra.

## Sesion 2026-08-25 (Valle+Claude) — anexo. El arco A→B del MAPA-MODELO se dibujaba con el camino del arco entre camaras

| Modulo | Quien | Desde | Estado |
|---|---|---|---|
| **producto/dashboard** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** `caminoCondiciona()` ahora tiene los DOS casos. |

**Lo vio Valle en pantalla.** La arista `condiciona` de `g_A` → `c_p_mayoria_origen` salia como **un pinche turquesa de 6 px** asomando sobre el nodo Paso B, con la etiqueta **debajo de los dos nodos**. Causa: hay **dos** aristas `condiciona` en `mapa_modelo_datos.js` y **una sola** funcion de camino, escrita —segun su propio comentario— para el arco **entre camaras**. `g_A` y `c_p_mayoria_origen` estan en la misma camara, misma fila, sin recuadro de grupo: el camino apuntaba hacia atras y hacia arriba y colapsaba. Ahora, sin recuadro destino o sin 60 px para bajar, dibuja un **puente corto por arriba**.

**Y la etiqueta se calculaba DOS veces** (la formula del caso (a) repetida en la rutina de dibujo). Ahora el ancla sale de `caminoCondiciona` via `a._rot` y el dibujo la consume: una sola cuenta. Mismo problema de la sesion, esta vez en el dibujo.

**Verificado renderizando en Chromium headless sobre `file://`:** cero errores de consola; el camino medido en el DOM pasa a `M2823.5,302.5 C2823.5,258.5 3034.5,258.5 3034.5,300.5` (211×33 px sobre los dos nodos) y el rotulo sube a la cima del puente. Captura revisada a ojo.

⚠️ **ANOTADO Y NO TOCADO (capa de datos, decision de Valle):** `g_A → c_p_mayoria_origen` esta declarada `condiciona` pero **`g_C → g_D` esta declarada `calcula`**, cuando segun la formulacion son simetricas. El mapa dice dos cosas distintas sobre la misma relacion.

**NO es de este cambio y sigue pendiente:** el dibujo arranca encajado abajo y *Ajustar* no lo recentra (medido el 22-08: viene de antes).

## Sesion 2026-08-25 (Valle+Claude) — CERRADA. Auditoria de duplicaciones: definiciones compartidas + la TERCERA formulacion

| Modulo | Quien | Desde | Estado |
|---|---|---|---|
| **datos/export** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Re-exporta las definiciones en vez de copiarlas. |
| **modelo/voto_individual** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Idem. |
| **modelo/agregador_institucional** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Idem (version escalar). |
| **variables/asistencia_quorum** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Idem. |
| **variables/legislador** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** Idem. |
| **casos** | Claude (con Valle) | 2026-08-25 | **HECHO, modulo LIBRE.** `proyeccion_hipotetica_bicameral.py` neutralizado. |

**ADR-0014: las definiciones compartidas viven en UN solo lugar.** `definiciones.py` en la raiz, hermano de `rutas.py`: **`rutas.py` dice DONDE esta cada cosa, `definiciones.py` dice QUE ES cada cosa.** Entran `periodo_parlamentario` (estaba en 4 modulos), `normalizar_mayoria` (3, en dos formas: Serie y escalar), `MAYORIAS` y `BANCAS` (`MIEMBROS`, 3). Los modulos **RE-EXPORTAN** el nombre, asi que `export_base.periodo_parlamentario` sigue existiendo y **aguas abajo no cambia nada**.

**El argumento, y esta medido.** El guardian ya existia (`tests/test_definiciones_compartidas.py`, 20-08) y estaba **avisando de un bug que nadie podia arreglar**: las CUATRO copias revientan con backend pyarrow (`a % 2` sobre `int64[pyarrow]` -> `NotImplementedError`), el arreglo era **una linea por copia**, y llevaba un mes trabado con el motivo en el propio `xfail`: *"toca 4 modulos con dueno"*. **Con las copias, un arreglo de una linea costaba cuatro claims de modulo.** El bug quedo arreglado y al test se le saco el `xfail`.

**Cero cambio de comportamiento, verificado antes de aplicar:** 15 casos borde de fecha y 13 de mayoria, en los **dos backends de dtype**, contra las cuatro copias viejas transcritas del disco. Identico con numpy; con pyarrow las viejas levantan `NotImplementedError` y la nueva responde.

**Test que falla con el codigo viejo:** `test_ninguna_copia_redefine_las_definiciones` compara **identidad de objeto**, no resultados. Los tests que ya estaban comparaban valores, y por eso pasaban igual con una definicion o con cinco. Verificado re-pegando a mano en `export_base.py` una copia *behaviorally identica*: los otros siete siguen en verde y **solo ese falla**. Archivo completo: **8 chequeos**.

**LA TERCERA FORMULACION, viva y sin neutralizar.** `casos/proyeccion_hipotetica_bicameral.py` calculaba con `umbral = n // 2 + 1` —mayoria **ABSOLUTA** (129 en Diputados), no simple, y sin el arreglo del empate del ADR-0013— y con `p_acompana` = share del bloque recortado a [0,02·0,98], sin componer `share·(1−d) + (1−share)·(d/2)` y sin separar direccion de presencia. **El detalle que lo delata:** el 22-08 alguien lo toco para importar `P_INCERTIDUMBRE` del contrato del modelo *"porque una copia es una divergencia esperando"* — y arreglo esa copia sin ver las otras dos, tres lineas mas abajo. Neutralizado (`main` levanta `SystemExit`; el cuerpo viejo quedo como `_main_original`). Copia en `Archivos_Borrar/`.

**Segunda aparicion del patron "dos archivos, mismo nombre, contenido distinto".** `Aportes sobre dataset congreso/Decada Votada/asuntos-diputados.csv` = **3.034 actas, 1993–2026**; el del ZIP que lee `run_pipeline.py:29` = **1.499, 2001–2014**. Contrastado contra `actas_canonico.parquet` (6.237 actas): de Diputados, antes de 2001 la canonica tiene **1994: 14 actas y 1997: 12, y nada mas**. Habia ~242 actas de 1993–2000 en disco que la base nunca vio. **Valle decidio que no interesan y hacen ruido** -> la carpeta suelta (19 MB) se fue a `Archivos_Borrar/`. **El ZIP NO se toco:** es dependencia viva.

**Lo que se miro y se decidio NO tocar** (homonimia legitima, no duplicacion): `main` ×73, `cargar` ×10, `construir` ×7, `_get` ×8, `_pedir` ×4, `to_canonical.py` ×3, los `check`/`chk` de los tests, y los cuatro `_fecha_iso` —que parsean formatos genuinamente distintos y unificarlos seria peor—. `variables/bloque::_periodo_parlamentario` tampoco se unifica: es un ANIO legislativo, otro concepto con nombre parecido, ya cubierto por su propio test.

⚠️ **PENDIENTE DE VALLE — la corrida es la que vale.** `python -m pytest tests/ -q` en PowerShell, mas los tests de los 5 modulos tocados (`datos/export/tests`, `modelo/voto_individual/tests`, `modelo/agregador_institucional/tests`, `variables/legislador/tests`, y `variables/asistencia_quorum` si tiene). **"Pasa en el sandbox" no es "pasa".**

⚠️ **DOS COSAS MEDIDAS Y NO TOCADAS, en `URGENTE.md` 4 y 5:** (a) el panel de puertas muestra **dos umbrales distintos** —la barra contra 122,1 y el margen contra 129—, que es el bug del 22-08 sobreviviendo en la mitad del codigo; (b) tres de los cuatro `_fecha_iso` arman el ISO sin validar, asi que `31/02/2026` sale como `"2026-02-31"`.

## Sesion 2026-08-22 (Valle+Claude) — CERRADA. UNA SOLA FORMULACION + siete errores del calculo del voto

| Modulo | Quien | Desde | Estado |
|---|---|---|---|
| **modelo/ensemble** | Claude (con Valle) | 2026-08-22 | **HECHO, modulo LIBRE.** Baja de la v1 (ADR-0012) y punto de entrada unico por puertas. |
| **modelo/agregador_institucional** | Claude (con Valle) | 2026-08-22 | **HECHO, modulo LIBRE.** El empate ya no aprueba (ADR-0013). |
| **datos/padron** | Claude (con Valle) | 2026-08-22 | **HECHO, modulo LIBRE.** Foto completa de la camara + linaje re-sincronizado. |

**LA FORMULACION ES UNA SOLA (ADR-0012).** `P(aprobacion) = [A observada] · P(B | caracter de origen) · [C observada] · P(D | caracter de la revisora)`. **A y C NO son probabilidades**: son el caracter observado del dictamen y CONDICIONAN, no multiplican; sin dato el condicionante se encoge a 0. `p_llega_recinto` sale de la cadena (es agenda politica, y no se modela). **El numero pasa a ser CONDICIONAL** —"si las dos camaras lo votan, ¿lo aprueban?"— y la interfaz lo dice.

**La baja se hizo sin borrar:** `componer`, `_p_llega_de_embudo`, `nowcast_proyecto`, `nowcast_auto`, `imprimir_tarjeta`, la CLI de `ensemble.py` y el `main` de `backtest_cadena.py` levantan `SystemExit` con el motivo y a donde ir. Copias enteras en `Archivos_Borrar/BORRAR_modelo-ensemble-src-*.py`.

**Punto de entrada vivo:** `modelo/ensemble/src/nowcast_puertas.py` — corre la cadena HACIA ADELANTE sobre la configuracion actual de las dos camaras y devuelve el numero **con el desagregado por legislador**: quien acompaña, quien no, sobre quien hay incognita y a quien ir a buscar. Su HTML: `casos/nowcast_puertas_html.py` -> `Nowcast-Puertas.html`.

**SIETE ERRORES en el calculo del voto, encontrados auditando el mecanismo a pedido de Valle.** Los tres de fondo:

1. **El numero del bloque se redondeaba a SI/NO en 0,5.** Coalicion Civica acompaña el 60,9% y el modelo daba 96,7%; Peronismo Federal con desvio 0,000 daba **1,000 exacto**. **Era la razon de que todo diera 99%.** Ahora se componen: `P = share·(1−d) + (1−share)·(d/2)`. Kirchnerismo: de 0,4% a **22,5%**.
2. **La DIRECCION salia del linaje y el DESVIO del bloque real.** Del Caño salia con **P=1,00** de acompañar al Ejecutivo teniendo un record de 0,01; De la Sota igual. Ahora con historial propio suficiente **manda el historial**.
3. **Faltar se leia como votar en contra.** Menem: vota el **1,3%** de las veces (preside) y cuando vota acompaña el **96%**. Direccion y presencia quedaron separadas; la presencia lo saca del conteo. Cubre tambien a Schiaretti (6%), marcado desde el 13-08.

Los otros cuatro: el record miraba el futuro (un nowcast de 2024 usaba el 85% de sus votos de despues); el tablero y la probabilidad salian de cuentas distintas; el umbral del navegador (129) no era el del modelo (125,5); y **el empate aprobaba** (ADR-0013).

**Cifras (medidas sobre el archivo generado).** Reforma de Ganancias al 2026-06-01, origen EJECUTIVO: **P 98,0% condicional**. Diputados 257 bancas · 132 acompañan / 107 no / **16 incognita** / 2 no votan · 150,5 afirmativos (banda 143-158) · umbral 122,1. Senado 72 · 40 / 25 / **7 incognita** / 0 · 45,5 afirmativos (banda 40-51) · umbral 35,6. **Antes el Senado tenia CERO incognitas y su banda era 46-51:** el modelo recupero incertidumbre real.

**Padron re-sincronizado con la taxonomia.** El arreglo del FIT por patron (Franco, 07-08) funciona, pero `padron_diputados.csv` se genero antes y nunca se recalculo: **24 filas cambian, 23 correctas**, `IZQUIERDA` pasa de 8 a **32**. La 24ª (Daer) es falso positivo del patron y quedo en URGENTE para Franco.

**El MAPA del modelo quedo actualizado:** la capa curada pasa de 96 a **103 nodos** y de 131 a **147 aristas**. Entran `nowcast_puertas.py`, `puerta_a.py`, `padron_vigente.py`, `dictamenes_firmas.parquet`, la ingesta de las Ordenes del Dia, las guardas de sobreconfianza y el `Nowcast-Puertas.html`; la v1 y `p_llega_recinto` quedan dibujadas como suspendidas. ⚠️ Anotado y NO tocado: el dibujo arranca encajado abajo y *Ajustar* no lo recentra — **no es de este cambio** (antes 3799x754, ahora 4312x754), es del HTML, que es capa de diseño y sigue pendiente de que elijas entre V1 y V2.

**Tests: 287 chequeos verdes.** Verificado ademas renderizando el HTML en un navegador: cero errores de consola.

⚠️ **PENDIENTE INMEDIATO, y bloquea dos cosas a la vez: decidir CONTRA QUE SE MIDE.** El backtest quedo neutralizado porque media la v1. Medido el 22-08: `p_sancion` da skill +0,4478 en total, pero **+0,2916 entre los 3.898 proyectos CON dictamen y −0,0257 entre los 34.799 sin el** — o sea que su merito es separar con-dictamen de sin-dictamen, justo lo que la Puerta A ahora OBSERVA. Medir la cadena nueva contra `sancionado` la mide contra algo que por diseño no predice. La unica salida con varianza real es el **MARGEN** del recuento (6.237 actas, 1.849 enganchadas). Esa misma decision destraba el condicionante del caracter (`estimar_delta_caracter`), hoy en 0 porque la etiqueta binaria esta degenerada: **2 RECHAZADO en 1.898**.

**Pendientes anotados:** el peso del firmante (jefes de bloque y presidentes de comision; las dos fuentes ya existen en el repo), el padron historico del Senado, y la Tarea 2 (nombres de las puertas).

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
- [x] ~~**producto/dashboard**~~ → reclamado 2026-08-20 por Claude+Franco; **re-reclamado 2026-08-20 por Claude+Valle** (ronda 2 del Mapa del Modelo; ver la sesion abierta, abajo). Dependencia cumplida: ensemble v1.

## Sesion 2026-08-21 (Valle+Claude) — CERRADA, firmantes del dictamen (Tarea 0 de la Puerta A). MODULOS LIBRES.

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **datos/expedientes** | Claude (con Valle) | 2026-08-21 | **HECHO, modulo LIBRE.** Ingestar los FIRMANTES del dictamen, que el CKAN no publica, desde el PDF de la Orden del Dia — en las DOS camaras. Prerrequisito de la Puerta A como senal observada (y de la C). Rama `feat/expedientes-firmantes-dictamen`. |

| **datos/padron** | Claude (con Valle) | 2026-08-21 | **HECHO, modulo LIBRE — cedido por Valle**, que era la owner. Construir el HISTORICO de Diputados: hoy el padron es la foto vigente y cubre **81 de 257 bancas en 2008** (209 en 2010, 142 en 2022, 257 recien en 2026). Es el pendiente que el propio README declara como "fase 2". Analogo de `src/padron_senado_historico.py`: archivo aparte, MISMO esquema, `fuente=derivado:canonica`. Sin esto, el bloque de las firmas del dictamen se resuelve para el 55% de los casos. |

**Decisiones de Valle (21-08):** (1) el backfill arranca **solo con proyectos de LEY** — 2.523 OD, no 18.087: las declaraciones y resoluciones no sirven; (2) el **bloque de cada firmante se resuelve contra `datos/padron`**, no se parsea del PDF (mas estable y manipulable); (3) la sonda del Senado se corrio en PowerShell.

**Hallazgos verificados el 21-08 (contra el disco y contra la fuente, no contra bitacoras):**

- **Regla de la URL de la OD de Diputados, cerrada:** `periodo = anio(od_publicacion) - 1882 - (1 si el mes es enero o febrero)`, y `https://www3.hcdn.gob.ar/dependencias/dcomisiones/periodo-<P>/<P>-<od_sin_ceros>.pdf`. El periodo parlamentario va del 1-mar al 28/29-feb (selector oficial de HCDN). Comprobada contra 7 PDF reales de 2008 a 2026. **El numero de OD NO reinicia con el periodo** (reinicia con la renovacion de la Camara, 10-dic de anios impares), asi que el periodo se deduce de la FECHA y nunca del numero. `www3` y `www4` son espejos.
- **El backfill es 7x mas chico de lo que decia el plan:** de 18.087 OD unicas totales, solo **2.523 son de proyectos de LEY** (cubren 3.176 proyectos). El resto son 2.988 de resolucion y 2.254 de declaracion.
- **HCDN ya cubre parte de la camara REVISORA.** El CKAN de Diputados publica los dictamenes de las comisiones DE Diputados, sea origen o revisora: de las 6.854 filas de dictamen de proyectos de ley, **1.515 son de proyectos con origen Senado**. El hueco real es el sistema de comisiones del Senado, no "la revisora".
- **El Senado es viable.** Formulario POST a `/parlamentario/parlamentaria/ordenDelDiaResultado` con `busqueda_orden[ordenDelDiaPeriodo]` (anios **1983-2026**) y `tipoExpedientes` (`PL` = proyecto de ley, `CD` = venido en revision de Diputados). Descarga por id interno `/parlamentario/parlamentaria/<id>/downloadOrdenDia`. **Los PDF del Senado SI traen la lista de firmantes**, con el mismo separador `–` que Diputados; verificado sobre OD 1/2026 (CD-21/24, "proyecto de ley venido en revision" = caso Puerta C) y OD 2/2026 (PE-46/24).

**RESULTADO FINAL (corrida completa del 22-08 con el parser nuevo, medido sobre el parquet y no sobre la consola).** `dictamenes_firmas.parquet`, 125.820 filas / 27 columnas: **125.504 firmas sobre 3.541 proyectos de ley, 2008-04-07 a 2026-06-19, 96,0% emparejado a un legislador** (120.545 firmas, 1.227 legisladores distintos). Dictamen unico 77.329 / mayoria 35.191 / minoria 12.984. Disidencia parcial 3.564 / total 147 / sin especificar 1.109. 5.373 primeros firmantes. Emparejamiento: exacto 114.188 · iniciales 3.429 · gana-el-oficial 2.928 · fuera de ventana 2.664 · sin match 1.879 · ambiguo 387 · nombre corto 29. Mas `dictamenes_comisiones.parquet`: 10.046 filas, 328 comisiones, 3.514 proyectos. De 2.517 Ordenes del Dia se leyeron **2.302 (91,5%)**; las 215 restantes entran **marcadas con su motivo**, no desaparecen (117 con ancla y sin nombres, 84 sin formula ni bloque reconocible, 13 con 404 de HCDN, 1 PDF corrupto).

**Control que valida el metodo (re-medido en la corrida final):** las 3.187 firmas leidas SIN la formula de cierre (las de 2020-2021, 152 Ordenes del Dia) resuelven al **96,2%, la misma tasa** que las 122.317 leidas con ella (96,0%). Si el reconocimiento por forma levantara texto cualquiera, esa tasa se desplomaria.

**Y el padron historico de Diputados** (`padron_diputados_historico.csv`, 7.323 filas / 2.060 legisladores): el emparejamiento paso de **55% a 98,9%**. El padron oficial cubria 81 de 257 bancas en 2008.

**Tests nuevos:** 44 (`test_od_url.py`) + 38 (`test_parser_od.py`) + 46 (`test_padron_diputados_historico.py`) = **128 checks**. Los del parser incluyen uno que **falla con el codigo viejo**: una OD con ancla y sin nombres devolvia cero filas y **115 Ordenes del Dia se evaporaban** del conteo sin que nada fallara.

**ADR-0011:** el chequeo del `.gitignore` que documentaba `PROTOCOLO-GIT.md` daba el resultado equivocado justo sobre los archivos con excepcion `!` — o sea sobre los que el equipo rescato a mano. Pasa a ser `git add -n`.

**Hallazgo ajeno, listado y NO tocado (es de `datos/canonica`, Franco):** 74 pares de `legislador_id` que son la misma persona con dos grafias -> `Archivos_Borrar/duplicados_entity_resolution_diputados.csv`.

**Pendiente de Valle (no lo puedo hacer yo):** `python -m pytest tests/ datos/proyectos/tests -q` en PowerShell, los tres tests nuevos, `git add -n` sobre los archivos nuevos, y reindexar (`python .mapa/indexar.py .` + `--sellar-todo`).

**OJO al limpiar:** `Archivos_Borrar/od_pdf/` esta en descartables porque el PDF crudo es regenerable, pero adentro viven el **cache y el checkpoint**, que son lo que hace que la actualizacion mensual cueste segundos en vez de 25 minutos. **No borrarla mientras el modulo este vivo.** El regimen normal son 50-80 Ordenes del Dia nuevas por anio, no 2.517.

**EL SENADO, CERRADO EN LA MISMA SESION.** `dictamenes_firmas_senado.parquet`: **17.688 firmas / 1.265 proyectos**, de 1.385 Ordenes del Dia leidas sobre **1.761 reales** (el listado da 1.882 filas pero 98 son el mismo documento repetido con otro id interno). **475 son de camara REVISORA** — la Puerta C con documentos contables por primera vez. El rol se lee del ORIGEN del expediente (`CD-` = revisora, `PE-`/`S-` = origen), no se supone.

**Emparejamiento 52,0% contra el 96,0% de Diputados, y el motivo esta medido:** `sin_candidatos = 7.450`, o sea que a esa fecha el padron del Senado no tiene ninguna banca cargada. **Arranca el 10-dic-2017 y 1.102 de las 1.761 OD son anteriores.** La canonica si cubre el Senado (220.426 votos desde 2004, 72 senadores exactos por anio no electoral), asi que se puede reconstruir — pero **NO se copia la receta de Diputados**: el Senado renueva por tercios cada dos anios con mandatos de seis. **Decision pendiente, con el numero que la justifica.**

**Cuatro diferencias de formato del Senado viejo** (formula "Sala de Comision," singular y sin articulo, fecha al reves, sin punto final, separador `.-`): al corregirlas las firmas saltaron de 9.454 a 17.688 y la lectura de 44% a 79%. **El Senado NO rotula mayoria/minoria** — cero coincidencias en 35 OD; el desacuerdo va como disidencia. Es diferencia entre camaras, no hueco del parser.

**Dos errores propios en el camino:** (1) el scraper extraia el enlace de paginacion y **no lo usaba**, asi que las paginas 2+ traian 2026 en vez del anio pedido — el sintoma fue que TODOS los anios daban exactamente 20 OD; el listado paso de 465 a 1.882. (2) La sonda de 3 paginas cortaba la lista de firmas al medio (`139-410.pdf` de 64 a 34 firmas); ahora sirve solo para detectar PDF escaneados, verificado con 25/25 OD de Diputados identicas.

✅ **CERRADO el 22-08: la corrida de Diputados con `--desde-cero` termino.** Las dos camaras ya salen del mismo codigo y las cifras de arriba son las de esa corrida. Diferencia contra la corrida previa: **+99 firmas, +3 Ordenes del Dia leidas**, y el reparto de clase se movio (minoria 13.267 → 12.984, unico 77.044 → 77.329). Son las Ordenes del Dia que la sonda de 3 paginas cortaba al medio, ahora leidas enteras.

⚠️ **PENDIENTE INMEDIATO, lo unico que separa al Senado del 96% de Diputados:** decidir el **padron historico del Senado**. Ver el bloque de arriba: la reconstruccion es viable pero no se copia la receta de Diputados.

**Descartable de la sonda:** `Archivos_Borrar/sonda_senado/` (33 HTML + 4 PDF + `ids_od_senado.csv`). Anotado en `PENDIENTES-DE-BORRAR.md`.

**URGENTE leido al empezar (regla de la casa).** `coordinacion/URGENTE.md` tiene vivo el punto 1 (validar 15 filas MEDIA del roster de jefes de bloque). **Se posterga explicitamente y se deja dicho por que:** es de `variables/proyecto`, no de `datos/expedientes`; no bloquea ni ensucia este trabajo; y su prioridad ya fue rebajada el 31-07 al medirse que `lider_jefe_bloque` aporta 1,25x y no 7x. Queda en URGENTE sin tocar.

## Sesion 2026-08-20 (Valle+Claude) — CERRADA, MAPA-MODELO.html: el flujo bicameral

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **producto/dashboard** | Claude (con Valle) | 2026-08-20 | **HECHO, modulo LIBRE.** Ronda 2 sobre `MAPA-MODELO.html`, sobre un croquis a mano de Valle. (1) El grafo por columnas pasa a ser un **diagrama de flujo bicameral**: dos bloques espejo (Camara de origen / Camara revisora) con el tronco compartido dibujado en los dos lados, formas por rol (rectangulo = base/fuente, hexagono = script, circulo = variable, rectangulo grueso = probabilidad), flecha curva gruesa `P(aprobar en Revisora \| se aprobo en Origen)` entre bloques, y lo condicionado por el paso previo agrupado y resaltado dentro de la revisora. (2) Se saca la capa de presentacion comercial (header, subtitulo, franja de formulas): las dos formulaciones se mudan a la leyenda, el lienzo arranca en el primer pixel y arriba queda una sola barra fina de instrumentos. (3) La ficha lateral por nodo se queda y se agranda. (4) Se resuelve la contradiccion de estado de las Puertas A y C. Sin CDN: el layout y el ruteo de aristas se escriben dentro del archivo. |

✅ **ELEGIDO POR VALLE EL 2026-08-22: gana la V2** (tronco unico y despues la horqueta). Se
ejecuto el protocolo que estaba escrito acá: el que pierde se fue a `Archivos_Borrar/` y el que
gana quedo como **`MAPA-MODELO.html`**, asi que todas las referencias del repo siguen valiendo sin
tocar nada. El descartado esta en `Archivos_Borrar/BORRAR_MAPA-MODELO-v1-descartado.html`.

⚠️ **Y se saco la v1 del MODELO de adentro del mapa**, que es cosa distinta del archivo: la leyenda
mostraba **dos formulaciones** cuando desde el ADR-0012 hay una sola. Fuera los nodos `n_v1` y
`c_p_llega`, fuera el camino "El numero que corre hoy (v1)" del selector, y re-cableado lo que
colgaba de ellos: el arco de condicionamiento hacia la revisora ahora sale del **paso B**, y el
embudo conserva su unico rol vivo (`p_sancion` -> la baseline). El mapa queda en **101 nodos y 144
aristas**. Ojo con la confusion de nombres, que ya mordio: **"v1" significa DOS cosas** en este repo
—la formulacion del modelo y el dibujo del mapa— y no se dieron de baja por el mismo motivo.

**TAREA NUEVA IDENTIFICADA — `datos/expedientes`: ingestar los firmantes del dictamen (20-08-2026).**
Nuestra base sabe que hay dictamen (23.891 filas / 19.702 proyectos, 2008-2026) pero **no quien lo firmo**, y no es culpa del loader: el dataset `dictamenes` de CKAN no lo publica. El dato esta en el PDF de la Orden del Dia, y el enganche ya existe (`od_numero` + `od_publicacion` en `expedientes_resultados.parquet`): **18.067 OD unicas que cubren 18.787 proyectos**. Es prerrequisito de la Puerta A como senal. Plan completo en `coordinacion/PROMPT-3-Formulacion-unica-y-nombres.md`. **Modulo LIBRE, candidato al proximo claim.** Ojo: las OD son de Diputados; el Senado necesita otra fuente.

**Pendiente de Valle (no lo puedo correr yo):** `python -m pytest tests/ datos/proyectos/tests -q`
en PowerShell (en el sandbox no hay pytest) y `git check-ignore -q` sobre los archivos tocados
antes de commitear. El generador quedo idempotente (dos corridas seguidas, mismo `.js`) y el
HTML se verifico abriendolo desde `file://` con la red cortada: dibuja, sin errores de consola
y sin un solo pedido de red.

**Regla de estado, decidida el 2026-08-20 (Valle):** las Puertas A y C quedan
**REPLANTEADO + suspendidas** — no se modela comision ni caducidad, por ser de
naturaleza estrictamente politica y no predecible estadisticamente. Como eso
contradice el `**Estado:** EN CURSO` del README de `modelo/ensemble` —que el
generador declaraba como su unica fuente—, el estado de un nodo ahora **puede
declararse por nodo** en la capa curada, con motivo obligatorio, y el mapa dice
en la ficha de donde salio cada estado. El estado de una puerta NO es el de su
modulo, y ahora esta escrito.

**URGENTE leido al empezar (regla de la casa).** `coordinacion/URGENTE.md` tiene
vivo el punto 1 (validar 15 filas MEDIA del roster de jefes de bloque). **Se
posterga explicitamente y se deja dicho por que:** es de `variables/proyecto`, no
de `producto/dashboard`; no bloquea ni ensucia este trabajo; y su prioridad ya
fue rebajada el 31-07 al medirse que `lider_jefe_bloque` aporta 1,25x y no 7x.
Queda en URGENTE sin tocar.

## Sesion 2026-08-20 (Franco+Claude) — CERRADA, MAPA-MODELO.html: el mapa de la maquinaria del calculo

| Modulo | Quien | Desde | Que se esta haciendo |
|---|---|---|---|
| **producto/dashboard** | Claude (con Franco) | 2026-08-20 | **HECHO, modulo LIBRE.** `MAPA-MODELO.html` (raiz, doble clic): grafo navegable de como se calcula P(sancion) — fuente oficial → script → base → variable → P(llega al recinto) → P(mayoria en origen) → Puerta D (revisora) → P(sancion). Muestra las **DOS formulaciones vivas**: v1 en produccion (`ensemble.py`: P(llega) × P(mayoria)) y el reencuadre por puertas A·B·C·D (`PUERTA-D.md`), con A y C parqueadas y dibujadas como parqueadas. Dos capas, como el resto del repo: `producto/dashboard/src/generar_mapa_modelo.py` lee `.mapa/mapa.json` + `rutas.py` + el `Estado:`/`Owner actual:` de cada README, lo fusiona con la capa curada a mano `producto/dashboard/data/mapa_modelo_semantica.json` y escribe `mapa_modelo_datos.js`. El HTML es diseno fijo y NO se edita a mano, mismo patron que `TABLERO-CONTROL.html` + `tablero_datos.js`. Es el **primer codigo propio del modulo**: hasta hoy sus entregables vivian sueltos en la raiz. |

**Entregado:** `MAPA-MODELO.html` + `mapa_modelo_datos.js` (raiz) + `producto/dashboard/src/generar_mapa_modelo.py` + `producto/dashboard/data/mapa_modelo_semantica.json`. 96 nodos / 130 aristas; la corrida deja **1 aviso**, que es un hallazgo real y ajeno a este modulo: `docs/taxonomias/README.md` no tiene la linea `**Estado:**` (la usa este mapa y tambien el router de `MAPA.md`). **No se toco**, por la regla un-modulo-un-dueno: lo arregla quien reclame `docs/taxonomias`.

**Pendiente de Valle o Franco (no lo puedo hacer yo):** `git check-ignore -q` sobre los cuatro archivos nuevos antes de commitear — la raiz git esta un nivel arriba del mount y desde el sandbox no corre git —, y `python .mapa/indexar.py .` + `python .mapa/indexar.py . --sellar-todo` para reindexar y sellar.

**URGENTE leido al empezar (regla de la casa).** `coordinacion/URGENTE.md` tiene vivo el punto 1 (validar 15 filas MEDIA del roster de jefes de bloque). **Se posterga explicitamente y se deja dicho por que:** es de `variables/proyecto`, no de `producto/dashboard`; no bloquea ni ensucia este trabajo; y su prioridad ya fue rebajada el 31-07 al medirse que `lider_jefe_bloque` aporta 1,25x y no 7x. Queda en URGENTE sin tocar.

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
