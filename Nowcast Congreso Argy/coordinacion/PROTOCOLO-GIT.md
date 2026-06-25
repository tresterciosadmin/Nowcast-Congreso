# PROTOCOLO GIT — cómo trabajar en paralelo sin conflictos

## Principio
Los conflictos de merge nacen cuando dos personas editan el mismo archivo. La estructura del repo está diseñada para que cada quien edite **archivos distintos** (su módulo). Si respetás los límites de módulo, casi nunca vas a tener conflictos.

## Ramas
- `main` siempre estable y mergeable. Nadie pushea directo a `main`.
- Una rama por tarea: `feat/<modulo>-<desc-corta>` (ej. `feat/embudo-supervivencia-comision`).
- Ramas cortas: abrí, trabajá, mergeá en días, no semanas. Cuanto más vieja la rama, más drift.

## Antes de empezar
1. `git pull origin main`.
2. Leé `coordinacion/ESTADO-DEL-PROYECTO.md` y `TABLERO.md`.
3. Reclamá tu módulo en `TABLERO.md` (commit en tu rama).

## Mientras trabajás
- Editá **solo** archivos dentro de tu módulo + tu entrada en ESTADO + tu fila en TABLERO.
- **Nunca** edites el módulo de otro. Consumí su salida (parquet/contrato), no su código.
- Cambios a archivos compartidos (`docs/schemas/`, este protocolo, el plan): requieren ADR en `DECISIONES/` y aviso. Son los únicos puntos de colisión posible; tratalos con cuidado.

## Pull Requests
- PR chico y enfocado a un módulo. Título: `<modulo>: <qué hace>`.
- Checklist del PR (pegá esto en la descripción):
  - [ ] Trabajé solo dentro de mi módulo.
  - [ ] Agregué entrada en `ESTADO-DEL-PROYECTO.md`.
  - [ ] Actualicé `TABLERO.md` (estado del módulo).
  - [ ] Código con las 4 directivas de resiliencia.
  - [ ] Si cambié un contrato compartido, hay ADR.
- Mergeá apenas pase. No acumules PRs abiertos sobre el mismo módulo.

## Archivos que NO se versionan
Ver `.gitignore`: datos crudos/limpios (`data/raw`, `data/clean`, `*.parquet`, `*.csv` pesados), entornos, cachés. Los datos se regeneran corriendo los scripts de ingesta; no se suben al repo.

## Si igual aparece un conflicto
1. No fuerces. `git pull origin main` en tu rama y resolvé localmente.
2. Si el conflicto es en `ESTADO`, `TABLERO` o un schema, resolvé conservando **ambas** entradas/cambios (son aditivos).
3. Ante la duda, registralo en el PR y pedí revisión.

## GitHub (primer setup)
```
# desde la carpeta del repo, una sola vez:
git init
git add .
git commit -m "Estructura inicial: módulos + coordinación + baseline Fase 0"
git branch -M main
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```
Luego cada colaborador clona y sigue el flujo de arriba.
