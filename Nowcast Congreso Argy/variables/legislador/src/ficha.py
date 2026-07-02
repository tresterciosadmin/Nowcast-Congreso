"""variables/legislador/src/ficha.py
Base de datos individual de legisladores: una FICHA por cada diputado/senador
que haya votado en la base canónica, con su historial completo.

La unidad de análisis temporal es el PERÍODO PARLAMENTARIO (entre recambios del
10 de diciembre de años impares): cada recambio reconfigura los escaños, por lo
que el comportamiento (presentismo, disciplina) se evalúa por período además de
en agregado. `anio_desde/anio_hasta` son actividad observada en la base, NO el
mandato formal (eso vendrá del padrón oficial).

Tablas de salida (data/):
  - legisladores.parquet / .csv     — una fila por legislador (la ficha resumen)
  - legislador_periodo.parquet      — legislador x período parlamentario x cámara (LA tabla de análisis)
  - legislador_bloques.parquet      — historial: legislador x bloque x cámara (desde-hasta, n votos)
  - legislador_anio.parquet         — evolución: legislador x año
  - legisladores.xlsx               — export legible (hojas: Metodologia / Fichas / PorPeriodo / Bloques / PorAnio)

Uso:
  python variables/legislador/src/ficha.py
  CANON=/ruta/clean OUT=/ruta/salida python variables/legislador/src/ficha.py
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("ficha_legislador")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SUST = ["AFIRMATIVO", "NEGATIVO"]


def periodo_parlamentario(fecha: pd.Series, anio: pd.Series) -> pd.Series:
    """Período entre recambios legislativos (10 de diciembre de años impares).
    Misma definición que modelo/voto_individual/src/disciplina.py (mantener sincronizadas)."""
    f = pd.to_datetime(fecha, errors="coerce")
    ini = f.dt.year.where(f.dt.year % 2 == 1, f.dt.year - 1)
    antes_recambio = (f.dt.year % 2 == 1) & (
        (f.dt.month < 12) | ((f.dt.month == 12) & (f.dt.day < 10))
    )
    ini = ini.where(~antes_recambio, ini - 2)
    a = pd.to_numeric(anio, errors="coerce")
    ini_aprox = a.where(a % 2 == 1, a - 1)
    ini = ini.fillna(ini_aprox)
    out = ini.astype("Int64").astype("string")
    return (out + "-" + (ini + 2).astype("Int64").astype("string")).where(ini.notna())


def cargar(src: Path) -> pd.DataFrame:
    """Carga votos resueltos + cámara del acta. Falla con mensaje claro si no está la base."""
    fv, fa = src / "votos_resuelto.parquet", src / "actas_canonico.parquet"
    for f in (fv, fa):
        if not f.exists():
            raise FileNotFoundError(
                f"No existe {f}. Reconstruí la base primero: python datos/canonica/src/run_pipeline.py"
            )
    v = pd.read_parquet(fv)
    a = pd.read_parquet(fa)[["acta_id", "camara", "fecha"]].rename(columns={"fecha": "fecha_acta"})
    v = v.merge(a, on="acta_id", how="left")
    v["fecha"] = v["fecha"].fillna(v["fecha_acta"])
    v["anio"] = pd.to_datetime(v["fecha"], errors="coerce").dt.year.astype("Int64")
    v.loc[v["anio"].isna() & (v["fuente"] == "manual_2026"), "anio"] = 2026
    v["periodo"] = periodo_parlamentario(v["fecha"], v["anio"])
    if v.empty:
        raise ValueError("Base canónica vacía; nada que fichar.")
    log.info("votos: %d | legisladores: %d", len(v), v["legislador_id"].nunique())
    return v


def _nombre_canonico(s: pd.Series) -> str:
    """El nombre más frecuente (y más largo ante empate) entre las variantes."""
    vc = s.value_counts()
    top = vc[vc == vc.max()].index
    return max(top, key=len)


def historial_bloques(v: pd.DataFrame) -> pd.DataFrame:
    g = (
        v.dropna(subset=["bloque_norm"])
        .groupby(["legislador_id", "camara", "bloque_norm"], observed=True)
        .agg(anio_desde=("anio", "min"), anio_hasta=("anio", "max"),
             n_votos=("voto", "size"), linaje=("bloque_linaje", "first"))
        .reset_index()
        .sort_values(["legislador_id", "anio_desde"])
    )
    return g


def por_periodo(v: pd.DataFrame, disc_periodo: pd.DataFrame | None) -> pd.DataFrame:
    """LA tabla de análisis: legislador x período parlamentario x cámara.
    Cada recambio (incluso con reelección) es una nueva configuración de escaños."""
    base = v.dropna(subset=["periodo"]).copy()
    base["presente"] = base["voto"] != "AUSENTE"
    g = (
        base.groupby(["legislador_id", "periodo", "camara"], observed=True)
        .agg(nombre=("legislador_nombre", _nombre_canonico),
             bloque=("bloque_norm", lambda s: _nombre_canonico(s.dropna()) if s.notna().any() else pd.NA),
             n_votaciones=("acta_id", "nunique"), n_votos=("voto", "size"),
             presentismo=("presente", "mean"))
        .reset_index()
    )
    g["presentismo"] = g["presentismo"].round(4)
    if disc_periodo is not None:
        d = disc_periodo[["legislador_id", "periodo", "camara", "tasa_desvio", "tasa_desvio_disputadas"]]
        g = g.merge(d, on=["legislador_id", "periodo", "camara"], how="left")
        log.info("tasa de desvío por período incorporada para %d filas", int(g["tasa_desvio"].notna().sum()))
    else:
        g["tasa_desvio"] = pd.NA
        g["tasa_desvio_disputadas"] = pd.NA
        log.warning("sin disciplina_por_periodo.csv; PorPeriodo sale sin tasa de desvío")
    return g.sort_values(["legislador_id", "periodo"])


def por_anio(v: pd.DataFrame, desvios: pd.DataFrame | None) -> pd.DataFrame:
    base = v.dropna(subset=["anio"]).copy()
    base["presente"] = base["voto"] != "AUSENTE"
    g = (
        base.groupby(["legislador_id", "anio"], observed=True)
        .agg(camara=("camara", "first"), bloque=("bloque_norm", _nombre_canonico),
             n_votaciones=("acta_id", "nunique"), n_votos=("voto", "size"),
             presentismo=("presente", "mean"))
        .reset_index()
    )
    g["presentismo"] = g["presentismo"].round(4)
    if desvios is not None:
        g = g.merge(desvios[["legislador_id", "anio", "tasa_desvio"]], on=["legislador_id", "anio"], how="left")
    return g


def ficha(v: pd.DataFrame, bloques: pd.DataFrame, disciplina: pd.DataFrame | None) -> pd.DataFrame:
    v = v.copy()
    v["presente"] = v["voto"] != "AUSENTE"

    def agg(sub: pd.DataFrame) -> pd.Series:
        pres = sub[sub["presente"]]
        sust = sub[sub["voto"].isin(SUST)]
        pers = sorted(sub["periodo"].dropna().unique())
        return pd.Series({
            "nombre": _nombre_canonico(sub["legislador_nombre"]),
            "camaras": "+".join(sorted(sub["camara"].dropna().unique())),
            "distrito": _nombre_canonico(sub["distrito"].dropna()) if sub["distrito"].notna().any() else pd.NA,
            "n_periodos": len(pers),
            "periodos": "; ".join(pers),
            "anio_desde": sub["anio"].min(), "anio_hasta": sub["anio"].max(),
            "anios_activos": sub["anio"].nunique(),
            "n_votaciones": sub["acta_id"].nunique(),
            "n_votos": len(sub),
            "presentismo": round(sub["presente"].mean(), 4),
            "pct_afirmativo": round((pres["voto"] == "AFIRMATIVO").mean(), 4) if len(pres) else np.nan,
            "pct_negativo": round((pres["voto"] == "NEGATIVO").mean(), 4) if len(pres) else np.nan,
            "pct_abstencion": round((pres["voto"] == "ABSTENCION").mean(), 4) if len(pres) else np.nan,
            "n_votos_sustantivos": len(sust),
            "bloque_ultimo": sub.sort_values("anio")["bloque_norm"].dropna().iloc[-1]
                             if sub["bloque_norm"].notna().any() else pd.NA,
        })

    f = v.groupby("legislador_id", observed=True).apply(agg, include_groups=False).reset_index()

    nb = bloques.groupby("legislador_id")["bloque_norm"].nunique().rename("n_bloques")
    trayecto = (
        bloques.sort_values("anio_desde")
        .groupby("legislador_id")["bloque_norm"]
        .apply(lambda s: " → ".join(dict.fromkeys(s)))
        .rename("trayectoria_bloques")
    )
    f = f.merge(nb, on="legislador_id", how="left").merge(trayecto, on="legislador_id", how="left")

    if disciplina is not None:
        d = disciplina[["legislador_id", "n_votos", "tasa_desvio", "tasa_desvio_disputadas"]].rename(
            columns={"n_votos": "n_votos_desvio_medibles"}
        )
        f = f.merge(d, on="legislador_id", how="left")
        log.info("tasa de desvío incorporada para %d legisladores", int(f["tasa_desvio"].notna().sum()))
    else:
        f["n_votos_desvio_medibles"] = pd.NA
        f["tasa_desvio"] = pd.NA
        f["tasa_desvio_disputadas"] = pd.NA
        log.warning("sin salida de modelo/voto_individual; la ficha sale sin tasa de desvío")

    return f.sort_values(["camaras", "nombre"]).reset_index(drop=True)


# Regla de la casa: todo Excel entregable arranca con una hoja "Metodologia" que
# explica cada columna de cada hoja (los archivos son muchos y extensos; nadie
# debería tener que leer código para entender un encabezado).
METODOLOGIA = [
    ("(general)", "", "Base: votaciones nominales del Congreso 2001-2026 (fuente: base canónica propia). "
     "PERÍODO PARLAMENTARIO = entre recambios del 10-dic de años impares; cada recambio (incluso reelectos) "
     "reconfigura los escaños, por eso el análisis fino es por período (hoja PorPeriodo). "
     "DESVÍO = votar contra la mayoría del propio bloque en esa votación (mayoría calculada sin el voto propio; "
     "solo cuenta si el resto del bloque tiene 5+ votos y no empata). "
     "DISPUTADA = votación donde la minoría juntó 10%+ de los votos (las peleadas, donde desviarse importa). "
     "Celda vacía = sin dato (NUNCA significa cero). Cuidado con tasas calculadas sobre pocos votos."),
    ("Fichas", "legislador_id", "Identificador único de la persona (unifica variantes del nombre entre fuentes)."),
    ("Fichas", "nombre", "Nombre más frecuente en las fuentes."),
    ("Fichas", "camaras", "Cámara(s) donde votó: diputados, senado o ambas."),
    ("Fichas", "distrito", "Provincia/distrito por el que ocupó la banca (según las fuentes)."),
    ("Fichas", "n_periodos / periodos", "Cuántos y cuáles períodos parlamentarios tiene con actividad registrada."),
    ("Fichas", "anio_desde / anio_hasta", "Primer y último año en que aparece votando en la base. Es actividad "
     "observada, NO el mandato formal: no detecta interrupciones y hereda huecos de cobertura (Senado 2015-2023)."),
    ("Fichas", "anios_activos", "Cantidad de años distintos con actividad (si es menor al rango, hubo huecos)."),
    ("Fichas", "n_votaciones / n_votos", "Votaciones distintas en las que figura / total de registros de voto."),
    ("Fichas", "presentismo", "Proporción de votaciones en las que NO figuró ausente (1 = asistió siempre)."),
    ("Fichas", "pct_afirmativo / pct_negativo / pct_abstencion", "Cómo vota cuando está presente (suman 1)."),
    ("Fichas", "n_votos_sustantivos", "Votos a favor o en contra (excluye ausencias y abstenciones)."),
    ("Fichas", "bloque_ultimo", "Último bloque registrado."),
    ("Fichas", "n_bloques / trayectoria_bloques", "Por cuántos bloques pasó y en qué orden."),
    ("Fichas", "n_votos_desvio_medibles", "Votos donde se pudo medir desvío (sustantivos + bloque con posición clara)."),
    ("Fichas", "tasa_desvio", "Proporción de votos contra la mayoría del propio bloque (0 = siempre alineado). "
     "Toda la carrera junta: para análisis fino usar PorPeriodo."),
    ("Fichas", "tasa_desvio_disputadas", "Ídem pero solo en votaciones peleadas. LA columna clave: desviarse ahí "
     "es lo que puede cambiar el resultado de una ley."),
    ("PorPeriodo", "(unidad)", "Una fila = un legislador en un período parlamentario en una cámara. "
     "La tabla de análisis principal."),
    ("PorPeriodo", "periodo", "Período parlamentario (ej. 2023-2025 = del 10-dic-2023 al 9-dic-2025)."),
    ("PorPeriodo", "bloque", "Bloque más frecuente de esa persona en ese período."),
    ("PorPeriodo", "n_votaciones / n_votos", "Actividad en el período."),
    ("PorPeriodo", "presentismo", "Asistencia a votaciones en el período (1 = nunca ausente)."),
    ("PorPeriodo", "tasa_desvio / tasa_desvio_disputadas", "Desvío vs. su bloque EN ESE PERÍODO (total / solo "
     "votaciones peleadas). Vacío = no medible (bloque chico, sin votos sustantivos, o falta correr disciplina.py)."),
    ("Bloques", "(unidad)", "Una fila = una etapa legislador x bloque x cámara."),
    ("Bloques", "anio_desde / anio_hasta", "Primer y último año votando con ese bloque (actividad observada)."),
    ("Bloques", "n_votos", "Registros de voto con ese bloque."),
    ("Bloques", "linaje", "Espacio político agregado (ej. FpV/FdT/UxP = mismo linaje kirchnerista)."),
    ("PorAnio", "(unidad)", "Una fila = un legislador en un año calendario. Para series finas; para análisis "
     "político usar PorPeriodo."),
]


def hoja_metodologia(w) -> None:
    m = pd.DataFrame(METODOLOGIA, columns=["hoja", "columna", "significado"])
    m.to_excel(w, sheet_name="Metodologia", index=False)
    ws = w.sheets["Metodologia"]
    for col, ancho in (("A", 14), ("B", 38), ("C", 120)):
        ws.column_dimensions[col].width = ancho
    for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
        for c in row:
            c.alignment = c.alignment.copy(wrap_text=True, vertical="top")


def export_excel(out: Path, f: pd.DataFrame, periodos: pd.DataFrame,
                 bloques: pd.DataFrame, anual: pd.DataFrame) -> None:
    try:
        with pd.ExcelWriter(out / "legisladores.xlsx", engine="openpyxl") as w:
            hoja_metodologia(w)
            f.to_excel(w, sheet_name="Fichas", index=False)
            periodos.to_excel(w, sheet_name="PorPeriodo", index=False)
            bloques.to_excel(w, sheet_name="Bloques", index=False)
            anual.to_excel(w, sheet_name="PorAnio", index=False)
    except ImportError:
        log.warning("openpyxl no instalado; salteo el Excel (quedan parquet/csv)")


def main() -> None:
    here = Path(__file__).resolve()
    root = here.parents[3]
    src = Path(os.environ.get("CANON", root / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", here.parents[1] / "data"))
    out.mkdir(parents=True, exist_ok=True)

    v = cargar(src)

    disc_dir = root / "modelo" / "voto_individual" / "outputs"
    disc = pd.read_csv(disc_dir / "disciplina_individual.csv") if (disc_dir / "disciplina_individual.csv").exists() else None
    disc_anual = pd.read_csv(disc_dir / "disciplina_por_anio.csv") if (disc_dir / "disciplina_por_anio.csv").exists() else None
    disc_per = pd.read_csv(disc_dir / "disciplina_por_periodo.csv") if (disc_dir / "disciplina_por_periodo.csv").exists() else None

    bloques = historial_bloques(v)
    periodos = por_periodo(v, disc_per)
    anual = por_anio(v, disc_anual)
    f = ficha(v, bloques, disc)

    f.to_parquet(out / "legisladores.parquet", index=False)
    f.to_csv(out / "legisladores.csv", index=False, encoding="utf-8-sig")
    periodos.to_parquet(out / "legislador_periodo.parquet", index=False)
    bloques.to_parquet(out / "legislador_bloques.parquet", index=False)
    anual.to_parquet(out / "legislador_anio.parquet", index=False)
    export_excel(out, f, periodos, bloques, anual)

    print(f"Fichas: {len(f)} legisladores | {f['camaras'].value_counts().to_dict()}")
    print(f"Filas legislador x período: {len(periodos)} | períodos: {periodos['periodo'].nunique()}")
    print(f"Presentismo mediano: {f['presentismo'].median():.3f} | "
          f"con tasa de desvío: {int(f['tasa_desvio'].notna().sum())}")
    print(f"Salida en: {out}")


if __name__ == "__main__":
    main()
