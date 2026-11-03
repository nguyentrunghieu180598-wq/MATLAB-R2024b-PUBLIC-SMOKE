"""Tests for the v02 selector, the prediction freeze, and equivalence with the hub oracle."""
import numpy as np
import pytest

import freeze as F
import margins as P
import selector as SEL

RECEIPT = "a" * 64


# --- equivalence with hub tools/two_margin_oracle_static.py -----------------------------
# Hub file SHA-256 eeb0b06e3e2c7860e40169284beb89fe1272c577a58ad16bbd4197ca3fd553d0
# (BTMS-IJEHV-hub @ cace1a7). oracle_predict() below is its predict(), unchanged.
def oracle_predict(T, S, j, b):
    Ts = T[S]; tm0 = Ts.max(); k = int(np.argmax(Ts)); jj = list(S).index(j)
    others = np.delete(Ts, jj)
    if b < 0:
        tmb = tm0 if jj != k else max(Ts[jj] + b, others.max())
    else:
        tmb = max(tm0, Ts[jj] + b)
    return tm0, tmb


def test_postproc_reproduces_hub_oracle_20000_states():
    rng = np.random.default_rng(20261103)
    bad = 0
    for _ in range(20000):
        T = 300 + rng.uniform(0, 9) + rng.uniform(0.2, 4) * rng.random(312)
        m = int(rng.choice([312, 16, 8]))
        S = np.sort(rng.choice(312, m, replace=False)) if m < 312 else np.arange(312)
        j = int(rng.choice(S)); b = float(rng.choice([-4, -2, 2]))
        c = P.Case("x", tuple(int(x) for x in S), j, b)
        tm0, tmb = oracle_predict(T, S, j, b)
        bad += P.measured_max(T[None, :], c)[0] != tmb
        u_full, u_b = P.u_law(np.array([T.max()]))[0], P.u_law(np.array([tmb]))[0]
        bad += np.sign(u_b - u_full) != P.command_change(T[None, :], c)[0]
        if m == 312:
            lo, hi = min(tm0, tmb), max(tm0, tmb)
            flip = any(lo < 300 + th <= hi for th in (5.0, 7.5))
            bad += flip != (P.command_change(T[None, :], c)[0] != 0)
    assert bad == 0


# --- selector -------------------------------------------------------------------------
def test_selector_window_ties_and_format():
    t = np.array([0.0, 1700.0, 1900.0, 2400.0])
    T = np.full((4, 312), 300.0)
    T[:, 9] = 310.0          # channel 10 hottest
    T[:, 4] = T[:, 6] = 305.0  # tie: channel 5 before channel 7
    T[0, 0] = 400.0          # outside the window: must not count
    s = SEL.selector_v02(t, T, RECEIPT)
    order = s["ranking_descending"]
    assert order[:3] == [10, 5, 7] and sorted(order) == list(range(1, 313))
    assert s["version"] == "JTE-050 v02" and s["source_run"] == "R2"
    assert s["window_s"] == [1800, 2400] and s["statistic"] == "time-weighted mean"


def test_selector_interpolates_window_ends():
    t = np.array([0.0, 2000.0, 2400.0])
    T = np.full((3, 312), 300.0)
    T[:, 0] = [300.0, 310.0, 310.0]   # value at 1800 s = 309 by interpolation
    m = SEL.window_means(t, T)
    assert m[0] == pytest.approx((0.5 * (309 + 310) * 200 + 310 * 400) / 600)


@pytest.mark.parametrize("t", [np.array([1900.0, 2400.0]), np.array([0.0, 2300.0])])
def test_selector_rejects_uncovered_window(t):
    with pytest.raises(ValueError):
        SEL.selector_v02(t, np.full((2, 312), 300.0), RECEIPT)


# --- freeze ---------------------------------------------------------------------------
def runs(order):
    full, s16, s8 = list(range(1, 313)), list(range(1, 313, 20))[:16], list(range(1, 313, 40))[:8]
    first_in = lambda S: next(j for j in order if j in S)
    spec = {"R5": (full, 0, 1), "R6": (full, -2, order[0]), "R7": (full, -2, order[155]),
            "R8": (s16, -2, first_in(s16)), "R9": (s16, -4, first_in(s16)),
            "R10": (s8, -4, first_in(s8)), "R11": (full, 2, order[0]),
            "R12": (s16, 0, s16[0]), "R13": (s8, 0, s8[0])}
    return [{"id": k, "subset": S, "bias_K": b, "channel": j,
             "resolution": "SOURCE_CONTRACT_ONLY_NOT_RUN_AUTHORIZATION"} for k, (S, b, j) in spec.items()]


def synthetic_baseline():
    t = np.linspace(0, 2400, 241)
    rng = np.random.default_rng(7)
    T = 300 + np.outer(t / 2400, 4 + 4 * rng.random(312)) + 0.05 * rng.random((241, 312))
    return t, T


def test_freeze_is_deterministic_and_complete():
    t, T = synthetic_baseline()
    sel = SEL.selector_v02(t, T, RECEIPT)
    rs = runs(sel["ranking_descending"])
    out1, h1 = F.freeze(t, T, rs, "b" * 64)
    out2, h2 = F.freeze(t, T, rs, "b" * 64)
    assert h1 == h2 and len(h1) == 64
    assert set(out1["full_sensing"]) == set(F.PREDICTED_RUNS)
    assert set(out1["paired_control"]) == set(F.PAIRED_CONTROL)
    # b = 0 full sensing (R5) predicts no change anywhere
    assert out1["full_sensing"]["R5"]["lower_command_intervals_s"] == []
    assert out1["full_sensing"]["R5"]["higher_command_intervals_s"] == []
    # a negative bias can only lower and a positive bias only raise the command vs its control
    for k in ("R6", "R7", "R8", "R9", "R10"):
        assert out1["paired_control"][k]["higher_command_intervals_s"] == []
    assert out1["paired_control"]["R11"]["lower_command_intervals_s"] == []


def test_freeze_rejects_unresolved_or_wrong_run_set():
    t, T = synthetic_baseline()
    rs = runs(list(range(1, 313)))
    rs[1] = {**rs[1], "channel": None, "resolution": "BLOCKED_PENDING_ACCEPTED_R2_V02_SELECTOR"}
    with pytest.raises(ValueError):
        F.freeze(t, T, rs, "b" * 64)
    with pytest.raises(ValueError):
        F.freeze(t, T, runs(list(range(1, 313)))[:-1], "b" * 64)
