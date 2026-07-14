#!/usr/bin/env python3
"""Aplica las bitácoras de variables/bloque (v1) sobre los archivos COMPLETOS.

Correr en LOCAL desde la raíz del repo (el mount del sandbox sirve copias
truncadas de estos archivos; por eso el Claude del sandbox no los tocó).
Es IDEMPOTENTE: si ya está aplicado, no duplica. Verifica y avisa.

    python variables/bloque/_aplicar_bitacoras.py

Toca: coordinacion/TABLERO.md, coordinacion/ESTADO-DEL-PROYECTO.md,
      coordinacion/EN-HUMANO.md, tablero_datos.js
"""
from pathlib import Path

FECHA = "2026-07-12"


def patch(path, edits):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    orig = s
    for old, new, marker in edits:
        if marker in s:
            print(f"  = ya aplicado en {path}: {marker[:48]}...")
            continue
        if old not in s:
            print(f"  ! NO encontré el ancla en {path}: {old[:60]!r}")
            continue
        s = s.replace(old, new, 1)
        print(f"  + {path}: {marker[:48]}...")
    if s != orig:
        p.write_text(s, encoding="utf-8")


# --- 1) TABLERO.md ---------------------------------------------------------
patch("coordinacion/TABLERO.md", [
    ("- [ ] **variables/bloque** — cohesión/posición/fracturas por bloque en el tiempo.",
     "- [x] ~~**variables/bloque**~~ → reclamado 2026-07-12 por Valle (ver \"En curso\"). Postura/cohesión proyectada para el escenario del ensemble.",
     "reclamado 2026-07-12 por Valle (ver \"En curso\"). Postura/cohesión"),
    ("\n## Hecho",
     "| variables/bloque | Claude+Valle | 2026-07-12 | serie por bloque (postura/cohesión/fracturas) + proyector point-in-time del escenario {bloque,bancas,linea,desvio} para el ensemble; walk-forward, sin leakage; 7 tests OK |\n\n## Hecho",
     "| variables/bloque | Claude+Valle | 2026-07-12 |"),
])

# --- 2) ESTADO-DEL-PROYECTO.md --------------------------------------------
entrada = """### [2026-07-12] variables/bloque — v1: serie temporal por bloque + proyector point-in-time de la postura
- **Quién:** Claude (con Valle)
- **Qué:** reclamado el módulo (el 'próximo paso' del ensemble lo pedía explícitamente) y construida la pieza que hoy falta para nowcastear un proyecto NO votado sin poner la postura a mano. `variables/bloque/src/bloque.py` produce (1) **serie temporal por bloque** `outputs/serie_bloque.parquet` — una fila por (período parlamentario, cámara, `bloque_linaje`) con **tamaño** (bancas medias), **postura** (`share_afirmativo` = fracción de actas donde la dirección del bloque fue AFIRMATIVO entre los que EMITIERON), **cohesión** (índice de Rice = |afirm−neg|/emitidos), **desvío interno** (fracción minoritaria) y **tasa de fractura** (actas con Rice<0,5); y (2) un **proyector** `proyectar_postura(fecha, cámara)` que, con SOLO las actas anteriores a la fecha en una ventana móvil (walk-forward, sin leakage), devuelve el escenario `[{bloque, bancas, linea, desvio}]` en el formato EXACTO que consume `modelo/ensemble` (misma semántica de conductas que el agregador, para que encaje sin traducir).
- **Cómo:** dirección del bloque por acta = mayoría AFIRMATIVO/NEGATIVO entre emitidos (ABSTENCION/AUSENTE → NO_ACOMPANA, no emiten); cohesión de Rice y desvío como fracción minoritaria; agregación por período parlamentario (recambio 10-dic: diciembre cuenta para el año siguiente); bancas = legisladores distintos vistos en la ventana. 4 directivas (errores específicos, parsing defensivo del contrato de la canónica, logging; sin red → sin backoff). Tests offline con fixture sintética (bloque oficialista disciplinado vs opositor con fracturas): **7 chequeos OK** (dirección, Rice, no-emiten los ausentes, serie por período, formato del escenario, **walk-forward sin leakage**, errores claros). Prueba de humo contra la canónica real (831.677 votos 2001-2025): serie de 272 filas; el desvío discrimina (OTRO/PROVINCIAL ~0,28 y fractura ~0,64 vs LA LIBERTAD AVANZA ~0,015). *Protocolo:* código y salida vía bash; tests desde /tmp; el mount sirvió TABLERO/ESTADO truncados, por eso estas bitácoras se aplican en local con `variables/bloque/_aplicar_bitacoras.py`.
- **Archivos:** `variables/bloque/{src/bloque.py, src/requirements.txt, tests/test_bloque.py, README.md, _aplicar_bitacoras.py}`, `coordinacion/{TABLERO.md, ESTADO-DEL-PROYECTO.md, EN-HUMANO.md}`, `tablero_datos.js`.
- **Estado del módulo:** variables/bloque EN CURSO (v1: cohesión/desvío/tamaño proyectados OK — el hueco del ensemble; falta la DIRECCIÓN condicionada por tema/origen = v2).
- **Próximo paso:** Valle corre `python variables\\bloque\\src\\bloque.py serie` y un `proyectar <fecha> <camara>` para verificar; enchufar el escenario proyectado al ensemble (reemplaza la postura a mano). **v2 (bloqueado por taxonomías):** proyectar la DIRECCIÓN condicionada por tema (batch del agente) y por origen del proyecto (`variables/proyecto/features_proyecto.parquet`) — hoy la dirección incondicional da AFIRMATIVO para casi todos porque lo que llega al recinto se aprueba.

"""
patch("coordinacion/ESTADO-DEL-PROYECTO.md", [
    ("## Bitácora (más reciente arriba)\n",
     "## Bitácora (más reciente arriba)\n" + entrada,
     "### [2026-07-12] variables/bloque — v1: serie temporal"),
    ("| variables/bloque | PENDIENTE | — |",
     "| variables/bloque | EN CURSO (v1: serie + proyector point-in-time; cohesión/desvío/tamaño OK, dirección por tema = v2) | Valle |",
     "| variables/bloque | EN CURSO (v1: serie + proyector"),
])

# --- 3) EN-HUMANO.md -------------------------------------------------------
parrafo = """

## Avance: cada bloque, su temperamento en el tiempo (y su postura para el Nowcast)
El Nowcast, para estimar una votación, necesita saber qué va a hacer cada bloque: ¿acompaña o rechaza?, y ¿vota en bloque o se rompe? Hasta hoy esa postura se ponía **a mano** en el simulador. Ahora la sacamos de la historia: para cada bloque y cada época medimos su **tamaño**, su **cohesión** (¿cuán unido vota? — con el índice de Rice, donde 1 es unánime), cuánto se **fractura**, y su **tendencia** de voto. Y un proyector arma, para una fecha dada, la ficha de cada bloque usando **solo el pasado** (nunca mira el resultado que queremos predecir). Lo que ya sale muy bien —y era justo lo que el simulador necesitaba— es la **cohesión**: el sistema distingue solo a un bloque disciplinado (La Libertad Avanza vota casi siempre igual) de una bolsa dispersa (los provinciales, que se parten en dos de cada tres votaciones). Lo que queda para la próxima: adivinar **la dirección** (a favor / en contra) depende del TEMA del proyecto y de quién lo empuja —porque casi todo lo que llega al recinto se aprueba, mirar la tendencia general no alcanza—, y eso se destraba cuando estén clasificados los temas (el agente que espera la API key).
"""
patch("coordinacion/EN-HUMANO.md", [
    ("__EOF_APPEND__", "", "temperamento en el tiempo"),  # marcador de idempotencia
])
# append manual idempotente
enh = Path("coordinacion/EN-HUMANO.md")
t = enh.read_text(encoding="utf-8")
if "temperamento en el tiempo" not in t:
    enh.write_text(t.rstrip() + "\n" + parrafo, encoding="utf-8")
    print("  + EN-HUMANO.md: párrafo agregado")
else:
    print("  = EN-HUMANO.md ya tenía el párrafo")

# --- 4) tablero_datos.js ---------------------------------------------------
hito = ('    { fecha: "2026-07-12", titulo: "Cada bloque, con su temperamento medido en el tiempo", '
        'texto: "Para estimar una votación el sistema necesita la postura de cada bloque; hasta hoy iba a mano. '
        'Ahora se mide de la historia: tamaño, cohesión (¿vota unido? — índice de Rice), fracturas y tendencia por bloque y época, '
        'y un proyector arma la ficha de cada bloque para una fecha usando solo el pasado (sin trampa). '
        'Ya distingue disciplinados (LLA) de dispersos (los provinciales, que se parten 2 de cada 3 votaciones). '
        'Falta adivinar la dirección a favor/en contra: depende del tema del proyecto (espera la clasificación por API key)." },\n')
patch("tablero_datos.js", [
    ('{ modulo: "variables/bloque", estado: "PENDIENTE", owner: "libre", nota: "Cohesión/posición/fracturas por bloque en el tiempo." },',
     '{ modulo: "variables/bloque", estado: "EN CURSO", owner: "Valle", nota: "v1: serie temporal (postura/cohesión/fracturas) + proyector point-in-time del escenario para el ensemble; cohesión OK, dirección por tema = v2." },',
     '{ modulo: "variables/bloque", estado: "EN CURSO"'),
    ("  hitos: [\n",
     "  hitos: [\n" + hito,
     "Cada bloque, con su temperamento medido en el tiempo"),
    ('  actualizado_por: "Claude (con Valle) — segmentación por tipo de proyecto: origen (ejecutivo/oficialismo/oposición) + liderazgo, enchufados al embudo",',
     '  actualizado_por: "Claude (con Valle) — variables/bloque v1: serie temporal por bloque + proyector point-in-time de la postura para el ensemble",',
     "variables/bloque v1: serie temporal por bloque"),
])

print("\nListo. Revisá los diffs (git diff) antes de commitear.")
