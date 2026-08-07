# Módulo: datos/proyectos

**Propósito.** La **base de Proyectos de Ley**: fuente de verdad del embudo. Una fila por proyecto, identificado por su **denominador** (`NNNN-X-AAAA`). Guarda metadata, autores, giros a comisiones, trámite, estado y taxonomías. Se actualiza en el tiempo sin duplicar (un mismo proyecto avanza de estado).

**Estado:** EN CURSO — **la base existe y es la fuente de verdad del universo de proyectos** (ADR-0009, 2026-08-07).

> ✅ **`data/proyectos.db` creada el 2026-08-07: 114.708 proyectos, 89 MB.**
> *(Este README decía hasta ese día "la base nunca se creó". Era cierto desde junio
> y dejó de serlo; se corrige acá porque un README desactualizado es el mecanismo
> anti-colisión fallando al revés — ya pasó con cinco módulos el 06-08.)*
>
> **Qué contiene y de dónde sale:**
>
> | fuente | qué aporta |
> |---|---|
> | backfill de CKAN (`datos/expedientes`) | 113.177 proyectos 2008 → 30-jun-2026, con trámite, dictámenes y resultados |
> | bot (`datos/bot_recoleccion`) | +1.531 proyectos hasta el **05-ago-2026**, los **cofirmantes completos** y el giro **medido** al ingresar |
>
> **Quién la consume:** `variables/embudo` lee de acá (`cargar_sqlite()`). La ruta
> vieja de parquet sigue viva como *fallback* con `EMBUDO_FUENTE=parquet`.
>
> **No viaja a git** (`*.db`, decisión previa y correcta: 89 MB binarios y cada
> regeneración quedaría en el historial para siempre). **Se reconstruye en ~1 minuto**
> desde fuentes versionadas:
>
> ```bash
> python datos/proyectos/src/migrar_ckan.py    # CKAN -> base (25 s)
> python datos/proyectos/src/upsert_bot.py     # + el bot (20 s)
> ```
>
> ⚠️ **Lo único NO reconstruible es `proyecto_taxonomias`** — la llena el agente y
> cuesta llamadas a la API. **Antes de que el agente escriba, hay que exportarla a un
> archivo versionado** (pendiente en `URGENTE.md`).

## Cuarentena: lo dudoso va aparte

Decisión de Valle (07-08): *"los pendientes de revisión van a una base de datos
distinta y los que están bien pasan a la base general"*. **Separación física, no una
etiqueta** — si una fila está en `proyectos.db`, se leyó bien.

- `data/cuarentena.db` guarda la fila cruda entera + el motivo. **Sí viaja a git**
  (pesa kilobytes y la mira una persona; excepción explícita en el `.gitignore`).
- Ver qué hay esperando: `python src/cuarentena.py`
- **Una fila rara no frena la carga; una avalancha sí.** >5% de una tanda en
  cuarentena = la fuente cambió de formato. Con piso de 10 filas, para que una tanda
  chica del bot diario no aborte por un caso suelto.

## Control de integridad

`src/verificar.py` — **14 invariantes que cortan con `exit 1`**. `migrar_ckan.py` y
`upsert_bot.py` lo corren solos al terminar.

Existe porque el 07-08 tres errores de carga **no dieron error**: la cohorte subió +1
en vez de +671, el giro corregido bajó de 633 a 559, y 34 expedientes del Ejecutivo se
descartaron como "formato inesperado". Los tres se encontraron mirando si el número era
el esperado, no viendo si el programa terminaba bien.

`tests/test_verificar.py` **rompe la base a propósito**, cada vez de la forma exacta en
que se rompió de verdad, y exige que el control lo detecte (10 tests). *Un control que
nunca se dispara no protege de nada.*

## Contrato
- **Entrada:** un dict con la forma de `FichaExpediente` (la salida de `datos/seguimiento`, serializada con `asdict`/JSON). El módulo **no importa código** de seguimiento; consume el contrato (dict).
- **Salida:** base SQLite `data/proyectos.db` (fuente de verdad) + export a Excel legible (`export_excel`).
- **Formato:** SQLite. Una tabla `proyectos` + hijas `proyecto_autores`, `proyecto_giros`, `proyecto_tramite`, `proyecto_taxonomias`. Ver `src/schema.sql`.

## Uso (CLI)
```bash
python src/store.py init   data/proyectos.db
python src/store.py cargar data/proyectos.db ficha.json            # objeto o lista de fichas
python src/store.py export data/proyectos.db Archivos_Borrar/proyectos.xlsx   # Excel multi-hoja
python src/store.py csv    data/proyectos.db Archivos_Borrar/proyectos_csv    # un CSV por tabla
```
Donde `ficha.json` es lo que imprime `datos/seguimiento/src/giros.py`. En código:
```python
from store import conectar, upsert_proyecto, export_excel
con = conectar("data/proyectos.db")
upsert_proyecto(con, ficha_dict); con.commit()
```

## Reglas de refresco (clave)
- `proyectos`, `proyecto_autores`, `proyecto_giros`, `proyecto_tramite` **se refrescan**
  en cada scrape (reflejan el estado oficial actual). `creado_en` se preserva; `actualizado_en` se renueva.
- `proyecto_taxonomias` **NO la toca el scraper**: la llena el agente de taxonomías y
  se conserva entre scrapes. Cada taxonomía tiene `taxonomia_id` (ID estable) + nombre + confianza.
- Idempotente por denominador: re-cargar el mismo proyecto **no duplica**, actualiza.

## Formato de export (universal, sin separadores en celdas)
Nada de "valor | valor" dentro de una celda. Lo multivaluado va **normalizado**:
- **Excel**: una **hoja por tabla** (`Proyectos`, `Autores`, `Giros`, `Tramite`, `Taxonomias`),
  cada una limpia y unida por `denominador`.
- **CSV**: un archivo por tabla, **UTF-8 con BOM** (`utf-8-sig`, abre con acentos en Excel-ES),
  coma estándar y comillas automáticas (los nombres con coma quedan `"Apellido, Nombre"`).

Ambos son cruzables por cualquier herramienta (Excel, pandas, Power BI, R) sin parsear texto.

## Estado (embudo)
`ingresado → en_comision → con_dictamen → media_sancion → sancionado` (o `rechazado`).
Derivado del trámite/giros en `datos/seguimiento`; acá se guarda tal cual.

## Test
`python tests/test_store.py` (sin red): init, upsert, idempotencia, preservación de
taxonomías y export a Excel.

## Pendiente
- El `.db` es la fuente de verdad: definir si se versiona o se sincroniza aparte (no conviene
  commitear el binario al repo; el Excel exportado puede ir a `Archivos_Borrar/`).
- Conectar el flujo completo: `seguimiento` (giros) → `upsert_proyecto` en lote.
- Falta el **agente de taxonomías** que llene `proyecto_taxonomias` desde el PDF.
- Bases hermanas que vendrán después: parlamentarios, partidos (la de votaciones ya existe: `datos/canonica`).
