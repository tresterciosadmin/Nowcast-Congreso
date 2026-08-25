# -*- coding: utf-8 -*-
"""Empareja el nombre de un firmante del dictamen con el legislador del padrón.

## Por qué contra el padrón y no contra el PDF

El PDF de la Orden del Día da el nombre y **casi nunca el bloque**: en el dictamen
de mayoría los firmantes vienen pelados, y el bloque sólo aparece en algunas
disidencias. Decisión de Valle (21-08-2026): el bloque se resuelve contra
`datos/padron`, que es mandate-aware y sabe qué bloque tenía cada legislador **a
la fecha del dictamen**. Sacarlo del PDF daría una segunda fuente contradictoria
para un dato que ya tenemos bien, y encima peor.

## Cómo empareja

El padrón ya trae la llave que hace falta: la columna `clave` son los tokens del
nombre en mayúsculas, sin acentos, sin partículas y **ordenados alfabéticamente**.

    'Cremer de Busti, Maria Cristina'  ->  'BUSTI CREMER CRISTINA MARIA'

Es decir, una llave **invariante al orden**, que es justo el problema: el padrón
escribe "Apellido, Nombres" y el PDF escribe "Nombres Apellido". Sin eso habría
que adivinar dónde termina el nombre y empieza un apellido compuesto — "Juan H.
Sylvestre Begnis", "Eva García de Moreno", "Norma A. Abdala de Matarazzo" — y ahí
es donde un emparejador se equivoca en silencio.

El PDF además abrevia: "Griselda A. Baldata" contra "BALDATA ANGELA GRISELDA".
Por eso el criterio es **subconjunto, no igualdad**: los tokens largos del PDF
tienen que estar todos en el padrón, y las iniciales sueltas se usan sólo para
desempatar.

## Las dos guardas que evitan el error caro

1. **Ventana de mandato.** Sólo compite quien tenía banca a la fecha del dictamen.
   Esto no es un refinamiento: hay homónimos y apellidos repetidísimos, y sin la
   ventana el emparejador elige a cualquiera. La fecha sale del propio dictamen
   (`Sala de las comisiones, <fecha>.`), no de la fecha de impresión de la OD.
2. **El empate no se rompe a la fuerza.** Si quedan dos candidatos y las iniciales
   no alcanzan, sale `ambiguo` con los candidatos anotados. Un firmante sin
   resolver es un dato faltante; un firmante mal resuelto le pone el bloque
   equivocado a una firma y contamina la señal. Ya pasó en este repo con el caso
   Bianchi: **una sola fila mal puesta contaminó 610 proyectos.**

## Salida

`resolver()` devuelve siempre un dict con `metodo` en {exacto, iniciales, ambiguo,
sin_candidatos, sin_match} y `legislador_id` vacío cuando no resolvió.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import (PADRON_DIPUTADOS, PADRON_DIPUTADOS_HISTORICO,  # noqa: E402
                   PADRON_SENADO, PADRON_SENADO_HISTORICO)

PARTICULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "DA", "DI", "DOS", "VON", "VAN", "SAN"}

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
         "noviembre": 11, "diciembre": 12}
RE_FECHA_TEXTO = re.compile(r"(\d{1,2})\s*de\s*([a-zñáéíóú]+)\s*de\s*(\d{4})", re.I)
# El Senado viejo escribe la fecha al revés: "Agosto 17 de 2010".
RE_FECHA_MES_PRIMERO = re.compile(r"([a-zñáéíóú]+)\s+(\d{1,2})\s*de\s*(\d{4})", re.I)


def fecha_es(texto: object) -> dt.date | None:
    """'27 de mayo de 2008' -> date(2008, 5, 27). Devuelve None si no se puede."""
    if texto is None or (isinstance(texto, float) and texto != texto):
        return None
    t = str(texto)
    m = RE_FECHA_TEXTO.search(t)
    if m:
        dia, mes, anio = m.group(1), m.group(2).lower(), m.group(3)
    else:
        m = RE_FECHA_MES_PRIMERO.search(t)
        if not m:
            return None
        mes, dia, anio = m.group(1).lower(), m.group(2), m.group(3)
    n = MESES.get(_sin_acentos(mes).lower())
    if not n:
        return None
    try:
        return dt.date(int(anio), n, int(dia))
    except ValueError:
        return None


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def tokenizar(nombre: object) -> tuple[frozenset[str], frozenset[str]]:
    """(tokens largos, iniciales). Mismo criterio que la columna `clave` del padrón."""
    if nombre is None or pd.isna(nombre):
        return frozenset(), frozenset()
    limpio = _sin_acentos(str(nombre)).upper()
    limpio = re.sub(r"[^A-ZÑ. ]", " ", limpio)
    largos, iniciales = set(), set()
    for pieza in limpio.replace(".", " . ").split():
        if pieza == ".":
            continue
        t = pieza.strip(".")
        if not t or t in PARTICULAS:
            continue
        (iniciales if len(t) == 1 else largos).add(t)
    return frozenset(largos), frozenset(iniciales)


def cargar_padron(camara: str) -> pd.DataFrame:
    """Padrón de una cámara, con tokens precalculados y ventana de mandato."""
    camara = camara.lower()
    # Oficial + histórico, en ese orden. Es el mismo patrón que ya usaba el Senado:
    # un solo sistema (el padrón), dos archivos, y el oficial gana cuando los dos
    # cubren la misma fecha. El histórico sólo rellena lo que el oficial no tiene.
    if camara.startswith("dip"):
        rutas = [p for p in (PADRON_DIPUTADOS, PADRON_DIPUTADOS_HISTORICO) if Path(p).exists()]
    else:
        rutas = [p for p in (PADRON_SENADO, PADRON_SENADO_HISTORICO) if Path(p).exists()]
    if not rutas:
        raise FileNotFoundError(f"no encontré ningún padrón para la cámara {camara!r}")
    partes = []
    for r in rutas:
        df = pd.read_csv(r, encoding="utf-8-sig", dtype=str)
        df = df[~df["legislador"].astype(str).str.startswith("#")]
        partes.append(df)
    # el orden de `rutas` importa: `keep="first"` deja ganar al oficial
    p = pd.concat(partes, ignore_index=True).drop_duplicates(
        subset=["legislador_id", "desde", "hasta"], keep="first")
    p["desde_d"] = pd.to_datetime(p["desde"], errors="coerce").dt.date
    p["hasta_d"] = pd.to_datetime(p["hasta"], errors="coerce").dt.date
    tok = p["clave"].map(tokenizar)
    p["tok"] = [t[0] for t in tok]
    p["ini"] = [t[1] for t in tok]
    return p


def resolver(nombre: str, padron: pd.DataFrame, fecha: dt.date | None) -> dict:
    vacio = {"legislador_id": "", "legislador": "", "bloque": "", "bloque_norm": "",
             "bloque_linaje": "", "distrito": "", "metodo": "sin_match", "candidatos": 0}
    tok, ini = tokenizar(nombre)
    if len(tok) < 2:
        return dict(vacio, metodo="nombre_corto")

    cand = padron
    if fecha is not None:
        cand = padron[(padron["desde_d"].notna()) & (padron["desde_d"] <= fecha)
                      & ((padron["hasta_d"].isna()) | (padron["hasta_d"] >= fecha))]
        if cand.empty:
            return dict(vacio, metodo="sin_candidatos")

    # subconjunto: todo token largo del PDF tiene que estar en el padrón
    hits = cand[cand["tok"].map(lambda s: tok <= s)]
    if hits.empty:
        # Separar "no está en el padrón" de "está, pero con otro mandato" NO es
        # cosmético: son dos problemas distintos y sólo uno es nuestro. El segundo
        # dice que al padrón le falta ese tramo, y se arregla en `datos/padron`.
        # Lo que NO se hace es aflojar la ventana para levantar el número: un
        # legislador con dos mandatos suele tener DOS bloques distintos, y agarrar
        # el que no es le pone la etiqueta equivocada a la firma.
        if fecha is not None and padron["tok"].map(lambda s: tok <= s).any():
            return dict(vacio, metodo="fuera_de_ventana")
        return dict(vacio, metodo="sin_match")

    metodo = "exacto"
    if len(hits) > 1 and ini:
        # las iniciales del PDF tienen que aparecer como inicial de algún token sobrante
        def calza(fila) -> bool:
            sobrantes = {t[0] for t in (fila["tok"] - tok)} | fila["ini"]
            return ini <= sobrantes
        filtrado = hits[hits.apply(calza, axis=1)]
        if len(filtrado) == 1:
            hits, metodo = filtrado, "iniciales"

    if len(hits) > 1:
        # un mismo legislador con dos filas de mandato solapadas no es ambigüedad
        if hits["legislador_id"].nunique() == 1:
            hits = hits.head(1)
        else:
            # Buena parte de la "ambigüedad" es la MISMA persona escrita distinto en
            # el padrón oficial y en el histórico ("Acosta, Maria Julia" contra
            # "ACOSTA, María Julia"): dos grafías -> dos claves -> dos ids. No es un
            # empate entre dos personas, así que se aplica la precedencia que el
            # módulo ya declara: **el oficial manda**.
            oficiales = hits[hits["fuente"].astype(str).str.startswith("oficial")]
            if oficiales["legislador_id"].nunique() == 1:
                hits, metodo = oficiales.head(1), "oficial_gana"
            else:
                return dict(vacio, metodo="ambiguo",
                            candidatos=int(hits["legislador_id"].nunique()))

    f = hits.iloc[0]
    return {"legislador_id": f["legislador_id"], "legislador": f["legislador"],
            "bloque": f.get("bloque", ""), "bloque_norm": f.get("bloque_norm", ""),
            "bloque_linaje": f.get("bloque_linaje", ""), "distrito": f.get("distrito", ""),
            "metodo": metodo, "candidatos": 1}


def resolver_muchos(nombres, camara: str, fecha_texto: object) -> list[dict]:
    padron = cargar_padron(camara)
    fecha = fecha_es(fecha_texto)
    return [dict(resolver(n, padron, fecha), firmante_raw=n) for n in nombres]
