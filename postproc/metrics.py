"""Run-level comparison metrics (hub issue #5).

Every quantity is computed from logged signals only; nothing is modelled here.
    T_peak_K        max of the logged true pack maximum (TmaxTrue)
    t_above_<x>K_s  time with TmaxTrue >= Tamb + x  (left-rectangle on the logged grid)
    J_u             time-averaged command (uSampled), piecewise constant -> left rectangle
    n_switches      number of command level changes
    E_pump_J        integral of the logged pump power (pumpPower), trapezoid; the
                    left-rectangle value is kept, and the gap between the two rules is part
                    of the reported numerical uncertainty
A case effect is called RESOLVED only if |effect| exceeds the numerical-sensitivity band:
the largest change of the same metric between the baseline (R2) and its numerical
variants (R3 Ts, R4 tolerance), and at least the integration-rule gap.
"""
from __future__ import annotations

import numpy as np

from margins import TAMB_K, THRESHOLDS_K


def _window(t, x, window):
    t = np.asarray(t, float)
    x = np.asarray(x, float).reshape(len(t), -1)[:, 0]
    if window is None:
        return t, x
    t0, t1 = map(float, window)
    keep = (t >= t0) & (t <= t1)
    if keep.sum() < 2:
        raise ValueError("METRIC_WINDOW_TOO_SHORT")
    return t[keep], x[keep]


def _left(t, x):
    return float(np.sum(x[:-1] * np.diff(t)))


def _trap(t, x):
    return float(np.sum(0.5 * (x[:-1] + x[1:]) * np.diff(t)))


def run_metrics(sig, tamb=TAMB_K, window=None):
    """sig: dict role -> (t, data) for TmaxTrue, uSampled, pumpPower."""
    tT, T = _window(*sig["TmaxTrue"], window)
    tu, u = _window(*sig["uSampled"], window)
    tP, P = _window(*sig["pumpPower"], window)
    out = {"T_peak_K": float(T.max())}
    for x in THRESHOLDS_K:
        out[f"t_above_{x:g}K_s"] = _left(tT, (T >= tamb + x).astype(float))
    span = tu[-1] - tu[0]
    out["J_u"] = _left(tu, u) / span
    out["n_switches"] = int(np.count_nonzero(np.diff(u)))
    out["E_pump_J"] = _trap(tP, P)
    out["E_pump_left_J"] = _left(tP, P)
    return out


def sensitivity_band(baseline, variants):
    """Per metric: max |variant - baseline| over the numerical variants, and the
    integration-rule gap for pump energy."""
    band = {}
    for k, v in baseline.items():
        diffs = [abs(var[k] - v) for var in variants]
        band[k] = float(max(diffs)) if diffs else 0.0
    gap = abs(baseline["E_pump_J"] - baseline["E_pump_left_J"])
    band["E_pump_J"] = max(band["E_pump_J"], gap)
    return band


def compare(case, baseline, band):
    """Effect = case - baseline per metric, with a RESOLVED flag (strictly above band)."""
    res = {}
    for k in baseline:
        if k == "E_pump_left_J":
            continue
        eff = float(case[k] - baseline[k])
        res[k] = {"effect": eff, "band": band[k], "resolved": abs(eff) > band[k]}
    return res
