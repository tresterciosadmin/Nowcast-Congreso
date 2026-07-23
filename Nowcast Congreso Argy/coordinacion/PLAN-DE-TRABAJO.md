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

### 1A.6b datos/licencias_suspensiones — registro y notificador *(a crear; decisión ADR-0004)*
- **Qué:** registro histórico + herramienta que detecte y NOTIFIQUE suspensiones y pedidos de licencia de legisladores (con fechas desde/hasta), para excluirlos del índice de indisciplina (su "no acompañar" no es una decisión libre) y alimentar asistencia_quorum.
- **Cómo:** fuentes candidatas: resoluciones de cámara, versiones taquigráficas, Boletín Oficial; formato tipo padrón curado (como `datos/senado/data/padron_*`). El notificador avisa cuando aparece una licencia/suspensión nueva.
- **Gate:** los casos conocidos (De Vido Art. 70, bancas en licencia de ministros/gobernadores) quedan cubiertos con fechas correctas.

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

### 1B.2 variables/asistencia_quorum — quién aparece y se abstiene *(prioritario; escalón 1 HECHO)*
- **Qué:** P(asiste) y P(abstiene) por legislador-acta (el ~19% que el bloque no explica).
- **Cómo:** presentismo histórico + atributos de la sesión; clasificador. Baseline: tasa de presentismo histórica por legislador.
- **Gate:** supera ese baseline.
- **Estado (2026-07-11):** escalón 1 construido (`asistencia.py`: presentismo por legislador, global 74,7%) y conectado al agregador (modo asistencia). **Resultado del backtest — informativo/negativo:** alimentar el motor con el presentismo PROMEDIO (aun individual) EMPEORA la calibración (Brier 0,011→0,034): mete ausencias falsas, porque en una votación que efectivamente ocurrió la asistencia fue mayor que el promedio (sesgo de selección). En cambio, un subproducto SÍ sirvió y se adoptó: leer la posición del bloque **entre presentes** (no contar ausentes como "no acompaña") mejora el motor (Brier 0,011→0,0089). **Conclusión:** el presentismo a secas es el baseline a SUPERAR; la asistencia debe ser **CONDICIONAL al proyecto** (tema, origen, incomodidad) → **escalón 2, en pausa hasta tener el feature store** (ver 1B.3 y `variables/proyecto/FEATURE-STORE.md`). Escalones futuros: (2) P(presente | tema/origen/saliencia/año electoral); (3) quórum como jugada estratégica de bloque.

### 1B.3 variables/legislador · proyecto · bloque — feature stores
- **Qué/Cómo:** features point-in-time por legislador, por proyecto (tema/autor/mayoría/NLP) y series por bloque (cohesión/posición/fracturas). Independientes entre sí.
- **Diseño del feature store por proyecto (2026-07-11, decisión de Valle: diseñar antes de recolectar):** `variables/proyecto/FEATURE-STORE.md` define las 6 familias de rasgos por proyecto/votación (A identidad/trámite, B tema/taxonomías, C autoría+origen oficialismo/oposición, D institucionales, E contexto ICG Di Tella/electoral, F derivadas CONDICIONADAS: posición de bloque por tema, presentismo condicionado, disciplina por tema) y a qué etapa alimenta cada una. Es el desbloqueo de todo el condicionamiento (asistencia y posición de bloque). **Orden:** (1) correr el agente de taxonomías [desbloqueo #1: API key batch o clasificar muestra a mano], (2) regla origen oficialismo/oposición por fecha, (3) ingesta ICG Di Tella (serie mensual UTDT), (4) derivadas condicionadas, (5) calendario electoral.
- **Avance 2026-07-11 sobre ese orden:** **(1) parcial — vocabulario VALIDADO a mano** (88 actas estratificadas 2001-25: 82% clasificable por título, 89% confianza alta/media; 5 huecos y 4 fronteras propuestos en `variables/proyecto/RESULTADOS-muestra-manual.md`; la muestra queda como set de referencia agente-vs-humano; el batch sigue esperando la API key). **(3) HECHA — ICG Di Tella vivo:** `variables/proyecto/data/icg_mensual.csv` (296 meses, nov-2001→jun-2026, 0 huecos, validado contra informes) + `src/ingesta_icg.py` con modo `serie` (Excel oficial; layout transpuesto resuelto) y modo `ultimo` (scrapea la página de informes para el mes nuevo antes de que rote el Excel; idempotente; invocable por el futuro bot). Tests 21 OK. **Siguen:** (2) regla origen por fecha ← próximo natural, (4) y (5).
- **Avance 2026-07-22/23 (Valle+Claude) — TEMA y ORIGEN por acta, sin esperar el batch de PDFs:** desbloqueado el condicionamiento por texto de las actas VOTADAS. (B tema) `variables/proyecto/tema_por_acta.py` clasifica por TÍTULO las actas votadas → `tema_por_acta.parquet` (1.537 actas, 2011-2026, 87% de cobertura en la ventana reciente del Senado). (C origen) `variables/proyecto/origen_por_acta.py` etiqueta `origen` (EJECUTIVO/OFICIALISMO/OPOSICION) + `origen_lado` (GOBIERNO/OPOSICION) + `gobierno` de turno POR ACTA, determinístico sin API key (4 vías: código de expediente, **código embebido en el título** del Senado viejo `PE-608/03`, O.D.→expedientes_resultados, match de título) → `origen_por_acta.parquet` (**59% global / 54,5% Senado**; tapa el hueco 2004-2014). (F derivadas) `variables/bloque` condiciona la dirección por tema/origen con shrinkage + **guard de mismo gobierno** (no mezcla eras en la ventana) + **exclusión de actas AUX** (homenajes/trámite/tratados = consenso, no informan postura). **Validado:** proyecto de SALUD de la oposición en Diputados (47 actas de historia) → LLA NEGATIVO 0,31, kirchnerismo AFIRMATIVO 0,98 = la política real. **Límite conocido (no del método, de los datos):** cruces finos (ej. ECON×GOBIERNO en el Senado) tienen 1-2 actas en la ventana → esperan más cobertura + multitemáticas (backlog).
- **Perfil temático por legislador (central, pedido de Valle 2026-07-02):** además del consolidado afirmativos/negativos (que cualquier página ya muestra), el diferencial es el **desagregado por taxonomía**: para cada legislador × período × taxonomía (`docs/taxonomias`), pct_afirmativo / pct_negativo / tasa_desvio → detectar tendencia a aprobar o rechazar dentro de cada tema. Sale como hoja "PorTema" en `legisladores.xlsx`. **Depende de:** (1) corrida a escala del agente de taxonomías (`variables/proyecto`, necesita API key) que llena `proyecto_taxonomias`; (2) cruce acta→expediente→proyecto para etiquetar cada votación con su tema (`datos/expedientes` + columna `expediente` de las actas).
- **Gate:** sin leakage; features validadas en muestra.

### 1B.4 modelo/voto_individual — desvío individual + pivotes *(reformulado 2026-06-30)*
- **Replanteo:** el voto-dirección por bloque acierta ~0,99, pero ese número es un **promedio** que tapa a los díscolos. El conteo agregado (p.ej. 120/257) es un punto; su varianza la cargan **10–20 bisagras** cuya (in)disciplina mueve la P(aprobación) en votaciones ajustadas. Por eso `modelo/voto_individual` se descongela: el objetivo no es predecir el voto medio, sino **separar el comportamiento partidario del individual** y modelar el desvío del legislador vs. su bloque. En 2024–25 la disciplina se afloja → más espacio para este modelo.
- **Qué (dos productos):** (1) **partidario/bloque** = posición esperada del bloque, para recuento agregado y análisis macro; (2) **individual/parlamentario** = el desvío respecto del bloque.
- **Cómo (cuatro piezas):** (a) **índice de disciplina individual** por legislador (tasa de desvío vs. bloque, global y por tema, time-aware); (b) **modelo de defección** P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral); (c) **recuento como distribución** — simular cada voto Bernoulli(pᵢ)=posición de bloque ajustada por desvío → distribución del conteo con intervalo, no número puntual; (d) **detección de pivotes** — qué legisladores son bisagra para una ley y cuánto mueve cada uno la P(aprobación). Distinguir partido ≠ bloque ≠ parlamentario.
- **Lee de:** `datos/canonica` (~781k votos) + `variables/legislador` y `variables/bloque` cuando existan.
- **Definición vigente del desvío: v2 (ADR-0004, 2026-07-02)** — indisciplina total: conductas aprobar/rechazar/no-acompañar; línea = mayoría de TODOS los escaños del bloque; estricta; desempate por linaje; parcial en OTRO/PROVINCIAL; presidencias de Diputados excluidas.
- **Pendientes que abre el v2:** (a) **reclasificar la bolsa OTRO/PROVINCIAL hacia linajes** (manual y/o automática; toca entity_resolution=canonica, coordinar con Franco) — **AVANCE 2026-07-23 (Valle+Claude): resuelto para el Senado reciente desde la capa de consumo.** Los votos del Senado 2024+ (fuente argentinadatos) llegaban con `bloque="SIN BLOQUE"`→OTRO/PROVINCIAL para los 8.496 (la ingesta no resolvió el bloque). `variables/bloque._enriquecer_linaje_senado` recupera el linaje real por NOMBRE contra el padrón oficial, **mandate-aware** (fecha del voto en [desde,hasta], sin anacronismos) + fallback apellido, + **override manual curado** `datos/padron/data/senado_linaje_manual.csv` para los 22 que dejaron banca en dic-2025 (COMPLETO por Valle) + canonicalización de etiquetas. Resultado: OTRO/PROVINCIAL del Senado 2024+ **53%→26%**; el nowcast del Senado ya condiciona. **Propuesta a Franco:** absorberlo en `votos_resuelto`/entity_resolution (hoy es parche de consumo, no de la fuente); la lógica mandate-aware + el override manual son reutilizables. (b) decidir tratamiento de **suspensiones y licencias**; (c) **ponderación por trascendencia** de la votación (sesión futura); (d) **disciplina ideológica por taxonomía** (consistencia de voto por tema; mitiga monobloques — ver 1B.3).
- **Gate:** (1) dimensionar el set pivote: cuántos legisladores superan un umbral de divergencia vs. su bloque; (2) el recuento como distribución calibra mejor que el punto del baseline en votaciones ajustadas (backtesting walk-forward, sin leakage).
- **Nota de gobernanza:** cambia el rumbo de un módulo antes congelado → conviene un **ADR** en `coordinacion/DECISIONES/`.

---

## Fase 2 — Composición del nowcast (depende de Fase 1)
### 2.1 modelo/agregador_institucional *(v1 CONSTRUIDO 2026-07-10)*
- **Qué:** P(mayoría|recinto) combinando voto + asistencia con reglas de quórum y tipo de mayoría (simple, absoluta, 2/3).
- **Gate:** reproduce el `resultado` histórico dentro de tolerancia.
- **Estado (2026-07-10/11):** motor construido (`agregador.py`): recuento como DISTRIBUCIÓN (Monte Carlo por legislador) → P(aprobación) con banda. Tests OK. **Backtest 4.890 actas: Brier 0,0089, skill 0,81, acc 0,990** (con la lectura de bloque entre presentes adoptada por default). Fuerte en agregado; residual chico en las disputadas (bin de rechazo seguro con 9% de aprobación real). Panel interactivo: `PANEL-NOWCAST.html`. Falta: proyectar la posición de bloque desde el feature store (hoy usa la observada) para nowcast de proyectos no votados.

### 2.2 modelo/ensemble *(cuello de botella: dueño único)*
- **Qué:** P(aprobación) = P(llega al recinto) × P(mayoría|recinto); calibrar (Brier/reliability).
- **Gate:** calibración dentro de tolerancia en backtesting.
- **Estado (2026-07-22, Valle+Claude) — ROSTER NOMINAL (cimiento "las partes hacen al todo"):** `nowcast_auto` arma el escenario como UNA FILA POR LEGISLADOR del padrón vigente a la fecha, cada uno con SU tasa de desvío individual (escalera reciente→global→bloque; el promedio de bloque solo como fallback para quien no tiene historial — única excepción). Se ELIMINÓ `_expandir_roster` (clonaba el desvío PROMEDIO del bloque `bancas` veces, aplicándoselo también a los 753 legisladores con desvío medido) + el comando `demo` + el `nowcast` con escenario JSON a mano (eran de la puesta en marcha del 10-jul). La dirección de bloque la proyecta `variables/bloque` (condicionable por tema/origen). Caso testigo 1167-D-2025 con `--origen GOBIERNO` se endereza (LLA 0,33→0,88; kirchnerismo 0,85→0,44). **Pendiente:** (1) **backtest de la cadena completa** (P(llega)×P(mayoría)) con roster nominal + tema/origen; (2) automatizar el `--tema`/`--origen` leyéndolos del PROPIO proyecto objetivo (hoy se pasan a mano).

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

**Cuellos de botella (un solo dueño, coordina
---

## Backlog anotado (pendientes, no abrir aún)

### Proyectos MULTITEMÁTICOS (leyes ómnibus) — pendiente (anotado 2026-07-22, Valle)
El tagger de temas (`variables/proyecto/tema_por_acta.py`) y el v2 de bloque usan hoy **un solo tema primario** por votación. Las leyes ómnibus mezclan varias materias en una sola votación y no encajan en un tema único: p. ej. **Ley Bases** (economía + desregulación + laboral + energía + privatizaciones), **Ley de Glaciares** (ambiente + minería + federalismo), y la **ley de desregulación difundida hoy en el Congreso**. El tagger YA guarda todas las etiquetas (`todas_ids`, multi-label), pero el condicionamiento del v2 sólo lee la primaria. **Pendiente:** decidir cómo condiciona la dirección de bloque cuando un proyecto es multitemático (¿promedio ponderado de las posturas por cada tema?, ¿el tema dominante?, ¿la materia más conflictiva?). **Por ahora se omite** — se usa el tema primario. Retomar cuando el v2 esté validado con temas de un solo eje.
- **Refuerzo 2026-07-23 (Valle):** la sesión confirmó que además del tema hace falta MÁS COBERTURA DE ACTAS. Un mismo tema mezcla consenso y conflicto: p. ej. "ECON" o "TRAB" en el Senado 2024-25 son mayormente proyectos que la oposición también acompañó, no las reformas contenciosas del gobierno (que aún no están en los datos votados). La exclusión de actas AUX (consenso puro: homenajes/trámite/tratados) ya está implementada en `variables/bloque` (`excluir_aux`), pero separar "proteger vs. desregular" dentro de un mismo tema necesita la designación multitemática + más actas. Dos ejes del mismo pendiente: (i) multi-label operativo, (ii) volumen de votaciones contenciosas.
