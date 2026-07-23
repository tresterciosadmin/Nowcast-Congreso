# -*- coding: utf-8 -*-
"""Aplica TODAS las bitácoras del avance v2 (2026-07-22) SOBRE LOS ARCHIVOS COMPLETOS.
Correr LOCAL (PC de Valle), donde el mount no trunca:

    git checkout -- tablero_datos.js        # restaura la cola (capex) que el sandbox truncó
    python coordinacion/_aplicar_v2_2026-07-22.py
    node --check tablero_datos.js           # sin salida = OK

Idempotente y defensivo. Toca: tablero_datos.js, ESTADO-DEL-PROYECTO.md, TABLERO.md, EN-HUMANO.md.
El CÓDIGO (bloque.py v2, tema_por_acta.py, tests) YA quedó aplicado y testeado en la sesión (16 tests OK).
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
            print(f"  [AVISO] ancla no encontrada en {archivo}: {viejo[:70]!r}")
    for ancla, bloque in inserciones:
        if bloque.strip() in s:
            continue
        if ancla in s:
            s = s.replace(ancla, ancla + bloque, 1); hechos += 1
        else:
            print(f"  [AVISO] inserción no encontrada en {archivo}: {ancla[:50]!r}")
    p.write_text(s, encoding="utf-8")
    print(f"  {archivo}: {hechos} cambios ({n} -> {len(s)} bytes)")


parche("tablero_datos.js",
    reemplazos=[
        ('actualizado: "2026-07-14",', 'actualizado: "2026-07-22",'),
        ('actualizado_por: "Valle (con Claude) — Nowcast bicameral de 1167-D-2025 (caso testigo): Dip 137/123 · Sen 61/33, ambas ~100%. Confirma que la dirección incondicional del v1 infla el resultado → prioridad = v2 (postura por tema/origen). Antes: nace datos/padron y se enchufa al proyector (roster 375→257)",',
         'actualizado_por: "Valle (con Claude) — v2 de posición de bloque: la dirección de cada bloque ahora se CONDICIONA por TEMA/ORIGEN del proyecto (antes incondicional → causa del 100% irreal del caso 1167). Puente tema_por_acta: clasifica por TEXTO los ~890 títulos de actas votadas (barato, sin PDF) para alimentar el v2. 16 tests OK. Falta la corrida del batch con API key (local).",'),
        ('desc: "Tamaño, cohesión (Rice), desvío interno y fracturas por bloque en el tiempo + proyector point-in-time. CORRIDO y ENCHUFADO: las bancas salen del padrón OFICIAL (composición real a la fecha, 257/72) y el desvío/postura del histórico; arreglado el roster inflado (375→257). Falta la dirección por tema/origen (v2).", estado: "EN CURSO" }',
         'desc: "Tamaño, cohesión (Rice), desvío interno y fracturas por bloque en el tiempo + proyector point-in-time. CORRIDO y ENCHUFADO: bancas del padrón OFICIAL (257/72) y desvío/postura del histórico; roster 375→257. v2 DISPONIBLE (jul-2026): proyectar_postura condiciona la DIRECCIÓN por tema/origen con encogimiento (shrinkage) y consume el puente tema_por_acta; cae a incondicional (v1) si no hay tema. Prueba real 2019 (gob. Macri): la oposición kirchnerista pasa de 0,74 afirmativo a 0,47 NEGATIVO condicionada a ECON. Falta correr el batch de temas (API key).", estado: "EN CURSO" }'),
        ('ORIGEN+LÍDER por proyecto construidos (origen_lider.py → features_proyecto.parquet): origen ejecutivo/oficialismo/oposición (cruce autor→bloque→fecha) y líder (jefe de bloque curado + pdte comisión + alto productor sin leakage). 16 tests OK." }',
         'ORIGEN+LÍDER por proyecto construidos (origen_lider.py → features_proyecto.parquet): origen ejecutivo/oficialismo/oposición y líder (jefe de bloque + pdte comisión + alto productor sin leakage). 16 tests OK. NUEVO (jul-2026): tema_por_acta.py — puente que clasifica por TEXTO los ~890 títulos de actas VOTADAS (acta_expediente) → contrato acta_id→tema que alimenta el v2 de bloque; consume clasificar_texto del agente, idempotente y resiliente, 4 tests OK. Falta la corrida con API key (local)." }'),
    ],
    inserciones=[
        ('  hitos: [\n',
         '    { fecha: "2026-07-22", titulo: "El motor ya LEE el tema del proyecto: la postura de cada bloque deja de ser \\"vota su promedio\\"", texto: "Era el agujero que dejó el caso testigo 1167 (todo daba ~100% porque cada bloque votaba su promedio sin importar de qué trataba la ley). Se resolvió en dos piezas. Primero, un PUENTE barato de temas: en vez de leer 112.000 PDFs, se clasifican por su TÍTULO las ~890 votaciones que realmente ocurrieron (lo único que el motor necesita), con el clasificador de IA que ya estaba listo — sin PDFs, con Haiku, centavos. Segundo, el proyector de bloques ahora CONDICIONA la dirección al tema y origen del proyecto: mira sólo las votaciones pasadas del mismo tema y las mezcla con el promedio general por encogimiento para no dar vuelta una postura con dos o tres casos sueltos. En datos reales de 2019 (gobierno Macri): la oposición kirchnerista, que en el promedio ciego figura 0,74 a favor, condicionada a temas ECONÓMICOS baja a 0,47 = EN CONTRA. Sin tema, idéntico al anterior: no rompe nada. 16 chequeos en verde. Falta encenderlo a full: correr la clasificación de los 890 títulos con la API key (liviano; PC de Valle)." },\n'),
    ])

ESTADO_ENTRY = (
'### [2026-07-22] variables/bloque (v2) + variables/proyecto (tema_por_acta) — la dirección de bloque deja de ser incondicional: se condiciona por TEMA/ORIGEN\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** se resolvió el límite que expuso el caso testigo 1167 (dirección INCONDICIONAL → 100% irreal). Dos piezas: (1) **`variables/proyecto/src/tema_por_acta.py`** — puente barato: clasifica por TEXTO los **~890 títulos de actas VOTADAS** (de `datos/expedientes/acta_expediente.parquet`, que traen título DESCRIPTIVO) usando la interfaz pública del agente (`clasificar_texto`); produce `data/tema_por_acta.parquet` (acta_id, tema_id, tema_area, confianza, todas_ids). No hace falta el batch de 112k PDFs para el v2: sólo importan las actas que se votaron. (2) **v2 de `variables/bloque` (`proyectar_postura`)**: parámetros `tema`, `origen`, `cond_por_acta`; calcula la dirección de cada bloque sobre las actas de la ventana con el mismo tema/origen y la mezcla con la incondicional por **encogimiento** (pseudo-conteo `k_shrink=5`). **Sin tema/origen → IDÉNTICO al v1** (verificado `share_afirm == share_incond`; ensemble intacto).\n'
'- **Cómo:** join canónica ∩ puente = **890/892**. Smoke-test real 2019 (Macri): **FdT-UxP** 0,74 afirmativo → ECON 0,47 = **NEGATIVO**; **PRO/Radicalismo** ECON 0,70 / JUST 0,92. Tests offline (LLM inyectado): `test_bloque_v2.py` (5) + `test_tema_por_acta.py` (4) + regresión `test_bloque.py` (7, con `padron_path="__no__"` para determinismo). **16 tests OK.** CLI: `python variables\\bloque\\src\\bloque.py proyectar <fecha> <camara> --tema ECON [--origen OPOSICION]`.\n'
'- **Archivos:** `variables/proyecto/src/tema_por_acta.py` (nuevo), `variables/proyecto/tests/test_tema_por_acta.py` (nuevo), `variables/bloque/src/bloque.py` (proyectar_postura v2 + cargar_tema_por_acta + _cond_map + CLI), `variables/bloque/tests/{test_bloque_v2.py (nuevo), test_bloque.py}`, READMEs, `coordinacion/{ESTADO,TABLERO,EN-HUMANO}`, `tablero_datos.js`.\n'
'- **Estado del módulo:** variables/bloque EN CURSO (v2 disponible y testeado; falta correrlo con temas reales); variables/proyecto EN CURSO (puente listo; falta corrida con API key).\n'
'- **Próximo paso:** (1) correr LOCAL `python variables\\proyecto\\src\\tema_por_acta.py` con API key (890 títulos, Haiku, barato) → llena `tema_por_acta.parquet`; (2) enchufar `tema/origen/cond_por_acta` en `modelo/ensemble` (nowcast_auto) y re-correr 1167-D-2025 para ver el 100% caer a la pelea real; (3) opcional: extender el puente vía `proyecto_taxonomias` cuando corra el batch masivo de PDFs.\n'
'- **NOTA DE INCIDENTE (sandbox):** al guardar `tablero_datos.js` desde el sandbox el mount truncó ~690 bytes de la COLA (sección `capex`, preexistente). Recuperación: `git checkout -- tablero_datos.js` + este script. El código NO se afectó (los 16 tests corren completos).\n\n'
)
parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    reemplazos=[
        ('| variables/bloque | EN CURSO (v1 CORRIDO: serie 272 filas + proyector ENCHUFADO al padrón oficial → bancas reales a fecha 257/72; roster 375→257; falta v2 dirección por tema/origen) | Claude+Valle |',
         '| variables/bloque | EN CURSO (v2: dirección de bloque CONDICIONADA por tema/origen con shrinkage; sin tema = v1 idéntico; 16 tests OK; falta correrlo con temas reales) | Claude+Valle |'),
        ('| variables/proyecto | EN CURSO (vocabulario validado; ICG vivo; origen+líder por proyecto listos; falta batch del agente/tema) | Valle |',
         '| variables/proyecto | EN CURSO (vocabulario validado; ICG vivo; origen+líder listos; NUEVO puente tema_por_acta ~890 actas votadas→tema; falta correr batch/tagger con API key) | Valle |'),
    ],
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO_ENTRY)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('| variables/bloque | Claude+Valle | 2026-07-12 | v1: serie temporal por bloque (tamaño/cohesión-Rice/desvío/fractura) + proyector point-in-time de postura (escenario del ensemble). SERIE CORRIDA (272) + proyector enchufado al padrón (bancas reales a fecha). Falta v2 dirección por tema/origen. Registrado 2026-07-14 |',
         '| variables/bloque | Claude+Valle | 2026-07-12 | v2 (2026-07-22): dirección de bloque CONDICIONADA por tema/origen (proyectar_postura con tema/origen/cond_por_acta + shrinkage); sin tema = v1 idéntico. Consume el puente tema_por_acta. 16 tests OK. Falta correr con temas reales + enchufar al ensemble |'),
        ('| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías listo + vocabulario validado a mano (88 actas, RESULTADOS-muestra-manual.md) + ICG Di Tella corrido (icg_mensual.csv, 296 meses) |',
         '| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + vocabulario validado (88 actas) + ICG (296 meses) + origen/líder. NUEVO (2026-07-22): tema_por_acta.py = puente que clasifica por TEXTO ~890 títulos de actas votadas → acta_id→tema para el v2 de bloque (4 tests). Falta corrida con API key |'),
    ])

EN_HUMANO = (
'\n## Avance: el motor ya LEE de qué trata la ley (y la postura de cada bloque deja de ser "vota su promedio")\n'
'El caso testigo de la reforma laboral (1167) había dejado el problema a la vista: el sistema daba ~100% de aprobación porque cada bloque "votaba su promedio reciente" sin mirar el TEMA del proyecto — y como casi todo lo que llega al recinto se aprueba, casi todos quedaban a favor. Lo arreglamos con dos piezas que encajan.\n\n'
'Primero, un atajo barato para los temas: en vez de leer los 112.000 PDF de todos los proyectos, clasificamos por su TÍTULO las ~890 votaciones que REALMENTE ocurrieron (lo único que el motor necesita para condicionar), usando el clasificador de IA que ya estaba listo. Sin descargar PDFs, con el modelo más barato, cuesta centavos.\n\n'
'Segundo, el "proyector de bloques" ahora condiciona la postura al tema y al origen del proyecto: para decidir cómo va a votar un bloque una ley económica, mira sólo sus votaciones ECONÓMICAS pasadas, y las mezcla con su promedio general con cuidado (si de ese tema hay sólo dos o tres antecedentes, no le cree del todo). Se ve clarísimo con datos reales de 2019, con Macri en el gobierno: la oposición kirchnerista, que en el promedio ciego figura 74% a favor, condicionada a temas económicos cae a 47% = EN CONTRA — lo que de verdad hacía. Y si no se le pasa ningún tema, el resultado es idéntico al de antes, así que no rompe nada. Falta un paso para encenderlo del todo: correr la clasificación de esos 890 títulos con la clave de la API (liviano, va en la compu de Valle).\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "el motor ya LEE de qué trata la ley" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(EN_HUMANO)
    print("  EN-HUMANO.md: 1 sección agregada al final")
else:
    print("  EN-HUMANO.md: ya estaba")

print("\nListo. Verificá: node --check tablero_datos.js")
