#!/usr/bin/env python3
"""
Generate all OQ test data files for the JR Validated Environment OQ suite.

Run this script once to create / refresh all files in oq/data/.
Uses only stdlib + numpy (available in the project venv).

Usage:
    ~/.venvs/MyProject/bin/python oq/generate_test_data.py
"""

import os
import csv
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def write_csv(filename, rows, header=("id", "value")):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {filename}  ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# 1. normal_n30_mean10_sd1_seed42.csv
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
vals = rng.normal(10.0, 1.0, 30)
write_csv(
    "normal_n30_mean10_sd1_seed42.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(vals)],
)

# ---------------------------------------------------------------------------
# 2. skewed_n30_lognormal_seed42.csv
# sdlog=1.2 ensures e1071 skewness > 1.0 in R, reliably triggering non-normal path
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
vals_ln = rng.lognormal(mean=2.0, sigma=1.2, size=30)
write_csv(
    "skewed_n30_lognormal_seed42.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(vals_ln)],
)

# ---------------------------------------------------------------------------
# 3. outlier_n30_seed42.csv  — same as normal but row 15 (1-indexed) = 15.0
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
vals_out = rng.normal(10.0, 1.0, 30)
vals_out[14] = 15.0  # inject 5-sigma outlier at position 15 (0-indexed: 14)
write_csv(
    "outlier_n30_seed42.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(vals_out)],
)

# ---------------------------------------------------------------------------
# 4. bland_altman_method1_seed42.csv
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
m1 = rng.normal(10.0, 1.0, 25)
write_csv(
    "bland_altman_method1_seed42.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(m1)],
)

# ---------------------------------------------------------------------------
# 5. bland_altman_method2_seed42.csv  — method1 + N(0, 0.2) noise, seed 99
# ---------------------------------------------------------------------------
# method1 values (same seed=42 → same draws)
rng = np.random.default_rng(42)
m1_base = rng.normal(10.0, 1.0, 25)
# add bias noise with seed 99
rng99 = np.random.default_rng(99)
noise = rng99.normal(0.0, 0.2, 25)
m2 = m1_base + noise
write_csv(
    "bland_altman_method2_seed42.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(m2)],
)

# ---------------------------------------------------------------------------
# 6. method1_short.csv  — first 10 rows of method1 (for TC-BA-003)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
m1_full = rng.normal(10.0, 1.0, 25)
write_csv(
    "method1_short.csv",
    [(i + 1, round(v, 6)) for i, v in enumerate(m1_full[:10])],
)

# ---------------------------------------------------------------------------
# 7. weibull_n20_seed42.csv  — Weibull(shape=2, scale=1000), 15 failures + 5 censored
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
# numpy Weibull: rng.weibull(shape) * scale
times_w = rng.weibull(2.0, 20) * 1000.0
status_w = [1] * 15 + [0] * 5  # first 15 failures, last 5 censored
rows_w = [(i + 1, round(t, 2), s) for i, (t, s) in enumerate(zip(times_w, status_w))]
path_w = os.path.join(DATA_DIR, "weibull_n20_seed42.csv")
with open(path_w, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "cycles", "status"])
    w.writerows(rows_w)
print(f"  wrote weibull_n20_seed42.csv  (20 rows, 3 cols)")

# ---------------------------------------------------------------------------
# 8. all_censored.csv  — all status=0, same times (for TC-WEIB-002)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
times_ac = rng.weibull(2.0, 20) * 1000.0
rows_ac = [(i + 1, round(t, 2), 0) for i, t in enumerate(times_ac)]
path_ac = os.path.join(DATA_DIR, "all_censored.csv")
with open(path_ac, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "cycles", "status"])
    w.writerows(rows_ac)
print("  wrote all_censored.csv  (20 rows, all status=0)")

# ---------------------------------------------------------------------------
# 9. neg_times.csv  — one negative time value (for TC-WEIB-003)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
times_neg = rng.weibull(2.0, 20) * 1000.0
times_neg[0] = -50.0  # inject negative time in first row
rows_neg = [(i + 1, round(t, 2), 1) for i, t in enumerate(times_neg)]
path_neg = os.path.join(DATA_DIR, "neg_times.csv")
with open(path_neg, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "cycles", "status"])
    w.writerows(rows_neg)
print("  wrote neg_times.csv  (20 rows, row 1 negative time)")

# ---------------------------------------------------------------------------
# 10. bad_status.csv  — status values in {0, 1, 2} (for TC-WEIB-004)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
times_bs = rng.weibull(2.0, 20) * 1000.0
status_bs = [1, 0, 2, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1]
rows_bs = [(i + 1, round(t, 2), s) for i, (t, s) in enumerate(zip(times_bs, status_bs))]
path_bs = os.path.join(DATA_DIR, "bad_status.csv")
with open(path_bs, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "cycles", "status"])
    w.writerows(rows_bs)
print("  wrote bad_status.csv  (20 rows, status includes 2)")

# ---------------------------------------------------------------------------
# 11. convert_multicolumn.txt  — tab-delimited, 3 header lines, cols id/ForceN/Temp
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
force_vals = rng.normal(100.0, 5.0, 20)
temp_vals = rng.normal(23.0, 0.5, 20)
path_mc = os.path.join(DATA_DIR, "convert_multicolumn.txt")
with open(path_mc, "w") as f:
    f.write("Test Equipment: JR Force Gauge v1.0\n")
    f.write("Date: 2026-03-15\n")
    f.write("Operator: Joep Rous\n")
    f.write("id\tForceN\tTemp\n")
    for i, (fv, tv) in enumerate(zip(force_vals, temp_vals)):
        f.write(f"{i+1}\t{fv:.4f}\t{tv:.4f}\n")
print("  wrote convert_multicolumn.txt  (3 header + 20 data rows, tab-delimited)")

# ---------------------------------------------------------------------------
# 12. convert_singlecolumn.txt  — 200 numeric values, one per line
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)
single_vals = rng.normal(50.0, 10.0, 200)
path_sc = os.path.join(DATA_DIR, "convert_singlecolumn.txt")
with open(path_sc, "w") as f:
    for v in single_vals:
        f.write(f"{v:.6f}\n")
print("  wrote convert_singlecolumn.txt  (200 lines)")

print("\nAll test data files generated successfully.")
