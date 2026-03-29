"""
OQ test suite — shared configuration and helpers.

All test modules import helpers from this file.
"""

import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

OQ_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(OQ_DIR)
JRRUN = os.path.join(PROJECT_ROOT, "bin", "jrrun")
DATA_DIR = os.path.join(OQ_DIR, "data")

# ---------------------------------------------------------------------------
# Platform constants
# ---------------------------------------------------------------------------

# On Windows, shell scripts must be invoked via bash explicitly.
BASH_PREFIX  = ["bash"] if sys.platform == "win32" else []
# Python executable name differs between platforms.
PYTHON_BIN   = "python" if sys.platform == "win32" else "python3"
# venv executables live in Scripts/ on Windows, bin/ on Unix.
VENV_BIN_DIR = "Scripts" if sys.platform == "win32" else "bin"
# PATH separator.
PATH_SEP     = ";" if sys.platform == "win32" else ":"
# Rscript binary — on Windows Python subprocess does not inherit Git Bash PATH,
# so locate Rscript.exe directly under Program Files.
if sys.platform == "win32":
    import glob as _glob
    _candidates = sorted(_glob.glob(r"C:\Program Files\R\R-*\bin\Rscript.exe"))
    RSCRIPT_BIN = _candidates[-1] if _candidates else "Rscript"
else:
    RSCRIPT_BIN = "Rscript"


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

def run(script, *args, cwd=None):
    """
    Invoke a script via jrrun and return subprocess.CompletedProcess.

    stdout and stderr are both captured as text. The combined output
    (stdout + stderr) should be used for content checks because R
    scripts write to stderr via message() and Python scripts write
    to stdout via print().
    """
    cmd = BASH_PREFIX + [JRRUN, script] + [str(a) for a in args]
    return subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        cwd=cwd or DATA_DIR,
    )


def combined(result):
    """Return stdout + stderr as a single string for pattern matching."""
    return (result.stdout or "") + (result.stderr or "")


def extract_n_at_f(result, f=0):
    """
    Extract the sample size n from the f=<f> row of a sample size table.
    Matches patterns like:  f = 0   n =  299
    Returns int or None.
    """
    pattern = rf"f\s*=\s*{f}\D+?n\s*=\s*(\d+)"
    m = re.search(pattern, combined(result))
    return int(m.group(1)) if m else None


def extract_float(result, label):
    """
    Extract the first float that follows *label* in the combined output.
    *label* should include any trailing colon, e.g. ``"proportion achieved:"``.
    Returns float, or None if not found.
    """
    m = re.search(rf"{re.escape(label)}\s+([-\d.]+)", combined(result))
    return float(m.group(1)) if m else None


def extract_table_n(result, power, col):
    """
    Extract n from a 3-column (C=0.90, 0.95, 0.99) table row formatted as:
        p = {power:.2f}   N1      N2      N3
    col: 1 = C=0.90, 2 = C=0.95, 3 = C=0.99
    Returns int or None.
    """
    pat = rf"p\s*=\s*{power:.2f}\s+(\d+)\s+(\d+)\s+(\d+)"
    m = re.search(pat, combined(result))
    return int(m.group(col)) if m else None
