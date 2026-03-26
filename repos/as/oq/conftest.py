"""
AS module OQ test suite — shared configuration and helpers.

All AS test modules import helpers from this file.
"""

import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

OQ_DIR       = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT  = os.path.dirname(OQ_DIR)                        # repos/as/
PROJECT_ROOT = os.path.dirname(os.path.dirname(MODULE_ROOT))  # project root
JRRUN        = os.path.join(PROJECT_ROOT, "bin", "jrrun")
DATA_DIR     = os.path.join(OQ_DIR, "data")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASH_PREFIX = ["bash"] if sys.platform == "win32" else []


def run(script, *args, cwd=None):
    """
    Invoke a script via jrrun and return subprocess.CompletedProcess.
    stdout and stderr are both captured as text.
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


def data(name):
    """Return full path to a file in the OQ data directory."""
    return os.path.join(DATA_DIR, name)


def extract_float(result, label):
    """
    Extract the first float that follows *label* in the combined output.
    Returns float, or None if not found.
    """
    m = re.search(rf"{re.escape(label)}\s+([-\d.]+)", combined(result))
    return float(m.group(1)) if m else None
