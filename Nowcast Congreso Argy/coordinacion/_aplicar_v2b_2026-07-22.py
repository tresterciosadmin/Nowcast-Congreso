# -*- coding: utf-8 -*-
"""Cierre del 2026-07-22 (segunda tanda): registra el ENSEMBLE con v2 tema/origen
enchufado, la EXTENSIÓN del tagger (fuente canónica 2020-26 + checkpoint), la corrida
completa (1537 actas 2011-2026) y el HALLAZGO del origen. Corre LOCAL:

    python coordinacion/_aplicar_v2b_2026-07-22.py

Idempotente y defensivo. Toca ESTADO, TABLERO, EN-HUMANO, tablero_datos.js.
El código (ensemble.py, tema_por_acta.py) ya quedó aplicado y testeado en la sesión.
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
'### [2026-07-22 · cierre] ensemble (v2 tema/origen enchufado) + tema_por_acta (canónica 2020-26 + checkpoint) — cobertura de temas 2011-2026 y HALLAZGO: el ORIGEN manda sobre el tema\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** (1) **v2 ENCHUFADO al ensemble**: `nowcast_auto` acepta `tema`/`origen` y se los pasa a `proyectar_postura` (consume `tema_por_acta`); sin tema = idéntico al v1. (2) **`tema_por_acta` EXTENDIDO**: nueva fuente `canonica` (clasifica el título DESCRIPTIVO de la propia acta para 2020-2026 —argentinadatos lo trae con el tema— mientras las viejas 2011-2019 siguen por el puente CKAN porque su título es genérico) + **checkpoint cada 50** (corrida larga a prueba de cortes). Corrida completa con API key: **1537 actas tagueadas, cobertura 2011-2026** (AUX 283, JUST 204, POLINST 171, ECON 170, TRAB 116...). (3) Re-corrida del caso testigo 1167-D-2025 @2026 con `--tema TRAB`.\n'
'- **HALLAZGO (para la próxima sesión):** condicionar por TEMA solo NO alcanza y puede dar el signo POLÍTICO INVERTIDO. En 1167 (reforma laboral del gobierno) el v2 con tema=TRAB pone a **LLA (oficialismo) en NEGATIVO** y al **kirchnerismo en AFIRMATIVO** — al revés. Causa: las votaciones "TRAB" de 2024-2025 fueron mayormente proyectos OPOSITORES pro-trabajador (kirchnerismo SÍ, LLA NO); la misma materia tiene signo opuesto según QUIÉN la impulsa. **El eje que falta es el ORIGEN** (oficialismo/oposición), que el código YA soporta (`--origen`) pero requiere etiquetar el origen POR ACTA (cruce acta→expediente→autor→bloque, que ya produce `origen_lider.py`). Además "TRAB" mezcla proteger vs. desregular (ver backlog multitemáticas en PLAN).\n'
'- **Cómo:** `python variables\\proyecto\\src\\tema_por_acta.py --fuente canonica --desde-anio 2020`; `python modelo\\ensemble\\src\\ensemble.py nowcast_auto 1167-D-2025 2026-07-14 diputados SIMPLE 1.0 --tema TRAB`. Tests regresión: tema_por_acta 4 OK, bloque v1 7 + v2 5 OK.\n'
'- **Archivos:** `modelo/ensemble/src/ensemble.py` (nowcast_auto + CLI --tema/--origen), `variables/proyecto/src/tema_por_acta.py` (cargar_actas_canonica + checkpoint + --fuente/--desde-anio), `variables/proyecto/data/tema_por_acta.parquet` (1537), `coordinacion/PLAN-DE-TRABAJO.md` (backlog multitemáticas), {ESTADO,TABLERO,EN-HUMANO}, tablero_datos.js.\n'
'- **Estado del módulo:** modelo/ensemble EN CURSO (v2 tema/origen enchufado; falta origen por acta); variables/proyecto EN CURSO (temas 2011-2026 completos; falta origen por acta).\n'
'- **Próximo paso (próxima sesión):** etiquetar **ORIGEN por acta** (oficialismo/oposición vía `origen_lider`) para condicionar la dirección por quién impulsa el proyecto — es el lever que endereza el 1167. Después, multitemáticas.\n\n'
)

parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    reemplazos=[
        ('| modelo/ensemble | EN CURSO (v1 bicameral: nowcast_auto por cámara; caso testigo 1167-D-2025 Dip 137/123 · Sen 61/33, ambas ~100% = artefacto de dirección incondicional → motiva v2 por tema/origen) | Claude+Valle |',
         '| modelo/ensemble | EN CURSO (v2 tema/origen ENCHUFADO a nowcast_auto; consume tema_por_acta; sin tema = v1. 1167@2026 con tema=TRAB no mueve: HALLAZGO = el ORIGEN manda sobre el tema; falta etiquetar origen por acta) | Claude+Valle |'),
    ],
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('| modelo/ensemble | Claude+Valle | 2026-07-12 | P(aprob)=P(llega)×P(mayoría). nowcast_auto (escenario desde padrón+histórico). CASO TESTIGO bicameral 1167-D-2025: Dip 137/123 · Sen 61/33, ambas ~100% = artefacto de dirección incondicional. PRIORIDAD = v2 (dirección por tema/origen) |',
         '| modelo/ensemble | Claude+Valle | 2026-07-12 | P(aprob)=P(llega)×P(mayoría). v2 (2026-07-22): nowcast_auto acepta --tema/--origen y condiciona la dirección de bloque (consume tema_por_acta); sin tema = v1. Re-corrida 1167@2026 con tema=TRAB NO mueve → HALLAZGO: el ORIGEN (quién impulsa) manda sobre el tema; falta etiquetar origen por acta. Temas 2011-2026 completos (1537 actas) |'),
    ])

ENH = (
'\n## Avance: probamos condicionar por tema y apareció una lección — no alcanza con el tema, importa QUIÉN impulsa la ley\n'
'Terminamos de conectar todo: taguear el tema de cada votación (ahora 2011-2026, 1537 votaciones, sumando las recientes desde el propio título de la canónica) y hacer que el Nowcast condicione la postura de cada bloque por ese tema. Al re-correr la reforma laboral del gobierno (1167) condicionada a "laboral", saltó algo revelador: el modelo puso al oficialismo (La Libertad Avanza) votando EN CONTRA y al kirchnerismo A FAVOR — justo al revés de la realidad.\n\n'
'¿Por qué? Porque las votaciones "laborales" de 2024-2025 que el modelo miró fueron casi todas proyectos de la OPOSICIÓN a favor de los trabajadores (contra las reformas de Milei), donde el kirchnerismo votaba sí y el oficialismo no. El modelo aprendió bien ese patrón… pero se da vuelta cuando el proyecto es una desregulación del gobierno. La misma materia tiene dos signos opuestos según QUIÉN la impulsa. La conclusión: el tema es necesario pero no suficiente; el eje que falta es el ORIGEN del proyecto (oficialismo vs. oposición). El motor ya sabe recibir ese dato; falta etiquetar cada votación histórica con su origen. Queda anotado como el próximo paso. El mecanismo, mientras tanto, quedó armado y andando de punta a punta.\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "importa QUIÉN impulsa la ley" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(ENH)
    print("  EN-HUMANO.md: 1 sección agregada")
else:
    print("  EN-HUMANO.md: ya estaba")

HITO = ("    { fecha: \"2026-07-22\", titulo: \"Probamos que el motor lea el tema y apareció la lección clave: importa QUIEN impulsa la ley, no solo de que trata\", "
        "texto: \"Conectamos todo de punta a punta: se taguearon los temas de 1537 votaciones (2011-2026, sumando las recientes desde el titulo de la propia base) y el Nowcast ya condiciona la postura de cada bloque por el tema. Al re-correr la reforma laboral del gobierno (1167) condicionada a 'laboral', salto algo revelador: el modelo puso al oficialismo (La Libertad Avanza) EN CONTRA y al kirchnerismo A FAVOR, justo al reves. La razon: las votaciones laborales de 2024-2025 fueron casi todas proyectos de la OPOSICION a favor de los trabajadores (kirchnerismo si, oficialismo no); el modelo aprendio ese patron, que se da vuelta cuando la ley la empuja el gobierno. La leccion: el tema no alcanza, falta el ORIGEN (quien impulsa el proyecto). El motor ya sabe recibir ese dato; falta etiquetar cada votacion con su origen, y es el proximo paso. El mecanismo quedo armado y andando.\" },\n")

parche("tablero_datos.js",
    reemplazos=[
        ('nota: "v1 puesta en marcha: P(aprobación) = P(llega al recinto) × P(mayoría). Nuevo comando nowcast_auto',
         'nota: "v2 (2026-07-22): nowcast_auto acepta --tema/--origen y condiciona la dirección de bloque (consume tema_por_acta, temas 2011-2026); sin tema = v1. Re-corrida 1167@2026 con tema=TRAB NO mueve → HALLAZGO: el ORIGEN (quién impulsa) manda sobre el tema, falta etiquetar origen por acta. || v1 puesta en marcha: P(aprobación) = P(llega al recinto) × P(mayoría). Nuevo comando nowcast_auto'),
    ],
    inserciones=[('  hitos: [\n', HITO)])

print("\nListo. Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
