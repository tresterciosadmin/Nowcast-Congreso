"""Agente de TAXONOMÍAS (LLM / Claude API).

Toma el texto de un proyecto de ley, consulta el vocabulario controlado
(`docs/taxonomias/taxonomias.json`) y asigna las taxonomías que correspondan,
escribiéndolas en la base de Proyectos (`proyecto_taxonomias`).

Diseño:
  • La llamada al LLM está AISLADA en `llamar_claude` (la única parte que necesita
    red + API key). El resto (prompt, parseo, validación, persistencia) es puro y
    testeable sin red: en los tests se inyecta un LLM falso.
  • El agente elige SOLO ids que existan en el vocabulario; los inventados se
    descartan (y se loguean). Si nada encaja, marca AUX.SINCLASIF y puede proponer
    candidatos en texto (no los agrega solo: los anota para revisión humana).
  • Multi-etiqueta. Aplica las reglas de frontera del vocabulario.

Config (variables de entorno):
  ANTHROPIC_API_KEY   — la API key (obligatoria para correr en vivo).
  TAXO_MODEL          — modelo a usar (default: claude-haiku-4-5-20251001).

CLI:
  # clasifica un expediente ya cargado en la base (usa su pdf_url):
  python agente_taxonomias.py clasificar data/proyectos.db 1091-S-2026
  # clasifica un PDF/URL suelto, sin tocar la base:
  python agente_taxonomias.py probar https://.../texto.pdf
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

# vocabulario controlado (docs/taxonomias/loader.py)
_RAIZ = Path(__file__).resolve().parents[3]   # .../Nowcast Congreso Argy

# Carga el .env de la raíz del repo (si existe y si python-dotenv está instalado).
# Así ANTHROPIC_API_KEY / TAXO_MODEL salen del .env local sin exportarlas a mano.
# En la nube no hace falta .env: las variables las inyecta el host (ver README).
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(_RAIZ / ".env")
except ImportError:
    pass  # sin python-dotenv: se usan las variables de entorno del sistema tal cual

sys.path.insert(0, str(_RAIZ / "docs" / "taxonomias"))
import loader as tx_loader  # noqa: E402

import pdf_text  # noqa: E402

logger = logging.getLogger("proyecto.agente_taxonomias")

# Tarea acotada (leer texto + elegir de una lista cerrada, con validación posterior):
# Haiku alcanza y es barato. Subí a un modelo mayor con TAXO_MODEL si hace falta.
MODELO_DEFAULT = os.environ.get("TAXO_MODEL", "claude-haiku-4-5-20251001")
# Ruta de visión (PDF escaneado enviado como documento): por default el mismo Haiku,
# que ya lee PDFs por visión. Para texto legal escaneado y denso conviene escalar a
# Sonnet; hacelo con TAXO_MODEL_OCR="claude-sonnet-5" (sin tocar código).
MODELO_OCR = os.environ.get("TAXO_MODEL_OCR", MODELO_DEFAULT)


# ────────────────────────────────────────────────────────────────────────────
# Resultado
# ────────────────────────────────────────────────────────────────────────────
@dataclass
class Asignacion:
    taxonomia_id: str
    confianza: float
    nombre: Optional[str] = None


@dataclass
class ResultadoClasificacion:
    denominador: Optional[str]
    asignaciones: list[Asignacion] = field(default_factory=list)
    candidatos_nuevos: list[str] = field(default_factory=list)
    descartadas: list[str] = field(default_factory=list)   # ids inventados por el LLM
    comentario: Optional[str] = None
    escaneado: bool = False                # el PDF de origen no tenía texto extraíble
    clasificado: bool = True               # False solo si no se pudo clasificar (no persistir)
    via: Optional[str] = None              # "texto" | "pdf_documento" | "no_clasificado"
    modelo: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────────
# Prompt
# ────────────────────────────────────────────────────────────────────────────
# System ESTÁTICO e independiente de la versión del vocabulario. La lista controlada
# y las reglas de frontera NO se hardcodean: se inyectan en el mensaje de usuario desde
# taxonomias.json (single source of truth). Espejo de docs/taxonomias/AGENTE-CONSOLE-descripcion.md
# (bloque 4): si tocás uno, tocá el otro.
SYSTEM_PROMPT = (
    "Sos un clasificador experto en proyectos de ley del Congreso argentino. "
    "Tu única tarea es asignar TAXONOMÍAS temáticas a un proyecto, eligiendo EXCLUSIVAMENTE "
    "de la LISTA CONTROLADA que se te entrega en el mensaje de usuario. Reglas:\n"
    "1) Multi-etiqueta: asigná TODOS los subtemas que apliquen (lo normal es más de uno).\n"
    "2) Usá SOLO ids que aparezcan en la LISTA CONTROLADA del mensaje. No inventes ids ni nombres.\n"
    "3) Proponé temas nuevos en 'candidatos_nuevos' (texto libre, sin id) en dos casos: "
    "(a) no encaja en ningún subtema sustantivo → además asigná AUX.SINCLASIF; "
    "(b) encaja pero tuviste que FORZAR un id porque falta uno más preciso → asigná igual "
    "el/los más cercanos Y dejá el candidato. Solo proponés; no inventás ids ni agregás taxonomías.\n"
    "4) Homenajes/declaraciones → AUX.HOMENAJE. Trámite sin contenido → AUX.TRAMITE.\n"
    "5) Aplicá SIEMPRE las REGLAS DE FRONTERA que vengan en el mensaje (tienen prioridad).\n"
    "6) Para cada asignación dá una confianza 0..1.\n"
    "7) Clasificá por el CONTENIDO (articulado y considerandos), no por el bloque ni el autor.\n\n"
    "Respondé SOLO con un objeto JSON válido, sin texto adicional, con esta forma:\n"
    '{"asignaciones":[{"id":"AREA.SUB","confianza":0.0}],'
    '"candidatos_nuevos":["..."],"comentario":"breve"}'
)


def _lista_y_reglas(tx: dict) -> tuple[str, str]:
    """Arma, desde taxonomias.json, la lista controlada y las reglas de frontera para el prompt."""
    lista = tx_loader.lista_para_prompt(tx)
    reglas = tx.get("reglas_frontera", [])
    reglas_txt = "\n".join(
        f"- {r.get('regla')} → usar {r.get('asignar')}" for r in reglas
    ) or "- (ninguna)"
    return lista, reglas_txt


def construir_prompt(texto: str, tx: dict) -> tuple[str, str]:
    """Ruta TEXTO: el articulado ya extraído va dentro del mensaje."""
    lista, reglas_txt = _lista_y_reglas(tx)
    user = (
        "LISTA CONTROLADA DE TAXONOMÍAS (id=nombre):\n"
        f"{lista}\n\n"
        "REGLAS DE FRONTERA (tienen prioridad):\n"
        f"{reglas_txt}\n\n"
        "TEXTO DEL PROYECTO DE LEY (articulado y considerandos):\n"
        '"""\n'
        f"{pdf_text.recortar_para_prompt(texto)}\n"
        '"""\n\n'
        "Devolvé el JSON de clasificación."
    )
    return SYSTEM_PROMPT, user


def construir_prompt_documento(tx: dict) -> tuple[str, str]:
    """Ruta VISIÓN: el texto del proyecto llega como PDF adjunto (documento), no en el prompt."""
    lista, reglas_txt = _lista_y_reglas(tx)
    user = (
        "LISTA CONTROLADA DE TAXONOMÍAS (id=nombre):\n"
        f"{lista}\n\n"
        "REGLAS DE FRONTERA (tienen prioridad):\n"
        f"{reglas_txt}\n\n"
        "El TEXTO DEL PROYECTO DE LEY está en el PDF adjunto (documento). Puede ser un PDF "
        "escaneado: leé también lo que esté como imagen. Devolvé el JSON de clasificación."
    )
    return SYSTEM_PROMPT, user


# ────────────────────────────────────────────────────────────────────────────
# Llamada al LLM (la ÚNICA parte que necesita red + API key)
# ────────────────────────────────────────────────────────────────────────────
def llamar_claude(system: str, user: str, modelo: str = MODELO_DEFAULT,
                  api_key: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Devuelve el texto crudo de la respuesta del modelo."""
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY. Configurá la variable de entorno con tu API key de Anthropic."
        )
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # concatena los bloques de texto de la respuesta
    return "".join(getattr(b, "text", "") for b in resp.content)


def llamar_claude_pdf(system: str, user: str, pdf_bytes: bytes, modelo: str = MODELO_OCR,
                      api_key: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Ruta de visión: manda el PDF como documento (base64) + el texto de instrucción.
    Claude lee el PDF con su visión nativa (incluye escaneados) — es el 'OCR' del modelo."""
    import base64
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY. Configurá la variable de entorno con tu API key de Anthropic."
        )
    b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": [
            {"type": "document",
             "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
            {"type": "text", "text": user},
        ]}],
    )
    return "".join(getattr(b, "text", "") for b in resp.content)


# ────────────────────────────────────────────────────────────────────────────
# Parseo + validación
# ────────────────────────────────────────────────────────────────────────────
def _extraer_json(raw: str) -> dict:
    """Toma el primer objeto JSON del texto (tolerante a ```json ... ``` o ruido)."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def parsear_y_validar(raw: str, tx: dict) -> ResultadoClasificacion:
    ids_validos = tx_loader.ids_validos(tx)
    nombres = {i: n for i, n, _ in tx_loader._todas_entradas(tx)}
    data = _extraer_json(raw)

    res = ResultadoClasificacion(denominador=None)
    res.comentario = (data.get("comentario") or None)
    res.candidatos_nuevos = [c for c in (data.get("candidatos_nuevos") or []) if str(c).strip()]

    vistos: set[str] = set()
    for a in data.get("asignaciones") or []:
        tid = str(a.get("id", "")).strip().upper()
        if not tid:
            continue
        if tid not in ids_validos:
            res.descartadas.append(tid)   # el LLM inventó un id: se descarta
            continue
        if tid in vistos:
            continue
        vistos.add(tid)
        try:
            conf = float(a.get("confianza", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        res.asignaciones.append(Asignacion(taxonomia_id=tid, confianza=conf, nombre=nombres.get(tid)))

    if not res.asignaciones:
        # nada válido: garantizamos al menos sin-clasificar
        res.asignaciones.append(Asignacion("AUX.SINCLASIF", 0.0, nombres.get("AUX.SINCLASIF")))
    return res


# ────────────────────────────────────────────────────────────────────────────
# Clasificación (orquesta; el LLM es inyectable para testear)
# ────────────────────────────────────────────────────────────────────────────
def clasificar_texto(texto: str, tx: Optional[dict] = None,
                     llm: Callable[[str, str], str] = None,
                     modelo: str = MODELO_DEFAULT) -> ResultadoClasificacion:
    tx = tx or tx_loader.cargar()
    llm = llm or (lambda s, u: llamar_claude(s, u, modelo=modelo))
    system, user = construir_prompt(texto, tx)
    raw = llm(system, user)
    res = parsear_y_validar(raw, tx)
    res.modelo = modelo
    res.via = "texto"
    return res


def clasificar_pdf_documento(pdf_bytes: bytes, tx: Optional[dict] = None,
                             llm_doc: Callable[[str, str, bytes], str] = None,
                             modelo: str = MODELO_OCR) -> ResultadoClasificacion:
    """Ruta de visión: clasifica un PDF (típicamente escaneado) mandándolo como documento."""
    tx = tx or tx_loader.cargar()
    llm_doc = llm_doc or (lambda s, u, b: llamar_claude_pdf(s, u, b, modelo=modelo))
    system, user = construir_prompt_documento(tx)
    raw = llm_doc(system, user, pdf_bytes)
    res = parsear_y_validar(raw, tx)
    res.modelo = modelo
    res.via = "pdf_documento"
    return res


def clasificar_pdf(url_o_ruta: str, tx: Optional[dict] = None,
                   llm: Callable[[str, str], str] = None,
                   llm_doc: Callable[[str, str, bytes], str] = None,
                   modelo: str = MODELO_DEFAULT, modelo_ocr: str = MODELO_OCR,
                   usar_vision: bool = True) -> ResultadoClasificacion:
    """Modelo híbrido: si el PDF tiene texto, ruta TEXTO (barata). Si está escaneado,
    ruta VISIÓN (manda el PDF como documento; Claude hace el OCR). `usar_vision=False`
    vuelve al viejo comportamiento de saltear escaneados."""
    if re.match(r"^https?://", url_o_ruta):
        tp = pdf_text.extraer_de_url(url_o_ruta)
    else:
        tp = pdf_text.extraer_de_archivo(url_o_ruta)

    if tp.escaneado:
        if usar_vision and tp.datos:
            logger.info("PDF escaneado → ruta visión (PDF-como-documento, modelo %s)", modelo_ocr)
            res = clasificar_pdf_documento(tp.datos, tx=tx, llm_doc=llm_doc, modelo=modelo_ocr)
            res.escaneado = True
            return res
        logger.warning("PDF escaneado y sin visión: no se clasifica")
        return ResultadoClasificacion(denominador=None, escaneado=True, clasificado=False,
                                      via="no_clasificado",
                                      comentario="PDF escaneado, ruta de visión deshabilitada")

    res = clasificar_texto(tp.texto, tx=tx, llm=llm, modelo=modelo)
    res.escaneado = False
    return res


# ────────────────────────────────────────────────────────────────────────────
# Persistencia en proyecto_taxonomias (contrato = schema de datos/proyectos)
# ────────────────────────────────────────────────────────────────────────────
def persistir(db_path: str | Path, denominador: str, res: ResultadoClasificacion,
              fuente: str = "agente") -> int:
    """Reemplaza las taxonomías de fuente 'agente' del proyecto por las nuevas.
    El HUMANO siempre gana: si una taxonomía ya está cargada a mano (fuente
    'humano'), el agente NO la sobrescribe ni la duplica. Devuelve cuántas
    taxonomías del agente quedaron escritas."""
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con = sqlite3.connect(str(db_path))
    try:
        humanas = {
            r[0] for r in con.execute(
                "SELECT taxonomia_id FROM proyecto_taxonomias WHERE denominador=? AND fuente='humano'",
                (denominador,),
            ).fetchall()
        }
        con.execute(
            "DELETE FROM proyecto_taxonomias WHERE denominador=? AND fuente=?",
            (denominador, fuente),
        )
        guardadas = 0
        for a in res.asignaciones:
            if a.taxonomia_id in humanas:
                continue  # el humano ya la asignó: no la tocamos
            con.execute(
                "INSERT OR REPLACE INTO proyecto_taxonomias "
                "(denominador, taxonomia_id, taxonomia, fuente, confianza, asignada_en) "
                "VALUES (?,?,?,?,?,?)",
                (denominador, a.taxonomia_id, a.nombre, fuente, a.confianza, ahora),
            )
            guardadas += 1
        con.commit()
        return guardadas
    finally:
        con.close()


def _pdf_url_de(db_path: str | Path, denominador: str) -> Optional[str]:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute("SELECT pdf_url FROM proyectos WHERE denominador=?", (denominador,)).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def _ya_clasificado_por_agente(db_path: str | Path, denominador: str) -> bool:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT 1 FROM proyecto_taxonomias WHERE denominador=? AND fuente='agente' LIMIT 1",
            (denominador,),
        ).fetchone()
        return row is not None
    finally:
        con.close()


# ────────────────────────────────────────────────────────────────────────────
# Batch: clasifica todos los proyectos de la base que tengan pdf_url
# ────────────────────────────────────────────────────────────────────────────
def clasificar_lote(db_path: str | Path, limite: Optional[int] = None,
                    solo_faltantes: bool = True, usar_vision: bool = True,
                    tx: Optional[dict] = None) -> dict:
    """Recorre `proyectos` con pdf_url y clasifica cada uno. Resiliente: un error en un
    proyecto se loguea y no corta el lote. Devuelve un resumen con los contadores.
    `solo_faltantes=True` saltea los que ya tienen taxonomías del agente (idempotente)."""
    tx = tx or tx_loader.cargar()
    con = sqlite3.connect(str(db_path))
    try:
        filas = con.execute(
            "SELECT denominador, pdf_url FROM proyectos "
            "WHERE pdf_url IS NOT NULL AND TRIM(pdf_url) <> '' ORDER BY fecha_ingreso DESC"
        ).fetchall()
    finally:
        con.close()

    resumen = {"total": len(filas), "clasificados": 0, "guardados_tax": 0,
               "saltados_ya": 0, "escaneados_vision": 0, "no_clasificados": 0, "errores": 0}
    hechos = 0
    for denom, url in filas:
        if limite is not None and hechos >= limite:
            break
        if solo_faltantes and _ya_clasificado_por_agente(db_path, denom):
            resumen["saltados_ya"] += 1
            continue
        try:
            res = clasificar_pdf(url, tx=tx, usar_vision=usar_vision)
            res.denominador = denom
            if not res.clasificado:
                resumen["no_clasificados"] += 1
                logger.warning("%s: no clasificado (%s)", denom, res.comentario)
                hechos += 1
                continue
            n = persistir(db_path, denom, res)
            resumen["clasificados"] += 1
            resumen["guardados_tax"] += n
            if res.via == "pdf_documento":
                resumen["escaneados_vision"] += 1
            logger.info("%s → %s (%d tax, vía %s)", denom,
                        [a.taxonomia_id for a in res.asignaciones], n, res.via)
        except Exception as e:  # resiliencia: no cortar el lote por un proyecto roto
            resumen["errores"] += 1
            logger.error("%s: error al clasificar (%s)", denom, e)
        hechos += 1
    return resumen


# ────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────
def _imprimir(res: ResultadoClasificacion) -> None:
    print(json.dumps({
        "denominador": res.denominador,
        "modelo": res.modelo,
        "via": res.via,
        "escaneado": res.escaneado,
        "clasificado": res.clasificado,
        "asignaciones": [{"id": a.taxonomia_id, "nombre": a.nombre, "confianza": a.confianza}
                         for a in res.asignaciones],
        "candidatos_nuevos": res.candidatos_nuevos,
        "ids_descartados_invalidos": res.descartadas,
        "comentario": res.comentario,
    }, ensure_ascii=False, indent=2))


def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Agente de taxonomías (LLM).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("clasificar", help="clasifica un expediente de la base y guarda")
    pc.add_argument("db"); pc.add_argument("denominador")

    pp = sub.add_parser("probar", help="clasifica un PDF/URL suelto (no toca la base)")
    pp.add_argument("pdf")

    pb = sub.add_parser("batch", help="clasifica en lote todos los proyectos con pdf_url")
    pb.add_argument("db")
    pb.add_argument("--limite", type=int, default=None, help="corta después de N proyectos")
    pb.add_argument("--todos", action="store_true",
                    help="reclasifica también los que ya tienen taxonomías del agente")
    pb.add_argument("--sin-vision", action="store_true",
                    help="saltea escaneados en vez de mandarlos como PDF-documento")

    args = p.parse_args()
    if args.cmd == "probar":
        res = clasificar_pdf(args.pdf)
        _imprimir(res)
        return 0
    if args.cmd == "clasificar":
        url = _pdf_url_de(args.db, args.denominador)
        if not url:
            print(f"No encuentro pdf_url para {args.denominador} en la base.")
            return 1
        res = clasificar_pdf(url)
        res.denominador = args.denominador
        if not res.clasificado:
            print(f"{args.denominador}: no se pudo clasificar ({res.comentario}). No se guardó.")
            return 0
        n = persistir(args.db, args.denominador, res)
        _imprimir(res)
        print(f"\nGuardadas {n} taxonomías para {args.denominador}.")
        return 0
    if args.cmd == "batch":
        resumen = clasificar_lote(args.db, limite=args.limite,
                                  solo_faltantes=not args.todos,
                                  usar_vision=not args.sin_vision)
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_main())
