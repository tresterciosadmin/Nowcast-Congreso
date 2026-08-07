# Corrida: backtest del embudo por las dos rutas (ADR-0009, paso final)

**Para:** Valle, en PowerShell · **Fecha:** 2026-08-07 · **Dura:** ~15-40 min las dos juntas
**Por qué a mano:** el sandbox corta a los ~45 s y los procesos en background no sobreviven.

> **Nada de esto pisa lo que funciona.** Las dos corridas escriben en `Archivos_Borrar/`.
> Recién en el paso 3, y sólo si el resultado convence, se promueve.

---

## 1 · Baseline nuevo (ruta vieja: parquet, SIN el bot)

⚠️ **Esto NO es el 0,3647 de Franco.** Ese número se midió con los datos de antes del refresco de
CKAN. Hace falta medir el baseline de nuevo para tener contra qué comparar.

```powershell
cd "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy"

$env:EMBUDO_FUENTE = "parquet"
$env:OUT           = "Archivos_Borrar\bt_parquet"
python variables\embudo\src\embudo.py modelo
```

**Tiene que decir:** `FUENTE: parquet` · `cohorte: 41470 proyectos de LEY` · y al final los dos
bloques `=== BACKTEST target=... ===`. **Anotá el `skill` del escalón (3) de `sancionado`.**

## 2 · Ruta nueva (SQLite, CON el bot)

```powershell
$env:EMBUDO_FUENTE = "auto"
$env:OUT           = "Archivos_Borrar\bt_sqlite"
python variables\embudo\src\embudo.py modelo
```

**Tiene que decir:** `FUENTE: sqlite` · `cohorte: 42141 proyectos de LEY` (671 más).

Y después la comparación:

```powershell
python -c "import json; a=json.load(open(r'Archivos_Borrar\bt_parquet\backtest_embudo.json',encoding='utf-8')); b=json.load(open(r'Archivos_Borrar\bt_sqlite\backtest_embudo.json',encoding='utf-8')); [print(f'{k:34} {a.get(k,{}).get(chr(115)+chr(107)+chr(105)+chr(108)+chr(108)+chr(95)+chr(115)+chr(99)+chr(111)+chr(114)+chr(101)) if isinstance(a.get(k),dict) else a.get(k)!s:>10} -> {b.get(k,{}).get(chr(115)+chr(107)+chr(105)+chr(108)+chr(108)+chr(95)+chr(115)+chr(99)+chr(111)+chr(114)+chr(101)) if isinstance(b.get(k),dict) else b.get(k)!s:>10}') for k in a]"
```

---

## Cómo leer el resultado (esto es lo importante)

**No hay un número "correcto" esperado.** Los datos cambiaron a propósito. Lo que hay que mirar es
la **dirección** y el **tamaño**:

| si pasa esto | qué significa |
|---|---|
| el skill queda **parecido** (±0,01) | ✅ lo esperable. Los 671 proyectos nuevos son pocos frente a 41.470 |
| el skill **sube** | ✅ bien, pero mirá que no sea por los cofirmantes solamente |
| el skill **baja poco** (−0,01 a −0,02) | 🟡 probablemente **dilución**: los 671 nuevos son de los últimos 5 meses y **ninguno pudo sancionarse todavía**. Entran como negativos "prematuros" y el modelo no tiene forma de acertarlos. No es un error: es que la cohorte incluye proyectos sin desenlace |
| el skill **se desploma** (>0,05) | 🔴 pará y avisame. Eso no lo explica la dilución |
| la **cohorte no da 42141** | 🔴 pará. Es el bug del `proyecto_id` nulo volviendo |

**El sospechoso número uno si algo sale raro:** la cohorte ahora mezcla proyectos maduros
(2008-2025, ya resueltos) con 671 de los últimos 5 meses **que no tuvieron tiempo de resolverse**.
La tasa base ya bajó por eso, de 3,21% a 3,16%. Si el skill cae, lo primero a probar es **recortar
la cohorte a proyectos con al menos N meses de antigüedad**, no desandar la carga.

---

## 3 · Promover (SÓLO si el paso 2 convence)

Esto además cierra un pendiente viejo: `p_embudo.parquet` es del 12-jul y se generó con el bug del
one-hot ya corregido.

```powershell
Copy-Item "Archivos_Borrar\bt_sqlite\p_embudo.parquet"      "variables\embudo\outputs\" -Force
Copy-Item "Archivos_Borrar\bt_sqlite\backtest_embudo.json"  "variables\embudo\outputs\" -Force
```

## 4 · Limpiar las variables (si no, quedan pegadas en esa ventana)

```powershell
Remove-Item Env:EMBUDO_FUENTE, Env:OUT
```

---

## Si algo falla

- **`FUENTE: parquet` cuando esperabas sqlite** → no encontró `proyectos.db`. Correr antes:
  `python datos\proyectos\src\migrar_ckan.py` y después `python datos\proyectos\src\upsert_bot.py`.
- **`disk I/O error`** → es el límite del mount del sandbox, **en Windows no debería pasar**. Si
  pasa igual, avisame.
- **Tarda muchísimo** → normal en el escalón (3); son 3 ablaciones × 2 targets, walk-forward.
- **Cualquier otra cosa** → pegame la salida entera, no el resumen.
