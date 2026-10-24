"""Adversarial synthetic fixtures, not MATLAB or G5 results."""
import unittest,math
import numpy as np
from JTE058_native_math import thermal_comparison,command_integral,native_switches
from JTE058_C1_contract import validate_c1,command_area_qualified

class ReviewTests(unittest.TestCase):
 def test_matrix_clock_rejected(self):
  with self.assertRaisesRegex(ValueError,'vector'):
   thermal_comparison([[0,1],[2,3]],[0,1,2,3],[0,3],[0,3])
 def test_complex_rejected(self):
  with self.assertRaisesRegex(ValueError,'real numeric'):
   thermal_comparison([0,1],[1+2j,2+3j],[0,1],[1,2])
 def test_string_coercion_rejected(self):
  with self.assertRaises(ValueError):thermal_comparison(['0','1'],[0,1],[0,1],[0,1])
 def test_empty_channels_rejected(self):
  with self.assertRaises(ValueError):thermal_comparison([0,1],np.empty((2,0)),[0,1],np.empty((2,0)))
 def test_finite_extreme_scale_rmse(self):
  for a in [1e200,1e-200]:
   got=thermal_comparison([0,1],[0,a],[0,1],[0,0])['time_weighted_rmse_by_channel'][0]
   np.testing.assert_allclose(got,a/math.sqrt(3),rtol=1e-14,atol=0)
 def test_zero_duration_switches_retained_no_area(self):
  t=[0,1,1,1,2];u=[0,0,1,0,0]
  self.assertEqual(native_switches(t,u),[(1.,0.,1.),(1.,1.,0.)])
  self.assertEqual(command_integral(t,u,[0,2],[0,0])['absolute_command_seconds'],0)
 def test_terminal_event_zero_area(self):
  self.assertEqual(command_integral([0,2,2],[0,0,1],[0,2],[0,0])['absolute_command_seconds'],0)
 def test_different_clocks_same_horizon(self):
  r=thermal_comparison([0,.25,2],[0,.25,2],[0,1,1.5,2],[0,1,1.5,2])
  self.assertEqual(r['max_abs_by_channel'][0],0)
 def test_overlap_is_not_complete_horizon(self):
  with self.assertRaisesRegex(ValueError,'Unmatched'):
   thermal_comparison([0,2],[0,2],[1,3],[1,3])
 def test_postfilter_zoh_refused(self):
  with self.assertRaisesRegex(ValueError,'never jteFlwR'):
   command_area_qualified([0,1],[0,1],[0,1],[0,0],signal_name='jteFlwR',semantics='verified_right_continuous_zoh',evidence_id='synthetic')
 def test_unverified_core_zoh_refused(self):
  with self.assertRaises(ValueError):
   command_area_qualified([0,1],[0,1],[0,1],[0,0],signal_name='jteUcore',semantics='unverified',evidence_id='')
 def test_C1_same_case_not_C0_state(self):
  # These physical states need not match another case's baseline.
  T=np.full((4,312),330.);T[2:]+=1
  M=T.copy();M[:,7]-=2
  self.assertEqual(validate_c1([0,1,1,2],T,[0,1,1,2],M,8,-2)['channels'],312)
 def test_C1_second_channel_wrong(self):
  T=np.full((2,312),315.);M=T.copy();M[:,0]-=2;M[:,1]-=2
  with self.assertRaisesRegex(ValueError,'exactly'):validate_c1([0,2],T,[0,2],M,1,-2)
 def test_C1_zero_bias_is_not_C1(self):
  T=np.full((2,312),315.)
  with self.assertRaises(ValueError):validate_c1([0,2],T,[0,2],T,1,0)
 def test_C1_scalar_aftermax_rejected(self):
  T=np.full((2,312),315.)
  with self.assertRaisesRegex(ValueError,'full312'):validate_c1([0,2],T,[0,2],[313,313],1,-2)
 def test_C1_mismatched_clock_and_boolean_channel(self):
  T=np.full((2,312),315.);M=T.copy();M[:,0]-=2
  with self.assertRaises(ValueError):validate_c1([0,2],T,[0,3],M,1,-2)
  with self.assertRaises(ValueError):validate_c1([0,2],T,[0,2],M,True,-2)

if __name__=='__main__':unittest.main()
