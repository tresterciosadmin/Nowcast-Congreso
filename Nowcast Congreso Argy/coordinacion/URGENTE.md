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


> **El proyecto está PARADO para la revisión intensiva de Franco (28-09-2026).** Lo que
> sigue no es una cola de tareas para retomar ya: es lo que la revisión tiene que decidir.
> Punto de partida: `coordinacion/ESTADO-REAL-DEL-MOTOR.md`. U1 (la fuga del harness) se
> cerró en ADR-0034; el registro está en `ESTADO-DEL-PROYECTO.md`.

## U2 — [2026-09-28, Claude, ADR-0034] La banda del recuento cubre el 63,6%, no el 90% que declara

**Qué pasa.** ε₀+τη está PRENDIDO (ADR-0025) con la justificación de que la banda [p5,p95]
contenía el recuento real el 99,88% de las veces. Ese backtest (`agregador.backtest`) le da al
agregador la **línea de bloque observada en la misma acta**: mide la mecánica con un oráculo.
Con las $P_i$ del motor en walk-forward limpio y la simulación del motor
(`medir_tau_limpio.py`), la banda cubre el **63,6%** de 5.851 actas, y el recuento esperado sale
**6,9 votos por debajo del real** en promedio. Sin τ cubre el 14,8%: τ ayuda, pero no alcanza.

**Por qué es urgente.** Es el término que hace "honestas" las bandas del producto, y hoy
promete 90% de confianza con 64%. **τ no es el problema** (re-estimado con el offset limpio da
1,197, igual que el de producción). Candidatos a mirar, no probados: el shock τη en logit baja la
media del recuento cuando las $P_i$ son altas (Jensen: sesgo 2,8 votos sin τ, 6,9 con τ); el ε₀
óptimo con el offset limpio es 0,055 (producción: 0,035); el estimador de τ usa la mediana por
acta.

**Qué hacer.** Decisión de Franco. Nada se cambió: TAU=1,19 y EPSILON0=0,035 siguen.

## U3 — [2026-09-28, Claude, ADR-0034] β (prendido), δ, θ y ψ se estimaron sobre un offset con fuga

`estimar_beta_dictamen.py`, `estimar_psi_arrastre.py`, `estimar_theta_sobre_tablas.py` (y
`validar_beta_dictamen_walkforward.py`, que reusa su panel) arman su propio récord con
`shift(1)` por fila, sin guard, sin encoger y sin origen. Están marcados en el código. β está
PRENDIDO y el censo no lo mide (el harness no lo aplica). El chequeo de dirección de β con el
offset limpio está en ADR-0034. **Qué hacer:** decidir si se re-estiman con el panel del censo
(`censo_detalle_paralelo.py` deja la $P_i$ limpia voto a voto) antes de seguir confiando en β.

## U4 — [2026-09-28, Claude, ADR-0034] Tres cortes temporales que no son historia de votos pero pueden filtrar

1. **La ficha de desvío individual** (`disciplina_individual.csv`, la usa `roster_nominal`) se
   calcula con toda la historia: en cualquier backtest de `nowcast()` el desvío mira el futuro.
   Entra en la rama de bloque (4,7% de los votos del censo, skill −0,38) y en β (lealtad). El
   harness usa el desvío del linaje en su lugar (declarado en su docstring).
2. **`puerta_a.caracter_de`** ve dictámenes con `fecha_dictamen <= corte`: 36 pares
   dictamen–acta del mismo día (34 proyectos). Si un dictamen del día de la sesión es
   información legítima es una pregunta de reglamento, no de código.
3. **El 15,3% de los votos cae en actas sin ley identificable** (`ley_por_acta`): ahí el corte
   por expediente no ve nada. Es fuga residual en el número publicado, de tamaño desconocido.
