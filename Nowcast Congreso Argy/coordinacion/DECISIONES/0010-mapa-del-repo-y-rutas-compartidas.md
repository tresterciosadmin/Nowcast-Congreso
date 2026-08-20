# ADR-0010 — Mapa del repo (MAPA.md), router en los README y `rutas.py`

**Fecha:** 2026-08-20 · **Estado:** Aceptada · **Quién:** Claude (con Valle)

## Contexto

Auditoría de la estructura del repo pedida por Valle (2026-08-20). El repo tiene
**tres sistemas de conexión superpuestos entre carpetas, y sólo uno estaba
documentado**:

1. **Imports Python.** No hay `pyproject.toml`, ni un `__init__.py`, ni
   `conftest.py`. Los módulos se alcanzan con `sys.path.insert` en tiempo de
   ejecución: **63 líneas** en 114 archivos. Riesgo concreto: hay **tres
   `to_canonical.py`** (ckan_diputados, argentinadatos, manual_2026); cualquier
   proceso que inserte dos de esos `src/` importa el primero y no se entera.
2. **Rutas de archivo — el grafo verdadero.** Los módulos se hablan por
   parquet/csv/db. Ese grafo no estaba escrito en ningún lado: hubo que
   reconstruirlo grepeando literales de ruta. Y la raíz del proyecto se
   recalculaba **47 veces en 41 archivos** con `parents[3]`, contando niveles de
   carpeta a mano.
3. **Copias sincronizadas a mano.** Como la regla es "no importes el código de
   otro módulo, consumí su salida", las *definiciones* compartidas se clonaron:
   `periodo_parlamentario` ×4, `normalizar_mayoria` ×3, `_get`/`_pedir` (HTTP con
   backoff) ×8, más `MIEMBROS`, `MARGEN_DISPUTADA`, `CONDUCTAS`. Se verificaron
   una por una: **hoy están de acuerdo**. El problema no es que estén rotas, es
   que el único control era que alguien se acordara — en un repo cuyo modo de
   falla documentado es que *los errores de datos no dan error*.

También se midió el co-cambio de git (83 commits): domina el ritual de las cuatro
bitácoras (ESTADO↔EN-HUMANO 33 veces, ESTADO↔`tablero_datos.js` 26, ESTADO↔TABLERO
21). Eso funciona y no se toca.

## Decisión

**1. `MAPA.md` en la raíz del proyecto, generado, con `.mapa/` al lado.**
Índice mecánico del repo (carpetas, archivos centrales, quién importa a quién,
fuentes externas, variables de entorno). Se lee antes de abrir código;
`.mapa/buscar.py` ubica un símbolo sin escanear nada. Un hook `pre-commit` lo
reindexa y avisa —sin bloquear— si algún README quedó vencido.

**2. El router vive en el `README.md` de cada módulo, NO en un `BITACORA.md`
aparte.** La skill `mapa-de-proyectos` pide un `BITACORA.md` por carpeta: acá
serían **44 archivos nuevos** repitiendo lo que los README ya dicen, en un
proyecto cuya patología número uno es que las bitácoras se contradicen entre sí.
Se agregó a cada README una línea `**Resumen:**` y una sección `## Buscar acá si`,
y se **forkeó `indexar.py`** (vendorizado en `.mapa/`, cabecera con los 7 parches
marcados `FORK NOWCAST`) para leerlas de ahí.

**3. `rutas.py` en la raíz: un único inventario de lo que cruza entre módulos.**
52 constantes nombradas (`CANONICA_CLEAN`, `PROYECTOS_DB`, `PADRON_DIPUTADOS`,
`DESVIOS_POR_VOTO`, …), respetando las variables de entorno que ya existían
(`CANON`, `EXP_CLEAN`, `OUT`…): sólo cambia el DEFAULT. El idioma para importarlo
**no usa `parents[N]`**: busca la raíz hacia arriba hasta encontrar `rutas.py`,
así que un archivo que cambia de profundidad sigue andando.

**4. Dos controles nuevos, en un `tests/` de raíz** (para lo que cruza módulos y
por eso no pertenece a ninguno):
- `tests/test_definiciones_compartidas.py` — las copias tienen que coincidir,
  sobre fechas borde y los dos backends de dtype.
- `tests/test_rutas.py` — lo declarado existe, **y lo que el código usa está
  declarado**: escanea todos los `.py` buscando rutas entre módulos armadas a
  mano y falla si alguna no figura en `rutas.py`. Hoy da 0 huérfanas.

**5. El ciclo `datos/proyectos` ↔ `variables/embudo` se rompe a nivel import.**
`verificar.py` hacía `sys.path.insert(.../variables/embudo/src); import embudo`:
una dependencia hacia arriba (capa 1 → capa 2) que este mismo CLAUDE.md prohíbe.
La medición se mudó a `variables/embudo/src/cohorte_dos_rutas.py` (dueño del
concepto de cohorte) y `verificar.py` la invoca **como proceso**, consumiendo su
JSON —su contrato— igual que `run_pipeline.py` invoca a los demás módulos.

## Consecuencias

**A favor**
- Orientarse cuesta 246 líneas de `MAPA.md` en vez de escanear el repo.
- El grafo de conexiones entre carpetas está escrito y **testeado**: ya no se
  puede agregar una ruta entre módulos sin declararla.
- La deriva silenciosa de las definiciones duplicadas pasa a ser un test rojo.
- `datos/` deja de importar código de `variables/`.

**En contra / a vigilar**
- `.mapa/indexar.py` es un **fork**: si la skill upstream cambia, hay que
  re-aplicar los parches (están marcados y documentados en su cabecera).
- **`rutas.py` migró sólo dos módulos** (`datos/proyectos`, `evaluacion/baseline`);
  quedan ~45 usos de `parents[3]` en módulos con claim abierto. El test cubre el
  inventario aunque no estén migrados, así que el valor no depende de terminar la
  migración — pero el repo queda con dos estilos conviviendo un tiempo.
- El control de cohorte sigue dependiendo de que `variables/embudo` funcione: si
  el medidor no corre, el control **falla** (a propósito: un control que se
  saltea en silencio es exactamente cómo se perdieron tres errores el 07-08).
- Se agregó una carpeta `tests/` en la raíz. Es una ubicación compartida nueva:
  un test de ahí que falla no es de nadie y de todos. La regla queda escrita en
  `tests/README.md`: **no se arregla tocando el test**.

## Hallazgo que NO se arregló acá (queda anotado)

`periodo_parlamentario` revienta con backend `pyarrow` en las **cuatro** copias:
`pd.to_numeric(anio)` conserva `int64[pyarrow]` y `a % 2` levanta
`NotImplementedError: mod not implemented` (verificado en pandas 2.2.3 y 3.0.2).
En producción no se nota porque `read_parquet` devuelve numpy. El arreglo es una
línea por copia (`.astype("float64")`), pero toca cuatro módulos con dueño: queda
como `xfail` documentado en `tests/test_definiciones_compartidas.py`.

Y una trampa que **no es un bug pero muerde**: `variables/bloque` publica una
columna `periodo` que es un **año legislativo** (entero, "diciembre cuenta para el
año siguiente"), mientras `export`, `disciplina`, `ficha` y `asistencia` publican
un `periodo` de dos años entre recambios ("2019-2021"). Nadie las cruza hoy;
cruzarlas por nombre daría cualquier cosa sin levantar un error. Queda con test
que lo documenta y aviso en el README de `variables/bloque`.
