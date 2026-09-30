"""Tests offline de datos/expedientes/src/capitulos_nombre.py — sin red, sin PDF.

Sólo ejercita `extraer_capitulos` (regex sobre texto ya extraído): la parte de
E/S (bajar y leer PDFs reales) se verificó a mano sobre el corpus escalado de
B2 (ver ADR-0023, addendum 2026-09-16) y no tiene sentido de mockear acá.

    python datos/expedientes/tests/test_capitulos_nombre.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capitulos_nombre import extraer_capitulos  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("formato con guión largo en la misma línea (Ley Bases, 141-1.pdf real)")
texto = (
    "Capítulo I — Disposiciones generales\n"
    "Art. 1° — Objeto.\n\n"
    "Capítulo II — Declaración de emergencia pública y bases de delegaciones "
    "legislativas\n"
    "Art. 3° — Declaración. Plazo.\n"
)
caps = extraer_capitulos(texto)
por_num = {c["capitulo_num"]: c["nombre_capitulo"] for c in caps}
check(por_num.get("I") == "Disposiciones generales", f"capítulo I: {por_num.get('I')!r}")
check(por_num.get("II") == "Declaración de emergencia pública y bases de delegaciones legislativas",
      f"capítulo II: {por_num.get('II')!r}")

print("\nformato con nombre en la línea siguiente, sin separador")
texto2 = "CAPÍTULO III\nDISPOSICIONES TRANSITORIAS\nArt. 10.- ...\n"
caps2 = extraer_capitulos(texto2)
check(len(caps2) == 1 and caps2[0]["capitulo_num"] == "III", "reconoce el numeral")
check(caps2[0]["nombre_capitulo"] == "DISPOSICIONES TRANSITORIAS", "reconoce el nombre en la línea siguiente")

print("\nreferencia de cuerpo en minúscula NO se confunde con un encabezado")
texto3 = "Lo dispuesto conforme al capítulo II de esta ley no se modifica.\n"
check(extraer_capitulos(texto3) == [], "minúscula: no matchea (evita falsos positivos)")

print("\nmismo capítulo mencionado dos veces (encabezado + índice/sumario): se deduplica")
texto4 = (
    "CAPÍTULO IV\nDEL RÉGIMEN\n\n"           # sumario, nombre corto
    "...\n\n"
    "Capítulo IV — Del régimen de contrataciones públicas y su fiscalización\n"  # encabezado real, más largo
    "Art. 40.- ...\n"
)
caps4 = extraer_capitulos(texto4)
check(len(caps4) == 1, f"un solo capítulo IV, no dos: {caps4}")
check(caps4[0]["nombre_capitulo"] == "Del régimen de contrataciones públicas y su fiscalización",
      f"se queda con el nombre más largo (más informativo): {caps4[0]['nombre_capitulo']!r}")

print("\ncapítulo SIN nombre propio: no se inventa uno con el texto del artículo que sigue")
texto_sin_nombre = "CAPÍTULO V\nARTÍCULO 91.- Las disposiciones de este Título entrarán en vigencia...\n"
check(extraer_capitulos(texto_sin_nombre) == [],
      f"un capítulo sin título no debe aparecer con el articulado como nombre falso: {extraer_capitulos(texto_sin_nombre)}")

print("\nencabezado de página repetido no se confunde con el nombre del capítulo")
texto_encabezado = "CAPÍTULO II\nCÁMARA DE DIPUTADOS DE LA NACIÓN O.D. Nº 7\nArt. 20.- ...\n"
check(extraer_capitulos(texto_encabezado) == [],
      f"un encabezado de página no es un nombre de capítulo: {extraer_capitulos(texto_encabezado)}")

print("\ntexto sin ningún capítulo (ley de un solo bloque, sin títulos formales)")
check(extraer_capitulos("Artículo 1°.- Apruébase...\nArtículo 2°.- Comuníquese.\n") == [],
      "sin capítulos: lista vacía, no un error")

print("\nnombres se normalizan (espacios de más colapsan, se sacan separadores colgados)")
texto5 = "CAPÍTULO V —   Del   procedimiento.-  \nArt. 50.- ...\n"
caps5 = extraer_capitulos(texto5)
check(caps5[0]["nombre_capitulo"] == "Del   procedimiento" or caps5[0]["nombre_capitulo"] == "Del procedimiento",
      f"nombre razonable pese a espacios/puntuación de más: {caps5[0]['nombre_capitulo']!r}")

print("\nel numeral de capítulo se REINICIA por título: 'Capítulo I' de dos títulos "
     "distintos NO se funde en uno solo (bug real encontrado sobre Ley Bases, 16-09)")
texto6 = (
    "TÍTULO I\n"
    "Capítulo I — Disposiciones generales\n"
    "Art. 1°.- Objeto.\n\n"
    "TÍTULO II\n"
    "Capítulo I — Del régimen laboral\n"
    "Art. 5°.- Ámbito de aplicación.\n"
)
caps6 = extraer_capitulos(texto6)
check(len(caps6) == 2, f"dos capítulos DISTINTOS, no uno fusionado: {caps6}")
por_titulo = {(c["titulo_num"], c["capitulo_num"]): c["nombre_capitulo"] for c in caps6}
check(por_titulo.get(("I", "I")) == "Disposiciones generales",
      f"Título I, Capítulo I: {por_titulo.get(('I', 'I'))!r}")
check(por_titulo.get(("II", "I")) == "Del régimen laboral",
      f"Título II, Capítulo I (mismo numeral de capítulo, título distinto): {por_titulo.get(('II', 'I'))!r}")

print("\nsin ningún 'TÍTULO' en el texto: titulo_num queda None, no rompe (leyes sin títulos formales)")
caps7 = extraer_capitulos("Capítulo I — Disposiciones generales\nArt. 1°.- Objeto.\n")
check(caps7[0]["titulo_num"] is None, f"sin título en el texto -> titulo_num None: {caps7}")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
