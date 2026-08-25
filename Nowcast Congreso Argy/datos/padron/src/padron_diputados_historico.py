# -*- coding: utf-8 -*-
"""Padrón HISTÓRICO de Diputados, reconstruido desde la canónica.

## Por qué existe

El padrón de Diputados es **la foto vigente**. El README del módulo ya lo declara
como pendiente de fase 2 —*«Falta: histórico profundo de mandatos … hoy el padrón
es la foto vigente»*—, y el 21-08-2026 se le puso número. Bancas cubiertas al 1 de
julio de cada año, sobre 257:

    2008:  81   2010: 209   2012: 221   2014: 220   2016: 204
    2018: 196   2020: 242   2022: 142   2024: 193   2026: 257

`nomina_diputados.csv` tiene las mismas 1.454 filas, así que el hueco viene de la
fuente y no de cómo se arma el padrón.

Qué se rompe por eso: al resolver los firmantes de los dictámenes de comisión
(`datos/expedientes`), el padrón resuelve **el 55%** de las firmas. La canónica
lleva ese número al **93,6%**, porque tiene **258 diputados con voto registrado en
2008** contra las 81 bancas del padrón.

## Es el mismo patrón que ya usa el Senado

`src/padron_senado_historico.py` reconstruyó el histórico del Senado de nómina
oficial + Wikipedia, en un archivo aparte y con el mismo esquema. Esto es el
análogo para Diputados. **Un solo sistema —el padrón— con dos archivos**, igual
que la otra cámara: el oficial manda, el histórico rellena lo que aquél no cubre.

## De dónde sale cada cosa

De `datos/canonica` (se consume su contrato, no se toca su código):

- **que alguien tenía banca en una fecha** → votó ese día en un acta de Diputados;
- **el bloque** → la columna `bloque` del voto, o sea point-in-time de verdad;
- **la identidad** → `_name_key` / `_leg_id` de `entity_resolution`, los mismos que
  usa `ingesta_padron.py`. No hay espacio de ids nuevo.

## Lo que este archivo NO sabe, y dice que no sabe

**Un voto prueba presencia un día, no los bordes del mandato.** Los bordes se
infieren del recambio del 10 de diciembre de los años impares, y por eso:

- si el primer voto del período cae dentro de `MARGEN_DIAS` del inicio, se asume
  que estaba desde el arranque; si cae mucho después, **se arranca en el primer
  voto**, porque probablemente sea un reemplazo y estirar hacia atrás le daría
  banca (y bloque) en meses en los que no la tenía;
- lo mismo del otro lado, para renuncias;
- si el bloque cambia dentro del período, la fila se **parte en dos** en el punto
  medio entre el último voto de un bloque y el primero del otro. Esto no es un
  refinamiento: en el padrón oficial ya hay casos así —Cremer de Busti tiene
  `2009-12-10..2011-12-06` y `2011-12-07..2013-12-09` con bloques distintos— y
  aplastarlos en una fila le pone a una firma el bloque que no era.

Todo eso queda escrito en la columna `nota`, y `fuente` dice `derivado:canonica`
para que nadie confunda un mandato oficial con uno inferido.

## Uso

    python datos/padron/src/padron_diputados_historico.py
    python datos/padron/src/padron_diputados_historico.py --verificar
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
from collections import Counter
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("padron.historico_dip")

_HERE = Path(__file__).resolve()
_RAIZ = next(d for d in _HERE.parents if (d / "rutas.py").is_file())
sys.path.insert(0, str(_RAIZ))
from rutas import CANONICA_ACTAS, CANONICA_VOTOS_RESUELTO, PADRON_DIR  # noqa: E402

_CANON_SRC = _RAIZ / "datos" / "canonica" / "src"
if str(_CANON_SRC) not in sys.path:
    sys.path.insert(0, str(_CANON_SRC))
try:
    from entity_resolution import _bloque_norm, _leg_id, _linaje_vec, _name_key
except ImportError as e:  # pragma: no cover
    raise RuntimeError(f"no pude importar entity_resolution desde {_CANON_SRC}: {e}") from e

CAMARA = "diputados"
BANCAS = 257
MARGEN_DIAS = 120        # cuánto se estira un borde hasta el límite del período
SALIDA = PADRON_DIR / "padron_diputados_historico.csv"

COLUMNAS = ["legislador", "clave", "legislador_id", "camara", "distrito", "bloque",
            "bloque_norm", "desde", "hasta", "bloque_linaje", "fuente", "nota"]


def periodos_legislativos(desde_anio: int, hasta_anio: int) -> list[tuple[dt.date, dt.date]]:
    """Períodos de la Cámara: del 10-dic de un año impar al 09-dic dos años después."""
    salida = []
    a = desde_anio if desde_anio % 2 else desde_anio - 1
    while a <= hasta_anio:
        salida.append((dt.date(a, 12, 10), dt.date(a + 2, 12, 9)))
        a += 2
    return salida


def cargar_votos() -> pd.DataFrame:
    votos = pd.read_parquet(CANONICA_VOTOS_RESUELTO)
    if "fecha" in votos.columns:
        votos = votos.drop(columns=["fecha"])     # la fecha buena es la del acta
    actas = pd.read_parquet(CANONICA_ACTAS)[["acta_id", "camara", "fecha"]]
    actas["fecha"] = pd.to_datetime(actas["fecha"], errors="coerce")
    m = votos.merge(actas, on="acta_id", how="left")
    m = m[m["fecha"].notna()]
    m = m[m["camara"].astype(str).str.lower().eq(CAMARA)]
    faltan = [c for c in ("legislador_id", "legislador_nombre", "bloque") if c not in m.columns]
    if faltan:
        raise KeyError(f"a votos_resuelto le faltan columnas: {faltan}")
    m["bloque"] = m["bloque"].map(lambda v: "" if pd.isna(v) else str(v).strip())
    # _bloque_norm sobre los ~800 valores distintos y no sobre las 790k filas:
    # es la diferencia entre 8 segundos y varios minutos.
    tabla = {b: _bloque_norm(b) for b in m["bloque"].unique()}
    m["bloque_norm"] = m["bloque"].map(tabla)
    if "distrito" not in m.columns:
        m["distrito"] = ""
    m["distrito"] = m["distrito"].map(lambda v: "" if pd.isna(v) else str(v).strip())
    return m[["legislador_id", "legislador_nombre", "bloque", "bloque_norm",
              "distrito", "fecha"]].sort_values("fecha")


def _modal(valores: list[str]) -> str:
    """El valor más frecuente, ignorando vacíos. Sobre listas: un Counter es
    órdenes de magnitud más barato que `Series.mode()` repetido 20.000 veces."""
    c = Counter(v for v in valores if v)
    return c.most_common(1)[0][0] if c else ""


def _tramos(fechas, bloques, bloques_norm, distritos, nombres,
            ini: dt.date, fin: dt.date) -> list[dict]:
    """Parte los votos de un legislador en un período según cambie el bloque.

    **El corte NO se hace voto a voto.** El `bloque` de la canónica varía entre
    votaciones para la misma persona —fuentes distintas escriben el bloque
    distinto, y la normalización no siempre los junta—, así que cortar cada vez
    que cambia el string produce decenas de tramos de un día por legislador. En
    la primera versión de esto salieron **50.036 filas** para ~3.200 bancas.

    Se corta por **mes**: se toma el bloque dominante de cada mes y se unen los
    meses consecutivos que coinciden. Un pase de bloque real dura meses; el ruido
    de grafía dura un voto.

    Recibe listas paralelas ya ordenadas por fecha (no un DataFrame): esta función
    corre una vez por legislador y por período, unas 3.200 veces.
    """
    # bloque dominante de cada mes
    por_mes: dict[tuple[int, int], list[int]] = {}
    for k, f in enumerate(fechas):
        por_mes.setdefault((f.year, f.month), []).append(k)
    meses = sorted(por_mes)
    dom = [_modal([bloques_norm[k] for k in por_mes[m]]) for m in meses]

    # unir meses consecutivos con el mismo bloque dominante
    grupos: list[list[int]] = []
    for j, m in enumerate(meses):
        if j and dom[j] == dom[j - 1]:
            grupos[-1].extend(por_mes[m])
        else:
            grupos.append(list(por_mes[m]))
    dom = [d for j, d in enumerate(dom) if j == 0 or d != dom[j - 1]]

    tramos = []
    for j, idxs in enumerate(grupos):
        d0, d1 = fechas[idxs[0]], fechas[idxs[-1]]
        primero, ultimo = (j == 0), (j == len(grupos) - 1)
        # estirar al borde del período sólo si el voto está cerca: si está lejos,
        # lo más probable es un reemplazo y estirar le inventaría banca
        estirado_ini = primero and (d0 - ini).days <= MARGEN_DIAS
        estirado_fin = ultimo and (fin - d1).days <= MARGEN_DIAS
        if estirado_ini:
            d0 = ini
        if estirado_fin:
            d1 = fin
        if not primero:
            # el día exacto del pase de bloque no se conoce: se parte al medio
            prev = fechas[grupos[j - 1][-1]]
            d0 = prev + dt.timedelta(days=max(1, (fechas[idxs[0]] - prev).days // 2))
        tramos.append({"desde": d0, "hasta": d1, "votos": len(idxs),
                       "bloque": _modal([bloques[k] for k in idxs]),
                       "bloque_norm": dom[j],
                       "distrito": _modal([distritos[k] for k in idxs]),
                       "legislador_nombre": _modal([nombres[k] for k in idxs]),
                       "estirado_ini": estirado_ini, "estirado_fin": estirado_fin})

    # el fin de un tramo es el día anterior al arranque del siguiente, sin poder
    # quedar antes de su propio inicio (un tramo de un solo día es válido)
    for k in range(len(tramos) - 1):
        tramos[k]["hasta"] = max(tramos[k]["desde"],
                                 tramos[k + 1]["desde"] - dt.timedelta(days=1))
    return tramos


def construir() -> pd.DataFrame:
    v = cargar_votos()
    a0, a1 = v["fecha"].min().year, v["fecha"].max().year
    logger.info("votos de Diputados con fecha: %d (%d a %d), %d legisladores",
                len(v), a0, a1, v["legislador_id"].nunique())

    v = v.assign(dia=v["fecha"].dt.date)
    filas = []
    for ini, fin in periodos_legislativos(a0, a1):
        vp = v[(v["dia"] >= ini) & (v["dia"] <= fin)].sort_values(["legislador_id", "dia"])
        if vp.empty:
            continue
        lid = vp["legislador_id"].tolist()
        dia = vp["dia"].tolist()
        blo = vp["bloque"].tolist()
        bno = vp["bloque_norm"].tolist()
        dis = vp["distrito"].tolist()
        nom = vp["legislador_nombre"].tolist()
        # recorrido por bloques contiguos del mismo legislador (ya vienen ordenados)
        i = 0
        bancas = 0
        while i < len(lid):
            j = i
            while j < len(lid) and lid[j] == lid[i]:
                j += 1
            bancas += 1
            for t in _tramos(dia[i:j], blo[i:j], bno[i:j], dis[i:j], nom[i:j], ini, fin):
                nota = [f"mandato inferido de {t['votos']} voto(s) en el período "
                        f"{ini.year}-{fin.year}"]
                if not t["estirado_ini"]:
                    nota.append("inicio = primer voto (posible reemplazo)")
                if not t["estirado_fin"]:
                    nota.append("fin = último voto (posible cese anticipado)")
                filas.append({"legislador": t["legislador_nombre"], "legislador_id": lid[i],
                              "camara": CAMARA, "distrito": t["distrito"],
                              "bloque": t["bloque"], "bloque_norm": t["bloque_norm"],
                              "desde": t["desde"].isoformat(), "hasta": t["hasta"].isoformat(),
                              "nota": "; ".join(nota)})
            i = j
        logger.info("período %s..%s: %d bancas reconstruidas", ini, fin, bancas)

    out = pd.DataFrame(filas)
    if out.empty:
        raise SystemExit("no salió ninguna fila; revisá que la canónica tenga actas de Diputados")
    claves = {n: _name_key(n) for n in out["legislador"].unique()}
    out["clave"] = out["legislador"].map(claves)
    # el id manda el de la canónica; se controla que la clave derive en el mismo
    recalc = out["clave"].map({c: _leg_id(c) for c in set(claves.values())})
    difieren = int((recalc != out["legislador_id"]).sum())
    if difieren:
        logger.warning("%d filas donde _leg_id(clave) != legislador_id de la canónica "
                       "(nombres con distinta grafía entre actas); manda el de la canónica",
                       difieren)
    out["bloque_linaje"] = _linaje_vec(out["bloque_norm"],
                                       pd.to_datetime(out["desde"], errors="coerce"))
    out["fuente"] = "derivado:canonica"
    return out[COLUMNAS].sort_values(["desde", "legislador"]).reset_index(drop=True)


def duplicados_probables(hist: pd.DataFrame, fecha: dt.date) -> list[tuple[str, str]]:
    """Pares de filas activas la MISMA fecha que parecen la misma persona.

    Dos legisladores distintos no pueden tener claves donde una esté contenida en
    la otra: `ACUNA JUAN KUNZ` dentro de `ACUNA ERWIN JUAN KUNZ` no son dos
    diputados, es uno con dos `legislador_id` en la canónica según la grafía traiga
    o no los segundos nombres. Esto **no se corrige acá** —la resolución de
    entidades es de `datos/canonica`— pero se lista, porque es la explicación de
    por qué un año da más de 257 bancas.
    """
    f = pd.Timestamp(fecha)
    act = hist[(pd.to_datetime(hist["desde"]) <= f) & (pd.to_datetime(hist["hasta"]) >= f)]
    act = act.drop_duplicates("legislador_id")[["legislador_id", "legislador", "clave"]]
    filas = [(r.legislador_id, r.legislador,
              frozenset(t for t in str(r.clave).split() if len(t) > 1))
             for r in act.itertuples()]
    pares = []
    for i in range(len(filas)):
        for j in range(i + 1, len(filas)):
            a, b = filas[i], filas[j]
            if a[2] and b[2] and a[2] != b[2] and (a[2] <= b[2] or b[2] <= a[2]):
                pares.append((a[1], b[1]))
    return pares


def verificar(hist: pd.DataFrame) -> int:
    """Controles que cortan: si esto no cierra, el archivo no sirve."""
    problemas = 0
    for col in COLUMNAS:
        if col not in hist.columns:
            logger.error("falta la columna %s", col); problemas += 1
    d = pd.to_datetime(hist["desde"], errors="coerce")
    h = pd.to_datetime(hist["hasta"], errors="coerce")
    if int((h < d).sum()):
        logger.error("%d filas con hasta < desde", int((h < d).sum())); problemas += 1
    if int(d.isna().sum()) or int(h.isna().sum()):
        logger.error("hay fechas que no parsean"); problemas += 1

    # dos tramos del mismo legislador no se pueden pisar
    x = hist.assign(d=d, h=h).sort_values(["legislador_id", "d"])
    mismo = x["legislador_id"].eq(x["legislador_id"].shift())
    solapes = int((mismo & (x["d"] <= x["h"].shift())).sum())
    if solapes:
        logger.error("%d tramos solapados dentro del mismo legislador", solapes); problemas += 1

    print("\n=== bancas reconstruidas al 1 de julio de cada año ===")
    print("  año  activos  exceso  de eso, duplicados de la canónica")
    todos_los_pares: set[tuple[str, str]] = set()
    for anio in range(int(d.dt.year.min()), int(h.dt.year.max()) + 1):
        f = dt.date(anio, 7, 1)
        ts = pd.Timestamp(f)
        n = int(((d <= ts) & (h >= ts)).sum())
        if n == 0:
            print(f"  {anio}   {n:6d}       -   (la canónica no tiene actas cubriendo esta fecha)")
            continue
        exceso = n - BANCAS
        pares = duplicados_probables(hist, f) if exceso > 0 else []
        todos_los_pares.update(pares)
        # cada PAR duplicado suma exactamente una banca de más: se cuentan pares,
        # no ids. (Contar ids duplicaría la explicación y taparía el residuo.)
        marca = ""
        if exceso > 0:
            resto = exceso - len(pares)
            marca = (f"  {exceso:+4d}   {len(pares):4d} pares dup."
                     f"   resto {resto:+3d} (recambio real)")
            if resto > BANCAS * 0.05:
                marca += "  <-- residuo grande, mirar"
                problemas += 1
        print(f"  {anio}   {n:6d}{marca}")
    if todos_los_pares:
        ruta = _RAIZ / "Archivos_Borrar" / "duplicados_entity_resolution_diputados.csv"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(sorted(todos_los_pares), columns=["nombre_a", "nombre_b"]).to_csv(
            ruta, index=False, encoding="utf-8-sig")
        print(f"\n  {len(todos_los_pares)} pares de nombres que parecen la misma persona "
              f"con dos legislador_id.\n  Es de `datos/canonica` (entity resolution), "
              f"no de acá. Lista -> {ruta}")
    return problemas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true", help="construye y sólo controla")
    args = ap.parse_args(argv)
    # stream=sys.stdout a propósito: por defecto logging escribe en stderr, y
    # PowerShell pinta de ROJO todo lo que un proceso manda por stderr —incluido
    # un INFO de avance— y encima lo envuelve en un NativeCommandError. Una
    # corrida sana parecía estar fallando. Con stdout, `| Tee-Object` alcanza y
    # no hace falta el `2>&1`.
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

    hist = construir()
    problemas = verificar(hist)
    if args.verificar:
        logger.info("sólo verificación: no se escribió nada")
        return 1 if problemas else 0
    if problemas:
        logger.error("%d controles fallaron: NO se escribe el archivo", problemas)
        return 1
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    hist.to_csv(SALIDA, index=False, encoding="utf-8-sig")
    logger.info("-> %s (%d filas, %d legisladores)", SALIDA, len(hist),
                hist["legislador_id"].nunique())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
