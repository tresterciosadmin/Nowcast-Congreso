"""variables/proyecto/src/icg_contexto.py — el ICG como CONTEXTO, no como rasgo.

**Qué cambia respecto del uso anterior.** Hasta el 04-08-2026 el ICG entraba al
embudo como una columna más de la regresión y no aportaba nada (+0,000 de skill,
0,3% de la ponderación). El replanteo de Valle: el ICG no es un atributo del
proyecto, es el **estado del sistema** en el que ese proyecto se juega. Por eso
no se suma como rasgo: se convierte en un **modulador de las chances**, aplicado
después del modelo y con signo según quién impulsa el proyecto.

    odds' = odds x k        k = (ICG_c / ICG_0) ^ (gamma * s)

Se multiplican las CHANCES, no la probabilidad: P x k puede dar más de 1, las
odds no. Equivale a sumar log(k) en el logit.

Este módulo NO aplica el modulador (eso vive donde se agregue el voto): produce
la **serie de contexto** limpia y lista para consumir, y deja documentado qué se
imputó y qué no.

## Las tres decisiones de diseño (Valle, 04-08-2026)

1. **El neutro `ICG_0` es relativo al propio gobierno**, no a la historia. Milei
   en 2,0 es un gobierno en su promedio; CFK en 2,0 era un gobierno en caída.
   Además resuelve un problema econométrico: el 54,5% de la varianza del ICG
   está ENTRE gobiernos, así que comparar entre presidencias mide bancas, no
   clima (Milei tiene el 2do ICG más alto de 25 años y convierte 41,7% de sus
   proyectos; CFK tenía uno de los más bajos y convertía 87,3%).

   **ANTI-LEAKAGE:** el promedio del gobierno se calcula EXPANDIENDO — sólo con
   los meses ya transcurridos. Usar el promedio completo de la presidencia sería
   mirar el futuro.

2. **Las ventanas de traspaso presidencial se imputan.** El ICG de nov-2015 no
   califica a CFK: califica a Macri, que todavía no asumió. Aplicárselo a un
   proyecto que el kirchnerismo empuja en el recinto invierte el signo. Se
   reemplaza por el **promedio plano de los últimos 12 meses del saliente**
   (decisión de Valle: plano y no tendencia — en esas ventanas hay MÁS
   votaciones peleadas (7,8% vs 4,3%), y para casos al filo conviene un número
   aburrido antes que uno que dependa de la pendiente de los últimos meses).

3. **La VOLATILIDAD modula la elasticidad.** Con el ICG planchado no hay
   tracción política y las iniciativas no prenden; con el ICG en movimiento la
   sociedad está permeable y el clima pesa. gamma(t) = gamma_0 * (1 + lambda * vol6).
   Validado: jul-2008 (la 125, ICG 1,27 y vol 0,334) y mar-2022→mar-2023
   (Alberto terminal, ICG ~1,3 y vol 0,045) tienen el MISMO nivel y realidades
   políticas opuestas. El nivel no los distingue; la volatilidad sí.

## Por qué NO se excluyen midterms ni PASO
Se midió: campañas 0,146 y midterms 0,171 de volatilidad, contra 0,156 de un mes
normal. No contaminan. Sólo el traspaso presidencial (0,325, 2,1x) lo hace.
Excluir sólo eso deja 76% de la serie utilizable en vez del 65%.

Uso:
    python variables/proyecto/src/icg_contexto.py            # genera el contrato
    python variables/proyecto/src/icg_contexto.py --resumen  # + diagnóstico

4 directivas: errores específicos, sin red (lee de disco), parsing defensivo,
logging estructurado.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("icg.contexto")

_HERE = Path(__file__).resolve()
DATA = _HERE.parents[1] / "data"
ICG_CSV = DATA / "icg_mensual.csv"
CAL_CSV = DATA / "calendario_electoral.csv"
SALIDA = DATA / "icg_contexto.parquet"

# Límites del índice (Valle): el ICG va de 0 a 5, pero ningún gobierno argentino
# estuvo por encima de 4 ni sostenidamente por debajo de 0,5. Se recorta para que
# un outlier no dispare el modulador.
PISO, TECHO = 1.0, 4.0
# Ventana de contaminación alrededor de un hito presidencial: desde ~3 meses
# antes (la campaña ya mira al que viene) hasta ~6 meses después (luna de miel).
DIAS_ANTES, DIAS_DESPUES = 95, 185
MESES_BASE = 12          # cuántos meses del saliente se promedian
VOL_MESES = 6            # ventana de la volatilidad
MIN_MESES_GOB = 6        # antes de eso, el neutro del gobierno no es confiable

# Gobiernos nacionales (fecha de asunción -> fin de mandato).
GOBIERNOS = [
    ("De la Rua",  "1999-12-10", "2001-12-20"),
    ("Crisis",     "2001-12-21", "2002-01-01"),
    ("Duhalde",    "2002-01-02", "2003-05-24"),
    ("Nestor",     "2003-05-25", "2007-12-09"),
    ("CFK I",      "2007-12-10", "2011-12-09"),
    ("CFK II",     "2011-12-10", "2015-12-09"),
    ("Macri",      "2015-12-10", "2019-12-09"),
    ("Alberto",    "2019-12-10", "2023-12-09"),
    ("Milei",      "2023-12-10", "2027-12-09"),
]


def cargar(icg_csv: Path = ICG_CSV, cal_csv: Path = CAL_CSV) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not icg_csv.exists():
        raise FileNotFoundError(f"falta {icg_csv}. Corré: python variables/proyecto/src/ingesta_icg.py")
    if not cal_csv.exists():
        raise FileNotFoundError(f"falta {cal_csv} (calendario electoral curado a mano)")
    d = pd.read_csv(icg_csv)
    faltan = {"anio", "mes", "icg"} - set(d.columns)
    if faltan:
        raise ValueError(f"icg_mensual.csv sin columnas {sorted(faltan)}")
    d = d.dropna(subset=["anio", "mes", "icg"]).copy()
    d["fecha"] = pd.to_datetime(dict(year=d.anio.astype(int), month=d.mes.astype(int), day=1))
    d = d.sort_values("fecha").drop_duplicates("fecha", keep="last").reset_index(drop=True)
    cal = pd.read_csv(cal_csv, parse_dates=["fecha"])
    return d, cal


def ventanas_transicion(cal: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Ventanas contaminadas por el recambio presidencial (fusionando solapes)."""
    hitos = cal[cal.tipo.isin(["presidencial", "balotaje", "asuncion", "crisis"])]["fecha"]
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for t in sorted(hitos):
        ini, fin = t - pd.Timedelta(days=DIAS_ANTES), t + pd.Timedelta(days=DIAS_DESPUES)
        if out and ini <= out[-1][1]:
            out[-1] = (out[-1][0], max(fin, out[-1][1]))
        else:
            out.append((ini, fin))
    return out


def imputar_plano(d: pd.DataFrame, ventanas) -> pd.DataFrame:
    """En cada ventana, el ICG se reemplaza por el promedio PLANO de los últimos
    `MESES_BASE` meses previos a la ventana (el gobierno saliente).

    Plano y no tendencia: en estas ventanas hay más votaciones peleadas, y un
    número que dependa de la pendiente de los últimos meses es frágil justo
    donde más caro sale equivocarse.
    """
    d = d.copy()
    d["icg_obs"] = d["icg"]
    d["imputado"] = False
    d["regimen"] = "normal"
    for ini, fin in ventanas:
        dentro = (d.fecha >= ini) & (d.fecha <= fin)
        if not dentro.any():
            continue
        prev = d[(d.fecha < ini) & (d.fecha >= ini - pd.DateOffset(months=MESES_BASE))]
        if len(prev) < MIN_MESES_GOB:
            # 2001-2002: la serie arranca en nov-2001, no hay saliente que promediar.
            # No se inventa: se marca para excluir del ajuste de gamma.
            d.loc[dentro, "regimen"] = "sin_base"
            logger.warning("ventana %s->%s sin historia previa suficiente (%d meses): se excluye",
                           ini.date(), fin.date(), len(prev))
            continue
        d.loc[dentro, "icg"] = float(prev["icg"].mean())
        d.loc[dentro, "imputado"] = True
        d.loc[dentro, "regimen"] = "transicion"
    return d


def _gobierno(f: pd.Timestamp) -> str | None:
    for n, a, b in GOBIERNOS:
        if pd.Timestamp(a) <= f <= pd.Timestamp(b):
            return n
    return None


def construir(d: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    d = imputar_plano(d, ventanas_transicion(cal))
    d["gobierno"] = d["fecha"].map(_gobierno)

    # neutro POINT-IN-TIME: promedio del gobierno con los meses ya transcurridos.
    # shift(1) para que el mes corriente no entre en su propio neutro.
    d["icg_base_gob"] = (d.groupby("gobierno")["icg"]
                          .transform(lambda s: s.shift(1).expanding(min_periods=MIN_MESES_GOB).mean()))
    # arranque de gobierno (todavía sin base propia) -> mediana histórica previa
    hist = d["icg"].shift(1).expanding(min_periods=12).median()
    d["icg_base_gob"] = d["icg_base_gob"].fillna(hist)
    d["base_es_propia"] = d.groupby("gobierno")["icg"].transform(
        lambda s: s.shift(1).expanding(min_periods=MIN_MESES_GOB).count()) >= MIN_MESES_GOB

    d["icg_c"] = d["icg"].clip(PISO, TECHO)
    base_c = d["icg_base_gob"].clip(PISO, TECHO)
    # el insumo del modulador: log del ICG relativo al propio gobierno
    d["log_rel"] = np.log(d["icg_c"] / base_c)
    # volatilidad sobre la serie YA limpia (si no, mide el recambio, no el clima)
    d["vol6"] = d["icg"].rolling(VOL_MESES).std()
    d["vol6_z"] = (d["vol6"] - d["vol6"].mean()) / d["vol6"].std()
    # FUERA DE ESCALA: meses con el ICG crudo por debajo del piso (decisión de
    # Valle, 04-08). Es el período 2002-2003: una crisis histórica —cinco
    # presidentes en dos semanas, default, corralito— que se escapa de cualquier
    # medición. Su ICG (0,60) queda pegado al recorte, así que su log_rel es
    # constante cero: no aporta variación al ajuste y sí aportaría un régimen
    # político que no se parece a nada de lo que el modelo tiene que predecir.
    # Se marcan y se excluyen del AJUSTE; para PREDECIR siguen disponibles.
    d["fuera_escala"] = d["icg"] < PISO

    # qué meses sirven para ESTIMAR gamma (predecir se puede en todos)
    d["apto_ajuste"] = ((d["regimen"] == "normal") & ~d["fuera_escala"]
                        & d["log_rel"].notna() & d["vol6"].notna())

    cols = ["fecha", "anio", "mes", "icg_obs", "icg", "icg_c", "imputado", "regimen",
            "gobierno", "icg_base_gob", "base_es_propia", "log_rel", "vol6", "vol6_z",
            "fuera_escala", "apto_ajuste"]
    return d[cols]


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--resumen", action="store_true")
    ap.add_argument("--out", type=Path, default=SALIDA)
    a = ap.parse_args(argv)

    d, cal = cargar()
    out = construir(d, cal)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(a.out, index=False)
    logger.info("contexto ICG -> %s (%d meses, %d imputados, %d aptos para ajuste)",
                a.out, len(out), int(out.imputado.sum()), int(out.apto_ajuste.sum()))

    if a.resumen:
        print("\n=== por regimen ===")
        print(out.groupby("regimen").agg(n=("icg", "size"), icg_medio=("icg", "mean"),
                                         vol_media=("vol6", "mean")).round(3).to_string())
        print("\n=== por gobierno (solo meses aptos) ===")
        ap_ = out[out.apto_ajuste]
        print(ap_.groupby("gobierno").agg(n=("icg", "size"), icg=("icg", "mean"),
                                          base=("icg_base_gob", "mean"),
                                          log_rel_sd=("log_rel", "std"),
                                          vol=("vol6", "mean")).round(3).to_string())
        print(f"\n  log_rel: rango [{ap_.log_rel.min():+.3f}, {ap_.log_rel.max():+.3f}]  "
              f"sd={ap_.log_rel.std():.3f}")
        print(f"  volatilidad: p10={ap_.vol6.quantile(.1):.3f}  p90={ap_.vol6.quantile(.9):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
