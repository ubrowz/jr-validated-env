#!/usr/bin/env Rscript
#
# use as: Rscript jrc_ss_discrete.R <proportion> <confidence>
#
# "proportion"  is the minimum fraction of the population that must conform
#               to the specification (e.g. 0.99)
# "confidence"  is the statistical confidence level for that claim (e.g. 0.95)
#
# Needs only base R — no external libraries required.
#
# Computes the minimum sample size required for discrete (pass/fail) design
# verification, assuming a binomial process model. Results are shown for
# 0 to 10 allowed failures so the engineer can evaluate the full trade-off
# between sample size and acceptance criterion.
#
# The formula used is the exact binomial method based on the chi-squared
# distribution:
#
#   n = ceiling( qchisq(confidence, df = 2*f + 2) / (2 * (1 - proportion)) )
#
# At f = 0 this reduces to the classic zero-failure rule:
#   n = ceiling( log(1 - confidence) / log(proportion) )
#
# Reference:
#   ASTM F3172-15 Standard Guide for Design Verification Device Size and
#   Sample Size Selection for Endovascular Devices
#
# Author: Joep Rous
# Version: 1.0

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop(paste(
    "Not enough arguments. Usage:",
    "  Rscript jrc_ss_discrete.R <proportion> <confidence>",
    "Example:",
    "  Rscript jrc_ss_discrete.R 0.99 0.95",
    sep = "\n"
  ))
}

proportion <- suppressWarnings(as.double(args[1]))
confidence <- suppressWarnings(as.double(args[2]))

if (is.na(proportion) || proportion <= 0 || proportion >= 1) {
  stop(paste("'proportion' must be a number strictly between 0 and 1. Got:", args[1]))
}
if (is.na(confidence) || confidence <= 0 || confidence >= 1) {
  stop(paste("'confidence' must be a number strictly between 0 and 1. Got:", args[2]))
}

# ---------------------------------------------------------------------------
# Sample size formula — exact binomial (chi-squared method)
# ---------------------------------------------------------------------------

ss_binomial <- function(proportion, confidence, f) {
  ceiling(qchisq(confidence, df = 2 * f + 2) / (2 * (1 - proportion)))
}

# ---------------------------------------------------------------------------
# Main output
# ---------------------------------------------------------------------------

message(" ")
message("✅ Sample Size for Discrete (Pass/Fail) Design Verification")
message("   version: 1.0, author: Joep Rous")
message("   ==========================================================")
message(paste("   proportion (minimum conforming fraction):  ", proportion))
message(paste("   confidence:                                ", confidence))
message(" ")
message("   Minimum sample sizes by number of allowed failures:")
message(" ")
message("   -----------------------------------------------")
message("    failures (f)   min sample size (n)   note")
message("   -----------------------------------------------")

for (f in 0:10) {
  n    <- ss_binomial(proportion, confidence, f)
  note <- if (f == 0) "  ← recommended (zero-failure)" else
          if (f <= 2) "  ⚠  requires justification"    else
                      "  ⚠  requires strong justification"
  message(sprintf("    f = %2d         n = %4d              %s", f, n, note))
}

message("   -----------------------------------------------")
message(" ")
message("   Note:")
message("   For FDA design verification, f = 0 (zero failures) is the standard")
message("   acceptance criterion. Allowing f > 0 failures requires a pre-specified")
message("   statistical justification and an Acceptable Quality Level (AQL) rationale")
message("   documented in the verification protocol before testing begins.")
message(" ")
message("   References:")
message("   - ASTM F3172-15(2021), Standard Guide for Design Verification Device Size")
message("     and Sample Size Selection for Endovascular Devices, ASTM International.")
message("     FDA-recognized consensus standard.")
message("   - NIST/SEMATECH e-Handbook of Statistical Methods, Section 7.2.4.1,")
message("     Binomial confidence intervals (exact method):")
message("     https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm")
message(" ")
