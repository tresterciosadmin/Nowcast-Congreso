#!/usr/bin/env bash
# Instala el hook de reindexado. Correr UNA vez, desde la raiz git.
# Los hooks NO viajan en git: cada persona que clone el repo tiene que correrlo.
set -eu
RAIZ="$(git rev-parse --show-toplevel)"
SRC="$RAIZ/Nowcast Congreso Argy/.mapa/hook-pre-commit"
DST="$RAIZ/.git/hooks/pre-commit"
if [ -f "$DST" ] && ! grep -q "mapa: el indexado fallo" "$DST" 2>/dev/null; then
  cp "$DST" "$DST.antes-del-mapa"
  echo "ya habia un pre-commit: lo guarde como pre-commit.antes-del-mapa"
fi
cp "$SRC" "$DST"
chmod +x "$DST"
echo "hook instalado en $DST"
