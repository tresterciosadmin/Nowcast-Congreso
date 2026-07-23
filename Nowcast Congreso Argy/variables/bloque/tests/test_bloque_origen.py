"""Tests del condicionamiento por ORIGEN (lado + guard de gobierno) en el proyector.
Correr:  python variables/bloque/tests/test_bloque_origen.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import bloque as B  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def _votos():
    """Historia sintética 2025-2026 (era MILEI) + una acta de era AF (2023).
    Bloque X: AFIRMA todo lo del gobierno, RECHAZA lo de la oposición."""
    filas = []
    def acta(aid, fecha, direccion, n=6):
        for i in range(n):
            filas.append({"acta_id": aid, "fecha": fecha, "camara": "diputados",
                          "bloque_linaje": "X", "legislador_id": f"x{i}",
                          "conducta": direccion})
    # 4 actas de origen GOBIERNO -> X afirma
    for k, f in enumerate(["2025-03-01", "2025-06-01", "2025-09-01", "2026-02-01"]):
        acta(f"g{k}", f, "AFIRMATIVO")
    # 4 actas de origen OPOSICION -> X niega
    for k, f in enumerate(["2025-04-01", "2025-07-01", "2025-10-01", "2026-03-01"]):
        acta(f"o{k}", f, "NEGATIVO")
    # 1 acta era AF (2023) etiquetada GOBIERNO donde X NEGABA: si el guard no
    # filtrara por gobierno, ensuciaría el condicionado
    acta("viejaAF", "2023-06-01", "NEGATIVO")
    df = pd.DataFrame(filas)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


COND = pd.DataFrame([
    {"acta_id": "g0", "origen": "EJECUTIVO", "origen_lado": "GOBIERNO", "gobierno": "MILEI"},
    {"acta_id": "g1", "origen": "OFICIALISMO", "origen_lado": "GOBIERNO", "gobierno": "MILEI"},
    {"acta_id": "g2", "origen": "EJECUTIVO", "origen_lado": "GOBIERNO", "gobierno": "MILEI"},
    {"acta_id": "g3", "origen": "OFICIALISMO", "origen_lado": "GOBIERNO", "gobierno": "MILEI"},
    {"acta_id": "o0", "origen": "OPOSICION", "origen_lado": "OPOSICION", "gobierno": "MILEI"},
    {"acta_id": "o1", "origen": "OPOSICION", "origen_lado": "OPOSICION", "gobierno": "MILEI"},
    {"acta_id": "o2", "origen": "OPOSICION", "origen_lado": "OPOSICION", "gobierno": "MILEI"},
    {"acta_id": "o3", "origen": "OPOSICION", "origen_lado": "OPOSICION", "gobierno": "MILEI"},
    {"acta_id": "viejaAF", "origen": "EJECUTIVO", "origen_lado": "GOBIERNO", "gobierno": "AF"},
])

F = "2026-07-01"  # ventana 730d: cubre 2024-07 -> 2026-07 (era MILEI pura)... y la
# vieja de 2023 queda FUERA de la ventana; para probar el guard usamos ventana larga.


def _share(esc, bloque="X"):
    b = [e for e in esc if e["bloque"] == bloque][0]
    return b["_share_afirm"], b["linea"], b["_n_cond"]


def main():
    chk(B._gobierno_por_fecha("2017-01-01") == "MACRI", "gobierno_por_fecha MACRI")
    chk(B._gobierno_por_fecha("2026-07-01") == "MILEI", "gobierno_por_fecha MILEI")

    votos = _votos()
    kw = dict(padron_path="/no/existe", k_shrink=2.0, cond_por_acta=COND)

    # incondicional: mitad y mitad -> share ~0.5
    esc0 = B.proyectar_postura(votos, F, "diputados", padron_path="/no/existe")
    s0, _, _ = _share(esc0)
    chk(abs(s0 - 0.5) < 0.01, "incondicional: 4 afirma / 4 niega -> share ~0,5")

    # condicionado por LADO GOBIERNO -> afirma
    esc1 = B.proyectar_postura(votos, F, "diputados", origen="GOBIERNO", **kw)
    s1, l1, n1 = _share(esc1)
    chk(l1 == "AFIRMATIVO" and s1 > 0.6 and n1 == 4,
        "origen=GOBIERNO (lado): agrupa EJECUTIVO+OFICIALISMO y da AFIRMATIVO")

    # condicionado por LADO OPOSICION -> niega
    esc2 = B.proyectar_postura(votos, F, "diputados", origen="OPOSICION", **kw)
    s2, l2, n2 = _share(esc2)
    chk(l2 == "NEGATIVO" and s2 < 0.4 and n2 == 4,
        "origen=OPOSICION: el mismo bloque da NEGATIVO (el origen invierte el signo)")

    # condicionado FINO por EJECUTIVO -> solo las 2 actas EJECUTIVO
    esc3 = B.proyectar_postura(votos, F, "diputados", origen="EJECUTIVO", **kw)
    _, l3, n3 = _share(esc3)
    chk(n3 == 2 and l3 == "AFIRMATIVO", "origen=EJECUTIVO (fino) matchea solo esas actas")

    # guard del recambio: ventana LARGA que alcanza la acta AF-2023 etiquetada
    # GOBIERNO donde X negaba; con guard NO debe entrar al condicionado
    esc4 = B.proyectar_postura(votos, F, "diputados", origen="GOBIERNO",
                               ventana_dias=1500, **kw)
    _, l4, n4 = _share(esc4)
    chk(n4 == 4 and l4 == "AFIRMATIVO",
        "guard de gobierno: la acta de la era AF NO entra aunque la ventana la cubra")

    # sin etiquetas de origen en el mapa -> cae a incondicional (aviso, no rompe)
    esc5 = B.proyectar_postura(votos, F, "diputados", origen="GOBIERNO",
                               padron_path="/no/existe", k_shrink=2.0,
                               cond_por_acta=pd.DataFrame({"acta_id": ["zz"],
                                                           "tema_area": ["ECON"]}))
    s5, _, n5 = _share(esc5)
    chk(n5 == 0 and abs(s5 - 0.5) < 0.01,
        "sin actas etiquetadas con origen -> incondicional (retrocompatible)")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
