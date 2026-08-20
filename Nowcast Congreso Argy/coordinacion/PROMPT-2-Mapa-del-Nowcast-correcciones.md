# Prompt — corregir el Mapa del Modelo (ronda 2)

> Para pegar en un chat nuevo **junto con la foto del boceto** del flujo.
> Guardado acá para no reescribirlo si hay que repetir la vuelta.

---

Trabajás sobre el repo **Nowcast Congreso** (`Nowcast Congreso Argy/`, la raíz git
está un nivel arriba). Aplicá la metodología del repo: leé `coordinacion/URGENTE.md`
primero, después `MAPA.md` en la raíz, y el `README.md` del módulo que toques. Usá
`.mapa/buscar.py` para ubicar código en vez de escanear el repo. Reclamá
`producto/dashboard` en `coordinacion/TABLERO.md` antes de escribir.

**Tu tarea:** corregir `MAPA-MODELO.html` — el mapa visual de cómo se calcula el
Nowcast. Existe y funciona, pero está mal resuelto visualmente. **La imagen adjunta
es un croquis a mano del flujo que quiero; manda sobre cualquier descripción de este
texto.**

## Lo que YA está bien — no lo rehagas

Verificado contra el disco:

- Las **67 rutas** que citan los nodos existen todas.
- **Las dos formulaciones conviven** y están distinguidas: la v1 en producción
  (`P(llega al recinto) × P(mayoría|recinto)`, en `modelo/ensemble/src/ensemble.py`)
  y el reencuadre por puertas del 08-08 (`P(A)·P(B|A)·P(C|A,B)·P(D|A,B,C)`, en
  `modelo/ensemble/PUERTA-D.md`), con A y C parqueadas. Era el requisito duro.
- Los datos se cargan con `<script src="mapa_modelo_datos.js">`, **no con `fetch`**.
  Es lo correcto: con `fetch` el doble clic (`file://`) se rompe por CORS.
  **No lo cambies.**
- La separación datos / diseño / semántica:
  `producto/dashboard/src/generar_mapa_modelo.py` escribe el `.js`,
  `producto/dashboard/data/mapa_modelo_semantica.json` tiene la prosa curada,
  el HTML es sólo el diseño.

## Corrección 1 — el flowchart no parece un flujo

Hoy es un grafo por columnas genérico: los nodos son cajas iguales y no se puede
seguir el recorrido. Quiero un **diagrama de flujo de verdad**, como el del croquis.

**La forma dice qué es cada cosa, sin leer el texto:**

| Rol | Forma | Ejemplos del repo |
|---|---|---|
| base de datos / fuente | **rectángulo** | `datos/canonica`, `proyectos.db`, el padrón, CKAN, argentinadatos |
| script / proceso | **hexágono** | `to_canonical.py`, `embudo.py`, `disciplina.py`, `agregador.py` |
| variable / señal | **círculo** | presentismo, desvío, ICG/γ, origen del proyecto, postura de bloque |
| resultado / probabilidad | **rectángulo grueso** | P(origen), P(revisora), P(sanción) |

**Izquierda a derecha, escalonado en profundidad** — no en columnas rígidas
alineadas. Que se vea que varias fuentes convergen en un script, los scripts
producen bases, las bases alimentan variables, y las variables entran al cálculo.

**La estructura bicameral es el esqueleto del dibujo, no un detalle.** Dos bloques
del mismo diseño, uno al lado del otro:

- izquierda: la cadena completa hasta **P(aprobación en Cámara de Origen)**;
- derecha: la cadena completa hasta **P(aprobación en Cámara Revisora)**;
- del resultado de origen sale una **flecha curva y gruesa por arriba** hasta el
  bloque de la revisora, rotulada `P(aprobar en Revisora | se aprobó en Origen)`;
- dentro del bloque de la revisora, **lo que está condicionado por el paso previo va
  agrupado y resaltado** (en el croquis, el recuadro turquesa);
- las dos probabilidades bajan y confluyen en una caja final abajo:
  **P(aprobación de un proyecto de ley)**.

**Tipos de línea, y que la leyenda lo diga:** llena = flujo de datos ·
punteada = realimentación o dependencia opcional · gruesa = el condicionamiento
entre cámaras.

**Restricción técnica:** el layout se calcula en JS dentro del archivo. **Nada de
CDN** — se abre con doble clic y tiene que andar sin internet. Si necesitás un
algoritmo de ruteo de aristas, escribilo o vendorizalo dentro del repo.

## Corrección 2 — sacar la capa de presentación comercial

El HTML que se usó de molde era una **presentación de venta**. Esto es una
herramienta interna: cuando alguien pregunta "¿de dónde sale este número?", se
señala un nodo. No hay que convencer a nadie.

**Sacar** todo lo que está arriba del lienzo (`MAPA-MODELO.html` ~líneas 242-245 y
el bloque `#formulas`): el `<header>` con `<h1>Mapa del Modelo</h1>`, el subtítulo,
la línea de metadatos, los textos `meta.para_que` y `meta.no_es` como banner, y el
bloque de fórmulas como franja destacada.

**Ojo: sacar el banner, no el contenido.** Las dos formulaciones tienen que seguir
estando — es justo el punto donde un mapa aplanado induce al error. Movelas a la
leyenda o al panel lateral, en chico y sin jerarquía de titular.

**Que quede arriba, en una sola barra fina:** buscador, filtros por etapa y por rol,
selector de camino, y los controles de zoom / ajustar / reordenar / pantalla
completa. Eso es instrumental y sirve. El lienzo tiene que ocupar la pantalla desde
el primer píxel.

## Corrección 3 — el panel lateral por unidad se queda y se agranda

`<aside class="ficha">` es lo más útil que tiene la página. Mantené el
comportamiento (click en un nodo → ficha a la derecha en PC) y aprovechá el espacio
que libera el header. Por cada nodo tiene que seguir contestando: qué es, qué
archivo lo produce, qué consume, quién lo consume, en qué estado está y cuál es su
trampa conocida. En pantalla angosta puede pasar abajo o a un cajón.

## Un error concreto, de paso

Los nodos `g_A` y `g_C` figuran con estado **REPLANTEADO**, pero el `**Estado:**`
del README de `modelo/ensemble` —que el generador declara como su fuente— dice
**EN CURSO**. Las dos cosas pueden ser ciertas (las puertas A y C están parqueadas
aunque el módulo esté en curso), pero entonces **el estado de una puerta no es el
estado de su módulo** y el generador no puede derivar uno del otro sin decirlo.

Elegí una y dejala explícita: o el estado por nodo se declara en
`mapa_modelo_semantica.json` y el generador no lo pisa con el del README, o los
nodos heredan el del módulo y las puertas parqueadas se marcan con otra cosa (un
badge "parqueada", no un estado). Lo que no puede quedar es que el mapa afirme un
estado que su propia fuente declarada contradice.

## Reglas de la casa

- **Las 4 bitácoras se mueven juntas** en el mismo cambio: `ESTADO-DEL-PROYECTO.md`,
  `EN-HUMANO.md`, `TABLERO.md` y `tablero_datos.js`.
- **`MAPA.md` y `.mapa/` son generados**: no los edites a mano. Si cambia lo que hace
  `producto/dashboard`, actualizá el `**Resumen:**` y el `## Buscar acá si` de su
  README, que es de donde sale el mapa.
- **No edites `TABLERO-CONTROL.html`** — es otro archivo y otro propósito.
- **El disco manda sobre las bitácoras.** Cualquier cifra que pongas en el mapa,
  re-derivala del archivo o del parquet en esta sesión. No la copies de un README.
- **En mi máquina no hay `bash`** — ni en PowerShell ni en el entorno de GitHub
  Desktop. Todo comando que me pases va en **PowerShell**; todo script que ejecute
  git va en **sh POSIX con `#!/bin/sh`**.
- **Prefijá `GIT_OPTIONAL_LOCKS=0` a todo comando git**, o me trabás el git.
- Lo temporal y los scripts de un solo uso van a `Archivos_Borrar/`, neutralizados.

## Cómo se prueba (no alcanza con que se vea bien)

1. **Doble clic sobre `MAPA-MODELO.html`, sin servidor y sin internet.** Tiene que
   dibujar. Si sale en blanco, mirá la consola: casi siempre es un `fetch` o un CDN.
2. `python producto/dashboard/src/generar_mapa_modelo.py` dos veces seguidas no debe
   producir diff en la segunda (idempotente).
3. `python -m pytest tests/ datos/proyectos/tests -q` sigue en verde.
4. **¿Se puede seguir el recorrido de una fuente hasta P(sanción) sin ayuda?**
   Si hay que explicarlo, todavía no está.

**Antes de escribir código, decime qué vas a hacer y esperá que confirme.**
