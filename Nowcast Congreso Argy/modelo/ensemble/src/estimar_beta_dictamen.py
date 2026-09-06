"""PASO 1 — Estima beta: cuanto mueve el DICTAMEN el voto de cada legislador.

FORMULACION QUE ESTIMA (§III.A.2 de FORMULA-COMPLETA.md, ADR-0016):

    logit(P_i^dict) = logit(P_i) + b1*F_i + b2*(1-d_i)*J_l + b3*W_{-l}

      F_i          firmo el propio legislador el dictamen
      J_l          firmo el jefe de SU bloque
      (1-d_i)      su lealtad: cuanto le pesa lo que hizo su jefe
      W_{-l}       anchura de los OTROS linajes firmantes (bancas ajenas / M_c)

EL DISENO: OFFSET, no efectos fijos
-----------------------------------
`logit(P_i)` —la prediccion del motor HOY— entra como **offset** (coeficiente fijado en 1),
no como regresor. Consecuencias, y son las que hacen que esto sirva:

  1. Los betas miden **lo que el dictamen agrega POR ENCIMA del motor**, que es exactamente
     el numero que la formula necesita sumar. No hay que re-escalar nada despues.
  2. El offset ya absorbe el historial de la persona, su bloque y su presencia, asi que
     **no hacen falta efectos fijos de legislador**: estan adentro de P_i.
  3. Si beta sale ~0, la lectura es limpia: el dictamen no agrega informacion sobre lo que
     el motor ya sabia. No es que "no importe" — es que era redundante.

CONTROLES DE SELECCION. El contraste crudo del 03-09 (-3,2 en logit entre dictamen unico y
disputado) mezcla dos cosas: que el dictamen informa, y que los proyectos con dictamen
disputado SON proyectos mas conflictivos. Se corre en tres capas anidadas para separarlas:

    M0  solo caracter del dictamen (el crudo, para comparar)
    M1  + offset del motor            -> descuenta quien es cada legislador
    M2  + tema y origen del proyecto  -> descuenta que clase de proyecto es

Si el efecto sobrevive a M2, es informacion del dictamen. Si se desploma, era seleccion.

WALK-FORWARD en todo: el record y el desvio individuales se acumulan con shift(1), y la
postura de bloque se proyecta con la ventana anterior (contrato de variables/bloque).

Uso:
    python modelo/ensemble/src/estimar_beta_dictamen.py --muestra 400   # rapido
    python modelo/ensemble/src/estimar_beta_dictamen.py                 # completo
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import unicodedata

import numpy as np
import pandas as pd

logger = logging.getLogger("estimar_beta")


def _norm_nombre(s) -> str:
    """'DI TULLIO, Juliana' y 'DI TULLIO, JULIANA' tienen que ser la misma persona."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().replace(".", " ").split())


def _clave_persona(s) -> str:
    """Clave laxa 'APELLIDO|PRIMER-NOMBRE' para cruzar rosters escritos distinto.

    El roster de jefes trae formas cortas ('ROSSI, AGUSTIN') y las firmas traen la
    forma larga ('ROSSI, Agustin Oscar'). Comparar el string entero resolvia 21 de 80.
    Con apellido + primer nombre de pila el cruce es robusto sin volverse promiscuo:
    'MARTINEZ, GERMAN' no colisiona con 'MARTINEZ, JULIA'.
    """
    n = _norm_nombre(s)
    if "," in n:
        ape, _, resto = n.partition(",")
    else:  # 'BORNORONI GABRIEL' (snapshot oficial, sin coma): ultimo token es el nombre
        partes = n.split()
        ape, resto = " ".join(partes[:-1]), partes[-1] if len(partes) > 1 else ""
    ape = " ".join(ape.split())
    pila = resto.split()[0] if resto.split() else ""
    return f"{ape}|{pila}"

MIN_HIST_INDIVIDUAL = 8
# Actas minimas para que un error estandar cluster-robusto POR ACTA signifique algo.
# La literatura pide 30-50; 20 es el piso por debajo del cual directamente no se
# reporta como hallazgo. Ver el comentario en `estimar()`.
MIN_CLUSTERS_CONFIABLE = 20
VENTANA_DIAS = 730
K_SHRINK = 5.0
BANCAS = {"diputados": 257, "senado": 72}


def _hallar_repo() -> Path:
    p = Path(__file__).resolve()
    for cand in [p, *p.parents]:
        if (cand / "coordinacion").is_dir() and (cand / "variables").is_dir():
            return cand
    raise FileNotFoundError("no encontre la raiz del repo")


REPO = _hallar_repo()
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))
sys.path.insert(0, str(REPO / "datos" / "canonica" / "src"))

# ALIAS de legislador_id (URGENTE C, 04-09-2026). La misma persona con dos ids en la
# canonica, casi siempre por la costura entre fuentes. Aca se usa SOLO para cruzar el
# roster de jefes contra las firmas del dictamen: si el jefe quedo con un id y su firma
# con el otro, el cruce falla y `J_l` da 0 por construccion. NO se toca la canonica —
# eso esta medido y por ahora empeora el skill; ver `datos/canonica/data/alias_legislador_id.csv`.
try:
    from alias_legislador import cargar_alias
except ImportError:  # pragma: no cover
    def cargar_alias():
        return {}


def _logit(p, eps=1e-4):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p / (1 - p))


# ---------------------------------------------------------------------------
# Insumos del dictamen
# ---------------------------------------------------------------------------

ENLACE_TODAS = "datos/expedientes/data/clean/acta_expediente_todas.parquet"
FIRMAS_DIP = "datos/expedientes/data/clean/dictamenes_firmas.parquet"
FIRMAS_SEN = "datos/expedientes/data/clean/dictamenes_firmas_senado.parquet"


def _caracter_por_proyecto_camara(f: pd.DataFrame) -> pd.DataFrame:
    """(proyecto_id, camara) -> caracter del dictamen. Ver §II.3 de FORMULA-COMPLETA.

    **Por camara, no por proyecto.** Un proyecto bicameral tiene dictamen en las
    dos, y no tienen por que coincidir: lo que un senador lee cuando vota es el
    dictamen de SU camara. Mezclarlos le pondria a un acta del Senado el caracter
    del despacho de Diputados.
    """
    g = (f.groupby(["proyecto_id", "camara"])["dictamen_clase"]
           .apply(lambda s: frozenset(x for x in s.dropna() if x)))

    def clasificar(c):
        # `desconocido` (parser_od, 04-09-2026) = no se encontro el rotulo del
        # dictamen. NO es "despacho unico": si es lo unico que hay, el proyecto
        # queda SIN caracter en esa camara y sale del panel.
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


def firmas_por_acta(repo: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Devuelve (firmas, mapa_acta, mapa_nombre) ya cruzadas al expediente y al acta.

    `firmas` es (proyecto_id, camara, legislador_id, bloque_linaje); `mapa_acta`
    es (acta_id, proyecto_id, caracter).

    **CAMBIO 04-09-2026 (ADR-0017), y es el que desbloquea el Senado.** Antes esta
    funcion leia UNA sola camara y UNA sola tabla de enlace:

      - las firmas salian solo de `dictamenes_firmas.parquet`, que es **Diputados**.
        Para un acta del Senado, `F_i` ("firmo el propio legislador") era 0 por
        construccion: sus 18.105 firmas vivian en otro parquet que nadie leia aca.
      - el enlace salia de `acta_expediente.parquet`, que es el volcado crudo de
        CKAN — **solo Diputados**, 1.849 filas, sin `proyecto_id` resuelto.

    Por eso `--camara senado` devolvia **"0 actas con dictamen identificado"**. No
    era el parser: era el cableado. Medido hoy sobre los mismos parquets:

        tabla de enlace              actas con caracter (dip / sen)
        acta_expediente.parquet          710 dip  ·    0 sen
        acta_expediente_todas.parquet  1.705 dip  ·  474 sen

    Ahora se leen las dos camaras y la tabla resuelta, que ya trae `proyecto_id` y
    `camara` y evita el merge a mano por texto de expediente.
    """
    partes = []
    for rel in (FIRMAS_DIP, FIRMAS_SEN):
        p = repo / rel
        if not p.exists():
            logger.warning("no encontre %s: esa camara queda sin dictamen", p.name)
            continue
        d = pd.read_parquet(p)
        partes.append(d[d["parseo_ok"]].copy())
    if not partes:
        raise FileNotFoundError(
            "no hay ningun parquet de firmas: corre "
            "datos/expedientes/src/construir_firmas.py [--senado]")
    f = pd.concat(partes, ignore_index=True)

    alias = cargar_alias()
    if alias and "legislador_id" in f.columns:
        antes = f["legislador_id"].nunique()
        f["legislador_id"] = f["legislador_id"].map(lambda x: alias.get(x, x))
        logger.info("alias de legislador_id: %d ids distintos -> %d en las firmas",
                    antes, f["legislador_id"].nunique())

    car = _caracter_por_proyecto_camara(f)

    enlace = repo / ENLACE_TODAS
    if enlace.exists():
        ae = pd.read_parquet(enlace)
        ae = ae[ae["proyecto_id"].map(lambda x: str(x) if x is not None else "") != ""]
        mapa = (ae[["acta_id", "proyecto_id", "camara"]]
                .merge(car, on=["proyecto_id", "camara"], how="left"))
        mapa = mapa[["acta_id", "proyecto_id", "caracter"]].drop_duplicates("acta_id")
    else:
        # Fallback RUIDOSO a proposito. La tabla vieja es solo Diputados y deja al
        # Senado en cero: si se cae aca en silencio, el resultado parece un
        # hallazgo politico y es un archivo que falta.
        logger.error("falta %s (lo arma datos/expedientes/src/enlace_senado.py): "
                     "caigo a acta_expediente.parquet, que es SOLO DIPUTADOS y "
                     "deja al Senado sin actas", enlace.name)
        ae = pd.read_parquet(repo / "datos/expedientes/data/clean/acta_expediente.parquet")
        ex = pd.read_parquet(repo / "datos/expedientes/data/clean/expedientes.parquet")
        m = pd.concat([
            ex[["proyecto_id", "exp_diputados"]].rename(columns={"exp_diputados": "exp"}),
            ex[["proyecto_id", "exp_senado"]].rename(columns={"exp_senado": "exp"}),
        ]).dropna().drop_duplicates("exp")
        ae = ae.merge(m, left_on="expediente", right_on="exp", how="left")
        car_pid = car.drop_duplicates("proyecto_id")[["proyecto_id", "caracter"]]
        ae = ae.merge(car_pid, on="proyecto_id", how="left")
        mapa = ae[["acta_id", "proyecto_id", "caracter"]].dropna(subset=["proyecto_id"])
        mapa = mapa.drop_duplicates("acta_id")

    # SOLO dictamenes de MAYORIA o UNICO firman "a favor" del despacho que se vota.
    # Las firmas de MINORIA son del despacho alternativo: contarlas como apoyo seria
    # exactamente al reves de lo que significan. `desconocido` queda AFUERA a
    # proposito: no sabemos de que despacho es esa firma, y suponerlo seria
    # inventar el dato que falta. Se pierde cobertura, no se gana ruido.
    fav = f[f["dictamen_clase"].isin(["mayoria", "unico"])]
    firmas = fav[["proyecto_id", "legislador_id", "bloque_linaje"]].drop_duplicates()

    # nombre normalizado -> legislador_id, para resolver el roster de jefes (que viene
    # por NOMBRE) contra las firmas (que vienen por id).
    nom = f[["legislador", "legislador_id"]].dropna().drop_duplicates()
    nom["k"] = nom["legislador"].map(_clave_persona)
    # una clave que apunta a dos ids distintos es ambigua: se descarta antes que
    # inventar un match. Mejor perder cobertura que asignarle la firma a otra persona.
    cuenta = nom.groupby("k")["legislador_id"].nunique()
    buenas = set(cuenta[cuenta == 1].index)
    nom = nom[nom["k"].isin(buenas)]
    mapa_nombre = dict(zip(nom["k"], nom["legislador_id"]))
    return firmas, mapa, mapa_nombre


def jefes(repo: Path) -> pd.DataFrame:
    """Roster de jefes de bloque (curado historico + snapshot oficial)."""
    out = []
    for nombre in ("jefes_bloque.csv", "jefes_bloque_oficial.csv"):
        p = repo / "variables/proyecto/data" / nombre
        if p.exists():
            d = pd.read_csv(p, comment="#")
            d["_fuente_archivo"] = nombre
            out.append(d)
    if not out:
        return pd.DataFrame(columns=["nombre", "camara", "bloque", "desde", "hasta"])
    j = pd.concat(out, ignore_index=True)
    j["desde"] = pd.to_datetime(j["desde"], errors="coerce")
    j["hasta"] = pd.to_datetime(j["hasta"], errors="coerce").fillna(pd.Timestamp("2099-01-01"))
    j["k"] = j["nombre"].map(_clave_persona)
    # El id EXPLICITO del roster manda sobre el cruce por nombre (URGENTE 10,
    # 04-09-2026). El cruce laxo `APELLIDO|PRIMER-NOMBRE` resolvia 50 de 80: se le
    # escapaban las formas largas del Senado ("PETCOFF NAIDENOFF, LUIS CARLOS") y
    # el snapshot oficial, que escribe Diputados como "APELLIDO NOMBRES" y Senado
    # como "NOMBRES APELLIDO" — o sea que para los senadores tomaba el apellido
    # como nombre de pila. Se deja el cruce como respaldo para las filas sin id.
    if "legislador_id" not in j.columns:
        j["legislador_id"] = pd.NA
    j["legislador_id"] = j["legislador_id"].replace("", pd.NA)
    return j


# ---------------------------------------------------------------------------
# Armado del panel
# ---------------------------------------------------------------------------

def construir_panel(muestra: int = 0, seed: int = 7, camara: str = "") -> pd.DataFrame:
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta
    from baseline_voto_individual import perfil, _norm_cond, _ContadorAvisos

    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)

    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                if cond is not None and len(cond) else {})

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara:
        v = v[v["camara"] == camara]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")

    gp = v.groupby("legislador_id")["af"]
    v["record"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_prev"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    # DESVIO INDIVIDUAL walk-forward: con que frecuencia voto distinto de la mayoria de
    # su linaje en esa acta. Es d_i, y hace falta para el termino (1-d_i)*J_l.
    lin = (v.groupby(["acta_id", "bloque_linaje"])["af"]
             .agg(["mean", "size"]).reset_index())
    lin = lin[lin["size"] >= 3]
    lin["linea_lin"] = (lin["mean"] >= 0.5).astype(int)
    v = v.merge(lin[["acta_id", "bloque_linaje", "linea_lin"]],
                on=["acta_id", "bloque_linaje"], how="left")
    v["_desvio_obs"] = (v["af"] != v["linea_lin"]).astype(float)
    v.loc[v["linea_lin"].isna(), "_desvio_obs"] = np.nan
    gd = v.groupby("legislador_id")["_desvio_obs"]
    v["d_i"] = gd.transform(lambda s: s.shift(1).expanding().mean())

    firmas, mapa, mapa_nombre = firmas_por_acta(REPO)
    firmantes = firmas.groupby("proyecto_id")["legislador_id"].apply(set).to_dict()
    lin_firm = firmas.groupby("proyecto_id")["bloque_linaje"].apply(set).to_dict()

    j = jefes(REPO)
    explicito = j["legislador_id"].notna()
    j["legislador_id"] = j["legislador_id"].fillna(j["k"].map(mapa_nombre))
    # los DOS lados del cruce pasan por el alias, o no sirve de nada normalizar uno solo
    alias = cargar_alias()
    if alias:
        j["legislador_id"] = j["legislador_id"].map(lambda x: alias.get(x, x) if x else x)
    n_res = int(j["legislador_id"].notna().sum())
    logger.info("jefes de bloque resueltos a legislador_id: %d/%d (%d por id explicito "
                "del roster, %d por cruce de nombre)", n_res, len(j), int(explicito.sum()),
                n_res - int(explicito.sum()))

    # actas que tienen dictamen identificado: es donde se puede estimar
    mapa = mapa[mapa["caracter"].notna()]
    v = v.merge(mapa, on="acta_id", how="inner")

    actas = (v[["acta_id", "fecha", "camara", "proyecto_id", "caracter"]]
             .drop_duplicates("acta_id").sort_values("fecha"))
    piso = votos["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)
    actas = actas[actas["fecha"] >= piso]
    if muestra:
        actas = actas.sample(min(muestra, len(actas)), random_state=seed).sort_values("fecha")
    logger.info("actas con dictamen a evaluar: %d", len(actas))

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cache: dict = {}
    filas = []

    for k, a in enumerate(actas.itertuples(), 1):
        if k % 200 == 0:
            logger.info("  %d/%d actas (cache=%d)", k, len(actas), len(cache))
        info = cond_map.get(str(a.acta_id), {})
        tema = _norm_cond(info.get("tema_area"))
        origen = _norm_cond(info.get("origen"))
        clave = (a.camara, a.fecha.year, a.fecha.month, tema, origen)
        if clave not in cache:
            try:
                post = proyectar_postura(votos, a.fecha, a.camara,
                                         ventana_dias=VENTANA_DIAS, tema=tema,
                                         origen=origen, cond_por_acta=cond,
                                         k_shrink=K_SHRINK)
                cache[clave] = {p["bloque"]: p for p in post}
            except (ValueError, KeyError):
                cache[clave] = None
        by_lin = cache[clave]
        if by_lin is None:
            continue

        firm = firmantes.get(a.proyecto_id, set())
        lins_firm = lin_firm.get(a.proyecto_id, set())
        # jefes vigentes a la fecha, por linaje: se resuelve por NOMBRE del bloque
        # J_l CORRECTO: linajes cuyo JEFE (persona concreta, resuelta por nombre->id)
        # figura entre los firmantes del dictamen. La version anterior marcaba
        # "mi linaje firmo", que daba 81,5% y no es lo que dice el ADR.
        jefes_hoy = j[(j["camara"] == a.camara) & (j["desde"] <= a.fecha)
                      & (j["hasta"] >= a.fecha) & j["legislador_id"].notna()]
        ids_jefes_firmantes = set(jefes_hoy["legislador_id"]) & firm
        lin_de = firmas[firmas["proyecto_id"] == a.proyecto_id]
        lin_jefe = set(lin_de[lin_de["legislador_id"].isin(ids_jefes_firmantes)]
                       ["bloque_linaje"].astype(str))
        # W_{-l}: bancas de los OTROS linajes firmantes sobre el total de la camara
        bancas_lin = {p["bloque"]: p.get("bancas", 0) or 0 for p in by_lin.values()}
        M = BANCAS.get(a.camara, 257)

        sub = por_acta.get(a.acta_id)
        if sub is None:
            continue
        for r in sub.itertuples():
            p = by_lin.get(str(r.bloque_linaje))
            if p is None:
                continue
            pi = perfil(p["_share_afirm"], p["desvio"], r.record, r.n_prev)
            d_i = r.d_i if not pd.isna(r.d_i) else p["desvio"]
            w_otros = sum(b for l, b in bancas_lin.items()
                          if l in lins_firm and l != str(r.bloque_linaje)) / M
            # J_l: el jefe de SU linaje firmo el dictamen (persona concreta).
            jefe_firmo = int(str(r.bloque_linaje) in lin_jefe)
            filas.append({
                "acta_id": a.acta_id, "fecha": a.fecha, "camara": a.camara,
                "legislador_id": r.legislador_id, "linaje": str(r.bloque_linaje),
                "y": int(r.af), "p_motor": pi, "caracter": a.caracter,
                "F_i": int(r.legislador_id in firm),
                "J_l": jefe_firmo,
                "d_i": float(d_i),
                "W_otros": float(w_otros),
                "linaje_firmo": int(str(r.bloque_linaje) in lins_firm),
                "tema": tema or "SIN_TEMA", "origen": origen or "SIN_ORIGEN",
            })

    d = pd.DataFrame(filas)
    d.attrs["avisos"] = dict(cont.tally)
    return d


# ---------------------------------------------------------------------------
# Estimacion
# ---------------------------------------------------------------------------

def estimar(d: pd.DataFrame) -> dict:
    import statsmodels.api as sm

    d = d.copy()
    d["offset"] = _logit(d["p_motor"])
    d["lealtad_x_jefe"] = (1 - d["d_i"]) * d["J_l"]
    # caracter: UNICO como referencia
    dummies = pd.get_dummies(d["caracter"], prefix="dict", drop_first=False)
    for c in ["dict_UNICO"]:
        if c in dummies:
            dummies = dummies.drop(columns=[c])

    def ajustar(X, offset=None, nombre=""):
        X = sm.add_constant(X.astype(float), has_constant="add")
        try:
            mod = sm.GLM(d["y"].astype(float), X,
                         family=sm.families.Binomial(),
                         offset=(offset.astype(float) if offset is not None else None))
            r = mod.fit(cov_type="cluster", cov_kwds={"groups": d["acta_id"]})
        except Exception as e:  # noqa: BLE001 - queremos el motivo en el reporte
            return {"error": f"{type(e).__name__}: {e}"}
        return {
            "n": int(r.nobs),
            "coef": {k: round(float(v), 4) for k, v in r.params.items()},
            "se_cluster_acta": {k: round(float(v), 4) for k, v in r.bse.items()},
            "p": {k: round(float(v), 5) for k, v in r.pvalues.items()},
            "llf": round(float(r.llf), 1),
        }

    res = {}
    # M0: crudo, sin offset -> reproduce el contraste del 03-09
    res["M0_crudo"] = ajustar(dummies)
    # M1: con offset del motor
    res["M1_offset"] = ajustar(dummies, offset=d["offset"])
    # M2: + tema y origen
    ctrl = pd.concat([dummies,
                      pd.get_dummies(d["tema"], prefix="t", drop_first=True),
                      pd.get_dummies(d["origen"], prefix="o", drop_first=True)], axis=1)
    res["M2_offset_tema_origen"] = ajustar(ctrl, offset=d["offset"])
    # M3: la formulacion del ADR — F_i, lealtad x jefe, W_otros
    adr = d[["F_i", "lealtad_x_jefe", "W_otros"]]
    res["M3_ADR_por_legislador"] = ajustar(adr, offset=d["offset"])
    # M4: la del ADR + caracter, para ver si sobra alguno
    res["M4_ADR_mas_caracter"] = ajustar(pd.concat([adr, dummies], axis=1),
                                         offset=d["offset"])

    # CUANTOS CLUSTERS SOSTIENE CADA DUMMY. El error estandar es cluster-robusto POR
    # ACTA, y eso significa que el numero de ACTAS —no de votos— es lo que le da sentido.
    #
    # El 06-09-2026 la corrida del Senado devolvio `dict_solo_minoria = +2,5026` con
    # `p = 0,0` y un error estandar de 0,157, del mismo orden que el de la constante.
    # Ese coeficiente sale de **UN acta** (53 votos de senado-2010-54.pdf). Un error
    # estandar cluster-robusto con UN cluster no es un error estandar: es un artefacto,
    # y con p = 0,0 al lado se lee como el hallazgo mas fuerte de la tabla.
    #
    # Regla de la casa: un numero imposible es un bug, no un fenomeno. Asi que el
    # reparto ahora se publica en ACTAS ademas de en votos, y se avisa fuerte debajo
    # del piso. El piso es 20 por convencion (la literatura pide 30-50 para inferencia
    # cluster-robusta; abajo de 20 el error estandar directamente no significa nada).
    por_caracter = d.groupby("caracter").agg(votos=("acta_id", "size"),
                                             actas=("acta_id", "nunique"))
    flacos = por_caracter[por_caracter["actas"] < MIN_CLUSTERS_CONFIABLE]
    for cat, r in flacos.iterrows():
        logger.error(
            "CARACTER %r se apoya en %d acta(s) (%d votos). El error estandar es "
            "cluster-robusto POR ACTA: con menos de %d clusters su SE y su p NO son "
            "interpretables. NO leas dict_%s como un hallazgo.",
            cat, int(r["actas"]), int(r["votos"]), MIN_CLUSTERS_CONFIABLE, cat)

    res["_descriptivos"] = {
        "n_votos": int(len(d)),
        "n_actas": int(d.acta_id.nunique()),
        "actas_por_caracter": {k: int(v) for k, v in por_caracter["actas"].items()},
        "caracter_sin_clusters_suficientes": {
            k: int(v) for k, v in flacos["actas"].items()},
        "min_clusters_confiable": MIN_CLUSTERS_CONFIABLE,
        "tasa_afirmativa": round(float(d.y.mean()), 4),
        "reparto_caracter": {k: int(v) for k, v in d.caracter.value_counts().items()},
        "firmantes_en_el_recinto": int(d.F_i.sum()),
        "share_F_i": round(float(d.F_i.mean()), 4),
        "share_J_l": round(float(d.J_l.mean()), 4),
        "share_mi_linaje_firmo": round(float(d.linaje_firmo.mean()), 4),
        "W_otros_medio": round(float(d.W_otros.mean()), 4),
        "d_i_medio": round(float(d.d_i.mean()), 4),
    }
    return res


def _exigir_statsmodels() -> None:
    """Falla en el segundo 1, no en el minuto 9.

    El 06-09-2026 este script murio con `ModuleNotFoundError: No module named
    'statsmodels'` DESPUES de procesar 1.556 actas (9,2 min), porque el import esta
    adentro de `estimar()`, que es la ultima cosa util que hace el programa. La regla
    que dejo: lo que puede fallar en el segundo 1 no puede fallar en el minuto 9.
    """
    import importlib.util
    if importlib.util.find_spec("statsmodels") is None:
        raise SystemExit(
            "falta statsmodels, y este script no sirve sin el.\n"
            "    python -m pip install statsmodels\n"
            "Chequeo completo de dependencias:  python verificar_dependencias.py")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--muestra", type=int, default=0)
    ap.add_argument("--camara", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    _exigir_statsmodels()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    d = construir_panel(args.muestra, args.seed, args.camara)
    if d.empty:
        raise SystemExit("panel vacio: ninguna acta con dictamen identificado")
    res = estimar(d)
    res["_avisos"] = d.attrs.get("avisos", {})
    res["_args"] = vars(args)

    out = Path(args.salida) if args.salida else (
        REPO / "modelo/ensemble/outputs/beta_dictamen.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
