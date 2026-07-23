# -*- coding: utf-8 -*-
"""Cierre del 2026-07-23: registra (1) la SUBA DE COBERTURA de origen_por_acta con la
nueva vía "código embebido en el título" (Senado viejo, semilla decada_votada) —
global 40,7%→59,0%, Senado 20,8%→54,5%, tapa el hueco 2004-2014— y (2) el HALLAZGO
que destapa: el nowcast del Senado a fecha actual NO es un problema de origen sino de
ATRIBUCIÓN DE LINAJE de los votos recientes (2024-2026 caen TODOS en OTRO/PROVINCIAL).
Corre LOCAL:

    python coordinacion/_aplicar_cobertura_senado_2026-07-23.py

Idempotente y defensivo. Toca ESTADO, TABLERO, EN-HUMANO, tablero_datos.js.
El código (origen_por_acta.py) ya quedó aplicado y testeado (20 chequeos) en la sesión.
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
'### [2026-07-23] variables/proyecto (origen_por_acta) — vía "código embebido" sube la cobertura de origen y destapa el verdadero cuello del Senado\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** nueva 4ta vía en `origen_por_acta.py`: las actas viejas del Senado (semilla decada_votada) NO traen columna `expediente` pero SÍ el código EMBEBIDO en el título (formato `PE-608/03`, `S-1234/05`, `CD-45/11` = LETRA-NUMERO/AÑO con barra, distinto del estándar N-LETRA-AÑO → no colisiona). `_code_embebido` lo extrae y normaliza; PE/JGM → EJECUTIVO directo (aunque no cruce expedientes), S/CD que cruzan expedientes → autor→linaje. **Cobertura: global 40,7%→59,0% (3.144/5.333); Senado 20,8%→54,5%; el hueco 2004-2014 pasó de ~0% a ~50-90% por año.**\n'
'- **HALLAZGO (redirige la prioridad del Senado):** con el origen ya resuelto, el nowcast del Senado a fecha ACTUAL sigue sin condicionar (n_cond=0 en casi todos los bloques). El diagnóstico: en la ventana 2024-2026 hay 117 actas / 8.280 votos y 68 actas con origen etiquetado (19 GOBIERNO + 49 OPOSICION) — o sea el origen está BIEN—, pero **los 8.280 votos caen TODOS en el linaje `OTRO / PROVINCIAL`**: el mapeo de bloques no atribuye a los senadores recientes su linaje real (kirchnerismo, LLA, radicalismo, PRO). Por eso esos bloques figuran "sin historia" (share 0,50) y el condicionamiento no engancha. Es el `entity_resolution` de `datos/canonica` (ADR de Franco), NO de este módulo. El flag de memoria ("4 bancas del FIT en OTRO/PROVINCIAL") era en realidad MÁS grande: es TODO el Senado reciente.\n'
'- **Cómo:** `python variables\\proyecto\\src\\origen_por_acta.py`. Tests: origen_por_acta 20 (suma code_embebido PE/S + no-colisión con formato estándar); regresión completa verde (bloque 7+5+8, ensemble 29, agregador 26, origen_lider 24).\n'
'- **Archivos:** `variables/proyecto/src/origen_por_acta.py` (_RE_CODE_EMB + _code_embebido + vía titulo_codigo en el loop), `variables/proyecto/tests/test_origen_por_acta.py`, `variables/proyecto/data/origen_por_acta.parquet` (re-generado), `coordinacion/{ESTADO,TABLERO,EN-HUMANO}`, `tablero_datos.js`.\n'
'- **Estado del módulo:** variables/proyecto EN CURSO (origen 59% global / 54,5% Senado; el resto pre-2008 del Senado necesita una fuente de expedientes del Senado que HCDN no tiene).\n'
'- **Próximo paso:** (1) **PRIORIDAD Senado = atribución de linaje de votos recientes** (coordinar con Franco / entity_resolution; hoy 2024-26 = 100% OTRO/PROVINCIAL — bloquea el nowcast del Senado a fecha actual); (2) backtest de la cadena completa con roster nominal + origen (Diputados ya condiciona); (3) automatizar el --origen del propio proyecto; (4) multitemáticas.\n\n'
)

parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    reemplazos=[
        ('| variables/proyecto | EN CURSO (tema_por_acta 1537 actas; NUEVO origen_por_acta: quién impulsa + gobierno por acta, 40,7% etiquetado, determinístico sin API key; falta subir cobertura) | Valle |',
         '| variables/proyecto | EN CURSO (tema_por_acta 1537; origen_por_acta 59% global / 54,5% Senado vía código embebido; el nowcast del Senado ahora se traba en la atribución de linaje de votos recientes = entity_resolution/Franco) | Valle |'),
    ],
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + ICG + origen/líder + tema_por_acta (1537 actas). NUEVO (2026-07-22): origen_por_acta.py = quién impulsa (EJECUTIVO/OFICIALISMO/OPOSICION) + gobierno de turno POR ACTA, determinístico sin API key (3 vías: código/O.D./título); 40,7% etiquetado + 14 tests. Falta subir cobertura |',
         '| variables/proyecto | Claude+Valle | 2026-06-30 | agente de taxonomías + ICG + origen/líder + tema_por_acta (1537). origen_por_acta.py = quién impulsa + gobierno POR ACTA (4 vías: código/embebido/O.D./título); 20 tests. Cobertura (2026-07-23): 59% global / 54,5% Senado (vía código embebido tapa el hueco 2004-2014). HALLAZGO: el nowcast del Senado a hoy se traba en la atribución de linaje de votos recientes (todo cae en OTRO/PROVINCIAL) = entity_resolution/Franco, no origen |'),
    ])

ENH = (
'\n## Avance: mejoramos mucho el etiquetado del Senado y, al hacerlo, descubrimos dónde está el verdadero cuello\n'
'Ayer el Nowcast del Senado daba un número que no había que creer. Hoy atacamos una de las causas: la mitad de las votaciones del Senado (sobre todo las viejas, 2004-2014) no tenían identificado quién impulsaba la ley. Encontramos que ese dato SÍ estaba, escondido dentro del título de cada votación (un código tipo "PE-608/03"), y lo extrajimos. Con eso, el etiquetado del Senado pasó del 21% al 55% y se tapó el agujero histórico; el total del sistema quedó en 59%.\n\n'
'Pero al resolver eso quedó a la vista el problema de fondo del Senado, que era otro: las votaciones recientes (2024-2025) SÍ tienen identificado quién impulsa, pero el sistema no está reconociendo a qué bloque pertenece cada senador actual —los mete a todos en una bolsa genérica ("otros/provinciales")—, así que cuando el modelo quiere ver "cómo vota el kirchnerismo" o "cómo vota La Libertad Avanza" en el Senado, no encuentra historia y se queda neutro. Ese reconocimiento de bloques del Senado reciente es una pieza de la base de datos que maneja Franco; queda anotado como la prioridad para destrabar el Senado. En Diputados esto ya funciona y el modelo distingue bien la política real.\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "descubrimos dónde está el verdadero cuello" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(ENH)
    print("  EN-HUMANO.md: 1 sección agregada")
else:
    print("  EN-HUMANO.md: ya estaba")

HITO = ("    { fecha: \"2026-07-23\", titulo: \"Subimos el etiquetado del Senado del 21% al 55% y, al hacerlo, encontramos el verdadero cuello\", "
        "texto: \"La mitad de las votaciones del Senado (sobre todo 2004-2014) no tenian identificado quien impulsaba la ley. El dato estaba escondido en el titulo de cada votacion (un codigo tipo 'PE-608/03'); lo extrajimos y el etiquetado del Senado paso del 21% al 55% (59% en todo el sistema), tapando el agujero historico. Pero eso destapo el problema de fondo del Senado: las votaciones recientes (2024-2025) SI dicen quien impulsa, pero el sistema no reconoce a que bloque pertenece cada senador actual (los mete a todos en 'otros/provinciales'), asi que el modelo no encuentra historia por bloque y se queda neutro. Ese reconocimiento de bloques del Senado reciente es de la base que maneja Franco y queda como la proxima prioridad. En Diputados ya funciona.\" },\n")

parche("tablero_datos.js",
    inserciones=[('  hitos: [\n', HITO)])

print("\nListo. Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
