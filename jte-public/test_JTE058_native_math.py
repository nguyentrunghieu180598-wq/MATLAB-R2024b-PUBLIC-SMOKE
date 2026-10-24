"""Synthetic-only tests for JTE058 independent numerical comparison."""
import math
import unittest
import numpy as np
from JTE058_native_math import thermal_comparison, command_integral, native_switches

class NativeMathTests(unittest.TestCase):
    def test_thermal_exact_linear_integral(self):
        r = thermal_comparison([0, 1], [0, 1], [0, .5, 1], [0, 0, 0])
        self.assertAlmostEqual(float(r['time_weighted_rmse_by_channel'][0]), 1/math.sqrt(3), places=12)
        self.assertAlmostEqual(float(r['max_abs_by_channel'][0]), 1.)

    def test_thermal_equal_duplicate_keep(self):
        r = thermal_comparison([0,1,1,2], [0,1,1,2], [0,2], [0,2])
        self.assertAlmostEqual(float(r['max_abs_by_channel'][0]), 0)

    def test_thermal_duplicate_unequal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            thermal_comparison([0,1,1,2], [0,1,9,2], [0,2], [0,2])

    def test_thermal_matrix(self):
        a = np.array([[0,1],[1,2],[2,3]], dtype=float)
        b = a + np.array([2,-2])
        r = thermal_comparison([0,1,2], a, [0,1,2], b)
        np.testing.assert_allclose(r['time_weighted_rmse_by_channel'], [2,2])
        np.testing.assert_allclose(r['max_abs_by_channel'], [2,2])

    def test_native_duplicate_event_preservation(self):
        t = [0,1,1,2]; a = [0,0,.5,.5]
        r = command_integral(t,a,[0,2],[0,0])
        self.assertAlmostEqual(r['absolute_command_seconds'], .5)
        self.assertEqual(r['events_a'], [(1.,0.,.5)])
        self.assertEqual(native_switches(t,a), [(1.,0.,.5)])

    def test_right_hold_and_signed(self):
        r = command_integral([0,.5,1,2], [0,.25,.5,.5], [0,1,2],[0,0,0])
        self.assertAlmostEqual(r['absolute_command_seconds'], .125+.5)
        self.assertAlmostEqual(r['signed_command_seconds'], .125+.5)
        r2 = command_integral([0,2],[0,0],[0,1,2],[0,.5,.5])
        self.assertAlmostEqual(r2['signed_command_seconds'], -.5)

    def test_reversed_time_rejected(self):
        with self.assertRaisesRegex(ValueError,'reversed'):
            thermal_comparison([0,2,1],[0,1,2],[0,2],[0,0])

    def test_horizon_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unmatched'):
            command_integral([0,1],[0,1],[0,2],[0,1])

    def test_command_requires_one_channel(self):
        with self.assertRaisesRegex(ValueError,'scalar'):
            command_integral([0,1],[[0,0],[1,1]],[0,1],[0,1])

    def test_no_extrapolation(self):
        with self.assertRaisesRegex(ValueError,'Unmatched'):
            thermal_comparison([1,2],[1,2],[0,2],[0,2])

if __name__ == '__main__':
    unittest.main()

