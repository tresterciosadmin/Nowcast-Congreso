"""variables/asistencia_quorum/src/asistencia.py
Escalón 1 del módulo de asistencia/quórum: PRESENTISMO por legislador.

La asistencia ya vive en la canónica: en cada acta, cada legislador figura con su voto,
y voto == AUSENTE marca la inasistencia. "Presente" = emitió algo (AFIRMATIVO / NEGATIVO /
ABSTENCION); "Ausente" = AUSENTE.

Salida (contrato para modelo/agregador_institucional):
  - outputs/presentismo_legislador.csv         (legislador_id -> p_present global, n)
  - outputs/presentismo_legislador_periodo.csv (legislador_id x periodo -> p_present, n)
La unidad temporal es el PERÍODO PARLAMENTARIO (recambios del 10-dic de años impares), igual
que disciplina/ficha: cada recambio reconfigura quién asiste.

Es el baseline del módulo (gate de pase: superarlo con el escalón 2). Pero además ya sirve:
alimenta al agregador con los PRESENTES esperados por bloque en vez de todas las bancas,
corrigiendo el sesgo pesimista del motor en las votaciones peleadas.

Uso:
  python variables/asistencia_quorum/src/asistencia.py
  CANON=/ruta/clean OUT=/ruta/salida python .../asistencia.py
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

# ── definiciones compartidas ──────────────────────────────────────────────────
# `periodo_parlamentario` vivía copiada acá, sincronizados a mano; el único
# control era un docstring que pedía "mantener sincronizadas". Unificados el
# 2026-08-25 en `definiciones.py` (raíz) — ADR-0014. Se RE-EXPORTA para que
# `asistencia.<nombre>` siga existiendo: aguas abajo no cambia nada.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(next(d for d in _Path(__file__).resolve().parents
                             if (d / "rutas.py").is_file())))
from definiciones import periodo_parlamentario  # noqa: E402,F401

log = logging.getLogger("asistencia")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

PRESENTES = {"AFIRMATIVO", "NEGATIVO", "ABSTENCION"}  # AUSENTE = inasistencia


def calcular_presentismo(votos: pd.DataFrame, actas: pd.DataFrame,
                         min_votos: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (presentismo_global, presentismo_por_periodo). p_present en [0,1]."""
    faltan = [c for c in ("acta_id", "legislador_id", "voto") if c not in votos.columns]
    if faltan:
        raise ValueError(f"votos: faltan columnas {faltan}")
    v = votos[["acta_id", "legislador_id", "voto"]].copy()
    v["presente"] = v["voto"].isin(PRESENTES).astype(int)
    # fecha/periodo desde actas
    a = actas[["acta_id", "fecha"]].copy()
    a["anio"] = pd.to_datetime(a["fecha"], errors="coerce").dt.year
    a["periodo"] = periodo_parlamentario(a["fecha"], a["anio"])
    v = v.merge(a[["acta_id", "periodo"]], on="acta_id", how="left")

    glob = (v.groupby("legislador_id")
              .agg(p_present=("presente", "mean"), n=("presente", "size"))
              .reset_index())
    glob["p_present"] = glob["p_present"].round(4)
    glob = glob[glob["n"] >= min_votos].sort_values("p_present")

    per = (v.dropna(subset=["periodo"]).groupby(["legislador_id", "periodo"])
             .agg(p_present=("presente", "mean"), n=("presente", "size"))
             .reset_index())
    per["p_present"] = per["p_present"].round(4)
    per = per[per["n"] >= min_votos]
    return glob, per


def main() -> None:
    here = Path(__file__).resolve()
    root = here.parents[3]
    canon = Path(os.environ.get("CANON", root / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", here.parents[1] / "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    min_votos = int(os.environ.get("MIN_VOTOS", "5"))

    votos = pd.read_parquet(canon / "votos_resuelto.parquet")
    actas = pd.read_parquet(canon / "actas_canonico.parquet")
    glob, per = calcular_presentismo(votos, actas, min_votos=min_votos)

    glob.to_csv(out / "presentismo_legislador.csv", index=False, encoding="utf-8-sig")
    per.to_csv(out / "presentismo_legislador_periodo.csv", index=False, encoding="utf-8-sig")

    log.info("presentismo: %d legisladores (global), %d filas legislador×período",
             len(glob), len(per))
    pg = float((votos["voto"].isin(PRESENTES)).mean())
    log.info("presentismo global de la base: %.3f  | mediana por legislador: %.3f",
             pg, float(glob["p_present"].median()))
    print(glob.head(8).to_string(index=False))
    print("...")
    print(glob.tail(8).to_string(index=False))


if __name__ == "__main__":
    main()
