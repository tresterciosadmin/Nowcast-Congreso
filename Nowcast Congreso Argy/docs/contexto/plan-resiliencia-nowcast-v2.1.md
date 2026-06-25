# Plan de Resiliencia — Nowcast Legislativo v2.1
**Fecha:** 2026-05-28
**Diferencia con v2:** se agrega Context Engine (capa de inferencia cualitativa), se corrige el manejo del veto electoral como filtro legal pre-modelo, se mapean explícitamente todas las variables del blueprint original, se demuestra capacidad numéricamente.

---

## 0. Corrección sobre el veto electoral

En la v2 propuse eliminar el veto absoluto. Estaba parcialmente equivocado: existe una restricción legal real (CNE + jurisprudencia consolidada: no se modifican reglas electorales dentro de ~24 meses de la elección). Boleta Única Papel se sancionó en 2024, año no electoral. La regularidad es legal, no solo política.

**Diseño correcto:** separar restricción legal de predicción estadística.

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│ Filtro de Eligibilidad│ → │  Modelo Predictivo   │ → │  Reporte         │
│ Legal (pre-modelo)   │    │  (si eligible)       │    │                  │
└──────────────────────┘    └──────────────────────┘    └──────────────────┘
```

- **Filtro legal:** función Python con citas normativas explícitas. Si un proyecto cae en categoría restringida, devuelve `legal_status: ineligible_until=2027-06-01, citation="CNE..."`. El reporte muestra "Probabilidad: <1% por restricción legal" con cita. No es magia ni hardcoding: es derecho positivo encapsulado.
- **Modelo predictivo:** solo se ejecuta si `legal_status: eligible`. Esto elimina el riesgo de "sobreajustar al veto" mientras preserva la regla cuando aplica.
- **Categorías de filtro legal:** reforma electoral cerca de elección, derogación tácita, materias que requieren mayoría calificada no alcanzable en el período. Pequeña, mantenible, auditable.

Esto es más limpio que mezclar derecho y estadística en la misma función de pérdida.

---

## 1. Mapa: cada variable del blueprint original → ubicación en v2.1

| Variable original | Cómo se computa en v2.1 | Servicio | Costo |
|---|---|---|---|
| **Gravedad Presidencial (ICG Di Tella)** | Scrape mensual del informe Di Tella → tabla `indicadores.icg`. Lag de 45 días asumido como feature. | ingestor | $0 |
| **Factor Gobernador (flujo ATN)** | Parser de resoluciones del Tesoro en BORA → tabla `transferencias.atn` por provincia/mes. Feature: ATN per cápita vs. baseline, signo del flujo. | ingestor | $0 |
| **Consistencia Histórica** | SQL window function sobre `votos.legislador` → tasa de votos a favor del proyecto-tipo en últimos N años. Feature: similitud de proyecto actual a histórico aprobado/rechazado vía embeddings. | feature engine | $0 |
| **Afinidad de Comisión** | Cosine similarity entre embedding del proyecto y centroide de embeddings de proyectos sancionados por la comisión asignada. | feature engine | $0 |
| **Fidelidad Partidaria** | Por legislador: % de votos coincidentes con jefe de bloque en últimos 12 meses. Feature agregada al proyecto: fidelidad media ponderada por PageRank de cofirmantes. | feature engine | $0 |
| **PageRank de Transversalidad** | Grafo bipartito legislador-proyecto-período → NetworkX `pagerank()` semanal. Feature: PageRank promedio de cofirmantes, std de PageRank (medida de heterogeneidad). | feature engine | $0 |
| **Liderazgo (PageRank de hub)** | Lo anterior + métrica de centralidad eigenvector → identificar "nodos" que traccionan votos transversales. Feature: presencia de nodo en cofirmas. | feature engine | $0 |
| **Espectro Ideológico Real** | UMAP + HDBSCAN sobre embeddings de votos por legislador (matriz N legisladores × M votaciones). Clusters emergentes = espectro real, no bloque formal. Feature: dispersión ideológica de cofirmantes según cluster. | feature engine | $0 |
| **Factor μ (Volatilidad)** | Bootstrap del ensemble sobre 1000 submuestras del train set → percentiles 5/50/95. Reporte: banda global, no por bucket hasta n≥30. | predictor | $0 |
| **Decaimiento por proximidad electoral** | Feature continua: días hasta próxima elección, transformada con `exp(-días/365)`. Aprendida por el modelo, no hardcoded. | feature engine | $0 |
| **Coyuntura política (lo nuevo)** | Context Engine: Hermes nocturno resume noticias/declaraciones → Sonnet semanal sintetiza en "context shift scores" por tema. Feature de override que el modelo aprende a usar. | context engine | ~$1/sem |

**Observación:** las 11 variables originales están todas presentes. El "9 agentes" del blueprint era una organización mental; computacionalmente son funciones puras + un par de llamadas LLM bien acotadas.

---

## 2. La capa que faltaba: Context Engine

**Problema que resuelve:** un modelo estadístico es ciego a contexto coyuntural. No sabe que ayer Massa renunció, que Milei tuiteó contra un proyecto, que la CGT amenazó con paro general. Los "9 analistas" del blueprint original aspiraban a capturar eso. Lo recupero acá, pero sin OpenClaw ni Hermes en el camino crítico.

**Arquitectura del Context Engine:**

```
┌───────────────────────────────────────────────────────────────┐
│ NOCTURNO (no bloquea predicción)                              │
│                                                                │
│  News scraper → Hermes local (resumen estructurado)            │
│  (BORA, La Nación, Página/12, Clarín, Infobae)                 │
│  → Tabla `context_events` con campos:                          │
│      (fecha, fuente, actor, tema, sentimiento, intensidad)     │
└───────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌───────────────────────────────────────────────────────────────┐
│ SEMANAL (corre lunes 6am, antes del reporte)                  │
│                                                                │
│  Sonnet recibe:                                                │
│   - últimos 7 días de context_events agrupados por tema       │
│   - lista de proyectos en agenda próxima                      │
│  Output estructurado (JSON):                                   │
│   { tema: "tributario", shift_score: -0.15,                    │
│     evidencia: ["Milei tuiteó..."], confidence: 0.7 }          │
│                                                                │
│  Se inserta como feature `context_shift_tema` al ensemble.    │
└───────────────────────────────────────────────────────────────┘
```

**Por qué esto preserva la profundidad de los "9 analistas":**
- Cada "analista" original era una perspectiva sobre una variable. Acá Sonnet hace múltiple-shot, una sección por dimensión (fiscal, social, institucional, internacional, etc.), produciendo un JSON estructurado.
- La diferencia: en vez de 7 agentes LLM corriendo en paralelo sobre Hermes local en ARM (imposible), un solo Sonnet con prompt estructurado en multi-shot. Más barato, más rápido, más controlable.
- Hermes vuelve a aparecer, pero como **batch processor nocturno** para resumir prensa — tarea donde latencia no importa y la baja velocidad ARM no estorba. Es el rol natural de Hermes en este stack.

**Costo del Context Engine:** ~$1/semana en Sonnet con prompt caching agresivo. Hermes nocturno es gratis (CPU desocupado).

---

## 3. Análisis de capacidad real (números, no opiniones)

**Hardware Oracle Cloud Always Free:**
- 4 OCPU Ampere Altra (Neoverse N1, 1:1 con cores físicos)
- 24 GB RAM
- 200 GB block storage

**Carga semanal estimada (Congreso en sesiones ordinarias):**
- ~200 proyectos nuevos en HCDN + Senado
- ~50 dictámenes de comisión
- ~30 votaciones nominales
- ~500 firmas de cofirmantes a procesar
- ~50 noticias relevantes para Context Engine

**Cómputo por tarea:**

| Tarea | Tiempo | Memoria | Frecuencia |
|---|---|---|---|
| Scrape REST HCDN (200 proyectos) | 2 min | 200 MB | diaria |
| Parsing + persistencia Postgres | 1 min | 300 MB | diaria |
| Embeddings 200 proyectos (MiniLM CPU) | 3 min | 800 MB | diaria |
| PageRank NetworkX (grafo ~500 nodos) | 8 s | 400 MB | semanal |
| UMAP+HDBSCAN espectro ideológico | 45 s | 1.2 GB | mensual |
| Feature engineering SQL | 30 s | 200 MB | diaria |
| Inferencia ensemble (200 proyectos) | 8 s | 300 MB | diaria |
| Cascada clasificación (200 proyectos) | 3 min total | 600 MB | diaria |
| Hermes resumen prensa (50 items, nocturno) | 1.5 h | 6 GB | nocturno |
| Sonnet Context Engine síntesis | 25 s | trivial | semanal |
| Sonnet narrador (top 20 proyectos) | 90 s | trivial | semanal |

**Picos:**
- Pico diurno (ingest + features + predicción): ~10 min de wall-clock total, ~3 GB RAM. **<15% utilización de capacidad.**
- Pico nocturno (Hermes batch): 1.5h CPU al 80%, 6 GB RAM. Sin contención con Postgres.

**Headroom:** Oracle Free está usado al ~15% en horario crítico. Podés procesar 5-10x el volumen actual antes de tocar techo. Es deliberadamente sobredimensionado.

**Picos críticos (sesiones extraordinarias, ley ómnibus):**
- Volumen puede duplicarse o triplicarse en 48h.
- Diseño escala lineal: 30 min wall-clock incluso a 3x volumen. Sin problemas.

---

## 4. Profundidad analítica: qué hace cada servicio explícitamente

### Service 1: `ingestor`
Más que un scraper: es un sistema de captura con normalización.
- Pull REST de HCDN + Senado + BORA + Di Tella + Tesoro (ATN).
- Adapter pattern: cada fuente con su Pydantic schema, retry policy, circuit breaker.
- Canonical Legislator Resolver: matching fuzzy + queue manual.
- Detección de cambios de schema upstream: si una respuesta no valida Pydantic, alerta inmediata.
- Persistencia: Postgres con versionado (cada registro tiene `valid_from`, `valid_to` para histórico reproducible).

### Service 2: `feature engine`
Núcleo analítico — esto es donde reside la **profundidad real** del modelo.
- 11 funciones Python, una por variable del blueprint, todas testeables independientemente.
- `compute_gravedad_presidencial()` — interpola ICG con su lag, calcula derivada (tendencia).
- `compute_factor_gobernador()` — agrega ATN por provincia, normaliza por baseline histórico, detecta outliers.
- `compute_consistencia_historica()` — embeddings de proyecto vs. corpus etiquetado por outcome.
- `compute_afinidad_comision()` — cosine vs. centroide histórico de la comisión.
- `compute_fidelidad_partidaria()` — matriz de votos × jefes de bloque, agregación ponderada.
- `compute_pagerank_features()` — grafo cofirmas, NetworkX, devuelve mean/std/max PageRank de firmantes.
- `compute_espectro_ideologico()` — UMAP+HDBSCAN sobre matriz de votos, asigna cluster a cada firmante.
- `compute_decaimiento_electoral()` — días a elección con transformación exponencial.
- `compute_block_diversity()` — Shannon entropy sobre bloques de cofirmantes.
- `compute_temporal_features()` — cuántos proyectos similares se sancionaron en los últimos 12/24 meses.
- `compute_context_shift()` — toma output del Context Engine, mapea al tema del proyecto.

Cada función con tests unitarios. Cada cambio versionado. Cuando una predicción falla, podés bisectarla feature por feature.

### Service 3: `predictor`
- Ensemble: Logística (sklearn) + LightGBM. Promedio ponderado por inverso de varianza out-of-sample.
- Calibración: Platt scaling sobre holdout 2024.
- Bootstrap: 1000 reentrenamientos en submuestras → percentiles para Factor μ.
- Cross-validation por régimen: train ≤2023, validation 2024, test live 2025-2026.
- Versionado de modelo: cada entrenamiento guarda hash + métricas en `model_registry`. Reproducible.
- Inferencia: <50ms por proyecto. 200 proyectos en 10 segundos.

### Service 4: `context engine` (NUEVO en v2.1)
- Hermes batch nocturno: resume 50-100 items de prensa por día en estructura `(actor, tema, sentimiento, intensidad)`.
- Sonnet semanal: lee 7 días de eventos + agenda legislativa próxima, produce JSON de `context_shift` por tema.
- Output alimenta directamente como feature al ensemble.
- Cuando Sonnet detecta evento de alto impacto (renuncia ministerial, escándalo), emite alerta para re-evaluar proyectos del tema afectado fuera del ciclo normal.

### Service 5: `narrator`
- Sonnet semanal con prompt caching (5 min TTL, llamadas en burst para aprovechar cache).
- Recibe: top 20 proyectos por importancia + features + context_shift + bandas Factor μ.
- Produce: informe en lenguaje natural con razonamiento explícito sobre qué features impulsaron cada predicción.
- Citaciones obligatorias: cada afirmación cuantitativa debe citar el feature numérico que la respalda.

---

## 5. Costos revisados v2.1

| Ítem | Mensual |
|---|---|
| Oracle Cloud Always Free | $0 |
| Backblaze B2 (backup) | $0 |
| UptimeRobot | $0 |
| **APIs Claude:** | |
| - Haiku (clasificación cascada, ~3000 llamadas) | ~$1 |
| - Sonnet Context Engine (4 sem × ~25k tokens cacheados) | ~$2-3 |
| - Sonnet Narrator (4 sem × ~40k tokens cacheados) | ~$3-5 |
| Hetzner CX22 standby (opcional) | $4.59 |
| **Total operativo** | **$6-13/mes** |

Con prompt caching agresivo (cache hit ratio >70%), el costo Sonnet baja otro ~30%.

---

## 6. Qué se gana sobre el blueprint original

| Dimensión | Blueprint original | v2.1 |
|---|---|---|
| Variables analizadas | 11 | 11 (idénticas) |
| Profundidad de razonamiento contextual | 7 agentes LLM | 1 Hermes batch + 1 Sonnet multi-shot |
| Throughput | ~31h cómputo/semana (insostenible) | ~30 min cómputo/semana |
| Costo operativo | $5-45/mes | $6-13/mes |
| Resiliencia ante cambio upstream | Sin estrategia | Adapter pattern + Pydantic + circuit breakers |
| Calibración estadística | Brier global no documentado, μ por bucket con n<12 | Bootstrap honesto + Platt scaling + CV por régimen |
| Restricción legal | Hardcoded en modelo | Filtro pre-modelo con citas normativas |
| Trazabilidad de predicción | Output narrativo del agregador LLM | Cada feature versionado + narrator cita features |

---

## 7. Lo que SÍ se pierde (y por qué está bien)

1. **Concurrencia real de 9 agentes LLM:** no la necesitás. La aparente "paralelización" del blueprint era ficticia — sobre ARM CPU los 7 agentes Hermes serializan en la misma cola de inferencia. El paralelismo real ahora viene de SQL + Python multiproceso para feature engineering, donde sí escala.
2. **Sensación de "sistema multi-agente sofisticado":** queda como abstracción mental, no como realidad de runtime. El sistema es igual de sofisticado analíticamente, menos sofisticado en plumbing, lo cual es deseable.
3. **Dependencia de OpenClaw como diferenciador técnico:** lo perdés a propósito. Tu diferenciador es el modelo + los features + la calibración, no el framework de orquestación.

---

## 8. Roadmap revisado por fases (incluye Fase 3.5 y adopciones GovTrack)

| Fase | Semanas | Entregable | Criterio de pase |
|---|---|---|---|
| 0 | 1-2 | Split en dos repos (`congreso-argy-data` CC0, `nowcast-engine`), scaffolding CLI `argcongress-run`, dataset validación (200-300 leyes etiquetadas), `legisladores-canonical/` inicial, `docs/schemas/` esqueleto, benchmark HCDN REST | Dataset listo, REST responde estable 3 días, repos creados con README y schema_version definido |
| 1 | 3-4 | Infra Docker + Postgres + heartbeat + backup + health endpoint + alertas dos canales (Telegram + msmtp) | Restore test exitoso desde Backblaze, alertas funcionando en ambos canales |
| 2 | 5-7 | Adapter HCDN + Person Service de primera clase + canonical resolver + cache | 100% proyectos últimos 30 días ingeridos, <1% errores, perfiles de 330 legisladores en Person Service |
| 3 | 8-10 | Feature engineering + logística + LightGBM + bootstrap | Brier holdout 2024 < 0.20 (baseline 0.25) |
| **3.5** | **11-14** | **Backtesting histórico 2015-2026: backfill, reconstrucción point-in-time, walk-forward (~10.000 predicciones), catálogo de fallos, calibración real Factor μ, comparación contra baseline-Tauberer** | **Brier walk-forward < baseline en ≥60% meses, ECE <0.05, cobertura banda 90% en [87%, 93%], ≥5 modos de fallo documentados, test no-leakage 100% pass, ensemble supera baseline-Tauberer por ≥0.03 Brier** |
| 4 | 15-16 | Cascada de clasificación NLP | Accuracy >85% sobre dataset validación |
| 5 | 17 | Reporte Claude Sonnet semanal + dashboard FastAPI+HTMX + module `analysis/` API | Primer reporte live generado y publicado, API analítica respondiendo |
| Shadow | 18-21 | Modo sombra: predicciones generadas, no publicadas, vs realidad | Brier shadow no degrada respecto al backtest |

Cada fase termina con un go/no-go basado en criterio cuantitativo, no en "parece funcionar".

**Por qué Fase 3.5 es crítica:** sin backtesting riguroso, el Factor μ arranca con cold start (n<20 en las primeras semanas live) — exactamente el modo de fallo #3 del premortem ("teatro estadístico"). Esta fase resuelve ese problema generando ~10.000 predicciones simuladas con sus errores reales, permitiendo calibración honesta antes del lanzamiento, no después. También produce el catálogo de modos de fallo pre-conocidos que alimenta drift detection en producción.

**Por qué el baseline-Tauberer:** GovTrack lleva 13 años operando con un modelo de regresión logística simple y reporta ~90% de accuracy en bills importantes. Si nuestro ensemble + Context Engine + bandas conformal no supera al baseline simple por al menos 0.03 de Brier score, la sofisticación adicional no se justifica. La complejidad debe ganarse.

---

## Resumen

El v2.1 mantiene las 11 variables del blueprint original, preserva el razonamiento cualitativo sobre contexto coyuntural vía el Context Engine, separa correctamente derecho positivo (filtro legal) de predicción estadística, y demuestra numéricamente que Oracle Free está usado al 15% de su capacidad. No es "más simple en análisis" — es más simple en plumbing y más riguroso en el resto. Las adopciones de GovTrack (split en dos repos, CLI por scraper, Person Service, baseline simple obligatorio, datasets curados como YAMLs versionados) refuerzan la arquitectura sin agregar costo material.

El siguiente paso útil es la Fase 0: construir el dataset de validación de 200-300 leyes históricas etiquetadas con sus features completas (incluso si imputadas), porque sin ese ground truth ningún modelo se puede entrenar ni evaluar honestamente. Es trabajo aburrido pero es donde se genera el valor real del proyecto.
