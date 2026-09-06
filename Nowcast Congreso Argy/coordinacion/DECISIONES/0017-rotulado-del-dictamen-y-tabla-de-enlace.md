# ADR-0017 — Cómo rotula el Senado sus dictámenes, y cuál es la tabla de enlace acta↔expediente

**Fecha:** 2026-09-04 · **Estado:** Aceptada (a revisar por Franco) · **Quién:** Claude (sesión autónoma), sobre URGENTE 11.

---

## Contexto

URGENTE 11 decía que el Senado tiene **cero dictámenes de mayoría** contra 28% en
Diputados, y que eso era **un bug del parser**: `_clase_del_dictamen()` arrancaba en
`clase = "unico"` y sólo la cambiaba si encontraba una cabecera `MAYOR`/`MINOR`. El
síntoma paralelo era que `estimar_beta_dictamen.py --camara senado` devolvía
**"0 actas con dictamen identificado"**.

La instrucción era leer los PDF antes de tocar el regex. Se leyeron **193 Órdenes del
Día reales del Senado de 2008 a 2026** (muestra aleatoria estratificada por año, más
los ODs más grandes de cada año, que son los más disputados).

## Lo que dicen los PDF — transcripción

El Senado rotula el carácter **en el SUMARIO**, no en el cuerpo. Las formas encontradas:

| forma | n de 193 | ejemplo |
|---|---:|---|
| `Dictamen en el proyecto de ley…` | 144 | `senado-2013-505.pdf` |
| `Dictamen en el mensaje y proyecto de ley…` | 23 | `senado-2026-104.pdf` |
| `Dictamen en distintos proyectos de ley…` | 9 | `senado-2008-1205.pdf` |
| `Dictamen en los proyectos de ley…` | 8 | `senado-2010-964.pdf` |
| `Dictamen en las modificaciones…` | 3 | |
| **`Dictamen de mayoría en el proyecto de ley…`** | **3** | `senado-2008-1168.pdf` |
| `Dictamen en los distintos…` / `en varios proyectos` | 3 | |

Y el **cuerpo** abre siempre con la genérica:

    DICTAMEN DE COMISIÓN

    Honorable Senado:

salvo en la forma calificada, donde aparece:

    DICTAMEN DE COMISIÓN EN MAYORIA          (senado-2009-485.pdf)

Cita literal del testigo, `senado-2008-1168.pdf` (SIPA/AFJP, CD-70/08):

> COMISION DE PRESUPUESTO Y HACIENDA Y DE TRABAJO Y PREVISIÓN SOCIAL
>
> **Dictamen de mayoría** en el proyecto de ley venido en revisión por el que se
> dispone la unificación del Sistema Integrado de Jubilaciones y Pensiones…
> (CD-70/08)
>
> **DICTAMEN DE COMISION**
>
> Honorable Senado: …
>
> Sala de las Comisiones, 12 de Noviembre de 2008
>
> Roberto F. Ríos.- Julio A. Miranda.- … Marina R. Riofrío.-
>
> **EN DISIDENCIA PARCIAL:**
>
> Roxana I. Latorre.

**Cero de las 193 dicen "Dictamen de minoría".**

## Decisión 1 — el default deja de ser `"unico"`

`_clase_del_dictamen()` devuelve **`"desconocido"`** cuando no encuentra ninguna
cabecera. `"unico"` sólo se afirma cuando el documento trae la cabecera genérica.

Arrancar en `"unico"` convertía *"no encontré el rótulo"* en una afirmación positiva
sobre el documento. Son dos cosas distintas y los consumidores tienen que poder
separarlas.

## Decisión 2 — una cabecera GENÉRICA no pisa a una calificada

La regla vieja era "la última cabecera antes del ancla manda". En el Senado eso
significa que la genérica del cuerpo **siempre** borra el rótulo del sumario. Ahora,
una vez vista una cabecera calificada (mayoría/minoría), una genérica posterior no la
degrada. En Diputados no cambia nada: sus cabeceras calificadas se siguen pisando
entre sí en orden, que es lo que hace falta para que cada ancla reciba la suya.

Se agrega además la forma `DICTAMEN DE COMISIÓN EN MAYORÍA/MINORÍA`, que el regex
viejo leía por la rama genérica.

## Decisión 3 — una reimpresión no es un segundo despacho

`senado-2018-16.pdf` (Parque Nacional Aconquija) imprime el mismo dictamen **dos
veces**: misma fecha de sala ("4 de abril de 2018") y los mismos 19 firmantes. El
parser veía dos anclas y la regla *"un segundo dictamen sin cabecera propia es de
minoría"* lo rotulaba como **dictamen de minoría**. Esas 19 filas eran **las únicas 19
minorías del Senado en todo el parquet** (18.105 filas): un fenómeno entero que no
existía, nacido de una reimpresión.

Se descartan los bloques con la misma `(fecha_sala, lista de firmantes)`, y la cuenta
viaja al parquet en la columna nueva **`dictamenes_repetidos`** — no se esconde.

En el mismo archivo apareció un segundo problema: `ANEXO` no estaba entre los cortes
del bloque de firmas, así que el parser seguía leyendo un **padrón catastral** y le
sacaba 18 nombres inventados ("Quebrada del Portugués", "Estancia El Mollar"): 37
firmantes donde el documento tiene 19. `ANEXO` se agrega a `CORTES`.

## Decisión 4 — `acta_expediente_senado.parquet` se llama `acta_expediente_todas.parquet`

Tenía las **dos** cámaras (2.745 actas del Senado y 2.285 de Diputados) y un nombre que
decía "senado". Por eso nadie del lado del modelo la miraba, mientras
`acta_expediente.parquet` —el volcado crudo de CKAN, **sólo Diputados**, sin
`proyecto_id` resuelto— se usaba para las dos.

`estimar_beta_dictamen.py` y `baseline_voto_individual.py` pasan a leer la tabla
resuelta, y las **dos** cámaras de firmas, con el carácter calculado **por
(proyecto, cámara)**: lo que un senador lee cuando vota es el dictamen de SU cámara,
no el de Diputados.

## Consecuencias — y la parte donde la hipótesis de URGENTE 11 no se sostiene

**El parser sí tenía un bug, y es real: `senado-2008-1168.pdf` dice literalmente
"Dictamen de mayoría" y el parquet lo tenía como `unico`.** Pero es un bug **chico**.
Medido sobre los PDF, no supuesto:

| | Diputados (220 ODs) | Senado (229 ODs) |
|---|---:|---:|
| `unico` → `mayoria` | 1 | 4 |
| `unico` → `desconocido` | 8 | 6 |
| reimpresiones descartadas | 0 | 1 |
| firmas antes / después | 6.968 / 6.968 | 2.492 / 2.413 |

Y sobre la muestra **aleatoria** de 193 ODs del Senado, la tasa de dictámenes
calificados es **3/193 = 1,6%** (IC 95% de Wilson ≈ [0,5%; 4,5%]), y de minoría **0**
(cota superior 95% ≈ 1,9%).

> **Conclusión: el 0% de mayorías del Senado es en su enorme mayoría un fenómeno real,
> no el default de una función.** El Senado casi no publica despachos de mayoría y
> minoría en sus Órdenes del Día de proyectos de ley: **el desacuerdo se expresa como
> "EN DISIDENCIA (PARCIAL/TOTAL)" dentro del dictamen único** — 213 de 18.105 filas de
> firma. Es una diferencia institucional entre cámaras, no un hueco del parser.

Esto **confirma** la entrada del 21-08 de `ESTADO-DEL-PROYECTO.md` ("El Senado NO
rotula mayoría/minoría… se buscó en 35 Órdenes del Día leídas: cero coincidencias") y
**corrige** el diagnóstico de URGENTE 11 del 03-09, que la contradecía. La versión de
193 ODs le agrega la excepción que las 35 no tenían con qué ver: existe un 1,6% que sí
se rotula, y ese 1,6% el parser lo estaba perdiendo.

**Lo que sí desbloqueaba al Senado era el cableado, no el parser.** El
"0 actas con dictamen identificado" venía de leer una tabla de enlace de una sola
cámara y un solo parquet de firmas. Con la tabla resuelta:

| tabla de enlace | actas con carácter (Diputados / Senado) |
|---|---|
| `acta_expediente.parquet` | 710 / **0** |
| `acta_expediente_todas.parquet` | 1.705 / **474** |

**Pero δ sigue sin ser estimable en el Senado, y ahora se sabe por qué.** La corrida
`--camara senado --muestra 400` da un panel de 23.047 votos con
`reparto_caracter = {"UNICO": 23047}`: **100% único, sin varianza**. β₁ y β₂ **sí** se
estiman (+2,22 y +2,28, p < 0,001). δ no, y no lo va a arreglar ningún parser: hay que
modelar el Senado con **la disidencia**, que es donde su desacuerdo deja rastro.

## Lo que este ADR NO decide

- **No prende nada** en el motor: δ, β₁, β₂ siguen apagados (§III.A.2 de
  `FORMULA-COMPLETA.md`). La corrida por defecto da el mismo número que ayer.
- **No reconstruye los parquets.** El cambio del parser está en el código y en los
  tests; los `dictamenes_firmas*.parquet` siguen siendo los del 03-09 hasta que se
  corra la reconstrucción (comando en `ESTADO-DEL-PROYECTO.md`).
- **No decide qué hacer con la disidencia** como reemplazo del carácter en el Senado.
  Es la propuesta que queda sobre la mesa para Franco.


---

## Anexo 06-09-2026 — los `desconocido` eran recuperables, y casi todos

La clase `desconocido` que introdujo este ADR hizo bien su trabajo: separó "no encontré el
rótulo" de "despacho único", y `_caracter_por_proyecto_camara` la deja **fuera** del panel
en vez de contarla como `UNICO`. O sea que nunca contaminó nada. Lo que sí hacía era
**costar cobertura**: 97 proyectos de Diputados (2,7%) y 29 del Senado (2,3%) quedaban sin
carácter.

Se fueron a leer las 95 Órdenes del Día que quedaban en `desconocido` — las 39 del Senado
y las 56 de Diputados — y **ninguna de las 95 era ilegible**. Eran tres cosas distintas:

**1. El Senado tiene una CUARTA forma de rotular.** Las 39, sin una sola excepción:

> *"**Dictamen en el proyecto de ley** de la señora senadora Latorre, por el que se..."*

Un dictamen a secas, sin "de comisión" y sin calificativo. Entra como genérica —dice que
hay un dictamen, no de qué carácter es— y va **última** en la alternancia, para que
"Dictamen **de mayoría** en el proyecto..." siga cayendo en la calificada. Hay un test que
lo controla.

**2. Un off-by-one que costaba mayorías.** `_clase_del_dictamen` buscaba la cabecera en
`[0, pos_ancla)`, medio abierto. En la rama `sin_ancla` (2020-2021) el "ancla" es el
arranque del bloque de firmas y la cabecera abre ese mismo bloque: en `131-2469.pdf`
*"Dictamen de mayoría"* y el bloque arrancan los dos en la posición 627, y el intervalo la
excluía **por un carácter**. Se perdía una mayoría entera sin que nada fallara.

**3. La cabecera puede estar DESPUÉS del ancla.** `126-445.pdf` cierra con *"Sala de la
comisión"* en 657 y recién abre el cuerpo del dictamen en 1030.

**La solución para 2 y 3 es un rescate hacia adelante que sólo corre cuando la respuesta
habría sido `desconocido`**, acotado por el arranque del dictamen siguiente y por 3.000
caracteres, y que toma la **primera** cabecera (hacia adelante, la primera es la que abre
este dictamen; las de más allá son del que sigue).

### Medido

| | hoy | con el arreglo |
|---|---|---|
| Senado, 39 OD en `desconocido` | — | **39 `unico`** |
| Diputados, 56 OD en `desconocido` | — | **55 `unico` + 1 `mayoria` + 1 `minoria`** |

Y el control que decide, porque un arreglo que mueve lo que ya estaba bien no es un
arreglo: sobre **340 Órdenes del Día con clase ya asignada** (200 del Senado + 140 de
Diputados, 377 dictámenes), **cero cambios**.

`131-2469.pdf` pasa a tener mayoría **y** minoría, o sea que ese proyecto entra al panel
como `DISPUTADO`, que es la categoría más informativa de todas.

**Para que esto llegue al dato hay que re-correr `construir_firmas` en las dos cámaras**
(~60 min, sin red).
