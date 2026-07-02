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


## La base entera, ahora en dos formatos que cualquiera puede abrir
Hasta hoy la base unificada vivía en archivos técnicos (parquet) que solo los scripts leían. Ahora hay dos salidas nuevas: una base SQLite única con TODO (para el programa y para consultas), y una serie de Excel — **uno por gobierno** (De la Rúa, Duhalde, Kirchner, las dos CFK, Macri, Fernández, Milei) — con las votaciones y el detalle voto por voto. Se separó por gobierno porque los 835 mil votos no entran en una sola hoja de Excel, y de paso los cortes coinciden con las etapas políticas (con cuidado en 2001–2003, donde las asunciones no fueron un 10 de diciembre).

Además cambió una definición importante, a pedido de Valle: qué es una votación "disputada". Antes usábamos un atajo (que la minoría juntara al menos 10%); ahora es la definición institucional correcta: que el resultado haya quedado a ±5% del número que se necesitaba para aprobar — número que cambia según el tipo de mayoría y cuántos estén presentes ese día. Con esta vara quedan solo 96 votaciones verdaderamente al filo en 25 años, y la lista da confianza: aparecen la Ley Bases de 2024 y la reforma jubilatoria que se perdió por un voto, exactamente las que cualquier analista nombraría.


## Afinamos qué cuenta como votación "al filo"
Valle vio que con la primera versión solo 96 votaciones en 25 años calificaban como disputadas y le pareció imposible. Revisamos con los datos: no había error de cálculo — la gran mayoría de las votaciones del Congreso se ganan por márgenes amplios, porque la pelea de verdad ocurre antes (si no están los números, la sesión se cae por falta de quórum y la votación nunca sucede). Pero sí había una vara demasiado exigente: el margen del 5% estaba calculado sobre un número que en el Senado equivalía a apenas ±2 votos. Probamos cuatro formas de calcularlo, Valle eligió la más razonable (5% de los votos emitidos ese día) y quedaron **190 votaciones disputadas** en 25 años. El reparto por gobierno es un buen control de calidad: el récord lo tiene la era Milei (57), y los mínimos son los gobiernos con mayorías cómodas.
