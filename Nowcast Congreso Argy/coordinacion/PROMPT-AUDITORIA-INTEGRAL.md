# PROMPT — Auditoría integral del motor y de los ADR (sólo diagnóstico)

**Fecha:** 2026-09-28 · **Pide:** Franco · **Para:** Claude Code, nativo en la PC de Franco, en la raíz de `Nowcast Congreso Argy/` · **Modo:** **SÓLO LECTURA Y MEDICIÓN.** No se toca motor, datos, tests ni documentos existentes.

---

## 0. Qué se te pide, en una línea

Auditar el motor de medición y de predicción del Nowcast, y los 34 ADR que lo justifican, para responderle a Franco tres preguntas con evidencia verificada contra archivo, y **proponer cómo dejarlo controlable**:

1. **¿Qué está haciendo HOY el modelo?** La fórmula que realmente se ejecuta al producir P(sanción), no la que dicen los documentos.
2. **¿Dónde se perdió el control?** Qué decisión, medición o mecanismo dejó de ser verificable, y cuándo.
3. **¿Dónde se complejizó?** Medido, no opinado: qué se agregó, qué sigue vivo, qué no aporta nada.
4. **¿Cómo lo dejamos controlable?** Tres propuestas, **sin ejecutarlas**:
   - **(a)** Reducir los 34 ADR a **entre 5 y 7**, que una persona pueda leer entera en una tarde y entender.
   - **(b)** Un documento de **reglas simples** (una página) que reemplace el régimen de reglas acumuladas.
   - **(c)** Un **mecanismo de anclaje a la realidad**: la forma de que el modelo siga siempre a los datos observados y de que cualquier desvío se vea solo, sin depender de que alguien se acuerde de mirar.

**Principio rector de la propuesta (lo que Franco quiere sostener a futuro):** *el modelo tiene que seguir siempre la realidad.* Traducido a algo verificable: **ningún término ni parámetro puede afectar el número publicado sin una medición vigente, hecha con el motor real, en walk-forward y con IC por ley; y esa medición tiene que volver a correrse sola cuando el motor cambia.** Las propuestas (a), (b) y (c) se evalúan contra ese principio.

**Alcance:** motor y medición. Es decir `modelo/ensemble`, `modelo/agregador_institucional`, `modelo/voto_individual`, `variables/bloque`, `variables/proyecto` (modulador, origen, tema), `variables/embudo`, `evaluacion/`, `definiciones.py`, `rutas.py`, y `coordinacion/DECISIONES/` (los 34 ADR) junto con `FORMULA-COMPLETA.md`. Datos, bots y workflows quedan fuera, salvo cuando un hallazgo del motor dependa de ellos (en ese caso se cita y se marca como "fuera de alcance, requiere otra ronda").

**Contexto de decisión ya tomado:** el número no tiene consumidor externo hoy (es interno), así que no hay apuro operativo. Se prioriza la exactitud sobre la velocidad. Los 34 ADR se re-litigan **todos**, no sólo los que mueven el motor.

---

## 1. Reglas del entorno (no negociables)

Salen de `CLAUDE.md`; se repiten acá porque acá `rm` funciona de verdad y eso lo hace más peligroso.

- **Nada de `git push`.** Nada de reescribir historia (`rebase`, `--amend` sobre algo compartido, `reset --hard`).
- **Nada se borra.** Lo temporal o regenerable va a `Archivos_Borrar/`.
- **Se puede crear archivos sólo en `coordinacion/AUDITORIA-2026-09/`** (crear la carpeta). Todo lo demás es de sólo lectura. **Los borradores de los ADR consolidados y del documento de reglas también viven ahí**: no se toca `coordinacion/DECISIONES/` ni se archiva ningún ADR existente en esta ronda. Si para medir algo hace falta tocar código existente, **no lo toques: anotalo como bloqueo y preguntá.**
- **Se puede correr** tests, `verificar_regeneracion.py`, scripts de medición y `.mapa/buscar.py`. Las salidas intermedias van a `Archivos_Borrar/`. Las corridas largas se corren y se esperan (el censo tarda ~35 min con `--procesos 3`); no se simulan.
- **Commits locales permitidos sólo sobre `coordinacion/AUDITORIA-2026-09/`**, en castellano, uno por fase.
- **Antes de repetir un número o un estado leído en cualquier bitácora, verificalo contra el archivo o corriéndolo.** Ese es el modo de falla más caro de este repo (CLAUDE.md, corolario). Un porcentaje imposible es un bug, no un fenómeno.
- **No abras `ESTADO-DEL-PROYECTO.md` entero** (650 KB, 3.422 líneas). Se consulta con `grep` por ADR, fecha o término. Leé `.mapa/buscar.py` / `MAPA.md` para ubicar código antes de abrir archivos.
- **Unidad de análisis: la LEY (expediente), no el acta.** Todo IC re-muestrea leyes enteras. Toda ventana de historia corta por fecha estricta y otra ley (FORMULA §IV.6, "regla del expediente").

## 2. Cómo se reporta la evidencia

Cada hallazgo lleva:
- **Referencia:** `archivo:línea`, o el comando y la salida relevante.
- **Confianza:** `VERIFICADO` (lo viste en código o lo corriste) · `INFERIDO` (se deduce, no lo corriste) · `NO VERIFICADO` (lo dice un documento y no pudiste confirmarlo).
- **Qué documento lo afirma y si el código coincide.**

Un hallazgo sin referencia no entra al informe. Si algo no se pudo verificar, va a la sección "No verificado" del final, con el motivo.

---

## 3. Lo que ya se afirma (a VERIFICAR, no a creer)

Punto de partida: `coordinacion/ESTADO-REAL-DEL-MOTOR.md` y ADR-0034. Todo esto está por confirmar o refutar:

| afirmación | fuente |
|---|---|
| Skill global del voto individual **0,1333** [0,057; 0,198] sobre 691.845 votos y 3.731 leyes | ESTADO-REAL, ADR-0034 |
| En la era vigente (desde 2023) **0,010** [−0,26; 0,25] | ídem |
| El número publicado previo (0,1611) estaba inflado por fuga del harness | ídem |
| De 8 términos prendidos, sólo el récord propio tiene evidencia sólida; share, desvío, presencia, β y ε₀+τη tienen evidencia rota o inexistente | ESTADO-REAL, filas 1-3, 12, 13 |
| La banda [p5,p95] declarada al 90% cubre 63,6% de 5.851 actas; sesgo −6,9 votos | ADR-0034 §4.2, URGENTE U2 |
| El harness importa el motor: 238/238 legisladores iguales a `nowcast()` | ADR-0034 FASE 2 |
| El 15,3% de los votos cae en actas sin clave de ley | ADR-0034, URGENTE U4.3 |
| `RECORD_POR_TEMA` está apagado por defecto | ADR-0034 §4.1 |
| TAU=1,19 y EPSILON0=0,035 siguen en producción | URGENTE U2 |

## 4. Hipótesis de Franco y Claude sobre dónde se perdió el control

Salen de leer encabezados y el ADR-0034; **no están confirmadas**. Tratalas como hipótesis: tenés que poder refutarlas, y si la evidencia dice otra cosa, decilo.

- **H1. Se medía con un espejo.** El harness de evaluación reimplementaba el récord con `shift(1)` por fila, y varios scripts de estimación hicieron lo mismo. Los ADR que prendieron términos se apoyaron en mediciones que compartían la fuga. **Es un solo error con muchas consecuencias, no muchos errores.**
- **H2. Se prendían banderas por delegación, sin auditoría independiente de la medición.** Los ADR 0026 a 0034 figuran como "Decide: Claude, sesión delegada". El criterio para prender era "si el censo mejora", con un censo que nadie contrastó.
- **H3. Complejidad sin retorno.** Los ADR de tema, capítulo y origen (0023, 0024, 0026 a 0033: 10 ADR) no dejan hoy ninguna mejora en pie sobre el motor, salvo la observabilidad del ADR-0031. Siete ADR se escribieron en dos días (15-16/09).
- **H4. La documentación dejó de ser un control.** ESTADO (3.422 líneas), FORMULA (2.029), EN-HUMANO (1.815), TABLERO (483), `tablero_datos.js`, 14 `PROMPT-*.md` y 34 ADR (283 KB) en ~95 días. CLAUDE.md ya reconocía "cinco documentos vivos que se contradicen". Cada incidente sumó una regla nueva y la lista de "defaults silenciosos" llegó igual a cinco.
- **H5. Las reglas se agregan después del daño, no lo previenen.** ADR-0015 (todo cambio se presenta en la fórmula) existía cuando se prendieron `RECORD_POR_TEMA` y ε₀+τη. Hay que ver por qué no frenó ninguno de los dos.

---

## 5. Fases

Al terminar cada fase: resumen de máximo 10 líneas y seguí a la siguiente. **Frená y preguntale a Franco sólo si aparece algo que cambia el alcance** (p. ej. una fuga nueva que invalida el 0,1333, o un término prendido que en el código no existe).

### FASE 0 — Blindaje y línea base
1. `git status` y `git log -1`. Anotá el commit exacto sobre el que se audita. Si el árbol está sucio, anotá qué.
2. Corré `python -m pytest tests/ datos/proyectos/tests -q` y `python verificar_regeneracion.py`. Anotá el resultado. Es la línea base.
3. Corré los dos tests-barandilla de ADR-0034: `evaluacion/baseline/tests/test_historia_sin_fuga.py` y `test_harness_es_el_motor.py`.
4. Leé, en este orden: `coordinacion/URGENTE.md`, `coordinacion/ESTADO-REAL-DEL-MOTOR.md`, ADR-0034, `FORMULA-COMPLETA.md` §I.00 (el $P_i$ que corre hoy), §IV.6 y §IV.7, y la tabla "Constantes del motor" y "Parámetros estimados".
5. Chequeá la carpeta `.claude/worktrees/suspicious-lalande-8a89b7` (aparece dentro de la raíz git y contiene una copia del repo). Decí si `.mapa/indexar.py`, `pytest` o `test_raiz_del_repo_una_sola_copia.py` la cuentan, y si infla algún número (LOC, archivos, resultados de búsqueda).

**Entregable:** `00-linea-base.md`.

### FASE 1 — Qué hace el motor HOY (pregunta 1)
1. **Traza real.** Elegí un proyecto de `casos/` o el panel de `REGENERAR` y seguí `nowcast()` de la entrada hasta P(sanción): $P_i$ por legislador → simulación Monte Carlo → puerta B y D → número. Anotá `archivo:línea` de cada paso.
2. **Inventario de banderas.** Listá **todas** las variables de entorno que cambian el cálculo (`os.environ.get`, `os.getenv`) en `modelo/`, `variables/`, `evaluacion/`. Para cada una: valor por defecto **efectivo en el código** (no en la doc), archivo:línea, qué cambia, qué otras banderas la condicionan, y si hay test que la ejercite prendida y apagada. Ya se ven al menos: `RECORD_POR_TEMA`, `INCERTIDUMBRE_LEGISLADOR`, `BETA_DICTAMEN`, `GUARD_ERA`, `SHRINK_RECORD`, `TEMA_AUTO`, `SOBRE_TABLAS`, `QUORUM_ABSTENCIONES`, `MATCH_AUTOR_FUZZY`, `EPSILON0`, `N_SIMS`, `COMBINAR_TEMAS`. Verificá si hay más.
3. **Tabla FORMULA vs código.** Para cada una de las 20 filas del inventario de ESTADO-REAL: ¿existe en código? ¿con qué bandera? ¿qué default? ¿el estado que dice el documento (✅ / ⚪ / 🔲) coincide con lo que el código ejecuta? ¿es alcanzable en el camino que produce el número publicado?
3b. **La fórmula efectiva.** Escribí, en una página, la fórmula que realmente se ejecuta con los defaults actuales. Compará contra §I.00 y §I.0 de `FORMULA-COMPLETA.md`.
4. **Bordes sin medir.** Confirmá, mirando el código, los cinco puntos que ESTADO-REAL dice "nunca medidos": presencia $\pi_i$, share del bloque como pronóstico, desvío individual (ficha no walk-forward), el paso de $P_i$ a $P_{aprob}$, y β en el censo.

**Entregable:** `01-motor-real.md` (incluye la traza, las banderas y la tabla).

### FASE 2 — El sistema de medición (pregunta 2, la causa principal)
El objetivo es saber **en qué número se puede confiar y en cuál no**.
1. **Inventario de toda lectura temporal.** Con `grep`/AST buscá cada corte de historia en `modelo/`, `evaluacion/`, `variables/`, `datos/`: `shift(`, `expanding(`, `rolling(`, `merge_asof`, filtros de fecha con `<=` o `<`, `cumsum`, cortes por período. No te limites a los scripts ya nombrados en ADR-0034. Para cada hit: qué historia ve, si es fecha estricta, si excluye la misma ley, y si alimenta un número publicado o un parámetro del motor.
2. **Clasificación de scripts de medición y estimación.** Tabla con: script · qué produce · ¿importa el motor o reimplementa el récord? · corte de historia · unidad del IC (ley/acta) · ¿alimenta una bandera o constante de producción? Ya se sabe que arman su propio récord con `shift(1)`: `estimar_beta_dictamen`, `estimar_epsilon_tau`, `estimar_psi_arrastre`, `estimar_theta_sobre_tablas`, `diagnostico_senado`, `fase1_rec_por_tema`, `medir_rec_por_tema`, `medir_guard_era`, `validar_beta_dictamen_walkforward`, `validar_sobre_tablas_walkforward`.
3. **Sospechosos sin declarar.** Verificá estos, que **no** figuran en la lista de ADR-0034 y aparecen con `shift(1)`: `modelo/ensemble/src/backtest_cadena.py` (550 líneas), las ocurrencias restantes de `shift(1)` en `nowcast_puertas.py` y `variables/proyecto/src/icg_contexto.py`. Decí si son fuga, uso legítimo, o ninguna de las dos.
4. **Fuentes de fuga que no son historia de votos.** Revisá y clasificá: la ficha `disciplina_individual.csv` (calculada con toda la historia y usada en la rama de bloque y en β), `puerta_a.caracter_de` (dictámenes con `fecha_dictamen <= corte`, 36 pares del mismo día), el 15,3% de votos sin clave de ley, las taxonomías asignadas por LLM (`agente_taxonomias.py`, `tema_por_capitulo.py`: ¿el clasificador vio información posterior a la fecha del acta?), `origen_por_acta` (fecha de publicación), `padron_vigente`, `jefes_bloque`. Para cada una: mecanismo, tamaño estimable, y si ya está cubierta por un test.
5. **Reproducibilidad del 0,1333.** Verificá si el detalle del censo limpio está en disco y corré `evaluacion/baseline/src/resumen_censo_limpio.py`. Si el detalle no está, corré `censo_detalle_paralelo.py --procesos 3` y esperá (~35 min). Confirmá skill global, era vigente, rama récord, rama bloque y IC. Si no reproduce, **frená y avisá**.
6. **Cobertura de la banda.** Corré `modelo/ensemble/src/medir_tau_limpio.py` y confirmá el 63,6% y el sesgo de −6,9 votos. Comparalo con lo que hace `agregador.backtest` (línea de bloque observada) y decí exactamente qué mide cada uno.
7. **Qué otros parámetros de producción dependen de mediciones contaminadas.** Lista cerrada: constante o bandera → medición que la justificó → ¿usa la fuga? → ¿re-medida?

**Entregable:** `02-sistema-de-medicion.md`, con la tabla de scripts y un veredicto por número: **CONFIABLE / CONFIABLE CON RESERVA / NO CONFIABLE**.

### FASE 3 — Re-litigio de los 34 ADR
Leé **cuerpo completo** de cada ADR, no sólo el encabezado (`coordinacion/DECISIONES/`). Si querés paralelizar, lanzá subagentes de lectura por lotes de ADR y consolidá vos; la tabla final es tu responsabilidad.

Para cada ADR una fila con:
- número, fecha, título corto;
- **quién decidió** (Franco / Valle / Claude en sesión delegada / Claude con permiso puntual);
- estado declarado en el encabezado y **estado real** (verificado en código o dato);
- **medición que lo justifica**: qué script, qué harness, qué historia de récord;
- **¿esa medición depende de la fuga o de un espejo?** (sí / no / parcial / no aplica);
- **¿sigue vigente en el código?** (bandera, default, archivo:línea);
- **¿la documentación coincide con el código?** (FORMULA, ESTADO, EN-HUMANO, tablero);
- **veredicto**: `VIGENTE-SÓLIDO` · `VIGENTE-SIN-EVIDENCIA` · `VIGENTE-EVIDENCIA-ROTA` · `INACTIVO` · `SUPERSEDIDO` · `REGISTRO-HISTÓRICO` (no decide nada ya);
- **destino en la consolidación** (ver Fase 5): en cuál de los 5-7 ADR nuevos queda absorbido, o `DESCARTABLE` si no aporta ninguna regla viva. Qué **regla** sobrevive de él (una línea) y cuál se pierde.

Atención especial a estas cadenas y contradicciones:
- **0012 → 0016 → 0025.** Formulación por puertas y doctrina "de la parte al todo": ¿el código cumple la doctrina? ¿queda algún ajuste aplicado al agregado en vez de al legislador (δ agregado, ε clip)?
- **0018 (guard de era)** con la nota de 0031 y 0033.
- **0024 → 0028** (enmienda) y **0026 → 0034** (enmienda): ¿los encabezados reflejan el estado real? ¿hay ADR con estado "prendido" o "aplicado" que ya no lo esté?
- **0025:** el 99,88% de cobertura frente al 63,6% medido. ¿Qué dice hoy el ADR? ¿Qué dice la doc que ve el usuario?
- **0027 y 0023:** código implementado y no enganchado. ¿Está muerto, o lo importa algo?
- **0029:** datos parciales por falta de crédito de API. ¿Qué parte del dato parcial se usa en producción?
- **0009 (BORRADOR neutralizado):** ¿queda algún otro ADR o documento con contenido que ya no vale y sigue en el árbol?
- **Numeración y duplicados:** dos archivos 0009.

También armá la **cronología** 25-06 → 28-09: cada ADR, cada término que se prendió o apagó, con `git log -S` / `git blame` para fechar el cambio de default de cada bandera, y qué medición se citó ese día. Marcá los puntos de inflexión (25-08, 03-16/09, 15-16/09, 28-09) y decí cuál fue el primero en que el control se perdió de verdad, con evidencia.

**Entregable:** `03-adr.md` (tabla de 34 filas + cadenas + cronología).

### FASE 4 — Complejidad, medida
1. **Por módulo del motor:** LOC de producción, LOC de scripts de estimación/medición, cantidad de banderas, cantidad de ramas detrás de bandera apagada. Base de referencia: 194 `.py`, ~44.316 LOC totales, `modelo/ensemble` 5.227, `evaluacion/baseline` 5.585, `variables/proyecto` 4.248.
2. **Código que no participa del número publicado.** Para cada función o script del alcance: ¿se llama desde el camino que produce P(sanción) con los defaults actuales? (`.mapa/buscar.py --archivo <ruta>`, más el análisis de llamadas que necesites). Clasificá en: `EN EL CAMINO` · `DETRÁS DE BANDERA APAGADA` · `SÓLO MEDICIÓN/ESTIMACIÓN` · `NO LO LLAMA NADIE`.
3. **Matriz de banderas.** Qué combinaciones existen, cuáles están testeadas, cuáles se contradicen o dependen unas de otras (por ejemplo `RECORD_POR_TEMA` frente a `TEMA_AUTO`).
4. **Documentos vivos.** Elegí 10 hechos clave (skill publicado, banderas prendidas, cobertura de banda, estado de β, estado de `RECORD_POR_TEMA`, τ, ε₀, número de tests, etc.) y buscá qué dice cada documento vivo (ESTADO, FORMULA, EN-HUMANO, TABLERO, `tablero_datos.js`, README de módulo, ESTADO-REAL, CLAUDE.md, MAPA.md). Matriz de contradicciones. El documento que **el código** contradice es el hallazgo más importante.
5. **Reglas acumuladas.** Contá las reglas y controles que el repo se impuso (CLAUDE.md, ADR-0015, regla del expediente, defaults silenciosos, URGENTE, tablero, mapa, hook). Para cada una: ¿se cumplió en los cambios de septiembre? Verificalo con `git log`, no con la doc. ¿Cuáles habrían detectado la fuga si se hubieran aplicado?
6. **Peso del proceso frente al del código.** Proporción entre líneas de documentación/ADR/PROMPT y líneas de código del motor.

**Entregable:** `04-complejidad.md`.

### FASE 5 — Propuesta de consolidación: de 34 ADR a 5-7, reglas simples y anclaje a la realidad
Esta fase **propone y redacta borradores**; no ejecuta nada. Requisito de Franco: *"algo controlable y que se pueda entender"*.

**5.1 Los 5-7 ADR consolidados.**
- Cada uno cubre **un tema**, tiene **como máximo 2 páginas** y sigue una estructura fija: **(1) La regla** (una frase) · **(2) Por qué** (un párrafo, con el número que la justifica y cómo se midió) · **(3) Cómo se verifica** (el test o comando que la comprueba, con su ruta) · **(4) Qué la invalida** (la condición que obliga a revisarla) · **(5) Estado real hoy** (verificado en código, con archivo:línea).
- Un ADR consolidado **describe el estado real verificado en la Fase 1-4**, no el histórico. La historia (por qué se llegó ahí) queda como una línea con el número del ADR original, que se conserva intacto en el archivo.
- Ningún término prendido puede figurar en un ADR consolidado como sólido si la Fase 2 lo marcó `NO CONFIABLE`: figura con su estado real (sin medición, evidencia rota, etc.).
- **Punto de partida, no vinculante** (armado sólo por títulos; podés reagrupar, partir o fusionar si el cuerpo de los ADR lo pide, justificándolo):

| # | tema tentativo | ADR que absorbería |
|---|---|---|
| 1 | Repo, datos y definiciones compartidas | 0001, 0002, 0009 (y su borrador), 0010, 0011, 0014, 0019, 0020, 0021 |
| 2 | Voto individual: desvío, linajes, récord, guard de era, dictamen | 0003, 0004, 0005, 0017, 0018, 0022 |
| 3 | Formulación y salida del número: puertas, mayoría, parte al todo | 0006, 0007, 0012, 0013, 0016 |
| 4 | Incertidumbre y coyuntura: ε₀+τη, ICG | 0008, 0025 |
| 5 | Medición y evidencia: unidad = expediente, walk-forward, cómo se prende una bandera | 0015, 0034 y la regla del expediente (FORMULA §IV.6-IV.7) |
| 6 | Línea de tema, capítulo y origen: cerrada | 0023, 0024, 0026 a 0033 |

- **Para el 6:** decidí si esa línea merece un ADR propio (por ejemplo, "qué se probó, qué dio, cuándo se reabre") o si se reduce a una nota dentro de otro. Si se reabre alguna vez, ¿con qué medición mínima?
- Cada ADR original tiene que aparecer en **exactamente un** destino de la tabla, sin huérfanos. Entregá esa tabla completa (34 → 5-7).
- **Redactá los borradores completos** de los 5-7 ADR en `coordinacion/AUDITORIA-2026-09/adr-consolidados/`.

**5.2 El documento de reglas simples.**
- **Una página**, **máximo 10 reglas**, en lenguaje llano.
- Cada regla: enunciado en una línea + **cómo se comprueba** (un test, un comando o una consulta a un archivo) + a cuál de los 5-7 ADR responde.
- Las reglas tienen que salir de lo que **realmente falló** en septiembre, no de una lista genérica. Ejemplos de candidatas para evaluar (no son obligatorias): "ninguna bandera se prende sin medición hecha con el motor real"; "toda historia cortada por fecha estricta y otra ley"; "todo IC re-muestrea leyes"; "un documento vivo, generado desde el código"; "lo que no se mide, no afecta el número".
- Decí qué **reglas actuales** de `CLAUDE.md`, ADR-0015, `PROTOCOLO-GIT.md` y FORMULA §IV se reemplazan, cuáles se conservan y cuáles se eliminan por redundantes. **El resultado debe tener menos reglas que hoy, no más.**
- Redactá el borrador en `coordinacion/AUDITORIA-2026-09/REGLAS-borrador.md`.

**5.3 El anclaje a la realidad.**
Evaluá y proponé el mecanismo mínimo para que el modelo **siga a los datos** y para que cualquier desvío se detecte solo. Cubrí como mínimo estas piezas, cada una con costo estimado (horas de trabajo, minutos de cómputo) y qué falla concreta de septiembre habría atrapado:
- **Una sola métrica de verdad.** El skill walk-forward del voto individual **calculado con el motor real** (no con un espejo), con IC por ley, cortado por era, con un número único y una fecha de cálculo. ¿Existe ya como script? ¿Cuánto cuesta correrlo?
- **Calibración de lo que se declara.** Cobertura observada frente a cobertura declarada de la banda (hoy 63,6% frente a 90%), y calibración de las probabilidades (Brier o curva de confiabilidad) sobre los resultados reales, incluidos los de la cámara: el paso $P_i \to P_{aprob}$ **nunca se contrastó** contra resultados con $P_i$ pronosticadas.
- **Una versión rápida para el día a día.** El censo completo tarda ~35 min. Proponé una **muestra por leyes** (con el tamaño que dé un IC útil, calculado) que corra en minutos y sirva como control de cada cambio del motor, y la corrida completa reservada para cambios que prenden o apagan algo.
- **Un gate automático.** Un test o job de CI (ya existe `.github/workflows/tests.yml`) que **falle** cuando un cambio en el motor empeore skill o cobertura más allá de una tolerancia con IC, o cuando una bandera cambie de valor sin una medición referenciada. Definí la tolerancia con números.
- **Un registro de banderas y parámetros generado desde el código**: nombre, default efectivo, medición que lo respalda, fecha, IC. Que reemplace la tabla escrita a mano de FORMULA (`Constantes del motor` y `Parámetros estimados`), que es la que hoy se desactualiza.
- **Monitoreo hacia adelante.** El bot ya recolecta votaciones nuevas: ¿se puede comparar automáticamente cada acta nueva contra lo que el motor habría predicho **antes** de que ocurriera (nowcast congelado con fecha), y acumular esa serie? Es la única evidencia que no puede tener fuga. Evaluá factibilidad con lo que hay en `datos/bot_recoleccion` y `.github/workflows/bot-diario.yml`, sin modificarlos.
- **Qué se corta.** Qué documentos vivos dejan de existir o pasan a generarse (ESTADO, EN-HUMANO, TABLERO, `tablero_datos.js`, MAPA.md), con la misma vara: cada dato del proyecto tiene **un solo lugar** donde se escribe.
- Para cada pieza, dá **una recomendación y una alternativa más barata**, y ordenalas en una secuencia de implementación realista con criterio de salida verificable.

**Entregable:** `05-consolidacion-y-anclaje.md` (la tabla 34 → 5-7, el mecanismo de anclaje y la secuencia), más `adr-consolidados/` y `REGLAS-borrador.md`.

### FASE 6 — Síntesis y devolución
Un único informe, `AUDITORIA-INTEGRAL-2026-09.md`, con estas secciones y en este orden:

1. **Qué hace el modelo hoy.** Una página. La fórmula efectiva, con los defaults verificados.
2. **En qué número se puede confiar.** Tabla actualizada de ESTADO-REAL con correcciones, más el veredicto de la Fase 2.
3. **Dónde se perdió el control.** Causas raíz ordenadas por peso, cada una con evidencia. Decí explícitamente cuáles de H1-H5 se confirman, cuáles se refutan y cuáles quedan abiertas.
4. **Dónde se complejizó.** Las mediciones de la Fase 4.
5. **Propuesta de poda del código. NO se ejecuta.** Candidatos a apagar, archivar, consolidar o borrar (recordá: nada se borra, se mueve), ordenados por riesgo y ahorro, cada uno con criterio de salida verificable y con el test que debería fallar si la poda rompe algo.
6. **De 34 ADR a 5-7, reglas simples y anclaje a la realidad.** Resumen de la Fase 5: la tabla de consolidación, las reglas (máximo 10) y el mecanismo de anclaje con su secuencia. Enlazá a los borradores.
7. **Decisiones que le tocan a Franco.** Lista cerrada, cada una con la opción recomendada y su costo. Incluí explícitamente: qué hacer con la banda declarada al 90%, si se re-estiman β/δ/θ/ψ con el offset limpio, qué política de prender banderas se adopta (por ejemplo, ninguna bandera se prende sin medición hecha con el motor real y con IC por ley, y sin OK de Franco), cuántos ADR finales (5, 6 o 7) y qué gate automático se implementa primero.
8. **Qué no se pudo verificar y por qué.**

**Tono del informe:** directo, con números, sin explicar conceptos que Franco ya domina (finanzas, estadística, ciencia política). Sin teatro.

---

## 6. Criterio de terminado

- Las 6 entregas y el informe final existen en `coordinacion/AUDITORIA-2026-09/` y cada afirmación tiene referencia y nivel de confianza.
- Los 34 ADR tienen veredicto **y destino** en la tabla de consolidación, sin huérfanos ni duplicados.
- Existen los borradores de los 5-7 ADR (cada uno ≤ 2 páginas, con la estructura fija) y de `REGLAS-borrador.md` (una página, ≤ 10 reglas, cada una con su comprobación).
- El mecanismo de anclaje tiene, por pieza, costo, recomendación, alternativa barata y orden de implementación.
- El 0,1333 y el 63,6% están reproducidos, o hay un aviso explícito de que no reproducen.
- Cada bandera del alcance tiene su default efectivo verificado.
- `git status` muestra cambios **únicamente** en `coordinacion/AUDITORIA-2026-09/` y en `Archivos_Borrar/`.
- Los tests de la línea base dan igual que al empezar.

Al final, mostrale a Franco: (a) el resumen de la sección 3 del informe (causas raíz) en no más de 15 líneas, (b) la tabla 34 → 5-7 y las reglas del borrador, (c) la lista de decisiones de la sección 7, y (d) cualquier cosa que hayas encontrado y que cambie el alcance de una segunda ronda (datos, bots, workflows).
