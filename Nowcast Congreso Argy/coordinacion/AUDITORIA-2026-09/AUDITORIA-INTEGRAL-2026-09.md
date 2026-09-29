# Auditoría integral del motor y de los ADR — informe final

**Commit auditado:** `bcc62b3` (motor idéntico a `6e6b629`) · **Rama:** `auditoria-2026-09` · **Fecha:** 2026-09-28/29 · **Modo:** sólo lectura y medición; se creó únicamente `coordinacion/AUDITORIA-2026-09/` y, como intermedios, `Archivos_Borrar/`. Nada se ejecutó de lo que se propone. **Auditor:** Claude (Sonnet 5.5; Opus como asesor). Como el auditor es del mismo tipo que escribió los ADR 0026-0034, los criterios de refutación se registraron **antes** de medir (`00-preregistro.md`) y hay tres mediciones independientes (`control_independiente.py`, `invariancia_al_futuro.py`, `contraste_aprobacion.py`).

**En una página.**
1. **El 0,1333 es real:** el censo regenerado desde cero reproduce voto por voto, y un récord de 30 líneas hecho aparte da 0,1335. **Pero toda la habilidad viene del *origen* del proyecto** (sin origen: 0,048), y en la era vigente el skill es 0,010 [−0,28; 0,26].
2. **El 63,6% también reproduce**, y re-estimar τ y ε₀ con el offset limpio **baja** la cobertura (60,4%). El término ε₀+τη, en cambio, **sí mejora** P(aprobación) contra resultados reales (log-loss −0,036 [−0,055; −0,018]): su justificación era falsa y el término se sostiene por otra vía.
3. **El número que ve el usuario no es el del motor.** El HTML publicado dice **98,01%**, que **nunca fue una estimación: es 0,99 × 0,99, el techo del clip agregado**. Y el titular lo recalcula un JavaScript aparte (normal bajo independencia, sin τη, con clip): **aun regenerado hoy, el HTML muestra 98,0%** mientras el motor da **61,3%**.
4. **El motor es más chico de lo que dice la fórmula:** "cuatro puertas" son dos simulaciones multiplicadas (A y C son identidad, ~300 líneas que no mueven nada) y hay un piso de 0,02 que la fórmula no muestra. **Sólo el 33% del código no-test del alcance está en el camino del número.**
5. **El control se perdió el 06-09, no el 25-08:** un solo commit `aaa` puso el harness con fuga, los estimadores que heredaron su offset, la regla de método que prescribía ese idioma y tres términos prendidos con cifras medidas con él.
6. **Los procesos se cumplieron y no frenaron nada:** los tres commits que prendieron términos cumplieron ADR-0015 al pie de la letra. La regla era del tipo equivocado: exige *presentar* el cambio, no *verificar la medición*.
7. **Propuesta:** 34 ADR → **6**, **10 reglas** (contra ≈ 55), un anclaje continuo (~80 h) y una poda de ~8.000 líneas sin riesgo para el número.

---

## 1. Qué hace el modelo hoy

Ver `01-motor-real.md` (traza con `archivo:línea`). Hay **dos "números publicados"** que el repo mezcla: **(A)** el skill 0,1333 del voto individual (calidad de $P_i$) y **(B)** la P(sanción) del panel: un proyecto **hipotético** del Ejecutivo en Diputados al 2026-06-01, **61,3%** hoy (`REGENERAR.ps1:291`, sin `proyecto_id`).

**La fórmula efectiva** (defaults verificados en código; panel B), para el legislador $i$ de linaje $\ell$, origen $o$, fecha $F$:

$$P_i=\begin{cases}\dfrac{n_i\,\mathrm{rec}_i+5\,s_\ell}{n_i+5}& n_i\ge1\\[5pt] s_\ell(1-d_i)+(1-s_\ell)\tfrac{d_i}{2}& n_i=0\end{cases}\quad
\bar P_i=\min(\max(P_i,0{,}02),0{,}98)\quad
P_i^{(j)}=\sigma\!\big(\mathrm{logit}(0{,}035+0{,}93\,\bar P_i)+1{,}19\,\eta_j\big)\,\pi_i$$

$$P_c=\Pr[\text{mayoría}]\ (2.000\text{ sims}),\qquad P_{\text{aprob}}=P_D\cdot P_S$$

$\mathrm{rec}_i$ = su récord en la **era**, proyectos del **mismo origen**, **`fecha < F`**; $s_\ell$ = share del linaje (730 días, mismo origen y gobierno, encogido $k=5$); $\eta_j\sim N(0,1)$ uno por simulación, común a todos; $\pi_i$ = presencia.

**Nueve hechos que la documentación no dice o dice al revés** (todos verificados):
1. Los pasos A y C (dictamen) son la **identidad**: `COEF_POR_DEFECTO` es todo cero desde el 25-08 (`puerta_a.py:101`), pero ~300 líneas se ejecutan en cada corrida para un efecto cero.
2. Hay un **piso `DESVIO_MIN_INDIVIDUAL = 0,02`** (`ensemble.py:361`) que topa $P_i$ en 0,98 (23,2% de los votos): no figura en FORMULA §I.00.
3. El origen sólo actúa **si el llamador pasa `origen`**, y en el 43% de las actas es `DESCONOCIDO`.
4. **β no actúa en el panel** (sin `proyecto_id`): el commit que lo prendió dice "byte a byte idéntico".
5. El clip agregado 0,01 **reaparece** con `INCERTIDUMBRE_LEGISLADOR=0`.
6. El censo mide **una** combinación de banderas (los defaults) y **no ejercita** el desvío de producción (usa el del linaje), β, ε₀+τη, ni la presencia.
7. `EPSILON0`/`TAU`, `MIN_VOTOS` y `N_SIMS` tienen **dos defaults** según el módulo; hay **14 banderas** de entorno que cambian el cómputo (el prompt listaba 12) y ningún test fija el valor de `RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0` ni `TAU`.
8. Producción **importa un script de estimación** (`beta_dictamen.py:102` → `estimar_beta_dictamen.py`, que importa el harness).
9. **El titular del HTML no sale del motor.** `casos/nowcast_puertas_html.py` imprime `nc['p_aprobacion']` sólo por consola (`:101`); lo que lee el usuario lo calcula `paprob()` en JavaScript (`:237-240,278,296-297`) con clip [0,01; 0,99] y las $P_i$ movidas por el ICG con los γ de la tabla original de ADR-0008. Reproducido sobre el HTML regenerado hoy: **98,0% contra 61,3% del motor**. El 98,01% de antes era 0,99 × 0,99 (el clip), así que toda comprobación "el número publicado no se movió (0,9801)" **no podía fallar**.

## 2. En qué número se puede confiar

**ESTADO-REAL-DEL-MOTOR corregido** (las 20 filas coinciden con el código en su estado; lo que cambia es la evidencia). Detalle y rúbrica: `02-sistema-de-medicion.md` §0.

| # | término | código hoy | ¿actúa en el panel? | veredicto de la evidencia | corrección respecto de ESTADO-REAL |
|---|---|---|---|---|---|
| 1 | share del bloque | ON | sí | **CON RESERVA** | como pronóstico sólo se mide donde actúa solo: −0,38 (4,7% de los votos) |
| 2 | desvío individual | ON (sin récord y β) | sí (rama sin récord) | NO CONFIABLE como walk-forward | efecto **acotado ≤ 0,002 de Brier**; el censo no ejercita ese código |
| 3 | presencia | ON | sí | **SIN MEDICIÓN** | confirmado |
| 4 | récord propio | ON | sí, con `origen` | **CONFIABLE** (0,1333; reproduce; control 0,1335) | **la habilidad viene del origen** (sin origen 0,048); en la era vigente 0,010 |
| 5-6 | umbrales, quórum, Monte Carlo | ON | sí | estructural | en mayorías especiales el modelo falla (dos tercios: Brier **0,30**) |
| 7 | clip agregado | OFF mientras ε₀>0 | no | ✓ | el **piso 0,02 sigue** y no figura; `INCERT=0` lo reactiva |
| 8 | quórum con abstenciones | OFF | no | inerte | — |
| 9 | δ agregado | 0 | corre, no mueve | ✓ | ~300 líneas ejecutándose para nada |
| 10 | ICG | desconectado | sólo se muestra | nunca predictor | — |
| 11 | gate del dictamen | OFF | no | nunca medido | — |
| 12 | **β** | **ON** | **no** | **NO CONFIABLE** | con offset limpio `F_i` 2,05, lealtad×jefe **1,29** (−26%); **el `.json` de producción no se actualizó**; el walk-forward no se re-corrió |
| 13 | **ε₀+τη** | **ON** | **sí** en el motor (0,98 → 0,61); **el titular del HTML no se movió** | justificación **NO CONFIABLE**; término **CON RESERVA** | cobertura **63,6%**; τ/ε₀ limpios 1,197 / 0,055 y **re-estimar baja la cobertura a 60,4%**; contra resultados mejora el log-loss |
| 14-17 | ψ, θ, proximidad, asimetría ICG | sin código / descartado | no | NO CONFIABLE / nunca medido | ψ no está implementado |
| 18 | récord por tema | OFF | no | "+11%" NO CONFIABLE; −2,12% CONFIABLE | — |
| 19 | multietiqueta | OFF | no | **evidencia rota** | ESTADO-REAL dice "probablemente" ✅: el brazo `primaria` del harness **nunca pasaba `tema`** (`fa4c572`), el brazo `primaria` era idéntico a "sin tema" (el efecto de un tema simple nunca se midió) |
| 20 | récord por origen heredado | inactivo | no | parcial | — |
| — | **piso 0,02** *(no estaba)* | ON | sí | CON RESERVA | mejora el Brier individual (0,1391 → 0,1373) |
| — | **guard de era** *(no estaba)* | ON | sí | **CON RESERVA** | medido acá (control independiente): ayuda ≈ 2% de Brier [−0,0006; +0,0066], **no hace nada en la era vigente** |
| — | **P(aprobación) vs resultados** *(nuevo)* | — | sí | CON RESERVA | **skill 0,25** [0,19; 0,30], 5.831 actas; malo en mayorías especiales |
| — | **origen del proyecto** *(no estaba)* | ON | sí | **SIN VALIDAR** | el insumo más influyente; 43% desconocido; **fuera de alcance: otra ronda** |

**Lo que sí es sólido:** el 0,1333 y su descomposición (reproducidos), encoger vs cortar, `n≥1`, el −2,12% del récord por tema, y P(aprobación) en mayoría simple (Brier 0,026).

## 3. Dónde se perdió el control

Cronología y evidencia: `03-adr.md` §4. **Causas raíz, ordenadas por peso:**

1. **Se medía con algo que sabía la respuesta, y nadie tenía un control independiente.** Tres mecanismos distintos, no uno: (a) el harness con `shift(1)` por fila y copia del récord, **desde su primer commit** (`2dbad10`, 06-09): 0,161 → 0,133; (b) el **oráculo** de `agregador.backtest` (línea de bloque observada): 99,88% → 63,6%; (c) el brazo `primaria` que nunca pasaba `tema`: el cierre de la línea de tema (0028) se hizo con un brazo `primaria` idéntico a "sin tema" (el efecto de un tema simple nunca se midió; las comparaciones multitema contra ninguno sí informan, pero con el harness con fuga). Más el `<=` del motor (0,326), que no afectó lo publicado.
2. **La regla de método prescribía el idioma con fuga y no había un test de la propiedad.** FORMULA §IV.4 entró en el **mismo commit** que el código con fuga y dice "`shift(1)` + `expanding`". El primer test de la propiedad es del 28-09.
3. **El proceso verificaba la presentación, no la medición.** Los tres commits que prendieron términos (`ec5fd05`, `64ff248`, `0a7a03f`) tocaron FORMULA, ESTADO, ADR, tablero y tests; cumplieron ADR-0015. Ninguna regla pedía re-correr la medición con el motor real ni un control independiente. El Nivel 2 ("qué supuesto se agrega sin querer") se llenó con descripciones del mecanismo; en un caso se usó para **sacar** la advertencia que debía frenar el cambio (`0a7a03f` borró de FORMULA "un término temático disputa como mucho el 4,6% restante"). Y **los controles "el número publicado no se movió (0,9801)" no tenían poder**: 0,9801 es el techo del clip.
4. **Tres términos prendidos en 48 horas** (β 09-14, ε₀+τη 09-15, récord por tema 09-16), con el OK de Franco sobre la evidencia que presentó el mismo agente; 10 de los 12 ADR 0023-0034 los decidió Claude en sesión delegada.
5. **Commits que no se pueden revisar.** `2dbad10` ("aaa"): 13+ archivos, FORMULA +1.303 líneas, cuatro ADR, tres defaults y el harness. 19 de 160 mensajes tienen menos de 16 caracteres.
6. **La documentación es una copia que se desalinea** (25.619 líneas, 2,2 MB, 3,7× el código del camino): los vivos se actualizan entre sí; el panel HTML publicado no se regeneró; `tablero_datos.js` afirma 63,6% y 99,88% en el mismo archivo.
7. **Nada fija los valores.** Cuatro constantes sin test; mismo nombre con dos defaults; comentarios que dicen lo contrario del código.

**Hipótesis:**

| | veredicto | evidencia |
|---|---|---|
| **H1** un solo error, muchas consecuencias | **SE REFUTA en su forma fuerte; se confirma la débil** | ≥ 4 mecanismos independientes (arriba), más controles sin poder. Lo común: *medir con algo que sabe la respuesta o que no puede fallar* |
| **H2** banderas prendidas por delegación sin auditoría independiente | **SE CONFIRMA, con matiz** | 10 de 12 ADR delegados; **ninguno de los que prendieron algo (0025, 0026) registra una contrastación independiente antes de prender** (0033 la hizo después y fue la que destapó la fuga). Matiz: β y ε₀+τη llevan un OK explícito de Franco, sobre la evidencia presentada por el agente |
| **H3** complejidad sin retorno (tema/capítulo/origen) | **SE CONFIRMA** | ningún término activo con ΔBrier limpio a favor; ~92% del contenido sin mejora en pie; ~4.850 líneas |
| **H4** la documentación dejó de ser un control | **SE CONFIRMA** | 7 de 10 hechos con contradicción; 6 contra el código; el panel publicado, 15 días desactualizado |
| **H5** las reglas se agregan después del daño | **SE CONFIRMA, con una precisión** | la regla se cumplió en la forma y no frenó nada: **es del tipo equivocado**; y la regla de método prescribía la fuga |

**Primer punto en que el control se perdió de verdad: el 06-09 (`2dbad10`)**, no el 25-08. Ver `03-adr.md` §4.

## 4. Dónde se complejizó

Ver `04-complejidad.md`. En números:
- **25.400 líneas** en el alcance (105 archivos), **16.482 de código**; sólo **4.026 (33% del código no-test)** están en el camino del panel; 4.696 (38%) son medición y estimación; 2.110 no las llama nadie.
- La mitad de `nowcast_puertas.py` es prosa (492 de 980 líneas son código).
- **Del orden de 10.000 líneas** no afectan el número con los defaults (≈640 dormidas en archivos vivos, ≈300 que corren sin mover nada, ≈1.850 sin llamador, ≈2.650 de estimadores con offset contaminado, ≈4.850 de la línea tema/capítulo/origen).
- 14 banderas de entorno, 2^9 combinaciones booleanas, **una** medida. ≈ 55 reglas y controles nombrados; documentación/código **3,7× en líneas, 6,4× en bytes**.

## 5. Propuesta de poda del código — **NO se ejecuta**

Regla: **nada se borra, se mueve** (a `coordinacion/archivo/` o `Archivos_Borrar/`). Ordenada por riesgo creciente. **Criterio de salida común:** (i) el HTML del panel regenerado es idéntico al de antes de la poda; (ii) `p__estricta__general` del censo idéntico (`max|ΔP| = 0`), (iii) `python -m pytest tests/ datos/proyectos/tests -q` y los `test_*.py` restantes con el mismo resultado menos los movidos. Cada poda se hace de a un ADR, con un commit.

| # | qué | LOC aprox. | riesgo | ahorro | criterio de salida específico | test que **debería fallar** si la poda rompe algo |
|---|---|---:|---|---|---|---|
| **P0** | **Archivar lo muerto**: `composicion_capitulos.py` (+test), `tema_por_capitulo.py` y `capitulos_nombre.py` (+tests), `backtest_cadena.py` (+test), `comparar_vias_icg.py`, los stubs "dados de baja" de `ensemble.py`, `0009-BORRADOR`, `CONECTAR-GIT.md`, `_wtest` | ~2.500 con tests | **nulo** | alto | `python .mapa/buscar.py --archivo <cada uno>` devuelve sólo tests/validaciones | `tests/test_rutas_citadas_existen.py`, `verificar_regeneracion.py` |
| **P1** | **Archivar la línea cerrada de medición** (0023-0033): `prueba1/2/3`, `validar_*capitulos/titulos`, `firma_tematica_*`, `medir_estabilidad_*`, `record_por_origen*` (rescatar `split_half` y el bootstrap), `fase0_control_temas`, `diagnostico_senado`, `fase1_rec_por_tema`, `medir_rec_por_tema` (los dos con la fuga) | ~3.900 + ~800 tests | **muy bajo** | muy alto | nadie los importa; C6 conserva cómo reabrir | `test_firma_tematica.py`, `test_fase1_rec_por_tema.py` (se mueven con ellos) |
| **P2** | **Términos descartados**: `estimar_psi_arrastre`, `estimar_theta_sobre_tablas`, `validar_sobre_tablas_walkforward`, `sobre_tablas.py` + `_via_sobre_tablas` + bandera `SOBRE_TABLAS` | ~950 | bajo | medio | el registro deja de listar `SOBRE_TABLAS` | `test_sobre_tablas.py` (se mueve) |
| **P3** | **Ramas dormidas en archivos vivos:** `alineacion_individual_por_area` y la plomería de `RECORD_POR_TEMA`; las ramas `union/ponderada/peor_tema` de `proyectar_postura` y `TEMA_AUTO`/`COMBINAR_TEMAS`; la rama `QUORUM_ABSTENCIONES`; "Manera 2" de `puerta_d` | ~400 y **3-4 banderas** | medio-bajo | alto (menos banderas) | el registro baja de 14 a ≤ 10 banderas | `test_harness_es_el_motor.py` (238/238), `test_agregador.py`, `test_incertidumbre_legislador.py` |
| **P4** | **A y C decorativas:** reemplazar `cargar_caracter`/`condicionar`/`delta_caracter`/`COEF_POR_DEFECTO` por la lectura del rótulo ya calculado (el payload `pasos[]` no cambia); deja de leer 143.817 firmas por corrida | ~300 | medio (contrato del payload) | medio | `pasos[]` idéntico en el panel y en 3 proyectos reales; `p_final` idéntico | `test_caracter_dictamen.py` |
| **P5** | **Desacoplar producción de la estimación:** mover `firmas_por_acta` y `jefes` a `beta_dictamen.py`; después archivar `estimar_beta_dictamen.py` (o reescribirlo sobre el offset del censo) | 562 | medio | medio (el motor deja de depender de un estimador) | `contexto_de` idéntico en los 34 proyectos con dictamen | `test_beta_dictamen.py` |
| **P6** | **Bajar las banderas de 14 a ≤ 4:** dejar `INCERTIDUMBRE_LEGISLADOR`, `GUARD_ERA` (hasta medirlo) y `BETA_DICTAMEN`; `SHRINK_RECORD`, `EPSILON0`, `TAU`, `MIN_VOTOS_FICHA` pasan a constantes del registro; unificar los nombres con dos defaults | ~100 | bajo-medio | alto (la matriz de banderas colapsa) | `test_defaults_fijados` verde | el propio `test_defaults_fijados` |
| **P7** | **Reescribir comentarios y docstrings que contradicen** y sacar la historia de `nowcast_puertas.py` (ya está en los ADR): 980 → ~600 líneas | ~400 de prosa | nulo (sólo comentarios) | medio (legibilidad) | `git diff` sin cambios de código | — |
| **P8** | **Documentos y titular** (ver `05` §5.3, pieza 7): congelar `ESTADO-DEL-PROYECTO` y `PROMPT-*.md`, generar el estado; **que el titular del HTML lea `p_aprobacion` del motor** (borrar `paprob()` y el slider del ICG con γ viejos, ~60 líneas de JS) y regenerar el panel en CI | ~60 de JS | **medio: cambia el número visible de 98% a 61%** | muy alto | el titular del HTML = `p_aprobacion` del motor | test de igualdad titular-motor |
| **P9** | **No se recomienda todavía:** achicar el modelo mismo (reemplazar `proyectar_postura` por el récord con origen de 30 líneas, ~570 líneas de `bloque.py`) | ~570 | **alto** | medio | — | el control independiente **empata** en skill global (ΔBrier −0,00002), pero el motor le gana en el **arranque de cada era** (2019-2023: 0,037 [0,002; 0,069]). Decidir después de los pasos 0-3 del anclaje |

**P0-P2 (≈ 8.000 líneas con tests) no pueden mover el número** y se pueden hacer ya. P3-P7 esperan al paso 3 del anclaje (la métrica de verdad) para tener con qué demostrar que nada se movió. Con P0-P7 el código no-test del alcance pasa de 16.482 a ≈ 9.000 líneas y las banderas de 14 a ≤ 4.

## 6. De 34 ADR a 6, reglas simples y anclaje a la realidad

Detalle: `05-consolidacion-y-anclaje.md`; borradores en `adr-consolidados/` y `REGLAS-borrador.md`.

| ADR consolidado | absorbe (destino principal) | n |
|---|---|---:|
| **C1** Repo, datos y contratos compartidos | 0001, 0002, 0009-BORRADOR *(descartable)*, 0009, 0010, 0011, 0014, 0019, 0020, 0021 | 10 |
| **C2** Voto individual: récord por origen encogido al linaje | 0003, 0004, 0005, 0017, 0018, 0022 | 6 |
| **C3** Formulación y salida del número | 0007, 0012, 0013, 0016 | 4 |
| **C4** Incertidumbre y coyuntura | 0008, 0025 | 2 |
| **C5** Medición y evidencia | 0015, 0032, 0034 | 3 |
| **C6** Línea tema / capítulo / origen: cerrada | 0006, 0023, 0024, 0026, 0027, 0028, 0029, 0030, 0031, 0033 | 10 |
| | **total: 35 archivos, ninguno huérfano, ninguno duplicado** | **35** |

C6 **merece ADR propio** y corto: registra qué se probó, qué dio y con qué medición mínima se reabre; sin él, las reglas que sobreviven (agregar sin reemplazar, un grado de libertad, un control idéntico al tratamiento es una alarma) se pierden con los ADR.

**Las 10 reglas** (`REGLAS-borrador.md`): (1) nada afecta el número sin medición vigente con el motor real; (2) historia por fecha estricta y otra ley; (3) todo IC re-muestrea leyes y las comparaciones son pareadas; (4) ninguna medición arma su propio récord; (5) un control tiene que poder fallar; (6) lo declarado se contrasta con lo observado; (7) una mejora sin explicación es una alarma; (8) ningún default cambia sin un test que fije el valor; (9) un dato, un lugar: los documentos se generan; (10) prender exige OK de Franco, IC a favor con Holm y confirmación fuera de muestra; apagar no exige nada. **De ≈ 55 reglas y controles a 10 + 4 trampas del dato.**

**El anclaje** (`05` §5.3), con costos: métrica de verdad (6 h; 14 min con una variante) · calibración de lo declarado (6 h) · versión rápida de 500 leyes (~5-7 min; **MDE 4,3% de Brier**) más invariancia (8 h) · gate de tres ramas (10 h) · registro generado (12 h) · monitoreo hacia adelante, nivel 1 (12 h; el bot trae resultado y conteos por acta, no votos nominales) · qué se corta (10 h). **Secuencia de 8 pasos, ≈ 80 h**, con criterio de salida verificable cada uno. Lo esencial y barato (pasos 0-2: CI en verde, registro con defaults fijados, invariancia y control independiente en los tests) son ~2 días.

**Un límite honesto que conviene tener presente:** un gate estadístico **no atrapa las fugas** (la de septiembre fue heterogénea entre leyes: con 500 leyes su MDE 0,052 supera al efecto 0,031) y **no puede afirmar skill > 0 en la era vigente** (necesitaría ~2.000 leyes para ±0,10, hoy hay 312). A las fugas las atrapa la prueba de invariancia; a las regresiones, el gate pareado; a lo demás, el monitoreo hacia adelante.

## 7. Decisiones que le tocan a Franco

Lista cerrada. Recomendación primero; costo entre paréntesis.

1. **La banda declarada al 90%** (cubre 63,6%; re-estimar la empeora). **Recomendado: rotularla con lo observado (≈ 64%) o sacarla del panel** hasta que exista una calibración fuera de muestra (0,5 h). Alternativa: recalibrar ε₀ y τ hasta cubrir 90% (6 h + medir el efecto sobre P(aprobación)). *URGENTE U2.*
2. **¿Re-estimar β/δ/θ/ψ con el offset limpio?** **β sí** (4 h; el censo ya deja el offset limpio; hoy `beta_dictamen.json` sigue con 1,750 y el limpio da 1,29); **δ, θ y ψ no**: no están en el número y sus estimadores se archivan (P2). *URGENTE U3.*
3. **Política de banderas:** adoptar las reglas 1, 8 y 10: **ninguna bandera se prende sin medición con el motor real, IC por ley pareado, un test que fije el valor y el OK de Franco; apagar es libre**, y en una sesión delegada Claude **propone, no prende**. (2 h para escribirla; el gate, ver 6.)
4. **Cuántos ADR:** **6 (recomendado)**; 5 si C6 se reduce a un anexo de C5; 7 si C2 se parte en voto individual y dictamen/β.
5. **Qué gate primero:** **el registro con los defaults fijados y la invariancia** (pasos 1 y 2, ~14 h), antes que el gate estadístico; el estadístico no atrapa fugas y su potencia en la era vigente es nula.
6. **El panel publicado.** El HTML dice 98,01% y el motor da 61,3%, y **regenerarlo no alcanza**: el titular lo recalcula un JavaScript con clip y sin τη (verificado: 98,0% aun regenerado). **Recomendado:** que el titular lea `p_aprobacion` del motor y borrar el slider del ICG con γ viejos (P8, ~2 h); hasta entonces, **retirar el panel o rotularlo "ilustrativo"**. Ojo: el número visible pasa de 98% a 61%, así que la decisión es tuya (ver 9).
7. **El guard de era** (ON): la medición independiente dio +2% de Brier a favor, con IC que incluye 0, y **cero efecto en la era vigente**. **Recomendado: dejarlo ON con reserva**; medirlo con el motor completo exige un brazo "sin corte por era" que hoy no existe (4 h + 45 min de cómputo). Nótese que `GUARD_ERA=0` **no** es esa medición: deja sin récord todo lo anterior a 2023.
8. **Validar las etiquetas de `origen`** con una muestra a mano de ~200 actas (6 h): es el insumo que carga todo el skill y no está validado. *Segunda ronda.*
9. **Mayorías especiales:** el modelo tiene Brier 0,30 en dos tercios (256 actas) y 0,185 en tres cuartos. **Recomendado: declarar que P(sanción) sólo vale para mayoría simple** hasta modelarlas (0,5 h para el rótulo).
10. **Aprobar la poda P0-P2** (≈ 8.000 líneas, riesgo nulo para el número, ~6 h) ahora, y P3-P7 tras el paso 3.
11. **El CI en rojo en `HEAD`** (`test_insumos_del_motor_viajan`): que el insumo del censo viaje como estadísticos por ley (~200 KB, recomendado) o declararlo excepción con su motivo (3 h).
12. **El worktree `suspicious-lalande`** (175 MB, motor del 15-09) y `Archivos_Borrar/repro/` (~180 MB, esta auditoría): retirarlos a mano con tu OK.
13. **Trabajar en ramas o en `main`:** hoy todo aterriza en `main` (12 fusiones en 243 commits). **Recomendado:** dejar `main` protegido para el motor y las mediciones, y eliminar de `CLAUDE.md` la regla "un módulo, un dueño, una rama", que no se practica.

## 8. Qué no se pudo verificar y por qué

- **El estado del CI en GitHub.** `gh` no está autenticado en esta PC; que está en rojo en `HEAD` es **inferencia** (el test que falla localmente falla igual en un checkout limpio). [N]
- **Que el CI, con Python 3.11, dé lo mismo que esta PC** (3.14, pandas 3.0). Un pandas 3 rompió una de mis pruebas. [N]
- **Las etiquetas de origen**, el insumo más influyente (43% desconocido). Fuera de alcance: datos. [N]
- **La asistencia** ($\pi_i$ y su efecto sobre la banda): ninguna medición la ejercita. [N]
- **La calibración de ε₀ y τ fuera de muestra**: se estimaron y evalúan sobre el mismo panel. [N]
- **Algunas afirmaciones de los lotes de lectura de ADR** (tamaños de archivos, cifras de `MAPA.md`, `rutas.py`, `proyectos.db`, el "205 firmas") **las tomé de las fichas** sin re-verificarlas una por una; las que cito en el informe las contrasté (`test_rutas`, `MAPA.md:181`, ADR-0017, brazo `primaria`). Están marcadas con su lote en `adr-fichas/`. [V parcial]
- **El "~1,7×"** de la regla del expediente (FORMULA §IV.6, ADR-0032/0034): no lo encontré derivado en ninguna medición. [N]
- **El bot y los workflows** (`bot-diario.yml`, `icg-mensual.yml`, `padron-vivo.yml`) quedaron fuera de alcance salvo lo necesario para evaluar el monitoreo hacia adelante; **la dependencia del motor de datos del bot requiere otra ronda**.
- **La calidad de la canónica** (hueco de Diputados 2020-23 que señala el lote A: 25 actas, 6.421 votos): fuera de alcance.
- **El lote de la cadena 0012 → 0016 → 0025** lo hizo Opus al tercer intento (los dos primeros chocaron con el límite de la API, igual que la primera tanda de lotes de Sonnet). Verifiqué por mi cuenta sus dos hallazgos más fuertes (0,9801 = 0,99² y el titular por JavaScript) y el borrado de la advertencia en `0a7a03f`; el resto de sus filas figura con su fuente en `adr-fichas/lote_C.md`.

## Anexo — Revisión independiente (refutación de las diez afirmaciones principales)

Como se fijó en `00-preregistro.md`, al cierre un revisor (Sonnet, sólo lectura) que **no vio este informe** intentó refutar diez afirmaciones. **Ninguna quedó refutada; seis se confirmaron tal cual y cuatro con matices de alcance**, ya incorporados arriba. Detalle y evidencia en `refutacion-independiente.md`.

| # | afirmación | veredicto | matiz del revisor |
|---|---|---|---|
| 1 | `puerta_a` con coeficientes en 0: `condicionar` es la identidad y se ejecuta en cada corrida | confirmada | el carácter no es código muerto: se muestra en el panel y alimenta `_via_sobre_tablas` (apagado); lo cierto es que no mueve la probabilidad |
| 2 | piso 0,02 en `ensemble.py:361` que §I.00 no menciona | con matices | FORMULA **sí** lo trae en §I.4b y en la tabla de constantes, bajo el aviso de que I.1-I.4 son versiones anteriores |
| 3 | el panel no pasa `proyecto_id`: β, `RECORD_POR_TEMA`, `TEMA_AUTO` no actúan | confirmada | β igual lee dos parquets de firmas (~125.820 filas en Diputados) para devolver `sin_dato` |
| 4 | `Nowcast-Puertas.html` dice 0,9801, del 14-09, anterior a `64ff248` | confirmada | — |
| 5 | los tres commits tocaron FORMULA, ADR, tablero y tests | confirmada | en `ec5fd05` el ADR es el 0016 ya existente |
| 6 | FORMULA §IV.4 entró en `2dbad10` prescribiendo `shift(1)` + `expanding` | confirmada | — |
| 7 | la rama `primaria` del harness nunca pasaba `tema` (`fa4c572`) | con matices | el bug siguió hasta `03c9340` (cierre de FASE 0) y se corrigió recién el 28-09; el JSON no es idéntico bit a bit (IC [−5e-05; 6e-05]); las comparaciones `union` y `ponderada_logit` contra `primaria` sí informan (esos brazos pasan `temas=`); **lo que no se midió es el efecto de un tema simple** |
| 8 | `tablero_datos.js` `:253` (63,6%) y `:318` (99,88%) se contradicen | con matices | `:318` es un hito fechado 09-16 que nunca se marcó como superado |
| 9 | `test_rutas` no puede fallar (`RAIZ` en el inventario) | confirmada | con `RAIZ` hay 80 rutas cruzadas y 0 huérfanas; sin `RAIZ` ni `RAIZ_GIT`, 14 |
| 10 | dos commits cambian el default de `RECORD_POR_TEMA` y ningún test lo fija | con matices | `test_record_por_tema.py` ejerce la función, no la bandera; los defaults de `BETA_DICTAMEN`, `INCERTIDUMBRE_LEGISLADOR` y `TEMA_AUTO` sí están fijados |

*Incidente del revisor:* un `Grep` con glob de exclusión mal armado le devolvió líneas sueltas de esta carpeta; declaró que no las usó como evidencia y no abrió ningún archivo de `coordinacion/AUDITORIA-2026-09/`.
