"""variables/proyecto/src/classify_tema_v1.py
Clasificador granular por PUNTAJE sobre el texto del proyecto (no el título).
Cuenta coincidencias de palabras clave por subtema y elige el de mayor puntaje.
Devuelve (area, subtema). Reglas ampliables; la versión final puede ir a embeddings/LLM.
"""
from __future__ import annotations
import re, unicodedata
def _n(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower())

# (area, subtema, [keywords])  -- keywords en minúscula sin acento
RULES = [
 ("ECONOMIA","Presupuesto y gasto",["presupuesto","credito presupuestario","gasto publico","administracion nacional","recursos y gastos"]),
 ("ECONOMIA","Tributario/Impuestos",["impuesto","tributari","ganancias","iva","monotributo","alicuota","exencion","blanqueo","regularizacion de activos","inocencia fiscal"]),
 ("ECONOMIA","Deuda y financiamiento",["deuda publica","endeudamiento","titulos publicos","bonos"]),
 ("ECONOMIA","Monetario y cambiario",["banco central","politica monetaria","tipo de cambio","estabilidad monetaria","reservas"]),
 ("PRODUCCION","Promocion de inversiones (RIGI)",["regimen de incentivo","grandes inversiones","rigi","promocion de inversiones","incentivo para"]),
 ("PRODUCCION","Regimenes especiales",["zona fria","zonas frias","regimen de promocion","beneficio fiscal regional"]),
 ("PRODUCCION","Agro/pesca",["agricola","ganader","pesca","agropecuari"]),
 ("DESREGULACION","Desregulacion economica",["desregulacion","deroga","derogase","simplificacion","desburocratizacion","hojarasca","eliminanse normas"]),
 ("JUSTICIA","Codigo civil/comercial/sociedades",["codigo civil","codigo comercial","codigo civil y comercial","sociedades comerciales","ley general de sociedades","sociedad anonima","sociedad por acciones","registro publico de comercio","directorio","asamblea de accionistas","capital social","19550","sociedad de responsabilidad"]),
 ("TRABAJO","Relaciones laborales",["contrato de trabajo","relaciones laborales","modernizacion laboral","convenio colectivo","jornada laboral","indemnizacion","periodo de prueba"]),
 ("TRABAJO","Previsional/jubilaciones",["jubilacion","previsional","haber jubilatorio","movilidad jubilatoria","anses","reparto"]),
 ("ENERGIA","Energia",["hidrocarburo","energia electrica","gas natural","combustible","tarifa energetica","energias renovables"]),
 ("AMBIENTE","Bosques/glaciares/agua",["glaciar","bosque nativo","ambient","periglacial","area protegida","recurso hidrico"]),
 ("AMBIENTE","Mineria",["mineria","minero","yacimiento"]),
 ("SALUD","Salud mental/adicciones",["salud mental","adiccion","ludopatia","apuestas","juego online","consumo problematico"]),
 ("SALUD","Sistema de salud",["sistema de salud","hospital","medicament","obra social","sanitari"]),
 ("EDUCACION","Educacion superior",["universi","financiamiento universitario","educacion superior"]),
 ("EDUCACION","Educacion basica",["educacion inicial","educacion primaria","escuela","docente"]),
 ("CIENCIA","Propiedad intelectual/patentes",["patente","propiedad intelectual","tratado de cooperacion en materia de patentes","pct","marcas"]),
 ("CIENCIA","Ciencia y tecnica",["ciencia y tecnologia","conicet","investigacion cientifica","economia del conocimiento"]),
 ("JUSTICIA","Penal/codigo penal",["codigo penal","pena privativa","delito","punib"]),
 ("JUSTICIA","Regimen penal juvenil",["penal juvenil","menor de edad","adolescente","responsabilidad penal de"]),
 ("JUSTICIA","Propiedad (inviolabilidad)",["inviolabilidad de la propiedad","propiedad privada","expropiacion","derecho de propiedad"]),
 ("JUSTICIA","Organizacion judicial",["consejo de la magistratura","juez","poder judicial","procesal"]),
 ("DEFENSA_RREE","Tratados internacionales",["mercosur","union europea","tratado","acuerdo entre","protocolo adicional","aprobacion del acuerdo","convencion internacional"]),
 ("DEFENSA_RREE","Defensa",["fuerzas armadas","defensa nacional","seguridad interior"]),
 ("DERECHOS","Genero/derechos",["violencia de genero","identidad de genero","derechos humanos","diversidad","interrupcion del embarazo"]),
 ("REGIMEN_POLITICO","Electoral",["codigo electoral","sistema electoral","boleta unica","reforma electoral","sufragio","primarias"]),
 ("REGIMEN_POLITICO","Transparencia/lobby",["lobby","gestion de intereses","etica publica","transparencia","conflicto de intereses"]),
 ("DESARROLLO_SOCIAL","Pensiones no contributivas",["pension por invalidez","pension no contributiva","fraude de pensiones"]),
]

def clasificar(texto):
    s=_n(texto)
    best=("SIN CLASIFICAR","SIN CLASIFICAR",0)
    for area,sub,kws in RULES:
        sc=sum(len(re.findall(r"\b"+re.escape(k),s)) for k in kws)
        if sc>best[2]: best=(area,sub,sc)
    return best[0],best[1],best[2]

if __name__=="__main__":
    import sys,glob,os
    for p in sorted(glob.glob("/tmp/leytxt/*.txt")):
        t=open(p).read()
        if len(t)<400: print(f"{'(OCR pendiente)':>22} | {os.path.basename(p)[:45]}"); continue
        a,sub,sc=clasificar(t)
        print(f"{a:>18} / {sub:<32} sc={sc:<3} | {os.path.basename(p)[:42]}")
