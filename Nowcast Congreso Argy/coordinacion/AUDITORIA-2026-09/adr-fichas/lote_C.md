# Auditoría 2026-09 — Lote C (el central): ADR 0006, 0007, 0008, 0012, 0013, 0015, 0016, 0018, 0025

Auditor de lote, SOLO LECTURA, 29-09-2026. Confianza: **[V]** verificado en código/dato/git con la
referencia dada · **[I]** inferido · **[N]** no verificado. Rutas relativas a `Nowcast Congreso Argy/`
salvo que se diga. Los "hechos ya verificados" de `contexto_lotes_adr.md` se usan sin re-verificar.

---

## Hallazgo que atraviesa todo el lote (leer primero)

1. **El 0,9801 que aparece como "control" en 0016, 0018 y 0025 es el techo del clip agregado, no un
   número del modelo.** `P_INCERTIDUMBRE = 0.01` (`modelo/ensemble/src/ensemble.py:319`) recorta cada
   cámara a 0,99 (`:374-376`) y `p_final = p_B·p_D` (`modelo/ensemble/src/nowcast_puertas.py:873`):
   0,99 × 0,99 = 0,9801. [V aritmética + código] Toda verificación del tipo "prendimos X y el número
   publicado no se movió (0,9801)" (0018:52-57, 0016:141-153, commit `ec5fd05`) **no podía fallar**:
   el número estaba pegado al techo y, además, el panel de producción no pasa `proyecto_id`
   (`REGENERAR.ps1:291-292`). [V]
2. **La cifra titular del HTML publicado NO es la del motor.** `casos/nowcast_puertas_html.py`
   imprime `nc['p_aprobacion']` sólo por consola (`:101`); la "Probabilidad de aprobación" que ve el
   lector la calcula el JavaScript (`:278`, `:296-297`) con `paprob()` (`:237-240`): aproximación
   normal bajo **independencia**, **sin τη_j**, con **clip agregado [0,01; 0,99]**, y con cada P_i
   corrida por el **ICG** (`pmod`, `:229-230`) usando los γ de la tabla ORIGINAL de 0008
   (0,555/0,354/0,333/0,220/0,094, `:227` = `0008:91-97`), el neutro 1,90 del mecanismo 2 eliminado
   (`:44`) y **sin el signo s** de gobierno/oposición que exige 0008:82-84. Arranca en el ICG real
   (`let ICG=DATA.icg`, `:228`; el HTML publicado trae `"icg": 2.07`). El docstring dice "no con un
   modelo paralelo" (`:17-18`): es cierto para P_i, falso para la agregación. [V] Consecuencia [I]: aun
   regenerado hoy, el titular mostraría ≈98% (márgenes de +28 votos saturan la normal en el clip)
   mientras el motor da 0,6132.
3. **Mismo η en las dos cámaras.** `simular_votacion` sortea `eta` como primer draw del rng
   (`modelo/agregador_institucional/src/agregador.py:198, 212`); B y D se llaman con la misma `seed`
   y `n_sims` (`nowcast_puertas.py:850-852, 862-866`; `puerta_d.py:190-193`) → el mismo vector η. Pero
   `p_final` multiplica marginales (`:873`), así que esa correlación se tira. [V código; efecto I]

---

## Filas por ADR

### ADR-0006 — 31-07-2026 — Multitaxonomía por TÍTULO (unidad jerárquica proyecto → título)
1. `0006` · 2026-07-31 · la unidad de análisis pasa a ser proyecto → título/capítulo; P por título; no publicar cifra por título sin backtest.
2. **Quién:** Franco decide, Claude registra (`0006:4`). [V]
3. **Estado declarado:** "ACEPTADO (diseño) / PENDIENTE (implementación)" (`0006:3`). **Real:** (a) lo que el código llama "multitaxonomía, ADR-0006" es **multi-etiqueta por PROYECTO** (`datos/taxonomias/src/registro.py:22`, `variables/proyecto/src/agente_taxonomias.py:1-14`, `mapa_modelo_datos.js:2416` "por título" = el título/nombre del proyecto), no por título de la ley; (b) el nivel título/capítulo se construyó por otra vía — `capitulos_nombre.py` (0023), `tema_por_capitulo.py` (0029), `composicion_capitulos.py` (0027) — todo INACTIVO y la línea **cerrada por ADR-0030** (`0030:3-4`); **ninguno de esos ADR cita a 0006** (grep "0006" en 0023/0027/0029/0030: 0 hits). No existe `proyecto_titulos` (grep: sólo el ADR). [V]
4. **Medición:** ninguna (diseño motivado por casos: Ley Bases, Presupuesto). [V]
5. **¿Fuga/espejo?** No aplica. [V]
6. **¿Vigente en código?** No en el camino de P(sanción): `nowcast()` no tiene nivel título; lo de capítulos está apagado y sin enganche (lote D, fila 0027). La regla "no se publica cifra por título" se cumple **por omisión**. [V]
7. **¿Doc coincide?** `coordinacion/AUDITORIA-2026-09/adr-consolidados/C3-...md:34` lo repite como pendiente; FORMULA no tiene nivel título. `docs/taxonomias/README.md:19` y `registro.py:22` usan el nombre del ADR para otra cosa (multi-etiqueta). [V]
8. **VEREDICTO: INACTIVO** (el diseño se intentó por la línea de capítulos, quedó apagado y cerrado por 0030 sin que 0006 lo registre).
9. **DESTINO: 6** (línea tema/capítulo/origen, cerrada) + ref. 3 (salida). **Sobrevive:** "no se publica una probabilidad por título/capítulo sin un target con qué backtestearla". **Se pierde:** la unidad jerárquica como decisión vigente; el nombre "multitaxonomía" debería quedar sólo para multi-etiqueta.

### ADR-0007 — 31-07-2026 — Régimen de salida: "dos respuestas, siempre"
1. `0007` · 2026-07-31 · cada proyecto: P(sanción) con contexto + nombres de pivotes; informe de 7 secciones; sección 6 (límites) obligatoria; cada corrida archivada en `casos/`.
2. **Quién:** Franco decide, Claude registra (`0007:4`). [V]
3. **Estado declarado:** "ACEPTADO (vigente)". **Real: parcial.** Sí: `nowcast()` devuelve el número y `a_negociar` (hasta 20 incógnitas por cámara, `nowcast_puertas.py:747-767`); el HTML muestra 8 nombres (`casos/nowcast_puertas_html.py:326`) y la advertencia "condicional" (`:298`). No: no hay código para la sección 3 (tasa base, antecedentes del tema), 4 (escenarios de autoría), 5 (pivotes **de comisión**, firmas faltantes: grep `firmas_faltantes|pivote.*comisi` = 0), 6 (sólo la leyenda "condicional") ni 7. `casos/` tiene **un solo caso** (Ley de Lobby, 31-07) y el panel de producción es hipotético, no un caso archivado. [V]
4. **Medición:** ninguna (regla de producto). Cita "skill 0,36" (`0007:60`), cifra de la v1 ya dada de baja. [V]
5. **¿Fuga/espejo?** No aplica. [V]
6. **¿Vigente en código?** Las dos respuestas sí (arriba); el resto del informe, no. La sección 3 pide P(recinto), que **0012 eliminó** (`0012:27`); la regla 3 "la comisión antes que el recinto" (`0007:48-50`) choca con 0012 ("el nowcast deja de estimar si una comisión… va a TRATAR", `0012:12`) y no tiene implementación. [V]
7. **¿Doc coincide?** FORMULA §IV.9 (`:1907-1915`) reduce 0007 a "probabilidad y nombres" (coincide con el código, no con el ADR completo). [V]
8. **VEREDICTO: VIGENTE-ESTRUCTURAL** (regla de producto que el código cumple en su núcleo).
9. **DESTINO: 3** (formulación y salida del número). **Sobrevive:** "ni una sin la otra: probabilidad + nombres; todo informe declara lo que no sabe". **Se pierde:** la plantilla de 7 secciones, P(recinto), "skill 0,36"; los pivotes de comisión pasan a pendiente explícito o se descartan.

### ADR-0008 — 04-08-2026 (enmienda 11-08) — ICG como modulador de coyuntura
1. `0008` · 2026-08-04 / 11-08 · el ICG sale del embudo; modula odds por legislador con γ por tramo de desvío; enmienda: dos horizontes (sólo fondo MA6), elimina el mecanismo 2 (nivel declarado).
2. **Quién:** Valle (diseño y decisiones), Claude (estimación e implementación) (`0008:3`); enmienda de Valle (`:5`). [V]
3. **Estado declarado:** "ACEPTADA (con enmienda 2026-08-11)". **Real:** el motor no importa `modulador_icg`/`icg_contexto`/`gamma_icg*` (grep en `modelo/ variables/ casos/ producto/`: sólo `comparar_vias_icg.py`, neutralizado, y tests) → **desconectado del número del motor** [V]. **Pero vive en el HTML publicado** (hallazgo transversal 2) con parámetros de la versión ANTERIOR a la enmienda y sin signo s. [V] Tres juegos de γ conviven: tabla original (0,094-0,555, `0008:91-97` = HTML `:227`), enmienda (0,44/0,48/0,51, núcleo −0,069, `0008:25-33`), JSON actual (`variables/proyecto/outputs/gamma_icg_dos_capas.json`: fondo 1,012/1,147/0,926, núcleo −0,076) ≈ "γ ≈ 1,0" de `ESTADO-REAL-DEL-MOTOR.md:37`. [V]
4. **Medición:** `estimar_gamma_individual.py --modelo dos_capas`, FE por legislador + bootstrap por mes (`0008:99-102`, `:25`); aporte cero como rasgo por ablación walk-forward (`:64-67`). [V texto]
5. **¿Fuga/espejo?** **No** para γ: el estimador no arma récord ni usa `shift(1)` (grep `shift(|expanding|record|offset` en `estimar_gamma_individual.py`: 0). [V] Nunca probado como predictor en el censo (`ESTADO-REAL:37,92`). Posible look-ahead en el tramo de desvío (desvío de muestra completa) [N].
6. **¿Vigente en código?** Motor: no. HTML: sí, como slider que arranca en el ICG real. ≈1.490 LOC de la línea ICG (con tests) sin consumidor en el motor (ver notas b). [V]
7. **¿Doc coincide?** FORMULA fila 10 "medido y desconectado" (`:73`) y ESTADO-REAL:37 son falsos respecto del producto (HTML); `tablero_datos.js:59` y `:230` ponen el ICG como "FUTURO"; FORMULA §I.3 atribuye el piso `d_min` a `modulador_icg.encoger_desvio` (`:315-337`), módulo que el motor no importa. [V]
8. **VEREDICTO: INACTIVO** (código presente y desconectado del motor; el residuo pre-enmienda que corre en el HTML es un defecto, no el ADR).
9. **DESTINO: 4** (incertidumbre y coyuntura). **Sobrevive:** "el clima, si entra, entra por P_i con γ por tramo de desvío y signo por origen, y se prueba como predictor antes de prenderlo". **Se pierde:** mecanismo 2, neutro 1,90, Consecuencia 1 (evaluación de coyuntura obligatoria), las tablas de γ viejas.

### ADR-0012 — 22-08-2026 — Una sola formulación: la cadena de puertas; baja de la v1
1. `0012` · 2026-08-22 · P = [A obs]·P(B|carácter)·[C obs]·P(D|carácter); sin `p_llega_recinto`; número condicional; v1 neutralizada.
2. **Quién:** Valle decide, Claude implementa (`0012:3`); rumbo de Valle del 20-08 (`:12`). [V]
3. **Estado declarado:** "Aceptada". **Real:** vigente. Entrada `nowcast_puertas.py`; `p_final = b["p"]*d["p"]` (`:873`); `condicional_a` en la salida (`:898`) y en el HTML (`casos/nowcast_puertas_html.py:298`); `p_sancion` no entra (grep en `nowcast_puertas.py`: 0); v1 levanta `SystemExit` (`ensemble.py:302-304, 383-395`); `backtest_cadena.main` neutralizado (`backtest_cadena.py:519-549`). A y C "condicionan" vía `puerta_a.condicionar` sobre el **agregado** (`:853, :867`), identidad con `COEF_POR_DEFECTO` en cero (`puerta_a.py:101-107`). [V]
4. **Medición:** ninguna que justifique el diseño (decisión de formulación). El pendiente "el backtest queda sin vara… bloquea re-apuntar" (`0012:40`) se atendió recién con la cobertura de banda de ADR-0034 (63,6%) y con el contraste del auditor contra el resultado oficial (5.831 actas). [V]
5. **¿Fuga/espejo?** No aplica al diseño. [V]
6. **¿Vigente en código?** Sí (arriba). Supuesto de independencia entre cámaras activo (FORMULA `:143-145`), ψ estimado sin implementar (FORMULA fila 14, `:77`). [V]
7. **¿Doc coincide?** FORMULA §I.0 (`:130-147`) sí; §I.1 (`:149-154`) dice que "la única operación real es el clip" — falso con `INCERTIDUMBRE_LEGISLADOR` ON (`ensemble.py:374`), aunque `:104` declara viejas I.1-I.4. [V]
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 3.** **Sobrevive:** "el número es P(aprobación | las dos cámaras votan) = P_B·P_D; A y C se observan, no se estiman; la agenda no se modela". **Se pierde:** el gancho δ agregado de `condicionar` (debe caer por 0016, ver §1), `backtest_cadena` (880 LOC con test), la tabla de skill de `p_sancion`.

### ADR-0013 — 22-08-2026 — Mayoría simple: el empate NO aprueba
1. `0013` · 2026-08-22 · umbral SIMPLE = ⌊emitidos/2⌋+1 con `>=`.
2. **Quién:** Valle lo detectó, Claude implementó (`0013:3`). [V]
3. **Estado declarado:** "Aceptada". **Real:** `agregador.umbral_aprobacion` devuelve `float(int(emitidos)//2+1)` (`agregador.py:117-123`); ABSOLUTA `miembros//2+1` (`:109-110`); decisión `aprob = (afirm >= umbrales) & con_quorum` (`:278`), umbral por simulación (`:274`). [V]
4. **Medición:** no aplica (reglamento). [V]
5. **¿Fuga/espejo?** No aplica. [V]
6. **¿Vigente en código?** Sí. **Test:** `modelo/agregador_institucional/tests/test_agregador.py:29-34` (200→101; **256→129**, "128 contra 128 es empate y NO aprueba"; **251→126**), log `log___modelo_agregador_institucional_tests_test_agregador_py.txt`: "OK — 55 chequeos". El presidente de la Cámara sigue sin modelarse como no-votante (sólo por presencia, `0013:30`). El JS del HTML usa `umbral_simulado` con corrección de continuidad `u-0.5` (`casos/nowcast_puertas_html.py:238-239`), coherente. [V]
7. **¿Doc coincide?** FORMULA `:179-187` sí; changelog `:2001` fecha el ADR el **13-08** (el ADR dice 22-08). [V]
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 3** (reglas del cuerpo, excepción 1 de la doctrina). **Sobrevive:** la regla ⌊E/2⌋+1 y su test. **Se pierde:** nada; el presidente queda como pendiente.

### ADR-0015 — 25-08-2026 — Todo cambio al motor se presenta en la fórmula (3 niveles)
1. `0015` · 2026-08-25 · función, motor en conjunto (quién lee, si mueve el número, contrato, supuesto), fórmula actualizada en el mismo commit.
2. **Quién:** Franco decide, Claude registra (`0015:3`). [V]
3. **Estado declarado:** "Aceptada". **Real:** se cumple **en la forma** (los tres commits que prendieron β, ε₀+τη y `RECORD_POR_TEMA` tocan FORMULA, ADR y tablero en el mismo commit), **no en el fondo** (§2). **Sin enforcement:** no hay hook (`.git/hooks` sólo `.sample`), ningún CI mira FORMULA; `COMMITEAR.ps1:6` es un script de un solo uso. [V]
4. **Medición:** no aplica (proceso). [V]
5. **¿Fuga/espejo?** No aplica; pero la regla **no pregunta** si la medición que justifica usó el motor real, fecha estricta u otra ley — que es exactamente lo que falló (§2). [V/I]
6. **¿Vigente?** Obliga por convención (CLAUDE.md "Regla del MOTOR"). [V]
7. **¿Doc coincide?** FORMULA §IV.8 (`:1894-1905`) y CLAUDE.md coinciden con el ADR. [V]
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 5** (medición y evidencia). **Sobrevive:** los tres niveles + "apagar deja el término marcado". **Debe agregarse:** un Nivel 0 — "la medición que justifica corre el motor real, fecha estricta, otra ley, IC por ley, y el control del número publicado tiene poder (no pegado a un techo)".

### ADR-0016 — 26-08-2026 (enmiendas 03-09 y 14-09) — Doctrina de la parte al todo
1. `0016` · 2026-08-26 · todo factor entra en P_i; la cámara es consecuencia; dos excepciones (reglas del cuerpo; shock común DENTRO de la simulación). Enmiendas: β del dictamen por legislador (03-09), sin carácter y PRENDIDO (14-09).
2. **Quién:** Franco (doctrina, `0016:3, :14-18`); enmienda 03-09 Franco (`:95`); prendido 14-09 Franco "dale, prendelo" (`:146`). [V]
3. **Estado declarado:** "Aceptada". **Real:** el camino activo cumple salvo los puntos de §1; dos ganchos agregados siguen en la cadena en cero; el HTML publicado la viola. [V]
4. **Medición:** doctrina sin medición. Las enmiendas sí: walk-forward 70/30 de `validar_beta_dictamen_walkforward.py` (`:123-133`) y GLM de `estimar_beta_dictamen.py`. [V]
5. **¿Fuga/espejo?** Doctrina: no aplica. **β: SÍ** — offset con `shift(1)` (`estimar_beta_dictamen.py:296-310`, hecho verificado); con offset limpio lealtad×jefe 1,75→1,29 (`0034:197-201`); el censo no aplica β. [V]
6. **¿Vigente?** Doctrina: obliga. β ON (`beta_dictamen.py:71`), pero no actúa en el número publicado (sin `proyecto_id`). [V]
7. **¿Doc coincide?** La "sección 'Auditoría de la doctrina' de FORMULA" que cita `0016:76-78` **no existe** (grep "Auditor" en FORMULA: sólo el changelog `:2005`); FORMULA no marca el nivel de cada término ni "deuda" (Consecuencia 1 incumplida). "Cuatro se corrigieron el mismo día" (`:76-78`): ε se corrigió el 16-09, ψ no se implementó, δ agregado sigue como identidad. [V]
8. **VEREDICTO: VIGENTE-ESTRUCTURAL** (la doctrina). Las enmiendas de β, separadas, serían **VIGENTE-EVIDENCIA-ROTA**.
9. **DESTINO: 3** (principal) + 2 (β va al voto individual) + 4 (excepción 2). **Sobrevive:** la regla y las dos excepciones, más "si un término va a la derecha de la simulación, está mal ubicado". **Se pierde:** el "0,9801 en los tres" como evidencia; la auditoría de 12 términos que no está escrita.

### ADR-0018 — 06-09-2026 — Guard de era en el récord individual (+ encoger, n≥1)
1. `0018` · 2026-09-06 · la era sale de la fecha del nowcast; encoger rec_i hacia s_ℓ (k=5); MIN_HIST 8→1; merge de ids.
2. **Quién:** Franco (`0018:9`). [V]
3. **Estado declarado:** "PRENDIDO POR DEFECTO". **Real:** `GUARD_ERA` ON (`nowcast_puertas.py:119`), `SHRINK_RECORD` ON (`:131`), `MIN_HIST_INDIVIDUAL=1` (`:97`); `era_de` usa `definiciones.era_de` (`:275-290`), no `bloque._GOBIERNOS` como dice el ADR (`0018:47`, ADR-0019 lo movió). Para cualquier nowcast del gobierno vigente la era deducida es 2023-12-10 = `ERA_FIJA` (`:121`): **el guard es un no-op en el producto**; sólo cambia backtests y el censo. [V]
4. **Medición:** `medir_guard_era.py` (espejo; listado en `0034:123`) y censo del 06-09 del harness con fuga: 0,1304→0,1611, valles 2015-19 y 2019-23 "cerrados" (`0018:123-133`). [V]
5. **¿Fuga/espejo?** **SÍ.** Con harness limpio 2019-2023 = 0,011 [−0,20; 0,11], desde 2023 = 0,010: los "valles cerrados" no se reproducen. [V hecho del contexto]
6. **¿Vigente?** Sí (arriba). **Nadie midió guard ON/OFF con el harness limpio:** `resumen_censo_limpio.reevaluar_adr0018` (`evaluacion/baseline/src/resumen_censo_limpio.py:99-127`) sólo compara encoger vs cortar y n≥8 vs n≥1 (`:116-117`); resultados en FORMULA `:67`: cortar +2,8% [1,8; 4,2] (**encoger, sólido**), n≥8 +0,5% [−0,01; 1,26] (borde). La mejor evidencia del guard es 0033 FASE 2: A1 0,092 vs A0 0,078 con fecha estricta **pero sin excluir la misma ley** y con brazos réplica (lote E `:18-19, :91`); 0031 es una correlación, no un Brier (lote E `:16`). [V]
7. **¿Doc coincide?** Encabezado (`:3-7`) dice "la objeción no se sostiene" por 0031 y no menciona 0033/0034; la nota final (`:164-176`) sí admite números inflados. FORMULA fila 4 (`:67`) y ESTADO-REAL:31 están al día; `tablero_datos.js:19` (hito viejo) repite 0,1304→0,1611 como confirmación. [V]
8. **VEREDICTO: VIGENTE-EVIDENCIA-ROTA** (el guard; el encogimiento, por separado, tiene evidencia limpia).
9. **DESTINO: 2.** **Sobrevive:** "el récord se encoge hacia el share de su linaje (k=5)" y "la era se deduce de la fecha, con el calendario de `definiciones`". **Se pierde:** 0,1304→0,1611, "valles cerrados", la tabla del merge; el guard queda como hipótesis a medir ON/OFF en el censo limpio.

### ADR-0025 — 16-09-2026 — ε₀ + τ·η_j: la incertidumbre baja al legislador
1. `0025` · 2026-09-16 · P̃_i = ε₀+(1−2ε₀)P_i; P_i^(j)=σ(logit P̃_i + τη_j), η_j común por simulación; se apaga el clip agregado; ε₀=0,035, τ=1,19.
2. **Quién:** Franco, "Hagamos el cambio"; antes "Asignale prioridad y resolvamos ese shock común" (`0025:3-6`, `:130`). [V]
3. **Estado declarado:** "IMPLEMENTADO, MEDIDO y PRENDIDO". **Real:** ON (`nowcast_puertas.py:192-196`, pasa a las dos cámaras `:848-852, :862-866`); τη_j implementado como shock común dentro de la simulación (`agregador.py:203-224`); clip agregado apagado (`ensemble.py:367-376`). Motor hoy: 0,6132 (`Archivos_Borrar/auditoria/panel_hoy.log`: 61,3%; con la bandera en 0: 98,0%). [V]
4. **Medición:** (i) sobredispersión 41× y ε₀ óptimo de `estimar_epsilon_tau.py` (2.485 actas) con récord `shift(1)` (`:103-104`) y `perfil` del harness (`:87`); (ii) escenario sintético; (iii) dos paneles que "se mueven en la dirección predicha" (`:138-150`). **Ninguna prueba fuera de muestra contra resultados antes de prender.** La cobertura 99,88% se corrió **después** ("no cambia la recomendación de activación, que ya estaba tomada", `:180-181`) con `agregador.backtest`, que usa la línea de bloque OBSERVADA del acta y sus votantes (`agregador.py:389-403`). [V]
5. **¿Fuga/espejo?** **SÍ** (offset espejo con fuga) **y oráculo** (cobertura). τ limpio = 1,197 (se sostiene); cobertura real 63,6% y −6,9 votos de sesgo (`0034:180-188`). [V]
6. **¿Vigente?** Sí. **Medición nueva del auditor** (`Archivos_Borrar/auditoria/contraste_aprobacion.json`): contra el resultado oficial de 5.831 actas, log-loss mejora 0,036 [0,018; 0,055] y las "seguras y equivocadas" bajan de 230 a 23; Brier no concluyente; **in-sample** (ε₀ y τ estimados sobre el mismo panel). La calibración por tramo muestra subconfianza en el centro (P 0,71 → real 0,79; 0,91 → 0,97): **mejora las colas, no el centro** — el pendiente 2 del ADR (`:197-198`) sigue abierto. [V]
7. **¿Doc coincide?** Ver §4: el ADR, FORMULA §III.A.3, EN-HUMANO 16-09 y el hito del tablero siguen diciendo 99,88%; el HTML publicado sigue en 0,9801. [V]
8. **VEREDICTO: VIGENTE-EVIDENCIA-ROTA** (la dirección queda parcialmente rehabilitada por el log-loss del auditor, in-sample).
9. **DESTINO: 4.** **Sobrevive:** "la incertidumbre se modela en P_i (encogimiento afín) y como shock común dentro de la simulación, nunca como clip del agregado". **Se pierde:** 99,88% "conservadora", "evidencia favorable en los tres frentes"; **se agrega:** la banda se mide con las P_i del motor, contra el recuento y contra el resultado, fuera de muestra.

---

## §1 — Cadena 0012 → 0016 → 0025: ¿el código HOY hace "de la parte al todo"?

| # | operación | dónde | nivel | con defaults | ¿cumple 0016? |
|---|---|---|---|---|---|
| 1 | rec_i, s_ℓ, d_i, π_i, β → P_i | `nowcast_puertas.armar_roster` `:648-688` | legislador | ON | sí [V] |
| 2 | piso `DESVIO_MIN_INDIVIDUAL=0.02` | `ensemble.py:318, :361`; desvío = 1−P_i vía `a_linea_y_desvio` (`nowcast_puertas.py:598-600`) | legislador (antes de simular) | ON: P_i ≤ 0,98 | en ubicación sí; pero es un **clip** (aplasta extremos) y se **apila con ε₀** (dos veces "nadie es certeza"): P̃ máx 0,946 en vez de 0,965 [V cálculo]. ε₀ se estimó **sin** ese piso (`estimar_epsilon_tau.py:87` usa `baseline_voto_individual.perfil`; grep `desvio_min` allí: 0) [V]. El propio argumento de 0025 contra apilar (`0025:51-54`) aplica. **No figura en §I.00** (sí en §I.3 `:315-323` atribuido a otro módulo y en constantes `:1924`). |
| 3 | ε₀ afín | `agregador.py:208-211` | legislador | ON | sí [V] |
| 4 | τ·η_j | `agregador.py:212-222` | shock común, un η por simulación para todos | ON | **sí: es la excepción 2** tal como la escribe `0016:67-70`. Supuesto no declarado: shock simétrico en logit baja la media si P_i altas (−6,9 votos, `0034:186-188`); mismo η en las dos cámaras, descartado al multiplicar marginales (hallazgo 3). [V/I] |
| 5 | umbral y quórum | `agregador.py:273-278` | regla del cuerpo | ON | excepción 1 [V] |
| 6 | clip agregado ε=0,01 | `ensemble.py:374-376` | agregado | OFF (eps=0 con la bandera) | reaparece: con `INCERTIDUMBRE_LEGISLADOR=0`; en `_via_sobre_tablas` (`nowcast_puertas.py:624-626`, no pasa ε₀/τ; OFF por `SOBRE_TABLAS`); y **vivo en el titular del HTML** (`casos/nowcast_puertas_html.py:240`) [V] |
| 7 | δ(carácter) `puerta_a.condicionar` | `nowcast_puertas.py:853, :867`; `puerta_a.py:396-416` | **agregado** (logit sobre P_c) | identidad (coef. 0, `puerta_a.py:101-107`) | **violación latente**: 0016 bajó δ a P_i y luego lo sacó, pero el gancho agregado sigue en la cadena; FORMULA fila 9 (`:72`) no lo marca como deuda doctrinal [V] |
| 8 | Manera 2 `ajuste_paso_origen(p0, delta, fe)` | `puerta_d.py:127-128, :195` | agregado | 0 (nowcast no pasa `delta`) | violación latente [V] |
| 9 | `_via_sobre_tablas`: `p_tablas × cond["p"]` | `nowcast_puertas.py:627-629` | agregado | OFF | violación latente [V] |
| 10 | P = P_B × P_D | `nowcast_puertas.py:873` | composición | ON | "tienen que pasar las dos" es regla; la **independencia** es supuesto "activo y falso" (FORMULA `:143-145`); "lo que hizo la otra cámara" debía entrar por P_i (`0016:9-10`) y ψ no está implementado (FORMULA `:77`) [V] |
| 11 | titular del HTML | `casos/nowcast_puertas_html.py:229-240, :278, :296-297` | agregado paralelo | ON en el producto | **viola 0016 y 0025**: normal bajo independencia, sin τη, clip, ICG sin signo [V] |

**Excepción 2 = τ·η_j:** sí, con la salvedad del sesgo en media y de que la correlación entre cámaras se pierde. [V/I]

## §2 — ADR-0015: ¿Nivel 2 cumplido en los tres commits que prendieron banderas?

| commit | FORMULA en el mismo commit | Nivel 2 escrito | Supuesto agregado sin querer y no declarado |
|---|---|---|---|
| `ec5fd05` 14-09 23:02, β | sí, 16 líneas: fila 12 pasa a PRENDIDO + párrafo §III.A.2 (`git show ec5fd05 -- …FORMULA`) | sólo "mueve el número publicado": "byte a byte idéntico… P=0,9801" (cuerpo del commit). Nada de quién lee, contrato ni supuesto | (a) β se estimó sobre un offset **distinto** del P_i del motor (espejo con `shift(1)`, sin guard/encoger/origen); (b) el censo no aplica β → queda sin medición; (c) el control "no se movió" no tenía poder: panel sin `proyecto_id` y P en el techo 0,99² [V] |
| `64ff248` 15-09 22:10, ε₀+τη | sí, 27 líneas: fila 13, §II.1, §III.A.3 (estado + dos paneles) | "mueve el número" sí (0,9801→0,6132 / 0,5277); **no regenera el HTML publicado** (no está en `--stat`; último commit del HTML `d9a7698` 14-09) | (a) shock simétrico en logit sesga la media; (b) apila con el piso 0,02; (c) ε₀/τ del espejo con fuga; (d) mismo η en ambas cámaras; (e) sin prueba fuera de muestra. El commit fecha 15-09 22:10 pero dice "medido desde el 16-09" [V; causa I: reloj/fecha] |
| `0a7a03f` 16-09 10:31, `RECORD_POR_TEMA` | sí, 35 líneas (fila 4, fila 18, §III.B.3) | no (lote D `adr_lote_D.md:57`) | **borra** de §III.B.3 el supuesto que debía frenar el 11,1%: "con el bloque en 95,4% de acierto, un término temático disputa como mucho el 4,6% restante" y "hay que medir antes cuántos llegan a n≥8" (diff del commit) [V]; los dos scripts de medición entran en el mismo commit que la activación [V] |

**Hipótesis confirmada.** [V/I] ADR-0015 exige PRESENTAR (función, radio, fórmula) y los tres commits lo hicieron en la letra. No exige VERIFICAR la medición que justifica el cambio: ningún ítem pregunta si midió el motor real o un espejo, si la historia es estricta, si la unidad es la ley, ni si el control "el número publicado no se movió" podía moverse. Además, el ítem "qué supuesto se agrega sin querer" se completó con descripciones del mecanismo, no con supuestos, y en un caso se usó para **sacar** una advertencia. Sin hook ni CI, la regla depende de quien escribe el commit, que es quien propone el cambio.

## §3 — ADR-0018 y el guard de era

- Evidencia del ADR: harness con fuga (0,1304→0,1611) y `medir_guard_era.py` (espejo marcado en `0034:123`). [V]
- **0031** (lote E `:16`): mide la correlación temática entre eras con tasa cruda, no el Brier del guard; 0033 la llama "error" (`evaluacion/baseline/src/record_por_origen.py:18`); nadie lo retracta y el encabezado de 0018 sigue citándola. [V]
- **0033** (lote E `:18-19, :91`): FASE 2 con fecha estricta pero **sin excluir la misma ley**, brazos réplica: sin guard +3,6% / B2 +3,9% (+44% en los primeros 180 días). Dirección favorable al guard, no re-corrida limpia. [V]
- **Harness limpio:** `reevaluar_adr0018` no tiene brazo guard ON/OFF (`resumen_censo_limpio.py:116-117`). **Nadie midió el guard encendido/apagado con el harness limpio.** [V]
- En producción el guard no cambia nada (era deducida = `ERA_FIJA` para el gobierno vigente, `0018:57`, `nowcast_puertas.py:121`); su efecto está en cómo se mide el modelo, no en el número publicado. [V]

## §4 — ADR-0025: qué dice cada documento sobre la banda y el número

| fuente | cobertura | número | ref |
|---|---|---|---|
| ADR-0025 hoy | **99,88%, "CONSERVADORA"**; sin enmienda, sin mención de 0034 | 0,9801 → 0,6132 | `0025:156-182` [V] |
| FORMULA | fila 13 y resumen: 63,6% (`:76`, `:90`, `:1985`, `:2028`); **§III.A.3 sigue en 99,88% "conservadora"** (`:1250-1254`) y "Queda para Franco" (`:1256-1258`); fila 7 "clip 🔴 corre pero está mal" (`:70`) y constante `P_INCERTIDUMBRE 🔴` (`:1925`), falsos con la bandera ON | — | [V] |
| EN-HUMANO | 28-09: "prometen 9 de cada 10 y aciertan algo más de 6" (`:18-19`); 16-09: 99,88% sin nota (`:262-270`) | "panel de referencia sigue en 61%" (`:20`) | [V] |
| `tablero_datos.js` | KPI `:253` 63,6% vs hito 16-09 `:316-318` 99,88% "ancho de más es mejor" | hitos viejos con 0,9801 (`:378`, `:393`, `:423`) | [V] |
| ESTADO-REAL | 63,6% (`:40`, `:70`) | — | [V] |
| `Nowcast-Puertas.html` | — | `"p_aprobacion": 0.9801`, commit `d9a7698` 14-09 (antes de prender ε₀+τη); el titular lo calcula el JS | [V] |

Decisión: Franco con "Hagamos el cambio" sobre una evidencia de sobredispersión medida con el espejo, un escenario sintético y dos paneles; la calibración vino después y con oráculo. [V]

## §5 — ADR-0006, 0007, 0008 y 0013 (resumen de lo pedido)
- **0006:** no se implementó la multitaxonomía por título. Lo que se llama así en el código es multi-etiqueta por proyecto; el nivel capítulo se hizo por 0023/0027/0029, quedó apagado y 0030 cerró la línea sin citar a 0006. [V]
- **0007:** el código entrega las dos respuestas (P + `a_negociar`) pero no el informe de 7 secciones, ni pivotes de comisión, ni archivo de corridas en `casos/`. [V]
- **0008:** vivo en el motor: nada. Vivo en el producto: el slider del HTML con γ pre-enmienda, neutro 1,90 y sin signo s. Además quedan en el árbol la serie `icg_contexto`, los estimadores de γ y `modulador_icg` sin consumidor. [V]
- **0013:** `agregador.py:117-123` + `:278`; test `test_agregador.py:31-34` (256 y 251 emitidos). [V]

---

## Notas finales

### (a) Contradicciones cuerpo/encabezado
- **0006:** encabezado "PENDIENTE (implementación)", pero hubo implementación parcial por otra vía (0023/0027/0029), ya cerrada (0030), sin registro en el ADR. [V]
- **0007:** "ACEPTADO (vigente)" con una sección 3 (P(recinto)) que 0012 eliminó y "skill 0,36" de la v1 (`:60`). [V]
- **0008:** "ACEPTADA (con enmienda)": el cuerpo (mecanismo 2, Consecuencia 1, tabla de γ) está dado de baja por la enmienda; los γ de la enmienda no son los del JSON vigente. [V]
- **0016:** remite a una sección "Auditoría de la doctrina" de FORMULA que no existe; "cuatro se corrigieron el mismo día" no es cierto para el código. [V]
- **0018:** el encabezado cita sólo 0031 ("la objeción no se sostiene"); la nota final (0033) admite niveles inflados; la Decisión 1 nombra `bloque._GOBIERNOS` y el código usa `definiciones`. [V]
- **0025:** encabezado "PRENDIDO" vs `:56-57` "Bandera única… apagada por defecto"; 99,88% sin corrección pese a 0034. [V]

### (b) Contenido o código que ya no vale y sigue en el árbol
- `modelo/ensemble/src/backtest_cadena.py` (550 LOC, `main` neutralizado) + `tests/test_backtest_cadena.py` (330 LOC, 53 checks en CI sobre la v1). [V]
- `ensemble.py`: stubs de la v1 (`:302-304`, `:383-395`), docstring obsoleto `:342-343` ("sigue siendo el default porque epsilon0/tau están apagados"). [V]
- `puerta_a.py` (444 LOC): `delta_caracter`/`condicionar`/`estimar_delta_caracter` (`:373-444`, ~70 LOC) = identidad en la cadena; `puerta_d.py` parámetros `delta`/`factor_encogimiento` y Manera 2 (`:127-128`, `:195-202`) sin uso. [V]
- `nowcast_puertas.py:656-661`: docstring "BETA_DICTAMEN apagada… el carácter del despacho" (β está ON y sin carácter). [V]
- Línea ICG sin consumidor en el motor: `modulador_icg.py` 254, `comparar_vias_icg.py` 298 (neutralizado), `icg_contexto.py` 264, `estimar_gamma.py` 155, `estimar_gamma_individual.py` 232, tests 143+140 (≈1.490 LOC). El slider del HTML (`casos/nowcast_puertas_html.py:44, :226-230`) con parámetros viejos. [V]
- `Nowcast-Puertas.html` (157 KB, P=0,9801, anterior a ε₀+τη). [V]
- `modelo/agregador_institucional/outputs/backtest_calibracion_epsilon0_tau_2026-09-16.json` (99,88%, oráculo) y `agregador.backtest` (`:338-450`) sin advertencia de línea observada. [V]
- `evaluacion/baseline/src/medir_guard_era.py` (199 LOC, espejo con fuga; sus tablas siguen en 0018:69-77). [V]
- FORMULA: fila 7 (`:70`), §I.1 (`:149-154`), constante `:1925`, §III.A.3 `:1250-1258`, changelog `:2001` (fecha de 0013). EN-HUMANO `:262-270`; `tablero_datos.js:316-318`, `:59`, `:230`. [V]

### (c) Veredicto sobre la doctrina de la parte al todo (≤120 palabras)
El motor, en el camino que produce P(sanción) con los defaults, cumple la doctrina en lo que se mueve: todo lo activo entra por P_i (récord, β, ε₀) o es regla del cuerpo, y τ·η_j es el shock común de la excepción 2. No la cumple en cuatro puntos: (1) dos ganchos agregados siguen en la cadena, en cero y sin marcar como deuda (`condicionar`, `ajuste_paso_origen`); (2) el piso 0,02 recorta cada P_i a 0,98, se apila con ε₀ y no figura en §I.00; (3) P_B×P_D multiplica marginales bajo una independencia que FORMULA declara falsa, y tira el η común; (4) el titular del HTML publicado lo recalcula JavaScript con clip agregado, sin τη y con ICG.
