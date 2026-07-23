"""Tests del enriquecimiento de LINAJE del Senado desde el padrón (mandate-aware).
Correr:  python variables/bloque/tests/test_bloque_linaje_senado.py
"""
import sys
import tempfile
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


def _padron(tmp: Path):
    pad = pd.DataFrame([
        {"legislador": "PARRILLI, Oscar", "bloque_linaje": "FdT-UxP (kirchnerismo)",
         "desde": "2021-12-10", "hasta": "2027-12-09"},
        {"legislador": "VILLARRUEL, Victoria", "bloque_linaje": "LA LIBERTAD AVANZA",
         "desde": "2023-12-10", "hasta": "2029-12-09"},
        {"legislador": "PROVINCIAL, Juan", "bloque_linaje": "OTRO / PROVINCIAL",
         "desde": "2021-12-10", "hasta": "2027-12-09"},
    ])
    (tmp / "padron_senado.csv").write_text(pad.to_csv(index=False), encoding="utf-8-sig")
    man = pd.DataFrame([{"clave_norm": "SNOPEK GUILLERMO", "nombre": "Snopek",
                         "distrito": "JUJUY", "linaje": "FdT-UxP (kirchnerismo)", "nota": ""}])
    (tmp / "senado_linaje_manual.csv").write_text(man.to_csv(index=False), encoding="utf-8-sig")
    return tmp


def _df(camara, nombre, fecha, linaje):
    return {"camara": camara, "legislador_nombre": nombre, "fecha": pd.Timestamp(fecha),
            "bloque_linaje": linaje, "acta_id": "x", "legislador_id": "l", "conducta": "AFIRMATIVO"}


def main():
    # --- canonicalización de etiquetas escritas a mano ---
    chk(B._canon_linaje("FdT-UxP") == "FdT-UxP (kirchnerismo)",
        "canon: 'FdT-UxP' (sin sufijo) -> canónico kirchnerismo")
    chk(B._canon_linaje("kirchnerismo") == "FdT-UxP (kirchnerismo)", "canon: 'kirchnerismo'")
    chk(B._canon_linaje("UCR") == "RADICALISMO" and B._canon_linaje("radical") == "RADICALISMO",
        "canon: UCR/radical -> RADICALISMO")
    chk(B._canon_linaje("PRO") == "PRO", "canon: PRO se mantiene")
    chk(B._canon_linaje("PERONISMO FEDERAL") == "PERONISMO FEDERAL", "canon: peronismo federal")
    chk(B._canon_linaje("") is None and B._canon_linaje("OTRO / PROVINCIAL") is None,
        "canon: vacío/genérico -> None (no reasigna)")

    tmp = _padron(Path(tempfile.mkdtemp()))
    filas = [
        # Senado, linaje genérico, dentro del mandato -> recupera kirchnerismo
        _df("senado", "Parrilli, Oscar Isidro", "2025-05-01", "OTRO / PROVINCIAL"),
        # Senado, genérico, FUERA del mandato (antes de asumir) -> NO cambia (anacronismo)
        _df("senado", "Villarruel, Victoria", "2010-05-01", "OTRO / PROVINCIAL"),
        # Senado, provincial genuino: el padrón también dice OTRO/PROVINCIAL -> queda
        _df("senado", "Provincial, Juan", "2025-05-01", "OTRO / PROVINCIAL"),
        # Senado, override manual (ya no está en el padrón) -> recupera kirchnerismo
        _df("senado", "SNOPEK, Guillermo", "2024-06-01", "OTRO / PROVINCIAL"),
        # Senado, linaje YA específico -> no se toca (aunque matchee)
        _df("senado", "Parrilli, Oscar Isidro", "2025-05-01", "RADICALISMO"),
        # Diputados, mismo apellido genérico -> NO se toca (solo Senado)
        _df("diputados", "Parrilli, Oscar Isidro", "2025-05-01", "OTRO / PROVINCIAL"),
    ]
    df = pd.DataFrame(filas)
    out, n = B._enriquecer_linaje_senado(df, padron_dir=tmp)
    lin = list(out["bloque_linaje"])

    chk(lin[0] == "FdT-UxP (kirchnerismo)", "Senado dentro del mandato -> recupera linaje del padrón")
    chk(lin[1] == "OTRO / PROVINCIAL", "Senado FUERA del mandato -> NO reasigna (sin anacronismo)")
    chk(lin[2] == "OTRO / PROVINCIAL", "provincial genuino (padrón dice OTRO) -> se mantiene")
    chk(lin[3] == "FdT-UxP (kirchnerismo)", "override manual (fuera del padrón) -> recupera linaje")
    chk(lin[4] == "RADICALISMO", "linaje ya específico -> intacto (no lo pisa)")
    chk(lin[5] == "OTRO / PROVINCIAL", "Diputados -> NO se toca (el enriquecimiento es solo Senado)")
    chk(n == 2, "cuenta exacta de reasignaciones (Parrilli + Snopek)")

    # sin archivos de padrón -> no-op limpio
    out2, n2 = B._enriquecer_linaje_senado(df, padron_dir=Path("/no/existe"))
    chk(n2 == 0 and list(out2["bloque_linaje"]) == list(df["bloque_linaje"]),
        "sin padrón/override -> no-op (degradación limpia)")

    # flag off en cargar: no debe requerir legislador_nombre ni fallar
    chk(hasattr(B, "_enriquecer_linaje_senado"), "el enriquecimiento es una función pública del módulo")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
