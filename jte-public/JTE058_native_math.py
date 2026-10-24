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
    raw_t = np.asarray(time_s)
    raw_x = np.asarray(values)
    if raw_t.dtype.kind not in "fiu" or raw_x.dtype.kind not in "fiu":
        raise ValueError(f"{name}: real numeric arrays required; no complex/coercion")
    if not (raw_t.ndim == 1 or (raw_t.ndim == 2 and 1 in raw_t.shape)):
        raise ValueError(f"{name}: clock must be a vector, not a flattened matrix")
    t = raw_t.astype(float).reshape(-1)
    x = raw_x.astype(float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or t.size != x.shape[0] or t.size < 2 or x.shape[1] < 1:
        raise ValueError(f"{name}: Time/Data dimensions or length invalid")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(x)):
        raise ValueError(f"{name}: nonfinite native trace")
    if np.any(np.diff(t) < 0) or not t[-1] > t[0]:
        raise ValueError(f"{name}: reversed or zero-duration clock")
    with np.errstate(over="raise", invalid="raise"):
        if not np.isfinite(t[-1] - t[0]):
            raise ValueError(f"{name}: nonfinite duration")
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
    """Per-channel maxAbs and time RMSE of piecewise-linear thermal traces.

    Exact integral of SQUARED DIFFERENCE of two explicitly interpolated
    piecewise-linear traces over all union knots. It is NOT exact for the
    unobserved physical Simscape trajectory between logged timestamps.

    Streaming per-column: avoids building multiple dense (union-times x
    312-channel) arrays for 2400-s/variable-step G5 data. O(union-times)
    temporary memory, not O(union-times * channels). No rounding,
    time deduplication or source value modification; conflicting duplicate
    thermal timestamps are rejected.
    """
    ta, xa = _native(t_a, data_a, "thermal_A")
    tb, xb = _native(t_b, data_b, "thermal_B")
    _matched_horizon(ta, tb)
    if xa.shape[1] != xb.shape[1]:
        raise ValueError("Channel count differs")
    ta, xa = _thermal_unique(ta, xa)
    tb, xb = _thermal_unique(tb, xb)
    knots = np.union1d(ta, tb)
    duration = knots[-1] - knots[0]
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        weights = np.diff(knots) / duration
    maxima = np.empty(xa.shape[1], dtype=float)
    rmses = np.empty(xa.shape[1], dtype=float)
    # Process one channel at a time. Avoid allocating 3+ dense 312-column
    # arrays and triggering memory pressure on large native study traces.
    for j in range(xa.shape[1]):
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            d = np.interp(knots, ta, xa[:, j]) - np.interp(knots, tb, xb[:, j])
            scale = float(np.max(np.abs(d)))
            maxima[j] = scale
            if scale == 0:
                rmses[j] = 0.0
                continue
            z = d / scale
            terms = (z[:-1]**2 + z[:-1]*z[1:] + z[1:]**2) / 3.0
            rmses[j] = scale * np.sqrt(max(0.0, float(np.sum(weights*terms))))
    return {
        "max_abs_by_channel": maxima,
        "time_weighted_rmse_by_channel": rmses,
        "method": "native common horizon; piecewise-linear interpolants; per-column exact squared integral",
        "scientific_acceptance": False,
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
    with np.errstate(over="raise", invalid="raise"):
        d = _right_hold(ta, xa, knots[:-1]) - _right_hold(tb, xb, knots[:-1])
        signed = float(np.sum(d*dt))
        absolute = float(np.sum(np.abs(d)*dt))
    return {
        "signed_command_seconds": signed,
        "absolute_command_seconds": absolute,
        "events_a": native_switches(ta, xa),
        "events_b": native_switches(tb, xb),
        "method": "right-continuous zero-order hold; duplicate native rows retained for events",
    }


def observed_event_bracket_diagnostics(time_s, command):
    """Clock-bracket diagnostics for OBSERVED discrete command changes.

    Each change from row i-1 to row i is conservatively bracketed by
    [time[i-1], time[i]]. Equal-time pre/post samples yield a zero-width
    bracket. No timestamp is rounded or projected onto an event instant.

    CONDITIONAL estimate of maximum error in integrating this single command
    if each logged transition represents EXACTLY ONE actual switch somewhere
    in its bracket, and NO other switches were omitted:
        sum(abs(level_after - level_before) * bracket_width_s).
    Without proven source-specific event completeness, the sum is NOT an
    unconditional bound on actual command integrals, event times or energy.
    """
    t, x = _native(time_s, command, "observed_command")
    if x.shape[1] != 1:
        raise ValueError("Expected scalar command")
    y = x[:, 0]
    with np.errstate(over="raise", invalid="raise"):
        idx = np.flatnonzero(np.diff(y) != 0) + 1
        widths = t[idx] - t[idx-1]
        jumps = np.abs(y[idx] - y[idx-1])
        timing_area = float(np.sum(widths*jumps))
        if not np.isfinite(timing_area):
            raise ValueError("Nonfinite event-bracket diagnostic")
    events = [
        {"left_time_s": float(t[i-1]),
         "right_time_s": float(t[i]),
         "before": float(y[i-1]), "after": float(y[i]),
         "bracket_width_s": float(t[i] - t[i-1])}
        for i in idx
    ]
    return {
        "observed_changes": len(events),
        "events": events,
        "candidate_integral_timing_error_command_seconds": timing_area,
        "conditional_on": "one real change per observed bracket, no missing/extra changes, piecewise-constant core command",
        "event_coverage_verified": False,
        "actual_physical_event_times_verified": False,
        "scientific_acceptance": False,
    }
