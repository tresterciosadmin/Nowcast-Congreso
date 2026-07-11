"""Explorador del TRÁMITE PARLAMENTARIO de Diputados (paso 0 del adaptador Dip).
El TP es el diario oficial de ingresos: todo lo presentado cada día con TODOS
los firmantes y giros. Este script baja el índice del año y 2 TP de muestra a
datos/Archivos_Borrar/tp_diputados/ para diseñar el parser sobre HTML real.
Correr en PC con internet:  python datos/bot_recoleccion/src/explorar_tp.py
"""
from pathlib import Path
import requests, time

H={"User-Agent":"nowcast-congreso/0.1 (datos/bot_recoleccion)"}
OUT=Path(__file__).resolve().parents[3]/"datos"/"Archivos_Borrar"/"tp_diputados"
OUT.mkdir(parents=True,exist_ok=True)
CANDIDATAS=[  # URLs reales (verificadas por búsqueda 11-07-2026)
 "https://www.hcdn.gob.ar/secparl/dsecretaria/s_t_parlamentario/tramites-parlamentarios.html",
 "https://www2.hcdn.gob.ar/secparl/dsecretaria/s_t_parlamentario/2026/tp_001.html",
 "https://www2.hcdn.gob.ar/secparl/dsecretaria/s_t_parlamentario/2026/tp_080.html",
 "https://www.hcdn.gob.ar/proyectos/boletin-de-asuntos-entrados",
]
for url in CANDIDATAS:
    try:
        r=requests.get(url,headers=H,timeout=60); r.raise_for_status()
        dest=OUT/("indice_"+url.split("/")[-2 if url.endswith('/') else -1].replace(".html","")+".html")
        dest.write_text(r.text,encoding=r.encoding or "utf-8")
        print(f"OK {url} -> {dest.name} ({len(r.text)//1024} KB)")
    except requests.RequestException as e:
        print(f"FALLO {url}: {e}")
    time.sleep(0.5)
print("Si algún índice bajó, abrilo y copiá también la URL de un TP puntual si se ve; avisale a Claude.")
