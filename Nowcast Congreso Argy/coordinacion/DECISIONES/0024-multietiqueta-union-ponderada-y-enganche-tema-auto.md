# ADR-0024 — Multietiqueta: `union`/`ponderada` en `proyectar_postura`, y el enganche `TEMA_AUTO`

**Fecha:** 2026-09-15 · **Estado:** IMPLEMENTADO y **PROBADO — NO SE RECOMIENDA
ACTIVAR** (PASO 2 dio negativo: ver abajo). Banderas APAGADAS por defecto
(`TEMA_AUTO=0`, `combinar_temas='primaria'`) y se quedan así. · **Decide:** Claude,
con el mandato de `coordinacion/PROMPT-MULTIETIQUETA.md` (Franco: "seguí el
camino que consideres mejor... resolvé todo lo que puedas") · **Toca:**
`variables/bloque/src/bloque.py`, `variables/proyecto/src/tema_por_proyecto.py`
(nuevo), `modelo/ensemble/src/nowcast_puertas.py`,
`evaluacion/baseline/src/baseline_voto_individual.py` · **Se relaciona con:**
ADR-0016 (doctrina de la parte al todo — dónde entra el término), la medición
PASO 0 en `ESTADO-DEL-PROYECTO.md` (2026-09-15)

## Contexto

El PASO 0 midió dos cosas que reordenan esta tarea:

1. **La multietiqueta es la norma, no la excepción.** 61,2% de las actas
   votadas clasificadas tienen ≥2 etiquetas sustantivas.
2. **El colapso a una sola etiqueta ocurre en dos lugares agua abajo**
   (`tema_por_acta._elegir_primaria` y `bloque.proyectar_postura._match`), pero
   **el problema real es OTRO, previo a los dos**: `tema` en
   `nowcast_puertas.nowcast()` es un parámetro `--tema` MANUAL. No existe
   ningún `proyecto_id -> tema` en la ruta de producción — `REGENERAR.ps1` no
   lo pasa. Cualquier regla de combinación que se construya en `bloque.py`
   queda huérfana sin ese enganche.

Este ADR resuelve las dos cosas juntas, porque una sin la otra no sirve:
la regla de combinación (qué hacer con varios temas) y el enganche (de dónde
salen esos temas para un proyecto real).

## Decisión — la regla de combinación (`combinar_temas`)

`proyectar_postura` (`variables/bloque/src/bloque.py`) gana un parámetro
`combinar_temas: str = "primaria"` con tres modos:

| modo | qué hace | archivo/función |
|---|---|---|
| `primaria` (default) | comportamiento de SIEMPRE: una sola etiqueta (`tema=`) | sin cambios, retrocompatible byte a byte |
| `union` | la ventana condicionada son las actas que comparten **cualquiera** de los temas objetivo — matcheando contra la multietiqueta COMPLETA de cada acta (`todas_ids`), no sólo su primaria | `_match` nuevo dentro de `proyectar_postura` |
| `ponderada` | cada tema objetivo arma SU PROPIO share condicionado (encogido, mismo `k_shrink`) y el resultado es el promedio ponderado por confianza de esos shares ya encogidos | idem |

**Por qué estas dos y no las cuatro de la tabla del prompt.** El prompt pedía
implementar "al menos dos". `union` y `ponderada` son las dos con semántica
más clara y menos partes móviles — `ponderada` además tiene la propiedad de
que con UN solo tema de peso 1.0 da EXACTAMENTE lo mismo que `primaria`: no es
una rama aparte, es la generalización (verificado en test,
`test_ponderada_con_un_tema_es_identica_a_primaria`). **`peor capítulo` y
`jerárquica` quedan sin implementar, no descartadas**: `peor capítulo` es un
caso particular fácil de agregar sobre la misma infraestructura (tomar el
`min` en vez del promedio ponderado) si `union`/`ponderada` no alcanzan;
`jerárquica` (Empirical-Bayes por tema y DESPUÉS combinar) es, mirado de
cerca, muy parecida a `ponderada` con un paso extra — no se justificaba
triplicar la superficie de test sin evidencia de que hiciera falta.

**Dónde vive en la doctrina (ADR-0016).** La combinación ocurre DENTRO de
`proyectar_postura`, por bloque, antes de que la simulación cuente votos — es
información que un legislador procesa (qué temas trata el proyecto), no una
corrección al agregado. Ningún término se mueve del lado derecho de la
simulación.

## Decisión — el enganche `TEMA_AUTO`

`variables/proyecto/src/tema_por_proyecto.py` (nuevo) es un módulo de
**LECTURA, no de clasificación**. La clasificación ya existe y está completa:
`agente_taxonomias.clasificar_lote()` baja el PDF de cada proyecto, lo
clasifica (multietiqueta, LLM) y escribe en `proyecto_taxonomias`
(`datos/proyectos/data/proyectos.db`) — **hoy tiene 0 filas** porque nadie la
corrió (necesita `ANTHROPIC_API_KEY` + red; no disponibles en la sesión que
escribió este ADR). Es un pendiente OPERATIVO, no de diseño.

Lo que faltaba, y sí se pudo construir sin red: **el cruce y la lectura.**
`temas_de_proyecto(proyecto_id=...)` resuelve `proyecto_id` (HCDN, el que usa
el motor) contra `denominador` (NNNN-X-AAAA, el que usa `proyectos.db`) vía
`datos/expedientes/data/clean/expedientes.parquet` (`exp_diputados` ==
denominador para el 100% de las 114.365 filas, verificado) y devuelve la
multietiqueta sustantiva ordenada por confianza.

`nowcast_puertas.nowcast()` llama a `_tema_auto(proyecto_id)` **sólo si el
llamador no pasó `tema` a mano** (lo manual siempre gana) y sólo si
`TEMA_AUTO=1`. Con `combinar_temas='primaria'` (default de `COMBINAR_TEMAS`),
usa el área de mayor confianza como `tema=` — el camino más parecido a lo
manual de siempre. Con `union`/`ponderada`, pasa la multietiqueta completa.

**Por qué las banderas quedan apagadas, y no es lo mismo apagar TEMA_AUTO que
apagar las otras banderas de este archivo (BETA_DICTAMEN, GUARD_ERA, ...).**
Esas se apagan por precaución sobre un término YA MEDIDO. Acá el apagado es
más fuerte: el DATO no existe (`proyecto_taxonomias` vacía), así que hoy
prender `TEMA_AUTO=1` es un no-op verificado —`P(aprobación) = 0,9801`, el
control de siempre, idéntico con la bandera prendida sobre un proyecto real
(`HCDN294440`)— y con un dato sintético insertado y borrado en la misma
prueba, se confirmó que el enganche efectivamente llega hasta
`proyectar_postura` (`tema=AMB` apareció en el log de condicionamiento).

## PASO 2 — validación empírica

`evaluacion/baseline/src/baseline_voto_individual.py` gana `--combinar-temas
{primaria,union,ponderada}` (default `primaria`, retrocompatible). Para
`union`/`ponderada` usa la multietiqueta YA CLASIFICADA de cada acta evaluada
(`tema_por_acta.todas_ids`) como su propio tema objetivo — no necesita
`proyecto_taxonomias` ni red: el histórico ya tiene la señal.

> **Limitación honesta:** `todas_ids` no guarda la confianza POR etiqueta
> (sólo la de la primaria). `ponderada` sobre el histórico real usa peso
> IGUAL para todas las sustantivas de cada acta — es la aproximación
> disponible sin re-consultar al agente; cuando `TEMA_AUTO` tenga datos reales
> de `proyecto_taxonomias` (que sí trae confianza por taxonomía), la
> `ponderada` en producción sí pesará de verdad.

### 🔴 Resultado: NEGATIVO. `union` y `ponderada` empeoran justo donde tenían que ayudar

**Corrida real, 2.984 actas evaluadas (16 saltadas), seed=7, 353.133 votos
totales por modo** (`evaluacion/baseline/outputs`, reproducible con
`--muestra 3000 --seed 7 --combinar-temas {primaria,union,ponderada}`):

| | `primaria` (hoy) | `union` | `ponderada` |
|---|---:|---:|---:|
| Brier global | 0,13634 | 0,13657 | 0,13668 |
| skill global | 0,1527 | 0,1512 | 0,1506 |
| **Brier rama de bloque** (n=1.263 votos) | **0,20380** | **0,20771** | **0,20569** |
| **skill rama de bloque** | **−0,0559** | **−0,0762** | **−0,0657** |
| MAE del margen | 0,1382 | 0,1380 | 0,1380 |

**Global: prácticamente plano**, exactamente lo que el PASO 0 anticipaba — la
rama de bloque es ~0,36% de los votos, así que cualquier cambio ahí se diluye
a nada en el agregado. **Pero en el subconjunto que el cambio REALMENTE
toca —la rama de bloque, que es donde había que mirar— los dos modos nuevos
EMPEORAN el Brier respecto de `primaria`, no lo mejoran.** `union` es el
peor (+0,0039, skill cae de −0,056 a −0,076); `ponderada` empeora menos
(+0,0019) pero sigue sin ganarle a `primaria`.

**Por qué, la hipótesis más plausible:** la rama de bloque ya es la parte más
débil del motor (skill NEGATIVO incluso con `primaria`, consistente con lo
medido en §II.5 de `FORMULA-COMPLETA.md` — "mandar gente ahí no es un refugio
conservador: es empeorarla"). Sobre una muestra ya chica (1.263 votos),
`union` suma actas de OTROS temas relacionados que diluyen la señal
específica; `ponderada` promedia con PESO IGUAL entre temas (limitación de
`todas_ids`, ver más arriba) cuando en la realidad un proyecto casi siempre
tiene un tema que manda y otros que son ruido de fondo — promediarlos parejo
es, en la práctica, agregar ruido a una estimación que ya tenía poca base.

**Esto es la doctrina de este proyecto funcionando, no un fracaso de la
tarea:** la misma familia de resultado que el sobre tablas (§III.A.5) y el
carácter del dictamen en el ADR-0016 — una hipótesis razonable que el
backtest walk-forward rechaza. **Se reporta como corresponde: no se fuerza.**

**Recomendación: NO activar `TEMA_AUTO` con `COMBINAR_TEMAS != "primaria"`
en base a esta medición.** Si algún día `proyecto_taxonomias` tiene datos
reales (con confianza por etiqueta, no la aproximación de peso igual que usa
esta validación), vale la pena remedir — pero con la evidencia de hoy, la
regla ganadora sigue siendo no tocar nada.

**Limitación de esta medición, honesta:** muestra de 3.000 de ~6.091 actas
totales (seed único), no el censo completo. La dirección del resultado
(ambos modos peores que primaria, en el mismo sentido) es consistente entre
`union` y `ponderada`, lo que pesa a favor de que sea señal real y no ruido
de una sola corrida — pero un censo completo (como el que se hizo para el
guard de era, ADR-0018) sería la confirmación definitiva si esto se
retoma.

## Verificación

- `variables/bloque/tests/test_bloque_v3_multietiqueta.py` — 8 checks: la
  generalización `ponderada`↔`primaria`, que `union` lee `todas_ids` y no sólo
  la primaria (el test que hubiera atrapado el colapso si `union` estuviera
  mal escrito), el pool de dos temas, el promedio ponderado exacto, la caída a
  incondicional, y los `ValueError` claros.
- `variables/proyecto/tests/test_tema_por_proyecto.py` — 12 checks: el cruce
  proyecto_id↔denominador, multietiqueta ordenada por confianza, degradación
  limpia sin datos.
- `modelo/ensemble/tests/test_tema_auto.py` — 9 checks: la bandera apagada es
  no-op total, sin proyecto_id es no-op, proyecto sin taxonomías es no-op, y
  los dos modos (`primaria`/`union`) resuelven bien con datos sintéticos.
- Las suites existentes (`test_bloque.py`, `test_bloque_v2.py`,
  `test_bloque_origen.py`, `test_bloque_linaje_senado.py`,
  `test_nowcast_puertas.py` 49/49) pasan sin cambios: el comportamiento por
  defecto es byte a byte el de antes.
- Corrida real: `P(aprobación) = 0,9801` con `TEMA_AUTO=0` y con `TEMA_AUTO=1`
  sobre la base vacía — el número publicado no se movió.

## Addendum — `proyecto_taxonomias` también se suma al registro único

`datos/taxonomias/src/registro.py` (el registro único, ver su propio docstring
sobre por qué existe) tenía `NIVELES = ("acta", "proyecto")` desde el principio,
pero su única fuente de nivel `proyecto` era `datos/proyectos/data/taxonomias.csv`
— un respaldo legacy que nunca se llenó (0 filas). Se agregó
`proyecto_taxonomias_db` como fuente nueva, leyendo la tabla VIVA
`proyecto_taxonomias` directamente. Hoy es un no-op (la tabla está vacía, mismo
motivo que el resto de este ADR): el día que `clasificar_lote` corra, `python
datos/taxonomias/src/registro.py consolidar` empieza a traer proyectos al
registro único sin ningún código nuevo. Tests: 3 checks nuevos en
`datos/taxonomias/tests/test_registro.py` (27/27 en total).

## Lo que queda pendiente, y de quién es cada pendiente

1. **Correr `agente_taxonomias.clasificar_lote`** — necesita
   `ANTHROPIC_API_KEY` + red, tarea operativa de Franco (o de una sesión con
   esas credenciales). Sin esto, `TEMA_AUTO=1` sigue siendo un no-op sin
   importar qué tan bien esté escrito el resto.
2. ~~Decidir la regla de combinación con los números de PASO 2~~ **RESUELTO
   por la medición de arriba: ninguna de las dos gana.** El código queda
   (tested, documentado, reusable si cambian las condiciones — por ejemplo con
   confianza real por etiqueta), pero no hay recomendación de activar nada.
   Sigue siendo decisión de Franco si quiere confirmar con el censo completo
   antes de cerrar el tema del todo.
3. **No se prende nada en publicación sin aprobación de Franco** — las tres
   banderas (`TEMA_AUTO`, `COMBINAR_TEMAS`, y el default de
   `combinar_temas` en `proyectar_postura`) quedan como están hasta entonces.
