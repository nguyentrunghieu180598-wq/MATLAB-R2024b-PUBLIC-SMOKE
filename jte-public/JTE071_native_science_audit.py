"""JTE071 native private MAT SCIENCE AUDIT — no publication artifact.

Read-only. Never uploads or publishes private numerical data.
Strictly local execution against owner-downloaded SHA-verified MATLAB v7.3
files. Two distinct evidence types:
  (1) EXACT native on-sample zero-bias/within-case vector invariants.
  (2) LINEAR union-grid surrogate comparisons of different solver outputs.
Interpolation is declared and cannot prove sub-step control event capture.
Requires h5py and numpy. Only aggregate internal result returned; no file
created unless separately authorized by owner.
"""
import hashlib
from pathlib import Path
import h5py
import numpy as np


def check_sha(path, expected=None):
    sha=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(8*1024**2),b""):
            sha.update(b)
    got=sha.hexdigest()
    if expected is not None and got.lower()!=expected.lower():
        raise ValueError("JTE071_SHA_MISMATCH")
    return got


def signal(f, name):
    b=f["record/signalData/"+name]
    t=np.asarray(b["time_s"]).reshape(-1).astype(np.float64)
    x=np.asarray(b["values"],dtype=np.float64).T
    if x.shape[0]!=len(t) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(t)):
        raise ValueError("JTE071_INVALID_SIGNAL")
    if t.size<2 or np.any(np.diff(t)<0):
        raise ValueError("JTE071_CLOCK_REVERSED_OR_TOO_SHORT")
    if t[0]!=0 or abs(t[-1]-2400)>1e-8:
        raise ValueError("JTE071_HORIZON_INCOMPLETE")
    return t,x


def audit_base(path):
    check_sha(path)
    with h5py.File(path) as f:
        t,T=signal(f,"jteTtrue")
        if T.shape[1]!=312:
            raise ValueError("JTE071_BAD_SENSOR_COUNT")
        tp,pair=signal(f,"jteTminTrue")
        tx,mx=signal(f,"jteTmaxTrue")
        if not np.array_equal(t,tp) or not np.array_equal(t,tx):
            raise ValueError("JTE071_REDUCER_CLOCK")
        if pair.shape!=(len(t),2) or mx.shape!=(len(t),1):
            raise ValueError("JTE071_REDUCER_SHAPE")
        if not np.array_equal(pair[:,0],np.min(T,axis=1)) or not np.array_equal(pair[:,1],np.max(T,axis=1)) or not np.array_equal(mx[:,0],np.max(T,axis=1)):
            raise ValueError("JTE071_REDUCER_MISMATCH")
        tc,u=signal(f,"jteUcore")
        tf,flow=signal(f,"jteFlwR")
        if u.shape[1]!=1 or flow.shape[1]!=1:
            raise ValueError("JTE071_BAD_COMMAND_SHAPE")
        if "jteTmeas" in f["record/signalData"]:
            tm,M=signal(f,"jteTmeas")
            if not np.array_equal(t,tm) or M.shape!=T.shape:
                raise ValueError("JTE071_MEAS_CLOCK_OR_SHAPE")
        else:M=None
        nTie=np.count_nonzero(T==T.max(axis=1,keepdims=True),axis=1)
        return dict(time=t,T=T,u=u[:,0],tc=tc,flow=flow[:,0],tf=tf,measurement=M,
            count=len(t),minT=float(T.min()),maxT=float(T.max()),
            minimum_tied_max_channels=int(nTie.min()),
            maxselector_tied_fraction=float(np.mean(nTie>=2)),
            max_core_levels=int(len(np.unique(u))),
            core_levels=np.unique(u[:,0]).tolist(),
            max_temperature_span_K=float(np.max(T.max(axis=1)-T.min(axis=1))))


def check_c0_exact(entry):
    if entry["measurement"] is None or not np.array_equal(entry["T"],entry["measurement"]):
        raise ValueError("JTE071_ZERO_BIAS_IDENTITY_FAIL")
    return True


def check_c1_single_channel(entry, expected_bias_K=-2):
    M=entry["measurement"]
    if M is None:raise ValueError("JTE071_C1_MEAS_MISSING")
    delta=M-entry["T"]
    changed=np.flatnonzero(np.max(np.abs(delta),axis=0)>1e-9)
    if len(changed)!=1:
        raise ValueError("JTE071_NOT_EXACT_ONE_CHANNEL")
    j=int(changed[0])
    if not np.allclose(delta[:,j],expected_bias_K,atol=1e-9,rtol=0) or np.any(delta[:,np.arange(312)!=j]!=0):
        raise ValueError("JTE071_C1_BIAS_MISMATCH")
    Tmax=entry["T"].max(axis=1)
    Mmax=M.max(axis=1)
    loss=Tmax-Mmax
    if np.any(loss < -1e-10) or np.any(loss>abs(expected_bias_K)+1e-10):
        raise ValueError("JTE071_MAX_SELECTOR_BOUNDS")
    return {"channel_1based":j+1, "max_selector_loss_K":float(loss.max()),
            "selector_exposed_sample_fraction":float(np.mean(loss>1e-10))}


def exact_matched_pair(a,b):
    if not np.array_equal(a["time"],b["time"]):
        raise ValueError("JTE071_BASELINE_STUDY_CLOCKS_DIFFER")
    return dict(max_abs_temperature_K=float(np.max(np.abs(a["T"]-b["T"]))),
      max_abs_core=float(np.max(np.abs(a["u"]-b["u"]))),
      max_abs_postfilter=float(np.max(np.abs(a["flow"]-b["flow"]))))


def solver_surrogate(a,b):
    """Declaration: interpolation of native traces, NOT native event times."""
    t1=a["time"];t2=b["time"]
    if np.any(np.diff(t1)<=0) or np.any(np.diff(t2)<=0):
        raise ValueError("JTE071_DUPLICATE_SOLVER_TIMES_REQUIRE_SIDE_AWARE_POLICY")
    grid=np.union1d(t1,t2)
    if grid[0]!=0 or abs(grid[-1]-2400)>1e-8:
        raise ValueError("JTE071_BAD_SOLVER_GRID")
    result={}
    for name in ("maxT","command","postfilter"):
        if name=="maxT":x=np.max(a["T"],axis=1);y=np.max(b["T"],axis=1);ta=t1;tb=t2
        elif name=="command":x=a["u"];y=b["u"];ta=a["tc"];tb=b["tc"]
        else:x=a["flow"];y=b["flow"];ta=a["tf"];tb=b["tf"]
        if len(ta)!=len(x) or len(tb)!=len(y) or np.any(np.diff(ta)<=0) or np.any(np.diff(tb)<=0):
            raise ValueError("JTE071_NONSTRICT_CONTROL_TIMES")
        evalgrid=np.union1d(ta,tb)
        diff=np.interp(evalgrid,ta,x)-np.interp(evalgrid,tb,y)
        result[name]={"max_abs":float(np.max(np.abs(diff))),
          "trapezoidal_RMSE":float(np.sqrt(np.trapezoid(diff**2,evalgrid)/(evalgrid[-1]-evalgrid[0])))}
    result["method"]="LINEAR_UNION_GRID_INTERPOLANT_ONLY_NOT_EVENT_ERROR"
    return result


def report_internal(paths):
    """Returns Python values only: user explicitly prohibited report export."""
    loaded={k:audit_base(v) for k,v in paths.items()}
    required={"B0L_original","C0_original","B0L_fine","C0_fine"}
    if not required.issubset(loaded):raise ValueError("JTE071_FOUR_G5_CASES_REQUIRED")
    for k in ("C0_original","C0_fine"):check_c0_exact(loaded[k])
    paired={p:exact_matched_pair(loaded["B0L_"+p],loaded["C0_"+p]) for p in ("original","fine")}
    numerical={c:solver_surrogate(loaded[c+"_original"],loaded[c+"_fine"]) for c in ("B0L","C0")}
    return {"pair":paired,"solver_surrogate":numerical,
      "native_coverage":{k:v["count"] for k,v in loaded.items()},
      "scope":"AGGREGATE_AUDIT_ONLY_NO_G5_PASS"}
