"""JTE110 independent first-order filter canary. SYNTHETIC ONLY; not G5 acceptance.

For an independently VERIFIED accepted right-continuous ZOH event sequence, u[i]
applies on [t[i],t[i+1]); repeated times cause zero physical evolution.
This code MUST NOT infer event semantics from ordinary Simulink native logs.
Source H(s)=1/(tau*s+1), tau=.001s; command is dimensionless.
"""
from __future__ import annotations
import argparse
import math
from collections.abc import Sequence

TAU_SOURCE_S = 0.001
MAXSTEP_SOURCE_S = 0.05

def _check(t: Sequence[float], u: Sequence[float], y0: float, tau: float) -> None:
    if not (math.isfinite(tau) and tau > 0 and math.isfinite(y0)):
        raise ValueError("Invalid tau or physical initial output")
    if len(t) != len(u) or len(t) < 2:
        raise ValueError("Clock/command lengths must match and be >=2")
    if not all(math.isfinite(float(z)) for z in t) or not all(math.isfinite(float(z)) for z in u):
        raise ValueError("Nonfinite sample")
    if any(t[k+1] < t[k] for k in range(len(t)-1)):
        raise ValueError("Timestamps must not decrease")

def exact_zoh(t: Sequence[float], u: Sequence[float], y0: float,
              tau: float = TAU_SOURCE_S) -> list[float]:
    """Exact continuous ODE under CERTIFIED ZOH input, not a Simulink trace oracle."""
    _check(t, u, y0, tau)
    y = [float(y0)]
    for k in range(len(t)-1):
        h = float(t[k+1]-t[k])
        y.append(y[-1] + (float(u[k])-y[-1])*(-math.expm1(-h/tau)))
    return y

def trapezoidal_zoh(t: Sequence[float], u: Sequence[float], y0: float,
                    tau: float = TAU_SOURCE_S) -> list[float]:
    """TR canary only; not a reproduction of Simulink ode23t event/step logic."""
    _check(t, u, y0, tau)
    y = [float(y0)]
    for k in range(len(t)-1):
        z = float(t[k+1]-t[k])/tau
        r = (1-z/2)/(1+z/2)
        y.append(float(u[k])+r*(y[-1]-float(u[k])))
    return y

def backward_euler_zoh(t: Sequence[float], u: Sequence[float], y0: float,
                       tau: float = TAU_SOURCE_S) -> list[float]:
    """L-stable single-step comparison, not a battery-plant run."""
    _check(t, u, y0, tau)
    y = [float(y0)]
    for k in range(len(t)-1):
        z = float(t[k+1]-t[k])/tau
        y.append(float(u[k])+(y[-1]-float(u[k]))/(1+z))
    return y

def damping_factor(h: float, tau: float = TAU_SOURCE_S) -> float:
    if not(math.isfinite(h) and h >= 0 and math.isfinite(tau) and tau>0):
        raise ValueError("Invalid h/tau")
    z=h/tau
    return (1-z/2)/(1+z/2)

def require_same_native_clock(t0: Sequence[float], t1: Sequence[float]) -> None:
    """Reject unequal/duplicated clock mismatch instead of interpolating events."""
    if len(t0)!=len(t1) or any(a!=b for a,b in zip(t0,t1)):
        raise ValueError("Pointwise C1/C0 comparison needs an identical native clock")

def self_test() -> int:
    names=[]
    def chk(name: str, ok: bool) -> None:
        assert ok, name
        names.append(name)
    chk("trapezoidal_factor", abs(damping_factor(.05)+12/13)<1e-13)
    chk("negative_factor_h_gt_2tau", damping_factor(.05)<0)
    chk("positive_factor_h_lt_2tau", damping_factor(.001)>0)
    t=[0.,.05,.1]
    u=[.25]*3
    chk("exact_equilibrium", exact_zoh(t,u,.25)==u)
    chk("trapezoidal_equilibrium", trapezoidal_zoh(t,u,.25)==u)
    chk("backward_euler_equilibrium", backward_euler_zoh(t,u,.25)==u)
    chk("trap_overshoots", trapezoidal_zoh(t,u,.5)[1]<.25)
    chk("exact_monotonic", .25<=exact_zoh(t,u,.5)[1]<.5)
    chk("BE_monotonic", .25<backward_euler_zoh(t,u,.5)[1]<.5)
    chk("tiny_step", exact_zoh([0.,1e-12,2e-12],[.75]*3,.25)[1]>.25)
    td=[0.,.5,.5,.5001]; ud=[.25,.25,.75,.75]
    yd=exact_zoh(td,ud,.25)
    chk("duplicate_no_state_reset", yd[1]==yd[2])
    chk("switch_after_duplicate", yd[3]>yd[2])
    require_same_native_clock(td,td[:]);chk("identical_clock", True)
    try:require_same_native_clock([0,1],[0,1.00001])
    except ValueError:chk("unequal_clock_rejected",True)
    else:raise AssertionError("Unequal clocks accepted")
    try:exact_zoh([1,0],[.25,.25],.25)
    except ValueError:chk("reverse_time_rejected",True)
    else:raise AssertionError("Reverse time accepted")
    try:exact_zoh([0,float("nan")],[.25,.25],.25)
    except ValueError:chk("nan_rejected",True)
    else:raise AssertionError("NaN accepted")
    print(f"JTE110_SYNTHETIC_FILTER_CANARY_PASS checks={len(names)} "
          f"factor={damping_factor(.05):.12f} studyMAT=NOT_USED "
          f"MATLAB=NOT_RUN G5_ACCEPTED=FALSE")
    return len(names)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    args=p.parse_args()
    if not args.self_test:p.error("Only synthetic --self-test is enabled")
    self_test()
