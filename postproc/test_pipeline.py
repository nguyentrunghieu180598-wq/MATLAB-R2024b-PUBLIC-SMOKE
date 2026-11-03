"""Synthetic-only tests for the #5 pipeline: positive-bias theorem, log reader, metrics,
sensitivity band and figures. No MATLAB, no run data."""
import numpy as np
import pytest
import h5py
from scipy.io import savemat

from margins import Case, TAMB_K, command_change, predicted_upshift, lock_predictions
from runlog import read_role, zoh, LogError
from metrics import run_metrics, sensitivity_band, compare
from figures import margin_timeseries, margin_map


# ---------- positive bias (R11) ----------
def test_upshift_hand_example():
    T = np.array([[304.0, 303.0, 302.0]])          # true max 304 K, next threshold 305 K
    assert predicted_upshift(T, Case("p", (0, 1, 2), 0, 1.0))[0]       # 304+1 = 305 inclusive
    assert not predicted_upshift(T, Case("p", (0, 1, 2), 2, 2.0))[0]   # 302+2 = 304 < 305
    assert command_change(T, Case("p", (0, 1, 2), 0, 1.0))[0] == 1


@pytest.mark.parametrize("seed", [20261103, 11])
def test_upshift_oracle_equivalence_random(seed):
    rng = np.random.default_rng(seed)
    ups = 0
    for _ in range(20000):
        T = TAMB_K + rng.uniform(0, 9) + rng.uniform(0.2, 4) * rng.random((1, 312))
        m = int(rng.choice([312, 16, 8]))
        S = tuple(np.sort(rng.choice(312, m, replace=False))) if m < 312 else tuple(range(312))
        c = Case("r", S, int(rng.choice(S)), float(rng.choice([2.0, 4.0])))
        direct = command_change(T, c)[0] > 0
        assert predicted_upshift(T, c)[0] == direct
        ups += direct
    assert ups > 0


def test_lock_checks_positive_case():
    t = np.arange(0, 10.0)
    T = TAMB_K + 4.0 + np.linspace(0, 2, 10)[:, None] + np.linspace(0, 0.3, 312)[None, :]
    res, h = lock_predictions(t, T, [Case("full-hot+2K", tuple(range(312)), 311, 2.0)])
    assert res["cases"]["full-hot+2K"]["higher_command_intervals_s"] and len(h) == 64


# ---------- log reader ----------
def _series(n=6, w=1):
    t = np.linspace(0, 5, n)
    return t, np.arange(n * w, dtype=float).reshape(n, w)


def test_read_v5_npz_v73(tmp_path):
    t, d = _series(w=312)
    savemat(tmp_path / "a.mat", {"time": t[:, None], "data": d})
    np.savez(tmp_path / "a.npz", time=t, data=d)
    p73 = tmp_path / "a73.mat"
    with h5py.File(p73, "w", userblock_size=512) as h:
        h["time"] = t[None, :]           # MATLAB column-major -> h5py sees transpose
        h["data"] = d.T
    with open(p73, "r+b") as f:
        f.write(b"MATLAB 7.3 MAT-file, synthetic test header".ljust(116))
    for p in ("a.mat", "a.npz", "a73.mat"):
        tt, dd = read_role(tmp_path / p, "Ttrue312", stop_time_s=5)
        assert np.array_equal(tt, t) and np.array_equal(dd, d)


@pytest.mark.parametrize("bad,code", [
    ("width", "LOG_WIDTH"), ("nan", "LOG_FINITE"), ("start", "LOG_TIME"),
    ("order", "LOG_TIME"), ("horizon", "LOG_HORIZON"), ("objonly", "LOG_PLAIN_EXPORT_REQUIRED")])
def test_read_rejections(tmp_path, bad, code):
    t, d = _series()
    if bad == "width":
        d = np.hstack([d, d])
    if bad == "nan":
        d[2, 0] = np.nan
    if bad == "start":
        t = t + 0.1
    if bad == "order":
        t[3], t[4] = t[4], t[3]
    p = tmp_path / "x.mat"
    if bad == "objonly":
        savemat(p, {"WK08_TmaxTrue": d})       # native name, no plain export
    else:
        savemat(p, {"time": t[:, None], "data": d})
    with pytest.raises(LogError, match=code):
        read_role(p, "TmaxTrue", stop_time_s=4 if bad == "horizon" else None)


def test_zoh_duplicate_timestamps_keep_last():
    t = np.array([0, 1, 1, 2.0])
    x = np.array([10, 11, 12, 13.0])
    assert list(zoh(t, x, [0, 0.5, 1, 1.5, 2])) == [10, 10, 12, 12, 13]
    with pytest.raises(LogError):
        zoh(t, x, [-0.1])


# ---------- metrics ----------
def _sig(Tmax, u, P, t):
    return {"TmaxTrue": (t, Tmax), "uSampled": (t, u), "pumpPower": (t, P)}


def test_metrics_hand_values():
    t = np.array([0, 1, 2, 3, 4.0])
    Tm = TAMB_K + np.array([4, 5, 6, 8, 7.0])
    u = np.array([0.25, 0.5, 0.5, 0.75, 0.75])
    P = np.array([0, 10, 10, 20, 20.0])
    m = run_metrics(_sig(Tm, u, P, t))
    assert m["T_peak_K"] == TAMB_K + 8
    assert m["t_above_5K_s"] == 3.0 and m["t_above_7.5K_s"] == 1.0
    assert m["J_u"] == pytest.approx((0.25 + 0.5 + 0.5 + 0.75) / 4)
    assert m["n_switches"] == 2
    assert m["E_pump_J"] == pytest.approx(5 + 10 + 15 + 20)
    assert m["E_pump_left_J"] == pytest.approx(0 + 10 + 10 + 20)
    w = run_metrics(_sig(Tm, u, P, t), window=(2, 4))
    assert w["t_above_5K_s"] == 2.0 and w["E_pump_J"] == pytest.approx(35)


def test_band_and_resolution():
    base = {"T_peak_K": 307.0, "J_u": 0.5, "E_pump_J": 100.0, "E_pump_left_J": 99.0}
    var = [{"T_peak_K": 307.02, "J_u": 0.5, "E_pump_J": 100.5, "E_pump_left_J": 99.4},
           {"T_peak_K": 306.99, "J_u": 0.501, "E_pump_J": 100.2, "E_pump_left_J": 99.2}]
    band = sensitivity_band(base, var)
    assert band["T_peak_K"] == pytest.approx(0.02) and band["E_pump_J"] == pytest.approx(1.0)
    case = {"T_peak_K": 307.5, "J_u": 0.5005, "E_pump_J": 100.9, "E_pump_left_J": 99.9}
    r = compare(case, base, band)
    assert r["T_peak_K"]["resolved"] and not r["J_u"]["resolved"]
    assert not r["E_pump_J"]["resolved"] and "E_pump_left_J" not in r


# ---------- figures ----------
def test_figures_write(tmp_path):
    t = np.arange(0, 60.0)
    T = TAMB_K + 4 + 0.08 * t[:, None] + np.linspace(0, 0.6, 312)[None, :]
    c = Case("full-hot-2K", tuple(range(312)), 311, -2.0)
    c16 = Case("C16", tuple(range(5, 312, 20))[:16], None, 0.0)
    margin_timeseries(t, T, c, synthetic=True, path=tmp_path / "ts.png")
    margin_map(T, [c, c16], synthetic=True, path=tmp_path / "map.png")
    assert (tmp_path / "ts.png").stat().st_size > 10_000
    assert (tmp_path / "map.png").stat().st_size > 10_000
