"""Proyección hipotética BICAMERAL de un proyecto de ley — por legislador + ICG.

Muestra, para un proyecto hipotético, la P(mayoría) en DIPUTADOS y en SENADORES
por separado, calculada LEGISLADOR POR LEGISLADOR (no por bloque), y con la
influencia del ICG aplicada individualmente (gamma según el desvío de cada uno).

UNIFICADO 2026-08-14 (Parte B): la postura de bloque sale de `proyectar_postura`
CONDICIONADA por el ORIGEN FINO del proyecto (EJECUTIVO / OFICIALISMO / ALIADOS /
OPOSICION), el mismo motor validado contra votos reales (acierto del voto 59%→76%).
Antes usaba `proyectar_lineas_alineacion`, que promedia TODAS las leyes del gobierno
y no distingue un proyecto del PE de uno de un aliado como PRO.

Piezas que integra (todas contratos ya existentes):
  - variables/bloque.proyectar_postura : P(afirmativo) de cada bloque CONDICIONADA
    por el origen del proyecto (`_share_afirm`), walk-forward, con shrinkage.
  - modelo/ensemble.roster_nominal : baja al ROSTER real de la cámara a la fecha
    (padrón histórico) y le pega a cada legislador su desvío individual.
  - variables/proyecto/modulador_icg : el ICG legislador por legislador.

Correr:  python casos/proyeccion_hipotetica_bicameral.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
for sub in ("variables/proyecto/src", "variables/bloque/src", "modelo/ensemble/src",
            "modelo/agregador_institucional/src"):
    sys.path.insert(0, str(RAIZ / sub))

from bloque import (cargar as cargar_bloque, proyectar_postura,  # noqa: E402
                    cargar_tema_por_acta)
from ensemble import roster_nominal                              # noqa: E402
import modulador_icg as icg                                      # noqa: E402

# ─────────── EL PROYECTO HIPOTÉTICO ───────────
ASUNTO = "Reforma del impuesto a las ganancias (iniciativa del Poder Ejecutivo)"
# ORIGEN FINO del proyecto: qué lo empuja. Define contra qué actas históricas se
# condiciona la postura de cada bloque. Valores: EJECUTIVO (mensaje del PE/JGM) |
# OFICIALISMO (partido de gobierno) | ALIADOS (PRO y otros) | OPOSICION.
ORIGEN = "EJECUTIVO"
# La fecha NO se clava a mano: se toma el mes MÁS NUEVO del ICG.
FECHA, ICG_ACTUAL = icg.ultimo_mes_icg()

# Incertidumbre irreducible: ninguna votación es 0%/100% segura (riesgo sistémico
# que la independencia entre legisladores no capta). Se reporta en [ε, 1-ε].
# 2026-08-22: se IMPORTA del contrato del modelo en vez de redefinirse acá. Había
# una copia propia con el mismo valor, y una copia es una divergencia esperando.
from ensemble import P_INCERTIDUMBRE  # noqa: E402

PADRON = {
    "diputados": RAIZ / "datos/padron/data/padron_diputados.csv",
    "senado": RAIZ / "datos/padron/data/padron_senado_historico.csv",
}
DISC = RAIZ / "modelo/voto_individual/outputs/disciplina_individual.csv"


def _clamp_conf(p: float) -> float:
    """Nunca 0%/100%: hay riesgo sistémico que el modelo no ve."""
    return float(np.clip(p, P_INCERTIDUMBRE, 1.0 - P_INCERTIDUMBRE))


def proyectar_camara(camara, votos, cond):
    # postura de bloque CONDICIONADA por el origen del proyecto (motor validado).
    # `_share_afirm` = P(el bloque vota AFIRMATIVO) en proyectos de ese origen.
    bloques = proyectar_postura(votos, FECHA, camara, origen=ORIGEN,
                                cond_por_acta=cond, padron_path=str(PADRON[camara]))
    share = {b["bloque"]: b["_share_afirm"] for b in bloques}
    _, _, det = roster_nominal(camara, FECHA, bloques,
                               padron_file=str(PADRON[camara]),
                               disciplina_path=str(DISC))
    filas = pd.DataFrame(det["filas"])          # una fila POR LEGISLADOR
    # P(acompaña) = share afirmativo condicionado de su bloque (ni 0 ni 1 exactos:
    # ni el más leal es un lock). El desvío individual queda para el clima (ICG).
    filas["p_acompana"] = (filas["bloque_linaje"].map(share).fillna(0.5)
                           .clip(0.02, 0.98))

    n = len(filas)
    umbral = n // 2 + 1                          # mayoría simple del cuerpo
    # baseline (sin clima)
    p_base = icg.p_mayoria(filas.assign(p_mod=filas["p_acompana"]), umbral, col="p_mod")
    # con ICG, legislador por legislador (s=+1: buen clima ayuda a un proyecto del
    # lado del gobierno; para uno OPOSITOR habría que invertir el signo).
    z_fondo, z_corto = icg.zetas_del_mes(FECHA)
    mod = icg.aplicar_individual(filas, s=1.0, z_fondo=z_fondo, z_corto=z_corto,
                                 encoger=False)
    p_icg = icg.p_mayoria(mod, umbral, col="p_mod")
    return {
        "camara": camara, "n": n, "umbral": umbral,
        "afirm_esperados": float(filas["p_acompana"].sum()),
        "p_base": _clamp_conf(p_base), "p_icg": _clamp_conf(p_icg),
        "bloques": bloques, "filas": mod,
    }


def main():
    """NEUTRALIZADO 2026-08-25 — era la TERCERA formulacion del numero.

    El 22-08 se decidio que la formulacion es UNA SOLA (ADR-0012) y se dio de baja la
    v1. Este archivo no entro en esa baja y siguio calculando con mecanismo propio.
    Auditado el 25-08 contra la cadena de puertas, tenia DOS de los siete errores que
    esa misma sesion habia corregido en los otros dos generadores:

      1. `umbral = n // 2 + 1` (linea 83). Eso es mayoria ABSOLUTA (129 en Diputados),
         no simple. El repo ya tiene la cuenta buena en
         `modelo/agregador_institucional/src/agregador.py::umbral_aprobacion`, con el
         empate arreglado por ADR-0013 — que este archivo nunca recibio.
      2. `p_acompana` = el share afirmativo del bloque, recortado a [0,02 · 0,98]. No
         compone `P = share*(1-d) + (1-share)*(d/2)`, que fue el arreglo que bajo a
         Kirchnerismo de 0,4% a 22,5% y explicaba que todo diera 99%. Tampoco separa
         DIRECCION de PRESENCIA: el que falta cuenta como que vota en contra (el caso
         Menem, que preside, vota el 1,3% de las veces y cuando vota acompana el 96%).

    Lo delator: el 22-08 alguien lo toco para importar `P_INCERTIDUMBRE` del contrato
    del modelo "porque una copia es una divergencia esperando" — y arreglo esa copia
    sin ver las otras dos. Es exactamente el fallo que esta tarea vino a buscar.

    No se borra porque el slider de ICG legislador-por-legislador no existe en
    `nowcast_puertas` y puede querer rehacerse ahi. Pero no puede seguir corriendo:
    produce un numero que alguien va a citar. Copia entera en
    `Archivos_Borrar/BORRAR_casos-proyeccion_hipotetica_bicameral.py`.
    """
    raise SystemExit(
        "proyeccion_hipotetica_bicameral.py esta NEUTRALIZADO (2026-08-25): era una "
        "tercera formulacion del numero, con el umbral de mayoria ABSOLUTA en vez de "
        "simple y sin componer el share del bloque con el desvio. Usa "
        "casos/nowcast_puertas_html.py, que corre la cadena de puertas. Ver el "
        "docstring de main, el ADR-0012 y el ADR-0014.")


def _main_original():
    votos = cargar_bloque()          # formato canónico (con `conducta`), el que espera proyectar_postura
    cond = cargar_tema_por_acta()    # tema + origen fusionados, para condicionar

    print("=" * 70)
    print(f"  PROYECCIÓN BICAMERAL — {ASUNTO}")
    print(f"  origen={ORIGEN} · fecha {FECHA} · ICG {ICG_ACTUAL} · clima en 2 horizontes (fondo 6m + sacudón 3m)")
    print("=" * 70)

    for camara in ("diputados", "senado"):
        r = proyectar_camara(camara, votos, cond)
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
