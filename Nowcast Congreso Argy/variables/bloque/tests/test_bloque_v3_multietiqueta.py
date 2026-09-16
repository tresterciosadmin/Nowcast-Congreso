"""Tests offline del v3 (combinar_temas: multietiqueta) de variables/bloque.

Parte A de coordinacion/PROMPT-MULTIETIQUETA.md. Sin datos reales ni red.
El caso que motiva todo esto (Ley Bases: un proyecto con varios temas
sustantivos a la vez) se prueba acá con votos sintéticos donde la dirección
DEPENDE de cuál tema se mira — si el proyector colapsara a una sola etiqueta,
alguno de estos tests lo detecta.

    python variables/bloque/tests/test_bloque_v3_multietiqueta.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import bloque as B  # noqa: E402


def _idx(esc):
    return {b["bloque"]: b for b in esc}


def _votos_dos_temas():
    """20 actas. OPO vota NEGATIVO en las 8 de tema ECON, AFIRMATIVO en las 12
    de tema OTRO. `cond` sólo tiene `tema_area` (primaria) — sirve para probar
    'primaria' y como caso base."""
    filas, cond = [], []
    base = pd.Timestamp("2020-01-01")
    for k in range(20):
        aid = f"a{k}"
        fecha = base + pd.Timedelta(days=k)
        tema = "ECON" if k < 8 else "OTRO"
        cond.append({"acta_id": aid, "tema_area": tema, "origen": "OPOSICION"})
        opo_dir = "NEGATIVO" if tema == "ECON" else "AFIRMATIVO"
        for L in range(3):
            filas.append(dict(acta_id=aid, fecha=fecha, camara="diputados",
                              bloque_linaje="OPO", legislador_id=f"opo{L}", conducta=opo_dir))
    return pd.DataFrame(filas), pd.DataFrame(cond)


def test_ponderada_con_un_tema_es_identica_a_primaria():
    """Con un solo tema de peso 1.0, 'ponderada' es la generalización de
    'primaria', no una rama aparte: tienen que dar EXACTAMENTE el mismo share."""
    votos, cond = _votos_dos_temas()
    primaria = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                        cond_por_acta=cond, padron_path="__no__"))
    ponderada = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                         combinar_temas="ponderada", temas=[("ECON", 1.0)],
                                         cond_por_acta=cond, padron_path="__no__"))
    assert primaria["OPO"]["_share_afirm"] == ponderada["OPO"]["_share_afirm"], \
        (primaria["OPO"], ponderada["OPO"])
    assert primaria["OPO"]["_n_cond"] == ponderada["OPO"]["_n_cond"] == 8
    print("OK ponderada con 1 tema (peso 1.0) == primaria, share=%.4f"
          % ponderada["OPO"]["_share_afirm"])


def test_union_usa_la_multietiqueta_completa_no_solo_la_primaria():
    """El caso Ley Bases: una acta cuya PRIMARIA es 'OTRO' pero cuya
    multietiqueta completa (todas_ids) incluye 'ECON' tiene que matchear bajo
    'union' target=ECON aunque NO matchee bajo 'primaria'. Si esto fallara,
    'union' estaría leyendo sólo tema_area y el colapso seguiría intacto."""
    votos, cond = _votos_dos_temas()
    # las 12 actas "OTRO": le agrego ECON a la multietiqueta de 4 de ellas
    # (siguen siendo afirmativas: OPO votó AFIRMATIVO en esas 12 actas)
    cond = cond.copy()
    cond["todas_ids"] = cond.apply(
        lambda r: f"{r['tema_area']}.SUB;ECON.OTRA" if r["acta_id"] in {"a8", "a9", "a10", "a11"}
        else f"{r['tema_area']}.SUB", axis=1)

    primaria = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                        cond_por_acta=cond, padron_path="__no__"))
    union = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                     combinar_temas="union", temas=["ECON"],
                                     cond_por_acta=cond, padron_path="__no__"))
    # primaria: sólo las 8 actas cuya PRIMARIA literal es ECON
    assert primaria["OPO"]["_n_cond"] == 8, primaria["OPO"]
    # union: las 8 + las 4 "OTRO" que también llevan ECON en todas_ids -> 12
    assert union["OPO"]["_n_cond"] == 12, union["OPO"]
    print("OK union ve %d actas (primaria sólo %d) al usar todas_ids"
          % (union["OPO"]["_n_cond"], primaria["OPO"]["_n_cond"]))


def test_union_pool_de_dos_temas_opuestos():
    """Bajo 'union' con dos temas objetivo, la ventana condicionada es la
    UNIÓN de ambos: más muestra que cualquiera de los dos solos."""
    votos, cond = _votos_dos_temas()
    solo_econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                         combinar_temas="union", temas=["ECON"],
                                         cond_por_acta=cond, padron_path="__no__"))
    union2 = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                      combinar_temas="union", temas=["ECON", "OTRO"],
                                      cond_por_acta=cond, padron_path="__no__"))
    assert solo_econ["OPO"]["_n_cond"] == 8
    assert union2["OPO"]["_n_cond"] == 20, "union de ECON+OTRO debe cubrir las 20 actas"
    print("OK union(ECON,OTRO) junta las 20 actas (solo ECON: 8)")


def test_ponderada_promedia_shares_ya_encogidos():
    """Ponderada calcula el share de CADA tema por separado (encogido) y
    combina por confianza. Con pesos 3:1 a favor de ECON (negativo), el
    resultado tiene que quedar más cerca del share de ECON que del de OTRO."""
    votos, cond = _votos_dos_temas()
    econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    otro = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="OTRO",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    pond = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                    combinar_temas="ponderada", temas=[("ECON", 0.75), ("OTRO", 0.25)],
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    esperado = 0.75 * econ + 0.25 * otro
    assert abs(pond - esperado) < 1e-9, (pond, esperado)
    assert econ < pond < otro, "el promedio ponderado tiene que caer ENTRE los dos extremos"
    print("OK ponderada(0.75 ECON + 0.25 OTRO) = %.4f == 0.75*%.4f + 0.25*%.4f"
          % (pond, econ, otro))


def test_peor_tema_toma_el_minimo_no_el_promedio():
    """'peor_tema' (PASO 1 extendido, 16-09): el tema donde el bloque está MÁS
    EN CONTRA manda. Con ECON (share bajo, opuesto) y OTRO (share alto,
    favorable), el resultado tiene que ser el share de ECON, no un promedio."""
    votos, cond = _votos_dos_temas()
    econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    otro = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="OTRO",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    peor = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                    combinar_temas="peor_tema", temas=["ECON", "OTRO"],
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    assert econ < otro, "sanity: ECON es el tema opuesto en este fixture"
    assert peor == econ, f"peor_tema tiene que dar EXACTAMENTE el mínimo (ECON={econ}): {peor}"
    assert peor != (econ + otro) / 2, "y no puede coincidir con el promedio simple (salvo por azar)"
    print("OK peor_tema(ECON,OTRO) = min(%.4f, %.4f) = %.4f" % (econ, otro, peor))


def test_peor_tema_con_un_tema_es_identico_a_primaria():
    votos, cond = _votos_dos_temas()
    primaria = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                        cond_por_acta=cond, padron_path="__no__"))
    peor = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                    combinar_temas="peor_tema", temas=["ECON"],
                                    cond_por_acta=cond, padron_path="__no__"))
    assert primaria["OPO"]["_share_afirm"] == peor["OPO"]["_share_afirm"], \
        "con un solo tema, 'el peor' es el único -> igual a primaria"
    print("OK peor_tema con 1 tema == primaria")


def test_ponderada_logit_con_un_tema_es_identica_a_primaria():
    """Igual que 'ponderada': con un solo tema de peso 1.0, logit y sigmoid son
    inversas exactas, así que 'ponderada_logit' también da EXACTAMENTE
    'primaria' — no es una rama aparte, es la generalización en logit."""
    votos, cond = _votos_dos_temas()
    primaria = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                        cond_por_acta=cond, padron_path="__no__"))
    plogit = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                      combinar_temas="ponderada_logit", temas=[("ECON", 1.0)],
                                      cond_por_acta=cond, padron_path="__no__"))
    assert abs(primaria["OPO"]["_share_afirm"] - plogit["OPO"]["_share_afirm"]) < 1e-9, \
        (primaria["OPO"], plogit["OPO"])
    print("OK ponderada_logit con 1 tema (peso 1.0) == primaria, share=%.4f"
          % plogit["OPO"]["_share_afirm"])


def test_ponderada_logit_no_se_aplasta_hacia_el_centro_como_la_de_probabilidad():
    """FASE 0 v2, crítica #2 (PROMPT-MULTITEMA-V2.md): promediar en PROBABILIDAD
    comprime hacia 0,5 y aplasta los temas extremos. Con ECON muy en contra
    (share bajo) y OTRO muy a favor (share alto), el promedio en LOGIT tiene
    que quedar MÁS CERCA del extremo dominante que el promedio en probabilidad
    — no exactamente entre los dos como 'ponderada' clásica."""
    votos, cond = _votos_dos_temas()
    econ = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="ECON",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    otro = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", tema="OTRO",
                                    cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    pond_prob = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                         combinar_temas="ponderada", temas=[("ECON", 0.5), ("OTRO", 0.5)],
                                         cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    pond_logit = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                          combinar_temas="ponderada_logit", temas=[("ECON", 0.5), ("OTRO", 0.5)],
                                          cond_por_acta=cond, padron_path="__no__"))["OPO"]["_share_afirm"]
    assert abs(pond_prob - (econ + otro) / 2) < 1e-9, "sanity: 'ponderada' es el promedio simple"
    assert pond_logit != pond_prob, "logit y probabilidad tienen que dar resultados DISTINTOS"
    print("OK ponderada_logit(%.4f) != ponderada en probabilidad(%.4f) -- econ=%.4f otro=%.4f"
          % (pond_logit, pond_prob, econ, otro))


def test_ponderada_sin_match_en_ningun_tema_cae_a_incondicional():
    votos, cond = _votos_dos_temas()
    v1 = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados", padron_path="__no__"))
    xx = _idx(B.proyectar_postura(votos, "2020-06-01", "diputados",
                                  combinar_temas="ponderada", temas=["NOEXISTE1", "NOEXISTE2"],
                                  cond_por_acta=cond, padron_path="__no__"))
    assert xx["OPO"]["_share_afirm"] == v1["OPO"]["_share_afirm"]
    assert xx["OPO"]["_cond"] is None
    print("OK ponderada sin match en ningún tema cae a incondicional sin romper")


def test_combinar_temas_invalido_rompe_claro():
    votos, cond = _votos_dos_temas()
    try:
        B.proyectar_postura(votos, "2020-06-01", "diputados", combinar_temas="mediana",
                            temas=["ECON"], cond_por_acta=cond, padron_path="__no__")
        assert False, "combinar_temas inválido debía levantar ValueError"
    except ValueError:
        pass
    print("OK combinar_temas inválido levanta ValueError claro")


def test_no_primaria_sin_temas_rompe_claro():
    votos, cond = _votos_dos_temas()
    try:
        B.proyectar_postura(votos, "2020-06-01", "diputados", combinar_temas="union",
                            cond_por_acta=cond, padron_path="__no__")
        assert False, "'union' sin tema/temas debía levantar ValueError"
    except ValueError:
        pass
    print("OK combinar_temas='union' sin tema/temas levanta ValueError claro")


def test_normalizar_temas_objetivo_acepta_formas_variadas():
    from bloque import _normalizar_temas_objetivo as norm
    assert norm(["ECON", "TRAB"]) == [("ECON", 1.0), ("TRAB", 1.0)]
    assert norm({"ECON": 0.9, "AUX": 0.5}) == [("ECON", 0.9)], "AUX se descarta"
    assert norm([("econ", 0.7), ("trab", 0)]) == [("ECON", 0.7)], "peso <=0 se descarta"
    assert norm(None) == []
    assert norm("econ") == [("ECON", 1.0)]
    print("OK _normalizar_temas_objetivo cubre lista/dict/tuplas/string/None")


if __name__ == "__main__":
    test_ponderada_con_un_tema_es_identica_a_primaria()
    test_union_usa_la_multietiqueta_completa_no_solo_la_primaria()
    test_union_pool_de_dos_temas_opuestos()
    test_ponderada_promedia_shares_ya_encogidos()
    test_peor_tema_toma_el_minimo_no_el_promedio()
    test_peor_tema_con_un_tema_es_identico_a_primaria()
    test_ponderada_logit_con_un_tema_es_identica_a_primaria()
    test_ponderada_logit_no_se_aplasta_hacia_el_centro_como_la_de_probabilidad()
    test_ponderada_sin_match_en_ningun_tema_cae_a_incondicional()
    test_combinar_temas_invalido_rompe_claro()
    test_no_primaria_sin_temas_rompe_claro()
    test_normalizar_temas_objetivo_acepta_formas_variadas()
    print("\n== 12 chequeos v3 (multietiqueta) OK ==")
