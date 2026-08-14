"""Qué actas de votación corresponden a un PROYECTO DE LEY.

EL NORTE DEL MODELO (decisión de Valle, 2026-08-09)
---------------------------------------------------
Toda medición probabilística del tratamiento de un proyecto de ley se calcula
**sólo sobre actas de ley** — proyectos de ley y mensajes del Ejecutivo (que en
la práctica son proyectos de ley). Los tratados, pliegos, homenajes,
declaraciones y resoluciones se aprueban por consenso y NO informan la postura
política de ningún bloque: meterlos en el promedio lava justo la señal que
buscamos (el subconjunto DISPUTADO, donde están las bisagras).

Medido el 2026-08-09, share afirmativo del kirchnerismo en el Senado 2024-2026:
  - sobre TODO el temario: 55,8%  -> dirección sale AFIRMATIVO (degenerado)
  - sobre SÓLO leyes:      29,0%  -> NEGATIVO, que es la realidad
El mismo efecto en Diputados (53,7% -> 27,1%). No es un problema de una cámara:
es el filtro que faltaba, uniforme para las dos.

CÓMO SE SABE EL TIPO
    El enlace acta→expediente (`acta_expediente_senado.parquet`) da el
    `proyecto_id`, y el maestro `expedientes.parquet` da el `tipo`. Este módulo
    los cruza y devuelve el conjunto de `acta_id` que son de ley.

LÍMITE HONESTO
    El enlace cubre ~47% de las actas; de una acta NO enlazada no se sabe el
    tipo. `actas_de_ley` devuelve sólo las CONFIRMADAS de ley. Para el uso
    aguas abajo (calcular la postura de bloque) eso es lo correcto: mejor
    computar sobre 88 leyes seguras que ensuciar con 130 actas de tipo
    desconocido. La cobertura sube sola a medida que mejora el enlace.

Módulo: datos/expedientes · creado 2026-08-09 (reconstrucción por puertas)
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"

# Un proyecto de ley, en la tipología de HCDN. MENSAJE = mensaje del Ejecutivo,
# que en la práctica es un proyecto de ley (decisión de Valle).
TIPOS_LEY = ("LEY", "MENSAJE Y PROYECTO DE LEY", "MENSAJE")

# DESIGNACIONES / PLIEGOS / ACUERDOS del Senado (jueces, embajadores, cónsules,
# ascensos militares): NO son proyectos de ley aunque el maestro los tipee "LEY" o
# "MENSAJE" y el enlace los cuelgue de un expediente de ley. Fix 2026-08-13: 226
# actas de designación se contaban como ley (1.611 tipeadas "LEY"), y en el Senado
# el share afirmativo de esas se aprueba por consenso -> lava la señal, igual que
# tratados/pliegos. El patrón es ESTRICTO a propósito (alta precisión): se validó
# contra el maestro que NO toca Presupuesto, Consenso/Alivio Fiscal, convenios de
# doble imposición, la Ley Orgánica del Ministerio Público Fiscal, leyes de ascensos
# ni desafueros — sólo las designaciones nominales. Precisión > recall (el norte del
# módulo). Palabras sueltas como FISCAL/JUEZ/ASCENSO/DESIGNA NO alcanzan: están
# llenas de leyes reales; por eso cada rama exige el CONTEXTO de nombramiento.
_PATRON_DESIGNACION = re.compile(
    r"\bPLIEGO\b"
    r"|C[OÓ]NSUL(ES)?\s+HONORARIO"
    r"|DESEMPE[NÑ]AR\s+(SUS\s+|LAS\s+)?FUNCIONES\s+DE\s+C[OÓ]NSUL"
    r"|(PRESTAR|SOLICITA\w*|PRESTA|PEDIDO\s+DE)\s+(EL\s+|SU\s+)?ACUERDO"
    r"|ACUERDO\s+CONSTITUCIONAL"
    r"|ACUERDO\s+PARA\s+(DESIGNA|PROMOVER|NOMBRAR|EL\s+ASCENSO)",
    # NOTA: a propósito NO se incluye un "DESIGNA(CION) DE JUEZ/FISCAL/..." genérico.
    # Se probó y excluyó por error una LEY real ("PROCEDIMIENTO PARA LA DESIGNACION DE
    # JUECES SUBROGANTES" es una ley sobre el procedimiento, no un nombramiento). No se
    # puede separar por palabras "nombran a una persona" de "ley sobre nombramientos":
    # ante la duda, se conserva como ley (precisión > recall) y la auditoría lista lo
    # que se saca para el control humano.
    re.I)


def es_designacion(titulo) -> bool:
    """True si el título es una designación/pliego/acuerdo del Senado (NO ley).
    Guarda de faltantes con pd.isna() + str() (tolera None/NaN/pd.NA de cualquier
    backend de dtype: 'pasa en el sandbox no es pasa')."""
    if pd.isna(titulo):
        return False
    return bool(_PATRON_DESIGNACION.search(str(titulo)))


# Reporte auditable de lo que el filtro EXCLUYE (lo escribe __main__ en cada corrida).
# En la raíz del módulo (NO bajo data/, que suele estar gitignored) para que viaje y se revise.
AUDITORIA_MD = RAIZ / "datos" / "expedientes" / "AUDITORIA-designaciones-excluidas.md"


def _escribir_auditoria(excluidas: pd.DataFrame, destino: Path) -> None:
    """Escribe la lista, en castellano, de las designaciones que el filtro sacó del
    conjunto de ley — para que una persona la revise de un vistazo. Sin regex a la
    vista: sólo el título y si tiene votación (acta). Es el control humano del filtro."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoy = pd.Timestamp.today().date()
    con_acta = excluidas[excluidas["tiene_acta"]]
    lineas = [
        "# Designaciones/pliegos excluidos del conjunto de LEY",
        "",
        f"> Generado por `actas_ley.py` el {hoy}. Es el CONTROL HUMANO del filtro: "
        "acá está, en castellano, cada expediente que el filtro dejó de contar como ley "
        "por ser una designación/pliego/acuerdo del Senado (jueces, embajadores, cónsules, "
        "ascensos). **Si ves una LEY DE VERDAD en esta lista, el filtro se pasó de largo — avisá.**",
        "",
        f"- Total excluidos: **{len(excluidas)}** expedientes "
        f"(de los cuales **{len(con_acta)}** tienen votación registrada y por eso afectaban la señal).",
        "",
        "## Con votación (los que importan — revisá estos)",
        "",
    ]
    if len(con_acta):
        lineas += ["| tipo | título |", "|---|---|"]
        for _, r in con_acta.iterrows():
            tit = str(r["titulo"]).replace("|", "/")[:160]
            lineas.append(f"| {r['tipo']} | {tit} |")
    else:
        lineas.append("_(ninguno con votación en esta corrida)_")
    lineas += ["", "## Sin votación (contexto, no afectan la señal hoy)", "",
               f"_{len(excluidas) - len(con_acta)} expedientes de designación sin acta enlazada._", ""]
    destino.write_text("\n".join(lineas), encoding="utf-8")
    logger.info("auditoría de designaciones excluidas -> %s (%d con acta)", destino, len(con_acta))


def actas_de_ley(
    tipos: Iterable[str] = TIPOS_LEY,
    enlace_path: Optional[Path] = None,
    expedientes_path: Optional[Path] = None,
    auditar_a: Optional[Path] = None,
) -> set[str]:
    """Conjunto de `acta_id` cuyo expediente es de ley (LEY/MENSAJE).

    Sólo las CONFIRMADAS: una acta sin enlace no entra (no se sabe su tipo). Excluye
    designaciones/pliegos/acuerdos (ver `es_designacion`). Si `auditar_a` es una ruta,
    escribe ahí la lista revisable de lo que excluyó (por defecto NO, para no tener
    efectos de lado cuando la llaman como librería; `__main__` la pasa siempre)."""
    enl_p = Path(enlace_path or CLEAN / "acta_expediente_senado.parquet")
    exp_p = Path(expedientes_path or CLEAN / "expedientes.parquet")
    for p, q in ((enl_p, "el enlace acta→expediente"), (exp_p, "el maestro de expedientes")):
        if not p.exists():
            raise FileNotFoundError(
                f"falta {q}: {p}\n  corré datos/expedientes/src/enlace_senado.py "
                "y datos/expedientes/src/ingesta_ckan.py")

    enl = pd.read_parquet(enl_p, columns=["acta_id", "proyecto_id"]).dropna(subset=["proyecto_id"])
    exp = pd.read_parquet(exp_p, columns=["proyecto_id", "tipo", "titulo"])
    tset = {str(t).upper() for t in tipos}
    es_ley_tipo = exp["tipo"].astype(str).str.upper().isin(tset)
    # excluir designaciones/pliegos/acuerdos aunque estén tipeados LEY/MENSAJE
    es_desig = exp["titulo"].map(es_designacion)
    ley_pid = set(exp.loc[es_ley_tipo & ~es_desig, "proyecto_id"])
    n_excl = int((es_ley_tipo & es_desig).sum())
    actas = set(enl.loc[enl["proyecto_id"].isin(ley_pid), "acta_id"])
    logger.info("actas de ley: %d (de %d enlazadas); %d expedientes de designación/pliego excluidos",
                len(actas), enl["acta_id"].nunique(), n_excl)

    if auditar_a is not None:
        pid_con_acta = set(enl["proyecto_id"])
        excl = exp.loc[es_ley_tipo & es_desig, ["proyecto_id", "tipo", "titulo"]].copy()
        excl["tiene_acta"] = excl["proyecto_id"].isin(pid_con_acta)
        _escribir_auditoria(excl, Path(auditar_a))

    return actas


def filtrar_votos_a_ley(votos: pd.DataFrame, actas_ley: Optional[set[str]] = None,
                        **kwargs) -> pd.DataFrame:
    """Deja en `votos` sólo las filas de actas de ley. Si `actas_ley` es None,
    lo calcula. No toca `votos` si el filtro dejaría el DataFrame vacío (se
    prefiere el comportamiento viejo antes que una serie sin datos: se avisa)."""
    if "acta_id" not in votos.columns:
        raise KeyError(f"votos sin columna 'acta_id'; hay {list(votos.columns)}")
    if actas_ley is None:
        actas_ley = actas_de_ley(**kwargs)
    filtrado = votos[votos["acta_id"].isin(actas_ley)]
    if filtrado.empty:
        logger.warning("el filtro de ley deja 0 votos; devuelvo los votos sin filtrar "
                       "(revisá la cobertura del enlace)")
        return votos
    logger.info("filtro de ley: %d de %d votos quedan (%.1f%%)",
                len(filtrado), len(votos), 100 * len(filtrado) / len(votos))
    return filtrado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = actas_de_ley(auditar_a=AUDITORIA_MD)
    print(f"actas de ley (LEY/MENSAJE): {len(s)}")
    print(f"lista revisable de lo excluido -> {AUDITORIA_MD}")
