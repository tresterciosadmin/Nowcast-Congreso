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


def _import_p_voto_revisora():
    """Factor de la SEGUNDA cámara: reusa puerta_d.p_voto_revisora (Manera 1)."""
    src = Path(__file__).resolve().parent
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from puerta_d import p_voto_revisora  # type: ignore
        return p_voto_revisora
    except ImportError as e:  # pragma: no cover - entorno
        raise RuntimeError(f"no pude importar p_voto_revisora desde {src}: {e}") from e


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


def construir_nowcast_mes_hoisteado(*, n_sims: int, tema=None, origen=None,
                                    p_embudo_path: Path):
    """OPTIMIZACION: carga la canonica UNA sola vez (no una por mes) y devuelve el
    `nowcast_mes_fn(camara, mes)` que usa esos votos precargados. Reproduce EXACTO la
    cadena de `nowcast_auto` (proyectar_postura + roster_nominal + nowcast_proyecto con
    p_llega=1.0), pero evita ~130 recargas del millon de votos -> de minutos a segundos.
    Resultados identicos: compone las MISMAS funciones publicas, solo hoistea la carga."""
    src = Path(__file__).resolve().parent
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from ensemble import (_cargar_proyector, roster_nominal,  # type: ignore
                          nowcast_proyecto)
    cargar_bloque, proyectar_postura, cargar_tema_por_acta = _cargar_proyector()
    canon = _root() / "datos" / "canonica" / "data" / "clean"
    votos = cargar_bloque(canon)                       # <-- UNA sola vez
    cond = cargar_tema_por_acta() if (tema or origen) else None
    logger.info("canonica precargada una vez (%d filas); proyeccion por mes reusa esto",
                len(votos))

    def nowcast_mes_fn(camara: str, mes: str) -> float:
        fecha = f"{mes}-15"
        bloques = proyectar_postura(votos, fecha, camara, tema=tema, origen=origen,
                                    cond_por_acta=cond)
        lineas, desvios, _ = roster_nominal(camara, fecha, bloques)
        nc = nowcast_proyecto("BACKTEST-MES", lineas, desvios, "SIMPLE", camara,
                              p_embudo_path, p_llega=1.0, n_sims=n_sims)
        return float(nc["p_mayoria_recinto"])

    return nowcast_mes_fn


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
# Factor 3 (opcional) — SEGUNDA CAMARA (revisora), memoizado por (origen, mes)   #
# --------------------------------------------------------------------------- #
def nowcast_revisora_mes_auto(p_voto_revisora, camara_origen: str, mes: str, *,
                              n_sims: int) -> float:
    """P(mayoria en la camara REVISORA) para (origen, mes), via puerta_d (Manera 1,
    delta=0). La revisora la deriva puerta_d de `camara_origen`. Fecha = dia 15."""
    r = p_voto_revisora(camara_origen, f"{mes}-15", n_sims=n_sims)
    return float(r["p_aprobacion"])


def construir_p_revisora_por_mes(cohorte: pd.DataFrame, revisora_mes_fn) -> dict:
    """Un p_revisora por (camara_origen, mes) unico. `revisora_mes_fn(camara, mes)
    ->float` es inyectable (los tests pasan una version sin datos)."""
    claves = cohorte[["camara", "mes"]].drop_duplicates().itertuples(index=False)
    out: dict[tuple[str, str], float] = {}
    fallidas = 0
    for camara, mes in claves:
        try:
            p = revisora_mes_fn(camara, mes)
            if pd.isna(p):
                raise ValueError("p_revisora NaN")
            out[(str(camara), str(mes))] = float(np.clip(p, 0.0, 1.0))
        except (ValueError, KeyError, RuntimeError, FileNotFoundError) as e:
            fallidas += 1
            logger.warning("sin p_revisora para (%s, %s): %s", camara, mes, e)
    logger.info("p_revisora (2a camara) para %d meses-origen (%d fallidos)",
                len(out), fallidas)
    return out


# --------------------------------------------------------------------------- #
# Factor 3 EMPIRICO — 2a camara como atenuacion (agenda/attrition, no voto)      #
# --------------------------------------------------------------------------- #
def factor_revisora_empirico(cohorte: pd.DataFrame, min_prev: int = 30) -> pd.Series:
    """Factor de 2a camara MEDIDO, no simulado: P(sancion | llego al recinto),
    estimado WALK-FORWARD (solo con proyectos de años ESTRICTAMENTE previos, para
    no espiar el futuro). Devuelve una Serie alineada a `cohorte` (NaN donde no hay
    suficiente historia previa, < min_prev casos).

    Por que empirico y no el voto simulado: de los que llegan al recinto, ~54%
    terminan en ley — o sea que la votacion de PISO casi siempre pasa (el simulador
    da ~1, y no se equivoca). El ~46% que se pierde es AGENDA/attrition en la 2a
    camara (que la traten, que no se modifique), que un simulador de recuento no ve.
    Este factor lo captura como tasa. Cubre toda la cohorte (no necesita el roster
    historico del Senado, a diferencia de la via mecanica --revisora-desde)."""
    c = cohorte.copy()
    lleg = c["llega_recinto"].astype(str).str.lower().isin(["true", "1", "verdadero"])
    c = c.assign(_lleg=lleg, _sanc=c["sancionado"].astype(int),
                 _anio=pd.to_numeric(c["anio"], errors="coerce").astype("Int64"))
    # tasa por año SOBRE los que llegaron al recinto, reindexada a TODOS los años de la
    # cohorte (asi un año sin recinto igual hereda el acumulado previo) y acumulada
    # walk-forward: el factor de un año usa SOLO años estrictamente anteriores.
    anios = sorted(a for a in c["_anio"].dropna().unique())
    por_anio = (c[c["_lleg"]].groupby("_anio")["_sanc"].agg(["sum", "count"])
                .reindex(anios, fill_value=0).sort_index())
    prev_sum = por_anio["sum"].cumsum().shift(1)
    prev_cnt = por_anio["count"].cumsum().shift(1)
    tasa_prev = (prev_sum / prev_cnt).where(prev_cnt >= min_prev)
    return c["_anio"].map(tasa_prev.to_dict()).astype(float)


# --------------------------------------------------------------------------- #
# Composicion + metricas                                                        #
# --------------------------------------------------------------------------- #
def componer_backtest(cohorte: pd.DataFrame, p_mayoria_map: dict,
                      p_revisora_map: dict | None = None) -> pd.DataFrame:
    """Agrega p_mayoria (por mes) y p_aprob. Sin `p_revisora_map`: la cadena de v1,
    p_aprob = p_llega x p_mayoria (cámara de origen). Con `p_revisora_map` (versión
    FINA): p_aprob = p_llega x p_mayoria_origen x p_mayoria_revisora — la segunda
    cámara simulada. Descarta las filas sin el factor de su mes."""
    c = cohorte.copy()
    c["p_mayoria"] = [p_mayoria_map.get((str(cam), str(mes)))
                      for cam, mes in zip(c["camara"], c["mes"])]
    antes = len(c)
    c = c[c["p_mayoria"].notna()].copy()
    if len(c) < antes:
        logger.info("descartadas %d filas sin p_mayoria de su mes", antes - len(c))
    p = c["p_llega"].astype(float) * c["p_mayoria"].astype(float)
    if p_revisora_map is not None:
        c["p_revisora"] = [p_revisora_map.get((str(cam), str(mes)))
                           for cam, mes in zip(c["camara"], c["mes"])]
        antes = len(c)
        c = c[c["p_revisora"].notna()].copy()
        if len(c) < antes:
            logger.info("descartadas %d filas sin p_revisora de su mes", antes - len(c))
        p = c["p_llega"].astype(float) * c["p_mayoria"].astype(float) * c["p_revisora"].astype(float)
    c["p_aprob"] = p.clip(0, 1)
    return c.reset_index(drop=True)


def skill_score(brier: float, brier_ref: float) -> float:
    """1 - BS/BS_ref. >0 = mejor que la referencia; 0 = igual; <0 = peor."""
    if brier_ref is None or brier_ref == 0 or pd.isna(brier_ref):
        return float("nan")
    return round(1.0 - brier / brier_ref, 4)


def resumen(embudo, c: pd.DataFrame, con_revisora: bool = False,
            empirico: bool = False) -> dict:
    """Metricas de la cadena vs las baselines, con la misma _metricas del embudo."""
    y = c["sancionado"].astype(int).to_numpy()
    base_rate = float(y.mean()) if len(y) else float("nan")

    m_cadena = embudo._metricas(y, c["p_aprob"].to_numpy())
    m_embudo = embudo._metricas(y, c["p_sancion_embudo"].to_numpy())
    # climatologia: predecir siempre la tasa base (referencia de skill honesta)
    brier_clima = float(((base_rate - y) ** 2).mean()) if len(y) else float("nan")

    if empirico:
        nota = ("cadena = p_llega x p_mayoria(origen) x k_revisora, donde k_revisora es la "
                "2a camara MEDIDA (walk-forward): P(sancion|llego al recinto) de años previos. "
                "Captura la atenuacion REAL (agenda/attrition en la revisora: ~54% de lo que "
                "llega al recinto se sanciona), que el voto simulado no ve porque la votacion "
                "de PISO casi siempre pasa. Cubre toda la cohorte. El voto de origen sigue sin "
                "condicionar por tema/origen (da p~1 y aporta poco): ese es el limite restante.")
    elif con_revisora:
        nota = ("version FINA (mecanica): cadena = p_llega x p_mayoria(origen) x p_mayoria(REVISORA), "
                "la segunda camara SIMULADA con puerta_d (Manera 1). OJO: el voto simulado de la "
                "revisora da ~1 (la votacion de piso casi siempre pasa), asi que NO captura la "
                "atenuacion real (que es agenda/attrition). Preferir --revisora-empirico.")
    else:
        nota = ("v1 con postura SIN condicionar por tema/origen y SIN segunda camara: "
                "p_mayoria depende solo de (camara, mes), asi que la discriminacion (AUC) "
                "la aporta casi toda el embudo y el agregador ajusta el NIVEL. Sumar la "
                "revisora (--revisora-desde) y condicionar por tema/origen son los pasos.")

    return {
        "n_evaluados": int(len(c)),
        "version": ("fina empirica (2a camara medida)" if empirico
                    else "fina mecanica (2a camara simulada)" if con_revisora
                    else "v1 (solo origen)"),
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
        "nota": nota,
    }


# --------------------------------------------------------------------------- #
# Orquestacion                                                                  #
# --------------------------------------------------------------------------- #
def correr(desde=None, hasta=None, camaras=None, n_sims=2000, muestra=None,
           seed=0, tema=None, origen=None, fuente="sqlite",
           revisora_desde=None, revisora_empirico=False) -> tuple[pd.DataFrame, dict]:
    embudo = _import_embudo()
    p_embudo_path = _root() / "variables" / "embudo" / "outputs" / "p_embudo.parquet"
    p_embudo = pd.read_parquet(p_embudo_path)

    # la version fina (2a camara) solo corre donde hay roster de la revisora -> 2018+
    if revisora_desde is not None:
        desde = max(desde, revisora_desde) if desde is not None else revisora_desde

    c = preparar_cohorte(embudo, p_embudo, desde=desde, hasta=hasta,
                         camaras=camaras, fuente=fuente)
    if muestra and muestra < len(c):
        c = c.sample(n=muestra, random_state=seed).reset_index(drop=True)
        logger.info("muestra aleatoria de %d proyectos (seed=%d)", muestra, seed)

    # OPTIMIZADO: la canonica se carga UNA vez (antes se recargaba por mes -> minutos).
    nowcast_mes_fn = construir_nowcast_mes_hoisteado(
        n_sims=n_sims, tema=tema, origen=origen, p_embudo_path=p_embudo_path)
    pmay = construir_p_mayoria_por_mes(c, nowcast_mes_fn)

    prev = None
    if revisora_desde is not None:
        p_voto_revisora = _import_p_voto_revisora()

        def revisora_mes_fn(camara, mes):
            return nowcast_revisora_mes_auto(p_voto_revisora, camara, mes, n_sims=n_sims)

        # solo pedimos revisora para los meses que sobrevivieron al factor de origen
        c_origen = componer_backtest(c, pmay)
        prev = construir_p_revisora_por_mes(c_origen, revisora_mes_fn)

    c = componer_backtest(c, pmay, p_revisora_map=prev)

    if revisora_empirico:
        # 2a camara MEDIDA (walk-forward), cubre toda la cohorte
        k = factor_revisora_empirico(c)
        antes = len(c)
        c = c.assign(k_revisora_emp=k)
        c = c[c["k_revisora_emp"].notna()].copy()
        if len(c) < antes:
            logger.info("descartadas %d filas sin historia previa para el factor empirico",
                        antes - len(c))
        c["p_aprob"] = (c["p_aprob"].astype(float) * c["k_revisora_emp"].astype(float)).clip(0, 1)

    res = resumen(embudo, c, con_revisora=(revisora_desde is not None) or revisora_empirico,
                  empirico=revisora_empirico)
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
    ap.add_argument("--revisora-desde", type=int, default=None,
                    help="2a camara SIMULADA (mecanica), desde este anio (necesita roster del "
                         "Senado historico; da p~1, no capta la atenuacion real). Preferir la empirica.")
    ap.add_argument("--revisora-empirico", action="store_true",
                    help="2a camara MEDIDA (walk-forward P(sancion|llego al recinto)); cubre toda "
                         "la cohorte y captura la atenuacion real. RECOMENDADA.")
    ap.add_argument("--out", default=None, help="ruta del JSON resumen (default outputs/)")
    a = ap.parse_args(argv)

    camaras = {a.camara.lower()} if a.camara else None  # la cohorte usa minusculas
    detalle, res = correr(desde=a.desde, hasta=a.hasta, camaras=camaras,
                          n_sims=a.n_sims, muestra=a.muestra, seed=a.seed,
                          fuente=a.fuente, revisora_desde=a.revisora_desde,
                          revisora_empirico=a.revisora_empirico)

    default_out = ("backtest_cadena_fina.json"
                   if (a.revisora_desde or a.revisora_empirico) else "backtest_cadena.json")
    out = Path(a.out) if a.out else _root() / "modelo" / "ensemble" / "outputs" / default_out
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
