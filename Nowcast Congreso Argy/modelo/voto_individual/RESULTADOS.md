# RESULTADOS — Índice de disciplina individual + set pivote (gate 1, ADR-0003)

**Corrida:** 2026-07-02 (base AMPLIADA con Senado 2015–2023, PC de Valle) · `python modelo/voto_individual/src/disciplina.py`
**Base:** canónica — 5 fuentes (Década Votada + CKAN + argentinadatos + Excel 2026 + **senado oficial 2015–2023 con bloque de época**), 2001–2026 ambas cámaras. Hueco mayor restante: Diputados 2020–2023.

## Metodología
Igual vara que `evaluacion/baseline`: votos sustantivos (AFIRMATIVO/NEGATIVO), sin `SIN BLOQUE`. La posición del bloque en cada acta se calcula **leave-one-out** (mayoría del resto del bloque; mínimo 5 votos del resto, sin empates). **Desvío** = votar contra esa mayoría. Disputadas = minoría ≥10% del acta.

## Cobertura
474.744 votos medibles en 5.206 actas (de 600.649 sustantivos; se descartan bloques chicos/empates). 1.255 legisladores con ≥50 votos medibles. Fichas completas por legislador en `variables/legislador` (1.972 fichas; 4.795 filas legislador×período en 14 períodos).

## Resultados (gate 1: dimensionar el set pivote)

Tasa de desvío global: **1,76%**. Mediana por legislador: **0,81%**; p90: **6,37%**.

| Umbral de divergencia | Legisladores (global) | % de medibles | En disputadas |
|---|---|---|---|
| ≥2% | 344 | 27,4% | 469 |
| ≥5% | 163 | 13,0% | 232 |
| ≥10% | 67 | 5,3% | 112 |
| ≥15% | 35 | 2,8% | 58 |

**Lectura del gate.** La hipótesis de las "10–20 bisagras" se sostiene: el desvío está muy concentrado (mediana 0,77% vs. p90 6,55%). A ≥10% en disputadas quedan ~105 legisladores en 25 años; por período legislativo el set activo es de decenas y por votación concreta baja a la decena. **Gate 1: APROBADO** — hay señal individual concentrada que el promedio de bloque tapa.

**Señal 2022–2026 (drift de disciplina), confirmada con la base completa.** El top de díscolos está dominado por la era reciente: Fernández E. (58%), Fernández A. (53%), Monzó (45%), Massot (45%), Calletti (43%), Agost Carreño (42%), Arrieta (32%), Juliano (31%), Manes (30%) — todos 2022–2026, con 200+ votos cada uno. El baseline anual acompaña: acc en disputadas cae a 0,946 (2024) y 0,923 (2025), mínimos de la serie salvo 2002. Validez externa: los nombres coinciden con díscolos conocidos del período (ex-PRO de Encuentro Federal, radicales críticos, ex-LLA).

**Hallazgo del Senado 2015–2023 (territorio recién medido).** Aparece un caso nuevo en el top: **García, Virginia María (Senado 2016–2017): 34% de desvío global y 75% en disputadas** (232 votos) — la tasa en disputadas más alta de toda la base. Cae justo en la ventana de la ruptura FpV→FpV-PJ del interbloque, la zona que el padrón del equipo marca con filas `REVISAR`: candidata #1 de la auditoría de etiquetas de bloque antes de tomar el número como indisciplina real. El resto del top se mantiene estable (era 2022–2026 dominante).

**Caveat de interpretación.** Tasas extremas (>40%) pueden mezclar dos cosas: indisciplina real y **etiqueta de bloque desactualizada** (legislador que migró y la fuente lo sigue listando en el bloque viejo). Antes de usar el índice en producción, revisar el historial de bloque de los top-20 contra `variables/legislador/data/legislador_bloques.parquet`.

## Salidas
- `outputs/disciplina_individual.csv` — una fila por legislador (tasas global / disputadas / tramo reciente).
- `outputs/disciplina_por_periodo.csv` — legislador × período parlamentario × cámara (la unidad de análisis: cada recambio reconfigura los escaños).
- `outputs/disciplina_por_anio.csv` — legislador × año (time-aware).
- `outputs/set_pivote.json` — el resumen de arriba, reproducible.

## Próximos pasos (piezas b–d del ADR)
1. Auditar etiquetas de bloque de los top díscolos (caveat de arriba).
2. Modelo de defección: P(desvía | tema, cercanía de la votación, período, provincia).
3. Recuento como distribución (Bernoulli por legislador) + detección de pivotes por ley (gate 2).

---

*Historial: la primera corrida (2026-07-01, base parcial 2001–2014+2026 por falta de red en el sandbox) dio el mismo patrón cualitativo: desvío concentrado y salto en 2026 (5,11% vs 0,1–0,5% en 2011–2014). Los números de arriba la reemplazan.*
