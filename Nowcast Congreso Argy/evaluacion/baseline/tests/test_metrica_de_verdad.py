# -*- coding: utf-8 -*-
"""LA MÉTRICA DE VERDAD reproduce lo publicado y no pisa nada (auditoría 2026-09, ítem C1).

QUÉ FIJA (los criterios 1 a 5 y 7 del pre-registro de C1 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. CONTINUIDAD EXACTA. Con 300 réplicas y semilla 7, `metrica_de_verdad.medir` da, en global, las 5 eras y las 2
     cámaras, el mismo skill y el mismo IC que `baseline_voto_individual.json` (0,1333 [0,0574; 0,1979] en global).
     Es la prueba de que el bootstrap es el mismo que el del harness.
  2. LAS 2.000 RÉPLICAS. Con el valor por defecto (2.000), cada extremo del IC global está a menos de 0,010 del
     del control independiente (`control_independiente.json`: [0,0586; 0,1996]) y del del plan ([0,059; 0,200]).
     El 0,010 es tres desvíos de la diferencia entre dos sorteos del bootstrap (medida con 20 semillas: el
     extremo inferior se mueve con desvío 0,0023). El control usa otra semilla (11) y otro orden de las leyes:
     las dos diferencias son ruido de Monte Carlo, no un error.
  3. ΔBrier PAREADO global (300 réplicas): +2,12% [0,84; 3,48] (el número de A2).
  4. CONTROL DE MUESTRA sin los votos sin ley (300 réplicas): 585.822 votos, 2.944 leyes, 0,166 [0,084; 0,252].
  5. NO PISA. Un destino que existe se rechaza (salida 3) sin tocarlo; aun con `--reemplazar`, un archivo que no es
     de este comando (`baseline_voto_individual.json`) se rechaza; y, para que el rechazo no sea la única salida,
     regenerar un archivo propio con `--reemplazar` anda.
  7. EL JSON VERSIONADO ESTÁ AL DÍA: sus números salen de la regeneración desde los estadísticos de git; cita el
     sha256 del JSON de estadísticos que hoy está en el repo (si alguien regenera el censo y no la métrica, falla);
     trae la procedencia completa, `n_boot ≥ 2000` y el certificado de vigencia del motor (`vigente: true`, que se
     escribe con `--verificar-motor` en la PC, donde está el detalle del censo).
Y un control que puede fallar (regla 5): un Σ(p−y)² alterado en 1%, o otra semilla, NO reproducen lo publicado.

No lee el detalle del censo (37 MB, no viaja por git): corre en el CI. Las anclas son las de los archivos de
`baseline_voto_individual.json` y `control_independiente.json`; cuando la fase D regenere el censo hay que
re-anclarlas a propósito, citando la medición.

    python evaluacion/baseline/tests/test_metrica_de_verdad.py
"""
from __future__ import annotations

import contextlib
import copy
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
import censo_estadisticos as ce  # noqa: E402
import metrica_de_verdad as M  # noqa: E402

PUBLICADO = RAIZ / "evaluacion" / "baseline" / "outputs" / "baseline_voto_individual.json"
CONTROL = RAIZ / "coordinacion" / "AUDITORIA-2026-09" / "resultados" / "control_independiente.json"
VERSIONADA = RAIZ / M.SALIDA
ESTADISTICOS = RAIZ / ce.ESTADISTICOS

TOL_IC_2000 = 0.010          # tres desvíos de la diferencia entre dos sorteos del bootstrap (pre-registro de C1)
PLAN = (0.059, 0.200)        # el criterio del plan para C1 (informe §9.4)
CONTINUIDAD = {"global": 0.1333}


def _cmd(argv: list) -> int:
    """`metrica_de_verdad.main` sin su salida (los rechazos escriben en stderr a propósito)."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return M.main(argv)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _publicado_por_corte(pub: dict) -> dict:
    out = {"global": pub["global"]}
    out.update({f"era={e}": v for e, v in pub["por_era"].items()})
    out.update({f"camara={c}": v for c, v in pub["por_camara"].items()})
    return out


def test(fallos: list[str]) -> int:
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    t0 = time.time()
    est = ce.cargar(ESTADISTICOS)
    pub = json.loads(PUBLICADO.read_text(encoding="utf-8"))
    ctl = json.loads(CONTROL.read_text(encoding="utf-8"))

    print("1. continuidad exacta con lo publicado por el harness (300 réplicas, semilla 7)")
    check(pub["columna"] == "p__estricta__general", f"lo publicado ya no es el motor de hoy: {pub['columna']}")
    check(M.SEMILLA == 7, f"la semilla por defecto es {M.SEMILLA}, no la 7 del harness: la continuidad se pierde")
    m300 = M.medir(est, n_boot=300, seed=7)
    for corte, p in _publicado_por_corte(pub).items():
        r = m300["skill"][corte]
        check(r["skill"] == p["skill"], f"{corte}: skill {r['skill']} ≠ publicado {p['skill']}")
        check(r["skill_ic95_ley"] == p["skill_ic95_ley"],
              f"{corte}: IC {r['skill_ic95_ley']} ≠ publicado {p['skill_ic95_ley']}")
        check(r["n_leyes"] == p["n_leyes"], f"{corte}: leyes {r['n_leyes']} ≠ publicado {p['n_leyes']}")
    g = m300["skill"]["global"]
    check(g["skill"] == CONTINUIDAD["global"], f"el skill global no es {CONTINUIDAD['global']}: {g['skill']}")
    # una sola copia del cálculo: lo mismo que `censo_estadisticos.skill` en los cortes estándar
    a = ce.tabla_actas(est)
    for corte in ce.cortes(a):
        ref = ce.skill(est, M.VARIANTE, corte, a, 300, 7)
        check(m300["skill"][corte] == ref, f"{corte}: la métrica no coincide con censo_estadisticos.skill")
    print(f"  global {g['skill']} {g['skill_ic95_ley']}; {len(m300['skill'])} cortes comparados ({time.time() - t0:.0f} s)")

    print("\n2. con 2.000 réplicas (el valor por defecto) el IC global reproduce el del control independiente")
    check(M.N_BOOT >= 2000, f"el default de réplicas es {M.N_BOOT}: la pieza 1 pide ≥ 2.000")
    m2000 = M.medir(est)       # los defaults de verdad
    lo, hi = m2000["skill"]["global"]["skill_ic95_ley"]
    motor_ctl = next(v for k, v in ctl["cortes"]["global"]["predictores"].items() if k.startswith("MOTOR"))
    for nombre, ref in (("el control independiente", tuple(motor_ctl["ic95_ley"])), ("el plan (C1)", PLAN)):
        check(abs(lo - ref[0]) <= TOL_IC_2000 and abs(hi - ref[1]) <= TOL_IC_2000,
              f"IC con 2.000 réplicas [{lo}; {hi}] a más de {TOL_IC_2000} de {nombre} {list(ref)}")
    check(m2000["skill"]["global"]["skill"] == motor_ctl["skill"], "el punto no coincide con el del control")
    print(f"  2.000 réplicas: [{lo}; {hi}] · control {motor_ctl['ic95_ley']} · plan {list(PLAN)}")

    print("\n3. ΔBrier pareado (300 réplicas): el número de A2")
    d = m300["dif_brier_pareado"]["global"]
    check(round(d["dBrier_rel_%"], 2) == 2.12, f"ΔBrier relativo {d['dBrier_rel_%']} ≠ +2,12%")
    check([round(x, 2) for x in d["ic95_rel_%_ley"]] == [0.84, 3.48], f"IC del ΔBrier {d['ic95_rel_%_ley']} ≠ [0,84; 3,48]")

    print("\n4. control de muestra: sin los votos sin ley")
    s = m300["skill"][M.CORTE_SIN_LEY]
    check((s["n_votos"], s["n_leyes"]) == (585_822, 2_944), f"votos/leyes {s['n_votos']}/{s['n_leyes']} ≠ 585.822/2.944")
    check(round(s["skill"], 3) == 0.166, f"skill {s['skill']} ≠ 0,166")
    check([round(x, 3) for x in s["skill_ic95_ley"]] == [0.084, 0.252], f"IC {s['skill_ic95_ley']} ≠ [0,084; 0,252]")

    print("\n5. no pisa ningún número versionado")
    antes = {p: _sha(p) for p in (PUBLICADO, VERSIONADA) if p.is_file()}
    check(_cmd(["--salida", str(PUBLICADO)]) == 3, "escribió (o no rechazó) sobre baseline_voto_individual.json")
    check(_cmd(["--salida", str(PUBLICADO), "--reemplazar"]) == 3,
          "con --reemplazar no rechazó un archivo que no es suyo")
    if VERSIONADA.is_file():
        check(_cmd(["--salida", str(VERSIONADA)]) == 3, "pisó la métrica versionada sin --reemplazar")
    despues = {p: _sha(p) for p in antes}
    check(antes == despues, "el rechazo modificó un archivo versionado")
    with tempfile.TemporaryDirectory() as tmp:
        propio = Path(tmp) / "m.json"
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 0, "no pudo escribir un destino nuevo")
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 3, "pisó un archivo suyo sin --reemplazar")
        check(_cmd(["--n-boot", "50", "--salida", str(propio), "--reemplazar"]) == 0,
              "no pudo regenerar un archivo suyo con --reemplazar")
        ajeno = Path(tmp) / "ajeno.json"
        ajeno.write_text(json.dumps({"skill": 0.1333}), encoding="utf-8")
        check(_cmd(["--n-boot", "50", "--salida", str(ajeno), "--reemplazar"]) == 3,
              "pisó un JSON ajeno (sin la marca `generador`) con --reemplazar")

    print("\n6. el control puede fallar (regla 5)")
    alterado = copy.deepcopy(est)
    c = {n: i for i, n in enumerate(alterado["actas"]["columnas"])}
    for f in alterado["actas"]["filas"]:
        f[c["se__estricta__general"]] *= 1.01
    sk = M.medir(alterado, n_boot=300, seed=7)["skill"]["global"]
    check(sk["skill"] != g["skill"], "un Σ(p−y)² alterado en 1% no movió el skill")
    check(sk["skill"] != pub["global"]["skill"], "con Σ(p−y)² × 1,01 el skill sigue igual al publicado")
    otra = M.medir(est, n_boot=300, seed=8)["skill"]["global"]["skill_ic95_ley"]
    check(otra != pub["global"]["skill_ic95_ley"], "otra semilla dio el mismo IC: el test no ve el bootstrap")
    print(f"  Σ(p−y)² × 1,01 → skill {sk['skill']}; semilla 8 → IC {otra}")

    print("\n7. el JSON versionado está al día, con su procedencia")
    check(VERSIONADA.is_file(), f"falta {VERSIONADA}: `python evaluacion/baseline/src/metrica_de_verdad.py --verificar-motor 60`")
    if VERSIONADA.is_file():
        v = json.loads(VERSIONADA.read_text(encoding="utf-8"))
        meto = v["metodo"]
        check(v.get("generador") == M.GENERADOR, "el JSON versionado no lleva la marca del generador")
        check(meto["n_boot"] >= 2000, f"el JSON versionado se generó con {meto['n_boot']} réplicas (< 2.000)")
        check((meto["variante"], meto["contra"], meto["n_boot"], meto["semilla"]) == (
            M.VARIANTE, M.CONTRA, M.N_BOOT, M.SEMILLA),
              "el JSON versionado se generó con otros valores por defecto que los del comando de hoy: regenerar")
        mismos = (meto["variante"], meto["contra"], meto["n_boot"], meto["semilla"]) == (
            M.VARIANTE, M.CONTRA, M.N_BOOT, M.SEMILLA)
        reg = m2000 if mismos else M.medir(est, meto["variante"], meto["contra"], meto["n_boot"], meto["semilla"])
        check(v["skill"] == reg["skill"], "el skill del JSON versionado no sale de los estadísticos de git: regenerar")
        check(v["dif_brier_pareado"] == reg["dif_brier_pareado"],
              "el ΔBrier pareado del JSON versionado no sale de los estadísticos de git: regenerar")
        pr = v["procedencia"]
        check(pr["estadisticos"]["sha256_lf"] == M._sha256_lf(ESTADISTICOS),
              "el JSON de estadísticos cambió y la métrica no se regeneró (sha256 distinto)")
        check(pr["estadisticos"]["censo"] == est["fuente"], "la fuente del censo citada no es la del JSON de estadísticos")
        for campo in ("head_sha_al_correr", "comando"):
            check(bool(pr.get(campo)), f"procedencia sin {campo}")
        for campo in ("escrito_el", "motor_sha_al_escribirlo", "nota_motor_sha", "sha256_lf", "ruta"):
            check(bool(pr["estadisticos"].get(campo)), f"procedencia.estadisticos sin {campo}")
        check(bool(v.get("generado")), "falta la fecha")
        vig = v.get("vigencia_del_motor")
        check(bool(vig) and vig.get("vigente") is True,
              "el JSON versionado no trae el certificado de vigencia del motor (`--verificar-motor`)")
        if vig:
            check(vig["max_abs_dP"] <= M.UMBRAL_VIGENCIA and vig["votos_solo_en_el_detalle"] == 0
                  and vig["votos_solo_en_el_motor_de_hoy"] == 0, "el certificado de vigencia no cumple su umbral")
            print(f"  certificado: {vig['actas']} actas, {vig['votos_comparados']} votos, max|ΔP| = {vig['max_abs_dP']:.3g}, "
                  f"motor {vig['motor_head_sha']}")

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
