# jr_helpers.R
# Sourced by JR Anchored scripts at startup (via jrrun).
# Provides jr_log_output_hashes() for logging output file SHA-256 hashes
# to the run log after a script completes.
#
# Requires env vars set by jrrun:
#   JR_PROJECT_ROOT  — project root directory
#   PROJECT_ID       — project identifier (used to locate run.log)

jr_log_output_hashes <- function(files) {
  project_id <- Sys.getenv("PROJECT_ID")
  if (nchar(project_id) == 0L) {
    warning("jr_log_output_hashes: PROJECT_ID not set — output hashes not logged.")
    return(invisible(NULL))
  }
  log_file <- file.path(path.expand("~"), ".jrscript", project_id, "run.log")
  timestamp <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
  for (f in files) {
    if (!file.exists(f)) {
      warning(sprintf("jr_log_output_hashes: file not found, skipping: %s", f))
      next
    }
    hash <- tryCatch(
      {
        f_norm <- normalizePath(f, winslash = "/", mustWork = FALSE)
        result <- system2("shasum", args = c("-a", "256", f_norm),
                          stdout = TRUE, stderr = FALSE)
        strsplit(result, " ")[[1]][1]
      },
      error = function(e) NA_character_
    )
    if (is.na(hash)) {
      warning(sprintf("jr_log_output_hashes: could not hash file: %s", f))
      next
    }
    cat(sprintf("%s\tjrrun_output\t%s\t%s\n",
                timestamp, basename(f), hash),
        file = log_file, append = TRUE)
  }
  invisible(NULL)
}

jr_log_report <- function(docx_path) {
  project_id <- Sys.getenv("PROJECT_ID")
  if (nchar(project_id) == 0L) return(invisible(NULL))
  log_file  <- file.path(path.expand("~"), ".jrscript", project_id, "run.log")
  timestamp <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
  cat(sprintf("%s\tjrrun_report\t%s\n", timestamp, basename(docx_path)),
      file = log_file, append = TRUE)
  invisible(NULL)
}

jr_python_bin <- function() {
  if (.Platform$OS.type != "windows") return("python3")
  # Locate the real python.exe via admin/python_version.txt (same logic as jrrun)
  ver_file <- file.path(Sys.getenv("JR_PROJECT_ROOT"), "admin", "python_version.txt")
  if (file.exists(ver_file)) {
    ver <- trimws(readLines(ver_file, warn = FALSE)[1L])
    mm  <- paste(strsplit(ver, "\\.")[[1L]][1:2], collapse = "")
    py  <- file.path(Sys.getenv("USERPROFILE"), "AppData", "Local", "Programs",
                     "Python", paste0("Python", mm), "python.exe")
    if (file.exists(py)) return(normalizePath(py, winslash = "/"))
  }
  "python"  # fallback: python in PATH
}
