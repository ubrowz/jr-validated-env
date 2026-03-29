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

## Phase 9 — Community scripts OQ plan

### Revised risk assessment

The original Tier 3 classification assumed community scripts are "decision-aid tools" with
no direct compliance impact. Two categories require a higher tier assignment.

**Argument 1 — Sample size scripts are verification design inputs**

Scripts in the `jrc_ss_*` family directly determine the number of units to be tested in a
design verification protocol. If the computed n is incorrect:

- The verification study is either under-powered (false-pass risk) or unnecessarily over-powered.
- A wrong n at f = 0 means the stated reliability/confidence pairing cannot be justified
  statistically in an FDA submission.
- The output of `jrc_ss_discrete` and `jrc_ss_discrete_ci` is typically transcribed verbatim
  into the verification protocol. A numerical error there invalidates the entire verification
  conclusion for that performance characteristic.

Existing tests for these scripts assert only behavioural properties (exit code, string presence).
`"300" in out` does not distinguish a correct result from a coincidental match.

**Argument 2 — jrc_verify_attr produces a binding pass/fail verdict**

`jrc_verify_attr` computes a statistical tolerance interval and compares it against engineering
spec limits, printing ✅ or ❌. This verdict:

- Constitutes the formal verification conclusion for continuous measurement characteristics.
- A false ✅ (tolerance interval that exceeds a spec limit, but script reports pass) is a
  direct patient-safety risk if it leads to design acceptance.
- The tolerance limits depend on a K-factor (from the `tolerance` R package) and on the
  mean and SD of the dataset. A numeric error in either — or in the back-transformation
  after Box-Cox — can flip the verdict.

Existing tests TC-VER-001..008 confirm only that a ✅ or ❌ symbol appears. They do not
verify that the tolerance limit value used to make the determination is numerically correct.

### Tier assignments for Phase 9

| Tier | Scripts | Rationale |
|------|---------|-----------|
| 9A — Highest | `jrc_ss_discrete`, `jrc_ss_discrete_ci` | Binomial formulas, exact closed-form; wrong n directly invalidates a DV study |
| 9B — Highest | `jrc_verify_attr` | Tolerance interval verdict; false ✅ is a patient-safety failure |
| 9C — High | `jrc_ss_attr`, `jrc_ss_attr_check`, `jrc_ss_attr_ci` | Attribute sample sizing and reporting; iterative computation via tolerance package |
| 9D — High | `jrc_ss_sigma` | Pilots the SD estimate that feeds into jrc_ss_attr; exact closed-form formula |
| 9E — Medium | `jrc_ss_fatigue`, `jrc_ss_paired`, `jrc_ss_equivalence` | Verification planning; closed-form but upstream of protocol (not the pass/fail gate) |
| Confirmed Tier 3 | `jrc_descriptive`, `jrc_normality`, `jrc_gen_*`, `jrc_doe_*`, `jrc_bland_altman`, `jrc_weibull`, `jrc_capability`, `jrc_outliers` | Exploratory/analytical tools; do not produce a compliance conclusion |

---

### Phase 9A — jrc_ss_discrete: binomial sample size (Tier 1 uplift)

**Formula (source: ASTM F3172-15, NIST/SEMATECH §7.2.4.1):**

```
n = ceiling( qchisq(C, df = 2f + 2) / (2 × (1 − P)) )
```

For f = 0 and df = 2 the chi-squared CDF has the closed form F(x) = 1 − exp(−x/2), so
`qchisq(C, 2) = −2 ln(1−C)`. All values below are therefore independently verifiable
with pencil, calculator, or three lines of Python — no R or external packages required.

| TC | P | C | f | Expected n | Independent derivation |
|----|---|----|---|------------|------------------------|
| TC-DISC-006 | 0.99 | 0.95 | 0 | 300 | ⌈5.9915 / 0.02⌉ = ⌈299.57⌉ = 300 |
| TC-DISC-007 | 0.99 | 0.95 | 1 | 475 | ⌈9.4877 / 0.02⌉ = ⌈474.39⌉ = 475 |
| TC-DISC-008 | 0.95 | 0.90 | 0 |  47 | ⌈4.6052 / 0.10⌉ = ⌈46.05⌉  =  47 |
| TC-DISC-009 | 0.99 | 0.99 | 0 | 461 | ⌈9.2103 / 0.02⌉ = ⌈460.52⌉ = 461 |

Tolerance: exact integer — assert `n == expected` (no rounding uncertainty after ceiling).

The existing TC-DISC-001 (`"300" in out`) is already satisfied by TC-DISC-006 and may be
retained as a redundant smoke test or removed to avoid duplication.

---

### Phase 9A — jrc_ss_discrete_ci: achieved proportion (Tier 1 uplift)

**Formula (source: Clopper & Pearson 1934; the standard for regulatory submissions):**

```
proportion = 1 − qbeta(1 − C,  f + 1,  n − f)
```

For f = 0: `qbeta(p, 1, n) = 1 − (1−p)^{1/n}` (exact closed-form for Beta(1, n)).
This means `proportion = 1 − (1−C)^{1/n}` — verifiable without any statistical library.

| TC | C | n | f | Expected proportion | Independent derivation |
|----|---|---|---|--------------------|-----------------------|
| TC-DISCICI-005 | 0.95 | 300 | 0 | 0.9998 | 1 − qbeta(0.05, 1, 300) = 1 − (1 − 0.95^{1/300}) = 0.99983 |
| TC-DISCICI-006 | 0.95 |  22 | 0 | 0.9977 | 1 − qbeta(0.05, 1, 22) = 1 − (1 − 0.95^{1/22}) = 0.99767 |

Tolerance: ±0.0001 (one unit of last printed decimal place).

**Consistency pairing with Phase 9A:**
`jrc_ss_discrete` says n = 300 achieves P = 0.99 at C = 0.95.
TC-DISCICI-005 independently confirms this: n = 300, f = 0, C = 0.95 → proportion = 0.9998 > 0.99 ✓
n = 22 (TC-DISCICI-006) achieves only 0.9977 — correctly below the 0.99 threshold,
confirming the sample size formula is not trivially conservative.

---

### Phase 9B — jrc_verify_attr: tolerance interval verdict (Tier 1 uplift)

**Risk statement:** The ✅/❌ verdict is the formal DV conclusion for the tested characteristic.
The existing tests confirm only symbol presence; they do not verify the numeric TI value that
produces the verdict.

**Test dataset: `oq/data/verify_attr_known.csv`** (new file to be created)
- n = 30 observations
- Constructed so that `mean(x) = 10.000` and `sd(x) = 1.000` to 3 decimal places
- All values normal (skewness < 0.1 by construction), guaranteeing the normal path;
  Box-Cox path is not exercised in these TCs
- Dataset construction script to be committed alongside the test for audit traceability

**K-factor reference (1-sided, n = 30, P = 0.95, C = 0.95):**
- K₁ = 1.778 (Hahn & Meeker 2017 Table A.7; NIST/SEMATECH e-Handbook §5.5.3.3)
- Reproduced by: `tolerance::K.factor(30, alpha=0.05, P=0.95, side=1, method="EXACT")`
- Lower TL = mean − K₁ × SD = 10.000 − 1.778 × 1.000 = **8.222**

**K-factor reference (2-sided, n = 30, P = 0.95, C = 0.95):**
- K₂ ≈ 2.220 (same references)
- LTL = 10.000 − 2.220 = **7.780**;  UTL = 10.000 + 2.220 = **12.220**

| TC | Dataset | Spec limits | Expected TI limit | Expected verdict | Key assertion |
|----|---------|-------------|-------------------|-----------------|---------------|
| TC-VER-009 | verify_attr_known.csv | LSL = 7.0, USL = − | Lower TL ≈ 8.222 ± 0.050 | ✅ | Extract TI value from output; assert ≈ 8.222; assert ✅ present |
| TC-VER-010 | verify_attr_known.csv | LSL = 8.5, USL = − | Lower TL ≈ 8.222 ± 0.050 | ❌ | Same TI value; assert TL < LSL = 8.5; assert ❌ present |
| TC-VER-011 | verify_attr_known.csv | LSL = 7.5, USL = 12.5 | LTL ≈ 7.780 ± 0.050 | ✅ | Extract both limits; assert within tolerance; assert ✅ present |

TC-VER-009 and TC-VER-010 use identical data and identical K-factor arithmetic but different
spec limits. They simultaneously verify (a) the numeric TI computation and (b) that the
verdict logic correctly distinguishes pass from fail for limits that straddle the same TI value.

**Extraction approach:** The script prints lines of the form `1-sided lower tolerance limit:  8.222`
(or similar). The `extract_float()` helper already present in the project-root `conftest.py`
can be used directly.

---

### Phase 9C — jrc_ss_attr, jrc_ss_attr_check, jrc_ss_attr_ci (Tier 1)

> **Deferred:** Numeric assertions for non-normal data paths (Box-Cox transformation in
> `jrc_ss_attr` and `jrc_verify_attr`) are not included in the current implementation.
> Non-normal TI limits require back-transformation of the K-factor interval, making
> independent derivation significantly more involved. These will be added in a later phase
> using purpose-built skewed test datasets with known Box-Cox lambda values.



These scripts compute n for tolerance-interval-based verification (jrc_ss_attr), check
whether a planned n is sufficient (jrc_ss_attr_check), and report the achieved proportion
from a completed study (jrc_ss_attr_ci).

**Independent derivation approach (iterative, unlike 9A):**
The minimum n is the smallest integer such that K₁(n) × SD ≤ mean − LSL (for 1-sided lower).
K₁(n) is a strictly decreasing function of n; values are tabulated in Hahn & Meeker and
reproduced by `K.factor()`. During implementation, expected n is computed in the test via
a small Python loop using `scipy.stats` or from a pre-computed lookup — not by running the
script under test.

Planned test cases (TC-ATTR-008, TC-ATTRCK-004, TC-ATTRCI-004 — exact IDs TBD during
implementation):
- `jrc_ss_attr`: known pilot dataset + wide spec → assert required n == independently computed value
- `jrc_ss_attr_check`: planned_N at exactly the required n → assert ✅ (boundary pass)
- `jrc_ss_attr_ci`: known dataset → extract and assert reported achieved proportion ± 0.005

---

### Phase 9D — jrc_ss_sigma: pilot study sample size (Tier 1)

**Formula (source: Browne 2001; Montgomery 2012 §3.3):**

```
n = ceiling( ((z_α + z_β) / precision)² ) + 1
```

where z_α = qnorm(C) for 1-sided or qnorm(1 − (1−C)/2) for 2-sided.

Standard normal quantiles used in derivations below (4 dp):
`qnorm(0.90) = 1.2816`,  `qnorm(0.95) = 1.6449`,  `qnorm(0.975) = 1.9600`,  `qnorm(0.99) = 2.3263`

| TC | precision | Sides | Power | C | Expected n | Independent derivation |
|----|-----------|-------|-------|---|------------|------------------------|
| TC-SIGMA-005 | 1.5 | 1 | 0.90 | 0.95 |  5 | ⌈((1.6449+1.2816)/1.5)²⌉+1 = ⌈3.806⌉+1 = 5 |
| TC-SIGMA-006 | 1.0 | 2 | 0.95 | 0.95 | 14 | ⌈((1.9600+1.6449)/1.0)²⌉+1 = ⌈12.995⌉+1 = 14 |
| TC-SIGMA-007 | 2.0 | 1 | 0.90 | 0.90 |  3 | ⌈((1.2816+1.2816)/2.0)²⌉+1 = ⌈1.642⌉+1 = 3 |

Tolerance: exact integer assertions.

---

### Phase 9E — jrc_ss_fatigue, jrc_ss_paired, jrc_ss_equivalence (Medium)

All three use variants of the chi-squared / normal-quantile formula, independently verifiable.

**jrc_ss_fatigue** — Weibull-adjusted chi-squared method (Nelson 2004; Meeker et al. 2017):

```
p_eff = 1 − R^(AF^β)
n     = ceiling( qchisq(C, 2f+2) / (2 × p_eff) )
```

| TC | R | C | β | AF | f | Expected n | Independent derivation |
|----|---|---|---|----|---|------------|------------------------|
| TC-FAT-006 | 0.90 | 0.95 | 2 | 1.0 | 0 | 30 | p_eff=0.10; ⌈5.9915/0.20⌉=30 (identical to ss_discrete at P=0.90) |
| TC-FAT-007 | 0.90 | 0.95 | 2 | 2.0 | 0 |  9 | p_eff=1−0.9^4=0.3439; ⌈5.9915/0.6878⌉=⌈8.71⌉=9 |

Note: TC-FAT-006 with AF = 1 must equal `jrc_ss_discrete(P=0.90, C=0.95, f=0)` = 30.
This cross-script consistency check is itself an audit-quality assertion.

**jrc_ss_paired** — paired t-test formula (Rosner 2015 §8):

```
n = ceiling( ((z_α + z_β) / effect_size)² ) + 1,   effect_size = delta / sd
```

| TC | delta | sd | Sides | Power | C | Expected n | Independent derivation |
|----|-------|----|-------|-------|---|------------|------------------------|
| TC-PAIRED-006 | 0.5 | 1.0 | 2 | 0.90 | 0.95 | 43 | ⌈((1.9600+1.2816)/0.5)²⌉+1 = ⌈42.03⌉+1 = 43 |
| TC-PAIRED-007 | 0.5 | 1.0 | 1 | 0.90 | 0.95 | 35 | ⌈((1.6449+1.2816)/0.5)²⌉+1 = ⌈34.26⌉+1 = 35 |

**jrc_ss_equivalence** — TOST formula (same structure as paired):
Planned test cases TC-EQUIV-005..006 using the same derivation approach as paired.
Specific values to be confirmed by reading the equivalence formula in the script source.

---

### Implementation notes

1. New test data file `oq/data/verify_attr_known.csv` must be generated with a short
   Python script committed to `oq/data/` (or as a pytest fixture) so the exact mean
   and SD are auditable — not just asserted.

2. All new TCs follow the same `extract_float()` + tolerance pattern established in
   Phases 1–8. No new infrastructure required.

3. The cross-script check in TC-FAT-006 (fatigue = discrete at equivalent inputs) is
   not a new script execution — it compares two independently run results and is a
   particularly strong audit argument for formula correctness.

4. After all Phase 9 sub-phases are implemented, run `admin_create_hash` and re-run
   the full OQ suite (≥ 440 tests) before tagging the version milestone.

---

## Version milestone

After all phases including Phase 9: bump to **v2.6.0** with CHANGELOG entry.
Update `web/index.html` stats: scripts count unchanged (46), OQ tests: 440 → updated count.

## Audit evidence

- Each module's `admin_<module>_oq` runner produces a timestamped evidence file
  in `~/.jrscript/<PROJECT_ID>/validation/`.
- Evidence files include the full pytest output with PASS/FAIL per TC.
- The independent derivations are documented in each test class docstring and
  in this file, providing traceability to published formulas.
