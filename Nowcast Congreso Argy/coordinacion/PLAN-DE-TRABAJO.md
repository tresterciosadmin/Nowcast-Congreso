# PLAN DE TRABAJO — Nowcast Legislativo

Plan estructurado para trabajo en paralelo. Para cada bloque: **qué** hay que hacer y **cómo**. El orden de prioridad sale del gate de Fase 0 (predecir el voto-dirección por bloque ya da ~0,99; el valor está en asistencia, embudo y posición de bloque).

## Cómo se trabaja (resumen operativo)
- Cada ítem de abajo mapea a un módulo/carpeta con su `README.md` (contrato).
- Reclamás el módulo en `TABLERO.md`, trabajás en rama propia, registrás en `ESTADO-DEL-PROYECTO.md`, abrís PR. Detalle en `PROTOCOLO-GIT.md`.
- "Cómo" = el enfoque técnico mínimo; el detalle fino se decide dentro del módulo y se documenta en ESTADO.

---

## Fase 0 — Datos y baseline · **CERRADA**
**Qué:** medir el piso de bloque y validar fuentes. **Resultado:** dirección ≈ 0,99; 4-clases ≈ 0,81; CKAN congelado en 2020. Ver `fase0/outputs/`.

---

## Fase 1 — Las tres fuentes de incertidumbre (paralelizable)
Estos cuatro módulos se pueden trabajar **en simultáneo** por personas distintas porque no comparten archivos. Dependencia única: que `docs/schemas` exista primero.

### 1.0 docs/schemas — contrato de datos *(hacelo primero, transversal)*
- **Qué:** definir el esquema y `schema_version` de cada tipo: votación (cabecera), voto (detalle), legislador, proyecto, feature.
- **Cómo:** un markdown + json-schema por tipo en `docs/schemas/`. Tomá como base las columnas reales ya vistas en `fase0` (acta_id, bloque, voto, tipo_mayoria, resultado, fecha...). Todo parquet en `data/clean` debe validar contra su schema.
- **Gate:** los demás módulos pueden escribir parquet que valida.

### 1.1 datos/argentinadatos — datos recientes 2020–2025
- **Qué:** ingestar Diputados (2020→oct-2025) y Senado (2024→nov-2025) desde `api.argentinadatos.com`, normalizado al MISMO esquema que CKAN.
- **Cómo:** endpoints `/v1/diputados/actas/` y `/v1/senado/actas/` (cada acta trae `votos[]` por legislador con bloque). Aplanar a cabecera+detalle, mapear nombres de campos al schema, guardar parquet. Reusar el patrón resiliente de `fase0/src/common.py` (reintentos/backoff/logging).
- **Gate:** serie continua 2011→2025 sin huecos al concatenar con CKAN.

### 1.2 datos/expedientes — universo de proyectos (sesgo de selección)
- **Qué:** ingestar proyectos presentados (CKAN `expedientes`) y cuantificar cuántos llegan a votación nominal.
- **Cómo:** bajar el dataset `expedientes`, cruzar con las actas por número de expediente parseado del `titulo`. Métrica: % de proyectos presentados que tienen votación nominal.
- **Gate:** número de sesgo de selección publicado en `ESTADO`.

### 1.3 variables/embudo — supervivencia del proyecto *(prioritario)*
- **Qué:** modelar P(un proyecto llega al recinto): presentado→comisión→dictamen→tratamiento.
- **Cómo:** etiquetar el ciclo de vida de cada expediente; modelo de supervivencia / clasificador temporal. Backtesting walk-forward (entrenar t, validar t+1), sin leakage.
- **Gate:** mejora medible sobre predecir solo el voto final.

### 1.4 variables/asistencia_quorum — quién aparece y se abstiene *(prioritario)*
- **Qué:** modelar P(asiste) y P(abstiene) por legislador-acta. Es el ~19% que el bloque no explica.
- **Cómo:** features de presentismo histórico por legislador + atributos de la sesión; clasificador. Baseline a superar: tasa de presentismo histórica por legislador.
- **Gate:** supera ese baseline de presentismo.

---

## Fase 2 — Composición del nowcast
Depende de Fase 1. No empezar hasta que sus insumos estén HECHOS.

### 2.1 modelo/agregador_institucional
- **Qué:** convertir votos individuales + asistencia en P(mayoría|recinto) aplicando quórum y tipo de mayoría (simple, absoluta, 2/3).
- **Cómo:** simulación: combinar P(asiste)·P(voto) por legislador, agregar por cámara, aplicar la regla de `tipo_mayoria` de la cabecera. Validar contra resultados históricos reales.
- **Gate:** reproduce el `resultado` histórico dentro de tolerancia.

### 2.2 modelo/ensemble
- **Qué:** P(aprobación) = P(llega al recinto) × P(mayoría|recinto).
- **Cómo:** componer salidas de `embudo` y `agregador`; calibrar (Brier/reliability).
- **Gate:** calibración dentro de tolerancia en backtesting.

---

## Fase 3 — Producto y validación comercial (en paralelo a Fase 2)
### 3.1 producto/dashboard
- **Qué:** tablero interno radar de tracción + mapa de pivotes + escenarios (encuadre *augmentation*, no oráculo).
- **Cómo:** Streamlit o notebook sobre las salidas del ensemble; foco en explicabilidad.
- **Gate:** una consultora valida utilidad en entrevista; buscar 1 LOI/piloto pago.

---

## Fase 4 — Nube *(NO abrir sin pagador validado)*
`producto/api` (FastAPI), ingesta programada, Postgres, monitoreo de drift, auth/multi-tenant, términos de uso + disclaimer. La migración es decisión comercial, no técnica.

---

## Mapa de paralelización (quién puede trabajar a la vez)
| Pueden ir en simultáneo | Por qué |
|---|---|
| docs/schemas → luego argentinadatos, expedientes, embudo, asistencia_quorum | módulos sin archivos compartidos |
| legislador, proyecto, bloque | feature stores independientes |
| dashboard mientras se cierra ensemble | consume contrato, no código |

**Cuellos de botella (un solo dueño, coordinar):** `docs/schemas` (transversal), `modelo/ensemble` (junta todo). Hacelos con dueño único y avisando en TABLERO.
