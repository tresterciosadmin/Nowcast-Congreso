"""Puerta D — voto en la cámara REVISORA.

¿Un proyecto que ya tiene media sanción consigue mayoría en la cámara que lo
revisa? Ficha completa y decisiones en `modelo/ensemble/PUERTA-D.md`.

QUÉ HACE, EN UNA FRASE
    Corre el mismo agregador que la cámara de origen (Puerta B), pero sobre el
    roster de la OTRA cámara a la fecha de la votación, y le suma un ajuste
    "pasó por origen" encogido por muestra (hoy = 0, o sea Manera 1 pura).

NO REIMPLEMENTA NADA
    - roster point-in-time + escalera de desvío  -> ensemble.roster_nominal
    - simulación del recuento                     -> agregador.simular_votacion
    - postura de bloque por tema/origen           -> bloque.proyectar_postura
    Este módulo sólo: (1) elige la cámara revisora, (2) apunta al padrón correcto
    (el HISTÓRICO del Senado), (3) aplica el ajuste escalar.

MANERA 1 vs MANERA 2 (decisión de Valle 2026-08-09)
    Manera 1: sólo la composición de la revisora.
    Manera 2: además, que ya pasó por origen mueve el número (`delta` en logit).
    El fallback a Manera 1 NO es un if: es el límite de Manera 2 cuando el
    encogimiento lleva `delta` a 0 por falta de muestra. Hoy `delta=0` fijo; el
    enganche del ajuste queda como hook (`estimar_delta_paso_origen`, pendiente).

Módulo: modelo/ensemble · creado 2026-08-09 (reconstrucción por puertas)
"""
from __future__ import annotations

import logging
import math
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s puerta_d: %(message)s")
logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
PADRON_SENADO_HIST = RAIZ / "datos" / "padron" / "data" / "padron_senado_historico.csv"
PADRON_DIP = RAIZ / "datos" / "padron" / "data" / "padron_diputados.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))  # ensemble/src (roster_nominal)


def camara_revisora(camara_origen: str) -> str:
    """La revisora es la otra cámara. Única fuente de esta regla en el módulo."""
    c = str(camara_origen).strip().lower()
    if c in ("diputados", "camara de diputados", "hcdn", "d"):
        return "senado"
    if c in ("senado", "camara de senadores", "hcsn", "s"):
        return "diputados"
    raise ValueError(f"camara_origen no reconocida: {camara_origen!r} "
                     "(esperaba 'diputados' o 'senado')")


def _padron_de(camara: str) -> Path:
    """El padrón point-in-time de la cámara. Para el Senado, el HISTÓRICO
    (2017→2031); para Diputados, el oficial que ya trae los tramos."""
    return PADRON_SENADO_HIST if str(camara).lower() == "senado" else PADRON_DIP


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def ajuste_paso_origen(p0: float, delta: float, factor_encogimiento: float = 1.0) -> float:
    """Aplica el ajuste 'pasó por origen' sobre la probabilidad base, en logit.

    `delta` es el corrimiento crudo (en log-odds) estimado sobre los casos de dos
    cámaras. `factor_encogimiento` ∈ [0,1] lo atenúa según la muestra: 0 = sin
    datos -> Manera 1 pura; 1 = muestra suficiente -> efecto pleno. El fallback a
    Manera 1 es exactamente `delta*factor == 0`, no un camino aparte.
    """
    fe = _clip01(factor_encogimiento)
    if delta == 0.0 or fe == 0.0:
        return _clip01(p0)
    return _clip01(_sigmoide(_logit(p0) + delta * fe))


def posturas_revisora(fecha, camara, *, tema=None, origen=None, canon=None) -> list[dict]:
    """Posturas de bloque (línea + desvío por linaje) para `camara` en `fecha`.

    Reusa `variables/bloque.proyectar_postura` — la MISMA maquinaria que la
    cámara de origen (Puerta B), condicionada por tema/origen. Se toma sólo
    `linea` y `desvio`; las bancas de la revisora las pone `roster_nominal`
    desde el padrón histórico, no esta función. Por eso es seguro en fechas
    pasadas aunque el padrón oficial no las cubra (proyectar_postura cae a
    contar por la ventana de votos).
    """
    from ensemble import _cargar_proyector
    cargar_bloque, proyectar_postura, cargar_tema_por_acta = _cargar_proyector()
    votos = cargar_bloque() if canon is None else cargar_bloque(canon)

    # EL NORTE DEL MODELO (Valle 2026-08-09): la postura de bloque se calcula SÓLO
    # sobre actas de ley. Sin este filtro, el consenso de tratados/pliegos/
    # homenajes lava la señal: el kirchnerismo sale 55,8% afirmativo (dirección
    # AFIRMATIVO, degenerado) en vez del 29% real sobre leyes. Ver actas_ley.py.
    exp_src = RAIZ / "datos" / "expedientes" / "src"
    if str(exp_src) not in sys.path:
        sys.path.insert(0, str(exp_src))
    from actas_ley import filtrar_votos_a_ley  # type: ignore
    votos = filtrar_votos_a_ley(votos)

    cond = cargar_tema_por_acta() if (tema or origen) else None
    return proyectar_postura(votos, fecha, camara, tema=tema, origen=origen,
                             cond_por_acta=cond)


def p_voto_revisora(
    camara_origen: str,
    fecha,
    bloques: Optional[list[dict]] = None,
    *,
    tema=None,
    origen=None,
    canon=None,
    tipo_mayoria: str = "SIMPLE",
    delta: float = 0.0,
    factor_encogimiento: float = 0.0,
    n_sims: int = 400,
    seed: Optional[int] = 0,
    padron_file: Optional[str] = None,
    disciplina_path: Optional[str] = None,
) -> dict:
    """P(mayoría en la cámara revisora) para un proyecto con media sanción.

    camara_origen : de dónde salió el proyecto; la revisora es la otra.
    fecha         : fecha de la votación en la revisora (o proyectada).
    bloques       : posturas por linaje ([{bloque, linea, desvio}, ...]). Si es
                    None (lo normal), se derivan solas de tema/origen con
                    `posturas_revisora` (misma maquinaria que B). Se pasan a mano
                    sólo para escenarios "¿y si…?" o para los tests.
    tema, origen  : condicionan las posturas de bloque (área temática y quién
                    impulsa). Sólo se usan cuando `bloques` es None.
    delta, factor_encogimiento : ajuste 'pasó por origen'. Por defecto (0,0) =
                    Manera 1 pura. Cuando se ajuste Manera 2, se pasan acá.

    Devuelve dict con p_aprobacion (ya ajustada), p0 (base), camara_revisora,
    manera ('1' | '2'), n_roster y el detalle del roster.
    """
    from ensemble import roster_nominal  # contrato del propio módulo
    agg = RAIZ / "modelo" / "agregador_institucional" / "src"
    if str(agg) not in sys.path:
        sys.path.insert(0, str(agg))
    from agregador import simular_votacion  # type: ignore

    revisora = camara_revisora(camara_origen)
    if bloques is None:
        bloques = posturas_revisora(fecha, revisora, tema=tema, origen=origen, canon=canon)
    pfile = padron_file or str(_padron_de(revisora))
    if not Path(pfile).exists():
        raise FileNotFoundError(
            f"falta el padrón de la revisora ({revisora}): {pfile}\n"
            "  para el Senado hace falta padron_senado_historico.csv "
            "(datos/padron/src/padron_senado_historico.py)")

    lineas, desvios, detalle = roster_nominal(
        revisora, fecha, bloques,
        padron_file=pfile, disciplina_path=disciplina_path)

    sim = simular_votacion(lineas, desvios, tipo_mayoria, revisora,
                           n_sims=n_sims, seed=seed)
    p0 = float(sim["p_aprobacion"])
    p_aj = ajuste_paso_origen(p0, delta, factor_encogimiento)

    usa_manera2 = not (delta == 0.0 or _clip01(factor_encogimiento) == 0.0)
    return {
        "p_aprobacion": p_aj,
        "p0": p0,
        "delta_aplicado": float(delta) * _clip01(factor_encogimiento),
        "manera": "2" if usa_manera2 else "1",
        "camara_origen": str(camara_origen).lower(),
        "camara_revisora": revisora,
        "fecha": str(fecha),
        "tipo_mayoria": tipo_mayoria,
        "n_roster": int(detalle["n"]),
        "afirm_medio": float(sim["afirm_medio"]),
        "umbral_medio": float(sim["umbral_medio"]),
        "roster_detalle": detalle,
    }


def estimar_delta_paso_origen(*args, **kwargs):
    """HOOK de Manera 2 — pendiente.

    Ajustar `delta` (corrimiento en logit) y su factor de encogimiento sobre los
    ~243 proyectos con votación en las dos cámaras (`cadena_camaras.parquet`),
    excluyendo los `es_omnibus`, por taxonomía/origen si la muestra alcanza. Ver
    PUERTA-D.md. Hasta que exista, `p_voto_revisora` corre en Manera 1 (delta=0).
    """
    raise NotImplementedError(
        "Manera 2 pendiente: ajustar delta sobre cadena_camaras.parquet "
        "(sin ómnibus, encogido por muestra). Hoy el modelo corre en Manera 1.")


if __name__ == "__main__":
    # Demo autocontenida: no toca disco real, muestra la forma de la salida.
    demo_bloques = [
        {"bloque": "FdT-UxP (kirchnerismo)", "linea": "NEGATIVO", "desvio": 0.03},
        {"bloque": "LA LIBERTAD AVANZA", "linea": "AFIRMATIVO", "desvio": 0.02},
    ]
    print("Puerta D — demo (requiere padrón real para correr de verdad)")
    print("camara_revisora('Diputados') =", camara_revisora("Diputados"))
    print("ajuste_paso_origen(0.60, delta=0.4, fe=0.0) =",
          round(ajuste_paso_origen(0.60, 0.4, 0.0), 4), "(Manera 1: sin cambio)")
    print("ajuste_paso_origen(0.60, delta=0.4, fe=1.0) =",
          round(ajuste_paso_origen(0.60, 0.4, 1.0), 4), "(Manera 2: sube)")
