# -*- coding: utf-8 -*-
"""El nowcast POR PUERTAS de un proyecto, como HTML autocontenido.

Sucesor de `nowcast_bicameral_html.py`, que dibujaba una sola cámara-por-lado sin la
cadena. Acá el número es el de `modelo/ensemble/nowcast_puertas` y la cadena está a
la vista, con lo que se OBSERVA y lo que se CALCULA distinguido:

    [A observada] · P(B | carácter de origen) · [C observada] · P(D | carácter revisora)

Lo que se conserva del anterior, porque es lo que sirve: el slider de clima que
recalcula en vivo y la tabla por legislador. Lo que se agrega: el estado real de A y
de C (con carácter / sin dictamen / sin dato), y que el número diga en pantalla que
es CONDICIONAL — no incluye la chance de que el proyecto sea tratado.

El slider recalcula con la MISMA P por legislador que usó la simulación
(`p_afirmativo`, pedida al agregador), no con un modelo paralelo.

    python casos/nowcast_puertas_html.py diputados --origen EJECUTIVO
    python casos/nowcast_puertas_html.py diputados --proyecto HCDN283397 --fecha 2026-06-01

Sin CDN y sin fetch: se abre con doble clic, sin servidor y sin internet.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

RAIZ = next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "modelo" / "ensemble" / "src"))

from nowcast_puertas import nowcast  # noqa: E402
from rutas import PROYECTO_ICG_MENSUAL  # noqa: E402

logger = logging.getLogger("nowcast_puertas_html")

ICG_NEUTRO = 1.90   # nivel de referencia (break-even reciente), igual que en el anterior


def icg_del_mes(fecha) -> tuple[float, str]:
    """El ICG del mes de la fecha; si no está, el más nuevo que haya."""
    if not Path(PROYECTO_ICG_MENSUAL).exists():
        logger.warning("no encontré %s: el clima queda en el neutro", PROYECTO_ICG_MENSUAL)
        return ICG_NEUTRO, "sin dato"
    d = pd.read_csv(PROYECTO_ICG_MENSUAL, header=None,
                    names=["fecha", "anio", "mes", "icg", "fuente"])
    # formato explícito: sin él pandas infiere fila por fila y avisa, y una inferencia
    # silenciosa sobre fechas es justo lo que no queremos en un archivo de serie mensual
    d["fecha"] = pd.to_datetime(d["fecha"], format="%Y-%m-%d", errors="coerce")
    d = d.dropna(subset=["fecha"]).sort_values("fecha")
    F = pd.to_datetime(fecha)
    prev = d[d["fecha"] <= F]
    fila = (prev.iloc[-1] if len(prev) else d.iloc[-1])
    return float(fila["icg"]), str(fila["fecha"].date())


def construir(camara_origen: str, fecha=None, proyecto=None, origen=None,
              tema=None, asunto=None, n_sims=2000) -> dict:
    nc = nowcast(camara_origen, fecha, proyecto_id=proyecto, origen=origen,
                 tema=tema, n_sims=n_sims)
    icg, icg_fecha = icg_del_mes(nc["fecha"])
    nc["icg"] = icg
    nc["icg_neutro"] = ICG_NEUTRO
    nc["icg_fecha"] = icg_fecha
    nc["asunto"] = asunto or (f"Proyecto {proyecto}" if proyecto
                              else "Proyecto hipotético")
    return nc


def escribir(nc: dict, salida: Path) -> Path:
    html = PLANTILLA.replace("/*DATA*/", json.dumps(nc, ensure_ascii=False))
    salida.write_text(html, encoding="utf-8")
    return salida


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("camara_origen", help="diputados | senado")
    ap.add_argument("--fecha", default=None, help="por defecto, hoy")
    ap.add_argument("--proyecto", default=None, help="proyecto_id; sin esto es hipotético")
    ap.add_argument("--origen", default=None,
                    help="EJECUTIVO | OFICIALISMO | ALIADOS | OPOSICION")
    ap.add_argument("--tema", default=None)
    ap.add_argument("--asunto", default=None, help="título que se muestra arriba")
    ap.add_argument("--n-sims", type=int, default=2000)
    ap.add_argument("--salida", default=str(RAIZ / "Nowcast-Puertas.html"))
    a = ap.parse_args(argv[1:])
    nc = construir(a.camara_origen, a.fecha, a.proyecto, a.origen, a.tema,
                   a.asunto, a.n_sims)
    out = escribir(nc, Path(a.salida))
    print(f"\n  escrito: {out}")
    print(f"  P(aprobación) {nc['p_aprobacion']*100:.1f}%  (condicional)")
    for cual in ("origen", "revisora"):
        c = nc["camaras"][cual]
        k = c["conteo"]
        print(f"  {cual:9s} {c['camara']:10s} {c['bancas']:3d} bancas | "
              f"acompañan {k['acompana']} · no {k['no_acompana']} · incógnita {k['incognita']}")


PLANTILLA = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nowcast por puertas — proyección bicameral</title>
<style>
  :root{--bg:#0f1420;--card:#1a2233;--ink:#e8edf7;--mut:#8a97b0;--line:#2a3550;
        --si:#37c98a;--no:#f0616d;--bis:#f2b53c;--acc:#5b8cff;--obs:#9b8cff;}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:26px;margin:0 0 2px} .sub{color:var(--mut);margin:0 0 4px}
  .meta{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 20px}
  .chip{background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:8px 12px;font-size:13px} .chip .k{color:var(--mut);margin-right:6px}
  /* la cadena de puertas */
  .cadena{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 8px}
  @media(max-width:860px){.cadena{grid-template-columns:1fr 1fr}}
  .paso{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;position:relative}
  .paso .let{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--mut)}
  .paso .nom{font-size:13px;margin:2px 0 8px;min-height:34px}
  .paso .val{font-size:26px;font-weight:700;line-height:1}
  .paso .nat{font-size:10px;font-weight:800;letter-spacing:.06em;padding:2px 7px;
             border-radius:20px;position:absolute;top:10px;right:10px}
  .n-obs{background:rgba(155,140,255,.18);color:var(--obs)}
  .n-cal{background:rgba(91,140,255,.16);color:var(--acc)}
  .paso .est{font-size:12px;color:var(--mut);margin-top:6px}
  .total{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);
         border-radius:12px;padding:16px 18px;margin:10px 0 22px}
  .total .big{font-size:40px;font-weight:800;line-height:1}
  .total .cond{color:var(--bis);font-size:13px;margin-top:6px;max-width:820px}
  .icgbox{background:var(--card);border:1px solid var(--line);border-radius:12px;
          padding:14px 16px;margin-bottom:22px}
  .icgbox .row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  input[type=range]{flex:1;min-width:200px;accent-color:var(--acc)}
  .cams{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  @media(max-width:760px){.cams{grid-template-columns:1fr}}
  .cam{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
  .cam h2{margin:0 0 2px;font-size:19px} .cam .r{color:var(--mut);font-size:13px;margin-bottom:12px}
  .big{font-size:42px;font-weight:700;line-height:1} .big small{font-size:15px;color:var(--mut);font-weight:400}
  .verdict{font-size:13px;font-weight:600;margin-top:4px}
  .bar{height:14px;background:#0d1220;border-radius:8px;position:relative;margin:14px 0 4px;overflow:hidden}
  .bar>i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#2f6df6,#37c98a);border-radius:8px}
  .thr{position:absolute;top:-3px;bottom:-3px;width:2px;background:#fff}
  .barlab{display:flex;justify-content:space-between;font-size:12px;color:var(--mut)}
  .mini{display:flex;gap:8px;margin-top:10px;font-size:12px;flex-wrap:wrap}
  .mini span{background:#0d1220;border-radius:8px;padding:4px 9px}
  .tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:22px 0 10px}
  select,input[type=search]{background:var(--card);border:1px solid var(--line);color:var(--ink);
    border-radius:8px;padding:7px 10px;font-size:13px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}
  th{color:var(--mut);cursor:pointer;user-select:none;font-weight:600}
  .pb{height:9px;border-radius:5px;background:#0d1220;position:relative;overflow:hidden;
      display:inline-block;width:110px;vertical-align:middle;margin-right:8px}
  .pb>i{position:absolute;left:0;top:0;bottom:0}
  .badge{font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px}
  .b-si{background:rgba(55,201,138,.16);color:var(--si)}
  .b-no{background:rgba(240,97,109,.16);color:var(--no)}
  .b-bis{background:rgba(242,181,60,.16);color:var(--bis)}
  .b-na{background:rgba(138,151,176,.18);color:var(--mut)}
  .tabbar{display:flex;gap:8px;margin:22px 0 0}
  .tab{background:var(--card);border:1px solid var(--line);border-radius:8px 8px 0 0;
       padding:8px 16px;cursor:pointer;font-size:13px;color:var(--mut)}
  .tab.on{color:var(--ink);border-bottom-color:var(--card);font-weight:600}
  .foot{color:var(--mut);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}
  .neg{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:18px}
  .neg h3{margin:0 0 4px;font-size:15px} .neg .why{color:var(--mut);font-size:12px;margin-bottom:10px}
  .neg ol{margin:0;padding-left:20px} .neg li{margin:3px 0}
</style></head>
<body><div class="wrap">
  <h1 id="asunto"></h1><p class="sub" id="subtitulo"></p>
  <div class="meta" id="meta"></div>

  <div class="cadena" id="cadena"></div>
  <div class="total" id="total"></div>

  <div class="icgbox"><div class="row">
    <div><div style="font-size:13px;color:var(--mut)">Clima político (ICG)</div>
      <div style="font-size:22px;font-weight:700"><span id="icgv"></span>
      <small style="font-size:12px;color:var(--mut)" id="icgtag"></small></div></div>
    <input type="range" id="icg" min="1.0" max="3.0" step="0.01">
    <div style="font-size:12px;color:var(--mut);max-width:250px">
      Movés el índice y las dos votaciones se recalculan. El clima pesa sobre los de
      desvío alto y casi nada sobre el núcleo duro.</div>
  </div></div>

  <div class="cams" id="cams"></div>
  <div class="neg" id="neg"></div>

  <div class="tabbar" id="tabs"></div>
  <div class="tools">
    <input type="search" id="q" placeholder="Buscar legislador…">
    <select id="fbloque"><option value="">Todos los bloques</option></select>
    <select id="fpost"><option value="">Toda postura</option>
      <option value="incognita">Sólo incógnitas</option>
      <option value="acompana">Sólo los que acompañan</option>
      <option value="no_acompana">Sólo los que no acompañan</option>
      <option value="no_vota">Sólo los que no votan</option></select>
    <span style="color:var(--mut);font-size:12px" id="cnt"></span>
  </div>
  <table><thead><tr>
    <th data-k="legislador">Legislador</th><th data-k="bloque">Bloque</th>
    <th data-k="postura">Postura</th>
    <th data-k="p">P(vota a favor)</th>
    <th data-k="p_si_vota">Si vota</th>
    <th data-k="presencia">Asiste</th>
    <th data-k="direccion_de">De dónde sale</th>
  </tr></thead><tbody id="tb"></tbody></table>
  <div class="foot" id="foot"></div>
</div>
<script>
const DATA = /*DATA*/;
const $=s=>document.querySelector(s);
function ncdf(z){const t=1/(1+.2316419*Math.abs(z));const d=.3989423*Math.exp(-z*z/2);
  let p=d*t*(.3193815+t*(-.3565638+t*(1.781478+t*(-1.821256+t*1.330274))));return z>0?1-p:p;}
function logit(p){p=Math.min(Math.max(p,1e-6),1-1e-6);return Math.log(p/(1-p));}
function inv(x){return 1/(1+Math.exp(-x));}
// gamma por banda de desvio: medido en el analisis del ICG (el nucleo duro no responde)
function gamma(dv){return dv>=.4?.555:dv>=.3?.354:dv>=.2?.333:dv>=.1?.220:.094;}
let ICG=DATA.icg, ACT=0, SORT={k:"desvio",dir:-1};
function pmod(l){const lr=Math.log(ICG/DATA.icg_neutro);
  return inv(logit(l.p_afirmativo)+gamma(l.desvio)*lr);}
// Poisson-binomial por aproximacion normal, con el MISMO techo/piso que el modelo:
// nunca 0%/100%, hay riesgo sistemico que la independencia entre legisladores no capta.
// El umbral es el que USO LA SIMULACION (la mitad de los que efectivamente votan),
// no n/2+1. Antes aca decia 129 mientras Python usaba 125,5: coincidian de casualidad
// porque los dos estaban saturados, y en una votacion ajustada se habrian contradicho.
// El clima cambia la DIRECCION del voto, no quien asiste, asi que el umbral no se mueve.
function paprob(cam){let m=0,v=0;cam.legisladores.forEach(l=>{const p=pmod(l);m+=p;v+=p*(1-p);});
  const u=(cam.umbral_simulado!==undefined)?cam.umbral_simulado:cam.umbral_mayoria_simple;
  const z=(u-0.5-m)/Math.sqrt(v||1);
  return {p:Math.min(Math.max(1-ncdf(z),0.01),0.99),m:m,u:u};}
function pct(x){return (100*x).toFixed(0)+"%";}
function badge(post){
  return post==="no_vota"?["NO VOTA","b-na"]
    :post==="acompana"?["ACOMPAÑA","b-si"]
    :post==="no_acompana"?["NO ACOMPAÑA","b-no"]:["INCÓGNITA","b-bis"];}
function camaras(){return [DATA.camaras.origen, DATA.camaras.revisora];}
function nom(c){return c==="diputados"?"Diputados":"Senado";}

function render(){
  $("#asunto").textContent=DATA.asunto;
  $("#subtitulo").textContent="Origen: "+nom(DATA.camara_origen)+" · revisora: "+nom(DATA.camara_revisora)
    +(DATA.origen?" · empuja: "+DATA.origen:"");
  const f=new Date(DATA.fecha+"T12:00:00").toLocaleDateString("es-AR",{day:"numeric",month:"long",year:"numeric"});
  $("#meta").innerHTML=`<div class="chip"><span class="k">Configuración al</span><b>${f}</b></div>
    <div class="chip"><span class="k">ICG</span><b>${DATA.icg.toFixed(2)}</b> <span class="k">(${DATA.icg_fecha})</span></div>
    <div class="chip"><span class="k">Mayoría</span><b>${DATA.tipo_mayoria}</b></div>
    <div class="chip"><span class="k">Proyecto</span><b>${DATA.proyecto_id}</b></div>`;
  // la cadena
  const rs=camaras().map(paprob);
  const pv={B:rs[0].p, D:rs[1].p};
  $("#cadena").innerHTML=DATA.pasos.map(p=>{
    const obs=p.naturaleza==="observado";
    const nat=obs?'<span class="nat n-obs">SE OBSERVA</span>':'<span class="nat n-cal">SE CALCULA</span>';
    let val,est;
    if(obs){
      const et={con_caracter:"con dictamen leído",sin_dictamen:"sin dictamen",sin_dato:"sin dato"}[p.estado]||p.estado;
      val=`<div class="val" style="font-size:19px;color:${p.estado==="con_caracter"?"var(--si)":"var(--mut)"}">${et}</div>`;
      est=p.estado==="con_caracter"
        ? `${p.n_firmantes} firmantes${p.hay_minoria?" · hay dictamen de minoría":""}${p.disidencia?" · con disidencias":""}${p.acumulado?" · acumulado":""}`
        : (p.motivo||"");
    }else{
      val=`<div class="val">${pct(pv[p.paso])}</div>`;
      est=p.condicionado_por_el_dictamen?"condicionado por el dictamen":"sin condicionar (no hay carácter)";
    }
    return `<div class="paso">${nat}<div class="let">PASO ${p.paso}</div>
      <div class="nom">${p.nombre}</div>${val}<div class="est">${est}</div></div>`;
  }).join("");
  const tot=pv.B*pv.D;
  // Si las dos votaciones estan pegadas al techo (0,99), el numero NO se mueve aunque
  // el clima cambie — y el slider parece roto. Pasa cuando el margen es holgado: con
  // 157 afirmativos contra un umbral de 129, ningun clima da vuelta la votacion. Se
  // dice en pantalla, porque un control mudo se lee como un control roto.
  const topeB=pv.B>=0.989, topeD=pv.D>=0.989, pisoB=pv.B<=0.011, pisoD=pv.D<=0.011;
  const enTope=(topeB||pisoB)&&(topeD||pisoD);
  const margenes=camaras().map((c,i)=>Math.round(rs[i].m-c.umbral_mayoria_simple));
  const nota=enTope
    ? `<div style="color:var(--mut);font-size:12px;margin-top:8px">El número está en el
       ${topeB?"techo":"piso"} de confianza y por eso no se mueve con el clima: los márgenes son
       de ${margenes[0]>=0?"+":""}${margenes[0]} y ${margenes[1]>=0?"+":""}${margenes[1]} votos sobre
       el umbral. Mirá los afirmativos esperados, que sí se mueven.</div>` : "";
  $("#total").innerHTML=`<div style="font-size:13px;color:var(--mut)">Probabilidad de aprobación</div>
    <div class="big">${pct(tot)}</div>
    <div class="cond">⚠ Condicional ${DATA.condicional_a}</div>${nota}`;
  $("#icg").value=ICG; $("#icgv").textContent=ICG.toFixed(2);
  $("#icgtag").textContent=ICG>DATA.icg_neutro?"(clima a favor del gobierno)":ICG<DATA.icg_neutro?"(clima en contra)":"(neutro)";
  // camaras
  $("#cams").innerHTML="";
  camaras().forEach((c,i)=>{
    const r=rs[i], rol=i===0?"Cámara de origen (paso B)":"Cámara revisora (paso D)";
    const verd=r.p>=.6?["Avanza","var(--si)"]:r.p<=.4?["Se frena","var(--no)"]:["En la cuerda floja","var(--bis)"];
    const fill=Math.min(100,100*r.m/c.bancas), thr=100*r.u/c.bancas;
    const k=c.conteo;
    const el=document.createElement("div"); el.className="cam";
    el.innerHTML=`<h2>${nom(c.camara)}</h2>
      <div class="r">${rol} · ${c.bancas} bancas · ${k.no_vota||0} no votan · padrón ${c.padron||"—"}</div>
      <div class="big">${pct(r.p)} <small>de aprobar</small></div>
      <div class="verdict" style="color:${verd[1]}">${verd[0]}</div>
      <div class="bar"><i style="width:${fill}%"></i><div class="thr" style="left:${thr}%"></div></div>
      <div class="barlab"><span>${r.m.toFixed(0)} afirmativos esperados</span><span>umbral ${r.u.toFixed(0)} (mitad de los que votan)</span></div>
      <div class="mini"><span style="color:var(--si)">acompañan ${k.acompana}</span>
        <span style="color:var(--no)">no acompañan ${k.no_acompana}</span>
        <span style="color:var(--bis)">incógnita ${k.incognita}</span></div>`;
    $("#cams").appendChild(el);
  });
  // a quien ir a buscar
  $("#neg").innerHTML=camaras().map(c=>{
    const why=c.hay_bisagras
      ? `Su voto no está decidido: la probabilidad de que acompañe cae entre 35% y 65%. Ordenados del más indeciso al menos.`
      : `Nadie en esta cámara queda en zona de duda; van igual los menos definidos. Son legisladores con posición tomada.`;
    return `<h3>${nom(c.camara)} — a quién ir a buscar</h3><div class="why">${why}</div>
      <ol>${c.a_negociar.slice(0,8).map(x=>`<li>${x.legislador} <span style="color:var(--mut)">— ${x.bloque} · <b style="color:var(--bis)">${pct(x.p_afirmativo)}</b> de acompañar · desvío ${x.desvio.toFixed(3)}</span></li>`).join("")}</ol>`;
  }).join('<div style="height:14px"></div>');
  // tabs
  $("#tabs").innerHTML="";
  camaras().forEach((c,i)=>{
    const t=document.createElement("div"); t.className="tab"+(i===ACT?" on":"");
    t.textContent=nom(c.camara); t.onclick=()=>{ACT=i;fillBloques();render();};
    $("#tabs").appendChild(t);});
  tabla();
}
function fillBloques(){
  const sel=$("#fbloque"), cur=sel.value;
  const bs=[...new Set(camaras()[ACT].legisladores.map(l=>l.bloque))].sort();
  sel.innerHTML='<option value="">Todos los bloques</option>'+bs.map(b=>`<option>${b}</option>`).join("");
  if(bs.includes(cur)) sel.value=cur;
}
function tabla(){
  const c=camaras()[ACT];
  const q=($("#q").value||"").toLowerCase(), fb=$("#fbloque").value, fp=$("#fpost").value;
  let rows=c.legisladores.map(l=>({...l,p:pmod(l)}));
  if(q) rows=rows.filter(l=>l.legislador.toLowerCase().includes(q));
  if(fb) rows=rows.filter(l=>l.bloque===fb);
  if(fp) rows=rows.filter(l=>l.postura===fp);
  rows.sort((a,b)=>{const k=SORT.k;let x=a[k],y=b[k];
    if(typeof x==="string") return SORT.dir*x.localeCompare(y);
    return SORT.dir*((x||0)-(y||0));});
  $("#cnt").textContent=`${rows.length} de ${c.legisladores.length}`;
  $("#tb").innerHTML=rows.map(l=>{
    const [txt,cls]=badge(l.postura);
    const col=l.p>=.6?"var(--si)":l.p<=.4?"var(--no)":"var(--bis)";
    return `<tr><td>${l.legislador}</td><td style="color:var(--mut)">${l.bloque}</td>
      <td><span class="badge ${cls}">${txt}</span></td>
      <td><span class="pb"><i style="width:${(100*l.p).toFixed(0)}%;background:${col}"></i></span>${pct(l.p)}</td>
      <td>${pct(l.p_si_vota)} <span style="color:var(--mut);font-size:11px">si vota</span></td>
      <td>${pct(l.presencia)}</td>
      <td style="color:var(--mut);font-size:11px">${l.direccion_de==="record_individual"?"su historial (n="+l.n_emitidos+")":"su bloque ("+pct(l.share_linaje)+")"}</td></tr>`;
  }).join("");
}
document.querySelectorAll("th[data-k]").forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; SORT.dir=(SORT.k===k)?-SORT.dir:-1; SORT.k=k; tabla();});
$("#icg").oninput=e=>{ICG=parseFloat(e.target.value);render();};
$("#q").oninput=tabla; $("#fbloque").onchange=tabla; $("#fpost").onchange=tabla;
$("#foot").innerHTML="Nowcast Legislativo Argentino · cadena de PUERTAS. A y C se OBSERVAN "
  +"(el dictamen y su carácter, leídos del PDF de la Orden del Día); B y D se CALCULAN "
  +"(el agregador sobre el roster nominal de cada cámara, con el desvío individual de "
  +"cada legislador). El número NO incluye la chance de que el proyecto sea tratado: eso "
  +"es agenda política y este modelo no la estima. Padrón point-in-time (oficial + histórico).";
fillBloques(); render();
</script></body></html>
"""


if __name__ == "__main__":
    main(sys.argv)
