"""datos/padron/src/vigilar_padron.py — EL PADRÓN VIVO (idea de Franco, URGENTE 2).

**Por qué existe.** Los expedientes y las votaciones ya entran solos (el bot
diario). La COMPOSICIÓN de la cámara, no: dependía de que alguien se acordara de
mirarla. Ese es exactamente el tipo de olvido que costó nueve meses de votaciones
sin cargar y un proyector que devolvía 383 bancas sobre 257.

Las bancas cambian todo el año — renuncias, licencias, fallecimientos, reemplazos
y pases entre bloques (que son señal política en sí misma). Este vigilante corre
periódicamente (semanal), baja la nómina, la compara contra el padrón versionado
y AVISA:

  • altas      — asumió alguien que no estaba
  • bajas      — cesantías, renuncias, fallecimientos
  • pases      — cambios de bloque (señal política, no ruido administrativo)
  • total ≠ 257 / 72 — la alarma más barata que tenemos

**Idempotente por diseño.** El estado va a `data/estado_vigilancia.json` con la
huella del último diff: si nada cambió respecto de la corrida anterior, no vuelve
a avisar (sin novedades = sin commit, sin issue, sin ruido). Mismo patrón que
`votaciones.py` y `dae_senado.py`.

**Códigos de salida** (los usa el workflow para decidir si abre un issue):
    0  sin novedades
   10  hay novedades (altas/bajas/pases) — revisar y regenerar el padrón
   20  ALARMA DURA (total de bancas fuera de rango, o fuente caída)

Uso:
    python datos/padron/src/vigilar_padron.py                    # ambas cámaras
    python datos/padron/src/vigilar_padron.py --camara diputados
    python datos/padron/src/vigilar_padron.py --nomina x.csv --camara diputados
    python datos/padron/src/vigilar_padron.py --dry-run          # no escribe estado

FUENTES Y SUS LÍMITES (heredado de bajar_nomina.py / README del módulo):
  • DIPUTADOS — `api.argentinadatos.com/v1/diputados/diputados`: automatizable.
    Trae `periodoBloque` por bloque, así que un pase genera una fila nueva.
  • SENADO — la API NO da el bloque parlamentario (da la alianza por la que
    ingresó, que no es lo mismo: Atauche entra por el P. Renovador Federal y
    bloquea en LLA). El bloque del Senado sale del export oficial `.xls`, que hoy
    se baja a mano a `data/raw/nomina_senado.csv`. Mientras no haya fuente
    automática, el vigilante NO se calla: mide la ANTIGÜEDAD de ese archivo y
    avisa cuando pasa de `--dias-rancio` (default 45). Un padrón viejo que nadie
    mira es peor que un padrón que se queja.

4 directivas: errores específicos, backoff (heredado de bajar_nomina), parsing
defensivo (columnas por nombre, tolerante a NA), logging estructurado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger("padron.vigilante")

_HERE = Path(__file__).resolve()
DATA = _HERE.parents[1] / "data"
OUT = _HERE.parents[1] / "outputs"
ESTADO = DATA / "estado_vigilancia.json"

# Bancas que DEBE tener cada cámara. Es la alarma más barata del proyecto:
# cualquier desvío significa tramos solapados, un recambio mal cargado o una
# fuente que cambió de contrato.
BANCAS = {"diputados": 257, "senado": 72}
# Tolerancia: una banca vacante es real y transitoria (hoy falta Matzkin y
# Pitrola viene con el tramo roto). Más de eso ya no es vacancia, es un bug.
TOLERANCIA = 2
DIAS_RANCIO = 45


# --------------------------------------------------------------------------- #
# Carga de las dos puntas de la comparación                                     #
# --------------------------------------------------------------------------- #
def _vigentes(df: pd.DataFrame, fecha: str, col_d="desde", col_h="hasta") -> pd.DataFrame:
    """Filas con desde <= F <= hasta. Parsing defensivo: las fechas ilegibles
    quedan afuera (y se cuentan aparte, no se inventan)."""
    d = pd.to_datetime(df[col_d], errors="coerce")
    h = pd.to_datetime(df[col_h], errors="coerce")
    f = pd.Timestamp(fecha)
    return df[(d <= f) & (h >= f)].copy()


def padron_versionado(camara: str, fecha: str) -> pd.DataFrame:
    """El contrato que hoy consume el modelo: data/padron_<camara>.csv."""
    p = DATA / f"padron_{camara}.csv"
    if not p.exists():
        raise FileNotFoundError(
            f"no existe {p}. Corré antes: python datos/padron/src/ingesta_padron.py {camara}")
    df = pd.read_csv(p, encoding="utf-8-sig")
    falta = {"clave", "legislador", "bloque_norm", "desde", "hasta"} - set(df.columns)
    if falta:
        raise ValueError(f"{p.name} sin columnas {sorted(falta)} — contrato roto")
    return _vigentes(df, fecha)


def nomina_fresca(camara: str, ruta: Path | None, fecha: str) -> tuple[pd.DataFrame, str]:
    """Snapshot ACTUAL de la cámara, normalizado igual que el padrón.

    Devuelve (df_vigentes, origen). `origen` documenta de dónde salió el dato,
    porque no todas las cámaras se bajan igual (ver docstring del módulo).
    """
    sys.path.insert(0, str(_HERE.parent))
    from ingesta_padron import cargar_nomina, construir_padron  # noqa: E402

    if ruta is None and camara == "diputados":
        # camino automático: la API
        from bajar_nomina import nomina_diputados  # noqa: E402
        cruda = nomina_diputados()
        tmp = DATA / "raw" / "_nomina_diputados_fresca.csv"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        cruda.to_csv(tmp, index=False, encoding="utf-8")
        ruta, origen = tmp, "api:argentinadatos"
    elif ruta is None:
        # SENADO sin fuente automática: se usa el raw versionado y se mide su edad
        ruta = DATA / "raw" / f"nomina_{camara}.csv"
        if not ruta.exists():
            raise FileNotFoundError(
                f"no existe {ruta} y {camara} no tiene bajador automático "
                "(ver FUENTES Y SUS LÍMITES en el docstring)")
        origen = "archivo:raw_versionado"
    else:
        origen = f"archivo:{Path(ruta).name}"

    df = construir_padron(cargar_nomina(Path(ruta)), camara, origen)
    return _vigentes(df, fecha), origen


# --------------------------------------------------------------------------- #
# El diff                                                                       #
# --------------------------------------------------------------------------- #
def comparar(viejo: pd.DataFrame, nuevo: pd.DataFrame) -> dict:
    """Altas, bajas y pases entre el padrón versionado y el snapshot fresco.

    La identidad es `clave` (name_key de entity_resolution), no el nombre crudo:
    la fuente escribe 'Recalde, Héctor Pedro' y el padrón 'Recalde, Héctor', y
    ese detalle ya nos costó 314 proyectos ignorados una vez.
    """
    def idx(d):
        if d.empty:
            return {}
        return {str(r.clave): {"legislador": str(r.legislador),
                               "bloque": str(getattr(r, "bloque_norm", "")),
                               "linaje": str(getattr(r, "bloque_linaje", "")),
                               "distrito": str(getattr(r, "distrito", ""))}
                for r in d.itertuples()}

    a, b = idx(viejo), idx(nuevo)
    altas = [{"clave": k, **b[k]} for k in b if k not in a]
    bajas = [{"clave": k, **a[k]} for k in a if k not in b]

    # UN PASE ES UN CAMBIO DE LINAJE, no un cambio de string (fix 2026-08-04).
    # La primera corrida reportó como "pase" a Del Plá, que había pasado de
    # "...FRENTE DE IZQUIERDA Y DE TRABAJADORES-U" a "...-UNIDAD": el mismo
    # bloque, truncado distinto por la fuente. Avisar de eso como si fuera una
    # ruptura política es exactamente el error que ya nos costó caro dos veces
    # (los 123 asesores, la falsa jefa con 610 proyectos). El linaje es la capa
    # canónica de entity_resolution y no se mueve por un cambio de tipeo; el
    # string crudo se reporta aparte, como lo que es: mantenimiento de la fuente.
    comunes = [k for k in b if k in a]
    pases = [{"clave": k, "legislador": b[k]["legislador"],
              "de": a[k]["linaje"], "a": b[k]["linaje"],
              "bloque_de": a[k]["bloque"], "bloque_a": b[k]["bloque"]}
             for k in comunes if a[k]["linaje"] != b[k]["linaje"]]
    reetiquetados = [{"clave": k, "legislador": b[k]["legislador"],
                      "de": a[k]["bloque"], "a": b[k]["bloque"]}
                     for k in comunes
                     if a[k]["linaje"] == b[k]["linaje"] and a[k]["bloque"] != b[k]["bloque"]]
    return {"altas": sorted(altas, key=lambda x: x["legislador"]),
            "bajas": sorted(bajas, key=lambda x: x["legislador"]),
            "pases": sorted(pases, key=lambda x: x["legislador"]),
            "reetiquetados": sorted(reetiquetados, key=lambda x: x["legislador"])}


def huella(diff: dict) -> str:
    """Hash estable del diff: si no cambió, no se vuelve a avisar."""
    return hashlib.sha256(
        json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def _hash_archivo(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def edad_contenido(p: Path, previo: dict) -> tuple[int | None, str | None]:
    """Días desde que el CONTENIDO del archivo cambió por última vez.

    NO se usa mtime: en GitHub Actions el checkout reescribe todos los archivos,
    así que el mtime siempre diría "0 días" y la alarma de padrón rancio nunca
    saltaría — justo en el único lugar donde importa que salte. Se compara el
    hash del contenido contra el que quedó guardado en el estado (que sí viaja
    versionado) y se cuenta desde la primera vez que se vio ese hash.
    """
    h = _hash_archivo(p)
    if h is None:
        return None, None
    visto = previo.get("hash_raw")
    desde = previo.get("hash_visto_desde")
    if visto != h or not desde:
        return 0, h            # contenido nuevo: la cuenta arranca hoy
    try:
        d0 = datetime.fromisoformat(desde)
    except ValueError:
        return 0, h
    if d0.tzinfo is None:
        d0 = d0.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - d0).days), h


# --------------------------------------------------------------------------- #
# Chequeo por cámara                                                            #
# --------------------------------------------------------------------------- #
def vigilar(camara: str, fecha: str, ruta: Path | None,
            dias_rancio: int = DIAS_RANCIO, previo: dict | None = None) -> dict:
    previo = previo or {}
    r = {"camara": camara, "fecha": fecha, "alarmas": [], "novedades": False}
    try:
        nuevo, origen = nomina_fresca(camara, ruta, fecha)
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        # fuente caída = alarma dura: el silencio es el peor resultado posible
        r["alarmas"].append({"nivel": "DURA", "que": "fuente_inaccesible",
                             "detalle": f"{type(e).__name__}: {e}"})
        return r
    viejo = padron_versionado(camara, fecha)
    r["origen"] = origen
    r["n_padron"] = len(viejo)
    r["n_nomina"] = len(nuevo)
    r["esperado"] = BANCAS.get(camara)

    d = comparar(viejo, nuevo)
    r.update(d)
    r["huella"] = huella(d)
    # un re-etiquetado NO es novedad: no despierta a nadie un fin de semana
    r["novedades"] = bool(d["altas"] or d["bajas"] or d["pases"])

    # --- alarma 1: el total de bancas ---
    esp = BANCAS.get(camara)
    if esp and abs(len(nuevo) - esp) > TOLERANCIA:
        r["alarmas"].append({
            "nivel": "DURA", "que": "total_de_bancas",
            "detalle": f"{len(nuevo)} bancas vigentes, se esperaban {esp} "
                       f"(tolerancia ±{TOLERANCIA}). Revisar tramos solapados "
                       f"antes de usar el padrón: cualquier P(mayoría) sale mal."})
    elif esp and len(nuevo) != esp:
        r["alarmas"].append({
            "nivel": "AVISO", "que": "banca_vacante",
            "detalle": f"{len(nuevo)}/{esp} — dentro de tolerancia (vacante transitoria)."})

    # --- alarma 2: padrón rancio (el caso del Senado) ---
    if origen == "archivo:raw_versionado":
        dias, h = edad_contenido(DATA / "raw" / f"nomina_{camara}.csv", previo)
        r["hash_raw"] = h
        if dias is not None and dias > dias_rancio:
            r["alarmas"].append({
                "nivel": "AVISO", "que": "padron_rancio",
                "detalle": f"nomina_{camara}.csv tiene {dias} días y esta cámara no "
                           f"tiene bajador automático. Volver a exportarla a mano."})
        r["edad_dias"] = dias

    # --- alarma 3: composición por bloque (para leer el pase en contexto) ---
    if not nuevo.empty and "bloque_linaje" in nuevo.columns:
        r["composicion"] = nuevo["bloque_linaje"].value_counts().to_dict()
    return r


# --------------------------------------------------------------------------- #
# Reporte                                                                       #
# --------------------------------------------------------------------------- #
def a_markdown(reportes: list[dict]) -> str:
    L = [f"# Padrón vivo — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ""]
    duras = [a for r in reportes for a in r["alarmas"] if a["nivel"] == "DURA"]
    novedades = any(r.get("novedades") for r in reportes)
    if duras:
        L += ["## 🔴 ALARMA", ""]
    elif novedades:
        L += ["## 🟡 Hay novedades en la composición", ""]
    else:
        L += ["## 🟢 Sin novedades", "", "La composición de ambas cámaras coincide "
              "con el padrón versionado.", ""]

    for r in reportes:
        cam = r["camara"].upper()
        L.append(f"### {cam}")
        if any(a["que"] == "fuente_inaccesible" for a in r["alarmas"]):
            L += ["", f"**No pude leer la fuente.** "
                  f"{r['alarmas'][0]['detalle']}", ""]
            continue
        L.append(f"- Bancas vigentes: **{r['n_nomina']}** (esperadas {r['esperado']}) "
                 f"· padrón versionado: {r['n_padron']} · fuente: `{r.get('origen')}`")
        for a in r["alarmas"]:
            icono = "🔴" if a["nivel"] == "DURA" else "🟡"
            L.append(f"- {icono} **{a['que']}** — {a['detalle']}")
        for etiqueta, campo in (("Altas", "altas"), ("Bajas", "bajas")):
            if r.get(campo):
                L += ["", f"**{etiqueta} ({len(r[campo])})**", ""]
                L += [f"  - {x['legislador']} — {x.get('bloque','')} ({x.get('distrito','')})"
                      for x in r[campo]]
        if r.get("pases"):
            L += ["", f"**Cambios de bloque ({len(r['pases'])})** — señal política, "
                  "no ruido administrativo", ""]
            L += [f"  - {x['legislador']}: {x['de']} → {x['a']}" for x in r["pases"]]
        if r.get("reetiquetados"):
            L += ["", f"_Re-etiquetados por la fuente ({len(r['reetiquetados'])}) — "
                  "mismo linaje, distinto texto. NO es un pase; se informa para "
                  "detectar cambios de contrato de la fuente._", ""]
            L += [f"  - {x['legislador']}: `{x['de']}` → `{x['a']}`"
                  for x in r["reetiquetados"]]
        if r.get("composicion"):
            L += ["", "**Composición por linaje**", ""]
            L += [f"  - {k}: {v}" for k, v in sorted(
                r["composicion"].items(), key=lambda kv: -kv[1])]
        L.append("")
    if novedades or duras:
        L += ["---", "", "**Qué hacer.** Regenerar el padrón y volver a correr lo que "
              "depende de él:", "", "```bash",
              "python datos/padron/src/bajar_nomina.py diputados --padron",
              "python datos/padron/src/ingesta_padron.py senado", "```", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser(description="Padrón vivo: vigila altas, bajas y pases.")
    ap.add_argument("--camara", choices=["diputados", "senado", "ambas"], default="ambas")
    ap.add_argument("--nomina", type=Path, default=None,
                    help="CSV de nómina a usar en vez de la fuente (tests/offline)")
    ap.add_argument("--fecha", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--dias-rancio", type=int, default=DIAS_RANCIO)
    ap.add_argument("--dry-run", action="store_true", help="no escribe estado ni reporte")
    a = ap.parse_args(argv)

    # el estado se lee ANTES: la antigüedad del raw se mide contra él
    previo = {}
    if ESTADO.exists():
        try:
            previo = json.loads(ESTADO.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("estado ilegible (%s): lo trato como primera corrida", e)

    camaras = ["diputados", "senado"] if a.camara == "ambas" else [a.camara]
    reportes = [vigilar(c, a.fecha, a.nomina, a.dias_rancio, previo.get(c, {}))
                for c in camaras]

    nuevas = [r for r in reportes
              if r.get("novedades") and previo.get(r["camara"], {}).get("huella") != r.get("huella")]

    md = a_markdown(reportes)
    print(md)
    if not a.dry_run:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "vigilancia_padron.md").write_text(md, encoding="utf-8")
        ahora = datetime.now(timezone.utc).isoformat()
        estado = {}
        for r in reportes:
            cam = r["camara"]; ant = previo.get(cam, {})
            h = r.get("hash_raw")
            estado[cam] = {
                "huella": r.get("huella"), "n": r.get("n_nomina"),
                "ultima_corrida": ahora,
                "hash_raw": h,
                # si el contenido no cambió, se conserva la fecha en que se vio primero
                "hash_visto_desde": (ant.get("hash_visto_desde")
                                     if h and ant.get("hash_raw") == h else ahora),
            }
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    duras = [a_ for r in reportes for a_ in r["alarmas"] if a_["nivel"] == "DURA"]
    if duras:
        logger.error("%d alarma(s) dura(s)", len(duras))
        return 20
    if nuevas:
        logger.warning("novedades nuevas en: %s", [r["camara"] for r in nuevas])
        return 10
    logger.info("sin novedades")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
