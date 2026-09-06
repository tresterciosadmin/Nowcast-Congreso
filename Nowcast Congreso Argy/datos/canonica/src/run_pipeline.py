"""datos/canonica/src/run_pipeline.py
Reconstruye la base canónica de votaciones de CERO, en orden:
  semilla CSV (Década Votada) + CKAN + argentinadatos + Senado oficial 2015-23
  + Excel 2026
  -> build (merge/dedup/validación) -> resolución de entidades -> baseline.

Uso:
  python datos/canonica/src/run_pipeline.py          # escribe en datos/canonica/data/clean
  WORK=/ruta python .../run_pipeline.py              # usa otra carpeta de trabajo
Requisitos: internet (CKAN, argentinadatos y senado.gob.ar se descargan; el
Senado cachea HTML en datos/Archivos_Borrar, ~20 min la 1ª vez, ~1 min después),
deps de cada módulo.
"""
from __future__ import annotations
import os, shutil, subprocess, sys, zipfile
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
    # 2. CKAN Diputados (2011-2019)   3. argentinadatos (2020-2025)
    run("datos/ckan_diputados/src/to_canonical.py", {"OUT": SRC})
    run("datos/argentinadatos/src/to_canonical.py", {"OUT": SRC})
    # 4. EL EXCEL 2026 SALIÓ DEL PIPELINE (2026-09-06, decisión de Franco).
    #
    # Se armó cuando `argentinadatos` no cubría 2026 y cumplió su función. Hoy
    # `argentinadatos` tiene 205 actas desde el recambio del 10-dic-2025, y las 17 del
    # Excel resultaron ser LAS MISMAS votaciones: 12 coinciden voto por voto al 100% y
    # las otras 5 tienen el recuento idéntico (139/97/21, 130/106/14/7, 40/22/10) y
    # difieren sólo en el `legislador_id` de algunas personas.
    #
    # No aportaba y sí confundía: entraba sin fecha, sin expediente y sin tipo_mayoría,
    # con la PRECEDENCIA más alta de todas, y obligaba a `disciplina.py` y a `ficha.py`
    # a parchear `anio = 2026` cada uno por su lado.
    #
    # El Excel NO se borra: sigue siendo la planilla de trabajo de Franco y la hoja
    # RESUMEN tiene la fila "Tema que trata la ley". Lo que sale es su ingesta.
    # Para volver a prenderla: MANUAL_2026=1.
    xlsx = ROOT / "datos" / "manual_2026" / "Congreso_25-27.xlsx"
    if os.environ.get("MANUAL_2026") == "1" and xlsx.exists():
        print("[aviso] MANUAL_2026=1: el Excel vuelve a entrar. Sus 17 actas son gemelas "
              "de actas de argentinadatos; `build.py` las va a reportar como INDICIO.")
        run("datos/manual_2026/src/to_canonical.py", {"XLSX": xlsx, "OUT": SRC})
    # 4b. Senado oficial 2015-2023 (módulo datos/senado): scrape (con caché)
    #     + bloque histórico. Consumimos su SALIDA publicada (contrato), no su
    #     código interno: los parquet quedan en datos/senado/data/clean y se
    #     copian a SRC. El padrón de bloques está VERSIONADO (CSV curado); solo
    #     se regenera si faltara y hay anexos wiki descargados.
    sen_data = ROOT / "datos" / "senado" / "data"
    if not (sen_data / "padron_bloques_senado.csv").exists():
        run("datos/senado/src/bajar_anexos_wiki.py", {})
        run("datos/senado/src/padron_bloques.py", {})
    run("datos/senado/src/scrape_votaciones.py", {})
    run("datos/senado/src/aplicar_bloques.py", {})
    for f in ("senado_actas.parquet", "senado_votos.parquet"):
        shutil.copy2(sen_data / "clean" / f, SRC / f)
    # 5. Build canónica  6. Entidades  7. Baseline
    run("datos/canonica/src/build.py", {"SOURCES": SRC, "CLEAN": WORK, "SCHEMAS": ROOT / "docs" / "schemas"})
    run("datos/canonica/src/entity_resolution.py", {"CANON": WORK, "OUT": WORK})
    run("evaluacion/baseline/src/baseline_canonico.py", {"CANON": WORK})
    print(f"\nOK. Base canónica en: {WORK}")

if __name__ == "__main__":
    main()
