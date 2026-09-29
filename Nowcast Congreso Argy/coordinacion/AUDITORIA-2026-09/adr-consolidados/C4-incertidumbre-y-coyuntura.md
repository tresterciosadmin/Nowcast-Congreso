# C4 — Incertidumbre y coyuntura

**BORRADOR** · **Absorbe:** 0008, 0025 · **Referencias:** 0016 (C3), 0034 (C5)

## 1. La regla

> **La incertidumbre se declara al nivel del legislador** —encogimiento afín ε₀ y un shock logit común τ·η por simulación— **y lo declarado se contrasta con lo observado:** una banda al 90% tiene que cubrir cerca del 90% y una probabilidad del 95% tiene que cumplirse cerca del 95%. **El ICG (coyuntura) está medido y desconectado**: entra sólo si mejora el pronóstico, según C5.

## 2. Por qué

ADR-0025 prendió ε₀+τη con una evidencia: la banda [p5,p95] del recuento contenía el resultado real el **99,88%** de las veces. Esa cifra salía de `agregador.backtest`, que le da a la simulación **la línea que cada bloque tuvo en esa misma acta** (`agregador.py:307-322,401-402`): mide la mecánica dado el resultado. Con las $P_i$ del motor en walk-forward limpio (`medir_tau_limpio.py`) la banda cubre el **63,6%** de 5.851 actas y el recuento esperado sale **6,9 votos por debajo** del real (sin τ: 14,8%, sesgo 2,8; el shock simétrico en logit baja la media cuando las $P_i$ son altas). La justificación original **cae**.

**Pero el término se sostiene por otra vía.** Contra el resultado oficial de 5.831 actas (`contraste_aprobacion.py`): con ε₀+τη el log-loss de P(aprobación) mejora **0,036** [0,018; 0,055] (pareado por ley) y las actas "seguras" (P > 0,95) que se rechazaron bajan de **230 a 23**; el Brier no es concluyente (−0,0018 [−0,005; +0,001]). Sin el término el modelo era sobreconfiado; con él es **subconfiado en los tramos altos** (P 0,91 → real 0,97; P 0,97 → real 0,99). A nivel individual, el piso de 0,02 más ε₀ mejora el Brier de $P_i$ (0,1391 → 0,1373; óptimo ε₀ ≈ 0,055) y el log-loss (0,524 → 0,432). ε₀ y τ se estimaron **sobre el mismo panel** en el que ahora se evalúan: no es una validación fuera de muestra.

## 3. Cómo se verifica

- `python modelo/ensemble/src/medir_tau_limpio.py` (63,6% y sesgo; escribe en una ruta versionada: correr en copia limpia).
- `python coordinacion/AUDITORIA-2026-09/contraste_aprobacion.py` (P(aprobación) contra resultados).
- `modelo/ensemble/tests/test_incertidumbre_legislador.py` (prendido y apagado).
- **Propuesto:** `calibracion_declarada.json` generado, y un test que falle si la cobertura observada difiere de la declarada en más de 5 puntos (hoy: 26,4).

## 4. Qué la invalida

- Un recalibrado fuera de muestra que dé un log-loss o una cobertura mejores con otros ε₀ y τ (los limpios: ε₀ 0,055, τ 1,197; Diputados 1,32, Senado 1,16).
- Que la asistencia, que en producción entra a la simulación y **no se midió**, cambie la cobertura.
- Que el monitoreo hacia adelante (`05` §5.3) contradiga la calibración.

## 5. Estado real hoy (verificado)

- `INCERTIDUMBRE_LEGISLADOR` ON, `EPSILON0 = 0,035`, `TAU = 1,19` (`nowcast_puertas.py:192-196`); **ningún test fija los valores**; la CLI del agregador usa **0 / 0** con los mismos nombres (`agregador.py:471-472`).
- **El panel se movió de 0,9801 a 0,6132** cuando se prendió (commit `64ff248`, 15-09 22:10). El HTML publicado **no se regeneró**: dice 98,01%; hoy el motor da 61,3%.
- **URGENTE U2 sigue abierto:** "TAU=1,19 y EPSILON0=0,035 siguen". La decisión sobre la banda declarada al 90% es de Franco (`07` del informe).
- **ICG:** medido (γ ≈ 1,0 en desvío ≥ 0,10, bootstrap por legislador, otra cadena; nunca como predictor). Está **desconectado del número**: sólo se muestra en el panel (`casos/nowcast_puertas_html.py:47-60`). `icg_contexto.py` (224 líneas) no lo importa nadie; `ingesta_icg.py` lo alimenta desde `icg-mensual.yml`. La enmienda del 11-08 eliminó el mecanismo 2 y se llevó la asimetría de la teoría prospectiva sin que nadie lo notara por dos semanas.
- **Comentarios que contradicen:** `tablero_datos.js:318` afirma el 99,88% "del lado seguro" en el mismo archivo que en `:253` dice 63,6%; EN-HUMANO conserva el 99,88%.

**Historia:** 0008 (08-04, ICG modulador; enmienda 08-11) · 0025 (09-16, Franco: "Hagamos el cambio") ε₀+τη, en lugar del clip agregado.

**Se pierde:** "la banda es conservadora (99,88%)"; el ICG como modulador activo; la lectura de τ como "subestimado por el offset con fuga" (con el offset limpio pasa de 1,186 a 1,197: 1%; lo que se mueve es ε₀, de 0,015 a 0,055).
