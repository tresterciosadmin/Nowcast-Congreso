# Prompt para Claude Code — ¿el guard de era está cortando historia que sí sirve?

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

## De dónde sale esto (leelo entero antes de tocar nada)

La sesión anterior (ADR-0030) cerró la PRUEBA 1 de pivotes por capítulo con **0,0%**: de
16.254 pares (legislador, capítulo), **ninguno** usó récord individual condicionado por
tema. Todos cayeron al mismo cálculo genérico.

La causa diagnosticada: Ley Bases se votó **53 días después del recambio presidencial**, y
el **guard de era** (ADR-0018) reinicia el récord individual en cada cambio de gobierno.
Antes de esa fecha había **una sola acta clasificada** en la era nueva.

**Franco objetó, y la objeción es el motivo de esta sesión:**

> *"Hay legisladores que estaban en el Congreso cuando se votó la Ley Bases que ya habían
> tenido muchos años en el Congreso. Miguel Ángel Pichetto es uno de ellos, ese sí tiene
> historial y debería haber estado contemplado. El guard de era tiene que marcar el
> recambio legislativo y cuando hay cambio de gobierno, no devolver a cero todos los temas
> que tienen los legisladores que se quedan."*

### Por qué la objeción es fuerte (y no un caso borde)

El guard se construyó con un argumento correcto: **el significado de "votar afirmativo"
cambia con el gobierno.** Que Pichetto acompañara el 80% bajo un gobierno no predice que
acompañe al siguiente — puede predecir lo contrario. Resetear tiene sentido **para el récord
GENERAL**, que es una relación con el Ejecutivo de turno.

**Pero el récord POR TEMA es otro objeto.** *"¿Está a favor de la desregulación laboral, de
la minería, del federalismo fiscal?"* es una posición sustantiva, mucho más estable entre
gobiernos que *"¿acompaña al Ejecutivo?"*.

**La hipótesis a testear: estamos aplicando un guard diseñado para un objeto a otro objeto
donde su justificación no se sostiene.** Y como el récord individual cubre el **99,6%** de
las predicciones, si esto está mal el costo es grande — mucho más grande que el 0,36% de la
rama de bloque que motivó la discusión original.

## 🔴 Reglas duras

1. **CERO gasto de API en la FASE 1.** Todo lo que hace falta para el test central ya está
   en el repo. Si te parece que necesitás clasificar algo, **estimá con lo que hay y declará
   el supuesto**.
2. **No prendas nada hasta tener el resultado de la FASE 1.** Si la FASE 1 respalda el
   cambio, ahí sí se implementa y se prende con backtest sobre el CENSO y ADR — Franco ya
   delegó ese criterio ("si el censo completo mejora y queda documentado").

## Antes de empezar

Leé, en este orden: `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`) →
`CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` **§II.5** (el guard de era y su
validación) → ADRs **0018** (guard de era), **0026** (récord por tema) y **0030** (la sesión
que motivó esto).

---

# FASE 1 — ¿El récord por tema es estable entre eras? (gratis, y es la que decide)

## La pregunta, en su forma medible

Tomá **todos los legisladores que atraviesan un recambio de gobierno** (10-dic de 2015,
2019, 2023 — y los anteriores que haya en la canónica) y, para cada par
**(legislador, área temática)** con muestra a ambos lados, compará su tasa afirmativa
**antes** y **después** del recambio.

**Y hacé lo mismo con el récord GENERAL, como contraste.** Ese contraste es el corazón del
test: la hipótesis de Franco predice que **el temático correlaciona más que el general**. Si
los dos correlacionan igual, el guard no está discriminando mal y la objeción no se
sostiene.

| medición | qué predice la hipótesis |
|---|---|
| correlación **temática** antes/después | **alta** — la posición sustantiva persiste |
| correlación **general** antes/después | **baja** — la relación con el Ejecutivo se da vuelta |

## Cómo medirlo bien (acá se decide si el número vale algo)

- **Correlación a nivel par (legislador, área)**, no de promedios agregados. Promediar
  primero destruye justamente la variación que se quiere medir.
- **Exigí muestra mínima a ambos lados** y reportá el resultado **para varios umbrales**
  ($n \geq 3, 5, 10$), no para uno elegido a mano. Ya hicimos esto con `MIN_HIST_INDIVIDUAL`
  en §II.5: la curva dice más que el punto.
- **Encogé antes de correlacionar**, o la correlación va a estar atenuada por ruido de
  muestra chica y vas a subestimar la estabilidad. Usá el mismo Empirical-Bayes $k=5$ del
  resto del motor.
- **Cortá por recambio** (2015, 2019, 2023): puede que la estabilidad dependa de cuán
  disruptivo fue el cambio. 2023 es el caso que importa para el producto.
- **Cortá por área**: puede que algunas sean estables (minería, federalismo) y otras no
  (las que se politizan con el gobierno de turno). **Si la estabilidad es heterogénea por
  área, ése es el resultado**, y lleva a un diseño por área en vez de uno global.
- **Cortá por continuidad**: legisladores que siguieron vs. los que entraron. Sólo los
  continuadores tienen historia de ambos lados — es el universo del test.

> ⚠️ **Ojo con el sesgo de supervivencia.** Los legisladores que atraviesan varios recambios
> no son una muestra al azar: son los que se sostienen, suelen ser de bloques provinciales o
> figuras de peso propio, y **podrían ser justamente los más estables**. Medí la composición
> del universo y **decilo**, no lo extrapoles en silencio a toda la cámara.

## Los tres diseños candidatos

El test no es "guard sí / guard no". Hay tres, y la medición debería poder discriminarlos:

| | diseño |
|---|---|
| **A** | resetear a todos en cada recambio *(lo de hoy)* |
| **B** | **no resetear nunca el récord temático** (mantener el guard sólo para el general) |
| **C** | **resetear sólo a los que son nuevos**; a los continuadores conservarles la historia, quizás descontada por un factor de antigüedad |

**C es probablemente la correcta y ninguna de las dos actuales la contempla.** Es la que
recoge literalmente lo que planteó Franco: el recambio *legislativo* no es el recambio de
*gobierno*.

## ✅ Criterio de decisión, escrito antes de medir

| resultado | veredicto |
|---|---|
| correlación temática **≥ 0,50** y **al menos 0,15 por encima** de la general | **el guard corta información válida** → implementar B o C y validar en el censo |
| temática entre 0,30 y 0,50, o la brecha con la general < 0,15 | **zona gris** → reportá y proponé el diseño más conservador (C con descuento), sin prenderlo |
| correlación temática **< 0,30** | **el guard tiene razón también para el tema** → la objeción no se sostiene, se documenta y se cierra |

---

# FASE 2 — Si la FASE 1 respalda el cambio: implementar y validar

Sólo si la FASE 1 pasa. Implementá el diseño que la medición respalde (B o C), **detrás de
bandera**, y validá con `baseline_voto_individual.py` **sobre el censo completo**.

**El número a batir** es el vigente con el guard actual — **leelo de `FORMULA-COMPLETA.md`,
no de este prompt**, porque se movió varias veces (ADR-0018, ADR-0026) y una cifra vieja acá
sería peor que ninguna.

Mirá obligatoriamente:

- el **agregado** y el **subconjunto que toca** (predicciones que cambian de rama o de valor);
- **`por_era`**, sobre todo **desde 2023**, que es la era del producto y la que motivó el
  guard original;
- **`por_camara`** — el Senado tiene mandatos de 6 años y se renueva por tercios, así que la
  relación entre recambio de gobierno y recambio legislativo **es distinta ahí**. Es
  plausible que el diseño correcto no sea el mismo en las dos cámaras. **Medilo, no lo
  asumas.**

**Si el censo mejora sin cortes negativos, prendelo** (criterio ya delegado). Si mejora el
agregado pero empeora "desde 2023", **no lo prendas** y reportá — esa era es la que importa.

---

# FASE 3 — El fallback silencioso (gratis, hacelo sí o sí)

Aprobado por Franco, independiente del resultado de las otras fases.

El encogimiento hacia el récord general **degrada en silencio**: cuando la celda
(legislador, área) está vacía devuelve algo parecido al récord general **sin avisar**. Eso
hizo que un **0,0%** pasara desapercibido hasta que alguien lo midió a propósito.

**Es la cuarta vez que el mismo patrón nos cuesta una sesión:**

| default silencioso | qué produjo |
|---|---|
| `clase="unico"` en el parser del Senado | **0%** de dictámenes de mayoría, imposible |
| capítulos sustantivos clasificados `AUX` | caían a incondicional sin error |
| partir comisiones por comas | una comisión faltante el **100%** de las veces |
| encogimiento sin aviso | el **0,0%** de ADR-0030 |

**Qué hacer:** que el camino de fallback **avise** (contador agregado, no un log por fila —
mirá `_ContadorAvisos` en `baseline_voto_individual.py`, que ya resuelve exactamente esto),
y que la salida del nowcast **exponga qué fracción de las $P_i$ usó datos condicionados
reales**. Que sea observable desde afuera, no sólo desde un script de diagnóstico.

Y revisá si hay **otros** fallbacks silenciosos en el mismo camino. El patrón ya es
sistemático: buscalo, no esperes a que muerda de nuevo.

---

# FASE 4 — Lo que queda ATADO al resultado, y no se toca antes

**Ninguna de estas dos se ejecuta en esta sesión.** Quedan escritas para que Franco decida
con el resultado de la FASE 1 en la mano:

- **Ampliar cobertura de temas** (9.582 proyectos, pausada). Franco fue explícito en no
  gastar hasta saber si vale. Y hay un motivo nuevo para esperar: **si el guard está
  cortando el récord temático, parte de la cobertura ya pagada no se está usando.** Arreglar
  el guard puede subir el valor de los datos existentes — medir eso primero es más barato
  que comprar más.
- **Capítulos (ADR-0030).** Queda **suspendida detrás del guard**, no cerrada. Si el récord
  temático resulta estable y el guard se parte, Ley Bases deja de ser un caso imposible
  —los continuadores recuperan su historia— y **la prueba de pivotes se puede rehacer con
  los datos que ya existen, sin clasificar nada nuevo**. Si la FASE 1 falla, ahí sí cierra,
  y cierra bien: no por un caso mal elegido sino porque no había señal de dónde sacarla.

**Al final, decí explícitamente qué habilita y qué cierra el resultado de la FASE 1 sobre
estas dos.**

---

# Reglas de la casa

**La doctrina (ADR-0016):** de la parte al todo. El récord individual es el objeto más "de
la parte" que tiene el motor, y cubre el 99,6% de las predicciones — por eso esta pregunta
pesa más que todo lo que se discutió sobre capítulos.

**ADR-0015:** todo cambio al motor se presenta en tres niveles y actualiza
`FORMULA-COMPLETA.md` en el mismo commit.

**No `git push`.** Commits locales, en español.

## Higiene, aprendida a los golpes

- **Un porcentaje imposible es un bug, no un fenómeno.** Cuando algo da cero, absurdo o
  sospechosamente redondo: **sospechá del cruce antes que de la hipótesis.**
- **Elegí bien la unidad.** Dos mediciones correctas del mismo fenómeno dieron resultados
  opuestos según qué mantenían fijo. Acá: **el par (legislador, área), no el promedio.**
- **Los estratos se leen sobre el censo, no sobre la muestra.** Un skill de era pasó de
  −0,189 (muestra de 300) a +0,024 (censo).
- **Las cotas se dicen como cotas** y los sesgos de selección se declaran.
- **Si el resultado contradice la hipótesis, decilo.** Acá eso significa: **si el guard tiene
  razón también para el tema, decilo aunque la objeción venga de Franco.** La medición manda.

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — bitácora arriba de todo: qué se midió, contra
   qué umbral, el veredicto, y qué habilita o cierra.
2. **Un ADR** (fijate el próximo número libre): la decisión sobre el guard, y **si cambia,
   una enmienda explícita al ADR-0018**.
3. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
4. **`coordinacion/URGENTE.md`** — sacá el fallback silencioso al resolverlo.
5. Reindexá: `python .mapa/indexar.py .`
6. **Tests:** el fallback tiene que tener un test que falle si vuelve a ser silencioso. Y si
   se cambia el guard, un test del caso Pichetto — un legislador que atraviesa un recambio
   conserva (o no, según el diseño) su historia temática.

# Cerrá con

| | resultado | umbral | veredicto |
|---|---|---|---|
| correlación temática | | ≥0,50 | |
| correlación general (contraste) | | — | |
| brecha | | ≥0,15 | |

Más: **qué esperabas y salió distinto**, qué quedó prendido y detrás de qué bandera, y **qué
habilita o cierra esto sobre cobertura y capítulos**.

Empezá por `URGENTE.md` y la **FASE 1**.
