"""Reader for exported WK08/WK09 run logs (hub issue #5).

The native Simulink To File sinks use SaveFormat='Timeseries'. A MATLAB timeseries is an
MCOS object; scipy and h5py cannot decode it. Python therefore reads a PLAIN export that
a reviewed MATLAB step must write after the run (one file per role):

    time : n x 1 double, data : n x w double        (MAT v5/v7 via scipy, v7.3 via h5py)
    or an .npz with arrays 'time' and 'data'.

Validation mirrors readNative() in jte-public/BTMS_WK08_run.m: finite values, time starts
at 0, non-decreasing, expected width, and (optionally) a complete horizon.
Roles and widths follow BTMS_WK08_prepare.m.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

ROLE_WIDTH = {
    "uCore": 1, "uSampled": 1, "actuatorY": 1, "Ttrue312": 312,
    "TmaxTrue": 1, "TmaxMeas": 1, "pumpPower": 1, "Ttrue312_1s": 312,
}


class LogError(ValueError):
    pass


def _need(cond, code):
    if not cond:
        raise LogError(code)


def _load_raw(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".npz":
        with np.load(path, allow_pickle=False) as z:
            return np.asarray(z["time"], float), np.asarray(z["data"], float)
    _need(suffix == ".mat", "LOG_UNSUPPORTED_SUFFIX")
    with path.open("rb") as f:
        head = f.read(128)
    if head.startswith(b"\x89HDF") or b"MATLAB 7.3" in head:
        import h5py
        with h5py.File(path, "r") as h:
            _need("time" in h and "data" in h, "LOG_PLAIN_EXPORT_REQUIRED")
            # MATLAB v7.3 stores column-major; h5py exposes the transpose.
            return np.asarray(h["time"], float).T, np.asarray(h["data"], float).T
    from scipy.io import loadmat
    m = loadmat(path)
    _need("time" in m and "data" in m, "LOG_PLAIN_EXPORT_REQUIRED")
    _need(np.issubdtype(m["data"].dtype, np.number), "LOG_PLAIN_EXPORT_REQUIRED")
    return np.asarray(m["time"], float), np.asarray(m["data"], float)


def read_role(path, role, stop_time_s=None):
    """Return (time[n], data[n, w]) for one exported role, validated."""
    _need(role in ROLE_WIDTH, "LOG_UNKNOWN_ROLE")
    t, d = _load_raw(Path(path))
    t = t.reshape(-1)
    _need(t.size > 0, "LOG_EMPTY")
    if d.ndim == 1:
        d = d.reshape(-1, 1)
    if d.shape[0] != t.size and d.shape[1] == t.size:
        d = d.T
    w = ROLE_WIDTH[role]
    _need(d.shape == (t.size, w), "LOG_WIDTH")
    _need(np.all(np.isfinite(t)) and np.all(np.isfinite(d)), "LOG_FINITE")
    _need(t[0] == 0.0 and np.all(np.diff(t) >= 0), "LOG_TIME")
    if stop_time_s is not None:
        _need(t[-1] == float(stop_time_s), "LOG_HORIZON")
    return t, d


def zoh(t_src, x_src, t_query):
    """Zero-order hold (last sample at or before t). Duplicate time stamps (event
    restarts) keep the LAST value, as Simulink does for the major step after an event."""
    t_src = np.asarray(t_src, float)
    x_src = np.asarray(x_src, float)
    idx = np.searchsorted(t_src, np.asarray(t_query, float), side="right") - 1
    if np.any(idx < 0):
        raise LogError("LOG_ZOH_BEFORE_START")
    return x_src[idx]
