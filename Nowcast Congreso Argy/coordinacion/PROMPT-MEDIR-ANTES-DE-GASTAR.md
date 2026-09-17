# Prompt para Claude Code — medir antes de gastar: ¿vale la pena ampliar cobertura?

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino**. Franco es dueño del producto y de la
metodología.

## 🔴 Regla dura de esta sesión: NO se gasta un centavo de API

**Ninguna llamada al agente clasificador. Ninguna.** Esta sesión existe para producir los
números con los que Franco va a decidir si vale la pena gastar — no para gastar.

Si en algún momento te parece que hace falta clasificar algo para responder una pregunta,
**la respuesta correcta es estimar con lo que ya está clasificado y decir el supuesto**, no
correr el agente. Si algo es genuinamente imposible de estimar sin clasificar, decilo y
dejalo como pendiente con el costo estimado.

## De dónde viene esto

ADR-0029 dejó tres tareas pagas pendientes y **ya midió que una de ellas compra menos de lo
que parecía**: de los 160 proyectos con votación en particular en Diputados, sólo 9 declaran
título/capítulo en el acta, y **sólo Ley Bases tiene resultado a nivel capítulo**. Clasificar
los 779 pares restantes no resolvería el problema de $n$.

Franco pidió explícitamente: *"No ampliemos cobertura aún. Debemos saber si vale la pena
realmente ampliarla antes de gastar en eso."*

---

# FASE A — ¿Vale la pena ampliar la cobertura de temas?

## A0. El corte que ordena todo: votado vs. no votado

**Esto va primero porque cambia qué métrica aplica a cada mitad.**

La tarea pausada de ADR-0029 (`clasificar --desde-fecha 2025-01-01`, 9.582 proyectos
restantes) es sobre **proyectos que todavía no se votaron**. Por definición **no aportan ni
un voto al backtest**, así que clasificarlos **no puede mover el Brier histórico**. Su valor
es de producto: poder nowcastear un proyecto en trámite. **No intentes medirlo con Brier —
sería medir la cosa equivocada y dar un número que parece riguroso y no lo es.**

Entonces separá el universo sin tema en dos y medí cada mitad con lo que corresponde:

| mitad | qué mide | métrica |
|---|---|---|
| **actas VOTADAS sin tema** | cuánto mejoraría el modelo | cota de Brier |
| **proyectos NO votados sin tema** | cuánto mejora el producto | cobertura, no Brier |

Reportá los dos tamaños. La bitácora dice que la cobertura de tema está en **51-57%**;
quiero saber exactamente cuántos votos y cuántas actas quedan afuera del lado votado.

## A1. El descuento que casi siempre se olvida: cuánto de lo nuevo sería AUX

De lo **ya clasificado**, ¿qué fracción salió `AUX.*` (homenaje, trámite, sin clasificar)?

Eso es un **descuento directo** sobre cualquier expansión: los AUX no condicionan nada
—`proyectar_postura` cae a incondicional con ellos— así que esa fracción del gasto **compra
cero**. Si el 40% de lo clasificado es AUX, el 40% de la ampliación es plata tirada.

Y es estimable hoy, sin clasificar nada. Reportalo por separado para el universo votado y
para el reciente, si la mezcla difiere.

## A2. ¿El 11,06% es uniforme o concentrado?

El ADR-0026 midió +11,06% de Brier sobre los 318.564 votos con tema. **Extrapolar ese número
a la cobertura nueva sólo es válido si la ganancia es pareja.** Cortá la ganancia por:

- **área temática** (¿viene de POLINST y ECON, que son las más frecuentes, o está repartida?)
- **cantidad de áreas por voto** (el ADR ya reporta 9,8% con 1 área y 39,9-59,8% con 5+, con
  $n$ chico — verificá si eso aguanta)
- **era y cámara**

Si la ganancia está concentrada en un tipo de proyecto, decilo: **la extrapolación sería
inválida y el número honesto es más bajo.**

## A3. La cota superior, dicha como cota

Con A0, A1 y A2, estimá **cuánto podría mejorar el Brier global si clasificáramos todo lo
VOTADO que hoy no tiene tema**. Presentalo explícitamente como **cota superior optimista**:
supone que los votos nuevos ganan lo mismo que los actuales, que es justamente lo que A2
pone en duda.

## A4. El costo real, en plata

Contá los llamados que harían falta y estimá el costo:

- cuántos ítems (proyectos / actas) quedan sin clasificar en cada universo;
- tokens aproximados por llamada — **medilo sobre los prompts reales del agente**
  (`agente_taxonomias.py`: system prompt + lista controlada + reglas de frontera + el título),
  no lo inventes;
- el precio vigente del modelo que usa el agente.

**Si no podés verificar el precio, decí el supuesto y dejá la cuenta parametrizada** para que
Franco la ajuste. Un número inventado es peor que una fórmula con el precio como variable.

---

# FASE B — La reconstrucción por rango de artículos (gratis, y es la que puede cambiar todo)

ADR-0029 la lista como camino abierto y **nadie la exploró**. Es lo único que podría romper
el techo de $n=3$ para validar `composicion_capitulos`, y no cuesta API.

**La idea:** las actas de votación en particular dicen el rango de artículos
(`"ARTS. 208 AL 214"`). El PDF de la Orden del Día tiene los artículos de cada capítulo. Si
se cruzan, se obtiene **resultado real por capítulo sin depender de que el acta declare el
capítulo** — que es exactamente la limitación que hoy deja el $n$ en 3.

**Qué hacer:**

1. Medí cuántas actas de votación en particular traen un **rango de artículos parseable** en
   el título. `votacion_por_articulo.py::extraer_titulo_capitulo` ya parsea parte de esto —
   mirá qué captura hoy y qué se está descartando.
2. Medí si el PDF de la OD permite mapear **capítulo → rango de artículos**.
   `capitulos_nombre.py` ya extrae `(titulo_num, capitulo_num, nombre)` del PDF; la pregunta
   es si también hay artículos. **Usá el caché local de PDFs, que es gratis.**
3. Cruzalos y reportá: **¿cuántos proyectos pasan de "sin resultado por capítulo" a "con
   resultado por capítulo"?** Hoy es 1 (Ley Bases). Ese número es el resultado de la fase.
4. **Si el $n$ sube a algo utilizable, corré la validación de plausibilidad de verdad** con
   `validar_leybases_por_capitulos.py` extendido al universo nuevo. Si no sube, decilo — es
   un resultado igual de válido y cierra la pregunta.

> ⚠️ **Cuidado con la clave.** El numeral de capítulo **se reinicia en cada título** (en Ley
> Bases "Capítulo I" aparece bajo 6 títulos distintos). La clave es
> `(proyecto_id, titulo_num, capitulo_num)`, nunca `capitulo_num` solo. Ese bug ya apareció
> **dos veces** el 16-09 — en `capitulos_nombre.py` y en el propio script de validación.

---

# FASE C — El patrón AUX (gratis, y es riesgo de degradación silenciosa)

En Ley Bases, el capítulo "Reorganización administrativa" (II/I) se clasificó **AUX**, y al
ser AUX `proyectar_postura` **no encontró actas para condicionar y cayó a incondicional sin
avisar como error**. Es degradación silenciosa: el mecanismo parece andar y no está usando
nada.

**Qué hacer, sin clasificar:**

1. Sobre `tema_por_capitulo.parquet`, listá los capítulos clasificados AUX y **mirá sus
   nombres a ojo**. ¿Son realmente trámite, o son sustantivos con nombre corto o genérico?
2. Medí cuántos son. Si es un patrón y no un caso, **es un bug del clasificador**, no un
   dato.
3. Si el patrón existe, la corrección probable es del **prompt del agente** (más contexto
   para nombres cortos: el sumario del proyecto ya se pasa — verificá si llega bien) o una
   **regla de frontera** en `taxonomias.json`. **Proponela, no la ejecutes:** cambiarla
   implica reclasificar, y eso es gasto.

> **Es el mismo patrón que ya nos mordió tres veces:** un default silencioso que convierte
> "no sé" en una categoría que parece un dato. El parser del Senado con `clase="unico"`, las
> comas en las comisiones, y ahora AUX. **Un valor imposible o sospechosamente frecuente es
> un bug, no un fenómeno.**

---

# Reglas de la casa

**Leé primero:** `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py` para ubicar
código sin releer el repo) → `CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` → ADRs
**0026** (récord por tema), **0027** (composición por capítulos), **0029** (lo que motiva
esta sesión, con sus cuatro addenda).

**No toques el motor.** Esta sesión no cambia comportamiento: mide. `RECORD_POR_TEMA` queda
como está (prendido). `composicion_capitulos` queda **construido y apagado** — decisión
explícita de Franco: no se publica un número que no se pueda respaldar, y no se tira el
trabajo hecho.

**No `git push`.** Commits locales, en español.

## Higiene, que en este proyecto se aprendió a los golpes

- **Un porcentaje imposible es un bug, no un fenómeno.** Cuando un número da cero, o
  absurdo, o sospechosamente redondo: **sospechá del cruce antes que de la hipótesis.** Las
  cuatro veces que pasó, era el cruce.
- **Dos tablas de enlace acta↔expediente**: usá la ANCHA (`acta_expediente_todas.parquet`),
  no la angosta. Esa confusión ya costó dos veces.
- **Elegí bien la unidad.** Dos mediciones correctas del mismo fenómeno dieron resultados
  opuestos según qué mantenían fijo.
- **Los estratos se leen sobre el censo, no sobre la muestra.** El skill de una era pasó de
  −0,189 (muestra de 300) a +0,024 (censo).
- **Las cotas se dicen como cotas.** Un número optimista presentado sin el adjetivo se cita
  después como si fuera la estimación.
- **Si el resultado contradice lo que esperábamos, decilo.** Un resultado negativo bien
  medido vale más que uno positivo forzado — y en esta sesión, "no vale la pena gastar" es
  un resultado perfectamente bueno.

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — entrada de bitácora: qué se midió y qué se
   concluye. Escribí para alguien que no estuvo.
2. **Addendum al ADR-0029** con los resultados de las tres fases (no un ADR nuevo: esto
   cierra preguntas que ese ADR dejó abiertas).
3. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
4. Reindexá: `python .mapa/indexar.py .`

# Cerrá con la recomendación, en una tabla

Para cada uno de los tres gastos pendientes — **ampliar cobertura**, **terminar
`tema_por_capitulo`**, **reclasificar los AUX** — decí:

| | cuánto cuesta | qué compra, medido | recomendación |
|---|---|---|---|

Y **decí cuál NO harías**, con el número que lo respalda. Franco decide con eso.

Empezá por `URGENTE.md` y la **FASE B** — es gratis y es la que puede cambiar el valor de
todo lo demás.
