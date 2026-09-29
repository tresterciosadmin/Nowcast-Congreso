# C1 — Repo, datos y contratos compartidos

**BORRADOR** · **Absorbe:** 0001, 0002, 0009-BORRADOR *(descartable)*, 0009-proyectos-db, 0010, 0011, 0014, 0019, 0020, 0021 · **Referencias:** 0005 (C2), 0017 (C2)

## 1. La regla

> **Lo compartido vive una vez, se re-exporta y se controla por identidad; un contrato de datos cambia sólo con un ADR; lo que el motor lee viaja por git (o figura como excepción con su motivo medido); y todo control tiene que poder fallar.**

## 2. Por qué

El proyecto se rompió en silencio por lo mismo una y otra vez: un dato que no viajaba, una ruta armada a mano, una definición copiada cinco veces (`BANCAS` sigue en cinco lugares), un test que nunca podía dar rojo. Hoy sigue pasando:

- `tests/test_insumos_del_motor_viajan.py` **falla en `HEAD`**: `censo_detalle_2026-09-28.parquet` (el insumo del 0,1333 y de τ) está ignorado por `*.parquet` y vive en un solo disco.
- `tests/test_rutas.py::test_el_codigo_no_usa_rutas_entre_modulos_sin_declarar` **no puede fallar**: `RAIZ` figura entre las rutas declaradas y es ancestro de cualquier ruta (`inventario()` la incluye; verificado). Sin ese escape hay 14 rutas huérfanas en 18 archivos.
- `MAPA.md:181` dice "**181 viajan por git, 0 no**". El inventario tiene el detalle del censo (ignorado) y otros 42; causa probable: `indexar.py:646-659` manda saltos de línea de Windows a `git check-ignore --stdin` [I].
- El hook `pre-commit` que CLAUDE.md y 0010 describen **no está instalado** (`.git/hooks` sólo tiene `.sample`).
- `proyectos.db` pesa 87,3 MiB (falla el test a 95); con el ritmo actual (~0,18 MiB/día) llega al techo a fines de octubre [I]; ningún pendiente registra la decisión de LFS.

## 3. Cómo se verifica

- `python -m pytest tests/ datos/proyectos/tests -q` **y** los 62 `test_*.py` como scripts (lo que corre `.github/workflows/tests.yml`; hoy 40 pasan y 1 falla).
- **Propuesto:** darle a cada test de infraestructura su *control positivo* (una ruta inventada, un archivo ignorado a propósito) para que se demuestre que puede fallar, y sacar `RAIZ` del conjunto de escapes.
- `python verificar_regeneracion.py` (hoy: 15 OK, 1 a mirar: `MAPA.md` fuera de presupuesto).

## 4. Qué la invalida

- Que `test_insumos_del_motor_viajan` siga en rojo sin que nadie lo trate como bloqueante (hoy es lo único que dice que **el CI está en rojo en `HEAD`** [I: `gh` sin login]).
- Que `proyectos.db` cruce los 95 MiB, o que GitHub cambie el techo de 100 MiB.
- Un segundo directorio con una copia del motor (hoy: el worktree `..\.claude\worktrees\suspicious-lalande-8a89b7`, 175 MB, del 15-09; y `Archivos_Borrar/repro/` de esta auditoría).

## 5. Estado real hoy (verificado)

| pieza | estado | dónde |
|---|---|---|
| rutas | `rutas.py` con 59 constantes (el ADR dice 52); 40 archivos lo importan pero quedan 51 `parents[3]` y 229 `sys.path.insert` | `rutas.py`, `tests/test_rutas.py:73-100` |
| definiciones compartidas | `definiciones.py` (212 líneas) re-exportada por 5 módulos; `MAYORIAS` sin consumidor; `__all__` omite `caracter_de_dictamen` | `definiciones.py`, `tests/test_definiciones_compartidas.py` |
| calendario de gobiernos (0019) | una sola frontera de eras; **afecta el número** (`GUARD_ERA` ON corta el récord en 2023-12-10); `MILEI` cierra en 2100: actualizar antes de 2027-12 | `definiciones.GOBIERNOS`, `nowcast_puertas.py:119,301` |
| bases sqlite por git (0020) | `proyectos.db` versionada, 87,3 MiB; aviso a 50, falla a 95 | `tests/test_bases_viajan.py` |
| "una sola copia" (0021) | el test mide que la *búsqueda de la raíz* sea única, no que el repo exista una vez; **no cuenta el worktree** | `tests/test_raiz_del_repo_una_sola_copia.py:30,40` |
| `proyectos.db` (0009) | 115.495 filas; **ya no alimenta P(sanción)** desde ADR-0012 (sólo el embudo) | `variables/embudo/src/embudo.py:708` |
| `git check-ignore -q` (0011) | los tests lo usan y 0011 lo prohíbe; su premisa no se reproduce con git 2.53 | `test_bases_viajan.py:92,109`, `.gitignore:143` |

**Reglas de datos que se conservan tal cual** (no son de proceso, son trampas del dato): las comisiones **contienen comas** y se matchean contra el catálogo, del nombre más largo al más corto; `od_numero` se repite entre períodos (la clave es `(periodo, od_numero)`); antes de declarar que falta un dato, mirar el parquet y no la carpeta de trabajo; no publicar P(sanción) de proyectos con origen Senado.

**Historia:** 0001 (06-25) estructura del repo · 0002 (06-25) semilla → canónica → bot · 0009-BORRADOR (08-07, Valle) **descartable**: neutralizado, su nota a `PENDIENTES-DE-BORRAR.md` es falsa y el texto vive en `git show fd2aa2b` · 0009 (08-07, Valle) `proyectos.db` como fuente de verdad · 0010 (08-20) mapa y rutas · 0011 (08-21) `.gitignore` · 0014 (08-25) definiciones compartidas · 0019 (09-06, Franco) calendario · 0020 (09-08, Franco) bases por git · 0021 (09-08, Franco) carácter y raíz.

**Se pierde:** "los datos van fuera de git" (falso: hay 23 `data/clean`, 30 parquet y 2 `.db` versionados); "una rama por módulo" (12 fusiones en 243 commits); "el bot agrega a la canónica" (abre un issue; un humano reconstruye, ~20 min); la garantía de completitud de `rutas.py` de 0010; las cifras 246 líneas / 2 módulos / 52 constantes; la prohibición del exit code de 0011 (se reformula: preguntarle a git con ruta relativa y `-v`).
