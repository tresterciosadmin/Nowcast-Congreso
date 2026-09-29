# 05 — Consolidación, reglas simples y anclaje a la realidad (PROPUESTA — nada de esto se ejecutó)

Los borradores están en `adr-consolidados/` (C1-C6) y `REGLAS-borrador.md`. Este archivo trae la tabla 34 → 6 (§5.1), las reglas (§5.2 resumen) y el **mecanismo de anclaje** (§5.3). Costos en horas de trabajo (h) y minutos de cómputo; todo lo que dice "medido" se corrió en esta auditoría.

## 5.1 La tabla 34 → 6 (35 archivos, cada uno en **exactamente un** destino principal; las referencias no cuentan)

| destino | ADR que absorbe | n |
|---|---|---:|
| **C1 Repo, datos y contratos compartidos** | 0001, 0002, 0009, 0009-BORRADOR, 0010, 0011, 0014, 0019, 0020, 0021 | 10 |
| **C2 Voto individual** | 0003, 0004, 0005, 0017, 0018, 0022 | 6 |
| **C3 Formulación y salida del número** | 0007, 0012, 0013, 0016 | 4 |
| **C4 Incertidumbre y coyuntura** | 0008, 0025 | 2 |
| **C5 Medición y evidencia** | 0015, 0032, 0034 | 3 |
| **C6 Línea de tema/capítulo/origen (cerrada)** | 0006, 0023, 0024, 0026, 0027, 0028, 0029, 0030, 0031, 0033 | 10 |
| | **total** | **35** |

Detalle por ADR (veredicto de `03-adr.md`; **regla que sobrevive** / **que se pierde**):

| ADR | veredicto | destino | regla que sobrevive / que se pierde |
|---|---|:-:|---|
| 0001 | VIGENTE-ESTRUCTURAL | C1 | módulo/dueño/contrato, ADR para cambiar un contrato / datos fuera de git, una rama por módulo |
| 0002 | VIGENTE-ESTRUCTURAL | C1 | semilla estática → canónica propia → bot que detecta / "el bot agrega" |
| 0009 | VIGENTE-ESTRUCTURAL | C1 | merge por campo, giro acumulado ≠ giro al ingresar, cuarentena con freno por invariante / "cuelga todo el nowcast" |
| 0009-BORRADOR | SUPERSEDIDO (por 0009) | C1 · **DESCARTABLE** | nada; el texto vive en `git show fd2aa2b` |
| 0010 | VIGENTE-ESTRUCTURAL | C1 | `rutas.py`, MAPA generado / la garantía de completitud, el hook, las cifras (246 líneas, 2 módulos) |
| 0011 | VIGENTE-ESTRUCTURAL | C1 | preguntarle a git con ruta relativa y `-v` / la prohibición del exit code |
| 0014 | VIGENTE-ESTRUCTURAL | C1 | lo compartido vive una vez, se re-exporta y se controla por identidad / — |
| 0019 | VIGENTE-ESTRUCTURAL | C1 | una sola frontera de eras (`definiciones.GOBIERNOS`) / — |
| 0020 | VIGENTE-ESTRUCTURAL | C1 | las bases viajan; aviso a 50, falla a 95 / "no viaja" (`tests.yml:26`) |
| 0021 | VIGENTE-ESTRUCTURAL | C1 | `definiciones.caracter_de_dictamen`, raíz por `rutas.py` / — |
| 0003 | VIGENTE-EVIDENCIA-ROTA | C2 | el desvío se modela respecto del bloque / el plan de 4 piezas y sus gates |
| 0004 | VIGENTE-ESTRUCTURAL | C2 | desvío v2 por conducta / la "línea bottom-up" (no es la del motor) |
| 0005 | VIGENTE-ESTRUCTURAL | C2 | 10 linajes con ventanas por fecha / Proyecto Sur ya no es PROGRESISMO |
| 0017 | VIGENTE-ESTRUCTURAL | C2 | `desconocido` ≠ único; enlace = `acta_expediente_todas` / la reserva sin levantar |
| 0018 | VIGENTE-EVIDENCIA-ROTA (el guard; el encogimiento tiene evidencia limpia) | C2 | el récord se encoge hacia el share del linaje (k=5); la era se deduce de la fecha con `definiciones` / 0,1304 → 0,1611, "valles cerrados" |
| 0022 | VIGENTE-ESTRUCTURAL | C2 | en el Senado la disidencia es minoría; Daer → massismo / la cifra "205 actas" |
| 0007 | VIGENTE-ESTRUCTURAL | C3 | probabilidad + nombres + límites declarados / la plantilla de 7 secciones, "skill 0,36" |
| 0012 | VIGENTE-ESTRUCTURAL | C3 | P(aprob \| se vota) = P_B·P_D; A y C se observan / el gancho δ agregado, `backtest_cadena` (880 LOC con test) |
| 0013 | VIGENTE-ESTRUCTURAL | C3 | ⌊E/2⌋+1 y su test / nada (el presidente queda como pendiente) |
| 0016 | VIGENTE-ESTRUCTURAL (las enmiendas de β: EVIDENCIA-ROTA) | C3 (+C2, C4) | la regla y sus dos excepciones; "si un término va a la derecha de la simulación, está mal ubicado" / "0,9801 en los tres" como evidencia |
| 0008 | INACTIVO | C4 | el clima, si entra, entra por $P_i$ con γ por tramo de desvío y signo por origen, y se prueba como predictor antes de prender / mecanismo 2, neutro 1,90, tablas viejas (≈ 1.490 LOC) |
| 0025 | VIGENTE-EVIDENCIA-ROTA (la dirección se rehabilita en parte: log-loss −0,036, in-sample) | C4 | la incertidumbre se modela en $P_i$ y como shock común dentro de la simulación, nunca como clip del agregado / el "99,88% conservadora" |
| 0015 | VIGENTE-ESTRUCTURAL | C5 | los tres niveles y "apagar deja el término marcado"; **se agrega un Nivel 0**: la medición que justifica corre el motor real, fecha estricta, otra ley, IC por ley, y el control tiene poder / — |
| 0032 | REGISTRO-HISTÓRICO | C5 (+C6) | la unidad efectiva es el expediente; un rasgo intra-era debe sobrevivir a la partición por ley entera / el "1,7×", `gobernadores.csv` |
| 0034 | **VIGENTE-SÓLIDO** (con reservas: τ/β/ficha no re-medidos, IC con 300 réplicas) | C5 | fecha estricta y otra ley; el harness importa el motor; IC por ley / el "~1,7×" |
| 0006 | INACTIVO | C6 (+C3) | no se publica una P por título sin un target con qué backtestearla / la unidad jerárquica como decisión vigente |
| 0023 | INACTIVO | C6 (+C1) | agregar sin reemplazar; el 9,8% de leyes aprobadas pierde algún tramo / la cifra 6/47 |
| 0024 | INACTIVO | C6 (+C5) | lo manual gana; sin dato, no-op / el "dónde SÍ está la ganancia" (0026) |
| 0026 | SUPERSEDIDO (por 0034) | C6 (+C2) | un grado de libertad, encoger al récord general, en logit / el "+11,06%" |
| 0027 | INACTIVO | C6 (+C3) | P(proyecto) no es un evento: se simula con shock común / — |
| 0028 | REGISTRO-HISTÓRICO | C6 (método → C5) | un control que da idéntico al tratamiento es una alarma / la conclusión "ninguna regla mejora" |
| 0029 | INACTIVO | C6 | clave de capítulo = `(proyecto_id, titulo_num, capitulo_num)` / la cobertura ampliada, los conteos 437→242→471 |
| 0030 | REGISTRO-HISTÓRICO | C6 (+C5) | medir la fracción con dato condicionado real antes del skill; criterios escritos antes / el diagnóstico del Senado |
| 0031 | REGISTRO-HISTÓRICO | C6 (+C5) | todo fallback avisa con un contador agregado / "el guard queda confirmado también para el tema" |
| 0033 | REGISTRO-HISTÓRICO | C6 (+C2, C5) | lo individual no persiste entre gobiernos, persiste el linaje; no se prende lo que predice peor / los niveles de skill, B1/B2 |

**El ADR C6 sí merece existir** (no una nota dentro de otro): guarda qué se probó, qué dio y con qué medición mínima se reabre. Sin él, las reglas que sobreviven de esos diez ADR (agregar sin reemplazar; un solo grado de libertad; un control idéntico al tratamiento es una alarma) se pierden con ellos.

## 5.2 Las reglas

Ver `REGLAS-borrador.md`: **10 reglas + 4 trampas del dato**, contra ≈ 55 reglas y controles hoy. Todas se comprueban con un test, un comando o un archivo generado. Se reemplazan ADR-0015, FORMULA §IV.4/IV.6/IV.7, la regla de trazabilidad y la del tablero; se eliminan "un módulo, un dueño, una rama" (12 fusiones en 243 commits) y los límites del sandbox.

## 5.3 El anclaje a la realidad

**Principio (redacción operativa, sin los agujeros del original).** *Parámetro* = toda variable de entorno, constante numérica o archivo derivado que lee el camino de `nowcast()`. *Afecta* = cambiarlo por su alternativa mueve algún $P_i$ o $P_{\text{aprob}}$ del panel de regresión en más de 1e-9. Cada parámetro que afecta es de un tipo: **(E)** estructural (reglamento o mecánica: test de conformidad) · **(M)** medido (comando reproducible, hash del motor y de los insumos, ΔBrier pareado por ley en la capa que toca, estimado sólo con datos anteriores a lo evaluado) · **(P)** provisional (marcado y con vencimiento). *Vigente* = el hash de los archivos que toca no cambió y las leyes nuevas son menos del 10%. El CI falla ante un parámetro que afecta y no está registrado, o ante un **(M)** vencido.

**Un límite honesto, medido.** Un gate por skill absoluto no puede afirmar nada en la era vigente: con 312 leyes el IC es [−0,26; 0,25]. Y **un gate estadístico no atrapa las fugas**: el efecto de la fuga del harness (ΔBrier −0,031) es heterogéneo entre leyes y con **500 leyes** el efecto mínimo detectable (MDE) es 0,052, mayor que el propio efecto. **A las fugas las atrapa una prueba determinística** (invariancia al futuro); a las regresiones de skill y calibración, un gate pareado. Son dos instrumentos distintos y hacen falta los dos.

### Tabla de los MDE (medida sobre el censo del 28-09; ΔBrier pareado por ley, α = 5%, potencia 80%)

| leyes muestreadas (estratificado era × cámara) | votos aprox. | SE del Δ de un efecto chico (récord por tema, +0,0030 real) | **MDE** | MDE relativo al Brier del motor (0,139) | cómputo estimado |
|---|---:|---:|---:|---:|---|
| 250 | ~41.000 | 0,0028 | 0,0078 | 5,6% | ~3 min |
| **500** | ~104.000 | 0,0022 | **0,0060** | **4,3%** | ~5-7 min |
| 1.000 | ~166.000 | 0,0014 | 0,0039 | 2,8% | ~10 min |
| 2.000 | ~366.000 | 0,0008 | 0,0022 | 1,6% | ~20 min |
| **3.731 (censo completo)** | 691.845 | **0,00083** | **0,0023** | **1,7%** | 35-60 min |

Consecuencias: **la muestra de 500 leyes sirve para regresiones ≥ 4,3%** (por ejemplo, un cambio que degrade el récord a la mitad); **no habría visto** el `RECORD_POR_TEMA` (+2,1%) que sí ve el censo completo. Agrupar el bootstrap por **fecha de sesión** o por **mes** en vez de por ley cambia el SE de −17% a +29%: se reporta el mayor de los tres.

### Piezas

| # | pieza | qué habría atrapado en septiembre | costo | recomendación | alternativa más barata |
|---|---|---|---|---|---|
| **1** | **Una métrica de verdad.** Skill del voto individual con el motor real, IC por ley (≥ 2.000 réplicas, hoy 300), por era, con fecha y sha del motor y de los insumos, escrito a `registro/metrica_de_verdad.json` | el 0,1611 (fuga) y el "prender si el censo mejora" sin censo independiente | **6 h** (envoltorio que no escribe en rutas versionadas: hoy `resumen_censo_limpio.py` pisa el número publicado); **14 min** con una sola variante (`censo_detalle_paralelo.py` con 6 variantes: 35-60 min) | correrla al mergear a `main`, y el censo completo (6 variantes) sólo cuando cambia una bandera | persistir **estadísticos suficientes por ley** (n, Σy, ΣSE por variante: ~200 KB, sí viaja por git) y recalcular IC sin el detalle de 37 MB |
| **2** | **Calibración de lo declarado.** Cobertura de la banda, y P(aprobación) contra resultados (Brier, log-loss, tabla de confiabilidad, "seguras y equivocadas"), incluidas las mayorías especiales | el 99,88% (hoy 63,6%: brecha de 26,4 pp) y el salto 0,9801 → 0,6132 aceptado "porque se movió" | **6 h** (ya existen `medir_tau_limpio.py` y `contraste_aprobacion.py`; hoy 10 min cada uno) | `calibracion_declarada.json` generado, con test: cobertura observada − declarada > 5 pp = rojo | 1.000 actas al azar (~2 min) |
| **3** | **Versión rápida** para cada cambio del motor: 500 leyes estratificadas (~5-7 min) más la **prueba de invariancia** con 30 actas (6 por era) | una fuga como la de `shift(1)` (la atrapa la invariancia, no la muestra) y cualquier degradación ≥ 4,3% | **8 h** (la invariancia actual reconstruye el contexto por acta: ~12 s/acta, hay que acelerarla) | correr en cada PR que toque el motor | sólo la invariancia (30 actas, ~6 min) |
| **4** | **Gate automático** (`.github/workflows/`, en la **raíz git**, no en el proyecto) | cambios sin medición (`RECORD_POR_TEMA`, ε₀+τη, `MIN_HIST`), una mejora "milagrosa", un default que cambia solo | **10 h** | tres ramas, abajo | un test que sólo compare `git diff` de defaults contra el registro (3 h) |
| **5** | **Registro de banderas y parámetros generado desde el código:** nombre, default efectivo, `archivo:línea`, tipo (E/M/P), medición que lo respalda, fecha, IC, `afecta_panel` (por perturbación), `aprobado_por` | la tabla "Constantes del motor" y "Parámetros estimados" de FORMULA, escrita a mano y desactualizada; el mismo nombre con dos defaults | **12 h** (AST + corrida de perturbación del panel: ~30 parámetros × 20 s = 10 min) | reemplaza esas dos tablas | AST sin perturbación (4 h) |
| **6** | **Monitoreo hacia adelante** (la única evidencia sin fuga posible) | el error de calibración de la banda se habría visto a los ~3 meses | **12 h** el nivel 1; **+16 h** el nivel 2 | ver abajo | congelar el commit hoy y re-correr el contraste a los 3 meses de actas nuevas (2 h) |
| **7** | **Qué se corta** | cinco documentos vivos que se contradicen | **10 h** | ver abajo | archivar sin generar (2 h) |

**Pieza 4, el gate (tres ramas, con tolerancias).** (i) *Refactor declarado* ("la fórmula no cambia"): $P_i$ idénticas con |Δ| < 1e-9 sobre las 500 leyes; sin estadística. (ii) *Cambio que mueve el número:* rojo si el **límite superior** del ΔBrier relativo pareado supera **+1%** (censo completo) o **+4%** (500 leyes); *comparaciones múltiples:* una sola comparación pre-declarada por bandera y Holm sobre las banderas de la ronda. (iii) *Mejora sin explicación:* rojo si el ΔBrier **mejora más de 2%** sin una entrada de medición registrada (la fuga mejoró el número un 22%). Además: rojo si un default del código ≠ registro. **La base de comparación se calcula en el mismo job** (motor de la rama base y de la rama nueva sobre los mismos votos): no se compara contra un JSON viejo. Prender exige, además de pasar, una **confirmación fuera de muestra** (las leyes más recientes o el monitoreo hacia adelante) y el OK de Franco; apagar no exige evidencia. Un job de CI tiene `timeout-minutes: 30` (`tests.yml`): la rama de 500 leyes entra; el censo completo va en un workflow `workflow_dispatch` o semanal.

**Pieza 6, monitoreo hacia adelante (factibilidad medida).** El bot (`bot-diario.yml`, lunes a sábado 07:00 ART) trae por cada acta nueva **el resultado y los conteos** (`votaciones_nuevas.parquet`: 578 actas, `n_afirmativos`, `n_negativos`, `n_ausentes`; última fecha 2026-09-24), **no los votos nominales**: esos entran con una reconstrucción canónica manual de ~20 min que el bot avisa con un issue. Entonces: **nivel 1 (automático, sin tocar el bot):** un workflow nuevo `monitoreo-adelante.yml`, disparado por `workflow_run` de `bot-diario`, que para cada acta nueva simula con la historia canónica *anterior* (por construcción no contiene el acta), congela la predicción con el sha del motor y compara conteos y resultado; con 5-20 actas por semana, ~300 actas en 6 meses fijan la cobertura con un error de ~3 pp. Es incondicional en origen (el origen de las actas nuevas requiere la reconstrucción). **Nivel 2:** tras cada reconstrucción, el skill de $P_i$ con origen sobre votos nominales nuevos.

**Pieza 7, qué se corta** (cada dato con **un solo lugar**): `ESTADO-DEL-PROYECTO.md` (650 KB, 3.422 líneas): se **congela** como archivo y se reemplaza por un estado **generado** de una página · `ESTADO-REAL-DEL-MOTOR.md`: pasa a generarse del registro · `EN-HUMANO.md` (254 KB): se genera del registro o se congela · `tablero_datos.js` (212 KB): los KPI se generan y los "hitos" manuales se eliminan · `TABLERO.md`: se conservan las tareas · `MAPA.md`: se mantiene generado, arreglando el bug de CRLF que hace decir "0 no viajan" · `FORMULA-COMPLETA.md` (126 KB): queda la ecuación vigente (§I.00) y las tablas generadas; las secciones históricas van a un archivo · los 15 `PROMPT-*.md` se **archivan** en `coordinacion/archivo/` (se mueven, no se borran) · el **panel HTML se regenera en el CI** y un test verifica que coincide con el motor.

### Secuencia de implementación (con criterio de salida verificable)

| paso | qué | h | criterio de salida |
|---|---|---:|---|
| **0** | poner el CI en verde: que el insumo del censo viaje (estadísticos por ley) o declararlo excepción con motivo | 3 | `python -m pytest tests/ datos/proyectos/tests -q` → 0 fallas |
| **1** | registro de parámetros (AST) + `test_defaults_fijados` | 6 | cambiar `TAU` a 1,2 en el código hace fallar el test |
| **2** | invariancia al futuro y control independiente dentro de `evaluacion/baseline/tests/` | 8 | pasan en `HEAD`; inyectar `shift(1)` sobre votos en el harness las pone en rojo |
| **3** | métrica de verdad + calibración declarada generadas | 12 | reproducen 0,1333 y 63,6%, con fecha y sha, sin tocar archivos versionados |
| **4** | generación de documentos y regeneración del panel en el CI | 10 | el HTML versionado = el motor de hoy |
| **5** | gate rápido (500 leyes + invariancia) en PR | 10 | rojo ante una degradación inyectada de 6% (aplanar $P_i$); verde en un refactor puro |
| **6** | monitoreo hacia adelante, nivel 1 | 12 | tras una semana de bot hay ≥ 10 predicciones congeladas con sha, comparadas |
| **7** | recortes de código de `06` (poda), de a un ADR | 20 | cada test dedicado falla si se rompe lo podado |
| | **Total** | **≈ 80 h** | |

El orden importa: **0 → 1 → 2** cierran las brechas por las que se coló septiembre y cuestan ~2 días; 3-5 arman el anclaje continuo; 6 es la única evidencia sin fuga posible pero tarda meses en acumular.
