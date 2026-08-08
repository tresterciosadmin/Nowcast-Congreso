"""datos/canonica/src/entity_resolution.py
Resolución de entidades sobre la base canónica.

LEGISLADOR: legislador_id canónico, clave invariante al formato del nombre.

BLOQUE (dos niveles, sin destruir el dato crudo):
  - bloque_norm   : normalización conservadora (mismo bloque escrito distinto).
  - bloque_linaje : agrupación del espacio político en el tiempo (decisión de
                    modelado, documentada en BLOQUES.md; reversible).
"""
from __future__ import annotations
import hashlib, os, re, unicodedata
from pathlib import Path
import pandas as pd

PARTICULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "DA", "DI", "VON", "VAN"}

# --- bloque_norm: SOLO variantes del mismo bloque (formato/abreviatura) ---
BLOQUE_ALIAS = {
    "UNION CIVICA RADICAL": "UCR", "UCR": "UCR", "UCR - UNION CIVICA RADICAL": "UCR",
    "PRO": "PRO", "UNION PRO": "PRO", "PROPUESTA REPUBLICANA": "PRO",
    "COALICION CIVICA": "COALICION CIVICA", "COALICION CIVICA - ARI": "COALICION CIVICA",
    "COALICION CIVICA ARI": "COALICION CIVICA",
    "FTE. DE IZQUIERDA Y DE LOS TRABAJADORES": "FRENTE DE IZQUIERDA",
    "FRENTE DE IZQUIERDA Y DE LOS TRABAJADORES": "FRENTE DE IZQUIERDA",
    "PTS - FRENTE DE IZQUIERDA": "FRENTE DE IZQUIERDA",
    "FRENTE DE IZQUIERDA Y DE TRABAJADORES - UNIDAD": "FRENTE DE IZQUIERDA",
    "FEDERAL UNIDOS POR UNA NUEVA ARGENTINA": "UNIDOS POR UNA NUEVA ARGENTINA",
    "UNIDOS POR UNA NUEVA ARGENTINA": "UNIDOS POR UNA NUEVA ARGENTINA",
    # Sucesión de etiquetas del MISMO frente kirchnerista (caso pedido):
    "FRENTE PARA LA VICTORIA - PJ": "FRENTE PARA LA VICTORIA",
    "FRENTE PARA LA VICTORIA-PJ": "FRENTE PARA LA VICTORIA",  # variante sin espacios (padrón wiki Senado)
    "FRENTE PARA LA VICTORIA": "FRENTE PARA LA VICTORIA",
}

# --- bloque_linaje: espacio político en el tiempo (grueso, documentado) ---
LINAJE = {
    # FdT/UxP: sucesión kirchnerista (FpV -> Frente de Todos -> Unión por la Patria)
    "FRENTE PARA LA VICTORIA": "FdT-UxP (kirchnerismo)",
    "FRENTE DE TODOS": "FdT-UxP (kirchnerismo)",
    "UNION POR LA PATRIA": "FdT-UxP (kirchnerismo)",
    "RADICALISMO": "RADICALISMO", "UCR": "RADICALISMO", "EVOLUCION RADICAL": "RADICALISMO",
    "PRO": "PRO",
    "COALICION CIVICA": "COALICION CIVICA",
    "FRENTE DE IZQUIERDA": "IZQUIERDA", "FTE. DE IZQUIERDA Y DE LOS TRABAJADORES": "IZQUIERDA",
    "PARTIDO OBRERO": "IZQUIERDA", "MST": "IZQUIERDA",
    "LA LIBERTAD AVANZA": "LA LIBERTAD AVANZA",
    # Aliados kirchneristas chicos (decisión del usuario: fundir en FdT-UxP)
    "PERONISMO PARA LA VICTORIA": "FdT-UxP (kirchnerismo)",
    "NUEVO ENCUENTRO": "FdT-UxP (kirchnerismo)",
    "LIBRES DEL SUR": "FdT-UxP (kirchnerismo)",
    # Sub-bloques del FdT-UxP en el Senado (etiquetas del padrón wiki; omisión
    # detectada 2026-07-11: caían en OTRO siendo kirchnerismo puro)
    "UNIDAD CIUDADANA": "FdT-UxP (kirchnerismo)",
    # SOLIDARIDAD E IGUALDAD (SI) -> kirchnerismo por decision de Franco (07-08):
    # termino integrando Unidad Ciudadana. Estaba en OTRO / PROVINCIAL (1.731
    # votos entre sus tres variantes).
    "SOLIDARIDAD E IGUALDAD (SI)": "FdT-UxP (kirchnerismo)",
    "SOLIDARIDAD E IGUALDAD (SI) - ARI (T.D.F)": "FdT-UxP (kirchnerismo)",
    "SOLIDARIDAD E IGUALDAD (SI) - PROYECTO P": "FdT-UxP (kirchnerismo)",
    "SOLIDARIDAD E IGUALDAD": "FdT-UxP (kirchnerismo)",
    "FRENTE NACIONAL Y POPULAR": "FdT-UxP (kirchnerismo)",
    # Bloque de Pichetto post-2019 (misma omisión, lado peronismo federal)
    "PERONISMO REPUBLICANO": "PERONISMO FEDERAL",
    # ---- Reclasificación OTRO/PROVINCIAL (ADR-0005, decisión Franco 2026-07-10) ----
    # Variantes claras de linajes existentes:
    "JUSTICIALISTA-FRENTE PARA LA VICTORIA": "FdT-UxP (kirchnerismo)",  # bloque Sen 2004-2014 (semilla)
    "DE LA CONCERTACION": "FdT-UxP (kirchnerismo)",  # radicales K 2007-2011 (aliado, ver BLOQUES.md)
    "FRENTE PRO": "PRO",
    "A.R.I": "COALICION CIVICA",  # el ARI de Carrió 2001-2007, antecesor directo de la CC
    "UNIDOS POR UNA NUEVA ARGENTINA": "FRENTE RENOVADOR (massismo)",  # UNA (Massa) 2015-2019
    # Linaje NUEVO: PERONISMO FEDERAL (peronismo no kirchnerista; eras verificadas en datos)
    "PERONISTA FEDERAL": "PERONISMO FEDERAL",           # 2005-09 (Villaverde, duhaldismo)
    "PERONISMO FEDERAL": "PERONISMO FEDERAL",           # 2009-11 (Cremer de Busti)
    "JUSTICIALISTA NACIONAL": "PERONISMO FEDERAL",      # 2006-09 (Sarghini)
    "FRENTE PERONISTA": "PERONISMO FEDERAL",            # 2011-23 (Thomas)
    "UNION PERONISTA": "PERONISMO FEDERAL",             # 2008-13 (F. Solá pre-massismo)
    "JUSTICIALISTA 8 DE OCTUBRE": "PERONISMO FEDERAL",  # 2009-21 (J.C. Romero, Salta)
    "SANTA FE FEDERAL": "PERONISMO FEDERAL",            # 2009-21 (Reutemann)
    "CORDOBA FEDERAL": "PERONISMO FEDERAL",             # 2010-25 (schiarettismo)
    "COMPROMISO FEDERAL": "PERONISMO FEDERAL",          # 2013-23 (rodriguezsaaísmo)
    "FRENTE DEL MOVIMIENTO POPULAR": "PERONISMO FEDERAL",  # 2003-07 (Lemme, San Luis)
    "FEDERALISMO Y LIBERACION": "PERONISMO FEDERAL",    # 2005-17 (Menem tardío)
    "PARTIDO UNIDAD FEDERALISTA": "PERONISMO FEDERAL",  # 2001-09 (PAUFE)
    "JUNTOS POR ARGENTINA": "PERONISMO FEDERAL",        # 2013-17 (Giustozzi ex-FR)
    "PRODUCCION Y TRABAJO": "PERONISMO FEDERAL",        # 2005-25 (Basualdo, San Juan)
    "UNIDAD FEDERAL": "PERONISMO FEDERAL",              # 2023 (ex-FdT: Snopek, Vigo, etc.)
    "JUSTICIALISTA SAN LUIS": "PERONISMO FEDERAL",      # rodriguezsaaísmo
    # Linaje NUEVO: PROGRESISMO (progresismo no kirchnerista)
    "PARTIDO SOCIALISTA": "PROGRESISMO",
    "SOCIALISTA": "PROGRESISMO",
    "GEN": "PROGRESISMO",                               # 2010-25 (Stolbizer)
    "FREPASO": "PROGRESISMO",                           # 2001-05
    "UNIDAD POPULAR": "PROGRESISMO",                    # 2011-15 (Lozano, CTA)
    # PROYECTO SUR (Solanas) -> IZQUIERDA por decision de Franco (07-08): es
    # izquierda, no progresismo socialdemocrata. Estaba en PROGRESISMO desde
    # ADR-0005; se mueve junto con sus variantes ("MOVIMIENTO PROYECTO SUR",
    # "BS. AS. PARA TODOS EN PROYECTO SUR"), que caian en OTRO / PROVINCIAL.
    "PROYECTO SUR - UNEN": "IZQUIERDA",                 # Solanas
    "PROYECTO SUR-UNEN": "IZQUIERDA",
    "PROYECTO SUR": "IZQUIERDA",
}

# JUSTICIALISTA a secas: tres animales con el mismo nombre -> ventanas por fecha
# (ADR-0005; eras verificadas: Dip 2001-05 + Sen 2004-08 = PJ unificado;
#  2016-19 = disidencia Bossio/Pichetto; 2024+ = sello del tronco UxP en el Senado)
LINAJE_VENTANAS = {
    "JUSTICIALISTA": [
        ("1900-01-01", "2003-05-25", "PERONISMO FEDERAL"),          # pre-Néstor (Duhalde)
        ("2003-05-25", "2015-12-10", "FdT-UxP (kirchnerismo)"),     # PJ oficialista K
        ("2015-12-10", "2019-12-10", "PERONISMO FEDERAL"),          # Bossio/Pichetto
        ("2019-12-10", "2100-01-01", "FdT-UxP (kirchnerismo)"),     # vuelve al tronco (UxP)
    ],
}

# Frente Renovador: opositor hasta 2019, kirchnerista desde dic-2019 (time-aware)
CUTOFF_FR = "2019-12-10"

# Coalición Juntos por el Cambio / Cambiemos: núcleo + ventana (en Congreso desde dic-2015)
JXC_MIEMBROS = {"UCR", "PRO", "COALICION CIVICA", "EVOLUCION RADICAL"}
CUTOFF_JXC = "2015-12-10"
CUTOFF_JXC_FIN = "2023-12-10"  # tras el recambio 2023 JxC se fragmenta (PRO->LLA, UCR dividida)

def _strip(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper().strip())

def _name_key(nombre):
    s = _strip(nombre).replace(",", " ")
    toks = [t for t in re.split(r"[^A-Z]+", s) if len(t) > 1 and t not in PARTICULAS]
    return " ".join(sorted(set(toks)))

def _leg_id(key):
    return "leg:" + hashlib.md5(key.encode()).hexdigest()[:12] if key else "leg:desconocido"

def _bloque_norm(b):
    s = _strip(b)
    if s.startswith("COALICION CIVICA"):
        return "COALICION CIVICA"
    return BLOQUE_ALIAS.get(s, s)

# IZQUIERDA por PATRON, no por lista (2026-08-07).
# El mapa exacto LINAJE tenia 4 entradas de izquierda y en la canonica hay **13
# variantes** del mismo espacio politico ("PTS-FRENTE DE IZQUIERDA UNIDAD",
# "PARTIDO OBRERO EN EL FRENTE DE IZQUIERDA Y DE TRABAJADORES-U", "MST - FRENTE
# DE IZQUIERDA Y TRABAJADORES UNIDAD"...). El FIT rota la etiqueta cada eleccion,
# asi que una lista exacta se desactualiza sola: todas menos una caian en
# OTRO / PROVINCIAL.
#
# POR QUE IMPORTA (medido en la canonica, era Milei, 333 actas):
#   la izquierda coincide con el kirchnerismo    96,1%
#   con LLA                                       8,1%
#   con OTRO / PROVINCIAL, donde estaba            49,8%  <- azar puro
# OTRO / PROVINCIAL es el cajon de los bloques NEGOCIADORES (los mas sensibles al
# clima segun ADR-0008); el FIT es lo contrario: vota siempre igual y en contra.
# Meterlo ahi ensucia el desvio del grupo y la lectura de bisagras.
#
# NO se funde con FdT-UxP, aunque hoy voten casi igual. El test por gobierno lo
# desmiente: Macri 80,2% · **Alberto (con el K gobernando) 58,3%** · Milei 96,1%.
# Coinciden cuando ambos son oposicion, no por identidad. Linaje propio.
# AUTODETERMINACION Y LIBERTAD (Zamora) entra por EVIDENCIA, no por nombre:
# coincide con el nucleo de izquierda en el **100,0%** de 121 actas.
#
# NO entran, aunque el nombre invite: MOVIMIENTO EVITA (88,9% de coincidencia en
# 54 actas) es kirchnerismo — un movimiento social peronista, no izquierda; la
# coincidencia es coyuntural, el mismo error que se descarto al no fundir el FIT
# con UxP. MOVIMIENTO POPULAR NEUQUINO (38,9%) y FRENTE POPULAR BONAERENSE
# (54,7%) son provinciales y quedan bien donde estan.
_RE_IZQUIERDA = re.compile(
    r"IZQUIERD|PARTIDO OBRERO|\bPTS\b|\bMST\b|BLOQUE DE LOS TRABAJADORES"
    r"|AUTODETERMINACION Y LIBERTAD|PROYECTO SUR", re.I)

# Excepciones: "SOCIALISTA" a secas es el PS (progresismo), no el FIT. Solo entra
# si viene acompanado de una marca del frente de izquierda.
_RE_NO_IZQ = re.compile(r"^PARTIDO SOCIALISTA(?: POPULAR)?$|^SOCIALISTA$", re.I)


def _linaje_vec(bnorm: pd.Series, fecha: pd.Series) -> pd.Series:
    out = bnorm.map(LINAJE).fillna("OTRO / PROVINCIAL")
    # el patron solo RESCATA lo que quedo en OTRO / PROVINCIAL: nunca pisa un
    # linaje ya asignado a mano (el mapa exacto sigue mandando).
    s = bnorm.astype(str)
    es_izq = s.str.contains(_RE_IZQUIERDA, na=False) & ~s.str.contains(_RE_NO_IZQ, na=False)
    out = out.mask(es_izq & out.eq("OTRO / PROVINCIAL"), "IZQUIERDA")
    fe = pd.to_datetime(fecha, errors="coerce")
    fr = bnorm.eq("FRENTE RENOVADOR")
    post = fe >= pd.Timestamp(CUTOFF_FR)
    out = out.mask(fr & post, "FdT-UxP (kirchnerismo)")
    out = out.mask(fr & ~post, "FRENTE RENOVADOR (massismo)")
    # ventanas temporales por bloque (mismo nombre, distintas eras políticas)
    for blo, ventanas in LINAJE_VENTANAS.items():
        es = bnorm.eq(blo)
        if not es.any():
            continue
        for desde, hasta, lin in ventanas:
            out = out.mask(es & (fe >= pd.Timestamp(desde)) & (fe < pd.Timestamp(hasta)), lin)
        # sin fecha no hay ventana aplicable: queda OTRO (conservador, se reporta)
    return out

def main():
    src = Path(os.environ.get("CANON", Path(__file__).resolve().parents[1] / "data" / "clean"))
    out = Path(os.environ.get("OUT", src))
    _root = Path(__file__).resolve()
    for _ in range(3): _root = _root.parent
    borrar = Path(os.environ.get("BORRAR", _root / "Archivos_Borrar"))
    out.mkdir(parents=True, exist_ok=True); borrar.mkdir(parents=True, exist_ok=True)

    v = pd.read_parquet(src / "votos_canonico.parquet")
    actas = pd.read_parquet(src / "actas_canonico.parquet")[["acta_id", "fecha"]]
    v = v.merge(actas, on="acta_id", how="left")
    v["_key"] = v["legislador_nombre"].map(_name_key)
    v["legislador_id"] = v["_key"].map(_leg_id)
    v["bloque_norm"] = v["bloque"].map(_bloque_norm)
    v["bloque_linaje"] = _linaje_vec(v["bloque_norm"], v["fecha"])
    # coalicion = linaje, salvo el núcleo JxC dentro de su ventana temporal
    v["coalicion"] = v["bloque_linaje"]
    _fe = pd.to_datetime(v["fecha"], errors="coerce")
    _jxc = v["bloque_norm"].isin(JXC_MIEMBROS) & (_fe >= pd.Timestamp(CUTOFF_JXC)) & (_fe < pd.Timestamp(CUTOFF_JXC_FIN))
    v.loc[_jxc, "coalicion"] = "Juntos por el Cambio (Cambiemos)"

    cwb = (v.groupby("bloque_norm").agg(
        variantes=("bloque", lambda s: sorted(set(s))[:8]),
        n_variantes=("bloque", "nunique"), linaje=("bloque_linaje", "first"),
        n_votos=("bloque_norm", "size")).reset_index().sort_values("n_votos", ascending=False))
    v.drop(columns="_key").to_parquet(out / "votos_resuelto.parquet", index=False)
    cwb.to_csv(borrar / "crosswalk_bloques.csv", index=False)

    print(f"votos: {len(v)}")
    print(f"bloque crudo: {v['bloque'].nunique()}  ->  bloque_norm: {v['bloque_norm'].nunique()}  ->  linaje: {v['bloque_linaje'].nunique()}")
    print("\n=== linaje (cobertura de votos) ===")
    print(v["bloque_linaje"].value_counts().to_string())
    print("\n=== coalicion (cobertura de votos) ===")
    print(v["coalicion"].value_counts().to_string())
    vy = v.assign(anio=pd.to_datetime(v["fecha"], errors="coerce").dt.year)
    print("\n=== JxC por año (control: debe arrancar 2015/16) ===")
    print(vy[vy["coalicion"].str.startswith("Juntos")].groupby("anio").size().to_string())
    print("\n=== merges aplicados (bloque_norm con >1 variante cruda) ===")
    for _, r in cwb[cwb["n_variantes"] > 1].head(12).iterrows():
        print(f"  {r['bloque_norm']:<35} <- {r['variantes']}")

if __name__ == "__main__":
    main()
