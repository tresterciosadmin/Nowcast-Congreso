"""FORK del indexar.py de la skill `mapa-de-proyectos`, para este repo.

QUE CAMBIA respecto del original (7 parches, todos marcados `FORK NOWCAST`):
  1. Lee el `Resumen:` y el `## Buscar aca si` del **README.md** del modulo
     cuando no hay BITACORA.md. En este repo cada modulo ya tiene un README con
     su contrato; pedir un BITACORA.md al lado seria una SEXTA capa de
     documentacion en un proyecto cuya patologia numero uno es que las bitacoras
     se contradicen entre si. Una sola fuente por modulo.
  2. Estado nuevo `heredada`: `variables/embudo/src/` no necesita bitacora
     propia, la describe el README de `variables/embudo/`. Sin esto el
     diagnostico reclama 40 carpetas que no hacen falta.
  3. `--sellar` estampa la huella en el README.md si no hay BITACORA.md.
  4. `co_cambios` devuelve `Counter()` (no `{}`) cuando no hay git: el original
     revienta con AttributeError en un repo sin historial.

POR QUE ESTA VENDORIZADO ACA y no se usa el de la skill: para que quien clone el
repo pueda reindexar sin tener la skill instalada, y para que el hook de
pre-commit no dependa de una ruta de fuera del repo.

Si la skill upstream cambia, re-aplicar estos parches; estan todos marcados.
"""
import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

IGNORAR_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "target", ".next", ".nuxt", ".cache", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "site-packages", ".idea", ".vscode", "vendor",
    "coverage", ".tox", "htmlcov", ".terraform", ".mapa",
    # FORK NOWCAST: dos carpetas de este repo que no son codigo del proyecto.
    #  - Archivos_Borrar/ (y datos/Archivos_Borrar/): por definicion NADA ahi es
    #    fuente de verdad (CLAUDE.md). Indexarlo meteria en el mapa scripts
    #    neutralizados y ~270 MB de HTML cacheado del Senado.
    #  - "Aportes sobre dataset congreso": material de terceros (Andy Tow /
    #    legislAr / towlandia). Se usa como semilla de un solo uso (ADR-0002),
    #    no se mantiene, y son ~800 HTML que tapan el mapa.
    "Archivos_Borrar", "Aportes sobre dataset congreso",
}
IGNORAR_ARCHIVOS = {"*.pyc", "*.pyo", "*.so", "*.dylib", "*.dll", "*.class", "*.o",
                    "*.a", "*.zip", "*.tar.gz", "*.png", "*.jpg", "*.jpeg", "*.gif",
                    "*.pdf", "*.xlsx", "*.xls", "*.db", "*.sqlite", "*.sqlite3",
                    "*.parquet", "*.lock", "*.min.js", "*.map"}
LENGUAJES = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".go": "go", ".rs": "rust", ".java": "java",
    ".kt": "kotlin", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".swift": "swift", ".r": "r",
    ".R": "r", ".jl": "julia", ".sh": "bash", ".bash": "bash", ".ps1": "powershell",
    ".sql": "sql", ".html": "html", ".css": "css", ".scss": "scss", ".yml": "yaml",
    ".yaml": "yaml", ".toml": "toml", ".json": "json", ".md": "markdown",
    ".ipynb": "notebook", ".tf": "terraform",
}
CODIGO = {"python", "javascript", "typescript", "go", "rust", "java", "kotlin",
          "c", "cpp", "ruby", "php", "csharp", "swift", "r", "julia", "bash", "sql"}
STDLIB = {
    "os", "sys", "re", "json", "time", "datetime", "pathlib", "typing", "math",
    "logging", "collections", "itertools", "functools", "subprocess", "argparse",
    "random", "csv", "io", "shutil", "glob", "traceback", "warnings", "copy",
    "hashlib", "base64", "uuid", "tempfile", "textwrap", "dataclasses", "enum",
    "abc", "asyncio", "threading", "unittest", "string", "pickle", "urllib",
    "http", "socket", "struct", "zlib", "gzip", "decimal", "statistics", "sqlite3",
}
HOSTS_RUIDO = {
    "github.com", "raw.githubusercontent.com", "w3.org", "schemas.xmlsoap.org",
    "localhost", "127.0.0.1", "example.com", "python.org", "docs.python.org",
    "pypi.org", "npmjs.com", "stackoverflow.com", "json-schema.org",
    "opensource.org", "creativecommons.org", "fonts.googleapis.com",
    "cdn.jsdelivr.net", "unpkg.com",
}
MAX_BYTES = 1_500_000
GRANDE = 500          # LOC a partir de las cuales un archivo se marca
MAX_LINEAS_MAPA = 460  # presupuesto de contexto del MAPA.md
# 2026-09-08: sube de 260 a 460 por decision explicita de Franco al agregar el
# inventario de datos. El argumento no es que el presupuesto no importe, es que
# importa MENOS que repetir tareas: dos sesiones seguidas reconstruyeron tablas
# que ya existian porque los datos no estaban indexados en ningun lado. 200
# lineas de indice cuestan una vez; buscar a mano cuesta cada vez.

RE_URL = re.compile(r"""https?://([A-Za-z0-9._~-]+\.[A-Za-z]{2,})(/[^\s'"`)\]>,;]*)?""")
RE_ENV = re.compile(
    r"""(?:os\.environ(?:\.get)?\(\s*|os\.getenv\(\s*|os\.environ\[\s*)['"]([A-Z0-9_]{2,})['"]"""
    r"""|process\.env\.([A-Z0-9_]{2,})|\$\{\{\s*(?:secrets|vars)\.([A-Z0-9_]{2,})\s*\}\}""")
RE_JS_SIMBOLO = re.compile(
    r"""^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)"""
    r"""|^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="""
    r"""|^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"""
    r"""|^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(""", re.M)
RE_JS_IMPORT = re.compile(r"""(?:from\s+|require\(\s*|import\(\s*)['"]([^'"]+)['"]""")
RE_CRON = re.compile(r"""cron:\s*['"]([^'"]+)['"]""")
RE_HUELLA = re.compile(r"<!--\s*huella:\s*(\S+)\s*-->")
RE_RESUMEN = re.compile(r"^\s*(?:\*\*)?Resumen(?:\*\*)?:\s*(.+)$", re.M | re.I)
RE_BUSCAR = re.compile(r"^##+\s*Buscar ac[aá] si.*$", re.M | re.I)


# ---------------------------------------------------------------- utilidades

def cargar_gitignore(raiz):
    pats = []
    gi = raiz / ".gitignore"
    if gi.exists():
        for l in gi.read_text(errors="ignore").splitlines():
            l = l.split("#")[0].strip()
            if l and not l.startswith("!"):
                pats.append(l.rstrip("/"))
    return pats


def ignorado(rel, pats):
    partes = Path(rel).parts
    if any(p in IGNORAR_DIRS for p in partes):
        return True
    nombre = Path(rel).name
    if any(fnmatch.fnmatch(nombre, p) for p in IGNORAR_ARCHIVOS):
        return True
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(nombre, p)
               or rel.startswith(p + "/") for p in pats)


def leer(p):
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        return p.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        return None


def git(raiz, *args, timeout=20):
    # FORK NOWCAST: `--no-optional-locks`. `git status` refresca el indice y para eso
    # toma `.git/index.lock`. Corrido desde un entorno que no puede borrarlo (el
    # puente de Claude; GitHub Desktop cerrado a destiempo), el lock queda huerfano y
    # el proximo `git commit` de cualquiera falla. Es el URGENTE B, cerrado dos veces
    # y reabierto las dos por esta linea. Indexar es de solo lectura: no toma locks.
    try:
        r = subprocess.run(["git", "-C", str(raiz), "--no-optional-locks", *args],
                           capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- extractores

def extraer_python(texto):
    simbolos, imports, rel_imports = [], set(), []
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return simbolos, imports, rel_imports, False
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            simbolos.append({"nombre": n.name, "tipo": "funcion", "linea": n.lineno,
                             "firma": ", ".join(a.arg for a in n.args.args),
                             "doc": (ast.get_docstring(n) or "").split("\n")[0][:100] or None})
        elif isinstance(n, ast.ClassDef):
            simbolos.append({"nombre": n.name, "tipo": "clase", "linea": n.lineno,
                             "firma": ", ".join(m.name for m in n.body
                                                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)))[:120],
                             "doc": (ast.get_docstring(n) or "").split("\n")[0][:100] or None})
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                rel_imports.append((n.level, n.module or ""))
            elif n.module:
                imports.add(n.module)
    return simbolos, imports, rel_imports, ("__main__" in texto and "if __name__" in texto)


def extraer_js(texto):
    simbolos, imports, rel = [], set(), []
    vistos = set()
    for m in RE_JS_SIMBOLO.finditer(texto):
        n = next((g for g in m.groups() if g), None)
        if n and n not in vistos:
            vistos.add(n)
            tipo = "export" if m.group(1) or m.group(2) else "funcion"
            simbolos.append({"nombre": n, "tipo": tipo,
                             "linea": texto[:m.start()].count("\n") + 1,
                             "firma": "", "doc": None})
    for m in RE_JS_IMPORT.finditer(texto):
        esp = m.group(1)
        if esp.startswith("."):
            rel.append(esp)
        else:
            partes = esp.split("/")
            imports.add("/".join(partes[:2]) if esp.startswith("@") else partes[0])
    return simbolos, imports, rel, False


def extraer_urls(texto):
    out = defaultdict(set)
    for m in RE_URL.finditer(texto):
        h = m.group(1).lower()
        if h.startswith("www."):
            h = h[4:]
        if h in HOSTS_RUIDO:
            continue
        out[h].add((m.group(2) or "/").split("?")[0][:70])
    return out


def extraer_env(texto):
    return {g for t in RE_ENV.findall(texto) for g in t if g}


# ---------------------------------------------------------------- bitacoras

def parsear_bitacora(texto):
    """Extrae de una BITACORA.md lo que se eleva al MAPA.md."""
    huella = RE_HUELLA.search(texto)
    resumen = RE_RESUMEN.search(texto)
    pistas = []
    m = RE_BUSCAR.search(texto)
    if m:
        resto = texto[m.end():]
        corte = re.search(r"^##+\s", resto, re.M)
        bloque = resto[:corte.start()] if corte else resto
        for l in bloque.splitlines():
            l = l.strip()
            if l.startswith(("-", "*")):
                pistas.append(l.lstrip("-* ").strip())
    return {
        "huella_declarada": huella.group(1) if huella else None,
        # FORK NOWCAST: el formato usado en los README es `**Resumen:** texto`,
        # asi que el `**` de cierre cae dentro del grupo capturado. Se saca aca.
        "resumen": resumen.group(1).strip().lstrip("*").strip() if resumen else None,
        "pistas": pistas,
    }


def huella_carpeta(archivos_texto):
    """Hash del contenido de codigo de una carpeta. Cambia => la bitacora vencio."""
    h = hashlib.sha256()
    for ruta, texto in sorted(archivos_texto):
        h.update(ruta.encode())
        h.update(hashlib.sha256(texto.encode("utf-8", "ignore")).digest())
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- co-cambio git

def co_cambios(raiz, max_commits=400, max_archivos=15):
    """Archivos que se modifican en el mismo commit. Acoplamiento real, no declarado."""
    salida = git(raiz, "log", f"-{max_commits}", "--name-only", "--format=%x00%H",
                 "--no-merges")
    if not salida:
        return Counter(), Counter()
    pares, toques = Counter(), Counter()
    for bloque in salida.split("\x00")[1:]:
        lineas = [l.strip() for l in bloque.splitlines()[1:] if l.strip()]
        archivos = [l for l in lineas if Path(l).suffix in LENGUAJES]
        if not 2 <= len(archivos) <= max_archivos:
            for a in archivos:
                toques[a] += 1
            continue
        for a in archivos:
            toques[a] += 1
        for i, a in enumerate(archivos):
            for b in archivos[i + 1:]:
                pares[tuple(sorted((a, b)))] += 1
    return pares, toques


# ---------------------------------------------------------------- resolucion interna

def construir_resolucion(archivos, raiz):
    """Mapea nombres de modulo a rutas del repo, para resolver imports internos."""
    por_modulo = {}
    for a in archivos:
        p = Path(a["ruta"])
        if a["lenguaje"] == "python":
            partes = list(p.with_suffix("").parts)
            if partes[-1] == "__init__":
                partes = partes[:-1]
            for i in range(len(partes)):
                por_modulo.setdefault(".".join(partes[i:]), a["ruta"])
        elif a["lenguaje"] in ("javascript", "typescript"):
            por_modulo.setdefault(str(p.with_suffix("")), a["ruta"])
            por_modulo.setdefault(p.stem, a["ruta"])
    return por_modulo


def resolver_imports(archivos, por_modulo):
    """Aristas archivo -> archivo dentro del repo."""
    aristas = defaultdict(set)
    externos = Counter()
    for a in archivos:
        origen = a["ruta"]
        for imp in a.get("_imports_crudos", []):
            destino = por_modulo.get(imp) or por_modulo.get(imp.split(".")[0])
            if destino and destino != origen:
                aristas[origen].add(destino)
            elif imp.split(".")[0] not in STDLIB:
                externos[imp.split(".")[0]] += 1
        for rel in a.get("_rel_crudos", []):
            base = Path(origen).parent
            if isinstance(rel, tuple):           # python: (nivel, modulo)
                nivel, mod = rel
                for _ in range(nivel - 1):
                    base = base.parent
                cand = str(base / mod.replace(".", "/")) if mod else str(base)
            else:                                 # js: './x'
                cand = os.path.normpath(str(base / rel))
            destino = por_modulo.get(cand) or por_modulo.get(cand.replace("/", "."))
            if destino and destino != origen:
                aristas[origen].add(destino)
    return aristas, externos


# ---------------------------------------------------------------- FORK NOWCAST: inventario de datos
#
# PARCHE 8 (2026-09-08). Por que existe, en una frase: el mapa indexaba el CODIGO
# y no los DATOS, y en este repo el trabajo caro no es el codigo.
#
# El indexador ignora `*.parquet`, `*.csv`, `*.db` y `*.xlsx` dos veces (por
# IGNORAR_ARCHIVOS y por las reglas del .gitignore), asi que 140 archivos de datos
# —177 MB, incluida la base que el ADR-0009 declara fuente de verdad— eran
# invisibles para cualquiera que leyera MAPA.md. La consecuencia medida: en dos
# sesiones seguidas se busco "donde estan las taxonomias" y se reconstruyo una
# tabla que ya existia, porque la unica forma de saber que hay era grepear.
#
# Lo que responde este inventario, que es lo que se preguntaba a mano:
#   - QUE datos hay y DONDE (ruta, formato, filas, tamaño);
#   - si VIAJAN por git o viven en un solo disco (el bug numero uno del repo,
#     documentado seis veces en el .gitignore);
#   - QUIEN los escribe y QUIEN los lee -> si nadie los lee, sobran; si nadie los
#     escribe, no se regeneran.
#
# Es caro de calcular (abre cada parquet y cada base), asi que se CACHEA por
# (tamaño, mtime) contra el mapa.json anterior: una corrida sin cambios en datos
# no lee ningun archivo de datos.

EXT_DATOS = {
    ".parquet": "parquet", ".csv": "csv", ".db": "sqlite", ".sqlite": "sqlite",
    ".sqlite3": "sqlite", ".xlsx": "excel", ".xls": "excel", ".json": "json",
}
# JSON que son configuracion o esquema, no datos del proyecto.
JSON_NO_ES_DATO = {"package.json", "package-lock.json", "tsconfig.json", "mapa.json",
                   ".eslintrc.json", "settings.json", "composer.json"}
MAX_BYTES_CONTAR = 40_000_000     # arriba de esto no se cuentan filas (tarda mas de lo que aporta)
MAX_DATOS_MAPA = 200              # tope de filas del inventario en MAPA.md

_VERBOS_ESCRIBE = (
    "to_parquet", "to_csv", "to_excel", "to_json", "to_sql", "write_parquet",
    "write_text", "write_bytes", "write_table", "ExcelWriter", "json.dump",
    "executemany", "INSERT INTO", "CREATE TABLE", "REPLACE INTO", "savefig",
)
_VERBOS_LEE = (
    "read_parquet", "read_csv", "read_excel", "read_json", "read_sql", "read_table",
    "json.load", "ParquetFile", "SELECT ", "open(", "load(",
)
_VENTANA = 400                    # caracteres alrededor de la mencion


def _modulo_de(rel):
    """El modulo dueño de un archivo de datos: lo que hay antes de data/ u outputs/."""
    partes = rel.split("/")
    for corte in ("data", "outputs", "output"):
        if corte in partes:
            i = partes.index(corte)
            if i:
                return "/".join(partes[:i])
    return "/".join(partes[:-1]) or "."


def _forma_parquet(p):
    try:
        import pyarrow.parquet as pq
        md = pq.ParquetFile(p).metadata
        return md.num_rows, md.num_columns, ""
    except Exception:
        return None, None, ""


def _forma_csv(p, n_bytes):
    if n_bytes > MAX_BYTES_CONTAR:
        return None, None, "no contado (pesado)"
    try:
        with open(p, "r", encoding="utf-8", errors="ignore", newline="") as f:
            cabecera = f.readline()
            filas = sum(1 for _ in f)
        sep = ";" if cabecera.count(";") > cabecera.count(",") else ","
        return filas, cabecera.count(sep) + 1 if cabecera.strip() else 0, ""
    except OSError:
        return None, None, ""


def _forma_sqlite(p):
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        try:
            tablas = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            filas, detalle = 0, []
            for t in tablas:
                try:
                    n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
                except sqlite3.Error:
                    n = 0
                filas += n
                detalle.append((t, n))
            detalle.sort(key=lambda x: -x[1])
            txt = ", ".join(f"{t} ({n:,})" for t, n in detalle[:5])
            if len(detalle) > 5:
                txt += f" +{len(detalle) - 5}"
            return filas, len(tablas), txt
        finally:
            con.close()
    except Exception:
        return None, None, ""


def _forma_excel(p, n_bytes):
    try:
        import zipfile
        with zipfile.ZipFile(p) as z:
            hojas = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
        return None, len(hojas), f"{len(hojas)} hoja(s)"
    except Exception:
        return None, None, ""


def _forma_json(p, n_bytes):
    if n_bytes > 5_000_000:
        return None, None, "no contado (pesado)"
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8", errors="ignore"))
    except (OSError, ValueError):
        return None, None, ""
    if isinstance(d, list):
        return len(d), None, "lista"
    if isinstance(d, dict):
        return None, len(d), "objeto: " + ", ".join(list(d)[:4])
    return None, None, ""


def _forma(p, fmt, n_bytes):
    if fmt == "parquet":
        return _forma_parquet(p)
    if fmt == "csv":
        return _forma_csv(p, n_bytes)
    if fmt == "sqlite":
        return _forma_sqlite(p)
    if fmt == "excel":
        return _forma_excel(p, n_bytes)
    if fmt == "json":
        return _forma_json(p, n_bytes)
    return None, None, ""


def _constantes_de_rutas(raiz):
    """`ruta relativa -> [nombres de rutas.py que la apuntan]`.

    En este repo los modulos NO escriben la ruta literal: importan la constante de
    `rutas.py` (ADR-0010). Buscar solo el nombre del archivo daria CERO consumidores
    para todos los contratos entre modulos, que son justamente los que importan.
    """
    f = raiz / "rutas.py"
    if not f.is_file():
        return {}
    ns = {"__file__": str(f), "__name__": "_rutas_inventario"}
    try:
        exec(compile(f.read_text(encoding="utf-8"), str(f), "exec"), ns)
    except Exception:
        return {}
    salida = defaultdict(list)
    for nombre, valor in ns.items():
        if nombre.startswith("_") or not isinstance(valor, Path):
            continue
        try:
            rel = valor.resolve().relative_to(raiz).as_posix()
        except ValueError:
            continue
        salida[rel].append(nombre)
    return dict(salida)


def _nombres_relacionados(texto, semilla, profundidad=2, tope=14):
    """Nombres por los que puede circular una ruta dentro de UN archivo.

    Hace falta porque en este repo la ruta casi nunca se lee ni se escribe donde se
    nombra. Los tres casos reales, medidos el 08-09:

        CAL_CSV = DATA / "calendario_electoral.csv"      # la mencion
        def cargar(..., cal_csv: Path = CAL_CSV):        # viaja como default
            pd.read_csv(cal_csv)                         # se lee ACA

        OUT_DEFAULT = Path(".../serie_bloque.parquet")
        _cli_serie(canon, OUT_DEFAULT)                   # viaja como argumento
        def _cli_serie(canon, out): s.to_parquet(out)    # se escribe ACA

    Sin esto, `serie_bloque.parquet` —que el .gitignore declara contrato del
    ensemble— figuraba como "nadie lo escribe ni lo lee". Un inventario que dice
    eso de un contrato es peor que no tener inventario: invita a borrarlo.
    """
    nombres = set(semilla)
    frontera = set(semilla)
    for _ in range(profundidad):
        nuevos = set()
        for n in frontera:
            e = re.escape(n)
            # x = N   /   x: T = N   (incluye defaults de firma)
            for mm in re.finditer(r"([A-Za-z_]\w*)\s*(?::[^=\n]{0,60})?=\s*" + e + r"\b", texto):
                nuevos.add(mm.group(1))
            # f(..., N, ...) -> los parametros de f
            for mm in re.finditer(r"([A-Za-z_]\w*)\s*\([^()\n]{0,200}\b" + e + r"\b", texto):
                d = re.search(r"def\s+" + re.escape(mm.group(1)) + r"\s*\(([^)]{0,400})\)",
                              texto, re.S)
                if not d:
                    continue
                for par in d.group(1).split(","):
                    par = par.strip().split(":")[0].split("=")[0].strip().lstrip("*")
                    if re.fullmatch(r"[A-Za-z_]\w*", par or "") and par not in ("self", "cls"):
                        nuevos.add(par)
        nuevos -= nombres
        nombres |= nuevos
        frontera = nuevos
        if not frontera or len(nombres) > tope:
            break
    return nombres


def _aplica(texto, verbos, nombre):
    """El verbo se aplica a ESE nombre, en forma de funcion o de metodo."""
    e = re.escape(nombre)
    for v in verbos:
        if not v.replace("_", "").isalnum():
            continue                       # "SELECT ", "INSERT INTO": no son llamadas
        ve = re.escape(v)
        if re.search(ve + r"\s*\(\s*(?:str\()?\s*" + e + r"\b", texto):
            return True          # pd.read_csv(CAL_CSV)
        if re.search(e + r"\s*\.\s*" + ve + r"\s*\(", texto):
            return True          # REGISTRO.write_text(...)  /  df.to_parquet no aplica
    return False


def _modo_open(texto, nombre):
    """`open(X, "w")` escribe y `open(X)` lee. Es como se escribe medio CSV del repo.

    Sin esto `asignaciones.csv` —el registro unico de taxonomias, que cuesta llamadas
    de API— figuraba sin escritor: `registro.py` lo abre con `open(REGISTRO, "w")` y
    ningun verbo de pandas aparece cerca.
    """
    e = re.escape(nombre)
    escribe = lee = False
    patrones = (
        r"open\s*\(\s*" + e + r"\s*(?:,\s*[\"\']([rwax][^\"\']*)[\"\'])?",   # open(X, "w")
        e + r"\s*\.\s*open\s*\(\s*(?:[\"\']([rwax][^\"\']*)[\"\'])?",        # X.open("w")
    )
    for pat in patrones:
        for m in re.finditer(pat, texto):
            modo = m.group(1) or "r"
            if modo[0] in "wax":
                escribe = True
            else:
                lee = True
    return escribe, lee


def _clasificar_uso(texto, tokens):
    """escribe / lee / menciona. Ver `_nombres_relacionados` para el por que."""
    escribe = lee = False
    semilla = set()
    for tok in tokens:
        if re.fullmatch(r"[A-Za-z_]\w*", tok):
            semilla.add(tok)
        for mm in re.finditer(re.escape(tok), texto):
            i = mm.start()
            v = texto[max(0, i - _VENTANA):i + _VENTANA]
            if any(x in v for x in _VERBOS_ESCRIBE):
                escribe = True
            if any(x in v for x in _VERBOS_LEE):
                lee = True
            fin = texto.find("\n", i)
            linea = texto[texto.rfind("\n", 0, i) + 1:fin if fin > 0 else len(texto)]
            m2 = re.match(r"\s*([A-Za-z_]\w*)\s*(?::[^=\n]{0,60})?=", linea)
            if m2:
                semilla.add(m2.group(1))
    if semilla:
        for n in _nombres_relacionados(texto, semilla):
            if _aplica(texto, _VERBOS_ESCRIBE, n):
                escribe = True
            if _aplica(texto, _VERBOS_LEE, n):
                lee = True
            e_open, l_open = _modo_open(texto, n)
            escribe = escribe or e_open
            lee = lee or l_open
    if escribe and lee:
        return "ambos"
    if escribe:
        return "escribe"
    if lee:
        return "lee"
    return "menciona"


def escanear_datos(raiz, pats, textos_codigo, cache_previa):
    """Inventario de los archivos de DATOS del repo. Ver la cabecera de esta seccion."""
    constantes = _constantes_de_rutas(raiz)
    items = []
    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR_DIRS and not d.startswith(".")]
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            fmt = EXT_DATOS.get(p.suffix.lower())
            if not fmt or fn in JSON_NO_ES_DATO or fn == "Thumbs.db":
                continue
            rel = p.relative_to(raiz).as_posix()
            try:
                st = p.stat()
            except OSError:
                continue
            prev = cache_previa.get(rel)
            if prev and prev.get("bytes") == st.st_size and prev.get("mtime") == int(st.st_mtime):
                filas, cols, detalle = prev.get("filas"), prev.get("columnas"), prev.get("detalle", "")
            else:
                filas, cols, detalle = _forma(p, fmt, st.st_size)
            items.append({
                "ruta": rel, "modulo": _modulo_de(rel), "formato": fmt,
                "bytes": st.st_size, "mtime": int(st.st_mtime),
                "filas": filas, "columnas": cols, "detalle": detalle,
                "constantes": constantes.get(rel, []),
                "escriben": [], "leen": [], "mencionan": [],
            })

    # viaja por git?  una sola llamada para los 140.
    # `--no-optional-locks`: `git` normalmente refresca el indice y toma
    # `.git/index.lock`. Desde entornos que no pueden borrarlo (el puente de
    # Claude; GitHub Desktop cerrado a destiempo) el lock queda huerfano y el
    # commit del otro falla. Un chequeo de lectura no toma un lock de escritura.
    ignorados = set()
    if items:
        try:
            r = subprocess.run(
                ["git", "-C", str(raiz), "--no-optional-locks", "check-ignore", "--stdin"],
                input="\n".join(i["ruta"] for i in items),
                capture_output=True, text=True, timeout=60)
            ignorados = {l.strip() for l in r.stdout.splitlines() if l.strip()}
        except (OSError, subprocess.SubprocessError):
            ignorados = set()
    for i in items:
        i["viaja"] = i["ruta"] not in ignorados

    # quien lo escribe y quien lo lee
    # Nombres repetidos: `diputados.csv` existe en tres carpetas. Atribuirle a las
    # tres cada mencion del nombre pelado inventa productores (paso: el inventario
    # v1 decia que `padron_diputados_historico.py` escribia el `diputados.csv` del
    # volcado de la decada). Para esos se exige ademas que el codigo nombre la
    # carpeta; si no la nombra, la mencion no alcanza para atribuir nada.
    veces = Counter(Path(i["ruta"]).name for i in items)
    for rel_src, texto in textos_codigo.items():
        if rel_src == "rutas.py" or rel_src.startswith(".mapa/"):
            continue                       # rutas.py declara; no produce ni consume
        ident = set(re.findall(r"[A-Za-z_]\w*", texto))
        for i in items:
            toks = []
            nombre = Path(i["ruta"]).name
            padre = Path(i["ruta"]).parent.name
            if nombre in texto and (veces[nombre] == 1 or padre in texto):
                toks.append(nombre)
            toks += [c for c in i["constantes"] if c in ident]
            if not toks:
                continue
            clase = _clasificar_uso(texto, toks)
            if clase in ("escribe", "ambos"):
                i["escriben"].append(rel_src)
            if clase in ("lee", "ambos"):
                i["leen"].append(rel_src)
            if clase == "menciona":
                i["mencionan"].append(rel_src)
    for i in items:
        i["escriben"] = sorted(set(i["escriben"]))
        i["leen"] = sorted(set(i["leen"]) - set(i["escriben"]))
        i["mencionan"] = sorted(set(i["mencionan"]) - set(i["escriben"]) - set(i["leen"]))
    return sorted(items, key=lambda x: (x["modulo"], x["ruta"]))


# ---------------------------------------------------------------- escaneo

def indexar(ruta):
    raiz = Path(ruta).resolve()
    if not raiz.is_dir():
        sys.exit(f"No es un directorio: {raiz}")
    pats = cargar_gitignore(raiz)

    archivos = []
    textos_por_carpeta = defaultdict(list)
    textos_codigo = {}                               # FORK NOWCAST (parche 8)
    bitacoras = {}
    readmes = {}                                     # FORK NOWCAST (ver cabecera)
    hosts = defaultdict(lambda: defaultdict(set))   # host -> archivo -> rutas
    envs = defaultdict(set)                          # var -> archivos
    workflows = []
    entrypoints = []

    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR_DIRS
                       and (not d.startswith(".") or d == ".github")]
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            # `.as_posix()` y no `str()`: en Windows `str(Path(...))` devuelve
            # separadores `\` y el resto del archivo compara contra `/` a mano. La
            # consecuencia se midió el 06-09-2026: la regla que marca `src/` y `tests/`
            # como "heredada" —`c.startswith(padre + "/")`— no matcheaba nunca en
            # Windows, así que cada subcarpeta se llevaba su propia fila y la tabla
            # `## Carpetas` pasaba de 38 a 79 líneas. MAPA.md daba 259 en Linux y 301 en
            # Windows con EXACTAMENTE el mismo índice (159 archivos, 38.195 LOC, 74
            # carpetas), y el aviso de presupuesto saltaba sólo en una de las dos.
            # MAPA.md está versionado: un generador que depende del sistema operativo
            # produce un diff en cada corrida.
            rel = p.relative_to(raiz).as_posix()
            if ignorado(rel, pats):
                continue
            texto = leer(p)
            if texto is None:
                continue
            carpeta = Path(rel).parent.as_posix() if Path(rel).parent != Path(".") else "."

            if fn.upper() == "BITACORA.MD":
                bitacoras[carpeta] = parsear_bitacora(texto)
                continue
            if fn.upper() == "README.MD":
                # FORK NOWCAST: en este repo el contrato de cada modulo ya vive
                # en su README.md. Se lee de ahi el `Resumen:` y el `## Buscar
                # aca si` en vez de pedir un BITACORA.md paralelo. NO lleva
                # `continue`: el README se sigue indexando como archivo normal.
                readmes[carpeta] = parsear_bitacora(texto)

            lenguaje = LENGUAJES.get(p.suffix, "otro")
            loc = texto.count("\n") + 1
            simbolos, imps, rels, es_ep = [], set(), [], False
            if lenguaje == "python":
                simbolos, imps, rels, es_ep = extraer_python(texto)
            elif lenguaje in ("javascript", "typescript"):
                simbolos, imps, rels, es_ep = extraer_js(texto)

            for h, rutas in extraer_urls(texto).items():
                hosts[h][rel] |= rutas
            for e in extraer_env(texto):
                envs[e].add(rel)

            if rel.startswith(".github/workflows"):
                workflows.append({
                    "archivo": rel,
                    "nombre": (re.search(r"^name:\s*(.+)$", texto, re.M) or [None, p.stem])[1].strip().strip("'\""),
                    "cron": RE_CRON.findall(texto),
                    "manual": "workflow_dispatch" in texto,
                })
            if es_ep or fn in ("main.py", "app.py", "index.js", "main.go", "run.py",
                               "manage.py", "cli.py", "bot.py", "server.py", "__main__.py"):
                entrypoints.append(rel)

            if lenguaje in CODIGO:
                textos_por_carpeta[carpeta].append((rel, texto))
            # FORK NOWCAST (parche 8): el inventario de datos necesita el texto de
            # TODO lo que puede nombrar un archivo de datos, y eso incluye los .ps1
            # y los .yml de workflows, no solo el codigo "de verdad".
            if lenguaje in CODIGO or lenguaje in ("yaml", "toml", "powershell"):
                textos_codigo[rel] = texto
            if lenguaje in CODIGO or lenguaje in ("yaml", "toml"):
                archivos.append({
                    "ruta": rel, "carpeta": carpeta, "lenguaje": lenguaje, "loc": loc,
                    "simbolos": simbolos,
                    "_imports_crudos": sorted(imps),
                    "_rel_crudos": rels,
                })

    # relaciones internas
    por_modulo = construir_resolucion(archivos, raiz)
    aristas, externos = resolver_imports(archivos, por_modulo)
    importado_por = defaultdict(set)
    for o, ds in aristas.items():
        for d in ds:
            importado_por[d].add(o)

    pares, toques = co_cambios(raiz)

    # FORK NOWCAST (parche 8): inventario de datos, con cache por (bytes, mtime)
    # contra el mapa.json anterior. Sin el cache, cada indexado abre 140 archivos
    # (incluida una base de 86 MB) y el hook de pre-commit se vuelve inusable.
    cache_previa = {}
    _anterior = raiz / ".mapa" / "mapa.json"
    if _anterior.is_file():
        try:
            cache_previa = {d["ruta"]: d for d in
                            json.loads(_anterior.read_text(encoding="utf-8")).get(
                                "inventario_datos", [])}
        except (OSError, ValueError):
            cache_previa = {}
    inventario = escanear_datos(raiz, pats, textos_codigo, cache_previa)

    # FORK NOWCAST: un README solo cuenta como bitacora si aporta algo (resumen
    # o pistas). Si no, la carpeta sigue figurando como "sin describir" — que es
    # la verdad, y es lo que hace util al diagnostico.
    for _c, _i in readmes.items():
        if _c not in bitacoras and (_i["resumen"] or _i["pistas"]):
            bitacoras[_c] = _i

    # carpetas
    carpetas = {}
    todas = sorted({a["carpeta"] for a in archivos} | set(bitacoras))
    con_bitacora = set(bitacoras)
    for c in todas:
        propios = [a for a in archivos if a["carpeta"] == c]
        # FORK NOWCAST: la huella de un modulo cubre TAMBIEN su src/ y tests/.
        # Sin esto el README de `variables/embudo` se sellaba contra el hash de
        # una carpeta que solo contiene al README: tocar `src/embudo.py` no lo
        # vencia nunca y el sello afirmaba una frescura falsa — peor que no
        # tener sello.
        textos = list(textos_por_carpeta.get(c, []))
        if c in con_bitacora:
            for c2, tx in textos_por_carpeta.items():
                if c2.startswith(c.rstrip("/") + "/") and c2 not in con_bitacora:
                    textos += tx
        h = huella_carpeta(textos)
        bit = bitacoras.get(c)
        if bit:
            estado = "al dia" if bit["huella_declarada"] == h else "desactualizada"
        elif any(c.startswith(a.rstrip("/") + "/") for a in bitacoras if a != "."):
            # FORK NOWCAST: src/ y tests/ estan descriptos por el README del
            # modulo que los contiene. Pedirles bitacora propia serian 40
            # archivos que repiten lo mismo.
            estado = "heredada"
        else:
            estado = "sin bitacora"
        carpetas[c] = {
            "archivos": len(propios),
            "loc": sum(a["loc"] for a in propios),
            "lenguajes": [l for l, _ in Counter(a["lenguaje"] for a in propios).most_common(3)],
            "huella": h,
            "estado_bitacora": estado,
            "resumen": (bit or {}).get("resumen"),
            "pistas": (bit or {}).get("pistas", []),
            "simbolos": sum(len(a["simbolos"]) for a in propios),
        }

    # acoplamiento entre carpetas
    entre_carpetas = Counter()
    dir_de = {a["ruta"]: a["carpeta"] for a in archivos}
    for o, ds in aristas.items():
        for d in ds:
            co, cd = dir_de.get(o), dir_de.get(d)
            if co and cd and co != cd:
                entre_carpetas[(co, cd)] += 1

    for a in archivos:
        a.pop("_imports_crudos", None)
        a.pop("_rel_crudos", None)
        a["importa"] = sorted(aristas.get(a["ruta"], []))
        a["importado_por"] = sorted(importado_por.get(a["ruta"], []))
        a["commits"] = toques.get(a["ruta"], 0)

    mapa = {
        "proyecto": raiz.name,
        "ruta": str(raiz),
        "indexado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "git": {
            "rama": git(raiz, "rev-parse", "--abbrev-ref", "HEAD").strip() or None,
            "ultimo_commit": git(raiz, "log", "-1", "--format=%cs %h %s").strip() or None,
            "sucio": bool([l for l in git(raiz, "status", "--porcelain").splitlines()
                           if ".mapa/" not in l and "MAPA.md" not in l]),
        },
        "tamano": {
            "archivos": len(archivos),
            "loc": sum(a["loc"] for a in archivos),
            "por_lenguaje": dict(Counter(
                {l: sum(a["loc"] for a in archivos if a["lenguaje"] == l)
                 for l in {a["lenguaje"] for a in archivos}}).most_common()),
        },
        "entrypoints": sorted(set(entrypoints)),
        "workflows": workflows,
        "carpetas": carpetas,
        "inventario_datos": inventario,
        "acoplamiento": [{"de": a, "a": b, "peso": n}
                         for (a, b), n in entre_carpetas.most_common()],
        "co_cambio": [{"a": a, "b": b, "veces": n}
                      for (a, b), n in pares.most_common(40) if n >= 3],
        "dependencias_externas": dict(externos.most_common(40)),
        "fuentes_externas": [
            {"host": h, "archivos": sorted(m), "rutas": sorted({r for rs in m.values() for r in rs})[:10]}
            for h, m in sorted(hosts.items(), key=lambda x: -len(x[1]))],
        "variables_entorno": {k: sorted(v) for k, v in sorted(envs.items())},
        "archivos": sorted(archivos, key=lambda a: -a["loc"]),
    }
    return mapa


# ---------------------------------------------------------------- diagnostico

def diagnostico(m):
    d = {"sin_bitacora": [], "bitacora_vencida": [], "huerfanos": [], "grandes": [],
         "ciclos": [], "co_cambio_disperso": [], "carpetas_infladas": []}
    for c, info in m["carpetas"].items():
        if info["archivos"] == 0:
            continue
        if info["estado_bitacora"] == "sin bitacora" and info["loc"] > 80:
            d["sin_bitacora"].append(c)
        elif info["estado_bitacora"] == "desactualizada":
            d["bitacora_vencida"].append(c)
        if info["archivos"] > 15:
            d["carpetas_infladas"].append((c, info["archivos"]))

    eps = set(m["entrypoints"])
    for a in m["archivos"]:
        if a["loc"] > GRANDE:
            d["grandes"].append((a["ruta"], a["loc"]))
        if (not a["importado_por"] and a["ruta"] not in eps
                and a["lenguaje"] in CODIGO and a["simbolos"]
                and "test" not in a["ruta"].lower()
                and not a["ruta"].startswith(".github")):
            d["huerfanos"].append(a["ruta"])

    pesos = {(x["de"], x["a"]): x["peso"] for x in m["acoplamiento"]}
    for (a, b), n in pesos.items():
        if (b, a) in pesos and a < b:
            d["ciclos"].append((a, b, n, pesos[(b, a)]))

    dir_de = {a["ruta"]: a["carpeta"] for a in m["archivos"]}
    for cc in m["co_cambio"]:
        ca, cb = dir_de.get(cc["a"]), dir_de.get(cc["b"])
        if ca and cb and ca != cb and cc["veces"] >= 4:
            d["co_cambio_disperso"].append((cc["a"], cc["b"], cc["veces"]))
    return d


def texto_diagnostico(d):
    L = ["## Diagnostico de estructura", ""]
    def bloque(titulo, items, fmt, nota=None):
        if not items:
            return
        L.append(f"**{titulo}**")
        if nota:
            L.append(f"_{nota}_")
        L.append("")
        for i in items[:12]:
            L.append("- " + fmt(i))
        L.append("")
    bloque("Carpetas sin bitacora", d["sin_bitacora"], lambda x: f"`{x}/`",
           "Cada una obliga a leer sus archivos para saber que hacen.")
    bloque("Bitacoras vencidas", d["bitacora_vencida"], lambda x: f"`{x}/`",
           "El codigo cambio desde que se escribieron. Refrescarlas o el mapa miente.")
    bloque("Archivos que nadie importa", d["huerfanos"], lambda x: f"`{x}`",
           "Codigo muerto, script suelto o entrypoint no declarado. Verificar cual.")
    bloque("Archivos grandes", d["grandes"], lambda x: f"`{x[0]}` ({x[1]} LOC)",
           "Candidatos a partir: encarecen cada lectura futura.")
    bloque("Ciclos entre carpetas", d["ciclos"],
           lambda x: f"`{x[0]}/` ↔ `{x[1]}/` ({x[2]} y {x[3]} imports)",
           "Se importan mutuamente: el limite entre ambas no esta bien trazado.")
    bloque("Cambian juntos pero viven separados", d["co_cambio_disperso"],
           lambda x: f"`{x[0]}` + `{x[1]}` ({x[2]} commits)",
           "Acoplamiento real que la estructura de carpetas no refleja.")
    bloque("Carpetas infladas", d["carpetas_infladas"], lambda x: f"`{x[0]}/` ({x[1]} archivos)",
           "Sin subdivision, obligan a escanear todo para encontrar algo.")
    if len(L) == 2:
        L.append("Sin hallazgos.")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- FORK NOWCAST: inventario en el MAPA

def _humano(n):
    if n >= 1024 * 1024:
        return f"{n / 1048576:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n} B"


def _forma_texto(i):
    if i["filas"] is not None and i["columnas"]:
        return f"{i['filas']:,}×{i['columnas']}"
    if i["filas"] is not None:
        return f"{i['filas']:,} filas"
    if i["detalle"]:
        return i["detalle"][:40]
    return "—"


def seccion_inventario(m):
    """El inventario de datos del MAPA. Indexado, generado, no editable a mano."""
    datos = m.get("inventario_datos") or []
    if not datos:
        return []
    L = ["## Inventario de datos", ""]
    tot = sum(d["bytes"] for d in datos)
    n_no_viajan = sum(1 for d in datos if not d["viaja"])
    L.append(f"{len(datos)} archivos de datos · {_humano(tot)} · "
             f"{len(datos) - n_no_viajan} viajan por git, **{n_no_viajan} no**.")
    L.append("")
    L.append("Buscar uno sin abrir nada: `python .mapa/buscar.py --dato <termino>`. "
             "Columna **git**: `si` = esta versionado, o sea que quien clone lo tiene; "
             "`NO` = vive solo en el disco de quien lo genero, que es el modo de falla "
             "mas repetido de este repo (seis veces, ver `.gitignore`). "
             "**Escribe/Lee**: quien lo produce y quien lo consume, deducido del codigo; "
             "sin lector, sobra — sin escritor, no se regenera.")
    L.append("")

    # UNA sola tabla y no una por modulo: el encabezado de cada grupo costaba 5
    # lineas y con 30 modulos eran 150 lineas de decoracion para 140 filas de dato.
    # La ruta ya dice de que modulo es.
    L.append("| Archivo | Forma | Peso | git | Escribe | Lee |")
    L.append("|---|---|---:|:---:|---|---|")
    orden = sorted(datos, key=lambda d: (d["modulo"], -d["bytes"]))
    for n, d in enumerate(orden):
        if n >= MAX_DATOS_MAPA:
            L.append(f"| _+{len(orden) - MAX_DATOS_MAPA} mas_ | | | | | |")
            break
        esc = ", ".join(f"`{Path(x).name}`" for x in d["escriben"][:2]) or "—"
        lee = ", ".join(f"`{Path(x).name}`" for x in d["leen"][:3])
        if len(d["leen"]) > 3:
            lee += f" +{len(d['leen']) - 3}"
        if not lee:
            lee = f"_({len(d['mencionan'])} lo nombran)_" if d["mencionan"] else "—"
        cte = f" _{d['constantes'][0]}_" if d["constantes"] else ""
        L.append(f"| `{d['ruta']}`{cte} | {_forma_texto(d)} | {_humano(d['bytes'])} | "
                 f"{'si' if d['viaja'] else '**NO**'} | {esc} | {lee} |")
    L.append("")

    huerfanos = [d for d in datos
                 if not d["escriben"] and not d["leen"] and not d["mencionan"]]
    sin_lector = [d for d in datos if d["escriben"] and not d["leen"]]
    no_viajan = [d for d in datos if not d["viaja"] and d["bytes"] > 100_000]
    if huerfanos or sin_lector or no_viajan:
        L.append("**Lo que el inventario marca**")
        L.append("")
        if no_viajan:
            L.append(f"- No viajan por git y pesan (>100 KB): "
                     + ", ".join(f"`{d['ruta']}`" for d in sorted(
                         no_viajan, key=lambda x: -x["bytes"])[:8])
                     + (f" _+{len(no_viajan) - 8}_" if len(no_viajan) > 8 else "")
                     + ". Cada uno vive en un solo disco.")
        if sin_lector:
            L.append(f"- Tienen productor y **ningun consumidor** ({len(sin_lector)}): "
                     + ", ".join(f"`{Path(d['ruta']).name}`" for d in sin_lector[:8])
                     + (f" _+{len(sin_lector) - 8}_" if len(sin_lector) > 8 else "")
                     + ". Es lo esperable en un entregable para humanos; en un "
                       "intermedio significa que sobra.")
        if huerfanos:
            peso = sum(d["bytes"] for d in huerfanos)
            L.append(f"- **Ningun archivo de codigo los nombra** ({len(huerfanos)}, "
                     f"{_humano(peso)}): "
                     + ", ".join(f"`{Path(d['ruta']).name}`" for d in sorted(
                         huerfanos, key=lambda x: -x["bytes"])[:8])
                     + (f" _+{len(huerfanos) - 8}_" if len(huerfanos) > 8 else "")
                     + ". Ojo: un output con nombre armado por f-string cae aca y "
                       "esta vivo. Lo que hay que mirar de verdad son los pesados.")
        L.append("")
    return L


# ---------------------------------------------------------------- MAPA.md

def generar_mapa(m):
    L = [f"# MAPA — {m['proyecto']}", ""]
    L.append("<!-- GENERADO por indexar.py. No editar: los cambios se pierden. -->")
    L.append("<!-- La prosa vive en el README.md de cada modulo (seccion `Buscar aca si`). -->")
    t = m["tamano"]
    git_i = m["git"]
    L.append(f"<!-- {m['indexado']} · {t['archivos']} archivos · {t['loc']:,} LOC -->")
    L.append("")

    L.append("## Como usar este archivo")
    L.append("")
    L.append("Es el unico archivo del proyecto que hace falta leer para empezar. Para "
             "ubicar algo concreto: `python3 .mapa/buscar.py \"<termino>\"` devuelve "
             "archivo y linea sin abrir nada. Recien despues abrir los archivos que "
             "salgan, y solo esos.")
    L.append("")
    if git_i.get("ultimo_commit"):
        sucio = " · **hay cambios sin commitear**" if git_i.get("sucio") else ""
        L.append(f"Rama `{git_i.get('rama')}` — ultimo commit: {git_i['ultimo_commit']}{sucio}")
        L.append("")

    # --- router
    L.append("## Donde buscar que")
    L.append("")
    filas = []
    for c, info in sorted(m["carpetas"].items()):
        for p in info["pistas"]:
            filas.append((p, c))
    if filas:
        L.append("| Si la consulta es sobre... | Ir a |")
        L.append("|---|---|")
        for pista, c in filas:
            L.append(f"| {pista} | `{c}/` |")
    else:
        L.append("_Sin pistas todavia: ningun modulo tiene seccion \"Buscar aca si\" "
                 "en su README.md. Es la seccion que hace util a este mapa._")
    L.append("")

    # --- carpetas
    L.append("## Carpetas")
    L.append("")
    L.append("| Carpeta | Que es | Arch. | LOC | Bitacora |")
    L.append("|---|---|---:|---:|---|")
    marca = {"al dia": "ok", "desactualizada": "**vencida**", "sin bitacora": "—"}
    # FORK NOWCAST: una fila por MODULO, no por carpeta fisica. `variables/embudo`
    # y su `src/` + `tests/` son una sola unidad de trabajo (un modulo, un dueno,
    # una rama); listarlas por separado triplicaba la tabla y la sacaba del
    # presupuesto de 260 lineas sin agregar informacion.
    filas_c = []
    for c, i in m["carpetas"].items():
        if i["estado_bitacora"] == "heredada":
            continue                                    # la suma su modulo
        arch, loc = i["archivos"], i["loc"]
        hijas = []
        for c2, i2 in m["carpetas"].items():
            if i2["estado_bitacora"] == "heredada" and c2.startswith(c.rstrip("/") + "/"):
                arch += i2["archivos"]; loc += i2["loc"]
                hijas.append(c2.split("/")[-1])
        if arch == 0 and not i["resumen"]:
            continue
        sub = f" _({'+'.join(sorted(set(hijas)))})_" if hijas else ""
        filas_c.append((loc, f"| `{c}/`{sub} | {i['resumen'] or '_sin describir_'} | "
                             f"{arch} | {loc:,} | {marca.get(i['estado_bitacora'], '—')} |"))
    for _, fila in sorted(filas_c, key=lambda x: -x[0]):
        L.append(fila)
    L.append("")

    # --- inventario de datos (FORK NOWCAST, parche 8)
    L += seccion_inventario(m)

    # --- entradas
    if m["entrypoints"] or m["workflows"]:
        L.append("## Puntos de entrada")
        L.append("")
        for e in m["entrypoints"][:10]:
            L.append(f"- `{e}`")
        for w in m["workflows"]:
            disp = ", ".join(w["cron"]) if w["cron"] else ("manual" if w["manual"] else "push")
            L.append(f"- `{w['archivo']}` — {w['nombre']} ({disp})")
        L.append("")

    # --- nucleo
    centrales = sorted(m["archivos"], key=lambda a: (-len(a["importado_por"]), -a["loc"]))
    centrales = [a for a in centrales if a["importado_por"] or a["loc"] > 150][:12]
    if centrales:
        L.append("## Archivos centrales")
        L.append("")
        L.append("Ordenados por cuantos otros archivos dependen de ellos. Tocar uno de "
                 "arriba tiene mas radio de impacto.")
        L.append("")
        L.append("| Archivo | LOC | Lo usan | Simbolos |")
        L.append("|---|---:|---:|---|")
        for a in centrales:
            nombres = ", ".join(f"`{s['nombre']}`" for s in a["simbolos"][:4])
            L.append(f"| `{a['ruta']}` | {a['loc']} | {len(a['importado_por'])} | {nombres or '—'} |")
        L.append("")

    # --- flujo entre carpetas
    if m["acoplamiento"]:
        L.append("## Flujo interno")
        L.append("")
        for x in m["acoplamiento"][:12]:
            L.append(f"- `{x['de']}/` → `{x['a']}/` ({x['peso']})")
        L.append("")

    # --- co-cambio
    if m["co_cambio"]:
        L.append("## Se tocan juntos")
        L.append("")
        L.append("Segun el historial de git. Si vas a cambiar uno, mira el otro.")
        L.append("")
        for cc in m["co_cambio"][:10]:
            L.append(f"- `{cc['a']}` + `{cc['b']}` ({cc['veces']} commits)")
        L.append("")

    # --- fuentes y config
    if m["fuentes_externas"]:
        L.append("## Fuentes externas")
        L.append("")
        for f in m["fuentes_externas"][:12]:
            L.append(f"- `{f['host']}` — {', '.join(f'`{a}`' for a in f['archivos'][:3])}")
        L.append("")
    if m["variables_entorno"]:
        L.append("## Configuracion requerida")
        L.append("")
        for k, archivos in list(m["variables_entorno"].items())[:15]:
            L.append(f"- `{k}` — {', '.join(f'`{a}`' for a in archivos[:3])}")
        L.append("")

    # --- frescura
    venc = [c for c, i in m["carpetas"].items() if i["estado_bitacora"] == "desactualizada"]
    falt = [c for c, i in m["carpetas"].items()
            if i["estado_bitacora"] == "sin bitacora" and i["loc"] > 80]
    if venc or falt:
        L.append("## Frescura")
        L.append("")
        if venc:
            L.append(f"- Bitacoras vencidas: {', '.join(f'`{c}/`' for c in venc)}")
        if falt:
            L.append(f"- Carpetas sin bitacora: {', '.join(f'`{c}/`' for c in falt)}")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- main

def sellar(raiz, c, info, callado=False):
    """Estampa la huella del contenido actual en la bitacora de la carpeta.

    FORK NOWCAST: cae al README.md si no hay BITACORA.md, y preserva el final de
    linea original (medio repo esta en CRLF; reescribir en LF haria que el diff
    de git sea el archivo entero).
    """
    bit = raiz / c / "BITACORA.md"
    if not bit.exists():
        bit = raiz / c / "README.md"
    if not bit.exists():
        if callado:
            return 0
        sys.exit(f"No existe bitacora ni README en {c}/.")
    crudo = bit.read_bytes()
    fin = "\r\n" if crudo.count(b"\r\n") > crudo.count(b"\n") // 2 else "\n"
    texto = crudo.decode("utf-8").replace("\r\n", "\n")
    marca = f"<!-- huella: {info['huella']} -->"
    nuevo = (RE_HUELLA.sub(marca, texto) if RE_HUELLA.search(texto)
             else re.sub(r"^(#\s.*\n)", r"\1\n" + marca + "\n", texto, count=1))
    if nuevo == texto:
        return 0
    salida = nuevo.replace("\n", fin).encode("utf-8")
    bit.write_bytes(salida)
    if not callado:
        print(f"{c}/{bit.name} sellado con huella {info['huella']}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="Indice vivo de un proyecto")
    ap.add_argument("ruta", nargs="?", default=".")
    ap.add_argument("--estructura", action="store_true", help="diagnostico de estructura")
    ap.add_argument("--verbose", action="store_true",
                    help="desglose de lineas por seccion del MAPA")
    ap.add_argument("--solo-json", action="store_true", help="no reescribir MAPA.md")
    ap.add_argument("--frescura", action="store_true", help="solo reportar desactualizados")
    ap.add_argument("--sellar", metavar="CARPETA",
                    help="estampa la huella actual en la BITACORA.md de esa carpeta "
                         "(usar SOLO despues de actualizarle el contenido)")
    ap.add_argument("--sellar-todo", action="store_true",
                    help="FORK NOWCAST: sella TODAS las bitacoras/README de una, con un solo indexado")
    args = ap.parse_args()

    m = indexar(args.ruta)
    raiz = Path(m["ruta"])

    if args.sellar:
        c = args.sellar.rstrip("/")
        info = m["carpetas"].get(c)
        if not info:
            sys.exit(f"Carpeta no indexada: {c}")
        sellar(raiz, c, info)
        return

    if args.sellar_todo:
        # FORK NOWCAST: sellar de a una carpeta reindexaba el repo entero cada
        # vez. Con 30 modulos eso son minutos; aca se sella todo con un indice.
        n = 0
        for c, info in sorted(m["carpetas"].items()):
            if info["estado_bitacora"] in ("al dia", "desactualizada"):
                n += sellar(raiz, c, info, callado=True)
        print(f"{n} README sellados", file=sys.stderr)
        return

    destino = raiz / ".mapa"
    destino.mkdir(exist_ok=True)
    (destino / "mapa.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")

    # dejar buscar.py junto al indice para que el comando del MAPA funcione
    origen_buscar = Path(__file__).parent / "buscar.py"
    if origen_buscar.exists() and not (destino / "buscar.py").exists():
        (destino / "buscar.py").write_text(origen_buscar.read_text(), encoding="utf-8")

    if args.frescura:
        for c, i in sorted(m["carpetas"].items()):
            # FORK NOWCAST: "heredada" (la describe el README de su modulo) es
            # lo esperado, no un pendiente. Solo se avisa de lo que miente.
            if i["estado_bitacora"] in ("desactualizada", "sin bitacora") and i["loc"] > 80:
                print(f"{i['estado_bitacora']:16} {c}/  (huella actual {i['huella']})")
        return

    if not args.solo_json:
        texto = generar_mapa(m)
        (raiz / "MAPA.md").write_text(texto, encoding="utf-8")
        n = texto.count("\n")
        aviso = "  ← excede el presupuesto, podar secciones" if n > MAX_LINEAS_MAPA else ""
        print(f"MAPA.md: {n} lineas{aviso}", file=sys.stderr)
        # DESGLOSE POR SECCION. No es adorno: el 06-09-2026 la corrida de Franco
        # reporto 301 lineas y la del sandbox 259, con EXACTAMENTE los mismos 158
        # archivos y 37.669 LOC. O sea que la diferencia no estaba en el contenido
        # indexado sino en el entorno, y sin desglose no habia forma de saber que
        # seccion crecia. "Excede el presupuesto" sin decir DONDE no es un aviso
        # accionable.
        if n > MAX_LINEAS_MAPA or args.verbose:
            sec, actual = {}, "(cabecera)"
            for l in texto.split("\n"):
                if l.startswith("## "):
                    actual = l[3:]
                sec[actual] = sec.get(actual, 0) + 1
            for k, v in sorted(sec.items(), key=lambda x: -x[1]):
                print(f"    {v:>4} lineas  {k}", file=sys.stderr)

    print(f".mapa/mapa.json: {m['tamano']['archivos']} archivos, "
          f"{m['tamano']['loc']:,} LOC, {len(m['carpetas'])} carpetas", file=sys.stderr)

    if args.estructura:
        print(texto_diagnostico(diagnostico(m)))


if __name__ == "__main__":
    main()
