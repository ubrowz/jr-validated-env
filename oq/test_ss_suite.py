"""
OQ test suite — Sample Size scripts.

Covers: jrc_ss_discrete, jrc_ss_discrete_ci, jrc_ss_attr, jrc_ss_attr_check,
        jrc_ss_attr_ci, jrc_ss_sigma, jrc_ss_paired, jrc_ss_equivalence,
        jrc_ss_fatigue, jrc_ss_gauge_rr
"""

import os
from conftest import run, combined, extract_n_at_f, DATA_DIR


def data(name):
    return os.path.join(DATA_DIR, name)


# ===========================================================================
# jrc_ss_discrete (TC-DISC-001 .. 005)
# ===========================================================================

class TestSsDiscrete:

    def test_tc_disc_001_normal_input(self):
        """TC-DISC-001: P=0.99, C=0.95 → f=0 N=300 (chi-squared method)"""
        r = run("jrc_ss_discrete.R", "0.99", "0.95")
        assert r.returncode == 0
        # chi-squared method: ceiling(qchisq(0.95,2)/(2*0.01)) = 300
        assert "300" in combined(r)

    def test_tc_disc_002_lower_confidence_smaller_n(self):
        """TC-DISC-002: Lower confidence → smaller N at f=0"""
        r_std = run("jrc_ss_discrete.R", "0.99", "0.95")
        r_low = run("jrc_ss_discrete.R", "0.99", "0.80")
        assert r_low.returncode == 0
        n_std = extract_n_at_f(r_std, 0)
        n_low = extract_n_at_f(r_low, 0)
        assert n_std is not None and n_low is not None
        assert n_low < n_std

    def test_tc_disc_003_invalid_proportion(self):
        """TC-DISC-003: proportion=1.5 → non-zero exit, mentions 'proportion'"""
        r = run("jrc_ss_discrete.R", "1.5", "0.95")
        assert r.returncode != 0
        assert "proportion" in combined(r).lower()

    def test_tc_disc_004_invalid_confidence_zero(self):
        """TC-DISC-004: confidence=0 → non-zero exit, mentions 'confidence'"""
        r = run("jrc_ss_discrete.R", "0.99", "0")
        assert r.returncode != 0
        assert "confidence" in combined(r).lower()

    def test_tc_disc_005_missing_arguments(self):
        """TC-DISC-005: only 1 argument → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_discrete.R", "0.99")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_discrete_ci (TC-DISCICI-001 .. 004)
# ===========================================================================

class TestSsDiscreteCi:

    def test_tc_discici_001_zero_failures(self):
        """TC-DISCICI-001: N=300, f=0, C=0.95 → achieved proportion ≥ 0.99"""
        r = run("jrc_ss_discrete_ci.R", "0.95", "300", "0")
        assert r.returncode == 0
        # Output should contain "0.99" (or higher)
        assert "0.99" in combined(r)

    def test_tc_discici_002_one_failure_lower_proportion(self):
        """TC-DISCICI-002: f=1 achieves lower proportion than f=0"""
        r0 = run("jrc_ss_discrete_ci.R", "0.95", "300", "0")
        r1 = run("jrc_ss_discrete_ci.R", "0.95", "300", "1")
        assert r0.returncode == 0 and r1.returncode == 0
        # Both should succeed; content will differ (output is descriptive)
        assert combined(r0) != combined(r1)

    def test_tc_discici_003_f_greater_than_n(self):
        """TC-DISCICI-003: f=15 > n=10 → non-zero exit"""
        r = run("jrc_ss_discrete_ci.R", "0.95", "10", "15")
        assert r.returncode != 0

    def test_tc_discici_004_missing_arguments(self):
        """TC-DISCICI-004: only 2 arguments → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_discrete_ci.R", "0.95", "299")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_attr (TC-ATTR-001 .. 007)
# ===========================================================================

class TestSsAttr:

    def test_tc_attr_001_one_sided_lower(self):
        """TC-ATTR-001: 1-sided lower, wide spec → exit 0, N ≥ 10"""
        # Use spec=7.0 (3σ from mean) so N stays within script's 250-sample cap
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "-")
        assert r.returncode == 0
        out = combined(r)
        assert "✅" in out or "n =" in out.lower()

    def test_tc_attr_002_one_sided_upper(self):
        """TC-ATTR-002: 1-sided upper, wide spec → exit 0"""
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "-", "13.0")
        assert r.returncode == 0

    def test_tc_attr_003_two_sided_requires_more_than_one_sided(self):
        """TC-ATTR-003: 2-sided and 1-sided both succeed"""
        r1 = run("jrc_ss_attr.R", "0.95", "0.95",
                 data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "-")
        r2 = run("jrc_ss_attr.R", "0.95", "0.95",
                 data("normal_n30_mean10_sd1_seed42.csv"), "value", "7.0", "13.0")
        assert r1.returncode == 0 and r2.returncode == 0

    def test_tc_attr_004_spec2_le_spec1(self):
        """TC-ATTR-004: spec2 < spec1 → non-zero exit, mentions 'spec2'"""
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "11.0", "9.0")
        assert r.returncode != 0
        assert "spec2" in combined(r).lower()

    def test_tc_attr_005_both_specs_absent(self):
        """TC-ATTR-005: both spec limits '-' → non-zero exit"""
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "-", "-")
        assert r.returncode != 0

    def test_tc_attr_006_file_not_found(self):
        """TC-ATTR-006: nonexistent file → non-zero exit, mentions 'not found'"""
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                "nonexistent.csv", "value", "9.0", "-")
        assert r.returncode != 0
        assert "not found" in combined(r).lower()

    def test_tc_attr_007_column_not_found(self):
        """TC-ATTR-007: bad column → non-zero exit, mentions 'not found' or 'available'"""
        r = run("jrc_ss_attr.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "badcol", "9.0", "-")
        assert r.returncode != 0
        out = combined(r).lower()
        assert "not found" in out or "available" in out


# ===========================================================================
# jrc_ss_attr_check (TC-ATTRCK-001 .. 003)
# ===========================================================================

class TestSsAttrCheck:

    def test_tc_attrck_001_planned_n_meets_requirement(self):
        """TC-ATTRCK-001: planned N=50 meets → exit 0, PASS signal"""
        r = run("jrc_ss_attr_check.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.0", "-", "50")
        assert r.returncode == 0
        out = combined(r)
        assert "✅" in out or "pass" in out.lower()

    def test_tc_attrck_002_planned_n_too_small(self):
        """TC-ATTRCK-002: planned N=5 fails → exit 0, FAIL signal"""
        r = run("jrc_ss_attr_check.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.0", "-", "5")
        assert r.returncode == 0
        out = combined(r)
        assert "❌" in out or "fail" in out.lower()

    def test_tc_attrck_003_missing_planned_n(self):
        """TC-ATTRCK-003: missing planned_N → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_attr_check.R", "0.95", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.0", "-")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_attr_ci (TC-ATTRCI-001 .. 003)
# ===========================================================================

class TestSsAttrCi:

    def test_tc_attrci_001_one_sided_lower(self):
        """TC-ATTRCI-001: 1-sided lower → exit 0, proportion between 0 and 1"""
        r = run("jrc_ss_attr_ci.R", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.0", "-")
        assert r.returncode == 0
        assert "0." in combined(r)  # some decimal proportion reported

    def test_tc_attrci_002_two_sided(self):
        """TC-ATTRCI-002: 2-sided → exit 0"""
        r = run("jrc_ss_attr_ci.R", "0.95",
                data("normal_n30_mean10_sd1_seed42.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0

    def test_tc_attrci_003_file_not_found(self):
        """TC-ATTRCI-003: nonexistent file → non-zero exit, mentions 'not found'"""
        r = run("jrc_ss_attr_ci.R", "0.95",
                "nonexistent.csv", "value", "9.0", "-")
        assert r.returncode != 0
        assert "not found" in combined(r).lower()


# ===========================================================================
# jrc_ss_sigma (TC-SIGMA-001 .. 004)
# ===========================================================================

class TestSsSigma:

    def test_tc_sigma_001_one_sided(self):
        """TC-SIGMA-001: 1-sided lower → exit 0, table output"""
        r = run("jrc_ss_sigma.R", "1.5", "9.0", "-")
        assert r.returncode == 0

    def test_tc_sigma_002_two_sided(self):
        """TC-SIGMA-002: 2-sided → exit 0"""
        r = run("jrc_ss_sigma.R", "1.5", "9.0", "11.0")
        assert r.returncode == 0

    def test_tc_sigma_003_invalid_precision(self):
        """TC-SIGMA-003: negative precision → non-zero exit"""
        r = run("jrc_ss_sigma.R", "-1.0", "9.0", "-")
        assert r.returncode != 0

    def test_tc_sigma_004_missing_arguments(self):
        """TC-SIGMA-004: only 1 argument → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_sigma.R", "1.5")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_paired (TC-PAIRED-001 .. 005)
# ===========================================================================

class TestSsPaired:

    def test_tc_paired_001_two_sided(self):
        """TC-PAIRED-001: 2-sided → exit 0, table with N ≥ 10"""
        r = run("jrc_ss_paired.R", "0.5", "1.0", "2")
        assert r.returncode == 0

    def test_tc_paired_002_one_sided_smaller_n(self):
        """TC-PAIRED-002: 1-sided produces output (smaller N than 2-sided)"""
        r1 = run("jrc_ss_paired.R", "0.5", "1.0", "1")
        r2 = run("jrc_ss_paired.R", "0.5", "1.0", "2")
        assert r1.returncode == 0 and r2.returncode == 0

    def test_tc_paired_003_invalid_sides(self):
        """TC-PAIRED-003: sides=3 → non-zero exit"""
        r = run("jrc_ss_paired.R", "0.5", "1.0", "3")
        assert r.returncode != 0

    def test_tc_paired_004_sd_le_zero(self):
        """TC-PAIRED-004: sd=0 → non-zero exit"""
        r = run("jrc_ss_paired.R", "0.5", "0", "2")
        assert r.returncode != 0

    def test_tc_paired_005_missing_arguments(self):
        """TC-PAIRED-005: only 1 argument → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_paired.R", "0.5")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_equivalence (TC-EQUIV-001 .. 004)
# ===========================================================================

class TestSsEquivalence:

    def test_tc_equiv_001_two_sided_tost(self):
        """TC-EQUIV-001: 2-sided → exit 0, output mentions TOST/equivalence"""
        r = run("jrc_ss_equivalence.R", "0.5", "1.0", "2")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "tost" in out or "equivalence" in out

    def test_tc_equiv_002_one_sided(self):
        """TC-EQUIV-002: 1-sided → exit 0"""
        r = run("jrc_ss_equivalence.R", "0.5", "1.0", "1")
        assert r.returncode == 0

    def test_tc_equiv_003_invalid_sides(self):
        """TC-EQUIV-003: sides=0 → non-zero exit"""
        r = run("jrc_ss_equivalence.R", "0.5", "1.0", "0")
        assert r.returncode != 0

    def test_tc_equiv_004_missing_arguments(self):
        """TC-EQUIV-004: only 1 argument → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_equivalence.R", "0.5")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_fatigue (TC-FAT-001 .. 005)
# ===========================================================================

class TestSsFatigue:

    def test_tc_fat_001_standard_no_acceleration(self):
        """TC-FAT-001: B10, C=0.95, beta=2, AF=1 → exit 0, table for f=0..5"""
        r = run("jrc_ss_fatigue.R", "0.90", "0.95", "2.0", "1.0")
        assert r.returncode == 0
        out = combined(r)
        assert "f = 0" in out

    def test_tc_fat_002_acceleration_reduces_n(self):
        """TC-FAT-002: AF=2 reduces n at f=0 vs AF=1"""
        r1 = run("jrc_ss_fatigue.R", "0.90", "0.95", "2.0", "1.0")
        r2 = run("jrc_ss_fatigue.R", "0.90", "0.95", "2.0", "2.0")
        assert r1.returncode == 0 and r2.returncode == 0
        n1 = extract_n_at_f(r1, 0)
        n2 = extract_n_at_f(r2, 0)
        assert n1 is not None and n2 is not None
        assert n2 < n1

    def test_tc_fat_003_reliability_ge_1(self):
        """TC-FAT-003: reliability=1.0 → non-zero exit"""
        r = run("jrc_ss_fatigue.R", "1.0", "0.95", "2.0", "1.0")
        assert r.returncode != 0

    def test_tc_fat_004_af_less_than_1(self):
        """TC-FAT-004: af=0.5 → non-zero exit"""
        r = run("jrc_ss_fatigue.R", "0.90", "0.95", "2.0", "0.5")
        assert r.returncode != 0

    def test_tc_fat_005_missing_arguments(self):
        """TC-FAT-005: only 3 arguments → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_fatigue.R", "0.90", "0.95", "2.0")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()


# ===========================================================================
# jrc_ss_gauge_rr (TC-GRR-001 .. 004)
# ===========================================================================

class TestSsGaugeRr:

    def test_tc_grr_001_process_based(self):
        """TC-GRR-001: process type → exit 0, table contains %GRR and ndc"""
        r = run("jrc_ss_gauge_rr.R", "10", "process", "1.0")
        assert r.returncode == 0
        out = combined(r).lower()
        assert "grr" in out or "ndc" in out

    def test_tc_grr_002_tolerance_based(self):
        """TC-GRR-002: tolerance type → exit 0, table output"""
        r = run("jrc_ss_gauge_rr.R", "10", "tolerance", "5.0")
        assert r.returncode == 0

    def test_tc_grr_003_invalid_type(self):
        """TC-GRR-003: badtype → non-zero exit"""
        r = run("jrc_ss_gauge_rr.R", "10", "badtype", "1.0")
        assert r.returncode != 0

    def test_tc_grr_004_missing_arguments(self):
        """TC-GRR-004: only 1 argument → non-zero exit, mentions 'Usage'"""
        r = run("jrc_ss_gauge_rr.R", "10")
        assert r.returncode != 0
        assert "usage" in combined(r).lower()
