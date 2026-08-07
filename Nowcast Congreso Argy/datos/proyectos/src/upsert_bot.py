"""Bot -> proyectos.db (ADR-0009, etapa 2: LA ENTREGA QUE FALTABA).

El bot recolecta desde marzo y ningun modulo leia sus parquet. Esto los carga.

⚠️ POR QUE ESTO NO ES `upsert_proyecto()` A SECAS
`store.upsert_proyecto()` REEMPLAZA las tablas hijas completas en cada llamada.
Correrlo con la ficha del bot sobre un proyecto que ya vino de CKAN **borraria su
tramite** (el bot no lo trae). Y al reves, CKAN borraria los cofirmantes. Se
pierden datos en cualquier orden, sin error: la base queda cargada con la mitad
de lo que cree tener. Por eso esto es un MERGE con precedencia POR CAMPO:

    firmantes, giros          -> gana el BOT   (cofirmantes completos; giro
                                                MEDIDO al ingresar)
    tramite, hitos            -> gana CKAN     (el bot es una foto del dia 0)
    sumario, fecha, camara    -> gana CKAN, con el bot de respaldo
    taxonomias                -> nadie las toca (las escribe el agente)

`store.py` no se modifica: su semantica de reemplazo es correcta para lo suyo.

Uso:
    python datos/proyectos/src/upsert_bot.py            # carga
    python datos/proyectos/src/upsert_bot.py --dry-run  # dice que haria
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cuarentena import Cuarentena  # noqa: E402  (necesita el sys.path de arriba)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("upsert_bot")

RAIZ = Path(__file__).resolve().parents[3]
BOT = RAIZ / "datos" / "bot_recoleccion" / "data" / "clean"
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"
DB = RAIZ / "datos" / "proyectos" / "data" / "proyectos.db"

# 'DE LEY' -> 'LEY'; el sufijo del expediente del Senado -> lo mismo.
TIPO_TP = {"DE LEY": "LEY", "DE RESOLUCIÓN": "RESOLUCION", "DE RESOLUCION": "RESOLUCION",
           "DE DECLARACIÓN": "DECLARACION", "DE DECLARACION": "DECLARACION"}
TIPO_DAE = {"PL": "LEY", "PD": "DECLARACION", "PC": "COMUNICACION", "PR": "RESOLUCION",
            "DC": "MENSAJE"}  # DC = del Ejecutivo (mensaje/decreto)


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return " ".join(s.split())


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def catalogo_comisiones() -> list[str]:
    """Nombres conocidos, del mas largo al mas corto (criterio de Franco).

    El orden importa: 'LEGISLACION GENERAL' tiene que consumirse antes que
    'LEGISLACION', o una comision larga se partiria en dos.
    """
    p = CLEAN / "expedientes_giros.parquet"
    if not p.exists():
        logger.warning("sin catalogo de comisiones: los giros del TP no se parsean")
        return []
    g = pd.read_parquet(p)
    return sorted({_norm(c) for c in g["comision"].dropna().unique()},
                  key=len, reverse=True)


def separar_giros_tp(texto, cat: list[str]) -> list[str]:
    """El campo `giros` del TP viene SIN separadores. Devuelve la lista.

    Es el mismo matcheo que `giros_iniciales.contar_en_texto()` de Franco, pero
    devolviendo los nombres y en el orden en que aparecen en el texto. Un primer
    intento de partir por espacios dio 10x de error (ver ESTADO 07-08).
    """
    t = _norm(texto)
    if not t or not cat:
        return []
    hallados: list[tuple[int, str]] = []
    for c in cat:
        if c and c in t:
            hallados.append((t.index(c), c))
            t = t.replace(c, " " * len(c))  # consumir sin correr las posiciones
    return [c for _, c in sorted(hallados)]


def separar_giros_dae(texto) -> list[str]:
    """El DAE si trae separador: 'DE MINERIA... - DE PRESUPUESTO Y HACIENDA -'."""
    if not texto or pd.isna(texto):
        return []
    partes = [p.strip(" -") for p in str(texto).split(" - ")]
    out = []
    for p in partes:
        p = _norm(p)
        if p.startswith("DE "):
            p = p[3:]
        if p:
            out.append(p)
    return out


def denom_dae(exp) -> str | None:
    """'S-2/26-PL' -> '0002-S-2026'; 'PE-8/26-PL' -> '0008-PE-2026'.

    El DAE **si** trae el codigo de origen en el prefijo, asi que no hay que
    adivinarlo: 'S' = senador, 'PE' = Poder Ejecutivo, 'CD' = Camara de Diputados.
    Es el mismo formato que usa CKAN (`0095-PE-2026` existe en la base).

    ⚠️ Un primer intento matcheaba solo `^S-` y descartaba **34 expedientes, todos
    del EJECUTIVO** — que son los de mayor valor predictivo del modelo (el PE
    convierte ~77% contra 1,4% del resto). Se habrian perdido en silencio: el log
    solo decia "formato inesperado". Los del Ejecutivo NO son un caso borde.
    """
    m = re.match(r"^([A-Z]{1,3})-(\d+)/(\d{2})-[A-Z]{2}$", str(exp).strip())
    if not m:
        return None
    origen, n, yy = m.groups()
    return f"{int(n):04d}-{origen}-20{yy}"


def fichas_tp(cat: list[str]) -> dict[str, dict]:
    p = BOT / "tp_entradas.parquet"
    if not p.exists():
        logger.warning("no esta %s", p.name)
        return {}
    tp = pd.read_parquet(p).dropna(subset=["expediente"])
    cua = Cuarentena("tp_diputados")
    fichas, crudas = {}, {}
    for r in tp.itertuples(index=False):
        firm = [f.strip() for f in str(r.firmantes or "").split(";") if f.strip()]
        crudas[str(r.expediente).strip()] = r._asdict()
        fichas[str(r.expediente).strip()] = {
            "camara": "diputados",
            "sumario": r.sumario,
            "fecha_ingreso": str(r.fecha)[:10] if pd.notna(r.fecha) else None,
            "tipo": TIPO_TP.get(_norm(r.tipo), _norm(r.tipo) or None),  # ver control abajo
            "pdf_url": r.pdf_url,
            "firmantes": firm,
            "giros": separar_giros_tp(r.giros, cat),
        }
    # Un proyecto sin `tipo` seria invisible para la cohorte de LEY: no entra a la
    # base general, va a cuarentena con su fila entera para poder recuperarlo.
    sin_tipo = [d for d, f in fichas.items() if not f["tipo"]]
    for d in sin_tipo:
        cua.apartar("tipo no reconocido (no entraria a la cohorte de LEY)",
                    d, crudas.get(d, {"expediente": d}))
        del fichas[d]
    cua.controlar_tasa(len(tp))
    cua.guardar()
    logger.info("TP  (Diputados): %d fichas", len(fichas))
    return fichas


def fichas_dae() -> dict[str, dict]:
    p = BOT / "dae_entradas.parquet"
    if not p.exists():
        logger.warning("no esta %s", p.name)
        return {}
    dae = pd.read_parquet(p).dropna(subset=["expediente"])
    cua = Cuarentena("dae_senado")
    fichas = {}
    for r in dae.itertuples(index=False):
        d = denom_dae(r.expediente)
        if not d:
            cua.apartar("expediente con formato desconocido",
                        r.expediente, r._asdict())
            continue
        m = re.search(r"-([A-Z]{2})$", str(r.expediente).strip())
        # El extracto arranca con el/los autores antes de los dos puntos:
        # 'VIGO Y ESPINOLA: PROYECTO DE LEY QUE...'
        ext = str(r.extracto or "")
        autores = []
        if ":" in ext:
            cab = ext.split(":", 1)[0]
            if len(cab) < 120:
                autores = [a.strip() for a in re.split(r"\s+Y\s+|,", cab) if a.strip()]
        fichas[d] = {
            "camara": "senado",
            "sumario": ext or None,
            "fecha_ingreso": str(r.fecha_mesa)[:10] if pd.notna(r.fecha_mesa) else None,
            "tipo": TIPO_DAE.get(m.group(1) if m else "", None),
            "url": r.expediente_url,
            "firmantes": autores,
            "giros": separar_giros_dae(r.giros),
        }
    # Lo que no se pudo leer NO se descarta ni frena la carga: va a la base de
    # cuarentena (decision de Valle, 07-08). `proyectos.db` queda limpia por
    # definicion; lo dudoso espera revision humana en `cuarentena.db`.
    cua.controlar_tasa(len(dae))
    cua.guardar()
    logger.info("DAE (Senado):    %d fichas", len(fichas))
    return fichas


def aplicar(fichas: dict[str, dict], dry: bool = False) -> dict[str, int]:
    if not DB.exists():
        raise SystemExit(f"no existe {DB}. Corre antes: migrar_ckan.py")
    trabajo = Path(tempfile.gettempdir()) / "proyectos_upsert.db"
    shutil.copyfile(DB, trabajo)
    con = sqlite3.connect(str(trabajo))
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")

    existentes = {r[0] for r in con.execute("SELECT denominador FROM proyectos")}
    nuevos = [d for d in fichas if d not in existentes]
    yaest = [d for d in fichas if d in existentes]
    nuevos_set = set(nuevos)
    st = {"nuevos": len(nuevos), "actualizados": len(yaest),
          "autores": 0, "giros": 0}
    logger.info("nuevos: %d · ya estaban (se enriquecen): %d", len(nuevos), len(yaest))
    if dry:
        con.close()
        return st

    ahora = _ahora()
    # 1. Altas: proyectos que CKAN todavia no publico. proyecto_id queda NULL
    #    justamente para poder distinguirlos.
    con.executemany(
        "INSERT INTO proyectos (denominador,camara,sumario,fecha_ingreso,fuente_ok,"
        "capturado_en,creado_en,actualizado_en,tipo,url,pdf_url) "
        "VALUES (?,?,?,?,1,?,?,?,?,?,?)",
        [(d, f["camara"], f.get("sumario"), f.get("fecha_ingreso"), ahora, ahora,
          ahora, f.get("tipo"), f.get("url"), f.get("pdf_url"))
         for d in nuevos for f in [fichas[d]]])

    # 2. MERGE: solo las hijas donde el bot manda. El tramite y los hitos de CKAN
    #    NI SE TOCAN — es exactamente lo que un upsert ciego habria destruido.
    con.executemany("DELETE FROM proyecto_autores WHERE denominador=?",
                    [(d,) for d in fichas])
    aut = [(d, i, n, None, None)
           for d, f in fichas.items() for i, n in enumerate(f["firmantes"])]
    con.executemany("INSERT INTO proyecto_autores (denominador,orden,nombre,distrito,"
                    "bloque) VALUES (?,?,?,?,?)", aut)
    st["autores"] = len(aut)

    # ⚠️ CORREGIDO 07-08. El primer intento le daba al bot precedencia sobre los
    # giros SIEMPRE, y estaba mal: son dos cosas distintas con el mismo nombre.
    #   CKAN  -> giros ACUMULADOS de hoy (incluye ampliaciones posteriores)
    #   bot   -> giros AL INGRESAR (la foto del dia 0)
    # Pisar unos con otros borro el acumulado de 2.267 proyectos (4.115 -> 4.006
    # giros). Al modelo no lo afecto —usa el inicial— pero se perdio el dato con
    # el que Franco midio las ampliaciones de giro el 07-08.
    # Ahora: `proyecto_giros` SOLO se escribe para proyectos que CKAN no conoce
    # (ahi el bot es la unica fuente). Para el resto, el giro al ingresar vive
    # donde corresponde: en la columna `n_giros_inicial`, mas abajo.
    con_giros = [d for d, f in fichas.items() if f["giros"] and d in nuevos_set]
    con.executemany("DELETE FROM proyecto_giros WHERE denominador=?",
                    [(d,) for d in con_giros])
    gir = [(d, i, c, 1 if i == 0 else 0, fichas[d].get("fecha_ingreso"), None)
           for d in con_giros for i, c in enumerate(fichas[d]["giros"])]
    con.executemany("INSERT INTO proyecto_giros (denominador,orden,comision,"
                    "competencia_primaria,fecha_ingreso,fecha_egreso) VALUES (?,?,?,?,?,?)", gir)
    st["giros"] = len(gir)

    # 3. El giro del bot ES el giro al ingresar: se registra como tal.
    # El giro AL INGRESAR si se registra para todos los del bot: es medicion
    # directa y le gana a la reconstruccion de `giros_iniciales.py`.
    con.executemany("UPDATE proyectos SET n_giros_inicial=?, n_giros_inicial_fuente='bot',"
                    " actualizado_en=? WHERE denominador=?",
                    [(len(f["giros"]), ahora, d) for d, f in fichas.items() if f["giros"]])

    con.commit()
    con.execute("PRAGMA optimize")
    con.close()
    shutil.copyfile(trabajo, DB)
    logger.info("publicada en %s (%.1f MB)", DB, DB.stat().st_size / 1e6)
    return st


def _control() -> int:
    """Corre el control de integridad. Ver `verificar.py` para el por que."""
    import verificar
    c = verificar.Control()
    verificar.controles_base(c)
    verificar.control_cohorte(c)
    return c.informe()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cat = catalogo_comisiones()
    logger.info("catalogo de comisiones: %d nombres", len(cat))
    fichas = {**fichas_tp(cat), **fichas_dae()}
    logger.info("fichas del bot en total: %d", len(fichas))
    st = aplicar(fichas, dry=a.dry_run)
    print("\n  " + " · ".join(f"{k}={v:,}" for k, v in st.items()))
    if a.dry_run:
        return 0
    # El control NO es opcional: si un numero no cierra, esto corta con exit 1.
    import verificar
    return verificar.main.__wrapped__() if hasattr(verificar.main, "__wrapped__") else _control()


if __name__ == "__main__":
    sys.exit(main())
