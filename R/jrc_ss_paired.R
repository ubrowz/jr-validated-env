#!/usr/bin/env Rscript
#
# use as: Rscript jrc_ss_paired.R <delta> <sd> <sides>
#
# "delta"   the minimum meaningful difference to detect between the two
#           conditions (absolute value, same units as the measurement).
#           This is the maximum allowable difference specified in the
#           verification protocol (e.g. 0.5 for a 0.5N difference).
# "sd"      expected standard deviation of the paired differences.
#           Estimate from a pilot study or prior data. Must be positive.
# "sides"   1 for a 1-sided test (direction of difference is pre-specified)
#           2 for a 2-sided test (direction of difference is unknown)
#
# Needs only base R — no external libraries required.
#
# Determines the minimum number of paired observations needed to detect a
# difference of 'delta' between two conditions (e.g. before/after, device A
# vs device B, method comparison) with given power and confidence.
#
# The paired t-test sample size formula is used:
#
#   n = ceiling( ((z_alpha + z_beta) / effect_size)^2 ) + 1
#
# where effect_size = delta / sd, z_alpha is the normal quantile for the
# confidence level (1-sided or 2-sided), and z_beta is the normal quantile
# for the power.
#
# Results are shown as a table over standard combinations of power
# (0.90, 0.95, 0.99) and confidence (0.90, 0.95, 0.99).
#
# Common uses in medical device development:
#   - Usability comparison: new design vs predicate
#   - Bench test comparison: two measurement methods
#   - Before/after design change assessment
#   - 510(k) substantial equivalence argument
#
# Note: 'n' is the number of pairs, not the total number of observations.
# Each pair consists of one measurement under each condition on the same
# unit or subject.
#
# Reference:
#   Rosner, B. (2015). Fundamentals of Biostatistics, 8th ed. Cengage.
#   Chapter 8: Hypothesis Testing — Means.
#
# Author: Joep Rous
# Version: 1.0

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop(paste(
    "Not enough arguments. Usage:",
    "  Rscript jrc_ss_paired.R <delta> <sd> <sides>",
    "Example (2-sided, detect 0.5N difference, SD of differences = 1.0N):",
    "  Rscript jrc_ss_paired.R 0.5 1.0 2",
    "Example (1-sided):",
    "  Rscript jrc_ss_paired.R 0.5 1.0 1",
    sep = "\n"
  ))
}

delta <- suppressWarnings(as.double(args[1]))
sd    <- suppressWarnings(as.double(args[2]))
sides <- suppressWarnings(as.integer(args[3]))

if (is.na(delta) || delta <= 0) {
  stop(paste("'delta' must be a positive number. Got:", args[1]))
}
if (is.na(sd) || sd <= 0) {
  stop(paste("'sd' must be a positive number. Got:", args[2]))
}
if (is.na(sides) || !(sides %in% c(1, 2))) {
  stop(paste("'sides' must be 1 or 2. Got:", args[3]))
}

effect_size <- delta / sd
two_sided   <- sides == 2

# ---------------------------------------------------------------------------
# Sample size formula
# ---------------------------------------------------------------------------

min_n_paired <- function(effect_size, power, confidence, two_sided = FALSE) {
  z_alpha <- if (two_sided) qnorm((1 + confidence) / 2) else qnorm(confidence)
  z_beta  <- qnorm(power)
  ceiling(((z_alpha + z_beta) / effect_size)^2) + 1
}

# ---------------------------------------------------------------------------
# Main output
# ---------------------------------------------------------------------------

sides_label <- if (two_sided) "2-sided" else "1-sided"

message(" ")
message("✅ Sample Size for Paired Comparison Study")
message("   version: 1.0, author: Joep Rous")
message("   ==========================================")
message(paste("   delta (minimum detectable difference): ", delta))
message(paste("   sd (of paired differences):            ", sd))
message(paste("   effect size (delta / sd):              ", round(effect_size, 4)))
message(paste("   test type:                             ", sides_label))
message(" ")

powers      <- c(0.90, 0.95, 0.99)
confidences <- c(0.90, 0.95, 0.99)

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

message(paste0("   Minimum number of pairs (", sides_label, " test):"))
message(" ")
message("   -----------------------------------------------")
message("                    confidence")
message("   power      0.90      0.95      0.99")
message("   -----------------------------------------------")

for (power in powers) {
  vals <- sapply(confidences, function(conf) {
    min_n_paired(effect_size, power, conf, two_sided = two_sided)
  })
  message(sprintf("   p = %.2f   %4d      %4d      %4d",
                  power, vals[1], vals[2], vals[3]))
}

message("   -----------------------------------------------")
message(" ")

# ---------------------------------------------------------------------------
# Interpretation note
# ---------------------------------------------------------------------------

n_fda <- min_n_paired(effect_size, 0.95, 0.95, two_sided = two_sided)

message(paste0(
  "   For FDA submissions (power = 0.95, confidence = 0.95): N >= ", n_fda, " pairs."
))
message(" ")
message("   Note:")
message("   N is the number of pairs, not the total number of observations.")
message("   Each pair consists of one measurement per condition on the same")
message("   unit or subject (e.g. one measurement with device A and one with")
message("   device B on the same test specimen).")
message(" ")
message("   The SD of paired differences is typically smaller than the SD of")
message("   individual measurements because between-unit variability cancels.")
message("   Use a pilot study or prior paired data to estimate this SD.")
message(" ")
if (!two_sided) {
  message("   1-sided test: use only when the direction of the difference is")
  message("   pre-specified in the protocol (e.g. new device >= predicate).")
  message("   Post-hoc selection of 1-sided testing is not acceptable.")
  message(" ")
}
