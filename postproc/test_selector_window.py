import numpy as np
from postproc.selector import selector_v02, window_means

def test_default_metadata_unchanged():
    t = np.arange(0, 2401.0); T = np.tile(np.linspace(300, 310, 312), (t.size, 1))
    s = selector_v02(t, T, "0" * 64)
    assert s["window_s"] == [1800, 2400] and s["integration"].endswith("600 s")

def test_d13_window_metadata_order_and_ties():
    t = np.arange(0, 341.0); base = np.linspace(300, 310, 312)
    T = np.tile(base, (t.size, 1)); T[:, 10] = T[:, 11] = base.max() + 1   # exact tie -> lower index first
    s = selector_v02(t, T, "a" * 64, window=(200.0, 340.0))
    assert s["window_s"] == [200, 340] and s["integration"].endswith("140 s")
    assert s["ranking_descending"][:2] == [11, 12]
    assert np.allclose(window_means(t, T, (200, 340)), T[0])
