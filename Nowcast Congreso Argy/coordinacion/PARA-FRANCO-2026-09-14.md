# PARA FRANCO — sesión autónoma 2026-09-14 (1h, Claude solo)

Todo lo de acá necesita tu criterio. Nada de esto se tocó sin tu decisión.

## 1. Caída del match autor→bloque: 89,8% hoy, 96,1% el 14-08 — diagnóstico, no arreglado

**Qué encontré:** `variables/proyecto/data/features_proyecto.parquet` da hoy
`match_autor` = 89,8% (4.263 sin match de 41.871), verificado contra el disco.
El 96,1% que se comparaba en la tarea que me diste sale de una entrada de
`ESTADO-DEL-PROYECTO.md` del **2026-08-14** — no es una medición reciente. El
número YA estaba en 89,79% en el último commit real antes de mi sesión
(`25ff5ca`, 09-11), así que **la caída NO es de la corrida del 14-09**: viene
de un mes de crecimiento de datos (CKAN pasó de un tamaño menor a 114.365
proyectos) sin que nadie volviera a mirar el match rate hasta ahora.

**Causa que encontré, con un caso concreto (Pitrola):**
- `expedientes.parquet` trae `autor = "PITROLA, NESTOR"`.
- `legisladores.csv` trae `nombre = "PITROLA Néstor Antonio"`.
- `_norm()` en `origen_lider.py` normaliza los dos a mayúsculas sin acentos,
  pero el match es por **igualdad exacta de string**: `"PITROLA NESTOR"` ≠
  `"PITROLA NESTOR ANTONIO"`. El segundo nombre/apellido compuesto rompe el
  match aunque la persona sea inequívoca.
- El patrón se repite con nombres conocidos y sin ambigüedad (Massot, Banfi,
  Ritondo, Biella), no son casos raros.

**Y hay una segunda señal, no exploré si es la misma causa o se suma:** el
match cae fuerte en 2020-2023 (81-83%) contra 93-96% en 2016-2019 y 92% en
2025-2026. 2020-2023 es el período con el "hueco de Diputados" que ya está
documentado en `datos/canonica/` (fuente distinta/menos completa para esos
años). Puede ser la misma causa (nombres con formato distinto según la
fuente) o una segunda causa independiente. **No lo separé por falta de
tiempo.**

**ACTUALIZACIÓN 2026-09-14 (vos ya de vuelta): implementado, testeado y medido — falta tu OK para prenderlo por defecto.**

`nowcast_puertas.py` SÍ lee `origen_por_acta.parquet` (confirmado: lo usa para
condicionar `proyectar_postura` y `alineacion_individual` por el `origen` del
proyecto). Así que esto sí podía mover P.

Se implementó `_match_prefijo` en `origen_lider.py`: cuando el nombre exacto
no está en el padrón, matchea por PREFIJO DE TOKENS ("PITROLA NESTOR" calza
con "PITROLA NESTOR ANTONIO") **solo si es el único candidato** con ese
primer token en todo el padrón — ambiguo (dos legisladores, mismo apellido,
mismo prefijo de nombre) no matchea nunca, se queda DESCONOCIDO. Detrás de
`MATCH_AUTOR_FUZZY=1`, apagado por defecto. 5 tests nuevos (35/35 OK).
Commit `edfedc9`.

**Medido con el flag prendido** (backup de los outputs, regenerados, medidos,
restaurados al estado flag-off — nada de esto quedó commiteado con el flag
en on):
- `match_autor`: 89,8% → **97,4%** (4.263 → 1.065 sin match)
- `origen_por_acta.parquet`: 82 de 5.998 actas pasan de DESCONOCIDO a un
  origen resuelto (2.664 → 2.582 DESCONOCIDO)
- **P(aprobación) recalculado con el panel completo: 0,9801 → 0,9801, IDÉNTICO**
  (no solo `verificar_regeneracion.py` — corrí `nowcast_puertas_html.py` de
  nuevo con el origen nuevo y comparé el JSON completo)
- Suite completa: 41/41 passed

**RESUELTO — dijiste "dale, prendelo".** Flag prendido por defecto,
`features_proyecto.parquet` y `origen_por_acta.parquet` regenerados, panel
recalculado: P sigue en 0,9801 (41/41 tests). Ver el commit de esta sesión con
mensaje que empieza "flip".

---

## 2. Actas gemelas "sin fecha" (35 pares) — caracterizadas, no descartadas

**Qué encontré:** el archivo es `datos/canonica/outputs/actas_gemelas_2026-09-06.csv`
(no hay uno más nuevo; no corrí `-ConCanonica` en esta sesión). De los 35
pares marcados `INDICIO` (sin fecha, solo mismo recuento de votos):

- **33 de 35 involucran a `manual_2026`**, que **ya está fuera del pipeline**
  por defecto desde el 06-09 (`MANUAL_2026=1` para reactivarlo). O sea que
  estos 33 pares **no tienen impacto hoy**: la fuente con la que colisionan
  ni siquiera entra a la canónica.
- Y dentro de esos 33, el patrón es un falso positivo previsible: una sola
  acta de `manual_2026` (ej. `ley_glaciares`, un solo registro sin fecha)
  matchea contra **8 actas distintas** de `argentinadatos` con el mismo
  `n_votos=72` (el Senado completo) — porque en una sesión con varios
  proyectos votados, TODAS las actas de esa sesión tienen el mismo total de
  votantes. El recuento solo no alcanza para desambiguar.
- Quedan **2 pares reales**: `argentinadatos:senado:2770` vs
  `decada_votada:sen:1805` (ambos con manual_2026 de por medio también, pero
  el par argentinadatos↔decada_votada existe independientemente). No llegué
  a confirmar si `decada_votada` se deduplica en vivo contra argentinadatos
  hoy o si solo se usó como semilla de arranque (ADR-0002 dice que no se
  depende en vivo, pero no verifiqué el flujo exacto de `build.py`).

**Criterio que propongo** (no lo apliqué): el fallback "sin fecha, mismo
recuento" es demasiado débil cuando hay múltiples votaciones el mismo día con
la misma asistencia. Subir la barra: exigir además coincidencia de
afirmativos/negativos/abstenciones (no solo el total), o directamente sacar
el fallback sin-fecha para pares donde uno de los dos lados tiene MÁS de una
acta candidata con el mismo recuento en la ventana de fechas plausible.

**Estado:** caracterizado, nada descartado ni fusionado.

---

## 3. Lo que decidiste hoy y ya está aplicado — con dos cosas que quedaron abiertas

- **D (disidencia = minoría en el Senado): código y tests listos (ADR-0022),
  datos NO regenerados todavía.** `parser_od.py::a_filas` ya reclasifica; 61/61
  OK. Para que llegue a `beta_dictamen.json` del Senado hace falta re-correr
  `construir_firmas.py` en las dos cámaras, y esta máquina no tiene el caché
  de PDFs (`Archivos_Borrar/od_pdf/`, local, no viaja por git): sería una
  descarga de ~1.761 Órdenes del Día desde cero. **No la lancé** — comando
  listo en `URGENTE.md` D. Si querés que la corra igual (puede tardar bastante
  más que los 60-90 min que tardaría con el caché puesto), decímelo. Si preferís
  correrla vos con el caché que ya tenés, también sirve.

- **F (Daer → massismo): aplicado y medido.** `entity_resolution.py` (mapa
  `LINAJE`), más un parche quirúrgico a mano en las 4 filas que ya existían
  (`padron_diputados.csv`, `padron_diputados_historico.csv` ×2,
  `legislador_bloques.parquet`) porque **correr el reconstructor completo del
  padrón dio un resultado raro que no tiene que ver con este cambio** — ver el
  punto siguiente. P recalculado: 0,9801, sin cambios.

- **5 (roster de jefes): RESUELTO por completo.** Naidenoff (hasta 2021→2023),
  Di Tullio reemplaza a Fernández Sagasti (Senado), "medimos bloque, no
  interbloque" confirmado, y Ciciliani/Binner con el corte 2015-12-09/10 que
  confirmaste. Único punto vivo del roster: DEL CAÑO (Frente de Izquierda),
  sin fuente que dé sus tramos — queda en `URGENTE.md` 5, no es urgente.

- **E (créditos de API): la dejé frenada, como pediste.** Medido offline (sin
  tocar la API), en `URGENTE.md` E: **faltan 1.960 actas** por la ruta
  `expedientes` (CKAN, la que usa `tema_por_acta.py` por defecto) o **2.915**
  por la ruta `canonica` (universo más amplio, incluye 2020+). El pipeline de
  guardado está sano: las 3.083 actas ya clasificadas están **las 3.083** en
  `datos/taxonomias/data/asignaciones.csv`, sin ninguna perdida.

## 4bis. RESUELTO — el "número raro" de `padron_diputados_historico.py`

Causa: el archivo se regeneró por última vez el 09-06; `alias_legislador_id.csv`
(el merge de 143 pares de `legislador_id` duplicados) se creó el 09-07, un día
después. Verificado: **108 de esos 143 pares tenían los DOS ids presentes como
legisladores separados** en el archivo viejo. Es deduplicación, no pérdida.
Regenerado de punta a punta (commit `25591ed`): 6.124 filas / 1.952
legisladores, `--verificar` en 0 controles fallidos, P sin cambios.

## 4. Lo que SÍ resolví y ya está commiteado (no necesita tu decisión)

- **Ítem M de URGENTE.md** (β estimado con datos viejos, antes de que el
  parser recuperara los `desconocido`): la corrida completa del 14-09 ya lo
  resolvió — verificado que `desconocido = 0%` en ambas cámaras y que
  `unico`/`mayoria` de Diputados quedaron en 76.333/36.065, los mismos
  números que el ítem esperaba. Lo borré de `URGENTE.md`.
- El test `test_agarra_el_tramite_borrado` y el fix de `REGENERAR.ps1` — ver
  el commit `49d41da`, P no se movió (medido, no supuesto).
