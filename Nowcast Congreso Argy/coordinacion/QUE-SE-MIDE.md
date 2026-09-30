# Qué se mide hoy (y qué no)

> Auditoría 2026-09, ítem A4. Escrito el 2026-09-30 desde el §9.4 de `AUDITORIA-2026-09/AUDITORIA-INTEGRAL-2026-09.md`, **con cada cifra verificada contra su archivo** (la columna «Fuente» dice cuál). Se actualiza al cerrar cada fase: las fases C y D cambian estas cifras. Si un número de acá contradice a otro documento vivo, vale éste y se corrige el otro.

## Estado de puesta en marcha

- El número que produce el motor —la probabilidad de aprobación de un acta— es **interno**: no tiene consumidor externo, **no debe presentarse como calibrado** y no es la probabilidad de que una ley se sancione (un acta no es una ley).
- Se mide **el motor real** (`nowcast_puertas` con los defaults del código, sin banderas de entorno), con **historia estricta**: para evaluar un voto sólo existen los votos de fecha anterior y de otra ley. El motor no cambió desde `6e6b629` (ADR-0034); las etapas A1, A2 y A3 de la auditoría no movieron ningún número (0 diferencias, medido).
- Entorno de medición: Python 3.11 (CI) y 3.14 (PC de Franco), paquetes fijados en `requirements.txt` (A3).

**Etiquetas:** **MEDIDO** (motor real, historia estricta, IC re-muestreando leyes) · **CON RESERVA** (medido, con un límite que cambia su lectura) · **SIN MEDIR** · **NO USAR** (se midió y no vale).

## 1. Qué se mide, capa por capa

| capa | qué se mide | resultado | fuente / cómo se reproduce | qué **no** se mide |
|---|---|---|---|---|
| **Voto individual** ($P_i$) — **MEDIDO** | skill = 1 − Brier / Brier de la tasa base, sobre los **691.845 votos emitidos** (afirmativo/negativo) de **3.731 leyes** (cada acta sin ley identificable cuenta como una unidad); IC 95% re-muestreando leyes (300 réplicas) | **0,1333 [0,0574; 0,1979]**. Por era: 0,133 [0,071; 0,190] · 0,277 [0,190; 0,352] · 0,081 [−0,044; 0,197] · 0,011 [−0,203; 0,106] · **0,010 [−0,264; 0,246]** (era vigente: 312 leyes, 105.334 votos). Diputados 0,126 [0,051; 0,196]; Senado 0,108 [0,058; 0,150]. **Casi todo viene del origen del proyecto:** el récord sin origen da 0,048 [−0,014; 0,104] | `evaluacion/baseline/outputs/baseline_voto_individual.json`. Sin el detalle de 37 MB: `censo_estadisticos_2026-09-28.json` (A2) y `tests/test_censo_estadisticos.py` | presencia y ausencias; la ficha de desvío como walk-forward; las etiquetas de origen (43% desconocido, sin validar); β en el censo |
| **Recuento** (afirmativos) — **CON RESERVA** | cobertura de la banda declarada al 90%, con la simulación del motor sobre los que votaron | **63,6%** (5.851 actas de ≥ 20 votos; 1.000 simulaciones; una semilla; sin IC). El recuento esperado queda **6,9 votos por debajo** del real; ancho mediano de la banda 40 votos. Sin τ: 14,8% | `modelo/ensemble/outputs/tau_limpio_2026-09-28.json` | la banda con asistencia real (aquí `p_presente = 1`) |
| **P(aprobación), mayoría simple** — **CON RESERVA: peor que la tasa base** | contra el resultado oficial del acta, por cámara | ver la tabla de abajo | `AUDITORIA-2026-09/resultados/simple_por_camara.txt` | discriminación en proyectos realmente disputados *de antemano*; el efecto de la asistencia |
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

**Términos** (cada uno con su estado; la re-estimación es la fase D, y **ninguno se archiva ni se borra**):

| término | qué dice la medición | estado |
|---|---|---|
| récord por tema (`RECORD_POR_TEMA`) | con el harness limpio **empeora** el Brier 2,12% [0,84; 3,48] (toca el 39% de los votos) → apagado. El «+11,06%» anterior era fuga | **MEDIDO** |
| encoger el récord hacia el bloque, contra cortarlo | cortar empeora el Brier 2,83% [1,81; 4,19] | **MEDIDO** |
| `MIN_HIST` 8 contra 1 | 8 empeora 0,52% [−0,01; 1,26]: no se distingue | **MEDIDO** |
| guard de era | quitar sólo el corte por era: +0,0028 de Brier a favor del guard [−0,0006; +0,0066] (≈ 2%, incluye 0); **en la era vigente −0,0003 [−0,012; +0,010]: no hace nada**. Provisional, **bajo revisión de Franco** (decisión 7) | **CON RESERVA** |
| ε₀ = 0,035 y τ = 1,19 | con el offset limpio: ε₀ óptimo **0,055**, τ 1,197. Contra resultados reales mejora el log-loss en el conjunto de todas las mayorías, pero **en mayoría simple lo empeora** (0,129 contra 0,100 del clip): la mejora la empujan las mayorías especiales | **CON RESERVA, y con evidencia en contra en el alcance que se conserva** |
| β (`F_i` 2,088; lealtad×jefe 1,750) | estimado sobre un offset con fuga; con el offset limpio da 2,05 y **1,29**; el censo no lo aplica | **SIN MEDIR** limpio |
| δ, θ, ψ | offset contaminado, sin re-medir; ψ no está implementado | **SIN MEDIR** |
| ICG | medido y **desconectado** de la fórmula (`FORMULA-COMPLETA` §II.4); `icg-mensual` sigue acumulando serie. Entra en el ítem D6 | **SIN MEDIR** dentro del número |

## 2. Cuándo «funciona» (definición numérica, a validar por Franco)

Nadie declara que el modelo funciona sin estos cinco números. **Hoy no se cumple ninguno.**

| # | condición | hoy | qué falta |
|---|---|---|---|
| 1 | skill de la era vigente con IC de **±0,10** | **±0,255** (0,010 [−0,264; 0,246]) | ~2.000 leyes en esa era, o el monitoreo hacia adelante |
| 2 | cobertura de la banda **entre 85% y 95%**, medida con asistencia real | **63,6%** y sin asistencia real | medir la presencia (límite 2) y rehacer τ y ε₀ |
| 3 | en mayoría simple, **Brier estrictamente menor que la constante**, con IC pareado que excluya 0, en cada cámara | **peor** en las dos (Dip 0,0357 contra 0,0242; Sen 0,0174 contra 0,0149); el IC pareado todavía no está calculado | fase D; el IC pareado, en el ítem C2 |
| 4 | AUC **≥ 0,75** en las actas disputadas de cada cámara | Dip 0,65 · Sen 0,56 | fase D |
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

**5. La ficha de desvío individual** (`disciplina_individual.csv`) se calcula con **toda la historia**, no en walk-forward. El censo usa el desvío del linaje en su lugar; el efecto está acotado: fijar el desvío de esa rama (4,67% de los votos) en cualquier valor entre 0 y 0,30 mueve el Brier total como máximo 0,0021 (de 0,1391).

**6. Intervalos.** El IC del skill usa 300 réplicas de un bootstrap sobre leyes (ruido de ~0,014 en las colas) y un único corte de historia. El del skill de la era vigente es ancho (±0,255).

**7. Estimadores con offset contaminado.** β, δ, θ y ψ se estimaron sobre un récord con fuga (`shift(1)` por fila, sin guard, sin encoger, sin origen). Se **corrigen y re-estiman** en la fase D; hasta entonces no se los cita como medición.

**8. Lo que las pruebas de reproducibilidad no cubren** (A2 y A3). Los estadísticos por acta que viajan por git alcanzan para recalcular skill, IC, τ y ε₀ **sobre la grilla de ε₀ de 0,005 y con Brier/log-loss**; cualquier otra cosa (la cobertura de la banda, tablas por fuente, otra pérdida) exige regenerar el censo (43 min). La igualdad entre Python 3.11 y 3.14 se midió en Windows; el CI es Linux y ahí sólo se sabe que la suite pasa.

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
python modelo/ensemble/src/estimar_epsilon_tau.py --columna estricta__general   # ε₀ y τ del motor de hoy (sin el parquet)
python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 --origen EJECUTIVO --json salida.json
python coordinacion/AUDITORIA-2026-09/cobertura_canonica.py               # la tabla del límite 3
python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 7     # regenerar el censo (43 min)
```
