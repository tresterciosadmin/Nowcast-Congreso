# C3 — Formulación y salida del número

**BORRADOR** · **Absorbe:** 0007, 0012, 0013, 0016 · **Referencias:** 0015 (C5), 0025 (C4), 0006 (C6)

## 1. La regla

> **P(aprobación) = P_D · P_S**, condicional a que las dos cámaras voten. Cada cámara es la probabilidad de mayoría **por simulación** del roster nominal a esa fecha. **Todo ajuste se aplica al legislador, nunca al agregado** —la única excepción es un shock común por simulación—. **Un empate no aprueba.** Toda salida entrega **dos respuestas**: la probabilidad y los nombres (pivotes, banda).

## 2. Por qué

Un ajuste hecho sobre el agregado se apila con los de abajo, cuenta dos veces la misma incertidumbre y no dice sobre quién actuar (0016). El paso $P_i \to P_{\text{aprob}}$ **se contrastó por primera vez en esta auditoría** (`contraste_aprobacion.py`), sobre las $P_i$ limpias del censo, con la simulación del motor y el tipo de mayoría real de cada acta, contra el resultado oficial de **5.831 actas**: skill **0,25** [0,19; 0,30] sobre la tasa base de aprobación (94%). Para mayoría simple (5.394 actas, 93%) el Brier es 0,026. **No sirve donde la mayoría no es simple:** 256 actas de dos tercios (50% aprobadas, P media 0,68) tienen Brier **0,30**, peor que tirar una moneda (0,25); las 124 de tres cuartos, 0,185. Es condicional a los presentes (`p_presente = 1`): la asistencia, que en producción sí entra, sigue sin medirse.

## 3. Cómo se verifica

- `python coordinacion/AUDITORIA-2026-09/contraste_aprobacion.py` (~10 min, 2.000 simulaciones) → propuesto para el registro (C5).
- `modelo/agregador_institucional/tests/test_agregador.py` (el empate no aprueba, `umbral_aprobacion`, `agregador.py:106-123`).
- **Propuesto:** un test que falle si aparece un ajuste sobre `p_aprobacion` de una cámara fuera de `simular_votacion`.

## 4. Qué la invalida

- Que el contraste dé un Brier peor que la tasa base en mayoría simple.
- Que la independencia entre cámaras (FORMULA §I.0: "supuesto activo y falso") se mida y pese: ψ (arrastre) está **estimado y no implementado**, con offset contaminado (+7,7).
- Que el panel deje de ser un proyecto hipotético de mayoría simple.

## 5. Estado real hoy (verificado)

- **La cadena de cuatro puertas son dos simulaciones multiplicadas.** Los pasos A y C son la **identidad**: `puerta_a.COEF_POR_DEFECTO` es todo cero desde el 25-08 (`puerta_a.py:101`), pero `cargar_caracter`, `caracter_de` y `condicionar` (≈300 líneas) **se ejecutan en cada corrida** (`nowcast_puertas.py:828-830,853,867`). `p_final = b["p"] * d["p"]` (`:873`).
- **Cumplimiento de la doctrina:**
  - Cumple: el desvío, ε₀ y el piso `DESVIO_MIN_INDIVIDUAL = 0,02` se aplican **por legislador** (`ensemble.py:361`, `agregador.py:203-224`); el shock τη es la excepción 2 del ADR-0016 (común por simulación).
  - **No cumple:** con `INCERTIDUMBRE_LEGISLADOR=0` **reaparece el clip agregado 0,01** (`ensemble.py:367-376`). El piso de 0,02 (23,2% de los votos topan en 0,98) **no figura en FORMULA §I.00**.
- **Empate:** `umbral_aprobacion` devuelve `emitidos // 2 + 1` (`agregador.py:123`); cubierto por `test_agregador.py`.
- **Dos respuestas:** el panel devuelve `a_negociar` y la banda `[p5,p95]` (`nowcast_puertas.py:748-771`); la banda declarada al 90% cubre 63,6% (ver C4).
- **Diferencia con lo que ve el usuario:** el HTML publicado (`Nowcast-Puertas.html`) dice 98,01%; el motor de hoy da **61,3%** para el mismo caso.
- ADR-0006 (multitaxonomía por título) sigue "aceptado (diseño) / pendiente (implementación)".

**Historia:** 0007 (07-31) régimen de salida: *dos respuestas, siempre* · 0012 (08-22) formulación única por puertas; se dio de baja la v1 (`p_llega_recinto`) · 0013 (08-22) mayoría simple = la mitad más uno; antes `emitidos/2` hacía que un empate aprobara, y el error corría a favor de la aprobación en los casos ajustados · 0016 (08-26) la doctrina de la parte al todo.

**Se pierde:** los cuatro pasos como estructura de cálculo (dos son decorativos); el `p_llega_recinto` de la v1; el texto de `puerta_a` como "carácter observado colapsa a 1".
