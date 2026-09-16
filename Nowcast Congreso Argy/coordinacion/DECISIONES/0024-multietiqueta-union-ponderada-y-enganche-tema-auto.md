> ⚠️ **ENMENDADO por ADR-0028 (16-09-2026).** El PASO 2 de este ADR medía sin
> brazo de control, promediando `ponderada` en probabilidad (no en logit) y
> con `peor_tema` sobre un estimador sesgado — tres problemas de DISEÑO, no de
> ejecución, que el prompt `PROMPT-MULTITEMA-V2.md` señaló. El re-test
> corregido (control + logit + estimador directo de simulación + censo
> completo + bootstrap clusterizado) da un resultado MÁS FUERTE, no
> contradictorio: **ninguna diferencia —incluida "no condicionar por tema"—
> es distinguible de cero en la rama de bloque.** La recomendación práctica
> de este ADR (no activar ninguna regla a nivel bloque) sigue siendo válida;
> lo que cambia es el motivo: no es que las reglas nuevas empeoren, es que
> este nivel no tiene información que ninguna regla pueda aprovechar. Ver
> ADR-0028 para el detalle, y ADR-0026 para dónde SÍ está la ganancia
> (`rec_i^tema`, a nivel legislador, 11,1% menos Brier).

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
`combinar_temas: str = "primaria"` con cuatro modos:

| modo | qué hace | archivo/función |
|---|---|---|
| `primaria` (default) | comportamiento de SIEMPRE: una sola etiqueta (`tema=`) | sin cambios, retrocompatible byte a byte |
| `union` | la ventana condicionada son las actas que comparten **cualquiera** de los temas objetivo — matcheando contra la multietiqueta COMPLETA de cada acta (`todas_ids`), no sólo su primaria | `_match` nuevo dentro de `proyectar_postura` |
| `ponderada` | cada tema objetivo arma SU PROPIO share condicionado (encogido, mismo `k_shrink`) y el resultado es el promedio ponderado por confianza de esos shares ya encogidos | idem |
| `peor_tema` **(agregado 16-09, a pedido de Franco: "probemos algo nuevo")** | mismo cómputo por tema que `ponderada`, pero el resultado final es el **mínimo** de los shares ya encogidos — el tema donde el bloque está más en contra manda, sin ponderar | idem, reusa `area_shares` |

**Por qué estas cuatro y no sólo dos.** El prompt original pedía "al menos
dos"; se implementaron `union` y `ponderada` primero por ser las de semántica
más clara. `ponderada` tiene la propiedad de que con UN solo tema de peso 1.0
da EXACTAMENTE lo mismo que `primaria` — no es una rama aparte, es la
generalización (`test_ponderada_con_un_tema_es_identica_a_primaria`).
**`peor_tema` se agregó el 16-09** después de que PASO 2 diera negativo para
`union`/`ponderada` (ver abajo): Franco pidió más pruebas o algo nuevo antes
de cerrar el tema, y `peor_tema` es la hipótesis "un ómnibus se cae por su
capítulo más resistido" de la tabla original del prompt, barata de agregar
porque reusa el mismo cómputo por área que ya existía para `ponderada` — sólo
cambia la combinación final (`min` en vez de promedio ponderado). Con un solo
tema, `peor_tema` también da EXACTAMENTE `primaria` (mismo test que
`ponderada`, `test_peor_tema_con_un_tema_es_identico_a_primaria`).
**`jerárquica` queda sin implementar**: mirada de cerca, es muy parecida a
`ponderada` con un paso extra de Empirical-Bayes anidado, y no se justificaba
sumar una quinta variante sin que las primeras tres hayan mostrado señal.

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
> `ponderada` en producción sí pesará de verdad. **`peor_tema` no tiene este
> problema**: no pondera, elige el mínimo — así que la falta de confianza por
> etiqueta no lo afecta. Es un punto a favor de probarlo aparte.

### 🔴 Resultado: NEGATIVO. Las TRES reglas nuevas empeoran justo donde tenían que ayudar

**Corrida real, 2.984 actas evaluadas (16 saltadas), seed=7, 353.133 votos
totales por modo** (`evaluacion/baseline/outputs`, reproducible con
`--muestra 3000 --seed 7 --combinar-temas {primaria,union,ponderada,peor_tema}`):

| | `primaria` (hoy) | `ponderada` | `union` | `peor_tema` |
|---|---:|---:|---:|---:|
| Brier global | 0,13634 | 0,13668 | 0,13657 | 0,13670 |
| skill global | 0,1527 | 0,1506 | 0,1512 | 0,1505 |
| **Brier rama de bloque** (n=1.263 votos) | **0,20380** | **0,20569** | **0,20771** | **0,20836** |
| **skill rama de bloque** | **−0,0559** | **−0,0657** | **−0,0762** | **−0,0795** |
| MAE del margen | 0,1382 | 0,1380 | 0,1380 | 0,1381 |

(ordenadas de mejor a peor por skill de la rama de bloque; `primaria` sigue
arriba de las tres)

**Global: prácticamente plano**, exactamente lo que el PASO 0 anticipaba — la
rama de bloque es ~0,36% de los votos, así que cualquier cambio ahí se diluye
a nada en el agregado. **Pero en el subconjunto que el cambio REALMENTE
toca —la rama de bloque, que es donde había que mirar— las TRES reglas nuevas
EMPEORAN el Brier respecto de `primaria`, ninguna lo mejora.**

**`peor_tema` (agregada el 16-09, a pedido de Franco — "probemos algo
nuevo") es la que PEOR sale de las tres**, incluso peor que `union`. No es lo
que se esperaba de la hipótesis "un ómnibus se cae por su capítulo más
resistido": tomar el mínimo entre varios shares ya encogidos empuja
sistemáticamente hacia el extremo pesimista, y sobre una rama que YA es
demasiado extrema para su propio bien (ver §II.5), empujarla más lejos del
extremo correcto —que la mayoría de los proyectos igual se aprueban— es
exactamente lo que le hace peor, no mejor. Es un resultado que vale la pena
tener presente para cualquier futura variante "peor caso": en este motor,
pesimismo ⧣ precisión.

**Por qué, la hipótesis más plausible (las tres reglas):** la rama de bloque
ya es la parte más débil del motor (skill NEGATIVO incluso con `primaria`,
consistente con lo medido en §II.5 de `FORMULA-COMPLETA.md` — "mandar gente
ahí no es un refugio conservador: es empeorarla"). Sobre una muestra ya chica
(1.263 votos), cualquier transformación que se aleje de "una sola etiqueta,
sin drama" agrega ruido a una estimación que ya tenía poca base: `union` lo
hace sumando actas de otros temas, `ponderada` promediando con peso igual
(limitación de `todas_ids`, ver más arriba), `peor_tema` empujando al extremo.

**Esto es la doctrina de este proyecto funcionando, no un fracaso de la
tarea:** la misma familia de resultado que el sobre tablas (§III.A.5) y el
carácter del dictamen en el ADR-0016 — una hipótesis razonable (o tres) que
el backtest walk-forward rechaza. **Se reporta como corresponde: no se
fuerza, ni siquiera después de probar "algo nuevo".**

**Recomendación: NO activar `TEMA_AUTO` con `COMBINAR_TEMAS != "primaria"`
en base a esta medición — con NINGUNA de las cuatro reglas disponibles.** Si
algún día `proyecto_taxonomias` tiene datos reales (con confianza por
etiqueta, no la aproximación de peso igual que usa `ponderada` en esta
validación — nota: `peor_tema` no tiene ese problema, no pondera), vale la
pena remedir `ponderada` en particular — pero con la evidencia de hoy, la
regla ganadora sigue siendo no tocar nada.

**Limitación de esta medición, honesta:** muestra de 3.000 de ~6.091 actas
totales (seed único), no el censo completo. La dirección del resultado (las
tres reglas peores que primaria, en el mismo sentido, con `peor_tema`
consistentemente la peor) es uniforme entre las tres, lo que pesa a favor de
que sea señal real y no ruido de una sola corrida — pero un censo completo
(como el que se hizo para el guard de era, ADR-0018) sería la confirmación
definitiva si esto se retoma.

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

1. ~~Correr `agente_taxonomias.clasificar_lote`~~ **RESUELTO el 16-09 — con un
   matiz, y ya corrido.** La API key SÍ estaba disponible (error de la entrada
   anterior de este ADR: ver la corrección en `tema_por_proyecto.py`). Pero
   `clasificar_lote` (la vía PDF) tiene un cuello de botella real: sólo
   71/115.495 proyectos (0,06%) tienen `pdf_url`. Se clasificó en cambio por
   TÍTULO (`clasificar_por_titulo`, más barato, mismo patrón que
   `tema_por_acta.py`) **el universo VOTADO completo: 1.182 de 1.182
   denominadores, 2.655 taxonomías guardadas, 0 errores.** De los ~1.070
   proyectos con al menos una etiqueta sustantiva, **76,5% tiene ≥2** —
   prácticamente idéntico al 76,1% medido a nivel ACTA en el PASO 0: el
   patrón multietiqueta se confirma en las dos granularidades, con dos
   corridas independientes del agente. Verificado de punta a punta con Ley
   Bases real (no sintético): `POLINST(0,95)/DESREG(0,85)/ECON(0,75)` desde su
   propio `sumario`, consistente con lo que ya daba la clasificación por
   título de acta en el PASO 0. Respaldado en `datos/proyectos/data/
   taxonomias.csv` (`taxonomias_backup.py exportar`, sobrevive a
   `migrar_ckan.py`) y consolidado en el registro único
   (`datos/taxonomias/data/asignaciones.csv`, ahora con nivel `proyecto`
   además de `acta`: 9.427 filas, 4.304 objetos).
2. ~~Decidir la regla de combinación con los números de PASO 2~~ **RESUELTO,
   dos veces: ninguna de las CUATRO reglas gana** (se sumó `peor_tema` el
   16-09 a pedido de Franco — "probemos algo nuevo" — y salió la PEOR de las
   tres nuevas, no la mejor). El código queda (tested, documentado, reusable
   si cambian las condiciones — por ejemplo con confianza real por etiqueta,
   que ahora sí existe para el universo votado gracias al punto 1), pero no
   hay recomendación de activar nada. Sigue siendo decisión de Franco si
   quiere confirmar con el censo completo antes de cerrar el tema del todo.
3. **No se prende nada en publicación sin aprobación de Franco** — las tres
   banderas (`TEMA_AUTO`, `COMBINAR_TEMAS`, y el default de
   `combinar_temas` en `proyectar_postura`) quedan como están hasta entonces.
