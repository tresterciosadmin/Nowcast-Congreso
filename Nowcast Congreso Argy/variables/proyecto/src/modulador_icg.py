"""modulador_icg.py — las DOS formas de meter el ICG en el nowcast.

Ninguna se descarta: el equipo decide con evidencia. Las dos comparten la misma
matemática —se multiplican las CHANCES, no la probabilidad— y se diferencian en
DÓNDE se aplican y en qué evidencia se apoyan.

    odds' = odds x k        k = (ICG_c / ICG_0) ^ (gamma * s)
    logit(p') = logit(p) + gamma * s * log_rel

`s` = +1 si el proyecto lo impulsa el gobierno, -1 la oposicion, 0 consenso.
`log_rel` = log del ICG relativo al promedio del propio gobierno (point-in-time).

## Vía A — INDIVIDUAL (estimada)
Se aplica legislador por legislador ANTES de agregar, con gamma segun cuan
bisagra sea cada uno. Respeta el cimiento del proyecto (las partes hacen al
todo) y descansa en un efecto MEDIDO:

    desvio >= 0.40 -> gamma 0.555   (IC95 [0.39, 0.78])
    desvio >= 0.30 -> gamma 0.354   (IC95 [0.17, 0.51])
    desvio >= 0.20 -> gamma 0.333   (IC95 [0.13, 0.46])
    desvio >= 0.10 -> gamma 0.220   (IC95 [0.06, 0.34])
    resto          -> gamma 0.094   (IC95 [-0.03, 0.24])  NO significativo

El patron es dosis-respuesta: gamma crece monotonamente con el desvio y se
mantiene significativo mientras la muestra cae de 410k votos a 22k. En la camara
de hoy: 51 legisladores con desvio >=0.10, 23 con >=0.20, 8 con >=0.40.

**Lo conservador es aplicar gamma SOLO a los tramos significativos** (>=0.10) y
dejar el resto en cero: eso da ~+3 votos de swing punta a punta. Si se acepta el
gradiente completo, el swing llega a ~12 votos sobre 257.

## Vía B — ESCENARIO DECLARADO (no estimada)
Un desplazamiento sobre el resultado agregado que el analista **declara**, no que
el modelo estima. Existe porque el test a nivel camara dio cero y porque, como
planteo Valle, hay causalidades politicas que no dejan huella estadistica con 25
años de datos y seis gobiernos: el clima del recinto, la expectativa de lo que
viene, el costo de oponerse a un gobierno con viento a favor.

**No se presenta como prediccion, se presenta como banda.** No decimos "el ICG
lleva el 57% a 67%": decimos "con este clima, entre 118 y 126 votos". La
honestidad del producto depende de no confundir lo medido con lo supuesto.

`INTENSIDAD` traduce una postura del analista en un gamma agregado. Son valores
DECLARADOS, no estimados — cambiarlos es una decision de equipo, no un ajuste.

4 directivas: errores especificos, sin red, parsing defensivo, logging.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger("icg.modulador")

# --- Via A: gamma por tramo de desvio (ESTIMADO, ver estimar_gamma_individual) ---
TRAMOS = [(0.40, 0.555), (0.30, 0.354), (0.20, 0.333), (0.10, 0.220), (0.00, 0.094)]
SIGNIFICATIVO_DESDE = 0.10          # por debajo de esto el IC cruza el cero

# DECISION DE VALLE (04-08-2026): el default INCLUYE a los disciplinados
# (`solo_significativo=False`). Razon sustantiva: un disciplinado tambien traiciona
# de vez en cuando, y esas pocas defecciones son justo las que definen una votacion
# al filo. Razon estadistica: excluirlos NO es la opcion "prudente" — es fijar su
# gamma en 0, que esta en el BORDE del intervalo [-0,03; +0,24]. El 0,094 estimado
# es el valor central, o sea la mejor apuesta que permiten los datos. Poner cero es
# tan supuesto como poner 0,094, solo que menos probable.

# --- NEUTRO HISTORICO (capa 2) ---
# Promedio de los promedios de cada presidencia sobre meses limpios (sin
# transiciones ni el periodo fuera de escala 2002-03). Se pondera por PRESIDENCIA
# y no por mes, para que Nestor (44 meses) no pese el doble que Milei (24).
#   Nestor 2,474 | Milei 2,343 | Macri 2,212 | CFK II 1,739 | CFK I 1,611 | Alberto 1,554
# Da 1,9888 — casi identico a la mediana de la serie mensual (1,973), asi que la
# eleccion del neutro NO depende de un juicio nuestro.
NEUTRO = 1.9888

# gamma del NIVEL ABSOLUTO, estimado sobre bisagras controlando por bancas del
# oficialismo. OJO con la lectura de esa correlacion (-0,544): NO significa que los
# gobiernos con buen clima lleguen sin bancas. Es el CALENDARIO DE RECAMBIO
# argentino (Diputados renueva por mitades, Senado por tercios): un presidente
# asume habiendo ganado la eleccion pero hereda un Congreso de ciclos anteriores,
# y ese arranque coincide con la luna de miel del ICG. Las dos cosas van juntas
# por el calendario, no por causalidad.
# +0,488 IC95 [0,28; 0,73]. Se ofrece como REFERENCIA para elegir la intensidad
# de la capa 2, no como parametro del modelo: controlar por bancas es mas debil
# que un efecto fijo y quedan afuera otras diferencias entre gobiernos.
GAMMA_ABS_REFERENCIA = 0.488

# --- Via B: intensidad DECLARADA para el escenario agregado ---
# ATENCION: con la forma ACELERADA, estos gammas NO son comparables con los de
# la version anterior (log-ratio). La escala cambio por completo. Referencia en
# votos que mueve el clima punta a punta (ICG 1,0 <-> 3,3) sobre 257 bancas en
# una votacion al filo:
#     0,05 -> 11 votos | 0,10 -> 22 | 0,20 -> 43 | 0,30 -> 64 | 0,45 -> 93
# Para comparar: el mecanismo INDIVIDUAL, que es el unico medido, mueve 6,6.
#
# **REQUISITO OPERATIVO (Valle, 04-08-2026):** ningun nowcast se publica sin que
# un analista humano evalue la coyuntura y asigne gamma explicitamente. No hay
# default silencioso — se elige en `PANEL-COYUNTURA.html` y se registra.
INTENSIDAD = {
    "nulo":     0.00,   # el clima no toca el agregado
    "leve":     0.05,   # ~11 votos punta a punta
    "moderado": 0.10,   # ~22 votos — 3x el efecto medido
    "fuerte":   0.20,   # ~43 votos — el clima como factor de primer orden
    "extremo":  0.30,   # ~64 votos — solo para coyunturas excepcionales
}


def gamma_individual(desvio: float, solo_significativo: bool = False) -> float:
    """gamma segun cuan bisagra es el legislador. NaN -> se trata como disciplinado."""
    if desvio is None or (isinstance(desvio, float) and np.isnan(desvio)):
        desvio = 0.0
    for umbral, g in TRAMOS:
        if desvio >= umbral:
            if solo_significativo and umbral < SIGNIFICATIVO_DESDE:
                return 0.0
            return g
    return 0.0


def _mover(p, gamma, s, log_rel):
    """logit(p) + gamma*s*log_rel, con los bordes protegidos."""
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    odds = p / (1 - p) * np.exp(np.asarray(gamma) * s * log_rel)
    return odds / (1 + odds)


def aplicar_individual(legisladores: pd.DataFrame, s: float, log_rel: float,
                       solo_significativo: bool = False) -> pd.DataFrame:
    """VÍA A. `legisladores` necesita `p_acompana` y `desvio`.

    Devuelve el mismo frame con `gamma`, `p_mod` y `delta`.
    """
    faltan = {"p_acompana", "desvio"} - set(legisladores.columns)
    if faltan:
        raise ValueError(f"faltan columnas {sorted(faltan)}")
    d = legisladores.copy()
    d["gamma"] = d["desvio"].map(lambda x: gamma_individual(x, solo_significativo))
    d["p_mod"] = _mover(d["p_acompana"].values, d["gamma"].values, s, log_rel)
    d["delta"] = d["p_mod"] - d["p_acompana"]
    return d


_CURVA = None


def neutro_ciclo(mes_mandato: int) -> float:
    """Neutro segun el MES DE MANDATO: lo que un gobierno suele tener a esa altura.

    Sale de alinear las 6 presidencias por mes de mandato y promediar (curva en
    `data/curva_ciclo_presidencial.csv`). Va de 2,58 en el mes 2 a 1,81 en el
    mes 32. **Truncada en el mes 41** (decision de Valle): de ahi en adelante la
    suba que muestra el promedio es expectativa de recambio, no del gobierno.
    """
    global _CURVA
    if _CURVA is None:
        import pathlib
        f = pathlib.Path(__file__).resolve().parents[1] / "data" / "curva_ciclo_presidencial.csv"
        _CURVA = pd.read_csv(f).set_index("mes_mandato")["neutro_ciclo"]
    m = int(np.clip(mes_mandato, _CURVA.index.min(), _CURVA.index.max()))
    return float(_CURVA.loc[m])


BREAK_EVEN = 1.90
EXP_ACEL = 1.5      # >1: cada punto extra de ICG pesa MAS que el anterior
AVERSION = 2.0      # la caida pesa AVERSION veces mas que la suba equivalente


def z_absoluto(icg_mes: float, break_even: float = BREAK_EVEN,
               exp_acel: float = EXP_ACEL, aversion: float = AVERSION) -> float:
    """Desvio del ICG contra el break-even, ACELERADO y con AVERSION A LA PERDIDA.

        z = d^exp_acel                 si d >= 0   (d = ICG - break_even)
        z = -aversion * |d|^exp_acel   si d < 0

    Forma elegida por Valle (04-08-2026) con este razonamiento: *"las personas no
    son sensibles a exitos a menos que sean notables; mientras que son muy
    sensibles a la perdida"*. Es, sin haberlo buscado, la funcion de valor de la
    teoria prospectiva (Kahneman-Tversky): sensibilidad creciente en los extremos
    y asimetria a favor del castigo.

    Con los valores por defecto: ICG 1,0 -> -40% de chances; ICG 3,3 -> +64%;
    y cada +0,5 punto suma 11, 24, 38 y 60 puntos de multiplicador — acelera.
    Para el mismo salto en puntos, la caida pesa entre 1,4x y 1,8x mas que la suba.

    **Caso testigo que motiva la forma (Valle):** Milei llega al poder con ICG
    ~2,8 y aprueba Ley Bases y RIGI con muchas menos bancas de las que tiene hoy.
    Ningun modelo que mire solo la composicion de la camara explica eso.
    """
    d = float(np.clip(icg_mes, 1.0, 4.0)) - break_even
    return d ** exp_acel if d >= 0 else -aversion * (abs(d) ** exp_acel)


def log_vs_fijo(icg_mes: float, break_even: float = BREAK_EVEN) -> float:
    """VARIANTE B del nivel: break-even FIJO, sin curva del ciclo (Valle, 04-08).

    Arriba de 1,90 el factor es positivo y escala cuanto mas se aleja; abajo,
    negativo. Es la version simple: un solo numero para toda la historia.

    **La diferencia con la curva del ciclo, en una frase:** con break-even fijo un
    gobierno recien asumido cobra premio automatico (el ICG a los 3 meses es ~2,55
    por la luna de miel, no por merito) y uno maduro cobra castigo automatico (a los
    30 meses lo normal es 1,82). La curva del ciclo neutraliza eso y premia solo
    estar MEJOR de lo esperable a esa altura.

    Cual conviene NO es una pregunta tecnica sino politica: si se cree que la luna
    de miel da poder real sobre el Congreso, el fijo lo captura. Si se cree que los
    legisladores ya descuentan que todo gobierno arranca alto, la curva es mejor.
    """
    return float(np.log(np.clip(icg_mes, 1.0, 4.0) / break_even))


def log_vs_ciclo(icg_mes: float, mes_mandato: int) -> float:
    """Cuanto esta este gobierno por encima/debajo de lo esperable A ESTA ALTURA."""
    return float(np.log(np.clip(icg_mes, 1.0, 4.0) / neutro_ciclo(mes_mandato)))


def log_nivel_gobierno(prom_gobierno: float, neutro: float = NEUTRO) -> float:
    """(en desuso, queda por compatibilidad) nivel contra el promedio de presidencias.

    Ojo — NO recibe el ICG del mes sino el PROMEDIO DEL GOBIERNO. La razon es
    que la descomposicion tiene que ser exacta y sin solapamiento:

        log(ICG_mes / NEUTRO) = log(ICG_mes / prom_gob) + log(prom_gob / NEUTRO)
                                 \_____ capa 1 _____/    \_____ capa 2 _____/

    Capa 1 = cuanto se desvia el mes respecto de su propio gobierno (lo medido,
    dentro del gobierno, sin el confundidor de las bancas).
    Capa 2 = que tan alto o bajo esta este gobierno contra la historia.

    Si la capa 2 usara el ICG del MES, se estaria contando dos veces el desvio
    mensual, que ya vive entero en la capa 1.

    En vivo, `prom_gobierno` es el promedio EXPANDIDO (los meses transcurridos),
    que es lo unico conocido a la fecha: `icg_base_gob` de icg_contexto.parquet.
    """
    return float(np.log(np.clip(prom_gobierno, 1.0, 4.0) / neutro))


def aplicar_agregado(p_aprobacion: float, s: float, icg_mes: float, mes_mandato: int,
                     intensidad: str = "moderado", modo: str = "ciclo") -> float:
    """CAPA 2. Corre la probabilidad final segun el NIVEL DE ESTE GOBIERNO.

    Recibe el promedio del gobierno (ej. 2,34 para Milei), no el ICG del mes:
    lo que el analista pondera es "este gobierno se sostiene alto/bajo", no el
    ruido del mes — ese ya lo tomo la capa 1. Es un ESCENARIO declarado, no una
    prediccion: se presenta como banda.
    """
    if intensidad not in INTENSIDAD:
        raise ValueError(f"intensidad debe ser una de {sorted(INTENSIDAD)}")
    if modo not in ("ciclo", "fijo"):
        raise ValueError("modo debe ser 'ciclo' o 'fijo'")
    dz = log_vs_ciclo(icg_mes, mes_mandato) if modo == "ciclo" else z_absoluto(icg_mes)
    return float(_mover(p_aprobacion, INTENSIDAD[intensidad], s, dz))


def aplicar_dos_capas(legisladores: pd.DataFrame, s: float, log_rel: float,
                      icg_mes: float, mes_mandato: int, umbral: float,
                      intensidad: str = "moderado", modo: str = "ciclo",
                      solo_significativo: bool = False) -> dict:
    """Las DOS capas compuestas, en el orden que definio Valle (04-08-2026).

    CAPA 1 — dentro del calculo probabilistico. `log_rel` (el ICG contra el
    promedio del propio gobierno) mueve a cada legislador segun cuan bisagra sea.
    Es lo MEDIDO: gamma sube 0,22 -> 0,33 -> 0,35 -> 0,56 con el desvio, con
    dosis-respuesta y significativo. Al ser una comparacion dentro del mismo
    gobierno, no la contamina el confundidor de las bancas.

    CAPA 2 — decision de analista, por fuera del estudio probabilistico. El
    NIVEL ABSOLUTO contra el neutro historico: un gobierno sostenido en 2,8 no
    es lo mismo que uno sostenido en 1,2, aunque los dos esten en su propio
    promedio y la capa 1 les de cero a ambos.

    Las dos capas son independientes por construccion: una mide desvios DENTRO
    del gobierno, la otra el nivel DEL gobierno. Por eso se pueden componer sin
    contarse dos veces.
    """
    d = aplicar_individual(legisladores, s, log_rel, solo_significativo)
    p_base = p_mayoria(d, umbral, "p_acompana")
    p_capa1 = p_mayoria(d, umbral, "p_mod")
    p_final = aplicar_agregado(p_capa1, s, icg_mes, mes_mandato, intensidad, modo)
    v0, _ = votos_esperados(d, "p_acompana")
    v1, _ = votos_esperados(d, "p_mod")
    return {"p_base": p_base, "p_capa1": p_capa1, "p_final": p_final,
            "votos_base": v0, "votos_capa1": v1,
            "log_ciclo": log_vs_ciclo(icg_mes, mes_mandato),
            "log_fijo": log_vs_fijo(icg_mes), "movidos": int((d["delta"].abs() > 0.005).sum()),
            "detalle": d}


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
