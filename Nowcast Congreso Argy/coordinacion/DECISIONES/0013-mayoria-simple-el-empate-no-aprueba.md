# ADR-0013 — Mayoría simple: el empate NO aprueba

**Fecha:** 2026-08-22 · **Estado:** Aceptada · **Quién:** Valle (lo detectó preguntando de dónde salía el umbral), Claude (implementación)

## Contexto

Valle preguntó por qué el umbral de mayoría simple daba **125,5** sobre 257 bancas, si su cuenta era otra: son 257 diputados, uno preside y no vota, así que la mayoría se consigue con más de la mitad de los 256 restantes.

La primera parte de la respuesta es que el umbral **no es un número fijo**: `umbral_aprobacion` lo calcula sobre los **emitidos** (afirmativos + negativos) de cada simulación, no sobre las bancas. De 257, unos 5 caen en ausencia o abstención, quedan ~252 emitiendo, y la mitad es ~126. Eso está bien: la regla parlamentaria depende de quiénes votan.

La segunda parte es un error. La regla programada era `umbral = emitidos / 2`, y la aprobación se decide con `afirm >= umbral`. Con 256 emitidos eso da `128 >= 128`: **un empate aprobaba**. Verificado en disco el 22-08 antes de tocar nada.

Un empate no aprueba. En Diputados desempata el presidente —que justamente no vota en el resto de la votación— y sin ese voto el proyecto cae. El error corría **a favor de la aprobación en exactamente los casos más ajustados**, que son los únicos donde el número importa.

## Decisión

`umbral_aprobacion(..., "SIMPLE")` devuelve **la mitad de los emitidos MÁS UNO**:

```python
return float(int(emitidos) // 2 + 1)
```

Queda consistente con `ABSOLUTA`, que ya usaba `miembros // 2 + 1` con el mismo `>=`.

## Consecuencias

- **Es un cambio de contrato de un módulo compartido** (`modelo/agregador_institucional`), por eso este ADR. El módulo figura en el TABLERO como `Claude+Valle`.
- **Mueve todos los números hacia abajo, y más cuanto más ajustada la votación.** En el caso sintético de los tests de la Puerta D —6 a favor y 4 en contra sobre 10 bancas— P pasó de **>0,90 a 0,862**: con umbral 6 en vez de 5, una sola deserción lo pierde. En el caso real medido (Reforma de Ganancias, junio 2026) no se movió: con 150 afirmativos esperados contra un umbral de 122, el margen es de 28 votos y la regla del empate no llega a tocarlo.
- **`test_agregador.py` cambió su expectativa** de `emitidos/2` a `emitidos//2+1`, con dos casos nuevos que fallan con la regla vieja (256 y 251 emitidos).
- **Queda anotado y NO resuelto:** el presidente de la Cámara ocupa una banca en el padrón. Hoy no suma voto porque su asistencia medida (1,3%) lo saca del conteo por el canal de presencia, que es un mecanismo general y también cubre a Schiaretti (6%). Pero conceptualmente los votantes son 256, no 257, y eso no está modelado como tal.
