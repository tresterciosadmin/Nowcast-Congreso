# LIMPIEZA 2026-09 — línea de base y veredictos

**Resumen:** El registro de la limpieza descrita en `PLAN-LIMPIEZA-2026-09.md`: la línea de
base medida antes de tocar nada, y el veredicto de cada archivo a medida que se revisa.
**Es un archivo temporal**: cuando la limpieza cierra, lo que quede vivo se pasa a
`ESTADO-DEL-PROYECTO.md` y este archivo se borra. No es un sexto documento vivo.

## Buscar acá si

- querés saber por qué un archivo se archivó, se fusionó o se dejó como estaba
- estás retomando la limpieza a mitad de camino y necesitás saber dónde quedó

---

## Línea de base — medida el 2026-09-08, ANTES de tocar nada

Contra esto se compara el cierre (fase 6). Si algo de acá cambia, la limpieza está mal.

| control | resultado |
|---|---|
| árbol de git | **limpio** (`git status --porcelain` vacío, incluidos untracked) |
| último commit | `b1ccd4d` "limpieza" (2026-09-07) |
| `pytest tests/ datos/proyectos/tests -q` | **30 passed** en 30 s |
| `verificar_regeneracion.py` | **16 OK · 0 a mirar · 0 sin poder leer** |
| **P(aprob) del panel de puertas** | **0,9801** (mayoría absoluta 129, simulado 122,5, afirmativos esperados 151,1, margen +28,6) |
| β ambas cámaras | n_actas 1.549 · n_votos 245.883 · β₁ 2,1045 · β₂ 2,138 (p=0,0) |
| β sólo Senado | n_actas 449 · n_votos 26.100 · β₁ 1,9931 · β₂ 1,681 (p=0,00176) |
| enlace acta→expediente | 5.004 filas (2.719 Senado + 2.285 Diputados) |
| `MAPA.md` | 414 líneas (presupuesto 460) |
| índice | 162 archivos · 38.865 LOC · 77 carpetas |
| inventario de datos | 140 archivos · 195,2 MB · 105 viajan por git, 35 no |

**Dónde se corrió:** Linux (Python 3.10.12, pandas 2.3.3, numpy 2.2.6, pyarrow 25.0.1,
statsmodels 0.15.0), no en la PC de Franco. Vale la advertencia del CLAUDE.md: *"pasa en el
sandbox" no es "pasa"*. La corrida que manda es la de Franco:

```powershell
python -m pytest tests/ datos/proyectos/tests -q
python verificar_regeneracion.py
```

## Lo que la fase 0 encontró de paso

1. **URGENTE ítem N.1 ya está resuelto y todavía figura como pendiente.**
   `datos/canonica/data/alias_legislador_id.csv` **sí está versionado**
   (`git ls-files` lo lista), igual que `legislador_id_merge_aprobado_2026-09-04.csv`
   y `datos/taxonomias/data/asignaciones.csv`. El commit que faltaba se hizo. Se borra
   de `URGENTE.md` en el cierre, junto con lo demás que se resuelva.

2. **`--estructura` sub-reporta las bitácoras vencidas: dice 7, son 27.**
   `diagnostico()` (línea 911 de `.mapa/indexar.py`) saltea toda carpeta con
   `archivos == 0`, y un módulo cuyo código vive en `src/` tiene 0 archivos propios.
   Por eso `--estructura` sólo ve `./`, `casos/`, `coordinacion/`, `datos/decada_votada/`,
   `docs/taxonomias/`, `modelo/ensemble/` y `variables/bloque/`, mientras la sección
   **Frescura** del MAPA (que no filtra) lista las 27 reales. El número bueno es 27.
   Candidato a arreglo en la fase 4: es el diagnóstico mintiendo sobre sí mismo.

3. **Los nueve restos de la fase 2 están confirmados: nadie los ejecuta ni los importa.**
   Medido con `git grep --cached` sobre todo el repo. Las únicas menciones son
   documentación (`coordinacion/README.md` los describe como "ya ejecutados y
   NEUTRALIZADOS", el plan de limpieza y este archivo). `_patch_tablero_v2.py` tiene una
   sola línea y dice de sí mismo **"OBSOLETO"**.
   Aparece además un resto que el plan no listaba y `ESTADO-DEL-PROYECTO.md` ya había
   anotado: **`_prueba.txt`** (3 bytes, raíz). El otro que esa entrada nombraba, `_wtest`,
   **ya no existe** — verificado en disco, no copiado de la bitácora.

4. **El hook `pre-commit` NO está instalado.** `.git/hooks/` sólo tiene los `.sample` de
   git. El CLAUDE.md lo da por puesto ("reindexa solo y avisa si algún README quedó
   vencido"), y es parte de por qué hay 27 bitácoras vencidas: nadie recibió el aviso.
   Se instala con
   `powershell -ExecutionPolicy Bypass -File "Nowcast Congreso Argy\.mapa\instalar-hook.ps1"`
   desde la raíz git. **Lo corre Franco**, y conviene hacerlo recién al cerrar la limpieza:
   con 27 bitácoras vencidas hoy, avisaría en cada commit.

## Veredictos

_(se completa a partir de la fase 1)_
