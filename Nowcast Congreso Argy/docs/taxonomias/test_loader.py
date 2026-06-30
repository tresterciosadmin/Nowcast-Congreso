"""Test del loader/validador de taxonomías. Sin red.
Corre: `python test_loader.py` (desde docs/taxonomias/).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loader  # noqa: E402


def _ok(cond, msg):
    print(("PASS" if cond else "FAIL"), "-", msg)
    assert cond, msg


def run():
    tx = loader.cargar()
    ids = loader.ids_validos(tx)
    _ok(len(ids) > 50, f"hay más de 50 ids ({len(ids)})")
    _ok("SALUD.ADICC" in ids and "CYT.IA" in ids and "AUX.SINCLASIF" in ids,
        "ids esperados presentes (ludopatía, IA, sin clasificar)")
    _ok(loader.validar(tx) == [], "el JSON real valida sin problemas")

    # detecta duplicados
    malo = {"areas": [{"id": "X", "subtemas": [
        {"id": "X.A", "nombre": "a"}, {"id": "X.A", "nombre": "a2"}]}], "auxiliares": []}
    probs = loader.validar(malo)
    _ok(any("DUPLICADO" in p for p in probs), "detecta id duplicado")

    # detecta prefijo de área mal puesto
    malo2 = {"areas": [{"id": "X", "subtemas": [{"id": "Y.A", "nombre": "a"}]}], "auxiliares": []}
    _ok(any("prefijo" in p for p in loader.validar(malo2)), "detecta prefijo de área inconsistente")

    prompt = loader.lista_para_prompt(tx)
    _ok("SALUD.ADICC=" in prompt and "[AUX]" in prompt, "el prompt lista ids y auxiliares")
    print("\nTODOS LOS TESTS PASARON")


if __name__ == "__main__":
    run()
