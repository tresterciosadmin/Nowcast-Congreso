# 02 — El sistema de medición: en qué número se puede confiar

**Commit auditado:** `bcc62b3` · Conf.: **V** verificado (código o corrida) · **I** inferido · **N** no verificado. Las rúbricas de veredicto están fijadas en `00-preregistro.md` **antes** de medir. Tres mediciones nuevas de esta auditoría: `control_independiente.py`, `invariancia_al_futuro.py`, `contraste_aprobacion.py` (en esta carpeta).

## 0. Veredicto por número

| número | veredicto | por qué |
|---|---|---|
| **Skill global 0,1333** [0,057; 0,198] (691.845 votos, 3.731 leyes) | **CONFIABLE** | **Reproduce byte a byte desde cero** (censo regenerado en una copia limpia de `HEAD`: `P_i` idénticos, JSON idénticos); motor real; invariancia al futuro (150 actas, 0 diferencias); IC por ley; un récord independiente hecho desde el voto crudo da **0,1335**. El IC no cambia al re-muestrear por fecha de sesión [0,066; 0,200] ni por mes [0,066; 0,203]; **al excluir los votos sin clave de ley el skill sube a 0,166** [0,076; 0,242]: no hay sesgo al alza. Reservas menores: IC con 300 réplicas (tiene ruido de ~0,014 en las colas) y vale con el origen conocido (57% de las actas). |
| Skill por era (0,133 / 0,277 / 0,081 / 0,011 / **0,010**) | **CONFIABLE** | mismo motor y datos. La conclusión "en la era vigente no se distingue de la tasa base" **es lo que dicen los datos**: [−0,28; 0,26] con 312 leyes ([−0,22; 0,24] por fecha). |
| Rama récord 0,164 (95,3%) | **CONFIABLE** | idem |
| Rama sin récord −0,380 (4,7%) | **CON RESERVA** | el harness usa el desvío **del linaje**, no la ficha; el censo no ejercita el código de desvío de producción (efecto acotado en ≤ 0,002 de Brier, ver §4a) |
| **P(aprobación) contra resultados** (skill 0,25 [0,19; 0,30], 5.831 actas) | **CON RESERVA** | medido por primera vez acá; condicionado a los presentes; ε₀ y τ se estimaron sobre el mismo panel; una configuración; malo en mayorías especiales |
| **Cobertura de la banda 63,6%** (sesgo −6,9 votos) | **CON RESERVA** | reproduce exacto (63,63%, sesgo 6,93). Es **condicional a los presentes** (`p_presente = 1`), actas con ≥ 20 votos, 1.000 simulaciones, una semilla, **sin IC** |
| Banda "99,88%" (ADR-0025) | **NO CONFIABLE** | mide con un oráculo: `agregador.backtest` le da a la simulación la línea que cada bloque tuvo **en esa acta** |
| Skill publicado anterior 0,1611 | **NO CONFIABLE** | `shift(1)` por fila, misma ley y mismo día; copia del récord sin origen |
| Récord por tema "+11,06%" | **NO CONFIABLE** | misma fuga. El número limpio (−2,12% [0,84; 3,48] contra el motor) es **CONFIABLE** |
| Encoger vs cortar (+2,8% [1,8; 4,2]); `n ≥ 8` vs `n ≥ 1` (+0,5% [−0,01; 1,26]) | **CONFIABLE** | re-medidos limpios en ADR-0034 |
| Guard de era | **CON RESERVA** | con el motor completo nadie lo midió encendido/apagado (`GUARD_ERA=0` deja sin récord todo lo anterior a 2023, no sirve). **Medido acá con el control independiente**, quitando sólo el corte por era: **+0,0028 de Brier a favor del guard [−0,0006; +0,0066]** (≈ 2%, incluye 0; sólo el Senado lo excluye: +0,0030 [0,0005; 0,0057]); **en la era vigente −0,0003 [−0,012; +0,010]**: no hace nada |
| β (`F_i` 2,088, lealtad×jefe 1,750) | **NO CONFIABLE** | offset con fuga y sin guard/encoger/origen; con el offset limpio 2,05 y **1,29**; el walk-forward que lo prendió no se re-corrió; el censo no lo aplica |
| ε₀ = 0,035, τ = 1,19 | **CON RESERVA** | estimados sobre el offset del espejo; limpio: ε₀ **0,055**, τ 1,197. El término sí mejora el log-loss contra resultados reales (Δ −0,036 [−0,055; −0,018]) |
| ψ, θ, δ | **NO CONFIABLE** | offset contaminado, no re-medidos; ninguno está en el número (ψ ni siquiera está implementado) |
| Presencia $\pi_i$ | **SIN MEDICIÓN** | el censo sólo evalúa votos emitidos |
| Ficha de desvío `disciplina_individual.csv` | **NO CONFIABLE como walk-forward** | usa toda la historia (69 actas posteriores al 2026-06-01 en la canónica) |
| **Origen del proyecto** (el insumo que carga el skill) | **SIN VALIDAR** | 43% `DESCONOCIDO`; etiquetas nunca contrastadas con una muestra a mano (**fuera de alcance: requiere otra ronda**) |

## 1. Inventario de toda lectura temporal

Búsqueda por `grep` y AST en `modelo/`, `evaluacion/`, `variables/`, `datos/`, `casos/` (sin tests). **Ninguna otra ocurrencia de `shift(`/`expanding(`/`cumsum(`/`merge_asof` alimenta el número publicado.** [V]

| hit | qué historia ve | ¿fecha estricta? | ¿excluye la misma ley? | ¿alimenta número o parámetro? |
|---|---|---|---|---|
| `nowcast_puertas.py:304,316` (`_alineacion_base`) | votos de la era, `fecha < F` | **sí** (`<`, desde el 28-09; antes `<=`) | no (el motor no conoce "ley"; en producción `F` = hoy) | **número** |
| `bloque.py:543-544` (`proyectar_postura`) | `[F−730d, F)` | **sí** | no (lo excluye el harness) | **número** |
| `baseline_voto_individual.py:497-505,656` | el harness decide qué votos existen: `<` + `_ley ≠ ley` | **sí** | **sí** (claves de ley) | número publicado (skill) |
| `ensemble.py:173`, `bloque.py:180,346` | mandatos `desde ≤ F ≤ hasta` | vigencia, no historia | — | número (roster) |
| `disciplina.py` (ficha) | **toda la historia** | **no** | no | número (rama sin récord y β) |
| `puerta_a.py:317` (`caracter_de`) | dictámenes con `fecha_dictamen ≤ corte` | no (`≤`; 36 pares del mismo día) | no | A/C: identidad; efecto 0 |
| `beta_dictamen.py:124` (`contexto_de`) | firmantes del dictamen, **sin corte de fecha** | no | — | β (sólo con `proyecto_id`) |
| `origen_lider.py:140,155`, `origen_por_acta.py:25` | vigencia del autor; OD publicada ≤ fecha del acta | sí | — | origen (insumo) |
| `icg_contexto.py:164-210` | serie **mensual** del ICG: `shift(1).expanding` por gobierno y medias móviles que incluyen el mes | mensual | — | ninguno (ICG desconectado) |
| `embudo.py:335` | año ≤ corte | anual | — | ninguno (el embudo no entra) |
| `casos/nowcast_puertas_html.py:59` | ICG del mes `≤ F` | — | — | sólo se muestra |
| `backtest_cadena.py:349-355` | años estrictamente previos; evaluación con día 15 de cada mes | anual/mensual | — | ninguno (neutralizado 22-08) |
| **10 scripts de estimación** con `shift(1).expanding()` por fila | ver §2 | **no** | **no** | parámetros de producción o justificaciones |

## 2. Scripts de medición y estimación

`import motor?` = importa `nowcast_puertas`/`perfil_legislador`; `récord propio` = arma su `shift(1)`/`cumsum`; unidad del IC: L = ley, A = acta, G = legislador. [V por grep y lectura]

| script | produce | ¿importa el motor? | ¿récord propio? | corte | IC | ¿alimenta producción? |
|---|---|---|---|---|---|---|
| `baseline_voto_individual.py` (harness) | P_i del motor por voto | **sí** (desde `bf831aa`) | no | `<` + otra ley | L (300 réplicas) | **el número publicado** |
| `censo_detalle_paralelo.py`, `resumen_censo_limpio.py` | censo y resumen | vía harness | no | idem | L | número publicado; **escribe rutas versionadas** |
| `medir_fuga_historia.py`, `medir_record_por_tema_limpio.py` | descomposición de la fuga; −2,12% | sí | no | variantes | L | apagó `RECORD_POR_TEMA` |
| `medir_tau_limpio.py`, `chequear_direccion_beta.py` | τ/ε₀ limpios, cobertura 63,6%; β limpio | sí | no | censo | — / L | no aplicados |
| **`estimar_beta_dictamen.py`** | β, δ (`beta_dictamen.json`) | no | **sí** (`:296-310`) | fila | A | **β (ON)** |
| **`estimar_epsilon_tau.py`** | ε₀, τ | no | **sí** (`:103-104`; hoy lee el censo por defecto) | fila / censo | — | **`EPSILON0`, `TAU` (ON)** |
| `estimar_psi_arrastre.py` / `estimar_theta_sobre_tablas.py` | ψ / θ | no | **sí** (`:87-88` / `:115`) | fila | A | no (ψ sin implementar; θ descartado) |
| `validar_beta_dictamen_walkforward.py` | el walk-forward que prendió β (Brier 0,1725 → 0,1591) | no | reusa el panel del estimador | 70/30 por tiempo | A | **justificó β** |
| `validar_sobre_tablas_walkforward.py` | saturación de θ | sí | reusa panel | tiempo | A | descartó θ |
| `fase1_rec_por_tema.py`, `medir_rec_por_tema.py` | el "+11,06%" | no | **sí** (`:117-132`, `:88-100`) | fila | G/A | **justificó `RECORD_POR_TEMA`** |
| `medir_guard_era.py` | guard de era | parcial | **sí** (`cumsum`, `:96-103`) | fila | — | **justificó `GUARD_ERA` (ON)** |
| `diagnostico_senado.py` | diagnóstico del Senado | no | **sí** (`:96-97`) | fila | — | no |
| `record_por_origen.py`, `record_por_origen_brazos.py` | 0033 | no / sí | réplica (`cumsum`, `merge_asof`) | fecha, sin otra ley | mayor de (Poisson por expediente, por legislador) | no |
| `fase0_control_temas.py` | 0028: brazos de multietiqueta | vía harness viejo | no | mes | A | cerró la línea de tema (**con el brazo `primaria` sin `tema`**) |
| `medir_estabilidad_record_por_tema.py`, `firma_tematica_*` | 0031, 0032 | no | no (correlaciones entre ventanas) | ventanas disjuntas | G | no |
| `agregador.backtest` (dentro de `agregador.py`) | calibración agregada: el "99,88%" | no | **oráculo**: línea de bloque observada, `agregador.py:307-322,401` | — | — | **justificó ε₀+τη (ON)** |
| `prueba1/2/3`, `validar_*capitulos/titulos` | cobertura de capítulos | sí (con `origen=None`) | no | `<` (margen 5 días) | — | no |

**Los cinco que sostienen algo prendido** (`estimar_beta_dictamen`, `validar_beta_dictamen_walkforward`, `estimar_epsilon_tau`, `agregador.backtest`, `medir_guard_era`) **usan un espejo o un oráculo**.

## 3. Los tres sospechosos que el prompt nombra

| archivo | veredicto | evidencia |
|---|---|---|
| `nowcast_puertas.py` (`shift(1)` restante) | **ninguna de las dos**: es un **comentario** | `:211`, dentro del bloque que explica la fuga |
| `variables/proyecto/src/icg_contexto.py` | **uso legítimo** | `shift(1).expanding` sobre una serie **mensual** del ICG, por gobierno, "para que el mes corriente no entre en su propio neutro" (`:174-181`); las medias móviles (`:204-210`) incluyen el mes; no alimenta el número |
| `modelo/ensemble/src/backtest_cadena.py` (550) | **ninguna de las dos**, y está **muerto** | `main` levanta `SystemExit` desde el 22-08 (ADR-0012). `cumsum().shift(1)` por **año** (`:353-354`, estrictamente previo). Sí tiene un mirar-adelante acotado: evalúa cada proyecto al **día 15 de su mes** (`fecha = mes-15`, `:202,236`), hasta ~14 días después de su publicación. Nada lo llama y su salida no alimenta ningún parámetro |

## 4. Fuentes de fuga que no son historia de votos

| # | fuente | mecanismo | tamaño | ¿cubierta por un test? |
|---|---|---|---|---|
| a | **ficha `disciplina_individual.csv`** | calculada con toda la historia; entra en la rama sin récord (4,67% de los votos, 9,99% del Brier total) y en β | **acotado**: fijar el desvío de esa rama en cualquier valor entre 0 y 0,30 mueve el Brier total como máximo 0,0021 (de 0,1391) | no (declarada en el docstring del harness y en URGENTE U4.1) |
| b | **`puerta_a.caracter_de`** y `beta_dictamen.contexto_de` | `fecha_dictamen ≤ corte`: 36 pares dictamen–acta del mismo día (34 proyectos); `contexto_de` no corta por fecha | **cero** en el número (A y C son identidad; β no actúa en el panel); β podría ver un dictamen que todavía no existía en un backtest | no |
| c | **15,3% de los votos sin clave de ley** | cada acta es su propia ley: no se excluye la misma ley de fecha anterior (el mismo día sí lo corta `<`) | **≈ 0,003 de skill [I]**: 18,5% de las actas con clave tienen otra de su ley en fecha anterior; excluir la ley costó 0,017 de skill en el harness viejo (ADR-0034). **Medición directa: el skill *excluyendo* esos votos es 0,166, mayor que el global 0,133**: no hay señal de inflado | el harness lo loguea; ningún test lo acota |
| d | **taxonomías por LLM** (`agente_taxonomias.py`, `tema_por_capitulo.py`) | el clasificador (Haiku) pudo conocer resultados por su preentrenamiento; no se auditó qué texto ve | **cero** en el número: `TEMA_AUTO` y `RECORD_POR_TEMA` están apagados y el panel no pasa `proyecto_id` | no |
| e | **`origen_por_acta`** | OD publicada ≤ fecha del acta (`origen_por_acta.py:25`); vigencia del autor (`origen_lider.py:140,155`): **sin fuga temporal** | — | `test_origen_lider.py` (unitario) |
| f | `padron_vigente`, `jefes_bloque` | `hasta` de los mandatos se conoce ex post | **cero** en el censo (usa los votantes reales); en producción es el roster a la fecha | no |
| g | **`ley_por_acta`** | unión de tres tablas de enlace: ninguna pasa del 72% de cobertura | conservador (excluye de más) | `test_historia_sin_fuga.py` (claves) |

**El que más pesa no es una fuga: es el origen (e)**: el récord **sin** origen da 0,048 y **con** origen 0,1335. El insumo más influyente del modelo no está validado (ver §0).

## 5. Reproducibilidad del 0,1333 (Fase 2.5)

**Reproduce.** Procedimiento: copia limpia de `HEAD` (`git archive`, sin el parquet ignorado) en `Archivos_Borrar/repro/`, y `censo_detalle_paralelo.py --procesos 4` desde cero (**43 min**, 4 procesos; el ADR cita 34 min con 3).

| chequeo | resultado |
|---|---|
| votos, claves `(acta, legislador)` y voto real | **691.845 idénticos** |
| `p__estricta__general`, `__fecha__tema`, `__dia_incluido__tema`, `__dia_incluido__general`, `__estricta__tema` contra el detalle en disco | **`max|ΔP_i| = 0` en las cinco** (0 votos con diferencia > 1e-9) |
| `resumen_censo_limpio.py` | **skill publicado 0,1333**; global 0,1335 (votos en común); 0,3257 con la fuga; 0,1152 con récord por tema; era vigente 0,0100 |
| `censo_limpio_2026-09-28.json`, `baseline_voto_individual.json` (mtime 14:28) y `tau_limpio_2026-09-28.json` (14:33) regenerados | **idénticos byte a byte a los versionados** (594 claves en el primero, 0 distintas) |

**Lo que no reproduce tal cual (hallazgo):** la receta de ADR-0034 §Reproducir (`censo_detalle_paralelo.py` y luego `resumen_censo_limpio.py`) **falla con `KeyError: 'share__estricta__general'` en un checkout limpio de `HEAD`**. El resumen espera columnas auxiliares que sólo existen si `RECORD_POR_TEMA` estaba **prendido** al generar el detalle, y esa bandera se apagó en el mismo commit. Además la columna `p` del detalle **sigue a la bandera**: el del disco (28-09 13:58) tiene `p` = récord por tema (skill 0,115), y el regenerado tiene `p` = general. Para completar la reproducción hubo que agregar en la copia las columnas con el sufijo esperado, tras verificar que son idénticas a las del disco (`max|Δ| = 0`). **El pipeline documentado depende del estado de una bandera que cambió después.**

## 6. Cobertura de la banda (Fase 2.6)

**63,6% reproduce.** `medir_tau_limpio.py` sobre el detalle regenerado: cobertura **0,6363** sobre 5.851 actas, ancho mediano 40 votos, sesgo **6,93** votos por debajo del real (ε₀ = 0,035, τ = 1,19). Estimaciones limpias: ε₀ **0,055**, τ **1,197**; con el offset del harness con fuga 0,015 / 1,185; con el `<=` del motor 0,000 / 1,146.

| configuración (misma simulación del motor, mismas 5.851 actas) | cobertura del [p5,p95] | sesgo del recuento |
|---|---:|---:|
| **producción** (ε₀ 0,035, τ 1,19) | **63,6%** | −6,93 votos |
| con los **ε₀ y τ re-estimados limpios** (0,055; 1,197) | **60,4%** | −8,68 |
| **sin τ** (ε₀ 0,035, τ 0) | 14,8% | −2,79 |
| offset del harness con fuga, τ 1,19 | 61,0% | −8,73 |

**Re-estimar con el offset limpio no arregla la banda: la baja** (63,6% → 60,4%). El problema no es el valor de τ ni de ε₀ sino la forma del shock (un shock simétrico en logit baja la media cuando las $P_i$ son altas, y el estimador de τ usa la mediana por acta). Los tres JSON regenerados (`censo_limpio`, `baseline_voto_individual`, `tau_limpio_2026-09-28`, reescritos hoy 14:28-14:33) son **idénticos byte a byte** a los versionados.

**Qué mide cada uno:**

| | `agregador.backtest` (el 99,88%) | `medir_tau_limpio.cobertura` (el 63,6%) |
|---|---|---|
| **entrada** | la línea de cada bloque **observada en esa misma acta** y la ficha de desvío de toda la historia | las $P_i$ del motor en walk-forward limpio |
| **qué prueba** | la mecánica (umbral, quórum, shock) **dado el resultado** | la cadena entera $P_i$ → recuento |
| **actas** | 4.859: sólo `resultado` en **mayúsculas** exactas (`agregador.py:383`); quedan afuera ~1.000 con `afirmativo`/`negativo` en minúscula | 5.851 con ≥ 20 votos |
| **asistencia** | `p_presente = None` | `p_presente = 1` (sólo los que votaron) |
| **resultado** | 99,88% con ε₀ = 0,035, τ = 1,19 | **63,6%** con los mismos |

**Ninguno mide la banda que produce el panel**: la producción incluye la asistencia (`p_presente` real), que ninguna medición ejercitó.

## 7. Parámetros de producción que dependen de mediciones contaminadas (lista cerrada)

| constante o bandera | medición que la justificó | ¿usa la fuga/espejo? | ¿re-medida limpia? |
|---|---|---|---|
| `MIN_HIST_INDIVIDUAL = 1` | 741.275 votos, `n≥1` 0,1702 / `n≥8` 0,1665 (06-09) | sí (harness con fuga) | **sí**: +0,5% [−0,01; 1,26] (ADR-0034) |
| `GUARD_ERA` ON | 0,1304 → 0,1611 (`medir_guard_era.py`) | **sí** | **parcial**: 0033, +3,6% sin guard, fecha estricta sin "otra ley" |
| `SHRINK_RECORD` ON, k = 5 | "le gana a cortar en las 5 eras" (06-09) | sí | **sí**: cortar es +2,8% peor [1,8; 4,2]; **k = 5 no se ajustó** |
| `BETA_DICTAMEN` ON (`beta_dictamen.json`) | M6 + walk-forward Brier 0,1725 → 0,1591 (14-09) | **sí** | **parcial**: coeficientes con offset limpio (`chequear_direccion_beta.py`) pero el `json` de producción **no se actualizó**; el walk-forward no se re-corrió |
| `INCERTIDUMBRE_LEGISLADOR` ON, `EPSILON0 = 0,035`, `TAU = 1,19` | 99,88% de `agregador.backtest`; `estimar_epsilon_tau` con offset del espejo | **sí, dos veces** | ε₀/τ: **sí** (0,055 / 1,197); la cobertura: **63,6%** — y **P(aprobación) contra resultados** (esta auditoría) sostiene el término |
| `DESVIO_MIN_INDIVIDUAL = 0,02`, `P_INCERTIDUMBRE = 0,01` | pedido de Valle (14-08); sin medición | — | individual: el piso + ε₀ mejora el Brier de $P_i$ (0,1391 → 0,1373) |
| `puerta_a.COEF_POR_DEFECTO = 0` | δ = −2,29 con offset del espejo | sí | no aplica: están en cero |
| `REPARTO_DESVIO = 1,0` | razonamiento sobre "45 ausentes por votación" (22-08) | — | **ninguna** |
| `ventana_dias = 730`, `k_shrink = 5` de `proyectar_postura`; `MIN_VOTOS_FICHA = 20` | elegidos, no ajustados | — | **ninguna** |
| `RECORD_POR_TEMA` (hoy OFF) | +11,06% | **sí** | **sí**: −2,12% [0,84; 3,48] → apagado |

## 8. Las tres mediciones nuevas

**a) Control independiente** (`control_independiente.py`, verificado por AST que no importa el motor; 34 s). Predictores hechos desde el voto crudo sobre los mismos 691.845 votos, con la misma métrica:

| predictor | skill | IC 95% (leyes) |
|---|---:|---|
| **motor** (`p__estricta__general`) | **0,1333** | [0,059; 0,200] |
| récord encogido al bloque **con origen** | **0,1335** | [0,069; 0,196] |
| récord encogido al bloque, sin origen | 0,0481 | [−0,014; 0,104] |
| récord puro | 0,0318 | [−0,035; 0,091] |
| share del bloque | 0,0266 | [−0,028; 0,078] |
| climatología walk-forward | 0,0135 | [−0,012; 0,034] |
| última votación del legislador | −0,2695 | [−0,366; −0,167] |
| **control positivo**: récord con fuga del mismo día | 0,2039 | [0,138; 0,267] |
| el motor con su corte viejo (`<=`, misma ley) | 0,3257 | [0,260; 0,384] |

**Guard de era, encendido/apagado** (mismo récord con origen, sólo se quita el corte por era; ΔBrier pareado por ley, positivo = el guard ayuda): global +0,0028 [−0,0006; +0,0066]; 2015-2019 +0,0144 [−0,0004; +0,0288]; 2019-2023 −0,0021; era vigente −0,0003 [−0,012; +0,010]; Senado +0,0030 [0,0005; 0,0057].

ΔBrier pareado (récord con origen − motor) global: −0,00002 [−0,004; +0,003]. **Por era el motor sólo gana en el arranque de un gobierno:** 2019-2023 el récord independiente pierde por 0,037 de Brier [0,002; 0,069] (empieza la era con la historia vacía). En la era vigente el independiente da 0,050 y el motor 0,010 (ΔBrier −0,009 [−0,026; +0,003]).

**b) Invariancia al futuro** (`invariancia_al_futuro.py`): 150 actas reales (30 por era, mitad Diputados y mitad Senado); se corrompen en memoria todos los votos de fecha ≥ la del acta y todos los de su misma ley (cada uno cambia de conducta). Resultado: **`max|ΔP_i| = 0` en las 150** (0 actas con diferencia, en las 5 eras). **Control positivo:** con el corte viejo (`dia_incluido`) la prueba detecta la fuga en **144 de 144** actas donde hay otras del mismo día (`max|ΔP| = 0,84`); con `fecha` (no excluye la misma ley) la detecta en **12 de las 25** actas que tienen otra de su ley en fecha anterior, con 0 falsos positivos: **la sensibilidad para la fuga por misma ley es del 48%**, así que en las otras 13 actas la prueba no habría podido detectarla. No cubre dictámenes ni taxonomías posteriores, la ficha ni la presencia.

**c) Contraste P(aprobación) contra resultados** (`contraste_aprobacion.py`; 5.831 actas, 2.000 simulaciones, tipo de mayoría real de cada acta, IC por ley):

| | producción (ε₀ 0,035, τ 1,19) | sin ε₀+τη (clip 0,01) |
|---|---:|---:|
| Brier (skill vs tasa base 0,94) | **0,0424** (0,250 [0,186; 0,304]) | 0,0442 (0,219) |
| log-loss | **0,171** | 0,207 |
| "seguras" (P > 0,95) y rechazadas | **23** | **230** |
| disputadas (≥10% en contra), skill | 0,281 [0,230; 0,330] | 0,163 [0,100; 0,223] |

Δlog-loss (producción − sin) **−0,036 [−0,055; −0,018]** (mejora); ΔBrier −0,0018 [−0,005; +0,001] (no concluyente). **Calibración de producción:** subconfiado arriba (P 0,909 → real 0,969; P 0,967 → 0,990) y algo optimista abajo (P 0,373 → 0,298). **Por tipo de mayoría:** simple 5.394 actas, Brier **0,026** (98% aprobadas); **dos tercios 256 actas, Brier 0,303** (50% aprobadas, P media 0,68: peor que 0,25); tres cuartos 124 actas, 0,185; absoluta 54, 0,104. El resultado oficial coincide con el recontado de los votos en el 99,5% de las actas.

## 9. Hipótesis de esta fase

- **H1 (un solo error): SE REFUTA en su forma fuerte**, con el criterio pre-registrado (≥ 2 mecanismos independientes, cada uno ≥ 25%): (1) `shift(1)` por fila + copia del récord (0,161 → 0,133: −0,028, 17% del skill publicado); (2) el **oráculo** del 99,88% (mecanismo distinto: la línea observada, no la historia); (3) el brazo **`primaria` del harness que nunca pasaba `tema`** (`fa4c572`: diferencia pareada 0,0 exacta en 232 actas; cerró la línea de tema con un control que era el tratamiento); (4) el `<=` del motor (0,326, que **no** afectó lo publicado); (5) la ficha no walk-forward (acotada) y (6) el 15,3% sin clave (acotado, sin señal). Lo que se confirma es la versión débil: **una clase de error —medir con algo que sabe la respuesta— con varias formas**.
