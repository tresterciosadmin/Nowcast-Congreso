# Prompt — una sola formulación (puertas), el dictamen como señal, y nombres que se entiendan

> Para pegar en un chat nuevo. Guardado en `coordinacion/` para no reescribirlo.
> Escrito el 2026-08-20. Lo marcado **[verificado 20-08]** salió del disco o de la
> fuente en esa sesión: no hace falta re-descubrirlo, pero **sí hay que
> re-verificarlo antes de actuar sobre ello** (el repo cambia sin aviso: el bot
> commitea solo y Franco trabaja en paralelo).

---

Trabajás sobre el repo **Nowcast Congreso** (`Nowcast Congreso Argy/`, la raíz git
está un nivel arriba). Aplicá la metodología del repo: leé `coordinacion/URGENTE.md`
primero, después `MAPA.md` en la raíz, y el `README.md` de cada módulo que toques.
Usá `.mapa/buscar.py` para ubicar código en vez de escanear el repo. Reclamá el
módulo en `coordinacion/TABLERO.md` antes de escribir.

**El disco manda sobre las bitácoras, y también sobre lo que vos mismo imprimís.**
Si imprimís un fragmento recortado para inspeccionarlo, no leas el recorte como si
fuera el archivo (el 20-08 diagnostiqué una frase truncada que no existía: la había
cortado mi propio `[:80]`).

---

## El rumbo, en una frase

Quiero **una sola formulación —la de puertas—**, quiero que la **Puerta A deje de
ser una probabilidad de que la comisión actúe** (eso es política y no se predice) y
pase a ser **el carácter del trabajo en comisión** (quién firmó el dictamen, si hubo
disidencias, si son figuras de peso), y quiero que **las puertas se llamen por lo que
son** y no por una letra.

Hay un problema de datos en el medio y es lo primero.

---

## Tarea 0 (prerrequisito) — faltan los firmantes del dictamen, **en las dos cámaras**

**El dato existe en la fuente y no está en nuestra base. Hay que corregirlo.**

**Antes que nada, el circuito real** (y si no lo tenés claro, frená y leelo — hay una
skill pendiente sobre esto en `PLAN-DE-TRABAJO.md`):

    presentación → giro a comisión(es) de la CÁMARA DE ORIGEN → DICTAMEN de comisión
    → pleno de origen → MEDIA SANCIÓN
    → giro a las comisiones de la CÁMARA REVISORA → NUEVOS DICTÁMENES
    → pleno de la revisora → SANCIÓN

**Los dictámenes existen en las DOS cámaras.** No son un evento de la cámara de origen.
Un proyecto que consigue media sanción vuelve a pasar por comisiones —las de la otra
cámara— y produce dictámenes nuevos, con otros firmantes y otras disidencias. Ese es el
insumo de la **Puerta C**, igual que los de origen lo son de la **Puerta A**.

**El trabajo central de esta tarea es vincular un mismo proyecto de ley con los
dictámenes que produce en los dos sistemas de comisiones, el de Diputados y el del
Senado.** El puente entre cámaras ya existe y está validado:
`datos/expedientes/src/enlace_senado.py` y la columna `exp_senado` — el mismo mecanismo
con el que se pasó de 39 a 223 proyectos con votación en las dos cámaras. Reusalo, no
lo reimplementes.

**[verificado 20-08] Lo que hay hoy.** `datos/expedientes/data/clean/expedientes_dictamenes.parquet`:
23.891 filas, **19.702 proyectos con dictamen**, del **2008-03-25 al 2026-08-05**,
columnas `proyecto_id, giro, orden, tipo, observaciones, numero, fecha, expedientes`.
**Ningún firmante.** Y no es que nuestro loader los tire: el CSV crudo de CKAN
cacheado en `datos/Archivos_Borrar/expedientes_ckan/dictamenes.csv` tiene esas mismas
8 columnas. **El dataset `dictamenes` de CKAN no publica los firmantes.** La
limitación ya estaba escrita en `datos/expedientes/src/ingesta_ckan.py`: *«`autor` es
solo el firmante PRIMARIO (el CKAN no publica cofirmantes)»*.

**[verificado 20-08] Dónde sí está: en el PDF de la Orden del Día.** Abrí uno
(`https://www3.hcdn.gob.ar/dependencias/dcomisiones/periodo-143/143-4.pdf`) y trae
exactamente lo que buscamos: la lista completa de firmantes del **dictamen de
mayoría** (~45 diputados, con el primer firmante identificado), los que firman **«en
disidencia parcial»** con nombre y bloque, y las secciones *«FUNDAMENTOS DE LA
DISIDENCIA DEL/LA SEÑOR/A DIPUTADO/A …»* con el bloque de cada uno.

**[verificado 20-08] Y el enganche ya lo tenemos.**
`expedientes_resultados.parquet` trae `od_numero` y `od_publicacion`:
**18.067 Órdenes del Día únicas** que cubren **18.787 proyectos**, de 2008 a 2026
(entre 500 y 1.200 por año en la ventana reciente). El patrón de URL es regular:
`wwwN.hcdn.gob.ar/dependencias/dcomisiones/periodo-<NNN>/<NNN>-<OD>.pdf`.

**Lo que quiero que hagas en esta tarea:**

1. Resolver el mapeo `od_publicacion` → **período parlamentario** (el `<NNN>` de la
   URL), y confirmar el host: los ejemplos que vi alternan `www3` y `www4` según el
   período, así que **no lo hardcodees sin verificarlo período por período**. Ojo
   también con el cero a la izquierda del número de OD (`"0356"`, `"1641"`).
2. Una ingesta nueva con **caché en disco** (18k PDFs es un backfill de una sola vez;
   después son ~600-1.000 por año). Régimen de descartables para el crudo.
3. Un parser que saque, por OD y por expediente: **firmantes del dictamen de mayoría**
   (y de minoría si lo hay), **quién firmó en disidencia** (parcial o total) y el
   **bloque** de cada uno. Que falle ruidoso, no en silencio: si el parseo no
   reconoce la estructura de un PDF, ese OD queda marcado, no descartado sin más.
4. **Contrato de salida nuevo**, documentado en el README del módulo: es una salida
   nueva, así que decidí en el mismo commit si entra al régimen transitorio del
   `.gitignore` y verificalo con `git check-ignore -q`.
5. **El Senado necesita su propia fuente, y no es opcional.** Las Órdenes del Día son
   de Diputados; los dictámenes del Senado se publican por su propia vía (DAE / sitio
   del Senado). Sin eso, la Puerta C se queda sin insumo y el circuito bicameral queda
   cojo. Decime qué encontrás antes de prometer cobertura.
6. **La salida tiene que estar indexada por (proyecto, cámara, comisión, dictamen)**,
   no por proyecto solo: un mismo expediente puede tener dictamen en Diputados y otro
   en el Senado, y hasta varios en cada una.

**[verificado 20-08] El embudo real de los proyectos de LEY (41.470, 2008-2026):**

| | proyectos | sobre los presentados |
|---|---|---|
| presentados | 41.470 | — |
| con dictamen | 3.237 | **7,8%** |
| llegaron al pleno | 1.767 | **4,3%** |

Y el dato que le da sentido a la Puerta A: **de los que consiguen dictamen, el 54,6%
llega al pleno.** Tener dictamen multiplica por ~13 la chance de llegar a votarse
(4,3% → 54,6%). O sea que **el hecho observado del dictamen ya carga casi toda la
información**; el carácter (quién firmó, disidencias) es el refinamiento arriba de eso.

⚠️ **Esta tabla NO es un argumento para volver a modelar la mortandad en comisión.**
Que un proyecto se muera en el cajón **no nos interesa** y no se predice: es la decisión
de fondo y no está en discusión. La tabla mide otra cosa —cuánta información carga el
**hecho observado** del dictamen— y es justamente lo que hace que A rinda sin predecir
nada. Si te encontrás estimando «P(sale de comisión)», te fuiste del rumbo.

**Cuidado con la ilusión del hueco de datos.** Se puede pensar que la cobertura baja es
un problema de registro. No lo es: se comprobó que **de 1.767 proyectos de ley con
resultado en el pleno, 1.766 ya tienen dictamen registrado** — sólo 1 no. Como todo
proyecto aprobado en el pleno pasó necesariamente por comisión, esa comprobación
falsifica la hipótesis del hueco: **el 7,8% es mortandad real, no datos faltantes.**
La única franja donde «sin registro» todavía puede significar «no publicado aún» es el
borde de la ventana viva, porque la mediana entre presentación y Orden del Día es de
**224 días** (66,6% dentro del año, 94,3% a los dos años).

**Trampa a evitar:** `comisiones_integrantes.parquet` (`COMISION_ID, DIPUTADO_NOMBRE,
DISTRITO`) es una **foto sin fechas**, la composición actual de cada comisión. Si la
usás para construir una señal histórica —«¿el autor integraba la comisión giradora?»—
metés fuga del futuro en el backtest. Si hace falta composición de comisiones
point-in-time, es otro dato y hay que ir a buscarlo.

---

## Tarea 1 — Una sola formulación: matar V1, quedarnos con puertas

Hoy conviven dos y el mapa las muestra a las dos a propósito:

- **V1, en producción:** `P(aprobación) = P(llega al recinto) × P(mayoría | recinto)`,
  en `modelo/ensemble/src/ensemble.py`.
- **Puertas:** `P(sanción) = P(A)·P(B|A)·P(C|A,B)·P(D|A,B,C)`, contrato en
  `modelo/ensemble/PUERTA-D.md`.

**[verificado 20-08]** Lo que dice `PUERTA-D.md`:

| Puerta | Qué es | Cómo se trata hoy |
|---|---|---|
| A | agenda origen (¿sale de comisión?) | se **observa el dictamen (firmas, bloques)**. Parqueada |
| B | voto origen (¿mayoría?) | agregador — ya existe |
| C | agenda revisora (¿la tratan antes de caducar?) | observada + reloj Ley 13.640. Parqueada |
| D | voto revisora | `src/puerta_d.py`, hoy con `delta = 0` |

Fijate que **A ya estaba definida como «observar el dictamen (firmas, bloques)»**.
Esta tarea no inventa una puerta nueva: desparquea la que ya estaba escrita, ahora
que la Tarea 0 le consigue los datos.

### Las decisiones ya tomadas (no las re-discutas, implementalas)

1. **Lo que mide «chances de tratamiento» SE VA.** `p_llega_recinto` del embudo
   —«¿llega a votarse?», porcentaje de aprobación en X días y compañía— es
   exactamente lo que decidimos no modelar. Deja de ser un factor del número.
2. **`p_sancion` NO SE TOCA y NO ENTRA a la cadena.** Es una logística aparte sobre
   «¿termina siendo ley?», entrenada de punta a punta: **ya contiene A, B, C y D
   adentro**. Meterla como factor haría que la cadena se multiplique por sí misma.
   Su lugar es el que ya tiene: **la baseline**. `modelo/ensemble/src/backtest_cadena.py`
   lo dice en su encabezado —*«¿la cadena aporta sobre el `p_sancion` que el embudo ya
   calcula solo?»*— y la usa como `baseline_embudo_p_sancion`. **Es la única vara que
   sobrevive a la muerte de V1: cuidala.**
3. **Todo lo que haga falta para mantener la validez del sistema se mantiene o se
   readapta a puertas.** El backtest no se apaga: se re-apunta a la cadena nueva.
4. **El carácter del dictamen no multiplica: condiciona.** Que un dictamen sea de
   mayoría, firmado por dos comisiones y sin disidencias no cambia la chance de que
   lo traten — cambia **cómo van a votar los bloques cuando lo traten**. Su lugar
   natural es como condicionante de **B** (y de **D**), en la misma familia que
   `variables/bloque.proyectar_postura(tema=, origen=)`, que ya condiciona la
   dirección del voto por tema y por origen. **A queda observada y colapsa a 1**
   cuando hay dictamen, que es la regla que ya está escrita.

### Lo que quiero que verifiques antes de escribir código

1. **¿Qué depende de V1 hoy?** Listalo con archivo y línea. Puntos de partida
   **[verificado 20-08]**: `componer(p_llega, p_mayoria)`, `nowcast_proyecto`,
   `nowcast_auto(proyecto_id, fecha, camara, tipo_mayoria)`, `_p_llega_de_embudo`,
   `imprimir_tarjeta` y el `main` de la CLI, todos en `modelo/ensemble/src/ensemble.py`.
   Y quién los llama: `modelo/ensemble/src/backtest_cadena.py` y los generadores de
   `casos/`.
2. **¿Hay algo que V1 hace y las puertas no?** Concretamente: el piso y techo de
   `P(mayoría)` en `[1%, 99%]` (ninguna votación es un lock), la escalera del roster
   nominal (`tasa_desvio_reciente` → `tasa_desvio` global → promedio del bloque) y la
   regla del colapso. ¿Cada una está en el camino de puertas, o se perdería?
3. **¿B y `P(mayoría | recinto)` son la misma cuenta?** Si lo son, mostralo (mismo
   `simular_votacion`, mismo roster). Si difieren, ese diff es el trabajo real.
4. **Doble conteo.** Si A vuelve a aportar información y el factor empírico de la
   revisora nació para capturar attrition en agregado, revisá que la misma mortandad
   no quede contada dos veces.
5. **[verificado 20-08, hallazgo abierto]** Al de-duplicar el mapa quedó a la vista
   que **la rama de la cámara revisora no consume el embudo ni asistencia/quórum**:
   hoy `embudo.py`, `ficha.py` y `asistencia.py` alimentan sólo el número de origen.
   ¿Correcto o hueco?

### El costo que hay que decir en pantalla

«La mortandad en el cajón» es esto: de cada proyecto de ley presentado, la enorme
mayoría no se rechaza — **se muere sin que nadie lo trate**, nunca sale de comisión y a
los dos años caduca por la Ley 13.640. Hoy `p_llega_recinto` le pone número a ese riesgo
y es lo que arrastra hacia abajo la probabilidad de un proyecto recién presentado.

Si sale y A queda observada, para un proyecto **sin dictamen** el modelo ya no puede
decir «tiene 4% de ser ley porque el 96% muere en el cajón»: sólo puede decir **«si
llega a votarse, gana con X%»**. **[verificado 20-08]** Con 3.237 de 41.470 proyectos de
ley con dictamen, eso alcanza al **92% de los proyectos**. El número publicado pasa a ser
**condicional** y eso tiene que estar dicho en la interfaz, no en un README.

**Ojo con la ventana viva:** la cobertura reciente es la más flaca (2023: 4,5% · 2024:
3,6% · 2025: 1,5% · 2026: 0,8% de los presentados ese año), en parte por inmadurez y en
parte porque la actividad de comisiones cayó: Órdenes del Día publicadas por año para
proyectos de ley, 268 en 2015 → 106 en 2024 → 52 en 2025. Para el **estado** («¿hay
dictamen?») no hace falta esperar a CKAN: `datos/seguimiento/src/giros.py` ya devuelve
`con_dictamen` leyendo la ficha oficial del expediente. Lo que hereda la demora de
publicación es el **carácter** (firmas y disidencias), que sólo vive en el PDF.

Por eso **la Puerta A tiene tres estados, no dos**: (1) con dictamen y carácter conocido,
(2) sin dictamen, (3) **sin dato** — el dictamen puede existir y nosotros no saberlo. El
tercero no puede colapsar al segundo: son opuestos.

### «Sin dato» es un estado de conocimiento, no un rango de fechas

El tercer estado tiene **dos causas distintas y el mismo tratamiento**:

1. **Por recencia:** la Orden del Día está firmada pero HCDN todavía no la publicó
   (mediana de 224 días entre presentación y OD).
2. **Por cobertura:** el dictamen es de una comisión de la **cámara revisora** y el
   empalme con el otro sistema todavía no está resuelto. Es previsible que la Puerta C
   pase un buen tiempo así.

**Regla de diseño, y es la que evita tener que deshacer lo hecho:** cuando una puerta
está en «sin dato», **no se anula nada ni se frena la cadena** — el condicionante del
dictamen **se encoge a 0** y queda la estimación no condicionada, que es exactamente lo
que el sistema calcula hoy. El repo ya tiene ese patrón escrito y probado en
`PUERTA-D.md`: *«El fallback NO es un `if`. Cuando la muestra para `delta` es
insuficiente, el encogimiento lo lleva a 0 y queda `p0` puro… Manera 1 es el límite de
Manera 2. Un solo modelo.»* **Usá el mismo mecanismo, no inventes otro.**

La contrapartida es de honestidad, y va en la interfaz: el número tiene que decir **con
qué se calculó** — qué puertas se observaron de verdad y cuáles corrieron sin dato. Un
proyecto con dictamen leído en las dos cámaras y otro sin ningún dictamen enganchado no
pueden mostrarse igual sólo porque los dos devuelven un número.

### Cómo se ejecuta la baja

No se borra V1 y después se ve qué pasa: **primero el reemplazo funcionando y medido,
después la baja**, y la baja con el régimen de `Archivos_Borrar/` (copiar +
**neutralizar el original** + anotar en `PENDIENTES-DE-BORRAR.md`). Cambiar la
formulación de producción **exige un ADR** en `coordinacion/DECISIONES/` y aviso en
el TABLERO: le cambia el contrato a todos los que consumen el número. La Puerta A
como señal observada, y no como probabilidad, es una **enmienda** al ADR que la
parqueó — se agrega arriba, el cuerpo original queda como registro.

---

## Tarea 2 — Que las puertas se entiendan sin decodificarlas

«Puerta A/B/C/D» no dice nada a primera vista. Quiero que cada paso se llame por **lo
que es**, y que la letra quede como código corto para donde el espacio no da (nodos
del mapa, columnas, ids).

- **Traeme una propuesta de nombres derivada de `PUERTA-D.md`**, no inventada. Del
  tipo «Tratamiento en origen / Votación en origen / Tratamiento en la revisora /
  Votación en la revisora», pero proponé la que te parezca mejor y por qué.
- **Que el nombre haga visible la asimetría que la letra esconde:** A y C se
  **observan** (son hechos o estados del expediente), B y D se **calculan** (son
  probabilidades). Llamarlas a las cuatro «puerta» las iguala, y no son lo mismo.
- **Jerarquía:** el nombre largo manda; la letra va entre paréntesis o como badge.
- **NOMBRE no es ID.** Cambiar cómo se muestra es barato. Cambiar los ids (`g_A`…`g_D`
  en la capa curada del mapa, y lo que haya en código o columnas) es **cambio de
  contrato**: si hace falta, ADR y aviso; si no hace falta, no lo toques.
- **Dónde impacta [verificado 20-08]:** `modelo/ensemble/PUERTA-D.md`,
  `producto/dashboard/data/mapa_modelo_semantica.json` (la prosa curada),
  `producto/dashboard/src/generar_mapa_modelo.py` (que escribe `mapa_modelo_datos.js`)
  y los dos HTML del mapa. **No edites `mapa_modelo_datos.js` a mano: es generado.**

---

## Estado del mapa, para que no te pierdas [verificado 20-08]

Hay **dos archivos de mapa vivos y falta que yo elija uno** (está en `TABLERO.md`):
`MAPA-MODELO.html` (bloques de cámara lado a lado, tronco duplicado) y
`MAPA-MODELO-V2.html` (**tronco único y después la horqueta**: el pipeline se dibuja
una vez y recién ahí se abre en dos ramas cortas que caen juntas en P(sanción); 96
nodos dibujados contra 153). Los dos leen el mismo `mapa_modelo_datos.js`: **son sólo
diseño**, así que tu cambio impacta en los dos por igual.

Cuidado con una confusión de nombres: **«V1» quiere decir dos cosas** en este repo.
La formulación V1 del modelo (Tarea 1) y la V1 del dibujo del mapa. No son lo mismo y
no se dan de baja juntas.

---

## Vocabulario (leelo antes de escribir en las bitácoras)

**«Bicameral» no quiere decir «votado en las dos cámaras».** Las **comisiones
bicamerales** son otra cosa: tratan asuntos que requieren a las dos cámaras juntas, como
el control de decretos del Ejecutivo. Cuando `PUERTA-D.md` habla de *«los ~243 proyectos
con votación en las dos cámaras (60 desde 2015)»* se refiere a eso y no a comisiones
bicamerales. Hay una **skill de funcionamiento parlamentario argentino pendiente** en
`coordinacion/PLAN-DE-TRABAJO.md` justamente porque una palabra mal usada en una
conversación de diseño termina siendo un supuesto mal puesto en el modelo.

## Reglas de la casa

- **Las 4 bitácoras se mueven juntas** en el mismo cambio: `ESTADO-DEL-PROYECTO.md`,
  `EN-HUMANO.md`, `TABLERO.md` y `tablero_datos.js`.
- **`MAPA.md` y `.mapa/` son generados**: no los edites a mano. Si cambia lo que hace
  un módulo, actualizá el `**Resumen:**` y el `## Buscar acá si` de su README.
- **No edites `TABLERO-CONTROL.html`** (es diseño; lee `tablero_datos.js`).
- **Lo temporal y los scripts de un solo uso** van a `Archivos_Borrar/`, neutralizados.
- **En mi máquina no hay `bash`.** Todo comando que me pases va en **PowerShell**;
  todo script que ejecute git, en **sh POSIX con `#!/bin/sh`**.
- **Prefijá `GIT_OPTIONAL_LOCKS=0` a todo comando git**, o me trabás el git.
- **Las corridas largas van a PowerShell** (la ingesta de 18k PDFs es una de ellas):
  pasame el comando listo y qué tiene que dar.
- **«Pasa en el sandbox» no es «pasa».** Otra versión de pandas que la mía: un
  faltante llega como `None`, `float('nan')` **o** `pd.NA`. Guardas con `pd.isna()`,
  `str()` antes de `.split()`, y tests sobre los dos backends de dtype.

## Cómo se prueba

1. `python -m pytest tests/ datos/proyectos/tests -q` — la vara de hoy
   **[verificado 20-08]: 20 passed, 1 xfailed.** El `xfailed` es conocido y está
   documentado en `tests/README.md` (`periodo_parlamentario` con backend `pyarrow`).
   **Si aparece un segundo `xfail` o un `failed`, lo trajiste vos.**
2. Si cambia la formulación, tiene que haber un test **nuevo** que **falle con el
   código viejo**.
3. El parser de la OD se prueba contra PDFs reales guardados como fixture, incluyendo
   **al menos uno con disidencias** y uno con dictamen de mayoría y de minoría.
4. Si tocás el mapa: `python producto/dashboard/src/generar_mapa_modelo.py` dos veces
   seguidas no debe producir diff en la segunda, y el HTML tiene que dibujar con
   **doble clic, sin servidor y sin internet**.
5. **La prueba de que la Tarea 2 salió bien:** que alguien que no conoce el proyecto
   mire el mapa y diga qué pasa en cada paso sin que se lo expliquen.

---

**Empezá por la Tarea 0. Antes de escribir código, decime qué encontraste sobre el
mapeo período/URL y el estado del Senado, contame el plan, y esperá que confirme.**
