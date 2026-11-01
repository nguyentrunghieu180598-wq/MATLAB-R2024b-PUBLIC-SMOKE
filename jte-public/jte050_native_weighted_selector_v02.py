"""JTE-050/054 original pre-registration: native-time-weighted mean, not v01 max.
Synthetic-only analysis helper; NO source-BTMS MATLAB run and NO G5 certification.
Select hot(rank1), middle(rank156), cold(rank312) on native T312 in [1800,2400]s.
Preserves double-sided identical event timestamps; do not deduplicate rows.
Event-preserving trapezoid convention must be cross-checked with archived
JTE050_selectNativeChannels.m before full physical baseline channel selection.
Requires explicit native samples at 1800 and 2400; fails closed otherwise.
"""
from dataclasses import dataclass
import numpy as np

N=312
START,END=1800.0,2400.0

@dataclass(frozen=True)
class Selection:
    hot_1based:int
    mid_1based:int
    cold_1based:int
    sample_count:int
    duplicate_rows:int
    mean_spread_K:float
    state:str="PROTOCOL_CANDIDATE_G5_NOT_ACCEPTED"

def select_native_weighted_mean(T_K,t_s):
    T=np.asarray(T_K,dtype=float)
    t=np.asarray(t_s,dtype=float)
    if T.ndim!=2 or T.shape[1]!=N or t.ndim!=1 or len(t)!=len(T) or len(t)<2:
        raise ValueError("INVALID_NATIVE_312_SHAPE")
    if not np.isfinite(T).all() or not np.isfinite(t).all() or np.any(np.diff(t)<0):
        raise ValueError("INVALID_NATIVE_CLOCK_OR_VALUES")
    if not np.any(t==START) or not np.any(t==END):
        raise ValueError("NATIVE_BOUNDARY_SAMPLE_NOT_OBSERVED")
    keep=(t>=START)&(t<=END)
    w=t[keep]
    z=T[keep]
    if w[0]!=START or w[-1]!=END or len(np.unique(w))<2:
        raise ValueError("INCOMPLETE_1800_TO_2400_WINDOW")
    dt=np.diff(w)
    # Two samples at the same event time contribute zero width while
    # preserving the before-event and after-event sides on adjacent intervals.
    score=np.sum(0.5*(z[:-1]+z[1:])*dt[:,None],axis=0)/(END-START)
    if not np.isfinite(score).all() or np.all(score==score[0]):
        raise ValueError("UNRANKABLE_BASELINE_MEAN")
    ids=np.arange(1,N+1)
    order=np.lexsort((ids,-score))
    return Selection(int(ids[order[0]]),int(ids[order[155]]),
                     int(ids[order[-1]]),len(w),len(w)-len(np.unique(w)),
                     float(score.max()-score.min()))

def selftest():
    t=np.array([0.,1800.,1900.,1900.,2000.,2400.])
    T=np.tile(300.+.001*np.arange(N),(len(t),1))
    T[:,0]=300.01
    T[2,0]=400.0  # highest instantaneous peak, NOT highest weighted mean
    T[:,1]=310.0
    r=select_native_weighted_mean(T,t)
    assert (r.hot_1based,r.mid_1based,r.cold_1based)==(2,159,3),r
    assert r.duplicate_rows==1 and r.sample_count==5
    for invalid_T,invalid_t in ((T,t[::-1]),(T[:,:2],t),
                                 (T[t!=2400.],t[t!=2400.]),
                                 (np.full_like(T,300.),t)):
        try:
            select_native_weighted_mean(invalid_T,invalid_t)
        except ValueError:
            pass
        else:
            raise AssertionError("FAIL_CLOSED_REGRESSION")
    print("JTE050_NATIVE_TIME_WEIGHTED_MEAN_SYNTHETIC_PASS; MATLAB_RUN=0; G5=false")

if __name__=="__main__":
    selftest()
