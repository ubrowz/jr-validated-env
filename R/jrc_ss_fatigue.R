#!/usr/bin/env Rscript
#
# use as: Rscript jrc_ss_fatigue.R <reliability> <confidence> <shape> <af>
#
# "reliability" minimum fraction of units that must survive to the target
#               life (e.g. 0.90 for B10, 0.99 for B1, 0.999 for B0.1).
#               This is the reliability at the target life, not a proportion
#               of the test duration.
# "confidence"  statistical confidence level (e.g. 0.95)
# "shape"       Weibull shape parameter (beta). Must be estimated from prior
#               data, literature, or engineering knowledge. Controls how
#               quickly failures accumulate:
#                 beta < 1: early failures (infant mortality)
#                 beta = 1: constant failure rate (exponential)
#                 beta > 1: wear-out failures (typical for fatigue)
#                 beta ~ 2: common for metallic fatigue
#                 beta ~ 3-4: common for polymer fatigue
# "af"          acceleration factor: ratio of test duration to target life.
#               af = 1.0 means testing exactly to the target life.
#               af = 2.0 means testing to twice the target life (each unit
#               accumulates 2x the target life cycles or duration).
#               Must be >= 1.0. Higher af reduces the required sample size
#               but requires longer individual tests.
#
# Needs only base R — no external libraries required.
#
# ---------------------------------------------------------------------------
# Load from validated renv library
# ---------------------------------------------------------------------------

renv_lib <- Sys.getenv("RENV_PATHS_ROOT")
if (renv_lib == "") {
  stop("\u274c RENV_PATHS_ROOT is not set. Run this script from the provided zsh wrapper.")
}
r_ver    <- paste0("R-", R.version$major, ".",
                   sub("\\..*", "", R.version$minor))
platform <- R.version$platform
lib_path <- file.path(renv_lib, "renv", "library", Sys.getenv("JR_R_PLATFORM_DIR", unset = "macos"), r_ver, platform)
if (!dir.exists(lib_path)) {
  stop(paste("\u274c renv library not found at:", lib_path))
}
.libPaths(c(lib_path, .libPaths()))

#
# Determines the minimum number of units to test to the target life (or
# accelerated life) to demonstrate Weibull reliability with a given confidence.
# Results are shown for f = 0 to 5 allowed failures.
#
# The formula is based on the exact binomial confidence interval (chi-squared
# method). With an acceleration factor AF and Weibull shape beta, the
# effective per-unit failure probability at the test duration is:
#
#   p_eff = 1 - reliability^(AF^beta)
#
# The minimum n for at most f failures at confidence c is then:
#
#   n = ceiling( qchisq(confidence, 2*f + 2) / (2 * p_eff) )
#
# At AF = 1 and f = 0 this reduces to the zero-failure binomial rule,
# consistent with jrc_ss_discrete.
#
# IMPORTANT: the Weibull shape parameter beta is an assumed value, not
# estimated from the test data. The result is sensitive to this assumption.
# If beta is uncertain, run the script for a range of plausible beta values
# and use the most conservative (largest n) result.
#
# Common uses in medical device development:
#   - Fatigue life demonstration for implants (e.g. hip stems, spinal rods)
#   - Cyclic loading tests for cardiovascular devices
#   - Accelerated lifetime testing for polymer components
#   - Wear testing for articulating surfaces
#
# Reference:
#   Meeker, W.Q., Hahn, G.J., Escobar, L.A. (2017). Statistical Intervals:
#   A Guide for Practitioners and Researchers, 2nd ed. Wiley. Chapter 8.
#   Nelson, W.B. (2004). Accelerated Testing: Statistical Models, Test Plans,
#   and Data Analysis. Wiley.
#
# Author: Joep Rous
# Version: 1.0

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  stop(paste(
    "Not enough arguments. Usage:",
    "  Rscript jrc_ss_fatigue.R <reliability> <confidence> <shape> <af>",
    "Example (B10 life, 95% confidence, Weibull beta=2, no acceleration):",
    "  Rscript jrc_ss_fatigue.R 0.90 0.95 2.0 1.0",
    "Example (B10 life, 95% confidence, Weibull beta=2, AF=2):",
    "  Rscript jrc_ss_fatigue.R 0.90 0.95 2.0 2.0",
    sep = "\n"
  ))
}

reliability <- suppressWarnings(as.double(args[1]))
confidence  <- suppressWarnings(as.double(args[2]))
shape       <- suppressWarnings(as.double(args[3]))
af          <- suppressWarnings(as.double(args[4]))

if (is.na(reliability) || reliability <= 0 || reliability >= 1) {
  stop(paste("'reliability' must be a number strictly between 0 and 1. Got:", args[1]))
}
if (is.na(confidence) || confidence <= 0 || confidence >= 1) {
  stop(paste("'confidence' must be a number strictly between 0 and 1. Got:", args[2]))
}
if (is.na(shape) || shape <= 0) {
  stop(paste("'shape' must be a positive number. Got:", args[3]))
}
if (is.na(af) || af < 1.0) {
  stop(paste("'af' must be >= 1.0. Got:", args[4]))
}

# ---------------------------------------------------------------------------
# Formula
# ---------------------------------------------------------------------------

# Effective per-unit failure probability at the test duration
p_eff <- 1 - reliability^(af^shape)

if (p_eff <= 0 || p_eff >= 1) {
  stop(paste(
    "The combination of reliability, shape, and af gives an invalid effective",
    "failure probability:", round(p_eff, 6),
    "Check your input parameters."
  ))
}

min_n_fatigue <- function(confidence, f, p_eff) {
  ceiling(qchisq(confidence, df = 2 * f + 2) / (2 * p_eff))
}

# ---------------------------------------------------------------------------
# Main output
# ---------------------------------------------------------------------------

b_life <- round((1 - reliability) * 100, 3)

message(" ")
message("✅ Sample Size for Fatigue / Lifetime Testing (Weibull)")
message("   version: 1.0, author: Joep Rous")
message("   ========================================================")
message(paste("   target reliability (B-life):           ", reliability,
              paste0("  (B", b_life, " life)")))
message(paste("   confidence:                            ", confidence))
message(paste("   Weibull shape parameter (beta):        ", shape))
message(paste("   acceleration factor (AF):              ", af))
message(paste("   effective failure probability (p_eff): ", round(p_eff, 6)))
message(" ")

if (af > 1.0) {
  message(paste0("   Each unit is tested to ", af, "x the target life."))
  message(paste0("   Equivalent reliability at test duration: ",
                 round(1 - p_eff, 6)))
  message(" ")
}

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

message("   Minimum sample sizes by number of allowed failures:")
message(" ")
message("   -----------------------------------------------")
message("    failures (f)   min sample size (n)   note")
message("   -----------------------------------------------")

for (f in 0:5) {
  n    <- min_n_fatigue(confidence, f, p_eff)
  note <- if (f == 0) "  \u2190 recommended (zero-failure)" else
          if (f <= 2) "  \u26a0  requires justification"    else
                      "  \u26a0  requires strong justification"
  message(sprintf("    f = %d          n = %4d              %s", f, n, note))
}

message("   -----------------------------------------------")
message(" ")

# ---------------------------------------------------------------------------
# Sensitivity note on shape parameter
# ---------------------------------------------------------------------------

# Show n at f=0 for +/- 0.5 shape to illustrate sensitivity
shape_low  <- max(0.5, shape - 0.5)
shape_high <- shape + 0.5
p_low  <- 1 - reliability^(af^shape_low)
p_high <- 1 - reliability^(af^shape_high)
n_low  <- if (p_low  > 0 && p_low  < 1) min_n_fatigue(confidence, 0, p_low)  else NA
n_high <- if (p_high > 0 && p_high < 1) min_n_fatigue(confidence, 0, p_high) else NA

message("   Sensitivity to Weibull shape parameter (f = 0):")
message(" ")
message("   -----------------------------------------------")
message("    beta           min sample size (n, f=0)")
message("   -----------------------------------------------")
if (!is.na(n_low)) {
  message(sprintf("    %.1f (low)      n = %4d", shape_low, n_low))
}
message(sprintf("    %.1f (assumed)  n = %4d  \u2190 your input", shape,
                min_n_fatigue(confidence, 0, p_eff)))
if (!is.na(n_high)) {
  message(sprintf("    %.1f (high)     n = %4d", shape_high, n_high))
}
message("   -----------------------------------------------")
message(" ")
message("   Note:")
message("   The Weibull shape parameter (beta) is an assumed value.")
message("   The required sample size is sensitive to this assumption.")
message("   If beta is uncertain, use the value that gives the largest n")
message("   (most conservative result) or justify your assumed value with")
message("   prior test data or published literature for similar devices.")
message(" ")
message("   For FDA design verification, f = 0 (zero failures) is the standard")
message("   acceptance criterion. f > 0 requires a pre-specified justification.")
message(" ")
