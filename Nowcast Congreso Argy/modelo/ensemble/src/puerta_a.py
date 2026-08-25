"""Puerta A / Puerta C — el CARÁCTER OBSERVADO del dictamen como condicionante.

Contrato y decisiones: `modelo/ensemble/PUERTA-D.md`, enmienda del 2026-08-22.

QUÉ ES, EN UNA FRASE
    A y C NO son probabilidades. Son el carácter del trabajo en comisión —quién
    firmó el dictamen, si hubo disidencias, de qué bloques son los firmantes—
    leído de los PDF de la Orden del Día. Un HECHO. Este módulo lo lee y lo
    convierte en un condicionante de la VOTACIÓN de esa cámara (A sobre B,
    C sobre D), nunca en un factor que multiplique el número.

    P(sanción) = [A observada] · P(B | carácter de origen)
               · [C observada] · P(D | carácter de la revisora)

POR QUÉ NO ES UNA PROBABILIDAD (decisión de Valle 2026-08-20, ratificada el 22-08)
    Que la comisión trate un proyecto —o que la revisora lo trate antes de que
    caduque— es agenda política: se define en labor parlamentaria a puertas
    cerradas y no hay estadística que la capture. El nowcast dejó de estimarla.
    Lo que sí se puede leer es el RESULTADO: el dictamen y su carácter.

LOS TRES ESTADOS, Y EL TERCERO NO COLAPSA AL SEGUNDO
    con_caracter : hay dictamen y lo leímos.
    sin_dictamen : a la fecha de corte no hay dictamen.
    sin_dato     : puede haberlo y no saberlo — la Orden del Día todavía no se
                   publicó (mediana de 224 días entre presentación y OD), o el
                   PDF existe y no se pudo leer, o es de un sistema de comisiones
                   cuyo empalme no está resuelto.
    «Sin dato» y «sin dictamen» son OPUESTOS. Colapsarlos es afirmar que no hay
    dictamen cuando lo que pasa es que no miramos.

EL FALLBACK NO ES UN `if`
    En `sin_dato` no se anula nada ni se frena la cadena: el condicionante se
    ENCOGE A 0 y queda la estimación sin condicionar, que es exactamente lo que
    el sistema calcula hoy. Es el mismo mecanismo que `puerta_d.ajuste_paso_origen`
    —y se REUSA esa función, no se reimplementa—. Un solo modelo, con la versión
    no condicionada como límite.

POINT-IN-TIME, Y ESTO NO ES OPCIONAL
    `caracter_de(..., fecha_corte=)` sólo ve dictámenes con fecha <= corte. Un
    proyecto que consiguió dictamen en 2015 tiene que salir `sin_dictamen` o
    `sin_dato` si se lo evalúa en 2013. Sin esa guarda, el backtest se mira al
    espejo del futuro y da un skill que no existe.

ACUMULADOS (decisión de Valle 2026-08-22: observada para todos, CON MARCA)
    Una Orden del Día dictamina varios expedientes a la vez. `expedientes_resultados`
    trae la estructura oficial en `cabecera`: o dice literalmente "cabecera", o
    trae el proyecto_id del que encabeza. Los acumulados salen marcados
    (`es_cabecera`, `cabecera_id`) porque su destino está atado al texto unificado
    y al medir hay que poder separarlos: son casos correlacionados, no
    independientes.

PENDIENTE ANOTADO (Valle, 2026-08-22): el PESO DEL FIRMANTE
    Hoy todas las firmas valen igual. No es cierto: la firma de un jefe de bloque
    o de un presidente de comisión carga más señal que la de un legislador raso.
    Las dos fuentes ya existen en el repo y no hay que salir a buscarlas:
    `variables/proyecto/src/scrape_jefes_bloque.py` (snapshots fechados de jefes)
    y `datos/expedientes/data/clean/comisiones_autoridades.parquet` (46 presidentes
    con su cargo). Cuando se implemente, entra como peso en `n_firmantes` y en el
    delta, no como una puerta nueva.

Módulo: modelo/ensemble · creado 2026-08-22 (Tarea 1 — una sola formulación)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("puerta_a")

# Las rutas que CRUZAN de módulo salen de `rutas.py`, no de contar `parents[N]` a
# mano: ese conteo es lo que rompía en silencio cuando un archivo cambiaba de
# profundidad, y en este proyecto los errores de datos no dan error — llegan como
# un parquet que "no existe todavía". Ver ADR-0010.
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import (  # noqa: E402
    EXPEDIENTES_FIRMAS as FIRMAS_DIP,
    EXPEDIENTES_FIRMAS_SENADO as FIRMAS_SEN,
    EXPEDIENTES_RESULTADOS as RESULTADOS,
    RAIZ,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))  # para reusar puerta_d

ESTADOS = ("con_caracter", "sin_dictamen", "sin_dato")

# Ventana viva: por debajo de esta antigüedad NO se puede afirmar "sin dictamen".
# La mediana entre presentación y Orden del Día es de 224 días; el 94,3% cae dentro
# de los dos años. Afirmar la ausencia antes de eso es confundir "todavía no
# publicado" con "no existe".
DIAS_VENTANA_VIVA = 730

# Coeficientes del condicionante. TODOS EN CERO A PROPÓSITO: ver
# `estimar_delta_caracter` — el estimador está pendiente y el motivo está medido.
# Con estos valores `delta = 0` y el módulo corre en su límite no condicionado,
# que es idéntico a lo que el sistema calcula hoy. No es un placeholder olvidado:
# es el fallback del diseño, y está testeado como tal.
COEF_POR_DEFECTO: dict[str, float] = {
    "minoria": 0.0,          # existe un dictamen de minoría enfrentado
    "disidencia_parcial": 0.0,
    "disidencia_total": 0.0,
    "dos_comisiones": 0.0,   # firmado por dos comisiones = acuerdo más ancho
    "por_linaje": 0.0,       # por cada linaje distinto que acompaña
}


# --------------------------------------------------------------------------- #
# Carga                                                                        #
# --------------------------------------------------------------------------- #
def _texto(s) -> str:
    """Un faltante puede llegar como None, NaN o pd.NA según el backend de dtype."""
    return "" if pd.isna(s) else str(s).strip()


def _fecha(s):
    return pd.to_datetime(s, errors="coerce")


def _algun_si(col) -> bool:
    """¿Alguna fila dice que sí? Tolera None/NaN/pd.NA sin el downcast deprecado."""
    if col is None:
        return False
    return bool(col.map(lambda v: bool(v) if not pd.isna(v) else False).any())


def _fecha_dictamen(f: pd.DataFrame) -> pd.Series:
    """Fecha del dictamen, en cascada, porque las dos cámaras no traen lo mismo.

    Diputados publica `od_publicacion` (fecha real). **El Senado NO la tiene** —trae
    `fecha_impresion` en castellano y `od_anio`—, y sin fecha la guarda point-in-time
    no puede filtrar nada: un dictamen de 2020 se vería en un corte de 2012. Por eso
    la cascada, y por eso el último escalón es el 31 de diciembre:

      1. `od_publicacion` (Diputados).
      2. `fecha_impresion` parseada con `resolver_firmantes.fecha_es` — el MISMO
         parser que ya lee «17 de agosto de 2010» y «Agosto 17 de 2010». Se reusa.
      3. 31-dic de `od_anio`. Fecha TARDÍA a propósito: equivocarse hacia adelante
         hace perder señal (decimos «todavía no hay dictamen» cuando ya había);
         equivocarse hacia atrás sería FUGA DEL FUTURO. Sólo el segundo error es
         inaceptable.
    """
    fecha = (_fecha(f["od_publicacion"]) if "od_publicacion" in f
             else pd.Series(pd.NaT, index=f.index))
    if "fecha_impresion" in f:
        falta = fecha.isna()
        if falta.any():
            src = RAIZ / "datos" / "expedientes" / "src"
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
            try:
                from resolver_firmantes import fecha_es  # type: ignore
                fecha.loc[falta] = pd.to_datetime(
                    f.loc[falta, "fecha_impresion"].map(fecha_es), errors="coerce")
            except ImportError as e:
                logger.warning("no pude importar fecha_es de datos/expedientes (%s): "
                               "queda el año como única fecha", e)
    if "od_anio" in f:
        falta = fecha.isna()
        if falta.any():
            anio = pd.to_numeric(f.loc[falta, "od_anio"], errors="coerce")
            fecha.loc[falta] = pd.to_datetime(
                anio.dropna().astype(int).astype(str) + "-12-31", errors="coerce")
    return fecha


def _n_expedientes(col) -> int:
    """Cuántos expedientes dictamina la Orden del Día (el sumario los lista con `;`).

    Es la evidencia DIRECTA del acumulado. Ojo: la columna `cabecera` de
    `expedientes_resultados` NO sirve para esto —se verificó el 2026-08-22: nunca
    apunta a otro proyecto, siempre al propio o al literal "cabecera", así que es un
    flag con dos grafías y no una estructura de enlace.
    """
    if col is None:
        return 0
    n = 0
    for s in col.dropna().astype(str):
        n = max(n, len([x for x in s.split(";") if x.strip()]))
    return n


def cargar_caracter(firmas_dip=None, firmas_sen=None, resultados=None) -> pd.DataFrame:
    """Una fila por (proyecto_id, camara) con el carácter observado del dictamen.

    Lee los DOS contratos de `datos/expedientes` —Diputados y Senado— porque el
    circuito es bicameral: el mismo expediente puede tener dictamen en las dos.
    """
    partes = []
    for ruta, defecto in ((firmas_dip, FIRMAS_DIP), (firmas_sen, FIRMAS_SEN)):
        p = Path(ruta or defecto)
        if not p.exists():
            logger.warning("no encontré %s: esa cámara queda sin carácter observado", p)
            continue
        cols = ["proyecto_id", "camara", "parseo_ok", "dictamen_clase", "disidencia",
                "bloque_linaje", "legislador_id", "dos_comisiones", "od_publicacion",
                "origen_firmas", "expedientes_sumario", "fecha_impresion", "od_anio"]
        # se leen SOLO las columnas necesarias: el parquet de Diputados tiene 125.820
        # filas y traerlo entero para descartar 17 columnas es tiempo regalado.
        import pyarrow.parquet as pq
        presentes = set(pq.read_schema(p).names)
        # `od_publicacion` (Diputados) y `od_anio` (Senado) son una alternativa, no dos
        # requisitos: cada cámara trae la suya. Que falten LAS DOS sí es un problema,
        # porque deja al dictamen sin fecha y la guarda point-in-time sin qué filtrar.
        opcionales = {"od_publicacion", "od_anio"}
        faltan = [c for c in cols if c not in presentes and c not in opcionales]
        if not (opcionales & presentes) and "fecha_impresion" not in presentes:
            faltan.append("ninguna fecha (od_publicacion / od_anio / fecha_impresion)")
        if faltan:
            logger.warning("a %s le faltan columnas del contrato: %s", p.name, faltan)
        partes.append(pd.read_parquet(p, columns=[c for c in cols if c in presentes]))
    if not partes:
        raise FileNotFoundError(
            f"no hay ningún parquet de firmas ({FIRMAS_DIP}, {FIRMAS_SEN}): "
            "corré datos/expedientes/src/construir_firmas.py")
    f = pd.concat(partes, ignore_index=True)

    # Las Órdenes del Día que NO se pudieron enganchar a un expediente (4.675 filas
    # del Senado al 22-08-2026) no son el carácter de ningún proyecto: si se dejan,
    # un `proyecto_id` vacío las matchea TODAS y un proyecto hipotético termina
    # diciendo que tiene dictamen con 155 firmantes. Se van acá, una sola vez.
    antes = len(f)
    f = f[f["proyecto_id"].map(_texto) != ""].copy()
    if len(f) < antes:
        logger.info("descarté %d filas sin expediente enganchado (no son el carácter "
                    "de ningún proyecto)", antes - len(f))

    f["_firma"] = f["legislador_id"].map(_texto) != ""
    f["_fecha"] = _fecha_dictamen(f)

    filas = []
    for (pid, cam), g in f.groupby([f["proyecto_id"].map(_texto),
                                    f["camara"].map(_texto)], sort=False):
        firm = g[g["_firma"]]
        clases = set(firm["dictamen_clase"].map(_texto))
        dis = set(firm["disidencia"].map(_texto))
        filas.append({
            "proyecto_id": pid,
            "camara": cam,
            "leida": _algun_si(g.get("parseo_ok")),
            "n_firmantes": int(firm["legislador_id"].map(_texto).nunique()),
            "n_linajes": int(firm["bloque_linaje"].map(_texto).replace("", pd.NA)
                             .dropna().nunique()),
            "hay_minoria": "minoria" in clases,
            "hay_mayoria": "mayoria" in clases,
            "disidencia_parcial": "parcial" in dis or "sin_especificar" in dis,
            "disidencia_total": "total" in dis,
            "dos_comisiones": _algun_si(g.get("dos_comisiones")),
            "n_expedientes": _n_expedientes(g.get("expedientes_sumario")),
            "sin_ancla": (g["origen_firmas"].map(_texto) == "sin_ancla").any()
            if "origen_firmas" in g else False,
            "fecha_dictamen": g["_fecha"].min(),
        })
    tabla = pd.DataFrame(filas)

    # marca de ACUMULADO desde la estructura oficial (expedientes_resultados.cabecera)
    rp = Path(resultados or RESULTADOS)
    if rp.exists():
        r = pd.read_parquet(rp, columns=["proyecto_id", "cabecera"])
        r["proyecto_id"] = r["proyecto_id"].map(_texto)
        r["cabecera"] = r["cabecera"].map(_texto)
        r = r[r["cabecera"] != ""].drop_duplicates("proyecto_id")
        # `cabecera` se escribe de DOS formas para decir lo mismo: el literal
        # "cabecera" o el propio proyecto_id. Verificado el 2026-08-22 sobre las
        # 117.412 filas: NUNCA apunta a otro proyecto.
        cab = dict(zip(r["proyecto_id"], r["cabecera"]))
        tabla["es_cabecera"] = tabla["proyecto_id"].map(
            lambda p: cab.get(p, "") in ("cabecera", p))
    else:
        logger.warning("no encontré %s: no puedo marcar cuál encabeza su Orden del Día", rp)
        tabla["es_cabecera"] = False
    # ACUMULADO = la Orden del Día dictamina más de un expediente. Decisión de Valle
    # (2026-08-22): A queda observada para TODOS los acumulados, pero MARCADOS —
    # su destino está atado al texto unificado, así que al medir son casos
    # correlacionados y hay que poder separarlos.
    tabla["acumulado"] = tabla["n_expedientes"] > 1
    return tabla


# --------------------------------------------------------------------------- #
# El estado observado                                                          #
# --------------------------------------------------------------------------- #
def caracter_de(proyecto_id: str, camara: str, tabla: pd.DataFrame,
                fecha_corte=None, fecha_presentacion=None,
                dias_ventana_viva: int = DIAS_VENTANA_VIVA) -> dict:
    """El carácter observado de (proyecto, cámara) A LA FECHA DE CORTE.

    `fecha_corte` : nada posterior a esta fecha se puede mirar (point-in-time).
    `fecha_presentacion` : con ella se distingue «sin dictamen» de «sin dato» en la
        ventana viva. Sin ella, la ausencia NUNCA se afirma: sale `sin_dato`, que
        es la respuesta conservadora.
    """
    pid, cam = _texto(proyecto_id), _texto(camara).lower()
    corte = _fecha(fecha_corte) if fecha_corte is not None else None

    if not pid:
        # Un proyecto hipotético no tiene expediente contra el cual buscar dictamen.
        # No es "sin dictamen" (eso sería afirmar algo sobre un proyecto que no
        # existe): es sin dato, y el condicionante se encoge a 0.
        return {"proyecto_id": "", "camara": cam, "estado": "sin_dato",
                "motivo": "proyecto sin expediente (hipotético): no hay dictamen que buscar",
                "n_firmantes": 0, "n_linajes": 0, "hay_minoria": False,
                "hay_mayoria": False, "disidencia_parcial": False,
                "disidencia_total": False, "dos_comisiones": False, "sin_ancla": False,
                "es_cabecera": False, "acumulado": False, "n_expedientes": 0,
                "fecha_dictamen": None}

    sub = tabla[(tabla["proyecto_id"] == pid) & (tabla["camara"] == cam)]
    sin_fecha = False
    if corte is not None and not sub.empty:
        # Point-in-time. Un dictamen posterior al corte NO existe todavía. Y uno SIN
        # FECHA tampoco se puede dar por existente: dejarlo pasar es exactamente la
        # fuga que la guarda tiene que impedir. Sale `sin_dato`, no `con_caracter`.
        sin_fecha = bool(sub["fecha_dictamen"].isna().all())
        sub = sub[sub["fecha_dictamen"].notna() & (sub["fecha_dictamen"] <= corte)]

    base = {"proyecto_id": pid, "camara": cam, "estado": "sin_dictamen",
            "motivo": "", "n_firmantes": 0, "n_linajes": 0,
            "hay_minoria": False, "hay_mayoria": False,
            "disidencia_parcial": False, "disidencia_total": False,
            "dos_comisiones": False, "sin_ancla": False,
            "es_cabecera": False, "acumulado": False, "n_expedientes": 0,
            "fecha_dictamen": None}

    if sin_fecha:
        base["estado"] = "sin_dato"
        base["motivo"] = ("hay dictamen pero sin fecha utilizable: no se puede afirmar "
                          "que ya existía a la fecha de corte")
        return base

    if not sub.empty:
        fila = sub.iloc[0].to_dict()
        leida, n = bool(fila["leida"]), int(fila["n_firmantes"])
        base.update({k: fila[k] for k in
                     ("n_firmantes", "n_linajes", "hay_minoria", "hay_mayoria",
                      "disidencia_parcial", "disidencia_total", "dos_comisiones",
                      "sin_ancla", "es_cabecera", "acumulado", "n_expedientes")})
        base["fecha_dictamen"] = fila["fecha_dictamen"]
        if leida and n > 0:
            base["estado"] = "con_caracter"
            return base
        base["estado"] = "sin_dato"
        base["motivo"] = ("hay Orden del Día para este proyecto pero no se pudo leer "
                          "el bloque de firmas")
        return base

    # No aparece en el contrato de firmas. ¿Puedo afirmar que no hay dictamen?
    if fecha_presentacion is None:
        base["estado"] = "sin_dato"
        base["motivo"] = ("sin fecha de presentación no se puede distinguir «no hay "
                          "dictamen» de «todavía no se publicó»")
        return base
    fp, ref = _fecha(fecha_presentacion), (corte if corte is not None else pd.Timestamp.today())
    if pd.isna(fp):
        base["estado"] = "sin_dato"
        base["motivo"] = "fecha de presentación ilegible"
        return base
    if (ref - fp).days < dias_ventana_viva:
        base["estado"] = "sin_dato"
        base["motivo"] = (f"dentro de la ventana viva ({dias_ventana_viva} días): la "
                          "Orden del Día puede existir y no estar publicada todavía")
        return base
    base["motivo"] = (f"sin dictamen registrado y con más de {dias_ventana_viva} días "
                      "desde la presentación")
    return base


# --------------------------------------------------------------------------- #
# El condicionante                                                             #
# --------------------------------------------------------------------------- #
def delta_caracter(caracter: dict, coef: dict | None = None) -> tuple[float, float]:
    """(delta, factor_encogimiento) del carácter sobre la votación de su cámara.

    `delta` es un corrimiento en log-odds, igual que en la Puerta D. El factor de
    encogimiento vale 0 salvo que el carácter esté OBSERVADO: en `sin_dato` y en
    `sin_dictamen` el condicionante desaparece por encogimiento, no por un `if`.
    """
    c = dict(coef or COEF_POR_DEFECTO)
    if caracter.get("estado") != "con_caracter":
        return 0.0, 0.0
    d = 0.0
    if caracter.get("hay_minoria"):
        d += c.get("minoria", 0.0)
    if caracter.get("disidencia_parcial"):
        d += c.get("disidencia_parcial", 0.0)
    if caracter.get("disidencia_total"):
        d += c.get("disidencia_total", 0.0)
    if caracter.get("dos_comisiones"):
        d += c.get("dos_comisiones", 0.0)
    d += c.get("por_linaje", 0.0) * float(caracter.get("n_linajes", 0) or 0)
    return float(d), 1.0


def condicionar(p0: float, caracter: dict, coef: dict | None = None) -> dict:
    """Aplica el carácter sobre una P(mayoría) ya calculada (B o D).

    Reusa `puerta_d.ajuste_paso_origen`: es el MISMO mecanismo de logit + encogimiento
    que ya está probado. No se reimplementa.
    """
    from puerta_d import ajuste_paso_origen  # contrato del propio módulo

    delta, fe = delta_caracter(caracter, coef)
    p = ajuste_paso_origen(float(p0), delta, fe)
    return {
        "p": p,
        "p0": float(p0),
        "delta": delta,
        "factor_encogimiento": fe,
        "delta_aplicado": delta * fe,
        "estado": caracter.get("estado"),
        "motivo": caracter.get("motivo", ""),
        "condicionado": bool(delta * fe),
        "acumulado": bool(caracter.get("acumulado")),
    }


def estimar_delta_caracter(*args, **kwargs):
    """HOOK pendiente — y el motivo está MEDIDO, no supuesto.

    El delta no se puede ajustar contra «¿ganó la votación en su cámara?» porque
    esa etiqueta está DEGENERADA: de 1.898 proyectos de ley con resultado
    registrado en el recinto (medido el 2026-08-22 sobre
    `expedientes_resultados.parquet`), **2 son RECHAZADO**. Ajustar sobre eso es
    ajustar ruido. Es el mismo hallazgo que ya está escrito en la bitácora del
    13-08: el factor de mayoría, sin condicionar, da p>=0,99 en 33.284 de 37.341
    casos — la votación de piso casi siempre pasa, y no se equivoca.

    Las dos salidas que SÍ tienen varianza, para decidir con Valle:
      1. El MARGEN (afirmativos contra el umbral), no el binario. El simulador ya
         lo produce y el carácter debería estrecharlo cuando hay minoría o
         disidencias. Se mide contra las actas de `datos/canonica`.
      2. La cámara REVISORA, donde la mortandad sí es real (de lo que llega al
         recinto, ~54% termina en ley) — pero ahí hay que separar agenda de voto,
         y la agenda no se modela.

    Hasta que se decida, `COEF_POR_DEFECTO` deja delta en 0 y el módulo corre en su
    límite no condicionado. Es el fallback del diseño, no un olvido.
    """
    raise NotImplementedError(
        "estimar_delta_caracter pendiente: la etiqueta binaria del voto en origen "
        "está degenerada (2 RECHAZADO en 1.898 resultados). Ver el docstring: hay "
        "que elegir el margen o la revisora como objetivo, y eso lo decide Valle.")
