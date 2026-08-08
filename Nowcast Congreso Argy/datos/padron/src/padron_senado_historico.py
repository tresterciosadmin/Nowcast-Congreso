"""Padrón HISTÓRICO del Senado: quién ocupaba cada banca en cada fecha.

POR QUÉ HACE FALTA
------------------
Para modelar la cadena `cámara de origen -> cámara revisora` hay que poder
revivir una votación del pasado, y para eso se necesita la composición del
cuerpo EN ESA FECHA, no la de hoy. Diputados ya lo tiene: `padron_diputados.csv`
son 1.454 tramos con `desde`-`hasta`. El Senado sólo tenía la foto de los 72
vigentes, así que la cadena no se podía backtestear.

LO QUE SE APROVECHA (no hay que bajar nada de nuevo)
    datos/senado/data/padron_bloques_senado.csv   291 tramos, 168 senadores,
        2017-2025, reconstruidos de Wikipedia el 2026-07-02 (decisión de Franco
        del 01-07: Wikipedia + validación contra snapshots propios).
    datos/padron/data/padron_senado.csv           los 72 vigentes, fuente
        oficial, con mandato hasta 2031.
    datos/padron/data/senado_linaje_manual.csv    override curado a mano
        (opcional; si no está, se sigue sin él).

DECISIONES
    - **Precedencia:** ante el mismo senador y ventana solapada, manda la fuente
      OFICIAL sobre Wikipedia. Wikipedia aporta la historia que la oficial no
      tiene; la oficial aporta la exactitud del presente.
    - **Tramos consecutivos con el MISMO bloque se fusionan.** Los anexos de
      Wikipedia son por período (2017-2019, 2019-2021...), así que un senador
      con un mandato de 6 años aparece partido en 3 filas idénticas. Sin
      fusionar, un `desde`-`hasta` no representa un mandato sino una ventana de
      scraping.
    - **El linaje se calcula con la fecha de inicio del tramo**, usando la misma
      función que la canónica (`_linaje_vec`): el mismo bloque significa cosas
      distintas en épocas distintas (ADR-0005, ventanas del JUSTICIALISTA).
    - **Se importa la implementación canónica de clave/id/linaje**, no se copia.
      Una copia se desincroniza en silencio y los joins empiezan a fallar por
      una tilde. Si `entity_resolution` cambia, esto cambia con él.

CONTROL QUE CORTA
    El Senado tiene 72 bancas. Si en alguna fecha el padrón devuelve más, el
    padrón está mal y se avisa fuerte. Es el control que faltó en el intento de
    reparar Diputados por heurística (julio): daba 278 bancas y Buenos Aires 74
    sobre 70, y por eso se abandonó.

CONTRATO DE SALIDA
    datos/padron/data/padron_senado_historico.csv — mismo esquema que
    `padron_diputados.csv`, para que cualquier consumidor trate a las dos
    cámaras igual:
        legislador, clave, legislador_id, camara, distrito, bloque,
        bloque_norm, desde, hasta, bloque_linaje, fuente, nota

USO
    python datos/padron/src/padron_senado_historico.py
    python datos/padron/src/padron_senado_historico.py --verificar
    python datos/padron/src/padron_senado_historico.py --fecha 2019-03-12
    python datos/padron/tests/test_padron_senado_historico.py

En código:
    from padron_senado_historico import composicion_a_fecha
    comp = composicion_a_fecha(df, "2019-03-12")   # 72 filas

Módulo: datos/padron · creado 2026-08-08 (línea Revisión de Comisiones)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s padron_senado_hist: %(message)s",
)
logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
SRC_CANONICA = RAIZ / "datos" / "canonica" / "src"
WIKI = RAIZ / "datos" / "senado" / "data" / "padron_bloques_senado.csv"
VIGENTES = RAIZ / "datos" / "padron" / "data" / "padron_senado.csv"
MANUAL = RAIZ / "datos" / "padron" / "data" / "senado_linaje_manual.csv"
SALIDA = RAIZ / "datos" / "padron" / "data" / "padron_senado_historico.csv"

BANCAS_SENADO = 72

COLUMNAS = ["legislador", "clave", "legislador_id", "camara", "distrito",
            "bloque", "bloque_norm", "desde", "hasta", "bloque_linaje",
            "fuente", "nota"]

sys.path.insert(0, str(SRC_CANONICA))
try:
    from entity_resolution import _bloque_norm, _leg_id, _linaje_vec, _name_key
except ImportError as e:  # pragma: no cover - entorno roto, no lógica
    raise SystemExit(
        f"no se pudo importar la resolución canónica desde {SRC_CANONICA}: {e}\n"
        "  este módulo REUSA a propósito clave/id/linaje de datos/canonica para "
        "que los joins entre cámaras no se rompan por una tilde."
    )


def _leer_csv(path: Path, que: str, obligatorio: bool = True) -> Optional[pd.DataFrame]:
    if not path.exists():
        if obligatorio:
            raise FileNotFoundError(f"falta {que}: {path}")
        logger.warning("sin %s (%s): se sigue sin él", que, path.name)
        return None
    # utf-8-sig: los CSV del proyecto se guardan con BOM para abrir en Excel-ES
    df = pd.read_csv(path, encoding="utf-8-sig", comment="#")
    logger.info("leído %-32s %5d filas", path.name, len(df))
    return df


def _tramos_wiki(df: pd.DataFrame) -> pd.DataFrame:
    faltan = {"senador", "provincia", "bloque", "desde", "hasta"} - set(df.columns)
    if faltan:
        raise ValueError(f"{WIKI.name} sin columnas esperadas: {sorted(faltan)}")
    out = pd.DataFrame({
        "legislador": df["senador"].astype(str).str.strip(),
        "distrito": df["provincia"].astype(str).str.strip(),
        "bloque": df["bloque"].astype(str).str.strip(),
        "desde": df["desde"], "hasta": df["hasta"],
        "fuente": df.get("fuente", "wikipedia"),
        "nota": df.get("nota", ""),
    })
    out["prioridad"] = 1  # Wikipedia cede ante la oficial
    return out


def _tramos_vigentes(df: pd.DataFrame) -> pd.DataFrame:
    faltan = {"legislador", "distrito", "bloque", "desde", "hasta"} - set(df.columns)
    if faltan:
        raise ValueError(f"{VIGENTES.name} sin columnas esperadas: {sorted(faltan)}")
    out = df[["legislador", "distrito", "bloque", "desde", "hasta"]].copy()
    out["fuente"] = df.get("fuente", "oficial:nomina_senado")
    out["nota"] = df.get("nota", "")
    out["prioridad"] = 0  # la oficial manda
    return out


def _reconciliar_claves(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica la clave de la misma persona escrita distinto en cada fuente.

    EL PROBLEMA, medido el 2026-08-08: Wikipedia usa el nombre de uso
    ("Eduardo Vischi") y la nómina oficial el nombre completo
    ("VISCHI, ALEJANDRO EDUARDO"). `_name_key` compara el conjunto de tokens, así
    que salen dos claves para el mismo senador y el padrón devolvía **90 bancas
    al 12-jun-2024**, en un año sin renovación. Eran 21 pares duplicados.

    LA REGLA — el apellido MANDA, y no alcanza con compartir nombres de pila.
    La nómina oficial escribe "APELLIDO, Nombres", así que la coma marca dónde
    termina el apellido. Se fusiona sólo si:
      1. todos los tokens del APELLIDO oficial están en el nombre de Wikipedia, y
      2. comparten al menos un nombre de pila.

    POR QUÉ TAN ESTRICTO: una regla de "comparten 2 tokens" fusionaría
    *PAGOTTO, Carlos Juan* con *Juan Carlos Romero*, y *BENSUSAN, Daniel Pablo*
    con *Pablo Daniel Blanco*. Son cuatro senadores distintos. Un merge malo
    inventa un legislador que nunca existió y le adjudica votos ajenos.

    Lo ambiguo (una forma corta que matchea a dos oficiales) NO se fusiona: se
    reporta para curaduría humana, como el override de linaje.
    """
    con_coma = df[df["legislador"].astype(str).str.contains(",")]
    sin_coma = df[~df["legislador"].astype(str).str.contains(",")]
    if con_coma.empty or sin_coma.empty:
        return df

    oficiales = {}
    for nombre in con_coma["legislador"].astype(str).unique():
        ape, _, pila = nombre.partition(",")
        t_ape = set(_name_key(ape).split())
        t_pila = set(_name_key(pila).split())
        if t_ape:
            oficiales[_name_key(nombre)] = (t_ape, t_pila)

    mapa, ambiguos = {}, []
    for clave_w in sin_coma["clave"].unique():
        tokens = set(str(clave_w).split())
        candidatos = [
            c for c, (t_ape, t_pila) in oficiales.items()
            if t_ape <= tokens and (t_pila & tokens)
        ]
        if len(candidatos) == 1 and candidatos[0] != clave_w:
            mapa[clave_w] = candidatos[0]
        elif len(candidatos) > 1:
            ambiguos.append((clave_w, candidatos))

    if ambiguos:
        logger.warning("%d nombres ambiguos, NO se fusionan (curaduría manual):",
                       len(ambiguos))
        for c, cands in ambiguos[:10]:
            logger.warning("   %s -> %s", c, cands)

    if not mapa:
        return df

    logger.info("reconciliadas %d claves duplicadas entre Wikipedia y la nómina oficial",
                len(mapa))
    df = df.copy()
    df["clave"] = df["clave"].replace(mapa)
    df["legislador_id"] = df["clave"].map(_leg_id)
    # El nombre canónico es el más completo: el de la nómina oficial.
    largos = (df.assign(n=df["legislador"].astype(str).str.len())
                .sort_values("n").groupby("clave")["legislador"].last())
    df["legislador"] = df["clave"].map(largos)
    return df


def _fusionar_consecutivos(df: pd.DataFrame, tolerancia_dias: int = 5) -> pd.DataFrame:
    """Une tramos contiguos del mismo senador con el mismo bloque.

    Los anexos de Wikipedia son por período, así que un mandato de 6 años queda
    partido en 3 filas iguales. `tolerancia_dias` cubre el hueco de un día entre
    el 09-12 (hasta) y el 10-12 (desde) del recambio.
    """
    if df.empty:
        return df
    df = df.sort_values(["clave", "bloque_norm", "desde"]).reset_index(drop=True)
    filas, actual = [], None
    for fila in df.to_dict("records"):
        if (actual is not None
                and fila["clave"] == actual["clave"]
                and fila["bloque_norm"] == actual["bloque_norm"]
                and (fila["desde"] - actual["hasta"]).days <= tolerancia_dias):
            if fila["hasta"] > actual["hasta"]:
                actual["hasta"] = fila["hasta"]
                # la fuente más precisa se queda pegada al tramo fusionado
                if fila.get("prioridad", 1) < actual.get("prioridad", 1):
                    actual["fuente"] = fila["fuente"]
                    actual["prioridad"] = fila["prioridad"]
            continue
        if actual is not None:
            filas.append(actual)
        actual = dict(fila)
    filas.append(actual)
    return pd.DataFrame(filas)


def _resolver_solapes(df: pd.DataFrame) -> pd.DataFrame:
    """Si un senador tiene dos tramos que se pisan, gana el de mejor prioridad.

    Pasa entre Wikipedia y la nómina oficial: 43 de los 72 vigentes también
    están en los anexos. Recortamos el tramo de Wikipedia en vez de borrarlo,
    para no perder la historia previa del mismo senador.
    """
    df = df.sort_values(["clave", "prioridad", "desde"]).reset_index(drop=True)
    salida = []
    for _, g in df.groupby("clave", sort=False):
        ocupados: list[tuple[pd.Timestamp, pd.Timestamp]] = []
        for fila in g.to_dict("records"):
            d, h = fila["desde"], fila["hasta"]
            for od, oh in ocupados:
                if d >= od and h <= oh:      # contenido en uno de mejor prioridad
                    d = None
                    break
                if od <= h and d <= oh:      # se pisan: recortamos
                    if d < od:
                        h = min(h, od - pd.Timedelta(days=1))
                    else:
                        d = max(d, oh + pd.Timedelta(days=1))
            if d is None or d > h:
                continue
            fila["desde"], fila["hasta"] = d, h
            ocupados.append((d, h))
            salida.append(fila)
    return pd.DataFrame(salida)


def construir(wiki: pd.DataFrame, vigentes: pd.DataFrame,
              manual: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Arma el padrón histórico completo a partir de las dos fuentes."""
    df = pd.concat([_tramos_wiki(wiki), _tramos_vigentes(vigentes)],
                   ignore_index=True)

    df["desde"] = pd.to_datetime(df["desde"], errors="coerce")
    df["hasta"] = pd.to_datetime(df["hasta"], errors="coerce")
    malas = df["desde"].isna() | df["hasta"].isna() | (df["hasta"] < df["desde"])
    if malas.any():
        logger.warning("%d tramos con fechas ilegibles o invertidas: se descartan",
                       int(malas.sum()))
        df = df[~malas]

    df["clave"] = df["legislador"].map(_name_key)
    df["legislador_id"] = df["clave"].map(_leg_id)
    df["bloque_norm"] = df["bloque"].map(_bloque_norm)
    df["camara"] = "senado"

    # El orden importa: primero se unifica QUIÉN es cada uno, y recién después
    # se resuelven solapes y se fusionan tramos. Al revés, la misma persona con
    # dos claves nunca se pisa consigo misma y ocupa dos bancas a la vez.
    df = _reconciliar_claves(df)
    df = _resolver_solapes(df)
    df = _fusionar_consecutivos(df)

    # El linaje depende de la ÉPOCA del tramo, no sólo del nombre del bloque.
    df["bloque_linaje"] = _linaje_vec(df["bloque_norm"], df["desde"])

    if manual is not None and "clave_norm" in manual.columns and "linaje" in manual.columns:
        ov = manual.dropna(subset=["linaje"])
        mapa = dict(zip(ov["clave_norm"].map(str.strip), ov["linaje"]))
        pisa = df["clave"].isin(mapa)
        if pisa.any():
            df["nota"] = df["nota"].astype("object")
            df.loc[pisa, "bloque_linaje"] = df.loc[pisa, "clave"].map(mapa)
            df.loc[pisa, "nota"] = (df.loc[pisa, "nota"].fillna("").astype(str)
                                    + " linaje: override manual").str.strip()
            logger.info("override manual de linaje aplicado a %d tramos", int(pisa.sum()))

    for c in ("desde", "hasta"):
        df[c] = df[c].dt.strftime("%Y-%m-%d")
    df["nota"] = df["nota"].fillna("")
    return df[COLUMNAS].sort_values(["clave", "desde"]).reset_index(drop=True)


def composicion_a_fecha(df: pd.DataFrame, fecha: str | pd.Timestamp) -> pd.DataFrame:
    """Quiénes ocupaban una banca en esa fecha. Es el uso real del módulo."""
    f = pd.Timestamp(fecha)
    d = pd.to_datetime(df["desde"], errors="coerce")
    h = pd.to_datetime(df["hasta"], errors="coerce")
    return df[(d <= f) & (f <= h)].copy()


def verificar(df: pd.DataFrame) -> int:
    """Controles que cortan. Devuelve la cantidad de problemas encontrados."""
    problemas = 0
    logger.info("tramos: %d | senadores distintos: %d", len(df), df["clave"].nunique())
    logger.info("cobertura: %s -> %s", df["desde"].min(), df["hasta"].max())

    fechas = ["2018-06-14", "2019-03-12", "2020-08-27", "2021-06-24",
              "2023-05-18", "2024-06-12", "2026-08-08"]
    for f in fechas:
        comp = composicion_a_fecha(df, f)
        n, dup = len(comp), int(comp["clave"].duplicated().sum())
        marca = "OK "
        if n > BANCAS_SENADO:
            marca, problemas = "MAL", problemas + 1
        elif n == 0:
            marca, problemas = "VAC", problemas + 1
        elif n < BANCAS_SENADO:
            marca = "inc"  # incompleto: hueco de cobertura, no error de lógica
        logger.info("  %s %s -> %2d bancas (dup: %d)", marca, f, n, dup)
        if dup:
            problemas += 1
            logger.error("     un senador con dos bancas simultáneas: %s",
                         comp[comp["clave"].duplicated(keep=False)]["legislador"].tolist()[:5])

    sin_linaje = int((df["bloque_linaje"] == "OTRO / PROVINCIAL").sum())
    logger.info("tramos en OTRO / PROVINCIAL: %d (%.1f%%)",
                sin_linaje, 100 * sin_linaje / len(df) if len(df) else 0)
    logger.info("linajes:\n%s", df["bloque_linaje"].value_counts().to_string())
    return problemas


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verificar", action="store_true", help="sólo controla, no escribe")
    ap.add_argument("--fecha", help="imprime la composición a esa fecha (AAAA-MM-DD)")
    ap.add_argument("--out", type=Path, default=SALIDA)
    args = ap.parse_args(argv)

    try:
        wiki = _leer_csv(WIKI, "el padrón de bloques del Senado (Wikipedia)")
        vig = _leer_csv(VIGENTES, "la nómina oficial de senadores vigentes")
        man = _leer_csv(MANUAL, "el override manual de linaje", obligatorio=False)
    except (FileNotFoundError, ValueError) as e:
        logger.error("%s", e)
        return 2

    df = construir(wiki, vig, man)
    problemas = verificar(df)

    if args.fecha:
        comp = composicion_a_fecha(df, args.fecha).sort_values(["bloque_linaje", "legislador"])
        print(f"\nComposición del Senado al {args.fecha} — {len(comp)} bancas\n")
        print(comp[["legislador", "distrito", "bloque", "bloque_linaje"]]
              .to_string(index=False, max_colwidth=38))
        print("\nPor linaje:")
        print(comp["bloque_linaje"].value_counts().to_string())

    if args.verificar:
        logger.info("--verificar: no se escribió nada")
        return 1 if problemas else 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    logger.info("escrito: %s (%d tramos)", args.out.name, len(df))
    if problemas:
        logger.error("%d controles fallaron: revisar antes de consumir", problemas)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
