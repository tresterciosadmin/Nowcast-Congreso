# Nowcast-Congreso — Viabilidad técnica, atractivo y plan de implementación

> Estudio inicial. Sistema B2B que estima la **probabilidad de que un proyecto de ley sea aprobado** por el Congreso argentino, agregando la **probabilidad individual de voto de cada legislador** en función de los atributos del proyecto. Arranque local (Python + notebooks), proyección a nube.
> Fecha: 25-jun-2026. Acompaña al premortem (`premortem-report-20260625.html`).

---

## 1. Qué es el proyecto (definición operativa)

Predecir P(aprobación) de un proyecto = combinar, por cámara, las probabilidades individuales `P(voto_i = afirmativo | atributos del proyecto, atributos del legislador i)` y agregarlas según el quórum y la mayoría requerida (simple, absoluta, 2/3).

Tres componentes:
1. **Modelo de voto individual** — clasificador de `{afirmativo, negativo, abstención/ausente}` por legislador.
2. **Agregador institucional** — convierte votos individuales en resultado (con reglas de quórum y mayorías).
3. **Capa de embudo** — antes de llegar al recinto, un proyecto debe sobrevivir comisión y obtener dictamen. Modelar esto es lo que distingue un *nowcast real* de un ejercicio académico.

---

## 2. Disponibilidad de datos (lo verificado)

**Fuentes oficiales (idealmente la base):**
- **Datos Abiertos Diputados (CKAN)** — `datos.hcdn.gob.ar`: datasets de *votaciones nominales* (desde período 129), *expedientes*, *proyectos parlamentarios*, *legisladores*, *sesiones*. Formato CSV/JSON vía API CKAN. Es la fuente más rica y mantenida.
- **Datos Abiertos Senado** — `senado.gob.ar/micrositios/DatosAbiertos/`: votaciones y labor parlamentaria. Menos estructurado que Diputados.
- **votaciones.hcdn.gob.ar** — consulta de votaciones nominales por diputado/ley (dominio público).

**Agregadores / comunidad (útiles para prototipar y cruzar):**
- **argentinadatos.com** — API pública que expone votaciones de ambas cámaras.
- **comovoto.dev.ar** — alineamiento y presentismo por legislador (investigador CONICET).
- **datacp.ar** — composición actual y datasets descargables (CSV/Excel/GeoJSON).
- **github.com/nahuelhds/votaciones-ar-datasets** — datasets normalizados Diputados (1993–2019) y Senado (2010–2019). **Atención: desactualizado (corte 2019); sirve de referencia de esquema, no como fuente viva.**

**Veredicto de datos:** hay materia prima oficial y viva, suficiente para un MVP serio. Pero con tres salvedades que definen el proyecto (ver §6):
- El **texto** de los proyectos suele ser PDF/no estructurado → requiere NLP/parsing.
- **No hay ID estable** que cruce limpio Diputados↔Senado↔proyecto↔legislador → entity resolution es trabajo real.
- Las votaciones son **ex-post**; el universo de proyectos que *no* se votan no tiene label → sesgo de selección.

---

## 3. Metodología (estado del arte aplicable)

- **Ideal point models (NOMINATE / W-NOMINATE):** ubican legisladores y proyectos en un espacio ideológico latente a partir del historial de votos. Base estándar en ciencia política.
- **Text-based ideal points (Gerrish & Blei, ICML 2011):** infieren la posición del proyecto desde su *texto* y predicen el voto; mejoran ~4% sobre baseline ingenuo. Clave acá porque permite predecir leyes *nuevas* sin historial de votación.
- **Clasificadores ML supervisados** (logística regularizada, gradient boosting) sobre features de legislador (bloque, provincia, historial, presentismo) × features de proyecto (tema, autor, cámara de origen, tipo de mayoría).
- **Enfoques recientes con LLM** ("Political Actor Agent", 2024): simulan legisladores para predecir roll-calls; interesante a futuro, costoso y difícil de auditar hoy.

**Recomendación de arranque:** baseline jerárquico (efecto bloque + efecto legislador) + regresión logística con features de proyecto, comparado **siempre** contra la heurística "votá con tu bloque". Sofisticar (ideal points con texto) solo si supera el baseline en los **votos cruzados**.

---

## 4. Viabilidad técnica — veredicto

**Viable como producto analítico; frágil como "predictor de aprobación" puro.**

| Dimensión | Evaluación |
|---|---|
| Datos disponibles | Alta para Diputados; media para Senado |
| Esfuerzo de ingestión/limpieza | **Alto** (es el verdadero costo del MVP) |
| Modelado del voto individual | Media — accesible, pero el baseline de bloque es muy fuerte |
| Modelado del embudo (comisión→recinto) | **Alto** — es donde está el valor y la dificultad |
| Estabilidad temporal | Baja — drift por recambios y rupturas de bloque |
| Stack local (Python + notebooks) | Trivial de montar |
| Proyección a nube | Estándar, sin obstáculos técnicos |

El riesgo no es técnico-de-infra; es **de señal y de encuadre de producto**. Ver premortem.

---

## 5. Atractivo (mercado B2B)

**Demanda real y compradores identificados:** consultoras de asuntos públicos y monitoreo legislativo ya operan y cobran — EGES, Synopsis, Arena Pública, Infomedia, Directorio Legislativo. Hoy venden **monitoreo cualitativo + juicio experto + contactos**, con reportes semanales.

**El hueco (diferencial posible):** ninguna ofrece una capa **cuantitativa y probabilística reproducible** — detección temprana de qué proyectos ganan tracción, mapa de **legisladores pivote**, y escenarios de resultado. El atractivo no es "reemplazar al analista" sino **darle al analista (o a su cliente) una herramienta de tablero** que prioriza dónde mirar.

**Posicionamiento sugerido:** *augmentation*, no *oracle*. Vender "radar + priorización + explicabilidad", no "la bola de cristal". Esto neutraliza la desconfianza a la caja negra y el riesgo reputacional.

---

## 6. Las tres decisiones que definen el éxito (del premortem)

1. **Encuadre de valor:** vender **detección temprana + pivotes**, no "P(aprobación)" a secas. El número de probabilidad es un feature, no el producto.
2. **Sesgo de selección:** modelar el **embudo completo** (presentado→comisión→dictamen→recinto). El label "no tratado" es información, no ausencia.
3. **Piso a superar:** la **heurística de bloque** es el benchmark obligatorio. Si el ML no le gana en votos cruzados, no hay producto — solo un dashboard lindo.

---

## 7. Arquitectura: local → nube

**Fase local (notebooks):**
```
[CKAN HCDN / Senado / argentinadatos]
        │  (requests + ckanapi)
        ▼
   ingesta cruda (CSV/JSON en /data/raw)
        │
        ▼
   limpieza + entity resolution (pandas)   → /data/clean (parquet)
        │
        ▼
   feature store local (legislador × proyecto)
        │
        ├── baseline heurístico (bloque)
        └── modelo ML (scikit-learn) + agregador institucional
        │
        ▼
   evaluación (backtesting, métrica en votos cruzados)
        │
        ▼
   notebook-dashboard (matplotlib/plotly) — uso interno
```

**Fase nube (cuando haya pagador validado):**
```
Ingesta programada (cron/Cloud Scheduler) → Storage (S3/GCS)
   → ETL (dbt o scripts) → DB (Postgres)
   → entrenamiento batch (job) → registro de modelo
   → API (FastAPI) → frontend/dashboard (Streamlit→React)
   → auth + multi-tenant + logs/monitoreo de drift
```
Sin obstáculos técnicos; es ingeniería estándar. La decisión de migrar es **comercial**, no técnica.

---

## 8. Plan de trabajo por fases

**Fase 0 — Validación de datos y baseline (1–2 semanas)**
- Descargar votaciones nominales de Diputados (CKAN) y construir el dataset legislador×votación.
- Medir el accuracy de la heurística de bloque. **Gate:** si >90%, redefinir el producto hacia votos cruzados/pivotes antes de seguir.
- Cuantificar el % de proyectos que llegan a votación (tamaño del sesgo de selección).

**Fase 1 — Modelo de voto individual (2–3 semanas)**
- Features de legislador + features de proyecto (tema, autor, cámara, mayoría requerida).
- Clasificador supervisado vs. baseline; foco en el subconjunto de votos cruzados.
- Agregador institucional con reglas de quórum/mayoría.

**Fase 2 — Capa de embudo y nowcast (2–4 semanas)**
- Modelar supervivencia en comisión / probabilidad de dictamen / probabilidad de tratamiento.
- Componer: P(aprobación) = P(llega al recinto) × P(mayoría | recinto).
- Backtesting temporal (entrenar con período t, validar en t+1).

**Fase 3 — Producto interno + validación comercial (en paralelo)**
- Dashboard local; 3–5 entrevistas con consultoras; buscar 1 LOI / piloto pago.
- **Gate de nube:** no migrar sin un pagador comprometido.

**Fase 4 — Nube (post-validación)**
- Ingesta programada, API, dashboard multiusuario, monitoreo de drift, términos de uso/disclaimer.

---

## 9. Primeros pasos concretos (esta semana)

1. Crear estructura de repo: `data/{raw,clean}`, `notebooks/`, `src/`, `requirements.txt`.
2. Notebook `01_ingesta.ipynb`: bajar `votaciones_nominales` de CKAN HCDN y `legisladores`; guardar en parquet.
3. Notebook `02_baseline_bloque.ipynb`: armar legislador×votación y medir el accuracy de "votá con tu bloque" → **este número decide el rumbo del producto**.
4. Cuantificar sesgo de selección: proyectos presentados vs. proyectos con votación nominal.
5. Revisar el premortem y completar el checklist pre-lanzamiento.

---

## Fuentes

- [Datos Abiertos Diputados (CKAN)](https://datos.hcdn.gob.ar/)
- [Votaciones Nominales — CKAN HCDN](https://datos.hcdn.gob.ar/dataset/votaciones_nominales)
- [Proyectos Parlamentarios — CKAN HCDN](https://datos.hcdn.gob.ar/dataset/proyectos-parlamentarios)
- [Consulta de Votaciones HCDN](https://votaciones.hcdn.gob.ar/)
- [Datos Abiertos Senado](https://www.senado.gob.ar/micrositios/DatosAbiertos/)
- [argentinadatos.com — API pública](https://argentinadatos.com/)
- [Data CP — datos electorales abiertos](https://www.datacp.ar/)
- [nahuelhds/votaciones-ar-datasets (GitHub, corte 2019)](https://github.com/nahuelhds/votaciones-ar-datasets)
- [Gerrish & Blei, "Predicting Legislative Roll Calls from Text" (ICML 2011)](https://icml.cc/2011/papers/333_icmlpaper.pdf)
- [Political Actor Agent — roll-call prediction con LLM (arXiv 2024)](https://arxiv.org/html/2412.07144v2)
- [EGES — consultora asuntos públicos](https://eges.com.ar/)
- [Synopsis — panorama legislativo](https://synopsis.com.ar/)
- [Directorio Legislativo — monitoreo parlamentario](https://directoriolegislativo.org/)
