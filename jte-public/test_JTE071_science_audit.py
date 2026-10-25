"""Read-only JTE071 audit contract tests on fully artificial 312-vectors."""
import tempfile, unittest
from pathlib import Path
import numpy as np
import h5py
from JTE071_native_science_audit import audit_base,check_c0_exact,check_c1_single_channel,exact_matched_pair,solver_surrogate


def fake(path,bias=None,shift=0.):
    tt=np.array([0.,600.,1200.,1800.,2400.])
    vals=np.full((len(tt),312),300.,dtype=float)
    vals[:,0]=np.array([300.,305.,306.,307.,308.])+shift
    vals[:,1]=vals[:,0]
    vals[:,2]=vals[:,0]
    meas=vals.copy()
    if bias is not None:meas[:,3]=vals[:,3]+bias
    with h5py.File(path,"w") as f:
        s=f.create_group("record/signalData")
        def put(name,t,x):
            g=s.create_group(name);g.create_dataset("time_s",data=t.reshape(1,-1))
            g.create_dataset("values",data=x.T)
        put("jteTtrue",tt,vals)
        put("jteTmaxTrue",tt,np.max(vals,axis=1,keepdims=True))
        put("jteTminTrue",tt,np.column_stack((np.min(vals,axis=1),np.max(vals,axis=1))))
        put("jteUcore",tt,np.full((len(tt),1),.25))
        put("jteFlwR",tt,np.full((len(tt),1),.25))
        put("jteTmeas",tt,meas)
    return path

class NativeAuditContract(unittest.TestCase):
  def test_synthetic_c0_pair(self):
    with tempfile.TemporaryDirectory() as t:
      p=fake(Path(t)/"a.mat");q=fake(Path(t)/"b.mat")
      a=audit_base(p);b=audit_base(q);self.assertTrue(check_c0_exact(a))
      self.assertEqual(exact_matched_pair(a,b)["max_abs_temperature_K"],0)
      self.assertEqual(a["minimum_tied_max_channels"],3)
  def test_synthetic_c1_masked_negative(self):
    with tempfile.TemporaryDirectory() as t:
      a=audit_base(fake(Path(t)/"a.mat",bias=-2.))
      x=check_c1_single_channel(a)
      self.assertEqual(x["channel_1based"],4)
      self.assertEqual(x["max_selector_loss_K"],0)
  def test_synthetic_solver_surrogate(self):
    with tempfile.TemporaryDirectory() as t:
      a=audit_base(fake(Path(t)/"a.mat",shift=0))
      b=audit_base(fake(Path(t)/"b.mat",shift=.01))
      d=solver_surrogate(a,b)
      self.assertGreater(d["maxT"]["max_abs"],.009)
      self.assertIn("LINEAR_UNION_GRID",d["method"])
  def test_bad_c0_identity_rejected(self):
    with tempfile.TemporaryDirectory() as t:
      a=audit_base(fake(Path(t)/"a.mat",bias=-2))
      with self.assertRaises(ValueError):check_c0_exact(a)

if __name__=="__main__": unittest.main()
