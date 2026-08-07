# Módulo: datos/proyectos

**Propósito.** La **base de Proyectos de Ley**: fuente de verdad del embudo. Una fila por proyecto, identificado por su **denominador** (`NNNN-X-AAAA`). Guarda metadata, autores, giros a comisiones, trámite, estado y taxonomías. Se actualiza en el tiempo sin duplicar (un mismo proyecto avanza de estado).

**Estado:** EN CURSO — el código está y funciona, **pero la base nunca se creó**.

> 🔴 **Verificado el 2026-08-06: `data/proyectos.db` NO EXISTE, la carpeta está vacía.**
> El esquema, el upsert idempotente y el export están escritos y testeados (18
> chequeos), pero nadie corrió `store.py init` ni conectó nada. Consecuencias, en
> orden de importancia:
>
> 1. **El bot recolecta proyectos y no tienen dónde entrar.** `datos/bot_recoleccion`
>    junta 2.799 proyectos de Diputados (con cofirmantes completos) y 1.007
>    expedientes del Senado, y quedan en parquets que nadie lee.
> 2. **Es el blocker real del agente de taxonomías.** Varios documentos del repo
>    dicen "el blocker es `proyectos.db` + M1". La API key está resuelta desde el
>    14-jul; lo que falta es esta base.
> 3. El universo de proyectos del modelo sigue siendo el backfill de CKAN,
>    congelado al **2026-06-02**.
>
> Registrado en `coordinacion/URGENTE.md` ítem 5. El primer paso es de un minuto:
> `python datos\proyectos\src\store.py init`. Lo que falta de verdad es el upsert
> desde el bot, y la decisión de contrato con `datos/expedientes` (→ ADR).

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
