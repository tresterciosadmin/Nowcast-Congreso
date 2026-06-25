# ADR 0001 — Estructura del repo para trabajo en paralelo

**Fecha:** 2026-06-25 · **Estado:** Aceptada

## Contexto
Varias personas/Claudes trabajan el proyecto en simultáneo sobre un repo de GitHub. Riesgo: pisarse y generar conflictos de merge y trabajo duplicado.

## Decisión
1. **Monorepo modular.** Un módulo por unidad de trabajo, organizado por variable/función: `datos/`, `variables/<variable>/`, `modelo/`, `evaluacion/`, `producto/`, `docs/`, `coordinacion/`.
2. **Un módulo, un dueño, una rama.** Se reclama en `TABLERO.md` antes de empezar. Cada quien edita solo su módulo; consume de otros vía su contrato de salida (parquet), no su código.
3. **Contratos en `docs/schemas/`.** Único punto compartido; cambiarlo requiere ADR.
4. **Documento vivo obligatorio.** `ESTADO-DEL-PROYECTO.md` se actualiza en cada PR; sin entrada no se mergea.
5. **Datos fuera de git.** `data/raw` y `data/clean` se regeneran con los scripts de ingesta; no se versionan.

## Alternativas descartadas
- **Dos repos (data CC0 + engine propietario)** como en el plan v2.1: válido a futuro, pero agrega fricción de coordinación ahora. Se difiere.
- **Carpeta por persona:** no escala y mezcla responsabilidades; se prefiere por variable/función.

## Consecuencias
- Conflictos de merge casi nulos si se respetan los límites de módulo.
- `docs/schemas` y `modelo/ensemble` son los cuellos de botella a coordinar con dueño único.
