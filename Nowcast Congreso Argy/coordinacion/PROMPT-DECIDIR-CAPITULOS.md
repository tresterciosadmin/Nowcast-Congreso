# Prompt para Claude Code — la sesión que DECIDE si capítulos vive o muere

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

## Qué es esta sesión, y qué NO es

Esta sesión **decide**. La línea de trabajo de capítulos lleva varias sesiones y **tres
intentos de validación que terminaron los tres en "no alcanza para concluir"** (ADR-0029 y
sus cuatro addenda). Franco fue explícito:

> *"Si vale la pena, se arma, se prende y lo cerramos. Si no, pasamos al Senado y lo
> mejoramos con lo que falte."*

**Tenés que terminar con un veredicto, no con un cuarto "es interesante pero".** Por eso los
criterios de decisión están escritos ABAJO, con números, **antes** de medir. Si el resultado
no llega al umbral, el veredicto es *no* — y es un resultado perfectamente bueno.

## 🔴 Dos reglas duras

1. **CERO gasto de API.** Ninguna llamada al agente clasificador. Todo lo que hace falta ya
   está clasificado (Ley Bases: 63/63 capítulos, 100%). Si te parece que necesitás
   clasificar algo, **estimá con lo que hay y declará el supuesto**.
2. **No toques el motor** hasta tener el veredicto. Si el veredicto es *sí*, ahí sí se
   arma y se prende, con backtest y ADR (Franco ya delegó ese criterio).

## Antes de nada

Leé, en este orden: `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`) →
`CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` → ADRs **0026** (récord por tema, el
mecanismo validado del que todo esto cuelga), **0027** (composición por capítulos) y
**0029 con sus cuatro addenda** (lo que ya se intentó y por qué falló — **no lo repitas**).

---

# PRUEBA 1 — Los pivotes por capítulo (la que responde la pregunta de Franco)

## La idea, y por qué no hereda el problema de validación

Las tres validaciones anteriores intentaron probar que **$P_k$ (la probabilidad del
capítulo) está calibrada**. Eso choca contra un techo estructural: sólo Ley Bases tiene
resultado real a nivel capítulo, así que $n=3$.

**Pero los pivotes son otra pregunta y tienen otra vara.** La lista de pivotes sale de
$P_i$ —quién queda cerca de 50/50— y **$P_i$ condicionada por tema SÍ está validada**: es
el mecanismo del ADR-0026 (−11,06% de Brier, positivo en todos los cortes, en producción).
Lo no validado es la **composición** a $P_k$, que la lista de pivotes **no usa**.

O sea: *"el diputado X es bisagra en el capítulo laboral pero no en el energético"* se
apoya en maquinaria validada. *"El capítulo laboral tiene P=0,62"* no. **Son dos productos
distintos y se venían tratando como uno.**

## Qué construir

Sobre **Ley Bases (`HCDN272347`)**, con el roster real de Diputados walk-forward a
2024-02-01 (la misma función que usa `nowcast_puertas.nowcast()` en producción — no
reimplementes el roster):

- **Lista A (la de hoy):** $P_i$ con las áreas del proyecto entero, pivotes = quienes caen
  en $[0{,}35;\,0{,}65]$, ordenados por cercanía a 0,50.
- **Lista B (por capítulo):** para cada uno de los 63 capítulos, $P_i$ condicionada al área
  **de ese capítulo** (`tema_por_capitulo.parquet`, clave
  `(proyecto_id, titulo_num, capitulo_num)` — **nunca `capitulo_num` solo**, ese bug ya
  apareció dos veces), y su lista de pivotes.

## Las tres mediciones, en orden de poder de veto

### 1.1 🔴 ¿La heterogeneidad es REAL o es fallback? (esta manda)

**Corré esta primera. Si falla, las otras dos no importan.**

Para cada $P_i$ por capítulo, registrá **si realmente usó datos condicionados por área o si
cayó al récord general** por celda vacía. El encogimiento Empirical-Bayes degrada suave, así
que un capítulo con poca muestra devuelve algo **parecido al récord general sin avisar** —
y entonces las "diferencias entre capítulos" serían un artefacto del ruido, no señal.

Reportá: **qué fracción de los $P_i$ por capítulo tuvo $n_i^{\text{área}} \geq 1$ real**, y
la distribución de $n_i^{\text{área}}$.

> Es exactamente el mismo modo de falla que ya nos mordió: el capítulo AUX de Ley Bases cayó
> a incondicional **sin reportar error** y su $P_k$ salió idéntico al de otro capítulo. Un
> mecanismo que degrada en silencio parece andar cuando no está usando nada.

### 1.2 ¿Las listas son distintas?

- Jaccard entre la lista A y la unión de las listas B.
- **Cuántos legisladores son pivote en algunos capítulos y no en otros** — esa es la
  información nueva que justificaría todo.
- ¿Hay capítulos con pivotes propios que la lista única no marca?

### 1.3 ¿Le acierta a algo?

El $n=3$ de la ronda 1 ya se sabe que no alcanza. **Probá primero un target mejor, que
nadie propuso:**

> **¿El modelo señala los capítulos que efectivamente se CAYERON del proyecto?** Ley Bases
> volvió en abril de 2024 recortada —perdió cerca de dos tercios del articulado—. "Este
> capítulo fue eliminado entre la ronda 1 y la ronda 2" es un resultado **mucho más
> abundante** que "este capítulo se votó y perdió", y **es literalmente lo que el producto
> promete predecir: dónde se va a recortar la ley.**

**Verificá primero si el dato existe** (¿hay OD o texto de las dos rondas para comparar qué
capítulos sobrevivieron?). Si existe, es la validación de esta prueba. Si no existe, decilo
y caé al $n=3$ sabiendo que no concluye.

## ✅ Criterio de decisión de la PRUEBA 1, escrito antes de medir

**Pasa si se cumplen las dos primeras:**

| | umbral |
|---|---|
| **1.1 heterogeneidad real** | **≥ 50%** de los $P_i$ por capítulo usan datos condicionados reales, no fallback |
| **1.2 listas distintas** | **≥ 30%** de los pivotes son específicos de capítulo (no están en la lista única, o son pivote en unos capítulos y no en otros) |
| 1.3 acierto | suma evidencia, **no es condición** — con este $n$ no puede serlo |

**Si 1.1 da < 50%, la prueba FALLA y no hace falta seguir**: las diferencias entre
capítulos serían ruido de fallback disfrazado de señal política.

---

# PRUEBA 2 — Reconstrucción por rango de artículos (gratis, un intento)

ADR-0029 la lista como camino abierto y **nadie la exploró**. Es lo único que podría romper
el techo de $n$.

Las actas de votación en particular declaran rangos (`"ARTS. 208 AL 214"`); el PDF de la
Orden del Día tiene los artículos de cada capítulo. Cruzarlos daría resultado real por
capítulo **sin depender de que el acta declare el capítulo**.

1. ¿Cuántas actas de votación en particular traen rango parseable?
   (`votacion_por_articulo.py::extraer_titulo_capitulo` ya parsea parte — mirá qué descarta).
2. ¿El PDF de la OD permite mapear capítulo → rango de artículos? Usá el **caché local de
   PDFs**, que es gratis.
3. Cruzalos.

## ✅ Criterio de decisión de la PRUEBA 2

| resultado | veredicto |
|---|---|
| **≥ 5 proyectos** pasan a tener resultado por capítulo | **pasa** — hay con qué validar $P_k$ de verdad, se rehace la validación |
| 2-4 proyectos | parcial: reportá y dejá dicho si vale una segunda vuelta |
| **1 proyecto** (o sea, sigue sólo Ley Bases) | **falla — el techo es estructural y se declara así** |

---

# PRUEBA 3 — ¿Vale la pena ampliar la cobertura de temas?

**Esta no se decide con Brier, y es importante que no lo intentes.** La tarea pausada
(`clasificar --desde-fecha 2025-01-01`, 9.582 proyectos) es sobre **proyectos que todavía
no se votaron**: no aportan ni un voto al histórico, así que **no pueden mover ninguna
métrica de backtest**. Medirla con Brier daría un número que parece riguroso y es la cosa
equivocada.

La pregunta correcta es de producto: **de los proyectos que alguien querría nowcastear hoy,
¿cuántos no tienen tema?**

Medí:

1. **Cobertura sobre el universo vivo:** de los proyectos con movimiento reciente (usá
   `expedientes_movimientos` o `fecha_ingreso`; el campo `estado` está enteramente NULL y no
   sirve de filtro), ¿qué fracción tiene tema?
2. **El descuento AUX:** de lo ya clasificado, ¿qué fracción salió `AUX.*`? Los AUX no
   condicionan nada — esa fracción del gasto **compra cero**. Es estimable hoy.
3. **Separá el universo votado del no votado** y reportá los dos tamaños. Del lado votado sí
   se puede dar una **cota superior** de mejora de Brier — presentala **como cota**, con el
   supuesto explícito de que los votos nuevos ganarían lo mismo que los actuales.
4. **El costo:** contá los llamados y medí los tokens sobre los prompts reales de
   `agente_taxonomias.py`. Si no podés verificar el precio vigente, **dejá la cuenta
   parametrizada** — un número inventado es peor que una fórmula.

## ✅ Criterio de decisión de la PRUEBA 3

| resultado | veredicto |
|---|---|
| **≥ 40%** de los proyectos del universo vivo no tienen tema | **conviene ampliar** — se compra capacidad de responder, no precisión |
| 15-40% | zona gris: reportá el costo y que decida Franco |
| **< 15%** | **no conviene** — la cobertura ya alcanza para el caso de uso real |

---

# El veredicto

Al final, escribí el veredicto de las tres pruebas contra sus umbrales, **sin suavizarlo**.

**Si la PRUEBA 1 pasa:** armá los pivotes por capítulo como salida real, prendelos con su
bandera, backtest y ADR — Franco ya delegó ese criterio ("si el censo mejora y queda
documentado"). Ojo: acá el criterio no es el Brier del censo (los pivotes no son una
predicción de voto) sino **que no degrade nada de lo que ya corre**. Verificá eso.

**Si la PRUEBA 1 falla:** escribí el **ADR de cierre** de la línea de capítulos. Que diga
qué se construyó, qué se midió, por qué no va, y qué haría falta para reabrirla (una ley
futura bien documentada, votada por artículo en una sola ronda). `composicion_capitulos` y
`tema_por_capitulo` **quedan en el repo, construidos y apagados** — decisión explícita de
Franco: no se publica lo que no se puede respaldar, y no se tira el trabajo.

**Y en ese caso, dejá preparado el pase al Senado:** una lista corta de qué le falta,
apoyada en lo ya medido (skill 0,072 contra 0,130 de Diputados; saturación —68,8% de los
votos con desvío en el piso, 47% de $P_i$ extremas—; el valle de era propio en 2019-2023;
el estado del dictamen del Senado tras ADR-0017). **No hagas el trabajo del Senado en esta
sesión** — sólo dejá el diagnóstico ordenado para la próxima.

---

# Reglas de la casa

**La doctrina (ADR-0016):** de la parte al todo. Todo factor entra por la decisión del
legislador; la P de la cámara es la consecuencia. **Es el argumento por el que los pivotes
por capítulo son defendibles y $P_k$ no**: los pivotes viven en $P_i$, que es donde la
doctrina dice que tienen que vivir, y donde está la validación.

**ADR-0015:** todo cambio al motor se presenta en tres niveles y actualiza
`FORMULA-COMPLETA.md` en el mismo commit.

**No `git push`.** Commits locales, en español.

## Higiene, aprendida a los golpes en este proyecto

- **Un porcentaje imposible es un bug, no un fenómeno.** Cuando algo da cero, absurdo o
  sospechosamente redondo: **sospechá del cruce antes que de la hipótesis.** Las cuatro
  veces que pasó, era el cruce.
- **Cuidado con los defaults silenciosos.** El `clase="unico"` del parser del Senado, el
  AUX de los capítulos, el fallback del encogimiento. Todos convierten "no sé" en algo que
  parece un dato. **La PRUEBA 1.1 existe por esto.**
- **La clave de capítulo es `(proyecto_id, titulo_num, capitulo_num)`.** El numeral se
  reinicia en cada título. Ya rompió dos veces el 16-09.
- **Elegí bien la unidad y decí las cotas como cotas.**
- **Si el resultado contradice lo que esperábamos, decilo.** En esta sesión, *"no vale la
  pena"* es un veredicto tan bueno como el otro — y a juzgar por lo ya medido, bastante
  probable.

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — bitácora arriba de todo: qué se midió, contra
   qué umbral, y el veredicto.
2. **Un ADR**: de activación si pasa, **de cierre si no** (fijate el próximo número libre).
3. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
4. **`coordinacion/URGENTE.md`** — sacá lo que quede cerrado.
5. Reindexá: `python .mapa/indexar.py .`

# Cerrá con

| prueba | umbral | resultado | veredicto |
|---|---|---|---|

Más: **qué esperabas y salió distinto**, y —si la línea se cierra— **la lista del Senado**.

Empezá por `URGENTE.md` y la **PRUEBA 1.1**, que es la que puede matar todo lo demás en una
sola medición.
