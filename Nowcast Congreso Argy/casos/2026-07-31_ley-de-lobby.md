# Caso de prueba end-to-end — Ley de Lobby (Gestión de Intereses)

> **Qué es esta carpeta.** `casos/` guarda corridas completas del nowcast sobre un
> proyecto REAL: taxonomía → embudo → escenarios → pivotes. Sirve para dos cosas:
> mostrar el producto terminado y **encontrar los agujeros del modelo con un caso
> concreto**, que es lo que pasó acá.

**Corrida:** 2026-07-31 · Claude+Franco · datos: expedientes al 2026-06, votaciones al 2025-10
**Insumo:** `MEN-2026-178` / `INLEG-2026-51552183-APN-PTE` (PDF del PE, 47 artículos)

---

## 1. Identificación — el proyecto ya estaba en la base

El PDF entró al repo por la puerta de atrás: el bot diario ya lo había levantado.

| | |
|---|---|
| **Expediente** | `0004-PE-2026` (interno `HCDN292179`) |
| **Título oficial** | RÉGIMEN DE TRANSPARENCIA Y PUBLICIDAD DE LA GESTIÓN DE INTERESES |
| **Firmantes** | Milei, Adorni (JGM), Santilli (Interior), Monteoliva (Seguridad) — 22/05/2026 |
| **Ingreso a Diputados** | 26/05/2026 |
| **Giro** | (1) ASUNTOS CONSTITUCIONALES · (2) LEGISLACIÓN GENERAL |
| **Estado al 31/07** | sin dictamen, sin tratamiento — **66 días parado en comisión** |

## 2. Taxonomía — `POLINST.ETICA` (match literal)

Vocabulario controlado (`docs/taxonomias/taxonomias.json`, 74 ids). El subtema
`POLINST.ETICA` se llama, textualmente, *"Transparencia / **Lobby** / Ética pública"*.

| id | rol | por qué |
|---|---|---|
| **POLINST.ETICA** | **primaria** | objeto declarado (art. 1°); deroga en los hechos el Dto. 1172/03 |
| **JUST.PENAL** | secundaria | Título VIII crea 4 delitos nuevos (arts. 39-42): gestión clandestina, falsedad agravada, representación clandestina de intereses extranjeros, obstrucción dolosa |
| POLINST.ORGEST | secundaria | crea 3 registros públicos y designa autoridades de aplicación en ambos poderes |
| DEF.EXTERIOR | menor | Título IV: régimen de interés extranjero tipo FARA (arts. 22-24) |

No es `AUX.*`: tiene contenido sustantivo. Regla de frontera aplicada: crea **legislación
penal especial**, no reforma el Código Penal → `JUST.PENAL` entra como secundaria, no como
área principal.

**Rasgo político que el texto no esconde:** el art. 18 inc. b) alcanza a **senadores y
diputados**, no solo al PE. El Ejecutivo se somete a un registro y de paso obliga al
Congreso. Eso importa para leer las resistencias.

---

## 3. Probabilidad — **39,2%**

Modelo de supervivencia del embudo (`variables/embudo`, logística walk-forward, skill 0,363
sobre tasa base) con las señales corregidas ayer.

| | P(llega al recinto) | P(sanción) |
|---|---|---|
| **Este proyecto** | **49,4%** | **39,2%** |
| Tasa base — cohorte madura, n=38.697 (comparable) | 4,90% | 3,40% |
| Tasa base — cohorte completa, n=41.339 (referencia) | 4,63% | 3,21% |

*Todas las cifras de este informe usan la **cohorte madura** (proyectos presentados hasta 2
años antes del último dato) salvo aviso: es la población sobre la que se entrena y la única
donde "no avanzó" significa muerto y no "todavía en trámite".*

**39,2% es 11,5 veces la tasa base.** Para un proyecto de ley argentino eso es muchísimo.
Pero es **la mitad del 77,1% que promedia el Poder Ejecutivo**, y la diferencia tiene dos
causas identificables:

1. **Quién es el Ejecutivo importa más que el hecho de serlo.** La tasa de conversión
   presidencial viene cayendo sin pausa:

   | presidente | proyectos | sancionados |
   |---|---:|---:|
   | Cristina Fernández | 377 | **87,3%** |
   | Macri | 156 | 69,2% |
   | Alberto Fernández | 110 | 61,8% |
   | **Milei** | 24 | **41,7%** |

2. **Las dos comisiones del giro son lentas.** Asuntos Constitucionales sanciona el 2,53%
   de lo que recibe y Legislación General el 4,27% — ambas por debajo del 7,82% promedio de
   dictamen. No son las peores (Presupuesto lo es), pero no ayudan.

### El antecedente que el modelo no ve, y conviene mirar

**35 proyectos de gestión de intereses / lobby desde 2009. Cero sancionados.** Ninguno
llegó siquiera a dictamen. El tema tiene 17 años de fracaso perfecto: se presenta, caduca a
los dos años, se re-presenta. Camaño lo intentó en 2021 y 2023; Pichetto en 2024 y 2026;
Scaglia en 2021 y 2026; Banfi en 2024 y 2026.

Contra eso hay un dato nuevo y fuerte: **en mayo de 2026 se presentaron cuatro proyectos de
lobby en diecisiete días** — Banfi (12/05), el PE y Scaglia (22/05), Pichetto (28/05). Los
diez proyectos vivos van a **las mismas dos comisiones** que el del PE. Eso es un cuadro
clásico de dictamen unificado: hay tema en agenda y hay con quién negociarlo.

---

## 4. Los escenarios — quién lo firma vale 30 veces más que su jerarquía

Mismo texto, mismas comisiones, mismo año; cambia solo quién lo presenta
(`variables/embudo/src/escenarios.py`, contrafactual sobre la fila real):

| escenario | P(recinto) | P(sanción) |
|---|---:|---:|
| **Poder Ejecutivo (real)** | **49,4%** | **39,2%** |
| Jefe de bloque oficialista | 2,0% | 1,3% |
| Diputado común oficialista | 1,3% | 1,3% |
| Jefe de bloque opositor | 0,6% | 0,6% |
| Diputado común opositor | 0,5% | 0,6% |

**Respuesta directa a las dos preguntas:**

- **¿Que lo presente el Ejecutivo afecta?** Es *lo único* que lo afecta de verdad. El mismo
  texto firmado por un jefe de bloque oficialista cae a **1,3%**: pierde 30 veces la
  probabilidad. El Ejecutivo tiene lo que ningún diputado tiene — puede convocar
  extraordinarias, negociar con gobernadores y poner el tema en el temario.
- **¿Jefe de bloque vs. diputado común?** Casi nada: **1,3% contra 1,3%** en sanción, y
  2,0% contra 1,3% en llegar al recinto. La jefatura ayuda a que el proyecto **se trate**,
  no a que se apruebe.

---

## 5. Hallazgo del test: el efecto líder era 5,7x y en realidad es 1,9x

Este es el resultado que justifica haber corrido el caso. La conclusión vigente del
proyecto —*"un líder multiplica ~7x las chances"*— **estaba inflada por composición**
(paradoja de Simpson):

| corte | no-líder | líder | efecto |
|---|---:|---:|---:|
| **Crudo (como se venía midiendo)** | 2,18% | 12,35% | **5,66x** |
| Dentro del Ejecutivo | 71,24% | 78,78% | 1,11x |
| Dentro del oficialismo | 2,83% | 5,41% | **1,91x** |
| Dentro de la oposición | 1,42% | 2,73% | **1,92x** |

La causa: **el 78% de los proyectos del PE cuentan como "líder"** (el presidente es alto
productor) y el PE sanciona el 78,8%. El efecto que se le atribuía al liderazgo era, en
buena medida, el efecto de ser el Ejecutivo.

Desagregado por tipo de liderazgo, dentro de proyectos de legisladores:

| señal | efecto |
|---|---:|
| ser **alto productor** | 1,80x |
| ser **jefe de bloque** | **1,25x** |

**Ser jefe de bloque casi no mueve la aguja por sí solo.** Notable, porque la curación del
roster bicameral de ayer fue trabajo pesado: sigue valiendo para interpretabilidad y para
el mapa de influencia, pero no es la palanca predictiva que parecía.

Que el efecto sea **1,91x en el oficialismo y 1,92x en la oposición** —dos poblaciones
distintas, mismo número— es la mejor señal de que ahora estamos midiendo algo real.

---

## 6. Los diputados que hay que afectar

El proyecto no se define en el recinto: se define en dos comisiones que **preside La
Libertad Avanza** (Mayoraz y Santurio). Pero presidir no alcanza — LLA no tiene mayoría
propia en ninguna de las dos:

### ASUNTOS CONSTITUCIONALES — 35 miembros, dictamen con 18

LLA 15 · UXP 13 · Provincias Unidas 3 · PRO 2 · Innovación Federal 1 · UCR 1
→ **LLA + PRO = 17. Falta exactamente una firma.**

### LEGISLACIÓN GENERAL — 31 miembros, dictamen con 16

LLA 12 · UXP 11 · PRO 2 · Provincias Unidas 2 · Innovación Federal 1 · Independencia 1 ·
Coalición Cívica 1 · UCR 1
→ **LLA + PRO = 14. Faltan dos.**

### Los nombres

| diputado | bloque | por qué |
|---|---|---|
| **GONZÁLEZ, Diógenes Ignacio** | UCR (Corrientes) | **está en las dos comisiones y es vicepresidente de ambas.** Es el pivote singular del proyecto: una sola persona destraba las dos llaves |
| **RUÍZ, Yamila** | Innovación Federal | la otra que integra ambas comisiones |
| FERRARO, Maximiliano | Coalición Cívica | secretario de Legislación General; la CC viene impulsando transparencia hace años — aliado natural, costo de conseguirlo bajo |
| BRÜGGE · FARÍAS · JULIANO | Provincias Unidas | los 3 en Asuntos Constitucionales: con uno alcanza para el dictamen |
| CAPOZZI · COLETTA | Provincias Unidas | los 2 en Legislación General |
| MEDINA, Gladys | Independencia | Legislación General |

**Lectura:** con Asuntos Constitucionales alcanza **una** firma no oficialista, y la más
barata está a la vista. Los autores de los diez proyectos competidores —Banfi, Pichetto,
Scaglia, Carrizo, López, Stolbizer, Agost Carreño, Brambilla— no son adversarios: son los
dueños históricos del tema, y el precio de su acompañamiento es previsiblemente que el
dictamen unificado tome artículos suyos.

**El riesgo no está en estos nombres, está en el art. 18 inc. b):** el régimen alcanza a
los propios legisladores. La resistencia esperable es transversal y silenciosa — la forma
que toma no es el rechazo (en 18 años hubo 4 rechazos explícitos en total) sino el cajón.
Los 66 días sin movimiento ya son parte de ese patrón.

---

## 7. Qué NO puede responder el modelo hoy (y por qué)

`P(aprobación) = P(llega al recinto) × P(mayoría | recinto)`. **Este informe calcula bien
el primer factor y no puede calcular el segundo.**

La última votación en nuestra base es del **9 de octubre de 2025**, anterior al recambio del
10 de diciembre. Hubo extraordinarias en diciembre y febrero y sesiones ordinarias todo
2026: **229 actas están publicadas en la fuente y no las ingestamos** (113 de la Cámara
nueva). El proyector de posturas, corrido para hoy, devuelve la Cámara vieja: 92 bancas de
UxP y 35 de LLA, total 267 sobre 257 reales, y todos los bloques en AFIRMATIVO.

Los datos de comisiones sí son actuales (bajados ayer): por eso la sección 6 es sólida y la
del recuento en el recinto no existe. **Queda cargado en `URGENTE.md`.**

### Otras dos limitaciones honestas

**Colinealidad `autor_tasa_hist` ↔ `origen_ejecutivo` = 0,874.** El rasgo "tasa histórica
del autor" y el rasgo "lo manda el PE" miden casi lo mismo, porque el autor del PE *es* el
presidente. La logística le da el crédito a la tasa del autor (coef. 0,61) y deja
`origen_ejecutivo` en 0,04 y `lider` en **−0,03**, pese a que las tasas crudas son 78,8%
vs 1,4%. **Los coeficientes del modelo v1 no se pueden leer como efectos.** Los
contrafactuales de la sección 4 mueven las tres cosas a la vez por eso.

**Corregir la señal no mejoró la predicción.** Skill sobre tasa base:

| | antes (13/07) | ahora | Δ |
|---|---:|---:|---:|
| sancionado | 0,3691 | **0,3628** | −0,006 |
| llega_recinto | 0,4120 | 0,4112 | −0,001 |

Eliminar 1.413 falsos positivos del líder **no movió el poder predictivo** — porque esa
información ya entraba por `autor_tasa_hist`. Lo que ganamos fue interpretabilidad, que es
justamente lo que el producto promete ("el nowcast explica por qué"). Vale registrarlo:
**limpiar una señal redundante mejora la explicación, no el acierto.**

---

## 8. Resumen ejecutivo

> **La Ley de Lobby tiene 39,2% de probabilidad de sancionarse: 11,5 veces la tasa base,
> la mitad de lo que promedia el Ejecutivo.** Todo su capital viene de quién la firma — el
> mismo texto presentado por un jefe de bloque valdría 1,3%. Enfrenta 17 años de
> antecedentes fracasados (35 proyectos, cero sanciones) y una resistencia previsible por
> alcanzar a los propios legisladores, pero llega en una ventana inusual: cuatro proyectos
> de lobby presentados en mayo y diez expedientes vivos en las mismas dos comisiones.
> **Se define en Asuntos Constitucionales, donde a LLA le falta una sola firma no
> oficialista, y el radical Diógenes González integra y vicepreside las dos comisiones que
> deciden.** El número no incluye el recuento en el recinto: no tenemos las votaciones de
> la Cámara actual.

**Fuentes:** `datos/expedientes` (41.339 proyectos de ley, 2008-2026) · CKAN HCDN
Comisiones (autoridades e integrantes vigentes, 30/07/2026) · `variables/embudo` ·
`variables/proyecto/data/jefes_bloque.csv` · PDF `MEN-2026-178`.
