"""Synthetic-only source-matched FlwR_calc and measurement-selector tests."""
import unittest
import numpy as np
from JTE060_selector_oracle import pinned_core_command, same_state_oracle


class SourceSelectorTests(unittest.TestCase):
    def test_controller_levels_away_from_and_at_ideal_boundaries(self):
        d=np.array([-20.,0.,4.99,5.,5.01,7.49,7.5,7.51,20.])
        np.testing.assert_allclose(pinned_core_command(d),[.25,.25,.25,.5,.5,.5,.75,.75,.75])

    def test_masked_cold_channel(self):
        T=np.full((3,312),310.)
        T[:,5]=318.
        r=same_state_oracle(T,1,-2.,300.)
        np.testing.assert_array_equal(r['selector_loss_K'],0.)
        np.testing.assert_array_equal(r['core_shadow'],r['core_biased_same_state'])

    def test_hottest_channel_and_threshold_cross(self):
        # In source's same state, j=1 leads by 3 K and bias reduces Tmax by 2.
        T=np.full((3,312),300.)
        T[:,0]=[305.5,307.6,309.]
        T[:,1:]=T[:,[0]]-3.
        r=same_state_oracle(T,1,-2.,300.)
        np.testing.assert_allclose(r['selector_loss_K'],[2,2,2])
        np.testing.assert_allclose(r['core_shadow']-r['core_biased_same_state'],[.25,.25,.25])

    def test_tied_max_masked(self):
        T=np.full((2,312),307.)
        T[:,0]=310.
        T[:,1]=310.
        r=same_state_oracle(T,1,-2.,300.)
        np.testing.assert_allclose(r['selector_loss_K'],0.)

    def test_partial_unmasking(self):
        T=np.full((2,312),305.)
        T[:,0]=[309.,309.]
        T[:,10]=308.
        r=same_state_oracle(T,1,-2.,300.)
        np.testing.assert_allclose(r['selector_loss_K'],1.)

    def test_random_312_channels_three_targets(self):
        rng=np.random.default_rng(2026)
        T=303.+16.*rng.random((50,312))
        for j in [1,156,312]:
            r=same_state_oracle(T,j,-2.,300.)
            np.testing.assert_allclose(r['selector_loss_K'],r['selector_oracle_K'],rtol=0.,atol=1e-10)
            self.assertTrue(np.all(r['selector_loss_K']>=-1e-10))
            self.assertTrue(np.all(r['selector_loss_K']<=2.+1e-10))
            self.assertTrue(np.all(r['core_biased_same_state']<=r['core_shadow']+1e-10))

    def test_reject_complex_and_wrong_count(self):
        with self.assertRaises(ValueError):
            same_state_oracle(np.ones((4,2)),1,-2.,300.)
        with self.assertRaises(ValueError):
            same_state_oracle(1j*np.ones((4,312)),1,-2.,300.)
        with self.assertRaises(ValueError):
            same_state_oracle(np.ones((4,312)),True,-2.,300.)

    def test_distinguishes_masking_from_no_command_change(self):
        T=np.full((2,312),301.)
        T[:,0]=[306.4,306.6]
        T[:,1:]=T[:,[0]]-3.
        r=same_state_oracle(T,1,-.2,300.)
        self.assertTrue(np.all(r['selector_loss_K']>.1))
        np.testing.assert_allclose(r['core_shadow'],r['core_biased_same_state'])

    def test_reject_time_varying_ambient_wrong_length(self):
        with self.assertRaisesRegex(ValueError,'Ambient'):
            same_state_oracle(np.ones((4,312)),1,-2.,np.ones(5))

if __name__=='__main__':
    unittest.main()
