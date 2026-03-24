"""
OQ test suite — Cap module: jrc_cap_sixpack

Maps to validation plan JR-VP-CAP-001 as follows:

  TC-CAP-S-001  Valid input (capable data, both limits) -> exit 0, "Sixpack" in output
  TC-CAP-S-002  Cpk label present in output
  TC-CAP-S-003  Ppk label present in output
  TC-CAP-S-004  Control chart limits (UCL/LCL) present in output
  TC-CAP-S-005  Shapiro-Wilk result reported in output
  TC-CAP-S-006  SPC verdict present in output
  TC-CAP-S-007  Capability verdict present in output
  TC-CAP-S-008  PNG saved to ~/Downloads/ with pattern *_jrc_cap_sixpack.png
  TC-CAP-S-009  No arguments -> non-zero exit, usage in output
  TC-CAP-S-010  File not found -> non-zero exit
  TC-CAP-S-011  n < 5 (cap_small.csv) -> non-zero exit
  TC-CAP-S-012  Non-numeric column (cap_nonnumeric.csv) -> non-zero exit
  TC-CAP-S-013  LSL >= USL -> non-zero exit
  TC-CAP-S-014  Direct Rscript call without RENV_PATHS_ROOT -> non-zero exit
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


class TestCapSixpack:

    def test_tc_cap_s_001_happy_path_exits_zero(self):
        """
        TC-CAP-S-001:
        Valid input (cap_normal_capable.csv, both limits) -> exit 0.
        Output must contain "Sixpack".
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Sixpack" in out, \
            f"Expected 'Sixpack' in output:\n{out}"

    def test_tc_cap_s_002_cpk_label_present(self):
        """
        TC-CAP-S-002:
        Output must contain "Cpk:" label.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Cpk:" in out, \
            f"Expected 'Cpk:' in output:\n{out}"

    def test_tc_cap_s_003_ppk_label_present(self):
        """
        TC-CAP-S-003:
        Output must contain "Ppk:" label.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Ppk:" in out, \
            f"Expected 'Ppk:' in output:\n{out}"

    def test_tc_cap_s_004_control_limits_present(self):
        """
        TC-CAP-S-004:
        Output must contain UCL and LCL for the I-MR chart.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "UCL" in out and "LCL" in out, \
            f"Expected UCL and LCL in output:\n{out}"

    def test_tc_cap_s_005_shapiro_wilk_reported(self):
        """
        TC-CAP-S-005:
        Shapiro-Wilk result must appear in output.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Shapiro-Wilk" in out, \
            f"Expected 'Shapiro-Wilk' in output:\n{out}"

    def test_tc_cap_s_006_spc_verdict_present(self):
        """
        TC-CAP-S-006:
        Output must contain an SPC verdict line.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "SPC:" in out, \
            f"Expected 'SPC:' in output:\n{out}"

    def test_tc_cap_s_007_capability_verdict_present(self):
        """
        TC-CAP-S-007:
        Output must contain "Cap:" verdict line with a known verdict word.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        out = combined(r)
        assert "Cap:" in out, \
            f"Expected 'Cap:' verdict in output:\n{out}"
        assert any(v in out for v in ["CAPABLE", "EXCELLENT", "MARGINAL", "NOT CAPABLE"]), \
            f"Expected a capability verdict word in output:\n{out}"

    def test_tc_cap_s_008_png_created(self):
        """
        TC-CAP-S-008:
        A PNG matching *_jrc_cap_sixpack.png must appear in ~/Downloads/.
        """
        t_start = time.time()
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "9.0", "11.0")
        assert r.returncode == 0, f"Expected exit 0:\n{combined(r)}"
        recent = _recent_png("*_jrc_cap_sixpack.png", t_start)
        assert recent, "No *_jrc_cap_sixpack.png found in ~/Downloads/ after run"

    def test_tc_cap_s_009_no_arguments(self):
        """
        TC-CAP-S-009:
        Calling with no arguments must exit non-zero and print usage.
        """
        r = run("jrc_cap_sixpack.R")
        assert r.returncode != 0, "Expected non-zero exit with no arguments"
        out = combined(r)
        assert "Usage" in out or "usage" in out.lower(), \
            f"Expected usage message:\n{out}"

    def test_tc_cap_s_010_file_not_found(self):
        """
        TC-CAP-S-010:
        Non-existent file must exit non-zero.
        """
        r = run("jrc_cap_sixpack.R", "nonexistent_file_xyz.csv", "value", "9.0", "11.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for missing file:\n{combined(r)}"

    def test_tc_cap_s_011_n_less_than_5(self):
        """
        TC-CAP-S-011:
        Input with only 3 rows (n < 5) must exit non-zero.
        """
        r = run("jrc_cap_sixpack.R", data("cap_small.csv"), "value", "9.0", "11.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when n < 5:\n{combined(r)}"

    def test_tc_cap_s_012_nonnumeric_column(self):
        """
        TC-CAP-S-012:
        Non-numeric value column must exit non-zero.
        """
        r = run("jrc_cap_sixpack.R", data("cap_nonnumeric.csv"), "value", "0.0", "1.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit for non-numeric column:\n{combined(r)}"

    def test_tc_cap_s_013_lsl_greater_than_usl(self):
        """
        TC-CAP-S-013:
        LSL >= USL must exit non-zero.
        """
        r = run("jrc_cap_sixpack.R", data("cap_normal_capable.csv"), "value", "11.0", "9.0")
        assert r.returncode != 0, \
            f"Expected non-zero exit when LSL > USL:\n{combined(r)}"

    def test_tc_cap_s_014_bypass_protection(self):
        """
        TC-CAP-S-014:
        Calling jrc_cap_sixpack.R directly via Rscript without RENV_PATHS_ROOT
        must exit non-zero and mention RENV_PATHS_ROOT in the error output.
        """
        script = os.path.join(MODULE_ROOT, "R", "jrc_cap_sixpack.R")
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
