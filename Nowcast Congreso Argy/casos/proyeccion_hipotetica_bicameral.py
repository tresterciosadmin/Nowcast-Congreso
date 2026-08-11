"""Proyección hipotética BICAMERAL de un proyecto de ley — por legislador + ICG.

Muestra, para un proyecto hipotético, la P(mayoría) en DIPUTADOS y en SENADORES
por separado, calculada LEGISLADOR POR LEGISLADOR (no por bloque), y con la
influencia del ICG aplicada individualmente (gamma según el desvío de cada uno).

Piezas que integra (todas contratos ya existentes):
  - variables/proyecto/postura_gobierno.proyectar_lineas_alineacion : la LÍNEA de
    cada bloque por ALINEACIÓN CON EL GOBIERNO (resuelve polaridad + era).
  - modelo/ensemble.roster_nominal : baja la línea al ROSTER real de la cámara a
    la fecha (padrón histórico) y le pega a cada legislador su desvío individual.
  - modelo/agregador_institucional.simular_votacion : el recuento (baseline).
  - variables/proyecto/modulador_icg : el ICG legislador por legislador.

Correr:  python casos/proyeccion_hipotetica_bicameral.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
for sub in ("variables/proyecto/src", "modelo/ensemble/src",
            "modelo/agregador_institucional/src"):
    sys.path.insert(0, str(RAIZ / sub))

from postura_gobierno import proyectar_lineas_alineacion  # noqa: E402
from ensemble import roster_nominal                        # noqa: E402
from agregador import simular_votacion                     # noqa: E402
import modulador_icg as icg                                # noqa: E402

# ─────────── EL PROYECTO HIPOTÉTICO ───────────
ASUNTO = "Reforma del impuesto a las ganancias (iniciativa del Poder Ejecutivo)"
POSTURA_GOBIERNO = "AFIRMATIVO"   # es un proyecto DEL gobierno: el gobierno vota que sí
# La fecha NO se clava a mano: se toma el mes MÁS NUEVO del ICG, así la proyección
# no se queda en un mes viejo apenas UTDT publica el siguiente. Para proyectar a un
# mes puntual, reemplazar por FECHA = "AAAA-MM-01".
FECHA, ICG_ACTUAL = icg.ultimo_mes_icg()
# El ICG entra por sus DOS señales (fondo 6m + sacudón 3m), leídas del mes objetivo
# desde icg_contexto.parquet. Ya no hay perilla global del analista: la capa 2 se
# eliminó (doble conteo del mismo clima), ver ADR-0008 rev 2026-08-11.

PADRON = {
    "diputados": RAIZ / "datos/padron/data/padron_diputados.csv",
    "senado": RAIZ / "datos/padron/data/padron_senado_historico.csv",
}
DISC = RAIZ / "modelo/voto_individual/outputs/disciplina_individual.csv"


def _p_acompana(alineacion: float, postura_target: str) -> float:
    """P(un legislador vote AFIRMATIVO) = la ALINEACIÓN de su bloque con el
    gobierno, no un 1/0 según la línea. Un bloque de alineación 0,55 aporta ~55%
    de votos afirmativos, no ~100%. Para un proyecto del gobierno (postura
    AFIRMATIVO), p = alineación; para uno opositor, p = 1 − alineación."""
    a = float(min(max(alineacion, 0.02), 0.98))   # nunca 0/1 exactos
    return a if postura_target == "AFIRMATIVO" else 1.0 - a


def proyectar_camara(camara, votos, postura):
    lineas_bloque = proyectar_lineas_alineacion(votos, FECHA, camara, postura,
                                                POSTURA_GOBIERNO)
    alin = {b["bloque"]: b["alineacion"] for b in lineas_bloque}
    _, _, det = roster_nominal(camara, FECHA, lineas_bloque,
                               padron_file=str(PADRON[camara]),
                               disciplina_path=str(DISC))
    filas = pd.DataFrame(det["filas"])          # una fila POR LEGISLADOR
    # la magnitud (alineación del bloque) manda; el desvío individual queda para
    # la sensibilidad al clima (gamma del ICG), no para el signo.
    filas["p_acompana"] = filas["bloque_linaje"].map(alin).fillna(0.5).map(
        lambda a: _p_acompana(a, POSTURA_GOBIERNO))

    n = len(filas)
    umbral = n // 2 + 1                          # mayoría simple del cuerpo
    # baseline (sin clima)
    p_base = icg.p_mayoria(filas.assign(p_mod=filas["p_acompana"]), umbral, col="p_mod")
    # con ICG, legislador por legislador (s=+1: buen clima ayuda al proyecto del gobierno).
    # Las dos señales del clima (fondo 6m + sacudón 3m) salen del mes objetivo.
    z_fondo, z_corto = icg.zetas_del_mes(FECHA)
    mod = icg.aplicar_individual(filas, s=1.0, z_fondo=z_fondo, z_corto=z_corto,
                                 encoger=False)
    p_icg = icg.p_mayoria(mod, umbral, col="p_mod")
    return {
        "camara": camara, "n": n, "umbral": umbral,
        "afirm_esperados": float(filas["p_acompana"].sum()),
        "p_base": p_base, "p_icg": p_icg,
        "lineas_bloque": lineas_bloque, "filas": mod,
    }


def main():
    votos = pd.read_parquet(RAIZ / "datos/canonica/data/clean/votos_resuelto.parquet")
    act = pd.read_parquet(RAIZ / "datos/canonica/data/clean/actas_canonico.parquet")[
        ["acta_id", "camara", "fecha"]]
    for c in ("fecha", "camara"):
        if c in votos.columns:
            votos = votos.drop(columns=c)
    votos = votos.merge(act, on="acta_id", how="left")
    votos["fecha"] = pd.to_datetime(votos["fecha"], errors="coerce")
    postura = pd.read_parquet(RAIZ / "variables/proyecto/data/postura_gobierno_por_acta.parquet")

    print("=" * 70)
    print(f"  PROYECCIÓN BICAMERAL — {ASUNTO}")
    print(f"  fecha {FECHA} · ICG {ICG_ACTUAL} · clima medido en 2 horizontes (fondo 6m + sacudón 3m)")
    print("=" * 70)

    for camara in ("diputados", "senado"):
        r = proyectar_camara(camara, votos, postura)
        print(f"\n### {camara.upper()}  ({r['n']} bancas, mayoría {r['umbral']})")
        print(f"  votos afirmativos esperados: {r['afirm_esperados']:.0f} / {r['n']}")
        print(f"  P(aprobación) SIN clima : {100*r['p_base']:5.1f}%")
        print(f"  P(aprobación) CON ICG   : {100*r['p_icg']:5.1f}%   (Δ {100*(r['p_icg']-r['p_base']):+.1f} pts)")
        # las bisagras: mayor movimiento por el clima
        f = r["filas"].copy()
        f["mov"] = (f["p_mod"] - f["p_acompana"]).abs()
        top = f.nlargest(5, "mov")[["legislador", "bloque_linaje", "linea", "desvio", "p_acompana", "p_mod"]]
        print("  legisladores que MÁS mueve el clima (las bisagras):")
        for _, x in top.iterrows():
            print(f"    {str(x['legislador'])[:26]:26} {x['bloque_linaje'][:18]:18} "
                  f"{x['linea']:11} desv={x['desvio']:.2f}  p:{x['p_acompana']:.2f}->{x['p_mod']:.2f}")


if __name__ == "__main__":
    main()
