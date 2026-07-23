# -*- coding: utf-8 -*-
"""Cierre del 2026-07-23 (3ª tanda): registra que la POSTURA de bloque ahora EXCLUYE
las actas AUX (homenajes, trámite, declaraciones y en la práctica tratados/pliegos de
consenso) del cálculo, porque son consenso puro (todos afirmativo) y no informan la
posición política de ningún bloque. Responde a la observación de Valle (usar las
taxonomías para diferenciar los temas de consenso). Corre LOCAL:

    python coordinacion/_aplicar_excluir_aux_2026-07-23.py

Idempotente. Toca ESTADO, TABLERO, EN-HUMANO, tablero_datos.js. El código
(variables/bloque/src/bloque.py: proyectar_postura excluir_aux=True) ya quedó aplicado
y testeado (test_bloque_v2 7 chequeos + regresión completa) en la sesión.
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
            print(f"  [AVISO] ancla no encontrada en {archivo}: {viejo[:60]!r}")
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
'### [2026-07-23 · 3ª tanda] variables/bloque — la POSTURA excluye las actas AUX (consenso): homenajes/trámite/tratados no moldean la posición de bloque\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** observación de Valle: al condicionar el Senado por origen=GOBIERNO todos los bloques daban afirmativo porque el balde mezcla tratados, pliegos y homenajes (consenso) con leyes contenciosas — para eso están las taxonomías. Verificado: de 18 actas origen=GOBIERNO en la ventana del Senado, **11 eran AUX** (homenajes/trámite). Se agrega `excluir_aux=True` (default) a `proyectar_postura`: las actas con tema_area=AUX se sacan del cálculo de postura (condicional E incondicional), salvo que TODA la ventana sea AUX (no se vacía). Requiere el tema por acta (tema_por_acta); sin él, no filtra.\n'
'- **Hallazgo (confirma a Valle sobre la escasez):** excluir AUX NO da vuelta el Senado — el kirchnerismo pasa de 0,70 a 0,87, no a negativo. Las 7 actas sustantivas de origen=GOBIERNO que llegaron al recinto del Senado 2024-25 también fueron cosas que el kirchnerismo acompañó; las reformas contenciosas donde votó en contra NO están en los datos aún. La exclusión de AUX es correcta como método (quita el consenso que no informa), pero la señal que falta la traen **más actas + la designación multitemática de leyes** (backlog, acordado con Valle). En Diputados el efecto es limpio (hay votaciones peleadas etiquetadas).\n'
'- **Cómo:** `proyectar_postura(..., excluir_aux=True)`. Tests: test_bloque_v2 7 (suma exclusión de AUX no infla la postura + no vacía la ventana) + regresión completa verde.\n'
'- **Archivos:** `variables/bloque/src/bloque.py` (proyectar_postura + excluir_aux), `variables/bloque/tests/test_bloque_v2.py`, `coordinacion/{ESTADO,TABLERO,EN-HUMANO}`, `tablero_datos.js`.\n'
'- **Estado del módulo:** variables/bloque EN CURSO (postura sin ruido de consenso; el Senado espera más actas contenciosas + multitema para diferenciar de verdad).\n'
'- **Próximo paso:** (1) backtest de la cadena completa; (2) automatizar el --origen (y el --tema) del PROPIO proyecto; (3) más cobertura de actas + multitemáticas (separar consenso de contencioso dentro de un tema).\n\n'
)

parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('35 tests. Contribución al entity_resolution (propuesta a Franco). Override manual COMPLETO 22/22 (Valle, con canonicalización de etiquetas): OTRO/PROVINCIAL del Senado 2024+ cae de 53% a 26% |',
         '37 tests. Override manual del Senado COMPLETO 22/22 (OTRO/PROVINCIAL 53%→26%). NUEVO: la postura EXCLUYE actas AUX (homenajes/trámite/tratados = consenso) para no inflar el share afirmativo; se nota en Diputados, en el Senado espera más actas contenciosas + multitema |'),
    ])

ENH = (
'\n## Avance: le pedimos al modelo que ignore las votaciones de puro trámite al medir la postura de cada bloque\n'
'Valle notó algo fino: cuando el modelo miraba "cómo vota cada bloque frente a proyectos del gobierno", daba que todos votan a favor. La razón es que ahí se mezclaban homenajes, tratados internacionales y pliegos —cosas que se aprueban por consenso, casi sin discusión— con las leyes de verdad peleadas. Para distinguirlas usamos las taxonomías (la clasificación por tema de cada votación) y sacamos del cálculo de postura todo lo que es "de trámite/consenso". Así la postura de cada bloque queda medida solo sobre votaciones que realmente marcan posición.\n\n'
'Un aprendizaje honesto: en el Senado esto todavía no cambia el resultado, porque las pocas votaciones sustantivas del gobierno que llegaron al recinto en 2024-25 también fueron cosas que la oposición acompañó — las reformas realmente conflictivas aún no están en los datos. O sea: la mejora es correcta como método, pero la diferencia fina va a aparecer cuando entren más votaciones y cuando etiquetemos las leyes que tocan varios temas a la vez. En Diputados, que tiene más votaciones peleadas cargadas, el efecto ya se ve limpio.\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "que ignore las votaciones de puro trámite" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(ENH)
    print("  EN-HUMANO.md: 1 sección agregada")
else:
    print("  EN-HUMANO.md: ya estaba")

HITO = ("    { fecha: \"2026-07-23\", titulo: \"El modelo ya ignora las votaciones de puro tramite al medir la postura de cada bloque\", "
        "texto: \"Valle noto que al mirar como vota cada bloque frente a proyectos del gobierno, daba que todos votan a favor: se mezclaban homenajes, tratados y pliegos (consenso, sin discusion) con leyes peleadas. Usando las taxonomias (clasificacion por tema) sacamos del calculo de postura todo lo de tramite/consenso, para que la posicion de cada bloque se mida solo sobre votaciones que marcan posicion. Aprendizaje honesto: en el Senado todavia no cambia el resultado porque las pocas votaciones sustantivas del gobierno que llegaron al recinto en 2024-25 tambien las acompano la oposicion; las reformas conflictivas aun no estan en los datos. La mejora es correcta como metodo; la diferencia fina llegara con mas votaciones y con la etiqueta multitematica de las leyes. En Diputados ya se ve limpio.\" },\n")

parche("tablero_datos.js",
    inserciones=[('  hitos: [\n', HITO)])

print("\nListo. Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
