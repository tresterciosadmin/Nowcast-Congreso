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
    chk(O.oficialista_por_fecha("PRO", pd.Timestamp("2024-06-01")) is False,
        "PRO opositor/aliado en 2024 (no cuenta como oficialista)")

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
    chk(by.loc["4-D-2024", "origen"] == "OPOSICION", "Macrista 2024 (Milei) -> OPOSICION")
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
