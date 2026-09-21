# Prompt para Claude Code — la firma temática del desvío: ¿dónde rompe filas cada legislador?

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

## La pregunta, y por qué NO es ninguna de las que ya se probaron

El producto tiene dos respuestas (ADR-0007): **la probabilidad y los nombres**. Esta sesión
es sobre los nombres — **los pivotes, los que negocian**.

Franco lo planteó así:

> *"Sabemos que los legisladores de Unión por la Patria van a votar a favor de su gobierno y
> en contra de Milei, pero lo que necesitamos saber son los pivote, los que negocian siempre.
> Pichetto es un caso, pueden ser los radicales, los de Provincias Unidas. Eso es lo que
> debemos saber."*

Y afinó el objeto rechazando dos formulaciones peores:

> *"Si hacemos que se mida el desvío contra el mismo bloque estamos mirando algo que ya
> medimos, que es justamente la lealtad hacia el bloque. Lo que estamos tratando de mirar acá
> es si hay **consistencia temática** en un legislador, especialmente dentro de los
> legisladores que ya son pivote."*

Y también rechazó, con razón, mantener "rasgos" asignados a mano: **todo tiene que salir del
registro de votos y ser matematizable.** Nada de etiquetar gente.

### Lo que YA se probó y falló (no lo repitas)

| intento | resultado |
|---|---|
| combinar temas a nivel BLOQUE (4 reglas, ADR-0024/0028) | nada distinguible de cero |
| **nivel** del récord temático entre eras (ADR-0031) | **−0,116**, peor que el general (−0,018) |
| pivotes por capítulo sobre Ley Bases (ADR-0030) | 0,0% — sin datos condicionados |

**Lo que SÍ funcionó y está en producción:** el récord por tema a nivel LEGISLADOR
(ADR-0026, −11,06% de Brier). Todo lo de acá cuelga de ese mecanismo validado.

---

# El objeto nuevo: la firma temática del desvío

No es *cuánto* se desvía alguien — eso es lealtad y ya está medido. Es **dónde**.

Para cada legislador $i$ y área temática $k$:

$$d_{i,k} = \text{tasa de ruptura con la línea de su bloque en actas del área } k$$

El objeto de interés es el **perfil** $(d_{i,1}, \dots, d_{i,K})$.

## 🔴 La pieza que hace que esto no sea lealtad otra vez: CENTRAR

$$\tilde{d}_{i,k} \;=\; d_{i,k} \;-\; \bar{d}_i$$

**Sin esa resta, correlacionar perfiles sólo recupera "el díscolo es díscolo en todo"** — que
es exactamente lo que ya sabemos y lo que Franco marcó que no hay que volver a medir.
Centrado por el desvío promedio **del propio legislador**, lo que queda es la pregunta
limpia: *¿rompe filas siempre en los mismos temas?*

**Esta resta es el corazón del diseño. Si se omite, el resultado es un artefacto.**

## La hipótesis

Un pivote que se desvía al azar no sirve para negociar. Uno que se desvía **predeciblemente
en energía y nunca en seguridad** es con el que se negocia. La hipótesis es que
$\tilde{d}_{i,k}$ **persiste** — a diferencia del nivel del récord, que ya se midió y no
persiste.

Ojo con la asimetría, que es justamente lo interesante: el récord dice *en qué dirección*
vota y eso se da vuelta con el gobierno; el desvío centrado dice *dónde se despega de su
bloque*, que responde a incentivos provinciales y peso propio — cosas que no cambian porque
cambie el presidente.

---

# FASE 0 — Contar celdas ANTES de calcular nada (gratis, y puede frenar todo)

**Este test necesita celdas más finas que el que falló**: legislador × área × era, y encima
restringido a **votaciones disputadas** (en las unánimes no hay desvío que medir).

**Contá primero, no calcules:**

1. ¿Cuántos pares (legislador, área) tienen $n \geq 3, 5, 10$ **actas disputadas** en cada
   lado de cada recambio? Tabla por umbral y por recambio.
2. ¿Cuántos legisladores quedan con **al menos 3 áreas** con muestra a ambos lados? Sin
   varias áreas por persona no hay perfil que correlacionar.
3. ¿Qué cobertura de tema tienen las actas disputadas? (la cobertura general está en 51-57%;
   sobre disputadas puede ser distinta).

**Si quedan menos de ~50 legisladores con perfil utilizable, reportalo y decilo claramente:
el test no tiene con qué correr.** Es el mismo muro que nos comimos con Ley Bases y hay que
verlo en los primeros diez minutos, no al final.

**Aun si no da, seguí con la FASE 2** (nivel bloque), que necesita muchas menos celdas.

---

# FASE 1 — La firma temática individual

Sobre los pares que sobrevivan la FASE 0:

1. Calculá $d_{i,k}$ por era, **walk-forward**, sólo sobre actas disputadas.
2. **Encogé** cada $d_{i,k}$ contra $\bar{d}_i$ (Empirical-Bayes, $k=5$, el mismo esquema del
   resto del motor) **antes** de centrar. Sin encoger, el ruido de celda chica atenúa la
   correlación y vas a subestimar la persistencia.
3. Centrá: $\tilde{d}_{i,k} = d_{i,k} - \bar{d}_i$.
4. **Correlacioná el perfil $\tilde{d}$ antes/después de cada recambio**, a nivel par
   (legislador, área) — **no promediando primero**, que destruiría la variación que se busca.

## Los contrastes que hacen interpretable el número

Reportá los tres juntos o el resultado no se puede leer:

| medición | qué aísla |
|---|---|
| correlación de **$d_{i,k}$ sin centrar** | contaminada por lealtad — es el control negativo |
| **correlación de $\tilde{d}_{i,k}$ centrado** | **la firma temática pura** |
| correlación del **récord** $\text{rec}_{i,k}$ (ADR-0031) | ya sabemos que da −0,116; sirve de referencia |

**Si la centrada no supera claramente a la sin centrar, no hay firma temática: hay lealtad
disfrazada.**

## Cortes obligatorios

- **Por recambio** (2015, 2019, 2023). 2023 es la era del producto.
- **Por cámara.** El Senado renueva por tercios y su desvío es la mitad (0,0080 vs 0,0131):
  puede que ahí no haya nada que medir. **Medilo, no lo asumas.**
- **Por nivel de desvío del legislador.** Franco pidió mirar *especialmente dentro de los que
  ya son pivote*: cortá por $\bar{d}_i$ (tercios o cuartiles) y reportá si la firma es más
  fuerte entre los díscolos. **Es plausible que la firma exista sólo ahí** — un legislador
  perfectamente disciplinado no tiene perfil que medir, su $\tilde{d}$ es ruido alrededor de
  cero.
- **Por continuidad de bloque:** separá a los que se quedaron en el mismo bloque de los que
  se mudaron. El desvío se mide contra el bloque; si el bloque cambió, la referencia cambió.

## Y la validación que importa de verdad

Más allá de la correlación: **¿el perfil de antes del recambio predice dónde rompió filas
después?** Tomá las 2-3 áreas de mayor $\tilde{d}_{i,k}$ de cada legislador antes del
recambio y medí si son las mismas después. Eso es el producto: *"a este tipo lo vas a
encontrar negociando en energía"*.

---

# FASE 2 — El mismo objeto a nivel BLOQUE

Franco también lo planteó a nivel bloque:

> *"o bien estén dentro de bloques con mayor propensión a negociar ciertos temas como
> Provincias Unidas, o la UCR en ciertas ocasiones."*

Un bloque no se desvía de sí mismo, así que el objeto análogo es **la cohesión interna por
área**: la dispersión de los votos de sus miembros en cada tema.

$$c_{\ell,k} = \text{dispersión intra-bloque del linaje } \ell \text{ en el área } k$$

Centrado igual, por la cohesión promedio del bloque: $\tilde{c}_{\ell,k} = c_{\ell,k} - \bar{c}_\ell$.

**Un bloque compacto en lo institucional y abierto en lo energético es negociable en energía
y no en lo otro** — y eso es un número, no una etiqueta.

**Necesita muchísimas menos celdas que la FASE 1** (hay ~10 linajes contra ~250
legisladores), así que **corré esta aunque la FASE 1 se caiga por falta de muestra.**
Controlá por tamaño de bloque: en un bloque chico la dispersión medida es alta por mecánica,
no por política.

---

# FASE 3 — Gobernadores: curar el dato, dejarlo APAGADO

**Buscado el 21-09: no hay tabla de gobernadores en el repo.** Aparece mencionado en
`PLAN-DE-TRABAJO.md` y en el caso de lobby, nunca como contrato.

Franco:

> *"Agregar un corte por provincia debería entrar en la consideración de qué bloque es el
> gobernador, si éste cambió en el recambio o si no."*

Tiene razón: **un corte por provincia sin el gobernador no significa nada.** Un diputado
salteño se comporta distinto según si su gobernador está alineado con el Ejecutivo nacional,
y en cada recambio pueden cambiar los dos, uno o ninguno. **Esas cuatro combinaciones son el
corte real**, no la provincia.

**Qué hacer:**

1. Curar `datos/padron/data/gobernadores.csv` (o donde corresponda según el mapa): provincia,
   período, gobernador, espacio político, y **si el espacio coincide con el del Ejecutivo
   nacional en ese momento**. Son **24 provincias × 4-5 períodos ≈ 100 filas**, registro
   público.
2. **Marcá la confianza de cada fila** y dejá explícito de dónde salió. Es dato curado a
   mano: si mañana alguien lo cuestiona, tiene que poder rastrearlo.
3. **NO lo enchufes a ningún consumidor.** Queda como contrato disponible, sin prender.
   Orden explícita de Franco.
4. Si la FASE 1 o la 2 dan algo, **mostrá el cruce como exploración** —¿la firma temática es
   más fuerte donde el gobernador cambió de alineación?— pero **no lo integres al motor** ni
   lo uses para justificar nada todavía.

**Es la única fase que crea datos nuevos.** No cuesta API, cuesta trabajo de curación.

---

# 🔴 Nada de esto cierra la línea

**Instrucción explícita de Franco:** esta sesión **no tiene cláusula de cierre**.

> *"No le des cierre, debemos seguir intentando encontrar la vuelta matemática para probar
> algo que pasa en la realidad."*

Si las correlaciones dan nulas, **el veredicto es "esta formulación no capta lo que pasa",
no "el fenómeno no existe"**. Los pivotes existen y se comportan así en la realidad; lo que
todavía no encontramos es la forma de medirlo.

Entonces, si da nulo:

- **decí con precisión qué formulación quedó descartada y por qué** (muestra insuficiente,
  el objeto no persiste, el centrado no separó de la lealtad, el confundidor tal);
- **proponé la siguiente formulación candidata**, con el razonamiento de por qué podría
  captar lo que ésta no capta;
- **dejá anotado qué dato haría falta** para que esa siguiente sea testeable.

El registro de formulaciones descartadas, con el motivo, **es parte del producto de esta
sesión** tanto como un resultado positivo. Que la próxima persona no repita lo mismo.

---

# Reglas de la casa

**CERO gasto de API.** Todo lo de las FASES 0-2 sale de datos que ya están. La FASE 3 es
curación manual, tampoco gasta.

**No prendas nada en el motor** sin backtest sobre el censo y ADR. Si algo de esto resulta
prometedor, implementalo **detrás de bandera apagada** y reportá — la decisión de prender es
de Franco, salvo el criterio ya delegado (censo mejora + documentado).

**Leé primero:** `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`) → `CLAUDE.md` →
`coordinacion/FORMULA-COMPLETA.md` → ADRs **0007** (las dos respuestas), **0016** (doctrina),
**0018** (guard de era), **0026** (récord por tema), **0031** (el test que falló).

**No `git push`.** Commits locales, en español.

## Higiene, aprendida a los golpes

- **Un porcentaje imposible es un bug, no un fenómeno.** Cuando algo da cero, absurdo o
  sospechosamente redondo: **sospechá del cruce antes que de la hipótesis.**
- **Cuidado con los defaults silenciosos.** Ya van cuatro (parser del Senado, AUX, comas en
  comisiones, encogimiento sin aviso). Si agregás un camino de fallback, **que avise**.
- **Elegí bien la unidad.** Dos mediciones correctas del mismo fenómeno dieron resultados
  opuestos según qué mantenían fijo. Acá: **el par (legislador, área), no el promedio.**
- **Encogé antes de correlacionar**, o el ruido de celda chica te va a dar una persistencia
  artificialmente baja y vas a concluir mal.
- **Las cotas se dicen como cotas** y los sesgos de selección se declaran. Los legisladores
  que atraviesan varios recambios **no son una muestra al azar**: son los que se sostienen, y
  probablemente los más estables. Medí la composición del universo y decilo.
- **Si el resultado contradice la hipótesis, decilo** — aunque la hipótesis venga de Franco.

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — bitácora arriba de todo: qué se midió, qué dio,
   y **qué formulación queda descartada con su motivo**.
2. **Un ADR** (fijate el próximo número libre) con el resultado **y el registro de
   formulaciones descartadas** — positivo o negativo, esto se documenta.
3. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
4. Reindexá: `python .mapa/indexar.py .`
5. **Tests** para lo que se construya, y si tocás un camino de fallback, un test que falle si
   vuelve a ser silencioso.

# Cerrá con

| | resultado | lectura |
|---|---|---|
| celdas utilizables (FASE 0) | | |
| correlación $d_{i,k}$ **sin centrar** | | control |
| correlación $\tilde{d}_{i,k}$ **centrada** | | la firma |
| ídem, sólo entre alto $\bar{d}_i$ | | los pivotes |
| cohesión de bloque por área (FASE 2) | | |

Más: **qué esperabas y salió distinto**, la **siguiente formulación candidata** con su
razonamiento, y **qué dato haría falta** para poder testearla.

Empezá por `URGENTE.md` y la **FASE 0**.
