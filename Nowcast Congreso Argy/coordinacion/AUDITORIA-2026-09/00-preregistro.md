# 00 — Pre-registro: qué evidencia confirma o refuta cada hipótesis

**Escrito el 2026-09-28, antes de leer los informes de los lotes de ADR y antes de correr las mediciones de la Fase 2 (reproducción del 0,1333 y del 63,6%, control independiente, invariancia al futuro).**

**Lo que ya había leído al escribirlo (para que el sesgo quede a la vista):** `ESTADO-REAL-DEL-MOTOR.md`, `URGENTE.md`, ADR-0034, FORMULA §I.00 y §IV.6-IV.7, `CLAUDE.md`, y el código de `nowcast_puertas.py`, `ensemble.simular_con_guardas`, `agregador.simular_votacion`, `puerta_a/d`, `beta_dictamen`, `bloque.proyectar_postura`. Esos documentos ya dicen que el 99,88% salía de un oráculo y no del `shift(1)`: **H1 en su forma fuerte probablemente se refute**, y se deja anotado antes de medir.

**Quién audita:** Claude (Sonnet 5.5, con Opus como asesor en la revisión metodológica y en el lote de ADR de la cadena central). El mismo tipo de agente que escribió los ADR 0026-0034 en "sesión delegada". Por eso los criterios de abajo se fijan antes, y al cierre un revisor que no vio el informe intenta refutar sus 10 afirmaciones principales.

## Criterios por hipótesis

| H | Se **confirma** si… | Se **refuta** si… | Evidencia que se mira |
|---|---|---|---|
| **H1** un solo error (el espejo/`shift(1)`), muchas consecuencias | los resultados contaminados que sostienen un término prendido o un número publicado comparten el mismo mecanismo | ≥2 mecanismos **independientes** explican cada uno ≥25% del inflado o de las decisiones erradas | Fase 2 tabla de scripts y fuentes de fuga; ADR-0034 §FASE 1 (0,3257 vs 0,1333, y la banda 99,88% → 63,6%) |
| **H2** banderas prendidas por delegación sin auditoría independiente | ≥3 de los ADR 0025-0034 que prenden/apagan figuran "Decide: Claude (delegado)" y ninguno cita una contrastación independiente del censo antes de prender | en ≥50% hay una contrastación independiente registrada (otro script, otra persona, otra fecha) | encabezados de ADR; `git show` de los commits que cambiaron cada default |
| **H3** complejidad sin retorno en la línea tema/capítulo/origen | ninguno de los ADR 0023, 0024, 0026-0033 deja un término **activo en el camino del número** con ΔBrier limpio que excluya 0 a favor (la observabilidad de 0031 no cuenta como término) | algún término activo de esa línea tiene medición limpia a favor | Fase 3 (lotes D y E) + Fase 4 clasificación EN EL CAMINO / DETRÁS DE BANDERA / SÓLO MEDICIÓN / NADIE LLAMA |
| **H4** la documentación dejó de ser un control | en la matriz de 10 hechos hay ≥3 con contradicción entre documentos vivos y ≥1 entre un documento y el **código** | ≤1 contradicción entre documentos y ninguna contra el código | Fase 4.4 |
| **H5** las reglas se agregan después del daño y no lo previenen | los commits que prendieron `RECORD_POR_TEMA` (16-09) y ε₀+τη (16-09) no cumplen ADR-0015 (nivel 2 y 3, FORMULA en el mismo commit) **o** cumplen y la regla igual no frenó nada | los commits cumplen ADR-0015 **y** la regla habría detectado el problema si se hubiera aplicado a la medición | `git show` de esos commits; ADR-0015 §texto |

Si H5 se confirma porque los commits **cumplían** la regla y aun así pasó el daño, el veredicto es **"regla del tipo equivocado"**: ADR-0015 exige presentar el cambio, no verificar la medición.

## Criterios de reproducción (Fase 2.5-2.6), fijados antes de correr

- **0,1333 reproduce** si el censo regenerado desde cero (copia limpia de `HEAD`, sin el parquet ignorado) da: mismo número de votos (691.845), skill global 0,1333 ± 0,0005, extremos del IC ± 0,003, y máx |ΔP_i| contra el detalle en disco < 1e-9. Si no, se identifica el primer voto que difiere y se **frena**.
- **63,6% reproduce** si `medir_tau_limpio.py` sobre el detalle regenerado da 63,6% ± 0,2 pp y sesgo −6,9 ± 0,2 votos. Se reporta además como **"cobertura condicional a los presentes"** (la simulación usa `p_presente = 1` y actas con ≥20 votos: `medir_tau_limpio.py:58-62`).

## Rúbrica de veredictos (Fase 2)

Vale la primera que aplique, por afirmación:
- **NO CONFIABLE:** no reproduce; o mide con espejo/oráculo lo que afirma del motor; o actúa sobre el número una fuga no acotada.
- **CONFIABLE:** reproduce, usa el motor real, pasa la invariancia al futuro, tiene IC por ley, y el resultado no cambia al re-muestrear por fecha de sesión.
- **CONFIABLE CON RESERVA:** todo lo demás, diciendo qué falta.

## Rúbrica de veredictos (Fase 3), una por decisión

¿Se ejecuta u obliga hoy?
- **No:** si otro ADR la revirtió → `SUPERSEDIDO`; si el código existe y está apagado → `INACTIVO`; si no → `REGISTRO-HISTÓRICO`.
- **Sí:** reglamento, mecánica o proceso → `VIGENTE-ESTRUCTURAL` *(categoría agregada por esta auditoría: el prompt no la prevé y los ADR de infraestructura no tienen "medición")*; con medición CONFIABLE a favor → `VIGENTE-SÓLIDO`; con medición NO CONFIABLE → `VIGENTE-EVIDENCIA-ROTA`; sin ninguna → `VIGENTE-SIN-EVIDENCIA`.
