"""datos/manual_2026/src/to_canonical.py
Integra el Excel hecho a mano (período 2025-2027) al esquema canónico.
Hojas Diputados/Senado: columnas de padrón + una columna por ley con el voto de
cada legislador. Cada (ley, cámara) con votos -> un acta. Aporta el BLOQUE del Senado.
"""
from __future__ import annotations
import os, re, unicodedata
from pathlib import Path
import openpyxl, pandas as pd

SV, FUENTE = 1, "manual_2026"
def _slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","_", s).strip("_")[:40]
def _voto(v):
    if v is None: return None
    s = unicodedata.normalize("NFKD", str(v)).encode("ascii","ignore").decode().upper().strip()
    if not s: return None
    if "PENDIENTE" in s: return None          # banca no incorporada -> excluir
    if s.startswith("AFIRMATIV"): return "AFIRMATIVO"
    if s.startswith("NEGATIV"): return "NEGATIVO"
    if s.startswith("ABSTEN"): return "ABSTENCION"
    if s.startswith("AUSENTE") or s.startswith("PRESIDENTE"): return "AUSENTE"
    return None

def parse_hoja(ws, cols, camara):
    rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
    c = cols  # dict con índices de columnas de padrón
    leyes = list(range(c["primera_ley"], len(hdr)))
    votos, actas = [], []
    for li in leyes:
        ley = str(hdr[li]).strip() if hdr[li] else None
        if not ley: continue
        acta_id = f"{FUENTE}:{camara}:{_slug(ley)}"
        vrows, cnt = [], {"AFIRMATIVO":0,"NEGATIVO":0,"ABSTENCION":0,"AUSENTE":0}
        for r in rows[1:]:
            ap = r[c["apellido"]]; no = r[c["nombre"]]
            if not ap and not no: continue
            vt = _voto(r[li]) if li < len(r) else None
            if vt is None: continue
            nombre = f"{str(ap).strip()}, {str(no).strip()}"
            blo = (str(r[c["bloque"]]).strip() if r[c["bloque"]] else "SIN BLOQUE")
            dist = (str(r[c["distrito"]]).strip() if r[c["distrito"]] else None)
            vrows.append(dict(schema_version=SV, acta_id=acta_id, legislador_id=None,
                legislador_nombre=nombre, bloque=blo, distrito=dist, voto=vt, fuente=FUENTE))
            cnt[vt]+=1
        if not vrows: continue
        votos += vrows
        actas.append(dict(schema_version=SV, acta_id=acta_id, camara=camara, fecha=None,
            periodo=None, titulo=ley, expediente=None, tipo_mayoria=None,
            resultado=("AFIRMATIVO" if cnt["AFIRMATIVO"]>cnt["NEGATIVO"] else "NEGATIVO"),
            n_afirmativos=cnt["AFIRMATIVO"], n_negativos=cnt["NEGATIVO"],
            n_abstenciones=cnt["ABSTENCION"], n_ausentes=cnt["AUSENTE"], fuente=FUENTE))
    return actas, votos

def main():
    xlsx = os.environ.get("XLSX")
    out = Path(os.environ.get("OUT", Path(__file__).resolve().parents[1] / "data" / "clean"))
    out.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ad, vd = parse_hoja(wb["Diputados"], {"apellido":1,"nombre":2,"distrito":3,"bloque":6,"primera_ley":8}, "diputados")
    asn, vsn = parse_hoja(wb["Senado"], {"apellido":2,"nombre":1,"distrito":4,"bloque":3,"primera_ley":17}, "senado")
    actas = pd.DataFrame(ad+asn); votos = pd.DataFrame(vd+vsn)
    for col in ["periodo","n_afirmativos","n_negativos","n_abstenciones","n_ausentes"]:
        actas[col] = pd.to_numeric(actas[col], errors="coerce").astype("Int64")
    actas.to_parquet(out/"manual_2026_actas.parquet", index=False)
    votos.to_parquet(out/"manual_2026_votos.parquet", index=False)
    print(f"actas={len(actas)} (dip={len(ad)} sen={len(asn)}) votos={len(votos)}")
    print("bloques Senado (muestra):", sorted(votos[votos.acta_id.str.contains('senado')].bloque.unique())[:8])

if __name__=="__main__": main()
