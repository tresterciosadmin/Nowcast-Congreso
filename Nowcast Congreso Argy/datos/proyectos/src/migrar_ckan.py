"""Backfill de CKAN -> proyectos.db (ADR-0009, etapa 1: MUDANZA PURA).

Etapa 1 mueve `datos/expedientes/data/clean/*.parquet` al esquema relacional SIN
agregar ni un solo proyecto nuevo. Es a proposito: el skill del embudo tiene que
dar IDENTICO despues de esto. Si se mueve, la mudanza rompio algo. Los proyectos
del bot entran en la etapa 2 (`upsert_bot.py`), donde el skill SI puede cambiar.

Por que no usa `store.upsert_proyecto()`: esa funcion hace SELECT + DELETE + INSERT
por proyecto, pensada para refrescar una ficha scrapeada. Para un backfill de 828k
filas sobre una base VACIA no hace falta (no hay nada que refrescar) y seria
ordenes de magnitud mas lento. La capa de merge con `upsert_proyecto` se usa en la
etapa 2, que es donde dos fuentes tocan el mismo proyecto.

Uso:
    python datos/proyectos/src/migrar_ckan.py            # crea/rehace la base
    python datos/proyectos/src/migrar_ckan.py --verificar # solo cuenta y compara
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migrar_ckan")

RAIZ = Path(__file__).resolve().parents[3]
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"
DB = RAIZ / "datos" / "proyectos" / "data" / "proyectos.db"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"

LOTE = 20_000


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _leer(nombre: str, obligatorio: bool = False) -> pd.DataFrame | None:
    """Lee un parquet del contrato de datos/expedientes. Tolerante a faltantes."""
    p = CLEAN / nombre
    if not p.exists():
        if obligatorio:
            raise SystemExit(f"FALTA {p}. Corre antes: datos/expedientes/src/ingesta_ckan.py")
        logger.warning("no esta %s: sigo sin el", nombre)
        return None
    df = pd.read_parquet(p)
    logger.info("%-38s %8d filas", nombre, len(df))
    return df


# El mount de la carpeta del proyecto NO soporta el file locking que SQLite
# necesita: crear la base ahi tira `disk I/O error` (comprobado 07-08-2026).
# Se construye en disco LOCAL y se copia al final; copiar un archivo terminado
# si funciona, porque no requiere locks. En Windows esto no pasa: si Valle corre
# el script a mano, TRABAJO y DB pueden ser el mismo path sin problema.
TRABAJO = Path(tempfile.gettempdir()) / "proyectos_build.db"


def _conectar_fresca() -> sqlite3.Connection:
    """Base NUEVA en disco local. Es un derivado: se rehace, no se repara."""
    if TRABAJO.exists():
        TRABAJO.unlink()
    con = sqlite3.connect(str(TRABAJO))
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    # Velocidad: es una carga masiva sobre una base descartable.
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")
    return con


def _publicar() -> None:
    """Copia la base terminada del disco local a su lugar definitivo."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TRABAJO, DB)
    logger.info("publicada en %s (%.1f MB)", DB, DB.stat().st_size / 1e6)


def _ids_a_denom(exp: pd.DataFrame) -> dict[str, str]:
    """proyecto_id (HCDN...) -> denominador (NNNN-X-AAAA)."""
    return dict(zip(exp["proyecto_id"].astype(str), exp["denominador"]))


def _insertar(con, sql: str, filas: list[tuple], que: str) -> int:
    if not filas:
        logger.info("  %-22s 0", que)
        return 0
    for i in range(0, len(filas), LOTE):
        con.executemany(sql, filas[i:i + LOTE])
    con.commit()
    logger.info("  %-22s %8d", que, len(filas))
    return len(filas)


def migrar() -> dict[str, int]:
    exp = _leer("expedientes.parquet", obligatorio=True)
    giros = _leer("expedientes_giros.parquet")
    dicts_ = _leer("expedientes_dictamenes.parquet")
    movs = _leer("expedientes_movimientos.parquet")
    res = _leer("expedientes_resultados.parquet")
    leyes = _leer("expedientes_leyes.parquet")
    gini = _leer("giros_iniciales.parquet")

    exp = exp.copy()
    exp["proyecto_id"] = exp["proyecto_id"].astype(str)

    # ── Denominador ──────────────────────────────────────────────────────────
    # exp_diputados esta en las 112.793 filas (verificado 07-08). Es la clave
    # oficial y la que usan los informes; proyecto_id queda como columna para
    # poder volver a los contratos viejos.
    exp["denominador"] = exp["exp_diputados"]
    sin = exp["denominador"].isna().sum()
    if sin:
        raise SystemExit(f"{sin} filas sin exp_diputados: no puedo darles denominador")

    dup = exp["denominador"].duplicated().sum()
    if dup:
        logger.warning("%d denominadores duplicados en CKAN -> me quedo con el mas "
                       "reciente por fecha_publicacion", dup)
        exp = (exp.sort_values("fecha_publicacion")
                  .drop_duplicates("denominador", keep="last"))

    ahora = _ahora()
    con = _conectar_fresca()
    stats: dict[str, int] = {}

    filas = [
        (r.denominador, str(r.camara_origen).strip().lower() if pd.notna(r.camara_origen) else None,
         r.titulo, r.fecha_publicacion, None, None, None, None, None, 1, ahora, ahora, ahora,
         r.proyecto_id, r.exp_senado, r.tipo, None, None)
        for r in exp.itertuples(index=False)
    ]
    stats["proyectos"] = _insertar(con,
        "INSERT INTO proyectos (denominador,camara,sumario,fecha_ingreso,estado,"
        "ultimo_movimiento,ultimo_movimiento_fecha,pdf_url,url,fuente_ok,capturado_en,"
        "creado_en,actualizado_en,proyecto_id,exp_senado,tipo,n_giros_inicial,"
        "n_giros_inicial_fuente) VALUES (" + ",".join("?" * 18) + ")",
        filas, "proyectos")

    id2d = _ids_a_denom(exp)

    # ── Autores: CKAN publica UNO solo (el primer firmante) ──────────────────
    aut = [(r.denominador, 0, r.autor, None, None)
           for r in exp.itertuples(index=False) if pd.notna(r.autor)]
    stats["autores"] = _insertar(con,
        "INSERT INTO proyecto_autores (denominador,orden,nombre,distrito,bloque)"
        " VALUES (?,?,?,?,?)", aut, "autores (1 c/u)")

    # ── Giros: acumulado de HOY (el inicial va aparte, abajo) ────────────────
    if giros is not None and "proyecto_id" in giros.columns:
        g = giros.copy(); g["proyecto_id"] = g["proyecto_id"].astype(str)
        g["denominador"] = g["proyecto_id"].map(id2d)
        g = g.dropna(subset=["denominador"])
        col = "comision" if "comision" in g.columns else None
        filas = [(r.denominador, None, getattr(r, col), 0, None, None)
                 for r in g.itertuples(index=False)] if col else []
        stats["giros"] = _insertar(con,
            "INSERT INTO proyecto_giros (denominador,orden,comision,"
            "competencia_primaria,fecha_ingreso,fecha_egreso) VALUES (?,?,?,?,?,?)",
            filas, "giros")

    # ── Tramite = movimientos ────────────────────────────────────────────────
    if movs is not None and "proyecto_id" in movs.columns:
        m = movs.copy(); m["proyecto_id"] = m["proyecto_id"].astype(str)
        m["denominador"] = m["proyecto_id"].map(id2d)
        m = m.dropna(subset=["denominador"])
        cm = "movimiento" if "movimiento" in m.columns else None
        cf = "fecha" if "fecha" in m.columns else None
        filas = [(r.denominador, i, None,
                  getattr(r, cm) if cm else None,
                  getattr(r, cf) if cf else None, None)
                 for i, r in enumerate(m.itertuples(index=False))]
        stats["tramite"] = _insertar(con,
            "INSERT INTO proyecto_tramite (denominador,idx,camara,movimiento,fecha,"
            "resultado) VALUES (?,?,?,?,?,?)", filas, "tramite")

    # ── Hitos: dictamen / resultado / ley ────────────────────────────────────
    hitos: list[tuple] = []
    for df, hito, cdet in ((dicts_, "dictamen", None),
                           (res, "resultado", "resultado"),
                           (leyes, "ley", None)):
        if df is None or "proyecto_id" not in df.columns:
            continue
        d = df.copy(); d["proyecto_id"] = d["proyecto_id"].astype(str)
        d["denominador"] = d["proyecto_id"].map(id2d)
        d = d.dropna(subset=["denominador"])
        if hito == "resultado" and cdet in d.columns:
            d = d[d[cdet].notna() & (d[cdet].astype(str).str.strip() != "")]
        cf = "fecha" if "fecha" in d.columns else None
        for r in d.itertuples(index=False):
            hitos.append((r.denominador, hito,
                          getattr(r, cf) if cf else None,
                          str(getattr(r, cdet)) if (cdet and cdet in d.columns) else None))
    stats["hitos"] = _insertar(con,
        "INSERT INTO proyecto_hitos (denominador,hito,fecha,detalle) VALUES (?,?,?,?)",
        hitos, "hitos")

    # ── Giro AL INGRESAR (contrato de Franco, 07-08) ─────────────────────────
    if gini is not None and "proyecto_id" in gini.columns:
        gi = gini.copy(); gi["proyecto_id"] = gi["proyecto_id"].astype(str)
        gi["denominador"] = gi["proyecto_id"].map(id2d)
        gi = gi.dropna(subset=["denominador"])
        cn = "n_giros_inicial" if "n_giros_inicial" in gi.columns else None
        cf = "fuente" if "fuente" in gi.columns else None
        if cn:
            filas = [(int(getattr(r, cn)), getattr(r, cf) if cf else None, r.denominador)
                     for r in gi.itertuples(index=False)]
            for i in range(0, len(filas), LOTE):
                con.executemany("UPDATE proyectos SET n_giros_inicial=?,"
                                " n_giros_inicial_fuente=? WHERE denominador=?",
                                filas[i:i + LOTE])
            con.commit()
            stats["giro_inicial"] = len(filas)
            logger.info("  %-22s %8d", "giro inicial", len(filas))

    con.execute("PRAGMA optimize")
    con.close()
    _publicar()
    return stats


def verificar() -> None:
    if not DB.exists():
        raise SystemExit(f"no existe {DB}")
    # Leer la base DESDE el mount tambien puede fallar por locks: se lee una
    # copia local. Es solo para contar, asi que da igual.
    tmp = Path(tempfile.gettempdir()) / "proyectos_check.db"
    shutil.copyfile(DB, tmp)
    con = sqlite3.connect(str(tmp))
    print(f"\n  {'tabla':24} {'filas':>10}")
    print("  " + "-" * 36)
    for t in ("proyectos", "proyecto_autores", "proyecto_giros",
              "proyecto_tramite", "proyecto_hitos", "proyecto_taxonomias"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:24} {n:>10,}")
    print()
    for q, t in ((("SELECT tipo, COUNT(*) FROM proyectos GROUP BY tipo"
                   " ORDER BY 2 DESC LIMIT 5"), "por tipo"),
                 ("SELECT camara, COUNT(*) FROM proyectos GROUP BY camara", "por camara"),
                 ("SELECT hito, COUNT(*) FROM proyecto_hitos GROUP BY hito", "hitos")):
        print(f"  {t}: " + " · ".join(f"{a}={b:,}" for a, b in con.execute(q)))
    con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verificar", action="store_true", help="solo contar la base existente")
    a = ap.parse_args()
    if a.verificar:
        verificar(); return 0
    st = migrar()
    logger.info("LISTO -> %s", DB)

    # Restaurar las TAXONOMIAS (2026-08-07). `migrar()` rehace la base desde cero,
    # y `proyecto_taxonomias` es lo unico que NO se puede reconstruir: la llena el
    # agente LLM y cuesta llamadas a la API. Sin esto, correr este script —que es
    # un comando inocente y documentado— borra trabajo pago. Se restaura SOLO, sin
    # depender de que alguien se acuerde, que es como se pierden las cosas.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import taxonomias_backup as tb
        n = tb.restaurar()
        if n:
            logger.info("taxonomias restauradas desde el respaldo versionado: %d", n)
    except (ImportError, OSError, ValueError) as e:
        logger.error("NO pude restaurar las taxonomias (%s). Si habia clasificaciones, "
                     "recuperarlas con: python datos/proyectos/src/taxonomias_backup.py "
                     "restaurar", e)

    verificar()
    # Control de integridad: si un numero no cierra, corta con exit 1.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import verificar as v
    c = v.Control()
    v.controles_base(c, etapa="ckan")  # el bot todavia no cargo
    return c.informe()


if __name__ == "__main__":
    sys.exit(main())
