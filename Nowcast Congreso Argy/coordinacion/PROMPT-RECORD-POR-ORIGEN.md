# Prompt para Claude Code — el récord del legislador condicionado por ORIGEN

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

---

# El encuadre, que es lo que dirige todo lo demás

Franco fijó el norte del modelo, y todo lo que se construya tiene que encuadrar ahí:

> **Un legislador, cuando vota, mira: el tema que se trata; quién lo trajo a la mesa (si fue
> oficialismo u oposición); cómo vota su bloque; cómo él se comporta frente a su bloque; si
> el dictamen tiene a su jefe de bloque incorporado, o cuántos legisladores lo firman y
> cuántas bancas suman los bloques firmantes; y cómo está el ICG del oficialismo.**

Y el principio que ordena las decisiones:

> *"No quiero adaptar la realidad al modelo, quiero adaptar el modelo a la realidad."*

## El problema concreto

El **guard de era** (ADR-0018) reinicia el récord individual en cada cambio de gobierno. Eso
implica que un legislador con veinte años de Congreso llega a una votación con la memoria en
blanco porque cambió el presidente. **Como representación de la realidad, es falso**, y ésa
es la objeción de Franco — no una preferencia de ajuste.

Pero el guard se prendió porque **mejora**: skill 0,1304 → 0,1611 (§II.5). Y cinco
mediciones independientes confirmaron que lo que hay del otro lado del recambio no predice:

| formulación probada | resultado | ADR |
|---|---:|---|
| nivel del récord entre eras | ~0 | 0018 |
| nivel del récord **por tema** | −0,116 | 0031 |
| desvío $d_i$ propio entre eras | ~0 | 0032 |
| firma temática del desvío (centrada) | +0,015 | 0032 |
| top-2 de áreas antes → después | +0,008 | 0032 |

## 🔴 El diagnóstico que unifica los cinco fracasos

**Todas esas cantidades están medidas contra algo que se mueve en el recambio.**

- El récord, contra **el Ejecutivo de turno**.
- El desvío, contra **el bloque** (y el bloque cambia).
- El récord temático, contra **temas que se politizan según quién gobierna**.

Ninguna está anclada a algo fijo. **No es que el legislador no recuerde: es que estamos
codificando su memoria en una unidad que cambia de significado.**

## La hipótesis de esta sesión

*"Pichetto votó 80% que sí"* no significa nada cruzando un recambio. Pero:

> *"Pichetto acompaña el 80% de lo que manda el Ejecutivo y el 30% de lo que trae la
> oposición"*

**no se da vuelta con el cambio de gobierno: se relabela.** El Ejecutivo pasa a ser otro, y
de qué lado quedó el legislador es un dato de bloque que el modelo ya tiene.

**Eso es memoria anclada al ROL INSTITUCIONAL, que no se mueve.** Y sale del registro de
votos: no hay ningún rasgo asignado a mano.

El modelo ya condiciona por `origen` **a nivel bloque** (`proyectar_postura(origen=...)`,
`variables/proyecto/data/origen_por_acta.parquet`). **Lo que nunca se hizo es condicionar el
récord INDIVIDUAL por origen.** Eso es lo que hay que construir y medir.

---

# FASE 0 — Insumos y celdas (gratis, y define el alcance)

## 0.1 El estado de `origen`, que tiene una salvedad conocida

`origen_por_acta.parquet` trae categorías tipo `EJECUTIVO` / `OFICIALISMO` / `OPOSICION`.
**Está medido y documentado que `EJECUTIVO` y `OPOSICION` son confiables y que `OFICIALISMO`
NO lo es** hasta arreglar la etiqueta (buscá en `ESTADO-DEL-PROYECTO.md`: separar PRO de LLA,
deduplicar votaciones multi-artículo, validar la atribución "od"→autor).

**Entonces el eje primario de esta sesión es EJECUTIVO vs. OPOSICIÓN**, que además es el que
más importa. `OFICIALISMO` se reporta aparte y **no se usa para concluir**.

Medí y reportá: cobertura de `origen` por era y por cámara, y el reparto entre categorías.

## 0.2 Contar celdas ANTES de calcular

Para cada par **(legislador, origen)** — que son ~2 categorías útiles, no 13 áreas, así que
las celdas deberían ser **mucho más gruesas** que en los tests que fallaron:

1. ¿Cuántos legisladores tienen $n \geq 5, 10, 20$ votos con `origen` conocido **a cada lado**
   de cada recambio (2015, 2019, 2023)?
2. ¿Cuántos tienen las **dos** categorías (EJECUTIVO y OPOSICIÓN) a ambos lados? Ése es el
   universo del test principal.
3. Composición: ¿quiénes son? **Declará el sesgo de supervivencia** — los que atraviesan
   recambios son los que se sostienen, y probablemente los más estables.

**Si el universo es chico, decilo antes de calcular.** Pero acá la expectativa es distinta a
las veces anteriores: sin partir por tema, las celdas son órdenes de magnitud más grandes.

---

# FASE 1 — ¿El récord por origen atraviesa el recambio?

## El objeto

Para cada legislador $i$ y origen $o \in \{\text{EJECUTIVO}, \text{OPOSICION}\}$:

$$r_{i,o} = \frac{\text{afirmativos de } i \text{ en actas de origen } o}{\text{emitidos de } i \text{ en actas de origen } o}$$

Walk-forward, con encogimiento Empirical-Bayes ($k=5$) hacia el récord general del propio
legislador — el mismo esquema que el resto del motor.

## Las dos formas de la hipótesis, y hay que medir las dos

**Forma A — persistencia directa.** ¿$r_{i,\text{EJEC}}$ antes del recambio correlaciona con
$r_{i,\text{EJEC}}$ después? **Probablemente NO**, y eso está bien: el que acompañaba al
Ejecutivo de Alberto no acompaña al de Milei si quedó del otro lado.

**Forma B — persistencia RELABELADA, y es la hipótesis de verdad.** Lo que debería persistir
no es "acompaña al Ejecutivo" sino **"acompaña al Ejecutivo cuando el Ejecutivo es de su
espacio, y no cuando no lo es"**. O sea: hay que **alinear por la relación del legislador con
el Ejecutivo de cada período**, no por la etiqueta cruda.

Definí, para cada legislador y período, si está **del lado del Ejecutivo o no** — medido con
el dato, no asignado: por ejemplo, la tasa afirmativa de su linaje en actas de origen
EJECUTIVO en ese período (el mismo criterio que ya usa `estimar_psi_arrastre.py` para el
"lado", **reusalo, no lo reinventes**).

Entonces medí la persistencia de:

$$\rho_i \;=\; r_{i,\text{EJEC}} \;-\; r_{i,\text{OPOS}}$$

**condicionado a si el legislador cambió de lado o no.**

> **Ésta es la medición central de la sesión.** $\rho_i$ es "cuánto más acompaña a lo que
> viene del Ejecutivo que a lo que viene de la oposición". Si el legislador **no cambió de
> lado**, $\rho_i$ debería persistir con el mismo signo. Si **cambió de lado**, debería
> **invertirse de forma predecible** — y una inversión predecible es señal, no ruido: significa
> que el récord viejo sirve, sólo que hay que darlo vuelta.

**Medí las dos cosas por separado y reportalas por separado.** Una correlación cruda que
mezcla los dos grupos daría ~0 aunque los dos sean perfectamente predecibles — es exactamente
el error que arruinó mediciones anteriores.

## Cortes obligatorios

- **Por recambio** (2015, 2019, 2023). 2023 es la era del producto.
- **Por cámara.** El Senado renueva por tercios: la relación entre recambio de gobierno y
  recambio legislativo es distinta. **Medilo, no lo asumas.**
- **Por continuidad de bloque**, además de por cambio de lado. Son cosas distintas: se puede
  cambiar de bloque sin cambiar de lado y viceversa.

## 🔴 Higiene que esta vez es obligatoria

**Clusterizá por EXPEDIENTE, no por acta.** La sesión anterior (ADR-0032) midió que
**1.070 actas son sólo 310 leyes**: el n efectivo es la ley. Clusterizar por acta subestima
los errores estándar por un factor de ~1,7.

**Y verificalo acá mismo**: partí la muestra al azar por acta vs. por expediente entero. Si
las dos dan lo mismo, no hay agrupamiento; si difieren, **vale la partición por expediente**.
Ese chequeo fue el que destapó que la "firma temática" era agrupamiento por ley.

---

# FASE 2 — Si la FASE 1 respalda, integrarlo y medirlo en el motor

Sólo si la FASE 1 da señal. **Detrás de bandera, apagada por defecto.**

$$\text{logit}(P_i) \;=\; \text{logit}(P_i^{\text{base}}) \;+\; \lambda \cdot \hat{\rho}_i \cdot s_o$$

con $s_o = +1$ si el proyecto viene del Ejecutivo, $-1$ si viene de la oposición, $0$ si no
se sabe — **el mismo truco de signo que ya usa el ICG** con $\varsigma$ (§II.4), que resuelve
la simetría sin ninguna rama condicional. Reusalo, no inventes otro.

Y con **el lado del legislador en el período objetivo** aplicado al $\hat\rho_i$ heredado: si
cambió de lado, el corrimiento se invierte.

**Validá sobre el CENSO completo** con `baseline_voto_individual.py`. **El número a batir
leelo de `FORMULA-COMPLETA.md`, no de este prompt** — se movió varias veces.

Mirá obligatoriamente: el agregado, el **subconjunto que toca**, `por_era` (sobre todo
**desde 2023**), y `por_camara`.

## Y la pregunta que decide sobre el guard

**Con el récord por origen puesto, ¿el guard de era sigue aportando?**

Corré las cuatro combinaciones: {guard on, guard off} × {récord por origen on, off}. **Si el
récord por origen hace que el guard deje de aportar, ése es el resultado que buscamos**: la
historia del legislador deja de borrarse, y no porque apaguemos el guard por decreto sino
porque ya no hay nada roto que tapar.

---

# 🔴 Cómo se decide, y la instrucción de Franco sobre esto

**No hay cláusula de cierre.** Si esta formulación tampoco capta el fenómeno, el veredicto es
*"esta codificación no lo capta"*, **no** *"el fenómeno no existe"*. Los legisladores
recuerdan; lo que todavía no encontramos es cómo escribirlo.

Si da nulo, entregá las tres cosas de siempre:

1. **qué codificación queda descartada y por qué** (muestra, confundidor, unidad equivocada);
2. **la siguiente candidata**, con el razonamiento de por qué podría captar lo que ésta no;
3. **qué dato haría falta** para poder testearla.

**Y sobre el conflicto entre realidad y ajuste**, la posición acordada con Franco:

> Si el mecanismo es real y la codificación hace que el modelo prediga peor, **lo que está mal
> es la codificación, no el mecanismo**. No se prende una versión que predice peor: se busca
> la codificación donde lo real también predice mejor.
>
> **Pero si al final de un intento honesto la versión realista predice peor, eso se documenta
> como discrepancia abierta en `FORMULA-COMPLETA.md`** — no se esconde, y no se resuelve
> callando ninguno de los dos lados.

---

# Reglas de la casa

**CERO gasto de API.** Todo sale de datos que ya están.

**Leé primero:** `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`) → `CLAUDE.md` →
`coordinacion/FORMULA-COMPLETA.md` (§II.4 el signo $\varsigma$ del ICG, §II.5 el guard) →
ADRs **0016** (doctrina), **0018** (guard de era), **0026** (récord por tema), **0031** y
**0032** (los dos tests que fallaron — **no los repitas**).

**ADR-0015:** todo cambio al motor se presenta en tres niveles y actualiza
`FORMULA-COMPLETA.md` en el mismo commit.

**No `git push`.** Commits locales, en español.

## Higiene, aprendida a los golpes

- **Un porcentaje imposible es un bug, no un fenómeno.** Cuando algo da cero, absurdo o
  sospechosamente redondo: **sospechá del cruce antes que de la hipótesis.**
- **Clusterizá por expediente.** Ya está medido: el n efectivo es la ley, no el acta.
- **No promedies sobre grupos con efectos de signo opuesto.** Mezclar los que cambiaron de
  lado con los que no daría ~0 aunque ambos sean perfectamente predecibles. **Es el error que
  ya arruinó una medición.**
- **Cuidado con los defaults silenciosos** — van cuatro. Si agregás un camino de fallback,
  **que avise**, y que haya un test que falle si vuelve a ser mudo.
- **Encogé antes de correlacionar**, o el ruido de celda chica te da persistencia
  artificialmente baja.
- **Declará los sesgos de selección.** Los que atraviesan recambios no son muestra al azar.
- **Si el resultado contradice la hipótesis, decilo** — aunque venga de Franco.

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — bitácora arriba de todo: qué se midió, qué dio,
   qué queda descartado con su motivo.
2. **Un ADR** (fijate el próximo libre) con el resultado **y el registro de codificaciones
   descartadas**. Si toca el guard, **enmienda explícita al ADR-0018**.
3. **`coordinacion/FORMULA-COMPLETA.md`** — el término nuevo si entra; y en la sección de
   metodología, **la regla del expediente como unidad efectiva** (hallazgo de ADR-0032, todavía
   sin escribir ahí).
4. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
5. Reindexá: `python .mapa/indexar.py .`
6. **Tests** de lo que se construya, incluido el caso Pichetto: un legislador que atraviesa un
   recambio **sin cambiar de lado** conserva el signo de su $\rho$; uno que **cambia de lado**
   lo invierte.

# Cerrá con

| | resultado | lectura |
|---|---|---|
| celdas utilizables (FASE 0) | | |
| persistencia de $\rho_i$, **sin cambio de lado** | | la hipótesis |
| persistencia de $\rho_i$, **con cambio de lado** | | ¿se invierte predeciblemente? |
| correlación cruda (mezclando los dos) | | control — debería dar ~0 |
| censo: guard on/off × origen on/off | | ¿el guard deja de aportar? |

Más: **qué esperabas y salió distinto**, la siguiente codificación candidata si ésta falla, y
qué dato haría falta.

Empezá por `URGENTE.md` y la **FASE 0**.
