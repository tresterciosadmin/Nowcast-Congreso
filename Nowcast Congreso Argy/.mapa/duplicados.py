# -*- coding: utf-8 -*-
"""Busca codigo repetido en TODO el repo, comparando la forma del arbol sintactico.

Contesta con numeros la pregunta "¿cuanto codigo redundante hay?", que hasta el
2026-09-08 se contestaba a ojo. Tres cortes, de mas fuerte a mas debil:

  A. CUERPOS IDENTICOS      mismo AST exacto en dos archivos distintos.
  B. MISMA FORMA            mismo AST despues de anonimizar los nombres locales:
                            agarra el copiar-pegar con variables renombradas.
  C. MISMO NOMBRE en >=3    el mismo helper reimplementado en varios lugares. Es
     archivos               el corte mas debil: `main` aparece en 75 archivos y
                            eso es correcto, no duplicacion.

**Lo que NO dice.** Que dos funciones tengan la misma forma no prueba que
sobren: puede ser el bootstrap que cada entrypoint necesita antes de poder
importar nada, o un helper que a proposito no crea una dependencia entre
modulos. El corte C tiene tantos falsos positivos que se lee como pista, no como
veredicto. *"Estan repetidas" es una propiedad medida; "sobran" es una
conclusion, y la saca una persona.*

Se excluyen `Archivos_Borrar/`, `Aportes sobre dataset congreso/`, `.mapa/` y
`fase0/` (fase cerrada, se conserva como registro).

    python .mapa/duplicados.py            # informe completo
    python .mapa/duplicados.py --min 10   # solo lo que ahorra >=10 LOC por grupo
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
EXCLUIDAS = ("Archivos_Borrar", "Aportes sobre dataset congreso", ".mapa", "fase0",
             "__pycache__", ".pytest_cache")
MIN_SENTENCIAS = 3   # por debajo de esto son helpers de una linea: ruido


def _archivos():
    for p in sorted(RAIZ.rglob("*.py")):
        rel = p.relative_to(RAIZ).as_posix()
        if any(rel.startswith(e) or f"/{e}/" in f"/{rel}" for e in EXCLUIDAS):
            continue
        yield rel, p


class _Anonimo(ast.NodeTransformer):
    """Renombra variables y argumentos a v0, v1... para comparar la FORMA."""

    def __init__(self):
        self.mapa: dict[str, str] = {}

    def _renombrar(self, n: str) -> str:
        if n in ("self", "cls"):
            return n
        return self.mapa.setdefault(n, f"v{len(self.mapa)}")

    def visit_Name(self, node):
        node.id = self._renombrar(node.id)
        return self.generic_visit(node)

    def visit_arg(self, node):
        node.arg = self._renombrar(node.arg)
        node.annotation = None
        return node


def _sin_docstring(fn) -> list:
    cuerpo = list(fn.body)
    if (cuerpo and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)):
        cuerpo = cuerpo[1:]
    return cuerpo


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()[:12]


def analizar():
    identicas = collections.defaultdict(list)
    formas = collections.defaultdict(list)
    por_nombre = collections.defaultdict(list)
    total = 0
    for rel, p in _archivos():
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            print(f"  [aviso] no parsea, lo salteo: {rel}", file=sys.stderr)
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            cuerpo = _sin_docstring(nodo)
            if len(cuerpo) < MIN_SENTENCIAS:
                continue
            total += 1
            loc = max(getattr(n, "lineno", 0) for n in ast.walk(nodo)) - nodo.lineno + 1
            literal = _md5("".join(
                ast.dump(c, annotate_fields=False, include_attributes=False)
                for c in cuerpo))
            copia = ast.parse(ast.unparse(ast.Module(body=cuerpo, type_ignores=[])))
            forma = _md5(ast.dump(_Anonimo().visit(copia), annotate_fields=False,
                                  include_attributes=False))
            identicas[literal].append((rel, nodo.name, loc))
            formas[forma].append((rel, nodo.name, loc))
            por_nombre[nodo.name].append((rel, loc))
    return total, identicas, formas, por_nombre


def _bloque(titulo, grupos, minimo):
    print("=" * 78)
    print(titulo)
    print("=" * 78)
    entre_archivos = {k: v for k, v in grupos.items() if len({x[0] for x in v}) > 1}
    ahorro = 0
    for v in sorted(entre_archivos.values(), key=lambda v: -(len(v) * v[0][2])):
        if v[0][2] * (len(v) - 1) < minimo:
            continue
        ahorro += v[0][2] * (len(v) - 1)
        print(f"\n  {v[0][2]:>3} LOC x{len(v)}  ->  ahorraria ~{v[0][2] * (len(v) - 1)} LOC")
        for rel, nom, _ in sorted(v):
            print(f"        {nom:<34} {rel}")
    print(f"\n  AHORRO ESTIMADO DE ESTE CORTE: ~{ahorro} LOC\n")
    return ahorro


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min", type=int, default=6,
                    help="ahorro minimo por grupo para listarlo (default 6 LOC)")
    ap.add_argument("--sin-nombres", action="store_true",
                    help="saltea el corte C, que es el mas ruidoso")
    args = ap.parse_args(argv)

    total, identicas, formas, por_nombre = analizar()
    loc_repo = sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
                   for _, p in _archivos())
    print(f"{total} funciones de >={MIN_SENTENCIAS} sentencias · "
          f"{loc_repo:,} LOC de Python analizadas\n".replace(",", "."))

    a = _bloque("A. CUERPOS IDENTICOS (mismo codigo exacto, distinto archivo)",
                identicas, args.min)
    _bloque("B. MISMA FORMA con nombres locales distintos (copiar-pegar renombrado)",
            formas, args.min)

    if not args.sin_nombres:
        print("=" * 78)
        print("C. MISMO NOMBRE EN >=3 ARCHIVOS  (pista debil: `main` sale aca y esta bien)")
        print("=" * 78)
        for nom, v in sorted(por_nombre.items(), key=lambda kv: -len(kv[1])):
            if len(v) < 3 or nom == "main":
                continue
            print(f"\n  {nom}  ({len(v)} archivos)")
            for rel, loc in sorted(v):
                print(f"        {loc:>3} LOC  {rel}")

    print("\n" + "=" * 78)
    pct = 100 * a / loc_repo if loc_repo else 0
    print(f"Duplicacion EXACTA entre archivos: ~{a} LOC sobre {loc_repo:,} "
          f"({pct:.1f}% del codigo).".replace(",", "."))
    print("Que esten repetidas es una propiedad medida; que SOBREN es una conclusion.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
