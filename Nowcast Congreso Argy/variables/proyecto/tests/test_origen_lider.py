"""Tests offline de origen_lider (feature store: origen + líder). Fixture sintética
que imita expedientes + el contrato de variables/legislador. Sin disco/red.
Correr: python variables/proyecto/tests/test_origen_lider.py
"""
import sys, tempfile
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import origen_lider as O  # noqa: E402

OK = 0
def chk(c, m):
    global OK
    assert c, "FALLO: " + m
    OK += 1; print("  ok:", m)


def fixture():
    # 2 autores: PERON (linaje FDT-UXP) y MACRISTA (linaje PRO)
    exp = pd.DataFrame({
        "proyecto_id": ["1-D-2013", "2-D-2017", "3-D-2021", "4-D-2024", "5-D-2020"],
        "tipo": ["LEY", "LEY", "LEY", "LEY", "MENSAJE Y PROYECTO DE LEY"],
        "fecha_publicacion": ["2013-06-01", "2017-06-01", "2021-06-01", "2024-06-01", "2020-06-01"],
        "autor": ["PERON, Juan", "PERON, Juan", "PERON, Juan", "MACRISTA, Ana", "Poder Ejecutivo"],
        "camara_origen": ["Diputados"] * 5,
    })
    legis = pd.DataFrame({"legislador_id": ["leg:p", "leg:m"],
                          "nombre": ["PERON, Juan", "MACRISTA, Ana"]})
    leg_bloques = pd.DataFrame({
        "legislador_id": ["leg:p", "leg:m"],
        "bloque_norm": ["FpV", "PRO"],
        "anio_desde": [2011, 2015], "anio_hasta": [2025, 2025],
        "linaje": ["FdT-UxP (kirchnerismo)", "PRO"],
    })
    # leyes previas de PERON para alto productor: 3 sancionadas antes de 2021
    leyes = pd.DataFrame({"proyecto_id": ["1-D-2013", "2-D-2017", "1-D-2013b", "1-D-2013c"]})
    exp_prod = pd.concat([exp, pd.DataFrame({
        "proyecto_id": ["1-D-2013b", "1-D-2013c"], "tipo": ["LEY", "LEY"],
        "fecha_publicacion": ["2014-06-01", "2015-06-01"],
        "autor": ["PERON, Juan", "PERON, Juan"], "camara_origen": ["Diputados", "Diputados"]})],
        ignore_index=True)
    return {"exp": exp_prod, "giros": None, "leyes": leyes, "comis": None,
            "legis": legis, "leg_bloques": leg_bloques}


def main():
    # --- normalización de nombres ---
    chk(O._norm("PERÓN, Juan") == "PERON JUAN", "normaliza acentos y 'APELLIDO, Nombre'")
    chk(O._norm("de la RÚA,  Fernando") == "DE LA RUA FERNANDO", "normaliza espacios/acentos")

    # --- mapeo de linaje real (con sufijos/nombres largos) a código ---
    chk(O._linaje_code("FdT-UxP (kirchnerismo)") == "KIRCHNERISMO", "FdT-UxP (kirchnerismo) -> KIRCHNERISMO")
    chk(O._linaje_code("RADICALISMO") == "RADICALISMO", "RADICALISMO -> RADICALISMO (no UCR literal)")
    chk(O._linaje_code("COALICION CIVICA") == "CC", "COALICION CIVICA -> CC")
    chk(O._linaje_code("LA LIBERTAD AVANZA") == "LLA", "LA LIBERTAD AVANZA -> LLA")
    chk(O._linaje_code("PROGRESISMO") == "PROGRESISMO", "PROGRESISMO no se confunde con PRO")
    chk(O._linaje_code("OTRO / PROVINCIAL") == "OTRO", "OTRO / PROVINCIAL -> OTRO (no matchea PRO)")
    chk(O.oficialista_por_fecha("RADICALISMO", pd.Timestamp("2017-06-01")) is True, "radicalismo oficialista con Macri 2017")
    chk(O.oficialista_por_fecha("FdT-UxP (kirchnerismo)", pd.Timestamp("2021-06-01")) is True, "kirchnerismo oficialista 2021 (A.Fernández)")

    # --- regla de gobierno por fecha ---
    chk(O.oficialista_por_fecha("FDT-UXP", pd.Timestamp("2013-06-01")) is True,
        "kirchnerismo oficialista en 2013")
    chk(O.oficialista_por_fecha("FDT-UXP", pd.Timestamp("2017-06-01")) is False,
        "kirchnerismo opositor en 2017 (Macri)")
    chk(O.oficialista_por_fecha("PRO", pd.Timestamp("2017-06-01")) is True,
        "PRO oficialista en 2017")
    chk(O.oficialista_por_fecha("LLA", pd.Timestamp("2024-06-01")) is True,
        "LLA oficialista en 2024")
    chk(O.oficialista_por_fecha("PRO", pd.Timestamp("2024-06-01")) is True,
        "PRO oficialista (aliado) en 2024 con Milei — fix PRO-Milei 08-09")

    # --- núcleo vs aliado (Valle 2026-08-14) ---
    chk(O.clase_oficialismo("LLA", pd.Timestamp("2024-06-01")) == "NUCLEO",
        "LLA = NUCLEO en Milei (partido de gobierno)")
    chk(O.clase_oficialismo("PRO", pd.Timestamp("2024-06-01")) == "ALIADO",
        "PRO = ALIADO en Milei (oficialista no-núcleo)")
    chk(O.clase_oficialismo("PRO", pd.Timestamp("2017-06-01")) == "NUCLEO",
        "PRO = NUCLEO con Macri")
    chk(O.clase_oficialismo("RADICALISMO", pd.Timestamp("2017-06-01")) == "ALIADO",
        "RADICALISMO = ALIADO con Macri (Cambiemos)")
    chk(O.clase_oficialismo("FDT-UXP", pd.Timestamp("2013-06-01")) == "NUCLEO",
        "kirchnerismo = NUCLEO en 2013")
    chk(O.clase_oficialismo("PRO", pd.Timestamp("2013-06-01")) is None,
        "PRO opositor en 2013 -> clase None")

    # --- fallback por prefijo de tokens (MATCH_AUTOR_FUZZY, prendido por
    # defecto desde el 14-09 -- decisión de Franco tras medir P idéntico) ---
    # Caso real que lo motivó: el autor viene "PITROLA, NESTOR" pero
    # legisladores.csv trae el nombre completo "PITROLA Néstor Antonio" -> el
    # exact-match falla aunque la persona sea inequívoca. Los dos estados del
    # flag se fijan EXPLÍCITAMENTE acá (no se asume el default del módulo),
    # así el test no se rompe si el default vuelve a cambiar.
    _flag_original = O.MATCH_AUTOR_FUZZY
    mapa_pitrola = {"PITROLA NESTOR ANTONIO": [(2015, 2025, "IZQUIERDA")]}
    chk(O._match_prefijo("PITROLA NESTOR", mapa_pitrola) == "PITROLA NESTOR ANTONIO",
        "_match_prefijo encuentra el único candidato con ese apellido+nombre como prefijo")
    try:
        O.MATCH_AUTOR_FUZZY = False
        chk(O._linaje_autor("PITROLA NESTOR", 2020, mapa_pitrola) is None,
            "con el flag apagado, el nombre incompleto NO matchea (exact-match puro)")
        O.MATCH_AUTOR_FUZZY = True
        chk(O._linaje_autor("PITROLA NESTOR", 2020, mapa_pitrola) == "IZQUIERDA",
            "con el flag prendido, el fallback por prefijo resuelve el linaje")
    finally:
        O.MATCH_AUTOR_FUZZY = _flag_original
    # Ambigüedad: DOS legisladores con el mismo apellido y el mismo nombre como
    # prefijo -> el fallback NO adivina, se queda sin match.
    mapa_ambiguo = {
        "PEREZ JUAN CARLOS": [(2015, 2025, "PRO")],
        "PEREZ JUAN MANUEL": [(2015, 2025, "RADICALISMO")],
    }
    chk(O._match_prefijo("PEREZ JUAN", mapa_ambiguo) is None,
        "dos candidatos con el mismo prefijo -> no matchea (nunca se adivina)")
    # Nombre COMPLETO más largo que el del padrón (padrón abreviado, autor completo):
    # el prefijo funciona en cualquier dirección mientras sea único.
    mapa_corto = {"BANFI KARINA": [(2019, 2025, "COALICION CIVICA")]}
    chk(O._match_prefijo("BANFI KARINA VERONICA", mapa_corto) == "BANFI KARINA",
        "el prefijo matchea también cuando el nombre del padrón es el más corto")

    # --- construir features ---
    dfs = fixture()
    with tempfile.TemporaryDirectory() as d:
        jefes = Path(d) / "jefes.csv"
        jefes.write_text("nombre\n\"PERON, Juan\"\n", encoding="utf-8")
        feat = O.construir_features(dfs, jefes)

    by = feat.set_index("proyecto_id")
    chk(by.loc["5-D-2020", "origen"] == "EJECUTIVO", "MENSAJE -> origen EJECUTIVO")
    chk(by.loc["1-D-2013", "origen"] == "OFICIALISMO", "Perón 2013 -> OFICIALISMO")
    chk(by.loc["2-D-2017", "origen"] == "OPOSICION", "Perón 2017 (Macri) -> OPOSICION")
    chk(by.loc["4-D-2024", "origen"] == "ALIADOS", "PRO/Macrista 2024 (Milei) -> ALIADOS (aliado, no núcleo)")
    chk(bool(by.loc["1-D-2013", "match_autor"]), "autor emparejado con bloque")

    # --- líder: alto productor walk-forward (3 leyes previas a 2021) ---
    chk(bool(by.loc["3-D-2021", "lider_alto_productor"]),
        "Perón en 2021 es alto productor (>=3 leyes previas)")
    chk(not bool(by.loc["1-D-2013", "lider_alto_productor"]),
        "en 2013 aún NO es alto productor (sin leyes previas) -> sin leakage")
    # --- líder: jefe de bloque (curado) ---
    chk(bool(by.loc["1-D-2013", "lider_jefe_bloque"]), "Perón figura como jefe de bloque")
    chk(bool(by.loc["1-D-2013", "lider"]), "lider = OR de las señales")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
