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

## P. 🔵 La sonda de argentinadatos ya tiene respuesta: la API NO publica el expediente
**Detectado:** 2026-08-08 · **Contestado:** 2026-09-09 · **decide Franco, no requiere corrida**

`explorar_campos.py` existía desde el 08-08 para contestar una pregunta que necesitaba
internet: *¿la API expone el expediente y lo estamos tirando, o no lo publica?* Se corrió el
09-09. La respuesta es **no lo publica**, y el "arreglo de dos líneas" que la sonda
hipotetizaba **no existe**:

- **Diputados (1.326 actas):** 22 campos, los 22 presentes en el 100% de las actas.
  **Ninguno es el expediente.** `numeroActa` es el número de acta dentro de la reunión.
- **Senado (321 actas):** hay un campo `proyecto`, poblado en el **95,3%** — y **cero** de
  esas 306 trae un expediente. El **62,0%** trae `O.D. N/AA` y el **33,3%** trae
  `ORDEN DEL DIA ...` en prosa.

**Lo que sí abre.** En el Senado el enganche por Orden del Día está al alcance en el 95,3%
de las actas, y este repo ya sabe trabajar con ODs (`datos/expedientes`, y la regla de la
casa de que la clave es `(periodo, od_numero)`). Es mejor que el rescate por título. Dos
advertencias antes de intentarlo: el campo viene en **dos formatos** distintos, y a veces es
un **rango** (`O.D. 41 al 59/24`), o sea varias ODs en un acta.

En Diputados no hay campo, pero el título menciona `O.D.` en el **39,3%** y algo con forma
de expediente en el **24,1%**.

## E. Récord por tema: frenado por créditos de API — DEJADA FRENADA (decisión de Franco 14-09)
**Trabajado:** 2026-09-06 · **frenado por: créditos de API** · **medido de nuevo el 2026-09-14, sin gastar API**

`tema_por_acta.py` leía `acta_expediente.parquet` — la tabla angosta, sólo `ckan_diputados`.
Corregido a `acta_expediente_todas.parquet` (las cuatro fuentes) desde el 06-09.

**Medido el 14-09 (offline: `cargar_actas`/`cargar_actas_canonica` + `_leer_previas`, sin
llamar al clasificador):**

| fuente (`--fuente`) | universo | ya clasificadas | **faltan** |
|---|---:|---:|---:|
| `expedientes` (default; CKAN, 2011-19) | 5.043 | 3.083 | **1.960** |
| `canonica` (título del acta, incluye 2020+) | 5.998 | 3.083 | **2.915** |

El universo `expedientes` creció de 5.036 a 5.043 desde la última medición (regeneración
del 13/14-09); `canonica` es el potencial más amplio (incluye lo que `expedientes` no
puede ver: `decada_votada`, `senado`, actas 2020+). Las 3.083 clasificadas no cambiaron
— nadie corrió el clasificador desde el 06-09.

**Verificado que la escritura al CSV es sana (lo que pedía Franco):** las **3.083** filas
de `variables/proyecto/data/tema_por_acta.parquet` (la caché del clasificador, no viaja
por git) están **las 3.083, sin faltar ninguna**, en
`datos/taxonomias/data/asignaciones.csv` (el registro único y versionado). Las 36
asignaciones de más en el registro (6.772 filas sobre 3.119 objetos vs. 3.083 actas de
`tema_por_acta`) vienen de las otras fuentes que `registro.py` consolida (revisión manual,
etc.), no de una pérdida. **El pipeline de guardado funciona.**

**Para retomar cuando haya créditos** (idempotente: sólo corre sobre lo que falta):

```powershell
python variables\proyecto\src\tema_por_acta.py                        # fuente expedientes, 1.960 actas
python variables\proyecto\src\tema_por_acta.py --fuente canonica      # universo mas amplio, 2.915 actas
```

### Ya no se pueden perder: hay un registro único (06-09)

`datos/taxonomias/data/asignaciones.csv` — consolidado desde las cuatro fuentes que
estaban sueltas. CSV, versionado, con procedencia por fila. `tema_por_acta.py` lo
actualiza solo al terminar de clasificar.

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

## 5. Roster de jefes: RESUELTO por completo (Del Caño acotado, 14-09)
**Detectado:** 2026-07-30 · **Trabajado:** 2026-09-04 · **Resuelto:** 2026-09-14

**El detalle completo, con fuentes y con cuánto aporta cada fila, está en
`variables/proyecto/data/VALIDACION-JEFES-2026-09-04.md`.** Decisiones de Franco del
14-09, ya aplicadas en `variables/proyecto/data/jefes_bloque.csv` (**"medimos bloque, no
interbloque, mantenelo así"** resuelve el punto 3 de abajo):

1. `PETCOFF NAIDENOFF` extendido a `2023-12-09` (UCR Senado).
2. `DI TULLIO, JULIANA` reemplaza a Fernández Sagasti (Unidad Ciudadana, Senado).
3. La columna `bloque` mide el bloque, no el interbloque — las filas de MASSA/UNA y
   CAMAÑO/Federal-UNA quedan como estaban.
4. `CICILIANI` extendida a `2015-12-10`; `BINNER` acortado a `2015-12-09` (mismo corte,
   confirmado por Franco) para no solapar en el mismo bloque.

Medido: P(aprobación) sin cambios en ninguno de los cuatro. 41/41 tests, 16 controles OK.

### La de más volumen — investigada y acotada, no cerrada del todo

**DEL CAÑO / Frente de Izquierda aporta 349 proyectos.** La duda era *estructural*: si el
FIT rota la jefatura entre PTS y PO —como rota las bancas—, una fila única desde 2014 no
es imprecisa, es incorrecta. **Confirmado (14-09): el FIT en Diputados NO es un bloque, es
un INTERBLOQUE de DOS bancadas propias** — Partido Obrero (preside Romina Del Plá) y PTS
(preside, con rotación, Myriam Bregman desde el recambio del 10-dic-2025). Dos fuentes
independientes: La Nueva 03-12-2025 ("el nuevo mapa del poder legislativo") y
`jefes_bloque_oficial.csv` (scraper oficial, snapshot 2026-07-30, ALTA), que ya marca a
Del Plá y Bregman como presidentas — no a Del Caño.

Se acotó el `hasta` de DEL CAÑO a `2025-12-09`: hay evidencia POSITIVA de que desde el
recambio no preside. **Para 2014-2025 sigue una sola fila** (confianza MEDIA, sin
cambios): la rotación parece haber sido práctica constante también en ese período, pero
no encontré fuente con fechas de esos tramos. Si aparece una, es una línea en el CSV.

> **La regla que deja el trabajo:** las dos filas que estaban mal (Losada, Fernández
> Sagasti) tenían la misma forma — confundir un cargo del cuerpo o el liderazgo de un
> espacio con la **presidencia del bloque parlamentario**, que es lo único que mide esta
> tabla. Cuando una fuente dice "referente", "conduce" o "lidera" en vez de "preside el
> bloque", la fila NO está validada. Del Caño agrega una tercera forma: un bloque que en
> realidad son dos, con presidencias separadas y rotativas.

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
