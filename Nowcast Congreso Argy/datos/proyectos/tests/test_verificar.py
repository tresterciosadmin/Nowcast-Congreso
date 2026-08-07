"""Prueba que el CONTROL agarra los bugs — no que la base este bien hoy.

Un control que nunca se dispara no sirve de nada. Estos tests **rompen la base a
proposito**, cada vez de la forma exacta en que se rompio de verdad el 07-08, y
exigen que el control lo detecte. Si alguno pasa a estar en verde con la base
rota, el control dejo de proteger y hay que arreglarlo.

Corren sobre una COPIA en disco local; no tocan `proyectos.db`.
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import verificar as V  # noqa: E402
import upsert_bot as U  # noqa: E402


@pytest.fixture
def base_rota(monkeypatch):
    """Devuelve (conexion, aplicar_dano) sobre una copia descartable."""
    if not V.DB.exists():
        pytest.skip("no existe proyectos.db; corre migrar_ckan.py primero")
    tmp = Path(tempfile.mkdtemp()) / "copia.db"
    shutil.copyfile(V.DB, tmp)
    monkeypatch.setattr(V, "DB", tmp)

    def romper(sql: str) -> None:
        con = sqlite3.connect(str(tmp))
        con.execute(sql)
        con.commit()
        con.close()

    return romper


def _falla(nombre_parcial: str) -> bool:
    """Corre los controles de base y dice si el que nos importa quedo en rojo."""
    c = V.Control()
    V.controles_base(c)
    return any((not ok) and nombre_parcial in nombre for ok, nombre, _ in c.filas)


# ─────────────────────────────────────────────────────────────────────────────
# Los tres bugs reales del 07-08
# ─────────────────────────────────────────────────────────────────────────────
def test_agarra_el_tramite_borrado(base_rota):
    """BUG 1 — un upsert ciego con la ficha del bot borra el tramite de CKAN."""
    assert not _falla("tramite de CKAN"), "la base deberia estar sana ANTES del daño"
    base_rota("DELETE FROM proyecto_tramite WHERE rowid % 100 = 0")
    assert _falla("tramite de CKAN"), "🔴 el control NO detecto el trámite borrado"


def test_agarra_los_giros_pisados(base_rota):
    """BUG 2 — el bot pisando el giro ACUMULADO con el giro AL INGRESAR."""
    base_rota("DELETE FROM proyecto_giros WHERE rowid % 200 = 0")
    assert _falla("giros acumulados"), "🔴 el control NO detecto los giros perdidos"


def test_agarra_proyectos_sin_tipo(base_rota):
    """BUG 3 — sin `tipo` el proyecto es invisible para la cohorte de LEY."""
    base_rota("UPDATE proyectos SET tipo = NULL WHERE rowid % 500 = 0")
    assert _falla("`tipo`"), "🔴 el control NO detecto los proyectos sin tipo"


def test_agarra_la_llave_colapsada(base_rota):
    """BUG 4 — el +1 en vez de +671: la llave del embudo repitiendose."""
    base_rota("UPDATE proyectos SET proyecto_id = 'HCDN000001'"
              " WHERE proyecto_id IS NOT NULL AND rowid % 1000 = 0")
    assert _falla("llave del embudo"), "🔴 el control NO detecto la llave duplicada"


def test_agarra_los_cofirmantes_perdidos(base_rota):
    """BUG 5 — el orden inverso del merge borra los cofirmantes."""
    base_rota("DELETE FROM proyecto_autores WHERE orden > 0")
    assert _falla("cofirmantes"), "🔴 el control NO detecto la perdida de cofirmantes"


def test_agarra_giros_huerfanos(base_rota):
    base_rota("INSERT INTO proyecto_giros (denominador, comision)"
              " VALUES ('NO-EXISTE-9999', 'COMISION FANTASMA')")
    assert _falla("huerfanos"), "🔴 el control NO detecto el giro huerfano"


# ─────────────────────────────────────────────────────────────────────────────
# El descarte silencioso en la INGESTA (el de los 34 del Ejecutivo)
# ─────────────────────────────────────────────────────────────────────────────
def test_el_parser_del_senado_reconoce_al_ejecutivo():
    """Los `PE-` son los de mayor peso del modelo. No pueden caerse."""
    assert U.denom_dae("PE-8/26-PL") == "0008-PE-2026"
    assert U.denom_dae("S-2/26-PD") == "0002-S-2026"
    assert U.denom_dae("CD-5/26-PL") == "0005-CD-2026"


def test_un_expediente_ilegible_VA_A_CUARENTENA_y_la_carga_sigue(monkeypatch, tmp_path):
    """Decisión de Valle: lo dudoso NO frena la carga, va a una base aparte.

    El primer intento hacía `SystemExit` ante cualquier fila rara. Está mal para
    este proyecto: el bot corre solo todos los días y un refresco trae 300+
    proyectos. Frenar todo por una fila rara es el mismo error que el workflow ya
    había corregido con `continue-on-error`.
    """
    import pandas as pd
    import cuarentena as C

    C.DB = tmp_path / "cuarentena.db"
    carpeta = tmp_path / "clean"
    carpeta.mkdir()
    n_ok, n_roto = 19, 1
    pd.DataFrame({
        "expediente": [f"S-{i}/26-PL" for i in range(n_ok)] + ["FORMATO-RARO"],
        "fecha_mesa": ["2026-01-01"] * 20, "giros": ["DE SALUD -"] * 20,
        "extracto": ["X: PROYECTO DE LEY"] * 20, "expediente_url": [None] * 20,
        "dae_numero": range(20), "dae_anio": [26] * 20, "texto_url": [None] * 20,
    }).to_parquet(carpeta / "dae_entradas.parquet")
    monkeypatch.setattr(U, "BOT", carpeta)

    fichas = U.fichas_dae()
    assert len(fichas) == n_ok, "las filas buenas TIENEN que entrar igual"
    assert sum(f[2] for f in C.resumen()) == n_roto, "la rara tiene que quedar apartada"


def test_una_AVALANCHA_de_filas_raras_SI_frena(monkeypatch, tmp_path):
    """Una fila rara es normal. Muchas juntas = la fuente cambió de formato."""
    import pandas as pd
    import cuarentena as C

    C.DB = tmp_path / "cuarentena.db"
    carpeta = tmp_path / "clean"
    carpeta.mkdir()
    n_ok, n_roto = 85, 15          # 15% — muy por encima del 5% tolerado
    pd.DataFrame({
        "expediente": [f"S-{i}/26-PL" for i in range(n_ok)] + [f"ROTO{i}" for i in range(n_roto)],
        "fecha_mesa": ["2026-01-01"] * 100, "giros": ["DE SALUD -"] * 100,
        "extracto": ["X: PROYECTO DE LEY"] * 100, "expediente_url": [None] * 100,
        "dae_numero": range(100), "dae_anio": [26] * 100, "texto_url": [None] * 100,
    }).to_parquet(carpeta / "dae_entradas.parquet")
    monkeypatch.setattr(U, "BOT", carpeta)

    with pytest.raises(C.Avalancha, match="cambió de formato"):
        U.fichas_dae()


def test_el_piso_absoluto_evita_frenar_una_tanda_chica(monkeypatch, tmp_path):
    """Salió de probarlo: con sólo el % una tanda chica frena de más.

    El bot diario puede traer 20 expedientes; uno raro ya es 5%. Un cron que
    aborta por una fila rara vuelve al problema de origen.
    """
    import pandas as pd
    import cuarentena as C
    assert C.MINIMO_ABSOLUTO >= 5, "el piso no puede ser tan bajo que no proteja"

    C.DB = tmp_path / "cuarentena.db"
    carpeta = tmp_path / "clean"
    carpeta.mkdir()
    pd.DataFrame({                       # 2 de 10 = 20%, pero son sólo 2 filas
        "expediente": [f"S-{i}/26-PL" for i in range(8)] + ["ROTO1", "ROTO2"],
        "fecha_mesa": ["2026-01-01"] * 10, "giros": ["DE SALUD -"] * 10,
        "extracto": ["X: PROYECTO DE LEY"] * 10, "expediente_url": [None] * 10,
        "dae_numero": range(10), "dae_anio": [26] * 10, "texto_url": [None] * 10,
    }).to_parquet(carpeta / "dae_entradas.parquet")
    monkeypatch.setattr(U, "BOT", carpeta)

    assert len(U.fichas_dae()) == 8, "no puede frenar por 2 filas raras"
