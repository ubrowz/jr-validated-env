#!/usr/bin/env python3
"""
jrc_curve_properties — Extract engineering properties from an XY measurement curve.

Config-file driven. Single CLI argument: path to .cfg file.
Usage: jrrun jrc_curve_properties.py path/to/config.cfg
       jrrun jrc_curve_properties.py --help

Author: Joep Rous
Version: 1.0
"""

import sys
import os
import configparser
import csv as csvmod

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def die(msg):
    print(msg)
    sys.exit(1)


_warnings = []


def warn(msg):
    print(msg)
    _warnings.append(msg)


def resolve_path(cfg_dir, p):
    if os.path.isabs(p):
        return p
    return os.path.normpath(os.path.join(cfg_dir, p))


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def parse_config(cfg_path):
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#",))
    cfg.optionxform = str          # preserve key case
    cfg.read(cfg_path, encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(cfg, cfg_dir):
    if not cfg.has_section("data"):
        die("❌ Config is missing required [data] section.")

    sec = dict(cfg["data"])
    for key in ("file", "x_col", "y_col"):
        if key not in sec:
            die(f"❌ [data] section is missing required key: {key}")

    csv_path = resolve_path(cfg_dir, sec["file"])
    if not os.path.isfile(csv_path):
        die(f"❌ Data file not found: {csv_path}")

    x_col = sec["x_col"]
    y_col = sec["y_col"]

    x_vals, y_vals = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csvmod.DictReader(f)
        headers = reader.fieldnames or []
        if x_col not in headers:
            die(f"❌ X column '{x_col}' not found. Available: {list(headers)}")
        if y_col not in headers:
            die(f"❌ Y column '{y_col}' not found. Available: {list(headers)}")
        for i, row in enumerate(reader, start=2):
            try:
                x_vals.append(float(row[x_col]))
                y_vals.append(float(row[y_col]))
            except (ValueError, TypeError):
                warn(f"⚠️  Row {i}: non-numeric in '{x_col}' or '{y_col}' — skipped")

    if len(x_vals) < 5:
        die(f"❌ Too few valid data rows ({len(x_vals)}). Minimum is 5.")

    return np.array(x_vals, dtype=float), np.array(y_vals, dtype=float)


# ---------------------------------------------------------------------------
# Phase extraction
# ---------------------------------------------------------------------------

def extract_phases(cfg, x, y):
    """
    Return ordered dict {name: (x_arr, y_arr, (i_start, i_end))}.
    Section [phase.NAME] → phase name is NAME.
    x_start matched as closest point in full series.
    x_end matched as closest point at or after i_start.
    """
    phases = {}

    for section in cfg.sections():
        if not section.startswith("phase."):
            continue
        name = section[len("phase."):]

        sec = dict(cfg[section])
        for key in ("x_start", "x_end"):
            if key not in sec:
                die(f"❌ [{section}] is missing required key: {key}")

        try:
            x_start = float(sec["x_start"])
            x_end   = float(sec["x_end"])
        except ValueError:
            die(f"❌ [{section}]: x_start and x_end must be numeric.")

        # Closest match for x_start in full series
        i_start = int(np.argmin(np.abs(x - x_start)))

        # Closest match for x_end at or after i_start
        tail = x[i_start:]
        if len(tail) == 0:
            die(f"❌ [{section}]: x_start ({x_start}) matches last data point — no room for x_end.")
        i_end = i_start + int(np.argmin(np.abs(tail - x_end)))

        if i_end <= i_start:
            die(f"❌ [{section}]: x_end ({x_end}) resolves to same or earlier row as x_start. "
                f"Check that x_end appears after x_start in the time series.")

        x_ph = x[i_start:i_end + 1]
        y_ph = y[i_start:i_end + 1]

        phases[name] = (x_ph, y_ph, (i_start, i_end))

        print(f"   Phase '{name}':  rows {i_start + 1}–{i_end + 1}  "
              f"(x: {x_ph[0]:.4g} → {x_ph[-1]:.4g},  {len(x_ph)} points)")

    return phases


# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------

def smooth_array(cfg, y_arr):
    """Return smoothed copy of y_arr. Raw data unchanged for max/min/AUC."""
    if not cfg.has_section("smoothing"):
        return y_arr.copy()

    method = cfg.get("smoothing", "method", fallback="none").lower()
    if method == "none":
        return y_arr.copy()

    n = len(y_arr)
    span_val = float(cfg.get("smoothing", "span", fallback="0.15"))

    if method == "savgol":
        window = max(5, int(span_val * n))
        if window % 2 == 0:
            window += 1
        window = min(window, n if n % 2 == 1 else n - 1)
        polyorder = min(3, window - 1)
        return savgol_filter(y_arr, window_length=window, polyorder=polyorder)

    if method == "moving_avg":
        window = max(3, int(span_val * n))
        if window % 2 == 0:
            window += 1
        kernel = np.ones(window) / window
        pad = window // 2
        padded = np.pad(y_arr, pad, mode="edge")
        smoothed = np.convolve(padded, kernel, mode="valid")
        return smoothed[:n]

    warn(f"⚠️  Unknown smoothing method '{method}'. No smoothing applied.")
    return y_arr.copy()


# ---------------------------------------------------------------------------
# Interpolation helpers
# ---------------------------------------------------------------------------

def interp_y_at_x(x_ph, y_ph, x_query):
    """Linear interpolation; returns (value, error_str)."""
    x_lo, x_hi = min(x_ph[0], x_ph[-1]), max(x_ph[0], x_ph[-1])
    if x_query < x_lo or x_query > x_hi:
        return None, f"x={x_query} outside range [{x_lo:.4g}, {x_hi:.4g}]"
    # np.interp requires ascending x; sort if needed
    if x_ph[-1] < x_ph[0]:
        order = x_ph.argsort()
        return float(np.interp(x_query, x_ph[order], y_ph[order])), None
    return float(np.interp(x_query, x_ph, y_ph)), None


def x_at_y_crossings(x_ph, y_ph, y_query, mode="first"):
    """Return list of x crossings where y == y_query (linear interp)."""
    crossings = []
    for i in range(len(y_ph) - 1):
        y0, y1 = y_ph[i], y_ph[i + 1]
        if y0 == y1:
            continue
        if (y0 - y_query) * (y1 - y_query) <= 0:
            t = (y_query - y0) / (y1 - y0)
            crossings.append(x_ph[i] + t * (x_ph[i + 1] - x_ph[i]))
    if not crossings:
        return []
    if mode == "first":
        return [crossings[0]]
    if mode == "last":
        return [crossings[-1]]
    return crossings


def slope_at_x(x_ph, y_smooth_ph, x_query):
    """Central (or edge) finite difference at x_query on smoothed data."""
    i = int(np.argmin(np.abs(x_ph - x_query)))
    n = len(x_ph)
    if n < 2:
        return None
    if i == 0:
        return (y_smooth_ph[1] - y_smooth_ph[0]) / (x_ph[1] - x_ph[0])
    if i == n - 1:
        return (y_smooth_ph[-1] - y_smooth_ph[-2]) / (x_ph[-1] - x_ph[-2])
    dx = x_ph[i + 1] - x_ph[i - 1]
    if dx == 0:
        return None
    return (y_smooth_ph[i + 1] - y_smooth_ph[i - 1]) / dx


# ---------------------------------------------------------------------------
# Computation — global
# ---------------------------------------------------------------------------

def compute_global(cfg, x, y, phases):
    if not cfg.has_section("global"):
        return []

    sec = dict(cfg["global"])
    results = []

    def _resolve(ph_key, default_label, scoped_label_fmt):
        ph = sec.get(ph_key, "").strip()
        if ph and ph in phases:
            return phases[ph][0], phases[ph][1], scoped_label_fmt.format(ph)
        if ph and ph not in phases:
            warn(f"⚠️  Phase '{ph}' not defined — using full dataset.")
        return x, y, default_label

    if sec.get("max_y", "").lower() == "yes":
        xp, yp, lbl = _resolve("max_y_phase", "max Y", "max Y [{}]")
        i = int(np.argmax(yp))
        results.append({"section": "Global", "label": lbl,
                        "value": f"{yp[i]:.6g}  at x = {xp[i]:.6g}"})

    if sec.get("min_y", "").lower() == "yes":
        xp, yp, lbl = _resolve("min_y_phase", "min Y", "min Y [{}]")
        i = int(np.argmin(yp))
        results.append({"section": "Global", "label": lbl,
                        "value": f"{yp[i]:.6g}  at x = {xp[i]:.6g}"})

    if sec.get("auc", "").lower() == "yes":
        xp, yp, lbl = _resolve("auc_phase", "AUC", "AUC [{}]")
        val = float(np.trapezoid(yp, xp))
        results.append({"section": "Global", "label": lbl,
                        "value": f"{val:.6g}",
                        "note": "trapezoid rule, raw data"})

    if sec.get("hysteresis", "").lower() == "yes":
        lp = sec.get("hysteresis_loading_phase", "loading").strip()
        up = sec.get("hysteresis_unloading_phase", "unloading").strip()
        if lp not in phases or up not in phases:
            warn(f"⚠️  Hysteresis requires phases '{lp}' and '{up}' — skipped.")
        else:
            xl, yl, _ = phases[lp]
            xu, yu, _ = phases[up]
            x_lo = max(xl.min(), xu.min())
            x_hi = min(xl.max(), xu.max())
            if x_hi <= x_lo:
                warn("⚠️  Hysteresis: phases have no overlapping X range — skipped.")
            else:
                xg = np.linspace(x_lo, x_hi, 500)
                sl = np.argsort(xl); su = np.argsort(xu)
                yl_i = np.interp(xg, xl[sl], yl[sl])
                yu_i = np.interp(xg, xu[su], yu[su])
                hyst = float(np.trapezoid(np.abs(yl_i - yu_i), xg))
                results.append({"section": "Global", "label": "Hysteresis",
                                "value": f"{hyst:.6g}",
                                "note": f"area between '{lp}' and '{up}', linear interp, raw data"})

    return results


# ---------------------------------------------------------------------------
# Computation — slope
# ---------------------------------------------------------------------------

def compute_slope(cfg, x, y, phases):
    if not cfg.has_section("slope"):
        return []

    sec = dict(cfg["slope"])
    results = []

    def _ph(ph_key):
        ph = sec.get(ph_key, "").strip()
        if ph and ph in phases:
            return phases[ph][0], phases[ph][1], ph
        if ph and ph not in phases:
            warn(f"⚠️  Phase '{ph}' not defined — using full dataset.")
        return x, y, ""

    # overall
    if sec.get("overall", "").lower() == "yes":
        xp, yp, ph = _ph("overall_phase")
        lbl = f"slope overall [{ph}]" if ph else "slope overall"
        coeffs = np.polyfit(xp, yp, 1)
        yp_fit = np.polyval(coeffs, xp)
        ss_res = np.sum((yp - yp_fit) ** 2)
        ss_tot = np.sum((yp - yp.mean()) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
        results.append({"section": "Slope", "label": lbl,
                        "value": f"{coeffs[0]:.6g}",
                        "note": f"R\u00b2 = {r2:.4f}, linear regression, raw data"})

    # secant
    if sec.get("secant", "").lower() == "yes":
        xp, yp, ph = _ph("secant_phase")
        try:
            sx1 = float(sec["secant_x1"])
            sx2 = float(sec["secant_x2"])
        except (KeyError, ValueError):
            warn("⚠️  [slope] secant: secant_x1 and secant_x2 required — skipped.")
        else:
            lbl = f"slope secant x={sx1}\u2013{sx2} [{ph}]" if ph else f"slope secant x={sx1}\u2013{sx2}"
            sy1, e1 = interp_y_at_x(xp, yp, sx1)
            sy2, e2 = interp_y_at_x(xp, yp, sx2)
            if e1 or e2:
                warn(f"⚠️  Secant slope: {e1 or e2} — skipped.")
            elif sx1 == sx2:
                warn("⚠️  Secant slope: secant_x1 == secant_x2 — skipped.")
            else:
                val = (sy2 - sy1) / (sx2 - sx1)
                results.append({"section": "Slope", "label": lbl,
                                "value": f"{val:.6g}",
                                "note": f"y({sx1})={sy1:.4g}, y({sx2})={sy2:.4g}"})

    # instantaneous slope at_x_N
    for key in sorted(sec):
        if not key.startswith("at_x_"):
            continue
        suffix = key[len("at_x_"):]
        if not suffix.isdigit():
            continue
        xp, yp, ph = _ph(f"at_x_{suffix}_phase")
        try:
            x_query = float(sec[key])
        except ValueError:
            warn(f"⚠️  [slope] at_x_{suffix} = '{sec[key]}' not numeric — skipped.")
            continue
        lbl = f"slope at x={x_query} [{ph}]" if ph else f"slope at x={x_query}"
        ys = smooth_array(cfg, yp)
        s = slope_at_x(xp, ys, x_query)
        if s is None:
            warn(f"⚠️  slope at x={x_query}: too few points — skipped.")
        else:
            results.append({"section": "Slope", "label": lbl,
                            "value": f"{s:.6g}",
                            "note": "numerical derivative, smoothed data"})

    return results


# ---------------------------------------------------------------------------
# Computation — query
# ---------------------------------------------------------------------------

def compute_query(cfg, x, y, phases):
    if not cfg.has_section("query"):
        return []

    sec = dict(cfg["query"])
    results = []

    def _ph(ph_key):
        ph = sec.get(ph_key, "").strip()
        if ph and ph in phases:
            return phases[ph][0], phases[ph][1], ph
        if ph and ph not in phases:
            warn(f"⚠️  Phase '{ph}' not defined — using full dataset.")
        return x, y, ""

    for key in sorted(sec):
        # y_at_x_N
        if key.startswith("y_at_x_"):
            suffix = key[len("y_at_x_"):]
            if not suffix.isdigit():
                continue
            xp, yp, ph = _ph(f"y_at_x_{suffix}_phase")
            try:
                xq = float(sec[key])
            except ValueError:
                warn(f"⚠️  [query] y_at_x_{suffix} not numeric — skipped.")
                continue
            lbl = f"Y at x={xq} [{ph}]" if ph else f"Y at x={xq}"
            val, err = interp_y_at_x(xp, yp, xq)
            if err:
                warn(f"⚠️  y_at_x_{suffix}: {err} — skipped.")
            else:
                results.append({"section": "Query", "label": lbl,
                                "value": f"{val:.6g}", "note": "linear interpolation"})

        # x_at_y_N
        elif key.startswith("x_at_y_"):
            suffix = key[len("x_at_y_"):]
            if not suffix.isdigit():
                continue
            mode = sec.get(f"x_at_y_{suffix}_mode", "first").strip().lower()
            xp, yp, ph = _ph(f"x_at_y_{suffix}_phase")
            try:
                yq = float(sec[key])
            except ValueError:
                warn(f"⚠️  [query] x_at_y_{suffix} not numeric — skipped.")
                continue
            lbl = f"X at y={yq} [{ph}]" if ph else f"X at y={yq}"
            crossings = x_at_y_crossings(xp, yp, yq, mode)
            if not crossings:
                warn(f"⚠️  x_at_y_{suffix}: no crossing at y={yq} — skipped.")
            else:
                for ci, xc in enumerate(crossings):
                    row_lbl = f"{lbl} [{ci + 1}]" if len(crossings) > 1 else lbl
                    results.append({"section": "Query", "label": row_lbl,
                                    "value": f"{xc:.6g}",
                                    "note": f"mode={mode}, linear interpolation"})

    return results


# ---------------------------------------------------------------------------
# Computation — transitions
# ---------------------------------------------------------------------------

def compute_transitions(cfg, x, y, phases):
    if not cfg.has_section("transitions"):
        return []

    sec = dict(cfg["transitions"])
    results = []

    def _ph(ph_key):
        ph = sec.get(ph_key, "").strip()
        if ph and ph in phases:
            return phases[ph][0], phases[ph][1], ph
        if ph and ph not in phases:
            warn(f"⚠️  Phase '{ph}' not defined — using full dataset.")
        return x, y, ""

    # inflections
    if sec.get("inflections", "").lower() == "yes":
        xp, yp, ph = _ph("inflections_phase")
        lbl_pfx = f"inflection [{ph}]" if ph else "inflection"
        ys = smooth_array(cfg, yp)
        dy  = np.gradient(ys, xp)
        d2y = np.gradient(dy, xp)
        # Minimum spacing between reported inflections: default 5% of X range
        x_span = float(xp.max() - xp.min())
        try:
            min_gap = float(sec.get("inflections_min_gap",
                                    str(round(0.05 * x_span, 6))))
        except ValueError:
            min_gap = 0.05 * x_span
        raw = []
        for i in range(len(d2y) - 1):
            if d2y[i] * d2y[i + 1] < 0 and (d2y[i + 1] - d2y[i]) != 0:
                t = -d2y[i] / (d2y[i + 1] - d2y[i])
                xi = xp[i] + t * (xp[i + 1] - xp[i])
                yi, _ = interp_y_at_x(xp, yp, xi)
                raw.append((xi, yi))
        # Enforce minimum gap: keep only points separated by >= min_gap
        found = []
        for xi, yi in raw:
            if not found or (xi - found[-1][0]) >= min_gap:
                found.append((xi, yi))
        if not found:
            results.append({"section": "Transitions", "label": lbl_pfx,
                            "value": "none found",
                            "note": "second derivative sign change, smoothed data"})
        else:
            note_gap = f"min gap = {min_gap:.4g}" if min_gap > 0 else ""
            note = "second derivative sign change, smoothed data"
            if note_gap:
                note += f"; {note_gap}"
            for k, (xi, yi) in enumerate(found):
                results.append({"section": "Transitions",
                                "label": f"{lbl_pfx} {k + 1}",
                                "value": f"x = {xi:.6g},  y = {yi:.6g}",
                                "note": note})

    # yield_slope
    if "yield_slope" in sec:
        xp, yp, ph = _ph("yield_phase")
        lbl = f"yield point [{ph}]" if ph else "yield point"
        try:
            frac = float(sec["yield_slope"])
        except ValueError:
            warn("⚠️  [transitions] yield_slope must be numeric — skipped.")
        else:
            ys = smooth_array(cfg, yp)
            dy = np.gradient(ys, xp)
            max_slope = np.max(np.abs(dy))
            if max_slope == 0:
                warn("⚠️  yield_slope: max slope is zero — skipped.")
            else:
                threshold = frac * max_slope
                i_max = int(np.argmax(np.abs(dy)))
                yield_x = yield_y = None
                for i in range(i_max, len(dy)):
                    if np.abs(dy[i]) <= threshold:
                        yield_x = float(xp[i])
                        yield_y, _ = interp_y_at_x(xp, yp, yield_x)
                        break
                if yield_x is None:
                    results.append({"section": "Transitions", "label": lbl,
                                    "value": "not reached",
                                    "note": f"slope never drops to {frac:.3g} \u00d7 max slope"})
                else:
                    results.append({"section": "Transitions", "label": lbl,
                                    "value": f"x = {yield_x:.6g},  y = {yield_y:.6g}",
                                    "note": f"slope threshold = {frac:.3g} \u00d7 max ({max_slope:.4g}), smoothed"})

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _label_x(cfg):
    if cfg.has_section("output"):
        return cfg.get("output", "label_x", fallback=cfg.get("data", "x_col", fallback="x"))
    return cfg.get("data", "x_col", fallback="x")


def _label_y(cfg):
    if cfg.has_section("output"):
        return cfg.get("output", "label_y", fallback=cfg.get("data", "y_col", fallback="y"))
    return cfg.get("data", "y_col", fallback="y")


def _title(cfg):
    if cfg.has_section("output"):
        return cfg.get("output", "title", fallback="Curve Properties Analysis")
    return "Curve Properties Analysis"


def print_results(all_results, cfg, n_rows):
    title = _title(cfg)
    sep = "=" * max(46, len(title) + 2)
    print()
    print(f"✅ {title}")
    print(f"   version: 1.0, author: Joep Rous")
    print(f"   {sep}")
    print(f"   Rows loaded  : {n_rows}")
    print(f"   X column     : {cfg.get('data', 'x_col', fallback='?')}")
    print(f"   Y column     : {cfg.get('data', 'y_col', fallback='?')}")
    print()

    current_section = None
    for r in all_results:
        sec = r.get("section", "")
        if sec != current_section:
            if current_section is not None:
                print()
            print(f"   {sec}")
            print(f"   {'-' * 46}")
            current_section = sec
        label = r["label"]
        value = r["value"]
        note  = r.get("note", "")
        pad   = max(1, 38 - len(label))
        print(f"   {label}{' ' * pad}: {value}")
        if note:
            print(f"   {'':38}  ({note})")
    print()


def write_results_file(all_results, cfg, cfg_dir, cfg_path):
    if cfg.has_section("output"):
        rf = cfg.get("output", "results_file", fallback=None)
        results_path = resolve_path(cfg_dir, rf) if rf else None
    else:
        results_path = None

    if results_path is None:
        stem = os.path.splitext(os.path.basename(cfg_path))[0]
        results_path = os.path.join(cfg_dir, f"{stem}_results.txt")

    os.makedirs(os.path.dirname(results_path) if os.path.dirname(results_path) else ".", exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        f.write("# jrc_curve_properties results\n")
        f.write(f"# config  : {cfg_path}\n")
        f.write(f"# data    : {cfg.get('data', 'file', fallback='?')}\n")
        f.write("#\n")
        header = f"{'section':<16}{'label':<42}{'value':<28}note\n"
        f.write(header)
        f.write("-" * 100 + "\n")
        for r in all_results:
            line = (f"{r.get('section', ''):<16}"
                    f"{r['label']:<42}"
                    f"{r['value']:<28}"
                    f"{r.get('note', '')}\n")
            f.write(line)

    print(f"   Results file : {results_path}")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

_PHASE_COLORS = ["#4878CF", "#D65F5F", "#6ACC65", "#B47CC7", "#C4AD66", "#77BEDB"]


def generate_plot(cfg, cfg_dir, cfg_path, x, y, phases):
    if cfg.has_section("output"):
        pf = cfg.get("output", "plot_file", fallback=None)
        plot_path = resolve_path(cfg_dir, pf) if pf else None
    else:
        plot_path = None

    if plot_path is None:
        stem = os.path.splitext(os.path.basename(cfg_path))[0]
        plot_path = os.path.join(cfg_dir, f"{stem}_plot.pdf")

    os.makedirs(os.path.dirname(plot_path) if os.path.dirname(plot_path) else ".", exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Raw data
    ax.plot(x, y, color="#888888", linewidth=0.8, alpha=0.7, label="raw data", zorder=1)

    # Smoothed overlay (if requested)
    apply_smooth = False
    if cfg.has_section("smoothing"):
        apply_smooth = cfg.get("smoothing", "apply_to_plot", fallback="no").lower() == "yes"
    if apply_smooth:
        ys = smooth_array(cfg, y)
        ax.plot(x, ys, color="#222222", linewidth=1.5, label="smoothed", zorder=2)

    # Phase shading + boundaries
    for k, (ph_name, (x_ph, y_ph, _)) in enumerate(phases.items()):
        color = _PHASE_COLORS[k % len(_PHASE_COLORS)]
        x_lo, x_hi = x_ph.min(), x_ph.max()
        ax.axvspan(x_lo, x_hi, alpha=0.07, color=color)
        ax.axvline(x=x_ph[0],  color=color, linewidth=0.9, linestyle="--", alpha=0.7,
                   label=f"phase: {ph_name}")
        ax.axvline(x=x_ph[-1], color=color, linewidth=0.9, linestyle="--", alpha=0.5)

    ax.set_xlabel(_label_x(cfg))
    ax.set_ylabel(_label_y(cfg))
    ax.set_title(_title(cfg))
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(plot_path, format="pdf", dpi=150)
    plt.close()

    print(f"   Plot file    : {plot_path}")


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

def print_help():
    print("""
jrc_curve_properties — XY Curve Properties Analysis
Version 1.0 | Author: Joep Rous

USAGE
    jrrun jrc_curve_properties.py path/to/config.cfg
    jrrun jrc_curve_properties.py --help

DESCRIPTION
    Extracts engineering properties from an XY time-ordered measurement
    curve (e.g. force vs. displacement, torque vs. angle). Input is a
    two-column CSV and a .cfg config file. Properties include peak values,
    area under curve, slopes, query values, inflection points, and
    hysteresis.

    All paths in the config are relative to the config file's own directory.
    Absent config key = skip that feature. No need to write 'no'.

    Smoothing (savgol or moving_avg) is applied ONLY to derivative-based
    calculations (slope at X, inflections, yield point). max/min/AUC/
    hysteresis are always computed on raw data.

CONFIG SECTIONS
    [data]         required — CSV path, x_col, y_col
    [output]       optional — label_x, label_y, title, plot (yes/no),
                              plot_file, results_file
    [smoothing]    optional — method (savgol|moving_avg|none), span (0–1),
                              apply_to_plot (yes/no)
    [phase.NAME]   optional, repeatable — x_start, x_end
    [global]       optional — max_y, min_y, auc, hysteresis
    [slope]        optional — overall, secant, at_x_1, at_x_2, ...
    [query]        optional — y_at_x_1, x_at_y_1, x_at_y_1_mode, ...
    [transitions]  optional — inflections, yield_slope

EXAMPLE CONFIG
    [data]
    file   = data/force_compression.csv
    x_col  = displacement_mm
    y_col  = force_N

    [phase.loading]
    x_start = 5
    x_end   = 95

    [global]
    max_y      = yes
    auc        = yes
    auc_phase  = loading

    [slope]
    secant        = yes
    secant_phase  = loading
    secant_x1     = 10.0
    secant_x2     = 40.0

    [query]
    y_at_x_1        = 50.0
    y_at_x_1_phase  = loading
    x_at_y_1        = 80.0
    x_at_y_1_phase  = loading
    x_at_y_1_mode   = first
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
    if len(sys.argv) > 2:
        die("❌ Too many arguments. Usage: jrrun jrc_curve_properties.py path/to/config.cfg")

    cfg_path = sys.argv[1]
    if not os.path.isfile(cfg_path):
        die(f"❌ Config file not found: {cfg_path}")

    cfg_dir = os.path.dirname(os.path.abspath(cfg_path))

    print()

    cfg = parse_config(cfg_path)
    x, y = load_data(cfg, cfg_dir)

    print(f"   Data loaded  : {len(x)} rows")

    phases = extract_phases(cfg, x, y)

    has_smooth = (cfg.has_section("smoothing") and
                  cfg.get("smoothing", "method", fallback="none").lower() != "none")
    if has_smooth:
        method = cfg.get("smoothing", "method", fallback="savgol")
        span   = cfg.get("smoothing", "span", fallback="0.15")
        print(f"   Smoothing    : {method}  span={span}")
        print(f"                  (applied to derivatives only; max/min/AUC use raw data)")

    print()

    all_results = []
    all_results.extend(compute_global(cfg, x, y, phases))
    all_results.extend(compute_slope(cfg, x, y, phases))
    all_results.extend(compute_query(cfg, x, y, phases))
    all_results.extend(compute_transitions(cfg, x, y, phases))

    print_results(all_results, cfg, len(x))

    write_results_file(all_results, cfg, cfg_dir, cfg_path)

    if cfg.has_section("output") and cfg.get("output", "plot", fallback="no").lower() == "yes":
        generate_plot(cfg, cfg_dir, cfg_path, x, y, phases)

    if _warnings:
        print(f"\n⚠️  {len(_warnings)} warning(s) issued during analysis.")

    print()


if __name__ == "__main__":
    main()
