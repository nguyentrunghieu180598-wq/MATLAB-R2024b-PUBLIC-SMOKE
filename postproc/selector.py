"""JTE-050 v02 channel selector, computed from the accepted R2 baseline (hub #5).

Output is the exact JSON that jte-public/WK09_run_definitions.resolve() consumes.
Rule (pre-registered): time-weighted mean of each channel over 1800..2400 s of R2,
ranked descending, ties by ascending 1-based channel index. The mean is the trapezoid
integral over the window divided by 600 s; the window ends are linearly interpolated,
as in JTE067_G6_case.m (trapz/T). Never a MAX statistic (v01 is rejected).
"""
from __future__ import annotations

import numpy as np

WINDOW_S = (1800.0, 2400.0)


def window_means(t, T, window=WINDOW_S):
    t = np.asarray(t, float)
    T = np.atleast_2d(np.asarray(T, float))
    a, b = window
    if not (t[0] <= a and t[-1] >= b and np.all(np.diff(t) >= 0) and np.isfinite(T).all()):
        raise ValueError("SELECTOR_WINDOW_NOT_COVERED_OR_INVALID")
    inside = (t > a) & (t < b)
    tw = np.concatenate(([a], t[inside], [b]))
    edges = np.vstack([[np.interp(a, t, T[:, k]) for k in range(T.shape[1])],
                       T[inside],
                       [np.interp(b, t, T[:, k]) for k in range(T.shape[1])]])
    return np.trapezoid(edges, tw, axis=0) / (b - a)


def selector_v02(t, T, baseline_receipt_sha256):
    if not (isinstance(baseline_receipt_sha256, str) and len(baseline_receipt_sha256) == 64):
        raise ValueError("SELECTOR_RECEIPT")
    m = window_means(t, T)
    if m.size != 312:
        raise ValueError("SELECTOR_WIDTH")
    idx = np.arange(1, 313)
    order = [int(i) for i in idx[np.lexsort((idx, -m))]]  # mean desc, then index asc
    return {
        "version": "JTE-050 v02",
        "source_run": "R2",
        "window_s": [1800, 2400],
        "statistic": "time-weighted mean",
        "integration": "trapezoid, window ends linearly interpolated, divided by 600 s",
        "accepted_baseline_receipt_SHA256": baseline_receipt_sha256,
        "ranking_descending": order,
        "means_K": [float(x) for x in m],
    }
