# ADR-0027 — Composición de P(proyecto) por capítulos, por simulación (FASE 2)

**Fecha:** 2026-09-16 · **Estado:** MÓDULO IMPLEMENTADO y TESTEADO, **NO
ENGANCHADO** a `nowcast_puertas.nowcast()` — cambia la semántica del número
publicado, decisión de Franco pendiente · **Decide:** Claude, mandato de
`coordinacion/PROMPT-MULTITEMA-V2.md` (FASE 2) · **Toca:**
`modelo/ensemble/src/composicion_capitulos.py` (nuevo),
`modelo/agregador_institucional/src/agregador.py` (`devolver_crudo`) ·
**Se relaciona con:** ADR-0023 (B1/B2, el contrato `votacion_por_articulo` y
`capitulos_nombre`), ADR-0024 (multitema a nivel bloque, negativo — esta fase
NO es una quinta variante de esa idea), ADR-0025 ($\eta_j$, la pieza que hace
posible componer capítulos sin asumir independencia)

## El error que esta fase NO repite

ADR-0024 probó cuatro formas de combinar TEMAS a nivel de TODA la ley. Las
tres nuevas fallaron. `PROMPT-MULTITEMA-V2.md` señaló por qué esta fase es
distinta: **no es una quinta forma de mezclar temas — cambia la UNIDAD.** Ley
Bases no es una ley multitema: son varias leyes, probablemente mono-tema cada
una, encuadernadas por capítulo. Si cada capítulo tiene su propio tema
dominante, el problema de "cómo combino varios temas" se disuelve en vez de
resolverse — no hay nada que combinar si cada capítulo se evalúa por separado.

## Decisión — simular, no componer con una fórmula

**"La P del proyecto" no es un evento: son varios**, y ninguno es el promedio
ni el producto de las P de los capítulos:

- Promediar en probabilidad trata "medio proyecto perdido" como si fuera un
  número, cuando en realidad depende de cuántos artículos tiene cada capítulo.
- Multiplicar SUPONE INDEPENDENCIA entre capítulos — la misma trampa que el
  Nivel 0 de `FORMULA-COMPLETA.md` ya tiene marcada como "supuesto activo y
  falso" entre cámaras, y que $\eta_j$ (ADR-0025) midió en 37-41× de
  sobredispersión sobre el voto individual. Un ómnibus no se cae capítulo por
  capítulo de forma independiente: si el bloque que sostenía el capítulo
  laboral se da vuelta, arrastra al económico.

**La forma correcta: simular cada capítulo con el MISMO shock $\eta_j$
compartido ENTRE capítulos** (no sólo entre legisladores de una misma
votación, que es lo que ADR-0025 ya hace). Implementado en
`modelo/ensemble/src/composicion_capitulos.py::simular_capitulos`:

$$P_k = \frac{1}{N}\sum_j \mathbb{1}[k\text{ pasa}] \qquad
P_{\text{todo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasan todos}] \qquad
P_{\text{algo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasa alguno}]$$
$$\mathbb{E}[\text{superviv.}] = \frac{1}{N}\sum_j \frac{\sum_k a_k\,\mathbb{1}[k\text{ pasa}]}{\sum_k a_k}, \quad a_k = \text{artículos del capítulo } k$$

**Mecanismo, sin simular los capítulos juntos en una sola llamada:**
`agregador.simular_votacion` gana `devolver_crudo=True` (aditivo, no cambia el
resumen agregado — verificado, 55/55 tests): dos llamadas con el MISMO
`seed`/`n_sims`/`epsilon0`/`tau` dibujan el MISMO `eta_j` porque es el
**primer draw** del generador, antes de cualquier muestreo de roster. Cada
capítulo se simula por separado (puede tener su propia postura de bloque,
condicionada a SU tema) y los `aprob_por_sim` booleanos quedan alineados sim a
sim — AND/OR/promedio ponderado entre capítulos sin volver a simular nada.

**La revancha de `peor_tema`, esta vez sin el estimador sesgado.** ADR-0024
midió que $\min_k \hat s_k$ sobre shares ruidosos está sesgado hacia abajo, y
por eso salió la peor de las tres reglas. Acá $P_{\text{todo}}$ y $\min_k P_k$
salen DIRECTO de contar simulaciones — no hay estimador que sesgar. El test
que lo prueba (`test_composicion_capitulos.py`, capítulos perfectamente
correlacionados, escenario de referencia de ADR-0025 con $\tau=1{,}2$):
$P_{\text{todo}}=0{,}7441$, $\min_k P_k=0{,}7441$ — **idénticos**, contra
$0{,}4121$ que daría el producto bajo independencia falsa (44,6% de
diferencia relativa). Es el test que atrapa el error de independencia si
alguien lo reintroduce.

## B0 — medir el histórico: Ley Bases reconstruida artículo por artículo

Con B1 (`votacion_por_articulo.parquet`, ADR-0023) y el nombre de capítulo
(`capitulos_nombre.parquet`, addendum del 16-09) ya en el repo, la
reconstrucción es una consulta, no una adquisición de datos nueva:

| ronda | fecha | tramos | AFIRMATIVO | NEGATIVO |
|---|---|---:|---:|---:|
| 1 (antes del retiro) | 2024-02-06 | 13 | 6 | **7** |
| 2 (volvió recortada) | 2024-04-30 | 35 | **35** | 0 |

**El método reproduce la crónica pública sin diferencias**: la primera ronda
pierde 7 de 13 tramos particulares (incluye el Título I Capítulo II —
"Sectores incluidos, plazo, sujetos habilitados", nombre real recuperado del
PDF) la noche del retiro; la segunda ronda, ya recortada por el Poder
Ejecutivo antes de reingresarla, pasa entera. Es el caso testigo que motivó
todo el prompt original (`PROMPT-MULTIETIQUETA.md`) y sigue reproduciéndose
igual con el contrato actual.

**Límite honesto que queda, no resuelto:** el NOMBRE de capítulo para "Título
II, Capítulo I" sale con ruido residual (un fragmento de sumario, no un
título real) — el mismo tipo de caso ya documentado en el segundo addendum de
ADR-0023 (dos ODs distintas del mismo proyecto, con contenido genuinamente
distinto entre rondas, generan más de un candidato y el heurístico actual no
siempre elige el correcto). No afecta el CONTEO de tramos AFIRMATIVO/NEGATIVO
(que sale del título de acta, no del PDF) — sólo el nombre que se muestra.

**B0 general (206 de 1.428 pares con votación en particular, 15 de 153 con
≥1 tramo negativo pese a aprobación general) ya estaba medido en ADR-0023 —
no se repite acá.**

## B1 y B2 — ya resueltos en sesiones anteriores, no se rehacen

`PROMPT-MULTITEMA-V2.md` pide "dejar de descartar en `elegir_votacion`,
agregar no reemplazar" (B1) y "agrupar artículos en capítulos... medí qué
haría falta, no arranques una adquisición grande sin decírselo a Franco" (B2).
**Las dos ya están hechas**, de una sesión anterior a este prompt:

- B1: `votacion_por_articulo.parquet` (ADR-0023) agrega sin tocar
  `elegir_votacion` ni `cadena_camaras.parquet` — exactamente lo pedido.
- B2: `extraer_titulo_capitulo` agrupa por capítulo leyendo el TÍTULO del
  acta (sin bajar ningún PDF, 2026-09-16), y `capitulos_nombre.py` bajó **163
  PDFs escogidos** (no una adquisición grande: los 145 proyectos de Diputados
  con votación en particular identificados por B0, ~4 minutos, 0 fallas) para
  el NOMBRE de cada capítulo. Ninguna de las dos cosas necesitó permiso
  adicional de Franco porque ninguna fue una descarga masiva sin acotar.

Este ADR no repite esas decisiones (regla de `CLAUDE.md`: no las repitas,
citalas) — las cita como ya resueltas y sigue con lo nuevo: el módulo de
COMPOSICIÓN, que ADR-0023 había dejado explícitamente pendiente ("el
consumidor que compone P(algo)/P(sobrevive) NO está implementado").

## Por qué esto NO está enganchado a producción

Dos motivos, uno de diseño y uno de datos:

1. **Cambia la semántica del número publicado.** `PROMPT-MULTITEMA-V2.md` es
   explícito: los dos números nuevos (P(se sanciona algo) / P(sobrevive) van
   apagados hasta que Franco los revise — redefinir qué cuenta como
   "aprobado" cambia la variable dependiente e invalida la comparación con el
   baseline actual.
2. **Falta el insumo para armar el roster POR capítulo de un proyecto real.**
   `simular_capitulos` simula lo que se le pase: necesita, por proyecto, una
   postura de bloque POR CAPÍTULO (cada capítulo condicionado a SU tema
   dominante). Eso requeriría clasificar el tema de cada capítulo por
   separado — un paso de clasificación que no existe todavía (hoy la
   clasificación es por PROYECTO o por ACTA completa, no por capítulo) y que,
   si usa el agente LLM, es exactamente el tipo de gasto que hay que
   consultar antes de lanzar (ver memoria de sesión: "Franco: activaste el
   agente sin mi permiso"). **No se armó ese cableado en esta sesión.** El
   módulo de composición está probado con rosters SINTÉTICOS (mecánicamente
   correcto) pero no se corrió sobre un proyecto real de punta a punta.

## Verificación

`modelo/ensemble/tests/test_composicion_capitulos.py` (10 checks): capítulos
perfectamente correlacionados dan $P_{\text{todo}}\approx\min_k P_k$, MUY por
encima del producto bajo independencia falsa; sin `epsilon0`/`tau` rompe
claro (no simula en silencio sin shock compartido); $P_{\text{algo}} \geq
P_{\text{todo}}$ y $\geq$ cualquier $P_k$ (cotas lógicas); $\mathbb E[\text{superviv.}]$
pondera por artículos (caso determinístico verificado); determinismo (mismo
seed -> mismo resultado); capítulo sin campo obligatorio rompe con el nombre
del campo.

`modelo/agregador_institucional/tests/test_agregador.py` (+5 checks, 55/55
totales): `devolver_crudo` no cambia el resumen agregado; el array crudo
promedia exacto al `p_aprobacion` reportado; dos llamadas con el mismo seed y
rosters DISTINTOS correlacionan por compartir `eta_j` (la propiedad que hace
posible componer capítulos sin simularlos juntos).

## Lo que queda pendiente, y de quién es cada pendiente

1. **Clasificar el tema POR CAPÍTULO** (no por proyecto/acta) — el insumo que
   falta para enganchar `simular_capitulos` a un proyecto real. Es una
   decisión de alcance y de gasto (agente LLM) de Franco.
2. **Activar los dos números publicados** (P(algo)/P(sobrevive)) — decisión
   de producto explícitamente diferida por el prompt, no técnica.
3. **La ambigüedad de nombres de capítulo entre ODs del mismo proyecto**
   (B0, arriba) — cosmética (no afecta el conteo), pero si se van a MOSTRAR
   nombres de capítulo en algún panel, hace falta una regla de desambiguación
   (ej. preferir la OD más reciente).
