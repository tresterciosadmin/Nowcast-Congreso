"""BASELINE del motor sobre la vara CORRECTA: el voto individual.

POR QUE ESTE Y NO `backtest_cadena.py`
--------------------------------------
`backtest_cadena` esta NEUTRALIZADO (22-08, ADR-0012) y su docstring explica el motivo:
medir contra `sancionado` mide contra algo que el motor por diseño no predice (el 69% de
los proyectos con dictamen que no llegan a ley se pierden en la AGENDA). Y
`backtest_agregador` (Brier 0,011, skill 0,76) mide contra "¿se aprobo el acta?", con
tasa base 95,15%: 4.542 de 4.890 actas caen en el bin superior. Un Brier lindo sobre una
variable casi constante no distingue un motor bueno de uno mediocre.

La vara con varianza real es **el voto de cada legislador**: ~20% de negativos, y es
exactamente el nivel donde la doctrina (ADR-0016) manda que entren todos los terminos
nuevos. Si delta, el shock comun o el sobre tablas mejoran algo, tienen que mejorar ESTO.

QUE MIDE
--------
Para cada acta con fecha y camara, reconstruye P_i tal como la calcula el motor HOY
(§I.4 de FORMULA-COMPLETA.md) y la contrasta con el voto REAL de cada persona:

    P_i = record_i                                    si n_i >= MIN_HIST (8)
        = s_l(1-d_i) + (1-s_l)(d_i/2)                 si no

Metricas: Brier, log-loss, accuracy y calibracion por decil sobre votos EMITIDOS
(afirmativo/negativo). Ademas el error del MARGEN por acta, que es lo que consume el
umbral.

ESTRATIFICA POR CARACTER DEL DICTAMEN, que es el punto: la diferencia de Brier entre
dictamen unico y disputado **es el techo de lo que delta puede recuperar**. Si el motor
ya predice igual de bien en los dos, delta no tiene nada que aportar.

WALK-FORWARD. La postura de cada bloque se proyecta con la ventana ANTERIOR a la fecha
del acta (`proyectar_postura`, contrato de variables/bloque; no se reimplementa). El
record individual se acumula con `shift(1)` sobre las actas ordenadas por fecha.

MEMOIZACION. La postura depende de (camara, mes, tema, origen) y no del acta puntual, asi
que se cachea por esa clave: sin eso la corrida completa no termina. Mismo truco que
usaba backtest_cadena v1, extendido con tema/origen porque ahora la direccion se
condiciona. El `record` individual NO se cachea: es por persona y por fecha.

NO TOCA EL REPO: solo lee. Escribe el resumen en outputs/.

Uso:
    python evaluacion/baseline/src/baseline_voto_individual.py --muestra 200   # smoke
    python evaluacion/baseline/src/baseline_voto_individual.py                 # completo
    python evaluacion/baseline/src/baseline_voto_individual.py --camara diputados
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("baseline_voto")

MIN_HIST_INDIVIDUAL = 1          # espejo de nowcast_puertas (era 8 hasta el 06-09)
VENTANA_DIAS = 730
K_SHRINK = 5.0

# GUARD DE ERA (URGENTE 9) — por defecto "off", que es como se venia midiendo.
#
# ATENCION, ESTO NO ES UN AGREGADO SINO UNA CORRECCION: este harness dice ser el
# "espejo exacto" del motor, y en el record NO LO ES. Medido el 06-09-2026:
#
#   este harness  ->  record = shift(1).expanding() sobre TODA la historia
#   el motor      ->  record = media sobre la ERA vigente (nowcast_puertas.ERA_FIJA)
#
# Comparados sobre los mismos 475 legisladores al 2026-06-01, la mediana de la
# diferencia es 0,004 pero la COLA es enorme: 12,2% difiere mas de 0,10 y el peor caso
# 0,73 (alguien con 0,93 de afirmativos historicos que en esta era vota 0,20). Son
# justo los que cambiaron de lado con el recambio, o sea los que deciden.
#
# Consecuencia: el "skill +0,024 desde 2023" del item 9 mide un modelo que no es el que
# corre. Por eso el guard entra ACA tambien y no solo en el motor.
#
#   "off"    lo de siempre (toda la historia, sin encoger)
#   "corte"  el record se reinicia en cada era
#   "shrink" corte + el record se encoge hacia el share de su linaje (Empirical-Bayes,
#            k=5, el mismo de `proyectar_postura`): encoger en vez de cortar
#
# DESDE EL 06-09 EL DEFAULT ES "shrink", porque es lo que hace el motor. Un harness que
# mide otra cosa que el motor es el bug que este mismo bloque documenta.
GUARD_ERA_MODOS = ("off", "corte", "shrink")
GUARD_ERA_DEFAULT = "shrink"


def _hallar_repo() -> Path:
    p = Path(__file__).resolve()
    for cand in [p, *p.parents]:
        if (cand / "coordinacion").is_dir() and (cand / "variables").is_dir():
            return cand
    raise FileNotFoundError("no encontre la raiz del repo (busco 'coordinacion/' y 'variables/')")


REPO = _hallar_repo()
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))


_VACIOS = {"", "NAN", "NONE", "DESCONOCIDO", "SIN DATO", "S/D"}


def _norm_cond(x):
    """Normaliza tema/origen a None cuando no hay dato.

    BUG 2026-09-03: se le pasaba `nan` y `'DESCONOCIDO'` tal cual a `proyectar_postura`,
    que entonces intentaba condicionar sobre una categoria inexistente, encontraba 0
    actas y caia a incondicional avisando por cada acta. Dos danios: ruido en el log, y
    —peor— la clave de memoizacion quedaba contaminada con `nan`, que no es igual a si
    mismo, asi que el cache podia no reusarse. Pasar None es lo mismo pero explicito.
    """
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    s = str(x).strip()
    return None if s.upper() in _VACIOS else s


class _ContadorAvisos(logging.Filter):
    """Cuenta los avisos de `bloque` en vez de imprimir uno por acta.

    Hay dos que son ESPERABLES y aparecen miles de veces: el padron oficial no cubre
    los anios viejos (cae a la ventana) y algunas actas no tienen tema/origen. Se
    silencian en pantalla y se reportan agregados en el JSON, que es donde sirven.
    """

    def __init__(self):
        super().__init__()
        self.tally: dict = {}

    def filter(self, record):
        msg = record.getMessage()
        if "padron" in msg and "sin bancas vigentes" in msg:
            self.tally["padron_cae_a_ventana"] = self.tally.get("padron_cae_a_ventana", 0) + 1
            return False
        if "condicionamiento" in msg and "0 actas en ventana" in msg:
            self.tally["sin_actas_condicionadas"] = self.tally.get("sin_actas_condicionadas", 0) + 1
            return False
        if "actas AUX" in msg:
            self.tally["excluyo_aux"] = self.tally.get("excluyo_aux", 0) + 1
            return False
        return True


def perfil(share_linaje: float, desvio: float, record=None, n_emitidos: int = 0,
           shrink: bool = False) -> float:
    """P(afirmativo | vota). Espejo de `perfil_legislador` de nowcast_puertas.

    `shrink` reproduce el encogimiento del motor (ADR-0018): el record se mezcla con el
    share de su linaje con Empirical-Bayes, k=5. El ancla es el MISMO objeto que usa la
    rama de bloque, no otro — que es lo que lo hace un espejo y no una aproximacion.
    """
    d = float(min(max(desvio, 0.0), 1.0))
    s = float(min(max(share_linaje, 0.0), 1.0))
    if record is not None and not pd.isna(record) and n_emitidos >= MIN_HIST_INDIVIDUAL:
        r = float(min(max(record, 0.0), 1.0))
        if shrink:
            n = float(max(n_emitidos, 0))
            return (n * r + K_SHRINK * s) / (n + K_SHRINK)
        return r
    return s * (1.0 - d) + (1.0 - s) * (d / 2.0)


def _metricas(p: np.ndarray, y: np.ndarray) -> dict:
    """Brier, log-loss, accuracy y skill contra la tasa base."""
    if len(p) == 0:
        return {}
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    base = y.mean()
    brier = float(((p - y) ** 2).mean())
    brier_base = float(((base - y) ** 2).mean())
    return {
        "n": int(len(y)),
        "tasa_base": round(float(base), 4),
        "brier": round(brier, 5),
        "brier_climatologia": round(brier_base, 5),
        "skill": round(1 - brier / brier_base, 4) if brier_base > 0 else None,
        "logloss": round(float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), 5),
        "accuracy": round(float(((p >= 0.5).astype(int) == y).mean()), 4),
    }


def _calibracion(p, y, bins: int = 10) -> list[dict]:
    d = pd.DataFrame({"p": p, "y": y})
    d["bin"] = np.clip((d.p * bins).astype(int), 0, bins - 1)
    g = d.groupby("bin").agg(n=("y", "size"), pred=("p", "mean"), real=("y", "mean"))
    return [{"bin": int(b), "n": int(r.n), "pred": round(float(r.pred), 4),
             "real": round(float(r.real), 4)} for b, r in g.iterrows()]


ENLACE_TODAS = "datos/expedientes/data/clean/acta_expediente_todas.parquet"
FIRMAS = ["datos/expedientes/data/clean/dictamenes_firmas.parquet",
          "datos/expedientes/data/clean/dictamenes_firmas_senado.parquet"]


def caracter_dictamen(repo: Path) -> pd.DataFrame:
    """(proyecto_id, camara) -> caracter del dictamen. Ver §II.3 de FORMULA-COMPLETA.

    **CAMBIO 04-09-2026 (ADR-0017).** Antes leia SOLO el parquet de Diputados y
    agregaba por `proyecto_id` a secas. Dos problemas: las 18.105 firmas del Senado
    no entraban nunca, y un proyecto bicameral mezclaba el caracter de las dos
    camaras. Lo que un senador lee cuando vota es el dictamen de SU camara.
    """
    partes = []
    for rel in FIRMAS:
        ruta = repo / rel
        if not ruta.exists():
            logger.warning("no encontre %s: esa camara queda sin caracter", ruta.name)
            continue
        partes.append(pd.read_parquet(ruta))
    if not partes:
        raise FileNotFoundError("no hay ningun parquet de firmas: corre "
                                "datos/expedientes/src/construir_firmas.py [--senado]")
    f = pd.concat(partes, ignore_index=True)
    g = (f.groupby(["proyecto_id", "camara"])["dictamen_clase"]
           .apply(lambda s: frozenset(x for x in s.dropna() if x)))

    def clasificar(c):
        # `desconocido` (parser_od, 04-09-2026) = no se encontro el rotulo del
        # dictamen. NO es "despacho unico": si es lo unico que hay, el proyecto
        # queda SIN caracter en esa camara y sale del corte.
        c = frozenset(x for x in c if x != "desconocido")
        if not c:
            return None
        if "minoria" in c and ("mayoria" in c or "unico" in c):
            return "DISPUTADO"
        if "minoria" in c:
            return "solo_minoria"
        if "mayoria" in c:
            return "mayoria"
        if "unico" in c:
            return "UNICO"
        return None

    return g.map(clasificar).dropna().rename("caracter").reset_index()


def mapa_acta_caracter(repo: Path) -> pd.DataFrame:
    """acta_id -> caracter del dictamen.

    Usa `acta_expediente_todas.parquet`, que trae `proyecto_id` y `camara` ya
    resueltos y cubre las DOS camaras (5.030 actas). La tabla vieja
    —`acta_expediente.parquet`, el volcado crudo de CKAN— es SOLO Diputados y
    obligaba a cruzar a mano por texto de expediente: con ella el Senado quedaba
    en cero actas con caracter. ADR-0017.
    """
    car = caracter_dictamen(repo)
    enlace = repo / ENLACE_TODAS
    if enlace.exists():
        ae = pd.read_parquet(enlace)
        ae = ae[ae["proyecto_id"].map(lambda x: str(x) if x is not None else "") != ""]
        ae = ae[["acta_id", "proyecto_id", "camara"]].merge(
            car, on=["proyecto_id", "camara"], how="left")
        return ae[["acta_id", "proyecto_id", "caracter"]].drop_duplicates("acta_id")

    # Fallback RUIDOSO a proposito: si se cae aca en silencio, el Senado da cero
    # y el resultado parece un hallazgo politico en vez de un archivo que falta.
    logger.error("falta %s (lo arma datos/expedientes/src/enlace_senado.py): caigo a "
                 "acta_expediente.parquet, que es SOLO DIPUTADOS", enlace.name)
    ae = pd.read_parquet(repo / "datos/expedientes/data/clean/acta_expediente.parquet")
    ex = pd.read_parquet(repo / "datos/expedientes/data/clean/expedientes.parquet")
    m = pd.concat([
        ex[["proyecto_id", "exp_diputados"]].rename(columns={"exp_diputados": "exp"}),
        ex[["proyecto_id", "exp_senado"]].rename(columns={"exp_senado": "exp"}),
    ]).dropna().drop_duplicates("exp")
    ae = ae.merge(m, left_on="expediente", right_on="exp", how="left")
    ae = ae.merge(car.drop_duplicates("proyecto_id")[["proyecto_id", "caracter"]],
                  on="proyecto_id", how="left")
    return ae[["acta_id", "proyecto_id", "caracter"]].drop_duplicates("acta_id")


def _eras_de(fechas: pd.Series) -> pd.Series:
    """Era de cada fecha. Delega en el motor —si el harness usara otro calendario que
    `nowcast_puertas`, volveria a medir un modelo distinto— pero resuelve UNA VEZ POR
    FECHA DISTINTA: hay ~2.800 fechas de sesion contra 1.016.058 filas, y el `.map` fila
    por fila tarda minutos.
    """
    sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
    from nowcast_puertas import era_de  # type: ignore
    mapa = {f: era_de(f) for f in pd.unique(fechas)}
    return fechas.map(mapa)


def correr(camara_filtro: str = "", muestra: int = 0, seed: int = 7,
           desde: str = "", guard_era: str = GUARD_ERA_DEFAULT) -> dict:
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta

    logger.info("cargando canonica...")
    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = None
    if cond is not None and len(cond):
        cond_map = cond.set_index(cond.columns[0]).to_dict("index")

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara_filtro:
        v = v[v["camara"] == camara_filtro]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")

    # record propio walk-forward: promedio de los votos ANTERIORES de esa persona.
    # Con guard, ese promedio se reinicia en cada era (ver GUARD_ERA_MODOS arriba).
    if guard_era not in GUARD_ERA_MODOS:
        raise ValueError(f"guard_era invalido: {guard_era!r} (esperaba {GUARD_ERA_MODOS})")
    if guard_era == "off":
        gp = v.groupby("legislador_id")["af"]
    else:
        v["_era"] = _eras_de(v["fecha"])
        gp = v.groupby(["legislador_id", "_era"])["af"]
    v["record"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_prev"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)
    # el encogimiento NO se hace aca: se hace en `perfil()`, contra el share proyectado
    # del linaje, que es exactamente donde y contra que lo hace el motor.
    encoger = guard_era == "shrink"

    actas = (v[["acta_id", "fecha", "camara"]].drop_duplicates("acta_id")
             .sort_values("fecha").reset_index(drop=True))
    # arranca despues de una ventana de historia
    piso = actas["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)
    if desde:
        piso = max(piso, pd.Timestamp(desde))
    actas = actas[actas["fecha"] >= piso]
    if muestra:
        actas = actas.sample(min(muestra, len(actas)), random_state=seed).sort_values("fecha")
    logger.info("actas a evaluar: %d", len(actas))

    # RENDIMIENTO. Dos cosas que hacian esto inviable sobre miles de actas:
    #  1. `v[v.acta_id == x]` escanea 800k filas por acta -> se pre-agrupa una vez.
    #  2. `proyectar_postura` recorre la ventana de 730 dias entera en cada llamada.
    #     La postura solo depende de (camara, mes, tema, origen), no del acta puntual
    #     -> se memoiza por esa clave. Es el mismo truco que usaba backtest_cadena v1,
    #     extendido con tema/origen porque ahora la direccion se condiciona.
    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cache: dict = {}

    filas, saltadas = [], 0
    for k, a in enumerate(actas.itertuples(), 1):
        if k % 250 == 0:
            logger.info("  %d/%d actas (cache=%d)", k, len(actas), len(cache))
        info = (cond_map or {}).get(str(a.acta_id), {})
        tema = _norm_cond(info.get("tema_area"))
        origen = _norm_cond(info.get("origen"))
        clave = (a.camara, a.fecha.year, a.fecha.month, tema, origen)
        if clave in cache:
            by_lin = cache[clave]
        else:
            try:
                post = proyectar_postura(
                    votos, a.fecha, a.camara, ventana_dias=VENTANA_DIAS,
                    tema=tema, origen=origen, cond_por_acta=cond, k_shrink=K_SHRINK)
            except (ValueError, KeyError) as e:
                cache[clave] = None
                saltadas += 1
                logger.debug("acta %s saltada: %s", a.acta_id, e)
                continue
            by_lin = {p["bloque"]: p for p in post}
            cache[clave] = by_lin
        if by_lin is None:
            saltadas += 1
            continue
        sub = por_acta.get(a.acta_id)
        if sub is None:
            continue
        for r in sub.itertuples():
            p = by_lin.get(str(r.bloque_linaje))
            if p is None:
                continue
            filas.append({
                "acta_id": a.acta_id, "fecha": a.fecha, "camara": a.camara,
                "legislador": r.legislador_id, "linaje": r.bloque_linaje,
                "p": perfil(p["_share_afirm"], p["desvio"], r.record, r.n_prev, encoger),
                "y": r.af,
                "fuente": ("record" if (not pd.isna(r.record)
                                        and r.n_prev >= MIN_HIST_INDIVIDUAL) else "bloque"),
            })

    d = pd.DataFrame(filas)
    if d.empty:
        raise RuntimeError("no se evaluo ningun voto; revisa filtros y contratos")

    car = mapa_acta_caracter(REPO)
    d = d.merge(car[["acta_id", "caracter"]], on="acta_id", how="left")

    res = {
        "n_actas_evaluadas": int(d.acta_id.nunique()),
        "n_actas_saltadas": int(saltadas),
        "avisos_agregados": dict(getattr(correr, "_tally", {})),
        "rango_fechas": [str(d.fecha.min().date()), str(d.fecha.max().date())],
        "ventana_dias": VENTANA_DIAS,
        "min_hist_individual": MIN_HIST_INDIVIDUAL,
        "guard_era": guard_era,
        "global": _metricas(d.p.values, d.y.values),
        "calibracion": _calibracion(d.p.values, d.y.values),
        "por_camara": {c: _metricas(g.p.values, g.y.values)
                       for c, g in d.groupby("camara")},
        "por_fuente_direccion": {c: _metricas(g.p.values, g.y.values)
                                 for c, g in d.groupby("fuente")},
        "por_caracter_dictamen": {str(c): _metricas(g.p.values, g.y.values)
                                  for c, g in d.groupby("caracter", dropna=False)},
        # ERA. Se corre la historia entera y se corta despues, para no tener que elegir
        # de antemano: si el motor se comporta distinto en la era reciente que en 2003,
        # eso mismo es un hallazgo. Los cortes son recambios de mandato (10-dic).
        "por_era": {e: _metricas(g.p.values, g.y.values)
                    for e, g in d.assign(era=pd.cut(
                        d.fecha,
                        bins=[pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"),
                              pd.Timestamp("2015-12-10"), pd.Timestamp("2019-12-10"),
                              pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")],
                        labels=["hasta 2011", "2011-2015", "2015-2019",
                                "2019-2023", "desde 2023"])).groupby("era", observed=True)},
    }

    # error del margen por acta: lo que realmente consume el umbral
    ma = d.groupby("acta_id").agg(pred=("p", "mean"), real=("y", "mean"), n=("y", "size"))
    res["margen"] = {
        "n_actas": int(len(ma)),
        "mae": round(float((ma.pred - ma.real).abs().mean()), 4),
        "sesgo_medio": round(float((ma.pred - ma.real).mean()), 4),
        "p90_error_abs": round(float((ma.pred - ma.real).abs().quantile(0.90)), 4),
    }
    return res


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--camara", default="", help="diputados | senado (vacio = ambas)")
    ap.add_argument("--muestra", type=int, default=0, help="0 = todas las actas")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--desde", default="",
                    help="fecha minima de acta, ej 2011-12-10. Vacio = toda la historia")
    ap.add_argument("--guard-era", default=GUARD_ERA_DEFAULT, choices=list(GUARD_ERA_MODOS),
                    help="off = como siempre; corte = el record se reinicia en cada era "
                         "(lo que hace el motor); shrink = corte + Empirical-Bayes k=5 "
                         "contra el linaje en la misma era")
    ap.add_argument("--verbose", action="store_true",
                    help="mostrar los avisos de `bloque` uno por uno (por defecto se cuentan)")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    if not args.verbose:
        cont = _ContadorAvisos()
        logging.getLogger("bloque").addFilter(cont)
        correr._tally = cont.tally
    res = correr(args.camara, args.muestra, args.seed, args.desde, args.guard_era)
    res["_args"] = {"camara": args.camara or "ambas", "muestra": args.muestra,
                    "desde": args.desde or None, "guard_era": args.guard_era}

    out = Path(args.salida) if args.salida else (
        REPO / "evaluacion/baseline/outputs/baseline_voto_individual.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
