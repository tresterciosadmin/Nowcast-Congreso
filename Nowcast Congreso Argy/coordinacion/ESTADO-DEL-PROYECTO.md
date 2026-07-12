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
| datos/bot_recoleccion | EN CURSO (adaptador DAE Senado listo; TP Diputados en exploración) | Claude+Franco |
| datos/ckan_diputados | HECHO (en `fase0/`, migrar) | — |
| datos/argentinadatos | HECHO (bloque Senado 24-25 resuelto vía padrón; queda sin_bloque menor en Dip) | Claude+Franco |
| datos/senado | HECHO (2015–2023: 749 actas / 53.910 votos, bloque histórico 100%; padrón con filas REVISAR) | Claude+Franco |
| datos/seguimiento | EN CURSO (extractor de giros Dip+Sen, validado en vivo) | Valle |
| datos/proyectos | EN CURSO (base SQLite + export Excel) | Valle |
| docs/taxonomias | HECHO (vocabulario controlado v1, 74 ids) | Valle |
| datos/expedientes | EN CURSO (backfill CKAN 112.793 proyectos 2008-2026; embudo bruto 3,22%) | Claude+Franco |
| datos/licencias_suspensiones | PENDIENTE (nuevo — registro+notificador; decisión ADR-0004) | — |
| datos/export | EN CURSO (SQLite + Excel por gobierno; disputada = ±5% de emitidos vs umbral) | Valle |
| variables/legislador | EN CURSO (ficha + por período; PorTema bloqueada por taxonomías) | Valle |
| variables/proyecto | EN CURSO (vocabulario validado; ICG vivo; origen+líder por proyecto listos; falta batch del agente/tema) | Valle |
| variables/bloque | PENDIENTE | — |
| variables/asistencia_quorum | PENDIENTE (prioritario) | — |
| variables/embudo | EN CURSO (v1 GATE APROBADO: skill 0,34-0,39; segmentación origen/líder enchufada; falta tema) | Valle |
| variables/contexto | FUTURO | — |
| modelo/voto_individual | EN CURSO (desvío v2 = indisciplina total, ADR-0004) | Valle |
| modelo/agregador_institucional | PENDIENTE | — |
| modelo/ensemble | EN CURSO (v1: composición P(aprob)=P(llega)×P(mayoría) + nowcast por proyecto; falta posición de bloque proyectada) | Valle |
| evaluacion/baseline | HECHO | — |
| evaluacion/backtesting | PENDIENTE | — |
| evaluacion/metricas | PENDIENTE | — |
| producto/dashboard | PENDIENTE | — |
| producto/api | FUTURO | — |

---

## Bitácora (más reciente arriba)
### [2026-07-12] variables/proyecto + variables/embudo — Segmentación por TIPO de proyecto: origen (ejecutivo/oficialismo/oposición) + liderazgo
- **Quién:** Claude (con Valle)
- **Qué:** punto de fondo de Valle — no juega el mismo torneo un proyecto del Poder Ejecutivo, uno de un jefe de bloque oficialista o uno de un diputado de a pie de la oposición. Se construyó el rasgo de tipo de proyecto (feature store paso 2). `variables/proyecto/src/origen_lider.py` produce `data/features_proyecto.parquet` con: **origen** ∈ {EJECUTIVO (tipo MENSAJE), OFICIALISMO, OPOSICION, DESCONOCIDO} — cruzando **autor → bloque (contrato de `variables/legislador`: `legislador_bloques`) → fecha → linaje** contra la regla de quién gobernaba (CFK ≤2015 · Macri 2015-19 · A.Fernández 2019-23 · Milei ≥2023); y **lider** = jefe de bloque (`data/jefes_bloque.csv` CURADO) OR presidente de comisión (de `comisiones_integrantes`, defensivo si trae el rol) OR **alto productor** (nº de leyes sancionadas de su autoría en años ESTRICTAMENTE previos — walk-forward, sin leakage). El embudo ya lo **absorbe**: mergea origen/lider al cohorte, saca `embudo_por_origen.csv` y `embudo_por_lider.csv` (mide el efecto por segmento) y agrega los rasgos `origen_{ejecutivo,oficialismo,oposicion}` y `lider` al modelo de supervivencia.
- **Cómo:** normalización de nombres defensiva ('APELLIDO, Nombre' → 'APELLIDO NOMBRE', sin acentos) para el cruce autor↔legislador; oficialismo por ventana de fecha sobre el LINAJE (no el nombre de bloque). Tests offline sintéticos: **origen_lider 16 OK** (regla de gobierno por fecha, EJECUTIVO por MENSAJE, oficialismo/oposición por época, alto productor sin leakage, jefe curado) + **smoke del embudo segmentado OK** (por_origen/por_lider + rasgos nuevos en el modelo). *No testeado contra datos reales acá* (parquets en disco de Valle): falta corrida local. *Protocolo:* código vía bash, tests desde `/tmp`.
- **⚠️ NOTA PARA EL CLAUDE DE FRANCO (pedido de Valle):** la definición de **"líder parlamentario"** es PROVISORIA (jefe de bloque + pdte de comisión + alto productor). Revisar y validar el criterio más adelante, y **completar `variables/proyecto/data/jefes_bloque.csv`** (hoy es una semilla mínima de ~6 nombres de alta confianza; el roster histórico de jefes de bloque 2008-2026 no existe y hay que armarlo). También verificar si `comisiones_integrantes` trae el rol de presidente (si no, esa señal queda en 0).
- **Archivos:** `variables/proyecto/{src/origen_lider.py, data/jefes_bloque.csv, tests/test_origen_lider.py}`, `variables/embudo/src/embudo.py` (hook origen/lider + segmentación), `coordinacion/{TABLERO.md, ESTADO, EN-HUMANO}`, `tablero_datos.js`.
- **Estado del módulo:** variables/proyecto EN CURSO (origen+lider listos, falta corrida local + el tema del agente); variables/embudo EN CURSO (segmentación enchufada).
- **Próximo paso:** Valle corre `python variables\proyecto\src\origen_lider.py` (verificar el % de match autor→bloque y el reparto de origen) y luego `python variables\embudo\src\embudo.py all` — mirar `embudo_por_origen.csv` (¿los del PE y oficialismo sobreviven más?) y si el skill del modelo sube con los rasgos nuevos.
- **RESULTADO 1ª corrida (Valle) + FIX:** el **match autor→bloque salió 96,1%** (muy bueno). Pero el origen dio 95% OPOSICION / 3% oficialismo (implausible): el diagnóstico mostró que los `linaje` del padrón traen nombres largos/con sufijo ("FdT-UxP **(kirchnerismo)**", "RADICALISMO", "COALICION CIVICA", "LA LIBERTAD AVANZA") y la regla hacía match EXACTO → solo "PRO" coincidía, y todo el kirchnerismo (13.876 proyectos, el linaje mayor) caía mal en oposición. **Arreglado:** `_linaje_code()` mapea el linaje a un código robusto por palabras clave (KIRCHNERISMO/PRO/RADICALISMO/CC/LLA/…, orden PROGRESISMO antes que PRO) y `GOBIERNOS` usa esos códigos. Tests ampliados a **24 OK** (incluyen los strings reales del padrón). Falta **re-correr** origen_lider + embudo para el reparto de origen corregido. *Avisos esperados y documentados:* `pdte_comisión`=0 (comisiones_integrantes sin columna de rol) y `jefe de bloque`≈0 (semilla de 6 nombres); el líder hoy = alto productor (9,3%).
- **RESULTADO 2ª corrida (Valle) — el efecto es CONTUNDENTE:** origen corregido = **OFICIALISMO 11.503 (28%) / OPOSICION 27.617 (67%) / EJECUTIVO 716 / DESCONOCIDO 1.503**. **Embudo por origen (% sancionado): EJECUTIVO 75,6% · OFICIALISMO 3,68% · OPOSICION 1,17%** — un proyecto del PE se convierte en ley 65x más que uno de la oposición, y el corte se juega en el dictamen (PE 78,8% consigue dictamen vs 4,6% la oposición). **Embudo por líder: 14,2% (líder) vs 2,1% (común)** — 7x. Queda validada la tesis de Valle: el TIPO de proyecto (quién lo empuja) es determinante. **Fix técnico:** el backtest no usaba los rasgos nuevos (solo el scoreo final); ahora `backtest_temporal` acepta `feats_proy` y `cmd_modelo` reporta skill **SIN vs CON origen/líder** (leakage-safe: origen es point-in-time y alto_productor es walk-forward). **Mejora del modelo CON los rasgos (3ª corrida):** sanción skill 0,3424→**0,3691** (AUC 0,9576→0,9633); llega_recinto 0,3921→**0,412** (AUC 0,946→0,9524). Lift modesto pero real —el modelo ya capturaba parte vía `autor_tasa_hist`— y sobre todo suma **interpretabilidad** (ahora el nowcast explica *por qué*: proyecto del Ejecutivo/oficialista/líder). Tanda cerrada: origen+líder construidos, medidos (efecto 65x del PE) y enchufados al modelo con mejora verificada.

### [2026-07-12] modelo/ensemble — v1: el Nowcast end-to-end de un proyecto (embudo × agregador)
- **Quién:** Claude (con Valle)
- **Qué:** reclamado el módulo (dependencias cumplidas: embudo v1 + agregador) y cerrada la **composición final**: `P(aprobación) = P(llega al recinto) × P(mayoría | recinto)`. `ensemble.py` toma un `proyecto_id` (busca su `p_llega_recinto` en `variables/embudo/outputs/p_embudo.parquet`) y un **escenario de votación** (postura esperada + desvío por bloque), corre `simular_votacion` del agregador (función pública, sin tocar su código) y devuelve la **tarjeta de nowcast**: los dos factores, P(aprobación) y los afirmativos esperados con banda 5-95% + umbral. Es la **puesta en marcha**: por primera vez todas las piezas producen un número de aprobación para un proyecto concreto. Demo end-to-end: 12,0% (llega) × 58,1% (mayoría) = **7,0%** con la votación al filo (109,6 afirmativos vs umbral 109,4) — muestra el valor de descomponer (un proyecto puede tener mayoría probable pero baja chance de llegar al recinto).
- **Cómo:** composición como producto de los dos factores validados; expansión escenario-por-bloque → roster por legislador para el Monte Carlo del agregador. Se importa `simular_votacion` vía sys.path (contrato público del agregador; no se replica el motor). Parsing defensivo (líneas válidas, bancas>0, p_llega en [0,1], fallback embudo↔escenario). Tests offline SIN datos (escenarios sintéticos + p_llega override): **16 chequeos OK** (composición = producto, embudo como techo, monotonía, escenarios holgados a favor/en contra → P mayoría ~1/~0, banda, errores claros, demo). *Protocolo:* código vía bash, tests desde `/tmp` (mirror ensemble+agregador).
- **Archivos:** `modelo/ensemble/{src/ensemble.py, src/requirements.txt, tests/test_ensemble.py, README.md}`, `coordinacion/{TABLERO.md, ESTADO-DEL-PROYECTO.md, EN-HUMANO.md}`, `tablero_datos.js`.
- **Estado del módulo:** modelo/ensemble EN CURSO (v1 con tests; falta posición de bloque proyectada para calibrar la cadena completa sobre proyectos no votados).
- **Próximo paso:** Valle corre `python modelo\ensemble\src\ensemble.py demo` (y un `nowcast` con un proyecto real de `p_embudo` + escenario a mano). Después: módulo de **posición de bloque por tema** (proyecta la postura hoy puesta a mano) — es lo que falta para el nowcast automático de un proyecto no votado y para calibrar la cadena completa.

### [2026-07-12] variables/embudo — v1: embudo por etapas + modelo de supervivencia con backtest temporal
- **Quién:** Claude (con Valle)
- **Qué:** reclamado el módulo (dependencia cumplida: `datos/expedientes`) y construida la primera pieza del diferencial del nowcast. (1) **Caracterización del embudo por etapas** (`presentado→giro→dictamen→recinto→sanción`) con tasas absolutas y condicionales, abierta por año, cámara y **comisión** (cementerios vs. rápidas). (2) **Modelo de supervivencia v1** que estima `P(llega al recinto)` y `P(sanción)` por proyecto de ley con rasgos conocidos SOLO al momento de presentar (sin leakage): año/mes, cámara, nº de comisiones giradas, one-hot de comisiones frecuentes, año electoral y tasa histórica de éxito del autor (calculada solo sobre train). (3) **Backtest walk-forward** (entrena años<T, predice T) con Brier/AUC/calibración vs. baseline de tasa base. Contrato de salida `p_embudo.parquet` (proyecto_id, etapa_actual, p_llega_recinto, p_sancion) — lo que consumirá el ensemble.
- **Cómo:** regresión logística SIN `class_weight` balanceado (el balanceo mejora el ranking pero rompe la calibración; el nowcast necesita P reales). Caducidad (Ley 13.640) tratada con **cohortes maduras** (presentadas ≤ último_año−2) para no contar vivo como muerto; los inmaduros igual se scorean. Parsing defensivo del contrato de expedientes (columnas por nombre, tolerante a NA/archivos faltantes). Tests offline con fixture sintética que imita el esquema: **18 chequeos OK** (cohorte, embudo, features sin leakage, backtest AUC>0.5 y skill>0, scoring en [0,1]). Prueba de humo del CLI end-to-end OK. **Backtest a escala pendiente de corrida local** (Valle: lee ~40k proyectos de ley + entrena). *Protocolo:* código escrito vía bash (mount trunca Write/Edit), tests desde `/tmp`.
- **Archivos:** `variables/embudo/{src/embudo.py, src/requirements.txt, tests/test_embudo.py, README.md}`, `coordinacion/{TABLERO.md, ESTADO-DEL-PROYECTO.md, EN-HUMANO.md}`, `tablero_datos.js`.
- **Estado del módulo:** variables/embudo EN CURSO (v1 con tests; falta backtest a escala + enchufar tema/origen de `variables/proyecto`).
- **Próximo paso:** Valle corre `python variables\embudo\src\embudo.py all` y pega el embudo por etapas + skill del backtest para verificar el gate. Después: enchufar `origen` (oficialismo/oposición) y `tema` cuando `variables/proyecto` los publique; conectar `p_embudo` al ensemble.
- **RESULTADO de la corrida a escala (Valle, mismo día) — GATE APROBADO:** sobre los **41.339 proyectos de ley 2008-2026**. **Embudo por etapas:** el 100% se gira a comisión pero solo el **7,82% consigue dictamen** — ahí muere ~92% (confirma el patrón: no se rechaza, se deja sin dictamen). Superado ese cuello, la supervivencia es alta: recinto|dictamen 59,2%, sanción|recinto 69,3%. Absolutas: 4,63% llega al recinto, 3,21% se sanciona (coincide con el embudo bruto 3,22% de expedientes). **Backtest walk-forward (n=36.726 maduros):** target *sancionado* → Brier 0,0209 vs baseline 0,0318, **skill 0,342**, AUC 0,958; target *llega_recinto* → Brier 0,0272 vs 0,0447, **skill 0,392**, AUC 0,946. El gate ("supera la tasa base") se cumple holgado. *Caveat honesto:* el AUC altísimo se apoya en parte en la masa de proyectos "muertos al llegar" (fáciles de descartar con base 3,2%); el salto de calidad real vendrá al enchufar tema/origen. Salidas: `variables/embudo/outputs/{embudo_*.csv, backtest_embudo.json, p_embudo.parquet}` (41.339 proyectos scoreados).

### [2026-07-11] datos/bot_recoleccion — Adaptador TP Diputados: el bot quedó BICAMERAL (con cofirmantes completos)
- **Quién:** Claude (con Franco)
- **Qué:** segunda mitad del padrón vivo: `src/tp_diputados.py` lee el **Trámite Parlamentario** (`tp.html?periodo=P&numero=N`, secuencial por período parlamentario; el índice publica hasta el 144 actual e histórico desde el 137). Por proyecto extrae: **lista COMPLETA de firmantes (autor + cofirmantes — el dato que el CKAN no publica y que necesitan los Módulos B/C)**, tipo, sumario, expediente con link al PDF, sección (Diputados/PE/Senado) y giros. Parser validado contra dos TP reales (87: 13 proyectos; 1: 49 proyectos; cofirmantes separados correctamente incl. el "Y" final). Workflow de Actions actualizado: el bot corre AMBAS cámaras cada mañana. Bonus descubierto: el TP histórico por período habilita un futuro backfill de cofirmantes 2019→hoy.
- **Cómo:** parsing por markup real (h1 número+fecha castellano→ISO, h3 secciones, un <p> por proyecto con strongs antes/después del link como firmantes/giros); estado incremental por período con corte seguro si un TP falla (no avanza el puntero más allá de lo logrado). Fixture RECORTADA de la página real + **13 chequeos OK**. `.gitignore`: excepción para `tp_entradas.parquet`.
- **Archivos:** `datos/bot_recoleccion/{src/tp_diputados.py, tests/test_tp.py, tests/fixtures/tp_87_144.html, README.md}`, `.github/workflows/bot-diario.yml`, `.gitignore`, `tablero_datos.js`.
- **Estado del módulo:** datos/bot_recoleccion EN CURSO (ambas cámaras automatizadas; falta estreno en vivo del TP + upsert hacia datos/proyectos).
- **Próximo paso:** Franco corre `py datos\bot_recoleccion\src\tp_diputados.py` (estreno: ~87 TPs del período 144, unos minutos) y commitea todo; verificar el workflow manual en Actions; luego backfill TP 137-143 y fase votaciones.

### [2026-07-11] datos/bot_recoleccion — Estreno en vivo (1.004 expedientes) + el bot queda corriendo en GitHub Actions
- **Quién:** Claude (con Franco)
- **Qué:** (1) primera corrida real del adaptador DAE: **51 DAEs del 2026, 1.004 expedientes con giros y extracto en ~1 minuto**, memoria incremental funcionando (la próxima corrida trae solo lo nuevo). (2) **Decisión de Franco: el bot corre en GitHub Actions en el propio repo** — `.github/workflows/bot-diario.yml`: cron 07:00 ARG (lun-sáb) + disparo manual, corre `dae_senado.py` y commitea el parquet + estado solo si hay novedades (idempotente; `git pull --rebase` antes del push para no pisar a nadie). Excepciones nuevas en `.gitignore` (el parquet del bot y su estado SÍ se versionan: son la base viva). Es el ejecutor 24/7 interino hasta la Etapa 4. (3) URLs reales del Trámite Parlamentario de Diputados encontradas (`tramites-parlamentarios.html` + `www2.../tp_NNN.html`); `explorar_tp.py` corregido para la próxima corrida de Franco.
- **Cómo:** workflow con permissions contents:write, concurrency para no solaparse, timeout 20 min. Verificar el estreno: pestaña Actions → "Bot diario (padrón vivo)" → Run workflow → debe decir "Sin novedades" (Franco ya trajo todo hoy).
- **Archivos:** `.github/workflows/bot-diario.yml` (raíz del repo git), `.gitignore`, `datos/bot_recoleccion/{README.md, src/explorar_tp.py, data/clean/dae_entradas.parquet, data/estado_bot.json}`, `tablero_datos.js`.
- **Estado del módulo:** datos/bot_recoleccion EN CURSO (Senado AUTOMATIZADO; Diputados en exploración).
- **Próximo paso:** push + corrida manual del workflow para validar el runner (si el Senado bloqueara IPs de GitHub, se documenta y evalúa proxy/self-hosted); correr `explorar_tp.py` corregido; adaptador TP; upsert hacia datos/proyectos.

### [2026-07-11] datos/bot_recoleccion — Nace el bot diario (padrón vivo): adaptador DAE Senado listo
- **Quién:** Claude (con Franco)
- **Qué:** reclamado el módulo (su dependencia — canónica cargada — está cumplida) y construida la primera pieza del padrón vivo: `src/dae_senado.py` lee el **DAE Digital del Senado** (diario oficial de ingresos, verificado en vivo: tabla con expediente + GIROS + extracto, numeración secuencial 32/2026) recordando el último número visto en `data/estado_bot.json` y trayendo solo lo nuevo (idempotente, dedup por expediente+dae). Salida `data/clean/dae_entradas.parquet`. Estrategia confirmada del diseño: diarios oficiales (1 request/día) y NO páginas personales de diputados; firmantes vía el propio diario o la ficha verExp (contrato de seguimiento). Descubrimiento del camino descartado: el export JSON de "Asuntos Entrados" del Senado es solo un índice de PDFs (inútil); el DAE Digital es la fuente estructurada.
- **Cómo:** parsing por firma de encabezados; form POST del buscador con fallback a rutas GET; 4 directivas. Tests offline con fixture sintética del HTML real: **13 chequeos OK**. `src/explorar_tp.py` listo para explorar el Trámite Parlamentario de Diputados desde PC (el dominio hcdn no responde al entorno).
- **Archivos:** `datos/bot_recoleccion/{README.md, src/dae_senado.py, src/explorar_tp.py, src/requirements.txt, tests/test_dae.py, tests/fixtures/*}`, `coordinacion/TABLERO.md`, `tablero_datos.js`.
- **Estado del módulo:** datos/bot_recoleccion EN CURSO (Senado listo, falta corrida en vivo; Diputados en exploración).
- **Próximo paso:** Franco corre `dae_senado.py` en vivo + `explorar_tp.py`; con las muestras del TP se escribe el adaptador Diputados; después upsert hacia datos/proyectos (contrato Valle) y fase votaciones.

### [2026-07-11] datos/argentinadatos + datos/canonica — Bloque Senado 2024-25 retro-completado: SIN BLOQUE = 0
- **Quién:** Claude (con Franco)
- **Qué:** cerrada la deuda más vieja de la canónica. (1) `datos/argentinadatos` ahora resuelve el bloque del Senado consumiendo el **padrón versionado de datos/senado** (contrato publicado: manual > automático, clave de tokens + fallback por variantes, ventana por fecha): de 9.863 SIN BLOQUE a **0 en el Senado** (quedan 1.367 de Diputados, roster de la fuente, tema aparte). Para los 20 senadores que el anexo wiki 2023-25 omite se agregaron filas retro al padrón (+20, total 131): 12 proyectados desde el Excel 2026 de Franco **con corrección de época** (los peronistas van como UNIÓN POR LA PATRIA — "Justicialista" es rename 2026; Juez era FRENTE PRO antes de LLA; Vigo UNIDAD FEDERAL — "Provincias Unidas" es 2026) y 8 con mandato terminado en dic-2025 curados a mano (UC en su mayoría; Kueider con nota de suspensión; Ledesma con su clave-variante). (2) **Omisión de linajes corregida:** UNIDAD CIUDADANA y FRENTE NACIONAL Y POPULAR (sub-bloques FdT del padrón wiki) caían en OTRO → FdT-UxP; PERONISMO REPUBLICANO (Pichetto post-2019) → PERONISMO FEDERAL.
- **Cómo:** `_padron_senado()`/`_bloque_sen()` en `to_canonical.py` (lee los CSV del padrón, no toca código de datos/senado) + 3 entradas en LINAJE. Resultado en la base: baseline Senado +2.008 medibles (128.238), drift 2024-25 con más base (0,947/0,926, se sostiene), **OTRO/PROVINCIAL 17,4%** (vs. 45,5% pre-ADR-0005). *Incidente de entorno documentado:* una variable OUT heredada en la consola hizo que entity_resolution escribiera en `_sources/` y el baseline leyera parquet viejo (dos corridas idénticas byte a byte); limpiar env o consola nueva.
- **Archivos:** `datos/argentinadatos/src/to_canonical.py`, `datos/senado/data/padron_manual_2015_2017.csv` (+20), `datos/canonica/src/entity_resolution.py`, `coordinacion/*`, `tablero_datos.js`.
- **Estado del módulo:** datos/argentinadatos HECHO (bloque Senado resuelto); canonica EN CURSO (queda Dip 2020-23 y el sin_bloque menor de Diputados).
- **Próximo paso (para Valle):** re-correr disciplina/ficha/export — el Senado 2024-25 entra por primera vez al índice de desvío con bloques reales (era el período del drift, el más valioso). Nuestro siguiente: bot diario o embudo.

### [2026-07-11] datos/expedientes — Backfill CKAN corrido: 112.793 proyectos (2008-2026); EMBUDO BRUTO = 3,22%
- **Quién:** Claude (con Franco)
- **Qué:** módulo reclamado y backfill completo desde el CKAN de Diputados (7 datasets vivos + 1 congelado): **112.793 proyectos 2008-2026** con su cadena de vida completa (422.143 giros, 23.801 dictámenes, 140.903 movimientos, 117.026 resultados, 1.335 leyes) + integrantes de comisiones (Committee Overlap) + **enlace acta→expediente oficial** (89,1% de las actas CKAN de la canónica matcheadas). Primer número del embudo: **de 41.339 proyectos de ley presentados, 1.332 sancionados = 3,22%**, y SOLO 4 rechazados explícitos en 18 años — el Congreso no rechaza, deja morir: eso es exactamente lo que variables/embudo va a modelar. Limitación: `autor` = firmante primario (el CKAN no publica cofirmantes).
- **Cómo:** `src/explorar_ckan.py` (paso 0: inventario + muestras para diseñar sobre estructura real) y `src/ingesta_ckan.py` (descarga con caché/backoff → 8 parquet de contrato en `data/clean/`). Corrida y verificación en PC de Franco. Detalle en el README del módulo.
- **Archivos:** `datos/expedientes/{README.md, src/explorar_ckan.py, src/ingesta_ckan.py}`, `coordinacion/{TABLERO.md, ESTADO, EN-HUMANO}`, `tablero_datos.js`.
- **Estado del módulo:** datos/expedientes EN CURSO (backfill hecho; fase 2 = cofirmantes + origen Senado).
- **Próximo paso — DISEÑO DEL BOT DIARIO ANOTADO (idea de Franco, no perder):** para el padrón vivo, el bot NO debe scrapear las páginas personales de los diputados (257 requests/día + slugs frágiles) sino los **diarios oficiales de ingreso: Trámite Parlamentario (Diputados) y DAE (Senado)** — todo lo presentado cada día con TODOS los firmantes y giros en un solo documento; la ficha de `datos/seguimiento` (Valle) como fallback puntual, consumiendo su contrato. Vive en `datos/bot_recoleccion` (dependencia ya cumplida) y de paso trae las votaciones nuevas. Candidato natural a próximo claim. Para variables/embudo: el insumo ya está servido.

### [2026-07-11] datos/senado — Auditoría del padrón de bloques COMPLETA: 17/17 filas validadas, cero errores
- **Quién:** Claude (con Franco)
- **Qué:** cerrado el caveat del gate 1 de voto_individual. Las 17 filas `REVISAR` del padrón manual del Senado se auditaron comparando la conducta de cada senador contra la línea de su bloque asignado en su ventana: 14 con desvío ≤5,6% (etiqueta trivialmente correcta, incl. Rodríguez→UC y los FNyP pre-Unidad Federal) y 3 casos con desvío alto que resultaron **SEÑAL POLÍTICA REAL, no error**: García (33,9% contra línea) desvía igual que TODA el ala cristinista del FpV-PJ 2016-17 (F. Sagasti 36,7%, Pilatti Vergara 38,4%, Almirón 34,4%) en las leyes calientes de la era (reforma previsional, capital emprendedor, resp. penal empresaria — el ala K votando NO mientras la mayoría de Pichetto acompañaba); Espínola 10,7% = disidencia leve de peronista dialoguista (aclarado: Camau ES senador desde 2015, no 2017). **El ranking de díscolos del equipo queda certificado: mide fracturas reales de bloque.**
- **Cómo:** barrido contra `votos_resuelto.parquet` (línea = mayoría A/N del bloque por acta; % de votos emitidos contra línea por senador-ventana). Notas del CSV actualizadas de REVISAR → AUDITADO con el detalle.
- **Archivos:** `datos/senado/data/padron_manual_2015_2017.csv` (notas), `coordinacion/{ESTADO,EN-HUMANO,TABLERO}`, `tablero_datos.js`.
- **Estado del módulo:** datos/senado HECHO (padrón auditado al 100%).
- **Próximo paso (para Valle):** el caveat "auditar etiquetas de los top díscolos" del gate 1 puede darse por cerrado en el Senado 2015-23; García y las camporistas son díscolas legítimas del período. Nuestro siguiente frente: datos/expedientes.

### [2026-07-11] variables/proyecto — Vocabulario VALIDADO con muestra manual + ingesta ICG Di Tella lista
- **Quién:** Claude (con Valle)
- **Qué:** ejecutados los pasos 1 y 3 del orden del feature store. (1) **Validación manual del vocabulario** (decisión de Valle: muestra a mano antes de gastar en batch): 88 actas de la canónica (estratificadas por año 2001-2025) clasificadas a mano contra los 74 ids. Resultado: **el vocabulario funciona** — 82% clasificable por título, 89% de ellas con confianza alta/media, 22% multi-etiqueta; la regla juego→SALUD.ADICC aplicó perfecto. Hallazgos: 18% de actas NO clasificables por título (opacos del CKAN + procedimentales) → para la historia hará falta el enlace acta→expediente o etiqueta `_PROCEDIMENTAL`; 5 huecos candidatos (control parlamentario, bienes del Estado, sistema financiero, biodiversidad, federalismo) y 4 fronteras a fijar (detalle en `variables/proyecto/RESULTADOS-muestra-manual.md`). (2) **Ingesta ICG Di Tella** (`src/ingesta_icg.py`): no hay API; el script scrapea la página oficial de descarga de UTDT (el `fname` del Excel de la serie mensual 2001-presente ROTA cada mes) y normaliza a `data/icg_mensual.csv` (fecha/anio/mes/icg, escala 0-5); fallback a los microdatos `.dta` espejados por PoliticaArgentina/data_warehouse (mecanismo tomado de `opinAr`, punta de Valle). Tests offline 9 chequeos OK (layouts largo/ancho/meses-texto/encabezado desplazado + limpieza defensiva).
- **Cómo:** muestra: filtro de títulos informativos sobre `congreso.db` + clasificación manual (queda como set de referencia agente-vs-humano). ICG: 4 directivas de resiliencia; crudos a `datos/Archivos_Borrar/icg_utdt/`. Corrida real en PC de Valle: `python variables\proyecto\src\ingesta_icg.py` (valida los últimos 12 meses a ojo contra los informes UTDT: jun-26=2,07 / may-26=1,99).
- **Archivos:** `variables/proyecto/{RESULTADOS-muestra-manual.md, outputs/muestra_manual_taxonomias.csv, src/ingesta_icg.py, src/requirements.txt, tests/test_ingesta_icg.py, README.md}`, `coordinacion/ESTADO-DEL-PROYECTO.md`, `tablero_datos.js`.
- **Estado del módulo:** variables/proyecto EN CURSO (vocabulario validado; ICG con código listo, falta corrida local).
- **Próximo paso:** el equipo decide sobre los 5 huecos/4 fronteras del vocabulario (tocar `docs/taxonomias` es contrato compartido); después, agente en batch (API key) usando la muestra manual como referencia, y regla `origen` oficialismo/oposición (paso 2 del feature store).
- **RESULTADO de la corrida (Valle, mismo día) — bug encontrado y CERRADO:** la corrida local encontró el link vigente pero el parser no reconoció el layout real del Excel: es **TRANSPUESTO** (una fila de fechas y debajo la fila `ICG`, más una fila `Variación ICG`), partido en 2 hojas (2001-2022 / 2023-presente), con etiquetas de año como texto que confundían la detección de la fila de fechas. Fix: parser nuevo `_extraer_transpuesto` que exige datetimes NATIVOS del Excel (un string "2002" o un float también parsean como fecha y elegían la fila equivocada) + concatenación de hojas; de paso se recuperó la variante "año"→"ao" perdida en el escaneo de encabezados (la agarró la suite). Tests: **12 chequeos OK** (incl. regresión con el layout real sintético). Sobre el crudo cacheado de la corrida de Valle: **296 meses, nov-2001→jun-2026, 0 huecos**, cola validada exacta contra los informes UTDT (jun 2,07 / may 1,99 / abr 2,02 / mar 2,30). **`data/icg_mensual.csv` ya generado y versionable** — la familia E del feature store tiene su primera serie viva. *Nota entorno:* el mount del sandbox volvió a servir copias truncadas de los .py recién editados (mismo incidente que el agregador del 11-jul); los tests corrieron desde copia reconstruida; los archivos reales están completos.
- **AMPLIACIÓN (mismo día, pedido de Valle) — modo `ultimo`:** la página de INFORMES de UTDT publica el mes nuevo ANTES de que rote el Excel ("El ICG de junio fue de 2,07 puntos…"). Nuevo comando `python src/ingesta_icg.py ultimo`: scrapea esa página, parsea mes/año/valor del texto (soporta las DOS redacciones históricas — "El ICG de X fue de…" y "La medición de X del ICG fue de…" — y los encabezados con el año partido por negritas, visto en vivo en "Febrero 202/6") y AGREGA al CSV solo los meses faltantes. No pisa valores existentes (el informe redondea a 2 decimales; el Excel es más preciso) e IDEMPOTENTE (correr dos veces no duplica). Es la pieza invocable por el futuro bot mensual. Tests: suite ampliada a **21 chequeos OK** (fixture calcada de la página real + merge + idempotencia + regresión del Excel real: 296 meses).

### [2026-07-11] variables/proyecto — Diseño del FEATURE STORE por proyecto/votación (decisión de Valle)
- **Quién:** Claude (con Valle)
- **Qué:** tras el diagnóstico de asistencia (el promedio, aun individual, no sirve — la presencia es CONDICIONAL al proyecto), Valle decidió **pausar el escalón 2 de asistencia y avanzar primero con el agente/taxonomías y el feature store**, porque sin saber el tema y los rasgos de cada proyecto no se puede condicionar nada (ni asistencia, ni posición de bloque). Y eligió **diseñar el feature store en papel antes de recolectar**. Documento nuevo `variables/proyecto/FEATURE-STORE.md`: define las 6 familias de rasgos (A identidad/trámite, B tema/taxonomías, C autoría y **origen oficialismo/oposición**, D institucionales incl. afinidad de comisión y veto legal, E contexto temporal incl. **ICG Di Tella** y proximidad electoral, F derivadas CONDICIONADAS: posición de bloque por tema, presentismo condicionado, disciplina por tema), con fuente, disponibilidad y a qué etapa del modelo alimenta cada una. Dos unidades: `features_proyecto` (por denominador) y `features_votacion_bloque` (acta×bloque).
- **Cómo:** solo diseño (sin código). Aprovecha lo que ya existe: autores/giros/cámara de `datos/proyectos`+`seguimiento`, taxonomías (74 ids), cortes de gobierno de `datos/export`. Orden de construcción sugerido: (1) correr el agente de taxonomías [desbloqueo #1], (2) regla origen oficialismo/oposición por fecha, (3) ingesta ICG Di Tella (serie mensual UTDT), (4) derivadas condicionadas, (5) calendario electoral.
- **Archivos:** `variables/proyecto/FEATURE-STORE.md`, `coordinacion/{ESTADO-DEL-PROYECTO.md, TABLERO.md}`, `tablero_datos.js`.
- **Estado del módulo:** variables/proyecto EN CURSO (agente listo + diseño del feature store; falta correr el agente e implementar las features).
- **Próximo paso:** decidir cómo correr el agente de taxonomías (API key para batch, o clasificar una muestra a mano para validar el vocabulario) y arrancar por B (tema) → C (origen). Asistencia escalón 2 espera al feature store.

### [2026-07-11] variables/asistencia_quorum — Escalón 1: presentismo + modo asistencia del agregador (arreglo del sesgo pesimista)
- **Quién:** Claude (con Valle)
- **Qué:** reclamado el módulo y construido el **escalón 1**. (1) `asistencia.py`: presentismo por legislador (presente = emitió algo ≠ AUSENTE; global 74,7%), global + por período parlamentario; salidas `outputs/presentismo_legislador{,_periodo}.csv` (1.959 legisladores). (2) **modo asistencia en el agregador** (`backtest_asistencia`): la línea deja de ser "mayoría incluyendo ausentes" y pasa a ser la **DIRECCIÓN del bloque entre presentes** (`_direccion_bloque_por_acta`), y cada legislador emite según su **presentismo histórico** (`simular_votacion(p_presente=...)`). Esto ataca la causa del sesgo pesimista detectado en el backtest del 10-jul (el motor daba por perdidas votaciones peleadas que se aprobaban, porque contaba ausentes como "no acompaña" y borraba afirmativos reales).
- **Cómo:** validado en unidad (7 chequeos nuevos, total 26): en una votación mal asistida que se aprueba (70 sí presentes / 80 ausentes en el bloque + 60 no), el motor viejo predice **P=0,00** (línea del bloque = NO_ACOMPANA) y el modo asistencia **P=0,54** (dirección AFIRMATIVO + presentismo recupera los 70 afirmativos). **Backtest histórico completo pendiente de corrida local** (Valle) para cuantificar la mejora de calibración vs. el Brier 0,011 pesimista actual. *Nota entorno:* el mount del sandbox truncó repetido el `agregador.py`/tests recién editados (latencia host→VM); los tests se corrieron importando el módulo desde una copia; el archivo real está completo (lo corre Valle local).
- **Archivos:** `variables/asistencia_quorum/{src/asistencia.py, README.md, outputs/*}`, `modelo/agregador_institucional/{src/agregador.py, tests/test_agregador.py}`, `coordinacion/{TABLERO.md, ESTADO-DEL-PROYECTO.md}`, `tablero_datos.js`.
- **Estado del módulo:** variables/asistencia_quorum EN CURSO (escalón 1 hecho, falta backtest a escala); modelo/agregador_institucional EN CURSO (modo asistencia agregado).
- **Próximo paso:** Valle corre `python modelo\agregador_institucional\src\agregador.py backtest_asistencia` y me pega el resumen; comparamos calibración vs. el backtest sin asistencia. Si mejora, subimos al escalón 2 (asistencia condicionada por saliencia/oficialismo/año electoral).
- **RESULTADO del backtest_asistencia (corrida de Valle, mismo día) — NEGATIVO, informativo:** el escalón 1 naive **empeoró** el agregado: Brier 0,011→0,034, skill 0,76→0,26, acc 0,987→0,966. Calibración: ~1.000 actas se corrieron del bin de "aprobación segura" (bin9 4.542→3.503) a los bins 5-8 (pred 0,55-0,85) **pero esas votaciones aprobaron el 98-100%** → el motor pasó de pesimista a SUB-confiado. El problema original tampoco se movió (bin0 sigue 230 actas pred ~0, real 9%). **Causa:** aplicar el presentismo PROMEDIO (0,77) uniforme mete ausencias falsas: en una votación que efectivamente se votó la asistencia fue mayor que el promedio (sesgo de selección — se vota lo que junta gente). Lección (anticipada por el plan): el presentismo a secas es el baseline a SUPERAR, no la solución; la asistencia es CONDICIONAL (más alta en las votaciones salientes que llegan al recinto) → es el escalón 2. Mientras tanto, el motor SIN asistencia (Brier 0,011) queda como default. Opciones: (a) escalón 2 = P(presente | saliencia/oficialismo/año electoral); (b) diagnóstico rápido: correr la dirección-entre-presentes SIN ruido de asistencia (p_present=1) para aislar si el arreglo de dirección ayuda por sí solo; (c) recalibración isotónica como piso.
- **DIAGNÓSTICO (SIN_RUIDO=1, corrida de Valle):** aísla los dos cambios. Solo **dirección-entre-presentes SIN ruido de asistencia**: **Brier 0,0089, skill 0,81, acc 0,990** — MEJOR que el original (0,011) y que el asistencia-con-ruido (0,034). Conclusión: (1) leer la postura del bloque entre PRESENTES es un arreglo genuino y se ADOPTA como default del motor; (2) el ruido de asistencia con promedio plano (aunque individual) es lo que rompía → confirma el punto de Valle: la asistencia debe ser CONDICIONAL al proyecto (tema, origen oficialismo/oposición, incomodidad para el propio espacio, contexto ICG), no un promedio. Residual que persiste en las 3 versiones: bin0 (230 actas pred ~0, real 9%) — chico, aparte. **Decisión de Valle: antes del escalón 2 de asistencia, avanzar con el AGENTE DE TAXONOMÍAS** (variables/proyecto) para tener el feature store por tema/rasgos que condiciona asistencia Y posición de bloque. Asistencia escalón 2 queda en pausa hasta eso.

### [2026-07-10] modelo/agregador_institucional — Backtest a escala: fuerte en agregado, mal calibrado en las peleadas (hallazgo)
- **Quién:** Claude (motor) + Valle (corrida local)
- **Qué:** backtest del agregador sobre **4.890 actas**. Agregado FUERTE: **Brier 0,011** (vs. 0,046 de la tasa base), **skill score 0,76**, **accuracy@0.5 0,987** (tasa base de aprobación 0,952). Gate de pase "reglas validadas contra resultados reales": aprobado en agregado. **PERO la calibración destapa el trabajo de fondo:** el bin de P≈100% concentra 4.542/4.890 actas (las cómodas, calibración perfecta 0,998/0,998); en los ~350 casos no-triviales el motor **subestima la aprobación de forma sistemática** (dice 56% → real 94%; dice ~0% en 231 actas → real 9%). Es demasiado pesimista justo en las disputadas, que son las que importan.
- **Cómo:** causa diagnosticada — la "línea de bloque" que alimenta el backtest es la conducta mayoritaria sobre TODOS los escaños (incl. ausentes, definición bottom-up de disciplina v2). Con ausentismo alto la línea cae en NO_ACOMPANA y el motor descuenta afirmativos que en la práctica se emitieron. Para *medir indisciplina* está bien; para *predecir el recuento* hay que estimar la asistencia (→ `variables/asistencia_quorum`). Salidas: `modelo/agregador_institucional/outputs/{backtest_agregador.json, backtest_detalle.csv}`.
- **Archivos:** `modelo/agregador_institucional/outputs/*` (generados), esta entrada, `tablero_datos.js`.
- **Estado del módulo:** modelo/agregador_institucional EN CURSO (motor validado en agregado; calibración de disputadas pendiente).
- **Próximo paso (opciones):** (a) alimentar el motor con la línea de bloque sobre PRESENTES (no todos los escaños) + una tasa de asistencia esperada por bloque → debería corregir el sesgo pesimista; (b) recalibrar la P de salida (isotónica/Platt) sobre el backtest; (c) arrancar `variables/asistencia_quorum` como insumo real. Es el puente natural hacia el embudo/asistencia.

### [2026-07-10] modelo/agregador_institucional + producto/dashboard — Motor de agregación + Panel Nowcast (puesta en marcha)
- **Quién:** Claude (con Valle)
- **Qué:** decisión de foco de Valle: **pausar** `datos/diputados_oficial` (Dip 2020-23, se reanuda después) y **poner en marcha el sistema** con lo ya obtenido. Se construyó el **motor de agregación institucional** (`modelo/agregador_institucional`): dado el roster + la línea esperada de cada bloque + la tasa de desvío individual, simula la votación (Monte Carlo, 3 conductas por legislador coherentes con desvío v2) y devuelve la **P(aprobación) como distribución** con banda, aplicando quórum/umbral por tipo de mayoría (misma regla que export/voto_individual). Backtest incluido (Brier/calibración/accuracy vs. resultado real). Y un **Panel Nowcast** (`PANEL-NOWCAST.html` en la raíz, se abre con doble clic, autocontenido, patrón TABLERO-CONTROL): (1) tarjetas de estado del sistema, (2) simulador interactivo de una votación con motor JS réplica del Python. Demostración del valor: el mismo reparto de votos aprueba por mayoría simple y se cae por dos tercios (P=1 → P=0).
- **Cómo:** `agregador.py` (funciones `simular_votacion`/`backtest` + CLI `backtest`/`nowcast`); tests sintéticos 12 chequeos OK (rosters unánime→P=1, al filo→P intermedia con banda, agravada endurece, quórum). Motor JS del panel verificado headless en node (mismos resultados). Simplificaciones v1 documentadas: quórum laxo (el fino es `variables/asistencia_quorum`) y postura de bloque puesta a mano (la proyectará posición-de-bloque + embudo). **Backtest completo pendiente de corrida local** (lee la canónica; pesa) → se le pasa a Valle.
- **Archivos:** `modelo/agregador_institucional/{src/agregador.py, tests/test_agregador.py, README.md}`, `PANEL-NOWCAST.html`, `coordinacion/{TABLERO.md, ESTADO-DEL-PROYECTO.md}`, `tablero_datos.js`.
- **Estado del módulo:** modelo/agregador_institucional EN CURSO (motor + tests listos; falta backtest a escala); producto/dashboard EN CURSO (v1 del panel); datos/diputados_oficial PAUSADO.
- **Próximo paso:** Valle corre el backtest (`python modelo\agregador_institucional\src\agregador.py backtest`) y me pega el resumen (Brier/accuracy) para calibrar; después, conectar el panel a datos reales (roster del período actual) y sumar una posición de bloque proyectada por tema.

### [2026-07-10] modelo/voto_individual + variables/legislador + datos/export — Re-corrida completa con linajes v2 (en PC de Valle)
- **Quién:** Claude (código) + Valle (corrida local en PowerShell)
- **Qué:** cerrada la cadena del ADR-0005. Sobre la canónica ya regenerada (linajes v2), Valle corrió `disciplina.py → ficha.py → export_base.py all`. Resultados: **disciplina** 822.481 votos medidos, set pivote 753 (≥10% en disputadas), el desempate por linaje resuelve 4.169 votos más que la v1 (método parcial→linaje); **fichas** 1.972 legisladores (1.650 dip / 232 sen / 90 ambas), 4.795 filas legislador×período (14 períodos), 1.950 con tasa de desvío, presentismo mediano 0,817; **export** `congreso.db` 266,8 MB + 8 Excel por gobierno, desvío v2 en 822.481 filas, 190 disputadas. Control de integridad: los 8 Excel suman exactamente 5.333 actas y 834.749 votos (el corte por gobierno no pierde nada).
- **Cómo:** corrida local (el export pesa ~3 min y genera el .db de 266 MB → se corre en PC, no en el entorno de Claude; ver preferencia de trabajo). Comandos: `python datos\canonica\src\entity_resolution.py && ... && python datos\export\src\export_base.py all`.
- **Archivos:** `modelo/voto_individual/outputs/*` (regenerados), `variables/legislador/data/*` (regenerados, incl. `legisladores.xlsx`), `datos/export/data/{congreso.db, votaciones_*.xlsx}` (regenerados; el .db no se versiona).
- **Estado del módulo:** modelo/voto_individual EN CURSO (v2 al día con linajes v2); variables/legislador EN CURSO; datos/export EN CURSO (entregables regenerados y verificados).
- **Próximo paso:** limpiar `datos/Archivos_Borrar/congreso.db-journal` (journal viejo). Pendientes de fondo siguen: Dip 2020-23, bloque Senado 24-25, auditoría García/REVISAR, embudo y asistencia_quorum sin dueño.

### [2026-07-10] datos/canonica + evaluacion/baseline — Regeneración con linajes v2 (parquet + baseline)
- **Quién:** Claude (con Valle)
- **Qué:** ejecutado el paso pendiente del ADR-0005: se corrió `entity_resolution.py` sobre los 834.749 votos y se regeneró `votos_resuelto.parquet`. La bolsa **OTRO/PROVINCIAL bajó de 45,5% (380.135) a 18,6% (154.850)**; taxonomía en **10 linajes** (nacen PERONISMO FEDERAL 71.045 y PROGRESISMO 23.198). Baseline re-medido: el desempate por linaje es **señal real** — precisión por `bloque_linaje` sube de 0,9457→0,9501 (todas) y 0,9051→0,9133 (disputadas) vs. la versión v1; `coalicion` idem (0,9455→0,9499 / 0,9048→0,9130). El voto-dirección por `bloque_norm` no se mueve (0,9784 / 0,9632), como debía. **Hallazgo de consistencia:** el `baseline_canonico.json` versionado ya reflejaba los números v2; lo único desincronizado era el parquet (estaba en v1). Ahora ambos quedan consistentes en v2.
- **Cómo:** `python datos/canonica/src/entity_resolution.py && python evaluacion/baseline/src/baseline_canonico.py` (deps: pandas/pyarrow/jsonschema). Diferencia v1/v2 verificada corriendo el baseline real sobre una versión v1-reconstruida (linajes nuevos colapsados a OTRO) vs. la v2 actual.
- **Archivos:** `datos/canonica/data/clean/votos_resuelto.parquet` (regenerado), `evaluacion/baseline/outputs/baseline_canonico.json` (re-escrito, sin cambio de valores), `tablero_datos.js`.
- **Estado del módulo:** datos/canonica EN CURSO (parquet al día con linajes v2); evaluacion/baseline HECHO.
- **Próximo paso:** Valle re-corre **disciplina v2 + ficha + export** para capturar los ~200k votos de universo que gana el desempate por linaje; pendientes previos siguen (Dip 2020-23, bloque Senado 24-25, auditoría García/REVISAR).

### [2026-07-10] datos/canonica — Linajes v2: reclasificación de OTRO/PROVINCIAL (ADR-0005)
- **Quién:** Claude (con Franco)
- **Qué:** respondido el pedido del ADR-0004: la bolsa OTRO/PROVINCIAL cae de **45,5% a ~19%** de los votos. Decisiones de Franco: (1) dos linajes nuevos — **PERONISMO FEDERAL** (~71k votos: Reutemann, Romero, Solá, schiarettismo, rodriguezsaaísmo, PAUFE, Menem tardío, Unidad Federal…) y **PROGRESISMO** (~23k: socialismo, GEN, Frepaso, Lozano, Solanas); (2) **JUSTICIALISTA a secas partido por fecha** (nuevo mecanismo `LINAJE_VENTANAS`): Duhalde→PF, 25/05/2003-2015→FdT-UxP, 2016-19 Bossio/Pichetto→PF, ≥2019→FdT-UxP; (3) variantes claras a linajes existentes (Justicialista-FpV y Concertación→FdT-UxP; Frente PRO→PRO; A.R.I→CC; UNA→FR). Cada asignación verificada contra los datos (era + legislador ejemplar) antes de mapear. Taxonomía: 10 linajes.
- **Cómo:** `entity_resolution.py` (+40 entradas LINAJE, alias FpV-PJ sin espacios, `LINAJE_VENTANAS` genérico por rangos de fecha). Dry-run validado sobre los 834.749 votos. Detalle y trazabilidad en `BLOQUES.md`; decisión en ADR-0005. **Regenerar:** `python datos/canonica/src/entity_resolution.py` y re-medir baseline; avisar a Valle para re-correr disciplina v2 y export (el desempate por linaje gana ~200k votos de universo).
- **Archivos:** `datos/canonica/{src/entity_resolution.py, BLOQUES.md}`, `coordinacion/DECISIONES/0005-*.md`, `tablero_datos.js`.
- **Estado del módulo:** datos/canonica EN CURSO (linajes v2 listos; falta regenerar parquet).
- **Próximo paso:** correr entity_resolution + baseline (Franco); Valle re-corre disciplina/export; pendientes previos siguen (Dip 2020-23, bloque Senado 24-25, auditoría García/REVISAR).

### [2026-07-02] modelo/voto_individual — Suspendidos excluidos + herramienta de licencias anotada; disciplina.py reparado
- **Quién:** Claude (con Valle)
- **Qué:** (1) decisión de Valle: presidentes, SUSPENDIDOS y LICENCIAS se excluyen del índice de indisciplina. Los suspendidos ya quedan fuera (la fuente los anota en el nombre, ej. De Vido "Suspendido Art 70 C.N." — 520 filas); las licencias no son detectables hoy → **anotado módulo futuro `datos/licencias_suspensiones`**: registro + herramienta que detecte y NOTIFIQUE licencias/suspensiones (en PLAN 1A.6b, TABLERO y ADR-0004). (2) **Incidente:** el pull del tablero de Franco pisó `disciplina.py` v2 sin commitear (quedó corrupto con bytes nulos, mezcla v1/v2); reescrito completo desde la copia de la sesión — el resto del v2 (ADR, README, RESULTADOS, outputs, export) había sobrevivido. Regla práctica reforzada: pushear apenas se cierra una sesión de trabajo.
- **Cómo:** filtro por nombre "SUSPENDID" en `excluir_no_medibles()`; tests 18 chequeos OK; corrida completa verificada (2.110 filas excluidas; desvío medio 18,9%). Tablero de control actualizado (regla nueva de Franco: hito v2 agregado a `tablero_datos.js`, sintaxis validada).
- **Archivos:** `modelo/voto_individual/{src/disciplina.py, tests/test_disciplina.py, outputs/*}`, `coordinacion/{DECISIONES/0004-*.md, PLAN-DE-TRABAJO.md, TABLERO.md}`, `tablero_datos.js`.
- **Estado del módulo:** modelo/voto_individual EN CURSO (v2 estable); datos/licencias_suspensiones PENDIENTE (nuevo, sin dueño).
- **Próximo paso:** Valle regenera y pushea; descomposición tasa_desvio_voto/ausencia (propuesta, a confirmar); reclasificación OTRO/PROVINCIAL con Franco.

### [2026-07-02] coordinacion — TABLERO-CONTROL.html: tablero ejecutivo del proyecto (regla nueva)
- **Quién:** Claude (con Franco)
- **Qué:** el plan original de la plataforma ("Propuesta Técnica y Operativa.docx") quedó fusionado con TODO lo hecho hasta hoy en un tablero de control interactivo en la raíz: `TABLERO-CONTROL.html` (doble click, sin servidor). 7 pestañas: La Plataforma (módulos A-D con sus variables y estado), Hoja de Ruta (6 etapas con avance), Módulos del Repo (semáforo de los 27 módulos con filtros), Datos y Métricas (cobertura + baselines), Bitácora (línea de tiempo humana), Pendientes y Revisiones, Presupuesto (CAPEX/OPEX del plan). Lenguaje humano primero, detalle técnico desplegable. Plan vivo fusionado: los replanteos (ej. regresión→embudo/pivotes tras Fase 0, Hermes/Ollama→agente Claude) están incorporados como rumbo vigente.
- **Cómo:** diseño fijo en el HTML (NO se edita) + datos en `tablero_datos.js` (lo ÚNICO que se toca: fecha, estados, hito nuevo, kpis). **REGLA NUEVA en CLAUDE.md:** actualizar `tablero_datos.js` es obligatorio en el mismo PR, mismo régimen que ESTADO y EN-HUMANO. Validado con node (sintaxis + estados válidos + conteos).
- **Archivos:** `TABLERO-CONTROL.html`, `tablero_datos.js`, `CLAUDE.md` (regla + orden de lectura), `README.md` (punto 0).
- **Estado del módulo:** coordinacion HECHO (tablero operativo).
- **Próximo paso:** que cada Claude lo mantenga al día; revisar en equipo si los avances por etapa reflejan la percepción de todos.
### [2026-07-02] modelo/voto_individual + datos/export — DESVÍO v2: indisciplina total (ADR-0004)
- **Quién:** Claude (con Valle — definición de Valle)
- **Qué:** reformulación completa del desvío (ADR-0004): tres conductas (aprobar/rechazar/NO ACOMPAÑAR=abstención+ausencia); línea del bloque = mayoría simple sobre TODOS los escaños (bottom-up, los ausentes cuentan); desvío = conducta ≠ línea, ESTRICTA (abstenerse contra línea de rechazo computa; votar cuando el bloque se ausenta, también); empates → desempate por linaje real, y desvío PARCIAL (fraccional) en la bolsa OTRO/PROVINCIAL. Disputada unificada (±5% emitidos). **Hallazgo de la validación:** el top estaba dominado por los presidentes de la Cámara de Diputados (85-95% de falso desvío: no votan por costumbre) → lista curada PRESIDENCIAS_DIPUTADOS y exclusión; también placeholders "NO INCORPORADO". Resultado (823.001 votos): desvío medio 18,9% — ahora es indisciplina TOTAL (domina el ausentismo individual); top nuevo = los que no usan la banca (NK diputado 2010, Insaurralde 2014, licencias, De Vido suspendido); los díscolos de voto resaltan en disputadas (Fernández E. 91%, Manes 79%). datos/export suma columnas conducta/linea/desvio a la tabla Votos vía `desvios_por_voto.parquet` (contrato nuevo entre módulos).
- **Cómo:** `disciplina.py` reescrito (vectorizado, 3 métodos: bloque/linaje/parcial); tests 17 chequeos v2 (todos los casos de Valle); export merge verificado (823.001/834.749 filas con dato). Pendientes que abre: reclasificar OTRO/PROVINCIAL (45% de votos) a linajes; tratamiento de suspensiones/licencias; ponderación por trascendencia; disciplina ideológica por taxonomía.
- **Archivos:** `coordinacion/DECISIONES/0004-*.md`, `modelo/voto_individual/{src/disciplina.py, tests/test_disciplina.py, README.md, RESULTADOS.md, outputs/*}`, `datos/export/src/export_base.py`, `variables/legislador/src/ficha.py` (Metodologia), `coordinacion/PLAN-DE-TRABAJO.md`.
- **Estado del módulo:** modelo/voto_individual EN CURSO (v2 corrido sobre base completa); datos/export EN CURSO (falta regenerar entregables con desvío).
- **Próximo paso:** Valle corre disciplina→ficha→export y pushea; decidir suspensiones/licencias; reclasificación OTRO/PROVINCIAL (coordinar con Franco); disciplina ideológica cuando haya taxonomías.

### [2026-07-02] datos/export — Columna margen_votos + cierre de la definición de disputada
- **Quién:** Claude (con Valle)
- **Qué:** Valle auditó la lógica de disputada con 4 casos reales (jubilaciones 109 vs umbral 110 → sí; Consejo Magistratura 2003 140 vs 128 con 2/3 → no por 2,4 votos; unanimidad 70-0 → no; DNU 2025 132 vs 112,5 → no) y la validó. Se agrega **`margen_votos`** a la tabla Actas: afirmativos − umbral CON SIGNO, para que cualquier analista filtre con la vara que quiera sin recalcular; `disputada` queda como corte oficial (±5% de emitidos, 190 casos).
- **Cómo:** una línea en `calcular_disputada()` + Metodologia; tests 26 chequeos OK.
- **Archivos:** `datos/export/{src/export_base.py, tests/test_export.py, README.md}`.
- **Estado del módulo:** datos/export EN CURSO — código cerrado; falta corrida completa en PC de Valle + push.
- **Próximo paso:** corrida `all` + push; después, columna desvío en Votos (definición de Valle).

### [2026-07-02] datos/export — Ajuste de DISPUTADA: margen sobre los votos emitidos (96 → 190)
- **Quién:** Claude (con Valle)
- **Qué:** Valle objetó que 96 disputadas en 25 años era demasiado poco. Diagnóstico: no había bug (las votaciones del Congreso son mayormente cómodas: distancia mediana al umbral 54 votos en Dip / 21 en Sen — la pelea real pasa antes, por quórum), pero el ±5% calculado sobre el UMBRAL era demasiado duro, sobre todo en el Senado (±2 votos). Se midieron 4 interpretaciones (5% del umbral / de los emitidos / de los miembros / margen fijo 10 votos → 96/190/248/516) y **Valle eligió: ±5% de los votos emitidos ese día** → **190 disputadas**, con distribución por gobierno consistente (Milei 57, Macri 28, CFK-1 34, CFK-2 11).
- **Cómo:** una línea en `calcular_disputada()`; tests re-validados (24 OK); Metodologia y README actualizados con la decisión y las alternativas medidas.
- **Archivos:** `datos/export/{src/export_base.py, tests/test_export.py, README.md}`.
- **Estado del módulo:** datos/export EN CURSO (falta corrida completa en PC de Valle + push).
- **Próximo paso:** los mismos de la entrada anterior (columna desvío, unificar disputada hacia atrás, corrida + push).

### [2026-07-02] datos/export — Base unificada: SQLite + Excel por gobierno; nueva definición de DISPUTADA
- **Quién:** Claude (con Valle)
- **Qué:** módulo nuevo `datos/export` (solo LEE la canónica): (1) `congreso.db` — SQLite único con actas/votos/legisladores/legislador_periodo (5.333/834.749/1.972/4.795 filas; ~250MB, NO se versiona); (2) un Excel POR GOBIERNO (cortes por fecha exacta de asunción, 2001-03 irregulares por la crisis) con hojas Metodologia/Actas/Votos — separado por gobierno porque 835k votos no entran en una hoja. (3) **Nueva definición de DISPUTADA (Valle):** resultado a ±5% del umbral de la mayoría requerida (sensible a presentes y tipo_mayoria; umbral: SIMPLE=emitidos/2, ABSOLUTA=129/37, 2/3, 3/4). Reemplaza al proxy "minoría ≥10%". Resultado: **96 disputadas en 25 años** — validación externa perfecta: Ley Bases feb-2024 (132 vs umbral 127), jubilaciones jun-2024 (109 vs 110, perdida por 1 voto), mociones ajustadas.
- **Cómo:** `src/export_base.py` (normaliza 16 variantes de tipo_mayoria; completa totales faltantes contando votos nominales; escribe el .db a temporal y copia — SQLite falla sobre carpetas sincronizadas). Tests: 24 chequeos OK incl. los ejemplos de Valle. Correr: `pip install xlsxwriter && python datos/export/src/export_base.py all`.
- **Archivos:** `datos/export/{README.md, src/export_base.py, tests/test_export.py}`, `.gitignore` (+excepción xlsx transitoria), `coordinacion/TABLERO.md`.
- **Estado del módulo:** datos/export EN CURSO (código y tests listos; falta corrida completa de los Excel en PC con recursos).
- **Próximo paso:** columna `desvio` en tabla Votos (definición de Valle en próximo prompt); unificar "disputada" hacia atrás en voto_individual/baseline (coordinar con Franco — el baseline es suyo); corrida completa + push.

### [2026-07-02] modelo/voto_individual + variables/legislador — Re-corrida sobre base ampliada (con Senado 2015-2023)
- **Quién:** Claude (con Valle; corrida en PC de Valle)
- **Qué:** disciplina y fichas re-medidas sobre la base con las 5 fuentes: 474.744 votos medibles / 5.206 actas; desvío global 1,76%; set pivote ≥10% en disputadas = 112. Fichas: 1.972 legisladores (232 senadores, +37), 4.795 filas legislador×período (14 períodos). Conclusiones del gate 1 estables. **Hallazgo nuevo:** García, Virginia María (Senado 2016-17) con 75% de desvío en disputadas — cae en la ventana de la ruptura FpV/FpV-PJ que el padrón marca `REVISAR` → primera candidata de la auditoría de etiquetas. Fix menor: openpyxl Alignment (deprecation).
- **Cómo:** cerrar los Excel antes de re-correr (Windows bloquea los CSV abiertos — causó un PermissionError con salidas mezcladas; re-corrida limpia después). `RESULTADOS.md` actualizado con los números nuevos.
- **Archivos:** `modelo/voto_individual/{RESULTADOS.md, outputs/*}`, `variables/legislador/{src/ficha.py, data/*}`.
- **Estado del módulo:** sin cambios (gate 1 sigue APROBADO; datos al día con la base ampliada).
- **Próximo paso:** auditar García 2016-17 y demás filas REVISAR del padrón con Franco; luego piezas b-d del ADR-0003.

### [2026-07-02] .gitignore — Entregables versionados TRANSITORIAMENTE
- **Quién:** Claude (con Valle)
- **Qué:** decisión de Valle: mientras el sistema no esté en funcionamiento, los entregables de análisis viajan por git para que el equipo los vea sin correr scripts: `modelo/voto_individual/outputs/*.csv`, `variables/legislador/data/legisladores.csv` y `legisladores.xlsx` (se quitó su regla de ignore). Marcado como TRANSITORIO en el propio .gitignore: cuando el sistema esté operativo, revertir el bloque.
- **Cómo:** excepciones `!` targeted en `.gitignore` (no se des-ignora `*.csv` global: las cachés y datos crudos siguen fuera). Quien regenere debe commitear también los archivos regenerados para no dejar versiones viejas en el repo.
- **Archivos:** `.gitignore`.
- **Estado del módulo:** n/a (régimen de repo).
- **Próximo paso:** revertir cuando haya pipeline en funcionamiento (bot/nube).

### [2026-07-02] datos/canonica + evaluacion/baseline — Senado integrado al pipeline; baseline re-medido
- **Quién:** Claude (con Franco)
- **Qué:** la fuente `senado` quedó integrada a `run_pipeline.py` (paso 4b: scrape con caché → bloque histórico → copia de parquet a SOURCES; el padrón versionado evita regenerar). Pipeline corrido de punta a punta: **base canónica 5.333 actas / 834.749 votos, 2001-2026 ambas cámaras** (senado 2.887 / diputados 2.446). Baseline re-medido: global bloque_norm 0,979 todas / 0,964 disputadas; **Senado (por primera vez con serie completa y bloque de época): 0,983 todas / 0,957 disputadas (n=40.646)** — en peleadas es algo MENOS disciplinado que Diputados (0,965), consistente con la tesis de pivotes/díscolos del replanteo de voto_individual. Drift 2024-25 confirmado (0,946/0,923). Fixes de compatibilidad pandas 4 en `baseline_canonico.py` (array read-only + axis keyword).
- **Cómo:** correr `python datos/canonica/src/run_pipeline.py` (nota: requiere `jsonschema`; en Python nuevo, `pip install -r datos/canonica/src/requirements.txt`). Detalle de cobertura en `datos/canonica/COBERTURA.md`.
- **Archivos:** `datos/canonica/src/run_pipeline.py`, `datos/canonica/COBERTURA.md`, `evaluacion/baseline/src/baseline_canonico.py`, `evaluacion/baseline/outputs/baseline_canonico.json` (regenerado).
- **Estado del módulo:** canonica EN CURSO (cubre 2001-2026; faltan Diputados 2020-23 y alias de bloques nuevos del Senado); evaluacion/baseline HECHO (re-medido).
- **Próximo paso:** `datos/diputados_oficial` (2020-2023, hueco que ahora es el más grande); retro-completar bloque Senado 2024-25 de argentinadatos con el padrón de datos/senado; curar alias/linaje de los bloques nuevos del Senado en entity_resolution; ADRs pendientes (fuente Wikipedia; precedencia senado/argentinadatos).

### [2026-07-02] datos/senado — Bloque histórico aplicado: 100% cobertura, 0 anacronismos
- **Quién:** Claude (con Franco)
- **Qué:** resuelto el bloque CONTEMPORÁNEO de los 53.910 votos 2015–2023 (el sitio oficial pinta el último bloque conocido, anacrónico; el PDF del acta tampoco trae bloque — ambos verificados). Padrón en dos capas: (1) automático desde anexos Wikipedia 2017–2025 (`padron_bloques.py`, 291 filas); (2) **manual curado** (`padron_manual_2015_2017.csv`, 111 filas, VERSIONADO como fuente de verdad): 2015-2017 curado con el bloque real 2014 de la semilla (66), bloques estables (21), inferencias FpV-PJ pre-ruptura (11, `REVISAR`), y correcciones (huecos del anexo wiki 2021-23: Cornejo/Torres/Weretilneck/Olalla/Rodríguez; variante de nombre Ledesma Abdala; Unidad Federal nacido 22/02/2023 → antes FNyP/Córdoba Federal, validado Franco; sesión preparatoria 09/12/2021). Hallazgo: "Frente de Todos (Corrientes)" pre-2019 es HOMÓNIMO del FdT nacional → renombrado.
- **Cómo:** `aplicar_bloques.py` (manual > automático; matching por clave de tokens con fallback por subconjunto/variantes; controles de anacronismo por igualdad exacta; diagnóstico a Archivos_Borrar). Pipeline documentado en el README del módulo (orden: scrape → padrón → aplicar). `.gitignore`: excepción para versionar el padrón + régimen Archivos_Borrar anidado.
- **Archivos:** `datos/senado/{src/padron_bloques.py, src/aplicar_bloques.py, src/bajar_anexos_wiki.py, data/padron_bloques_senado.csv, data/padron_manual_2015_2017.csv, README.md}`, `.gitignore`, `coordinacion/{TABLERO.md, EN-HUMANO.md}`.
- **Estado del módulo:** datos/senado HECHO (quedan filas `REVISAR` del padrón, marcadas para el equipo).
- **Próximo paso:** sumar la fuente a `run_pipeline.py` (módulo canonica) y re-medir baseline Senado con bloque de época; ADRs pendientes: fuente Wikipedia para bloques, precedencia senado vs. argentinadatos 2024-25.

### [2026-07-01] datos/senado — Scraper oficial de votaciones (hueco 2015–2023)
- **Quién:** Claude (con Franco)
- **Qué:** scraper de la fuente oficial senado.gob.ar/votaciones para tapar el hueco Senado 2015–2023. Dos niveles: listado por año (form POST `busqueda_actas[anio]`) → detalle nominal por acta (`detalleActa/<id>`), que trae **bloque y provincia** por senador (resuelve además el gate "bloque del Senado" y podría retro-completar el SIN BLOQUE de argentinadatos 2024–25). Salida al esquema canónico v1 (`senado_actas.parquet` + `senado_votos.parquet`, `acta_id=senado:<id>`, fuente=`senado`, ya en el enum del schema). Plan B incluido: barrido directo por rango de ids (`--ids`) si el form cambiara. Se evaluó AndyTow-Robado (repo privado, inaccesible; su Senado nominal llega a 2014) y nahuelhds/votaciones-ar-datasets (Senadores 2010–2019, congelado; queda como VALIDACIÓN CRUZADA 2015–2019, no como fuente).
- **Cómo:** `src/scrape_votaciones.py` con las 4 directivas (tenacity/backoff, errores específicos, tablas por firma de encabezados, logging). Caché de HTML crudo en `datos/Archivos_Borrar/senado_html/`. QA integrado: nominal vs. totales publicados por acta (WARNING si no cuadra). Tests offline con fixtures sintéticos: 22 chequeos OK (`python datos/senado/tests/test_scrape.py`). Estructura del sitio verificada en vivo (listado 1983–2026 y detalle acta 2623).
- **Archivos:** `datos/senado/{README.md, src/scrape_votaciones.py, src/requirements.txt, tests/test_scrape.py, tests/fixtures/*}`, `coordinacion/{TABLERO.md, EN-HUMANO.md}`.
- **Estado del módulo:** datos/senado EN CURSO (scraper validado en vivo con 2018; falta corrida completa).
- **Actualización mismo día (corrida en vivo 2018, Franco):** 81 actas / 5.832 votos, 0 fallidas, nominal==totales en las 81, 0 SIN BLOQUE, ausentes listados nominalmente (sirve directo para asistencia_quorum). **HALLAZGO:** el `bloque` del sitio es el ÚLTIMO conocido del senador, no el contemporáneo (aparece "FRENTE DE TODOS" en 2018) → NO usar para disciplina 2015–2023; fix pendiente: padrón histórico→bloque por fecha. Fix aplicado al scraper: columna extra `instancia` eliminada (los schemas tienen additionalProperties=false y rompía el build de canonica); la instancia va plegada al título `[EN GENERAL]`. Tests: 24 chequeos OK.
- **Corrida completa 2015–2023 (Franco) + validación cruzada:** 749 actas / 53.910 votos, 0 fallidas, todas con cámara completa (71–72 filas). **Cruce contra nahuelhds/votaciones-ar-datasets (mismos ids de acta): 43.684 votos comparados por (acta, senador) → 0 discrepancias.** Conteo de actas por año idéntico en 2015/2017/2018; 2016 difiere en 2 actas VACÍAS del propio sitio (ids 99–100, hoy deslistadas; verificado en vivo); 2019 difiere porque nahuelhds congeló a mitad de año. Warning único (acta senado:1119): los totales publicados por el sitio (36 afirm.) no cuadran con su propia tabla nominal (43 afirm., tabla completa y sin duplicados → el nominal es lo confiable). **Defecto detectado y corregido:** `resultado`/`tipo_mayoria` se extraían del texto del detalle y se contaminaban con la tabla de votos (745/749 AFIRMATIVO); ahora se toman de las columnas del LISTADO. Requiere re-correr (con caché tarda ~2 min, re-parsea sin descargar).
- **Cierre de etapa (mismo día):** re-corrida con fixes OK. Datos finales: **749 actas / 53.910 votos, Senado 2015–2023 completo**, `resultado` normalizado (720 AFIRMATIVO, 13 NEGATIVO, 16 con detalle: AUSENTE/CANCELADA/LEV.VOT./EMPATE), `tipo_mayoria` del listado (712 SIMPLE, 22 ABSOLUTA, 14 DOS TERCIOS). Tests: 29 chequeos OK. El scraping quedó DELIMITADO y REPRODUCIBLE (caché en Archivos_Borrar; re-corrida completa ~40 s).
- **Próximo paso:** resolver bloque histórico (padrón Senado por fecha) — sin eso el bloque de esta fuente NO sirve para disciplina; sumar la fuente a `run_pipeline.py` (módulo canonica) y re-medir baseline Senado; decidir precedencia senado vs. argentinadatos en 2024–25 (hoy ambas =2, conviene ADR).
### [2026-07-02] (cierre de sesión) — Estado consolidado y próximos pasos priorizados
- **Quién:** Claude (con Valle)
- **Qué:** cierre de la sesión 2026-07-01/02. Quedó: (1) base canónica completa corrida en PC de Valle (781k votos); (2) gate 1 de voto_individual APROBADO (bisagras concentradas + drift 2024-26); (3) ficha individual de 1.935 legisladores con análisis por período parlamentario; (4) reglas nuevas en CLAUDE.md (hoja Metodologia en todo Excel) y resumen de estado refrescado; (5) perfil temático explicitado como pieza central (PLAN 1B.3).
- **Cómo:** para regenerar todo tras el pull: `python datos/canonica/src/run_pipeline.py && python modelo/voto_individual/src/disciplina.py && python variables/legislador/src/ficha.py`.
- **Archivos:** esta entrada + `CLAUDE.md` (resumen refrescado).
- **Estado del módulo:** ver tabla.
- **Próximo paso (en orden de prioridad):** (1) **corrida en vivo del agente de taxonomías** (variables/proyecto; solo necesita ANTHROPIC_API_KEY, todo lo demás está listo) → desbloquea el perfil temático; (2) **datos/expedientes** para el cruce acta→proyecto→taxonomía (segunda llave del perfil temático); (3) auditar etiquetas de bloque de los top díscolos (caveat del gate 1); (4) piezas b–d de voto_individual (defección, recuento como distribución, pivotes); (5) huecos de datos: Senado 2015–2023; (6) embudo y asistencia_quorum siguen prioritarios y sin dueño.

### [2026-07-02] coordinacion/PLAN + variables/legislador — Perfil temático por legislador, explicitado
- **Quién:** Claude (con Valle)
- **Qué:** Valle plantea una pieza central que el plan tenía solo implícita ("por tema" en 1B.4): el **desagregado del voto por taxonomía** — para cada legislador, además del consolidado afirmativos/negativos, su tendencia a aprobar/rechazar DENTRO de cada categoría temática (legislador × período × taxonomía). Es el diferencial vs. las páginas que solo muestran consolidados. Queda explicitado en PLAN 1B.3 y como pendiente en el README de variables/legislador (futura hoja "PorTema" del Excel).
- **Cómo:** todavía NO calculable: depende de (1) corrida a escala del agente de taxonomías (variables/proyecto, falta API key) y (2) cruce acta→expediente→proyecto para etiquetar cada votación con su tema. Solo documentación; sin código nuevo.
- **Archivos:** `coordinacion/PLAN-DE-TRABAJO.md`, `variables/legislador/README.md`.
- **Estado del módulo:** sin cambios (diseño registrado).
- **Próximo paso:** correr el agente de taxonomías en vivo; avanzar datos/expedientes para el cruce acta→proyecto; recién entonces implementar la hoja PorTema.

### [2026-07-02] variables/legislador + CLAUDE.md — Hoja "Metodologia" en todo Excel entregable (regla nueva)
- **Quién:** Claude (con Valle)
- **Qué:** pedido de Valle: los Excel van a ser muchos y extensos, así que **todo .xlsx entregable arranca con una hoja "Metodologia"** que explica cada columna de cada hoja (tabla hoja|columna|significado + definiciones generales: período parlamentario, desvío, disputada, vacío≠cero). Implementado en `legisladores.xlsx` (ahora 5 hojas: Metodologia/Fichas/PorPeriodo/Bloques/PorAnio) y elevado a regla de la casa en `CLAUDE.md`. Aclarado además que los CSV de `outputs/` no se borran: son contrato entre módulos (disciplina_individual.csv alimenta la ficha) y no se versionan.
- **Cómo:** constante `METODOLOGIA` + `hoja_metodologia()` en `ficha.py` (ancho de columnas + wrap). Los módulos con export propio (p. ej. datos/proyectos) adoptan la regla la próxima vez que se toquen.
- **Archivos:** `variables/legislador/src/ficha.py`, `CLAUDE.md`.
- **Estado del módulo:** variables/legislador EN CURSO.
- **Próximo paso:** re-correr `ficha.py` para regenerar el Excel con la hoja; replicar en el export de datos/proyectos cuando se retome ese módulo.

### [2026-07-02] variables/legislador + modelo/voto_individual — Período parlamentario como unidad de análisis
- **Quién:** Claude (con Valle)
- **Qué:** replanteo de Valle: el comportamiento se evalúa POR PERÍODO PARLAMENTARIO (entre recambios del 10-dic de años impares), porque cada recambio —incluso con reelección— es una nueva configuración de escaños que interviene en la disciplina. Se agregó la dimensión período en los dos módulos: `disciplina.py` emite `disciplina_por_periodo.csv` (legislador × período × cámara) y `ficha.py` emite `legislador_periodo.parquet` + hoja PorPeriodo en el Excel + columnas `periodos`/`n_periodos` en la ficha. Documentado que `anio_desde/hasta` es actividad observada, no mandato formal (el mandato exacto requiere el padrón oficial — pendiente).
- **Cómo:** `periodo_parlamentario(fecha, anio)`: límite exacto 10-dic en años impares con fecha; aproximación por año cuando falta (los pares son inequívocos). Definición duplicada y sincronizada en ambos módulos (regla un-módulo-un-dueño; unificar en `datos/_common` cuando exista). Tests: 12 chequeos disciplina + 18 ficha, OK.
- **Archivos:** `modelo/voto_individual/{src/disciplina.py, tests/test_disciplina.py, README.md, RESULTADOS.md}`, `variables/legislador/{src/ficha.py, tests/test_ficha.py, README.md}`.
- **Estado del módulo:** ambos EN CURSO; falta re-correr en PC con internet para regenerar salidas con la dimensión período.
- **Próximo paso:** correr `disciplina.py` y luego `ficha.py`; mandato formal desde el padrón oficial; auditar bloques de top díscolos.

### [2026-07-01] modelo/voto_individual — Gate 1 re-medido sobre base COMPLETA: APROBADO
- **Quién:** Claude (con Valle; corrida en PC de Valle)
- **Qué:** con la base completa (445.134 votos medibles, 4.463 actas, 2001–2026, 4 fuentes): desvío global 1,69%, mediana 0,77%, p90 6,55%. Set pivote: ≥10% en disputadas = 105 legisladores en 25 años → hipótesis de bisagras concentradas CONFIRMADA. Drift confirmado: top díscolos dominado por 2022–2026 (Monzó 45%, Massot 45%, Manes 30%, etc.) y baseline anual en disputadas cae a 0,946 (2024) / 0,923 (2025), mínimos salvo 2002. Fichas actualizadas: 1.935 legisladores, 1.642 con tasa de desvío. Caveat documentado: tasas >40% pueden reflejar etiqueta de bloque desactualizada → auditar top-20.
- **Cómo:** `disciplina.py` + `ficha.py` + `baseline_canonico.py` sobre la canónica completa. Fixes de compatibilidad pandas 4: `sum/min(axis=1)` explícito además del `copy=True` ya registrado.
- **Archivos:** `modelo/voto_individual/{RESULTADOS.md, src/disciplina.py, outputs/*}`, `evaluacion/baseline/src/baseline_canonico.py`, `variables/legislador/data/*` (regenerados).
- **Estado del módulo:** modelo/voto_individual EN CURSO — gate 1 APROBADO; variables/legislador v1 completa.
- **Próximo paso:** auditar etiquetas de bloque de los top díscolos; pieza (b) modelo de defección; luego (c) recuento como distribución y (d) pivotes (gate 2).

### [2026-07-01] fix — compatibilidad pandas nuevo (arrays de solo-lectura)
- **Quién:** Claude (con Valle)
- **Qué:** en la PC de Valle (pandas más nuevo, Copy-on-Write) `to_numpy()` devuelve arrays de solo-lectura y rompía el cálculo leave-one-out con `ValueError: assignment destination is read-only`. Corregido con `to_numpy(dtype=float, copy=True)` en los dos lugares que usan ese patrón.
- **Cómo:** una línea en cada script; tests de disciplina siguen OK (10 chequeos).
- **Archivos:** `modelo/voto_individual/src/disciplina.py`, `evaluacion/baseline/src/baseline_canonico.py`.
- **Estado del módulo:** sin cambios (fix de compatibilidad).
- **Próximo paso:** re-correr `disciplina.py` y `ficha.py` sobre la base completa ya reconstruida.

### [2026-07-01] variables/legislador — Base de datos individual de legisladores (ficha v1)
- **Quién:** Claude (con Valle)
- **Qué:** **corrección de encuadre de Valle:** el objetivo del análisis individual es la BASE DE DATOS de legisladores (la ficha completa de cada diputado/senador), no solo los díscolos — eso era el ejemplo motivador. Se construyó `variables/legislador` v1: 1.294 fichas (1.054 dip / 201 sen / 39 ambas cámaras) con identidad, cámara(s), distrito, años activos, trayectoria de bloques (con desde–hasta), presentismo, perfil de voto (afirm/neg/abst sobre presentes) y tasa de desvío tomada de `modelo/voto_individual` (1.095 con dato). Sanity check: Carrió presentismo 0,45 (su ausentismo conocido), Pichetto 2001–2026 ambas cámaras.
- **Cómo:** `src/ficha.py` lee la canónica y escribe `data/{legisladores,legislador_bloques,legislador_anio}.parquet` + CSV + Excel (regenerables, no se versionan). La tasa de desvío se integra si existe la salida de voto_individual; si no, queda NA (nunca 0). Tests sin red: 11 chequeos OK (`tests/test_ficha.py`). Aclaración de alcance agregada al ADR-0003 y al README de voto_individual para que nadie confunda pieza con todo.
- **Archivos:** `variables/legislador/{README.md, src/ficha.py, tests/test_ficha.py}`, `modelo/voto_individual/README.md`, `coordinacion/DECISIONES/0003-*.md`, `.gitignore`, `coordinacion/{TABLERO,EN-HUMANO}.md`.
- **Estado del módulo:** variables/legislador EN CURSO (v1 sobre base parcial 2001–2014+2026; re-correr con base completa).
- **Próximo paso:** re-correr con base completa; sumar slug web del diputado (desde datos/seguimiento); versión point-in-time (legislador-fecha) para el feature store.

### [2026-07-01] modelo/voto_individual — Gate 1 medido: índice de disciplina + set pivote (ADR-0003)
- **Quién:** Claude (con Valle)
- **Qué:** (1) ADR-0003 formaliza el cambio de rumbo del módulo (desvío individual + pivotes). (2) Implementada la pieza (a): `src/disciplina.py` calcula la tasa de desvío de cada legislador vs. la mayoría leave-one-out de su bloque por acta (misma vara que el baseline). (3) **Gate 1 medido** sobre base parcial (237.089 votos medibles, 2001–2014 + 2026): desvío global 1,54%; a ≥10% de divergencia en disputadas quedan ~56 legisladores en 25 años → la hipótesis de las 10–20 bisagras por período se sostiene. **Hallazgo:** en 2026 la tasa de desvío es 5,11%, un orden de magnitud sobre 2011–2014 (0,1–0,5%) — la disciplina se afloja como suponía el replanteo (caveat: 17 actas de alta saliencia).
- **Cómo:** base reconstruida OFFLINE con `run_pipeline.py` parcial (semilla CSV + Excel 2026; CKAN/argentinadatos requieren internet que este entorno no tiene → base 3.170 actas / 439.947 votos). Correr completo en PC con internet: `python datos/canonica/src/run_pipeline.py && python modelo/voto_individual/src/disciplina.py`. Detalle en `modelo/voto_individual/RESULTADOS.md`.
- **Archivos:** `coordinacion/DECISIONES/0003-voto-individual-desvio-y-pivotes.md`, `modelo/voto_individual/{README.md, RESULTADOS.md, src/disciplina.py, outputs/*}`, `coordinacion/{TABLERO.md, EN-HUMANO.md}`.
- **Estado del módulo:** modelo/voto_individual EN CURSO (pieza a hecha; b–d pendientes).
- **Próximo paso:** re-correr sobre base completa (2015–2025); modelo de defección P(desvía|tema,…); recuento como distribución + pivotes por ley.

### [2026-06-27] Reconciliación temas + lado votos listo para commit
- **Quién:** Claude (con Franco)
- **Qué:** (1) Temas: se mantiene SOLO el sistema del equipo (docs/taxonomias/taxonomias.json + variables/proyecto/agente_taxonomias.py). Mi clasificador por keywords y mi TAXONOMIA.md quedaron deprecados (stubs/punteros); mis 2 reglas de frontera ya están en el vocabulario controlado. (2) Lado votos: orquestador reproducible `datos/canonica/src/run_pipeline.py` que reconstruye la base de cero (4.584 actas / 780.839 votos, 2001-2025). .gitignore suma *.db/*.sqlite y Archivos_Borrar.
- **Cómo:** ver `datos/canonica/RECONSTRUIR.md`. Probado de punta a punta.
- **Archivos:** `datos/canonica/{src/run_pipeline.py,RECONSTRUIR.md}`, `.gitignore`, `variables/proyecto/{TAXONOMIA.md,RESULTADOS-tema.md,src/classify_tema*.py}` (deprecados).
- **Estado:** lado votos COMPLETO y reproducible; temas en manos del equipo.
- **Próximo paso:** commitear desde el clon limpio (git de esta carpeta OneDrive está corrupto). Pendiente real: Senado 2015-2023.

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

#### [2026-06-25] datos — Estrategia semilla → canónica → bot (aportes Andy Tow)
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
- **Próximo paso:** ninguno.
