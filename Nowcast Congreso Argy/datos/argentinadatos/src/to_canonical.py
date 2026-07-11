"""datos/argentinadatos/src/to_canonical.py
Normaliza argentinadatos (Diputados 2020-2025, Senado 2024-2025) al esquema canónico.
Diputados: el detalle de voto NO trae bloque -> se resuelve cruzando con el padrón
(`/diputados/diputados`, campo periodoBloque con fechas) por nombre + fecha del acta.
Senado: la fuente no trae bloque -> se resuelve con el PADRÓN DE BLOQUES de
datos/senado (CSVs versionados = contrato publicado de ese módulo: el manual
gana sobre el automático, matching por clave de tokens con fallback por
variantes del mismo nombre, ventana [desde, hasta] por fecha del acta).
Lo que no matchea queda 'SIN BLOQUE' y se reporta.
(Retro-completado 2026-07-11; antes TODO el Senado iba SIN BLOQUE.)
"""
from __future__ import annotations
import json, os, time, unicodedata
from pathlib import Path
import pandas as pd, requests
from requests.exceptions import ConnectionError as CE, HTTPError, Timeout

SV, BASE = 1, "https://api.argentinadatos.com/v1"
H = {"User-Agent": "nowcast-congreso/0.1"}

def _get(path):
    last=None
    for i in range(4):
        try:
            r=requests.get(BASE+path,headers=H,timeout=120); r.raise_for_status(); return r.json()
        except (CE,Timeout,HTTPError) as e: last=e; time.sleep(2*(i+1))
    raise RuntimeError(f"GET {path}: {last}")

def _key(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().upper()
    return " ".join(s.replace(",", " ").split())

def _voto(x):
    v=_key(x)
    if "AFIRMATIV" in v or v=="SI": return "AFIRMATIVO"
    if "NEGATIV" in v or v=="NO": return "NEGATIVO"
    if "ABSTEN" in v: return "ABSTENCION"
    return "AUSENTE"  # incluye 'presidente', 'ausente', etc.

# --- Padrón de bloques del Senado (consume el CONTRATO de datos/senado) ---
_PARTICULAS={"DE","DEL","LA","LAS","LOS","Y","E","VAN","VON","DI","DA"}

def _clave(n):
    import re
    toks=[t for t in re.split(r"[^A-Z]+",_key(n)) if len(t)>1 and t not in _PARTICULAS]
    return " ".join(sorted(set(toks)))

def _padron_senado():
    """Lee los CSV versionados de datos/senado (manual primero: gana en solapes)."""
    import csv
    base=Path(__file__).resolve().parents[2]/"senado"/"data"
    idx={}
    for f in (base/"padron_manual_2015_2017.csv", base/"padron_bloques_senado.csv"):
        if not f.exists(): continue
        with open(f,encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if r.get("bloque"):
                    idx.setdefault(r["clave"],[]).append(
                        (r["desde"], r.get("hasta") or "9999-12-31", r["bloque"]))
    return idx

def _bloque_sen(idx,nombre,fecha):
    k=_clave(nombre); filas=list(idx.get(k,[]))
    if not filas:  # fallback: variantes del mismo nombre (subconjunto de tokens)
        toks=set(k.split())
        cands=[c for c in idx if c!=k and (toks<=set(c.split()) or set(c.split())<=toks)]
        if len(cands)>1:
            variantes=all(set(a.split())<=set(b.split()) or set(b.split())<=set(a.split())
                          for i,a in enumerate(cands) for b in cands[i+1:])
            if not variantes: cands=[]
        filas=[fl for c in cands for fl in idx[c]]
    for d,h,b in filas:
        if d<=(fecha or "")<=h: return b
    return "SIN BLOQUE"

def _roster_dip():
    ros=_get("/diputados/diputados/")
    idx={}
    for r in ros:
        k=_key(f"{r.get('apellido','')} {r.get('nombre','')}")
        pb=r.get("periodoBloque") or {}
        idx.setdefault(k,[]).append((str(pb.get("inicio",""))[:10], str(pb.get("fin",""))[:10] or "9999-12-31",
                                     r.get("bloque") or "SIN BLOQUE", r.get("provincia")))
    return idx

def _bloque_at(idx,nombre,fecha):
    for ini,fin,blo,prov in idx.get(_key(nombre),[]):
        if (ini=="" or ini<=fecha) and fecha<=fin: return blo,prov
    rows=idx.get(_key(nombre))
    return (rows[-1][2], rows[-1][3]) if rows else ("SIN BLOQUE", None)

def main():
    out=Path(os.environ.get("OUT", Path(__file__).resolve().parents[1]/"data"/"clean")); out.mkdir(parents=True,exist_ok=True)
    actas_rows, votos_rows = [], []

    # --- Diputados ---
    idx=_roster_dip()
    for a in _get("/diputados/actas/"):
        fecha=str(a.get("fecha",""))[:10]; aid=f"argentinadatos:diputados:{a.get('id')}"
        vs=a.get("votos") or []
        for v in vs:
            blo,prov=_bloque_at(idx, v.get("diputado",""), fecha)
            votos_rows.append(dict(schema_version=SV,acta_id=aid,legislador_id=None,
                legislador_nombre=str(v.get("diputado","")).strip(),bloque=blo,distrito=prov,
                voto=_voto(v.get("tipoVoto")),fuente="argentinadatos"))
        actas_rows.append(dict(schema_version=SV,acta_id=aid,camara="diputados",fecha=fecha or None,
            periodo=a.get("periodo"),titulo=str(a.get("titulo","")).strip() or "(sin titulo)",expediente=None,
            tipo_mayoria=None,resultado=a.get("resultado"),
            n_afirmativos=a.get("votosAfirmativos"),n_negativos=a.get("votosNegativos"),
            n_abstenciones=a.get("abstenciones"),n_ausentes=a.get("ausentes"),fuente="argentinadatos"))

    # --- Senado (bloque desde el padrón versionado de datos/senado) ---
    idx_sen=_padron_senado()
    for a in _get("/senado/actas/"):
        fecha=str(a.get("fecha",""))[:10]; aid=f"argentinadatos:senado:{a.get('actaId')}"
        for v in (a.get("votos") or []):
            votos_rows.append(dict(schema_version=SV,acta_id=aid,legislador_id=None,
                legislador_nombre=str(v.get("nombre","")).strip(),
                bloque=_bloque_sen(idx_sen, v.get("nombre",""), fecha),
                distrito=(v.get("banca") or None),voto=_voto(v.get("voto")),fuente="argentinadatos"))
        actas_rows.append(dict(schema_version=SV,acta_id=aid,camara="senado",fecha=fecha or None,
            periodo=None,titulo=str(a.get("titulo","")).strip() or "(sin titulo)",expediente=None,
            tipo_mayoria=a.get("mayoria"),resultado=a.get("resultado"),
            n_afirmativos=a.get("afirmativos"),n_negativos=a.get("negativos"),
            n_abstenciones=a.get("abstenciones"),n_ausentes=a.get("ausentes"),fuente="argentinadatos"))

    actas=pd.DataFrame(actas_rows); votos=pd.DataFrame(votos_rows)
    for c in ["periodo","n_afirmativos","n_negativos","n_abstenciones","n_ausentes"]:
        actas[c]=pd.to_numeric(actas[c],errors="coerce").astype("Int64")
    votos=votos[votos["legislador_nombre"].str.len()>0]
    actas.to_parquet(out/"argentinadatos_actas.parquet",index=False)
    votos.to_parquet(out/"argentinadatos_votos.parquet",index=False)
    sinblo=(votos["bloque"]=="SIN BLOQUE").sum()
    es_sen=votos["acta_id"].str.contains(":senado:")
    print(f"OK actas={len(actas)} votos={len(votos)} sin_bloque={sinblo} -> {out}")
    print("  por cámara:",actas['camara'].value_counts().to_dict())
    print(f"  senado: {es_sen.sum()} votos, sin_bloque={int((es_sen&(votos['bloque']=='SIN BLOQUE')).sum())} "
          f"({100*(es_sen&(votos['bloque']=='SIN BLOQUE')).sum()/max(es_sen.sum(),1):.1f}%)")
    if (es_sen&(votos['bloque']=='SIN BLOQUE')).any():
        top=votos[es_sen&(votos['bloque']=='SIN BLOQUE')]['legislador_nombre'].value_counts().head(5)
        print("  sin match en padrón (top):",top.to_dict())

if __name__=="__main__": main()
