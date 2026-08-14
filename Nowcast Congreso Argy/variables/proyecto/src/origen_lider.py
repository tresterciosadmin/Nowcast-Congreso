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
# El conjunto oficialista = NÚCLEO ∪ ALIADOS (ver NUCLEO abajo). Se deja 3-tuplas
# porque varios consumidores desempaquetan (desde, hasta, ofi); el split núcleo/aliado
# va en la lista paralela NUCLEO para no romper esa firma.
GOBIERNOS = [
    ("1900-01-01", "2015-12-10", {"KIRCHNERISMO"}),                 # Néstor/CFK
    ("2015-12-10", "2019-12-10", {"PRO", "RADICALISMO", "CC"}),     # Cambiemos (Macri)
    ("2019-12-10", "2023-12-10", {"KIRCHNERISMO"}),                 # Frente de Todos (A. Fernández)
    ("2023-12-10", "2100-01-01", {"LLA", "PRO"}),                   # La Libertad Avanza (Milei) + PRO
]
# NÚCLEO (partido de gobierno) dentro de cada conjunto oficialista, ALINEADO 1:1 con
# GOBIERNOS. Lo que está en el conjunto oficialista pero NO en el núcleo = ALIADO.
# Decisión de Valle (2026-08-14): distinguir el partido propio de sus aliados, porque
# no se comportan igual — LLA no acompaña la agenda regulatoria de PRO aunque sea aliado
# (la categoría "OFICIALISMO" vieja mezclaba PRO con LLA y daba señales absurdas).
NUCLEO = [
    {"KIRCHNERISMO"},   # Néstor/CFK: sin aliados con etiqueta propia
    {"PRO"},            # Macri: núcleo PRO; aliados = RADICALISMO, CC (Cambiemos)
    {"KIRCHNERISMO"},   # Frente de Todos: sin aliados con etiqueta propia
    {"LLA"},            # Milei: núcleo LLA; aliado = PRO
]
# PRO aliado de Milei (Valle 2026-08-09): PRO acompaña la agenda del gobierno en el
# Congreso pero NO es el partido de gobierno. Matiz sin resolver: la alianza se consolidó
# DURANTE 2024, no desde el 10-dic-2023; los votos PRO de los primeros meses de Milei
# quedan etiquetados como aliado aunque el acuerdo todavía no estaba cerrado. Se deja así
# por ahora (la tabla usa los recambios del 10-dic como únicos cortes); afinar si hace ruido.


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
    """True si el linaje gobernaba (núcleo O aliado) en esa fecha; False si no;
    None si sin dato. (Sin cambios de contrato: sigue agrupando núcleo+aliados.)"""
    code = _linaje_code(linaje)
    if code is None or pd.isna(fecha):
        return None
    for desde, hasta, ofi in GOBIERNOS:
        if pd.Timestamp(desde) <= fecha < pd.Timestamp(hasta):
            return code in ofi
    return None


def clase_oficialismo(linaje, fecha):
    """Distingue el partido de gobierno de sus aliados en esa fecha:
      'NUCLEO'  -> partido propio de gobierno (LLA en Milei, PRO en Macri, ...)
      'ALIADO'  -> bloque oficialista NO-núcleo (PRO en Milei, UCR/CC en Macri, ...)
      None      -> opositor o sin dato.
    Es el refinamiento de `oficialista_por_fecha` (que devuelve True para núcleo Y aliado)."""
    code = _linaje_code(linaje)
    if code is None or pd.isna(fecha):
        return None
    for (desde, hasta, ofi), nuc in zip(GOBIERNOS, NUCLEO):
        if pd.Timestamp(desde) <= fecha < pd.Timestamp(hasta):
            if code in nuc:
                return "NUCLEO"
            if code in ofi:
                return "ALIADO"
            return None
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
        # AUTORIDADES primero (trae la columna `cargo` con Presidente/Vice/Secretario:
        # es la que destraba lider_pdte_comision). `comisiones_integrantes` queda de
        # fallback: es la nómina completa pero SIN rol. Bajar con
        # `python variables/proyecto/src/bajar_autoridades_comisiones.py`.
        "comis": (_pq(exp_clean / "comisiones_autoridades.parquet")
                  if (exp_clean / "comisiones_autoridades.parquet").exists()
                  else _pq(exp_clean / "comisiones_integrantes.parquet")),
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
    """nombres_norm de jefes de bloque. Une DOS fuentes (sin período aún, v1):
      1. `jefes_bloque_oficial.csv` — SNAPSHOTS de la web oficial de Diputados,
         que marca "Presidente" en cada bloque. Lo genera (y acumula)
         `scrape_jefes_bloque.py`; cubre TODOS los bloques del período vigente
         sin curación manual. Correrlo ~1×/mes construye la serie hacia adelante.
      2. `jefes_bloque.csv` — curación MANUAL para el histórico 2008-2025, que
         no tiene fuente estructurada (ver README del módulo)."""
    TRAMOS: dict[str, list] = {}
    fuentes = []
    for f, etiqueta in ((jefes_csv.parent / "jefes_bloque_oficial.csv", "oficial"),
                        (jefes_csv, "curado")):
        if not f.exists():
            continue
        df = pd.read_csv(f, dtype=str, encoding="utf-8-sig", comment="#")
        col = next((c for c in df.columns if "nombre" in c.lower()), df.columns[0])
        n = 0
        for _, r in df.dropna(subset=[col]).iterrows():
            desde = str(r.get("desde") or "").strip() or "1900-01-01"
            hasta = str(r.get("hasta") or "").strip() or "2100-01-01"
            TRAMOS.setdefault(_norm(r[col]), []).append((desde, hasta))
            n += 1
        fuentes.append(f"{etiqueta}={n}")
    if not TRAMOS:
        logger.warning("sin jefes de bloque (ni oficial ni curado): "
                       "lider_jefe_bloque = 0. Correr scrape_jefes_bloque.py")
    else:
        logger.info("jefes de bloque: %d nombres, %d tramos (%s)", len(TRAMOS),
                    sum(len(v) for v in TRAMOS.values()), ", ".join(fuentes))
    return TRAMOS


def _clave_nom(nombre_norm: str) -> frozenset:
    """Tokens del nombre sin partículas, para matching tolerante al 2º nombre.
    El CKAN escribe 'ROSSI, AGUSTIN OSCAR' y el roster curado 'ROSSI, AGUSTIN'."""
    _PART = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "E", "VAN", "VON", "DI", "DA"}
    limpio = "".join(c if c.isalpha() else " " for c in str(nombre_norm))
    return frozenset(t for t in limpio.split() if len(t) > 1 and t not in _PART)


def _es_jefe_en(tramos: dict, nombre_norm: str, fecha, _cache: dict = {}) -> bool:
    """TIME-AWARE: ¿era jefe de bloque a la FECHA del proyecto? Sin fecha (o sin
    tramos) → False, para no inflar la señal atribuyendo jefaturas fuera de
    período (caveat 2026-07-30: un ex jefe contaba en TODOS sus proyectos).

    Matching por SUBCONJUNTO de tokens (2026-07-30): el nombre del roster debe
    estar contenido en el del autor o viceversa ('ROSSI AGUSTIN' ⊂ 'ROSSI
    AGUSTIN OSCAR'), y solo si el candidato es ÚNICO — así no se unen homónimos
    (ej. 'SOLA, FELIPE' vs 'SOLARI QUINTANA'; 'GONZALEZ' a secas)."""
    if not tramos or pd.isna(fecha):
        return False
    key = tramos.get(nombre_norm)
    if key is None:
        if nombre_norm not in _cache:
            toks = _clave_nom(nombre_norm)
            cands = [v for k, v in tramos.items()
                     if (c := _clave_nom(k)) and (c <= toks or toks <= c)]
            _cache[nombre_norm] = cands[0] if len(cands) == 1 else []
        key = _cache[nombre_norm]
    f = str(pd.Timestamp(fecha).date())
    return any(d <= f <= h for d, h in (key or ()))


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
    exp["clase_ofi"] = [
        clase_oficialismo(lin, f) for lin, f in zip(exp["autor_linaje"], exp["fecha"])]

    def _origen(r):
        if r["es_ejecutivo"]:
            return "EJECUTIVO"
        if r["clase_ofi"] == "NUCLEO":
            return "OFICIALISMO"     # partido propio de gobierno
        if r["clase_ofi"] == "ALIADO":
            return "ALIADOS"         # aliado oficialista (PRO en Milei, UCR/CC en Macri)
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

    # --- jefe de bloque (TIME-AWARE: solo cuenta si presidía a la fecha) ---
    jefes = _jefes_bloque(jefes_csv)
    exp["lider_jefe_bloque"] = [
        _es_jefe_en(jefes, nn, f) for nn, f in zip(exp["autor_nn"], exp["fecha"])]

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
