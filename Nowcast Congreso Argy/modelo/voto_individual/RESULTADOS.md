# RESULTADOS — Desvío v2 (indisciplina total) · ADR-0004

**Corrida:** 2026-07-02 · base completa (5 fuentes, 2001–2026) · `python modelo/voto_individual/src/disciplina.py`
**Definición:** ver ADR-0004 — conductas (aprobar/rechazar/no acompañar), línea = mayoría de TODOS los escaños del bloque, estricta con abstenciones/ausencias, desempate por linaje, parcial en OTRO/PROVINCIAL, presidentes de Diputados excluidos. **Los números de la metodología v1 quedaron superseded** (medían solo voto cruzado entre presentes; ~1,8%).

## Cobertura
823.001 votos medibles en 5.212 actas (se excluyen SIN BLOQUE, placeholders y presidencias de Diputados: 1.590 filas). Método de resolución: 95,4% línea de bloque · 4,5% desvío parcial (bloques sin mayoría en la bolsa OTRO/PROVINCIAL) · 0,1% desempate por linaje.

## Resultados

Desvío medio global: **18,9%**. Mediana por legislador (n≥50): **16,4%**; p90: **36,4%**. La lectura cambió respecto de v1: esto es **indisciplina total** — no acompañar la línea del bloque por cualquier vía, incluida la silla vacía. Por eso el nivel general se parece a la tasa de ausentismo (~18%): la mayoría de los "desvíos" son ausencias individuales cuando el bloque fue a votar.

**El top pasa a estar dominado por quienes no usan la banca:** N. Kirchner diputado 2010 (96%), Insaurralde 2014 (67%), bancas en licencia de funcionarios (Alicia Kirchner 67%), De Vido suspendido Art. 70 (69% — ver pendiente abajo). Los díscolos "de voto" siguen visibles sobre todo en **disputadas**: Fernández E. 91%, Manes 79% — en las votaciones al filo, donde más duele.

## Caveats y pendientes (detalle en ADR-0004)
1. **Suspensiones y licencias** computan como no acompañar — decidir si se excluyen como las presidencias.
2. **Reclasificar OTRO/PROVINCIAL** (45% de los votos) hacia linajes → amplía el desempate por espacio.
3. Ponderación por trascendencia de la votación (futuro).
4. Disciplina ideológica por taxonomía (mitiga monobloques; depende de PLAN 1B.3).
5. Etiquetas de bloque desactualizadas pueden inflar tasas (auditoría con Franco pendiente; caso García 2016-17).

## Salidas
- `outputs/disciplina_individual.csv` · `disciplina_por_periodo.csv` · `disciplina_por_anio.csv` — índices (el desvío ahora puede ser fraccional).
- `outputs/desvios_por_voto.parquet` — voto por voto (conducta, línea, método, desvío) → alimenta la columna `desvio` de la tabla Votos de datos/export.
- `outputs/set_pivote.json` — resumen reproducible.
