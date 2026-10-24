"""Independent G5 numerical acceptance primitives; synthetic tests only.

No MAT loading, network, secrets, or automatic PASS decision.
Native timestamps and duplicate event rows are never changed in source traces.

Thermal comparison assumes piecewise-linear continuous traces. Repeated
thermal timestamps must have exactly matching values, otherwise comparison is
ambiguous and rejected. Commands use *explicit* right-continuous zero-order
hold: the last row at duplicate time is the post-event value. That assumption
requires review against Simulink logging semantics before study use.
"""
from __future__ import annotations
import numpy as np

def _native(time_s, values, name: str):
    t = np.asarray(time_s, dtype=float).reshape(-1)
    x = np.asarray(values, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or t.size != x.shape[0] or t.size < 2:
        raise ValueError(f"{name}: Time/Data dimensions or length invalid")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(x)):
        raise ValueError(f"{name}: nonfinite native trace")
    if np.any(np.diff(t) < 0) or not t[-1] > t[0]:
        raise ValueError(f"{name}: reversed or zero-duration clock")
    return t, x

def _matched_horizon(t1, t2):
    if t1[0] != t2[0] or t1[-1] != t2[-1]:
        raise ValueError("Unmatched horizon; no extrapolation is allowed")

def _thermal_unique(t, x):
    last = np.r_[np.diff(t) != 0, True]
    for i in np.flatnonzero(~last):
        if not np.array_equal(x[i], x[i+1]):
            raise ValueError("Ambiguous unequal pre/post thermal values at duplicate time")
    return t[last], x[last]

def _linear_columns(t, x, knots):
    return np.column_stack([np.interp(knots, t, x[:, j]) for j in range(x.shape[1])])

def thermal_comparison(t_a, data_a, t_b, data_b):
    """maxAbs and exact time RMSE of piecewise-linear differences, per channel.

    For difference linear on a union-grid interval: integral(delta**2)
    = dt*(d0**2 + d0*d1 + d1**2)/3. Units equal input temperature.
    This is NOT a confidence bound or physical validation.
    """
    ta, xa = _native(t_a, data_a, "thermal_A")
    tb, xb = _native(t_b, data_b, "thermal_B")
    _matched_horizon(ta, tb)
    if xa.shape[1] != xb.shape[1]:
        raise ValueError("Channel count differs")
    ta, xa = _thermal_unique(ta, xa)
    tb, xb = _thermal_unique(tb, xb)
    knots = np.union1d(ta, tb)
    delta = _linear_columns(ta, xa, knots) - _linear_columns(tb, xb, knots)
    dt = np.diff(knots)[:, None]
    integral = np.sum(dt * (delta[:-1]**2 + delta[:-1]*delta[1:] + delta[1:]**2)/3., axis=0)
    rmse = np.sqrt(np.maximum(integral/(knots[-1]-knots[0]), 0.0))
    return {
        "max_abs_by_channel": np.max(np.abs(delta), axis=0),
        "time_weighted_rmse_by_channel": rmse,
        "method": "matched horizon, union knots, linear thermal segments, exact squared integral",
    }

def native_switches(time_s, command):
    """All consecutive row-to-row changes, including zero-duration events."""
    t, x = _native(time_s, command, "command")
    if x.shape[1] != 1:
        raise ValueError("Expected scalar command")
    idx = np.flatnonzero(np.diff(x[:, 0]) != 0) + 1
    return [(float(t[i]), float(x[i-1,0]), float(x[i,0])) for i in idx]

def _right_hold(t, x, knots):
    idx = np.searchsorted(t, knots, side="right") - 1
    if np.any(idx < 0):
        raise ValueError("Missing left endpoint")
    return x[idx, 0]

def command_integral(t_a, data_a, t_b, data_b):
    """Difference area under explicit right-continuous zero-order hold.

    Output is normalized-command*seconds (seconds for dimensionless commands),
    NOT coolant volume, pump power, energy or verified event-time precision.
    """
    ta, xa = _native(t_a, data_a, "command_A")
    tb, xb = _native(t_b, data_b, "command_B")
    _matched_horizon(ta, tb)
    if xa.shape[1] != 1 or xb.shape[1] != 1:
        raise ValueError("Expected scalar command")
    knots = np.union1d(ta, tb)
    dt = np.diff(knots)
    d = _right_hold(ta, xa, knots[:-1]) - _right_hold(tb, xb, knots[:-1])
    return {
        "signed_command_seconds": float(np.sum(d*dt)),
        "absolute_command_seconds": float(np.sum(np.abs(d)*dt)),
        "events_a": native_switches(ta, xa),
        "events_b": native_switches(tb, xb),
        "method": "right-continuous zero-order hold; duplicate native rows retained for events",
    }
