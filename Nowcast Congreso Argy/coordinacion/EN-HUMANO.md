# EN HUMANO — el sistema explicado sin tecnicismos

> Documento vivo. Cada cambio importante en el proyecto se explica acá en lenguaje claro, además de registrarse en `ESTADO-DEL-PROYECTO.md`. Si algo del sistema no se entiende leyendo esto, está mal escrito y hay que arreglarlo.

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

Detalle importante: la base de datos oficial del Congreso dejó de actualizarse en 2020, así que lo reciente (hasta 2025) lo sacamos de otra fuente (argentinadatos). Y nos falta un pedazo del Senado entre 2014 y 2023, que hay que ir a buscar aparte.

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
# EN HUMANO — el sistema explicado sin tecnicismos

> Documento vivo. Cada cambio importante en el proyecto se explica acá en lenguaje claro, además de registrarse en `ESTADO-DEL-PROYECTO.md`. Si algo del sistema no se entiende leyendo esto, está mal escrito y hay que arreglarlo.

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

Detalle importante: la base de datos oficial del Congreso dejó de actualizarse en 2020, así que lo reciente (hasta 2025) lo sacamos de otra fuente (argentinadatos). Y nos falta u

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
