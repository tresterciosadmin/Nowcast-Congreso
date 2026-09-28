# 🔴 URGENTE — lo primero que se lee y se resuelve en CADA sesión

> **Regla de la casa (CLAUDE.md):** cualquiera del equipo — persona o Claude —
> abre este archivo **al empezar**, antes de reclamar tarea. Si hay algo acá, se
> resuelve o se decide explícitamente postergarlo (dejando dicho por qué).
> Nada se toca "después": lo que está acá bloquea o ensucia trabajo de otros.
>
> **Cómo usarlo:** al detectar algo urgente, se agrega un bloque con fecha, quién
> lo detectó, qué hay que hacer y por qué es urgente. Al resolverlo se BORRA de
> acá (queda el registro en `ESTADO-DEL-PROYECTO.md`, que es la bitácora
> permanente). Este archivo debería estar vacío la mayor parte del tiempo.
>
> ⚠️ **Nada de secciones de "resueltos".** El 04-08 se dejó una, y adentro quedó
> enterrado un pendiente **vivo** (la ingesta del Senado leyendo el padrón viejo)
> que nadie vio durante dos días. Un archivo que existe para que no se pueda no
> ver algo no puede tener una zona donde las cosas se esconden. Lo resuelto se
> borra: para eso está la bitácora.

---

## U1 — [2026-09-28, Claude, ADR-0033] El harness del censo cuenta votos del MISMO DÍA como historia

**Qué pasa.** `baseline_voto_individual.correr` arma el récord con
`shift(1).expanding()` sobre votos ordenados por `fecha`: una acta ve como "historia" las
actas previas de la misma sesión (los artículos de la misma ley, en un orden arbitrario dentro
del día). Un nowcast hecho antes de la sesión no tiene esa información.

**Cuánto mueve (medido, `record_por_origen_brazos.py --historia estricta`):** skill global
**0,161 → 0,092**; 2019-23 0,331 → 0,009; desde 2023 0,063 → −0,029. El guard (ADR-0018) sigue
ganando con historia estricta, pero **todos los niveles publicados están inflados**.

**Por qué es urgente — lo que puede estar contaminado:**
1. **`RECORD_POR_TEMA` está PRENDIDO** (fila 18 de FORMULA, ADR-0026) por un "11,1% menos
   Brier" medido con el mismo `shift(1)` (`medir_rec_por_tema.py`, `fase1_rec_por_tema.py`).
   Los artículos de una ley comparten tema: es la medición más expuesta. **Re-medir con
   historia estricta antes de seguir confiando en esa bandera.**
2. El motor tiene la misma forma de fuga en modo backtest: `nowcast_puertas._alineacion_base`
   corta con `fecha <= hasta` (inclusive) y `proyectar_postura` con `<`. En producción (fecha
   futura) no muerde; en cualquier backtest del motor, sí.
3. "Número a batir" de FORMULA (0,1611) y comparaciones de ADR-0018/0024/0026/0028.

**Qué hacer.** Decisión de Franco: (a) agregar `--historia estricta` al harness (la función ya
existe en `record_por_origen_brazos._previos`) y re-correr el censo (~14 min con
`censo_detalle_paralelo.py`); (b) re-medir el récord por tema; (c) `<=` → `<` en
`_alineacion_base` (cambio al motor: ADR-0015).
