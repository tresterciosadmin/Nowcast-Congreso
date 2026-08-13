"""modelo/ensemble - BACKTEST DE LA CADENA COMPLETA (opcion B, 2026-08-13).

Mide la calibracion del nowcast END-TO-END contra la realidad:

    P(aprobacion) = P(llega al recinto)  x  P(mayoria | recinto)
                    \\_____ embudo _____/    \\__ agregador + roster nominal __/

sobre la cohorte etiquetada y MADURA del embudo, y la compara con `sancionado`
(el proyecto termino siendo ley, si/no). La pregunta que responde: **la maquinaria
de roster nominal + agregador, encima del embudo, mejora la prediccion de sancion
o no aporta sobre el `p_sancion` que el embudo ya calcula solo?**

QUE CONSUME (contratos publicos de otros modulos; NO reimplementa su logica):
  - `variables/embudo`  -> `construir_cohorte` + `cohorte_madura` (la cohorte con el
    label `sancionado`, la `fecha_publicacion` = fecha point-in-time, y `camara_origen`)
    y `_metricas` (misma definicion de Brier/AUC/calibracion que usa el embudo).
  - `variables/embudo/outputs/p_embudo.parquet` -> `p_llega_recinto` (factor 1) y
    `p_sancion` (la BASELINE: el end-to-end propio del embudo).
  - `modelo/ensemble.nowcast_auto` -> el factor 2, `p_mayoria_recinto`, con la postura
    de bloque PROYECTADA point-in-time (variables/bloque) sobre el roster nominal de
    conducta (modelo/voto_individual, columnas de conducta desde el 2026-08-13).

POINT-IN-TIME. Cada proyecto se evalua a su `fecha_publicacion`: la postura de bloque
y el padron se proyectan walk-forward a esa fecha (no miran el futuro). El label
`sancionado` es honesto porque `cohorte_madura` deja solo proyectos con >= MADUREZ_ANIOS
de antiguedad (si iban a ser ley, ya lo serian).

MEMOIZACION. En v1 la postura NO se condiciona por tema/origen del proyecto, asi que
`p_mayoria_recinto` depende solo de (camara, mes) -> se calcula UNA vez por mes y se
reusa. Eso hace la corrida liviana. Condicionar por tema/origen (que vuelve p_mayoria
propia de cada proyecto) queda como el proximo refinamiento, anotado abajo.

4 directivas: errores especificos, parsing defensivo, logging estructurado.

Uso (la corrida pesada la corre Valle en PowerShell):
    python modelo\\ensemble\\src\\backtest_cadena.py --n-sims 2000
    python modelo\\ensemble\\src\\backtest_cadena.py --desde 2016 --hasta 2024 --camara Diputados
    python modelo\\ensemble\\src\\backtest_cadena.py --muestra 500 --seed 7   # smoke test rapido
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("backtest_cadena")

# Mapa de la camara de origen del embudo (MAYUSCULAS) al formato del roster/agregador.
# OJO: en MINUSCULAS. La canonica guarda `camara` como 'diputados'/'senado' y
# `proyectar_postura` filtra por igualdad EXACTA; roster_nominal y el agregador tambien
# esperan minusculas. Pasar "Diputados" da "sin historia" (empty) en silencio.
_CAMARA = {"DIPUTADOS": "diputados", "SENADO": "senado"}

# v1 corre efectivamente sobre DIPUTADOS. El Senado historico no se puede rostear con
# el padron por defecto de nowcast_auto: `padron_senado.csv` solo trae los 72 vigentes
# (mandatos 2021+) y `padron_senado_historico.csv` arranca fin-2017 — y nowcast_auto no
# expone `padron_file` para apuntarlo. Ademas Diputados tiene el hueco 2020-2023 (pausado),
# que invalida la ventana de postura para proyectos presentados ~2020-2025. El harness
# SALTEA con aviso los (camara, mes) sin historia/roster; no inventa nada.


# --------------------------------------------------------------------------- #
# Imports de contratos publicos (no se toca el codigo de los otros modulos)    #
# --------------------------------------------------------------------------- #
def _root() -> Path:
    return Path(__file__).resolve().parents[2].parent  # .../Nowcast Congreso Argy


def _import_embudo():
    src = _root() / "variables" / "embudo" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        import embudo  # type: ignore
        return embudo
    except ImportError as e:  # pragma: no cover - entorno
        raise RuntimeError(f"no pude importar el modulo embudo desde {src}: {e}") from e


def _import_nowcast_auto():
    src = Path(__file__).resolve().parent
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from ensemble import nowcast_auto  # type: ignore
        return nowcast_auto
    except ImportError as e:  # pragma: no cover - entorno
        raise RuntimeError(f"no pude importar nowcast_auto desde {src}: {e}") from e


# --------------------------------------------------------------------------- #
# Cohorte etiquetada + factores del embudo                                     #
# --------------------------------------------------------------------------- #
def preparar_cohorte(embudo, p_embudo: pd.DataFrame,
                     desde: int | None = None, hasta: int | None = None,
                     camaras: set[str] | None = None,
                     fuente: str = "sqlite") -> pd.DataFrame:
    """Devuelve una fila por proyecto MADURO con: proyecto_id, fecha (point-in-time),
    camara, sancionado (0/1), p_llega y p_sancion_embudo (baseline)."""
    if fuente == "sqlite":
        db = _root() / "datos" / "proyectos" / "data" / "proyectos.db"
        dfs = embudo.cargar_sqlite(db)
    else:
        dfs = embudo.cargar(_root() / "datos" / "canonica" / "data" / "clean")

    c = embudo.cohorte_madura(embudo.construir_cohorte(dfs))
    if c.empty:
        raise RuntimeError("la cohorte madura del embudo salio vacia")

    c = c.copy()
    c["proyecto_id"] = c["proyecto_id"].astype(str)
    c["camara"] = c["camara_origen"].astype(str).str.strip().str.upper().map(_CAMARA)
    c["sancionado"] = c["sancionado"].astype(int)
    c["fecha"] = pd.to_datetime(c["fecha_publicacion"], errors="coerce")

    antes = len(c)
    c = c[c["camara"].notna() & c["fecha"].notna()]
    if len(c) < antes:
        logger.info("descartados %d proyectos sin camara/fecha usable", antes - len(c))
    if camaras:
        c = c[c["camara"].isin(camaras)]
    if desde is not None:
        c = c[c["anio"] >= desde]
    if hasta is not None:
        c = c[c["anio"] <= hasta]

    # factores del embudo (contrato p_embudo.parquet): p_llega y baseline p_sancion
    pe = p_embudo.copy()
    pe["proyecto_id"] = pe["proyecto_id"].astype(str)
    pe = pe.drop_duplicates("proyecto_id").set_index("proyecto_id")
    c["p_llega"] = c["proyecto_id"].map(pe["p_llega_recinto"]).astype(float)
    c["p_sancion_embudo"] = c["proyecto_id"].map(pe["p_sancion"]).astype(float)

    antes = len(c)
    c = c[c["p_llega"].notna()]
    if len(c) < antes:
        logger.info("descartados %d proyectos sin p_llega en p_embudo", antes - len(c))
    c["mes"] = c["fecha"].dt.strftime("%Y-%m")
    return c.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Factor 2 memoizado por (camara, mes) via nowcast_auto (contrato del ensemble) #
# --------------------------------------------------------------------------- #
def nowcast_mes_auto(nowcast_auto, camara: str, mes: str, *, n_sims: int,
                     tema=None, origen=None, p_embudo_path: Path) -> float:
    """P(mayoria | recinto) para (camara, mes), via nowcast_auto con p_llega=1.0.

    Reusa el ensemble tal cual: fija p_llega=1 para aislar el factor de mayoria y
    lee `p_mayoria_recinto`. La fecha es el dia 15 del mes (representativo)."""
    fecha = f"{mes}-15"
    nc = nowcast_auto("BACKTEST-MES", fecha, camara, "SIMPLE", p_embudo_path,
                      p_llega=1.0, n_sims=n_sims, tema=tema, origen=origen)
    return float(nc["p_mayoria_recinto"])


def construir_p_mayoria_por_mes(cohorte: pd.DataFrame, nowcast_mes_fn) -> dict:
    """Un p_mayoria por (camara, mes) unico. `nowcast_mes_fn(camara, mes)->float`
    es inyectable (los tests pasan una version sin datos)."""
    claves = cohorte[["camara", "mes"]].drop_duplicates().itertuples(index=False)
    out: dict[tuple[str, str], float] = {}
    fallidas = 0
    for camara, mes in claves:
        try:
            p = nowcast_mes_fn(camara, mes)
            if pd.isna(p):
                raise ValueError("p_mayoria NaN")
            out[(str(camara), str(mes))] = float(np.clip(p, 0.0, 1.0))
        except (ValueError, KeyError, RuntimeError, FileNotFoundError) as e:
            fallidas += 1
            logger.warning("sin p_mayoria para (%s, %s): %s", camara, mes, e)
    logger.info("p_mayoria calculado para %d meses-camara (%d fallidos)",
                len(out), fallidas)
    return out


# --------------------------------------------------------------------------- #
# Composicion + metricas                                                        #
# --------------------------------------------------------------------------- #
def componer_backtest(cohorte: pd.DataFrame, p_mayoria_map: dict) -> pd.DataFrame:
    """Agrega p_mayoria (por mes) y p_aprob = p_llega x p_mayoria. Descarta las
    filas sin p_mayoria (mes que no se pudo simular)."""
    c = cohorte.copy()
    c["p_mayoria"] = [p_mayoria_map.get((str(cam), str(mes)))
                      for cam, mes in zip(c["camara"], c["mes"])]
    antes = len(c)
    c = c[c["p_mayoria"].notna()].copy()
    if len(c) < antes:
        logger.info("descartadas %d filas sin p_mayoria de su mes", antes - len(c))
    c["p_aprob"] = (c["p_llega"].astype(float) * c["p_mayoria"].astype(float)).clip(0, 1)
    return c.reset_index(drop=True)


def skill_score(brier: float, brier_ref: float) -> float:
    """1 - BS/BS_ref. >0 = mejor que la referencia; 0 = igual; <0 = peor."""
    if brier_ref is None or brier_ref == 0 or pd.isna(brier_ref):
        return float("nan")
    return round(1.0 - brier / brier_ref, 4)


def resumen(embudo, c: pd.DataFrame) -> dict:
    """Metricas de la cadena vs las baselines, con la misma _metricas del embudo."""
    y = c["sancionado"].astype(int).to_numpy()
    base_rate = float(y.mean()) if len(y) else float("nan")

    m_cadena = embudo._metricas(y, c["p_aprob"].to_numpy())
    m_embudo = embudo._metricas(y, c["p_sancion_embudo"].to_numpy())
    # climatologia: predecir siempre la tasa base (referencia de skill honesta)
    brier_clima = float(((base_rate - y) ** 2).mean()) if len(y) else float("nan")

    return {
        "n_evaluados": int(len(c)),
        "tasa_base_sancion": round(base_rate, 4),
        "brier_climatologia": round(brier_clima, 5),
        "cadena": {
            "brier": m_cadena["brier"], "auc": m_cadena["auc"],
            "skill_vs_climatologia": skill_score(m_cadena["brier"], brier_clima),
            "skill_vs_embudo": skill_score(m_cadena["brier"], m_embudo["brier"]),
            "calibracion": m_cadena["calibracion"],
        },
        "baseline_embudo_p_sancion": {
            "brier": m_embudo["brier"], "auc": m_embudo["auc"],
            "skill_vs_climatologia": skill_score(m_embudo["brier"], brier_clima),
        },
        "nota": ("v1 con postura SIN condicionar por tema/origen: p_mayoria depende "
                 "solo de (camara, mes), asi que la discriminacion (AUC) de la cadena "
                 "la aporta casi toda el embudo; el agregador ajusta el NIVEL. "
                 "Condicionar por tema/origen es el proximo paso."),
    }


# --------------------------------------------------------------------------- #
# Orquestacion                                                                  #
# --------------------------------------------------------------------------- #
def correr(desde=None, hasta=None, camaras=None, n_sims=2000, muestra=None,
           seed=0, tema=None, origen=None, fuente="sqlite") -> tuple[pd.DataFrame, dict]:
    embudo = _import_embudo()
    nowcast_auto = _import_nowcast_auto()
    p_embudo_path = _root() / "variables" / "embudo" / "outputs" / "p_embudo.parquet"
    p_embudo = pd.read_parquet(p_embudo_path)

    c = preparar_cohorte(embudo, p_embudo, desde=desde, hasta=hasta,
                         camaras=camaras, fuente=fuente)
    if muestra and muestra < len(c):
        c = c.sample(n=muestra, random_state=seed).reset_index(drop=True)
        logger.info("muestra aleatoria de %d proyectos (seed=%d)", muestra, seed)

    def nowcast_mes_fn(camara, mes):
        return nowcast_mes_auto(nowcast_auto, camara, mes, n_sims=n_sims,
                                tema=tema, origen=origen, p_embudo_path=p_embudo_path)

    pmay = construir_p_mayoria_por_mes(c, nowcast_mes_fn)
    c = componer_backtest(c, pmay)
    res = resumen(embudo, c)
    return c, res


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Backtest de la cadena completa (ensemble).")
    ap.add_argument("--desde", type=int, default=None, help="anio minimo de presentacion")
    ap.add_argument("--hasta", type=int, default=None, help="anio maximo de presentacion")
    ap.add_argument("--camara", choices=["Diputados", "Senado"], default=None)
    ap.add_argument("--n-sims", type=int, default=2000)
    ap.add_argument("--muestra", type=int, default=None, help="submuestra aleatoria")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fuente", choices=["sqlite", "clean"], default="sqlite")
    ap.add_argument("--out", default=None, help="ruta del JSON resumen (default outputs/)")
    a = ap.parse_args(argv)

    camaras = {a.camara.lower()} if a.camara else None  # la cohorte usa minusculas
    detalle, res = correr(desde=a.desde, hasta=a.hasta, camaras=camaras,
                          n_sims=a.n_sims, muestra=a.muestra, seed=a.seed,
                          fuente=a.fuente)

    out = Path(a.out) if a.out else _root() / "modelo" / "ensemble" / "outputs" / "backtest_cadena.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    # el detalle por proyecto es regenerable y voluminoso -> Archivos_Borrar (y *.csv esta gitignored)
    det_dir = _root() / "Archivos_Borrar"
    det_dir.mkdir(parents=True, exist_ok=True)
    detalle.to_csv(det_dir / "backtest_cadena_detalle.csv", index=False, encoding="utf-8")

    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\nresumen -> {out}\ndetalle por proyecto -> {det_dir / 'backtest_cadena_detalle.csv'}")


if __name__ == "__main__":
    main(sys.argv[1:])
