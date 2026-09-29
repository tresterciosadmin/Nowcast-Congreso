# Auditoría lote E — ADR-0029, 0030, 0031, 0032, 0033 (línea tema / capítulo / origen)

Auditor: Claude (Sonnet 5.5), sólo lectura, 28-09-2026. No se corrió ningún script ni test.
Convención de confianza: **[V]** verificado (lectura de código/dato/git, con referencia) · **[I]** inferido · **[N]** no verificado.
Rutas relativas a `Nowcast Congreso Argy/`. Los números de línea son de hoy.

## 0. Respuestas directas a las preguntas especiales

**(i) Datos parciales de 0029 en producción: NINGUNO.** [V]
- `tema_por_capitulo.parquet`, `capitulos_nombre.py`, `composicion_capitulos.py`: sus únicos consumidores son tests, `evaluacion/baseline/src/{validar_leybases_por_capitulos,validar_piloto_capitulos,validar_piloto_titulos,prueba1,prueba2}.py` y un docstring (`modelo/agregador_institucional/src/agregador.py:189`). Grep sobre `*.py`, `REGENERAR.ps1` y `../.github/workflows/*.yml`: cero enganches.
- `proyecto_taxonomias` (+328 proyectos; `datos/proyectos/data/taxonomias.csv` 3.340 líneas, `datos/taxonomias/data/asignaciones.csv` 10.112): se lee sólo vía `nowcast_puertas._resolver_multietiqueta` (`:222`), llamada desde `_tema_auto` (`:256`, guardada por `TEMA_AUTO` OFF `:155`) y desde `nowcast()` (`:809-811`, guardada por `RECORD_POR_TEMA` OFF `:219`). Además el panel de REGENERAR no pasa `proyecto_id` (`REGENERAR.ps1:291-292`), así que devolvería `[]`.
- `tema_por_acta.parquet` (el que SÍ se usa en producción cuando se pasa `origen`, vía `bloque.cargar_tema_por_acta`) tiene mtime 07-09, anterior a 0029: 0029 no lo tocó [I: mtime].
- Ninguna corrida llama a la API de Anthropic (grep `ANTHROPIC|agente_taxonomias|tema_por` en `.github`: 0).

**(ii) 0031 y 0033 vs ADR-0018 y la fuga.**
- 0031 FASE 1 (`medir_estabilidad_record_por_tema.py:112-117`): correlación entre ventanas disjuntas antes/después de cada recambio; no es un predictor, no usa `shift(1)` ni historia por fila. **No depende de la fuga.** [V] Pero su codificación es la tasa afirmativa CRUDA, y 0033 la llama "el error de ADR-0031" (`evaluacion/baseline/src/record_por_origen.py:18`: mezclar los grupos da ~0 aunque ambos sean predecibles). Ningún ADR lo retracta; `0018:3-7` sigue diciendo "la objeción no se sostiene". [V]
- 0033 FASE 1 (persistencia de ρ): ventanas disjuntas + IC más ancho de bootstrap Poisson por expediente y por legislador: **no depende de la fuga.** [V]
- 0033 FASE 2 (censo, brazos): historia "estricta" = sólo FECHA anterior (`record_por_origen_brazos.py:81-97`, quita el mismo día); **no excluye la misma ley de fecha anterior**; los brazos son una réplica propia del récord (`_previos`) sobre `censo_detalle_2026-09-27.parquet` del harness espejo (`:45`). ESTADO-REAL fila 20: "parcial (fecha sí; misma ley no)". También se reporta la variante `--historia harness` (con fuga): misma conclusión (`0033:133-134`). [V] Los scripts de 0033 no figuran en la lista de espejos marcados de 0034 (`0034:119-126`) y no se re-corrieron. [V]
- El guard de era (ADR-0018, ON `nowcast_puertas.py:119`) hoy NO tiene una medición on/off con el harness limpio: 0034 re-evaluó sólo encoger vs cortar y n>=8 vs n>=1 (`0034` FORMULA `:749-752`). La mejor evidencia post-fuga del guard es 0033 FASE 2 (A2 vs A0o: +3,6% sin guard, fecha estricta, sin "otra ley", brazos réplica). **Evidencia PARCIAL.** [V/I]

**(iii) Método split-half por expediente de 0032: reutilizable como PRINCIPIO, no como código.** [V]
`firma_tematica_fase1_2.py::_mitades/split_half` (`:225-275`) tiene: (1) un solo corte `crc32(expediente)%2` sin repeticiones ni IC (la versión de 0033, `record_por_origen.py::split_half:404-450`, repite 20 veces); (2) clave = `tema_por_acta.expediente` sola (`:254`), no `ley_por_acta` (union-find de 3 tablas, `baseline_voto_individual.py:273-308`); (3) `str(NaN)` → 'nan': todas las actas sin expediente caen en la MISMA mitad (`:272-273`; sólo se corta si <50% de las con tema tienen expediente, `:268`); (4) 2019-23 y 2023 quedan "n/d". Además el IC de persistencia de 0032 es bootstrap por LEGISLADOR (`:30-46`), contra su propio titular "la unidad es la ley". Ensancharlo sólo refuerza el nulo (mata el único IC que excluía 0, tercil medio +0,12 [0,04; 0,21]). Reutilizable: `record_por_origen.py` (`split_half`, `bootstrap` Poisson `:343`) + `ley_por_acta`.

**(iv) 0030: qué queda vivo y `diagnostico_senado.py`.**
- Vivo: nada de motor. Tres scripts de medición (685 LOC), `tema_por_capitulo.parquet` y `composicion_capitulos.py` "construidos y apagados" (`0030:220-224`), un camino de reapertura (PRUEBA 2) sin ejecutar. [V]
- `diagnostico_senado.py` TIENE LA FUGA: `:87-97` récord `shift(1).expanding()` por fila, sin guard de era, sin encoger, sin origen; marcado "ESPEJO VIEJO" en el propio archivo (commit bf831aa). Fue creado el 06-09 (2dbad10), antes de 0030; ADR-0030 no lo corrió, pero sus cifras del Senado (68,8% desvío en el piso, 47,0% P_i extremas, 58% en el bin superior, valle 2019-23 −0,069) coinciden una a una con `evaluacion/baseline/outputs/diagnostico_senado.json` (03-09: 0,6879; 0,4701; 24.762/42.596; −0,0686). [V]
- La causa que 0030 le atribuye a la saturación ("`DESVIO_MIN_INDIVIDUAL` ES la estimación para dos tercios") no está establecida: en el mismo JSON, `fuente_direccion` da 98,5% récord (41.969/42.596) y `perfil_legislador` ignora el desvío cuando hay récord (`nowcast_puertas.py:569-577`). [V/I]
- Skill del Senado: 0030 cita 0,072→0,120; hoy 0,108 (Diputados 0,126) (`0034:143-144`): la brecha "la mitad" casi desaparece.

**(v) Cambios de código que corren hoy.** Ninguno de los cinco ADR deja lógica activa en el camino de P(sanción) con los defaults, salvo lo que ya era de 0018. [V]
- 0031: `nowcast_puertas.py:385-495` (`devolver_stats`, `_salir`, logs) y `:910-915` (payload `record_por_tema`). El código está cargado, pero `record_legisladores` (`:519-525`) sólo llama a la función si `RECORD_POR_TEMA` (OFF), y el payload sale `{"activo": False}`. Nadie en `casos/` ni `producto/` lee esa clave. Observabilidad "prendida" = dormida.
- 0029: `tema_por_proyecto.py` (`--desde-fecha`, `denominadores_desde`) sólo CLI; datos sin lector.
- 0030 y 0032: cero código de motor (`git show --stat 9dda9f5, 141729b`).
- 0033: `baseline_voto_individual.py` +10 líneas aditivas; luego reescrito por 0034 (bf831aa).

**(vi) Reglas que sobreviven y cómo reabrir**: ver cada ficha y el punto (c).

---

## 1. Fichas por ADR

### ADR-0029 — Tema por capítulo + cobertura ampliada, PARCIAL sin crédito de API (16-09-2026)
1. `0029` · 16-09-2026 · "Tema por capítulo + ampliar cobertura — PARCIAL, sin crédito de API". [V] `0029:1-3`
2. **Quién decidió:** Claude con permiso puntual de Franco: "Sí, alcance acotado" / "Sí, ampliar cobertura" / "Sí, córranlo" (`0029:5-6`); recarga de crédito, foco en Ley Bases, pausa de la cobertura ampliada y "avanzá en el punto 1" también por pedido explícito (`0029:189-192, 250-251`, `ESTADO:104,120`). [V]
3. **Estado declarado vs real:** declara "CÓDIGO IMPLEMENTADO y TESTEADO, DATOS PARCIALES (sin crédito)" (`:3-5`). Real: crédito recargado el mismo día (`:245`); Ley Bases 63/63; `tema_por_capitulo.parquet` 471 filas (`0030:220`); cobertura ampliada PAUSADA (`:250`); línea cerrada por `0030:3` y `0031:205-208`. El encabezado quedó viejo. [V]
4. **Medición:** no hay medición de skill. Tres validaciones de plausibilidad: `validar_leybases_por_capitulos.py` (n=3; corte 2024-02-01, `:59`), `validar_piloto_capitulos.py` (0/20 con resultado real por capítulo), `validar_piloto_titulos.py` (25 títulos, 5 proyectos; r=−0,95 empujado por 2 títulos de Ley Bases; corte = fecha mínima − 5 días, `:134-135`). Historia: `alineacion_individual(votos, {}, None, hasta=fecha)` (`validar_piloto_titulos.py:80`). [V]
5. **¿Depende de fuga/espejo?** No por fuga (el margen de 5 días esquiva el `<=`); PARCIAL por espejo: llama al motor con `origen=None` y `origen_map={}` (producción condiciona por origen, `nowcast_puertas.py:317-319`). Y no mide skill: n=3. [V]
6. **¿Vigente en código?** Sí como archivos, no como camino: cero consumidores productivos (ver 0.(i)). Nada de esto llama P(sanción) con los defaults. [V]
7. **¿Documentación coincide?** FORMULA III.A.6 (`:1599-1618`) coincide ("NO enganchado a producción"); EN-HUMANO `:97-203`, tablero coinciden. Contradicen: `0029:98-101` ("ya alimenta RECORD_POR_TEMA/TEMA_AUTO… mecanismo que ya estaba prendido"): `TEMA_AUTO` nunca estuvo prendido (`nowcast_puertas.py:142-155`) y `RECORD_POR_TEMA` se apagó el 28-09 (`:219`); ESTADO conserva la entrada base "437/704 y 328/9.910" (superada por las siguientes); `0030:220` dice 105 proyectos, `ESTADO:116` "~100". [V]
8. **VEREDICTO: INACTIVO** (código y datos sin enganche; lo que documenta ya lo cerró 0030).
9. **DESTINO: 6** (con la definición de clave en 1). **Sobrevive:** clave de capítulo = `(proyecto_id, titulo_num, capitulo_num)`, porque el numeral se reinicia por título (bug real: "Capítulo I" bajo 6 títulos en Ley Bases, `0029:117-152`); medir antes de escalar el gasto de API. **Se pierde:** la cobertura ampliada como "insumo vivo", los 437→242→471 conteos, y la afirmación de que alimenta el récord.

### ADR-0030 — Cierre de la línea de capítulos/pivotes + diagnóstico del Senado (17-09-2026)
1. `0030` · 17-09-2026 · cierre de pivotes por capítulo (PRUEBAS 1-3) y diagnóstico Senado "preparado, no ejecutado". [V]
2. **Quién decidió:** Claude, sesión de veredicto "explícitamente delegada por Franco" (`PROMPT-DECIDIR-CAPITULOS.md`, `0030:4-7`); conservar artefactos = "decisión explícita de Franco, ya tomada" (`:220-224`). [V]
3. **Estado:** declara "CERRADA (pivotes por capítulo, esta ronda)". Real: cerrada, y 0031 la pasa a "CERRADO definitivo" (`0031:205`). PRUEBA 2 (camino de reapertura), pendientes 2-4 y el diagnóstico del Senado: sin ejecutar. Pendiente 1 (observabilidad) lo resolvió 0031 (dormida). [V]
4. **Medición:** `prueba1_pivotes_por_capitulo.py` (322 LOC: fracción de pares (legislador, capítulo) con n^área>=1 en Ley Bases al 2024-02-01, con funciones reales del motor), `prueba2_reconstruccion_por_rango.py` (204: cuenta proyectos reconstruibles), `prueba3_cobertura_universo_vivo.py` (159: cobertura). Ninguna mide skill. Diagnóstico Senado: cifras de `diagnostico_senado.json` (03-09), ver 0.(iv). [V]
5. **¿Depende de fuga/espejo?** PRUEBAS 1-3: no aplica (recuentos de cobertura; el 0,0% es dato disponible, no skill). Diagnóstico Senado: SÍ (récord `shift(1)` por fila, sin guard/origen, `diagnostico_senado.py:87-97`; skill citado 0,072→0,120 sale del censo con fuga). [V]
6. **¿Vigente en código?** Ningún cambio de motor (`git show --stat 9dda9f5`: 3 scripts + docs). Nada llama a P(sanción). [V]
7. **¿Doc coincide?** FORMULA `:673, :1887`, ESTADO `:95-101`, EN-HUMANO `:97-135`, tablero coinciden en el cierre. Contradicciones dentro del ADR: `0030:99-101` "ADR-0026 sigue en pie, validado y prendido… POSITIVO incluida la era desde 2023" (falso desde 0034: −2,1% total, −10,8% desde 2023, `0034:164`); `0030:283-284` "BETA_DICTAMEN (ADR-0016, apagado por defecto)" contra `modelo/ensemble/src/beta_dictamen.py:71` (default "1", prendido desde el 14-09; `modelo/ensemble/README.md:27,198`; `tests/test_beta_dictamen.py:85`): falso ya al escribirse. [V]
8. **VEREDICTO: REGISTRO-HISTÓRICO.**
9. **DESTINO: 6** (cierre) + reglas a **5**. **Sobrevive:** (a) antes de medir skill de un mecanismo condicionado, medir la fracción con dato condicionado REAL (gate 1.1, `0030:73-111`) — es la regla que hoy encarna "todo fallback avisa" (FORMULA IV.7 `:1887,1890-1892`); (b) criterios de decisión escritos antes de medir; (c) cobertura del universo no votado mueve capacidad de respuesta, no Brier (`:171-205`). **Se pierde:** diagnóstico del Senado con sus cifras (0,072/0,120, 68,8%, "DESVIO_MIN es la estimación"), "ADR-0026 prendido", "BETA apagado".

### ADR-0031 — El récord temático no es más estable que el general; el fallback deja de ser silencioso (17-09-2026)
1. `0031` · 17-09-2026 · "objeción al guard testeada y no sostenida; fallback observable". [V]
2. **Quién decidió:** Claude, sesión delegada por Franco (`PROMPT-GUARD-DE-ERA-POR-TEMA.md`, `0031:6`); FASE 3 "aprobada así por Franco" (`:28-29`); la objeción es de Franco (`ESTADO:88`). [V]
3. **Estado:** declara "FASE 1 NO SOSTENIDA (guard sin cambios). FASE 3 IMPLEMENTADA Y PRENDIDA". Real: FASE 1 vigente sólo como resultado sobre una codificación cruda (0033 la califica de "error", `record_por_origen.py:18`), sin retractación; FASE 3 cargada pero inalcanzable con defaults (`nowcast_puertas.py:519-525`, `:915`). "Prendida" = dormida. [V]
4. **Medición:** `medir_estabilidad_record_por_tema.py` (304 LOC): Pearson por par (legislador, área) entre ventanas antes/después de 3 recambios, EB k=5, n>=3/5/10 (`:112-152`). Sin IC, sin cluster por ley, sin walk-forward. Salida `medir_estabilidad_record_por_tema_2026-09-17.json`. [V]
5. **¿Depende de fuga/espejo?** No (no predice; ventanas disjuntas). Defectos propios: (i) codificación cruda (0033: crudo −0,35 vs relabelado +0,54); (ii) unidad = par, no ley (3,45 actas por ley comparten tema); (iii) en 2023 —la era del producto— la temática le gana a la general por +0,26 (+0,053 vs −0,206), del lado contrario al pooled (−0,098), y la decisión se tomó sobre el pooled sin IC. [V]
6. **¿Vigente en código?** Rige el guard (ON `:119`, es ADR-0018). FASE 3 dormida (arriba). [V]
7. **¿Doc coincide?** FORMULA §II.5 `:658-678` coincide con el ADR pero presenta `frac_condicionado_real` como expuesto sin decir que con `RECORD_POR_TEMA` OFF es `activo: False`; `ESTADO:92` "observabilidad… prendida en producción" ya no describe el default; `0018:3-7` no menciona 0033/0034; ESTADO-REAL no tiene fila para esto. [V]
8. **VEREDICTO: REGISTRO-HISTÓRICO** (FASE 1 = resultado negativo puntual; FASE 3 = INACTIVO de facto).
9. **DESTINO: 6** (registro de codificaciones descartadas) + regla a **5**. **Sobrevive:** todo fallback degrada CON aviso agregado y el aviso viaja en el payload. **Se pierde:** "el guard queda confirmado también para el tema" como afirmación general (sólo vale para tasa cruda); las áreas estables (SALUD/TRAB/EDU +0,45 a +0,58) como pista huérfana.

### ADR-0032 — Firma temática del desvío: formulación descartada, línea abierta (21-09-2026)
1. `0032` · 21-09-2026 · "esta formulación no capta lo que pasa; el motivo es la ley, no el tema". [V]
2. **Quién decidió:** Claude, sesión delegada (`PROMPT-FIRMA-TEMATICA-DEL-DESVIO.md`, `0032:3-4`); el veredicto lleva "las palabras que pidió Franco" (`:11`); "línea NO cerrada (instrucción de Franco)" (`ESTADO:85`). Desvío del prompt declarado: "contestada" (minoría >=10%) en lugar de "disputada" (±5%) (`:22-26`). [V]
3. **Estado:** "MEDIDO, sin cambios en el motor". Real: coincide; `gobernadores.csv` aislado por test (`evaluacion/baseline/tests/test_firma_tematica.py:75-81`). Tensión entre documentos: 0032 dice "no se cierra", 0030/0031 cierran la línea de tema y el plan consolidado la marca "cerrada". [V]
4. **Medición:** `firma_tematica_desvio.py` (118), `_fase0_celdas.py` (68), `_fase1_2.py` (303). Usa el desvío v2 del motor (`disciplina.marcar_desvios`, `:63-66`), Pearson entre eras por (legislador, área), IC por legislador, split-half `_mitades`. No usa el harness de predicción. [V]
5. **¿Depende de fuga/espejo?** No aplica (no predice). El IC por legislador subestima, pero el resultado es un nulo (+0,015 [−0,03; 0,06]) y ensancharlo lo refuerza. [V/I]
6. **¿Vigente en código?** No: ningún consumidor (test lo garantiza). `RECAMBIOS`/`era_de` propios (`firma_tematica_desvio.py:30,51-56`) en vez de `definiciones`. [V]
7. **¿Doc coincide?** FORMULA §IV.6 `:1841-1865` lo eleva a regla (coincide). Problemas: "~1,7×" (`FORMULA:1845`, `0034:38`) no está derivado en 0032 ni en ninguna medición que encontré [N]; `FORMULA:1952` atribuye a ADR-0032 los "SE por ley 3-4× más anchos", que salen de `chequear_direccion_beta.py` (ADR-0034) [V]. EN-HUMANO/tablero `:278` coinciden.
8. **VEREDICTO: REGISTRO-HISTÓRICO** (la firma no gobierna nada; su método vive en FORMULA §IV.6).
9. **DESTINO: 5** (regla del expediente + split-half) y **6** (registro de descartadas; la candidata "con quién se desvía", par a par, queda abierta por instrucción de Franco). **Sobrevive:** un rasgo intra-era sólo cuenta si sobrevive a una partición por ley entera; desempate aleatorio en top-k (el `nlargest` daba un +0,069 falso). **Se pierde:** d̃ por (legislador, área), la definición "contestada", `gobernadores.csv` (2011-2019 sin verificar).

### ADR-0033 — Récord por origen relabelado: persiste pero no mejora; el harness filtra el mismo día (27/28-09-2026)
1. `0033` · 27-28/09/2026 · ρ relabelado cruza el recambio pero es memoria de linaje; el guard sigue; colateral: fuga. [V]
2. **Quién decidió:** Claude, sesión delegada por Franco (`PROMPT-RECORD-POR-ORIGEN.md`, `0033:3-4`); regla "no se prende, no se esconde" (`:27-29`); el colateral queda como "decisiones de Franco" (`:197-198`). Dos desvíos del prompt declarados (`:62-71`). [V]
3. **Estado:** "MEDIDO, sin cambios en el motor". Real: correcto (commit daf9474 sólo toca `evaluacion/baseline` + docs). Los NIVELES (0,173 / 0,092 / 0,193) los superó 0034 (0,1333 / 0,010); ESTADO-REAL fila 20: "parcial (fecha sí; misma ley no)". [V]
4. **Medición:** FASE 1 `record_por_origen.py` (518 LOC): ρ antes/después por recambio, EB k=5, IC = más ancho de (Poisson por expediente, por legislador), split-half por acta/expediente/sesión. FASE 2 `record_por_origen_brazos.py` (400): A1/A2/A0o/B1/B2 sobre `censo_detalle_2026-09-27.parquet`, `--historia estricta` (default CLI `:333`) = fecha anterior. [V]
5. **¿Depende de fuga/espejo?** FASE 1: no. FASE 2: PARCIAL: fecha sí, misma ley de fecha anterior no (0034: 0,0916 → 0,0742 sólo por excluir ley); brazos = réplica del motor (A2 "espejo del motor"); no re-corrida. La dirección (B1 ≈ 0; residuo individual ≈ 0) no depende del nivel; el "+3,6% sin guard" y "B2 +3,9% / +44%" no están re-medidos limpios. [V/I]
6. **¿Vigente en código?** ρ_her/B1/B2 no existen en el motor (grep `rho_heredado|record_por_origen` en `modelo/ variables/ casos/ producto/ datos/`: 0 archivos). Lo que rige por otra vía: guard ON (`:119`), récord por origen (`_alineacion_base :317-319`, sólo con `origen`; REGENERAR pasa EJECUTIVO). [V]
7. **¿Doc coincide?** FORMULA fila 20 (`:83`) y §II.5 `:680-765` coinciden; `:702` ("0,173 vs 0,092") lo supera `:742-747` en el mismo apartado. `ESTADO:73` ("revisar el 11,1%… PRENDIDO") superado por 0034. `tablero_datos.js:273` repite "0,161 a 0,092" (vigente `:252` 0,1333; el 0,0742 con otra ley no figura). `ESTADO-REAL:55` "guard… ya con historia por fecha" omite "otra ley". [V]
8. **VEREDICTO: REGISTRO-HISTÓRICO** (ρ_her probado e inactivo; hallazgo descriptivo sólido; su respaldo al guard es parcial).
9. **DESTINO: 2** (voto individual: entre gobiernos sólo cruza el linaje relabelado; guard y récord por origen) y **5** (IC "el más ancho de dos bootstraps"; colateral de fuga ya en 0034). **Sobrevive:** "lo individual no persiste entre gobiernos; lo que persiste es el rol/linaje, y el motor lo reaprende en semanas"; "no se prende lo que predice peor y se deja la discrepancia escrita". **Se pierde:** B1/B2/ρ_her como candidatos, los niveles de skill de la FASE 2, `record_por_origen_brazos.py` atado al detalle del 27-09.

---

## 2. Notas finales

### (a) Contradicciones entre cuerpo y encabezado de un mismo ADR
- **0029:** encabezado/título "PARCIAL, sin crédito" vs cuerpo "crédito recargado", Ley Bases 100% (`:245-248`); `:98-101` "TEMA_AUTO ya estaba prendido" vs `nowcast_puertas.py:155`; universo 9.910 (`:24`) vs 9.962 (0030) vs "9.582 esperando" (`:194`); 328 clasificados vs 273 con tema (0030).
- **0030:** "sigue en pie, validado y prendido" (`:99-101`) y "BETA apagado" (`:283-284`) contradicen el código; `Estado: CERRADA (esta ronda)` vs 0031 "CERRADO definitivo" vs PRUEBA 2 "camino abierto".
- **0031:** "guard confirmado" vs prueba que es de correlación, no de Brier; criterio "brecha >=+0,15" se cumple en 2023 (+0,26) y se decide con el pooled; "PRENDIDA" vs dormida.
- **0032:** "la unidad es la ley (310 leyes)" vs IC por legislador (`firma_tematica_fase1_2.py:30-46`) y 310/3,45 contado sólo con `tema_por_acta.expediente` (2019+ casi sin vínculo); "línea NO cerrada" vs "línea de tema cerrada".
- **0033:** "el que vale" = historia estricta, pero 0034 muestra otra más estricta; ADR-0018:173-176 "guard sigue ganando (A1 0,092 vs A0 0,078)" es fecha-estricta, no otra-ley.

### (b) Contenido/código que ya no vale y sigue en el árbol (LOC aprox., con tests)
- 0029: `tema_por_capitulo.py` 280 + test 187 · `capitulos_nombre.py` 211 + test 115 · `composicion_capitulos.py` 145 + test 161 (ADR-0027) · `validar_{leybases,piloto_capitulos,piloto_titulos}` 187+225+195 = 607 · `tema_por_capitulo*.parquet` (21 KB + 18 KB "OBSOLETO") ⇒ **~1.700 LOC**.
- 0030: `prueba1/2/3` 322+204+159 = 685 · `diagnostico_senado.py` 224 (fuga, `.json` del 03-09) ⇒ **~910 LOC**.
- 0031: `medir_estabilidad_record_por_tema.py` 304 (copia propia de RECAMBIOS, `:53`) · `alineacion_individual_por_area` + payload dormidos ~111 LOC de código y 203 de test ⇒ **~620 LOC**.
- 0032: `firma_tematica_*` 489 + test 81 · `gobernadores.csv` 97 líneas sin verificar ⇒ **~570 LOC**.
- 0033: `record_por_origen.py` 518 + `record_por_origen_brazos.py` 400 + test 136 ⇒ **~1.050 LOC**; reciclable: `split_half`/`bootstrap` de `record_por_origen.py` y `censo_detalle_paralelo.py` (96, vivo).
- Total lote: **~4.850 LOC**, casi todo medición o código sin enganche.

### (c) ¿Esta línea deja algo en pie? (<=100 palabras)
Deja tres cosas, ninguna es un mecanismo: (1) guard de era y récord por origen, vigentes, con evidencia post-fuga parcial (0033 FASE 2: fecha estricta, sin otra ley, brazos réplica); (2) reglas de método (unidad = ley, split-half por expediente, gate de fallback, criterios previos); (3) el hallazgo de que entre gobiernos sólo persiste memoria de linaje. Para reabrir: `censo_detalle_paralelo.py` limpio (~34 min) con `GUARD_ERA` 0/1 y con récord temático relabelado por lado; criterio ΔBrier<0, IC por leyes que excluya 0, total y desde 2023; gate: >=50% de votos con dato condicionado real.

**Medición mínima por sub-línea:** (1) guard: on/off en el censo limpio (mismos 691.845 votos). (2) tema: variante `record_por_tema` ya soportada por el censo, más versión relabelada; gate de cobertura en la era vigente. (3) capítulos: sólo si PRUEBA 2 ampliada (regex "ARTS." + control de monotonía por PDF) da >=20 leyes con resultado por capítulo; P_k con `nowcast()` real, corte `<`, IC por ley. (4) firma: "con quién se desvía" par a par, partición por ley entera, >=100 leyes efectivas.

### Hallazgos colaterales fuera del lote
- `nowcast_puertas.py:832-833` dice "BANDERA APAGADA POR DEFECTO" para `BETA_DICTAMEN`; el default es ON (`beta_dictamen.py:71`). Comentario viejo, misma confusión que 0030.
- La evidencia numérica de ADR-0018 (0,1304→0,1611; valles "cerrados" 2015-19 y 2019-23) proviene del harness con fuga; con harness limpio 2019-23 = 0,011 [−0,20; 0,11] y desde 2023 = 0,010. Nadie midió el guard on/off limpio.
- `record_por_origen_brazos.py:45` apunta al parquet del 27-09 (harness espejo), no al del 28-09.
