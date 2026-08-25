# PLAN DE TRABAJO — Nowcast Legislativo

Plan estructurado para trabajo en paralelo. Para cada bloque: **qué** hay que hacer y **cómo**. El orden de prioridad sale del gate de Fase 0 (predecir el voto-dirección por bloque ya da ~0,99 **en promedio**; el valor está en asistencia, embudo, posición de bloque y —matiz 2026-06-30— en el **desvío individual vs. bloque** de los pocos legisladores bisagra que el promedio esconde; ver 1B.4).

## Cómo se trabaja (resumen operativo)

### Regla general: Claude NO puede borrar archivos (04-08-2026)

Claude tiene permiso de **lectura y escritura** sobre la carpeta, **no de
eliminación**. Puede crear y sobrescribir; no puede hacer desaparecer nada. Esto
no es una limitación menor: un archivo que "hay que borrar" y mientras tanto
sigue funcionando no es un pendiente, es un problema activo.

**Procedimiento obligatorio** cuando algo tiene que dejar de existir:

1. **Copiarlo** a `Archivos_Borrar/` con el nombre `BORRAR_<ruta-con-guiones>`.
2. **Neutralizar el original** para que no haga daño mientras espera: a un
   workflow se le sacan los disparadores automáticos, a un script se le saca el
   `__main__`, a un archivo de datos se le agrega una cabecera que lo invalide.
   **Este paso no es opcional.**
3. **Anotarlo** en `Archivos_Borrar/PENDIENTES-DE-BORRAR.md` con la ruta exacta
   y el motivo.

El dueño humano borra cuando quiera. Nada se rompe si tarda.

**De dónde sale la regla:** el 04-08 quedó un workflow duplicado en
`.github/workflows/` que, de haber llegado activo al repo, habría corrido en
paralelo con el bot real y los dos se habrían pisado al pushear.

### Regla general: lo que Claude NO ve no prueba que no exista (04-08-2026)

El entorno donde corre Claude monta la carpeta con **dos límites que no se
anuncian solos**, y los dos generaron trabajo equivocado el mismo día:

- **Los directorios que empiezan con punto: a veces se ven y a veces no.**
  El 04-08 Claude corrió `ls -a`, no vio `.git` ni `.github`, y concluyó que el
  repo no estaba conectado y que no había workflows. Las dos cosas eran falsas:
  escribió un instructivo entero para conectar git y un workflow que duplicaba
  uno existente. **Actualización 2026-08-06:** en esa sesión `ls -la` **sí**
  mostró `.github`, `.gitignore`, `.env` y `.gitattributes`. O sea que el mount
  cambió de comportamiento sin avisar, y la regla no puede escribirse como
  "nunca se ven" — hay que **mirar cada vez**. `.git` sigue sin aparecer, pero
  por el límite siguiente: vive un nivel más arriba, fuera de lo montado.
- **Sólo monta `Nowcast Congreso Argy/`, no la raíz del repo**, que está un
  nivel más arriba (`Nowcast-Congreso/`). Por eso los workflows nuevos quedaron
  en una ruta donde GitHub nunca los habría leído.

**Qué hacer:** ante un archivo o carpeta que *debería* estar y no aparece,
**preguntar antes de concluir**. El disco del dueño humano es la fuente de
verdad; lo que Claude ve es una vista parcial. Y cuando el trabajo toque
infraestructura del repo (workflows, hooks, configuración de CI), **pedir un
listado de la raíz antes de escribir nada**.

- Cada ítem mapea a un módulo/carpeta con su `README.md` (contrato).
- Reclamás el módulo en `TABLERO.md`, trabajás en rama propia, registrás en `ESTADO-DEL-PROYECTO.md`, abrís PR. Detalle en `PROTOCOLO-GIT.md`.

---

## Fase 0 — Datos y baseline · **CERRADA**
**Qué:** medir el piso de bloque y validar fuentes. **Resultado:** dirección ≈ 0,99; 4-clases ≈ 0,81; CKAN congelado en 2020. Ver `fase0/outputs/`.

---

## Tarea transversal — una skill de funcionamiento parlamentario argentino *(a crear; pedido de Valle 2026-08-20)*

**Por qué.** El 20-08 Claude escribió «los 243 casos bicamerales» para referirse a los
proyectos con votación en las **dos cámaras**. En el Congreso «bicameral» nombra otra cosa
—las **comisiones bicamerales**, que tratan asuntos que requieren las dos cámaras, como el
control de decretos del Ejecutivo—. Una palabra mal usada en una conversación de diseño se
convierte en un supuesto mal puesto en el modelo.

**Qué tiene que cubrir, como mínimo:**
- El circuito completo de un proyecto de ley: presentación → **giro a comisión(es) de la
  cámara de origen** → **dictamen de comisión** → pleno de origen → **media sanción / primera
  sanción** → **giro a las comisiones de la cámara revisora** → **nuevos dictámenes** → pleno
  de la revisora → **sanción**. Los dictámenes existen en LAS DOS cámaras: no son un evento
  de la cámara de origen.
- Dictamen de mayoría / de minoría / con disidencias (parciales y totales) / con
  observaciones, y qué significa cada uno para el tratamiento posterior.
- Comisiones **permanentes**, **especiales** y **bicamerales** — y por qué las bicamerales no
  son «un proyecto votado en las dos cámaras».
- Vías de tratamiento sin dictamen: **sobre tablas**, mociones de preferencia con y sin
  despacho, artículo 114 del reglamento de Diputados.
- Caducidad (**Ley 13.640**), períodos parlamentarios, sesiones ordinarias / de prórroga /
  extraordinarias, y qué cambia en cada una.
- Vocabulario que en el repo se usa con sentido propio: *denominador*, *acta*, *expediente*,
  *giro*, *linaje de bloque*, *roster nominal*.

**Para qué sirve, operativamente:** que cualquier Claude que entre al repo hable con
precisión institucional antes de tocar el modelo, y que los nombres de las puertas y de los
nodos del mapa salgan del vocabulario real y no de una analogía.

**Dueño:** sin asignar. **Estado:** PENDIENTE.

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
- **⚠️ 07-08:** la ingesta usa **caché** salvo `REFRESH=1` — una corrida sin esa variable no baja nada y el log lo dice bajito (`caché: proyectos.csv`). Refrescado ese día: 113.177 proyectos hasta el 30-jun. **HCDN publica con ~5 semanas de atraso.** Quien consume esto ahora es `datos/proyectos` (1A.5b), no el embudo directamente.

### 1A.5b datos/proyectos — la base de proyectos *(FUENTE DE VERDAD desde 2026-08-07, ADR-0009)*
- **Qué:** `proyectos.db` consolida el backfill de CKAN (`datos/expedientes`) **y** lo que junta el bot (`datos/bot_recoleccion`). **Es de donde lee `variables/embudo`.**
- **Cómo:** `migrar_ckan.py` (backfill) + `upsert_bot.py` (capa de merge con precedencia por campo). `store.py` **no se toca**: su `upsert_proyecto` reemplaza las tablas hijas completas, así que dos upserts sucesivos pierden datos en cualquier orden — por eso hay merge y no dos cargas.
- **Régimen:** la base **no viaja a git** (89 MB binarios) y se reconstruye en ~1 minuto desde fuentes versionadas. **Excepción:** `proyecto_taxonomias` NO es reconstruible (la llena el agente, cuesta API) → hay que exportarla a un archivo versionado antes de que el agente escriba.
- **Cuarentena:** lo que no se pudo leer va a `cuarentena.db`, una base aparte (decisión de Valle). Una fila rara no frena la carga; una avalancha (>5%, con piso de 10 filas) sí.
- **Control:** `verificar.py` — 14 invariantes que cortan con `exit 1`. `tests/test_verificar.py` rompe la base a propósito para probar que el control se dispara.
- **Gate:** CUMPLIDO — cohorte idéntica celda por celda entre la ruta vieja y la nueva; backtest 0,3643 / 0,4195 por ambas.

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
- **Avance 2026-07-11 sobre ese orden:** **(1) parcial — vocabulario VALIDADO a mano** (88 actas estratificadas 2001-25: 82% clasificable por título, 89% confianza alta/media; 5 huecos y 4 fronteras propuestos en `variables/proyecto/RESULTADOS-muestra-manual.md`; la muestra queda como set de referencia agente-vs-humano; el batch NO espera la API key —resuelta por Franco el 14-jul, prueba en vivo OK—; ~~el blocker real es `proyectos.db` + M1~~ → **DESBLOQUEADO 07-08: la base existe (ADR-0009)**). **(3) HECHA — ICG Di Tella vivo:** `variables/proyecto/data/icg_mensual.csv` (296 meses, nov-2001→jun-2026, 0 huecos, validado contra informes) + `src/ingesta_icg.py` con modo `serie` (Excel oficial; layout transpuesto resuelto) y modo `ultimo` (scrapea la página de informes para el mes nuevo antes de que rote el Excel; idempotente; invocable por el futuro bot). Tests 21 OK. **Siguen:** (2) regla origen por fecha ← próximo natural, (4) y (5).
- **Avance 2026-07-22/23 (Valle+Claude) — TEMA y ORIGEN por acta, sin esperar el batch de PDFs:** desbloqueado el condicionamiento por texto de las actas VOTADAS. (B tema) `variables/proyecto/tema_por_acta.py` clasifica por TÍTULO las actas votadas → `tema_por_acta.parquet` (1.537 actas, 2011-2026, 87% de cobertura en la ventana reciente del Senado). (C origen) `variables/proyecto/origen_por_acta.py` etiqueta `origen` (EJECUTIVO/OFICIALISMO/OPOSICION) + `origen_lado` (GOBIERNO/OPOSICION) + `gobierno` de turno POR ACTA, determinístico sin API key (4 vías: código de expediente, **código embebido en el título** del Senado viejo `PE-608/03`, O.D.→expedientes_resultados, match de título) → `origen_por_acta.parquet` (**59% global / 54,5% Senado**; tapa el hueco 2004-2014). (F derivadas) `variables/bloque` condiciona la dirección por tema/origen con shrinkage + **guard de mismo gobierno** (no mezcla eras en la ventana) + **exclusión de actas AUX** (homenajes/trámite/tratados = consenso, no informan postura). **Validado:** proyecto de SALUD de la oposición en Diputados (47 actas de historia) → LLA NEGATIVO 0,31, kirchnerismo AFIRMATIVO 0,98 = la política real. **Límite conocido (no del método, de los datos):** cruces finos (ej. ECON×GOBIERNO en el Senado) tienen 1-2 actas en la ventana → esperan más cobertura + multitemáticas (backlog).
- **Perfil temático por legislador (central, pedido de Valle 2026-07-02):** además del consolidado afirmativos/negativos (que cualquier página ya muestra), el diferencial es el **desagregado por taxonomía**: para cada legislador × período × taxonomía (`docs/taxonomias`), pct_afirmativo / pct_negativo / tasa_desvio → detectar tendencia a aprobar o rechazar dentro de cada tema. Sale como hoja "PorTema" en `legisladores.xlsx`. **Depende de:** (1) corrida a escala del agente de taxonomías (`variables/proyecto`; la API key YA está, ~~el blocker es `proyectos.db` + M1~~ → **DESBLOQUEADO 07-08 (ADR-0009)**) que llena `proyecto_taxonomias`; (2) cruce acta→expediente→proyecto para etiquetar cada votación con su tema (`datos/expedientes` + columna `expediente` de las actas).
- **Gate:** sin leakage; features validadas en muestra.

### 1B.4 modelo/voto_individual — desvío individual + pivotes *(reformulado 2026-06-30)*
- **Replanteo:** el voto-dirección por bloque acierta ~0,99, pero ese número es un **promedio** que tapa a los díscolos. El conteo agregado (p.ej. 120/257) es un punto; su varianza la cargan **10–20 bisagras** cuya (in)disciplina mueve la P(aprobación) en votaciones ajustadas. Por eso `modelo/voto_individual` se descongela: el objetivo no es predecir el voto medio, sino **separar el comportamiento partidario del individual** y modelar el desvío del legislador vs. su bloque. En 2024–25 la disciplina se afloja → más espacio para este modelo.
- **Qué (dos productos):** (1) **partidario/bloque** = posición esperada del bloque, para recuento agregado y análisis macro; (2) **individual/parlamentario** = el desvío respecto del bloque.
- **Cómo (cuatro piezas):** (a) **índice de disciplina individual** por legislador (tasa de desvío vs. bloque, global y por tema, time-aware); (b) **modelo de defección** P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral); (c) **recuento como distribución** — simular cada voto Bernoulli(pᵢ)=posición de bloque ajustada por desvío → distribución del conteo con intervalo, no número puntual; (d) **detección de pivotes** — qué legisladores son bisagra para una ley y cuánto mueve cada uno la P(aprobación). Distinguir partido ≠ bloque ≠ parlamentario.
- **Lee de:** `datos/canonica` (**1.016.632 votos** al 06-08-2026; decía ~781k, cifra de junio) + `variables/legislador` y `variables/bloque` cuando existan.
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

**Cuellos de botella (un solo dueño, coordinar antes de tocar):**

| Módulo | Por qué es cuello de botella |
|---|---|
| `datos/canonica` | es la fuente de verdad; todo `variables/` y `modelo/` lee de ahí. Un rebuild cambia el piso de todos. |
| `modelo/ensemble` | compone las salidas de todos los demás; dos personas tocándolo se pisan seguro. |
| `docs/schemas` | contrato de datos compartido. **Cambiarlo requiere ADR** (`coordinacion/DECISIONES/`) y aviso en el TABLERO. |
| `.gitignore` | tocarlo mal esconde trabajo. Ya pasó **cuatro veces**: parquet de expedientes (11-07), roster de jefes (30-07), salidas del embudo (31-07) y el padrón del Senado (04-08, que además generó una urgencia falsa). Al crear la salida de un módulo nuevo, decidir en el MISMO commit si entra al régimen transitorio. |

> **Nota de reparación (2026-08-06).** Esta sección estaba **truncada a mitad de
> la palabra "coordina"** — el mount corta los archivos grandes al leerlos y algún
> read-modify-write anterior propagó el corte al disco. Es el mismo daño que ya
> había sufrido `CLAUDE.md` (reparado el 04-08). Se reconstruyó a partir de las
> dependencias reales del repo y del `.gitignore`. **El guard:** verificar `wc -c`
> antes y después de reescribir cualquier archivo grande, y no leer entero lo que
> se puede parchear por streaming.

---

## Backlog anotado (pendientes, no abrir aún)

### Presidencias de DOS PERÍODOS en la curva del ciclo — pendiente (anotado 2026-08-04, Valle)
La curva del ciclo presidencial (`variables/proyecto/data/curva_ciclo_presidencial.csv`)
promedia todas las presidencias alineadas por mes de mandato, tratándolas como
equivalentes. **No lo son.** Observación de Valle: CFK I termina muy por encima
de la curva (+0,48 en los meses 43-48) **porque venía una reelección** — no hay
expectativa de cambio abrupto, así que la caída típica del final de mandato no se
produce. Lo mismo aplicaría al tramo Néstor→CFK I, que también fue continuidad.

Es decir: el ciclo de un gobierno que **se sabe saliente** no es el mismo que el de
uno que **puede continuar** (por reelección propia o por sucesión del mismo signo).
La curva actual mezcla los dos regímenes.

**Pendiente:** decidir si la curva se parte en dos (mandatos con continuidad vs. con
alternancia) o si se corrige el tramo final. **Por ahora se omite** — con 6
presidencias, partir la muestra deja 3 y 3, y la curva ya es frágil en la cola
(los meses 43+ quedan con n=1 al sacar la contaminación del traspaso).
Retomar cuando el mecanismo del ICG esté validado end-to-end.


### Proyectos MULTITEMÁTICOS (leyes ómnibus) — pendiente (anotado 2026-07-22, Valle)
El tagger de temas (`variables/proyecto/tema_por_acta.py`) y el v2 de bloque usan hoy **un solo tema primario** por votación. Las leyes ómnibus mezclan varias materias en una sola votación y no encajan en un tema único: p. ej. **Ley Bases** (economía + desregulación + laboral + energía + privatizaciones), **Ley de Glaciares** (ambiente + minería + federalismo), y la **ley de desregulación difundida hoy en el Congreso**. El tagger YA guarda todas las etiquetas (`todas_ids`, multi-label), pero el condicionamiento del v2 sólo lee la primaria. **Pendiente:** decidir cómo condiciona la dirección de bloque cuando un proyecto es multitemático (¿promedio ponderado de las posturas por cada tema?, ¿el tema dominante?, ¿la materia más conflictiva?). **Por ahora se omite** — se usa el tema primario. Retomar cuando el v2 esté validado con temas de un solo eje.
- **Refuerzo 2026-07-23 (Valle):** la sesión confirmó que además del tema hace falta MÁS COBERTURA DE ACTAS. Un mismo tema mezcla consenso y conflicto: p. ej. "ECON" o "TRAB" en el Senado 2024-25 son mayormente proyectos que la oposición también acompañó, no las reformas contenciosas del gobierno (que aún no están en los datos votados). La exclusión de actas AUX (consenso puro: homenajes/trámite/tratados) ya está implementada en `variables/bloque` (`excluir_aux`), pero separar "proteger vs. desregular" dentro de un mismo tema necesita la designación multitemática + más actas. Dos ejes del mismo pendiente: (i) multi-label operativo, (ii) volumen de votaciones contenciosas.

---

## 🔭 REVISIÓN DE LAS COMISIONES — línea de trabajo abierta (nombrada por Valle, 2026-08-07)

> Valle abre esta línea al aparecer el sesgo del Senado (abajo). **Criterio suyo:** no se
> parchea de a un síntoma; cuando se toque, se revisa **el circuito completo** de cómo un
> proyecto atraviesa comisiones y cámaras. Hasta entonces **no se abre** — se acumulan
> insumos acá.

### Insumo 1 — El universo del Senado está sesgado por supervivencia (detectado 2026-08-07)

**El síntoma, medido en `p_embudo.parquet`:**

| cámara de origen | proyectos | P(sanción) media |
|---|---:|---:|
| Diputados | 39.971 | 1,73% |
| **Senado** | 1.368 | **48,03%** |

**La causa, verificada:** `expedientes.parquet` es el registro de **HCDN (Diputados)**. De un
proyecto nacido en el Senado se entera **recién cuando le llega con media sanción**. Prueba
directa: los **1.999** expedientes con `camara_origen=Senado` tienen **los 1.999** un
`exp_senado` — o sea que todos ya cruzaron. **No hay un solo proyecto del Senado en la base que
se haya quedado en el Senado.** De los 1.368 de ley, 656 son ley = 47,95%.

**Por qué importa más de lo que parece:** `camara_senado` **es un rasgo del modelo**
(`embudo.py:366`). El modelo aprendió que "viene del Senado" predice sanción, cuando lo que
codifica es "**ya pasó** el Senado". El error va **para arriba**, que es el lado peligroso.

**Precaución operativa mientras tanto:** no publicar P(sanción) de proyectos con origen Senado.

**Lo que lo mejora, y ya está en curso:** los 520 proyectos de ley del Senado que junta el bot
(DAE) son la primera vista de proyectos senatoriales **que todavía pueden morir** — le dan al
modelo el denominador que le falta. Entran con el ADR-0009. Aun así el universo va a seguir
siendo parcial: el bot arranca en 2026.

**Preguntas que la Revisión tendrá que contestar:**

1. ¿El nowcast es de **Diputados** y se declara así, o se modela el Senado **aparte** con su
   propio denominador? (decisión de producto, no técnica → ADR)
2. ¿`camara_origen` sigue siendo un rasgo, o hay que sacarlo hasta tener universo comparable?
3. ¿Cuánto del **embudo** de Diputados sufre lo mismo en menor grado? El circuito real es
   comisión → dictamen → recinto → otra cámara, y hoy se modela como etapas de un solo lado.
4. ¿Los **giros** (a qué comisión va cada proyecto) son comparables entre cámaras, siendo que
   el catálogo de 151 comisiones sale del lado de Diputados?

### Insumo 2 — `expedientes_giros` conoce 278.196 proyectos; la tabla principal tiene 112.793 (detectado 2026-08-07)

Al migrar a `proyectos.db` (ADR-0009) aparecieron **242.890 filas de giro huérfanas**: apuntan a
**165.403 proyectos que no están en `expedientes.parquet`**. El embudo ya las ignora —
`cnt.reindex(exp["proyecto_id"])` las descarta en silencio — así que **no son un bug ni afectan
el skill actual**, y la migración las descarta igual (verificado: 179.253 giros entran, que es
exactamente lo que el embudo ve hoy).

**Pero dicen algo sobre la cobertura:** el backfill de CKAN de la tabla de expedientes es un
**subconjunto** de lo que las tablas hijas conocen. O bien `expedientes.parquet` está filtrado
por algún criterio no documentado, o la ingesta se cortó. Son 1,5 veces el universo actual.

**Afinado el mismo día, a pedido de Valle ("¿son de ley o de otro tipo?"). Se parten en dos:**

- **~90.963 tienen id POR DEBAJO del mínimo de la base** (`HCDN092249`). Los ids de HCDN son
  correlativos y la base arranca el **2008-03-03**, así que son anteriores al backfill.
  **Ignorarlos es correcto:** están fuera de la ventana declarada.
- **🔴 74.440 tienen id DENTRO del rango de la base** y aun así no están en ella. Eso **no** lo
  explica la antigüedad. Es un hueco sin diagnóstico.

**Y la pregunta de Valle no se puede contestar:** el `tipo` (LEY / RESOLUCION / DECLARACION) vive
en `expedientes.parquet`, que es justamente la tabla de la que faltan. De un huérfano se sabe
**sólo su comisión y el orden del giro** — ni fecha, ni título, ni autor, ni desenlace. No hay
forma de saber si son proyectos de ley sin volver a la fuente.

**Rastreado hasta la fuente el mismo día (Valle: "¿cómo volvemos a la fuente original?").**
El crudo de CKAN **sobrevive en disco**: `datos/Archivos_Borrar/expedientes_ckan/` (bajado el
12-jul). No hizo falta descargar nada. Resultado:

> 📅 **Cifras del crudo del 12-jul**, que es el que estaba en disco al hacer este análisis.
> Tras el refresco del 07-08 son 113.177; **la conclusión no cambia** (el hueco es de ~165.000
> proyectos), pero si alguien rehace la cuenta le van a dar números un poco distintos.

| crudo de HCDN | filas | proyectos distintos |
|---|---:|---:|
| `proyectos.csv` | 112.793 | **112.793** |
| `giros.csv` | 422.143 | **278.196** |

**La ingesta no pierde nada** — el parquet tiene exactamente las 112.793 del crudo. **El hueco
viene así de CKAN:** HCDN publica giros de 165.403 proyectos que no publica en el dataset de
proyectos. No es un bug nuestro.

**Qué son, con la evidencia disponible.** Los huérfanos tocan **147 comisiones** contra 94 de los
conocidos, y **58 aparecen SÓLO entre ellos**: `ENERGIA`, `POBLACION Y RECURSOS HUMANOS`,
`REFORMA ADMINISTRATIVA`, varias bicamerales viejas, y `EDUCACION Y CULTURA` — que hoy figura
partida en `EDUCACION` y `CULTURA` por separado del lado de los conocidos. **Usan la nomenclatura
vieja de comisiones**, o sea que son de períodos anteriores. Van a comisiones legislativas
normales (Presupuesto y Hacienda, Relaciones Exteriores), así que **no** son "oficiales varios"
ni peticiones particulares: parecen proyectos de verdad, sólo que más viejos.

⚠️ **La pista del id no servía.** Se creyó que 74.440 estaban "dentro del rango" y por lo tanto
eran contemporáneos. Los ids de HCDN **no son cronológicos entre tandas de digitalización**, así
que el solapamiento de rangos no prueba nada. La nomenclatura de comisiones es mejor evidencia
que el número de id.

**Si son anteriores a 2008, ignorarlos es correcto y la tasa base está bien.** Es lo más
probable, pero **no está confirmado**. Lo que lo confirmaría, y es barato: leer en
`datos.hcdn.gob.ar` qué período declara cubrir cada dataset (`proyectos-parlamentarios` vs
`giro-a-comisiones`). Requiere red, así que queda para la Revisión.

💡 **Aparte, y aprovechable ya:** el crudo es del **12-jul** y el parquet llega al **02-jun**.
Volver a correr `ingesta_ckan.py` podría cerrar parte del hueco de proyectos recientes **gratis**,
sin depender del bot. Vale probarlo antes de dar por sentado que sólo el bot puede taparlo.
