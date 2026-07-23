# -*- coding: utf-8 -*-
"""Repara tablero_datos.js: reemplaza la COLA rota (desde 'capex:' hasta el final) por
la cola SANA de la versión completa más reciente del historial de git — conservando
TODO lo de arriba (hitos, estados, mis ediciones). No inventa datos.

Corrige el bug anterior: la ruta como la ve git es relativa a la RAÍZ del repo
(Nowcast-Congreso/Nowcast-Congreso), no 'tablero_datos.js' a secas.

USO (LOCAL, PC de Valle), parada en la carpeta del proyecto:
    python coordinacion/_reparar_tablero.py
"""
import subprocess
from pathlib import Path

P = (Path(__file__).resolve().parents[1] / "tablero_datos.js")


def _strip(src):
    out=[];i=0;n=len(src)
    while i<n:
        c=src[i]
        if c in '"\'':
            q=c;i+=1
            while i<n and src[i]!=q:
                if src[i]=="\\":i+=2;continue
                i+=1
            i+=1;continue
        if c=="/" and i+1<n and src[i+1]=="/":
            while i<n and src[i]!="\n":i+=1
            continue
        out.append(c);i+=1
    return "".join(out)


def _bal(s):
    t=_strip(s)
    return (t.count("{")==t.count("}") and t.count("[")==t.count("]")
            and t.count("(")==t.count(")") and s.rstrip().endswith((";","}","]")))


def _corte(txt):
    j=txt.find("capex:")
    if j<0: return -1
    nl=txt.rfind("\n",0,j)
    return nl+1 if nl>=0 else 0


def _git(args, binary=False, cwd=None):
    return subprocess.run(["git"]+args, cwd=cwd or P.parent, capture_output=True,
                          text=not binary, encoding=None if binary else "utf-8")


actual = P.read_text(encoding="utf-8")
print(f"actual: {len(actual)} chars, ¿balanceado? {_bal(actual)}")
if _bal(actual):
    print("Ya está sano. No hago nada."); raise SystemExit(0)
if _corte(actual) < 0:
    print("No encuentro 'capex:' en el actual. Aborto."); raise SystemExit(1)

# ruta tal como la ve git (relativa a la raíz del repo)
root = _git(["rev-parse","--show-toplevel"]).stdout.strip()
if not root:
    print("No estoy dentro de un repo git."); raise SystemExit(1)
rel = P.resolve().relative_to(Path(root).resolve()).as_posix()
print(f"repo: {root}\nruta git: {rel}")

ROOT = Path(root).resolve()
hashes = _git(["log","--format=%H","--", rel], cwd=ROOT).stdout.split()
print(f"versiones en git: {len(hashes)}")
buena = None
for h in hashes:
    blob = _git(["show", f"{h}:{rel}"], binary=True, cwd=ROOT).stdout.decode("utf-8","replace")
    if _bal(blob) and "capex:" in blob:
        buena = (h, blob); break

if buena is None:
    print("\nNINGUNA versión de git está completa. No toco nada. (Reconstruir capex a mano.)")
    raise SystemExit(2)

h, blob = buena
reparado = actual[:_corte(actual)] + blob[_corte(blob):]
if not _bal(reparado):
    print("Tras injertar SIGUE desbalanceado. No escribo."); raise SystemExit(3)

P.write_text(reparado, encoding="utf-8")
print(f"\nREPARADO: {len(actual)} -> {len(reparado)} chars. Cola sana de {h[:10]}.")
print("Termina en:", repr(reparado[-40:]))
print("Verificá: python -c \"s=open('tablero_datos.js',encoding='utf-8').read(); print(s.count('{'),s.count('}'),s.count('['),s.count(']'))\"")
