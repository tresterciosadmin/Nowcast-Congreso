# PLAN DE LIMPIEZA — análisis por fases (2026-09-08)

**Resumen:** El orden en que hay que hacer la limpieza del repo, por qué en ese orden, y qué se decide en cada fase. El prompt para correrla en una sesión aparte es `PROMPT-LIMPIEZA-SESION-NUEVA.md`, que es autocontenido: no hace falta leer este archivo para ejecutarla.

Pedido de Franco (07/08-09): *"repasemos todo el modelo y las carpetas completas para
reordenar y hacer limpieza. Quiero que vayas archivo por archivo y verifiquemos qué sirve,
qué no y ordenemos variable a variable cada elemento."*

## El estado del que se parte, medido

| | |
|---|---|
| código | **162 archivos · 38.865 LOC · 29 módulos** con código |
| datos | **140 archivos · 195 MB** (48 parquet, 42 csv, 38 json, 10 xlsx, 2 bases) |
| proyecto en disco | 390 MB · `.git` ~139 MB · `fase0/` 20 MB · `Aportes sobre dataset congreso/` 6,1 MB (169 archivos) · `Archivos_Borrar/` **vacío** |
| documentación | 28 README de módulo, **27 con la bitácora vencida** |
| tests | 53 archivos de test; `pytest tests/ datos/proyectos/tests` da 30 OK |
| controles | `verificar_regeneracion.py`: 16 OK · 0 a mirar |
| pendientes | 10 ítems abiertos en `URGENTE.md` (M, D, E, H, I, 2, F, 5, 8, L) |

## Por qué en fases, y no módulo por módulo de una

La tentación es abrir `datos/argentinadatos/` y empezar. Está mal por tres razones que
ya costaron trabajo en este repo:

1. **Sin el inventario de datos no se puede decidir nada.** "¿Sirve este parquet?" se
   contesta con "¿quién lo lee?", y hasta el 08-09 eso no estaba escrito en ningún lado.
   Por eso el inventario se hizo PRIMERO y ya está en `MAPA.md` — la fase 1 lo usa, no
   lo rehace.
2. **Los módulos no son independientes.** `datos/canonica` es insumo de casi todo; tocarlo
   al final significa rehacer las decisiones de los que dependen de él. El orden es el de
   la cadena de datos, no el alfabético.
3. **El repo tiene un modo de falla propio y hay que respetarlo.** Acá los errores de
   datos **no dan error**: llegan como una columna vacía o un archivo que "no existe
   todavía". Borrar antes de medir es exactamente cómo se pierde trabajo pago.

## Fase 0 — Blindaje (antes de borrar el primer archivo)

Nada de esto es limpieza; es lo que hace reversible a la limpieza.

- Commitear TODO lo pendiente, incluida la base (`.gitignore` cambiado el 08-09: ver
  ADR-0020). Una limpieza sobre un árbol sucio no se puede revertir por partes.
- `python -m pytest tests/ datos/proyectos/tests -q` y `python verificar_regeneracion.py`:
  se anota el resultado. Es la línea de base contra la que se compara al final.
- `python .mapa/indexar.py` y leer `MAPA.md` entero, **incluido el inventario de datos**.
- Leer `coordinacion/URGENTE.md` (381 líneas). No para resolverlo: para no borrar algo
  que un ítem abierto necesita.

**Criterio de salida:** suite en verde anotada + commit limpio.

## Fase 1 — Datos (la que más plata ahorra, y la única que ya tiene el mapa hecho)

El inventario del MAPA da, para cada uno de los 140 archivos: forma, peso, **si viaja por
git**, quién lo escribe y quién lo lee. Tres grupos salen solos:

- **28 archivos que ningún archivo de código nombra** (49,7 MB). El grueso son los ocho
  `datos/export/data/votaciones_*.xlsx` (49,6 MB, versionados). Hay que decidir si son un
  entregable para el equipo o un resto de la etapa de exportación. **Es la decisión de
  mayor impacto en el peso del repo, y es de Franco.**
- **37 archivos que NO viajan por git**, 13 de ellos de más de 100 KB. Cada uno vive en un
  solo disco. Para cada uno: o es intermedio regenerable (y está bien que no viaje), o es
  un contrato/curado y **falta la excepción en `.gitignore`**. Este mismo chequeo, corrido
  el 08-09, encontró la séptima repetición del bug: `alias_legislador_id.csv`, los 143
  pares que Franco aprobó uno por uno, no viajaba.
- **45 archivos con productor y sin consumidor.** En un entregable para humanos es lo
  esperado; en un intermedio significa que sobra.

Ojo con una trampa que el propio inventario documenta: un output cuyo nombre se arma con
f-string (`nowcast_{pid}.json`) figura como "nadie lo nombra" y está vivo. **"Nadie lo
nombra" es una propiedad medida; "no sirve" es una conclusión, y la saca una persona.**

**Criterio de salida:** cada uno de los 140 con veredicto escrito, y `.gitignore` con una
excepción por cada curado que hoy no viaja.

## Fase 2 — Restos evidentes (barato y sin criterio)

Nueve archivos que **nadie importa**, y siete de ellos son parches de un solo uso con la
fecha en el nombre:

```
coordinacion/_aplicar_v2_2026-07-22.py          coordinacion/_aplicar_v2b_2026-07-22.py
coordinacion/_aplicar_roster_nominal_2026-07-22.py
coordinacion/_aplicar_linaje_senado_2026-07-23.py
coordinacion/_aplicar_cobertura_senado_2026-07-23.py
coordinacion/_aplicar_excluir_aux_2026-07-23.py coordinacion/_reparar_tablero.py
variables/bloque/_aplicar_bitacoras.py          coordinacion/_patch_tablero_v2.py
```

Van a `Archivos_Borrar/` (hoy vacía), no al tacho: la regla de la casa es que el descarte
se conserve un tiempo. `verificar_regeneracion.py` también figura como "nadie lo importa"
y **no se toca**: es un entrypoint, el diagnóstico no lo sabe.

Acá entra también `Aportes sobre dataset congreso/` (169 archivos, 6,1 MB): material de
terceros de un solo uso según el ADR-0002. Si ya cumplió, se archiva.

**Criterio de salida:** `--estructura` sin huérfanos que no sean entrypoints.

## Fase 3 — Módulo por módulo, en orden de dependencia

29 módulos. El orden es el de la cadena, porque el de abajo condiciona al de arriba:

1. **Ingesta** — `datos/decada_votada`, `datos/ckan_diputados`, `datos/argentinadatos`,
   `datos/senado`, `datos/manual_2026`, `datos/bot_recoleccion`, `datos/padron`
2. **Base** — `datos/canonica`, `datos/expedientes`, `datos/proyectos`, `datos/taxonomias`
3. **Variables** — `variables/legislador`, `variables/bloque`, `variables/proyecto`,
   `variables/embudo`, `variables/asistencia_quorum`
4. **Modelo** — `modelo/voto_individual`, `modelo/agregador_institucional`,
   `modelo/ensemble`  ← **CONGELADOS**, ver más abajo
5. **Evaluación y producto** — `evaluacion/baseline`, `producto/dashboard`, `casos`
6. **Bordes** — `datos/export`, `datos/seguimiento`, `fase0`, `docs/taxonomias`,
   `coordinacion`, `tests`, raíz

Por cada archivo, uno de cuatro veredictos y nada más:

| veredicto | qué significa | qué se hace |
|---|---|---|
| **SIRVE** | alguien lo importa o lo corre, y hace lo que dice | nada |
| **SIRVE PERO MIENTE** | funciona, pero el README o el docstring dicen otra cosa | se corrige el texto, no el código |
| **SE FUSIONA** | duplica lo que hace otro | se unifica, con test que compare las dos salidas antes |
| **SE ARCHIVA** | ni importado, ni corrido, ni citado | a `Archivos_Borrar/` |

Los cuatro más gordos primero, porque son donde está el desorden:
`variables/proyecto` (26 archivos, **17 en un solo `src/`**), `modelo/ensemble` (16),
`datos/expedientes` (15), `datos/padron` (11).

**Criterio de salida por módulo:** veredicto escrito para cada archivo + README con su
`**Resumen:**` y su `## Buscar acá si` al día + `--sellar` de ese módulo.

## Fase 4 — La documentación, que es la parte que hoy miente

**27 de los 28 README tienen la bitácora vencida.** No es un detalle de forma: el MAPA se
arma con la línea `**Resumen:**` y la sección `## Buscar acá si` de cada uno, así que hoy
el router del mapa describe un repo que ya no existe.

Se sella **después** de revisar la prosa, nunca antes. El 08-09 se corrió `--sellar-todo`
por comodidad y hubo que revertir 27 sellos: estampar la huella sin leer el texto afirma
una frescura falsa, que es peor que no tener sello. El propio `indexar.py` lo dice.

## Fase 5 — Los URGENTE abiertos

No se resuelven en la limpieza, pero la limpieza no puede pisarlos. Los diez, en una línea:

- **M** — β se estimó antes del parser nuevo y antes del dedupe de gemelas. Se arregla
  corriendo `.\REGENERAR.ps1 -Desde 5` (~10 min).
- **D** — δ en el Senado sigue sin ser estimable, ahora por falta de clusters (20 actas de
  mayoría, 1 de sólo-minoría). La propuesta de usar la disidencia necesita un ADR.
- **E** — temas: 51,8% de cobertura, faltan 2.134 títulos. Necesita créditos de API.
- **H** — `_sources/` está viejo: rehacer la canónica desde ahí borra 181.309 votos.
- **I** — actas gemelas aplicado; el skill publicado estaba inflado.
- **2** — leer la revisión metodológica del 25-08 antes de tocar el motor.
- **F** — a qué linaje va el bloque personal de Daer.
- **5** — 9 filas MEDIA en el roster de jefes, dos estaban mal.
- **8** — récord por tema, destrabado el 06-09.
- **L** — `test_ensemble.py` aborta 1 de cada 6 corridas al cerrar el intérprete (los 33
  chequeos pasan siempre).

## Fase 6 — Cierre

Suite completa, `verificar_regeneracion.py`, reindexado, `MAPA.md` dentro del presupuesto
(460 líneas, declarado en `.mapa/indexar.py`), `URGENTE.md` con lo resuelto **borrado**
(no hay sección "resueltos"), `TABLERO.md` y `tablero_datos.js` al día, y un commit por
tarea, en español, **sin push**.

## Lo que NO se toca, pase lo que pase

`modelo/ensemble/`, `modelo/agregador_institucional/`, `modelo/voto_individual/`,
`variables/bloque/`, `variables/proyecto/` (modulador y origen) y `variables/embudo/`
**no cambian de comportamiento efectivo**. Se pueden ordenar, documentar y testear; una
mejora va detrás de una bandera apagada por defecto, con su test y su medición.

**El número publicado hoy es P = 0,9801. Si al final de la limpieza cambió, la limpieza
está mal, no el número.**
