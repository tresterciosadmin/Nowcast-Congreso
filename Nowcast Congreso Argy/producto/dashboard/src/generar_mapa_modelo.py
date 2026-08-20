# -*- coding: utf-8 -*-
"""producto/dashboard - generador de los datos de MAPA-MODELO.html.

QUE HACE
    Arma el grafo de "como se calcula P(sancion)" fusionando DOS capas, igual que
    el resto del repo separa diseno de datos:

      1. MECANICA  - se lee del repo, no se escribe a mano:
         `.mapa/mapa.json` (LOC, simbolos con linea, entrypoints, hosts externos),
         `rutas.py` (los 52 artefactos que cruzan entre modulos) y el
         `**Estado:**` / `**Owner actual:**` de cada `README.md` de modulo.

      2. CURADA    - `producto/dashboard/data/mapa_modelo_semantica.json`, a mano:
         que calcula cada script EN CASTELLANO, que significa cada parquet, la
         formula de cada etapa, y que puertas estan parqueadas y por que. Nada de
         esto lo puede saber un escaner.

    Salida: `mapa_modelo_datos.js` en la raiz del proyecto, que lee
    `MAPA-MODELO.html`. **El HTML es diseno fijo y no se edita a mano**, mismo
    patron que `TABLERO-CONTROL.html` + `tablero_datos.js`.

POR QUE ASI
    El modo de falla documentado de este proyecto es la copia que envejece: un
    numero o un estado escrito a mano en un archivo que nadie vuelve a mirar. Si
    los datos del mapa vivieran dentro del HTML, en tres meses el mapa miente.
    Aca el estado y el dueno de cada pieza salen del README que ya se mantiene, y
    la existencia de cada archivo se verifica contra el disco EN CADA CORRIDA.

EL CONTROL QUE IMPORTA
    Si un nodo curado declara un `archivo` que no existe, o una `ruta_declarada`
    que no esta en `rutas.py`, el generador **FALLA** y no escribe nada. Un mapa
    que apunta a un archivo que se movio es peor que no tener mapa.

USO
    python producto/dashboard/src/generar_mapa_modelo.py
    python producto/dashboard/src/generar_mapa_modelo.py --verificar   # no escribe
    python producto/dashboard/src/generar_mapa_modelo.py --salida otro.js

    En la PowerShell de Valle:
    python "producto\\dashboard\\src\\generar_mapa_modelo.py"
    (tiene que imprimir "OK  96 nodos - 130 aristas" y 0 problemas)

4 directivas: errores especificos, backoff (n/a: I/O local), parsing defensivo,
logging estructurado.

Modulo: producto/dashboard - creado 2026-08-20.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("generar_mapa_modelo")

# Los mismos seis estados que usa tablero_datos.js. Cualquier otra cosa es un typo.
# Orden logico (de terminado a inexistente), no alfabetico: asi se lee la leyenda.
ESTADOS_ORDEN = ["HECHO", "EN CURSO", "PARCIAL", "PENDIENTE", "FUTURO", "REPLANTEADO"]

# De que lado del dibujo bicameral cae un nodo. Solo se declara en la punta de
# cada cadena; de los de mas arriba se ocupa el HTML, por alcance -- y los que
# alimentan a las DOS camaras se dibujan de los dos lados.
BLOQUES_VALIDOS = {"origen", "revisora", "final", "fuera"}
ESTADOS_VALIDOS = set(ESTADOS_ORDEN)

# `**Estado:** ...` y `**Owner actual:** ...` en el README de cada modulo.
_RE_ESTADO = re.compile(r"^\*\*Estado:\*\*\s*(.+?)\s*$", re.MULTILINE)
_RE_OWNER = re.compile(r"^\*\*Owner actual:\*\*\s*(.+?)\s*$", re.MULTILINE)
# Algunos README traen el owner pegado a la linea de estado: `... · **Owner:** Valle (fecha)`
_RE_OWNER_INLINE = re.compile(r"\*\*Owner:\*\*\s*([^·|]+?)\s*$", re.MULTILINE)


class ErrorDeMapa(RuntimeError):
    """El mapa no se puede generar sin mentir. Se corta antes de escribir."""


# --------------------------------------------------------------------------- #
# Ubicacion del repo                                                           #
# --------------------------------------------------------------------------- #
def raiz_proyecto() -> Path:
    """La raiz es la primera carpeta hacia arriba que tenga `rutas.py`.

    No lleva `parents[N]`: asi el script sigue funcionando si cambia de
    profundidad, que es justo lo que rompia antes (ver la cabecera de rutas.py).
    """
    for d in Path(__file__).resolve().parents:
        if (d / "rutas.py").is_file():
            return d
    raise ErrorDeMapa(
        "no encontre `rutas.py` hacia arriba desde "
        f"{Path(__file__).resolve()}: no se donde esta la raiz del proyecto"
    )


# --------------------------------------------------------------------------- #
# Capa mecanica                                                                #
# --------------------------------------------------------------------------- #
def cargar_indice(raiz: Path) -> dict:
    """`.mapa/mapa.json`: el indice generado por `.mapa/indexar.py`."""
    p = raiz / ".mapa" / "mapa.json"
    if not p.is_file():
        raise ErrorDeMapa(
            f"falta {p}. Corre `python .mapa/indexar.py .` desde la raiz del proyecto."
        )
    try:
        with p.open(encoding="utf-8") as fh:
            indice = json.load(fh)
    except json.JSONDecodeError as e:
        raise ErrorDeMapa(f"{p} no es JSON valido: {e}") from e

    archivos = indice.get("archivos")
    if not isinstance(archivos, list):
        raise ErrorDeMapa(f"{p} no trae la lista `archivos` (indice viejo o corrupto)")
    logger.info("indice: %s archivos, indexado %s",
                len(archivos), indice.get("indexado", "?"))
    return indice


def por_archivo(indice: dict) -> dict[str, dict]:
    """{ruta relativa -> ficha del archivo} para no recorrer la lista 96 veces."""
    salida: dict[str, dict] = {}
    for a in indice.get("archivos", []):
        ruta = a.get("ruta")
        if isinstance(ruta, str):
            salida[ruta.replace("\\", "/")] = a
    return salida


def cargar_rutas(raiz: Path) -> dict[str, Path]:
    """Importa `rutas.py` y devuelve su `inventario()`: {NOMBRE: Path}.

    Se importa en vez de parsearlo a mano a proposito: si manana `rutas.py`
    agrega una constante, el mapa la ve sola.
    """
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    try:
        import rutas  # type: ignore
    except ImportError as e:
        raise ErrorDeMapa(f"no pude importar `rutas.py` desde {raiz}: {e}") from e
    try:
        inventario = rutas.inventario()
    except AttributeError as e:
        raise ErrorDeMapa(
            "`rutas.py` no expone `inventario()`. Lo usa este generador y "
            "tambien `tests/test_rutas.py`."
        ) from e
    logger.info("rutas.py: %s rutas declaradas", len(inventario))
    return inventario


def _limpiar_owner(txt: str) -> str:
    """`_(vacante - reclamalo en ...)_` -> `vacante`. Deja el resto tal cual."""
    t = txt.strip()
    if t.startswith("_(") or t.startswith("_"):
        t = t.strip("_").strip()
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1]
        # "vacante - reclamalo en coordinacion/TABLERO.md antes de empezar"
        t = re.split(r"\s+[-—]\s+", t, maxsplit=1)[0]
        t = re.split(r"\s*—\s*", t, maxsplit=1)[0]
    return t.strip() or "—"


def _estado_canonico(txt: str) -> str:
    """De la linea libre del README saca uno de los seis estados validos.

    Los README escriben cosas como `EN CURSO - v1 en produccion. **1.016.632...`.
    Se busca el estado como prefijo; si no matchea ninguno se devuelve "" y el
    llamador decide (no se inventa un estado).
    """
    t = txt.strip().upper()
    # El mas largo primero para que "EN CURSO" gane sobre un futuro "EN".
    for e in sorted(ESTADOS_VALIDOS, key=len, reverse=True):
        if t.startswith(e):
            return e
    for e in sorted(ESTADOS_VALIDOS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(e) + r"\b", t):
            return e
    return ""


def modulo_de(raiz: Path, ruta_rel: str) -> str:
    """Modulo dueno de un archivo: el ancestro mas cercano que tenga README.md.

    Asi un parquet de salida hereda el estado y el dueno del modulo que lo
    produce, sin tener que escribirlo a mano en la capa curada (que es
    exactamente el tipo de copia que despues envejece).
    """
    p = Path(ruta_rel.replace("\\", "/"))
    for padre in list(p.parents):
        if str(padre) in (".", ""):
            break
        if (raiz / padre / "README.md").is_file():
            return str(padre).replace("\\", "/")
    return ""


def leer_readmes(raiz: Path, modulos: set[str]) -> dict[str, dict]:
    """{modulo -> {estado, estado_texto, owner}} leido de su README.md.

    Parsing defensivo: un modulo sin README, o con README sin las lineas, no
    rompe el mapa — queda con estado desconocido y se reporta como problema.
    """
    salida: dict[str, dict] = {}
    for mod in sorted(modulos):
        p = raiz / mod / "README.md"
        if not p.is_file():
            salida[mod] = {"estado": "", "estado_texto": "", "owner": "—",
                           "problema": f"no tiene README.md ({mod}/README.md)"}
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            salida[mod] = {"estado": "", "estado_texto": "", "owner": "—",
                           "problema": f"no pude leer {mod}/README.md: {e}"}
            continue

        m_est = _RE_ESTADO.search(txt)
        estado_texto = m_est.group(1).strip() if m_est else ""
        estado = _estado_canonico(estado_texto)

        m_own = _RE_OWNER.search(txt)
        if m_own:
            owner = _limpiar_owner(m_own.group(1))
        else:
            m_own2 = _RE_OWNER_INLINE.search(txt)
            owner = _limpiar_owner(m_own2.group(1)) if m_own2 else "—"

        ficha = {"estado": estado, "estado_texto": estado_texto, "owner": owner}
        if not estado_texto:
            ficha["problema"] = (
                f"{mod}/README.md no tiene la linea `**Estado:**` "
                "(la usa este mapa y la usa el router de MAPA.md)")
        elif not estado:
            ficha["problema"] = (
                f"{mod}/README.md dice Estado: '{estado_texto[:40]}...', que no "
                f"empieza por ninguno de {sorted(ESTADOS_VALIDOS)}")
        salida[mod] = ficha
    return salida


# --------------------------------------------------------------------------- #
# Capa curada                                                                  #
# --------------------------------------------------------------------------- #
def cargar_semantica(raiz: Path) -> dict:
    p = raiz / "producto" / "dashboard" / "data" / "mapa_modelo_semantica.json"
    if not p.is_file():
        raise ErrorDeMapa(f"falta la capa curada: {p}")
    try:
        with p.open(encoding="utf-8") as fh:
            sem = json.load(fh)
    except json.JSONDecodeError as e:
        raise ErrorDeMapa(f"{p} no es JSON valido: {e}") from e

    for clave in ("nodos", "aristas", "etapas", "roles", "tipos_arista"):
        if not isinstance(sem.get(clave), list):
            raise ErrorDeMapa(f"{p} no trae la lista `{clave}`")
    return sem


# --------------------------------------------------------------------------- #
# Fusion                                                                       #
# --------------------------------------------------------------------------- #
def _validar_caminos(sem: dict, conocidos: set[str]) -> list[dict]:
    """Los `caminos` son recorridos guiados: «seguí con el dedo de la fuente al numero».

    Un camino que nombra un nodo inexistente es un boton que no hace nada, asi
    que se corta aca y no en el navegador.
    """
    caminos = sem.get("caminos", []) or []
    for c in caminos:
        faltan = [n for n in c.get("nodos", []) if n not in conocidos]
        if faltan:
            raise ErrorDeMapa(
                f"el camino '{c.get('id')}' nombra nodos que no existen: {faltan}")
    return caminos



def fusionar(raiz: Path, sem: dict, indice: dict, rutas_dec: dict[str, Path]) -> tuple[dict, list[str]]:
    """Devuelve (datos_del_grafo, problemas). No escribe nada."""
    problemas: list[str] = []
    fichas = por_archivo(indice)
    entrypoints = {e.replace("\\", "/") for e in indice.get("entrypoints", [])}

    ids = [n["id"] for n in sem["nodos"]]
    if len(ids) != len(set(ids)):
        vistos, dup = set(), set()
        for i in ids:
            (dup if i in vistos else vistos).add(i)
        raise ErrorDeMapa(f"ids de nodo duplicados en la capa curada: {sorted(dup)}")
    conocidos = set(ids)

    etapas_validas = {e["id"] for e in sem["etapas"]}
    roles_validos = {r["id"] for r in sem["roles"]}
    tipos_validos = {t["id"] for t in sem["tipos_arista"]}
    grupos_validos = {g["id"] for g in sem.get("grupos", []) or []}

    nodos = []
    for n in sem["nodos"]:
        nodo = dict(n)

        if nodo["etapa"] not in etapas_validas:
            raise ErrorDeMapa(f"nodo {nodo['id']}: etapa desconocida '{nodo['etapa']}'")
        if nodo["rol"] not in roles_validos:
            raise ErrorDeMapa(f"nodo {nodo['id']}: rol desconocido '{nodo['rol']}'")
        if nodo.get("bloque") and nodo["bloque"] not in BLOQUES_VALIDOS:
            raise ErrorDeMapa(
                f"nodo {nodo['id']}: bloque '{nodo['bloque']}' desconocido "
                f"(validos: {sorted(BLOQUES_VALIDOS)})")
        if nodo.get("grupo") and nodo["grupo"] not in grupos_validos:
            raise ErrorDeMapa(
                f"nodo {nodo['id']}: grupo '{nodo['grupo']}' no esta declarado en `grupos`")

        # --- archivo del repo -------------------------------------------------
        arch = nodo.get("archivo") or nodo.get("archivo_dato")
        if arch:
            nodo["archivo"] = arch
            p = raiz / arch
            nodo["existe"] = p.is_file()
            if not nodo["existe"]:
                # Un output que todavia no se corrio no es un error; un SCRIPT que
                # no existe si lo es: significa que el mapa apunta al vacio.
                if nodo.get("archivo"):
                    raise ErrorDeMapa(
                        f"nodo {nodo['id']} declara `{arch}` y ese archivo NO existe "
                        f"en disco ({p}). O se movio, o el mapa esta mintiendo."
                    )
                problemas.append(
                    f"{nodo['id']}: `{arch}` no existe todavia (output sin correr)")
            ficha = fichas.get(arch.replace("\\", "/"))
            if ficha:
                nodo["loc"] = ficha.get("loc")
                simbolos = ficha.get("simbolos") or []
                nodo["simbolos"] = [
                    {"nombre": s.get("nombre"), "tipo": s.get("tipo"),
                     "linea": s.get("linea"), "doc": s.get("doc")}
                    for s in simbolos[:6] if isinstance(s, dict)
                ]
                nodo["lenguaje"] = ficha.get("lenguaje")
            nodo["entrypoint"] = arch.replace("\\", "/") in entrypoints

        # Archivos que viven en la RAIZ GIT (un nivel arriba): no se pueden
        # verificar desde aca y NO se inventan como existentes. Ver CLAUDE.md.
        if nodo.get("archivo_externo"):
            nodo["existe"] = None
            nodo["fuera_del_arbol"] = True

        # --- ruta declarada en rutas.py ---------------------------------------
        rd = nodo.get("ruta_declarada")
        if rd:
            if rd not in rutas_dec:
                raise ErrorDeMapa(
                    f"nodo {nodo['id']} declara la ruta `{rd}`, que NO esta en "
                    "`rutas.py`. Toda ruta que cruza entre modulos va declarada ahi "
                    "(regla 1 de rutas.py)."
                )
            destino = rutas_dec[rd]
            if nodo.get("archivo_dato"):
                destino = raiz / nodo["archivo_dato"]
            try:
                nodo["archivo"] = str(destino.relative_to(raiz)).replace("\\", "/")
            except ValueError:
                nodo["archivo"] = str(destino)
            nodo["existe"] = destino.exists()
            if not nodo["existe"]:
                problemas.append(
                    f"{nodo['id']}: {rd} -> {nodo['archivo']} no existe todavia "
                    "(es generado, puede no haberse corrido)")

        # --- de que modulo es -------------------------------------------------
        # Si la capa curada no lo dice, se deduce del path: el ancestro mas
        # cercano con README.md. Un parquet hereda el estado de quien lo produce.
        if not nodo.get("modulo"):
            ref = nodo.get("archivo") or nodo.get("archivo_externo") or ""
            if ref and not nodo.get("fuera_del_arbol"):
                inferido = modulo_de(raiz, ref)
                if inferido:
                    nodo["modulo"] = inferido
                    nodo["modulo_inferido"] = True

        if nodo.get("es_hueco"):
            nodo["parqueada"] = True

        nodos.append(nodo)

    # --- estado y dueno: recien aca, con todos los modulos ya conocidos -------
    modulos = {n["modulo"] for n in nodos if n.get("modulo")}
    readmes = leer_readmes(raiz, modulos)
    for f in readmes.values():
        if f.get("problema"):
            problemas.append(f["problema"])

    for nodo in nodos:
        mod = nodo.get("modulo")
        if nodo.get("estado_declarado"):
            # REGLA (2026-08-20). Por defecto el estado de un nodo es el de su
            # modulo. Un nodo puede declarar el suyo -- las Puertas A y C estan
            # SUSPENDIDAS aunque `modelo/ensemble` este EN CURSO -- pero entonces
            # tiene que decir POR QUE, y el mapa muestra de donde salio cada
            # estado. Lo que no puede pasar es que el mapa afirme en silencio un
            # estado que su fuente declarada contradice.
            declarado = _estado_canonico(nodo["estado_declarado"])
            if not declarado:
                raise ErrorDeMapa(
                    f"nodo {nodo['id']}: `estado_declarado` = "
                    f"'{nodo['estado_declarado']}' no es uno de {ESTADOS_ORDEN}")
            if not str(nodo.get("estado_motivo", "")).strip():
                raise ErrorDeMapa(
                    f"nodo {nodo['id']}: declara su propio estado "
                    f"('{declarado}') pero no dice por que. `estado_motivo` es "
                    "obligatorio: un estado a mano sin motivo es la copia que "
                    "envejece.")
            nodo["estado"] = declarado
            nodo["estado_fuente"] = "capa curada"
            nodo["owner"] = readmes.get(mod, {}).get("owner", "—") if mod else "—"
            nodo["estado_texto"] = nodo["estado_motivo"]
            nodo["estado_modulo"] = readmes.get(mod, {}).get("estado", "") if mod else ""
        elif mod and mod in readmes and readmes[mod]["estado"]:
            nodo["estado"] = readmes[mod]["estado"]
            nodo["estado_texto"] = readmes[mod]["estado_texto"]
            nodo["estado_fuente"] = f"{mod}/README.md"
            nodo["owner"] = readmes[mod]["owner"]
        elif nodo["rol"] == "fuente":
            nodo["estado"] = "HECHO"
            nodo["owner"] = "externo"
            nodo["estado_fuente"] = "—"
            nodo["estado_texto"] = "fuente externa: no la controlamos"
        elif mod and mod in readmes:
            # Hay modulo pero su README no declara estado: se dice asi, no se
            # inventa. El problema ya quedo listado arriba.
            nodo["estado"] = ""
            nodo["owner"] = readmes[mod]["owner"]
            nodo["estado_texto"] = "su README no declara `**Estado:**`"
        else:
            nodo["estado"] = ""
            nodo["owner"] = "—"
            nodo["estado_texto"] = ""
            problemas.append(f"{nodo['id']}: sin modulo ni estado (nodo huerfano)")

    # --- aristas -------------------------------------------------------------
    aristas = []
    for a in sem["aristas"]:
        if a["de"] not in conocidos or a["a"] not in conocidos:
            raise ErrorDeMapa(
                f"arista {a['de']} -> {a['a']}: uno de los dos nodos no existe")
        if a["tipo"] not in tipos_validos:
            raise ErrorDeMapa(f"arista {a['de']} -> {a['a']}: tipo '{a['tipo']}' desconocido")
        aristas.append(dict(a))

    # Un nodo suelto casi siempre es un olvido, no una decision.
    tocados = {x for a in aristas for x in (a["de"], a["a"])}
    for i in sorted(conocidos - tocados):
        problemas.append(f"{i}: nodo sin ninguna arista (isla)")

    datos = {
        "meta": {
            **sem.get("meta", {}),
            "generado": indice.get("indexado", ""),
            "indice_archivos": len(indice.get("archivos", [])),
            "rutas_declaradas": len(rutas_dec),
            "nodos": len(nodos),
            "aristas": len(aristas),
            "problemas": problemas,
        },
        "etapas": sem["etapas"],
        "grupos": sem.get("grupos", []) or [],
        "roles": sem["roles"],
        "tipos_arista": sem["tipos_arista"],
        "formulaciones": sem.get("formulaciones", []),
        "caminos": _validar_caminos(sem, conocidos),
        "trampas": sem.get("trampas", []),
        "estados": ESTADOS_ORDEN,
        "nodes": nodos,
        "links": aristas,
    }
    return datos, problemas


# --------------------------------------------------------------------------- #
# Escritura                                                                    #
# --------------------------------------------------------------------------- #
CABECERA = """// =====================================================================
// MAPA DEL MODELO - DATOS (GENERADO, no se edita a mano)
// =====================================================================
// Lo escribe: producto/dashboard/src/generar_mapa_modelo.py
// Lo lee:     MAPA-MODELO.html (el diseno, tambien fijo)
//
// Para cambiar QUE dice un nodo -> producto/dashboard/data/mapa_modelo_semantica.json
// Para cambiar el estado o el dueno de un modulo -> el `**Estado:**` /
//   `**Owner actual:**` de su README.md (de ahi sale por defecto).
// Un nodo puede declarar SU estado con `estado_declarado` + `estado_motivo`
//   (obligatorio) en la capa curada: el mapa dice cual de los dos esta mostrando.
// Despues: python producto/dashboard/src/generar_mapa_modelo.py
// =====================================================================
"""


def escribir(datos: dict, salida: Path) -> None:
    cuerpo = json.dumps(datos, ensure_ascii=False, indent=2)
    texto = CABECERA + "\nconst MAPA_MODELO = " + cuerpo + ";\n"
    salida.parent.mkdir(parents=True, exist_ok=True)
    # CRLF: es lo que tiene el resto del arbol en Windows (`* text=auto` en
    # .gitattributes normaliza a LF dentro de git). newline="" evita la doble
    # conversion en Windows.
    with salida.open("w", encoding="utf-8", newline="") as fh:
        fh.write(texto.replace("\n", "\r\n"))
    logger.info("escrito %s (%s bytes)", salida, salida.stat().st_size)


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=None,
                    help="ruta del .js (default: <raiz>/mapa_modelo_datos.js)")
    ap.add_argument("--verificar", action="store_true",
                    help="valida todo y reporta, pero NO escribe")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s")

    try:
        raiz = raiz_proyecto()
        logger.info("raiz del proyecto: %s", raiz)
        indice = cargar_indice(raiz)
        rutas_dec = cargar_rutas(raiz)
        sem = cargar_semantica(raiz)
        datos, problemas = fusionar(raiz, sem, indice, rutas_dec)
    except ErrorDeMapa as e:
        logger.error("NO se genero nada. %s", e)
        return 2

    for p in problemas:
        logger.warning("%s", p)

    if args.verificar:
        print(f"OK  {len(datos['nodes'])} nodos - {len(datos['links'])} aristas "
              f"- {len(problemas)} problemas (no se escribio nada)")
        return 0

    salida = Path(args.salida) if args.salida else raiz / "mapa_modelo_datos.js"
    try:
        escribir(datos, salida)
    except OSError as e:
        logger.error("no pude escribir %s: %s", salida, e)
        return 3

    print(f"OK  {len(datos['nodes'])} nodos - {len(datos['links'])} aristas "
          f"- {len(problemas)} problemas")
    print(f"    -> {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
