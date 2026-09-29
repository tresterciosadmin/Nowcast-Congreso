# 03 — Los 34 ADR, re-litigados

**Commit auditado:** `bcc62b3`. Los ADR son 35 archivos (hay **dos `0009`**): `0001`-`0034` más el `0009-BORRADOR`. Cada uno se leyó **completo** por un lote de lectura (Sonnet; el lote de la cadena central, Opus o el auditor principal) y se verificó contra el código. Las fichas completas, con `archivo:línea` y nivel de confianza por afirmación, están en `adr-fichas/lote_*.md`. Rúbrica de veredictos: `00-preregistro.md`.

**Quién decidió** se lee de la línea del propio ADR; el autor de git no discrimina: los commits de Claude Code llevan el nombre de Franco (`Franco Marconi` firma 129 de 243 commits; `ThiagoPP260` 42, el "Valle" de los ADR 0009-0014 [I]; los bots 72).

## 1. Tabla de veredictos y destino

Fecha = la del encabezado. **Fuga** = ¿la medición que lo justifica depende de la fuga o de un espejo? (s / n / p = parcial / n.a.). Destino: C1 repo y datos · C2 voto individual · C3 formulación y salida · C4 incertidumbre y coyuntura · C5 medición y evidencia · C6 línea tema/capítulo/origen (cerrada).

| ADR | fecha | decidió | estado declarado → real | fuga | veredicto | destino | regla que **sobrevive** / que **se pierde** |
|---|---|---|---|:-:|---|:-:|---|
| **0001** | 06-25 | s/d (commit de Franco) | Aceptada → reglas 1, 3, 4 se cumplen; "una rama" sin uso; "datos fuera de git" **falsa** | n.a. | VIGENTE-ESTRUCTURAL | C1 | módulo/dueño/contrato, ADR para cambiar un contrato / datos fuera de git, una rama por módulo |
| **0002** | 06-25 | "el equipo" | Aceptada → semilla → canónica → bot; el punto 3 **falso** (el bot abre un issue, no agrega); hueco Diputados 2020-23 no declarado | n.a. | VIGENTE-ESTRUCTURAL | C1 | semilla estática → canónica propia → bot que detecta / "el bot agrega" |
| **0003** | 07-01 | Valle + Claude | aceptada → existen la ficha y el simulador; la defección nunca se construyó; los pivotes los cerró 0030 | **s** (premisa 0,99 = línea observada) | VIGENTE-EVIDENCIA-ROTA | C2 | el desvío se modela respecto del bloque / el plan de 4 piezas y sus gates |
| **0004** | 07-02 | Valle + Claude | aceptada → `disciplina.py` implementado; **el ADR está truncado a mitad de palabra desde su primer commit**; el motor consume la variante *conducta* (0,073), no la "indisciplina total" (0,179) | n.a. | VIGENTE-ESTRUCTURAL | C2 | desvío v2 por conducta / la "línea bottom-up" (no es la del motor) |
| **0005** | 07-10 | Franco | aplicado; 10 linajes y ventanas idénticas; OTRO/PROVINCIAL hoy 22,6% (dice ~19%) | n.a. | VIGENTE-ESTRUCTURAL | C2 | 10 linajes con ventanas por fecha / Proyecto Sur ya no es PROGRESISMO |
| **0009-BORRADOR** | 08-07 | Valle (iba a decidir) | neutralizado → **sigue versionado 53 días**; su nota a `PENDIENTES-DE-BORRAR.md` es falsa (ese archivo no existe) | n.a. | SUPERSEDIDO (por 0009) | C1 · **DESCARTABLE** | nada; el texto vive en `git show fd2aa2b` |
| **0009** | 08-07 | Valle | ACEPTADO → implementado (`embudo.py:708`, `upsert_bot`, cuarentena), pero **no alimenta P(sanción) desde 0012**; `proyectos.db` 115.495 filas | n.a. | VIGENTE-ESTRUCTURAL | C1 | merge por campo, giro acumulado ≠ giro al ingresar, cuarentena con freno por invariante / "cuelga todo el nowcast" |
| **0010** | 08-20 | Claude "con Valle" | aceptada → `rutas.py` sí; **hook no instalado**; el test de completitud **no puede fallar** (`RAIZ` es ancestro de todo) | n.a. | VIGENTE-ESTRUCTURAL | C1 | `rutas.py`, MAPA generado / la garantía de completitud, el hook, las cifras (246 líneas, 2 módulos) |
| **0011** | 08-21 | Claude "con Valle" | aceptada → `PROTOCOLO-GIT` corregido; la premisa "`-q` da 0 con `!`" **no se reproduce**; los tests usan `-q` | n.a. | VIGENTE-ESTRUCTURAL | C1 | preguntarle a git con ruta relativa y `-v` / la prohibición del exit code |
| **0014** | 08-25 | Valle decide, Claude implementa | aplicada; 5 módulos re-exportan; `MAYORIAS` sin consumidor; `BANCAS` copiada 5 veces | n.a. | VIGENTE-ESTRUCTURAL | C1 | lo compartido vive una vez, se re-exporta y se controla por identidad / — |
| **0017** | 09-04 | **Claude, sesión autónoma** ("Franco no está disponible… No hagas preguntas") | "Aceptada (a revisar por Franco)" → **nunca se revisó**; parser y enlace aplicados; A y C identidad; dice β "apagado" (ON desde el 14-09) | n.a. | VIGENTE-ESTRUCTURAL | C2 | `desconocido` ≠ único; enlace = `acta_expediente_todas` / la reserva sin levantar |
| **0019** | 09-06 | Franco | aplicado; **afecta el número** (`GUARD_ERA` corta el récord en 2023-12-10) | n.a. | VIGENTE-ESTRUCTURAL | C1 | una sola frontera de eras (`definiciones.GOBIERNOS`) / — |
| **0020** | 09-08 | Franco | aplicado; `proyectos.db` 87,3 MiB (falla el test a 95); trigger de LFS "90 MB" vs test 50/95 | n.a. | VIGENTE-ESTRUCTURAL | C1 | las bases viajan; aviso a 50, falla a 95 / "no viaja" (`tests.yml:26`) |
| **0021** | 09-08 | Franco | aplicado; raíz por `rutas.py` sólo en 9 archivos (quedan 91 `parents[N]`); "una sola copia" mide la búsqueda de la raíz, no las copias | n.a. | VIGENTE-ESTRUCTURAL | C1 | `definiciones.caracter_de_dictamen`, raíz por `rutas.py` / — |
| **0022** | 09-14 | Franco + Claude | D2 (Daer) aplicada; D1 (disidencia = minoría) sólo reconstruida para el Senado; "205 actas" son 205 **firmas** | p (re-estimación con offset espejo) | VIGENTE-ESTRUCTURAL | C2 | en el Senado la disidencia es minoría; Daer → massismo / la cifra "205 actas" |
| **0023** | 09-15 | Claude (mandato de Franco) | APLICADO → parquet estático del 15-09 sin regeneración ni consumidor; cifras del ADR (6/47) ≠ parquet (7/35) | n.a. | INACTIVO | C6 (+C1) | agregar sin reemplazar; el 9,8% de leyes aprobadas pierde algún tramo / la cifra 6/47 |
| **0024** | 15/16-09 | Claude (mandato de Franco) | "PROBADO — NO SE RECOMIENDA" → banderas apagadas; el banner de 0028 lo contradice; **el brazo `primaria` del harness nunca pasaba `tema`** | **s** (+ bug de rama) | INACTIVO | C6 (+C5) | lo manual gana; sin dato, no-op / el "dónde SÍ está la ganancia" (0026) |
| **0026** | 09-16 | Claude "con autonomía delegada" | **PRENDIDO → APAGADO el 28-09**; el encabezado sigue diciendo PRENDIDO | **s** (dos veces) | SUPERSEDIDO (por 0034) | C6 (+C2) | un grado de libertad, encoger al récord general, en logit / el "+11,06%" |
| **0027** | 09-16 | Claude (mandato) | "no enganchado, decisión pendiente" → decidido en 0030; sólo tests y `validar_*` lo importan | n.a. | INACTIVO | C6 (+C3) | P(proyecto) no es un evento: se simula con shock común / — |
| **0028** | 09-16 | Claude (mandato) | "cierra la pregunta" → evidencia rota: **control idéntico al tratamiento** (0,0 exacto en 232 actas) | **s** | REGISTRO-HISTÓRICO | C6 (método → C5) | un control que da idéntico al tratamiento es una alarma / la conclusión "ninguna regla mejora" |
| **0029** | 09-16 | Claude con permiso puntual de Franco | "PARCIAL, sin crédito de API" → crédito recargado el mismo día; **ningún dato se usa en producción** | p | INACTIVO | C6 | clave de capítulo = `(proyecto_id, titulo_num, capitulo_num)` / la cobertura ampliada, los conteos 437→242→471 |
| **0030** | 09-17 | Claude, sesión delegada | CERRADA → sin cambios de motor; dice "0026 prendido" y "β apagado" (falsos); el diagnóstico del Senado **tiene la fuga** | **s** (Senado) | REGISTRO-HISTÓRICO | C6 (+C5) | medir la fracción con dato condicionado real antes del skill; criterios escritos antes / el diagnóstico del Senado |
| **0031** | 09-17 | Claude, sesión delegada | "guard confirmado" sólo vale para tasa cruda (0033 la llama "el error de 0031"); la FASE 3 "prendida" está **dormida** | n | REGISTRO-HISTÓRICO | C6 (+C5) | todo fallback avisa con un contador agregado / "el guard queda confirmado también para el tema" |
| **0032** | 09-21 | Claude, sesión delegada | MEDIDO, sin cambios en el motor; tensión: 0032 "no se cierra" vs 0030/0031 "cerrada"; el "~1,7×" **no está derivado** | n.a. | REGISTRO-HISTÓRICO | C5 (+C6) | la unidad efectiva es el expediente; un rasgo intra-era debe sobrevivir a la partición por ley entera / el "1,7×", `gobernadores.csv` |
| **0033** | 09-27/28 | Claude, sesión delegada | MEDIDO, sin cambios; ρ_her no existe en el motor; **descubrió** la fuga del mismo día; los niveles (0,173/0,092) los superó 0034 | p (fecha sí; misma ley no) | REGISTRO-HISTÓRICO | C6 (+C2, C5) | lo individual no persiste entre gobiernos, persiste el linaje; no se prende lo que predice peor / los niveles de skill, B1/B2 |
| **0034** | 09-28 | Claude, sesión de saneamiento delegada | HECHO → **verificado**: el 0,1333 reproduce byte a byte; la receta de reproducción **falla en un checkout limpio** (`KeyError`, depende de una bandera) | n | **VIGENTE-SÓLIDO** (con reservas: τ/β/ficha no re-medidos, IC con 300 réplicas) | C5 | fecha estricta y otra ley; el harness importa el motor; IC por ley / el "~1,7×" |

<!--FILAS_C-->

## 2. Las cadenas y contradicciones que pedía el prompt

- **0012 → 0016 → 0025 (doctrina "de la parte al todo").** Ver la tabla de lote C. Hecho verificado por el auditor principal: el código cumple la doctrina en el desvío, ε₀ y el piso de 0,02 (todos por legislador) y en el shock τη (la excepción 2 de 0016); **no la cumple** en que con `INCERTIDUMBRE_LEGISLADOR=0` reaparece el clip agregado 0,01 (`ensemble.py:367-376`), en que los pasos A y C —"δ agregado"— siguen ejecutándose con coeficientes en cero (≈300 líneas), y en que el piso de 0,02 no figura en FORMULA §I.00.
- **0018 (guard de era) con 0031 y 0033.** El guard está ON (`nowcast_puertas.py:119`). Su evidencia (0,1304 → 0,1611; valles 2015-19 y 2019-23 "cerrados") salió del harness con fuga: con el limpio, 2019-2023 = 0,011 [−0,20; 0,11]. 0031 lo "confirma" con una correlación de tasas crudas que 0033 llama "el error de 0031"; 0033 da +3,6% sin guard con fecha estricta pero **sin excluir la misma ley**. **Con el motor completo nadie midió el guard encendido/apagado** (`GUARD_ERA=0` deja sin récord todo lo anterior a 2023). La medición independiente de esta auditoría —quitando sólo el corte por era— da **+0,0028 de Brier a favor del guard [−0,0006; +0,0066]** (≈ 2%, incluye 0) y **cero efecto en la era vigente**.
- **0024 → 0028 y 0026 → 0034 (enmiendas).** Los encabezados **no reflejan el estado real**: 0026 dice PRENDIDO (está APAGADO desde el 28-09); 0024 y 0028 tienen un banner que contradice su propio cuerpo; 0027 sigue "pendiente" cuando 0030 ya decidió; 0029 sigue "sin crédito" cuando el crédito se recargó el mismo día. **No queda ningún ADR de la línea tema/capítulo realmente "prendido" en el código.**
- **0025 (99,88% frente a 63,6%).** Ver lote C y `02` §6: el ADR nunca se corrigió; `tablero_datos.js` **se contradice a sí mismo** (`:253` dice 63,6% y `:318` "99,88% … del lado seguro"); EN-HUMANO conserva el 99,88%; el panel HTML publicado dice 98,01% y el motor da 61,3%.
- **0027 y 0023 (código implementado y no enganchado).** Están **muertos** para el número: sólo los importan sus tests y scripts de validación (`composicion_capitulos.py`, 145 líneas; `votacion_por_articulo`, 222).
- **0029 (datos parciales).** **Ninguna parte del dato se usa en producción** (`tema_por_capitulo.parquet` no tiene lector; `proyecto_taxonomias` sólo se lee con `TEMA_AUTO` o `RECORD_POR_TEMA`, ambos apagados, y el panel no pasa `proyecto_id`).
- **0009-BORRADOR neutralizado.** Sigue versionado; y **el patrón "copiar a `Archivos_Borrar/`, neutralizar, anotar" falla** porque `Archivos_Borrar/` está ignorado por git: `CONECTAR-GIT.md` (26 líneas, "NO LEER") y el borrador apuntan a copias que no existen. Sigue en el árbol código neutralizado: `backtest_cadena.py` (550) y su test (330), `comparar_vias_icg.py` (298), los stubs de `ensemble.py`.
- **Numeración.** Dos `0009` (el borrador y el definitivo); "34 ADR" son 35 archivos.
- **Los scripts de 0033 no figuran en la lista de espejos que marca ADR-0034** (`record_por_origen_brazos.py` sigue apuntando al detalle del 27-09, el del harness espejo) y no se re-corrieron.

## 3. Quién decidió

| | ADR | n |
|---|---|---:|
| sin campo "Decide" en el encabezado | 0001-0017 y 0022, 0024 | 19 (54%) |
| Franco (explícito) | 0018, 0019, 0020, 0021, **0025** ("Hagamos el cambio") | 5 |
| **Claude en sesión delegada o con mandato** | 0023, 0026, 0027, 0028, 0029, 0030, 0031, 0032, 0033, 0034 | **10** |
| Claude en sesión autónoma sin Franco | 0017 | 1 |

De los 12 ADR entre 0023 y 0034, **10 los decidió Claude en una sesión delegada** y uno solo (0025) figura como decisión de Franco. Aun así, **los tres commits que prendieron un término** (`ec5fd05` β, `64ff248` ε₀+τη, `0a7a03f` récord por tema) llevan una cita textual de Franco autorizando ("dale, prendelo y corre el panel completo"; "Hagamos el cambio"; la delegación en `PROMPT-MULTITEMA-V2.md`): el OK humano existió, **sobre la evidencia que presentó el mismo agente** y sin una contrastación independiente.

## 4. Cronología 25-06 → 28-09 (de `git log -G`, no de la documentación)

Repo: 243 commits desde el 25-06 (Franco 129, `bot-recoleccion` 61, `ThiagoPP260` 42, `bot-nowcast` 11). 19 de 160 mensajes humanos tienen menos de 16 caracteres.

| fecha | qué | commit | medición citada ese día |
|---|---|---|---|
| 06-25 → 07-10 | ADR 0001-0005; estructura, semilla→canónica→bot, desvío y linajes | — | "la disciplina en disputadas es 96,4%" (descriptivo) |
| 08-14 | `DESVIO_MIN_INDIVIDUAL = 0,02` y `P_INCERTIDUMBRE = 0,01` (piso y clip) | `5044142` "Update a medias (esperando tokens)" | pedido de Valle; **ninguna** |
| 08-22 | ADR-0012/0013: formulación por puertas; se da de baja la v1; el empate no aprueba | — | recuentos de ejemplo |
| **08-25** | **Primera inflexión.** Revisión metodológica: cuatro problemas "llevaban semanas en producción y ninguno era un bug: eran supuestos" (aprobados función por función). `puerta_a` con coeficientes en cero y `MIN_HIST_INDIVIDUAL = 8`. Nace ADR-0015 | `5aff5b0` "Megacanje" | revisión manual |
| 09-04 | ADR-0017 (sesión autónoma) y `REGENERAR.ps1` | — | 193 PDF, 340 controles |
| **09-06** | **Segunda inflexión — el control se pierde acá.** En **un solo commit `aaa`** (`2dbad10`, 13+ archivos, FORMULA +1.303 líneas, ADR 0016-0019): `GUARD_ERA` y `SHRINK_RECORD` **ON**, `MIN_HIST_INDIVIDUAL` 8→1, **nace el harness con `shift(1)` por fila** y los estimadores `estimar_beta_dictamen`, `estimar_epsilon_tau`, `estimar_psi_arrastre`, y FORMULA §IV.4 prescribe "`shift(1)` + `expanding`" | `2dbad10` | skill 0,1304 → 0,1611 sobre 741.275 votos, **con la fuga** |
| 09-08 | ADR-0020/0021 (bases por git, raíz única) | `459e15d` | tests |
| **09-14** | β **PRENDIDO** ("dale, prendelo y corre el panel completo"). El panel salió **byte a byte idéntico**: es hipotético, β no actúa | `ec5fd05` 23:02 | walk-forward 0,1725 → 0,1591 con el offset del espejo |
| **09-15** | `TEMA_AUTO` (16:21), sobre tablas cerrado (20:23), ε₀+τη implementado (20:39) y **prendido a las 22:10** ("Hagamos el cambio"): el panel pasa de **0,9801 a 0,6132** | `fa4c572`, `fa9a20c`, `24f5969`, `64ff248` | "99,88% de cobertura" (oráculo); paneles: 0,9801 → 0,5277 y → 0,6132 |
| **09-16** | `RECORD_POR_TEMA` **PRENDIDO** 10:31 ("podés prender banderas si el censo completo mejora"). ADR 0025-0029 en el día; siete ADR (0023-0029) en dos días | `0a7a03f` | **+11,06% de Brier**, con la fuga |
| 09-17 → 09-21 | ADR-0030/0031/0032: se cierra la línea de capítulos, guard "confirmado", firma temática descartada | — | correlaciones, recuentos |
| 09-27/28 | ADR-0033 **descubre** que el harness filtra el mismo día | `daf9474` | 0,173 / 0,092 / 0,193 |
| **09-28** | **Tercera inflexión.** ADR-0034: se arregla el corte (`<=` → `<`), el harness importa el motor, el número pasa a **0,1333**, `RECORD_POR_TEMA` **OFF** | `f449af3`, `bf831aa`, `8b310c1` 18:51 | censo limpio, 34 min |
| 09-28 19:37 | pull con datos del bot (`bcc62b3`) | — | — |

**El primer punto en que el control se perdió de verdad: el 06-09 (`2dbad10`, "aaa")**, y no el 25-08. El 25-08 fue una pérdida de *comprensión* (cuatro supuestos aprobados función por función) que se detectó y se atacó con ADR-0015. El 06-09 fue la pérdida de la *verificabilidad*: el mismo commit puso el instrumento de medición con fuga, los estimadores que heredaron su offset, la regla de método que prescribía el idioma con fuga y tres términos prendidos con cifras medidas con él, dentro de un commit de 13 archivos con el mensaje `aaa`. **Nada de lo que vino después (β, ε₀+τη, récord por tema) pudo ser verificado por construcción**, aunque cada uno de esos commits cumplió, en la forma, la regla del repo.
