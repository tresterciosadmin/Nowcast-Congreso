# -*- coding: utf-8 -*-
"""LA CALIBRACIÓN DECLARADA reproduce la tabla del §9.2 y no pisa nada (auditoría 2026-09, ítem C2).

QUÉ FIJA (los criterios 3, 4, 6 y 7 del pre-registro de C2 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. LA TABLA DEL §9.2. Desde el JSON por acta que viaja por git, `calibracion_declarada.tabla_simple` da los cuatro
     renglones por cámara y «ambas» de `coordinacion/AUDITORIA-2026-09/resultados/simple_por_camara.txt` (n, tasa base,
     Brier de la constante, Brier del modelo, AUC, Brier recalibrado, Brier y log-loss sin ε₀+τη) y las rechazadas
     (106, mediana de P 0,911, 79 con P > 0,8). El recalibrado se compara a ±0,00015 (la versión de `scipy` del CI y la
     de la PC difieren); el resto, exacto al redondeo de la tabla.
  2. LO NUEVO, ANCLADO. El IC pareado de Δ = Brier(modelo) − Brier(constante) y la cobertura de la banda (con su IC)
     que dio la medición de C2 —las anclas están abajo, fijadas DESPUÉS de medir, citando la medición—, y la
     coherencia interna: Δ = Brier del modelo − Brier de la constante, el IC contiene al punto, los «objetivos» salen
     de los IC con la regla fijada en el pre-registro.
  3. NO PISA. Un destino que existe se rechaza (salida 3); aun con `--reemplazar`, un archivo sin la marca `generador`
     (`baseline_voto_individual.json`); y regenerar uno propio con `--reemplazar` anda.
  4. EL JSON VERSIONADO ESTÁ AL DÍA: sus números salen de la regeneración desde el JSON por acta; cita el sha256 del
     JSON por acta de hoy; trae la procedencia; y los parámetros con que se simuló (ε₀, τ, `reparto_desvio`, piso de
     desvío, ε de incertidumbre, quórum) son los del `registro_parametros.json` (por archivo y nombre).
Y un control que puede fallar (regla 5): una P de producción alterada, otra semilla del bootstrap o un default de
réplicas distinto NO reproducen lo anclado.

No lee el detalle del censo (37 MB, no viaja por git) ni simula nada: corre en el CI. Cuando la fase D cambie el motor
hay que regenerar (`calibracion_declarada.py --simular`, ≈ 15 min) y re-anclar a propósito, citando la medición.

    python evaluacion/baseline/tests/test_calibracion_declarada.py
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import calibracion_declarada as C  # noqa: E402
import metrica_de_verdad as MV  # noqa: E402

PUBLICADO = RAIZ / "evaluacion" / "baseline" / "outputs" / "baseline_voto_individual.json"
VERSIONADA = RAIZ / C.SALIDA
ACTAS = RAIZ / C.ACTAS
REGISTRO = RAIZ / "modelo" / "ensemble" / "outputs" / "registro_parametros.json"

# ── la tabla del §9.2 (`coordinacion/AUDITORIA-2026-09/resultados/simple_por_camara.txt`) ───────────────────────
# (cámara, subconjunto): n, tasa base, Brier const., Brier modelo, AUC, Brier recal. (CV), Brier sin ε₀+τη, log-loss, log-loss sin
TABLA = {("diputados", "todas"): (2543, 0.975, 0.0242, 0.0357, 0.732, 0.0236, 0.0244, 0.1658, 0.1241),
         ("diputados", "disputadas"): (1314, 0.953, 0.0450, 0.0576, 0.648, 0.0447, 0.0472, 0.2333, 0.2307),
         ("senado", "todas"): (2851, 0.985, 0.0149, 0.0174, 0.600, 0.0149, 0.0149, 0.0970, 0.0794),
         ("senado", "disputadas"): (885, 0.953, 0.0452, 0.0485, 0.562, 0.0457, 0.0466, 0.2031, 0.2281)}
AMBAS = (5394, 0.980, 0.0193, 0.0260, 0.687, None, 0.0194, 0.1294, 0.1004)
RECHAZADAS = (106, 0.911, 79)
TOL_RECAL = 0.00015

# ── lo nuevo: fijado DESPUÉS de medir (C2, `calibracion_declarada.py --simular`, 2.000 réplicas, semilla 7) ─────
ANCLA_DELTA = {       # (cámara, subconjunto) → (Δ, extremo inferior del IC, extremo superior)
    ("diputados", "todas"): (0.01154, 0.00793, 0.01576),
    ("diputados", "disputadas"): (0.01265, 0.00679, 0.01889),
    ("senado", "todas"): (0.00258, 0.00154, 0.00376),
    ("senado", "disputadas"): (0.00328, 0.00043, 0.00678),
}
ANCLA_BANDA = {       # (población, cámara) → (n_actas, cobertura, extremo inferior, extremo superior, ancho mediano, sesgo)
    ("todas_las_actas", "ambas"): (5852, 0.6364, 0.6148, 0.658, 40.0, 6.93),
    ("todas_las_actas", "diputados"): (2858, 0.6039, 0.5692, 0.6385, 88.1, 10.53),
    ("todas_las_actas", "senado"): (2994, 0.6673, 0.6432, 0.6903, 23.0, 3.49),
    ("mayoria_simple", "ambas"): (5414, 0.6289, 0.6056, 0.6521, 34.5, 8.29),
    ("mayoria_simple", "diputados"): (2547, 0.585, 0.5434, 0.6226, 87.0, 13.56),
    ("mayoria_simple", "senado"): (2867, 0.6679, 0.6428, 0.6925, 23.0, 3.6),
}

CAMPOS = ("n", "tasa_base", "brier_constante", "brier_modelo", "auc", "brier_recalibrado_cv", "brier_sin_eps0_tau",
          "logloss_modelo", "logloss_sin_eps0_tau")


def _cmd(argv: list) -> int:
    """`calibracion_declarada.main` sin su salida (los rechazos escriben en stderr a propósito)."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return C.main(argv)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test(fallos: list[str]) -> int:
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    t0 = time.time()
    est, a = C.cargar_actas(ACTAS)
    res = C.medir(a)       # los defaults de verdad: 2.000 réplicas, semilla 7
    t = res["tabla_simple"]

    print("1. la tabla del §9.2 desde el JSON por acta")
    check(C.N_BOOT >= 2000 and C.SEMILLA == 7, f"defaults del IC: {C.N_BOOT} réplicas, semilla {C.SEMILLA}")
    for (cam, sub), ref in list(TABLA.items()) + [(("ambas", "todas"), AMBAS)]:
        f = t[cam][sub]
        for campo, esperado in zip(CAMPOS, ref):
            if esperado is None:
                continue
            valor = round(f[campo], 3) if campo == "tasa_base" else f[campo]
            tol = TOL_RECAL if campo == "brier_recalibrado_cv" else 1e-9
            check(abs(valor - esperado) <= tol, f"{cam} {sub}: {campo} {valor} ≠ {esperado} (§9.2)")
    r = t["rechazadas_en_simple"]
    check((r["n"], r["p_mediana"], r["n_con_p_mayor_0_8"]) == RECHAZADAS,
          f"rechazadas {r} ≠ {RECHAZADAS} (§9.2)")
    print(f"  Diputados {t['diputados']['todas']['brier_modelo']} contra {t['diputados']['todas']['brier_constante']}; "
          f"Senado {t['senado']['todas']['brier_modelo']} contra {t['senado']['todas']['brier_constante']} "
          f"({time.time() - t0:.0f} s)")

    print("\n2. lo nuevo: el IC pareado de Δ y la cobertura de la banda (anclas fijadas después de medir)")
    for cam in ("diputados", "senado"):
        for sub in ("todas", "disputadas"):
            f, d = t[cam][sub], t[cam][sub]["modelo_menos_constante"]
            check(abs(d["delta"] - (f["brier_modelo"] - f["brier_constante"])) <= 2e-4,
                  f"{cam} {sub}: Δ {d['delta']} ≠ Brier modelo − Brier constante")
            check(d["ic95_ley"][0] <= d["delta"] <= d["ic95_ley"][1], f"{cam} {sub}: el IC de Δ no contiene a Δ")
            if (cam, sub) in ANCLA_DELTA:
                ref = ANCLA_DELTA[(cam, sub)]
                check((d["delta"], *d["ic95_ley"]) == ref, f"{cam} {sub}: Δ e IC {(d['delta'], *d['ic95_ley'])} ≠ ancla {ref}")
    check(bool(ANCLA_DELTA), "no hay anclas de Δ")
    o3 = res["objetivos_9_4"]["3_brier_menor_que_la_constante_con_ic_pareado_que_excluya_0"]
    for cam in ("diputados", "senado"):
        sup = t[cam]["todas"]["modelo_menos_constante"]["ic95_ley"][1]
        check(o3[cam]["cumple"] == (sup < 0), f"objetivo 3 de {cam} no sale de su IC")
    check(o3["cumple"] == (o3["diputados"]["cumple"] and o3["senado"]["cumple"]), "objetivo 3 global no sale de los de las cámaras")
    b = res["banda"]
    for (pob, cam), ref in ANCLA_BANDA.items():
        c = b[pob][cam]
        valor = (c["n_actas"], c["cobertura_banda_90"], *c["ic95_ley"], c["ancho_mediano_votos"], c["sesgo_medio_votos"])
        check(valor == ref, f"banda {pob}/{cam}: {valor} ≠ ancla {ref}")
        check(c["ic95_ley"][0] <= c["cobertura_banda_90"] <= c["ic95_ley"][1], f"banda {pob}/{cam}: el IC no contiene a la cobertura")
    check(bool(ANCLA_BANDA), "no hay anclas de la banda")
    todas = b["todas_las_actas"]["ambas"]
    check(abs(todas["observada_menos_declarada_pp"] - 100 * (todas["cobertura_banda_90"] - 0.9)) <= 0.06,
          "observada − declarada no sale de la cobertura")
    print(f"  Δ Diputados {t['diputados']['todas']['modelo_menos_constante']['delta']:+.5f} "
          f"{t['diputados']['todas']['modelo_menos_constante']['ic95_ley']} · Senado "
          f"{t['senado']['todas']['modelo_menos_constante']['delta']:+.5f} {t['senado']['todas']['modelo_menos_constante']['ic95_ley']}"
          f" · banda {todas['cobertura_banda_90']} {todas['ic95_ley']}")

    print("\n3. no pisa ningún número versionado")
    versionados = [p for p in (PUBLICADO, VERSIONADA, ACTAS) if p.is_file()]
    antes = {p: _sha(p) for p in versionados}
    check(_cmd(["--salida", str(PUBLICADO)]) == 3, "escribió (o no rechazó) sobre baseline_voto_individual.json")
    check(_cmd(["--salida", str(PUBLICADO), "--reemplazar"]) == 3, "con --reemplazar no rechazó un archivo ajeno")
    if VERSIONADA.is_file():
        check(_cmd(["--salida", str(VERSIONADA)]) == 3, "pisó la calibración versionada sin --reemplazar")
    check(_cmd(["--simular", "--salida", str(Path(tempfile.gettempdir()) / "no_existe_c2.json"), "--actas", str(ACTAS)]) == 3,
          "con --simular no rechazó pisar el JSON por acta versionado")
    check(_cmd(["--simular", "--reemplazar", "--salida", str(Path(tempfile.gettempdir()) / "no_existe_c2.json"),
                "--actas", str(PUBLICADO)]) == 3, "con --simular --reemplazar no rechazó un JSON por acta ajeno")
    check(antes == {p: _sha(p) for p in antes}, "el rechazo modificó un archivo versionado")
    with tempfile.TemporaryDirectory() as tmp:
        propio = Path(tmp) / "c.json"
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 0, "no pudo escribir un destino nuevo")
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 3, "pisó un archivo suyo sin --reemplazar")
        check(_cmd(["--n-boot", "50", "--salida", str(propio), "--reemplazar"]) == 0, "no pudo regenerar uno suyo")
        ajeno = Path(tmp) / "ajeno.json"
        ajeno.write_text(json.dumps({"x": 1}), encoding="utf-8")
        check(_cmd(["--n-boot", "50", "--salida", str(ajeno), "--reemplazar"]) == 3, "pisó un JSON ajeno con --reemplazar")

    print("\n4. el control puede fallar (regla 5)")
    a2 = a.copy()
    a2["p"] = a2["p"] * 0.5
    t2 = C.tabla_simple(a2, n_boot=50)
    check(t2["diputados"]["todas"]["brier_modelo"] != t["diputados"]["todas"]["brier_modelo"],
          "una P de producción alterada no movió el Brier")
    check(abs(t2["diputados"]["todas"]["brier_modelo"] - TABLA[("diputados", "todas")][3]) > 1e-3,
          "con P × 0,5 la tabla sigue reproduciendo el §9.2")
    s = a[(a["tipo"] == "SIMPLE") & a["y"].notna()]
    ic8 = C.ic_pareado(s["y"], s["p"], s["ley"], 300, 8)
    ic7 = C.ic_pareado(s["y"], s["p"], s["ley"], 300, 7)
    check(ic8["ic95_ley"] != ic7["ic95_ley"], "otra semilla dio el mismo IC: el test no ve el bootstrap")

    print("\n5. el JSON versionado está al día, con su procedencia")
    check(VERSIONADA.is_file(), f"falta {VERSIONADA}: `python evaluacion/baseline/src/calibracion_declarada.py`")
    if VERSIONADA.is_file():
        v = json.loads(VERSIONADA.read_text(encoding="utf-8"))
        check(v.get("generador") == C.GENERADOR, "el JSON versionado no lleva la marca del generador")
        check((v["metodo"]["n_boot"], v["metodo"]["semilla"]) == (C.N_BOOT, C.SEMILLA),
              "el JSON versionado se generó con otros defaults que los del comando de hoy: regenerar")
        for k in ("tabla_simple", "confiabilidad", "banda", "objetivos_9_4"):
            check(v[k] == res[k], f"`{k}` del JSON versionado no sale del JSON por acta de git: regenerar")
        pr = v["procedencia"]
        check(pr["actas"]["sha256_lf"] == MV._sha256_lf(ACTAS), "el JSON por acta cambió y la calibración no se regeneró")
        check(bool(pr.get("head_sha_al_correr")) and bool(pr.get("comando")), "procedencia sin HEAD o comando")
        check(bool(v.get("generado")), "falta la fecha")
    par = est["parametros"]
    reg = {(p["archivo"], p["nombre"]): p["default"] for p in json.loads(REGISTRO.read_text(encoding="utf-8"))["parametros"]}
    NPS, ENS, AGR = ("modelo/ensemble/src/nowcast_puertas.py", "modelo/ensemble/src/ensemble.py",
                     "modelo/agregador_institucional/src/agregador.py")
    for clave, (arch, nombre) in {"epsilon0": (NPS, "EPSILON0"), "tau": (NPS, "TAU"), "reparto_desvio": (NPS, "REPARTO_DESVIO"),
                                  "desvio_min_individual": (ENS, "DESVIO_MIN_INDIVIDUAL"), "p_incertidumbre": (ENS, "P_INCERTIDUMBRE"),
                                  "quorum_cuenta_abstenciones": (AGR, "QUORUM_CUENTA_ABSTENCIONES")}.items():
        check(par[clave] == reg[(arch, nombre)], f"se simuló con {clave} = {par[clave]}, el registro dice {reg[(arch, nombre)]}: regenerar")
    check(est["fuente"]["n_actas"] == len(a) == 5852, f"actas: {len(a)}")

    print(f"\n{corridos - len(fallos)}/{corridos} OK  ({time.time() - t0:.0f} s)")
    return corridos


def main() -> int:
    fallos: list[str] = []
    test(fallos)
    if fallos:
        print(f"\n{len(fallos)} FALLA(S)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
