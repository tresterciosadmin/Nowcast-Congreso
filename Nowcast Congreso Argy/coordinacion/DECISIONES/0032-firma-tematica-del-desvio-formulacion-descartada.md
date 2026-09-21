# ADR-0032 — Firma temática del desvío: esta formulación NO capta lo que pasa (y el motivo es la ley, no el tema). La línea sigue abierta.

**Fecha:** 2026-09-21 · **Estado:** MEDIDO, sin cambios en el motor · **Decide:** Claude, sesión
delegada por Franco (`coordinacion/PROMPT-FIRMA-TEMATICA-DEL-DESVIO.md`) · **Toca:**
`evaluacion/baseline/src/firma_tematica_{desvio,fase0_celdas,fase1_2}.py` (nuevos),
`evaluacion/baseline/tests/test_firma_tematica.py`, `datos/padron/data/gobernadores.csv` (nuevo,
APAGADO) · **Se relaciona con:** ADR-0026, ADR-0030, ADR-0031, ADR-0007

**Fórmula (ADR-0015 nivel 3): la fórmula no cambia.** Nada se prende, nada se consume.

## Veredicto (con las palabras que pidió Franco)

**Esta formulación no capta lo que pasa. No decimos que el fenómeno no existe** — los pivotes
existen y negocian por tema en la realidad; lo que no encontramos es una medición que lo vea.
La línea **no se cierra**. Lo que queda descartado, con motivo, está en el registro de abajo.

## Qué se midió

Objeto: d̃_{i,k} = (d_{i,k} encogido EB k=5 hacia el d̄_i propio) − d̄_i; desvío v2 del motor
(`disciplina.py`), sólo estando presente; pares (legislador, área) antes/después de cada recambio
(2015, 2019, 2023), sin promediar. Bootstrap por legislador para los IC.

### FASE 0 — celdas (y un desvío declarado del prompt)

- **Con "disputada" estricta (±5% del umbral) el test no corre**: 531 actas en toda la historia,
  **92 con tema**, **0 pares (legislador, área) con n≥5** en ningún recambio. Es el muro del prompt.
- Se cambió a **"contestada" = minoría ≥10% de los emitidos** (hay desvío que medir): 1.070 actas
  con tema. **Es un desvío del prompt, declarado.** Con eso: n≥5 → 1.546 pares, 218 legisladores
  con ≥3 áreas a ambos lados en el pooled — **pero 209 son del recambio 2015 (era K); el de 2023
  tiene 34 con n≥5 (<50)**, y los recambios 2019/2023 pasan por la era 2019-23, que tiene sólo 296
  actas (90 contestadas, 48 con tema).
- **Las 1.070 actas son 310 expedientes** (3,45 actas por ley): el n efectivo es la ley.

### FASE 1 — persistencia entre recambios (pooled, n≥5, IC95)

| medición | r | IC95 |
|---|---:|---|
| d sin centrar (control) | −0,054 | [−0,10; 0,02] |
| **d̃ CENTRADA (la firma)** | **+0,015** | [−0,03; 0,06] |
| d̃ neta de efecto-área | +0,002 | [−0,04; 0,05] |
| récord afirmativo (ref. ADR-0031) | −0,366 | [−0,45; −0,29] |

Por recambio (centrada, n≥5): 2015 +0,02 · 2019 −0,01 · **2023 +0,16 [−0,08; 0,36], n=115**.
Con n≥10 y 2023: +0,28 (n=47) — sin potencia para creerle. **Cámara:** Diputados +0,015, Senado −0,001.
**Por tercil de d̄:** disciplinados −0,02 · medio +0,12 [0,04; 0,21] (único IC que excluye 0, n≥5;
no replica en n≥3 con el mismo tamaño y es 1 de ~15 cortes) · díscolos +0,003 (**la firma no
existe más entre los díscolos**). **Continuidad de bloque:** mismo bloque +0,04, cambió +0,005.
**Validación de producto** (¿las 2 áreas de mayor d̃ antes son las de después?): coincidencia
0,388 vs azar 0,380, exceso **+0,008 [−0,03; +0,05]**. Nada.

Una versión previa de esta validación dio +0,069 "significativo": era un **artefacto** — `nlargest`
desempata por orden de fila y los díscolos-cero tienen muchos empates. Corregido con desempate
aleatorio.

### Dos hallazgos que valen más que el nulo

1. **Ni la lealtad general persiste entre eras.** El d̄ propio del legislador correlaciona
   −0,005 / −0,085 / +0,105 entre eras (continuadores, n≥10). Por eso el control "sin centrar"
   da ≈0 y **el contraste centrada-vs-sin-centrar no puede leerse**: no había lealtad que
   contaminara. Dentro de una era sí persiste (cronológica 0,33–0,53; por expediente 0,53–0,70).
   El desvío es relativo al bloque, y el bloque cambia con el gobierno.
2. **La "firma" que se ve dentro de una era es agrupamiento por ley, no perfil temático.**
   Partiendo las actas por azar la firma es confiable (r 0,47–0,79); partiendo por **expediente
   entero** cae a ≈0 (era 2015: 0,01; era 2019: 0,12). Cronológica: ≈0. Las actas de una misma
   ley (general + artículos) comparten tema y resultado. **Nota:** las actas con tema de la era
   2023 y de 2019-23 casi no tienen expediente vinculado (`tema_por_acta`) — no se pudo hacer esa
   partición ahí; se reporta "n/d", no se imputa.

### FASE 2 — cohesión de bloque por área (linaje, dispersión 1 − share modal; exploratoria)

Sin la bolsa "OTRO / PROVINCIAL" (que no es un bloque): n_actas≥5, **centrada r=+0,23** [0,16; 0,31],
7 linajes, 109 pares; sin centrar +0,42. Pero **por recambio: 2015 +0,33 · 2019 +0,64 (n=21) ·
2023 −0,23 (n=18)**. Positiva en las eras vieja, **se da vuelta en la era del producto**.
Es lo único distinto de cero, y con 7 linajes y n=18-21 por recambio **no se toma como señal**;
sí se deja como la formulación con más para dar. Lectura descriptiva de 2023 (n_actas≥5):
LLA más abierta que su promedio en SALUD y CYT, PRO muy cerrada en DESREG/DERSOC/SALUD, RADICALISMO
abierta en CYT/TRAB/POLINST — hipótesis para mirar, no resultado.

### FASE 3 — gobernadores (dato, apagado)

`datos/padron/data/gobernadores.csv`: 24 jurisdicciones × 4 períodos = 96 filas, con `confianza`
y `fuente` por fila. **Sólo el período 2023 tiene fuente pública (Wikipedia, con dos errores
visibles en la propia fuente: "Juan Pablo Valdés", Santiago del Estero "UCR")**; 2011-2019 salen
del conocimiento del modelo, **sin verificar** (confianza media/baja, con nombres marcados
dudosos: Corrientes, Misiones, San Luis, Santiago del Estero, Chubut). `parcial` en
`coincide_con_ejecutivo` es criterio subjetivo: definir una regla objetiva antes de usarlo.
**Sin consumidor** (un test falla si alguien lo importa). No se hizo el cruce exploratorio: no hay
firma que cruzar.

## Registro de formulaciones descartadas

| formulación | motivo del descarte |
|---|---|
| firma d̃ por (legislador, área) sobre actas **disputadas ±5%** | sin muestra: 92 actas con tema, 0 pares n≥5 |
| firma d̃ por (legislador, área), actas contestadas, **entre recambios** | r=+0,015 [−0,03; 0,06]; el nivel propio d̄ ni siquiera persiste entre eras |
| top-2 áreas de d̃ como predictor de "dónde negocia después" | +0,008 sobre azar, IC incluye 0 |
| firma por área **dentro** de la era | el 0,5–0,8 aparente es agrupamiento por ley: por expediente cae a ≈0 |
| contraste centrada vs sin centrar como test de "no es lealtad" | inservible: la lealtad no persiste entre eras, no hay contaminación que medir |

## Siguiente formulación candidata

**La unidad es la ley (expediente), no el área.** El n efectivo son 310 leyes, y la única
regularidad estable dentro de una era aparece al nivel de ley/acta. Candidata concreta: **"con quién
se desvía"** — coincidencia de desvío par a par (¿i y j rompen juntos?) en vez de tasa por área. Capta
al pivote como *coalición de desvío* (los que negocian juntos) y sobrevive a los cambios de bloque
porque no usa la línea de un bloque sino a los otros díscolos. Segunda: FASE 2 con más actas por
(linaje, área) (pedir más clasificación de tema).

## Qué dato haría falta

1. **Vincular expediente a las actas con tema de 2019 en adelante** (hoy casi no lo tienen).
2. **Más cobertura de tema en actas contestadas** (37% en la era 2023).
3. **Verificar la cobertura de la era 2019-23** (296 actas en cuatro años: parece agujero en la
   canónica; verificar antes de atribuirle nada).
4. Gobernadores contra fuente primaria y una regla objetiva para "coincide con el Ejecutivo".

## Sesgos declarados

Los que atraviesan un recambio no son una muestra al azar: son los que se sostienen. En el pooled
dominan los de 2015 (era K, desvío medio 0,094). d̄ medio de los continuadores 0,056 vs 0,066 de
todos los activos: algo más disciplinados. El desvío v2 (ADR-0004) usa la línea del propio bloque:
la referencia cambia cuando el legislador cambia de bloque.

Reproducir: `python evaluacion/baseline/src/firma_tematica_fase0_celdas.py` y
`python evaluacion/baseline/src/firma_tematica_fase1_2.py` (salidas en
`evaluacion/baseline/outputs/firma_tematica_*_2026-09-21.json`).
