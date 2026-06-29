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
