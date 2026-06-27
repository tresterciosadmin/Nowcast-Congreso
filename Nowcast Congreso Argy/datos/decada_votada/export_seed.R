#!/usr/bin/env Rscript
# datos/decada_votada/export_seed.R
# Semilla historica (uso unico): exporta los datos de Andy Tow ("La Decada Votada")
# via el paquete R legislAr a parquet en el ESQUEMA CANONICO (docs/schemas, schema_version=1).
#
# Correr LOCALMENTE en R (no en el sandbox):
#   Rscript export_seed.R              # corrida completa (lenta: miles de actas)
#   Rscript export_seed.R 25           # corrida de prueba: primeras 25 actas por camara
#
# Salidas:
#   data/clean/decada_votada_actas.parquet
#   data/clean/decada_votada_votos.parquet
# Temporales/descartables -> ../../Archivos_Borrar/

SCHEMA_VERSION <- 1L
FUENTE <- "decada_votada"

# --- Dependencias (instala lo que falte) ---
need <- function(pkg, gh = NULL) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (is.null(gh)) install.packages(pkg, repos = "https://cloud.r-project.org")
    else { if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes"); remotes::install_github(gh) }
  }
}
need("dplyr"); need("stringr"); need("purrr"); need("arrow"); need("legislAr", gh = "politicaargentina/legislAr")
library(dplyr)

args <- commandArgs(trailingOnly = TRUE)
limit <- if (length(args) >= 1) suppressWarnings(as.integer(args[[1]])) else NA_integer_

here    <- tryCatch(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)))), error = function(e) ".")
clean   <- file.path(here, "data", "clean"); dir.create(clean, recursive = TRUE, showWarnings = FALSE)
borrar  <- file.path(here, "..", "..", "Archivos_Borrar"); dir.create(borrar, recursive = TRUE, showWarnings = FALSE)
log <- function(...) cat(sprintf("[%s] %s\n", format(Sys.time(), "%H:%M:%S"), sprintf(...)))

# --- Normalizacion del enum canonico de voto ---
norm_voto <- function(x) {
  v <- toupper(trimws(as.character(x)))
  v <- chartr("ÁÉÍÓÚ", "AEIOU", v)
  dplyr::case_when(
    stringr::str_detect(v, "AFIRMATIV|^SI$|POSITIV") ~ "AFIRMATIVO",
    stringr::str_detect(v, "NEGATIV|^NO$")           ~ "NEGATIVO",
    stringr::str_detect(v, "ABSTEN")                  ~ "ABSTENCION",
    TRUE                                              ~ "AUSENTE"   # ausente, no vota, presidente
  )
}

# --- Trae los votos de un acta con reintentos ---
safe_votes <- function(bill_id, intentos = 3) {
  for (i in seq_len(intentos)) {
    out <- tryCatch(legislAr::get_bill_votes(bill = bill_id), error = function(e) e)
    if (!inherits(out, "error")) return(out)
    Sys.sleep(2 * i)  # backoff
  }
  log("  ! fallo acta %s: %s", bill_id, conditionMessage(out)); NULL
}

actas_all <- list(); votos_all <- list()

for (camara in c("diputados", "senado")) {
  log("Camara: %s — listando actas...", camara)
  bills <- tryCatch(legislAr::show_available_bills(chamber = camara), error = function(e) NULL)
  if (is.null(bills) || nrow(bills) == 0) { log("  sin actas para %s", camara); next }
  if (!is.na(limit)) bills <- head(bills, limit)
  log("  %d actas", nrow(bills))

  for (k in seq_len(nrow(bills))) {
    id <- bills$id[[k]]
    acta_id <- paste0(FUENTE, ":", id)
    v <- safe_votes(id)
    if (is.null(v) || nrow(v) == 0) next

    votos_all[[length(votos_all) + 1]] <- tibble::tibble(
      schema_version = SCHEMA_VERSION, acta_id = acta_id,
      legislador_id = NA_character_,
      legislador_nombre = as.character(v$nombre_legislador),
      bloque = as.character(v$nombre_bloque),
      distrito = as.character(v$provincia),
      voto = norm_voto(v$voto), fuente = FUENTE)

    actas_all[[length(actas_all) + 1]] <- tibble::tibble(
      schema_version = SCHEMA_VERSION, acta_id = acta_id, camara = camara,
      fecha = NA, periodo = NA_integer_,
      titulo = as.character(bills$description[[k]]),
      expediente = stringr::str_extract(as.character(bills$description[[k]]), "\\d+-[A-Za-z]+-\\d+"),
      tipo_mayoria = NA_character_, resultado = NA_character_,
      n_afirmativos = sum(norm_voto(v$voto) == "AFIRMATIVO"),
      n_negativos   = sum(norm_voto(v$voto) == "NEGATIVO"),
      n_abstenciones= sum(norm_voto(v$voto) == "ABSTENCION"),
      n_ausentes    = sum(norm_voto(v$voto) == "AUSENTE"),
      fuente = FUENTE)

    if (k %% 50 == 0) log("  %s: %d/%d", camara, k, nrow(bills))
    Sys.sleep(0.3)  # cortesia con el servidor
  }
}

actas <- dplyr::bind_rows(actas_all)
votos <- dplyr::bind_rows(votos_all)
log("Total: %d actas, %d votos", nrow(actas), nrow(votos))

arrow::write_parquet(actas, file.path(clean, "decada_votada_actas.parquet"))
arrow::write_parquet(votos, file.path(clean, "decada_votada_votos.parquet"))
log("Escrito en %s", clean)
log("NOTA: 'fecha' viene NA desde show_available_bills (solo month/year). Enriquecer en datos/canonica si hace falta.")
