# Puerta D — voto en la cámara REVISORA

> Ficha acordada con Valle el 2026-08-09, antes de escribir código. Parte de la
> reconstrucción del nowcast por puertas (línea Revisión de Comisiones). Este
> documento es el contrato de D; el código es `src/puerta_d.py`.

---

## ⚠️ ENMIENDA 2026-08-22 — A y C NO son probabilidades de agenda

**Esta enmienda manda sobre el cuerpo del documento.** Lo de abajo queda como
registro de lo acordado el 2026-08-09; donde diga otra cosa, vale esto.

El 2026-08-20 Valle decidió que el nowcast **deja de estimar si una comisión o una
cámara va a TRATAR un proyecto**. Eso es agenda política y no se predice. La versión
original de este documento —escrita once días antes— todavía describía A como
*«agenda origen (¿sale de comisión?)»* y C como *«agenda revisora (¿la tratan antes
de caducar?)»*. **Las dos frases están dadas de baja.** Si aparecen citadas en algún
lado, es una cita del marco viejo, no del contrato vigente.

**Lo que son A y C ahora:** el **carácter del trabajo en comisión** en cada cámara —
quién firmó el dictamen, si hubo disidencias y de qué tipo, de qué bloques son los
firmantes, si firmaron dos comisiones. Es un **hecho observado**, leído de los PDF
de la Orden del Día (`datos/expedientes`, ingestado el 21 y 22-08-2026). No se
estima, no se predice y **no lleva probabilidad**.

La formulación queda simétrica, y la simetría es el punto:

    P(sanción) = [A observada] · P(B | carácter del dictamen de ORIGEN)
               · [C observada] · P(D | carácter del dictamen de la REVISORA)

| Paso | Qué es | Naturaleza | Cómo entra al número |
|---|---|---|---|
| **A** | dictamen en la cámara de ORIGEN | **se observa** (hecho) | colapsa a 1 si ocurrió; su **carácter condiciona B** |
| **B** | votación en la cámara de ORIGEN | **se calcula** (probabilidad) | el agregador sobre el roster nominal |
| **C** | dictamen en la cámara REVISORA | **se observa** (hecho) | colapsa a 1 si ocurrió; su **carácter condiciona D** |
| **D** | votación en la cámara REVISORA | **se calcula** (probabilidad) | este documento |

**A y C no multiplican: condicionan.** Que un dictamen sea de mayoría, firmado por
dos comisiones y sin disidencias no cambia la chance de que lo traten —cambia **cómo
van a votar los bloques cuando lo traten**. Su lugar es el de
`variables/bloque.proyectar_postura(tema=, origen=)`, que ya condiciona la dirección
del voto. Decisión de Valle, 2026-08-22: **el dictamen de la revisora condiciona D
exactamente como el de origen condiciona B.**

**Los TRES estados de A y de C** (no son dos, y el tercero no puede colapsar al
segundo porque son opuestos):

1. **con dictamen y carácter conocido** — se observó y se leyó;
2. **sin dictamen** — no lo hay;
3. **sin dato** — puede haberlo y nosotros no lo sabemos: la Orden del Día todavía
   no se publicó (mediana de 224 días), o es de un sistema de comisiones cuyo
   empalme no está resuelto.

**En «sin dato» no se anula nada ni se frena la cadena:** el condicionante se **encoge
a 0** y queda la estimación no condicionada. Es el mismo mecanismo que este documento
ya define abajo para `delta` — *«El fallback NO es un `if`… Manera 1 es el límite de
Manera 2. Un solo modelo.»* **No se inventa otro.**

**Lo que sale de la cadena publicada:** `p_llega_recinto` (variables/embudo) deja de
ser factor — es exactamente la mortandad de agenda que decidimos no modelar.
`p_sancion` **no se toca y tampoco entra**: ya contiene A, B, C y D adentro y su lugar
es la **baseline** del backtest. `factor_revisora_empirico` queda **fuera del número
publicado** (contiene C y D juntas: meterlo con D simulada cuenta dos veces lo mismo)
y sobrevive sólo como vara alternativa en `backtest_cadena.py`.

**El costo, que va en la interfaz y no en un README:** sin `p_llega_recinto`, para un
proyecto **sin dictamen** el modelo ya no dice «tiene 4% de ser ley porque el 96% muere
en el cajón». Dice **«si llega a votarse, gana con X%»**. El número pasa a ser
**condicional** y tiene que decir con qué se calculó: qué pasos se observaron de verdad
y cuáles corrieron sin dato.

**Vocabulario, para que no se repita el error que originó esta enmienda:** no se
escribe «puerta» a secas para las cuatro. A y C se **observan**, B y D se **calculan**;
llamarlas igual las iguala y no son lo mismo. Los nombres largos son la Tarea 2 del
`PROMPT-3`; hasta que se acuerden, la letra va siempre con la naturaleza al lado.

---

## El mapa completo (contexto) — REGISTRO del 2026-08-09, superado por la enmienda

> ⚠️ La tabla que sigue describe A y C en el marco de agenda que la enmienda de arriba
> dio de baja. Se conserva para poder leer las decisiones del 09-08 en sus términos.
> **No la cites como contrato vigente ni derives nombres de ella.**


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
  *[Marco viejo — ver la enmienda del 22-08: C no es «que se trate a tiempo» sino el
  carácter observado del dictamen de la revisora, y condiciona D.]*
- **El flag ómnibus** (`es_omnibus`, ≥8 votaciones en particular) NO vive en D:
  es higiene de datos global. D sólo lo usa para excluir del ajuste de Manera 2.

## Contrato de código (`src/puerta_d.py`)

    p_voto_revisora(proyecto_id | camara_origen, fecha, bloques, ...) -> dict
      { p_aprobacion, camara_revisora, p0, delta, n_roster, manera, detalle }

Reusa `roster_nominal` (ensemble), `simular_votacion` (agregador) y
`proyectar_postura` (bloque). No reimplementa nada de eso.
