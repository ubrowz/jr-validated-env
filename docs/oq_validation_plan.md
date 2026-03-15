# JR Validated Environment — OQ Validation Plan

**Document:** OQ Validation Plan
**Version:** 1.1.0
**Date:** 2026-03-15
**Author:** Joep Rous
**Scope:** Operational Qualification (OQ) test specifications for all community
scripts in `R/` and `Python/` (excluding `jrhello.R` / `jrhello.py`)

---

## 1. Purpose and Scope

This document defines the Operational Qualification (OQ) test specifications
for the JR Validated Environment community script suite. Each test case
specifies inputs, the expected behaviour, and the pass criterion used by the
automated OQ test runner (`admin_oq`).

**In scope:** all 22 R scripts and 2 Python scripts listed in Section 3.
**Out of scope:** infrastructure scripts in `bin/` and `admin/`; demo scripts
`jrhello.R` and `jrhello.py`.

---

## 2. Test Environment

| Item | Requirement |
|---|---|
| Python test runner | pytest, executed inside the OQ venv (`~/.venvs/MyProject_oq/`) |
| OQ venv requirements | `oq/requirements.txt` (frozen, separate from the user venv) |
| Scripts under test | Invoked as subprocesses via `jrrun` (not called directly) |
| Test data | Synthetic CSV files committed to `oq/data/`; generated with fixed seeds |
| Evidence output | Timestamped qualification report written by `admin_oq` |

All test cases check the subprocess **exit code** and **stdout/stderr content**
(via `message()` output captured on stderr in R scripts).

---

## 3. Scripts Under Test

### 3.1 Sample Size Suite (R)

| Script | Arguments |
|---|---|
| `jrc_ss_discrete` | `<proportion> <confidence>` |
| `jrc_ss_discrete_ci` | `<confidence> <n> <f>` |
| `jrc_ss_attr` | `<proportion> <confidence> <file> <col> <spec1> <spec2>` |
| `jrc_ss_attr_check` | `<proportion> <confidence> <file> <col> <spec1> <spec2> <planned_N>` |
| `jrc_ss_attr_ci` | `<confidence> <file> <col> <spec1> <spec2>` |
| `jrc_ss_sigma` | `<precision> <spec1> <spec2>` |
| `jrc_ss_paired` | `<delta> <sd> <sides>` |
| `jrc_ss_equivalence` | `<delta> <sd> <sides>` |
| `jrc_ss_fatigue` | `<reliability> <confidence> <shape> <af>` |
| `jrc_ss_gauge_rr` | `<grr> <type> <sigma_or_tolerance>` |

### 3.2 Diagnostic Suite (R)

| Script | Arguments |
|---|---|
| `jrc_normality` | `<file> <col>` |
| `jrc_outliers` | `<file> <col>` |
| `jrc_capability` | `<file> <col> <spec1> <spec2>` |
| `jrc_descriptive` | `<file> <col>` |

### 3.3 Statistical Analysis (R)

| Script | Arguments |
|---|---|
| `jrc_bland_altman` | `<file1> <col1> <file2> <col2>` |
| `jrc_weibull` | `<file> <time_col> <status_col>` |

### 3.4 Verification (R)

| Script | Arguments |
|---|---|
| `jrc_verify_attr` | `<proportion> <confidence> <file> <col> <spec1> <spec2>` |

### 3.5 Data Generation (R)

| Script | Arguments |
|---|---|
| `jrc_gen_normal` | `<n> <mean> <sd> <output_folder> [seed]` |
| `jrc_gen_lognormal` | `<n> <meanlog> <sdlog> <output_folder> [seed]` |
| `jrc_gen_sqrt` | `<n> <df> <scale> <output_folder> [seed]` |
| `jrc_gen_boxcox` | `<n> <shape> <scale> <output_folder> [seed]` |
| `jrc_gen_uniform` | `<n> <min> <max> <output_folder> [seed]` |

### 3.6 Data Conversion (Python)

| Script | Arguments |
|---|---|
| `jrc_convert_csv` | `<file> <column> <skip_lines> [delimiter]` |
| `jrc_convert_txt` | `<file> [start_line] [end_line]` |

---

## 4. Test Data

The following synthetic data files are committed to `oq/data/` and used
across multiple test cases. All files follow the standard two-column CSV
format (`id`, `value`) unless noted otherwise.

| File | Content | Used by |
|---|---|---|
| `normal_n30_mean10_sd1_seed42.csv` | 30 values, N(10, 1), seed 42 | jrc_ss_attr, jrc_ss_attr_check, jrc_ss_attr_ci, jrc_normality, jrc_outliers, jrc_capability, jrc_descriptive, jrc_verify_attr |
| `skewed_n30_lognormal_seed42.csv` | 30 values, log-normal (meanlog=2, sdlog=0.5), seed 42 | jrc_normality (non-normal path), jrc_verify_attr (Box-Cox path) |
| `outlier_n30_seed42.csv` | `normal_n30_mean10_sd1_seed42.csv` with row 15 replaced by 15.0 (5-sigma outlier) | jrc_outliers (detected path) |
| `bland_altman_method1_seed42.csv` | 25 values, N(10, 1), seed 42 | jrc_bland_altman (method 1) |
| `bland_altman_method2_seed42.csv` | Same 25 values + N(0, 0.2) bias, seed 99 | jrc_bland_altman (method 2) |
| `weibull_n20_seed42.csv` | 20 rows, columns `id`, `cycles`, `status`; 15 failures (status=1), 5 censored (status=0); Weibull(shape=2, scale=1000), seed 42 | jrc_weibull |
| `convert_multicolumn.txt` | Tab-delimited, 3 header lines, columns: `id`, `ForceN`, `Temp` | jrc_convert_csv |
| `convert_singlecolumn.txt` | One numeric value per line, 200 lines | jrc_convert_txt |

---

## 5. Test Specifications

Pass criterion for all test cases unless stated otherwise:
- **Exit code 0** — script completes without error
- **Output contains** the specified string(s) on stderr (R scripts use `message()`)
- **Output does not contain** `Error` or `❌` (unless the test is specifically testing error handling, in which case exit code must be non-zero and the specified error string must be present)

---

### 5.1 jrc_ss_discrete

**TC-DISC-001 — Normal input, standard parameters**
Command: `jrc_ss_discrete 0.99 0.95`
Expected output contains: `f = 0` and `299` (zero-failure N for P=0.99, C=0.95:
`ceiling(log(0.05)/log(0.99))` = 299)
Pass criterion: exit 0, "299" present in output for f=0 row.

**TC-DISC-002 — Lower confidence produces smaller N**
Command: `jrc_ss_discrete 0.99 0.80`
Expected: exit 0, f=0 N < 299.

**TC-DISC-003 — Invalid proportion (out of range)**
Command: `jrc_ss_discrete 1.5 0.95`
Expected: exit non-zero, output contains `proportion`.

**TC-DISC-004 — Invalid confidence (zero)**
Command: `jrc_ss_discrete 0.99 0`
Expected: exit non-zero, output contains `confidence`.

**TC-DISC-005 — Missing arguments**
Command: `jrc_ss_discrete 0.99`
Expected: exit non-zero, output contains `Usage`.

---

### 5.2 jrc_ss_discrete_ci

**TC-DISCICI-001 — Standard inputs, zero failures**
Command: `jrc_ss_discrete_ci 0.95 299 0`
Expected: exit 0, output contains `0.99` (achieved proportion ≥ 0.99 at N=299, f=0, C=0.95).

**TC-DISCICI-002 — One failure in sample**
Command: `jrc_ss_discrete_ci 0.95 299 1`
Expected: exit 0, achieved proportion < proportion from TC-001 (larger f → lower achieved P).

**TC-DISCICI-003 — f > n (invalid)**
Command: `jrc_ss_discrete_ci 0.95 10 15`
Expected: exit non-zero, output contains `f` or `n`.

**TC-DISCICI-004 — Missing arguments**
Command: `jrc_ss_discrete_ci 0.95 299`
Expected: exit non-zero, output contains `Usage`.

---

### 5.3 jrc_ss_attr

**TC-ATTR-001 — Normal data, 1-sided lower**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 -`
Expected: exit 0, output contains minimum N (a positive integer ≥ 10), output contains `✅`.

**TC-ATTR-002 — Normal data, 1-sided upper**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value - 11.0`
Expected: exit 0, output contains minimum N ≥ 10.

**TC-ATTR-003 — Normal data, 2-sided**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 11.0`
Expected: exit 0, 2-sided N ≥ 1-sided N from TC-001 (2-sided requires more samples).

**TC-ATTR-004 — spec2 ≤ spec1 (invalid)**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 11.0 9.0`
Expected: exit non-zero, output contains `spec2`.

**TC-ATTR-005 — Both spec limits absent**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value - -`
Expected: exit non-zero.

**TC-ATTR-006 — File not found**
Command: `jrc_ss_attr 0.95 0.95 nonexistent.csv value 9.0 -`
Expected: exit non-zero, output contains `not found`.

**TC-ATTR-007 — Column not found**
Command: `jrc_ss_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv badcol 9.0 -`
Expected: exit non-zero, output contains `not found` or `Available`.

---

### 5.4 jrc_ss_attr_check

**TC-ATTRCK-001 — Planned N meets requirement (PASS)**
Command: `jrc_ss_attr_check 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 - 50`
Expected: exit 0, output contains `✅` and/or `PASS`.

**TC-ATTRCK-002 — Planned N too small (FAIL)**
Command: `jrc_ss_attr_check 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 - 5`
Expected: exit 0 (script completes), output contains `❌` or `FAIL`.

**TC-ATTRCK-003 — Missing planned_N argument**
Command: `jrc_ss_attr_check 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 -`
Expected: exit non-zero, output contains `Usage`.

---

### 5.5 jrc_ss_attr_ci

**TC-ATTRCI-001 — 1-sided lower, well-centred data**
Command: `jrc_ss_attr_ci 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 -`
Expected: exit 0, achieved proportion reported as a number between 0 and 1.

**TC-ATTRCI-002 — 2-sided, well-centred data**
Command: `jrc_ss_attr_ci 0.95 normal_n30_mean10_sd1_seed42.csv value 9.0 11.0`
Expected: exit 0, 2-sided achieved proportion ≤ 1-sided proportion from TC-001.

**TC-ATTRCI-003 — File not found**
Command: `jrc_ss_attr_ci 0.95 nonexistent.csv value 9.0 -`
Expected: exit non-zero, output contains `not found`.

---

### 5.6 jrc_ss_sigma

**TC-SIGMA-001 — 1-sided, precision 1.5**
Command: `jrc_ss_sigma 1.5 9.0 -`
Expected: exit 0, output contains a table with N values for various power/confidence combinations.

**TC-SIGMA-002 — 2-sided, precision 1.5**
Command: `jrc_ss_sigma 1.5 9.0 11.0`
Expected: exit 0, N values ≥ those from TC-001 (2-sided requires larger N).

**TC-SIGMA-003 — Invalid precision (negative)**
Command: `jrc_ss_sigma -1.0 9.0 -`
Expected: exit non-zero.

**TC-SIGMA-004 — Missing arguments**
Command: `jrc_ss_sigma 1.5`
Expected: exit non-zero, output contains `Usage`.

---

### 5.7 jrc_ss_paired

**TC-PAIRED-001 — 2-sided paired test**
Command: `jrc_ss_paired 0.5 1.0 2`
Expected: exit 0, output contains a table of N values; all N ≥ 10.

**TC-PAIRED-002 — 1-sided produces smaller N than 2-sided**
Command: `jrc_ss_paired 0.5 1.0 1`
Expected: exit 0; N values < those from TC-001 at the same power/confidence.

**TC-PAIRED-003 — Invalid sides (3)**
Command: `jrc_ss_paired 0.5 1.0 3`
Expected: exit non-zero.

**TC-PAIRED-004 — sd ≤ 0**
Command: `jrc_ss_paired 0.5 0 2`
Expected: exit non-zero.

**TC-PAIRED-005 — Missing arguments**
Command: `jrc_ss_paired 0.5`
Expected: exit non-zero, output contains `Usage`.

---

### 5.8 jrc_ss_equivalence

**TC-EQUIV-001 — 2-sided TOST**
Command: `jrc_ss_equivalence 0.5 1.0 2`
Expected: exit 0, output contains `TOST` or `equivalence`, table of N values ≥ 10.

**TC-EQUIV-002 — 1-sided non-inferiority**
Command: `jrc_ss_equivalence 0.5 1.0 1`
Expected: exit 0, N values < those from TC-001.

**TC-EQUIV-003 — Invalid sides**
Command: `jrc_ss_equivalence 0.5 1.0 0`
Expected: exit non-zero.

**TC-EQUIV-004 — Missing arguments**
Command: `jrc_ss_equivalence 0.5`
Expected: exit non-zero, output contains `Usage`.

---

### 5.9 jrc_ss_fatigue

**TC-FAT-001 — Standard Weibull, no acceleration**
Command: `jrc_ss_fatigue 0.90 0.95 2.0 1.0`
Expected: exit 0, output contains a table for f=0..5; f=0 N is the largest.

**TC-FAT-002 — Acceleration factor reduces N**
Command: `jrc_ss_fatigue 0.90 0.95 2.0 2.0`
Expected: exit 0, f=0 N < f=0 N from TC-001.

**TC-FAT-003 — Reliability ≥ 1 (invalid)**
Command: `jrc_ss_fatigue 1.0 0.95 2.0 1.0`
Expected: exit non-zero.

**TC-FAT-004 — af < 1 (invalid)**
Command: `jrc_ss_fatigue 0.90 0.95 2.0 0.5`
Expected: exit non-zero.

**TC-FAT-005 — Missing arguments**
Command: `jrc_ss_fatigue 0.90 0.95 2.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.10 jrc_ss_gauge_rr

**TC-GRR-001 — Process-based %GRR target**
Command: `jrc_ss_gauge_rr 10 process 1.0`
Expected: exit 0, output contains a table of operators × replicates combinations; output contains `%GRR` and `ndc`.

**TC-GRR-002 — Tolerance-based %GRR target**
Command: `jrc_ss_gauge_rr 10 tolerance 5.0`
Expected: exit 0, output contains a table.

**TC-GRR-003 — Invalid type**
Command: `jrc_ss_gauge_rr 10 badtype 1.0`
Expected: exit non-zero.

**TC-GRR-004 — Missing arguments**
Command: `jrc_ss_gauge_rr 10`
Expected: exit non-zero, output contains `Usage`.

---

### 5.11 jrc_normality

**TC-NORM-001 — Normal data → normal verdict**
Command: `jrc_normality normal_n30_mean10_sd1_seed42.csv value`
Expected: exit 0, output contains `normal` (case-insensitive) and `✅`.

**TC-NORM-002 — Skewed data → non-normal verdict + Box-Cox attempt**
Command: `jrc_normality skewed_n30_lognormal_seed42.csv value`
Expected: exit 0, output contains `Box-Cox` or `not normal`; script does not error out.

**TC-NORM-003 — File not found**
Command: `jrc_normality nonexistent.csv value`
Expected: exit non-zero, output contains `not found`.

**TC-NORM-004 — Column not found**
Command: `jrc_normality normal_n30_mean10_sd1_seed42.csv badcol`
Expected: exit non-zero, output contains `not found` or `Available`.

**TC-NORM-005 — Missing arguments**
Command: `jrc_normality normal_n30_mean10_sd1_seed42.csv`
Expected: exit non-zero, output contains `Usage`.

---

### 5.12 jrc_outliers

**TC-OUT-001 — No outliers in clean data**
Command: `jrc_outliers normal_n30_mean10_sd1_seed42.csv value`
Expected: exit 0, output contains `no outlier` (case-insensitive) or zero flagged observations.

**TC-OUT-002 — Outlier detected in spiked data**
Command: `jrc_outliers outlier_n30_seed42.csv value`
Expected: exit 0, output contains row ID `15` (the injected outlier) or reports ≥ 1 flagged observation.

**TC-OUT-003 — File not found**
Command: `jrc_outliers nonexistent.csv value`
Expected: exit non-zero.

**TC-OUT-004 — Missing arguments**
Command: `jrc_outliers normal_n30_mean10_sd1_seed42.csv`
Expected: exit non-zero, output contains `Usage`.

---

### 5.13 jrc_capability

**TC-CAP-001 — 2-sided, capable process**
Command: `jrc_capability normal_n30_mean10_sd1_seed42.csv value 7.0 13.0`
Expected: exit 0, output contains `Cp`, `Cpk`, `Pp`, `Ppk`; Cpk > 1.0 (data centred at 10, spec ±3σ).

**TC-CAP-002 — 1-sided upper only**
Command: `jrc_capability normal_n30_mean10_sd1_seed42.csv value - 13.0`
Expected: exit 0, output reports Cpk/Ppk; Cp/Pp absent or noted as not applicable.

**TC-CAP-003 — Both spec limits absent**
Command: `jrc_capability normal_n30_mean10_sd1_seed42.csv value - -`
Expected: exit non-zero.

**TC-CAP-004 — File not found**
Command: `jrc_capability nonexistent.csv value 7.0 13.0`
Expected: exit non-zero.

---

### 5.14 jrc_descriptive

**TC-DESC-001 — Standard normal dataset**
Command: `jrc_descriptive normal_n30_mean10_sd1_seed42.csv value`
Expected: exit 0, output contains `mean`, `median`, `SD`, `min`, `max`, `skewness`; reported mean is within 0.5 of 10.0.

**TC-DESC-002 — File not found**
Command: `jrc_descriptive nonexistent.csv value`
Expected: exit non-zero, output contains `not found`.

**TC-DESC-003 — Column not found**
Command: `jrc_descriptive normal_n30_mean10_sd1_seed42.csv badcol`
Expected: exit non-zero.

**TC-DESC-004 — Missing arguments**
Command: `jrc_descriptive normal_n30_mean10_sd1_seed42.csv`
Expected: exit non-zero, output contains `Usage`.

---

### 5.15 jrc_bland_altman

**TC-BA-001 — Two methods, known bias**
Command: `jrc_bland_altman bland_altman_method1_seed42.csv value bland_altman_method2_seed42.csv value`
Expected: exit 0, output contains `Bias`, `LoA` (or `Limits of Agreement`), `✅` or `⚠️` for bias verdict; PNG file created in the same directory as method1 file.

**TC-BA-002 — No proportional bias expected (NS)**
Command: same as TC-BA-001.
Expected: output contains `p >=` or `No significant proportional bias`.

**TC-BA-003 — Mismatched row counts**
Prepare `method1_short.csv` (10 rows) and use `bland_altman_method2_seed42.csv` (25 rows).
Command: `jrc_bland_altman method1_short.csv value bland_altman_method2_seed42.csv value`
Expected: exit non-zero, output contains `different numbers`.

**TC-BA-004 — File not found**
Command: `jrc_bland_altman nonexistent.csv value bland_altman_method2_seed42.csv value`
Expected: exit non-zero.

**TC-BA-005 — Missing arguments**
Command: `jrc_bland_altman bland_altman_method1_seed42.csv value bland_altman_method2_seed42.csv`
Expected: exit non-zero, output contains `Usage`.

---

### 5.16 jrc_weibull

**TC-WEIB-001 — Standard Weibull fit with censoring**
Command: `jrc_weibull weibull_n20_seed42.csv cycles status`
Expected: exit 0, output contains `beta`, `eta`, `B1`, `B10`, `B50`; beta reported as a positive number within ±50% of 2.0 (true shape); PNG file created.

**TC-WEIB-002 — All units censored (< 2 failures)**
Prepare `all_censored.csv` with all status=0.
Expected: exit non-zero, output contains `failure` or `At least 2`.

**TC-WEIB-003 — Negative time values**
Prepare `neg_times.csv` with one negative time.
Expected: exit non-zero, output contains `positive`.

**TC-WEIB-004 — Status column contains invalid values**
Prepare `bad_status.csv` with status values {0, 1, 2}.
Expected: exit non-zero, output contains `0` and `1` (valid values described).

**TC-WEIB-005 — File not found**
Command: `jrc_weibull nonexistent.csv cycles status`
Expected: exit non-zero.

**TC-WEIB-006 — Missing arguments**
Command: `jrc_weibull weibull_n20_seed42.csv cycles`
Expected: exit non-zero, output contains `Usage`.

---

### 5.17 jrc_verify_attr

**TC-VER-001 — Normal data, 1-sided lower, spec met**
Command: `jrc_verify_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 7.0 -`
Expected: exit 0, output contains `✅` and `Lower Tolerance Limit greater than Lower Spec Limit`.

**TC-VER-002 — Normal data, 1-sided lower, spec not met (tight spec)**
Command: `jrc_verify_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 9.8 -`
Expected: exit 0, output contains `❌` and `Lower Tolerance Limit less than Lower Spec Limit`.

**TC-VER-003 — Normal data, 2-sided, spec met**
Command: `jrc_verify_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 7.0 13.0`
Expected: exit 0, output contains `✅` and `inside Spec`.

**TC-VER-004 — Skewed data, Box-Cox path, spec met**
Command: `jrc_verify_attr 0.95 0.95 skewed_n30_lognormal_seed42.csv value 1.0 -`
Expected: exit 0, output contains `Box-Cox` or `boxcox`; tolerance limit reported in original units.

**TC-VER-005 — spec2 ≤ spec1 (invalid)**
Command: `jrc_verify_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 11.0 9.0`
Expected: exit non-zero, output contains `spec2`.

**TC-VER-006 — PNG file created**
Command: same as TC-VER-001.
Expected: a `*_tolerance.png` file is created in the same directory as the input CSV.

**TC-VER-007 — File not found**
Command: `jrc_verify_attr 0.95 0.95 nonexistent.csv value 7.0 -`
Expected: exit non-zero.

**TC-VER-008 — Missing arguments**
Command: `jrc_verify_attr 0.95 0.95 normal_n30_mean10_sd1_seed42.csv value 7.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.18 jrc_gen_normal

**TC-GEN-N-001 — Reproducible generation with seed**
Command: `jrc_gen_normal 50 10.0 1.0 <output_dir> 42`
Expected: exit 0, file `normal_n50_mean10_sd1_seed42.csv` created in `<output_dir>`; file has 51 lines (header + 50 data rows); `id` column runs 1..50.

**TC-GEN-N-002 — Correct column names**
Expected (from TC-001 output): CSV header is `id,value`.

**TC-GEN-N-003 — Output directory does not exist**
Command: `jrc_gen_normal 50 10.0 1.0 /nonexistent/path 42`
Expected: exit non-zero.

**TC-GEN-N-004 — sd ≤ 0**
Command: `jrc_gen_normal 50 10.0 0 <output_dir> 42`
Expected: exit non-zero.

**TC-GEN-N-005 — Missing arguments**
Command: `jrc_gen_normal 50 10.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.19 jrc_gen_lognormal

**TC-GEN-LN-001 — Reproducible generation with seed**
Command: `jrc_gen_lognormal 50 2.0 0.5 <output_dir> 42`
Expected: exit 0, CSV file created; all values > 0 (log-normal is strictly positive).

**TC-GEN-LN-002 — Correct column names**
Expected (from TC-001 output): header is `id,value`.

**TC-GEN-LN-003 — sdlog ≤ 0**
Command: `jrc_gen_lognormal 50 2.0 0 <output_dir> 42`
Expected: exit non-zero.

**TC-GEN-LN-004 — Missing arguments**
Command: `jrc_gen_lognormal 50 2.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.20 jrc_gen_sqrt

**TC-GEN-SQ-001 — Reproducible generation with seed**
Command: `jrc_gen_sqrt 50 3 1.0 <output_dir> 42`
Expected: exit 0, CSV file created; all values ≥ 0.

**TC-GEN-SQ-002 — Correct column names**
Expected: header is `id,value`.

**TC-GEN-SQ-003 — df ≤ 0**
Command: `jrc_gen_sqrt 50 0 1.0 <output_dir> 42`
Expected: exit non-zero.

**TC-GEN-SQ-004 — Missing arguments**
Command: `jrc_gen_sqrt 50 3`
Expected: exit non-zero, output contains `Usage`.

---

### 5.21 jrc_gen_boxcox

**TC-GEN-BC-001 — Reproducible Weibull generation with seed**
Command: `jrc_gen_boxcox 50 2.0 1000.0 <output_dir> 42`
Expected: exit 0, CSV file created; all values > 0.

**TC-GEN-BC-002 — Correct column names**
Expected: header is `id,value`.

**TC-GEN-BC-003 — shape ≤ 0**
Command: `jrc_gen_boxcox 50 0 1000.0 <output_dir> 42`
Expected: exit non-zero.

**TC-GEN-BC-004 — Missing arguments**
Command: `jrc_gen_boxcox 50 2.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.22 jrc_gen_uniform

**TC-GEN-U-001 — Reproducible generation with seed**
Command: `jrc_gen_uniform 50 0.0 10.0 <output_dir> 42`
Expected: exit 0, CSV file created; all values within [0.0, 10.0].

**TC-GEN-U-002 — Correct column names**
Expected: header is `id,value`.

**TC-GEN-U-003 — max ≤ min**
Command: `jrc_gen_uniform 50 10.0 5.0 <output_dir> 42`
Expected: exit non-zero, output contains `max` or `min`.

**TC-GEN-U-004 — Missing arguments**
Command: `jrc_gen_uniform 50 0.0`
Expected: exit non-zero, output contains `Usage`.

---

### 5.23 jrc_convert_csv

**TC-CCSV-001 — Column by name, auto-delimiter, 3 header lines**
Command: `jrc_convert_csv convert_multicolumn.txt ForceN 3`
Expected: exit 0, output CSV created; header is `id,value`; row count matches data rows in source file; output contains `✅`.

**TC-CCSV-002 — Column by number**
Command: `jrc_convert_csv convert_multicolumn.txt 2 3`
Expected: exit 0, output CSV created with same values as TC-001 (column 2 = ForceN).

**TC-CCSV-003 — Forced tab delimiter**
Command: `jrc_convert_csv convert_multicolumn.txt ForceN 3 tab`
Expected: exit 0, same result as TC-001.

**TC-CCSV-004 — skip_lines exceeds file length**
Command: `jrc_convert_csv convert_multicolumn.txt ForceN 999`
Expected: exit non-zero, output contains `skip_lines`.

**TC-CCSV-005 — Column name not found**
Command: `jrc_convert_csv convert_multicolumn.txt NonExistentCol 3`
Expected: exit non-zero, output contains `not found`.

**TC-CCSV-006 — File not found**
Command: `jrc_convert_csv nonexistent.txt ForceN 0`
Expected: exit non-zero, output contains `not found`.

**TC-CCSV-007 — Invalid delimiter**
Command: `jrc_convert_csv convert_multicolumn.txt ForceN 3 pipe`
Expected: exit non-zero, output contains `delimiter`.

**TC-CCSV-008 — Missing arguments**
Command: `jrc_convert_csv convert_multicolumn.txt ForceN`
Expected: exit non-zero, output contains `Usage`.

---

### 5.24 jrc_convert_txt

**TC-CTXT-001 — Full file, no range**
Command: `jrc_convert_txt convert_singlecolumn.txt`
Expected: exit 0, output CSV created with header `id,value`; 200 data rows; output contains `✅`.

**TC-CTXT-002 — Line range specified**
Command: `jrc_convert_txt convert_singlecolumn.txt 50 100`
Expected: exit 0, output CSV has 51 data rows (lines 50–100 inclusive); filename contains `lines50to100`.

**TC-CTXT-003 — Start line only (no end)**
Command: `jrc_convert_txt convert_singlecolumn.txt 150`
Expected: exit 0, output CSV has 51 rows (lines 150–200); filename contains `lines150to200`.

**TC-CTXT-004 — start_line > total lines**
Command: `jrc_convert_txt convert_singlecolumn.txt 500`
Expected: exit non-zero, output contains `start_line` or `exceeds`.

**TC-CTXT-005 — end_line < start_line**
Command: `jrc_convert_txt convert_singlecolumn.txt 100 50`
Expected: exit non-zero, output contains `end_line`.

**TC-CTXT-006 — File not found**
Command: `jrc_convert_txt nonexistent.txt`
Expected: exit non-zero, output contains `not found`.

**TC-CTXT-007 — Missing arguments**
Command: `jrc_convert_txt`
Expected: exit non-zero, output contains `Usage`.

---

## 6. Test Case Summary

| Script | # Test Cases | Happy-path | Error-path | File I/O |
|---|---|---|---|---|
| jrc_ss_discrete | 5 | 2 | 3 | — |
| jrc_ss_discrete_ci | 4 | 2 | 2 | — |
| jrc_ss_attr | 7 | 3 | 4 | CSV in |
| jrc_ss_attr_check | 3 | 2 | 1 | CSV in |
| jrc_ss_attr_ci | 3 | 2 | 1 | CSV in |
| jrc_ss_sigma | 4 | 2 | 2 | — |
| jrc_ss_paired | 5 | 2 | 3 | — |
| jrc_ss_equivalence | 4 | 2 | 2 | — |
| jrc_ss_fatigue | 5 | 2 | 3 | — |
| jrc_ss_gauge_rr | 4 | 2 | 2 | — |
| jrc_normality | 5 | 2 | 3 | CSV in |
| jrc_outliers | 4 | 2 | 2 | CSV in |
| jrc_capability | 4 | 2 | 2 | CSV in |
| jrc_descriptive | 4 | 2 | 2 | CSV in |
| jrc_bland_altman | 5 | 2 | 3 | CSV in, PNG out |
| jrc_weibull | 6 | 2 | 4 | CSV in, PNG out |
| jrc_verify_attr | 8 | 4 | 4 | CSV in, PNG out |
| jrc_gen_normal | 5 | 2 | 3 | CSV out |
| jrc_gen_lognormal | 4 | 2 | 2 | CSV out |
| jrc_gen_sqrt | 4 | 2 | 2 | CSV out |
| jrc_gen_boxcox | 4 | 2 | 2 | CSV out |
| jrc_gen_uniform | 4 | 2 | 2 | CSV out |
| jrc_convert_csv | 8 | 3 | 5 | File in, CSV out |
| jrc_convert_txt | 7 | 3 | 4 | File in, CSV out |
| **Total** | **117** | **55** | **62** | |

---

## 7. Open Items

| ID | Item |
|---|---|
| OI-001 | Test data files in `oq/data/` must be generated and committed before OQ execution. Use `jrc_gen_*` scripts with the seeds specified in Section 4 for the normal/lognormal datasets; prepare weibull, outlier-spiked, Bland-Altman, and conversion files manually. |
| OI-002 | `admin_oq` script and `oq/` directory structure to be created in the OQ suite implementation phase. |
| OI-003 | The `jrc_ss_fatigue.R` file was found corrupted (contained `admin_scaffold` content) prior to this validation plan and has been replaced. The replacement file must be verified against the test cases in Section 5.9 before OQ execution. |

---

*Last updated: 2026-03-15*
