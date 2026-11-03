"""Two-margin post-processing for the IJEHV BTMS study (hub issue #5).

Pure numpy. Works on synthetic arrays or on the native R-run logs once they exist.
Controller (verified from the pinned MathWorks SLX, see hub DECISIONS.md):
    q = sat[0.001, 0.95](0.1 * (Tmax_meas - Tamb)),  u = max(q - mod(q, 0.25), 0.25)
Level changes only at Tamb + 5 K and Tamb + 7.5 K (inclusive).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict

import numpy as np

TAMB_K = 300.0
THRESHOLDS_K = (5.0, 7.5)  # above ambient


def mod_matlab(x, y):
    """MATLAB mod for y > 0."""
    return x - np.floor(x / y) * y


def u_law(tmax_meas, tamb=TAMB_K):
    q = np.clip(0.1 * (np.asarray(tmax_meas, float) - tamb), 0.001, 0.95)
    return np.maximum(q - mod_matlab(q, 0.25), 0.25)


@dataclass(frozen=True)
class Case:
    name: str
    sensed: tuple          # channel indices, 0-based
    channel: int | None    # biased channel (0-based) or None for b = 0
    bias_K: float

    def __post_init__(self):
        s = np.asarray(self.sensed)
        if len(s) == 0 or len(np.unique(s)) != len(s):
            raise ValueError("sensed set must be non-empty and unique")
        if self.channel is not None and self.channel not in set(self.sensed):
            raise ValueError("biased channel must be sensed (WK08:BiasNotSensed)")


def measured_max(T, case: Case):
    """Direct evaluation: corrupted sensed maximum. T has shape (n_t, n_ch)."""
    T = np.atleast_2d(np.asarray(T, float))
    Tm = T[:, list(case.sensed)].copy()
    if case.channel is not None and case.bias_K != 0.0:
        k = list(case.sensed).index(case.channel)
        Tm[:, k] += case.bias_K
    return Tm.max(axis=1)


def margins(T, case: Case, tamb=TAMB_K):
    """Per-time-step margins on a trajectory (same-state, static)."""
    T = np.atleast_2d(np.asarray(T, float))
    S = list(case.sensed)
    TS = T[:, S]
    true_max = T.max(axis=1)
    sensed_max = TS.max(axis=1)
    s = true_max - sensed_max                       # sparse deficit >= 0
    srt = np.sort(TS, axis=1)
    M = srt[:, -1] - srt[:, -2] if TS.shape[1] > 1 else np.full(len(T), np.inf)
    hottest = np.array(S)[np.argmax(TS, axis=1)]
    on_hottest = (case.channel is not None) & (hottest == (case.channel if case.channel is not None else -1))
    th = np.array(THRESHOLDS_K) + tamb
    below = th[None, :] <= true_max[:, None]
    d = np.where(below.any(axis=1),
                 true_max - np.where(below, th[None, :], -np.inf).max(axis=1), np.nan)
    return dict(true_max=true_max, sensed_max=sensed_max, s=s, M=M, d=d,
                bias_on_hottest=on_hottest)


def effective_underreading(mg, case: Case):
    """Delta_eff = s + min(|b|, M) if a negative bias sits on the hottest sensed channel, else s."""
    b = case.bias_K
    extra = np.where(mg["bias_on_hottest"] & (b < 0), np.minimum(abs(b), mg["M"]), 0.0)
    return mg["s"] + extra


def predicted_downshift(mg, case: Case):
    """Theorem (b <= 0): command drops below full-sensing command iff 0 <= d < Delta_eff."""
    D = effective_underreading(mg, case)
    d = mg["d"]
    return np.where(np.isnan(d), False, d < D)


def predicted_upshift(T, case: Case, tamb=TAMB_K):
    """Positive bias (b > 0): command rises above full-sensing command iff the inflated
    reading reaches the next threshold above the true maximum (thresholds inclusive).

    Delta_up = max(0, T_j + b - Tmax_true); e = (next threshold above Tmax_true) - Tmax_true;
    upshift iff e <= Delta_up. A sparse deficit can only lower the reading, so for b > 0
    the sensed maximum max(sensed_max, T_j + b) is what is compared with the threshold.
    """
    T = np.atleast_2d(np.asarray(T, float))
    if case.channel is None or case.bias_K <= 0:
        return np.zeros(len(T), bool)
    true_max = T.max(axis=1)
    sensed_max = T[:, list(case.sensed)].max(axis=1)
    reading = np.maximum(sensed_max, T[:, case.channel] + case.bias_K)
    th = np.array(THRESHOLDS_K) + tamb
    above = th[None, :] > true_max[:, None]
    e = np.where(above.any(axis=1),
                 np.where(above, th[None, :], np.inf).min(axis=1) - true_max, np.inf)
    return np.isfinite(e) & (true_max + e <= reading)


def command_change(T, case: Case, tamb=TAMB_K):
    """Direct: -1 lower, 0 same, +1 higher command than full-sensing unbiased baseline."""
    u0 = u_law(np.atleast_2d(T).max(axis=1), tamb)
    u1 = u_law(measured_max(T, case), tamb)
    return np.sign(u1 - u0).astype(int)


def intervals(t, mask):
    """[start, end] time intervals where mask is True."""
    t = np.asarray(t, float)
    m = np.asarray(mask, bool)
    out, start = [], None
    for k, v in enumerate(m):
        if v and start is None:
            start = t[k]
        if not v and start is not None:
            out.append([float(start), float(t[k - 1])])
            start = None
    if start is not None:
        out.append([float(start), float(t[-1])])
    return out


def lock_predictions(t, T_baseline, cases, tamb=TAMB_K):
    """Static predictions on the BASELINE trajectory for every case; returns (dict, sha256)."""
    res = {"tamb_K": tamb, "thresholds_K": list(THRESHOLDS_K), "n_steps": int(len(t)), "cases": {}}
    for c in cases:
        mg = margins(T_baseline, c, tamb)
        ch = command_change(T_baseline, c, tamb)
        if c.bias_K <= 0:
            if not np.array_equal(predicted_downshift(mg, c), ch < 0):
                raise AssertionError(f"theorem/direct mismatch (down): {c.name}")
        else:
            if not np.array_equal(predicted_upshift(T_baseline, c, tamb), ch > 0):
                raise AssertionError(f"theorem/direct mismatch (up): {c.name}")
        res["cases"][c.name] = {
            "case": {**asdict(c), "sensed": [int(x) for x in c.sensed]},
            "lower_command_intervals_s": intervals(t, ch < 0),
            "higher_command_intervals_s": intervals(t, ch > 0),
            "min_d_K": None if np.all(np.isnan(mg["d"])) else float(np.nanmin(mg["d"])),
            "min_M_K": float(np.min(mg["M"])),
            "max_s_K": float(np.max(mg["s"])),
        }
    blob = json.dumps(res, sort_keys=True, separators=(",", ":")).encode()
    return res, hashlib.sha256(blob).hexdigest()
