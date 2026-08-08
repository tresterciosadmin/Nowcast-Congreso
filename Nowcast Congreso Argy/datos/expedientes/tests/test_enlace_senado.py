"""Tests offline de datos/expedientes/src/enlace_senado.py — sin red, sin datos reales.

Cada test fija una forma REAL en que el enlace se puede romper. Un enlace que
matchea de más es peor que uno que matchea de menos: un falso positivo mete la
votación de otro proyecto en la cadena de dos cámaras y contamina
P(revisora | aprobó origen), que es justo lo que el módulo existe para medir.

    python datos/expedientes/tests/test_enlace_senado.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enlace_senado import (  # noqa: E402
    construir_cadena,
    construir_enlace,
    expediente_en_titulo,
    mapa_od,
    normalizar_expediente,
    od_en_titulo,
    prefijo,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ───────────────────────── normalización ─────────────────────────
print("normalizar_expediente")

check(normalizar_expediente("CD-38/22-PL") == "0038-CD-2022",
      "formato Senado con sufijo -PL")
check(normalizar_expediente("S-2234/22-PD") == "2234-S-2022",
      "formato Senado origen propio")
check(normalizar_expediente("PE-184/21-AC") == "0184-PE-2021",
      "formato Senado mensaje del Ejecutivo")
check(normalizar_expediente("1623-D-2018") == "1623-D-2018",
      "formato HCDN se conserva")
check(normalizar_expediente("16-D-2018") == "0016-D-2018",
      "HCDN con número corto se rellena a 4 dígitos")
check(normalizar_expediente("0016-PE-2019") == "0016-PE-2019",
      "HCDN del Ejecutivo")
# La canónica mezcla año de 4 y de 2 dígitos según la fuente. Exigir 4 dejaba
# 1.628 actas de Diputados sin enlazar; lo detectó la corrida real del 08-08.
check(normalizar_expediente("5094-D-18") == "5094-D-2018",
      "HCDN con año de 2 dígitos")
check(normalizar_expediente("82-S-17") == "0082-S-2017",
      "HCDN corto con año de 2 dígitos")
check(normalizar_expediente("16-JGM-11") == "0016-JGM-2011",
      "HCDN con letra de 3 caracteres (Jefatura de Gabinete)")
check(normalizar_expediente("  cd-38/22  ") == "0038-CD-2022",
      "tolera minúsculas y espacios")

# Lo que NO debe parsear: ante la duda, None.
for basura in [None, "", "  ", "sin datos", "NAN", "-", "varios", "38/22",
               "expediente 38", float("nan")]:
    check(normalizar_expediente(basura) is None,
          f"basura {basura!r} debe dar None, no un match inventado")

check(prefijo("0038-CD-2022") == "CD", "prefijo CD")
check(prefijo(None) is None, "prefijo de None")
check(prefijo("cualquiera") is None, "prefijo de algo mal formado")


# ───────────────────────── fixtures ─────────────────────────
def fixture():
    actas = pd.DataFrame([
        # cadena completa: mismo proyecto votado en las dos cámaras
        {"acta_id": "dip:1", "camara": "diputados", "expediente": "7435-D-2018",
         "fecha": "2018-11-07", "resultado": "APROBADO"},
        {"acta_id": "sen:1", "camara": "senado", "expediente": "CD-57/18-PL",
         "fecha": "2018-12-05", "resultado": "APROBADO"},
        # sólo Senado, origen propio
        {"acta_id": "sen:2", "camara": "senado", "expediente": "S-108/18-PD",
         "fecha": "2018-08-01", "resultado": "APROBADO"},
        # expediente que no existe en el maestro
        {"acta_id": "sen:3", "camara": "senado", "expediente": "CD-999/18-PL",
         "fecha": "2018-09-01", "resultado": "RECHAZADO"},
        # expediente ilegible
        {"acta_id": "sen:4", "camara": "senado", "expediente": "sin datos",
         "fecha": "2018-09-02", "resultado": None},
        # acta sin expediente: no debe aparecer en la salida
        {"acta_id": "sen:5", "camara": "senado", "expediente": None,
         "fecha": "2018-09-03", "resultado": None},
        # dos votaciones del mismo proyecto en Diputados (vuelve en revisión)
        {"acta_id": "dip:2", "camara": "diputados", "expediente": "7435-D-2018",
         "fecha": "2019-02-20", "resultado": "APROBADO"},
    ])
    actas["fecha"] = pd.to_datetime(actas["fecha"])
    expedientes = pd.DataFrame([
        {"proyecto_id": "HCDN1", "camara_origen": "Diputados",
         "exp_diputados": "7435-D-2018", "exp_senado": "0057-CD-2018",
         "tipo": "LEY", "titulo": "cadena completa"},
        {"proyecto_id": "HCDN2", "camara_origen": "Senado",
         "exp_diputados": "0108-S-2018", "exp_senado": "0108-S-2018",
         "tipo": "LEY", "titulo": "origen senado"},
    ])
    return actas, expedientes


# ───────────── rescate del expediente desde el título ─────────────
# La columna `expediente` viene vacía en el 92% de las actas del Senado, pero el
# título lo trae escrito adentro en 2.229 de ellas. Es lo que llevó la cobertura
# del Senado de 8,1% a 72,4% sin volver a scrapear nada.
print("\nexpediente_en_titulo")

check(expediente_en_titulo("Reforma Laboral. PE-608/03. Votacion en general")
      == "0608-PE-2003", "expediente en medio del título")
check(expediente_en_titulo("Presupuesto 2026. Artículo 67. CD-30/25-PL")
      == "0030-CD-2025", "con sufijo -PL pegado")
check(expediente_en_titulo("Moción sobre el OD 701/25. CD-31/25-PL , O.D. 701/2025")
      == "0031-CD-2025", "elige el expediente y no el número de orden del día")
check(expediente_en_titulo("Dictamen sobre S-2234/22") == "2234-S-2022",
      "origen Senado dentro del título")

for t in [None, "", "Presupuesto 2026", "Ley Glaciares",
          "Creación de la Universidad Nacional de Rio Tercero. O.D. 206/2023",
          float("nan")]:
    check(expediente_en_titulo(t) is None,
          f"título sin expediente {t!r} -> None (una O.D. NO es un expediente)")

print("\nprecedencia: el campo manda sobre el título")
actas_p = pd.DataFrame([
    # tiene las dos cosas y NO coinciden: el título nombra un expediente
    # REFERENCIADO (proyecto que se reproduce), no el que se vota.
    {"acta_id": "sen:a", "camara": "senado", "expediente": "S-967/15-PL",
     "titulo": "ROMERO: REPRODUCE EL PROYECTO 1297-S-2013", "fecha": "2015-05-01",
     "resultado": "APROBADO"},
    # sin campo: se rescata del título
    {"acta_id": "sen:b", "camara": "senado", "expediente": None,
     "titulo": "Reforma Laboral. PE-608/03. Votacion en general", "fecha": "2004-03-01",
     "resultado": "APROBADO"},
])
actas_p["fecha"] = pd.to_datetime(actas_p["fecha"])
exp_p = pd.DataFrame([{"proyecto_id": "HCDNa", "camara_origen": "Senado",
                       "exp_diputados": "0967-S-2015", "exp_senado": "0967-S-2015",
                       "tipo": "LEY", "titulo": "x"}])
e_p = construir_enlace(actas_p, exp_p).set_index("acta_id")
check(e_p.loc["sen:a", "clave"] == "0967-S-2015",
      "con campo y título distintos gana el CAMPO (el título cita otro expediente)")
check(e_p.loc["sen:a", "origen_clave"] == "campo", "queda marcado el origen 'campo'")
check(e_p.loc["sen:b", "clave"] == "0608-PE-2003", "sin campo se usa el título")
check(e_p.loc["sen:b", "origen_clave"] == "titulo", "queda marcado el origen 'titulo'")
check(e_p.loc["sen:a", "proyecto_id"] == "HCDNa",
      "el rescate no rompe el enlace normal")

# ───────────── puente por ORDEN DEL DÍA (sólo Diputados) ─────────────
# Desde 2020 las actas de Diputados no traen expediente (0 de 369 entre 2024 y
# 2026) ni lo nombran en el título, pero sí traen la O.D. Es el puente de la
# ventana que le importa al producto.
print("\nod_en_titulo")

check(od_en_titulo("O. D. 759 - DNU 179/2025, QUE APRUEBA...") == "759",
      "O.D. con espacios y puntos")
check(od_en_titulo("O.D. 790 - INCREMENTO EXCEPCIONAL") == "790", "O.D. junta")
check(od_en_titulo("OD Nº 0206 - ALGO") == "206", "quita ceros a la izquierda")
for t in ["PLAN DE LABOR", "APARTAMIENTO DE REGLAMENTO SOLICITADO POR EL DIP. X",
          None, "", float("nan")]:
    check(od_en_titulo(t) is None, f"sin O.D. {t!r} -> None")

print("\nmapa_od")
res = pd.DataFrame([
    {"proyecto_id": "P1", "od_numero": "0759", "od_publicacion": "2025-09-01"},
    {"proyecto_id": "P2", "od_numero": "0790", "od_publicacion": "2025-10-01"},
    # misma O.D. y año apuntando a dos proyectos: ambigua, se descarta
    {"proyecto_id": "P3", "od_numero": "0800", "od_publicacion": "2025-11-01"},
    {"proyecto_id": "P4", "od_numero": "0800", "od_publicacion": "2025-11-01"},
    # misma numeración, OTRO año: no choca, las O.D. se renumeran cada año
    {"proyecto_id": "P5", "od_numero": "0759", "od_publicacion": "2024-09-01"},
])
m = mapa_od(res)
check(m.get((2025, "759")) == "P1", "clave (año, O.D.) resuelve")
check(m.get((2024, "759")) == "P5", "la misma O.D. de otro año es otro proyecto")
check((2025, "800") not in m, "O.D. ambigua se descarta, no se elige una al azar")
check(mapa_od(pd.DataFrame({"x": [1]})) == {}, "sin columnas devuelve mapa vacío")

print("\npuente O.D.: aplica a Diputados y NO al Senado")
actas_od = pd.DataFrame([
    {"acta_id": "dip:od", "camara": "diputados", "expediente": None,
     "titulo": "O. D. 759 - DNU 179/2025", "fecha": "2025-10-15", "resultado": "APROBADO"},
    # ⛔ el Senado numera SUS PROPIAS O.D.: buscarlas en la tabla de HCDN
    # devolvería un proyecto ajeno. Este es el test que impide ese falso positivo.
    {"acta_id": "sen:od", "camara": "senado", "expediente": None,
     "titulo": "Universidad Nacional de Rio Tercero. O.D. 759/2025", "fecha": "2025-11-20",
     "resultado": "APROBADO"},
    # una O.D. de fin de año se vota al siguiente
    {"acta_id": "dip:od2", "camara": "diputados", "expediente": None,
     "titulo": "O.D. 790 - JUBILACIONES", "fecha": "2026-03-04", "resultado": "APROBADO"},
    # procedimental: no debe enlazar con nada
    {"acta_id": "dip:pl", "camara": "diputados", "expediente": None,
     "titulo": "PLAN DE LABOR", "fecha": "2025-10-15", "resultado": None},
])
actas_od["fecha"] = pd.to_datetime(actas_od["fecha"])
exp_od = pd.DataFrame([{"proyecto_id": "P1", "camara_origen": "Diputados",
                        "exp_diputados": "0001-D-2025", "exp_senado": None,
                        "tipo": "LEY", "titulo": "x"}])
e_od = construir_enlace(actas_od, exp_od, res).set_index("acta_id")

check(e_od.loc["dip:od", "proyecto_id"] == "P1", "acta de Diputados enlaza por O.D.")
check(e_od.loc["dip:od", "metodo"] == "od_titulo", "queda marcado el método od_titulo")
check(e_od.loc["dip:od2", "proyecto_id"] == "P2",
      "O.D. publicada a fin de año se vota al siguiente y matchea igual")
check("sen:od" not in e_od.index or pd.isna(e_od.loc["sen:od", "proyecto_id"]),
      "⛔ el acta del SENADO NO enlaza por O.D. (numeración propia = falso positivo)")
check("dip:pl" not in e_od.index or pd.isna(e_od.loc["dip:pl", "proyecto_id"]),
      "una votación procedimental (PLAN DE LABOR) no enlaza con nada")

print("\nsin resultados el módulo sigue corriendo")
e_sin = construir_enlace(actas_od, exp_od, None)
check(len(e_sin) >= 0, "sin la tabla de resultados no rompe, sólo pierde el puente")

print("\nconstruir_enlace")
actas, expedientes = fixture()
enl = construir_enlace(actas, expedientes)

check(len(enl) == 6, f"las actas sin expediente se excluyen (esperaba 6, dio {len(enl)})")
check(set(enl["acta_id"]) == {"dip:1", "dip:2", "sen:1", "sen:2", "sen:3", "sen:4"},
      "conjunto de actas con expediente")

por_acta = enl.set_index("acta_id")
check(por_acta.loc["dip:1", "proyecto_id"] == "HCDN1", "acta de Diputados enlaza por exp_diputados")
check(por_acta.loc["sen:1", "proyecto_id"] == "HCDN1",
      "acta del Senado enlaza al MISMO proyecto por la numeración CD")
check(por_acta.loc["sen:1", "metodo"] == "exp_senado", "método correcto para el Senado")
check(bool(por_acta.loc["sen:1", "es_cruce"]) is True, "prefijo CD marca cruce entre cámaras")
check(bool(por_acta.loc["sen:2", "es_cruce"]) is False, "prefijo S no es cruce")
check(pd.isna(por_acta.loc["sen:3", "proyecto_id"]),
      "expediente inexistente NO debe enlazar (falso positivo)")
check(pd.isna(por_acta.loc["sen:4", "proyecto_id"]), "expediente ilegible no enlaza")
check(por_acta.loc["sen:4", "clave"] is None, "expediente ilegible deja clave nula")

print("\nambigüedad: una clave que apunta a dos proyectos NO debe enlazar")
amb = pd.concat([expedientes, pd.DataFrame([{
    "proyecto_id": "HCDN9", "camara_origen": "Diputados",
    "exp_diputados": "9999-D-2018", "exp_senado": "0057-CD-2018",  # choca con HCDN1
    "tipo": "LEY", "titulo": "duplicado"}])], ignore_index=True)
enl_amb = construir_enlace(actas, amb).set_index("acta_id")
check(pd.isna(enl_amb.loc["sen:1", "proyecto_id"]),
      "clave ambigua se descarta en vez de elegir una al azar")

print("\nconstruir_cadena")
cad = construir_cadena(enl, expedientes).set_index("proyecto_id")
check(int(cad.loc["HCDN1", "n_camaras"]) == 2, "HCDN1 tiene votación en las dos cámaras")
check(int(cad.loc["HCDN2", "n_camaras"]) == 1, "HCDN2 sólo en una")
check(cad.loc["HCDN1", "acta_sen"] == "sen:1", "acta del Senado en la cadena")
check(cad.loc["HCDN1", "acta_dip"] == "dip:1",
      "con dos votaciones sin marca se toma la PRIMERA, no la última "
      "(la general va antes que el articulado)")
check(int(cad.loc["HCDN1", "n_actas_dip"]) == 2,
      "queda registrado cuántas votaciones hubo en la cámara")

# ─────────── elegir la votación DECISIVA ───────────
# La primera versión tomaba la ÚLTIMA votación de cada cámara. Para la Ley Bases
# —50 votaciones del mismo proyecto en Diputados— eso devolvía el último
# artículo en vez de la votación en general. El 15,2% de los pares
# (proyecto, cámara) tiene más de una votación: no es un caso raro.
print("\nvotación decisiva: general antes que articulado")
actas_g = pd.DataFrame([
    {"acta_id": "g:part1", "camara": "diputados", "expediente": "7435-D-2018",
     "titulo": "LEY BASES. EN PARTICULAR. ARTICULO 5", "fecha": "2024-02-06",
     "resultado": "APROBADO"},
    {"acta_id": "g:gen", "camara": "diputados", "expediente": "7435-D-2018",
     "titulo": "LEY BASES. VOTACION EN GENERAL", "fecha": "2024-02-02",
     "resultado": "APROBADO"},
    {"acta_id": "g:part2", "camara": "diputados", "expediente": "7435-D-2018",
     "titulo": "LEY BASES. EN PARTICULAR. CAPITULO XII", "fecha": "2024-02-08",
     "resultado": "RECHAZADO"},
])
actas_g["fecha"] = pd.to_datetime(actas_g["fecha"])
exp_g = pd.DataFrame([{"proyecto_id": "LB", "camara_origen": "Diputados",
                       "exp_diputados": "7435-D-2018", "exp_senado": None,
                       "tipo": "LEY", "titulo": "Ley Bases"}])
cad_g = construir_cadena(construir_enlace(actas_g, exp_g), exp_g).set_index("proyecto_id")
check(cad_g.loc["LB", "acta_dip"] == "g:gen",
      "se elige la votación EN GENERAL aunque no sea ni la primera ni la última")
check(cad_g.loc["LB", "tipo_votacion_dip"] == "general", "queda marcada como 'general'")
check(cad_g.loc["LB", "resultado_dip"] == "APROBADO",
      "el resultado es el de la general, no el del artículo rechazado")
check(int(cad_g.loc["LB", "n_actas_dip"]) == 3, "se cuentan las 3 votaciones")

print("\nsi TODAS son en particular, se toma la primera y se avisa")
actas_p2 = actas_g[actas_g["acta_id"] != "g:gen"].copy()
cad_p2 = construir_cadena(construir_enlace(actas_p2, exp_g), exp_g).set_index("proyecto_id")
check(cad_p2.loc["LB", "acta_dip"] == "g:part1", "sin votación general, la primera")
check(cad_p2.loc["LB", "tipo_votacion_dip"] == "primera_particular",
      "queda marcado que NO se encontró una votación en general")

print("\nvotación única")
actas_u = actas_g[actas_g["acta_id"] == "g:gen"].copy()
cad_u = construir_cadena(construir_enlace(actas_u, exp_g), exp_g).set_index("proyecto_id")
check(cad_u.loc["LB", "tipo_votacion_dip"] == "unica", "una sola votación -> 'unica'")
check(int((cad["n_camaras"] == 2).sum()) == 1, "una sola cadena completa en la fixture")

print("\nrobustez")
try:
    construir_enlace(pd.DataFrame({"acta_id": ["x"]}), expedientes)
    check(False, "faltar columnas debe levantar ValueError")
except ValueError:
    check(True, "faltar columnas levanta ValueError con mensaje claro")

vacio = construir_enlace(actas.iloc[0:0].copy(), expedientes)
check(len(vacio) == 0, "entrada vacía devuelve salida vacía, no rompe")

sin_col = expedientes.drop(columns=["exp_senado"])
enl_sc = construir_enlace(actas, sin_col).set_index("acta_id")
check(pd.isna(enl_sc.loc["sen:1", "proyecto_id"]),
      "si falta exp_senado el módulo sigue corriendo y no enlaza el Senado")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
