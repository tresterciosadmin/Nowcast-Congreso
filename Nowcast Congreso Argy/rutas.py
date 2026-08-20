# -*- coding: utf-8 -*-
"""Un solo lugar donde dice DONDE esta cada cosa que cruza de un modulo a otro.

## Por que existe

Antes de esto, la raiz del repo se recalculaba **47 veces en 41 archivos** con
`Path(__file__).resolve().parents[3]`, contando niveles de carpeta a mano. Mover
un archivo de profundidad hacia que apuntara en silencio a otro lado — y en este
proyecto **los errores de datos no dan error**: llegan como una columna vacia o
un parquet que "no existe todavia".

Ademas, el grafo de conexiones entre carpetas no estaba escrito en ningun lado:
habia que reconstruirlo grepeando literales de ruta. Este archivo ES ese grafo.

## Que va aca y que NO

- **SI:** todo artefacto que un modulo produce y OTRO consume. Es el contrato
  entre modulos hecho ruta.
- **NO:** rutas internas de un modulo (`parents[1]/"data"`, sus temporales, sus
  caches). Eso es asunto del modulo y no le interesa a nadie mas.

## Como se usa

Estas cinco lineas, iguales en todos lados. **No llevan `parents[3]`**: buscan la
raiz hacia arriba hasta encontrar este archivo, asi que siguen funcionando si el
modulo cambia de profundidad — que es justo lo que rompia antes.

    import sys
    from pathlib import Path
    sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                                if (d / "rutas.py").is_file())))
    from rutas import CANONICA_CLEAN, PROYECTOS_DB

Las variables de entorno que ya existian siguen mandando: `CANON`, `CLEAN`,
`EXP_CLEAN`, `PROYECTOS_DB`, `OUT`... Este archivo solo cambia el DEFAULT.

## Reglas

1. **Nada se agrega aca sin agregarlo tambien al modulo que lo produce.** Una
   ruta declarada que nadie escribe es peor que ninguna.
2. `tests/test_rutas.py` verifica dos cosas: que lo declarado como versionado
   exista en disco, y que **no haya rutas entre modulos hardcodeadas en el
   codigo que no figuren aca**. Si agregas un artefacto nuevo y no lo declaras,
   ese test te avisa.
3. Lo que se GENERA (parquets pesados, la base, los outputs) se marca en
   `GENERADOS`: el test no exige que exista, pero si que este declarado.

Creado 2026-08-20. Ver ESTADO-DEL-PROYECTO.md y el ADR correspondiente.
"""
from __future__ import annotations

import os
from pathlib import Path

# La raiz del PROYECTO (`Nowcast Congreso Argy/`). Ojo: la raiz GIT esta un nivel
# mas arriba — ahi viven `.github/workflows/` y `.git/`.
RAIZ = Path(__file__).resolve().parent
RAIZ_GIT = RAIZ.parent


def _env(var: str, default: Path) -> Path:
    """Respeta la variable de entorno si esta seteada. Los modulos ya la usan."""
    v = os.environ.get(var)
    return Path(v) if v else default


# ─────────────────────────────────────────────── datos/ (capa 1: la base)

CANONICA = RAIZ / "datos" / "canonica"
CANONICA_CLEAN = _env("CANON", CANONICA / "data" / "clean")
CANONICA_ACTAS = CANONICA_CLEAN / "actas_canonico.parquet"
CANONICA_VOTOS = CANONICA_CLEAN / "votos_canonico.parquet"
CANONICA_VOTOS_RESUELTO = CANONICA_CLEAN / "votos_resuelto.parquet"

EXPEDIENTES_CLEAN = _env("EXP_CLEAN", RAIZ / "datos" / "expedientes" / "data" / "clean")
EXPEDIENTES_ACTA_EXP = EXPEDIENTES_CLEAN / "acta_expediente.parquet"

BOT_CLEAN = RAIZ / "datos" / "bot_recoleccion" / "data" / "clean"
BOT_TP_ENTRADAS = BOT_CLEAN / "tp_entradas.parquet"

PROYECTOS_DB = _env("PROYECTOS_DB", RAIZ / "datos" / "proyectos" / "data" / "proyectos.db")
PROYECTOS_CUARENTENA_DB = RAIZ / "datos" / "proyectos" / "data" / "cuarentena.db"
PROYECTOS_SCHEMA_SQL = RAIZ / "datos" / "proyectos" / "src" / "schema.sql"

PADRON_DIR = RAIZ / "datos" / "padron" / "data"
PADRON_DIPUTADOS = PADRON_DIR / "padron_diputados.csv"
PADRON_SENADO = PADRON_DIR / "padron_senado.csv"
PADRON_SENADO_HISTORICO = PADRON_DIR / "padron_senado_historico.csv"
PADRON_SENADO_LINAJE_MANUAL = PADRON_DIR / "senado_linaje_manual.csv"

SENADO_DATA = RAIZ / "datos" / "senado" / "data"
SENADO_PADRON_BLOQUES = SENADO_DATA / "padron_bloques_senado.csv"

MANUAL_2026_XLSX = RAIZ / "datos" / "manual_2026" / "Congreso_25-27.xlsx"

EXPORT_DATA = RAIZ / "datos" / "export" / "data"

# ─────────────────────────────────────────── variables/ (capa 2: las señales)

LEGISLADOR_DATA = RAIZ / "variables" / "legislador" / "data"

ASISTENCIA_OUT = RAIZ / "variables" / "asistencia_quorum" / "outputs"

PROYECTO_DATA = RAIZ / "variables" / "proyecto" / "data"
PROYECTO_FEATURES = PROYECTO_DATA / "features_proyecto.parquet"
PROYECTO_ORIGEN_POR_ACTA = PROYECTO_DATA / "origen_por_acta.parquet"
PROYECTO_TEMA_POR_ACTA = PROYECTO_DATA / "tema_por_acta.parquet"
PROYECTO_POSTURA_POR_ACTA = PROYECTO_DATA / "postura_gobierno_por_acta.parquet"
PROYECTO_ICG_MENSUAL = PROYECTO_DATA / "icg_mensual.csv"
PROYECTO_CURVA_CICLO = PROYECTO_DATA / "curva_ciclo_presidencial.csv"
PROYECTO_JEFES_BLOQUE = PROYECTO_DATA / "jefes_bloque.csv"

EMBUDO_OUT = RAIZ / "variables" / "embudo" / "outputs"
# Entrypoint publicado: lo invoca `datos/proyectos/src/verificar.py` como
# proceso (su contrato), no importando su codigo. Ver ese archivo.
EMBUDO_COHORTE_DOS_RUTAS = RAIZ / "variables" / "embudo" / "src" / "cohorte_dos_rutas.py"

# ──────────────────────────────────────────── modelo/ (capa 3: el pronostico)

VOTO_INDIVIDUAL_OUT = RAIZ / "modelo" / "voto_individual" / "outputs"
DISCIPLINA_INDIVIDUAL = VOTO_INDIVIDUAL_OUT / "disciplina_individual.csv"
DESVIOS_POR_VOTO = VOTO_INDIVIDUAL_OUT / "desvios_por_voto.parquet"

AGREGADOR_OUT = RAIZ / "modelo" / "agregador_institucional" / "outputs"
ENSEMBLE_OUT = RAIZ / "modelo" / "ensemble" / "outputs"

# ─────────────────────────────────────────────────── compartido y coordinacion

SCHEMAS = _env("SCHEMAS", RAIZ / "docs" / "schemas")
TAXONOMIAS = RAIZ / "docs" / "taxonomias"

COORDINACION = RAIZ / "coordinacion"
URGENTE = COORDINACION / "URGENTE.md"
ESTADO = COORDINACION / "ESTADO-DEL-PROYECTO.md"
EN_HUMANO = COORDINACION / "EN-HUMANO.md"
TABLERO = COORDINACION / "TABLERO.md"
DECISIONES = COORDINACION / "DECISIONES"

TABLERO_DATOS_JS = RAIZ / "tablero_datos.js"
TABLERO_CONTROL_HTML = RAIZ / "TABLERO-CONTROL.html"

# Semilla historica de un solo uso (ADR-0002). Material de terceros.
SEMILLA_DECADA_VOTADA_ZIP = (RAIZ / "Aportes sobre dataset congreso" /
                             "towlandia-master" / "public" / "DecadaVotadaCSV.zip")

WORKFLOWS = RAIZ_GIT / ".github" / "workflows"

# ─────────────────────────────────────────────────────────────────────────────
# Lo que se GENERA: el test no exige que exista (puede no haberse corrido aun,
# o estar fuera de git por peso). Lo que NO esta aca tiene que existir en disco.
GENERADOS = {
    "CANONICA_CLEAN", "CANONICA_ACTAS", "CANONICA_VOTOS", "CANONICA_VOTOS_RESUELTO",
    "EXPEDIENTES_CLEAN", "EXPEDIENTES_ACTA_EXP",
    "BOT_CLEAN", "BOT_TP_ENTRADAS",
    "PROYECTOS_DB", "PROYECTOS_CUARENTENA_DB",
    "PADRON_SENADO_HISTORICO",
    "EXPORT_DATA",
    "LEGISLADOR_DATA", "ASISTENCIA_OUT",
    "PROYECTO_FEATURES", "PROYECTO_ORIGEN_POR_ACTA", "PROYECTO_TEMA_POR_ACTA",
    "PROYECTO_POSTURA_POR_ACTA",
    "EMBUDO_OUT", "VOTO_INDIVIDUAL_OUT", "DISCIPLINA_INDIVIDUAL", "DESVIOS_POR_VOTO",
    "AGREGADOR_OUT", "ENSEMBLE_OUT",
    "MANUAL_2026_XLSX",            # lo mantiene Franco a mano, puede no estar en un clon
    "SEMILLA_DECADA_VOTADA_ZIP",   # material de terceros, no siempre presente
}


# Estas viven en la raiz GIT, un nivel arriba del proyecto. Cuando se mira solo
# la subcarpeta (el sandbox la monta asi), no se ven — y "no lo veo" no prueba
# que no exista: es el error que este repo ya cometio tres veces.
SOLO_EN_RAIZ_GIT = {"RAIZ_GIT", "WORKFLOWS"}


def inventario() -> dict[str, Path]:
    """Todas las rutas declaradas, {NOMBRE: Path}. Lo usa el test."""
    return {k: v for k, v in globals().items()
            if k.isupper() and isinstance(v, Path)}


if __name__ == "__main__":
    faltan = []
    for nombre, ruta in sorted(inventario().items()):
        estado = "OK " if ruta.exists() else ("gen" if nombre in GENERADOS else "NO ")
        if estado == "NO ":
            faltan.append(nombre)
        print(f"  {estado}  {nombre:32} {ruta.relative_to(RAIZ_GIT)}")
    print(f"\n  {len(inventario())} rutas declaradas · {len(faltan)} faltan en disco")
    if faltan:
        print("  faltan: " + ", ".join(faltan))
