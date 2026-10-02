"""modelo/voto_individual/src/disciplina.py
Índice de disciplina individual + set pivote — DESVÍO v2 (definición de Valle, ADR-0004).

MODELO (bottom-up): la línea del bloque EMERGE de sus miembros, no baja de afuera.
En cada votación, cada miembro tiene una de tres CONDUCTAS:
  AFIRMATIVO · NEGATIVO · NO_ACOMPANA (abstenerse o ausentarse — usar el escaño es una decisión).
La BAJADA DE LÍNEA del bloque = la conducta con mayoría simple sobre TODOS sus escaños
en esa acta (incluidos los ausentes). DESVÍO = tu conducta ≠ la línea (regla ESTRICTA:
abstenerse cuando la línea es rechazar también computa; votar cuando el bloque se
ausenta en masa, también).

Sin mayoría en el bloque (ej. 2-2):
  1) si el bloque pertenece a un espacio político real (linaje ≠ "OTRO / PROVINCIAL"),
     se desempata con la línea del ESPACIO entero en esa acta (metodo="linaje");
  2) si no hay espacio real o el espacio también empata: DESVÍO PARCIAL =
     1 − (fracción de escaños del bloque con tu misma conducta) (metodo="parcial").
Pendiente anotado: reclasificar los partidos de la bolsa OTRO/PROVINCIAL hacia linajes.

EXCLUSIONES (falso desvío estructural, decisión de Valle 2026-07-02): presidentes de la
Cámara de Diputados (no votan por costumbre), SUSPENDIDOS (anotados en el nombre por la
fuente) y placeholders. Las LICENCIAS no están en los datos: dependen de la herramienta
de licencias/suspensiones (PLAN — datos/licencias_suspensiones, a crear).

DISPUTADA: misma definición que datos/export (resultado a ±5% de los votos emitidos
respecto del umbral de la mayoría requerida). Mantener sincronizadas.

Separación INDISCIPLINA / AUSENTISMO (URGENTE 1, 2026-08-13): el `tasa_desvio` v2
mezcla dos cosas — votar distinto (indisciplina) y no ir (ausentismo), correlacionadas
r≈0,63. Se agregan columnas ADITIVAS (no se renombra nada consumido): `tasa_desvio_conducta`
mide el desvío SÓLO estando presente; `tasa_desvio_ausencia`, sólo sobre ausencias;
`pct_ausente` + `ausentista_outlier` (μ+2σ) marcan a quienes casi no usan la banca
(muertes/testimoniales/licencias — ADR-0004). Los consumidores del γ (variables/proyecto)
leen la columna de conducta y sacan los outliers.

Salidas (outputs/):
  - disciplina_individual.csv    (una fila por legislador; incluye las columnas de
                                  conducta/ausencia y el flag ausentista_outlier)
  - disciplina_por_periodo.csv   (legislador × período parlamentario × cámara)
  - disciplina_por_anio.csv      (legislador × año)
  - desvios_por_voto.parquet     (una fila por VOTO: conducta, línea, método, desvío —
                                  contrato para la columna `desvio` de datos/export)
  - set_pivote.json              (dimensionamiento del set pivote)

Uso:
  python modelo/voto_individual/src/disciplina.py
  CANON=/ruta/a/clean OUT=/ruta/salida MIN_VOTOS=50 python .../disciplina.py
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

# ── definiciones compartidas ──────────────────────────────────────────────────
# `periodo_parlamentario`, `normalizar_mayoria` y `MIEMBROS` vivían copiados acá, sincronizados a mano; el único
# control era un docstring que pedía "mantener sincronizadas". Unificados el
# 2026-08-25 en `definiciones.py` (raíz) — ADR-0014. Se RE-EXPORTAN para que
# `disciplina.<nombre>` siga existiendo: aguas abajo no cambia nada.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(next(d for d in _Path(__file__).resolve().parents
                             if (d / "rutas.py").is_file())))
from definiciones import BANCAS as MIEMBROS  # noqa: E402,F401
from definiciones import normalizar_mayoria  # noqa: E402,F401
from definiciones import periodo_parlamentario  # noqa: E402,F401

log = logging.getLogger("disciplina")

CONDUCTAS = ["AFIRMATIVO", "NEGATIVO", "NO_ACOMPANA"]
# Para separar INDISCIPLINA de AUSENTISMO (URGENTE 1, 2026-08-13): "presente" = usó el
# escaño (votó o se abstuvo — abstenerse es un acto político estando en la banca,
# ADR-0004); "ausente" = no fue. La abstención va del lado PRESENTE porque el problema
# que se corrige es el ausentismo, no la abstención (17.792 abstenciones vs 254.370
# ausencias en la base). `tasa_desvio_conducta` = desvío medido SÓLO sobre los presentes.
PRESENTE_VOTOS = {"AFIRMATIVO", "NEGATIVO", "ABSTENCION"}
LINAJE_BOLSA = "OTRO / PROVINCIAL"   # no es un espacio político real: no sirve para desempatar
MARGEN_DISPUTADA = 0.05              # ±5% de los emitidos (igual que datos/export)
UMBRALES = [0.02, 0.05, 0.10, 0.15]

# Presidentes de la Cámara de Diputados: por costumbre NO votan (solo desempatan), así
# que computarles "no acompaña" sería falso desvío. Se excluyen sus filas durante su
# presidencia (hallazgo de la validación v2: dominaban el top con 85-95% de "desvío").
# Lista curada — mantener al día en cada recambio. El Senado no lo necesita: lo preside
# el vicepresidente de la Nación, que no es senador.
PRESIDENCIAS_DIPUTADOS = [
    ("PASCUAL",    "1999-12-10", "2001-12-20"),
    ("CAMAÑO",     "2001-12-21", "2005-12-09"),   # Eduardo Camaño
    ("BALESTRINI", "2005-12-10", "2007-12-09"),
    ("FELLNER",    "2007-12-10", "2011-12-09"),
    ("DOMINGUEZ",  "2011-12-10", "2015-12-09"),   # Julián Domínguez
    ("MONZO",      "2015-12-10", "2019-12-09"),   # Emilio Monzó
    ("MASSA",      "2019-12-10", "2022-08-02"),   # Sergio Massa
    ("MOREAU",     "2022-08-02", "2023-12-09"),   # Cecilia Moreau
    ("MENEM",      "2023-12-10", None),           # Martín Menem
]


def _sin_acentos(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.upper()
             .str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii"))


def excluir_no_medibles(v: pd.DataFrame, presidencia: str = "total") -> pd.DataFrame:
    """Saca (1) filas placeholder de las fuentes (bancas no incorporadas), (2) suspendidos
    (Art. 70 C.N., anotados en el nombre: no votar no es una decisión) y (3) al presidente
    de Diputados durante su presidencia. Las LICENCIAS quedan pendientes de la herramienta
    de licencias/suspensiones (ver PLAN).

    `presidencia` decide con qué se mira si el presidente "no vota" (> 80% NO_ACOMPANA):
    "total" (el CSV de siempre) mira TODA la presidencia, incluido lo posterior a cada acta;
    "al_dia" (la ficha point-in-time, auditoría 2026-09 D1.0) decide acta por acta con lo
    que hizo en la presidencia hasta esa fecha, así que nunca usa nada posterior."""
    if presidencia not in ("total", "al_dia"):
        raise ValueError(f"presidencia inválida: {presidencia!r}")
    antes = len(v)
    # El nombre normalizado se calcula UNA vez, sobre los nombres distintos (2026-10-01, D1.0:
    # el motor arma la ficha al día en cada proceso). Mismo resultado que normalizar fila por fila
    # antes de cada filtro: los tres filtros miran el mismo valor de la fila.
    crudo = v["legislador_nombre"].astype(str)
    distintos = pd.Series(crudo.unique())
    nombre = crudo.map(dict(zip(distintos, _sin_acentos(distintos))))
    # Placeholder de banca vacante: "Legislador a Designar" / "#, Legislador a Designar"
    # (1.023 votos fantasma al 100% de ausencia que se colaban en el ranking de díscolos,
    # detectado 2026-08-13). El filtro de "NO INCORPORADO" no lo cazaba.
    fuera_nombre = (nombre.str.contains("NO INCORPORADO", na=False) | nombre.str.contains("DESIGNAR", na=False)
                    | nombre.str.contains("SUSPENDID", na=False))
    v, nombre = v[~fuera_nombre], nombre[~fuera_nombre]
    f = pd.to_datetime(v["fecha"], errors="coerce")
    fuera = pd.Series(False, index=v.index)
    for apellido, desde, hasta in PRESIDENCIAS_DIPUTADOS:
        m = (v["camara"] == "diputados") & nombre.str.contains(apellido, na=False)
        m &= f >= pd.Timestamp(desde)
        if hasta:
            m &= f <= pd.Timestamp(hasta)
        # solo si su conducta dominante en el período es NO votar (evita homónimos:
        # p.ej. otro MASSA que sí vota no debe excluirse)
        if m.any():
            for lid in v.loc[m, "legislador_id"].unique():
                mi = m & (v["legislador_id"] == lid)
                if presidencia == "total":
                    if (v.loc[mi, "conducta"] == "NO_ACOMPANA").mean() > 0.8:
                        fuera |= mi
                    continue
                # al día: la proporción acumulada hasta cada fecha (incluido ese día)
                por_dia = (v.loc[mi, "conducta"].eq("NO_ACOMPANA")
                           .groupby(f[mi]).agg(["sum", "size"]).sort_index())
                prop = por_dia["sum"].cumsum() / por_dia["size"].cumsum()
                fuera |= mi & f.isin(prop.index[prop > 0.8])
    v = v[~fuera]
    log.info("excluidos no medibles: %d filas (placeholders + suspendidos + presidencias)", antes - len(v))
    return v


def actas_disputadas(actas: pd.DataFrame, v: pd.DataFrame) -> set:
    """Disputada = resultado a ±5% de los emitidos respecto del umbral (def. de Valle,
    sincronizada con datos/export)."""
    a = actas.copy()
    cnt = v.pivot_table(index="acta_id", columns="voto", aggfunc="size", fill_value=0)
    for col, nc in [("AFIRMATIVO", "n_afirmativos"), ("NEGATIVO", "n_negativos")]:
        calc = a["acta_id"].map(cnt[col]) if col in cnt.columns else np.nan
        a[nc] = pd.to_numeric(a.get(nc), errors="coerce").fillna(calc)
    afirm, neg = a["n_afirmativos"], a["n_negativos"]
    emitidos = afirm + neg
    miembros = a["camara"].map(MIEMBROS)
    tipo = normalizar_mayoria(a.get("tipo_mayoria", pd.Series(index=a.index, dtype=object)))
    umbral = pd.Series(np.nan, index=a.index, dtype=float)
    umbral[tipo == "SIMPLE"] = emitidos[tipo == "SIMPLE"] / 2
    umbral[tipo == "ABSOLUTA"] = (miembros[tipo == "ABSOLUTA"] // 2 + 1).astype(float)
    umbral[tipo == "DOS_TERCIOS"] = np.ceil(emitidos[tipo == "DOS_TERCIOS"] * 2 / 3)
    umbral[tipo == "DOS_TERCIOS_CUERPO"] = np.ceil(miembros[tipo == "DOS_TERCIOS_CUERPO"] * 2 / 3)
    umbral[tipo == "TRES_CUARTOS"] = np.ceil(emitidos[tipo == "TRES_CUARTOS"] * 3 / 4)
    disp = (afirm - umbral).abs() <= MARGEN_DISPUTADA * emitidos
    return set(a.loc[disp.fillna(False), "acta_id"])


def cargar(src: Path, presidencia: str = "total") -> tuple[pd.DataFrame, pd.DataFrame]:
    fv, fa = src / "votos_resuelto.parquet", src / "actas_canonico.parquet"
    for f in (fv, fa):
        if not f.exists():
            raise FileNotFoundError(
                f"No existe {f}. Reconstruí la base primero: python datos/canonica/src/run_pipeline.py"
            )
    v = pd.read_parquet(fv)
    actas = pd.read_parquet(fa)
    a = actas[["acta_id", "camara", "fecha"]].rename(columns={"fecha": "fecha_acta"})
    v = v.merge(a, on="acta_id", how="left")
    v["fecha"] = v["fecha"].fillna(v["fecha_acta"])
    v["anio"] = pd.to_datetime(v["fecha"], errors="coerce").dt.year.astype("Int64")
    v.loc[v["anio"].isna() & (v["fuente"] == "manual_2026"), "anio"] = 2026
    v["periodo"] = periodo_parlamentario(v["fecha"], v["anio"])
    # v2: TODOS los votos cuentan (la ausencia/abstención es una conducta), solo se
    # excluye lo que no tiene bloque asignable y los no-medibles estructurales.
    v = v[v["bloque_norm"].notna() & (v["bloque_norm"] != "SIN BLOQUE")].copy()
    v["conducta"] = np.where(v["voto"].isin(["AFIRMATIVO", "NEGATIVO"]), v["voto"], "NO_ACOMPANA")
    v = excluir_no_medibles(v, presidencia)
    if v.empty:
        raise ValueError("Base sin votos con bloque resuelto; nada que medir.")
    log.info("votos con bloque (todas las conductas): %d (%d actas)", len(v), v["acta_id"].nunique())
    return v, actas


def _linea(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """Conducta con >50% de los escaños del nivel (bloque o linaje) en cada acta."""
    cnt = (df.groupby(["acta_id", nivel, "conducta"], observed=True).size()
             .unstack(fill_value=0).reindex(columns=CONDUCTAS, fill_value=0))
    total = cnt.sum(axis=1)
    top = cnt.max(axis=1)
    linea = cnt.idxmax(axis=1).where(top * 2 > total)  # mayoría simple estricta, si no NA
    out = linea.rename("linea").reset_index()
    out["n_total"] = total.values
    return out


def marcar_desvios(v: pd.DataFrame) -> pd.DataFrame:
    """Desvío v2 por voto: línea del bloque → desempate por linaje → desvío parcial."""
    v = v.copy()
    # Banderas presente/ausente para separar el desvío de CONDUCTA del de AUSENCIA
    # (URGENTE 1, 2026-08-13). Acá y no en cargar() para que también las tenga quien
    # llame a marcar_desvios directo (los tests). Guarda de faltantes con pd.isna() +
    # str() explícito: en la PC de Valle `voto` puede llegar como pd.NA (backend
    # pyarrow) y `NA == "AUSENTE"` es ambiguo (bug del 2026-08-08, ver ESTADO).
    voto_up = v["voto"].map(lambda x: "" if pd.isna(x) else str(x).upper())
    v["presente"] = voto_up.isin(PRESENTE_VOTOS)
    v["ausente"] = voto_up.eq("AUSENTE")
    lb = _linea(v, "bloque_norm").rename(columns={"linea": "linea_bloque", "n_total": "n_bloque"})
    d = v.merge(lb, on=["acta_id", "bloque_norm"], how="left")

    # cuántos pares del bloque comparten mi conducta (para el desvío parcial)
    mismos = (v.groupby(["acta_id", "bloque_norm", "conducta"], observed=True).size()
                .rename("n_misma_conducta").reset_index())
    d = d.merge(mismos, on=["acta_id", "bloque_norm", "conducta"], how="left")

    # línea del espacio político (solo linajes reales)
    vreal = v[v["bloque_linaje"].notna() & (v["bloque_linaje"] != LINAJE_BOLSA)]
    ll = _linea(vreal, "bloque_linaje").rename(columns={"linea": "linea_linaje"})[
        ["acta_id", "bloque_linaje", "linea_linaje"]]
    d = d.merge(ll, on=["acta_id", "bloque_linaje"], how="left")

    con_linea = d["linea_bloque"].notna()
    linaje_ok = ~con_linea & d["linea_linaje"].notna() & (d["bloque_linaje"] != LINAJE_BOLSA)
    parcial = ~con_linea & ~linaje_ok

    d["metodo"] = np.select([con_linea, linaje_ok, parcial], ["bloque", "linaje", "parcial"], default="parcial")
    d["desvio"] = np.select(
        [con_linea, linaje_ok, parcial],
        [(d["conducta"] != d["linea_bloque"]).astype(float),
         (d["conducta"] != d["linea_linaje"]).astype(float),
         1.0 - d["n_misma_conducta"] / d["n_bloque"]],
    )
    d["linea"] = d["linea_bloque"].fillna(d["linea_linaje"].where(linaje_ok))
    log.info("desvíos v2 — método: %s | desvío medio: %.4f",
             d["metodo"].value_counts().to_dict(), d["desvio"].mean())
    return d


def indice_por_legislador(d: pd.DataFrame, disputadas: set) -> pd.DataFrame:
    d = d.assign(disputada=d["acta_id"].isin(disputadas))

    def agg(sub: pd.DataFrame) -> pd.Series:
        anio_max = sub["anio"].max()
        reciente = sub[sub["anio"] >= (anio_max - 1)] if pd.notna(anio_max) else sub.iloc[0:0]
        sd = sub[sub["disputada"]]
        # separación indisciplina / ausentismo (URGENTE 1): el desvío de CONDUCTA se
        # mide sólo sobre los votos donde el legislador ESTUVO PRESENTE; el de AUSENCIA,
        # sólo sobre los AUSENTE. `tasa_desvio` (mezclada) se conserva sin tocar.
        pres, aus = sub[sub["presente"]], sub[sub["ausente"]]
        sd_pres, rec_pres = sd[sd["presente"]], reciente[reciente["presente"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "camaras": "+".join(sorted(sub["camara"].dropna().unique())),
            "bloques": "; ".join(sorted(sub["bloque_norm"].dropna().unique())[:4]),
            "anio_desde": sub["anio"].min(), "anio_hasta": anio_max,
            "n_votos": len(sub), "n_desvios": round(float(sub["desvio"].sum()), 1),
            "tasa_desvio": round(float(sub["desvio"].mean()), 4),
            "pct_ausente": round(float(sub["ausente"].mean()), 4),
            "n_presente": int(sub["presente"].sum()),
            "tasa_desvio_conducta": round(float(pres["desvio"].mean()), 4) if len(pres) else np.nan,
            "tasa_desvio_ausencia": round(float(aus["desvio"].mean()), 4) if len(aus) else np.nan,
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(float(sd["desvio"].mean()), 4) if len(sd) else np.nan,
            "tasa_desvio_disputadas_conducta": round(float(sd_pres["desvio"].mean()), 4) if len(sd_pres) else np.nan,
            "n_reciente": len(reciente),
            "tasa_desvio_reciente": round(float(reciente["desvio"].mean()), 4) if len(reciente) else np.nan,
            "tasa_desvio_reciente_conducta": round(float(rec_pres["desvio"].mean()), 4) if len(rec_pres) else np.nan,
            "pct_metodo_linaje": round(float((sub["metodo"] == "linaje").mean()), 4),
            "pct_metodo_parcial": round(float((sub["metodo"] == "parcial").mean()), 4),
            "tam_bloque_mediano": float(sub["n_bloque"].median()),
        })

    idx = d.groupby("legislador_id", observed=True).apply(agg, include_groups=False).reset_index()
    return idx.sort_values("tasa_desvio", ascending=False)


# ── LA FICHA AL DÍA (point-in-time) — auditoría 2026-09, D1.0, decisión de Franco ─────────
# `disciplina_individual.csv` se calcula con TODA la historia (y su «reciente» se mide desde
# el último año de cada legislador): un nowcast fechado en el pasado veía el futuro y ningún
# backtest podía usarla. La ficha al día aplica LA MISMA REGLA que `indice_por_legislador`
# (las seis columnas que lee `ensemble.roster_nominal`) sólo con los votos de fecha < F.
# El desvío de cada voto sale de su propia acta (`marcar_desvios`), así que la tabla por voto
# no trae nada de otra fecha; la exclusión del presidente se decide al día (`presidencia=
# "al_dia"`). Los votos sin fecha válida quedan afuera: no tienen fecha de disponibilidad.
# Una sola copia: la usan el motor (`roster_nominal`) y el harness del censo.
COLUMNAS_FICHA = ("n_votos", "n_reciente", "tasa_desvio", "tasa_desvio_conducta",
                  "tasa_desvio_reciente", "tasa_desvio_reciente_conducta")


COLUMNAS_TABLA = ("acta_id", "legislador_id", "fecha", "presente", "desvio")


def tabla_desvios_al_dia(src: Path | None = None, completa: bool = False) -> pd.DataFrame:
    """La tabla por voto de la ficha point-in-time, desde la canónica (que viaja por git):
    `cargar` con la exclusión del presidente al día + `marcar_desvios`, sin los votos sin
    fecha, ordenada por legislador y fecha. Por defecto sólo las columnas que usa la ficha
    (`COLUMNAS_TABLA`); `completa=True` deja todas (las que necesita `indice_por_legislador`)."""
    src = Path(src) if src is not None else Path(__file__).resolve().parents[3] / "datos" / "canonica" / "data" / "clean"
    v, _ = cargar(src, presidencia="al_dia")
    d = marcar_desvios(v)
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    d = d[d["fecha"].notna()]
    if not completa:
        d = d[list(COLUMNAS_TABLA)]
    d = d.copy()
    d["anio"] = d["fecha"].dt.year.astype(int)
    d["legislador_id"] = d["legislador_id"].astype(str)
    return d.sort_values(["legislador_id", "fecha"], kind="mergesort").reset_index(drop=True)


class FichaAlDia:
    """La ficha de cada legislador a una fecha, sobre una tabla de `tabla_desvios_al_dia`.

    `al(hasta, legisladores=None, excluir_ley=None)` -> {legislador_id: {columna: valor}} con
    las seis `COLUMNAS_FICHA`, redondeadas como el CSV, sobre los votos con fecha < `hasta`
    (de las dos cámaras, como el CSV) y, si se pasa `excluir_ley`, sin los de esa ley (la
    regla del EXPEDIENTE del harness; `ley_de_acta` dice a qué ley pertenece cada acta). Un
    legislador sin ningún voto anterior no figura (la escalera de `roster_nominal` cae al
    linaje). Las medias se calculan sobre los mismos valores y en el mismo orden que
    `indice_por_legislador` aplicado a la tabla recortada."""

    def __init__(self, tabla: pd.DataFrame, ley_de_acta: dict | None = None):
        t = tabla[list(COLUMNAS_TABLA)].copy()
        t["legislador_id"] = t["legislador_id"].astype(str)
        t = t.sort_values(["legislador_id", "fecha"], kind="mergesort").reset_index(drop=True)
        # sólo arreglos numéricos (cada proceso del censo y del motor tiene su copia)
        self._f = t["fecha"].values.astype("datetime64[ns]").astype(np.int64)
        self._anio = t["fecha"].dt.year.values.astype(np.int64)
        self._pres = t["presente"].values.astype(bool)
        self._d = t["desvio"].values.astype(float)
        cod, lids = pd.factorize(t["legislador_id"], sort=False)
        cambia = np.r_[True, cod[1:] != cod[:-1]] if len(cod) else np.zeros(0, bool)
        ini = np.flatnonzero(cambia)
        fin = np.r_[ini[1:], len(cod)]
        self._rango = {str(lids[cod[i]]): (int(i), int(j)) for i, j in zip(ini, fin)}
        self._ley, self._ley_cod = None, {}
        if ley_de_acta is not None:
            cod_acta, actas = pd.factorize(t["acta_id"].astype(str), sort=False)
            ley_de = pd.Series(actas).map(ley_de_acta)
            ley_de = ley_de.where(ley_de.notna(), "acta:" + pd.Series(actas)).astype(str)
            cod_ley, leyes = pd.factorize(ley_de, sort=False)
            self._ley = cod_ley[cod_acta]
            self._ley_cod = {str(x): i for i, x in enumerate(leyes)}

    def _fila(self, idx: np.ndarray) -> dict:
        d, p, a = self._d[idx], self._pres[idx], self._anio[idx]
        rec = a >= (a.max() - 1)
        dp, dr, drp = d[p], d[rec], d[rec & p]
        return {"n_votos": int(idx.size), "n_reciente": int(rec.sum()),
                "tasa_desvio": round(float(d.mean()), 4),
                "tasa_desvio_conducta": round(float(dp.mean()), 4) if dp.size else np.nan,
                "tasa_desvio_reciente": round(float(dr.mean()), 4) if dr.size else np.nan,
                "tasa_desvio_reciente_conducta": round(float(drp.mean()), 4) if drp.size else np.nan}

    def al(self, hasta, legisladores=None, excluir_ley: str | None = None) -> dict:
        corte = pd.Timestamp(hasta).value
        claves = self._rango.keys() if legisladores is None else (str(x) for x in legisladores)
        out = {}
        for lid in claves:
            r = self._rango.get(lid)
            if r is None:
                continue
            s, e = r
            k = s + int(np.searchsorted(self._f[s:e], corte, side="left"))
            if k == s:
                continue
            idx = np.arange(s, k)
            if excluir_ley is not None and self._ley is not None and str(excluir_ley) in self._ley_cod:
                idx = idx[self._ley[s:k] != self._ley_cod[str(excluir_ley)]]
                if idx.size == 0:
                    continue
            out[lid] = self._fila(idx)
        return out


_FICHA_CACHE: dict = {}


def ficha_al_dia(fecha, src: Path | None = None, legisladores=None) -> dict:
    """La ficha de todos (o de `legisladores`) al día `fecha`, desde la canónica de `src`.
    La tabla por voto se arma una vez por proceso y por canónica (≈ 12 s)."""
    clave = str(Path(src).resolve()) if src is not None else "default"
    if clave not in _FICHA_CACHE:
        _FICHA_CACHE[clave] = FichaAlDia(tabla_desvios_al_dia(src))
    return _FICHA_CACHE[clave].al(fecha, legisladores)


def por_anio(d: pd.DataFrame) -> pd.DataFrame:
    g = (d.dropna(subset=["anio"])
           .groupby(["legislador_id", "anio"], observed=True)
           .agg(nombre=("legislador_nombre", lambda s: s.mode().iat[0]),
                camara=("camara", "first"),
                n_votos=("desvio", "size"), n_desvios=("desvio", "sum"))
           .reset_index())
    g["n_desvios"] = g["n_desvios"].round(1)
    g["tasa_desvio"] = (g["n_desvios"] / g["n_votos"]).round(4)
    return g


def por_periodo(d: pd.DataFrame, disputadas: set) -> pd.DataFrame:
    d = d.assign(disputada=d["acta_id"].isin(disputadas)).dropna(subset=["periodo"])

    def agg(sub: pd.DataFrame) -> pd.Series:
        sd = sub[sub["disputada"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "bloque": sub["bloque_norm"].mode().iat[0],
            "n_votos": len(sub), "n_desvios": round(float(sub["desvio"].sum()), 1),
            "tasa_desvio": round(float(sub["desvio"].mean()), 4),
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(float(sd["desvio"].mean()), 4) if len(sd) else np.nan,
        })

    g = (d.groupby(["legislador_id", "periodo", "camara"], observed=True)
           .apply(agg, include_groups=False).reset_index())
    return g.sort_values(["legislador_id", "periodo"])


def dimensionar_set_pivote(idx: pd.DataFrame, min_votos: int) -> dict:
    base = idx[idx["n_votos"] >= min_votos]
    res = {
        "definicion": "desvío v2 (ADR-0004): conducta vs línea del bloque (mayoría de TODOS los escaños); "
                      "estricta con abstenciones/ausencias; desempate por linaje; parcial en OTRO/PROVINCIAL; "
                      "excluidos presidentes de Diputados y suspendidos",
        "min_votos": min_votos,
        "legisladores_medibles": int(len(base)),
        "tasa_desvio_mediana": round(float(base["tasa_desvio"].median()), 4),
        "tasa_desvio_p90": round(float(base["tasa_desvio"].quantile(0.90)), 4),
        "por_umbral": {},
    }
    for u in UMBRALES:
        sel = base[base["tasa_desvio"] >= u]
        res["por_umbral"][f">={int(u*100)}%"] = {
            "n_legisladores": int(len(sel)),
            "pct_de_medibles": round(100 * len(sel) / len(base), 1) if len(base) else 0.0,
        }
    disp = base.dropna(subset=["tasa_desvio_disputadas"])
    disp = disp[disp["n_disputadas"] >= 5]
    res["disputadas"] = {
        f">={int(u*100)}%": int((disp["tasa_desvio_disputadas"] >= u).sum()) for u in UMBRALES
    }
    return res


def marcar_ausentista_outlier(idx: pd.DataFrame, min_votos: int) -> tuple[pd.DataFrame, dict]:
    """Marca `ausentista_outlier` = pct_ausente MUY por encima de la distribución
    (media + 2σ sobre los legisladores medibles). Decisión de Valle (2026-08-13): el
    Reglamento sanciona la ausencia reiterada, y estos casos (muertes en el cargo,
    bancas testimoniales, licencias — ADR-0004) inflan el "desvío" con inasistencia,
    no con indisciplina. Se los MARCA acá; los consumidores del γ los sacan de la
    muestra. Los que tienen mandato vigente se revisan caso por caso (no se borran).
    El umbral se calcula sobre la corrida y se registra en set_pivote.json (2σ ≈ 0,61
    con la base actual, pero se recomputa por si cambian los datos)."""
    base = idx[idx["n_votos"] >= min_votos]
    mu = float(base["pct_ausente"].mean())
    sd = float(base["pct_ausente"].std())
    umbral = mu + 2 * sd
    idx = idx.copy()
    # guarda de faltantes: pct_ausente no debería tener NA, pero fillna(0) evita que un
    # NA se convierta en outlier espurio en cualquier backend de dtype.
    idx["ausentista_outlier"] = idx["pct_ausente"].fillna(0) >= umbral
    info = {"umbral_mu_2sigma": round(umbral, 4), "media": round(mu, 4), "sigma": round(sd, 4),
            "n_outliers_medibles": int((base["pct_ausente"].fillna(0) >= umbral).sum())}
    log.info("ausentismo: media=%.3f sigma=%.3f umbral(mu+2sigma)=%.3f -> %d outliers medibles",
             mu, sd, umbral, info["n_outliers_medibles"])
    return idx, info


def main() -> None:
    # Acá y no al importar: el motor importa este módulo (la ficha al día) y no tiene por
    # qué heredar su configuración de logging.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    here = Path(__file__).resolve()
    src = Path(os.environ.get("CANON", here.parents[3] / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", here.parents[1] / "outputs"))
    min_votos = int(os.environ.get("MIN_VOTOS", "50"))
    out.mkdir(parents=True, exist_ok=True)

    v, actas = cargar(src)
    d = marcar_desvios(v)
    disputadas = actas_disputadas(actas, v)
    log.info("actas disputadas (±5%% emitidos): %d", len(disputadas))

    idx = indice_por_legislador(d, disputadas)
    idx, outlier_info = marcar_ausentista_outlier(idx, min_votos)
    anual = por_anio(d)
    periodos = por_periodo(d, disputadas)
    gate = dimensionar_set_pivote(idx, min_votos)
    gate["ausentismo_outlier"] = outlier_info
    gate["cobertura"] = {
        "n_votos_medidos": int(len(d)),
        "n_actas": int(d["acta_id"].nunique()),
        "anios": f"{int(d['anio'].min())}-{int(d['anio'].max())}" if d["anio"].notna().any() else "s/d",
        "fuentes": sorted(d["fuente"].unique().tolist()),
        "metodo": {k: int(n) for k, n in d["metodo"].value_counts().items()},
    }

    idx.to_csv(out / "disciplina_individual.csv", index=False, encoding="utf-8-sig")
    anual.to_csv(out / "disciplina_por_anio.csv", index=False, encoding="utf-8-sig")
    periodos.to_csv(out / "disciplina_por_periodo.csv", index=False, encoding="utf-8-sig")
    d[["acta_id", "legislador_id", "conducta", "linea", "metodo", "desvio"]].to_parquet(
        out / "desvios_por_voto.parquet", index=False)
    (out / "set_pivote.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False, indent=2))
    top = idx[idx["n_votos"] >= min_votos].head(15)
    print("\nTop díscolos v2 (n_votos >= %d):" % min_votos)
    print(top[["nombre", "camaras", "anio_desde", "anio_hasta", "n_votos", "tasa_desvio",
               "tasa_desvio_disputadas"]].to_string(index=False))


if __name__ == "__main__":
    main()
