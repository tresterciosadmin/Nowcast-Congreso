"""Cuarentena — la base aparte de lo que NO se pudo leer bien.

## La decisión (Valle, 2026-08-07)

> *"Los pendientes de revisión van a una base de datos distinta y los que están
> bien pasan a la base de datos general."*

Separación **física**, no una etiqueta. `proyectos.db` queda limpia por definición:
si una fila está ahí, se leyó bien. Lo dudoso vive en `cuarentena.db` con el motivo
y la fila cruda, esperando que una persona lo mire.

## Por qué no es "frenar la carga"

El primer intento hacía `SystemExit` ante cualquier fila rara. **Está mal para este
proyecto**: el bot corre solo todos los días y los refrescos traen 300+ proyectos.
Frenar 300 porque uno vino raro es el mismo error que ya se había corregido en el
workflow con `continue-on-error` — una fuente caída no puede matar la recolección.

Una fila rara es **normal**: la fuente cambia, aparece un tipo nuevo.

## Pero una AVALANCHA de filas raras sí frena

Si de golpe se cuarentenan 300 en vez de 3, eso no es "una fila rara": es que la
fuente cambió de formato. Ahí sí conviene mirar antes de seguir. El umbral está en
`TASA_MAXIMA` y es lo que separa "anomalía" de "algo se rompió".
"""
from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("cuarentena")

RAIZ = Path(__file__).resolve().parents[3]
DB = RAIZ / "datos" / "proyectos" / "data" / "cuarentena.db"

# Si más de este % de una tanda cae en cuarentena, la carga FRENA: no es una fila
# rara, es la fuente que cambió.
TASA_MAXIMA = 0.05

# ...pero con un PISO ABSOLUTO, y esto salió de probarlo. Con sólo el porcentaje,
# una tanda chica frena de más: el bot diario puede traer 20 expedientes y uno raro
# ya es 5%. Un cron que aborta por una fila rara vuelve al problema de origen (una
# fuente caída matando la recolección entera). Debajo de este número NUNCA frena:
# se apartan las filas, se avisa, y la carga sigue.
MINIMO_ABSOLUTO = 10

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pendientes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    detectado_en  TEXT NOT NULL,
    origen        TEXT NOT NULL,   -- 'tp_diputados' | 'dae_senado' | ...
    motivo        TEXT NOT NULL,   -- por qué no pasó
    clave         TEXT,            -- el expediente, si se pudo leer
    fila_cruda    TEXT,            -- JSON de la fila entera, para no perder nada
    resuelto      INTEGER DEFAULT 0,
    nota_revision TEXT
);
CREATE INDEX IF NOT EXISTS ix_pend_origen   ON pendientes(origen);
CREATE INDEX IF NOT EXISTS ix_pend_resuelto ON pendientes(resuelto);
"""


class Avalancha(SystemExit):
    """Demasiadas filas en cuarentena: la fuente cambió, no es una anomalía."""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Cuarentena:
    """Acumula lo dudoso y lo escribe aparte. Nunca toca `proyectos.db`."""

    def __init__(self, origen: str) -> None:
        self.origen = origen
        self.filas: list[dict] = []

    def apartar(self, motivo: str, clave, fila: dict) -> None:
        """Esta fila NO entra a la base general. Se guarda entera, sin interpretar."""
        self.filas.append({
            "motivo": motivo,
            "clave": None if clave is None else str(clave),
            "fila_cruda": json.dumps(
                {k: (None if v is None else str(v)) for k, v in fila.items()},
                ensure_ascii=False),
        })

    def __len__(self) -> int:
        return len(self.filas)

    def controlar_tasa(self, total: int) -> None:
        """Una fila rara es normal. Muchas juntas significan otra cosa."""
        if not total or not self.filas:
            return
        tasa = len(self.filas) / total
        if len(self.filas) < MINIMO_ABSOLUTO:
            logger.warning("cuarentena: %d de %d filas de %s (%.1f%%) — por debajo "
                           "del piso de %d, no freno la carga",
                           len(self.filas), total, self.origen, tasa * 100,
                           MINIMO_ABSOLUTO)
            return
        if tasa > TASA_MAXIMA:
            motivos = {}
            for f in self.filas:
                motivos[f["motivo"]] = motivos.get(f["motivo"], 0) + 1
            raise Avalancha(
                f"\n🔴 {len(self.filas)} de {total} filas de `{self.origen}` "
                f"({tasa:.1%}) cayeron en cuarentena, y el máximo tolerado es "
                f"{TASA_MAXIMA:.0%} (con piso de {MINIMO_ABSOLUTO} filas).\n"
                f"   Eso no es una fila rara: es la fuente que cambió de formato.\n"
                f"   Motivos: {motivos}\n"
                "   Revisá el parser antes de seguir. Si el formato nuevo es "
                "legítimo, actualizá el parser; si no, subí TASA_MAXIMA a "
                "conciencia y dejá dicho por qué.")

    def guardar(self) -> int:
        """Escribe en `cuarentena.db`. Devuelve cuántas filas apartó."""
        if not self.filas:
            logger.info("cuarentena: 0 filas de %s ✓", self.origen)
            return 0
        DB.parent.mkdir(parents=True, exist_ok=True)
        # Mismo rodeo que el resto: el mount no soporta el locking de SQLite.
        trabajo = Path(tempfile.gettempdir()) / "cuarentena_build.db"
        if DB.exists():
            shutil.copyfile(DB, trabajo)
        elif trabajo.exists():
            trabajo.unlink()
        con = sqlite3.connect(str(trabajo))
        con.executescript(ESQUEMA)
        # Se reemplaza lo no resuelto de este origen: la cuarentena refleja el
        # estado de la ÚLTIMA corrida, no un historial que crece solo.
        con.execute("DELETE FROM pendientes WHERE origen = ? AND resuelto = 0",
                    (self.origen,))
        ahora = _ahora()
        con.executemany(
            "INSERT INTO pendientes (detectado_en, origen, motivo, clave, fila_cruda)"
            " VALUES (?,?,?,?,?)",
            [(ahora, self.origen, f["motivo"], f["clave"], f["fila_cruda"])
             for f in self.filas])
        con.commit()
        con.close()
        shutil.copyfile(trabajo, DB)
        logger.warning("cuarentena: %d filas de %s apartadas -> %s",
                       len(self.filas), self.origen, DB.name)
        return len(self.filas)


def resumen() -> list[tuple]:
    """Qué hay esperando revisión. Para el informe y para los humanos."""
    if not DB.exists():
        return []
    tmp = Path(tempfile.gettempdir()) / "cuarentena_lee.db"
    try:
        shutil.copyfile(DB, tmp)
        con = sqlite3.connect(str(tmp))
    except OSError:
        con = sqlite3.connect(str(DB))
    filas = list(con.execute(
        "SELECT origen, motivo, COUNT(*) FROM pendientes WHERE resuelto = 0"
        " GROUP BY origen, motivo ORDER BY 3 DESC"))
    con.close()
    return filas


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    filas = resumen()
    if not filas:
        print("\n  ✅ Cuarentena vacía: no hay nada esperando revisión.\n")
        return 0
    print(f"\n  PENDIENTES DE REVISIÓN — {DB}")
    print("  " + "-" * 66)
    for origen, motivo, n in filas:
        print(f"  {n:>5}  {origen:<16} {motivo}")
    print("  " + "-" * 66)
    print(f"  {sum(f[2] for f in filas):>5}  TOTAL\n")
    print("  Para ver las filas crudas de un motivo:")
    print("    python -c \"import sqlite3;[print(r) for r in "
          "sqlite3.connect('datos/proyectos/data/cuarentena.db')"
          ".execute('SELECT clave, fila_cruda FROM pendientes WHERE resuelto=0 LIMIT 5')]\"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
