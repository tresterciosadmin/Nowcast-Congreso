# -*- coding: utf-8 -*-
"""Todo dato que el MOTOR lee tiene que viajar por git.

El bug va OCHO veces: un archivo cae en un comodin del `.gitignore`, vive en un
solo disco, y quien clona no obtiene un error sino una columna vacia. Las ocho:
parquet de expedientes (11-07), roster de jefes (30-07), salidas del embudo
(31-07), padron del Senado (04-08), contratos entre modulos (06-08), registro de
taxonomias (06-09), alias de legislador_id (08-09) y
`variables/legislador/data/legislador_bloques.parquet` (08-09, esta limpieza).

La octava es la que motivo este archivo, y muestra por que un test hace falta.
`origen_por_acta.py:154` lee ese parquet con un `if p.exists()` pelado, sin
warning. Sin el, `_mapa_autor_linaje` devuelve `{}` y la variable ORIGEN del
motor cae a DESCONOCIDO en 39.249 de 41.470 filas de `features_proyecto.parquet`
(94,6%), con `match_autor` de 96,07% a 0%. Nadie recibe un error. Y la
regeneracion no lo salva: `REGENERAR.ps1` tiene ocho pasos y ninguno corre
`variables/legislador/src/ficha.py`, que es lo unico que escribe ese parquet.

**Como esta escrito, y por que asi.** Es una PROPIEDAD, no una lista del dia
(regla de la casa): la lista de insumos se DERIVA del inventario del MAPA en cada
corrida, asi que un insumo nuevo del motor queda cubierto sin que nadie se
acuerde de agregarlo aca. Lo unico escrito a mano son las excepciones, y cada una
lleva por que.

    python -m pytest tests/test_insumos_del_motor_viajan.py -q
    python tests/test_insumos_del_motor_viajan.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
MAPA_JSON = RAIZ_PROYECTO / ".mapa" / "mapa.json"

# El MOTOR, tal como lo define CLAUDE.md ("Regla del MOTOR", ADR-0015).
MOTOR = (
    "modelo/ensemble/",
    "modelo/agregador_institucional/",
    "modelo/voto_individual/",
    "variables/bloque/",
    "variables/proyecto/",
    "variables/embudo/",
)

# Excepciones: rutas que el inventario atribuye al motor y que NO tienen que
# viajar. Cada una con el motivo MEDIDO, no supuesto. Si una deja de estar
# atribuida al motor, el test avisa para que se borre de aca: una excepcion que
# ya no aplica es una puerta abierta que nadie mira.
EXCEPCIONES = {
    "datos/canonica/data/clean/_decada_csv/diputados.csv":
        "Atribucion FALSA del inventario, por colision de basename: "
        "`comparar_vias_icg.py:76` lee `datos/padron/data/padron_diputados.csv`, "
        "y el indexador matchea el sufijo `diputados.csv`. El unico codigo que "
        "nombra `_decada_csv` es `run_pipeline.py:30`, que lo ESCRIBE. Es un "
        "intermedio regenerable de la semilla historica.",
}


def _git(*args: str) -> subprocess.CompletedProcess:
    # `--no-optional-locks`: un test de solo lectura no toma un lock de escritura.
    # En este repo los `.git/*.lock` huerfanos ya bloquearon commits de otros.
    return subprocess.run(["git", "--no-optional-locks", *args],
                          cwd=str(RAIZ_PROYECTO),
                          capture_output=True, text=True, timeout=120)


def _hay_git() -> bool:
    return _git("rev-parse", "--git-dir").returncode == 0


def _es_del_motor(ruta: str) -> bool:
    return any(ruta.startswith(m) for m in MOTOR)


def insumos_del_motor() -> dict[str, list[str]]:
    """ruta del dato -> archivos del motor que lo leen, segun el inventario."""
    if not MAPA_JSON.exists():
        return {}
    inventario = json.loads(MAPA_JSON.read_text(encoding="utf-8")).get("inventario_datos", [])
    salida = {}
    for item in inventario:
        lectores = [l for l in item.get("leen", []) if _es_del_motor(l)]
        if lectores:
            salida[item["ruta"]] = lectores
    return salida


def test_el_inventario_esta_disponible():
    """Sin inventario este archivo pasaria en verde sin controlar nada.

    Un test que no puede fallar es peor que no tenerlo: entrena a creerle.
    """
    assert MAPA_JSON.exists(), (
        f"falta {MAPA_JSON.relative_to(RAIZ_PROYECTO)}: reindexar con "
        "`python .mapa/indexar.py`. Sin el, este control no controla nada.")
    assert insumos_del_motor(), (
        "el inventario no atribuye NINGUN dato al motor. O el indice quedo viejo "
        "(reindexar) o cambiaron los nombres de los modulos en MOTOR.")


def test_los_insumos_del_motor_no_estan_ignorados():
    """Un insumo ignorado vive en un solo disco, y su ausencia no da error."""
    if not _hay_git():
        return
    ignorados = []
    for ruta, lectores in sorted(insumos_del_motor().items()):
        if ruta in EXCEPCIONES:
            continue
        if _git("check-ignore", "-q", ruta).returncode == 0:
            quien = ", ".join(sorted({Path(l).name for l in lectores}))
            ignorados.append(f"{ruta}\n      lo leen: {quien}")
    assert not ignorados, (
        "estos datos los LEE el motor y git los IGNORA, o sea que viven en un solo "
        "disco:\n    " + "\n    ".join(ignorados)
        + "\n  Es el modo de falla que el .gitignore ya documenta ocho veces: el "
          "archivo falta, nadie recibe un error, y el modelo mide sobre una columna "
          "vacia. Si de verdad no tiene que viajar, agregalo a EXCEPCIONES con el "
          "motivo MEDIDO, no lo dejes caer en un comodin.")


def test_no_quedan_excepciones_que_ya_no_aplican():
    """Una excepcion vencida es una puerta abierta que nadie mira."""
    atribuidos = set(insumos_del_motor())
    if not atribuidos:
        return
    sobran = sorted(set(EXCEPCIONES) - atribuidos)
    assert not sobran, (
        "estas rutas estan en EXCEPCIONES y el inventario ya NO las atribuye al "
        "motor: " + ", ".join(sobran)
        + ". Borralas de EXCEPCIONES; si se quedan, tapan un insumo nuevo que "
          "caiga en la misma ruta.")


if __name__ == "__main__":
    import sys
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"[OK ] {nombre}")
            except AssertionError as e:
                fallas += 1
                print(f"[FALLA] {nombre}\n  {e}")
    n = len(insumos_del_motor())
    print(f"\n{n} datos atribuidos al motor · {len(EXCEPCIONES)} excepcion(es) declarada(s)")
    raise SystemExit(1 if fallas else 0)
