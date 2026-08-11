"""Tests del ICG como contexto (offline, sin red).

Lo que se protege, por orden de importancia:

1. **Anti-leakage.** El neutro de cada gobierno se calcula sólo con los meses YA
   transcurridos. Si se colara el promedio completo de la presidencia, el modelo
   estaria mirando el futuro — y este proyecto ya tiene una urgencia abierta por
   sospecha de leakage en otra variable.
2. **Que la imputacion sea PLANA.** Decision explicita de Valle: en las ventanas
   de traspaso hay MAS votaciones peleadas (7,8% vs 4,3%), asi que el numero
   tiene que ser aburrido y no depender de la pendiente de los ultimos meses.
3. **Que el ICG de una transicion no se le aplique al gobierno equivocado.** En
   nov-2015 el indice califica a Macri, que todavia no asumio; usarlo para un
   proyecto que empuja el kirchnerismo invierte el signo del modulador.

Correr:  python variables/proyecto/tests/test_icg_contexto.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import icg_contexto as C  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def serie(desde="2010-01", n=48, valores=None):
    f = pd.period_range(desde, periods=n, freq="M").to_timestamp()
    icg = valores if valores is not None else np.linspace(2.0, 2.4, n)
    return pd.DataFrame({"fecha": f, "anio": f.year, "mes": f.month, "icg": icg})


def cal(fechas):
    return pd.DataFrame({"fecha": pd.to_datetime([x for x, _ in fechas]),
                         "tipo": [t for _, t in fechas], "detalle": ""})


def main():
    # ---------- ventanas ----------
    v = C.ventanas_transicion(cal([("2015-10-25", "presidencial"),
                                   ("2015-11-22", "balotaje"),
                                   ("2015-12-10", "asuncion")]))
    chk(len(v) == 1, "los hitos de un mismo recambio se fusionan en UNA ventana")
    chk(v[0][0] < pd.Timestamp("2015-10-25") and v[0][1] > pd.Timestamp("2015-12-10"),
        "la ventana cubre desde antes de la eleccion hasta despues de la asuncion")
    v2 = C.ventanas_transicion(cal([("2011-10-23", "presidencial"),
                                    ("2019-10-27", "presidencial")]))
    chk(len(v2) == 2, "recambios lejanos quedan como ventanas separadas")

    # ---------- imputacion PLANA ----------
    val = np.concatenate([np.linspace(1.0, 2.0, 24), np.full(24, 3.0)])  # salto brusco
    d = serie(n=48, valores=val)
    out = C.imputar_plano(d, [(pd.Timestamp("2012-01-01"), pd.Timestamp("2012-12-01"))])
    imp = out[out.imputado]
    chk(len(imp) > 0, "la ventana se imputa")
    chk(imp["icg"].nunique() == 1, "la imputacion es PLANA: un solo valor en toda la ventana")
    esperado = d[(d.fecha < "2012-01-01") & (d.fecha >= "2011-01-01")]["icg"].mean()
    chk(abs(imp["icg"].iloc[0] - esperado) < 1e-9,
        "el valor imputado es el promedio de los 12 meses previos, no la tendencia")
    chk((out.loc[out.imputado, "icg_obs"] != out.loc[out.imputado, "icg"]).any(),
        "se conserva el valor observado en icg_obs (no se pierde el dato)")
    chk(imp["icg"].iloc[0] < 3.0,
        "el salto de la luna de miel (3,0) NO entra en la ventana imputada")

    # ---------- sin historia previa: no se inventa ----------
    d2 = serie(desde="2001-11", n=12)
    out2 = C.imputar_plano(d2, [(pd.Timestamp("2001-11-01"), pd.Timestamp("2002-06-01"))])
    chk(not out2["imputado"].any(), "sin 12 meses previos NO se imputa nada")
    chk((out2["regimen"] == "sin_base").any(), "esos meses quedan marcados como sin_base")

    # ---------- ANTI-LEAKAGE del neutro ----------
    d3 = serie(desde="2016-01", n=40, valores=np.concatenate([np.full(20, 2.0), np.full(20, 3.0)]))
    r = C.construir(d3, cal([]))
    fila = r[(r.fecha == "2016-10-01")]
    chk(not fila.empty and abs(fila["icg_base_gob"].iloc[0] - 2.0) < 1e-6,
        "el neutro del mes 10 usa SOLO los meses anteriores (2,0), no el futuro (3,0)")
    chk(r["icg_base_gob"].iloc[:C.MIN_MESES_GOB].isna().all()
        or r["base_es_propia"].iloc[:C.MIN_MESES_GOB].eq(False).all(),
        "los primeros meses no tienen base propia y quedan marcados")
    idx = r.index[r.fecha == "2016-08-01"][0]
    chk(r.loc[idx, "icg_base_gob"] <= r.loc[idx, "icg"] + 1e-9,
        "el neutro nunca incorpora el valor del propio mes")

    # ---------- log_rel y recorte ----------
    chk(C.PISO == 1.0 and C.TECHO == 4.0, "el recorte es [1, 4] como definio Valle")
    d4 = serie(n=30, valores=np.full(30, 5.9))
    r4 = C.construir(d4, cal([]))
    chk((r4["icg_c"] <= C.TECHO).all(), "un ICG fuera de rango se recorta al techo")
    r5 = C.construir(serie(n=30, valores=np.full(30, 2.0)), cal([]))
    ap = r5[r5.log_rel.notna()]
    chk(abs(ap["log_rel"]).max() < 1e-9,
        "ICG constante -> log_rel = 0: un gobierno en su promedio no recibe ni castigo ni premio")

    # ---------- DOS CAPAS: fondo (6m) + corto (3m) ----------
    chk({"z_fondo", "z_corto"} <= set(r5.columns), "el contrato expone z_fondo y z_corto")
    apz = r5[r5.z_fondo.notna()]
    chk(abs(apz["z_fondo"]).max() < 1e-9 and abs(r5["z_corto"]).max() < 1e-9,
        "ICG constante -> z_fondo = z_corto = 0 (gobierno en su promedio, sin ruido)")
    # salto DENTRO de un gobierno: el corto reacciona antes que el fondo, y NO hay
    # leakage del futuro (los meses previos al salto siguen en cero)
    step = np.concatenate([np.full(20, 2.0), np.full(20, 3.0)])
    rs = C.construir(serie(desde="2016-01", n=40, valores=step), cal([])).reset_index(drop=True)
    antes = rs.loc[15]      # 5 meses antes del salto (idx 20)
    chk(abs(antes["z_corto"]) < 1e-9 and abs(antes["z_fondo"]) < 1e-9,
        "point-in-time: la suba futura NO afecta los meses previos (media móvil trailing)")
    despues = rs.loc[23]    # 3 meses después del salto
    chk(despues["z_corto"] > 0.02,
        "tras una suba reciente el sacudón de corto plazo se pone positivo")
    chk(despues["z_fondo"] > 0,
        "el humor de fondo también sube, pero con más retraso")

    # ---------- volatilidad ----------
    r6 = C.construir(serie(n=40, valores=np.full(40, 2.0)), cal([]))
    chk(r6["vol6"].dropna().max() < 1e-9, "serie planchada -> volatilidad cero (elasticidad colapsa)")
    ruido = 2.0 + np.tile([0.5, -0.5], 20)
    r7 = C.construir(serie(n=40, valores=ruido), cal([]))
    chk(r7["vol6"].dropna().mean() > 0.3, "serie agitada -> volatilidad alta")

    # ---------- apto_ajuste ----------
    chk("apto_ajuste" in r.columns and r["apto_ajuste"].dtype == bool,
        "el contrato marca que meses sirven para ESTIMAR gamma")
    r8 = C.construir(serie(n=60), cal([("2012-10-25", "presidencial"), ("2012-12-10", "asuncion")]))
    chk(not r8.loc[r8.imputado, "apto_ajuste"].any(),
        "los meses imputados NO se usan para ajustar (pero si se puede predecir en ellos)")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
