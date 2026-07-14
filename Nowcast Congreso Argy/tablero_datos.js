// =====================================================================
// TABLERO DE CONTROL — DATOS (único archivo que se edita)
// =====================================================================
// REGLA DE LA CASA (ver CLAUDE.md): todo cambio relevante en el repo
// actualiza este archivo en el mismo PR, igual que ESTADO-DEL-PROYECTO
// y EN-HUMANO. Qué tocar:
//   1. `actualizado` y `actualizado_por`
//   2. el `estado` de lo que cambió (modulos_plataforma / etapas /
//      modulos_repo) y su nota
//   3. agregar un hito arriba de todo en `hitos` (1-3 frases, en humano)
//   4. si cambió un número clave, actualizar `kpis` / `metricas`
// NO tocar TABLERO-CONTROL.html (el diseño es fijo y lee este archivo).
// Estados válidos: "HECHO" | "EN CURSO" | "PARCIAL" | "PENDIENTE"
//                  | "FUTURO" | "REPLANTEADO"
// =====================================================================

const TABLERO = {
  actualizado: "2026-07-14",
  actualizado_por: "Valle (con Claude) — puesta en marcha con la cámara REAL: nace datos/padron (nómina oficial individual, Dip 257 + Sen 72), se enchufa al proyector (roster 375→257) y el Nowcast corre end-to-end sobre 1167-D-2025",

  proyecto: {
    nombre: "Nowcast Legislativo Argentino — Plataforma de Inteligencia Política",
    mision: "Una plataforma predictiva automatizada que calcula la probabilidad de sanción de proyectos de ley en el Congreso argentino. No reemplaza al analista político: le da un radar — qué proyectos ganan tracción, qué legisladores son la bisagra que define una votación, y cuánta incertidumbre real hay detrás de cada número.",
    dinamica: [
      "El sistema indexa la actividad legislativa (proyectos, giros, dictámenes, votaciones) mediante scraping y procesamiento de lenguaje.",
      "Con esa base, el motor recalcula las probabilidades y las presenta no como un número seco sino como un rango con su incertidumbre (ej.: \"80% ± 9%\").",
      "El producto final es un informe periódico en lenguaje natural con la predicción graficada y su banda de confianza.",
      "Aprendizaje clave que ordenó todo (Fase 0): predecir el voto individual mirando al bloque ya acierta ~99%, así que el valor NO está ahí. Está en: quién asiste (quórum), si el proyecto llega a votarse (embudo), qué postura toma el bloque, y los 10-20 legisladores bisagra que definen las votaciones peleadas."
    ]
  },

  kpis: [
    { etiqueta: "Base canónica", valor: "834.749 votos", detalle: "5.333 actas · 2001-2026 · ambas cámaras (senado 2.887 / diputados 2.446)" },
    { etiqueta: "Disciplina de bloque (disputadas)", valor: "96,4%", detalle: "Diputados 96,5% · Senado 95,7% — el Senado es la cámara menos disciplinada en votaciones peleadas" },
    { etiqueta: "Drift 2024-25", valor: "94,6% → 92,3%", detalle: "La disciplina se afloja: más espacio para el modelo de desvíos y pivotes" },
    { etiqueta: "Fichas de legisladores", valor: "1.972", detalle: "Identidad, bloques, presentismo, perfil de voto y desvío, por período parlamentario (14 períodos)" },
    { etiqueta: "Módulos del repo", valor: "7 HECHOS · 10 en curso", detalle: "Ver pestaña Módulos del repo" }
  ],

  // ============ LOS 4 MÓDULOS DE LA PLATAFORMA (las "pestañas" del producto) ============
  modulos_plataforma: [
    {
      id: "A",
      nombre: "El Nowcast (Probabilidad de Sanción)",
      pregunta: "¿Qué probabilidad tiene este proyecto de convertirse en ley?",
      estado: "EN CURSO",
      resumen_humano: "Es el motor principal: la probabilidad (0-100%) de que un proyecto sea aprobado. La Fase 0 nos enseñó que el camino no es adivinar cada voto (el bloque ya lo explica casi todo) sino descomponer el problema: ¿el proyecto llega a votarse? (embudo), ¿quiénes van a estar ese día? (asistencia/quórum), ¿qué postura toma cada bloque?, y ¿qué hacen las bisagras? El resultado se entrega como distribución (\"entre 115 y 125 votos\"), no como número seco.",
      detalle_tecnico: [
        "Arquitectura actual: embudo (P de llegar al recinto) × agregador institucional (reglas de quórum y mayorías) × posición de bloque ajustada por desvío individual (simulación Bernoulli por legislador).",
        "El diseño original preveía una regresión logística directa sobre el voto; quedó reformulado tras la Fase 0 (baseline bloque ≈ 0,99 la volvía redundante). Las variables previstas siguen vigentes como features del embudo y del agregador."
      ],
      variables: [
        { nombre: "Embudo legislativo", desc: "P(comisión → dictamen → tratamiento). Medido en bruto: solo el 3,22% de los proyectos de ley se sanciona (y casi nada se rechaza: muere en cajón). Modelo v1 con GATE APROBADO (skill 0,34-0,39, AUC ~0,95) sobre 41.339 proyectos, segmentado por origen/líder; falta enchufar el tema. El insumo lo sirve datos/expedientes.", estado: "EN CURSO" },
        { nombre: "Asistencia / quórum", desc: "Quién está presente el día de la votación (el ~19% que el bloque no explica). Escalón 1 (presentismo por legislador) construido y backtesteado: el presentismo promedio empeora la calibración → la asistencia debe ser CONDICIONAL al proyecto (escalón 2). El Senado 2015-2023 ya trae ausentes nominales.", estado: "EN CURSO" },
        { nombre: "Posición de bloque (variables/bloque)", desc: "Tamaño, cohesión (Rice), desvío interno y fracturas por bloque en el tiempo + proyector point-in-time. CORRIDO y ENCHUFADO: las bancas salen del padrón OFICIAL (composición real a la fecha, 257/72) y el desvío/postura del histórico; arreglado el roster inflado (375→257). Falta la dirección por tema/origen (v2).", estado: "EN CURSO" },
        { nombre: "Desvío individual y pivotes", desc: "Índice de disciplina por legislador + detección de las 10-20 bisagras que mueven la P en votaciones ajustadas.", estado: "EN CURSO" },
        { nombre: "Gravedad Presidencial (ICG - Di Tella)", desc: "El costo social de oponerse al Ejecutivo.", estado: "FUTURO" },
        { nombre: "Proximidad Electoral", desc: "Penalización de la probabilidad a medida que se acercan las urnas.", estado: "FUTURO" },
        { nombre: "Factor Gobernador / ATN", desc: "El impacto del flujo de fondos discrecionales hacia las provincias.", estado: "FUTURO" },
        { nombre: "Consistencia Temática", desc: "La rigidez histórica del legislador frente a temas específicos (requiere el perfil temático, PLAN 1B.3).", estado: "PENDIENTE" },
        { nombre: "Afinidad de Comisión (Committee Overlap)", desc: "Si los firmantes del proyecto integran la comisión a la que fue girado (los giros ya se extraen).", estado: "PENDIENTE" },
        { nombre: "Veto Legal (Gatekeeper)", desc: "Regla de nulidad automática para reformas electorales en años comiciales.", estado: "FUTURO" }
      ]
    },
    {
      id: "B",
      nombre: "Mapa de Influencia (Puntos de Liderazgo)",
      pregunta: "¿Quién tracciona realmente los votos?",
      estado: "PENDIENTE",
      resumen_humano: "Mide quién firma los proyectos de quién: los legisladores \"Nodos\" cuyos proyectos atraen firmas transversales reciben un Puntaje de Liderazgo. Si un proyecto lo impulsa un Nodo de alto puntaje, su probabilidad de dictamen favorable se multiplica.",
      detalle_tecnico: [
        "Algoritmo PageRank (NetworkX) sobre la red de co-autorías.",
        "Insumo ya disponible: datos/seguimiento extrae los firmantes de cada expediente (validado en vivo en ambas cámaras). Falta la ingesta masiva de expedientes para armar la red."
      ],
      variables: []
    },
    {
      id: "C",
      nombre: "Espectro Ideológico Real",
      pregunta: "¿Quiénes negocian en las sombras?",
      estado: "PENDIENTE",
      resumen_humano: "Supera la visión de \"bloques cerrados\": agrupa a los legisladores por con quién co-patrocinan proyectos, sin importar el bloque formal. Detecta temprano los \"votos fugitivos\" (opositores que firman consistentemente con el oficialismo) y mapea alianzas invisibles.",
      detalle_tecnico: [
        "Clustering sobre la red de co-firmas (mismo grafo que el Módulo B).",
        "Germen ya construido: el índice de disciplina individual (modelo/voto_individual) detecta díscolos por VOTO; este módulo agrega la dimensión por FIRMA."
      ],
      variables: []
    },
    {
      id: "D",
      nombre: "Medición de Volatilidad Política (Factor μ)",
      pregunta: "¿Cuánto ruido de pasillo hay detrás del número?",
      estado: "PENDIENTE",
      resumen_humano: "Un índice de aleatoriedad que captura las negociaciones invisibles: mide el error histórico entre lo que predijimos y lo que pasó, y lo convierte en la banda de confianza de cada predicción (ej.: \"75% ± 12%\"). Es lo que hace honesto al Nowcast.",
      detalle_tecnico: [
        "μ = varianza histórica de los errores de predicción (Brier Score) agrupada por temática: μ = (1/N) Σ (Y_real − P_predicho)².",
        "Se actualiza por inferencia bayesiana con cada ciclo de backtesting. Vive en evaluacion/metricas + evaluacion/backtesting (ambos pendientes; necesitan al menos un modelo nuevo corriendo)."
      ],
      variables: []
    }
  ],

  // ============ HOJA DE RUTA (etapas del plan, fusionadas con la realidad) ============
  etapas: [
    {
      n: 0,
      nombre: "Fase 0 — Baseline (¿el problema vale la pena?)",
      estado: "HECHO",
      avance: 100,
      resumen_humano: "Antes de construir nada, medimos lo obvio: ¿cuánto acierta la regla \"votá con tu bloque\"? Respuesta: ~99%. Eso mató el enfoque ingenuo y redirigió el producto hacia el embudo, la asistencia y las bisagras. La decisión más importante del proyecto.",
      detalle: [
        "Baseline LOO sobre 831k votos: bloque_norm 0,979 todas / 0,964 disputadas.",
        "Gate 1 de voto_individual APROBADO: las bisagras están concentradas y el drift 2024-26 les da cada vez más peso (ADR-0003)."
      ],
      pendiente: []
    },
    {
      n: 1,
      nombre: "Etapa 1 — Datos: la base canónica (la fundación real)",
      estado: "EN CURSO",
      avance: 80,
      resumen_humano: "La materia prima: TODAS las votaciones nominales del Congreso en una base propia, verificable y reproducible con un comando. Ya cubre 2001-2026 en ambas cámaras (835 mil votos), con los bloques que correspondían el día de cada votación.",
      detalle: [
        "Estrategia semilla → canónica → bot (ADR-0002): Andy Tow como semilla de un solo uso; fuentes oficiales y agregadores encima; esquema canónico versionado (schema_version=1).",
        "Senado 2015-2023 cerrado (749 actas / 53.910 votos, validado voto a voto contra fuente independiente, bloque histórico 100%).",
        "Reproducible: python datos/canonica/src/run_pipeline.py reconstruye todo de cero."
      ],
      pendiente: [
        "Diputados 2020-2023 (argentinadatos incompleto → scraper de votaciones.hcdn.gob.ar). HOY ES EL HUECO MÁS GRANDE.",
        "Bloque del Senado 2024-25 (retro-completar con el padrón de datos/senado).",
        "Bot de recolección continua (trae las votaciones nuevas solo).",
        "Alias/linaje de los bloques nuevos del Senado en entity_resolution."
      ]
    },
    {
      n: 2,
      nombre: "Etapa 2 — Ingesta y clasificación (la lectura)",
      estado: "EN CURSO",
      avance: 60,
      resumen_humano: "El sistema lee el Congreso: rastrea proyectos y su avance (giros, dictámenes) y les pone temas automáticamente usando IA, eligiendo de un diccionario controlado de 74 temas que el equipo puede editar.",
      detalle: [
        "datos/seguimiento: extractor de giros/trámite validado en vivo (Diputados y Senado).",
        "datos/proyectos: base SQLite de proyectos de ley, upsert idempotente, export Excel.",
        "docs/taxonomias: vocabulario controlado v1 (74 ids estables, multi-etiqueta).",
        "Agente de taxonomías: motor Claude API (reemplazó al plan original Hermes/Ollama zero-shot — más calidad, costo acotado con Haiku); valida ids contra el vocabulario, el humano siempre gana."
      ],
      pendiente: [
        "CORRIDA EN VIVO del agente de taxonomías (solo falta la API key) → desbloquea el perfil temático.",
        "datos/expedientes: ingesta masiva (cruce acta→proyecto→tema + red de firmas para Módulos B/C).",
        "OCR para proyectos escaneados."
      ]
    },
    {
      n: 3,
      nombre: "Etapa 3 — Procesamiento matemático y backtesting",
      estado: "PARCIAL",
      avance: 30,
      resumen_humano: "Los cálculos que convierten datos en señal: el índice de disciplina ya corre (quiénes son los díscolos y cuánto pesan); faltan la red de influencia (PageRank), las métricas de calibración y el Factor μ de volatilidad.",
      detalle: [
        "HECHO: índice de disciplina individual por legislador y por período parlamentario + dimensionamiento del set pivote (modelo/voto_individual, gate 1 aprobado).",
        "HECHO: ficha individual de 1.935 legisladores con Excel de 5 hojas (regla: toda entrega .xlsx lleva hoja Metodologia).",
        "PENDIENTE: PageRank de co-autorías (NetworkX) — necesita expedientes.",
        "PENDIENTE: evaluacion/metricas (Brier, calibración) y evaluacion/backtesting → de ahí sale el Factor μ."
      ],
      pendiente: [
        "Modelo de defección: P(desvía | tema, cercanía de la votación, período, provincia, ciclo electoral).",
        "Recuento como distribución + detección de pivotes por ley.",
        "✅ Auditoría de etiquetas de los top díscolos: CERRADA 11-07 (17/17 validadas; García y las camporistas son fractura real del FpV-PJ 2016-17, no error)."
      ]
    },
    {
      n: 4,
      nombre: "Etapa 4 — Infraestructura y orquestación (el cerebro 24/7)",
      estado: "FUTURO",
      avance: 0,
      resumen_humano: "Llevar todo a un servidor que corra solo: la nube que indexa a diario, el enjambre de agentes de IA que cruza las variables y emite el dictamen predictivo. Hoy todo corre en las PCs del equipo, a propósito: primero el modelo, después el fierro.",
      detalle: [
        "Plan: Oracle Cloud Always Free (ARM 24GB RAM) + Docker + PostgreSQL.",
        "Orquestación multi-agente: 7 agentes analistas (modelo local) + 1 agregador (API Claude, suma/resta el Factor μ temático y aplica vetos legales) + 1 redactor (API Claude).",
        "A revisar al arrancar: framework de orquestación y si el modelo local sigue siendo la mejor opción de costo/calidad."
      ],
      pendiente: ["No abrir hasta que el ensemble tenga sus piezas (embudo + agregador) — regla del TABLERO de módulos."]
    },
    {
      n: 5,
      nombre: "Etapa 5 — Síntesis y reporte (el producto final)",
      estado: "FUTURO",
      avance: 0,
      resumen_humano: "El informe semanal que un cliente puede leer: la predicción de cada proyecto graficada con su \"banda de sombra\" (ej.: \"Probabilidad de Sanción: 80% — Volatilidad Temática: ±9%\"), explicada en lenguaje natural.",
      detalle: [
        "Agente Redactor (API Claude) explica la matriz de datos en lenguaje natural.",
        "Dashboard (producto/dashboard) y API (producto/api) como canales; no abrir sin ensemble / sin pagador."
      ],
      pendiente: []
    }
  ],

  // ============ MÓDULOS DEL REPO (semáforo operativo) ============
  modulos_repo: [
    { modulo: "docs/schemas", estado: "HECHO", owner: "—", nota: "Esquema canónico v1 (acta + voto). Cambiarlo requiere ADR." },
    { modulo: "docs/taxonomias", estado: "HECHO", owner: "Valle", nota: "Vocabulario controlado v1: 74 ids estables, multi-etiqueta, editable." },
    { modulo: "evaluacion/baseline", estado: "HECHO", owner: "—", nota: "Re-medido 02-07 sobre base completa: 0,964 disputadas global; Senado 0,957." },
    { modulo: "datos/ckan_diputados", estado: "HECHO", owner: "—", nota: "Diputados 2011-2019. Migrar de fase0/ a su carpeta." },
    { modulo: "datos/decada_votada", estado: "HECHO", owner: "—", nota: "Semilla integrada vía CSV (Dip 2001-2010 + Sen 2004-2014). El export R quedó innecesario." },
    { modulo: "datos/senado", estado: "HECHO", owner: "Claude+Franco", nota: "2015-2023 completo: 749 actas / 53.910 votos, bloque histórico 100%. Padrón curado versionado con filas REVISAR para el equipo." },
    { modulo: "datos/manual_2026", estado: "HECHO", owner: "—", nota: "Excel curado 2026 integrado (máxima precedencia)." },
    { modulo: "datos/padron", estado: "EN CURSO", owner: "Valle", nota: "Padrón OFICIAL de bancas a nivel LEGISLADOR (no bloque): Diputados 257 + Senado 72 vigentes, con mandato desde-hasta individual, clave canónica (join con voto_individual) y linaje consistente con la canónica. Es la composición de la cámara A LA FECHA: reemplaza el conteo por ventana móvil del proyector (que inflaba el roster a 375). Fuente: nómina oficial de cada cámara (bajada aparte; el módulo solo normaliza). Flag: 4 bancas del FIT + algunos federales del Senado caen hoy en OTRO/PROVINCIAL (mapeo de entity_resolution = ADR). Falta: histórico profundo de mandatos (fase 2)." },
    { modulo: "datos/canonica", estado: "EN CURSO", owner: "Claude+Franco", nota: "Base 2001-2026 ambas cámaras, 835k votos, reproducible. Linajes v2 (ADR-0005): 10 linajes, OTRO/PROVINCIAL 45%→19%, parquet regenerado + baseline re-medido. Falta: Dip 2020-23." },
    { modulo: "datos/argentinadatos", estado: "HECHO", owner: "Claude+Franco", nota: "Bloque Senado 2024-25 resuelto vía padrón versionado (SIN BLOQUE=0 en Senado). Queda un residuo menor en Diputados (roster de la fuente)." },
    { modulo: "datos/seguimiento", estado: "EN CURSO", owner: "Valle", nota: "Extractor de giros/trámite Dip+Sen, validado en vivo. Insumo del embudo." },
    { modulo: "datos/proyectos", estado: "EN CURSO", owner: "Valle", nota: "Base SQLite de PdL + export Excel; upsert idempotente." },
    { modulo: "datos/export", estado: "EN CURSO", owner: "Valle", nota: "Base unificada para analistas: SQLite + Excel por gobierno (solo LEE la canónica). Definición oficial de DISPUTADA: ±5% de los emitidos → 190 en 25 años, + margen_votos por acta. Entregables regenerados con linajes v2 (congreso.db 266,8 MB + 8 Excel, verificados)." },
    { modulo: "variables/proyecto", estado: "EN CURSO", owner: "Valle", nota: "Agente de taxonomías listo + vocabulario VALIDADO a mano (88 actas: 82% clasificable, 5 huecos y 4 fronteras propuestos en RESULTADOS-muestra-manual.md). ICG Di Tella CORRIDO: data/icg_mensual.csv con 296 meses (nov-2001→jun-2026, 0 huecos, validado contra informes UTDT) + modo 'ultimo' para la actualización mensual (scrapea la página de informes, idempotente; tests 21 OK). FEATURE-STORE.md diseñado (6 familias de rasgos). ORIGEN+LÍDER por proyecto construidos (origen_lider.py → features_proyecto.parquet): origen ejecutivo/oficialismo/oposición (cruce autor→bloque→fecha) y líder (jefe de bloque curado + pdte comisión + alto productor sin leakage). 16 tests OK." },
    { modulo: "variables/legislador", estado: "EN CURSO", owner: "Valle", nota: "Ficha de 1.935 legisladores por período parlamentario. Hoja PorTema bloqueada por taxonomías." },
    { modulo: "modelo/voto_individual", estado: "EN CURSO", owner: "Valle", nota: "Gate 1 APROBADO (ADR-0003). Re-corrido con Senado 2015-23: set pivote = 112 legisladores (≥10% desvío en disputadas). Faltan defección, distribución y pivotes por ley." },
    { modulo: "datos/diputados_oficial", estado: "PENDIENTE", owner: "PAUSADO", nota: "Diputados 2020-2023 desde votaciones.hcdn.gob.ar. PAUSADO por decisión de Valle (2026-07-10): se prioriza poner en marcha el sistema con lo ya obtenido; se reanuda después." },
    { modulo: "datos/expedientes", estado: "EN CURSO", owner: "Claude+Franco", nota: "Backfill CKAN hecho: 112.793 proyectos 2008-2026, embudo bruto 3,22%, enlace acta→expediente 89%. Fase 2: cofirmantes + origen Senado (bot diario TP+DAE anotado)." },
    { modulo: "datos/licencias_suspensiones", estado: "PENDIENTE", owner: "libre", nota: "Registro + notificador de licencias/suspensiones (ADR-0004: se excluyen del índice de indisciplina; hoy solo los suspendidos son detectables)." },
    { modulo: "variables/embudo", estado: "EN CURSO", owner: "Claude+Valle", nota: "v1 GATE APROBADO: embudo por etapas (el cuello está en el dictamen: solo 7,8% lo consigue) + modelo de supervivencia sin leakage. Backtest a escala (41.339 proyectos): skill 0,34-0,39, AUC ~0,95 vs tasa base. Ahora SEGMENTA por origen (ejecutivo/oficialismo/oposición) y liderazgo (embudo_por_origen/lider) y los suma al modelo. Falta el tema." },
    { modulo: "variables/asistencia_quorum", estado: "EN CURSO", owner: "Valle", nota: "Escalón 1 (presentismo por legislador + modo asistencia del agregador) construido y backtesteado: el presentismo PROMEDIO uniforme empeoró la calibración (Brier 0,011→0,034; volvió dudosas ~1.000 votaciones cómodas). Aprendizaje: la asistencia es CONDICIONAL (sesgo de selección: se vota lo que junta gente) → escalón 2. Motor sin asistencia queda de default." },
    { modulo: "variables/bloque", estado: "EN CURSO", owner: "Claude+Valle", nota: "v1 CORRIDO Y ENCHUFADO: serie temporal por bloque (272 filas: tamaño, postura, cohesión de Rice, desvío, fracturas) + proyector point-in-time (proyectar_postura) que ahora toma las bancas del PADRÓN oficial (datos/padron): composición real a la fecha (257 Dip / 72 Sen), desvío/postura del histórico. Arreglado el roster inflado (375→257). La DIRECCIÓN proyectada sigue incondicional (v2 = por tema/origen)." },
    { modulo: "modelo/agregador_institucional", estado: "EN CURSO", owner: "Valle", nota: "Motor de recuento como DISTRIBUCIÓN: roster + línea de bloque + desvío → P(aprobación) con banda, aplicando quórum/umbral. Tests 12 OK. Backtest 4.890 actas: Brier 0,011, skill 0,76, acc 0,987 — fuerte en agregado; falta calibrar las disputadas (subestima aprobación por ausentismo → necesita asistencia_quorum)." },
    { modulo: "evaluacion/metricas", estado: "PENDIENTE", owner: "libre", nota: "Brier, calibración → insumo del Factor μ." },
    { modulo: "datos/bot_recoleccion", estado: "EN CURSO", owner: "Claude+Franco", nota: "BICAMERAL y AUTOMATIZADO en GitHub Actions: DAE Senado (1.004 exp.) + TP Diputados con cofirmantes completos. Falta: estreno TP en vivo, upsert, fase votaciones, backfill TP 2019-25." },
    { modulo: "modelo/ensemble", estado: "EN CURSO", owner: "Claude+Valle", nota: "v1 puesta en marcha: P(aprobación) = P(llega al recinto) × P(mayoría). Nuevo comando nowcast_auto: arma el escenario SOLO desde variables/bloque (composición del padrón + postura histórica), sin escenario a mano. Primer end-to-end con cámara real: 1167-D-2025 → 15% (llega) × 100% (mayoría) = 15%, 137 afirmativos (banda 131-143) vs umbral 123, roster 257. Falta: dirección de bloque condicionada (v2) y p_llega del embudo por id." },
    { modulo: "evaluacion/backtesting", estado: "PENDIENTE", owner: "bloqueado", nota: "Necesita al menos un modelo nuevo corriendo." },
    { modulo: "producto/dashboard", estado: "EN CURSO", owner: "Valle", nota: "PANEL-NOWCAST.html (raíz, doble clic, autocontenido): tarjetas de estado + simulador interactivo de una votación (motor JS réplica del agregador). v1." },
    { modulo: "variables/contexto", estado: "FUTURO", owner: "—", nota: "ICG, proximidad electoral, ATN. No abrir sin cerrar prioridades." },
    { modulo: "producto/api", estado: "FUTURO", owner: "—", nota: "No abrir sin pagador." }
  ],

  // ============ COBERTURA DE DATOS ============
  cobertura: {
    descripcion: "Qué años y cámaras cubre la base canónica y de qué fuente sale cada tramo.",
    filas: [
      { periodo: "2001-2010", diputados: "✅ semilla (Década Votada)", senado: "✅ semilla (2004-2014)" },
      { periodo: "2011-2019", diputados: "✅ CKAN oficial", senado: "✅ semilla (→2014) + scraper oficial (2015→)" },
      { periodo: "2020-2023", diputados: "🟡 incompleto (argentinadatos parcial) — PRÓXIMO OBJETIVO", senado: "✅ scraper oficial con bloque de época" },
      { periodo: "2024-2025", diputados: "✅ argentinadatos", senado: "🟡 argentinadatos (SIN BLOQUE — retro-completable)" },
      { periodo: "2026", diputados: "✅ Excel curado", senado: "✅ Excel curado (con bloque)" }
    ],
    notas: [
      "Senado 2001-2003 no existe como voto nominal (se votaba a mano alzada).",
      "Validación externa del Senado 2015-2019: 43.684 votos cruzados contra nahuelhds, 0 discrepancias.",
      "El bloque de cada voto del Senado 2015-2023 es el CONTEMPORÁNEO (padrón Wikipedia + curación manual, 0 anacronismos)."
    ]
  },

  metricas: [
    { nombre: "Disciplina bloque_norm (todas)", valor: "97,9%", contexto: "600.649 votos sustantivos, LOO" },
    { nombre: "Disciplina bloque_norm (disputadas)", valor: "96,4%", contexto: "290.400 votos en votaciones peleadas (minoría ≥10%)" },
    { nombre: "Senado disputadas", valor: "95,7%", contexto: "n=40.646 — menos disciplinado que Diputados (96,5%)" },
    { nombre: "Drift de disciplina", valor: "2024: 94,6% · 2025: 92,3%", contexto: "La disciplina se afloja: crece el espacio de las bisagras" },
    { nombre: "Disidencia intra-espacio", valor: "~8,7%", contexto: "Linaje/coalición aciertan 91,3% en disputadas (linajes v2 + bolsa OTRO en 17,4%): la interna que queda es señal pura" },
    { nombre: "Desvío individual global", valor: "1,76%", contexto: "474.744 votos medibles — el legislador típico casi no se desvía" },
    { nombre: "Set pivote", valor: "112 legisladores", contexto: "≥10% de desvío en votaciones disputadas: la lista corta de bisagras a modelar" }
  ],

  // ============ HITOS (línea de tiempo humana; el más nuevo ARRIBA) ============
  hitos: [
    { fecha: "2026-07-14", titulo: "Puesta en marcha con la cámara REAL: nace el padrón oficial y el Nowcast corre de punta a punta sobre un proyecto", texto: "Faltaba un dato de base sorprendentemente ausente: quién ocupa cada banca HOY. El proyector de bloques venía contando 'bancas' mirando quién votó en los últimos dos años, y con el recambio del 10 de diciembre eso inflaba la cámara a 375 diputados (hay 257). Se creó un módulo nuevo, datos/padron, con la nómina OFICIAL a nivel de cada legislador —Diputados 257 y Senado 72, con su mandato y su bloque— y se enchufó al motor: ahora la composición es la real del día y el comportamiento (cuánto se desvía cada espacio) sigue saliendo de la historia. Con eso, por primera vez el circuito completo corrió sobre un proyecto de verdad (1167-D-2025): 15% de llegar al recinto × mayoría prácticamente asegurada = 15% de aprobación, con 137 votos esperados sobre un umbral de 123. La dirección de cada bloque todavía es la de su promedio reciente (falta condicionarla al tema del proyecto: próximo paso)." },
    { fecha: "2026-07-14", titulo: "Puesta a punto del tablero de coordinación: todo el estado quedó al día y sin trabajo 'invisible'", texto: "Se revisó módulo por módulo comparando lo que hay en disco contra lo que decían los tres tableros. Apareció un caso de trabajo hecho pero no anotado —el módulo de bloques (variables/bloque), que ya tenía su versión 1 programada y probada— y varias casillas de estado que habían quedado viejas (base canónica, asistencia, motor de agregación y el panel figuraban como 'pendientes' cuando ya estaban en curso). Se corrigió todo para que el mapa del proyecto refleje la realidad. No se tocó código ni datos: es orden y trazabilidad." },
    { fecha: "2026-07-13", titulo: "El clasificador de temas por IA quedó listo de punta a punta (y ya no le hace falta OCR)", texto: "Se consolidó el agente que le pone temas a cada proyecto de ley: lee el PDF, elige del diccionario de 74 temas (sin inventar), puede proponer temas nuevos para revisión humana y nunca pisa lo que cargó una persona. Novedad clave: los PDF escaneados ya no se saltean — el modelo los lee con su visión (el 'OCR' viene incorporado), mandando texto cuando lo hay (barato) y el PDF entero solo cuando es imagen. Se agregó una corrida en lote idempotente para clasificar todo de una y quedó decidido que corre por API desde el código (no depende de la consola). 23 chequeos en verde. Falta la corrida masiva sobre los proyectos vivos." },
    { fecha: "2026-07-12", titulo: "El embudo ahora distingue quién empuja el proyecto (Gobierno, oficialismo, oposición, líderes)", texto: "No todos los proyectos juegan el mismo torneo: uno del Poder Ejecutivo o de un jefe de bloque oficialista tiene otra llegada que uno de un diputado de a pie de la oposición. Se etiqueta cada proyecto por origen (ejecutivo / oficialismo / oposición, mirando el bloque del autor EN LA FECHA y quién gobernaba) y por liderazgo del firmante, y el embudo ya se lee por segmento y usa esas pistas. La definición de 'líder' y el listado de jefes de bloque quedan para afinar (nota para el equipo de Franco)." },
    { fecha: "2026-07-12", titulo: "Puesta en marcha: el Nowcast ya da un número de aprobación para un proyecto", texto: "Se conectaron las piezas: P(aprobación) = P(llega al recinto) × P(mayoría en el recinto). El sistema toma un proyecto y un escenario de bloques y devuelve la probabilidad descompuesta, con los votos esperados y su banda. En la prueba: 58% de mayoría pero 12% de llegar al recinto = 7% de aprobación, con la votación al filo del umbral. Por primera vez el circuito completo produce un número explicado. Falta que la postura de cada bloque se proyecte sola (hoy va a mano)." },
    { fecha: "2026-07-12", titulo: "Arrancó el embudo: de \"3% se sanciona\" a una predicción por proyecto", texto: "Se abrió el número grueso del embudo en sus etapas (presentado→comisión→dictamen→recinto→ley) por año, cámara y comisión, y se construyó un modelo que estima la probabilidad de que cada proyecto llegue al recinto y sea ley, usando SOLO lo conocido al presentarlo (sin trampa) y validado a ciegas con backtest temporal. Es la mitad que faltaba del nowcast: P(aprobación) = P(llega al recinto) × P(mayoría). 18 tests OK; corrida a escala en la PC de Valle." },
    { fecha: "2026-07-11", titulo: "El robot quedó bicameral: Diputados con firmas completas", texto: "El bot ahora también lee el Trámite Parlamentario de Diputados: cada proyecto con TODOS sus firmantes (el dato que faltaba para los Módulos B y C), tipo, giros y PDF. 13 chequeos contra páginas reales. Bonus: hay archivo histórico hasta 2019 para reconstruir redes de firmas hacia atrás." },
    { fecha: "2026-07-11", titulo: "El robot ya corre solo en GitHub Actions", texto: "Estreno del bot: 1.004 expedientes del Senado (51 DAEs de 2026) en un minuto, con memoria incremental. Y quedó programado en GitHub Actions: cada mañana trae lo nuevo y lo commitea al repo solo — la primera pieza 100% automática del sistema, sin servidor propio. Falta la mitad de Diputados (TP, URLs ya ubicadas)." },
    { fecha: "2026-07-11", titulo: "Cero votos sin bloque en el Senado (deuda saldada)", texto: "Los votos 2024-25 del Senado ahora toman el bloque del padrón histórico propio + el Excel curado de Franco proyectado con corrección de época. El baseline ganó 2.000 votos justo en los años del drift, y la bolsa de \"sin familia\" cerró en 17,4% (empezó en 45,5%)." },
    { fecha: "2026-07-11", titulo: "El iceberg completo: 112.793 proyectos presentados y el embudo dio 3,22%", texto: "Backfill del CKAN de Diputados (2008-2026) con giros, dictámenes y resultados. De cada 100 proyectos de ley, se sancionan 3 — y en 18 años hubo solo 4 rechazos formales: el Congreso deja morir, no rechaza. El denominador del embudo existe, más el enlace acta→expediente (89%) y los integrantes de comisiones. Anotado el diseño del bot diario (Trámite Parlamentario + DAE)." },
    { fecha: "2026-07-11", titulo: "Los rebeldes del Senado son de verdad (auditoría cerrada)", texto: "Las 17 filas dudosas del padrón de bloques quedaron validadas: cero errores de etiqueta. Los desvíos altos resultaron ser la fractura real del FpV-PJ 2016-17 — el ala cristinista votando NO a las leyes de Macri mientras la conducción de Pichetto acompañaba. El medidor de díscolos queda certificado." },
    { fecha: "2026-07-11", titulo: "El diccionario de temas aprobó su examen (y llegó el clima político)", texto: "Antes de gastar en clasificar miles de proyectos con IA, se probó el vocabulario de 74 temas a mano sobre 88 votaciones reales de 25 años: funciona (82% clasificable por título, con alta confianza). La prueba dejó además la lista de retoques: 5 temas que faltan (el más frecuente: el control del Congreso al Ejecutivo — DNU, interpelaciones) y 4 reglas de frontera a fijar. Y el Índice de Confianza en el Gobierno de Di Tella ya está adentro: 296 meses (nov-2001→jun-2026, sin huecos, verificado contra los informes oficiales) — la 'gravedad presidencial' que mide cuánto cuesta oponerse al gobierno de turno. El Excel de Di Tella tenía un formato rebuscado (fechas en una fila, valores abajo, dos hojas) y la primera corrida lo destapó; el lector quedó arreglado y con examen de regresión." },
    { fecha: "2026-07-11", titulo: "El plano de los datos: qué sabe el sistema de cada proyecto", texto: "El experimento de asistencia dejó clara una idea: la presencia (y casi todo) depende del TIPO de proyecto — un legislador falta cuando el tema lo incomoda o cuando lo presenta su oposición. Para condicionar así hace falta saber de qué es cada proyecto y quién lo impulsa. Se diseñó en papel el 'feature store': la ficha de rasgos de cada proyecto (tema, quién lo presenta y si es oficialismo u oposición, tipo de mayoría, clima político con el índice de confianza de Di Tella, cercanía de elecciones) y cómo cada rasgo alimenta la predicción. Es el mapa que ordena lo que viene: primero correr el agente que le pone temas a los proyectos." },
    { fecha: "2026-07-11", titulo: "Asistencia (escalón 1): probamos, midió, y nos enseñó algo", texto: "Conectamos el presentismo de cada legislador al motor (leer la postura del bloque entre los presentes, y hacer votar a cada uno según cuánto suele asistir). En casos de prueba corregía el pesimismo. PERO el backtest histórico completo dio peor: usar el presentismo PROMEDIO para todas las votaciones mete ausencias falsas y volvió 'dudosas' ~1.000 votaciones que en realidad eran cómodas (el motor pasó de pesimista a inseguro). La lección era la que anticipaba el plan: la asistencia no es pareja, es más alta en las votaciones que importan. El presentismo a secas es el piso a superar; el próximo escalón es modelar la asistencia CONDICIONADA. Mientras tanto el motor sin asistencia (Brier 0,011) sigue de default." },
    { fecha: "2026-07-10", titulo: "El sistema arranca: motor de agregación + Panel Nowcast", texto: "Decisión de foco: se pausa Diputados 2020-23 y se prioriza poner en marcha el sistema con lo que ya hay. Nace el motor de agregación institucional (roster + postura de bloque + desvío → probabilidad de aprobación como RANGO, no número seco, con quórum y mayorías) y un Panel Nowcast en HTML que se abre con doble clic: muestra el estado del sistema y deja simular una votación a mano. Prueba de que funciona: el mismo reparto de votos aprueba por mayoría simple y se cae por dos tercios." },
    { fecha: "2026-07-10", titulo: "Base regenerada con los linajes v2: la reclasificación es señal real", texto: "Se corrió entity_resolution + baseline sobre los 834.749 votos: la bolsa \"sin familia\" quedó efectivamente en 18,6% (antes 45,5%) y el baseline confirma que reconocer PERONISMO FEDERAL y PROGRESISMO mejora la predicción por espacio político (linaje 94,6%→95,0% en general, 90,5%→91,3% en disputadas). El voto-dirección por bloque no se mueve (97,8%). Cadena cerrada: se re-corrieron disciplina v2 (822.481 votos, set pivote 753), fichas (1.972 legisladores) y export (congreso.db 266,8 MB + 8 Excel por gobierno, que suman exactos los 5.333 actas / 834.749 votos)." },
    { fecha: "2026-07-02", titulo: "El desvío, versión 2: la silla vacía también cuenta (ADR-0004)", texto: "Valle redefinió la indisciplina de raíz: tres conductas (aprobar/rechazar/no acompañar), la línea del bloque emerge de la mayoría de TODOS sus escaños (ausentes incluidos), regla estricta en ambos sentidos, desempate por espacio político y desvío fraccional donde no hay línea. El índice pasó a medir indisciplina total (~19% promedio). Exclusiones curadas: presidentes de Diputados (no votan por costumbre — dominaban el top con falso desvío), suspendidos, placeholders. Pendiente anotado: herramienta que detecte y notifique licencias y suspensiones." },
    { fecha: "2026-07-10", titulo: "La bolsa de los \"sin familia\" bajó del 45% al 19%", texto: "Reclasificación de linajes (ADR-0005): nacieron PERONISMO FEDERAL y PROGRESISMO, y el bloque \"Justicialista\" —que fue tres cosas distintas según el año— ahora se asigna por fecha. El desempate del desvío v2 gana ~200 mil votos de universo. (Base ya regenerada; ver hito de arriba)." },
    { fecha: "2026-07-02", titulo: "Nace este tablero de control", texto: "El plan original (Word) quedó fusionado con todo lo hecho en un tablero vivo. Regla nueva: quien cambia algo en el repo, actualiza tablero_datos.js en el mismo PR." },
    { fecha: "2026-07-02", titulo: "La base entera, en formatos que cualquier analista puede abrir", texto: "Módulo nuevo datos/export: toda la canónica en un SQLite único y en Excel cortados por gobierno. Y quedó la definición oficial de votación \"disputada\" (resultado a ±5% de los votos emitidos: 190 en 25 años, validada con casos reales como las jubilaciones perdidas por 1 voto), más el margen exacto de cada acta para que cada analista use su propia vara." },
    { fecha: "2026-07-02", titulo: "Los díscolos, re-medidos con el Senado completo", texto: "Disciplina y fichas re-corridas sobre las 5 fuentes: 1.972 legisladores, desvío global 1,76%, y un set pivote de 112 nombres. Apareció el primer caso a auditar: una senadora con 75% de desvío justo en la ventana donde el padrón de bloques pide revisión humana." },
    { fecha: "2026-07-02", titulo: "El Senado entró al pipeline y se re-midió todo", texto: "La base canónica llegó a 835 mil votos (2001-2026, ambas cámaras). Primera medición del Senado con serie completa y bloques de época: es la cámara menos disciplinada en votaciones peleadas (95,7%)." },
    { fecha: "2026-07-02", titulo: "Cada voto del Senado con el bloque de SU época", texto: "El sitio oficial pintaba el bloque actual (anacrónico). Se reconstruyó el padrón histórico (Wikipedia + curación a mano con la semilla 2014): 100% de cobertura, 0 anacronismos. Perlita: un bloque correntino \"Frente de Todos\" de 2015 que no era el FdT nacional." },
    { fecha: "2026-07-01", titulo: "El agujero del Senado 2015-2023 quedó tapado", texto: "749 votaciones / 54 mil votos scrapeados de la fuente oficial, con ausentes nominales (sirve directo para asistencia/quórum). Validación contra un dataset independiente: 0 discrepancias en 43.684 votos comparados." },
    { fecha: "2026-07-01", titulo: "Los díscolos tienen número (gate 1 aprobado)", texto: "El índice de disciplina individual corrió sobre la historia completa: el legislador típico se desvía 1 de cada 100 votos, las bisagras están concentradas, y en 2024-26 son más que nunca. El replanteo quedó formalizado en ADR-0003." },
    { fecha: "2026-07-01", titulo: "1.935 fichas de legisladores, por período parlamentario", texto: "Cada legislador tiene su ficha: quién es, qué bloques integró, presentismo, perfil de voto y desvío — medido entre recambios del 10 de diciembre, porque cada recambio es una configuración nueva. Todo Excel entregable lleva ahora hoja Metodologia." },
    { fecha: "2026-06-30", titulo: "Replanteo: mirar al parlamentario uno por uno", texto: "El 99% de disciplina es un promedio que engaña: esconde a los 10-20 que definen las votaciones peleadas. Se descongeló voto_individual con otro objetivo: medir el desvío, no el voto medio." },
    { fecha: "2026-06-30", titulo: "El agente que lee la ley y le pone los temas", texto: "Un agente (Claude API) lee el PDF del proyecto y le asigna temas del diccionario controlado de 74 ids. Solo puede elegir de la lista, nunca pisa una etiqueta humana. Falta la corrida real con API key." },
    { fecha: "2026-06-29", titulo: "Diccionario de temas + base de proyectos + seguimiento de giros", texto: "Quedó la infraestructura del embudo: el extractor de giros validado en vivo en ambas cámaras, la base SQLite de proyectos que nunca duplica, y el vocabulario de 74 temas con código fijo." },
    { fecha: "2026-06-27", titulo: "La base cubre 25 años y las dos cámaras", texto: "Con la semilla de Andy Tow integrada, la base llegó a 781 mil votos (2001-2025). Primera medición sólida del Senado histórico: ~97% de disciplina." },
    { fecha: "2026-06-25", titulo: "Fase 0: el hallazgo que ordenó el proyecto", texto: "\"Votá con tu bloque\" acierta ~99%. Un modelo sofisticado no agrega nada ahí. El valor está en la asistencia, el embudo y la posición del bloque. Se montó toda la estructura de trabajo en paralelo (módulos, TABLERO, ESTADO, EN-HUMANO)." }
  ],

  // ============ PENDIENTES PRIORIZADOS ============
  pendientes: [
    { prioridad: 1, titulo: "Corrida en vivo del agente de taxonomías", detalle: "Solo falta la ANTHROPIC_API_KEY. Desbloquea el perfil temático (PLAN 1B.3) y la Consistencia Temática del Módulo A.", depende: "variables/proyecto" },
    { prioridad: 2, titulo: "datos/expedientes", detalle: "Ingesta masiva de proyectos: segunda llave del perfil temático y única llave de la red de co-firmas (Módulos B y C).", depende: "libre para reclamar" },
    { prioridad: 3, titulo: "Diputados 2020-2023", detalle: "El hueco de datos más grande que queda. Scraper de votaciones.hcdn.gob.ar (datos/diputados_oficial).", depende: "libre para reclamar" },
    { prioridad: 4, titulo: "datos/expedientes (nuevo frente Franco+Claude)", detalle: "Ingesta masiva de proyectos: enlace acta→expediente (18% de actas opacas por título), red de co-firmas para los Módulos B/C, e insumo del embudo. La auditoría del padrón quedó CERRADA 11-07 (17/17 validadas, ranking de díscolos certificado).", depende: "libre — próximo claim nuestro" },
    { prioridad: 5, titulo: "Embudo y asistencia/quórum", detalle: "Los dos módulos PRIORITARIOS del Nowcast siguen sin dueño.", depende: "libres para reclamar" },
    { prioridad: 6, titulo: "Piezas b-d de voto_individual", detalle: "Modelo de defección, recuento como distribución, pivotes por ley.", depende: "gate 1 aprobado ✓" }
  ],

  // ============ REVISIONES HUMANAS PENDIENTES ============
  revisiones: [
    { que: "✅ RESUELTO 11-07 — Padrón del Senado auditado: 17/17 filas validadas, cero errores", donde: "datos/senado/data/padron_manual_2015_2017.csv", detalle: "14 filas con desvío ≤5,6% (etiqueta trivialmente correcta) y 3 de desvío alto que son SEÑAL REAL: García (33,9% contra línea) desvía igual que toda el ala cristinista del FpV-PJ 2016-17 (F. Sagasti, Pilatti, Almirón) en las leyes de la era Macri — fractura interna del bloque, no error. El caveat del gate 1 (auditar díscolos) queda cerrado para Senado 2015-23: el ranking es confiable." },
    { que: "ADRs pendientes de formalizar", donde: "coordinacion/DECISIONES/", detalle: "(1) Wikipedia como fuente del padrón de bloques del Senado; (2) precedencia senado vs. argentinadatos en 2024-25 (hoy empatan)." }
  ],

  // ============ PRESUPUESTO (del plan original; vigente como estimación) ============
  presupuesto: {
    nota: "El Factor μ y el backtesting se resuelven dentro de PostgreSQL/Python, sin aumentar consumo de API. Gasto real actual: solo la suscripción de IA (fase de desarrollo in-house). La infraestructura 24/7 recién se contrata en la Etapa 4.",
    capex: [
      { item: "Suscripción IA (asistente de 