"""Control de integridad de proyectos.db — que los fallos DEJEN de ser silenciosos.

## Por que existe

El 07-08-2026, cargar el bot produjo tres errores y **ninguno dio error**:

| sintoma | lo que pasaba |
|---|---|
| la cohorte subio **+1** en vez de +671 | las altas del bot no tienen id de CKAN; `astype(str)` volvia `"None"` a los 1.531 nulos y `drop_duplicates` los colapsaba a UNA fila |
| el log decia **559** giros corregidos donde antes decia 633 | el bot pisaba el giro ACUMULADO con el giro AL INGRESAR y borraba 109 giros |
| **34 expedientes** descartados como "formato inesperado" | eran los del PODER EJECUTIVO, los de mayor peso del modelo (convierte ~77%) |

Los tres se encontraron **mirando si el numero que salio era el que tenia que salir**.
Ninguno se habria notado viendo si el programa terminaba bien. Este modulo convierte
esa mirada en codigo: cada invariante que no se cumple **corta con exit != 0**.

## Uso

    python datos/proyectos/src/verificar.py            # todo
    python datos/proyectos/src/verificar.py --rapido   # sin la cohorte (2 s en vez de ~40)

`migrar_ckan.py` y `upsert_bot.py` lo llaman solos al terminar.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

logger = logging.getLogger("verificar")

# Las rutas que cruzan de un modulo a otro salen de `rutas.py` (raiz del
# proyecto), no se cuentan niveles de carpeta a mano. Las cinco lineas de abajo
# buscan la raiz HACIA ARRIBA: si este archivo cambia de profundidad, siguen
# andando. Antes esto era `parents[3]`, repetido en 41 archivos.
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import (RAIZ, EXPEDIENTES_CLEAN, BOT_CLEAN, PROYECTOS_DB,  # noqa: E402
                   EMBUDO_COHORTE_DOS_RUTAS)

CLEAN = EXPEDIENTES_CLEAN
BOT = BOT_CLEAN
DB = PROYECTOS_DB


class Control:
    """Acumula resultados. Un solo FALLA hace que el proceso corte."""

    def __init__(self) -> None:
        self.filas: list[tuple[bool, str, str]] = []

    def check(self, ok: bool, nombre: str, detalle: str = "") -> bool:
        self.filas.append((ok, nombre, detalle))
        return ok

    def igual(self, a, b, nombre: str, nota: str = "") -> bool:
        det = f"{a:,} vs {b:,}" if isinstance(a, int) else f"{a} vs {b}"
        return self.check(a == b, nombre, det + (f" · {nota}" if nota else ""))

    def informe(self) -> int:
        print(f"\n  {'CONTROL DE INTEGRIDAD — proyectos.db':<62}")
        print("  " + "-" * 62)
        for ok, nombre, det in self.filas:
            print(f"  {'✅' if ok else '🔴'} {nombre:<44} {det}")
        malas = [f for f in self.filas if not f[0]]
        print("  " + "-" * 62)
        if malas:
            print(f"  🔴 {len(malas)} DE {len(self.filas)} CONTROLES FALLARON — NO USAR ESTA BASE\n")
            return 1
        print(f"  ✅ {len(self.filas)} controles OK")
        try:
            import cuarentena
            pend = cuarentena.resumen()
            if pend:
                tot = sum(f[2] for f in pend)
                print(f"  ⏳ {tot} fila(s) en CUARENTENA esperando revision "
                      "(`python datos/proyectos/src/cuarentena.py`)")
            else:
                print("  ✅ cuarentena vacia")
        except Exception:  # noqa: BLE001 - el informe nunca puede romper la carga
            pass
        print()
        return 0


def _abrir() -> sqlite3.Connection:
    if not DB.exists():
        raise SystemExit(f"no existe {DB}. Corre antes: migrar_ckan.py")
    tmp = Path(tempfile.gettempdir()) / "proyectos_verif.db"
    try:
        shutil.copyfile(DB, tmp)
        return sqlite3.connect(str(tmp))
    except OSError:
        return sqlite3.connect(str(DB))


def controles_base(c: Control, etapa: str = "completa") -> None:
    """`etapa`: 'ckan' = recien migrado, sin el bot todavia · 'completa' = con bot.

    ⚠️ Existe porque el primer intento corria TODOS los controles despues de
    `migrar_ckan.py` y reportaba "1 de 8 fallaron" cuando no fallaba nada: los
    cofirmantes solo pueden existir despues del bot. **Un control que grita cuando
    todo esta bien es peor que no tenerlo** — ensena a ignorarlo, que es
    exactamente el habito que estos controles vinieron a romper.
    """
    con_bot = etapa == "completa"
    con = _abrir()
    q = lambda s: con.execute(s).fetchone()[0]  # noqa: E731

    # ── 1. Nada se descarta en silencio al leer el bot ───────────────────────
    # El caso de los 34 del Ejecutivo: el parser no fallaba, sólo saltaba filas.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import upsert_bot as ub
    for nombre, arch, col, fn in () if not con_bot else (
            ("TP  (Diputados)", "tp_entradas.parquet", "expediente", lambda x: x),
            ("DAE (Senado)", "dae_entradas.parquet", "expediente", ub.denom_dae)):
        p = BOT / arch
        if not p.exists():
            continue
        d = pd.read_parquet(p).dropna(subset=[col])
        parseados = d[col].map(fn).notna().sum()
        c.igual(int(parseados), len(d), f"bot: {nombre} sin descartes",
                "toda fila del bot tiene que llegar a la base")

    # ── 2. Todo proyecto tiene tipo (si no, no entra a la cohorte de LEY) ────
    c.igual(q("SELECT COUNT(*) FROM proyectos WHERE tipo IS NULL"), 0,
            "todo proyecto tiene `tipo`", "sin tipo => invisible para el embudo")

    # ── 3. La llave no colapsa (el bug del +1) ──────────────────────────────
    c.igual(q("SELECT COUNT(*) FROM proyectos"),
            q("SELECT COUNT(DISTINCT COALESCE(proyecto_id, denominador)) FROM proyectos"),
            "la llave del embudo es unica",
            "COALESCE(proyecto_id, denominador) no puede repetirse")

    # ── 4. Lo de CKAN quedó INTACTO ─────────────────────────────────────────
    # Es lo que un upsert ciego habría borrado, y lo que el bot pisó con los giros.
    pares = [("expedientes_movimientos.parquet", "proyecto_tramite", "tramite de CKAN"),
             ("expedientes_giros.parquet", None, "giros acumulados de CKAN")]
    mov = CLEAN / pares[0][0]
    if mov.exists():
        c.igual(q("SELECT COUNT(*) FROM proyecto_tramite"), len(pd.read_parquet(mov)),
                "tramite de CKAN intacto", "el bot NO lo trae: si baja, lo borro")

    gp = CLEAN / "expedientes_giros.parquet"
    if gp.exists():
        g = pd.read_parquet(gp)
        g["pid"] = g["proyecto_id"].astype(str)
        conocidos = {r[0] for r in con.execute(
            "SELECT proyecto_id FROM proyectos WHERE proyecto_id IS NOT NULL")}
        esperados = int(g["pid"].isin(conocidos).sum())
        en_db = q("SELECT COUNT(*) FROM proyecto_giros g JOIN proyectos p USING(denominador)"
                  " WHERE p.proyecto_id IS NOT NULL")
        c.igual(en_db, esperados, "giros acumulados de CKAN intactos",
                "el giro AL INGRESAR va en n_giros_inicial, no aca")

    # ── 5. Cofirmantes: solo tienen sentido DESPUES del bot ─────────────────
    if con_bot:
        c.check(q("SELECT COUNT(*) FROM (SELECT denominador FROM proyecto_autores"
                  " GROUP BY denominador HAVING COUNT(*)>1)") > 0,
                "hay cofirmantes cargados", "si da 0, el merge perdio los firmantes")

    # ── 6. Ningun proyecto sin autor ni huerfano ────────────────────────────
    c.igual(q("SELECT COUNT(*) FROM proyecto_giros g LEFT JOIN proyectos p"
              " USING(denominador) WHERE p.denominador IS NULL"), 0,
            "no hay giros huerfanos")
    con.close()


MEDIDOR_COHORTE = EMBUDO_COHORTE_DOS_RUTAS


def control_cohorte(c: Control) -> None:
    """La prueba fuerte: las dos rutas tienen que coincidir en lo que comparten.

    El CONTROL sigue aca (es sobre `proyectos.db`), pero la MEDICION la hace
    `variables/embudo`, que es el dueno del concepto de cohorte. Se lo invoca
    como proceso y se consume su salida JSON — su contrato —, no su codigo.

    Antes esto hacia `sys.path.insert(.../variables/embudo/src); import embudo`:
    una dependencia hacia arriba (datos/ -> variables/) que CLAUDE.md prohibe, y
    que ademas hacia que `datos/proyectos` no se pudiera verificar si el embudo
    estaba roto. Cambiado el 2026-08-20; ver el encabezado de
    `variables/embudo/src/cohorte_dos_rutas.py`.
    """
    if not MEDIDOR_COHORTE.exists():
        c.check(False, "el medidor de cohorte existe",
                f"falta {MEDIDOR_COHORTE.relative_to(RAIZ)} — sin el, esta prueba NO corre")
        return

    r = subprocess.run([sys.executable, str(MEDIDOR_COHORTE)],
                       capture_output=True, text=True,
                       env={**os.environ, "CLEAN": str(CLEAN), "PROYECTOS_DB": str(DB)})
    if r.returncode != 0 or not r.stdout.strip():
        # Un control que no se pudo correr NO se saltea en silencio: eso es
        # exactamente como se perdieron tres errores el 07-08. Falla y se ve.
        c.check(False, "el control de cohorte pudo correr",
                (r.stderr or "sin salida").strip().splitlines()[-1][:160])
        return
    try:
        m = json.loads(r.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as e:
        c.check(False, "el control de cohorte devolvio JSON", str(e)[:160])
        return

    c.igual(m["n_comun"], m["n_parquet"], "la ruta SQLite no pierde proyectos de la vieja")
    c.check(m["n_sqlite"] > m["n_parquet"], "la cohorte CRECIO con lo del bot",
            f"{m['n_parquet']:,} -> {m['n_sqlite']:,} (+{m['n_sqlite'] - m['n_parquet']:,})")
    # Las de RESULTADO no pueden moverse jamas: no dependen del bot.
    for col, n in m["cols_movidas"].items():
        c.igual(n, 0, f"`{col}` sin cambios entre rutas",
                "una variable de RESULTADO que cambia = carga rota")


def main() -> int:
    logging.basicConfig(level=logging.ERROR)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rapido", action="store_true", help="saltear la cohorte (~40 s)")
    a = ap.parse_args()
    c = Control()
    controles_base(c)
    if not a.rapido:
        control_cohorte(c)
    return c.informe()


if __name__ == "__main__":
    sys.exit(main())
