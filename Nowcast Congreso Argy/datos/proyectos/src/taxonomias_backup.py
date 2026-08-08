"""datos/proyectos/src/taxonomias_backup.py
RESPALDO VERSIONADO de `proyecto_taxonomias` — lo único de la base que no se
puede reconstruir.

Por qué existe (2026-08-07). `proyectos.db` **no viaja a git** (90 MB) y se
regenera en un minuto con `migrar_ckan.py` + `upsert_bot.py`. Eso es correcto para
todo… salvo para `proyecto_taxonomias`: esa tabla no sale de ninguna fuente
pública, **la llena el agente LLM y cuesta llamadas a la API**. Un
`migrar_ckan.py` corrido de más —que es un comando inocente, documentado en el
README y que cualquiera del equipo puede ejecutar— **borra trabajo pago**.

El riesgo no es hipotético: es la misma forma de todos los incidentes del
proyecto (el corrector construido sobre datos viejos, el `p_embudo` mutilado, los
tres ítems de URGENTE que ya estaban resueltos). El dato existe, la implicación
no está escrita, y alguien actúa razonablemente y rompe algo.

**Se resuelve hoy porque hoy es gratis:** la tabla está en 0 filas. Montar el
respaldo cuando ya haya 100.000 clasificaciones es pagar la API dos veces.

CONTRATO
    `datos/proyectos/data/taxonomias.csv` — versionado (excepción en .gitignore).
    Columnas: denominador · taxonomia_id · taxonomia · fuente · confianza · asignada_en

CÓMO SE USA (lo importante es que la restauración NO dependa de que alguien se acuerde)
    python datos/proyectos/src/taxonomias_backup.py exportar   # db  -> csv
    python datos/proyectos/src/taxonomias_backup.py restaurar  # csv -> db
    python datos/proyectos/src/taxonomias_backup.py estado     # compara ambos

`migrar_ckan.py` debería llamar a `restaurar()` al final (ver README). Mientras eso
no esté, el paso queda en el runbook post-pull.

PRECEDENCIA al restaurar: `fuente='humano'` **nunca** se pisa con `fuente='agente'`.
Una clasificación revisada por una persona vale más que una del modelo, y el agente
ya respeta esa regla al escribir (`persistir()` en agente_taxonomias.py).

4 directivas: errores específicos, parsing defensivo, logging estructurado.
"""
from __future__ import annotations

import argparse
import csv
import logging
import sqlite3
import sys
from pathlib import Path

logger = logging.getLogger("proyectos.taxo_backup")

DATA = Path(__file__).resolve().parents[1] / "data"
DB = DATA / "proyectos.db"
CSV = DATA / "taxonomias.csv"
COLS = ["denominador", "taxonomia_id", "taxonomia", "fuente", "confianza", "asignada_en"]


def _con(db: Path) -> sqlite3.Connection:
    if not db.exists():
        raise FileNotFoundError(
            f"no existe {db}. Crearla con:\n"
            "  python datos/proyectos/src/migrar_ckan.py\n"
            "  python datos/proyectos/src/upsert_bot.py")
    return sqlite3.connect(db)


def exportar(db: Path = DB, csv_path: Path = CSV) -> int:
    """Vuelca la tabla al CSV versionado. Devuelve la cantidad de filas."""
    con = _con(db)
    try:
        filas = con.execute(
            f"SELECT {', '.join(COLS)} FROM proyecto_taxonomias "
            "ORDER BY denominador, taxonomia_id").fetchall()
    except sqlite3.OperationalError as e:
        logger.error("no pude leer proyecto_taxonomias: %s", e)
        return 0
    finally:
        con.close()

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    # Se escribe SIEMPRE, aunque haya 0 filas: un CSV vacío con encabezado es la
    # señal de que el respaldo existe y está al día. Si no se escribiera, no habría
    # forma de distinguir "no hay taxonomías" de "nadie corrió el respaldo".
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(filas)
    logger.info("exportadas %d filas -> %s", len(filas), csv_path)
    return len(filas)


def restaurar(db: Path = DB, csv_path: Path = CSV) -> int:
    """Carga el CSV en la base. Idempotente. No pisa lo marcado como 'humano'.

    Devuelve cuántas filas se insertaron o actualizaron.
    """
    if not csv_path.exists():
        logger.info("no hay respaldo en %s: nada que restaurar", csv_path)
        return 0
    con = _con(db)
    try:
        humanas = {r[0] for r in con.execute(
            "SELECT denominador || '|' || COALESCE(taxonomia_id,'') "
            "FROM proyecto_taxonomias WHERE fuente='humano'")}
        with csv_path.open(encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            faltan = set(COLS) - set(lector.fieldnames or [])
            if faltan:
                raise ValueError(f"el respaldo no tiene las columnas {sorted(faltan)}")
            filas, saltadas = [], 0
            for r in lector:
                den = (r.get("denominador") or "").strip()
                if not den:
                    continue
                clave = f"{den}|{(r.get('taxonomia_id') or '').strip()}"
                if clave in humanas and (r.get("fuente") or "") != "humano":
                    saltadas += 1          # ya hay revisión humana: no se pisa
                    continue
                try:
                    conf = float(r["confianza"]) if r.get("confianza") else None
                except ValueError:
                    conf = None
                filas.append((den, r.get("taxonomia_id"), r.get("taxonomia"),
                              r.get("fuente"), conf, r.get("asignada_en")))
        if filas:
            con.executemany(
                "INSERT OR REPLACE INTO proyecto_taxonomias "
                f"({', '.join(COLS)}) VALUES (?, ?, ?, ?, ?, ?)", filas)
            con.commit()
        logger.info("restauradas %d filas desde %s%s", len(filas), csv_path,
                    f" ({saltadas} salteadas por tener revisión humana)" if saltadas else "")
        return len(filas)
    finally:
        con.close()


def estado(db: Path = DB, csv_path: Path = CSV) -> dict:
    """Compara base y respaldo. Sirve de alarma barata: si la base tiene filas y
    el respaldo no, hay trabajo del agente sin proteger."""
    n_db = 0
    if db.exists():
        con = _con(db)
        try:
            n_db = con.execute("SELECT COUNT(*) FROM proyecto_taxonomias").fetchone()[0]
        except sqlite3.OperationalError:
            n_db = -1
        finally:
            con.close()
    n_csv = 0
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as f:
            n_csv = max(0, sum(1 for _ in f) - 1)
    return {"en_base": n_db, "en_respaldo": n_csv, "desprotegidas": max(0, n_db - n_csv)}


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("accion", choices=["exportar", "restaurar", "estado"])
    a = ap.parse_args(argv)

    if a.accion == "exportar":
        n = exportar()
        print(f"\n{n} clasificaciones respaldadas en {CSV}")
        if n == 0:
            print("(la tabla está vacía: el respaldo queda con solo el encabezado, "
                  "que es la señal de que el mecanismo está montado)")
    elif a.accion == "restaurar":
        n = restaurar()
        print(f"\n{n} clasificaciones restauradas en la base")
    else:
        e = estado()
        print(f"\nen la base: {e['en_base']} · en el respaldo: {e['en_respaldo']}")
        if e["desprotegidas"]:
            print(f"⚠️  {e['desprotegidas']} clasificaciones SIN respaldar. "
                  f"Correr: python {Path(__file__).name} exportar")
        else:
            print("✅ nada sin respaldar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
