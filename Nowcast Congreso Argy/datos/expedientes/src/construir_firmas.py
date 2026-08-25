# -*- coding: utf-8 -*-
"""Arma el contrato de salida: los FIRMANTES de cada dictamen de comisión.

Junta las tres piezas: el caché de PDF que bajó `ingesta_od.py`, el parseo de
`parser_od.py` y el emparejamiento contra el padrón de `resolver_firmantes.py`.

## Las dos salidas, y por qué son dos

**`dictamenes_firmas.parquet`** — una fila por **(proyecto, cámara, dictamen,
firmante)**. Es el dato nuevo: quién firmó, en qué carácter, y con qué bloque a
esa fecha.

**`dictamenes_comisiones.parquet`** — una fila por **(proyecto, cámara, comisión,
dictamen)**. Es el índice que pidió el contrato.

Van separadas por una razón de honestidad, no de comodidad. Un dictamen conjunto
de dos comisiones trae **una sola lista de firmas**: el PDF no dice cuál de las
dos comisiones integra cada diputado (lo marca con un asterisco sólo para quienes
integran las dos, y eso no lo parseamos). Meter las dos cosas en una tabla
obligaría a repetir cada firmante una vez por comisión, **inventando una
atribución que el documento no da**. Con dos tablas, el que necesita el cruce lo
hace y sabe lo que está haciendo.

## Cómo se engancha un dictamen con su proyecto

Una Orden del Día puede tratar varios expedientes. Cuando el expediente del
sumario del PDF matchea el `exp_diputados` de nuestra base, el enlace es directo
(`enlace=expediente`). Cuando no, el dictamen se atribuye a **todos** los
proyectos que nuestra base asocia a esa OD (`enlace=orden_del_dia`), que es más
flojo y por eso queda dicho en una columna en vez de escondido.

## Lo que NO se descarta

Un PDF que no se pudo bajar (404) o que el parser no entendió **entra igual** con
`parseo_ok=False` y su `motivo`. Si desapareciera, la cobertura se vería mejor de
lo que es.

## Uso (corrida larga: PowerShell)

    python datos/expedientes/src/construir_firmas.py
    python datos/expedientes/src/construir_firmas.py --limite 50    # prueba corta

Necesita `pdfminer.six`. Tarda ~1 s por PDF.
"""
from __future__ import annotations

import argparse
import collections
import logging
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve()
_RAIZ = next(d for d in _HERE.parents if (d / "rutas.py").is_file())
sys.path.insert(0, str(_RAIZ))
sys.path.insert(0, str(_HERE.parent))
from rutas import EXPEDIENTES_CLEAN  # noqa: E402

from ingesta_od import cache_dir  # noqa: E402
from ingesta_od_senado import cache_dir as cache_dir_senado  # noqa: E402
from parser_od import a_filas, parsear, texto_de_pdf  # noqa: E402
from resolver_firmantes import cargar_padron, fecha_es, resolver  # noqa: E402

logger = logging.getLogger("expedientes.firmas")

SALIDA_FIRMAS = EXPEDIENTES_CLEAN / "dictamenes_firmas.parquet"
SALIDA_COMISIONES = EXPEDIENTES_CLEAN / "dictamenes_comisiones.parquet"
PARCIAL = "_firmas_parcial.parquet"       # checkpoint, en el caché descartable
EN_CURSO = "_en_curso.txt"                 # qué PDF se está leyendo AHORA
CADA = 100                                 # cada cuántas OD se guarda


def _normalizar_expediente(exp: str) -> str:
    """`160-S-2007` (formato del PDF) -> `0160-S-2007` (formato de nuestra base)."""
    partes = str(exp).split("-")
    if len(partes) != 3:
        return ""
    num, tipo, anio = partes
    num = num.replace(".", "").lstrip("0") or "0"
    if len(anio) == 2:
        anio = ("19" if int(anio) > 50 else "20") + anio
    # el tipo va SIN puntos: el PDF escribe `P.E.` y nuestra base `PE`
    return f"{int(num):04d}-{tipo.replace('.', '')}-{anio}"


def cargar_trabajo(destino: Path) -> pd.DataFrame:
    ruta = destino / "od_trabajo.csv"
    if not ruta.exists():
        raise FileNotFoundError(
            f"no está {ruta}. Corré primero: python datos/expedientes/src/ingesta_od.py")
    t = pd.read_csv(ruta, dtype=str)
    t["od_publicacion"] = pd.to_datetime(t["od_publicacion"], errors="coerce")
    return t


def construir(limite: int | None = None, reanudar: bool = True,
              cada: int = CADA,
              saltear: set[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    destino = cache_dir()
    saltear = saltear or set()
    trabajo = cargar_trabajo(destino)
    if limite:
        trabajo = trabajo.head(limite)

    exp = pd.read_parquet(EXPEDIENTES_CLEAN / "expedientes.parquet")[
        ["proyecto_id", "exp_diputados", "camara_origen"]]
    por_exp = {str(e): p for e, p in zip(exp["exp_diputados"], exp["proyecto_id"])
               if isinstance(e, str)}

    padron = cargar_padron("diputados")
    filas_firmas: list[dict] = []
    stats = collections.Counter()

    # Checkpoint. Esto tarda ~50 minutos y antes escribía sólo al final: una
    # interrupción a los 45 tiraba todo. Ahora cada `cada` Órdenes del Día se
    # vuelca lo acumulado, y al reanudar se saltea lo ya hecho. Vale la pena
    # incluso si nunca se corta: permite mirar el resultado a mitad de camino.
    ruta_parcial = destino / PARCIAL
    hechos: set[str] = set()
    previas = pd.DataFrame()
    if reanudar and ruta_parcial.exists():
        previas = pd.read_parquet(ruta_parcial)
        hechos = set(previas["archivo"].astype(str))
        logger.info("reanudando: %d Órdenes del Día ya procesadas en %s",
                    len(hechos), ruta_parcial)

    def _volcar() -> None:
        acumulado = pd.concat([previas, pd.DataFrame(filas_firmas)], ignore_index=True) \
            if len(previas) else pd.DataFrame(filas_firmas)
        if len(acumulado):
            acumulado.to_parquet(ruta_parcial, index=False)

    for i, od in enumerate(trabajo.itertuples(index=False), start=1):
        # El checkpoint va ACÁ, al principio del cuerpo, y no al final: abajo hay
        # cuatro `continue` (ya hecho, salteado, PDF faltante, PDF ilegible) y
        # cualquiera de ellos se saltaba el guardado. Con PDF faltantes seguidos
        # no se guardaba nada y la reanudación era una ficción.
        if i > 1 and (i - 1) % cada == 0:
            _volcar()
            logger.info("%d/%d Órdenes del Día · %d firmas (checkpoint guardado)",
                        i - 1, len(trabajo), len(filas_firmas) + len(previas))

        if od.archivo in hechos or od.archivo in saltear:
            if od.archivo in saltear:
                stats["salteado_a_mano"] += 1
                for pr in str(od.proyecto_ids).split(";"):
                    filas_firmas.append(dict(od_numero=od.od_num, camara="diputados",
                                             archivo=od.archivo, fuente_url=od.url,
                                             od_publicacion=od.od_publicacion,
                                             proyecto_id=pr, enlace="orden_del_dia",
                                             parseo_ok=False,
                                             motivo="salteado a mano (--saltear)"))
            continue
        proyectos_od = str(od.proyecto_ids).split(";")
        ruta = destino / od.archivo
        base = {"od_numero": od.od_num, "od_publicacion": od.od_publicacion,
                "camara": "diputados", "archivo": od.archivo, "fuente_url": od.url}

        if not ruta.exists():
            stats["pdf_faltante"] += 1
            for p in proyectos_od:
                filas_firmas.append(dict(base, proyecto_id=p, enlace="orden_del_dia",
                                         parseo_ok=False, motivo="el PDF no se pudo bajar"))
            continue

        # Rastro de una línea con el archivo que se está leyendo. pdfminer puede
        # colgarse indefinidamente en un PDF con fuentes rotas, y sin esto no hay
        # forma de saber cuál era: el log sólo dice "voy por la 2200". Pasó el
        # 21-08 y costó una corrida entera de 50 minutos.
        try:
            (destino / EN_CURSO).write_text(od.archivo, encoding="utf-8")
        except OSError:
            pass
        try:
            od_parseada = parsear(texto_de_pdf(ruta), archivo=od.archivo)
        except Exception as exc:                      # noqa: BLE001 - queremos el motivo
            stats["pdf_ilegible"] += 1
            for p in proyectos_od:
                filas_firmas.append(dict(base, proyecto_id=p, enlace="orden_del_dia",
                                         parseo_ok=False,
                                         motivo=f"{type(exc).__name__}: {exc}"))
            continue

        # ¿a qué proyecto pertenece? por expediente si se puede, si no por OD
        del_pdf = [_normalizar_expediente(e) for e in od_parseada.expedientes]
        emparejados = [por_exp[e] for e in del_pdf if e in por_exp]
        if emparejados:
            proyectos, enlace = sorted(set(emparejados)), "expediente"
            stats["enlace_expediente"] += 1
        else:
            proyectos, enlace = proyectos_od, "orden_del_dia"
            stats["enlace_od"] += 1

        stats["parseo_ok" if od_parseada.parseo_ok else "parseo_falla"] += 1
        planas = a_filas(od_parseada)

        for p in proyectos:
            for f in planas:
                fecha = fecha_es(f.get("fecha_sala"))
                r = (resolver(f["firmante_raw"], padron, fecha)
                     if f.get("firmante_raw") else {})
                stats["firma_" + r.get("metodo", "sin_firmante")] += 1
                # Se vuelca **todo** lo que trae el parser (`**f`) en vez de copiar
                # campo por campo. La versión anterior enumeraba las columnas a
                # mano, así que cuando el parser ganó `origen_firmas` y
                # `dos_comisiones` esos datos nunca llegaron al parquet: el README
                # los documentaba y el archivo no los tenía. Un campo nuevo en el
                # parser ahora viaja solo.
                filas_firmas.append(dict(
                    f, **base, proyecto_id=p, enlace=enlace,
                    legislador_id=r.get("legislador_id", ""),
                    legislador=r.get("legislador", ""), bloque=r.get("bloque", ""),
                    bloque_norm=r.get("bloque_norm", ""),
                    bloque_linaje=r.get("bloque_linaje", ""),
                    metodo_match=r.get("metodo", "")))

    _volcar()
    logger.info("%d/%d Órdenes del Día · %d firmas (checkpoint final)",
                len(trabajo), len(trabajo), len(filas_firmas) + len(previas))

    firmas = pd.concat([previas, pd.DataFrame(filas_firmas)], ignore_index=True) \
        if len(previas) else pd.DataFrame(filas_firmas)
    comisiones = indice_comisiones(firmas)
    logger.info("stats: %s", dict(sorted(stats.items())))
    return firmas, comisiones


# ─────────────────────────── Senado ───────────────────────────

SALIDA_FIRMAS_SENADO = EXPEDIENTES_CLEAN / "dictamenes_firmas_senado.parquet"
PARCIAL_SENADO = "_firmas_senado_parcial.parquet"


def _expediente_senado(crudo: str) -> tuple[str, str]:
    """`33.25/CD/PL` -> (`0033-CD-2025`, `CD`).

    El listado del Senado da el expediente en tres partes: numero.anio, **origen** y
    tipo. Nuestra base lo guarda en `exp_senado` con el formato `0021-CD-2024`, que
    es el mismo que ya usa `enlace_senado.py`. El **origen** es lo que distingue una
    puerta de la otra y por eso se devuelve aparte:

    - `CD` = vino en revision de Diputados -> el Senado es camara REVISORA (Puerta C)
    - `PE` / `S` = nacio en el Senado o lo mando el Ejecutivo -> camara de ORIGEN (Puerta A)
    """
    try:
        numanio, origen, _tipo = str(crudo).split("/")
        num, anio = numanio.split(".")
    except ValueError:
        return "", ""
    anio = anio.strip()
    if len(anio) == 2:
        anio = ("19" if int(anio) > 50 else "20") + anio
    return f"{int(num):04d}-{origen.strip()}-{anio}", origen.strip()


def construir_senado(limite: int | None = None, reanudar: bool = True,
                     cada: int = CADA) -> pd.DataFrame:
    """Igual que `construir()` pero para las Órdenes del Día del Senado.

    Se comparte todo lo que se puede —el parser y el resolver son los mismos— y
    cambia lo que de verdad es distinto: de dónde sale la lista de trabajo, cómo se
    normaliza el expediente, qué padrón se consulta, y que acá **el rol de la cámara
    no es fijo**: depende del origen del expediente.
    """
    destino = cache_dir_senado()
    ruta_listado = destino / "od_senado_listado.csv"
    if not ruta_listado.exists():
        raise FileNotFoundError(
            f"no está {ruta_listado}. Corré primero: "
            "python datos/expedientes/src/ingesta_od_senado.py --anios 2008-2026")
    listado = pd.read_csv(ruta_listado, dtype=str)
    if limite:
        listado = listado.head(limite)

    exp = pd.read_parquet(EXPEDIENTES_CLEAN / "expedientes.parquet")[
        ["proyecto_id", "exp_senado", "camara_origen"]]
    por_exp = {str(e): p for e, p in zip(exp["exp_senado"], exp["proyecto_id"])
               if isinstance(e, str)}
    padron = cargar_padron("senado")

    ruta_parcial = destino / PARCIAL_SENADO
    hechos: set[str] = set()
    previas = pd.DataFrame()
    if reanudar and ruta_parcial.exists():
        previas = pd.read_parquet(ruta_parcial)
        hechos = set(previas["archivo"].astype(str))
        logger.info("reanudando: %d Órdenes del Día del Senado ya procesadas", len(hechos))

    filas: list[dict] = []
    stats = collections.Counter()

    def _volcar() -> None:
        acum = (pd.concat([previas, pd.DataFrame(filas)], ignore_index=True)
                if len(previas) else pd.DataFrame(filas))
        if len(acum):
            acum.to_parquet(ruta_parcial, index=False)

    for i, od in enumerate(listado.itertuples(index=False), start=1):
        if i > 1 and (i - 1) % cada == 0:
            _volcar()
            logger.info("%d/%d Órdenes del Día · %d firmas (checkpoint guardado)",
                        i - 1, len(listado), len(filas) + len(previas))
        nombre = f"senado-{od.od_anio or od.anio_buscado}-{od.od_numero or od.id}.pdf"
        if nombre in hechos:
            continue
        ruta = destino / nombre

        crudos = [x for x in str(od.expedientes).split(";") if x.strip()]
        normalizados = [_expediente_senado(x) for x in crudos]
        proyectos = sorted({por_exp[e] for e, _ in normalizados if e in por_exp})
        origenes = sorted({o for _, o in normalizados if o})
        # el rol de la camara sale del ORIGEN del expediente, no de un supuesto
        rol = ("revisora" if origenes == ["CD"] else
               "origen" if origenes and "CD" not in origenes else
               "mixto" if origenes else "")
        base = {"camara": "senado", "rol_camara": rol,
                "od_numero": od.od_numero, "od_anio": od.od_anio,
                "archivo": nombre, "expedientes_senado": ";".join(e for e, _ in normalizados),
                "fuente_url": f"{od.id}/downloadOrdenDia"}
        if proyectos:
            enlace = "expediente"
            stats["enlace_expediente"] += 1
        else:
            proyectos, enlace = [""], "sin_enlace"
            stats["sin_enlace"] += 1

        if not ruta.exists():
            stats["pdf_faltante"] += 1
            for pr in proyectos:
                filas.append(dict(base, proyecto_id=pr, enlace=enlace, parseo_ok=False,
                                  motivo="el PDF no se pudo bajar"))
            continue
        try:
            (destino / EN_CURSO).write_text(nombre, encoding="utf-8")
        except OSError:
            pass
        try:
            od_p = parsear(texto_de_pdf(ruta), archivo=nombre)
        except Exception as exc:                      # noqa: BLE001
            stats["pdf_ilegible"] += 1
            for pr in proyectos:
                filas.append(dict(base, proyecto_id=pr, enlace=enlace, parseo_ok=False,
                                  motivo=f"{type(exc).__name__}: {exc}"))
            continue

        stats["parseo_ok" if od_p.parseo_ok else "parseo_falla"] += 1
        for f in a_filas(od_p):
            fecha = fecha_es(f.get("fecha_sala"))
            r = (resolver(f["firmante_raw"], padron, fecha) if f.get("firmante_raw") else {})
            stats["firma_" + r.get("metodo", "sin_firmante")] += 1
            for pr in proyectos:
                filas.append(dict(f, **base, proyecto_id=pr, enlace=enlace,
                                  legislador_id=r.get("legislador_id", ""),
                                  legislador=r.get("legislador", ""),
                                  bloque=r.get("bloque", ""),
                                  bloque_norm=r.get("bloque_norm", ""),
                                  bloque_linaje=r.get("bloque_linaje", ""),
                                  metodo_match=r.get("metodo", "")))

    _volcar()
    logger.info("stats Senado: %s", dict(sorted(stats.items())))
    return (pd.concat([previas, pd.DataFrame(filas)], ignore_index=True)
            if len(previas) else pd.DataFrame(filas))


def indice_comisiones(firmas: pd.DataFrame) -> pd.DataFrame:
    """El índice (proyecto, cámara, comisión, dictamen), **derivado de las firmas**.

    Se deriva en vez de acumularse aparte por una razón concreta: acumulándolo, una
    corrida reanudada desde el checkpoint producía un índice incompleto —las
    comisiones de lo ya procesado se habían perdido— y el parquet salía a medias
    sin que nada fallara. Derivándolo, las dos tablas no pueden desincronizarse:
    salen del mismo lugar.
    """
    cols = ["proyecto_id", "camara", "comisiones", "dictamen_orden", "dictamen_clase",
            "od_numero", "od_publicacion", "enlace"]
    faltan = [c for c in cols if c not in firmas.columns]
    if faltan:
        logger.warning("no puedo armar el índice de comisiones, faltan columnas: %s", faltan)
        return pd.DataFrame()
    idx = firmas[cols].copy()
    idx = idx[idx["comisiones"].notna()]
    idx["comision"] = idx["comisiones"].astype(str).str.split(";")
    idx = idx.explode("comision")
    idx["comision"] = idx["comision"].str.strip()
    idx = idx[idx["comision"].ne("")]
    return (idx.drop(columns=["comisiones"])
               .drop_duplicates()
               .sort_values(["proyecto_id", "comision", "dictamen_orden"])
               .reset_index(drop=True))


def resumen(firmas: pd.DataFrame) -> None:
    # ojo con el `astype(str)` sobre NaN: devuelve la cadena "nan", que no es vacía
    # y contaba como firma las filas de las OD que ni siquiera se pudieron bajar
    col = firmas["firmante_raw"] if "firmante_raw" in firmas.columns else pd.Series(dtype=str)
    con_firma = firmas[col.notna() & col.astype(str).str.strip().ne("")]
    print("\n=== cobertura ===")
    print(f"  Órdenes del Día leídas .... {firmas['archivo'].nunique()}")
    print(f"  proyectos alcanzados ...... {firmas['proyecto_id'].nunique()}")
    print(f"  firmas ..................... {len(con_firma)}")
    if len(con_firma):
        ok = con_firma["metodo_match"].isin(["exacto", "iniciales", "oficial_gana"]).sum()
        print(f"  con legislador resuelto .... {ok} ({100 * ok / len(con_firma):.1f}%)")
        print("\n=== por método de emparejamiento ===")
        print(con_firma["metodo_match"].value_counts().to_string())
        print("\n=== carácter del dictamen ===")
        print(con_firma["disidencia"].value_counts().to_string())
        print(con_firma["dictamen_clase"].value_counts().to_string())
    malas = firmas[~firmas["parseo_ok"].astype(bool)]
    if len(malas):
        print(f"\n=== {malas['archivo'].nunique()} Órdenes del Día sin leer ===")
        print(malas.groupby("motivo")["archivo"].nunique().sort_values(ascending=False).head(8).to_string())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limite", type=int, default=None, help="procesar sólo las primeras N")
    ap.add_argument("--desde-cero", action="store_true",
                    help="ignorar el checkpoint y rehacer todo")
    ap.add_argument("--cada", type=int, default=CADA,
                    help="cada cuántas Órdenes del Día se guarda el checkpoint")
    ap.add_argument("--senado", action="store_true",
                    help="procesar las Órdenes del Día del SENADO en vez de las de Diputados")
    ap.add_argument("--saltear", default="",
                    help="archivos a NO leer, separados por coma (p. ej. un PDF que cuelga "
                         "a pdfminer). Entran a la salida marcados, no desaparecen.")
    args = ap.parse_args(argv)
    # stream=sys.stdout a propósito: por defecto logging escribe en stderr, y
    # PowerShell pinta de ROJO todo lo que un proceso manda por stderr —incluido
    # un INFO de avance— y encima lo envuelve en un NativeCommandError. Una
    # corrida sana parecía estar fallando. Con stdout, `| Tee-Object` alcanza y
    # no hace falta el `2>&1`.
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

    if args.senado:
        firmas = construir_senado(args.limite, reanudar=not args.desde_cero, cada=args.cada)
        if firmas.empty:
            logger.error("no salió ninguna fila")
            return 1
        SALIDA_FIRMAS_SENADO.parent.mkdir(parents=True, exist_ok=True)
        firmas.to_parquet(SALIDA_FIRMAS_SENADO, index=False)
        logger.info("-> %s (%d filas)", SALIDA_FIRMAS_SENADO, len(firmas))
        resumen(firmas)
        if "rol_camara" in firmas.columns:
            print("\n=== rol de la cámara (de dónde vino el expediente) ===")
            print(firmas.groupby("rol_camara")["archivo"].nunique().to_string())
        return 0

    firmas, comisiones = construir(
        args.limite, reanudar=not args.desde_cero, cada=args.cada,
        saltear={x.strip() for x in args.saltear.split(',') if x.strip()})
    if firmas.empty:
        logger.error("no salió ninguna fila")
        return 1
    SALIDA_FIRMAS.parent.mkdir(parents=True, exist_ok=True)
    firmas.to_parquet(SALIDA_FIRMAS, index=False)
    if not comisiones.empty:
        comisiones.to_parquet(SALIDA_COMISIONES, index=False)
    logger.info("-> %s (%d filas)", SALIDA_FIRMAS, len(firmas))
    logger.info("-> %s (%d filas)", SALIDA_COMISIONES, len(comisiones))
    resumen(firmas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
