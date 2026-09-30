# -*- coding: utf-8 -*-
"""Comprobación estática de los tres bots (auditoría 2026-09, ítem A9).

QUÉ MIDE. Si `bot-diario`, `padron-vivo` e `icg-mensual` siguen teniendo todo lo que necesitan
en `HEAD` después de que la auditoría eliminó y movió archivos (A6 y A7). NO ejecuta nada de la
red: eso lo hace el ensayo aparte (criterio 6 del pre-registro) y la corrida real en GitHub
*Actions* (que confirma Franco).

CRITERIOS, fijados antes de mirar los resultados (2026-09-30; ver «A9 — pre-registro» en
ESTADO-EJECUCION.md). Umbral de cada uno: 0 fallas.
  1. los tres `.yml` no cambiaron desde `auditoria-punto-de-partida`; sin `pull_request`;
     mismos `permissions:`.
  2. toda ruta que nombran los workflows (o el texto de sus avisos) existe y viaja por git
     (salvo las que el script crea) y no está entre los archivos eliminados o movidos.
  3. la clausura de imports locales de los scripts de entrada sólo tiene archivos vivos; los
     imports de terceros los cubre lo que instala cada workflow.
  4. ningún archivo de esa clausura ni de los workflows nombra un archivo eliminado o movido.
  5. lo que los bots escriben y leen sigue existiendo y viajando por git, y sus lectores según
     el índice del repo (`.mapa/mapa.json`) siguen existiendo.

    python coordinacion/AUDITORIA-2026-09/verificar_bots.py [--sin-json]
Salida: coordinacion/AUDITORIA-2026-09/resultados/verificar_bots.json. Código de salida 1 si algún
criterio falla. Se repite en E (cierre) y cada vez que se toque algo que los bots lean.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())
TAG = "auditoria-punto-de-partida"
WORKFLOWS = ("bot-diario", "padron-vivo", "icg-mensual")
SALIDA_JSON = Path(__file__).resolve().parent / "resultados" / "verificar_bots.json"

# Lo que los bots escriben (los `git add` de los workflows) y lo que lee `vigilar_padron.py`
# (por su código: `padron_<camara>.csv` y `raw/nomina_<camara>.csv`).
SALIDAS = (
    "datos/bot_recoleccion/data/clean/dae_entradas.parquet",
    "datos/bot_recoleccion/data/clean/tp_entradas.parquet",
    "datos/bot_recoleccion/data/clean/votaciones_nuevas.parquet",
    "datos/bot_recoleccion/data/estado_bot.json",
    "datos/padron/data/estado_vigilancia.json",
    "datos/padron/outputs/vigilancia_padron.md",
    "variables/proyecto/data/icg_mensual.csv",
)
INSUMOS_PADRON = (
    "datos/padron/data/padron_diputados.csv",
    "datos/padron/data/padron_senado.csv",
    "datos/padron/data/raw/nomina_senado.csv",
)

# distribución de PyPI -> nombre con el que se importa, y lo que trae por dependencia
IMPORTA_COMO = {"beautifulsoup4": "bs4", "pyyaml": "yaml", "python-dateutil": "dateutil", "python-dotenv": "dotenv"}
TRAE_CONSIGO = {
    "pandas": {"numpy", "dateutil", "pytz", "tzdata"},
    "requests": {"urllib3", "idna", "certifi", "charset_normalizer"},
    "beautifulsoup4": {"soupsieve"},
}


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(GIT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} -> {r.stderr.strip()}")
    return r.stdout


GIT = Path(subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip())
PREFIJO = RAIZ.resolve().relative_to(GIT.resolve()).as_posix() + "/"


def viaja(ruta_git: str) -> bool:
    """¿Hay algún archivo versionado en esa ruta (archivo o carpeta)?"""
    return bool(_git("ls-files", "--", ruta_git).strip())


def eliminados_o_movidos() -> set[str]:
    """Rutas ORIGINALES (desde la raíz git) de lo que se borró (D) o movió (R) desde el punto de partida."""
    res: set[str] = set()
    for linea in _git("diff", "--name-status", "-M", TAG, "HEAD").splitlines():
        cols = linea.split("\t")
        if cols[0][:1] in ("D", "R"):
            res.add(cols[1])
    return res


def bajo_removido(ruta: str, removidos: set[str]) -> str | None:
    for r in removidos:
        if ruta == r or ruta.startswith(r.rstrip("/") + "/"):
            return r
    return None


# ── criterio 1 ───────────────────────────────────────────────────────────────────────────────
def bloque_yaml(texto: str, clave: str) -> str:
    """Las líneas indentadas que siguen a `clave:` en el nivel superior (sin parsear YAML)."""
    m = re.search(rf"^{clave}:[^\n]*\n((?:[ \t]+[^\n]*\n|\s*\n)*)", texto, re.M)
    return m.group(0).strip() if m else ""


def criterio_1(textos: dict[str, str]) -> dict:
    det = {}
    for w in WORKFLOWS:
        ruta = f".github/workflows/{w}.yml"
        diff = _git("diff", "--stat", TAG, "HEAD", "--", ruta).strip()
        t = textos[w]
        det[w] = {
            "diff_vs_punto_de_partida": diff or "(vacío)",
            "on": bloque_yaml(t, "on"),
            "permissions": bloque_yaml(t, "permissions"),
            "tiene_pull_request": bool(re.search(r"^\s*pull_request", t, re.M)),
        }
    ok = all(d["diff_vs_punto_de_partida"] == "(vacío)" and not d["tiene_pull_request"] for d in det.values())
    return {"ok": ok, "detalle": det}


# ── criterio 2 ───────────────────────────────────────────────────────────────────────────────
def rutas_de(texto: str) -> dict[str, set[str]]:
    """{ruta desde la raíz git: {rol}} de todo lo que el workflow nombra entre comillas."""
    rutas: dict[str, set[str]] = {}
    for m in re.finditer(r"""["'`](""" + re.escape(PREFIJO) + r"""[^"'`]*)["'`]""", texto):
        ruta = m.group(1).rstrip("/")
        linea = texto[texto.rfind("\n", 0, m.start()) + 1: texto.find("\n", m.end())]
        if linea.lstrip().startswith("#") or ruta == PREFIJO.rstrip("/"):    # comentario del .yml
            continue
        rol = set()
        if "git add" in linea:
            rol.add("commitea")
        if ruta.endswith(".py") and "python" in linea:
            rol.add("entrada")
        if "requirements" in ruta:
            rol.add("requirements")
        if not rol:
            rol.add("lee_o_cita")
        rutas.setdefault(ruta, set()).update(rol)
    # los avisos a humanos citan scripts con barras invertidas (`datos\\canonica\\src\\run_pipeline.py`)
    for m in re.finditer(r"""((?:datos|variables|modelo)(?:\\\\[\w.\-]+)+\.py)""", texto):
        rutas.setdefault(PREFIJO + m.group(1).replace("\\\\", "/"), set()).add("citada_en_aviso")
    return rutas


def criterio_2(textos: dict[str, str], removidos: set[str]) -> dict:
    det, ok = {}, True
    for w in WORKFLOWS:
        filas = []
        for ruta, roles in sorted(rutas_de(textos[w]).items()):
            existe = (GIT / ruta).exists()
            tracked = viaja(ruta) if existe else False
            quitado = bajo_removido(ruta, removidos)
            crea_el_script = "commitea" in roles and not existe
            falla = bool(quitado) or (not existe and not crea_el_script) or (existe and not tracked)
            ok &= not falla
            filas.append({"ruta": ruta, "roles": sorted(roles), "existe": existe, "viaja_por_git": tracked,
                          "eliminada_o_movida": quitado, "FALLA": falla})
        det[w] = filas
    return {"ok": ok, "detalle": det}


# ── criterio 3 y 4 ───────────────────────────────────────────────────────────────────────────
def importes(archivo: Path) -> tuple[list[tuple[str, int, bool]], bool]:
    """([(módulo de primer nivel, nivel relativo, dentro_de_try)], usa_importacion_dinamica)."""
    src = archivo.read_text(encoding="utf-8")
    arbol = ast.parse(src)
    en_try: set[int] = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Try):
            for s in n.body:
                en_try.update(id(x) for x in ast.walk(s))
    res = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            res += [(a.name.split(".")[0], 0, id(n) in en_try) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                res.append((n.module.split(".")[0], n.level, id(n) in en_try))
            else:                                    # `from . import x`
                res += [(a.name, n.level, id(n) in en_try) for a in n.names]
    dinamica = bool(re.search(r"importlib|__import__|runpy|\bexec\(", src))
    return res, dinamica


def clausura(entradas: list[str], py_versionados: dict[str, list[str]]) -> tuple[dict[str, list[str]], set, set, list]:
    """Recorre los imports locales. Devuelve ({archivo: [locales que importa]}, terceros, opcionales, dinámicos)."""
    vistos: dict[str, list[str]] = {}
    terceros: set[str] = set()
    opcionales: set[str] = set()
    dinamicos: list[str] = []
    pendientes = list(entradas)
    stdlib = set(sys.stdlib_module_names)
    while pendientes:
        rel = pendientes.pop()                       # ruta desde RAIZ, con /
        if rel in vistos:
            continue
        vistos[rel] = []
        lista, dinamica = importes(RAIZ / rel)
        if dinamica:
            dinamicos.append(rel)
        carpeta = Path(rel).parent.as_posix()
        for mod, nivel, opcional in lista:
            if mod in stdlib and nivel == 0:
                continue
            local = None
            if (RAIZ / carpeta / f"{mod}.py").is_file():
                local = f"{carpeta}/{mod}.py"
            elif (RAIZ / f"{mod}.py").is_file():
                local = f"{mod}.py"
            elif len(py_versionados.get(mod, [])) == 1:
                local = py_versionados[mod][0]
            if local:
                vistos[rel].append(local)
                pendientes.append(local)
            elif nivel == 0:
                (opcionales if opcional else terceros).add(mod)
    return vistos, terceros, opcionales, dinamicos


def instalado_por(texto: str) -> set[str]:
    """Nombres de import que deja disponibles el `pip install` del workflow."""
    dist: set[str] = set()
    for m in re.finditer(r"pip install ([^\n]+)", texto):
        arg = m.group(1).strip()
        r = re.match(r"-r\s+[\"']?([^\"']+)[\"']?", arg)
        if r:
            req = GIT / r.group(1)
            nombres = [re.split(r"[<>=!~\[ ;#]", l.strip())[0] for l in req.read_text(encoding="utf-8").splitlines()
                       if l.strip() and not l.strip().startswith("#")]
        else:
            nombres = arg.split()
        dist |= {n.lower().replace("_", "-") for n in nombres if n}
    prov: set[str] = set()
    for d in dist:
        prov.add(IMPORTA_COMO.get(d, d.replace("-", "_")))
        prov |= TRAE_CONSIGO.get(d, set())
    return prov


def criterio_3_y_4(textos: dict[str, str], removidos: set[str]) -> tuple[dict, dict]:
    py_versionados: dict[str, list[str]] = {}
    for l in _git("ls-files", "--", PREFIJO + "*.py").splitlines():
        rel = l[len(PREFIJO):]
        if "coordinacion/archivo/" not in rel:
            py_versionados.setdefault(Path(rel).stem, []).append(rel)

    det3, det4, ok3, ok4 = {}, {}, True, True
    nombres = sorted({Path(r).name for r in removidos})
    for w in WORKFLOWS:
        entradas = [r[len(PREFIJO):] for r, roles in rutas_de(textos[w]).items() if "entrada" in roles]
        # `vigilar_padron.py` importa a `ingesta_padron` y `bajar_nomina` desde una función: los sigue igual
        vistos, terceros, opcionales, dinamicos = clausura(entradas, py_versionados)
        faltan, quitados = [], []
        for rel, locales in vistos.items():
            for l in locales:
                if not (RAIZ / l).is_file():
                    faltan.append((rel, l))
            r = bajo_removido(PREFIJO + rel, removidos)
            if r:
                quitados.append(rel)
        prov = instalado_por(textos[w])
        sin_instalar = sorted(t for t in terceros if t not in prov)
        ok3 &= not faltan and not quitados and not sin_instalar
        # informativo (no es falla): archivos de la clausura que se editaron desde el punto de partida
        editados = [rel for rel in sorted(vistos) if _git("diff", "--name-only", TAG, "HEAD", "--", PREFIJO + rel).strip()]
        det3[w] = {"entradas": entradas, "clausura": sorted(vistos), "editados_desde_el_punto_de_partida": editados,
                   "faltan": faltan, "eliminados_en_la_clausura": quitados,
                   "terceros": sorted(terceros), "opcionales_en_try": sorted(opcionales), "terceros_sin_instalar": sin_instalar,
                   "importacion_dinamica_en": dinamicos}
        # criterio 4: texto
        hits = []
        for rel in sorted(vistos) + [f".github/workflows/{w}.yml"]:
            texto = textos[w] if rel.startswith(".github") else (RAIZ / rel).read_text(encoding="utf-8")
            for i, linea in enumerate(texto.splitlines(), 1):
                for n in nombres:
                    if n in linea:
                        hits.append({"archivo": rel, "linea": i, "nombre": n, "texto": linea.strip()[:160]})
        ok4 &= not hits
        det4[w] = hits
    return {"ok": ok3, "detalle": det3}, {"ok": ok4, "detalle": det4}


# ── criterio 5 ───────────────────────────────────────────────────────────────────────────────
def criterio_5(removidos: set[str]) -> dict:
    mapa = json.loads((RAIZ / ".mapa" / "mapa.json").read_text(encoding="utf-8"))
    inv = {d["ruta"]: d for d in mapa["inventario_datos"]}
    filas, ok = [], True
    for ruta in SALIDAS + INSUMOS_PADRON:
        g = PREFIJO + ruta
        existe, tracked = (GIT / g).exists(), viaja(g)
        d = inv.get(ruta)
        lectores = sorted(set(d["leen"]) | set(d["mencionan"])) if d else None
        escritores = sorted(d["escriben"]) if d else None
        faltan = [l for l in (lectores or []) + (escritores or []) if not (RAIZ / l).exists()]
        quitado = bajo_removido(g, removidos)
        falla = (not existe) or (not tracked) or bool(faltan) or bool(quitado)
        ok &= not falla
        filas.append({"ruta": ruta, "existe": existe, "viaja_por_git": tracked, "en_el_indice": d is not None,
                      "escriben": escritores, "leen_o_mencionan": lectores, "lectores_que_no_existen": faltan, "FALLA": falla})
    return {"ok": ok, "detalle": filas}


def main() -> int:
    textos = {w: (GIT / ".github" / "workflows" / f"{w}.yml").read_text(encoding="utf-8") for w in WORKFLOWS}
    removidos = eliminados_o_movidos()
    c1 = criterio_1(textos)
    c2 = criterio_2(textos, removidos)
    c3, c4 = criterio_3_y_4(textos, removidos)
    c5 = criterio_5(removidos)
    res = {"punto_de_partida": TAG, "head": _git("rev-parse", "--short", "HEAD").strip(),
           "eliminados_o_movidos_desde_el_punto_de_partida": len(removidos),
           "criterios": {"1_sin_cambios": c1, "2_rutas": c2, "3_imports": c3, "4_texto": c4, "5_insumos_y_lectores": c5}}
    if "--sin-json" not in sys.argv:
        SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
        SALIDA_JSON.write_bytes((json.dumps(res, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))

    print(f"HEAD {res['head']} contra {TAG}: {len(removidos)} archivos eliminados o movidos")
    for w in WORKFLOWS:
        d = c1["detalle"][w]
        print(f"\n[{w}] diff del .yml: {d['diff_vs_punto_de_partida']} | pull_request: {d['tiene_pull_request']}")
        print("   " + d["permissions"].replace("\n", "\n   "))
        for f in c2["detalle"][w]:
            marca = "FALLA" if f["FALLA"] else "ok   "
            print(f"   {marca} {'/'.join(f['roles']):22s} existe={f['existe']!s:5} git={f['viaja_por_git']!s:5} {f['ruta'][len(PREFIJO):]}")
        k = c3["detalle"][w]
        print(f"   clausura de imports: {len(k['clausura'])} archivos {k['clausura']}")
        print(f"   terceros: {k['terceros']} | opcionales (try): {k['opcionales_en_try']} | sin instalar: {k['terceros_sin_instalar']}"
              f" | dinámicos: {k['importacion_dinamica_en']}")
        print(f"   faltan: {k['faltan']} | eliminados en la clausura: {k['eliminados_en_la_clausura']}"
              f" | editados desde el punto de partida: {k['editados_desde_el_punto_de_partida']}")
        for h in c4["detalle"][w]:
            print(f"   TEXTO {h['archivo']}:{h['linea']} nombra «{h['nombre']}»: {h['texto']}")
    print("\n[insumos y lectores]")
    for f in c5["detalle"]:
        print(f"   {'FALLA' if f['FALLA'] else 'ok   '} existe={f['existe']!s:5} git={f['viaja_por_git']!s:5} "
              f"escriben={len(f['escriben'] or [])} leen={len(f['leen_o_mencionan'] or [])} {f['ruta']}"
              + (f"  LECTORES QUE NO EXISTEN: {f['lectores_que_no_existen']}" if f["lectores_que_no_existen"] else ""))
    print()
    for nombre, c in res["criterios"].items():
        print(f"criterio {nombre}: {'OK' if c['ok'] else 'FALLA'}")
    return 0 if all(c["ok"] for c in res["criterios"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
