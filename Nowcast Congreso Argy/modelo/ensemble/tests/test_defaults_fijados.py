"""Los defaults del motor están FIJADOS: cambiar uno rompe este test (regla 8; ítem B1 de la auditoría 2026-09).

`modelo/ensemble/outputs/registro_parametros.json` es el registro de parámetros GENERADO DESDE EL CÓDIGO
(`modelo/ensemble/src/registro_parametros.py`): toda variable de entorno, constante con nombre y default
numérico de función que alcanza el camino de `nowcast()`, los archivos de datos que ese camino referencia y el
sha256 de los coeficientes estimados (β y θ). Este test regenera el registro desde el código de hoy y exige que
coincida con el guardado en lo que IMPORTA: clase, variable de entorno, default efectivo y texto de la expresión.
No mira la línea (cambia con cualquier edición) ni la medición `afecta_panel`.

QUÉ PASA CUANDO FALLA. El mensaje dice qué parámetro cambió, qué tenía el registro y qué hay en el código. Si el
cambio es A PROPÓSITO (una re-estimación), se regenera y se commitea el JSON citando la medición que lo
justifica (regla 8: «ningún default cambia sin un test que fije el valor nuevo y cite la medición»):

    python modelo/ensemble/src/registro_parametros.py --escribir

CONTROL POSITIVO (regla 5: un control tiene que poder fallar). La sección 4 toma el código REAL, le hace en
memoria los cambios que este test tiene que atrapar —`TAU_DEFAULT` 1,19 → 1,2 (el ejemplo del plan),
`EPSILON0_DEFAULT`, una bandera invertida, una constante borrada o nueva, un default de función, una lectura de
entorno nueva, un archivo de datos nuevo— y exige que CADA UNO aparezca como diferencia; y que lo que no es un
parámetro (un comentario, una línea corrida, un docstring) no la produzca. Si un sabotaje ya no se puede
aplicar (porque el texto que buscaba cambió), falla fuerte: un control que no se aplica no controla nada.

    python modelo/ensemble/tests/test_defaults_fijados.py
"""
from __future__ import annotations

import copy
import importlib
import os
import re
import sys
import tempfile
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


import registro_parametros as R  # noqa: E402

COMANDO = R.COMANDO

# ── 1. el registro guardado existe y tiene la forma ──────────────────────────────────────────────
print("1. el registro guardado existe y tiene la forma")
guardado = R.leer_guardado()
check(guardado is not None, f"falta {R.REGISTRO}: {COMANDO}")
guardado = guardado or {"parametros": [], "archivos_derivados": [], "estimados_fijados": {}, "clausura": []}
check(guardado.get("formato") == R.FORMATO, f"formato del registro {guardado.get('formato')!r} ≠ {R.FORMATO}")
check(len(guardado["parametros"]) > 100, f"el registro trae {len(guardado['parametros'])} parámetros (≈ 146 hoy)")
check(len({p["id"] for p in guardado["parametros"]}) == len(guardado["parametros"]), "hay ids repetidos")
check({"entorno", "constante", "default_funcion"} <= {p["clase"] for p in guardado["parametros"]},
      "el registro tiene que traer las tres clases de parámetro")
TERMINOS = ["EPSILON0", "TAU", "EPSILON0_DEFAULT", "TAU_DEFAULT", "INCERTIDUMBRE_LEGISLADOR", "RECORD_POR_TEMA",
            "SHRINK_RECORD", "K_SHRINK_RECORD", "MIN_HIST_INDIVIDUAL", "MIN_HIST_ANTERIOR", "GUARD_ERA",
            "ERA_FIJA", "BETA_DICTAMEN", "TEMA_AUTO", "COMBINAR_TEMAS", "SOBRE_TABLAS",
            "DESVIO_MIN_INDIVIDUAL", "MIN_VOTOS_FICHA", "DIAS_VENTANA_VIVA"]
nombres = {p["nombre"] for p in guardado["parametros"]} | {p["asignado_a"] for p in guardado["parametros"]}
faltan = [t for t in TERMINOS if t not in nombres]
check(not faltan, f"términos del informe que el registro no trae: {faltan}")
check(all(v["sha256"] for v in guardado["estimados_fijados"].values()) and guardado["estimados_fijados"],
      "el registro tiene que fijar el sha256 de los coeficientes estimados (β y θ)")

# ── 2. el código de hoy coincide con el registro ─────────────────────────────────────────────────
print("\n2. el código de hoy da EXACTAMENTE lo que el registro fija")
fuentes = R.cargar_fuentes()
actual = R.generar(fuentes=fuentes, previo=guardado)
dif = R.diferencias(guardado, actual)
check(not dif, "el código ya no coincide con `modelo/ensemble/outputs/registro_parametros.json` "
      f"({len(dif)} diferencias):\n      " + "\n      ".join(dif[:12])
      + ("\n      …" if len(dif) > 12 else "")
      + f"\n      Si el cambio es a propósito: regenerar con\n        {COMANDO}\n"
      "      y commitear el JSON citando la medición que lo justifica (regla 8).")

# ── 3. el valor del registro es el que el módulo tiene de verdad ─────────────────────────────────
print("\n3. el valor efectivo del registro coincide con el del módulo importado con el entorno limpio")
variables = {p["entorno"] for p in guardado["parametros"] if p["entorno"]}
guardadas = {v: os.environ.pop(v) for v in list(variables) if v in os.environ}
try:
    for rel in guardado["clausura"]:
        d = str(RAIZ_PROYECTO / Path(rel).parent)
        if d not in sys.path:
            sys.path.insert(0, d)
    comparados, distintos, no_importables = 0, [], []
    for rel in guardado["clausura"]:
        objetivos = [p for p in guardado["parametros"] if p["archivo"] == rel and p["evaluable"]
                     and p["asignado_a"] and p["clase"] in ("entorno", "constante")]
        if not objetivos:
            continue
        try:
            modulo = importlib.import_module(Path(rel).stem)
        except Exception as e:  # noqa: BLE001 — un módulo que no importa acá (dependencia opcional) no invalida el resto
            no_importables.append(f"{rel} ({type(e).__name__})")
            continue
        for p in objetivos:
            ok, valor = R._jsonable(getattr(modulo, p["asignado_a"], object()))
            comparados += 1
            if not ok or valor != p["default"]:
                distintos.append(f"{p['id']}: registro {p['default']!r} · módulo {valor!r}")
    check(comparados > 40, f"se compararon {comparados} parámetros contra los módulos (esperaba > 40)")
    check(not distintos, "el valor efectivo del registro no es el que el módulo tiene con el entorno vacío:\n      "
          + "\n      ".join(distintos))
    check(len(no_importables) <= 2, f"demasiados módulos que no se pudieron importar: {no_importables}")
    print(f"  {comparados} parámetros comparados contra el módulo real; "
          f"módulos que no importan acá: {no_importables or 'ninguno'}")
finally:
    os.environ.update(guardadas)


# ── 4. CONTROL POSITIVO: cada cambio de un default tiene que romper el test ──────────────────────
print("\n4. control positivo: los cambios sobre el código real SE DETECTAN (y lo que no es parámetro, no)")


def _con(archivo: str, reemplazos: list[tuple[str, str]] | None = None, agregar: str = "") -> dict[str, str]:
    """Copia de las fuentes con `reemplazos` (patrón regex → texto) aplicados a UN archivo y `agregar` al final."""
    rel = next(r for r in fuentes if r.endswith(archivo))
    copia = dict(fuentes)
    texto = fuentes[rel]
    for patron, nuevo in reemplazos or []:
        texto, n = re.subn(patron, nuevo, texto, count=1)
        if n != 1:
            check(False, f"el sabotaje no se puede aplicar: no encontré «{patron}» en {rel} "
                  "(un control que no se aplica no controla nada)")
    copia[rel] = texto + agregar
    return copia


def detecta(copia: dict[str, str]) -> list[str]:
    return R.diferencias(guardado, R.generar(fuentes=copia, previo=guardado))


def debe_detectar(nombre: str, copia: dict[str, str], *fragmentos: str) -> None:
    d = detecta(copia)
    texto = "\n".join(d)
    check(bool(d), f"SABOTAJE NO DETECTADO: {nombre}")
    for f in fragmentos:
        check(f in texto, f"el sabotaje «{nombre}» se detectó pero no nombra {f!r}: {d[:3]}")
    print(f"  detectado  {nombre}  ({len(d)} diferencias)")


debe_detectar("TAU_DEFAULT 1,19 → 1,2 (el ejemplo del plan)",
              _con("nowcast_puertas.py", [(r"(?m)^TAU_DEFAULT\s*=\s*1\.19\b", "TAU_DEFAULT = 1.2")]),
              "nowcast_puertas.py::TAU_DEFAULT", "nowcast_puertas.py::ENV:TAU")
debe_detectar("EPSILON0_DEFAULT 0,035 → 0,04",
              _con("nowcast_puertas.py", [(r"(?m)^EPSILON0_DEFAULT\s*=\s*0\.035\b", "EPSILON0_DEFAULT = 0.04")]),
              "nowcast_puertas.py::EPSILON0_DEFAULT", "nowcast_puertas.py::ENV:EPSILON0")
debe_detectar("bandera invertida: GUARD_ERA `!= \"0\"` → `== \"0\"`",
              _con("nowcast_puertas.py", [(r'(os\.environ\.get\("GUARD_ERA", "1"\)) != "0"', r'\1 == "0"')]),
              "nowcast_puertas.py::ENV:GUARD_ERA")
debe_detectar("constante borrada: DESVIO_MIN_INDIVIDUAL (el piso 0,02)",
              _con("ensemble.py", [(r"(?m)^DESVIO_MIN_INDIVIDUAL\s*=\s*0\.02\s*$", "")]),
              "SE FUE", "DESVIO_MIN_INDIVIDUAL")
debe_detectar("constante nueva", _con("ensemble.py", agregar="\nPARAMETRO_NUEVO = 3\n"),
              "NUEVO", "PARAMETRO_NUEVO")
debe_detectar("default numérico de función: nowcast(n_sims) 2000 → 1999",
              _con("nowcast_puertas.py", [(r"n_sims: int = 2000", "n_sims: int = 1999")]),
              "nowcast(n_sims)")
debe_detectar("lectura de entorno nueva",
              _con("beta_dictamen.py", agregar='\nOTRA = os.environ.get("BANDERA_NUEVA", "0") != "0"\n'),
              "NUEVO", "ENV:BANDERA_NUEVA")
debe_detectar("archivo de datos nuevo referenciado",
              _con("ensemble.py", agregar='\n_NUEVO = "sin_carpeta/nuevo.parquet"\n'),
              "ARCHIVO DERIVADO NUEVO", "nuevo.parquet")

# Los coeficientes estimados: el sha256 cambia si cambia el archivo (con el mismo contenido y otros saltos de línea, no).
clave = next(iter(guardado["estimados_fijados"]))
mod = copy.deepcopy(actual)
mod["estimados_fijados"][clave]["sha256"] = "0" * 64
d = R.diferencias(guardado, mod)
check(any("COEFICIENTES ESTIMADOS" in x for x in d), "cambiar el contenido de un JSON estimado no se detecta")
print(f"  detectado  coeficiente estimado modificado  ({len(d)} diferencia)")
with tempfile.TemporaryDirectory() as tmp:
    a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
    a.write_bytes(b'{"x": 1,\n "y": 2}\n')
    b.write_bytes(b'{"x": 1,\r\n "y": 2}\r\n')
    check(R._sha256_texto(a) == R._sha256_texto(b), "el sha256 tiene que ignorar CRLF contra LF (Windows contra el CI)")

# Lo que NO es un parámetro no puede romper el test.
rel_np = next(r for r in fuentes if r.endswith("nowcast_puertas.py"))
corrida = dict(fuentes)
corrida[rel_np] = "# un comentario nuevo\n\n\n" + fuentes[rel_np].replace(
    "TAU_DEFAULT = 1.19", "TAU_DEFAULT = 1.19  # mismo valor, otro comentario")
check(not detecta(corrida), "un comentario y líneas corridas NO son un cambio de parámetro y el test se rompió igual")
print("  no se rompe  un comentario, una línea en blanco y líneas corridas")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
