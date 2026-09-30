# Estado de ejecución de la auditoría (documento vivo)

> **Es el carril de la auditoría.** Todo lo que se hace en esta etapa es un ítem de esta tabla (fase + número). Lo que no está acá **no se hace**: se anota en `PENDIENTES-POST-AUDITORIA.md` (regla 1 del §9.9 del informe). Se actualiza **al terminar cada ítem y al cerrar cada sesión**: la conversación siguiente arranca de acá, no de la memoria del chat.
>
> Decisiones y su porqué: `AUDITORIA-INTEGRAL-2026-09.md` §9. Reglas del carril: §9.9. Definición numérica de "funcionando": §9.4.
> Estados: `PENDIENTE` · `EN CURSO` · `HECHO` (con la evidencia: comando y salida, o sha del commit) · `DESCARTADO` (con el motivo escrito y la firma de Franco).

**Última actualización:** 2026-09-30 — A1, A2 y A3 hechos (CI verde confirmado por Franco, también con los pines); A4 a A8 hechos; A9 hecho (Franco confirmó en *Actions*: los tres en verde); A10 hecho: **fase A CERRADA por Franco el 2026-09-30** (evidencia de salida abajo); **fase B en curso (2026-09-30): B1 empezado** (pre-registro escrito y commiteado antes de codificar).
**Dónde se trabaja:** `main`, commits chicos (uno por corrección), con la suite en verde **antes** de cada commit; sin `git push` (lo hace Franco). Los bots empujan a `main`: no se les toca el permiso. Rama sólo si una corrección no puede dejar la suite en verde entre commits (vida corta: se mergea en la misma sesión).
**Punto de partida (para deshacer):** el tag local `auditoria-punto-de-partida` marca `main` antes de la primera corrección.

## Fase A — Orden y limpieza

| ítem | qué | quién | criterio de salida | estado |
|---|---|---|---|---|
| **A1** | Verificar el arranque: `git status`, rama `main`, y correr la suite; el resultado debe coincidir con `00-linea-base.md` (§7) | Claude | mismo resultado que la línea base (el único rojo esperado es `test_insumos_del_motor_viajan`) | **HECHO** 2026-09-29 sobre `d0e4897` (evidencia en la sección «Evidencia de A1», abajo) |
| **A2** | **CI en verde** (decisión 11, opción 1): guardar en git los estadísticos por ley (JSON, no `.parquet`/`.csv`: están ignorados) que alcanzan para recalcular skill, IC, τ y ε₀; re-apuntar los consumidores; que `test_insumos_del_motor_viajan` pase | Claude | test verde en local; **Franco confirma en la pestaña *Actions* de GitHub** (d5) | **HECHO** 2026-09-29: verificado en local (simulación del CI) y **confirmado por Franco en *Actions*** («corrió perfecto»). Evidencia en «Evidencia de A2» (commits `51212bc`, `e944a3c`, `55ca0b8`) |
| **A3** | **Paridad de versiones** (d6): correr la suite en Python 3.11 (el del CI) y fijar versiones; documentar la de esta PC (3.14 / pandas 3.0) | Claude | resultados iguales en ambas | **HECHO** 2026-09-29: 0 diferencias entre 3.11, 3.14 y la PC (ver «Evidencia de A3»). **Franco confirmó en *Actions* (30-09) que sigue todo verde con los pines instalados** |
| **A4** | Escribir `coordinacion/QUE-SE-MIDE.md` desde el §9.4 (incluye d7: origen Senado sin publicar; y los límites: etiquetas de origen sin validar, presencia sin medir, cobertura de la canónica por año — d4-a) | Claude | archivo publicado; Franco lo lee | **HECHO** 2026-09-30: publicado (`coordinacion/QUE-SE-MIDE.md`) y **leído y aprobado por Franco** («está bien el documento»). Evidencia en «Evidencia de A4» |
| **A5** | **Apagar las mayorías especiales** (decisión 9): `nowcast()` con `tipo_mayoria ≠ SIMPLE` devuelve sin número y con el motivo | Claude | test que lo fija; el resto del número no cambia (`max|ΔP| = 0` en simple) | **HECHO** 2026-09-30: `nowcast()` sin número para mayorías especiales; en SIMPLE `max\|ΔP\| = 0` sobre la salida completa (ver «Evidencia de A5») |
| **A6** | **Eliminar HTML y panel** (decisiones 1 y 6; alcance según §9.1): los 3 HTML de producto, sus generadores y sus `.js` de datos; `REGENERAR.ps1` paso 8 → JSON de regresión; `verificar_regeneracion.py`; sacar `Senado_2002-03-05_muestra.html` y `premortem-report-…html`; **se quedan los 6 fixtures** de los tests de los bots; `comparar_vias_icg.py` pierde la salida HTML pero **se conserva** (ICG, ver D6). Antes de sacar cada archivo: copia a `Archivos_Borrar/` y `git rm`; se busca quién lo referencia | Claude | `git ls-files \| grep -i html` devuelve sólo los 6 fixtures; el JSON de regresión existe y un test lo compara con el motor; suite verde | **HECHO** 2026-09-30: `git ls-files \| grep -i html` devuelve sólo los 6 fixtures; JSON de regresión + test; suite verde (ver «Evidencia de A6») |
| **A7** | **Poda P0 y P1** (decisión 10; ≈ 7.000 líneas). **Antes:** confirmar que nada de lo que se mueve pertenece a δ, θ, ψ, β ni al ICG (decisión 2 y ronda 2, punto 9 —ICG—, ver §9.1b del informe); `comparar_vias_icg.py` **sale de P0** | Claude | los criterios de salida del §5 del informe (`max|ΔP| = 0`, suite igual menos lo movido) | **HECHO** 2026-09-30 con **una excepción confirmada por Franco** (`fase1_rec_por_tema` se queda) y los stubs de `ensemble.py` **sacados por decisión suya** (ver «Evidencia de A7» y «Resolución de las excepciones»): `max\|ΔP\| = 0`, suite igual menos lo movido |
| **A8** | **Worktree y rama `suspicious-lalande`** (d9): rescatar `c916e0e` a una rama (`rescate-taxonomias`) y avisar a Franco para que borre el worktree y `Archivos_Borrar/repro/` | Claude + Franco | el commit queda a salvo; worktree y `repro/` eliminados por Franco | **HECHO** 2026-09-30: el commit `c916e0e` está a salvo en `rescate-taxonomias`; **worktree y `Archivos_Borrar/repro/` eliminados por Franco y verificados** (ver «Evidencia de A8») |
| **A9** | **Bots** (d10): comprobar que los tres workflows siguen sanos después de A6 y A7 (rutas, insumos); **no** activar protección de rama con "requerir PR" | Claude | los workflows corren sin cambios de permisos; Franco confirma en *Actions* | **HECHO** 2026-09-30 (los tres workflows en verde en *Actions*, confirmado por Franco) |
| **A10** | Actualizar `CLAUDE.md`: sacar la regla del TABLERO DE CONTROL y las referencias a los HTML y al mapa eliminados; **conservar** el bloque MODO AUDITORÍA | Claude | `tests/test_rutas_citadas_existen.py` y `tests/test_rutas.py` verdes | **HECHO** 2026-09-30 (commit `edcc93e`; ver «A10 — `CLAUDE.md`» y «Salida de la fase A») |

**Salida de la fase A:** suite igual o mejor que la línea base; `nowcast_puertas.py` corre; mayorías especiales devuelven sin número; sólo los 6 fixtures HTML; CI en verde confirmado por Franco.

## Fase B — Anclaje básico (`05` §5.3, pasos 1-2)

| ítem | qué | criterio de salida | estado |
|---|---|---|---|
| **B1** | Registro de parámetros **generado desde el código** + `test_defaults_fijados` | cambiar un default rompe un test | **EN CURSO** (pre-registro: «B1 — pre-registro») |
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

### A4 — `coordinacion/QUE-SE-MIDE.md` (2026-09-30)

**Qué se hizo.** Se publicó `coordinacion/QUE-SE-MIDE.md` desde el §9.4: capa por capa qué se mide, con qué resultado, de qué archivo sale y qué **no** se mide; la definición numérica de «funciona» con el estado de hoy de cada uno de los 5 objetivos (**no se cumple ninguno**); los límites (origen sin validar, presencia sin medir, cobertura de la canónica por año, acta ≠ ley, ficha de desvío, estimadores contaminados, alcance de la reproducibilidad); las cifras que ya no se deben citar; y cómo se reproduce cada número. Incluye d7 (origen Senado sin medir y sin publicar; «mayoría simple en ambas cámaras» = Senado como cámara votante).

**Cada cifra se verificó contra su archivo** (no se copió del informe). Reproducidas desde cero: mayorías especiales por tipo (dos tercios 256 actas, Brier 0,3028; tres cuartos 124, 0,1854; absoluta 54, 0,1037; simple 5.394, 0,0260 contra 0,0193 de la constante, desde `Archivos_Borrar/auditoria/contraste_aprobacion_actas.parquet`); skill sin los votos sin ley (con los estadísticos de A2); % `DESCONOCIDO` (2.582 de 5.998 = 43,05%). Leídas de su JSON: skill por era y cámara con IC, cobertura de la banda, encoger/cortar, `MIN_HIST`, récord por tema, guard de era, β con offset limpio.

**Medición nueva: cobertura de la canónica por año y cámara** (d4-a): `coordinacion/AUDITORIA-2026-09/cobertura_canonica.py` → `resultados/cobertura_canonica.json`. Criterio fijado antes de calcular (queda escrito en el docstring del script). Resultado: **dentro de cada acta el voto individual está completo** (257/72 filas; cobertura 0,97–1,01); **lo que falta son actas**. **El hueco de Diputados 2020–2023 se confirma: 25 actas y 6.421 votos individuales** (lo que decía el lote A), contra 96–190 actas por año en los años vecinos. Además, no hay ninguna acta del Senado antes de 2004 ni de Diputados en 1995, 1996, 1998–2000. La regla marca 8 años-cámara como sospechosos; **no prueba que falten actas** (no hay número oficial de sesiones). De las 142 actas de la canónica que no entran al censo, 51 tienen afirmativos y negativos y **el motivo no se auditó** (anotado en `PENDIENTES-POST-AUDITORIA.md`).

**Dos errores de mi propia medición, corregidos y escritos en el script:** (a) la cobertura individual daba hasta 1,71 porque el denominador incluía actas sin conteo declarado; (b) el % de votos sin ley daba 0 en todos los años porque el censo marca «sin ley» con el id del acta (`acta:…`), no con un nulo.

**Diferencias con el informe (ninguna cambia una conclusión):**
1. IC del skill de la era vigente: el harness da **[−0,264; 0,246]** (`baseline_voto_individual.json`); el «[−0,28; 0,26]» del informe es del control independiente. Semiancho 0,255. Igual criterio que la nota de A2 para C1.
2. Skill sin los votos sin ley: el valor coincide (0,166) pero el IC del harness es **[0,084; 0,252]** (2.944 leyes, 585.822 votos), no [0,076; 0,242].
3. «3.731 leyes» incluye una unidad por cada acta sin ley identificable (el 15,3% de los votos); ahora está dicho en el documento.
4. La cifra «−2,12%» del récord por tema es «mejora relativa»: en palabras, **empeora el Brier 2,12% [0,84; 3,48]**. El documento lo dice en palabras.

**Franco leyó el documento y lo aprobó sin cambios (2026-09-30).**

### A5 — pre-registro (2026-09-30, escrito ANTES de medir)

**Qué cambia (decisión 9):** `nowcast()` con un `tipo_mayoria` que `definiciones.normalizar_mayoria_valor` lleva a algo distinto de `SIMPLE` (`ABSOLUTA`, `DOS_TERCIOS`, `DOS_TERCIOS_CUERPO`, `TRES_CUARTOS`, o el texto que se normalice a ellos) devuelve `p_aprobacion = None` y `motivo_sin_numero`, **sin correr la simulación** (la guarda va antes de cargar nada). Lo que la normalización manda a `SIMPLE` (incluidos `None` y texto no reconocido) sigue calculándose como hoy. No se tocan `simular_con_guardas`, `simular_votacion`, `agregador` ni `composicion_capitulos`: los usan las mediciones (`contraste_aprobacion.py` evalúa mayorías especiales contra resultados) y los tests.

**Panel de comparación, con el motor real y los defaults (`n_sims = 2000`, `seed = 0`), corrido sobre el código de `HEAD` (valor anterior) y sobre el código nuevo:**
- 9 casos `SIMPLE`: Diputados y Senado como origen a 2026-06-01 con origen EJECUTIVO; Diputados 2024-06-01 sin origen; Senado 2024-06-01 con origen OPOSICION; `tipo_mayoria="simple"` (minúscula) y `tipo_mayoria=None` (ambos = SIMPLE); dos con `proyecto_id` real (`HCDN274473` a 2024-06-01 y `HCDN279791` a 2026-06-01, para ejercitar las puertas A y C) y uno con el Senado como origen y el segundo proyecto.
- 9 casos de mayoría especial: Diputados y Senado como origen × {`ABSOLUTA`, `DOS_TERCIOS`, `DOS_TERCIOS_CUERPO`, `TRES_CUARTOS`} a 2026-06-01, origen EJECUTIVO, más el texto crudo `"dos tercios"`.

**Qué decide (umbral):** (1) en los 9 casos `SIMPLE`, la salida completa —todos los campos, no sólo la probabilidad— es **idéntica** al valor anterior: `max|ΔP| = 0` y 0 campos distintos; (2) en los 9 de mayoría especial, `p_aprobacion` es `None` con motivo y el valor anterior era un número (queda registrado); (3) el test nuevo falla si se le quita la guarda (sabotaje en memoria) y no puede pasar si la simulación llega a correr (se le sustituye por una que rompe).

### A5 — mayorías especiales apagadas (2026-09-30; pre-registro arriba, commit `9d81932`)

**Presentación en los tres niveles (ADR-0015).** *(1) La función:* `nowcast()` normaliza `tipo_mayoria` con `definiciones.normalizar_mayoria_valor` (la regla de todo el repo) y, si no es SIMPLE, devuelve `p_aprobacion = None` y `motivo_sin_numero` **sin cargar ni simular nada** (la guarda va antes de la primera carga). Antes calculaba el número con el umbral de cada tipo. `imprimir()` y la CLI toleran el caso sin número. *(2) El motor en su conjunto:* `nowcast()` lo llaman la CLI, `casos/nowcast_puertas_html.py` (siempre SIMPLE; se elimina en A6) y dos tests (SIMPLE por defecto); `composicion_capitulos`, `simular_con_guardas`, `agregador` y `contraste_aprobacion.py` **no se tocan** (las mediciones y los tests siguen pudiendo evaluar mayorías especiales). No mueve el número de SIMPLE (medido). Supuesto que se saca: «el modelo sirve para cualquier tipo de mayoría»; supuesto que se mantiene: `normalizar_mayoria_valor` lleva lo desconocido, incluido `None`, a SIMPLE (así ya trabajaba el resto del repo). *(3) La fórmula:* `FORMULA-COMPLETA.md` fila 5 y §I.2b: el término «umbrales por tipo de mayoría» queda **marcado como inactivo** para los tipos especiales, no borrado.

**Medido (criterio pre-registrado), motor real, `n_sims = 2000`, `seed = 0`, valor anterior = `git archive` del código sin tocar:**

| criterio | resultado |
|---|---|
| 1. 9 casos SIMPLE (Diputados y Senado como origen, 2 fechas, con y sin origen, `tipo_mayoria` `"simple"` y `None`, y 3 con `proyecto_id` real que ejercitan las puertas A y C): salida completa idéntica | **46.437 campos comparados, 0 distintos, `max\|ΔP\| = 0`** |
| 2. 9 casos de mayoría especial (4 tipos × 2 cámaras + el texto crudo «dos tercios») | el valor anterior era un número (0,5335 absoluta · 0,1421 dos tercios · 0,0917 dos tercios del cuerpo · 0,036 tres cuartos); **ahora `None` con motivo en los 9** |
| 3. el test falla sin la guarda | `tests`: 191 comprobaciones; con la guarda abierta (todos los tipos pasan) **falla**; con la guarda bloqueando todo (ni SIMPLE pasa) **falla** |

**El test** (`modelo/ensemble/tests/test_mayorias_especiales_apagadas.py`) no corre ninguna simulación: sustituye la carga y las simulaciones por algo que rompe y comprueba (a) que los 4 tipos y **17 textos crudos reales** de `actas_canonico.tipo_mayoria` devuelven sin número sin llegar a ellas —o sea que la guarda va *antes* del cálculo—, (b) que los 8 textos de mayoría simple de la fuente, `None` y el texto no reconocido **sí llegan** al cálculo, (c) que `imprimir()` y la CLI no se rompen. Un dato de prueba mío (`"Mayoría absoluta de los miembros"`) falló porque **no existe en la fuente** y el normalizador lo lleva a SIMPLE; se reemplazó por el vocabulario real, todo el cual se normaliza bien.

**Suite:** `pytest` 54 pasan; **63 scripts en 0** (los 62 de siempre + el nuevo); árbol idéntico antes y después. `QUE-SE-MIDE.md` actualizado (antes decía «siguen encendidas hasta A5»); `modelo/ensemble/README.md` actualizado.

**Límites / observaciones:** (1) la guarda se apoya en que el llamador pase el tipo de mayoría **del proyecto**; hoy `nowcast()` no lo deduce del `proyecto_id` (default SIMPLE). Un proyecto que necesita dos tercios y se consulta sin `--tipo-mayoria` sigue dando el número de simple. Es el comportamiento de siempre, ahora declarado; deducirlo sería un cambio nuevo (no está en el plan). (2) Con la guarda, las columnas `pasos`, `camaras` y `record_por_tema` llegan vacías en el resultado sin número; `casos/nowcast_puertas_html.py` fallaría con un tipo especial, pero ese archivo sale en A6 y nunca lo llama con otro tipo.

### A6 — HTML y panel eliminados (2026-09-30; commits `fa107e2`, `3216c6b`, `43537e7`, `8367d85`, `55ecda2`, `1547c6e`)

**Orden de trabajo (para que nada quedara sin reemplazo):** (1) primero el sustituto: `modelo/ensemble/outputs/panel_regresion.json` (203 KB; la salida completa de `nowcast_puertas.py diputados --fecha 2026-06-01 --origen EJECUTIVO`, P = 0,6132, idéntica a la del código sin tocar de A5) y `modelo/ensemble/tests/test_panel_regresion.py`, que corre el motor con los mismos argumentos y exige igualdad campo por campo; `REGENERAR.ps1` paso 8 y la sección 6 de `verificar_regeneracion.py` pasan al JSON; (2) recién entonces las eliminaciones, en tres commits, cada una con copia previa en `Archivos_Borrar/A6-eliminados/` (`cmp`: idénticas) y búsqueda de referencias antes del `git rm`.

**Qué salió de git** (recuperable con `git log -- <ruta>`): `Nowcast-Puertas.html` (153 KB) + `casos/nowcast_puertas_html.py` (350 líneas); `MAPA-MODELO.html` (89 KB) + `mapa_modelo_datos.js` (161 KB) + `producto/dashboard/src/generar_mapa_modelo.py` (482 líneas); `TABLERO-CONTROL.html` (14 KB) + `tablero_datos.js` (212 KB); `datos/senado/muestras/Senado_2002-03-05_muestra.html` (720 KB); `docs/contexto/premortem-report-20260625-validado.html` (11 KB). `comparar_vias_icg.py` **se conserva sin la salida HTML** (`SALIDA`, `CSS`, `html()`: 298 → 132 líneas; ya estaba neutralizado desde el 11-08 y no producía nada). `rutas.py` sacó `TABLERO_DATOS_JS` y `TABLERO_CONTROL_HTML` (nadie las usaba).

**Referencias:** ejecutables, ninguna queda (`grep` sobre `.py`, `.ps1`, `.yml`). Punteros vivos corregidos: `README.md`, `casos/README.md` (describía tres generadores cuando sólo quedaba uno), `producto/dashboard/README.md` (reescrito: módulo sin código), `modelo/ensemble/README.md`, docstring de `beta_dictamen.py`, `FORMULA-COMPLETA.md`, `coordinacion/README.md`, `datos/expedientes/README.md`, `datos/senado/NOTA-2001-2003.md`, `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`, `variables/proyecto/README.md`. **No se reescribieron** los documentos históricos (prompts, bitácoras, ADR, `EN-HUMANO.md`, `TABLERO.md`) que nombran estos archivos. Los tres workflows de los bots no mencionan ninguno (`grep`); la comprobación completa de los bots es el ítem A9.

**Criterio de salida:**

| criterio | resultado |
|---|---|
| `git ls-files \| grep -i html` sólo devuelve los 6 fixtures | **cumple**: `dae_32_2026`, `tp_87_144`, `diputados_2832-D-2026`, `senado_1091.26`, `detalle_1000`, `listado_2018` |
| el JSON de regresión existe y un test lo compara con el motor | **cumple**; el test **detecta un cambio real de parámetro**: con `TAU` 1,19 → 1,30 falla y lista los campos que se movieron (P 0,6132 → 0,5762) |
| suite verde | PC: `pytest` 54 pasan, **64 scripts en 0**, árbol idéntico antes y después. Checkout limpio de `1547c6e`, Python 3.11 y pines: `pytest` 53 pasan y 1 se saltea, **64/64 scripts en 0** (incluido `test_panel_regresion`, 25 s) |

*Nota de método:* durante la sesión cada commit corrió `pytest` (54 verdes); la tanda completa de 64 scripts se corrió **una vez, sobre el estado final**, no por commit.

**Observaciones (ninguna abre trabajo):**
1. **El JSON no se pone rojo por lo que suben los bots:** `bot-diario` y `padron-vivo` sólo escriben `estado_bot.json`, `tp_entradas`, `dae_entradas`, `votaciones_nuevas` y los archivos de vigilancia del padrón; ninguno es insumo del motor a 2026-06-01. **Riesgo para D6:** `icg_mensual.csv` (lo escribe `icg-mensual` el día 5 de cada mes) sí es insumo; hoy no mueve el número porque el ICG está desconectado, pero cuando D6 lo conecte el test se moverá una vez por mes. Queda escrito en el docstring del test.
2. **Se conserva `producto/dashboard/data/mapa_modelo_semantica.json`** (73 KB de texto curado) **sin consumidor**: no estaba en lo que el informe manda eliminar. Anotado en `PENDIENTES-POST-AUDITORIA.md`, junto con `COMMITEAR.ps1` y `COMMITEAR-2026-09-08.ps1` (scripts de commit de una sola vez que nombran `tablero_datos.js`; históricos).
3. `MAPA.md` sigue en «1 a mirar» de `verificar_regeneracion.py` (481 líneas contra un presupuesto de 460; eran 472 al empezar la auditoría): lo agrandan los archivos nuevos de A2–A5, no las eliminaciones. Es el mismo control que ya figuraba en la línea base.
4. **`CLAUDE.md`** todavía manda actualizar `tablero_datos.js` (regla del TABLERO DE CONTROL) y cita los HTML; el bloque MODO AUDITORÍA ya prevalece sobre eso. Se corrige en A10, como dice el plan.

### A7 — pre-registro (2026-09-30, escrito ANTES de mover nada)

**Qué se mueve.** P0 y P1 del §5 del informe, con estas precisiones que salieron del relevamiento:
- **Método.** `git mv` a `coordinacion/archivo/A7-poda-2026-09/<ruta original>`, con el sufijo `.archivado` en el código, para que ni `pytest`, ni el bucle de scripts del CI, ni el indexador, ni `test_rutas*` lo tomen como código vivo; restaurar es `git mv` y quitar el sufijo. Los `.md` se mueven tal cual. **Nada sale de git** (Franco: sólo el HTML y el panel salen de git). Los JSON de resultados quedan en `evaluacion/baseline/outputs/` (evidencia que citan los ADR). Un `README.md` en la carpeta del archivo dice qué es cada cosa y cómo restaurarla.
- **P0:** `composicion_capitulos`, `tema_por_capitulo`, `capitulos_nombre`, `backtest_cadena` (con sus 4 tests); los stubs «dados de baja» de `ensemble.py` (`componer`, `_p_llega_de_embudo`, `nowcast_proyecto`, `nowcast_auto`, `imprimir_tarjeta`, `main`, `_BAJA_V1`; `test_ensemble.py` los fija hoy y se ajusta); `CONECTAR-GIT.md`, `0009-BORRADOR-…md`, `_wtest`. Se **queda** `_cargar_proyector` (lo usa `puerta_d`).
- **P1:** `prueba1/2/3`, `validar_leybases_por_capitulos`, `validar_piloto_capitulos`, `validar_piloto_titulos`, `diagnostico_senado`, `firma_tematica_desvio/fase0_celdas/fase1_2` (+ test), `medir_estabilidad_record_por_tema`, `fase0_control_temas`, `medir_rec_por_tema`, `record_por_origen` y `_brazos` (+ test).
- **EXCEPCIÓN — NO se mueve:** `fase1_rec_por_tema.py` (+ `test_fase1_rec_por_tema.py`). `medir_record_por_tema_limpio.py` —la medición limpia de ADR-0034, cuyo resultado cita `QUE-SE-MIDE.md`— importa `K_SHRINK` y `_areas_de` de él; el informe decía «nadie los importa» y para éste no era cierto (regla 9: ante la duda, no se hace y se anota).
- **«Rescatar `split_half` y el bootstrap» (P1):** el bootstrap por ley ya vive en `censo_estadisticos.py` (A2). `split_half` queda en el archivo (existe una versión en `record_por_origen` y otra en `firma_tematica_fase1_2`); **no se agrega código a módulos vivos** (regla 3) y su lugar se documenta en el README del archivo.

**Confirmación que exige el plan, hecha antes de mover:** nada de lo que se mueve pertenece a δ, θ, ψ, β ni al ICG. (1) Por nombre (`beta_dictamen`, `sobre_tablas`, `estimar_psi/theta`, `icg`, `delta_caracter`, `condicionar`, `puerta_a`…): sólo `record_por_origen.py` los nombra, y es para **citar** dos veces el criterio de `estimar_psi_arrastre.py` en un docstring; no lo importa. (2) Ningún módulo del motor ni ningún estimador importa a un candidato (grafo de imports de todo el repo). (3) Ningún dato que escriban los candidatos lo lee algo fuera de ellos (`.mapa`): sólo quedan sus JSON de resultados, que no se mueven.

**Panel y umbral (con el motor real; valor anterior = código previo a A7):**
1. Los 9 casos SIMPLE del panel de A5 (referencia: la salida de A5, motor sin cambios desde entonces salvo docstrings): comparación completa, **0 campos distintos, `max|ΔP| = 0`**; y el test del JSON de regresión pasa.
2. Una porción del censo (actas del 2026-05-01 al 2026-07-01, mismo código y mismas variantes que `censo_detalle_paralelo.py`): `p` y todas las `p__*` **idénticas voto a voto**, mismo número de votos y de actas (criterio (ii) del §5).
3. Suite: `pytest` igual (54 pasan); scripts: los 64 de hoy **menos los 6 tests que se mueven** (`test_composicion_capitulos`, `test_backtest_cadena`, `test_capitulos_nombre`, `test_tema_por_capitulo`, `test_firma_tematica`, `test_record_por_origen`) = **58**, todos en 0. El único test que se modifica es `test_ensemble.py` (los stubs).
4. `.mapa/buscar.py --archivo <candidato>` y el grafo de imports: sólo tests, validaciones o candidatos entre sí.

**Orden de los commits (uno por línea de ADR):** capítulos/pivotes/Senado (P1, ADR-0029/0030) → `composicion_capitulos`, `capitulos_nombre`, `tema_por_capitulo` (P0) → firma temática (ADR-0032) → estabilidad, fase 0 y `medir_rec` (ADR-0028/0031) → récord por origen (ADR-0033) → `backtest_cadena` → stubs de `ensemble.py` → documentos → índice y evidencia.

### A7 — poda P0 y P1 (2026-09-30; commits `d6a46d6` (pre-registro) … `2d1b275`)

**Qué se movió** (`git mv` a `coordinacion/archivo/A7-poda-2026-09/`, con sufijo `.archivado` en el código; nada sale de git; el README de esa carpeta dice qué es cada cosa y cómo restaurarla): 19 archivos de código (4.920 líneas), 6 tests (1.016 líneas) y 3 documentos. Por línea de ADR: capítulos/pivotes/Senado (7 scripts P1) · `composicion_capitulos`, `capitulos_nombre`, `tema_por_capitulo` (+ 3 tests) · firma temática (3 + test) · `medir_estabilidad_record_por_tema`, `fase0_control_temas`, `medir_rec_por_tema` · `record_por_origen` y `_brazos` (+ test) · `backtest_cadena` (+ test) · `CONECTAR-GIT.md`, `0009-BORRADOR`, `_wtest`. Los JSON de resultados no se movieron. **Total: 5.936 líneas de código y tests**, no las ≈ 7.000 del informe: la diferencia son las dos excepciones (≈ 300 líneas) y que esa estimación era gruesa. El índice del repo pasó de 200 archivos y 43.434 líneas a **175 y 37.499**; los scripts de test, de 64 a **58**.

**Confirmación previa que exigía el plan (hecha antes de mover, en el pre-registro):** nada de lo movido pertenece a δ, θ, ψ, β ni al ICG — por nombre, por grafo de imports y por flujo de datos.

**Medido (criterios pre-registrados en `d6a46d6`, motor real, valor anterior = código previo a A7):**

| criterio | resultado |
|---|---|
| 1. los 9 casos SIMPLE del panel de A5, salida completa | **46.437 campos, 0 distintos, `max\|ΔP\| = 0`**; los 9 de mayoría especial siguen sin número y con motivo; el test del JSON de regresión pasa |
| 2. porción del censo (actas 2026-05-01 a 2026-07-01, mismo código y variantes que `censo_detalle_paralelo.py`) | 8.882 votos y 51 actas antes y después, mismas filas; **las 6 columnas `p*` idénticas bit a bit** (`max\|d\| = 0`) |
| 3. suite | PC: `pytest` 54 pasan y **58 scripts en 0** (64 − 6 movidos, como se fijó); árbol idéntico antes y después. Checkout limpio de `2d1b275`, Python 3.11 y pines: `pytest` 53 pasan + 1 se saltea y **58/58 scripts en 0**. Los 6 tests movidos ya no corren. Además `pytest` (54 verdes) en cada uno de los 9 commits |
| 4. quién los usa | `buscar.py --archivo` y el grafo de imports: sólo tests, validaciones o candidatos entre sí. **Extra:** al correr el motor y el harness (y los 4 scripts de medición que siguen vivos) **se cargan 0 de los 19 módulos archivados** |

**Dos excepciones (resueltas por Franco el 30-09; ver «Resolución de las excepciones» más abajo):**
1. **`fase1_rec_por_tema.py` (+ su test) NO se movió.** El informe decía «nadie lo importa» y no era cierto: `medir_record_por_tema_limpio.py` —la medición limpia de ADR-0034, la que sostiene «el récord por tema empeora el Brier 2,12%» de `QUE-SE-MIDE.md`— importa `K_SHRINK` y `_areas_de` de él. Para moverlo habría que copiar esas dos cosas al script vivo. **Propuesta:** dejarlo como está.
2. **Los stubs «dados de baja» de `ensemble.py` NO se sacaron.** No son código muerto: el archivo dice «no se borraron a propósito» (quien llame a la API de la v1 recibe un `SystemExit` con el motivo y a dónde ir) y `test_ensemble.py` lo fija («falla si alguien las revive sin pasar por el ADR»). Sacarlos ahorra ≈ 40 líneas, exige tocar un archivo del motor y cambiar ese test. **Propuesta:** dejarlos. Si preferís sacarlos, se hace en un commit chico con la presentación de ADR-0015.

**Otras observaciones (ninguna abre trabajo):** (a) el criterio (i) del informe (HTML del panel idéntico) ya no existe: lo reemplaza el JSON de regresión de A6. (b) La cita a un archivo movido dentro de un docstring de `.py` rompe `test_rutas_citadas_existen` (la regex toma `x.py` de `x.py.archivado` y no lo encuentra), así que las dos citas vivas (`agregador.py` y `rutas.py`) se reescribieron sin ruta. (c) `MAPA.md` sigue en «1 a mirar» de `verificar_regeneracion.py` (481 líneas contra 460): la poda no lo arregla porque lo agrandan las secciones del inventario y los README, no el código. (d) Siguen vivos varios scripts de medición cerrados que el informe no listaba (`medir_guard_era.py`, `medir_fuga_historia.py`, `medir_record_por_tema_limpio.py`, `censo_*`, `chequear_direccion_beta.py`…): entran en las fases C y D.

### Resolución de las excepciones de A7 (2026-09-30; commit `ed978ac`)

Franco: **(1) «dejalo»** → `fase1_rec_por_tema.py` y su test **se quedan**. **(2) «sacalos»** → se sacaron los stubs de `ensemble.py`.

**Qué salió de `modelo/ensemble/src/ensemble.py`** (413 → 358 líneas): `componer`, `_p_llega_de_embudo`, `nowcast_proyecto`, `nowcast_auto`, `imprimir_tarjeta`, la CLI (`main` y el bloque `__main__`), `_BAJA_V1` y `_p_embudo_path` (helper de esa CLI, sin ninguna referencia en el repo). **Se quedan** `_cargar_proyector` y `_cargar_simulador` (los usa `puerta_d`), `roster_nominal`, `simular_con_guardas` y `_resolver_proyecto_id` (tiene su test). El código eliminado quedó **literal** en `coordinacion/archivo/A7-poda-2026-09/modelo/ensemble/src/ensemble_stubs_v1.py.archivado`. `test_ensemble.py` pasó de «los stubs levantan `SystemExit`» a «los stubs **no existen**» (misma intención: falla si alguien los revive sin pasar por el ADR; 35 comprobaciones; con un stub revivido en memoria el test falla). Presentación de ADR-0015 en el mensaje del commit: función (se elimina la trampa de la v1; quien la llame recibe `AttributeError`), motor (nadie fuera de `ensemble.py` y de su test los llamaba: `backtest_cadena`, el único llamador real, se archivó en el commit 6) y fórmula (la v1 no estaba en la fórmula activa).

**Medido (mismos criterios que la poda):** panel, 9 casos SIMPLE contra A5: **46.437 campos, 0 distintos, `max\|ΔP\| = 0**; los 9 de mayoría especial siguen sin número; porción del censo (2026-05-01 a 07-01): **6 columnas `p*` idénticas bit a bit**; **0 de los 19 módulos archivados se cargan**; PC: `pytest` 54 y **58 scripts en 0**, árbol idéntico antes y después; checkout limpio de `ed978ac` con Python 3.11 y pines: `pytest` 53 + 1 y **58/58 scripts en 0**.

### A8 — rescate del commit `c916e0e` (2026-09-30)

**Qué se hizo (mi parte).** La rama **`rescate-taxonomias`** (`8e127fe`) es `main` + el commit `c916e0e` (15-09, «`datos/taxonomias`: `asignada_en` estable en `_de_muestra_manual`»: la función usaba `_ahora()` en cada fila y en cada corrida, así que las 95 filas de fuente `manual` se «reemplazaban» sin cambio real y ensuciaban el diff de `asignaciones.csv`). Toca sólo `datos/taxonomias/src/registro.py` (+27 −1). **Verificado:** `registro.py` no había cambiado en `main` desde el punto de partida de esa rama (aplica limpio); el blob de `registro.py` en la rama es idéntico al de `c916e0e`; el diff `main..rescate-taxonomias` coincide línea por línea con el parche original; y `datos/taxonomias/tests/test_registro.py` con la versión rescatada sobre el árbol completo da **27/27** (igual que `main`). **`main` no se tocó.** La rama **no se mergea** (es un arreglo del registro de taxonomías, no de la auditoría): se anotó en `PENDIENTES-POST-AUDITORIA.md`.

*Cómo:* `git worktree add` falló («Filename too long»: la ruta del scratchpad es demasiado larga para un checkout completo en Windows), así que la rama se armó con comandos de bajo nivel de git (árbol de `main` con `registro.py` reemplazado, autor, fecha y mensaje originales más «(cherry picked from commit …)»), sin árbol de trabajo. Al fallar, `git worktree add` dejó creada la rama `rescate-taxonomias` apuntando a `main`; era mía y se reusó.

**Estado de lo que borra Franco (medido hoy):** el worktree `.claude/worktrees/suspicious-lalande-8a89b7` está **limpio** (sin cambios sin commitear ni archivos sin rastrear), pesa 175 MB y su único commit propio (`c916e0e`) ya está a salvo; `Archivos_Borrar/repro/` (225 MB) es la copia de `HEAD` con el censo regenerado de la línea base. Nada fuera de los documentos de la auditoría los cita.

**Qué pasó con el borrado (2026-09-30, revisado a mano).** `git worktree remove` se trabó al borrar `.github/workflows` dentro del worktree (`Filename`/acceso: las subcarpetas son puntos de reanálisis de OneDrive, `workflows` además de solo lectura). Verificado después: (a) el registro del worktree **ya no figura** en `git worktree list` (sólo `main`); (b) `Archivos_Borrar/repro/` **no existe**; (c) la rama `rescate-taxonomias` (`8e127fe`), la rama vieja y el commit `c916e0e` siguen; (d) `main` limpia; (e) `censo_detalle_2026-09-28.parquet` (35,2 MB) sigue; (f) **la carpeta del worktree sigue** con los 469 archivos: la sesión de la app «Fix registro.py: consolidar() reescribe timestamps de fuente manual» (`local_d0a3abbb…`, sin archivar y con esa carpeta como directorio de trabajo) la mantiene retenida (`get_storage_usage`: 1 worktree, 175 MB, «held by sessions»). **Para cerrar:** archivar esa sesión en la app (el worktree está limpio, la app lo elimina sola), y después `git worktree prune`; si la carpeta resiste, borrarla desde el Explorador con OneDrive en pausa.

**`Archivos_Borrar/` quedó completamente vacía**, no sólo sin `repro/`: se fueron también `auditoria/` (los datos de trabajo de la auditoría) y `A6-eliminados/` (mis copias de seguridad de A6). Verificado que **nada depende de eso**: `pytest` 54 verdes, `verificar_regeneracion` 15 OK · 1 a mirar, el test del JSON de regresión pasa, y los checkouts limpios del CI simulado (que nunca tuvieron esa carpeta) daban 58/58. Lo que hay que saber: (1) lo eliminado en A6 y A7 **sigue en el historial de git** (p. ej. `git show 3216c6b^:"Nowcast Congreso Argy/Nowcast-Puertas.html"`), así que las copias eran redundantes; (2) el detalle por acta de la medición de mayorías especiales (`contraste_aprobacion_actas.parquet`, la fuente del Brier por tipo de mayoría de `QUE-SE-MIDE.md`) **ya no está en disco**; `QUE-SE-MIDE.md` ya decía que no viaja por git y se regenera con `coordinacion/AUDITORIA-2026-09/contraste_aprobacion.py` (necesita el detalle del censo, que sí está)

**Cierre de A8 (2026-09-30, verificado a mano tras el borrado final de Franco).** `git worktree list` sólo lista `main`; la carpeta `.claude/worktrees/suspicious-lalande-8a89b7` y `.claude/worktrees/` **ya no existen**; `Archivos_Borrar/repro/` no existe; la rama `rescate-taxonomias` (`8e127fe`) y el commit `c916e0e` siguen; `main` limpia; `censo_detalle_2026-09-28.parquet` (35,2 MB) sigue. La app ve el worktree en 0 bytes. **Quedan dos cosas menores, ambas opcionales y de Franco:** (a) la rama local `claude/suspicious-lalande-8a89b7` (el commit ya está en `rescate-taxonomias`; borrarla necesita `git branch -D`); (b) la sesión de la app «Fix registro.py…» sigue sin archivar y apunta a una carpeta que ya no existe (archivarla la ordena).

### A9 — pre-registro (2026-09-30, escrito ANTES de comprobar)

**Qué se comprueba.** Los tres workflows de recolección (`bot-diario`, `padron-vivo`, `icg-mensual`) tal como están en `HEAD` (`69165e8`; `origin/main` ya es igual a `main`: Franco subió todo hasta A8) contra el punto de partida (`auditoria-punto-de-partida`, `bcc62b3`), después de A6 (HTML y panel) y A7 (poda). `tests.yml` no es un bot (lo cubrieron A2 y A3). **No se toca ningún workflow, ningún permiso ni la protección de rama.**

**Criterios (umbral: 0 fallas en cada uno; fijados antes de mirar los resultados):**
1. **Sin cambios.** `git diff` de los tres `.yml` entre el punto de partida y `HEAD` vacío; mismos `on:` (cron y `workflow_dispatch`, ningún `pull_request`) y mismos `permissions:` (`contents: write`, `issues: write`).
2. **Rutas.** Toda ruta `Nowcast Congreso Argy/...` que nombran los workflows (scripts, `requirements`, lo que `git add` commitea, el archivo que lee el paso `github-script`) existe en `HEAD`, **viaja por git** (o es salida que el script crea) y no está entre los archivos eliminados (`D`) o movidos (`R`) desde el punto de partida (37 hoy).
3. **Imports.** La clausura de imports locales de los scripts de entrada (`dae_senado`, `tp_diputados`, `votaciones`, `vigilar_padron` con `ingesta_padron` y `bajar_nomina`, `ingesta_icg`) sólo contiene archivos que existen y que no fueron eliminados ni movidos; los imports de terceros están cubiertos por lo que instala cada workflow.
4. **Texto.** Ningún archivo de esa clausura ni de los workflows nombra (por nombre de archivo) algo eliminado o movido en A6/A7.
5. **Insumos y consumidores.** Cada archivo que escriben los bots (`dae_entradas`, `tp_entradas`, `votaciones_nuevas`, `estado_bot`, `estado_vigilancia`, `vigilancia_padron.md`, `icg_mensual.csv`) sigue existiendo y viajando por git, y sus lectores (`.mapa/buscar.py --dato`) siguen existiendo.
6. **Ensayo con el código de `HEAD`** en un checkout limpio (`git archive`), con el Python y las dependencias **de cada workflow** (bot-diario: 3.12 y su `requirements.txt`; padron-vivo e icg-mensual: 3.11 y su línea de `pip install`) y `CI=true`. Umbral: `bot-diario`, los tres scripts salen con código 0; `padron-vivo`, sale 0, 10 o 20 (nunca más de 20); `icg-mensual`, sale 0 y el chequeo de la serie pasa (≥ 296 filas, sin duplicados ni huecos). Si una fuente externa está caída se distingue «cae la fuente» de «falla el código» mirando el error, y se dice. El ensayo hace las mismas consultas de sólo lectura que el bot cada mañana y escribe **únicamente dentro de la copia** temporal, no en el repo.
7. **Lo que no se puede comprobar desde acá:** que corran en los servidores de GitHub. `gh` no tiene sesión en esta PC, así que **eso lo confirma Franco en *Actions*** (criterio de salida de A9 en el plan).

**Qué no se hace:** cambiar workflows; activar «Require a pull request» o «Require status checks»; tocar la protección de rama (la regla de d10 —bloquear sólo borrado y force-push— se configura en la interfaz de GitHub y es de Franco).

### A9 — bots (2026-09-30; pre-registro en `f384c08`, verificador en `b5490d2`)

**Pregunta:** ¿A6 y A7 rompieron a `bot-diario`, `padron-vivo` o `icg-mensual`? **Respuesta: no.** Medido contra los criterios pre-registrados con `python coordinacion/AUDITORIA-2026-09/verificar_bots.py` (resultado en `coordinacion/AUDITORIA-2026-09/resultados/verificar_bots.json`; se repite en E):

| criterio | resultado |
|---|---|
| 1. sin cambios | los tres `.yml` son **idénticos** al punto de partida (`git diff` vacío); `on:` con `schedule` y `workflow_dispatch`, **ningún `pull_request`**; `permissions` = `contents: write` + `issues: write` en los tres. No se tocó ningún workflow ni ningún permiso |
| 2. rutas | 13 rutas nombradas por los workflows (8 en `bot-diario`, 3 en `padron-vivo`, 2 en `icg-mensual`: scripts, `requirements`, lo que se commitea, lo que lee el paso `github-script` y los scripts que citan sus avisos a humanos): **todas existen y viajan por git; 0 de los 37 archivos eliminados o movidos** |
| 3. imports | clausura de imports locales: `bot-diario` 3 archivos (sólo stdlib, `pandas`, `requests`, `bs4`, `urllib3` y `tenacity` opcional dentro de un `try`), `padron-vivo` 5 (`vigilar_padron`, `ingesta_padron`, `bajar_nomina` y, vía `ingesta_padron`, `alias_legislador` y `entity_resolution` de `datos/canonica`), `icg-mensual` 1. **0 faltantes, 0 eliminados, 0 terceros sin instalar, y ningún archivo de las clausuras se editó desde el punto de partida** |
| 4. texto | ningún archivo de las clausuras ni de los workflows nombra un archivo eliminado o movido |
| 5. insumos y lectores | los 7 archivos que escriben los bots y los 3 que lee el padrón existen, viajan por git, y todos sus lectores según `.mapa/mapa.json` existen |
| prueba en negativo del verificador | simulando que se hubiera movido un script de entrada, un módulo importado, un módulo de `datos/canonica`, el CSV del ICG, la carpeta de datos del bot o el script que cita un aviso: **detecta los 6** |
| 6. ensayo | checkout limpio de `f384c08`; `bot-diario` con Python 3.12.8 y su `requirements.txt`, `padron-vivo` e `icg-mensual` con 3.11.0 y su línea de `pip install` (sin fijar, como en el workflow: pandas 3.0.6, requests 2.34.2…), `CI=true`. **`dae_senado` 0** (67 s, trajo el DAE 77/2026), **`tp_diputados` 0** (sin novedades, TP 144), **`votaciones` 0** (sin actas nuevas: 107 de Diputados y 218 del Senado en 2026), **`vigilar_padron --camara ambas` 0** («sin novedades»), **`ingesta_icg ultimo` 0** y el chequeo de la serie pasa («ICG OK: 297 meses, último 2026-07»). Contra una copia limpia, lo único que cambió es lo esperable: `dae_entradas.parquet`, `estado_bot.json` (DAE 74 → 77 y `ultima_revision`), `estado_vigilancia.json` y `vigilancia_padron.md` (más `raw/_nomina_diputados_fresca.csv`, un temporal que el workflow no commitea porque hace `git add` de rutas puntuales) |
| 7. corrida en GitHub | **falta: lo confirma Franco en *Actions*** (`gh` no tiene sesión en esta PC). El ensayo no la reemplaza: usa la red de la PC y no el runner |

**Dos hallazgos del ensayo, ninguno causado por A6/A7 (el código de los bots no cambió) y ninguno arreglado** (regla 9; ambos en `PENDIENTES-POST-AUDITORIA.md`):
1. **El ICG está estancado en 2026-07 y el bot no avisa.** La página de UTDT ya trae **agosto 2026 (2,06) y septiembre 2026 (1,94)**, pero el parser los saltea: los encabezados vienen como `Agosto &nbsp;2026` y la regex no atraviesa el `&nbsp;`. Comprobado corriendo el propio `scrapear_informes` sobre la misma página: tal cual, 27 informes y el último es 2026-07; con las entidades resueltas, 34 informes y llega a 2026-09. El paso «Verificar que la serie siga sana» no lo ve y la corrida termina verde diciendo «serie al día». **Importa para D6**, que usa esa serie. Arreglo probable de una línea más un test; se hace sólo si Franco escribe `CAMBIO DE ALCANCE:`.
2. **`dae_senado` no pudo traer los DAE 75 y 76/2026** («form y rutas fallaron») y el script avanzó el estado a 77, así que no los reintenta. No se investigó si es un hueco real de la fuente o de la ruta.

**Lo que falta para cerrar A9 (de Franco):** en *Actions*, correr a mano (*Run workflow*) los tres y ver que terminan en verde; `bot-diario` y `padron-vivo` **commitean a `main`** si hay novedades (esperable: el DAE 77 y el reporte del padrón), así que antes del próximo `git push` local hay que hacer `git pull --rebase`. Si además se configura la regla de `main` del §9.6 d10 (sólo *Restrict deletions* y *Block force pushes*), **no** marcar *Require a pull request* ni *Require status checks*.

**Cierre de A9 (2026-09-30, confirmado por Franco).** Franco corrió a mano los tres workflows en *Actions*: **los tres en verde**. La corrida de `padron-vivo` dejó el commit `998c8d8` («padrón vivo: limpio 2026-09-30»: sólo `estado_vigilancia.json` y `vigilancia_padron.md`), como se esperaba; `main` local se puso al día con `origin/main` por avance rápido (no había nada propio que perder). **Decisión de Franco sobre los dos hallazgos: «dejá esas mejoras para el final»** → siguen en `PENDIENTES-POST-AUDITORIA.md` y no se tocan durante la auditoría; **D6 tiene que declarar que la serie del ICG llega a 2026-07** (la página de UTDT ya trae hasta 2026-09).

### A10 — `CLAUDE.md` (2026-09-30; commit `edcc93e`)

**Criterios fijados antes de editar:** (1) fuera del bloque MODO AUDITORÍA, `CLAUDE.md` no nombra `TABLERO-CONTROL.html`, `tablero_datos.js`, `MAPA-MODELO`, `Nowcast-Puertas` ni «TABLERO DE CONTROL»; (2) el bloque MODO AUDITORÍA queda **idéntico byte a byte**; (3) el diff son sólo las piezas previstas; (4) `tests/test_rutas_citadas_existen.py` y `tests/test_rutas.py` verdes (el criterio del plan).

**Qué se sacó** (24.319 → 23.295 bytes; 1 línea cambiada y 6 borradas): (a) el ítem 7 del «Orden de lectura obligatorio» (`TABLERO-CONTROL.html`); (b) la sección entera «Regla del TABLERO DE CONTROL»; (c) la fila `TABLERO-CONTROL.html + tablero_datos.js` de la tabla del estado vivo; (d) en «Límites del entorno», el ejemplo `git <cmd> tablero_datos.js` pasó a `git <cmd> <archivo>` (el resto de la frase, igual). **No se tocó** `TABLERO.md` (el tablero de tareas) ni su regla de reclamar módulos: es otra cosa y el bloque MODO AUDITORÍA la suspende mientras dure.

**Medido:** (1) `grep` de esos nombres: **0 fuera del bloque** y 1 dentro (línea 9, «actualizar `tablero_datos.js`», en la lista de reglas que el bloque dice que prevalece sobre); (2) el script de edición compara el bloque antes y después y aborta si difiere: **idéntico**; (3) `git diff`: sólo esas cuatro piezas; (4) `test_rutas_citadas_existen` y `test_rutas`: **5 passed**; suite completa **54 passed**.

**Dos observaciones, ninguna abre trabajo:** (a) la mención de `tablero_datos.js` dentro del bloque MODO AUDITORÍA no se toca (el plan manda conservarlo y sólo Franco lo retira): desaparece con el bloque al cerrar la auditoría. (b) Los dos tests del criterio miran docstrings y comentarios de `.py`, **no `CLAUDE.md`**: no detectarían una cita rota en este archivo, así que la verificación de (1) es el `grep`.

### Salida de la fase A (2026-09-30, sobre `edcc93e`; comando y salida)

| criterio de salida del plan | evidencia |
|---|---|
| suite igual o mejor que la línea base | `python -m pytest tests/ datos/proyectos/tests -q` → **54 passed** (línea base, `00-linea-base.md` §7: 40 pasan y 1 falla, `test_insumos_del_motor_viajan`). Los scripts `test_*.py`: **58 de 58 en 0** (los 64 del inicio menos los 6 que movió A7), árbol de trabajo idéntico antes y después |
| `nowcast_puertas.py` corre | `python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 --origen EJECUTIVO` → exit 0, **P(APROBACIÓN) 61,3 %** (la salida de referencia que fija `test_panel_regresion`) |
| mayorías especiales devuelven sin número | `python modelo/ensemble/tests/test_mayorias_especiales_apagadas.py` → **191/191 OK**; con `--tipo-mayoria "Dos tercios"` la salida es «SIN NÚMERO — P(aprobación) sólo se estima para mayoría simple. Este proyecto pide DOS_TERCIOS…» |
| sólo los 6 fixtures HTML | `git ls-files "*.html"` → exactamente 6, todos en `tests/fixtures/` de `datos/bot_recoleccion` (2), `datos/seguimiento` (2) y `datos/senado` (2) |
| CI en verde, confirmado por Franco | confirmado por Franco en *Actions* en las entregas de A2 a A8 («todo verde») y los tres bots en A9. Lo posterior —documentos, `verificar_bots.py` (no es un test) y `CLAUDE.md`— se ve en *Actions* tras el próximo `git push` |

**La fase A está completa y Franco la dio por cerrada el 2026-09-30.** La conversación siguiente arranca de la fase B con el prompt de `PROMPT-NUEVA-CONVERSACION.md`. Lo estacionado que salió de ella (no se hace durante la auditoría): arreglo del parser del ICG (**D6 declara que la serie llega a 2026-07**) y los DAE 75 y 76; el arreglo de `rescate-taxonomias`; la decisión sobre `mapa_modelo_semantica.json` (ver `PENDIENTES-POST-AUDITORIA.md`).

### B1 — pre-registro (2026-09-30, escrito ANTES de escribir código y de medir)

**Estado de partida, verificado hoy:** `HEAD` `e2b097b`, `main`, `git status` limpio; `python -m pytest tests/ datos/proyectos/tests -q` → **54 pasan** (16 s). Coincide con lo que dice este archivo.

**Qué se construye** (todo dentro de `modelo/ensemble/`; ningún archivo existente del motor se toca):
1. `src/registro_parametros.py` — extrae el registro **desde el código** (AST) y lo compara con el guardado.
2. `outputs/registro_parametros.json` — el registro generado (viaja por git; JSON, no `.csv`/`.parquet`).
3. `tests/test_defaults_fijados.py` — la regla 8 hecha test, con su control positivo (regla 5).
4. *(etapa 2)* `src/perturbar_panel.py` — mide `afecta_panel` perturbando cada parámetro y corriendo el motor real.

**Versión elegida: AST + perturbación, en dos commits sucesivos.** La etapa 1 (AST + test) **cierra por sí sola el criterio de salida** («cambiar un default rompe un test»); la etapa 2 agrega `afecta_panel`. *Por qué no sólo AST:* (a) la clausura estática de imports desde `nowcast_puertas.py` es una **sobreaproximación** (22 archivos; medido: en una corrida real se cargan 14; `baseline_voto_individual`, `censo_estadisticos` y `agente_taxonomias` no se cargan) y de ≈ 140 candidatos sólo unos pocos mueven el número; sin `afecta_panel` el registro pone a ε₀ y τ en el mismo plano que `HTTP_TIMEOUT`; (b) la definición de «Afecta» del §5.3 **es** una perturbación, y de ella depende qué parámetros necesitan tipo E/M/P; (c) la fase D usa el registro para decidir qué re-estimar y en qué orden; (d) cuesta ≈ 20 min de cómputo **una vez**, fuera del CI. Si la etapa 2 resultara inviable, B1 queda cerrado con la etapa 1 y se dice.

**Qué es un «parámetro»** (definición operativa del §5.3), dentro de la **clausura** de archivos locales alcanzables por `import` desde `nowcast_puertas.py` (incluidos los imports dentro de funciones; sin tests, `Archivos_Borrar/` ni `coordinacion/archivo/`):
- **`entorno`**: toda lectura de variable de entorno (`os.environ.get`, `os.environ[...]`, `os.getenv`, `rutas._env`), con su **default efectivo** (la expresión evaluada con el entorno vacío; si no es evaluable —p. ej. una ruta— se guarda sólo el texto).
- **`constante`**: asignación de módulo con nombre en MAYÚSCULAS y valor literal (número, booleano, texto ≤ 120 caracteres, tupla/lista/conjunto/dict de literales); los textos que son rutas de datos van a `archivo_derivado`.
- **`default_funcion`**: default numérico de un argumento de función.
- **`archivo_derivado`**: toda referencia literal a un archivo de datos (`.parquet .csv .json .db .xlsx`) y todo nombre que el código importa de `rutas`; para los dos JSON de coeficientes estimados (`beta_dictamen.json`, `theta_sobre_tablas.json`) se fija además el **sha256** del contenido (con saltos de línea normalizados: el repo tiene `text=auto`).
- **Fuera del registro, declarado:** los números dentro del cuerpo de las funciones (constantes «mágicas» sin nombre) y los parámetros de los *generadores* de archivos derivados (p. ej. `MIN_VOTOS` de `disciplina.py`): de ellos queda el sha256 del archivo estimado, no el parámetro.

**Qué fija el test:** por parámetro, `(id, clase, entorno, default efectivo, texto de la expresión)`; que no aparezca ni desaparezca ninguno; el conjunto de referencias a archivos derivados; y el sha256 de los dos JSON. **Se ignoran** la línea (cambia con cualquier edición) y todo campo de medición (`afecta_panel`). Si el código difiere, el test dice qué parámetro, qué valor guardado, cuál hay, y el comando para regenerar.

**Criterios de la etapa 1 (umbral: 0 fallas en cada uno, fijados antes de mirar):**
1. **Idempotencia:** regenerar el registro desde `HEAD` dos veces da bytes idénticos, y coincide con el guardado.
2. **Cobertura y verdad:** están todos los términos que el informe nombra (`EPSILON0`, `TAU`, `EPSILON0_DEFAULT`, `TAU_DEFAULT`, `INCERTIDUMBRE_LEGISLADOR`, `RECORD_POR_TEMA`, `SHRINK_RECORD`, `K_SHRINK_RECORD`, `MIN_HIST_INDIVIDUAL`, `MIN_HIST_ANTERIOR`, `GUARD_ERA`, `ERA_FIJA`, `BETA_DICTAMEN`, `TEMA_AUTO`, `COMBINAR_TEMAS`, `SOBRE_TABLAS`, `DESVIO_MIN_INDIVIDUAL` —el piso 0,02—, `MIN_VOTOS_FICHA`, `DIAS_VENTANA_VIVA`); y para **todo** parámetro de clase `entorno` o `constante`, el valor efectivo del registro coincide con el atributo del módulo importado con el entorno limpio (**0 distintos**).
3. **Cambiar un default rompe el test** (control positivo, regla 5): sobre el código real, modificado en memoria, el test **detecta los 7**: (i) `TAU_DEFAULT` 1,19 → 1,2 (el ejemplo del plan); (ii) `EPSILON0_DEFAULT`; (iii) una bandera invertida (`GUARD_ERA`: `!= "0"` → `== "0"`); (iv) una constante borrada; (v) una constante nueva; (vi) un default numérico de función; (vii) una lectura de entorno nueva. Y **no** se rompe ante lo que no es un parámetro: cambiar un comentario o correr una línea. Una vez, además, se edita el archivo real (`TAU_DEFAULT = 1.2`), se corre el test, falla, y se revierte con `git checkout` (la evidencia del criterio del plan).
4. **Suite:** `pytest` sigue en 54; los scripts `test_*.py` pasan de 58 a 59, todos en 0; checkout limpio (`git archive`) con Python 3.11 y los pines: el test nuevo pasa ahí.
5. **El motor no cambia:** `git diff` de `modelo/ variables/ definiciones.py rutas.py` sin archivos existentes modificados (sólo archivos nuevos) y `test_panel_regresion` pasa (`max|ΔP| = 0`).

*Informativo, no decide:* el JSON lista los **nombres con varios defaults** (la trampa de la regla 8: `MIN_HIST_INDIVIDUAL` 1 contra 8, `epsilon0` 0,0 contra 0,035, `n_sims` 2000 contra 400, `reparto_desvio` 0,5 contra 1,0…).

**Etapa 2 — perturbación (qué y con qué umbral):**
- **Panel: 3 casos**, `n_sims = 2000`, `seed = 0`: **P1** Diputados, 2026-06-01, `EJECUTIVO`, hipotético (el panel de regresión); **P2** el mismo con `proyecto_id = HCDN279791` (ejercita las puertas A y C y β); **P3** Senado, 2019-06-01, `OPOSICION`, hipotético (otra cámara de origen y **otra era**: con el gobierno vigente el guard de era no se ve, `QUE-SE-MIDE.md` ya lo dice).
- **Alternativa de cada parámetro** (fijada ahora): booleano o bandera → el opuesto; número *x* → {2*x*, *x*/2} (los enteros con `//`; si 0 < *x* ≤ 1 el doble se acota a 1 y se descarta si iguala a *x*; si *x* = 0, la alternativa es 1 o 0,1); categóricos de entorno → una lista escrita a mano en el script (`COMBINAR_TEMAS`: `union`). Los contenedores y textos (tuplas, dicts, fechas, nombres) **no se perturban**: se marcan `no_perturbable` con el motivo. Los parámetros de módulos que **no se cargan** en el panel se marcan `afecta_panel = false, motivo = módulo no cargado`.
- **Procedimiento:** un proceso por perturbación (el módulo se importa con el literal **reescrito en el AST** antes de ejecutarse, o con la variable de entorno puesta), 6 a la vez; comparo **todos** los campos numéricos de la salida contra la corrida base.
- **Umbral:** *afecta* = `max|Δ| > 1e-9` en algún campo de algún caso con alguna alternativa (se guardan `afecta_p_aprobacion`, `afecta_campos`, el caso y la alternativa que lo mueve). Un proceso que falla se guarda como `error`, no como «no afecta».
- **Controles positivos** (mismo criterio escrito antes de correr): `TAU`, `EPSILON0`, `nowcast.n_sims` **afectan**; `GUARD_ERA` afecta **en P3 y no en P1 ni P2**; un parámetro que el llamador siempre pisa (`simular_con_guardas(epsilon0=…)`, default 0,0 contra el 0,035 que pasa `nowcast`) **no afecta**. Si algún control sale al revés, **la medición está mal** y no se publica hasta entenderlo.
- **Límite que se escribe en el registro:** `afecta_panel = false` quiere decir «no mueve estos 3 casos», no «no afecta nunca» (un umbral que el panel no cruza, o una rama de otro proyecto, no se ven).

**Qué B1 NO hace:** no asigna tipo E/M/P ni «medición que lo respalda» a cada parámetro (eso se anota en la fase D, donde se mide cada uno; el registro deja los campos para que D sepa cuáles anotar y el gate de E3 los exija); no agrega ni cambia ningún término, bandera o default; no toca ningún archivo existente del motor; no cambia el CI.

## Bitácora de alcance

Todo cambio de alcance se escribe **acá antes de ejecutarse**. Sólo Franco lo autoriza, con la frase `CAMBIO DE ALCANCE:`.

| fecha | qué cambió | quién lo pidió | qué se posterga a cambio |
|---|---|---|---|
| 2026-09-29 | Alcance inicial fijado (este documento) | Franco | — |
