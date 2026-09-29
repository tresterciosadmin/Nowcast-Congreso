# 01 — Qué hace el motor HOY

**Commit auditado:** `bcc62b3` (motor idéntico a `6e6b629`). Confianza: **V** = lo vi en código o lo corrí · **I** = inferido · **N** = no verificado. Rutas relativas a `Nowcast Congreso Argy/`.

## 0. Dos "números publicados" distintos

El repo llama "el número publicado" a dos cosas. Conviene no mezclarlas:

| | qué es | valor | cómo se produce |
|---|---|---|---|
| **A. el skill** | calidad del **voto individual** (P_i contra el voto real), 691.845 votos | 0,1333 [0,057; 0,198] | el censo (`censo_detalle_paralelo.py` → `resumen_censo_limpio.py`) |
| **B. la P(sanción) del panel** | la probabilidad que ve el usuario, de un **proyecto hipotético** del Ejecutivo en Diputados al 2026-06-01 | **0,6132** (`8b310c1`) | `REGENERAR.ps1:291` → `casos/nowcast_puertas_html.py` |

El panel B pasó de **0,9801 a 0,6132** el 15-09 22:10, cuando se prendió ε₀+τη (`64ff248`, mensaje del commit). Esa variación de 37 puntos se aceptó porque "se movió como se esperaba", no porque se contrastara con resultados (ver §6, borde iv). **El 0,9801 nunca fue una estimación: es 0,99 × 0,99, el techo del clip agregado** (`ensemble.py:319,374-376`); con `INCERTIDUMBRE_LEGISLADOR=0` el panel vuelve a dar exactamente 0,9801. **Y el titular que lee el usuario en el HTML no es esa salida:** lo recalcula `paprob()` en JavaScript (`casos/nowcast_puertas_html.py:237-240,278,296-297`), con clip [0,01; 0,99], sin τη y con las $P_i$ movidas por el ICG (γ de la tabla original de ADR-0008). Sobre el HTML regenerado hoy da **98,0%** contra 61,3% del motor.

**Lo que el panel B NO puede ejercitar** (V): no pasa `proyecto_id` (`REGENERAR.ps1:291-292`), así que **β no actúa** (`nowcast_puertas.py:836`: `if proyecto_id:`), **`RECORD_POR_TEMA` no actúa** (`:809`), `TEMA_AUTO` no actúa (`_tema_auto` devuelve `None` sin `proyecto_id`, `:256`) y los pasos A y C son `sin_dato`. El propio commit que prendió β lo dice: el panel salió "BYTE A BYTE IDÉNTICO" (`ec5fd05`).

## 1. La traza real (panel B), paso a paso

| # | paso | dónde | qué hace con los defaults |
|---|---|---|---|
| 1 | entrada | `REGENERAR.ps1:291` → `casos/nowcast_puertas_html.py:64-66` → `nowcast_puertas.nowcast` (`:775`) | `diputados`, `fecha=2026-06-01`, `origen=EJECUTIVO`, `n_sims=2000`, `seed=0`, `tipo_mayoria=SIMPLE` |
| 2 | votos | `nowcast_puertas.py:814` `bloque.cargar(CANONICA_CLEAN)` (`bloque.py:216`) | `votos_resuelto` + `actas_canonico`; `AFIRMATIVO/NEGATIVO/NO_ACOMPANA` (ausente y abstención se funden, `bloque.py:44-49`) |
| 3 | tema / origen | `:797-816` | `tema=None`; `origen_map` de `origen_por_acta.parquet` (`:817-820`); `cond=cargar_tema_por_acta()` porque `origen` está dado (`necesita_cond_por_acta`, `:498`) |
| 4 | **récord** de cada legislador | `record_legisladores` (`:508`, llamada en `:824`) → `alineacion_individual` (`:333`) → `_alineacion_base` (`:293`) | ventana = desde el inicio de la **era** de `F` (`GUARD_ERA` ON, `:303`), **`fecha < F`** (`:316`), sólo actas del **mismo origen** (`:317-319`). `p_af = n_af / n_emitidos` (`:363`), `presencia = emitidos / todas` (`:353,364`) |
| 5 | A y C | `:828-830` `caracter_de` | `sin_dato` (proyecto hipotético) |
| 6 | **postura del bloque** (B) | `proyectar_postura` (`:843`, `bloque.py:480`) | historia `[F−730d, F)` (`:543-544`); sin actas AUX (`:556-562`); share afirmativo por linaje **por acta** (`:564-568`); condicionado por origen y por gobierno (`:582-603`) y **encogido k=5** hacia el incondicional (`:751`); línea = AFIRMATIVO si share ≥ 0,5 (`:755`) |
| 7 | roster + desvío | `roster_nominal` (`ensemble.py:134`) | padrón vigente a `F` (`:183`); desvío individual de la **ficha** `disciplina_individual.csv` (escalera `ficha_reciente → ficha_global → bloque`, `MIN_VOTOS_FICHA=20`, `:227-252`) |
| 8 | **P_i** | `armar_roster` (`:648`) → `perfil_legislador` (`:528`) | si `n_emitidos ≥ 1`: `P_i = (n·rec + 5·s_ℓ)/(n+5)` (`:574`); si no: `s_ℓ(1−d)+(1−s_ℓ)d/2` (`:577`). β sólo si hay `contexto_dictamen` (`:676-678`): no en el panel |
| 9 | a (línea, desvío) | `a_linea_y_desvio` (`:582`) | `p ≥ 0,5` → AFIRMATIVO con desvío `1−p`; si no NEGATIVO con desvío `p`; `REPARTO_DESVIO=1,0` |
| 10 | **piso de desvío** | `ensemble.simular_con_guardas` (`ensemble.py:361`) | `desv = max(desvío, 0,02)` ⇒ **P_i queda en [0,02; 0,98]** |
| 11 | **ε₀ y τη** | `agregador.simular_votacion` (`agregador.py:203-224`) | `P̃_i = ε₀+(1−2ε₀)P_i` con ε₀=0,035; `P_i^(j) = σ(logit P̃_i + τ·η_j)`, τ=1,19, un `η_j~N(0,1)` por simulación compartido por los 257 |
| 12 | presencia | `agregador.py:229-239` | `P(afirma)·π_i`; el resto va a ausencia |
| 13 | recuento y umbral | `agregador.py:240-278` | 2.000 simulaciones; aprueba si `afirm ≥ umbral` (SIMPLE = emitidos//2+1, `:123`) y hay quórum (`:276-277`) |
| 14 | clip agregado | `ensemble.py:367-376` | **apagado solo** porque ε₀>0 |
| 15 | carácter A/C | `condicionar` (`puerta_a.py:396`) | **identidad**: `COEF_POR_DEFECTO` es todo cero (`puerta_a.py:101`) |
| 16 | sobre tablas | `_via_sobre_tablas` (`:603`) | devuelve la entrada sin tocar (`SOBRE_TABLAS` OFF) |
| 17 | cámara revisora (D) | `p_voto_revisora` (`puerta_d.py:118`, llamada `:862`) | mismos pasos 6-14 con el padrón de la otra cámara y el **mismo** récord `ind`; `delta=0` ⇒ `ajuste_paso_origen` es identidad (`puerta_d.py:75-87`) |
| 18 | **el número** | `:873` | `p_final = b["p"] · d["p"]` |

## 2. La fórmula efectiva (con los defaults de hoy, panel B)

Para el legislador $i$, linaje $\ell$, proyecto de origen $o$ a la fecha $F$ (era $E(F)$, gobierno vigente):

$$\mathrm{rec}_i=\frac{\#\text{AF}}{\#\text{AF+NE}}\ \text{en votos con } E(F)\!\le\! t\!<\!F,\ \text{origen}=o \qquad
P_i=\begin{cases}\dfrac{n_i\,\mathrm{rec}_i+5\,s_\ell}{n_i+5}& n_i\ge 1\\[6pt] s_\ell(1-d_i)+(1-s_\ell)\tfrac{d_i}{2}& n_i=0\end{cases}$$

$$\bar P_i=\min(\max(P_i,\,0{,}02),\,0{,}98)\qquad \tilde P_i=0{,}035+0{,}93\,\bar P_i\qquad P_i^{(j)}=\sigma\!\big(\mathrm{logit}\,\tilde P_i+1{,}19\,\eta_j\big)\ \cdot\ \pi_i$$

$$P_c=\Pr\!\big[\textstyle\sum_i \mathbf 1\{u_{ij}<P_i^{(j)}\}\ \ge\ \lceil\tfrac{\text{emitidos}}2\rceil+1\ \wedge\ \text{quórum}\big]\quad(2.000\ \text{sims}),\qquad \boxed{P_{\text{aprob}}=P_D\cdot P_S}$$

con $s_\ell$ = share del linaje (730 días, `<`, mismo origen y gobierno, encogido $k=5$), $d_i$ = desvío de la ficha (sólo en la rama sin récord y en β), $\pi_i$ = presencia.

**Diferencias con `FORMULA-COMPLETA.md` §I.00** (líneas 102-128):

| | §I.00 dice | el código hace | conf. |
|---|---|---|---|
| Piso de desvío | no aparece | `P_i ∈ [0,02; 0,98]` **antes** de ε₀ (`ensemble.py:361`). En el censo, **23,2% de los votos tienen P_i>0,98** (el piso muerde) | V |
| Pasos A y C | "la cadena de puertas" (`nowcast_puertas.py:9-16`, ADR-0012) | son **identidad**; el número es exactamente `P_B × P_D` | V |
| Origen | "condicionado por origen" | sólo si el llamador pasa `origen` (`:817-820`); si no, el récord es incondicional (~0,048 de skill, ver `02`) | V |
| β | "si el proyecto tiene dictamen" | no actúa en el panel; en un proyecto real usa los coeficientes de `beta_dictamen.json`, estimados con el offset contaminado | V |
| Simulación | "ε₀ y τη actúan en la simulación" | ✓ coincide; pero la §I.00 no dice que **el recuento condiciona a `p_presente`** (π_i escala la P) | V |

## 3. Inventario de banderas (default EFECTIVO en el código)

Búsqueda por `os.environ`/`os.getenv` en `modelo/`, `variables/`, `evaluacion/`, `definiciones.py`, `rutas.py`. **Banderas que cambian el cálculo del número** (V):

| bandera | default efectivo | dónde | qué cambia | la condicionan | test que la ejerce |
|---|---|---|---|---|---|
| `GUARD_ERA` | **ON** | `nowcast_puertas.py:119` | era del récord = la del gobierno de `F` (si no, fija 2023-12-10) | — | `test_guard_era.py` (on/off) |
| `SHRINK_RECORD` | **ON** | `:131` | encoge el récord hacia $s_\ell$, $k=5$ | — | **ninguno nombra la bandera** |
| `MIN_HIST_INDIVIDUAL` (constante) | **1** | `:97` | antes 8 | — | consumido como contrato por el harness |
| `INCERTIDUMBRE_LEGISLADOR` | **ON** | `:194` | prende ε₀ y τη (y apaga el clip agregado) | — | `test_incertidumbre_legislador.py` (on/off) |
| `EPSILON0` / `TAU` | **0,035 / 1,19** | `:192-196` | los valores de arriba | `INCERTIDUMBRE_LEGISLADOR` | **ninguno fija el valor** |
| `BETA_DICTAMEN` | **ON** | `beta_dictamen.py:71` | corrimiento logit por legislador (`F_i`, lealtad×jefe) | `proyecto_id` con dictamen; lee `beta_dictamen.json` (`:73,79-107`); si falta, cae a 0 con un `warning` | `test_beta_dictamen.py` (default fijado, líneas 85-90) |
| `RECORD_POR_TEMA` | **OFF** | `:219` | récord por área | `proyecto_id` o `tema` (`:809`) | **0 tests nombran la bandera**; sí el parámetro `record_por_tema=` |
| `TEMA_AUTO` / `COMBINAR_TEMAS` | **OFF / `primaria`** | `:155,161` | tema de la postura de bloque desde la taxonomía | `proyecto_id` | `test_tema_auto.py` |
| `SOBRE_TABLAS` | **OFF** | `sobre_tablas.py:72` | vía "sobre tablas" | `es_admisible(caracter)` | `test_sobre_tablas.py` (default fijado) |
| `QUORUM_ABSTENCIONES` | **OFF** | `agregador.py:102` | quórum cuenta abstenciones | modo asistencia | `test_agregador.py` |
| `MATCH_AUTOR_FUZZY` | **ON** | `origen_lider.py:217` | matching difuso del autor (define el **origen**) | — | `test_origen_lider.py` |
| `MIN_VOTOS_FICHA` | **20** | `ensemble.py:57` | umbral de la escalera de desvío | — | **ninguno** |
| `EMBUDO_FUENTE` | `auto` | `embudo.py:708` | fuente del embudo | — | **ninguno** (el embudo no entra al número) |

**No estaban en la lista del prompt** (V): `TAU`, `MIN_VOTOS_FICHA`, `EMBUDO_FUENTE`, y en la CLI del agregador `N_SIMS` (400), `SIN_RUIDO`, `ASIST`, `MAX_ACTAS`, `EPSILON0`/`TAU` (`agregador.py:462-472`). Además ~12 variables que sólo mueven **rutas** (`CANON`, `DISC`, `OUT`, `EXP_CLEAN`, `LEG_DATA`, `CLEAN`, `PROYECTOS_DB`, `P_EMBUDO`, `NOWCAST_REPO`, `rutas.py:63`…) y el modelo del clasificador LLM (`TAXO_MODEL`, `agente_taxonomias.py:61`).

**Un mismo nombre, dos defaults** (V; candidato a sexto "default silencioso" de FORMULA §IV.7):

| nombre | valor A | valor B |
|---|---|---|
| `EPSILON0` / `TAU` | 0,035 / 1,19 en `nowcast_puertas.py:195-196` | **0 / 0** en la CLI de `agregador.py:471-472` (así se corrió el `agregador.backtest` que dio el 99,88%) |
| `MIN_VOTOS` | 50 en `disciplina.py:368` | 5 en `asistencia.py:88` |
| `N_SIMS` | 2.000 (parámetro de `nowcast()`) | 400 en `agregador.py:462` |

**Ningún test fija el valor** de `RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0`, `TAU`. Por eso el commit que apagó `RECORD_POR_TEMA` (`8b310c1`) no tocó ningún test para hacerlo (sus archivos: sólo `test_harness_es_el_motor.py`).

**Comentarios que contradicen al código** (V): `nowcast_puertas.py:832-834` y el docstring de `armar_roster` (`:656`) dicen "BANDERA APAGADA POR DEFECTO" para `BETA_DICTAMEN`, que está ON desde el 14-09; el bloque de `GUARD_ERA` (`:99-119`) abre con "bandera APAGADA por defecto" y termina "PRENDIDO POR DEFECTO"; `ensemble.py:343` dice que ε₀/τ "están apagados por defecto" (lo están a nivel de la función, no de `nowcast()`).

## 4. Los 20 términos de ESTADO-REAL contra el código

| # | término | doc | ¿existe en código? | default efectivo | ¿alcanza el panel B? | ¿doc = código? |
|---|---|---|---|---|---|---|
| 1 | share del bloque $s_\ell$ | ✅ | `bloque.py:564-568,751` | siempre | **sí** (ancla del récord y rama sin récord) | ✓ |
| 2 | desvío $d_i$ | ✅ | `ensemble.py:227-252` (ficha) | siempre | sí, sólo rama sin récord (4,7% de los votos del censo) | ✓ |
| 3 | presencia $\pi_i$ | ✅ | `nowcast_puertas.py:364` → `agregador.py:229` | siempre | sí | ✓ |
| 4 | récord propio | ✅ | `:293-330,574` | ON, `n≥1`, `<` | sí, **si se pasa `origen`** | ✓ |
| 5 | umbrales y quórum | ✅ | `agregador.py:106-123,276` | siempre | sí | ✓ |
| 6 | Monte Carlo 2.000 | ✅ | `:777`, `agregador.py:240` | `seed=0` | sí | ✓ |
| 7 | ε clip agregado | ⚪ | `ensemble.py:367-376` | apagado *mientras* ε₀>0; **vuelve con `INCERTIDUMBRE_LEGISLADOR=0`** | no | ✓ (falta el **piso 0,02**, que sigue) |
| 8 | quórum con abstenciones | ⚪ | `agregador.py:102` | OFF | no | ✓ |
| 9 | δ agregado del dictamen | ⚪ | `puerta_a.py:101,373-395` corre, con coeficientes 0 | 0 | ejecuta, no mueve | ✓ |
| 10 | ICG | ⚪ | **ninguno en el camino** (sólo `casos/nowcast_puertas_html.py:47-60` lo *muestra*) | — | no | ✓ |
| 11 | gate del dictamen $\mathcal C_c$ | ⚪ | aproximación en `puerta_a.caracter_de` + `es_admisible` | — | no | ✓ |
| 12 | β | ✅ PRENDIDO | `beta_dictamen.py` | **ON** | **no** (sin `proyecto_id`) | ⚠️ "prendido" es cierto sólo para proyectos reales con dictamen |
| 13 | ε₀+τη | ✅ PRENDIDO | `agregador.py:203-224` | ON, 0,035 / 1,19 | **sí** (movió el panel 0,98→0,61) | ✓ |
| 14 | ψ arrastre | ⚪ | **sin código** (sólo `estimar_psi_arrastre.py`) | — | no | ✓ |
| 15 | sobre tablas θ | ⚪ | `sobre_tablas.py` (109 líneas) + `_via_sobre_tablas` | OFF | no | ✓ |
| 16 | proximidad electoral | 🔲 | **sin código** | — | no | ✓ |
| 17 | asimetría del ICG | 🔲 | **sin código** | — | no | ✓ |
| 18 | récord por tema | ⚪ APAGADO | `alineacion_individual_por_area` (~110 líneas) | **OFF** | no (`proyecto_id`) | ✓ |
| 19 | multietiqueta / TEMA_AUTO | ⚪ | ramas `union/ponderada/peor_tema` de `bloque.py` (~120 líneas) | OFF | no | ✓ |
| 20 | récord por origen heredado | ⚪ | sólo `evaluacion/baseline/src/record_por_origen*.py` | — | no | ✓ |

Los estados de ESTADO-REAL coinciden con el código en las 20 filas. Lo que **no** aclara: (a) las filas 12 y 18-19 no pueden actuar en el panel; (b) el piso de desvío no figura como término.

## 5. Los cinco bordes "nunca medidos" (V, mirando el código)

1. **Presencia $\pi_i$.** El harness evalúa sólo votos emitidos: `baseline_voto_individual.py:644` filtra `conducta ∈ {AFIRMATIVO, NEGATIVO}`. Ausencias y abstenciones no entran a ninguna métrica.
2. **Share del bloque como pronóstico.** Sólo se mide donde actúa solo (rama sin récord: 4,7% de los votos, skill −0,38). La "Fase 0" (≈0,99) usó la línea **observada** en la misma acta (`agregador._linea_bloque_por_acta`, `:307`).
3. **Desvío individual.** `disciplina_individual.csv` se calcula con **toda la historia** (`disciplina.py` sin corte de fecha); `roster_nominal` lo lee tal cual (`ensemble.py:204-211`). El harness lo esquiva usando el desvío del linaje (`baseline_voto_individual.py:609-610`), o sea que **el censo no ejercita el código de desvío de producción**.
4. **De $P_i$ a $P_{\text{aprob}}$.** Ningún test ni script contrasta $P_{\text{aprob}}$ con resultados a partir de $P_i$ pronosticadas: `agregador.backtest` usa la línea observada y `medir_tau_limpio.py` mide el **recuento**, no la aprobación. *(Se mide por primera vez en `02`, con `contraste_aprobacion.py`.)*
5. **β en el censo.** `Contexto.p_legisladores` (`baseline_voto_individual.py:586-613`) no llama a `beta_dictamen`.

## 6. Hallazgos de la fase

1. **El panel publicado no ejercita β, `RECORD_POR_TEMA` ni `TEMA_AUTO`.** De los términos "prendidos" de ESTADO-REAL, en el número que ve el usuario actúan: récord (con origen), share, desvío (rama sin récord), presencia y ε₀+τη. [V]
2. **La "cadena de puertas" son dos simulaciones multiplicadas.** A y C están en cero desde el 25-08 (`Megacanje`, `5aff5b0`): `P = P_B × P_D`. [V]
3. **Hay un término activo que la fórmula no muestra**: el piso `DESVIO_MIN_INDIVIDUAL=0,02` (`ensemble.py:361`; el 23,2% de los votos del censo topan en 0,98). Al nivel individual el piso más ε₀=0,035 **mejora** el Brier (0,13910 → 0,13731; óptimo ε₀≈0,055: 0,13712) y el log-loss (0,524 → 0,432). Lo que no está medido es el efecto sobre el recuento agregado. [V, sobre `censo_detalle_2026-09-28.parquet`]
4. **La medición 0,1333 vale para "origen conocido".** El origen es `DESCONOCIDO` en el 43% de las actas (`origen_por_acta.parquet`: 2.582 de 5.998); ahí el récord es incondicional. El panel siempre pasa `--origen`. [V]
5. **Producción importa el script de estimación de β** (`beta_dictamen.py:102` → `estimar_beta_dictamen.py`, que importa el harness en `:271`): un cambio en un estimador puede romper el número. [V]
6. **Tres nombres de variable con dos defaults distintos** (`EPSILON0/TAU`, `MIN_VOTOS`, `N_SIMS`) y **comentarios que dicen lo contrario del código** en `BETA_DICTAMEN` y `GUARD_ERA`. [V]
7. **Cuatro constantes sin test que fije su valor** (`RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0`, `TAU`): el valor de una constante de producción puede cambiar sin que falle nada. [V]
8. **Trampa del detalle del censo**: la columna `p` de `censo_detalle_*.parquet` es la variante que la bandera dejaba **al generarlo** (el del 28-09 13:58 tiene `RECORD_POR_TEMA` prendido: skill 0,115, no 0,1333). El número publicado sale de `p__estricta__general` (`resumen_censo_limpio.columna_publicada`). Lo usé mal en mi primera corrida. [V]
