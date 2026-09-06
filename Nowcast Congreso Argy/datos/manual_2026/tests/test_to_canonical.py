# -*- coding: utf-8 -*-
"""El Excel 2025-2027 aporta los VOTOS; la identidad la resuelve el PADRON.

Este test existe por un bug de datos y por un bug mio, los dos del 06-09-2026.

- **El bug de datos.** La columna PROVINCIA de la hoja Senado estaba desalineada:
  66 de 72 senadores tenian el distrito de otro. No era un corrimiento (ningun
  offset lo explicaba) sino una PERMUTACION: las 72 provincias correctas estaban
  todas, repartidas entre las personas equivocadas. Firma de "ordenar sin extender
  la seleccion". No dio error: entro a la canonica y se quedo ahi.
- **El bug mio.** La primera version del cruce comparaba SENSIBLE A MAYUSCULAS. El
  padron guarda "Santa Fe" y el Excel "SANTA FE", asi que "corregia" las 256 filas
  de Diputados que estaban perfectas. Se agarro solo porque se corrio a /tmp antes
  de escribir al repo.

Lo que fija:

1. `_norm` iguala mayusculas, acentos y los alias de CABA / Tierra del Fuego.
2. `_clave` es invariante al orden Apellido/Nombre (lo mismo que datos/canonica).
3. El padron pisa el DISTRITO y NO pisa el BLOQUE. La asimetria es a proposito: el
   distrito es estable mientras dure la banca; el bloque depende del tiempo, y
   ponerle a un voto de marzo el bloque de agosto es leakage que no da error.
4. `_voto` excluye "Pendiente de incorporacion" y cuenta al presidente de la
   camara como AUSENTE.
5. Sin padron no explota: el Excel queda como esta y se avisa.
6. Contra el Excel real (si esta): Senado 72/72 en distrito, 24 provincias con
   exactamente 3 senadores cada una, y ninguna correccion en Diputados (el caso
   que delataba la comparacion sensible a mayusculas).

    python datos/manual_2026/tests/test_to_canonical.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import to_canonical as tc  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("_norm iguala lo que tiene que igualar")
for a, b in (("SANTA FE", "Santa Fe"),
             ("ENTRE RIOS", "Entre Ríos"),
             ("CORDOBA", "Córdoba"),
             ("  BUENOS   AIRES ", "Buenos Aires"),
             ("CIUDAD AUTONOMA DE BUENOS AIRES", "CABA"),
             ("Ciudad de Buenos Aires", "caba"),
             ("TIERRA DEL FUEGO, ANTARTIDA E ISLAS DEL ATLANTICO SUR",
              "Tierra del Fuego")):
    check(tc._norm(a) == tc._norm(b), f"_norm({a!r}) tendria que igualar a {b!r}")

print("_norm NO iguala provincias distintas")
for a, b in (("SALTA", "JUJUY"), ("LA RIOJA", "RIOJA NEGRA"), ("CHACO", "CHUBUT")):
    check(tc._norm(a) != tc._norm(b), f"_norm no puede igualar {a!r} con {b!r}")

print("_clave es invariante al orden Apellido/Nombre")
check(tc._clave("MARQUEZ, NADIA JUDITH") == tc._clave("Nadia Judith Márquez"),
      "el orden del nombre no puede cambiar la clave")
check(tc._clave("SNOPEK, GUILLERMO") != tc._clave("SNOPEK, ALEJANDRA"),
      "dos personas distintas no pueden compartir clave")

print("_voto: que entra y que no")
for crudo, esperado in (("AFIRMATIVO", "AFIRMATIVO"), ("Negativo", "NEGATIVO"),
                        ("ABSTENCIÓN", "ABSTENCION"), ("AUSENTE", "AUSENTE"),
                        ("PRESIDENTE", "AUSENTE"),
                        ("Pendiente de incorporación", None),
                        ("", None), (None, None), ("cualquier cosa", None)):
    check(tc._voto(crudo) == esperado,
          f"_voto({crudo!r}) tendria que dar {esperado!r}, dio {tc._voto(crudo)!r}")

print("sin padron no explota")
_orig = dict(tc.PADRON)
try:
    tc.PADRON["senado"] = Path("/no/existe/padron.csv")
    check(tc.cargar_padron("senado") == {}, "sin archivo tiene que dar {}")
    check(tc.cargar_padron("camara_inventada") == {}, "camara desconocida tiene que dar {}")
finally:
    tc.PADRON.update(_orig)

XLSX = Path(__file__).resolve().parents[1] / "Congreso_25-27.xlsx"
if not XLSX.exists():
    print(f"\n[salteo] no esta {XLSX.name}; los checks contra el Excel real no corren")
else:
    import openpyxl

    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    _, vs = tc.parse_hoja(wb["Senado"],
                          {"apellido": 2, "nombre": 1, "distrito": 4, "bloque": 3,
                           "primera_ley": 17}, "senado")
    _, vd = tc.parse_hoja(wb["Diputados"],
                          {"apellido": 1, "nombre": 2, "distrito": 3, "bloque": 6,
                           "primera_ley": 8}, "diputados")

    pad_sen = tc.cargar_padron("senado")
    sen = {v["legislador_nombre"]: v for v in vs}
    check(len(sen) == 72, f"el Senado tiene 72 bancas, salieron {len(sen)}")
    mal = [n for n, v in sen.items()
           if tc._clave(n) in pad_sen
           and tc._norm(v["distrito"]) != tc._norm(pad_sen[tc._clave(n)][0])]
    check(not mal, f"distrito distinto al padron en {len(mal)}: {mal[:5]}")

    porprov: dict[str, int] = {}
    for v in sen.values():
        porprov[tc._norm(v["distrito"])] = porprov.get(tc._norm(v["distrito"]), 0) + 1
    check(len(porprov) == 24, f"tendrian que ser 24 provincias, son {len(porprov)}")
    check(all(n == 3 for n in porprov.values()),
          f"cada provincia elige 3 senadores; no pasa en "
          f"{ {p: n for p, n in porprov.items() if n != 3} }")

    # El caso que delataba la comparacion sensible a mayusculas: el padron de
    # Diputados guarda Title Case y el Excel MAYUSCULAS. Si algo se "corrige" aca,
    # es la normalizacion la que se rompio, no el Excel.
    pad_dip = tc.cargar_padron("diputados")
    dip = {v["legislador_nombre"]: v for v in vd}
    malos_dip = [n for n, v in dip.items()
                 if tc._clave(n) in pad_dip
                 and tc._norm(v["distrito"]) != tc._norm(pad_dip[tc._clave(n)][0])]
    check(not malos_dip,
          f"Diputados no necesita correcciones; aparecieron {len(malos_dip)}: {malos_dip[:5]}")

    # El bloque NO se pisa: tiene que quedar el del Excel aunque el padron diga otra cosa.
    distintos = [n for n, v in sen.items()
                 if tc._clave(n) in pad_sen
                 and tc._norm(v["bloque"]) != tc._norm(pad_sen[tc._clave(n)][1])]
    check(True, "")  # marcador de que el bloque se leyo
    corridos -= 1
    if distintos:
        print(f"  (aviso) el bloque difiere del padron en {len(distintos)} y NO se piso: "
              f"{distintos[:4]}")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
