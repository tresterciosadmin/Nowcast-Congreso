# Puerta D — voto en la cámara REVISORA

> Ficha acordada con Valle el 2026-08-09, antes de escribir código. Parte de la
> reconstrucción del nowcast por puertas (línea Revisión de Comisiones). Este
> documento es el contrato de D; el código es `src/puerta_d.py`.

## El mapa completo (contexto)

El nowcast dejó de intentar predecir la etapa de COMISIÓN (política, no medible)
y pasa a medir la aprobación **en la cámara de origen y en la revisora**:

    P(sanción) = P(A) · P(B|A) · P(C|A,B) · P(D|A,B,C)

| Puerta | Qué es | Cómo se trata |
|---|---|---|
| A | agenda origen (¿sale de comisión?) | se **observa el dictamen** (firmas, bloques). Parqueado |
| B | voto origen (¿mayoría?) | agregador — ya existe |
| C | agenda revisora (¿la tratan antes de caducar?) | **observada** + reloj Ley 13.640 |
| **D** | **voto revisora (¿mayoría, sabiendo que ya pasó origen?)** | **este documento** |

Una puerta que ya ocurrió deja de ser probabilidad y vale 1: el número publicado
se colapsa según el estado observado del proyecto. Con media sanción, A y B son
hechos y queda `P(C)·P(D)`.

## Las tres declaraciones de D

**1. Unidad.** El proyecto (`denominador`), representado por su votación decisiva
—la "en general", vía `elegir_votacion` de `datos/expedientes/enlace_senado`—,
nunca por las votaciones de artículo. Un número por proyecto.

**2. Evento con fecha.** El condicionante es *"obtuvo media sanción en la cámara
de origen, en fecha `t_ms`"*. La **cámara revisora es la otra** respecto de
`camara_origen`. Su composición se lee **a la fecha de la votación** (o a la
proyectada, para un pronóstico), con el padrón point-in-time: Diputados
`padron_diputados.csv` (1.454 tramos) y Senado `padron_senado_historico.csv`
(243 tramos, 2017→2031). Se simula sobre quienes REALMENTE estaban esa fecha.

**3. Población.** Dos, porque D tiene dos partes:
- **Base** (¿mayoría dada la composición?): todos los proyectos con votación
  decisiva en la revisora. Es mecánico (el agregador cuenta bancas + postura +
  desvío), no necesita entrenamiento.
- **Ajuste "pasó por origen"** (Manera 2): sólo los ~243 proyectos con votación
  en las dos cámaras (60 desde 2015), con **ómnibus excluidos** y **encogido por
  tamaño de muestra**.

## El cálculo, con el fallback adentro

1. **Base (Manera 1).** El agregador (`simular_votacion`) corre sobre el roster
   de la revisora a la fecha. Las **posturas de bloque salen de la MISMA
   maquinaria que en origen** (`variables/bloque.proyectar_postura`, dirección
   por tema/origen). → `p0 = P(mayoría | composición)`.
2. **Ajuste (Manera 2).** Un término `delta` en escala logit que corrige `p0`
   usando que el proyecto ya pasó por origen, estimado sobre los casos de dos
   cámaras, **encogido hacia 0 según la muestra** (por taxonomía/origen si
   alcanza; global si no).
3. **El fallback NO es un `if`.** Cuando la muestra para `delta` es insuficiente,
   el encogimiento lo lleva a 0 y queda `p0` puro = la composición de la revisora
   sola. Manera 1 es el **límite** de Manera 2. Un solo modelo.

Estado hoy: `delta = 0` (Manera 1 pura). El enganche de Manera 2 queda como hook
con `delta` y su factor de encogimiento; se activa cuando se ajuste sobre los 243
casos. Ver `estimar_delta_paso_origen` (pendiente).

## Lo que NO es D (decidido con Valle)

- **No transfiere posturas de origen a la revisora por linaje.** Se evaluó y se
  descartó: un partido puede tener otra fuerza en cada cámara y la revisora es una
  herramienta de negociación — a veces alinea, a veces no. Queda como PROPUESTA
  para el equipo (ver ESTADO 2026-08-09), no como parte de D.
- **No modela C** (que se trate a tiempo). Eso es estado observado + caducidad.
- **El flag ómnibus** (`es_omnibus`, ≥8 votaciones en particular) NO vive en D:
  es higiene de datos global. D sólo lo usa para excluir del ajuste de Manera 2.

## Contrato de código (`src/puerta_d.py`)

    p_voto_revisora(proyecto_id | camara_origen, fecha, bloques, ...) -> dict
      { p_aprobacion, camara_revisora, p0, delta, n_roster, manera, detalle }

Reusa `roster_nominal` (ensemble), `simular_votacion` (agregador) y
`proyectar_postura` (bloque). No reimplementa nada de eso.
