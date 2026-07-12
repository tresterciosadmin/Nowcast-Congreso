"""variables/proyecto - ORIGEN y LIDERAZGO por proyecto (feature store, paso 2).

Segmenta cada proyecto de ley por TIPO, porque no juega el mismo torneo un
proyecto del Poder Ejecutivo, uno de un jefe de bloque oficialista o uno de un
diputado de a pie de la oposición. Produce dos rasgos que el embudo consume:

  origen ∈ {EJECUTIVO, OFICIALISMO, OPOSICION, DESCONOCIDO}
    - EJECUTIVO  : el proyecto lo manda el PE (tipo MENSAJE).
    - OFICIALISMO/OPOSICION : según el LINAJE del bloque del autor en la FECHA de
      presentación vs. quién gobernaba (CFK → Macri → A.Fernández → Milei).
    - DESCONOCIDO: no se pudo emparejar el autor con un legislador/bloque.

  lider (bool) = jefe_bloque OR pdte_comision OR alto_productor
    - jefe_bloque   : el autor figura en data/jefes_bloque.csv para ese período (CURADO).
    - pdte_comision : el autor preside una comisión a la que se giró el proyecto
      (de comisiones_integrantes, si trae el rol; defensivo).
    - alto_productor: nº de leyes sancionadas de su autoría ANTES del año del
      proyecto (walk-forward, sin leakage) ≥ UMBRAL_PRODUCTOR.

DEFINICIÓN DE LÍDER = PROVISORIA (decisión de Valle 2026-07-12): jefe de bloque +
presidente de comisión + alto productor. Anotado en ESTADO para que el Claude de
Franco la revise más adelante.

Insumos (contratos de otros módulos; se consumen, no se editan):
  datos/expedientes/data/clean/{expedientes,expedientes_giros,expedientes_leyes}.parquet
  variables/legislador/data/{legisladores.csv, legislador_bloques.parquet}
  datos/expedientes/data/clean/comisiones_integrantes.parquet (opcional)
  variables/proyecto/data/jefes_bloque.csv (curado, opcional)

Salida (contrato estable): variables/proyecto/data/features_proyecto.parquet
  proyecto_id, anio, origen, oficialista, autor_linaje, match_autor,
  lider, lider_jefe_bloque, lider_pdte_comision, lider_alto_productor

CLI:  python variables/proyecto/src/origen_lider.py

4 directivas: errores específicos, parsing defensivo (columnas por nombre,
tolerante a NA/archivos faltantes), logging estructurado.
"""
from __future__ import annotations

import logging
import os
import unicodedata
from pathlib import Path

import pandas as pd

logger = logging.getLogger("origen_lider")

UMBRAL_PRODUCTOR = 3   # leyes previas de su autoría para contar como "alto productor"

# Ventanas de gobierno: (desde inclusive, hasta exclusive, linajes oficialistas).
# Fechas de recambio presidencial (10-dic). Linajes = los de datos/canonica.
GOBIERNOS = [
    ("1900-01-01", "2015-12-10", {"KIRCHNERISMO"}),                 # Néstor/CFK
    ("2015-12-10", "2019-12-10", {"PRO", "RADICALISMO", "CC"}),     # Cambiemos (Macri)
    ("2019-12-10", "2023-12-10", {"KIRCHNERISMO"}),                 # Frente de Todos (A. Fernández)
    ("2023-12-10", "2100-01-01", {"LLA"}),                          # La Libertad Avanza (Milei)
]


def _norm(s) -> str:
    """Normaliza un nombre: sin acentos, mayúsculas, sin puntuación, 'APELLIDO NOMBRE'.
    Maneja el formato 'APELLIDO, Nombre' -> 'APELLIDO NOMBRE'."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    t = str(s).strip()
    if "," in t:                       # 'APELLIDO, Nombre' -> 'APELLIDO Nombre'
        ap, _, no = t.partition(",")
        t = f"{ap} {no}"
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t)
    return " ".join(t.upper().split())


def _linaje_code(linaje) -> str | None:
    """Mapea el linaje del padrón (con nombres largos y sufijos, ej.
    'FdT-UxP (kirchnerismo)', 'RADICALISMO', 'LA LIBERTAD AVANZA') a un CÓDIGO
    estable, robusto a variantes. El orden importa (PROGRESISMO antes que PRO)."""
    t = _norm(linaje)  # MAYÚSCULAS, sin acentos ni puntuación, con espacios
    if not t:
        return None
    if "KIRCHNER" in t or "FDT" in t or "UXP" in t:
        return "KIRCHNERISMO"
    if "LIBERTAD AVANZA" in t or t == "LLA":
        return "LLA"
    if "RADICAL" in t or "UCR" in t:
        return "RADICALISMO"
    if "COALICION CIVICA" in t or "ARI" in t.split():
        return "CC"
    if "PROGRESISMO" in t:
        return "PROGRESISMO"
    if "PERONISMO FEDERAL" in t:
        return "PERONISMO_FEDERAL"
    if "FRENTE RENOVADOR" in t or "MASSISMO" in t:
        return "MASSISMO"
    if "PRO" in t.split() or "PROPUESTA REPUBLICANA" in t:
        return "PRO"
    if "IZQUIERDA" in t:
        return "IZQUIERDA"
    return "OTRO"


def oficialista_por_fecha(linaje, fecha):
    """True si el linaje gobernaba en esa fecha; False si no; None si sin dato."""
    code = _linaje_code(linaje)
    if code is None or pd.isna(fecha):
        return None
    for desde, hasta, ofi in GOBIERNOS:
        if pd.Timestamp(desde) <= fecha < pd.Timestamp(hasta):
            return code in ofi
    return None


# --------------------------------------------------------------------------- #
def cargar(exp_clean: Path, leg_data: Path) -> dict:
    def _pq(p):
        return pd.read_parquet(p) if p.exists() else None
    exp = _pq(exp_clean / "expedientes.parquet")
    if exp is None:
        raise FileNotFoundError(f"falta expedientes.parquet en {exp_clean}")
    return {
        "exp": exp,
        "giros": _pq(exp_clean / "expedientes_giros.parquet"),
        "leyes": _pq(exp_clean / "expedientes_leyes.parquet"),
        "comis": _pq(exp_clean / "comisiones_integrantes.parquet"),
        "legis": pd.read_csv(leg_data / "legisladores.csv", dtype=str, encoding="utf-8-sig")
                 if (leg_data / "legisladores.csv").exists() else None,
        "leg_bloques": _pq(leg_data / "legislador_bloques.parquet"),
    }


def _mapa_autor_linaje(legis: pd.DataFrame | None, leg_bloques: pd.DataFrame | None):
    """(nombre_norm) -> lista de (anio_desde, anio_hasta, linaje) del legislador."""
    if legis is None or leg_bloques is None:
        return {}
    legis = legis.copy()
    legis["nn"] = legis["nombre"].map(_norm)
    id2nn = dict(zip(legis["legislador_id"], legis["nn"]))
    lb = leg_bloques.copy()
    for c in ("anio_desde", "anio_hasta"):
        lb[c] = pd.to_numeric(lb[c], errors="coerce")
    lb["nn"] = lb["legislador_id"].map(id2nn)
    mapa: dict[str, list] = {}
    for _, r in lb.dropna(subset=["nn"]).iterrows():
        mapa.setdefault(r["nn"], []).append(
            (r["anio_desde"], r["anio_hasta"], r.get("linaje")))
    return mapa


def _linaje_autor(nombre_norm: str, anio: float, mapa: dict):
    """Linaje del bloque del autor en el año del proyecto (ventana [desde,hasta])."""
    tramos = mapa.get(nombre_norm)
    if not tramos or pd.isna(anio):
        return None
    # preferimos el tramo que contiene el año; si ninguno, el más cercano
    contiene = [lin for d, h, lin in tramos if pd.notna(d) and d <= anio <= (h if pd.notna(h) else d)]
    if contiene:
        return contiene[0]
    cercano = min(tramos, key=lambda t: min(abs(anio - (t[0] or anio)), abs(anio - (t[1] or anio))))
    return cercano[2]


def _set_pdte_comision(comis: pd.DataFrame | None):
    """(nombre_norm, comision_norm) presidentes, si comisiones_integrantes trae el rol."""
    if comis is None:
        return set(), False
    cols = {c.lower(): c for c in comis.columns}
    col_rol = next((cols[c] for c in cols if c in ("rol", "cargo", "caracter")), None)
    col_nom = next((cols[c] for c in cols if "nombre" in c or "legislador" in c or c == "apellido"), None)
    col_com = next((cols[c] for c in cols if "comis" in c), None)
    if not (col_rol and col_nom and col_com):
        logger.warning("comisiones_integrantes sin rol/nombre/comisión: salteo pdte_comision")
        return set(), False
    df = comis[comis[col_rol].astype(str).str.contains("PRESID", case=False, na=False)]
    s = {(_norm(n), _norm(c)) for n, c in zip(df[col_nom], df[col_com])}
    return s, True


def _jefes_bloque(jefes_csv: Path):
    """nombres_norm de jefes de bloque (curado). Sin período por ahora (v1)."""
    if not jefes_csv.exists():
        logger.warning("no hay jefes_bloque.csv: lider_jefe_bloque = 0 (a curar)")
        return set()
    df = pd.read_csv(jefes_csv, dtype=str, encoding="utf-8-sig", comment="#")
    col = next((c for c in df.columns if "nombre" in c.lower()), df.columns[0])
    return {_norm(x) for x in df[col].dropna()}


def construir_features(dfs: dict, jefes_csv: Path) -> pd.DataFrame:
    exp = dfs["exp"].copy()
    exp["proyecto_id"] = exp["proyecto_id"].astype(str)
    if "tipo" in exp.columns:
        es_ley = exp["tipo"].str.contains("LEY", case=False, na=False)
        exp = exp[es_ley]
    exp["fecha"] = pd.to_datetime(exp.get("fecha_publicacion"), errors="coerce")
    exp["anio"] = exp["fecha"].dt.year
    exp["autor_nn"] = exp.get("autor").map(_norm) if "autor" in exp.columns else ""
    exp["es_ejecutivo"] = exp.get("tipo", "").astype(str).str.contains("MENSAJE", case=False, na=False)

    mapa = _mapa_autor_linaje(dfs.get("legis"), dfs.get("leg_bloques"))
    exp["autor_linaje"] = [
        _linaje_autor(nn, an, mapa) for nn, an in zip(exp["autor_nn"], exp["anio"])]
    exp["match_autor"] = exp["autor_linaje"].notna()
    exp["oficialista"] = [
        oficialista_por_fecha(lin, f) for lin, f in zip(exp["autor_linaje"], exp["fecha"])]

    def _origen(r):
        if r["es_ejecutivo"]:
            return "EJECUTIVO"
        if r["oficialista"] is True:
            return "OFICIALISMO"
        if r["oficialista"] is False:
            return "OPOSICION"
        return "DESCONOCIDO"
    exp["origen"] = exp.apply(_origen, axis=1)

    # --- alto productor: nº de leyes previas del autor (walk-forward) ---
    exp["lider_alto_productor"] = False
    leyes = dfs.get("leyes")
    if leyes is not None and "proyecto_id" in leyes.columns:
        sanc_ids = set(leyes["proyecto_id"].astype(str))
        san = exp[exp["proyecto_id"].isin(sanc_ids)][["autor_nn", "anio"]].dropna()
        # para cada (autor, año) cuántas leyes suyas hubo en años ESTRICTAMENTE previos
        conteo = san.groupby(["autor_nn", "anio"]).size().reset_index(name="n")
        acum: dict[str, list] = {}
        for _, r in conteo.iterrows():
            acum.setdefault(r["autor_nn"], []).append((r["anio"], r["n"]))
        def _previas(nn, anio):
            if pd.isna(anio) or nn not in acum:
                return 0
            return sum(n for a, n in acum[nn] if a < anio)
        exp["leyes_previas_autor"] = [_previas(nn, an) for nn, an in zip(exp["autor_nn"], exp["anio"])]
        exp["lider_alto_productor"] = exp["leyes_previas_autor"] >= UMBRAL_PRODUCTOR

    # --- presidente de comisión (defensivo) ---
    pdtes, hay_rol = _set_pdte_comision(dfs.get("comis"))
    exp["lider_pdte_comision"] = False
    if hay_rol and dfs.get("giros") is not None:
        g = dfs["giros"].copy()
        g["proyecto_id"] = g["proyecto_id"].astype(str)
        g["cn"] = g.get("comision").map(_norm) if "comision" in g.columns else ""
        com_por_proy = g.groupby("proyecto_id")["cn"].apply(set).to_dict()
        def _es_pdte(pid, nn):
            for cn in com_por_proy.get(pid, ()):
                if (nn, cn) in pdtes:
                    return True
            return False
        exp["lider_pdte_comision"] = [
            _es_pdte(pid, nn) for pid, nn in zip(exp["proyecto_id"], exp["autor_nn"])]

    # --- jefe de bloque (curado) ---
    jefes = _jefes_bloque(jefes_csv)
    exp["lider_jefe_bloque"] = exp["autor_nn"].isin(jefes) if jefes else False

    exp["lider"] = (exp["lider_alto_productor"] | exp["lider_pdte_comision"]
                    | exp["lider_jefe_bloque"])

    cols = ["proyecto_id", "anio", "origen", "oficialista", "autor_linaje", "match_autor",
            "lider", "lider_jefe_bloque", "lider_pdte_comision", "lider_alto_productor"]
    return exp[cols]


def resumen(feat: pd.DataFrame) -> None:
    n = len(feat)
    print(f"\n=== features_proyecto: {n:,} proyectos de ley ===")
    print("  match autor->bloque: {:.1f}%".format(100 * feat["match_autor"].mean()))
    print("  origen:", feat["origen"].value_counts().to_dict())
    print("  líderes: {:.1f}%  (jefe {:.1f} · pdte_com {:.1f} · productor {:.1f})".format(
        100 * feat["lider"].mean(), 100 * feat["lider_jefe_bloque"].mean(),
        100 * feat["lider_pdte_comision"].mean(), 100 * feat["lider_alto_productor"].mean()))


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = Path(__file__).resolve().parents[3]
    exp_clean = Path(os.environ.get("EXP_CLEAN", root / "datos" / "expedientes" / "data" / "clean"))
    leg_data = Path(os.environ.get("LEG_DATA", root / "variables" / "legislador" / "data"))
    out = Path(os.environ.get("OUT", root / "variables" / "proyecto" / "data"))
    out.mkdir(parents=True, exist_ok=True)
    jefes_csv = out / "jefes_bloque.csv"
    dfs = cargar(exp_clean, leg_data)
    feat = construir_features(dfs, jefes_csv)
    feat.to_parquet(out / "features_proyecto.parquet", index=False)
    resumen(feat)
    print(f"\n  -> {out / 'features_proyecto.parquet'}")


if __name__ == "__main__":
    main()
