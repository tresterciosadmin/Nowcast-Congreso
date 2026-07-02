"""datos/export/src/export_base.py
Base unificada de votaciones para consumo humano y del programa.

Lee la canónica (datos/canonica/data/clean) y produce:
  - data/congreso.db                    — SQLite con TODO (actas, votos, legisladores,
                                          legislador_periodo). El archivo único para el programa.
                                          NO se versiona (pesado y regenerable).
  - data/votaciones_<gobierno>.xlsx     — un Excel POR GOBIERNO (hojas Metodologia/Actas/Votos).
                                          Se separa por gobierno porque el detalle voto-a-voto
                                          completo (835k filas) no entra en una hoja de Excel.

DISPUTADA (definición de Valle, 2026-07-02): una votación es disputada cuando el
resultado queda a ±5% de los VOTOS EMITIDOS ese día respecto del UMBRAL de la
mayoría requerida para ESA votación.
El umbral depende del tipo de mayoría y de los presentes (mayoría simple = sobre los
votos emitidos ese día, no un número fijo). Ej.: aprobación por 130 con umbral 129 →
disputada; rechazo con 200 negativos sobre 257 → no disputada.

GOBIERNOS: cortes por fecha exacta de asunción (los recambios legislativos son los
10 de diciembre; 2001-2003 tiene cortes irregulares por la crisis).

Uso:
  python datos/export/src/export_base.py all          # db + todos los Excel
  python datos/export/src/export_base.py db           # solo SQLite
  python datos/export/src/export_base.py xlsx         # solo los Excel
  python datos/export/src/export_base.py xlsx 2023-2027_Milei   # un gobierno
"""
from __future__ import annotations

import logging
import os
import sqlite3
import sys
from math import ceil, floor
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("export_base")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

MIEMBROS = {"diputados": 257, "senado": 72}
MARGEN_DISPUTADA = 0.05  # ±5% de los votos emitidos (base del margen; decisión Valle)

# (etiqueta, desde, hasta) — inclusive; None = abierto
GOBIERNOS = [
    ("1999-2001_DeLaRua",   None,         "2001-12-20"),
    ("2002-2003_Duhalde",   "2001-12-21", "2003-05-24"),
    ("2003-2007_Kirchner",  "2003-05-25", "2007-12-09"),
    ("2007-2011_CFK-1",     "2007-12-10", "2011-12-09"),
    ("2011-2015_CFK-2",     "2011-12-10", "2015-12-09"),
    ("2015-2019_Macri",     "2015-12-10", "2019-12-09"),
    ("2019-2023_Fernandez", "2019-12-10", "2023-12-09"),
    ("2023-2027_Milei",     "2023-12-10", None),
]


def periodo_parlamentario(fecha: pd.Series, anio: pd.Series) -> pd.Series:
    """Recambios legislativos del 10-dic de años impares (misma definición que
    modelo/voto_individual y variables/legislador; mantener sincronizadas)."""
    f = pd.to_datetime(fecha, errors="coerce")
    ini = f.dt.year.where(f.dt.year % 2 == 1, f.dt.year - 1)
    antes = (f.dt.year % 2 == 1) & ((f.dt.month < 12) | ((f.dt.month == 12) & (f.dt.day < 10)))
    ini = ini.where(~antes, ini - 2)
    a = pd.to_numeric(anio, errors="coerce")
    ini = ini.fillna(a.where(a % 2 == 1, a - 1))
    out = ini.astype("Int64").astype("string")
    return (out + "-" + (ini + 2).astype("Int64").astype("string")).where(ini.notna())


def gobierno(fecha: pd.Series, fuente: pd.Series) -> pd.Series:
    f = pd.to_datetime(fecha, errors="coerce")
    out = pd.Series(pd.NA, index=f.index, dtype="string")
    for etiqueta, desde, hasta in GOBIERNOS:
        m = pd.Series(True, index=f.index)
        if desde:
            m &= f >= pd.Timestamp(desde)
        if hasta:
            m &= f <= pd.Timestamp(hasta + " 23:59:59")
        out = out.where(~(m & f.notna()), etiqueta)
    # manual_2026 no trae fecha: es período 2025-2027 → gobierno Milei
    out = out.where(~(out.isna() & (fuente == "manual_2026")), "2023-2027_Milei")
    return out


def normalizar_mayoria(tipo: pd.Series) -> pd.Series:
    """SIMPLE | ABSOLUTA | DOS_TERCIOS | DOS_TERCIOS_CUERPO | TRES_CUARTOS.
    Sin dato → SIMPLE (el caso abrumadoramente más común)."""
    t = tipo.fillna("").astype(str).str.upper()

    def clas(s: str) -> str:
        if "TERCIO" in s:
            return "DOS_TERCIOS_CUERPO" if "CUERPO" in s else "DOS_TERCIOS"
        if "CUARTO" in s:
            return "TRES_CUARTOS"
        if s == "ABSOLUTA" or "CUERPO" in s or "MITAD MÁS UNO" in s or "MITAD MAS UNO" in s:
            return "ABSOLUTA"
        return "SIMPLE"

    return t.map(clas).astype("string")


def calcular_disputada(a: pd.DataFrame) -> pd.DataFrame:
    """Agrega n_emitidos, umbral_aprobacion y disputada (definición ±5% del umbral)."""
    a = a.copy()
    afirm = pd.to_numeric(a["n_afirmativos"], errors="coerce")
    neg = pd.to_numeric(a["n_negativos"], errors="coerce")
    emitidos = afirm + neg
    miembros = a["camara"].map(MIEMBROS)
    tipo = a["tipo_mayoria_norm"]

    umbral = pd.Series(np.nan, index=a.index, dtype=float)
    umbral[tipo == "SIMPLE"] = emitidos[tipo == "SIMPLE"] / 2
    umbral[tipo == "ABSOLUTA"] = (miembros[tipo == "ABSOLUTA"] // 2 + 1).astype(float)
    umbral[tipo == "DOS_TERCIOS"] = np.ceil(emitidos[tipo == "DOS_TERCIOS"] * 2 / 3)
    umbral[tipo == "DOS_TERCIOS_CUERPO"] = np.ceil(miembros[tipo == "DOS_TERCIOS_CUERPO"] * 2 / 3)
    umbral[tipo == "TRES_CUARTOS"] = np.ceil(emitidos[tipo == "TRES_CUARTOS"] * 3 / 4)

    a["n_emitidos"] = emitidos.astype("Int64")
    a["umbral_aprobacion"] = umbral.round(1)
    # margen = 5% de los VOTOS EMITIDOS ese día (decisión Valle 2026-07-02):
    # escala igual en ambas cámaras y se ajusta a los presentes de cada sesión.
    a["margen_votos"] = (afirm - umbral).round(1)  # con signo: + aprobada holgada, − rechazada
    dist = (afirm - umbral).abs()
    a["disputada"] = (dist <= MARGEN_DISPUTADA * emitidos).astype("Int64")
    a.loc[umbral.isna() | afirm.isna(), "disputada"] = pd.NA
    return a


def cargar(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    clean = Path(os.environ.get("CANON", root / "datos" / "canonica" / "data" / "clean"))
    fa, fv = clean / "actas_canonico.parquet", clean / "votos_resuelto.parquet"
    for f in (fa, fv):
        if not f.exists():
            raise FileNotFoundError(f"No existe {f}. Corré antes: python datos/canonica/src/run_pipeline.py")
    a = pd.read_parquet(fa)
    v = pd.read_parquet(fv)

    a["fecha"] = a["fecha"].astype("string")
    a["anio"] = pd.to_datetime(a["fecha"], errors="coerce").dt.year.astype("Int64")
    a.loc[a["anio"].isna() & (a["fuente"] == "manual_2026"), "anio"] = 2026
    a["periodo"] = periodo_parlamentario(a["fecha"], a["anio"])
    a["gobierno"] = gobierno(a["fecha"], a["fuente"])
    a["tipo_mayoria_norm"] = normalizar_mayoria(a["tipo_mayoria"])

    # totales faltantes: completarlos contando los votos del acta
    cnt = v.pivot_table(index="acta_id", columns="voto", aggfunc="size", fill_value=0)
    for col, nc in [("AFIRMATIVO", "n_afirmativos"), ("NEGATIVO", "n_negativos"),
                    ("ABSTENCION", "n_abstenciones"), ("AUSENTE", "n_ausentes")]:
        if col in cnt.columns:
            calc = a["acta_id"].map(cnt[col])
            a[nc] = pd.to_numeric(a[nc], errors="coerce").fillna(calc).astype("Int64")
    a = calcular_disputada(a)

    cols_a = ["acta_id", "camara", "fecha", "periodo", "gobierno", "titulo", "expediente",
              "tipo_mayoria", "tipo_mayoria_norm", "resultado", "n_afirmativos", "n_negativos",
              "n_abstenciones", "n_ausentes", "n_emitidos", "umbral_aprobacion", "margen_votos", "disputada", "fuente"]
    actas = a[[c for c in cols_a if c in a.columns]].sort_values(["fecha", "acta_id"])

    ctx = actas[["acta_id", "camara", "fecha", "periodo", "gobierno"]]
    v = v.drop(columns=[c for c in ("camara", "fecha", "periodo", "gobierno") if c in v.columns], errors="ignore")
    v = v.merge(ctx, on="acta_id", how="left")
    cols_v = ["acta_id", "camara", "fecha", "periodo", "gobierno", "legislador_id", "legislador_nombre",
              "bloque", "bloque_norm", "bloque_linaje", "coalicion", "distrito", "voto", "fuente"]
    votos = v[[c for c in cols_v if c in v.columns]]

    # desvío v2 (si modelo/voto_individual ya corrió; si no, columnas vacías — NUNCA cero)
    fdesv = root / "modelo" / "voto_individual" / "outputs" / "desvios_por_voto.parquet"
    if fdesv.exists():
        desv = pd.read_parquet(fdesv).drop_duplicates(["acta_id", "legislador_id"])
        votos = votos.merge(desv[["acta_id", "legislador_id", "conducta", "linea", "desvio"]],
                            on=["acta_id", "legislador_id"], how="left")
        log.info("desvío v2 incorporado a votos: %d filas con dato", int(votos["desvio"].notna().sum()))
    else:
        votos = votos.assign(conducta=pd.NA, linea=pd.NA, desvio=pd.NA)
        log.warning("sin desvios_por_voto.parquet (correr antes disciplina.py); votos sale sin desvío")
    log.info("actas: %d | votos: %d | disputadas: %s", len(actas), len(votos),
             actas["disputada"].sum())
    return actas, votos


METODOLOGIA = [
    ("(general)", "", "Base unificada de votaciones nominales del Congreso argentino (fuentes: base canónica "
     "propia 2001-2026). Un archivo por GOBIERNO (cortes por fecha exacta de asunción; los recambios "
     "legislativos son los 10 de diciembre de años impares). El archivo completo para consultas está en "
     "congreso.db (SQLite). Celda vacía = sin dato (NUNCA significa cero)."),
    ("(general)", "DISPUTADA", "Una votación es disputada cuando el resultado queda dentro de ±5% del UMBRAL "
     "de la mayoría requerida para ESA votación. El umbral depende del tipo de mayoría y de los presentes "
     "(mayoría simple se calcula sobre los votos emitidos ese día, no sobre un número fijo). Ej.: aprobación "
     "por 130 votos con umbral 129 → disputada; rechazo con 200 negativos sobre 257 presentes → no disputada."),
    ("Actas", "acta_id", "Identificador único de la votación (incluye la fuente)."),
    ("Actas", "camara", "diputados / senado."),
    ("Actas", "fecha", "Fecha de la votación (vacía en la fuente manual 2026)."),
    ("Actas", "periodo", "Período parlamentario: entre recambios del 10-dic de años impares (ej. 2023-2025)."),
    ("Actas", "gobierno", "Gobierno nacional al momento de la votación (cortes por fecha de asunción)."),
    ("Actas", "titulo", "Qué se votó, según la fuente."),
    ("Actas", "expediente", "N° de expediente si se pudo extraer (llave futura al cruce con taxonomías)."),
    ("Actas", "tipo_mayoria", "Mayoría requerida, tal como vino en la fuente (texto crudo)."),
    ("Actas", "tipo_mayoria_norm", "Normalizada: SIMPLE / ABSOLUTA / DOS_TERCIOS (de emitidos) / "
     "DOS_TERCIOS_CUERPO (del total de miembros) / TRES_CUARTOS. Sin dato → SIMPLE."),
    ("Actas", "resultado", "Resultado publicado por la fuente."),
    ("Actas", "n_afirmativos / n_negativos / n_abstenciones / n_ausentes", "Totales de la votación (si la "
     "fuente no los traía, se calcularon contando los votos nominales)."),
    ("Actas", "n_emitidos", "Afirmativos + negativos (la base de la mayoría simple)."),
    ("Actas", "umbral_aprobacion", "Votos afirmativos necesarios para aprobar según tipo_mayoria_norm: "
     "SIMPLE = mitad de los emitidos; ABSOLUTA = 129 (Dip) / 37 (Sen); DOS_TERCIOS = 2/3 de emitidos o del "
     "cuerpo según corresponda; TRES_CUARTOS = 3/4 de emitidos."),
    ("Actas", "margen_votos", "Afirmativos menos umbral, CON SIGNO: positivo = aprobada con ese sobrante; "
     "negativo = le faltaron esos votos. Permite filtrar con cualquier vara ('definidas por menos de 20 votos') "
     "sin recalcular."),
    ("Actas", "disputada", "1 = el resultado quedó a ±5% de los emitidos respecto del umbral (ver definición "
     "general). Vacío = no calculable (faltan totales)."),
    ("Actas", "fuente", "De qué fuente salió el dato (decada_votada / ckan_diputados / senado / "
     "argentinadatos / manual_2026)."),
    ("Votos", "acta_id", "Enlace a la hoja Actas."),
    ("Votos", "camara / fecha / periodo / gobierno", "Copiados del acta para filtrar sin cruzar hojas."),
    ("Votos", "legislador_id", "Identificador único de la persona (unifica variantes del nombre entre fuentes)."),
    ("Votos", "legislador_nombre", "Nombre tal como vino en la fuente."),
    ("Votos", "bloque", "Bloque crudo de la fuente."),
    ("Votos", "bloque_norm", "Bloque normalizado (unifica variantes de escritura del mismo bloque)."),
    ("Votos", "bloque_linaje", "Espacio político agregado (ej. FpV/FdT/UxP = un mismo linaje)."),
    ("Votos", "coalicion", "Coalición de época (ej. JxC solo entre 2015-12-10 y 2023-12-10)."),
    ("Votos", "distrito", "Provincia por la que ocupa la banca."),
    ("Votos", "voto", "AFIRMATIVO / NEGATIVO / ABSTENCION / AUSENTE."),
    ("Votos", "conducta", "El voto agrupado en tres conductas: AFIRMATIVO / NEGATIVO / NO_ACOMPANA "
     "(abstenerse o ausentarse: usar el escaño es una decisión)."),
    ("Votos", "linea", "La bajada de línea del bloque en esa votación: la conducta con mayoría simple "
     "sobre TODOS los escaños del bloque (incluidos ausentes). Si el bloque empata, se desempata con la "
     "línea del espacio político (linaje); vacía si tampoco la hubo."),
    ("Votos", "desvio", "Indisciplina en esta votación: 1 = conducta distinta de la línea (estricta: "
     "abstenerse o ausentarse contra la línea también computa; votar cuando el bloque se ausenta, también); "
     "0 = alineado. Valores intermedios (ej. 0.5) = bloque sin línea (desvío parcial: fracción de pares con "
     "otra conducta). Vacío = no calculado. Excluidos: presidentes de Diputados (no votan por costumbre). "
     "Definición completa: ADR-0004."),
    ("Votos", "fuente", "Origen del dato."),
]


def hoja_metodologia(w) -> None:
    m = pd.DataFrame(METODOLOGIA, columns=["hoja", "columna", "significado"])
    m.to_excel(w, sheet_name="Metodologia", index=False)


def export_db(out: Path, actas: pd.DataFrame, votos: pd.DataFrame, root: Path) -> None:
    """Escribe a un temporal local y copia al final: SQLite falla sobre carpetas
    sincronizadas (OneDrive y similares) y así el .db nunca queda a medias."""
    import shutil, tempfile
    db = out / "congreso.db"
    tmp = Path(tempfile.mkstemp(suffix=".db")[1])
    con = sqlite3.connect(tmp)
    try:
        actas.to_sql("actas", con, index=False)
        votos.astype({"fecha": "string"}).to_sql("votos", con, index=False)
        con.execute("CREATE INDEX ix_votos_acta ON votos(acta_id)")
        con.execute("CREATE INDEX ix_votos_leg ON votos(legislador_id)")
        ldir = root / "variables" / "legislador" / "data"
        for tabla, f in [("legisladores", "legisladores.parquet"),
                         ("legislador_periodo", "legislador_periodo.parquet")]:
            if (ldir / f).exists():
                pd.read_parquet(ldir / f).to_sql(tabla, con, index=False)
            else:
                log.warning("no está %s; el .db sale sin la tabla %s", f, tabla)
        con.commit()
    finally:
        con.close()  # en Windows hay que cerrar explícito antes de copiar/borrar el temporal
    shutil.copyfile(tmp, db)  # copyfile sobreescribe (algunos entornos no permiten borrar)
    try:
        tmp.unlink()
    except OSError:
        log.warning("no pude borrar el temporal %s (lo limpia el sistema)", tmp)
    log.info("SQLite listo: %s (%.1f MB)", db, db.stat().st_size / 1e6)


def export_xlsx(out: Path, actas: pd.DataFrame, votos: pd.DataFrame, solo: str | None = None) -> None:
    gobiernos = [g for g, _, _ in GOBIERNOS if solo is None or g == solo]
    for g in gobiernos:
        a = actas[actas["gobierno"] == g]
        v = votos[votos["gobierno"] == g]
        if a.empty:
            log.info("sin actas para %s; salteado", g)
            continue
        f = out / f"votaciones_{g}.xlsx"
        with pd.ExcelWriter(f, engine="xlsxwriter") as w:
            hoja_metodologia(w)
            a.to_excel(w, sheet_name="Actas", index=False)
            v.to_excel(w, sheet_name="Votos", index=False)
        log.info("%s: %d actas / %d votos (%.1f MB)", f.name, len(a), len(v), f.stat().st_size / 1e6)


def main() -> None:
    modo = sys.argv[1] if len(sys.argv) > 1 else "all"
    solo = sys.argv[2] if len(sys.argv) > 2 else None
    root = Path(__file__).resolve().parents[3]
    out = Path(os.environ.get("OUT", Path(__file__).resolve().parents[1] / "data"))
    out.mkdir(parents=True, exist_ok=True)
    # caché opcional (acelera correr los Excel de a uno): EXPORT_CACHE=/ruta
    cache = os.environ.get("EXPORT_CACHE")
    ca = Path(cache) / "_actas_prep.parquet" if cache else None
    cv = Path(cache) / "_votos_prep.parquet" if cache else None
    if cache and ca.exists() and cv.exists():
        actas, votos = pd.read_parquet(ca), pd.read_parquet(cv)
        log.info("base preparada desde caché (%d actas / %d votos)", len(actas), len(votos))
    else:
        actas, votos = cargar(root)
        if cache:
            actas.to_parquet(ca, index=False); votos.to_parquet(cv, index=False)
    if modo in ("all", "db"):
        export_db(out, actas, votos, root)
    if modo in ("all", "xlsx"):
        export_xlsx(out, actas, votos, solo)


if __name__ == "__main__":
    main()
