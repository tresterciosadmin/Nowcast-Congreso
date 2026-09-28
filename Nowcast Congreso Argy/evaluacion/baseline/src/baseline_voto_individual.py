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
record individual usa sólo votos de FECHA ANTERIOR y de OTRA LEY (ver HISTORIAS; hasta
el 28-09 era `shift(1)` por fila y contaba los artículos previos de la misma ley).

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

# QUÉ CUENTA COMO HISTORIA (28-09-2026, ADR-0034 — la regla del EXPEDIENTE).
#
#   "estricta"  votos de FECHA anterior al acta y de OTRA ley. El default: es lo único
#               que un nowcast hecho antes de que la ley empiece a votarse puede saber.
#   "fecha"     votos de fecha anterior, aunque sean de la misma ley (sólo para medir
#               cuánto pesa cada parte del arreglo).
#   "fila"      lo que se hacía hasta el 28-09: `shift(1)` sobre votos ordenados por
#               fecha. Cuenta como historia los artículos ANTERIORES DE LA MISMA LEY,
#               votados el mismo día y casi siempre con el mismo resultado: le dice la
#               respuesta. Se deja sólo para reproducir el número viejo.
#
# La unidad efectiva es la LEY, no el acta (ADR-0032: 1.070 actas son 310 leyes). La
# misma dependencia que subestimaba los errores estándar, puesta en el punto estimado:
# una votación anterior de la misma ley no es una observación independiente.
HISTORIAS = ("estricta", "fecha", "fila")
HISTORIA_DEFAULT = "estricta"


# La raiz del repo sale de `rutas.py`: hay UNA sola copia del criterio
# (ver tests/test_raiz_del_repo_una_sola_copia.py). Buscar `coordinacion/` +
# `variables/` daba lo mismo -- esta medido -- pero se apoyaba en que esas dos
# carpetas no cambiaran de nombre ni de lugar.
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
from definiciones import caracter_de_dictamen, era_de  # noqa: E402
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


def record_previo(v: pd.DataFrame, llave: list[str], historia: str = HISTORIA_DEFAULT
                  ) -> tuple[np.ndarray, np.ndarray]:
    """(n, afirmativos) de la historia de cada fila dentro de `llave`.

    `v` tiene que venir ordenado por fecha (orden estable) y traer `af`, `fecha` y
    `_ley`. Con `historia="fila"` es exactamente `shift(1).expanding()` —el de siempre—;
    con "fecha" se descuentan las filas del mismo día; con "estricta" además las de la
    misma ley en fechas anteriores. Todo con cumcount/cumsum: sobre un millón de filas
    el `transform(lambda)` tarda minutos."""
    if historia not in HISTORIAS:
        raise ValueError(f"historia invalida: {historia!r} (esperaba {HISTORIAS})")

    def _cum(cols):
        g = v.groupby(cols, sort=False, observed=True)["af"]
        return g.cumcount().to_numpy(float), (g.cumsum() - v["af"]).to_numpy(float)

    n, a = _cum(llave)
    if historia in ("fecha", "estricta"):
        n_d, a_d = _cum(llave + ["fecha"])
        n, a = n - n_d, a - a_d
    if historia == "estricta":
        n_l, a_l = _cum(llave + ["_ley"])
        n_ld, a_ld = _cum(llave + ["_ley", "fecha"])
        n, a = n - (n_l - n_ld), a - (a_l - a_ld)
    return n, a


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


def correr(camara_filtro: str = "", muestra: int = 0, seed: int = 7,
           desde: str = "", guard_era: str = GUARD_ERA_DEFAULT,
           combinar_temas: str = "primaria", devolver_detalle: bool = False,
           hasta: str = "", historia: str = HISTORIA_DEFAULT):
    """`combinar_temas` (PASO 2 de coordinacion/PROMPT-MULTIETIQUETA.md, Parte A;
    FASE 0 de PROMPT-MULTITEMA-V2.md agrega 'sin_tema' y 'ponderada_logit'):

    'primaria' es el comportamiento de SIEMPRE — la única etiqueta que
    `tema_por_acta._elegir_primaria` le dejó a cada acta — y es el default, así
    que una corrida sin este argumento da EXACTAMENTE el mismo resultado que
    antes de que existiera. 'union'/'ponderada' condicionan `proyectar_postura`
    con la multietiqueta COMPLETA (`todas_ids`) de la acta evaluada, no sólo su
    primaria.

    'sin_tema' (FASE 0, el BRAZO DE CONTROL que PASO 2 no tenía): la rama de
    bloque NUNCA se condiciona por tema —ni primaria ni multietiqueta—, sólo
    por origen (que sigue igual en los 5 modos: es un eje distinto, ya
    decidido, no lo que esta fase pone a prueba). Sin este brazo no se puede
    distinguir "qué regla de combinación es mejor" de "condicionar por tema
    ACÁ hace daño" — que es la pregunta real.

    'ponderada_logit': mismo cómputo que 'ponderada' pero combinando en LOGIT
    (`bloque.proyectar_postura`) con la confianza REAL por etiqueta
    (`cargar_confianza_por_area`, el registro único) en vez de peso igual.

    `devolver_detalle=True` además del resumen agregado, devuelve
    `(resumen, d)` con `d` el DataFrame voto-a-voto (acta_id, camara, p, y,
    fuente, caracter) — lo que hace falta para un bootstrap clusterizado por
    acta entre brazos (FASE 0 lo pide explícitamente: "clusterizando por
    acta", "reportá el intervalo, no sólo el punto")."""
    if combinar_temas not in ("primaria", "union", "ponderada", "peor_tema",
                              "sin_tema", "ponderada_logit"):
        raise ValueError(f"combinar_temas invalido: {combinar_temas!r}")
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta

    logger.info("cargando canonica...")
    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = None
    if cond is not None and len(cond):
        cond_map = cond.set_index(cond.columns[0]).to_dict("index")
    conf_area = cargar_confianza_por_area() if combinar_temas == "ponderada_logit" else {}

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara_filtro:
        v = v[v["camara"] == camara_filtro]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    # el mismo `sort_values` de siempre (no `stable`): con historia="fila" el orden dentro
    # del día decide el récord, y así reproduce el número viejo bit a bit. Con
    # "fecha"/"estricta" el orden dentro del día no importa.
    v = v.sort_values("fecha")

    # record propio walk-forward: promedio de los votos ANTERIORES de esa persona.
    # Con guard, ese promedio se reinicia en cada era (ver GUARD_ERA_MODOS arriba).
    # "Anteriores" según `historia` (ver HISTORIAS): por defecto, de fecha anterior Y
    # de otra ley.
    if guard_era not in GUARD_ERA_MODOS:
        raise ValueError(f"guard_era invalido: {guard_era!r} (esperaba {GUARD_ERA_MODOS})")
    leyes = ley_por_acta(REPO)
    v["_ley"] = v["acta_id"].astype(str).map(leyes)
    sin_ley = v["_ley"].isna()
    v.loc[sin_ley, "_ley"] = "acta:" + v.loc[sin_ley, "acta_id"].astype(str)
    logger.info("ley_por_acta: %.1f%% de los votos con ley conocida (el resto: cada acta "
                "es su propia ley, y ahí el corte por expediente no ve nada)",
                100 * (1 - sin_ley.mean()))
    if guard_era == "off":
        llave = ["legislador_id"]
    else:
        v["_era"] = _eras_de(v["fecha"])
        llave = ["legislador_id", "_era"]
    n_prev, a_prev = record_previo(v, llave, historia)
    v["n_prev"] = n_prev
    v["record"] = np.where(n_prev > 0, a_prev / np.maximum(n_prev, 1), np.nan)
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
    # `hasta` (exclusivo) sólo recorta QUÉ actas se evalúan: el récord ya se calculó
    # sobre toda la historia, así que partir el censo por fechas da el mismo detalle.
    if hasta:
        actas = actas[actas["fecha"] < pd.Timestamp(hasta)]
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
        origen = _norm_cond(info.get("origen"))
        kwargs_tema: dict = {}
        if combinar_temas == "sin_tema":
            # el BRAZO DE CONTROL: nunca condiciona por tema (ni primaria ni
            # multietiqueta) — origen sigue igual que en los demás brazos, es
            # un eje distinto. kwargs_tema vacío -> proyectar_postura recibe
            # combinar_temas='primaria' (su único modo sin match obligatorio)
            # pero SIN tema, que es exactamente la incondicional.
            clave_tema = None
        elif combinar_temas == "primaria":
            tema = _norm_cond(info.get("tema_area"))
            clave_tema = tema
        elif combinar_temas == "ponderada_logit":
            areas = _areas_sustantivas(info.get("todas_ids"))
            pesos_reales = conf_area.get(str(a.acta_id), {})
            if areas:
                # confianza real si el registro la tiene para esa área; si no
                # (falla del cruce acta_id, ver ADR-0023/registro), 1.0 —
                # mismo fallback a peso igual que 'ponderada' para esa etiqueta
                # puntual, no para la corrida entera.
                temas_pesados = [(ar, pesos_reales.get(ar, 1.0)) for ar in areas]
                kwargs_tema = {"temas": temas_pesados, "combinar_temas": combinar_temas}
                clave_tema = tuple(sorted(temas_pesados))
            else:
                clave_tema = None
        else:
            areas = _areas_sustantivas(info.get("todas_ids"))
            if areas:
                kwargs_tema = {"temas": areas, "combinar_temas": combinar_temas}
                clave_tema = tuple(areas)
            else:
                clave_tema = None  # sin multietiqueta sustantiva: incondicional, como primaria
        clave = (a.camara, a.fecha.year, a.fecha.month, clave_tema, origen, combinar_temas)
        if clave in cache:
            by_lin = cache[clave]
        else:
            try:
                post = proyectar_postura(
                    votos, a.fecha, a.camara, ventana_dias=VENTANA_DIAS,
                    origen=origen, cond_por_acta=cond, k_shrink=K_SHRINK, **kwargs_tema)
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
                # insumos de `p`, para recomputar brazos sin re-proyectar la postura
                "share": p["_share_afirm"], "desvio": p["desvio"],
                "record": r.record, "n_prev": r.n_prev, "origen": origen,
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
        "historia": historia,
        "combinar_temas": combinar_temas,
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
    if devolver_detalle:
        return res, d
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
    ap.add_argument("--combinar-temas", default="primaria",
                    choices=["primaria", "union", "ponderada", "peor_tema",
                             "sin_tema", "ponderada_logit"],
                    help="primaria (default, de siempre) = una sola etiqueta por acta; "
                         "union/ponderada (PASO 2, Parte A) condicionan con la "
                         "multietiqueta completa (todas_ids) de la acta evaluada; "
                         "sin_tema (FASE 0) = brazo de control, nunca condiciona por "
                         "tema; ponderada_logit (FASE 0) = como ponderada pero en "
                         "logit y con confianza real por etiqueta")
    ap.add_argument("--historia", default=HISTORIA_DEFAULT, choices=list(HISTORIAS),
                    help="estricta (default) = fecha anterior y otra ley; fecha = fecha "
                         "anterior; fila = shift(1), el harness con fuga hasta el 28-09")
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
    res = correr(args.camara, args.muestra, args.seed, args.desde, args.guard_era,
                args.combinar_temas, historia=args.historia)
    res["_args"] = {"camara": args.camara or "ambas", "muestra": args.muestra,
                    "desde": args.desde or None, "guard_era": args.guard_era,
                    "combinar_temas": args.combinar_temas, "historia": args.historia}

    out = Path(args.salida) if args.salida else (
        REPO / "evaluacion/baseline/outputs/baseline_voto_individual.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
