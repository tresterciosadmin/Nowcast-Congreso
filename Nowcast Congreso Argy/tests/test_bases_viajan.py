# -*- coding: utf-8 -*-
"""Las bases SQLite tienen que VIAJAR por git, y ninguna puede acercarse al techo.

Decision del 2026-09-08 (Franco, explicita): sacamos `*.db` del .gitignore para
que las bases queden grabadas en GitHub y el equipo trabaje sobre LA MISMA base.
El costo aceptado son pushes y pulls mas pesados. Este archivo es el control de
esa decision, y son dos controles distintos que se necesitan mutuamente:

1. **Que las bases no vuelvan a quedar ignoradas.** Es literalmente el modo de
   falla que este repo ya sufrio seis veces (parquet de expedientes 11-07, roster
   de jefes 30-07, salidas del embudo 31-07, padron del Senado 04-08, contratos
   entre modulos 06-08, registro de taxonomias 06-09). Las seis veces el archivo
   existia en un disco, no daba error, y el equipo concluyo -con razon- que el
   dato no existia. Una regla `*.db` reintroducida "por prolijidad" repite eso
   sobre el objeto mas grande del repo.

2. **Que ningun archivo se acerque a los 100 MB.** GitHub RECHAZA archivos de mas
   de 100 MB: el push falla entero. `proyectos.db` estaba en 85,7 MB el 08-09, o
   sea al 86% del techo, y crece con cada ingesta. Si este test avisa, hay que
   decidir Git LFS ANTES de que el push falle -- despues el arreglo es reescribir
   historia, que en este repo esta prohibido.

El segundo control es el que hace honesta a la decision: sacar las bases del
.gitignore sin vigilar el tamaño es cambiar un problema silencioso (bases que
divergen) por otro (un push que no entra y nadie sabe por que).

    python -m pytest tests/test_bases_viajan.py -q
    python tests/test_bases_viajan.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

MB = 1024 * 1024
LIMITE_GITHUB = 100 * MB   # rechazo duro del lado de GitHub
FALLA = 95 * MB            # margen: si algo llega aca, ya hay que actuar
AVISO = 50 * MB            # GitHub avisa a partir de aca

# Archivos_Borrar es descarte por definicion (CLAUDE.md): ahi NADA viaja, y esta
# bien que no viaje. Igual "Aportes sobre dataset congreso", que es material de
# terceros de un solo uso (ADR-0002).
FUERA = ("Archivos_Borrar/", "Aportes sobre dataset congreso/")

# Bases de trabajo temporales de SQLite: estas SI se ignoran, siempre.
JOURNALES = ("-wal", "-shm", "-journal")


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    # `--no-optional-locks`: `git status` normalmente refresca el indice y para
    # eso toma `.git/index.lock`. En este repo eso ya dejo locks huerfanos que
    # bloquean los commits de otra persona (URGENTE B, 05-09 y 08-09). Un test
    # de solo lectura no tiene por que tomar un lock de escritura.
    return subprocess.run(["git", "--no-optional-locks", *args],
                          cwd=str(cwd or RAIZ_PROYECTO),
                          capture_output=True, text=True, timeout=120)


def _hay_git() -> bool:
    return _git("rev-parse", "--git-dir").returncode == 0


def _relevante(rel: str) -> bool:
    return not any(rel.startswith(f) or f"/{f}" in f"/{rel}" for f in FUERA)


def _bases_en_disco() -> list[Path]:
    salida = []
    for patron in ("*.db", "*.sqlite", "*.sqlite3"):
        for p in RAIZ_PROYECTO.rglob(patron):
            rel = p.relative_to(RAIZ_PROYECTO).as_posix()
            if any(f in rel + "/" for f in FUERA):
                continue
            if p.name == "Thumbs.db":          # basura de Windows, no es una base
                continue
            salida.append(p)
    return sorted(salida)


def test_las_bases_no_estan_ignoradas():
    """Una base ignorada vive en un solo disco. Es el bug que se cerro el 08-09."""
    if not _hay_git():
        return
    bases = _bases_en_disco()
    assert bases, "no se encontro ninguna base .db: revisar el test, no el repo"
    ignoradas = []
    for p in bases:
        rel = p.relative_to(RAIZ_PROYECTO).as_posix()
        if _git("check-ignore", "-q", rel).returncode == 0:
            ignoradas.append(f"{rel} ({p.stat().st_size / MB:.1f} MB)")
    assert not ignoradas, (
        "estas bases estan IGNORADAS por git y por lo tanto viven en un solo disco:\n  "
        + "\n  ".join(ignoradas)
        + "\nEs el modo de falla que el .gitignore documenta seis veces. Si hace falta "
          "excluir una, hay que decirlo EN EL .gitignore con el motivo, no dejarla caer "
          "en un comodin.")


def test_los_journales_siguen_ignorados():
    """`-wal`/`-shm` son estado de UNA corrida: versionarlos corrompe la base del otro."""
    if not _hay_git():
        return
    viajan = []
    for suf in JOURNALES:
        candidato = "datos/proyectos/data/proyectos.db" + suf
        if _git("check-ignore", "-q", candidato).returncode != 0:
            viajan.append(candidato)
    assert not viajan, (
        "los journals de SQLite NO estan ignorados: " + ", ".join(viajan)
        + ". Versionar un `-wal` le entrega a otra persona una transaccion a medio "
          "escribir sobre una base que ella no abrio.")


def test_nada_versionado_se_acerca_al_techo_de_github():
    """GitHub rechaza >100 MB. El push falla entero y el arreglo es reescribir historia."""
    if not _hay_git():
        return
    r = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if r.returncode != 0:
        return
    pesados, avisos = [], []
    for rel in r.stdout.split("\0"):
        if not rel or not _relevante(rel):
            continue
        p = RAIZ_PROYECTO / rel
        try:
            n = p.stat().st_size
        except OSError:
            continue
        if n >= FALLA:
            pesados.append(f"{rel}: {n / MB:.1f} MB")
        elif n >= AVISO:
            avisos.append(f"{rel}: {n / MB:.1f} MB")
    if avisos:
        print("  aviso (GitHub avisa a partir de 50 MB, todavia entran):")
        for a in avisos:
            print(f"    {a}")
    assert not pesados, (
        "estos archivos estan por encima de los 95 MB y GitHub corta en 100:\n  "
        + "\n  ".join(pesados)
        + "\nNO commitear hasta decidir. Las dos salidas son Git LFS (mismo objetivo de "
          "unidad, sin techo) o partir el archivo. Lo que NO es salida es pushear y ver "
          "que pasa: el rechazo es del lado del servidor y deja el commit hecho.")


def test_no_volvio_la_regla_que_escondia_las_bases():
    """Si alguien repone `*.db`, el punto 1 se rompe en silencio la proxima ingesta."""
    gi = RAIZ_PROYECTO / ".gitignore"
    if not gi.exists():
        return
    lineas = [l.strip() for l in gi.read_text(encoding="utf-8").splitlines()]
    reglas = [l for l in lineas if l and not l.startswith("#")]
    prohibidas = [l for l in reglas if l in ("*.db", "*.sqlite", "*.sqlite3", "**/*.db")]
    assert not prohibidas, (
        f"volvio al .gitignore una regla que esconde las bases: {prohibidas}. "
        "La decision del 08-09 fue que las bases viajen; si se quiere revertir, se "
        "revierte con un ADR y avisandole al equipo, no agregando una linea.")


def _correr() -> int:
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"OK   {nombre}")
            except AssertionError as e:
                fallas += 1
                print(f"FALLA {nombre}\n  {e}")
    bases = _bases_en_disco()
    print("\nbases encontradas:")
    for p in bases:
        print(f"  {p.relative_to(RAIZ_PROYECTO).as_posix():55} {p.stat().st_size / MB:7.1f} MB")
    print(f"\n{fallas} fallas")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(_correr())
