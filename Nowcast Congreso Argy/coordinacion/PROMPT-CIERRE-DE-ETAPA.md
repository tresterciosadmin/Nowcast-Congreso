# Prompt para Claude Code — arreglar la fuga, limpiar los números, cerrar la etapa

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

## Qué es esta sesión

**No es una sesión de mejora. Es de saneamiento.** Se descubrió una fuga de información en el
harness de medición (URGENTE U1) que contamina el número publicado y la justificación de una
bandera que está prendida en producción. Hay que arreglarla, volver a medir todo lo que
dependía de ella, y **dejar el proyecto en un estado donde se pueda revisar de cero.**

Después de esta sesión Franco para el proyecto para una revisión intensiva. Lo que esta sesión
tiene que entregar es **la verdad sobre en qué estado está el motor**, no una mejora.

## 🔴 Nada nuevo. Ni un término, ni una hipótesis, ni una idea.

Está prohibido en esta sesión: proponer formulaciones nuevas, estimar parámetros nuevos,
explorar líneas abiertas, o prender nada que no estuviera prendido. **Si encontrás algo
interesante, anotalo en `URGENTE.md` y seguí.** La tentación de "aprovechar que estoy acá" es
exactamente lo que hay que resistir.

---

# El problema, y de dónde viene

## La fuga

`evaluacion/baseline/src/baseline_voto_individual.py` calcula el récord con
`shift(1).expanding()` sobre la serie del legislador ordenada por fecha. Eso desplaza **un
voto, no una fecha**: al predecir el artículo 3 de una ley, usa como historia los artículos 1
y 2 de la misma ley, votados el mismo día y con el mismo resultado. **Le está diciendo la
respuesta.**

Medido: **el skill publicado baja de 0,161 a 0,092 al quitarla.**

Y el motor tiene la misma forma de fuga en su camino de backtest: filtra con
`fecha <= hasta` en vez de `<`.

## El espejo

El harness define `perfil()` con el comentario *"espejo exacto de `perfil_legislador`"* en vez
de importarlo. **Un espejo es una divergencia esperando pasar, y pasó**: el motor condiciona
el récord por origen y el harness no. Medido sin fuga, el motor es **mejor** de lo que el
harness decía en la era vigente: **0,19 contra −0,03 desde 2023**.

**Las dos cosas las escribí yo en el prompt del 03-09** (la versión de Claude que armó ese
baseline). No son errores del equipo: son errores de diseño del instrumento, y hay que
arreglarlos en la raíz, no parchearlos.

## Y es una sola causa, no dos hallazgos

ADR-0032 midió que **1.070 actas son sólo 310 leyes**: el n efectivo es la ley. Esta fuga es
**el mismo hecho** —las actas de una ley no son independientes— manifestándose en el punto
estimado en vez de en el error estándar.

**Escribilo como una sola regla**, no como dos ítems separados.

---

# FASE 1 — La fuga, en los dos lados

1. **En el harness:** el corte de historia tiene que ser **por fecha estricta Y por
   expediente**. No alcanza `<` sobre la fecha: dos artículos de la misma ley pueden tener el
   mismo timestamp, y aunque no lo tuvieran, **la votación anterior de la misma ley no es
   historia legítima para predecir la siguiente**. Excluí el mismo expediente.
2. **En el motor:** `fecha <= hasta` → `<` en el camino de backtest. Buscá **todas** las
   ocurrencias de ese patrón, no sólo la que se reportó — con `.mapa/buscar.py` y grep sobre
   `<=` en filtros de fecha.
3. **Un test que falle si vuelve a filtrarse**: un caso sintético con dos actas del mismo
   expediente el mismo día, donde la segunda no puede usar la primera.

**Verificá el efecto y reportalo**: cuánto cae el skill en cada arreglo por separado, para
saber cuál de los dos pesaba.

---

# FASE 2 — Matar el espejo

`perfil()` y cualquier otra lógica duplicada del motor en el harness **se eliminan y se
importan**. El harness mide el motor; si lo reimplementa, mide otra cosa.

- Importá de `nowcast_puertas` (o de donde viva el contrato) en vez de copiar.
- Si la importación es incómoda por dependencias, **extraé la función a un módulo compartido** y
  que los dos importen de ahí. No la copies "por practicidad".
- **Un test que falle si el harness y el motor devuelven distinto** para el mismo input. Ese
  test es la barandilla estructural: es lo que impide que vuelvan a divergir.

Buscá si hay otros espejos del mismo tipo — los scripts de estimación (`estimar_*.py`)
importan de `baseline_voto_individual`, así que revisá qué más se está copiando.

---

# FASE 3 — El número real

Re-corré el censo completo con el harness arreglado. **Ése pasa a ser el número publicado**, y
hay que decirlo con esas palabras en `FORMULA-COMPLETA.md`: el anterior estaba inflado por
fuga.

Reportá, con la comparación explícita antes/después:

- agregado, `por_era`, `por_camara`, `por_fuente_direccion`;
- **clusterizando por expediente**, no por acta (ADR-0032);
- y el dato que más importa para la revisión: **cuál es el skill en la era vigente**, que es
  donde el harness y el motor más diferían.

Tiempo: la sesión anterior lo corrió en **14 minutos** partiendo por fechas en 3 procesos.
Usá ese método, no la corrida monolítica.

---

# FASE 4 — Re-evaluar todo lo que dependía del harness

## 4.1 `RECORD_POR_TEMA`, que está PRENDIDO en producción

El **11,06%** que justificó prenderlo se midió con la fuga, y es **la medición más expuesta**:
el récord temático tiene celdas más finas, así que los votos de la misma ley pesan
proporcionalmente más en la historia condicionada.

**Re-medilo con el harness limpio, y aplicá el criterio simétrico al que se usó para
prenderlo.** Franco fijó *"prender si el censo completo mejora y queda documentado"*. La
versión simétrica es: **si el censo limpio no mejora, se apaga.** Una bandera que no aporta es
complejidad sin beneficio, y dejarla prendida con la justificación caída sería la opción
deshonesta.

**Esto cambia el número publicado. Reportalo de forma prominente, no en una nota al pie.**

## 4.2 τ, que quedó subestimado

Los seis parámetros estimados usaron el offset del motor, y **un offset contaminado es
demasiado bueno**: deja menos residuo. Eso **subestima** los coeficientes de los términos
nuevos — o sea que β, δ, θ y ψ son probablemente **conservadores** y sus efectos aguantan.

**Pero τ mide justamente la dispersión que el motor no explica.** Con un offset demasiado
bueno, la dispersión parece menor: **τ está subestimado y las bandas del producto quedan
angostas.** Re-estimalo con el offset limpio.

**Verificá esa lógica antes de aplicarla** — si al re-medir alguno de los otros cinco se mueve
de forma inconsistente con "eran conservadores", decilo, porque significa que mi razonamiento
sobre la dirección del sesgo está mal.

## 4.3 Los demás

No hace falta re-estimar β, δ, θ y ψ en esta sesión si el argumento de la dirección del sesgo
se sostiene. **Pero dejá anotado en la tabla de parámetros que fueron estimados con offset
contaminado y en qué dirección**, para que nadie los cite como limpios.

---

# FASE 5 — El inventario honesto (esto es lo que Franco necesita para la revisión)

**Es el entregable más importante de la sesión.** Franco va a frenar el proyecto para una
revisión intensiva, y necesita saber **qué sabemos de verdad**.

Armá `coordinacion/ESTADO-REAL-DEL-MOTOR.md` con una fila por término del motor:

| término | ¿prendido? | número que lo justificó | cómo se midió | ¿contaminado? | número limpio |
|---|---|---|---|---|---|

Incluí **todos** los términos del tablero de `FORMULA-COMPLETA.md`, prendidos y apagados. Y
para cada uno, la columna que más importa: **¿la evidencia que lo sostiene sigue en pie
después de esta sesión?**

Además, tres secciones cortas:

**1. Qué sabemos con confianza.** Los resultados que no dependían del harness contaminado, o
que sobreviven al arreglo.

**2. Qué creíamos y ya no.** Sin suavizarlo, con el número viejo y el nuevo al lado.

**3. Qué nunca estuvo medido.** Los términos que están en la fórmula por argumento y no por
evidencia. Hay varios y conviene que estén juntos.

**No opines sobre prioridades ni propongas un plan.** Esa conversación es de Franco. Tu trabajo
acá es que tenga los hechos ordenados.

---

# FASE 6 — La regla metodológica, escrita una sola vez

En la sección de metodología de `FORMULA-COMPLETA.md`, agregá **una** regla que unifique el
hallazgo de ADR-0032 y esta fuga:

> **La unidad efectiva es el EXPEDIENTE, no el acta.** 1.070 actas son 310 leyes. Eso tiene
> dos consecuencias y son la misma: **(a)** clusterizar por acta subestima los errores estándar
> ~1,7×; **(b)** usar una acta de la misma ley como historia es fuga, porque no es una
> observación independiente. Todo corte, cluster o ventana de historia **se hace por
> expediente**.

Y sumá a la lista de defaults silenciosos —van cuatro— **el quinto**: un `<=` donde debía ir
`<`. La familia ya es un patrón, no una casualidad.

---

# Reglas de la casa

**CERO gasto de API.** Nada de esto necesita el clasificador.

**Leé primero:** `coordinacion/URGENTE.md` (U1 y sus tres opciones) → `MAPA.md` (y
`.mapa/buscar.py`) → `CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` → ADRs **0026**
(récord por tema, el que hay que re-evaluar), **0031**, **0032**.

**ADR-0015:** todo cambio al motor se presenta en tres niveles y actualiza
`FORMULA-COMPLETA.md` en el mismo commit.

**No `git push`.** Commits locales, en español, uno por fase.

## Lo único que se puede apagar sin preguntar

`RECORD_POR_TEMA`, si el censo limpio no lo respalda — y es revertir a un estado conocido, no
agregar. **Cualquier otro cambio de comportamiento del motor se reporta y no se prende.**

## Higiene

- **Un porcentaje imposible es un bug, no un fenómeno.** Y un salto sospechosamente grande
  también: el 11,06% tendría que habernos llamado la atención cuando apareció.
- **Si el resultado contradice lo que esperábamos, decilo.** Acá eso incluye: si al arreglar la
  fuga el motor resulta peor de lo que creíamos, ése es el número y va publicado.
- **No maquilles la comparación.** El antes y el después se reportan sobre el mismo conjunto de
  actas, con el mismo método, y con la diferencia a la vista.

# Qué dejar escrito

1. **`coordinacion/ESTADO-REAL-DEL-MOTOR.md`** (nuevo) — el inventario de la FASE 5.
2. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — bitácora arriba de todo.
3. **Un ADR** (próximo número libre): la fuga, el espejo, qué se re-midió, qué se apagó. Con
   **enmienda explícita al ADR-0026** si `RECORD_POR_TEMA` cambia de estado.
4. **`coordinacion/FORMULA-COMPLETA.md`** — el número publicado nuevo, la regla del expediente,
   la marca de "offset contaminado" en la tabla de parámetros.
5. **`coordinacion/URGENTE.md`** — cerrá U1; abrí lo que aparezca y no se resuelva acá.
6. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa: qué estaba mal, qué se arregló, y qué
   significa para lo que el modelo dice hoy.
7. Reindexá: `python .mapa/indexar.py .`

# Cerrá con

| | antes | después |
|---|---:|---:|
| skill del censo | 0,161 | |
| skill era vigente | | |
| `RECORD_POR_TEMA` | prendido (11,06%) | |
| τ | 1,197 | |

Más:

- **qué esperabas y salió distinto**;
- **qué quedó prendido y qué se apagó**, con el motivo;
- y la frase que Franco va a leer primero: **en una línea, ¿el motor es mejor o peor de lo que
  creíamos, y cuánto?**

Empezá por `URGENTE.md` y la **FASE 1**.
