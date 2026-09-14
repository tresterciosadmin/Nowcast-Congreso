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

**Por qué no lo arreglé yo:** `variables/proyecto/` (origen_lider.py) es
módulo del motor — está en la lista de restricción dura. Cambiar la lógica de
match cambia `origen` para las filas que hoy caen en DESCONOCIDO, lo que
puede mover el downstream (aunque medí que `nowcast_puertas.py` no lee
`origen_por_acta.parquet` de forma directa para el número publicado — sí lo
hace `puerta_a`/`puerta_d`, no llegué a confirmar eso al 100%). Necesita flag
+ test + medición, no una sesión de una hora sin vos.

**Lo que yo haría:** en vez de exact-match, agregar un fallback por
`apellido + primera inicial del nombre` (o similar) cuando el exacto falla,
SOLO si es no ambiguo (un único legislador con ese apellido+inicial en la
ventana de años). Medirlo contra los ~4.263 casos actuales antes de
integrarlo, detrás de un flag.

**Estado en que dejé el repo:** nada tocado en `variables/proyecto/`. Solo
diagnóstico.

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

## 3. Urgentes que dejé en `URGENTE.md`, sin tocar (necesitan tu decisión)

- **D.** δ en el Senado: si conviene redefinir el carácter del dictamen desde
  la disidencia en vez del carácter (213 firmas "EN DISIDENCIA" de 18.105).
  Es cambio de definición de una variable del motor → ADR. No lo toqué.
- **F.** A qué linaje va el bloque personal de Daer (88,9% massismo vs 90,0%
  peronismo federal, demasiado parejo). Una línea en `LINAJE_VENTANAS`
  (`variables/bloque/`, motor) — la dejo para vos.
- **5.** Roster de jefes de bloque: 4 filas para agregar/corregir (Naidenoff,
  Di Tullio, Cicoliani) y una decisión de fondo (¿la columna `bloque` mide el
  bloque o el interbloque? — afecta a Massa/UNA y a Camaño/Federal-UNA). Todo
  el detalle ya estaba en `URGENTE.md`, no lo dupliqué acá.
- **E** (URGENTE, distinto de la tarea E que me diste): clasificación de tema
  por acta frenada por créditos de API — no corrí nada que consuma la API
  paga, como me pediste. Sigue frenado.

## 4. Lo que SÍ resolví y ya está commiteado (no necesita tu decisión)

- **Ítem M de URGENTE.md** (β estimado con datos viejos, antes de que el
  parser recuperara los `desconocido`): la corrida completa del 14-09 ya lo
  resolvió — verificado que `desconocido = 0%` en ambas cámaras y que
  `unico`/`mayoria` de Diputados quedaron en 76.333/36.065, los mismos
  números que el ítem esperaba. Lo borré de `URGENTE.md`.
- El test `test_agarra_el_tramite_borrado` y el fix de `REGENERAR.ps1` — ver
  el commit `49d41da`, P no se movió (medido, no supuesto).
