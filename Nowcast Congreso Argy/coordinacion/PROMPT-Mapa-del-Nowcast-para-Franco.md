# Prompt para Franco — Mapa del Nowcast (workflow visual del cálculo)

> Pasale esto tal cual a tu Claude, junto con el archivo adjunto
> **`MIA — Mapa del modelo.html`** (es el modelo de referencia visual).
> Está escrito para que arranque leyendo el repo, no para que invente nada.

---

## Lo que hay que construir

Un **HTML autocontenido** que se abra con doble clic y muestre, como grafo
navegable, **cómo se calcula la probabilidad de que un proyecto de ley sea
aprobado** en el Nowcast Legislativo Argentino: de qué fuentes oficiales sale
cada dato, qué script lo transforma, en qué parquet/base aterriza, qué variable
alimenta, y cómo se compone el número final — primero en la **cámara de origen**,
después en la **revisora**, y de ahí la probabilidad final.

Es para **uso interno del equipo**: guiarnos, ver de un vistazo qué depende de
qué, y que cuando alguien pregunte "¿de dónde sale este número?" la respuesta sea
señalar un nodo en vez de abrir quince archivos.

**No es un tablero.** No compite con `TABLERO-CONTROL.html` (que muestra plan y
avance). Este muestra **la maquinaria**.

## El artefacto de referencia

El adjunto `MIA — Mapa del modelo.html` es el mismo tipo de artefacto hecho para
otro proyecto. **Copiale la forma, no el contenido.** Lo que hay que replicar:

- Un solo archivo, sin dependencias externas. Los datos van embebidos como
  `const DATOS = {nodes, links, meta}`.
- Grafo SVG con zoom, pan, botones `+ / − / Ajustar / Reordenar / ⛶`.
- Formas por rol: **cuadrado** = fuente oficial, **hexágono** = script,
  **rombo** = dato (parquet, base, csv, config), **círculo** = variable / etapa
  del cálculo. Tamaño del círculo según jerarquía.
- Barra de filtros arriba, sticky: buscador por texto, chips por etapa, chips por
  rol, alternar etiquetas (todas / sólo las claves), tema claro/oscuro.
- Ficha lateral al tocar un nodo: qué es, qué archivo lo implementa, entradas,
  salidas, notas.
- **Tabla gemela** ("Ver tabla") con los mismos datos en dos tablas (Nodos y
  Conexiones). No es un extra: es el modo de leer el mapa sin depender del color
  ni del hover, y sirve para buscar con Ctrl+F.
- Leyenda al pie explicando formas, tipos de línea y qué significa cada estado.
- Tipos de arista con trazo distinto: **flujo** (línea llena, el dato pasa),
  **config** (línea gris clara, parametriza), **calcula** (punteado fino),
  **alerta** (guiones, es un control o un aviso, no el valor publicado).

La paleta y las variables CSS del adjunto están validadas para modo claro y
oscuro: **reusalas tal cual**, no inventes colores.

---

## La espina dorsal del grafo: la cadena de cálculo

Esto es lo que hay que respetar con precisión, porque es el contenido real y está
verificado contra el código del repo (2026-08-20). El mapa se organiza en
**columnas de izquierda a derecha**, una por etapa:

```
FUENTES → INGESTA → BASES → VARIABLES → CÁMARA DE ORIGEN → CÁMARA REVISORA → NOWCAST → EVALUACIÓN
```

### Ojo: conviven DOS formulaciones, y el mapa tiene que mostrar las dos

**No las mezcles ni elijas una.** Están las dos vivas en el repo y confundirlas
sería el error más caro que puede tener este mapa.

**(1) v1, la que está en producción** — `modelo/ensemble/src/ensemble.py`:

```
P(aprobación) = P(llega al recinto) × P(mayoría | recinto)
```

- `P(llega al recinto)` ← `variables/embudo` (el embudo: presentado → comisión →
  dictamen → recinto → sanción). Salida: `variables/embudo/outputs/p_embudo.parquet`.
- `P(mayoría | recinto)` ← `modelo/agregador_institucional` (cuenta bancas,
  quórum, umbral de mayoría, bandas). Se importa su función pública
  `simular_votacion`.

**(2) El reencuadre por puertas (decisión de Valle, 2026-08-08)** —
documentado en `modelo/ensemble/PUERTA-D.md`:

```
P(sanción) = P(A) · P(B|A) · P(C|A,B) · P(D|A,B,C)
```

| Puerta | Qué es | Estado en el repo |
|---|---|---|
| **A** | agenda origen (¿sale de comisión?) | **PARQUEADA** — se *observa* el dictamen, no se predice: lo que pasa en comisión es política pura |
| **B** | voto en la cámara de ORIGEN (¿hay mayoría?) | **existe** → `modelo/agregador_institucional` |
| **C** | agenda revisora (¿la tratan antes de caducar?) | **PARQUEADA** post-lanzamiento — observada + reloj Ley 13.640 |
| **D** | voto en la cámara REVISORA | **existe** → `modelo/ensemble/src/puerta_d.py` |

Regla que el mapa debe hacer visible: **una puerta que ya ocurrió deja de ser
probabilidad y vale 1**. Con media sanción, A y B son hechos y queda `P(C)·P(D)`.

Sugerencia de representación: las cuatro puertas como nodos-etapa en el eje
horizontal, las parqueadas con borde punteado, y la fórmula v1 como un camino
alternativo marcado ("v1 en producción").

### Lo que alimenta cada pieza (verificado, no inventar)

**Fuentes oficiales** (nodos cuadrados). Salen de `MAPA.md`, sección
"Fuentes externas":

| Fuente | Host | Alimenta |
|---|---|---|
| CKAN HCDN | `datos.hcdn.gob.ar` | votaciones Diputados 2011-2020, backfill de expedientes |
| HCDN — Trámite Parlamentario | `hcdn.gob.ar` | proyectos nuevos con firmantes y giros (bot diario) |
| Senado — votaciones y DAE | `senado.gob.ar` | votaciones del Senado, expedientes |
| argentinadatos | `api.argentinadatos.com` | Diputados 2020-2025, Senado 2024-2025 |
| Wikipedia (anexos) | `es.wikipedia.org` | padrón histórico del Senado |
| UTDT | `utdt.edu` | ICG (índice de confianza en el gobierno) |
| Década Votada / legislAr | (semilla, un solo uso) | votaciones anteriores a 2011 |

**Los tres bots que corren solos** (van como nodos de script, con su horario —
esto es infraestructura viva y hay que verlo). Están en la **raíz git**, un nivel
arriba del proyecto: `.github/workflows/`

- `bot-diario.yml` — cron `0 10 * * 1-6` (07:00 ARG, lunes a sábado)
- `icg-mensual.yml` — cron `0 12 5 * *` (día 5, 09:00 ARG)
- `padron-vivo.yml` — cron `0 11 * * 1` (lunes 08:00 ARG)

**Bases y artefactos que cruzan de un módulo a otro.** No los busques a mano:
están **todos declarados** en `rutas.py` (raíz del proyecto), 52 constantes
nombradas. Es literalmente el inventario de aristas del grafo.

**Variables que entran al cálculo** — una carpeta por variable en `variables/`:
`bloque` (cohesión, postura, proyector point-in-time), `legislador` (ficha
individual), `embudo`, `asistencia_quorum`, `proyecto` (tema, origen
Ejecutivo/Oficialismo/Aliados/Oposición, jefe de bloque, ICG como modulador),
`contexto` (futuro).

**Evaluación**: `modelo/ensemble/src/backtest_cadena.py` mide la cadena completa
contra `sancionado` real (Brier, skill, calibración), con el `p_sancion` del
embudo como baseline.

---

## Estado y dueño de cada pieza

Cada nodo lleva **estado** y **dueño**, y eso NO se inventa: se lee del repo.

- El `README.md` de cada módulo tiene las líneas `**Estado:**` y
  `**Owner actual:**`.
- `coordinacion/TABLERO.md` dice qué módulo está tomado y por quién.
- Estados válidos (los mismos que usa `tablero_datos.js`):
  `HECHO | EN CURSO | PARCIAL | PENDIENTE | FUTURO | REPLANTEADO`.

En el grafo, el estado se representa con **opacidad o borde**, no con color de
relleno (el color ya lo usa el rol). Las piezas `PENDIENTE` / `FUTURO` /
parqueadas van con borde punteado: **se ven, pero se ve que no están**. Eso es
media utilidad del mapa — mostrar los huecos, no esconderlos.

---

## De dónde sacar los datos del grafo

**No armes el JSON leyendo el repo archivo por archivo.** El repo ya tiene un
índice mecánico hecho para esto (instalado el 2026-08-20, ver ADR-0010):

- **`MAPA.md`** (raíz) — leelo PRIMERO y entero. Es el índice del repo: qué hace
  cada módulo, archivos centrales, quién importa a quién, fuentes externas,
  variables de entorno.
- **`.mapa/mapa.json`** — el mismo índice completo en JSON: 121 archivos, símbolos
  con línea, aristas de import, co-cambio de git, hosts externos. **Esta es tu
  materia prima.**
- **`.mapa/buscar.py`** — consultá en vez de escanear:
  `python .mapa/buscar.py --archivo modelo/ensemble/src/ensemble.py` te dice
  quién lo usa y con qué cambia junto.
- **`rutas.py`** — los 52 artefactos que cruzan entre módulos.

**Arquitectura pedida:** dos capas, igual que el resto del repo.

1. **Mecánica** — un script `producto/dashboard/src/generar_mapa_modelo.py` que
   lea `.mapa/mapa.json` + `rutas.py` + los `README.md` (estado y dueño) y arme
   los nodos de script, dato y fuente con sus aristas.
2. **Curada** — un archivo a mano, `producto/dashboard/data/mapa_modelo_semantica.json`,
   con lo que ningún escáner puede saber: qué **calcula** cada script en
   castellano, qué significa cada parquet, cuál es la fórmula de cada etapa, qué
   puertas están parqueadas y por qué.

El script fusiona las dos y escribe `mapa_modelo_datos.js`. El HTML lo lee y
**no se edita a mano** — mismo patrón que `TABLERO-CONTROL.html` + `tablero_datos.js`.

Si esa arquitectura resulta demasiado para una primera vuelta, es aceptable
arrancar con el JSON curado a mano **siempre que quede en su archivo aparte**,
para poder escribir el generador después sin rehacer el HTML. Lo que no es
aceptable es incrustar los datos dentro del HTML: en tres meses el mapa miente y
nadie lo actualiza, que es el modo de falla documentado de este proyecto.

---

## Dónde vive

Siguiendo la convención del repo (los paneles se abren con doble clic desde la
raíz del proyecto):

```
MAPA-MODELO.html                                   ← el diseño, fijo. NO se edita a mano
mapa_modelo_datos.js                               ← los datos, generados
producto/dashboard/src/generar_mapa_modelo.py      ← el generador
producto/dashboard/data/mapa_modelo_semantica.json ← la capa curada a mano
```

**Reclamá `producto/dashboard` en `coordinacion/TABLERO.md` antes de escribir
una línea** (regla de la casa: un módulo, un dueño, una rama). Hoy ese módulo
está prácticamente vacío y sus entregables viven sueltos en la raíz; esto es
buena oportunidad para que además tenga código propio.

---

## Requisitos técnicos

- **Un solo archivo HTML**, sin CDN ni fetch: todo CSS y JS inline. Tiene que
  funcionar con doble clic desde el disco, sin servidor.
- **Nada de `localStorage`/`sessionStorage`.** Estado en memoria.
- Debe verse bien en **modo claro y oscuro** (el adjunto ya trae las dos paletas).
- **Accesible:** la tabla gemela no es opcional; `aria-label` en los controles;
  navegable con teclado; nada que dependa sólo del color.
- Funcionar en una notebook: si la ventana es baja, que el grafo no quede
  miniatura (mirá cómo lo resuelve el adjunto con `min-height` y el botón ⛶).
- Sin acentos en nombres de archivo. Los `.ps1`, si hacés alguno, sin acentos y
  en UTF-8 sin BOM.

---

## Reglas del repo que hay que cumplir (no son burocracia, cada una nació de un error)

1. **Leé primero `coordinacion/URGENTE.md`.** Siempre, antes de elegir en qué
   trabajar. Si hay algo, se resuelve o se posterga por escrito.
2. **Después `MAPA.md`.** Es el índice; te ahorra abrir medio repo.
3. **Reclamá el módulo en `TABLERO.md`** antes de escribir.
4. **Las cuatro bitácoras se mueven JUNTAS** en el mismo cambio:
   `ESTADO-DEL-PROYECTO.md` (entrada arriba de todo, con el formato exacto que
   está documentado ahí), `EN-HUMANO.md` (lo mismo sin tecnicismos),
   `TABLERO.md` y `tablero_datos.js` (fecha, autor, estado, un hito nuevo arriba).
   **NO edites `TABLERO-CONTROL.html`.**
5. **El disco manda sobre las bitácoras.** Antes de escribir una cifra o un
   estado en el mapa, verificalo contra el archivo. La auditoría del 06-08
   encontró la base canónica con tres cifras distintas circulando.
6. **Todo lo temporal o regenerable va a `Archivos_Borrar/`**, y los scripts de
   un solo uso van neutralizados (guarda al principio que imprime y sale).
7. **`git check-ignore -q <archivo>`** sobre las salidas nuevas antes de
   commitear: las reglas `*.csv` / `*.parquet` del `.gitignore` ya escondieron
   trabajo cuatro veces.
8. Cuando termines, **reindexá y sellá el mapa**:
   `python .mapa/indexar.py .` y `python .mapa/indexar.py . --sellar-todo`.
   Y agregale al `README.md` de `producto/dashboard` su línea `**Resumen:**` y
   sus pistas en `## Buscar acá si` — de ahí sale el router de `MAPA.md`.

---

## Trampas conocidas (verificadas, no teóricas)

- **La raíz git está UN NIVEL ARRIBA del proyecto.** `.github/workflows/` vive en
  `Nowcast-Congreso/Nowcast-Congreso/`, no en `Nowcast Congreso Argy/`. Las rutas
  dentro de un workflow llevan el prefijo `"Nowcast Congreso Argy/"`
  **entrecomillado** (tiene espacios).
- **Mitad de los archivos del repo están en CRLF.** Si reescribís uno, preservá
  el final de línea original o el diff de git pasa a ser el archivo entero.
- **`variables/bloque` publica una columna `periodo` que NO significa lo mismo**
  que la `periodo` de `export`/`disciplina`/`ficha`/`asistencia`: la primera es
  un año legislativo (entero), las otras el período de dos años entre recambios
  ("2019-2021"). Si el mapa muestra ese enlace, aclaralo — cruzarlas por nombre
  daría cualquier cosa sin levantar un error.
- **`ingesta_ckan.py` usa CACHÉ** salvo `REFRESH=1`, y lo dice bajito en el log.
  HCDN publica con ~5 semanas de atraso.
- **No publicar P(sanción) de proyectos con origen Senado**: la base tiene sesgo
  de supervivencia (48% vs 1,7% de Diputados). Si el mapa muestra ese camino,
  tiene que llevar la advertencia.
- **La suite de tests del repo son scripts, no pytest.** Se corren de a uno
  (`python <archivo>`). No corras pytest sobre todo el repo: aborta, y peor,
  algunos chequeos pueden fallar sin que pytest lo note. Detalle en
  `tests/README.md`.
- **Las corridas largas van a la PC de Valle**, en PowerShell. Pasale el comando
  listo y qué tiene que dar.

---

## Criterios de aceptación

El mapa está listo cuando:

1. Se abre con doble clic, sin internet, y se ve bien en claro y oscuro.
2. **Se puede seguir con el dedo** el camino completo de un proyecto de ley:
   fuente oficial → script → base → variable → P(llega) → P(mayoría en origen) →
   puerta D (revisora) → P(sanción), con la fórmula visible en cada composición.
3. Las dos formulaciones (v1 y puertas A-D) están las dos, distinguidas, y las
   puertas parqueadas se ven como parqueadas.
4. Cada nodo dice **qué archivo lo implementa** y **en qué estado está, con dueño**.
5. La tabla gemela tiene exactamente la misma información que el grafo.
6. Los huecos conocidos se ven: Diputados 2020-23, `variables/contexto`,
   `evaluacion/metricas`, `evaluacion/backtesting`, `producto/api`.
7. Un integrante nuevo del equipo entiende de dónde sale el número **sin abrir
   una sola carpeta**.

**Antes de darlo por terminado:** abrilo, recorrelo, y verificá contra el disco
tres nodos al azar — que el archivo que dice exista, que la fuente sea la que es,
que el estado coincida con el README. Si el mapa se equivoca en tres nodos al
azar, se equivoca en todos.
