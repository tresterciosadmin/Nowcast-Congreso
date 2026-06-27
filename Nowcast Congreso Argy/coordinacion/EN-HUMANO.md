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
