# ADR-0029 — Tema por capítulo + ampliar cobertura de temas — PARCIAL, sin crédito de API

**Fecha:** 2026-09-16 · **Estado:** CÓDIGO IMPLEMENTADO y TESTEADO, DATOS
PARCIALES (se cortó por falta de crédito de la API de Anthropic a mitad de
las dos corridas) · **Decide:** Claude, con permiso explícito de Franco (ver
las tres respuestas de la sesión: "Sí, alcance acotado" / "Sí, ampliar
cobertura" / "Sí, córranlo") · **Toca:** `variables/proyecto/src/
{tema_por_capitulo.py (nuevo), tema_por_proyecto.py}`, `datos/proyectos/data/
{proyectos.db, taxonomias.csv}`, `datos/taxonomias/data/asignaciones.csv` ·
**Se relaciona con:** ADR-0027 (composición por capítulos, el consumidor que
necesita este insumo), ADR-0024 (registro único), memoria de sesión
("Activaste el agente sin mi permiso" — esta vez SÍ se preguntó antes)

## Qué se pidió y qué se construyó

Franco autorizó dos tareas pagas (agente LLM) en la misma ronda de preguntas:

1. **Tema por capítulo**, alcance acotado a Ley Bases + los 145 proyectos de
   Diputados con votación en particular (el mismo universo que
   `capitulos_nombre.parquet` ya cubre) — el insumo que le faltaba a
   `composicion_capitulos.simular_capitulos` (ADR-0027) para poder correr
   sobre un proyecto real.
2. **Ampliar la cobertura de temas** a proyectos que TODAVÍA no se votaron
   (hoy sólo cubre el universo votado) — acotado a `fecha_ingreso >=
   2025-01-01` (9.910 proyectos, el universo "reciente/en trámite" que más
   necesita el nowcast).

**Módulo nuevo:** `variables/proyecto/src/tema_por_capitulo.py`. Mismo patrón
barato ya usado dos veces (clasificar por TEXTO, sin PDF): el texto es el
NOMBRE del capítulo (`capitulos_nombre.parquet`), con el `sumario` del
proyecto como CONTEXTO para desambiguar nombres cortos ("Del régimen",
"Disposiciones generales") — resuelto vía el mismo crosswalk
proyecto_id↔denominador que ya usa `tema_por_proyecto.py`, no reimplementado.
Produce `variables/proyecto/data/tema_por_capitulo.parquet` (contrato nuevo,
NO toca `proyecto_taxonomias` ni el registro único: es una granularidad que
esas tablas no tienen). 13 checks, `test_tema_por_capitulo.py`.

**Extensión:** `tema_por_proyecto.py` gana `denominadores_desde(fecha,
sin_clasificar=True)` y la CLI `clasificar --desde-fecha AAAA-MM-DD` — el
`estado` de `proyectos` está enteramente NULL (no sirve como filtro; no se
intentó arreglarlo, fuera de alcance), así que el corte es por
`fecha_ingreso`, más simple y suficiente. 3 checks nuevos,
`test_tema_por_proyecto.py` (24/24).

## Lo que pasó: se acabó el crédito de la API a mitad de las dos corridas

Las dos corridas (`tema_por_capitulo` y `clasificar --desde-fecha`) se
lanzaron EN PARALELO. A las 14:27-14:30 del 16-09, la API empezó a devolver
`400 — Your credit balance is too low`. **No es un bug de este código**: es
la cuenta de Anthropic sin saldo. El código maneja el error como cualquier
otro (resiliencia por fila, no corta el lote) — la consecuencia es que TODO
lo que faltaba clasificar quedó marcado como error, no como pendiente.

**Se cortó la corrida de cobertura ampliada apenas se detectó** (no tenía
sentido seguir generando cientos de errores 400 sin avanzar nada). La de
capítulos ya había terminado su lote (llegó al final de la lista, con la
segunda mitad en error) cuando se notó.

### Estado real de los datos, medido, no estimado

| | universo objetivo | clasificados | cobertura |
|---|---:|---:|---:|
| tema por capítulo | 704 pares (proyecto, capítulo) | **437** | **62,1%** |
| cobertura ampliada (desde 2025-01-01) | 9.910 proyectos | **328** | **3,3%** |

Los 437 capítulos clasificados son reales y usables — no hay nada a medias
en cada fila individual, sólo falta el resto de la lista. Ejemplo real, Ley
Bases: `Capítulo VII — "Consolidación de deuda del sector público nacional"`
→ `ECON.DEUDA` (0,95); `Capítulo IV — "De los Trabajadores independientes
con colaboradores"` → `TRAB.LABOR` (0,85). Distribución de áreas sobre los
437: POLINST (212), ECON (56), CULT (36), DESREG (34), JUST (25) y 9 áreas
más con menos de 20 cada una — razonable para un corpus de leyes ómnibus.

Los 328 proyectos nuevos de cobertura ampliada ya se sumaron al registro
único (`asignaciones.csv`: 9.427 → 10.111 filas) siguiendo el mismo camino
que la corrida de 1.182 proyectos de la sesión anterior:
`taxonomias_backup.py exportar` (2.655 → 3.339 filas respaldadas) y
`registro.py consolidar`.

**Nada se pierde por la interrupción — las dos corridas son idempotentes y
tienen checkpoint.** `tema_por_capitulo.py` guarda cada 25 clasificaciones;
`clasificar_por_titulo` cada 25 también. Re-correr EL MISMO comando, cuando
Franco recargue crédito, retoma exactamente donde se cortó (`solo_faltantes`
es el default en las dos, y ya está probado por tests):

```
python variables/proyecto/src/tema_por_capitulo.py clasificar
python variables/proyecto/src/tema_por_proyecto.py clasificar --desde-fecha 2025-01-01
```

## Por qué no se prendió nada con esto todavía

`tema_por_capitulo.parquet` es un insumo NUEVO, sin ningún consumidor
enganchado (ADR-0027 sigue sin conectar `composicion_capitulos` a un
proyecto real — este ADR sólo agrega el DATO, no el cableado, que sigue
pendiente y es otra decisión de alcance). La cobertura ampliada
(`proyecto_taxonomias`) ya alimenta `RECORD_POR_TEMA`/`TEMA_AUTO` para
cualquier proyecto que tenga taxonomías — con 328 proyectos nuevos, un
puñado de proyectos NO VOTADOS (el caso que antes no tenía tema) empieza a
tener `rec_i^tema` real. No es un cambio de comportamiento del motor: es más
cobertura para un mecanismo que ya estaba prendido.

## Verificación

`variables/proyecto/tests/test_tema_por_capitulo.py` (13 checks, sin red):
dedup por (proyecto_id, capítulo) quedándose con el nombre más largo;
contexto del sumario resuelto vía crosswalk, degrada limpio sin cruce;
clasificación real con clasificador inyectado, usando el sumario para
desambiguar; idempotencia; `--todos`; resiliencia (un capítulo roto no corta
el lote); `--limite`.
`variables/proyecto/tests/test_tema_por_proyecto.py` (+3 checks, 24/24):
`denominadores_desde` filtra por fecha Y excluye lo ya clasificado, con
`sin_clasificar=False` para el caso sin filtrar, degrada limpio sin matches.
`datos/taxonomias/tests/test_registro.py` sigue en 27/27 tras la nueva
consolidación.

## Addendum 2026-09-16 (más tarde el mismo día) — un bug real, encontrado tratando de USAR lo que había

Franco preguntó: *"¿Podemos usar lo que tenemos hasta ahora para recorrer el
modelo y sacar conclusiones sobre la plausibilidad de usar el tema por
capítulo?"* — la respuesta correcta era intentarlo de verdad, no simularlo.
Se armó `evaluacion/baseline/src/validar_leybases_por_capitulos.py`: arma el
roster real de Diputados por capítulo (misma función que usa
`nowcast_puertas.nowcast()` en producción), simula cada capítulo con
`composicion_capitulos` y compara contra lo que REALMENTE pasó en la ronda 1
de Ley Bases (2024-02-06).

**Al correrlo apareció un bug real, no una curiosidad menor.** El numeral de
capítulo se REINICIA en cada título — medido: en Ley Bases, "Capítulo I"
aparece bajo **6 títulos distintos** (I, II, III, V, VI, VIII), y lo mismo
"Capítulo II". La clave que se venía usando en TODO el trabajo del día
—`capitulos_nombre.py` (extracción del PDF) y `tema_por_capitulo.py`
(clasificación)— era `capitulo_num` SOLO, así que estaban fusionando bajo
una misma fila capítulos de partes completamente distintas de la ley (ej.
"Capítulo I" de emergencia pública y "Capítulo I" de régimen laboral,
tratados como si fueran el mismo).

**Corregido en el código, gratis (sin gastar créditos):**
- `capitulos_nombre.extraer_capitulos` ahora trackea el TÍTULO vigente
  (nuevo regex `_RE_TITULO_TEXTO`) y devuelve `(titulo_num, capitulo_num,
  nombre_capitulo)`, no sólo `(capitulo_num, nombre_capitulo)`.
- `tema_por_capitulo.cargar_capitulos`/`clasificar_capitulos` usan
  `(proyecto_id, titulo_num, capitulo_num)` como clave, con un chequeo
  explícito (`KeyError` claro) si se les pasa un `capitulos_nombre.parquet`
  del esquema viejo.
- `capitulos_nombre.parquet` se **regeneró gratis** (usa el caché local de
  PDFs, no la API): 320 → 546 filas — la diferencia es exactamente la
  fusión indebida que se deshizo.
- 15 checks nuevos/actualizados entre los dos módulos (`test_capitulos_nombre.py`
  15/15, `test_tema_por_capitulo.py` 15/15), incluido un test que reproduce
  el bug exacto (mismo `capitulo_num` bajo dos `titulo_num` distintos).

**Cuánto se salva y cuánto NO — medido, no estimado.** De los 437, se separó
cada (proyecto_id, capitulo_num) según si ese numeral de capítulo aparece
bajo UN SOLO título real (dato correcto y reetiquetable, gratis) o bajo MÁS
de uno (ambiguo, la clasificación vieja no dice cuál de los títulos era):

| | filas |
|---|---:|
| **salvadas** (reetiquetadas con su `titulo_num` real, sin gastar nada) | **242** |
| **perdidas** (capitulo_num ambiguo entre títulos: hay que reclasificar) | **195** |
| **total clasificado el 16-09 con la clave vieja** | 437 |

Las 242 ya están reescritas en `tema_por_capitulo.parquet` con la clave
correcta — no hace falta ni un llamado nuevo a la API para ellas. Las 195
perdidas quedan como referencia en
`tema_por_capitulo_OBSOLETO_clave_sin_titulo_2026-09-16.parquet`, junto con
las que ya estaban ahí. El universo real bajo la clave corregida es 1.084
pares — con los 242 salvados ya adentro, **quedan 842 por clasificar** (los
195 perdidos + los que nunca se habían intentado, porque separar por título
reveló capítulos reales que antes quedaban tapados bajo la fusión).

**Cuánta plata es esto, en limpio.** 195 llamados a Haiku con textos cortos
— del orden de centavos de dólar en total, no un gasto grande. Lo que se
pierde no es plata significativa; es TIEMPO (esos 195 capítulos hay que
volver a pedírselos al modelo) y la razón de fondo por la que importa: es la
prueba de que medir antes de escalar sirve — si el plan hubiera sido
"clasificar los 9.500+ que faltan primero, validar después", este mismo bug
se habría descubierto recién después de gastar el crédito completo con la
clave equivocada, mucho más que centavos.

**No se pudo completar la validación de plausibilidad que Franco pidió**:
sin capítulos correctamente clasificados no hay nada real que simular
todavía. Queda pendiente, bloqueada por crédito de API (para reclasificar) y
no por diseño.

## Addendum 2026-09-16 (tercera vuelta) — Ley Bases clasificada completa, la validación corrida de verdad, resultado HONESTO: no alcanza para concluir

Franco: *"Ya hice la recarga. Pausá la ampliación a los 9500 proyectos por
ahora. Vamos a concentrarnos en la ley bases."* Se clasificaron los 63
capítulos reales de Ley Bases (clave `(titulo_num, capitulo_num)` corregida,
`--proyecto-id HCDN272347`, nuevo filtro del CLI) — **100% cubierto**, sin
tocar la tarea de cobertura ampliada (queda pausada, intacta, 9.582
proyectos esperando).

**Se corrió `validar_leybases_por_capitulos.py` de verdad** (roster real,
walk-forward a 2024-02-01, simulación con $\eta_j$ compartido) — pero
también se encontró que la primera versión del propio script TENÍA EL MISMO
BUG que se acababa de corregir en otro lado (agrupaba por `capitulo_num`
solo, no por el par) — corregido antes de correrlo de verdad.

**Resultado real, y la limitación que importa más que el número:**

| título | capítulo | tema | pasó en la realidad (ronda 1) | $P_k$ simulado |
|---|---|---|:---:|---:|
| I | I | DESREG | ✅ Sí | 0,9160 |
| I | II | ECON | ❌ No | 0,8507 |
| II | I | AUX | ❌ No | 0,9160 |

**Sólo 3 de los 63 capítulos tuvieron tramo en la RONDA 1** — la mayoría de
la votación en particular de Ley Bases pasó en la RONDA 2 (después del
retiro y el recorte), no en la primera, así que no hay con qué comparar más
capítulos de esa ronda. **Con n=3 no se puede concluir nada con confianza
estadística.** Lo que sí se puede decir:

- **Dirección correcta, débil:** el capítulo que SÍ pasó (I/I) tiene el
  $P_k$ más alto de los tres (0,9160); el que peor la pasó en la realidad
  (I/II, 4 tramos negativos) tiene el $P_k$ más bajo (0,8507). Consistente
  con la hipótesis, pero un solo par no prueba nada.
- **Un caso no distingue, y por una razón identificable:** (II/I,
  "Reorganización administrativa") se clasificó como **AUX** — probablemente
  mal clasificado (reorganización administrativa es una reforma sustantiva,
  no trámite). Al ser AUX, `proyectar_postura` no encontró ninguna acta
  histórica con ese "tema" para condicionar y cayó a la postura
  INCONDICIONAL (el log lo confirma: *"condicionamiento tema=AUX... 0 actas
  en ventana; caigo a incondicional"*) — por eso su $P_k$ (0,9160) es idéntico
  al del capítulo que sí pasó: no es que el modelo haya fallado en discriminar,
  es que efectivamente no tenía información condicionada para ese capítulo.

**Conclusión honesta: el mecanismo es COHERENTE (nada roto, nada absurdo —
$P_{\text{todo}}$, $P_{\text{algo}}$, $\mathbb E[\text{superviv.}]$ salen
todos en el rango esperado y ordenados lógicamente) pero esta corrida NO
alcanza para validar ni descartar la hipótesis de plausibilidad.** Hacen
falta más casos comparables. Dos caminos, ninguno tomado todavía:
1. Escalar la clasificación a los otros ~144 proyectos con votación en
   particular (retomando la tarea pausada) para tener más pares
   capítulo-real vs. capítulo-simulado.
2. Revisar por qué "Reorganización administrativa" clasificó como AUX —
   podría ser un patrón sistemático (nombres de capítulo cortos/genéricos
   que el clasificador no tiene forma de distinguir de trámite) que también
   afecte a otros proyectos.

## Lo que queda pendiente (actualizado tras la tercera vuelta)

1. ~~Recargar crédito de la API~~ **RESUELTO** — crédito recargado el 16-09.
2. ~~Clasificar Ley Bases~~ **RESUELTO** — 63/63 capítulos, 100%.
3. ~~Correr la validación de plausibilidad~~ **RESUELTO, resultado
   INCONCLUSO** — mecanismo coherente, n=3 no alcanza para validar ni
   descartar la hipótesis (ver addendum de la tercera vuelta).
4. **Cobertura ampliada (9.582 proyectos) — PAUSADA a pedido explícito de
   Franco**, no retomar sin que él lo pida.
5. **Terminar `tema_por_capitulo` para el resto del universo de 145
   proyectos**: 842−63 = 779 pares restantes fuera de Ley Bases — es el
   camino más directo para conseguir más casos comparables y resolver la
   pregunta de plausibilidad con potencia real, pero no se arrancó: es una
   decisión de alcance de Franco, no algo que se pueda asumir.
6. **Investigar el patrón AUX** (capítulos sustantivos con nombre corto/
   genérico que el clasificador confunde con trámite) — encontrado en un
   caso (Ley Bases II/I), podría repetirse en otros proyectos y degradar
   silenciosamente el mecanismo (cae a incondicional sin avisar como error).

## Addendum 2026-09-16 (piloto sustantivo — hallazgo de granularidad, no de clasificación)

Franco pidió ampliar a "algunos proyectos, una prueba piloto sustantiva" para
tener más casos que los n=3 de Ley Bases. Dos intentos, ambos documentados en
`evaluacion/baseline/src/validar_piloto_capitulos.py`:

**Intento 1 (fallido):** elegí los 20 proyectos de una sola ronda con más
tramos según `capitulos_nombre.parquet` (PDF de la Orden del Día) — 33/33
después de completarlos, 160 capítulos clasificados (`tema_por_capitulo.parquet`
pasó de 305 a 467 filas). Al correr la validación: **0/20 proyectos tenían
resultado real por capítulo utilizable.**

**Por qué: descubrí una segunda fuente de título/capítulo, independiente de la
que uso para clasificar.** `votacion_por_articulo.py::extraer_titulo_capitulo`
saca `titulo_num`/`capitulo_num` del propio TÍTULO DEL ACTA de votación (texto
tipo *"TITULO VIII. CAPITULO VIII. ARTS. 208 AL 214."*) — es la única fuente
que dice qué resultado real tuvo CADA capítulo. El PDF de la Orden del Día
(que uso para clasificar, `capitulos_nombre.parquet`) es mucho más rico en
estructura pero NO dice qué pasó en la votación: son dos extracciones
independientes que sólo coinciden si el acta declara el título/capítulo
explícitamente, y eso pasa en **9 proyectos de los 160 con votación en
particular en Diputados** — el resto vota "en particular" sin que el acta
declare a qué capítulo pertenece cada tramo.

**Intento 2, con el universo correcto (también sin resultado, por una razón
distinta):** de esos 9 proyectos, **medí la granularidad real del resultado**
(`(titulo_num, capitulo_num)` ambos no nulos vs. sólo `titulo_num`) y encontré
que **Ley Bases es el ÚNICO proyecto de los 160 con resultado real a nivel
CAPÍTULO** (43 filas con ambos campos). **Los otros 8 proyectos con
título/capítulo declarado sólo lo declaran a nivel TÍTULO** (`capitulo_num`
siempre nulo) — HCDN289082 (26 tramos), HCDN274473 (9), HCDN293348 (4),
HCDN287440 (2), HCDN293445 (2), HCDN096679/HCDN285290/HCDN101088 (1 cada
uno). Clasifiqué los 4 capítulos que le faltaban a HCDN285290 (costo
trivial) para completarlo, pero no cambia el hallazgo: **no hay ningún otro
proyecto con resultado real DESAGREGADO POR CAPÍTULO para comparar contra
`P_k` simulado.**

**Lo que esto significa, sin adornar:** el límite no es cuánto clasifiquemos
(eso es barato y ya lo probamos dos veces) — es que **el dato de "qué pasó
en la votación" casi nunca baja a nivel capítulo**, salvo en la ley más
grande y mejor documentada del período (Ley Bases). El camino directo del
punto 5 de arriba ("terminar los 779 pares restantes") **no resolvería el
problema de n**: aunque clasifiquemos TODOS los capítulos de los 145
proyectos, seguiríamos sin saber el resultado real de la mayoría, porque esa
información no existe en el acta a ese nivel de detalle.

**Caminos que sí quedan abiertos** (ninguno tomado, decisión de Franco):
- **Validar a nivel TÍTULO en vez de CAPÍTULO** para los 8 proyectos con
  granularidad de título (HCDN289082 el más rico, 26 tramos en un solo
  título). Requiere combinar en logit los temas de los capítulos de cada
  título (mismo patrón que `ponderada_logit`/`combinar_logit`) para simular
  el título como unidad — no es lo mismo que se construyó (capítulo-por-
  capítulo) y no se armó todavía: es una pieza nueva, chica pero real.
- **Reconstruir el resultado real por capítulo desde el rango de artículos**
  del propio texto del acta (`"ARTS. 208 AL 214"`) cruzado contra los rangos
  de artículos de cada capítulo en el PDF de la Orden del Día — más
  laborioso, no explorado, podría no ser mucho más rico (la mayoría de las
  actas de votación particular ni siquiera declaran título/capítulo).
- **Aceptar que el n disponible para esta pregunta es estructuralmente bajo**
  y usar lo que hay (Ley Bases n=3 capítulos + potencialmente 8 proyectos a
  nivel título) sin perseguir más clasificación — la clasificación ya no es
  el cuello de botella.

Ningún capítulo/proyecto adicional se clasificó más allá de lo ya descripto
(160 + 4 = 164 clasificaciones nuevas esta sesión, todas ya en
`tema_por_capitulo.parquet`, ninguna perdida: quedan como insumo para cuando
`composicion_capitulos` se cablee a producción, aunque no sirvan para esta
validación puntual).
