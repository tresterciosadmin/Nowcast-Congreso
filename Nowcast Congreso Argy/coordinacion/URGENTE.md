# 🔴 URGENTE — lo primero que se lee y se resuelve en CADA sesión

> **Regla de la casa (CLAUDE.md):** cualquiera del equipo — persona o Claude —
> abre este archivo **al empezar**, antes de reclamar tarea. Si hay algo acá, se
> resuelve o se decide explícitamente postergarlo (dejando dicho por qué).
> Nada se toca "después": lo que está acá bloquea o ensucia trabajo de otros.
>
> **Cómo usarlo:** al detectar algo urgente, se agrega un bloque con fecha, quién
> lo detectó, qué hay que hacer y por qué es urgente. Al resolverlo se BORRA de
> acá (queda el registro en `ESTADO-DEL-PROYECTO.md`, que es la bitácora
> permanente). Este archivo debería estar vacío la mayor parte del tiempo.
>
> ⚠️ **Nada de secciones de "resueltos".** El 04-08 se dejó una, y adentro quedó
> enterrado un pendiente **vivo** (la ingesta del Senado leyendo el padrón viejo)
> que nadie vio durante dos días. Un archivo que existe para que no se pueda no
> ver algo no puede tener una zona donde las cosas se esconden. Lo resuelto se
> borra: para eso está la bitácora.

---

> ℹ️ **Sacado de urgencias por decisión de Valle (07-08).** El sesgo de supervivencia del
> Senado (el modelo da 48% a proyectos del Senado contra 1,7% de Diputados, porque la base sólo
> tiene los que ya cruzaron a Diputados) **no se parchea de a un síntoma**: queda como insumo de
> la **Revisión de las Comisiones**, la línea que revisa el circuito completo comisión → cámara.
> Está desarrollado en `PLAN-DE-TRABAJO.md`. **Precaución vigente mientras tanto: no publicar
> P(sanción) de proyectos con origen Senado.**

## N. 🔵 Dos decisiones de Franco que el inventario de datos dejó a la vista
**Detectado:** 2026-09-08 · **decide Franco, no requiere corrida**

El inventario de datos que se agregó al MAPA el 08-09 encontró dos cosas el mismo día.

**1. SÉPTIMA vez que el `.gitignore` esconde trabajo pago — ya arreglado, falta commitear.**
`datos/canonica/data/alias_legislador_id.csv` son los **143 pares de `legislador_id` que
Franco revisó uno por uno el 04-09**. No se regenera: es criterio humano. `alias_legislador.py`
lo LEE, o sea que es insumo del pipeline. Estaba cayendo en el `*.csv` de la línea 5.

Lo grave es cómo se escondió: **`COMMITEAR.ps1` lo nombra explícitamente** en las rutas de su
commit 2, así que el `git add` lo salteó **en silencio** y el commit se hizo igual. Quien
pullee hoy y corra `entity_resolution.py` obtiene **cero merges** y no se entera: los 2.302
ids se quedan sin unificar y el modelo mide sobre carreras partidas.
Ya se agregaron las excepciones (más el CSV de veredictos, para que la próxima persona pueda
auditar por qué dos ids son la misma persona sin volver a molestar a Franco 153 veces).
**Falta que Franco commitee.**

**2. Los ocho `datos/export/data/votaciones_*.xlsx`: 49,6 MB versionados que ningún archivo
de código nombra.** Es, de lejos, el objeto más pesado del repo después de la base, y son más
de un tercio de los 195 MB de datos. Las dos lecturas posibles son opuestas y no se puede
elegir sin Franco: o son **el entregable** para que el equipo vea las votaciones sin correr
nada (y entonces está bien que viajen), o son un **resto** de la etapa de exportación (y
entonces son 49,6 MB que todos los del equipo se bajan en cada clone para nada).
**Pregunta concreta: ¿alguien del equipo abre esos xlsx?**

## M. 🔵 β se estimó ANTES de que el parser recuperara los `desconocido`
**Detectado:** 2026-09-06 · **una corrida de ~10 min**

Orden real de la corrida de Franco: β a las **12:56/12:59**, firmas del Senado a las
**13:11** y de Diputados a las **13:35**. O sea que β se estimó con el dato viejo y no ve
las 95 Órdenes del Día que el parser recuperó (`desconocido` pasó de **3.106 a 0** en las
dos cámaras: Diputados `unico` 73.681 → 76.333 y `mayoria` 36.058 → **36.065**; Senado
`unico` 17.031 → 17.478).

Además la canónica se dedupliqué a las **13:19**, después de β y antes del baseline: β está
estimado sobre la base con duplicados y el baseline sobre la limpia.

```powershell
.\REGENERAR.ps1 -Desde 5
```

Recupera el carácter de 97 proyectos de Diputados y 29 del Senado que hoy salen del panel,
y deja β y el baseline sobre la misma base.

## D. δ en el Senado: ya NO es 100% UNICO — pero sigue sin ser estimable, por otro motivo
**Detectado:** 2026-09-04 · **Corregido el diagnóstico:** 2026-09-06 · **necesita a Franco**

**Lo que decía este ítem, y ya no es cierto:** que el `reparto_caracter` del Senado era
**100% UNICO** y por lo tanto δ no tenía varianza. Eso salía del A/B del 04-09, sobre una
muestra de 400 actas y con el dato viejo. Con la regeneración completa:

| carácter | votos | **actas** |
|---|---:|---:|
| UNICO | 25.322 | 438 |
| mayoría | 1.138 | **20** |
| sólo minoría | 53 | **1** |

O sea que **hay varianza**, y el modelo la estima: `dict_mayoria = −0,6261` (p = 0,0014) y
`dict_solo_minoria = +2,5026` (p = 0,0).

### Y ese +2,50 con p = 0,0 es un artefacto, no un hallazgo

**Sale de UN acta.** El error estándar es cluster-robusto **por acta**; con un solo cluster
no es un error estándar, es un número que el estimador devuelve porque tiene que devolver
algo. Se nota en que su SE (0,157) es del mismo orden que el de la constante, con n = 53.

La regla de la casa lo agarra: *un número imposible es un bug, no un fenómeno.* Quedó
puesto en el código — `MIN_CLUSTERS_CONFIABLE = 20` en `estimar_beta_dictamen.py`, el
reparto se publica ahora **en actas además de en votos**, y por debajo del piso sale un
`logger.error` que dice explícitamente "NO leas dict_X como un hallazgo".

**`dict_mayoria` (20 actas) es el que se puede mirar**, y aun así 20 clusters está por
debajo de lo que la inferencia cluster-robusta pide (30-50): el signo se puede creer, la
magnitud y el p no.

### Lo que queda para Franco

1. **La propuesta original sigue en pie y ahora es más fuerte:** en el Senado el término
   del dictamen debería salir de la **disidencia** (213 firmas de 18.105 dicen "EN
   DISIDENCIA"), no del carácter — porque el carácter, aunque ya no sea degenerado, se
   apoya en 21 actas de 459. Es un cambio de definición de una variable de la fórmula, así
   que va con ADR.
2. **Re-correr el paso 6 completo** para que `beta_dictamen.json` (ambas cámaras) traiga
   también el diagnóstico de clusters. En mi entorno no entra; en el tuyo son ~9 min:
   `python modelo\ensemble\src\estimar_beta_dictamen.py`.

## E. Récord por tema: 24,6% → 51,8%. Faltan 2.134 títulos y créditos
**Trabajado:** 2026-09-06 · **frenado por: créditos de API** · retomar cuando haya

`tema_por_acta.py` leía `acta_expediente.parquet` — **la tabla angosta: 892 actas únicas,
todas de `ckan_diputados`**. Es el mismo cableado que trababa el β del Senado hasta el
ADR-0017. Corregido a `acta_expediente_todas.parquet` (5.036 actas, las cuatro fuentes).

Franco lo corrió el 06-09 y clasificó **1.550 actas nuevas** antes de quedarse sin
créditos (última a las 14:52).

| | antes | ahora | potencial |
|---|---:|---:|---:|
| clasificadas | 1.537 | **3.083** | 5.215 |
| cobertura de la canónica | 24,6% | **51,8%** | **87,7%** |
| faltan | — | **2.134** | — |

Y la corrida alcanzó fuentes que la tabla angosta **no podía ver**: `decada_votada` 1.370
y `senado` 377, que antes eran 0.

**Para retomar** (idempotente: sólo corre sobre lo que falta):

```powershell
python variables\proyecto\src\tema_por_acta.py
```

### Ya no se pueden perder: hay un registro único (06-09)

`datos/taxonomias/data/asignaciones.csv` — **6.772 asignaciones sobre 3.119 objetos**,
consolidadas desde las cuatro fuentes que estaban sueltas. CSV, versionado, con
procedencia por fila. `tema_por_acta.py` lo actualiza solo al terminar de clasificar.

**Y hacía falta una excepción en `.gitignore`:** el registro cae en el `*.csv` de la línea
5 y **no viajaba a git**. Sin eso, la consolidación no servía de nada. Hay un test cuyo
único trabajo es que nadie la saque.

### 🔵 Una decisión chica que queda abierta: `OPACO` merece su propio id

La revisión manual usó dos etiquetas que el vocabulario no tiene. Se mapean, y una de las
dos merece existir de verdad:

| etiqueta | mapeada a | por qué |
|---|---|---|
| `PROCEDIMENTAL` | `AUX.TRAMITE` | apartamiento de reglamento, cuestión de privilegio. El mapeo es correcto. |
| **`OPACO`** | `AUX.SINCLASIF` | *"Temas Varios"*, *"Votación en General y Particular"*: **el título no alcanza y hace falta el PDF** |

`AUX.SINCLASIF` dice "no encaja en ninguna, revisar". `OPACO` dice algo más preciso y más
útil: **el clasificador por título no puede saberlo**. Es exactamente el techo de la vía
`texto`, y con id propio se podría medir cuánto del 12,3% que falta es eso y cuánto es otra
cosa. Decide Franco: agregarlo a `docs/taxonomias/taxonomias.json` o dejarlo mapeado.

### Lo que hay que saber antes de retomar

- **El vocabulario nunca fue el problema.** `docs/taxonomias/taxonomias.json` está completo
  desde el 30-06 (74 ids, áreas + auxiliares + reglas de frontera), con loader y test.
- **`proyecto_taxonomias` en `proyectos.db` sigue en 0 filas** — verificado en la base, no
  copiado de este archivo. Es a nivel **proyecto**; `tema_por_acta` es a nivel **acta**, y
  es la que consumen el v2 de bloque y el récord por tema. Son dos tablas distintas y para
  esto sólo hacía falta la segunda. El respaldo `datos/proyectos/data/taxonomias.csv`
  nunca tuvo filas: se creó con la cabecera sola y así quedó (verificado en git).
- **Al deduplicar las actas gemelas, 21 clasificaciones quedaron apuntando a un acta que
  ya no existe.** Se remapearon a su gemela viva (4 colisiones resueltas por confianza).
  **Es un contrato a tener en cuenta:** todo lo que esté indexado por `acta_id` hay que
  remapearlo cuando el dedup descarta una copia. Quedan 2 sin remapeo (`ckan_diputados:411`
  y `412`), que nunca estuvieron en la canónica — son anteriores a todo esto.

## H. `_sources/` está VIEJO: rehacer la canónica desde ahí borra 181.309 votos
**Detectado:** 2026-09-06 · Claude · **bloquea: correr `build.py` sin el `run_pipeline` completo**

`datos/canonica/data/clean/_sources/` es la carpeta de insumos de la que sale
`votos_canonico.parquet`. Sus archivos son del **11-07**; la canónica publicada es del
**25-08**. La diferencia está toda en una fuente:

| fuente | en `_sources` (11-07) | en la canónica (25-08) |
|---|---:|---:|
| **argentinadatos** | **84.311** | **265.620** |
| decada_votada | 436.875 | 436.875 |
| ckan_diputados | 256.581 | 256.581 |
| senado | 53.910 | 53.910 |

O sea: `SOURCES=_sources python datos/canonica/src/build.py` reconstruye una canónica de
**834.749 votos en vez de 1.016.058**, sin avisar. Lo encontré el 06-09 queriendo pasar
el arreglo del distrito por el pipeline en vez de a mano: el rebuild dio 834.749 y por eso
el arreglo se aplicó **quirúrgicamente** sobre `votos_canonico.parquet` (ver la bitácora).

`run_pipeline.py` completo **no** tiene el problema: baja argentinadatos de nuevo antes de
buildear. El problema es el atajo — correr sólo los pasos 5 y 6.

**Qué hacer:** correr `python datos/canonica/src/run_pipeline.py` entero una vez, que deja
`_sources` al día. Hasta entonces, **no correr `build.py` suelto**. Lo ideal sería que
`build.py` avise cuando una fuente encoge, como ya hace `ingesta_padron.py` (URGENTE 3):
es el mismo control de encogimiento.

## I. Actas gemelas: aplicado. Queda decidir si el skill publicado se corrige
**Detectado y aplicado:** 2026-09-06 · **necesita a Franco: una lectura, no una tarea**

**274 actas entraban dos veces** (67.570 votos, 6,7%): 259 de `ckan_diputados` con su
gemela de `argentinadatos`, 15 de `decada_votada`, y las 17 de `manual_2026`. El dedup era
por `acta_id` y los ingestores prefijan distinto el MISMO id.

**Verificado que CKAN es la fuente más completa, como decía Franco** — yo había
recomendado lo contrario sin medirlo:

| en las 250 actas duplicadas | `ckan_diputados` | `argentinadatos` |
|---|---:|---:|
| `tipo_mayoria` | **100%** | 0% |
| `expediente` | **88%** | 0% |
| temas ya clasificados | **248** | 0 |

De esas 250, **12 no son de mayoría simple** (10 "Dos tercios", 2 "La mitad más uno"): con
argentinadatos ganando, esas 12 caían al default SIMPLE y el umbral del recuento era el
equivocado. **La `PRECEDENCIA` que ya estaba escrita da el resultado correcto** — no hubo
que cambiarla, sólo que el dedup viera las gemelas.

`manual_2026` salió del pipeline (`MANUAL_2026=1` para volver a prenderlo). El Excel no se
borra: sigue siendo la planilla de Franco.

### 🔵 Lo que hay que leer: el skill publicado estaba inflado

| | con duplicados | deduplicada |
|---|---:|---:|
| skill | 0,1720 | **0,1682** |
| Brier | 0,13255 | 0,13427 |

**Baja, y está bien que baje.** Los 46.979 votos duplicados se predecían mucho mejor que el
resto —skill 0,2032 contra 0,1698, Brier 0,111 contra 0,134— porque al predecir la segunda
copia el récord walk-forward **ya contenía la primera**: misma persona, mismo voto, mismo
día. El modelo estaba prediciendo algo que ya había visto.

O sea que **0,1682 es el número honesto y 0,1720 estaba inflado por duplicación**. Ninguna
era se mueve (2015-2019 y desde 2023 quedan iguales al cuarto decimal).

**Lo que falta:** re-correr el baseline completo para tener el número publicado sobre la
base limpia. Es la misma corrida de siempre.

## 2. 📋 LEER antes de tocar el motor: revisión metodológica del 25-08
**Detectado:** 2026-08-25 · Franco (objeciones) + Claude (verificación) · **bloquea: cambios al motor hechos sin conocer estos supuestos**

Franco revisó la formulación completa y planteó ocho objeciones. **Cuatro obligan a
cambiar el modelo.** Todo el detalle —posiciones, argumentos, fórmulas y qué hacer en
cada caso— en **`coordinacion/REVISION-METODOLOGICA-2026-08-25.md`**.

Los cuatro hallazgos que un cambio al motor NO puede ignorar:

| | hallazgo | consecuencia |
|---|---|---|
| 🔴 | **12,5% de las leyes se sancionan SIN dictamen** | el sobre tablas tiene **53% de sanción contra 1,9% general** y no está modelado en ninguna parte |
| 🔴 | **el quórum ignora las abstenciones** | `presentes = afirm + neg`; quien se abstiene está en el recinto. Bug acotado |
| 🔴 | **`P_B · P_D` supone independencia entre cámaras** | es falsa; el hook `estimar_delta_paso_origen` está en 0 |
| 🟡 | **el ε de incertidumbre es un clip, no un modelo** | tapa la sobreconcentración de suponer votos independientes |

**Lo que NO hay que "arreglar"** (verificado, funciona): la ausencia entra por
`p_presente` y da `NO_ACOMPANA = 1-π`; los ausentes fuera de emitidos es correcto;
el desvío tiene piso y no techo a propósito; `expanding`+`shift(1)` del ICG no tiene
leakage.

**Orden sugerido:** quórum (acotado) → condicionante del dictamen `δ = β₁ρ + β₂W`
(desbloquea el backtest) → sobre tablas (necesita ADR).

---

## F. ¿A qué linaje va el bloque personal de Daer? (queda de URGENTE 4)
**Detectado:** 2026-09-04 · Claude · **necesita a Franco** · no bloquea a nadie

URGENTE 4 se resolvió el 04-09: `BLOQUE DE LOS TRABAJADORES` salió del patrón de
IZQUIERDA y hoy cae en **OTRO / PROVINCIAL**. Lo que queda abierto es si ahí se queda.

**Ojo con el diagnóstico viejo, que estaba mal en el mecanismo:** no era un match
accidental por la palabra *trabajadores*. `BLOQUE DE LOS TRABAJADORES` era una
**alternativa literal** del regex, puesta a mano. Por eso el arreglo no fue una excepción
por delante del patrón: fue sacar la alternativa.

**Y era más grande de lo que decía:** no son 7 meses de 2017 sino **237 votos entre
2014-04-24 y 2017-11-23**, más 3 filas de padrón. Una sola persona en toda la canónica usa
esa etiqueta.

**La evidencia, con el mismo método con el que entró AUTODETERMINACION Y LIBERTAD**
(coincidencia con el núcleo de cada linaje, 89 actas con voto emitido):

| linaje | coincidencia | actas |
|---|---:|---:|
| PERONISMO FEDERAL | **90,0%** | 80 |
| FRENTE RENOVADOR (massismo) | **88,9%** | 63 |
| OTRO / PROVINCIAL | 86,5% | 89 |
| PROGRESISMO | 86,1% | 79 |
| FdT-UxP | 80,9% | 89 |
| RADICALISMO | 78,8% | 85 |
| **IZQUIERDA** | **78,6%** | 70 |

AUTODETERMINACION Y LIBERTAD entró con 100,0%. Daer con 78,6% y **séptimo de nueve**: no
es izquierda, y de eso no hay duda.

**La pregunta que queda:** 88,9% (massismo, que es donde están sus otros dos bloques en la
misma ventana) contra 90,0% (peronismo federal) está **demasiado parejo para decidirlo con
el dato solo**. Se dejó en OTRO / PROVINCIAL, que es el default conservador del mapa. Si
Franco quiere mandarlo a massismo, es una línea en `LINAJE_VENTANAS`.

## 5. Roster de jefes: quedan 9 filas MEDIA (eran 15) — y dos estaban MAL
**Detectado:** 2026-07-30 · **Trabajado:** 2026-09-04 · **bloquea: confiar en `lider_jefe_bloque`**

**El detalle completo, con fuentes y con cuánto aporta cada fila, está en
`variables/proyecto/data/VALIDACION-JEFES-2026-09-04.md`.** Resumen:

- **4 confirmadas → ALTA:** PINEDO/PRO Diputados (La Nación 01-12-2015, y se corrigió el
  `hasta` de 2015-12-01 a 2015-12-09), ATAUCHE/LLA Senado (El Tribuno de Jujuy 03-12-2023),
  MAYANS/FNyP (Río Negro 20-04-2022), CAMAÑO/Frente Renovador (Wikipedia + Chequeado 2018).
- **2 ELIMINADAS por estar mal**, con el motivo como comentario en el CSV (precedente Bianchi):
  - **LOSADA/UCR Senado**: no presidió el bloque. Naidenoff siguió hasta dic-2023 (letrap
    06-12-2023). Lo de Losada fue la **vicepresidencia del Senado** (Infobae 08-12-2021).
  - **FERNÁNDEZ SAGASTI/Unidad Ciudadana**: lo presidía **Juliana Di Tullio** (Río Negro,
    20-04-2022, con los dos bloques y su número de bancas).
- **9 siguen MEDIA**, cada una con qué le falta exactamente.

### Lo que necesita a Franco

1. **Extender el `hasta` de `PETCOFF NAIDENOFF`** de `2021-12-09` a `2023-12-09`. La fuente
   es explícita, pero **agrega** cobertura en vez de sacarla, así que no se tocó.
2. **Reemplazar la fila borrada por `DI TULLIO, JULIANA`** (Unidad Ciudadana, 2022-04 a
   2025-12). Mismo motivo: es agregar.
3. **Decidir qué mide la columna `bloque`: el bloque o el interbloque.** De eso dependen
   dos filas: Chequeado atribuye la presidencia del bloque UNA 2015-2017 a **Claudia
   Rucci**, no a Massa —que era el referente del **interbloque**—, y la de Federal-UNA a
   Camaño. **La fila de Massa aporta 62 proyectos y tiene la forma exacta del caso
   Bianchi.**
4. **Extender el `desde` de CICILIANI** de 2017-12 a 2015-12 (Chequeado 08-03-2018 la da
   asumiendo la jefatura socialista en 2015). Agrega cobertura.

### La de más volumen, y la que más conviene resolver

**DEL CAÑO / Frente de Izquierda aporta 349 proyectos** y es la única cuya duda es
*estructural*: si el FIT rota la jefatura entre PTS y PO —como rota las bancas—, una fila
única desde 2014 **no es imprecisa, es incorrecta**. No encontré fuente que nombre al
presidente del bloque del FIT por tramos.

> **La regla que deja el trabajo:** las dos filas que estaban mal tenían la misma forma —
> confundir un cargo del cuerpo (vicepresidencia del Senado) o el liderazgo de un espacio
> (referente del interbloque) con la **presidencia del bloque parlamentario**, que es lo
> único que mide esta tabla. Cuando una fuente dice "referente", "conduce" o "lidera" en
> vez de "preside el bloque", la fila NO está validada.

## 8. Récord por TEMA — DESTRABADO el 06-09: era la tabla de enlace equivocada

> 🔵 **Leer primero el ítem E.** Lo que este ítem daba por techo —*sólo el 24,6% de las
> actas tiene tema*— no era un techo: `tema_por_acta.py` leía la tabla de enlace angosta
> (892 actas, sólo `ckan_diputados`) en vez de la ancha (5.036, las dos cámaras). Con la
> ancha el potencial es **84,1%** y faltan clasificar 3.712 títulos, que es una corrida
> de Haiku. Todo lo de abajo se escribió con el diagnóstico viejo.


> **⚠️ MEDIDO el 2026-09-04 y el resultado es NO ALCANZA — pero por otro motivo del que
> decía este ítem.** La medición pendiente ("cuántos legisladores llegan a
> $n_i^{tema} \ge 8$") está hecha, con corte walk-forward, en
> `evaluacion/baseline/outputs/record_por_tema_2026-09-04.json`. **El cuello de botella
> no es el umbral: es que sólo el 24,6% de las actas tiene tema** y
> `proyecto_taxonomias` está vacía (ítem E). Dentro de ese 24,6%, el 65,3% de los votos
> llega a n≥8 por **área** (17 categorías) y el 43,3% por **tema_id** (70). Sobre toda la
> base, la cobertura efectiva es **16,1%** por área y **10,6%** por tema_id, contra
> **96,5%** del récord general. Conclusión: el término entra **encogido** contra el
> récord general (Empirical-Bayes, k=5), y **antes** hay que poblar la taxonomía.
> Lo que sigue vivo de este ítem es el compromiso con Franco sobre ρ, no la medición.


**Qué falta:** `rec_i^tema` — afirmativos/emitidos de cada legislador **condicionado a
la taxonomía del proyecto**, con corte walk-forward. Hoy sólo existe el récord general.

**Qué desbloquea:**

1. **El término $\rho$ del sobre tablas.** Quedó fuera de la formulación del 26-08 por
   falta de insumo, **no por haber sido descartado**. Franco: *"cuando modelemos la
   probabilidad de apoyar un proyecto con determinado tema, deberíamos revisar esta
   formulación, ya que el tema impactaría en el legislador"*. **Es una revisión
   comprometida, no opcional.**
2. **La medición que quedó pendiente:** cuántos legisladores llegan a
   $n_i^{tema} \ge 8$. Si son pocos, el término entra como ruido y hay que encogerlo
   contra el récord general (mismo esquema Empirical-Bayes que el share, $k=5$).

**Ojo con el sesgo que ya conocemos:** el récord general tiene Brier 0,435 en sobre
tablas —peor que decir 0,50— porque está calibrado para otra base. El temático puede
tener el mismo problema si la muestra por tema es chica. **Medir antes de creerle.**

**Dónde:** taxonomías en `datos/proyectos/data/proyectos.db` (`proyecto_taxonomias`),
enlace acta↔expediente en `datos/expedientes/data/clean/acta_expediente.parquet`,
votos en `datos/canonica/data/clean/votos_canonico.parquet`.

## L. `test_ensemble.py` aborta 1 de cada 6 corridas, sin fallar ningún chequeo
**Detectado:** 2026-09-06 · Claude · no bloquea, pero ensucia la suite

Los 33 chequeos pasan siempre. Lo que falla es el CIERRE del intérprete: sale
`terminate called without an active exception` y código 134 (SIGABRT), o sea un abort de
C++ en el teardown de alguna librería. Medido: 1 de 6 corridas, y después 5 limpias
seguidas.

**Por qué importa igual:** un test que falla al azar entrena a la gente a re-correr en vez
de mirar, y el día que falle de verdad nadie le va a creer. No lo perseguí.
