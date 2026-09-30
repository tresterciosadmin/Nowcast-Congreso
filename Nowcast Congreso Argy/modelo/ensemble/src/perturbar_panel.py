# -*- coding: utf-8 -*-
"""Cuáles parámetros MUEVEN el número: `afecta_panel` del registro (auditoría 2026-09, ítem B1, etapa 2).

Definición del §5.3 (`coordinacion/AUDITORIA-2026-09/05-consolidacion-y-anclaje.md`): *Afecta* = cambiar un
parámetro por su alternativa mueve algún P_i o P_aprob del panel de regresión en más de 1e-9. Acá se mide con el
MOTOR REAL: un proceso por perturbación, que importa `nowcast_puertas` con el literal del parámetro reescrito en el
AST (o con la variable de entorno puesta) y corre `nowcast()` sobre el panel; se compara TODA la salida (la
probabilidad, los pasos, el tablero de las dos cámaras y la postura de cada legislador) contra la corrida base.

EL PANEL (3 casos, con los defaults de `nowcast()`: `n_sims = 2000`, `seed = 0`)
    P1  Diputados, 2026-06-01, origen EJECUTIVO, hipotético (el panel de regresión: `panel_regresion.json`)
    P2  lo mismo con `proyecto_id = HCDN279791` (ejercita las puertas A y C y β)
    P3  Senado, 2019-06-01, origen OPOSICION, hipotético (otra cámara de origen y OTRA ERA: con el gobierno
        vigente el guard de era no se ve)

LA ALTERNATIVA DE CADA PARÁMETRO (fijada en el pre-registro, `ESTADO-EJECUCION.md`, «B1 — pre-registro»)
    bandera o booleano -> el opuesto · número x -> {2x, x/2} (enteros con //; si 0 < x <= 1 el doble se acota a 1
    y se descarta si iguala a x; si x = 0, la alternativa es 1 o 0,1) · categóricos de entorno -> una lista a mano.
    Contenedores, textos y fechas NO se perturban (`no perturbable`). Los parámetros de módulos que no se cargan en
    el panel quedan `afecta = false, motivo = módulo no cargado`.

UMBRAL: `afecta` = `max|Δ| > 1e-9` en algún campo numérico (o cambia un texto o la estructura) de algún caso con
alguna alternativa. Un proceso que falla se guarda como error, no como «no afecta».

LÍMITES (quedan escritos en el registro): (1) `afecta = false` dice «no mueve estos 3 casos», no «no afecta
nunca»: un umbral que el panel no cruza o una rama de otro proyecto no se ven. (2) Se perturba de a UN parámetro:
no se ven las interacciones (p. ej. `COMBINAR_TEMAS` sólo importa con `TEMA_AUTO` prendido). (3) Un parámetro
que el llamador siempre pisa (un default de función que `nowcast()` siempre pasa explícito) sale `false` y es
correcto: el default está muerto.

CONTROLES POSITIVOS (escritos antes de correr; si alguno sale al revés la medición está mal y NO se guarda):
la corrida base de P1 reproduce `panel_regresion.json` campo por campo; afectan `TAU` y `TAU_DEFAULT`, `EPSILON0` y
`EPSILON0_DEFAULT`, `nowcast(n_sims)`; `GUARD_ERA` afecta en P3 y no en P1 ni P2; los defaults que `nowcast()`
pisa siempre (`simular_con_guardas(epsilon0)`, `p_voto_revisora(epsilon0)`) no afectan.

    python modelo/ensemble/src/perturbar_panel.py --medir [--procesos 6] [--cache ruta.jsonl]   # ≈ 20 min
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.abc
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import registro_parametros as R  # noqa: E402

CASOS = {
    "P1": dict(camara_origen="diputados", fecha="2026-06-01", origen="EJECUTIVO"),
    "P2": dict(camara_origen="diputados", fecha="2026-06-01", proyecto_id="HCDN279791", origen="EJECUTIVO"),
    "P3": dict(camara_origen="senado", fecha="2019-06-01", origen="OPOSICION"),
}
UMBRAL = 1e-9
ALTERNATIVAS_ENTORNO = {"COMBINAR_TEMAS": ["union"]}
PANEL_REGRESION = AQUI.parent / "outputs" / "panel_regresion.json"
_FALTA = object()


# ═══════════════════════════════════════════════════════════════ las alternativas
def alternativas(x):
    """Las alternativas de un valor numérico o booleano (la regla del pre-registro). [] si no se perturba."""
    if isinstance(x, bool):
        return [not x]
    if isinstance(x, int):
        return [1] if x == 0 else [a for a in dict.fromkeys([x * 2, x // 2]) if a != x]
    if isinstance(x, float):
        if x == 0.0:
            return [0.1]
        a = [2 * x, x / 2]
        if 0 < x <= 1:
            a[0] = min(2 * x, 1.0)
        return [v for v in dict.fromkeys(a) if v != x]
    return []


def plan_de(p: dict, cargados: set[str]):
    """(alternativas, motivo): qué se prueba de este parámetro, o por qué no."""
    if p["archivo"] not in cargados:
        return [], "no se perturba: módulo no cargado en el panel"
    d = p["default"]
    if p["clase"] == "entorno":
        if p["entorno"] in ALTERNATIVAS_ENTORNO:
            return list(ALTERNATIVAS_ENTORNO[p["entorno"]]), None
        if not p["evaluable"] or d is None:
            return [], "no perturbable: sin default evaluable (una ruta, una clave o no hay default)"
        if isinstance(d, str):
            return [], "no perturbable: texto"
    elif p["clase"] == "constante" and not isinstance(d, (bool, int, float)):
        return [], "no perturbable: texto, fecha o contenedor (estructural)"
    alts = alternativas(d)
    return (alts, None) if alts else ([], "no perturbable: sin alternativa numérica")


# ════════════════════════════════════════════ el proceso que corre UNA perturbación
class _Cargador(importlib.abc.Loader):
    def __init__(self, ruta: str, reescribir):
        self.ruta, self.reescribir = ruta, reescribir

    def create_module(self, spec):
        return None

    def exec_module(self, modulo):
        arbol = self.reescribir(Path(self.ruta).read_text(encoding="utf-8"))
        exec(compile(arbol, self.ruta, "exec"), modulo.__dict__)  # noqa: S102 — el módulo del repo, con un literal cambiado


class _Buscador(importlib.abc.MetaPathFinder):
    def __init__(self, nombre: str, ruta: str, reescribir):
        self.nombre, self.ruta, self.reescribir = nombre, ruta, reescribir

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self.nombre:
            return None
        return importlib.util.spec_from_file_location(
            fullname, self.ruta, loader=_Cargador(self.ruta, self.reescribir))


def _reescritor(p: dict, alt):
    """Función texto -> AST con el literal del parámetro `p` cambiado por `alt`. Falla si no lo encuentra."""
    def reescribir(fuente: str) -> ast.Module:
        arbol = ast.parse(fuente)
        hecho = False
        if p["clase"] == "constante":
            for s in arbol.body:
                if (isinstance(s, (ast.Assign, ast.AnnAssign)) and s.lineno == p["linea"]
                        and s.value is not None):
                    s.value = ast.Constant(value=alt)
                    hecho = True
        elif p["clase"] == "default_funcion":
            for n in ast.walk(arbol):
                if isinstance(n, ast.FunctionDef) and n.lineno == p["linea"]:
                    a = n.args
                    pos = a.posonlyargs + a.args
                    k0 = len(pos) - len(a.defaults)
                    for i, arg in enumerate(pos):
                        if arg.arg == p["nombre"] and i >= k0:
                            a.defaults[i - k0] = ast.Constant(value=alt)
                            hecho = True
                    for i, arg in enumerate(a.kwonlyargs):
                        if arg.arg == p["nombre"] and a.kw_defaults[i] is not None:
                            a.kw_defaults[i] = ast.Constant(value=alt)
                            hecho = True
        if not hecho:
            raise RuntimeError(f"no encontré el literal de {p['id']} (línea {p['linea']}) para reescribirlo")
        return ast.fix_missing_locations(arbol)
    return reescribir


def _a_entorno(alt) -> str:
    """La variable de entorno que representa la alternativa: los booleanos son «1»/«0»."""
    if isinstance(alt, bool):
        return "1" if alt else "0"
    return str(alt)


def _hojas(x, ruta="", salida=None) -> dict:
    """Todas las hojas de la salida, `ruta -> valor`."""
    salida = {} if salida is None else salida
    if isinstance(x, dict):
        for k, v in x.items():
            _hojas(v, f"{ruta}/{k}", salida)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _hojas(v, f"{ruta}[{i}]", salida)
    else:
        salida[ruta] = x
    return salida


def _trabajar(spec: dict, salida: Path) -> None:
    """El proceso hijo: aplica la perturbación, corre `nowcast()` sobre el caso y guarda las hojas."""
    caso = CASOS[spec["caso"]]
    pert = spec.get("perturbacion")
    if pert:
        if pert["clase"] == "entorno":
            os.environ[pert["entorno"]] = _a_entorno(pert["alt"])
        else:
            ruta = str(RAIZ / pert["archivo"])
            nombre = Path(pert["archivo"]).stem
            sys.modules.pop(nombre, None)           # `rutas` ya lo importó este mismo script
            sys.meta_path.insert(0, _Buscador(nombre, ruta, _reescritor(pert, pert["alt"])))
    import logging
    logging.disable(logging.CRITICAL)
    import nowcast_puertas as NP
    t0 = time.time()
    res = json.loads(json.dumps(NP.nowcast(**caso)))
    raiz = str(RAIZ.resolve()).lower()
    modulos = sorted({Path(m.__file__).resolve().relative_to(RAIZ.resolve()).as_posix()
                      for m in list(sys.modules.values())
                      if getattr(m, "__file__", None) and str(Path(m.__file__).resolve()).lower().startswith(raiz)
                      and "tests" not in Path(m.__file__).parts})
    salida.write_text(json.dumps({"p_aprobacion": res.get("p_aprobacion"), "hojas": _hojas(res),
                                  "modulos": modulos, "segundos": round(time.time() - t0, 1)}), encoding="utf-8")


# ══════════════════════════════════════════════════════════════ la comparación
def comparar(base: dict, otra: dict) -> dict:
    """max|Δ| sobre las hojas numéricas, cuántas hojas no numéricas difieren y cuántas faltan en un lado."""
    max_dif, no_num, estructura = 0.0, 0, 0
    for k in set(base) | set(otra):
        a, b = base.get(k, _FALTA), otra.get(k, _FALTA)
        if a is _FALTA or b is _FALTA:
            estructura += 1
        elif (isinstance(a, (int, float)) and isinstance(b, (int, float))
              and not isinstance(a, bool) and not isinstance(b, bool)):
            if a != b and not (a != a and b != b):                # NaN contra NaN es igual
                max_dif = max(max_dif, abs(a - b) if (a == a and b == b) else float("inf"))
        elif a != b:
            no_num += 1
    return {"max_abs_dif": max_dif, "no_numericos": no_num, "estructura": estructura,
            "afecta": bool(max_dif > UMBRAL or no_num or estructura)}


# ═════════════════════════════════════════════════════════════ el orquestador
def _correr(spec: dict, variables: set[str], tmp: Path, etiqueta: str) -> dict:
    """Lanza el proceso hijo y devuelve sus hojas, o {'error': ...}."""
    archivo_spec, archivo_out = tmp / f"{etiqueta}.spec.json", tmp / f"{etiqueta}.out.json"
    archivo_spec.write_text(json.dumps(spec), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in variables}
    env["PYTHONUTF8"] = "1"
    try:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--trabajar", str(archivo_spec),
                            "--salida", str(archivo_out)], capture_output=True, text=True, env=env, timeout=1800)
    except subprocess.TimeoutExpired:
        return {"error": "timeout de 30 minutos"}
    if r.returncode != 0 or not archivo_out.is_file():
        cola = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
        return {"error": f"código {r.returncode}: " + " | ".join(cola)[:400]}
    return json.loads(archivo_out.read_text(encoding="utf-8"))


def _sha_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
                              timeout=30).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def medir(procesos: int, cache: Path | None, limite: int | None = None,
          ids: list[str] | None = None) -> int:
    t_inicio = time.time()
    guardado = R.leer_guardado()
    fuentes = R.cargar_fuentes()
    registro = R.generar(fuentes=fuentes, previo=guardado)
    variables = {p["entorno"] for p in registro["parametros"] if p["entorno"]}
    sha = R.sha_fuentes(fuentes)
    sha_total = hashlib.sha256(json.dumps(sha, sort_keys=True).encode()).hexdigest()
    hechos: dict[str, dict] = {}
    candado = threading.Lock()
    if cache and cache.is_file():
        for linea in cache.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                x = json.loads(linea)
                if x.get("fuentes") == sha_total:
                    hechos[x["clave"]] = x["resultado"]
    print(f"registro: {len(registro['parametros'])} parámetros; en cache {len(hechos)} corridas")

    with tempfile.TemporaryDirectory(prefix="perturbar_") as tmp_:
        tmp = Path(tmp_)

        def lanzar(clave: str, spec: dict) -> dict:
            if clave in hechos:
                return hechos[clave]
            res = _correr(spec, variables, tmp, clave.replace("|", "_").replace("/", "_").replace(":", "_")[:120])
            hechos[clave] = res
            if cache:
                with cache.open("a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({"clave": clave, "fuentes": sha_total, "resultado": res}) + "\n")
            return res

        # 1. la corrida base de cada caso (y los módulos que quedan cargados)
        print("corridas base…")
        with ThreadPoolExecutor(max_workers=min(procesos, len(CASOS))) as ex:
            futuros = {c: ex.submit(lanzar, f"base|{c}", {"caso": c, "perturbacion": None}) for c in CASOS}
            bases = {c: f.result() for c, f in futuros.items()}
        for c, b in bases.items():
            if "error" in b:
                print(f"  la base de {c} falló: {b['error']}")
                return 1
        todos = set().union(*[set(b["modulos"]) for b in bases.values()])
        cargados = todos & set(registro["clausura"])
        ajenos = sorted(todos - set(registro["clausura"]) - {"modelo/ensemble/src/perturbar_panel.py",
                                                              "modelo/ensemble/src/registro_parametros.py"})
        print(f"  módulos cargados en el panel: {len(cargados)} de {len(registro['clausura'])} de la clausura"
              + (f" (cargados y FUERA de la clausura: {ajenos})" if ajenos else "")
              + "; p_aprobacion base: " + ", ".join(f"{c} {b['p_aprobacion']}" for c, b in bases.items()))

        # 2. las perturbaciones
        trabajos, plan = [], {}
        for p in registro["parametros"]:
            alts, motivo = plan_de(p, cargados)
            if ids and not any(i in p["id"] for i in ids):
                alts, motivo = [], "fuera de --ids"
            plan[p["id"]] = (alts, motivo)
            for alt in alts:
                for c in CASOS:
                    trabajos.append((p, alt, c))
        if limite:
            trabajos = trabajos[:limite]
        print(f"{len(trabajos)} corridas de perturbación ({sum(1 for a, _ in plan.values() if a)} parámetros)…")
        resultados: dict[tuple, dict] = {}
        with ThreadPoolExecutor(max_workers=procesos) as ex:
            futuros = {}
            for p, alt, c in trabajos:
                spec = {"caso": c, "perturbacion": {k: p[k] for k in ("id", "clase", "archivo", "nombre", "linea",
                                                                        "entorno")} | {"alt": alt}}
                futuros[ex.submit(lanzar, f"{p['id']}|{alt!r}|{c}", spec)] = (p["id"], alt, c)
            for i, f in enumerate(as_completed(futuros), 1):
                resultados[futuros[f]] = f.result()
                if i % 25 == 0 or i == len(futuros):
                    print(f"  {i}/{len(futuros)}  ({(time.time() - t_inicio) / 60:.1f} min)")

    # 3. se agrega por parámetro
    for p in registro["parametros"]:
        alts, motivo = plan[p["id"]]
        if not alts:
            p["afecta_panel"] = {"afecta": False if "no cargado" in motivo else None, "motivo": motivo}
            continue
        por_caso = {c: {"afecta": False, "max_abs_dif": 0.0, "alt_que_mueve": None, "no_numericos": 0,
                        "estructura": 0, "error": None} for c in CASOS}
        errores, mueve_p = [], False
        for alt in alts:
            for c in CASOS:
                r = resultados.get((p["id"], alt, c))
                if r is None:
                    continue
                if "error" in r:
                    errores.append(f"{c} con {alt!r}: {r['error']}")
                    por_caso[c]["error"] = r["error"]
                    continue
                if (r["p_aprobacion"] is not None and bases[c]["p_aprobacion"] is not None
                        and abs(r["p_aprobacion"] - bases[c]["p_aprobacion"]) > UMBRAL):
                    mueve_p = True
                cmp = comparar(bases[c]["hojas"], r["hojas"])
                if cmp["max_abs_dif"] >= por_caso[c]["max_abs_dif"] and cmp["afecta"]:
                    por_caso[c].update(afecta=True, alt_que_mueve=alt, max_abs_dif=cmp["max_abs_dif"],
                                       no_numericos=cmp["no_numericos"], estructura=cmp["estructura"])
        afecta = any(v["afecta"] for v in por_caso.values())
        p["afecta_panel"] = {
            "afecta": True if afecta else (None if errores else False),
            "afecta_p_aprobacion": mueve_p,
            "max_abs_dif": max(v["max_abs_dif"] for v in por_caso.values()),
            "alternativas": alts, "por_caso": por_caso}
        if errores:
            p["afecta_panel"]["errores"] = errores

    # 4. los controles positivos: si alguno sale al revés, la medición está mal y no se guarda
    def get(pid: str) -> dict:
        return next(p["afecta_panel"] for p in registro["parametros"] if p["id"] == pid)
    nowcast_py = "modelo/ensemble/src/nowcast_puertas.py"
    panel = json.loads(PANEL_REGRESION.read_text(encoding="utf-8"))
    controles = [{"control": "la base de P1 reproduce panel_regresion.json campo por campo",
                  "esperado": True, "observado": not comparar(_hojas(panel), bases["P1"]["hojas"])["afecta"]}]
    for pid, esp in [(f"{nowcast_py}::ENV:TAU", True), (f"{nowcast_py}::TAU_DEFAULT", True),
                     (f"{nowcast_py}::ENV:EPSILON0", True), (f"{nowcast_py}::EPSILON0_DEFAULT", True),
                     (f"{nowcast_py}::nowcast(n_sims)", True),
                     ("modelo/ensemble/src/ensemble.py::simular_con_guardas(epsilon0)", False),
                     ("modelo/ensemble/src/puerta_d.py::p_voto_revisora(epsilon0)", False)]:
        controles.append({"control": f"{pid} afecta", "esperado": esp, "observado": get(pid)["afecta"]})
    g = get(f"{nowcast_py}::ENV:GUARD_ERA")["por_caso"]
    for c, esp in (("P1", False), ("P2", False), ("P3", True)):
        controles.append({"control": f"GUARD_ERA afecta en {c}", "esperado": esp, "observado": g[c]["afecta"]})
    for c in controles:
        c["ok"] = c["esperado"] == c["observado"]
        print(f"  control {'OK ' if c['ok'] else 'MAL'} {c['control']}: esperado {c['esperado']} · observado {c['observado']}")
    if not all(c["ok"] for c in controles):
        print("\nALGÚN CONTROL SALIÓ AL REVÉS: la medición está mal y NO se guarda hasta entenderlo.")
        return 1
    if ids:
        print("\n--ids: prueba parcial, NO se guarda. Los parámetros medidos:")
        for p in registro["parametros"]:
            a = p["afecta_panel"]
            if plan[p["id"]][0]:
                print(f"  {p['id']}: afecta={a['afecta']} max|Δ|={a['max_abs_dif']:.3g} "
                      + " ".join(f"{c}={v['afecta']}" for c, v in a["por_caso"].items()))
        return 0
    if limite:
        print("\n--limite: prueba parcial, NO se guarda.")
        return 0

    n_afecta = sum(1 for p in registro["parametros"] if p["afecta_panel"]["afecta"] is True)
    registro["medicion_afecta_panel"] = {
        "fecha": date.today().isoformat(), "git_head": _sha_head(), "fuentes_sha256": sha,
        "python": sys.version.split()[0], "comando": "python modelo/ensemble/src/perturbar_panel.py --medir",
        "casos": CASOS, "umbral": UMBRAL,
        "p_aprobacion_base": {c: b["p_aprobacion"] for c, b in bases.items()},
        "modulos_cargados": sorted(cargados), "n_corridas": len(hechos),
        "estado_de_las_puertas": {c: {"A": b["hojas"].get("/pasos[0]/estado"), "via_B": b["hojas"].get("/pasos[1]/via"),
                                      "C": b["hojas"].get("/pasos[2]/estado"), "via_D": b["hojas"].get("/pasos[3]/via")}
                                  for c, b in bases.items()},
        "controles": controles,
        "resumen": {"afecta": n_afecta,
                    "no_afecta": sum(1 for p in registro["parametros"] if p["afecta_panel"]["afecta"] is False),
                    "sin_medir": sum(1 for p in registro["parametros"] if p["afecta_panel"]["afecta"] is None)},
        "limite": ("`afecta = false` dice «no mueve estos 3 casos» (n_sims 2000, seed 0), no «no afecta nunca». "
                   "(1) Se perturba de a UN parámetro: no se ven las interacciones (`COMBINAR_TEMAS` sólo importa con "
                   "`TEMA_AUTO`; `p_voto_revisora(delta)` queda anulado mientras `factor_encogimiento` sea 0, y hoy "
                   "`nowcast()` no lo pasa: el gancho de δ no está conectado). (2) El panel no ejercita el estado "
                   "`sin_dictamen` de las puertas A y C (ver `estado_de_las_puertas`): lo que sólo actúa ahí, como la "
                   "vía `SOBRE_TABLAS`, sale `false` sin que se haya probado. (3) Los defaults que nowcast() pisa "
                   "siempre salen `false` y es correcto: están muertos. (4) `max_abs_dif` es el máximo sobre CUALQUIER "
                   "campo numérico de la salida (incluye conteos de legisladores), no sólo probabilidades; "
                   "`afecta_p_aprobacion` dice si movió la probabilidad final."),
    }
    R.escribir(registro)
    print(f"\nguardado en {R.REGISTRO.relative_to(RAIZ).as_posix()}: {registro['medicion_afecta_panel']['resumen']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--medir", action="store_true", help="mide afecta_panel y lo guarda en el registro")
    ap.add_argument("--procesos", type=int, default=6)
    ap.add_argument("--cache", type=Path, default=None, help="JSONL para reanudar (se invalida si cambia el código)")
    ap.add_argument("--limite", type=int, default=None, help="sólo las primeras N corridas (prueba)")
    ap.add_argument("--ids", nargs="+", default=None,
                    help="sólo los parámetros cuyo id contiene alguno de estos textos (prueba: no guarda)")
    ap.add_argument("--trabajar", type=Path, help="(interno) el proceso hijo")
    ap.add_argument("--salida", type=Path, help="(interno) donde el hijo escribe")
    args = ap.parse_args(argv)
    if args.trabajar:
        _trabajar(json.loads(args.trabajar.read_text(encoding="utf-8")), args.salida)
        return 0
    if args.medir:
        return medir(args.procesos, args.cache, args.limite, args.ids)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
