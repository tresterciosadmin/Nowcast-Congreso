# Módulo: modelo/ensemble

**Propósito.** La composición final del Nowcast — el nowcast **end-to-end de un proyecto**:

    P(aprobación) = P(llega al recinto) × P(mayoría | recinto)

Une las dos piezas ya validadas del sistema en un solo número (con su descomposición).

**Estado:** EN CURSO (v1: composición + nowcast por proyecto + tests)
**Owner actual:** Claude+Valle (2026-07-12)

## Contrato
- **Entradas:**
  - `variables/embudo/outputs/p_embudo.parquet` → `p_llega_recinto` por `proyecto_id` (el embudo).
  - `modelo/agregador_institucional` → función reutilizable `simular_votacion` (P mayoría|recinto como distribución). *Se importa su función pública; no se toca su código.*
- **Salida (contrato estable, `outputs/`):** `nowcast_<proyecto_id>.json` con los dos factores, P(aprobación) y la banda de votos. Función reutilizable: `nowcast_proyecto(proyecto_id, escenario, p_embudo_path)`.
- **Gate de pase:** calibración de la cadena dentro de tolerancia — **parcial**: cada factor está validado por separado (embudo skill 0,34-0,39; agregador Brier 0,0089). La calibración de la cadena COMPLETA sobre proyectos NO votados espera la posición de bloque proyectada (ver simplificación).

## Cómo se usa
```powershell
# demo autocontenida (no necesita datos): muestra la tarjeta end-to-end
python modelo\ensemble\src\ensemble.py demo

# nowcast de un proyecto real: su P(llega) sale de p_embudo por proyecto_id,
# y la postura de cada bloque se pasa en un escenario JSON
python modelo\ensemble\src\ensemble.py nowcast 1234-D-2026 escenario.json
```
Escenario JSON:
```json
{ "tipo_mayoria": "SIMPLE", "camara": "Diputados",
  "p_llega_recinto": 0.12,
  "bloques": [
    {"bloque": "UxP", "bancas": 99, "linea": "NEGATIVO",   "desvio": 0.03},
    {"bloque": "LLA", "bancas": 39, "linea": "AFIRMATIVO",  "desvio": 0.02}
  ] }
```
- `p_llega_recinto` es opcional: si falta, se busca por `proyecto_id` en `p_embudo.parquet`. Pasarlo en el JSON lo fuerza (útil para escenarios "¿y si…?").
- `linea` ∈ {AFIRMATIVO, NEGATIVO, NO_ACOMPANA}; `desvio` es la tasa de indisciplina del bloque (de `modelo/voto_individual`).
- Tipos de mayoría y cámaras: los del agregador (SIMPLE / ABSOLUTA / DOS_TERCIOS / TRES_CUARTOS).

## Qué devuelve (tarjeta)
`P(llega al recinto)` × `P(mayoría | recinto)` = **`P(aprobación)`**, más los afirmativos esperados con banda 5-95% y el umbral. Ejemplo (demo): 12,0% × 58,1% = **7,0%**, con la votación al filo (109,6 vs umbral 109,4).

## Simplificación v1 (documentada)
La **postura de cada bloque** es un dato de entrada (elegida a mano / observada), heredado del agregador. En el sistema final la proyecta un módulo de **posición de bloque por tema** (pendiente). Por eso:
- el nowcast de un proyecto YA VOTADO reproduce la historia (postura observada) → equivale al backtest del agregador (Brier 0,0089);
- el nowcast de un proyecto NO votado usa la postura que le pongas → la calibración de la cadena completa depende de esa proyección futura.

## Tests
```bash
python modelo/ensemble/tests/test_ensemble.py   # 16 chequeos offline (sin datos)
```

## Pendientes / v2
- **Posición de bloque proyectada por tema** (desbloquea la calibración de la cadena completa y el nowcast automático sin escenario a mano). Depende de `variables/proyecto` (tema) + un módulo de posición de bloque.
- Propagar incertidumbre del embudo a una **banda sobre P(aprobación)** (hoy es un punto).
- Conectar la asistencia condicional (`variables/asistencia_quorum` escalón 2) al factor de mayoría.

## Convenciones
Resiliencia: errores específicos, parsing defensivo, logging estructurado. Se consume el
CONTRATO de los otros módulos (parquet del embudo, función pública del agregador); no se
edita su código.
