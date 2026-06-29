"""variables/proyecto/src/classify_tema.py  (v0, reglas por palabra clave)
Asigna una materia/tema a cada acta a partir del título. PRIMER PASE: reglas
simples; el texto del título suele ser pobre (referencia al expediente), así que
la versión buena necesitará el texto del expediente (datos/expedientes) + NLP.
"""
from __future__ import annotations
import json, os, re, unicodedata
from pathlib import Path
import pandas as pd

def _n(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)

# Orden = prioridad. Primer match gana.
TAXONOMIA = [
 ("TRAMITE PARLAMENTARIO", r"sobre tablas|apartamiento del reglamento|mocion de preferencia|incorporacion del expediente|cuestion de privilegio|plan de labor|prorroga de la sesion|juramento|apertura del sobre|orden del dia|votacion en general|tratamiento"),
 ("HOMENAJES Y DECLARACIONES", r"homenaje|beneplacito|de interes|repudio|adhesion|pesar|reconocimiento|capital nacional|dia nacional|dia mundial|designa\w* con el nombre|monumento|fiesta nacional"),
 ("ECONOMIA Y HACIENDA", r"presupuesto|impuest|tribut|fiscal|deuda|arancel|tarifa|ganancias|monotributo|coparticipacion|emergencia economica|financ|credito|moneda|inflacion|aduana|iva"),
 ("TRABAJO Y PREVISION SOCIAL", r"laboral|trabajo|empleo|jubilac|previsional|pension|sindical|convenio colectivo|riesgos del trabajo|obra social|salario"),
 ("SALUD", r"salud|sanitari|hospital|medicament|vacuna|enfermedad|oncolog|emergencia sanitaria|discapacidad"),
 ("EDUCACION CIENCIA Y CULTURA", r"educa|universi|escuela|docente|ciencia|tecnolog|cultura|patrimonio|deporte"),
 ("SEGURIDAD Y DEFENSA", r"seguridad|defensa|fuerzas armadas|gendarmeria|policia|narcotrafico|terroris"),
 ("JUSTICIA Y PENAL", r"codigo penal|penal|delito|justicia|judicial|procesal|magistrad|excarcelacion|prision|codigo civil"),
 ("DERECHOS Y GENERO", r"derechos humanos|genero|mujer|igualdad|identidad de genero|interrupcion.*embarazo|aborto|violencia|diversidad|niñez|infancia"),
 ("AMBIENTE Y ENERGIA", r"ambient|bosque|glaciar|agua|mineria|hidrocarbur|energia|combustible|petroleo|renovable|residuos|climatic"),
 ("INFRAESTRUCTURA Y TRANSPORTE", r"obra publica|transporte|vial|ruta|ferrocarril|aeropuerto|puerto|vivienda|infraestructura"),
 ("AGRO Y PRODUCCION", r"agro|agricola|ganader|pesca|industri|pyme|produccion|comercio"),
 ("RELACIONES EXTERIORES Y TRATADOS", r"tratado|convenio.*internacional|acuerdo.*(con|entre)|protocolo|relaciones exteriores|mercosur|naciones unidas"),
 ("REGIMEN POLITICO Y ELECTORAL", r"electoral|sufragio|partidos politicos|reforma constitucional|codigo electoral|boleta|primarias|ciudadania"),
 ("ADMINISTRACION DEL ESTADO", r"ministerio|organismo|administracion publica|estructura del estado|ente nacional|emergencia publica"),
]
RX = [(t, re.compile(p)) for t, p in TAXONOMIA]

def clasificar(titulo):
    s = _n(titulo)
    for t, rx in RX:
        if rx.search(s): return t
    return "SIN CLASIFICAR"

def main():
    src = Path(os.environ.get("CANON", Path(__file__).resolve().parents[3] / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", Path(__file__).resolve().parents[1] / "outputs"))
    a = pd.read_parquet(src / "actas_canonico.parquet")
    a["tema_v0"] = a["titulo"].map(clasificar)
    out.mkdir(parents=True, exist_ok=True)
    a[["acta_id", "camara", "titulo", "tema_v0"]].to_parquet(out / "actas_tema_v0.parquet", index=False)
    vc = a["tema_v0"].value_counts()
    print("actas:", len(a))
    print(vc.to_string())
    print(f"\nsin clasificar: {vc.get('SIN CLASIFICAR',0)} ({vc.get('SIN CLASIFICAR',0)/len(a):.0%})")
    print("\nEjemplos SIN CLASIFICAR:")
    for t in a[a.tema_v0=='SIN CLASIFICAR']['titulo'].head(6): print("  -", str(t)[:90])

if __name__ == "__main__":
    main()
