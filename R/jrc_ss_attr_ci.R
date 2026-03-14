#!/usr/bin/env Rscript
#
# use as: Rscript jrc_ss_attr_ci.R <confidence> <file_path> <column_name> <spec1> <spec2>
#
# "confidence"  is the confidence level at which to evaluate the tolerance
#               interval (e.g. 0.95). In medical device verification, 0.95 is
#               the accepted standard.
# "file_path"   should point to a csv file with column names as the first row
# "column_name" should be one of the column names in the csv file
#               (NOT the name of the first column, which is used for row names)
# "spec1"       lower spec limit, or "-" if not applicable
# "spec2"       upper spec limit, or "-" if not applicable
#
# At least one of spec1 / spec2 must be numeric. Pass "-" for the one that
# does not apply:
#   1-sided lower:  spec1 = <value>  spec2 = -
#   1-sided upper:  spec1 = -        spec2 = <value>
#   2-sided:        spec1 = <value>  spec2 = <value>  (spec2 must be > spec1)
#
# IMPORTANT! The CSV file must have at least 2 columns: the first column is
# used for row names, the remaining columns contain data.
#
# Needs the <stats>, <tolerance>, <MASS> and <e1071> libraries.
#
# Given a fixed confidence level and a verification dataset, determines the
# maximum proportion of the population that the data can demonstrate conforms
# to the specification. The tolerance interval bounds are reported in original
# units so the result can be compared directly to the spec limits.
#
# This is the reporting companion to jrc_ss_attr and jrc_ss_attr_check:
#   jrc_ss_attr        — what minimum N do I need?
#   jrc_ss_attr_check  — does my planned N meet the requirement?
#   jrc_ss_attr_ci     — given my test result, what proportion did I achieve?
#
# The proportion is found by bisection: for fixed N and confidence, k_factor()
# is monotonically decreasing in proportion, so the proportion at which
# k_factor(N, p, confidence) == k_sample is located precisely in ~50 iterations.
#
# Author: Joep Rous
# Version: 1.0

renv_lib <- Sys.getenv("RENV_PATHS_ROOT")
if (renv_lib == "") {
  stop("❌ RENV_PATHS_ROOT is not set. Run this script from the provided zsh wrapper.")
}
r_ver    <- paste0("R-", R.version$major, ".",
                   sub("\\..*", "", R.version$minor))
platform <- R.version$platform
lib_path <- file.path(renv_lib, "renv", "library", "macos", r_ver, platform)
if (!dir.exists(lib_path)) {
  stop(paste("❌ renv library not found at:", lib_path))
}
.libPaths(c(lib_path, .libPaths()))

suppressPackageStartupMessages({
  library(tolerance)
  library(stats)
  library(MASS)
  library(e1071)
})

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOXCOX_ALPHA  <- 0.01
LAMBDA_EPS    <- 1e-6
BISECT_TOL    <- 1e-8   # Convergence tolerance for proportion search
BISECT_ITER   <- 100    # Maximum bisection iterations

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 5) {
  stop(paste(
    "Not enough arguments. Usage:",
    "  Rscript jrc_ss_attr_ci.R <confidence> <file_path> <column_name> <spec1> <spec2>",
    "Example (1-sided lower):",
    "  Rscript jrc_ss_attr_ci.R 0.95 mydata.csv ForceN 8.0 -",
    "Example (1-sided upper):",
    "  Rscript jrc_ss_attr_ci.R 0.95 mydata.csv ForceN - 12.0",
    "Example (2-sided):",
    "  Rscript jrc_ss_attr_ci.R 0.95 mydata.csv ForceN 8.0 12.0",
    sep = "\n"
  ))
}

confidence <- suppressWarnings(as.double(args[1]))
file_path  <- args[2]
input_col  <- args[3]
col        <- make.names(input_col)

if (is.na(confidence) || confidence <= 0 || confidence >= 1) {
  stop(paste("'confidence' must be a number strictly between 0 and 1. Got:", args[1]))
}
if (!file.exists(file_path)) {
  stop(paste("File not found:", file_path))
}

spec1_raw <- suppressWarnings(as.double(args[4]))
spec2_raw <- suppressWarnings(as.double(args[5]))

has_spec1 <- !is.na(spec1_raw)
has_spec2 <- !is.na(spec2_raw)

if (!has_spec1 && !has_spec2) {
  stop("Both spec1 and spec2 are '-'. At least one numeric spec limit must be provided.")
}
if (args[4] != "-" && !has_spec1) {
  stop(paste("'spec1' must be a numeric value or '-'. Got:", args[4]))
}
if (args[5] != "-" && !has_spec2) {
  stop(paste("'spec2' must be a numeric value or '-'. Got:", args[5]))
}
if (has_spec1 && has_spec2 && spec2_raw <= spec1_raw) {
  stop(paste("'spec2' must be greater than 'spec1'. Got spec1 =", spec1_raw,
             "and spec2 =", spec2_raw))
}

two_sided  <- has_spec1 && has_spec2
lower_only <- has_spec1 && !has_spec2
upper_only <- !has_spec1 && has_spec2

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

mydata <- tryCatch(
  read.table(file_path, header = TRUE, sep = ",", dec = ".", row.names = 1),
  error = function(e) stop(paste("Failed to read CSV file:", e$message))
)

if (ncol(mydata) < 1) {
  stop(paste(
    "The CSV file must have at least 2 columns: one for row names and at",
    "least one data column. The file appears to have only 1 column."
  ))
}

if (!col %in% names(mydata)) {
  stop(paste0(
    "Column '", col, "' not found in file. ",
    "Available columns: ", paste(names(mydata), collapse = ", ")
  ))
}

x_raw <- mydata[[col]]

n_bad <- sum(is.na(x_raw) | !is.finite(x_raw))
if (n_bad > 0) {
  warning(paste(n_bad, "NA or non-finite value(s) removed from column before analysis."))
}
x <- x_raw[is.finite(x_raw) & !is.na(x_raw)]

if (length(x) < 3) {
  stop(paste(
    "Fewer than 3 valid (finite) observations remain after removing NA/Inf.",
    "Cannot estimate process parameters."
  ))
}

N <- length(x)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

boxcox_transform <- function(val, lambda) {
  if (abs(lambda) < LAMBDA_EPS) log(val) else (val^lambda - 1) / lambda
}

boxcox_backtransform <- function(val, lambda) {
  if (abs(lambda) < LAMBDA_EPS) exp(val) else (lambda * val + 1)^(1 / lambda)
}

k_factor_one_side <- function(N, p, c) {
  K.factor(N, f = NULL, alpha = (1 - as.double(c)), P = as.double(p),
           side = 1, method = "EXACT", m = 50)
}

k_factor_two_side <- function(N, p, c) {
  K.factor(N, f = NULL, alpha = (1 - as.double(c)), P = as.double(p),
           side = 2, method = "EXACT", m = 50)
}

k_sample_one_side <- function(sample_mean, sample_sd, spec) {
  abs(sample_mean - spec) / sample_sd
}

# Returns the binding k-factor for a 2-sided interval: the minimum of the
# distances from the mean to each spec limit in SD units. Using the minimum
# ensures both bounds are within spec simultaneously. The symmetric half-window
# formula is only correct when the mean is exactly centred in the spec window.
k_sample_two_side <- function(sample_mean, sample_sd, s1, s2) {
  ks_lower <- (sample_mean - s1) / sample_sd
  ks_upper <- (s2 - sample_mean) / sample_sd
  min(ks_lower, ks_upper)
}

is_normal <- function(data, skew_threshold = 0.5) {
  if (length(data) < 3 || length(unique(data)) < 3) return(FALSE)
  if (any(is.na(data) | is.infinite(data))) return(FALSE)
  skew <- abs(e1071::skewness(data))
  message(paste("   Skewness value is:", round(skew, 4)))
  skew < skew_threshold
}

try_boxcox <- function(x, alpha = BOXCOX_ALPHA) {
  message("   Trying Box-Cox transformation (MLE-based)...")
  lm_model    <- stats::lm(x ~ 1)
  bc_result   <- MASS::boxcox(lm_model, plotit = FALSE)
  best_lambda <- bc_result$x[which.max(bc_result$y)]
  message(paste("   Optimal lambda =", round(best_lambda, 4)))
  x_bc        <- boxcox_transform(x, best_lambda)
  skew_before <- abs(e1071::skewness(x))
  skew_after  <- abs(e1071::skewness(x_bc))
  if (length(x_bc) >= 3 && length(x_bc) <= 5000) {
    p_val <- shapiro.test(x_bc)$p.value
    message(paste("   Shapiro-Wilk p-value after transform:", round(p_val, 4)))
  } else {
    p_val <- NA
    message(paste("   Shapiro-Wilk test skipped (N =", length(x_bc),
                  "is outside the valid range 3-5000); using skewness only."))
  }
  message(paste("   |Skew| before:", round(skew_before, 4),
                " |Skew| after:", round(skew_after, 4)))
  if (skew_after < skew_before || (!is.na(p_val) && p_val > alpha)) {
    message("   Box-Cox transformation accepted.\n")
    lam <- best_lambda
    return(list(
      transformation = paste0("boxcox (lambda=", round(lam, 4), ")"),
      lambda         = lam,
      transformed    = x_bc
    ))
  }
  message("   Box-Cox did not sufficiently improve normality.")
  return(NULL)
}

auto_transform_normal <- function(x, alpha = BOXCOX_ALPHA) {
  results <- list(
    original       = x,
    transformation = "none",
    lambda         = NA,
    transformed    = x
  )
  message("✅ Analyzing data ...")
  if (is_normal(x)) {
    message("   Data is approximately normal.")
    results$transformation <- "normal"
    return(results)
  }
  message("   Data considered not normal. Trying Box-Cox transformation!")
  if (all(x > 0)) {
    bc <- try_boxcox(x, alpha)
    if (!is.null(bc)) {
      results$transformation <- bc$transformation
      results$lambda         <- bc$lambda
      results$transformed    <- bc$transformed
      return(results)
    }
  } else {
    message("   Box-Cox requires strictly positive data; skipping (data contains zeros or negatives).")
  }
  return(results)
}

#' Find the maximum proportion p such that k_factor(N, p, confidence) <= k_sample.
#' Uses bisection on p in (0, 1). k_factor is monotonically decreasing in p,
#' so the crossing point is unique and well-defined.
find_proportion <- function(N, confidence, k_sample, side = 1) {
  k_fn <- if (side == 1) k_factor_one_side else k_factor_two_side

  # Guard: if even p -> 0 gives k_factor > k_sample, the data cannot support
  # any meaningful proportion claim.
  if (k_fn(N, 0.001, confidence) > k_sample) return(NA)

  # Guard: if p -> 1 gives k_factor <= k_sample, proportion is effectively 1.
  if (k_fn(N, 0.9999, confidence) <= k_sample) return(0.9999)

  lo <- 0.001
  hi <- 0.9999
  for (i in seq_len(BISECT_ITER)) {
    mid  <- (lo + hi) / 2
    k_mid <- k_fn(N, mid, confidence)
    if (k_mid <= k_sample) {
      lo <- mid
    } else {
      hi <- mid
    }
    if ((hi - lo) < BISECT_TOL) break
  }
  (lo + hi) / 2
}

# ---------------------------------------------------------------------------
# Main — header
# ---------------------------------------------------------------------------

message(" ")
message("✅ Attribute Tolerance Interval — Proportion Achieved")
message("   version: 1.0, author: Joep Rous")
message("   =====================================================")
message(paste("   confidence:                    ", confidence))
message(paste("   file:                          ", file_path))
message(paste("   column:                        ", input_col))
message(paste("   spec limit 1 (lower):          ", if (has_spec1) spec1_raw else "-"))
message(paste("   spec limit 2 (upper):          ", if (has_spec2) spec2_raw else "-"))
message(paste("   sample size (N):               ", N))
message(" ")

# ---------------------------------------------------------------------------
# Transformation
# ---------------------------------------------------------------------------

result <- auto_transform_normal(x, alpha = BOXCOX_ALPHA)

if (result$transformation == "none") {
  message(" ")
  message("❌ Could not evaluate tolerance interval: data are not normally distributed")
  message("   and Box-Cox transformation did not achieve sufficient normality.")
  message(" ")
  message("   Suggestions:")
  message("     - If data are heavily rounded, try using more decimal places.")
  message("     - Plot your data and inspect for multimodality or outliers.")
  message("     - Consider whether the process may have shifted over time.")
  message("     - A non-parametric tolerance interval may be appropriate.")
  quit(save = "no", status = 1)
}

X     <- mean(result$transformed)
sigma <- sd(result$transformed)
lam   <- result$lambda

message(paste("   transformation applied:        ", result$transformation))
message(" ")

# ---------------------------------------------------------------------------
# Proportion search and tolerance interval bounds
# ---------------------------------------------------------------------------

if (lower_only) {

  message("   Mode: 1-sided (lower) tolerance interval")

  spec1_t <- if (result$transformation != "normal") boxcox_transform(spec1_raw, lam) else spec1_raw

  if (X < spec1_t) {
    warning(paste(
      "The sample mean (transformed:", round(X, 4),
      ") is below spec1 (transformed:", round(spec1_t, 4), ").",
      "The process may already be failing the specification.",
      "Interpret this result with caution."
    ))
  }

  ks         <- k_sample_one_side(X, sigma, spec1_t)
  proportion <- find_proportion(N, confidence, ks, side = 1)

  # Tolerance interval lower bound: mean - k_sample * sd, back-transformed
  ti_lower_t <- X - ks * sigma
  ti_lower   <- if (result$transformation != "normal") {
    boxcox_backtransform(ti_lower_t, lam)
  } else {
    ti_lower_t
  }

  message(" ")
  message("✅ Result:")
  if (is.na(proportion)) {
    message("   The sample k-factor is too low to support any meaningful proportion claim.")
    message("   The dataset does not demonstrate conformance to the spec at this confidence.")
  } else {
    message(paste("   k-factor from sample:                  ", round(ks, 4)))
    message(paste("   proportion achieved at", confidence, "confidence: ", round(proportion, 4)))
    message(" ")
    message(paste("   tolerance interval lower bound:        ", round(ti_lower, 4), "(original units)"))
    message(paste("   spec limit 1 (lower):                  ", spec1_raw))
    if (ti_lower >= spec1_raw) {
      message("✅ Lower bound: tolerance interval is at or above the spec limit.")
    } else {
      message("❌ Lower bound: tolerance interval falls below the spec limit.")
    }
  }

} else if (upper_only) {

  message("   Mode: 1-sided (upper) tolerance interval")

  spec2_t <- if (result$transformation != "normal") boxcox_transform(spec2_raw, lam) else spec2_raw

  if (X > spec2_t) {
    warning(paste(
      "The sample mean (transformed:", round(X, 4),
      ") is above spec2 (transformed:", round(spec2_t, 4), ").",
      "The process may already be failing the specification.",
      "Interpret this result with caution."
    ))
  }

  ks         <- k_sample_one_side(X, sigma, spec2_t)
  proportion <- find_proportion(N, confidence, ks, side = 1)

  # Tolerance interval upper bound: mean + k_sample * sd, back-transformed
  ti_upper_t <- X + ks * sigma
  ti_upper   <- if (result$transformation != "normal") {
    boxcox_backtransform(ti_upper_t, lam)
  } else {
    ti_upper_t
  }

  message(" ")
  message("✅ Result:")
  if (is.na(proportion)) {
    message("   The sample k-factor is too low to support any meaningful proportion claim.")
    message("   The dataset does not demonstrate conformance to the spec at this confidence.")
  } else {
    message(paste("   k-factor from sample:                  ", round(ks, 4)))
    message(paste("   proportion achieved at", confidence, "confidence: ", round(proportion, 4)))
    message(" ")
    message(paste("   tolerance interval upper bound:        ", round(ti_upper, 4), "(original units)"))
    message(paste("   spec limit 2 (upper):                  ", spec2_raw))
    if (ti_upper <= spec2_raw) {
      message("✅ Upper bound: tolerance interval is at or below the spec limit.")
    } else {
      message("❌ Upper bound: tolerance interval exceeds the spec limit.")
    }
  }

} else {

  message("   Mode: 2-sided tolerance interval")

  spec1_t <- if (result$transformation != "normal") boxcox_transform(spec1_raw, lam) else spec1_raw
  spec2_t <- if (result$transformation != "normal") boxcox_transform(spec2_raw, lam) else spec2_raw

  if (X < spec1_t || X > spec2_t) {
    warning(paste(
      "The sample mean (transformed:", round(X, 4),
      ") lies outside the spec window [transformed:", round(spec1_t, 4),
      ",", round(spec2_t, 4), "].",
      "The process may already be failing the specification.",
      "Interpret this result with caution."
    ))
  }

  ks         <- k_sample_two_side(X, sigma, spec1_t, spec2_t)
  proportion <- find_proportion(N, confidence, ks, side = 2)

  # TI bounds use the per-side k-factors so each bound aligns with its own
  # spec limit. The binding ks (minimum) drives the proportion claim; the
  # per-side values drive the reported interval in original units.
  ks_lower   <- (X - spec1_t) / sigma
  ks_upper   <- (spec2_t - X) / sigma
  ti_lower_t <- X - ks_lower * sigma
  ti_upper_t <- X + ks_upper * sigma
  ti_lower   <- if (result$transformation != "normal") boxcox_backtransform(ti_lower_t, lam) else ti_lower_t
  ti_upper   <- if (result$transformation != "normal") boxcox_backtransform(ti_upper_t, lam) else ti_upper_t

  message(" ")
  message("✅ Result:")
  if (is.na(proportion)) {
    message("   The sample k-factor is too low to support any meaningful proportion claim.")
    message("   The dataset does not demonstrate conformance to the spec at this confidence.")
  } else {
    message(paste("   k-factor from sample:                  ", round(ks, 4)))
    message(paste("   proportion achieved at", confidence, "confidence: ", round(proportion, 4)))
    message(" ")
    message(paste("   tolerance interval lower bound:        ", round(ti_lower, 4), "(original units)"))
    message(paste("   spec limit 1 (lower):                  ", spec1_raw))
    if (ti_lower >= spec1_raw) {
      message("✅ Lower bound: tolerance interval is at or above the spec limit.")
    } else {
      message("❌ Lower bound: tolerance interval falls below the spec limit.")
    }
    message(" ")
    message(paste("   tolerance interval upper bound:        ", round(ti_upper, 4), "(original units)"))
    message(paste("   spec limit 2 (upper):                  ", spec2_raw))
    if (ti_upper <= spec2_raw) {
      message("✅ Upper bound: tolerance interval is at or below the spec limit.")
    } else {
      message("❌ Upper bound: tolerance interval exceeds the spec limit.")
    }
  }

}

message(" ")
