# Revisión metodológica del motor — 2026-08-25

**Quiénes:** Franco (revisión y objeciones) · Claude (verificación contra el código)
**Alcance:** la formulación por puertas (ADR-0012), el recuento del agregador, el
modulador del ICG y el condicionante del dictamen (Puerta A).
**Estado:** ninguna de estas conclusiones está implementada. Es el registro de la
discusión y el punto de partida para decidir qué se cambia.

> **Por qué existe este documento.** Franco revisó la formulación completa y planteó
> ocho objeciones. **Cuatro son correctas y obligan a cambiar el modelo**, dos eran
> errores inducidos por una explicación mía incompleta, y dos abren discusiones que
> requieren consenso del equipo. Nada de esto se ve leyendo el código: son supuestos,
> y los supuestos no se comentan solos.

---

## 1. La notación `P(B|A)` era engañosa. No hay condicional bayesiano

**Lo que se dijo mal.** Se presentó la fórmula como
`P = [A]·P(B|A)·[C]·P(D|C)`, lo que sugiere probabilidad condicional en el sentido
de Bayes: que estaríamos calculando la probabilidad de B **dado que ocurrió A**.

**Planteo de Franco.** *"La fórmula general es un doble condicional bayesiano.
Esto implica que buscamos la probabilidad de B dado que A es 1. No entiendo por qué
le damos esa fórmula a la probabilidad de aprobación."*

**Lo que hace el código.** Dos factores, no cuatro:

```python
p_final = float(b["p"] * d["p"])          # nowcast_puertas.py
```

A y C **no son factores multiplicativos ni eventos condicionantes en sentido
probabilístico**. Son un corrimiento aditivo en log-odds *dentro* de cada factor.
La escritura correcta es:

$$P = \sigma\big(\text{logit}(P_B^{0}) + \delta_A\big)\cdot\sigma\big(\text{logit}(P_D^{0}) + \delta_C\big)$$

con `σ` la función logística y `P⁰` la probabilidad sin condicionar.

**Lo que la multiplicación sí supone: INDEPENDENCIA entre cámaras.** Y ahí Franco
puso el dedo en el punto real:

> *"exactamente el punto que iba a hacer es ese: no son independientes las cámaras
> y eso hay que considerarlo matemáticamente."*

**Coincidimos: el supuesto es falso.** Un proyecto que sale de Diputados con 200
votos llega al Senado en una posición distinta que uno que salió con 130 — y el
modelo hoy los trata igual. El hook existe (`estimar_delta_paso_origen` en
`puerta_d.py`) pero está en 0, o sea "Manera 1 pura": sólo la composición de la
revisora.

**Formalización pendiente.** El paso por origen debería entrar como corrimiento en
la revisora, función del margen obtenido:

$$\text{logit}(P_D) = \text{logit}(P_D^{0}) + \delta_C + \underbrace{\psi\left(\frac{A_{\text{origen}}}{E_{\text{origen}}} - \tfrac{1}{2}\right)}_{\text{arrastre del margen de origen}}$$

`ψ > 0` significa que una media sanción holgada facilita la revisora. Es estimable
sobre los 1.166 proyectos de `cadena_camaras.parquet` que tienen las dos votaciones.

---

## 2. "Sumatoria de probabilidades" — la distinción que importa

**Planteo de Franco.** *"la probabilidad de aprobación de un proyecto es igual a la
sumatoria de probabilidades de aprobación de cada legislador."*

**Precisión.** No es sumatoria. Sumar `Σ Pᵢ` da el **número esperado de votos**;
lo que se busca es la probabilidad de **cruzar un umbral**:

$$P(\text{mayoría}) = P\left(\sum_i V_i \ \geq\ u\right), \qquad V_i \sim \text{Bernoulli}(P_i)$$

La diferencia no es formal. Dos cámaras con la misma esperanza pueden tener
probabilidades de éxito muy distintas según la varianza: 130 legisladores con
`Pᵢ = 0,99` y 130 con `Pᵢ = 0,51` promedian parecido y se comportan al revés.
Por eso Monte Carlo y no aritmética.

**Estado: aclaración aceptada, no hay cambio.**

---

## 3. `NO_ACOMPAÑA = 0` — error inducido por explicación incompleta

**Planteo de Franco.** *"No acompaña es una resta de la sumatoria de afirmativo y
negativo, la cual va a dar siempre 0 porque r es siempre 1. Esto significa que un
legislador siempre va afirmativo o va negativo, nunca modelamos la probabilidad de
que no vaya."*

**El álgebra de Franco es correcta** para el vector crudo. Con `r = 1`:

```
p = [(1-d), d, 0]
```

**Lo que faltaba en la explicación** es que el agregador aplica DESPUÉS la
presencia `π`:

```python
probs[:, 0] *= pp          # AFIRM  → (1-d)·π
probs[:, 1] *= pp          # NEG    → d·π
probs[:, 2] = 1.0 - probs[:, 0] - probs[:, 1]      # NO_ACOMPAÑA → 1-π
```

Verificado en corrida:

| d | π | AFIRM | NEG | NO ACOMPAÑA |
|---|---|---|---|---|
| 0,05 | 1,00 | 0,950 | 0,050 | 0,000 |
| 0,05 | 0,85 | 0,807 | 0,043 | **0,150** |
| 0,30 | 0,60 | 0,420 | 0,180 | **0,400** |

**La ausencia SÍ está modelada: es `1-π`.** El orden es deliberado — el desvío es
cambio de dirección, la ausencia viaja por su propio canal. `REPARTO_DESVIO = 1,0`
está puesto justamente para que el desvío no invente ausencias.

**Estado: sin cambio. Falla de documentación, no de modelo.**

---

## 4. 🔴 El quórum ignora las abstenciones — BUG CONFIRMADO

**Planteo de Franco.** *"En la simulación Monte Carlo no estamos tomando las
ausencias... si hay ausentes se pierden."*

**Precisión sobre los emitidos:** el código hace `emitidos = afirm + neg` (suma).
Que los ausentes no cuenten como emitidos es **correcto**: emitido = voto
efectivamente depositado, y los umbrales de mayoría simple se calculan sobre
emitidos.

**Pero al verificarlo apareció un error real** (`agregador.py`, línea 154):

```python
presentes = afirm + neg  # v1: no_acompaña incluye ausentes; quórum se trata laxo abajo
```

`NO_ACOMPANA` mezcla **abstenciones y ausencias**, y para el quórum se descartan
las dos. **Quien se abstiene está presente y cuenta para el quórum.** El modelo lo
trata como si se hubiera retirado del recinto.

**Corrección acordada:**

$$E = A + N \quad \text{(emitidos, sin cambio)} \qquad\qquad \text{Presentes} = A + N + \text{Abs}$$

**Sesgo:** unidireccional — subestima el quórum, y por lo tanto subestima P en
votaciones donde el quórum es el límite. Con 17.792 abstenciones históricas contra
254.370 ausencias el efecto agregado es chico, **pero el escenario donde importa es
justamente el interesante**: una votación con abstenciones tácticas masivas.

**Requisito de implementación:** hoy `NO_ACOMPANA` es una sola categoría. Separar
el quórum exige distinguir abstención de ausencia en el vector de conductas
(4 estados en vez de 3, o un canal de abstención paralelo a `p_presente`).

---

## 5. La banda y los pivotes son dos cosas distintas

**Planteo de Franco.** *"¿Cómo detectamos esos casos pivote el 'entre 118 y 126'?"*

Son objetos separados:

**La banda** es incertidumbre AGREGADA — los percentiles de la distribución
simulada:

$$\big[\,Q_5(A_j),\ Q_{95}(A_j)\,\big]$$

Se ordenan las 2.000 corridas por cantidad de afirmativos y se toman la 100ª y la
1900ª. Responde *"¿cuál es el respaldo mínimo y máximo plausible?"*.

**Los pivotes** son individuales. Se marca `incógnita` a quien cae en:

$$0{,}35 \ \leq\ P_i^{\text{efectiva}} \ \leq\ 0{,}65$$

Y desde el 22-08 la lista se **ordena por cuán cerca de 50/50 está**, no por
desvío: alguien con `P = 0,55` es incógnita aunque su bloque sea disciplinado, y
eso sólo se ve desde que el share del bloque dejó de redondearse a sí/no.

**Confirmado por Franco:** *"la banda nos sirve para entender cuánto es el mínimo y
el máximo respaldo posible al proyecto. A partir de ahí buscamos los pivotes con P
alrededor de 50."* Es exactamente el diseño.

---

## 6. La lealtad: piso sí, techo no — y por qué

**Planteo de Franco.** *"¿La lealtad partidaria nunca puede ser 0, pero sí puede ser
100? ¿Un diputado puede votar siempre con su partido, pero no puede votar siempre en
contra?"*

**Estado actual.** `d ∈ [0,1]` en teoría. Piso forzado `d ≥ 0,02`
(`DESVIO_MIN_INDIVIDUAL`), sin techo.

**Medido sobre los datos reales** (1.751 legisladores medibles, ≥50 votos):

| métrica | máximo | casos en 1,0 |
|---|---:|---:|
| `tasa_desvio` | 0,944 | 0 |
| `tasa_desvio_conducta` | 0,667 | 0 |
| `tasa_desvio_disputadas` | 0,889 | 0 |

**Ningún legislador llega a desvío 1,0.** El techo no se fuerza porque el dato nunca
lo alcanza.

**El argumento de fondo para la asimetría:** `d` se mide **contra la línea de su
propio bloque**. Un `d = 1` sostenido no sería indisciplina — sería señal de que la
persona está clasificada en el bloque equivocado, o de que la línea del bloque está
mal calculada. O sea: un techo alcanzado sería un síntoma de otro problema, no un
valor a acotar.

**Recomendación: dejar como está, pero agregar una alarma.** Si algún legislador con
muestra suficiente superara `d ≈ 0,80`, conviene que salte un aviso: es más probable
que sea un error de asignación de bloque que un díscolo real.

---

## 7. El épsilon de incertidumbre: es un recorte, no un modelo

**Planteo de Franco.** *"Ese épsilon de incertidumbre ¿cómo se modela? Dada la
fórmula que tenemos ahora nunca tenemos incertidumbre."*

**Estado actual.** `P ← clip(P, 0,01, 0,99)`. No modela nada: tapa el rango.

**La crítica es correcta en el fondo.** Con votos independientes, 257 Bernoullis con
`Pᵢ` lejos de 0,5 producen una distribución tan concentrada que `P(mayoría)` se pega
a 0 o a 1. El épsilon está tapando ese artefacto en lugar de corregir su causa.

**Lo que debería cubrir es riesgo SISTÉMICO CORRELACIONADO**, que la suma de ruidos
independientes no puede generar. Franco propuso los escenarios concretos:

1. **La oposición se levanta y vacía el quórum.**
2. **El oficialismo vuelve el proyecto a comisión** porque no reunió los votos.
3. **Tratamiento sobre tablas** — con 2/3 se incorpora al temario sin dictamen.

**Frecuencia medida** sobre 69.308 movimientos con texto:

| evento | casos |
|---|---:|
| `MANIFESTACIONES EN MINORÍA` (la sesión se cae por falta de quórum) | **468** |
| `MOCIÓN SOBRE TABLAS (afirmativa)` | **769** |
| `MOCIÓN SOBRE TABLAS (negativa)` | 226 |
| `MOCIÓN DE PREFERENCIA` | 1.710 |
| vuelta a comisión (registrada como tal) | 1 |
| retirado | 9 |

**No son casos raros.** 468 sesiones caídas por quórum sobre 6.237 actas es un 7,5%.

**Formalización propuesta — shock común:**

$$P_i^{(j)} = \sigma\big(\text{logit}(P_i) + \tau\cdot\eta_j\big), \qquad \eta_j \sim \mathcal{N}(0,1)$$

`η_j` es un shock **compartido por todos los legisladores dentro de la simulación j**
y `τ` su magnitud. Eso produce colas gordas reales: en algunas corridas todos se
corren juntos, que es lo que pasa cuando cambia la línea a último momento. `τ` se
puede calibrar contra la dispersión observada del margen `A/E`.

Con el shock común modelado, **el clip deja de hacer falta**.

### 7 bis. 🔴 HALLAZGO NUEVO: el sobre tablas no es un caso excepcional, es una vía principal

La pregunta de Franco por el tratamiento sobre tablas abrió algo que nadie había
medido. Sobre 40.752 proyectos de ley:

| | |
|---|---:|
| proyectos con `SOBRE TABLAS` afirmativa | 221 |
| **de esos, sancionados** | **118 (53%)** |
| de esos, sin dictamen previo | 107 |
| tasa de sanción general | 784 / 40.752 = **1,9%** |

**Un proyecto que consigue el sobre tablas tiene 53% de chance de ser ley, contra
1,9% general — 28 veces más.** Es el camino más exitoso del Congreso argentino.

Y el corolario que obliga a revisar el diseño:

> **98 de las 784 leyes sancionadas (12,5%) NO tienen dictamen registrado.**

La formulación por puertas asume implícitamente el camino comisión → recinto.
**Una de cada ocho leyes salta la comisión.** El sobre tablas es un mecanismo con
umbral propio (2/3 para incorporar al temario) que hoy no está modelado en ninguna
parte, ni como puerta ni como condicionante.

**Esto no es una corrección menor: es una vía de sanción faltante en el modelo.**

---

## 8. El condicionante del dictamen: reformulación completa

**Planteo de Franco.** *"¿Por qué tenemos un factor de encogimiento si estamos
mirando un valor observado? Si un proyecto no tiene dictamen no tiene dictámenes de
minoría ni disidencias, por lo que el valor observado es siempre 0. Lo que debería
interesarnos es, con el dictamen ya sancionado, cuáles fueron los valores."*

**Coincidencia total.** El diseño actual pregunta *"¿hay dictamen?"* cuando lo que
importa es *"dado que hay dictamen, ¿de qué tipo es?"*. Y los tres estados
(`con_caracter` / `sin_dictamen` / `sin_dato`) colapsan al mismo resultado
operativo (`f = 0`), así que la distinción no compra nada hoy.

**Reformulación acordada.** El condicionamiento se define **sólo sobre el subconjunto
que tiene dictamen** — porque para que haya votación en el recinto por la vía normal,
naturalmente tuvo que haber dictamen:

$$\text{logit}(P_B) = \text{logit}(P_B^{0}) + \delta, \qquad \delta \text{ definido sólo si } \mathcal{D}$$

### (a) Cobertura de comisiones

Definición precisada por Franco: si el proyecto se giró a `m` comisiones y obtuvo
dictamen de mayoría en `k`:

$$\rho = \frac{k}{m} \ \in [0,1]$$

Con tres reglas:
- girado a UNA comisión con dictamen → `ρ = 1`
- sin dictamen en ninguna → `ρ = 0` (fuera del condicionamiento)
- **dictamen de PLENARIO de comisiones → equivale a dictamen en cada una: `k = m`, `ρ = 1`**

### (b) Anchura de la coalición firmante, ponderada

$$W = \sum_{\ell \in L} w_\ell \cdot \frac{b_\ell}{B}$$

donde `L` son los linajes que firmaron el dictamen, `b_ℓ` las bancas de cada linaje,
`B` el total de la cámara, y `w_ℓ` un **peso por quién firma**:

$$w_\ell = 1 + \omega_1\mathbb{1}[\text{jefe de bloque}] + \omega_2\mathbb{1}[\text{pdte. de comisión}]$$

**Por qué el peso.** La firma de un jefe de bloque compromete a su bloque; la de un
diputado raso, no. Es el pendiente que el ADR-0012 ya había anotado, y las fuentes
existen: `jefes_bloque.csv` (roster curado 2002-2026) y
`comisiones_autoridades.parquet` (46 presidentes).

### El condicionante completo

$$\boxed{\ \delta = \beta_1\,\rho \ + \ \beta_2\,W\ }$$

### Lo que se descarta explícitamente

**Disidencias parciales, totales y dictámenes de minoría quedan afuera.** Criterio de
Franco: *"en la praxis legislativa no tienen relevancia real"*. Y el dato lo
respalda: con **2 RECHAZADO en 1.898 proyectos con resultado**, no hay con qué
estimar su efecto ni motivo para suponer que existe.

### Lo que hace estimable esto y no lo anterior

La variable dependiente deja de ser `aprobado/rechazado` —degenerada— y pasa a ser
el **margen del recuento** `A/E`, que tiene varianza real sobre las **1.849 actas
enganchadas a su expediente**. Es exactamente la vara que el ADR-0012 dejó pendiente:
resolver esto desbloquea el backtest.

---

## 9. El logaritmo del ICG es simétrico y no debería serlo

**Planteo de Franco.** *"Está mal usado el logaritmo, ya que una baja fuerte del
gobierno no es relativa a una suba fuerte. La oposición responde peor a un gobierno
débil... En la política, los movimientos negativos pesan más que los positivos."*

**El planteo es correcto.** `ln` es simétrico en cambios relativos:
`ln(1,1) = −ln(1/1,1)`. Subir 10% y bajar 10% producen corrimientos de igual
magnitud y signo opuesto.

**Y lo notable: la asimetría EXISTÍA y se perdió.** El ADR-0008 la tenía en el
mecanismo que se eliminó el 11-08:

$$z = d^{1{,}5} \ \ \text{si } d \geq 0; \qquad z = -2{,}0\,|d|^{1{,}5} \ \ \text{si } d < 0$$

Castigaba entre 1,4 y 1,8 veces más de lo que premiaba, con la justificación de
Valle: *"las personas no son sensibles a éxitos a menos que sean notables; son muy
sensibles a la pérdida"* — la función de valor de la teoría prospectiva.

**Al eliminar ese mecanismo por duplicación de señal —decisión correcta— se fue la
asimetría con él.** Lo que quedó (mecanismo 1, el medido) es simétrico.

**El segundo punto de Franco no estaba en ninguna versión:** *"si el ICG sube desde
un punto bajo no es igual a que sube desde un punto medio o fuerte"*. Eso es
dependencia del NIVEL, no sólo de la variación.

**Formalización PARA DISCUTIR (no para aplicar):**

$$z^{*} = \underbrace{\text{sgn}(z)\,|z|^{\alpha}\big(1 + (\kappa-1)\mathbb{1}[z<0]\big)}_{\text{asimetría en la variación}} \cdot \underbrace{\big(1 + \lambda\,(\text{ICG}_{\text{ref}} - \text{ICG}_0)\big)}_{\text{amplificación en niveles bajos}}$$

con `α ≈ 1,5` (aceleración), `κ ≈ 2` (la caída pesa el doble), `λ > 0` (el mismo
movimiento pesa más si el gobierno está débil), `ICG_ref` un nivel de referencia.

> **Franco (25-08):** *"Dejá formalizada la matemática pero no para aplicar sino para
> discutir. Hay más cosas que quiero ver relacionadas con la amplificación. Hay que
> definir niveles y eso requiere el consenso del equipo."*

**Los tres parámetros `α`, `κ`, `λ` y el nivel `ICG_ref` NO se estiman: se acuerdan.**
Es la misma lógica del ADR-0008 para el break-even fijo en 1,90.

---

## 10. Composición de las capas del ICG y recálculo

**Preguntas de Franco.** *"¿El z se compone de ambos z_fondo y z_corto? ¿La medida es
proporcionalmente igual? La fórmula implica que cada dato nuevo recalcula las medias
móviles y el promedio del gobierno."*

**Composición: secuencial, no proporcional.** Se aplica primero el fondo y después el
corto, cada uno con su propio `γ`. Como es aditivo en logit, equivale a:

$$\text{logit}(P') = \text{logit}(P) + \sigma\,(\gamma_f z_f + \gamma_c z_c)$$

**Pero los `γ` son muy distintos** — en el tramo ≥0,20: `γ_fondo = 1,147` y
`γ_corto = −0,004`. Y **el corto está apagado** (`USAR_CORTO = False`), así que hoy
sólo actúa el fondo.

**Recálculo: sí, y está bien hecho.** Verificado en `icg_contexto.py`:

```python
.transform(lambda s: s.shift(1).expanding(min_periods=...).mean())
```

`shift(1)` + `expanding` = sólo meses anteriores, sin incluir el mes en curso.
**Point-in-time, sin mirar el futuro.** Confirmado por Franco.

---

## 11. Proximidad electoral: no está modelada

**Planteo de Franco.** *"El factor de proximidad electoral, que entiendo no está
modelado, debería actuar como colapsador de las probabilidades de voto afirmativo a
medida que se acercan las elecciones."*

**Correcto, no está.** La única aproximación fue `anio_electoral` en el embudo, y se
midió que **no discrimina**: 3,51% de sanción en año electoral contra 3,32% en año no
electoral (0,19 puntos de diferencia).

**La hipótesis de Franco es más específica y más plausible** que esa binaria: no es
"año electoral sí/no", es **colapso progresivo** a medida que se acerca la fecha.
Formalización con dos efectos separados:

$$\pi_i' = \pi_i\,e^{-\theta/T} \qquad\qquad \text{logit}(P_i') = \text{logit}(P_i) - \phi\,\tfrac{1}{T}\,\mathbb{1}[\text{costoso}]$$

con `T` = días a la elección. El primero baja la asistencia; el segundo sube el costo
de acompañar lo impopular.

**Acordado:** primero backtest de significancia, después modelado. Testeable contra
las votaciones de septiembre-octubre de años impares.

---

# Modificaciones propuestas

Ordenadas por relación valor/costo. **Ninguna está implementada.**

| # | Cambio | Por qué | Qué hay que hacer | Bloquea a |
|---|---|---|---|---|
| **A** | **Quórum: sumar abstenciones a presentes** | Bug confirmado. Quien se abstiene está en el recinto | Separar abstención de ausencia en el vector de conductas (hoy `NO_ACOMPANA` las mezcla) y usar `A+N+Abs` para el quórum | — |
| **B** | **Condicionante del dictamen `δ = β₁ρ + β₂W`** | El actual pregunta "¿hay dictamen?" en vez de "¿de qué tipo?"; y sus coeficientes están en 0 por dependiente degenerada | Definir la vara = margen `A/E`; estimar `β₁,β₂` sobre 1.849 actas; incorporar peso del firmante desde `jefes_bloque.csv` y `comisiones_autoridades.parquet` | el backtest |
| **C** | **Modelar el sobre tablas** | 53% de sanción contra 1,9% general; **12,5% de las leyes no tienen dictamen** | Decidir si es puerta propia, condicionante o vía paralela. Requiere ADR | la cobertura del modelo |
| **D** | **Shock común en vez de clip** | El épsilon tapa un artefacto en lugar de modelar riesgo sistémico. 468 sesiones caídas por quórum | Agregar `η_j ~ N(0,1)` compartido por simulación; calibrar `τ` contra la dispersión del margen | — |
| **E** | **Dependencia entre cámaras** | La multiplicación supone independencia y es falsa | Estimar `ψ` del arrastre del margen de origen sobre 1.166 proyectos bicamerales | — |
| **F** | **Asimetría del ICG** | El log es simétrico; la política no. La asimetría existía y se perdió el 11-08 | **Discusión de equipo primero**: acordar `α`, `κ`, `λ`, `ICG_ref`. No se estiman | — |
| **G** | **Proximidad electoral** | No modelada; la binaria que se probó no discrimina | Backtest de significancia con `1/T` antes de modelar | — |
| **H** | **Alarma de desvío > 0,80** | Un desvío casi total es más probablemente un error de asignación de bloque que un díscolo real | Chequeo en `disciplina.py` | — |

## Lo que NO se cambia, y por qué

- **`NO_ACOMPAÑA` y `REPARTO_DESVIO = 1,0`** — funcionan bien: la ausencia entra por
  `π` y el desvío es sólo cambio de dirección. Era un problema de documentación.
- **Ausentes fuera de emitidos** — correcto: los umbrales se calculan sobre votos
  efectivamente depositados.
- **Piso de desvío sin techo** — el dato nunca llega a 1,0 (máximo observado 0,944);
  un techo alcanzado sería síntoma de otro problema. Se agrega alarma, no tope.
- **Monte Carlo en vez de fórmula cerrada** — la pregunta es P(cruzar umbral), que
  depende de la varianza y no sólo de la media.
- **`expanding` + `shift(1)` del ICG** — correcto, sin leakage.

## Orden sugerido

1. **A** (bug acotado, sin dependencias).
2. **B**, que arrastra la definición de la vara del backtest y desbloquea todo lo demás.
3. **C**, que probablemente sea el hallazgo de mayor impacto sobre la cobertura real
   del modelo y necesita ADR.
4. **D** y **E** en paralelo, ambos sobre el simulador.
5. **F** cuando el equipo defina niveles; **G** después del backtest de significancia.
