"""Las mayorías especiales están APAGADAS en `nowcast()` (auditoría 2026-09, ítem A5,
decisión 9 de Franco).

Contra el resultado oficial de cada acta el modelo rinde peor que una moneda en dos tercios
(Brier 0,30 sobre 256 actas) y peor que una constante en tres cuartos y en absoluta
(`coordinacion/QUE-SE-MIDE.md`, §1). Por eso `nowcast()` con un `tipo_mayoria` que
`definiciones.normalizar_mayoria_valor` lleva a algo distinto de SIMPLE devuelve
`p_aprobacion = None` y `motivo_sin_numero`.

Lo que fija este archivo, sin correr una sola simulación (todo lo pesado se sustituye):
  1. cada tipo especial (y el texto crudo que se normaliza a él) devuelve sin número y con motivo;
  2. **la guarda va ANTES de cargar nada**: con la carga y la simulación reemplazadas por algo que
     rompe, igual devuelve sin número. Si alguien mueve la guarda detrás del cálculo, falla;
  3. lo que se normaliza a SIMPLE (incluido `None` y el texto no reconocido) NO lo frena la guarda:
     llega al cálculo (aquí, una excepción centinela);
  4. `imprimir()` y la CLI no se rompen con un resultado sin número.
Que el número de SIMPLE no cambió (`max|ΔP| = 0`) lo mide el panel de `ESTADO-EJECUCION.md` (A5) y
lo fija `test_incertidumbre_legislador.py` (dip 2026-06-01 origen EJECUTIVO = 0,6132).

    python modelo/ensemble/tests/test_mayorias_especiales_apagadas.py
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


import nowcast_puertas as N  # noqa: E402


class _Llego(Exception):
    """Centinela: el cálculo pesado (que en el test está sustituido) fue alcanzado."""


def _no_debe_correr(*_a, **_k):
    raise AssertionError("la guarda de mayorías especiales tiene que estar ANTES de este cálculo")


def _llego(*_a, **_k):
    raise _Llego()


class _Sustituye:
    """Reemplaza los cargadores/simuladores pesados de `nowcast()` por `reemplazo`."""

    def __init__(self, reemplazo):
        import ensemble
        import puerta_d
        self._objetivos = [(N, "_bloque"), (N, "record_legisladores"),
                           (ensemble, "simular_con_guardas"), (puerta_d, "p_voto_revisora")]
        self._reemplazo = reemplazo
        self._originales = []

    def __enter__(self):
        for mod, nombre in self._objetivos:
            self._originales.append(getattr(mod, nombre))
            setattr(mod, nombre, self._reemplazo)
        return self

    def __exit__(self, *_):
        for (mod, nombre), original in zip(self._objetivos, self._originales):
            setattr(mod, nombre, original)


# Los cuatro nombres normalizados, y el vocabulario CRUDO real de `actas_canonico.tipo_mayoria`
# (medido el 30-09-2026: todos los valores de la fuente que no son simples).
ESPECIALES = ["ABSOLUTA", "DOS_TERCIOS", "DOS_TERCIOS_CUERPO", "TRES_CUARTOS",
              "Dos tercios", "Tres cuartos", "Tres cuartos Tres cuartos — Votos Emitidos",
              "DOS TERCIOS LEGISLADORES PRESENTES", "Dos tercios Dos tercios — Votos Emitidos",
              "DOS TERCIOS DE MIEMBROS PRESENTES", "La mitad más uno",
              "Más de la mitad — Miembros del Cuerpo", "DOS TERCIOS VOTOS EMITIDOS",
              "MAS 1/2 MIEMBROS DEL CUERPO", "DOS TERCIOS MIEMBROS DEL CUERPO",
              "Tipo Mayoria: Dos tercios", "DOS TERCIOS DE MIEMBROS DEL CUERPO"]
# Lo que la fuente trae para mayoría simple (y lo que no trae nada).
SIMPLES = ["SIMPLE", "Más de la mitad", "Más de la mitad — Votos Emitidos",
           "MAS 1/2 LEGISLADORES PRESENTES", "MAS 1/2 VOTOS EMITIDOS", "", None,
           "texto que nadie reconoce"]

print("1. cada mayoría especial devuelve sin número y con el motivo — SIN cargar ni simular")
for camara in ("diputados", "senado"):
    for tipo in ESPECIALES:
        with _Sustituye(_no_debe_correr):
            try:
                r = N.nowcast(camara, "2026-06-01", tipo_mayoria=tipo, origen="EJECUTIVO")
            except AssertionError as e:
                check(False, f"{camara}/{tipo!r}: la guarda quedó detrás del cálculo ({e})")
                continue
        norm = N.normalizar_mayoria_valor(tipo)
        check(r["p_aprobacion"] is None, f"{camara}/{tipo!r}: p_aprobacion tiene que ser None: {r['p_aprobacion']}")
        check(bool(r.get("motivo_sin_numero")) and norm in r["motivo_sin_numero"],
              f"{camara}/{tipo!r}: el motivo tiene que nombrar el tipo ({norm}): {r.get('motivo_sin_numero')!r}")
        check(r["tipo_mayoria"] == tipo, f"{camara}/{tipo!r}: el tipo pedido se devuelve tal cual")
        check(r["pasos"] == [] and r["camaras"] == {}, f"{camara}/{tipo!r}: sin pasos ni tablero")
        check(r["camara_origen"] == camara and r["camara_revisora"] != camara,
              f"{camara}/{tipo!r}: las cámaras se identifican igual")

print("\n2. lo que la normalización manda a SIMPLE NO lo frena la guarda: llega al cálculo")
for tipo in SIMPLES + ["simple"]:
    check(N.normalizar_mayoria_valor(tipo) == "SIMPLE", f"{tipo!r} tiene que normalizarse a SIMPLE")
    with _Sustituye(_llego):
        try:
            N.nowcast("diputados", "2026-06-01", tipo_mayoria=tipo, origen="EJECUTIVO")
            check(False, f"{tipo!r}: no llegó al cálculo (¿la guarda lo frenó?)")
        except _Llego:
            check(True, "")

print("\n3. imprimir() y la CLI no se rompen sin número")
with _Sustituye(_no_debe_correr):
    r = N.nowcast("senado", "2026-06-01", tipo_mayoria="DOS_TERCIOS")
    buf = io.StringIO()
    with redirect_stdout(buf):
        N.imprimir(r)
    check("SIN NÚMERO" in buf.getvalue() and "P(APROBACIÓN)" not in buf.getvalue(),
          "imprimir() tiene que decir SIN NÚMERO y no imprimir una probabilidad")
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / "salida.json"
        with redirect_stdout(io.StringIO()):
            N.main(["nowcast_puertas.py", "diputados", "--fecha", "2026-06-01",
                    "--tipo-mayoria", "TRES_CUARTOS", "--json", str(ruta)])
        salida = json.loads(ruta.read_text(encoding="utf-8"))
        check(salida["p_aprobacion"] is None and salida["motivo_sin_numero"],
              f"la CLI tiene que escribir p_aprobacion null con motivo: {salida.get('p_aprobacion')!r}")

print("\n4. la lista de tipos con número es exactamente SIMPLE")
check(tuple(N.MAYORIAS_CON_NUMERO) == ("SIMPLE",), f"MAYORIAS_CON_NUMERO = {N.MAYORIAS_CON_NUMERO}")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
