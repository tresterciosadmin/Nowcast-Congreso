# ADR-0034 — La fuga y el espejo: el harness contaba la respuesta y medía otro motor. Arreglados en la raíz; el número publicado se re-mide; lo que dependía de él, también.

**Fecha:** 2026-09-28 · **Estado:** HECHO · **Decide:** Claude, sesión de saneamiento delegada
por Franco (`coordinacion/PROMPT-CIERRE-DE-ETAPA.md`) · **Toca:** `modelo/ensemble/src/
nowcast_puertas.py` (corte `<`; extracción de `record_legisladores` y `necesita_cond_por_acta`),
`evaluacion/baseline/src/baseline_voto_individual.py` (reescrito: importa el motor),
`evaluacion/baseline/src/{censo_detalle_paralelo,medir_fuga_historia,resumen_censo_limpio,
medir_record_por_tema_limpio}.py`, `modelo/ensemble/src/{estimar_epsilon_tau,medir_tau_limpio,
chequear_direccion_beta}.py`, tests `test_historia_sin_fuga.py` y `test_harness_es_el_motor.py`
· **Enmienda:** ADR-0026 (ver abajo) · **Se relaciona con:** ADR-0018, ADR-0025, ADR-0032,
ADR-0033

**Fórmula (ADR-0015 nivel 3):** cambia. Se apaga $\text{rec}_i^{\text{tema}}$ (fila 18, queda
inactiva); el récord corta con `<`. Todo lo demás, igual. FORMULA actualizada en el mismo commit.

## Veredicto

1. **El motor es peor de lo que creíamos.** El número publicado pasa de **0,1611** (inflado por
   fuga) a **0,1333** [0,057; 0,198]. **En la era vigente, 0,010 [−0,26; 0,25]: no se distingue
   de la tasa base.**
2. **`RECORD_POR_TEMA` se apaga.** Su 11,06% era fuga: con la misma metodología y historia
   estricta da −2,9%; contra el motor en el censo limpio empeora 2,1% (IC por ley [0,8; 3,5]).
3. **τ casi no se mueve** (1,197 limpio contra 1,186 con el offset viejo), **pero la banda del
   recuento cubre el 63,6% de las actas, no el 99,88%** que se había reportado con un backtest
   que usaba la línea de bloque observada. No se cambió ningún valor: URGENTE U2.
4. **El razonamiento "offset contaminado ⇒ coeficientes conservadores" no se sostiene como
   regla.** En β, $F_i$ se sostiene (2,09 → 2,05) pero lealtad×jefe baja (1,75 → 1,29), y el
   offset con que se estimó β era *peor*, no mejor, que el limpio.
5. **El harness ya no es un espejo**: importa el motor, y un test lo compara contra `nowcast()`.

## Una sola causa, no dos hallazgos

ADR-0032 midió que 1.070 actas son 310 leyes: el n efectivo es la ley. La fuga de ADR-0033 es
**el mismo hecho** —las actas de una ley no son independientes— manifestándose en el punto
estimado en vez de en el error estándar. Se escribe como una sola regla (FORMULA §IV.6):

> **La unidad efectiva es el EXPEDIENTE, no el acta.** (a) clusterizar por acta subestima los
> errores estándar ~1,7×; (b) usar una acta de la misma ley como historia es fuga. Todo corte,
> cluster o ventana de historia se hace por expediente.

"Ley" = actas que comparten `proyecto_id` o expediente normalizado en cualquiera de
`origen_por_acta`, `acta_expediente_todas` y `tema_por_acta` (union-find,
`baseline_voto_individual.ley_por_acta`; el normalizador es `enlace_senado.normalizar_expediente`,
importado). Ninguna tabla sola pasa del 72% de cobertura. **El 15,3% de los votos cae en actas
sin ninguna clave**: ahí el corte por expediente no ve nada. Se loguea en cada corrida.

## FASE 1 — la fuga, en los dos lados

**Harness.** El récord se armaba con `shift(1).expanding()` sobre votos ordenados por fecha: al
predecir el art. 3 de una ley veía los arts. 1 y 2, del mismo día. Ahora sólo cuentan votos de
**fecha anterior y de otra ley**. **Motor.** `_alineacion_base` cortaba con `fecha <= hasta`: en
backtest el récord veía el día entero, **incluida el acta a predecir** (peor que el harness). Pasa
a `<`, el corte que ya usaba `proyectar_postura`. Se buscaron todas las ocurrencias del patrón
(`buscar.py` + grep sobre `<=` en filtros de fecha de `modelo/`, `variables/`, `datos/`,
`casos/`): es la única sobre historia de votos. Las otras son vigencias de mandato
(`padron_vigente`, `bloque._bancas_padron`, `ensemble.roster_nominal`, jefes de bloque),
calendarios (`icg_contexto`, `origen_lider`) o fechas de publicación (`origen_por_acta`); una
queda anotada en URGENTE: `puerta_a` ve dictámenes con `fecha_dictamen <= corte` (36 pares
dictamen–acta del mismo día, 34 proyectos).

**Cuánto pesaba cada arreglo.**

*El del harness* (misma postura, sólo cambia la historia del récord; `medir_fuga_historia.py`):

| historia del récord del harness | skill | IC 95% (leyes) | desde 2023 |
|---|---:|---|---:|
| `shift(1)` por fila (lo publicado) | 0,1613 | [0,097; 0,221] | 0,0627 |
| fecha estricta | 0,0916 | [0,036; 0,140] | −0,0293 |
| fecha estricta y otra ley | 0,0742 | [0,025; 0,117] | −0,1086 |

*El del motor* (el harness nuevo, que importa el motor, con el corte viejo `<=` contra el
nuevo; `resumen_censo_limpio.py`):

| corte del récord del MOTOR (mismos 691.677 votos) | skill | desde 2023 |
|---|---:|---:|
| `<=` (hasta el 28-09): ve el día entero, incluida el acta a predecir | **0,3257** | 0,3738 |
| `<`, sin excluir la ley (con récord por tema) | 0,1574 | 0,1919 |
| `<` y otra ley (con récord por tema) | 0,1152 | 0,0004 |
| **`<` y otra ley, sin récord por tema (el que queda)** | **0,1335** | **0,0100** |

**Cuál pesaba:** en el harness, el corte por fecha se llevó 0,07 de skill y el de la ley 0,02.
En el motor, el `<=` era una fuga mucho más grande (0,33 contra 0,16), porque metía el voto a
predecir en su propio récord; pero **el harness nunca usó ese camino**, así que el número
publicado se infló por la fuga del harness, no por la del motor. La del motor contaminaba
cualquier backtest que llamara a `nowcast()` o `alineacion_individual` con la fecha del acta
(`validar_*_capitulos.py`, `validar_piloto_titulos.py`, `prueba1_pivotes_por_capitulo.py`).
En la era vigente, excluir la ley es lo que más pesa (0,19 → 0,00): son 3,4 actas por ley.

**Tests** (`test_historia_sin_fuga.py`, 14): dos actas de la misma ley el mismo día, la segunda
no ve la primera; misma ley en fecha anterior tampoco; otra ley antes sí; el modo viejo SÍ tiene
la fuga (si no, el test no probaría nada); la definición vectorizada = fuerza bruta; el motor al
20-03 no ve las actas del 20-03; las claves de ley se unen.

## FASE 2 — matar el espejo

`perfil()` decía ser "espejo exacto de `perfil_legislador`". No lo era en el récord: el motor
lo condiciona por el ORIGEN del proyecto y el harness no. Ahora el harness **no calcula nada del
legislador**:

| pieza | de dónde sale |
|---|---|
| récord (general + por tema) | `nowcast_puertas.record_legisladores` — extraída de `nowcast()` |
| cuándo se carga `tema_por_acta` | `nowcast_puertas.necesita_cond_por_acta` — extraída de `nowcast()` (sin ella la postura no excluye las actas AUX) |
| postura del linaje | `bloque.proyectar_postura`, a la fecha exacta del acta (antes, memoizada por mes) |
| $P_i$ | `nowcast_puertas.perfil_legislador` |

El harness sólo decide **qué votos existían**. Las dos extracciones no cambian ningún cálculo
(49/49 tests del motor). **La barandilla:** `test_harness_es_el_motor.py` corre `nowcast()` real
y el harness sobre la misma acta y compara $P_i$ legislador por legislador: **238/238
iguales**. Si vuelven a divergir, falla.

**Dos diferencias con `nowcast()` que quedan, declaradas en el docstring:** (1) las áreas del
proyecto para RECORD_POR_TEMA salen de la clasificación del ACTA (en producción, de
`proyecto_taxonomias`); (2) en la rama de bloque ($n_i=0$) el desvío es el del linaje: `nowcast`
usa la ficha de `disciplina_individual.csv`, que **no es walk-forward** (se calcula con toda la
historia) — anotado en URGENTE. **Lo que el censo no mide:** β (prendido), ε₀+τη (en la
simulación), la presencia.

**Otros espejos del mismo tipo** (todos arman su propio récord con `shift(1)` por fila, sin
guard de era, sin encoger y sin origen, y los que importaban `perfil` ahora reciben el del
motor): `estimar_beta_dictamen.py` (β, δ), `estimar_epsilon_tau.py` (ε₀, τ),
`estimar_psi_arrastre.py` (ψ), `estimar_theta_sobre_tablas.py` (θ), `diagnostico_senado.py`,
`fase1_rec_por_tema.py` y `medir_rec_por_tema.py` (el 11,06%), `medir_guard_era.py`. También
`validar_beta_dictamen_walkforward.py` y `validar_sobre_tablas_walkforward.py`, que reusan
esos paneles. Quedan marcados en el código; **no se re-estimaron** salvo τ (y ε₀, que sale del
mismo script). `estimar_epsilon_tau.py` ahora lee el censo por defecto (`--panel censo`).

## FASE 3 — el número real

Censo con el harness nuevo, partido por fechas en 3 procesos (**34,4 min**; el del 27-09
tardó 13,8 porque calculaba una sola variante y memoizaba la postura por mes; éste calcula seis
variantes a la fecha exacta de cada acta). 691.845 votos, 5.856 actas, 3.731 leyes; en común
con el censo del 27-09, 691.677 votos con el mismo voto real.

| | antes (publicado) | **después** | IC 95% (leyes) |
|---|---:|---:|---|
| **skill global** | 0,1611 | **0,1333** | [0,057; 0,198] |
| hasta 2011 | 0,1546 | 0,1331 | [0,071; 0,190] |
| 2011-2015 | 0,2185 | 0,2770 | [0,190; 0,352] |
| 2015-2019 | 0,0954 | 0,0808 | [−0,044; 0,197] |
| 2019-2023 | 0,3308 | 0,0113 | [−0,203; 0,106] |
| **desde 2023** | 0,0474 | **0,0100** | [−0,264; 0,246] |
| Diputados | 0,158 | 0,126 | [0,051; 0,196] |
| Senado | 0,120 | 0,108 | [0,058; 0,150] |
| rama récord | 0,169 (97,3%) | 0,164 (95,3%) | [0,110; 0,220] |
| rama bloque | −0,102 (2,7%) | **−0,380 (4,7%)** | [−0,667; 0,135] |

(Los "antes" son los del censo del 06-09 que se publicó; sobre los mismos votos de hoy, el
harness viejo da 0,1614.) La rama de bloque crece porque el récord ahora está condicionado por
origen y sin la misma ley: más legisladores llegan sin ningún voto previo comparable.

## FASE 4 — lo que dependía del harness

### 4.1 `RECORD_POR_TEMA` — se apaga

| medición | mejora de Brier | IC 95% (leyes) |
|---|---:|---|
| la que lo prendió (`fase1_rec_por_tema.py`, `shift(1)`) | **+11,06%** | reproducida exacta |
| misma metodología, historia estricta (`medir_record_por_tema_limpio.py`) | **−2,91%** | [−8,6; +2,1] |
| contra el motor, censo limpio, total | **−2,12%** | [−3,5; −0,8] |
| contra el motor, censo limpio, votos donde actúa (39%) | **−6,36%** | [−10,1; −2,9] |
| ídem Diputados / Senado | −3,8% / **−20,5%** | |
| ídem hasta 2011 / 2011-2019 / desde 2023 | −19,6% / ≈0 / −10,8% | |
| contra el motor con su `<=` (el mundo con fuga) | +10,65% donde actúa | [+6,4; +14,9] |

La fuga explica el 11% entero: el récord por área veía los artículos de la misma ley, que
comparten tema. Criterio simétrico al que la prendió ⇒ **apagada** (`RECORD_POR_TEMA=0` por
defecto; la función queda). El panel de `REGENERAR` (proyecto hipotético, sin `proyecto_id`) no
se mueve; se mueven los nowcasts de proyectos con taxonomía.

### 4.2 τ — re-estimado, no aplicado

Mismo estimador (`estimar_epsilon_tau.estimar_tau`), mismos 691.677 votos, tres offsets
(`medir_tau_limpio.py`):

| offset | τ | IQR | ε₀ óptimo (log-loss) | sobredispersión |
|---|---:|---|---:|---:|
| motor con su `<=` | 1,146 | [0,76; 1,51] | 0,000 | 41× |
| harness viejo con fuga | 1,186 | [0,76; 1,48] | 0,015 | 40× |
| **motor limpio** | **1,197** | [0,88; 1,61] | **0,055** | 53× |

**La lógica se verificó y la dirección es la esperada, pero el tamaño no importa: 1%.**
(Diputados sí sube más: 1,23 → 1,32.) Lo que el prompt esperaba —bandas angostas— **es cierto,
por otra razón.** Simulando con la función del motor (`simular_con_guardas`, ε₀=0,035,
τ=1,19) sobre las $P_i$ limpias, la banda [p5,p95] contiene el recuento real en el **63,6%** de
5.851 actas, y el esperado sale **6,9 votos por debajo** del real. Sin τ, 14,8% (y sesgo 2,8):
τ agrega cobertura y también sesgo, porque un shock simétrico en logit baja la media cuando
las $P_i$ son altas. El 99,88% de ADR-0025 salía de `agregador.backtest`, que usa la línea de
bloque OBSERVADA. **TAU y EPSILON0 no se tocaron** (URGENTE U2).

### 4.3 β, δ, θ, ψ — marcados; β, chequeado

No se re-estiman. La tabla de parámetros de FORMULA los marca todos como "offset contaminado".
El chequeo de dirección en β (`chequear_direccion_beta.py`, mismo panel de 246.306 votos,
M6, cluster por LEY):

| offset | $F_i$ | lealtad×jefe | Brier del offset |
|---|---:|---:|---:|
| el de la estimación | 2,09 (0,40) | 1,75 (0,37) | 0,143 |
| harness con fuga | 1,92 (0,33) | 1,42 (0,35) | 0,121 |
| motor limpio | 2,05 (0,43) | **1,29** (0,33) | 0,135 |

**El razonamiento del prompt falla en lealtad×jefe**: con el offset limpio el coeficiente baja,
no sube. Y la premisa no aplica tal cual: el offset de la estimación tenía fuga pero era *peor*
que el limpio (le faltaban guard, encogimiento y origen). Conclusión: la dirección del sesgo
depende de todo lo que le faltaba a cada offset; **δ, θ y ψ no pueden darse por conservadores**.
Además, los SE clusterizados por ley son 3-4× los publicados por acta.

## Enmienda al ADR-0026

**ADR-0026 queda enmendado:** `RECORD_POR_TEMA` pasa de PRENDIDO a **APAGADO** el 28-09-2026.
La evidencia que lo sostenía (11,06% en el censo, positivo en todos los cortes) era fuga del
harness: el récord por área contaba los artículos de la misma ley votados el mismo día. Con el
harness limpio empeora el Brier. La implementación (`alineacion_individual_por_area`, sus tests,
la observabilidad de ADR-0031) queda intacta. Para volver a prenderlo hace falta una medición
que mejore el censo limpio. Se agregó una nota al principio del ADR-0026.

## FASE 6 — la regla y el quinto default silencioso

Escritas en FORMULA §IV.6 (la regla del expediente, arriba) y §IV.7 (la lista, que ya tiene
cinco: parser del Senado, AUX, comas en comisiones, encogimiento sin aviso, **y un `<=` donde
iba `<`**).

## Reproducir

```
python evaluacion/baseline/src/medir_fuga_historia.py                 # FASE 1, ~1 min
python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 3 # el censo, ~35 min
python evaluacion/baseline/src/resumen_censo_limpio.py                # FASE 3 y 4.1
python evaluacion/baseline/src/medir_record_por_tema_limpio.py        # de dónde salía el 11,06%
python modelo/ensemble/src/medir_tau_limpio.py                        # FASE 4.2
python modelo/ensemble/src/chequear_direccion_beta.py                 # dirección del sesgo en β
python evaluacion/baseline/tests/test_historia_sin_fuga.py
python evaluacion/baseline/tests/test_harness_es_el_motor.py
```
