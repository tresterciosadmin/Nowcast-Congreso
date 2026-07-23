"""Tests offline de origen_por_acta (insumos sintéticos, sin disco del repo).
Correr:  python variables/proyecto/tests/test_origen_por_acta.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import origen_por_acta as O  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def _dfs():
    """Mundo chico: 1 autor PRO (linaje PRO 2014-2026), proyectos y actas."""
    actas = pd.DataFrame([
        # vía codigo, letra PE -> EJECUTIVO (era Macri)
        {"acta_id": "a1", "fecha": "2017-05-01", "titulo": "Expediente 0010-PE-2016 - Votación",
         "expediente": "0010-PE-2016"},
        # vía codigo D: autor PRO votado en 2017 (Macri) -> OFICIALISMO
        {"acta_id": "a2", "fecha": "2017-06-01", "titulo": "lo que sea", "expediente": "0100-D-2016"},
        # EL MISMO proyecto/autor votado en 2021 (AF) -> OPOSICION (tu ejemplo PRO)
        {"acta_id": "a3", "fecha": "2021-06-01", "titulo": "lo que sea", "expediente": "0100-D-2016"},
        # vía od: "O.D. 7" publicado antes de la fecha -> proyecto MENSAJE -> EJECUTIVO (Milei)
        {"acta_id": "a4", "fecha": "2024-04-30", "titulo": "O.D. 7 - LEY DE BASES", "expediente": None},
        # vía titulo: match exacto normalizado -> autor PRO en era Milei -> OPOSICION... no:
        # PRO no gobierna con Milei en linajes (LLA); PRO es OPOSICION segun GOBIERNOS
        {"acta_id": "a5", "fecha": "2024-08-01",
         "titulo": "REGIMEN ESPECIAL DE PROMOCION DE LA ECONOMIA DEL CONOCIMIENTO Y SUS BENEFICIOS",
         "expediente": None},
        # sin nada -> DESCONOCIDO
        {"acta_id": "a6", "fecha": "2024-09-01", "titulo": "(sin titulo)", "expediente": None},
        # vía titulo_codigo: código EMBEBIDO PE-608/03 en el título (Senado viejo, era
        # Kirchner) -> EJECUTIVO directo aunque NO cruce expedientes
        {"acta_id": "a7", "fecha": "2004-06-01",
         "titulo": "Dictamen de Ordenamiento Laboral. PE-608/03.", "expediente": None},
        # vía titulo_codigo: S-100/16 embebido que SÍ cruza exp_senado -> autor GOMEZ
        # (PRO) votado en 2016 (Macri) -> OFICIALISMO
        {"acta_id": "a8", "fecha": "2016-06-01",
         "titulo": "Proyecto sobre lo que sea. S-100/16.", "expediente": None},
    ])
    expedientes = pd.DataFrame([
        {"proyecto_id": "H1", "titulo": "MENSAJE DEL PE", "fecha_publicacion": "2016-03-01",
         "exp_diputados": "0010-PE-2016", "exp_senado": None, "tipo": "MENSAJE", "autor": None},
        {"proyecto_id": "H2", "titulo": "PROYECTO DEL DIPUTADO GOMEZ SOBRE ALGO LARGO Y DESCRIPTIVO",
         "fecha_publicacion": "2016-04-01", "exp_diputados": "0100-D-2016", "exp_senado": None,
         "tipo": "LEY", "autor": "GOMEZ, Juan"},
        {"proyecto_id": "H3", "titulo": "LEY DE BASES", "fecha_publicacion": "2023-12-27",
         "exp_diputados": "0025-PE-2023", "exp_senado": None, "tipo": "MENSAJE", "autor": None},
        {"proyecto_id": "H4", "titulo": "REGIMEN ESPECIAL DE PROMOCION DE LA ECONOMIA DEL "
         "CONOCIMIENTO Y SUS BENEFICIOS", "fecha_publicacion": "2024-03-01",
         "exp_diputados": "0200-D-2024", "exp_senado": None, "tipo": "LEY", "autor": "GOMEZ, Juan"},
        # expediente del Senado que matchea el código embebido S-100/16 de a8
        {"proyecto_id": "H5", "titulo": "PROYECTO DEL SENADOR GOMEZ",
         "fecha_publicacion": "2016-05-01", "exp_diputados": None, "exp_senado": "0100-S-2016",
         "tipo": "LEY", "autor": "GOMEZ, Juan"},
    ])
    resultados = pd.DataFrame([
        {"proyecto_id": "H3", "cabecera": "H3", "od_numero": "7", "od_publicacion": "2024-04-20"},
        # otro O.D. 7 de un período VIEJO: no debe ganar (publicación más lejana)
        {"proyecto_id": "H2", "cabecera": "H2", "od_numero": "7", "od_publicacion": "2016-05-01"},
    ])
    legis = pd.DataFrame([{"legislador_id": "leg:g", "nombre": "GOMEZ, Juan"}])
    lb = pd.DataFrame([{"legislador_id": "leg:g", "anio_desde": 2014, "anio_hasta": 2026,
                        "linaje": "PRO"}])
    return {"actas": actas, "acta_exp": None, "expedientes": expedientes,
            "resultados": resultados, "legis": legis, "leg_bloques": lb}


def main():
    # helpers
    chk(O.gobierno_por_fecha("2017-05-01") == "MACRI", "gobierno_por_fecha: 2017 -> MACRI")
    chk(O.gobierno_por_fecha("2021-06-01") == "AF", "gobierno_por_fecha: 2021 -> AF")
    chk(O.gobierno_por_fecha("2024-04-30") == "MILEI", "gobierno_por_fecha: 2024 -> MILEI")
    chk(O.gobierno_por_fecha(None) is None, "gobierno_por_fecha: sin fecha -> None")
    chk(O._norm_code("10-pe-16") == "0010-PE-2016", "norm_code normaliza número/letra/año")
    chk(O._norm_code("basura") is None, "norm_code devuelve None si no es código")
    # código embebido (Senado viejo): 'PE-608/03' -> estándar '0608-PE-2003'
    chk(O._code_embebido("Ordenamiento Laboral. PE-608/03.") == "0608-PE-2003",
        "code_embebido: 'PE-608/03' -> '0608-PE-2003'")
    chk(O._code_embebido("S-1234/05 algo") == "1234-S-2005", "code_embebido: S-1234/05")
    chk(O._code_embebido("Expediente 0020-PE-2019") is None,
        "code_embebido NO dispara con el formato estándar (con guiones, sin barra)")
    chk(O._code_embebido("un titulo sin codigo") is None, "code_embebido: None si no hay código")

    res = O.etiquetar(_dfs()).set_index("acta_id")

    chk(res.loc["a1", "origen"] == "EJECUTIVO" and res.loc["a1", "via"] == "codigo",
        "vía codigo: letra PE -> EJECUTIVO")
    chk(res.loc["a1", "origen_lado"] == "GOBIERNO" and res.loc["a1", "gobierno"] == "MACRI",
        "EJECUTIVO -> lado GOBIERNO + gobierno de la fecha del acta")

    # ==== el caso conceptual de Valle: mismo autor PRO, distinta era ====
    chk(res.loc["a2", "origen"] == "OFICIALISMO" and res.loc["a2", "gobierno"] == "MACRI",
        "autor PRO votado en 2017 (Macri) -> OFICIALISMO")
    chk(res.loc["a3", "origen"] == "OPOSICION" and res.loc["a3", "gobierno"] == "AF",
        "el MISMO proyecto PRO votado en 2021 (AF) -> OPOSICION (origen a fecha del ACTA)")

    chk(res.loc["a4", "origen"] == "EJECUTIVO" and res.loc["a4", "via"] == "od"
        and res.loc["a4", "proyecto_id"] == "H3",
        "vía od: O.D. 7 elige la publicación previa MÁS CERCANA (H3, no el O.D. 7 de 2016)")
    chk(res.loc["a5", "via"] == "titulo" and res.loc["a5", "proyecto_id"] == "H4"
        and res.loc["a5", "origen"] == "OPOSICION",
        "vía titulo: match exacto normalizado -> autor PRO en era Milei = OPOSICION")
    chk(res.loc["a6", "origen"] == "DESCONOCIDO" and res.loc["a6", "origen_lado"] is None,
        "sin vía -> DESCONOCIDO con lado None (no inventa)")

    # el gobierno queda SIEMPRE, aun sin origen (sirve para el guard del proyector)
    chk(res.loc["a6", "gobierno"] == "MILEI", "gobierno etiquetado aun con origen DESCONOCIDO")

    # ==== vía código embebido (el que tapa el hueco del Senado viejo) ====
    chk(res.loc["a7", "via"] == "titulo_codigo" and res.loc["a7", "origen"] == "EJECUTIVO"
        and res.loc["a7", "gobierno"] == "KIRCHNER",
        "embebido PE-608/03: EJECUTIVO directo (aunque no cruce expedientes)")
    chk(res.loc["a8", "via"] == "titulo_codigo" and res.loc["a8", "proyecto_id"] == "H5"
        and res.loc["a8", "origen"] == "OFICIALISMO",
        "embebido S-100/16: cruza exp_senado -> autor PRO en 2016 (Macri) = OFICIALISMO")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
