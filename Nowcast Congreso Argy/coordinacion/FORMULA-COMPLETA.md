# La fórmula completa del nowcast — desagregada

**Última actualización:** 2026-08-25 · **Regla:** ADR-0015 — quien toca el motor
actualiza este archivo en el mismo commit.

> **Qué es esto.** La fórmula del número publicado, abierta hasta la última variable,
> con qué significa cada símbolo y de qué archivo sale. Sirve para dos cosas: entender
> qué mide el sistema, y ver **dónde cae** un cambio antes de hacerlo.
>
> **Convención:** ✅ activo · ⏸️ implementado pero apagado · 🔲 propuesto, no existe.

---

## Nivel 0 — El número

$$P_{\text{aprob}} \;=\; P_{D}\;\cdot\;P_{S}$$

| símbolo | qué es |
|---|---|
| $P_{\text{aprob}}$ | probabilidad de que el proyecto sea aprobado por el Congreso |
| $P_{D}$ | probabilidad de conseguir mayoría en **Diputados** |
| $P_{S}$ | probabilidad de conseguir mayoría en el **Senado** |

Una de las dos es la cámara de **origen** y la otra la **revisora**; el orden lo
determina dónde se presentó el proyecto. El producto es probabilidad conjunta:
tienen que pasar las dos.

> ⚠️ **Supuesto activo y falso: independencia.** El producto trata a las dos cámaras
> como si no se influyeran. Un proyecto con media sanción holgada llega distinto a la
> revisora. Corrección propuesta en el Nivel 5.

**Archivo:** `modelo/ensemble/src/nowcast_puertas.py` → `p_final = b["p"] * d["p"]`

---

## Nivel 1 — Cada cámara: recuento, dictamen y guardas

$$P_{c} \;=\; \underbrace{\text{clip}\Big(\;\underbrace{\sigma\big(\text{logit}(P^{0}_{c}) + \delta_{c}\big)}_{\text{recuento condicionado}}\;,\;\varepsilon,\;1-\varepsilon\Big)}_{\text{guarda de confianza}}$$

para $c \in \{D, S\}$.

| símbolo | qué es | valor / estado |
|---|---|---|
| $P^{0}_{c}$ | probabilidad **cruda** del recuento, sin condicionar | Nivel 2 |
| $\delta_{c}$ | corrimiento por el **carácter del dictamen** en esa cámara | ⏸️ **= 0** hoy |
| $\sigma(x)$ | función logística, $1/(1+e^{-x})$ | — |
| $\text{logit}(p)$ | $\ln\!\big(p/(1-p)\big)$ | — |
| $\varepsilon$ | épsilon de incertidumbre sistémica | ✅ 0,01 |

**Por qué en logit y no multiplicando:** si $P = 0{,}9$ y se multiplica por 1,2 da
1,08, que no es una probabilidad. El logit mapea $[0,1]$ a toda la recta real, así que
sumar ahí nunca se sale del rango.

**Por qué $\delta = 0$:** los coeficientes no se pudieron estimar — la variable
dependiente está degenerada (2 RECHAZADO en 1.898 proyectos con resultado). El módulo
corre en su límite no condicionado, que está testeado como tal.

> ⚠️ **$\varepsilon$ es un recorte, no un modelo.** Tapa la sobreconcentración que
> produce suponer votos independientes. Corrección propuesta en el Nivel 5.

**Archivos:** `puerta_a.py` (`condicionar`), `puerta_d.py` (`ajuste_paso_origen`),
`ensemble.py` (`simular_con_guardas`)

---

## Nivel 2 — El recuento: Monte Carlo

$$P^{0}_{c} \;=\; \frac{1}{N}\sum_{j=1}^{N}\; \mathbb{1}\big[A_{j} \ge u_{j}\big]\;\cdot\;\mathbb{1}\big[\text{Pres}_{j} \ge q_{c}\big]$$

| símbolo | qué es | valor |
|---|---|---|
| $N$ | simulaciones | ✅ 2.000 |
| $j$ | índice de simulación | — |
| $A_{j}$ | afirmativos en la simulación $j$ | — |
| $N_{j}$ | negativos en la simulación $j$ | — |
| $E_{j}$ | **emitidos** $= A_{j} + N_{j}$ | — |
| $u_{j}$ | umbral de aprobación de esa simulación | Nivel 2b |
| $\text{Pres}_{j}$ | presentes para el quórum | ⚠️ **$= A_j + N_j$** |
| $q_{c}$ | quórum mínimo $= \lfloor M_c/2 \rfloor + 1$ | ✅ 129 / 37 |
| $M_{c}$ | miembros de la cámara | ✅ 257 / 72 |
| $\mathbb{1}[\cdot]$ | indicador: 1 si se cumple, 0 si no | — |

**Por qué Monte Carlo y no fórmula cerrada:** la pregunta no es cuántos votos se
esperan, sino **la probabilidad de cruzar un umbral**. Eso depende de la varianza, no
sólo de la media: 130 legisladores con $P_i = 0{,}99$ y 130 con $P_i = 0{,}51$
promedian parecido y se comportan al revés.

> 🔴 **Bug conocido: $\text{Pres}_j$ ignora las abstenciones.** Debería ser
> $A_j + N_j + \text{Abs}_j$ — quien se abstiene está en el recinto. Los **emitidos**
> $E_j$ sí están bien: son votos depositados.

### Nivel 2b — Los umbrales

$$u_{j} = \begin{cases}
\lfloor E_{j}/2 \rfloor + 1 & \text{simple (más de la mitad de los emitidos)}\\[2pt]
\lfloor M_{c}/2 \rfloor + 1 & \text{absoluta (sobre miembros: 129 / 37)}\\[2pt]
\lceil 2E_{j}/3 \rceil & \text{dos tercios de emitidos}\\[2pt]
\lceil 2M_{c}/3 \rceil & \text{dos tercios del cuerpo}\\[2pt]
\lceil 3E_{j}/4 \rceil & \text{tres cuartos}
\end{cases}$$

El $+1$ de la simple es el **ADR-0013**: antes era $E_j/2$ con comparación $\geq$, y
**un empate aprobaba**.

**Archivo:** `modelo/agregador_institucional/src/agregador.py`

---

## Nivel 3 — Cada legislador: de qué lado está y si aparece

En cada simulación, el legislador $i$ saca una conducta de este vector:

$$\mathbf{p}_{i} \;=\; \big[\;\underbrace{(1-d_{i})\,\pi_{i}}_{\text{AFIRMATIVO}}\;,\;\; \underbrace{d_{i}\,r\,\pi_{i}}_{\text{NEGATIVO}}\;,\;\; \underbrace{1-\pi_{i}}_{\text{NO ACOMPAÑA}}\;\big]$$

| símbolo | qué es | valor / archivo |
|---|---|---|
| $d_{i}$ | **tasa de desvío**: con qué frecuencia vota distinto de su bloque | Nivel 4b |
| $\pi_{i}$ | **presencia**: votos emitidos / votaciones posibles | `alineacion_individual` |
| $r$ | reparto del desvío entre las otras dos conductas | ✅ **1,0** |

**Por qué $r = 1$:** todo el desvío va a la conducta **opuesta**, nada a la ausencia.
El desvío es cambio de dirección; la ausencia viaja por $\pi_i$. Con el 0,5 por
defecto se inventaban ausencias en masa.

**La ausencia sí está modelada:** es $1-\pi_i$. Con $\pi_i = 1$ el tercer término es 0,
que es correcto: quien nunca falta, no falta.

**Corte:** si $\pi_i < 0{,}15$ (`PRESENCIA_MINIMA`) la persona **no se cuenta como
votante** — preside la cámara, está de licencia o no aparece.

**Archivo:** `agregador.py` (`_prob_conductas` + escalado por `p_presente`)

---

## Nivel 4 — De dónde sale la dirección

$$P_{i} \;=\; \begin{cases}
\;\text{rec}_{i} & \text{si } n_{i} \ge 8 \quad \text{(historial propio)}\\[6pt]
\;\underbrace{s_{\ell(i)}\,(1-d_{i})}_{\text{el bloque va a favor y lo sigue}} \;+\; \underbrace{(1-s_{\ell(i)})\,\tfrac{d_{i}}{2}}_{\text{el bloque va en contra y se desvía}} & \text{si no}
\end{cases}$$

| símbolo | qué es |
|---|---|
| $P_{i}$ | probabilidad de que $i$ vote afirmativo **dado que vota** |
| $\text{rec}_{i}$ | récord propio: afirmativos / emitidos, con corte walk-forward |
| $n_{i}$ | votos emitidos por $i$ antes de la fecha del nowcast |
| $s_{\ell(i)}$ | **share afirmativo del linaje** al que pertenece $i$ |
| $\ell(i)$ | linaje (familia política) de $i$ |

**Por qué la composición.** Son dos incertidumbres distintas: *qué vota el bloque* y
*si esta persona lo sigue*. Antes se hacía `línea = AFIRMATIVO si s ≥ 0,5` y después
`P = 1 − d`, lo que reemplazaba la primera por la segunda. Con eso la Coalición Cívica
—que acompaña el 60,9% de las veces— salía con $P = 0{,}967$, y Peronismo Federal con
desvío 0 salía **1,000 exacto**. Era la razón de que todo diera 99%.

**El $d_i/2$** es porque quien se desvía de un bloque que va en contra puede irse a
favor **o** abstenerse: la mitad de su desvío apunta al sí.

**El walk-forward** del récord: sin el corte por fecha, un nowcast fechado 2024-06-01
usaba el 85% de sus votos de **después** de esa fecha.

### Nivel 4a — El share del bloque, condicionado y encogido

$$s_{\ell} \;=\; \frac{n^{c}_{\ell}\, s^{c}_{\ell} \;+\; k\, s^{u}_{\ell}}{n^{c}_{\ell} + k}$$

| símbolo | qué es | valor |
|---|---|---|
| $s^{c}_{\ell}$ | share **condicionado** al tema y origen del proyecto | — |
| $n^{c}_{\ell}$ | actas de la ventana que comparten ese tema/origen | — |
| $s^{u}_{\ell}$ | share **incondicional** (todas las actas de la ventana) | — |
| $k$ | pseudo-conteo del encogimiento | ✅ 5,0 |
| ventana | historia anterior a la fecha | ✅ 730 días |

Con pocas actas condicionadas manda el incondicional; con muchas, el condicionado.
**Sin historia:** $s = 0{,}5$ y $d = 0{,}15$ — neutro explícito, no cero.

Las actas `AUX` (homenajes, trámite, tratados por consenso) se **excluyen**: todos
votan que sí y inflarían el share.

**Archivo:** `variables/bloque/src/bloque.py` → `proyectar_postura`

### Nivel 4b — El desvío, encogido y con piso

$$d_{i} \;=\; \max\!\left(\;\underbrace{\frac{n^{\text{disp}}_{i}\, d^{\text{obs}}_{i} + k\, \bar{d}_{\ell(i)}}{n^{\text{disp}}_{i} + k}}_{\text{encogido hacia su bloque}}\;,\;\; d_{\min}\right)$$

| símbolo | qué es | valor |
|---|---|---|
| $d^{\text{obs}}_{i}$ | desvío observado en votaciones **disputadas** | — |
| $n^{\text{disp}}_{i}$ | cuántas disputadas respaldan esa medición | — |
| $\bar{d}_{\ell(i)}$ | mediana del desvío de su bloque, **sólo entre los de muestra sólida** ($\ge 10$) | — |
| $k$ | pseudo-conteo | ✅ 5,0 |
| $d_{\min}$ | piso de desvío | ✅ 0,02 |

**Por qué el encogimiento:** los 104 diputados que asumieron en dic-2025 tenían
**mediana de 2 votaciones disputadas** contra 47 de los veteranos. Con 2 observaciones
el desvío sólo puede valer 0 / 0,5 / 1, y los tramos cortan en 0,10 / 0,20 / 0,30 —
imposible caer en los intermedios. 96 quedaban en el piso y 6 en el tramo máximo de la
cámara, con dos datos.

**Por qué el prior sale sólo de los sólidos:** con la mediana del bloque entero, los
novatos se encogían hacia el ruido de sus propios pares y el ajuste no hacía nada.

**Por qué piso y no techo:** un cero medido sobre historia finita no es un cero real.
Del otro lado, ningún legislador llega a 1,0 (máximo observado 0,944); un desvío casi
total sería señal de bloque mal asignado, no de indisciplina.

**Archivo:** `variables/proyecto/src/modulador_icg.py` → `encoger_desvio`

---

## Nivel 5 — El clima político (ICG) ⏸️

**Estado: medido, significativo y NO conectado al motor.** `nowcast_puertas.py` no lo
importa. Sólo lo usa `casos/proyeccion_hipotetica_bicameral.py`, que calcula el número
con y sin ICG para **comparar**.

Cuando se aplica, corrige a cada legislador **antes** del recuento:

$$\text{logit}(P^{\text{mod}}_{i}) \;=\; \text{logit}(P_{i}) \;+\; \underbrace{\gamma^{f}(d_{i})\;\varsigma\; z_{f}}_{\text{fondo, 6 meses}} \;+\; \underbrace{\gamma^{c}(d_{i})\;\varsigma\; z_{c}}_{\text{corto, 3 meses} \;⏸️}$$

| símbolo | qué es | valor |
|---|---|---|
| $\varsigma$ | signo político del proyecto: $+1$ gobierno, $-1$ oposición, $0$ consenso | ✅ |
| $z_{f}$ | desvío de **fondo** del clima | abajo |
| $z_{c}$ | **sacudón** de corto plazo | ⏸️ apagado |
| $\gamma^{f}, \gamma^{c}$ | elasticidad al clima, por tramo de desvío | tabla abajo |

**El signo $\varsigma$ es la pieza elegante:** el mismo clima que ayuda a un proyecto
del gobierno perjudica a uno de la oposición, y eso sale del signo del exponente, sin
ninguna rama condicional.

### Los dos horizontes

$$z_{f} = \ln\!\frac{\text{MM}_{6}(\text{ICG})}{\overline{\text{ICG}}_{\text{gob}}} \qquad\qquad z_{c} = \ln\!\frac{\text{MM}_{3}(\text{ICG})}{\text{MM}_{6}(\text{ICG})}$$

| símbolo | qué es | valor |
|---|---|---|
| $\text{MM}_{6}, \text{MM}_{3}$ | medias móviles **trailing**, dentro de cada gobierno | ✅ 6 y 3 meses |
| $\overline{\text{ICG}}_{\text{gob}}$ | promedio del gobierno, **expanding + shift(1)** | ✅ sin leakage |
| piso / techo | recorte del ICG | ✅ 1,0 / 4,0 |

**El neutro es el promedio del propio gobierno**, no un valor absoluto: así un
gobierno estructuralmente bajo no queda penalizado para siempre. Y es *point-in-time*
—sólo meses anteriores, sin incluir el corriente— para no mirar el futuro.

> ⚠️ **El logaritmo es simétrico y la política no.** $\ln(1{,}1) = -\ln(1/1{,}1)$:
> subir 10% y bajar 10% dan el mismo corrimiento con signo opuesto. La asimetría
> existía en el mecanismo 2 del ADR-0008 y **se perdió al eliminarlo el 11-08**.
> Corrección propuesta abajo.

### Elasticidad por tramo (corrida oficial, con bootstrap)

| tramo de desvío | legisladores | $\gamma^{f}$ | IC 95% | $\gamma^{c}$ | signif. |
|---|---:|---:|---|---:|---|
| < 0,10 (núcleo duro) | 1.356 | −0,076 | [−0,40; 0,16] | −0,155 | no |
| ≥ 0,10 | 305 | **1,012** | [0,62; 1,46] | 0,041 | no |
| ≥ 0,20 | 132 | **1,147** | [0,70; 1,61] | −0,004 | no |
| ≥ 0,30 | 62 | **0,925** | [0,29; 1,57] | −0,759 | no |

**La capa corta está apagada** (`USAR_CORTO = False`): ningún tramo se distingue de
cero. Con el corto apagado, el modelo es un único suavizado de 6 meses.

**Lo que dice esta tabla:** el clima **no mueve a la cámara, mueve a los
negociadores**. El núcleo duro no reacciona (y su coeficiente ni siquiera es
significativo).

**Archivos:** `variables/proyecto/src/{icg_contexto,modulador_icg}.py`

---

## Términos propuestos, no implementados 🔲

### 5a. Dependencia entre cámaras

$$\text{logit}(P_{S}) \;=\; \text{logit}(P^{0}_{S}) + \delta_{S} + \underbrace{\psi\left(\frac{A_{D}}{E_{D}} - \tfrac{1}{2}\right)}_{\text{arrastre del margen de origen}}$$

$\psi > 0$: una media sanción holgada facilita la revisora. Estimable sobre los 1.166
proyectos de `cadena_camaras.parquet` con votación en las dos cámaras.

### 5b. Shock común (reemplaza al $\varepsilon$)

$$P^{(j)}_{i} \;=\; \sigma\big(\text{logit}(P_{i}) + \tau\,\eta_{j}\big), \qquad \eta_{j}\sim\mathcal{N}(0,1)$$

$\eta_j$ es **compartido por todos los legisladores dentro de la simulación $j$**: en
algunas corridas todos se corren juntos. Eso produce las colas gordas que el supuesto
de independencia no puede generar, y hace innecesario el clip.

### 5c. Condicionante del dictamen

$$\delta_{c} \;=\; \beta_{1}\,\rho_{c} \;+\; \beta_{2}\,W_{c}$$

$$\rho_{c} = \frac{k_{\text{com}}}{m_{\text{com}}} \qquad\qquad W_{c} = \sum_{\ell \in L}\; w_{\ell}\,\frac{b_{\ell}}{M_{c}}$$

| símbolo | qué es |
|---|---|
| $\rho_c$ | **cobertura**: comisiones con dictamen de mayoría sobre comisiones giradas |
| $k_{\text{com}}, m_{\text{com}}$ | con dictamen / giradas. **Plenario de comisiones ⇒ $k = m$** |
| $W_c$ | **anchura** de la coalición firmante, ponderada |
| $L$ | linajes que firmaron el dictamen |
| $b_\ell$ | bancas del linaje $\ell$ |
| $w_\ell$ | peso del firmante: $1 + \omega_1\mathbb{1}[\text{jefe de bloque}] + \omega_2\mathbb{1}[\text{pdte. comisión}]$ |

**Se descartan** disidencias parciales, totales y dictámenes de minoría: sin
relevancia en la praxis legislativa, y sin datos para estimarlas.

**La vara pasa a ser el margen $A/E$** sobre 1.849 actas enganchadas a su expediente,
en vez de `aprobado/rechazado`, que está degenerada.

### 5d. Vía sobre tablas

$$P_{\text{aprob}} \;=\; \big[1 - \Lambda\big]\,\cdot\, P_{D}P_{S} \;+\; \Lambda \,\cdot\, P^{\text{tablas}}$$

$\Lambda$ = probabilidad de que el proyecto entre por sobre tablas (umbral de 2/3 para
incorporarlo al temario). **Medido: 221 proyectos con sobre tablas afirmativa, 118
sancionados (53%) contra 1,9% general — y 98 de las 784 leyes (12,5%) no tienen
dictamen registrado.** La forma exacta requiere ADR.

### 5e. Proximidad electoral

$$\pi'_{i} = \pi_{i}\,e^{-\theta/T} \qquad\qquad \text{logit}(P'_{i}) = \text{logit}(P_{i}) - \phi\,\tfrac{1}{T}\,\mathbb{1}[\text{costoso}]$$

$T$ = días a la elección. Dos efectos: baja la asistencia y sube el costo de acompañar
lo impopular. **Backtest de significancia primero.**

### 5f. Asimetría del ICG (para discutir, no aplicar)

$$z^{*} = \text{sgn}(z)\,|z|^{\alpha}\big(1 + (\kappa-1)\mathbb{1}[z<0]\big)\cdot\big(1 + \lambda(\text{ICG}_{\text{ref}} - \text{ICG}_{0})\big)$$

$\alpha$ = aceleración, $\kappa$ = cuánto más pesa la caída, $\lambda$ = amplificación
en niveles bajos. **Estos parámetros se acuerdan, no se estiman** — igual que el
break-even del ADR-0008.

---

## Mapa de qué afecta a qué

```
ICG ──⏸️──► P_i ──► p_i ──► A_j ──► P⁰_c ──► P_c ──► P_aprob
             ▲       ▲       ▲        ▲        ▲
   share s ──┤       │       │        │        │
   récord ───┤    π_i┘   u_j─┘   δ_c ─┘   ε ───┘
   desvío d ─┘                (dictamen)  (clip)
```

**Lo que mueve el número hoy:** $s$, $d$, $\pi$, el umbral y el padrón.
**Lo que está construido y apagado:** ICG, $\delta$ del dictamen, arrastre entre cámaras.
**Lo que no existe:** sobre tablas, proximidad electoral, shock común.

---

## Constantes del motor

| constante | valor | dónde | qué hace |
|---|---:|---|---|
| `N` (simulaciones) | 2.000 | `nowcast_puertas` | corridas de Monte Carlo |
| `DESVIO_MIN_INDIVIDUAL` | 0,02 | `ensemble` | piso de desvío |
| `P_INCERTIDUMBRE` | 0,01 | `ensemble` | el $\varepsilon$ del clip |
| `REPARTO_DESVIO` | 1,0 | `nowcast_puertas` | todo el desvío a la conducta opuesta |
| `MIN_HIST_INDIVIDUAL` | 8 | `nowcast_puertas` | votos para creerle al récord propio |
| `PRESENCIA_MINIMA` | 0,15 | `nowcast_puertas` | debajo de esto no se cuenta como votante |
| `DESVIO_BISAGRA` | 0,20 | `nowcast_puertas` | umbral de bisagra |
| `INCERTIDUMBRE_INCOGNITA` | 0,35 | `nowcast_puertas` | $P\in[0{,}35;0{,}65]$ ⇒ incógnita |
| `k_shrink` | 5,0 | `bloque` y `modulador_icg` | pseudo-conteo del encogimiento |
| `MIN_DISPUTADAS` | 10 | `modulador_icg` | muestra sólida para el prior |
| `ventana_dias` | 730 | `bloque` | historia para la postura |
| `MA_MED` / `MA_CORTO` | 6 / 3 | `icg_contexto` | medias móviles del ICG |
| `PISO` / `TECHO` | 1,0 / 4,0 | `icg_contexto` | recorte del ICG |
| `USAR_CORTO` | `False` | `modulador_icg` | capa corta apagada |
| `BANCAS` | 257 / 72 | `definiciones.py` | miembros por cámara |
