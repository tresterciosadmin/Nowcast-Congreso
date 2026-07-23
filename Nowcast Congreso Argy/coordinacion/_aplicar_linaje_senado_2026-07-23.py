# -*- coding: utf-8 -*-
"""Cierre del 2026-07-23 (2ª tanda): registra el ENRIQUECIMIENTO DE LINAJE DEL SENADO.
Los votos del Senado 2024+ (fuente argentinadatos) llegaban con bloque="SIN BLOQUE" →
linaje "OTRO / PROVINCIAL" para TODOS (la ingesta no resolvió el bloque), lo que dejaba
al nowcast del Senado sin historia por bloque (todo caía a neutro). Decisión de Valle:
no esperar a Franco, contribuir nosotros. Se recupera el linaje por NOMBRE contra el
padrón oficial (mandate-aware) + un override manual curado para los que dejaron banca.
Corre LOCAL:

    python coordinacion/_aplicar_linaje_senado_2026-07-23.py

Idempotente y defensivo. Toca ESTADO, TABLERO, EN-HUMANO, tablero_datos.js.
El código (variables/bloque/src/bloque.py) ya quedó aplicado y testeado (9 chequeos
nuevos + regresión completa 119) en la sesión.
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
'### [2026-07-23 · 2ª tanda] variables/bloque — enriquecimiento de LINAJE del Senado: se destraba el nowcast del Senado (contribución al entity_resolution, sin esperar a Franco)\n'
'- **Quién:** Valle (con Claude)\n'
'- **Qué:** el hallazgo de la tanda anterior (Senado no condiciona) se rastreó a la RAÍZ: los votos del Senado 2024+ (fuente argentinadatos) llegan con `bloque="SIN BLOQUE"` → linaje `OTRO / PROVINCIAL` para los 8.496 (la ingesta nunca resolvió el bloque), así que NINGÚN bloque real (kirchnerismo, LLA, UCR, PRO) tenía historia y el proyector caía a neutro (share 0,50). Decisión de Valle: **no esperar a Franco, contribuir nosotros.** Nace `_enriquecer_linaje_senado` en `variables/bloque`: recupera el linaje real por NOMBRE contra el padrón oficial (`datos/padron`, contrato ya consumido), **mandate-aware** (la fecha del voto cae en [desde,hasta] del senador → sin anacronismos), con fallback apellido+nombre; solo reasigna hacia un linaje ESPECÍFICO (respeta el OTRO/PROVINCIAL genuino) y solo toca el Senado. Enchufado en `cargar(enriquecer_senado=True)` (default on; `=False` reproduce el crudo).\n'
'- **Resultado:** Senado 2024+ pasa de **100% OTRO/PROVINCIAL** a repartirse en linajes reales (FdT-UxP 1.652, RADICALISMO 1.062, LLA 944, PRO 354, resto OTRO/PROVINCIAL). El nowcast del Senado **YA CONDICIONA**: en el hipotético "económico del PE" con `--origen GOBIERNO`, todos los bloques pasan de n_cond=0 a n_cond=16-18 (tienen historia diferenciada). Cobertura del match: 51/73 senadores por padrón; los **22 restantes** (dejaron banca en el recambio dic-2025) quedan en `datos/padron/data/senado_linaje_manual.csv` para que Valle los complete a mano (recupera ~2.596 votos, mayormente kirchneristas).\n'
'- **Cómo:** `python modelo\\ensemble\\src\\ensemble.py nowcast_auto HIP-ECON-PE 2026-07-23 senado SIMPLE 1.0 --origen GOBIERNO`. Tests: `test_bloque_linaje_senado.py` 9 (mandate-aware, no toca Diputados, respeta provincial genuino, override manual, no-op sin padrón) + regresión completa 119 verde.\n'
'- **Archivos:** `variables/bloque/src/bloque.py` (_norm_nombre, _cargar_padron_linaje_senado, _enriquecer_linaje_senado + cargar con flag), `variables/bloque/tests/test_bloque_linaje_senado.py` (nuevo), `datos/padron/data/senado_linaje_manual.csv` (nuevo, plantilla curada — 22 filas a completar), `coordinacion/{ESTADO,TABLERO,EN-HUMANO}`, `tablero_datos.js`.\n'
'- **PROPUESTA para Franco (entity_resolution / datos/canonica):** absorber esta resolución en `votos_resuelto` para que el linaje del Senado 2024+ salga bien EN LA FUENTE (hoy lo parchamos en la capa de consumo de variables/bloque). El override manual del Senado y la lógica mandate-aware son reutilizables.\n'
'- **Estado del módulo:** variables/bloque EN CURSO (linaje del Senado enriquecido; nowcast del Senado condiciona; falta que Valle complete los 22 manuales y subir la cobertura de origen del Senado para afinar la precisión).\n'
'- **Próximo paso:** (1) Valle completa `senado_linaje_manual.csv` (22 senadores); (2) backtest de la cadena completa con roster nominal + origen (Diputados y ahora Senado); (3) automatizar el --origen del propio proyecto; (4) multitemáticas.\n\n'
)

parche("coordinacion/ESTADO-DEL-PROYECTO.md",
    reemplazos=[
        ('| variables/bloque | EN CURSO (dirección condicionada por tema/origen con shrinkage; origen por lado GOBIERNO/OPOSICION + guard de mismo gobierno; 24 tests OK; enderezó el 1167) | Claude+Valle |',
         '| variables/bloque | EN CURSO (dirección condicionada por tema/origen; enriquecimiento de LINAJE del Senado desde el padrón mandate-aware → el nowcast del Senado ya condiciona; 33 tests OK; falta completar 22 senadores manuales) | Claude+Valle |'),
    ],
    inserciones=[('## Bitácora (más reciente arriba)\n', ESTADO)])

parche("coordinacion/TABLERO.md",
    reemplazos=[
        ('| variables/bloque | Claude+Valle | 2026-07-12 | v2 (2026-07-22): dirección de bloque CONDICIONADA por tema/origen (proyectar_postura con tema/origen/cond_por_acta + shrinkage); sin tema = v1 idéntico. Consume el puente tema_por_acta. 16 tests OK. Falta correr con temas reales + enchufar al ensemble |',
         '| variables/bloque | Claude+Valle | 2026-07-12 | dirección condicionada por tema/origen (shrinkage + guard de gobierno). NUEVO (2026-07-23): _enriquecer_linaje_senado recupera el linaje real de los votos del Senado 2024+ (llegaban SIN BLOQUE→OTRO/PROVINCIAL) contra el padrón mandate-aware → el nowcast del Senado YA CONDICIONA (n_cond 0→16-18). 33 tests. Contribución al entity_resolution (propuesta a Franco). Falta: Valle completa 22 senadores en senado_linaje_manual.csv |'),
    ])

ENH = (
'\n## Avance: destrabamos el Senado — ahora el modelo sí distingue cómo vota cada bloque\n'
'Ayer descubrimos que el Nowcast del Senado no servía porque el sistema no sabía a qué bloque pertenecía cada senador reciente (los metía a todos en una bolsa "otros/provinciales"). Hoy fuimos a la raíz: los datos de las votaciones del Senado 2024-2025 venían literalmente sin el bloque cargado. En vez de esperar a que se corrija en la base, lo resolvimos nosotros: cruzamos cada senador con el padrón oficial (que sí tiene su bloque), respetando las fechas de su mandato para no confundir épocas.\n\n'
'El resultado: las votaciones del Senado dejaron de estar todas en la bolsa genérica y se repartieron en los bloques reales (kirchnerismo, La Libertad Avanza, radicales, PRO). Con eso, el Nowcast del Senado ya distingue la postura de cada bloque —lo que ayer era imposible—. Quedan 22 senadores que ya dejaron su banca (en el recambio de diciembre) y que el padrón actual no tiene; los dejamos en una lista aparte para completar a mano y así recuperar el 100%. También le dejamos la propuesta a Franco para que esta corrección quede hecha directamente en la base de datos, que es su lugar natural.\n'
)
enh = RAIZ / "coordinacion" / "EN-HUMANO.md"
if enh.exists() and "ahora el modelo sí distingue cómo vota cada bloque" not in enh.read_text(encoding="utf-8"):
    with enh.open("a", encoding="utf-8") as f:
        f.write(ENH)
    print("  EN-HUMANO.md: 1 sección agregada")
else:
    print("  EN-HUMANO.md: ya estaba")

HITO = ("    { fecha: \"2026-07-23\", titulo: \"Destrabamos el Senado: el modelo ya distingue como vota cada bloque\", "
        "texto: \"El Nowcast del Senado no servia porque el sistema no sabia a que bloque pertenecia cada senador reciente (los metia a todos en 'otros/provinciales'). Fuimos a la raiz: los datos de las votaciones del Senado 2024-2025 venian sin el bloque cargado. En vez de esperar a que se arregle en la base, lo resolvimos nosotros cruzando cada senador con el padron oficial, respetando las fechas de su mandato. Ahora las votaciones se reparten en los bloques reales (kirchnerismo, La Libertad Avanza, radicales, PRO) y el Nowcast del Senado ya distingue la postura de cada bloque. Quedan 22 senadores que dejaron su banca en diciembre y que el padron actual no tiene: los pusimos en una lista para completar a mano. Le dejamos la propuesta a Franco para que la correccion quede en la base misma.\" },\n")

parche("tablero_datos.js",
    inserciones=[('  hitos: [\n', HITO)])

print("\nListo. Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
