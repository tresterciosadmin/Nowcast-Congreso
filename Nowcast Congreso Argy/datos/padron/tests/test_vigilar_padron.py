"""Tests offline del PADRÓN VIVO. No toca red ni el padrón real.

Lo que se protege acá, por orden de importancia:

1. **Que un pase sea un pase.** La primera corrida del vigilante reportó como
   cambio de bloque a Del Plá, que había pasado de "...TRABAJADORES-U" a
   "...TRABAJADORES-UNIDAD": el mismo bloque, truncado distinto por la fuente.
   Este proyecto ya pagó caro dos falsos positivos parecidos (los 123 asesores
   leídos como jefes de bloque, la falsa jefa que valía 610 proyectos). Un
   vigilante que grita en falso se termina ignorando, que es la única forma de
   que sea peor que no tenerlo.

2. **Que la alarma del total suene.** Es la alarma más barata del proyecto:
   257 y 72 son números que no se negocian.

3. **Que no avise dos veces lo mismo.** Si el aviso semanal repite lo de la
   semana pasada, deja de leerse.

Correr:  python datos/padron/tests/test_vigilar_padron.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import vigilar_padron as V  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def padron(filas):
    """filas: (clave, legislador, bloque_norm, bloque_linaje)"""
    return pd.DataFrame([
        {"clave": c, "legislador": n, "bloque_norm": b, "bloque_linaje": l,
         "distrito": "BUENOS AIRES", "desde": "2023-12-10", "hasta": "2027-12-09"}
        for c, n, b, l in filas])


def main():
    base = [("K1", "Perez, Ana", "LA LIBERTAD AVANZA", "LA LIBERTAD AVANZA"),
            ("K2", "Gomez, Luis", "UNION POR LA PATRIA", "FdT-UxP (kirchnerismo)"),
            ("K3", "Diaz, Sol", "PRO", "PRO")]

    # ---------- sin cambios ----------
    d = V.comparar(padron(base), padron(base))
    chk(not (d["altas"] or d["bajas"] or d["pases"]),
        "padrones identicos: no reporta nada")

    # ---------- alta y baja ----------
    nuevo = base[:2] + [("K4", "Ruiz, Juan", "PRO", "PRO")]
    d = V.comparar(padron(base), padron(nuevo))
    chk(len(d["altas"]) == 1 and d["altas"][0]["legislador"] == "Ruiz, Juan",
        "detecta el alta de quien asumio")
    chk(len(d["bajas"]) == 1 and d["bajas"][0]["legislador"] == "Diaz, Sol",
        "detecta la baja de quien dejo la banca")

    # ---------- PASE REAL: cambia el linaje ----------
    pase = [("K1", "Perez, Ana", "PRO", "PRO")] + base[1:]
    d = V.comparar(padron(base), padron(pase))
    chk(len(d["pases"]) == 1, "un cambio de linaje SI es un pase")
    chk(d["pases"][0]["de"] == "LA LIBERTAD AVANZA" and d["pases"][0]["a"] == "PRO",
        "el pase informa de donde a donde")

    # ---------- FALSO PASE: el caso Del Pla ----------
    truncado = [("K1", "Perez, Ana",
                 "LA LIBERTAD AVANZA-UNIDAD", "LA LIBERTAD AVANZA")] + base[1:]
    d = V.comparar(padron(base), padron(truncado))
    chk(not d["pases"],
        "mismo linaje con el texto truncado distinto NO es un pase (caso Del Pla)")
    chk(len(d["reetiquetados"]) == 1,
        "el re-etiquetado se informa aparte, como mantenimiento de la fuente")

    # ---------- vigentes: la ventana de mandato ----------
    p = padron(base)
    p.loc[0, "hasta"] = "2024-01-01"          # ya ceso
    chk(len(V._vigentes(p, "2026-08-04")) == 2,
        "quien termino su mandato no cuenta como banca vigente")
    p2 = padron(base)
    p2.loc[1, "desde"] = "2027-12-10"         # todavia no asumio
    chk(len(V._vigentes(p2, "2026-08-04")) == 2,
        "quien todavia no asumio tampoco cuenta")
    p3 = padron(base)
    p3.loc[2, "hasta"] = "no-es-fecha"
    chk(len(V._vigentes(p3, "2026-08-04")) == 2,
        "una fecha ilegible se descarta en vez de romper la corrida")

    # ---------- idempotencia ----------
    h1 = V.huella(V.comparar(padron(base), padron(nuevo)))
    h2 = V.huella(V.comparar(padron(base), padron(nuevo)))
    chk(h1 == h2, "la huella del mismo diff es estable (no re-avisa)")
    h3 = V.huella(V.comparar(padron(base), padron(pase)))
    chk(h1 != h3, "un diff distinto cambia la huella (si avisa)")

    # ---------- la alarma del total ----------
    chk(V.BANCAS["diputados"] == 257 and V.BANCAS["senado"] == 72,
        "las bancas esperadas son 257 y 72")
    chk(V.TOLERANCIA < 6,
        "la tolerancia es chica: 6 bancas de mas ya fue un bug real (383 sobre 257)")

    # ---------- el reporte se arma sin explotar ----------
    rep = {"camara": "diputados", "fecha": "2026-08-04", "alarmas": [], "novedades": True,
           "n_nomina": 257, "n_padron": 256, "esperado": 257, "origen": "api:test",
           "altas": [{"legislador": "Ruiz, Juan", "bloque": "PRO", "distrito": "BA"}],
           "bajas": [], "pases": [], "reetiquetados": [],
           "composicion": {"PRO": 257}}
    md = V.a_markdown([rep])
    chk("Ruiz, Juan" in md and "novedades" in md.lower(),
        "el markdown nombra al que asumio y marca que hay novedades")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
