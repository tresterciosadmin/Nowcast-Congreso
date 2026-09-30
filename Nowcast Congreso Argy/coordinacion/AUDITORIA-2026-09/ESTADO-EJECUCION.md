# Estado de ejecución de la auditoría (documento vivo)

> **Es el carril de la auditoría.** Todo lo que se hace en esta etapa es un ítem de esta tabla (fase + número). Lo que no está acá **no se hace**: se anota en `PENDIENTES-POST-AUDITORIA.md` (regla 1 del §9.9 del informe). Se actualiza **al terminar cada ítem y al cerrar cada sesión**: la conversación siguiente arranca de acá, no de la memoria del chat.
>
> Decisiones y su porqué: `AUDITORIA-INTEGRAL-2026-09.md` §9. Reglas del carril: §9.9. Definición numérica de "funcionando": §9.4.
> Estados: `PENDIENTE` · `EN CURSO` · `HECHO` (con la evidencia: comando y salida, o sha del commit) · `DESCARTADO` (con el motivo escrito y la firma de Franco).

**Última actualización:** 2026-09-29 — A1, A2 (CI verde confirmado por Franco) y A3 hechos; próximo ítem: A4.
**Dónde se trabaja:** `main`, commits chicos (uno por corrección), con la suite en verde **antes** de cada commit; sin `git push` (lo hace Franco). Los bots empujan a `main`: no se les toca el permiso. Rama sólo si una corrección no puede dejar la suite en verde entre commits (vida corta: se mergea en la misma sesión).
**Punto de partida (para deshacer):** el tag local `auditoria-punto-de-partida` marca `main` antes de la primera corrección.

## Fase A — Orden y limpieza

| ítem | qué | quién | criterio de salida | estado |
|---|---|---|---|---|
| **A1** | Verificar el arranque: `git status`, rama `main`, y correr la suite; el resultado debe coincidir con `00-linea-base.md` (§7) | Claude | mismo resultado que la línea base (el único rojo esperado es `test_insumos_del_motor_viajan`) | **HECHO** 2026-09-29 sobre `d0e4897` (evidencia en la sección «Evidencia de A1», abajo) |
| **A2** | **CI en verde** (decisión 11, opción 1): guardar en git los estadísticos por ley (JSON, no `.parquet`/`.csv`: están ignorados) que alcanzan para recalcular skill, IC, τ y ε₀; re-apuntar los consumidores; que `test_insumos_del_motor_viajan` pase | Claude | test verde en local; **Franco confirma en la pestaña *Actions* de GitHub** (d5) | **HECHO** 2026-09-29: verificado en local (simulación del CI) y **confirmado por Franco en *Actions*** («corrió perfecto»). Evidencia en «Evidencia de A2» (commits `51212bc`, `e944a3c`, `55ca0b8`) |
| **A3** | **Paridad de versiones** (d6): correr la suite en Python 3.11 (el del CI) y fijar versiones; documentar la de esta PC (3.14 / pandas 3.0) | Claude | resultados iguales en ambas | **HECHO** 2026-09-29: 0 diferencias entre 3.11, 3.14 y la PC (ver «Evidencia de A3»). Tras el próximo push, la primera corrida de *Actions* ya instala los pines |
| **A4** | Escribir `coordinacion/QUE-SE-MIDE.md` desde el §9.4 (incluye d7: origen Senado sin publicar; y los límites: etiquetas de origen sin validar, presencia sin medir, cobertura de la canónica por año — d4-a) | Claude | archivo publicado; Franco lo lee | PENDIENTE |
| **A5** | **Apagar las mayorías especiales** (decisión 9): `nowcast()` con `tipo_mayoria ≠ SIMPLE` devuelve sin número y con el motivo | Claude | test que lo fija; el resto del número no cambia (`max|ΔP| = 0` en simple) | PENDIENTE |
| **A6** | **Eliminar HTML y panel** (decisiones 1 y 6; alcance según §9.1): los 3 HTML de producto, sus generadores y sus `.js` de datos; `REGENERAR.ps1` paso 8 → JSON de regresión; `verificar_regeneracion.py`; sacar `Senado_2002-03-05_muestra.html` y `premortem-report-…html`; **se quedan los 6 fixtures** de los tests de los bots; `comparar_vias_icg.py` pierde la salida HTML pero **se conserva** (ICG, ver D6). Antes de sacar cada archivo: copia a `Archivos_Borrar/` y `git rm`; se busca quién lo referencia | Claude | `git ls-files \| grep -i html` devuelve sólo los 6 fixtures; el JSON de regresión existe y un test lo compara con el motor; suite verde | PENDIENTE |
| **A7** | **Poda P0 y P1** (decisión 10; ≈ 7.000 líneas). **Antes:** confirmar que nada de lo que se mueve pertenece a δ, θ, ψ, β ni al ICG (decisión 2 y ronda 2, punto 9 —ICG—, ver §9.1b del informe); `comparar_vias_icg.py` **sale de P0** | Claude | los criterios de salida del §5 del informe (`max|ΔP| = 0`, suite igual menos lo movido) | PENDIENTE |
| **A8** | **Worktree y rama `suspicious-lalande`** (d9): rescatar `c916e0e` a una rama (`rescate-taxonomias`) y avisar a Franco para que borre el worktree y `Archivos_Borrar/repro/` | Claude + Franco | el commit queda a salvo; worktree y `repro/` eliminados por Franco | PENDIENTE |
| **A9** | **Bots** (d10): comprobar que los tres workflows siguen sanos después de A6 y A7 (rutas, insumos); **no** activar protección de rama con "requerir PR" | Claude | los workflows corren sin cambios de permisos; Franco confirma en *Actions* | PENDIENTE |
| **A10** | Actualizar `CLAUDE.md`: sacar la regla del TABLERO DE CONTROL y las referencias a los HTML y al mapa eliminados; **conservar** el bloque MODO AUDITORÍA | Claude | `tests/test_rutas_citadas_existen.py` y `tests/test_rutas.py` verdes | PENDIENTE |

**Salida de la fase A:** suite igual o mejor que la línea base; `nowcast_puertas.py` corre; mayorías especiales devuelven sin número; sólo los 6 fixtures HTML; CI en verde confirmado por Franco.

## Fase B — Anclaje básico (`05` §5.3, pasos 1-2)

| ítem | qué | criterio de salida | estado |
|---|---|---|---|
| **B1** | Registro de parámetros **generado desde el código** + `test_defaults_fijados` | cambiar un default rompe un test | PENDIENTE |
| **B2** | `invariancia_al_futuro.py` como test de la suite | una fuga sintética (usar datos de la fecha) lo hace fallar | PENDIENTE |
| **B3** | `control_independiente.py` como test de regresión | el control reproduce 0,1335 y detecta el desvío | PENDIENTE |

## Fase C — Métrica de verdad y calibración declarada

| ítem | qué | criterio de salida | estado |
|---|---|---|---|
| **C1** | Skill por ley con IC pareado, **generado por un solo comando** (paso 3 del anclaje) | reproduce 0,1333 [0,059; 0,200] | PENDIENTE |
| **C2** | Calibración declarada: cobertura de la banda y Brier contra la constante **por cámara, en mayoría simple** | reproduce la tabla del §9.2 | PENDIENTE |
| **C3** | Brazo "sin corte por era" con el motor completo (decisión 7) | veredicto medido; decide Franco | PENDIENTE |

*(La validación de las etiquetas de origen —decisión 8— **no está en esta tabla**: se hace más adelante y con una persona. Ver `PENDIENTES-POST-AUDITORIA.md`; queda declarada como límite en `QUE-SE-MIDE.md`.)*

## Fase D — Re-estimación limpia y walk-forward (decisión 2)

Método obligatorio: estimar con datos **anteriores** a *t* y evaluar **después**. Cada parámetro deja: valor, panel, corte, IC por ley pareado contra el valor anterior, fecha y sha del motor. **El punto de partida es corregir y re-estimar para que el término aporte al motor; no se archiva ni se borra ningún estimador.** Cada veredicto lo revisa un segundo agente (Opus) que no vio la conclusión. Orden (los parámetros no son independientes):

| ítem | qué | estado |
|---|---|---|
| **D1** | Parámetros de $P_i$: `k_shrink` del récord y de la postura, ventana de 730 días, `MIN_HIST`, `MIN_VOTOS_FICHA`, granularidad del origen, guard de era | PENDIENTE |
| **D2** | Piso 0,02, ε₀ y τ | PENDIENTE |
| **D3** | β y δ (sobre el offset de D1) | PENDIENTE |
| **D4** | θ y ψ (corregirlos y re-estimarlos) | PENDIENTE |
| **D5** | Recheck de ε₀ y τ con β prendido | PENDIENTE |
| **D6** | **ICG en la fórmula** (ronda 2, punto 9; §9.1b del informe): hoy está "medido y desconectado" (`FORMULA-COMPLETA` §II.4; el único lugar donde actuaba era el slider del panel, que se elimina en A6). Estimar γ y la forma de entrada con la serie disponible, walk-forward; si no hay poder para decidirlo, el término queda **declarado "pendiente de datos"** y el bot sigue acumulando | PENDIENTE |

**Salida de la fase D:** para cada parámetro y para el ICG, decisión escrita (se conserva / se recalibra / se simplifica) con su medición; y el resultado de la meta operativa de §9.4 para mayoría simple, en ambas cámaras.

## Fase E — Cierre

| ítem | qué | estado |
|---|---|---|
| **E1** | Promover los ADR C1-C6 con su "estado real" (post-D); banner "consolidado en …" en los originales, que se conservan intactos | PENDIENTE |
| **E2** | Adoptar las 10 reglas (`REGLAS-borrador.md`) en `CLAUDE.md` | PENDIENTE |
| **E3** | Gate pareado (pasos 4-5 del anclaje) | PENDIENTE |
| **E4** | Monitoreo hacia adelante, nivel 1 | PENDIENTE |
| **E5** | Actualizar `FORMULA-COMPLETA.md` (nivel 3 de ADR-0015) con el estado final de cada término | PENDIENTE |
| **E6** | Generar `PROMPT-POST-AUDITORIA.md` desde `PENDIENTES-POST-AUDITORIA.md`; **Franco declara cerrada la auditoría**; se retira el bloque MODO AUDITORÍA de `CLAUDE.md` | PENDIENTE |

## Evidencia de cierre por ítem

### A1 — arranque verificado (2026-09-29, sobre `d0e4897`, `main`, Python 3.14.3 / pandas 3.0.2, `PYTHONUTF8=1`)

| chequeo | comando | resultado | línea base (§3 y §7 de `00-linea-base.md`) |
|---|---|---|---|
| rama y árbol | `git branch --show-current`; `git status --porcelain` | `main`; salida vacía | árbol limpio |
| tag de partida | `git rev-parse auditoria-punto-de-partida` | `bcc62b3…` (el commit auditado) | — |
| motor sin cambios desde lo auditado | `git diff --name-only bcc62b3 HEAD` filtrado por `modelo/ variables/ evaluacion/ definiciones.py rutas.py tests/` | vacío (los 14 commits nuevos: 12 de documentación de la auditoría, 1 del bot, 1 del prompt) | motor idéntico a `6e6b629` |
| pytest | `python -m pytest tests/ datos/proyectos/tests -q` | **40 pasan, 1 falla** (`test_insumos_del_motor_viajan`: `censo_detalle_2026-09-28.parquet`, lo lee `estimar_epsilon_tau.py`), 16,5 s | 40 pasan, 1 falla (el mismo) |
| los 62 `test_*.py` como scripts (bucle de `tests.yml`) | `find . -name "test_*.py"` sin `tests/`, `datos/proyectos/tests` ni `Archivos_Borrar` | **62/62 con código 0**; `test_historia_sin_fuga` 14/14; `test_harness_es_el_motor` 15/15 («comparados 238 legisladores; distintos 0»); el más lento, `test_incertidumbre_legislador`, 69 s | 62/62 con código 0 (308 s, con el censo corriendo en paralelo) |
| `verificar_regeneracion.py` | `python verificar_regeneracion.py` | **15 OK · 1 a mirar** («MAPA.md dentro del presupuesto»: 472 líneas contra 460) | 15 OK · 1 a mirar (el mismo) |
| ninguna corrida escribió en lo versionado | `git status --porcelain` antes y después de los 62 scripts | vacío en ambos | idéntico |

**Diferencias con el informe (ninguna toca el motor ni los números):**
1. El tag `auditoria-punto-de-partida` apunta a `bcc62b3` (el commit auditado), no a `d0e4897`. Entre los dos sólo hay documentación de la auditoría y un commit del bot. Para deshacer correcciones del motor sirve igual; si se quiere «`main` antes de la primera corrección» habría que moverlo (no se movió: no está en el plan).
2. `coordinacion/PROMPT-AUDITORIA-INTEGRAL.md`, que la línea base registraba sin rastrear, ya está versionado (`d0e4897`, hecho por Franco).
3. La rama local `auditoria-2026-09` sigue existiendo, a 0 commits de `main` (ya mergeada).

### A2 — CI en verde (2026-09-29; commits `51212bc`, `e944a3c`, `55ca0b8`; confirmado por Franco en *Actions*)

**Qué se hizo.** `evaluacion/baseline/outputs/censo_estadisticos_2026-09-28.json` (1,25 MB, versionado): una fila por acta con su ley, cámara, fecha y era (5.856 actas, 3.731 leyes, 691.845 votos) con n, Σy y, por variante (`estricta__general` = el motor de hoy; `estricta__tema` = la columna `p`), Σ(p−y)², Σp y Σp²; más la curva de Brier y log-loss de ε₀ sobre la grilla 0–0,30 cada 0,005. Lo genera y lo lee `evaluacion/baseline/src/censo_estadisticos.py`; `censo_detalle_paralelo.py` lo regenera al terminar el censo (así la fase D no lo deja viejo); `estimar_epsilon_tau.py` lo lee por defecto (`--detalle X.parquet` fuerza el camino voto a voto); el bootstrap por ley pasó al módulo nuevo y `skill_ic_por_ley` / `dif_brier_ic_por_ley` del harness lo llaman (una sola copia). Test nuevo: `tests/test_censo_estadisticos.py` (13).

**Criterio de la comparación (fijado antes de mirar):** el camino por estadísticos tiene que dar lo mismo que el voto a voto original, campo por campo; diferencia numérica < 1e-9.

**Medido, sobre el censo real** (valor anterior = el código original en `HEAD` antes de A2, corrido sobre el parquet):

| comparación | resultado |
|---|---|
| `estimar_epsilon_tau` original vs nuevo por JSON vs nuevo por parquet, columnas `p` y `p__estricta__general` | 129 campos por caso, **0 distintos, max\|Δ\| = 0** (incluye `por_camara`) |
| skill + IC 95% por ley, 2 variantes × 8 cortes (global, 5 eras, 2 cámaras) | 16 cortes, **0 distintos** (IC idéntico elemento a elemento) |
| ΔBrier pareado tema−general, 8 cortes | **0 distintos** (global: +2,12% [0,84; 3,48]) |
| curvas de ε₀ sin redondear | max\|ΔBrier\| 5,6e-17; max\|ΔLog-loss\| 2,2e-16 |
| lo que da: motor de hoy | skill **0,1333 [0,0574; 0,1979]**; ε₀ = **0,055**; τ = **1,197** (con ε₀: 1,1521) |
| lo que da: columna `p` (la de `--columna` por defecto) | skill 0,115 [0,0371; 0,1781]; ε₀ = 0,05; τ = 1,2249 (con ε₀: 1,1734) |
| tests con sabotaje en memoria (Σp² +1%; otra semilla del bootstrap) | ambos **detectados** |

**CI: el criterio del plan se cumplió, pero un checkout limpio mostró que la línea base subestimaba el rojo.** La línea base decía que el CI fallaba por un solo test ([INFERIDO]). Al probar A2 en un `git archive` de `HEAD` (sin nada de lo ignorado) con Python 3.11 aparecieron **tres fallas más**, que en esta PC no se ven porque el disco tiene lo que git ignora o lo que pip no pidió:

| falla | causa | arreglo (commit) |
|---|---|---|
| `test_insumos_del_motor_viajan` | el estimador leía el parquet ignorado | A2, estadísticos versionados (`51212bc`) |
| `test_rutas_citadas_existen` | `variables/proyecto/data/tema_por_capitulo.parquet` (ignorado) citado en 5 archivos; es salida generada, la leen pilotos de `evaluacion/`, no el motor | declarada en `rutas.py` y `GENERADOS`, como indica el test (`e944a3c`) |
| `datos/canonica/tests/test_actas_gemelas.py` | `build.py` importa `jsonschema`; no estaba en `requirements.txt` (y `verificar_dependencias.py` decía «está todo» porque salía de la misma lista) | agregado a los dos (`e944a3c`) |
| **el primer paso del workflow** (`python -m pytest`) | `pytest` no está en `requirements.txt` ni lo trae ninguna dependencia: en un venv 3.11 limpio, `No module named pytest` | agregado a `requirements.txt` (`55ca0b8`) |

**Simulación del CI sobre `55ca0b8`:** `git archive HEAD` en carpeta limpia (0 parquets del censo) + venv Python 3.11.0 nuevo instalado **sólo** con `requirements.txt` + los dos pasos de `tests.yml` tal cual. Resultado: `python -m pytest tests/ datos/proyectos/tests -q` → **exit 0, 53 pasan, 1 se saltea** (el de frescura, que sólo corre donde existe el parquet); los **62 scripts → código 0**. En esta PC (3.14): `pytest` 54 pasan; 62/62 scripts en 0; árbol idéntico antes y después. *No pude leer el estado real de GitHub (d5): lo de arriba es una simulación. La confirmación real la dio Franco después del `git push`: «corrió Actions perfecto».*

**Límites y observaciones (ninguna es un ítem nuevo):**
1. **Lo que sigue pidiendo el parquet** (necesita el voto a voto: cobertura de la banda, tablas por fuente/carácter, re-armar P con otros parámetros): `medir_tau_limpio.py`, `chequear_direccion_beta.py`, `resumen_censo_limpio.py`, `medir_fuga_historia.py`, `record_por_origen_brazos.py`, `control_independiente.py`, `contraste_aprobacion.py`. En un clon fallan con `FileNotFoundError` (error claro, no columna vacía); se regeneran con `censo_detalle_paralelo.py` (43 min). `test_insumos_del_motor_viajan` es una heurística por texto del indexador (un archivo «lee» un dato si su nombre aparece a menos de 400 caracteres de un verbo de lectura): hoy esos scripts figuran como «menciona» y no como «lee».
2. **ε₀ sólo se recalcula sobre la grilla de 0,005 y con Brier/log-loss**: el log-loss depende de los 135.000 valores distintos de p. Otra grilla u otra pérdida piden regenerar el censo.
3. **Para D2:** el estimador usa por defecto la columna `p`, que es **idéntica** a `p__estricta__tema` (RECORD_POR_TEMA prendido cuando se generó el censo), y el motor hoy lo tiene apagado. Con el offset del motor de hoy (`estricta__general`) ε₀ da 0,055 y τ 1,197; con `p`, 0,05 y 1,2249. Producción: EPSILON0 = 0,035, TAU = 1,19 (no se tocó).
4. **Para C1:** el IC que reproduce el harness es **[0,0574; 0,1979]** (idéntico al ya publicado en `baseline_voto_individual.json`). El «[0,059; 0,200]» del informe (§9.4 y criterio de C1) es el del *control independiente*, que usa su propio bootstrap. Los dos son consistentes; el criterio de C1 debería citar el del harness.
5. **Defecto de Windows del indexador** (`viaja` siempre `True` en esta PC): anotado en `PENDIENTES-POST-AUDITORIA.md`; `mapa.json` y `MAPA.md` se reindexaron a mano porque el hook de pre-commit no está instalado en esta PC.

### A3 — pre-registro (2026-09-29, escrito ANTES de medir)

**Pregunta:** ¿el repo da lo mismo en el Python del CI (3.11) que en el de la PC de Franco (3.14) cuando los paquetes están fijados? **Qué se fija:** los 14 paquetes directos de `requirements.txt` con `==`, en las versiones que ya tiene la PC (pandas 3.0.2, numpy 2.4.4, pyarrow 24.0.0, statsmodels 0.15.0, scikit-learn 1.9.0, …), **salvo `scipy`: 1.17.1**, porque la 1.18.1 de la PC no existe para 3.11 (máximo 1.17.1). Se declara `scipy` porque el código lo importa directo (`simple_por_camara.py`) y no figuraba. Los transitivos quedan libres: hoy resuelven idénticos en 3.11 y 3.14 (44 paquetes, comprobado con `pip install --dry-run --report`). Bots: no se tocan (sus listas son otras; `bot-diario` en 3.12, `icg-mensual` y `padron-vivo` en 3.11).

**Tres entornos:** E1 = Python 3.11 + venv nuevo con el `requirements.txt` fijado, en un `git archive` limpio (el CI); E2 = Python 3.14 + venv nuevo con el mismo archivo; E3 = la PC tal cual (3.14.3, pandas 3.0.2, **scipy 1.18.1**, resto igual a los pines).

**Qué se compara y qué decide** (E1 = E2 = E3):
1. `pytest tests/ datos/proyectos/tests -q`: mismos conteos (pasan / se saltean / fallan).
2. Los 62 scripts: todos con código 0 y la misma línea de cierre en cada log («N/N OK»).
3. **Huella numérica**, con el motor real y la salida completa como JSON: `nowcast_puertas.py diputados` y `senado` con `--fecha 2026-06-01 --origen EJECUTIVO` (semilla y `--n-sims` por defecto); `estimar_epsilon_tau.py --columna estricta__general` y `--columna p`; y skill + IC por ley de los estadísticos en los 8 cortes. **Umbral: igualdad exacta campo por campo**, sin contar campos volátiles (fecha de generación, rutas). Una diferencia numérica distinta de 0 se informa con su campo y su max\|Δ\|; ≤ 1e-12 se declara «igual salvo redondeo de coma flotante»; mayor es un hallazgo y A3 no se cierra hasta explicarlo.
4. Si E3 difiere de E1 y E2 **sólo** donde interviene `scipy` 1.18.1 contra 1.17.1, se informa por separado (no se puede igualar: 1.18 no existe en 3.11).

### A3 — paridad de versiones: resultado (2026-09-29; pre-registro arriba, commit `037d160`)

**Qué se cambió:** `requirements.txt` con los 14 paquetes directos fijados con `==` (los que ya tenía la PC, salvo `scipy 1.17.1`; `scipy` se declara por primera vez) y encabezado que explica cómo se eligieron y cómo actualizarlos. El workflow no se tocó (el CI sigue en Python 3.11). Los bots no usan este archivo.

**Entornos** (E1 y E2: `git archive` limpio, sin nada de lo ignorado, venv nuevo instalado sólo con el `requirements.txt` fijado; E3: la PC sin tocar):

| | Python | pandas | numpy | scipy | pyarrow | statsmodels | scikit-learn |
|---|---|---|---|---|---|---|---|
| **E1** (el CI) | 3.11.0 | 3.0.2 | 2.4.4 | 1.17.1 | 24.0.0 | 0.15.0 | 1.9.0 |
| **E2** | 3.14.3 | 3.0.2 | 2.4.4 | 1.17.1 | 24.0.0 | 0.15.0 | 1.9.0 |
| **E3** (la PC de Franco) | 3.14.3 | 3.0.2 | 2.4.4 | **1.18.1** | 24.0.0 | 0.15.0 | 1.9.0 |

**Resultado contra el criterio pre-registrado:**

| criterio | E1 | E2 | E3 | veredicto |
|---|---|---|---|---|
| 1. `pytest tests/ datos/proyectos/tests -q` | 53 pasan, 1 se saltea | 53 pasan, 1 se saltea | 54 pasan | igual (el «1 se saltea» de E1/E2 es el test de frescura del JSON, que sólo corre donde existe el parquet: E3 lo tiene) |
| 2. los 62 scripts | 62/62 en 0 | 62/62 en 0 | 62/62 en 0 | igual; **la línea de cierre es idéntica en los 62 logs** de los tres entornos |
| 3a. `nowcast_puertas.py diputados` y `senado` (`--fecha 2026-06-01 --origen EJECUTIVO`, salida completa) | — | — | — | **5.141 campos cada uno, 0 distintos, max\|Δ\| = 0**, en los tres pares |
| 3b. `estimar_epsilon_tau.py` (`estricta__general` y `p`) | — | — | — | 129 campos cada uno, 0 distintos |
| 3c. skill + IC por ley y ΔBrier pareado, 8 cortes × 2 variantes | — | — | — | 112 campos, 0 distintos |
| 4. E3 contra E1/E2 sólo donde interviene `scipy` | — | — | — | no hay ninguna diferencia: `scipy` 1.18.1 y 1.17.1 dan lo mismo en la suite y en la huella |

**Sensibilidad de la huella** (para que «0 diferencias» signifique algo): diputados y senado *difieren* (34 de 78 campos comparados); una perturbación de 1e-12 en un solo campo (`p_aprobacion`) se detecta.

**Comprobaciones de plataforma:** con `pip install --dry-run --report --platform manylinux… --python-version 3.11 --only-binary=:all:` los 14 pines tienen rueda para **Linux/cp311** (el CI) y se resuelven los mismos 44 paquetes que en Windows.

**Un tropiezo de la medición (no de las versiones):** la primera vez corrí E1, E2 y E3 a la vez y `pytest` dio 3 fallas en E1 y E2 (`test_verificar.py`: `database disk image is malformed`). La causa es que `datos/proyectos/src/verificar.py:_abrir()` copia la base a un archivo temporal de **nombre fijo** y las tres corridas se lo pisaron. Repetido en serie: 53 pasan y 1 se saltea en E1 y en E2. El log del choque se conservó. Anotado en `PENDIENTES-POST-AUDITORIA.md`.

**Límites (declarados):** (1) la huella se corrió en Windows; el CI es Linux, y sólo se sabe que allí la suite pasa (lo confirmó Franco en A2), no que los números coincidan al último bit (BLAS distinto). (2) La huella no incluye las re-estimaciones con `statsmodels` (β, ψ, θ): la fase D las corre con este entorno fijado. (3) Los transitivos siguen libres (hoy resuelven idénticos en 3.11 y 3.14); si algún día derivan, la suite o la huella lo dirán. (4) Hoy hay **cuatro Pythons**: CI 3.11, PC 3.14, `bot-diario` 3.12, `icg-mensual` y `padron-vivo` 3.11; no se unificaron (no es de A3). (5) Instalar `requirements.txt` en la PC bajaría `scipy` de 1.18.1 a 1.17.1: no hace falta hacerlo.

## Bitácora de alcance

Todo cambio de alcance se escribe **acá antes de ejecutarse**. Sólo Franco lo autoriza, con la frase `CAMBIO DE ALCANCE:`.

| fecha | qué cambió | quién lo pidió | qué se posterga a cambio |
|---|---|---|---|
| 2026-09-29 | Alcance inicial fijado (este documento) | Franco | — |
