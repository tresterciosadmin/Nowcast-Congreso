# Qué se mide hoy (y qué no)

> Auditoría 2026-09, ítem A4. Escrito el 2026-09-30 desde el §9.4 de `AUDITORIA-2026-09/AUDITORIA-INTEGRAL-2026-09.md`, **con cada cifra verificada contra su archivo** (la columna «Fuente» dice cuál). Se actualiza al cerrar cada fase: **actualizado el 2026-10-01 al cerrar la fase C** (métrica de verdad, calibración declarada y brazo del guard de era) **y el 2026-10-02 con el lote de D1.0** (la ficha de desvío al día: el motor cambió y sus cifras se re-anclaron; las del 28-09 quedan entre paréntesis como «hasta D1.0») **y el 2026-10-05 con el lote de D1** (la ventana de la postura pasó de 730 a 2.190 días; las cifras de D1.0 quedan entre paréntesis como «hasta D1»). **Las cifras del motor desde D1 llevan selección sobre el panel fuera de muestra:** la ventana se eligió mirando ese panel, y el 73,6% de su mejora viene de una sola ley (la Ley Bases); ver el límite 9. La fase D cambia estas cifras ítem por ítem. Si un número de acá contradice a otro documento vivo, vale éste y se corrige el otro.

## Estado de puesta en marcha

- El número que produce el motor —la probabilidad de aprobación de un acta— es **interno**: no tiene consumidor externo, **no debe presentarse como calibrado** y no es la probabilidad de que una ley se sancione (un acta no es una ley).
- Se mide **el motor real** (`nowcast_puertas` con los defaults del código, sin banderas de entorno), con **historia estricta**: para evaluar un voto sólo existen los votos de fecha anterior y de otra ley. El motor no cambió desde `6e6b629` (ADR-0034); las etapas A1, A2 y A3 de la auditoría no movieron ningún número (0 diferencias, medido).
- Entorno de medición: Python 3.11 (CI) y 3.14 (PC de Franco), paquetes fijados en `requirements.txt` (A3).

**Etiquetas:** **MEDIDO** (motor real, historia estricta, IC re-muestreando leyes) · **CON RESERVA** (medido, con un límite que cambia su lectura) · **SIN MEDIR** · **NO USAR** (se midió y no vale).

## 1. Qué se mide, capa por capa

| capa | qué se mide | resultado | fuente / cómo se reproduce | qué **no** se mide |
|---|---|---|---|---|
| **Voto individual** ($P_i$) — **MEDIDO** (desde D1, **con selección sobre el panel OOS**) | skill = 1 − Brier / Brier de la tasa base, sobre los **692.715 votos emitidos** (afirmativo/negativo) de **3.737 leyes** (cada acta sin ley identificable cuenta como una unidad; hasta D1, 691.845 y 3.731: la ventana de 2.190 días proyecta postura en 6 actas más); IC 95% re-muestreando leyes (**2.000 réplicas** desde C1; el harness usaba 300) | **0,1527 [0,0991; 0,2080]** (hasta D1, 0,1336 [0,0624; 0,1975]; hasta D1.0, 0,1333 [0,0605; 0,1982]). Por era: 0,134 [0,074; 0,192] · 0,285 [0,197; 0,364] · 0,089 [−0,036; 0,213] · −0,006 [−0,223; 0,104] · **0,090 [−0,104; 0,273]** (era vigente: 312 leyes, 105.334 votos; hasta D1, 0,014 [−0,270; 0,264]). Diputados 0,149 [0,087; 0,212]; Senado 0,110 [0,062; 0,157]. **Casi todo viene del origen del proyecto:** el récord sin origen da 0,048 [−0,014; 0,104] (medido hasta D1) | `evaluacion/baseline/outputs/metrica_de_verdad.json` (C1: `metrica_de_verdad.py`, un solo comando, con certificado de que el motor de hoy da esas P_i; `tests/test_metrica_de_verdad.py`). Con 300 réplicas: `baseline_voto_individual.json`. Sin el detalle del censo: `censo_estadisticos_2026-10-02.json` (el motor de hoy; el del 28-09 sigue en git como continuidad con lo publicado) | presencia y ausencias; la ficha de desvío como walk-forward; las etiquetas de origen (43% desconocido, sin validar); β en el censo |
| **Recuento** (afirmativos) — **CON RESERVA** | cobertura de la banda declarada al 90%, con la simulación del motor sobre los que votaron | **63,5%** (5.858 actas de ≥ 20 votos, 63,52% [61,3; 65,5] con IC por ley; 1.000 simulaciones; una semilla; hasta D1, 63,29% en 5.852 actas; hasta D1.0, 63,64%; con la población del 27-09, 5.851 actas, 63,63%). **Por cámara en mayoría simple: Diputados 58,7% [54,8; 62,6], Senado 66,3% [63,7; 68,8]** (hasta D1, 58,5% y 66,1%; hasta D1.0, 66,8% el Senado). El recuento esperado queda **6,9 votos por debajo** del real; ancho mediano de la banda 40 votos. Sin τ: 14,8% | `evaluacion/baseline/outputs/calibracion_declarada.json` (C2: `calibracion_declarada.py`) y `modelo/ensemble/outputs/tau_limpio_2026-09-28.json` | la banda con asistencia real (aquí `p_presente = 1`) |
| **P(aprobación), mayoría simple** — **MEDIDO: peor que una constante, con IC pareado (C2)** | contra el resultado oficial del acta, por cámara | ver la tabla de abajo | `evaluacion/baseline/outputs/calibracion_declarada.json` (C2; reproduce `AUDITORIA-2026-09/resultados/simple_por_camara.txt`) | discriminación en proyectos realmente disputados *de antemano*; el efecto de la asistencia |
| **P(aprobación), mayorías especiales** — **APAGADO (A5)** | contra el resultado oficial | dos tercios (256 actas): Brier **0,3028** (una moneda da 0,25); tres cuartos (124): 0,1854 (constante 0,0808); absoluta (54): 0,1037 (constante 0,0686) | `Archivos_Borrar/auditoria/contraste_aprobacion_actas.parquet` (no viaja por git; se regenera con `AUDITORIA-2026-09/contraste_aprobacion.py`) | — **Apagadas desde el 30-09-2026 (ítem A5):** `nowcast()` con `tipo_mayoria` ≠ SIMPLE devuelve `p_aprobacion = None` y `motivo_sin_numero`, sin simular; los umbrales siguen implementados para las mediciones |
| **Proyectos con origen Senado** — **SIN MEDIR y sin publicar** | — | — | `CLAUDE.md` («Precaución vigente») | sesgo de supervivencia: la base sólo tiene los proyectos del Senado que **ya cruzaron** a Diputados (~48% contra ~1,7% de origen Diputados). No se publica P(sanción) de un proyecto con `camara_origen = senado`. La «mayoría simple en ambas cámaras» se entiende con el Senado **como cámara votante**, no como origen |
| **Términos del modelo** | ver la tabla «Términos» | | | β, δ, θ, ψ con el offset limpio (fase D) |

**P(aprobación) dentro de la mayoría simple** (resultado oficial; 5.394 actas):

| cámara | subconjunto | actas | tasa de aprobación | Brier de una **constante** | Brier del modelo | AUC | Brier recalibrado (fuera de muestra) |
|---|---|---:|---:|---:|---:|---:|---:|
| Diputados | todas | 2.543 | 0,975 | 0,0242 | 0,0357 | **0,73** | 0,0236 |
| Diputados | disputadas (≥ 10% en contra) | 1.314 | 0,953 | 0,0450 | 0,0576 | 0,65 | 0,0447 |
| Senado | todas | 2.851 | 0,985 | 0,0149 | 0,0174 | **0,60** | 0,0149 |
| Senado | disputadas | 885 | 0,953 | 0,0452 | 0,0485 | 0,56 | 0,0457 |
| **ambas** | todas | 5.394 | 0,980 | **0,0193** | **0,0260** | 0,69 | — |

*Lectura.* En mayoría simple el modelo rinde **peor que una constante** (Brier 0,0260 contra 0,0193): es subconfiado (P media 0,92 cuando la aprobación real es 0,98) y de las 106 actas rechazadas, 79 tenían P > 0,8. Recalibrado fuera de muestra queda igual a la tasa base: no hay información que rescatar con una recalibración simple. La discriminación es débil y en el Senado casi nula. El «skill 0,25» que se citaba antes **es un efecto de composición** (mezcla mayoría simple, 98% aprobada, con dos tercios y tres cuartos): el modelo acierta *qué tipo de acta es*, no el resultado dentro del tipo.

**IC pareado (C2).** Δ = Brier(modelo) − Brier(constante), re-muestreando leyes (2.000 réplicas): Diputados **+0,0115 [+0,0079; +0,0157]** (todas; con el motor de D1.0, que movió el extremo superior en 0,0001) y +0,0127 [+0,0068; +0,0189] (disputadas); Senado **+0,0026 [+0,0015; +0,0038]** y +0,0033 [+0,0004; +0,0068]; ambas +0,0068 [+0,0048; +0,0090]. **Con el motor de D1** (ventana de 2.190 días; 2.549 y 2.851 actas en mayoría simple): Diputados **+0,0116 [+0,0080; +0,0156]** (Brier 0,0357 contra 0,0241; AUC **0,75**) y disputadas +0,0126 [+0,0074; +0,0186] (AUC 0,67); Senado **+0,0025 [+0,0014; +0,0037]** (0,0173 contra 0,0149; AUC 0,59) y disputadas +0,0032 [+0,0004; +0,0067] (AUC 0,54): **sigue peor que la constante en las dos cámaras**; la tabla de arriba es la del §9.2 (censo del 28-09). **Los IC excluyen 0 del lado malo: el modelo es significativamente peor que la constante en las dos cámaras** (la constante es la tasa base de la muestra: una vara dura). Es subconfiado en todas las clases de P (P media 0,72 → aprobada el 93,5% en Diputados) y hay **19 actas del Senado con P > 0,95 que se rechazaron**.

**Términos** (cada uno con su estado; la re-estimación es la fase D, y **ninguno se archiva ni se borra**):

| término | qué dice la medición | estado |
|---|---|---|
| récord por tema (`RECORD_POR_TEMA`) | con el harness limpio **empeora** el Brier 2,12% [0,84; 3,48] (toca el 39% de los votos) → apagado. El «+11,06%» anterior era fuga | **MEDIDO** |
| encoger el récord hacia el bloque, contra cortarlo | cortar empeora el Brier 2,83% [1,81; 4,19] | **MEDIDO** |
| `MIN_HIST` 8 contra 1 | 8 empeora 0,52% [−0,01; 1,26]: no se distingue | **MEDIDO** |
| **parámetros de $P_i$ (D1, walk-forward anual contra V0, Holm m = 7; revisado a ciegas)** | k del récord D (conserva 5; MDE 1,25%) · `MIN_HIST` **C** (equivalente: conserva 1) · `MIN_VOTOS_FICHA` D (conserva 20; MDE 11,5%) · k de la postura D (conserva 5) · granularidad del origen Z (conserva las 4 clases) · guard de era Z · **ventana de la postura: F → A por decisión de Franco: 730 → 2.190 días** (−2,55% [−5,79; −0,36] de Brier fuera de muestra; el 89% de la mejora es Diputados 2024 y el 73,6% una sola ley, la Ley Bases: la ventana de 730 días miraba el hueco 2020–2023 de la base; 2.190 es el borde de la grilla). Detalle: `ESTADO-EJECUCION.md`, «D1 — veredicto» y «D1 — lote» | **MEDIDO**; la ventana, **CON RESERVA** (ver límite 9) |
| guard de era | **Decidido en D1 (2026-10-03): se conserva prendido** (el walk-forward lo eligió los 21 años: salida Z; el contraste fijo de la simplificación dio D). Con el motor de D1, quitarlo **empeora** con IC que excluye 0: **+5,7% [+0,4; +11,5]** en las actas desde 2015-12-10; era vigente +1,3% [−4,7; +6,2]; Senado desde 2015 +5,4% [+1,9; +9,6] (`guard_era_sin_corte.json`). Lo de abajo es la historia. **C3, con el motor completo** (el récord acumula desde 1900; la postura conserva su corte): en las actas desde 2015-12-10, donde el guard actúa, el ΔBrier de quitarlo es **+3,0% [−2,9; +9,7]** a favor del guard (**no se distingue de 0**); por era: 2015-2019 +9,0% [−0,7; +19,5], 2019-2023 +12,9% [−4,7; +21,1], **era vigente −3,7% [−7,7; +3,5]** (312 leyes: poco poder); Senado desde 2015 +5,0% [+1,4; +9,0] (secundario). *(La cifra anterior, +0,0028, era del control independiente y medía otro guard: cortaba también en 2011-12-10.)* Provisional, **bajo revisión de Franco** (decisión 7; **Franco decidió el 2026-10-01 resolverlo en D1**, con este brazo como insumo y la bandera prendida hasta entonces). **Re-corrido sobre el motor de D1.0** (ficha de desvío al día, 2026-10-02): primario +3,2% [−2,3; +9,7], era vigente −3,2% [−7,0; +3,4], Senado desde 2015 +4,8% [+1,2; +8,8]: la misma conclusión; fue el insumo de D1 | **MEDIDO: se conserva prendido** (D1) |
| ε₀ = 0,035 y τ = 1,19 | con el offset limpio del motor de D1 (ventana de 2.190 días): ε₀ óptimo por log-loss **0,035**, τ **1,188** (con el motor de D1.0, 0,055 y 1,201; hasta entonces, 0,055 y 1,197); se re-estiman walk-forward en D2 (en muestra; no decide). Contra resultados reales mejora el log-loss en el conjunto de todas las mayorías, pero **en mayoría simple lo empeora** (0,129 contra 0,100 del clip): la mejora la empujan las mayorías especiales | **CON RESERVA, y con evidencia en contra en el alcance que se conserva** |
| β (`F_i` 2,088; lealtad×jefe 1,750) | estimado sobre un offset con fuga; con el offset limpio da 2,05 y **1,29**; el censo no lo aplica | **SIN MEDIR** limpio |
| δ, θ, ψ | offset contaminado, sin re-medir; ψ no está implementado | **SIN MEDIR** |
| ICG | medido y **desconectado** de la fórmula (`FORMULA-COMPLETA` §II.4); `icg-mensual` sigue acumulando serie. Entra en el ítem D6 | **SIN MEDIR** dentro del número |

## 2. Cuándo «funciona» (definición numérica, a validar por Franco)

Nadie declara que el modelo funciona sin estos cinco números. **Hoy no se cumple ninguno.**

| # | condición | hoy | qué falta |
|---|---|---|---|
| 1 | skill de la era vigente con IC de **±0,10** | **±0,189** (0,090 [−0,104; 0,273], 2.000 réplicas, motor de D1, con selección sobre el panel OOS; hasta D1, 0,014 ±0,267; hasta D1.0, 0,010 ±0,274) | ~2.000 leyes en esa era, o el monitoreo hacia adelante |
| 2 | cobertura de la banda **entre 85% y 95%**, medida con asistencia real | **63,5%** en conjunto; por cámara (mayoría simple) **58,7% Diputados y 66,3% Senado**; sin asistencia real | medir la presencia (límite 2) y rehacer τ y ε₀ |
| 3 | en mayoría simple, **Brier estrictamente menor que la constante**, con IC pareado que excluya 0, en cada cámara | **peor** en las dos, **con IC pareado que excluye 0 del lado malo** (motor de D1: Dip 0,0357 contra 0,0241, Δ +0,0116 [+0,0080; +0,0156]; Sen 0,0173 contra 0,0149, Δ +0,0025 [+0,0014; +0,0037]) | fase D |
| 4 | AUC **≥ 0,75** en las actas disputadas de cada cámara | Dip 0,67 · Sen 0,54 (motor de D1; hasta D1, 0,65 y 0,56) | fase D |
| 5 | etiquetas de origen con **≥ 90%** de precisión en una muestra a mano | **sin medir** (43% desconocido) | validación con una persona (fuera de la auditoría) |

## 3. Límites conocidos

**1. Etiquetas de origen sin validar.** `origen_por_acta.parquet`: **2.582 de 5.998 actas (43,05%) son `DESCONOCIDO`**; el resto es ejecutivo (1.744), oposición (1.006), oficialismo (588) y aliados (78). Nunca se contrastaron con una muestra a mano, y es el insumo que más pesa en el skill (sin origen, 0,048). La validación se hará **más adelante y con una persona** (decisión 8; protocolo en el §9.6 d1 del informe; está en `PENDIENTES-POST-AUDITORIA.md`).

**2. La presencia no se mide.** El censo sólo evalúa votos emitidos: los ausentes no entran. La cobertura de la banda y P(aprobación) están **condicionadas a los presentes**. En producción la asistencia sí entra a la simulación.

**3. Cobertura de la base canónica por año** (medida en esta auditoría: `AUDITORIA-2026-09/cobertura_canonica.py` → `resultados/cobertura_canonica.json`). La canónica tiene **5.998 actas** y 959.815 votos individuales; **5.856 entran al censo**. Dentro de cada acta el voto individual está **completo** (257 filas en Diputados, 72 en el Senado; los votos emitidos coinciden con los que el acta declara: 0,97–1,01 en todos los años que declaran conteo). **Lo que falta son actas**, y la base es muy despareja:

| año | Diputados | Senado | año | Diputados | Senado |
|---|---:|---:|---|---:|---:|
| 1994 | 14 | **0** | 2011 | 64 | 125 |
| 1995 | **0** | **0** | 2012 | 136 | 135 |
| 1996 | **0** | **0** | 2013 | 118 | 137 |
| 1997 | 12 | **0** | 2014 | 141 | 66 ⚠ |
| 1998 | **0** | **0** | 2015 | 63 ⚠ | 84 |
| 1999 | **0** | **0** | 2016 | 190 | 195 |
| 2000 | **0** | **0** | 2017 | 156 | 102 |
| 2001 | 39 | **0** | 2018 | 105 | 81 |
| 2002 | 41 | **0** | 2019 | 96 | 46 |
| 2003 | 64 | **0** | 2020 | 7 ⚠ | 93 |
| 2004 | 207 | 395 | 2021 | 1 ⚠ | 86 |
| 2005 | 107 ⚠ | 279 | 2022 | 9 | 36 |
| 2006 | 406 | 209 | 2023 | 8 ⚠ | 26 ⚠ |
| 2007 | 227 | 181 | 2024 | 177 | 45 |
| 2008 | 132 | 221 | 2025 | 116 | 97 |
| 2009 | 128 | 175 | 2026 | 107 | 96 |
| 2010 | 61 ⚠ | 124 | | | |

⚠ = **sospechoso según la regla fijada antes de medir**: menos de la mitad de las actas de la mediana de los ±2 años vecinos de esa cámara, o cobertura individual < 90%. Ocho marcados; **la regla no prueba que falten actas** (no hay un número oficial de sesiones contra el cual comparar: algunos, como 2005, 2015 o 2023, son años electorales). **Sólo un hueco está confirmado y es grande: Diputados 2020–2023 tiene 25 actas y 6.421 votos individuales** (7 + 1 + 9 + 8), contra 96–190 actas por año en los años vecinos; el Senado, en el mismo período, tiene 93, 86, 36 y 26. Además: **el Senado no tiene ninguna acta antes de 2004** y Diputados no tiene 1995, 1996, 1998, 1999 ni 2000 (1994 y 1997 casi vacíos). Consecuencia para el modelo: la era 2019–2023 se evalúa con 246 leyes y 25.755 votos, y el récord de cada legislador en esos años se apoya en muy pocas actas. Investigar y rellenar el hueco **no** es de la auditoría (`PENDIENTES-POST-AUDITORIA.md`).
De las 142 actas de la canónica que no entran al censo: 54 no tienen votos individuales, 32 no tienen fecha válida, 5 sólo tienen abstenciones o ausentes, y **51 tienen afirmativos y negativos sin que se haya auditado por qué quedan afuera**.

**4. Un acta no es una ley; el 15,3% de los votos no tiene ley identificable.** El censo agrupa actas en leyes (`ley_por_acta`) para no usar como historia lo que pasó en la misma ley; para el 15,3% de los votos no se conoce la ley y ahí el corte por expediente no ve nada. Al excluir esos votos (585.822 votos, 2.944 leyes) el skill sube a **0,166 [0,084; 0,252]**: no hay sesgo al alza. *(Medido con los estadísticos versionados y el mismo bootstrap del harness; el informe cita [0,076; 0,242], de otro bootstrap.)*

**5. La ficha de desvío individual: point-in-time desde el 2026-10-02 (D1.0).** Hasta entonces `disciplina_individual.csv` se calculaba con **toda la historia** (un nowcast fechado en el pasado veía el futuro) y el censo usaba el desvío del linaje en su lugar. Desde D1.0 (decisión de Franco) el motor y el censo usan la **ficha al día** (`disciplina.FichaAlDia`: la misma regla, sólo con los votos anteriores a la fecha y, en el censo, sin la misma ley); actúa en la rama de bloque (4,67% de los votos) y en la lealtad de β. Efecto en el censo, fuera de muestra (Diputados desde 2006, Senado desde 2007): global −0,08% de Brier [−0,37; +0,11] (no se distingue); en la rama de bloque −0,79% [−1,63; +2,89], pero en la del **Senado empeora +5,4% [+2,8; +9,0]** (IC por ley y por mes): la ficha individual predice peor que el desvío del linaje para los senadores sin récord en la era (`AUDITORIA-2026-09/resultados/ficha_al_dia_D1_0.json`). El CSV sigue existiendo como la ficha de hoy para los consumidores fuera del motor.

**6. Intervalos.** El IC del skill usa 2.000 réplicas de un bootstrap sobre leyes (error de Monte Carlo de los extremos ≈ 0,002; con las 300 del harness la era vigente daba ±0,255 y con 2.000, ±0,274; con el motor de D1.0, ±0,267) y un único corte de historia. El del skill de la era vigente es ancho (±0,267). La cobertura de la banda trae IC por ley (C2) pero usa una semilla y 1.000 simulaciones por acta; el AUC no trae IC.

**7. Estimadores con offset contaminado.** β, δ, θ y ψ se estimaron sobre un récord con fuga (`shift(1)` por fila, sin guard, sin encoger, sin origen). Se **corrigen y re-estiman** en la fase D; hasta entonces no se los cita como medición.

**8. Lo que las pruebas de reproducibilidad no cubren** (A2 y A3). Los estadísticos por acta que viajan por git alcanzan para recalcular skill, IC, τ y ε₀ **sobre la grilla de ε₀ de 0,005 y con Brier/log-loss**; cualquier otra cosa (la cobertura de la banda, tablas por fuente, otra pérdida) exige regenerar el censo (43 min). La igualdad entre Python 3.11 y 3.14 se midió en Windows; el CI es Linux y ahí sólo se sabe que la suite pasa.

**9. La ventana de la postura (D1) se eligió con selección sobre el panel y descansa en una ley.** La ventana de 2.190 días la eligió el walk-forward de D1 mirando el panel fuera de muestra, y Franco aceptó el mecanismo contra la recomendación de los dos agentes: el 89% de la mejora es Diputados 2024 y el 73,6% la Ley Bases (con 730 días la postura de esas actas salía de las 17 actas del hueco 2020–2023; con 2.190, de 225); sin esa ley la mejora es −0,73% y en 2025–2026 la ventana larga empeora +0,46% [+0,28; +0,66]. **La réplica independiente (el control de B3) cubre ≈ 0,135 del skill; los +0,018 que agrega D1 sólo los respaldan B2 sobre el brazo y el control «censo nuevo = brazo 2.190»** (max|Δp| = 0): nada los reimplementa por separado. Por eso el skill de hoy (0,1527) se rotula «con selección sobre el panel OOS» y la ventana se re-mide cuando se rellene el hueco de Diputados 2020–2023.

## 4. Cifras que ya no se deben citar

| cifra | por qué no |
|---|---|
| skill **0,1611** (el «publicado» hasta el 28-09) | inflado por fuga: `shift(1)` por fila, misma ley y mismo día |
| skill **0,25** de P(aprobación) | efecto de composición del conjunto de mayorías (ver arriba) |
| banda **99,88%** (ADR-0025) | medía con un oráculo: le daba a la simulación la línea que cada bloque tuvo *en esa acta* |
| récord por tema **+11,06%** | misma fuga; el número limpio es el de la tabla de términos |
| cobertura de la banda **90%** declarada | la medida es 63,6% |

## 5. Cómo se reproduce

```
python -m pytest tests/ datos/proyectos/tests -q                          # la suite (CI)
python evaluacion/baseline/src/censo_estadisticos.py                      # el JSON de estadísticos, desde el detalle del censo
python evaluacion/baseline/src/calibracion_declarada.py                  # la calibración declarada (C2): tabla del §9.2 con IC pareado del Brier contra la constante y cobertura de la banda, por cámara; con --simular regenera el JSON por acta (PC, 6 min)
python evaluacion/baseline/src/metrica_de_verdad.py                       # la métrica de verdad (C1): skill por era y cámara, IC por ley con 2.000 réplicas, ΔBrier pareado; escribe outputs/metrica_de_verdad.json y no pisa nada. Con --verificar-motor 60 certifica (en la PC) que el motor de hoy da esas P_i
python modelo/ensemble/src/estimar_epsilon_tau.py --columna estricta__general   # ε₀ y τ del motor de hoy (sin el parquet)
python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 --origen EJECUTIVO --json salida.json
python coordinacion/AUDITORIA-2026-09/cobertura_canonica.py               # la tabla del límite 3
python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 7     # regenerar el censo (43 min)
```
