"""Independent Decimal ZOH oracle against actual single MATLAB toy; no simulation."""
import json,os
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from sampled_actuator_review_io import ROOT
def D(x):return Decimal.from_float(float(x))
def require(ok,code):
    if not ok:raise RuntimeError(code)
def branch(pre,b):
    s=b["spec"];ident=s["id"];a=D(s["A"]);bb=D(s["B"]);Ts=D(s["Ts_s"]);x0=D(s["x0"])
    data=np.loadtxt(str(pre)+"_"+ident+"_DENSE.csv",delimiter=",",ndmin=2)
    ticks=np.loadtxt(str(pre)+"_"+ident+"_TICKS.csv",delimiter=",",ndmin=2)
    require(data.shape[1]==4 and ticks.shape[1]==6 and np.isfinite(data).all() and np.isfinite(ticks).all(),"TOY_ACTUAL_STATE_OR_TRACE_NOT_QUALIFIED")
    t,raw,held,y=data.T;N=len(ticks);tol=32*np.spacing(1.0)
    require(np.all(np.diff(t)>0) and t[0]==0 and abs(t[-1]-.12)<=tol,"TOY_DENSE_CLOCK")
    require(np.array_equal(ticks[:,0],np.arange(N)) and np.all(np.abs(ticks[:,1]-np.arange(N)*float(Ts))<=tol),"TOY_TICK_CLOCK")
    expected=np.asarray(s["inputValues"],dtype=float).reshape(-1)
    require(len(expected)==len(raw) and np.array_equal(expected,raw),"TOY_SOURCE_DISCONTINUITY_INPUT")
    sample_idx=np.rint(np.arange(N+1)*float(Ts)/.00025).astype(int)
    require(np.max(np.abs(t[sample_idx]-np.arange(N+1)*float(Ts)))<=tol,"TOY_SOURCE_SAMPLE_PHASE")
    require(np.array_equal(ticks[:,2],held[sample_idx[:-1]]) and np.array_equal(ticks[:,2],raw[sample_idx[:-1]]),"TOY_ZOH_AT_HITS")
    with localcontext() as c:
        c.prec=80
        Tnom=Decimal("0.01") if s["Ts_s"]==.01 else Decimal("0.005")
        ae=(-Tnom/Decimal(".001")).exp();be=1-ae
        unit=Decimal(2)**-53;gamma3=3*unit/(1-3*unit)
        exact=x0;E=Decimal(0);ex=[exact];err=[E];observed=[]
        max_err=Decimal(0);max_hold=Decimal(0)
        require(ticks[0,3]==s["x0"],"TOY_ARCHIVED_OR_SYNTHETIC_INITIAL_STATE")
        for k,row in enumerate(ticks):
            u,prex,post,out=map(D,row[2:6])
            require(out==prex,"TOY_D0_OUTPUT_STAGING")
            require(abs(prex-exact)<=E+Decimal("1e-65"),"TOY_EXACT_ZOH_PRESTATE")
            local=gamma3*(abs(a*prex)+abs(bb*u))
            require(abs(post-(a*prex+bb*u))<=local+Decimal("1e-65"),"TOY_LOCAL_DOUBLE_RECURRENCE")
            require(min(prex,u)-local<=post<=max(prex,u)+local,"TOY_DISCRETE_CONVEX_BOUND")
            nxt=ae*exact+be*u
            En=abs(a)*E+abs(a-ae)*abs(exact)+abs(bb-be)*abs(u)+local+Decimal("1e-65")
            require(abs(post-nxt)<=En,"TOY_EXACT_ZOH_POSTSTATE")
            if k+1<N:require(post==D(ticks[k+1,3]),"TOY_POST_TO_NEXT_PRE_CONTINUITY")
            max_err=max(max_err,abs(prex-exact),abs(post-nxt))
            exact,E=nxt,En;ex.append(exact);err.append(E);observed.append(float(prex))
        observed.append(float(ticks[-1,4]))
        ki=np.rint(t/.00025).astype(int)//round(float(Ts)/.00025)
        require(np.all(ki<=N) and np.array_equal(y,np.asarray(observed)[ki]),"TOY_OUTPUT_HOLD")
        expected_held=np.asarray(raw[sample_idx])[ki]
        require(np.array_equal(held,expected_held),"TOY_COMMAND_HOLD")
        continuous=[]
        for ti,kk in zip(t,ki):
            if kk==N:val=ex[N]
            else:
                elapsed=D(ti)-D(t[sample_idx[kk]])
                val=D(ticks[kk,2])+(ex[kk]-D(ticks[kk,2]))*(-elapsed/Decimal(".001")).exp()
            continuous.append(float(val));max_hold=max(max_hold,abs(val-D(y[len(continuous)-1])))
        oracle=np.column_stack((t,np.asarray(continuous),y,np.asarray(continuous)-y))
        np.savetxt(str(pre)+"_"+ident+"_INDEPENDENT_ORACLE.csv",oracle,delimiter=",",fmt="%.17g")
        if s["pattern"]=="MISSED_TWO_MS_PULSE":
            require(np.any(raw==.5) and np.all(held==.25) and np.all(y==.25),"TOY_SUB_TS_PULSE_MISSED")
        if s["pattern"]=="CAPTURED_TEN_MS_PULSE":require(np.any(ticks[:,2]==.5),"TOY_PULSE_NOT_CAPTURED")
        if s["pattern"]=="TWO_STEP_AND_RETURN":require(set(ticks[:,2])=={.25,.5,.75},"TOY_TWO_STEP_INPUT")
        return {"id":ident,"Ts_s":s["Ts_s"],"pattern":s["pattern"],"PASS":True,"maximumExactOracleError":str(max_err),
          "maximumDenseHoldVsContinuousOracleDiscrepancy":str(max_hold),
          "arithmeticRule":"gamma3 local two products+addition; coefficient representation discrepancy separately propagated",
          "clockRule":"Pure fixed-grid toy method phases, never a battery accepted-step certificate"}
def main():
    pre=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_TOY")
    summary=json.loads(Path(str(pre)+"_SUMMARY.json").read_text())
    report={"scope":"One actual MATLAB toy independent Decimal oracle; no extra trajectory","branches":[],"physicalSimulation":False,"G5Accepted":False}
    if not(summary["flags"]["MATLAB_TOY_COMPLETE"] and summary["flags"]["ACTUAL_PRE_POST_STATE_AVAILABLE"] and summary["flags"]["MATLAB_PHASE_CHECKS"]):
        report["status"]="UNQUALIFIED_TOY_CLOCK_OR_STATE";report["MATLABSummary"]=summary
    else:
        try:
            require(summary["simCount"]==1 and len(summary["branches"])==8,"TOY_SINGLE_TRAJECTORY_SCOPE")
            report["branches"]=[branch(pre,b) for b in summary["branches"]]
            report["status"]="PASS_DISCRETE_TOY_SEMANTICS_ONLY"
        except Exception as e:
            report["status"]="FAIL_INDEPENDENT_TOY_CHECK";report["privateFailure"]=str(e)
    p=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_TOY_INDEPENDENT_REVIEW.json")
    p.write_text(json.dumps(report,indent=2,allow_nan=False))
    print("SAMPLED_TOY_INDEPENDENT_STATUS="+report["status"]+" noSecondToy=1 batteryRun=0 G5_ACCEPTED=false")
if __name__=="__main__":
    try:main()
    except Exception as e:
        p=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_TOY_CHECK_UNAVAILABLE.json")
        p.write_text(json.dumps({"status":"UNAVAILABLE_CHECK_INPUT","exception":type(e).__name__,"physicalSimulation":False,"G5Accepted":False}))
        print("SAMPLED_TOY_INDEPENDENT_STATUS=UNAVAILABLE_CHECK_INPUT batteryRun=0 G5_ACCEPTED=false")
