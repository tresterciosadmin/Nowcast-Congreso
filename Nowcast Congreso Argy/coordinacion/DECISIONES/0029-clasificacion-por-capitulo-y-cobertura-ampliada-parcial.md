# ADR-0029 — Tema por capítulo + ampliar cobertura de temas — PARCIAL, sin crédito de API

**Fecha:** 2026-09-16 · **Estado:** CÓDIGO IMPLEMENTADO y TESTEADO, DATOS
PARCIALES (se cortó por falta de crédito de la API de Anthropic a mitad de
las dos corridas) · **Decide:** Claude, con permiso explícito de Franco (ver
las tres respuestas de la sesión: "Sí, alcance acotado" / "Sí, ampliar
cobertura" / "Sí, córranlo") · **Toca:** `variables/proyecto/src/
{tema_por_capitulo.py (nuevo), tema_por_proyecto.py}`, `datos/proyectos/data/
{proyectos.db, taxonomias.csv}`, `datos/taxonomias/data/asignaciones.csv` ·
**Se relaciona con:** ADR-0027 (composición por capítulos, el consumidor que
necesita este insumo), ADR-0024 (registro único), memoria de sesión
("Activaste el agente sin mi permiso" — esta vez SÍ se preguntó antes)

## Qué se pidió y qué se construyó

Franco autorizó dos tareas pagas (agente LLM) en la misma ronda de preguntas:

1. **Tema por capítulo**, alcance acotado a Ley Bases + los 145 proyectos de
   Diputados con votación en particular (el mismo universo que
   `capitulos_nombre.parquet` ya cubre) — el insumo que le faltaba a
   `composicion_capitulos.simular_capitulos` (ADR-0027) para poder correr
   sobre un proyecto real.
2. **Ampliar la cobertura de temas** a proyectos que TODAVÍA no se votaron
   (hoy sólo cubre el universo votado) — acotado a `fecha_ingreso >=
   2025-01-01` (9.910 proyectos, el universo "reciente/en trámite" que más
   necesita el nowcast).

**Módulo nuevo:** `variables/proyecto/src/tema_por_capitulo.py`. Mismo patrón
barato ya usado dos veces (clasificar por TEXTO, sin PDF): el texto es el
NOMBRE del capítulo (`capitulos_nombre.parquet`), con el `sumario` del
proyecto como CONTEXTO para desambiguar nombres cortos ("Del régimen",
"Disposiciones generales") — resuelto vía el mismo crosswalk
proyecto_id↔denominador que ya usa `tema_por_proyecto.py`, no reimplementado.
Produce `variables/proyecto/data/tema_por_capitulo.parquet` (contrato nuevo,
NO toca `proyecto_taxonomias` ni el registro único: es una granularidad que
esas tablas no tienen). 13 checks, `test_tema_por_capitulo.py`.

**Extensión:** `tema_por_proyecto.py` gana `denominadores_desde(fecha,
sin_clasificar=True)` y la CLI `clasificar --desde-fecha AAAA-MM-DD` — el
`estado` de `proyectos` está enteramente NULL (no sirve como filtro; no se
intentó arreglarlo, fuera de alcance), así que el corte es por
`fecha_ingreso`, más simple y suficiente. 3 checks nuevos,
`test_tema_por_proyecto.py` (24/24).

## Lo que pasó: se acabó el crédito de la API a mitad de las dos corridas

Las dos corridas (`tema_por_capitulo` y `clasificar --desde-fecha`) se
lanzaron EN PARALELO. A las 14:27-14:30 del 16-09, la API empezó a devolver
`400 — Your credit balance is too low`. **No es un bug de este código**: es
la cuenta de Anthropic sin saldo. El código maneja el error como cualquier
otro (resiliencia por fila, no corta el lote) — la consecuencia es que TODO
lo que faltaba clasificar quedó marcado como error, no como pendiente.

**Se cortó la corrida de cobertura ampliada apenas se detectó** (no tenía
sentido seguir generando cientos de errores 400 sin avanzar nada). La de
capítulos ya había terminado su lote (llegó al final de la lista, con la
segunda mitad en error) cuando se notó.

### Estado real de los datos, medido, no estimado

| | universo objetivo | clasificados | cobertura |
|---|---:|---:|---:|
| tema por capítulo | 704 pares (proyecto, capítulo) | **437** | **62,1%** |
| cobertura ampliada (desde 2025-01-01) | 9.910 proyectos | **328** | **3,3%** |

Los 437 capítulos clasificados son reales y usables — no hay nada a medias
en cada fila individual, sólo falta el resto de la lista. Ejemplo real, Ley
Bases: `Capítulo VII — "Consolidación de deuda del sector público nacional"`
→ `ECON.DEUDA` (0,95); `Capítulo IV — "De los Trabajadores independientes
con colaboradores"` → `TRAB.LABOR` (0,85). Distribución de áreas sobre los
437: POLINST (212), ECON (56), CULT (36), DESREG (34), JUST (25) y 9 áreas
más con menos de 20 cada una — razonable para un corpus de leyes ómnibus.

Los 328 proyectos nuevos de cobertura ampliada ya se sumaron al registro
único (`asignaciones.csv`: 9.427 → 10.111 filas) siguiendo el mismo camino
que la corrida de 1.182 proyectos de la sesión anterior:
`taxonomias_backup.py exportar` (2.655 → 3.339 filas respaldadas) y
`registro.py consolidar`.

**Nada se pierde por la interrupción — las dos corridas son idempotentes y
tienen checkpoint.** `tema_por_capitulo.py` guarda cada 25 clasificaciones;
`clasificar_por_titulo` cada 25 también. Re-correr EL MISMO comando, cuando
Franco recargue crédito, retoma exactamente donde se cortó (`solo_faltantes`
es el default en las dos, y ya está probado por tests):

```
python variables/proyecto/src/tema_por_capitulo.py clasificar
python variables/proyecto/src/tema_por_proyecto.py clasificar --desde-fecha 2025-01-01
```

## Por qué no se prendió nada con esto todavía

`tema_por_capitulo.parquet` es un insumo NUEVO, sin ningún consumidor
enganchado (ADR-0027 sigue sin conectar `composicion_capitulos` a un
proyecto real — este ADR sólo agrega el DATO, no el cableado, que sigue
pendiente y es otra decisión de alcance). La cobertura ampliada
(`proyecto_taxonomias`) ya alimenta `RECORD_POR_TEMA`/`TEMA_AUTO` para
cualquier proyecto que tenga taxonomías — con 328 proyectos nuevos, un
puñado de proyectos NO VOTADOS (el caso que antes no tenía tema) empieza a
tener `rec_i^tema` real. No es un cambio de comportamiento del motor: es más
cobertura para un mecanismo que ya estaba prendido.

## Verificación

`variables/proyecto/tests/test_tema_por_capitulo.py` (13 checks, sin red):
dedup por (proyecto_id, capítulo) quedándose con el nombre más largo;
contexto del sumario resuelto vía crosswalk, degrada limpio sin cruce;
clasificación real con clasificador inyectado, usando el sumario para
desambiguar; idempotencia; `--todos`; resiliencia (un capítulo roto no corta
el lote); `--limite`.
`variables/proyecto/tests/test_tema_por_proyecto.py` (+3 checks, 24/24):
`denominadores_desde` filtra por fecha Y excluye lo ya clasificado, con
`sin_clasificar=False` para el caso sin filtrar, degrada limpio sin matches.
`datos/taxonomias/tests/test_registro.py` sigue en 27/27 tras la nueva
consolidación.

## Addendum 2026-09-16 (más tarde el mismo día) — un bug real, encontrado tratando de USAR lo que había

Franco preguntó: *"¿Podemos usar lo que tenemos hasta ahora para recorrer el
modelo y sacar conclusiones sobre la plausibilidad de usar el tema por
capítulo?"* — la respuesta correcta era intentarlo de verdad, no simularlo.
Se armó `evaluacion/baseline/src/validar_leybases_por_capitulos.py`: arma el
roster real de Diputados por capítulo (misma función que usa
`nowcast_puertas.nowcast()` en producción), simula cada capítulo con
`composicion_capitulos` y compara contra lo que REALMENTE pasó en la ronda 1
de Ley Bases (2024-02-06).

**Al correrlo apareció un bug real, no una curiosidad menor.** El numeral de
capítulo se REINICIA en cada título — medido: en Ley Bases, "Capítulo I"
aparece bajo **6 títulos distintos** (I, II, III, V, VI, VIII), y lo mismo
"Capítulo II". La clave que se venía usando en TODO el trabajo del día
—`capitulos_nombre.py` (extracción del PDF) y `tema_por_capitulo.py`
(clasificación)— era `capitulo_num` SOLO, así que estaban fusionando bajo
una misma fila capítulos de partes completamente distintas de la ley (ej.
"Capítulo I" de emergencia pública y "Capítulo I" de régimen laboral,
tratados como si fueran el mismo).

**Corregido en el código, gratis (sin gastar créditos):**
- `capitulos_nombre.extraer_capitulos` ahora trackea el TÍTULO vigente
  (nuevo regex `_RE_TITULO_TEXTO`) y devuelve `(titulo_num, capitulo_num,
  nombre_capitulo)`, no sólo `(capitulo_num, nombre_capitulo)`.
- `tema_por_capitulo.cargar_capitulos`/`clasificar_capitulos` usan
  `(proyecto_id, titulo_num, capitulo_num)` como clave, con un chequeo
  explícito (`KeyError` claro) si se les pasa un `capitulos_nombre.parquet`
  del esquema viejo.
- `capitulos_nombre.parquet` se **regeneró gratis** (usa el caché local de
  PDFs, no la API): 320 → 546 filas — la diferencia es exactamente la
  fusión indebida que se deshizo.
- 15 checks nuevos/actualizados entre los dos módulos (`test_capitulos_nombre.py`
  15/15, `test_tema_por_capitulo.py` 15/15), incluido un test que reproduce
  el bug exacto (mismo `capitulo_num` bajo dos `titulo_num` distintos).

**Consecuencia que SÍ cuesta:** los 437 capítulos clasificados con la clave
vieja quedan **obsoletos** — no se puede confiar en a qué (título, capítulo)
real corresponde cada clasificación, así que no sirven como `previas` para
continuar idempotentemente. Se movieron a
`tema_por_capitulo_OBSOLETO_clave_sin_titulo_2026-09-16.parquet` (no se
borran: quedan como referencia). **Los 437 hay que reclasificarlos desde
cero contra la clave corregida** — eso sí necesita créditos de API, que
siguen en cero.

**Por qué esto es una buena noticia, no sólo una mala.** El bug se encontró
gastando UNA corrida de validación sobre 11 capítulos de un solo proyecto —
antes de escalar a los 9.500+ proyectos que faltan de la otra tarea. Si el
plan hubiera sido "reclasificar todo primero, validar después", el mismo
bug se habría descubierto recién después de gastar el crédito completo en
datos con la clave equivocada.

**No se pudo completar la validación de plausibilidad que Franco pidió**:
sin capítulos correctamente clasificados no hay nada real que simular
todavía. Queda pendiente, bloqueada por crédito de API (para reclasificar) y
no por diseño.

## Lo que queda pendiente

1. **Recargar crédito de la API** — bloqueante para las dos corridas.
2. **Reclasificar `tema_por_capitulo` DESDE CERO** contra la clave corregida:
   **1.084 pares (proyecto, título, capítulo) reales** — más, no menos, que
   los 704 de la clave vieja (separar por título revela capítulos reales
   que antes quedaban tapados bajo la fusión). Los 437 anteriores quedaron
   obsoletos (ver addendum) — no hay atajo, es empezar de nuevo con
   `python variables/proyecto/src/tema_por_capitulo.py clasificar`.
3. **Terminar la cobertura ampliada**: 9.582 proyectos restantes
   (9.910-328) — a este ritmo (~3,5s/llamada) son varias horas de corrida,
   no minutos; queda como una corrida larga a lanzar cuando convenga, no
   necesariamente de una sola vez.
4. **Conectar `composicion_capitulos` a un proyecto real** usando
   `tema_por_capitulo.parquet` — sigue sin hacerse (ADR-0027); ahora la
   CLAVE es correcta, pero no hay ningún dato clasificado con ella todavía.
5. **Correr `validar_leybases_por_capitulos.py` de verdad** (la validación de
   plausibilidad que Franco pidió) una vez que Ley Bases tenga sus capítulos
   reclasificados con la clave corregida.
