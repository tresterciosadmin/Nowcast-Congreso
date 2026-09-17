# -*- coding: utf-8 -*-
"""PRUEBA 3 de `coordinacion/PROMPT-DECIDIR-CAPITULOS.md` — ¿vale la pena
ampliar la cobertura de temas? PREGUNTA DE PRODUCTO, no de Brier: la tarea
pausada (`tema_por_proyecto.py clasificar --desde-fecha 2025-01-01`) es
sobre proyectos que TODAVÍA NO SE VOTARON, así que no pueden mover ninguna
métrica de backtest -- medirla con Brier daría un número que parece
riguroso y es la cosa equivocada. La pregunta correcta: de los proyectos
que alguien querría nowcastear HOY, ¿cuántos no tienen tema?

⚠️ `proyectos.estado` y `proyectos.ultimo_movimiento`/`ultimo_movimiento_fecha`
están ENTERAMENTE NULOS (medido acá, no sólo el primero como avisaba el
prompt) -- no sirven de filtro de "universo vivo". Se usa `fecha_ingreso`
(0 nulos, rango 2008-2026), consistente con el corte que ya usaba la tarea
pausada (`--desde-fecha 2025-01-01`).

CERO GASTO DE API. NO TOCA EL MOTOR: sólo lee y cuenta.

    python evaluacion/baseline/src/prueba3_cobertura_universo_vivo.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "proyecto" / "src"))
sys.path.insert(0, str(REPO / "docs" / "taxonomias" / "src"))

FECHA_DESDE_VIVO = "2025-01-01"  # mismo corte que la tarea pausada


def main() -> int:
    from tema_por_proyecto import cargar_crosswalk

    con = sqlite3.connect(str(REPO / "datos/proyectos/data/proyectos.db"))
    df = pd.read_sql("SELECT proyecto_id, camara, fecha_ingreso, sumario FROM proyectos", con)
    df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"])
    print(f"proyectos.estado / ultimo_movimiento_fecha -- fracción NULA: "
         f"{pd.read_sql('SELECT estado, ultimo_movimiento_fecha FROM proyectos', con).isna().mean().to_dict()}")

    vivo = df[df["fecha_ingreso"] >= FECHA_DESDE_VIVO].copy()

    a = pd.read_csv(REPO / "datos/taxonomias/data/asignaciones.csv")
    proy_clasif = a[a["nivel"] == "proyecto"]
    cx = cargar_crosswalk()
    vivo["denom"] = vivo["proyecto_id"].map(lambda p: cx["pid_a_denom"].get(str(p)))
    denoms_clasificados = set(proy_clasif["objeto"].astype(str))
    vivo["tiene_tema"] = vivo["denom"].isin(denoms_clasificados)

    v = pd.read_parquet(REPO / "datos/expedientes/data/clean/votacion_por_articulo.parquet")
    votados_ids = set(v["proyecto_id"].dropna().astype(str))
    vivo["votado"] = vivo["proyecto_id"].astype(str).isin(votados_ids)

    n_vivo = len(vivo)
    n_con_tema = int(vivo["tiene_tema"].sum())
    frac_sin_tema = 1 - (n_con_tema / n_vivo)

    n_votado = int(vivo["votado"].sum())
    n_votado_con_tema = int((vivo["votado"] & vivo["tiene_tema"]).sum())
    n_no_votado = n_vivo - n_votado
    n_no_votado_con_tema = n_con_tema - n_votado_con_tema

    clasif_vivo_denoms = vivo.loc[vivo["tiene_tema"], "denom"].dropna().unique()
    sub_aux = proy_clasif[proy_clasif["objeto"].isin(clasif_vivo_denoms)]
    frac_aux = float(sub_aux["area"].astype(str).str.upper().str.startswith("AUX").mean()) if len(sub_aux) else None

    # cota superior de mejora de Brier del lado VOTADO -- supuesto explícito:
    # los votos nuevos ganarían lo mismo que ya midió ADR-0026 (11,06% censo
    # completo) SI hubiera cobertura faltante ahí. Ya no la hay (ver resultado).
    MEJORA_BRIER_ADR0026 = 0.1106
    faltante_lado_votado = n_votado - n_votado_con_tema
    cota_brier = {
        "supuesto": "los votos del lado VOTADO sin tema, si se clasificaran, "
                    "ganarían lo mismo que ADR-0026 midió en el censo completo (11,06% "
                    "de mejora de Brier) -- cota, no medición.",
        "n_votado_sin_tema": faltante_lado_votado,
        "interpretacion": ("cero cobertura faltante del lado votado: no hay mejora de "
                          "Brier disponible por este camino, todo el hueco de cobertura "
                          "está del lado NO votado, que no puede mover ningún backtest"
                          if faltante_lado_votado == 0 else
                          f"{faltante_lado_votado} proyectos votados sin tema -- mejora "
                          f"de Brier acotada arriba por 11,06% aplicado a esos votos"),
    }

    # costo -- tokens REALES del prompt de agente_taxonomias.py (construir_prompt,
    # ruta texto/sumario, la barata -- "cobertura", no la de articulado completo),
    # precio DEJADO PARAMETRIZADO (no se verifica acá el precio vigente).
    from agente_taxonomias import construir_prompt, SYSTEM_PROMPT, MODELO_DEFAULT
    import loader as tx_loader
    tx = tx_loader.cargar()
    muestra = df[df["sumario"].notna() & (df["sumario"].str.strip() != "")]["sumario"].head(200)
    _, user_ejemplo = construir_prompt(muestra.iloc[0], tx)
    chars_input_medio = len(SYSTEM_PROMPT) + len(user_ejemplo) + int(muestra.str.len().mean()) - len(muestra.iloc[0])
    # (system + parte fija del user + sumario promedio de la muestra, no sólo el de ejemplo)
    chars_input_medio = len(SYSTEM_PROMPT) + (len(user_ejemplo) - len(muestra.iloc[0])) + int(muestra.str.len().mean())
    TOKENS_POR_CHAR = 0.25  # heurística estándar ~4 chars/token, no medido con el tokenizer real
    tokens_in_por_llamado = round(chars_input_medio * TOKENS_POR_CHAR)
    tokens_out_estimado_por_llamado = 120  # JSON corto: pocas ids + confianza + comentario breve

    n_llamados = n_vivo - n_con_tema
    costo = {
        "modelo": MODELO_DEFAULT,
        "n_llamados_necesarios": int(n_llamados),
        "chars_prompt_input_medio": chars_input_medio,
        "tokens_input_estimados_por_llamado": tokens_in_por_llamado,
        "tokens_output_estimados_por_llamado": tokens_out_estimado_por_llamado,
        "tokens_input_totales_estimados": int(n_llamados * tokens_in_por_llamado),
        "tokens_output_totales_estimados": int(n_llamados * tokens_out_estimado_por_llamado),
        "formula_costo": "tokens_input_totales * precio_input_por_token + "
                         "tokens_output_totales * precio_output_por_token "
                         "(precio vigente de claude-haiku-4-5-20251001, NO verificado acá)",
        "nota": "la corrida real de 437 clasificaciones por capítulo esta sesión costó "
               "'centavos de dólar' (medido cualitativamente, no en $ exactos) -- orden de "
               "magnitud consistente con que esto sea decenas de USD, no cientos.",
    }

    if frac_sin_tema >= 0.40:
        veredicto = "CONVIENE_AMPLIAR"
    elif frac_sin_tema >= 0.15:
        veredicto = "ZONA_GRIS"
    else:
        veredicto = "NO_CONVIENE"

    reporte = {
        "definicion_universo_vivo": f"fecha_ingreso >= {FECHA_DESDE_VIVO} (mismo corte que la "
                                    f"tarea pausada; estado/ultimo_movimiento están 100% nulos, "
                                    f"no sirven de filtro)",
        "n_universo_vivo": n_vivo,
        "n_con_tema": n_con_tema, "n_sin_tema": n_vivo - n_con_tema,
        "fraccion_sin_tema": round(frac_sin_tema, 4),
        "descuento_AUX_entre_clasificados_vivo": round(frac_aux, 4) if frac_aux is not None else None,
        "split_votado_no_votado": {
            "n_votado": n_votado, "n_votado_con_tema": n_votado_con_tema,
            "n_no_votado": n_no_votado, "n_no_votado_con_tema": n_no_votado_con_tema,
        },
        "cota_superior_mejora_brier_lado_votado": cota_brier,
        "costo": costo,
        "UMBRAL_conviene": 0.40, "UMBRAL_zona_gris_min": 0.15,
        "VEREDICTO": veredicto,
    }

    print("\n" + json.dumps(reporte, indent=1, ensure_ascii=False))
    print(f"\n=== VEREDICTO PRUEBA 3: {veredicto} ===")

    out = REPO / "evaluacion/baseline/outputs/prueba3_cobertura_universo_vivo_2026-09-17.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
