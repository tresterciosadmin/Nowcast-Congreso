"""Tests offline del puente tema_por_acta (sin red / sin API: clasificador inyectado).
Correr desde /tmp (protocolo de sync):  python test_tema_por_acta.py
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import tema_por_acta as T  # noqa: E402


def _fake(titulo):
    u = titulo.upper()
    if "PENAL" in u:
        return [("JUST.PENAL", 0.9), ("AUX.TRAMITE", 0.3)]
    if "IMPUESTO" in u:
        return [("ECON.TRIB", 0.85)]
    return [("AUX.SINCLASIF", 0.4)]


def _actas_df():
    return pd.DataFrame([
        {"acta_id": "x1", "expediente": "1-D-2020", "titulo": "REFORMA DEL CODIGO PENAL, ARTICULO 80"},
        {"acta_id": "x2", "expediente": "2-D-2020", "titulo": "MODIFICACION DEL IMPUESTO A LAS GANANCIAS"},
        {"acta_id": "x2", "expediente": "2-D-2020", "titulo": "IMPUESTO (titulo corto)"},   # dup acta -> gana el largo
        {"acta_id": "x3", "expediente": "3-D-2020", "titulo": "HOMENAJE A UN VECINO ILUSTRE"},
        {"acta_id": "x4", "expediente": None, "titulo": "  "},                              # sin titulo -> se cae
    ])


def test_cargar_actas_dedup_y_filtro():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "acta_expediente.parquet"
        _actas_df().to_parquet(p, index=False)
        out = T.cargar_actas(p)
        assert set(out["acta_id"]) == {"x1", "x2", "x3"}, out["acta_id"].tolist()
        # x2 quedó con el título largo
        assert "GANANCIAS" in out.set_index("acta_id").loc["x2", "titulo"]
        print("OK cargar_actas: dedup por acta_id (título más largo) + filtra vacíos")


def test_clasificar_primaria_salta_aux():
    actas = T.cargar_actas.__wrapped__ if hasattr(T.cargar_actas, "__wrapped__") else None
    df = pd.DataFrame([
        {"acta_id": "x1", "expediente": "1", "titulo": "CODIGO PENAL"},
        {"acta_id": "x2", "expediente": "2", "titulo": "IMPUESTO GANANCIAS"},
    ])
    res = T.clasificar_actas(df, clasificar=_fake)
    m = res.set_index("acta_id")
    assert m.loc["x1", "tema_id"] == "JUST.PENAL"      # saltó AUX.TRAMITE
    assert m.loc["x1", "tema_area"] == "JUST"
    assert m.loc["x2", "tema_area"] == "ECON"
    assert "JUST.PENAL;AUX.TRAMITE" == m.loc["x1", "todas_ids"]
    print("OK clasificar: primaria = mayor confianza NO auxiliar; guarda todas")


def test_idempotencia():
    df = pd.DataFrame([{"acta_id": "x1", "expediente": "1", "titulo": "CODIGO PENAL"}])
    r1 = T.clasificar_actas(df, clasificar=_fake)
    r2 = T.clasificar_actas(df, clasificar=_fake, previas=r1)
    assert len(r2) == len(r1) == 1, "no debe reclasificar lo ya resuelto"
    print("OK idempotencia contra previas")


def test_resiliencia_una_fila_rota():
    df = pd.DataFrame([
        {"acta_id": "x1", "expediente": "1", "titulo": "CODIGO PENAL"},
        {"acta_id": "x2", "expediente": "2", "titulo": "IMPUESTO"},
    ])

    def rompe(t):
        if "IMPUESTO" in t.upper():
            raise RuntimeError("LLM cayó")
        return _fake(t)

    res = T.clasificar_actas(df, clasificar=rompe)
    assert set(res["acta_id"]) == {"x1"}, "la fila rota se saltea, el lote sigue"
    print("OK resiliencia: una fila rota no corta el lote")


if __name__ == "__main__":
    test_cargar_actas_dedup_y_filtro()
    test_clasificar_primaria_salta_aux()
    test_idempotencia()
    test_resiliencia_una_fila_rota()
    print("\n== 4 chequeos tema_por_acta OK ==")
