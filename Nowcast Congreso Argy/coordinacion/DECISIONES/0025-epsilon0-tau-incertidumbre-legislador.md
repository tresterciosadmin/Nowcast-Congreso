# ADR-0025 — ε₀ + τ·η_j: la incertidumbre baja al legislador (§III.A.3)

**Fecha:** 2026-09-16 · **Estado:** IMPLEMENTADO, MEDIDO y **PRENDIDO**
(`INCERTIDUMBRE_LEGISLADOR=1` por defecto desde el 16-09) · **Decide:** Franco
("Hagamos el cambio"), prioridad asignada antes por él mismo ("Asignale
prioridad y resolvamos ese shock común") ·
**Toca:** `modelo/agregador_institucional/src/agregador.py`,
`modelo/ensemble/src/ensemble.py`, `modelo/ensemble/src/puerta_d.py`,
`modelo/ensemble/src/nowcast_puertas.py` · **Se relaciona con:** ADR-0016
(doctrina de la parte al todo), §II.1 y §III.A.3 de `FORMULA-COMPLETA.md`

## Contexto

`FORMULA-COMPLETA.md` §III.A.3 tenía esto **decidido y estimado desde el
03-09-2026**, pero no implementado. El problema que resuelve:

`ensemble.simular_con_guardas` recorta $P_c$ (la probabilidad de la CÁMARA) a
$[0{,}01;\,0{,}99]$ **después** de simular. Es un parche sobre el síntoma, y
viola la doctrina (ADR-0016 §II.1): actúa sobre el agregado en vez de en el
legislador. Peor: **no arregla lo que tiene que arreglar**. Medido con el
escenario de referencia (140 a favor con $P_i=0{,}97$, 117 en contra con
$P_i=0{,}04$, umbral 129): con $\varepsilon_0=0{,}05$ la cámara sigue dando
**99,8%**. El problema no son los $P_i$ extremos: es que **257 votos
tratados como independientes concentran** pase lo que pase con las
probabilidades individuales.

## Decisión

Dos piezas, las dos a nivel **legislador** (ninguna toca $P_c$):

$$\tilde{P_i} = \varepsilon_0 + (1-2\varepsilon_0)\,P_i \qquad\qquad P_i^{(j)} = \sigma\big(\text{logit}(\tilde P_i) + \tau\,\eta_j\big),\ \ \eta_j\sim\mathcal N(0,1)$$

- **$\varepsilon_0$** (encogimiento afín, no recorte): ningún legislador es una
  certeza absoluta. Preserva el ORDEN entre pivotes — un clip los aplasta a
  todos al mismo valor.
- **$\tau\eta_j$** (shock compartido): **un solo $\eta_j$ por simulación**,
  igual para los 257 (o 72) legisladores de esa corrida. Es la **excepción 2**
  del ADR-0016 (shock correlacionado, no corrección al agregado) y es lo único
  que reproduce la sobredispersión real.

**Implementado en `agregador.simular_votacion`** (`epsilon0: float = 0.0, tau:
float = 0.0`, apagados por defecto → **ni un draw de más al rng** cuando están
en 0, byte a byte igual que antes). $P_i$ es `probs[:,0]` (la probabilidad de
AFIRMATIVO que ya calculaba `_prob_conductas`, antes de escalar por
presencia). NEGATIVO y NO_ACOMPAÑA se reparten lo que le queda a $P_i^{(j)}$
**en la misma proporción que tenían entre sí antes del shock** — el shock
mueve "¿cuánta gente acompaña hoy?", no "¿quién se ausenta en vez de votar en
contra?", que es una pregunta distinta y no la que $\eta_j$ está pensado para
responder.

**El clip agregado se apaga solo cuando la incertidumbre baja al legislador**
(`ensemble.simular_con_guardas`): con `epsilon0>0` o `tau>0`, `p_incertidumbre`
pasa a 0. Apilar las dos sería doble-contar la misma incertidumbre en dos
niveles — el error exacto que el ADR-0016 existe para evitar.

**Bandera única, `INCERTIDUMBRE_LEGISLADOR`** (`modelo/ensemble/src/
nowcast_puertas.py`), apagada por defecto. Prendida, usa `EPSILON0`/`TAU`
(re-estimados, ver abajo) en las DOS cámaras simétricamente — origen
(`simular_con_guardas` directo) y revisora (`puerta_d.p_voto_revisora`, que
ahora también acepta `epsilon0`/`tau` y los pasa derecho).

## Re-estimación 2026-09-16 — por qué no se reusó ciegamente el 1,197 del 03-09

`FORMULA-COMPLETA.md` tenía una advertencia explícita: *"$\tau$ está estimado
sobre el error del motor ACTUAL. Si $\delta$ mejora las predicciones, parte de
esa dispersión debería desaparecer y $\tau$ hay que re-estimarlo después, no
antes."* Desde el 14-09, `BETA_DICTAMEN` está prendido por defecto — así que
antes de fijar el valor, se corrió `estimar_epsilon_tau.py` de nuevo (2.485
actas, 293.655 votos — 5× la muestra del 03-09).

| | 03-09 (497 actas) | 16-09 (2.485 actas) |
|---|---:|---:|
| $\varepsilon_0$ óptimo (logloss) | 0,020 | **0,035** |
| $\tau$ mediana | 1,197 | **1,190** |
| sobredispersión observada | 38,9× | **41,0×** (37× con $\varepsilon_0$) |
| mejora Brier / logloss con $\varepsilon_0$ | 0,21% / 6,13% | 0,39% / 9,29% |

**$\tau$ es casi idéntico** (1,197 → 1,190) pese al cambio de motor. Esperable:
ni `estimar_epsilon_tau.py` ni `baseline_voto_individual.py` incluyen
`beta_dictamen` en su `p_motor` — el harness que mide la dispersión no cambió,
así que la dispersión que mide tampoco. Queda anotado como límite conocido de
esta estimación, no descartado en silencio: el día que el harness incorpore
$\beta$, hay que volver a medir.

Salida completa: `modelo/ensemble/outputs/epsilon_tau_2026-09-16.json`.
Defaults del motor: `EPSILON0=0,035`, `TAU=1,19`.

## Verificación

`modelo/agregador_institucional/tests/test_agregador.py` (+9 checks, 50/50
totales): apagado es byte a byte igual (incluye comparación de dict completo);
$\varepsilon_0$ solo no puede empeorar la sobreconfianza; $\tau$ es lo que
realmente ensancha la banda (afirm_std); con $\tau=1{,}2$ sobre el escenario de
referencia $P_c$ pasa de $\approx 1{,}0$ a $\approx 0{,}73$ — **coherente con la
tabla de `FORMULA-COMPLETA.md`** (0,8771 sin $\varepsilon_0$, 0,7758 con
$\varepsilon_0=0{,}05$, ambos con $\tau=1{,}0$: mi 0,7664 con $\varepsilon_0=0{,}02$
cae exactamente entre los dos); determinismo (mismo seed → mismo resultado);
$P_i$ pegado a 0 o 1 exacto no rompe el logit (clip interno a
$[10^{-9}, 1-10^{-9}]$); interactúa bien con el modo asistencia y las
abstenciones.

`modelo/ensemble/tests/test_incertidumbre_legislador.py` (5 checks, nuevo):
con datos reales — apagada da **exactamente** $P=0{,}9801$ (el control de
siempre); prendida (`EPSILON0=0,035, TAU=1,19`) mueve el número; restaurada
vuelve a $0{,}9801$.

Toda la suite existente sin regresión: `test_agregador.py` (50/50),
`test_nowcast_puertas.py` (49/49), `test_puerta_d.py` (24/24),
`test_ensemble.py` (33), `test_guardas_confianza.py` (14/14),
`test_beta_dictamen.py` (17/17), `test_puerta_a.py` (31/31),
`test_backtest_cadena.py` (53).

## Por qué esto NO es como el resultado negativo de la multietiqueta (ADR-0024)

Ahí la evidencia fue: implementar, medir contra el histórico real, y el
resultado salió en contra de la hipótesis — se reportó así y no se recomendó
activar. **Acá la evidencia apunta en la dirección contraria en todos los
puntos donde se la puede poner a prueba:**

1. El problema que $\tau$ resuelve —sobredispersión de 37-41×— no es una
   hipótesis: es una medición directa del error del motor de HOY, repetida dos
   veces con 5× de diferencia en tamaño de muestra y coincidiendo casi exacto.
2. $\varepsilon_0$ mejora Brier Y log-loss simultáneamente (nunca al revés) en
   las dos re-estimaciones.
3. El comportamiento en el escenario de referencia es exactamente el que la
   fórmula predecía antes de escribir una línea de código.

## Activación — 2026-09-16

Franco: *"Hagamos el cambio."* Antes de tocar el default se corrió la
verificación que el ADR dejaba pendiente — **paneles reales, no sólo el
escenario sintético** — comparando `INCERTIDUMBRE_LEGISLADOR=0` (el
comportamiento de siempre) contra `=1` (los defaults re-estimados
$\varepsilon_0=0{,}035$, $\tau=1{,}19$), llamando a `nowcast()` directo (no
hizo falta correr las 2-3 horas de `REGENERAR.ps1` completo: la bandera no
toca ningún parquet de entrada, sólo el paso de simulación):

| caso | apagada (de siempre) | prendida (16-09) |
|---|---:|---:|
| EJECUTIVO / Diputados @2026-06-01 (hipotético, el de la tabla de §III.A.3) | 0,9801 | 0,6132 |
| `HCDN292179` (Ley de Lobby) / Diputados @2026-07-31 | 0,9801 | 0,5277 |

Las dos se mueven en la dirección que predecía la fórmula — $P_c$ deja de
pegarse a 0,98 y baja a la banda 0,5-0,6 que el shock compartido predice para
mayorías no abrumadoras — y la suite completa (`test_nowcast_puertas.py`
49/49, `test_incertidumbre_legislador.py` reescrito para el nuevo default,
`test_ensemble.py` 33, `test_puerta_d.py` 24/24, `test_guardas_confianza.py`
14/14, `test_beta_dictamen.py` 17/17, `test_puerta_a.py` 31/31,
`test_agregador.py` 50/50, `test_backtest_cadena.py` 53) sigue en verde tras
el cambio de default.

**`INCERTIDUMBRE_LEGISLADOR=1` es el default en `nowcast_puertas.py` desde
este commit.** `INCERTIDUMBRE_LEGISLADOR=0` en el entorno vuelve al
comportamiento anterior sin tocar código, para quien necesite comparar.

## Lo que queda pendiente

1. **El límite del harness de estimación** (no incluye `beta_dictamen`) queda
   anotado. Si en algún momento se decide corregirlo, hay que re-estimar
   $\varepsilon_0$/$\tau$ con ese harness corregido antes de tocar los
   defaults.
2. **Backtest de CALIBRACIÓN agregada** (¿el 95% de confianza declarado
   contiene el resultado real el 95% de las veces?) sigue como el paso
   opcional de más confianza si Franco lo pide más adelante — la evidencia de
   arriba ya alcanzó para activar, pero no es lo mismo que un backtest de
   cobertura acta por acta.
