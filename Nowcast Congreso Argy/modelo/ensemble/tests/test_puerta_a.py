"""Tests offline de la Puerta A / C — el carácter observado del dictamen.

Sin red y sin datos del repo: los parquet de firmas se fabrican sintéticos en tmp.

Lo que vigilan, en orden de importancia:
  1. Que «sin dato» NO colapse a «sin dictamen». Son opuestos: uno dice que no hay
     dictamen, el otro que no miramos.
  2. Que la guarda POINT-IN-TIME no se pueda saltear. Incluye el caso que se me
     escapó al escribir el módulo: un dictamen SIN FECHA se colaba como observado,
     que es exactamente la fuga del futuro que la guarda debía impedir.
  3. Que el condicionante se apague por ENCOGIMIENTO y no por un `if`.

    python modelo/ensemble/tests/test_puerta_a.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from puerta_a import (  # noqa: E402
    COEF_POR_DEFECTO,
    ESTADOS,
    caracter_de,
    cargar_caracter,
    condicionar,
    delta_caracter,
    estimar_delta_caracter,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def fila(pid, camara="diputados", *, leida=True, firmante="leg:1", clase="unico",
         disidencia="none", linaje="LIN_A", dos_com=False, fecha="2015-06-01",
         sumario="1-D-2015", origen="ancla"):
    return {"proyecto_id": pid, "camara": camara, "parseo_ok": leida,
            "dictamen_clase": clase, "disidencia": disidencia,
            "bloque_linaje": linaje, "legislador_id": firmante,
            "dos_comisiones": dos_com, "od_publicacion": fecha,
            "origen_firmas": origen, "expedientes_sumario": sumario,
            "fecha_impresion": None}


def tabla_de(filas, resultados=None):
    """Escribe un parquet sintético y devuelve la tabla de carácter."""
    td = tempfile.mkdtemp()
    dip = Path(td) / "firmas.parquet"
    d = pd.DataFrame(filas)
    d["od_publicacion"] = pd.to_datetime(d["od_publicacion"], errors="coerce")
    d.to_parquet(dip, index=False)
    res = Path(td) / "resultados.parquet"
    pd.DataFrame(resultados or [{"proyecto_id": "P1", "cabecera": "cabecera"}]
                 ).to_parquet(res, index=False)
    sen = Path(td) / "no_existe.parquet"
    return cargar_caracter(firmas_dip=dip, firmas_sen=sen, resultados=res)


# ───────────── los tres estados ─────────────
print("los tres estados son tres")
check(set(ESTADOS) == {"con_caracter", "sin_dictamen", "sin_dato"},
      "ESTADOS declara exactamente los tres")

tab = tabla_de([fila("P1")])

r = caracter_de("P1", "diputados", tab, fecha_corte="2020-01-01")
check(r["estado"] == "con_caracter", f"dictamen leído con firmas -> con_caracter (dio {r['estado']})")
check(r["n_firmantes"] == 1, "cuenta el firmante")

# proyecto que NO está, VIEJO -> se puede afirmar la ausencia
r = caracter_de("PX", "diputados", tab, fecha_corte="2020-01-01",
                fecha_presentacion="2010-01-01")
check(r["estado"] == "sin_dictamen", f"proyecto viejo sin dictamen -> sin_dictamen (dio {r['estado']})")

# el MISMO proyecto, RECIENTE -> no se puede afirmar nada
r = caracter_de("PX", "diputados", tab, fecha_corte="2020-01-01",
                fecha_presentacion="2019-06-01")
check(r["estado"] == "sin_dato",
      f"dentro de la ventana viva NO se afirma la ausencia (dio {r['estado']})")
check("ventana viva" in r["motivo"], "y el motivo lo dice")

# sin fecha de presentación: la respuesta conservadora
r = caracter_de("PX", "diputados", tab, fecha_corte="2020-01-01")
check(r["estado"] == "sin_dato", "sin fecha de presentación no se afirma la ausencia")


# ───────────── point-in-time ─────────────
print("\npoint-in-time: no se mira el futuro")
r = caracter_de("P1", "diputados", tab, fecha_corte="2010-01-01",
                fecha_presentacion="2009-01-01")
check(r["estado"] != "con_caracter",
      f"un dictamen de 2015 NO se ve en un corte de 2010 (dio {r['estado']})")

# EL CASO QUE SE ME ESCAPÓ: dictamen sin fecha utilizable.
tab_sf = tabla_de([fila("PSF", fecha=None)])
r = caracter_de("PSF", "diputados", tab_sf, fecha_corte="2015-01-01",
                fecha_presentacion="2012-01-01")
check(r["estado"] == "sin_dato",
      f"dictamen SIN FECHA no se da por existente al corte (dio {r['estado']}) "
      "— con la guarda ingenua daba con_caracter: fuga del futuro")
check("sin fecha" in r["motivo"], "y el motivo nombra la falta de fecha")

# sin corte, en cambio, sí se puede leer el carácter (uso no point-in-time)
r = caracter_de("PSF", "diputados", tab_sf)
check(r["estado"] == "con_caracter", "sin fecha de corte no hay nada que filtrar")


# ───────────── OD leída pero sin nombres ─────────────
print("\nOD que no dejó firmas: sin_dato, no sin_dictamen")
tab_v = tabla_de([fila("PV", firmante="")])
r = caracter_de("PV", "diputados", tab_v, fecha_corte="2020-01-01",
                fecha_presentacion="2010-01-01")
check(r["estado"] == "sin_dato",
      f"hay OD pero no se leyeron firmas -> sin_dato (dio {r['estado']})")


# ───────────── acumulados ─────────────
print("\nacumulados: observados, pero MARCADOS")
tab_ac = tabla_de([fila("PA", sumario="1-D-2015;2-D-2015;3-D-2015"),
                   fila("PS", sumario="9-D-2015")])
ra = caracter_de("PA", "diputados", tab_ac, fecha_corte="2020-01-01")
rs = caracter_de("PS", "diputados", tab_ac, fecha_corte="2020-01-01")
check(ra["estado"] == "con_caracter" and ra["acumulado"] is True,
      "el acumulado se observa igual, y sale marcado")
check(ra["n_expedientes"] == 3, f"cuenta los expedientes de la OD (dio {ra['n_expedientes']})")
check(rs["acumulado"] is False, "una OD de un solo expediente NO es acumulado")


# ───────────── el condicionante ─────────────
print("\nel condicionante se apaga por ENCOGIMIENTO, no por un if")
for estado_falso in ({"estado": "sin_dato"}, {"estado": "sin_dictamen"}):
    d, fe = delta_caracter({**estado_falso, "hay_minoria": True, "n_linajes": 5},
                           {"minoria": 1.5, "por_linaje": 0.3})
    check(fe == 0.0, f"{estado_falso['estado']}: el factor de encogimiento es 0")
    check(condicionar(0.60, {**estado_falso}, {"minoria": 1.5})["p"] == 0.60,
          f"{estado_falso['estado']}: p queda EXACTAMENTE sin condicionar")

obs = {"estado": "con_caracter", "hay_minoria": True, "disidencia_parcial": False,
       "disidencia_total": False, "dos_comisiones": False, "n_linajes": 4}
d, fe = delta_caracter(obs, {"minoria": -0.8, "por_linaje": 0.0})
check(fe == 1.0 and d == -0.8, f"observado: el delta se aplica entero (dio {d}, {fe})")
check(condicionar(0.60, obs, {"minoria": -0.8})["p"] < 0.60,
      "un dictamen con minoría enfrentada baja la probabilidad si el coeficiente es negativo")
check(condicionar(0.60, obs, {"minoria": 0.8})["p"] > 0.60, "y la sube si es positivo")
for p in (0.01, 0.5, 0.99):
    q = condicionar(p, obs, {"minoria": 9.0})["p"]
    check(0.0 <= q <= 1.0, f"nunca se sale de [0,1] (p={p} dio {q})")

print("\nlos coeficientes por defecto dejan el límite NO condicionado")
check(all(v == 0.0 for v in COEF_POR_DEFECTO.values()),
      "COEF_POR_DEFECTO está todo en cero a propósito")
for p in (0.2, 0.5, 0.8):
    check(condicionar(p, obs)["p"] == p,
          f"con los coeficientes por defecto, condicionar es la identidad en p={p}")
check(condicionar(0.5, obs)["condicionado"] is False,
      "y la salida DICE que no condicionó (el cero no se disfraza de ajuste)")


# ───────────── el estimador es un hook honesto ─────────────
print("\nel estimador pendiente falla ruidoso y con el motivo")
try:
    estimar_delta_caracter()
    check(False, "estimar_delta_caracter debe levantar NotImplementedError")
except NotImplementedError as e:
    check("degenerada" in str(e), "y el mensaje dice POR QUÉ está pendiente")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
