# ADR-0021 — El carácter del dictamen y la raíz del repo viven una sola vez

**Fecha:** 2026-09-08 · **Estado:** APLICADO · **Decide:** Franco · **Toca:** `definiciones.py`, `modelo/ensemble/src/{estimar_beta_dictamen, estimar_epsilon_tau, estimar_psi_arrastre, estimar_theta_sobre_tablas}.py`, `modelo/ensemble/validar_condicionamiento_votos.py`, `evaluacion/baseline/src/{baseline_voto_individual, diagnostico_senado, medir_guard_era}.py`, `evaluacion/baseline/tests/test_guard_era.py`, `tests/test_caracter_dictamen.py`, `tests/test_raiz_del_repo_una_sola_copia.py` · **Se relaciona con:** ADR-0014 (definiciones compartidas), ADR-0010 (rutas compartidas), ADR-0017 (rotulado del dictamen), ADR-0019 (el calendario vive en definiciones)

## Contexto

Franco pidió, durante la limpieza de septiembre, saber cuánto código redundante
hay y fusionar lo que corresponda. Se midió en vez de estimar: `.mapa/duplicados.py`
compara la forma del árbol sintáctico de las 732 funciones del repo.

**El resultado desarma la premisa: ~201 LOC de duplicación exacta entre archivos
sobre 32.427 de Python, o sea 0,6%.** Y de esos 201, unos 150 son un solo patrón
—el helper `check`/`chk` copiado en 40 archivos de test— que es lo que permite que
cada test corra como script suelto, o sea una convención, no un descuido.

Quedaron dos casos que sí valían, y son los que este ADR resuelve. Los dos tienen
la misma forma que el ADR-0014: una regla que dos módulos tienen que responder
igual, copiada en los dos.

## Decisión 1 — `caracter_de_dictamen` va a `definiciones.py`

Dieciséis líneas idénticas carácter por carácter en
`modelo/ensemble/src/estimar_beta_dictamen.py` y
`evaluacion/baseline/src/baseline_voto_individual.py`: dado el conjunto de
`dictamen_clase` de un proyecto en una cámara, devolver
`DISPUTADO` / `solo_minoria` / `mayoria` / `UNICO` / `None`.

**Por qué no podían quedar separadas.** Son la MISMA partición usada para dos
cosas distintas: con ella `modelo/ensemble` arma el panel con el que **estima** el
$\beta$ del dictamen, y con ella `evaluacion/baseline` arma el corte con el que lo
**evalúa**. Si divergen, se estima sobre una partición y se mide sobre otra —y
**nada da error**. El control 5 de `verificar_regeneracion.py` seguiría en verde,
porque verifica que las categorías existan, no cómo se asignan.

**Se verificó ANTES de unificar**, como pide el plan de limpieza: se extrajeron
las dos implementaciones y se compararon en las **16 entradas posibles** del
vocabulario (`unico`, `mayoria`, `minoria`, `desconocido`) más dos etiquetas
desconocidas. **Cero diferencias.** Esa tabla es ahora
`tests/test_caracter_dictamen.py`, que además falla si alguien vuelve a escribir
la regla por su cuenta (verificado: con las dos copias puestas, fallaba).

Se conserva el matiz que motivó el ADR-0017 y está en el docstring: `desconocido`
es *"no se encontró el rótulo"*, **no** *"despacho único"*. Se descarta antes de
decidir.

## Decisión 2 — la raíz del repo se busca como dice `rutas.py`

**Nueve** archivos —cuatro de ellos en el motor— subían por los padres hasta
encontrar una carpeta que tuviera `coordinacion/` **y** `variables/`. `rutas.py`
(ADR-0010) documenta otro criterio y explica por qué es el bueno: subir hasta
encontrar el propio `rutas.py`, *"así siguen funcionando si el módulo cambia de
profundidad — que es justo lo que rompía antes"*.

Los dos criterios daban lo mismo, y está **medido desde la carpeta de cada `.py`
del repo** antes de tocar nada (`tests/test_raiz_del_repo_una_sola_copia.py`,
primer test). Pero el viejo se apoya en que dos carpetas concretas no cambien de
nombre ni de lugar; una limpieza que mueva `coordinacion/` deja a los nueve
buscando una raíz que no existe, y el error no aparece donde está la causa.

**Un hallazgo de paso:** `modelo/ensemble/validar_condicionamiento_votos.py` tenía,
además, un fallback que devolvía `/sessions/wizardly-friendly-hamilton/mnt/...`
—una ruta de sandbox de una sesión vieja de Claude—. Cuando la búsqueda fallaba,
el script **no daba error**: apuntaba a un disco que no existe en ninguna máquina y
todo lo de abajo leía archivos ausentes. Se sacó. La variable `NOWCAST_REPO`, que
sí sirve, se conserva.

## Presentación del cambio al motor (ADR-0015)

1. **La función.** `caracter_de_dictamen` hace exactamente lo que hacían las dos
   copias —verificado en las 16 entradas—, y ahora vive en `definiciones.py`. El
   bootstrap de la raíz cambia de criterio pero no de resultado, verificado desde
   cada carpeta del repo.
2. **El motor en su conjunto.** Cambian imports, no cálculos. Ningún contrato
   cambia de forma. No se agrega, saca ni modifica ningún supuesto: las dos
   fusiones se eligieron justamente porque eran idénticas, y las que **no** eran
   idénticas (`_eras_de`, que delega en el motor y sólo memoiza) se dejaron.
3. **La fórmula.** `coordinacion/FORMULA-COMPLETA.md` **no cambia**. Ningún
   término se agrega, se saca ni se modifica.

## Consecuencias

- **Medido después de aplicar:** suite 33 → **39 passed** (los seis tests nuevos),
  `verificar_regeneracion.py` **16 OK · 0 a mirar**, y los números del control 4
  idénticos al dígito — $\beta_1 = 2{,}1045$, $\beta_2 = 2{,}138$, n_actas 1.549,
  n_votos 245.883; Senado 449 actas y 26.100 votos. **P(aprob) = 0,9801**, sin
  cambio.
- Un arreglo en la regla del carácter ahora cuesta un claim de módulo en vez de
  dos, que es el argumento del ADR-0014.
- Lo que **no** se unificó, y por qué: el helper `check`/`chk` de los 40 archivos
  de test (~150 LOC, el 75% de toda la duplicación). Fusionarlo obliga a que cada
  test importe de un lugar común, y rompe la convención de que un test corre solo.
  Es una decisión de diseño de la suite, no una limpieza. Queda abierta.
