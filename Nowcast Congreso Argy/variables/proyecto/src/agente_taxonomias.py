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
sys.path.insert(0, str(_RAIZ / "docs" / "taxonomias"))
import loader as tx_loader  # noqa: E402

import pdf_text  # noqa: E402

logger = logging.getLogger("proyecto.agente_taxonomias")

# Tarea acotada (leer texto + elegir de una lista cerrada, con validación posterior):
# Haiku alcanza y es barato. Subí a un modelo mayor con TAXO_MODEL si hace falta.
MODELO_DEFAULT = os.environ.get("TAXO_MODEL", "claude-haiku-4-5-20251001")


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
    escaneado: bool = False
    modelo: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────────
# Prompt
# ────────────────────────────────────────────────────────────────────────────
def construir_prompt(texto: str, tx: dict) -> tuple[str, str]:
    lista = tx_loader.lista_para_prompt(tx)
    reglas = tx.get("reglas_frontera", [])
    reglas_txt = "\n".join(
        f"- {r.get('regla')} → usar {r.get('asignar')}" for r in reglas
    )
    system = (
        "Sos un clasificador experto en proyectos de ley del Congreso argentino. "
        "Tu tarea es asignar TAXONOMÍAS temáticas a un proyecto, eligiendo ÚNICAMENTE "
        "de la lista controlada que se te da. Reglas:\n"
        "1) Multi-etiqueta: asigná TODOS los subtemas que apliquen (lo normal es más de uno).\n"
        "2) Usá EXCLUSIVAMENTE ids que estén en la lista. No inventes ids ni nombres.\n"
        "3) Si el proyecto no encaja en ningún subtema sustantivo, asigná AUX.SINCLASIF "
        "y proponé el tema faltante en 'candidatos_nuevos' (texto libre, sin id).\n"
        "4) Homenajes/declaraciones → AUX.HOMENAJE. Trámite sin contenido → AUX.TRAMITE.\n"
        "5) Respetá estas reglas de frontera:\n" + (reglas_txt or "- (ninguna)") + "\n"
        "6) Para cada asignación dá una confianza 0..1.\n\n"
        "Respondé SOLO con un objeto JSON válido, sin texto adicional, con esta forma:\n"
        '{"asignaciones":[{"id":"AREA.SUB","confianza":0.0}],'
        '"candidatos_nuevos":["..."],"comentario":"breve"}'
    )
    user = (
        "LISTA CONTROLADA DE TAXONOMÍAS (id=nombre):\n"
        f"{lista}\n\n"
        "TEXTO DEL PROYECTO DE LEY (articulado y considerandos):\n"
        '"""\n'
        f"{pdf_text.recortar_para_prompt(texto)}\n"
        '"""\n\n'
        "Devolvé el JSON de clasificación."
    )
    return system, user


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
    return res


def clasificar_pdf(url_o_ruta: str, tx: Optional[dict] = None,
                   llm: Callable[[str, str], str] = None,
                   modelo: str = MODELO_DEFAULT) -> ResultadoClasificacion:
    if re.match(r"^https?://", url_o_ruta):
        tp = pdf_text.extraer_de_url(url_o_ruta)
    else:
        tp = pdf_text.extraer_de_archivo(url_o_ruta)
    if tp.escaneado:
        logger.warning("PDF escaneado (sin texto): OCR pendiente, no se clasifica")
        r = ResultadoClasificacion(denominador=None, escaneado=True,
                                   comentario="PDF escaneado: OCR pendiente")
        return r
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


# ────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────
def _imprimir(res: ResultadoClasificacion) -> None:
    print(json.dumps({
        "denominador": res.denominador,
        "modelo": res.modelo,
        "escaneado": res.escaneado,
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
        if res.escaneado:
            print(f"{args.denominador}: PDF escaneado, OCR pendiente. No se guardó.")
            return 0
        n = persistir(args.db, args.denominador, res)
        _imprimir(res)
        print(f"\nGuardadas {n} taxonomías para {args.denominador}.")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_main())
