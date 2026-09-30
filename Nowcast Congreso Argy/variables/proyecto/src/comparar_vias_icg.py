"""comparar_vias_icg.py — SUPERSEDED / NEUTRALIZADO 2026-08-11.

⛔ Este comparador contrastaba el MECANISMO 1 (individual, medido) contra el
MECANISMO 2 (nivel declarado por el analista = capa 2 global). El 2026-08-11
Valle DECIDIÓ ELIMINAR la capa 2 (doble conteo del mismo clima), así que la
comparación ya no tiene sentido y `modulador_icg.aplicar_dos_capas` fue removido:
este script NO corre más (levantaría AttributeError). Se conserva sólo como
registro histórico. La copia con la capa 2 NO está en Archivos_Borrar (esa carpeta
no viaja por git y se vació): se recupera del historial, en el último commit antes
de neutralizarlo:
    git show 0a798bb:"Nowcast Congreso Argy/variables/proyecto/src/comparar_vias_icg.py"
El `__main__` está neutralizado. Ver ADR-0008 (rev 2026-08-11) y ESTADO 2026-08-11.

2026-09-30 (auditoría, A6, decisión 1): se le SACÓ la salida HTML (`SALIDA`, `CSS` y `html()`, ~170 líneas de
plantilla del COMPARADOR-ICG.html). Se conserva el resto (los escenarios, `camara`, `_calibrar`, `base_escenario`,
`correr`) porque es lo único que documenta cómo se comparaban las vías del ICG, que vuelve en el ítem D6.
La versión con el HTML se recupera con `git log -- variables/proyecto/src/comparar_vias_icg.py`.

--- diseño original (histórico) --------------------------------------------
Reescrito de cero el 2026-08-04 con el diseño final acordado con Valle:

  MECANISMO 1 — VARIACION (medido, individual).
    El ICG del mes contra el promedio del propio gobierno, aplicado legislador
    por legislador segun cuan discolo sea. Es lo que se estimo: gamma sube
    0,22 -> 0,33 -> 0,35 -> 0,56 con el desvio, con dosis-respuesta.

  MECANISMO 2 — NIVEL (declarado, agregado).
    El ICG del mes contra la CURVA DEL CICLO: lo que un gobierno suele tener a
    esa altura del mandato. Un 2,0 en el mes 3 es malo; el mismo 2,0 en el mes
    30 es bueno. La intensidad la declara el analista.

Los dos son independientes: uno mide el desvio DENTRO del gobierno, el otro el
nivel del gobierno contra la historia.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

_HERE = Path(__file__).resolve(); RAIZ = _HERE.parents[3]
sys.path.insert(0, str(_HERE.parent))
import modulador_icg as M

UMBRAL = 129
HOY = pd.Timestamp("2026-08-04")

GRUPOS = [("Muy díscolos", 0.40, 9.9, 0.555), ("Díscolos", 0.30, 0.40, 0.354),
          ("Moderados", 0.20, 0.30, 0.333), ("Poco móviles", 0.10, 0.20, 0.220),
          ("Núcleo duro", 0.00, 0.10, 0.0)]

# icg = ICG del mes · mes = mes de mandato del gobierno · prom = promedio del gobierno
ESC = [
 dict(t="Reforma laboral del Ejecutivo", tema="Trabajo", lado="GOBIERNO", votos=124,
      icg=2.62, mes=31, prom=2.34, nota="gobierno arriba de su promedio y del ciclo"),
 dict(t="Presupuesto del Ejecutivo", tema="Economía", lado="GOBIERNO", votos=133,
      icg=2.34, mes=31, prom=2.34, nota="en su promedio, apenas sobre el ciclo"),
 dict(t="Emergencia en discapacidad", tema="Salud", lado="OPOSICION", votos=131,
      icg=1.10, mes=45, prom=1.55, nota="gobierno en caída al final del mandato"),
 dict(t="Privatización de empresa pública", tema="Economía", lado="GOBIERNO", votos=118,
      icg=1.45, mes=28, prom=1.61, nota="gobierno debilitado en el valle del ciclo"),
 dict(t="Ficha limpia", tema="Justicia", lado="OPOSICION", votos=129,
      icg=1.90, mes=20, prom=1.74, nota="empate técnico: el clima define"),
 dict(t="Actualización de haberes jubilatorios", tema="Previsional", lado="OPOSICION", votos=136,
      icg=1.19, mes=38, prom=1.55, nota="desgaste fuerte"),
 dict(t="Ley de lobby", tema="Institucional", lado="GOBIERNO", votos=126,
      icg=2.97, mes=24, prom=2.21, nota="pico de confianza a mitad de mandato"),
 dict(t="Financiamiento universitario", tema="Educación", lado="OPOSICION", votos=140,
      icg=1.51, mes=12, prom=2.21, nota="caída temprana: mal contra el ciclo"),
 dict(t="Reforma del Código Penal", tema="Seguridad", lado="GOBIERNO", votos=120,
      icg=3.32, mes=9, prom=2.47, nota="luna de miel larga, máximo de la serie"),
 dict(t="Moratoria previsional", tema="Previsional", lado="OPOSICION", votos=127,
      icg=1.07, mes=36, prom=1.55, nota="piso histórico"),
 # --- los dos siguientes existen para EXPONER la diferencia entre las variantes
 #     del nivel: caen en la luna de miel, que es donde ciclo y fijo discrepan ---
 dict(t="Paquete de reformas del PE recién asumido", tema="Institucional", lado="GOBIERNO", votos=128,
      icg=2.00, mes=4, prom=2.00, nota="ARRANQUE FLOJO: 2,00 cuando lo normal recién asumido es 2,51"),
 dict(t="Derogación de decretos (oposición)", tema="Institucional", lado="OPOSICION", votos=130,
      icg=2.51, mes=4, prom=2.51, nota="LUNA DE MIEL TÍPICA: 2,51 es exactamente lo normal al mes 4"),
]


def camara():
    pad = pd.read_csv(RAIZ/"datos/padron/data/padron_diputados.csv", encoding="utf-8-sig")
    for c in ("desde","hasta"): pad[c] = pd.to_datetime(pad[c], errors="coerce")
    v = pad[(pad.desde<=HOY)&(pad.hasta>=HOY)].copy()
    d = pd.read_csv(RAIZ/"modelo/voto_individual/outputs/disciplina_individual.csv")
    d = d[d.n_votos>=50][["legislador_id","tasa_desvio_disputadas"]]
    v = v.merge(d, on="legislador_id", how="left")
    v["sin_historial"] = v.tasa_desvio_disputadas.isna()
    v["desvio"] = v.tasa_desvio_disputadas.fillna(0.0)
    return v


def _calibrar(p0, objetivo):
    lo, hi = -6.0, 6.0
    for _ in range(60):
        c = (lo+hi)/2; o = (p0/(1-p0))*np.exp(c)
        if (o/(1+o)).sum() < objetivo: lo = c
        else: hi = c
    o = (p0/(1-p0))*np.exp((lo+hi)/2)
    return np.clip(o/(1+o), 0.01, 0.99)


def base_escenario(v, lado, votos):
    ofi = v.bloque_linaje.isin({"LA LIBERTAD AVANZA"}); ali = v.bloque_linaje.isin({"PRO"})
    p = np.where(ofi, 0.97, np.where(ali, 0.85, 0.30)) if lado=="GOBIERNO" \
        else np.where(ofi, 0.12, np.where(ali, 0.28, 0.78))
    p = np.clip(p + (0.5-p)*np.clip(v.desvio.values*1.2, 0, 0.75), 0.02, 0.98)
    return _calibrar(p, votos)


def correr():
    v = camara(); out = []
    for e in ESC:
        s = 1.0 if e["lado"]=="GOBIERNO" else -1.0
        base = pd.DataFrame({"p_acompana": base_escenario(v, e["lado"], e["votos"]),
                             "desvio": v.desvio.values})
        log_rel = float(np.log(np.clip(e["icg"],1,4)/e["prom"]))
        r = M.aplicar_dos_capas(base, s, log_rel, e["icg"], e["mes"], UMBRAL, "moderado", "ciclo")
        rf = M.aplicar_dos_capas(base, s, log_rel, e["icg"], e["mes"], UMBRAL, "moderado", "fijo")
        out.append(dict(**e, log_rel=log_rel, log_ciclo=r["log_ciclo"], log_fijo=r["log_fijo"],
                        neutro=M.neutro_ciclo(e["mes"]), p0=r["p_base"],
                        p1=r["p_capa1"], p2=r["p_final"], p2f=rf["p_final"],
                        v0=r["votos_base"], v1=r["votos_capa1"], movidos=r["movidos"]))
    return pd.DataFrame(out), v


if __name__ == "__main__":
    raise SystemExit(
        "comparar_vias_icg.py NEUTRALIZADO (2026-08-11): la capa 2 global se "
        "eliminó y aplicar_dos_capas ya no existe. Este comparador no corre más. "
        "Ver ADR-0008 rev 2026-08-11.")
