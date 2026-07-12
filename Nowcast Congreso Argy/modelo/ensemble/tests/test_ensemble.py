"""Tests offline de modelo/ensemble. Usan el agregador real (simular_votacion) pero
NINGÚN dato en disco: los escenarios son sintéticos y p_llega va como override.
Correr:  python modelo/ensemble/tests/test_ensemble.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ensemble as E  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def esc(linea_mayoria, bancas_si=200, bancas_no=57, p_llega=0.5):
    """Escenario Diputados simple: un bloque grande con la línea dada + un opositor."""
    return {
        "tipo_mayoria": "SIMPLE", "camara": "Diputados", "p_llega_recinto": p_llega,
        "bloques": [
            {"bloque": "A", "bancas": bancas_si, "linea": linea_mayoria, "desvio": 0.02},
            {"bloque": "B", "bancas": bancas_no, "linea": "NEGATIVO", "desvio": 0.02},
        ],
    }


def main():
    # --- componer ---
    chk(abs(E.componer(0.5, 0.4) - 0.20) < 1e-9, "componer = producto de los dos factores")
    chk(E.componer(1.0, 0.9) == 0.9, "componer con p_llega=1 devuelve p_mayoria")
    for bad in [(-0.1, 0.5), (0.5, 1.2)]:
        try:
            E.componer(*bad); chk(False, "componer rechaza fuera de [0,1]")
        except ValueError:
            chk(True, f"componer rechaza fuera de [0,1] {bad}")

    # --- expandir roster ---
    lin, dev = E._expandir_roster([{"bloque": "X", "bancas": 3, "linea": "AFIRMATIVO", "desvio": 0.1}])
    chk(len(lin) == 3 and len(dev) == 3, "expandir: bancas -> filas por legislador")
    chk(set(lin) == {"AFIRMATIVO"}, "expandir: propaga la línea del bloque")
    for bad in [{"bloque": "X", "bancas": 2, "linea": "SI"}, {"bloque": "Y", "bancas": 0, "linea": "AFIRMATIVO"}]:
        try:
            E._expandir_roster([bad]); chk(False, "expandir rechaza inválidos")
        except ValueError:
            chk(True, f"expandir rechaza inválido ({bad.get('linea')}/{bad.get('bancas')})")

    # --- nowcast: mayoría clara a favor vs. en contra ---
    dummy = Path("/no/existe")
    a_favor = E.nowcast_proyecto("P1", esc("AFIRMATIVO", p_llega=0.5), dummy)
    en_contra = E.nowcast_proyecto("P2", esc("NEGATIVO", p_llega=0.5), dummy)
    chk(a_favor["p_mayoria_recinto"] > 0.95, "escenario holgado a favor -> P(mayoría) ~1")
    chk(en_contra["p_mayoria_recinto"] < 0.05, "escenario en contra -> P(mayoría) ~0")

    # --- descomposición correcta: p_aprobacion = p_llega * p_mayoria ---
    chk(abs(a_favor["p_aprobacion"] - a_favor["p_llega_recinto"] * a_favor["p_mayoria_recinto"]) < 0.02,
        "p_aprobacion = p_llega × p_mayoría")
    chk(a_favor["p_aprobacion"] <= a_favor["p_llega_recinto"] + 1e-9,
        "el embudo es techo: P(aprobación) <= P(llega al recinto)")

    # --- monotonía en el embudo: más P(llega) -> más P(aprobación) ---
    bajo = E.nowcast_proyecto("P3", esc("AFIRMATIVO", p_llega=0.10), dummy)
    alto = E.nowcast_proyecto("P4", esc("AFIRMATIVO", p_llega=0.80), dummy)
    chk(alto["p_aprobacion"] > bajo["p_aprobacion"], "más P(llega) -> más P(aprobación)")

    # --- banda de votos presente y ordenada ---
    b = a_favor["afirmativos_banda_5_95"]
    chk(b[0] <= a_favor["afirmativos_medio"] <= b[1], "banda 5-95 contiene la media")

    # --- error claro si no hay p_llega por ningún lado ---
    try:
        E.nowcast_proyecto("PX", {"tipo_mayoria": "SIMPLE", "camara": "Diputados",
                                  "bloques": [{"bloque": "A", "bancas": 10, "linea": "AFIRMATIVO"}]}, dummy)
        chk(False, "sin p_llega debe fallar")
    except ValueError:
        chk(True, "falla claro si no hay p_llega (ni embudo ni escenario)")

    # --- demo end-to-end corre ---
    d = E._demo()
    chk(0 <= d["p_aprobacion"] <= 1 and d["p_aprobacion"] <= d["p_llega_recinto"] + 1e-9,
        "demo end-to-end produce tarjeta válida")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
