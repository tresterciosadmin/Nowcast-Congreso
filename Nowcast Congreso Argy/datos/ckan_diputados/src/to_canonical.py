"""datos/ckan_diputados/src/to_canonical.py
Normaliza CKAN Diputados (votaciones nominales, períodos 129-137 ≈ 2011-2020) al
esquema canónico. Combina el bundle histórico (129-137, 2011-2018) con el recurso
del período 137 (2019-2020) para no dejar el hueco de 2019.
"""
from __future__ import annotations
import io, os, time
from pathlib import Path
import pandas as pd, requests
from requests.exceptions import ConnectionError as CE, HTTPError, Timeout

SV, FUENTE, CAMARA = 1, "ckan_diputados", "diputados"
API = "https://datos.hcdn.gob.ar/api/3/action/resource_show?id="
H = {"User-Agent": "nowcast-congreso/0.1"}
# (cabecera, detalle) por tramo
RES = [("28bdc184-d8e3-4d50-b5b5-e2151f902ac7", "262cc543-3186-401b-b35e-dcdb2635976d"),  # 129-137 (2011-2018)
       ("59c05ba8-ad0a-4d55-803d-20e3fe464d0b", "f86728ed-d4b9-479e-b939-a9841fd6d8d3")]  # período 137 (2019-2020)

def _req(url):
    last=None
    for i in range(4):
        try:
            r=requests.get(url,headers=H,timeout=180); r.raise_for_status(); return r
        except (CE,Timeout,HTTPError) as e: last=e; time.sleep(2*(i+1))
    raise RuntimeError(f"GET {url}: {last}")

def _csv(rid):
    url=_req(API+rid).json()["result"]["url"]
    return pd.read_csv(io.BytesIO(_req(url).content), sep=None, engine="python")

def _norm_voto(s):
    v=s.astype("string").str.upper().str.strip().str.normalize("NFKD").str.encode("ascii","ignore").str.decode("ascii")
    out=pd.Series("AUSENTE",index=v.index)
    out[v.str.contains("AFIRMATIV|^SI$|POSITIV",regex=True,na=False)]="AFIRMATIVO"
    out[v.str.contains("NEGATIV|^NO$",regex=True,na=False)]="NEGATIVO"
    out[v.str.contains("ABSTEN",na=False)]="ABSTENCION"
    return out

def main():
    out=Path(os.environ.get("OUT", Path(__file__).resolve().parents[1]/"data"/"clean")); out.mkdir(parents=True,exist_ok=True)
    cab=pd.concat([_csv(c) for c,_ in RES],ignore_index=True).drop_duplicates("acta_id")
    det=pd.concat([_csv(d) for _,d in RES],ignore_index=True).drop_duplicates(["acta_id","diputado_nombre"])

    actas=pd.DataFrame({
        "schema_version":SV,"acta_id":FUENTE+":"+cab["acta_id"].astype(str),"camara":CAMARA,
        "fecha":pd.to_datetime(cab["fecha"],errors="coerce").dt.strftime("%Y-%m-%d"),
        "periodo":pd.to_numeric(cab["nroperiodo"],errors="coerce").astype("Int64"),
        "titulo":cab["titulo"].astype("string").str.strip(),
        "expediente":cab["titulo"].astype("string").str.extract(r"(\d+-[A-Za-z]+-\d+)",expand=False),
        "tipo_mayoria":cab["tipo_mayoria"].astype("string").str.strip(),
        "resultado":cab["resultado"].astype("string").str.strip(),
        "n_afirmativos":pd.to_numeric(cab["votos_afirmativos"],errors="coerce").astype("Int64"),
        "n_negativos":pd.to_numeric(cab["votos_negativos"],errors="coerce").astype("Int64"),
        "n_abstenciones":pd.to_numeric(cab["abstenciones"],errors="coerce").astype("Int64"),
        "n_ausentes":pd.to_numeric(cab["ausentes"],errors="coerce").astype("Int64"),"fuente":FUENTE})
    votos=pd.DataFrame({
        "schema_version":SV,"acta_id":FUENTE+":"+det["acta_id"].astype(str),"legislador_id":pd.NA,
        "legislador_nombre":det["diputado_nombre"].astype("string").str.strip(),
        "bloque":det["bloque"].astype("string").str.strip(),
        "distrito":det["distrito_nombre"].astype("string").str.strip(),
        "voto":_norm_voto(det["voto"]),"fuente":FUENTE}).dropna(subset=["legislador_nombre","bloque"])

    actas.to_parquet(out/"ckan_diputados_actas.parquet",index=False)
    votos.to_parquet(out/"ckan_diputados_votos.parquet",index=False)
    aa=pd.to_datetime(actas["fecha"],errors="coerce").dt.year
    print(f"OK actas={len(actas)} votos={len(votos)} años={int(aa.min())}-{int(aa.max())} -> {out}")

if __name__=="__main__": main()
