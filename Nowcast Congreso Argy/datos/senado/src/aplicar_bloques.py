"""Aplica el padrón histórico de bloques a senado_votos.parquet (in place).

Reemplaza el campo `bloque` (que el sitio pinta con el ÚLTIMO bloque conocido,
anacrónico) por el bloque CONTEMPORÁNEO al voto según el padrón:
  data/padron_bloques_senado.csv      (Wikipedia 2017-2025, regenerable)
  data/padron_manual_2015_2017.csv    (curado a mano; fuente != BORRADOR gana)

Asignación: clave(nombre) + fecha del acta dentro de [desde, hasta]. Si la
clave exacta no matchea, hay FALLBACK por subconjunto de tokens (une
"MERA, DALMACIO" con "Dalmacio Mera Figueroa" o "SOLANAS, FERNANDO EZEQUIEL"
con "Fernando Solanas") siempre que el candidato sea ÚNICO.
El padrón MANUAL tiene precedencia sobre el automático (permite corregir a
mano casos donde el anexo de Wikipedia pinta el bloque de fin de ventana).
Si un voto no tiene cobertura en el padrón, CONSERVA el bloque del sitio y se
reporta (los votos de filas BORRADOR sin revisar cuentan como sin cobertura).

Además corre CONTROLES DE ANACRONISMO (ningún bloque puede aparecer antes de
su fecha de nacimiento) sobre el resultado final.

Correr (después de scrape_votaciones.py y padron_bloques.py):
  python datos/senado/src/aplicar_bloques.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from padron_bloques import clave  # noqa: E402  (misma clave de matching)

logger = logging.getLogger("senado.aplicar_bloques")
DATA = Path(__file__).resolve().parents[1] / "data"

# bloque -> primera fecha posible (nacimiento del bloque en el Senado)
NACIMIENTOS = {
    "CAMBIEMOS": "2015-12-10",
    "UNIDAD CIUDADANA": "2017-12-10",
    "FRENTE DE TODOS": "2019-12-10",
    "JUNTOS POR EL CAMBIO": "2019-12-10",
    "UNIDAD FEDERAL": "2023-01-01",
    "LA LIBERTAD AVANZA": "2023-12-10",
    "UNION POR LA PATRIA": "2023-12-10",
}


def _anacronismos(votos: pd.DataFrame, fechas: pd.Series) -> int:
    # igualdad exacta, no contains: existen homónimos legítimos anteriores
    # (ej. "FRENTE DE TODOS (CORRIENTES)", partido correntino pre-2019)
    n = 0
    f = fechas.reindex(votos.index)
    for blo, ini in NACIMIENTOS.items():
        malos = votos[(votos["bloque"].str.strip() == blo) & (f < ini)]
        if len(malos):
            n += len(malos)
            logger.warning("ANACRONISMO: %d votos '%s' antes de %s (ej: %s)",
                           len(malos), blo, ini,
                           malos["legislador_nombre"].iloc[0])
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    votos = pd.read_parquet(DATA / "clean" / "senado_votos.parquet")
    actas = pd.read_parquet(DATA / "clean" / "senado_actas.parquet")
    fechas = votos["acta_id"].map(actas.set_index("acta_id")["fecha"])

    frames = []
    auto = DATA / "padron_bloques_senado.csv"
    manual = DATA / "padron_manual_2015_2017.csv"
    if manual.exists():  # el manual va PRIMERO: gana en solapamientos
        m = pd.read_csv(manual, dtype=str)
        pend = m[(m["fuente"] == "BORRADOR") | m["bloque"].isna() | (m["bloque"] == "")]
        if len(pend):
            logger.warning("padrón manual: %d filas BORRADOR sin curar "
                           "(esos votos quedan sin cobertura)", len(pend))
        frames.append(m[~m.index.isin(pend.index)])
    if auto.exists():
        frames.append(pd.read_csv(auto, dtype=str))
    if not frames:
        raise FileNotFoundError("no hay padrón: correr padron_bloques.py primero")
    padron = pd.concat(frames, ignore_index=True).fillna("")
    padron["hasta"] = padron["hasta"].replace("", "9999-12-31")

    # índice clave -> [(desde, hasta, bloque, fuente)] en orden de precedencia
    idx: dict[str, list[tuple[str, str, str, str]]] = {}
    for r in padron.itertuples(index=False):
        idx.setdefault(r.clave, []).append((r.desde, r.hasta, r.bloque, r.fuente))

    # fallback: subconjunto de tokens (2º nombre / 2º apellido en una sola
    # fuente). Se SUMA a los matches exactos (una clave puede tener filas
    # exactas en un período y variantes con más tokens en otro, ej. MERA /
    # MERA FIGUEROA). Varios candidatos se aceptan solo si son variantes
    # entre sí (cadena de subconjuntos, ej. OLALLA / OLALLA DE MOREIRA /
    # OLALLA DE MOREIRA ELISA); si no, se descartan para no unir homónimos.
    def _candidatos(k: str) -> list:
        filas = list(idx.get(k, []))
        toks = set(k.split())
        cands = [c for c in idx if c != k
                 and (toks <= set(c.split()) or set(c.split()) <= toks)]
        if len(cands) > 1:
            variantes = all(set(a.split()) <= set(b.split())
                            or set(b.split()) <= set(a.split())
                            for i, a in enumerate(cands) for b in cands[i + 1:])
            if not variantes:
                cands = []
        for c in cands:
            filas += idx[c]
        return filas

    claves = votos["legislador_nombre"].map(clave)
    resol = {k: _candidatos(k) for k in claves.unique()}
    nuevos, cubiertos = [], 0
    for k, f_acta, blo_orig in zip(claves, fechas, votos["bloque"]):
        nuevo = None
        for desde, hasta, blo, _ in resol.get(k, []):
            if desde <= (f_acta or "") <= hasta:
                nuevo = blo
                break
        if nuevo:
            cubiertos += 1
            nuevos.append(nuevo)
        else:
            nuevos.append(blo_orig)  # conserva el del sitio (queda reportado)
    votos["bloque"] = nuevos

    n_ana = _anacronismos(votos, fechas)
    sin = len(votos) - cubiertos
    votos.to_parquet(DATA / "clean" / "senado_votos.parquet", index=False)
    print(f"OK bloques aplicados: {cubiertos}/{len(votos)} votos cubiertos "
          f"({100*cubiertos/len(votos):.1f}%), {sin} conservan bloque del sitio")
    print(f"   anacronismos restantes: {n_ana}")
    resumen = (pd.DataFrame({"bloque": votos['bloque'], "anio": fechas.str[:4]})
               .groupby("anio")["bloque"].nunique())
    print("   bloques distintos por año:", resumen.to_dict())
    idx_faltan = [i for i, k in enumerate(claves)
                  if not any(d <= (fechas.iloc[i] or "") <= h
                             for d, h, _, _ in resol.get(k, []))]
    faltan = votos.loc[idx_faltan, "legislador_nombre"].value_counts().head(10)
    if len(faltan):
        print("   sin cobertura (top):", faltan.to_dict())
        # volcado completo para diagnóstico: senador x año x n votos
        # (a Archivos_Borrar: es descartable, régimen del proyecto)
        borrar = Path(__file__).resolve().parents[3] / "datos" / "Archivos_Borrar"
        borrar.mkdir(parents=True, exist_ok=True)
        diag = (pd.DataFrame({"senador": votos.loc[idx_faltan, "legislador_nombre"],
                              "anio": fechas.iloc[idx_faltan].str[:4]})
                .value_counts().rename("votos").reset_index()
                .sort_values(["senador", "anio"]))
        diag.to_csv(borrar / "senado_diag_sin_cobertura.csv", index=False,
                    encoding="utf-8-sig")
        print(f"   detalle -> {borrar / 'senado_diag_sin_cobertura.csv'}")


if __name__ == "__main__":
    main()
