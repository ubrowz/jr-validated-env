#!/usr/bin/env Rscript
#
# use as: Rscript jrc_ss_discrete_ci.R <confidence> <n> <f>
#
# "confidence"  is the confidence level at which to evaluate the result
#               (e.g. 0.95). In medical device verification, 0.95 is the
#               accepted standard.
# "n"           total number of units tested (positive integer)
# "f"           number of failures observed (non-negative integer, f <= n)
#
# Needs only base R — no external libraries required.
#
# Given a fixed confidence level and a discrete (pass/fail) test result,
# determines the maximum proportion of the population that the result
# demonstrates conforms to the specification.
#
# This is the reporting companion to jrc_ss_discrete:
#   jrc_ss_discrete     — what minimum n do I need?
#   jrc_ss_discrete_ci  — given my test result, what proportion did I achieve?
#
# The proportion is found in closed form using the quantile of the beta
# distribution (exact Clopper-Pearson method):
#
#   proportion = 1 - qbeta(1 - confidence, f + 1, n - f)
#
# Two tables are shown:
#   Table 1: proportion achieved varying f from 0 to actual f (fixed n)
#            Shows what proportion would have been achieved with fewer failures.
#   Table 2: proportion achieved varying n from a lower bound to actual n
#            (fixed f). Shows what proportion would have been achieved with a
#            smaller sample.
#
# The row matching the actual test result is marked in both tables.
#
# Reference:
#   Clopper, C.J., Pearson, E.S. (1934). The use of confidence or fiducial
#   limits illustrated in the case of the binomial. Biometrika, 26(4), 404-413.
#   (Exact binomial confidence interval — the standard for regulatory submissions.)
#
# Author: Joep Rous
# Version: 2.0

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop(paste(
    "Not enough arguments. Usage:",
    "  Rscript jrc_ss_discrete_ci.R <confidence> <n> <f>",
    "Example (29 out of 30 passed, 95% confidence):",
    "  Rscript jrc_ss_discrete_ci.R 0.95 30 1",
    "Example (zero failures in 300 units, 95% confidence):",
    "  Rscript jrc_ss_discrete_ci.R 0.95 300 0",
    sep = "\n"
  ))
}

confidence <- suppressWarnings(as.double(args[1]))
n          <- suppressWarnings(as.integer(args[2]))
f          <- suppressWarnings(as.integer(args[3]))

if (is.na(confidence) || confidence <= 0 || confidence >= 1) {
  stop(paste("'confidence' must be a number strictly between 0 and 1. Got:", args[1]))
}
if (is.na(n) || n < 1) {
  stop(paste("'n' must be a positive integer. Got:", args[2]))
}
if (is.na(f) || f < 0) {
  stop(paste("'f' must be a non-negative integer. Got:", args[3]))
}
if (f > n) {
  stop(paste("'f' cannot exceed 'n'. Got f =", f, "and n =", n))
}
if (f == n) {
  stop("All units failed (f == n). Cannot demonstrate any conforming proportion.")
}

# ---------------------------------------------------------------------------
# Proportion formula — exact binomial (Clopper-Pearson)
# ---------------------------------------------------------------------------

# Maximum proportion of the population demonstrating conformance at the given
# confidence level, given n tested and f failures.
# Consistent with jrc_ss_discrete (exact Clopper-Pearson method).
binomial_proportion <- function(confidence, n, f) {
  1 - qbeta(1 - confidence, f + 1, n - f)
}

# ---------------------------------------------------------------------------
# Main output
# ---------------------------------------------------------------------------

p_actual <- binomial_proportion(confidence, n, f)

message(" ")
message("✅ Proportion Achieved for Discrete (Pass/Fail) Design Verification")
message("   version: 2.0, author: Joep Rous")
message("   ===================================================================")
message(paste("   confidence:                               ", confidence))
message(paste("   units tested (n):                        ", n))
message(paste("   failures observed (f):                   ", f))
message(paste("   proportion achieved:                     ", round(p_actual, 4)))
message(" ")

# ---------------------------------------------------------------------------
# Table 1: vary f from 0 to actual f, fixed n
# ---------------------------------------------------------------------------

message("   Table 1: proportion achieved for 0 to f failures (fixed n)")
message(" ")
message("   -------------------------------------------------------")
message("    failures (f)   proportion achieved   note")
message("   -------------------------------------------------------")

for (fi in 0:f) {
  p    <- binomial_proportion(confidence, n, fi)
  note <- if (fi == f) "  <- actual result" else ""
  message(sprintf("    f = %2d         %.4f                %s", fi, p, note))
}

message("   -------------------------------------------------------")
message(" ")

# ---------------------------------------------------------------------------
# Table 2: vary n from a lower bound to actual n, fixed f
# ---------------------------------------------------------------------------

# Lower bound: smallest n >= f+1 that gives a proportion of at least 0.50,
# to keep the table meaningful. Cap at 20 rows for readability.
n_min       <- max(f + 1, 2)
p_min_check <- binomial_proportion(confidence, n_min, f)
while (p_min_check < 0.50 && n_min < n) {
  n_min       <- n_min + 1
  p_min_check <- binomial_proportion(confidence, n_min, f)
}

n_range <- n - n_min + 1
step    <- max(1, ceiling(n_range / 20))

message("   Table 2: proportion achieved for varying n (fixed f)")
message(" ")
message("   -------------------------------------------------------")
message("    sample size (n)   proportion achieved   note")
message("   -------------------------------------------------------")

n_seq <- unique(c(seq(n_min, n, by = step), n))
for (ni in n_seq) {
  p    <- binomial_proportion(confidence, ni, f)
  note <- if (ni == n) "  <- actual result" else ""
  message(sprintf("    n = %4d        %.4f                %s", ni, p, note))
}

message("   -------------------------------------------------------")
message(" ")

# ---------------------------------------------------------------------------
# Interpretation note
# ---------------------------------------------------------------------------

if (f == 0) {
  message("   Note:")
  message("   Zero failures observed — this is the standard outcome for FDA design")
  message("   verification. The proportion above is achieved under the assumption")
  message("   that zero failures was the pre-specified acceptance criterion.")
} else {
  message("   Note:")
  message("   One or more failures were observed. For FDA design verification, f > 0")
  message("   requires a pre-specified AQL justification in the verification protocol.")
  message("   Proportions shown assume the observed f was the pre-specified")
  message("   acceptance criterion. Post-hoc acceptance of failures is not valid.")
}

message(" ")
