"""comparar_vias_icg.py — SUPERSEDED / NEUTRALIZADO 2026-08-11.

⛔ Este comparador contrastaba el MECANISMO 1 (individual, medido) contra el
MECANISMO 2 (nivel declarado por el analista = capa 2 global). El 2026-08-11
Valle DECIDIÓ ELIMINAR la capa 2 (doble conteo del mismo clima), así que la
comparación ya no tiene sentido y `modulador_icg.aplicar_dos_capas` fue removido:
este script NO corre más (levantaría AttributeError). Se conserva sólo como
registro histórico; copia en Archivos_Borrar/BORRAR_comparar_vias_icg_capa2_2026-08-11.py.
El `__main__` está neutralizado. Ver ADR-0008 (rev 2026-08-11) y ESTADO 2026-08-11.

--- diseño original (histórico) --------------------------------------------
Reescrito de cero el 2026-08-04 con el diseño final acordado con Valle:

  MECANISMO 1 — VARIACION (medido, individual).
    El ICG del mes contra el promedio del propio gobierno, aplicado legislador
    por legislador segun cuan discolo sea. Es lo que se estimo: gamma sube
    0,22 -> 0,33 -> 0,35 -> 0,56 con el desvio, con dosis-respuesta.

  MECANISMO 2 — NIVEL (declarado, agregado).
    El ICG del mes contra la CURVA DEL CICLO: lo que un gobierno suele tener a
    esa altura del mandato. Un 2,0 en el mes 3 es malo; el mismo 2,0 en el mes
    30 es bueno. La intensidad la declara el analista.

Los dos son independientes: uno mide el desvio DENTRO del gobierno, el otro el
nivel del gobierno contra la historia.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

_HERE = Path(__file__).resolve(); RAIZ = _HERE.parents[3]
sys.path.insert(0, str(_HERE.parent))
import modulador_icg as M

SALIDA = RAIZ / "COMPARADOR-ICG.html"
UMBRAL = 129
HOY = pd.Timestamp("2026-08-04")

GRUPOS = [("Muy díscolos", 0.40, 9.9, 0.555), ("Díscolos", 0.30, 0.40, 0.354),
          ("Moderados", 0.20, 0.30, 0.333), ("Poco móviles", 0.10, 0.20, 0.220),
          ("Núcleo duro", 0.00, 0.10, 0.0)]

# icg = ICG del mes · mes = mes de mandato del gobierno · prom = promedio del gobierno
ESC = [
 dict(t="Reforma laboral del Ejecutivo", tema="Trabajo", lado="GOBIERNO", votos=124,
      icg=2.62, mes=31, prom=2.34, nota="gobierno arriba de su promedio y del ciclo"),
 dict(t="Presupuesto del Ejecutivo", tema="Economía", lado="GOBIERNO", votos=133,
      icg=2.34, mes=31, prom=2.34, nota="en su promedio, apenas sobre el ciclo"),
 dict(t="Emergencia en discapacidad", tema="Salud", lado="OPOSICION", votos=131,
      icg=1.10, mes=45, prom=1.55, nota="gobierno en caída al final del mandato"),
 dict(t="Privatización de empresa pública", tema="Economía", lado="GOBIERNO", votos=118,
      icg=1.45, mes=28, prom=1.61, nota="gobierno debilitado en el valle del ciclo"),
 dict(t="Ficha limpia", tema="Justicia", lado="OPOSICION", votos=129,
      icg=1.90, mes=20, prom=1.74, nota="empate técnico: el clima define"),
 dict(t="Actualización de haberes jubilatorios", tema="Previsional", lado="OPOSICION", votos=136,
      icg=1.19, mes=38, prom=1.55, nota="desgaste fuerte"),
 dict(t="Ley de lobby", tema="Institucional", lado="GOBIERNO", votos=126,
      icg=2.97, mes=24, prom=2.21, nota="pico de confianza a mitad de mandato"),
 dict(t="Financiamiento universitario", tema="Educación", lado="OPOSICION", votos=140,
      icg=1.51, mes=12, prom=2.21, nota="caída temprana: mal contra el ciclo"),
 dict(t="Reforma del Código Penal", tema="Seguridad", lado="GOBIERNO", votos=120,
      icg=3.32, mes=9, prom=2.47, nota="luna de miel larga, máximo de la serie"),
 dict(t="Moratoria previsional", tema="Previsional", lado="OPOSICION", votos=127,
      icg=1.07, mes=36, prom=1.55, nota="piso histórico"),
 # --- los dos siguientes existen para EXPONER la diferencia entre las variantes
 #     del nivel: caen en la luna de miel, que es donde ciclo y fijo discrepan ---
 dict(t="Paquete de reformas del PE recién asumido", tema="Institucional", lado="GOBIERNO", votos=128,
      icg=2.00, mes=4, prom=2.00, nota="ARRANQUE FLOJO: 2,00 cuando lo normal recién asumido es 2,51"),
 dict(t="Derogación de decretos (oposición)", tema="Institucional", lado="OPOSICION", votos=130,
      icg=2.51, mes=4, prom=2.51, nota="LUNA DE MIEL TÍPICA: 2,51 es exactamente lo normal al mes 4"),
]


def camara():
    pad = pd.read_csv(RAIZ/"datos/padron/data/padron_diputados.csv", encoding="utf-8-sig")
    for c in ("desde","hasta"): pad[c] = pd.to_datetime(pad[c], errors="coerce")
    v = pad[(pad.desde<=HOY)&(pad.hasta>=HOY)].copy()
    d = pd.read_csv(RAIZ/"modelo/voto_individual/outputs/disciplina_individual.csv")
    d = d[d.n_votos>=50][["legislador_id","tasa_desvio_disputadas"]]
    v = v.merge(d, on="legislador_id", how="left")
    v["sin_historial"] = v.tasa_desvio_disputadas.isna()
    v["desvio"] = v.tasa_desvio_disputadas.fillna(0.0)
    return v


def _calibrar(p0, objetivo):
    lo, hi = -6.0, 6.0
    for _ in range(60):
        c = (lo+hi)/2; o = (p0/(1-p0))*np.exp(c)
        if (o/(1+o)).sum() < objetivo: lo = c
        else: hi = c
    o = (p0/(1-p0))*np.exp((lo+hi)/2)
    return np.clip(o/(1+o), 0.01, 0.99)


def base_escenario(v, lado, votos):
    ofi = v.bloque_linaje.isin({"LA LIBERTAD AVANZA"}); ali = v.bloque_linaje.isin({"PRO"})
    p = np.where(ofi, 0.97, np.where(ali, 0.85, 0.30)) if lado=="GOBIERNO" \
        else np.where(ofi, 0.12, np.where(ali, 0.28, 0.78))
    p = np.clip(p + (0.5-p)*np.clip(v.desvio.values*1.2, 0, 0.75), 0.02, 0.98)
    return _calibrar(p, votos)


def correr():
    v = camara(); out = []
    for e in ESC:
        s = 1.0 if e["lado"]=="GOBIERNO" else -1.0
        base = pd.DataFrame({"p_acompana": base_escenario(v, e["lado"], e["votos"]),
                             "desvio": v.desvio.values})
        log_rel = float(np.log(np.clip(e["icg"],1,4)/e["prom"]))
        r = M.aplicar_dos_capas(base, s, log_rel, e["icg"], e["mes"], UMBRAL, "moderado", "ciclo")
        rf = M.aplicar_dos_capas(base, s, log_rel, e["icg"], e["mes"], UMBRAL, "moderado", "fijo")
        out.append(dict(**e, log_rel=log_rel, log_ciclo=r["log_ciclo"], log_fijo=r["log_fijo"],
                        neutro=M.neutro_ciclo(e["mes"]), p0=r["p_base"],
                        p1=r["p_capa1"], p2=r["p_final"], p2f=rf["p_final"],
                        v0=r["votos_base"], v1=r["votos_capa1"], movidos=r["movidos"]))
    return pd.DataFrame(out), v


CSS = """*{box-sizing:border-box}
body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;color:#0b0b0b;max-width:1120px;
margin:0 auto;padding:40px 28px 80px;line-height:1.65;background:#fff;font-size:15px}
h1{font-size:26px;font-weight:500;margin:0 0 6px;letter-spacing:-.2px}
h2{font-size:19px;font-weight:500;margin:44px 0 6px}
h3{font-size:15px;font-weight:500;margin:0 0 8px}
.sub{color:#5f5e5a;margin:0 0 6px}
.m{color:#5f5e5a;font-size:12.5px}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px}
th{text-align:left;font-weight:500;font-size:12px;color:#5f5e5a;border-bottom:1px solid #d3d1c7;
padding:9px 10px;vertical-align:bottom}
td{padding:11px 10px;border-bottom:1px solid #e1e0d9;vertical-align:top}
td.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
tr:hover td{background:#fbfbf9}
.card{background:#fcfcfb;border:1px solid #e1e0d9;border-radius:12px;padding:18px 22px;margin:12px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid5{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0}
.g{border:1px solid #e1e0d9;border-radius:10px;padding:12px 14px;background:#fcfcfb}
.g .big{font-size:26px;font-weight:500;line-height:1.2}
.g .lbl{font-size:12px;color:#5f5e5a;margin-bottom:2px}
.warn{background:#FAEEDA;border-left:3px solid #BA7517;padding:13px 17px;margin:18px 0;font-size:13.5px}
.ok{background:#EAF3DE;border-left:3px solid #639922;padding:13px 17px;margin:18px 0;font-size:13.5px}
.up{color:#3B6D11;font-weight:500}.dn{color:#A32D2D;font-weight:500}.eq{color:#898781}
code{background:#F1EFE8;padding:1px 5px;border-radius:3px;font-size:12.5px}
.bar{height:7px;background:#e1e0d9;border-radius:4px;overflow:hidden;margin-top:5px;width:110px;display:inline-block;vertical-align:middle}
.bar>i{display:block;height:100%;background:#2a78d6}
@media(max-width:820px){.grid2,.grid5{grid-template-columns:1fr}}"""


def html(df, v):
    def P(x): return f"{100*x:.1f}%"
    def D(a, b):
        d = 100*(a-b); c = "up" if d > 0.4 else ("dn" if d < -0.4 else "eq")
        return f'<span class="{c}">{d:+.1f}</span>'

    gs = []
    for nom, lo, hi, g in GRUPOS:
        sub = v[(v.desvio >= lo) & (v.desvio < hi)]
        cambio = 0 if g == 0 else 100*(1/(1+np.exp(-(np.log(.54/.46)+g*1.094))) -
                                       1/(1+np.exp(-(np.log(.54/.46)+g*(-0.628)))))
        gs.append(f'<div class="g"><div class="lbl">{nom}</div><div class="big">{len(sub)}</div>'
                  f'<div class="m">desvío {int(lo*100)}–{"100" if hi>1 else int(hi*100)}%<br>'
                  f'{"no se mueven" if g==0 else f"mueven {cambio:+.0f} pts"}</div></div>')

    ej = []
    for nom, lo, hi, g in GRUPOS[:4]:
        sub = v[(v.desvio >= lo) & (v.desvio < hi)].nlargest(3, "desvio")
        ej.append(f'<tr><td><strong>{nom}</strong><br><span class="m">γ = {g}</span></td>'
                  f'<td>{"<br>".join(f"{r.legislador[:32]} <span class=m>· {r.bloque_linaje[:20]} · desvío {r.desvio:.0%}</span>" for r in sub.itertuples())}</td></tr>')

    fs = []
    for r in df.itertuples():
        fs.append(f"""<tr>
<td><strong>{r.t}</strong><br><span class="m">{r.tema} · impulsa {'el gobierno' if r.lado=='GOBIERNO' else 'la oposición'}</span></td>
<td><span class="m">mes {r.mes} de mandato · ICG {r.icg:.2f}<br>
promedio del gobierno {r.prom:.2f} · normal a esa altura {r.neutro:.2f}<br>{r.nota}</span></td>
<td class="n">{P(r.p0)}<br><span class="m">{r.v0:.0f} votos</span></td>
<td class="n">{P(r.p1)} {D(r.p1,r.p0)}<br><span class="m">{r.movidos} movidos · {r.v1:.0f} votos</span></td>
<td class="n">{P(r.p2)} {D(r.p2,r.p1)}<br><span class="m">{r.log_ciclo:+.2f}</span></td>
<td class="n">{P(r.p2f)} {D(r.p2f,r.p1)}<br><span class="m">{r.log_fijo:+.2f}</span></td></tr>""")

    curva = pd.read_csv(RAIZ/"variables/proyecto/data/curva_ciclo_presidencial.csv")
    cs = []
    for m in (3, 6, 12, 18, 24, 30, 36, 41):
        f = curva[curva.mes_mandato == m]
        if f.empty: continue
        val = float(f.neutro_ciclo.iloc[0])
        cs.append(f'<tr><td>mes {m}</td><td class="n">{val:.2f}</td>'
                  f'<td><span class="bar"><i style="width:{100*(val-1.7)/0.95:.0f}%"></i></span></td></tr>')

    sin_hist = int(v.sin_historial.sum())
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>El ICG en el nowcast — comparador para el equipo</title><style>{CSS}</style></head><body>

<h1>Cómo entra el clima político en el nowcast</h1>
<p class="sub">Dos mecanismos, sobre la cámara real de hoy ({len(v)} bancas) y el ICG de Di Tella (296 meses, 2001-2026).<br>
Generado el 4 de agosto de 2026 · para decidir en equipo.</p>

<h2>La idea en una línea</h2>
<div class="card"><p style="margin:0">El ICG no es un dato del proyecto de ley: es el estado del sistema en el que ese proyecto se juega.
Por eso no entra como una variable más del modelo — entra <strong>modulando</strong> el resultado, y con signo
contrario según quién impulsa el proyecto: un gobierno con buen clima empuja lo suyo y frena lo de la oposición.</p></div>

<h2>Mecanismo 1 — La variación, dentro de cada gobierno <span class="m">(medido)</span></h2>
<p class="sub">El ICG del mes contra el promedio de ese mismo gobierno. Se aplica <strong>legislador por legislador</strong>.
La cámara se parte sola en cinco grupos según cuánto se despega cada uno de su bloque en las votaciones peleadas.</p>
<div class="grid5">{''.join(gs)}</div>

<div class="ok"><strong>Lo que da confianza en este mecanismo.</strong> Nadie le explicó al modelo nada de política argentina:
solo miró votos. Y ordenó la cámara poniendo a los <strong>bloques provinciales y federales</strong> —los negociadores de siempre—
como los más sensibles al clima, y a La Libertad Avanza, el kirchnerismo y el PRO como núcleo duro que no se mueve.</div>

<table><thead><tr><th style="width:22%">Grupo</th><th>Quiénes son, en la cámara de hoy</th></tr></thead>
<tbody>{''.join(ej)}</tbody></table>

<h2>Mecanismo 2 — El nivel, contra el ciclo presidencial <span class="m">(declarado)</span></h2>
<p class="sub">Un ICG de 2,0 no significa lo mismo al principio que al final de un mandato. Alineando las seis presidencias
por mes de gobierno sale la curva de lo <em>normal</em> a cada altura: un 2,0 en el mes 3 es malo, el mismo 2,0 en el mes 30 es bueno.</p>
<div class="grid2"><div>
<table><thead><tr><th>Altura del mandato</th><th class="n">ICG normal</th><th></th></tr></thead><tbody>{''.join(cs)}</tbody></table>
</div><div class="card"><h3>Por qué es "declarado" y no medido</h3>
<p class="m" style="margin:0">Probamos estimar el efecto del nivel absoluto y no se puede separar de "qué gobierno era":
con seis presidencias, un ICG alto y una presidencia particular son la misma columna.<br><br>
Por eso la intensidad la elige el analista y el resultado se muestra como <strong>banda</strong>, nunca como predicción.
La curva está cortada en el mes 41: lo que sube después es expectativa de recambio, no del gobierno.</p></div></div>

<h2>Dos formas de medir el nivel — hay que elegir una</h2>
<div class="grid2">
<div class="card"><h3>A · Contra la curva del ciclo</h3>
<p class="m" style="margin:0">El neutro cambia según el mes de mandato: 2,55 recién asumido, 1,82 a mitad de camino.
Premia estar <strong>mejor de lo esperable a esa altura</strong>.<br><br>
Un gobierno recién asumido con ICG 2,55 no cobra nada: es lo normal. Uno con 2,00 en el mes 3 <strong>cobra castigo</strong>,
porque arrancó flojo.<br><br>
<em>Supone que los legisladores descuentan que todo gobierno arranca alto.</em></p></div>
<div class="card"><h3>B · Contra 1,90 fijo</h3>
<p class="m" style="margin:0">Un solo umbral para toda la historia. Arriba de 1,90 suma, abajo resta, y escala con la distancia.<br><br>
Un gobierno recién asumido con ICG 2,55 <strong>cobra premio grande</strong> (+0,29) sólo por estar en su luna de miel.
Uno maduro con 1,82 cobra un castigo leve aunque esté en su normal.<br><br>
<em>Supone que la luna de miel da poder real sobre el Congreso.</em></p></div>
</div>
<table><thead><tr><th>Situación</th><th class="n">ICG</th><th class="n">normal a esa altura</th>
<th class="n">A · vs ciclo</th><th class="n">B · vs 1,90</th></tr></thead><tbody>
<tr><td>Recién asumido, ICG típico</td><td class="n">2,55</td><td class="n">2,55</td><td class="n">0,00</td><td class="n"><span class="up">+0,29</span></td></tr>
<tr><td>Recién asumido pero flojo</td><td class="n">2,00</td><td class="n">2,55</td><td class="n"><span class="dn">−0,24</span></td><td class="n"><span class="up">+0,05</span></td></tr>
<tr><td>Maduro, ICG típico</td><td class="n">1,82</td><td class="n">1,82</td><td class="n">0,00</td><td class="n"><span class="dn">−0,04</span></td></tr>
<tr><td>Maduro y fuerte</td><td class="n">2,30</td><td class="n">1,82</td><td class="n"><span class="up">+0,23</span></td><td class="n"><span class="up">+0,19</span></td></tr>
<tr><td>Final de mandato, débil</td><td class="n">1,50</td><td class="n">1,90</td><td class="n"><span class="dn">−0,24</span></td><td class="n"><span class="dn">−0,24</span></td></tr>
</tbody></table>
<p class="m">Donde más se separan es al arranque de un gobierno. En un mandato maduro las dos dan casi lo mismo.</p>

<h2>Los doce escenarios</h2>
<div class="warn"><strong>Cómo leer la tabla.</strong> Los proyectos son hipotéticos y la línea de base de cada legislador es estilizada.
Los porcentajes absolutos <em>no</em> son predicciones: lo que hay que mirar es <strong>cuánto mueve cada mecanismo sobre el mismo caso</strong>.</div>
<table><thead><tr><th style="width:23%">Proyecto</th><th style="width:27%">Situación política</th>
<th class="n">Sin clima</th><th class="n">+ variación<br><span class="m">medido</span></th>
<th class="n">+ nivel A<br><span class="m">vs curva del ciclo</span></th>
<th class="n">+ nivel B<br><span class="m">vs 1,90 fijo</span></th></tr></thead>
<tbody>{''.join(fs)}</tbody></table>

<h2>Lo que hay que decidir</h2>
<div class="card">
<p style="margin-top:0"><strong>1. Los {sin_hist} sin historial.</strong> De los 257 diputados, {sin_hist} asumieron en diciembre de 2025
y todavía no votaron lo suficiente para saber si son díscolos. Hoy se los trata como núcleo duro —o sea, se asume que el clima
no los toca—, y eso es un supuesto, no una medición. La alternativa es darles el desvío promedio de su bloque hasta que se midan solos.</p>
<p><strong>2. ¿Se le da algo al núcleo duro?</strong> Estimado sobre los disciplinados solos, γ da −0,03 con 50% de probabilidad
de ser positivo: una moneda al aire. Hoy están en cero. Con γ = 0,05 el swing de la cámara pasa de <strong>6,6 a 10,8 votos</strong>;
con 0,10, a 15,0. Es una perilla, no un default escondido.</p>
<p><strong>3. ¿Qué intensidad tiene el mecanismo 2?</strong> Hoy "moderado" = 0,35. Como referencia, el efecto del
nivel estimado controlando por bancas dio 0,49 — con las salvedades de arriba.</p>
<p style="margin-bottom:0"><strong>4. ¿Ciclo o break-even fijo?</strong> No es una decisión técnica: es una lectura política.
¿La luna de miel le da al gobierno poder real sobre el Congreso, o los legisladores ya saben que todo gobierno arranca alto
y no se dejan impresionar? Los datos no lo dicen — hay que decidirlo.</p>
</div>

<h2>Lo que quedó sin resolver</h2>
<div class="card"><p style="margin-top:0"><strong>La volatilidad no aparece.</strong> La hipótesis era que con el ICG planchado no hay
tracción política y con el ICG moviéndose la sociedad está permeable. Se midió: +0,045 con intervalo [−0,12; +0,09]. No se distingue de cero.
El razonamiento sigue en pie; los datos todavía no lo respaldan.</p>
<p style="margin-bottom:0"><strong>Presidencias de dos períodos.</strong> La curva del ciclo trata a todas las presidencias como iguales,
pero un gobierno que se sabe saliente no tiene el mismo final que uno que puede continuar. Cristina I termina muy por encima de la curva
justamente porque venía una reelección. Anotado en el plan de trabajo.</p></div>

<p class="m" style="margin-top:36px;border-top:1px solid #e1e0d9;padding-top:14px">
Generado por <code>comparar_vias_icg.py</code>. Fuentes: <code>estimar_gamma_individual.py</code> (γ por grupo),
<code>icg_contexto.py</code> (serie limpia), <code>curva_ciclo_presidencial.csv</code> (el ciclo),
<code>datos/padron</code> (la cámara), <code>modelo/voto_individual</code> (los desvíos).</p>
</body></html>"""


if __name__ == "__main__":
    raise SystemExit(
        "comparar_vias_icg.py NEUTRALIZADO (2026-08-11): la capa 2 global se "
        "eliminó y aplicar_dos_capas ya no existe. Este comparador no corre más. "
        "Ver ADR-0008 rev 2026-08-11.")
