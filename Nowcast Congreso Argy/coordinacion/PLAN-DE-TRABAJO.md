# PLAN DE TRABAJO — Nowcast Legislativo

Plan estructurado para trabajo en paralelo. Para cada bloque: **qué** hay que hacer y **cómo**. El orden de prioridad sale del gate de Fase 0 (predecir el voto-dirección por bloque ya da ~0,99 **en promedio**; el valor está en asistencia, embudo, posición de bloque y —matiz 2026-06-30— en el **desvío individual vs. bloque** de los pocos legisladores bisagra que el promedio esconde; ver 1B.4).

## Cómo se trabaja (resumen operativo)
- Cada ítem mapea a un módulo/carpeta con su `README.md` (contrato).
- Reclamás el módulo en `TABLERO.md`, trabajás en rama propia, registrás en `ESTADO-DEL-PROYECTO.md`, abrís PR. Detalle en `PROTOCOLO-GIT.md`.

---

## Fase 0 — Datos y baseline · **CERRADA**
**Qué:** medir el piso de bloque y validar fuentes. **Resultado:** dirección ≈ 0,99; 4-clases ≈ 0,81; CKAN congelado en 2020. Ver `fase0/outputs/`.

---

## Fase 1A — Base de datos propia: semilla → canónica → bot (ver ADR-0002)
**Principio:** Andy Tow es **semilla de un solo uso**, no dependencia viva. Construimos nuestra base y la mantenemos con un bot. Paralelizable salvo donde se indica.

### 1A.0 docs/schemas — contrato de datos *(primero, transversal)*
- **Qué:** definir esquema y `schema_version` por tipo (votación, voto, legislador, proyecto, feature). Base del esquema canónico.
- **Cómo:** markdown + json-schema por tipo, partiendo de las columnas reales de `fase0`. Todo parquet valida contra su schema.
- **Gate:** los demás módulos escriben parquet que valida.

### 1A.1 datos/decada_votada — semilla histórica
- **Qué:** exportar una vez los datos de Andy Tow vía legislAr (Diputados 1998–2019, Senado 2004–2013) a parquet canónico.
- **Cómo:** R + legislAr (`show_available_bills` → `get_bill_votes`), escribir parquet con `schema_version`. **R solo acá**; el resto en Python.
- **Gate:** export reproducible y validado; cobertura documentada.

### 1A.2 datos/argentinadatos — datos recientes
- **Qué:** Diputados 2020–2025 y Senado 2024–2025 desde `api.argentinadatos.com`, al esquema canónico.
- **Cómo:** endpoints `/v1/diputados/actas/` y `/v1/senado/actas/` (traen `votos[]` por legislador). Aplanar a cabecera+detalle. Reusar patrón resiliente de `fase0/src/common.py`.
- **Gate:** serie continua al concatenar con semilla y CKAN.

### 1A.3 datos/canonica — base propia única *(cuello de botella: dueño único)*
- **Qué:** unificar semilla + CKAN + argentinadatos + senado + expedientes en una sola tabla; deduplicar solapamientos y resolver entidades (legislador/bloque).
- **Cómo:** precedencia de fuentes, clave estable por acta, entity resolution; carga idempotente. Es la fuente de verdad de `variables/` y `modelo/`.
- **Gate:** sin duplicados en períodos solapados; entity resolution validada en muestra.

### 1A.4 datos/bot_recoleccion — el bot *(depende de canonica)*
- **Qué:** proceso programado que detecta votaciones nuevas en fuentes oficiales y las agrega a la canónica (upsert idempotente).
- **Cómo:** leer último acta conocido por cámara; pedir a cada fuente solo lo posterior; cron local primero, Cloud Scheduler en nube. Resiliencia obligatoria.
- **Gate:** corrida idempotente; detecta actas nuevas en ventana de prueba; alerta ante caída de fuente.

### 1A.5 datos/expedientes — universo de proyectos (sesgo de selección)
- **Qué:** ingestar proyectos presentados (CKAN `expedientes`); medir % que llega a votación nominal.
- **Cómo:** cruzar por número de expediente parseado del título de cada acta.
- **Gate:** número de sesgo de selección publicado en ESTADO.

### 1A.6 datos/senado — cerrar el hueco 2014–2023
- **Qué:** conseguir Senado 2014–2023 (no está ni en la semilla ni en argentinadatos).
- **Cómo:** DatosAbiertos Senado + scraping del portal de votaciones del Senado si hace falta.
- **Gate:** mapeo de bloques del Senado resuelto; franja cubierta o documentada como faltante.

---

## Fase 1B — Las tres fuentes de incertidumbre (paralelizable, leen de la canónica)
### 1B.1 variables/embudo — supervivencia del proyecto *(prioritario)*
- **Qué:** P(un proyecto llega al recinto): presentado→comisión→dictamen→tratamiento.
- **Cómo:** etiquetar ciclo de vida del expediente; modelo de supervivencia / clasificador temporal; backtesting walk-forward sin leakage.
- **Gate:** mejora sobre predecir solo el voto final.

### 1B.2 variables/asistencia_quorum — quién aparece y se abstiene *(prioritario)*
- **Qué:** P(asiste) y P(abstiene) por legislador-acta (el ~19% que el bloque no explica).
- **Cómo:** presentismo histórico + atributos de la sesión; clasificador. Baseline: tasa de presentismo histórica por legislador.
- **Gate:** supera ese baseline.

### 1B.3 variables/legislador · proyecto · bloque — feature stores
- **Qué/Cómo:** features point-in-time por legislador, por proyecto (tema/autor/mayoría/NLP) y series por bloque (cohesión/posición/fracturas). Independientes entre sí.
- **Gate:** sin leakage; features validadas en muestra.

### 1B.4 modelo/voto_individual — desvío individual + pivotes *(reformulado 2026-06-30)*
- **Replanteo:** el voto-dirección por bloque acierta ~0,99, pero ese número es un **promedio** que tapa a los díscolos. El conteo agregado (p.ej. 120/257) es un punto; su varianza la cargan **10–20 bisagras** cuya (in)disciplina mueve la P(aprobación) en votaciones ajustadas. Por eso `modelo/voto_individual` se descongela: el objetivo no es predecir el voto medio, sino **separar el comportamiento partidario del individual** y modelar el desvío del legislador vs. su bloque. En 2024–25 la disciplina se afloja → más espacio para este modelo.
- **Qué (dos productos):** (1) **partidario/bloque** = posición esperada del bloque, para recuento agregado y análisis macro; (2) **individual/parlamentario** = el desvío respecto del bloque.
- **Cómo (cuatro piezas):** (a) **índice de disciplina individual** por legislador (tasa de desvío vs. bloque, global y por tema, time-aware); (b) **modelo de defección** P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral); (c) **recuento como distribución** — simular cada voto Bernoulli(pᵢ)=posición de bloque ajustada por desvío → distribución del conteo con intervalo, no número puntual; (d) **detección de pivotes** — qué legisladores son bisagra para una ley y cuánto mueve cada uno la P(aprobación). Distinguir partido ≠ bloque ≠ parlamentario.
- **Lee de:** `datos/canonica` (~781k votos) + `variables/legislador` y `variables/bloque` cuando existan.
- **Gate:** (1) dimensionar el set pivote: cuántos legisladores superan un umbral de divergencia vs. su bloque; (2) el recuento como distribución calibra mejor que el punto del baseline en votaciones ajustadas (backtesting walk-forward, sin leakage).
- **Nota de gobernanza:** cambia el rumbo de un módulo antes congelado → conviene un **ADR** en `coordinacion/DECISIONES/`.

---

## Fase 2 — Composición del nowcast (depende de Fase 1)
### 2.1 modelo/agregador_institucional
- **Qué:** P(mayoría|recinto) combinando voto + asistencia con reglas de quórum y tipo de mayoría (simple, absoluta, 2/3).
- **Gate:** reproduce el `resultado` histórico dentro de tolerancia.

### 2.2 modelo/ensemble *(cuello de botella: dueño único)*
- **Qué:** P(aprobación) = P(llega al recinto) × P(mayoría|recinto); calibrar (Brier/reliability).
- **Gate:** calibración dentro de tolerancia en backtesting.

---

## Fase 3 — Producto y validación comercial (en paralelo a Fase 2)
### 3.1 producto/dashboard
- **Qué:** tablero interno radar de tracción + mapa de pivotes + escenarios (encuadre *augmentation*).
- **Gate:** una consultora valida utilidad; buscar 1 LOI/piloto pago.

---

## Fase 4 — Nube *(NO abrir sin pagador validado)*
`producto/api` (FastAPI), el bot en Cloud Scheduler, Postgres, monitoreo de drift, auth/multi-tenant, términos de uso + disclaimer. La migración es decisión comercial, no técnica.

---

## Mapa de paralelización
| Pueden ir en simultáneo | Por qué |
|---|---|
| docs/schemas → luego decada_votada, argentinadatos, expedientes, senado | fuentes sin archivos compartidos |
| embudo, asistencia_quorum, legislador, proyecto, bloque | leen de la canónica, escriben en su carpeta |
| dashboard mientras se cierra ensemble | consume contrato, no código |

**Cuellos de botella (un solo dueño, coordinar):** `docs/schemas` (transversal), `datos/canonica` (junta las fuentes), `modelo/ensemble` (junta los modelos).
