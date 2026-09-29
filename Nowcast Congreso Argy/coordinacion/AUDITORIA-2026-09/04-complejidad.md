# 04 — Dónde se complejizó, medido

**Commit auditado:** `bcc62b3`. Alcance de código: `modelo/`, `variables/`, `evaluacion/`, `casos/`, `producto/`, `definiciones.py`, `rutas.py` (105 archivos `.py`). Conf.: **V** = medido o visto · **I** = inferido. Los scripts de medida están en `Archivos_Borrar/auditoria/` (`clasificar_codigo.py`, `clasificacion_codigo.csv`).

## 1. Por módulo: líneas, código real y quién lo usa

"Código" = líneas con tokens de código (sin comentarios ni docstrings). Categorías por **grafo de imports** (AST) desde el punto de entrada del panel publicado (`casos/nowcast_puertas_html.py`) más los scripts que corre `REGENERAR.ps1` y los workflows. [V]

| módulo | archivos | líneas | código | % código | código en el **camino** | insumos (REGENERAR) | sólo medición/estimación | nadie lo llama | tests |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `modelo/ensemble` | 29 | 7.265 | 4.310 | 59% | 1.501 | — | 1.318 | 57 | 1.434 |
| `modelo/agregador_institucional` | 2 | 754 | 476 | 63% | 288 | — | — | — | 188 |
| `modelo/voto_individual` | 2 | 595 | 399 | 67% | — | 264 | — | — | 135 |
| `variables/bloque` | 6 | 1.575 | 1.080 | 69% | 568 | — | — | — | 512 |
| `variables/proyecto` | 25 | 5.770 | 3.850 | 67% | 621 | 1.065 | 97 | 971 | 1.096 |
| `variables/embudo` | 5 | 1.217 | 818 | 67% | — | — | — | 659 | 159 |
| `variables/(otros)` | 3 | 493 | 349 | 71% | — | 221 | — | 57 | 71 |
| `evaluacion/baseline` | 29 | 6.321 | 4.328 | 68% | 542 | — | **3.281** | — | 505 |
| `casos` + `producto` | 2 | 941 | 700 | 74% | 334 | — | — | 366 | — |
| `definiciones` + `rutas` | 2 | 469 | 172 | 37% | 172 | — | — | — | — |
| **TOTAL alcance** | **105** | **25.400** | **16.482** | **65%** | **4.026** | **1.550** | **4.696** | **2.110** | **4.100** |

- **Del código no-test del alcance (12.382 líneas), sólo 4.026 (33%) están en el camino que produce el número del panel.** La medición y estimación pesan más (4.696, 38%) que el motor. [V]
- El **motor** propiamente dicho, `nowcast_puertas.py`, son 980 líneas: 492 de código (50%), 197 de comentarios y 225 de docstrings. Es decir, **la mitad del archivo central es prosa** (`bloque.py`: 68% código; `agregador.py`: 58%; `ensemble.py`: 52%). [V]
- Referencia del prompt (194 `.py`, 44.316 líneas): **confirmado** (194 archivos y 44.316 líneas en todo el repo; 25.400 son del alcance). [V]

## 2. Código que no participa del número publicado

Con los defaults de hoy y el panel B (`REGENERAR.ps1:291`):

| categoría | qué es | LOC aprox. | conf. |
|---|---|---:|---|
| **DETRÁS DE BANDERA APAGADA** (dentro de archivos que sí corren) | `alineacion_individual_por_area` y su plomería (`RECORD_POR_TEMA`), `nowcast_puertas.py:222-263,371-495,910-915` | ~170 | V |
| | ramas `union/ponderada/peor_tema/ponderada_logit` de `proyectar_postura` (`TEMA_AUTO`), `bloque.py:570-682,702-743` + helpers | ~190 | V (lote D) |
| | `_via_sobre_tablas` + `sobre_tablas.py` (`SOBRE_TABLAS`) | ~160 | V |
| | rama `QUORUM_ABSTENCIONES` de `simular_votacion`, `Manera 2` de `puerta_d`, stubs "dados de baja" de `ensemble.py` (`nowcast_proyecto`, `nowcast_auto`, `componer`, `imprimir_tarjeta`) | ~120 | V |
| **CORRE PERO NO MUEVE NADA** | `puerta_a.py`: `cargar_caracter`, `caracter_de`, `delta_caracter`, `condicionar` (≈300 de sus 444 líneas), con `COEF_POR_DEFECTO` en cero (`puerta_a.py:101`). Se ejecuta en cada corrida (`nowcast_puertas.py:828-830,853,867`): **lee y arma la tabla de dictámenes para un efecto cero** | ~300 | V |
| **NADIE LO IMPORTA NI LO CORRE** (ni `REGENERAR` ni workflows) | `composicion_capitulos.py` (145), `tema_por_acta.py` (260), `tema_por_capitulo.py` (240), `icg_contexto.py` (224), `scrape_jefes_bloque.py` (148), `escenarios.py` (139), `asistencia.py` (87), `cohorte_dos_rutas.py` (69), `bajar_autoridades_comisiones.py` (55), `generar_mapa_modelo.py` (482) | ~1.850 | V |
| **SÓLO MEDICIÓN/ESTIMACIÓN con offset contaminado** | `estimar_beta_dictamen` 562*, `estimar_epsilon_tau` 304, `estimar_psi_arrastre` 247 (ψ **no está implementado**), `estimar_theta_sobre_tablas` 247 (θ descartado), `diagnostico_senado` 224, `fase1_rec_por_tema` 191, `medir_rec_por_tema` 239, `medir_guard_era` 199, `validar_beta_dictamen_walkforward` 159, `validar_sobre_tablas_walkforward` 282 | ~2.650 | V |
| **LÍNEA TEMA/CAPÍTULO/ORIGEN** (medición cerrada) | `prueba1/2/3`, `validar_*capitulos/titulos`, `firma_tematica_*`, `medir_estabilidad_record_por_tema`, `record_por_origen*` + sus tests | ~4.850 con tests (lote E) | V |
| **NEUTRALIZADO** | `backtest_cadena.py` (550): `main` levanta `SystemExit` desde el 22-08 (ADR-0012) | 550 | V |
| **ACOPLAMIENTO** | *producción importa un estimador*: `beta_dictamen.py:102` → `estimar_beta_dictamen.py` (562 líneas, importa el harness en `:271`) | — | V |

\* `estimar_beta_dictamen.py` no puede archivarse sin antes mover `firmas_por_acta` y `jefes` a `beta_dictamen.py`.

**Total de código sin efecto sobre el número, con los defaults:** ≈ 640 líneas dormidas dentro de archivos vivos + 300 que corren sin mover nada + ≈ 1.850 sin ningún llamador + ≈ 2.650 de estimadores contaminados + ≈ 4.850 de la línea tema/capítulo/origen (incluye tests) ⇒ **del orden de 10.000 líneas**, sobre 16.482 de código del alcance. [I: suma de estimaciones que se solapan poco]

## 3. Matriz de banderas

Trece banderas de entorno cambian el cómputo (`01-motor-real.md` §3) y la CLI del agregador suma cuatro más. Con 9 de ellas booleanas hay 512 combinaciones. **El censo mide una sola: la de los defaults** (β no se aplica, ε₀/τη no están en $P_i$). Lo que se ejercita por test es cada bandera aislada, nunca sus interacciones. [V]

| combinación | qué pasa | ¿protegida? |
|---|---|---|
| `INCERTIDUMBRE_LEGISLADOR=0` | vuelve el **clip agregado 0,01** (viola la doctrina ADR-0016) y se ignoran `EPSILON0`/`TAU` | test on/off, sí; nada avisa que se reactiva un ajuste agregado |
| `SHRINK_RECORD=0` (con `MIN_HIST_INDIVIDUAL=1`, que es una constante) | un legislador con **un solo voto** usa `P_i = 0` ó `1` sin encoger (`perfil_legislador`, `:569-575`) | **no**: ninguna guarda ni test |
| `RECORD_POR_TEMA=1` sin `proyecto_id` ni `tema` | no hace nada (`:809`) | sí, por construcción |
| `TEMA_AUTO=1` con `COMBINAR_TEMAS≠primaria` | el harness levanta `NotImplementedError` (`baseline_voto_individual.py:455-458`): la **medición se niega a medir lo que producción haría** | sí, deliberado |
| `RECORD_POR_TEMA` × `TEMA_AUTO` | dos mecanismos independientes que resuelven la misma multietiqueta (`:797-811`) | no |
| `BETA_DICTAMEN=1` × `INCERTIDUMBRE_LEGISLADOR` | β corre **antes** de ε₀/τη (`armar_roster` → `simular_con_guardas`); τ se estimó sin β | no; el propio `nowcast_puertas.py:187-191` lo reconoce |
| `GUARD_ERA=0` | era fija 2023-12-10: un nowcast anterior a esa fecha queda **sin ningún récord** (`:99-115`, medido el 06-09) | sí, hoy ON |
| `EPSILON0`/`TAU` (env) | mismo nombre, **dos defaults** (`nowcast_puertas` 0,035/1,19; CLI `agregador` 0/0) | no |

## 4. Documentos vivos: diez hechos, qué dice cada uno

Referencia: **lo que hace el código**. ✓ = coincide · ✗ = contradice al código · ○ = no lo menciona. [V con `grep`, y `git log -1` para las fechas]

| # | hecho (el código) | `FORMULA` | `ESTADO-REAL` / `URGENTE` | `ESTADO-DEL-PROY.` | `EN-HUMANO` | `tablero_datos.js` | READMEs / otros |
|---|---|---|---|---|---|---|---|
| 1 | el panel publicado da **0,6132** | ✓ (1 mención) | ○ | ✓ (2) | ○ | **✗ 0,9801 (6×), 0,6132 (0×)** | **✗ `Nowcast-Puertas.html`: `p_aprobacion` 0,9801** (regenerado 14-09); **✗ `modelo/ensemble/README.md`: 0,9801 (4×)** |
| 2 | skill del voto individual **0,1333** | ✓ | ✓ | ✓ | ○ | ✓ (`:252`), **✗ `:273` repite "0,161 a 0,092"** | — |
| 3 | banda [p5,p95] cubre **63,6%** | ✓ | ✓ | ✓ | **✗ conserva "99,88%"** | **✗ `:253` dice 63,6% y `:318` dice 99,88% "del lado seguro"** (contradice al mismo archivo) | ADR-0025 (ver lote C) |
| 4 | `RECORD_POR_TEMA` **OFF** | ✓ | ✓ | ✗ `:92` "observabilidad… prendida" | ○ | **✗ `:332-333` "se activó"** | ✗ `nowcast_puertas.py:198-208` (comentario "PRENDIDA POR DEFECTO"); ADR-0026 (encabezado "PRENDIDO") |
| 5 | `BETA_DICTAMEN` **ON** | ✓ | ✓ | ✓ | ○ | ○ | **✗ `nowcast_puertas.py:832-834,656` "APAGADA POR DEFECTO"**; ✗ ADR-0030 `:283` "apagado" |
| 6 | `GUARD_ERA` **ON** | ✓ | ✓ | ✓ | ○ | ○ | ✗ `nowcast_puertas.py:99` "bandera APAGADA por defecto" (bloque que termina "PRENDIDO") |
| 7 | el hook `pre-commit` **no está instalado** | ○ | ○ | ○ | ○ | ○ | **✗ `CLAUDE.md:29` "reindexa solo"** (último cambio del archivo: 14-09) |
| 8 | 73 archivos `test_*.py` (8 pytest + 62 scripts + 3 en `datos/proyectos/tests`) | ○ | ○ | ○ | ○ | ○ | ✗ `tests.yml` "~56 archivos"; ADR/commits citan "392 chequeos" |
| 9 | 35 archivos de ADR (34 números; dos `0009`) | ○ | ✓ (34) | ✓ (34) | ○ | ✓ (34) | ✗ `CLAUDE.md` llega hasta ADR-0015; `mapa_modelo_datos.js` hasta ADR-0013 |
| 10 | `TAU=1,19`, `EPSILON0=0,035` en `nowcast()`; **0 / 0** en la CLI del agregador | ✓ tabla de parámetros | ✓ | ✓ | ○ | ○ | ✗ ninguno avisa del default 0 de la CLI |

**El documento que el código contradice, y el más grave:** el **HTML del panel** (`Nowcast-Puertas.html`), el artefacto que ve el usuario: dice **98,01%**; el motor de hoy, corrido sobre la misma entrada en una copia limpia, da **61,3%**; con `INCERTIDUMBRE_LEGISLADOR=0` vuelve a 98,01%. Nadie lo regeneró tras prender ε₀+τη (15-09 22:10). [V: corrí `casos/nowcast_puertas_html.py diputados --fecha 2026-06-01 --origen EJECUTIVO` en `Archivos_Borrar/repro/`]

Fechas del último cambio de cada vivo (`git log -1`): `ESTADO`, `EN-HUMANO`, `TABLERO.md`, `ESTADO-REAL`, `tablero_datos.js`, `MAPA.md` → 28-09 18:51; **`CLAUDE.md` → 14-09**; `README.md` → 14-09; `modelo/ensemble/README.md` → **15-09 20:39** (el commit que *implementó* ε₀+τη, no el que lo prendió); `mapa_modelo_datos.js` → 14-09; `Nowcast-Puertas.html` → 14-09. Los documentos que se actualizan en cada tanda (5 de 12) se actualizan **entre sí**; los que no, quedan con la realidad de la semana anterior.

## 5. Reglas acumuladas y si se cumplieron (con `git log`, no con la doc)

**Cuántas reglas se impuso el repo:** `CLAUDE.md` tiene 15 secciones-regla (anti-colisión, MAPA, trazabilidad, COMISIONES, precaución Senado, MOTOR, URGENCIAS, TABLERO, descartables, "dónde corro" con 4 sub-reglas, límites del sandbox con 5 puntos, corolario, flujo mínimo de 6 pasos, número de OD, insumo faltante); `PROTOCOLO-GIT.md` tiene 23 ítems; FORMULA §IV tiene 11 subsecciones (IV.1-IV.9), más 5 "defaults silenciosos" y 5 "trampas conocidas"; más ADR-0015, la regla del expediente, `URGENTE`, tablero, mapa y hook. **≈ 55 reglas y controles nombrados.** [V]

**Cumplimiento medido** sobre los **20 commits no-bot que tocan el código del motor desde el 25-08** (`git log --name-only`):

| regla | cumplimiento | nota |
|---|---:|---|
| ADR-0015: FORMULA en el mismo commit | **16/20** | los tres commits que **prendieron** algo (`ec5fd05` β, `64ff248` ε₀+τη, `0a7a03f` récord por tema) **lo cumplieron**: tocaron FORMULA, ESTADO, ADR, `tablero_datos.js` y tests |
| trazabilidad: ESTADO en el mismo commit | 14/20 | |
| TABLERO DE CONTROL: `tablero_datos.js` | 12/20 | `8b310c1` (la corrección más grande) no lo tocó |
| ADR en el mismo commit | 13/20 | |
| tests tocados | 18/20 | pero **ninguno fija el valor** de `RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0`, `TAU` |
| "un módulo, un dueño, una rama" | **no se practica** | 12 merges en 243 commits; 5 ramas en toda la historia; el trabajo aterriza en `main` |
| hook `pre-commit` que reindexa | **no está instalado** | `.git/hooks` sólo tiene `.sample` |
| mensajes de commit | **19 de 160 con < 16 caracteres** | `aaa` (×2), `asd`, `a`, `afas`, `Megacanje`, `AAAA`… |
| `URGENTE` "vacío la mayor parte del tiempo" | hoy tiene 3 ítems (parado a propósito) | |
| `MAPA.md` dentro del presupuesto | **no** (`verificar_regeneracion.py`) | |

**¿Cuáles habrían detectado la fuga?** Ninguna de las de proceso. La regla correcta **existía y era la equivocada**: FORMULA §IV.4 "Walk-forward siempre" entró el 06-09 (commit `2dbad10`, "aaa") **en el mismo commit que el código con `shift(1)` por fila**, y su texto prescribe justamente ese idioma: *"Todo estimador usa sólo información anterior: `shift(1)` + `expanding`"*. No hubo test de la propiedad hasta el 28-09 (`test_historia_sin_fuga.py`). Lo que sí habría atrapado el problema, y no existía, es una **prueba de invariancia** (corromper el futuro y ver que $P_i$ no se mueve: `invariancia_al_futuro.py`) o un **control independiente** (`control_independiente.py`).

## 6. Peso del proceso frente al del código

| | líneas | KB |
|---|---:|---:|
| ADR (35 archivos) | 4.688 | 275 |
| `PROMPT-*.md` (15) | 3.746 | 208 |
| `ESTADO` + `EN-HUMANO` + `TABLERO.md` + `FORMULA` + `ESTADO-REAL` + `URGENTE` | 7.922 | 1.078 |
| resto de `coordinacion/*.md` | 3.220 | 182 |
| `tablero_datos.js`, `mapa_modelo_datos.js`, `MAPA.md`, `CLAUDE.md`, `README.md` | 6.043 | 442 |
| **documentación y proceso, total** | **25.619** | **2.185** |
| código **en el camino** del panel (en alcance) | 6.906 | 343 |
| todo el código no-test del alcance | 19.595 | 945 |

**Documentación/código = 3,7× en líneas y 6,4× en bytes** contra el código que produce el número; 1,3× y 2,3× contra todo el código no-test. En 95 días (25-06 → 28-09): 35 archivos de ADR (283 KB), 15 `PROMPT-*.md` (214 KB) y **siete ADR entre el 15 y el 16-09** (0023-0029, verificado con las fechas de los encabezados). [V]

## 7. Veredicto sobre las hipótesis de esta fase

- **H3 (complejidad sin retorno en tema/capítulo/origen): SE CONFIRMA**, con el criterio pre-registrado: ninguno de los ADR 0023, 0024, 0026-0033 deja un término activo en el camino del número con ΔBrier limpio a favor. Hay ~92% de contenido sin mejora en pie (lote D) y ~4.850 líneas de código y tests (lote E). Lo único vivo que toca esa línea es el récord **por origen**, que sí pesa (ver `02`), pero no nació en ella: ADR-0033 sólo lo *midió* (y el motor ya condicionaba por origen).
- **H4 (la documentación dejó de ser un control): SE CONFIRMA**: el criterio pedía ≥3 hechos con contradicción entre documentos y ≥1 contra el código; hay **7 de 10 hechos** con al menos una contradicción y **6 contra el código** (filas 1, 3, 4, 5, 6, 7).
- **H5 (las reglas se agregan después del daño): SE CONFIRMA, con una precisión que la refina.** ADR-0015 se cumplió en la forma en los tres commits que prendieron términos y aun así pasó el daño: **es una regla del tipo equivocado**, exige *presentar* el cambio y no *verificar la medición*. Y la regla de método (§IV.4) prescribía el idioma con fuga.
