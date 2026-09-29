# Auditoría lote A — ADR 0001, 0002, 0009-BORRADOR, 0009, 0010, 0011, 0014, 0019

Auditor: Claude (Sonnet 5.5), 29-09-2026, SOLO LECTURA. No corrí tests, censo ni scripts de medición. Sí ejecuté: `git` de lectura (`log`, `show`, `ls-files`, `check-ignore`, `branch`), `python .mapa/buscar.py --dato`, y tres one-liners de Python que sólo leen (abrir `mapa.json`, `actas_canonico.parquet`, `proyectos.db?mode=ro`, importar `rutas.py` para ver su inventario; simular a mano el filtro de `test_rutas.py`, sin correr el test).
Convención: **[V]** verificado (`archivo:línea` o comando) · **[I]** inferido · **[N]** no verificado. Rutas relativas a `Nowcast Congreso Argy/` salvo que diga `raíz git`.
"Valle" = quien firma como decisor en 0009/0010/0011/0014; los commits de esas fechas son de `ThiagoPP260` [I: coinciden fecha y ADR; no hay mapeo nombre↔autor escrito en ningún lado].
El resultado de `pytest tests/` en HEAD (41 tests: 40 OK, 1 falla) lo tomé de `Archivos_Borrar/auditoria/pytest.txt` (corrida del auditor principal), no lo corrí [V].

---

## 0. Respuestas directas a las cuatro atenciones especiales

### (i) ¿Queda otro ADR o documento con contenido que ya no vale y sigue en el árbol? — SÍ, varios, con el mismo patrón que el BORRADOR

El patrón es el de CLAUDE.md §"Archivos descartables" (copiar a `Archivos_Borrar/`, neutralizar, anotar en `PENDIENTES-DE-BORRAR.md`), y **falla en los dos pasos que dependen de `Archivos_Borrar/`**:

- `coordinacion/DECISIONES/0009-BORRADOR-…md` (16 líneas, versionado). Dice "Anotado en `Archivos_Borrar/PENDIENTES-DE-BORRAR.md`" (`0009-BORRADOR:16`): ese archivo **no existe** (`ls Archivos_Borrar/PENDIENTES-DE-BORRAR.md` → No such file) y no podría viajar: `.gitignore` ignora `Archivos_Borrar/*` [V]. `LIMPIEZA-2026-09-VEREDICTOS.md:256` ya lo decía ("archivo que no existía") [V]. El borrador completo (181 líneas) sí está en git: `git show fd2aa2b:"Nowcast Congreso Argy/coordinacion/DECISIONES/0009-BORRADOR-…md"`; la neutralización es `6782526` (mismo día, 20:49) [V]. Lleva 53 días "esperando que Valle lo borre".
- `coordinacion/CONECTAR-GIT.md` (26 líneas, versionado): "⛔ NO LEER — documento retirado (2026-08-06) … está esperando que Valle lo borre" y dice que la copia íntegra está en `Archivos_Borrar/BORRAR_coordinacion-CONECTAR-GIT.md` (`CONECTAR-GIT.md:4`): **no existe** (`ls Archivos_Borrar/BORRAR*` → vacío) [V]. Además la fila 2 de su tabla remite a "PROTOCOLO-GIT, sección final" para el chequeo de `check-ignore`, cuyo diagnóstico es el discutido en ADR-0011 (ver abajo).
- `coordinacion/_wtest`: 0 bytes, versionado desde 2026-06-27 (`git ls-files`, `git log` 0079baa) [V].
- Código neutralizado que sigue en el árbol: `modelo/ensemble/src/backtest_cadena.py` (550 LOC, NEUTRALIZADO 22-08 por ADR-0012, líneas 3/520/541) **y su test `modelo/ensemble/tests/test_backtest_cadena.py` (330 LOC) que el CI corre** (existe `log___modelo_ensemble_tests_test_backtest_cadena_py.txt`); `variables/proyecto/src/comparar_vias_icg.py` (298 LOC, "SUPERSEDED / NEUTRALIZADO 2026-08-11", línea 1); `modelo/ensemble/src/ensemble.py` (412 LOC: la formulación v1 "DADA DE BAJA", líneas 3/110/303/384-407, pero convive con lo vivo: `DESVIO_MIN_INDIVIDUAL` `:361`) [V].
- Documentos vivos con premisas caídas: ver (b) abajo (`datos/proyectos/README.md:58`, `MAPA.md:65,181`, `tests.yml:26`, `tablero_datos.js:213`, `PLAN-DE-TRABAJO.md:132`, `casos/README.md:21,28-29`, `PROTOCOLO-GIT.md:84-86`, `.gitignore:143`, `COMMITEAR*.ps1`).
- Otros ADR: fuera de mi lote sólo levanté por grep; en mi lote el único ADR con contenido ya inválido es el BORRADOR. Para los demás ver lotes B–E (0029 ya marcado INACTIVO en `adr_lote_E.md`).

### (ii) Para cada ADR de infraestructura: ¿la regla HOY se cumple? (test/comando concreto)

Estado de los cinco tests leídos (HEAD, según `pytest.txt`): pasan 4 de 5 archivos; falla `test_insumos_del_motor_viajan::test_los_insumos_del_motor_no_estan_ignorados`.

| Test | Qué controla | Puede fallar de verdad? | Cubre a |
|---|---|---|---|
| `tests/test_rutas.py::test_lo_declarado_existe` (`:57-70`) | lo declarado como no-generado existe en disco | sí | ADR-0010 (mitad) |
| `tests/test_rutas.py::test_el_codigo_no_usa_rutas_entre_modulos_sin_declarar` (`:73-100`) | "toda ruta entre módulos armada a mano está en `rutas.py`" | **NO: es vacuo** [V] | ADR-0010 (la mitad que "importa") |
| `tests/test_definiciones_compartidas.py` (448 líneas, ≈12 tests) | copias por valor + **identidad de objeto** (`:268-304`) + ventanas de gobierno vs literales viejas (`:307-388`) + ICG no unificado (`:391-412`) + `periodo` de bloque distinto (`:417-448`) | sí (identidad) | ADR-0014 y ADR-0019 |
| `tests/test_bases_viajan.py` (4 tests) | `.db` no ignoradas, journals sí, nada ≥95 MiB, no volvió `*.db` al `.gitignore` | sí | ADR-0020 (fuera de lote); toca ADR-0011 |
| `tests/test_rutas_citadas_existen.py` (2 tests) | rutas citadas en docstrings de `.py` existen | sí (con control `test_el_detector_mira_algo`) | ADR-0010 (higiene) |
| `tests/test_insumos_del_motor_viajan.py` (3 tests) | insumos del MOTOR (derivados de `mapa.json`) no están ignorados | sí — **falla hoy** | doctrina de `.gitignore` / ADR-0001 regla 5 |

**Hallazgo grave: `test_el_codigo_no_usa_rutas_entre_modulos_sin_declarar` no puede fallar.** [V]
- `declaradas = {r.resolve() for r in rutas.inventario().values()}` (`test_rutas.py:75`) y `inventario()` devuelve TODA global en mayúsculas que sea `Path` (`rutas.py:194-197`), incluidas `RAIZ` y `RAIZ_GIT` (`rutas.py:57-58`). La guarda `p in declaradas or any(d in p.parents for d in declaradas)` (`test_rutas.py:89`) es siempre verdadera porque `RAIZ` es ancestro de cualquier ruta del proyecto.
- Lo ejecuté a mano (sólo el filtro, sin correr el test): una ruta inventada `datos/senado/data/clean/ruta_que_nadie_declaro.parquet` pasa el filtro; ancestros "declarados": `.`, `Nowcast Congreso Argy`, `datos/senado/data`.
- Quitando sólo el escape `RAIZ`/`RAIZ_GIT`, con el regex del propio test hay **14 rutas huérfanas en 18 archivos**, entre ellas del camino del número: `modelo/ensemble/src/nowcast_puertas.py:267` (`RAIZ / "variables" / "bloque" / "src"`), `:641` (agregador), `puerta_a.py:150`/`puerta_d.py:107` → `datos/expedientes/src`, `datos/taxonomias/src/registro.py` → `datos/proyectos/data/taxonomias.csv` (dato real no declarado). Con el alias `REPO` (que ADR-0021 estandarizó: `from rutas import RAIZ as REPO`) y que el regex no incluye (`test_rutas.py:43-45`): 17 rutas en 45 archivos.
- El vacío viene desde el primer commit (`4f87cd9`, 2026-08-20: `rutas.py:57` y `test_rutas.py:89` ya estaban así) [V `git show`]. La afirmación "hoy da 0 huérfanas, o sea el inventario está completo" (`ESTADO-DEL-PROYECTO.md:1475`; ADR-0010:61-62) no tuvo control positivo.

**Hallazgo sobre ADR-0011 y los tests: los tres tests que consultan git usan exactamente lo que el ADR prohíbe.** [V]
- ADR-0011:78-83 "se prohíbe leer el código de salida de `check-ignore` como ignorado sí/no". `tests/test_bases_viajan.py:92` y `:109`, y `tests/test_insumos_del_motor_viajan.py:111` hacen `_git("check-ignore", "-q", ruta).returncode == 0` ⇒ ignorado. También `.gitignore:143` sigue instruyendo `git check-ignore -q <archivo> && echo IGNORADO`, y `producto/dashboard/README.md:145`.
- **La premisa de 0011 no se reproduce con `-q`.** Con git 2.53.0.windows.3 (esta PC): `git check-ignore -q --no-index datos/padron/data/padron_diputados_historico.csv` → rc=1 (correcto: viaja); `git check-ignore -v --no-index …` → rc=0 e imprime `.gitignore:164:!datos/padron/…`. O sea que el código 0 con una excepción `!` es propio de **`-v`**, no de `-q`. La transcripción del propio ADR (`0011:20-22`) es de `-v`. El falso positivo que observó Valle se explica mejor por el **segundo error** del ADR (prefijo `"Nowcast Congreso Argy/"` desde adentro): reproducido, `git check-ignore -q "Nowcast Congreso Argy/datos/padron/data/padron_diputados_historico.csv"` → rc=0 con regla `*.csv` (`.gitignore:5`) [V]. Que Valle usara otra versión de git: [N].
- Los tests, entonces, están semánticamente bien (para un archivo no trackeado `-q` rc=0 ⇒ ignorado; rc=1 ⇒ no) pero contradicen la letra del ADR. Hay además una ceguera que el ADR no menciona: `check-ignore` **saltea archivos trackeados** salvo `--no-index` (`datos/padron/data/gobernadores.csv` está trackeado y coincide con `*.csv`: rc=1 sin `--no-index`, rc=0 con él; `git ls-files -ci --exclude-standard` lo lista, único caso) [V]. Para "¿viaja?" es la respuesta correcta (trackeado = viaja), pero explica por qué `-q` no sirve para auditar lo existente.
- La falla actual de `test_insumos_del_motor_viajan` es genuina, no un falso positivo: `evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet` (36,9 MB, no trackeado, `git check-ignore -v` → `.gitignore:4:*.parquet`) lo lee `modelo/ensemble/src/estimar_epsilon_tau.py:150` (estimador de ε₀ y τ, prendidos en producción). Un clon no puede re-estimar τ sin re-correr el censo [V]. Si CI corre `tests/` en checkout limpio (`tests.yml:60`) el test falla igual (el archivo ausente también matchea `*.parquet`) [I].

**Cumplimiento por ADR** (detalle en las fichas): 0001 regla 5 ("datos fuera de git") FALSA hoy; 0001 regla 2 ("una rama") sin uso; 0002 punto 3 (el bot agrega a la canónica) FALSO en la letra; 0009 se cumple y tiene test propio que corre en CI (`tests.yml:60`); 0010 se cumple a medias (MAPA sí, hook no, test de rutas vacuo); 0011 diagnóstico parcialmente no reproducible; 0014 y 0019 se cumplen con test real (identidad).

### (iii) ¿Lo que dicen los ADR sobre `definiciones.py` y `rutas.py` coincide con esos archivos hoy?

**`definiciones.py` (260 líneas) vs ADR-0014/0019:**
- ✔ `periodo_parlamentario` (`:93-122`, con el `.astype("float64")` que arregla pyarrow, `:111-115`), `normalizar_mayoria`/`_valor` (`:192-215`), `BANCAS` (`:89`), `GOBIERNOS` de 4 ventanas (`:149-154`), `gobierno_por_fecha`, `era_de` (`:158-185`).
- ✔ Los cinco módulos de 0014 re-exportan: `datos/export/src/export_base.py:49-51`, `modelo/voto_individual/src/disciplina.py:67-69`, `modelo/agregador_institucional/src/agregador.py:60-61`, `variables/asistencia_quorum/src/asistencia.py:46`, `variables/legislador/src/ficha.py:40`. ✔ Los tres de 0019: `variables/bloque/src/bloque.py:363`, `origen_lider.py:63`, `origen_por_acta.py:71`; y el cuarto, el guard de era: `modelo/ensemble/src/nowcast_puertas.py:275-290` (`era_de` → `definiciones.era_de`).
- ✘ `MAYORIAS` (`:79`, `:189`) no lo importa ningún módulo (grep en `*.py`: sólo `definiciones.py`). Viola la regla 2 del propio archivo ("nada se agrega sin al menos DOS módulos", `:60-61`).
- ✘ `BANCAS` sigue copiada: `modelo/ensemble/src/estimar_beta_dictamen.py:88` (**en el motor**, posterior a 0014), `datos/padron/src/padron_vigente.py:76` y `vigilar_padron.py:104` (mismo dict `{"diputados": 257, "senado": 72}`), `padron_diputados_historico.py:89` (=257), `padron_senado_historico.py:84` (=72). 0014:54 sólo anotaba las dos escalares de `datos/padron`. El test de identidad (`:284-304`) no cubre `BANCAS`/`MIEMBROS` (`test_constantes_compartidas` `:224-248` compara valor, no identidad).
- ✘ `__all__` (`:74-84`) omite `CARACTERES_DICTAMEN`/`caracter_de_dictamen` (`:221-260`, ADR-0021). El docstring (`:68`) sólo cita ADR-0014; no menciona 0019 ni 0021.
- `MARGEN_DISPUTADA`, `CONDUCTAS`, `PRESENTE_VOTOS/PRESENTES` siguen duplicadas y vigiladas sólo por valor (`test_definiciones_compartidas.py:224-263`); 0014 no las unifica (coherente con su criterio).

**`rutas.py` (209 líneas) vs ADR-0010:**
- ✔ Existe en la raíz; idioma de import sin `parents[N]` (`:28-32`); `GENERADOS`/`SOLO_EN_RAIZ_GIT` (`:170-191`); respeta env `CANON`, `EXP_CLEAN`, `PROYECTOS_DB`, `SCHEMAS` (`_env` en `:70,75,94,148`).
- ✘ "52 constantes": hoy `inventario()` devuelve **59** (`import rutas; len(inventario())`) [V].
- ✘ "migró sólo dos módulos" (0010:83): hoy 40 archivos lo importan (`grep "from rutas import"`), casi todos `RAIZ` (ADR-0021). Pero quedan **51 `parents[3]` en 51 archivos** (ADR: ~45 en 41) y **229 `sys.path.insert` en 146 archivos** (ADR: 63 en 114). Ejemplos que siguen a mano: `variables/embudo/src/embudo.py:618-629`, `datos/proyectos/src/upsert_bot.py:45-48`, `cuarentena.py:39-40`. `upsert_bot.py:48` y `cuarentena.py:40` ignoran la env `PROYECTOS_DB` que `rutas.PROYECTOS_DB` sí respeta.
- ✘ Docstring `rutas.py:34-35` dice que "siguen mandando `CANON`, `CLEAN`, `EXP_CLEAN`, `PROYECTOS_DB`, `OUT`": sólo cuatro pasan por `_env`, y no son `CLEAN` ni `OUT`. (0010:52-53 dice "`CANON`, `EXP_CLEAN`, `OUT`…".)
- ✘ `test_rutas.py` no cubre el alias `REPO` ni tiene filtro válido (ver (ii)).

### (iv) ADR-0010: el MAPA y su hook

**Qué dice el ADR** (`0010:38-39`): "Un hook `pre-commit` lo reindexa y avisa —sin bloquear— si algún README quedó vencido"; consecuencia "orientarse cuesta 246 líneas de MAPA.md" (`:74`).

**Qué hay:**
1. **Hook NO instalado en esta PC.** `ls ../.git/hooks` → sólo `*.sample`; `git config core.hooksPath` vacío [V]. `.mapa/hook-pre-commit` e `instalar-hook.{ps1,sh}` están versionados; los hooks no viajan. `ESTADO-DEL-PROYECTO.md:1478` lo dio por instalado "en la PC de Valle (2026-08-20)"; `TABLERO.md:318` lo dejó "Pendiente de Valle: correr instalar-hook.sh". Los 107 commits de septiembre son de `Franco Marconi` (`git log --format=%an`), o sea sin hook [V/I]. `CLAUDE.md:29-31` y `README.md:31` lo describen como automático (CLAUDE.md agrega "si no está instalado…").
2. **El MAPA igual está fresco**, pero por ritual manual, no por el hook: generado 2026-09-28 21:51 UTC, 195 archivos, 48.199 LOC (`MAPA.md:5`), commiteado en `6e6b629`; `REGENERAR.ps1:293` corre `.mapa\indexar.py` en el paso 8 [V].
3. **Presupuesto excedido**: `MAPA.md` tiene 471 líneas (`wc -l`; `verificar_regeneracion.txt`: "472 líneas (presupuesto 460)") contra `MAX_LINEAS_MAPA = 460` (`.mapa/indexar.py:83`). El presupuesto original era 260; Franco lo subió a 460 el 08-09 "al agregar el inventario de datos" (`:84-88`). El "246 líneas" del ADR quedó obsoleto: hoy son casi el doble [V].
4. **El inventario de datos del MAPA dice algo falso sobre "viaja".** `MAPA.md:181`: "181 archivos de datos · 354.5 MB · 181 viajan por git, **0 no**". Real: **43 archivos, 196,0 MB, están ignorados por git** (calculado con la misma lista de `mapa.json` y `git check-ignore --stdin` con entrada en bytes) [V]. Causa reproducida: `.mapa/indexar.py:646-659` manda `input="\n".join(rutas)` con `text=True`; en Windows Python traduce `\n`→`\r\n`, git recibe `ruta\r`, contesta `"ruta\r"` entre comillas y `ruta not in ignorados` nunca da verdadero ⇒ `viaja=True` para todo. `mapa.json`: `viaja:true` en 181/181, incluido `censo_detalle_2026-09-28.parquet`, ignorado por `.gitignore:4`. Consecuencia: la línea "No viajan por git y pesan" (`indexar.py:1040-1048`) no sale nunca, y `buscar.py --dato` muestra `git:si` para archivos que no viajan. También `MAPA.md:65` (`rehacer proyectos.db (no viaja a git…)`, copiado de `datos/proyectos/README.md:58`) contradice a `git ls-files` (proyectos.db está trackeado).
5. `verificar_regeneracion.py` marca sólo "MAPA.md dentro del presupuesto" a mirar (check 7); su exit code es 0 (`verificar_regeneracion.txt`, `rc=0`): un aviso, no una barrera.
6. El inventario atribuye lectores por regex y se pierde `variables/embudo/src/embudo.py:626-629` como lector de `proyectos.db` (`mapa.json` lista 4 lectores, sin embudo) [V]; ese inventario es la base de `test_insumos_del_motor_viajan`.

---

## 1. Fichas

### ADR-0001 — Estructura del repo para trabajo en paralelo (2026-06-25)
1. `0001` · 2026-06-25 · monorepo modular; un módulo/un dueño/una rama; contratos en `docs/schemas/`; ESTADO obligatorio; datos fuera de git.
2. **Quién decidió:** no consta. El ADR no tiene campo "Quién" (`0001:3` sólo "Fecha · Estado: Aceptada"). Commit `ddde5d3` de Franco Marconi, mensaje "25/6" [V].
3. **Declarado:** "Aceptada". **Real:** reglas 1, 3, 4 vigentes; regla 2 ("una rama") sin uso; regla 5 falsa. Evidencia:
   - Regla 1: `ls` muestra `datos/ variables/ modelo/ evaluacion/ producto/ docs/ coordinacion/` más `casos/`, `fase0/`, `tests/`, `.mapa/` que el ADR no lista [V].
   - Regla 2: en la historia no hay una sola fusión de rama de feature (`git log --merges` sólo trae 12 "Merge branch 'main' of …"); `git branch -a` sólo tiene `main` y las de auditoría; 107 commits de septiembre en `main` de un único autor; el bot empuja a `main` (`bot-diario.yml`, paso "Commit si hay novedades": `git push origin main`) [V]. El claim en `TABLERO.md` sí sigue vivo (`TABLERO.md:9-14`, "Claude (sesión delegada por Franco)") [V].
   - Regla 2b ("consumí su salida, no su código"): 31 archivos / 54 líneas hacen `sys.path.insert/append` hacia el `src` de otro módulo, incluido el camino del número: `nowcast_puertas.py:267` (bloque) y `:641` (agregador); el harness importa el motor por diseño (ADR-0034, `test_harness_es_el_motor.py:33-35`) [V].
   - Regla 3: `docs/schemas/` existe (`acta.schema.json`, `voto.schema.json`) [V]; pero `rutas.py`, `definiciones.py` y `tests/` son hoy puntos compartidos que el ADR no nombra (los crearon 0010/0014).
   - Regla 4: ningún test ni CI lo exige (`tests.yml` no lo chequea) [V]; el resultado es `ESTADO-DEL-PROYECTO.md` de 650.621 bytes, que `CLAUDE.md` y este mismo encargo mandan no abrir entero [V].
   - Regla 5: `git ls-files` → 23 archivos bajo `data/clean/`, 1 bajo `data/raw/`, 30 `.parquet` y 2 `.db` versionados; `.gitignore` tiene 58 líneas `!` (51 de datos). La regla efectiva es otra: "si la salida de un módulo es insumo de otro, viaja" (`.gitignore` bloque 2026-08-06) + ADR-0020 [V].
4. **Medición:** ninguna (decisión de diseño; no hay script).
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** Sí como marco; test que lo cubre: ninguno para las reglas 2 y 4; `test_insumos_del_motor_viajan.py` vigila la doctrina que reemplazó a la regla 5 (y hoy falla, ver (ii)).
7. **¿Doc coincide?** `PROTOCOLO-GIT.md:31-32` repite la regla 5 ("Los datos se regeneran…; no se suben al repo") — falso hoy. `CLAUDE.md` coincide con reglas 1-4 y la regla 2 de "módulo/dueño/rama" tiene su bloque propio.
8. **VEREDICTO: VIGENTE-ESTRUCTURAL** (con la regla 5 derogada de hecho: hay que reescribirla, no citarla).
9. **DESTINO: 1.** Sobrevive: un módulo = una unidad con contrato de salida; cambiar un contrato compartido exige ADR + aviso; ESTADO al día. Se pierde: "datos fuera de git" (sustituir por la doctrina "insumo de otro módulo viaja" + límite de 100 MB) y "una rama por módulo" (no se practica).

### ADR-0002 — Semilla → canónica propia → bot incremental (2026-06-25)
1. `0002` · 2026-06-25 · Andy Tow como semilla de un solo uso; `datos/canonica` como fuente de verdad; bot; R sólo para el export.
2. **Quién decidió:** "Decisión del equipo" (`0002:6`), anónima. Commit `0079baa` de Franco Marconi 2026-06-27 [V].
3. **Declarado:** "Aceptada". **Real:** puntos 1, 2 y 4 vigentes; punto 3 falso en la letra; tabla de cobertura desactualizada.
   - Punto 1/4: `datos/decada_votada/export_seed.R` es el único `.R` del repo (`find -name "*.R"`); el pipeline no lo usa: `datos/canonica/src/run_pipeline.py:26-32` descomprime `DecadaVotadaCSV.zip` (1 archivo trackeado en `Aportes sobre dataset congreso/`) y corre `from_csv.py` (Python) [V]. Semilla estática, no dependencia "en vivo" ✔.
   - Punto 2: `actas_canonico.parquet` (5.998 actas), `votos_canonico.parquet` (959.815 votos), `votos_resuelto.parquet` trackeados (`git ls-files`) [V].
   - **Punto 3 falso:** "el bot… las agrega a la canónica" (`0002:11`). Hoy el bot escribe `votaciones_nuevas.parquet` (`datos/bot_recoleccion/src/votaciones.py:26,62`) y **no reconstruye la canónica**: "el bot DETECTA actas nuevas; la canónica NO se reconstruye sola… abre un issue" (`.github/workflows/bot-diario.yml:115-119`, raíz git). Nadie en el código lee `votaciones_nuevas.parquet` salvo el workflow (grep `*.py|*.ps1|*.yml`) [V]. El bot sí corre a diario (61 commits de `bot-recoleccion`, último 2026-09-28) [V]. Lo último que trae la canónica: Diputados hasta 2026-09-09, Senado hasta 2026-08-27 [V].
   - **Cobertura:** el hueco Senado 2014-2023 **está cerrado** (fuente `senado`: 749 actas 2015-02-12→2023-09-28; `decada_votada` Senado llega a 2014-11-19) [V]. Hueco que la tabla **no declara**: Diputados 2020-2023 tiene 25 actas (7+1+9+8) y 6.421 votos, contra 24.619-40.076 votos/año en 2017-2019 y 27.499-45.489 en 2024-2026 [V: `actas_canonico`, `votos_canonico`]. Sólo lo reconoce `datos/canonica/README.md:24`. Es la ventana AF del calendario de ADR-0019 (2019-12-10→2023-12-10): en Diputados casi no hay historia de esa era.
   - Cuerpo internamente flojo: "desde 1998" (`0002:6`) vs "Combinado ~2001–2025" (`:17`); la fuente más vieja en la canónica para Diputados es 1994-06-10 (argentinadatos), y `decada_votada` en la canónica arranca 2001-05-03 [V].
4. **Medición:** ninguna (recuento de cobertura; no hay skill).
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** Sí (puntos 1, 2, 4). Test: no hay uno para la estrategia; `datos/canonica/tests/*` cubren entity resolution/alias/gemelas [V listado].
7. **¿Doc coincide?** `CLAUDE.md` §"Estrategia de datos" coincide con 1-4 (copia la letra del punto 3, con la misma imprecisión); `bot-diario.yml:115-119` la contradice.
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 1.** Sobrevive: semilla estática → canónica propia como fuente de verdad → bot que detecta (la reconstrucción es decisión humana, con issue automático) → R sólo para el export. Se pierde: "el bot agrega a la canónica" y la tabla de cobertura (hay que reescribirla con el hueco Diputados 2020-23).

### ADR-0009-BORRADOR — Entrega del bot: dónde aterrizan los proyectos (2026-08-07)
1. `0009-BORRADOR` · 2026-08-07 · borrador de dos opciones, hoy neutralizado (16 líneas).
2. **Quién decidió:** el texto vigente dice "Ya eligió: Opción B" (`:4`, Valle). El borrador original: "Decisor: Valle · Registra: Claude · Estado: BORRADOR — esperando la decisión de Valle" (`git show fd2aa2b:…`, líneas 3-4) [V].
3. **Declarado:** "⛔ NEUTRALIZADO — no leer" (`:1`). **Real:** es exactamente eso, pero no está borrado: sigue versionado 53 días después; su promesa de anotación en `PENDIENTES-DE-BORRAR.md` es falsa (ver (i)).
4. **Medición:** en su versión original, la tabla de "números medidos en disco hoy" (112.793 filas hasta 2026-06-02, etc.) [V `git show fd2aa2b`]; no se conserva.
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** No; nada lo ejecuta ni lo referencia salvo `0009:6` ("ya neutralizado").
7. **¿Doc coincide?** Sí con 0009; `0009:6` lo cita.
8. **VEREDICTO: SUPERSEDIDO** (por ADR-0009 `proyectos-db-fuente-de-verdad…`, que dice "Reemplaza: el borrador…").
9. **DESTINO: DESCARTABLE.** No aporta regla viva; el razonamiento de las dos opciones, si alguien lo quiere, está en `git show fd2aa2b:…`. Un ADR con número duplicado (dos "0009") es el modo de falla que el propio texto denuncia.

### ADR-0009 — `proyectos.db` es la fuente de verdad de los proyectos (2026-08-07)
1. `0009` · 2026-08-07 · Opción B directa: `proyectos.db` recibe CKAN + bot (con el Senado), `variables/embudo` lee de ahí; un merge con precedencia por campo (no dos upserts); cuarentena aparte; frenar sólo por invariante rota o >5% con piso de 10 filas.
2. **Quién decidió:** "**Decisor:** Valle · **Registra:** Claude" (`0009:4`); "razón explícita de Valle" (`:17-18`); cuarentena: "decisión de Valle" (`:201-204`), con cita textual de Valle (`:180-184`) [V]. Commit `6782526` de ThiagoPP260.
3. **Declarado:** "ACEPTADO (vigente)". **Real:** implementado y operativo; pero **no alimenta el número publicado**.
   - Implementación [V]: `datos/proyectos/src/migrar_ckan.py` (backfill), `upsert_bot.py:207-280` (merge: autores del bot; giros sólo para proyectos que CKAN no conoce; `n_giros_inicial` del bot), `cuarentena.py:44,51` (`TASA_MAXIMA=0.05`, `MINIMO_ABSOLUTO=10`), `verificar.py:178-199` (invoca `cohorte_dos_rutas.py` como proceso), `embudo.py:626-629,708-714` (fuente `auto`: SQLite si existe, parquet si `EMBUDO_FUENTE=parquet` o no hay db). `store.py` sin tocar (mtime 30-06) ✔.
   - Datos hoy [V, lectura `mode=ro`]: 115.495 proyectos (112.427 D + 3.068 S), 1.130 con `proyecto_id` nulo (altas sólo-bot), `max(fecha_ingreso)=2026-09-09`; `cuarentena.db` con 0 filas; `proyectos.db` 87,3 MiB (límite de FALLA del test 95 MiB, `test_bases_viajan.py:40`), última modificación 2026-09-16 (`b2ad65f`). Se rehace sólo con `REGENERAR.ps1 -ConExpedientes` (apagado por defecto, `REGENERAR.ps1:24-37,180-193`); ni el bot ni CI llaman a `upsert_bot.py` (grep en workflows: sin coincidencias) [V].
   - **No entra al número:** "El embudo… del que cuelga todo el nowcast" (`0009:114-115`) dejó de ser cierto el 22-08 con ADR-0012: `ensemble.py:302-303` (`_p_llega_de_embudo` "DADA DE BAJA"), `nowcast_puertas.py` no lee `proyectos.db` ni `p_embudo` (grep en `modelo/ensemble/src` y `casos`: sólo `ensemble.py`), y `REGENERAR.ps1:183-185` lo dice: "solo variables/embudo lo lee, y hoy no alimenta el numero publicado, ADR-0012". Sí lo leen `verificar.py`, `variables/proyecto/src/tema_por_proyecto.py`, `prueba3_cobertura_universo_vivo.py` (inventario `.mapa/buscar.py --dato proyectos.db`) [V].
4. **Medición que lo justifica:** prueba de equivalencia de rutas: cohorte idéntica celda por celda (41.470 filas × 13 columnas, 0 diferencias) y skill del embudo 0,3643 (`sancionado`) y 0,4195 (`llega_recinto`) iguales en parquet y SQLite (`0009:87-98`), producida con `variables/embudo/src/embudo.py` + `cohorte_dos_rutas.py`. No re-medí (no corrí nada) [N: los números; V: que los scripts existen].
5. **¿Fuga/espejo?** No aplica: es una prueba de equivalencia de datos entre dos rutas de lectura del embudo; no toca el récord del legislador.
6. **¿Vigente?** Sí (mecánica de datos). Test: `datos/proyectos/tests/test_verificar.py` (5 tests "agarra…" + cuarentena/avalancha/piso `:102-172`) corre en CI (`tests.yml:60`). El control de equivalencia no forma parte de `REGENERAR.ps1` (no invoca `verificar.py` ni el embudo) [V].
7. **¿Doc coincide?** No en cuatro puntos:
   - `upsert_bot.py:14-15` (docstring) sigue diciendo "firmantes, giros → gana el BOT"; el código y la Corrección 1 del ADR dicen lo contrario (`upsert_bot.py:232-245`).
   - `0009:57-59` ("una ficha por denominador… `upsert_proyecto` una sola vez") y `migrar_ckan.py:11-12` ("la capa de merge con `upsert_proyecto` se usa en la etapa 2") no coinciden con `upsert_bot.py`, que hace SQL directo y no llama a `upsert_proyecto` (grep: 0 usos fuera de `store.py`) [V].
   - `0009:210` "excepción explícita en el `.gitignore`" para `cuarentena.db`; hoy viaja "por regla" (`.gitignore:64`, tras ADR-0020) [V].
   - `tablero_datos.js:213` ("NO viaja a git (89 MB)"), `datos/proyectos/README.md:58`, `MAPA.md:65`, `tests.yml:26-27` y `PLAN-DE-TRABAJO.md:132` dicen que `proyectos.db` no viaja: falso (`git ls-files` la lista) [V]. `tablero_datos.js:213` y `ESTADO-DEL-PROYECTO.md:35` traen "114.708 proyectos" (hoy 115.495).
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 1** (datos y definiciones). Sobrevive: una sola base de proyectos con clave `denominador`; **merge por campo, nunca dos upserts sucesivos**; giro acumulado (CKAN) ≠ giro al ingresar (`n_giros_inicial`, bot); lo dudoso va a `cuarentena.db`, la carga sólo frena por invariante rota o >5% con piso de 10; antes de apagar la ruta vieja, las dos dan lo mismo. Se pierde: la premisa "el embudo alimenta el nowcast" y "el modelo está ciego a lo presentado después del 02-06" (el número no lo lee).

### ADR-0010 — MAPA del repo, router en los README y `rutas.py` (2026-08-20)
1. `0010` · 2026-08-20 · `MAPA.md` generado + hook; router en README (no `BITACORA.md`); `rutas.py`; dos tests en `tests/`; se rompe el ciclo `datos/proyectos`↔`variables/embudo`.
2. **Quién decidió:** "Quién: Claude (con Valle)" (`0010:3`); "Auditoría de la estructura… pedida por Valle" (`:7`). Diseño de Claude en una sesión pedida por Valle; commit `4f87cd9` de ThiagoPP260 [V]. Decisión explícita de Valle sobre cada punto: no consta [N].
3. **Declarado:** "Aceptada". **Real:** ver (iii) y (iv): MAPA sí; hook no (esta PC); `rutas.py` sí (migración avanzó); test de completitud vacuo; ciclo roto ✔ (`verificar.py:178-199`; `datos/` no importa código de `variables/`: grep de `sys.path.insert` con "variables" en `datos/` sólo da el docstring `verificar.py:188`).
4. **Medición:** recuentos por `grep`/`git` el 2026-08-20: 47 usos de `parents[3]` en 41 archivos, 63 `sys.path.insert` en 114 `.py`, co-cambio de 83 commits (`0010:9-31`, `ESTADO:1475`). No es skill.
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** Sí. `MAPA.md` regenerado a mano/`REGENERAR` (ver (iv)). `rutas.py` lo importan 40 archivos, incluido `nowcast_puertas.py:51` (camino del número). Tests: `test_rutas.py` (2 de 3 reales), `test_definiciones_compartidas.py` (real), `test_rutas_citadas_existen.py` (real). Hook: no instalado en esta PC.
7. **¿Doc coincide?** No: 246 líneas (hoy 471); "sólo dos módulos migrados" (hoy 40 archivos); "63/114" y "47/41" (hoy 229/146 y 51/51); "hallazgo pyarrow que NO se arregló" (`0010:96-101`) quedó arreglado cinco días después por 0014 (`definiciones.py:111-115`) sin cruce en el ADR; `tests/README.md` lista 4 de los 8 archivos de `tests/` y dice "8 chequeos" para `test_definiciones_compartidas` [V].
8. **VEREDICTO: VIGENTE-ESTRUCTURAL** (con dos garantías no cumplidas: "ya no se puede agregar una ruta sin declararla" y "el hook lo reindexa").
9. **DESTINO: 1.** Sobrevive: un inventario de rutas entre módulos (`rutas.py`), un MAPA generado que se lee antes de abrir código, el router en el README de cada módulo (no `BITACORA.md`), y "lo que cruza módulos tiene su test en `tests/` y no se arregla tocando el test". Se pierde: la garantía de completitud (hay que arreglar `test_rutas.py`), el hook como mecanismo (hoy es un paso manual de `REGENERAR`), y todas las cifras del ADR.

### ADR-0011 — El chequeo del `.gitignore` estaba mal documentado (2026-08-21)
1. `0011` · 2026-08-21 · corrige `PROTOCOLO-GIT.md`: no usar `check-ignore -q`/código de salida; usar `git add -n` (archivo nuevo) o `check-ignore -v --non-matching` (existentes); la ruta va relativa a donde uno está parado.
2. **Quién decidió:** "Quién: Claude (con Valle)" (`0011:3`; `ESTADO:1330`). El hallazgo lo produce una corrida en la PC de Valle (`0011:8-25`). Commit `5aff5b0` de ThiagoPP260 [V].
3. **Declarado:** "Aceptada". **Real:** `PROTOCOLO-GIT.md:68-94` incorporó la corrección [V]; pero (a) la premisa central no se reproduce con `-q` en git 2.53.0 (ver (ii)); (b) el segundo error (prefijo desde adentro) sí se reproduce; (c) tres tests y `.gitignore:143` siguen leyendo el código de `-q`.
4. **Medición:** reproducción de comandos (`0011:20-27, 50-54`) y auditoría de las 39 excepciones de datos con `check-ignore -v --non-matching`: 68 archivos, 0 ignorados (`:96-102`). Hoy hay 51 líneas `!` de datos (`grep '^!' .gitignore`), no re-auditadas [N].
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** Sí como disciplina de proceso; ningún test la hace cumplir (los tests que consultan git usan `-q`; `test_bases_viajan.py:52-59` sí aplica la parte de "ruta relativa desde `cwd=RAIZ_PROYECTO`" y `--no-optional-locks`).
7. **¿Doc coincide?** `PROTOCOLO-GIT.md:84-86` repite la premisa dudosa ("Devolvía 0 también cuando matchea una excepción"). `PROTOCOLO-GIT.md:65-66` ("hay que correrlos desde la raíz… o fallan") quedó sin corregir en la misma sección que 0011 dice haber arreglado. `.gitignore:143`, `producto/dashboard/README.md:145` y dos PROMPT (`PROMPT-3…:96`, `PROMPT-Mapa…:244`) siguen prescribiendo `-q`. El ADR decía que sólo quedaban menciones históricas (`0011:92-95`): no es del todo así.
8. **VEREDICTO: VIGENTE-ESTRUCTURAL** (proceso/mecánica de git; con premisa parcialmente no reproducible).
9. **DESTINO: 1.** Sobrevive (reformulada): para saber si un archivo viaja, preguntarle a git con la ruta relativa a donde uno está parado; `check-ignore` saltea lo trackeado (usar `--no-index` o `git ls-files`) y `-v` es el que muestra las excepciones `!`. Se pierde: la afirmación de que `-q` devuelve 0 sobre una excepción y la prohibición general del código de salida.

### ADR-0014 — Las definiciones compartidas viven en un solo lugar (`definiciones.py`) (2026-08-25)
1. `0014` · 2026-08-25 · `definiciones.py` en la raíz, hermano de `rutas.py`; cinco módulos re-exportan.
2. **Quién decidió:** "Valle (decisión), Claude (auditoría e implementación)" (`0014:3`). Commit `5aff5b0` de ThiagoPP260 [V].
3. **Declarado:** "Aceptada". **Real:** implementado y cubierto por test de identidad (ver (iii)). Pasa en HEAD (`pytest.txt`).
4. **Medición:** 15 casos borde de fecha y 13 de mayoría en los dos backends de dtype (`0014:50`), hoy en `test_definiciones_compartidas.py:81-110` [V]. El bug de pyarrow fue medido en pandas 2.2.3 y 3.0.2 (`:24`, `definiciones.py:111-114`).
5. **¿Fuga/espejo?** No aplica.
6. **¿Vigente?** Sí. Lo importan 5 módulos (0014) + el motor: `nowcast_puertas.py:289`, `estimar_beta_dictamen.py:98`, `baseline_voto_individual.py:100`, `record_por_origen.py:45`, `medir_guard_era.py:55` [V]. Test: `test_definiciones_compartidas.py::test_ninguna_copia_redefine_las_definiciones` (`:268-304`) compara identidad y falla con el código viejo.
7. **¿Doc coincide?** Sí en lo central. Desvíos: `MAYORIAS` sin consumidor (`definiciones.py:189` vs regla `:60-61`); cinco copias de `BANCAS` fuera de `definiciones.py`, una en el motor (`estimar_beta_dictamen.py:88`); `__all__` sin `caracter_de_dictamen`; `tests/README.md` describe 8 chequeos; 0014:54 anota `datos/padron` como "escalares" y hoy dos son el mismo dict.
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 1.** Sobrevive: "una definición que dos módulos deben responder igual vive UNA vez (`definiciones.py`), se re-exporta, y se controla por identidad de objeto, no por resultado"; criterio de qué entra ("si divergen mañana, ¿alguien se entera?") y de qué NO (dos parsers de fecha con formatos distintos). Se pierde: nada de fondo; hay que sumar 0019 y 0021 al mismo ADR consolidado y limpiar `MAYORIAS`/`BANCAS`.

### ADR-0019 — El calendario de gobiernos vive en `definiciones.py` (y el del ICG NO) (2026-09-06)
1. `0019` · 2026-09-06 · `definiciones.GOBIERNOS` (4 ventanas, frontera exclusiva en el recambio) + `gobierno_por_fecha` + `era_de`; el calendario del ICG (9 ventanas, borde inclusivo) queda aparte.
2. **Quién decidió:** "Decide: Franco" (`0019:3`). Commit `2dbad10` de Franco Marconi [V].
3. **Declarado:** "APLICADO". **Real:** aplicado y verificado (ver (iii)).
4. **Medición:** el test compara contra literales viejas transcritas del código del 04-09 (`test_definiciones_compartidas.py:309-330`) sobre 14 fechas borde (`:317-319`) [V]. No es skill.
5. **¿Fuga/espejo?** No aplica a este ADR. La razón de ser —el guard de era del récord (ADR-0018)— sí tiene evidencia contaminada/parcial (ADR-0034; ver lote de 0018); 0019 no depende de que el guard mejore el skill.
6. **¿Vigente?** Sí, y **actúa sobre el número**: `GUARD_ERA` ON (`nowcast_puertas.py:119`) → `_alineacion_base` toma `era_de(hasta)` (`:301-303`) ⇒ con `--fecha 2026-06-01` (`REGENERAR.ps1:291`) el récord del legislador sólo mira votos ≥ 2023-12-10 (`test_era_de_es_el_arranque_del_gobierno`, `:378`). Consumidores: `bloque.py:363`, `origen_lider.py:63`, `origen_por_acta.py:71,89`, `nowcast_puertas.py:289`, y en el harness `record_por_origen.py:45`, `record_por_origen_brazos.py:104`, `medir_guard_era.py:55`, `baseline_voto_individual.py:100`. Test: `test_definiciones_compartidas.py:333-412`, pasa en HEAD.
7. **¿Doc coincide?** Sí. `FORMULA-COMPLETA.md:555-557` cita 0019 correctamente; `definiciones.py:126-148` repite el argumento; no encontré contradicción. Riesgo futuro anotado: `MILEI` cierra en `2100-01-01` (`definiciones.py:153`); el recambio del 10-dic-2027 exigirá tocar `GOBIERNOS` y `OFICIALISTAS` de `origen_lider` [I].
8. **VEREDICTO: VIGENTE-ESTRUCTURAL.**
9. **DESTINO: 1** (con referencia a 2, porque el guard de era consume `era_de`). Sobrevive: "la frontera de eras es UNA (`definiciones.GOBIERNOS`, media abierta); la carga útil (quién es oficialista) se queda en su módulo; el calendario del ICG es otra regla y no se unifica". Se pierde: nada.

---

## 2. Notas finales

### (a) Contradicciones entre cuerpo y encabezado de un mismo ADR
- **0001:** encabezado "Aceptada"; la regla 5 del cuerpo ("data/raw y data/clean… no se versionan") es falsa hoy (23+1 archivos versionados en esas carpetas). No hay contradicción interna, sí contradicción con el árbol.
- **0002:** encabezado "Aceptada"; cuerpo: "desde 1998" (`:6`) vs "Combinado ~2001" (`:17`); punto 3 ("las agrega a la canónica") vs la realidad del bot (`bot-diario.yml:115-119`).
- **0009-BORRADOR:** título "no leer", cuerpo "Pendiente para Valle: borrar este archivo… Anotado en `PENDIENTES-DE-BORRAR.md`" (`:15-16`): la nota apunta a un archivo inexistente.
- **0009:** encabezado "ACEPTADO (vigente)"; cuerpo: el diseño de un solo `upsert_proyecto` (`:57-59`) no es lo implementado; "excepción en el `.gitignore`" (`:210`) ya no existe; "del que cuelga todo el nowcast" (`:114-115`) falso desde ADR-0012. La tabla de precedencia fue editada en el lugar (`:66`) y además hay una "Corrección" que dice que estaba mal (`:145-173`): el ADR se lee mejor de abajo hacia arriba.
- **0010:** "Aceptada"; el cuerpo promete "testeado: ya no se puede agregar una ruta sin declararla" (`:75-76`) con un test que no puede fallar; "hallazgo que NO se arregló" (`:96-101`) arreglado por 0014; "hook lo reindexa" (`:38-39`).
- **0011:** "Aceptada"; el cuerpo prohíbe el código de salida (`:78-83`) y la premisa (`:28-30`: "`check-ignore` devuelve 0 cuando la ruta matchea alguna regla… El `-q` esconde cuál fue") no coincide con lo que hace `-q` (`-q` no reporta negaciones; `-v` sí).
- **0014:** "Aceptada"; cuerpo: `MAYORIAS`/`BANCAS` entran en "contenido inicial" (`:39`) aunque `MAYORIAS` no tiene segundo consumidor (regla 2 del archivo).
- **0019:** sin contradicción encontrada.

### (b) Contenido o código que ya no vale y sigue en el árbol (con LOC)
| Ruta | LOC | Qué es |
|---|---:|---|
| `coordinacion/DECISIONES/0009-BORRADOR-…md` | 16 | ADR neutralizado; nota apunta a un archivo inexistente |
| `coordinacion/CONECTAR-GIT.md` | 26 | documento retirado 2026-08-06; copia "íntegra" prometida no existe |
| `coordinacion/_wtest` | 0 | archivo vacío versionado desde 2026-06-27 |
| `modelo/ensemble/src/backtest_cadena.py` | 550 | NEUTRALIZADO ADR-0012 |
| `modelo/ensemble/tests/test_backtest_cadena.py` | 330 | test de lo neutralizado; corre en CI |
| `variables/proyecto/src/comparar_vias_icg.py` | 298 | SUPERSEDED/NEUTRALIZADO 2026-08-11 |
| `modelo/ensemble/src/ensemble.py` | 412 | formulación v1 dada de baja; contiene además lo vivo (`DESVIO_MIN_INDIVIDUAL`, clip) |
| `variables/proyecto/RESULTADOS-tema.md` | 3 | "(Histórico)… DEPRECADO" |
| `COMMITEAR.ps1`, `COMMITEAR-2026-09-08.ps1` | 285 + 220 | scripts de un solo uso de commits de 06-09 y 08-09 |
| `casos/README.md:21,28-29` | — | describe dos generadores y HTML que ya no existen (`ls casos` → sólo `nowcast_puertas_html.py`); su propio Resumen (`:5`) dice que se archivaron el 10-09 |
| `tests/test_rutas.py:73-100` | 28 | test que no puede fallar |
| `.mapa/indexar.py:646-659` | ~14 | cálculo de `viaja` roto en Windows (43 archivos, 196 MB mal informados) |
| `definiciones.MAYORIAS` | 1 | constante sin consumidor |
| Afirmaciones "proyectos.db no viaja" | — | `datos/proyectos/README.md:58`, `MAPA.md:65`, `tests.yml:26-27`, `tablero_datos.js:213`, `PLAN-DE-TRABAJO.md:132` |
| Instrucciones `check-ignore -q` | — | `.gitignore:143`, `producto/dashboard/README.md:145`, `PROTOCOLO-GIT.md:65-66,84-86` |

### (c) Reglas de infraestructura repetidas en varios ADR (candidatas a fusionar en el ADR 1)
1. **"Lo compartido tiene UN dueño/lugar y un control que compara identidad, no valores"** — 0010 (#3-#4), 0014, 0019, 0021 (carácter del dictamen y raíz del repo). Además `definiciones.py` (docstring) y `tests/README.md`.
2. **"Idioma de import: buscar la raíz hacia arriba hasta `rutas.py`, sin `parents[N]`"** — 0010, 0014, 0021, `rutas.py:22-35`, `definiciones.py:42-51`, `test_raiz_del_repo_una_sola_copia.py`.
3. **"Los errores de datos no dan error" / "coincidir no es garantía"** (motivación) — 0010, 0011, 0014, 0017, 0019, 0020.
4. **"Qué viaja por git y cómo se chequea"** — 0001 (#5), 0009 (cuarentena viaja), 0011, 0017, 0020, 0023 (y la doctrina real en `.gitignore`, que no está en ningún ADR).
5. **"Un cambio en un contrato compartido exige ADR y aviso en el TABLERO"** — 0001 (#3), 0014 (consecuencias), `definiciones.py:58-59`, `PROTOCOLO-GIT.md:19`, `CLAUDE.md`.
6. **"Un test de `tests/` que falla no se arregla tocando el test"** — 0010 (`:90-92`), `tests/README.md`, docstrings de los tests (con la excepción de que `test_insumos_del_motor_viajan` prescribe agregar a `EXCEPCIONES`).
7. **"Un control tiene que poder fallar / se prueba rompiéndolo a propósito"** — 0009 (`test_verificar.py`), 0014 (test que falla con el código viejo), 0019 (literales viejas). Es justo la regla que 0010 no cumplió con `test_rutas.py`.
8. **"Frenar vs. apartar"** — sólo 0009 (cuarentena; frenar por invariante rota o avalancha). Regla propia de datos.

Fuentes de "hechos" usados que no verifiqué de nuevo: cifras del censo (0,1333 etc.) y el estado de `pytest` (del contexto del auditor principal).
