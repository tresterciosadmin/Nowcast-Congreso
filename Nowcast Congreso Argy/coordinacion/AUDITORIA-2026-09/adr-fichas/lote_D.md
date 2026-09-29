# Auditoría lote D — ADR-0023, 0024, 0026, 0027, 0028 (multietiqueta, récord por tema, capítulos)

Auditor: Claude (Sonnet 5.5), sólo lectura, 29-09-2026. No se corrió ningún script de medición, censo ni test (sí se leyeron JSON/parquet con pandas para reproducir cifras descriptivas; ver [V*]).
Convención: **[V]** verificado (código/dato/git con referencia) · **[I]** inferido · **[N]** no verificado.
Rutas relativas a `Nowcast Congreso Argy/`. Números de línea = HOY salvo que se diga commit. Leí el lote E (`adr_lote_E.md`) y no lo repito; donde hay solape de LOC se marca.

---

## 0. Respuestas directas a las preguntas especiales

### (i) 0024 → 0028 y 0026 → 0034: ¿los encabezados reflejan el estado real? ¿hay ADR "prendido/aplicado/implementado" que ya no lo esté?

- **0026 → 0034: el banner es correcto pero el encabezado no.** `0026:14-19` dice "RECORD_POR_TEMA está APAGADO" y es cierto (`modelo/ensemble/src/nowcast_puertas.py:219`, default "0"). Pero la línea **Estado** (`0026:3-4`) sigue diciendo "IMPLEMENTADO, MEDIDO sobre el censo completo y **PRENDIDO** (`RECORD_POR_TEMA=1` por defecto)", y la sección "Activación" (`:114-126`) y "positivo en TODOS los cortes" (`:108-112`) no llevan marca. [V]
  Restos vivos que siguen diciendo "prendido": comentario `nowcast_puertas.py:198-208` ("PRENDIDA POR DEFECTO desde el 16-09"; el párrafo del 28-09 está debajo, `:210-218`), docstring de `_resolver_multietiqueta` (`:226-230`: "uno sigue apagado… y el otro prendido (positivo a nivel legislador)"), `FORMULA-COMPLETA.md:308` ("+11,1%, sin ningún corte negativo" como "ganancia real"), `FORMULA-COMPLETA.md:1650-1666` (cuerpo de III.B.3 "prendida por defecto / 11,1%", bajo el banner de `:1640-1648`) y `FORMULA-COMPLETA.md:82` (fila 19: "La ganancia real está en la fila 18"; la fila 18 es `:81` y dice APAGADO). [V]
- **0024 → 0028: el banner (`0024:1-13`) es parcialmente falso hoy y contradice el cuerpo.** Dice que 0028 "da un resultado MÁS FUERTE, no contradictorio" y que "no es que las reglas nuevas empeoren", pero el cuerpo (`0024:131-132`, `:174-178`) sigue afirmando "🔴 NEGATIVO. Las TRES reglas nuevas empeoran" y la Estado (`:17-20`) "PROBADO". Y el banner manda a leer 0026 "para dónde SÍ está la ganancia (11,1% menos Brier)" (`0024:12-13`): falso desde 0034. 0034 no puso banner ni en 0024 ni en 0028. [V]
  Lo peor: **ni 0024 ni 0028 midieron lo que dicen** (hallazgo H1, abajo): el brazo `primaria` del harness nunca pasó `tema=` a `proyectar_postura`, así que `primaria ≡ sin_tema`. La conclusión "no activar nada" sigue siendo lo que hace el código (`TEMA_AUTO=0`, `:155`; `COMBINAR_TEMAS="primaria"`, `:161`; `proyectar_postura(combinar_temas="primaria")`, `variables/bloque/src/bloque.py:485`), pero por una razón distinta de la escrita. [V]
- **0027:** encabezado "NO ENGANCHADO… decisión de Franco pendiente" (`0027:3-5`) vs ADR-0030 (`0030:15-24`, `:220-224`): "quedan en el repo, construidos y apagados — decisión explícita de Franco, ya tomada". El pendiente ya no está pendiente. [V]
- **0023:** "APLICADO (sólo el contrato de datos)" es literalmente cierto, pero "aplicado" no significa usado: el parquet no lo regenera `REGENERAR.ps1` ni ningún workflow (Grep sobre `*.ps1`, `.github/workflows/*.yml`: 0 apariciones; sólo `.mapa/mapa.json`), quedó estático en `2026-09-15 20:44` con `fecha` máxima 2026-08-27 [V*], y nadie del motor lo lee. [V]
- Ningún ADR de este lote está hoy "prendido" en el código salvo la infraestructura inerte (funciones cargadas que con los defaults no corren).

### (ii) 0027 y 0023: código implementado y no enganchado — ¿muerto o lo importa algo?

`python .mapa/buscar.py --archivo modelo/ensemble/src/composicion_capitulos.py` (145 LOC, 0 commits en el índice):
- **LO IMPORTAN:** `evaluacion/baseline/src/validar_leybases_por_capitulos.py`, `evaluacion/baseline/src/validar_piloto_capitulos.py`, `modelo/ensemble/tests/test_composicion_capitulos.py`. Ninguno corre en CI (los workflows sólo corren `test_*.py`) ni en `REGENERAR.ps1`. Grep de `composicion_capitulos|simular_capitulos` en `*.py/*.ps1/*.yml/*.sh/*.js` confirma: el resto son docstrings. [V]
- **IMPORTA** `agregador.py`, que ganó `devolver_crudo` (`agregador.py:154, 300-302`; default `False`). Único llamador productivo posible de `devolver_crudo=True`: `composicion_capitulos.py:113`. Con los defaults, `simular_votacion` sale idéntico. [V]
- Veredicto: **no está muerto por accidente: está apagado por decisión** (0030:220-224), pero **ninguna línea del camino que produce P(sanción) lo llama**. Sólo sobrevive porque un test (10/10 OK, `Archivos_Borrar/auditoria/log___modelo_ensemble_tests_test_composicion_capitulos_py.txt`) y dos scripts de validación lo importan.
- 0023: `datos/expedientes/src/votacion_por_articulo.py` (222 LOC) lo importa sólo su test y, vía su parquet (`.mapa/buscar.py --dato votacion_por_articulo`), `prueba2_reconstruccion_por_rango.py`, `prueba3_cobertura_universo_vivo.py`, `validar_leybases_por_capitulos.py`, `validar_piloto_capitulos.py`, `validar_piloto_titulos.py` (todos cierre de la línea, lote E). Importa a `enlace_senado.py` (`elegir_votacion`, `_RE_PARTICULAR`). `cadena_camaras.parquet`, que sí alimenta `elegir_votacion` sin cambios, lo lee sólo `estimar_psi_arrastre.py` (ψ estimado, no implementado). [V]

### (iii) ¿Qué fracción de cada ADR describe una línea que HOY no deja ninguna mejora en pie sobre el motor?

Estimación por líneas (INFERIDO, criterio: texto cuyo objeto es un mecanismo/dato sin consumidor en el número o con evidencia rota):

| ADR | líneas | ~% sin mejora en pie | qué queda |
|---|---:|---:|---|
| 0023 | 213 | ~90% | conteos descriptivos reproducibles (206/1.428, 15/153) y la regla "agregar sin reemplazar" |
| 0024 | 260 | ~95% | sólo la plomería `TEMA_AUTO` inerte y "lo manual siempre gana" |
| 0026 | 160 | ~90% | el diseño (un grado de libertad, EB k=5 hacia el récord general, combinar en logit) como hipótesis a reabrir |
| 0027 | 168 | ~85% | B0 (reconstrucción de Ley Bases, dato) y la definición de los 4 eventos P_k/P_todo/P_algo/E[superv.] |
| 0028 | 124 | ~100% | el método (brazo de control + diferencia pareada con IC), no su resultado |

Ponderado por líneas: **~92%** de las 925 líneas. Nada de esto mueve el número publicado: `REGENERAR.ps1:291-292` sólo corre `casos/nowcast_puertas_html.py diputados --fecha 2026-06-01 --origen EJECUTIVO`, sin `--proyecto` ni `--tema` (`casos/nowcast_puertas_html.py:89,92`), de modo que ni TEMA_AUTO, ni RECORD_POR_TEMA ni ninguna rama multietiqueta pueden actuar sobre el panel. [V]

### (iv) 0024 "IMPLEMENTADO y PROBADO — NO SE RECOMIENDA": qué medición, qué harness, ¿depende de la fuga?

- **Medición:** `evaluacion/baseline/src/baseline_voto_individual.py --muestra 3000 --seed 7 --combinar-temas {primaria,union,ponderada,peor_tema}` (versión del commit fa4c572 del 15-09, ajustada en c37b532). Salidas: `evaluacion/baseline/outputs/baseline_combinar_temas_{primaria,union,ponderada}_2026-09-15.json`, `…peor_tema_2026-09-16.json`. **2.984 actas, 353.133 votos; rama de bloque n=1.263 votos (0,36%), Brier 0,20380 / 0,20569 / 0,20771 / 0,20836.** Sin IC, sin cluster, un solo seed. [V*] (leí `por_fuente_direccion` de los cuatro JSON: coinciden con `0024:139-146`).
- **Harness:** copia propia del motor: récord = `s.shift(1).expanding().mean()` por legislador (era) con `n_prev = shift(1).count()` (versión 03c9340 del harness, `:384-385`; idem en fa4c572), y `perfil()` propio. La "rama de bloque" es `n_prev < MIN_HIST_INDIVIDUAL` (`:478`). [V]
- **¿Depende de la fuga? SÍ.** (1) Con `shift(1)` por fila, un legislador con 2+ votos del mismo día ya tiene `n_prev≥1`: la rama de bloque queda reducida a la primera fila de cada legislador/era: 0,36% de los votos en 0024/0028 contra **4,7%** con el harness limpio (`0034:146`). Se evaluó un subconjunto definido por la fuga. [V] (2) Además el harness tenía una regresión propia (H1). (3) El "NEGATIVO" es lectura de puntos: diferencias de 0,002-0,005 de Brier sobre 1.263 votos sin IC; 0028 mostró que los IC cruzan 0. [V]
- Encabezado "no se recomienda activar" = correcto en efecto; "PROBADO negativo" = no sostenido.

### (v) 0026: ¿ADR-0015 se cumplió al prenderlo? (`git log -S"RECORD_POR_TEMA" -- modelo/ensemble/src/nowcast_puertas.py`)

Commits que tocaron el default: **0a7a03f (2026-09-16 10:31, lo prende)**, bf831aa (28-09 13:25, refactor de FASE 2, ADR-0034) y 8b310c1 (28-09 18:51, lo apaga). [V]

**0a7a03f:**
- **¿Tocó FORMULA-COMPLETA.md en el mismo commit? Sí.** `git show --stat 0a7a03f`: `FORMULA-COMPLETA.md | 35 ++-` (+19/−16), además de ADR-0026, ESTADO, EN-HUMANO, tablero, 4 scripts/tests, `nowcast_puertas.py` (+187/−35). [V]
- **Pero sólo en la letra de ADR-0015.** Qué cambió en FORMULA: (a) nota en la fila 4 de la tabla, (b) la fila 18 pasa de "bloqueado" a "PRENDIDO 16-09-2026", (c) §III.B.3 reescrita. **No** cambió: la ecuación de la Parte I (§I.4 seguía diciendo `P_i = rec_i si n_i ≥ 8`, sin guard ni encogimiento ni el término temático); el encabezado "Última actualización: 2026-09-08"; el "Resumen honesto" (7 términos que corren…). Es decir, el término quedó descripto en la **Parte III ("Lo pendiente")**, cuando el propio archivo dice "si un término no está en la Parte I, no afecta el número". `git show 0a7a03f:…/FORMULA-COMPLETA.md` líneas 3, 56-62, 155-176. [V]
- **Nivel 2 (quién consume, ¿mueve el número publicado?): no escrito.** ADR-0026 no dice quién lee `alineacion_individual_por_area` ni si el panel se mueve. La respuesta ("el panel de REGENERAR no se mueve") recién aparece en `0034:168-169`. ESTADO 16-09 dice "Estado del módulo: HECHO (activado en producción)" (`ESTADO-DEL-PROYECTO.md:175-186`, entrada del 16-09) y EN-HUMANO "se activó directamente en el modelo": en producción, el efecto sobre el panel publicado era **cero**, porque `REGENERAR.ps1:291-292` (idéntico en 0a7a03f) no pasa proyecto ni tema. [V]
- **Medición citada:** `fase1_rec_por_tema.py` (11,06% global; "positivo en todos los cortes") + `medir_rec_por_tema.py` (8,1% con n≥1; 44,75% de 1.419 legisladores sobre el p95 del shuffle) + un caso real (Ley Bases @2024-01-15: 0,8380 → 0,8756). **Ninguna llama a `alineacion_individual_por_area` ni a `nowcast()`**: son espejos con `shift(1)` (`fase1_rec_por_tema.py:117-132`, `medir_rec_por_tema.py:88-100`), sin guard de era, sin encoger al bloque, sin origen; lo activado (la función del motor) no fue lo medido. Los tests de la función (`test_record_por_tema.py`) son sintéticos. [V]
- **Quién decidió:** `0026:5-8` "Claude, con autonomía delegada explícitamente por Franco en PROMPT-MULTITEMA-V2.md"; ESTADO: "Claude, ejecución autónoma (Franco delegó explícitamente…)". El commit lleva como autor "Franco Marconi" (identidad de git de la PC) y `Co-Authored-By: Claude Sonnet 5`: **el autor de git no discrimina**. El prompt que delega (`PROMPT-MULTITEMA-V2.md:75-82, 240-243`: "puede prender banderas si el censo completo mejora y queda documentado en fórmula + ADR — el mismo criterio con el que se prendieron el guard de era y η_j") es, según `RESUMEN-MULTIETIQUETA-COWORK.md:3-7` y `tablero_datos.js:322-323`, "una revisión externa"; **el propio prompt entró al repo en el mismo commit que la activación** (0a7a03f lo crea, +314 líneas). No hay en el repo ningún mensaje de Franco que revise el 11,06% antes de prender [N: puede haber ocurrido en el chat]. Es decir: decidió Claude aplicando un criterio delegado, cuyo precedente ("como el guard de era y η_j") estaba medido con el mismo harness luego declarado con fuga. [V/I]
- Además: la activación fue **antes** cronológicamente que el cierre de FASE 0 (ADR-0028, 03c9340 11:37) y sin que Franco viera nada más que el prompt.
- **Veredicto (v): ADR-0015 cumplido en forma, no en fondo.** Costo real de un cumplimiento en fondo: habría obligado a escribir el Nivel 2 y a notar que el panel no se movía y que la "fórmula completa" de la Parte I ni siquiera tenía el guard.

### (vi) Regla que sobrevive de cada uno

| ADR | regla viva | dónde ya está / dónde debería quedar |
|---|---|---|
| 0023 | **Agregar sin reemplazar**: un contrato nuevo importa la función existente (`elegir_votacion`) en vez de reimplementar el criterio de "decisiva"; se expone la ambigüedad (nombre de capítulo no 1:1) en vez de elegir en silencio | destino 1/6 |
| 0023 | "Aprobado en general" no agota "sancionado": **15 de 153 (9,8%)** proyectos aprobados perdieron ≥1 tramo en particular [V*] | destino 3 (definición de la salida del número) |
| 0024 | **Lo manual siempre gana** (`tema=` a mano > TEMA_AUTO); una bandera sobre un dato que no existe es no-op *verificado*, no "prendible" | destino 6 |
| 0026 | **"Un solo grado de libertad, aislado"** (para el mismo voto sólo cambia qué récord se usa) + **encoger hacia el récord GENERAL de la misma persona** (EB k=5) + **combinar áreas en logit** | destino 2 (como diseño si se reabre); el principio de aislamiento, a 5 |
| 0027 | **La P del proyecto no es un evento**: P_k, P_todo, P_algo, E[superv.]; ni promedio ni producto; se cuenta sobre simulaciones con shock común | destino 3 |
| 0028 | **Sin brazo de control no hay conclusión; se reporta el IC de la diferencia pareada, clusterizada** (y hoy: clusterizar por LEY, `0034` §IV.6) | destino 5 |
| 0028/0026 | "Condicionar/combinar en logit, nunca en probabilidad": OJO, **`FORMULA-COMPLETA.md:1760-1768` (IV.2) sólo dice "nunca multiplicando"; no menciona "promediando probabilidades"**, que es lo que 0026:70-74 y 0028:14-15 le atribuyen. La regla "promediar en logit" es un principio de diseño, sin evidencia empírica en este lote (la diferencia real ponderada vs ponderada_logit no se distinguió de cero). | destino 5 (formularla bien) |

---

## 1. Fichas por ADR

### ADR-0023 — `votacion_por_articulo`: contrato nuevo, agrega sin reemplazar (15-09-2026, addenda 16-09)

1. `0023` · 15-09-2026 (+2 addenda del 16-09) · contrato de datos `votacion_por_articulo.parquet` + `titulo_num/capitulo_num` + `capitulos_nombre.parquet`.
2. **Quién decidió:** `0023:4-5` "Claude, con el mandato de `coordinacion/PROMPT-MULTIETIQUETA.md` (Franco)"; addendum 1 "Franco: *Sí, hay que hacerlo*" (`:79`); addendum 2 "Franco: *Deberiamos ahora seguir con escalar la descarga*" (`:121-122`). Las citas de Franco las transcribe Claude; no verificables desde el repo [I]. Franco autorizó (por transcripción) los 163 PDF; el propio ADR lo trata como alcance acotado. El prompt fuente prohibía cambiar el número publicado sin aprobación (`PROMPT-MULTIETIQUETA.md:252`): **respetado**.
3. **Estado declarado:** "APLICADO (sólo el contrato de datos; el consumidor NO está implementado)". **Real:** parquet presente y en git, 2.361×13 [V*], 37/37 tests OK (`log___datos_expedientes_tests_test_votacion_por_articulo_py.txt`); **no regenerado** (mtime 15-09; `fecha` máx 2026-08-27; ningún ps1/yml lo llama), sin consumidor del motor. El encabezado "Toca" (`:6-7`) no lista `capitulos_nombre.py` que el addendum 2 agregó (211 LOC + parquet 546×5 hoy).
4. **Medición:** ninguna de skill. Recuentos descriptivos sobre `acta_expediente_todas.parquet` (B0). **Reproducidos [V*] desde el parquet:** 1.428 pares (proyecto, cámara); 206 con >1 acta (el "14,4%"); 1.423 tramos particulares (12,7% con `titulo_num`, 9,8% con `capitulo_num`); 153 proyectos con decisiva aprobada y ≥1 tramo particular no decisivo, **15 (9,8%)** con ≥1 tramo negativo, **24 de 838** tramos (2,86%). Nombre de capítulo 32/36 (88,9%) [N: parquet posterior sobrescrito por ADR-0029].
5. **¿Depende de fuga/espejo?** **No aplica** (recuentos de actas, sin récord ni predicción).
6. **¿Vigente en código?** Sí como archivo (`datos/expedientes/src/votacion_por_articulo.py`, 222 LOC), no como camino: ni REGENERAR ni CI lo ejecutan (sólo su test); ningún módulo de `modelo/`, `variables/`, `casos/`, `producto/` lee el parquet (`buscar.py --dato`). No toca `elegir_votacion` ni `cadena_camaras` (cumple lo prometido).
7. **¿Documentación coincide?** FORMULA III.A.6 (`:1599-1618`) y EN-HUMANO/tablero lo describen como construido y no enganchado: coincide. **Contradicciones internas:** el ADR cuenta que Ley Bases "perdió 6 artículos/incisos" (`:24-25`) y que la segunda ronda fueron "47 tramos" (`:26-27`); el parquet da **7 NEGATIVO de 13** el 2024-02-06 y **34 particulares + 1 general = 35** el 2024-04-30 [V*], y ADR-0027 (`:74-77`), EN-HUMANO y tablero dicen 7/13 y 35. La afirmación "reproduce la crónica pública sin diferencias" (`:212`) es de un texto que no coincide con su propio dato. La verificación dice "29 checks" (`:204`) y el addendum "37 en total" (`:115`): hoy 37.
8. **VEREDICTO: INACTIVO** (código, datos y tests presentes; sin consumidor en el número ni regeneración; los recuentos descriptivos son válidos pero no gobiernan nada).
9. **DESTINO: 6** principal (línea capítulo, cerrada) + **1** (contrato de datos compartido) + **3** (qué cuenta como "sancionado"). **Sobrevive:** "agregar sin reemplazar / un solo criterio de decisiva importado"; el hecho descriptivo 9,8%. **Se pierde:** el pipeline de PDF (`capitulos_nombre.py`), la cobertura 12,7/9,8%, las cifras de la crónica de Ley Bases (6/47).

### ADR-0024 — Multietiqueta `union`/`ponderada`/`peor_tema` y enganche `TEMA_AUTO` (15/16-09-2026; enmendado por 0028)

1. `0024` · 15-09-2026 (+ `peor_tema` 16-09) · reglas de combinación de temas en `proyectar_postura` + `TEMA_AUTO` + lectura `proyecto_taxonomias`.
2. **Quién decidió:** `0024:19-21` "Claude, con el mandato de `PROMPT-MULTIETIQUETA.md` (Franco: *seguí el camino que consideres mejor… resolvé todo lo que puedas*)"; `peor_tema` "a pedido de Franco: *probemos algo nuevo*" (`:56`); "no se prende nada en publicación sin aprobación de Franco" (`:258-260`) → respetado (banderas apagadas).
3. **Estado declarado:** "IMPLEMENTADO y PROBADO — NO SE RECOMIENDA ACTIVAR. Banderas APAGADAS" + banner "ENMENDADO por 0028". **Real:** banderas apagadas ✓ (`nowcast_puertas.py:155, 161`; `bloque.py:485`); "PROBADO" no sostenido (H1, iv); banner contradice cuerpo (i).
4. **Medición:** ver (iv). Harness de 15-09, 2.984 actas, muestra seed 7, rama de bloque n=1.263, sin IC. 0028 lo declara "sin brazo de control, en probabilidad, con estimador sesgado".
5. **¿Depende de fuga/espejo?** **Sí** (récord `shift(1)` por fila, `perfil()` copia; subconjunto de bloque definido por la fuga: 0,36% vs 4,7%) **y de un bug de harness (H1)**: `primaria` no aplicaba tema.
6. **¿Vigente en código?** Rama multietiqueta cargada, inalcanzable con defaults: `bloque.py:405-447, 570-580, 632-745` (~190 LOC de 842); `nowcast_puertas.py:155-161, 249-263` (`_tema_auto`); cubierta por `test_bloque_v3_multietiqueta.py` (12/12), `test_tema_auto.py` (9/9), `test_tema_por_proyecto.py` (24/24), todos OK en CI. Nada del camino con defaults la llama (`TEMA_AUTO` OFF; el panel no pasa proyecto ni tema).
7. **¿Documentación coincide?** FORMULA `:256-309` (I.4a) conserva el PASO 2 como "IMPLEMENTADO y PROBADO… EMPEORA" y luego el "CIERRE 16-09" — ambos en la misma sección, coherente con el ADR (misma contradicción interna). Fila 19 (`:82`) "CERRADO 16-09" y su remisión a la fila 18 quedaron viejas. ESTADO-REAL fila 19 (`ESTADO-REAL-DEL-MOTOR.md:46`): "✅ probablemente: la fuga era común a los brazos" → no contempla que dos brazos eran idénticos. Comentario `nowcast_puertas.py:142-154` sigue justificando el apagado por "las tres reglas empeoran".
8. **VEREDICTO: INACTIVO** (código presente y apagado; el motivo escrito está roto).
9. **DESTINO: 6** (registro de reglas de combinación descartadas) + **5** (control aislado). **Sobrevive:** "lo manual siempre gana; una bandera sin dato es no-op verificado; nada de multietiqueta a nivel bloque se prende sin evidencia". **Se pierde:** las cuatro tablas de skill, "pesimismo ≠ precisión" (peor_tema, medido con un baseline que no era el descripto), la afirmación "primaria byte a byte retrocompatible" (`0024:53`).

### ADR-0026 — `rec_i^tema`: el récord del legislador condicionado por tema (16-09-2026; enmendado por 0034)

1. `0026` · 16-09-2026 · `RECORD_POR_TEMA`: récord por área encogido (k=5) hacia el récord general del mismo legislador, combinado en logit.
2. **Quién decidió:** `0026:5-8` "Claude, con autonomía delegada explícitamente por Franco en PROMPT-MULTITEMA-V2.md ('podés prender banderas si el censo completo mejora y queda documentado en fórmula + ADR')". Ver (v).
3. **Estado declarado:** "IMPLEMENTADO, MEDIDO sobre el censo completo y PRENDIDO"; banner 28-09 "APAGADO". **Real:** APAGADO (`nowcast_puertas.py:219`); función `alineacion_individual_por_area` (`:385-495`) cargada; `record_legisladores` la llama sólo si la bandera está prendida (`:519-525`); payload `record_por_tema` sale `{"activo": False}` (`:910-915`).
4. **Medición:** `medir_rec_por_tema.py` (3 preguntas) + `fase1_rec_por_tema.py` (comparación pareada voto a voto, 318.564 votos). Historia = `shift(1)` por fila; "récord general" = media expansiva ingenua, no `rec_i` del motor. El "44,75% sobre el p95" sale de un shuffle a nivel **voto** (`medir_rec_por_tema.py:189-194`: `rng.choice(votos, size=sum(ns), replace=False)`), que trata como independientes los artículos de una misma ley que comparten tema [I: inflado por la unidad efectiva, ADR-0034 §IV.6].
5. **¿Depende de fuga/espejo?** **Sí, las dos.** 0034 reprodujo el 11,06% exacto y con la misma metodología e historia estricta da **−2,91% [−8,6; +2,1]**; contra el motor en el censo limpio **empeora 2,1% [0,8; 3,5]** y 6,4% donde actúa (`0034:154-169`).
6. **¿Vigente en código?** Apagado. Función y wiring (`:222-246, 385-495, 802-823`, ~160 LOC) inalcanzables con defaults; tests `test_record_por_tema.py` 18/18 OK (LOC 203, incluye los de 0031). Los espejos `fase1_rec_por_tema.py` (191) y `medir_rec_por_tema.py` (239) siguen en el árbol con aviso de fuga (`:6-11`).
7. **¿Documentación coincide?** FORMULA fila 18 (`:81`) y III.B.3 (banner `:1640-1648`) sí; pero cuerpo de III.B.3 y `:308` no. ESTADO-REAL fila 18 sí. EN-HUMANO: el relato del 16-09 ("se activó directamente") queda como historia, la entrada del 28-09 (`EN-HUMANO.md:5-24`) lo corrige. `tablero_datos.js:332-333` (hito del 16-09) sigue afirmando "11% menos de error… sin ninguna excepción negativa… se activó" sin retractación en ese hito (sí en `:19`). El ADR dice "el 99,6% de las predicciones sale de rec_i" (`:29-31`); hoy 95,3% (`0034:145`).
8. **VEREDICTO: SUPERSEDIDO por ADR-0034** (la decisión de prender fue revertida; la implementación queda además INACTIVA). La evidencia que lo prendió: fuga + espejo.
9. **DESTINO: 2** (voto individual) principal + **5** (criterio simétrico de encendido/apagado; el caso testigo de por qué no basta un espejo). **Sobrevive:** el diseño (un grado de libertad; EB k=5 al récord general de la misma persona; combinar en logit) **como hipótesis a reabrir con el censo limpio**; el hecho descriptivo de cobertura de tema 51-57%. **Se pierde:** el 11,06%, "sin cortes negativos", 44,75%, "el tema tiene que vivir en P_i" como conclusión (es hipótesis; midió peor).

### ADR-0027 — Composición de P(proyecto) por capítulos, por simulación (16-09-2026)

1. `0027` · 16-09-2026 · `composicion_capitulos.simular_capitulos` + `agregador.devolver_crudo` + B0 (Ley Bases reconstruida).
2. **Quién decidió:** `0027:4-7` "Claude, mandato de `PROMPT-MULTITEMA-V2.md` (FASE 2)"; los dos números publicados se reservan a Franco (`:124-128, 163-164`) y el prompt lo exigía (`PROMPT-MULTITEMA-V2.md:247`). Mantener el código: "decisión explícita de Franco" (`0030:220-224`).
3. **Estado declarado:** "MÓDULO IMPLEMENTADO y TESTEADO, NO ENGANCHADO… decisión de Franco pendiente". **Real:** NO enganchado ✓; "pendiente" superado por 0030 (apagado por decisión).
4. **Medición:** ninguna de skill. Tests sintéticos (10/10) y B0 descriptivo sobre el parquet. B0 reproduce: 2024-02-06 → 6 AFIRMATIVO / 7 NEGATIVO de 13; 2024-04-30 → 34 particulares + 1 general, todos AFIRMATIVO [V*]. Las validaciones reales (`validar_*`) las hicieron 0029/0030 (lote E): "n=3 no alcanza".
5. **¿Depende de fuga/espejo?** B0: **no aplica**. El mecanismo hereda ε₀/τ de 0025 (estimados con offset con fuga; cobertura real de la banda 63,6%, no 99,88%: `0034:171-189`) [I: indirecto]. Y el sostén de "los capítulos se caen juntos" es la sobredispersión de **votos dentro de una votación** (37-41×), que no mide correlación **entre capítulos** de un mismo proyecto [I].
6. **¿Vigente en código?** No: sin enganche (ver ii). `composicion_capitulos.py` 145 LOC + test 161; `agregador.py:154, 183-190, 300-302`.
7. **¿Documentación coincide?** FORMULA III.A.6 (`:1599-1618`) coincide. **Dos problemas técnicos no declarados** [V/I]: (a) `simular_votacion` sortea `eta = rng.standard_normal(n_sims)` (`agregador.py:212`) y luego `u = rng.random((n_sims, n))` (`:241`): con la misma `seed` y rosters del mismo tamaño (257 en Diputados) **los capítulos comparten también el sorteo individual `u`**, no sólo η_j. El ADR atribuye el acoplamiento sólo a η_j (`0027:48-56`). (b) El test "capítulos perfectamente correlacionados" (`test_composicion_capitulos.py:60-79`) usa **mismo roster y misma seed**: `P_todo == min_k P_k` sale por construcción (arrays idénticos), aun con τ=0, así que **no prueba que η_j sea el mecanismo**; lo que "atrapa" es que alguien cambie la seed por capítulo. El propio código exige ε₀>0 o τ>0 pero eso no cambia el sorteo `u`. Un supuesto que se agrega sin querer (ADR-0015 nivel 2).
8. **VEREDICTO: INACTIVO** (módulo presente, sin enganche, decisión de dejarlo apagado).
9. **DESTINO: 6** principal + **3** (los cuatro eventos y "composición por simulación con shock común"). **Sobrevive:** la definición de P_k/P_todo/P_algo/E[superv.]; "ni promedio ni producto". **Se pierde:** el módulo como está (si se reabre, hay que separar η de `u`), el test tautológico, "la revancha de peor_tema" como resultado.

### ADR-0028 — FASE 0: el re-test cierra el multitema a nivel BLOQUE (enmienda a 0024) (16-09-2026)

1. `0028` · 16-09-2026 · brazos `sin_tema`/`primaria`/`union`/`ponderada_logit` sobre el censo; conclusión "ninguna diferencia distinguible de cero".
2. **Quién decidió:** `0028:3-5` "Claude, mandato de `PROMPT-MULTITEMA-V2.md` (FASE 0)"; el criterio "si el control gana, apagar" es "lo que Franco ya decidió" (`PROMPT-MULTITEMA-V2.md:79`); `peor_tema` cerrado "decisión explícita de Franco" (`0028:44-46`).
3. **Estado declarado:** "MEDIDO sobre el CENSO completo, cierra la pregunta". **Real:** el censo es el del harness con fuga (5.852-5.855 actas, 691.460-691.893 votos), el brazo `primaria` ≡ `sin_tema`, y no es reproducible hoy (ver 7).
4. **Medición:** `evaluacion/baseline/src/fase0_control_temas.py` (249 LOC) sobre `baseline_voto_individual.correr(combinar_temas=arm, devolver_detalle=True)` (versión 03c9340), 1.000 réplicas bootstrap clusterizadas **por acta**, seed 7. Salida `evaluacion/baseline/outputs/fase0_control_temas_censo.json` (leída [V*]); detalle `fase0_detalle_*.parquet` (4×~6,3 MB, gitignored por `*.parquet`).
5. **¿Depende de fuga/espejo?** **Sí.** Mismo harness `shift(1)`; rama de bloque = 232-235 actas, 2.258-2.292 votos (0,33%) vs 4,7% limpio; cluster por acta (0034: subestima ~1,7×). **Y H1: `primaria` no condicionaba** (`fase0_control_temas_censo.json`, `diferencias_vs_primaria.sin_tema_menos_primaria__rama_bloque`: `n_actas_comunes 232`, `diff_punto 0.0`, IC [−5e-05; 6e-05]; las eras 2015-19, 2019-23 y desde 2023 salen idénticas al quinto decimal). Quedan `union` y `ponderada_logit` contra un control, con IC ±0,006-0,010 sobre ~235 actas (potencia baja).
6. **¿Vigente en código?** Código de las reglas apagado (ver 0024); `ponderada_logit` en `bloque.py` (~+25 LOC). `fase0_control_temas.py` corre hoy contra el harness **reescrito** (bf831aa): `baseline_voto_individual.py:566-584` **sí** pasa `{"tema": tema}` en `primaria` y usa historia estricta: si se re-corre, dará otra cosa que las tablas del ADR (INFERIDO; no se corrió). "Reproducible: `python fase0_control_temas.py`" (`0028:108`) ya no lo es en el sentido original.
7. **¿Documentación coincide?** FORMULA `:296-309`, EN-HUMANO `:286-296` y tablero `:322-323` repiten "ninguna diferencia distinguible de cero… la ganancia real está en FASE 1 (+11,1%)": la segunda mitad cayó con 0034. **Inconsistencia en la tabla del propio ADR** (`0028:57`): `sin_tema` "diff −0,00068, IC [−0,00005; 0,00006]" — el punto está **fuera de su propio IC** porque el punto es no pareado (232 vs 235 actas) y el IC es pareado (diff exacta 0,0); el ADR lo justifica como "ruido de precisión numérica" (`:88-93`) en vez de ver que los dos brazos eran el mismo cálculo. `ESTADO-REAL:46` (fila 19) "✅ probablemente" no contempla esto.
8. **VEREDICTO: REGISTRO-HISTÓRICO** (cierra una hipótesis; el código que "no se activa" está INACTIVO por 0024). Evidencia rota, pero no obliga a nada.
9. **DESTINO: 5** (medición: brazo de control verificable — un control que da idéntico al tratamiento es una alarma, no un resultado; diferencia pareada clusterizada por ley) + **6**. **Sobrevive:** el método. **Se pierde:** el "cierre" como evidencia, las cifras, "la ganancia está en FASE 1".

---

## 2. Hallazgos nuevos de este lote

### H1. El brazo `primaria` del harness nunca aplicó `tema` (regresión de fa4c572) — invalida el "control" de 0028 y el baseline de 0024 [V]
- **Antes** de fa4c572 (`git show fa4c572^:…/baseline_voto_individual.py:337-339`): `proyectar_postura(votos, a.fecha, a.camara, ventana_dias=…, tema=tema, origen=origen, cond_por_acta=cond, k_shrink=K_SHRINK)`.
- **fa4c572** (15-09 16:21, ADR-0024; `…:355-392`): en modo `primaria` sólo se asigna `tema = _norm_cond(info.get("tema_area")); clave_tema = tema` y **`kwargs_tema` queda `{}`**; la llamada pasó a `…origen=origen, cond_por_acta=cond, k_shrink=K_SHRINK, **kwargs_tema)`: **sin `tema=`**. Idéntico en c37b532 y 03c9340 (`:416-454`) y en bf831aa^ (`:547-585`).
- Consecuencia: `primaria` = incondicional por tema (sólo origen) = `sin_tema` (`fase0_control_temas.py` lo llama "el CONTROL"). Los JSON lo confirman (diff pareada exactamente 0,0). El ADR-0024 comparó "sin tema" contra multietiqueta (accidentalmente lo que 0028 dice que faltaba) y 0028 comparó "sin tema" contra "sin tema".
- El harness de 0034 lo arregla sin decirlo (`baseline_voto_individual.py:574-576`). Ningún documento lo menciona (Grep en `coordinacion/`: 0 resultados). No lo atrapó ningún test (`test_bloque_v3_multietiqueta.py` prueba `proyectar_postura`, no el harness).
- La afirmación de ADR-0024 (`:52-53`) "primaria (default): comportamiento de SIEMPRE, retrocompatible byte a byte" es cierta para `proyectar_postura`, falsa para el harness que la midió.

### H2. Regla de la fórmula mal citada
`FORMULA-COMPLETA.md:1760-1768` (IV.2) sólo dice "Condicionar en logit, nunca multiplicando". Los ADR-0026/0028 y el prompt citan "nunca promediando probabilidades" como si estuviera ahí.

### H3. El panel publicado no puede reflejar nada de esta línea
`REGENERAR.ps1:291-292` + `casos/nowcast_puertas_html.py:89-92`: hipotético, sin proyecto, sin tema. TEMA_AUTO, RECORD_POR_TEMA y las ramas multietiqueta son **estructuralmente incapaces** de mover el número publicado. Los ADR de este lote nunca lo dicen; 0034:168-169 lo dice sólo para RECORD_POR_TEMA.

### H4. Los precedentes citados para delegar la activación estaban medidos con la misma fuga
`PROMPT-MULTITEMA-V2.md:242-243` ("el mismo criterio con el que se prendieron el guard de era y η_j"). El guard: 0,1304 → 0,1611 con harness con fuga (lote E, colateral); η_j: τ con offset del espejo viejo y cobertura del 99,88% con `agregador.backtest` sobre la línea de bloque observada (`0034:188-189`).

---

## 3. Notas finales

### (a) Contradicciones entre cuerpo y encabezado de un mismo ADR
- **0023:** encabezado "Toca" sólo `votacion_por_articulo.py` vs addendum 2 que agrega `capitulos_nombre.py`, `ingesta_od.py --solo-proyectos` y un parquet nuevo; "6 artículos perdidos / 47 tramos" (`:24-27`) vs parquet 7/13 y 35 [V*]; "29 checks" vs "37"; "206 pares con votación en particular" es en realidad "pares con >1 acta" (con `es_particular` son 700; con un tramo particular no decisivo, 160) [V*].
- **0024:** encabezado "PROBADO… NO SE RECOMIENDA" y cuerpo "🔴 NEGATIVO… empeoran" vs banner "no es que empeoren"; banner: "ADR-0026 es donde SÍ está la ganancia" vs 0026 banner "APAGADO".
- **0026:** Estado "PRENDIDO" (`:3-4`) vs banner "APAGADO" (`:14`); "positivo en TODOS los cortes" vs −20,5% Senado limpio (`0034:162`); "99,6% de las predicciones" vs 95,3%.
- **0027:** "decisión de Franco pendiente" vs `0030:220-224` "decisión ya tomada: construido y apagado"; "reproduce la crónica sin diferencias" vs 0023.
- **0028:** "cierra la pregunta… con evidencia limpia" vs brazos idénticos (H1); tabla con punto fuera de su IC (`:57`); "Reproducible" vs harness reescrito y salidas gitignored; "la ganancia real está en FASE 1" vs 0034.

### (b) Contenido/código que ya no vale y sigue en el árbol (LOC, código + tests; INFERIDO en las partes marcadas ~)
| origen | archivo | LOC | nota |
|---|---|---:|---|
| 0023 | `datos/expedientes/src/votacion_por_articulo.py` + `tests/test_votacion_por_articulo.py` | 222 + 161 | sin consumidor de motor; parquet 171 KB estático |
| 0023 | `capitulos_nombre.py` + test | 211 + 115 | **ya contado en lote E (0029)** |
| 0024 | `variables/bloque/src/bloque.py` (multietiqueta) | ~190 | ~ por rangos `:405-447, 504-540, 570-580, 632-745` |
| 0024 | `variables/bloque/tests/test_bloque_v3_multietiqueta.py` | 243 | |
| 0024 | `variables/proyecto/src/tema_por_proyecto.py` + test | 354 + 229 | parte de lectura la usa `_resolver_multietiqueta` sólo con banderas apagadas; solapa con 0029 |
| 0024 | `nowcast_puertas.py` (`_tema_auto`, constantes) + `test_tema_auto.py` | ~55 + 105 | ~ |
| 0026 | `nowcast_puertas.py:222-246, 385-495, 802-823` | ~160 | función dormida |
| 0026 | `modelo/ensemble/tests/test_record_por_tema.py` | 203 | incluye tests de 0031 |
| 0026 | `fase1_rec_por_tema.py` + `medir_rec_por_tema.py` + test | 191 + 239 + 64 | espejos con fuga (marcados) |
| 0027 | `composicion_capitulos.py` + test | 145 + 161 | |
| 0027 | `agregador.py` `devolver_crudo` + tests | ~13 + 33 | |
| 0028 | `evaluacion/baseline/src/fase0_control_temas.py` | 249 | corre contra otro harness que el de sus tablas |
| 0028 | `evaluacion/baseline/outputs/fase0_detalle_*.parquet` | 4 × ~6,3 MB | gitignored; el JSON sí está en git |

**Total del lote ≈ 3.000 LOC (código + tests), ~1.400 de ellos tests**, sin contar solapes con el lote E (~326 de capitulos_nombre y ~150 de tema_por_proyecto). Con los defaults, **0 líneas** de esto se ejecutan en el camino que produce P(sanción).
Datos que ningún camino por defecto lee: `proyecto_taxonomias` (`datos/proyectos/data/proyectos.db`) y `taxonomias.csv`/`asignaciones.csv` (lote E), `votacion_por_articulo.parquet`, `capitulos_nombre.parquet`.

### (c) ¿Esta línea, tal como está en el árbol, deja algo en pie? (≤100 palabras)
No deja ninguna mejora sobre el motor. Las reglas de combinación de temas no se distinguen de no condicionar (y el control era el mismo cálculo que el tratamiento); el récord por tema empeora 2,1% con el harness limpio; capítulos y votación por artículo son módulos sin consumidor en el número. Queda método (control aislado, IC pareado por ley, agregar sin reemplazar), dos hechos descriptivos (15 de 153 leyes aprobadas pierden algún tramo; la cobertura de tema es 51-57%) y una hipótesis sin refutar limpiamente: el récord por tema, si se re-mide con historia estricta y cluster por ley.

### Verificaciones [V*] hechas leyendo datos (sin correr scripts de medición)
- `datos/expedientes/data/clean/votacion_por_articulo.parquet` con pandas: (2361, 13); 1.423 particulares; cobertura titulo/capitulo 12,7/9,8%; 206 pares con >1 acta; 153/15/838/24; Ley Bases HCDN272347: 2024-02-06 AFIRMATIVO 6 + NEGATIVO 7; 2024-04-30 34 particulares AFIRMATIVO + 1 general.
- `evaluacion/baseline/outputs/fase0_control_temas_censo.json` y `baseline_combinar_temas_*.json` con json.
- Logs de tests en `Archivos_Borrar/auditoria/log___*` (test_votacion_por_articulo 37/37, test_composicion_capitulos 10/10, test_tema_auto 9/9, test_record_por_tema 18/18, test_bloque_v3_multietiqueta 12 chequeos, test_tema_por_proyecto 24/24, test_fase1_rec_por_tema 8/8, test_registro 27/27).
- Archivos temporales que dejé fuera del repo: `/tmp/formula_0a7a03f.md` y `%TEMP%\bvi_03c9340.py` (copias de `git show`, no versionados).
