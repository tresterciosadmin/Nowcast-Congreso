# Cierre de la sesión del 04-08-2026 — qué subir y qué hacer después

> ## Estado de los 5 pendientes, verificado el 2026-08-06
>
> | # | Pendiente (sección 6) | Al 06-08 |
> |---|---|---|
> | 1 | Re-correr `embudo.py modelo` | 🔴 **sin hacer** — `p_embudo.parquet` sigue siendo el del 12-jul. Promovido a `URGENTE.md` ítem 1: el ensemble se apoya en la salida del modelo mutilado. |
> | 2 | URGENTE 0 — leakage de `n_giros` | 🔴 sin hacer — sigue siendo `URGENTE.md` ítem 0 |
> | 3 | Senado 2026 sin bloque en la ingesta | 🟡 **arreglado en código** el 06-08 (padrón vigente mandate-aware + 8 tests; los 72 senadores resuelven). Falta re-correr `run_pipeline.py` para que llegue a los parquet → `URGENTE.md` ítem 2. |
> | 4 | Enchufar el mecanismo 1 del ICG al ensemble | 🔴 sin hacer — espera que el equipo mire los paneles y fije γ |
> | 5 | Confirmar el padrón contra la API | ✅ **HECHO el 06-08** — lo hizo el propio `padron-vivo #1` contra la API en vivo. Resultado: el padrón versionado coincide con la fuente, pero **da 256, no 257** (ver la corrección más abajo). |
>
> El **PASO 4 del runbook** (mover los workflows a la raíz) tampoco se había
> hecho — **se hizo el 06-08**. `padron-vivo` corrió por primera vez (`#1`) y
> salió verde; `bot-diario` se mergeó con los avisos que le faltaban e
> `icg-mensual` sigue sin estrenar. Detalle en `URGENTE.md` ítem 3.
>
> *(Banner agregado el 06-08 por la auditoría general. Este archivo es el cierre
> de UNA sesión: para saber qué está pendiente HOY, la fuente es `URGENTE.md`.)*

Todo está escrito, testeado y registrado. Este archivo es la checklist para
publicar y para no perder los pendientes.

## 1 · Antes de commitear (2 minutos)

En PowerShell, parada en la carpeta del proyecto:

```powershell
$criticos = @(
  "datos\padron\data\padron_senado.csv",
  "datos\padron\data\padron_diputados.csv",
  "datos\padron\data\senado_linaje_manual.csv",
  "datos\padron\data\raw\nomina_senado.csv",
  "variables\proyecto\data\icg_mensual.csv",
  "variables\proyecto\data\icg_contexto.parquet",
  "variables\proyecto\data\calendario_electoral.csv",
  "variables\proyecto\data\curva_ciclo_presidencial.csv"
)
foreach ($f in $criticos) {
  git check-ignore -q $f
  if ($LASTEXITCODE -eq 0) { Write-Host "IGNORADO  $f" -ForegroundColor Red }
  else                     { Write-Host "OK viaja  $f" -ForegroundColor Green }
}
```

Todos tienen que salir en verde. Ya se les agregó la excepción en el
`.gitignore` de esta sesión, pero el chequeo cuesta diez segundos y es lo que
destapó el problema del padrón del Senado.

## 2 · Borrar antes de subir

`.github\workflows\bot-diario.yml` de **esta carpeta** duplica el bot que ya
corre. Está neutralizado (sin disparadores automáticos) pero hay que borrarlo,
junto con `BORRAR-bot-diario.md`. Detalle en `Archivos_Borrar\PENDIENTES-DE-BORRAR.md`.

Y los dos workflows que sí sirven van **a la raíz del repo**, un nivel arriba:
ver el PASO 4 de `PUESTA-EN-MARCHA-2026-08-04.md`.

## 3 · Texto del commit

```
sesion 04-08: el ICG pasa a ser modulador de coyuntura (ADR-0008)

MODELO
- ICG deja de ser un rasgo del embudo (aportaba 0) y pasa a modulador,
  con dos mecanismos independientes.
- Mecanismo 1 (MEDIDO): variacion dentro del gobierno, aplicada legislador
  por legislador. gamma 0,22 a 0,56 segun cuan discolo, con dosis-respuesta,
  estimado sobre 410k votos con efectos fijos por legislador.
- Mecanismo 2 (DECLARADO): nivel vs break-even 1,90, forma acelerada con
  aversion a la perdida. gamma lo asigna un analista humano.
- REQUISITO NUEVO: ningun nowcast se publica sin evaluacion de coyuntura
  registrada (PANEL-COYUNTURA.html / PANEL-MOVIL.html).

DATOS
- Padron de Diputados regenerado: 257 exactos. ⛔ **CORREGIDO 2026-08-06: es FALSO, da 256.** Verificado contra la API en vivo (`padron-vivo #1`) y contra el archivo: `padron_diputados.csv` da 256 vigentes en todas las fechas de agosto, incluido el 04-08, y el `.bak` previo también. Nunca dio 257. La banca faltante es la de **Pitrola** (`hasta = 2026-04-27`), vacante desde abril.
- vigilar_padron.py: vigilante semanal de altas, bajas y pases de bloque.
- calendario_electoral.csv y curva_ciclo_presidencial.csv, curados a mano.

INFRA
- 2 workflows nuevos en Actions: padron los lunes, ICG el dia 5.

BUGS CORREGIDOS
- construir_features rechazaba en SILENCIO las comisiones leidas de parquet:
  25 columnas quedaban en cero sin avisar.
- CLAUDE.md estaba truncado en disco desde una sesion vieja.
- La correlacion -0,54 entre bancas e ICG es el calendario de recambio, no
  una relacion causal.

Tests: 18 + 17 + 15 + 20 + 21 en verde.
```

## 4 · Qué mirar del trabajo

| Archivo | Para qué |
|---|---|
| `PANEL-MOVIL.html` | **empezá por acá** — teléfono, 12 proyectos en vivo |
| `PANEL-COYUNTURA.html` | lo mismo para escritorio, con más detalle |
| `COMPARADOR-ICG.html` | para decidir en equipo: las dos vías y las 4 preguntas abiertas |
| `coordinacion/DECISIONES/0008-...md` | el ADR con todo el razonamiento |

## 5 · Decisiones que quedan para el equipo

1. **¿Qué γ se usa?** Hoy no hay default. Con 0,10 el clima mueve 22 votos punta
   a punta; con 0,20, 43. La prueba de realidad está en el panel: si el γ elegido
   no le alcanza al oficialismo para explicar la Ley Bases, se está quedando corto.
2. **Los 104 sin historial.** La camada de dic-2025 se trata como núcleo duro por
   defecto. Es un supuesto, no una medición. La alternativa es darles el desvío
   promedio de su bloque hasta que se midan solos.
3. **¿Se le da algo al núcleo duro?** Su γ propio es −0,03 con 50% de probabilidad
   de ser positivo: una moneda al aire. Hoy están en cero.

## 6 · Pendientes técnicos, en orden

1. **Re-correr `embudo.py modelo` completo** en la PC. El `p_embudo.parquet` que
   consume el ensemble se generó con el modelo mutilado por el bug del one-hot.
   El sandbox no lo termina.
2. **URGENTE 0 — el leakage de `n_giros`.** Sigue siendo el que puede invalidar el
   skill entero, y es el rasgo más pesado del modelo (68% con las comisiones).
3. **El Senado 2026 sin bloque en la canónica.** El padrón correcto existe; la
   ingesta (`to_canonical.py`) todavía lee el viejo, que termina el 09-dic-2025.
4. **Enchufar el mecanismo 1 al ensemble.** Está implementado y testeado pero no
   conectado.
5. **Confirmar el padrón contra la API** (`bajar_nomina.py diputados --padron`).

## 7 · Lo que se probó y no funcionó

Vale tenerlo a mano para no repetirlo:

- **La volatilidad del ICG no modula la elasticidad.** +0,045 con IC [−0,12; +0,09].
- **No hay efecto del clima a nivel cámara.** El promedio de 69 votos por acta no
  tiene resolución para ver un efecto de 10-20 bisagras.
- **El nivel absoluto no se puede estimar.** Con seis presidencias, "ICG alto" y
  "este gobierno" son la misma columna. Por eso el mecanismo 2 es declarado.
