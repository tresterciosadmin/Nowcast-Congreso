# Fase 3.5 — Backtesting Histórico (2015 - 2026)
**Posición:** entre Fase 3 (modelo predictivo) y Fase 4 (cascada NLP).
**Duración:** 4 semanas dedicadas.
**Objetivo triple:** calibrar Factor μ real, detectar modos de fallo pre-lanzamiento, generar baseline público de credibilidad.

---

## 1. Por qué arrancar en 2015

- HCDN datos abiertos publica estructurado desde ~2015-2016.
- Cubre 4 regímenes políticos: tail de CFK, Macri completo (2015-2019), Alberto Fernández (2019-2023), Milei (2023+).
- ~10 años × ~100 leyes sancionadas/año = ~1.000 sanciones + ~5.000-10.000 proyectos rechazados o abandonados = volumen estadísticamente útil para entrenamiento y validación.
- Data quality degrada hacia atrás (ver tabla abajo) pero el grueso aprovechable es 2017+.

| Período | Cobertura esperada | Uso |
|---|---|---|
| 2015-2016 | 60-70% | Calentamiento del modelo, no validación |
| 2017-2020 | 80-85% | Train + walk-forward inicial |
| 2021-2023 | 90-95% | Train + walk-forward principal |
| 2024-2025 | 95-100% | Holdout final + calibración OOS |

---

## 2. Sub-fases

### 3.5.A — Backfill estructurado (Semana 1)

**Trabajo:**
- Pull completo de HCDN datos abiertos CSV/JSON 2015-2026 (más estable que REST para histórico)
- Senado: scraping del archivo histórico con políticas de stealth, delays aleatorios y respeto a robots.txt
- Ingestión de ATN históricos del Tesoro (BORA + dataset secundario MECON)
- ICG Di Tella: serie completa desde 2015 (publicada con delay, pero el histórico ya está consolidado)
- Composición histórica de comisiones por período legislativo

**Verificación cruzada obligatoria:**
- Lista pública de leyes sancionadas (Honorable Senado + InfoLeg) usada como ground truth para sanciones
- OPC reports para verificar costo fiscal y categoría temática cuando esté disponible

**Métrica de pase:** ≥90% de leyes sancionadas conocidas presentes en el dataset con metadata completa (firmantes, comisión, fechas, texto).

### 3.5.B — Reconstrucción point-in-time de features (Semana 2)

**El paso más delicado. Cero leakage es no-negociable** (la falla #3 del premortem fue exactamente este punto).

Para CADA proyecto histórico, reconstruir features tal como existirían a la fecha del dictamen, NO la fecha actual:

| Feature | Reconstrucción point-in-time |
|---|---|
| ICG Di Tella | Valor publicado en t-1 mes (no el revisado posteriormente) |
| ATN per cápita | Agregado mensual publicado hasta t-1 |
| PageRank cofirmantes | Grafo construido SOLO con cofirmas registradas ≤ fecha_dictamen |
| Composición comisión | Padrón vigente en t (Wikipedia + HCDN tienen histórico de composiciones) |
| Track record sponsor | Solo proyectos suyos con outcome conocido antes de t |
| Polarización UMAP | Ajustar UMAP sobre votos ≤ t, EXCLUYENDO el voto del proyecto que estamos prediciendo |
| Context shift | Wayback Machine + GDELT para archivo de prensa de la época; si no disponible, imputar con score neutral 0 + flag `context_unavailable=True` |
| Días a próxima elección | Calculado al momento, no en retrospectiva |
| Composición de bloques | Snapshot de bloques activos en t (con cambios de bloque registrados) |

**Test de no-leakage automatizado:** función `test_no_leakage()` que para cada feature reconstruida verifica que su valor NO cambia si se re-ejecuta el cómputo agregando datos posteriores a t. Si cambia, hay leakage y la feature debe rediseñarse.

**Output:** tabla `features_pit` con ~50.000 filas (1 por proyecto × snapshot temporal).

### 3.5.C — Walk-forward validation (Semana 3)

**Protocolo:**

```
Estado inicial: entrenar modelo con datos 2015-2016 (período de calentamiento, sin validación)

Loop mensual desde 2017-01-01 hasta 2025-12-31:
    1. Reentrenar modelo con todos los datos disponibles hasta t
    2. Para cada proyecto en estado activo en t (en comisión, con dictamen pendiente, etc.):
        - Calcular features point-in-time a fecha t
        - Predecir P(sanción dentro de N días) y banda de confianza
        - Registrar en historical_predictions
    3. Avanzar t += 1 mes
```

**Output:** tabla `historical_predictions` con ~10.000-15.000 predicciones simuladas, cada una con:
- `(project_id, prediction_date, predicted_prob, predicted_band_low, predicted_band_high, actual_outcome, outcome_date, model_version, features_snapshot_hash, regime_label)`

**Métricas calculadas y persistidas:**
- Brier rolling 3, 6, 12 meses
- ECE rolling
- AUC-ROC y AUC-PR
- Coverage empírica de intervalos vs. nominal
- Performance separada por:
  - 4 regímenes políticos (CFK-tail, Macri, AF, Milei)
  - Cámara de origen (Diputados vs. Senado)
  - Estado del proyecto al momento de predicción (en_comisión, con_dictamen, media_sanción)
  - Temática (cuando el bucket tenga n ≥ 30)
  - Tipo de proyecto (ley común, ley orgánica, declarativa, resolución)

**Visualización obligatoria:**
- Time series de Brier mes a mes con líneas verticales en cambios de gobierno
- Reliability diagram global y por régimen
- Distribución de errores por percentil de probabilidad predicha

### 3.5.D — Catálogo de modos de fallo (Semana 4, parte 1)

Análisis cualitativo sistemático de los errores del walk-forward:

**Procedimiento:**
1. Aislar Top 50 false positives (predicción > 0.75, sanción no ocurrió)
2. Aislar Top 50 false negatives (predicción < 0.25, sanción ocurrió)
3. Aislar Top 20 mayores errores absolutos
4. Clustering automático sobre features de los proyectos errados
5. Inspección manual de cada cluster con 2-3 ejemplos canónicos
6. Naming + documentación + contramedida propuesta

**Catálogo esperado (5-10 modos de fallo nombrados):**

Ejemplos de modos de fallo que el catálogo probablemente capturará:

| Modo | Descripción | Contramedida |
|---|---|---|
| **Régimen-shift errors** | Predicciones fallan en los 3 meses post-cambio de gobierno cuando alianzas se reconfiguran | Feature `days_since_government_change` + ampliación automática de banda μ |
| **Media-storm cases** | Proyectos que tomaron escala mediática súbita y se sancionaron contra el modelo | Context Engine debe captar; revisar peso del context_shift |
| **Bicameral asymmetry** | Predicciones mejores en Diputados que Senado (o viceversa) | Modelo jerárquico por cámara (Parte 2.2 del análisis de mejoras) |
| **Decree-conversion** | DNUs que se sancionan/rechazan con dinámica distinta a leyes ordinarias | Sub-modelo dedicado a DNUs |
| **Coalition swing** | Cambio mid-process de posición de un bloque no anticipado | Feature de "estabilidad de bloque" + monitoring de declaraciones |
| **Quorum failures** | Predijo sanción pero el recinto no llegó a quorum | Feature de "concurrencia esperada" basada en sesiones recientes |
| **Late-session crunch** | Sanciones masivas en últimas semanas que el modelo subestima | Feature `position_in_cycle` con interacción cuadrática |
| **Omnibus bills** | Proyectos ómnibus tratados como uno solo cuando deberían descomponerse | Detector + splitter pre-feature engineering |
| **Pliego logic** | Pliegos del PEN tratados como leyes cuando tienen lógica distinta | Sub-modelo dedicado a pliegos |
| **OOD outliers** | Proyectos con features muy alejadas del manifold de entrenamiento | OOD detector + flag de "predicción no confiable" |

Cada modo del catálogo entra al backlog técnico con prioridad asignada por frecuencia × magnitud del error.

### 3.5.E — Calibración honesta de Factor μ (Semana 4, parte 2)

Usando exclusivamente residuals del walk-forward (no datos retroactivos imputados):

**Procedimiento:**
1. Para cada predicción del walk-forward, calcular residual = (outcome_real - predicted_prob)
2. Agrupar residuals por percentil de probabilidad predicha (10 buckets: 0-10%, 10-20%, ..., 90-100%)
3. Bootstrap (1.000 iteraciones) sobre residuals de cada bucket → bandas de confianza percentiles 5/50/95
4. Beta calibration ajustada sobre toda la curva (mejor que Platt en colas)
5. Conformal prediction calibrado sobre holdout 2025 (que NO entró en walk-forward training)

**Factor μ resultante:**
- NO desagregado por temática (insuficiente n)
- Banda global garantizada por conformal prediction con cobertura nominal verificable
- Modificadores que amplifican banda para:
  - Proyectos con OOD score alto (features fuera del manifold)
  - Proyectos con context_shift score significativo (alta volatilidad coyuntural)
  - Predicciones en períodos post-cambio-de-gobierno (régimen-shift documentado)
  - Predicciones con discordancia alta entre modelos del ensemble (|logistic - lgbm| > 0.3)

**Output publicable:** `mu_calibration_curve` table + reliability diagram + documentación de cobertura empírica histórica.

### 3.5.F — Gate de paso a Fase 4

Criterios obligatorios (todos deben pasar):

| Criterio | Umbral |
|---|---|
| Cobertura del dataset histórico vs fuentes secundarias | ≥ 90% |
| Test de no-leakage automatizado | 100% pass |
| Brier walk-forward < baseline ("siempre frecuencia base") | ≥ 60% de los meses |
| ECE global | < 0.05 |
| Cobertura empírica de banda 90% | en [0.87, 0.93] |
| Catálogo de modos de fallo | ≥ 5 modos documentados con contramedida asignada |
| Reproducibilidad | `make backtest YEAR=2024 MONTH=06` regenera bit-idénticas predicciones |
| Performance no degrada catastróficamente entre regímenes | gap de Brier entre régimen peor y mejor < 0.10 |

Si cualquier criterio falla: NO avanzar a Fase 4. Iterar features y/o modelo. Es preferible retrasar el lanzamiento que lanzar con calibración fake.

---

## 3. Outputs persistentes (viven en producción)

Tablas en Postgres generadas durante esta fase y consultadas por el sistema vivo:

1. **`historical_predictions`** — ~10.000-15.000 predicciones simuladas (backtest completo)
2. **`features_pit`** — features point-in-time reconstruidas para cada proyecto histórico
3. **`failure_modes_catalog`** — modos de fallo nombrados, descriptos, con contramedidas
4. **`mu_calibration_curve`** — bandas de confianza por percentil de predicción
5. **`regime_performance`** — métricas separadas por régimen político
6. **`feature_importance_walkforward`** — evolución de importancia de cada feature en el tiempo

Estos outputs alimentan tres flujos en producción:

a) **Methodology page pública** — publicar Brier histórico, reliability diagram, performance por régimen. Credibilidad inmediata.

b) **Drift detection live** — comparar performance de las primeras N semanas live contra la distribución esperada según walk-forward. Si la live performance está fuera del rango bootstrap, alerta.

c) **Sanity check predictivo** — antes de publicar una predicción live, calcular qué predeciría el backtest con features similares. Si discrepa >0.2, marcar como "alta incertidumbre" y narrator lo explicita.

---

## 4. Beneficios concretos para el lanzamiento

1. **Factor μ con n ≥ 1.000 predicciones** en vez de cold start con n < 20 de las primeras semanas live. El premortem identificó esto como el principal teatro estadístico del proyecto.
2. **Calibración OOS rigurosa**: el primer reporte público ya tiene bandas honestas, no inventadas.
3. **Catálogo de fallos pre-conocidos**: ningún usuario va a descubrir un modo de fallo nuevo si ya están catalogados internamente y documentados en la methodology page.
4. **Credibilidad inmediata** ante consultoras y prensa: "Brier histórico 0.18 sobre 8 años y 4 regímenes políticos, reliability diagram público" es radicalmente distinto a "confíen, está calibrado".
5. **Performance esperada documentada por régimen**: si el gobierno actual cae y entra otro, sabés exactamente cuánto degradación esperar mientras el modelo se readjusta. Permite gestionar expectativas honestamente.
6. **Priorización del backlog técnico**: las mejoras del feature engine (Parte 2.1 del análisis de resiliencia) se priorizan según qué modos de fallo del catálogo cubren cada una. Decisiones basadas en evidencia, no en intuición.

---

## 5. Costos adicionales

- **Tiempo de desarrollo:** 4 semanas → roadmap pasa de 16-18 a 20-22 semanas
- **API costs:** ~$30-50 one-time si necesita reclasificar históricos sin etiqueta usando Haiku
- **Compute:** walk-forward = 8 años × ~200 proyectos activos/mes × ensemble train ≈ 16.000 reentrenamientos. Con LightGBM en ARM, ~6-8 horas totales. Distribuido en 3-4 noches usando CPU desocupado de Oracle Free. **Sin costo.**
- **Storage:** ~500 MB adicionales en Postgres (historical_predictions + features_pit). Trivial vs 200GB block storage gratis.

---

## 6. Lo que esta fase NO hace

- **No reemplaza el shadow mode de 4 semanas pre-launch.** Backtesting valida sobre el pasado; shadow mode valida sobre el futuro con sistema completo corriendo. Ambos son necesarios.
- **No garantiza ausencia de fallos en producción.** Reduce el riesgo de fallar por modos conocidos. Cisne negro sigue siendo posible (mitigado parcialmente por Context Engine + OOD detection).
- **No resuelve problemas de availability de datos históricos.** 2015-2017 va a tener data quality menor. Mitigación: ponderación inversamente proporcional a la incertidumbre de los datos en el train set.

---

## 7. Pre-launch checklist actualizado (items que esta fase agrega)

Incorporados al checklist global del documento de resiliencia:

- [ ] Backfill 2015-2026 completo con cobertura ≥ 90% vs fuentes secundarias
- [ ] Test automatizado de no-leakage pasa 100%
- [ ] Walk-forward validation ejecutado con ≥ 10.000 predicciones simuladas
- [ ] Brier walk-forward < baseline en ≥ 60% de los meses
- [ ] ECE global < 0.05
- [ ] Cobertura empírica de banda 90% en [0.87, 0.93]
- [ ] Catálogo de modos de fallo con ≥ 5 modos documentados
- [ ] Contramedidas del catálogo asignadas a fase/sprint posterior
- [ ] Methodology page con reliability diagram público lista para publicar
- [ ] Sanity check predictivo (live vs backtest) integrado al pipeline de inferencia
- [ ] Drift detection conectado a alertas
- [ ] Gap de Brier entre régimen peor y mejor < 0.10
- [ ] Reproducibilidad bit-exacta verificada
