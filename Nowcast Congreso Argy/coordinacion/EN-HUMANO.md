# EN HUMANO — el sistema explicado sin tecnicismos

> Documento vivo. Cada cambio importante en el proyecto se explica acá en lenguaje claro, además de registrarse en `ESTADO-DEL-PROYECTO.md`. Si algo del sistema no se entiende leyendo esto, está mal escrito y hay que arreglarlo.

## Se subieron sin querer las marcas que git deja cuando no sabe unir dos versiones (25-08-2026)

Valle intentó traerse los cambios del repositorio y GitHub Desktop la frenó: dos archivos del padrón estaban modificados en su computadora **y** en el servidor. Eligió la opción de guardar sus cambios y seguir, y ahí pasó lo que no se ve: git no supo unir las dos versiones y **escribió adentro de los archivos sus propias marcas de conflicto** —unas líneas con `<<<<<<<` y `>>>>>>>`—, y eso se subió tal cual.

**Por qué no es un detalle.** Uno de esos dos archivos es la memoria del vigilante del padrón: lo que le permite comparar la foto de hoy contra la de la semana pasada y decir si algo cambió. Con esas marcas adentro dejó de ser un archivo legible. Y el programa **no avisa**: está escrito para que, si no puede leer su memoria, siga como si fuera la primera vez que corre. O sea que el lunes que viene habría vuelto a reportar como novedad cosas ya reportadas, y —peor— habría perdido el dato de **hace cuántos días el padrón del Senado no cambia**, que hoy son 18. Ese contador es justamente el que enciende la alarma de "este dato está viejo". Se habría puesto en cero y la alarma no habría sonado.

Restauramos los dos archivos desde la versión que había dejado el robot el lunes, que era la más nueva. No se perdió nada: las dos versiones decían exactamente lo mismo sobre la composición de las cámaras; sólo cambiaba la fecha de la última corrida.

**Y esto va a volver a pasar todos los lunes** mientras esos dos archivos tengan dos autores: el robot que corre en la nube y la computadora de casa. Quedó anotado como urgente. La solución no es sacarlos del control de versiones —el robot los necesita ahí para comparar— sino al revés: que correr el programa localmente **no pueda** tocar la copia oficial.

## El mapa perdió las puntas de flecha y ganó que se pueda acomodar a mano (25-08-2026)

Dos cosas que pidió Valle mirando el dibujo.

**Las flechitas.** Alrededor de algunos nodos aparecían varias puntas de flecha apiladas, sueltas, sin llegar a tocar nada. El motivo: la punta se dibujaba en el borde de la **caja invisible** que rodea a cada nodo, no en el borde del **óvalo** que se ve. En un óvalo esas dos cosas no coinciden —la caja es un rectángulo, el óvalo es una curva—, así que la punta quedaba flotando en el hueco entre las dos. Y cuando varias líneas entran al mismo nodo, cada una por su carril, quedaban todas apiladas ahí.

Valle eligió **sacarlas de todo el diagrama** en vez de reacomodarlas, y tiene sentido: el dibujo se lee de izquierda a derecha por columnas, así que la dirección ya la dice el lugar de cada cosa. Quedan sólo las líneas, más limpias. Dejamos escrito en el código cómo volver atrás por si alguna vez se quieren.

**Y ahora se pueden mover los nodos.** Arrastrás un óvalo con el mouse y las líneas, los recuadros y las bandas lo siguen. **No se guarda nada, a propósito:** al recargar vuelve el orden automático, y eso mismo funciona como "deshacer". Sirve para desenredar una zona apretada, sacar una captura y pedir el arreglo. Si algún día quisiéramos que las posiciones quedaran fijas, no irían en el archivo del dibujo sino en el de datos, que es donde el repo guarda todo lo que se decide a mano.

Un detalle que vale contar porque es el tema de toda la sesión: para que los recuadros siguieran a los nodos hubo que separar en dos el cálculo del armado. Antes, "dónde va cada nodo" y "de qué tamaño es el recuadro que los envuelve" se calculaban juntos, así que mover un nodo obligaba a recalcular todo — y eso devolvía el nodo a su lugar original. Ahora el encuadre es su propia cuenta, y la usan los dos: el armado inicial y el arrastre. **Una cuenta, dos usuarios.**

## El mapa dibujaba una flecha con la fórmula de otra (25-08-2026)

Valle vio algo raro en `MAPA-MODELO.html` y tenía razón: entre "Puerta A" y "P(mayoría en origen)" había **un pinche turquesa asomando sobre el nodo**, y un texto a medias tapado por los círculos.

En el mapa hay **dos flechas de "condicionamiento"**, que son cosas distintas: una cruza de una cámara a la otra —la gruesa que baja hasta el Senado— y la otra se queda dentro de la misma cámara, para decir que el carácter del dictamen condiciona la votación. **Las dos se dibujaban con la misma función**, y esa función estaba escrita sólo para la primera: buscaba el recuadro de la cámara de destino y bajaba hacia él. Como la segunda no cruza a ningún lado y sus dos nodos están uno al lado del otro, la flecha salía apuntando hacia atrás y hacia arriba, y se aplastaba hasta desaparecer. El texto, calculado con la misma fórmula, caía justo encima de los nodos.

Ahora la función distingue los dos casos: si no hay adónde bajar, dibuja un **puente corto por arriba** de los dos nodos. Y la etiqueta dejó de calcularse dos veces —una en cada lado del código— para calcularse en un solo lugar; que es, otra vez, el mismo problema del que veníamos hablando toda la sesión, esta vez en el dibujo en lugar del cálculo.

**Lo verifiqué abriéndolo**, no leyendo el código: abrí el archivo en un navegador sin pantalla, medí la flecha y miré la imagen. Cero errores.

**Y quedó algo anotado que no toqué porque lo tenés que decidir vos:** en los datos del mapa, la relación A→B está marcada como "condiciona" y la C→D como "calcula", cuando según la formulación son la misma cosa espejada. El mapa está diciendo dos cosas distintas sobre la misma relación.

## Fuimos a buscar lo que estaba escrito dos veces — y encontramos un tercer cálculo vivo (25-08-2026)

La sesión pasada se fue entera en un problema que nadie había buscado: convivían **dos** formas de sacar el número. Esta vez la pregunta fue al revés: *¿qué más está escrito dos veces en este repo y todavía no lo sabemos?*

**No leímos el repo entero para averiguarlo.** Se usó el índice del proyecto más un programa corto que lee cada función, le saca los comentarios y le calcula una huella. Dos funciones con la misma huella son la misma función copiada, aunque estén en carpetas distintas y tengan nombres distintos. De 141 archivos salieron **10 grupos de código idéntico** y **32 nombres repetidos**. La mayor parte era ruido: en cualquier programa hay veinte funciones que se llaman `main` y no tienen nada que ver entre sí. Lo que quedó después de mirar una por una fueron tres cosas.

**Una: la definición de "período parlamentario" estaba copiada en cuatro lugares.** Tres eran idénticas letra por letra; la cuarta hacía la misma cuenta escrita distinto. Cada copia llevaba un comentario que pedía *"mantener sincronizadas"* — o sea, el único control era que alguien se acordara.

Lo interesante es que **eso ya se sabía y ya había un control automático**. El 20 de agosto se había escrito una prueba que revisa que las cuatro copias digan lo mismo. Y esa prueba estaba avisando de un problema **que nadie podía arreglar**: las cuatro copias fallan cuando el dato llega en cierto formato, el arreglo es **una línea en cada una**, y llevaba un mes trabado. El motivo estaba escrito ahí mismo: *"toca 4 módulos con dueño"*, y la regla de la casa es que cada módulo lo trabaja una sola persona a la vez.

Ese es el punto y por eso se decidió unificar: **con las copias, un arreglo de una línea costaba pedirle permiso a cuatro dueños.** El control veía el problema y la organización del trabajo impedía repararlo. Ahora la definición vive en un solo archivo, `definiciones.py`, hermano del que ya decía *dónde* está cada cosa: este dice *qué es* cada cosa. Y el arreglo de la línea, hecho.

**Nada cambió de resultado.** Se probó la definición nueva contra las cuatro viejas sobre las fechas donde una diferencia se vería primero —los tres días alrededor del recambio del 10 de diciembre— y da exactamente lo mismo. Lo único que cambia es que ahora también funciona en el formato donde antes fallaba.

**Dos: había un tercer cálculo del número, vivo.** Un archivo que arma una proyección hipotética por las dos cámaras seguía usando mecanismo propio, y tenía **dos de los siete errores que se habían corregido la semana pasada**: pedía la mitad más uno de *todas las bancas* para aprobar (129), cuando la mayoría simple se mide sobre los que efectivamente votan (122); y volvía a tratar el acompañamiento del bloque como un sí o un no, que fue justamente lo que hacía que todo diera 99%.

Y hay un detalle que vale más que el hallazgo: **ese archivo fue tocado el 22 de agosto**, para corregirle otra cosa, con un comentario que decía *"una copia es una divergencia esperando"*. Se arregló esa copia y no se miraron las otras dos que estaban tres líneas más abajo. Es exactamente el mecanismo que esta tarea vino a buscar, atrapado en el acto. El archivo quedó desactivado: si alguien lo corre ahora, avisa por qué no puede correr en vez de escupir un número que alguien iba a citar.

**Tres: dos archivos con el mismo nombre y adentro cosas distintas.** En una carpeta de material de terceros había una copia suelta de una base histórica de votaciones con **exactamente los mismos nombres de archivo** que la versión comprimida que el sistema sí usa — pero con el doble de datos y llegando ocho años más atrás. El programa toma la comprimida, sin decir nada. Es el mismo mecanismo que ya está anotado como urgente para el padrón de diputados, donde correr un comando sin argumentos borra dieciocho años de historia sin dar error. Valle decidió que ese material extra no interesa y hace ruido, así que la copia suelta se fue a la carpeta de descarte. (La comprimida, que sí se usa, no se tocó.)

**Lo que decidimos NO tocar, y por qué importa decirlo.** Hay cuatro funciones en el repo que convierten fechas y se llaman igual. Podría parecer lo mismo copiado cuatro veces, pero no: cada una lee un formato distinto —una lee "14 DE MARZO DE 2026", otra "14/03/2026"— y juntarlas sería peor que dejarlas. **Emprolijar no es el objetivo; que dos cosas no puedan desacomodarse en silencio, sí.** Lo que sí quedó anotado es que tres de las cuatro no verifican que la fecha exista: un "31 de febrero" pasa sin protestar.

**Y una prueba nueva que merece explicación.** Las pruebas que ya había comparaban **resultados**: pasaban igual con una definición o con cinco, mientras las cinco coincidieran. La nueva compara otra cosa: que sea **literalmente la misma**. Se verificó pegando a mano una copia que daba resultados idénticos: las siete pruebas viejas siguieron en verde y sólo la nueva se dio cuenta. Que coincidan hoy nunca fue garantía de nada.

## Ahora hay una sola cuenta, y encontramos siete errores en cómo se calculaba el voto (22-08-2026)

**Lo primero: se dio de baja la forma vieja de calcular.** Hasta hoy convivían dos maneras de sacar el número y eso ya no pasa. La que queda es la de puertas, y arrastra un cambio de fondo: **el modelo dejó de estimar si a un proyecto lo van a tratar.** Eso es política —se decide a puertas cerradas— y no se predice.

La consecuencia hay que decirla de frente: **el número ya no responde "¿va a ser ley?". Responde "si las dos cámaras lo votan, ¿lo aprueban?"**. Es una pregunta más chica y mucho más honesta. La pantalla lo dice.

**Y después, lo que apareció al revisar el cálculo.** Valle pidió mirar cómo se sacaba el porcentaje de acompañamiento de cada legislador. Salieron siete errores. Los tres que más importan:

**Uno.** El modelo miraba cuántas veces acompaña cada bloque —un número entre 0 y 100— y lo **redondeaba a sí o no**. La Coalición Cívica, que acompaña al gobierno el 61% de las veces, quedaba convertida en "sí", y como sus diputados son disciplinados, el modelo terminaba diciendo **97%**. La duda desaparecía. Por eso todas las votaciones daban 99%: no era que el dato fuera pobre, era que la cuenta tiraba la información en el camino.

**Dos.** Para saber de qué lado está cada uno, el modelo miraba a su grupo grande; para saber cuánto se despega, miraba a su bloque real. Dos grupos distintos para la misma persona. Del Caño, del Frente de Izquierda, salía como **voto seguro a favor del Ejecutivo** —100%— cuando su propio historial dice 1%. Le pasaba lo mismo a De la Sota. Ahora, si alguien tiene historial propio suficiente, **manda su historial**.

**Tres.** Faltar se contaba como votar en contra. Martín Menem, que preside la Cámara y por eso casi no vota, aparecía como un voto en contra en la versión vieja y como un voto a favor en la nueva. Las dos mal. Ahora son dos cosas separadas: **de qué lado está** y **con qué frecuencia aparece**. Vota el 1,3% de las veces, así que no suma a la cuenta — y cuando vota, acompaña al gobierno el 96%.

**Lo que se ve ahora que antes no se veía:** el Senado pasó de tener **cero** legisladores indecisos a tener **siete**. No es que hayan cambiado de opinión: es que antes el redondeo los tapaba.

**Un error propio, y lo cuento porque es el tipo de cosa que este proyecto no perdona:** al corregir lo anterior, el umbral para aprobar cayó a 112 sobre 257, o sea que el modelo suponía 45 ausentes en cada votación. No es creíble. La causa era que estaba mezclando "votar distinto" con "no venir". Separadas, el umbral quedó en 122.

**Y una trampa que casi me lleva puesta:** al regenerar el padrón de diputados con el comando normal, el archivo pasó de 1.454 filas a 257 — se llevó dieciocho años de historia sin dar ningún error. Lo detecté porque comparé el antes y el después, no porque algo fallara. Quedó anotado en URGENTE, porque le puede pasar a cualquiera.

## Y también los del Senado: la Puerta C deja de estar vacía (21-08-2026)

El mismo día, la otra mitad. Bajamos **1.761 Órdenes del Día del Senado** y sacamos **17.688 firmas** sobre 1.265 proyectos.

**Lo importante no es el número, es cuáles son.** De esas 1.761, **475 son dictámenes del Senado sobre proyectos que ya habían pasado por Diputados** — o sea, el Senado actuando de cámara revisora. Ese era el eslabón que el modelo no tenía: sabíamos qué pasaba en la cámara donde nace un proyecto, y nada de lo que pasa en la que lo revisa. Ahora hay documentos, con nombres y disidencias.

**El límite, dicho de frente.** De esas firmas, sólo la mitad se pudo enganchar a un legislador con su bloque, contra el 96% de Diputados. La razón está medida y es una sola: **nuestro padrón del Senado empieza en diciembre de 2017**, y 1.102 de las 1.761 Órdenes del Día son anteriores. No es que los nombres no se lean —se leen— es que no tenemos contra qué compararlos. Se puede reconstruir, igual que hicimos con Diputados, pero el Senado renueva por tercios cada dos años con mandatos de seis, así que la receta no se copia: hay que rehacerla. Queda decidido para otro día, con el número a la vista.

**Un hallazgo del camino:** el Senado escribe sus dictámenes distinto que Diputados, y por eso al principio la mitad no se leía. La fórmula de cierre, la fecha al revés, el separador entre nombres: cuatro diferencias chicas que, corregidas, casi duplicaron las firmas encontradas. Y algo que conviene saber: **el Senado no rotula "dictamen de mayoría" ni "de minoría"**. Cuando hay desacuerdo lo escribe como disidencia. No es que falte el dato: es que esa cámara trabaja así.

## Ya sabemos quién firma cada dictamen: 125.504 firmas (21-08-2026)

Ayer descubrimos que nos faltaba un dato clave y que estaba en la fuente. Hoy lo fuimos a buscar.

*(Los números de esta entrada son los de la corrida completa que terminó el 22-08, ya con el lector corregido. Los que se anotaron el 21 eran de una corrida anterior y diferían en menos de cien firmas.)*

**Qué hay ahora.** Para 3.541 proyectos de ley, entre 2008 y junio de 2026, sabemos **quién firmó el dictamen de comisión, en qué carácter y de qué bloque era esa persona ese día**. Son 125.504 firmas, y el 96,0% está enganchado a un legislador concreto de nuestro padrón: 1.227 personas distintas.

Y lo más importante para el modelo: **el carácter del trabajo en comisión ya es visible**. De esas firmas, 35.191 son de dictámenes de mayoría y 12.984 de minoría — o sea, casos donde la comisión no se puso de acuerdo y salieron dos textos enfrentados. Hay 3.564 firmas en disidencia parcial y 147 en disidencia total. Eso es exactamente lo que Valle quería que la Puerta A pasara a medir: no adivinar si una comisión va a tratar algo, sino leer cómo salió cuando lo trató.

**De dónde salió.** De 2.517 PDF de Órdenes del Día, bajados uno por uno del sitio de Diputados. Se leyeron 2.302 (el 91,5%). Las 215 que no, quedan en la tabla **marcadas con el motivo** en vez de desaparecer: 13 son documentos que Diputados directamente no tiene publicados, uno está corrupto, y las otras 201 tienen el texto armado de una forma que el lector todavía no reconoce. Esa distinción importa: un dato que falta y se sabe que falta es manejable; uno que desaparece sin avisar hace que todo parezca más completo de lo que es.

**Una cosa que hubo que arreglar antes.** Para saber de qué bloque era cada firmante hay que consultar el padrón de legisladores a la fecha del dictamen. Y ahí apareció que **nuestro padrón de Diputados sólo tenía la foto actual**: para 2008 conocía 81 de las 257 bancas. Con eso, sólo el 55% de las firmas se podía identificar. Se reconstruyó la historia a partir de las votaciones —si alguien votó un día, ese día tenía banca, y el acta dice de qué bloque era— y el número subió al **98,9%**. El padrón oficial sigue mandando donde llega; lo reconstruido sólo rellena lo que faltaba, y cada fila dice de dónde salió.

**Lo que sigue faltando, dicho claro.** Los años 2021 y 2022 no se pueden reconstruir porque casi no tenemos votaciones de Diputados de esos años — es un hueco viejo y conocido. Y los dictámenes del **Senado** todavía no están: el portal de Diputados publica los dictámenes de las comisiones de Diputados, así que para el Senado hace falta otra fuente. Ya está encontrada, verificada y programada; falta correrla.

**Y una advertencia práctica.** Bajar y leer 18 años de documentos llevó una tarde, pero **es por única vez**. De acá en adelante son entre 50 y 80 documentos nuevos por año: una actualización mensual son segundos. Todos los cálculos del modelo leen un archivo de 900 KB, no los PDF.

## Descubrimos que nos falta un dato clave: quién firma los dictámenes (20-08-2026)

Valle decidió el rumbo del modelo: dejamos de intentar adivinar **si una comisión va a tratar un proyecto** —eso es política y no se predice— y pasamos a mirar **cómo salió el trabajo de la comisión**: quién acompañó el dictamen, si hubo acuerdos entre bloques distintos, si los que firmaron son figuras de peso. Es una señal mucho más honesta, porque no adivina nada: lee lo que efectivamente pasó.

Al ir a buscar ese dato apareció el problema: **no lo tenemos**. Nuestra base sabe que hay dictamen, de qué comisión y de qué fecha —19.702 proyectos, desde 2008— pero **no sabe quién lo firmó**. Y no es que lo estemos tirando al cargarlo: el portal de datos abiertos de Diputados directamente no lo publica.

Pero el dato existe. Está en el PDF de la **Orden del Día**, que es el documento donde se publica cada dictamen: ahí figuran los firmantes uno por uno, quiénes firmaron en disidencia y por qué. Y ya tenemos el número de Orden del Día de cada proyecto, así que sabemos exactamente qué ir a buscar: **18.067 documentos que cubren 18.787 proyectos**. Es trabajo, pero es trabajo acotado y con un final claro.

Mientras tanto hay algo que sí se puede usar desde hoy, porque está en las observaciones que ya cargamos: si el dictamen fue **de mayoría o de minoría**, si tuvo **disidencias**, y si lo firmaron **varias comisiones juntas** (que es una buena señal de acuerdo amplio).

Y hay una consecuencia que conviene tener clara: si el modelo deja de estimar la mortandad en el cajón, el número que publicamos pasa a significar otra cosa. Ya no es «qué chance tiene este proyecto de ser ley» sino «qué chance tiene **dado que llegó hasta acá**». Sólo 1 de cada 6 proyectos llega a tener dictamen, así que la diferencia no es menor y tiene que estar escrita en la pantalla, no escondida en un manual.


## El mapa del modelo dejó de dibujar dos veces lo mismo (20-08-2026)

El mapa que muestra de dónde sale el número dibujaba la cadena entera **dos veces**, una por cámara: 153 cajas en pantalla para 96 piezas reales. No era sólo cargoso de mirar — era **falso**. La maquinaria que junta los datos (bajar las votaciones, armar el padrón, limpiar la base) corre **una sola vez** y sirve para las dos cámaras. Dibujarla espejada hacía creer que hay dos maquinarias.

Ahora el dibujo se lee como lo que pasa de verdad: un **tronco común** a la izquierda —la maquinaria de datos, una sola— y recién a la derecha se abre en **dos ramas cortas**, una por cámara, que terminan juntándose en la probabilidad final de que el proyecto sea ley.

Las cámaras se rotulan «ej.: Diputados» y «ej.: Senadores» a propósito. Un proyecto puede nacer en cualquiera de las dos y el modelo no supone cuál: poner «(Diputados)» a secas habría convertido un ejemplo en una afirmación.

De paso apareció algo para mirar: la rama de la cámara revisora **no usa el embudo ni la asistencia**. Puede estar bien o puede ser un agujero; quedó anotado.


## Qué estamos construyendo
Una herramienta que estima **qué probabilidad tiene un proyecto de ley de ser aprobado** en el Congreso argentino. No para reemplazar al analista político, sino para darle un radar: qué proyectos están ganando tracción y qué legisladores son la bisagra que define una votación.

## Lo más importante que aprendimos (y que cambió el rumbo)
Probamos lo obvio primero: ¿se puede adivinar cómo vota cada diputado mirando a su bloque? **Sí, y demasiado bien: acierta el 99%.** Los diputados votan casi siempre con su bloque. Eso suena bien, pero en realidad es una mala noticia para el producto: si una regla trivial ("votá con tu bloque") ya acierta el 99%, un modelo sofisticado no agrega nada ahí. Sería gastar pólvora en chimangos.

Entonces, ¿dónde está el valor real? En las tres cosas que el bloque **no** explica:
1. **Quién va a estar presente** (asistencia y quórum). Muchas leyes se ganan o pierden por quién falta ese día.
2. **Si el proyecto siquiera llega a votarse** (el "embudo"): la mayoría de los proyectos mueren en comisión y nunca llegan al recinto.
3. **Qué postura va a tomar el bloque** (la negociación de los líderes), que es política pura y no sale de los datos abiertos.

Ese giro es la decisión más importante del proyecto hasta ahora.

## Cómo conseguimos los datos (la idea de "semilla, base propia y bot")
Pensalo como una huerta:
- **La semilla:** Andy Tow tiene un trabajo enorme ("La Década Votada") con votaciones desde 1998. Lo usamos **una sola vez** para arrancar, no para depender de él para siempre. Tomamos su cosecha como punto de partida.
- **Nuestra base propia (la huerta):** juntamos esa semilla con los datos oficiales (Congreso) y los volcamos en **una sola base de datos nuestra**, ordenada y sin duplicados. Esa base es la fuente de verdad del proyecto.
- **El bot (el que riega):** un programita que corre solo cada tanto, mira las fuentes oficiales y agrega las votaciones nuevas a nuestra base. Así la base se mantiene fresca sin que dependamos de que otro la actualice.

Detalle importante: la base de datos oficial del Congreso dejó de actualizarse en 2020, así que lo reciente lo sacamos de otra fuente (argentinadatos).

**Dónde está la huerta hoy (al 06-08-2026):** **1.016.632 votos en 6.231 votaciones**, de 2001 a 2026, las dos cámaras. *(Este párrafo decía que faltaba un pedazo del Senado entre 2014 y 2023: ese hueco se cerró el 02-07-2026 con el scraper del Senado oficial. Queda un solo hueco abierto, Diputados 2020-2023, y está pausado a propósito desde el 10 de julio para priorizar la puesta en marcha.)*

## El "idioma común" de los datos (el esquema)
Cada fuente trae los datos con nombres distintos. Para que todo encaje, definimos un **formato único** (lo llamamos esquema canónico): dos planillas, una de "votaciones" y otra de "votos", con columnas fijas y una lista cerrada de valores para el voto (afirmativo, negativo, abstención, ausente). Antes de entrar a nuestra base, toda fuente se traduce a ese idioma. Es como obligar a que todos los enchufes sean del mismo tipo.

## Cómo trabajamos varios a la vez sin pisarnos
El proyecto está dividido en **módulos**, como estaciones de una cocina (uno para cada fuente de datos, uno por cada variable del modelo, etc.). La regla de oro: **un módulo, una persona, una rama**. Cada uno cocina en su estación y no mete la mano en la del otro; si necesita algo, usa el plato terminado del vecino, no su sartén. Así casi nunca chocamos.

Para coordinarnos hay tres papeles siempre a la vista:
- **TABLERO:** quién está haciendo qué (se reclama una tarea antes de empezar).
- **ESTADO:** la bitácora técnica de todo lo hecho.
- **EN HUMANO** (este archivo): la misma historia, pero contada para entender.
- **PLAN:** qué sigue y cómo.

## Dos detalles de "plomería"
- **Archivos_Borrar/**: la carpeta vive en OneDrive y el entorno no puede borrar archivos. Entonces todo lo descartable (pruebas, descargas temporales) lo dejamos en esa carpeta para que un humano lo borre a mano.
- **GitHub manda:** la carpeta sincronizada con OneDrive dio problemas (rompió el control de versiones). La fuente de verdad es el repositorio en GitHub; conviene trabajar desde ahí, no desde OneDrive.

## En una frase
Ya sabemos que adivinar el voto individual no sirve (el bloque lo explica casi todo); el valor está en la asistencia, el embudo y la cúpula. Estamos armando una base de datos propia (arrancada con el trabajo de Andy Tow y mantenida por un bot), con un formato común y una forma de trabajar en equipo sin pisarnos.

## Avance: ahora hay un mapa que muestra de dónde sale el número

Cuando alguien preguntaba «¿de dónde sale este 12%?», la respuesta honesta era abrir quince archivos y armar la historia de memoria. Ahora hay un **mapa** que se abre con doble clic (`MAPA-MODELO.html`, en la carpeta principal, sin internet) y que muestra la máquina entera dibujada: de qué página oficial sale cada dato, qué programa lo transforma, en qué archivo aterriza, qué señal alimenta, y cómo se combinan todas para dar la probabilidad final. Son 96 piezas y 131 conexiones.

**Segunda vuelta (20-08):** el mapa estaba bien de contenido y mal de dibujo — parecía una tabla de columnas y no un recorrido. Ahora se lee como un circuito: **dos bloques, uno al lado del otro, uno por cada cámara**. En cada uno se sigue la misma cadena de punta a punta, y la forma sola te dice qué estás mirando (un rectángulo es una base de datos, un hexágono es un programa, un círculo es una señal, y un rectángulo de borde grueso es una probabilidad). Del resultado de la primera cámara sale una **flecha gruesa por arriba** hasta la segunda, que dice lo que hay que entender: la pregunta ahí ya no es «¿se aprueba?» sino «¿se aprueba **habiendo pasado** por la otra cámara?». Lo que depende de ese paso previo está agrupado y pintado aparte. Las dos probabilidades bajan y se juntan abajo en una sola: la de que el proyecto sea ley.

Dos cosas más. Las piezas que alimentan a las dos cámaras (la base de votos, el padrón, casi toda la recolección) **se dibujan de los dos lados**, para poder seguir cada camino sin saltar de un bloque al otro; llevan una marquita y al hacerles click se encienden las dos copias, así nadie cree que son dos máquinas distintas. Y se sacó de arriba todo lo que era presentación —título grande, subtítulo, la franja de fórmulas—: esto es una herramienta interna, no un folleto. Las dos fórmulas que conviven siguen estando, abajo en la leyenda, en chico.

**Y una corrección de fondo:** las Puertas A y C (¿sale de comisión? ¿la tratan antes de que caduque?) figuraban con un estado que su propia fuente contradecía. Quedaron marcadas como **replanteadas y suspendidas**, que es lo que son: no las vamos a modelar, porque son política pura y no hay estadística que las prediga. Como eso no coincide con el estado del módulo que las contiene, ahora el mapa dice explícitamente de dónde saca cada estado.

Lo importante no es que sea lindo, son tres cosas:

1. **Se puede seguir con el dedo.** Hay un botón «Seguir un camino» que enciende el recorrido completo de un proyecto de ley, paso por paso, y apaga todo lo demás. En diez segundos se ve por dónde pasa el número.
2. **Cada pieza dice en qué estado está y quién la tiene.** Y eso no está escrito a mano en el mapa: sale del `README` de cada módulo, que es el papel que ya mantenemos. Si mañana un módulo cambia de dueño, el mapa se entera solo.
3. **Los agujeros se ven.** Lo que todavía no existe (el tramo de Diputados 2020-23, el módulo de contexto, las dos carpetas de evaluación, la API) aparece dibujado con borde punteado. Se ve, y se ve que no está. Esconder los huecos era la mitad del problema.

Y hay una cosa que el mapa muestra a propósito y que veníamos arrastrando como confusión: **hoy conviven dos maneras de escribir la cuenta.** La que está corriendo (probabilidad de llegar a votarse × probabilidad de ganar la votación, y sólo en la cámara donde nace el proyecto) y la que decidió Valle en agosto, que abre el camino en cuatro «puertas» — sale de comisión, gana en origen, la tratan en la otra cámara, gana en la otra cámara — de las cuales dos están **deliberadamente apagadas** porque lo que pasa en comisión y los tiempos de tratamiento son política pura y no se pueden medir: se miran, no se predicen. Las dos aparecen juntas arriba de todo, cada una con su fórmula, para que nadie las confunda. Con una regla que hasta ahora estaba sólo en un documento: **una puerta que ya pasó deja de ser una probabilidad y vale 1** — por eso el mismo proyecto tiene un número distinto según en qué etapa esté, y eso no es un error, es la regla.

Detalle de plomería que vale la pena: el mapa **no tiene los datos adentro**. Los arma un programa que lee el índice del repo y los papeles de cada módulo cada vez que se corre. Es a propósito: el error que este proyecto ya cometió varias veces es escribir un número a mano en un archivo que después nadie vuelve a mirar, y que a los tres meses miente.

## Avance grande: el modelo ahora mira DE QUÉ LADO juega cada proyecto (y mejora mucho)
Veníamos con un problema: para adivinar cómo vota cada bloque, el modelo miraba su historial promediando TODAS las leyes del gobierno juntas —las fáciles de consenso y las peleadas—. En una reforma dura eso le hacía creer que la oposición acompañaba más de lo que realmente acompaña. La solución fue enseñarle a mirar sólo el historial en leyes PARECIDAS: si el proyecto lo empuja el gobierno o lo empuja la oposición.

Lo medimos contra votos reales de la era Milei (casi 70.000 votos, sin hacer trampa de mirar el futuro): prender ese "filtro" sube el acierto de cómo vota cada legislador **del 59% al 76%**. Y salió un hallazgo tuyo importante: no es lo mismo un proyecto del **Poder Ejecutivo** (un mensaje que manda el gobierno) que uno de un **diputado oficialista suelto** —y menos todavía uno de un **aliado** como el PRO—. Cuando mirás fino, ves que LLA no acompaña la agenda regulatoria del PRO aunque sean aliados. Así que ahora el sistema distingue cuatro tipos de proyecto: del Ejecutivo, del partido de gobierno, de aliados, y de la oposición.

También arreglamos una sobreconfianza: el sistema a veces decía "esto se aprueba con 100% de seguridad". Eso no puede ser: ni el legislador más leal es un 100% seguro, y siempre puede pasar algo raro (una ausencia masiva, una sorpresa). Ahora nunca dice 0% ni 100% —como máximo, 99%—.

Ya lo medimos con los datos regenerados: separar a los aliados funciona tal cual. Los proyectos del PRO (los "aliados") pasan de acertarse el 42% al 78% cuando se los trata como categoría propia en vez de mezclarlos con el gobierno. Y los informes bicamerales (los que muestran un proyecto puntual en las dos cámaras, incluido el HTML interactivo) ahora usan ese mismo motor afinado: miran de qué tipo es el proyecto y nunca dicen 0% ni 100%. Falta que Valle lo suba al repositorio.

Una salvedad honesta que anotamos para no comerla después: lo que mejoró y medimos es el acierto PROMEDIO del voto (76%). Para un proyecto puntual y emblemático —como una reforma de Ganancias— el número-titular todavía es frágil: el modelo lo estima mirando reformas parecidas del Ejecutivo que ya pasaron (Presupuesto, la reforma laboral), y como esas se aprobaron, le da una probabilidad demasiado alta al Senado. El arreglo pendiente es contar cada proyecto una sola vez (hoy uno votado artículo por artículo pesa de más) y mostrar el titular con una banda, apoyándose en el detalle por legislador más que en el porcentaje solo. Queda para una próxima.

## Corrección de rumbo: la segunda cámara se mide como VOTO, no como "¿la tratan?"
Durante la sesión me fui por un camino equivocado y Valle lo corrigió. Yo había intentado estimar "qué chance hay de que la segunda cámara trate el proyecto" con un promedio histórico. Pero eso es justo lo que decidimos NO medir cuando sacamos la etapa de comisiones: si una cámara pone o no un proyecto en el recinto es una decisión política pura (negociación de bloques, la vice, la oposición), volátil y atada al contexto —más aún en un período tan atípico como el de Milei—. Ningún promedio la captura.

Lo correcto, que es lo que vamos a hacer: la segunda cámara se calcula igual que la primera —**¿gana la votación, dada la composición real de esa cámara?**— y el "si la tratan o no" se **observa** (se mira si está en agenda), no se adivina. El trabajo de fondo que sigue es hacer que el sistema entienda **de qué trata y de qué lado juega cada proyecto**, porque eso es lo que hace que la estimación del voto distinga un proyecto de otro —en las dos cámaras, no en una—. Hoy, sin eso, el motor dice "pasa" casi siempre; la apuesta es que, con eso, distinga de verdad. (Aclaración honesta: eso es una hipótesis a comprobar, no un hecho. Un número que circulaba —el modelo dando el Senado al filo en un supuesto de Ganancias— es una proyección del propio modelo, no un resultado real, y parece no haber coincidido con lo que pasó; así que sirve para probar el sistema, no para darlo por bueno.)

## Arreglo con control humano: sacamos "designaciones" de lo que cuenta como ley
El sistema, para medir la postura de los bloques, mira sólo las votaciones de leyes de verdad (los tratados, homenajes y designaciones se aprueban por consenso y ensucian la señal). Se coló un grupo que no debía: las **designaciones del Senado** (cónsules, jueces, embajadores), que figuraban mal etiquetadas como "ley". Se agregó un filtro que las saca — pero **conservador a propósito**: sólo cuando el título es inequívocamente un nombramiento, para no borrar por error una ley real.

Y lo importante para la confianza: el filtro **deja escrita, cada vez que corre, una lista en castellano de todo lo que sacó**, para que una persona la revise de un vistazo. De hecho, armándolo se coló por error una ley real (una sobre el procedimiento para nombrar jueces suplentes); esa lista la detectó enseguida y quedó como control para que no vuelva a pasar. La idea: que no haya que confiar a ciegas en el filtro, sino poder auditarlo siempre.

## Ajustes: la prueba ahora corre en segundos, y una idea queda para más adelante
Dos cosas de mantenimiento. Primero, la herramienta que mide si el sistema le acierta a la realidad ahora corre **mucho más rápido**: antes releía toda la base de votaciones una y otra vez (por eso tardaba minutos); ahora la lee una sola vez y da exactamente el mismo resultado, pero en segundos. Eso nos deja probar variantes sin esperar.

Segundo, quedó **parqueada para después** (para cuando el sistema ya esté publicado y andando) una idea sobre la segunda cámara: modelar el "reloj" que hace caducar un proyecto si no lo tratan a tiempo. Decisión de Valle, con buen fundamento: los tiempos de tratamiento son políticos —lo que va a ser ley se trata rápido, y lo que no tiene peso político (la mayoría) nunca avanza—, y eso el sistema ya lo captura "en promedio" con el número que pusimos. Afinarlo fino es un lujo para más adelante, no algo que frene nada.

## Avance: le sumamos la segunda cámara bien, y el sistema empata a lo que teníamos
Entendimos algo que cambia cómo se suma la segunda cámara. De los proyectos que **llegan a votarse**, poco más de la mitad (54%) terminan siendo ley. Lo importante: esa mitad que se cae **no pierde la votación** — casi todo lo que se vota, se aprueba. Lo que pasa es que muchos proyectos **nunca llegan a tratarse** en la segunda cámara, o se cambian y quedan en la nada. Por eso no servía "simular la votación" del Senado (esa da que sí casi siempre): lo que hay que meter es esa realidad de que "más o menos la mitad completa el camino".

Metiéndolo como corresponde (usando sólo la historia previa a cada proyecto, sin hacer trampa con el futuro), el sistema completo pasó de estar **claramente por debajo** de la pieza que ya teníamos a **quedar empatado** con ella. Quedó hecho y probado dentro de la herramienta, listo para correr cuando quieras.

## Hallazgo: el simulador dice "pasa seguro" casi siempre, y por qué eso importa
Al probar sumarle la segunda cámara al sistema, apareció algo que ordena la prioridad: el simulador de votaciones, cuando no le decimos **de qué trata** el proyecto, contesta "hay mayoría" con casi total certeza — en las dos cámaras (en Diputados, en 9 de cada 10 casos). Suena bien pero es un problema: si siempre dice que sí, no distingue un proyecto de otro. Por eso agregar la segunda cámara "a lo mecánico" no cambió nada (multiplica por casi uno), mientras que el número fijo de la vez anterior sí ayudaba, porque metía la realidad de que la mitad se cae.

La conclusión útil: las dos cosas que parecían pendientes separadas (la segunda cámara y "decirle de qué trata cada proyecto") son en realidad **una con orden**: primero hay que decirle de qué trata; recién ahí el simulado de cualquier cámara vale la pena. Quedó todo anotado y la herramienta lista para cuando se haga ese paso.

## Cerramos un pendiente urgente: la cadena ya se re-corrió con los linajes nuevos
Había quedado anotado en la lista de "urgente" que, después de arreglar cómo se agrupan los bloques de izquierda, faltaba volver a correr dos piezas que dependían de ese cambio (el clima político y el simulador de votación) y **guardar todo en el repositorio**. Se verificó contra el disco que las dos piezas ya estaban rehechas y quedaron guardadas en el commit del 13 de agosto. Como ya está resuelto, se sacó de la lista de urgentes (el registro completo queda en la bitácora técnica). La lista de urgentes queda con un solo tema, y de baja prioridad: validar unas pocas filas del listado de jefes de bloque.

## Avance: una forma de medir si el sistema completo le acierta a la realidad
Hasta ahora cada pieza del Nowcast se validaba por separado: el "embudo" (¿el proyecto llega a votarse?) por un lado, y el "simulador de votación" (¿hay mayoría?) por otro. Faltaba probar la CADENA COMPLETA de una: multiplicar las dos y comparar con lo que de verdad pasó (¿el proyecto terminó siendo ley, sí o no?). Se armó esa herramienta. Toma los proyectos ya "maduros" (viejos como para saber si fueron ley o no), los evalúa **con la información que existía en su momento** (sin espiar el futuro), y mide qué tan bien le acierta — usando como vara de comparación la estimación que el embudo ya hace solo, para responder: ¿la maquinaria del simulador agrega algo o no?

Dos límites honestos que aparecieron al probarla contra el disco: por ahora corre sobre **Diputados** (para el Senado viejo no tenemos la lista de quién ocupaba cada banca en cada fecha con el detalle necesario), y el hueco conocido de Diputados 2020-2023 deja afuera esos años. La herramienta está probada y lista; **la corrida grande la hace Valle en su computadora** porque es pesada, y de ahí sale el número real (los de la prueba chica no cuentan).

## Avance: separamos "no vota porque desafía" de "no vota porque no va"

El sistema marca a los legisladores "bisagra" —los que pueden cambiar una votación peleada— midiendo cuánto se apartan de su bloque. El problema: ese número mezclaba dos cosas muy distintas. Una es **votar distinto** (indisciplina de verdad). La otra es **no aparecer** (ausentismo). Y estaban tan pegadas que casi cuatro de cada diez puntos del "desvío" eran, en realidad, inasistencia.

Se veía en el ranking: lo encabezaban personas que casi nunca votaban. Néstor Kirchner figuraba como el más díscolo de todos… con 98% de ausencias y una sola votación presente en toda la base. Cuando esta gente aparecía, votaba con su bloque. Su "rebeldía" era pura ausencia. Y el modelo les daba máxima sensibilidad al clima político, cuando un ausente crónico no es una bisagra: es alguien que no está.

Lo que hicimos: separar el número en dos. Uno mide cuánto se desvía **estando presente** (la indisciplina real), otro mide la ausencia por separado. Además, con tu criterio, armamos la distribución de ausentismo y marcamos a los que están **muy por encima** (más de dos desvíos de lo normal, ~61% de faltas). De 77 casos así, 75 ni siquiera tienen banca hoy —son muertes en el cargo, bancas testimoniales y licencias— y se quitan del análisis. Los dos que sí tienen banca: Menem (que preside la Cámara y por eso no vota, pero entra correctamente como voto oficialista) y Schiaretti, que quedó marcado para que lo mires vos.

De paso se tapó una fuga: una banca fantasma anotada como "Legislador a Designar" metía más de mil votos vacíos en el ranking.

¿Sirvió? La cuenta definitiva ya la corrimos, y la respuesta es sí, y fuerte: al medir las bisagras por su conducta real, el efecto del clima político sobre ellas **más que se duplica** (y con margen de error firme, no por casualidad). Los legisladores disciplinados siguen sin moverse por el clima, como debe ser. Era lo que sospechábamos: mezclar ausentes diluía la señal a la mitad.

Y cerramos el circuito hasta la punta: la parte del sistema que arma la cámara para una proyección (el "roster") también empezó a usar el número limpio de conducta, no el mezclado. Así el arreglo no se queda en la estimación: llega hasta la predicción final. Con esto el pendiente queda cerrado. Un detalle que vimos de paso: que el clima cambie el *resultado* de una votación depende del proyecto — si una cámara lo gana holgado o si los que definen son legisladores disciplinados, el clima casi no mueve la aguja; se nota cuando la votación está en el filo y la definen las bisagras.

## Aviso: los tests pasaban en mi entorno y fallaban en el de Valle

Vale la pena contarlo porque es una trampa que se puede repetir. Ayer di por buenos unos controles que en mi entorno daban "83 de 83 correctos", y al correrlos Valle en su computadora **fallaron**. No era que el trabajo estuviera mal hecho: era que las dos máquinas tienen versiones distintas de una de las bibliotecas, y en una de ellas un dato faltante se representa de una forma que mi código no contemplaba.

El detalle técnico es chico y el error es de manual: yo preguntaba "¿este valor está vacío?" de una manera que funciona cuando el vacío es de un tipo y falla cuando es de otro. Hay tres formas de "vacío" dando vueltas y yo cubría una sola, justamente la que es fácil acordarse de probar.

Ya está arreglado, y sobre todo está arreglado el control: ahora las pruebas **imitan el entorno de Valle**, no el mío. Antes de dar por bueno el arreglo verifiqué que la prueba nueva efectivamente falla con el código viejo — una prueba de regresión que no reproduce el problema original no sirve para nada.

Se revisó también el otro módulo de ayer, el del padrón del Senado, por si tenía el mismo defecto: está sano.

La lección para el proyecto, que se suma a las otras del entorno: **"funciona en mi máquina" no es "funciona"**, y la corrida de Valle es la que vale. Los datos, por suerte, no se habían ensuciado: al regenerarlos dieron exactamente lo mismo.

## Aviso: estábamos mirando la votación equivocada

Se corrió el chequeo que había quedado pendiente sobre la fuente de datos recientes, para saber si publica el número de expediente de cada votación. La respuesta: **el Senado sí lo trae, Diputados no lo trae de ninguna forma**. O sea que el rodeo que se armó ayer —deducirlo del número de Orden del Día— no era un parche provisorio: es lo mejor que existe. Queda escrito, porque ya se buscó dos veces.

Pero el chequeo mostró de paso otra cosa, y esa sí obligó a corregir algo. **Una ley no se vota una vez: se vota "en general" —donde se decide si se aprueba— y después "en particular", artículo por artículo.** La Ley Bases tiene **50 votaciones** de un mismo proyecto. Y el programa que armé ayer se quedaba con la última de cada cámara, que en esos casos es el último artículo, no la votación que define la ley. Un artículo puede rechazarse y la ley aprobarse igual: estábamos por medir el resultado equivocado.

Ya está arreglado: ahora busca explícitamente la votación en general y, si no la encuentra identificada, se queda con la primera, que es la que va antes del articulado. Además queda anotado en cada caso **cuántas votaciones hubo** y **por qué se eligió esa**, para que quien use el dato sepa cuándo fue por evidencia y cuándo por regla. De los 243 proyectos con votación en las dos cámaras, 55 se votaron en partes.

Vale la pena decir de dónde salió el error, porque es el mismo de siempre en este proyecto: quedarse con la última votación parecía obviamente correcto, se escribió como si lo fuera, y nadie lo midió. Apareció de casualidad, mirando otra cosa.

## Avance: se destapó la ventana reciente (2025-2026)

Al cerrar lo del Senado quedó una alarma anotada: las leyes con votación en las dos cámaras se cortaban en 2020. Al mirarlo, el problema no era el Senado sino **Diputados**: desde 2020 sus votaciones entran sin ninguna referencia al proyecto votado — cero de 177 en 2024, cero de 116 en 2025. Y como una cadena necesita las dos mitades, no importaba lo bien que estuviera el Senado.

Los títulos de Diputados tampoco nombran el expediente, pero sí nombran la **Orden del Día**: *"O. D. 759 - DNU 179/2025..."*. La Orden del Día es el número con el que un dictamen llega al recinto, y esa numeración sí la teníamos cruzada con los proyectos. Con ese puente entran 251 votaciones más y aparecen las primeras cadenas completas de **2025 (7) y 2026 (5)**, que antes eran cero.

Dos cuidados que valieron la pena. Primero, las Órdenes del Día se renumeran todos los años, así que la búsqueda usa año y número juntos (y prueba el año anterior, porque una del final de diciembre se vota en marzo). Segundo, y más importante: **el puente NO se usa para el Senado**, porque el Senado numera sus propias Órdenes del Día y buscarlas en la tabla de Diputados devolvería un proyecto equivocado sin ningún aviso. Eso quedó escrito como prueba.

Sobre lo viejo, siguiendo el criterio de Valle: lo anterior a 2015 se conserva como historia —sirve para linajes y comportamiento de arrastre— pero no se va a forzar. Ningún legislador de esa época sigue en actividad y el Congreso de entonces no estaba digitalizado.

Queda una sola cosa por confirmar, y necesita internet: el sistema que trae los datos recientes pone el campo del expediente en blanco por una línea de código. No sabemos si la fuente lo publica o directamente no lo tiene. En vez de adivinar y arreglar mal, se dejó un chequeo de un solo comando que lo responde.

## Avance: el Senado pasa de 8% a 72% de votaciones identificadas

Quedaba un problema grande del cambio de enfoque: para seguir una ley de una cámara a la otra hay que saber **qué proyecto se votó** en cada votación, y del lado del Senado eso sólo estaba anotado en 8 de cada 100 votaciones. La conclusión natural era que había que volver a recorrer la web del Senado, votación por votación, veinte años para atrás.

**No hizo falta.** El dato estaba escrito en el propio título de la votación, en texto: *"Reforma Laboral. PE-608/03. Votación en general"*. Estaba a la vista y nadie lo estaba leyendo. Con eso el Senado pasa de **250 a 2.230 votaciones identificadas**, y los proyectos con votación registrada en las dos cámaras saltan de **39 a 223**.

Como el título es texto libre y podía traer errores, se comprobó contra los casos donde el dato ya existía anotado aparte: **coinciden en el 98,8%**. Y las tres diferencias resultaron útiles, porque explican cuándo NO hay que confiar en el título: a veces menciona *otro* expediente, uno que el proyecto cita o reproduce, no el que se está votando. Por eso la regla quedó en que el dato anotado siempre gana y el título es sólo el respaldo.

Una aclaración para que nadie lea mal el número: el porcentaje general de votaciones enlazadas *bajó* de 59,7% a 49,8%, y sin embargo se enlazaron 767 votaciones más. Es que ahora se está intentando con muchas más: las de antes de 2008 no tienen con qué cruzarse, porque la base de proyectos del Congreso arranca ahí. Las posteriores a 2008 se enlazan en el 79,6% de los casos.

Queda una sola cosa que sí es de recolección: el sistema que trae los datos recientes descarta el expediente a propósito, por una línea de código que lo pone en blanco. Habría que ver si la fuente lo publica; si lo publica, se arregla en dos líneas y el flujo del día a día queda cubierto.

## Avance: ahora podemos seguir una ley de una cámara a la otra

Cambió el enfoque del pronóstico. Hasta ahora intentábamos adivinar si un proyecto lograba salir de comisión, y eso resultó ser lo menos pronosticable de todo: lo que pasa en comisión se define en reuniones donde los partidos negocian a puertas cerradas, y no hay estadística que capture eso. Así que el nowcast pasa a medir lo que sí se puede medir: **si el proyecto se aprueba en la cámara donde nació y después en la otra**.

Eso trajo un problema práctico. Para seguir una ley de Diputados al Senado hay que saber que "el expediente 7435-D-2018 de Diputados" y "el CD-57/18 del Senado" son **el mismo proyecto**: cada cámara lo numera a su manera. Se creía que había que salir a buscar esa correspondencia a la web del Senado, expediente por expediente. **Ya estaba en nuestros propios archivos**: una columna que veníamos guardando desde el backfill tiene la numeración del Senado. Era juntar dos columnas, no un mes de scraping.

Con eso enlazamos el 60% de las votaciones que tienen expediente anotado, y aparecen los primeros **39 proyectos con votación registrada en las dos cámaras**. Es poco, y la razón es honesta: de cada 100 votaciones del Senado, sólo 8 tienen anotado qué proyecto se votó. Ese es el próximo arreglo, y es de carga de datos, no de modelo.

Lo segundo: **el Senado ahora tiene memoria**. Antes teníamos la foto de los 72 senadores de hoy, pero para revivir una votación de 2019 hace falta saber quiénes estaban en 2019. Se armó juntando lo que ya se había reconstruido de Wikipedia con la nómina oficial: 243 mandatos, 176 senadores, de 2017 a 2031.

Y una del tipo "el control sirvió": al pedirle la composición de un día cualquiera de 2024, devolvía **90 senadores en un cuerpo de 72**. El motivo no era político sino de nombres — Wikipedia dice "Eduardo Vischi" y la lista oficial dice "VISCHI, ALEJANDRO EDUARDO", y el sistema los tomaba por dos personas distintas. Al unirlos hubo que ser cuidadoso: *Carlos Juan Pagotto* y *Juan Carlos Romero* comparten los dos nombres de pila y son dos senadores distintos, igual que *Bensusán, Daniel Pablo* y *Pablo Daniel Blanco*. Fusionarlos habría inventado un senador que no existe y le habría atribuido votos ajenos. La regla quedó en que **manda el apellido**, y esos cuatro casos quedaron escritos como prueba para que nadie los rompa de nuevo.

Un dato que salió de paso y que ordena la discusión del producto: de las 1.340 leyes sancionadas desde 2008, **669 nacieron en Diputados y 661 en el Senado**. Mitad y mitad. Un producto que mire sólo Diputados deja afuera la mitad de las leyes del país.

## Avance: la base canónica ya respira
Ya tenemos la "huerta" funcionando con su primera fuente real: tomamos las votaciones oficiales de Diputados (2011–2020), las tradujimos al idioma común y armamos nuestra base propia —casi 231 mil votos en 899 votaciones— con un control automático que rechaza cualquier dato mal formado. Todavía es una sola fuente; faltan sumar la semilla histórica de Andy Tow y los datos recientes, y unificar los nombres de legisladores que aparecen distinto en cada fuente. Pero el circuito completo (bajar → traducir → unir → validar) ya está probado y andando.

## Avance: la base ya cubre 2011–2025 (Diputados) y arrancó el Senado
Sumamos los datos recientes (2020–2025) y tapamos 2019. Hoy la base tiene 1.414 votaciones y 340 mil votos. Para Diputados, además, cuando el dato venía sin el bloque del legislador, lo completamos cruzando con el padrón (qué bloque tenía cada uno en esa fecha). Falta para llegar a los 25 años completos en ambas cámaras: la historia vieja (antes de 2011) sale de la semilla de Andy Tow; el Senado está casi todo por completar (hoy solo 2024–2025) y su dato de bloque es el más difícil. El mapa exacto de qué falta está en `datos/canonica/COBERTURA.md`.

## Avance: empezamos a "unir personas"
El mismo legislador aparece escrito distinto en cada fuente (con coma, sin coma, mayúsculas, orden de nombres). Armamos un paso que reconoce que son la misma persona y le pone un identificador único. En la primera pasada, de 1.358 formas de escribir nombres quedaron 1.131 personas reales, y 225 quedaron correctamente pegadas entre las dos fuentes. Es un primer pase: los casos con un segundo nombre que aparece en una fuente y no en otra todavía quedan separados, y los nombres de bloques los seguiremos puliendo.

## Avance: ordenamos los bloques (con cuidado)
Los bloques aparecen escritos de muchas formas y, además, cambian de nombre con el tiempo. Hicimos dos cosas separadas: primero unificamos las formas de escribir el mismo bloque (UCR, PRO, etc.); y segundo, agrupamos los espacios políticos a lo largo del tiempo —por ejemplo, Frente para la Victoria, Frente de Todos y Unión por la Patria como una misma línea kirchnerista—. Lo importante: guardamos siempre el nombre original, y dejamos por escrito qué juntamos y qué NO (por ejemplo, no metimos al Frente Renovador de Massa dentro del kirchnerismo, ni armamos "Juntos por el Cambio" porque su composición cambia según el año). Todo eso está explicado y es reversible en `datos/canonica/BLOQUES.md`.

## Avance: linaje de bloques afinado con tus criterios
Aplicamos tus decisiones sobre los espacios políticos: los aliados chicos del kirchnerismo (Peronismo para la Victoria, Nuevo Encuentro, Libres del Sur) ahora cuentan como FdT-UxP; y el Frente Renovador de Massa figura aparte hasta 2019 y como parte del kirchnerismo desde diciembre de ese año (cuando confluyó en el Frente de Todos). Quedó anotado, además, que más adelante hay que clasificar los proyectos por TEMA (economía, penal, laboral, etc.), que es clave para analizar por materia. Todo documentado y reversible en `BLOQUES.md`.

## Avance: agrupamos por coalición (respetando las fechas)
Sumamos un nivel más: la coalición electoral. Lo más delicado era Juntos por el Cambio, porque solo existió como alianza entre 2015 y 2023. Lo resolvimos con fechas: UCR, PRO y la Coalición Cívica cuentan como "Juntos por el Cambio" únicamente en esa ventana; antes de 2015 y después de 2023 vuelven a figurar por separado (porque antes no estaban coaligados y después la alianza se rompió). Verificamos que recién aparece en 2016, como corresponde. Quedan anotadas dos cosas para definir más adelante: si sumar aliados provinciales, y cómo tratar el acercamiento PRO–La Libertad Avanza en 2024–2025.

## Hallazgo: el Senado 2001–2003 no tiene "quién votó qué"
Abrimos una muestra de los diarios de sesiones del Senado de 2002. Buena noticia: se puede leer y trae la lista de quién estuvo presente o ausente, y el resultado de cada votación (aprobado/rechazado). Mala noticia: en esa época el Senado votaba a mano alzada, así que el documento NO dice cómo votó cada senador uno por uno. O sea, para el Senado viejo no existe el "voto por bloque" — eso recién empieza en 2004. Lo dejamos anotado con todo el detalle (en `datos/senado/NOTA-2001-2003.md`) y vos decidís más adelante si igual aprovechamos la asistencia y los resultados.

## Avance: volvimos a medir la disciplina, ahora con más años
Repetimos la medición clave sobre toda la base (2011–2025). Tres cosas: (1) predecir el voto de cada diputado mirando su bloque sigue acertando ~97% aun en las votaciones peleadas — o sea, ahí no hay nada que ganar con un modelo. (2) Pero si miramos por coalición (no por bloque chico), baja a ~92%: hay un 8% de "díscolos" que se despegan de la línea de su coalición, y eso SÍ es señal aprovechable. (3) Lo más llamativo: la disciplina, que fue altísima de 2011 a 2023, se afloja en 2024 y 2025 (la fragmentación de la era Milei). El Senado todavía no se puede medir porque nos falta el dato de bloque.

## Avance: arrancamos la clasificación por tema (y descubrimos qué falta)
Empezamos a etiquetar cada votación por tema (economía, salud, penal, etc.) con una lista de 15 materias y un primer clasificador automático. Al probarlo apareció un límite claro: el título de la votación casi siempre dice solo "expediente tal, votación", sin contar de qué trata la ley. Para clasificar bien necesitamos el texto descriptivo del proyecto, que está en otra fuente (los "expedientes"). Buena noticia: ya guardamos el número de expediente de cada votación, así que es cuestión de traer esos textos y cruzarlos. Te dejé la taxonomía propuesta para que la ajustes a tu gusto.

## Avance: ya clasificamos leyes leyendo su texto (y le acertamos a tu criterio)
Aprobaste la taxonomía granular (16 áreas, ~55 subtemas, con energía/ambiente, laboral/previsional y educación/ciencia/cultura separados). Probamos un clasificador que LEE el texto completo de cada ley y le pone tema, y lo comparamos con las etiquetas que vos pusiste a mano: coincidió en 13 de 15. Los 2 que no coincidieron no son errores, son decisiones de criterio (¿la ludopatía es Salud o Justicia? ¿una reforma del código de sociedades es Comercial o Judicial?) que conviene que definas vos. Dos de las leyes son escaneos sin texto, así que esas necesitan OCR.

## Cierre: el clasificador quedó alineado 100% con tu criterio
Definiste dos reglas (la ludopatía va a Salud; cualquier reforma de un código de fondo va a Justicia) y con eso el clasificador coincide con tus 15 etiquetas, 15 de 15. Quedó listo para usarse y escalar al resto de las leyes.

## Avance: integramos tu Excel 2026 y por fin medimos el Senado
Cargamos tu planilla hecha a mano: sumó los votos de 2026 de las dos cámaras y, sobre todo, trajo el dato de bloque del Senado que nos faltaba. Con eso pudimos medir por primera vez la disciplina del Senado (~94% en votaciones peleadas, parecido a Diputados aunque con pocos casos todavía). La base ya tiene 1.431 votaciones y casi 344 mil votos. Tu Excel quedó como una fuente más del sistema, con la máxima prioridad por ser curado a mano.

## Avance grande: la base ya cubre 25 años y las dos cámaras
Descubrimos que dentro de los Aportes ya estaba el dato histórico completo de Andy Tow en planillas (no hacía falta esperar la descarga lenta de R). Lo integramos: ahora la base tiene casi 781 mil votos de 2001 a 2025, Diputados y Senado. Por primera vez medimos bien la disciplina del Senado histórico: ~97%, parecida o un poco mayor que Diputados. Lo único que falta para completar el Senado es el tramo 2015–2023.

## Avance: el agente que lee la ley y le pone los temas
Construimos el "etiquetador automático": un programa que toma el PDF de un proyecto de ley, lo lee entero (articulado y fundamentos) y le pone los temas que correspondan, eligiéndolos del diccionario de temas que armamos antes. Lo hace una IA (Claude), que es la que entiende el texto. Tres recaudos importantes: (1) la IA solo puede elegir temas que estén en nuestra lista —si se le ocurre uno que no existe, lo descartamos y, si de verdad falta, lo anota como sugerencia para que una persona lo agregue; (2) si vos ya etiquetaste un proyecto a mano, la IA nunca te pisa esa etiqueta; (3) si el PDF es una foto escaneada sin texto, lo deja pendiente (eso necesita el paso de "lectura de imagen" que veremos más adelante). Para usarlo de verdad hace falta una clave de acceso a la IA (API key), que se configura una vez. Probamos toda la lógica con una IA "de mentira" y funciona; falta la corrida final con la clave real.

## Avance: armamos el "diccionario de temas" (taxonomías)
Hicimos la lista oficial de temas con la que se va a etiquetar cada proyecto de ley: 16 grandes áreas (economía, energía, salud, justicia, etc.) divididas en unos 55 subtemas más finos (minería, inteligencia artificial, ciberseguridad, jubilaciones, subsidios, universidades, medicamentos, trenes…), más algunas etiquetas auxiliares (homenajes, trámite, sin clasificar). Dos detalles importantes: (1) cada tema tiene un **código fijo** además del nombre, así si mañana le cambiamos el nombre a un tema, todo lo ya etiquetado sigue funcionando; (2) un proyecto puede tener **varios** temas a la vez (lo normal). La lista es fácil de ampliar: le pedís a Claude "agregá el tema X" y lo suma respetando las reglas. Esta lista es la que va a consultar el agente para poner las etiquetas, y vos la podés editar cuando quieras.

## Avance: ya tenemos dónde guardar cada proyecto (la "base de Proyectos")
Armamos la libreta donde se anota cada proyecto de ley, uno por fila, identificado por su denominador (ese código tipo 2832-D-2026 que ustedes leen en las tablas). Por cada proyecto guarda el tema, la fecha, los autores con su bloque, a qué comisiones lo giraron, su último movimiento y en qué estado está (en comisión, media sanción, aprobado, rechazado…). Lo importante: cuando un proyecto avanza, la libreta **actualiza** esa fila en vez de crear una nueva, así nunca se duplica. Y las etiquetas de tema (las "taxonomías" que pondrá el agente) quedan guardadas aparte y no se borran cuando volvemos a chequear el estado del proyecto. Además, en cualquier momento se puede sacar un Excel lindo para leer. Por debajo es una base de datos (SQLite), pero vos la ves como una planilla.

## Replanteo: sí vamos a mirar al parlamentario uno por uno (no solo al bloque)
Antes habíamos dicho que adivinar el voto individual "no servía" porque mirar al bloque ya acierta el 99%. Lo afinamos, porque ese 99% es un **promedio que engaña**. La mayoría de los legisladores —diputados y senadores— votan siempre con su bloque (fáciles de adivinar), pero hay un grupo chico —10 o 20— que se despegan de la línea. Ese puñado es justo el que define las votaciones peleadas.

Pensalo así: nuestro indicador puede decir "hay 98% de chances de juntar los votos para aprobar". Pero ese número esconde que todo depende de 10 o 20 parlamentarios bisagra: si ellos se disciplinan o se rebelan, la probabilidad de aprobación cambia de un lado al otro. Por eso vale la pena mirarlos individualmente. Esto aplica a las **dos cámaras**: tanto diputados como senadores.

Entonces separamos **dos miradas** que antes mezclábamos:
- **La del partido/bloque:** sirve para la foto grande (cuántos votos junta cada espacio, cómo negocian las cúpulas).
- **La del parlamentario:** mira a cada legislador (diputado o senador) y, sobre todo, **cuánto se desvía de su bloque**. Eso nos deja: medir qué tan "díscolo" es cada uno (en general y según el tema), estimar cuándo es probable que se rebele, dar el resultado como un **rango** ("entre 115 y 125 votos") en vez de un número seco, y —lo más útil— marcar la **lista corta de los parlamentarios
## Cierre del día: ordenamos para subir al repo
Dos cosas. Primero, la clasificación de temas: el equipo armó un sistema más completo (un agente que lee el PDF y usa una lista de temas controlada), así que dejamos solo ese y retiramos el clasificador más simple que habíamos hecho —pero sirvió, porque las reglas que definiste (juego→Salud, códigos→Justicia) ya quedaron en su lista. Segundo, dejamos nuestro lado (la base de votaciones) listo para subir: hay un solo comando que reconstruye toda la base de 25 años desde cero, y marcamos qué archivos no se suben (los datos pesados se regeneran). Lo único a tener en cuenta: el control de versiones dentro de la carpeta de OneDrive está roto, así que el commit conviene hacerlo desde tu copia limpia del repo.
ficha oficial y saca esos datos ordenados. Funciona para las dos cámaras: en Diputados se entra por la página del diputado autor (por eso necesitamos guardar el "apodo web" de cada uno, ej. *sajmechet*); en el Senado alcanza con el número de expediente y trae todo más completo. Lo probamos con ejemplos reales y anda; falta una prueba final conectados a internet desde tu PC (la computadora donde yo trabajo no puede entrar a las webs del Congreso). Un detalle: algunos proyectos son PDF escaneados (una foto del papel), y para esos hace falta un paso extra de "lectura de imagen" que veremos más adelante.

## Avance: le pusimos número a los "díscolos" (y encontramos algo)
La semana pasada decidimos que el valor no estaba en adivinar el voto promedio sino en los pocos legisladores que se apartan de su bloque. Hoy eso dejó de ser una hipótesis y pasó a ser una medición: para cada legislador de los últimos 25 años calculamos su "termómetro de rebeldía" — de todas sus votaciones, ¿cuántas veces votó contra la mayoría de su propio bloque?

Resultados: el legislador típico se desvía solo 1 de cada 100 votos. Los muy díscolos (más de 1 desvío cada 10 votos en votaciones peleadas) son unas pocas decenas en 25 años de historia. Es decir: la famosa "lista corta de bisagras" existe y es corta de verdad, tal como suponíamos. Y un hallazgo: en 2026 la rebeldía promedio se disparó a 5 de cada 100 votos, diez veces más que hace una década — la disciplina partidaria se está aflojando, que es exactamente el escenario donde nuestra herramienta más sirve (con la cautela de que 2026 recién empieza y solo miramos las leyes más conflictivas).

Una aclaración de cocina: la computadora donde trabajo hoy no tiene internet hacia las fuentes de datos, así que la medición usa la historia 2001–2014 más las votaciones 2026 cargadas a mano. Falta el tramo 2015–2025; cuando alguien corra el comando de reconstrucción desde una PC con internet, los números se recalculan solos con la base completa.

## Corrección de rumbo: la ficha de cada legislador (no solo los rebeldes)
Valle aclaró algo importante que habíamos entendido al revés: el objetivo no era medir solo a los legisladores rebeldes — eso era un *ejemplo* de para qué sirve mirar a cada uno individualmente. Lo que hace falta es la **base de datos de los legisladores**: una ficha por cada diputado y senador que haya votado en estos 25 años.

Eso quedó construido hoy: 1.294 fichas. Cada una dice quién es, por qué provincia entró, en qué años estuvo, por qué bloques pasó (y en qué orden), cuánto asiste a las votaciones, cómo suele votar y —ahora sí, como un dato más de la ficha— qué tan seguido se aparta de su bloque. Como control de calidad miramos casos conocidos y dan bien: por ejemplo, la ficha de Carrió muestra su famoso ausentismo (asistió a menos de la mitad de las votaciones de su época) y la de Pichetto lo sigue por sus 25 años y sus dos cámaras.

Para que nadie vuelva a confundir la parte con el todo, dejamos la aclaración escrita en los tres lugares donde un compañero (humano o Claude) podría tropezar: el documento de la decisión, la carpeta del "termómetro de rebeldía" y la carpeta nueva de fichas. Regla de la casa: ningún archivo suelto sin explicación.

Igual que antes: los números salen de la historia 2001–2014 más 2026; cuando se corra la reconstrucción completa desde una PC con internet, las fichas se recalculan solas con los años que faltan.


## Confirmado con la historia completa: las bisagras existen y hoy son más que nunca
Valle corrió la reconstrucción completa desde su PC y ahora los números cubren los 25 años con todas las fuentes. La foto final: el legislador típico se aparta de su bloque menos de 1 vez cada 100 votos, y los realmente díscolos son un grupo chico e identificable. Pero lo más llamativo es QUIÉNES encabezan la lista: casi todos son de los últimos cuatro años (Monzó, Massot, Manes, Arrieta…), con tasas de rebeldía del 30% al 58%. Y la regla "votá con tu bloque", que históricamente acertaba 97-98 de cada 100 en votaciones peleadas, en 2024–2025 cayó a 92-95 — su peor momento desde la crisis de 2002. Traducción: el Congreso actual es el más indisciplinado en dos décadas, y una herramienta que mira legislador por legislador vale más hoy que nunca. Una precaución anotada: algunas tasas altísimas pueden ser en parte un error de etiqueta (legisladores que cambiaron de bloque y la fuente los sigue contando en el viejo); está en la lista de cosas a revisar antes de usar esto en serio.


## Ajuste importante: medimos por período parlamentario, no por carrera
Valle marcó un error de concepto: veníamos resumiendo a cada legislador con un solo número para toda su carrera ("desde 2001 hasta 2026"). Pero el Congreso se renueva cada dos años (el 10 de diciembre de los años impares), y cada renovación cambia la composición de las bancas: un mismo diputado puede ser disciplinado en un período y rebelde en el siguiente, porque cambió el contexto, su bloque o su relación con la conducción. Incluso los reelectos empiezan de cero en un tablero distinto.

Ahora todo se mide período por período: el Excel tiene una hoja nueva (PorPeriodo) donde cada fila es "este legislador, en este período de dos años, en esta cámara: votó tanto, faltó tanto, se desvió tanto de su bloque". La ficha resumen sigue existiendo para la vista rápida, pero el análisis fino se hace sobre esa hoja. También dejamos aclarado que las columnas "año desde/hasta" indican actividad observada en nuestros datos, no el mandato formal — para el mandato exacto falta cruzar con el padrón oficial, que quedó en la lista de pendientes.


## Regla nueva: los Excel se explican solos
A pedido de Valle, todos los Excel que generemos van a arrancar con una hoja llamada "Metodologia": un pequeño diccionario que dice qué significa cada columna de cada hoja, en lenguaje claro, más las definiciones importantes (qué es un período parlamentario, qué cuenta como "desvío", por qué una celda vacía no es un cero). La idea es que cualquier persona que abra el archivo dentro de seis meses —o un compañero que lo recibe por primera vez— entienda todo sin preguntar ni leer código. Ya está aplicado al Excel de legisladores y quedó como regla escrita para todos los que vengan.


## La próxima gran pieza: qué vota cada legislador según el tema
Valle explicitó algo que estaba a medias en el plan: las páginas que siguen al Congreso ya muestran el consolidado de votos a favor y en contra de cada legislador. Nuestro diferencial es cruzar eso con el catálogo de temas que armamos (las taxonomías): poder decir "este diputado aprueba casi todo en materia laboral, pero rechaza sistemáticamente lo tributario". Todavía no se puede calcular porque faltan dos piezas que ya están en marcha: que el agente lector de PDFs termine de etiquetar los proyectos por tema, y conectar cada votación con su proyecto de ley. Cuando esté

## Cambio práctico: los resultados ahora viajan con el repo (por ahora)
Hasta ahora los archivos de resultados (los CSV de disciplina y el Excel de legisladores) no se subían a GitHub: cada uno los regeneraba en su máquina. Valle decidió que, mientras el sistema está en construcción, es más práctico que viajen con el repo — así cualquiera del equipo los abre directo después de un pull, sin correr nada. Quedó marcado como transitorio: cuando el sistema esté funcionando solo (con el bot actualizando la base), volvemos al régimen anterior. Ojo con un detalle: el que re-corra los scripts debe subir también los resultados regenerados, para que en GitHub no quede una versión vieja.


## Nuevo: un tablero de control para saber dónde estamos parados (sin leer 40 archivos)
El plan original del proyecto vivía en un Word y el estado real vivía repartido entre bitácoras. Ahora hay un solo lugar que junta las dos cosas: **TABLERO-CONTROL.html**, en la raíz de la carpeta — doble click y se abre en el navegador, sin internet ni instalación. Tiene el plan completo de la plataforma (los 4 módulos del producto, las etapas, hasta el presupuesto), el semáforo de los 27 módulos del repo, las métricas clave, la línea de tiempo de hitos y qué falta, en ese orden de prioridad. Todo en lenguaje llano, con el detalle técnico escondido detrás de un click. Regla nueva para todos (Claudes incluidos): cuando cambiás algo del proyecto, actualizás el archivo de datos del tablero (`tablero_datos.js`) igual que actualizás esta bitácora — es un archivo de texto simple donde solo se cambia el estado, la fecha y se agrega el hito. El diseño no se toca nunca, así nadie lo puede romper.


## Quiénes NO cuentan para el índice de indisciplina (y la herramienta que falta)
Valle definió las excepciones: al presidente de la Cámara de Diputados (que por costumbre no vota), a los suspendidos (como De Vido, que no PUEDE votar) y a los legisladores con licencia no corresponde contarles la silla vacía como rebeldía — no es una decisión libre. Los dos primeros ya quedaron excluidos automáticamente. Las licencias son el problema: no figuran en ningún dato que tengamos hoy. Quedó anotado como módulo futuro crear una herramienta que detecte y avise cuándo un legislador pide licencia o es suspendido (mirando resoluciones de cámara y Boletín Oficial), para mantener el índice limpio hacia adelante.

Nota de coordinación: en el cruce con el trabajo de Franco (su tablero de control nuevo) se pisó un archivo nuestro sin subir y hubo que reconstruirlo. Moraleja para el equipo: subir el trabajo a GitHub apenas se termina una sesión, antes de traer lo del otro.


## Avance: la "bolsa de los sin familia" se achicó a menos de la mitad
Casi la mitad de los votos históricos estaba etiquetada como "OTRO / PROVINCIAL" — una bolsa donde convivían el peronismo no kirchnerista, el socialismo y los partidos provinciales de verdad. Con el criterio de Franco la desarmamos: nacieron dos familias nuevas (**Peronismo Federal**, el peronismo que no responde al kirchnerismo — de Reutemann a los Rodríguez Saá — y **Progresismo** — socialistas, Stolbizer, Solanas), y resolvimos un caso de manual: el bloque "Justicialista" a secas, que según el año fue tres cosas distintas (el PJ de Duhalde, el oficialismo de Néstor y Cristina, o los disidentes de Pichetto). Ahora cada voto se asigna según la FECHA. La bolsa pasó del 45% al 19%, y lo que queda adentro es provincial genuino. Esto le da al medidor de díscolos del equipo (desvío v2) unos 200 mil votos más de universo para desempatar. Cada asignación se verificó contra los datos antes de decidirla, y todo quedó documentado y reversible.

## Avance: el diccionario de temas aprobó su examen, y llegó el "clima político"
Antes de pagar por clasificar miles de proyectos con inteligencia artificial, hicimos la prueba barata: tomamos 88 votaciones reales de los últimos 25 años y les pusimos tema A MANO usando nuestro diccionario de 74 temas. Aprobó: 8 de cada 10 se pueden clasificar bien con solo leer el título, y la mayoría con confianza alta. La prueba también dejó la lista de retoques: faltan unos pocos temas (el más repetido: el control del Congreso al Ejecutivo — DNU, interpelaciones, pedidos de informes) y hay que fijar 4 reglas para casos limítrofes (¿un juicio político es "justicia" o "política"?). Con esos ajustes, el agente clasificador puede correr en serio, y esta muestra manual queda como examen de referencia para medir si la IA coincide con el criterio humano.

Además quedó listo el programa que trae el **Índice de Confianza en el Gobierno** de la Universidad Di Tella (mensual, desde 2001): el "clima político" que mide cuánto respaldo tiene el gobierno de turno — y por lo tanto cuánto cuesta oponérsele en el recinto. Di Tella no ofrece una conexión automática, así que el programa lee la página oficial de descargas (el archivo cambia de nombre cada mes) y tiene un plan B por si el sitio se cae.

## Cierre del día: el ICG ya está adentro (con anécdota) y con actualización mensual automatizable
La primera corrida en la PC de Valle destapó que el Excel de Di Tella tiene un formato rebuscado (las fechas en una fila y los valores abajo, partido en dos hojas). Se arregló el lector y quedó verificado: **296 meses, de noviembre 2001 a junio 2026, sin ningún hueco**, con los últimos valores idénticos a los informes oficiales. Además, a pedido de Valle, quedó el modo "último": un comando que lee la página de informes de Di Tella (que publica el mes nuevo ANTES de actualizar el Excel) y agrega solo lo que falta, sin duplicar aunque se corra dos veces. Es la pieza que el futuro bot va a poder invocar todos los meses. Con esto, la familia "clima político" del feature store ya tiene su primera serie viva.
a, fue peor. Pero al separarlos aprendimos algo importante:
- **Leer la postura del bloque mirando solo a los que estuvieron presentes**: bien, mejora el motor. Se queda.
- **Suponer que cada legislador asiste "su promedio" a toda votación**: mal. Mete ausencias falsas — en una votación que de verdad ocurrió, la gente fue más que su promedio (justo por eso hubo votación).

La moraleja, que fue el aporte de Valle: **la asistencia no es un promedio, depende del proyecto**. Un legislador falta cuando el tema lo incomoda, o cuando lo presenta su oposición. Para modelar eso primero hay que saber de qué es cada proyecto y quién lo impulsa.

## El plano de los datos: la "ficha de rasgos" de cada proyecto
De ahí salió la decisión de frenar y **dibujar el mapa antes de seguir**: qué sabe (o debería saber) el sistema de cada proyecto de ley. Quedó diseñado en papel el **feature store** (`FEATURE-STORE.md`): la ficha de rasgos de cada proyecto y a qué parte de la predicción alimenta cada uno. Los rasgos van desde lo básico (tema del proyecto, en qué comisiones está) hasta lo político (¿lo presenta el oficialismo o la oposición?, ¿cómo está el clima con el índice de confianza en el gobierno de Di Tella?, ¿se vienen elecciones?). La idea de fondo: casi todo en política es **condicional al tipo de proyecto**, y este mapa es lo que va a permitir que el sistema entienda esas diferencias. El primer paso concreto que habilita todo lo demás es poner a andar el **agente que le pone temas a cada proyecto** leyendo su texto.


## Auditoría cerrada: los "rebeldes" del Senado son de verdad
Quedaba una duda colgada: 17 senadores cuyos bloques habíamos inferido a mano llevaban la marca "revisar", y una de ellas (García, de Santa Cruz) aparecía altísima en el ranking de díscolos — ¿era rebelde de verdad o le habíamos puesto el bloque equivocado? Revisamos las 17: catorce votan casi calcado a su bloque (etiqueta correcta, caso cerrado) y los tres de desvío alto resultaron ser lo mejor del hallazgo: García se desvía exactamente igual que todas sus compañeras camporistas — en las leyes de la era Macri (la reforma previsional, la de emprendedores), el ala cristinista del bloque votaba NO mientras la conducción de Pichetto acompañaba. O sea: no había ningún error de etiqueta — el sistema estaba detectando una fractura política real dentro del bloque, que es exactamente para lo que lo construimos. El padrón queda certificado al 100% y el medidor de díscolos del equipo, con luz verde.


## Avance grande: ahora sabemos TODO lo que se presentó (no solo lo que se votó)
Hasta hoy la base conocía las votaciones — la punta del iceberg. Ahora tiene el iceberg entero: 112.793 proyectos presentados desde 2008, con quién los presentó, a qué comisiones fueron girados, si consiguieron dictamen y en qué terminaron. Ahí apareció el número que justifica todo el enfoque del embudo: de cada 100 proyectos de ley que se presentan, se sancionan 3. Y el dato más elocuente: en 18 años hubo solo 4 proyectos RECHAZADOS formalmente — el Congreso casi nunca dice que no: simplemente deja que los proyectos mueran en un cajón. Predecir ESO (qué proyectos salen del cajón) es el corazón del Nowcast. De yapa: el enlace entre cada votación histórica y su expediente (para ponerle tema a las votaciones de título críptico) y los integrantes de cada comisión. Quedó anotada la idea de Franco para el paso siguiente: un robot diario que lea los boletines oficiales de ingreso de ambas cámaras (ahí están todos los firmantes y giros de cada día, en un solo documento) para mantener el padrón vivo.


## Deuda saldada: el Senado 2024-2025 ya tiene bloque (y era el período que más importaba)
Desde el primer día, los votos del Senado de 2024 y 2025 estaban huérfanos: la fuente no decía de qué bloque era cada senador. Ahora el sistema les pregunta a nuestro propio padrón histórico, y los 20 senadores que ni Wikipedia tenía salieron del Excel curado de Franco (proyectado hacia atrás con cuidado: a cada uno se le puso el bloque que tenía EN ESA ÉPOCA, no el de hoy). Resultado: cero votos sin bloque en el Senado, y el medidor de disciplina ganó dos mil votos justo en los años donde la disciplina se está aflojando — el período más valioso para el modelo. De paso encontramos y corregimos un descuido propio: dos nombres internos del kirchnerismo en el Senado ("Unidad Ciudadana" y "Frente Nacional y Popular") estaban cayendo en la bolsa de "sin familia". La bolsa quedó en 17% — empezó la semana en 45%.


## Nació el robot del padrón vivo (por ahora, la mitad senatorial)
La idea de Franco tomó forma: en vez de que el sistema se entere de los proyectos nuevos cuando alguien corre un script a mano, un robot diario lee el "diario de entradas" oficial de cada cámara. La mitad del Senado ya está construida: el DAE Digital publica cada proyecto que entra con su expediente, sus giros a comisión y su resumen, numerado en secuencia — así que el robot solo recuerda el último número que vio y pide los que faltan, como quien retira el correo. Probado en seco con 13 chequeos. Falta la mitad de Diputados (su "Trámite Parlamentario"), que se explora desde la compu de Franco porque a la mía ese sitio no le responde. Cuando ambas mitades estén, el sistema va a saber de cada proyecto nuevo el mismo día que entra — con todos sus firmantes, no solo el primero.


## El robot ya no necesita que nadie lo despierte
Doble hito. Primero, el estreno: en su primera corrida real, el robot del Senado trajo los 51 diarios de entradas del año — 1.004 proyectos con sus giros y resúmenes — en un minuto, y se acordó de dónde quedó: mañana solo va a pedir lo que falte. Segundo, y más importante: por decisión de Franco el robot ya no corre en la compu de nadie — quedó programado en GitHub (el mismo lugar donde vive el código), que lo despierta solo cada mañana de lunes a sábado. Si encontró proyectos nuevos, los guarda en el repo y cualquiera del equipo los recibe con un simple pull; si no hay nada, no toca nada. Es la primera pieza del sistema que funciona completamente sola — el embrión de la plataforma automatizada del plan original, sin haber alquilado un solo servidor.


## El robot ya escucha a las dos cámaras (y trae las firmas completas)
Se completó la otra mitad: el robot ahora también lee el Trámite Parlamentario de Diputados — el boletín donde la Cámara publica cada proyecto presentado. Y ahí está el dato que veníamos persiguiendo: la lista completa de quiénes firman cada proyecto, no solo el primer autor. Esas co-firmas son la materia prima de dos módulos enteros del plan (el mapa de influencia y el espectro ideológico real: quién firma con quién dice más que el bloque al que pertenecen). Probado contra páginas reales con 13 chequeos. Desde mañana, GitHub despierta al robot y éste revisa ambas cámaras solo. Yapa: descubrimos que el boletín tiene archivo histórico hasta 2019 — cuando queramos, el robot puede leer hacia atrás y reconstruir las redes de firmas de los últimos siete años.


## Arrancó el "embudo": adivinar qué proyectos salen del cajón
Hasta ahora sabíamos el número grueso: de cada 100 proyectos de ley, terminan siendo ley 3. Hoy empezamos a abrir ese número y a convertirlo en una predicción. Dos cosas.

Primero, medimos el **embudo por etapas**: cuántos proyectos pasan de presentados a ser girados a comisión, de ahí a conseguir dictamen, de ahí a llegar al recinto, y de ahí a ser ley. Ahí se ve dónde mueren: la enorme mayoría se queda sin dictamen (nunca sale de la comisión). Lo abrimos por año, por cámara y por comisión, así se ven las comisiones "cementerio" (donde los proyectos entran y no salen) frente a las rápidas.

Segundo, un **modelo que estima la probabilidad de que cada proyecto llegue al recinto y de que se convierta en ley**, usando solo lo que se sabe el día que el proyecto se presenta (a qué comisiones fue, quién lo firma, en qué año, si es año electoral). Que use solo eso es clave: si le diéramos datos del futuro —como "consiguió dictamen"— estaríamos haciendo trampa y el número sería mentira. Para chequear que sirve de verdad lo probamos "a ciegas": lo entrenamos con los años viejos, le pedimos que adivine un año que no vio, y comparamos con lo que realmente pasó.

Dos recaudos de cocina: (1) los proyectos de ley caducan si no avanzan, así que para medir bien no contamos como "muertos" los proyectos recientes que todavía están vivos —solo evaluamos los que ya tuvieron tiempo de resolverse—; (2) el modelo ya deja "enchufes" listos para cuando tengamos el tema de cada proyecto y si lo presenta el oficialismo o la oposición, que son los datos que más van a mejorar la predicción.

Como siempre: yo dejé el programa escrito y probado con datos de mentira (18 chequeos), y la corrida final con los ~40 mil proyectos reales la corrés vos en tu PC, porque es pesada.

**Resultado de la corrida (mismo día): el modelo aprobó.** Sobre los 41.339 proyectos de ley presentados desde 2008, el embudo por etapas dejó clarísimo dónde está el cuello: todos los proyectos se giran a comisión, pero **solo el 8% consigue dictamen** — ahí se muere el 92%. Y una vez que un proyecto logra dictamen, la cosa cambia: 6 de cada 10 llegan al recinto y 7 de cada 10 de esos se convierten en ley. Traducción política: la pelea de verdad no es en la votación, es en conseguir que la comisión saque dictamen. En total, de 100 proyectos de ley llegan al recinto menos de 5 y se sancionan 3. Y lo más importante: el modelo que adivina esto "a ciegas" (entrenado con años viejos, probado en años que no vio) le gana claramente a tirar la moneda con la tasa promedio — reduce el error un 34-39% y ordena casi perfecto cuáles proyectos van a prosperar. Con una honestidad: parte de ese "casi perfecto" es fácil, porque la enorme mayoría de proyectos están muertos desde que entran y son sencillos de descartar; el salto fino vendrá cuando le sumemos el tema de cada proyecto y si lo empuja el oficialismo o la oposición.


## Puesta en marcha: por fin sale un número de aprobación para un proyecto
Hasta hoy teníamos las piezas sueltas; ahora las juntamos. La probabilidad de que un proyecto se apruebe se arma multiplicando dos cosas que ya sabíamos calcular por separado: **la chance de que el proyecto llegue a votarse** (el embudo) por **la chance de que, ya en el recinto, junte los votos** (el agregador, con sus reglas de quórum y mayorías). Multiplicar esas dos da la foto completa.

Lo lindo es que el resultado no es un número solo, sino que **muestra de dónde viene**. En la prueba que corrimos, un proyecto tenía 58% de chances de ganar la votación si llegaba al recinto… pero solo 12% de llegar. Resultado final: 7% de aprobación. Sin descomponerlo, ese 7% parecería "no tiene chance"; descompuesto, se ve que el cuello de botella es la comisión, no la votación —y eso es información accionable: si querés que avance, la pelea es sacarlo de comisión, no convencer diputados en el recinto. Además el sistema dice cuántos votos afirmativos espera y con qué margen (en la prueba, 109-110 votos contra un umbral de 109: una votación al filo, justo las que importan).

Cómo se usa: le das el proyecto (de ahí saca su chance de llegar al recinto) y una foto de cómo se va a plantar cada bloque, y te devuelve la tarjeta. Una honestidad importante: hoy la postura de cada bloque se la ponemos a mano (o la tomamos de una votación que ya pasó). El paso que falta para que sea totalmente automático es un módulo que **adivine solo la postura de cada bloque según el tema del proyecto** —eso queda para lo próximo—. Pero el circuito completo, de un proyecto a un número de aprobación explicado, ya está andando.


## No todos los proyectos son iguales: quién lo firma cambia todo
Valle marcó algo clave: un proyecto del Gobierno (el Poder Ejecutivo), uno de un jefe de bloque del oficialismo y uno de un diputado de a pie de la oposición NO tienen la misma suerte, aunque traten el mismo tema. El de a pie casi siempre muere en un cajón; el del Gobierno tiene otra llegada. Así que ahora el sistema etiqueta cada proyecto por **quién lo empuja**.

Dos etiquetas nuevas por proyecto. La primera, **el origen**: si lo manda el Poder Ejecutivo (eso ya venía marcado en los datos), o si el legislador que lo firma era del oficialismo o de la oposición *en ese momento* —y ojo con "en ese momento", porque el mismo diputado fue oficialista con un gobierno y opositor con el siguiente; para eso miramos qué bloque tenía en la fecha del proyecto y quién gobernaba entonces (Cristina, Macri, Alberto, Milei)—. La segunda, **si el que lo firma es un "líder"**: un jefe de bloque, un presidente de comisión, o alguien con muchas leyes propias ya aprobadas (un "peso pesado" legislativo). Para no hacer trampa, lo de "muchas leyes" se cuenta solo con las que consiguió ANTES del proyecto que estamos mirando.

Con esto, el embudo ahora se puede leer **por tipo de proyecto**: cuánto sobrevive lo del Gobierno vs. lo del oficialismo vs. lo de la oposición, y cuánto ayuda que lo firme un líder. Y el modelo que predice usa esas etiquetas como pistas.

Una aclaración honesta: la lista de "jefes de bloque" hoy es apenas una semilla de unos pocos nombres (armar el listado completo de jefes de bloque de los últimos 18 años es un laburo aparte, que quedó anotado para el equipo de Franco, junto con la decisión de qué cuenta exactamente como "líder", que por ahora dejamos así para avanzar). Como siempre, el programa quedó escrito y probado con datos de mentira; la corrida con los proyectos reales la hacés vos.

## Puesta en marcha con la cámara REAL: quién ocupa cada banca hoy
Al enchufar el módulo de bloques al motor apareció un problema de base, medio invisible pero grave: el sistema **no sabía quién ocupa cada banca hoy**. Para armar el escenario de una votación contaba "bancas" mirando quién había votado en los últimos dos años. Pero como el Congreso renueva la mitad cada 10 de diciembre, esa cuenta mezclaba al que se fue con el que llegó y daba **375 diputados… cuando hay 257**. Con una cámara inflada, los umbrales y el quórum salen mal y el pronóstico se distorsiona.

Valle marcó el camino correcto: no arreglarlo con un promedio por bloque, sino armar el **padrón oficial a nivel de cada legislador** —que además es el corazón del proyecto, porque lo que define una votación peleada son diez o veinte personas concretas, no el promedio del bloque—. Así nació un módulo nuevo, **datos/padron**: la nómina oficial con **cada diputado y senador, su provincia, su bloque y las fechas de su mandato**. Quedaron cargadas las dos cámaras de hoy: **257 diputados** (incluye a los que asumieron en diciembre de 2025) y **72 senadores**. Cada legislador queda con una "clave" que permite cruzarlo con su historial de votos y su nivel de desvío.

La idea que ordena todo: la **foto** de la cámara (quién está sentado hoy) sale del padrón oficial; el **comportamiento** (cuánto se desvía cada espacio, qué tan cohesionado vota) sigue saliendo de la historia. Dos cosas distintas, cada una de su fuente.

Con eso enchufado, por primera vez el circuito completo corrió sobre un proyecto de verdad, el **1167-D-2025** (una reforma laboral): 15% de probabilidad de llegar al recinto, mayoría prácticamente asegurada si llega, y **15% de aprobación final**, con unos 137 votos esperados sobre un umbral de 123, ya con la cámara de 257 bien contada. 

Lo honesto que falta: la "dirección" de cada bloque todavía es la de su promedio reciente (por eso da mayoría casi segura); el siguiente paso es que esa postura dependa del **tema y de quién impulsa** cada proyecto. Y hay un detalle a resolver con Franco: cuatro bancas de la izquierda y algunos bloques federales del Senado, por cómo se escriben sus nombres en 2025, hoy caen en la bolsa "otros/provincial" — se arregla ampliando el diccionario de bloques (que es un contrato compartido, así que se decide en equipo).

## Caso testigo: probamos un proyecto en las DOS cámaras y quedó clarísimo qué falta
Le hicimos al sistema la pregunta completa: ¿qué chance tiene 1167-D-2025 (una reforma laboral) de conseguir **media sanción** en Diputados y después **sanción completa** en el Senado? Para aislar el motor de recuento, imaginamos que el proyecto ya llegó a los dos recintos (salteamos el "embudo" de las comisiones).

El sistema respondió: media sanción prácticamente asegurada (137 votos sobre un umbral de 123 en Diputados) y Senado también (61 de 72). O sea, ley cantada: casi 100%.

Y **ese "casi 100%" es justo la lección**, porque es irreal para una reforma laboral polémica. Lo que pasa es que hoy el sistema asume que **cada bloque vota como su promedio reciente**, y como en la historia "lo que llega al recinto casi siempre se aprueba", termina poniendo "a favor" a casi todos **sin leer de qué trata el proyecto**. Por eso el Senado da una paliza de 61 a 11 que en la vida real no ocurre en un tema que divide.

Lo bueno, que quedó demostrado: el motor **cuenta bien la estructura** de las dos cámaras —las bancas reales (257 y 72), el quórum, los umbrales y la incertidumbre— y **encadena** correctamente las dos votaciones (sanción = pasar en las dos). Lo que todavía **no** hace es leer el proyecto para inclinar las posturas.

Ese es el próximo gran paso (lo llamamos **v2**): que la postura de cada bloque dependa del **tema** y de **quién impulsa** el proyecto. Es lo que convierte ese "61 a 11" irreal del Senado en lo que de verdad pasa: una pelea que se define por las ~27 bancas de provinciales y radicales que son el fiel de la balanza, muchas veces por dos o tres votos. Este par de números (Diputados 137/123 · Senado 61/33) queda guardado como **caso testigo**: cuando el v2 esté, vamos a poder medir el antes y el después sobre el mismo proyecto.

## Avance: el motor ya LEE de qué trata la ley (y la postura de cada bloque deja de ser "vota su promedio")
El caso testigo de la reforma laboral (1167) había dejado el problema a la vista: el sistema daba ~100% de aprobación porque cada bloque "votaba su promedio reciente" sin mirar el TEMA del proyecto — y como casi todo lo que llega al recinto se aprueba, casi todos quedaban a favor. Lo arreglamos con dos piezas que encajan.

Primero, un atajo barato para los temas: en vez de leer los 112.000 PDF de todos los proyectos, clasificamos por su TÍTULO las ~890 votaciones que REALMENTE ocurrieron (lo único que el motor necesita para condicionar), usando el clasificador de IA que ya estaba listo. Sin descargar PDFs, con el modelo más barato, cuesta centavos.

Segundo, el "proyector de bloques" ahora condiciona la postura al tema y al origen del proyecto: para decidir cómo va a votar un bloque una ley económica, mira sólo sus votaciones ECONÓMICAS pasadas, y las mezcla con su promedio general con cuidado (si de ese tema hay sólo dos o tres antecedentes, no le cree del todo). Se ve clarísimo con datos reales de 2019, con Macri en el gobierno: la oposición kirchnerista, que en el promedio ciego figura 74% a favor, condicionada a temas económicos cae a 47% = EN CONTRA — lo que de verdad hacía. Y si no se le pasa ningún tema, el resultado es idéntico al de antes, así que no rompe nada. Falta un paso para encenderlo del todo: correr la clasificación de esos 890 títulos con la clave de la API (liviano, va en la compu de Valle).

## Avance: volvimos el motor al cimiento (mide legislador por legislador) y probamos que el ORIGEN endereza el caso que estaba al revés
Dos cosas en esta tanda. Primero, corregimos un atajo viejo: el motor, en el último paso, agarraba el promedio de cada bloque y lo repetía tantas veces como bancas —tratando a los 257 diputados como 7 promedios fotocopiados—, justo lo contrario del cimiento del proyecto (medir a cada legislador y que el conjunto surja de las partes). Ahora el nowcast arma la lista real de legisladores vigentes según el padrón oficial y le pone a cada uno SU propia tasa de "cuánto se aparta de su bloque"; sólo cuando alguien no tiene historial (por ejemplo la camada que asumió en diciembre) usamos el promedio del bloque como red. Sacamos también la demo y el modo "escenario a mano", que ya no hacían falta.

Segundo, resolvimos lo que había quedado pendiente la vez pasada: etiquetar cada votación con QUIÉN impulsa la ley (el Ejecutivo, un legislador del oficialismo o de la oposición) y bajo qué gobierno se votó. Con eso, al re-correr la reforma laboral del gobierno (1167) pidiéndole al modelo que mire sólo las votaciones impulsadas por el gobierno, el signo se acomodó: La Libertad Avanza pasó a estar A FAVOR (de 0,33 a 0,88) y el kirchnerismo EN CONTRA (de 0,85 a 0,44), como en la realidad. Lo hicimos sin gastar en clasificar PDFs: se cruzan los datos de expedientes que ya teníamos. Además dejamos una regla fina para no mezclar épocas: un mismo bloque es oficialista en un gobierno y opositor en el siguiente, así que al condicionar por origen el modelo sólo mira votaciones del mismo gobierno que la fecha que se está prediciendo. Queda por subir la cobertura del etiquetado (hoy llega al 41% de las votaciones) y hacer que el modelo tome el origen del propio proyecto de forma automática.

## Avance: mejoramos mucho el etiquetado del Senado y, al hacerlo, descubrimos dónde está el verdadero cuello
Ayer el Nowcast del Senado daba un número que no había que creer. Hoy atacamos una de las causas: la mitad de las votaciones del Senado (sobre todo las viejas, 2004-2014) no tenían identificado quién impulsaba la ley. Encontramos que ese dato SÍ estaba, escondido dentro del título de cada votación (un código tipo "PE-608/03"), y lo extrajimos. Con eso, el etiquetado del Senado pasó del 21% al 55% y se tapó el agujero histórico; el total del sistema quedó en 59%.

Pero al resolver eso quedó a la vista el problema de fondo del Senado, que era otro: las votaciones recientes (2024-2025) SÍ tienen identificado quién impulsa, pero el sistema no está reconociendo a qué bloque pertenece cada senador actual —los mete a todos en una bolsa genérica ("otros/provinciales")—, así que cuando el modelo quiere ver "cómo vota el kirchnerismo" o "cómo vota La Libertad Avanza" en el Senado, no encuentra historia y se queda neutro. Ese reconocimiento de bloques del Senado reciente es una pieza de la base de datos que maneja Franco; queda anotado como la prioridad para destrabar el Senado. En Diputados esto ya funciona y el modelo distingue bien la política real.

## Avance: destrabamos el Senado — ahora el modelo sí distingue cómo vota cada bloque
Ayer descubrimos que el Nowcast del Senado no servía porque el sistema no sabía a qué bloque pertenecía cada senador reciente (los metía a todos en una bolsa "otros/provinciales"). Hoy fuimos a la raíz: los datos de las votaciones del Senado 2024-2025 venían literalmente sin el bloque cargado. En vez de esperar a que se corrija en la base, lo resolvimos nosotros: cruzamos cada senador con el padrón oficial (que sí tiene su bloque), respetando las fechas de su mandato para no confundir épocas.

El resultado: las votaciones del Senado dejaron de estar todas en la bolsa genérica y se repartieron en los bloques reales (kirchnerismo, La Libertad Avanza, radicales, PRO). Con eso, el Nowcast del Senado ya distingue la postura de cada bloque —lo que ayer era imposible—. Quedan 22 senadores que ya dejaron su banca (en el recambio de diciembre) y que el padrón actual no tiene; los dejamos en una lista aparte para completar a mano y así recuperar el 100%. También le dejamos la propuesta a Franco para que esta corrección quede hecha directamente en la base de datos, que es su lugar natural.

## Avance: le pedimos al modelo que ignore las votaciones de puro trámite al medir la postura de cada bloque
Valle notó algo fino: cuando el modelo miraba "cómo vota cada bloque frente a proyectos del gobierno", daba que todos votan a favor. La razón es que ahí se mezclaban homenajes, tratados internacionales y pliegos —cosas que se aprueban por consenso, casi sin discusión— con las leyes de verdad peleadas. Para distinguirlas usamos las taxonomías (la clasificación por tema de cada votación) y sacamos del cálculo de postura todo lo que es "de trámite/consenso". Así la postura de cada bloque queda medida solo sobre votaciones que realmente marcan posición.

Un aprendizaje honesto: en el Senado esto todavía no cambia el resultado, porque las pocas votaciones sustantivas del gobierno que llegaron al recinto en 2024-25 también fueron cosas que la oposición acompañó — las reformas realmente conflictivas aún no están en los datos. O sea: la mejora es correcta como método, pero la diferencia fina va a aparecer cuando entren más votaciones y cuando etiquetemos las leyes que tocan varios temas a la vez. En Diputados, que tiene más votaciones peleadas cargadas, el efecto ya se ve limpio.


## Chequeo de solapamiento: dos arreglos para el mismo problema, sin choque
El equipo detectó que a los votos del Senado 2024-25 les faltaba el dato de bloque y construyó una solución en su módulo. Nosotros habíamos arreglado exactamente eso el 11 de julio, pero en otro lugar: en la puerta de entrada de los datos. Verificamos si se pisaban: no. Sobre la base actual, su corrector no cambia ni una sola fila — porque cuando los datos llegan ya vienen bien. Queda como red de seguridad (si alguien reconstruye la base con una versión vieja del código, corrige), y dejamos anotada la regla para la próxima: los agujeros de datos se tapan en la entrada, una sola vez, así los ve todo el sistema — y no en cada módulo que los consume, que multiplica el mantenimiento.


## Los "líderes" del Congreso ya no son una suposición
El equipo había definido que un proyecto empujado por un líder tiene más chances de convertirse en ley, y lo midieron: 7 veces más. Pero la definición andaba coja — de las tres señales que la componen, dos estaban en cero por falta de datos. Las dos quedaron destrabadas hoy. Primero, los presidentes de comisión: no figuraban en la lista que usábamos, pero la Cámara publica otro archivo con las autoridades de cada comisión, y ahí están los 46 presidentes con nombre y bloque. Segundo, y más lindo: los jefes de bloque, que dábamos por perdidos porque no existen como dataset. Resulta que la web oficial de Diputados marca "Presidente" al lado del jefe de cada bloque — así que en vez de investigarlos a mano, escribimos un programita que los lee: los 20 bloques actuales, del que tiene 95 diputados al que tiene uno solo. Y como esa página solo muestra el presente, el programa guarda una foto con fecha cada vez que corre: si lo corremos una vez por mes, en un año tenemos la historia armada sola. Para el pasado (2008-2025) sigue haciendo falta investigación humana, pero solo de los bloques grandes: en un monobloque el jefe es el único integrante y la señal no dice nada.


## Quién mandaba en cada bloque, desde 2005
Completamos la lista de jefes de bloque hacia atrás: veinte años de conducciones, reconstruidas de prensa una por una. Ahí está la cadena del kirchnerismo (Rossi durante siete años, Di Tullio cuando él se fue al ministerio, Recalde en los años de Macri, Máximo Kirchner hasta que renunció por el acuerdo con el FMI, y Germán Martínez desde entonces), la del PRO (Pinedo, Massot, Ritondo), la del radicalismo (Negri casi ocho años), y las de los bloques más chicos que igual pesan. Cada nombre lleva su fuente y una marca de cuán seguros estamos. Dejamos fuera a propósito los monobloques viejos: cuando el bloque tiene un solo integrante, decir que es su jefe no informa nada. Un detalle que anotamos para el equipo: el sistema todavía no mira las FECHAS de esas jefaturas — cuenta a alguien como jefe en todos sus proyectos, incluso los que presentó cuando ya no lo era. Los datos para arreglarlo ya están cargados; es el próximo ajuste, y conviene hacerlo antes de volver a medir cuánto pesa el liderazgo, para no darle crédito de más.


## El sistema ya distingue "ser jefe" de "haber sido jefe"
Detectamos y arreglamos un problema silencioso: cuando el sistema marcaba un proyecto como "impulsado por un jefe de bloque", solo miraba el nombre — así que alguien que presidió un bloque entre 2015 y 2019 seguía contando como jefe en los proyectos que presentó en 2023, cuando ya era un diputado más. Ahora mira la fecha. El efecto fue grande: de 1.753 proyectos marcados quedaron 340; los otros 1.413 eran falsos. El caso más claro es el de Graciela Camaño, que figuraba como jefa en sus 376 proyectos y ahora lo hace solo en los 124 que presentó mientras realmente conducía su bloque. La señal quedó mucho más chica, pero por fin dice la verdad. Y eso tiene una consecuencia para el equipo: la conclusión de que "los proyectos de líderes tienen 7 veces más chances" se midió con la señal vieja y contaminada — hay que volver a medirla ahora que el dato es correcto.


## Faltaba el Senado (y ahí estaba el récord)
Franco notó que el listado de jefes de bloque cubría solo Diputados. Al ir a buscar los del Senado apareció una sorpresa buena: esa cámara publica el dato mejor todavía —una columna "Presidente" al lado de cada bloque—, así que el mismo programa ahora lee las dos cámaras de una pasada. Y en la parte histórica apareció el récord del Congreso argentino: Miguel Ángel Pichetto condujo el bloque peronista del Senado durante quince años seguidos, de 2002 a 2017, hasta que él mismo encabezó la ruptura llevándose a 25 senadores. Después Mayans, y en el radicalismo Naidenoff con una década al frente. Una aclaración honesta: estos nombres del Senado casi no mueven la aguja todavía, porque la base de proyectos que tenemos es la de Diputados; van a valer cuando incorporemos los expedientes del Senado —que es justamente lo que el robot ya está juntando todos los días.


## El día que casi metemos 123 asesores como jefes de bloque
Al extender el lector de jefes al Senado, el programa avisó que había encontrado 123 bloques. El Senado tiene catorce. Esa desproporción fue la que delató el error: la página del Senado mete, dentro de la fila de cada bloque, una tablita con el personal y los asesores — y el programa la estaba leyendo como si cada empleado administrativo fuera el presidente de una bancada. Se corrigió con tres controles (un bloque de verdad tiene un número de integrantes, no una categoría de empleado), se borraron las filas falsas y se volvió a capturar: ahora sí, catorce bloques reales. La moraleja quedó anotada para todos los recolectores del proyecto: cuando un programa trae muchísimo más de lo que uno esperaría, casi siempre está trayendo basura. Es la alarma más barata y más efectiva que tenemos.


## Ampliamos la lista de jefes… y encontramos que el problema era otro
Sumamos jefes de los bloques medianos —el massismo, el peronismo disidente de Solá, el bloque que rompió con el kirchnerismo en 2016, el socialismo de Binner, el GEN de Stolbizer, la izquierda— eligiéndolos por peso real: primero medimos qué bloques movían más votos y recién ahí salimos a buscar sus conducciones. Pero al revisar el resultado apareció algo raro: los años viejos seguían casi vacíos aunque teníamos cargados a sus jefes. La causa no era falta de datos sino un detalle tonto: los registros oficiales escriben el nombre completo ("Recalde, Héctor Pedro") y nuestra lista tenía la forma corta ("Recalde, Héctor"), así que no se reconocían. Arreglado eso, la señal se triplicó: de 465 a 1.238 proyectos. Recalde solo aportó 314 que estábamos ignorando. La moraleja quedó anotada: antes de agrandar una lista, conviene comprobar que lo que ya está cargado se esté usando — duplicamos el trabajo de curación para ganar 103 proyectos, y un arreglo de media hora sumó 773.


## Ampliamos a los provinciales… y descubrimos un falso jefe que valía 610 proyectos
Sumamos las conducciones de los bloques provinciales y federales (el neuquino, el cordobés de Schiaretti, los puntanos de Rodríguez Saá, el salteño de Romero). La señal se disparó, pero antes de festejar hicimos la pregunta incómoda: ¿de dónde viene todo esto? La mitad venía de filas que habíamos marcado como "no confirmadas", y dos personas explicaban el 43%. Fuimos a verificarlas una por una. Una resultó correcta: Alicia Comelli sí presidía el bloque neuquino desde 2008. La otra, no: Ivana Bianchi no era jefa de bloque — era, sencillamente, la diputada que más proyectos presentó en toda la Cámara en 2017. Es decir, el sistema la habría contado como "líder" por algo que ya mide otra variable distinta (la productividad), inflando la señal con 610 proyectos y mezclando dos cosas que queremos mantener separadas. La eliminamos y lo dejamos escrito dentro del propio archivo, para que nadie la vuelva a agregar por error. Quedan quince nombres por confirmar, marcados como lo primero a revisar: el caso Bianchi mostró que una sola fila mal puesta puede ensuciar cientos de casos.


## Regla nueva: lo urgente se lee antes de empezar, siempre
Nos pasó dos veces en el mismo mes: alguien del equipo trabajó sobre datos viejos y construyó algo que ya no hacía falta, y una ficha mal cargada metió cientos de casos falsos en el modelo. Las dos veces el aviso estaba escrito… enterrado entre decenas de anotaciones. Así que ahora hay un archivo aparte, URGENTE, con lo poquito que realmente bloquea o ensucia el trabajo de los demás, y quedó como la primera cosa que cualquiera —persona o asistente— abre al sentarse a trabajar, antes incluso del manual del proyecto. Cuando algo se resuelve, se borra de ahí (queda registrado en la bitácora de siempre): la idea es que ese archivo esté vacío casi todo el tiempo, y que cuando tenga algo, sea imposible no verlo. Hoy arranca con dos cosas: que el equipo vuelva a correr dos programas después de bajarse los cambios —porque el código viaja solo, pero los resultados no— y que revise quince nombres del listado de jefes que quedaron sin confirmar.


## Probamos el modelo con una ley de verdad, y encontramos dos cosas
Franco trajo el proyecto de Ley de Lobby que mandó el Ejecutivo en mayo y pidió que el sistema hiciera el recorrido completo: entenderlo, clasificarlo, calcular sus chances y decir a quién hay que convencer. El resultado es que tiene un 39% de probabilidad de convertirse en ley — doce veces lo normal, pero la mitad de lo que suele conseguir un proyecto del Ejecutivo. Y se define en dos comisiones donde al oficialismo le falta una sola firma ajena para poder dictaminar; hay un diputado radical que está en las dos y las vicepreside, así que una sola persona destraba el camino.

Pero el caso sirvió sobre todo para encontrar dos problemas nuestros. El primero: veníamos diciendo que un proyecto firmado por un líder tiene siete veces más chances. Es falso. Ese número estaba inflado porque casi todos los proyectos del Presidente contaban como "de líder", y los del Presidente se aprueban muchísimo. Cuando comparás peras con peras, el efecto real es de dos veces, y ser jefe de bloque solo, apenas 1,25. Lo tranquilizador es que el número da casi idéntico en el oficialismo y en la oposición, que son mundos distintos: eso indica que ahora sí estamos midiendo algo real.

El segundo problema es más serio y ya quedó anotado como urgente: nuestra base de votaciones se quedó en octubre del año pasado, antes de que asumieran los diputados nuevos. Hubo sesiones extraordinarias en diciembre y febrero y sesiones todo este año, y hay 229 votaciones publicadas que nunca cargamos. Eso significa que el sistema hoy no puede calcular cuántos votos junta un proyecto en el recinto: si le preguntás, te contesta con la Cámara vieja y ni siquiera avisa que está desactualizado.

Y una lección que vale guardar: limpiar los errores del dato de líder no mejoró en nada la capacidad de acertar del modelo. Lo que mejoró fue la capacidad de explicar por qué predice lo que predice — que es, al final, lo que promete el producto.


## Le pusimos ojos nuevos al sistema (y le enseñamos a mantenerlos abiertos)
Ayer descubrimos que nuestra base de votaciones se había quedado en octubre, antes de que asumieran los diputados nuevos. Hoy la pusimos al día: entraron casi novecientas votaciones y ciento ochenta mil votos, y la Cámara que aparece ahora es otra — La Libertad Avanza pasó de tercera a primera minoría, con noventa y cinco bancas contra noventa y tres del peronismo.

Apareció un problema escondido detrás del primero. El sistema contaba las bancas mirando quiénes habían votado en los últimos dos años, y como en ese lapso hubo un recambio, estaba sumando la Cámara vieja más la nueva: daba 383 diputados sobre 257 que existen. Ahora armamos un padrón de verdad, con la fecha en que cada diputado entra y sale de cada bloque, y el conteo da 256. Falta uno, probablemente una banca vacante.

Lo más importante para el futuro es que el bot que corre solo cada mañana ahora también trae las votaciones, no solo los proyectos presentados. Esa era la causa de fondo: teníamos automatizada la mitad del trabajo, y la otra mitad dependía de que alguien se acordara.

Queda una cosa sin resolver, y es del Senado: los senadores que asumieron en diciembre no tienen bloque asignado, porque —curiosamente— ninguna fuente oficial publica a qué bloque pertenece cada senador. Publican el partido por el que se presentaron, que muchas veces es otro. Así que el nowcast de Diputados ya se puede usar y el del Senado todavía no.

Y quedaron anotadas dos decisiones de Franco para más adelante. Una: las leyes grandes que manda el Ejecutivo, tipo Ley Bases, no deberían analizarse como un bloque único, porque cada título tiene su propio tema y su propia suerte — los títulos de reforma política se cayeron mientras otros avanzaban. La otra: fijamos qué tiene que responder el sistema ante cada proyecto nuevo, siempre lo mismo, la probabilidad y a quién hay que convencer. El informe de la Ley de Lobby quedó como el modelo a seguir.


## Qué mira el modelo, y qué todavía no mira
Franco preguntó qué tiene en cuenta el sistema para estimar si una ley va a salir. Hoy mira siete cosas, y casi todas son de trámite: a cuántas comisiones fue girada (lo más determinante de todo), cuáles son esas comisiones, qué tan exitoso fue históricamente quien la firma, si la manda el Ejecutivo o un legislador, si es un jefe de bloque, en qué mes entró y si es año electoral. Nada de eso mide el clima político del momento.

Existe un programa listo para traer el Índice de Confianza en el Gobierno de Di Tella, bien hecho, pero nunca se corrió y el modelo no lo usa. Vale la pena: sería la única variable que capta el contexto político, y probablemente explique cosas que hoy quedan sin explicar — como que el Ejecutivo de Cristina convirtiera el 87% de sus proyectos en leyes y el actual el 42%.

Sobre la banca que faltaba: la encontramos. Es Néstor Pitrola, de Buenos Aires, que asumió el 27 de abril y en la base de donde sacamos los datos figura con fecha de salida el mismo día que entró. Hay otro caso, Matzkin, que directamente no aparece. Intentamos corregirlo automáticamente y salió peor: según cómo lo arreglábamos, terminábamos con 278 o con 263 diputados en vez de 257, porque la fuente no permite distinguir a quien asumió de quien se fue. Así que preferimos dejarlo como está y avisar: falta una banca real en lugar de inventar seis. El arreglo de verdad es usar la nómina oficial de la Cámara.

También apareció un detalle técnico que conviene recordar: usábamos el año 9999 para decir "mandato sin fecha de fin", y resulta que la herramienta de cálculo no soporta fechas más allá del año 2262 — así que esos registros se volvían invisibles. Ya está corregido.


## Lo que queda para la próxima
Franco revisó las variables que usa el modelo y no le cerraron varias. Quedó anotado como lo primero a mirar, y con razón: la más importante de todas —a cuántas comisiones fue girado el proyecto— podría estar haciendo trampa sin que nos diéramos cuenta. Si los giros se agregan después de que el proyecto se presenta, entonces el modelo está espiando el futuro, y buena parte de su aparente puntería sería falsa. Es verificable y hay que hacerlo antes de seguir construyendo encima.

También quedó anotado conectar el índice de confianza en el gobierno, que daría al modelo lo único que hoy le falta: alguna noción de cómo está el clima político.

Y una idea de Franco que cierra un círculo: que el bot revise cada tanto la lista de diputados para avisar si alguien renunció, asumió o se cambió de bloque. Hoy los proyectos y las votaciones entran solos, pero la composición de la Cámara todavía depende de que alguien se acuerde de mirarla — que es exactamente el tipo de olvido que nos costó nueve meses de votaciones sin cargar.


## Le dimos al modelo su primera variable de clima político (y midió menos de lo que esperábamos)

Faltaba enchufar el índice de confianza en el gobierno, lo único que le daría al sistema alguna noción de en qué momento político se presenta un proyecto. Primera sorpresa: los datos ya estaban bajados desde hace un mes —veinticinco años de mediciones, sin un solo hueco—; lo que nunca se había hecho era conectarlos al modelo. Ya está hecho, con un candado importante: un proyecto presentado en junio ve el clima de mayo, nunca el de junio. Si le dejáramos ver su propio mes, el modelo estaría espiando el futuro, que es justo el problema que estamos investigando en otra variable.

Y acá viene lo honesto: **mejora poco**. Sumar el clima político aporta tres milésimas de precisión, contra las veinticuatro que aportó en su momento saber quién impulsa el proyecto. Es una mejora real y consistente en las dos cosas que el sistema predice, pero es una séptima parte de lo que esperábamos. La lectura: el clima político sirve para afinar el número, no para explicar lo que hoy no se explica. Si el modelo tiene un techo, no está acá.

Lo que sí resultó interesante es la intuición de Franco sobre que importa más la tendencia que el nivel. Se confirmó, y por bastante: si el gobierno viene subiendo o bajando en los últimos tres meses pesa casi seis veces más que dónde está parado hoy. Pero el signo salió al revés de lo esperable —cuando la confianza sube, se aprueban *menos* leyes— y eso puede querer decir dos cosas muy distintas: que un gobierno con viento a favor necesita menos al Congreso, o que cuando la confianza cae el Ejecutivo empuja más. **No lo damos por sabido**: queda anotado para contrastar gobierno por gobierno antes de decir nada en público.


## El sistema ahora se vigila solo (y la banca que faltaba apareció)

Hasta hoy, los proyectos y las votaciones entraban solos, pero saber quién ocupa cada banca dependía de que alguien se acordara de mirar. Eso se terminó: hay un vigilante que corre todos los lunes, baja la lista de legisladores, la compara con la que tenemos guardada y avisa si alguien asumió, renunció, falleció o se cambió de bloque —y, sobre todo, si el total dejó de dar 257 diputados y 72 senadores, que es la alarma más barata y más efectiva que tenemos.

En su primera corrida ya encontró algo. Hace unos días habíamos dado por perdida una banca: el padrón daba 256 sobre 257 y habíamos decidido avisar antes que inventar. El vigilante detectó que dos diputados —Matzkin y Pitrola— ya figuran en la lista oficial y que Ravier dejó su banca. La cámara queda con La Libertad Avanza en 95, el peronismo en 93, cuarenta y seis de bloques provinciales y el resto repartido.

> ⛔ **Corrección del 06-08.** Acá decía que con ellos "el total da **257 exacto**". **No es cierto: da 256**, y nunca dio 257. Lo confirmaron dos cosas el 6 de agosto: el vigilante corriendo por primera vez de verdad, contra la lista oficial en vivo, y una revisión del archivo, que da 256 en todas las fechas de agosto — incluido el 4, el día en que se escribió la frase.
>
> **La banca que falta tiene nombre: Pitrola**, cuyo mandato figura terminado el 27 de abril. Es el único que termina en 2026. O sea que hay una banca **vacante desde hace más de tres meses**, o el reemplazante todavía no aparece en la fuente oficial. Vale confirmarlo, aunque el efecto sobre las cuentas es chico: la mayoría absoluta son 129 votos por ley, no depende de cuántos diputados haya en total.
>
> Vale contarlo porque es la misma historia que este documento viene contando todo el día: **un número que se escribió sin abrirlo, y que después seis documentos repitieron.** Esta vez el que lo repitió fue Claude, al reescribir la lista de urgencias esa misma tarde — copió la frase sin verificarla, mientras redactaba la regla que dice que hay que verificarla.

También se atrapó un error nuestro en el acto, que vale contarlo porque es el tercero de la misma familia. La primera versión avisó que una diputada se había cambiado de bloque; era falso: el nombre del bloque venía escrito completo en un lado y cortado en el otro, y el programa lo leyó como una ruptura política. Ya nos pasó con los ciento veintitrés asesores que entraban como jefes de bloque y con la falsa jefa que valía seiscientos diez proyectos. Un vigilante que grita en falso se termina ignorando, así que ahora compara la familia política real y no el texto: los cambios de tipeo se informan aparte, como lo que son.


## Los avisos automáticos ya tienen dónde correr

Quedaron armadas las tres tareas que ahora corren solas en la nube, sin depender de que tu computadora esté prendida: el bot que trae proyectos y votaciones todas las mañanas de lunes a sábado, el vigilante del padrón los lunes, y la actualización del índice de confianza el día 5 de cada mes. Cada una avisa sola si algo se rompe, y ninguna hace ruido cuando no hay novedades.

Falta un paso tuyo y es importante: **tu carpeta no está conectada al repositorio**. Trabajás sobre una copia suelta, así que ni tus cambios suben ni los del equipo bajan, y mientras eso siga así estas tareas automáticas no existen para GitHub. Quedó escrito paso a paso, con copia de seguridad primero, en `coordinacion/CONECTAR-GIT.md`.


## Encontramos por qué el Senado parecía no tener bloques (y no era cierto)

Esta merece contarse. En la lista de urgencias figuraba, con todas las letras, que los senadores que asumieron en diciembre no tenían bloque asignado y que "ninguna fuente oficial publica el bloque parlamentario del Senado" — con la conclusión de que había que curar setenta y dos filas a mano o salir a buscarlas a Wikipedia.

Es falso. El archivo con los setenta y dos senadores, cada uno con su bloque y su familia política —incluidos los veinticuatro que asumieron el 10 de diciembre— existe y está completo en tu disco desde hace semanas. Lo que pasó es que una regla del proyecto que evita subir archivos de datos pesados se lo tragó, así que ese archivo nunca llegó al repositorio. Cualquiera que mirara el repositorio concluía, con toda razón, que el dato no existía — y se ponía a resolver un problema ya resuelto.

Es la cuarta vez que esa misma regla esconde trabajo hecho, pero es la primera que genera una urgencia falsa y días de investigación al pedo. Quedó arreglado, y el diagnóstico quedó escrito dentro del propio archivo de reglas para que la quinta vez no exista.


## Lo que sigue

La urgencia más grave sigue abierta y es la que Franco marcó primero: la variable más influyente del modelo —a cuántas comisiones fue girado el proyecto— puede estar mirando el futuro. Si los giros se amplían después de que el proyecto se presenta, buena parte de la puntería del sistema es falsa. Es verificable con datos que ya tenemos y es lo próximo, antes de seguir construyendo encima.


## El clima político entró al modelo, y hubo que darlo vuelta tres veces para que funcionara

Teníamos el índice de confianza en el gobierno, que mide desde hace veinticinco años cuánta confianza le tiene la gente al gobierno de turno. Lo habíamos enchufado como una variable más —al lado de "a cuántas comisiones fue girado el proyecto" o "quién lo firma"— y no servía para nada: aportaba cero.

Valle vio por qué: el clima político no es una característica del proyecto de ley, como su tema o su autor. Es el estado del mundo en el que ese proyecto se juega. Estábamos preguntándole al modelo lo que no podía responder. Así que dejó de ser una variable y pasó a ser algo distinto: un factor que **corrige** el resultado, empujando a favor del gobierno cuando la gente lo acompaña y en contra cuando lo rechaza.

Y ahí apareció el hallazgo lindo. Buscamos el efecto en el conjunto de la cámara y no había nada. Pero cuando lo buscamos legislador por legislador, apareció con toda claridad — y apareció justo donde Valle decía que iba a estar: **en los que negocian**.

El sistema mira el historial de cada diputado y calcula cuántas veces se despegó de su bloque en las votaciones peleadas. Con eso los ordena en cinco grupos. Los que casi nunca se despegan —el núcleo duro— no se mueven ni un milímetro por el clima político: votan igual con el gobierno arriba o abajo. Los que se despegan seguido son otra cosa: entre el peor y el mejor momento de un gobierno, su chance de acompañar un proyecto oficial cambia hasta veintitrés puntos.

Lo que da confianza es quiénes son. Nadie le explicó al programa nada de política argentina, solo le dimos los votos. Y ordenó la cámara poniendo arriba a Schiaretti, de la Sota, Massot, Lousteau —los bloques provinciales y federales, los negociadores de siempre— y abajo a La Libertad Avanza, el kirchnerismo y el PRO. Cualquier analista habría hecho la misma lista a mano.

En la cámara de hoy son cincuenta y un diputados los que se mueven con el clima. Los otros doscientos seis, no.


## Lo que el índice no puede decirnos, y cómo lo resolvimos

Hay una parte del efecto que **no se puede medir**, y conviene ser honestos sobre eso.

Uno esperaría que un gobierno con mucha confianza popular tenga más facilidad para aprobar leyes que uno repudiado. Suena obvio. El problema es que en veinticinco años hubo apenas seis presidencias, y dentro de cada una el nivel de confianza es más o menos el mismo. Entonces, cuando el programa intenta separar "había buen clima" de "era el gobierno de Néstor", no puede: para él son el mismo dato.

Así que decidimos no fingir que lo medimos. Ese factor lo **elige una persona**, mirando la coyuntura, y queda registrado con fecha y justificación. Ningún número sale publicado sin ese paso.

Para eso hicimos dos paneles, uno para computadora y otro para teléfono. Se mueven dos perillas —dónde está el índice hoy y cuánto peso le damos— y los doce proyectos de ejemplo se recalculan al instante. Se ve qué proyecto cruza la mayoría y cuál se cae.

La forma de la curva la definió Valle con un razonamiento que después resultó ser un clásico de la psicología económica: la gente no se impresiona con los éxitos salvo que sean notables, pero es muy sensible a las pérdidas. Así que el castigo por caer pesa casi el doble que el premio por subir, y los extremos pesan mucho más que los movimientos chicos.

El caso que ordenó todo fue la Ley Bases. Milei llegó con el índice cerca de 2,8 y aprobó dos leyes enormes y muy resistidas teniendo bastantes menos bancas que hoy. Ningún modelo que mire solo cuántos diputados tiene cada bloque explica eso. Ese es exactamente el fenómeno que este mecanismo tiene que capturar, y quedó como prueba de realidad dentro del panel: si el peso que elegís no le alcanza al oficialismo para pasar la Ley Bases, te estás quedando corto.


## Tres cosas que probamos y no funcionaron

Vale contarlas, porque saber qué no anda es tan útil como saber qué anda.

**La volatilidad.** La idea era que cuando el índice está planchado no hay tracción política y nada prende, y cuando se mueve mucho la sociedad está más permeable a los cambios. Es un razonamiento convincente. Lo medimos y no se distingue de cero. Queda anotado por si con más datos aparece.

**El efecto sobre el conjunto de la cámara.** No existe, o al menos no lo podemos ver. Y encontramos por qué: en una votación típica hay unos setenta votos emitidos, así que aunque quince diputados cambien de opinión eso mueve el resultado un cuatro por ciento, cuando la variación normal entre votaciones es del dieciocho. El promedio de la cámara es un instrumento demasiado grueso para medir algo tan fino. Por eso hubo que bajar al nivel de cada legislador.

**Los saltos del índice en los cambios de gobierno.** Descubrimos que los ocho meses más agitados de toda la serie son ocho de ocho pegados a un traspaso presidencial. Y ahí el índice está midiendo al gobierno que **entra**, no al que está. Si no lo corregíamos, en noviembre de 2015 le habríamos dado viento a favor al kirchnerismo por la aprobación que tenía Macri, que todavía no había asumido. Esos meses ahora se reemplazan por el promedio del gobierno saliente.


## Una corrección que evitó que publicáramos algo falso

Habíamos anotado que los gobiernos con buen clima "llegan sin bancas", porque los números mostraban esa relación. Valle lo frenó: eso no es una relación entre confianza y bancas, es el calendario electoral argentino. Un presidente asume habiendo ganado la elección, pero el Congreso que hereda se eligió en tandas anteriores —los diputados se renuevan por mitades y los senadores por tercios—, así que estructuralmente arranca con pocas bancas. Y arrancar es justo cuando la confianza está más alta, por la luna de miel. Las dos cosas van juntas por el almanaque, no porque una cause la otra.

Estaba escrito en tres páginas y en dos programas. Se sacó de todos lados y se dejó la explicación correcta en el código, para que a nadie se le ocurra volver a escribirlo.


## Revisión general: el proyecto se estaba contando a sí mismo con números viejos

Antes de seguir construyendo, Valle pidió parar y hacer un control general: mirar si lo que las bitácoras dicen del proyecto sigue siendo cierto. Después pidió algo más exigente — mirar **todas las carpetas y todos los archivos, uno por uno**. Son 1.352 archivos y 632 megas.

Aparecieron doce cosas, y lo interesante es que **todas tienen la misma forma**: alguien escribió algo sobre el estado del proyecto sin abrir el archivo. No es descuido de nadie. Es que hoy hay **cinco lugares distintos** donde se declara cómo va el proyecto —la bitácora técnica, el tablero de tareas, este documento, el tablero ejecutivo y el README de cada módulo— y nada obliga a que digan lo mismo. Cuando uno se actualiza, los otros cuatro quedan mintiendo en silencio.

**Las tres que importaban de verdad:**

La primera: **la base de votaciones figuraba con 834.749 votos cuando en realidad tiene 1.016.632.** El crecimiento del 31 de julio se anotó en la bitácora y ahí quedó; nadie lo copió al tablero que mira el equipo. Durante una semana el número más visible del proyecto estuvo 18% por debajo de la realidad.

La segunda: **los dos robots nuevos —el que vigila el padrón los lunes y el que baja el índice de confianza el día 5— nunca corrieron.** Los archivos que los definen quedaron guardados en una subcarpeta, y GitHub sólo los lee si están en la carpeta de más arriba. El tablero los anunciaba como funcionando. La forma de comprobarlo fue simple: si el vigilante del padrón hubiera corrido aunque sea una vez, habría dejado su reporte escrito en una carpeta. La carpeta está vacía. Moverlos son cinco minutos, y el instructivo ya está escrito desde el 4 de agosto.

La tercera: **el archivo que el modelo usa para estimar si un proyecto llega a votarse sigue siendo el del 12 de julio**, generado con un programa que tenía un error. El error se corrigió el 4 de agosto, pero nunca se volvió a generar el archivo. O sea que todo número que sale hoy se apoya en esa versión defectuosa.

**Lo que sí se arregló acá mismo:** los votos del Senado de 2026 entraban a la base sin saber a qué bloque pertenece cada senador — más de seis mil votos, que es lo mismo que decir que el pronóstico de esa cámara estaba a ciegas. Dos veces se había concluido que la culpa era de que ninguna fuente oficial publica esa información. Las dos veces era falso: el listado con los 72 senadores y su bloque existe desde el 14 de julio. La causa real era mucho más aburrida — el programa que carga los datos estaba consultando un padrón que **termina el 9 de diciembre de 2025**, así que todo lo que pasó después del recambio de bancas caía afuera. Se le enseñó a consultar también el padrón nuevo, y ahora los 72 resuelven bien. Falta volver a correr la carga para que el arreglo llegue a los datos.

**Y una que vale la pena contar aparte,** porque es una lección sobre cómo trabajamos: el archivo `URGENTE.md` existe para que lo importante no se pueda no ver. Tenía una sección al final titulada "resueltos" — y adentro de esa sección estaba enterrado, sin resolver, justamente el problema del Senado. Un archivo diseñado para que nada se esconda no puede tener un rincón donde las cosas se esconden. Se eliminó la sección y quedó escrito que no se vuelve a hacer.

Cinco fichas de módulo, además, decían "pendiente, sin dueño" sobre trabajo que está en curso hace meses — incluida la de la base de datos central del proyecto. Eso importa porque la regla de la casa es que antes de agarrar un módulo leas su ficha: una ficha que dice "libre" sobre algo ocupado es el mecanismo para no pisarnos funcionando exactamente al revés.

**Lo que queda para Valle:** cinco corridas en la computadora, en orden. Volver a cargar la base (arregla el Senado y suma 250 votaciones nuevas que el robot ya detectó), regenerar el archivo del embudo, mover los dos robots a su lugar, confirmar el padrón contra la fuente oficial y subir todo. Después de eso el sistema vuelve a apoyarse en datos sanos.


## Le estábamos midiendo la disciplina a los diputados nuevos con dos votaciones
El equipo construyó algo muy bueno mientras no estuvimos: un mecanismo que estima cuánto se mueve cada legislador según cómo esté el clima político. La idea es que el clima no mueve a la Cámara entera, mueve a los negociadores — y el modelo, sin que nadie le diera información política, puso a los bloques provinciales como los más sensibles y a La Libertad Avanza, el kirchnerismo y el PRO como núcleo duro. Eso es exactamente lo que diría un analista.

El problema que encontramos hoy es de dónde saca ese número. Para saber cuán díscolo es un diputado se mira cuántas veces votó distinto de su bloque en votaciones peleadas. Los diputados que asumieron en diciembre llevan dos votaciones peleadas; los veteranos, cuarenta y siete. Y con dos, el resultado solo puede ser "nunca se desvió", "se desvió una vez" o "se desvió las dos" — no hay puntos intermedios posibles. Así, seis diputados nuevos quedaron catalogados como los más díscolos de toda la Cámara por haberse desviado dos de dos veces, y noventa y seis quedaron como disciplina de hierro por no haberse desviado en dos intentos, que es lo más probable que le pase incluso a alguien que en realidad negocia.

La corrección es la que se usa siempre para estos casos y que el propio proyecto ya aplicaba en otra parte: cuando hay pocos datos de alguien, se lo mezcla con el comportamiento típico de su bloque, dándole más peso a su historia propia a medida que acumula votaciones. Con eso ningún diputado nuevo queda ya en el casillero extremo, y los veteranos casi no se mueven, que es justo lo que uno quiere.

Un detalle que casi se nos pasa: al principio mezclábamos a los nuevos con el promedio de su bloque incluyendo a los propios nuevos, y entonces no cambiaba nada — se estaban comparando con el mismo ruido que queríamos corregir. El promedio tiene que salir de los que sí tienen historia.


## La sospecha más grande sobre el modelo: falsa alarma
Franco venía marcando algo que, de ser cierto, tiraba abajo buena parte del sistema. El dato que más pesa a la hora de predecir si una ley va a salir es a cuántas comisiones fue enviada — pesa más que quién la firma, incluso más que si la manda el Presidente. Y ahí estaba la duda: si las comisiones se van agregando con el tiempo, entonces el modelo no estaría prediciendo nada, estaría espiando lo que ya pasó.

Lo probamos por dos caminos. El primero fue mirar la foto del momento exacto en que cada proyecto entra —que el bot viene guardando desde marzo— y compararla con la situación de hoy: nueve de cada diez proyectos tienen exactamente las mismas comisiones que el primer día. El segundo fue buscar en el historial las veces que se amplió formalmente el giro: pasa en el 1,5% de los casos, y esos proyectos efectivamente avanzan más. O sea, algo de contaminación hay, pero es marginal.

La prueba final fue sacarle la contaminación al modelo y volver a medirlo. Si el dato estuviera haciendo trampa, limpiarlo tendría que empeorar la puntería. Pasó lo contrario: mejoró un poquito. Y cuando probamos sacar el dato por completo, la puntería cayó un 16%. Conclusión: el dato es legítimo y además es tan importante como parecía.

Queda una respuesta interesante a la pregunta de fondo. Que un proyecto vaya a varias comisiones no lo hace más difícil, como uno podría pensar por tener que convencer a más gente: lo hace más probable. El giro múltiple lo decide la Presidencia de la Cámara cuando el proyecto entra, y funciona como una señal de que el tema se toma en serio.

Una anécdota que vale como advertencia: el primer cálculo nos dio que el 82% de los proyectos habían cambiado de comisiones — diez veces más de lo real. El error era de lectura: la lista de comisiones viene sin separadores, y tres comisiones seguidas se contaban como una sola. Estuvimos a un paso de anunciar un problema gravísimo que no existía.


## Ahora el modelo mira las comisiones del primer día, no las de hoy
Cerramos la auditoría de las comisiones con una mejora chica y gratis. El modelo contaba a cuántas comisiones fue enviado un proyecto usando la lista de hoy; ahora usa la del día en que entró, que es lo único que se sabe cuando uno tiene que predecir. Para los proyectos de este año el dato es exacto, porque el bot viene guardando la foto del momento de ingreso desde marzo; para los viejos se reconstruye restando las ampliaciones que quedaron registradas.

La puntería del modelo subió un poco, y tiene una gracia: va a seguir mejorando sola. Cuantos más meses corra el bot, más proyectos van a tener el dato medido en vez de reconstruido — hoy ya son tres de cada cuatro.


## Auditamos las variables que faltaban, y la sorpresa fue que no había que tocarlas
Quedaban tres datos del modelo bajo sospecha. Los tres tenían efectivamente el problema que les atribuíamos. Pero cuando probamos arreglarlos, el modelo empeoró en los tres casos.

El más interesante es el historial de éxito del autor. La sospecha era razonable: los autores con pocos proyectos aparecen con tasas de éxito altísimas, que son ruido y no talento — de hecho, tres de cada diez autores con menos de diez proyectos figuran con una tasa tres veces superior al promedio. Cuando corregimos eso de la misma forma que habíamos corregido otro problema esta mañana, la puntería del modelo cayó.

La razón resultó ser reveladora. El "autor" de los proyectos del Poder Ejecutivo es el Presidente, que firma pocos proyectos pero convierte tres de cada cuatro en ley. Al suavizar las tasas extremas estábamos, sin querer, apagando justamente la señal más fuerte que tiene el modelo. Y eso explica algo que nos venía llamando la atención: por qué el dato "lo manda el Ejecutivo" parecía no importar nada. No es que no importe — es que ya estaba contado dentro del historial del autor.

Así que la conclusión no es que haya que cambiar el modelo, sino cómo se lo lee. Los números internos del modelo no se pueden interpretar como "cuánto influye cada cosa", porque hay variables que se solapan. Para saber cuánto pesa realmente que un proyecto lo mande el Ejecutivo hay que hacer lo que ya veníamos haciendo: simular el mismo proyecto firmado por otro. Esa herramienta ya existía desde julio; hoy entendimos por qué era imprescindible.

Y queda una lección que vale para adelante. Hoy corregimos tres problemas y en dos casos mejoró y en uno empeoró. Encontrar un defecto estadístico real no garantiza que arreglarlo sirva. Si hubiéramos aplicado la corrección por analogía con el caso de la mañana —que era lo natural— habríamos bajado la calidad del modelo un 4% convencidos de estar mejorándolo.


## Se cerró el punto ciego que venía haciéndonos deducir en vez de mirar
Hasta hoy, el entorno donde trabaja Claude veía la carpeta del proyecto pero no el registro de quién cambió qué: ese registro vive un nivel más arriba, fuera de su alcance. Era como tener la llave de una habitación pero no del pasillo. La consecuencia práctica era que, para saber qué había hecho Franco, había que deducirlo mirando las fechas de los archivos y creyéndole a las bitácoras — que es exactamente el hábito que ya nos costó varios errores.

Valle sumó la carpeta de arriba y el punto ciego se cerró. La primera comprobación fue justamente esa: lo que se había deducido a ciegas sobre el trabajo de Franco coincidía exactamente con lo que dice el registro real. La deducción estaba bien, pero ya no hace falta.

Apareció además algo que sólo se ve con el historial a la vista: en este repositorio escriben tres manos, y una de ellas es automática. Los bots suben datos casi todos los días por su cuenta. Entre ayer y hoy entraron 27 proyectos nuevos sin que nadie tocara nada. Por eso ningún número del proyecto se puede citar sin la fecha en que se midió.

## Los tres robots estaban por romperse todos juntos, y ya no
Los tres procesos automáticos —el que junta proyectos y votaciones, el que vigila la composición de las cámaras y el que trae el índice de confianza— se apoyaban en piezas que GitHub está dejando de mantener. No estaban rotos: venían avisando. Pero el día que GitHub cortara el soporte, los tres iban a fallar el mismo día, y el modo de falla es el peor posible: el sistema deja de recolectar sin que nadie se entere.

Quedó actualizado. Aparecieron dos cosas en el camino. Una: había una cuarta pieza con el mismo problema que no estaba en la lista de pendientes — es la que abre los avisos cuando algo falla, así que se habría caído junto con todo lo demás, justo cuando más falta hacía. Dos: pudiendo actualizar una de las piezas dos escalones, se actualizó sólo uno. El segundo escalón no agregaba nada sobre el problema que queríamos resolver y sí cambiaba la forma en que estos procesos guardan sus permisos para subir archivos — que es de lo que dependen para funcionar. Cambiar un riesgo conocido por uno desconocido, en algo que nadie mira todos los días, no es prudencia mal entendida: es la diferencia entre arreglar y tocar.

Falta el paso que lo confirma: verlos correr una vez cada uno. Hasta entonces el pendiente sigue anotado, porque si algo se rompió, no va a avisar.


## El bot por fin entrega lo que junta
Desde marzo, el robot venía juntando todos los proyectos que se presentan en las dos cámaras y guardándolos en un archivo que **ningún otro programa leía**. Recolectaba bien y no entregaba: hacía la mitad de su trabajo.

Ya no. Ahora esos proyectos entran a la base que mira el modelo. En números: el sistema pasó a conocer **671 proyectos de ley más**, y —esto es lo importante— **514 de ellos son del Senado**, la cámara de la que casi no teníamos nada. Y la base, que estaba congelada en junio, ahora llega al **5 de agosto**.

También entró por primera vez un dato que la fuente oficial no publica: **quiénes firman cada proyecto además del autor principal**. Hay 1.222 proyectos con varios firmantes, y uno con quince. Ese dato era la razón por la que se construyó el robot, y hasta hoy no llegaba a ningún lado.

## Dos errores que no dieron error
Los dos casos de hoy valen como advertencia, porque ninguno se manifestó como una falla.

El primero: al cargar los proyectos nuevos, el sistema informó alegremente que había cargado 1.531. El modelo vio **uno**. Los proyectos del robot todavía no tienen el número de identificación que asigna la Cámara, y el programa que arma la tabla trataba a todos los "sin número" como si fueran el mismo proyecto, quedándose con uno solo. No hubo mensaje de error: hubo un número que no cerraba, y sólo apareció porque fuimos a comparar cuánto tenía que haber subido.

El segundo: el lector de expedientes del Senado estaba descartando 34 documentos por "formato inesperado". Resultaron ser **los del Poder Ejecutivo**, que son justamente los que más peso tienen en el modelo: el Presidente firma pocos proyectos pero convierte tres de cada cuatro en ley. Se estaban tirando en silencio.

La lección es la misma en los dos casos: **un proceso que no falla no es un proceso que funciona.** Lo único que los encontró fue ir a chequear si el número que salió era el que tenía que salir.

## Una advertencia sobre los números de acá en más
La tasa de éxito general bajó de 3,21% a 3,16%. No cambió nada en el Congreso: los 671 proyectos nuevos son de los últimos cinco meses y **ninguno tuvo tiempo de aprobarse**. Entran al denominador y no al numerador.

Es correcto que estén, pero de ahora en más cualquier tasa calculada sobre el total va a salir un poco baja. Hay que medirla sobre proyectos que ya tuvieron tiempo de resolverse.


## Ahora los errores silenciosos hacen ruido
Los tres problemas del día tuvieron algo en común, y es lo más importante que dejó la sesión: **ninguno dio error**. El programa terminaba bien, decía que había cargado todo, y estaba mal.

Uno informó que había cargado 1.531 proyectos y el modelo vio uno. Otro dejó de contar 109 comisiones. El tercero tiró a la basura 34 expedientes del Poder Ejecutivo —los de más peso del modelo— bajo un aviso que decía "formato inesperado". Los tres aparecieron porque alguien fue a chequear si el número que salió era el que tenía que salir.

Eso ya no depende de que alguien se acuerde de mirar. Ahora el sistema **se controla solo**: cada vez que se carga algo, corre una lista de catorce comprobaciones y, si alguna no cierra, **se detiene y avisa**. No sigue adelante con datos rotos.

Las catorce salen de errores reales, no de imaginar qué podría fallar: cada una vigila una de las formas concretas en que esto se rompió hoy.

Y hay un detalle que importa más de lo que parece: **probamos que los controles funcionan rompiendo la base a propósito**. Ocho pruebas que dañan los datos exactamente como se dañaron de verdad, y verifican que el control lo detecta. Un control que nunca se dispara no protege de nada — hasta no verlo saltar, no sabés si sirve o si es un adorno.

Además, los programas que cargan datos pasaron de *avisar* a *frenar*. Antes, un expediente que no se entendía generaba una línea de aviso que nadie leía. Ahora corta la carga y muestra ejemplos. Si algo se tiene que descartar, hay que decirlo explícitamente en el código: no puede colarse en un aviso.


## Corrección: los datos raros se apartan, no frenan todo
La primera versión del control estaba mal y Valle la frenó. Yo había hecho que **cualquier dato raro detuviera la carga entera**. Suena prudente y no lo es: el robot corre todos los días y una actualización trae trescientos proyectos. Parar los trescientos porque uno vino con un formato desconocido es el mismo error que ya habíamos corregido meses atrás, cuando una fuente caída dejaba al robot sin recolectar nada.

La idea de Valle es mejor y quedó implementada así: **los datos que no se entienden van a una base separada**, con la fila entera guardada y el motivo por el que no se pudo leer. La base principal queda limpia por definición — si un proyecto está ahí, se leyó bien. Nada dudoso llega al modelo y nada se pierde.

Esa lista de pendientes **se sube a GitHub**, aunque la base grande no. Pesa unos kilobytes y la tiene que mirar una persona; si se quedara sólo en la máquina de quien cargó, sería otra vez trabajo invisible.

Hay una excepción: **si de golpe se apartan muchos datos a la vez, ahí sí se frena.** Uno raro es normal, la fuente cambia de a poco. Que se aparte el 15% de una tanda significa que cambió el formato, y eso conviene mirarlo antes de seguir.

Y un detalle que salió de probarlo, no de pensarlo: al principio el corte era sólo por porcentaje, y con tandas chicas frenaba de más — el robot puede traer veinte expedientes en un día, y uno raro ya es el 5%. Se le agregó un piso: por debajo de diez casos nunca frena.

**Un control mal calibrado es peor que ninguno**, porque enseña a ignorarlo. Eso pasó también con mi propio control: al principio avisaba "falló 1 de 8" cuando no fallaba nada, porque revisaba cosas que todavía no podían existir. Corregido.


## Le pusimos red a lo único que no se puede recuperar
La base de proyectos que armó el equipo pesa noventa megas y no se guarda en el repositorio: se reconstruye en un minuto con dos comandos. Eso está bien para casi todo, porque todo sale de fuentes públicas que podemos volver a bajar. Con una excepción: la clasificación temática de cada proyecto, que no la publica nadie — la hace un modelo de lenguaje y cada clasificación cuesta dinero.

El problema era que reconstruir la base borraba esa tabla. Y no hablamos de un comando peligroso: está documentado en el manual del módulo, es rápido y cualquiera del equipo puede correrlo con toda razón. Alguien iba a hacerlo alguna vez y el trabajo pago se perdía sin aviso.

Lo resolvimos hoy justamente porque hoy no cuesta nada: la tabla está vacía, la base se creó esta tarde. Montarlo cuando ya haya cien mil clasificaciones adentro habría significado pagarlas dos veces.

Ahora hay una copia de seguridad en un archivo de texto que sí viaja por el repositorio, y la reconstrucción la restaura sola al terminar — sin depender de que nadie se acuerde, que es exactamente como se pierden las cosas. Además, si alguien revisó a mano una clasificación, esa revisión nunca queda pisada por la del modelo.


## El padrón por fin cierra en 257
Veníamos con 256 diputados de los 257 que existen. Faltaba Néstor Pitrola, porque la fuente que usábamos le anotó la fecha de salida el mismo día que entró. Habíamos intentado corregirlo con reglas y salía peor —según cómo lo arreglábamos terminábamos con 278 o con 263—, así que lo dejamos anotado esperando la nómina oficial de la Cámara.

Hoy la encontramos: la Cámara publica la composición actual de sus bloques, y trae exactamente 257 filas. La usamos para completar lo que faltaba, sin reemplazar la fuente anterior — porque esa tiene la historia de los cambios de bloque, que es lo que hace falta para reconstruir cualquier fecha pasada, y la oficial es solo una foto de hoy.

De paso apareció algo para revisar: el bloque del Partido Obrero está cayendo en la bolsa de "otros/provinciales", que es donde van los bloques negociadores. Es justo lo contrario de lo que hace la izquierda, que vota siempre igual y casi siempre en contra. Quedó anotado, porque mezclar esas dos cosas distorsiona el cálculo de quiénes son las bisagras.


## La izquierda estaba en el cajón equivocado
Franco planteó que la izquierda vota casi siempre en contra de Milei y junto al kirchnerismo, y pidió verificarlo antes de tocar nada. Lo medimos sobre las votaciones de este gobierno: coincide con el kirchnerismo en el 96% de las veces y con La Libertad Avanza en el 8%. La hipótesis era correcta.

Lo llamativo es dónde estaba clasificada: en la bolsa de "otros y provinciales", con la que coincide el 49,8% de las veces — o sea, exactamente lo mismo que si tiráramos una moneda. Esa bolsa es la de los bloques negociadores, los que más se mueven según cómo esté el clima político. La izquierda es justo lo contrario: vota siempre igual, pase lo que pase. La teníamos en el grupo de comportamiento opuesto.

La causa era simple y vieja: el frente de izquierda se cambia el nombre en cada elección, y la lista que traduce nombres de bloque a familias políticas estaba escrita a mano. De trece variantes, doce no figuraban. Lo resolvimos con una regla por patrón en vez de una lista, así las próximas versiones del nombre entran solas.

Y hubo un test que evitó un error más grande. Con un 96% de coincidencia, la tentación era fundir a la izquierda con el kirchnerismo. Pero al mirar gobierno por gobierno aparece que durante la presidencia de Alberto Fernández —cuando el kirchnerismo era gobierno— la coincidencia baja al 58%. No votan igual porque sean lo mismo: votan igual cuando ambos son oposición. Así que la izquierda queda como familia propia.


## Seguimos buscando, y apareció Zamora
Franco pidió no quedarnos con el frente de izquierda y buscar todos los partidos de izquierda que pasaron por el Congreso. Revisamos los cincuenta y un bloques que estaban en la bolsa de "otros" con nombre sospechoso, pero no decidimos por el nombre: medimos cómo vota cada uno comparado con la izquierda ya identificada.

Apareció uno inequívoco: Autodeterminación y Libertad, el bloque de Luis Zamora, que coincide con la izquierda en el cien por ciento de las ciento veintiún votaciones donde ambos estuvieron. Entra sin dudas.

Y apareció una trampa. El Movimiento Evita coincide el 89% de las veces, un número altísimo. Pero es un movimiento social peronista, no de izquierda: coincide porque en el período que le tocó ambos eran oposición. Es exactamente el mismo error que habíamos evitado un rato antes al no fusionar la izquierda con el kirchnerismo. Quedó afuera.

Quedan dos casos sin resolver, Proyecto Sur y Solidaridad e Igualdad, que probablemente sean progresismo. No los tocamos porque no hay manera de medirlos: son de épocas en que la izquierda no tenía bancas, así que no hay votaciones donde comparar. Esos necesitan criterio político del equipo, no estadística.


## Quedó armada la familia de la izquierda
Franco cerró los dos casos que no habíamos podido resolver midiendo. Proyecto Sur, el espacio de Pino Solanas, va con la izquierda y no con el progresismo donde estaba. Y Solidaridad e Igualdad va con el kirchnerismo, porque terminó integrando Unidad Ciudadana.

Los dos eran justamente los que la estadística no podía decidir: son de épocas en que la izquierda no tenía bancas, así que no había votaciones donde comparar. Cuando el dato no alcanza, decide el criterio político — y queda anotado quién decidió qué, que es lo que permite revisarlo mañana.

El resultado final es casi ocho mil votos reclasificados, más del triple de lo que habíamos logrado con la primera búsqueda. La izquierda pasó de un puñado de registros a diecinueve bloques cubriendo desde 1994 hasta hoy. Y como control, después de la corrida volvimos a medir: sigue coincidiendo 96% con el kirchnerismo y 8% con La Libertad Avanza en el gobierno actual. Cambió la etiqueta, no el comportamiento — que es exactamente lo que tenía que pasar.


## Descubrimos que "indisciplinado" y "ausente" se nos estaban mezclando
Al terminar de reclasificar a la izquierda corrimos de nuevo los cálculos, y el cambio quedó validado: la izquierda aparece como el bloque más disciplinado del Congreso —vota siempre igual, sin una sola excepción— y vota que no en tres de cada cuatro ocasiones, mientras el oficialismo vota que sí en ocho de cada diez. Metida en la bolsa de "otros" eso no se veía.

Pero apareció algo que conviene mirar. La lista de los diputados más "indisciplinados" está encabezada por gente que directamente no iba a votar: uno con el 100% de ausencias, Néstor Kirchner con el 98% en su año como diputado, otro con el 97%. Medimos la relación en todo el padrón y da que cerca del 40% de lo que llamamos "desvío" es en realidad inasistencia.

No es un error de programación: el sistema fue diseñado a propósito para contar las ausencias como forma de no acompañar, y eso tiene sentido. El problema es lo que hacemos después con ese número: lo usamos para decidir qué legisladores son sensibles al clima político, o sea quiénes son las bisagras que hay que convencer. Y alguien que no viene al recinto no es una bisagra: es alguien que no está.

Quedó anotado con una forma barata de verificarlo. Es el cuarto caso del día del mismo tipo: una medición que en realidad mide otra cosa. Ya nos pasó con el efecto de los jefes de bloque, con las comisiones, con el índice de confianza, y ahora con esto. Vale la pena que preguntarse "¿qué mide realmente este número, y con cuántos datos?" se vuelva parte de la rutina.


## Le arreglamos el oído al modelo para el clima político (y le sacamos una perilla que contaba doble)
El clima político (el índice de confianza en el gobierno) medía menos de lo que esperábamos, y encontramos por qué. Le estábamos pasando al modelo el número del **mes suelto**, que rebota mucho: un mes sube, el otro baja, y buena parte de eso es ruido. Cuando le pedís a alguien que reaccione a un número que salta todo el tiempo, la reacción que medís sale más chica de lo que es en realidad. La confianza dentro de un mismo gobierno se mueve bastante —no es plana—, así que la variación estaba; lo que fallaba era medirla contra la señal ruidosa.

La solución, con una idea de Valle: en vez del mes suelto, el modelo ahora mira **dos climas a la vez**. El **humor de fondo** (cómo viene la cosa en los últimos seis meses) y el **sacudón reciente** (cuánto se despegó el último trimestre de ese fondo). Son dos preguntas distintas y limpias, y así podemos medir cuánto pesa cada una. El resultado preliminar confirma la sospecha: al sacar el ruido, el efecto del clima sobre las bisagras sube fuerte. El humor de fondo pesa parejo y firme; el sacudón reciente también empuja, sobre todo en los legisladores más movedizos, aunque para confirmar que ese pedazo es sólido falta la corrida grande en la máquina de Valle.

De paso sacamos algo que estaba mal. Había **dos perillas** para el mismo clima: una medida (legislador por legislador) y otra que ponía el analista a mano sobre el total. Mirando el código, las dos multiplicaban la misma señal, o sea contaban el mismo clima dos veces. Nos quedamos con la medida, que es la que tiene respaldo en los datos, y la perilla del analista se elimina. El número final va a ser más honesto: lo que el clima mueve, lo mueve una sola vez.

**Actualización (corrida grande de Valle):** el humor de fondo (6 meses) quedó **confirmado y firme** — el efecto sobre las bisagras más que se duplicó respecto de antes. El sacudón corto (3 meses), en cambio, **no se pudo confirmar**: los datos no alcanzan para asegurar que exista, así que lo apagamos. No publicamos lo que no está medido con confianza. Curiosamente, al apagar el corto el modelo queda mirando solo el humor de 6 meses, que era la idea más simple del principio: los dos caminos llegaron al mismo lado. Una cosa que sí dejamos prendida por criterio de Valle: al núcleo duro no lo damos por insensible al clima aunque el número salga chico — en una caída fuerte hasta los más leales pueden dudar, y "no lo medimos con certeza" no es lo mismo que "no existe". De hecho miramos la caída del gobierno de Alberto (donde el clima se derrumbó de verdad) y los mismos leales bajaron el acompañamiento al gobierno de 82% a 75% — apunta en esa dirección. Con tan pocos datos no alcanza para asegurarlo, así que el número queda puesto pero anotado para revisarlo a medida que pasen los meses.


## Le hicimos un índice al repo (y le pusimos alarma a las cosas que se copiaron a mano)

El proyecto creció a unos 30 módulos y encontrar dónde estaba cada cosa empezó a costar tiempo: había que abrir carpetas hasta dar con el archivo. Le armamos un **índice** (`MAPA.md`, en la raíz): una sola página que dice qué hace cada módulo, cuáles son los archivos importantes, quién usa a quién y de qué páginas oficiales se baja cada dato. Se genera solo, así que no puede quedar viejo por olvido, y hay un buscador (`.mapa/buscar.py "presentismo"`) que te dice archivo y línea sin abrir nada.

Una decisión de fondo: el texto que alimenta ese índice lo pusimos **dentro del README de cada módulo**, no en archivos nuevos. La herramienta que usamos pedía crear un archivo aparte por carpeta —44 archivos— y este proyecto ya tiene cinco documentos vivos que a veces se contradicen entre sí. Sumar un sexto era empeorar justo el problema que el índice viene a resolver.

Lo segundo es lo que más puede ahorrar un dolor de cabeza. Al revisar el código apareció algo previsible: como la regla del equipo es que un módulo no toca el código de otro, varias **definiciones quedaron copiadas** en cuatro o cinco lugares. Por ejemplo, "a qué período parlamentario pertenece esta fecha" está escrito cuatro veces, y "qué tipo de mayoría exige este proyecto", tres. Los comentarios decían *"mantener sincronizadas"* — o sea, el único control era que alguien se acordara.

Las revisamos una por una: **hoy dicen todas lo mismo**, no había ningún error dando vueltas. Pero escribimos una prueba que las compara automáticamente, porque si alguna vez una se corrige y las otras no, en este proyecto eso **no daría error**: el número saldría un poco distinto y nadie sabría por qué. Ahora, el día que se separen, la prueba avisa.

También escribimos en un solo archivo (`rutas.py`) **dónde está guardada cada cosa que un módulo le pasa a otro**. Antes eso estaba repartido: 47 lugares del código calculaban a mano dónde queda la carpeta principal contando niveles de carpeta, y mover un archivo de lugar podía hacer que apuntara en silencio a otro lado. Y hay una prueba que revisa que ese archivo esté completo: si alguien conecta dos módulos por un camino nuevo y no lo anota ahí, salta.

Por último, destrabamos un enredo: la base de proyectos, para verificarse a sí misma, estaba usando código del módulo del embudo. Es al revés de como debería ser (el embudo se apoya en la base, no al revés), y significaba que la base no se podía controlar si el embudo estaba roto. Ahora la base le **pide el número** al embudo en vez de meterse en su código.

### Y al probar todo junto aparecio una prueba que apagaba a todas las demas

Al correr las pruebas del proyecto todas juntas por primera vez, no fallo ninguna:
directamente **no corrio ninguna**. Una de ellas (la del respaldo de temas) estaba
escrita de una forma que, apenas el programa la abre para mirarla, se ejecuta sola
y da la orden de terminar — y se llevaba puesta la corrida entera antes de empezar.
Arreglado: ahora sirve para las dos cosas, se puede correr sola como antes y ademas
entra en la corrida conjunta. Sus 14 chequeos, que hasta hoy no se ejecutaban nunca
en el conjunto, ahora si.

Eso destapo algo mas grande y que conviene tener claro: **las pruebas de este
proyecto estan escritas como programitas sueltos, no como una suite.** Se corren de
a una, a mano, y asi funcionan perfecto — es como se hicieron siempre y no hay que
cambiarlo. Lo que no hay que hacer es correrlas todas juntas con la herramienta
estandar, porque en ese modo algunas cortan la corrida y, peor, otras podrian
fallar sin que la herramienta lo note: imprimen "FALLA" y el resumen igual sale en
verde. Quedo escrito donde corresponde, con los comandos que si valen.

## Revisamos el motor a fondo, y aparecieron cuatro cosas para corregir
Franco revisó la fórmula completa del sistema y planteó ocho objeciones. Fui verificando cada una contra el código, y el saldo es que cuatro dan en el blanco y obligan a cambiar cosas, dos eran malentendidos que generé yo por explicar a medias, y dos abren discusiones que necesitan que el equipo se ponga de acuerdo.

Lo más importante salió de una pregunta lateral. Franco preguntó si el tratamiento "sobre tablas" —cuando dos tercios de la cámara deciden tratar un proyecto que no pasó por comisión— debería considerarse. Fuimos a medirlo: de los proyectos que consiguen el sobre tablas, más de la mitad terminan siendo ley, contra menos del dos por ciento del resto. Y hay algo más grave detrás: una de cada ocho leyes sancionadas nunca tuvo dictamen de comisión. Todo el modelo está construido asumiendo que el camino es comisión y después recinto, y resulta que hay una autopista paralela que no estábamos mirando.

También apareció un error concreto y acotado: cuando el sistema cuenta si hay quórum, descarta a los que se abstuvieron junto con los ausentes. Pero quien se abstiene está sentado en su banca. Es un caso puntual pero justo en el escenario que más nos interesa, el de las abstenciones tácticas.

El tercero es conceptual: el sistema calcula la probabilidad de cada cámara por separado y las multiplica, como si fueran independientes. No lo son — un proyecto que sale de Diputados con doscientos votos llega al Senado en una posición muy distinta de uno que salió raspando.

Y el cuarto tiene algo de irónico. Franco observó que la manera en que medimos el clima político trata igual una subida que una bajada, cuando en política las malas noticias pesan más. Tiene razón, y lo llamativo es que esa asimetría existía en el diseño original: se perdió hace dos semanas, cuando se eliminó —con buen criterio— una parte del mecanismo que duplicaba la señal. Se fue la duplicación y se llevó puesta la asimetría.

Dos objeciones no eran problemas del sistema sino de cómo se lo expliqué, y quedaron anotadas para que nadie las "arregle": la ausencia sí está modelada, y que los ausentes no cuenten como votos emitidos es correcto.

Todo quedó en un documento aparte con las fórmulas y el detalle de qué hacer en cada caso, y los puntos a resaltar se propagaron al mapa del proyecto y al diagrama del modelo, que ahora avisa de estas cinco trampas cuando alguien lo abre.


## Ahora la fórmula del sistema está escrita en un solo lugar
Franco pidió dos cosas para adelante. La primera es una regla de trabajo: cada vez que toquemos el motor de cálculo, no alcanza con mostrar qué hace la función que cambió. Hay que mostrar también a quién afecta dentro del sistema y cómo queda la fórmula general después del cambio.

La razón es lo que aprendimos esta semana. Los cuatro problemas que encontramos llevaban semanas funcionando y ninguno era un error de programación: eran supuestos. Cada cambio se había revisado por separado y ninguno estaba mal en sí mismo — lo que nadie miraba era qué le hacía cada uno al conjunto. El caso más claro: al sacar una parte del mecanismo del clima político, decisión correcta porque duplicaba la señal, se fue con ella la idea de que las malas noticias pesan más que las buenas. Nadie lo notó durante dos semanas.

La segunda cosa es la fórmula completa, escrita y abierta hasta la última variable. Arranca en algo simple —la probabilidad de que una ley se apruebe es la de Diputados por la del Senado— y se va desarmando hasta llegar a cómo se calcula la posición de un solo legislador. Cada símbolo tiene su explicación al lado, cada constante su valor, y cada pieza dice de qué archivo sale.

Lo más útil de tenerla escrita es lo que se ve de un vistazo: hoy el número lo mueven apenas cinco cosas. El clima político y el análisis del dictamen están construidos pero desconectados, y la vía del "sobre tablas" —por donde pasa una de cada ocho leyes— no aparece en ninguna parte del cálculo.
