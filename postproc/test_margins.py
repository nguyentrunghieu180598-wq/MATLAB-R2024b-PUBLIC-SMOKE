import numpy as np
import pytest
from margins import (Case, u_law, measured_max, margins, predicted_downshift,
                     command_change, lock_predictions, TAMB_K)


def test_thresholds_inclusive():
    assert u_law(TAMB_K + 5 - 1e-12) == 0.25 and u_law(TAMB_K + 5) == 0.5
    assert u_law(TAMB_K + 7.5 - 1e-12) == 0.5 and u_law(TAMB_K + 7.5) == 0.75
    dT = np.arange(0, 12, 1e-4)
    u = u_law(TAMB_K + dT)
    jumps = dT[1:][np.diff(u) != 0]
    assert np.allclose(jumps, [5.0, 7.5])


def test_hand_example_three_channels():
    T = np.array([[305.6, 305.1, 303.0]])         # hottest 305.6, second 305.1 -> M = 0.5
    c = Case("hot-2K", (0, 1, 2), 0, -2.0)
    assert measured_max(T, c)[0] == pytest.approx(305.1)
    mg = margins(T, c)
    assert mg["M"][0] == pytest.approx(0.5) and mg["d"][0] == pytest.approx(0.6)
    # Delta_eff = min(2, 0.5) = 0.5 < d = 0.6 -> no change (masking)
    assert not predicted_downshift(mg, c)[0] and command_change(T, c)[0] == 0
    c2 = Case("median-2K", (0, 1, 2), 2, -2.0)    # bias on non-hottest: fully masked
    assert command_change(T, c2)[0] == 0


def test_bias_on_unsensed_channel_rejected():
    with pytest.raises(ValueError):
        Case("bad", (0, 1), 5, -2.0)


@pytest.mark.parametrize("seed", [20261102, 7])
def test_oracle_equivalence_random(seed):
    """Reproduces hub tools/two_margin_oracle_*.py: theorem == direct evaluation, 0 mismatches."""
    rng = np.random.default_rng(seed)
    flips = 0
    for _ in range(20000):
        T = TAMB_K + rng.uniform(0, 9) + rng.uniform(0.2, 4) * rng.random((1, 312))
        m = int(rng.choice([312, 16, 8]))
        S = tuple(np.sort(rng.choice(312, m, replace=False))) if m < 312 else tuple(range(312))
        j = int(rng.choice(S))
        b = float(rng.choice([-4.0, -2.0]))
        c = Case("r", S, j, b)
        direct = command_change(T, c)[0] < 0
        assert predicted_downshift(margins(T, c), c)[0] == direct
        flips += direct
    assert flips > 0


def test_lock_predictions_deterministic():
    t = np.arange(0, 10.0)
    T = TAMB_K + 4.0 + np.linspace(0, 2, 10)[:, None] + np.linspace(0, 0.3, 312)[None, :]
    cases = [Case("full-hot-2K", tuple(range(312)), 311, -2.0),
             Case("C8", (17, 53, 89, 131, 179, 221, 257, 293), None, 0.0)]
    r1, h1 = lock_predictions(t, T, cases)
    r2, h2 = lock_predictions(t, T, cases)
    assert h1 == h2 and len(h1) == 64
    assert r1["cases"]["C8"]["max_s_K"] > 0
