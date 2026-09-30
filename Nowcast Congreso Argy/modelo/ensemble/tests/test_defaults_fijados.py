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

LA MEDICIÓN `afecta_panel` (sección 5). Qué parámetros MUEVEN el número lo mide `perturbar_panel.py` con el motor
real (≈ 1 hora, por eso no corre acá): se guarda en el mismo registro. Este test sólo comprueba que la medición
existe, que sus controles positivos dieron bien y que ningún parámetro quedó sin medir; y AVISA (no rompe) si los
archivos del camino cambiaron desde que se midió.

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

# ── 5. la medición `afecta_panel` (etapa 2 de B1) ────────────────────────────────────────────────
print("\n5. la medición `afecta_panel`: está, sus controles dieron bien y se dice si quedó vieja")
med = guardado.get("medicion_afecta_panel")
check(med is not None, "falta `medicion_afecta_panel`: python modelo/ensemble/src/perturbar_panel.py --medir")
if med:
    check(med["controles"] and all(c["ok"] for c in med["controles"]),
          f"algún control positivo de la medición dio al revés: {[c for c in med['controles'] if not c['ok']]}")
    sin = [p["id"] for p in guardado["parametros"] if not isinstance(p.get("afecta_panel"), dict)]
    check(not sin, f"parámetros sin `afecta_panel` (se agregaron sin medir; corré perturbar_panel.py --medir): {sin[:5]}")
    sin_motivo = [p["id"] for p in guardado["parametros"]
                  if isinstance(p.get("afecta_panel"), dict) and p["afecta_panel"]["afecta"] is None
                  and not p["afecta_panel"].get("motivo") and not p["afecta_panel"].get("errores")]
    check(not sin_motivo, f"`afecta = null` tiene que traer el motivo: {sin_motivo[:5]}")
    # ¿Cambió el código desde la medición? Informativo (no rompe): un default cambiado rompe la sección 2; esto avisa
    # que los módulos que la medición midió ya no son los de hoy y conviene repetirla antes de citar `afecta_panel`.
    hoy = R.sha_fuentes(fuentes)
    cambiados = sorted(r for r, h in med["fuentes_sha256"].items() if hoy.get(r) != h)
    res = med["resumen"]
    print(f"  medido el {med['fecha']} sobre {med['git_head'][:7] if med.get('git_head') else '?'} · "
          f"{res['afecta']} afectan, {res['no_afecta']} no, {res['sin_medir']} sin medir · "
          f"{len(med['controles'])} controles positivos OK")
    if cambiados:
        print(f"  AVISO (no rompe): {len(cambiados)} archivos del camino cambiaron desde la medición: "
              f"{[Path(c).name for c in cambiados][:6]}; repetir `perturbar_panel.py --medir` antes de citar `afecta_panel`.")

# ── 6. la maquinaria de la medición (sin correr el motor) ─────────────────────────────────────────
print("\n6. la maquinaria de `perturbar_panel.py`: alternativas, umbral y reescritura del AST")
import perturbar_panel as PP  # noqa: E402

check(PP.alternativas(True) == [False] and PP.alternativas(False) == [True], "la alternativa de un booleano es el opuesto")
check(PP.alternativas(20) == [40, 10] and PP.alternativas(1) == [2, 0] and PP.alternativas(0) == [1],
      f"enteros: {PP.alternativas(20)}, {PP.alternativas(1)}, {PP.alternativas(0)}")
check(PP.alternativas(1.19) == [2.38, 0.595], f"un real: {PP.alternativas(1.19)}")
check(PP.alternativas(0.6) == [1.0, 0.3], f"una probabilidad acota el doble a 1: {PP.alternativas(0.6)}")
check(PP.alternativas(1.0) == [0.5] and PP.alternativas(0.0) == [0.1], "x = 1 descarta el doble; x = 0 prueba 0,1")
check(PP.alternativas("texto") == [] and PP.alternativas(None) == [], "un texto o None no se perturba")
base = {"/p": 0.5, "/n": 3, "/texto": "a", "/x[0]": 1.0}
check(not PP.comparar(base, dict(base))["afecta"], "salida idéntica: no afecta")
check(not PP.comparar(base, {**base, "/p": 0.5 + 5e-10})["afecta"], "una diferencia bajo el umbral (1e-9) no cuenta")
check(PP.comparar(base, {**base, "/p": 0.5 + 2e-9})["afecta"], "una diferencia sobre el umbral cuenta")
check(PP.comparar(base, {**base, "/texto": "b"})["afecta"], "cambiar un texto cuenta")
check(PP.comparar(base, {k: v for k, v in base.items() if k != "/n"})["afecta"], "perder un campo cuenta")
fuente = "X = 1\nY = 2.5\n\ndef f(a, b=2, *, c=3.0):\n    return a, b, c\n"
for clase, nombre, linea, alt, leer in [("constante", "X", 1, 5, lambda m: m["X"]),
                                        ("default_funcion", "b", 4, 9, lambda m: m["f"](0)[1]),
                                        ("default_funcion", "c", 4, 7.5, lambda m: m["f"](0)[2])]:
    espacio: dict = {}
    exec(compile(PP._reescritor({"clase": clase, "nombre": nombre, "linea": linea, "id": nombre}, alt)(fuente),
                 "<prueba>", "exec"), espacio)
    check(leer(espacio) == alt, f"la reescritura de {clase} {nombre} no dejó {alt}: {leer(espacio)}")
    check(espacio["Y"] == 2.5, f"la reescritura de {nombre} tocó otra cosa")
try:
    PP._reescritor({"clase": "constante", "nombre": "NO_ESTA", "linea": 99, "id": "x"}, 1)(fuente)
    check(False, "reescribir un literal que no existe tiene que fallar fuerte, no pasar en silencio")
except RuntimeError:
    check(True, "")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
