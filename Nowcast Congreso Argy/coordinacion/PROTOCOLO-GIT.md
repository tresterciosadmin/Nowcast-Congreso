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

## GitHub — el repo YA está creado y conectado

**Repositorio:** https://github.com/tresterciosadmin/Nowcast-Congreso ·
**Rama de trabajo:** `main` · Valle trabaja con **GitHub Desktop**.

Acá había un instructivo de `git init` / `git remote add` para el primer setup.
**Se sacó el 2026-08-06** porque ya no aplica y porque el 04-08 esa idea —"esto
todavía no está conectado"— generó un documento entero equivocado
(`CONECTAR-GIT.md`). Un instructivo de inicialización que sobrevive al proyecto
inicializado es una invitación a repetir el error.

Un colaborador nuevo **clona**, no inicializa:

```
git clone https://github.com/tresterciosadmin/Nowcast-Congreso.git
```

⚠️ **Ojo con el anidamiento doble.** La raíz del repo es
`Nowcast-Congreso\Nowcast-Congreso`, y el proyecto vive en el subdirectorio
`Nowcast Congreso Argy\`. Consecuencias:

- `.github/workflows/` va **en la raíz**, no en el subdirectorio. Lo que se
  escriba adentro, GitHub no lo lee nunca (pasó el 04-08 con dos workflows que
  siguen sin correr — ver `URGENTE.md`).
- Las rutas dentro de un workflow llevan el prefijo `"Nowcast Congreso Argy/"`
  **entrecomillado** (tiene espacios).
- Los comandos de git que reciben una ruta (`git check-ignore`, `git log <file>`)
  hay que correrlos desde la raíz con ruta root-relative, o fallan.

## Antes de commitear: el chequeo del `.gitignore` (10 segundos)

Las reglas `*.csv`, `*.parquet` y `**/data/clean/` **ya escondieron trabajo
cuatro veces** (parquet de expedientes 11-07, roster de jefes 30-07, salidas del
embudo 31-07, padrón del Senado 04-08 — este último generó una urgencia falsa que
costó días). Al crear la salida de un módulo nuevo, decidí **en el mismo commit**
si entra al régimen transitorio, y verificá:

```powershell
git add -n <archivo>   # ARCHIVO NUEVO: si imprime `add '<ruta>'`, VIAJA.

# Para auditar archivos que YA estan en el repo, `add -n` NO sirve (un archivo
# trackeado y sin cambios tampoco imprime nada). Ahi va:
git check-ignore -v --non-matching -- <rutas>   # ignorado si la regla NO empieza con !
```

**No uses `git check-ignore -q`.** Devolvia 0 tambien cuando matchea una
**excepcion** (`!...`), o sea justo sobre los archivos que rescatamos a mano,
y el `-q` esconde cual fue la regla. Leerlo como "esta ignorado" es al reves.
Ver **ADR-0011**. Si queres ver POR QUE, `git check-ignore -v <archivo>` y mira
la regla: si empieza con `!`, el archivo viaja.

**Y la ruta va relativa a donde estas parado.** El prefijo
`"Nowcast Congreso Argy/"` es correcto **desde la raiz git** y veneno desde
adentro del proyecto: ahi arma una ruta que no existe, no le pega a ninguna
excepcion, cae en `*.csv` y un archivo sano se ve ignorado. No falla: contesta
otra cosa.
