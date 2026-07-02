# Módulo: datos/export

**Propósito.** La base de votaciones armonizada en formatos consultables: un **SQLite único para el programa** y **Excel por gobierno para humanos**. Solo LEE la canónica (no toca código de otros módulos).

**Estado:** EN CURSO — v1 (falta corrida completa de los Excel en PC del equipo)
**Owner actual:** Claude+Valle (desde 2026-07-02)

## Contrato
- **Entradas:** `datos/canonica/data/clean/{actas_canonico,votos_resuelto}.parquet`. Opcional: `variables/legislador/data/{legisladores,legislador_periodo}.parquet` (se incluyen como tablas del .db).
- **Salidas** en `data/`:
  - `congreso.db` — SQLite con tablas `actas`, `votos`, `legisladores`, `legislador_periodo`. **NO se versiona** (~250MB, regenerable; supera el límite de GitHub).
  - `votaciones_<gobierno>.xlsx` — un Excel por gobierno, hojas **Metodologia / Actas / Votos**. Actas incluye `margen_votos` (afirmativos − umbral, con signo) para filtrar con cualquier vara sin recalcular. Se separan por gobierno porque los 835k votos no entran en una hoja de Excel. SÍ se versionan (transitorio, ver .gitignore).

## Definiciones clave (detalle en la hoja Metodologia de cada Excel)
- **DISPUTADA** (definición de Valle, 2026-07-02): el resultado quedó a **±5% de los votos emitidos ese día** respecto del **umbral de la mayoría requerida** para esa votación. El umbral depende del `tipo_mayoria` y de los presentes (mayoría simple = sobre los emitidos, NO un número fijo); el margen del 5% se calcula sobre los emitidos para que escale igual en ambas cámaras. Reemplaza al proxy anterior "minoría ≥10%". Resultado: **190 disputadas en 2001–2026** (validado: Ley Bases 2024, jubilaciones 2024 perdida por 1 voto; pico en Milei con 57, mínimo en CFK-2 con 11). Se evaluaron 4 interpretaciones del ±5% (umbral/emitidos/miembros/fijo → 96/190/248/516); Valle eligió emitidos.
- **Umbrales:** SIMPLE = emitidos/2 · ABSOLUTA = 129 (Dip) / 37 (Sen) · DOS_TERCIOS = 2/3 de emitidos (o del cuerpo si la fuente lo dice) · TRES_CUARTOS = 3/4 de emitidos. Sin dato → SIMPLE.
- **GOBIERNO:** cortes por fecha exacta de asunción (2001–2003 irregulares por la crisis: De la Rúa hasta 20-dic-2001, Duhalde desde 21-dic-2001, Kirchner desde 25-may-2003; después siempre 10-dic).

## Cómo correr
```bash
pip install xlsxwriter                                    # una vez
python datos/export/src/export_base.py all                # db + todos los Excel
python datos/export/src/export_base.py db                 # solo SQLite
python datos/export/src/export_base.py xlsx 2023-2027_Milei   # un gobierno puntual
python datos/export/tests/test_export.py                  # tests sin red (24 chequeos)
```
Cerrar los Excel abiertos antes de correr (Windows bloquea los archivos abiertos).

## Pendientes conocidos
- Columna `desvio` en la tabla Votos (pedido de Valle, definición en discusión — próximo paso).
- Unificar la definición de "disputada" hacia atrás: `modelo/voto_individual` y `evaluacion/baseline` aún usan el proxy "minoría ≥10%" (coordinar; el baseline es de Franco).
- `TRES_CUARTOS` asumido sobre emitidos (revisar si alguna fuente lo define sobre el cuerpo).
