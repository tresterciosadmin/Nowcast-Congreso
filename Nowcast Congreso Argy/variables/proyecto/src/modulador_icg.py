"""modulador_icg.py — el ICG entra al nowcast en DOS HORIZONTES, legislador por legislador.

Revisión 2026-08-11 (Valle). Antes había dos vías: (A) individual medida y (B) un
multiplicador GLOBAL que fijaba el analista. **La vía B se eliminó**: como estaba
cableada, la perilla del analista y el efecto medido multiplicaban la MISMA señal
(el ICG del mes contra un neutro), o sea contaban dos veces el mismo clima. Nos
quedamos SOLO con lo medido, legislador por legislador.

Y lo medido cambió de forma: en vez de reaccionar al ICG del mes suelto (que
rebota mucho y SUBESTIMA el efecto por atenuación), cada legislador reacciona a
DOS horizontes que no se pisan (ver icg_contexto.py):

    FONDO  (mediano plazo, media móvil 6m vs promedio del gobierno) -> z_fondo
    CORTO  (sacudón reciente, media móvil 3m vs el fondo)           -> z_corto

Matemática, por capa (se multiplican las CHANCES, no la probabilidad):

    odds' = odds * exp(gamma * s * z)
    logit(p') = logit(p) + gamma * s * z

`s` = +1 si el proyecto lo impulsa el gobierno, -1 la oposición, 0 consenso.
Las dos capas se componen: primero el fondo, después el corto.

`gamma` depende de cuán BISAGRA sea cada legislador (dose-response por tramo de
desvío) y de la capa. Los valores salen de `estimar_gamma_individual.py --modelo
dos_capas` (outputs/gamma_icg_dos_capas.json); si falta ese archivo se usan los
provisionales de la exploración del 2026-08-11 (punto, sin IC).

4 directivas: errores específicos, sin red (lee sólo de disco local), parsing
defensivo, logging.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("icg.modulador")

_OUT = Path(__file__).resolve().parents[1] / "outputs" / "gamma_icg_dos_capas.json"

# CAPA CORTO (sacudón 3m) APAGADA (Valle, 2026-08-11): la corrida oficial con
# bootstrap NO pudo distinguir su efecto de cero (IC muy anchos en todos los
# tramos). No se publica lo que no está medido con confianza. El fondo (6m) SÍ
# quedó sólido y significativo (0,44 / 0,48 / 0,51). Con el corto apagado, el
# modelo es de hecho un único suavizado de 6 meses. Poner True sólo si una corrida
# futura confirma significancia del corto.
USAR_CORTO = False

# --- dose-response PROVISIONAL (fallback si falta el JSON oficial). La corrida de
# Valle reescribe el JSON y estos valores dejan de usarse. Tramos: el <0.10 es el
# NÚCLEO DURO medido aparte; los demás son acumulados (>=x).
# núcleo duro (0.00) = valor medido sobre <0.10 (~-0.07), sin piso — ver nota abajo.
_PROV_FONDO = [(0.40, 0.400), (0.30, 0.509), (0.20, 0.477), (0.10, 0.443), (0.00, -0.069)]
_PROV_CORTO = [(0.40, 0.552), (0.30, 0.575), (0.20, 0.318), (0.10, 0.270), (0.00, 0.000)]

# el tramo 0.00 (núcleo duro) lee la banda "<0.10" del JSON, no "TODOS": medir el
# disciplinado mezclado con las bisagras daría otro número (Valle, 2026-08-11).
_CLAVE_TRAMO = {0.40: ">=0.40", 0.30: ">=0.30", 0.20: ">=0.20", 0.10: ">=0.10", 0.00: "<0.10"}


def _cargar_tramos() -> tuple[list, list, str]:
    """Devuelve (TRAMOS_FONDO, TRAMOS_CORTO, fuente). Lee la dose-response oficial;
    si el JSON no está o está roto, cae a los provisionales sin explotar. Si
    USAR_CORTO es False, la capa corto queda en cero (apagada)."""
    if not _OUT.exists():
        fondo, corto, fuente = _PROV_FONDO, _PROV_CORTO, "provisional"
    else:
        try:
            j = json.loads(_OUT.read_text(encoding="utf-8"))
            t = j["tramos"]
            fondo, corto = [], []
            for u in (0.40, 0.30, 0.20, 0.10, 0.00):
                k = _CLAVE_TRAMO[u]
                if u == 0.00 and k not in t and "TODOS" in t:
                    k = "TODOS"      # JSON viejo (previo al 2026-08-11): núcleo duro = TODOS
                if k not in t:
                    continue
                # se toma el valor MEDIDO tal cual, SIN piso (decisión de Valle,
                # 2026-08-11): "no significativo" no es "cero". El núcleo duro
                # (<0.10) da ~-0.07 — un nudge minúsculo y de signo dudoso. ⚠️ HAY
                # QUE VALIDARLO mes a mes para ver si se condice (ver ESTADO). Los
                # tramos de bisagra (>=0.10) son positivos y significativos.
                fondo.append((u, float(t[k]["gamma_fondo"]["punto"])))
                corto.append((u, float(t[k]["gamma_corto"]["punto"])))
            if not fondo:
                raise KeyError("tramos de fondo vacíos")
            fuente = "oficial(json)"
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning("no pude leer %s (%s); uso dose-response provisional", _OUT.name, e)
            fondo, corto, fuente = _PROV_FONDO, _PROV_CORTO, "provisional"
    if not USAR_CORTO:
        corto = [(u, 0.0) for u, _ in (corto or fondo)]   # capa corto apagada
    return fondo, corto, fuente


TRAMOS_FONDO, TRAMOS_CORTO, FUENTE_TRAMOS = _cargar_tramos()
logger.info("dose-response del ICG: fuente=%s", FUENTE_TRAMOS)

K_SHRINK = 5.0        # pseudo-conteo; mismo valor que variables/bloque (proyectar_postura)
MIN_DISPUTADAS = 10   # por debajo de esto el desvio propio no alcanza para un tramo


def encoger_desvio(desvio, n_disputadas, prior: float, k: float = K_SHRINK) -> float:
    """Desvio ENCOGIDO hacia un `prior` (la mediana de su bloque), con peso
    proporcional a cuantas votaciones disputadas lo respaldan.

        desvio' = (n * desvio_obs + k * prior) / (n + k)

    POR QUE (detectado 2026-08-07). Los 104 diputados de la camada dic-2025 tienen
    **mediana de 2 votaciones disputadas** contra 47 de los veteranos. Con 2
    observaciones el desvio solo puede valer 0, 0,5 o 1 — y los TRAMOS cortan en
    0,10 / 0,20 / 0,30 / 0,40, asi que es **aritmeticamente imposible caer en los
    tramos intermedios**: o se cae al piso o se salta al techo. Se corrige con
    encogimiento empirico-bayesiano.

    Con k=5 y n=2 el dato propio pesa 29% y el prior 71%; con n=47 pesa 90%.
    """
    # Guardas con pd.isna(): reconoce None, float('nan') Y pd.NA (backend pyarrow).
    # `isinstance(x, float) and np.isnan(x)` NO cazaba pd.NA y explotaba en la PC de
    # Valle (bug del 2026-08-08, ver ESTADO).
    if pd.isna(desvio):
        return float(prior)
    n = 0.0 if pd.isna(n_disputadas) else float(n_disputadas)
    return (n * float(desvio) + k * float(prior)) / (n + k)


def _gamma_tramo(desvio: float, tabla: list) -> float:
    """gamma de UNA capa según cuán bisagra es el legislador. NaN -> disciplinado."""
    if pd.isna(desvio):     # None / nan / pd.NA (ver nota en encoger_desvio)
        desvio = 0.0
    for umbral, g in tabla:
        if desvio >= umbral:
            return g
    return 0.0


def gamma_fondo(desvio: float) -> float:
    """gamma de la capa de FONDO (mediano plazo, 6m)."""
    return _gamma_tramo(desvio, TRAMOS_FONDO)


def gamma_corto(desvio: float) -> float:
    """gamma de la capa de CORTO (sacudón reciente, 3m)."""
    return _gamma_tramo(desvio, TRAMOS_CORTO)


def _mover(p, gamma, s, z):
    """logit(p) + gamma*s*z, con los bordes protegidos."""
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    odds = p / (1 - p) * np.exp(np.asarray(gamma) * s * z)
    return odds / (1 + odds)


def aplicar_individual(legisladores: pd.DataFrame, s: float,
                       z_fondo: float, z_corto: float,
                       encoger: bool = True, k: float = K_SHRINK) -> pd.DataFrame:
    """Aplica las DOS capas del ICG legislador por legislador.

    `legisladores` necesita `p_acompana` y `desvio`. Si trae `n_disputadas` (y
    opcionalmente `bloque`), el desvio se ENCOGE hacia la mediana de su bloque
    antes de mapearlo a un tramo — ver `encoger_desvio`.

    `z_fondo` y `z_corto` son las dos señales del ICG para el mes objetivo (de
    icg_contexto: columnas z_fondo / z_corto). Se componen: primero el fondo,
    después el corto.

    Devuelve el frame con `gamma_fondo`, `gamma_corto`, `p_mod`, `delta`
    (y `desvio_enc` si se encogió).
    """
    faltan = {"p_acompana", "desvio"} - set(legisladores.columns)
    if faltan:
        raise ValueError(f"faltan columnas {sorted(faltan)}")
    d = legisladores.copy()

    col = "desvio"
    if encoger and "n_disputadas" in d.columns:
        # El prior se calcula SOLO con legisladores de muestra suficiente (si no,
        # los novatos se encogen hacia el ruido de sus propios pares novatos).
        nd = pd.to_numeric(d["n_disputadas"], errors="coerce").fillna(0)
        solido = d[nd >= MIN_DISPUTADAS]
        if solido.empty:
            solido = d
        base = float(solido["desvio"].median())
        if "bloque" in d.columns:
            med = solido.groupby("bloque")["desvio"].median()
            prior = d["bloque"].map(med).astype(float).fillna(base)
        else:
            prior = pd.Series(base, index=d.index)
        d["desvio_enc"] = [
            encoger_desvio(dv, n, pr, k)
            for dv, n, pr in zip(d["desvio"], d["n_disputadas"], prior)
        ]
        col = "desvio_enc"
        flojos = int((nd < MIN_DISPUTADAS).sum())
        if flojos:
            logger.info("encogimiento aplicado (k=%.1f): %d de %d legisladores "
                        "tienen menos de %d disputadas", k, flojos, len(d), MIN_DISPUTADAS)
    elif encoger:
        logger.warning("sin columna `n_disputadas`: no puedo encoger el desvio. "
                       "Un legislador con 2 votaciones recibe el mismo trato que "
                       "uno con 47 (ver encoger_desvio).")

    d["gamma_fondo"] = d[col].map(gamma_fondo)
    d["gamma_corto"] = d[col].map(gamma_corto)
    p1 = _mover(d["p_acompana"].values, d["gamma_fondo"].values, s, z_fondo)  # capa fondo
    d["p_mod"] = _mover(p1, d["gamma_corto"].values, s, z_corto)              # capa corto
    d["delta"] = d["p_mod"] - d["p_acompana"]
    return d


def zetas_del_mes(fecha, contexto_path: Path | None = None) -> tuple[float, float]:
    """(z_fondo, z_corto) del ICG para un mes dado, leídas de icg_contexto.parquet.

    `fecha` puede ser 'YYYY-MM' / 'YYYY-MM-DD' / Timestamp. Es el modo point-in-time
    de conseguir las dos señales para un nowcast: el mes objetivo ya vive en la
    serie. Levanta KeyError si el mes no está en el contexto.
    """
    path = contexto_path or (Path(__file__).resolve().parents[1] / "data" / "icg_contexto.parquet")
    ctx = pd.read_parquet(path)
    mes = pd.Timestamp(fecha).to_period("M")
    fila = ctx[pd.to_datetime(ctx["fecha"]).dt.to_period("M") == mes]
    if fila.empty:
        raise KeyError(f"el mes {mes} no está en {path.name}; ¿corriste icg_contexto.py?")
    r = fila.iloc[0]
    return float(r["z_fondo"]), float(r["z_corto"])


def votos_esperados(d: pd.DataFrame, col="p_mod") -> tuple[float, float]:
    """Media y desvio del recuento, tratando cada voto como Bernoulli independiente."""
    p = d[col].values
    return float(p.sum()), float(np.sqrt((p * (1 - p)).sum()))


def p_mayoria(d: pd.DataFrame, umbral: float, col="p_mod", n: int = 20000,
              semilla: int = 7) -> float:
    """P(los afirmativos alcanzan el umbral), por Monte Carlo."""
    rng = np.random.default_rng(semilla)
    p = d[col].values
    sim = (rng.random((n, len(p))) < p).sum(axis=1)
    return float((sim >= umbral).mean())
