# -*- coding: utf-8 -*-
"""La MISMA persona con dos `legislador_id`: tabla de alias y resolucion.

**Por que existe.** `_leg_id()` hashea el CONJUNTO de palabras del nombre, asi que
"ROSSI Agustin" y "Rossi, Agustin Oscar" dan ids distintos. En 118 de los 153 pares
del censo del 04-09 las dos mitades vienen de **fuentes disjuntas** (`ckan_diputados`
por un lado, `argentinadatos`/`manual_2026` por el otro): no son dos personas, es la
costura entre dos ingestores que escriben los nombres con otra convencion.

**Donde se aplica.** Desde el 06-09-2026, en `entity_resolution.py`: los ids de la
canonica se reemplazan por su canonico al final del resolutor (25.030 filas de voto,
2.302 ids -> 2.159). Antes de esa fecha SOLO se usaba para cruces por id, y no por
prolijidad: mergear SIN el guard de era EMPEORA el skill (0,1317 -> 0,1301, medido el
04-09), porque la fragmentacion de ids venia funcionando como un guard de era
accidental. Primero se prendio el guard (ADR-0018) y despues el merge.

**Y con el guard puesto tampoco sale gratis, aunque casi.** Medido el 06-09 con la
clave del motor (camara, id, era): skill 0,1691 -> 0,1684. La perdida esta concentrada
en 2019-2023 (-0,0140), que es la era con menos votos (3,5% de la base) y por lo tanto
la mas ruidosa; las dos eras que le importan al producto no se mueven (2015-2019
+0,0000, desde 2023 -0,0001). Se aplico igual porque **son la misma persona**: una
metrica que mejora manteniendo partida una carrera esta midiendo un beneficio
accidental, no la verdad. Queda anotado para que nadie lo descubra despues.

**Tambien sirve para los CRUCES POR ID**, que fue su primer uso: el roster de jefes de
bloque contra las firmas del dictamen. Ahi se normalizan los dos lados antes de
comparar (`modelo/ensemble/src/estimar_beta_dictamen.py`).

    from alias_legislador import canonico, cargar_alias
    canonico("leg:3a122de91183")   -> "leg:3cc84340cad1"
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "data" / "alias_legislador_id.csv"


@lru_cache(maxsize=1)
def cargar_alias(ruta: str | None = None) -> dict[str, str]:
    """{id_absorbido: id_canonico}. Vacio si el archivo no esta (no rompe nada)."""
    p = Path(ruta) if ruta else RUTA
    if not p.exists():
        return {}
    salida: dict[str, str] = {}
    with p.open(encoding="utf-8-sig") as fh:
        for fila in csv.DictReader(l for l in fh if not l.lstrip().startswith("#")):
            a, c = (fila.get("id_absorbido") or "").strip(), (fila.get("id_canonico") or "").strip()
            if a and c and a != c:
                salida[a] = c
    # cadenas: A->B y B->C tienen que terminar los dos en C
    for _ in range(5):
        salida = {k: salida.get(v, v) for k, v in salida.items()}
    return {k: v for k, v in salida.items() if k != v}


def canonico(lid, alias: dict[str, str] | None = None):
    """Devuelve el id canonico. Lo que no esta en la tabla vuelve tal cual."""
    if lid is None:
        return lid
    a = cargar_alias() if alias is None else alias
    return a.get(lid, lid)
