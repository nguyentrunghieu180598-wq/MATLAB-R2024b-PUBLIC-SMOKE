import tempfile,unittest
from pathlib import Path
import h5py,numpy as np
from JTE102_metrics import read,num,event,matched,comparison,config
class NativeAuditTests(unittest.TestCase):
    def test_matlab_reference_shape_and_char(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"f.mat"
            with h5py.File(p,"w") as f:
                g=f.create_group("record");refs=f.create_group("#refs#")
                a=refs.create_dataset("T",data=np.arange(12).reshape(4,3).T);a.attrs["MATLAB_class"]=np.bytes_("double")
                b=g.create_dataset("T",(1,1),dtype=h5py.ref_dtype);b[0,0]=a.ref
                c=g.create_dataset("schema",data=np.array([[ord(x)] for x in "native"],np.uint16));c.attrs["MATLAB_class"]=np.bytes_("char")
            with h5py.File(p,"r") as f:
                self.assertTrue(np.array_equal(num(f,"record/T"),np.arange(12).reshape(4,3)))
                self.assertEqual(read(f,"record/schema"),"native")
    def test_empty_matlab_callback_preserves_config_pair(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"f.mat"
            with h5py.File(p,"w") as f:
                refs=f.create_group("#refs#")
                nodes=[]
                for k,text in enumerate(("Solver","InitFcn","ode23t","")):
                    ar=np.array([[ord(c)] for c in text],np.uint16) if text else np.array([[0],[0]],np.uint64)
                    n=refs.create_dataset(str(k),data=ar);n.attrs["MATLAB_class"]=np.bytes_("char")
                    if not text:n.attrs["MATLAB_empty"]=1
                    nodes.append(n)
                keys=refs.create_dataset("keys",(2,1),dtype=h5py.ref_dtype)
                vals=refs.create_dataset("vals",(2,1),dtype=h5py.ref_dtype)
                for k in range(2):keys[k,0]=nodes[k].ref;vals[k,0]=nodes[k+2].ref
                c=f.create_dataset("cfg",(2,1),dtype=h5py.ref_dtype);c[0,0]=keys.ref;c[1,0]=vals.ref
            with h5py.File(p,"r") as f:self.assertEqual(config(f,"cfg"),{"Solver":"ode23t","InitFcn":""})
    def test_repeated_event_zero_time_not_extra_duration(self):
        t=np.array([330.,331.,331.,332.]);u=np.full(4,.25);y=np.array([.25,.35,.15,.25]);T=np.full((4,312),300.)
        e=event(t,y,u,T,(330.,338.))
        self.assertAlmostEqual(e["signedArea_trapezoid_normalized_s"],0.)
        self.assertAlmostEqual(e["absoluteEndpointArea_trapezoid_normalized_s"],.1)
        self.assertEqual(e["repeatPostfilter"]["adjacentRepeatCount"],1)
        self.assertAlmostEqual(e["repeatPostfilter"]["maxAdjacentValueChange"],.2)
        self.assertEqual(e["exceedanceIntervalUnion_s"],2.)
    def test_duplicate_multiplicity_not_blindly_joined(self):
        t=np.array([0.,1.,1.,2.]);s=np.array([0.,1.,2.])
        i,j,exact,amb=matched(t,s)
        self.assertFalse(exact);self.assertEqual(amb,1)
        self.assertTrue(np.array_equal(i,[0,3]));self.assertTrue(np.array_equal(j,[0,2]))
    def test_no_interpolation_and_per_channel_error(self):
        a={"t":np.array([0.,1.,2.]),"T":np.array([[300.,300.],[301.,302.],[302.,304.]])}
        b={"t":np.array([0.,.5,1.,2.]),"T":np.array([[300.,300.],[999.,999.],[301.5,302.],[302.,304.]])}
        r=comparison(a,b)
        self.assertEqual(r["matchedRows"],3);self.assertEqual(r["maxAbs"],.5)
        self.assertFalse(r["fullNativeVectorIdentity"])
    def test_no_common_event_clock_is_unavailable_not_failure(self):
        a={"t":np.array([0.,330.1,331.1,340.]),"T":np.full((4,2),300.)}
        b={"t":np.array([0.,330.2,331.2,340.]),"T":np.full((4,2),300.)}
        r=comparison(a,b,window=(330.,338.))
        self.assertEqual(r["status"],"UNAVAILABLE_NO_EXACT_COMMON_NATIVE_POINTS")
        self.assertIsNone(r["maxAbs"]);self.assertFalse(r["fullNativeVectorIdentity"])
    def test_localization_is_not_roundoff_acceptance(self):
        t=np.array([330.,331.,332.]);u=np.full(3,.25);T=np.full((3,312),300.)
        e=event(t,np.array([.25,.251,.25]),u,T,(330.,338.))
        self.assertFalse(e["excursion"]);self.assertGreater(e["residualPeakAbs"],0)
        self.assertEqual(e["thresholdRole"],"LOCALIZATION_NOT_ACCEPTANCE")
if __name__=="__main__":unittest.main()
