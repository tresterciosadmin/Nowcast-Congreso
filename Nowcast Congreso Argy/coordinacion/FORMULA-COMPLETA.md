# La fórmula completa del nowcast

**Última actualización:** 2026-09-03 · **Regla:** ADR-0015 — quien toca el motor actualiza
este archivo en el mismo commit.

> **Qué es esto.** La fórmula del número publicado, abierta hasta la última variable, con
> qué significa cada símbolo, de qué archivo sale y **en qué estado está**. Sirve para dos
> cosas: entender qué mide el sistema hoy, y ver **dónde cae** un cambio antes de hacerlo.
>
> **Cómo está organizado.** Tres partes que no se mezclan:
>
> | parte | qué contiene |
> |---|---|
> | **I — LO QUE CORRE** | está implementado, encendido y produce el número publicado |
> | **II — LO QUE NO FUNCIONA** | está implementado pero apagado, o tiene un error conocido |
> | **III — LO PENDIENTE** | decidido y formulado (III.A) o propuesto sin decidir (III.B) |
>
> **Regla de oro de este archivo:** si un término no está en la Parte I, **no afecta el
> número que ve el usuario**, por más prolija que sea su fórmula. Una fórmula que miente
> es peor que no tenerla, porque se le cree.

---

# Tablero de estado

| # | término | qué hace | estado |
|---|---|---|---|
| 1 | $s_\ell$ — share del bloque | de qué lado va el bloque | ✅ **corre** |
| 2 | $d_i$ — desvío / lealtad | si la persona sigue a su bloque | ✅ **corre** |
| 3 | $\pi_i$ — presencia | si aparece a votar | ✅ **corre** |
| 4 | $\text{rec}_i$ — récord propio | historial individual ($n_i\ge1$), cortado por era y encogido hacia el bloque | ✅ **corre** — guard, encogimiento y umbral en 1, prendidos el 06-09 y confirmados con el censo: skill 0,1304 → **0,1611** (§II.5, ADR-0018) |
| 5 | umbrales y quórum | reglas del cuerpo | ✅ **corre** |
| 6 | Monte Carlo (2.000 sims) | agrega votos a probabilidad | ✅ **corre** |
| 7 | $\varepsilon$ — clip de confianza | recorta $P_c$ a $[0{,}01;0{,}99]$ | 🔴 **corre pero está mal** (§II.1) |
| 8 | $\text{Pres}_j$ — quórum | ignora las abstenciones | 🔲 **arreglado 04-09, tras bandera apagada** (§II.2); hoy Δ=0,0000 |
| 9 | $\delta$ — dictamen | condicionar por carácter del dictamen | 🔴 **implementado en 0** (§II.3) |
| 10 | ICG — clima político | modula según el humor social | 🔴 **medido y desconectado** (§II.4) |
| 11 | $\mathcal{C}_c$ — gate del dictamen | admisibilidad reglamentaria | 🔲 **decidido** (§III.A.1) |
| 12 | $\beta$ — dictamen por legislador | reemplaza a $\delta$ | 🔲 **decidido y ESTIMADO 03-09** (§III.A.2) |
| 13 | $\varepsilon_0 + \eta_j$ — incertidumbre | reemplaza al clip | 🔲 **decidido y ESTIMADO 03-09** (§III.A.3) |
| 14 | $\psi$ — arrastre entre cámaras | la revisora lee a la de origen | 🔲 **ESTIMADO y controlado 03-09** (§III.A.4) |
| 15 | sobre tablas | el 24,4% que hoy es invisible | 🔲 **decidido y $\theta$ ESTIMADO 03-09** (§III.A.5) |
| 16 | proximidad electoral | el calendario cambia incentivos | 🔲 **propuesto** (§III.B.1) |
| 17 | asimetría del ICG | las caídas pesan más que las subas | 🔲 **propuesto** (§III.B.2) |
| 18 | $\rho$ — récord por tema | falta la tabla | 🔲 **bloqueado** (§III.B.3) |

**Resumen honesto: 6 términos corren, 4 están rotos o apagados, 5 están decididos sin
implementar y 3 son propuestas.** El motor que corre hoy es más chico que esta fórmula.

---
---

# PARTE I — LO QUE HOY CORRE

Esto es el número publicado. Nada de lo que sigue en las Partes II y III lo afecta.

## I.0 — El número

$$P_{\text{aprob}} \;=\; P_{D}\;\cdot\;P_{S}$$

| símbolo | qué es |
|---|---|
| $P_{\text{aprob}}$ | probabilidad de que el Congreso apruebe el proyecto |
| $P_{D}$ | probabilidad de conseguir mayoría en **Diputados** |
| $P_{S}$ | probabilidad de conseguir mayoría en el **Senado** |

Una cámara es la de **origen** y la otra la **revisora**; el orden lo determina dónde se
presentó. El producto es probabilidad conjunta: tienen que pasar las dos.

> ⚠️ **Supuesto activo y falso: independencia.** El producto trata a las dos cámaras como
> si no se influyeran. Un proyecto con media sanción holgada llega distinto a la revisora.
> Corrección decidida en §III.A.4.

**Archivo:** `modelo/ensemble/src/nowcast_puertas.py` → `p_final = b["p"] * d["p"]`

## I.1 — Cada cámara

$$P_{c} \;=\; \text{clip}\Big(P^{0}_{c},\;\varepsilon,\;1-\varepsilon\Big), \qquad c\in\{D,S\}$$

Hoy $\delta_c = 0$ (§II.3), así que **la única operación real es el clip** — y el clip
está mal (§II.1). En la práctica: $P_c \approx P^0_c$ recortada en los bordes.

## I.2 — El recuento: Monte Carlo

$$P^{0}_{c} \;=\; \frac{1}{N}\sum_{j=1}^{N}\; \mathbb{1}\big[A_{j} \ge u_{j}\big]\;\cdot\;\mathbb{1}\big[\text{Pres}_{j} \ge q_{c}\big]$$

| símbolo | qué es | valor |
|---|---|---|
| $N$ | simulaciones | ✅ 2.000 |
| $A_{j}$ | afirmativos en la simulación $j$ | — |
| $N_{j}$ | negativos en la simulación $j$ | — |
| $E_{j}$ | **emitidos** $= A_{j} + N_{j}$ | — |
| $u_{j}$ | umbral de esa simulación | §I.2b |
| $\text{Pres}_{j}$ | presentes para el quórum | 🔲 $= A_j + N_j$ por defecto; $+\,\text{Abs}_j$ con la bandera (§II.2) |
| $q_{c}$ | quórum mínimo $=\lfloor M_c/2\rfloor+1$ | ✅ 129 / 37 |
| $M_{c}$ | miembros de la cámara | ✅ 257 / 72 |

**Por qué Monte Carlo y no fórmula cerrada:** la pregunta no es cuántos votos se esperan
sino **la probabilidad de cruzar un umbral**, y eso depende de la varianza además de la
media. 130 legisladores con $P_i=0{,}99$ y 130 con $P_i=0{,}51$ promedian parecido y se
comportan al revés.

### I.2b — Los umbrales

$$u_{j} = \begin{cases}
\lfloor E_{j}/2 \rfloor + 1 & \text{simple (más de la mitad de los emitidos)}\\[2pt]
\lfloor M_{c}/2 \rfloor + 1 & \text{absoluta (sobre miembros: 129 / 37)}\\[2pt]
\lceil 2E_{j}/3 \rceil & \text{dos tercios de emitidos}\\[2pt]
\lceil 2M_{c}/3 \rceil & \text{dos tercios del cuerpo}\\[2pt]
\lceil 3E_{j}/4 \rceil & \text{tres cuartos}
\end{cases}$$

El $+1$ de la simple es el **ADR-0013**: antes era $E_j/2$ con comparación $\ge$, y **un
empate aprobaba**.

**Archivo:** `modelo/agregador_institucional/src/agregador.py`

## I.3 — Cada legislador: conducta

En cada simulación, el legislador $i$ saca una conducta de este vector:

$$\mathbf{p}_{i} \;=\; \big[\;\underbrace{(1-d_{i})\,\pi_{i}}_{\text{AFIRMATIVO}}\;,\;\; \underbrace{d_{i}\,r\,\pi_{i}}_{\text{NEGATIVO}}\;,\;\; \underbrace{1-\pi_{i}}_{\text{NO ACOMPAÑA}}\;\big]$$

| símbolo | qué es | valor |
|---|---|---|
| $d_{i}$ | **tasa de desvío**: con qué frecuencia vota distinto de su bloque | §I.4b |
| $\pi_{i}$ | **presencia**: emitidos / votaciones posibles | `alineacion_individual` |
| $r$ | reparto del desvío | ✅ **1,0** |

**Por qué $r=1$:** todo el desvío va a la conducta **opuesta**, nada a la ausencia. El
desvío es cambio de dirección; la ausencia viaja por $\pi_i$. Con el 0,5 por defecto se
inventaban ausencias en masa.

**La ausencia sí está modelada:** es $1-\pi_i$. Con $\pi_i=1$ el tercer término da 0, que
es correcto: quien nunca falta, no falta.

**Corte:** si $\pi_i < 0{,}15$ la persona **no se cuenta como votante** — preside la
cámara, está de licencia o no aparece.

**Archivo:** `agregador.py` → `_prob_conductas` + escalado por `p_presente`

## I.4 — De dónde sale la dirección

$$P_{i} \;=\; \begin{cases}
\;\text{rec}_{i} & \text{si } n_{i} \ge 8 \quad \text{(historial propio)}\\[6pt]
\;\underbrace{s_{\ell(i)}\,(1-d_{i})}_{\text{el bloque va a favor y lo sigue}} \;+\; \underbrace{(1-s_{\ell(i)})\,\tfrac{d_{i}}{2}}_{\text{el bloque va en contra y se desvía}} & \text{si no}
\end{cases}$$

| símbolo | qué es |
|---|---|
| $P_{i}$ | probabilidad de que $i$ vote afirmativo **dado que vota** |
| $\text{rec}_{i}$ | récord propio: afirmativos / emitidos, con corte walk-forward |
| $n_{i}$ | votos emitidos por $i$ **antes** de la fecha del nowcast |
| $s_{\ell(i)}$ | share afirmativo del **linaje** de $i$ |

**Por qué la composición.** Son dos incertidumbres distintas: *qué vota el bloque* y *si
esta persona lo sigue*. Antes se hacía `línea = AFIRMATIVO si s ≥ 0,5` y después
`P = 1 − d`, lo que reemplazaba la primera por la segunda. Con eso la Coalición Cívica
—que acompaña el 60,9% de las veces— salía con $P=0{,}967$, y Peronismo Federal con desvío
0 salía **1,000 exacto**. Era la razón de que todo diera 99%.

**El $d_i/2$:** quien se desvía de un bloque que va en contra puede irse a favor **o**
abstenerse; la mitad de su desvío apunta al sí.

### I.4a — El share del bloque, condicionado y encogido

$$s_{\ell} \;=\; \frac{n^{c}_{\ell}\, s^{c}_{\ell} \;+\; k\, s^{u}_{\ell}}{n^{c}_{\ell} + k}$$

| símbolo | qué es | valor |
|---|---|---|
| $s^{c}_{\ell}$ | share **condicionado** al tema y origen del proyecto | — |
| $n^{c}_{\ell}$ | actas de la ventana con ese tema/origen | — |
| $s^{u}_{\ell}$ | share **incondicional** de la ventana | — |
| $k$ | pseudo-conteo del encogimiento | ✅ 5,0 |
| ventana | historia anterior a la fecha | ✅ 730 días |

Con pocas actas condicionadas manda el incondicional; con muchas, el condicionado.
**Sin historia:** $s=0{,}5$ y $d=0{,}15$ — neutro explícito, no cero.

Las actas `AUX` (homenajes, trámite, consenso) se **excluyen**: todos votan que sí e
inflarían el share.

**Archivo:** `variables/bloque/src/bloque.py` → `proyectar_postura`

### I.4b — El desvío, encogido y con piso

$$d_{i} \;=\; \max\!\left(\;\underbrace{\frac{n^{\text{disp}}_{i}\, d^{\text{obs}}_{i} + k\, \bar{d}_{\ell(i)}}{n^{\text{disp}}_{i} + k}}_{\text{encogido hacia su bloque}}\;,\;\; d_{\min}\right)$$

| símbolo | qué es | valor |
|---|---|---|
| $d^{\text{obs}}_{i}$ | desvío observado en votaciones **disputadas** | — |
| $n^{\text{disp}}_{i}$ | cuántas disputadas respaldan la medición | — |
| $\bar{d}_{\ell(i)}$ | mediana del bloque, **sólo entre los de muestra sólida** ($\ge10$) | — |
| $k$ | pseudo-conteo | ✅ 5,0 |
| $d_{\min}$ | piso de desvío | ✅ 0,02 |

**Por qué el encogimiento:** los 104 diputados que asumieron en dic-2025 tenían **mediana
de 2 votaciones disputadas** contra 47 de los veteranos. Con 2 observaciones el desvío
sólo puede valer 0 / 0,5 / 1, y los tramos cortan en 0,10 / 0,20 / 0,30 — imposible caer
en los intermedios. 96 quedaban en el piso y 6 en el tramo máximo, con dos datos.

**Por qué el prior sale sólo de los sólidos:** con la mediana del bloque entero los novatos
se encogían hacia el ruido de sus propios pares y el ajuste no hacía nada.

**Por qué piso y no techo:** un cero medido sobre historia finita no es un cero real. Del
otro lado, ningún legislador llega a 1,0 (máximo observado 0,944); un desvío casi total
sería señal de bloque mal asignado, no de indisciplina.

**Archivo:** `variables/proyecto/src/modulador_icg.py` → `encoger_desvio`

---
---

# PARTE II — LO QUE ESTÁ Y NO FUNCIONA

Cuatro cosas construidas que **no aportan**: dos están apagadas, dos están mal.

## II.1 🔴 El $\varepsilon$ es un recorte, no un modelo

**Qué hace hoy:** recorta $P_c$ a $[0{,}01;\,0{,}99]$ después de simular.

**Por qué está mal, en dos niveles:**

1. **Viola la doctrina** (ADR-0016): actúa sobre el agregado ya calculado. Es literalmente
   "corregir el número".
2. **Tapa un problema en vez de resolverlo.** Existe porque simular votos independientes
   sobreconcentra: 257 monedas independientes casi nunca dan resultados apretados. El clip
   esconde el síntoma.

**Efecto colateral:** un clip aplasta a todos los extremos al **mismo** valor, o sea que
**destruye el ranking de pivotes** — que es la mitad del producto (ADR-0007).

**Corrección decidida:** §III.A.3.

## II.2 🔴 El quórum ignora las abstenciones — bug confirmado

`agregador.py`, línea 154:

```python
presentes = afirm + neg   # NO_ACOMPANA mezcla abstenciones y ausencias; se descartan las dos
```

**Quien se abstiene está en el recinto y cuenta para el quórum.** El modelo lo trata como
si se hubiera retirado.

$$E = A + N \quad \text{(emitidos: bien)} \qquad\qquad \text{Presentes} = A + N + \text{Abs} \quad \text{(mal hoy)}$$

**Sesgo:** unidireccional — subestima el quórum, y con él subestima $P$ donde el quórum es
el límite. Con 17.792 abstenciones históricas contra 254.370 ausencias el efecto agregado
es chico, **pero el escenario donde importa es el interesante**: una votación con
abstenciones tácticas masivas.

**Costo de arreglarlo:** hay que partir `NO_ACOMPAÑA` en dos (abstención vs ausencia), o
sea 4 estados en vez de 3, o un canal de abstención paralelo a `p_presente`.

### ✅ IMPLEMENTADO EL 04-09-2026, DETRÁS DE BANDERA APAGADA — y hoy no mueve nada

`simular_votacion(..., quorum_cuenta_abstenciones=True)`, o `QUORUM_ABSTENCIONES=1`. El
default sigue siendo el v1, así que **el número publicado no cambió**.

Se resolvió por el canal paralelo, no por los 4 estados: en modo asistencia,
$p(\text{abstención presente}) = p_{\text{presente}} \times p(\text{NO\_ACOMPAÑA})$ —el que
está y no acompaña se abstiene; el que no está, falta— y el sorteo va con su propio
generador para que **con la bandera apagada la corrida salga bit a bit igual**. Sin modelo
de asistencia no hay ausentes que modelar, así que todo el roster cuenta como presente.

**Cuánto mueve, medido** (4.000 simulaciones por escenario, roster de 257 con 140 a favor y
117 en contra):

| escenario | sims sin quórum (v1 → arreglado) | $\Delta P$ |
|---|---|---:|
| Diputados típico ($d=0{,}05$) | 0,0% → 0,0% | **0,0000** |
| Diputados desvío alto ($d=0{,}25$) | 0,0% → 0,0% | **0,0000** |
| modo asistencia, presentismo 0,85 | 0,0% → 0,0% | **0,0000** |
| Senado típico | 0,0% → 0,0% | **0,0000** |
| modo asistencia, presentismo 0,55 | 12,5% → 5,5% | **+0,0623** |
| modo asistencia, presentismo 0,50 | 64,4% → 49,5% | **+0,1297** |

> **El bug es real y hoy es INERTE.** Con presentismo realista sobran ~120 votos sobre el
> umbral de quórum y la guarda no muerde nunca. Sólo aparece cuando la asistencia se acerca
> a la mitad del cuerpo — que es, justamente, el escenario donde el quórum es la pregunta
> interesante. **Prenderlo hoy no cambiaría ni un decimal del número publicado**; el día que
> `variables/asistencia_quorum` entregue presentismo real y bajo, pasa a valer un octavo de
> punto de probabilidad.
>
> Y una nota de calibración: la primera medición, hecha con la cota superior (contar TODO
> `NO_ACOMPAÑA` como abstención presente), daba $\Delta = +0{,}5667$ en el escenario del
> filo. Con la separación correcta da **+0,1297**. La cota superior exageraba por cuatro:
> con presentismo bajo, casi todo el `NO_ACOMPAÑA` es ausencia genuina, no abstención.

## II.3 🔴 El $\delta$ del dictamen está implementado en cero

**El hook existe** (`puerta_a.py` → `condicionar`) y está en 0. Durante semanas se creyó
que era porque la variable estaba degenerada. **Medido el 03-09, el diagnóstico era
equivocado en la mitad que importa:**

| | |
|---|---|
| variable **explicativa** (carácter del dictamen) | ✅ sana: 60,5% único, 25,3% disputado, 4,4% mayoría, 1,5% minoría |
| variable **dependiente** vieja (¿se aprobó el proyecto?) | 🔴 degenerada: **2 rechazados en 1.898** |

**El problema nunca fue el predictor: era contra qué se lo medía.** Con δ actuando sobre
$P_c$, la dependiente es "aprobado / rechazado" y no hay nada que explicar.

**Y esto es lo que la doctrina destrabó.** Bajando δ a $P_i$, la dependiente pasa a ser el
voto individual — 261.000 votos con 20% de negativos:

| carácter del dictamen | tasa afirmativa | $\Delta$ logit vs único | votos |
|---|---:|---:|---:|
| único (consenso) | **0,988** | 0,000 | 157.169 |
| sólo minoría | 0,891 | **−2,29** | 4.825 |
| disputado (mayoría + minoría) | **0,762** | **−3,23** | 78.119 |
| mayoría sin minoría | 0,710 | **−3,49** | 20.981 |

**δ es estimable y el efecto es enorme.** El ADR-0016 no ordenó la fórmula: destrabó un
parámetro clavado en cero.

> ⚠️ **Es contraste crudo, no causal.** Los proyectos con dictamen disputado *son*
> proyectos distintos —más conflictivos de entrada—, así que parte de esos −3,2 es
> selección. Hay que estimarlo con efectos fijos de legislador, bloque, tema y origen.
> **Prender δ sin controles puede empeorar la calibración sintiendo que mejora.**

## II.4 🔴 El ICG está medido, es significativo y no está conectado

`nowcast_puertas.py` **no lo importa**. Sólo lo usa
`casos/proyeccion_hipotetica_bicameral.py`, que calcula el número con y sin ICG para
comparar.

Cuando se aplique, corrige a cada legislador **antes** del recuento — o sea que ya está
escrito en el nivel correcto:

$$\text{logit}(P^{\text{mod}}_{i}) \;=\; \text{logit}(P_{i}) \;+\; \underbrace{\gamma^{f}(d_{i})\;\varsigma\; z_{f}}_{\text{fondo, 6 meses}} \;+\; \underbrace{\gamma^{c}(d_{i})\;\varsigma\; z_{c}}_{\text{corto, 3 meses} \;⏸️}$$

| símbolo | qué es |
|---|---|
| $\varsigma$ | signo político: $+1$ gobierno, $-1$ oposición, $0$ consenso |
| $z_f$ | desvío de **fondo** del clima |
| $z_c$ | **sacudón** de corto plazo (apagado) |
| $\gamma^f,\gamma^c$ | elasticidad al clima, por tramo de desvío |

**El signo $\varsigma$ es la pieza elegante:** el mismo clima que ayuda a un proyecto del
gobierno perjudica a uno de la oposición, y sale del signo del exponente, sin ninguna rama
condicional.

$$z_{f} = \ln\!\frac{\text{MM}_{6}(\text{ICG})}{\overline{\text{ICG}}_{\text{gob}}} \qquad\qquad z_{c} = \ln\!\frac{\text{MM}_{3}(\text{ICG})}{\text{MM}_{6}(\text{ICG})}$$

**El neutro es el promedio del propio gobierno**, no un valor absoluto: así un gobierno
estructuralmente bajo no queda penalizado para siempre. Es *point-in-time* (expanding +
`shift(1)`) para no mirar el futuro.

### Elasticidad por tramo (corrida oficial, con bootstrap)

| tramo de desvío | legisladores | $\gamma^{f}$ | IC 95% | $\gamma^{c}$ | signif. |
|---|---:|---:|---|---:|---|
| < 0,10 (núcleo duro) | 1.356 | −0,076 | [−0,40; 0,16] | −0,155 | no |
| ≥ 0,10 | 305 | **1,012** | [0,62; 1,46] | 0,041 | no |
| ≥ 0,20 | 132 | **1,147** | [0,70; 1,61] | −0,004 | no |
| ≥ 0,30 | 62 | **0,925** | [0,29; 1,57] | −0,759 | no |

**Lo que dice esta tabla:** el clima **no mueve a la cámara, mueve a los negociadores**. El
núcleo duro no reacciona, y su coeficiente ni siquiera es significativo.

**La capa corta está apagada** (`USAR_CORTO = False`): ningún tramo se distingue de cero.

> ⚠️ **El logaritmo es simétrico y la política no.** $\ln(1{,}1)=-\ln(1/1{,}1)$: subir 10%
> y bajar 10% dan el mismo corrimiento con signo opuesto. La asimetría vivía en el
> mecanismo 2 del ADR-0008 y **se perdió al eliminarlo el 11-08** — nadie lo notó por dos
> semanas. Es el caso que motivó el ADR-0015. Propuesta de recuperación en §III.B.2.

**Archivos:** `variables/proyecto/src/{icg_contexto,modulador_icg}.py`

---
---

## II.5 ✅ El guard de era del récord: existía con la fecha clavada, y se prendió bien

**Corregido el 06-09-2026 el diagnóstico de URGENTE 9**, que decía que el récord
individual **no** tenía guard de era. Tiene. Lo que no tiene es una fecha que se mueva.

```python
# nowcast_puertas.alineacion_individual, tal como estaba
def alineacion_individual(votos, origen_map, origen, era_desde="2023-12-10", hasta=None):
    d = votos[votos["fecha"] >= pd.Timestamp(era_desde)]
    if hasta is not None:
        d = d[d["fecha"] <= pd.Timestamp(hasta)]
```

Para cualquier nowcast del gobierno vigente eso **es** la era correcta y el término está
bien. Para cualquier fecha anterior, los dos filtros se cruzan y dejan el conjunto vacío:

| nowcast al | gobierno | legisladores con récord propio |
|---|---|---:|
| 2026-06-01 | Milei | **478** |
| 2022-06-01 | A. Fernández | **0** |
| 2018-06-01 | Macri | **0** |
| 2013-06-01 | Kirchner | **0** |

Los 478 caen enteros a la rama de bloque, que cubre el 2% de las predicciones y tiene
skill −0,059. **El motor no se puede backtestear fuera de la era vigente**: en cualquier
fecha anterior mide otra cosa. Avisaba por log; en una corrida de backtest ese log no lo
lee nadie.

### Y el harness que lo mide NO era el espejo que dice ser

`baseline_voto_individual.perfil` se documenta como *"espejo exacto de
`perfil_legislador`"*, y en el reparto de ramas lo es. En el **récord** no:

| | cómo calcula $\text{rec}_i$ |
|---|---|
| el motor | media de afirmativos sobre la **era vigente**, condicionada por origen |
| el baseline | `shift(1).expanding()` sobre **toda la historia**, sin condicionar |

Sobre los mismos 475 legisladores al 2026-06-01, la mediana de la diferencia es 0,004 —
pero la **cola** es lo que importa: **12,2% difiere en más de 0,10** y el peor caso es
**0,73** (alguien con 0,93 de afirmativos históricos que en esta era vota 0,20). Son
exactamente los que cambiaron de lado con el recambio, o sea los que deciden una votación.

**Consecuencia:** el *"skill +0,024 desde 2023"* que motivó URGENTE 9 mide un modelo que
no es el que corre. Por eso el guard entró en los dos lados.

### Lo implementado el 06-09, y PRENDIDO

**Dos cosas, las dos prendidas por defecto.**

1. **La era se deduce de la fecha del nowcast** (`GUARD_ERA=0` para volver atrás). El
   calendario ya no sale de `variables/bloque` sino de `definiciones.py` — este fue el
   cuarto consumidor y el que obligó a unificar las tres copias (ADR-0019).
2. **El récord se encoge hacia el bloque** (`SHRINK_RECORD=0` para volver atrás), en
   `perfil_legislador`, contra `share_linaje`:

$$\text{rec}_i^{\text{enc}} \;=\; \frac{n_i\,\text{rec}_i \;+\; k\,s_\ell}{n_i + k}, \qquad k = 5$$

El ancla es el **mismo objeto** que usa la rama de bloque, no otro parecido: quien tiene
9 votos en la era nueva no elige entre creerse a sí mismo o desaparecer, se apoya en su
bloque en la proporción que su historia justifica. Con 145 votos mueve 0,024; con 10,
0,24; nunca cruza al otro lado.

**EL NÚMERO PUBLICADO NO SE MOVIÓ.** Corrido el nowcast completo (Diputados, 2026-06-01,
origen EJECUTIVO, 2.000 sims, seed 0) en las tres configuraciones:

| configuración | P(aprobación) | afirmativos esperados (Dip) |
|---|---:|---:|
| como estaba | **0,9801** | 150,5 |
| guard prendido | **0,9801** | 150,5 |
| guard + encogimiento | **0,9801** | 151,2 |

Los afirmativos se mueven 0,7 votos, muy adentro de la banda 5-95 (143-158): hay ~28
votos de holgura sobre el umbral, así que la probabilidad no se entera. **Que no se mueva
no es que no haga nada** — hace mucho hacia atrás, donde se mide.

En el harness, `baseline_voto_individual.py --guard-era {off,corte,shrink}`, con `shrink`
por defecto: un espejo que mide otra cosa que el motor es el bug que abre esta sección.

**Cuánto mueve, medido** sobre los 741.275 votos emitidos de la canónica
(`evaluacion/baseline/src/medir_guard_era.py`, proxy pareado de la rama del récord):

| modo | skill global | hasta 2011 | 2011-2015 | **2015-2019** | 2019-2023 | **desde 2023** |
|---|---:|---:|---:|---:|---:|---:|
| `off` (hoy) | 0,1334 | 0,1551 | 0,2191 | **−0,010** | 0,2164 | **0,0242** |
| `corte` | 0,1643 | 0,1551 | 0,2191 | **0,0917** | 0,3828 | **0,0611** |
| **`shrink`** | **0,1680** | 0,1594 | 0,2214 | **0,0967** | **0,3876** | **0,0642** |

`corte` reinicia el récord en cada era; `shrink` es `corte` + Empirical-Bayes contra el
récord del **linaje en la misma era**, con el mismo $k=5$ del share (§IV.5) — que es lo
que pedía el ítem 9: *encoger, no cortar*.

**El criterio de aceptación se cumple y sobra:** los dos valles se cierran (2015-2019 de
−0,010 a 0,097; desde 2023 de 0,024 a 0,064) **sin hundir ninguna era vieja** — de hecho
suben todas. El Senado pasa de 0,073 a 0,115 (+58%). La rama de bloque, que era el temor,
**sube** del 2,41% al 3,14% de las predicciones —más gente deja de calificar, como el ítem 9
anticipaba— **y su propio skill sube de 0,055 a 0,102**:
la gente que deja de calificar es la que estaba usando historia de otra cámara.

### El censo confirmó el proxy (06-09, 579,9 min)

Baseline completo, 6.091 actas y 730.574 votos:

| | `off` | `shrink` |
|---|---:|---:|
| **skill** | 0,1304 | **0,1611** |
| Brier | 0,13819 | **0,13332** |
| hasta 2011 | 0,1504 | 0,1546 |
| 2011-2015 | 0,2161 | 0,2185 |
| **2015-2019** | **−0,0105** | **0,0954** |
| **2019-2023** | 0,1971 | **0,3308** |
| **desde 2023** | **0,0235** | **0,0474** |
| Diputados / Senado | 0,130 / 0,072 | **0,158 / 0,120** |
| MAE del margen | 0,1408 | 0,1390 |

El proxy había dicho 0,1306 → 0,1665; el censo dice 0,1304 → 0,1611. Misma dirección,
**ganancia real un 15% menor** — exactamente lo que hay que esperar de un proxy que aísla
la rama del récord y no compone con la postura de bloque proyectada.

**Lo único que empeora, y hay que decirlo:** el sesgo medio del margen pasa de −0,0151 a
−0,0201 y el p90 del error absoluto de 0,2500 a 0,2541. El MAE **baja** (0,1408 → 0,1390),
o sea que el error típico es menor pero un poco más sesgado hacia abajo. Es chico y va en
la dirección conservadora.

### El umbral `MIN_HIST_INDIVIDUAL` quedó sin trabajo, y encima cuesta

Ese umbral era la **única** protección contra creerle a un récord de 3 votos: binaria, o le
creías entero o lo tirabas. El encogimiento hace lo mismo de forma continua —con $n=1$ el
récord queda en $\tfrac{5}{6} s_\ell$— así que el umbral es redundante. Y medido, dañino:

| $n_i \ge$ | 1 | 3 | 5 | **8 (hoy)** | 12 | 20 | 40 |
|---|---:|---:|---:|---:|---:|---:|---:|
| skill | **0,1702** | 0,1693 | 0,1681 | **0,1665** | 0,1639 | 0,1610 | 0,1502 |
| desde 2023 | **0,0726** | 0,0693 | 0,0669 | **0,0616** | 0,0532 | 0,0418 | 0,0109 |

Monótono. Bajarlo de 8 a 1 da +0,0037 global y **+0,0110 en la era vigente**, y no movió
el número publicado (244 → 246 legisladores en la rama individual de 257; P = 0,9801 con
8, con 3 y con 1). **Bajado a 1 el 06-09 por decisión de Franco.**

Y el censo explica *por qué* el umbral costaba, mejor que el proxy: **la rama de bloque
tiene skill NEGATIVO** —−0,0586 con `off`, −0,1024 con `shrink`, sobre 19.923 votos—.
Mandar gente ahí no es un refugio conservador: es empeorarla. El umbral existía justamente
para mandarla.

### Y lo que el guard desbloqueó: el merge de ids

Con el guard puesto se aplicaron los 143 alias de `legislador_id` (25.030 filas, 2.302 ids
→ 2.159). **Sin** el guard el merge empeoraba (0,1317 → 0,1301); con el guard cuesta
**−0,0007**, y casi todo está en 2019-2023 (−0,0140), la era con menos votos (3,5% de la
base). Las dos eras que le importan al producto no se mueven. Se aplicó igual porque **son
la misma persona**: una métrica que mejora manteniendo partida una carrera mide un
beneficio accidental. Detalle en el ADR-0018.

---

# PARTE III — LO PENDIENTE

## III.A — Decidido y formulado (falta implementar)

Estos cinco están acordados con Franco y escritos en su forma final. **Ninguno está en el
código.** El orden de implementación propuesto está al final.

### III.A.1 — El gate del dictamen $\mathcal{C}_c$

**La cobertura no es un modulador gradual: es una CONDICIÓN DE ADMISIBILIDAD.** Por
reglamento un proyecto sólo puede tratarse si tiene dictamen de mayoría **en todas** las
comisiones a las que se giró, o en un **plenario** de todas ellas. Tener dictamen en 2 de 3
no da "menos probabilidad": **no habilita el tratamiento**.

$$\mathcal{C}_c \;=\; \mathbb{1}\Big[\;\underbrace{K_c \supseteq G_c}_{\text{dictamen en todas las giradas}}\;\;\lor\;\; \underbrace{\text{plenario}(G_c)}_{\text{un dictamen que las abarca}}\;\Big]$$

| símbolo | qué es |
|---|---|
| $G_c$ | comisiones a las que se giró en la cámara $c$ |
| $K_c$ | comisiones que emitieron dictamen de mayoría |
| $\mathcal{C}_c$ | 1 si es tratable por la vía normal, 0 si no |

Es **excepción legítima** a la doctrina (ADR-0016, excepción 1): es una regla del cuerpo,
no la decisión de nadie.

**Estado del dato (medido 03-09, sobre 1.496 proyectos votados en recinto en Diputados):**

| situación | proyectos | ¿recuperable? |
|---|---:|---|
| con firmas parseadas | 1.069 (71,5%) | ya está |
| el PDF existe pero el parser falló | 62 (4,1%) | sí, arreglando el parser |
| **no hay dictamen en ningún lado** | **365 (24,4%)** | **no — es sobre tablas** |

**Conclusión operativa:** parsear al 100% lleva la cobertura de 71,5% a 75,6%. **La vía
sobre tablas es seis veces más grande que todo lo que compra parsear.**

### III.A.2 — El dictamen entra POR LEGISLADOR (reemplaza a $\delta$)

**El planteo que corrige la versión anterior.** Poner $a_\ell=1$ cuando firma el jefe
equivale a decir que **compromete el 100% de las bancas de su bloque**. Pero la deslealtad
existe igual: es lo que el modelo mide en $d_i$ y aplica dos pasos después. Asumir
disciplina perfecta acá y desvío individual allá es **contarse dos veces la misma cosa, en
sentidos opuestos**.

Franco: *"la firma del jefe de bloque no debería involucrar 100% de las bancas del
partido... la deslealtad existe haya o no firmado el jefe de bloque el dictamen"*.

$$\text{logit}(P_i^{\text{dict}}) \;=\; \text{logit}(P_i) \;+\; \underbrace{\beta_1 F_i}_{\text{firmó él}} \;+\; \underbrace{\beta_2\,(1-d_i)\,J_{\ell(i)}}_{\text{firmó su jefe, filtrado por su lealtad}} \;+\; \underbrace{\delta(\text{carácter})}_{\text{consenso, medido por el carácter}}$$

> ✅ **APROBADO 03-09 (Franco):** $\beta_3 W_{-\ell}$ **sale** y lo reemplaza el carácter del
> dictamen. Motivo: $W_{-\ell}$ cambia de signo al agregar el carácter (+0,26 → −1,46), o
> sea que mide lo mismo y peor. Enmienda registrada en el ADR-0016.

| símbolo | qué es |
|---|---|
| $F_i\in\{0,1\}$ | el propio legislador firmó el dictamen |
| $J_{\ell(i)}\in\{0,1\}$ | el **jefe de su bloque** firmó |
| $(1-d_i)$ | su **lealtad** — cuánto le pesa lo que hizo su jefe |
| $W_{-\ell(i)}$ | anchura de los **otros** linajes firmantes (bancas ajenas / $M_c$) |

**Por qué esta forma:**

1. **No hay doble conteo.** La lealtad aparece una vez, filtrando el efecto del jefe. Con
   $d_i=0{,}05$ recibe casi todo el empujón; con $d_i=0{,}40$ recibe el 60%. Que es el
   fenómeno real: **la firma del jefe arrastra a los leales y no a los díscolos**.
2. **El peso del bloque grande EMERGE, no se declara.** Si el jefe de un bloque de 90
   firma, son 90 legisladores los que reciben $\beta_2(1-d_i)$ y el agregado sale de la
   simulación: $\text{efecto} \approx b_\ell\,\beta_2\,(1-\bar d_\ell)$ — **modulado por la
   disciplina del bloque**, que un término $b_\ell/M_c$ escrito a mano no captura.
3. **Habilita el condicionamiento por tema**, que es como el legislador realmente lee un
   dictamen: si firmó su jefe, de qué bloques más, y sobre qué materia.

**Lo que se pierde y hay que aceptar:** ya no hay un $\delta_c$ único e interpretable por
cámara. El efecto del dictamen sólo se ve corriendo la simulación con y sin él.

### 🔬 ESTIMADO 2026-09-03 — dos de los tres términos se confirman, el tercero no

**Script:** `modelo/ensemble/src/estimar_beta_dictamen.py` · **Salida:**
`modelo/ensemble/outputs/beta_dictamen.json`
**Muestra:** 709 actas con dictamen identificado, **138.351 votos**, walk-forward, errores
estándar **clusterizados por acta**.

**El diseño: `logit(P_i)` del motor entra como OFFSET, no como regresor.** Así los β miden
**lo que el dictamen agrega POR ENCIMA de lo que el motor ya sabe** — que es exactamente el
número que la fórmula necesita sumar, sin re-escalar nada. Y el offset absorbe el historial,
el bloque y la presencia de cada persona, así que no hacen falta efectos fijos de legislador:
ya están adentro de $P_i$.

| término | coef | se (cluster) | p | veredicto |
|---|---:|---:|---:|---|
| $\beta_1$ — **$F_i$, firmó él** | **+1,529** | 0,110 | <0,0001 | ✅ **confirmado** |
| $\beta_2$ — **$(1-d_i)J_\ell$, firmó su jefe × lealtad** | **+0,645** | 0,172 | 0,0002 | ✅ **confirmado** |
| $\beta_3$ — $W_{-\ell}$, anchura de otros | +0,262 | 0,227 | 0,25 | 🔴 **no identificado** |

**$\beta_3$ hay que sacarlo, y por un motivo concreto, no por el p-valor:** al agregar el
carácter del dictamen, $W_{-\ell}$ **cambia de signo** (+0,26 → −1,44). Un coeficiente que
se da vuelta al agregar un control es colinealidad, no efecto: **$W_{-\ell}$ y el carácter
miden lo mismo** —cuánto consenso hubo—, y el carácter lo mide mejor.

### El carácter del dictamen sobrevive a los controles de selección

La objeción del 03-09 era que los proyectos con dictamen disputado *son* proyectos más
conflictivos, así que parte del efecto sería selección. Medido en capas anidadas:

| modelo | DISPUTADO vs ÚNICO | qué descuenta |
|---|---:|---|
| M0 crudo | −2,298 | nada |
| M1 + offset del motor | **−2,644** | quién es cada legislador |
| M2 + tema y origen | **−2,285** | qué clase de proyecto es |

**Dos lecturas:**

1. **Con el offset el efecto CRECE** (−2,30 → −2,64). El motor estaba *tapando* información
   del dictamen: parte de lo que el dictamen dice ya venía en $P_i$ con el signo contrario.
2. **Con tema y origen cae sólo 14%** (−2,64 → −2,29) y sigue con $p<0{,}0001$. **La
   selección existe pero es chica: el grueso es información real del dictamen.**

### 🔴 Un bug de matcheo casi nos hace tirar el término que Franco pidió

La primera corrida daba $\beta_2 = +0{,}039$ con **$p = 0{,}88$** — o sea "la firma del jefe
no importa", que es justo el término que Franco insistió en agregar el 26-08.

Era falso. El roster de jefes trae formas cortas (`ROSSI, AGUSTIN`) y las firmas traen la
forma larga (`ROSSI, Agustín Oscar`); comparar el string entero resolvía **21 de 80** jefes.
Y las firmas del **Senado viven en otro parquet** que no estaba cargando, así que ningún
jefe del Senado se resolvía. Con clave `APELLIDO|PRIMER-NOMBRE` y las dos fuentes: **50 de
80**, y $\beta_2$ pasa a **+0,645 con $p=0{,}0002$**.

> **Atenuación por error de medición, de manual: el ruido en $J_\ell$ empujaba el
> coeficiente a cero.** Un término correcto se veía nulo por una diferencia de formato de
> nombre. Es el primo hermano de la trampa de las comas en las comisiones, y ya son dos
> veces que un cruce mal hecho casi nos hace sacar algo que sí estaba.

### Formulación resultante

$$\text{logit}(P_i^{\text{dict}}) = \text{logit}(P_i) + \underbrace{1{,}53\,F_i}_{\beta_1} + \underbrace{0{,}65\,(1-d_i)\,J_{\ell(i)}}_{\beta_2} + \underbrace{\delta(\text{carácter})}_{\text{reemplaza a }\beta_3}$$

con $\delta(\text{ÚNICO}) = 0$ (referencia), $\delta(\text{DISPUTADO}) = -2{,}29$,
$\delta(\text{mayoría sin minoría}) = -2{,}36$, $\delta(\text{sólo minoría}) = -2{,}02$.

> ~~🔴 TODO ESTO ES DE DIPUTADOS. El Senado no tiene dictámenes usables porque el parser
> arranca en `clase="unico"`.~~ **CORREGIDO el 04-09-2026 — ADR-0017. El diagnóstico era
> medio cierto y medio al revés.**
>
> **Lo que sí era un bug:** el parser perdía el rótulo del Senado, que va en el SUMARIO
> ("Dictamen de mayoría en el proyecto de ley…") y quedaba pisado por la cabecera genérica
> del cuerpo ("DICTAMEN DE COMISIÓN"). Arreglado, con su test.
>
> **Lo que NO era un bug:** las mayorías que faltan son reales. Leídas **193 Órdenes del
> Día del Senado (2008-2026)**, sólo **3 (1,6%)** rotulan "de mayoría" y **ninguna** "de
> minoría". El Senado expresa el desacuerdo como **"EN DISIDENCIA (PARCIAL/TOTAL)" dentro
> del dictamen único** — 213 firmas de 18.105. Es una diferencia institucional entre
> cámaras. (Y las 19 "minorías" que el parquet mostraba eran **una reimpresión** del mismo
> dictamen en `senado-2018-16.pdf`, no un despacho.)
>
> **Lo que de verdad trababa al Senado era el CABLEADO:** `firmas_por_acta()` leía un solo
> parquet de firmas (Diputados) y `acta_expediente.parquet`, que también es sólo Diputados.
> Con `acta_expediente_todas.parquet` y las dos cámaras, el Senado pasa de **0 a 474 actas
> con carácter**, y sobre `--camara senado --muestra 400` (23.047 votos):
>
> | término | coef | se | p |
> |---|---:|---:|---:|
> | $\beta_1$ — $F_i$ | **+2,22** | 0,71 | 0,0018 |
> | $\beta_2$ — $(1-d_i)J_\ell$ | **+2,28** | 0,63 | 0,0003 |
>
> **Pero $\delta$ sigue sin ser estimable en el Senado**, y ahora se sabe por qué: el panel
> da `reparto_caracter = {"UNICO": 23047}`, 100% único, sin varianza. **No lo arregla ningún
> parser.** Si el Senado va a tener término de dictamen, tiene que salir de la
> **disidencia**. → URGENTE D.

> ⚠️ **PENDIENTE DE FRANCO — tres cosas.**
> 1. **Sacar $\beta_3$ y poner el carácter en su lugar** modifica el §III.A.2 del ADR-0016.
> 2. **No toqué el motor.** `puerta_a.py` y `nowcast_puertas.py` están intactos; esto es
>    estimación y documentación. Prender δ es cambio de motor y va con su backtest.
> 3. ~~**Faltan 30 de 80 jefes** en el roster. $\beta_2$ está atenuado: el valor real es más
>    grande que +0,645.~~ **RESUELTO el 04-09 (URGENTE 10) y la expectativa NO se cumplió.**
>    El roster va de 50/80 a **76/80** con `legislador_id` explícito (4 filas quedan vacías
>    a propósito: la canónica tiene dos ids para la misma persona → URGENTE C). En el A/B
>    controlado (`modelo/ensemble/outputs/beta_dictamen_ab_2026-09-04.json`, `--muestra 400
>    --seed 7`) **β₂ no se mueve**: 2,4034 → 2,3782, muy adentro de un error estándar. Lo
>    que sube β₂ es la **tabla de enlace** (1,343 → 2,403 con el roster fijo). Lo que hace
>    el roster es **bajar el ruido en el Senado**: SE 0,722 → 0,634 (−12%), p 0,00095 →
>    0,00033, con el coeficiente quieto. Motivo: **23 de los 30 jefes que faltaban son del
>    snapshot 2026-07-30** y la canónica llega al 2026-06-25 en Diputados — todavía no
>    tienen actas que tocar. Los niveles de esa tabla son de `--muestra 400` y **no** son
>    comparables con el +0,645 de arriba, que sale de la corrida completa; lo comparable es
>    la diferencia entre filas.

### III.A.3 — El $\varepsilon$ baja al legislador, y hacen falta DOS piezas

**Pieza 1 — piso y techo de certeza individual.** Franco: *"nunca debería estar en 100% la
probabilidad de apoyar como tampoco en 0% la de no apoyar"*.

$$\tilde{P_i} \;=\; \varepsilon_0 \;+\; (1-2\varepsilon_0)\,P_i \qquad\Longrightarrow\qquad \tilde{P_i}\in[\varepsilon_0,\,1-\varepsilon_0]$$

Encogimiento **afín**, no recorte: preserva el orden entre legisladores. Un clip aplasta a
todos los extremos al mismo valor y destruye el ranking de pivotes.

**Pero el piso individual NO arregla la sobreconcentración**, y eso hay que decirlo.
Medido con 20.000 corridas (140 a favor con $P_i=0{,}97$, 117 en contra con $P_i=0{,}04$,
umbral 129):

| $\varepsilon_0$ | $P_c$ sin shock | con shock $\tau=1{,}0$ |
|---:|---:|---:|
| 0,00 | 1,0000 | 0,8771 |
| 0,02 | 1,0000 | 0,8744 |
| 0,05 | **0,9983** | 0,7758 |
| 0,10 | 0,9734 | 0,6526 |

Con $\varepsilon_0=0{,}05$ la cámara sigue dando **99,8%**. **La razón es que el problema
no son los $P_i$ extremos sino el supuesto de independencia:** 257 monedas independientes
concentran, por sesgadas o no que estén.

**Pieza 2 — shock común.**

$$P_i^{(j)} \;=\; \sigma\big(\text{logit}(\tilde{P_i}) + \tau\,\eta_j\big), \qquad \eta_j \sim \mathcal{N}(0,1)$$

$\eta_j$ es **compartido por todos los legisladores de la corrida $j$**: en algunas
simulaciones el cuerpo entero se corre junto. Es la **excepción 2** del ADR-0016, y es lo
único que produce colas gordas.

- **$\varepsilon_0$** arregla la *afirmación individual*: la lista de pivotes deja de mentir.
- **$\eta_j$** arregla la *concentración agregada*: las bandas dejan de mentir.

Ambas nacen en el legislador; ninguna toca $P_c$. **El clip se elimina.**

### 🔬 ESTIMADO 2026-09-03 — $\varepsilon_0 \approx 0{,}02$ y $\tau \approx 1{,}2$

**Script:** `modelo/ensemble/src/estimar_epsilon_tau.py` · **Salida:**
`modelo/ensemble/outputs/epsilon_tau.json` · 497 actas, **57.848 votos**.

#### $\varepsilon_0$: casi no cambia el acierto, y arregla mucho la confianza

| $\varepsilon_0$ | Brier | log-loss |
|---:|---:|---:|
| 0,000 | 0,13688 | 0,45238 |
| **0,020** | — | **0,42465** ← óptimo |
| **0,025** | **0,13659** ← óptimo | — |
| 0,050 | 0,13694 | 0,42688 |
| 0,100 | 0,13951 | 0,43946 |
| 0,200 | 0,15218 | 0,48034 |

**Brier mejora 0,21%. Log-loss mejora 6,13%.** Y esa brecha *es* el resultado, no un detalle:
Brier castiga el error promedio y log-loss castiga la **confianza equivocada**. Que uno
apenas se mueva y el otro mejore 30 veces más dice exactamente lo que la calibración del
baseline mostraba: **el motor no está lejos, está demasiado seguro.**

$\varepsilon_0 = 0{,}02$ es un valor chico y modesto —nadie pasa de 98% ni baja de 2%— y
alcanza. Los valores grandes (0,10 y más) **empeoran las dos métricas**: encoger de más
destruye información real.

#### $\tau$: la sobredispersión es de 39×, y no es sesgo

| | valor |
|---|---:|
| **$\tau$ (mediana por acta)** | **1,197** |
| IQR de $\tau$ | [0,881; 1,458] |
| Diputados / Senado | 1,294 / 1,187 |
| **sobredispersión observada** | **38,9×** |
| **fracción del error que es sesgo** | **0,0007** |

**La varianza real del recuento por acta es ~39 veces la que produce suponer votos
independientes.** Y la fracción del error atribuible a sesgo sistemático es **0,07%**: el
motor no apunta al lado equivocado, **se dispersa mucho más de lo que admite**.

> **Esto cierra el argumento de §III.A.3 con un número.** El problema nunca fueron los
> $P_i$ extremos —por eso $\varepsilon_0$ óptimo es apenas 0,02— sino **el supuesto de
> independencia**, y ahí el factor es 39×. Las dos piezas son necesarias y ninguna
> reemplaza a la otra.

**Nota de método:** el estimador por mínimos cuadrados (`res² ~ aS + bS²` sin constante)
**no sirve** y quedó reportado como `tau_lstsq_NO_USAR`: $S$ y $S^2$ están casi
perfectamente correlacionadas entre actas —todas tienen ~el mismo $n$—, así que el ajuste
manda todo al término lineal y $b$ sale con signo arbitrario (daba negativo en Diputados y
2,62 en Senado). El despeje directo por acta, $\tau^2 = (\text{res}^2 - S)/S^2$, con
**mediana** en vez de media, es robusto a las actas donde el motor erró de lado.

> ⚠️ **PENDIENTE DE FRANCO.** $\tau \approx 1{,}2$ está estimado sobre el error del motor
> ACTUAL. Si δ (§III.A.2) mejora las predicciones, parte de esa dispersión debería
> desaparecer y $\tau$ hay que **re-estimarlo después**, no antes. El orden importa: si se
> fija $\tau$ ahora y después entra δ, las bandas quedan infladas.

### III.A.4 — El arrastre entre cámaras lo lee el senador, no el Senado

La versión del 25-08 violaba la doctrina sin que lo notáramos:

$$\text{logit}(P_S) = \text{logit}(P_S^{0}) + \psi\Big(\tfrac{A_D}{E_D} - \tfrac{1}{2}\Big) \qquad \text{🔴 agregado}$$

El margen de Diputados **es información pública que cada senador lee**, igual que el
dictamen. Va donde va el dictamen:

$$\text{logit}(P_i^{\text{rev}}) = \text{logit}(P_i) + \psi_{\ell(i)}\Big(\tfrac{A_D}{E_D} - \tfrac{1}{2}\Big) \qquad \text{✅ por legislador}$$

**Y así aparece algo que la versión agregada no podía expresar:** $\psi$ **depende del
bloque**. Un senador del espacio que impulsó el proyecto lee una media sanción holgada como
respaldo; uno de la oposición la lee como amenaza. Con un $\psi$ único los dos se mueven
igual — que es falso.

**Estimado el 03-09** sobre `cadena_camaras.parquet`.

### 🔬 ESTIMADO 2026-09-03 — el arrastre es enorme; la heterogeneidad por bloque, **no probada**

**Script:** `modelo/ensemble/src/estimar_psi_arrastre.py` · **Salida:**
`modelo/ensemble/outputs/psi_arrastre.json` · 239 proyectos con votación en las dos
cámaras, **24.570 votos** en la revisora, offset del motor, cluster por acta.

| modelo | coeficiente | valor | se | p |
|---|---|---:|---:|---:|
| **P1 — $\psi$ único** | margen de origen | **+7,221** | 0,695 | <0,0001 |
| **P2 — $\psi$ por lado** | margen × lado del linaje | +5,490 | 3,148 | **0,081** |
| | lado del linaje | +2,603 | 1,161 | 0,025 |
| **P3 — $\psi$ por linaje** | FdT-UxP | +9,339 | 1,335 | <0,0001 |
| | RADICALISMO | +7,546 | 0,854 | <0,0001 |
| | OTRO / PROVINCIAL | +7,509 | 0,674 | <0,0001 |

**El arrastre existe y es grande.** Con un margen medio de 0,388 sobre ½, $\psi=7{,}2$ da
un corrimiento de **+2,8 en logit** para el legislador medio de la revisora. Es de los
efectos más grandes del motor.

> 🔴 **Y acá me tengo que corregir.** El 26-08 escribí que con un $\psi$ único "los dos se
> mueven igual — **que es falso**". Lo afirmé como hecho y **el dato no lo respalda todavía**:
> la interacción con el lado del bloque da $p=0{,}081$, y los $\psi$ por linaje (9,34 vs
> 7,51) difieren en 1,8 con errores estándar de 1,34 y 0,67 — los intervalos se pisan.
>
> **La dirección es la predicha y el signo es el correcto, pero con 239 proyectos no
> alcanza para afirmarlo.** Lo honesto: bajar el término al legislador es correcto **por
> construcción** (doctrina); que *además* revele heterogeneidad por bloque era una
> **hipótesis empírica**, y hoy está sugerida, no establecida.
>
> **Implementar $\psi$ único** y dejar $\psi_\ell$ como refinamiento a re-testear cuando
> haya más cadena.

#### La confusión con "proyecto de consenso": descartada

La objeción obvia es que un proyecto que sale holgado de la cámara de origen **suele ser un
proyecto de consenso**, que iba a pasar holgado en las dos por su naturaleza. El offset
absorbe *quién* es cada legislador pero **no absorbe qué clase de proyecto es**. Se corrió
la misma capa que a δ:

| modelo | $\psi$ | se | p |
|---|---:|---:|---:|
| P1 sin controles | +7,221 | 0,695 | <0,0001 |
| **P1b + tema y origen** | **+7,725** | 0,816 | <0,0001 |

**El efecto no se cae: crece un poco.** La composición temática de los proyectos que van a
dos cámaras no explica el arrastre. $\psi$ queda **listo para implementar en su versión
única**.

*(Nota: en P1b la constante sale con error estándar enorme por separación en las dummies de
tema; no afecta al coeficiente del margen, que es el que interesa.)*

### III.A.5 — El sobre tablas es una VOTACIÓN, no una mezcla de probabilidades

**Es el agujero más grande del modelo: 24,4% de los proyectos votados en recinto.**

La versión del 25-08 mezclaba dos probabilidades agregadas:

$$P = (1-\Lambda)\,P_D P_S + \Lambda\,P^{\text{tablas}} \qquad \text{🔴 agregado}$$

Pero el sobre tablas **es una votación del cuerpo con umbral de dos tercios**: lo mismo que
ya sabemos simular, cambiando el umbral.

$$P^{\text{tablas}}_c = \frac{1}{N}\sum_{j=1}^{N} \mathbb{1}\Big[A_j^{\text{tablas}} \ge \lceil \tfrac{2}{3}E_j \rceil\Big]$$

#### Lo que dijo la medición (26-08) — y corrigió el planteo original

Franco propuso que, sin dictamen, el legislador queda "falto de información" y decide con
su **récord por tema**, el ICG y la proximidad electoral, **desacoplado del bloque**. El
mecanismo es correcto; la consecuencia empírica es la opuesta. Sobre 185 actas (59 en
Diputados, 14.630 votos), walk-forward, $n_i\ge8$:

| en Diputados | sobre tablas | resto |
|---|---:|---:|
| tasa afirmativa individual | **50,4%** | 78,5% |
| acierto de la **línea de bloque** | **95,4%** | 97,4% |
| acierto del **récord propio general** | **45,0%** | 79,7% |
| Brier del récord propio | **0,435** | 0,141 |
| Brier de decir 0,50 y listo | 0,250 | 0,250 |

1. **El $\theta>0$ original era falso.** La tasa afirmativa cae de 78,5% a 50,4%:
   acompañar el tratamiento no es más barato, es **más caro**. Sobre lo observable
   $\theta<0$. (Ojo: sesgo de selección — lo que llega a votarse sobre tablas ya es
   material disputado.)
2. **El récord general no sirve acá: hace daño.** Brier 0,435 es **peor que decir 0,50**.
   Dice "afirmativo" el 88% de las veces en los dos regímenes, pero la tasa real pasa de
   78% a 50%: está calibrado para otra base.
3. **El bloque sobrevive casi intacto: 95,4%.** **El legislador sin dictamen no cae en sí
   mismo: cae en su bloque, más fuerte.** Sacada la información cara, queda la barata.

#### Dos correcciones a la lectura inicial (mismo día)

**(a) El desvío NO sube. Era efecto de composición.** Primero se comparó actas contra actas
(mediana 0,56% → 1,36%, Mann-Whitney $p=2\cdot10^{-4}$). Rehecho **pareado —los mismos
legisladores consigo mismos**, $n\ge30$ normales y $n\ge10$ sobre tablas:

| | Diputados (216 leg.) | Senado (159 leg.) |
|---|---:|---:|
| suben / bajan | **54 / 133** | **33 / 92** |
| Wilcoxon pareado | $p=0{,}10$ | $p=0{,}13$ |
| corrimiento mediano en $\text{logit}(d)$ | **0,000** | **0,000** |

**El legislador mediano se desvía menos, no más.** ⇒ **$d_i$ entra sin factor de
inflación.**

**(b) La medición no refuta la propuesta de Franco, refuta una versión más débil.** El
récord usado fue el **general**, no el **temático** — que es lo que él propuso y **cuya
tabla no existe**. La propuesta original está **sin testear, no refutada**.

#### Formulación acordada

$$\text{logit}(P_i^{\text{tablas}}) \;=\; \text{logit}\big(P_i^{\text{bloque}}(s_\ell, d_i)\big) \;+\; \theta \;+\; \gamma^{\text{tab}}\,z_{\text{ICG}} \;+\; \underbrace{\rho\,\text{logit}(\text{rec}_i^{\text{tema}})}_{\text{🔲 no existe la tabla}}$$

- $P_i^{\text{bloque}} = s_\ell(1-d_i) + (1-s_\ell)\tfrac{d_i}{2}$ — la rama de bloque de
  §I.4 **sin modificar**. La lealtad partidaria ya vive ahí dentro;
- **el corte $n_i\ge8$ del récord propio NO aplica en esta vía** — único cambio estructural,
  y el que la medición respalda;
- $\theta<0$, estimable sobre las 185 actas;
- $d_i$ **sin inflar**, por (a).

Y la cadena queda como dos caminos al mismo recinto, **ambos simulados desde legisladores**:

$$P_c^{\text{total}} = \underbrace{\mathcal{C}_c \cdot P_c}_{\text{vía dictamen}} + \underbrace{(1-\mathcal{C}_c)\cdot P^{\text{tablas}}_c \cdot P_c}_{\text{vía sobre tablas}}$$

Un proyecto sin dictamen completo sólo llega si consigue los dos tercios; uno con dictamen
no necesita esa votación.

### 🔬 ESTIMADO 2026-09-03 — $\theta$ es negativo, grande, y **sólo existe en Diputados**

**Script:** `modelo/ensemble/src/estimar_theta_sobre_tablas.py` · **Salida:**
`modelo/ensemble/outputs/theta_sobre_tablas.json`
**Diseño:** 186 actas de sobre tablas contra las **1.420 actas normales del mismo mes y la
misma cámara** —para que $\theta$ no confunda "sobre tablas" con "época"—, 162.325 votos,
offset = $\text{logit}(P_i^{\text{bloque}})$ **sin** el atajo al récord propio, errores
estándar clusterizados por acta.

| | sobre tablas | resto |
|---|---:|---:|
| tasa afirmativa observada | **64,5%** | 86,1% |
| $P_i^{\text{bloque}}$ que predice el motor | **0,802** | 0,816 |

**El motor predice prácticamente lo mismo en los dos regímenes y la realidad difiere en 21
puntos.** Ese hueco es exactamente lo que $\theta$ tiene que llenar.

| estimación | $\theta$ | se | p |
|---|---:|---:|---:|
| contra el resto del mismo mes/cámara | **−1,493** | 0,153 | <0,0001 |
| sólo sobre tablas (constante) | −1,078 | 0,144 | <0,0001 |
| **Diputados** | **−2,047** | 0,217 | <0,0001 |
| **Senado** | **−0,262** | 0,185 | **0,157 (nulo)** |

**Dos conclusiones:**

1. **Mi $\theta > 0$ original era falso, y por bastante.** "Acompañar el tratamiento es más
   barato que acompañar la ley" suena razonable y el dato dice lo contrario: acompañar
   sobre tablas cuesta **1,5 en logit** más caro.
2. **🎯 $\theta$ es un fenómeno de DIPUTADOS.** En el Senado no se distingue de cero
   ($p=0{,}16$). Encaja con lo que ya habíamos medido el 26-08: en el Senado el desvío en
   sobre tablas *bajaba* (1,76% → 1,25%) mientras en Diputados subía. **En el Senado el
   sobre tablas es trámite; en Diputados es trinchera.** ⇒ **$\theta$ va por cámara:**
   $\theta_D = -2{,}05$, $\theta_S = 0$.

> ⚠️ **Sesgo de selección, dicho de frente.** Lo que llega a votarse sobre tablas ya es
> material disputado —muchas veces una moción de la oposición que el oficialismo bloquea—.
> Así que $\theta$ **no es "el costo de tratar sobre tablas" en abstracto**: es el
> corrimiento **condicional a que alguien haya pedido el tratamiento**. Para el nowcast
> alcanza, porque se aplica en el mismo escenario en que se midió. Como parámetro causal,
> no.

## III.B — Propuesto, sin decidir

### III.B.1 — Proximidad electoral

$$\pi'_{i} = \pi_{i}\,e^{-\theta/T} \qquad\qquad \text{logit}(P'_{i}) = \text{logit}(P_{i}) - \phi\,\tfrac{1}{T}\,\mathbb{1}[\text{costoso}]$$

$T$ = días a la elección. Dos efectos: baja la asistencia y sube el costo de acompañar lo
impopular. **Backtest de significancia primero.** Cumple la doctrina: entra por $P_i$ y
$\pi_i$.

### III.B.2 — Asimetría del ICG (para discutir, no aplicar)

$$z^{*} = \text{sgn}(z)\,|z|^{\alpha}\big(1 + (\kappa-1)\mathbb{1}[z<0]\big)\cdot\big(1 + \lambda(\text{ICG}_{\text{ref}} - \text{ICG}_{0})\big)$$

$\alpha$ = aceleración, $\kappa$ = cuánto más pesa la caída, $\lambda$ = amplificación en
niveles bajos. **Estos parámetros se acuerdan, no se estiman** — igual que el break-even
del ADR-0008. Recupera la asimetría de teoría prospectiva perdida el 11-08.

### III.B.3 — Récord por tema $\rho$ — BLOQUEADO por falta de insumo

Necesita `rec_i^tema`: afirmativos/emitidos de cada legislador **condicionado a la
taxonomía**, con corte walk-forward. Hoy sólo existe el récord general.

**Compromiso registrado (URGENTE 8).** Franco: *"cuando modelemos la probabilidad de apoyar
un proyecto con determinado tema, deberíamos revisar esta formulación, ya que el tema
impactaría en el legislador"*. **Es revisión comprometida, no opcional.**

Hay que medir **antes** cuántos legisladores llegan a $n_i^{\text{tema}}\ge8$. Si son
pocos, el término entra como ruido y hay que encogerlo contra el récord general (mismo
Empirical-Bayes que el share, $k=5$).

**Lo que acota el margen:** con el bloque en 95,4% de acierto, un término temático disputa
como mucho el 4,6% restante en dirección — aunque puede aportar más en **calibración**, que
es lo que consume la simulación.

## III.C — Orden de implementación propuesto

**Paso 0 — congelar el baseline. ✅ HECHO 03-09.**

`backtest_cadena` está neutralizado (ADR-0012) y `backtest_agregador` mide contra una
variable casi constante (95,15% de aprobación). **La vara es el voto individual**, que
tiene 22,5% de negativos. Script nuevo: `evaluacion/baseline/src/baseline_voto_individual.py`.

**EL NÚMERO A BATIR — censo completo corrido por Franco el 03-09**
(6.091 actas, **730.574 votos**, las dos cámaras, 1997-2026, walk-forward):

| métrica | **censo** | *(muestra previa)* |
|---|---:|---:|
| **Brier** | **0,13819** | *0,15197* |
| skill vs climatología | **0,1304** | *0,1297* |
| accuracy | **0,8051** | *0,7823* |
| **MAE del margen por acta** | **0,1408** | *0,1502* |
| sesgo medio del margen | −0,0151 | *−0,0187* |
| Diputados / Senado (skill) | 0,130 / **0,072** | — |

**El skill agregado de la muestra clavó el del censo** (0,1297 vs 0,1304). Los estratos, no.

**Y el baseline ya dejó servidos los dos primeros cambios:**

1. **El techo de δ:** con dictamen **único** el motor da skill **−1,38** en el censo
   (−3,25 en la muestra: el signo aguanta, la magnitud no); con dictamen disputado, +0,22.
   **Está ciego justo en el caso fácil**, que es exactamente lo que δ corrige.
2. **La evidencia de $\varepsilon_0$:** la calibración muestra sobre-confianza en los dos
   extremos (bin 0 predice 0,054 y la realidad es 0,186; bin 9 predice 0,952 y es 0,928).
   Es el síntoma que ataca el encogimiento afín.
3. **Hallazgo inesperado, confirmado en el censo:** el **98,0%** de las predicciones sale
   del récord individual y sólo el **2,0%** de la rama de bloque (14.581 de 730.574), donde
   además tiene skill **−0,059**. Toda la maquinaria de share condicionado corre para 2 de
   cada 100 predicciones. **Revisado el 06-09: `MIN_HIST_INDIVIDUAL` bajó de 8 a 1** y la
   rama de bloque se achicó a 0,4% de las predicciones — que es lo correcto, porque su
   skill es NEGATIVO (−0,10 sobre 19.923 votos): no era un refugio, era un pozo.
4. **Por era:** el skill cae de +0,216 (2011-2015) a **+0,024 desde 2023** y −0,011 en
   2015-2019. **Los dos valles son recambios de gobierno.** → URGENTE 9.

Detalle en `evaluacion/baseline/RESULTADOS.md`.

**Después, UN CAMBIO POR VEZ**, cada uno con backtest antes y después. Con cuatro cambios
simultáneos no se sabe cuál fue.

| orden | cambio | por qué ahí |
|---|---|---|
| 1 | **δ del dictamen** (§III.A.2) con efectos fijos | único que *prende* algo apagado; señal grande y ya verificada |
| 2 | **$\varepsilon_0$ + shock común** (§III.A.3) | barato; hace honestas la probabilidad y las bandas |
| 3 | **sobre tablas** (§III.A.5) | 24,4% de cobertura — la ganancia más grande |
| 4 | ~~**bug del quórum** (§II.2)~~ | **ya implementado 04-09, apagado.** Bajó de prioridad solo: medido, hoy mueve 0,0000. Prenderlo espera presentismo real |
| 5 | **$\psi$ entre cámaras** (§III.A.4) | sobre 1.166 proyectos con votación en ambas |
| 6 | **parser al 100%** y **récord por tema** | cola larga; ninguno bloquea a los anteriores |

**Por qué el parser va último:** compra 4,1 puntos de cobertura contra los 24,4 del sobre
tablas, y los 215 PDFs que fallan **no son un formato raro concentrado** — el motivo
dominante ("ancla sin nombres debajo") aparece parejo de 2008 a 2025. Es trabajo constante
contra ganancia chica.

---
---

# PARTE IV — METODOLOGÍA

Los principios que gobiernan cualquier cambio. Si una propuesta viola uno de estos, la
discusión es sobre el principio, no sobre el término.

## IV.1 — La doctrina: de la parte al todo (ADR-0016)

> **Todo factor entra en la decisión del LEGISLADOR, no en el agregado de la cámara.** El
> clima, el dictamen, las elecciones, lo que hizo la otra cámara: todo eso es información
> que una persona lee y procesa según su historial, su lealtad y el tema. La probabilidad
> de la cámara es la CONSECUENCIA de sumar esas decisiones, nunca un lugar donde se aplican
> correcciones.

```
información  →  P_i (decisión del legislador)  →  simulación  →  P_c  →  P_aprob
```

**Si un término se aplica a la derecha de la simulación, está mal ubicado**, salvo dos
excepciones: (1) **reglas institucionales** —umbrales, quórum, bancas, el gate
$\mathcal{C}_c$—, que no son decisiones de nadie; (2) **shocks correlacionados**, pero
implementados como shock **común dentro** de la simulación ($\eta_j$), no como recorte del
resultado.

**Al proponer un término, la pregunta es:** *¿esto lo lee una persona y decide, o es una
regla del cuerpo?* Si lo primero, va en $P_i$.

**Bajar un término al legislador no es prolijidad: cambia lo que el modelo puede decir.**
Los tres casos del 26-08: el arrastre **reveló** que $\psi$ depende del bloque; el
$\varepsilon$ **mostró que no alcanzaba**; el sobre tablas **obligó a preguntar qué lee esa
persona**, y la respuesta contradijo la hipótesis.

## IV.2 — Condicionar en logit, nunca multiplicando

Si $P=0{,}9$ y se multiplica por 1,2 da 1,08, que no es una probabilidad. El logit mapea
$[0,1]$ a toda la recta real, así que sumar ahí nunca se sale del rango.

$$\sigma(x)=\frac{1}{1+e^{-x}} \qquad \text{logit}(p)=\ln\frac{p}{1-p}$$

**Y no llamarlo $P(B|A)$.** No es un condicional bayesiano: son corrimientos aditivos en
log-odds. La notación bayesiana sugiere una estructura que no existe.

## IV.3 — Probabilidad de cruzar un umbral, no suma de probabilidades

$$P(\text{mayoría}) = P\!\left(\sum_i V_i \ \ge\ u\right), \qquad V_i\sim\text{Bernoulli}(P_i)$$

Sumar $\sum_i P_i$ da el **número esperado de votos**, que es otra cosa. La diferencia no
es formal: depende de la varianza. Por eso Monte Carlo y no aritmética.

## IV.4 — Walk-forward siempre (point-in-time)

Todo estimador usa **sólo información anterior** a la fecha del nowcast: `shift(1)` +
`expanding`. Sin el corte por fecha, un nowcast fechado 2024-06-01 usaba el **85% de sus
votos de después** de esa fecha.

## IV.5 — Encogimiento Empirical-Bayes para muestras chicas

$$\hat\vartheta = \frac{n\,\vartheta^{\text{obs}} + k\,\vartheta^{\text{prior}}}{n+k}, \qquad k=5$$

Se aplica al share ($s_\ell$) y al desvío ($d_i$). Con muestra chica manda el prior; con
muestra grande, lo observado. **El prior sale sólo de unidades con muestra sólida**, o los
novatos se encogen hacia el ruido de sus propios pares.

## IV.6 — Medir antes de creer, y elegir bien la unidad

**El caso que lo funda (26-08):** dos mediciones correctas del mismo fenómeno dieron
resultados opuestos. Comparando **actas** contra actas, el desvío subía en sobre tablas con
$p=2\cdot10^{-4}$. Comparando **legisladores consigo mismos**, el efecto desaparecía.

> **Un $p$ chico sobre unidades mal elegidas es efecto de composición con cara de
> hallazgo.** La pregunta antes de creerle a un número es *qué se mantiene fijo*.

Corolario: **un porcentaje imposible es un bug, no un fenómeno.** 100% de una comisión
faltante, 82% de ampliación de giro donde había 8%, 2,1% de cobertura — los tres eran
errores de parseo o de filtrado.

## IV.7 — Trampas conocidas de estos datos

| trampa | síntoma | regla |
|---|---|---|
| **Nombres de comisión con comas** | una comisión falta el 100% de las veces | matchear contra el **catálogo** (151 comisiones, del nombre más largo al más corto), **nunca partir por separadores**. Medido: partir por `[;,]` produce **36% de fragmentos basura**; el catálogo resuelve **99,2%** |
| **`expedientes_giros` mezcla cámaras** | cobertura 2,1% en vez de 63,6% | filtrar por cámara **antes** de cualquier cálculo sobre giros |
| **`od_numero` se repite entre períodos** | 1.722 números para 2.517 pares | la clave es `(periodo, od_numero)` o directamente `archivo` |
| **Cachés vacíos ≠ datos faltantes** | 90 minutos de descarga para reproducir un archivo idéntico | mirar el **parquet**, no la carpeta de trabajo. `Archivos_Borrar/` y `data/raw/` son descartables por diseño |
| **Actas `AUX`** | shares inflados hacia el sí | excluir homenajes, trámite y consenso |

## IV.8 — Todo cambio al motor se presenta en tres niveles (ADR-0015)

1. **La función** — qué hace ahora, qué hacía antes, por qué.
2. **El motor en conjunto** — quién lee la salida modificada, si mueve el número publicado
   o sólo el desagregado, si cambia algún contrato, qué supuesto se agrega o se saca.
3. **La fórmula** — cómo queda **este archivo** después del cambio.

**Si el cambio no se puede ubicar en la fórmula, es señal de que no se entiende del todo
qué se está cambiando** — y ese es el momento de frenar, no de mergear.

Aplica también a lo que **apaga** algo: el término sigue acá, marcado como inactivo. Así no
se pierde —como pasó con la asimetría del ICG— lo que se sacó y por qué.

## IV.9 — Dos respuestas, siempre (ADR-0007)

Cada informe entrega **la probabilidad y los nombres**. Es la razón operativa de la
doctrina: un corrimiento agregado mueve el número sin decir sobre quién actuar.

- **La banda** es incertidumbre agregada: $[Q_5(A_j),\,Q_{95}(A_j)]$ sobre las 2.000
  corridas. Responde *"¿cuál es el respaldo mínimo y máximo plausible?"*.
- **Los pivotes** son individuales: se marca `incógnita` a quien cae en
  $0{,}35\le P_i\le 0{,}65$, ordenado por cercanía a 50/50.

---

# Constantes del motor

| constante | valor | dónde | qué hace |
|---|---:|---|---|
| `N` (simulaciones) | 2.000 | `nowcast_puertas` | corridas de Monte Carlo |
| `DESVIO_MIN_INDIVIDUAL` | 0,02 | `ensemble` | piso de desvío |
| `P_INCERTIDUMBRE` | 0,01 | `ensemble` | el $\varepsilon$ del clip 🔴 |
| `REPARTO_DESVIO` | 1,0 | `nowcast_puertas` | todo el desvío a la conducta opuesta |
| `MIN_HIST_INDIVIDUAL` | **1** | `nowcast_puertas` | votos para creerle al récord propio. **Era 8; bajó el 06-09** — el encogimiento lo dejó sin trabajo y encima costaba (§II.5) |
| `MIN_CLUSTERS_CONFIABLE` | 20 | `estimar_beta_dictamen` | actas mínimas para que un SE cluster-robusto signifique algo |
| `ERA_FIJA` | 2023-12-10 | `nowcast_puertas` | era del récord con el guard apagado |
| `GUARD_ERA` | **True** | `nowcast_puertas` | deducir la era de la fecha (§II.5) |
| `SHRINK_RECORD` | **True** | `nowcast_puertas` | encoger el récord hacia el bloque (§II.5) |
| `K_SHRINK_RECORD` | 5,0 | `nowcast_puertas` | pseudo-conteo de ese encogimiento |
| `MERGE_IDS` | **True** | `entity_resolution` | aplicar la tabla de alias de `legislador_id` |
| `PRESENCIA_MINIMA` | 0,15 | `nowcast_puertas` | debajo no se cuenta como votante |
| `DESVIO_BISAGRA` | 0,20 | `nowcast_puertas` | umbral de bisagra |
| `INCERTIDUMBRE_INCOGNITA` | 0,35 | `nowcast_puertas` | $P\in[0{,}35;0{,}65]$ ⇒ incógnita |
| `k_shrink` | 5,0 | `bloque`, `modulador_icg` | pseudo-conteo del encogimiento |
| `MIN_DISPUTADAS` | 10 | `modulador_icg` | muestra sólida para el prior |
| `ventana_dias` | 730 | `bloque` | historia para la postura |
| `MA_MED` / `MA_CORTO` | 6 / 3 | `icg_contexto` | medias móviles del ICG |
| `PISO` / `TECHO` | 1,0 / 4,0 | `icg_contexto` | recorte del ICG |
| `USAR_CORTO` | False | `modulador_icg` | capa corta del ICG, apagada |

---

# Parámetros estimados el 2026-09-03 y el 2026-09-04 (ninguno implementado)

| parámetro | valor | se | p | script |
|---|---:|---:|---:|---|
| $\beta_1$ — firmó él ($F_i$) | **+1,529** | 0,110 | <0,0001 | `estimar_beta_dictamen.py` |
| $\beta_2$ — jefe × lealtad | **+0,645** | 0,172 | 0,0002 | idem *(roster completado el 04-09; el coeficiente no se movió, bajó el SE — §III.A.2)* |
| $\beta_1$, $\beta_2$ — **SENADO** | **+2,22 / +2,28** | 0,71 / 0,63 | 0,0018 / 0,0003 | idem `--camara senado` *(nuevo el 04-09: antes daba 0 actas — ADR-0017; `--muestra 400`)* |
| $\delta$ — **SENADO** | **no estimable** | — | — | el carácter es 100% ÚNICO en el Senado: sin varianza. No es el parser (ADR-0017) |
| ~~$\beta_3$ — anchura $W_{-\ell}$~~ | +0,262 | 0,227 | 0,25 | **DESCARTADO 03-09** (colineal) |
| $\delta$ — DISPUTADO vs ÚNICO | **−2,285** | 0,198 | <0,0001 | idem *(con tema y origen)* |
| $\delta$ — mayoría sin minoría | −2,356 | 0,223 | <0,0001 | idem |
| $\delta$ — sólo minoría | −2,019 | 0,395 | <0,0001 | idem |
| $\varepsilon_0$ | **0,020** | — | — | `estimar_epsilon_tau.py` |
| $\tau$ | **1,197** | IQR [0,88; 1,46] | — | idem |
| $\theta_D$ — sobre tablas, Diputados | **−2,047** | 0,217 | <0,0001 | `estimar_theta_sobre_tablas.py` |
| $\theta_S$ — sobre tablas, Senado | −0,262 | 0,185 | 0,157 | idem → **usar 0** |
| $\psi$ — arrastre entre cámaras | **+7,725** | 0,816 | <0,0001 | `estimar_psi_arrastre.py` |

**Todos son estimaciones sobre muestras (400-900 actas) con el motor ACTUAL como offset.**
Al implementar cualquiera hay que re-estimar los demás: los parámetros no son
independientes entre sí. En particular **$\tau$ se re-estima al final**, porque mide la
dispersión que el motor no explica y δ debería reducirla.

---

# Historial de correcciones a la fórmula

| fecha | qué cambió |
|---|---|
| 2026-08-13 | composición share × lealtad en $P_i$ — antes todo daba 99% |
| 2026-08-13 | ADR-0013: el $+1$ del umbral simple; antes **un empate aprobaba** |
| 2026-08-25 | ADR-0015: todo cambio al motor se presenta en la fórmula |
| 2026-08-25 | bug del quórum confirmado (abstenciones descartadas) |
| 2026-09-04 | quórum: arreglo implementado tras bandera apagada; medido, hoy Δ=0,0000 |
| 2026-08-26 | ADR-0016: doctrina de la parte al todo; auditoría de 12 términos |
| 2026-08-26 | el dictamen pasa de $\delta_c$ agregado a $\beta$ por legislador |
| 2026-08-26 | el $\varepsilon$ pasa de clip a $\varepsilon_0$ + shock común |
| 2026-08-26 | $\psi$ pasa de $P_S$ agregado a $\psi_\ell$ por senador |
| 2026-08-26 | sobre tablas pasa de mezcla agregada a votación simulada de 2/3 |
| 2026-08-26 | medido: en sobre tablas el bloque acierta 95,4% y el récord propio 45,0% |
| 2026-08-26 | corregido: el desvío **no** sube en sobre tablas (test pareado) |
| 2026-09-03 | medido: **δ es estimable** — el problema era la dependiente, no el predictor |
| 2026-09-03 | medido: el 24,4% sin dictamen es sobre tablas real, no dato faltante |
| 2026-09-03 | reestructura en tres partes: lo que corre / lo que no / lo pendiente |
| 2026-09-03 | baseline del voto individual: **Brier 0,15197** es el número a batir |
| 2026-09-03 | medido: el motor tiene skill **−0,19 en la era desde 2023** → URGENTE 9 |
| 2026-09-03 | estimados β, δ, ε₀, τ, θ y ψ — **ninguno implementado** |
| 2026-09-03 | β₃ ($W_{-\ell}$) se descarta: colineal con el carácter, cambia de signo |
| 2026-09-03 | θ resulta ser fenómeno de **Diputados**; en el Senado es nulo |
| 2026-09-03 | corregido: la heterogeneidad de ψ por bloque está **sugerida, no probada** |
