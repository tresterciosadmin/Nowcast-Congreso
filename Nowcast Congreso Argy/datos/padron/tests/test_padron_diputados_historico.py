# -*- coding: utf-8 -*-
"""Tests de datos/padron/src/padron_diputados_historico.py — sin red y sin la canónica.

Los votos son sintéticos a propósito: lo que hay que fijar es la **lógica de
reconstrucción**, y con datos reales un test se rompe cada vez que la canónica se
regenera. La corrida sobre datos reales la controla `--verificar`.

Cada caso fija algo que ya salió mal:

- **El bloque que titila.** La primera versión cortaba un tramo cada vez que
  cambiaba el string del bloque, y salieron **50.036 filas** para ~3.200 bancas.
  El corte va por mes.
- **`hasta` antes que `desde`.** Ese mismo bug dejó 17.055 filas imposibles.
- **Estirar el borde de un reemplazo.** Si a quien asume en agosto se le da el
  mandato desde el 10 de diciembre anterior, se le inventa banca —y bloque— en
  meses en los que no la tenía. Es el error Bianchi con otra ropa.

    python datos/padron/tests/test_padron_diputados_historico.py
    python -m pytest datos/padron/tests/test_padron_diputados_historico.py -q
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from padron_diputados_historico import (  # noqa: E402
    MARGEN_DIAS,
    _modal,
    _tramos,
    duplicados_probables,
    periodos_legislativos,
)

INI = dt.date(2007, 12, 10)
FIN = dt.date(2009, 12, 9)


def _correr() -> int:
    fallos: list[str] = []
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    def tramos(pares, ini=INI, fin=FIN):
        """pares = [(fecha, bloque), ...] ya ordenados."""
        f = [p[0] for p in pares]
        b = [p[1] for p in pares]
        return _tramos(f, b, b, ["CABA"] * len(f), ["Perez, Juan"] * len(f), ini, fin)

    # ─────────────────── períodos ───────────────────
    print("períodos legislativos (10-dic de años impares)")
    ps = periodos_legislativos(2008, 2011)
    check(ps[0] == (dt.date(2007, 12, 10), dt.date(2009, 12, 9)),
          f"un año par arranca en el período que ya estaba abierto: {ps[0]}")
    check(all((b - a).days > 700 for a, b in ps), "cada período dura dos años")
    check(all(ps[i][1] < ps[i + 1][0] for i in range(len(ps) - 1)),
          "los períodos no se pisan entre sí")

    # ─────────────────── el bloque que titila ───────────────────
    print("un bloque que cambia de grafía NO parte el mandato")
    # mismo mes, tres grafías: el dominante gana y queda UN tramo
    t = tramos([(dt.date(2008, 5, 5), "FRENTE PARA LA VICTORIA"),
                (dt.date(2008, 5, 7), "FRENTE PARA LA VICTORIA"),
                (dt.date(2008, 5, 9), "FPV"),
                (dt.date(2008, 6, 3), "FRENTE PARA LA VICTORIA"),
                (dt.date(2008, 6, 5), "FRENTE PARA LA VICTORIA")])
    check(len(t) == 1, f"debería dar UN tramo, dio {len(t)}: {[x['bloque_norm'] for x in t]}")
    check(t[0]["bloque_norm"] == "FRENTE PARA LA VICTORIA", f"gana el dominante: {t[0]['bloque_norm']}")

    # un voto suelto con otra grafía en un mes entero tampoco corta
    t = tramos([(dt.date(2008, 5, 5), "UCR"), (dt.date(2008, 5, 7), "UCR"),
                (dt.date(2008, 5, 9), "U.C.R."), (dt.date(2008, 5, 20), "UCR")])
    check(len(t) == 1, f"un voto con otra grafía no parte nada, dio {len(t)}")

    # ─────────────────── un pase de bloque REAL sí parte ───────────────────
    print("un pase de bloque que dura meses SÍ parte el mandato")
    t = tramos([(dt.date(2008, 3, 5), "UCR"), (dt.date(2008, 4, 5), "UCR"),
                (dt.date(2008, 9, 5), "COALICION CIVICA"),
                (dt.date(2008, 10, 5), "COALICION CIVICA")])
    check(len(t) == 2, f"dos tramos, dio {len(t)}")
    if len(t) == 2:
        check(t[0]["bloque_norm"] == "UCR" and t[1]["bloque_norm"] == "COALICION CIVICA",
              "cada tramo con su bloque")
        check(t[0]["hasta"] < t[1]["desde"], "los tramos no se pisan")
        check(dt.date(2008, 4, 5) < t[1]["desde"] < dt.date(2008, 9, 5),
              f"el corte va entre el último voto de uno y el primero del otro: {t[1]['desde']}")

    # ─────────────────── invariantes que nunca se pueden romper ───────────────────
    print("invariantes de todo tramo")
    casos = [
        [(dt.date(2008, 3, 5), "A")],
        [(dt.date(2008, 3, 5), "A"), (dt.date(2008, 3, 6), "B"), (dt.date(2008, 3, 7), "A")],
        [(dt.date(m // 12 + 2008, m % 12 + 1, 5), "A" if m % 2 else "B") for m in range(20)],
    ]
    for k, caso in enumerate(casos):
        for x in tramos(caso):
            check(x["desde"] <= x["hasta"], f"caso {k}: hasta<desde ({x['desde']}..{x['hasta']})")
        ts = tramos(caso)
        check(all(ts[i]["hasta"] < ts[i + 1]["desde"] for i in range(len(ts) - 1)),
              f"caso {k}: tramos solapados")

    # ─────────────────── no inventarle banca a un reemplazo ───────────────────
    print("los bordes: quién estaba desde el principio y quién es reemplazo")
    t = tramos([(INI + dt.timedelta(days=MARGEN_DIAS - 10), "A"), (dt.date(2009, 5, 5), "A")])
    check(t[0]["desde"] == INI, "quien vota apenas arranca el período tiene mandato desde el inicio")
    check(t[0]["estirado_ini"] is True, "y queda marcado como estirado")

    tarde = tramos([(dt.date(2008, 8, 20), "A"), (dt.date(2008, 9, 20), "A")])
    check(tarde[0]["desde"] == dt.date(2008, 8, 20),
          f"un reemplazo arranca en su primer voto, no en el 10-dic: {tarde[0]['desde']}")
    check(tarde[0]["estirado_ini"] is False, "y NO queda marcado como estirado")
    check(tarde[0]["hasta"] == dt.date(2008, 9, 20),
          "y termina en su último voto si dejó de votar mucho antes del cierre")

    # ─────────────────── el modal ───────────────────
    print("el valor dominante ignora vacíos")
    check(_modal(["", "A", "A", "B"]) == "A", "gana el más frecuente")
    check(_modal(["", "", ""]) == "", "todo vacío devuelve vacío")
    check(_modal([]) == "", "lista vacía no explota")

    # ─────────────────── duplicados de entity resolution ───────────────────
    print("detección de duplicados de la canónica")
    import pandas as pd

    hist = pd.DataFrame([
        {"legislador_id": "leg:1", "legislador": "ACUÑA KUNZ, Juan",
         "clave": "ACUNA JUAN KUNZ", "desde": "2008-01-01", "hasta": "2009-01-01"},
        {"legislador_id": "leg:2", "legislador": "Acuña Kunz, Juan Erwin",
         "clave": "ACUNA ERWIN JUAN KUNZ", "desde": "2008-01-01", "hasta": "2009-01-01"},
        {"legislador_id": "leg:3", "legislador": "Perez, Ana",
         "clave": "ANA PEREZ", "desde": "2008-01-01", "hasta": "2009-01-01"},
        {"legislador_id": "leg:4", "legislador": "Gomez, Juan",
         "clave": "GOMEZ JUAN", "desde": "2008-01-01", "hasta": "2009-01-01"},
    ])
    pares = duplicados_probables(hist, dt.date(2008, 6, 1))
    check(len(pares) == 1, f"un solo par duplicado, dio {len(pares)}: {pares}")
    check(not any("Perez, Ana" in p or "Gomez, Juan" in p for p in pares),
          "dos personas distintas NO son un duplicado aunque compartan un nombre de pila")
    check(duplicados_probables(hist, dt.date(2010, 6, 1)) == [],
          "fuera de la ventana no hay nadie activo, así que no hay pares")

    print(f"\n{corridos - len(fallos)}/{corridos} OK")
    if fallos:
        print(f"\n{len(fallos)} FALLAS:")
        for f in fallos:
            print(f"  - {f}")
    return len(fallos)


def test_padron_diputados_historico() -> None:
    assert _correr() == 0


if __name__ == "__main__":
    sys.exit(1 if _correr() else 0)
