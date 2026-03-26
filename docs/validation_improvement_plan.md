# JR Anchored — Numerical OQ Enhancement Plan

**Version**: v2.5.0
**Status**: In progress (Tiers 1 & 2 complete)
**Regulatory context**: 21 CFR 820.70(i), ISO 13485:2016 §7.5.6

## Background

Original OQ tests were behavioural-only: exit code + string-presence assertions.
These confirm scripts run and produce output but do not verify computed values are
numerically correct. This plan adds tolerance-based numeric assertions so that each
key calculation has independent, quantitative correctness evidence for audit.

**Key principle**: Each new test case uses a dataset whose expected output can be
computed independently (by hand or in Python from a published formula), not by running
the script itself. The tolerance is set to half the least significant digit of the
printed output.

## Completed phases

| Phase | Module | Tests before | Added | Tests after | Status |
|-------|--------|-------------|-------|-------------|--------|
| 1 | Cap (jrc_cap_normal) | 40 | 5 | 45 | ✅ DONE |
| 2a | MSA Gauge R&R | 53 (total) | 3+2 | 58 | ✅ DONE |
| 2b | MSA Type 1 | — | — | — | ✅ DONE (in phase 2a) |
| 3+4 | SPC (IMR, Xbar-R, Xbar-S, P, C) | 55 | 16 | 71 | ✅ DONE |
| 6 | Corr (Pearson, Regression) | 45 | 5 | 50 | ✅ DONE |
| 8 | AS (Attributes) | 44 | 2 | 46 | ✅ DONE |
| 10 | Curve | 28 | 3 | 31 | ✅ DONE |

**Total OQ test count**: 407 → 440 (+33 numeric correctness assertions)

## What was added per module

### Cap (`repos/cap/oq/`)
New file: `oq/data/cap_cpk_1p000.csv` (26 pts, alternating [9.859, 10.141])
New file: `oq/data/cap_cpk_0p667.csv` (26 pts, alternating [10.109, 10.391])

| TC | Assertion | Expected | Tolerance |
|----|-----------|----------|-----------|
| TC-CAP-N-014 | Cpk for centred data | 1.000 | ±0.005 |
| TC-CAP-N-015 | Cp for centred data | 1.000 | ±0.005 |
| TC-CAP-N-016 | Cpk for offset data | 0.667 | ±0.005 |
| TC-CAP-N-017 | Cp for offset data | 1.000 | ±0.005 |
| TC-CAP-N-018 | Ppk for centred data | 1.739 | ±0.020 |

### MSA (`repos/msa/oq/`)
Dataset: `gauge_rr_balanced.csv` (10 parts × 3 operators × 3 reps)
Dataset: `type1_good.csv` (n=25, reference=10.0, tolerance=0.5)

| TC | Assertion | Expected | Tolerance | Reference |
|----|-----------|----------|-----------|-----------|
| TC-MSA-GRR-011 | %GRR (Study Var) | 4.15% | ±0.10% | AIAG ANOVA |
| TC-MSA-GRR-012 | ndc | 33 | exact | AIAG formula |
| TC-MSA-GRR-013 | Part-to-Part % | 99.91% | ±0.20% | AIAG ANOVA |
| TC-MSA-T1-012 | Cg | 6.250 | ±0.005 | ISO 22514-7 |
| TC-MSA-T1-013 | Cgk | 5.015 | ±0.005 | ISO 22514-7 |

### SPC (`repos/spc/oq/`)
Datasets: `imr_stable.csv`, `xbar_r_stable.csv`, `xbar_s_stable.csv`, `p_stable.csv`, `c_stable.csv`

| TC | Chart | Assertion | Expected | Tolerance |
|----|-------|-----------|----------|-----------|
| TC-SPC-IMR-012 | I-MR | X-bar | 10.0668 | ±0.0001 |
| TC-SPC-IMR-013 | I-MR | UCL_I | 10.9212 | ±0.001 |
| TC-SPC-IMR-014 | I-MR | LCL_I | 9.2124 | ±0.001 |
| TC-SPC-IMR-015 | I-MR | UCL_MR | 1.0495 | ±0.001 |
| TC-SPC-XBR-013 | Xbar-R | Grand X-bar | 50.165 | ±0.001 |
| TC-SPC-XBR-014 | Xbar-R | UCL_x | 50.9151 | ±0.001 |
| TC-SPC-XBR-015 | Xbar-R | LCL_x | 49.4149 | ±0.001 |
| TC-SPC-XBR-016 | Xbar-R | UCL_R | 2.7482 | ±0.001 |
| TC-SPC-XBS-012 | Xbar-S | Grand X-bar | 100.060 | ±0.001 |
| TC-SPC-XBS-013 | Xbar-S | UCL_x | 100.5807 | ±0.001 |
| TC-SPC-XBS-014 | Xbar-S | LCL_x | 99.5393 | ±0.001 |
| TC-SPC-XBS-015 | Xbar-S | UCL_s | 0.8598 | ±0.001 |
| TC-SPC-P-012 | P | p-bar | 0.04160 | ±0.0001 |
| TC-SPC-P-013 | P | UCL | 0.10150 | ±0.0010 |
| TC-SPC-C-011 | C | c-bar | 4.960 | ±0.001 |
| TC-SPC-C-012 | C | UCL | 11.641 | ±0.010 |

### Corr (`repos/corr/oq/`)
New file: `oq/data/corr_exact_linear.csv` (10 pts, y=2x+1)

| TC | Assertion | Expected | Tolerance |
|----|-----------|----------|-----------|
| TC-CORR-P-012 | Pearson r | 1.000 | ±0.001 |
| TC-CORR-P-013 | p-value significant | < 0.001 | — |
| TC-CORR-R-012 | OLS slope | 2.000 | ±0.001 |
| TC-CORR-R-013 | OLS intercept | 1.000 | ±0.001 |
| TC-CORR-R-014 | R-squared | 1.000 | ±0.001 |

### AS (`repos/as/oq/`)
Plan: N=500, AQL=0.01, RQL=0.10 → n=51, c=2

| TC | Assertion | Expected | Tolerance | Reference |
|----|-----------|----------|-----------|-----------|
| TC-AS-ATTR-012 | Pa(AQL=0.01) | 0.9913 | ±0.0005 | Hypergeom CDF |
| TC-AS-ATTR-013 | Pa(RQL=0.10) | 0.0918 | ±0.0005 | Hypergeom CDF |

### Curve (`repos/curve/oq/`)
Dataset: `linear.csv` (y=2x, x=0..20), `test_slope.cfg`, `test_query.cfg`

| TC | Assertion | Expected | Tolerance |
|----|-----------|----------|-----------|
| TC-CURVE-N-001 | AUC (trapezoid) | 400.0 | ±0.5 |
| TC-CURVE-N-002 | overall slope | 2.000 | ±0.001 |
| TC-CURVE-N-003 | Y at x=5 | 10.0 | ±0.01 |

## Remaining work (Phase 9 — Community scripts, Tier 3)

Community scripts (oq/ at project root) already have some numeric assertions
(e.g., `"300" in out` for jrc_ss_discrete). Lower priority for regulatory audit
since these scripts are decision-aid tools, not release gates.

Candidate additions:
- `jrc_ss_discrete`: extract n integer from output, assert n == 300
- `jrc_ss_variables`: known z-formula solution → extract n
- `jrc_descriptive`: known mean/SD from seed-fixed data → extract and assert

## Version milestone

After all phases including Phase 9: bump to **v2.5.0** with CHANGELOG entry.
Update `web/index.html` stats: scripts count unchanged (46), OQ tests: 407 → 440+.

## Audit evidence

- Each module's `admin_<module>_oq` runner produces a timestamped evidence file
  in `~/.jrscript/<PROJECT_ID>/validation/`.
- Evidence files include the full pytest output with PASS/FAIL per TC.
- The independent derivations are documented in each test class docstring and
  in this file, providing traceability to published formulas.
