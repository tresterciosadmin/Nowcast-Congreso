# Resumen para la sesión de cowork — el problema multitema

**Fecha:** 2026-09-16 · **Para:** sesión de cowork de Franco (fuera de este repo) ·
**Estado del código:** cerrado por ahora, documentado en ADR-0024 y `PASO 2`
(`coordinacion/DECISIONES/0024-...md`), banderas apagadas, nada pendiente de
código — este documento es la síntesis para discutir el PRÓXIMO enfoque, no
un ADR nuevo.

## El problema en una frase

Un proyecto de ley grande (Ley Bases es el caso de manual) toca varios temas a
la vez — administración pública, desregulación, economía — pero en el punto
donde el motor decide **cómo vota cada bloque** frente a ese proyecto, todo
eso se colapsa a UN solo tema. El bloque termina votando según su historial en
"el tema principal", ignorando que la ley también es, por ejemplo, una ley
económica y una ley de reforma del Estado.

## Por qué importa

`variables/bloque/src/bloque.py::proyectar_postura` decide la postura de cada
bloque mirando su historial CONDICIONADO al tema. Si el proyecto es
multitema y sólo se usa el tema de mayor confianza, se está preguntando "¿qué
hizo este bloque en administración pública?" cuando la pregunta real —para un
ómnibus— es más parecida a "¿qué hizo este bloque frente a leyes que MEZCLAN
administración pública, desregulación y economía?", que puede tener una
respuesta distinta.

## Qué se probó (PASO 2, ADR-0024) — y el resultado, sin adornos

Se implementaron y midieron **cuatro** formas de resolver la postura de
bloque frente a un proyecto multitema (backtest walk-forward, 2.984 actas
reales, comparando contra el histórico):

| regla | idea | resultado vs. `primaria` (hoy) |
|---|---|---|
| `primaria` | usar sólo el tema de mayor confianza (lo de siempre) | — (la base de comparación) |
| `union` | juntar el historial de CUALQUIER tema que el proyecto toque | **peor** |
| `ponderada` | promediar el historial de cada tema, pesado por confianza | **peor** |
| `peor_tema` | quedarse con el tema donde el bloque está MÁS en contra (pedido explícito de Franco: "probemos algo nuevo") | **la peor de las cuatro** |

Las tres reglas nuevas **empeoran** el Brier score específicamente en la rama
de bloque (el subconjunto de votos que de verdad usan esta lógica) — ninguna
mejora, y `peor_tema` es la que más se equivoca. En el número agregado global
el efecto es invisible (la rama de bloque es ~0,36% de todos los votos), así
que esto NO se ve si se mira sólo el Brier general: hay que mirar
específicamente la rama que el cambio toca.

## Por qué fallaron las tres — la hipótesis más plausible

La rama de bloque **ya era la parte más débil del motor** antes de tocar nada
(skill NEGATIVO incluso con `primaria`, ver §II.5 de `FORMULA-COMPLETA.md`):
es una estimación con poca base (1.263 votos en la muestra), y cualquiera de
las tres transformaciones —juntar actas de otros temas, promediar entre
temas, quedarse con el peor caso— agrega variabilidad a una estimación que ya
era frágil, en vez de agregar señal. `peor_tema` en particular empuja
sistemáticamente hacia el extremo pesimista una rama que ya tiende a
predecir demasiado extremo — el peor lugar posible para empujar.

**Una hipótesis alternativa que NO se pudo descartar del todo:** la limitación
de `ponderada` en esta medición (usa peso IGUAL entre temas porque el
histórico de actas no guarda confianza por etiqueta, sólo por la primaria) sí
podría estar castigándola de más. Con `proyecto_taxonomias` ahora poblada
(1.182 proyectos, con confianza real por etiqueta — ver bitácora del 16-09),
`ponderada` con pesos reales es una remedición barata que todavía no se hizo.
No cambiaría el resultado de `union` ni de `peor_tema`, que no tienen ese
problema.

## Caminos a explorar en la sesión de cowork (propuestas, NO probadas)

Tres ángulos genuinamente distintos, no variantes de lo mismo que ya falló:

**1. Mover el arreglo de nivel — de BLOQUE a LEGISLADOR (ADR-0016).**
Las tres reglas probadas combinan HISTORIALES DE BLOQUE ya agregados y
encogidos, y después los vuelven a combinar entre sí — dos capas de
agregación apiladas sobre una muestra chica, que es justo el patrón que la
doctrina de este proyecto (ADR-0016, "de la parte al todo") advierte que
suele perder señal. La alternativa no probada: que cada LEGISLADOR (no el
bloque) cargue su propia propensión por tema, y que la multietiqueta se
resuelva a nivel individual antes de agregar a bloque — un solo paso de
agregación en vez de dos. Es más trabajo (hoy el historial por tema vive a
nivel de bloque) pero ataca la causa que señala la hipótesis de arriba
directamente, en vez de intentar una cuarta forma de combinar lo mismo.

**2. Dejar de tratar "multitema" como un problema de MEZCLA, y tratarlo como
un problema de DESCOMPOSICIÓN — vía B2 (capítulos).** La pregunta "¿qué tema
es esta ley?" puede ser la pregunta equivocada para un ómnibus. Ley Bases no
es una ley multitema: es VARIAS leyes mono-tema encuadernadas juntas, cada
capítulo con su propio tema dominante (el Título II es laboral, el Título IV
es desregulación, etc.). B1/B2 (`votacion_por_articulo.py`,
`extraer_titulo_capitulo`, ver ADR-0023) ya identifican qué tramo de votación
pertenece a qué capítulo. El camino no explorado: en vez de mezclar temas a
nivel de la ley entera, asignar un tema por CAPÍTULO (cada uno probablemente
mono-tema) y simular cada capítulo por separado con el shock compartido
$\eta_j$ (§III.A.3, ya implementado y prendido — ver ADR-0025), agregando
después. Esto no reutiliza nada de lo que ya falló: es una arquitectura
distinta, más alineada con el "de la parte al todo" que "combinar temas a
nivel bloque" nunca terminó de ser.

**3. Antes de diseñar una quinta regla, medir si el problema es de MÉTODO o
de DATOS.** Las tres reglas fallaron sobre la MISMA muestra chica y la MISMA
rama ya débil. Vale la pena, antes de construir nada nuevo, medir si el
patrón se sostiene sobre el CENSO completo (6.091 actas, no la muestra de
3.000) — la limitación honesta que ya quedó anotada en ADR-0024 — y si
`ponderada` con pesos reales (punto de arriba) cambia el panorama. Si el
censo completo y los pesos reales siguen dando negativo, es más evidencia de
que el problema es de método (angle 1 o 2), no de una medición con mala
suerte.

## Lo que NO vale la pena reproponer

`union` ya es, en espíritu, "juntar todo el historial relacionado sin pesar
nada" — la versión más simple posible de "no perder ninguna señal
combinando". Ya se probó y perdió. Cualquier variante que siga siendo
"combinar historiales de bloque ya agregados, de una forma distinta" hereda
el mismo problema de fondo que el punto 1 de arriba señala — no vale la pena
gastar tiempo en una quinta/sexta regla de ese mismo tipo sin antes resolver
si el nivel (bloque vs. legislador) o la unidad (proyecto vs. capítulo) es lo
que hay que cambiar.

## Estado del código, para quien lo retome

Todo lo de este documento está en ADR-0024 (implementación de las 4 reglas,
`variables/bloque/src/bloque.py::proyectar_postura(combinar_temas=...)`) y en
`evaluacion/baseline/src/baseline_voto_individual.py --combinar-temas` (cómo
reproducir la medición). Las cuatro reglas quedan en el código, testeadas
(18 checks entre `test_bloque_v3_multietiqueta.py` y las suites relacionadas)
y reusables — no hay que reescribir nada para probar una remedición con
pesos reales o sobre el censo completo. Ninguna bandera está prendida.
