# Puesta en marcha — lo que queda de la sesión del 04-08-2026

Todo el código está escrito, testeado y corriendo en seco. **Lo que falta es
operativo, no de programación:** conectar la carpeta a git y ver a los tres
workflows correr una vez cada uno.

Tiempo estimado: **30-40 minutos**, casi todo esperando.

> **Regla para todo lo que sigue:** ningún paso avanza si el anterior no dio lo
> que dice "Tiene que dar". Si algo no coincide, parás y lo miramos — seguir
> encima de un paso que falló es como se acumulan los problemas que después
> aparecen en URGENTE.

---

## Estado antes de empezar

| Pieza | Estado |
|---|---|
| ICG enchufado al embudo | ✅ hecho y medido |
| Padrón de Diputados a 257 | ✅ **ya aplicado** (backup en `padron_diputados.ANTES-2026-08-04.csv.bak`) |
| Vigilante del padrón | ✅ corre limpio en seco |
| 3 workflows escritos | ✅ YAML validado |
| Tests | ✅ 18 + 17 + 15 + 21 en verde |
| Carpeta conectada a git | ✅ ya lo estaba (GitHub Desktop, rama `main`) |
| **Workflows corriendo en GitHub** | ❌ falta |

---

## PASO 1 — Chequeo local antes de tocar git (5 min)

Abrí PowerShell y pegá esto tal cual:

```powershell
cd "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy"

python variables\embudo\tests\test_embudo.py
python variables\embudo\tests\test_embudo_icg.py
python datos\padron\tests\test_vigilar_padron.py
python variables\proyecto\tests\test_ingesta_icg.py
```

**Tiene que dar:** `18 chequeos OK`, `17 chequeos OK`, `15 chequeos OK`,
`21 chequeos OK`.

Si alguno falla por un import (`No module named sklearn`, `pyarrow`, etc.):

```powershell
pip install -r variables\embudo\src\requirements.txt
pip install pandas requests
```

---

## PASO 2 — El padrón, verificado contra la fuente viva (3 min)

En esta sesión regeneré el padrón desde el crudo que ya tenías en disco y da
257. Falta confirmarlo contra la API, que es la fuente real (mi entorno no
llega a internet).

```powershell
python datos\padron\src\bajar_nomina.py diputados --padron
python datos\padron\src\vigilar_padron.py --camara ambas
```

**Tiene que dar:** `bancas vigentes al ...: 257` y después
`🟢 Sin novedades`, con Diputados en **257** y Senado en **72**.

**Si da otra cosa:** no lo arregles a mano. El vigilante te va a listar quién
sobra o falta — mandámelo y lo miramos. Ya sabemos que esta fuente carga mal
algunos tramos (fin antes que inicio) y que taparlo a ciegas da 278 o 263.

---

## PASO 3 — Commitear y pushear desde GitHub Desktop (10 min)

> **Corrección del 04-08:** este paso decía "conectar la carpeta a git". Estaba
> mal: el repo siempre estuvo conectado. Ver `coordinacion/CONECTAR-GIT.md`.

Tenés **25 archivos cambiados** esperando en GitHub Desktop. Antes de commitear:

### 3.a — Confirmar que no falta nada en la lista

Bajá hasta el final de la lista de archivos y **verificá que estén estos dos**:

- `variables\proyecto\data\icg_mensual.csv`
- `variables\embudo\tests\test_embudo_icg.py`

**Si `icg_mensual.csv` NO aparece**, el `.gitignore` todavía se lo está comiendo
y el workflow del ICG no va a poder actualizarlo. Avisame antes de pushear.

Los que ya confirmaste que están —`padron_senado.csv`, `nomina_senado.csv` y
`senado_linaje_manual.csv`— son los importantes: llevaban semanas invisibles y
son los que causaron la urgencia falsa del Senado.

### 3.b — El chequeo del `.gitignore` (opcional pero recomendado)

Está en `coordinacion/CONECTAR-GIT.md`. Tarda 10 segundos y es la verificación
que destapó el problema del Senado.

### 3.c — Commitear

**Summary:**

```
sesion 04-08: ICG al embudo, padron vivo y los tres cron en Actions
```

**Description:**

```
- ICG enchufado al embudo, rezagado un mes (anti-leakage). Aporta +0,003
  de skill; la deriva a 3 meses pesa 6x mas que el nivel.
- datos/padron/vigilar_padron.py: vigilante semanal de altas, bajas, pases
  de bloque y total != 257/72. Idempotente.
- Padron de Diputados regenerado: 257 exacto (aparecen Matzkin y Pitrola).
- 3 workflows de GitHub Actions: bot diario, padron los lunes, ICG el dia 5.
- .gitignore: el padron del Senado estaba oculto y genero una urgencia falsa.
- Tests: 18 + 17 + 15 + 21 en verde.
```

Después **Commit to main** y **Push origin**.

### 3.d — Si el push rebota

Si Franco pusheó mientras tanto, GitHub Desktop te va a ofrecer **Pull origin**
primero. Aceptá, revisá que no haya conflictos en `ESTADO-DEL-PROYECTO.md` (es el
archivo que más se toca desde los dos lados) y volvé a pushear.

---

## PASO 4 — Mover los workflows a la RAÍZ del repo y borrar el duplicado (5 min)

> **Corrección del 04-08.** Escribí `.github/workflows/` dentro de
> `Nowcast Congreso Argy\`, pero **la raíz del repo está un nivel más arriba**
> (`Nowcast-Congreso\`, como muestra la ruta del runner). GitHub sólo lee
> `.github/workflows/` de la raíz: ahí donde están, los tres nunca se dispararían.

### 4.a — Borrar el duplicado

`Nowcast Congreso Argy\.github\workflows\bot-diario.yml` **duplica el
workflow que ya viene corriendo** ("Bot diario (padrón vivo)"). Borralo, junto
con `BORRAR-bot-diario.md` (que explica las dos mejoras que tiene, por si querés
pasarlas al que ya existe).

### 4.b — Mover los otros dos a la raíz

```powershell
$sub  = "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy"
$raiz = "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso"

Remove-Item "$sub\.github\workflows\bot-diario.yml"
Remove-Item "$sub\.github\workflows\BORRAR-bot-diario.md"
Move-Item   "$sub\.github\workflows\padron-vivo.yml"  "$raiz\.github\workflows\"
Move-Item   "$sub\.github\workflows\icg-mensual.yml"  "$raiz\.github\workflows\"
Remove-Item "$sub\.github" -Recurse

Get-ChildItem "$raiz\.github\workflows"
```

**Tiene que dar:** el workflow del bot que ya existía, más `padron-vivo.yml` e
`icg-mensual.yml`. Las rutas internas de esos dos ya llevan el prefijo
`"Nowcast Congreso Argy/"` entrecomillado, igual que el que ya funciona.

---

## PASO 5 — Darle permiso de escritura a los workflows (2 min)

**Este es el paso que más se olvida y sin él los tres bots fallan al pushear.**

En el navegador:

1. Entrá a `https://github.com/tresterciosadmin/Nowcast-Congreso`
2. **Settings** → **Actions** → **General**
3. Bajá hasta **Workflow permissions**
4. Marcá **Read and write permissions**
5. Marcá también **Allow GitHub Actions to create and approve pull requests**
6. **Save**

Mientras estás ahí, confirmá que en la pestaña **Actions** los workflows no
aparezcan como deshabilitados (en repos que estuvieron inactivos, GitHub a veces
los pausa y hay un botón para reactivarlos).

---

## PASO 6 — Probar los DOS workflows nuevos (10 min)

Cada uno tiene botón manual. **Corrélos en este orden**, de menos a más
invasivo: si algo está mal configurado, lo vas a descubrir con el más inocuo.

Para cada uno: pestaña **Actions** → elegí el workflow en la lista de la
izquierda → botón **Run workflow** → **Run workflow**.

### 5.a — `icg-mensual` (el más inocuo: sólo lee y agrega un mes)

Dejá el modo en `ultimo`.

**Tiene que dar:** verde. Casi seguro **no commitea nada** — ya tenés hasta
junio-2026 y el mes nuevo entra recién cuando UTDT lo publique. Eso está bien:
"sin mes nuevo: no commiteo" es el resultado esperado.

**Si falla:** casi siempre es que UTDT cambió el layout del Excel o movió la
página. Volvé a correrlo con el modo `serie`, que rebaja el histórico completo.
El workflow te abre un issue explicando esto solo.

### 5.b — `padron-vivo` (lee, compara y puede abrir un issue)

**Tiene que dar:** verde, y el reporte con **257 / 72**. Si hiciste el PASO 2,
lo más probable es `🟢 Sin novedades` y que no abra ningún issue.

**Lo que confirma este paso:** que el bot puede **commitear** (escribe
`estado_vigilancia.json`) y que puede **abrir issues**. Son los dos permisos
del PASO 4. Si falla en el paso "Commitear reporte y memoria", volvé al PASO 4.

### El bot diario NO hace falta probarlo

Ya viene corriendo solo desde julio (corrida #22 al 04-08) y en la última trajo
15 proyectos nuevos del Trámite Parlamentario. No se toca.

**Un detalle del log que conviene tener anotado:** el scraper de Diputados falla
la verificación SSL contra `hcdn.gob.ar` y reintenta con `verify=False`. Funciona,
pero es un parche: si algún día ese sitio cambia de certificado o alguien se mete
en el medio, no nos vamos a enterar. No es urgente; queda anotado.

---

## PASO 7 — Confirmar que los horarios quedaron activos (1 min)

En **Actions**, cada workflow tiene que mostrar el ícono de reloj (schedule).

| Workflow | Cuándo corre |
|---|---|
| `bot-diario` | lun-sáb 07:00 ARG |
| `padron-vivo` | lunes 08:00 ARG |
| `icg-mensual` | día 5, 09:00 ARG |

**Dato de GitHub que conviene saber:** los cron pueden atrasarse hasta 30-40
minutos cuando hay mucha carga, y **GitHub deshabilita los schedules de un repo
sin actividad durante 60 días**. Con el bot commiteando todos los días eso no va
a pasar, pero si alguna vez el proyecto queda quieto dos meses, hay que
reactivarlos a mano.

---

## PASO 8 — Cerrar la sesión en las bitácoras (5 min)

Cuando los tres corrieron bien:

1. En `coordinacion/URGENTE.md`, **borrá el ítem 1** (regenerar el padrón): ya
   está hecho. El registro permanente queda en ESTADO.
2. En `coordinacion/TABLERO.md`, liberá los módulos reclamados el 04-08.
3. `git add -A && git commit -m "puesta en marcha: los tres cron andando" && git push`

---

## Lo que NO queda operativo con esto (y es a propósito)

Para que no haya sorpresas, esto queda pendiente y **no** es parte de esta
puesta en marcha:

- **La canónica del Senado 2026 sigue entrando sin bloque.** El padrón correcto
  existe, pero la ingesta (`datos/argentinadatos/src/to_canonical.py`) todavía
  lee el padrón viejo que termina el 09-dic-2025. Está anotado en URGENTE con el
  diagnóstico completo. **El nowcast de Diputados es usable; el del Senado no.**
- **El leakage de `n_giros` (URGENTE 0)** sigue abierto. Es el que puede
  invalidar el skill entero y es lo próximo que conviene mirar.
- **Las 15 jefaturas sin confirmar** (URGENTE 3), de prioridad baja desde que se
  midió que el jefe de bloque aporta 1,25x y no 7x.

---

## Si algo se rompe

Todo lo de esta sesión es reversible:

- El padrón viejo está en `datos/padron/data/padron_diputados.ANTES-2026-08-04.csv.bak`.
- Tenés la copia de seguridad hecha, y además todo el historial en GitHub:
  cualquier commit se revierte desde GitHub Desktop (History → botón derecho →
  *Revert changes in commit*).
- Los workflows se desactivan desde Actions → el workflow → `...` → *Disable*.
- El ICG se puede apagar sin tocar código: si `variables/proyecto/data/icg_mensual.csv`
  no está, el embudo corre igual sin la variable (lo verifica un test).
