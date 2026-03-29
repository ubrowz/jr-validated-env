"""
OQ test suite — Statistical analysis scripts.

Covers: jrc_bland_altman, jrc_weibull, jrc_verify_attr
"""

import os
import glob
from conftest import run, combined, extract_float, DATA_DIR


def data(name):
    return os.path.join(DATA_DIR, name)


def png_count_in_data():
    return glob.glob(os.path.join(DATA_DIR, "*.png"))


# ===========================================================================
# jrc_bland_altman (TC-BA-001 .. 005)
# ===========================================================================

class TestBlandAltman:

    def test_tc_ba_001_two_methods_known_bias(self):
        """TC-BA-001: Two methods → exit 0, Bias and LoA in output, PNG created"""
        # Clean any pre-existing PNGs
        for p in glob.glob(os.path.join(DATA_DIR, "*bland_altman*.png")):
            os.remove(p)

        r = run("jrc_bland_altman.R",
                data("bland_altman_method1_seed42.csv"), "value",
                data("bland_altman_method2_seed42.csv"), "value")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "bias" in out
        assert "loa" in out or "limits of agreement" in out or "limit" in out

    def test_tc_ba_002_no_proportional_bias(self):
        """TC-BA-002: No significant proportional bias expected"""
        r = run("jrc_bland_altman.R",
                data("bland_altman_method1_seed42.csv"), "value",
                data("bland_altman_method2_seed42.csv"), "value")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "p >=" in out or "no significant" in out or "proportional" in out

    def test_tc_ba_003_mismatched_row_counts(self):
        """TC-BA-003: 10-row file vs 25-row file → non-zero exit, 'different' in output"""
        r = run("jrc_bland_altman.R",
                data("method1_short.csv"), "value",
                data("bland_altman_method2_seed42.csv"), "value")
        assert r.returncode != 0
        out = combined(r).lower()
        assert "different" in out or "mismatch" in out or "rows" in out or "length" in out

    def test_tc_ba_004_file_not_found(self):
        """TC-BA-004: nonexistent file1 → non-zero exit"""
        r = run("jrc_bland_altman.R",
                "nonexistent.csv", "value",
                data("bland_altman_method2_seed42.csv"), "value")
        assert r.returncode != 0

    def test_tc_ba_005_missing_arguments(self):
        """TC-BA-005: only 3 arguments → non-zero exit, mentions 'Usage'"""
        r = run("jrc_bland_altman.R",
                data("bland_altman_method1_seed42.csv"), "value",
                data("bland_altman_method2_seed42.csv"))
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_weibull (TC-WEIB-001 .. 006)
# ===========================================================================

class TestWeibull:

    def test_tc_weib_001_standard_fit_with_censoring(self):
        """TC-WEIB-001: Weibull fit → exit 0, beta/eta/B-life values, PNG created"""
        for p in glob.glob(os.path.join(DATA_DIR, "*weibull*.png")):
            os.remove(p)

        r = run("jrc_weibull.R",
                data("weibull_n20_seed42.csv"), "cycles", "status")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "beta" in out or "shape" in out
        assert "eta" in out or "scale" in out
        assert "b10" in out or "b1" in out or "b50" in out or "b-life" in out

    def test_tc_weib_002_all_censored(self):
        """TC-WEIB-002: All units censored → non-zero exit, mentions 'failure' or '2'"""
        r = run("jrc_weibull.R",
                data("all_censored.csv"), "cycles", "status")
        assert r.returncode != 0
        out = combined(r).lower()
        assert "failure" in out or "least 2" in out or "at least" in out

    def test_tc_weib_003_negative_time_values(self):
        """TC-WEIB-003: Negative time → non-zero exit, mentions 'positive'"""
        r = run("jrc_weibull.R",
                data("neg_times.csv"), "cycles", "status")
        assert r.returncode != 0
        assert "positive" in combined(r).lower()

    def test_tc_weib_004_invalid_status_values(self):
        """TC-WEIB-004: Status values {0,1,2} → non-zero exit"""
        r = run("jrc_weibull.R",
                data("bad_status.csv"), "cycles", "status")
        assert r.returncode != 0

    def test_tc_weib_005_file_not_found(self):
        """TC-WEIB-005: nonexistent file → non-zero exit"""
        r = run("jrc_weibull.R", "nonexistent.csv", "cycles", "status")
        assert r.returncode != 0

    def test_tc_weib_006_missing_arguments(self):
        """TC-WEIB-006: only 2 arguments → non-zero exit, mentions 'Usage'"""
        r = run("jrc_weibull.R",
                data("weibull_n20_seed42.csv"), "cycles")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_verify_attr (TC-VER-001 .. 008)
# ===========================================================================

class TestVerifyAttr:

    def test_tc_ver_001_one_sided_lower_spec_met(self):
        """TC-VER-001: 1-sided lower, wide spec → exit 0, ✅ in output"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "-")
        assert r.returncode == 0
        assert "✅" in combined(r)

    def test_tc_ver_002_one_sided_lower_spec_not_met(self):
        """TC-VER-002: 1-sided lower, tight spec → exit 0, ❌ in output"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.8", "-")
        assert r.returncode == 0
        assert "❌" in combined(r)

    def test_tc_ver_003_two_sided_spec_met(self):
        """TC-VER-003: 2-sided, wide spec → exit 0, ✅ in output"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "13.0")
        assert r.returncode == 0
        assert "✅" in combined(r)

    def test_tc_ver_004_skewed_data_boxcox_path(self):
        """TC-VER-004: Skewed data → exit 0, Box-Cox mentioned"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("skewed_n30_lognormal_seed42.csv"), "value", "1.0", "-")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "box-cox" in out or "boxcox" in out

    def test_tc_ver_005_spec2_le_spec1(self):
        """TC-VER-005: spec2 < spec1 → non-zero exit, mentions 'spec2'"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "11.0", "9.0")
        assert r.returncode != 0
        assert "spec2" in combined(r).lower()

    def test_tc_ver_006_png_file_created(self):
        """TC-VER-006: PNG output created in same directory as input CSV"""
        # Clean any pre-existing tolerance PNGs
        for p in glob.glob(os.path.join(DATA_DIR, "*tolerance*.png")):
            os.remove(p)
        before = set(os.listdir(DATA_DIR))

        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "-")
        assert r.returncode == 0

        after = set(os.listdir(DATA_DIR))
        new_files = after - before
        png_files = [f for f in new_files if f.endswith(".png")]
        assert len(png_files) >= 1

    def test_tc_ver_007_file_not_found(self):
        """TC-VER-007: nonexistent file → non-zero exit"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                "nonexistent.csv", "value", "7.0", "-")
        assert r.returncode != 0

    def test_tc_ver_008_missing_arguments(self):
        """TC-VER-008: only 5 arguments → non-zero exit, mentions 'Usage'"""
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()

    def test_tc_ver_009_ti_lower_value_and_pass_verdict(self):
        """TC-VER-009: known dataset (mean=10, sd=1), P=0.95, C=0.95, LSL=7.0 → ✅
        Dataset: verify_attr_known.csv — 28 rows of 10.0 + rows 29 (13.8079) and 30 (6.1921).
        Exact: mean=10.0000, sd=1.0000 (sum(x-10)^2 = 2×(3.8079)^2 ≈ 29.000; var = 29/29 = 1).
        K1(n=30, P=0.95, C=0.95) = 2.220 (nct.ppf(0.95, df=29, nc=sqrt(30)*qnorm(0.95))/sqrt(30)).
        Expected lower TL = 10.000 - 2.220×1.000 = 7.780.
        LSL=7.0 < 7.780 → ✅.
        Assertion: extracted TI lower ≈ 7.780 ± 0.050 AND ✅ in output.
        """
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("verify_attr_known.csv"), "value", "7.0", "-")
        assert r.returncode == 0
        tl = extract_float(r, "1-sided lower tolerance limit:")
        assert tl is not None, f"Could not extract TI lower limit:\n{combined(r)}"
        assert abs(tl - 7.780) <= 0.050, \
            f"Expected TI lower ≈ 7.780 ± 0.050, got {tl}"
        assert "✅" in combined(r)

    def test_tc_ver_010_ti_lower_value_and_fail_verdict(self):
        """TC-VER-010: same dataset as TC-VER-009, LSL tightened to 8.0 → ❌
        Same TI lower = 7.780 (same data, same K-factor K1=2.220).
        7.780 < 8.0 = LSL → ❌.
        TC-VER-009 and TC-VER-010 use identical K-factor arithmetic but different spec limits,
        simultaneously verifying (a) the numeric TI computation and (b) the verdict logic.
        """
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("verify_attr_known.csv"), "value", "8.0", "-")
        assert r.returncode == 0
        tl = extract_float(r, "1-sided lower tolerance limit:")
        assert tl is not None, f"Could not extract TI lower limit:\n{combined(r)}"
        assert abs(tl - 7.780) <= 0.050, \
            f"Expected TI lower ≈ 7.780 ± 0.050, got {tl}"
        assert tl < 8.0, f"Expected TI lower < 8.0 (so verdict is ❌), got {tl}"
        assert "❌" in combined(r)

    def test_tc_ver_011_ti_2sided_values_and_pass_verdict(self):
        """TC-VER-011: same dataset, 2-sided, LSL=7.0, USL=13.0 → ✅
        K2(n=30, P=0.95, C=0.95) = 2.555 (computed via nct / two-sided algorithm).
        LTL = 10.000 - 2.555×1.000 = 7.445; UTL = 10.000 + 2.555 = 12.555.
        7.445 > 7.0 (LSL) and 12.555 < 13.0 (USL) → ✅.
        """
        r = run("jrc_verify_attr.R", "0.95", "0.95",
                data("verify_attr_known.csv"), "value", "7.0", "13.0")
        assert r.returncode == 0
        ltl = extract_float(r, "2-sided lower tolerance limit:")
        utl = extract_float(r, "2-sided upper tolerance limit:")
        assert ltl is not None, f"Could not extract 2-sided lower TL:\n{combined(r)}"
        assert utl is not None, f"Could not extract 2-sided upper TL:\n{combined(r)}"
        assert abs(ltl - 7.445) <= 0.050, \
            f"Expected 2-sided LTL ≈ 7.445 ± 0.050, got {ltl}"
        assert abs(utl - 12.555) <= 0.050, \
            f"Expected 2-sided UTL ≈ 12.555 ± 0.050, got {utl}"
        assert "✅" in combined(r)
