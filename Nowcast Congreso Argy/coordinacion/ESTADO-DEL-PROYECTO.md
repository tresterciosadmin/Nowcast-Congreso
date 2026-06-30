# ESTADO DEL PROYECTO — documento vivo

> **Este archivo se actualiza en CADA modificación del repo.** Es la fuente de verdad de qué se hizo y cómo. Un PR que cambia algo y no agrega su entrada acá no se mergea.

## Cómo actualizarlo (obligatorio)
Agregá una entrada **arriba de todo** en la sección "Bitácora" con este formato exacto:

```
### [AAAA-MM-DD] <módulo> — <título corto>
- **Quién:** nombre o ID (ej. Claude-A / Franco)
- **Qué:** qué cambió, en una o dos frases.
- **Cómo:** enfoque técnico / decisiones clave / comando para reproducir.
- **Archivos:** rutas tocadas.
- **Estado del módulo:** PENDIENTE | EN CURSO | HECHO | CONGELADO.
- **Próximo paso:** qué queda, o "ninguno".
```

No borres entradas viejas. Si algo se revierte, agregá una entrada nueva explicándolo.

## Tablero de estado por módulo (resumen)
Mantené esta tabla sincronizada con la bitácora.

| Módulo | Estado | Owner |
|---|---|---|
| docs/schemas | HECHO (schema_version=1) | — |
| datos/decada_votada | EN CURSO (export_seed.R listo, falta correrlo en R) | — |
| datos/canonica | PENDIENTE (base propia, fuente de verdad) | — |
| datos/bot_recoleccion | PENDIENTE (depende de canonica) | — |
| datos/ckan_diputados | HECHO (en `fase0/`, migrar) | — |
| datos/argentinadatos | PENDIENTE | — |
| datos/senado | PENDIENTE (hueco 2014–2023) | — |
| datos/seguimiento | EN CURSO (extractor de giros Dip+Sen, validado en vivo) | Valle |
| datos/proyectos | EN CURSO (base SQLite + export Excel) | Valle |
| docs/taxonomias | HECHO (vocabulario controlado v1, 74 ids) | Valle |
| datos/expedientes | PENDIENTE | — |
| variables/legislador | PENDIENTE | — |
| variables/proyecto | EN CURSO (agente de taxonomías LLM) | Valle |
| variables/bloque | PENDIENTE | — |
| variables/asistencia_quorum | PENDIENTE (prioritario) | — |
| variables/embudo | PENDIENTE (prioritario) | — |
| variables/contexto | FUTURO | — |
| modelo/voto_individual | DESCONGELADO / reformulado (desvío individual + pivotes) | — |
| modelo/agregador_institucional | PENDIENTE | — |
| modelo/ensemble | PENDIENTE | — |
| evaluacion/baseline | HECHO | — |
| evaluacion/backtesting | PENDIENTE | — |
| evaluacion/metricas | PENDIENTE | — |
| producto/dashboard | PENDIENTE | — |
| producto/api | FUTURO | — |

---

## Bitácora (más reciente arriba)
### [2026-06-30] modelo/voto_individual — Descongelado y reformulado (desvío individual + pivotes)
- **Quién:** Claude (con Valle)
- **Qué:** se descongela `modelo/voto_individual` y se reformula su objetivo. NO es predecir el voto medio (eso lo resuelve la regla de bloque ~0,99); es **separar dos comportamientos** y modelar el desvío del legislador respecto de su bloque. Razón (replanteo de Valle): el conteo agregado es un punto, pero la varianza real de ese punto la cargan 10–20 bisagras cuya (in)disciplina puede mover contundentemente la P(aprobación) en votaciones ajustadas. El ~0,99 es un PROMEDIO que tapa a los díscolos; y en 2024–25 la disciplina se afloja (más espacio para el modelo). Por ahora es solo actualización del plan; sin código todavía.
- **Cómo:** dos productos distintos. (1) **Partidario/bloque** = posición esperada del bloque, para recuento agregado y análisis macro (ya medido). (2) **Individual/parlamentario** = (a) índice de disciplina individual por legislador (tasa de desvío vs. bloque, global y por tema, time-aware); (b) modelo de defección P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral); (c) recuento como DISTRIBUCIÓN (simular cada voto Bernoulli(pᵢ)=bloque ajustado por desvío) con intervalo, no número puntual; (d) detección de pivotes (qué legisladores son bisagra para una ley y cuánto mueve cada uno la P). Distinguir partido ≠ bloque ≠ parlamentario.
- **Archivos:** `coordinacion/{ESTADO-DEL-PROYECTO.md, TABLERO.md, EN-HUMANO.md, PLAN-DE-TRABAJO.md}`.
- **Estado del módulo:** modelo/voto_individual DESCONGELADO / reformulado (en plan, sin empezar el código). Conviene un ADR en `coordinacion/DECISIONES/` que formalice el cambio de rumbo.
- **Próximo paso:** reclamar el módulo en TABLERO; medir contra los ~781k votos cuántos legisladores superan un umbral de divergencia (dimensionar el set pivote); arrancar por el índice de disciplina individual. Depende de `datos/canonica`.

### [2026-06-30] variables/proyecto — Agente de taxonomías (LLM / Claude API)
- **Quién:** Claude (con Valle)
- **Qué:** agente que clasifica un proyecto leyendo su PDF y asignando taxonomías del vocabulario controlado (`docs/taxonomias`), escribiéndolas en `datos/proyectos.proyecto_taxonomias`. Motor elegido: **solo LLM (Claude API)**. La llamada al modelo está aislada (inyectable) → todo el resto (prompt, parseo, validación, persistencia) se testea sin red: 14 chequeos OK con LLM falso.
- **Cómo:** `src/pdf_text.py` (baja PDF + extrae texto con pypdf; detecta escaneados→OCR pendiente) y `src/agente_taxonomias.py` (prompt con la lista controlada + reglas de frontera; parseo tolerante de JSON; **valida ids contra el vocabulario y descarta los inventados**; multi-etiqueta; fallback AUX.SINCLASIF + candidatos para revisión humana). Persistencia: **el humano gana** (no pisa taxonomías fuente='humano') y re-clasificar no duplica. Config: `ANTHROPIC_API_KEY`, `TAXO_MODEL` (default claude-haiku-4-5-20251001; tarea acotada + validación de ids → Haiku alcanza). CLI: `probar <pdf>` / `clasificar <db> <denominador>`.
- **Archivos:** `variables/proyecto/{src/agente_taxonomias.py, src/pdf_text.py, src/requirements.txt, tests/test_agente.py, README.md}`.
- **Estado del módulo:** variables/proyecto EN CURSO (agente listo; falta corrida en vivo con API key).
- **Próximo paso:** correr en vivo sobre PDFs reales; OCR para escaneados; conectar el flujo completo seguimiento→proyectos→agente en lote; clasificar la historia vía expedientes.

### [2026-06-29] docs/taxonomias — Documento controlado de taxonomías (con id estable)
- **Quién:** Claude (con Valle)
- **Qué:** vocabulario controlado único de temas de PdL, construido sobre la v1 de `variables/proyecto` y ampliado con ejemplos de Valle (IA, ciberseguridad, software, subsidios energéticos/transporte). 16 áreas + ~55 subtemas + 3 auxiliares = **74 ids**. Cada taxonomía tiene **id estable** (`ECON.TRIB`) que no cambia aunque se renombre. Multi-etiqueta. El agente elegirá solo de esta lista y propondrá candidatos sin inventar ids. Supersede a `variables/proyecto/TAXONOMIA.md` (queda como apunte).
- **Cómo:** `docs/taxonomias/taxonomias.json` (fuente de verdad) + `TAXONOMIAS.md` (vista humana + gobernanza: cómo agregar/quitar/editar, reglas de frontera) + `loader.py` (cargar/validar ids únicos/lista para el prompt del agente). Test: 7 chequeos OK (`python test_loader.py`). Reglas de frontera conservadas: ludopatía→SALUD.ADICC; códigos de fondo→JUST.*.
- **Archivos:** `docs/taxonomias/{taxonomias.json, TAXONOMIAS.md, loader.py, test_loader.py}`, `variables/proyecto/TAXONOMIA.md` (puntero).
- **Estado del módulo:** docs/taxonomias HECHO (v1 lista para usar y editar).
- **Próximo paso:** el **agente de taxonomías**: lee el PDF del proyecto + este JSON y escribe en `datos/proyectos.proyecto_taxonomias`.

### [2026-06-29] datos/proyectos — Base de Proyectos de Ley (SQLite) + export a Excel
- **Quién:** Claude (con Valle)
- **Qué:** módulo nuevo `datos/proyectos`: la base de PdL, fuente de verdad del embudo. Guarda una fila por proyecto (PK = denominador) + tablas hijas (autores, giros, trámite, taxonomías). Consume la salida de `datos/seguimiento` (dict FichaExpediente; no importa su código, respeta el contrato). Upsert idempotente: re-cargar un proyecto no duplica, actualiza estado/giros/autores/trámite y preserva `creado_en`. Las taxonomías (que llena el agente) sobreviven al re-scrape. Export a Excel legible para consultoría. Test sin red: 18 chequeos OK.
- **Cómo:** `src/schema.sql` (SQLite, FKs ON DELETE CASCADE, índices) + `src/store.py` (conectar/upsert_proyecto/export_excel/export_csv + CLI init|cargar|export|csv). **Export universal sin separadores en celdas:** Excel con una hoja por tabla (Proyectos/Autores/Giros/Tramite/Taxonomias) y CSV (utf-8-sig) por tabla, todo unido por denominador. Estado = el derivado por seguimiento (ingresado→en_comision→con_dictamen→media_sancion→sancionado / rechazado).
- **Archivos:** `datos/proyectos/{README.md, src/schema.sql, src/store.py, src/requirements.txt, tests/test_store.py}`.
- **Estado del módulo:** datos/proyectos EN CURSO.
- **Próximo paso:** conectar el flujo seguimiento→upsert en lote; agente de taxonomías que llene `proyecto_taxonomias`; decidir versionado del .db (no commitear binario).

### [2026-06-29] datos/seguimiento — Extractor de giros/trámite de PdL (Diputados + Senado)
- **Quién:** Claude (con Valle)
- **Qué:** módulo nuevo `datos/seguimiento`: dado un expediente conocido, baja su ficha oficial y extrae estado de avance (giros a comisiones, trámite, fechas, autores, link al PDF) a un objeto común `FichaExpediente`. Insumo del embudo. **Validado EN VIVO** contra las webs reales de ambas cámaras (Senado 1091/26 y Diputados 2832-D-2026): trae bien sumario, fecha, giros con orden/fecha, firmantes (Dip con distrito+bloque; Sen el autor por link al perfil) y PDF absoluto. Tests offline contra fixtures: todos pasan. Fuentes confirmadas jun-2026.
- **Cómo:** `src/giros.py`. Diputados = página del autor `hcdn.gov.ar/diputados/<slug>/proyecto.html?exp=<exp>` (requiere slug del autor). Senado = `senado.gob.ar/parlamentario/comisiones/verExp/<NRO>.<AA>/S/PL` (más completa, sin slug, trae orden de giro y fecha ingreso/egreso). Parsing defensivo por firma de encabezados de tabla; reintentos con backoff; denominador normalizado a NNNN-X-AAAA. Correr en vivo (PC con internet): `python src/giros.py senado 1091 2026` / `python src/giros.py diputados 2832-D-2026 sajmechet`. Test sin red: `python tests/test_giros.py`.
- **Archivos:** `datos/seguimiento/{README.md, src/giros.py, src/requirements.txt, tests/test_giros.py, tests/fixtures/*}`.
- **Estado del módulo:** datos/seguimiento EN CURSO.
- **Próximo paso:** validar selectores en vivo; plan B Diputados cuando el slug no resuelve; persistir a la base de Proyectos (módulo aparte); el slug del autor debe vivir en el dataset de parlamentarios.

### [2026-06-27] datos/decada_votada — Semilla vía CSV (sin R); base 2001-2025 completa
- **Quién:** Claude (con Franco)
- **Qué:** integrada la Década Votada desde el CSV local (Aportes/towlandia), Diputados 2001-2010 + Senado 2004-2014. La corrida de R no es necesaria (su test de 25 funcionó, pero el CSV es más rápido e incluye Senado). Base canónica: 4.584 actas / 780.839 votos, 2001-2025 ambas cámaras. Baseline Senado robusto: 0,971 (n=26.359).
- **Cómo:** `datos/decada_votada/src/from_csv.py`; voto 0/1/2/3 -> AFIRMATIVO/NEGATIVO/ABSTENCION/AUSENTE. Diputados recortado a <=2010 para no solapar con CKAN.
- **Archivos:** `datos/decada_votada/src/from_csv.py`, README, COBERTURA, RESULTADOS, EN-HUMANO.
- **Estado del módulo:** decada_votada HECHO (vía CSV).
- **Próximo paso:** hueco Senado 2015-2023; retro-completar bloque argentinadatos Senado 2024-25.

### [2026-06-27] datos/manual_2026 — Excel 2026 integrado; primer baseline de Senado
- **Quién:** Claude (con Franco)
- **Qué:** integrado el Excel curado (período 2025-2027) como fuente manual_2026: 17 actas (10 Dip + 7 Sen), votos 2026 de ambas cámaras + padrón con bloque del Senado. Canónica: 1.431 actas / 343.964 votos. Primer baseline de Senado: 0,938 disputadas (n=388).
- **Cómo:** `datos/manual_2026/src/to_canonical.py` (PRESIDENTE→ausente, PENDIENTE→excluido). Fixes de esquema: acta_id admite dígitos; fuente enum suma manual_2026; precedencia manual_2026=máxima.
- **Archivos:** `datos/manual_2026/*`, `docs/schemas/*`, `datos/canonica/src/build.py`, `datos/canonica/COBERTURA.md`, `evaluacion/baseline/RESULTADOS.md`.
- **Estado del módulo:** datos/manual_2026 HECHO; canonica EN CURSO.
- **Próximo paso:** retro-completar bloque Senado 2024-25 con el padrón; sumar la semilla (R) cuando termine.

### [2026-06-27] variables/proyecto — Clasificador sobre texto de leyes (validado 13/15)
- **Quién:** Claude (con Franco)
- **Qué:** taxonomía granular v1 aprobada (16 áreas/~55 subtemas). Clasificador por puntaje sobre el TEXTO de los proyectos (18 PDFs), validado contra las etiquetas de Franco: 13/15 en el mismo grupo temático. 2 casos de frontera (ludopatía, sociedades). 2 PDFs escaneados → OCR pendiente.
- **Cómo:** `classify_tema_v1.py` cuenta keywords por subtema sobre texto extraído con pdftotext. Reforzado el detector de Sociedades.
- **Archivos:** `variables/proyecto/{src/classify_tema_v1.py,TAXONOMIA.md,RESULTADOS-tema.md}`.
- **Estado del módulo:** EN CURSO. Próximo: OCR, integrar Excel 2026 como fuente, clasificar historia vía expedientes.
- **Próximo paso:** definir 2 fronteras con Franco; integrar datos/manual_2026.

### [2026-06-27] variables/proyecto — Clasificación por tema v0 (esqueleto)
- **Quién:** Claude (con Franco)
- **Qué:** taxonomía base (15 materias + trámite/homenajes/sin clasificar) y clasificador v0 por palabras clave. Sobre los títulos actuales: 65pct trámite, 24pct sin clasificar -> confirma que hace falta el texto del expediente.
- **Cómo:** reglas regex en `classify_tema.py`; el acta ya tiene el nº de expediente para unir con datos/expedientes.
- **Archivos:** `variables/proyecto/{src/classify_tema.py,TAXONOMIA.md}`.
- **Estado del módulo:** EN CURSO (v0). Depende de `datos/expedientes` para texto descriptivo.
- **Próximo paso:** que Franco confirme/ajuste la taxonomía; luego ingestar expedientes y clasificar sobre su texto.


### [2026-06-27] evaluacion/baseline — Baseline re-medido sobre canónica (2011–2025)
- **Quién:** Claude (con Franco)
- **Qué:** baseline votá-con-tu-grupo sobre la base ampliada. bloque_norm 0,969 (disputadas) — confirma callejón sin salida del voto-dirección. Coalición/linaje caen a ~0,92 (disidencia intra-coalición = señal). DRIFT: 2024–2025 baja a 0,946/0,923. Senado sin medir (SIN BLOQUE).
- **Cómo:** LOO sobre votos_resuelto; por nivel/cámara/año. `evaluacion/baseline/src/baseline_canonico.py`.
- **Archivos:** `evaluacion/baseline/{src/baseline_canonico.py,RESULTADOS.md,outputs/baseline_canonico.json}`.
- **Estado del módulo:** evaluacion/baseline HECHO (sobre canónica).
- **Próximo paso:** clasificación por tema (variables/proyecto); resolver bloque del Senado para medir su baseline.

### [2026-06-27] datos/senado — Hallazgo: diarios 2001–2003 sin voto nominal (pendiente)
- **Quién:** Claude (con Franco)
- **Qué:** revisada una muestra de diario de sesiones del Senado (2002). Son HTML (taquigráfico) con .pdf mal puesto. Tienen asistencia (PRESENTES/AUSENTES) y resultados agregados, pero NO voto nominal por senador (votación a mano alzada). Decisión de uso: pendiente.
- **Cómo:** detalle, ejemplo y notas de parsing en `datos/senado/NOTA-2001-2003.md`; muestra guardada en `datos/senado/muestras/`.
- **Archivos:** `datos/senado/NOTA-2001-2003.md`, `datos/senado/muestras/Senado_2002-03-05_muestra.html`.
- **Estado del módulo:** ANOTADO, sin parser todavía.
- **Próximo paso:** decidir entre asistencia+resultados / solo resultados / dejarlo. Senado nominal sigue arrancando en 2004 (semilla).

### [2026-06-25] datos/canonica — Capa de coaliciones (JxC time-aware)
- **Quién:** Claude (con decisiones de Franco)
- **Qué:** agregado el campo `coalicion`: Juntos por el Cambio/Cambiemos (UCR+PRO+CC+Evolución Radical) acotado 2015-12-10→2023-12-10 (53.768 votos); fuera de ventana los miembros vuelven a su espacio. Control: JxC arranca en 2016, sin anacronismo.
- **Cómo:** regla por rango de fechas en `entity_resolution.py`; unificadas variantes de Coalición Cívica por prefijo. Flags (aliados provinciales, PRO-LLA 2024–2025) en `BLOQUES.md`.
- **Archivos:** `datos/canonica/src/entity_resolution.py`, `datos/canonica/BLOQUES.md`.
- **Estado del módulo:** canonica EN CURSO.
- **Próximo paso:** sumar semilla y re-correr todo; tema (variables/proyecto); Senado por PDF.

### [2026-06-25] datos/canonica — Linaje time-aware + tema en agenda
- **Quién:** Claude (con decisiones de Franco)
- **Qué:** finalizado bloque_linaje (8 grupos): aliados K (Peronismo para la Victoria, Nuevo Encuentro, Libres del Sur) fundidos en FdT-UxP; Frente Renovador time-aware (massismo hasta 2019-12-10, kirchnerismo después). Registrado que falta separación por TEMA del proyecto.
- **Cómo:** mapas + regla por fecha en `entity_resolution.py`; join de fecha desde actas. Detalle y banderas en `BLOQUES.md`.
- **Archivos:** `datos/canonica/src/entity_resolution.py`, `datos/canonica/BLOQUES.md`, `variables/proyecto/README.md`.
- **Estado del módulo:** canonica EN CURSO.
- **Próximo paso:** tema (variables/proyecto), JxC por ventanas, Senado por PDF, sumar semilla.

### [2026-06-25] datos/canonica — Agrupamiento de bloques (norm + linaje)
- **Quién:** Claude (sesión con Franco)
- **Qué:** ampliada la resolución de bloques en dos niveles: `bloque_norm` (166→143, variantes del mismo bloque) y `bloque_linaje` (7 espacios; FpV/FdT/UxP unificados = 116.635 votos). `bloque` crudo intacto.
- **Cómo:** mapas curados `BLOQUE_ALIAS` y `LINAJE` en `entity_resolution.py`; decisiones y exclusiones (Frente Renovador, JxC time-dependent) documentadas en `BLOQUES.md`.
- **Archivos:** `datos/canonica/src/entity_resolution.py`, `datos/canonica/BLOQUES.md`.
- **Estado del módulo:** EN CURSO.
- **Próximo paso:** mapeo temporal de coaliciones (JxC); ampliar alias con la semilla cuando entre.

### [2026-06-25] datos/canonica — Resolución de entidades (1er pase)
- **Quién:** Claude (sesión con Franco)
- **Qué:** `entity_resolution.py` asigna un legislador_id canónico invariante al formato del nombre y normaliza bloques. Sobre CKAN+argentinadatos: 1.358 nombres → 1.131 legisladores; 225 unidos cross-fuente; bloques 166→148.
- **Cómo:** clave por tokens ordenados/únicos sin partículas (une "APELLIDO Nombre" y "Apellido, Nombre"); alias de bloque ampliable. Crosswalks a `Archivos_Borrar/`.
- **Archivos:** `datos/canonica/src/entity_resolution.py`.
- **Estado del módulo:** EN CURSO. Limitación: nombres con 2º nombre presente en una sola fuente no se unen (a refinar con padrón/fuzzy); alias de bloque a ampliar.
- **Próximo paso:** refinar con el padrón de Diputados; sumar la semilla cuando esté; ampliar alias de bloque.

### [2026-06-25] datos/argentinadatos + ckan_diputados — Cobertura 2011–2025
- **Quién:** Claude (sesión con Franco)
- **Qué:** integrado argentinadatos (Diputados 2020–2025, Senado 2024–2025) a la canónica y sumado el recurso CKAN período 137 para tapar 2019. Base: 1.414 actas, 340.892 votos.
- **Cómo:** bloque de Diputados resuelto cruzando el padrón (`periodoBloque` por fecha); Senado sin bloque en el detalle → "SIN BLOQUE" (a resolver). Reproducir: correr los dos `to_canonical.py` y `build.py`.
- **Archivos:** `datos/argentinadatos/src/to_canonical.py`, `datos/ckan_diputados/src/to_canonical.py`, `datos/canonica/COBERTURA.md`, `docs/schemas/acta.schema.json` (fecha pasó a opcional).
- **Estado del módulo:** argentinadatos EN CURSO (falta bloque Senado); canonica EN CURSO (2 fuentes).
- **Próximo paso:** semilla (pre-2011 y Senado 2004–2013), Diputados 2020–2023 oficial, Senado 2014–2023, entity resolution.

### [2026-06-25] datos/canonica + datos/ckan_diputados — Base canónica corriendo con CKAN
- **Quién:** Claude (sesión con Franco)
- **Qué:** CKAN Diputados normalizado al esquema canónico y base canónica construida y validada: 899 actas, 230.938 votos.
- **Cómo:** `datos/ckan_diputados/src/to_canonical.py` baja y traduce; `datos/canonica/src/build.py` une, deduplica (precedencia oficial>agregador>semilla), chequea FK y valida contra json-schema. Reproducir: correr to_canonical.py y luego build.py (deps en `datos/canonica/src/requirements.txt`).
- **Archivos:** `datos/ckan_diputados/src/to_canonical.py`, `datos/canonica/src/{build.py,requirements.txt}`.
- **Estado del módulo:** ckan_diputados→canónico HECHO; datos/canonica EN CURSO (corre con 1 fuente).
- **Próximo paso:** sumar la semilla (export R) y argentinadatos; resolución de entidades legislador/bloque.

### [2026-06-25] coordinacion/EN-HUMANO — Régimen de explicación en humano
- **Quién:** Claude (sesión con Franco)
- **Qué:** se creó `coordinacion/EN-HUMANO.md` (documento vivo que explica el sistema sin tecnicismos) y se volvió regla en `CLAUDE.md`: cada cambio se cuenta también en humano.
- **Cómo:** doc con analogías (semilla/huerta/bot, estaciones de cocina, idioma común). Se actualiza en cada cambio junto con este ESTADO.
- **Archivos:** `coordinacion/EN-HUMANO.md`, `CLAUDE.md`.
- **Estado del módulo:** HECHO (parte del régimen de trabajo).
- **Próximo paso:** mantenerlo actualizado en cada cambio.

### [2026-06-25] docs/schemas + datos/decada_votada — Esquema canónico v1 y export de la semilla
- **Quién:** Claude (sesión con Franco)
- **Qué:** definido el esquema canónico (schema_version=1) con tablas `acta` y `voto` + enum de voto; escrito `export_seed.R` que vuelca la semilla de Andy Tow (legislAr) al esquema canónico. Adoptado el régimen `Archivos_Borrar/` para descartables.
- **Cómo:** `docs/schemas/{README.md,acta.schema.json,voto.schema.json}`. El script R instala deps, itera `show_available_bills` → `get_bill_votes` por cámara, normaliza voto y escribe parquet. Correr local: `Rscript datos/decada_votada/export_seed.R 25` (prueba) o sin arg (completo).
- **Archivos:** `docs/schemas/*`, `datos/decada_votada/export_seed.R`, `Archivos_Borrar/README.md`, `CLAUDE.md`.
- **Estado del módulo:** docs/schemas HECHO; datos/decada_votada EN CURSO (falta correr el export en R).
- **Próximo paso:** correr el export, validar parquet contra schema, y arrancar `datos/canonica` (merge/dedup).

### [2026-06-25] datos — Estrategia semilla → canónica → bot (aportes Andy Tow)
- **Quién:** Claude (sesión con Franco)
- **Qué:** revisados los "Aportes sobre dataset congreso" (legislAr + Década Votada/towlandia). Andy Tow = semilla histórica de un solo uso; base canónica propia (`datos/canonica`) + bot (`datos/bot_recoleccion`). No se copia ni se depende en vivo.
- **Cómo:** legislAr (R) exporta parquet una vez; canónica unifica/deduplica/resuelve entidades; bot hace upsert idempotente. Límite R↔Python y cobertura en ADR-0002.
- **Archivos:** `datos/decada_votada/`, `datos/canonica/`, `datos/bot_recoleccion/`, `coordinacion/DECISIONES/0002-*.md`, `TABLERO.md`, `PLAN-DE-TRABAJO.md`, `CLAUDE.md`.
- **Estado del módulo:** los tres nuevos en PENDIENTE/EN CURSO.
- **Próximo paso:** schema + export (hecho); luego canónica.

### [2026-06-25] coordinacion — Estructura para trabajo en paralelo
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** estructura de carpetas por variable/módulo + documentos de coordinación (CLAUDE.md, PLAN, ESTADO, TABLERO, PROTOCOLO-GIT, ADR-0001).
- **Cómo:** monorepo, un módulo por unidad de trabajo; regla "un módulo, un dueño, una rama".
- **Archivos:** `CLAUDE.md`, `coordinacion/*`, `datos/*`, `variables/*`, `modelo/*`, `evaluacion/*`, `producto/*`, `docs/schemas/`.
- **Estado del módulo:** HECHO.
- **Próximo paso:** elegir prioridad de Fase 1 y reclamar módulos.

### [2026-06-25] evaluacion/baseline — Gate de Fase 0 medido
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** baseline "votá con tu bloque" sobre 231k votos (CKAN Diputados 2011–2020). Dirección sustantiva ≈ 0,989 (todas) / 0,984 (disputadas); 4 clases ≈ 0,807 / 0,820.
- **Cómo:** leave-one-out por bloque; corte disputadas = minoría ≥10%. Reproducir: `python fase0/src/ingesta.py && python fase0/src/baseline_bloque.py`.
- **Archivos:** `fase0/src/*`, `fase0/outputs/baseline_resultados.*`.
- **Estado del módulo:** HECHO. Redirige el producto a asistencia/embudo/posición de bloque.
- **Próximo paso:** migrar a `datos/ckan_diputados/` y `evaluacion/baseline/`.

### [2026-06-25] (análisis) — Validación crítica + premortem v2
- **Quién:** Claude (sesión inicial con Franco)
- **Qué:** validación de afirmaciones del estudio de viabilidad; premortem a 11 modos; informe Word.
- **Cómo:** WebSearch + inspección de fuentes. Hallazgo: CKAN de votaciones congelado en 2020.
- **Archivos:** `docs/contexto/Nowcast-Congreso_informe_validacion.docx`, `docs/contexto/premortem-*-validado.*`.
- **Estado del módulo:** HECHO (documentación).
- **Próximo paso:** ninguno; insumo para el plan.
