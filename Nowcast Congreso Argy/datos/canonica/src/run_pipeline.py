"""datos/canonica/src/run_pipeline.py
Reconstruye la base canónica de votaciones de CERO, en orden:
  semilla CSV (Década Votada) + CKAN + argentinadatos + Excel 2026
  -> build (merge/dedup/validación) -> resolución de entidades -> baseline.

Uso:
  python datos/canonica/src/run_pipeline.py          # escribe en datos/canonica/data/clean
  WORK=/ruta python .../run_pipeline.py              # usa otra carpeta de trabajo
Requisitos: internet (CKAN y argentinadatos se descargan), deps de cada módulo.
"""
from __future__ import annotations
import os, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(os.environ.get("WORK", ROOT / "datos" / "canonica" / "data" / "clean"))
SRC = WORK / "_sources"; SRC.mkdir(parents=True, exist_ok=True)

def run(rel, env):
    e = dict(os.environ); e.update({k: str(v) for k, v in env.items()})
    print(f"\n=== {rel} ===", flush=True)
    subprocess.run([sys.executable, str(ROOT / rel)], check=True, env=e)

def main():
    # 1. Semilla Década Votada (descomprimir el CSV de los Aportes)
    zp = ROOT / "Aportes sobre dataset congreso" / "towlandia-master" / "public" / "DecadaVotadaCSV.zip"
    csvdir = WORK / "_decada_csv"; csvdir.mkdir(exist_ok=True)
    if zp.exists():
        with zipfile.ZipFile(zp) as z: z.extractall(csvdir)
        run("datos/decada_votada/src/from_csv.py", {"CSV": csvdir, "OUT": SRC})
    else:
        print("[warn] no está DecadaVotadaCSV.zip; salteo la semilla histórica")
    # 2. CKAN Diputados (2011-2019)   3. argentinadatos (2020-2025)   4. Excel 2026
    run("datos/ckan_diputados/src/to_canonical.py", {"OUT": SRC})
    run("datos/argentinadatos/src/to_canonical.py", {"OUT": SRC})
    xlsx = ROOT / "datos" / "manual_2026" / "Congreso_25-27.xlsx"
    if xlsx.exists():
        run("datos/manual_2026/src/to_canonical.py", {"XLSX": xlsx, "OUT": SRC})
    # 5. Build canónica  6. Entidades  7. Baseline
    run("datos/canonica/src/build.py", {"SOURCES": SRC, "CLEAN": WORK, "SCHEMAS": ROOT / "docs" / "schemas"})
    run("datos/canonica/src/entity_resolution.py", {"CANON": WORK, "OUT": WORK})
    run("evaluacion/baseline/src/baseline_canonico.py", {"CANON": WORK})
    print(f"\nOK. Base canónica en: {WORK}")

if __name__ == "__main__":
    main()
