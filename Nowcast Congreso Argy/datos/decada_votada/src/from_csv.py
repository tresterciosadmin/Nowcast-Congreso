"""datos/decada_votada/src/from_csv.py
Semilla histórica desde el dump CSV de 'La Década Votada' (Aportes/towlandia).
Cubre Diputados 2001-2014 y Senado 2004-2014. Reemplaza la corrida lenta de R.
Normaliza al esquema canónico (schema_version=1, fuente=decada_votada).
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

SV, FUENTE = 1, "decada_votada"
VOTO = {"0":"AFIRMATIVO","1":"NEGATIVO","2":"ABSTENCION","3":"AUSENTE"}

def fix(s):  # corrige doble-encoding (AcciÃ³n -> Acción)
    if not isinstance(s,str): return s
    try: return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError,UnicodeEncodeError): return s

def _read(p): return pd.read_csv(p, encoding="latin-1", dtype=str).map(fix)

def parse(src: Path, camara: str, votf, asuf, legf, blof, legcol_id, legcol_nom, legcol_dist):
    vot=_read(src/votf); asu=_read(src/asuf); leg=_read(src/legf); blo=_read(src/blof)
    leg_nom=dict(zip(leg[legcol_id], leg[legcol_nom]))
    leg_dist=dict(zip(leg[legcol_id], leg[legcol_dist]))
    blo_nom=dict(zip(blo.iloc[:,0], blo.iloc[:,1]))
    asu_idx=asu.set_index("asuntoId")
    pre="dip" if camara=="diputados" else "sen"

    votos=pd.DataFrame({
        "schema_version":SV,
        "acta_id":f"{FUENTE}:{pre}:"+vot["asuntoId"].astype(str),
        "legislador_id":pd.NA,
        "legislador_nombre":vot["diputadoId"].map(leg_nom).astype("string").str.strip(),
        "bloque":vot["bloqueId"].map(blo_nom).astype("string").str.strip(),
        "distrito":vot["diputadoId"].map(leg_dist),
        "voto":vot["voto"].map(VOTO),
        "fuente":FUENTE,
    }).dropna(subset=["legislador_nombre","voto"])

    f=pd.to_datetime(asu_idx["fecha"], format="%m/%d/%Y", errors="coerce")
    actas=pd.DataFrame({
        "schema_version":SV,
        "acta_id":f"{FUENTE}:{pre}:"+asu_idx.index.astype(str),
        "camara":camara,
        "fecha":f.dt.strftime("%Y-%m-%d"),
        "periodo":pd.NA,
        "titulo":asu_idx["titulo"].fillna(asu_idx["asunto"]).astype("string").str.strip(),
        "expediente":asu_idx["titulo"].astype("string").str.extract(r"(\d+-[A-Za-z]+-\d+)",expand=False),
        "tipo_mayoria":asu_idx["mayoria"].astype("string").str.strip(),
        "resultado":asu_idx["resultado"].astype("string").str.strip(),
        "n_afirmativos":pd.to_numeric(asu_idx["afirmativos"],errors="coerce").astype("Int64"),
        "n_negativos":pd.to_numeric(asu_idx["negativos"],errors="coerce").astype("Int64"),
        "n_abstenciones":pd.to_numeric(asu_idx["abstenciones"],errors="coerce").astype("Int64"),
        "n_ausentes":pd.to_numeric(asu_idx["ausentes"],errors="coerce").astype("Int64"),
        "fuente":FUENTE,
    })
    return actas, votos

def main():
    src=Path(os.environ.get("CSV","."))
    out=Path(os.environ.get("OUT", Path(__file__).resolve().parents[1]/"data"/"clean")); out.mkdir(parents=True,exist_ok=True)
    ad,vd=parse(src,"diputados","votaciones-diputados.csv","asuntos-diputados.csv","diputados.csv","bloques-diputados.csv","diputadoID","nombre","distrito")
    asn,vs=parse(src,"senado","votaciones-senado.csv","asuntos-senado.csv","senadores.csv","bloques-senado.csv","diputadoId","nombre","distrito")
    # Evitar solapamiento con CKAN (Diputados 2011+): la semilla de Diputados solo hasta 2010.
    ya=pd.to_datetime(ad["fecha"],errors="coerce").dt.year
    keep=ad[(ya<=2010)|ya.isna()]["acta_id"]
    ad=ad[ad["acta_id"].isin(keep)]; vd=vd[vd["acta_id"].isin(keep)]
    actas=pd.concat([ad,asn],ignore_index=True); votos=pd.concat([vd,vs],ignore_index=True)
    actas.to_parquet(out/"decada_votada_actas.parquet",index=False)
    votos.to_parquet(out/"decada_votada_votos.parquet",index=False)
    aa=pd.to_datetime(actas["fecha"],errors="coerce").dt.year
    print(f"DIP actas={len(actas)} votos={len(votos)} años={int(aa.min())}-{int(aa.max())}")
    print("voto dist:",votos['voto'].value_counts().to_dict())

if __name__=="__main__": main()
