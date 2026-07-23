# -*- coding: utf-8 -*-
"""Cierre del 2026-07-22 (tercera tanda): registra (1) el ROSTER NOMINAL en el
ensemble (se eliminó _expandir_roster + demo + comando nowcast a mano; el motor
simula legislador por legislador con su desvío individual — cimiento "las partes
hacen al todo"), y (2) el ORIGEN POR ACTA (nuevo origen_por_acta.py: quién impulsa
+ gobierno de turno por acta), el LEVER que endereza el 1167. Corre LOCAL:

    python coordinacion/_aplicar_roster_nominal_2026-07-22.py

Idempotente y defensivo. Toca ESTADO, TABLERO, EN-HUMANO, tablero_datos.js.
El código (ensemble.py, origen_por_acta.py, bloque.py) ya quedó aplicado y testeado
en la sesión (tests: ensemble 29, origen_por_acta 14, bloque_origen 8, + regresión
bloque 7+5, agregador 26, origen_lider 24 = todo verde).
"""
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]


def parche(archivo, reemplazos=(), inserciones=()):
    p = RAIZ / archivo
    if not p.exists():
        print(f"  [SKIP] no existe {archivo}"); return
    s = p.read_text(encoding="utf-8"); n = len(s); hechos = 0
    for viejo, nuevo in reemplazos:
        if nuevo in s:
            continue
        if viejo in s:
            s = s.replace(viejo, nuevo, 1); hechos += 1
        else:
            print(f"  [AVISO] ancla no encontrada en {archivo}: {viejo[:65]!r}")
    for ancla, bloque in inserciones:
        if bloque.strip() in s:
            continue
        if ancla in s:
            s = s.replace(ancla, ancla + bloque, 1); hechos += 1
        else:
            print(f"  [AVISO] inserción no encontrada en {archivo}: {ancla[:45]!r}")
    p.write_text(s, encoding="utf-8")
    print(f"  {archivo}: {hechos} cambios ({n} -> {len(s)} bytes)")


ESTADO = (
'### [2026-07-22 · cierre 3] modelo/ensemble (ROSTER NOMINAL) + variables/proyecto (origen_por_acta) — el motor vuelve al cimiento individual y el ORIGEN endereza el 1167\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** (1) **ROSTER NOMINAL en el ensemble.** Se ELIMINÓ `_expandir_roster` (clonaba el desvío PROMEDIO del bloque `bancas` veces, aplicándoselo también a los 753 legisladores con desvío ya medido) junto con el comando `demo` y el `nowcast` con escenario JSON a mano (eran de la puesta en marcha del 10-jul). Ahora `nowcast_auto` arma UNA FILA POR LEGISLADOR del padrón oficial vigente a la fecha, cada uno con SU tasa de desvío individual por escalera reciente→global→bloque (fallback al promedio de bloque SOLO para quien no tiene historial — la única excepción admitida, ej. camada 2025-29). Coherente con el principio "las partes hacen al todo". (2) **`variables/proyecto/src/origen_por_acta.py` (NUEVO).** Etiqueta cada acta con `origen` (EJECUTIVO/OFICIALISMO/OPOSICION/DESCONOCIDO), `origen_lado` (GOBIERNO/OPOSICION) y `gobierno` (KIRCHNER/MACRI/AF/MILEI a la FECHA DEL ACTA, no de la presentación) por 3 vías determinísticas sin API key (código de expediente → O.D.→expedientes_resultados → match de título). 2.170/5.333 actas etiquetadas (40,7%). `variables/bloque` fusiona ese contrato en `cargar_tema_por_acta` y condiciona la dirección por origen fino O por lado, con **guard de mismo gobierno** (no mezcla eras dentro de la ventana de 730 días: un bloque cambia de lado con el recambio del 10-dic).\n'
'- **HALLAZGO CONFIRMADO (el lever del 1167):** condicionar por **ORIGEN=GOBIERNO** endereza el signo político que el tema solo invertía. En 1167-D-2025 @2026 (reforma laboral del PE), sobre 23 actas de origen GOBIERNO en la ventana: **LLA pasa de share 0,33 (NEGATIVO) a 0,88 (AFIRMATIVO)** y el **kirchnerismo de 0,85 (AFIRMATIVO) a 0,44 (NEGATIVO)** — al derecho. `--tema TRAB --origen GOBIERNO` da 0 actas (no hay esa intersección en la ventana): el eje que manda es el ORIGEN, como anticipaba la nota del cierre anterior.\n'
'- **Cómo:** `python variables\\proyecto\\src\\origen_por_acta.py` (llena `data/origen_por_acta.parquet`); `python modelo\\ensemble\\src\\ensemble.py nowcast_auto 1167-D-2025 2026-07-14 diputados SIMPLE 1.0 --origen GOBIERNO`. Tests: ensemble 29 (roster nominal + escalera + "las bisagras bajan P(mayoría)"), origen_por_acta 14 (incluye el caso PRO oficialista-2017 vs opositor-2021), bloque_origen 8 (lado + guard de gobierno), regresión bloque 7+5 / agregador 26 / origen_lider 24 — TODO verde.\n'
'- **Archivos:** `modelo/ensemble/src/ensemble.py` (roster_nominal + nowcast_proyecto/nowcast_auto nominales; se fue _expandir_roster/_demo), `modelo/ensemble/tests/test_ensemble.py` (reescrito v3), `variables/proyecto/src/origen_por_acta.py` (nuevo), `variables/proyecto/tests/test_origen_por_acta.py` (nuevo), `variables/proyecto/data/origen_por_acta.parquet` (nuevo), `variables/bloque/src/bloque.py` (cargar_tema_por_acta fusiona origen + _cond_map + guard de gobierno en _match), `variables/bloque/tests/test_bloque_origen.py` (nuevo), `coordinacion/{ESTADO,TABLERO,EN-HUMANO}`, `tablero_datos.js`.\n'
'- **Estado del módulo:** modelo/ensemble EN CURSO (roster nominal individual; falta backtest de la cadena completa con origen enchufado); variables/proyecto EN CURSO (origen por acta al 40,7%; se puede subir con la 2ª vía de O.D. y sumando acta_expediente).\n'
'- **Próximo paso:** (1) subir la cobertura de origen_por_acta (hoy 40,7%: faltan sobre todo Senado viejo y actas sin código/O.D.); (2) enchufar `--origen` por default en `nowcast_auto` leyendo el origen del PROPIO proyecto objetivo (hoy se pasa a mano); (3) backtest de la cadena con roster nominal + origen; (4) multitemáticas (proteger vs. desregular dentro de TRAB).\n\n'
)

parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    reemplazos=[
        ('| modelo/ensemble | EN CURSO (v1 bicameral: nowcast_auto por cámara; caso testigo 1167-D-2025 Dip 137/123 · Sen 61/33, ambas ~100% = artefacto de dirección incondicional → motiva v2 por tema/origen) | Claude+Valle |',
         '| modelo/ensemble | EN CURSO (ROSTER NOMINAL: simula legislador por legislador con desvío individual; se eliminó _expandir_roster/demo. Origen=GOBIERNO endereza el 1167. Falta backtest de la cadena) | Claude+Valle |'),
        ('| variables/proyecto | EN CURSO (vocabulario validado; ICG vivo; origen+líder listos; NUEVO puente tema_por_acta ~890 actas votadas→tema; falta correr batch/tagger con API key) | Valle |',
         '| variables/proyecto | EN CURSO (tema_por_acta 1537 actas; NUEVO origen_por_acta: quién impulsa + gobierno por acta, 40,7% etiquetado, determinístico sin API key; falta subir cobertura) | Valle |'),
        ('| variables/bloque | EN CURSO (v2: dirección de bloque CONDICIONADA por tema/origen con shrinkage; sin tema = v1 idéntico; 16 tests OK; falta correrlo con temas reales) | Claude+Valle |',
         '| variables/bloque | EN CURSO (dirección condicionada por tema/origen con shrinkage; origen por lado GOBIERNO/OPOSICION + guard de mismo gobierno; 24 tests OK; enderezó el 1167) | Claude+Valle |'),
    ],
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('| modelo/ensemble | Claude+Valle | 2026-07-12 | P(aprob)=P(llega)×P(mayoría). v2 (2026-07-22): nowcast_auto acepta --tema/--origen y condiciona la dirección de bloque (consume tema_por_acta); sin tema = v1. Re-corrida 1167@2026 con tema=TRAB NO mueve → HALLAZGO: el ORIGEN (quién impulsa) manda sobre el tema; falta etiquetar origen por acta. Temas 2011-2026 completos (1537 actas) |',
         '| modelo/ensemble | Claude+Valle | 2026-07-12 | ROSTER NOMINAL (2026-07-22): nowcast_auto simula UNA FILA POR LEGISLADOR (padrón vigente + desvío individual, escalera reciente→global→bloque); se eliminó _expandir_roster/demo. Con --origen GOBIERNO el 1167 se endereza (LLA 0,33→0,88; K 0,85→0,44). Falta backtest de la cadena y enchufar --origen automático |'),
        ('| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + vocabulario validado (88 actas) + ICG (296 meses) + origen/líder. NUEVO (2026-07-22): tema_por_acta.py = puente que clasifica por TEXTO ~890 títulos de actas votadas → acta_id→tema para el v2 de bloque (4 tests). Falta corrida con API key |',
         '| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + ICG + origen/líder + tema_por_acta (1537 actas). NUEVO (2026-07-22): origen_por_acta.py = quién impulsa (EJECUTIVO/OFICIALISMO/OPOSICION) + gobierno de turno POR ACTA, determinístico sin API key (3 vías: código/O.D./título); 40,7% etiquetado + 14 tests. Falta subir cobertura |'),
    ])

ENH = (
'\n## Avance: volvimos el motor al cimiento (mide legislador por legislador) y probamos que el ORIGEN endereza el caso que estaba al revés\n'
'Dos cosas en esta tanda. Primero, corregimos un atajo viejo: el motor, en el último paso, agarraba el promedio de cada bloque y lo repetía tantas veces como bancas —tratando a los 257 diputados como 7 promedios fotocopiados—, justo lo contrario del cimiento del proyecto (medir a cada legislador y que el conjunto surja de las partes). Ahora el nowcast arma la lista real de legisladores vigentes según el padrón oficial y le pone a cada uno SU propia tasa de "cuánto se aparta de su bloque"; sólo cuando alguien no tiene historial (por ejemplo la camada que asumió en diciembre) usamos el promedio del bloque como red. Sacamos también la demo y el modo "escenario a mano", que ya no hacían falta.\n\n'
'Segundo, resolvimos lo que había quedado pendiente la vez pasada: etiquetar cada votación con QUIÉN impulsa la ley (el Ejecutivo, un legislador del oficialismo o de la oposición) y bajo qué gobierno se votó. Con eso, al re-correr la reforma laboral del gobierno (1167) pidiéndole al modelo que mire sólo las votaciones impulsadas por el gobierno, el signo se acomodó: La Libertad Avanza pasó a estar A FAVOR (de 0,33 a 0,88) y el kirchnerismo EN CONTRA (de 0,85 a 0,44), como en la realidad. Lo hicimos sin gastar en clasificar PDFs: se cruzan los datos de expedientes que ya teníamos. Además dejamos una regla fina para no mezclar épocas: un mismo bloque es oficialista en un gobierno y opositor en el siguiente, así que al condicionar por origen el modelo sólo mira votaciones del mismo gobierno que la fecha que se está prediciendo. Queda por subir la cobertura del etiquetado (hoy llega al 41% de las votaciones) y hacer que el modelo tome el origen del propio proyecto de forma automática.\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "el ORIGEN endereza el caso que estaba al revés" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(ENH)
    print("  EN-HUMANO.md: 1 sección agregada")
else:
    print("  EN-HUMANO.md: ya estaba")

HITO = ("    { fecha: \"2026-07-22\", titulo: \"El motor vuelve a medir legislador por legislador, y el ORIGEN endereza el caso que estaba al reves\", "
        "texto: \"Dos avances. (1) Corregimos un atajo: el motor repetia el promedio de cada bloque tantas veces como bancas (257 diputados = 7 promedios fotocopiados), lo contrario del cimiento del proyecto. Ahora arma la lista real de legisladores del padron y le pone a cada uno SU tasa de desvio; el promedio de bloque queda solo como red para quien no tiene historial (la camada nueva). (2) Etiquetamos cada votacion con QUIEN impulsa la ley (Ejecutivo / oficialismo / oposicion) y bajo que gobierno se voto, sin gastar en clasificar PDFs. Al re-correr la reforma laboral del gobierno (1167) mirando solo lo impulsado por el gobierno, el signo se acomodo: La Libertad Avanza A FAVOR (0,33 a 0,88) y el kirchnerismo EN CONTRA (0,85 a 0,44), como en la realidad. Regla fina: un bloque es oficialista en un gobierno y opositor en el siguiente, asi que el modelo solo compara votaciones del mismo gobierno. Falta subir la cobertura del etiquetado (hoy 41%) y automatizar el origen del propio proyecto.\" },\n")

parche("tablero_datos.js",
    reemplazos=[
        ('nota: "v2 (2026-07-22): nowcast_auto acepta --tema/--origen y condiciona la dirección de bloque (consume tema_por_acta, temas 2011-2026); sin tema = v1. Re-corrida 1167@2026 con tema=TRAB NO mueve → HALLAZGO: el ORIGEN (quién impulsa) manda sobre el tema, falta etiquetar origen por acta.',
         'nota: "ROSTER NOMINAL (2026-07-22): nowcast_auto simula UNA FILA POR LEGISLADOR (padrón vigente + desvío individual; se eliminó _expandir_roster/demo). Origen por acta enchufado: con --origen GOBIERNO el 1167 se endereza (LLA 0,33→0,88; kirchnerismo 0,85→0,44). Falta backtest de la cadena y automatizar el origen del proyecto.'),
    ],
    inserciones=[('  hitos: [\n', HITO)])

print("\nListo. Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
