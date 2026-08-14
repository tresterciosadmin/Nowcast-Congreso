"""Tests del filtro de designaciones/pliegos de actas_ley.py (fix 2026-08-13).
Offline, sin datos del repo. Ejercita los DOS backends de dtype para el faltante.
Correr:  python datos/expedientes/tests/test_actas_ley.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import actas_ley as A  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


# --- designaciones que SÍ deben excluirse (no son ley) -------------------- #
DESIGNACIONES = [
    "CONCEDER AUTORIZACION PARA DESEMPEÑAR FUNCIONES DE CONSULES HONORARIOS",
    "AUTORIZACION PARA DESEMPEÑAR SUS RESPECTIVOS CARGOS DE CONSULES Y VICECONSULES HONORARIOS",
    "PLIEGO DEL DOCTOR X PARA JUEZ DE LA CORTE",
    "SOLICITA ACUERDO PARA DESIGNAR EMBAJADOR EN LA REPUBLICA DE CHILE",
    "PRESTAR EL ACUERDO CONSTITUCIONAL PARA PROMOVER AL GRADO DE GENERAL",
]

# --- leyes REALES que NO deben excluirse (aunque mencionen fiscal/juez/etc) - #
LEYES = [
    "PRESUPUESTO GENERAL DE LA ADMINISTRACION NACIONAL PARA EL EJERCICIO FISCAL DEL AÑO 2026",
    "APROBACION DEL CONSENSO FISCAL SUSCRIPTO POR EL PODER EJECUTIVO NACIONAL",
    "MEDIDAS FISCALES PALIATIVAS Y RELEVANTES",
    "MODIFICACION DE LA LEY ORGANICA DEL MINISTERIO PUBLICO FISCAL - 27148",
    "APROBACION DEL PROTOCOLO DE ENMIENDA AL CONVENIO PARA EVITAR LA DOBLE IMPOSICION",
    "PERSONAL MILITAR - LEY 19101 -. MODIFICACION SOBRE BENEFICIO DEL ASCENSO",
    "DESAFUERO DEL DIPUTADO JULIO DE VIDO SOLICITADO POR EL JUEZ FEDERAL",
    "CREACION DE NUEVOS JUZGADOS FEDERALES DE PRIMERA INSTANCIA",
    # ley REAL sobre el PROCEDIMIENTO de designación (no un nombramiento): NO excluir.
    # Este caso se coló como falso positivo al ampliar el patrón; la auditoría lo cazó.
    "PROCEDIMIENTO PARA LA DESIGNACION DE JUECES SUBROGANTES DE PRIMERA INSTANCIA",
]


def test_designaciones_caen():
    for t in DESIGNACIONES:
        chk(A.es_designacion(t) is True, f"excluye designación: {t[:55]}...")


def test_leyes_quedan():
    for t in LEYES:
        chk(A.es_designacion(t) is False, f"conserva ley real: {t[:55]}...")


def test_faltantes_no_rompen():
    # None / NaN / pd.NA no deben romper ni contar como designación
    for v in (None, np.nan, pd.NA, float("nan")):
        chk(A.es_designacion(v) is False, f"faltante {v!r} -> False sin excepción")


def test_dos_backends_dtype():
    """El .map(es_designacion) sobre una columna 'titulo' con faltantes no debe
    romper en ninguno de los dos backends (el path del pd.NA de pyarrow)."""
    base = pd.DataFrame({"titulo": DESIGNACIONES[:2] + LEYES[:2] + [None]})
    esperado = [True, True, False, False, False]
    for backend in ("numpy_nullable", "pyarrow"):
        try:
            d = base.convert_dtypes(dtype_backend=backend)
        except Exception as e:
            print(f"  (backend {backend} no disponible: {e})")
            continue
        got = d["titulo"].map(A.es_designacion).tolist()
        chk(got == esperado, f"backend {backend}: máscara correcta con faltante")


if __name__ == "__main__":
    test_designaciones_caen()
    test_leyes_quedan()
    test_faltantes_no_rompen()
    test_dos_backends_dtype()
    print(f"\nOK: {OK} chequeos")
