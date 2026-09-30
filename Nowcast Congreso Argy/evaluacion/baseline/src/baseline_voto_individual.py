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

QUE MIDE — Y QUE YA NO HACE (28-09-2026, ADR-0034)
--------------------------------------------------
Para cada acta, la P_i de cada legislador que votó, calculada POR EL MOTOR, contra su
voto real. Hasta el 28-09 este archivo tenía su propia copia del récord y de `perfil`
("espejo exacto de `perfil_legislador`"). Un espejo es una divergencia esperando pasar,
y pasó dos veces: no condicionaba el récord por origen (el motor sí) y contaba como
historia los votos del mismo día. Ahora el harness NO calcula nada del legislador:

    récord    nowcast_puertas.record_legisladores   (general + por tema si RECORD_POR_TEMA)
    postura   bloque.proyectar_postura              (con la misma regla de `cond_por_acta`
                                                     que `nowcast`: necesita_cond_por_acta)
    P_i       nowcast_puertas.perfil_legislador

Lo ÚNICO que decide el harness es qué votos existían antes del acta (HISTORIAS): el motor
corta por fecha (`hasta`, estricto); el harness saca además los votos de la MISMA LEY. Un
test compara el harness contra `nowcast()` legislador por legislador
(tests/test_harness_es_el_motor.py): si vuelven a divergir, falla.

Dos diferencias con `nowcast()` que quedan, declaradas:
  1. las áreas del proyecto (para RECORD_POR_TEMA) salen de la clasificación del ACTA
     (`todas_ids` + confianza del registro); en producción, de `proyecto_taxonomias`.
  2. en la rama de BLOQUE (sin ningún voto en la era: 0,3% de los votos) el desvío es el
     del linaje; `nowcast` usa la ficha individual de `disciplina_individual.csv`, que no
     es walk-forward (se calcula con toda la historia) y no se puede usar en un backtest.
Y dos términos del motor que el harness NO mide: β del dictamen (prendido desde el
14-09) y ε0+τη (actúan en la simulación, no en P_i).

Metricas: Brier, log-loss, accuracy y calibracion por decil sobre votos EMITIDOS
(afirmativo/negativo); skill con IC por bootstrap de LEYES (la unidad efectiva,
ADR-0032). Ademas el error del MARGEN por acta, que es lo que consume el umbral.

MEMOIZACION. La postura y el récord dependen de (cámara, fecha, origen, ley excluida,
áreas) y no del acta puntual: los artículos de una ley votados el mismo día comparten
todo. Se cachea por esa clave y se vacía al cambiar de fecha.

NO TOCA EL REPO: solo lee. Escribe el resumen en outputs/.

Uso:
    python evaluacion/baseline/src/baseline_voto_individual.py --muestra 200   # smoke
    python evaluacion/baseline/src/baseline_voto_individual.py                 # completo
    python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 7     # el censo
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

VENTANA_DIAS = 730   # la de `proyectar_postura` por defecto; sólo la usan los bordes del censo
K_SHRINK = 5.0       # idem (lo importan los estimar_*.py viejos)

# QUÉ CUENTA COMO HISTORIA (28-09-2026, ADR-0034 — la regla del EXPEDIENTE).
#
#   "estricta"      fecha anterior al acta (corte del motor, `<`) y OTRA ley. El
#                   default: lo único que sabe un nowcast hecho antes de que la ley
#                   empiece a votarse.
#   "fecha"         fecha anterior, aunque sea de la misma ley (para medir cuánto pesa
#                   cada parte del arreglo).
#   "dia_incluido"  el corte del motor hasta el 28-09 (`<=`): el día entero, incluida el
#                   acta a predecir. Sólo para medir la fuga del motor.
#
# El `shift(1)` por fila que usaba este harness hasta el 28-09 ya no se puede pedir acá:
# el motor agrega por fecha. Se reproduce en `medir_fuga_historia.py`.
#
# La unidad efectiva es la LEY, no el acta (ADR-0032: 1.070 actas son 310 leyes). La
# misma dependencia que subestimaba los errores estándar, puesta en el punto estimado:
# una votación anterior de la misma ley no es una observación independiente.
HISTORIAS = ("estricta", "fecha", "dia_incluido")
HISTORIA_DEFAULT = "estricta"


# La raiz del repo sale de `rutas.py`: hay UNA sola copia del criterio
# (ver tests/test_raiz_del_repo_una_sola_copia.py).
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
from rutas import PROYECTO_ORIGEN_POR_ACTA  # noqa: E402
from definiciones import caracter_de_dictamen, era_de  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from censo_estadisticos import (dif_brier_ic_desde_sumas,  # noqa: E402
                                skill_ic_desde_sumas)
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
import nowcast_puertas as NP  # noqa: E402

# Lo importan los estimar_*.py viejos; es la constante del motor, no una copia.
MIN_HIST_INDIVIDUAL = NP.MIN_HIST_INDIVIDUAL


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
    """P(afirmativo | vota) — DELEGA en `nowcast_puertas.perfil_legislador`.

    Hasta el 28-09 esto era una copia ("espejo exacto de `perfil_legislador`"). Queda
    sólo porque los `estimar_*.py` de modelo/ensemble la importan con esta firma
    (y con `shrink=False` por defecto, que es como estimaron β, δ, θ, ψ y τ). No hace
    ninguna cuenta propia: si el motor cambia, esto cambia con él."""
    if record is not None:
        try:
            if pd.isna(record):
                record = None
        except (TypeError, ValueError):
            pass
    return NP.perfil_legislador(share_linaje, desvio, record=record,
                                n_emitidos=int(n_emitidos or 0),
                                shrink=shrink)["p_afirma_si_vota"]


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

    return g.map(caracter_de_dictamen).dropna().rename("caracter").reset_index()


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


ORIGEN_POR_ACTA = "variables/proyecto/data/origen_por_acta.parquet"
TEMA_POR_ACTA = "variables/proyecto/data/tema_por_acta.parquet"


def ley_por_acta(repo: Path = REPO) -> dict:
    """acta_id -> la LEY (expediente) a la que pertenece. La unidad efectiva (ADR-0034).

    Hay tres tablas que dicen a qué proyecto pertenece un acta, con formatos distintos
    ('0017-PE-2019' / '0017-PE-19' / 'PE-17/19-PL') y coberturas distintas (ninguna
    pasa del 72%). Una sola no alcanza: si el art. 1 de una ley sale con `proyecto_id`
    y el art. 2 sólo con expediente, quedan como dos leyes y el corte no los separa.
    Por eso se UNEN: dos actas que comparten `proyecto_id` o expediente normalizado
    (`enlace_senado.normalizar_expediente`, el normalizador del repo — no se copia)
    son la misma ley. Lo que no tiene ninguna clave queda como su propia ley, y se
    CUENTA (lo loguea `correr`): una ley sin clave es una fuga que el corte no ve."""
    sys.path.insert(0, str(repo / "datos" / "expedientes" / "src"))
    from enlace_senado import normalizar_expediente  # noqa: E402

    pares: list[tuple[str, str]] = []
    fuentes = [(ORIGEN_POR_ACTA, ["proyecto_id"], ["expediente"]),
               (ENLACE_TODAS, ["proyecto_id"], ["expediente", "clave"]),
               (TEMA_POR_ACTA, [], ["expediente"])]
    for rel, cols_pid, cols_exp in fuentes:
        ruta = repo / rel
        if not ruta.exists():
            logger.warning("ley_por_acta: falta %s (se arma con las otras fuentes)", rel)
            continue
        t = pd.read_parquet(ruta)
        for c in cols_pid:
            if c in t.columns:
                for a, x in zip(t["acta_id"].astype(str), t[c]):
                    if not pd.isna(x) and str(x).strip():
                        pares.append((a, "pid:" + str(x).strip()))
        for c in cols_exp:
            if c in t.columns:
                for a, x in zip(t["acta_id"].astype(str), t[c]):
                    e = normalizar_expediente(x)
                    if e:
                        pares.append((a, "exp:" + e))
    return agrupar_leyes(pares)


def agrupar_leyes(pares: list[tuple[str, str]]) -> dict:
    """[(acta_id, clave)] -> {acta_id: 'ley:<acta menor del grupo>'}. Union-find: dos
    actas que comparten CUALQUIER clave son la misma ley, aunque no compartan todas."""
    padre: dict = {}

    def _raiz(x):
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, k in pares:
        ra, rk = _raiz("acta:" + a), _raiz(k)
        if ra != rk:
            padre[max(ra, rk)] = min(ra, rk)
    grupos: dict = {}
    for a, _ in pares:
        grupos.setdefault(_raiz("acta:" + a), []).append(a)
    out = {}
    for miembros in grupos.values():
        etiqueta = "ley:" + min(miembros)
        for a in miembros:
            out[a] = etiqueta
    return out



def _eras_de(fechas: pd.Series) -> pd.Series:
    """Era de cada fecha. `era_de` sale de `definiciones.py` (ADR-0014) —si el
    calendario cambiara, se cambia UNA vez y lo ven todos los consumidores, incluido
    `nowcast_puertas`— pero acá se resuelve UNA VEZ POR FECHA DISTINTA: hay ~2.800
    fechas de sesion contra 1.016.058 filas, y el `.map` fila por fila tarda minutos.
    """
    mapa = {f: era_de(f) for f in pd.unique(fechas)}
    return fechas.map(mapa)


_AUX_PREFIX = "AUX"


def _areas_sustantivas(todas_ids) -> list[str]:
    """De la multietiqueta completa de una acta (`todas_ids`, ';'-separado),
    las áreas SUSTANTIVAS (no AUX), sin duplicados, orden estable. Sin
    confianza por etiqueta preservada en el contrato (`tema_por_acta.py` sólo
    guarda los ids en el orden que devolvió el agente): PASO 2 usa peso
    IGUAL para todas al validar 'ponderada' contra el histórico real — es la
    limitación honesta a reportar, no un defecto de esta función. Para peso
    REAL (confianza por etiqueta), ver `cargar_confianza_por_area` +
    `combinar_temas='ponderada_logit'` (FASE 0 de PROMPT-MULTITEMA-V2.md)."""
    if not todas_ids or (isinstance(todas_ids, float) and pd.isna(todas_ids)):
        return []
    vistas: list[str] = []
    for i in str(todas_ids).split(";"):
        i = i.strip()
        if not i or i.upper().startswith(_AUX_PREFIX):
            continue
        area = i.split(".")[0].upper()
        if area not in vistas:
            vistas.append(area)
    return vistas


REGISTRO_ASIGNACIONES = "datos/taxonomias/data/asignaciones.csv"


def cargar_confianza_por_area(repo: Path = REPO) -> dict:
    """acta_id -> {area: confianza} con la confianza REAL por etiqueta —no
    peso igual— leyendo el registro único (`datos/taxonomias/src/registro.py`,
    `nivel='acta'`). Es la pieza que le faltaba a 'ponderada' según ADR-0024
    ("todas_ids no guarda la confianza POR etiqueta"): el registro sí la
    guarda por fila (nivel, objeto=acta_id, área, confianza). Con más de una
    fila para la misma (acta_id, área) —el mismo tema con `taxonomia_id`
    distinto, ej. ECON.DEUDA y ECON.PRESU— se queda con la confianza MÁXIMA
    (la lectura más segura de "cuánto sabemos que este tema aplica").
    AUX se descarta: no es un tema sustantivo (mismo criterio que
    `_areas_sustantivas`). Degradación limpia: sin el archivo, dict vacío
    (todo cae a peso igual, como hasta ahora)."""
    p = repo / REGISTRO_ASIGNACIONES
    if not p.exists():
        logger.warning("no encontré %s: ponderada_logit va a usar peso IGUAL "
                       "(el mismo fallback que 'ponderada')", p)
        return {}
    a = pd.read_csv(p, dtype={"objeto": str, "area": str})
    a = a[(a["nivel"] == "acta") & (a["area"].astype(str).str.upper() != _AUX_PREFIX)]
    g = a.groupby(["objeto", "area"])["confianza"].max()
    out: dict = {}
    for (acta_id, area), conf in g.items():
        out.setdefault(acta_id, {})[str(area).upper()] = float(conf)
    return out


def skill_ic_por_ley(p, y, ley, n_boot: int = 300, seed: int = 7) -> list[float]:
    """IC 95% del skill re-muestreando LEYES enteras (bootstrap de Poisson, ADR-0032).
    La climatología se recalcula en cada réplica con la tasa base de esa réplica.
    El bootstrap en sí vive en `censo_estadisticos.skill_ic_desde_sumas` (una sola copia:
    el mismo cálculo sale de los estadísticos por acta que viajan por git)."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    _, cod = np.unique(np.asarray(ley).astype(str), return_inverse=True)
    k = int(cod.max()) + 1
    se = np.bincount(cod, (p - y) ** 2, k)
    sy = np.bincount(cod, y, k)
    n = np.bincount(cod, minlength=k).astype(float)
    return skill_ic_desde_sumas(se, sy, n, n_boot, seed)


def dif_brier_ic_por_ley(p1, p0, y, ley, n_boot: int = 300, seed: int = 7) -> dict:
    """ΔBrier (p1 − p0), relativo, y su IC 95% re-muestreando LEYES."""
    p1, p0, y = (np.asarray(x, float) for x in (p1, p0, y))
    e1, e0 = (p1 - y) ** 2, (p0 - y) ** 2
    _, cod = np.unique(np.asarray(ley).astype(str), return_inverse=True)
    k = int(cod.max()) + 1
    d = np.bincount(cod, e1 - e0, k)
    b0 = np.bincount(cod, e0, k)
    n = np.bincount(cod, minlength=k).astype(float)
    return dif_brier_ic_desde_sumas(d, b0, n, n_boot, seed)


ERA_BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
            pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
ERA_LABELS = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


class Contexto:
    """Todo lo que el harness le pasa al motor, cargado una vez.

    `votos` son TODAS las conductas (el motor cuenta presencia con los ausentes). Se
    parten por cámara y por (cámara, era) sólo por velocidad: el motor vuelve a filtrar
    por era y por fecha, así que pasarle un superconjunto de la era da lo mismo que
    pasarle todo — con el guard de era apagado se le pasa la cámara entera."""

    def __init__(self, votos: pd.DataFrame, leyes: dict, origen_map: dict, cond,
                 conf_area: dict, combinar_temas: str | None = None):
        if NP.TEMA_AUTO and combinar_temas is None:
            raise NotImplementedError(
                "TEMA_AUTO está prendido y el harness no reproduce cómo el motor resuelve "
                "la multietiqueta del proyecto para la postura: medir con --combinar-temas")
        v = votos.copy()
        v["acta_id"] = v["acta_id"].astype(str)
        v["_ley"] = v["acta_id"].map(leyes)
        sin = v["_ley"].isna()
        v.loc[sin, "_ley"] = "acta:" + v.loc[sin, "acta_id"]
        self.frac_votos_sin_ley = float(sin.mean())
        self.votos = v
        self.por_cam = {c: g for c, g in v.groupby("camara", sort=False)}
        eras = _eras_de(v["fecha"])
        self.por_cam_era = {k: g for k, g in v.groupby([v["camara"], eras], sort=False)}
        self.ley_de_acta = dict(zip(v["acta_id"], v["_ley"]))
        self.origen_map = origen_map
        self.cond = cond
        self.cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                         if cond is not None and len(cond) else {})
        self.conf_area = conf_area
        self.combinar_temas = combinar_temas
        self._fecha_cache = None
        self._rec: dict = {}
        self._post: dict = {}
        self.avisos = {"record_sin_votos_en_la_era": 0, "postura_saltada": 0}

    @classmethod
    def desde_repo(cls, combinar_temas: str | None = None, votos=None) -> "Contexto":
        from bloque import cargar as cargar_bloque, cargar_tema_por_acta
        votos = cargar_bloque() if votos is None else votos
        cond = cargar_tema_por_acta()
        opa = pd.read_parquet(PROYECTO_ORIGEN_POR_ACTA)            # lo mismo que `nowcast`
        origen_map = dict(zip(opa["acta_id"].astype(str), opa["origen"]))
        return cls(votos, ley_por_acta(REPO), origen_map, cond, cargar_confianza_por_area(),
                   combinar_temas)

    # ── lo que decide el harness: qué votos existían ──
    def _base(self, camara: str, hasta: pd.Timestamp) -> pd.DataFrame:
        if NP.GUARD_ERA:
            return self.por_cam_era.get((camara, NP.era_de(hasta)), self.votos.iloc[:0])
        return self.por_cam.get(camara, self.votos.iloc[:0])

    @staticmethod
    def _hasta(fecha: pd.Timestamp, historia: str) -> pd.Timestamp:
        if historia not in HISTORIAS:
            raise ValueError(f"historia invalida: {historia!r} (esperaba {HISTORIAS})")
        return fecha + pd.Timedelta(days=1) if historia == "dia_incluido" else fecha

    @staticmethod
    def _sin_ley(v: pd.DataFrame, ley: str, historia: str) -> pd.DataFrame:
        return v[v["_ley"] != ley] if historia == "estricta" else v

    def areas_del_acta(self, acta_id: str) -> list | None:
        """Las áreas del proyecto para RECORD_POR_TEMA, con su confianza (1.0 si el
        registro no la tiene). None si el acta no tiene áreas sustantivas."""
        info = self.cond_map.get(str(acta_id), {})
        areas = _areas_sustantivas(info.get("todas_ids"))
        if not areas:
            return None
        pesos = self.conf_area.get(str(acta_id), {})
        return [(a, pesos.get(a, 1.0)) for a in areas]

    def _vaciar_si_cambia(self, fecha):
        if fecha != self._fecha_cache:
            self._rec.clear()
            self._post.clear()
            self._fecha_cache = fecha

    def record(self, camara, fecha, ley, origen, areas, historia, record_por_tema):
        self._vaciar_si_cambia(fecha)
        hasta = self._hasta(fecha, historia)
        usar_tema = NP.RECORD_POR_TEMA if record_por_tema is None else bool(record_por_tema)
        k = (camara, historia, ley if historia == "estricta" else None, origen,
             tuple(areas) if (usar_tema and areas) else None)
        if k not in self._rec:
            base = self._sin_ley(self._base(camara, hasta), ley, historia)
            if base.empty:
                self.avisos["record_sin_votos_en_la_era"] += 1
            cond = self.cond if NP.necesita_cond_por_acta(None, origen, None,
                                                          areas if usar_tema else None) else None
            ind, _ = NP.record_legisladores(base, hasta, origen, self.origen_map, areas,
                                            cond, record_por_tema=usar_tema)
            self._rec[k] = ind
        return self._rec[k]

    def postura(self, camara, fecha, ley, origen, areas_ind, historia, acta_id=None):
        """{linaje: postura} de `proyectar_postura`, con la misma regla de `cond_por_acta`
        que `nowcast` (sin cond, la postura no puede sacar las actas AUX). La postura
        corta siempre con `<` (nunca tuvo la fuga del récord); con historia "estricta"
        la ventana tampoco ve la misma ley. None si no se pudo proyectar."""
        from bloque import proyectar_postura
        self._vaciar_si_cambia(fecha)
        kwargs, clave_tema = self._kwargs_tema(acta_id)
        estricta = historia == "estricta"
        usa_cond = NP.necesita_cond_por_acta(kwargs.get("tema"), origen, kwargs.get("temas"),
                                            areas_ind)
        k = (camara, estricta, ley if estricta else None, origen, usa_cond, clave_tema)
        if k not in self._post:
            v = self._sin_ley(self.por_cam.get(camara, self.votos.iloc[:0]), ley,
                              "estricta" if estricta else "fecha")
            try:
                post = proyectar_postura(v, fecha, camara, origen=origen,
                                         cond_por_acta=self.cond if usa_cond else None,
                                         **kwargs)
                self._post[k] = {p["bloque"]: p for p in post}
            except (ValueError, KeyError) as e:
                logger.debug("postura %s %s saltada: %s", camara, fecha.date(), e)
                self.avisos["postura_saltada"] += 1
                self._post[k] = None
        return self._post[k]

    def _kwargs_tema(self, acta_id) -> tuple[dict, object]:
        """Tema de la POSTURA. Con `combinar_temas=None` (el default) hace lo que hace el
        motor con TEMA_AUTO apagado: nada. Los otros modos son los experimentos de
        ADR-0024/0028 (`fase0_control_temas.py`) y no describen al motor."""
        ct = self.combinar_temas
        if ct is None or ct == "sin_tema":
            return {}, None
        info = self.cond_map.get(str(acta_id), {})
        if ct == "primaria":
            tema = _norm_cond(info.get("tema_area"))
            return ({"tema": tema} if tema else {}), tema
        areas = _areas_sustantivas(info.get("todas_ids"))
        if not areas:
            return {}, None
        if ct == "ponderada_logit":
            pes = self.conf_area.get(str(acta_id), {})
            tp = [(a, pes.get(a, 1.0)) for a in areas]
            return {"temas": tp, "combinar_temas": ct}, tuple(sorted(tp))
        return {"temas": areas, "combinar_temas": ct}, tuple(areas)

    def p_legisladores(self, acta_id, camara, fecha, votantes: pd.DataFrame,
                       historia=HISTORIA_DEFAULT, record_por_tema=None) -> dict | None:
        """{legislador_id: (p, fuente, share, desvio, record, n_emit)} para los
        `votantes` de un acta (columnas legislador_id, bloque_linaje). Es la P_i del
        motor; el harness sólo eligió la historia. None si la postura no se pudo
        proyectar (se cuenta)."""
        acta_id = str(acta_id)
        fecha = pd.Timestamp(fecha)
        ley = self.ley_de_acta.get(acta_id, "acta:" + acta_id)
        origen = _norm_cond(self.origen_map.get(acta_id))
        usar_tema = NP.RECORD_POR_TEMA if record_por_tema is None else bool(record_por_tema)
        areas = self.areas_del_acta(acta_id) if usar_tema else None
        post = self.postura(camara, fecha, ley, origen, areas, historia, acta_id)
        if post is None:
            return None
        ind = self.record(camara, fecha, ley, origen, areas, historia, usar_tema)
        out = {}
        for lid, lin in zip(votantes["legislador_id"], votantes["bloque_linaje"]):
            p = post.get(str(lin))
            if p is None:
                continue
            rec = ind.get((camara, lid))
            p_rec, _n, pres, n_emit = rec if rec else (None, 0, 1.0, 0)
            pf = NP.perfil_legislador(p["_share_afirm"], p["desvio"], record=p_rec,
                                      n_emitidos=n_emit, presencia=pres)
            out[lid] = (pf["p_afirma_si_vota"], pf["fuente_direccion"], p["_share_afirm"],
                        p["desvio"], p_rec, n_emit)
        return out


def _nombre(historia: str, record_por_tema) -> str:
    t = NP.RECORD_POR_TEMA if record_por_tema is None else bool(record_por_tema)
    return f"{historia}__{'tema' if t else 'general'}"


def correr(camara_filtro: str = "", muestra: int = 0, seed: int = 7, desde: str = "",
           hasta: str = "", historia: str = HISTORIA_DEFAULT, record_por_tema=None,
           variantes_extra: tuple = (), combinar_temas: str | None = None,
           devolver_detalle: bool = False, contexto: Contexto | None = None):
    """El censo: P_i del motor contra el voto real, para cada voto emitido.

    `historia`/`record_por_tema` definen la variante PRINCIPAL (columna `p`, y el
    resumen). `variantes_extra` = [(historia, record_por_tema), ...] agrega columnas
    `p__<historia>__<tema|general>` en el detalle, calculadas en la misma pasada (el
    censo de ADR-0034 las usa para descomponer el arreglo). `record_por_tema=None`
    sigue a la bandera del motor.

    `desde`/`hasta` (exclusivo) recortan QUÉ actas se evalúan, no la historia: partir
    el censo por fechas da el mismo detalle (`censo_detalle_paralelo.py`)."""
    ctx = contexto or Contexto.desde_repo(combinar_temas)
    logger.info("ley_por_acta: %.1f%% de los votos sin ley conocida (ahí el corte por "
                "expediente no ve nada: cada acta es su propia ley)",
                100 * ctx.frac_votos_sin_ley)
    variantes = [(historia, record_por_tema)] + [tuple(x) for x in variantes_extra]
    nombres = [_nombre(h, t) for h, t in variantes]
    if len(set(nombres)) != len(nombres):
        raise ValueError(f"variantes repetidas: {nombres}")

    v = ctx.votos[ctx.votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    if camara_filtro:
        v = v[v["camara"] == camara_filtro]
    v = v.assign(af=(v["conducta"] == "AFIRMATIVO").astype(int))

    actas = (v[["acta_id", "fecha", "camara"]].drop_duplicates("acta_id")
             .sort_values(["fecha", "acta_id"]).reset_index(drop=True))
    piso = ctx.votos["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)   # una ventana de historia
    if desde:
        piso = max(piso, pd.Timestamp(desde))
    actas = actas[actas["fecha"] >= piso]
    if hasta:
        actas = actas[actas["fecha"] < pd.Timestamp(hasta)]
    if muestra:
        actas = actas.sample(min(muestra, len(actas)), random_state=seed).sort_values(
            ["fecha", "acta_id"])
    logger.info("actas a evaluar: %d · variantes: %s", len(actas), nombres)

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cols: dict = {c: [] for c in ("acta_id", "fecha", "camara", "legislador", "linaje", "y",
                                  "ley", "origen")}
    extra: dict = {}
    saltadas = 0
    for k, a in enumerate(actas.itertuples(), 1):
        if k % 250 == 0:
            logger.info("  %d/%d actas", k, len(actas))
        sub = por_acta.get(a.acta_id)
        if sub is None:
            continue
        res = [ctx.p_legisladores(a.acta_id, a.camara, a.fecha, sub, h, t)
               for h, t in variantes]
        if res[0] is None:
            saltadas += 1
            continue
        for r in sub.itertuples():
            lid = r.legislador_id
            if lid not in res[0] or any(x is None or lid not in x for x in res):
                continue
            cols["acta_id"].append(a.acta_id)
            cols["fecha"].append(a.fecha)
            cols["camara"].append(a.camara)
            cols["legislador"].append(lid)
            cols["linaje"].append(r.bloque_linaje)
            cols["y"].append(r.af)
            cols["ley"].append(ctx.ley_de_acta.get(str(a.acta_id)))
            cols["origen"].append(_norm_cond(ctx.origen_map.get(str(a.acta_id))))
            for i, (nom, x) in enumerate(zip(nombres, res)):
                p, fuente, share, desvio, rec, n_emit = x[lid]
                pre = "" if i == 0 else f"__{nom}"
                for c, val in (("p", p), ("fuente", fuente), ("share", share),
                               ("desvio", desvio), ("record", rec), ("n_prev", n_emit)):
                    extra.setdefault(c + pre, []).append(val)
    d = pd.DataFrame({**cols, **extra})
    if d.empty:
        raise RuntimeError("no se evaluo ningun voto; revisa filtros y contratos")
    # la principal también con su nombre largo, para que los brazos se lean igual
    d[f"p__{nombres[0]}"] = d["p"]
    d["fuente"] = d["fuente"].map(lambda f: "bloque" if f == "bloque" else "record")

    car = mapa_acta_caracter(REPO)
    d = d.merge(car[["acta_id", "caracter"]], on="acta_id", how="left")

    res = resumir(d, "p")
    res.update({
        "n_actas_evaluadas": int(d.acta_id.nunique()),
        "n_leyes_evaluadas": int(d.ley.nunique()),
        "n_actas_saltadas": int(saltadas),
        "frac_votos_sin_ley": round(ctx.frac_votos_sin_ley, 4),
        "avisos_motor": dict(ctx.avisos),
        "avisos_agregados": dict(getattr(correr, "_tally", {})),
        "rango_fechas": [str(d.fecha.min().date()), str(d.fecha.max().date())],
        "historia": historia,
        "variante": nombres[0],
        "motor": {"GUARD_ERA": NP.GUARD_ERA, "SHRINK_RECORD": NP.SHRINK_RECORD,
                  "RECORD_POR_TEMA": NP.RECORD_POR_TEMA, "TEMA_AUTO": NP.TEMA_AUTO,
                  "MIN_HIST_INDIVIDUAL": NP.MIN_HIST_INDIVIDUAL,
                  "K_SHRINK_RECORD": NP.K_SHRINK_RECORD},
        "combinar_temas_postura": combinar_temas or "(el del motor: sin tema)",
    })
    if devolver_detalle:
        return res, d
    return res


def resumir(d: pd.DataFrame, col: str = "p") -> dict:
    """Métricas de una columna de P sobre el detalle voto a voto. Los IC del skill
    re-muestrean LEYES (columna `ley`; si falta, el acta)."""
    ley = d["ley"].fillna("acta:" + d["acta_id"].astype(str)) if "ley" in d else d["acta_id"]
    fuente = d["fuente"] if col == "p" or f"fuente{col[1:]}" not in d else d[f"fuente{col[1:]}"]
    fuente = fuente.map(lambda f: "bloque" if f == "bloque" else "record")
    era = pd.cut(d["fecha"], bins=ERA_BINS, labels=ERA_LABELS)

    def _m(mask):
        m = _metricas(d.loc[mask, col].values, d.loc[mask, "y"].values)
        if m:
            m["skill_ic95_ley"] = skill_ic_por_ley(d.loc[mask, col], d.loc[mask, "y"],
                                                   ley[mask])
            m["n_leyes"] = int(ley[mask].nunique())
        return m

    todo = np.ones(len(d), bool)
    res = {
        "columna": col,
        "global": _m(todo),
        "calibracion": _calibracion(d[col].values, d["y"].values),
        "por_camara": {c: _m((d["camara"] == c).to_numpy()) for c in sorted(d["camara"].unique())},
        "por_fuente_direccion": {c: _m((fuente == c).to_numpy()) for c in sorted(fuente.unique())},
        "por_caracter_dictamen": ({str(c): _metricas(g[col].values, g["y"].values)
                                   for c, g in d.groupby("caracter", dropna=False)}
                                  if "caracter" in d else {}),
        # ERA. Los cortes son recambios de mandato (10-dic).
        "por_era": {e: _m((era == e).to_numpy()) for e in ERA_LABELS if (era == e).any()},
    }
    ma = d.groupby("acta_id").agg(pred=(col, "mean"), real=("y", "mean"))
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
    ap.add_argument("--historia", default=HISTORIA_DEFAULT, choices=list(HISTORIAS),
                    help="estricta (default) = fecha anterior y otra ley; fecha = fecha "
                         "anterior; dia_incluido = el corte `<=` que tenía el motor")
    ap.add_argument("--record-por-tema", choices=["motor", "si", "no"], default="motor",
                    help="motor (default) = lo que diga RECORD_POR_TEMA; si/no = forzarlo")
    ap.add_argument("--combinar-temas", default=None,
                    choices=["primaria", "union", "ponderada", "peor_tema",
                             "sin_tema", "ponderada_logit"],
                    help="tema de la POSTURA. Sin esto, lo que hace el motor (TEMA_AUTO "
                         "apagado: sin tema). Los modos son los experimentos de ADR-0024/0028")
    ap.add_argument("--verbose", action="store_true",
                    help="mostrar los avisos de `bloque` uno por uno (por defecto se cuentan)")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    silenciar_avisos_del_motor(args.verbose)
    rpt = {"motor": None, "si": True, "no": False}[args.record_por_tema]
    res = correr(args.camara, args.muestra, args.seed, args.desde, historia=args.historia,
                 record_por_tema=rpt, combinar_temas=args.combinar_temas)
    res["_args"] = {"camara": args.camara or "ambas", "muestra": args.muestra,
                    "desde": args.desde or None, "historia": args.historia,
                    "record_por_tema": args.record_por_tema,
                    "combinar_temas": args.combinar_temas}

    out = Path(args.salida) if args.salida else (
        REPO / "evaluacion/baseline/outputs/baseline_voto_individual.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("global", "por_era", "n_actas_evaluadas")},
                     ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


def silenciar_avisos_del_motor(verbose: bool = False) -> None:
    """El motor loguea una línea por llamada (`alineacion_individual_por_area`, el
    'sin votos entre...' al arrancar cada era). En un censo son decenas de miles: se
    cuentan en vez de imprimirse (mismo criterio que `_ContadorAvisos` con `bloque`)."""
    if verbose:
        return
    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)
    logging.getLogger("nowcast_puertas").setLevel(logging.ERROR)
    correr._tally = cont.tally


if __name__ == "__main__":
    main(sys.argv[1:])
