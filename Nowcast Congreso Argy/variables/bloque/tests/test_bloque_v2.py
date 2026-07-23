"""Tests offline del v2 (dirección condicionada por tema/origen) de variables/bloque.
Sin datos reales ni red: votos sintéticos con dirección conocida por bloque/tema.
Correr desde /tmp (protocolo de sync):  python test_bloque_v2.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import bloque as B  # noqa: E402


def _votos_sinteticos():
    """20 actas antes de la fecha objetivo. El bloque OPO vota NEGATIVO en las actas
    de tema ECON y AFIRMATIVO en el resto; OFI siempre AFIRMATIVO. Así la dirección
    INCONDICIONAL de OPO es mayoritariamente afirmativa, pero CONDICIONADA a ECON es
    negativa."""
    filas, cond = [], []
    base = pd.Timestamp("2020-01-01")
    for k in range(20):
        aid = f"a{k}"
        fecha = base + pd.Timedelta(days=k)
        tema = "ECON" if k < 8 else "OTRO"          # 8 actas ECON, 12 otras
        cond.append({"acta_id": aid, "tema_area": tema, "origen": "OPOSICION"})
        opo_dir = "NEGATIVO" if tema == "ECON" else "AFIRMATIVO"
        for L in range(3):
            filas.append(dict(acta_id=aid, fecha=fecha, camara="diputados",
                              bloque_linaje="OPO", legislador_id=f"opo{L}", conducta=opo_dir))
            filas.append(dict(acta_id=aid, fecha=fecha, camara="diputados",
                              bloque_linaje="OFI", legislador_id=f"ofi{L}", conducta="AFIRMATIVO"))
    return pd.DataFrame(filas), pd.DataFrame(cond)


def _idx(esc):
    return {b["bloque"]: b for b in esc}


def test_sin_tema_es_v1():
    votos, _ = _votos_sinteticos()
    esc = B.proyectar_postura(votos, "2020-06-01", "diputados", padron_path="__no__")
    for b in esc:
        assert b["_share_afirm"] == b["_share_incond"], "sin tema debe ser incondicional"
        assert b["_cond"] is None
    print("OK sin tema == v1 incondicional")


def test_condicionar_da_vuelta_la_direccion():
    votos, cond = _votos_sinteticos()
    v1 = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", padron_path="__no__"))
    econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                    tema="ECON", cond_por_acta=cond, padron_path="__no__"))
    # incondicional: OPO afirmativo (12 de 20 actas) -> AFIRMATIVO
    assert v1["OPO"]["linea"] == "AFIRMATIVO", v1["OPO"]
    # condicionado a ECON: OPO negativo -> con 8 actas y shrink 5, share < 0.5
    assert econ["OPO"]["linea"] == "NEGATIVO", econ["OPO"]
    assert econ["OPO"]["_share_afirm"] < v1["OPO"]["_share_afirm"]
    assert econ["OPO"]["_n_cond"] == 8
    # OFI siempre afirmativo, no cambia
    assert econ["OFI"]["linea"] == "AFIRMATIVO"
    print("OK condicionar ECON da vuelta OPO a NEGATIVO (share %.2f->%.2f)"
          % (v1["OPO"]["_share_afirm"], econ["OPO"]["_share_afirm"]))


def test_shrinkage_no_da_vuelta_con_pocas():
    """Con MUCHAS actas incondicionales afirmativas y POCAS condicionadas negativas,
    el encogimiento evita el vuelco espurio."""
    votos, cond = _votos_sinteticos()
    # dejo solo 1 acta ECON en el mapa -> n_cond=1, k=5 -> domina la incondicional
    cond1 = cond[cond["acta_id"] == "a0"]
    econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                    tema="ECON", cond_por_acta=cond1, padron_path="__no__"))
    assert econ["OPO"]["_n_cond"] == 1
    assert econ["OPO"]["linea"] == "AFIRMATIVO", "1 sola acta no debe dar vuelta la dirección"
    print("OK shrinkage: 1 acta condicionada no vuelca (share %.2f)" % econ["OPO"]["_share_afirm"])


def test_tema_sin_match_cae_a_incondicional():
    votos, cond = _votos_sinteticos()
    v1 = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", padron_path="__no__"))
    # tema inexistente en el mapa -> 0 actas -> incondicional
    xx = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                  tema="NOEXISTE", cond_por_acta=cond, padron_path="__no__"))
    assert xx["OPO"]["_share_afirm"] == v1["OPO"]["_share_afirm"]
    print("OK tema sin match cae a incondicional sin romper")


def test_cond_map_acepta_dict_y_df():
    votos, cond = _votos_sinteticos()
    d = {r["acta_id"]: {"tema_area": r["tema_area"]} for _, r in cond.iterrows()}
    a = B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                            cond_por_acta=d, padron_path="__no__")
    b = B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                            cond_por_acta=cond, padron_path="__no__")
    assert _idx(a)["OPO"]["_share_afirm"] == _idx(b)["OPO"]["_share_afirm"]
    print("OK _cond_map acepta dict y DataFrame por igual")


if __name__ == "__main__":
    test_sin_tema_es_v1()
    test_condicionar_da_vuelta_la_direccion()
    test_shrinkage_no_da_vuelta_con_pocas()
    test_tema_sin_match_cae_a_incondicional()
    test_cond_map_acepta_dict_y_df()
    print("\n== 5 chequeos v2 OK ==")
