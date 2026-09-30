# -*- coding: utf-8 -*-
"""El registro de parámetros del motor, GENERADO DESDE EL CÓDIGO.

Auditoría 2026-09, ítem B1 (pasos 1 del anclaje, `coordinacion/AUDITORIA-2026-09/05-consolidacion-y-anclaje.md`
§5.3; reglas 1 y 8 de `REGLAS-borrador.md`). Reemplaza a las tablas «Constantes del motor» y «Parámetros
estimados» de `coordinacion/FORMULA-COMPLETA.md`, que se escribían a mano y se desactualizaban.

QUÉ ES UN PARÁMETRO (la definición operativa del §5.3), dentro de la CLAUSURA de archivos locales que se
alcanzan por `import` desde `nowcast_puertas.py` (incluidos los imports dentro de funciones; sin tests):
    entorno          toda lectura de variable de entorno (`os.environ.get`, `os.environ[...]`, `os.getenv`,
                     `rutas._env`), con su default EFECTIVO: la expresión evaluada con el entorno vacío.
    constante        asignación de módulo con nombre en MAYÚSCULAS y valor literal.
    default_funcion  default numérico de un argumento de función.
    archivo_derivado referencia literal a un archivo de datos (.parquet .csv .json .db .xlsx) o nombre que el
                     código toma de `rutas`. Para los coeficientes estimados (β y θ) se fija además el sha256.

QUÉ NO ESTÁ (declarado): los números dentro del cuerpo de las funciones (constantes «mágicas» sin nombre) y los
parámetros de los GENERADORES de los archivos derivados (p. ej. `MIN_VOTOS` de `disciplina.py`): de ésos queda
el sha256 del archivo estimado, no el parámetro. Tampoco se registra cuáles MUEVEN el número: eso lo mide
`perturbar_panel.py` (etapa 2 de B1) y lo guarda en `afecta_panel`.

PARA QUÉ SIRVE. `tests/test_defaults_fijados.py` compara este registro contra el código: cambiar un default,
invertir una bandera, agregar o sacar un parámetro o un archivo derivado lo pone en rojo. Un cambio a propósito
(una re-estimación de la fase D) se regenera con

    python modelo/ensemble/src/registro_parametros.py --escribir

y el diff de `modelo/ensemble/outputs/registro_parametros.json` es la evidencia de qué se movió. Regla 8: ese
commit cita la medición que lo justifica. Este módulo LEE el código; no agrega términos ni banderas al motor.

    python modelo/ensemble/src/registro_parametros.py             # resumen
    python modelo/ensemble/src/registro_parametros.py --verificar # exit 1 si el código difiere del guardado
    python modelo/ensemble/src/registro_parametros.py --escribir  # regenera y guarda (conserva `afecta_panel`)
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / "nowcast_puertas.py"
REGISTRO = AQUI.parent / "outputs" / "registro_parametros.json"
OUTPUTS = AQUI.parent / "outputs"
COMANDO = "python modelo/ensemble/src/registro_parametros.py --escribir"

FORMATO = 1
# Carpetas que no son código del motor: tests, datos descartables, lo archivado por la poda (A7).
EXCLUIDAS = {"Archivos_Borrar", "__pycache__", ".git", ".mapa", "archivo", "tests", "node_modules"}
# Los coeficientes ESTIMADOS (β del dictamen y θ de sobre tablas): de ellos se fija el contenido.
ESTIMADOS = ("beta_dictamen.json", "theta_sobre_tablas.json")
# Metadatos de `test_rutas.py`, no parámetros del modelo: listar un archivo nuevo en ellos no mueve nada.
NO_PARAMETROS = {("rutas.py", "GENERADOS"), ("rutas.py", "SOLO_EN_RAIZ_GIT")}
# Lo que cada parámetro fija en el test. La línea NO (cambia con cualquier edición) ni `afecta_panel` (medición).
FIJADOS = ("clase", "entorno", "default", "evaluable", "expresion")
# Los nombres que se importan de `rutas` pero no son un archivo de datos.
RUTAS_NO_DATO = {"RAIZ", "RAIZ_GIT"}
# `rutas.py` DECLARA todas las rutas del repo (28 archivos de datos que el motor no lee): lo que el motor
# usa de él se ve en los nombres que los demás archivos le importan, no en sus literales.
SIN_LITERALES_DE_ARCHIVO = {"rutas.py"}

_NOMBRE_CONSTANTE = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
_ARCHIVO_DATO = re.compile(r"\.(parquet|csv|json|db|xlsx)$", re.IGNORECASE)
_MAX_TEXTO = 120


# ════════════════════════════════════════════════════════ la clausura de imports
def _indice_modulos(raiz: Path) -> dict[str, list[Path]]:
    """nombre de módulo (el stem del archivo) -> archivos .py del repo que lo pueden ser."""
    idx: dict[str, list[Path]] = {}
    for p in sorted(raiz.rglob("*.py")):
        rel = p.relative_to(raiz)
        if any(parte in EXCLUIDAS for parte in rel.parts[:-1]):
            continue
        idx.setdefault(p.stem, []).append(p)
    return idx


def _nombres_importados(arbol: ast.AST) -> set[str]:
    """Los nombres que un archivo importa, en cualquier parte (también dentro de funciones)."""
    out: set[str] = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                out.add(n.module.split(".")[-1])
            for a in n.names:
                out.add(a.name)
    return out


def clausura(raiz: Path = RAIZ, entrada: Path = ENTRADA) -> list[str]:
    """Rutas (relativas a `raiz`, con `/`) de los archivos alcanzables desde `entrada`, ordenadas.

    Es una SOBREAPROXIMACIÓN: incluye lo que sólo se importa con una bandera prendida (β trae al
    estimador y éste al harness). Por eso existe `afecta_panel`."""
    idx = _indice_modulos(raiz)
    visto = {entrada.resolve()}
    cola = [entrada.resolve()]
    while cola:
        p = cola.pop()
        arbol = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for nombre in _nombres_importados(arbol):
            for cand in idx.get(nombre, []):
                cand = cand.resolve()
                if cand not in visto:
                    visto.add(cand)
                    cola.append(cand)
    return sorted(p.relative_to(raiz.resolve()).as_posix() for p in visto)


def cargar_fuentes(raiz: Path = RAIZ, archivos: list[str] | None = None) -> dict[str, str]:
    """{ruta relativa: texto} de la clausura. Sobre este diccionario trabaja `extraer`, de modo que el test
    pueda modificar un texto en memoria (los sabotajes) sin tocar el disco."""
    archivos = archivos if archivos is not None else clausura(raiz)
    return {rel: (raiz / rel).read_text(encoding="utf-8") for rel in archivos}


# ═══════════════════════════════════════════════════════════ valores y evaluación
class _OSVacio:
    """`os` con el entorno vacío: así se evalúa el default EFECTIVO de una lectura de entorno."""
    environ: dict = {}

    @staticmethod
    def getenv(clave, defecto=None):
        return defecto


def _jsonable(v):
    """(ok, valor) con el valor llevado a tipos de JSON: tuplas y listas -> lista, conjuntos -> lista ordenada."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return True, v
    if isinstance(v, (list, tuple)):
        res = [_jsonable(x) for x in v]
        return all(ok for ok, _ in res), [x for _, x in res]
    if isinstance(v, (set, frozenset)):
        res = [_jsonable(x) for x in v]
        if not all(ok for ok, _ in res):
            return False, None
        return True, sorted((x for _, x in res), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(v, dict):
        res = {str(k): _jsonable(x) for k, x in v.items()}
        return all(ok for ok, _ in res.values()), {k: x for k, (_, x) in res.items()}
    return False, None


def _evaluar(nodo: ast.AST, nombres: dict):
    """(evaluable, valor_jsonable) de una expresión con el entorno vacío y los literales del módulo a mano."""
    try:
        expr = ast.fix_missing_locations(ast.Expression(body=nodo))
        v = eval(compile(expr, "<registro>", "eval"),  # noqa: S307 — sólo literales y os vacío
                 {"__builtins__": {}, "os": _OSVacio, "float": float, "int": int, "str": str,
                  "bool": bool}, dict(nombres))
    except Exception:  # noqa: BLE001 — cualquier cosa no evaluable a mano queda como «sólo el texto»
        return False, None
    return _jsonable(v)


def _texto(fuente: str, nodo: ast.AST) -> str:
    """El código fuente del nodo con los espacios colapsados (no depende de la versión de Python)."""
    return " ".join((ast.get_source_segment(fuente, nodo) or "").split())


def _padres(arbol: ast.AST) -> dict:
    return {hijo: padre for padre in ast.walk(arbol) for hijo in ast.iter_child_nodes(padre)}


def _es_os_environ(n) -> bool:
    return (isinstance(n, ast.Attribute) and n.attr == "environ"
            and isinstance(n.value, ast.Name) and n.value.id == "os")


def _lectura_entorno(n):
    """(variable, nodo_default | None) si `n` lee una variable de entorno con nombre literal; si no, None."""
    if isinstance(n, ast.Subscript) and _es_os_environ(n.value):
        clave = n.slice
        return (clave.value, None) if isinstance(clave, ast.Constant) and isinstance(clave.value, str) else None
    if not isinstance(n, ast.Call) or not n.args:
        return None
    f = n.func
    es_get = isinstance(f, ast.Attribute) and (
        (f.attr == "get" and _es_os_environ(f.value))
        or (f.attr == "getenv" and isinstance(f.value, ast.Name) and f.value.id == "os"))
    es_helper = isinstance(f, ast.Name) and f.id == "_env"      # rutas._env(var, default)
    if not (es_get or es_helper):
        return None
    clave = n.args[0]
    if not (isinstance(clave, ast.Constant) and isinstance(clave.value, str)):
        return None
    defecto = n.args[1] if len(n.args) > 1 else next(
        (k.value for k in n.keywords if k.arg in ("default", "defecto")), None)
    return clave.value, defecto


def _nombres_literales(arbol: ast.Module) -> dict:
    """Los literales que el módulo asigna a un nombre (para evaluar `float(os.environ.get('TAU', TAU_DEFAULT))`)."""
    out: dict = {}
    for s in arbol.body:
        if isinstance(s, (ast.Assign, ast.AnnAssign)) and s.value is not None:
            objetivos = s.targets if isinstance(s, ast.Assign) else [s.target]
            try:
                v = ast.literal_eval(s.value)
            except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
                continue
            for t in objetivos:
                if isinstance(t, ast.Name):
                    out[t.id] = v
    return out


def _es_ruta_de_dato(texto: str) -> bool:
    return bool(_ARCHIVO_DATO.search(texto)) and "\n" not in texto and len(texto) <= 300


def _textos_de(v):
    """Todos los str que hay adentro de un literal."""
    if isinstance(v, str):
        yield v
    elif isinstance(v, (list, tuple, set, frozenset)):
        for x in v:
            yield from _textos_de(x)
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from _textos_de(k)
            yield from _textos_de(x)


# ════════════════════════════════════════════════════════════════ la extracción
def extraer(fuentes: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """(parámetros, archivos_derivados) de los textos de `fuentes` ({ruta relativa: código}). Determinista."""
    parametros: list[dict] = []
    derivados: list[dict] = []
    for rel in sorted(fuentes):
        fuente = fuentes[rel]
        arbol = ast.parse(fuente, filename=rel)
        padres = _padres(arbol)
        literales = _nombres_literales(arbol)
        en_archivo: list[dict] = []

        # ── entorno: toda lectura de variable de entorno con nombre literal
        for n in sorted((x for x in ast.walk(arbol) if _lectura_entorno(x)),
                        key=lambda x: (x.lineno, x.col_offset)):
            var, nodo_defecto = _lectura_entorno(n)
            estado = n
            while estado in padres and not isinstance(estado, ast.stmt):
                estado = padres[estado]
            asignado = None
            if (isinstance(estado, (ast.Assign, ast.AnnAssign)) and isinstance(padres.get(estado), ast.Module)
                    and estado.value is not None):
                objetivos = estado.targets if isinstance(estado, ast.Assign) else [estado.target]
                if len(objetivos) == 1 and isinstance(objetivos[0], ast.Name):
                    asignado = objetivos[0].id
            if asignado is not None:
                nodo_eval, expresion = estado.value, _texto(fuente, estado.value)
            else:
                nodo_eval = nodo_defecto if nodo_defecto is not None else ast.Constant(value=None)
                expresion = _texto(fuente, n)
            evaluable, valor = _evaluar(nodo_eval, literales)
            en_archivo.append({
                "id": f"{rel}::ENV:{var}", "clase": "entorno", "archivo": rel, "nombre": asignado or var,
                "linea": n.lineno, "entorno": var, "asignado_a": asignado,
                "default": valor if evaluable else None, "evaluable": evaluable, "expresion": expresion})

        # ── constante: asignación de módulo, nombre en MAYÚSCULAS, valor literal
        for s in arbol.body:
            if not (isinstance(s, (ast.Assign, ast.AnnAssign)) and s.value is not None):
                continue
            objetivos = s.targets if isinstance(s, ast.Assign) else [s.target]
            for t in objetivos:
                if not (isinstance(t, ast.Name) and _NOMBRE_CONSTANTE.match(t.id)):
                    continue
                if (rel, t.id) in NO_PARAMETROS or any(_lectura_entorno(x) for x in ast.walk(s.value)):
                    continue
                try:
                    v = ast.literal_eval(s.value)
                except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
                    continue
                if v is None or any(_es_ruta_de_dato(x) for x in _textos_de(v)):
                    continue                     # los archivos de datos van a `archivo_derivado`
                if isinstance(v, str) and len(v) > _MAX_TEXTO:
                    continue                     # prosa (un prompt, un motivo), no un parámetro
                ok, valor = _jsonable(v)
                if not ok:
                    continue
                en_archivo.append({
                    "id": f"{rel}::{t.id}", "clase": "constante", "archivo": rel, "nombre": t.id,
                    "linea": s.lineno, "entorno": None, "asignado_a": t.id, "default": valor,
                    "evaluable": True, "expresion": _texto(fuente, s.value)})

        # ── default_funcion: default numérico de un argumento
        def recorrer(nodo, pila):
            for hijo in ast.iter_child_nodes(nodo):
                if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    calificado = ".".join(pila + [hijo.name])
                    a = hijo.args
                    posicionales = a.posonlyargs + a.args
                    pares = list(zip(posicionales[len(posicionales) - len(a.defaults):], a.defaults))
                    pares += [(k, d) for k, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
                    for arg, d in pares:
                        try:
                            v = ast.literal_eval(d)
                        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
                            continue
                        if isinstance(v, bool) or not isinstance(v, (int, float)):
                            continue
                        en_archivo.append({
                            "id": f"{rel}::{calificado}({arg.arg})", "clase": "default_funcion", "archivo": rel,
                            "nombre": arg.arg, "linea": hijo.lineno, "entorno": None, "asignado_a": None,
                            "default": v, "evaluable": True, "expresion": _texto(fuente, d)})
                    recorrer(hijo, pila + [hijo.name])
                elif isinstance(hijo, ast.ClassDef):
                    recorrer(hijo, pila + [hijo.name])
                else:
                    recorrer(hijo, pila)
        recorrer(arbol, [])

        # ids únicos dentro del archivo (dos lecturas de la misma variable, dos funciones homónimas)
        vistos: dict[str, int] = {}
        for p in sorted(en_archivo, key=lambda x: (x["linea"], x["id"])):
            vistos[p["id"]] = vistos.get(p["id"], 0) + 1
            if vistos[p["id"]] > 1:
                p["id"] = f"{p['id']}#{vistos[p['id']]}"
            parametros.append(p)

        # ── archivo_derivado: referencias literales a archivos de datos y nombres tomados de `rutas`
        alias_rutas = {"rutas"}
        for n in ast.walk(arbol):
            if isinstance(n, ast.Import):
                alias_rutas |= {a.asname for a in n.names if a.name == "rutas" and a.asname}
        refs: dict[tuple[str, str], int] = {}
        for n in ast.walk(arbol):
            ref = None
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                if isinstance(padres.get(n), (ast.JoinedStr, ast.Expr)):
                    continue                      # una pieza de un f-string, o un docstring
                if _es_ruta_de_dato(n.value) and rel not in SIN_LITERALES_DE_ARCHIVO:
                    ref = ("literal", n.value)
            elif isinstance(n, ast.JoinedStr):
                piezas = "".join(p.value if isinstance(p, ast.Constant) else "{}" for p in n.values)
                if _es_ruta_de_dato(piezas) and rel not in SIN_LITERALES_DE_ARCHIVO:
                    ref = ("literal", piezas)
            elif isinstance(n, ast.ImportFrom) and n.module == "rutas":
                for a in n.names:
                    if a.name not in RUTAS_NO_DATO:
                        refs.setdefault(("rutas", f"rutas.{a.name}"), n.lineno)
            elif (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in alias_rutas
                  and _NOMBRE_CONSTANTE.match(n.attr) and n.attr not in RUTAS_NO_DATO):
                ref = ("rutas", f"rutas.{n.attr}")
            if ref is not None:
                refs.setdefault(ref, n.lineno)
        for (tipo, texto), linea in sorted(refs.items()):
            derivados.append({"archivo": rel, "ref": texto, "tipo": tipo, "linea": linea})

    return parametros, derivados


# ═════════════════════════════════════════════════════════════ el registro completo
def _sha256_texto(ruta: Path) -> str:
    """sha256 del contenido con los saltos de línea normalizados (el repo tiene `text=auto`)."""
    return hashlib.sha256(ruta.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha_fuentes(fuentes: dict[str, str]) -> dict[str, str]:
    """sha256 del texto de cada archivo (saltos de línea normalizados): con qué código se hizo una medición."""
    return {rel: hashlib.sha256(x.replace("\r\n", "\n").encode("utf-8")).hexdigest()
            for rel, x in fuentes.items()}


def _estimados(raiz: Path) -> dict:
    out = {}
    for nombre in ESTIMADOS:
        ruta = OUTPUTS / nombre
        rel = ruta.resolve().relative_to(raiz.resolve()).as_posix()
        out[rel] = {"sha256": _sha256_texto(ruta) if ruta.is_file() else None}
    return out


def _nombres_con_varios_defaults(parametros: list[dict]) -> list[dict]:
    """La trampa de la regla 8: el MISMO nombre (sin distinguir mayúsculas) con defaults distintos."""
    por_nombre: dict[str, list[dict]] = {}
    for p in parametros:
        if p["evaluable"] and p["default"] is not None:
            clave = (p["asignado_a"] or p["nombre"]).lower()
            por_nombre.setdefault(clave, []).append(p)
    out = []
    for nombre, ps in sorted(por_nombre.items()):
        distintos = {json.dumps(p["default"], sort_keys=True) for p in ps}
        if len(distintos) > 1:
            out.append({"nombre": nombre,
                        "valores": [{"id": p["id"], "default": p["default"]} for p in ps]})
    return out


def generar(raiz: Path = RAIZ, fuentes: dict[str, str] | None = None, previo: dict | None = None) -> dict:
    """El registro completo, desde el código. `previo` (el guardado) aporta lo que NO sale del código:
    la medición `afecta_panel`, que se conserva por id."""
    fuentes = fuentes if fuentes is not None else cargar_fuentes(raiz)
    parametros, derivados = extraer(fuentes)
    medido = {p["id"]: p.get("afecta_panel") for p in (previo or {}).get("parametros", [])}
    for p in parametros:
        p["afecta_panel"] = medido.get(p["id"])
    registro = {
        "formato": FORMATO,
        "generado_por": COMANDO,
        "entrada": ENTRADA.relative_to(raiz).as_posix(),
        "que_es_un_parametro": (
            "Toda variable de entorno, constante numérica o archivo derivado que lee el camino de nowcast() "
            "(05-consolidacion-y-anclaje.md §5.3). Clases: entorno, constante, default_funcion, archivo_derivado. "
            "El test fija (clase, entorno, default, evaluable, expresion); la línea y afecta_panel no."),
        "limites": [
            "No incluye los números dentro del cuerpo de las funciones (constantes sin nombre).",
            "No incluye los parámetros de los generadores de los archivos derivados; de los coeficientes "
            "estimados (β, θ) se fija el sha256 del archivo.",
            "La clausura es una sobreaproximación (incluye lo que sólo se importa con una bandera prendida): "
            "`afecta_panel` dice cuáles mueven el número.",
        ],
        "medicion_afecta_panel": (previo or {}).get("medicion_afecta_panel"),
        "clausura": sorted(fuentes),
        "parametros": parametros,
        "archivos_derivados": derivados,
        "estimados_fijados": _estimados(raiz),
        "nombres_con_varios_defaults": _nombres_con_varios_defaults(parametros),
    }
    return registro


def a_texto(registro: dict) -> str:
    """El JSON como se guarda: sangría fija, sin ASCII forzado, LF, un salto final."""
    return json.dumps(registro, ensure_ascii=False, indent=1) + "\n"


def leer_guardado(ruta: Path = REGISTRO) -> dict | None:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def escribir(registro: dict, ruta: Path = REGISTRO) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(a_texto(registro).encode("utf-8"))        # bytes: nada convierte los LF en CRLF


# ════════════════════════════════════════════════════════════ la comparación
def _fijado(p: dict) -> dict:
    return {k: p.get(k) for k in FIJADOS}


def diferencias(guardado: dict, actual: dict) -> list[str]:
    """Lo que el código dice y el registro guardado no, en frases que se entienden sin abrir nada. Vacío = igual."""
    dif: list[str] = []
    g = {p["id"]: p for p in guardado["parametros"]}
    a = {p["id"]: p for p in actual["parametros"]}
    for i in sorted(set(g) | set(a)):
        if i not in a:
            dif.append(f"SE FUE {i}: el registro lo tenía (default {g[i]['default']!r}) y el código ya no lo tiene")
        elif i not in g:
            dif.append(f"NUEVO {i}: el código lo tiene (default {a[i]['default']!r}, `{a[i]['expresion']}`) "
                       "y el registro no")
        elif _fijado(g[i]) != _fijado(a[i]):
            campos = [k for k in FIJADOS if g[i].get(k) != a[i].get(k)]
            detalle = "; ".join(f"{k}: registro {g[i].get(k)!r} -> código {a[i].get(k)!r}" for k in campos)
            dif.append(f"CAMBIÓ {i}: {detalle}")
    cg = {(d["archivo"], d["ref"]) for d in guardado["archivos_derivados"]}
    ca = {(d["archivo"], d["ref"]) for d in actual["archivos_derivados"]}
    for archivo, ref in sorted(ca - cg):
        dif.append(f"ARCHIVO DERIVADO NUEVO {ref} en {archivo}: el motor lee un archivo que el registro no conoce")
    for archivo, ref in sorted(cg - ca):
        dif.append(f"ARCHIVO DERIVADO QUE SE FUE {ref} en {archivo}")
    for ruta in sorted(set(guardado["estimados_fijados"]) | set(actual["estimados_fijados"])):
        x = guardado["estimados_fijados"].get(ruta, {}).get("sha256")
        y = actual["estimados_fijados"].get(ruta, {}).get("sha256")
        if x != y:
            dif.append(f"COEFICIENTES ESTIMADOS {ruta}: el contenido cambió (sha256 {str(x)[:12]} -> {str(y)[:12]}): "
                       "un parámetro estimado se movió sin pasar por el registro")
    if guardado["clausura"] != actual["clausura"]:
        nuevos = sorted(set(actual["clausura"]) - set(guardado["clausura"]))
        idos = sorted(set(guardado["clausura"]) - set(actual["clausura"]))
        dif.append(f"CLAUSURA: el camino de nowcast() cambió (archivos nuevos {nuevos}, que se fueron {idos})")
    return dif


# ════════════════════════════════════════════════════════════════════════ CLI
def resumen(registro: dict) -> str:
    por_clase: dict[str, int] = {}
    for p in registro["parametros"]:
        por_clase[p["clase"]] = por_clase.get(p["clase"], 0) + 1
    l = [f"clausura: {len(registro['clausura'])} archivos",
         "parámetros: " + ", ".join(f"{n} {c}" for c, n in sorted(por_clase.items()))
         + f" (total {len(registro['parametros'])})",
         f"archivos derivados referenciados: {len(registro['archivos_derivados'])}",
         f"coeficientes estimados con sha256: {sum(1 for v in registro['estimados_fijados'].values() if v['sha256'])}",
         f"nombres con varios defaults: {len(registro['nombres_con_varios_defaults'])}"]
    return "\n".join(l)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--escribir", action="store_true", help="regenera el registro y lo guarda")
    g.add_argument("--verificar", action="store_true", help="exit 1 si el código difiere del guardado")
    args = ap.parse_args(argv)
    guardado = leer_guardado()
    actual = generar(previo=guardado)
    if args.escribir:
        escribir(actual)
        print(f"escrito {REGISTRO.relative_to(RAIZ).as_posix()}\n{resumen(actual)}")
        if guardado:
            dif = diferencias(guardado, actual)
            print(f"\nlo que cambió respecto del guardado ({len(dif)}):")
            for d in dif:
                print("  -", d)
        return 0
    if args.verificar:
        if guardado is None:
            print(f"falta {REGISTRO}: {COMANDO}")
            return 1
        dif = diferencias(guardado, actual)
        for d in dif:
            print("  -", d)
        print("registro al día" if not dif else f"{len(dif)} diferencias: si es a propósito, {COMANDO}")
        return 1 if dif else 0
    print(resumen(actual))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
