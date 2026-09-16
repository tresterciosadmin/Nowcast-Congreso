# ADR-0023 — `votacion_por_articulo`: contrato nuevo, agrega sin reemplazar

**Fecha:** 2026-09-15 · **Estado:** APLICADO (sólo el contrato de datos; el
consumidor que compone P(algo)/P(sobrevive) NO está implementado) · **Decide:**
Claude, con el mandato de `coordinacion/PROMPT-MULTIETIQUETA.md` (Franco) ·
**Toca:** `datos/expedientes/src/votacion_por_articulo.py`,
`datos/expedientes/data/clean/votacion_por_articulo.parquet` ·
**Se relaciona con:** ADR-0016 (doctrina de la parte al todo — dónde entrará el
consumidor cuando exista), la formulación de $\eta_j$ en §III.A.3 de
`FORMULA-COMPLETA.md` (de la que depende la composición, todavía no prendida)

## Contexto

`datos/expedientes/src/enlace_senado.py::elegir_votacion` reduce todas las
votaciones de un proyecto en una cámara a UNA: la decisiva. Es correcto para lo
que alimenta (`cadena_camaras.parquet`, el insumo de
P(revisora | aprobó origen)). Pero las votaciones que descarta —la votación
**en particular**, artículo por artículo, que sigue a la general— no son
ruido: son el único insumo que existe, sin parsear una palabra de articulado,
para medir qué sobrevive de una ley y qué se cae en el recinto.

El caso testigo, medido el 15-09 sobre `acta_expediente_todas.parquet`: **Ley
Bases** (`HCDN272347`) se aprobó en general el 02-02-2024, perdió **6
artículos/incisos** en la votación en particular del 06-02-2024 (la noche que
se retiró del recinto), volvió el 30-04-2024 recortada y esa segunda ronda —47
tramos— pasó entera. El nowcast de hoy no ve nada de esto: cuenta "aprobado" y
sigue.

Medido en conjunto (todo el universo con proyecto_id resuelto): **206 de 1.428
pares (proyecto, cámara) — 14,4% — tuvieron votación en particular**; de los
153 proyectos con decisiva aprobada y al menos un tramo particular
identificable, **15 (9,8%) tuvieron ≥1 tramo NEGATIVO** pese a la aprobación
general (24 de 838 tramos, 2,86%).

## Decisión

Se agrega `datos/expedientes/src/votacion_por_articulo.py`, que produce
`data/clean/votacion_por_articulo.parquet`: **una fila por ACTA** (no por
proyecto), con `es_decisiva` calculado por la MISMA `elegir_votacion` que ya
usa `construir_cadena` (importada, no reimplementada — dos criterios
independientes de "cuál es la general" sería exactamente el tipo de bug que
las trampas de este repo ya castigaron dos veces) y `es_particular` por el
mismo regex `_RE_PARTICULAR`.

**No se toca `elegir_votacion` ni `cadena_camaras.parquet`.** El motor que
corre hoy (`modelo/ensemble`, `variables/bloque`, etc.) no lee este contrato:
cero impacto en el número publicado. Es agregar, no reemplazar — la instrucción
explícita del prompt que originó esta tarea.

## Lo que este ADR NO decide (a propósito)

1. **La composición de P(proyecto) a partir de los tramos.** El prompt es
   explícito: la P del proyecto no es el promedio de las P de los tramos ni el
   producto (supondría independencia, y el Nivel 0 de la fórmula ya tiene
   marcada como "supuesto activo y falso" la independencia entre cámaras —
   agregar un tercer supuesto de independencia sería el mismo error otra vez).
   La forma correcta es simular con el shock común $\eta_j$ (§III.A.3 de
   `FORMULA-COMPLETA.md`) y contar sobre esas mismas simulaciones. **$\eta_j$
   está formulado pero NO implementado.** Cuando se implemente, ese consumidor
   —y los dos números que Franco quiere publicar, P(se sanciona algo) y
   P(sobrevive sustancialmente)— ameritan su propio ADR, porque cambia la
   semántica del número publicado. Éste no la cambia: sólo agrega el dato
   crudo.
2. **El agrupamiento en CAPÍTULOS (B2).** Cada fila de este contrato es un voto
   registrado, que a veces cubre un artículo y a veces un bloque ("ARTS. 24 AL
   51") según cómo la cámara agrupó la votación ese día — no es una elección
   de este módulo. Agrupar por capítulo temático depende de tener el TEXTO del
   articulado, que hoy no está (sólo títulos de acta). No se arranca esa
   adquisición de datos sin decisión de Franco.
3. **Las columnas nuevas de argentinadatos** (`descripcion = "SE VOTA EN
   PARTICULAR"` explícito en el Senado, `quorumTipo`, `miembros`, `amn`) — hoy
   se infiere "particular" leyendo el título, lo cual funciona pero es más
   frágil que un campo explícito. Sumarlas a la canónica es un cambio de
   schema y pide su propio ADR (regla de `CLAUDE.md`); queda anotado, no
   implementado.

## Addendum 2026-09-16 — B2 arranca: `titulo_num`/`capitulo_num`, sin bajar un PDF

Franco: *"Sí, hay que hacerlo"* (arrancar B2). Antes de organizar una descarga
masiva de PDFs de Órdenes del Día, se probó algo más barato: **el propio
título del acta ya declara su posición en la ley.** Ley Bases lo confirma en
sus dos rondas: `"TITULO VIII. CAPITULO VIII. ARTS. 208 AL 214."` (O.D. 7,
segunda ronda) y `"TÍTULO II, CAP. I ART. 5 INCISO E."` (O.D. 1, primera
ronda — nótese la coma y la abreviatura `CAP.`, los dos formatos aparecen en
la práctica real, no son hipotéticos).

`extraer_titulo_capitulo(titulo)` saca esos dos numerales romanos con dos
regex (`TÍTULO\s+([IVXLCDM]+)`, `CAP(ITULO)?\.?\s+([IVXLCDM]+)`) y los agrega
como columnas nuevas al MISMO contrato (`titulo_num`, `capitulo_num`) — no
hace falta una tabla aparte ni bajar nada de red. Se guardan como TEXTO, no
como entero: alcanza con agrupar por igualdad, no hace falta ordenar ni sumar
romanos, y un numeral mal formado sigue sirviendo como clave de agrupamiento.

**Medido sobre los 1.423 tramos particulares reales:** 12,7% trae `titulo_num`
y 9,8% trae `capitulo_num`. **No es un techo del método: es que la mayoría de
las leyes NO están organizadas en títulos/capítulos formales** — sólo los
ómnibus complejos (como Ley Bases) lo hacen. La cobertura baja es, en sí
misma, una señal útil: qué proyectos son candidatos reales a agrupamiento por
capítulo y cuáles no lo necesitan porque ya son de un tema solo.

**Y se confirmó que la vía más profunda (el PDF) es viable, sin usarla
todavía.** Se bajó el PDF real de Ley Bases (`141-1.pdf`, la Orden del Día
0001) y se extrajeron 106.008 caracteres de texto con `parser_od.texto_de_pdf`
—ya existente, usado hoy sólo para extraer firmantes—, incluyendo el
articulado completo con sus encabezados: *"Capítulo II — Declaración de
emergencia pública y bases de delegaciones legislativas"*, seguido de
*"Art. 3° — Declaración. Plazo. [...]"*. Es la vía para conseguir el NOMBRE de
cada capítulo (útil para presentar el número, no para calcularlo) y para
cubrir los tramos que el título del acta no alcanza a describir. **No se hizo
el batch de 2.500+ descargas**: es una adquisición de datos grande y queda
para cuando Franco decida escalar esta parte, con su propio alcance acotado
(el candidato natural es la misma lista de 179 proyectos con votación en
particular que ya identificó B0, no el universo entero).

**Tests:** 8 checks nuevos en `test_votacion_por_articulo.py` (37 en total)
— los dos formatos reales de Ley Bases, la ausencia de capítulo en la
votación EN GENERAL, y que `construir()` propaga las columnas sin romper.

## Addendum 2026-09-16 (segundo) — B2 escala: 163 PDF bajados, NOMBRE de capítulo para el 88,9% de los pares reales

Franco: *"Deberiamos ahora seguir con escalar la descarga... Respecto del
multitema tenemos que encontrarle la vuelta"* (esto último resuelto aparte,
ver `coordinacion/RESUMEN-MULTIETIQUETA-COWORK.md`). Este addendum es la
continuación de B2: pasar de "se probó que se puede" (addendum anterior, un
solo PDF) a escala real, sobre el alcance que el propio addendum anterior
proponía — los proyectos de Diputados con votación en particular.

**Dónde vive cada cosa (respuesta a la pregunta de Franco: "¿carpeta nueva o
cómo lo guardamos?"):** el PDF crudo **no es una carpeta nueva** — es
descartable por diseño (régimen de `Archivos_Borrar/`, `CLAUDE.md`), así que
usa el mismo caché que ya existía, `Archivos_Borrar/od_pdf/` (el que llena
`ingesta_od.py` para las firmas de Diputados). Lo que SÍ es un contrato nuevo,
y por eso SÍ vive en `datos/expedientes/data/clean/` (viaja por git,
ADR-0020) es la salida YA PARSEADA: `capitulos_nombre.parquet`. Mismo
principio que ya rige el resto del repo — el insumo crudo se puede
regenerar bajándolo de nuevo; el trabajo de extraerle valor no.

**Escala del alcance real, medida (no la estimación del addendum anterior):**
de los 160 proyectos de Diputados con ≥1 tramo de votación en particular
(B0), **145 (90,6%) tienen al menos una Orden del Día de tipo LEY** —
`ingesta_od.py` gana `--solo-proyectos <archivo>` para bajar sólo las ODs que
cubren una lista de `proyecto_id`, sin tocar el corpus completo de ~2.500.
Esos 145 proyectos resuelven a **163 Órdenes del Día** (`archivo` es la
unidad real de descarga: una OD suele cubrir varios proyectos a la vez —
280 en total, "gratis" junto con los 145 que se pidieron).

**Tiempo real, no estimado:** 163 PDF, ~4 minutos, 0 fallas (`PAUSA=0,35s`
entre descargas + red). Muy por debajo de cualquier estimación basada en el
corpus completo (~2.500 ODs, 45-60 min): acotar a la lista de B0 es lo que
hace que esto sea barato.

**Extracción del NOMBRE de capítulo** (`datos/expedientes/src/
capitulos_nombre.py`, nuevo): lee el texto COMPLETO de cada PDF (no el
`texto_de_pdf` de `parser_od.py`, que corta a los 20 páginas por diseño —
correcto para firmantes, que están cerca del principio; incorrecto acá,
donde el capítulo de interés puede estar al final del articulado) y busca
encabezados "Capítulo N — Nombre" o "CAPÍTULO N\nNOMBRE". Resultado: **163
ODs leídas, 54 con al menos un capítulo con nombre reconocible, 320 filas**
(`datos/expedientes/data/clean/capitulos_nombre.parquet`).

**Cruzado contra el contrato B1/B2 real** (los 36 pares únicos
`(proyecto_id, capitulo_num)` que `extraer_titulo_capitulo` ya identificó
para Diputados, 5 proyectos): **32/36 (88,9%) consiguieron al menos un
nombre real del PDF** — de "Capítulo VIII" a "Capítulo VIII — Régimen
Infraccional y Recursivo Aplicable al VPU".

**Dos rondas de falsos positivos encontradas y corregidas EN ESTA CORRIDA,
no simuladas** (mismo principio de "medir, no asumir" del resto del repo):
1. Un capítulo sin nombre propio (numeral seguido directo del articulado)
   hacía que el regex agarrara el texto del primer artículo como si fuera el
   título ("ARTÍCULO 91.- Las disposiciones..."). 10/322 filas (3,1%) antes
   del filtro.
2. El encabezado de página repetido en cada hoja ("CÁMARA DE DIPUTADOS DE LA
   NACIÓN O.D. Nº 7") caía justo después de un "CAPÍTULO N" real y se leía
   como su nombre.
Las dos formas se filtran ahora (`_RE_ES_ARTICULO`, `_RE_ES_ENCABEZADO_PAGINA`
en `capitulos_nombre.py`), con test de regresión para cada una
(`test_capitulos_nombre.py`, 11 checks).

**Limitación honesta que QUEDA, sin resolver:** 18/32 pares con nombre tienen
MÁS DE UN candidato en conflicto entre distintas ODs del mismo proyecto —
`nombre_capitulo` de `capitulos_nombre.parquet` no es 1:1 con
`(proyecto_id, capitulo_num)`, así que este contrato **no elige** entre
candidatos (eso queda para quien lo consuma). Dos causas distintas mezcladas
en esos 18: (a) ruido residual —fragmentos de sumario, capítulos mal
delimitados— y (b) señal real: **Ley Bases (HCDN272347) tiene nombres
DISTINTOS y ambos correctos para el mismo `capitulo_num` entre su primera
ronda (perdió artículos, se retiró) y la segunda (volvió recortada)** — el
capítulo se renumeró/renombró entre rondas. Esto último no es un bug: es la
misma dinámica de "el proyecto cambia en el recinto" que motiva toda la
Parte B del prompt original, apareciendo en un lugar donde no se la estaba
buscando. Desambiguar (preferir la OD más reciente, o exponer las dos con su
fecha) queda para cuando haya un consumidor real de `capitulos_nombre.parquet`.

**Lo que este addendum NO hace:** no agranda la cobertura de QUÉ tramo
pertenece a qué capítulo (eso lo decide `extraer_titulo_capitulo` sobre el
título del acta, sin cambios) — sólo agrega el NOMBRE para presentación,
exactamente el alcance que el addendum anterior había anotado como
pendiente. No se escaló al Senado (usa HTML, no PDF — fuente distinta,
scope aparte) ni a los 15 proyectos sin OD de tipo LEY identificable.

## Verificación

`datos/expedientes/tests/test_votacion_por_articulo.py` (29 checks, sin red):
normalización de `resultado` a 4 clases (incluido el caso ambiguo `"NEGATIVO -
EMPATE"`, que se clasifica por el resultado oficial, no por la anotación);
ninguna fila se pierde (al revés de `elegir_votacion`, acá "agregar" es el
contrato); la decisiva coincide con la que ya usa `cadena_camaras.parquet`;
proyectos con el mismo `proyecto_id` en dos cámaras no se mezclan entre sí.

Corrida real sobre `acta_expediente_todas.parquet` (15-09-2026): 2.361 filas,
179 proyectos con más de una acta, reconstruye la secuencia completa de Ley
Bases sin diferencias con la crónica pública del caso.
