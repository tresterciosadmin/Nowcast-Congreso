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

En su primera corrida ya encontró algo. Hace unos días habíamos dado por perdida una banca: el padrón daba 256 sobre 257 y habíamos decidido avisar antes que inventar. El vigilante detectó que dos diputados —Matzkin y Pitrola— ya figuran en la lista oficial y que Ravier dejó su banca. Con ellos, el total da **257 exacto**. La cámara queda con La Libertad Avanza en 95, el peronismo en 93, cuarenta y siete de bloques provinciales y el resto repartido.

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
