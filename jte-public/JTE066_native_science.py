"""JTE066 native G5 verification, G6 fixed-channel preregistration.

Works on owner-private MATs after they are independently read back; this
module contains NO study results, raw numeric thresholds or paper drafts.
Never automatically accepts G5. Temperature is K; core command unitless.
"""
from pathlib import Path
import hashlib
import h5py
import numpy as np

NCHANNELS=312
HORIZON_S=2400.
CASES={"B0L_original","C0_original","B0L_fine","C0_fine"}


def _txt(data):
    arr=np.asarray(data).reshape(-1)
    return "".join(chr(int(x)) for x in arr)


def _signal(data,name):
    g=data["signalData"][name]
    t=np.asarray(g["time_s"]).reshape(-1).astype(np.float64)
    v=np.asarray(g["values"]).T.astype(np.float64)
    if not (np.all(np.isfinite(t)) and np.all(np.isfinite(v))):
        raise ValueError("JTE066_NONFINITE_"+name)
    if len(t)!=len(v) or len(t)==0 or np.any(np.diff(t)<0):
        raise ValueError("JTE066_BAD_NATIVE_CLOCK_"+name)
    return t,v


def read_case(path,expected):
    """Return only in-memory scientific tensors; never print or publish them."""
    if expected not in CASES: raise ValueError("JTE066_BAD_CASE")
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise ValueError("JTE066_MAT_NOT_FOUND")
    with p.open("rb") as fh: sha=hashlib.file_digest(fh,"sha256").hexdigest()
    with h5py.File(p,"r") as mat:
        r=mat["record"]
        if _txt(r["caseName"])!=expected:
            raise ValueError("JTE066_WRONG_CASE_RECEIPT")
        if _txt(r["sourceSHA256"])!="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0":
            raise ValueError("JTE066_SOURCE_SHA_MISMATCH")
        if _txt(r["dataUse"])!="REAL_R2024B_G5_RAW_UNREVIEWED_NOT_ACCEPTED":
            raise ValueError("JTE066_NOT_RAW_STUDY")
        t,T=_signal(r,"jteTtrue")
        if T.shape!=(len(t),NCHANNELS):raise ValueError("JTE066_NOT_312_CHANNELS")
        if not (t[0]==0 and abs(t[-1]-HORIZON_S)<1e-8):
            raise ValueError("JTE066_HORIZON")
        tmin,R=_signal(r,"jteTminTrue")
        tmax,M=_signal(r,"jteTmaxTrue")
        if not (np.array_equal(t,tmin) and np.array_equal(t,tmax)
                and R.shape==(len(t),2) and M.shape==(len(t),1)
                and np.array_equal(R[:,0],np.min(T,axis=1))
                and np.array_equal(R[:,1],np.max(T,axis=1))
                and np.array_equal(M[:,0],np.max(T,axis=1))):
            raise ValueError("JTE066_REDUCER_MISMATCH")
        if expected.startswith("C0"):
            tm,meas=_signal(r,"jteTmeas")
            if not (np.array_equal(tm,t) and np.array_equal(meas,T)):
                raise ValueError("JTE066_C0_ZERO_BIAS_MISMATCH")
        u_t,u=_signal(r,"jteUcore")
        flow_t,flow=_signal(r,"jteFlwR")
        if u.shape[1]!=1 or flow.shape[1]!=1:
            raise ValueError("JTE066_COMMAND_CHANNELS")
        if not np.all((u>=-1e-8)&(u<=1+1e-8)) or not np.all((flow>=-1e-8)&(flow<=1+1e-8)):
            raise ValueError("JTE066_COMMAND_UNIT_INTERVAL")
        return {"case":expected,"source_sha":_txt(r["sourceSHA256"]),
            "load_sha":_txt(r["load"]["SHA256"]),
            "solver_name":_txt(r["solver"]["Solver"]),
            "solver_reltol":_txt(r["solver"]["RelTol"]),
            "solver_abstol":_txt(r["solver"]["AbsTol"]),
            "solver_maxstep":_txt(r["solver"]["MaxStep"]),
            "sha256":sha,"time":t,"T_K":T,
            "u_t":u_t,"u":u[:,0],"flow_t":flow_t,"flow":flow[:,0],
            "status":"RAW_UNREVIEWED"}


def select_g6_channels(reference):
    """Predeclared hot/median/cold: time-weighted mean over entire C0-original.

    Use ONLY C0_original, not G6 outcomes. Tie-break smaller 1-based index.
    -2K is a fixed *study perturbation*, NOT a proven sensor datasheet bound.
    """
    if reference.get("case")!="C0_original":
        raise ValueError("JTE066_G6_SELECTION_ONLY_C0_ORIGINAL")
    t=np.asarray(reference["time"])
    T=np.asarray(reference["T_K"])
    if T.shape!=(len(t),NCHANNELS) or len(t)<2 or t[0]!=0 or abs(t[-1]-HORIZON_S)>1e-8 or np.any(np.diff(t)<0):
        raise ValueError("JTE066_G6_REFERENCE_INVALID")
    means=np.trapezoid(T,x=t,axis=0)/HORIZON_S
    if not np.all(np.isfinite(means)):raise ValueError("JTE066_G6_NONFINITE")
    ids=np.arange(1,NCHANNELS+1)
    rank=np.lexsort((ids,means))
    selected={"cold":int(ids[rank[0]]),"middle":int(ids[rank[(NCHANNELS-1)//2]]),
              "hot":int(ids[rank[-1]])}
    if len(set(selected.values()))!=3:raise ValueError("JTE066_NON_DISTINCT_CHANNELS")
    return selected


def thermal_duplicate_diagnostics(case):
    t=case["time"];T=case["T_K"]
    ix=np.flatnonzero(np.diff(t)==0)
    if not len(ix):return {"duplicate_pairs":0,"max_duplicate_jump_K":0.}
    return {"duplicate_pairs":int(len(ix)),
            "max_duplicate_jump_K":float(np.max(np.abs(T[ix+1]-T[ix])))}


def interpolate_temperature(case,target_t):
    """Continuous thermal interpolation only; never use for discrete core command.

    Duplicate native timestamps with distinct temperatures must be reviewed,
    rather than silently sorted or deduplicated.
    """
    t=case["time"];T=case["T_K"]
    d=thermal_duplicate_diagnostics(case)
    if d["max_duplicate_jump_K"]>0.:
        raise ValueError("JTE066_THERMAL_MULTIVALUED_DUPLICATE")
    unique=np.r_[True,np.diff(t)>0]
    tx=t[unique];X=T[unique]
    if len(tx)<2 or target_t[0]<tx[0] or target_t[-1]>tx[-1]:
        raise ValueError("JTE066_INTERPOLATION_EXTRAPOLATION")
    return tx,X


def compare_native_temperatures(a,b):
    """Numerical resolution check on UNION OF ALL RECORDED thermal samples.

    No unobserved-event guarantee. No tolerance is silently selected.
    """
    if a["source_sha"]!=b["source_sha"] or a["load_sha"]!=b["load_sha"]:
        raise ValueError("JTE066_SOURCE_OR_LOAD_MISMATCH")
    union=np.union1d(a["time"],b["time"])
    ta,xa=interpolate_temperature(a,union)
    tb,xb=interpolate_temperature(b,union)
    sumsq=0.; maxerr=0.
    for col in range(NCHANNELS):
        aa=np.interp(union,ta,xa[:,col])
        bb=np.interp(union,tb,xb[:,col])
        diff=aa-bb
        sumsq+=float(np.dot(diff,diff))
        maxerr=max(maxerr,float(np.max(np.abs(diff))))
    return {"max_abs_T_K":maxerr,"rmse_T_K":float(np.sqrt(sumsq/(len(union)*NCHANNELS))),
            "common_union_samples":len(union),
            "interpolation":"piecewise linear TEMP only; not exact physical event times",
            "review_status":"NUMERIC_EVIDENCE_ONLY_NO_AUTO_PASS"}


def prerequisite_status(four):
    if set(four)!=CASES:raise ValueError("JTE066_MISSING_G5_CASES")
    base=four["B0L_original"]
    for c in four.values():
        if c["source_sha"]!=base["source_sha"] or c["load_sha"]!=base["load_sha"]:
            raise ValueError("JTE066_G5_PROVENANCE_MISMATCH")
    return {"B0L_C0_original":compare_native_temperatures(four["B0L_original"],four["C0_original"]),
            "B0L_C0_fine":compare_native_temperatures(four["B0L_fine"],four["C0_fine"]),
            "B0L_original_fine":compare_native_temperatures(four["B0L_original"],four["B0L_fine"]),
            "C0_original_fine":compare_native_temperatures(four["C0_original"],four["C0_fine"]),
            "G5_PASS":False,"needs_independent_review":True}
