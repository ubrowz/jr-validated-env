"""
OQ test suite — Cap module: jrc_cap_nonnormal

Maps to validation plan JR-VP-CAP-001 as follows:

  TC-CAP-NN-001  Valid input (non-normal data, both limits) -> exit 0, "Capability" in output
  TC-CAP-NN-002  Ppk label (percentile) present in output
  TC-CAP-NN-003  P0.135 percentile label present in output
  TC-CAP-NN-004  P99.865 percentile label present in output
  TC-CAP-NN-005  Shapiro-Wilk result reported in output
  TC-CAP-NN-006  Non-normal data triggers normality note (p < 0.05)
  TC-CAP-NN-007  PNG saved to ~/Downloads/ with pattern *_jrc_cap_nonnormal.png
  TC-CAP-NN-008  No arguments -> non-zero exit, usage in output
  TC-CAP-NN-009  File not found -> non-zero exit
  TC-CAP-NN-010  n < 5 (cap_small.csv) -> non-zero exit
  TC-CAP-NN-011  Non-numeric column (cap_nonnumeric.csv) -> non-zero exit
  TC-CAP-NN-012  LSL >= USL -> non-zero exit
  TC-CAP-NN-013  Direct Rscript call without RENV_PATHS_ROOT -> non-zero exit
"""

import glob
import os
import subprocess
import time

from conftest import PROJECT_ROOT, MODULE_ROOT, run, combined, data


DOWNLOADS = os.path.expanduser("~/Downloads")


def _recent_png(pattern, t_start):
    return [
        f for f in glob.glob(os.path.join(DOWNLOADS, pattern))
        if os.path.getmtime(f) >= t_start
    ]


class TestCapNonnormal:

    def test_tc_cap_nn_001_happy_path_exits_zero(self):
        """
        TC-CAP-NN-001:
        Valid input (cap_nonnormal.csv, both limits) -> exit 0.
        Output must contain "Capability".
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Capability" in out, \
            f"Expected 'Capability' in output:\n{out}"

    def test_tc_cap_nn_002_ppk_label_present(self):
        """
        TC-CAP-NN-002:
        Output must contain "Ppk" label (percentile method).
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Ppk" in out, \
            f"Expected 'Ppk' in output:\n{out}"

    def test_tc_cap_nn_003_p0135_label_present(self):
        """
        TC-CAP-NN-003:
        Output must contain "P0.135" percentile label.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "P0.135" in out, \
            f"Expected 'P0.135' in output:\n{out}"

    def test_tc_cap_nn_004_p99865_label_present(self):
        """
        TC-CAP-NN-004:
        Output must contain "P99.865" percentile label.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "P99.865" in out, \
            f"Expected 'P99.865' in output:\n{out}"

    def test_tc_cap_nn_005_shapiro_wilk_reported(self):
        """
        TC-CAP-NN-005:
        Shapiro-Wilk result must appear in output.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Shapiro-Wilk" in out, \
            f"Expected 'Shapiro-Wilk' in output:\n{out}"

    def test_tc_cap_nn_006_nonnormal_data_p_below_005(self):
        """
        TC-CAP-NN-006:
        Skewed (exponential-like) data should yield Shapiro-Wilk p < 0.05,
        so the normality advisory should NOT appear (that advisory triggers for p >= 0.05).
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        # The advisory "Data may be approximately normal" appears only for p >= 0.05
        assert "Data may be approximately normal" not in out, \
            f"Skewed data should not trigger normal advisory:\n{out}"

    def test_tc_cap_nn_007_png_created(self):
        """
        TC-CAP-NN-007:
        A PNG matching *_jrc_cap_nonnormal.png must appear in ~/Downloads/.
        """
        t_start = time.time()
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "0.0", "6.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        recent = _recent_png("*_jrc_cap_nonnormal.png", t_start)
        assert recent, "No *_jrc_cap_nonnormal.png found in ~/Downloads/ after run"

    def test_tc_cap_nn_008_no_arguments(self):
        """
        TC-CAP-NN-008:
        Calling with no arguments must exit non-zero and print usage.
        """
        r = run("jrc_cap_nonnormal.R")
        assert r.returncode != 0, "Expected non-zero exit with no arguments"
        out = combined(r)
        assert "Usage" in out or "usage" in out.lower(), \
            f"Expected usage message:\n{out}"

    def test_tc_cap_nn_009_file_not_found(self):
        """
        TC-CAP-NN-009:
        Non-existent file must exit non-zero.
        """
        r = run("jrc_cap_nonnormal.R", "nonexistent_file_xyz.csv", "value", "0.0", "6.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for missing file:\n{combined(r)}"

    def test_tc_cap_nn_010_n_less_than_5(self):
        """
        TC-CAP-NN-010:
        Input with only 3 rows (n < 5) must exit non-zero.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_small.csv"), "value", "0.0", "20.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when n < 5:\n{combined(r)}"

    def test_tc_cap_nn_011_nonnumeric_column(self):
        """
        TC-CAP-NN-011:
        Non-numeric value column must exit non-zero.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnumeric.csv"), "value", "0.0", "1.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for non-numeric column:\n{combined(r)}"

    def test_tc_cap_nn_012_lsl_greater_than_usl(self):
        """
        TC-CAP-NN-012:
        LSL >= USL must exit non-zero.
        """
        r = run("jrc_cap_nonnormal.R", data("cap_nonnormal.csv"), "value", "6.0", "0.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when LSL > USL:\n{combined(r)}"

    def test_tc_cap_nn_013_bypass_protection(self):
        """
        TC-CAP-NN-013:
        Calling jrc_cap_nonnormal.R directly via Rscript without RENV_PATHS_ROOT
        must exit non-zero and mention RENV_PATHS_ROOT in the error output.
        """
        script = os.path.join(MODULE_ROOT, "R", "jrc_cap_nonnormal.R")
        env = {k: v for k, v in os.environ.items() if k != "RENV_PATHS_ROOT"}
        result = subprocess.run(
            ["Rscript", "--vanilla", script,
             data("cap_nonnormal.csv"), "value", "0.0", "6.0"],
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
