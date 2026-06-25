# Análisis Exhaustivo de Resiliencia y Mejoras del Índice — Pre-Lanzamiento
**Fecha:** 2026-05-28
**Premisa:** identificar TODO punto único de fallo (SPOF), TODA superficie de error externa o interna, y proponer mitigaciones concretas + mejoras analíticas. Nada se lanza sin pasar por esta auditoría.

---

# PARTE 1 — RESILIENCIA: SUPERFICIES DE FALLO Y MITIGACIONES

## 1.1 Dependencias externas (cada una es un SPOF)

### A. HCDN REST API (`rest.hcdn.gob.ar`)

**Modos de fallo:**
- DNS no resuelve / TLS handshake falla
- Timeout (response_time > 30s)
- HTTP 5xx (servidor caído)
- HTTP 429 (rate limit)
- HTTP 4xx (request malformado, esquema cambió)
- Respuesta 200 con JSON inválido o esquema renombrado
- Respuesta 200 con campos faltantes
- Encoding corrupto (Latin-1 cuando esperás UTF-8)
- Datos inconsistentes entre llamadas consecutivas (race condition upstream)

**Mitigaciones obligatorias:**
- `httpx.AsyncClient` con `timeout=Timeout(connect=5, read=30, write=10, pool=5)`
- Retry con exponential backoff via `tenacity`: 5 intentos, base 2s, jitter aleatorio ±25%, máximo 60s
- Circuit breaker: si 3 fallos consecutivos en 5 min, abrir circuito por 15 min y servir desde caché
- Validación con Pydantic en cada response: si no valida, log estructurado con `response_body[:500]` + `request_url` + `headers` y caer al fallback
- Schema versionado en código: `HCDNProjectV2024 -> HCDNProjectV2025` con migración explícita si HCDN cambia
- Idempotencia: cada proyecto tiene `expediente_id` como clave única; reingestas son seguras
- Hash de respuesta: si dos llamadas consecutivas devuelven datos contradictorios sobre el mismo expediente en <60s, log warning y reintentar tras 5 min

**Patrón de código:**
```python
@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=2, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def fetch_proyecto(exp_id: str) -> ProyectoDTO:
    async with httpx.AsyncClient(timeout=Timeout(30)) as client:
        resp = await client.get(f"{HCDN_BASE}/proyectos/{exp_id}")
        resp.raise_for_status()
        try:
            return ProyectoDTO.model_validate(resp.json())
        except ValidationError as e:
            logger.error(
                "hcdn_schema_violation",
                exp_id=exp_id,
                errors=e.errors(),
                body_preview=resp.text[:500],
            )
            raise UpstreamSchemaError(exp_id) from e
```

### B. HCDN datos abiertos (`datos.hcdn.gob.ar`)

**Modos de fallo:**
- URL del CSV rota (typical pattern: `?d=2024-Q1` → archivo renombrado)
- CSV con columnas renombradas o reordenadas
- CSV con filas malformadas, comas dentro de campos sin escape
- Encoding mixto

**Mitigaciones:**
- Lectura con `pandas.read_csv(..., on_bad_lines='warn', dtype=str, keep_default_na=False)` (sin NA implícitos, todo string, parsing explícito downstream)
- Validación de columnas esperadas vs columnas recibidas → si difieren, alerta y NO ingerir (mejor parar que persistir basura)
- Checksum SHA-256 del archivo descargado: si cambia el checksum entre descargas del mismo período, log
- Snapshot del CSV crudo guardado en Backblaze antes de procesar (para reprocesamiento histórico)

### C. Senado (HTML scraping)

**Modos de fallo:**
- WAF / Cloudflare challenge (JS, captcha)
- IP banning tras N requests
- Selectores XPath/CSS rotos por rediseño
- Contenido JS-rendered no presente en HTML inicial
- Sesiones con cookies que expiran

**Mitigaciones:**
- Playwright con `stealth-mode` (fingerprint humano)
- User-Agent rotativo desde lista realista
- Delays aleatorios entre requests (2-7 segundos)
- Respeto absoluto a `robots.txt` (auditoría legal)
- Detección de challenge page: si HTML contiene `cf-challenge`, abortar y notificar
- Selectores con múltiples fallbacks: `[data-bill-id]` → `.bill-id` → `XPath:.//div[contains(@class,"id")]`
- Snapshot HTML guardado en caché 24h: ante caída del Senado, servís desde caché
- Política de fallback: si Senado cae >24h, alerta manual y suspender features que dependen de él (la predicción degrada pero no muere)

### D. BORA — Boletín Oficial

**Modos de fallo:**
- Resoluciones publicadas como PDF nativo, PDF escaneado, o mixto
- Búsqueda con UX inconsistente
- Tablas como imágenes embebidas (especialmente ATN)

**Mitigaciones:**
- Pipeline en tres pasos:
  1. Intentar `pdfplumber` para texto nativo
  2. Si falla o texto < umbral, `tesseract` con lang `spa` y `psm 6`
  3. Si OCR confidence < 70%, encolar para revisión manual
- Cola manual con UI mínima (HTMX form + Postgres queue): te lleva 10 min/semana
- Cache permanente: cada PDF parseado se guarda con `(url, sha256, extracted_text)` para nunca reprocesar
- Logger estructurado con razón de fallo para cada PDF que va a manual

### E. Di Tella ICG

**Modos de fallo:**
- Publicación mensual con delay variable (30-60 días)
- Formato del informe cambia (PDF, XLSX, web embed)
- Meses faltantes

**Mitigaciones:**
- Feature `icg_freshness_days` que reporta días desde la última publicación
- Imputación explícita cuando hay gaps: interpolación lineal entre observaciones disponibles, marcada con flag `icg_imputed=True`
- Alerta si ICG no publicado por >75 días (anomalía estructural)

### F. Tesoro Nacional ATN

**Modos de fallo:**
- Resoluciones mensuales en BORA con tablas como imagen
- Formato cambia cada gestión política

**Mitigaciones:**
- OCR + parser tolerante por provincia (lista de 24 provincias + CABA es enumerable)
- Validación de suma: total ATN del mes debe coincidir entre fuentes secundarias (presupuesto MECON)
- Si discrepancia >5%, no ingestar y alertar

### G. Claude API (Anthropic)

**Modos de fallo:**
- 429 rate limit (incluyendo TPM, RPM, ITPM caps)
- 5xx temporary service degradation
- Network timeout
- 401/403 (API key expirado o suspendido)
- Quota exhaustion (presupuesto mensual)
- Modelo deprecado mid-run
- Prompt cache invalidado por cambio leve en system prompt

**Mitigaciones:**
- Retry con backoff exponencial respetando `retry-after` header
- Budget guard: tabla `api_spend` actualizada cada llamada; si spend mensual > umbral configurado, abortar y fallback a Haiku/skip
- Cache de prompts versionado: `system_prompt_hash` en cada request, mismo hash = mismo cache key
- Fallback model: si Sonnet falla 3 veces, intentar Haiku; si Haiku también falla, narrator genera reporte con plantilla determinística desde features
- Detección de modelo deprecado: si response trae warning, log + alerta + congelar fecha de migración
- Idempotencia: cada llamada LLM tiene un `request_id` único; el sistema nunca repite la misma llamada lógica el mismo día (cache por `request_id`)

### H. Ollama / Hermes local

**Modos de fallo:**
- OOM en ARM (modelo + contexto > RAM disponible)
- Crash del proceso ollama
- GGUF file corrupto
- Inferencia cuelga indefinidamente
- Download del modelo falla

**Mitigaciones:**
- Container con `mem_limit: 8g` y `oom_kill_disable: false` (que se muera limpio, no que cuelgue el host)
- Healthcheck cada 60s que pingea `/api/tags`
- Reintentar 3 veces, luego marcar nodo `unhealthy` y skip Context Engine nocturno por ese día
- Validación SHA-256 del GGUF al inicio
- Timeout de inferencia hardware: 180s; si excede, abort y log
- Política de degradación: si Hermes cae >48h, Context Engine usa solo Sonnet con eventos crudos (más caro: ~$3/sem extra) en vez de skipping

### I. PostgreSQL

**Modos de fallo:**
- Connection pool exhaustion bajo carga concurrente
- Deadlock entre escrituras simultáneas
- Disk full por logs WAL o tablas crecientes
- Índices degradados (autovacuum atrasado)
- Corrupción por OOM previo

**Mitigaciones:**
- Pool de conexiones con `asyncpg` o `psycopg-pool`: `min_size=2, max_size=10` (4 OCPU no necesitan más)
- Timeout en cada query: `statement_timeout=30s` global, `idle_in_transaction_session_timeout=60s`
- Transacciones con `SELECT FOR UPDATE SKIP LOCKED` para colas
- Monitoreo de disk usage: alerta a 70%, panic a 85%
- Autovacuum tuneado: `autovacuum_naptime=30s` (más frecuente que default 60s)
- Backup diario via `pg_dump --format=custom --compress=6` → Backblaze
- Test de restore mensual con script automatizado: si el restore falla, el monitor está mintiendo
- PITR opcional con `wal-g` si crece la criticidad

### J. Oracle Cloud instance

**Modos de fallo:**
- Reclamación por CPU <20% por 7 días
- Hardware failure (raro pero existe)
- Mantenimiento programado de Oracle
- Network outage del datacenter
- API de OCI rate-limiting si abusás de operaciones

**Mitigaciones:**
- Heartbeat cron cada 30 min: `stress-ng --cpu 2 --timeout 60s` (mantiene 95th percentile > umbral)
- Monitoreo independiente con `oci-cli` ping a la instancia (alerta si no responde)
- Standby caliente en Hetzner CX22 ($4.59/mes) sincronizado nightly via `pg_dump | restic backup`
- DNS con TTL bajo (60s) en Cloudflare DNS gratis para switch rápido
- Runbook de migración a Hetzner: <30 min de RTO si Oracle cae

### K. Backblaze B2 backups

**Modos de fallo:**
- Quota exceeded (10GB free)
- Auth token expirado
- Upload corrupto (rare con B2 pero pasa)
- Backblaze caído

**Mitigaciones:**
- Retención: solo últimos 7 daily + 4 weekly + 6 monthly (cabe en 10GB con compresión)
- Backup secundario gratis: Cloudflare R2 (10GB free, 0 egress) como tercer destino
- Verificación post-upload: descargar SHA-256 del archivo y comparar
- Alert si backup falla 2 días seguidos

### L. Fuentes de prensa para Context Engine

**Modos de fallo:**
- Paywalls
- Bot detection
- Layout changes
- Información falsa / duplicados

**Mitigaciones:**
- Whitelist de fuentes: La Nación, Página/12, Clarín, Infobae, Ámbito, LPO (mix ideológico)
- RSS donde esté disponible (más estable que HTML scraping)
- Deduplicación por similitud de embedding (>0.92 cosine = duplicado)
- Score de confiabilidad por fuente: agregación de eventos requiere >=2 fuentes para alto peso
- Detección de paywall: si HTML contiene marker característico, skip
- Política de no-scrape en paywalls duros (legal/ético)

### M. UptimeRobot / monitoreo externo

**Modos de fallo:**
- Falso positivo (red de monitor, no del sistema)
- Notificación falla
- UptimeRobot down

**Mitigaciones:**
- Doble monitor: UptimeRobot + Healthchecks.io (ambos gratis)
- Heartbeat outbound: el sistema pingea a Healthchecks.io cada 5 min; si Healthchecks no recibe ping en 15 min, alerta
- Alertas por dos canales: Telegram bot + email (uno suele fallar)

---

## 1.2 Componentes internos

### N. Embeddings model

**Modos de fallo:**
- Archivo del modelo corrupto
- Versión drift entre training y serving (modelo distinto al usado para entrenar)
- Memory leak en proceso de inferencia largo

**Mitigaciones:**
- Pin de versión exacta: `sentence-transformers==3.2.1`, `model_name@commit_hash`
- Hash del modelo cargado loggeado al inicio
- Worker con reciclado periódico: cada 4h, mata y reinicia proceso de embeddings para evitar leaks
- Test smoke al startup: embed de una frase canónica, comparar contra vector esperado (tolerancia 1e-4)

### O. Feature engine

**Modos de fallo:**
- División por cero (ej. comisión sin miembros activos)
- NaN propagation (un feature NaN contamina la predicción)
- Type mismatches entre data y model expectations
- Cold start: features que requieren N observaciones históricas
- Drift de distribución (features que cambian de rango sin que nadie note)

**Mitigaciones:**
- Cada función feature retorna `FeatureResult(value, confidence, status)`:
  - `status = "ok"` → usar
  - `status = "imputed"` → usar con flag
  - `status = "missing"` → modelo recibe imputación + indicator variable
  - `status = "error"` → no predecir, devolver "insufficient_data"
- Validación de rango: cada feature tiene rango esperado declarado; valor fuera de rango → log + clamp
- Schema de features con Pydantic: si el modelo recibe shape incorrecto, falla loud, no silent
- Monitor de distribución: percentiles 5/50/95 de cada feature registrados diariamente; alerta si shift >2σ vs baseline
- Cold start policy: hasta tener N=30 observaciones para un feature, el modelo NO lo usa (peso 0 forzado)

### P. Ensemble model

**Modos de fallo:**
- Train/serve skew (preprocessing diferente entre training y inference)
- Feature drift (input data shift)
- Concept drift (relación features→outcome cambia)
- Modelos en desacuerdo extremo (logística dice 0.9, LightGBM dice 0.1)

**Mitigaciones:**
- Pipeline serializado: `sklearn.Pipeline` con preprocessing + model en un solo `joblib.dump`. Mismo objeto en train y serve.
- Logging de cada predicción con (features_hash, model_version, prediction, probability, individual_model_outputs)
- Test de skew en CI: 10 ejemplos canónicos, comparar predicción local vs producción (debe ser bit-exacto)
- Drift monitor: Brier score rolling 30 días; si degrada >0.05 vs baseline histórico, alerta
- Discordancia de ensemble: si |logistic_p - lgbm_p| > 0.3, marcar predicción como `low_confidence` y narrator lo refleja explícitamente
- Champion-challenger: nuevo modelo corre en shadow mode 4 semanas antes de promoverse

### Q. Canonical Legislator Resolver

**Modos de fallo:**
- Falso positivo: dos legisladores distintos unificados
- Falso negativo: un legislador con dos identidades
- Stale mappings cuando legisladores cambian apellido (matrimonio, divorcio)

**Mitigaciones:**
- Confidence score en cada match; >0.95 auto, 0.7-0.95 cola humana, <0.7 nueva entidad
- Auditoría trimestral: report de matches dudosos para revisión
- Inmutable IDs: una vez asignado un canonical_id, jamás se reasigna; merges/splits son operaciones explícitas con audit log
- DNI como ground truth cuando esté disponible (HCDN no siempre lo expone)
- Test de regresión: dataset de 100 nombres ambiguos conocidos; cada cambio del resolver debe pasar 100/100

### R. Context Engine LLM output

**Modos de fallo:**
- Hallucinated events (Sonnet inventa una declaración)
- JSON malformado en respuesta
- Sentiment misclassification
- Context shift sobreponderado por un evento espurio

**Mitigaciones:**
- Prompt con instrucción explícita: "cada evento mencionado DEBE incluir cita textual; si no hay cita, no lo menciones"
- Validación post-LLM: cada evento estructurado debe matchear textualmente con corpus de input. Si no, descartar.
- Validación JSON con Pydantic + reintento si falla (Sonnet a veces responde con un trailing comma)
- Cap del context_shift_score en [-0.25, +0.25]: no puede dominar features estadísticos
- Multi-source corroboration: evento de alto impacto solo se aplica si aparece en ≥2 fuentes distintas
- Sanity check vs histórico: si Sonnet reporta shift >0.2 en una semana sin votación importante, log warning

### S. Narrator output

**Modos de fallo:**
- Errores factuales en la narrativa
- Citación de feature inexistente o con valor distinto al real
- Riesgo de difamación al nombrar legisladores

**Mitigaciones:**
- Prompt restringido: narrator recibe TODOS los features con sus valores numéricos y DEBE citar solo esos
- Post-procesamiento: parser regex que extrae cada afirmación cuantitativa del narrativo y verifica contra el feature numérico subyacente; si discrepa >5%, regenerar
- Política de nombramiento: solo legisladores con votación pública identificable; pronombres genéricos para análisis sin votos
- Disclaimer automático al pie del reporte: metodología, limitaciones, contacto para erratas

---

## 1.3 Operacional

### T. Deploy / rollback

**Modos de fallo:**
- Migration de DB rompe schema en producción
- Container OOM al startup
- Secret leak en logs o env
- Sin path de rollback

**Mitigaciones:**
- Migrations con `alembic`, jamás manual SQL
- Cada migration testeada en staging con copia de prod (anonimizada)
- Migration script siempre genera reverse migration; rollback es un comando
- Healthcheck post-deploy: si después de 5 min no healthy, rollback automático
- Secrets en archivo `.env` con permisos 600, nunca commiteados
- Logging filter: regex que enmascara `API_KEY|SECRET|TOKEN|PASSWORD` antes de imprimir

### U. Monitoring blind spots

**Modos de fallo:**
- Feature retorna 0 silenciosamente cuando debería errorear
- Ingestion stopped pero nadie notó
- Model drift sin alerta

**Mitigaciones:**
- Métricas obligatorias publicadas a Prometheus (gratis, single binary):
  - `ingestion_last_success_timestamp` por fuente
  - `features_computed_count` rolling 24h
  - `model_predictions_count` rolling 24h
  - `model_brier_rolling_30d`
  - `claude_api_spend_mtd`
  - `oracle_cpu_p95_7d`
- Cada métrica con alerta en Grafana (gratis self-hosted)
- "Dead man's switch": si `model_predictions_count == 0` por 24h, alerta crítica
- Smoke test sintético: cada hora, una "predicción de prueba" sobre un proyecto fijo; resultado debe ser idéntico ± tolerancia

### V. Seguridad

**Modos de fallo:**
- Secrets en variables de entorno expuestas
- Postgres expuesto a internet
- Container con privilegio root
- API endpoints sin auth

**Mitigaciones:**
- Firewall OCI: solo SSH (puerto 22 con key auth, password disabled) + HTTPS (443)
- Postgres bindeado a `127.0.0.1`, jamás a `0.0.0.0`
- Containers con `user: 1000:1000` no-root
- API protegida con Cloudflare Access (gratis hasta 50 users) o JWT
- Rotación de SSH key trimestral, API key Anthropic semestral
- `fail2ban` activo

### W. Cost runaway

**Modos de fallo:**
- Bug que llama Sonnet en bucle infinito
- Retry sin backoff genera 100x llamadas
- Embedding generation loop

**Mitigaciones:**
- Hard cap en `api_spend` por día: si excede $1, kill switch automático que pausa narrator y Context Engine
- Rate limit propio sobre Sonnet: máximo 100 calls/día, 10 calls/hora
- Métrica `cost_per_prediction` visible: si supera $0.10 por predicción, algo está mal
- Webhook de Anthropic billing (cuando esté disponible) → alerta a Telegram

### X. Data quality

**Modos de fallo:**
- Duplicados (mismo proyecto ingerido dos veces)
- Encoding mixto (UTF-8 vs Latin-1)
- Timezone confusion (Argentina UTC-3, no UTC)

**Mitigaciones:**
- `UNIQUE` constraint sobre `(camara, expediente_numero, expediente_anio)` en Postgres
- Todo string normalizado a UTF-8 NFC al ingestar
- Todo timestamp en UTC en DB, conversión a UTC-3 solo en reporte
- Validación: timestamps futuros (>30 días adelante) son inválidos por definición

### Y. Reproducibilidad

**Modos de fallo:**
- Modelo no versionado
- Dataset de train cambia silenciosamente entre runs
- Random seeds no fijos → resultados no reproducibles

**Mitigaciones:**
- DVC o Git LFS para versionar datasets
- Modelo guardado con `joblib` + metadata: `{commit_hash, train_dataset_hash, sklearn_version, python_version, timestamp}`
- Random seeds fijos: `np.random.seed(42)` + `random.seed(42)` + `torch.manual_seed(42)` al inicio
- Cada predicción persistida en DB con `model_version` referenciable

---

# PARTE 2 — MEJORAS DEL ÍNDICE (CALIDAD ANALÍTICA)

## 2.1 Features adicionales que aumentan poder predictivo

### Temporales
- **Time-since-similar-bill**: días desde el último proyecto sustancialmente similar (cosine >0.85). Bills similares muy recientes pueden indicar saturación temática.
- **Position in legislative cycle**: días desde inicio del período ordinario / extraordinario. Sanciones se concentran en últimas semanas.
- **Days-in-committee**: tiempo en comisión sin dictamen. Proyectos con >180 días suelen morir.
- **Días-hasta-fin-de-mandato del firmante principal**: legisladores salientes empujan agenda final.

### Track record
- **Sponsor success rate**: % histórico de proyectos del firmante principal sancionados.
- **Committee throughput**: tasa de sanción de la comisión asignada en último año.
- **Bicameral rebound score**: si proyecto viene del Senado, tasa histórica de aprobación en Diputados por tipo.

### Composición y dinámica
- **Committee composition stability**: rotación de miembros en últimos 90 días.
- **Cross-block sponsorship momentum**: cambio en diversidad de bloques cofirmantes semana a semana.
- **Brokerage scores (Burt structural holes)**: legisladores que conectan grupos densos. Mejor que PageRank para identificar puentes reales.

### Salience externa
- **Media coverage**: cuenta de menciones del proyecto en prensa whitelist (vía Context Engine).
- **Public opinion proxy**: Google Trends del tema asociado, normalizado por baseline mensual.
- **Stakeholder pressure**: declaraciones de CGT, UIA, sociedades rurales, IDEA, etc., agrupadas por posición.

### Económicas y institucionales
- **Costo fiscal estimado**: si OPC (Oficina de Presupuesto) publica análisis. Proyectos con costo alto tienen rechazo mayor en regímenes de ajuste.
- **Riesgo de inconstitucionalidad declarado**: si dictamen tiene disidencia jurídica, banderazo de problema.
- **Necesidad de mayoría calificada**: agravante para algunos tipos de proyecto.

### Polarización ideológica
- **Polarization index sobre cofirmantes**: distancia promedio en espacio ideológico UMAP entre firmantes. Alta polarización predice rechazo.
- **Median voter position vs project ideology**: si el "votante mediano" del cuerpo está lejos del proyecto, sanción improbable.

**Total propuesto: ~25 features (vs ~11 originales).** Aumento de dimensionalidad manejable con regularización L2 + LightGBM.

---

## 2.2 Arquitectura del modelo: más allá del ensemble simple

### Modelos adicionales en el ensemble

**Hierarchical model por cámara**: Diputados y Senado tienen dinámicas distintas (representación territorial vs poblacional, quorum diferente, lógica de bloques distinta). Un modelo por cámara, con pooling parcial bayesiano vía PyMC para compartir información cuando hay poca muestra.

**Sequential / survival model**: en vez de predecir solo P(sanción), modelar la trayectoria como Markov chain:
```
presentado → giro_comisión → dictamen → media_sanción → segunda_cámara → sanción
```
Con probabilidad de transición entre estados. Permite responder "¿cuánto le falta?" no solo "¿pasará?". Survival analysis (Cox proportional hazards) sobre time-to-sanción es alternativa.

**Modelo de votación nominal**: además de P(sanción), predecir P(voto positivo) por legislador individual condicional al proyecto llegando al recinto. Permite chequear consistencia: si predijiste sanción pero la mayoría de los legisladores predichos votarían en contra, hay inconsistencia interna y la predicción es sospechosa.

### Calibración mejor
- **Beta calibration** en vez de Platt: mejor performance en colas (probabilidades cerca de 0 y 1, que es donde nos importa)
- **Reliability diagram público**: gráfico de probabilidad predicha vs frecuencia empírica, publicado y actualizado mensualmente. Honestidad radical.
- **Calibración por régimen**: separar calibración kirchner / macri / fernández / milei. Si el modelo está mal calibrado en un régimen, lo decís.

### Uncertainty quantification rigurosa
- **Conformal prediction**: garantía distribución-libre de cobertura. Si decís "intervalo 90%", el 90% de los casos reales caen en el intervalo. Matemáticamente garantizado, no empírico.
- **Out-of-distribution detection**: si un proyecto tiene features lejos del manifold de entrenamiento, marcar predicción como `OOD: alta_incertidumbre` y degradar narrativa a "predicción no confiable".

---

## 2.3 Evaluación rigurosa pre-lanzamiento

### Datasets disjuntos
- **Train**: 2016-2022
- **Validation**: 2023 (hyperparameter tuning, model selection)
- **Holdout 1 (calibration)**: H1 2024 (Platt/Beta calibration)
- **Holdout 2 (test final)**: H2 2024 - 2025 (NUNCA usado hasta el final, una sola medición)
- **Live**: 2026+ (production, monitoreado para drift)

### Métricas obligatorias
- **Brier score** global y por bucket temático (cuando n≥30)
- **Log loss**
- **AUC-ROC** y **AUC-PR**
- **Calibration error (ECE)** con bins de 10
- **Coverage de intervalos** vs nominal (¿el 90% real cae en el intervalo 90%?)
- **Lift contra baselines**:
  - Baseline 1: siempre predecir clase mayoritaria
  - Baseline 2: siempre predecir 50%
  - Baseline 3: media móvil histórica del proyecto-tipo
  - Baseline 4: regresión logística sin Context Engine

### Adversarial testing
- **Proyectos diseñados para confundir al modelo**: cofirmas atípicas (un legislador K firmando proyecto de LLA), proyectos de temática ambigua. Si el modelo confía mucho en estos, está sobreajustado.
- **Counterfactual stress test**: ¿qué pasaría si el ICG cambia en 0.1? Si la predicción cambia más de lo razonable, el modelo es frágil.

### Decision-theoretic evaluation
- Definir costo asimétrico: falso positivo (decir que un proyecto pasará y no pasa) vs falso negativo (decir que no pasará y pasa). El costo no es simétrico para el usuario.
- Threshold óptimo elegido para minimizar costo esperado, no para maximizar accuracy.

---

## 2.4 Mejoras del Context Engine

- **Source credibility weighting**: cada fuente tiene peso aprendido por consistencia histórica.
- **Cross-reference**: un evento solo se cuenta si aparece en ≥2 fuentes whitelist.
- **Anomaly detection sobre volumen**: si volumen de noticias sobre tema X salta >3σ, alerta y re-evaluación.
- **Counterfactual prompts a Sonnet**: "¿Qué evento haría cambiar la probabilidad de este proyecto en >0.2?" Útil para identificar riesgos.
- **Bayesian update explícito**: Context shift NO es feature directa, sino prior bayesiano sobre la salida del ensemble. Más interpretable.

---

## 2.5 Mejoras operativas

- **Shadow mode** para nuevos modelos: el nuevo corre en paralelo 4 semanas, sus predicciones se loguean pero no se publican.
- **Champion-challenger deployment**: promoción solo si challenger supera champion en Brier en al menos 60% de semanas.
- **A/B de features**: agregar feature nueva con flag `enabled=False` por default; entrenar dos modelos (con y sin), comparar antes de habilitar.
- **Backtesting harness reproducible**: comando `make backtest YEAR=2024` que reproduce exactamente la predicción del año pasado.

---

## 2.6 Trust & transparencia

- **Model card pública**: en sitio del proyecto, describir features, datos de entrenamiento, métricas en holdout, limitaciones conocidas.
- **Methodology page**: explicar el modelo en lenguaje accesible para periodistas y políticos.
- **Errata log público**: cada vez que una predicción importante falla, post-mortem público.
- **Pre-registered predictions**: para proyectos clave, publicar predicción ANTES de la votación, no después. Es la única forma honesta de demostrar calibración.
- **Open data**: predicciones históricas y métricas en CSV descargable. Permite auditoría independiente.

---

## 2.7 Edge cases específicos de la política argentina

Modelo debe manejar explícitamente:

- **Sesiones extraordinarias**: convocadas por PEN, fuera de calendario ordinario. Cambian dinámica.
- **DNU (Decreto de Necesidad y Urgencia)**: la "sanción" en sentido legislativo es la confirmación bicameral, no el dictado. Modelar como bills implícitos.
- **Insistencia**: si Senado rechaza, Diputados puede insistir con 2/3. Caso especial.
- **Pliegos del PEN**: nominación de jueces, embajadores. Lógica completamente distinta a leyes (no se modifican, se aprueban o rechazan).
- **Comisiones bicamerales** (BCRA, JGM): dinámica distinta a comisiones unicamerales.
- **Leyes "ómnibus"**: como Ley Bases. Mezclan decenas de temas. Tratamiento especial: dividir en sub-proyectos artificiales y predecir cada uno.
- **Tratados internacionales**: pasan por procedimiento especial.
- **Reformas constitucionales**: requieren ley declarativa + convención. Casi nunca aplican pero el sistema debe reconocerlas.
- **Vetos presidenciales**: el "ciclo de vida" del proyecto no termina con sanción si hay veto. Modelar como estado adicional.

---

# PARTE 3 — CHECKLIST PRE-LANZAMIENTO

Nada se enciende hasta que estos puntos pasen:

## Resiliencia
- [ ] Cada adapter externo tiene retry + circuit breaker + Pydantic validation
- [ ] Test de chaos: matar el container de cada servicio mientras corre el pipeline; sistema debe recuperar
- [ ] Test de Oracle reclamation: simular con `docker compose down -v`, verificar restore desde Backblaze en <2h
- [ ] Test de schema upstream: cambiar manualmente el shape de una respuesta HCDN mock, verificar que el sistema falla loud y no persiste basura
- [ ] Rate limit Anthropic simulado: respond con 429 desde mock; verificar backoff correcto
- [ ] Kill switch de costos: forzar `api_spend` artificial al límite, verificar que abortó

## Observabilidad
- [ ] Prometheus + Grafana corriendo
- [ ] Dashboard con ≥15 métricas críticas (lista en sección U)
- [ ] Alertas configuradas: Telegram + email
- [ ] Healthchecks.io outbound heartbeat funcionando
- [ ] Logs estructurados (JSON) con `structlog`, no `print`
- [ ] Trace ID por pipeline run para debugging

## Modelo
- [ ] Dataset de validación 200-300 leyes etiquetadas a mano
- [ ] Métricas en holdout final: Brier < baseline en al menos 0.05
- [ ] Calibración: ECE < 0.05
- [ ] Conformal prediction: coverage empírica dentro de ±2% del nominal
- [ ] Adversarial test pasado
- [ ] Cross-validation por régimen: el modelo generaliza milei/macri/kirchner
- [ ] Reliability diagram publicado

## Backtesting Histórico 2015-2026 (Fase 3.5 — ver documento dedicado)
- [ ] Backfill 2015-2026 completo con cobertura ≥ 90% vs fuentes secundarias (Senado, InfoLeg, OPC)
- [ ] Reconstrucción point-in-time de features completada para todo el histórico
- [ ] Test automatizado de no-leakage pasa 100% (`test_no_leakage()`)
- [ ] Walk-forward validation ejecutado con ≥ 10.000 predicciones simuladas
- [ ] Brier walk-forward < baseline en ≥ 60% de los meses del backtest
- [ ] ECE global walk-forward < 0.05
- [ ] Cobertura empírica de banda 90% en rango [0.87, 0.93]
- [ ] Catálogo `failure_modes_catalog` con ≥ 5 modos de fallo documentados
- [ ] Cada modo de fallo del catálogo tiene contramedida asignada a sprint/fase posterior
- [ ] Gap de Brier entre régimen político peor y mejor < 0.10
- [ ] Factor μ calibrado con bandas honestas basadas en bootstrap de residuals reales (NO imputación retroactiva)
- [ ] Methodology page con reliability diagram histórico y métricas por régimen lista para publicar
- [ ] Sanity check predictivo (live vs backtest) integrado al pipeline de inferencia
- [ ] Drift detection conectado a alertas (live performance vs distribución walk-forward esperada)
- [ ] Reproducibilidad bit-exacta verificada: `make backtest YEAR=2024 MONTH=06` regenera idénticas predicciones
- [ ] Tablas persistentes pobladas: `historical_predictions`, `features_pit`, `failure_modes_catalog`, `mu_calibration_curve`, `regime_performance`, `feature_importance_walkforward`

## Datos
- [ ] Canonical Legislator Resolver: dataset de 100 nombres ambiguos, 100/100 correctos
- [ ] Backfill histórico completo desde 2016 ingerido y verificado contra fuente secundaria (Congresso, OPC)
- [ ] Test de idempotencia: ejecutar ingest dos veces, verificar 0 duplicados
- [ ] Versionado: cada predicción referenciable a `(model_hash, data_snapshot_hash)`

## Operacional
- [ ] Migrations con Alembic + rollback testeado
- [ ] Backup → restore drill exitoso en <2h
- [ ] Standby Hetzner provisionado (aunque no activo)
- [ ] DNS con TTL bajo
- [ ] Firewall configurado, Postgres no expuesto
- [ ] Secrets en .env con permisos 600
- [ ] Runbook de incidentes escrito (qué hacer si Oracle reclama, si Sonnet falla, si HCDN cambia schema)

## Trust y legal
- [ ] Model card pública redactada
- [ ] Methodology page redactada
- [ ] Disclaimer legal redactado (no asesoramiento, predicciones probabilísticas, etc.)
- [ ] Política de erratas pública
- [ ] Estructura legal mínima (monotributo / SRL) operativa antes de primera publicación con nombres

## Pre-launch sanity
- [ ] 4 semanas de shadow mode: predicciones generadas, no publicadas. Comparar con resultados reales semana a semana.
- [ ] Si en 4 semanas el Brier shadow > baseline + 0.05, NO lanzar. Iterar.
- [ ] Si pasa, primer lanzamiento es "soft": 5 proyectos por semana, no 200. Escalar gradualmente.

---

# Resumen

Resiliencia: 25 superficies de fallo identificadas, todas con mitigación concreta. La mayoría aplican principios estándar (retry+backoff, circuit breaker, validation, structured logging, kill switches) adaptados a este stack. El blueprint original asumía que las dependencias externas eran confiables — ahora ninguna lo es por default.

Mejoras del índice: 14 features adicionales sobre los 11 originales, ensemble jerárquico por cámara + modelo de trayectoria secuencial, calibración con Beta + conformal prediction, evaluación con 4 datasets disjuntos y 4 baselines, transparencia radical (model card, pre-registered predictions, errata log).

Edge cases argentinos: 9 casos específicos del derecho parlamentario que el modelo debe reconocer (DNU, insistencia, pliegos, etc.).

Pre-launch checklist: 30+ items que deben pasar. El item más importante: 4 semanas de shadow mode con Brier shadow > baseline + 0.05. Si no pasa, no lanzar.

Costo adicional sobre v2.1: cero. Toda la resiliencia es trabajo de ingeniería, no de hardware. Las mejoras del modelo requieren más tiempo de feature engineering y entrenamiento, no infraestructura.

Tiempo realista: agregar estas mejoras al roadmap de 12 semanas lo extiende a 16-18 semanas si trabajás 20h/sem. Si querés lanzar antes, hay que priorizar: Parte 1 (resiliencia) es obligatoria; Parte 2.1 y 2.3 (features adicionales y evaluación rigurosa) son P1; Parte 2.2 (modelos avanzados) puede esperar a v2 post-lanzamiento.
