"""Independent actual-event Decimal checks; original dense-clock failure remains."""
import json,os,math
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from sampled_actuator_review_io import ROOT
def need(x,s):
    if not x:raise RuntimeError(s)
def D(x):return Decimal.from_float(float(x))
def scalar(x):
    if isinstance(x,list):
        need(len(x)==1,"ACTUAL_STATE_NOT_SCALAR");return float(x[0])
    return float(x)
def audit(j,s,events,pre):
    ev=[x for x in events if x["branch"]==j]
    Ts=float(s["Ts_s"]);N=round(.12/Ts);tol=32*np.spacing(1.0)
    phases={}
    for p in ("PostOutputs","PreUpdate","PostUpdate"):
        a=[x for x in ev if x["phase"]==p]
        need(len(a)==N+1,"EVENT_PHASE_COUNT")
        need(all(abs(e["time_s"]-k*Ts)<=tol for k,e in enumerate(a)),"EVENT_PHASE_CLOCK")
        need(all(x["actualStateReadable"] and x["NumDworks"]==1 for x in a),"ACTUAL_STATE_UNAVAILABLE")
        phases[p]=a
    rows=[];input_times=np.asarray(s["inputTimes"],dtype=float);input_values=np.asarray(s["inputValues"],dtype=float)
    with localcontext() as c:
        c.prec=80;ae=(-(Decimal(".01") if Ts==.01 else Decimal(".005"))/Decimal(".001")).exp();be=1-ae
        a,b=D(s["A"]),D(s["B"]);gamma=3*(Decimal(2)**-53)/(1-3*(Decimal(2)**-53))
        exact=D(s["x0"]);E=Decimal(0);peak=Decimal(0)
        for k in range(N+1):
            po,pu,qu=[phases[p][k] for p in ("PostOutputs","PreUpdate","PostUpdate")]
            need(po["sequence"]<pu["sequence"]<qu["sequence"],"EVENT_ORDER")
            x,y,xn,u=map(D,(scalar(pu["actualDState"]),scalar(po["output"]),scalar(qu["actualDState"]),scalar(pu["heldInput"])))
            need(x==D(scalar(po["actualDState"])) and y==x and D(scalar(qu["output"]))==y and D(scalar(qu["heldInput"]))==u,"D0_PRE_POST_STAGING")
            ix=np.searchsorted(input_times,pu["time_s"],side="right")-1
            need(ix>=0 and u==D(input_values[ix]),"SOURCE_INPUT_NATIVE_PHASE")
            need(abs(x-exact)<=E+Decimal("1e-65"),"EXACT_ZOH_PRESTATE")
            local=gamma*(abs(a*x)+abs(b*u))
            need(abs(xn-(a*x+b*u))<=local+Decimal("1e-65"),"DOUBLE_RECURRENCE")
            need(min(x,u)-local<=xn<=max(x,u)+local,"CONVEX_BOUND")
            nxt=ae*exact+be*u;En=abs(a)*E+abs(a-ae)*abs(exact)+abs(b-be)*abs(u)+local+Decimal("1e-65")
            need(abs(xn-nxt)<=En,"EXACT_ZOH_POSTSTATE")
            if k<N:need(xn==D(scalar(phases["PreUpdate"][k+1]["actualDState"])),"NEXT_PRESTATE_CONTINUITY")
            peak=max(peak,abs(x-exact),abs(xn-nxt))
            rows.append([k,pu["time_s"],float(u),float(x),float(xn),float(y)])
            exact,E=nxt,En
        native=np.asarray(rows)
    np.savetxt(str(pre)+"_"+s["id"]+"_ACTUAL_TICKS.csv",native,delimiter=",",fmt="%.17g")
    # Compare each observer on ITS OWN original clock. No common-grid fabrication.
    obs={};event_times=np.asarray([x["time_s"] for x in phases["PostOutputs"]])
    vals=np.asarray([scalar(x["output"]) for x in phases["PostOutputs"]])
    for signal in ("raw","hold","actuator"):
        z=np.loadtxt(str(pre)+"_"+s["id"]+"_"+signal+".csv",delimiter=",",ndmin=2)
        out={"nativeRows":len(z),"clockStart_s":float(z[0,0]),"clockEnd_s":float(z[-1,0])}
        if signal=="actuator":
            ix=np.searchsorted(event_times,z[:,0],side="right")-1
            good=ix>=0;out["matchesLastActualOutputWrite"]=bool(np.all(good) and np.array_equal(z[:,1],vals[np.maximum(ix,0)]))
            gap=np.min(abs(z[:,0,None]-event_times[None,:]),axis=1)
            out["betweenHitObservationPresent"]=bool(np.any(gap>tol))
        obs[signal]=out
    return {"branch":j,"id":s["id"],"Ts_s":Ts,"pattern":s["pattern"],"nativeTickMath":"PASS",
      "maximumIndependentExactOracleError":str(peak),"nativeObservers":obs,
      "fullToyAccepted":False,"scope":"Native method-phase/recurrence evidence only. Original identical-dense-clock gate not reclassified.",
      "roundoff":"gamma3 local, coefficient representation discrepancy propagated separately, not physical acceptance tolerance."}
def main():
    pre=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_NATIVE")
    summary=json.load(open(ROOT/"toy_summary.json"));events=json.load(open(ROOT/"toy_events.json"));reports=[]
    for j,s in enumerate(summary["specs"],1):
        try:reports.append(audit(j,s,events,pre))
        except Exception as e:reports.append({"branch":j,"id":s["id"],"nativeTickMath":"UNQUALIFIED","reason":str(e),"fullToyAccepted":False})
    r={"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"sourceRun":"40683965769","branches":reports,
      "status":"NATIVE_TICK_PARTIAL_EVIDENCE_ONLY","originalDenseClockGate":"UNQUALIFIED_UNCHANGED",
      "newSimulation":False,"fullToyAccepted":False,"G5Accepted":False}
    p=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_NATIVE_PARTIAL_REVIEW.json")
    p.write_text(json.dumps(r,indent=2,allow_nan=False))
    print("SAVED_TOY_NATIVE_REVIEW_COMPLETE nativeTickBranchesQualified="+str(sum(x["nativeTickMath"]=="PASS" for x in reports))+" fullToyAccepted=0 newSimulation=0 G5_ACCEPTED=false")
if __name__=="__main__":main()
