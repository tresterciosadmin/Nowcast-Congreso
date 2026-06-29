# Módulo: datos/manual_2026

**Propósito.** Integrar el Excel curado a mano por Franco (período 2025–2027) al esquema canónico. Aporta votos nominales 2026 de **ambas cámaras**, padrón con **bloque del Senado** (resuelve el hueco), provincia, comisión y mandato.

**Estado:** HECHO (primera carga). Fuente viva: Franco la sigue completando a mano.

## Contrato
- **Entrada:** `Congreso_25-27.xlsx` (hojas Diputados, Senado; una columna por ley con el voto de cada legislador).
- **Salida:** `data/clean/manual_2026_{actas,votos}.parquet` (esquema canónico, fuente=`manual_2026`).
- **Correr:** `XLSX=Congreso_25-27.xlsx python src/to_canonical.py`

## Mapeo
- Cada (ley × cámara) con votos → un acta (`manual_2026:<camara>:<slug_ley>`).
- Voto: AFIRMATIVO/NEGATIVO/ABSTENCIÓN/AUSENTE. "PRESIDENTE" → AUSENTE. "PENDIENTE DE INCORPORACIÓN" → se excluye (banca no asumida).
- `legislador_nombre` = "Apellido, Nombre"; `bloque` y `distrito/provincia` del padrón.
- `fecha` queda vacía (el Excel no trae fecha por ley); por eso estos votos no entran en el corte por año del baseline.

## Valor
- Extiende la base a 2026.
- **Resuelve el bloque del Senado** → habilitó la primera medición de baseline del Senado (~0,94 en disputadas, muestra chica).
- `manual_2026` tiene **máxima precedencia** en la deduplicación (curado a mano).

## Pendiente
- Cuando Franco agregue fechas por ley, enriquecer `fecha`.
- Usar el padrón del Senado para **retro-completar** el bloque de los votos de argentinadatos 2024–2025 (hoy "SIN BLOQUE").
