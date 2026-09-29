# Reglas del proyecto — borrador (una página)

**Diez reglas. Cada una sale de algo que falló en septiembre y se comprueba con un test, un comando o un archivo. Reemplazan a ≈ 55 reglas y controles hoy dispersos en `CLAUDE.md`, `PROTOCOLO-GIT.md`, FORMULA §IV y los ADR.** Principio rector: *el modelo sigue siempre a la realidad; cualquier desvío se ve solo.*

| # | Regla | Qué falló | Cómo se comprueba | ADR |
|---|---|---|---|---|
| **1** | **Nada afecta el número publicado sin una medición vigente, hecha con el motor real** (importado, no copiado). Lo sin medición queda apagado o en su valor neutro. | β, ε₀+τη, presencia y guard de era se prendieron con mediciones con fuga, oráculo o inexistentes | test contra el **registro de parámetros generado desde el código**: falla si un parámetro que mueve el panel no tiene medición, o si el hash del motor de la medición no es el actual | C5 |
| **2** | **La historia se corta por fecha estricta y otra ley** (unidad = la ley, no el acta). | skill 0,1611 → 0,1333 | `test_historia_sin_fuga.py` + `invariancia_al_futuro.py` (corrompe el futuro y la misma ley: $P_i$ no se mueve) | C5 |
| **3** | **Todo IC re-muestrea leyes; una comparación entre versiones es pareada.** | SE clusterizados por acta salían 3-4× angostos | una sola función (`skill_ic_por_ley` / `dif_brier_ic_por_ley`); test que prohíbe otra en `evaluacion/` | C5 |
| **4** | **Ninguna medición arma su propio récord: importa el motor.** | diez scripts con `shift(1)` por fila | test AST: `.expanding(` o `shift(1)` sobre votos fuera de `baseline_voto_individual` = rojo | C5 |
| **5** | **Un control tiene que poder fallar:** cada invariante lleva su control positivo. | `test_rutas.py` no podía dar rojo; el "control" de 0028 era el tratamiento | cada test de invariante incluye un caso que **debe** fallar (`*_control_positivo`) | C1, C5 |
| **6** | **Lo declarado se contrasta con lo observado:** banda, calibración y P(aprobación). | banda "90%" cubre 63,6% | `calibracion_declarada.json` generado; falla si cobertura observada − declarada > 5 pp | C4 |
| **7** | **Una mejora sin explicación es una alarma.** | la fuga *mejoró* el número | gate: falla si el ΔBrier pareado mejora > 2% sin entrada de medición registrada | C5 |
| **8** | **Ningún default cambia sin un test que fije el valor nuevo y cite la medición.** | nada fijaba `RECORD_POR_TEMA`, `SHRINK_RECORD`, `EPSILON0`, `TAU`; mismo nombre con dos defaults | `test_defaults_fijados` generado del registro | C5, C6 |
| **9** | **Un dato, un lugar:** el estado, la fórmula-tabla y el tablero se **generan** del código y de las mediciones; lo escrito a mano no repite números; **el número que ve el usuario es la salida del motor, no un recálculo**. | el HTML dice 98,01% y su titular lo calcula un JavaScript aparte (98,0% aun regenerado; el motor da 61,3%); `tablero_datos.js` dice 63,6% y 99,88% | `generar_estado.py` + test: el titular del HTML = `p_aprobacion` del motor | C1, C3 |
| **10** | **Prender algo exige el OK de Franco, IC a favor con Holm sobre las banderas de la ronda y confirmación fuera de muestra. Apagar no exige nada.** | 10 de los 12 ADR 0023-0034 los decidió Claude en sesión delegada | entrada del registro con `aprobado_por` y `fecha`; el gate la exige | C5, C6 |

## Qué pasa con las reglas de hoy

**Se reemplazan:** ADR-0015 (los tres niveles) → reglas 1 y 8 · FORMULA §IV.4 (`shift(1)` + `expanding`, que prescribía la fuga) → regla 2 · §IV.6 y regla del expediente → reglas 2 y 3 · §IV.7 "defaults silenciosos" → regla 8 · "regla de trazabilidad" (una entrada a `ESTADO` por cambio) y "regla del TABLERO" → regla 9 · "orden de lectura obligatorio" de siete documentos → leer estas diez reglas y `URGENTE.md`.

**Se conservan (reducidas):** `URGENTE.md` (un párrafo; hoy está parado a propósito) · `Archivos_Borrar/` y "nada se borra" (una línea) · MAPA generado, con el hook arreglado o sacado de la doc · las **trampas del dato** —comisiones con comas, `od_numero`, insumo faltante, origen Senado— que pasan a C1 §5 · en git: sin `push` desde Claude Code, sin reescribir historia, mensajes en castellano y con contenido (19 de 160 tienen < 16 caracteres).

**Se eliminan por redundantes o incumplidas:** "un módulo, un dueño, una rama" (12 fusiones en 243 commits) · los "límites del entorno" del sandbox, que el propio `CLAUDE.md` dice que no aplican a Claude Code · el flujo mínimo de seis pasos · `PROTOCOLO-GIT.md` salvo cinco líneas · la lista de trampas de FORMULA §IV.7 tras pasar a C1.

**Cuenta final:** de ≈ 55 reglas y controles → **10 reglas + 4 trampas del dato**.
