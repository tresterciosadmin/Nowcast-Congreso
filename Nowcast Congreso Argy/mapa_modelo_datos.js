// =====================================================================
// MAPA DEL MODELO - DATOS (GENERADO, no se edita a mano)
// =====================================================================
// Lo escribe: producto/dashboard/src/generar_mapa_modelo.py
// Lo lee:     MAPA-MODELO.html (el diseno, tambien fijo)
//
// Para cambiar QUE dice un nodo -> producto/dashboard/data/mapa_modelo_semantica.json
// Para cambiar el estado o el dueno de un modulo -> el `**Estado:**` /
//   `**Owner actual:**` de su README.md (de ahi sale por defecto).
// Un nodo puede declarar SU estado con `estado_declarado` + `estado_motivo`
//   (obligatorio) en la capa curada: el mapa dice cual de los dos esta mostrando.
// Despues: python producto/dashboard/src/generar_mapa_modelo.py
// =====================================================================

const MAPA_MODELO = {
  "meta": {
    "titulo": "Mapa del Modelo — Nowcast Legislativo Argentino",
    "subtitulo": "De donde sale la probabilidad de que un proyecto de ley sea aprobado",
    "para_que": "Uso interno del equipo. Cuando alguien pregunte «de dónde sale este número», la respuesta es señalar un nodo, no abrir quince archivos.",
    "no_es": "No es un tablero. TABLERO-CONTROL.html muestra plan y avance; esto muestra la maquinaria.",
    "verificado": "2026-08-20",
    "generado": "2026-08-25 19:09 UTC",
    "indice_archivos": 142,
    "rutas_declaradas": 58,
    "nodos": 101,
    "aristas": 144,
    "problemas": [
      "casos/README.md no tiene la linea `**Estado:**` (la usa este mapa y la usa el router de MAPA.md)",
      "docs/taxonomias/README.md no tiene la linea `**Estado:**` (la usa este mapa y la usa el router de MAPA.md)"
    ]
  },
  "etapas": [
    {
      "id": "fuentes",
      "nombre": "Fuentes",
      "orden": 0,
      "descripcion": "Las páginas y APIs oficiales de donde sale cada dato crudo. Nada de esto es nuestro."
    },
    {
      "id": "ingesta",
      "nombre": "Ingesta",
      "orden": 1,
      "descripcion": "Los scripts que bajan, parsean y normalizan. Tres de ellos corren solos en GitHub Actions."
    },
    {
      "id": "bases",
      "nombre": "Bases",
      "orden": 2,
      "descripcion": "Las bases propias: la canónica de votaciones, la de proyectos, el padrón. Fuente de verdad."
    },
    {
      "id": "variables",
      "nombre": "Variables",
      "orden": 3,
      "descripcion": "Las señales que entran al cálculo. Una carpeta por variable en variables/."
    },
    {
      "id": "origen",
      "nombre": "Cámara de origen",
      "orden": 4,
      "descripcion": "Donde nace el proyecto: se OBSERVA el dictamen y su carácter (A) y se calcula la mayoría (B)."
    },
    {
      "id": "revisora",
      "nombre": "Cámara revisora",
      "orden": 5,
      "descripcion": "La otra cámara: se OBSERVA el dictamen de sus comisiones (C) y se calcula la mayoría (D)."
    },
    {
      "id": "nowcast",
      "nombre": "Nowcast",
      "orden": 6,
      "descripcion": "El número publicado. Acá conviven las dos formulaciones."
    },
    {
      "id": "evaluacion",
      "nombre": "Evaluación",
      "orden": 7,
      "descripcion": "Contra qué se mide el número: Brier, skill, calibración, y la línea de base."
    }
  ],
  "grupos": [
    {
      "id": "condicionado_por_origen",
      "bloque": "revisora",
      "nombre": "Condicionado por lo que pasó en origen",
      "descripcion": "Con media sanción, las puertas A y B dejan de ser probabilidades y valen 1 (regla del colapso). Todo lo de adentro se lee bajo ese supuesto."
    }
  ],
  "roles": [
    {
      "id": "fuente",
      "nombre": "Fuente oficial",
      "forma": "rectangulo",
      "descripcion": "Página, API o dataset externo. No lo controlamos."
    },
    {
      "id": "script",
      "nombre": "Script",
      "forma": "hexagono",
      "descripcion": "Código del repo que transforma algo."
    },
    {
      "id": "dato",
      "nombre": "Base de datos / dato",
      "forma": "rectangulo",
      "descripcion": "Parquet, base SQLite, CSV o config que queda en disco."
    },
    {
      "id": "variable",
      "nombre": "Variable / etapa del cálculo",
      "forma": "circulo",
      "descripcion": "Una señal del modelo o un paso del cálculo. El tamaño indica jerarquía."
    },
    {
      "id": "resultado",
      "nombre": "Resultado / probabilidad",
      "forma": "rectangulo-grueso",
      "descripcion": "Un número publicable: la probabilidad con la que termina una cadena."
    }
  ],
  "tipos_arista": [
    {
      "id": "flujo",
      "nombre": "Flujo",
      "descripcion": "El dato pasa de un nodo al otro."
    },
    {
      "id": "config",
      "nombre": "Config",
      "descripcion": "Parametriza, no aporta el valor (env vars, catálogos, padrones de referencia)."
    },
    {
      "id": "calcula",
      "nombre": "Calcula",
      "descripcion": "Composición aritmética: el destino se calcula a partir del origen."
    },
    {
      "id": "alerta",
      "nombre": "Alerta",
      "descripcion": "Control o advertencia. NO es el valor publicado."
    },
    {
      "id": "condiciona",
      "nombre": "Condiciona",
      "descripcion": "El resultado de una cámara cambia el supuesto con el que se lee la otra. NO es flujo de datos: en código nada se pasa de un lado al otro."
    }
  ],
  "formulaciones": [
    {
      "id": "puertas",
      "nombre": "La formulación (única)",
      "formula": "P(sanción) = [A observada] · P(B | carácter del dictamen de origen) · [C observada] · P(D | carácter del dictamen de la revisora)",
      "archivo": "modelo/ensemble/PUERTA-D.md",
      "estado": "EN CURSO",
      "detalle": "La UNICA formulacion desde el 2026-08-22 (ADR-0012). Antes convivia con la v1 —P(llega al recinto) x P(mayoria | recinto)— que se dio de baja: `p_llega_recinto` media la chance de que el proyecto fuera TRATADO, y eso es agenda politica. A y C NO son probabilidades: son el CARACTER OBSERVADO del dictamen en cada camara, leido de los PDF de la Orden del Dia, y CONDICIONAN la votacion de su camara en vez de multiplicarla. Sin dato, el condicionante se encoge a 0 y queda la estimacion sin condicionar. Corre en `nowcast_puertas.py`.",
      "regla_clave": "Un paso que ya ocurrio deja de ser probabilidad y vale 1. Y el numero es CONDICIONAL a que las camaras voten: NO incluye la chance de que el proyecto sea tratado."
    }
  ],
  "caminos": [
    {
      "id": "mayoria",
      "nombre": "Cómo se arma P(mayoría)",
      "descripcion": "El otro factor: de la votación cruda al recuento como distribución, legislador por legislador.",
      "nodos": [
        "f_ckan",
        "s_ckan_to_canonical",
        "s_canonica_build",
        "d_canonica_votos",
        "s_entity_res",
        "d_canonica_resuelto",
        "s_bloque",
        "v_bloque",
        "c_roster_origen",
        "c_simular_origen",
        "c_p_mayoria_origen",
        "n_puertas"
      ]
    },
    {
      "id": "puertas",
      "nombre": "El camino por puertas A·B·C·D",
      "descripcion": "El reencuadre bicameral. A y C están parqueadas: se observan, no se predicen.",
      "nodos": [
        "g_A",
        "g_B",
        "g_C",
        "c_roster_revisora",
        "g_D",
        "n_colapso",
        "n_puertas"
      ]
    },
    {
      "id": "revisora",
      "nombre": "Cómo se hace posible la Puerta D",
      "descripcion": "Sin el padrón histórico del Senado y el enlace entre cámaras, la revisora no es rosteable y D no existe.",
      "nodos": [
        "f_wikipedia",
        "s_wiki_anexos",
        "s_padron_hist",
        "d_padron_sen_hist",
        "c_roster_revisora",
        "g_D",
        "n_puertas"
      ]
    },
    {
      "id": "evaluacion",
      "nombre": "Contra qué se mide el número (decisión pendiente)",
      "descripcion": "El backtest de la cadena completa contra `sancionado` real, con el p_sancion del embudo como vara.",
      "nodos": [
        "n_puertas",
        "e_backtest_cadena",
        "e_baseline_embudo",
        "e_backtest_embudo"
      ]
    }
  ],
  "trampas": [
    {
      "titulo": "La raíz git está un nivel arriba",
      "texto": "`.github/workflows/` vive en `Nowcast-Congreso/Nowcast-Congreso/`, no en `Nowcast Congreso Argy/`. Las rutas dentro de un workflow llevan el prefijo \"Nowcast Congreso Argy/\" entrecomillado (tiene espacios)."
    },
    {
      "titulo": "`periodo` significa dos cosas distintas",
      "texto": "En `variables/bloque` es un AÑO legislativo (entero). En `export`, `disciplina`, `ficha` y `asistencia` es el período de DOS AÑOS entre recambios («2019-2021»). Cruzarlas por nombre da cualquier cosa sin levantar un error."
    },
    {
      "titulo": "`ingesta_ckan.py` usa caché",
      "texto": "Salvo `REFRESH=1`, y lo dice bajito en el log. Además HCDN publica con ~5 semanas de atraso: el último mes siempre está incompleto."
    },
    {
      "titulo": "No publicar P(sanción) de origen Senado",
      "texto": "Sesgo de supervivencia: 48% contra 1,7% de Diputados, porque la base sólo tiene los proyectos del Senado que ya cruzaron a Diputados."
    },
    {
      "titulo": "La suite de tests son scripts, no pytest",
      "texto": "Se corren de a uno (`python <archivo>`). No correr pytest sobre todo el repo: aborta, y algunos chequeos pueden fallar sin que pytest lo note. Detalle en `tests/README.md`."
    },
    {
      "titulo": "«Pasa en el sandbox» no es «pasa»",
      "texto": "El sandbox corre otra versión de pandas: un faltante llega como None, NaN o pd.NA según el backend. Las corridas largas van a la PC de Valle, en PowerShell."
    },
    {
      "titulo": "Mitad del repo está en CRLF",
      "texto": "Si se reescribe un archivo hay que preservar el final de línea original, o el diff de git pasa a ser el archivo entero."
    },
    {
      "titulo": "Las cámaras NO son independientes",
      "texto": "`P = P_B · P_D` supone independencia y es falsa: un proyecto con media sanción holgada llega distinto a la revisora. El hook existe (`estimar_delta_paso_origen`) y está en 0. Revisión 25-08."
    },
    {
      "titulo": "12,5% de las leyes se sancionan SIN dictamen",
      "texto": "El sobre tablas (2/3 para incorporar al temario) tiene 53% de tasa de sanción contra 1,9% general, y 107 de sus 221 casos no tenían dictamen. La formulación por puertas asume comisión → recinto: una de cada ocho leyes salta la comisión."
    },
    {
      "titulo": "El quórum ignora las abstenciones",
      "texto": "`presentes = afirm + neg`: quien se abstiene está en el recinto y cuenta para el quórum, pero el modelo lo descarta junto con los ausentes. Subestima P donde el quórum es el límite."
    },
    {
      "titulo": "El épsilon es un clip, no un modelo",
      "texto": "`clip(P, 0,01, 0,99)` tapa la sobreconcentración que produce suponer votos independientes. El riesgo sistémico real (468 sesiones caídas por falta de quórum) pide un shock común compartido por simulación."
    },
    {
      "titulo": "El ICG es simétrico y la política no",
      "texto": "`ln(MM6/base)` da el mismo corrimiento subiendo 10% que bajando 10%. La asimetría (caída pesa ~2x) existía en el mecanismo 2 del ADR-0008 y se perdió al eliminarlo el 11-08."
    }
  ],
  "estados": [
    "HECHO",
    "EN CURSO",
    "PARCIAL",
    "PENDIENTE",
    "FUTURO",
    "REPLANTEADO"
  ],
  "nodes": [
    {
      "id": "f_ckan",
      "label": "CKAN HCDN",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 2,
      "host": "datos.hcdn.gob.ar",
      "que_es": "El portal de datos abiertos de Diputados. De acá salen las votaciones nominales 2011-2020 y el backfill de expedientes.",
      "notas": [
        "Dejó de actualizarse en 2020 para votaciones. Para lo posterior se usa argentinadatos.",
        "HCDN publica los expedientes con ~5 semanas de atraso."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_hcdn_tp",
      "label": "HCDN — Trámite Parlamentario",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 2,
      "host": "hcdn.gob.ar",
      "que_es": "El Trámite Parlamentario de Diputados: los proyectos nuevos con firmantes y giros a comisión. Lo lee el bot diario.",
      "notas": [
        "Es la única vía por la que el modelo ve los proyectos de las últimas semanas."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_senado",
      "label": "Senado — votaciones y DAE",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 2,
      "host": "senado.gob.ar",
      "que_es": "Actas de votación nominal del Senado y el DAE (Diario de Asuntos Entrados) con los expedientes.",
      "notas": [
        "El scraping cachea el HTML; la primera corrida tarda ~20 min."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_argentinadatos",
      "label": "argentinadatos",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 2,
      "host": "api.argentinadatos.com",
      "que_es": "API de terceros que cubre Diputados 2020-2025 y Senado 2024-2025, el tramo que CKAN dejó de publicar.",
      "notas": [
        "No tiene el bloque de cada senador: se resuelve cruzando con el padrón."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_wikipedia",
      "label": "Wikipedia (anexos)",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 1,
      "host": "es.wikipedia.org",
      "que_es": "Los anexos de senadores por período. Se usan para reconstruir el padrón histórico del Senado junto con la nómina oficial.",
      "notas": [
        "Un control cortó un error real: daba 90 bancas sobre 72 porque los nombres se escriben distinto en Wikipedia y en la nómina oficial."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_utdt",
      "label": "UTDT — ICG",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 1,
      "host": "utdt.edu",
      "que_es": "Índice de Confianza en el Gobierno. Es la única variable NO procedimental del modelo: el clima político.",
      "notas": [
        "Entra rezagado un mes (anti-leakage duro): el proyecto presentado en M ve el ICG de M-1."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_decada",
      "label": "Década Votada / legislAr",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 1,
      "que_es": "El dataset de Andy Tow. Semilla histórica de UN SOLO USO para las votaciones anteriores a 2011 (ADR-0002).",
      "notas": [
        "No se depende de él en vivo. Se exportó una vez y se normalizó."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "f_excel_franco",
      "label": "Excel curado (Franco)",
      "rol": "fuente",
      "etapa": "fuentes",
      "jerarquia": 1,
      "que_es": "Congreso_25-27.xlsx: los votos 2026 de ambas cámaras cargados a mano, con bloque del Senado, provincia y mandato.",
      "notas": [
        "Fuente VIVA: Franco la sigue completando. Tiene máxima precedencia en la canónica."
      ],
      "estado": "HECHO",
      "owner": "externo",
      "estado_fuente": "—",
      "estado_texto": "fuente externa: no la controlamos"
    },
    {
      "id": "s_bot_diario",
      "label": "bot-diario.yml",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo_externo": ".github/workflows/bot-diario.yml",
      "cron": "0 10 * * 1-6",
      "cron_humano": "07:00 ARG, lunes a sábado",
      "que_es": "El workflow que corre el bot de recolección todos los días: trae proyectos y votaciones nuevas de ambas cámaras con upsert idempotente.",
      "notas": [
        "Vive en la RAÍZ GIT, un nivel arriba del proyecto. Las rutas adentro llevan el prefijo \"Nowcast Congreso Argy/\" entrecomillado."
      ],
      "modulo": "datos/bot_recoleccion",
      "existe": null,
      "fuera_del_arbol": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).",
      "estado_fuente": "datos/bot_recoleccion/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_icg_mensual",
      "label": "icg-mensual.yml",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo_externo": ".github/workflows/icg-mensual.yml",
      "cron": "0 12 5 * *",
      "cron_humano": "día 5 de cada mes, 09:00 ARG",
      "que_es": "Baja el ICG del mes de la UTDT y actualiza icg_mensual.csv.",
      "notas": [
        "Vive en la raíz git."
      ],
      "modulo": "variables/proyecto",
      "existe": null,
      "fuera_del_arbol": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "s_padron_vivo",
      "label": "padron-vivo.yml",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo_externo": ".github/workflows/padron-vivo.yml",
      "cron": "0 11 * * 1",
      "cron_humano": "lunes 08:00 ARG",
      "que_es": "Corre vigilar_padron.py: chequea si cambió la composición de las cámaras (reemplazos, renuncias, bancas vacantes) y avisa.",
      "notas": [
        "Vive en la raíz git."
      ],
      "modulo": "datos/padron",
      "existe": null,
      "fuera_del_arbol": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "s_ckan_to_canonical",
      "label": "ckan → canónico",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/ckan_diputados/src/to_canonical.py",
      "modulo": "datos/ckan_diputados",
      "que_es": "Baja cabecera + detalle de las votaciones nominales de Diputados 2011-2020 de CKAN y las traduce al esquema canónico.",
      "existe": true,
      "loc": 69,
      "simbolos": [
        {
          "nombre": "_req",
          "tipo": "funcion",
          "linea": 19,
          "doc": null
        },
        {
          "nombre": "_csv",
          "tipo": "funcion",
          "linea": 27,
          "doc": null
        },
        {
          "nombre": "_norm_voto",
          "tipo": "funcion",
          "linea": 31,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 39,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO. **La migración desde `fase0/` ya se hizo** (`src/to_canonical.py`",
      "estado_fuente": "datos/ckan_diputados/README.md",
      "owner": "cerrado"
    },
    {
      "id": "s_ingesta_ckan",
      "label": "ingesta_ckan.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo": "datos/expedientes/src/ingesta_ckan.py",
      "modulo": "datos/expedientes",
      "que_es": "Trae de CKAN el registro de todo lo PRESENTADO (no sólo lo votado): título, autor, tipo, fecha y cadena de vida del expediente. Es el denominador del embudo.",
      "notas": [
        "⚠ Usa CACHÉ salvo REFRESH=1, y lo dice bajito en el log. Si la ingesta «trae menos de lo esperado», es esto.",
        "HCDN publica con ~5 semanas de atraso: el último mes siempre está incompleto."
      ],
      "existe": true,
      "loc": 191,
      "simbolos": [
        {
          "nombre": "_get",
          "tipo": "funcion",
          "linea": 69,
          "doc": null
        },
        {
          "nombre": "_url_recurso",
          "tipo": "funcion",
          "linea": 83,
          "doc": null
        },
        {
          "nombre": "_descargar",
          "tipo": "funcion",
          "linea": 91,
          "doc": null
        },
        {
          "nombre": "_csv",
          "tipo": "funcion",
          "linea": 104,
          "doc": "Lectura defensiva: encoding con BOM, filas rotas se saltean y reportan."
        },
        {
          "nombre": "_fecha",
          "tipo": "funcion",
          "linea": 112,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 116,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_tp_diputados",
      "label": "tp_diputados.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/bot_recoleccion/src/tp_diputados.py",
      "modulo": "datos/bot_recoleccion",
      "que_es": "Scrapea el Trámite Parlamentario de Diputados: proyectos nuevos con firmantes y giros a comisión.",
      "existe": true,
      "loc": 244,
      "simbolos": [
        {
          "nombre": "_pedir",
          "tipo": "funcion",
          "linea": 75,
          "doc": null
        },
        {
          "nombre": "_fecha_iso",
          "tipo": "funcion",
          "linea": 95,
          "doc": null
        },
        {
          "nombre": "_limpiar",
          "tipo": "funcion",
          "linea": 102,
          "doc": null
        },
        {
          "nombre": "_firmantes",
          "tipo": "funcion",
          "linea": 106,
          "doc": "'RUIZ, YAMILA; VANCSIK, DANIEL Y HERRERA AHUAD, OSCAR A.:' -> lista."
        },
        {
          "nombre": "parse_tp",
          "tipo": "funcion",
          "linea": 119,
          "doc": "Devuelve (identidad, filas). Identidad={numero, fecha}. Cada <p> con un"
        },
        {
          "nombre": "_antes_de",
          "tipo": "funcion",
          "linea": 177,
          "doc": "True si el1 aparece antes que el2 en el orden del documento."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).",
      "estado_fuente": "datos/bot_recoleccion/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_dae_senado",
      "label": "dae_senado.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/bot_recoleccion/src/dae_senado.py",
      "modulo": "datos/bot_recoleccion",
      "que_es": "Scrapea el Diario de Asuntos Entrados del Senado: la contraparte de TP para la cámara alta.",
      "existe": true,
      "loc": 240,
      "simbolos": [
        {
          "nombre": "_norm",
          "tipo": "funcion",
          "linea": 63,
          "doc": null
        },
        {
          "nombre": "_pedir",
          "tipo": "funcion",
          "linea": 76,
          "doc": null
        },
        {
          "nombre": "parse_dae",
          "tipo": "funcion",
          "linea": 99,
          "doc": "Devuelve (identidad_del_dae, filas). Identidad = {numero, anio} del DAE"
        },
        {
          "nombre": "_form_dae",
          "tipo": "funcion",
          "linea": 148,
          "doc": "Arma el POST del buscador de DAE (todos los campos del form, pisando"
        },
        {
          "nombre": "traer_dae",
          "tipo": "funcion",
          "linea": 176,
          "doc": "Trae un DAE puntual: primero por form POST; plan B, rutas GET conocidas."
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 198,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).",
      "estado_fuente": "datos/bot_recoleccion/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_bot_votaciones",
      "label": "votaciones.py (bot)",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/bot_recoleccion/src/votaciones.py",
      "modulo": "datos/bot_recoleccion",
      "que_es": "La pata de votaciones del bot diario: trae las actas nuevas de ambas cámaras.",
      "existe": true,
      "loc": 212,
      "simbolos": [
        {
          "nombre": "_pedir",
          "tipo": "funcion",
          "linea": 67,
          "doc": "GET con backoff exponencial. Devuelve [] si la API responde 404 (año sin"
        },
        {
          "nombre": "_campo",
          "tipo": "funcion",
          "linea": 87,
          "doc": "Primer campo presente y no vacío, buscado POR NOMBRE (no por posición):"
        },
        {
          "nombre": "parse_actas",
          "tipo": "funcion",
          "linea": 97,
          "doc": "Normaliza la respuesta a filas mínimas para el radar del bot. Defensivo:"
        },
        {
          "nombre": "_leer_estado",
          "tipo": "funcion",
          "linea": 124,
          "doc": null
        },
        {
          "nombre": "_guardar_estado",
          "tipo": "funcion",
          "linea": 133,
          "doc": null
        },
        {
          "nombre": "revisar",
          "tipo": "funcion",
          "linea": 138,
          "doc": "Trae las actas de cada (cámara, año) y devuelve SOLO las que no estaban."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).",
      "estado_fuente": "datos/bot_recoleccion/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_argdatos",
      "label": "argentinadatos → canónico",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/argentinadatos/src/to_canonical.py",
      "modulo": "datos/argentinadatos",
      "que_es": "Normaliza Diputados 2020-2025 y Senado 2024-2025 al mismo esquema que CKAN.",
      "existe": true,
      "loc": 169,
      "simbolos": [
        {
          "nombre": "_get",
          "tipo": "funcion",
          "linea": 23,
          "doc": null
        },
        {
          "nombre": "_key",
          "tipo": "funcion",
          "linea": 31,
          "doc": null
        },
        {
          "nombre": "_voto",
          "tipo": "funcion",
          "linea": 35,
          "doc": null
        },
        {
          "nombre": "_clave",
          "tipo": "funcion",
          "linea": 45,
          "doc": null
        },
        {
          "nombre": "_padron_senado",
          "tipo": "funcion",
          "linea": 50,
          "doc": "Lee los CSV versionados del padrón del Senado, en orden de precedencia."
        },
        {
          "nombre": "_bloque_sen",
          "tipo": "funcion",
          "linea": 87,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (integrado 2026-07-11) · reabierto 2026-08-06 por el bloque del Senado",
      "estado_fuente": "datos/argentinadatos/README.md",
      "owner": "Claude (con Valle), desde 2026-08-06"
    },
    {
      "id": "s_scrape_senado",
      "label": "scrape_votaciones.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/senado/src/scrape_votaciones.py",
      "modulo": "datos/senado",
      "que_es": "Scrapea las votaciones nominales del Senado desde senado.gob.ar. Tapó el hueco 2015-2023 (749 actas / 53.910 votos).",
      "notas": [
        "Cachea el HTML. La primera corrida tarda ~20 min."
      ],
      "existe": true,
      "loc": 422,
      "simbolos": [
        {
          "nombre": "_norm",
          "tipo": "funcion",
          "linea": 90,
          "doc": "MAYÚSCULAS sin tildes ni espacios repetidos (para comparar headers)."
        },
        {
          "nombre": "_voto",
          "tipo": "funcion",
          "linea": 96,
          "doc": null
        },
        {
          "nombre": "_fetch",
          "tipo": "funcion",
          "linea": 108,
          "doc": null
        },
        {
          "nombre": "_resultado_lista",
          "tipo": "funcion",
          "linea": 132,
          "doc": "La celda \"Resultado\" del listado concatena signo + detalle"
        },
        {
          "nombre": "_form_payload",
          "tipo": "funcion",
          "linea": 150,
          "doc": "Encuentra el form del buscador y arma el POST con TODOS sus campos"
        },
        {
          "nombre": "_parse_listado",
          "tipo": "funcion",
          "linea": 175,
          "doc": "Filas del listado anual. Tabla ubicada por firma de encabezados."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (2015–2023 completo; quedan filas `REVISAR` en el padrón manual)",
      "estado_fuente": "datos/senado/README.md",
      "owner": "Claude+Franco (2026-07-01/02)"
    },
    {
      "id": "s_wiki_anexos",
      "label": "bajar_anexos_wiki.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/senado/src/bajar_anexos_wiki.py",
      "modulo": "datos/senado",
      "que_es": "Baja los anexos de senadores de Wikipedia para reconstruir el padrón histórico del Senado.",
      "existe": true,
      "loc": 53,
      "simbolos": [
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 27,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (2015–2023 completo; quedan filas `REVISAR` en el padrón manual)",
      "estado_fuente": "datos/senado/README.md",
      "owner": "Claude+Franco (2026-07-01/02)"
    },
    {
      "id": "s_decada_csv",
      "label": "from_csv.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/decada_votada/src/from_csv.py",
      "modulo": "datos/decada_votada",
      "que_es": "Normaliza la semilla de La Década Votada (Dip 2001-2010 + Sen 2004-2014) al esquema canónico. Un solo uso.",
      "existe": true,
      "loc": 76,
      "simbolos": [
        {
          "nombre": "fix",
          "tipo": "funcion",
          "linea": 14,
          "doc": null
        },
        {
          "nombre": "_read",
          "tipo": "funcion",
          "linea": 19,
          "doc": null
        },
        {
          "nombre": "parse",
          "tipo": "funcion",
          "linea": 21,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 59,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO — semilla integrada vía CSV (Diputados 2001-2010 + Senado 2004-2014).",
      "estado_fuente": "datos/decada_votada/README.md",
      "owner": "Claude+Franco (cerrado 2026-06-29)"
    },
    {
      "id": "s_manual_2026",
      "label": "manual_2026 → canónico",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/manual_2026/src/to_canonical.py",
      "modulo": "datos/manual_2026",
      "que_es": "Integra el Excel curado por Franco al esquema canónico, con máxima precedencia sobre las otras fuentes.",
      "existe": true,
      "loc": 72,
      "simbolos": [
        {
          "nombre": "_slug",
          "tipo": "funcion",
          "linea": 12,
          "doc": null
        },
        {
          "nombre": "_voto",
          "tipo": "funcion",
          "linea": 15,
          "doc": null
        },
        {
          "nombre": "parse_hoja",
          "tipo": "funcion",
          "linea": 26,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 56,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (primera carga). Fuente viva: Franco la sigue completando a mano.",
      "estado_fuente": "datos/manual_2026/README.md",
      "owner": "—"
    },
    {
      "id": "s_ingesta_icg",
      "label": "ingesta_icg.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "variables/proyecto/src/ingesta_icg.py",
      "modulo": "variables/proyecto",
      "que_es": "Baja el Índice de Confianza en el Gobierno de la UTDT y arma la serie mensual.",
      "existe": true,
      "loc": 447,
      "simbolos": [
        {
          "nombre": "ICGError",
          "tipo": "clase",
          "linea": 63,
          "doc": "Error específico de la ingesta del ICG."
        },
        {
          "nombre": "_get",
          "tipo": "funcion",
          "linea": 67,
          "doc": "GET con backoff exponencial (directiva de resiliencia)."
        },
        {
          "nombre": "encontrar_link_excel",
          "tipo": "funcion",
          "linea": 83,
          "doc": "Scrapea la página de descarga y devuelve la URL vigente del .xls de la serie."
        },
        {
          "nombre": "_normalizar_columna",
          "tipo": "funcion",
          "linea": 105,
          "doc": null
        },
        {
          "nombre": "parsear_excel",
          "tipo": "funcion",
          "linea": 109,
          "doc": "Normaliza el Excel de UTDT a (fecha, anio, mes, icg). Parsing defensivo."
        },
        {
          "nombre": "_extraer_transpuesto",
          "tipo": "funcion",
          "linea": 140,
          "doc": "Layout transpuesto: fila de fechas + fila 'ICG' con los valores."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "s_bajar_nomina",
      "label": "bajar_nomina.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/padron/src/bajar_nomina.py",
      "modulo": "datos/padron",
      "que_es": "Baja la nómina oficial de legisladores: quién ocupa cada banca y en qué ventana de mandato.",
      "existe": true,
      "loc": 266,
      "simbolos": [
        {
          "nombre": "_get",
          "tipo": "funcion",
          "linea": 85,
          "doc": null
        },
        {
          "nombre": "nomina_diputados",
          "tipo": "funcion",
          "linea": 99,
          "doc": "Una fila por (diputado, tramo de bloque). Defensivo: campos por nombre,"
        },
        {
          "nombre": "composicion_oficial",
          "tipo": "funcion",
          "linea": 144,
          "doc": "Composición ACTUAL de bloques, del CKAN oficial de HCDN."
        },
        {
          "nombre": "_periodo_a_fechas",
          "tipo": "funcion",
          "linea": 171,
          "doc": "'2025-2029' -> ('2025-12-10', '2029-12-09'). Los mandatos arrancan el 10-dic."
        },
        {
          "nombre": "completar_con_oficial",
          "tipo": "funcion",
          "linea": 180,
          "doc": "Suma al padrón las bancas vigentes que la API no trajo."
        },
        {
          "nombre": "_norm_txt",
          "tipo": "funcion",
          "linea": 215,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "s_vigilar_padron",
      "label": "vigilar_padron.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/padron/src/vigilar_padron.py",
      "modulo": "datos/padron",
      "que_es": "Control semanal: detecta si cambió la composición de las cámaras (recambio del 10-dic, reemplazos, renuncias, vacantes) y avisa.",
      "es_control": true,
      "existe": true,
      "loc": 392,
      "simbolos": [
        {
          "nombre": "_vigentes",
          "tipo": "funcion",
          "linea": 80,
          "doc": "Filas con desde <= F <= hasta. Parsing defensivo: las fechas ilegibles"
        },
        {
          "nombre": "padron_versionado",
          "tipo": "funcion",
          "linea": 89,
          "doc": "El contrato que hoy consume el modelo: data/padron_<camara>.csv."
        },
        {
          "nombre": "nomina_fresca",
          "tipo": "funcion",
          "linea": 102,
          "doc": "Snapshot ACTUAL de la cámara, normalizado igual que el padrón."
        },
        {
          "nombre": "comparar",
          "tipo": "funcion",
          "linea": 137,
          "doc": "Altas, bajas y pases entre el padrón versionado y el snapshot fresco."
        },
        {
          "nombre": "huella",
          "tipo": "funcion",
          "linea": 180,
          "doc": "Hash estable del diff: si no cambió, no se vuelve a avisar."
        },
        {
          "nombre": "_hash_archivo",
          "tipo": "funcion",
          "linea": 187,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "s_padron_hist",
      "label": "padron_senado_historico.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/padron/src/padron_senado_historico.py",
      "modulo": "datos/padron",
      "que_es": "Reconstruye el padrón del Senado con historia cruzando nómina oficial y Wikipedia: 243 tramos, 176 senadores, 2017→2031. Es lo que hace rosteable a la Puerta D.",
      "existe": true,
      "loc": 395,
      "simbolos": [
        {
          "nombre": "_leer_csv",
          "tipo": "funcion",
          "linea": 101,
          "doc": null
        },
        {
          "nombre": "_tramos_wiki",
          "tipo": "funcion",
          "linea": 113,
          "doc": null
        },
        {
          "nombre": "_tramos_vigentes",
          "tipo": "funcion",
          "linea": 129,
          "doc": null
        },
        {
          "nombre": "_reconciliar_claves",
          "tipo": "funcion",
          "linea": 140,
          "doc": "Unifica la clave de la misma persona escrita distinto en cada fuente."
        },
        {
          "nombre": "_fusionar_consecutivos",
          "tipo": "funcion",
          "linea": 209,
          "doc": "Une tramos contiguos del mismo senador con el mismo bloque."
        },
        {
          "nombre": "_resolver_solapes",
          "tipo": "funcion",
          "linea": 239,
          "doc": "Si un senador tiene dos tramos que se pisan, gana el de mejor prioridad."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "s_canonica_build",
      "label": "build.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 3,
      "archivo": "datos/canonica/src/build.py",
      "modulo": "datos/canonica",
      "que_es": "Unifica TODAS las fuentes de votaciones en una sola base, deduplica y aplica precedencia. El corazón de la capa de datos.",
      "existe": true,
      "loc": 87,
      "simbolos": [
        {
          "nombre": "_load",
          "tipo": "funcion",
          "linea": 22,
          "doc": null
        },
        {
          "nombre": "_checks",
          "tipo": "funcion",
          "linea": 31,
          "doc": null
        },
        {
          "nombre": "_sample_jsonschema",
          "tipo": "funcion",
          "linea": 39,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 50,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "s_entity_res",
      "label": "entity_resolution.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo": "datos/canonica/src/entity_resolution.py",
      "modulo": "datos/canonica",
      "que_es": "Resuelve identidades: el mismo legislador escrito de cinco maneras distintas pasa a ser una sola persona con un id estable.",
      "existe": true,
      "loc": 243,
      "simbolos": [
        {
          "nombre": "_strip",
          "tipo": "funcion",
          "linea": 124,
          "doc": null
        },
        {
          "nombre": "_name_key",
          "tipo": "funcion",
          "linea": 128,
          "doc": null
        },
        {
          "nombre": "_leg_id",
          "tipo": "funcion",
          "linea": 133,
          "doc": null
        },
        {
          "nombre": "_bloque_norm",
          "tipo": "funcion",
          "linea": 136,
          "doc": null
        },
        {
          "nombre": "_linaje_vec",
          "tipo": "funcion",
          "linea": 178,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 200,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "s_upsert_bot",
      "label": "upsert_bot.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo": "datos/proyectos/src/upsert_bot.py",
      "modulo": "datos/proyectos",
      "que_es": "Carga lo que trae el bot a proyectos.db con merge por campo. Desde el 07-08-2026 el bot por fin ENTREGA (antes recolectaba en archivos que nadie leía).",
      "existe": true,
      "loc": 310,
      "simbolos": [
        {
          "nombre": "_norm",
          "tipo": "funcion",
          "linea": 57,
          "doc": null
        },
        {
          "nombre": "_ahora",
          "tipo": "funcion",
          "linea": 62,
          "doc": null
        },
        {
          "nombre": "catalogo_comisiones",
          "tipo": "funcion",
          "linea": 66,
          "doc": "Nombres conocidos, del mas largo al mas corto (criterio de Franco)."
        },
        {
          "nombre": "separar_giros_tp",
          "tipo": "funcion",
          "linea": 81,
          "doc": "El campo `giros` del TP viene SIN separadores. Devuelve la lista."
        },
        {
          "nombre": "separar_giros_dae",
          "tipo": "funcion",
          "linea": 99,
          "doc": "El DAE si trae separador: 'DE MINERIA... - DE PRESUPUESTO Y HACIENDA -'."
        },
        {
          "nombre": "denom_dae",
          "tipo": "funcion",
          "linea": 114,
          "doc": "'S-2/26-PL' -> '0002-S-2026'; 'PE-8/26-PL' -> '0008-PE-2026'."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "s_migrar_ckan",
      "label": "migrar_ckan.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/proyectos/src/migrar_ckan.py",
      "modulo": "datos/proyectos",
      "que_es": "Carga el backfill de CKAN a proyectos.db. Junto con upsert_bot rehace la base en ~1 min (no viaja a git).",
      "existe": true,
      "loc": 288,
      "simbolos": [
        {
          "nombre": "_ahora",
          "tipo": "funcion",
          "linea": 42,
          "doc": null
        },
        {
          "nombre": "_leer",
          "tipo": "funcion",
          "linea": 46,
          "doc": "Lee un parquet del contrato de datos/expedientes. Tolerante a faltantes."
        },
        {
          "nombre": "_conectar_fresca",
          "tipo": "funcion",
          "linea": 67,
          "doc": "Base NUEVA en disco local. Es un derivado: se rehace, no se repara."
        },
        {
          "nombre": "_publicar",
          "tipo": "funcion",
          "linea": 79,
          "doc": "Copia la base terminada del disco local a su lugar definitivo."
        },
        {
          "nombre": "_ids_a_denom",
          "tipo": "funcion",
          "linea": 86,
          "doc": "proyecto_id (HCDN...) -> denominador (NNNN-X-AAAA)."
        },
        {
          "nombre": "_insertar",
          "tipo": "funcion",
          "linea": 91,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "s_cuarentena",
      "label": "cuarentena.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/proyectos/src/cuarentena.py",
      "modulo": "datos/proyectos",
      "que_es": "Una fila rara no entra a la base principal: va a una base aparte. Diseño de Valle, para que lo dudoso no contamine en silencio.",
      "es_control": true,
      "existe": true,
      "loc": 192,
      "simbolos": [
        {
          "nombre": "Avalancha",
          "tipo": "clase",
          "linea": 69,
          "doc": "Demasiadas filas en cuarentena: la fuente cambió, no es una anomalía."
        },
        {
          "nombre": "_ahora",
          "tipo": "funcion",
          "linea": 73,
          "doc": null
        },
        {
          "nombre": "Cuarentena",
          "tipo": "clase",
          "linea": 77,
          "doc": "Acumula lo dudoso y lo escribe aparte. Nunca toca `proyectos.db`."
        },
        {
          "nombre": "resumen",
          "tipo": "funcion",
          "linea": 154,
          "doc": "Qué hay esperando revisión. Para el informe y para los humanos."
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 171,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "s_verificar",
      "label": "verificar.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo": "datos/proyectos/src/verificar.py",
      "modulo": "datos/proyectos",
      "que_es": "14 invariantes que CORTAN la carga si la base no cuadra. Incluye el control de cohorte, que invoca al embudo como proceso y compara.",
      "es_control": true,
      "notas": [
        "Si el medidor no corre, el control FALLA. No se saltea en silencio."
      ],
      "existe": true,
      "loc": 237,
      "simbolos": [
        {
          "nombre": "Control",
          "tipo": "clase",
          "linea": 55,
          "doc": "Acumula resultados. Un solo FALLA hace que el proceso corte."
        },
        {
          "nombre": "_abrir",
          "tipo": "funcion",
          "linea": 95,
          "doc": null
        },
        {
          "nombre": "controles_base",
          "tipo": "funcion",
          "linea": 106,
          "doc": "`etapa`: 'ckan' = recien migrado, sin el bot todavia · 'completa' = con bot."
        },
        {
          "nombre": "control_cohorte",
          "tipo": "funcion",
          "linea": 181,
          "doc": "La prueba fuerte: las dos rutas tienen que coincidir en lo que comparten."
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 223,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "s_giros",
      "label": "giros.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/seguimiento/src/giros.py",
      "modulo": "datos/seguimiento",
      "que_es": "Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. NO descubre proyectos nuevos.",
      "existe": true,
      "loc": 434,
      "simbolos": [
        {
          "nombre": "Giro",
          "tipo": "clase",
          "linea": 75,
          "doc": null
        },
        {
          "nombre": "Movimiento",
          "tipo": "clase",
          "linea": 84,
          "doc": null
        },
        {
          "nombre": "Firmante",
          "tipo": "clase",
          "linea": 92,
          "doc": null
        },
        {
          "nombre": "FichaExpediente",
          "tipo": "clase",
          "linea": 99,
          "doc": null
        },
        {
          "nombre": "_norm",
          "tipo": "funcion",
          "linea": 122,
          "doc": null
        },
        {
          "nombre": "_sin_tildes_upper",
          "tipo": "funcion",
          "linea": 126,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (primer extractor de giros, ambas cámaras, validado contra fixtures).",
      "estado_fuente": "datos/seguimiento/README.md",
      "owner": "—"
    },
    {
      "id": "s_enlace_senado",
      "label": "enlace_senado.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 2,
      "archivo": "datos/expedientes/src/enlace_senado.py",
      "modulo": "datos/expedientes",
      "que_es": "El puente entre cámaras: enlaza el acta de votación con su expediente y detecta los proyectos votados en LAS DOS cámaras. Sin esto no hay Puerta D.",
      "notas": [
        "Hallazgo del 08-08: el expediente estaba escrito DENTRO del título del acta en 2.229 casos. El Senado pasó de 8,1% a 72,4% de actas identificadas sin scrapear nada."
      ],
      "existe": true,
      "loc": 576,
      "simbolos": [
        {
          "nombre": "_vacio",
          "tipo": "funcion",
          "linea": 111,
          "doc": "¿Es un faltante, en cualquiera de sus disfraces?"
        },
        {
          "nombre": "normalizar_expediente",
          "tipo": "funcion",
          "linea": 132,
          "doc": "Lleva cualquiera de los dos formatos al denominador canónico NNNN-XX-AAAA."
        },
        {
          "nombre": "expediente_en_titulo",
          "tipo": "funcion",
          "linea": 170,
          "doc": "Rescata el expediente escrito dentro del título del acta."
        },
        {
          "nombre": "od_en_titulo",
          "tipo": "funcion",
          "linea": 193,
          "doc": "Número de Orden del Día escrito en el título, sin ceros a la izquierda."
        },
        {
          "nombre": "mapa_od",
          "tipo": "funcion",
          "linea": 207,
          "doc": "(año de publicación, nº de O.D.) -> proyecto_id, **sólo claves unívocas**."
        },
        {
          "nombre": "prefijo",
          "tipo": "funcion",
          "linea": 235,
          "doc": "Letra del denominador ya normalizado ('0038-CD-2022' -> 'CD')."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_actas_ley",
      "label": "actas_ley.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/expedientes/src/actas_ley.py",
      "modulo": "datos/expedientes",
      "que_es": "Filtra qué actas son de LEY. Excluye designaciones y pliegos del Senado (cónsules, jueces) que vienen tipeados como LEY.",
      "es_control": true,
      "notas": [
        "Cada corrida escribe AUDITORIA-designaciones-excluidas.md, una lista revisable en castellano, a pedido de Valle que desconfiaba del regex."
      ],
      "existe": true,
      "loc": 190,
      "simbolos": [
        {
          "nombre": "es_designacion",
          "tipo": "funcion",
          "linea": 77,
          "doc": "True si el título es una designación/pliego/acuerdo del Senado (NO ley)."
        },
        {
          "nombre": "_escribir_auditoria",
          "tipo": "funcion",
          "linea": 91,
          "doc": "Escribe la lista, en castellano, de las designaciones que el filtro sacó del"
        },
        {
          "nombre": "actas_de_ley",
          "tipo": "funcion",
          "linea": 125,
          "doc": "Conjunto de `acta_id` cuyo expediente es de ley (LEY/MENSAJE)."
        },
        {
          "nombre": "filtrar_votos_a_ley",
          "tipo": "funcion",
          "linea": 166,
          "doc": "Deja en `votos` sólo las filas de actas de ley. Si `actas_ley` es None,"
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_export_base",
      "label": "export_base.py",
      "rol": "script",
      "etapa": "ingesta",
      "jerarquia": 1,
      "archivo": "datos/export/src/export_base.py",
      "modulo": "datos/export",
      "que_es": "La canónica en formatos consultables: un SQLite único para el programa y Excel por gobierno para humanos. Sólo LEE.",
      "existe": true,
      "loc": 298,
      "simbolos": [
        {
          "nombre": "gobierno",
          "tipo": "funcion",
          "linea": 71,
          "doc": null
        },
        {
          "nombre": "calcular_disputada",
          "tipo": "funcion",
          "linea": 86,
          "doc": "Agrega n_emitidos, umbral_aprobacion y disputada (definición ±5% del umbral)."
        },
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 113,
          "doc": null
        },
        {
          "nombre": "hoja_metodologia",
          "tipo": "funcion",
          "linea": 222,
          "doc": null
        },
        {
          "nombre": "export_db",
          "tipo": "funcion",
          "linea": 227,
          "doc": "Escribe a un temporal local y copia al final: SQLite falla sobre carpetas"
        },
        {
          "nombre": "export_xlsx",
          "tipo": "funcion",
          "linea": 257,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 (falta corrida completa de los Excel en PC del equipo)",
      "estado_fuente": "datos/export/README.md",
      "owner": "Claude+Valle (desde 2026-07-02)"
    },
    {
      "id": "d_canonica_actas",
      "label": "actas_canonico.parquet",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "ruta_declarada": "CANONICA_ACTAS",
      "que_es": "Una fila por votación nominal. 6.231 actas, 2001-2026, ambas cámaras.",
      "archivo": "datos/canonica/data/clean/actas_canonico.parquet",
      "existe": true,
      "modulo": "datos/canonica",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "d_canonica_votos",
      "label": "votos_canonico.parquet",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 3,
      "ruta_declarada": "CANONICA_VOTOS",
      "que_es": "La tabla madre: un voto por fila. 1.016.632 votos. De acá leen variables/ y modelo/.",
      "archivo": "datos/canonica/data/clean/votos_canonico.parquet",
      "existe": true,
      "modulo": "datos/canonica",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "d_canonica_resuelto",
      "label": "votos_resuelto.parquet",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "ruta_declarada": "CANONICA_VOTOS_RESUELTO",
      "que_es": "Los mismos votos con las identidades ya resueltas: cada legislador con un id estable a través de las fuentes.",
      "archivo": "datos/canonica/data/clean/votos_resuelto.parquet",
      "existe": true,
      "modulo": "datos/canonica",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "d_acta_expediente",
      "label": "acta_expediente.parquet",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "ruta_declarada": "EXPEDIENTES_ACTA_EXP",
      "que_es": "El enlace acta → expediente. Es lo que permite saber qué proyecto se votó en cada acta, y cruzar las dos cámaras.",
      "notas": [
        "Enlace 89% global. En el Senado, 72,4% de actas identificadas."
      ],
      "archivo": "datos/expedientes/data/clean/acta_expediente.parquet",
      "existe": true,
      "modulo": "datos/expedientes",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "d_tp_entradas",
      "label": "tp_entradas.parquet",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "BOT_TP_ENTRADAS",
      "que_es": "Lo que trajo el bot del Trámite Parlamentario antes de entrar a proyectos.db.",
      "archivo": "datos/bot_recoleccion/data/clean/tp_entradas.parquet",
      "existe": true,
      "modulo": "datos/bot_recoleccion",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).",
      "estado_fuente": "datos/bot_recoleccion/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "d_proyectos_db",
      "label": "proyectos.db",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 3,
      "ruta_declarada": "PROYECTOS_DB",
      "que_es": "La base de Proyectos de Ley: una fila por proyecto identificado por denominador NNNN-X-AAAA. FUENTE DE VERDAD del universo de proyectos y denominador del embudo (ADR-0009).",
      "notas": [
        "No viaja a git (pesa). Se rehace en ~1 min con migrar_ckan.py + upsert_bot.py.",
        "114.708 proyectos al 07-08-2026."
      ],
      "archivo": "datos/proyectos/data/proyectos.db",
      "existe": true,
      "modulo": "datos/proyectos",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "d_cuarentena_db",
      "label": "cuarentena.db",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "PROYECTOS_CUARENTENA_DB",
      "que_es": "Las filas dudosas, aparte. Existen, se pueden mirar, y no contaminan la base principal.",
      "archivo": "datos/proyectos/data/cuarentena.db",
      "existe": true,
      "modulo": "datos/proyectos",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).",
      "estado_fuente": "datos/proyectos/README.md",
      "owner": "—"
    },
    {
      "id": "d_padron_dip",
      "label": "padron_diputados.csv",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "ruta_declarada": "PADRON_DIPUTADOS",
      "que_es": "Quién ocupa cada una de las 257 bancas de Diputados y en qué ventana de mandato. 1.454 tramos.",
      "archivo": "datos/padron/data/padron_diputados.csv",
      "existe": true,
      "modulo": "datos/padron",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "d_padron_sen",
      "label": "padron_senado.csv",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "PADRON_SENADO",
      "que_es": "Los 72 senadores VIGENTES. Alcanza para el nowcast de hoy, no para rostear el pasado.",
      "notas": [
        "⚠ Es el motivo por el que el backtest de la cadena corre efectivamente sólo sobre Diputados."
      ],
      "archivo": "datos/padron/data/padron_senado.csv",
      "existe": true,
      "modulo": "datos/padron",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "d_padron_sen_hist",
      "label": "padron_senado_historico.csv",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "ruta_declarada": "PADRON_SENADO_HISTORICO",
      "que_es": "El Senado con historia: 243 tramos, 176 senadores, 2017→2031. Es el padrón que usa la Puerta D.",
      "archivo": "datos/padron/data/padron_senado_historico.csv",
      "existe": true,
      "modulo": "datos/padron",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "d_padron_linaje",
      "label": "senado_linaje_manual.csv",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "PADRON_SENADO_LINAJE_MANUAL",
      "que_es": "Override manual del linaje de bloque del Senado. Completo 22/22: es lo que hizo que el nowcast del Senado pueda condicionar por linaje.",
      "archivo": "datos/padron/data/senado_linaje_manual.csv",
      "existe": true,
      "modulo": "datos/padron",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "d_bloques_senado",
      "label": "padron_bloques_senado.csv",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "SENADO_PADRON_BLOQUES",
      "que_es": "Qué bloque tenía cada senador en el momento de votar. Reconstruido; quedan filas marcadas REVISAR.",
      "archivo": "datos/senado/data/padron_bloques_senado.csv",
      "existe": true,
      "modulo": "datos/senado",
      "modulo_inferido": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (2015–2023 completo; quedan filas `REVISAR` en el padrón manual)",
      "estado_fuente": "datos/senado/README.md",
      "owner": "Claude+Franco (2026-07-01/02)"
    },
    {
      "id": "d_excel_2026",
      "label": "Congreso_25-27.xlsx",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "MANUAL_2026_XLSX",
      "que_es": "El Excel que Franco mantiene a mano con los votos 2026 de ambas cámaras.",
      "archivo": "datos/manual_2026/Congreso_25-27.xlsx",
      "existe": true,
      "modulo": "datos/manual_2026",
      "modulo_inferido": true,
      "estado": "HECHO",
      "estado_texto": "HECHO (primera carga). Fuente viva: Franco la sigue completando a mano.",
      "estado_fuente": "datos/manual_2026/README.md",
      "owner": "—"
    },
    {
      "id": "d_taxonomias",
      "label": "taxonomias.json",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "archivo": "docs/taxonomias/taxonomias.json",
      "modulo": "docs/taxonomias",
      "que_es": "El vocabulario controlado de temas: 74 ids estables, multi-etiqueta. Es un CATÁLOGO, no un modelo.",
      "existe": true,
      "entrypoint": false,
      "estado": "",
      "owner": "—",
      "estado_texto": "su README no declara `**Estado:**`"
    },
    {
      "id": "d_export",
      "label": "base consultable (SQLite + Excel)",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 1,
      "ruta_declarada": "EXPORT_DATA",
      "que_es": "La canónica en formato consultable para el equipo. No alimenta el modelo: es para mirar.",
      "notas": [
        "Su columna `periodo` es el período de dos años entre recambios («2019-2021»)."
      ],
      "archivo": "datos/export/data",
      "existe": true,
      "modulo": "datos/export",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 (falta corrida completa de los Excel en PC del equipo)",
      "estado_fuente": "datos/export/README.md",
      "owner": "Claude+Valle (desde 2026-07-02)"
    },
    {
      "id": "s_embudo",
      "label": "embudo.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 3,
      "archivo": "variables/embudo/src/embudo.py",
      "modulo": "variables/embudo",
      "que_es": "Mide el embudo por etapas (presentado → comisión → dictamen → recinto → sanción) y entrena un modelo de supervivencia que estima P(llega al recinto) y P(sanción) con rasgos conocidos AL MOMENTO DE PRESENTACIÓN, sin leakage.",
      "notas": [
        "Entrena y backtestea sobre COHORTES MADURAS: los proyectos caducan (Ley 13.640), así que lo reciente no se puede contar como muerto.",
        "Lee de proyectos.db; `EMBUDO_FUENTE=parquet` es la ruta de fallback."
      ],
      "existe": true,
      "loc": 730,
      "simbolos": [
        {
          "nombre": "cargar_icg",
          "tipo": "funcion",
          "linea": 74,
          "doc": "Lee icg_mensual.csv -> {(anio, mes): {\"icg\": x, \"icg_delta_3m\": y}}."
        },
        {
          "nombre": "_mes_rezagado",
          "tipo": "funcion",
          "linea": 109,
          "doc": "(anio, mes) - lag meses. Devuelve None si la fecha no es utilizable."
        },
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 124,
          "doc": "Lee el contrato de datos/expedientes. Tolerante a archivos faltantes."
        },
        {
          "nombre": "cargar_sqlite",
          "tipo": "funcion",
          "linea": 153,
          "doc": "Mismo contrato que `cargar()`, pero leido de `proyectos.db` (ADR-0009)."
        },
        {
          "nombre": "_ids",
          "tipo": "funcion",
          "linea": 236,
          "doc": null
        },
        {
          "nombre": "construir_cohorte",
          "tipo": "funcion",
          "linea": 245,
          "doc": "Una fila por proyecto de LEY con sus etapas y rasgos de presentacion."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "s_bloque",
      "label": "bloque.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 3,
      "archivo": "variables/bloque/src/bloque.py",
      "modulo": "variables/bloque",
      "que_es": "Cohesión, tamaño, postura y fracturas de cada bloque en el tiempo, y el proyector point-in-time (`proyectar_postura`) que arma el escenario por bloque que consume el ensemble. Condiciona por tema y por origen.",
      "notas": [
        "⚠ Su columna `periodo` es un AÑO legislativo (entero). En export/disciplina/ficha/asistencia, `periodo` es el período de DOS AÑOS entre recambios («2019-2021»). Cruzarlas por nombre da cualquier cosa sin levantar un error."
      ],
      "existe": true,
      "loc": 633,
      "simbolos": [
        {
          "nombre": "_canon_linaje",
          "tipo": "funcion",
          "linea": 78,
          "doc": "Lleva una etiqueta de linaje escrita a mano a su forma canónica. Devuelve el"
        },
        {
          "nombre": "_norm_nombre",
          "tipo": "funcion",
          "linea": 110,
          "doc": "APELLIDO NOMBRE sin acentos/puntuación (misma convención que origen_lider)."
        },
        {
          "nombre": "_cargar_padron_linaje_senado",
          "tipo": "funcion",
          "linea": 124,
          "doc": "Devuelve (tramos, manual): tramos = lista (nn, desde, hasta, linaje) del padrón"
        },
        {
          "nombre": "_enriquecer_linaje_senado",
          "tipo": "funcion",
          "linea": 151,
          "doc": "Reasigna bloque_linaje de las filas del SENADO cuyo linaje es genérico"
        },
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 216,
          "doc": "Lee votos_resuelto + actas_canonico y devuelve el detalle voto-a-voto con"
        },
        {
          "nombre": "metricas_acta_bloque",
          "tipo": "funcion",
          "linea": 275,
          "doc": "Una fila por (acta, bloque) con dirección (mayoría A/N entre EMITIDOS),"
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1) · **Owner:** Claude+Valle (2026-07-12)",
      "estado_fuente": "variables/bloque/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "s_disciplina",
      "label": "disciplina.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 2,
      "archivo": "modelo/voto_individual/src/disciplina.py",
      "modulo": "modelo/voto_individual",
      "que_es": "No predice el voto medio (la regla de bloque ya acierta ~0,99): modela el DESVÍO del legislador respecto de su bloque y detecta las bisagras.",
      "notas": [
        "13-08: se separó INDISCIPLINA de AUSENTISMO. El desvío mezclado correlacionaba r=0,65 con la inasistencia — el top de «díscolos» eran ausentes crónicos con desvío de conducta CERO."
      ],
      "existe": true,
      "loc": 406,
      "simbolos": [
        {
          "nombre": "_sin_acentos",
          "tipo": "funcion",
          "linea": 103,
          "doc": null
        },
        {
          "nombre": "excluir_no_medibles",
          "tipo": "funcion",
          "linea": 108,
          "doc": "Saca (1) filas placeholder de las fuentes (bancas no incorporadas), (2) suspendidos"
        },
        {
          "nombre": "actas_disputadas",
          "tipo": "funcion",
          "linea": 143,
          "doc": "Disputada = resultado a ±5% de los emitidos respecto del umbral (def. de Valle,"
        },
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 165,
          "doc": null
        },
        {
          "nombre": "_linea",
          "tipo": "funcion",
          "linea": 191,
          "doc": "Conducta con >50% de los escaños del nivel (bloque o linaje) en cada acta."
        },
        {
          "nombre": "marcar_desvios",
          "tipo": "funcion",
          "linea": 203,
          "doc": "Desvío v2 por voto: línea del bloque → desempate por linaje → desvío parcial."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — pieza (a) implementada; gate 1 APROBADO sobre base completa (ver `RESULTADOS.md`)",
      "estado_fuente": "modelo/voto_individual/README.md",
      "owner": "Claude+Valle (desde 2026-07-01)"
    },
    {
      "id": "s_ficha",
      "label": "ficha.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 1,
      "archivo": "variables/legislador/src/ficha.py",
      "modulo": "variables/legislador",
      "que_es": "Una ficha por legislador que votó alguna vez: identidad, cámara, distrito, períodos, trayectoria de bloques, presentismo y tasa de desvío.",
      "existe": true,
      "loc": 292,
      "simbolos": [
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 48,
          "doc": "Carga votos resueltos + cámara del acta. Falla con mensaje claro si no está la base."
        },
        {
          "nombre": "_nombre_canonico",
          "tipo": "funcion",
          "linea": 69,
          "doc": "El nombre más frecuente (y más largo ante empate) entre las variantes."
        },
        {
          "nombre": "historial_bloques",
          "tipo": "funcion",
          "linea": 76,
          "doc": null
        },
        {
          "nombre": "por_periodo",
          "tipo": "funcion",
          "linea": 88,
          "doc": "LA tabla de análisis: legislador x período parlamentario x cámara."
        },
        {
          "nombre": "por_anio",
          "tipo": "funcion",
          "linea": 113,
          "doc": null
        },
        {
          "nombre": "ficha",
          "tipo": "funcion",
          "linea": 129,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 con dimensión período (re-correr tras cada rebuild de la canónica)",
      "estado_fuente": "variables/legislador/README.md",
      "owner": "Claude+Valle (desde 2026-07-01)"
    },
    {
      "id": "s_asistencia",
      "label": "asistencia.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 1,
      "archivo": "variables/asistencia_quorum/src/asistencia.py",
      "modulo": "variables/asistencia_quorum",
      "que_es": "Presentismo por legislador y período. Es donde vive la incertidumbre que el bloque no explica.",
      "notas": [
        "⚠ Alimentar el motor con presentismo PROMEDIO lo EMPEORA. Lo que se usa es la posición del bloque entre los PRESENTES. La asistencia condicional es el escalón 2, pendiente."
      ],
      "existe": true,
      "loc": 102,
      "simbolos": [
        {
          "nombre": "calcular_presentismo",
          "tipo": "funcion",
          "linea": 47,
          "doc": "Devuelve (presentismo_global, presentismo_por_periodo). p_present en [0,1]."
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 75,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — Owner: Valle (reclamado 2026-07-11). **Escalón 1 hecho:** `asistencia.py`",
      "estado_fuente": "variables/asistencia_quorum/README.md",
      "owner": "—"
    },
    {
      "id": "s_origen_lider",
      "label": "origen_lider.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 2,
      "archivo": "variables/proyecto/src/origen_lider.py",
      "modulo": "variables/proyecto",
      "que_es": "Quién impulsa el proyecto: EJECUTIVO / OFICIALISMO / ALIADOS / OPOSICIÓN, y si el firmante es jefe de bloque.",
      "notas": [
        "La categoría ALIADOS se creó el 14-08: agrupar PRO con el gobierno de Milei daba señales absurdas.",
        "El efecto jefe de bloque es 1,25x, no el 7x que se creía: es aceite del motor, no propositor."
      ],
      "existe": true,
      "loc": 395,
      "simbolos": [
        {
          "nombre": "_norm",
          "tipo": "funcion",
          "linea": 81,
          "doc": "Normaliza un nombre: sin acentos, mayúsculas, sin puntuación, 'APELLIDO NOMBRE'."
        },
        {
          "nombre": "_linaje_code",
          "tipo": "funcion",
          "linea": 95,
          "doc": "Mapea el linaje del padrón (con nombres largos y sufijos, ej."
        },
        {
          "nombre": "oficialista_por_fecha",
          "tipo": "funcion",
          "linea": 123,
          "doc": "True si el linaje gobernaba (núcleo O aliado) en esa fecha; False si no;"
        },
        {
          "nombre": "clase_oficialismo",
          "tipo": "funcion",
          "linea": 135,
          "doc": "Distingue el partido de gobierno de sus aliados en esa fecha:"
        },
        {
          "nombre": "cargar",
          "tipo": "funcion",
          "linea": 155,
          "doc": null
        },
        {
          "nombre": "_mapa_autor_linaje",
          "tipo": "funcion",
          "linea": 178,
          "doc": "(nombre_norm) -> lista de (anio_desde, anio_hasta, linaje) del legislador."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "s_tema_por_acta",
      "label": "tema_por_acta.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 1,
      "archivo": "variables/proyecto/src/tema_por_acta.py",
      "modulo": "variables/proyecto",
      "que_es": "Asigna el tema de cada acta contra el catálogo de taxonomías.",
      "existe": true,
      "loc": 265,
      "simbolos": [
        {
          "nombre": "_ahora",
          "tipo": "funcion",
          "linea": 53,
          "doc": null
        },
        {
          "nombre": "_clasificador_agente",
          "tipo": "funcion",
          "linea": 60,
          "doc": "Devuelve fn(titulo) -> [(tema_id, confianza), ...] usando el agente real."
        },
        {
          "nombre": "_elegir_primaria",
          "tipo": "funcion",
          "linea": 73,
          "doc": "De las asignaciones, elige el TEMA primario: mayor confianza NO auxiliar."
        },
        {
          "nombre": "cargar_actas",
          "tipo": "funcion",
          "linea": 89,
          "doc": "Lee acta_expediente y devuelve las actas votadas con título utilizable."
        },
        {
          "nombre": "cargar_actas_canonica",
          "tipo": "funcion",
          "linea": 112,
          "doc": "Fuente para actas RECIENTES: el título DESCRIPTIVO ya vive en la canónica"
        },
        {
          "nombre": "clasificar_actas",
          "tipo": "funcion",
          "linea": 146,
          "doc": "Clasifica cada acta por su título. Idempotente contra `previas` (no reclasifica"
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "s_agente_taxonomias",
      "label": "agente_taxonomias.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 1,
      "archivo": "variables/proyecto/src/agente_taxonomias.py",
      "modulo": "variables/proyecto",
      "que_es": "Clasifica un proyecto por título contra taxonomias.json usando un LLM. Multi-etiqueta (ADR-0006).",
      "notas": [
        "Necesita ANTHROPIC_API_KEY."
      ],
      "existe": true,
      "loc": 495,
      "simbolos": [
        {
          "nombre": "Asignacion",
          "tipo": "clase",
          "linea": 72,
          "doc": null
        },
        {
          "nombre": "ResultadoClasificacion",
          "tipo": "clase",
          "linea": 79,
          "doc": null
        },
        {
          "nombre": "_lista_y_reglas",
          "tipo": "funcion",
          "linea": 118,
          "doc": "Arma, desde taxonomias.json, la lista controlada y las reglas de frontera para el prompt."
        },
        {
          "nombre": "construir_prompt",
          "tipo": "funcion",
          "linea": 128,
          "doc": "Ruta TEXTO: el articulado ya extraído va dentro del mensaje."
        },
        {
          "nombre": "construir_prompt_documento",
          "tipo": "funcion",
          "linea": 145,
          "doc": "Ruta VISIÓN: el texto del proyecto llega como PDF adjunto (documento), no en el prompt."
        },
        {
          "nombre": "llamar_claude",
          "tipo": "funcion",
          "linea": 162,
          "doc": "Devuelve el texto crudo de la respuesta del modelo."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "s_modulador_icg",
      "label": "modulador_icg.py",
      "rol": "script",
      "etapa": "variables",
      "jerarquia": 2,
      "archivo": "variables/proyecto/src/modulador_icg.py",
      "modulo": "variables/proyecto",
      "que_es": "Traduce el clima político en un gamma que ENCOGE el desvío de las bisagras. Es la única vía por la que la coyuntura toca el número.",
      "notas": [
        "11-08: el ICG entra en horizonte de FONDO (6 meses) dentro de cada gobierno. El horizonte CORTO no fue significativo y se apagó. La capa 2 global del analista se eliminó (contaba doble)."
      ],
      "existe": true,
      "loc": 255,
      "simbolos": [
        {
          "nombre": "_cargar_tramos",
          "tipo": "funcion",
          "linea": 65,
          "doc": "Devuelve (TRAMOS_FONDO, TRAMOS_CORTO, fuente). Lee la dose-response oficial;"
        },
        {
          "nombre": "encoger_desvio",
          "tipo": "funcion",
          "linea": 107,
          "doc": "Desvio ENCOGIDO hacia un `prior` (la mediana de su bloque), con peso"
        },
        {
          "nombre": "_gamma_tramo",
          "tipo": "funcion",
          "linea": 131,
          "doc": "gamma de UNA capa según cuán bisagra es el legislador. NaN -> disciplinado."
        },
        {
          "nombre": "gamma_fondo",
          "tipo": "funcion",
          "linea": 141,
          "doc": "gamma de la capa de FONDO (mediano plazo, 6m)."
        },
        {
          "nombre": "gamma_corto",
          "tipo": "funcion",
          "linea": 146,
          "doc": "gamma de la capa de CORTO (sacudón reciente, 3m)."
        },
        {
          "nombre": "_mover",
          "tipo": "funcion",
          "linea": 151,
          "doc": "logit(p) + gamma*s*z, con los bordes protegidos."
        }
      ],
      "lenguaje": "python",
      "entrypoint": false,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_p_embudo",
      "label": "p_embudo.parquet",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 3,
      "ruta_declarada": "EMBUDO_OUT",
      "archivo_dato": "variables/embudo/outputs/p_embudo.parquet",
      "que_es": "proyecto_id, etapa_actual, p_llega_recinto, p_sancion. La columna `p_llega_recinto` es el factor 1 del nowcast; `p_sancion` es la BASELINE contra la que se mide la cadena completa.",
      "archivo": "variables/embudo/outputs/p_embudo.parquet",
      "existe": true,
      "entrypoint": false,
      "modulo": "variables/embudo",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "d_embudo_etapas",
      "label": "embudo_etapas.csv",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 1,
      "archivo_dato": "variables/embudo/outputs/embudo_etapas.csv",
      "que_es": "Tasas de transición por etapa, global y por año/cámara. Es el embudo descriptivo: por qué la mayoría de los proyectos nunca se votan.",
      "archivo": "variables/embudo/outputs/embudo_etapas.csv",
      "existe": true,
      "entrypoint": false,
      "modulo": "variables/embudo",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "d_features_proyecto",
      "label": "features_proyecto.parquet",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 2,
      "ruta_declarada": "PROYECTO_FEATURES",
      "que_es": "El feature store por proyecto: tema, origen, jefe de bloque, mayoría requerida. Lo consumen el embudo y el condicionamiento de postura.",
      "archivo": "variables/proyecto/data/features_proyecto.parquet",
      "existe": true,
      "modulo": "variables/proyecto",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_origen_por_acta",
      "label": "origen_por_acta.parquet",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 1,
      "ruta_declarada": "PROYECTO_ORIGEN_POR_ACTA",
      "que_es": "El origen (EJECUTIVO/OFICIALISMO/ALIADOS/OPOSICIÓN) de cada acta. Es lo que permite condicionar la postura de bloque.",
      "archivo": "variables/proyecto/data/origen_por_acta.parquet",
      "existe": true,
      "modulo": "variables/proyecto",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_tema_por_acta",
      "label": "tema_por_acta.parquet",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 1,
      "ruta_declarada": "PROYECTO_TEMA_POR_ACTA",
      "que_es": "El tema de cada acta. La otra mitad del condicionamiento.",
      "archivo": "variables/proyecto/data/tema_por_acta.parquet",
      "existe": true,
      "modulo": "variables/proyecto",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_icg_mensual",
      "label": "icg_mensual.csv",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 1,
      "ruta_declarada": "PROYECTO_ICG_MENSUAL",
      "que_es": "La serie mensual del ICG. Entra al embudo rezagada un mes y al modulador como horizonte de 6 meses.",
      "archivo": "variables/proyecto/data/icg_mensual.csv",
      "existe": true,
      "modulo": "variables/proyecto",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_jefes_bloque",
      "label": "jefes_bloque.csv",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 1,
      "ruta_declarada": "PROYECTO_JEFES_BLOQUE",
      "que_es": "Quién presidía cada bloque y cuándo.",
      "notas": [
        "⚠ URGENTE vivo: 15 filas con confianza MEDIA sin validar. El caso Bianchi mostró el daño: una sola fila mal puesta metió 610 proyectos falsos (27% de la señal)."
      ],
      "archivo": "variables/proyecto/data/jefes_bloque.csv",
      "existe": true,
      "modulo": "variables/proyecto",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "d_disciplina",
      "label": "disciplina_individual.csv",
      "rol": "dato",
      "etapa": "variables",
      "jerarquia": 2,
      "ruta_declarada": "DISCIPLINA_INDIVIDUAL",
      "que_es": "La tasa de desvío de cada legislador. Desde el 13-08 trae columnas separadas: `tasa_desvio_conducta` (voto distinto ESTANDO PRESENTE) y `tasa_desvio_ausencia`.",
      "archivo": "modelo/voto_individual/outputs/disciplina_individual.csv",
      "existe": true,
      "modulo": "modelo/voto_individual",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — pieza (a) implementada; gate 1 APROBADO sobre base completa (ver `RESULTADOS.md`)",
      "estado_fuente": "modelo/voto_individual/README.md",
      "owner": "Claude+Valle (desde 2026-07-01)"
    },
    {
      "id": "v_embudo",
      "label": "Embudo",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 3,
      "modulo": "variables/embudo",
      "que_es": "¿El proyecto siquiera llega a votarse? Es el diferencial del nowcast: la mayoría de los proyectos mueren en comisión.",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "v_bloque",
      "label": "Bloque",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 3,
      "modulo": "variables/bloque",
      "que_es": "¿Qué postura toma cada bloque en este tema, con este origen, a esta fecha? Y ¿cuán cohesionado está?",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1) · **Owner:** Claude+Valle (2026-07-12)",
      "estado_fuente": "variables/bloque/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "v_legislador",
      "label": "Legislador",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 2,
      "modulo": "variables/legislador",
      "que_es": "La ficha individual: quién es, por qué bloques pasó, cuánto falta, cuánto se desvía.",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 con dimensión período (re-correr tras cada rebuild de la canónica)",
      "estado_fuente": "variables/legislador/README.md",
      "owner": "Claude+Valle (desde 2026-07-01)"
    },
    {
      "id": "v_asistencia",
      "label": "Asistencia / quórum",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 2,
      "modulo": "variables/asistencia_quorum",
      "que_es": "¿Quién va a estar presente? Muchas leyes se ganan o se pierden por quién falta ese día.",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — Owner: Valle (reclamado 2026-07-11). **Escalón 1 hecho:** `asistencia.py`",
      "estado_fuente": "variables/asistencia_quorum/README.md",
      "owner": "—"
    },
    {
      "id": "v_proyecto",
      "label": "Proyecto",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 3,
      "modulo": "variables/proyecto",
      "que_es": "Qué ES el proyecto: tema, origen (Ejecutivo/Oficialismo/Aliados/Oposición), si lo firma un jefe de bloque, qué mayoría requiere, y el ICG como modulador de coyuntura.",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO",
      "estado_fuente": "variables/proyecto/README.md",
      "owner": "Valle (con Claude)"
    },
    {
      "id": "v_contexto",
      "label": "Contexto",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 1,
      "modulo": "variables/contexto",
      "que_es": "Señal cualitativa de prensa y clima político (factor mu). NO EXISTE todavía: la carpeta está vacía.",
      "es_hueco": true,
      "parqueada": true,
      "estado": "FUTURO",
      "estado_texto": "FUTURO",
      "estado_fuente": "variables/contexto/README.md",
      "owner": "vacante"
    },
    {
      "id": "v_voto_individual",
      "label": "Desvío individual",
      "rol": "variable",
      "etapa": "variables",
      "jerarquia": 2,
      "modulo": "modelo/voto_individual",
      "que_es": "Cuánto se aparta cada legislador de la línea de su bloque. Es la puerta por la que las bisagras cambian una votación.",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — pieza (a) implementada; gate 1 APROBADO sobre base completa (ver `RESULTADOS.md`)",
      "estado_fuente": "modelo/voto_individual/README.md",
      "owner": "Claude+Valle (desde 2026-07-01)"
    },
    {
      "id": "c_roster_origen",
      "label": "Roster nominal (origen)",
      "rol": "variable",
      "etapa": "origen",
      "jerarquia": 2,
      "archivo": "modelo/ensemble/src/ensemble.py",
      "simbolo": "roster_nominal",
      "que_es": "UNA FILA POR LEGISLADOR de la camara a la fecha, no bancas anonimas. Desde el 22-08 el padron es la foto COMPLETA (oficial + historico, sin duplicados): antes leia un solo archivo y el oficial cubre 81 de 257 bancas en 2008 y 203 en 2019.",
      "notas": [
        "Escalera del desvío: (1) tasa reciente si n≥MIN_VOTOS_FICHA, (2) tasa global si alcanza, (3) desvío promedio del bloque — sólo para camada nueva. Es la única excepción admitida.",
        "El v2 (clonar el promedio del bloque `bancas` veces) se ELIMINÓ el 22-07: aplicaba el promedio incluso a los 753 legisladores con desvío medido."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "origen",
      "existe": true,
      "loc": 396,
      "simbolos": [
        {
          "nombre": "_cargar_simulador",
          "tipo": "funcion",
          "linea": 68,
          "doc": "Importa simular_votacion del agregador sin tocar su código."
        },
        {
          "nombre": "_cargar_proyector",
          "tipo": "funcion",
          "linea": 81,
          "doc": "Importa cargar + proyectar_postura de variables/bloque (contrato publico)."
        },
        {
          "nombre": "componer",
          "tipo": "funcion",
          "linea": 107,
          "doc": "DADA DE BAJA (2026-08-22) - era el corazon de la v1. Ver `_BAJA_V1`."
        },
        {
          "nombre": "_root",
          "tipo": "funcion",
          "linea": 115,
          "doc": null
        },
        {
          "nombre": "_padron_csv",
          "tipo": "funcion",
          "linea": 119,
          "doc": null
        },
        {
          "nombre": "_disciplina_csv",
          "tipo": "funcion",
          "linea": 126,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "c_simular_origen",
      "label": "simular_votacion",
      "rol": "variable",
      "etapa": "origen",
      "jerarquia": 3,
      "archivo": "modelo/agregador_institucional/src/agregador.py",
      "simbolo": "simular_votacion",
      "modulo": "modelo/agregador_institucional",
      "formula": "cada legislador sigue su línea con prob (1−d) y se desvía con prob d",
      "que_es": "El recuento como DISTRIBUCIÓN, no como número seco. Simula la votación muchas veces contando bancas, quórum y umbral, y devuelve P(aprobación) con su banda 5-95%.",
      "notas": [
        "Umbrales: SIMPLE = emitidos/2 · ABSOLUTA = miembros//2+1 (129 dip / 37 sen) · DOS_TERCIOS = ceil(emitidos·2/3) · DOS_TERCIOS_CUERPO = ceil(miembros·2/3) · TRES_CUARTOS = ceil(emitidos·3/4).",
        "v1 modela el quórum de forma laxa: se asume reunido si los presentes ≥ mitad+1 de los miembros."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 347,
      "simbolos": [
        {
          "nombre": "umbral_aprobacion",
          "tipo": "funcion",
          "linea": 70,
          "doc": "Umbral de afirmativos para aprobar, según el tipo de mayoría."
        },
        {
          "nombre": "_prob_conductas",
          "tipo": "funcion",
          "linea": 90,
          "doc": "Vector [p(AFIRM), p(NEG), p(NO_ACOMPANA)] para un legislador dada su línea y"
        },
        {
          "nombre": "simular_votacion",
          "tipo": "funcion",
          "linea": 106,
          "doc": "Simula la votación n_sims veces a partir del roster (una línea y un desvío por"
        },
        {
          "nombre": "_linea_bloque_por_acta",
          "tipo": "funcion",
          "linea": 180,
          "doc": "Línea observada de cada bloque en cada acta = conducta con mayoría simple sobre"
        },
        {
          "nombre": "_direccion_bloque_por_acta",
          "tipo": "funcion",
          "linea": 198,
          "doc": "DIRECCIÓN del bloque = mayoría AFIRMATIVO vs NEGATIVO SOLO entre los que emitieron"
        },
        {
          "nombre": "backtest",
          "tipo": "funcion",
          "linea": 211,
          "doc": "Corre el agregador sobre las actas históricas (alimentándolo con la línea de"
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — Owner: Valle (reclamado 2026-07-10). Gate de pase: reglas validadas",
      "estado_fuente": "modelo/agregador_institucional/README.md",
      "owner": "—"
    },
    {
      "id": "c_p_mayoria_origen",
      "label": "P(mayoría en origen) — Paso B",
      "rol": "variable",
      "etapa": "origen",
      "jerarquia": 3,
      "formula": "P(afirma) = share·(1−d) + (1−share)·(d/2), escalado por la asistencia",
      "que_es": "La votacion en la camara de origen. Desde el 22-08 la P de cada legislador COMPONE el numero real de su bloque con su desvio individual, en vez de redondear el bloque a SI/NO: antes la Coalicion Civica, que acompaña el 60,9% de las veces, salia en 96,7%. Si tiene historial propio suficiente, la direccion sale de SU historial y no del linaje.",
      "notas": [
        "Ese redondeo era la razon de que casi todas las votaciones dieran 99%.",
        "Faltar ya no es votar en contra: la asistencia va por su propio canal (p_presente).",
        "Umbral de mayoria simple = mitad de los EMITIDOS mas uno (ADR-0013: el empate no aprueba)."
      ],
      "modulo": "modelo/agregador_institucional",
      "bloque": "origen",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — Owner: Valle (reclamado 2026-07-10). Gate de pase: reglas validadas",
      "estado_fuente": "modelo/agregador_institucional/README.md",
      "owner": "—"
    },
    {
      "id": "g_A",
      "label": "Puerta A — agenda origen",
      "rol": "variable",
      "etapa": "origen",
      "jerarquia": 3,
      "parqueada": false,
      "formula": "A observada (no es probabilidad)",
      "que_es": "¿Hay dictamen en la cámara de origen y con qué carácter? Se OBSERVA, no se predice: quién firmó, si hubo disidencias y de qué bloques son los firmantes. Ese carácter CONDICIONA la votación (B).",
      "notas": [
        "3.970 proyectos con dictamen leido sobre los 42.141 del embudo.",
        "TRES estados, y el tercero no colapsa al segundo: con caracter / sin dictamen / SIN DATO.",
        "En 'sin dato' el condicionante se ENCOGE A 0 y queda la estimacion sin condicionar: el fallback no es un `if`. Reusa puerta_d.ajuste_paso_origen.",
        "Point-in-time obligatorio: un dictamen sin fecha utilizable sale 'sin dato', nunca 'con caracter' — darlo por existente seria fuga del futuro.",
        "El condicionante arranca en CERO: la etiqueta binaria del voto esta degenerada (2 RECHAZADO en 1.898), asi que todavia no hay contra que calibrarlo."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "origen",
      "estado_declarado": "EN CURSO",
      "suspendida": false,
      "estado_motivo": "Implementada el 2026-08-22 (ADR-0012). Dejo de estar parqueada como probabilidad —esa probabilidad no existe mas— y pasa a ser señal OBSERVADA. Lo que sigue suspendido para siempre es modelar si la comision va a tratar el proyecto.",
      "archivo": "modelo/ensemble/src/puerta_a.py",
      "existe": true,
      "loc": 445,
      "simbolos": [
        {
          "nombre": "_texto",
          "tipo": "funcion",
          "linea": 113,
          "doc": "Un faltante puede llegar como None, NaN o pd.NA según el backend de dtype."
        },
        {
          "nombre": "_fecha",
          "tipo": "funcion",
          "linea": 118,
          "doc": null
        },
        {
          "nombre": "_algun_si",
          "tipo": "funcion",
          "linea": 122,
          "doc": "¿Alguna fila dice que sí? Tolera None/NaN/pd.NA sin el downcast deprecado."
        },
        {
          "nombre": "_fecha_dictamen",
          "tipo": "funcion",
          "linea": 129,
          "doc": "Fecha del dictamen, en cascada, porque las dos cámaras no traen lo mismo."
        },
        {
          "nombre": "_n_expedientes",
          "tipo": "funcion",
          "linea": 169,
          "doc": "Cuántos expedientes dictamina la Orden del Día (el sumario los lista con `;`)."
        },
        {
          "nombre": "cargar_caracter",
          "tipo": "funcion",
          "linea": 185,
          "doc": "Una fila por (proyecto_id, camara) con el carácter observado del dictamen."
        }
      ],
      "lenguaje": "python",
      "entrypoint": false,
      "estado": "EN CURSO",
      "estado_fuente": "capa curada",
      "owner": "Claude+Valle (2026-07-12)",
      "estado_texto": "Implementada el 2026-08-22 (ADR-0012). Dejo de estar parqueada como probabilidad —esa probabilidad no existe mas— y pasa a ser señal OBSERVADA. Lo que sigue suspendido para siempre es modelar si la comision va a tratar el proyecto.",
      "estado_modulo": "EN CURSO"
    },
    {
      "id": "g_B",
      "label": "Puerta B — voto en origen",
      "rol": "variable",
      "etapa": "origen",
      "jerarquia": 3,
      "formula": "P(B | carácter del dictamen de origen)",
      "que_es": "¿Hay mayoría en la cámara donde nació el proyecto? EXISTE: es el agregador institucional corriendo sobre el roster de origen.",
      "notas": [
        "Es la misma maquinaria que P(mayoría | recinto) de la v1, leída en el lenguaje de puertas."
      ],
      "modulo": "modelo/agregador_institucional",
      "bloque": "origen",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — Owner: Valle (reclamado 2026-07-10). Gate de pase: reglas validadas",
      "estado_fuente": "modelo/agregador_institucional/README.md",
      "owner": "—"
    },
    {
      "id": "g_C",
      "label": "Puerta C — agenda revisora",
      "rol": "variable",
      "etapa": "revisora",
      "jerarquia": 3,
      "parqueada": false,
      "formula": "C observada (no es probabilidad)",
      "que_es": "¿Hay dictamen en las comisiones de la cámara revisora y con qué carácter? Se OBSERVA igual que A. Ese carácter CONDICIONA la votación de la revisora (D).",
      "notas": [
        "809 proyectos tienen dictamen leido en LAS DOS camaras.",
        "TRES estados, y el tercero no colapsa al segundo: con caracter / sin dictamen / SIN DATO.",
        "En 'sin dato' el condicionante se ENCOGE A 0 y queda la estimacion sin condicionar: el fallback no es un `if`. Reusa puerta_d.ajuste_paso_origen.",
        "Point-in-time obligatorio: un dictamen sin fecha utilizable sale 'sin dato', nunca 'con caracter' — darlo por existente seria fuga del futuro.",
        "El condicionante arranca en CERO: la etiqueta binaria del voto esta degenerada (2 RECHAZADO en 1.898), asi que todavia no hay contra que calibrarlo."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "revisora",
      "grupo": "condicionado_por_origen",
      "estado_declarado": "EN CURSO",
      "suspendida": false,
      "estado_motivo": "Implementada el 2026-08-22 (ADR-0012). Dejo de estar parqueada como probabilidad —esa probabilidad no existe mas— y pasa a ser señal OBSERVADA. Lo que sigue suspendido para siempre es modelar si la comision va a tratar el proyecto.",
      "archivo": "modelo/ensemble/src/puerta_a.py",
      "existe": true,
      "loc": 445,
      "simbolos": [
        {
          "nombre": "_texto",
          "tipo": "funcion",
          "linea": 113,
          "doc": "Un faltante puede llegar como None, NaN o pd.NA según el backend de dtype."
        },
        {
          "nombre": "_fecha",
          "tipo": "funcion",
          "linea": 118,
          "doc": null
        },
        {
          "nombre": "_algun_si",
          "tipo": "funcion",
          "linea": 122,
          "doc": "¿Alguna fila dice que sí? Tolera None/NaN/pd.NA sin el downcast deprecado."
        },
        {
          "nombre": "_fecha_dictamen",
          "tipo": "funcion",
          "linea": 129,
          "doc": "Fecha del dictamen, en cascada, porque las dos cámaras no traen lo mismo."
        },
        {
          "nombre": "_n_expedientes",
          "tipo": "funcion",
          "linea": 169,
          "doc": "Cuántos expedientes dictamina la Orden del Día (el sumario los lista con `;`)."
        },
        {
          "nombre": "cargar_caracter",
          "tipo": "funcion",
          "linea": 185,
          "doc": "Una fila por (proyecto_id, camara) con el carácter observado del dictamen."
        }
      ],
      "lenguaje": "python",
      "entrypoint": false,
      "estado": "EN CURSO",
      "estado_fuente": "capa curada",
      "owner": "Claude+Valle (2026-07-12)",
      "estado_texto": "Implementada el 2026-08-22 (ADR-0012). Dejo de estar parqueada como probabilidad —esa probabilidad no existe mas— y pasa a ser señal OBSERVADA. Lo que sigue suspendido para siempre es modelar si la comision va a tratar el proyecto.",
      "estado_modulo": "EN CURSO"
    },
    {
      "id": "c_roster_revisora",
      "label": "Roster nominal (revisora)",
      "rol": "variable",
      "etapa": "revisora",
      "jerarquia": 2,
      "archivo": "modelo/ensemble/src/puerta_d.py",
      "simbolo": "camara_revisora",
      "que_es": "El mismo roster_nominal, pero de la OTRA cámara, a la fecha de la votación, con el padrón histórico del Senado cuando corresponde.",
      "notas": [
        "La revisora es la otra respecto de `camara_origen`. Única fuente de esa regla en el módulo."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "revisora",
      "existe": true,
      "loc": 236,
      "simbolos": [
        {
          "nombre": "camara_revisora",
          "tipo": "funcion",
          "linea": 45,
          "doc": "La revisora es la otra cámara. Única fuente de esta regla en el módulo."
        },
        {
          "nombre": "_padron_de",
          "tipo": "funcion",
          "linea": 56,
          "doc": "El padrón point-in-time de la cámara. Para el Senado, el HISTÓRICO"
        },
        {
          "nombre": "_clip01",
          "tipo": "funcion",
          "linea": 62,
          "doc": null
        },
        {
          "nombre": "_logit",
          "tipo": "funcion",
          "linea": 66,
          "doc": null
        },
        {
          "nombre": "_sigmoide",
          "tipo": "funcion",
          "linea": 71,
          "doc": null
        },
        {
          "nombre": "ajuste_paso_origen",
          "tipo": "funcion",
          "linea": 75,
          "doc": "Aplica el ajuste 'pasó por origen' sobre la probabilidad base, en logit."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "g_D",
      "label": "P(aprobación en Cámara Revisora)",
      "rol": "resultado",
      "etapa": "revisora",
      "jerarquia": 3,
      "archivo": "modelo/ensemble/src/puerta_d.py",
      "modulo": "modelo/ensemble",
      "formula": "P(D | carácter del dictamen de la revisora) = logit⁻¹( logit(p₀) + delta )",
      "que_es": "¿Un proyecto que ya tiene media sanción consigue mayoría en la cámara que lo revisa? EXISTE en código.",
      "notas": [
        "p₀ = P(mayoría | composición de la revisora), del mismo agregador. `delta` corrige por «ya pasó por origen», encogido por tamaño de muestra.",
        "HOY delta = 0 (Manera 1 pura). El fallback NO es un `if`: cuando la muestra no alcanza, el encogimiento lleva delta a 0. Manera 1 es el LÍMITE de Manera 2, un solo modelo.",
        "El ajuste se estimaría sobre los ~243 proyectos con votación en las dos cámaras (60 desde 2015), con ómnibus excluidos. `estimar_delta_paso_origen` está pendiente.",
        "NO transfiere posturas de origen a la revisora por linaje: se evaluó y se descartó."
      ],
      "bloque": "revisora",
      "sublabel": "Puerta D — voto en revisora",
      "grupo": "condicionado_por_origen",
      "existe": true,
      "loc": 236,
      "simbolos": [
        {
          "nombre": "camara_revisora",
          "tipo": "funcion",
          "linea": 45,
          "doc": "La revisora es la otra cámara. Única fuente de esta regla en el módulo."
        },
        {
          "nombre": "_padron_de",
          "tipo": "funcion",
          "linea": 56,
          "doc": "El padrón point-in-time de la cámara. Para el Senado, el HISTÓRICO"
        },
        {
          "nombre": "_clip01",
          "tipo": "funcion",
          "linea": 62,
          "doc": null
        },
        {
          "nombre": "_logit",
          "tipo": "funcion",
          "linea": 66,
          "doc": null
        },
        {
          "nombre": "_sigmoide",
          "tipo": "funcion",
          "linea": 71,
          "doc": null
        },
        {
          "nombre": "ajuste_paso_origen",
          "tipo": "funcion",
          "linea": 75,
          "doc": "Aplica el ajuste 'pasó por origen' sobre la probabilidad base, en logit."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "n_puertas",
      "label": "P(aprobación de un proyecto de ley)",
      "rol": "resultado",
      "etapa": "nowcast",
      "jerarquia": 3,
      "archivo": "modelo/ensemble/src/nowcast_puertas.py",
      "modulo": "modelo/ensemble",
      "formulacion": "puertas",
      "formula": "P = [A observada] · P(B | carácter de origen) · [C observada] · P(D | carácter de la revisora)",
      "que_es": "LA UNICA FORMULACION desde el 22-08-2026. A y C se OBSERVAN y CONDICIONAN; B y D se CALCULAN. El numero es CONDICIONAL a que las camaras voten: NO incluye la chance de que el proyecto sea tratado.",
      "bloque": "final",
      "sublabel": "P(aprobación), la única cadena",
      "estado_declarado": "EN CURSO",
      "estado_motivo": "EN CURSO y ya no PARCIAL: desde el 2026-08-22 (ADR-0012) es la UNICA formulacion y corre de punta a punta. A y C estan implementadas como señal observada (`puerta_a.py`), B y D calculan. Lo que falta no es la cadena sino su CALIBRACION: el condicionante del caracter vale 0 porque no hay contra que ajustarlo.",
      "existe": true,
      "loc": 479,
      "simbolos": [
        {
          "nombre": "_bloque",
          "tipo": "funcion",
          "linea": 79,
          "doc": null
        },
        {
          "nombre": "alineacion_individual",
          "tipo": "funcion",
          "linea": 88,
          "doc": "P(afirmativo) de CADA legislador sobre su PROPIO récord."
        },
        {
          "nombre": "perfil_legislador",
          "tipo": "funcion",
          "linea": 136,
          "doc": "Cómo se espera que vote esta persona. Devuelve p_afirma_si_vota y p_presente."
        },
        {
          "nombre": "a_linea_y_desvio",
          "tipo": "funcion",
          "linea": 178,
          "doc": "Traduce una P(afirmativo) al par (línea, desvío) que el agregador reproduce."
        },
        {
          "nombre": "_p_afirmativo_del_simulador",
          "tipo": "funcion",
          "linea": 199,
          "doc": "P(este legislador vote AFIRMATIVO) según el MISMO modelo que simula la votación."
        },
        {
          "nombre": "armar_roster",
          "tipo": "funcion",
          "linea": 215,
          "doc": "Perfil de cada legislador -> los arrays que entran al agregador."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_fuente": "capa curada",
      "owner": "Claude+Valle (2026-07-12)",
      "estado_texto": "EN CURSO y ya no PARCIAL: desde el 2026-08-22 (ADR-0012) es la UNICA formulacion y corre de punta a punta. A y C estan implementadas como señal observada (`puerta_a.py`), B y D calculan. Lo que falta no es la cadena sino su CALIBRACION: el condicionante del caracter vale 0 porque no hay contra que ajustarlo.",
      "estado_modulo": "EN CURSO"
    },
    {
      "id": "n_colapso",
      "label": "Regla del colapso",
      "rol": "variable",
      "etapa": "nowcast",
      "jerarquia": 2,
      "formula": "puerta ya ocurrida ⇒ vale 1",
      "que_es": "Una puerta que ya pasó deja de ser probabilidad. Con media sanción, A y B son HECHOS y el número publicado queda P(C)·P(D).",
      "notas": [
        "Es lo que hace que el mismo proyecto tenga un número distinto según en qué etapa esté. No es una inconsistencia: es la regla."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "final",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "n_salida",
      "label": "nowcast_<proyecto>.json",
      "rol": "dato",
      "etapa": "nowcast",
      "jerarquia": 2,
      "ruta_declarada": "ENSEMBLE_OUT",
      "que_es": "La tarjeta de salida por proyecto: p_llega_recinto, p_mayoria_recinto, p_aprobacion, y el detalle del escenario (ADR-0007).",
      "bloque": "final",
      "archivo": "modelo/ensemble/outputs",
      "existe": true,
      "modulo": "modelo/ensemble",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "n_alerta_senado",
      "label": "⚠ No publicar origen Senado",
      "rol": "variable",
      "etapa": "nowcast",
      "jerarquia": 2,
      "es_alerta": true,
      "que_es": "PRECAUCIÓN VIGENTE: no se publica P(sanción) de proyectos con origen Senado.",
      "notas": [
        "La base tiene sesgo de supervivencia: el modelo da 48% a proyectos del Senado contra 1,7% de Diputados, porque sólo están los que ya cruzaron a Diputados.",
        "No se parchea de a un síntoma: queda como insumo de la Revisión de las Comisiones. Decisión de Valle, 07-08."
      ],
      "modulo": "modelo/ensemble",
      "bloque": "final",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "e_backtest_cadena",
      "label": "backtest_cadena.py — NEUTRALIZADO",
      "rol": "script",
      "etapa": "evaluacion",
      "jerarquia": 3,
      "archivo": "modelo/ensemble/src/backtest_cadena.py",
      "modulo": "modelo/ensemble",
      "que_es": "NEUTRALIZADO el 22-08-2026: medía la v1. Su `main` levanta SystemExit con el motivo. Re-apuntarlo pide decidir ANTES contra que se mide.",
      "notas": [
        "p_sancion da skill +0,4478 en total, pero +0,2916 entre los 3.898 proyectos CON dictamen y -0,0257 entre los 34.799 sin el: su merito es separar con-dictamen de sin-dictamen, justo lo que la Puerta A ahora OBSERVA en vez de estimar.",
        "Medir la cadena nueva contra `sancionado` la mide contra algo que por diseño no predice: el 69% de los proyectos con dictamen que no llegan a ley se pierden en agenda.",
        "La unica vara con varianza real es el MARGEN del recuento (6.237 actas, 1.849 enganchadas a su expediente). DECISION PENDIENTE."
      ],
      "bloque": "fuera",
      "parqueada": true,
      "estado_declarado": "REPLANTEADO",
      "estado_motivo": "NEUTRALIZADO el 2026-08-22 (ADR-0012): medía la v1. Su `main` levanta SystemExit. Re-apuntarlo pide decidir antes contra que se mide.",
      "existe": true,
      "loc": 549,
      "simbolos": [
        {
          "nombre": "_root",
          "tipo": "funcion",
          "linea": 74,
          "doc": null
        },
        {
          "nombre": "_import_embudo",
          "tipo": "funcion",
          "linea": 78,
          "doc": null
        },
        {
          "nombre": "_import_nowcast_auto",
          "tipo": "funcion",
          "linea": 89,
          "doc": null
        },
        {
          "nombre": "_import_p_voto_revisora",
          "tipo": "funcion",
          "linea": 100,
          "doc": "Factor de la SEGUNDA cámara: reusa puerta_d.p_voto_revisora (Manera 1)."
        },
        {
          "nombre": "preparar_cohorte",
          "tipo": "funcion",
          "linea": 115,
          "doc": "Devuelve una fila por proyecto MADURO con: proyecto_id, fecha (point-in-time),"
        },
        {
          "nombre": "origen_fino_por_proyecto",
          "tipo": "funcion",
          "linea": 169,
          "doc": "Serie alineada a `cohorte` con el ORIGEN FINO de cada proyecto"
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "REPLANTEADO",
      "estado_fuente": "capa curada",
      "owner": "Claude+Valle (2026-07-12)",
      "estado_texto": "NEUTRALIZADO el 2026-08-22 (ADR-0012): medía la v1. Su `main` levanta SystemExit. Re-apuntarlo pide decidir antes contra que se mide.",
      "estado_modulo": "EN CURSO"
    },
    {
      "id": "e_baseline_embudo",
      "label": "Baseline: p_sancion del embudo",
      "rol": "variable",
      "etapa": "evaluacion",
      "jerarquia": 3,
      "que_es": "La vara. La pregunta que responde el backtest es si el roster nominal + agregador MEJORAN sobre el `p_sancion` que el embudo ya calcula solo.",
      "notas": [
        "Al 13-08 el resultado era empate técnico: skill del embudo 0,293 vs cadena con 2ª cámara empírica −0,025 sobre climatología 0,276.",
        "El límite conocido: sin condicionar la postura, el factor de mayoría multiplica por ~1 y no aporta."
      ],
      "modulo": "variables/embudo",
      "bloque": "fuera",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "e_backtest_embudo",
      "label": "backtest_embudo.json",
      "rol": "dato",
      "etapa": "evaluacion",
      "jerarquia": 1,
      "archivo_dato": "variables/embudo/outputs/backtest_embudo.json",
      "que_es": "Brier / AUC / calibración walk-forward del embudo solo, contra la tasa base.",
      "notas": [
        "Skill 0,3643 sancionado / 0,4195 recinto, medido el 07-08 sobre datos frescos."
      ],
      "bloque": "fuera",
      "archivo": "variables/embudo/outputs/backtest_embudo.json",
      "existe": true,
      "entrypoint": false,
      "modulo": "variables/embudo",
      "modulo_inferido": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)",
      "estado_fuente": "variables/embudo/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "e_baseline_bloque",
      "label": "Baseline de bloque (~0,99)",
      "rol": "variable",
      "etapa": "evaluacion",
      "jerarquia": 2,
      "modulo": "evaluacion/baseline",
      "que_es": "El piso medido en la Fase 0: predecir la dirección del voto individual mirando al bloque acierta ~0,99. Ese resultado ORDENA todo el proyecto.",
      "notas": [
        "Por eso el negocio no está en el voto individual medio, sino en asistencia, embudo, postura de bloque y las 10-20 bisagras."
      ],
      "bloque": "fuera",
      "estado": "HECHO",
      "estado_texto": "HECHO",
      "estado_fuente": "evaluacion/baseline/README.md",
      "owner": "vacante"
    },
    {
      "id": "e_metricas",
      "label": "evaluacion/metricas",
      "rol": "variable",
      "etapa": "evaluacion",
      "jerarquia": 1,
      "modulo": "evaluacion/metricas",
      "que_es": "Métricas comunes (Brier, calibración, accuracy en votos cruzados, cobertura de bandas). PENDIENTE: la carpeta está vacía; hoy cada módulo trae las suyas.",
      "es_hueco": true,
      "bloque": "fuera",
      "parqueada": true,
      "estado": "PENDIENTE",
      "estado_texto": "PENDIENTE",
      "estado_fuente": "evaluacion/metricas/README.md",
      "owner": "vacante"
    },
    {
      "id": "e_backtesting",
      "label": "evaluacion/backtesting",
      "rol": "variable",
      "etapa": "evaluacion",
      "jerarquia": 1,
      "modulo": "evaluacion/backtesting",
      "que_es": "Validación walk-forward con test de no-leakage, transversal al repo. PENDIENTE: la carpeta está vacía.",
      "es_hueco": true,
      "bloque": "fuera",
      "parqueada": true,
      "estado": "PENDIENTE",
      "estado_texto": "PENDIENTE",
      "estado_fuente": "evaluacion/backtesting/README.md",
      "owner": "vacante"
    },
    {
      "id": "h_dip2020",
      "label": "Hueco: Diputados 2020-23",
      "rol": "dato",
      "etapa": "bases",
      "jerarquia": 2,
      "es_hueco": true,
      "que_es": "Falta el tramo 2020-2023 de Diputados. PAUSADO a propósito desde el 10-07 (decisión de Valle: priorizar la puesta en marcha).",
      "notas": [
        "⚠ No es cosmético: invalida la ventana de postura del backtest de la cadena en ese período."
      ],
      "modulo": "datos/canonica",
      "parqueada": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,",
      "estado_fuente": "datos/canonica/README.md",
      "owner": "Claude+Franco (desde 2026-06-25)"
    },
    {
      "id": "h_api",
      "label": "producto/api",
      "rol": "variable",
      "etapa": "nowcast",
      "jerarquia": 1,
      "modulo": "producto/api",
      "es_hueco": true,
      "que_es": "Servir el nowcast por HTTP. FUTURO: no se abre sin pagador validado.",
      "bloque": "fuera",
      "parqueada": true,
      "estado": "FUTURO",
      "estado_texto": "FUTURO",
      "estado_fuente": "producto/api/README.md",
      "owner": "vacante"
    },
    {
      "id": "s_ingesta_od",
      "label": "ingesta_od.py + parser_od.py",
      "rol": "script",
      "etapa": "ingesta",
      "archivo": "datos/expedientes/src/parser_od.py",
      "modulo": "datos/expedientes",
      "que_es": "Baja los PDF de la Orden del Dia y saca los FIRMANTES del dictamen. El CKAN no los publica: el dato solo vive en el PDF.",
      "notas": [
        "Ancla del parser: 'Sala de las comisiones, <fecha>.' — la misma formula en las DOS camaras.",
        "En 2020-2021 esa formula NO EXISTE y las firmas se reconocen por su FORMA; salen marcadas sin_ancla y resuelven al 96,2%, la misma tasa que las demas.",
        "Lo que no se puede leer queda MARCADO con su motivo, no se descarta en silencio."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 487,
      "simbolos": [
        {
          "nombre": "Dictamen",
          "tipo": "clase",
          "linea": 117,
          "doc": null
        },
        {
          "nombre": "OrdenDelDia",
          "tipo": "clase",
          "linea": 125,
          "doc": null
        },
        {
          "nombre": "_normalizar",
          "tipo": "funcion",
          "linea": 143,
          "doc": "Colapsa los espacios que mete la extracción de PDF, sin tocar los saltos."
        },
        {
          "nombre": "_sin_acentos_mayus",
          "tipo": "funcion",
          "linea": 149,
          "doc": null
        },
        {
          "nombre": "_parece_nombre",
          "tipo": "funcion",
          "linea": 154,
          "doc": "Filtro conservador: preferimos perder un nombre raro a inventar uno."
        },
        {
          "nombre": "_firmantes_de",
          "tipo": "funcion",
          "linea": 176,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "d_firmas",
      "label": "dictamenes_firmas.parquet",
      "rol": "dato",
      "etapa": "bases",
      "modulo": "datos/expedientes",
      "que_es": "Quien firmo cada dictamen, en que caracter, con que disidencia y de que bloque. 125.504 firmas en Diputados (2008-2026) y 17.688 en el Senado.",
      "notas": [
        "Indexado por (proyecto, camara, comision, dictamen): un mismo expediente puede tener dictamen en las dos camaras.",
        "96,0% de las firmas emparejadas a un legislador concreto del padron."
      ],
      "bloque": "origen",
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO — backfill CKAN **refrescado el 07-08-2026**.",
      "estado_fuente": "datos/expedientes/README.md",
      "owner": "Claude+Franco (2026-07-11)"
    },
    {
      "id": "s_puerta_a",
      "label": "puerta_a.py",
      "rol": "script",
      "etapa": "origen",
      "archivo": "modelo/ensemble/src/puerta_a.py",
      "modulo": "modelo/ensemble",
      "que_es": "Lee el CARACTER observado del dictamen y lo convierte en un condicionante de la votacion de su camara. Sirve a A sobre B y a C sobre D.",
      "notas": [
        "Devuelve uno de tres estados y, cuando no hay dato, un condicionante que vale 0.",
        "Marca los ACUMULADOS: una Orden del Dia dictamina varios expedientes y su destino esta atado al texto unificado."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 445,
      "simbolos": [
        {
          "nombre": "_texto",
          "tipo": "funcion",
          "linea": 113,
          "doc": "Un faltante puede llegar como None, NaN o pd.NA según el backend de dtype."
        },
        {
          "nombre": "_fecha",
          "tipo": "funcion",
          "linea": 118,
          "doc": null
        },
        {
          "nombre": "_algun_si",
          "tipo": "funcion",
          "linea": 122,
          "doc": "¿Alguna fila dice que sí? Tolera None/NaN/pd.NA sin el downcast deprecado."
        },
        {
          "nombre": "_fecha_dictamen",
          "tipo": "funcion",
          "linea": 129,
          "doc": "Fecha del dictamen, en cascada, porque las dos cámaras no traen lo mismo."
        },
        {
          "nombre": "_n_expedientes",
          "tipo": "funcion",
          "linea": 169,
          "doc": "Cuántos expedientes dictamina la Orden del Día (el sumario los lista con `;`)."
        },
        {
          "nombre": "cargar_caracter",
          "tipo": "funcion",
          "linea": 185,
          "doc": "Una fila por (proyecto_id, camara) con el carácter observado del dictamen."
        }
      ],
      "lenguaje": "python",
      "entrypoint": false,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "s_padron_vigente",
      "label": "padron_vigente.py",
      "rol": "script",
      "etapa": "bases",
      "archivo": "datos/padron/src/padron_vigente.py",
      "modulo": "datos/padron",
      "que_es": "La foto de la camara a una fecha: UNA fila por banca. El padron oficial gana, el historico rellena lo que aquel no cubre.",
      "notas": [
        "Pegarlos sin mas da 513 diputados en vez de 257, y deduplicar por id tampoco alcanza: la misma persona tiene otro id en cada archivo cuando su nombre esta escrito distinto.",
        "Se resuelve con match por SUBCONJUNTO de tokens, la misma regla que empareja los firmantes. Un empate NUNCA se rompe por la fuerza: se cuenta como ambiguo.",
        "Control contra las bancas reales: 256/257/259/258/257 en cinco fechas, cero ambiguedades."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 186,
      "simbolos": [
        {
          "nombre": "_tokenizar",
          "tipo": "funcion",
          "linea": 79,
          "doc": "El tokenizador de `datos/expedientes` — el mismo que empareja las firmas."
        },
        {
          "nombre": "archivos_de",
          "tipo": "funcion",
          "linea": 88,
          "doc": "Los archivos de esa cámara, EN ORDEN DE PRIORIDAD: oficial primero."
        },
        {
          "nombre": "_vigentes",
          "tipo": "funcion",
          "linea": 96,
          "doc": null
        },
        {
          "nombre": "padron_vigente",
          "tipo": "funcion",
          "linea": 105,
          "doc": "Una fila por banca a `fecha`, oficial primero y el histórico rellenando."
        },
        {
          "nombre": "verificar",
          "tipo": "funcion",
          "linea": 159,
          "doc": "Contrasta el conteo contra las bancas reales. El control que puede decir NO."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)",
      "estado_fuente": "datos/padron/README.md",
      "owner": "Valle (2026-07-14)"
    },
    {
      "id": "s_nowcast_puertas",
      "label": "nowcast_puertas.py",
      "rol": "script",
      "etapa": "nowcast",
      "archivo": "modelo/ensemble/src/nowcast_puertas.py",
      "modulo": "modelo/ensemble",
      "que_es": "EL PUNTO DE ENTRADA. Entra un proyecto —real o hipotetico— y corre la cadena HACIA ADELANTE sobre la configuracion actual de las dos camaras.",
      "notas": [
        "Devuelve el numero CON el desagregado por legislador: quien acompaña, quien no, sobre quien hay incognita y a quien ir a buscar.",
        "El tablero por legislador y la probabilidad salen del MISMO calculo: antes eran dos, y la tabla contradecia al numero.",
        "No reimplementa nada: reusa roster_nominal, simular_con_guardas, proyectar_postura, puerta_a y puerta_d."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 479,
      "simbolos": [
        {
          "nombre": "_bloque",
          "tipo": "funcion",
          "linea": 79,
          "doc": null
        },
        {
          "nombre": "alineacion_individual",
          "tipo": "funcion",
          "linea": 88,
          "doc": "P(afirmativo) de CADA legislador sobre su PROPIO récord."
        },
        {
          "nombre": "perfil_legislador",
          "tipo": "funcion",
          "linea": 136,
          "doc": "Cómo se espera que vote esta persona. Devuelve p_afirma_si_vota y p_presente."
        },
        {
          "nombre": "a_linea_y_desvio",
          "tipo": "funcion",
          "linea": 178,
          "doc": "Traduce una P(afirmativo) al par (línea, desvío) que el agregador reproduce."
        },
        {
          "nombre": "_p_afirmativo_del_simulador",
          "tipo": "funcion",
          "linea": 199,
          "doc": "P(este legislador vote AFIRMATIVO) según el MISMO modelo que simula la votación."
        },
        {
          "nombre": "armar_roster",
          "tipo": "funcion",
          "linea": 215,
          "doc": "Perfil de cada legislador -> los arrays que entran al agregador."
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "c_guardas",
      "label": "Guardas de sobreconfianza",
      "rol": "variable",
      "etapa": "origen",
      "archivo": "modelo/ensemble/src/ensemble.py",
      "modulo": "modelo/ensemble",
      "formula": "piso de desvío 0,02 · P(mayoría) ∈ [1%, 99%]",
      "que_es": "Ni el legislador mas leal es un lock, y ninguna votacion es 0%/100%: hay riesgo sistemico que la independencia entre legisladores no capta.",
      "notas": [
        "Un SOLO lugar en todo el repo, y hay un test que recorre el codigo y falla si alguien define las constantes en otro archivo.",
        "Hasta el 22-08 vivian solo en el camino de la v1: la Puerta D devolvia el numero CRUDO y un roster unanime le daba 1,0 exacto."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 396,
      "simbolos": [
        {
          "nombre": "_cargar_simulador",
          "tipo": "funcion",
          "linea": 68,
          "doc": "Importa simular_votacion del agregador sin tocar su código."
        },
        {
          "nombre": "_cargar_proyector",
          "tipo": "funcion",
          "linea": 81,
          "doc": "Importa cargar + proyectar_postura de variables/bloque (contrato publico)."
        },
        {
          "nombre": "componer",
          "tipo": "funcion",
          "linea": 107,
          "doc": "DADA DE BAJA (2026-08-22) - era el corazon de la v1. Ver `_BAJA_V1`."
        },
        {
          "nombre": "_root",
          "tipo": "funcion",
          "linea": 115,
          "doc": null
        },
        {
          "nombre": "_padron_csv",
          "tipo": "funcion",
          "linea": 119,
          "doc": null
        },
        {
          "nombre": "_disciplina_csv",
          "tipo": "funcion",
          "linea": 126,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "EN CURSO",
      "estado_texto": "EN CURSO (v1: composición + nowcast por proyecto + tests)",
      "estado_fuente": "modelo/ensemble/README.md",
      "owner": "Claude+Valle (2026-07-12)"
    },
    {
      "id": "x_nowcast_puertas_html",
      "label": "Nowcast-Puertas.html",
      "rol": "resultado",
      "etapa": "nowcast",
      "archivo": "casos/nowcast_puertas_html.py",
      "modulo": "casos",
      "que_es": "El entregable: la cadena a la vista con lo que se OBSERVA y lo que se CALCULA distinguido, el slider de clima, y la tabla por legislador.",
      "notas": [
        "Dice en pantalla que el numero es CONDICIONAL, y avisa cuando esta en el techo de confianza para que un slider que no mueve nada no se lea como un slider roto."
      ],
      "bloque": "origen",
      "existe": true,
      "loc": 373,
      "simbolos": [
        {
          "nombre": "icg_del_mes",
          "tipo": "funcion",
          "linea": 45,
          "doc": "El ICG del mes de la fecha; si no está, el más nuevo que haya."
        },
        {
          "nombre": "construir",
          "tipo": "funcion",
          "linea": 62,
          "doc": null
        },
        {
          "nombre": "escribir",
          "tipo": "funcion",
          "linea": 75,
          "doc": null
        },
        {
          "nombre": "main",
          "tipo": "funcion",
          "linea": 81,
          "doc": null
        }
      ],
      "lenguaje": "python",
      "entrypoint": true,
      "estado": "",
      "owner": "—",
      "estado_texto": "su README no declara `**Estado:**`"
    }
  ],
  "links": [
    {
      "de": "f_ckan",
      "a": "s_ckan_to_canonical",
      "tipo": "flujo"
    },
    {
      "de": "f_ckan",
      "a": "s_ingesta_ckan",
      "tipo": "flujo"
    },
    {
      "de": "f_ckan",
      "a": "s_bajar_nomina",
      "tipo": "flujo"
    },
    {
      "de": "f_hcdn_tp",
      "a": "s_tp_diputados",
      "tipo": "flujo"
    },
    {
      "de": "f_senado",
      "a": "s_dae_senado",
      "tipo": "flujo"
    },
    {
      "de": "f_senado",
      "a": "s_scrape_senado",
      "tipo": "flujo"
    },
    {
      "de": "f_senado",
      "a": "s_giros",
      "tipo": "flujo"
    },
    {
      "de": "f_argentinadatos",
      "a": "s_argdatos",
      "tipo": "flujo"
    },
    {
      "de": "f_wikipedia",
      "a": "s_wiki_anexos",
      "tipo": "flujo"
    },
    {
      "de": "f_utdt",
      "a": "s_ingesta_icg",
      "tipo": "flujo"
    },
    {
      "de": "f_decada",
      "a": "s_decada_csv",
      "tipo": "flujo"
    },
    {
      "de": "f_excel_franco",
      "a": "s_manual_2026",
      "tipo": "flujo"
    },
    {
      "de": "s_bot_diario",
      "a": "s_tp_diputados",
      "tipo": "config",
      "nota": "lo dispara"
    },
    {
      "de": "s_bot_diario",
      "a": "s_dae_senado",
      "tipo": "config",
      "nota": "lo dispara"
    },
    {
      "de": "s_bot_diario",
      "a": "s_bot_votaciones",
      "tipo": "config",
      "nota": "lo dispara"
    },
    {
      "de": "s_icg_mensual",
      "a": "s_ingesta_icg",
      "tipo": "config",
      "nota": "lo dispara"
    },
    {
      "de": "s_padron_vivo",
      "a": "s_vigilar_padron",
      "tipo": "config",
      "nota": "lo dispara"
    },
    {
      "de": "s_ckan_to_canonical",
      "a": "s_canonica_build",
      "tipo": "flujo"
    },
    {
      "de": "s_argdatos",
      "a": "s_canonica_build",
      "tipo": "flujo"
    },
    {
      "de": "s_scrape_senado",
      "a": "s_canonica_build",
      "tipo": "flujo"
    },
    {
      "de": "s_decada_csv",
      "a": "s_canonica_build",
      "tipo": "flujo"
    },
    {
      "de": "s_manual_2026",
      "a": "s_canonica_build",
      "tipo": "flujo",
      "nota": "máxima precedencia"
    },
    {
      "de": "s_bot_votaciones",
      "a": "s_canonica_build",
      "tipo": "flujo"
    },
    {
      "de": "s_canonica_build",
      "a": "d_canonica_actas",
      "tipo": "flujo"
    },
    {
      "de": "s_canonica_build",
      "a": "d_canonica_votos",
      "tipo": "flujo"
    },
    {
      "de": "s_canonica_build",
      "a": "s_entity_res",
      "tipo": "flujo"
    },
    {
      "de": "s_entity_res",
      "a": "d_canonica_resuelto",
      "tipo": "flujo"
    },
    {
      "de": "d_canonica_votos",
      "a": "s_export_base",
      "tipo": "flujo"
    },
    {
      "de": "s_export_base",
      "a": "d_export",
      "tipo": "flujo"
    },
    {
      "de": "h_dip2020",
      "a": "d_canonica_votos",
      "tipo": "alerta",
      "nota": "tramo faltante"
    },
    {
      "de": "s_ingesta_ckan",
      "a": "s_migrar_ckan",
      "tipo": "flujo"
    },
    {
      "de": "s_ingesta_ckan",
      "a": "d_acta_expediente",
      "tipo": "flujo"
    },
    {
      "de": "s_tp_diputados",
      "a": "d_tp_entradas",
      "tipo": "flujo"
    },
    {
      "de": "s_dae_senado",
      "a": "d_tp_entradas",
      "tipo": "flujo"
    },
    {
      "de": "d_tp_entradas",
      "a": "s_upsert_bot",
      "tipo": "flujo"
    },
    {
      "de": "s_upsert_bot",
      "a": "d_proyectos_db",
      "tipo": "flujo"
    },
    {
      "de": "s_migrar_ckan",
      "a": "d_proyectos_db",
      "tipo": "flujo"
    },
    {
      "de": "s_cuarentena",
      "a": "d_cuarentena_db",
      "tipo": "alerta",
      "nota": "lo dudoso, aparte"
    },
    {
      "de": "s_cuarentena",
      "a": "d_proyectos_db",
      "tipo": "alerta"
    },
    {
      "de": "s_verificar",
      "a": "d_proyectos_db",
      "tipo": "alerta",
      "nota": "14 invariantes que cortan la carga"
    },
    {
      "de": "s_verificar",
      "a": "s_embudo",
      "tipo": "alerta",
      "nota": "control de cohorte: lo invoca como proceso"
    },
    {
      "de": "d_canonica_actas",
      "a": "s_enlace_senado",
      "tipo": "flujo"
    },
    {
      "de": "s_enlace_senado",
      "a": "d_acta_expediente",
      "tipo": "flujo"
    },
    {
      "de": "s_actas_ley",
      "a": "d_acta_expediente",
      "tipo": "alerta",
      "nota": "filtro de LEY con auditoría humana"
    },
    {
      "de": "s_giros",
      "a": "d_acta_expediente",
      "tipo": "flujo"
    },
    {
      "de": "s_bajar_nomina",
      "a": "d_padron_dip",
      "tipo": "flujo"
    },
    {
      "de": "s_bajar_nomina",
      "a": "d_padron_sen",
      "tipo": "flujo"
    },
    {
      "de": "s_wiki_anexos",
      "a": "s_padron_hist",
      "tipo": "flujo"
    },
    {
      "de": "s_bajar_nomina",
      "a": "s_padron_hist",
      "tipo": "flujo"
    },
    {
      "de": "s_padron_hist",
      "a": "d_padron_sen_hist",
      "tipo": "flujo"
    },
    {
      "de": "d_padron_linaje",
      "a": "s_bloque",
      "tipo": "config",
      "nota": "override manual de linaje, 22/22"
    },
    {
      "de": "d_bloques_senado",
      "a": "s_bloque",
      "tipo": "config"
    },
    {
      "de": "s_vigilar_padron",
      "a": "d_padron_dip",
      "tipo": "alerta",
      "nota": "avisa si cambió la composición"
    },
    {
      "de": "s_vigilar_padron",
      "a": "d_padron_sen",
      "tipo": "alerta"
    },
    {
      "de": "d_excel_2026",
      "a": "s_manual_2026",
      "tipo": "flujo"
    },
    {
      "de": "d_proyectos_db",
      "a": "s_embudo",
      "tipo": "flujo",
      "nota": "denominador del embudo (ADR-0009)"
    },
    {
      "de": "d_acta_expediente",
      "a": "s_embudo",
      "tipo": "flujo"
    },
    {
      "de": "d_icg_mensual",
      "a": "s_embudo",
      "tipo": "config",
      "nota": "rezagado un mes, anti-leakage"
    },
    {
      "de": "d_features_proyecto",
      "a": "s_embudo",
      "tipo": "config",
      "nota": "tema y origen, si existen"
    },
    {
      "de": "s_embudo",
      "a": "d_p_embudo",
      "tipo": "flujo"
    },
    {
      "de": "s_embudo",
      "a": "d_embudo_etapas",
      "tipo": "flujo"
    },
    {
      "de": "s_embudo",
      "a": "v_embudo",
      "tipo": "calcula"
    },
    {
      "de": "d_p_embudo",
      "a": "v_embudo",
      "tipo": "flujo"
    },
    {
      "de": "d_canonica_resuelto",
      "a": "s_bloque",
      "tipo": "flujo"
    },
    {
      "de": "d_canonica_resuelto",
      "a": "s_disciplina",
      "tipo": "flujo"
    },
    {
      "de": "d_canonica_resuelto",
      "a": "s_ficha",
      "tipo": "flujo"
    },
    {
      "de": "d_canonica_resuelto",
      "a": "s_asistencia",
      "tipo": "flujo"
    },
    {
      "de": "d_tema_por_acta",
      "a": "s_bloque",
      "tipo": "config",
      "nota": "condiciona la postura por tema"
    },
    {
      "de": "d_origen_por_acta",
      "a": "s_bloque",
      "tipo": "config",
      "nota": "condiciona la postura por origen"
    },
    {
      "de": "s_bloque",
      "a": "v_bloque",
      "tipo": "calcula"
    },
    {
      "de": "s_disciplina",
      "a": "d_disciplina",
      "tipo": "flujo"
    },
    {
      "de": "d_disciplina",
      "a": "v_voto_individual",
      "tipo": "flujo"
    },
    {
      "de": "s_ficha",
      "a": "v_legislador",
      "tipo": "calcula"
    },
    {
      "de": "s_asistencia",
      "a": "v_asistencia",
      "tipo": "calcula"
    },
    {
      "de": "d_proyectos_db",
      "a": "s_origen_lider",
      "tipo": "flujo"
    },
    {
      "de": "d_taxonomias",
      "a": "s_agente_taxonomias",
      "tipo": "config",
      "nota": "catálogo cerrado, 74 ids"
    },
    {
      "de": "s_agente_taxonomias",
      "a": "s_tema_por_acta",
      "tipo": "flujo"
    },
    {
      "de": "s_tema_por_acta",
      "a": "d_tema_por_acta",
      "tipo": "flujo"
    },
    {
      "de": "s_origen_lider",
      "a": "d_origen_por_acta",
      "tipo": "flujo"
    },
    {
      "de": "s_origen_lider",
      "a": "d_features_proyecto",
      "tipo": "flujo"
    },
    {
      "de": "d_jefes_bloque",
      "a": "s_origen_lider",
      "tipo": "config"
    },
    {
      "de": "s_ingesta_icg",
      "a": "d_icg_mensual",
      "tipo": "flujo"
    },
    {
      "de": "d_icg_mensual",
      "a": "s_modulador_icg",
      "tipo": "flujo"
    },
    {
      "de": "s_modulador_icg",
      "a": "v_proyecto",
      "tipo": "calcula",
      "nota": "gamma: encoge el desvío de las bisagras"
    },
    {
      "de": "s_origen_lider",
      "a": "v_proyecto",
      "tipo": "calcula"
    },
    {
      "de": "d_features_proyecto",
      "a": "v_proyecto",
      "tipo": "flujo"
    },
    {
      "de": "v_contexto",
      "a": "v_proyecto",
      "tipo": "alerta",
      "nota": "FUTURO: no existe"
    },
    {
      "de": "v_bloque",
      "a": "c_roster_origen",
      "tipo": "flujo",
      "nota": "la línea de cada legislador"
    },
    {
      "de": "v_voto_individual",
      "a": "c_roster_origen",
      "tipo": "flujo",
      "nota": "la tasa de desvío de cada uno"
    },
    {
      "de": "d_padron_dip",
      "a": "c_roster_origen",
      "tipo": "flujo",
      "nota": "quién estaba esa fecha"
    },
    {
      "de": "d_padron_sen",
      "a": "c_roster_origen",
      "tipo": "flujo"
    },
    {
      "de": "v_legislador",
      "a": "c_roster_origen",
      "tipo": "config"
    },
    {
      "de": "v_asistencia",
      "a": "c_simular_origen",
      "tipo": "config",
      "nota": "quién se cuenta como presente"
    },
    {
      "de": "v_proyecto",
      "a": "c_simular_origen",
      "tipo": "config",
      "nota": "tipo de mayoría requerida"
    },
    {
      "de": "v_proyecto",
      "a": "v_bloque",
      "tipo": "config",
      "nota": "tema y origen condicionan la postura"
    },
    {
      "de": "c_roster_origen",
      "a": "c_simular_origen",
      "tipo": "flujo"
    },
    {
      "de": "c_simular_origen",
      "a": "c_p_mayoria_origen",
      "tipo": "calcula"
    },
    {
      "de": "g_A",
      "a": "g_B",
      "tipo": "calcula"
    },
    {
      "de": "c_p_mayoria_origen",
      "a": "g_B",
      "tipo": "calcula",
      "nota": "misma maquinaria, otro lenguaje"
    },
    {
      "de": "g_B",
      "a": "g_C",
      "tipo": "calcula"
    },
    {
      "de": "d_acta_expediente",
      "a": "g_C",
      "tipo": "flujo",
      "nota": "estado observado"
    },
    {
      "de": "d_padron_sen_hist",
      "a": "c_roster_revisora",
      "tipo": "flujo",
      "nota": "padrón histórico: sin esto no hay D"
    },
    {
      "de": "d_padron_dip",
      "a": "c_roster_revisora",
      "tipo": "flujo"
    },
    {
      "de": "v_bloque",
      "a": "c_roster_revisora",
      "tipo": "flujo",
      "nota": "la MISMA maquinaria de postura que en origen"
    },
    {
      "de": "v_voto_individual",
      "a": "c_roster_revisora",
      "tipo": "flujo"
    },
    {
      "de": "s_enlace_senado",
      "a": "g_D",
      "tipo": "config",
      "nota": "los ~243 casos de dos cámaras"
    },
    {
      "de": "c_roster_revisora",
      "a": "g_D",
      "tipo": "flujo"
    },
    {
      "de": "c_simular_origen",
      "a": "g_D",
      "tipo": "config",
      "nota": "reusa simular_votacion, no reimplementa"
    },
    {
      "de": "g_C",
      "a": "g_D",
      "tipo": "calcula"
    },
    {
      "de": "g_A",
      "a": "n_puertas",
      "tipo": "calcula"
    },
    {
      "de": "g_B",
      "a": "n_puertas",
      "tipo": "calcula"
    },
    {
      "de": "g_C",
      "a": "n_puertas",
      "tipo": "calcula"
    },
    {
      "de": "g_D",
      "a": "n_puertas",
      "tipo": "calcula"
    },
    {
      "de": "n_colapso",
      "a": "n_puertas",
      "tipo": "config",
      "nota": "puerta ocurrida ⇒ vale 1"
    },
    {
      "de": "n_puertas",
      "a": "n_salida",
      "tipo": "flujo",
      "nota": "el numero publicado, condicional a que las camaras voten"
    },
    {
      "de": "n_alerta_senado",
      "a": "n_salida",
      "tipo": "alerta",
      "nota": "no publicar origen Senado"
    },
    {
      "de": "h_api",
      "a": "n_salida",
      "tipo": "alerta",
      "nota": "FUTURO"
    },
    {
      "de": "d_p_embudo",
      "a": "e_backtest_cadena",
      "tipo": "flujo",
      "nota": "cohorte madura + label sancionado"
    },
    {
      "de": "e_backtest_cadena",
      "a": "e_baseline_embudo",
      "tipo": "alerta",
      "nota": "se mide CONTRA esto"
    },
    {
      "de": "s_embudo",
      "a": "e_backtest_embudo",
      "tipo": "flujo"
    },
    {
      "de": "e_backtest_embudo",
      "a": "e_baseline_embudo",
      "tipo": "flujo"
    },
    {
      "de": "e_baseline_bloque",
      "a": "e_backtest_cadena",
      "tipo": "config",
      "nota": "el piso de la Fase 0"
    },
    {
      "de": "e_metricas",
      "a": "e_backtest_cadena",
      "tipo": "alerta",
      "nota": "PENDIENTE"
    },
    {
      "de": "e_backtesting",
      "a": "e_backtest_cadena",
      "tipo": "alerta",
      "nota": "PENDIENTE"
    },
    {
      "de": "h_dip2020",
      "a": "e_backtest_cadena",
      "tipo": "alerta",
      "nota": "invalida la ventana de postura 2020-23"
    },
    {
      "de": "d_padron_sen",
      "a": "e_backtest_cadena",
      "tipo": "alerta",
      "nota": "sólo 72 vigentes ⇒ el backtest corre sobre Diputados"
    },
    {
      "de": "c_p_mayoria_origen",
      "a": "g_D",
      "tipo": "condiciona",
      "nota": "P(aprobar en Revisora | se aprobo en Origen)",
      "detalle": "No es flujo de datos: `puerta_d.py` no lee la P de origen. Lo que cambia es el SUPUESTO — con media sancion, el dictamen y la votacion de origen ya ocurrieron y valen 1, y el numero queda [C observada] · P(D)."
    },
    {
      "de": "s_ingesta_od",
      "a": "d_firmas",
      "tipo": "flujo"
    },
    {
      "de": "d_firmas",
      "a": "s_puerta_a",
      "tipo": "flujo",
      "nota": "el caracter observado del dictamen"
    },
    {
      "de": "d_padron_dip",
      "a": "s_padron_vigente",
      "tipo": "flujo",
      "nota": "el oficial gana"
    },
    {
      "de": "s_padron_vigente",
      "a": "c_roster_origen",
      "tipo": "flujo",
      "nota": "la foto completa de la camara"
    },
    {
      "de": "s_padron_vigente",
      "a": "c_roster_revisora",
      "tipo": "flujo"
    },
    {
      "de": "s_puerta_a",
      "a": "g_A",
      "tipo": "calcula"
    },
    {
      "de": "s_puerta_a",
      "a": "g_C",
      "tipo": "calcula"
    },
    {
      "de": "g_A",
      "a": "c_p_mayoria_origen",
      "tipo": "condiciona",
      "nota": "el caracter CONDICIONA la votacion; no la multiplica",
      "detalle": "Sin dictamen leido el condicionante se encoge a 0 y queda la estimacion sin condicionar. Hoy vale 0 para todos: falta contra que calibrarlo."
    },
    {
      "de": "c_guardas",
      "a": "c_p_mayoria_origen",
      "tipo": "config",
      "nota": "nunca 0%/100%"
    },
    {
      "de": "c_guardas",
      "a": "g_D",
      "tipo": "config",
      "nota": "la Puerta D hereda las MISMAS guardas desde el 22-08"
    },
    {
      "de": "s_nowcast_puertas",
      "a": "n_puertas",
      "tipo": "calcula"
    },
    {
      "de": "c_p_mayoria_origen",
      "a": "s_nowcast_puertas",
      "tipo": "flujo",
      "nota": "paso B"
    },
    {
      "de": "g_D",
      "a": "s_nowcast_puertas",
      "tipo": "flujo",
      "nota": "paso D"
    },
    {
      "de": "n_puertas",
      "a": "x_nowcast_puertas_html",
      "tipo": "flujo"
    },
    {
      "de": "f_hcdn_tp",
      "a": "s_ingesta_od",
      "tipo": "flujo",
      "nota": "los PDF de la Orden del Dia (el CKAN no publica firmantes)"
    },
    {
      "de": "f_senado",
      "a": "s_ingesta_od",
      "tipo": "flujo",
      "nota": "el Senado publica sus Ordenes del Dia por su propia via"
    },
    {
      "de": "v_embudo",
      "a": "e_baseline_embudo",
      "tipo": "flujo",
      "nota": "p_sancion: la unica vara que sobrevive a la baja de la v1",
      "detalle": "`p_sancion` NO entra a la cadena: ya contiene A, B, C y D adentro, asi que meterlo como factor la haria multiplicarse por si misma. Su lugar es la baseline."
    }
  ]
};
