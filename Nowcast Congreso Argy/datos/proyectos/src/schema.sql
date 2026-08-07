-- Base de PROYECTOS DE LEY (fuente de verdad del embudo).
-- Una fila por proyecto en `proyectos`; lo multivaluado va en tablas hijas.
-- El denominador (NNNN-X-AAAA) es la clave primaria del proyecto.
--
-- Convención de refresco (ver store.py):
--   • proyectos / autores / giros / tramite  -> se REFRESCAN en cada scrape
--     (reflejan el estado oficial actual).
--   • taxonomias -> las llena el AGENTE; el scraper NO las toca.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS proyectos (
    denominador     TEXT PRIMARY KEY,          -- '2832-D-2026' / '1091-S-2026'
    camara          TEXT NOT NULL,             -- 'diputados' | 'senado'
    sumario         TEXT,
    fecha_ingreso   TEXT,                      -- ISO yyyy-mm-dd
    estado          TEXT,                      -- ingresado/en_comision/con_dictamen/media_sancion/sancionado/rechazado
    ultimo_movimiento       TEXT,              -- texto del último movimiento de trámite
    ultimo_movimiento_fecha TEXT,
    pdf_url         TEXT,
    url             TEXT,                      -- ficha oficial de la que se extrajo
    fuente_ok       INTEGER DEFAULT 1,         -- 1 si la página parecía la esperada
    capturado_en    TEXT,                      -- timestamp del scrape que trajo estos datos
    creado_en       TEXT,                      -- alta en la base (no cambia)
    actualizado_en  TEXT                       -- último upsert
);

CREATE TABLE IF NOT EXISTS proyecto_autores (
    denominador TEXT NOT NULL,
    orden       INTEGER,                       -- orden de firma (0 = primer firmante)
    nombre      TEXT NOT NULL,
    distrito    TEXT,
    bloque      TEXT,
    PRIMARY KEY (denominador, orden),
    FOREIGN KEY (denominador) REFERENCES proyectos(denominador) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS proyecto_giros (
    denominador          TEXT NOT NULL,
    orden                INTEGER,              -- orden de giro (Senado lo trae explícito)
    comision             TEXT NOT NULL,
    competencia_primaria INTEGER DEFAULT 0,
    fecha_ingreso        TEXT,
    fecha_egreso         TEXT,
    FOREIGN KEY (denominador) REFERENCES proyectos(denominador) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS proyecto_tramite (
    denominador TEXT NOT NULL,
    idx         INTEGER,                       -- orden de aparición en la ficha
    camara      TEXT,
    movimiento  TEXT,
    fecha       TEXT,
    resultado   TEXT,
    FOREIGN KEY (denominador) REFERENCES proyectos(denominador) ON DELETE CASCADE
);

-- Llenada por el AGENTE de taxonomías (no por el scraper).
CREATE TABLE IF NOT EXISTS proyecto_taxonomias (
    denominador TEXT NOT NULL,
    taxonomia_id TEXT,                         -- ID estable del documento de taxonomías
    taxonomia    TEXT,                         -- nombre legible
    fuente       TEXT,                         -- 'agente' | 'humano'
    confianza    REAL,
    asignada_en  TEXT,
    PRIMARY KEY (denominador, taxonomia_id),
    FOREIGN KEY (denominador) REFERENCES proyectos(denominador) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_proy_camara  ON proyectos(camara);
CREATE INDEX IF NOT EXISTS ix_proy_estado  ON proyectos(estado);
CREATE INDEX IF NOT EXISTS ix_proy_fecha   ON proyectos(fecha_ingreso);
CREATE INDEX IF NOT EXISTS ix_giros_denom  ON proyecto_giros(denominador);
CREATE INDEX IF NOT EXISTS ix_tax_denom    ON proyecto_taxonomias(denominador);

-- ═══════════════════════════════════════════════════════════════════════════
-- AMPLIACIÓN 2026-08-07 — ADR-0009 (proyectos.db como fuente de verdad)
--
-- El esquema original modelaba la FICHA de un proyecto (scrape ficha por ficha).
-- Al absorber el backfill de CKAN aparecieron tres datos que el embudo consume y
-- que no tenían dónde vivir. Todo lo de acá es ADITIVO: `CREATE TABLE IF NOT
-- EXISTS` y columnas nuevas, así que una base vieja sigue abriendo igual y
-- `upsert_proyecto()` no cambia de comportamiento.
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. HITOS del expediente: dictamen / tratamiento en el recinto / ley sancionada.
--    El embudo los usa como conjuntos de pertenencia para armar las etapas, así
--    que se guardan como evidencia cruda y NO como un `estado` precalculado: si
--    mañana cambia la definición de etapa, se recalcula sin re-migrar.
CREATE TABLE IF NOT EXISTS proyecto_hitos (
    denominador TEXT NOT NULL,
    hito        TEXT NOT NULL,   -- 'dictamen' | 'resultado' | 'ley'
    fecha       TEXT,
    detalle     TEXT,            -- nº de ley, texto del resultado, etc.
    FOREIGN KEY (denominador) REFERENCES proyectos(denominador) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_hitos_denom ON proyecto_hitos(denominador);
CREATE INDEX IF NOT EXISTS ix_hitos_tipo  ON proyecto_hitos(hito);

-- 2. Identidad cruzada. `denominador` es el expediente de Diputados (todas las
--    112.793 filas de CKAN lo tienen). Estos dos permiten volver a la fuente:
--    `proyecto_id` es el id interno de CKAN (HCDN292367) del que dependen los
--    contratos viejos, y `exp_senado` es el número que el mismo proyecto recibe
--    al cruzar de cámara (3.315 proyectos con media sanción lo tienen).
ALTER TABLE proyectos ADD COLUMN proyecto_id TEXT;
ALTER TABLE proyectos ADD COLUMN exp_senado  TEXT;
ALTER TABLE proyectos ADD COLUMN tipo        TEXT;   -- LEY | RESOLUCION | DECLARACION
CREATE INDEX IF NOT EXISTS ix_proy_pid  ON proyectos(proyecto_id);
CREATE INDEX IF NOT EXISTS ix_proy_tipo ON proyectos(tipo);

-- 3. Giro AL INGRESAR (contrato de Franco del 07-08). Es el rasgo más pesado del
--    modelo y NO se deduce de `proyecto_giros`, que es el acumulado de hoy.
ALTER TABLE proyectos ADD COLUMN n_giros_inicial        INTEGER;
ALTER TABLE proyectos ADD COLUMN n_giros_inicial_fuente TEXT;  -- 'tp_bot' | 'reconstruido'
