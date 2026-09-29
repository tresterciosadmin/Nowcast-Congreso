# 00 — Línea base de la auditoría

**Fecha de la corrida:** 2026-09-28 19:39 → 2026-09-29 (la sesión se cortó por el límite de la API y se retomó) · **Auditor:** Claude (Sonnet 5.5; Opus como asesor) · **Modo:** sólo lectura y medición.

## 1. Sobre qué commit se audita

| | |
|---|---|
| **Commit auditado** | `bcc62b3` (merge de `main` con `origin/main`, 2026-09-28 19:37, hecho por Franco con un `pull` mientras empezaba la sesión) |
| **Motor y evaluación** | **idénticos a `6e6b629`** (ADR-0034, cierre de etapa): `git diff --name-only 6e6b629 bcc62b3` no toca `modelo/`, `variables/`, `evaluacion/`, `definiciones.py` ni `rutas.py`. Sólo trajo datos del bot: `tp_entradas.parquet`, `votaciones_nuevas.parquet`, `estado_bot.json`, vigilancia del padrón. [VERIFICADO] |
| **Rama de trabajo** | `auditoria-2026-09` (creada desde `bcc62b3`; los commits van sólo sobre `coordinacion/AUDITORIA-2026-09/`). No se tocó `main`. |
| **Árbol de trabajo** | Limpio salvo `coordinacion/PROMPT-AUDITORIA-INTEGRAL.md` **sin rastrear** (preexistente; Franco: "dejalo ahí, como excepción"). |
| **Raíz git** | **`Nowcast Congreso/`**, un nivel arriba de `Nowcast Congreso Argy/` (donde vive el proyecto). `.github/workflows/` y `.claude/worktrees/` están en la raíz git. El prompt decía `.github/workflows/tests.yml` sin ese prefijo. [VERIFICADO] |
| **`main` se mueve** | El bot empuja a diario (61 commits de `bot-recoleccion` sobre 243). Un `pull` en medio de una auditoría cambia el suelo. Por eso todo se ancla a un sha. |

## 2. Entorno

| | |
|---|---|
| Python / pandas / numpy / scipy / pytest | **3.14.3** / 3.0.2 / 2.4.4 / 1.18.1 / 9.0.2 — **el CI usa Python 3.11** (`tests.yml`). Un pandas 3 ya rompió una de mis pruebas (`groupby.apply` dejó de devolver las columnas de agrupación). |
| Banderas seteadas en el entorno de esta PC | **ninguna** de `RECORD_POR_TEMA`, `INCERTIDUMBRE_LEGISLADOR`, `BETA_DICTAMEN`, `GUARD_ERA`, `SHRINK_RECORD`, `TEMA_AUTO`, `SOBRE_TABLAS`, `QUORUM_ABSTENCIONES`, `MATCH_AUTOR_FUZZY`, `EPSILON0`, `TAU`, `N_SIMS`, `COMBINAR_TEMAS`, `MIN_VOTOS_FICHA`, `EMBUDO_FUENTE`, `CANON`, `OUT`… Las banderas se leen **al importar** (`nowcast_puertas.py:119-219`): lo que se mide es el default del código. [VERIFICADO con `env`] |
| Codificación | `PYTHONUTF8=1` (para imitar el Linux del CI; sin él, los `print` con acentos de algunos scripts fallan en cp1252) |
| CPU | 8 núcleos |

**Insumos del censo (sha256, primeros 16 hex):**

| archivo | sha256 | versionado |
|---|---|---|
| `datos/canonica/data/clean/votos_resuelto.parquet` | `ffea8e729eae0227` | sí |
| `datos/canonica/data/clean/actas_canonico.parquet` | `fda52f44d2f51240` | sí |
| `variables/proyecto/data/origen_por_acta.parquet` | `8296e9d97609bbaf` | sí |
| `variables/proyecto/data/tema_por_acta.parquet` | `7f5117bb3becb43b` | sí |
| `datos/expedientes/data/clean/acta_expediente_todas.parquet` | `cb2f7808804ae46b` | sí |
| `modelo/voto_individual/outputs/disciplina_individual.csv` (la ficha) | `9faf2392fbf725a9` | sí |
| `modelo/ensemble/outputs/beta_dictamen.json` (coeficientes de β en producción) | `4805acc3aad6b61a` | sí |
| `evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet` (37 MB) | `7ee19ed89396f92c` | **NO** |
| `evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet` (10 MB) | `bf45e8dc7bc64fc9` | **NO** |

## 3. Línea base de tests (replica el CI: `.github/workflows/tests.yml`)

| corrida | resultado |
|---|---|
| `python -m pytest tests/ datos/proyectos/tests -q` | **40 pasan, 1 FALLA** (23 s) |
| los 62 `test_*.py` restantes, uno por uno como scripts (incluye `test_historia_sin_fuga.py`, 14 chequeos, y `test_harness_es_el_motor.py`, 238/238) | **62/62 con código de salida 0** (el más lento, `test_incertidumbre_legislador.py`, 308 s; con el censo corriendo en paralelo) |
| `python verificar_regeneracion.py` | 15 OK · **1 a mirar**: "MAPA.md dentro del presupuesto de contexto" |
| `git status --porcelain` antes y después | **idéntico** (ninguna corrida escribió sobre archivos versionados) |

**El test que falla** — `tests/test_insumos_del_motor_viajan.py::test_los_insumos_del_motor_no_estan_ignorados`:
> estos datos los LEE el motor y git los IGNORA, o sea que viven en un solo disco: `evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet` — lo leen: `estimar_epsilon_tau.py`

Es la propia barandilla del repo diciendo que **el insumo del 0,1333 y de τ existe sólo en este disco**. El fallo lo introdujo ADR-0034 (`estimar_epsilon_tau.py` pasó a leer el censo por defecto). En un `checkout` limpio del CI, el mismo test falla: **el CI está en rojo en `HEAD` [INFERIDO]**. No pude verificarlo: `gh` no está autenticado en esta PC [NO VERIFICADO].

Las dos barandillas de ADR-0034 (`test_historia_sin_fuga.py`, `test_harness_es_el_motor.py`) **pasan**.

## 4. El worktree `.claude/worktrees/suspicious-lalande-8a89b7`

- Es un `git worktree` **registrado** (`git worktree list`), 175 MB, rama `claude/suspicious-lalande-8a89b7` en `c916e0e` (2026-09-15, antes de ADR-0025…0034): una copia **vieja** del motor. [VERIFICADO]
- Vive en `<raíz git>/.claude/worktrees/`, **fuera** de `Nowcast Congreso Argy/`, y está excluido con `.git/info/exclude`.
- **No infla nada**: `test_raiz_del_repo_una_sola_copia.py` recorre `RAIZ_PROYECTO.rglob("*.py")` con `RAIZ_PROYECTO = tests/..` (`tests/test_raiz_del_repo_una_sola_copia.py:30,40`), `.mapa/indexar.py` no baja a directorios que empiezan con punto (`indexar.py:619`) y pytest corre sobre `tests/` y `datos/proyectos/tests`. Los 194 `.py` y 44.316 líneas del prompt cuentan sólo el proyecto. [VERIFICADO]
- Sí es un riesgo latente: un motor de hace dos semanas ejecutable desde un directorio que un `find` desde la raíz git encuentra. Candidato a archivar (con OK de Franco).

## 5. Lo leído para la Fase 0.4

`URGENTE.md`, `ESTADO-REAL-DEL-MOTOR.md` (las 20 filas), ADR-0034 completo, `FORMULA-COMPLETA.md` §I.00 (líneas 102-128), §I.0, §IV.6-IV.7, las tablas "Constantes del motor" y "Parámetros estimados", `CLAUDE.md` completo. **Ninguno se dio por bueno**: cada afirmación de las fases siguientes se contrasta con código, `git` o una corrida.

## 6. Desvíos declarados respecto de `PROMPT-AUDITORIA-INTEGRAL.md`

El prompt manda; estos desvíos lo hacen ejecutable sin romper su propia regla de sólo lectura. Franco puede revertir cualquiera.

| # | Desvío | Por qué |
|---|---|---|
| 1 | Los commits van en la rama `auditoria-2026-09`, no en `main`; se agrega con `git add -- coordinacion/AUDITORIA-2026-09` | el bot empuja a `main` todos los días; hay un archivo sin rastrear en `coordinacion/` |
| 2 | La línea base corre **todo** `tests.yml`, no sólo `pytest tests/ datos/proyectos/tests` | son ~62 scripts más, y las dos barandillas de ADR-0034 están entre ellos |
| 3 | El censo se **regenera desde cero** en una copia limpia de `HEAD` (`git archive` a `Archivos_Borrar/repro/`), sin el parquet ignorado, y se compara contra el detalle en disco | `resumen_censo_limpio.py` y `medir_tau_limpio.py` escriben en rutas **versionadas** sin opción de cambiarlas (`baseline_voto_individual.json`, `censo_limpio_2026-09-28.json`, `tau_limpio_2026-09-28.json`); y "si el detalle está en disco, no lo corras" da re-aritmética, no reproducción |
| 4 | Se agregó un **pre-registro** (`00-preregistro.md`) de los criterios de refutación de H1-H5, escrito antes de los informes de ADR y de las mediciones | H1-H5 las redactó el mismo tipo de agente que audita |
| 5 | Se agregaron tres mediciones que el prompt no pedía: `control_independiente.py`, `invariancia_al_futuro.py`, `contraste_aprobacion.py` | verificación circular; y el paso P_i → P(aprobación) es el borde más importante y "nunca medido" |
| 6 | Veredicto nuevo **`VIGENTE-ESTRUCTURAL`** para ADR de reglamento/mecánica/proceso | los ADR de infraestructura no tienen "medición" |
| 7 | La tabla 34 → 5-7 admite **destino principal + referencias** por ADR | mandar 0032 (unidad = expediente) y 0033 a "línea cerrada" enterraba la regla central |
| 8 | Se declara que este prompt **prevalece sobre `CLAUDE.md`** en esta ronda: no se anotó en `ESTADO-DEL-PROYECTO.md`, `tablero_datos.js` ni `TABLERO.md`, y no se reclamó módulo | la regla de trazabilidad de `CLAUDE.md` contradice "no se toca ningún documento existente" |
| 9 | No se corrió nada que llame a la red ni a la API de LLM | hay 6 scripts en `variables/proyecto/src` que lo hacen (`agente_taxonomias.py`, etc.) |
| 10 | Los lotes de lectura de ADR se hicieron con subagentes (Sonnet; Opus para la cadena 0012→0016→0025); **el límite de la API cortó la primera tanda** y hubo que rehacerla | el prompt lo permite; queda registrado |

## 7. Cierre: los tests de la línea base, contra el final

Re-corrido el 2026-09-29 14:4x, con todo lo de la auditoría ya escrito:

| | al empezar | al terminar |
|---|---|---|
| `python -m pytest tests/ datos/proyectos/tests -q` | 40 pasan, 1 falla (`test_insumos_del_motor_viajan`) | **40 pasan, 1 falla (el mismo)** |
| `git status --porcelain` fuera de `coordinacion/AUDITORIA-2026-09/` | `?? coordinacion/PROMPT-AUDITORIA-INTEGRAL.md` (la excepción acordada) | **idéntico** |
| `git diff main..auditoria-2026-09` fuera de esa carpeta | — | **vacío** |

Lo que queda en disco y **no viaja por git** (`Archivos_Borrar/`, gitignored): `repro/` (copia de `HEAD` de ~180 MB con el censo regenerado), `auditoria/` (logs, parquets intermedios, fichas de trabajo). Lo puede borrar Franco a mano cuando quiera; nada de lo versionado depende de eso. Los tres archivos versionados que las mediciones reescribirían (`baseline_voto_individual.json`, `censo_limpio_2026-09-28.json`, `tau_limpio_2026-09-28.json`) se regeneraron **sólo en la copia** y se compararon: idénticos.

