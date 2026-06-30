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
