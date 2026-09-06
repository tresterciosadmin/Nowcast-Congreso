"""datos/manual_2026/src/to_canonical.py
Integra el Excel hecho a mano (período 2025-2027) al esquema canónico.
Hojas Diputados/Senado: columnas de padrón + una columna por ley con el voto de
cada legislador. Cada (ley, cámara) con votos -> un acta.

## El Excel aporta los VOTOS. La identidad se resuelve contra el PADRÓN (06-09-2026)

Antes, `distrito` y `bloque` salían de las columnas del Excel. El 06-09 se encontró
que la columna **PROVINCIA de la hoja Senado estaba desalineada**: 66 de 72 senadores
tenían el distrito de otro. No era un corrimiento —ningún offset lo explicaba— sino una
**permutación**: las 72 provincias correctas estaban todas, repartidas entre los
legisladores equivocados. Es la firma de un "ordenar sin extender la selección". El
`bloque` tenía además 8 etiquetas viejas.

Y no dio error: el dato entró a la canónica y ahí se quedó. En este repo ese es el modo
de fallar más caro.

**Desde entonces:** el Excel es la fuente de los **votos**; el **distrito** se resuelve
contra el padrón oficial —es un atributo estable, no cambia mientras dure la banca— y
cada discrepancia se reporta. Lo que no cruza contra el padrón conserva lo del Excel y
se cuenta aparte.

**El BLOQUE se reporta pero NO se pisa**, y la diferencia importa: el bloque depende del
tiempo. El del Excel es contemporáneo a esos votos; el del padrón es la foto vigente.
Pisarlo le pondría a un voto de marzo el bloque de agosto — leakage, y del que no da
error. Cuando difieren, decide una persona.

**Y se compara NORMALIZADO.** El padrón guarda "Santa Fe" y el Excel "SANTA FE": una
comparación sensible a mayúsculas "corrige" 256 filas que estaban perfectas. Pasó al
escribir esto, el 06-09.

La hoja Diputados estaba bien (256/256), así que esto no es sólo para el Senado: es
para que la próxima vez que se desalinee una columna, se entere alguien.
"""
from __future__ import annotations
import os, re, unicodedata
from pathlib import Path
import openpyxl, pandas as pd

SV, FUENTE = 1, "manual_2026"
RAIZ = Path(__file__).resolve().parents[3]
PADRON = {"diputados": RAIZ / "datos/padron/data/padron_diputados.csv",
          "senado": RAIZ / "datos/padron/data/padron_senado.csv"}


def _norm(x):
    """Para COMPARAR, no para guardar: sin acentos, en mayuscula, sin espacios de mas."""
    x = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode()
    x = " ".join(x.upper().split())
    for a, b in (("CIUDAD AUTONOMA DE BUENOS AIRES", "CABA"), ("CIUDAD DE BUENOS AIRES", "CABA"),
                 ("C.A.B.A.", "CABA"),
                 ("TIERRA DEL FUEGO, ANTARTIDA E ISLAS DEL ATLANTICO SUR", "TIERRA DEL FUEGO")):
        x = x.replace(a, b)
    return x


def _clave(nombre):
    """Clave invariante al orden Apellido/Nombre, como en datos/canonica."""
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    return " ".join(sorted(set(t for t in re.split(r"[^A-Za-z]+", s.upper()) if len(t) > 1)))


def cargar_padron(camara):
    """{clave: (distrito, bloque)} del padron oficial. Vacio si no esta el archivo."""
    p = PADRON.get(camara)
    if not p or not p.exists():
        print(f"  ! sin padron de {camara} ({p}): distrito y bloque quedan como vienen del Excel")
        return {}
    d = pd.read_csv(p, dtype=str, keep_default_na=False)
    if not {"legislador", "distrito", "bloque"} <= set(d.columns):
        print(f"  ! {p.name} no tiene las columnas esperadas: {list(d.columns)[:6]}")
        return {}
    # una fila por persona: la mas reciente si hay tramos
    if "desde" in d.columns:
        d = d.sort_values("desde").drop_duplicates("legislador", keep="last")
    return {_clave(r.legislador): (r.distrito, r.bloque) for r in d.itertuples()}
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
    pad = cargar_padron(camara)
    disc = {"distrito": [], "bloque": [], "sin_padron": set()}
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
            # EL PADRON MANDA sobre el DISTRITO (ver el docstring). Se compara
            # NORMALIZADO: el padron guarda "Santa Fe" y el Excel "SANTA FE", y una
            # comparacion sensible a mayusculas "corrige" 256 filas que estaban bien.
            #
            # EL BLOQUE NO SE PISA, a proposito. El bloque depende del TIEMPO: el del
            # Excel es contemporaneo a esos votos y el del padron es la foto vigente.
            # Pisarlo le pondria a un voto de marzo el bloque de agosto — leakage, y
            # del que no da error. Se reporta y decide una persona.
            k = _clave(nombre)
            if k in pad:
                d_ok, b_ok = pad[k]
                if d_ok and _norm(dist) != _norm(d_ok):
                    disc["distrito"].append((nombre, dist, d_ok)); dist = d_ok
                if b_ok and _norm(blo) != _norm(b_ok):
                    disc["bloque"].append((nombre, blo, b_ok))       # SOLO se reporta
            elif pad:
                disc["sin_padron"].add(nombre)
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
    _reportar(camara, disc, len({v["legislador_nombre"] for v in votos}))
    return actas, votos


def _reportar(camara, disc, n_personas):
    """Una discrepancia silenciosa es el modo de fallar mas caro de este repo."""
    nd, nb, ns = len({x[0] for x in disc["distrito"]}), len({x[0] for x in disc["bloque"]}), len(disc["sin_padron"])
    if not (nd or nb or ns):
        print(f"  {camara}: Excel y padron coinciden en distrito y bloque ({n_personas} personas)")
        return
    print(f"  {camara}: el padron CORRIGIO el distrito de {nd} personas; el bloque "
          f"DIFIERE en {nb} (no se pisa, ver el docstring); sin cruzar: {ns}")
    for etq in ("distrito", "bloque"):
        vistos = set()
        for nombre, viejo, nuevo in disc[etq]:
            if nombre in vistos:
                continue
            vistos.add(nombre)
            print(f"     {etq:9s} {nombre:34s} {viejo!r} -> {nuevo!r}")
    if ns:
        print(f"     sin match en el padron: {sorted(disc['sin_padron'])[:6]}")
    if nd > n_personas * 0.5:
        print(f"  !! MAS DE LA MITAD de los distritos del Excel no coinciden con el padron.")
        print(f"     Eso no es una fila mal cargada: es una COLUMNA desalineada.")
        print(f"     Paso el 06-09-2026 con la hoja Senado (66 de 72). Revisa el Excel.")

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
