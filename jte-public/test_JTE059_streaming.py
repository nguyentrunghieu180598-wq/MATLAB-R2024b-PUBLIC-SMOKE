"""JTE059: synthetic-only regression of memory-safe G5 math/event brackets.

No real battery data, no MATLAB run, no acceptance of physical event coverage.
Run: cd jte-public && python3 -m unittest -v test_JTE059_streaming
"""
import math
import unittest

import numpy as np

from JTE058_native_math import (
    thermal_comparison, observed_event_bracket_diagnostics,
)


class G5MemoryEventTests(unittest.TestCase):
    def test_linear_exact_rmse_and_peak(self):
        r = thermal_comparison([0, 1], [0, 1], [0, .5, 1], [0, 0, 0])
        self.assertAlmostEqual(float(r["max_abs_by_channel"][0]), 1)
        self.assertAlmostEqual(float(r["time_weighted_rmse_by_channel"][0]), 1/math.sqrt(3), places=12)
        self.assertFalse(r["scientific_acceptance"])

    def test_multichannel_independent_sign(self):
        t = [0., 1., 2.]
        a = np.array([[0., 1., 2.], [1., 2., 3.], [2., 3., 4.]])
        b = a + np.array([.01, -.2, 3.])
        r = thermal_comparison(t, a, t, b)
        np.testing.assert_allclose(r["max_abs_by_channel"], [.01, .2, 3])
        np.testing.assert_allclose(r["time_weighted_rmse_by_channel"], [.01, .2, 3], rtol=1e-12)

    def test_large_312_channels_streams(self):
        # Sufficiently wide/time-dense to catch matrix shape errors; no
        # attempt to benchmark Work Cloud RAM or full 2400-s duration.
        t = np.linspace(0., 2400., 10001)
        offset = np.linspace(-.3, .3, 312)
        a = 310. + np.sin(t[:, None] / 90.) + offset[None, :]
        b = a + .02
        r = thermal_comparison(t, a, t, b)
        np.testing.assert_allclose(r["max_abs_by_channel"], .02, rtol=1e-11)
        np.testing.assert_allclose(r["time_weighted_rmse_by_channel"], .02, rtol=1e-11)

    def test_small_big_scale(self):
        for size in (1e200, 1e-200):
            r = thermal_comparison([0, 1], [0, size], [0, 1], [0, 0])
            np.testing.assert_allclose(r["time_weighted_rmse_by_channel"][0], size/math.sqrt(3), rtol=1e-13)

    def test_thermal_duplicate_conflict_rejected(self):
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            thermal_comparison([0,1,1,2],[0,0,10,0],[0,2],[0,0])

    def test_command_bracket_between_samples(self):
        r = observed_event_bracket_diagnostics([0, .999, 1.001, 2], [0,0,.5,.5])
        self.assertEqual(r["observed_changes"], 1)
        self.assertAlmostEqual(r["events"][0]["left_time_s"], .999)
        self.assertAlmostEqual(r["events"][0]["right_time_s"], 1.001)
        self.assertAlmostEqual(r["candidate_integral_timing_error_command_seconds"], .001)
        self.assertFalse(r["event_coverage_verified"])

    def test_equal_timestamp_pre_post_zero_width(self):
        r = observed_event_bracket_diagnostics([0,1,1,2],[0,0,.25,.25])
        self.assertEqual(r["observed_changes"],1)
        self.assertEqual(r["events"][0]["bracket_width_s"],0)
        self.assertEqual(r["candidate_integral_timing_error_command_seconds"],0)

    def test_opposite_instantaneous_transitions(self):
        r = observed_event_bracket_diagnostics([0,1,1,1,2],[0,0,1,0,0])
        self.assertEqual(r["observed_changes"], 2)
        self.assertEqual(r["candidate_integral_timing_error_command_seconds"],0)

    def test_no_observed_change_is_not_proof_no_hidden_change(self):
        r=observed_event_bracket_diagnostics([0,2],[0,0])
        self.assertEqual(r["observed_changes"],0)
        self.assertFalse(r["event_coverage_verified"])

    def test_non_scalar_command_rejected(self):
        with self.assertRaisesRegex(ValueError,"scalar"):
            observed_event_bracket_diagnostics([0,1],[[0,0],[1,1]])

if __name__ == "__main__":
    unittest.main()
