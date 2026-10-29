"""Private native-record audit. No MATLAB, sim(), interpolation or physical acceptance claim."""
import hashlib,json,os,re,sys,csv
from pathlib import Path
import h5py,numpy as np
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
WINDOWS={"FIRST":(330.,338.),"SECOND":(2000.,2400.)}
FLAG=.005 # localization ONLY, never a scientific acceptance tolerance
ULPS=64    # floating point diagnostic budget, not engineering thermal tolerance
def require(v,c):
    if not v:raise RuntimeError(c)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(8*1024**2),b""):h.update(b)
    return h.hexdigest()
def unwrap(f,n):
    while isinstance(n,h5py.Dataset) and h5py.check_dtype(ref=n.dtype) is not None and n.size==1:
        r=n[()].reshape(-1)[0];require(bool(r),"JTE102_EMPTY_REFERENCE");n=f[r]
    return n
def node(f,path):
    n=f
    for key in path.split("/"):
        n=unwrap(f,n);n=n[key]
    return unwrap(f,n)
def decode(f,n,depth=0):
    require(depth<20,"JTE102_METADATA_DEPTH")
    n=unwrap(f,n)
    if isinstance(n,h5py.Group):
        return {k:decode(f,n[k],depth+1) for k in n.keys() if not k.startswith("#")}
    cls=n.attrs.get("MATLAB_class",b"")
    if isinstance(cls,bytes):cls=cls.decode()
    if n.attrs.get("MATLAB_empty",0):return "" if cls=="char" else []
    a=n[()]
    if cls=="char":return "".join(chr(int(x)) for x in np.asarray(a).T.ravel(order="F") if x)
    if h5py.check_dtype(ref=n.dtype) is not None:
        ar=np.asarray(a).transpose()
        return [decode(f,f[r],depth+1) if r else None for r in ar.ravel(order="F")]
    a=np.asarray(a).transpose()
    if a.size==1:return a.reshape(-1)[0].item()
    return a
def read(f,path):return decode(f,node(f,path))
def num(f,path):
    n=node(f,path);require(isinstance(n,h5py.Dataset) and h5py.check_dtype(ref=n.dtype) is None,"JTE102_EXPECTED_NUMERIC")
    a=np.asarray(n[()],dtype=float).transpose()
    require(np.isfinite(a).all(),"JTE102_NONFINITE")
    return a
def vec(f,path):return num(f,path).reshape(-1,order="F")
def strings(v):
    if isinstance(v,str):return [v]
    if isinstance(v,(list,tuple)):return sum((strings(x) for x in v),[])
    if isinstance(v,np.ndarray):return sum((strings(x) for x in v.ravel(order="F")),[])
    raise RuntimeError("JTE102_CONFIG_NOT_STRING_CELLS")
def config(f,path):
    v=strings(read(f,path));require(len(v)%2==0,"JTE102_CONFIG_PAIR")
    n=len(v)//2;return dict(zip(v[:n],v[n:]))
def clock(t,h):
    require(t.ndim==1 and t.size>1 and t[0]==0 and t[-1]==h and (np.diff(t)>=0).all(),"JTE102_CLOCK")
def step_stats(t):
    dt=np.diff(t);p=dt[dt>0]
    return {"rows":len(t),"repeatAdjacentRows":int((dt==0).sum()),"minPositive_s":float(p.min()),"medianPositive_s":float(np.median(p)),"max_s":float(p.max()),"acceptedStepCertification":"UNAVAILABLE"}
def repeated(t,v):
    ix=np.flatnonzero(np.diff(t)==0)
    return {"adjacentRepeatCount":len(ix),"maxAdjacentValueChange":float(np.max(np.abs(v[ix+1]-v[ix]))) if len(ix) else 0.}
def matched(t,s):
    if np.array_equal(t,s):return np.arange(len(t)),np.arange(len(s)),True,0
    u,ix,c=np.unique(t,return_index=True,return_counts=True);v,jx,d=np.unique(s,return_index=True,return_counts=True)
    _,a,b=np.intersect1d(u,v,return_indices=True)
    left=[];right=[];ambiguous=0
    for k,z in zip(a,b):
        if c[k]!=d[z]:ambiguous+=1;continue
        left.extend(range(ix[k],ix[k]+c[k]));right.extend(range(jx[z],jx[z]+d[z]))
    return np.array(left,int),np.array(right,int),False,ambiguous
def comparison(a,b,field="T",window=None):
    ta=a["t"];tb=b["t"]
    i,j,exact,amb=matched(ta,tb)
    if window is not None:
        keep=(ta[i]>=window[0])&(ta[i]<=window[1]);i=i[keep];j=j[keep]
    if len(i)==0:
        return {"status":"UNAVAILABLE_NO_EXACT_COMMON_NATIVE_POINTS","clockExact":False,
          "ambiguousDuplicateGroupsExcludedFromPairing":amb,"matchedRows":0,"matchedFractionA":0.,"matchedFractionB":0.,
          "fullNativeVectorIdentity":False,"maxAbs":None,"sampleRMSE":None,"signedMin":None,"signedMax":None,
          "perChannelMaxAbs":None,"perChannelSampleRMSE":None,"roundoffDiagnosticBudget":None,
          "withinRoundoffOnMatchedPoints":False,"semantics":"No interpolation, no fabricated comparison on unmatched clocks."}
    x=a[field][i];y=b[field][j]
    diff=y-x;xx=np.asarray(diff).reshape(len(i),-1)
    scale=max(1.,float(np.max(np.abs(x))),float(np.max(np.abs(y))))
    rounding=ULPS*np.spacing(scale)
    return {"status":"EXACT_NATIVE_MATCHED_SUBSET","clockExact":exact,"ambiguousDuplicateGroupsExcludedFromPairing":amb,"matchedRows":len(i),
      "matchedFractionA":len(i)/len(ta),"matchedFractionB":len(j)/len(tb),"fullNativeVectorIdentity":exact and np.array_equal(a[field],b[field]),
      "maxAbs":float(np.max(np.abs(diff))),"sampleRMSE":float(np.sqrt(np.mean(diff**2))),"signedMin":float(np.min(diff)),"signedMax":float(np.max(diff)),
      "perChannelMaxAbs":np.max(np.abs(xx),axis=0),"perChannelSampleRMSE":np.sqrt(np.mean(xx**2,axis=0)),
      "roundoffDiagnosticBudget":float(rounding),"withinRoundoffOnMatchedPoints":bool(np.max(np.abs(diff))<=rounding),
      "semantics":"Exact time + equal duplicate multiplicity/order; no interpolation. Conditional sample contrast, not causal thermal effect or rigorous error bound."}
def event(t,y,u,T,window,state=None,C=None):
    w=(t>=window[0])&(t<=window[1]);ix=np.flatnonzero(w);require(len(ix)>1,"JTE102_EVENT_WINDOW_EMPTY")
    tt=t[ix];r=y[ix]-u[ix];dt=np.diff(tt);hit=np.abs(r)>FLAG
    # Every recorded interval retained. Duplicate timestamps have zero elapsed width.
    left=np.sum(dt*r[:-1]);right=np.sum(dt*r[1:])
    al=np.sum(dt*np.abs(r[:-1]));ar=np.sum(dt*np.abs(r[1:]))
    first=np.flatnonzero(hit);k=int(ix[first[0]]) if len(first) else None
    z={"windowRequested_s":window,"windowNativeCoverage_s":[float(tt[0]),float(tt[-1])],"sampleCount":len(tt),
       "flagThresholdNormalized":FLAG,"thresholdRole":"LOCALIZATION_NOT_ACCEPTANCE","excursion":bool(hit.any()),
       "postfilterMin":float(y[ix].min()),"postfilterMax":float(y[ix].max()),"residualPeakAbs":float(np.abs(r).max()),
       "residualMin":float(r.min()),"residualMax":float(r.max()),"signedArea_trapezoid_normalized_s":float((left+right)/2),
       "absoluteEndpointArea_trapezoid_normalized_s":float((al+ar)/2),"signedArea_left_right":[float(left),float(right)],
       "absoluteArea_left_right":[float(al),float(ar)],"exceedanceDuration_left_right_s":[float(np.sum(dt*hit[:-1])),float(np.sum(dt*hit[1:]))],
       "exceedanceIntervalUnion_s":float(np.sum(dt*(hit[:-1]|hit[1:]))),"exceedanceSamples":int(hit.sum()),
       "firstBracket_s":[float(t[k-1]),float(t[k])] if k is not None and k>0 else None,
       "repeatPostfilter":repeated(tt,y[ix]),"repeatThermal":repeated(tt,T[ix]),
       "thermalPerChannelNativeMin_K":T[ix].min(axis=0),"thermalPerChannelNativeMax_K":T[ix].max(axis=0),
       "thermalPerChannelEndMinusStart_K":T[ix[-1]]-T[ix[0]],
       "eventAreaSemantics":"Sample-path left/right/trapezoid quadratures, no accepted-step certification, no physical reset/event-duration inference. Endpoint absolute trapezoid does not reconstruct interior sign crossings."}
    if state is not None:
        z["repeatState"]=repeated(tt,state[ix])
        z["stateOutputResidualMax"]=float(np.abs(y[ix]-C*state[ix]).max())
        if k is not None and k>0:
            z["firstStateChange"]=float(state[k]-state[k-1])
            z["conditionalHeldInputResetFreeResidual"]=float(y[k]-(u[k]+(y[k-1]-u[k])*np.exp(-(t[k]-t[k-1])/.001)))
    return z
def load_case(path,key,manifest):
    m=next(x for x in manifest["files"] if x["local"]==path.name)
    require(sha(path)==m["sha256"],"JTE102_LOCAL_SHA")
    with h5py.File(path,"r") as f:
        old=key not in ("ORIGINAL340","CONSTANT340");r="record/"
        if old:
            require(read(f,r+"schema")=="JTE056_NATIVE_V1" and read(f,r+"caseName")==key,"JTE102_CASE")
            require("24.2.0.3361896" in read(f,r+"matlabVersion"),"JTE102_RUNTIME")
            require(read(f,r+"units/temperature")=="K" and read(f,r+"units/time")=="s","JTE102_UNITS")
            t=vec(f,r+"signalData/jteTtrue/time_s");T=num(f,r+"signalData/jteTtrue/values")
            tu=vec(f,r+"signalData/jteUcore/time_s");u=vec(f,r+"signalData/jteUcore/values")
            ty=vec(f,r+"signalData/jteFlwR/time_s");y=vec(f,r+"signalData/jteFlwR/values")
            meta={"sourceSHA":read(f,r+"sourceSHA256"),"loadSHA":read(f,r+"load/SHA256"),"modelSHA":read(f,r+"generatedModelSHA256"),
              "solver":read(f,r+"solver"),"units":read(f,r+"units"),"schema":read(f,r+"schema"),"TFstate":"ABSENT_IN_SOURCE_SCHEMA",
              "inputOverridesEncoding":"MATLAB objects retained in original MAT; not converted by Python","provenanceScope":"Saved requested solver + metadata; no profiler effective-step certificate"}
            d={"t":t,"T":T,"u":u,"y":y,"meta":meta,"actualInput":None}
            if key.startswith("C0"):
                tm=vec(f,r+"signalData/jteTmeas/time_s");Tm=num(f,r+"signalData/jteTmeas/values")
                require(Tm.shape==T.shape and np.array_equal(tm,t),"JTE102_C0_MEASURED_CLOCK")
                meta["zeroBiasMeasuredTrueVectorIdentity"]=bool(np.array_equal(Tm,T))
                meta["zeroBiasMeasuredTrueMaxAbs_K"]=float(np.max(np.abs(Tm-T)))
        else:
            require(read(f,r+"schema")=="JTE101_TF_340_RAW_NOT_G5" and read(f,r+"role")==key,"JTE102_CASE")
            require(read(f,r+"run")=="40449421507" and read(f,r+"commit")=="7876e3db9ed8ed5fc4e8735e35cfce80e790c358","JTE102_RAW_ORIGIN")
            t=vec(f,r+"observed/trueTime");T=num(f,r+"observed/trueTemperature");tu=vec(f,r+"observed/coreTime");u=vec(f,r+"observed/core")
            ty=vec(f,r+"observed/outputTime");y=vec(f,r+"observed/output")
            ti=vec(f,r+"observed/inputTime");ui=vec(f,r+"observed/input")
            tx=vec(f,r+"observed/stateTime");x=vec(f,r+"observed/state")
            require(np.array_equal(t,tx) and np.array_equal(t,ti),"JTE102_STATE_INPUT_CLOCK")
            C=float(read(f,r+"calibration/C")) if key=="ORIGINAL340" else float(read(f,r+"comparison/calibrationC"))
            meta={"sourceSHA":read(f,r+"sourceSHA256"),"loadSHA":read(f,r+"prepared/loadSHA256"),"modelSHA":read(f,r+"modelSHA256"),
              "solver":config(f,r+"prepared/beforeGraph/config"),"schema":read(f,r+"schema"),"TFstate":"SAVED_EXACT_TF_PATH_QUALIFIED_JTE101",
              "sourceStateClockQualified":bool(read(f,r+"observed/clocksQualified")),"initialStateProof":"Archived JTE101 qualification; saved-state map, not all hidden algebraic Simscape IC",
              "savedStateOutputGain":C,"stateOutputResidualMax":float(np.max(np.abs(y-C*x))),
              "eventTopologyEquivalence":read(f,r+"prepared/eventTopologyEquivalence"),"effectiveHorizon":"Native0to340 + source-pinned simulation overrides; declared model StopTime may remain2400"}
            require(sha(path.with_suffix(".slx"))==meta["modelSHA"],"JTE102_MODEL_BYTES")
            d={"t":t,"T":T,"u":u,"y":y,"x":x,"C":C,"actualInput":ui,"meta":meta}
        h=2400 if old else 340;clock(t,h)
        require(T.shape==(len(t),312) and np.array_equal(t,tu) and np.array_equal(t,ty) and len(u)==len(t) and len(y)==len(t),"JTE102_NATIVE_DIM_CLOCK")
        require(meta["sourceSHA"]==PIN and re.fullmatch("[a-f0-9]{64}",meta["loadSHA"]),"JTE102_PROVENANCE")
        meta["fileSHA"]=m["sha256"];meta["fileName"]=m["name"];meta["timeStep"]=step_stats(t)
        meta["repeatCore"]=repeated(t,u);meta["repeatPostfilter"]=repeated(t,y);meta["repeatT"]=repeated(t,T)
        meta["coreConstantAtNativePoints"]=bool(np.all(u==.25));meta["nativeHorizon_s"]=h
        meta["thermalEndpoint_K"]=T[-1];meta["thermalPerChannelMin_K"]=T.min(axis=0);meta["thermalPerChannelMax_K"]=T.max(axis=0)
        meta["TmaxGlobal_K"]=float(T.max());meta["TminGlobal_K"]=float(T.min())
        if d["actualInput"] is not None:
            meta["actualInputConstantAtNativePoints"]=bool(np.all(d["actualInput"]==.25))
            meta["actualInputMinusCoreMaxAbs"]=float(np.max(np.abs(d["actualInput"]-u)))
            meta["actualInputMinusCoreSignedAreaNormalized_s"]=float(np.sum(np.diff(t)*(d["actualInput"][:-1]-u[:-1]+d["actualInput"][1:]-u[1:])/2))
        else:meta["actualTFInputAndGap"]="UNAVAILABLE_2400_UCORE_IS_NOT_CERTIFIED_ACTUAL_TF_INPUT"
        d["events"]={name:event(t,y,u,T,w,d.get("x"),d.get("C")) for name,w in WINDOWS.items() if w[0]<h}
        return d
def clean(v):
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)):return [clean(x) for x in v]
    return v
def main():
    root=Path("jte102-private");m=json.loads((root/"input_manifest.json").read_text())
    keys=["ORIGINAL340","CONSTANT340","B0L_original","C0_original","B0L_fine","C0_fine"]
    cases={k:load_case(root/(k+".mat"),k,m) for k in keys}
    require(len({v["meta"]["loadSHA"] for v in cases.values()})==1,"JTE102_LOAD_MISMATCH")
    report={"schema":"JTE102_PRIVATE_NATIVE_IMPACT_V1","run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "inputManifest":m,"sourcePin":PIN,"protocol":"jte102/PROTOCOL.md","simulationRun":False,
      "cases":{k:{"metadata":d["meta"],"events":d["events"]} for k,d in cases.items()},"comparisons":{}}
    cp=report["comparisons"]
    cp["paired340_temperature"]=comparison(cases["ORIGINAL340"],cases["CONSTANT340"])
    cp["paired340_postfilter"]=comparison(cases["ORIGINAL340"],cases["CONSTANT340"],"y")
    cp["paired340_core"]=comparison(cases["ORIGINAL340"],cases["CONSTANT340"],"u")
    cp["paired340_temperature_first"]=comparison(cases["ORIGINAL340"],cases["CONSTANT340"],window=WINDOWS["FIRST"])
    zb=[]
    for p in ("original","fine"):
        for field in ("T","u","y"):
            z=comparison(cases["B0L_"+p],cases["C0_"+p],field)
            cp["zeroBias_"+p+"_"+field]=z
            if field=="T":zb.append(z["fullNativeVectorIdentity"])
        for w,win in WINDOWS.items():
            cp["zeroBias_"+p+"_T_"+w]=comparison(cases["B0L_"+p],cases["C0_"+p],window=win)
    for c in ("B0L","C0"):
        for field in ("T","u","y"):
            cp["solver_"+c+"_"+field]=comparison(cases[c+"_original"],cases[c+"_fine"],field)
        for w,win in WINDOWS.items():
            cp["solver_"+c+"_T_"+w]=comparison(cases[c+"_original"],cases[c+"_fine"],window=win)
            cp["solver_"+c+"_y_"+w]=comparison(cases[c+"_original"],cases[c+"_fine"],"y",win)
        so=cases[c+"_original"]["meta"]["solver"];sf=cases[c+"_fine"]["meta"]["solver"]
        report.setdefault("solverProfileDeltas",{})[c]={k:{"original":so.get(k),"fine":sf.get(k)} for k in sorted(set(so)|set(sf)) if so.get(k)!=sf.get(k)}
        require(float(sf["RelTol"])==float(so["RelTol"])/2 and float(so["MaxStep"])==.05 and sf["MaxStep"]==so["MaxStep"],"JTE102_SOLVER_PROFILE")
    effect=cp["paired340_temperature_first"]["perChannelMaxAbs"];resolution=cp["solver_B0L_T_FIRST"]["perChannelMaxAbs"]
    available=effect is not None and resolution is not None
    report["observableContrastDiagnostic"]={"paired340PerChannelContrast_K":effect,"RelTolHalfOnlyPerChannelDifference_K":resolution,
      "channelsContrastExceedsObservedRelTolDifference":int(np.sum(effect>resolution+cp["paired340_temperature_first"]["roundoffDiagnosticBudget"])) if available else None,
      "status":"EXACT_NATIVE_SUBSET_ONLY" if available else "UNAVAILABLE_EXACT_EVENT_CLOCK_ALIGNMENT",
      "qualification":"Observed contrasts only. RelTol difference is not an error bound; topology alteration confounds causal thermal attribution; no independent 1ms-filter refinement."}
    report["nearestNativeTemperatureDiagnostics"]={}
    for label,ka,kb in (("paired340","ORIGINAL340","CONSTANT340"),("solverB0L","B0L_original","B0L_fine"),("solverC0","C0_original","C0_fine")):
        a=cases[ka];b=cases[kb];idx=np.searchsorted(b["t"],a["t"]);right=np.minimum(idx,len(b["t"])-1);left=np.maximum(idx-1,0)
        j=np.where(np.abs(b["t"][right]-a["t"])<np.abs(b["t"][left]-a["t"]),right,left)
        dt=b["t"][j]-a["t"];dv=b["T"][j]-a["T"]
        report["nearestNativeTemperatureDiagnostics"][label]={"perChannelMaxAbsContrast_K":np.max(np.abs(dv),axis=0),
          "maxAbsoluteTimeSeparation_s":float(np.max(np.abs(dt))),"sampleRMSE_K":float(np.sqrt(np.mean(dv**2))),
          "semantics":"Nearest actual native temperature samples, earlier row on equal-distance tie. No interpolation. Includes real time-separation/load effects; NOT an error bound, event reconstruction, causal effect or convergence proof."}
    old_events=all(cases[c]["events"][w]["excursion"] for c in keys[2:] for w in WINDOWS)
    state_original=cases["ORIGINAL340"]["events"]["FIRST"]["excursion"]
    stable_cf=not cases["CONSTANT340"]["events"]["FIRST"]["excursion"]
    needs=old_events and state_original and stable_cf and cases['ORIGINAL340']['meta']['actualInputConstantAtNativePoints'] and cases['CONSTANT340']['meta']['actualInputConstantAtNativePoints']
    flags={"G5_PROVENANCE":"PASS_EXISTING_NATIVE_ASSETS","ZERO_BIAS_NATIVE_VECTOR":"PASS" if all(zb) and all(cases[k]["meta"].get("zeroBiasMeasuredTrueVectorIdentity",False) for k in ("C0_original","C0_fine")) else "FAIL_OR_INCOMPLETE",
      "G5_THERMAL_NUMERICS":"OBSERVABLES_AUDITED_CONVERGENCE_UNPROVEN","G5_ACTUATION_EVENT":"ACTUATION_EVENT_UNRESOLVED",
      "SECOND_EVENT_STATE":"UNAVAILABLE","ACCEPTED_STEP_CERTIFICATION":"UNAVAILABLE","B":"NEEDS_RUN" if needs else "SKIPPED_BY_DATA",
      "B_REASON":"Recurring full-horizon source events, paired source state excursion and stable direct-constant derivative justify one controller-connected equivalent realization; no causal actor proved." if needs else "Prerequisite pattern not established; inspect private metrics before any experiment.",
      "simulationRun":False,"G5_ACCEPTED":False}
    report["flags"]=flags
    prefix=root/("JTE102_"+os.environ["GITHUB_RUN_ID"])
    (prefix.with_name(prefix.name+"_METRICS.json")).write_text(json.dumps(clean(report),indent=2,allow_nan=False))
    (prefix.with_name(prefix.name+"_FLAGS.json")).write_text(json.dumps(flags,indent=2))
    with prefix.with_name(prefix.name+"_CHANNELS.csv").open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["channel_1based","B0L_endpoint_original_K","B0L_endpoint_fine_K","solverNativeMaxAbs_K","paired340FirstWindowNativeContrast_K","RelTolFirstWindowNativeDifference_K"])
        for i in range(312):
            writer.writerow([i+1,cases["B0L_original"]["T"][-1,i],cases["B0L_fine"]["T"][-1,i],cp["solver_B0L_T"]["perChannelMaxAbs"][i],effect[i] if effect is not None else "",resolution[i] if resolution is not None else ""])
    print("JTE102_A_RESULT "+" ".join(k+"="+flags[k] for k in ("G5_PROVENANCE","ZERO_BIAS_NATIVE_VECTOR","G5_THERMAL_NUMERICS","G5_ACTUATION_EVENT","B"))+" simulationRun=0 rawValuesPublished=0")
if __name__=="__main__":
    try:main()
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE102_AUDIT_EXECUTION_FAILED"
        print("JTE102_AUDIT_BLOCKED code="+code+" exceptionClass="+type(e).__name__);sys.exit(1)
