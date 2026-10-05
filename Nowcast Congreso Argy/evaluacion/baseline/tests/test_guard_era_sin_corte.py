# -*- coding: utf-8 -*-
"""EL BRAZO «SIN CORTE POR ERA» reproduce su veredicto y sus controles desde git (auditoría 2026-09, ítem C3).

QUÉ FIJA (el criterio 5 del pre-registro de C3 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. LOS CONTROLES DEL BRAZO, desde los estadísticos por acta que viajan por git: el panel es el de A2 (las sumas de
     `estricta__general` coinciden acta por acta); ANTES DE 2015-12-10 el brazo es IDÉNTICO al motor (el guard ya no
     corta: la era arranca en 1900) y desde esa fecha algunas actas difieren. Si esto falla, el brazo no mide lo que dice
     y no se interpreta ningún Δ.
  2. EL VERDICTO, anclado: ΔBrier pareado (sin corte − con corte) / con corte, con su IC por ley, en el primario
     (actas desde 2015-12-10), el control (antes) y los secundarios; y la regla (`regla`), que no puede mover la bandera.
  3. NO PISA (mismas reglas que `metrica_de_verdad.py` y `calibracion_declarada.py`), también con `--censo`.
  4. EL JSON VERSIONADO ESTÁ AL DÍA: sus números salen de los estadísticos de git, cita el sha256 de los estadísticos
     de hoy, trae la procedencia y los controles de la PC (`pc_solo`: mismo conjunto de votos, max|Δp| = 0 antes de
     2015-12-10, `n_prev` del brazo nunca menor, postura idéntica).
Y un control que puede fallar (regla 5): un brazo alterado antes de 2015 rompe el control 1; un brazo sin ningún efecto
da Δ ≡ 0; otra semilla del bootstrap no reproduce el ancla.

  0. EL VEREDICTO DE C3, conservado: desde los estadísticos del brazo de C3 (`R.ESTADISTICOS_C3`, sobre el censo del 28-09,
     que siguen en git y no se pisan), los controles contra ESE censo y las anclas y el resultado de C3.

No lee el detalle del censo (no viaja por git): corre en el CI. Las anclas de 0 son las de la medición de C3; las de 1 a 5,
las del brazo re-corrido sobre el censo del motor de HOY (auditoría D1.0, censo del 2026-10-02, con la ficha de desvío al
día; `medir_sin_corte_por_era.py --censo`, 2.000 réplicas, semilla 7), fijadas DESPUÉS de medir. Si la fase D vuelve a
cambiar el motor hay que regenerar el censo del brazo y re-anclar a propósito, citando la medición.

    python evaluacion/baseline/tests/test_guard_era_sin_corte.py
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

import numpy as np

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import censo_estadisticos as ce  # noqa: E402
import medir_sin_corte_por_era as R  # noqa: E402
import metrica_de_verdad as MV  # noqa: E402

PUBLICADO = RAIZ / "evaluacion" / "baseline" / "outputs" / "baseline_voto_individual.json"
VERSIONADA = RAIZ / R.SALIDA
ESTADISTICOS = RAIZ / R.ESTADISTICOS                 # el brazo sobre el motor de hoy (1 a 5)
A2 = RAIZ / ce.ESTADISTICOS                           # el censo del motor de hoy
ESTADISTICOS_C3 = RAIZ / R.ESTADISTICOS_C3            # el brazo de C3 (0)
A2_C3 = RAIZ / ce.ESTADISTICOS_2026_09_28             # el censo del 28-09

# ── el veredicto de C3, fijado DESPUÉS de medir (`medir_sin_corte_por_era.py --censo`; 2.000 réplicas, semilla 7) ──
# corte → (ΔBrier relativo %, extremo inferior, extremo superior, votos, leyes); positivo = el guard ayuda
ANCLA_C3 = {
    "primario__desde_2015-12-10": (3.0, -2.94, 9.67, 257543, 1055),
    "control__antes_de_2015-12-10": (0.0, 0.0, 0.0, 434302, 2684),
    "secundario__global": (1.46, -1.4, 4.69, 691845, 3731),
    "secundario__era=2015-2019": (8.95, -0.66, 19.53, 126454, 505),
    "secundario__era=2019-2023": (12.91, -4.72, 21.12, 25755, 246),
    "secundario__era=desde 2023": (-3.68, -7.72, 3.45, 105334, 312),
    "secundario__desde_2015-12-10 & camara=diputados": (2.7, -3.65, 10.59, 204123, 540),
    "secundario__desde_2015-12-10 & camara=senado": (4.99, 1.4, 8.99, 53420, 592),
}
RESULTADO_C3 = "NO_SE_DISTINGUE"
# ── el brazo sobre el motor de hoy (lote de D1: la ventana de la postura en 2190 días), fijado DESPUÉS de medir; mismo
# formato. Con este motor quitar el guard EMPEORA con IC que excluye 0: coincide con lo que D1 decidió (Z, «se conserva
# prendido») y no reabre nada. Los de D1.0 (censo del 2026-10-02, NO_SE_DISTINGUE), en el comentario de cada fila ──
ANCLA = {
    "primario__desde_2015-12-10": (5.66, 0.4, 11.5, 257543, 1055),                  # D1.0: (3.23, -2.33, 9.72, …)
    "control__antes_de_2015-12-10": (0.0, 0.0, 0.0, 435172, 2690),                  # D1.0: 434302 votos, 2684 leyes
    "secundario__global": (2.69, 0.1, 5.53, 692715, 3737),                          # D1.0: (1.57, -1.14, 4.68, 691845, 3731)
    "secundario__era=2015-2019": (9.23, -0.52, 19.8, 126454, 505),                  # D1.0: (8.91, -0.69, 19.49, …)
    "secundario__era=2019-2023": (11.79, -3.63, 18.6, 25755, 246),                  # D1.0: (12.94, -5.03, 21.45, …)
    "secundario__era=desde 2023": (1.27, -4.69, 6.16, 105334, 312),                 # D1.0: (-3.23, -7.04, 3.35, …)
    "secundario__desde_2015-12-10 & camara=diputados": (5.69, -0.39, 12.38, 204123, 540),  # D1.0: (2.99, -3.21, 10.69, …)
    "secundario__desde_2015-12-10 & camara=senado": (5.43, 1.88, 9.59, 53420, 592),        # D1.0: (4.8, 1.22, 8.82, …)
}
RESULTADO = "EL_GUARD_SE_SOSTIENE"   # D1.0: NO_SE_DISTINGUE


def _cmd(argv: list) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return R.main(argv)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def controles_en_estadisticos(est: dict, a2_ruta: Path = A2) -> list[str]:
    """Los controles del brazo que se pueden verificar sin el voto a voto. Devuelve las violaciones (vacío = en orden).
    Es la ÚNICA función que decide «el brazo está mal cableado»: el test y las derivas sintéticas la comparten."""
    import pandas as pd
    a, a2 = ce.tabla_actas(est), ce.tabla_actas(ce.cargar(a2_ruta))
    mal = []
    if list(a["acta_id"]) != list(a2["acta_id"]) or not (a["n"].to_numpy() == a2["n"].to_numpy()).all() \
            or not (a["sy"].to_numpy() == a2["sy"].to_numpy()).all():
        mal.append("el panel (actas, votos, afirmativos) no es el de los estadísticos de A2")
    elif not np.allclose(a["se__estricta__general"], a2["se__estricta__general"], rtol=0, atol=1e-9):
        mal.append("las sumas del motor (`estricta__general`) ya no coinciden con las de A2")
    antes = (a["fecha"] < pd.Timestamp(R.PRIMARIO_DESDE)).to_numpy()
    for col in ("se", "sp", "sp2"):
        d = (a[f"{col}__{R.ARM}"] - a[f"{col}__{R.BASE}"]).abs().to_numpy()
        if d[antes].max() != 0.0:
            mal.append(f"antes de {R.PRIMARIO_DESDE} el brazo NO es idéntico al motor ({col}: max|Δ| = {d[antes].max():.3g})")
    if not (np.abs(a[f"se__{R.ARM}"] - a[f"se__{R.BASE}"]).to_numpy()[~antes] > 0).any():
        mal.append(f"desde {R.PRIMARIO_DESDE} el brazo no difiere del motor en ninguna acta: no tiene efecto")
    return mal


def test(fallos: list[str]) -> int:
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    t0 = time.time()
    print("0. el veredicto de C3, conservado (brazo sobre el censo del 28-09)")
    est_c3 = ce.cargar(ESTADISTICOS_C3)
    mal = controles_en_estadisticos(est_c3, A2_C3)
    check(not mal, "controles del brazo de C3: " + "; ".join(mal))
    res_c3 = R.veredicto(est_c3)
    for corte, ref in ANCLA_C3.items():
        x = res_c3["dif_brier_pareado"][corte]
        check((x["dBrier_rel_%"], *x["ic95_rel_%_ley"], x["n_votos"], x["n_leyes"]) == ref, f"C3 {corte}: ≠ ancla {ref}")
    check(res_c3["veredicto"]["resultado"] == RESULTADO_C3, f"el veredicto de C3 es {res_c3['veredicto']['resultado']}")
    est = ce.cargar(ESTADISTICOS)
    res = R.veredicto(est)       # los defaults de verdad: 2.000 réplicas, semilla 7

    print("1. los controles del brazo, desde los estadísticos de git")
    mal = controles_en_estadisticos(est)
    check(not mal, "controles del brazo: " + "; ".join(mal))
    # la población del censo de hoy (lote de D1: la ventana de 2190 días suma 870 votos y 6 actas; antes, 691.845 y 5.856)
    check(est["fuente"]["n_votos"] == 692_715 and est["fuente"]["n_actas"] == 5_862,
          f"el panel no tiene los votos y actas de siempre: {est['fuente']}")
    check(est["fuente"].get("era_desde_del_brazo") == R.ERA_DESDE, "el brazo no se generó con era_desde = 1900-01-01")
    check(R.N_BOOT >= 2000 and R.SEMILLA == 7, f"defaults del IC: {R.N_BOOT} réplicas, semilla {R.SEMILLA}")

    print("\n2. el veredicto, anclado")
    d = res["dif_brier_pareado"]
    check(bool(ANCLA) and RESULTADO is not None, "faltan las anclas del brazo sobre el motor de hoy (fijarlas citando la medición)")
    for corte, (rel, lo, hi, nv, nl) in ANCLA.items():
        x = d[corte]
        check((x["dBrier_rel_%"], *x["ic95_rel_%_ley"], x["n_votos"], x["n_leyes"]) == (rel, lo, hi, nv, nl),
              f"{corte}: {(x['dBrier_rel_%'], *x['ic95_rel_%_ley'], x['n_votos'], x['n_leyes'])} ≠ ancla {(rel, lo, hi, nv, nl)}")
    check(res["veredicto"]["resultado"] == RESULTADO, f"el veredicto es {res['veredicto']['resultado']}, no {RESULTADO}")
    check(res["veredicto"]["la_bandera_se_toca"] is False and res["veredicto"]["decide"] == "Franco",
          "el veredicto movería la bandera o no deja decidir a Franco")
    # la regla, por sus tres ramas (y recomienda Opus sólo cuando el IC incluye 0)
    r1, r2, r3 = R.regla([0.1, 2.0]), R.regla([-2.0, -0.1]), R.regla([-1.0, 1.0])
    check((r1["resultado"], r2["resultado"], r3["resultado"]) ==
          ("EL_GUARD_SE_SOSTIENE", "SIN_CORTE_ES_MEJOR", "NO_SE_DISTINGUE"), "la regla no separa las tres ramas")
    check((r1["recomendar_opus"], r2["recomendar_opus"], r3["recomendar_opus"]) == (False, False, True),
          "la regla recomienda Opus fuera del caso «el IC incluye 0»")
    check(not any(x["la_bandera_se_toca"] for x in (r1, r2, r3)), "una rama de la regla toca la bandera")
    p = d["primario__desde_2015-12-10"]
    print(f"  primario: {p['dBrier_rel_%']:+.2f}% {p['ic95_rel_%_ley']} ({p['n_leyes']} leyes) → {res['veredicto']['resultado']}")

    print("\n3. no pisa ningún número versionado")
    versionados = [q for q in (PUBLICADO, VERSIONADA, ESTADISTICOS, ESTADISTICOS_C3) if q.is_file()]
    antes = {q: _sha(q) for q in versionados}
    check(_cmd(["--salida", str(PUBLICADO)]) == 3, "escribió (o no rechazó) sobre baseline_voto_individual.json")
    check(_cmd(["--salida", str(PUBLICADO), "--reemplazar"]) == 3, "con --reemplazar no rechazó un archivo ajeno")
    check(_cmd(["--salida", str(VERSIONADA)]) == 3, "pisó el veredicto versionado sin --reemplazar")
    check(_cmd(["--censo", "--salida", str(Path(tempfile.gettempdir()) / "no_existe_c3.json")]) == 3,
          "con --censo no rechazó pisar los estadísticos versionados (habría corrido el censo de 14 min)")
    check(_cmd(["--censo", "--reemplazar", "--salida", str(PUBLICADO)]) == 3,
          "con --censo --reemplazar no rechazó un destino ajeno antes de correr el censo")
    check(antes == {q: _sha(q) for q in antes}, "el rechazo modificó un archivo versionado")
    with tempfile.TemporaryDirectory() as tmp:
        propio = Path(tmp) / "g.json"
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 0, "no pudo escribir un destino nuevo")
        check(_cmd(["--n-boot", "50", "--salida", str(propio)]) == 3, "pisó un archivo suyo sin --reemplazar")
        check(_cmd(["--n-boot", "50", "--salida", str(propio), "--reemplazar"]) == 0, "no pudo regenerar uno suyo")
        ajeno = Path(tmp) / "ajeno.json"
        ajeno.write_text(json.dumps({"x": 1}), encoding="utf-8")
        check(_cmd(["--n-boot", "50", "--salida", str(ajeno), "--reemplazar"]) == 3, "pisó un JSON ajeno con --reemplazar")

    print("\n4. el control puede fallar (regla 5)")
    cols = est["actas"]["columnas"]
    i_f, i_se = cols.index("fecha"), cols.index(f"se__{R.ARM}")
    alterado = copy.deepcopy(est)
    for f in alterado["actas"]["filas"]:
        if f[i_f] < R.PRIMARIO_DESDE:
            f[i_se] *= 1.01
    check(bool(controles_en_estadisticos(alterado)), "un brazo alterado ANTES de 2015-12-10 no rompió el control")
    nulo = copy.deepcopy(est)
    for f in nulo["actas"]["filas"]:
        f[i_se] = f[cols.index(f"se__{R.BASE}")]
    check(bool(controles_en_estadisticos(nulo)), "un brazo sin efecto (idéntico al motor) no rompió el control")
    dn = R.veredicto(nulo, n_boot=50)["dif_brier_pareado"]["primario__desde_2015-12-10"]
    check(dn["dBrier_rel_%"] == 0.0 and dn["ic95_rel_%_ley"] == [0.0, 0.0], "un brazo sin efecto no da Δ ≡ 0")
    otra = R.veredicto(est, n_boot=300, seed=8)["dif_brier_pareado"]["primario__desde_2015-12-10"]["ic95_rel_%_ley"]
    ref = R.veredicto(est, n_boot=300, seed=7)["dif_brier_pareado"]["primario__desde_2015-12-10"]["ic95_rel_%_ley"]
    check(otra != ref, "otra semilla dio el mismo IC: el test no ve el bootstrap")

    print("\n5. el JSON versionado está al día, con su procedencia")
    check(VERSIONADA.is_file(), f"falta {VERSIONADA}: `python evaluacion/baseline/src/medir_sin_corte_por_era.py`")
    if VERSIONADA.is_file():
        v = json.loads(VERSIONADA.read_text(encoding="utf-8"))
        check(v.get("generador") == R.GENERADOR, "el JSON versionado no lleva la marca del generador")
        check((v["metodo"]["n_boot"], v["metodo"]["semilla"]) == (R.N_BOOT, R.SEMILLA),
              "el JSON versionado se generó con otros defaults que los del comando de hoy: regenerar")
        for k in ("dif_brier_pareado", "skill", "veredicto"):
            check(v[k] == res[k], f"`{k}` del JSON versionado no sale de los estadísticos de git: regenerar")
        pr = v["procedencia"]["estadisticos"]
        check(pr["sha256_lf"] == MV._sha256_lf(ESTADISTICOS), "los estadísticos cambiaron y el veredicto no se regeneró")
        check(bool(v["procedencia"].get("head_sha_al_correr")) and bool(v["procedencia"].get("comando")), "procedencia sin HEAD o comando")
        pc = v.get("pc_solo", {}).get("controles_del_brazo", {})
        check(pc.get("cumple") is True, "el JSON versionado no trae los controles del censo del brazo (`--censo`) cumplidos")
        if pc:
            check(pc["mismo_conjunto_de_votos"] and pc["antes_de_2015-12-10"]["max_abs_dp"] == 0.0
                  and pc["n_prev_brazo_menor_que_el_motor"] == 0 and pc["postura_share_max_abs_dif"] == 0.0
                  and pc["postura_desvio_max_abs_dif"] == 0.0 and pc["sumas_del_motor_iguales_a_las_de_A2"],
                  "los controles de la PC no cumplen el pre-registro")
            print(f"  controles de la PC: {pc['votos']} votos, antes de 2015: max|Δp| {pc['antes_de_2015-12-10']['max_abs_dp']}, "
                  f"desde 2015: {pc['desde_2015-12-10']['votos_distintos']} votos distintos")

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
