"""Genera un HTML interactivo del nowcast BICAMERAL de un proyecto de ley.

Entregable-simulacro para cliente: muestra las dos cámaras, la P(avance) de cada
una, el ICG del momento, y —por legislador— la probabilidad de votar a favor /
en contra / ser bisagra. Slider de ICG para ver la influencia del clima en vivo.

Corre el modelo (alineación con el gobierno, por legislador) y escribe el HTML
autocontenido (datos embebidos; se abre con doble clic, sin servidor).

    python casos/nowcast_bicameral_html.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
for sub in ("variables/proyecto/src", "variables/bloque/src", "modelo/ensemble/src",
            "modelo/agregador_institucional/src"):
    sys.path.insert(0, str(RAIZ / sub))
from bloque import (cargar as cargar_bloque, proyectar_postura,  # noqa: E402
                    cargar_tema_por_acta)
from ensemble import roster_nominal                        # noqa: E402

# ─── el proyecto hipotético y la coyuntura ───
# UNIFICADO 2026-08-14 (Parte B): la postura de bloque y el récord individual se
# CONDICIONAN por el ORIGEN FINO del proyecto (motor validado, 59%→76%). Antes se
# promediaban TODAS las leyes del gobierno (no distinguía PE de un aliado como PRO).
FECHA = "2026-06-01"
ASUNTO = "Reforma del impuesto a las ganancias"
SUBTITULO = "Iniciativa del Poder Ejecutivo · proyecto con media sanción, en revisión"
CAMARA_ORIGEN = "diputados"          # nace en Diputados; el Senado revisa
ORIGEN = "EJECUTIVO"                 # qué empuja el proyecto (EJECUTIVO/OFICIALISMO/ALIADOS/OPOSICION)
ICG_VALOR = 2.07                     # ICG de 2026-06 (icg_mensual.csv)
ICG_NEUTRO = 1.90                    # nivel de referencia (break-even reciente)
MES_MANDATO = 30

PADRON = {"diputados": RAIZ / "datos/padron/data/padron_diputados.csv",
          "senado": RAIZ / "datos/padron/data/padron_senado_historico.csv"}
DISC = RAIZ / "modelo/voto_individual/outputs/disciplina_individual.csv"


MIN_HIST = 8   # votos mínimos en proyectos del gobierno para usar el dato INDIVIDUAL


def alineacion_individual(votos, origen_map, era_desde="2023-12-10"):
    """P(afirmativo) de CADA legislador, medida sobre su PROPIO récord en proyectos
    del MISMO ORIGEN que el proyecto objetivo (CONDICIONADA — antes mezclaba todas
    las leyes del gobierno). Ausente/abstención/negativo cuentan como no-afirmativo.
    Es la regla fundacional (nivel legislador); el bloque queda como fallback.
    Devuelve {(camara, legislador_id): (p_af, n, presencia)}."""
    d = votos[votos["fecha"] >= pd.Timestamp(era_desde)].copy()
    d["ori"] = d["acta_id"].map(origen_map)
    d = d[d["ori"] == ORIGEN]                            # proyectos del origen objetivo
    V = d["conducta"].astype(str).str.upper().str[:2]
    d["af"] = V.eq("AF")
    d["emitio"] = V.isin(["AF", "NE"])                   # votó (no ausente/abstención)
    g = d.groupby(["camara", "legislador_id"]).agg(
        n=("af", "size"), p_af=("af", "mean"), presencia=("emitio", "mean"))
    return {idx: (float(r["p_af"]), int(r["n"]), float(r["presencia"]))
            for idx, r in g.iterrows()}


def datos_camara(camara, votos, cond, ind):
    # postura de bloque CONDICIONADA por el origen del proyecto (motor validado).
    bloques = proyectar_postura(votos, FECHA, camara, origen=ORIGEN, cond_por_acta=cond,
                                padron_path=str(PADRON[camara]))
    share = {b["bloque"]: b["_share_afirm"] for b in bloques}
    _, _, det = roster_nominal(camara, FECHA, bloques, padron_file=str(PADRON[camara]),
                               disciplina_path=str(DISC))
    legs = []
    for f in det["filas"]:
        lid = f["legislador_id"]
        p_ind, n_h, pres = ind.get((camara, lid), (None, 0, 1.0))
        a_bloque = share.get(f["bloque_linaje"], 0.5)   # _share_afirm ya es P(afirmativo) condicionada
        if p_ind is not None and n_h >= MIN_HIST:
            p_af, fuente = p_ind, "individual"          # su propio récord (mismo origen)
        else:
            p_af, fuente = a_bloque, "bloque"           # fallback (novato)
        legs.append({
            "nombre": f.get("legislador") or lid,
            "bloque": f["bloque_linaje"],
            "desvio": round(float(f["desvio"]), 3),
            "p_af": round(float(min(max(p_af, 0.02), 0.98)), 4),
            "n": int(n_h), "fuente": fuente,
            "presencia": round(float(pres), 3),         # emite voto / total
        })
    n = len(legs)
    return {"camara": camara, "n": n, "umbral": n // 2 + 1,
            "es_origen": camara == CAMARA_ORIGEN, "legisladores": legs}


def main():
    """NEUTRALIZADO 2026-08-22 — lo reemplaza `casos/nowcast_puertas_html.py`.

    Este generador calculaba el acompanamiento con el mecanismo que la auditoria del
    22-08 encontro con SIETE errores, y los tres de fondo cambian el resultado de
    verdad: el numero del bloque se redondeaba a SI/NO (la Coalicion Civica, que
    acompana el 60,9%, salia en 96,7%), la direccion salia del linaje mientras el
    desvio salia del bloque real (Del Caño salia en 100% con un record de 1%), y
    faltar se contaba como votar en contra (Menem, que preside y vota el 1,3% de las
    veces, aparecia EN CONTRA). Ademas el umbral usaba n//2+1, que es mayoria
    ABSOLUTA, no simple.

    No se borra para no perder el diseno del HTML, que se reuso. Pero no puede seguir
    corriendo: produciria numeros que alguien va a citar. Copia entera en
    Archivos_Borrar/BORRAR_casos-nowcast_bicameral_html.py
    """
    raise SystemExit(
        "nowcast_bicameral_html.py esta NEUTRALIZADO (2026-08-22): calculaba el "
        "acompanamiento con el mecanismo que tenia siete errores. Usa "
        "casos/nowcast_puertas_html.py, que corre la cadena de puertas. Ver el "
        "docstring de main y el ADR-0012.")


PLANTILLA = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nowcast Legislativo — proyección bicameral</title>
<style>
  :root{--bg:#0f1420;--card:#1a2233;--ink:#e8edf7;--mut:#8a97b0;--line:#2a3550;
        --si:#37c98a;--no:#f0616d;--bis:#f2b53c;--acc:#5b8cff;}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
  .wrap{max-width:1100px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:26px;margin:0 0 2px} .sub{color:var(--mut);margin:0 0 4px}
  .meta{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 24px}
  .chip{background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:8px 12px;font-size:13px} .chip b{color:var(--ink)}
  .chip .k{color:var(--mut);margin-right:6px}
  .icgbox{background:var(--card);border:1px solid var(--line);border-radius:12px;
          padding:14px 16px;margin-bottom:24px}
  .icgbox .row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  input[type=range]{flex:1;min-width:200px;accent-color:var(--acc)}
  .cams{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  @media(max-width:760px){.cams{grid-template-columns:1fr}}
  .cam{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
  .cam h2{margin:0 0 2px;font-size:19px} .cam .r{color:var(--mut);font-size:13px;margin-bottom:12px}
  .big{font-size:44px;font-weight:700;line-height:1} .big small{font-size:15px;color:var(--mut);font-weight:400}
  .verdict{font-size:13px;font-weight:600;margin-top:4px}
  .bar{height:14px;background:#0d1220;border-radius:8px;position:relative;margin:14px 0 4px;overflow:hidden}
  .bar>i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#2f6df6,#37c98a);border-radius:8px}
  .thr{position:absolute;top:-3px;bottom:-3px;width:2px;background:#fff}
  .barlab{display:flex;justify-content:space-between;font-size:12px;color:var(--mut)}
  .tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:22px 0 10px}
  select,input[type=search]{background:var(--card);border:1px solid var(--line);color:var(--ink);
    border-radius:8px;padding:7px 10px;font-size:13px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}
  th{color:var(--mut);cursor:pointer;user-select:none;font-weight:600}
  td.p{font-variant-numeric:tabular-nums;width:200px}
  .pb{height:9px;border-radius:5px;background:#0d1220;position:relative;overflow:hidden;display:inline-block;width:120px;vertical-align:middle;margin-right:8px}
  .pb>i{position:absolute;left:0;top:0;bottom:0}
  .badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px}
  .b-si{background:rgba(55,201,138,.16);color:var(--si)}
  .b-no{background:rgba(240,97,109,.16);color:var(--no)}
  .b-bis{background:rgba(242,181,60,.16);color:var(--bis)}
  .b-na{background:rgba(138,151,176,.18);color:var(--mut)}
  .foot{color:var(--mut);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}
  .tabbar{display:flex;gap:8px;margin:22px 0 0}
  .tab{background:var(--card);border:1px solid var(--line);border-radius:8px 8px 0 0;
       padding:8px 16px;cursor:pointer;font-size:13px;color:var(--mut)}
  .tab.on{color:var(--ink);border-bottom-color:var(--card);font-weight:600}
</style></head>
<body><div class="wrap">
  <h1 id="asunto"></h1><p class="sub" id="subtitulo"></p>
  <div class="meta" id="meta"></div>

  <div class="icgbox">
    <div class="row">
      <div><div style="font-size:13px;color:var(--mut)">Clima político (ICG)</div>
        <div style="font-size:22px;font-weight:700"><span id="icgv"></span>
        <small style="font-size:12px;color:var(--mut)" id="icgtag"></small></div></div>
      <input type="range" id="icg" min="1.0" max="3.0" step="0.01">
      <div style="font-size:12px;color:var(--mut);max-width:230px">
        Movés el índice y el nowcast se recalcula. El clima pesa más en los legisladores bisagra.</div>
    </div>
  </div>

  <div class="cams" id="cams"></div>

  <div class="tabbar" id="tabs"></div>
  <div class="tools">
    <input type="search" id="q" placeholder="Buscar legislador…">
    <select id="fbloque"><option value="">Todos los bloques</option></select>
    <span style="color:var(--mut);font-size:12px" id="cnt"></span>
  </div>
  <table><thead><tr>
    <th data-k="nombre">Legislador</th><th data-k="bloque">Bloque</th>
    <th data-k="p_af">P(vota a favor)</th><th data-k="accion">Acción esperada</th>
    <th data-k="n">Base</th>
  </tr></thead><tbody id="tb"></tbody></table>

  <div class="foot" id="foot"></div>
</div>
<script>
const DATA = /*DATA*/;
const $=s=>document.querySelector(s);
function ncdf(z){ // aprox normal CDF
  const t=1/(1+.2316419*Math.abs(z));
  const d=.3989423*Math.exp(-z*z/2);
  let p=d*t*(.3193815+t*(-.3565638+t*(1.781478+t*(-1.821256+t*1.330274))));
  return z>0?1-p:p;}
function logit(p){p=Math.min(Math.max(p,1e-6),1-1e-6);return Math.log(p/(1-p));}
function inv(x){return 1/(1+Math.exp(-x));}
function gamma(dv){return dv>=.4?.555:dv>=.3?.354:dv>=.2?.333:dv>=.1?.220:.094;}
let ICG=DATA.icg, ACT=0;

function pmod(l){ // p(afirmativo) con clima
  const logrel=Math.log(ICG/DATA.icg_neutro);
  return inv(logit(l.p_af)+gamma(l.desvio)*1*logrel);
}
function paprob(cam){ // P(afirmativos >= umbral), normal approx Poisson-binomial
  let m=0,v=0; cam.legisladores.forEach(l=>{const p=pmod(l);m+=p;v+=p*(1-p);});
  const z=(cam.umbral-0.5-m)/Math.sqrt(v||1);
  // nunca 0%/100%: hay riesgo sistemico que el modelo no capta (incertidumbre irreducible)
  const P=Math.min(Math.max(1-ncdf(z),0.01),0.99); return {p:P,m};
}
function accion(p,l){
  if(l && l.presencia!==undefined && l.presencia<0.15) return ["RARA VEZ VOTA","b-na"];
  return p>=.6?["A FAVOR","b-si"]:p<=.4?["EN CONTRA","b-no"]:["BISAGRA","b-bis"];}
function pct(x){return (100*x).toFixed(0)+"%";}

function render(){
  $("#asunto").textContent=DATA.asunto;
  $("#subtitulo").textContent=DATA.subtitulo;
  const f=new Date(DATA.fecha).toLocaleDateString("es-AR",{day:"numeric",month:"long",year:"numeric"});
  $("#meta").innerHTML=`<div class="chip"><span class="k">Evaluado al</span><b>${f}</b></div>
    <div class="chip"><span class="k">ICG del momento</span><b>${DATA.icg.toFixed(2)}</b></div>
    <div class="chip"><span class="k">Mes de mandato</span><b>${DATA.mandato_meses}</b></div>
    <div class="chip"><span class="k">Modelo</span><b>récord por legislador · condicionado por tipo de proyecto</b></div>`;
  $("#icg").value=ICG; $("#icgv").textContent=ICG.toFixed(2);
  $("#icgtag").textContent=ICG>DATA.icg_neutro?"(clima a favor del gobierno)":ICG<DATA.icg_neutro?"(clima en contra)":"(neutro)";

  // cámaras
  $("#cams").innerHTML="";
  DATA.camaras.forEach((c,i)=>{
    const r=paprob(c); const rol=c.es_origen?"Cámara de origen":"Cámara revisora";
    const nombre=c.camara==="diputados"?"Diputados":"Senado";
    const verd=r.p>=.6?["Avanza","var(--si)"]:r.p<=.4?["Se frena","var(--no)"]:["En la cuerda floja","var(--bis)"];
    const fill=Math.min(100,100*r.m/c.n), thr=100*c.umbral/c.n;
    const el=document.createElement("div"); el.className="cam";
    el.innerHTML=`<h2>${nombre}</h2><div class="r">${rol} · ${c.n} bancas · mayoría ${c.umbral}</div>
      <div class="big">${pct(r.p)} <small>de aprobar</small></div>
      <div class="verdict" style="color:${verd[1]}">${verd[0]}</div>
      <div class="bar"><i style="width:${fill}%"></i><div class="thr" style="left:${thr}%"></div></div>
      <div class="barlab"><span>${r.m.toFixed(0)} afirmativos esperados</span><span>umbral ${c.umbral}</span></div>`;
    $("#cams").appendChild(el);
  });

  // tabs
  $("#tabs").innerHTML="";
  DATA.camaras.forEach((c,i)=>{
    const t=document.createElement("div"); t.className="tab"+(i===ACT?" on":"");
    t.textContent=c.camara==="diputados"?"Diputados":"Senado";
    t.onclick=()=>{ACT=i;fillBloques();render();}; $("#tabs").appendChild(t);
  });
  tabla();
}
function fillBloques(){
  const sel=$("#fbloque"), cur=sel.value;
  const bs=[...new Set(DATA.camaras[ACT].legisladores.map(l=>l.bloque))].sort();
  sel.innerHTML='<option value="">Todos los bloques</option>'+bs.map(b=>`<option>${b}</option>`).join("");
  sel.value=cur;
}
let SORT="p_af",DIR=-1;
function tabla(){
  const c=DATA.camaras[ACT]; const q=$("#q").value.toLowerCase(), fb=$("#fbloque").value;
  let rows=c.legisladores.map(l=>{const p=pmod(l);return {...l,p,acc:accion(p,l)};})
    .filter(l=>(!q||l.nombre.toLowerCase().includes(q))&&(!fb||l.bloque===fb));
  rows.sort((a,b)=>{let x=SORT==="accion"?a.p:a[SORT],y=SORT==="accion"?b.p:b[SORT];
    if(typeof x==="string")return DIR*x.localeCompare(y); return DIR*(x-y);});
  $("#cnt").textContent=rows.length+" legisladores";
  $("#tb").innerHTML=rows.map(l=>{
    const col=l.acc[1]==="b-si"?"var(--si)":l.acc[1]==="b-no"?"var(--no)":"var(--bis)";
    const base=l.fuente==="individual"?`<span title="su propio récord">${l.n} votos</span>`
      :`<span style="color:var(--bis)" title="novato: usa el promedio de su bloque">bloque</span>`;
    return `<tr><td>${l.nombre}</td><td style="color:var(--mut)">${l.bloque}</td>
      <td class="p"><span class="pb"><i style="width:${100*l.p}%;background:${col}"></i></span>${pct(l.p)}</td>
      <td><span class="badge ${l.acc[1]}">${l.acc[0]}</span></td>
      <td style="color:var(--mut);font-size:12px">${base}</td></tr>`;}).join("");
}
$("#icg").addEventListener("input",e=>{ICG=+e.target.value;render();});
$("#q").addEventListener("input",tabla);
$("#fbloque").addEventListener("change",tabla);
document.querySelectorAll("th[data-k]").forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; if(SORT===k)DIR*=-1;else{SORT=k;DIR=k==="nombre"||k==="bloque"?1:-1;} tabla();});
$("#foot").innerHTML="Nowcast Legislativo Argentino · proyección por puertas (origen + revisora). "+
  "La probabilidad por legislador sale de su <b>récord en proyectos del mismo tipo</b> (según quién "+
  "los impulsa: Ejecutivo, oficialismo, aliados u oposición), con el promedio de su bloque como "+
  "respaldo; el ICG modula legislador por legislador (los bisagra se mueven más). Nunca se reporta "+
  "0% ni 100%: ninguna votación es segura. Cifras del modelo sobre datos al "+DATA.fecha+" — simulación, no asesoramiento.";
fillBloques(); render();
</script></body></html>"""


if __name__ == "__main__":
    main()
