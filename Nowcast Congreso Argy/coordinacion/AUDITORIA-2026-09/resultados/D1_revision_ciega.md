# D1 — veredicto del revisor ciego (regla 6, §11 del protocolo)

**Revisor:** subagente Opus, sin ver el veredicto del primer agente. **Fecha:** 2026-10-03. **Insumo:** el paquete `revision_ciega\` y, para auditar, el código del runner, el harness y `bloque.proyectar_postura` en `e869db1`.

**Recómputo propio.** Rehice desde las tablas por acta del JSON, con código propio (sin importar el runner ni llamar `veredicto/arbol/holm`): selección anual (entrenamiento = actas < 1-ene-Y sin las leyes con actas de test en Y; empate → V0), compuesto WF, Δ, IC por ley y por mes (Poisson, 2.000 réplicas, semilla 7, `default_rng`), p, p*, global OOS y subgrupos. **Coincide al cuarto decimal con todo lo que trae el JSON** en los siete parámetros (trayectorias, valor WF final, Δ, IC, p).

## 1. Salidas por parámetro (árbol del punto 6, en orden Z → F → C → E → A/B → D)

Holm (m = 7, α = 0,05) sobre p* = máx(p_ley; p_mes), Z con p* = 1:

| orden | parámetro | p* | umbral α/(m−i) | rechaza |
|---|---|---:|---:|---|
| 1 | ventana de la postura | 0,0020 | 0,00714 | **sí** |
| 2 | k de la postura | 0,1209 | 0,00833 | no (se corta acá) |
| 3 | k del récord | 0,2789 | 0,0100 | no |
| 4 | `MIN_VOTOS_FICHA` | 0,7406 | 0,0125 | no |
| 5 | `MIN_HIST` | 0,9115 | 0,0167 | no |
| 6–7 | origen, guard (Z) | 1 | — | no |

| # | parámetro (V0) | trayectoria WF · valor WF final | global OOS (umbral F) | primario: Δ, IC ley · IC mes | salida | acción (hiperparámetro) |
|---|---|---|---|---|---|---|
| 1 | k del récord (5) | 10, 20, 40×4 (2008–11), 20×15 · **40** (tocó el borde 40 → extensión 80, nunca elegido) | −0,44% (2%) → no F | −0,50% [−1,18; +0,23] · [−1,35; +0,40]; p* 0,279 | **D** (IC sale del margen por abajo e incluye 0; Holm no rechaza) | conservar 5; MDE 1,25% |
| 2 | `MIN_HIST` (1) | 2 salvo 2019–2020 (1) · **2** | +0,005% (2%) → no F | +0,03% [−0,32; +0,40] · [−0,42; +0,47]; p* 0,912 | **C** (los dos IC dentro de ±1%) | conservar 1 |
| 3 | `MIN_VOTOS_FICHA` (20) | 5 todos los años · **5** (tocó el borde 5 → extensión 2, nunca elegido) | +0,02% (2%) → no F | +0,38% [−1,18; +11,27] · [−1,24; +10,44]; p* 0,741 | **D** | conservar 20; **MDE 11,5%** (sin poder). Nota: en el Senado el WF daña +21,5% [9,6; 46,5] por ley (no veta: Holm no rechaza) |
| 4 | k de la postura (5) | 40×11 (2006–16), 2,5×4, 10×4, 5×2 · **10** (tocó 20 → extensión 40, **vuelve a tocar el borde**: se dice, no se extiende) | +0,50% (2%) → no F | +0,90% [−0,08; +2,31] · [−0,10; +2,28]; p* 0,121 | **D** | conservar 5; MDE 1,82% |
| 5 | ventana de la postura (730) | 2.190 todos los años · **2.190** (la grilla base tocó los dos bordes: 365 en 2006–11, 1.460 en 2012–20; extensión 182 y 2.190; **2.190 vuelve a tocar el borde**: se dice, no se extiende) | **−2,55% (umbral 2% = máx(2%; 2×1%)) → F** | −2,55% [−5,79; −0,36] · [−5,56; −0,38]; p* 0,0020 | **F (alarma)** → ver §2. Invariancia (B2 sobre el brazo 2.190): cumple. Mecanismo: sin fuga, pero artefacto del hueco de Diputados 2020–2023 (73,6% de ΣΔ en una ley) → **no pasa**; si Franco lo acepta, el árbol da A | en suspenso: no se cambia; va a Franco con las mediciones de §2 (recomendación: conservar 730) |
| 6 | granularidad del origen (fino) | fino todos los años · fino | 0 | idéntico a V0 en el panel | **Z** | conservar fino |
| 7 | guard de era (prendido) | prendido todos los años · prendido | 0 | idéntico a V0 en el panel | **Z** → «se conserva prendido» | conservar prendido |

**Guard, contraste fijo «sin corte contra con corte» (informativo, la simplificación):** +3,23% [−2,33; +9,72] por ley · [−1,98; +9,39] por mes (1.055 leyes, 116.777 votos del panel, denominador = los 257.543 votos desde 2015-12-10) → los IC salen de ±1% e incluyen 0 → **D: no se le ofrece a Franco quitar el guard.** Con Z en el WF, el guard sigue prendido sin reabrir la discusión.

**Regla por término:** cada parámetro tiene un solo contraste; no hay A y B cruzados. **Confirmación conjunta:** no corresponde (a lo sumo un contraste —ventana— podría terminar en A).

**Si Franco diera por bueno el mecanismo de la ventana** (§2), el árbol seguiría desde el paso 2: C no (IC hasta −5,8%); E no (Holm rechaza, los dos IC excluyen 0 del lado bueno, la acción es un cambio —730 → 2.190— pero ninguno de los subgrupos pre-registrados se daña: era vigente −7,74% [−14,59; −0,41], Diputados −2,88% [−6,73; −0,28], Senado −0,72% [−1,16; −0,34], todos por ley) → **A: recalibrar a 2.190**, un valor de borde. Y sería el único A: sin confirmación conjunta.

## 2. La alarma F de la ventana de la postura

### (a) Qué invariancia corresponde y si se cumple

El punto 7 pide la invariancia por insumo «para cada brazo que **agrega** un insumo» (firmas, carácter, ICG, ψ). La ventana no agrega ninguno: cambia cuánta historia de **votos** mira `proyectar_postura`; los demás insumos de la postura (padrón vigente a la fecha, `cond_por_acta` con `origen`/`origen_lado`/`gobierno`) no dependen de la ventana. Para este brazo la invariancia que corresponde es **B2 sobre el brazo** (la de los votos), que el pre-registro (tabla del punto 3) ya exige. **Se cumple:** `extensiones.log.b2.txt`, brazo `{"ventana_postura": 2190}`: 13/13; historia estricta, 25 actas (5 estratificadas + 3 con otras actas el mismo día + 8 con acta anterior de su ley + 3 primeras de un recambio + 3 con la ley en la ficha), 3.395 P_i, **max|dP| = 0**; anti-vacuidad: 3 actas sumadas por regla fija y **3.127 P_i de la muestra distintas del motor** (el brazo actúa donde se prueba); controles positivos detectados: fecha 3/3 (0,09), misma ley 4/8 (sensibilidad 48%, la misma en todos los brazos), ficha 3/3, ficha sin la ley 3/3. El 182 también pasa (3.246 distintas). Además, el código confirma que la ventana sólo corta `fecha < acta` y `fecha ≥ acta − ventana` y que con historia estricta excluye la misma ley (`Contexto.postura` → `_sin_ley`). **(a) cumple.**

### (b) El mecanismo: sin fuga, pero es un artefacto del hueco de Diputados 2020–2023 concentrado en una ley

1. **Concentración.** ΣΔ (2.190 − 730) en el panel = −2.061 (sobre ΣBrier V0 = 80.791). **Una sola ley aporta el 73,6%**: `ley:argentinadatos:diputados:5101` (50 actas del 2024-02-02, 02-06, 04-30 y 06-28 — la «Ley Bases»), 12.186 votos, Brier medio por voto **0,474 con 730 → 0,350 con 2.190**. Las 5 leyes de mayor |Δ|: 79,9%; **las 10: 83,9%; las 20: 90,0%**; las 50: 95,6%. Leyes que mejoran 1.540, que empeoran 1.423. Sin las 10 mayores, Δ = −0,48%; sin las 20, −0,31%.
2. **Por año y cámara.** Diputados 2024 = **88,9% de ΣΔ** (−15,3% relativo en ese año). Diputados 2025 −0,17%, 2026 **+0,85%**; Senado 2025 +0,74%, 2026 +0,68%. Fuera de 2024 los años van y vienen (Dip 2017 −2,0%, 2019 +2,1%; Sen 2019 −17,3% sobre 152 de Brier, 2020 −6,1%).
3. **Por qué: el hueco de la base, a través de los dos cortes por era del motor** (verificado en los parquets de V0 y del brazo 2.190, sólo las 12.186 filas de la ley 5101). Antes del 2024-02-02, la ventana de Diputados contiene (tabla de la ventana, que es la intersección con el brazo 182): 365 días → 9 actas; 548 → 16; **730 → 17; 1.095 → 18; 1.460 → 20; 2.190 → 225** (105 de 2018 y 96 de 2019). En el censo de V0 Diputados tiene **7, 1, 9 y 8 actas en 2020–2023 = 25**, las del protocolo (la tabla de la ventana muestra 23 porque pierde 3 leyes en la intersección). La cadena:
   - **Corte del récord (el guard de era):** el récord individual acumula sólo desde 2023-12-10, así que en la Ley Bases **el 98% de los votos va a la rama de bloque** (`n_prev` ≥ 1 en el 2%) y la P_i sale del share y el desvío del linaje que da la postura. El récord es idéntico en los dos brazos.
   - **Corte dentro de la postura** (`_match_origen`: al condicionar por origen, sólo actas del mismo gobierno; y la historia estricta saca la misma ley): el origen de las 50 actas es **EJECUTIVO**; antes de cada fecha había en Diputados 1 acta del gobierno nuevo (0 del Ejecutivo) el 02-02, 2 (1) el 02-06, 16 (14) el 04-30 y 76 (58) el 06-28 — y las del 02-06 son de la propia ley 5101, que la historia estricta excluye. Así que la condicionada cae a la incondicional o queda dominada por ella (encogimiento con k = 5).
   - **La incondicional** sale de toda la ventana: con 730/1.460 días, de ~17–20 actas del gobierno anterior; con 2.190, sobre todo de 2018–2019. El share cambia en 9.849 de los 12.186 votos (media 0,80 con 730 → 0,76 con 2.190; la tasa real de afirmativos fue 0,54); P_i media 0,763 → 0,722; Brier 0,474 → 0,350.
   
   2.190 es **la primera ventana de la grilla que cruza el hueco**: por eso el escalón está ahí y no antes.
4. **La curva no es monótona.** Δ OOS contra 730, en el panel: 182 +0,76% · 365 **+3,40%** · 548 +0,75% · 730 0 · 1.095 −0,04% · 1.460 +0,08% · **2.190 −2,55%**. Plana de 548 a 1.460 y un escalón en 2.190; 365 es la peor y 182 mejor que 365 (en Diputados ≥ 2024, 365 da +12,2%: con 9 actas en la ventana). En entrenamiento la grilla base eligió **los dos bordes** según la época (365 en 2006–11, 1.460 en 2012–20, 1.095 en 2021–26), y con la extensión eligió 2.190 todos los años con márgenes de −0,35% a −0,82% (hasta 2024) y −2,5/−2,65% en 2025–2026, cuando el entrenamiento ya incluye la Ley Bases. Sin la ley 5101 la curva sigue sin ser monótona (182 +2,09%, 365 +0,87%, 548 +0,78%, 1.095 −0,07%, 1.460 +0,12%, 2.190 −0,73%).
5. **Vuelve a tocar el borde.** 2.190 se elige los 21 años y es el valor de la extensión: el protocolo manda decirlo y no extender más. El óptimo de entrenamiento podría estar más allá; el valor «a adoptar» es un borde.
6. **Sensibilidad (descriptiva, bootstrap del punto 5):**

| subconjunto del panel | votos | Δ | IC por ley | IC por mes |
|---|---:|---:|---|---|
| primario | 575.134 | −2,55% | [−5,79; −0,36] | [−5,56; −0,38] |
| sin la ley 5101 | 562.948 | −0,73% | [−1,22; −0,21] | [−1,55; −0,08] |
| sin Diputados 2024 | 535.741 | −0,33% | [−0,67; +0,09] | [−0,84; +0,17] |
| 2006–2019 | 451.559 | −0,43% | [−0,84; +0,08] | [−1,01; +0,15] |
| era vigente sin la ley 5101 | 92.674 | −1,54% | [−3,09; −0,14] | [−4,81; +0,29] |
| **2025–2026** | 63.306 | **+0,46%** | **[+0,28; +0,66]** | **[+0,02; +0,96]** |
| Diputados 2025–2026 | 50.643 | +0,40% | [+0,22; +0,57] | [−0,08; +0,91] |
| Senado 2025–2026 | 12.663 | +0,72% | [+0,17; +1,52] | [−0,03; +1,53] |

**Dictamen del mecanismo.** No hay fuga: B2 pasa con anti-vacuidad, el corte es estricto por fecha y por ley, y la mejora se explica sin mirar el futuro. Pero **lo que dispara la alarma no es una mejora del parámetro: es la ventana larga tapando un hueco de la base**, en una sola ley de un año de recambio. El sostén del dictamen son tres hechos que no dependen de elegir subconjuntos después de mirar: (1) la **concentración** (73,6% de ΣΔ en una ley, 90% en 20); (2) el **escalón exactamente donde la ventana cruza el hueco** (730 → 17 actas, 1.460 → 20, 2.190 → 225; la curva es plana de 548 a 1.460); (3) el valor elegido es **otra vez un borde**.

**El límite 5 del protocolo** («los años 2020–2023 de Diputados tienen 25 actas… Se dice; no se corrige») manda no corregir el hueco en el reajuste anual; **no convierte en mejora legítima del parámetro una ganancia que viene del hueco**. Por eso este dictamen no va contra el árbol: es la revisión del mecanismo que el paso 1 exige justamente antes de seguirlo.

**La parte generalizable existe y es chica:** en entrenamiento, antes de 2024, 2.190 ya le ganaba a 730 entre −0,35% y −0,82% todos los años, y fuera de la ley 5101 y de Diputados 2024 el Δ OOS es −0,33% a −0,73% (2006–2019: −0,43% [−0,84; +0,08]): del orden de −0,4%, **dentro del margen de equivalencia**. **Corroboración (post hoc, no es la base del dictamen):** en 2025–2026 la ventana de 2.190 días todavía abarca el hueco, pero la de 730 ya no está desabastecida (ve 2023-2026, con datos densos desde 2024), y ahí 2.190 empeora: +0,46% [+0,28; +0,66] por ley · [+0,02; +0,96] por mes. El subconjunto 2025–2026 **no** está pre-registrado como subgrupo de veto: no dispara E.

**Conclusión:** **el mecanismo no pasa como «mejora generalizable»**; el contraste queda en **F (en suspenso)** y va a Franco con dos lecturas: (i) si acepta el mecanismo, el árbol da **A (2.190, borde)**; (ii) mi recomendación: **conservar 730** y anotar en el estacionamiento que la ventana se re-mide cuando se rellene el hueco de Diputados 2020–2023, porque la ganancia depende de ese hueco.

## 3. Auditoría de controles

Contra la tabla del punto 3 del pre-registro y el punto 7 del protocolo.

| control | brazos de censo (k postura 1/2,5/10/20/**40**; ventana 365/548/1.095/1.460/**182/2.190**; origen lado) | sin censo (k récord, `MIN_HIST`, `MIN_VOTOS_FICHA`) y guard | estado |
|---|---|---|---|
| rama por defecto = motor | `verificar_motor` 60 actas: 7.298 votos, max\|ΔP\| = 0 (`d1_controles_brazos.json`); `test_harness_es_el_motor` 16/16 y B2 sin brazo 12/12 sólo citados en «avance» | — | ✔ (lo citado no lo pude ver crudo) |
| control positivo V0 explícito | 0 distintos en 7.298 votos, y por año 0 distintos | recomposición (5; 1; 20): max\|Δp\| = 0 en 691.845 votos (`control_positivo_max_abs_dp` = 0 en la matriz de los tres) | ✔ |
| el recálculo representa al motor | — | `K_SHRINK_RECORD` 20, `MIN_HIST` 8, `MIN_VOTOS_FICHA` 80: 0 distintos; mueven 6.406, 1.779 y 26 (de bloque) P_i | ✔ (los valores de extensión 80 y 2 no se probaron por harness: mismo camino de código; MENOR) |
| donde no puede actuar | k postura (incl. 40): 0 con origen desconocido, récord/`n_prev` 0, ficha6 0, desvío del linaje 0. Ventana (incl. 182 y 2.190): récord/`n_prev` 0, ficha6 0; el desvío del linaje cambia, como se previó. Origen lado: 0 con desconocido, 0 con OPOSICION, ficha6 0, linaje 0 | k récord 0 fuera de la rama; `MIN_HIST` 0 con `n_prev` ≥ valor o en bloque (incl. 32); `MIN_VOTOS_FICHA` 0 en la rama del récord (incl. 2 y 160); guard 0 antes de 2015-12-10 | ✔ |
| el piso del censo no se mueve con la ventana (punto 4) | `VENTANA_DIAS = 730` es una constante del harness (línea 74) que sólo usa el piso del censo (línea 786); el brazo pasa la ventana únicamente a `proyectar_postura(ventana_dias=…)` (líneas 666–669). Los votos que agregan 1.095/1.460/2.190 son actas que V0 salta porque su postura de 730 días no tiene historia, no un piso movido | — | ✔ |
| mismo conjunto de votos | k postura e origen: 691.845, mismos pares; ventana: 182 pierde 639 votos (12 leyes), 365 pierde 238 (2), 1.095/1.460/2.190 agregan 276/868/870 (no se interpretan); **intersección 691.206, caen 3 leyes enteras**; `y_identico` = true en todos los brazos | idéntico por construcción; guard 691.845 | ✔ |
| B2 sobre el brazo | los nueve de la grilla 13/13 (según «avance»); **los tres de extensión 13/13 en el log crudo** | declarado: columnas de V0 ya pasaron B2 en D1.0; guard en D1.0 | ✔ (los nueve de la grilla y el guard, sólo citados) |
| anti-vacuidad | 60 actas: k 10 → 4.650, ventana 365 → 6.363, lado → 2.419 distintas; B2: 3 actas sumadas por regla fija y P_i distintas (k 40: 1.640; 182: 3.246; 2.190: 3.127) | `MIN_VOTOS_FICHA` 80 mueve 26 P_i de bloque en las 60 | ✔ |

**Severidad, en una línea: no hay BLOQUEANTE de controles ni del runner. Pero la F de la ventana bloquea el lote de D1 hasta que decida Franco** (no es un defecto: es el protocolo funcionando; mientras esté en suspenso no hay nada que adoptar en D1, porque los otros seis conservan V0).

**Hallazgos**

| # | severidad | hallazgo |
|---|---|---|
| 1 | **IMPORTANTE — frena el lote** | **La F de la ventana es un artefacto del hueco de la base, no una fuga** (§2): 73,6% de ΣΔ en la Ley Bases; 88,9% en Diputados 2024; escalón justo donde la ventana cruza el hueco; el valor vuelve a tocar el borde. No se libera la F hacia A sin la decisión de Franco: **sin lote de D1 hasta entonces**. Si el primer agente dio A a la ventana, **difiere de este revisor y, por el §11, no se aplica nada.** |
| 2 | IMPORTANTE | **El árbol del runner no tiene salida después de F:** `arbol()` devuelve F y nada recorre el árbol desde el paso 2 cuando el mecanismo pasa; tampoco hay un campo para el resultado de la revisión. Lo hice a mano (§1). No cambia ninguna salida de hoy, pero el test del CI que «recalcula el veredicto» va a anclar F, no la salida final. |
| 3 | MENOR | **Paneles distintos de los pre-registrados, legítimos.** `MIN_VOTOS_FICHA`: 13.562 votos · 395 leyes (pre-registro: 10.246 base; 16.630 con las dos extensiones) — la grilla final lleva sólo la extensión de abajo (2), porque sólo tocó ese borde, y el panel se fija «con la grilla final» (pre-registro 2.3 c). Ventana: 575.134 · 2.963 (avance: 569.195 · 2.966) — grilla final con 182 y 2.190 e intersección con el brazo 182 (punto 4). k postura: 365.006 (364.726 + el brazo 40). k récord: igual con 80. El global OOS de la ventana es sobre la intersección (575.638 votos, no 576.270): correcto por el punto 4. |
| 4 | MENOR | k de la postura **vuelve a tocar el borde** (40 elegido en 2006–2016) y la ventana también (2.190 los 21 años): declarado en el JSON (`vuelve_a_tocar`), sin extender, como manda el protocolo. En k de la postura la salida (D) no depende de eso. |
| 5 | MENOR | Los nueve B2 de la grilla, `test_harness_es_el_motor` y B2 sin brazo están en el paquete sólo como cifras del «avance», no como salida cruda; los tres de extensión sí están crudos. El control positivo «misma ley» de B2 detecta 4/8 (48%): es la sensibilidad conocida de la prueba, igual en todos los brazos. |
| 6 | MENOR | El log de B2 muestra `NativeCommandError` de PowerShell: es el stderr del aviso `bloque: descarté 3072/959815 filas…` envuelto por PowerShell 5.1, con exit = 0 y «13/13 OK». No es una falla. |
| 7 | MENOR (informativo) | `MIN_VOTOS_FICHA` = 5 (lo que elige el WF todos los años) daña al Senado +21,5% [9,6; 46,5] por ley: no decide (Holm no rechaza, D), pero confirma que el umbral bajo sería malo en el Senado, como anticipaba el pre-registro. |

**Errores del runner que cambien un veredicto:** no encontré. Revisé `seleccion_anual` (entrenamiento, exclusión de leyes de test, empate → V0), `toca_borde`/extensión (una vez por lado, `vuelve_a_tocar`), `boot` (Poisson sobre grupos, semilla 7, p con la fórmula del protocolo), `contraste` (agrupamiento por ley y por mes, Δ relativo pareado), `compuesto` (sólo actas OOS), el global OOS (denominador `e0_todos` de las actas OOS), el umbral F por parámetro (2/2/2/2/2/3/3 = máx(2%; 2 × lo esperado) del pre-registro), Holm (step-down, m = 7, Z con p* = 1), el veto E (sólo si Holm rechaza, lado bueno y la acción cambia; IC por ley de era vigente y de cada cámara, dentro del panel) y el contraste fijo del guard (denominador = todos los votos de las actas OOS desde 2015-12-10, como C3). Mi recómputo independiente coincide con el JSON en todo.

## 4. Archivos que leí

Del paquete (`scratchpad\revision_ciega\`): `protocolo_y_preregistro_D1.md` (entero), `d1_parametros_pi_SIN_VEREDICTO.json` (con Python: `resultados` y `estadisticos_por_acta`), `d1_controles_brazos.json`, `d1_panel_primario.json`, `extensiones.log`, `extensiones.log.b2.txt`.

Del repo (sólo para auditar): `evaluacion/baseline/src/medir_d1_parametros_pi.py` (líneas 40–169 y 290–765, que incluyen el código de `arbol`, `veredicto` y `holm` —leído para auditar, no ejecutado—), `evaluacion/baseline/src/baseline_voto_individual.py` (líneas 620–699 y `grep` de `era_desde`/`ventana`/`k_postura`/`VENTANA_DIAS`), `variables/bloque/src/bloque.py` (líneas 368–383 y 480–760, `proyectar_postura`). Lecturas filtradas (pocas columnas, sólo la ley 5101 y los `acta_id`/fecha/origen de Diputados) de `evaluacion/baseline/outputs/censo_detalle_2026-10-02.parquet` y `censo_detalle_d1_ventana_postura-2190_sobre_2026-10-02.parquet`. `git log --oneline -3` (HEAD = `e869db1`). El `CLAUDE.md` del repo se cargó solo al abrir el código.

Mis scripts y salidas intermedias: `scratchpad\revisor_trabajo\` (`cargar.py`, `recomputar.py`, `ventana.py`–`ventana4.py`, `tabs.pkl`, `res.pkl`). No abrí nada más del scratchpad, ni `outputs/d1_parametros_pi.json`, ni `ESTADO-EJECUCION.md`, ni historial posterior a `e869db1`. No corrí el runner ni modifiqué nada del repo.
