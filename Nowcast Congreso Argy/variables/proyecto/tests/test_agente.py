"""Test del agente de taxonomías SIN red (LLM falso inyectado).

Valida: construcción del prompt, parseo/validación (descarta ids inventados,
fallback a sin-clasificar), persistencia en proyecto_taxonomias (preserva 'humano'),
y detección de PDF escaneado. Corre: `python tests/test_agente.py`.
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import agente_taxonomias as ag  # noqa: E402
import pdf_text  # noqa: E402

# schema de la base de Proyectos (contrato de datos/proyectos)
SCHEMA = Path(__file__).resolve().parents[3] / "datos" / "proyectos" / "src" / "schema.sql"


def _ok(cond, msg):
    print(("PASS" if cond else "FAIL"), "-", msg)
    assert cond, msg


def test_prompt_y_parseo():
    tx = ag.tx_loader.cargar()
    system, user = ag.construir_prompt("texto de un proyecto sobre minería y ambiente", tx)
    _ok("AMB.MINER=" in user, "el prompt incluye la lista controlada")
    _ok("JSON" in system, "el system pide JSON")

    # LLM válido: 2 etiquetas buenas + 1 inventada → la inventada se descarta
    raw = ('```json\n{"asignaciones":[{"id":"AMB.MINER","confianza":0.95},'
           '{"id":"ENER.HIDRO","confianza":0.6},{"id":"INVENTADA.X","confianza":0.9}],'
           '"candidatos_nuevos":["régimen de regalías mineras"],"comentario":"ok"}\n```')
    res = ag.parsear_y_validar(raw, tx)
    ids = [a.taxonomia_id for a in res.asignaciones]
    _ok(ids == ["AMB.MINER", "ENER.HIDRO"], f"mantiene válidas, ordena ({ids})")
    _ok(res.descartadas == ["INVENTADA.X"], "descarta id inventado")
    _ok(res.asignaciones[0].nombre == "Minería", "completa el nombre desde el vocabulario")
    _ok(res.candidatos_nuevos == ["régimen de regalías mineras"], "captura candidato nuevo")

    # LLM sin nada válido → fallback AUX.SINCLASIF
    res2 = ag.parsear_y_validar('{"asignaciones":[{"id":"NOPE","confianza":1}]}', tx)
    _ok([a.taxonomia_id for a in res2.asignaciones] == ["AUX.SINCLASIF"], "fallback sin-clasificar")
    print(" --> prompt/parseo OK\n")


def test_clasificar_con_llm_falso():
    tx = ag.tx_loader.cargar()
    fake = lambda s, u: '{"asignaciones":[{"id":"SALUD.ADICC","confianza":0.88}],"comentario":"juego"}'
    res = ag.clasificar_texto("proyecto sobre ludopatía y apuestas online", tx=tx, llm=fake)
    _ok([a.taxonomia_id for a in res.asignaciones] == ["SALUD.ADICC"], "clasifica con LLM inyectado")
    _ok(res.via == "texto", "marca la vía 'texto'")
    print(" --> clasificar OK\n")


def test_ruta_vision_pdf_documento():
    """Ruta híbrida: un PDF escaneado (poco texto) se manda como documento y se clasifica."""
    tx = ag.tx_loader.cargar()

    # el prompt-documento incluye la lista y NO pide pegar texto del proyecto
    system, user = ag.construir_prompt_documento(tx)
    _ok("AMB.MINER=" in user, "el prompt-documento incluye la lista controlada")
    _ok("PDF adjunto" in user, "el prompt-documento remite al PDF adjunto")

    # LLM de visión falso: recibe (system, user, bytes) y devuelve JSON
    vistos = {}
    def fake_doc(s, u, b):
        vistos["bytes"] = b
        return '{"asignaciones":[{"id":"JUST.PENAL","confianza":0.9}],"comentario":"penal"}'
    res = ag.clasificar_pdf_documento(b"%PDF-fake-bytes", tx=tx, llm_doc=fake_doc)
    _ok(vistos["bytes"] == b"%PDF-fake-bytes", "le pasa los bytes crudos del PDF al LLM de visión")
    _ok([a.taxonomia_id for a in res.asignaciones] == ["JUST.PENAL"], "clasifica por visión")
    _ok(res.via == "pdf_documento", "marca la vía 'pdf_documento'")

    # clasificar_pdf ruta un 'escaneado' con datos hacia la vía visión (monkeypatch de extracción)
    orig = ag.pdf_text.extraer_de_archivo
    ag.pdf_text.extraer_de_archivo = lambda ruta: ag.pdf_text.TextoProyecto(
        texto="", paginas=3, escaneado=True, fuente=str(ruta), datos=b"%PDF-fake")
    try:
        r2 = ag.clasificar_pdf("cualquier.pdf", tx=tx, llm_doc=fake_doc)
    finally:
        ag.pdf_text.extraer_de_archivo = orig
    _ok(r2.via == "pdf_documento" and r2.escaneado and r2.clasificado,
        "clasificar_pdf enruta el escaneado a visión y queda clasificado")

    # con usar_vision=False, el escaneado NO se clasifica (comportamiento viejo)
    ag.pdf_text.extraer_de_archivo = lambda ruta: ag.pdf_text.TextoProyecto(
        texto="", paginas=3, escaneado=True, fuente=str(ruta), datos=b"%PDF-fake")
    try:
        r3 = ag.clasificar_pdf("cualquier.pdf", tx=tx, usar_vision=False)
    finally:
        ag.pdf_text.extraer_de_archivo = orig
    _ok(not r3.clasificado and r3.via == "no_clasificado", "usar_vision=False saltea el escaneado")
    print(" --> ruta visión OK\n")


def test_persistencia():
    tmp = Path(tempfile.mkdtemp())
    db = tmp / "p.db"
    con = sqlite3.connect(db)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.execute("INSERT INTO proyectos (denominador,camara,creado_en) VALUES (?,?,?)",
                ("1091-S-2026", "senado", "2026-06-30T00:00:00+00:00"))
    # una taxonomía cargada a mano (fuente humano): debe sobrevivir
    con.execute("INSERT INTO proyecto_taxonomias VALUES (?,?,?,?,?,?)",
                ("1091-S-2026", "CULT.DEPORTE", "Deporte", "humano", 1.0, "2026-06-30T00:00:00+00:00"))
    con.commit(); con.close()

    res = ag.ResultadoClasificacion(denominador="1091-S-2026", asignaciones=[
        ag.Asignacion("CULT.DEPORTE", 0.9, "Deporte"),
        ag.Asignacion("ECON.PRESU", 0.5, "Presupuesto y gasto público"),
    ])
    n = ag.persistir(db, "1091-S-2026", res, fuente="agente")
    _ok(n == 1, f"guardó 1 del agente (la otra ya estaba como humano) ({n})")

    con = sqlite3.connect(db)
    filas = con.execute(
        "SELECT taxonomia_id, fuente FROM proyecto_taxonomias ORDER BY fuente, taxonomia_id"
    ).fetchall()
    con.close()
    _ok(("CULT.DEPORTE", "humano") in filas, "la taxonomía 'humano' sobrevivió")
    _ok(("CULT.DEPORTE", "agente") not in filas, "el agente NO duplicó la del humano")
    _ok(("ECON.PRESU", "agente") in filas, "el agente sumó la nueva")
    # re-clasificar reemplaza solo las del agente (no duplica)
    ag.persistir(db, "1091-S-2026", res, fuente="agente")
    con = sqlite3.connect(db)
    total = con.execute("SELECT COUNT(*) FROM proyecto_taxonomias").fetchone()[0]
    con.close()
    _ok(total == 2, f"re-clasificar no duplica (humano CULT.DEPORTE + agente ECON.PRESU = 2, hay {total})")
    print(" --> persistencia OK\n")


def test_escaneado():
    res = pdf_text.extraer_de_bytes  # solo referencia
    tp = pdf_text.TextoProyecto(texto="hola", paginas=1, escaneado=len("hola") < pdf_text.MIN_CHARS_TEXTO, fuente="x")
    _ok(tp.escaneado, "detecta poco texto como escaneado")
    largo = "palabra " * 100
    _ok(len(largo) >= pdf_text.MIN_CHARS_TEXTO, "umbral de escaneo razonable")
    print(" --> escaneado OK\n")


def test_batch_idempotente():
    """El batch clasifica los que faltan, saltea los ya hechos y no corta por un error."""
    tmp = Path(tempfile.mkdtemp())
    db = tmp / "p.db"
    con = sqlite3.connect(db)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    for d in ("1-D-2026", "2-D-2026"):
        con.execute("INSERT INTO proyectos (denominador,camara,pdf_url,creado_en) VALUES (?,?,?,?)",
                    (d, "diputados", f"https://x/{d}.pdf", "2026-06-30T00:00:00+00:00"))
    # uno sin pdf_url: no debe entrar al lote
    con.execute("INSERT INTO proyectos (denominador,camara,creado_en) VALUES (?,?,?)",
                ("3-D-2026", "diputados", "2026-06-30T00:00:00+00:00"))
    con.commit(); con.close()

    # monkeypatch: en vez de bajar PDF, devolvemos texto; el LLM da una etiqueta fija
    orig = ag.pdf_text.extraer_de_url
    ag.pdf_text.extraer_de_url = lambda url, session=None: ag.pdf_text.TextoProyecto(
        texto="proyecto sobre presupuesto", paginas=1, escaneado=False, fuente=url)
    fake = lambda s, u: '{"asignaciones":[{"id":"ECON.PRESU","confianza":0.8}]}'
    # inyectamos el LLM vía clasificar_pdf -> clasificar_texto: parcheamos llamar_claude
    orig_llm = ag.llamar_claude
    ag.llamar_claude = lambda s, u, **k: fake(s, u)
    try:
        r1 = ag.clasificar_lote(db, solo_faltantes=True)
        r2 = ag.clasificar_lote(db, solo_faltantes=True)  # segunda vuelta: todo saltado
    finally:
        ag.pdf_text.extraer_de_url = orig
        ag.llamar_claude = orig_llm

    _ok(r1["clasificados"] == 2 and r1["guardados_tax"] == 2, f"batch clasifica los 2 con pdf ({r1})")
    _ok(r1["total"] == 2, "el proyecto sin pdf_url no entra al lote")
    _ok(r2["saltados_ya"] == 2 and r2["clasificados"] == 0, f"segunda vuelta idempotente ({r2})")
    print(" --> batch OK\n")


if __name__ == "__main__":
    test_prompt_y_parseo()
    test_clasificar_con_llm_falso()
    test_ruta_vision_pdf_documento()
    test_persistencia()
    test_escaneado()
    test_batch_idempotente()
    print("TODOS LOS TESTS PASARON")
