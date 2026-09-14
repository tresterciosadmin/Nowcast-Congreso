# ADR-0022 — En el Senado, disidencia = dictamen de minoría · el bloque personal de Daer va a massismo

**Fecha:** 2026-09-14 · **Estado:** Aceptada · **Quién:** Franco (decisión) + Claude (implementación, con Franco presente en la sesión).

---

## Decisión 1 — la disidencia se trata como dictamen de MINORÍA

**Contexto.** ADR-0017 (04-09) midió que el Senado casi nunca abre un dictamen de
minoría propio (0 de 193 Órdenes del Día leídas a mano): el desacuerdo se expresa
como firmas **"EN DISIDENCIA (PARCIAL/TOTAL)"** anexadas al mismo dictamen que la
mayoría firma, 213 de 18.105 firmas. Eso dejaba a δ (el condicionante del carácter
del dictamen) sin varianza en el Senado — `reparto_caracter = {UNICO: 100%}` — y el
ADR-0017 dejó la pregunta abierta: *"No decide qué hacer con la disidencia como
reemplazo del carácter en el Senado. Es la propuesta que queda sobre la mesa para
Franco."* (URGENTE.md ítem D lo mantuvo vivo desde entonces.)

**Decisión de Franco (14-09):** las actas de minoría del Senado están anexas al
dictamen de mayoría en formato de disidencia. Se tratan esas disidencias como
dictámenes de MINORÍA, igual que en Diputados.

**Implementación.** `datos/expedientes/src/parser_od.py::a_filas()`: una firma
cuyo `disidencia` no es `"none"` recibe `dictamen_clase = "minoria"` en su fila,
sin importar el rótulo (`d.clase`) del bloque de dictamen que la aloja. El rótulo
del BLOQUE no cambia — sólo el `dictamen_clase` efectivo de esa firma puntual. En
Diputados esto es, en la práctica, un no-op: sus minorías ya salen rotuladas en
bloques propios con cabecera calificada.

**Tests:** `datos/expedientes/tests/test_parser_od.py` — 61/61 OK, con el caso
nuevo (`disidencia se reclasifica como dictamen_clase='minoria'`) verificando las
dos cosas: la disidencia se reclasifica, y las firmas plenas NO cambian.

**APLICADO A LOS DATOS el 14-09.** Descargadas 1.902 Órdenes del Día del Senado
(1.778 nuevas + 123 en caché, 1 falla) y reconstruidas las firmas
(`construir_firmas.py --senado --desde-cero`). Resultado, medido sobre el
parquet:

| | antes (carácter puro) | después (+ disidencia) |
|---|---:|---:|
| `dictamen_clase` mayoría (Senado) | 20 actas | 16 actas (¹) |
| `dictamen_clase` minoría (Senado) | 1 acta | **205 actas** |
| firmas en disidencia reclasificadas | — | 194 (135 parcial + 56 sin especificar + 3 total) |

(¹) la cifra de "mayoría" baja levemente porque `_sin_repetidos` y el rescate
hacia adelante del parser cambiaron de base (más Órdenes del Día leídas), no
por el cambio de disidencia en sí.

**δ pasa a ser estimable de verdad, pero recién agrupando las dos cámaras.**
Re-corrido `estimar_beta_dictamen.py` (ambas cámaras y sólo Senado):

| | ambas cámaras (n=1.555 actas) | sólo Senado (n=455 actas) |
|---|---:|---:|
| actas con `mayoria` | **157** (¹) | 16 |
| actas con `solo_minoria` | **30** (¹) | 1 |
| `dict_mayoria` | −1,79 (p=0,0) | −1,34 (p=0,0) |
| `dict_solo_minoria` | −0,84 (p=0,0025) | +2,10 (p=0,0) — **1 solo cluster, no creer** |

(¹) `MIN_CLUSTERS_CONFIABLE = 20`: con las dos cámaras juntas, `mayoria` (157) y
`solo_minoria` (30) **cruzan el piso por primera vez** — antes el Senado solo
llegaba a 20/1. El propio `estimar_beta_dictamen.py` sigue marcando
`solo_minoria` del Senado en soledad como no confiable (`caracter_sin_clusters_suficientes`).

**El número publicado no se movió** (P = 0,9801, panel recalculado completo):
δ sigue **implementado en 0** en el camino que corre `nowcast_puertas.py`
(FORMULA-COMPLETA.md §III.A.2/§II.3) — esta corrida deja el término ESTIMADO
y con varianza real por primera vez, no lo PRENDE. Prenderlo es una decisión
de motor aparte, con su propio backtest.

**Control corregido de paso:** `verificar_regeneracion.py` tenía un chequeo
que asumía "minoria en senado-2018-16.pdf siempre tiene que ser 0" (el caso de
la reimpresión de ADR-0017). Ese archivo tiene una disidencia real (Beatriz
Mirkin, "EN DISIDENCIA PARCIAL") que con esta decisión pasa a `minoria` a
propósito. El control ahora verifica lo que de verdad importa — que la
reimpresión no duplique firmas (19, ni 38 ni 0) — en vez de un número que
esta misma decisión volvía falso.

## Decisión 2 — el bloque personal de Daer va a FRENTE RENOVADOR (massismo)

**Contexto.** URGENTE.md ítem F (desde el 04-09): `BLOQUE DE LOS TRABAJADORES` es
la etiqueta personal de Héctor Daer (CGT, peronista, 237 votos 2014-2017), sacada
del patrón de IZQUIERDA el 04-09 por ser un falso positivo. Sin alternativa cae al
mapa `LINAJE` exacto, que no la tenía, y termina en `OTRO / PROVINCIAL` (el default).
Medido por coincidencia con el núcleo de cada linaje (89 actas con voto emitido):
FRENTE RENOVADOR (massismo) 88,9% vs. PERONISMO FEDERAL 90,0% — demasiado parejo
para decidirlo con el dato solo. Sus otros dos bloques en la misma ventana
(FRENTE RENOVADOR, UNIDOS POR UNA NUEVA ARGENTINA) ya son massismo.

**Decisión de Franco (14-09):** va a massismo.

**Implementación.** `datos/canonica/src/entity_resolution.py`: se agrega
`"BLOQUE DE LOS TRABAJADORES": "FRENTE RENOVADOR (massismo)"` al diccionario
`LINAJE` (mapa exacto, no alternativa del patrón — mismo criterio con el que se
sacó del patrón el 04-09: una sola persona, mejor en el mapa exacto que en un
regex). Regenerado `votos_resuelto.parquet` (959.815 filas, mismo total — sólo
cambia el `bloque_linaje` de las filas de Daer) y `variables/bloque/outputs/serie_bloque.parquet`
(304 filas, mismo total).

**Parcheado a mano** (sin re-correr el pipeline completo, ver nota de riesgo más
abajo): las 3 filas de padrón que traían el label viejo —
`datos/padron/data/{padron_diputados.csv, padron_diputados_historico.csv}` (2 filas)
y `variables/legislador/data/legislador_bloques.parquet` (1 fila) — al mismo valor
que produciría una corrida completa de `padron_diputados_historico.py` sobre el
`votos_resuelto.parquet` ya corregido.

**⚠️ Hallazgo colateral, sin resolver:** correr
`datos/padron/src/padron_diputados_historico.py` de punta a punta en esta sesión
dio **6.124 filas / 1.952 legisladores**, contra las **7.323 filas / 2.443
legisladores** del archivo commiteado — una diferencia de ~1.200 filas que **no
puede explicarse por el cambio de Daer** (un solo legislador). Se revirtió esa
regeneración completa y se aplicó el parche quirúrgico de arriba en su lugar. La
causa queda sin diagnosticar — anotado en `coordinacion/PARA-FRANCO-2026-09-14.md`.

**Tests:** `datos/canonica/tests/test_entity_resolution.py` — 21/21 OK, con el
caso `BLOQUE DE LOS TRABAJADORES no es izquierda` actualizado para esperar
`FRENTE RENOVADOR (massismo)` en vez de `OTRO / PROVINCIAL`.

## Medido: el número publicado no se movió

Con las dos decisiones aplicadas (más el flip de `MATCH_AUTOR_FUZZY`, ver commit
aparte): `P(aprobación)` recalculado con el panel completo (`nowcast_puertas_html.py
diputados --fecha 2026-06-01 --origen EJECUTIVO`) da **0,9801**, idéntico al de
antes de estos tres cambios. Suite completa: 41/41. Daer no integra el Congreso
vigente (2026), así que su reclasificación no toca el roster actual; el efecto es
sólo en el récord histórico agregado por linaje, y a esa escala (119 votos sobre
~960k) no mueve el cuarto decimal.

## Lo que este ADR NO hace

- No re-corre `construir_firmas.py` (Decisión 1 sigue sin dato hasta esa corrida).
- No investiga la caída de filas en `padron_diputados_historico.py` (queda
  estacionado).
- No toca ningún otro linaje ni ningún otro bloque.
