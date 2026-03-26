"""
OQ test suite — Cap module: jrc_cap_normal

Maps to validation plan JR-VP-CAP-001 as follows:

  TC-CAP-N-001  Valid input (capable data, both limits) -> exit 0, "Capability" in output
  TC-CAP-N-002  Cpk label present in output
  TC-CAP-N-003  Cp label present in output (both limits supplied)
  TC-CAP-N-004  Ppk label present in output
  TC-CAP-N-005  Capable verdict for capable dataset (Cpk >= 1.33)
  TC-CAP-N-006  Marginal/Not-capable verdict for marginal dataset
  TC-CAP-N-007  PNG saved to ~/Downloads/ with pattern *_jrc_cap_normal.png
  TC-CAP-N-008  No arguments -> non-zero exit, usage in output
  TC-CAP-N-009  File not found -> non-zero exit
  TC-CAP-N-010  n < 5 (cap_small.csv) -> non-zero exit
  TC-CAP-N-011  Non-numeric column (cap_nonnumeric.csv) -> non-zero exit
  TC-CAP-N-012  LSL >= USL -> non-zero exit
  TC-CAP-N-013  Direct Rscript call without RENV_PATHS_ROOT -> non-zero exit

Numeric correctness assertions (TC-CAP-N-014 to TC-CAP-N-018):

  These test cases use analytically constructed datasets whose expected output
  values are independently computable from first principles (AIAG/ISO formulas).
  They assert that the script produces the correct numeric result within a
  documented tolerance, providing quantitative correctness evidence for audit.

  Analytical datasets (oq/data/):

    cap_cpk_1p000.csv — 26 pts alternating [9.859, 10.141], LSL=9.25, USL=10.75
      Derivation:
        mean      = 10.000  (symmetric about target)
        MR-bar    = |10.141 - 9.859| = 0.282  (constant MR)
        sigma_w   = MR-bar / d2 = 0.282 / 1.128 = 0.250  (d2=1.128 for n=2 pairs)
        Cp        = (10.75 - 9.25) / (6 * 0.250) = 1.500 / 1.500 = 1.000 (exact)
        Cpk       = min(0.750, 0.750) / (3 * 0.250) = 1.000 (exact, both sides equal)
        sigma_s   = sqrt(26 * 0.141^2 / 25) = 0.14379
        Pp        = 1.500 / (6 * 0.14379) = 1.739
        Ppk       = 1.739  (centred)

    cap_cpk_0p667.csv — 26 pts alternating [10.109, 10.391], LSL=9.25, USL=10.75
      Derivation:
        mean      = 10.250  (shifted +0.250 toward USL)
        sigma_w   = 0.250  (same alternating structure)
        Cp        = 1.000  (exact, specification width unchanged)
        Cpk       = min(0.500, 1.000) / (3 * 0.250) = 0.500/0.750 = 0.667 (exact)

  Tolerances are set to half the least significant digit of the printed output (4 dp).

  TC-CAP-N-014  Cpk for centred dataset = 1.000 ± 0.005
  TC-CAP-N-015  Cp  for centred dataset = 1.000 ± 0.005
  TC-CAP-N-016  Cpk for offset dataset  = 0.667 ± 0.005 (USL side governs)
  TC-CAP-N-017  Cp  for offset dataset  = 1.000 ± 0.005 (Cp is location-independent)
  TC-CAP-N-018  Ppk for centred dataset = 1.739 ± 0.020 (sigma_s vs sigma_w differ)
"""

import glob
import os
import subprocess
import time

from conftest import PROJECT_ROOT, MODULE_ROOT, run, combined, data, extract_float


DOWNLOADS = os.path.expanduser("~/Downloads")


def _recent_png(pattern, t_start):
    return [
        f for f in glob.glob(os.path.join(DOWNLOADS, pattern))
        if os.path.getmtime(f) >= t_start
    ]


class TestCapNormal:

    def test_tc_cap_n_001_happy_path_exits_zero(self):
        """
        TC-CAP-N-001:
        Valid input (cap_normal_capable.csv, both limits) -> exit 0.
        Output must contain "Capability".
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Capability" in out, \
            f"Expected 'Capability' in output:\n{out}"

    def test_tc_cap_n_002_cpk_label_present(self):
        """
        TC-CAP-N-002:
        Output must contain the "Cpk:" label.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Cpk:" in out, \
            f"Expected 'Cpk:' in output:\n{out}"

    def test_tc_cap_n_003_cp_label_present_both_limits(self):
        """
        TC-CAP-N-003:
        With both LSL and USL, output must contain "Cp:" label.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Cp:" in out, \
            f"Expected 'Cp:' in output with both limits:\n{out}"

    def test_tc_cap_n_004_ppk_label_present(self):
        """
        TC-CAP-N-004:
        Output must contain "Ppk:" label.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Ppk:" in out, \
            f"Expected 'Ppk:' in output:\n{out}"

    def test_tc_cap_n_005_capable_verdict_for_capable_data(self):
        """
        TC-CAP-N-005:
        Capable dataset (mean ~10.0, tight spread) with wide spec limits
        must yield CAPABLE or EXCELLENT verdict.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "CAPABLE" in out or "EXCELLENT" in out, \
            f"Expected CAPABLE or EXCELLENT verdict for capable data:\n{out}"

    def test_tc_cap_n_006_marginal_verdict_for_shifted_data(self):
        """
        TC-CAP-N-006:
        Marginal dataset (mean ~11.0, shifted toward USL) with spec 9.0-11.0
        must yield MARGINAL or NOT CAPABLE verdict.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_marginal.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "MARGINAL" in out or "NOT CAPABLE" in out, \
            f"Expected MARGINAL or NOT CAPABLE verdict for shifted data:\n{out}"

    def test_tc_cap_n_007_png_created(self):
        """
        TC-CAP-N-007:
        A PNG matching *_jrc_cap_normal.png must appear in ~/Downloads/.
        """
        t_start = time.time()
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        recent = _recent_png("*_jrc_cap_normal.png", t_start)
        assert recent, "No *_jrc_cap_normal.png found in ~/Downloads/ after run"

    def test_tc_cap_n_008_no_arguments(self):
        """
        TC-CAP-N-008:
        Calling with no arguments must exit non-zero and print usage.
        """
        r = run("jrc_cap_normal.R")
        assert r.returncode != 0, "Expected non-zero exit with no arguments"
        out = combined(r)
        assert "Usage" in out or "usage" in out.lower(), \
            f"Expected usage message:\n{out}"

    def test_tc_cap_n_009_file_not_found(self):
        """
        TC-CAP-N-009:
        Non-existent file must exit non-zero.
        """
        r = run("jrc_cap_normal.R", "nonexistent_file_xyz.csv", "value", "9.0", "11.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for missing file:\n{combined(r)}"

    def test_tc_cap_n_010_n_less_than_5(self):
        """
        TC-CAP-N-010:
        Input with only 3 rows (n < 5) must exit non-zero.
        """
        r = run("jrc_cap_normal.R", data("cap_small.csv"), "value", "9.0", "11.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when n < 5:\n{combined(r)}"

    def test_tc_cap_n_011_nonnumeric_column(self):
        """
        TC-CAP-N-011:
        Non-numeric value column must exit non-zero.
        """
        r = run("jrc_cap_normal.R", data("cap_nonnumeric.csv"), "value", "0.0", "1.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for non-numeric column:\n{combined(r)}"

    def test_tc_cap_n_012_lsl_greater_than_usl(self):
        """
        TC-CAP-N-012:
        LSL >= USL must exit non-zero.
        """
        r = run("jrc_cap_normal.R", data("cap_normal_capable.csv"), "value", "11.0", "9.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when LSL > USL:\n{combined(r)}"

    def test_tc_cap_n_013_bypass_protection(self):
        """
        TC-CAP-N-013:
        Calling jrc_cap_normal.R directly via Rscript without RENV_PATHS_ROOT
        must exit non-zero and mention RENV_PATHS_ROOT in the error output.
        """
        script = os.path.join(MODULE_ROOT, "R", "jrc_cap_normal.R")
        env = {k: v for k, v in os.environ.items() if k != "RENV_PATHS_ROOT"}
        result = subprocess.run(
            ["Rscript", "--vanilla", script,
             data("cap_normal_capable.csv"), "value", "9.0", "11.0"],
            capture_output=True,
            encoding="utf-8",
            env=env,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode != 0, \
            "Expected non-zero exit when called without RENV_PATHS_ROOT"
        out = (result.stdout or "") + (result.stderr or "")
        assert "RENV_PATHS_ROOT" in out, \
            f"Expected 'RENV_PATHS_ROOT' in error output:\n{out}"


class TestCapNormalNumeric:
    """Numeric correctness assertions — see module docstring for derivations."""

    def test_tc_cap_n_014_cpk_centred_exact(self):
        """
        TC-CAP-N-014:
        Cpk for centred analytical dataset (cap_cpk_1p000.csv) = 1.000 ± 0.005.
        """
        r = run("jrc_cap_normal.R", data("cap_cpk_1p000.csv"), "value", "9.25", "10.75")
        assert r.returncode == 0, combined(r)
        cpk = extract_float(r, "Cpk:")
        assert cpk is not None, f"Cpk not found in output:\n{combined(r)}"
        assert abs(cpk - 1.000) < 0.005, \
            f"Expected Cpk = 1.000 ± 0.005, got {cpk:.4f}"

    def test_tc_cap_n_015_cp_centred_exact(self):
        """
        TC-CAP-N-015:
        Cp for centred analytical dataset (cap_cpk_1p000.csv) = 1.000 ± 0.005.
        """
        r = run("jrc_cap_normal.R", data("cap_cpk_1p000.csv"), "value", "9.25", "10.75")
        assert r.returncode == 0, combined(r)
        cp = extract_float(r, "Cp:")
        assert cp is not None, f"Cp not found in output:\n{combined(r)}"
        assert abs(cp - 1.000) < 0.005, \
            f"Expected Cp = 1.000 ± 0.005, got {cp:.4f}"

    def test_tc_cap_n_016_cpk_offset_exact(self):
        """
        TC-CAP-N-016:
        Cpk for offset analytical dataset (cap_cpk_0p667.csv) = 0.667 ± 0.005.
        The USL side governs: (10.75 - 10.25) / (3 * 0.250) = 0.667.
        """
        r = run("jrc_cap_normal.R", data("cap_cpk_0p667.csv"), "value", "9.25", "10.75")
        assert r.returncode == 0, combined(r)
        cpk = extract_float(r, "Cpk:")
        assert cpk is not None, f"Cpk not found in output:\n{combined(r)}"
        assert abs(cpk - 0.667) < 0.005, \
            f"Expected Cpk = 0.667 ± 0.005, got {cpk:.4f}"

    def test_tc_cap_n_017_cp_location_independent(self):
        """
        TC-CAP-N-017:
        Cp for offset dataset (cap_cpk_0p667.csv) = 1.000 ± 0.005.
        Cp measures process potential (spec width vs spread); it is independent
        of where the process is centred.
        """
        r = run("jrc_cap_normal.R", data("cap_cpk_0p667.csv"), "value", "9.25", "10.75")
        assert r.returncode == 0, combined(r)
        cp = extract_float(r, "Cp:")
        assert cp is not None, f"Cp not found in output:\n{combined(r)}"
        assert abs(cp - 1.000) < 0.005, \
            f"Expected Cp = 1.000 ± 0.005, got {cp:.4f}"

    def test_tc_cap_n_018_ppk_centred_exact(self):
        """
        TC-CAP-N-018:
        Ppk for centred dataset (cap_cpk_1p000.csv) = 1.739 ± 0.020.
        sigma_s (sample SD) = 0.14379; Ppk = 0.750 / (3 * 0.14379) = 1.739.
        Wider tolerance reflects that sigma_s differs from sigma_w.
        """
        r = run("jrc_cap_normal.R", data("cap_cpk_1p000.csv"), "value", "9.25", "10.75")
        assert r.returncode == 0, combined(r)
        ppk = extract_float(r, "Ppk:")
        assert ppk is not None, f"Ppk not found in output:\n{combined(r)}"
        assert abs(ppk - 1.739) < 0.020, \
            f"Expected Ppk = 1.739 ± 0.020, got {ppk:.4f}"
