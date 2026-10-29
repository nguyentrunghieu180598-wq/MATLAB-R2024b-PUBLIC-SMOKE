"""Existing native sidecar audit only; never read serialized profiler internals."""
import json,os,re,sys
from pathlib import Path
import h5py,numpy as np
from JTE102_metrics import read,num,vec,sha,clock,step_stats,event,clean,require
def main():
    root=Path("jte103-private");m=json.loads((root/"delivery_manifest.json").read_text())
    for x in m["files"]:require(sha(root/x["local"])==x["sha256"],"JTE103_DELIVERY_SHA")
    summary=json.loads((root/"summary.json").read_text());p=json.loads((root/"provenance.json").read_text())
    flags=json.loads((root/"source_flags.json").read_text());rb=json.loads((root/"source_readback.json").read_text())
    g=json.loads((root/"g6_ledger.json").read_text())
    require(summary["tStart"]==0 and summary["tStop"]==340 and summary["solver"]=="ode23t","JTE103_DELIVERY_HORIZON")
    result={"schema":"JTE103_PRIVATE_DELIVERY_AUDIT","run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "manifest":m,"actualSourceRun":"40476191914","actualSourceCommit":"b2724df711a93e792df92279f22c12fa00a88b90",
      "profilerPublicSummary":summary,"sourceProvenance":p,"rawSourceFlags":flags,"privateReadback":rb,
      "PUBLIC_API_EVENT_BLOCK_ACCESS":"UNAVAILABLE_GUI_REQUIRED","EXACT_RESET_OR_ZC_ACTOR_PROVEN":False,
      "FIRST_EVENT_CAUSALITY":"NOT_PROVEN","SECOND_EVENT_SCOPE":"NOT_COVERED_340","newSimulationRun":False,"G5_ACCEPTED":False}
    with h5py.File(root/"native.mat","r") as f:
        n="native/"
        failure=read(f,n+"nativeCaptureFailure") if "nativeCaptureFailure" in f["native"] else None
        result["nativeCaptureWrapperFailure"]=failure
        available=bool(read(f,n+"available"));result["primaryNativePresent"]=available
        if available:
            t=vec(f,n+"time");T=num(f,n+"T312_K");u=vec(f,n+"core");y=vec(f,n+"postfilter")
            clock(t,340);require(T.shape==(len(t),312) and len(u)==len(t) and len(y)==len(t),"JTE103_NATIVE_PRIMARY_DIMENSIONS")
            e=event(t,y,u,T,(330.,338.));ctrl=(t>=330)&(t<=334)
            result["freshFirstEventNative"]=e
            result["freshNegativeControlNative"]={"window_s":[330,334],"flaggedSamples":int((np.abs(y[ctrl]-.25)>.005).sum()),"nativeRows":int(ctrl.sum()),
              "semantics":"Native-output localization only, not profiler reset/event counts or accepted-step certification."}
            result["nativeTimeStep"]=step_stats(t);result["coreHeldAtSavedPoints"]=bool(np.all(u==.25))
            result["initialThermalMatchesExpected"]=bool(np.array_equal(T[0],np.array(p["expectedInitialT312_K"]).reshape(-1)))
            result["FIRST_EVENT_NATIVE"]="EXCURSION_RECORDED_PRIMARY_CLOCK_QUALIFIED" if e["excursion"] else "NO_NATIVE_LOCALIZATION_FLAG"
            result["actualInputCaptured"]="actualInput" in f["native"] and "actualInputTime" in f["native"]
            result["nativeTFStateCaptured"]="TFState" in f["native"] and "TFStateTime" in f["native"]
            if result["actualInputCaptured"]:
                ti=vec(f,n+"actualInputTime");ui=vec(f,n+"actualInput")
                result["nativeInputEqualsCore"]=bool(np.array_equal(ti,t) and np.array_equal(ui,u))
            if result["nativeTFStateCaptured"]:
                tx=vec(f,n+"TFStateTime");x=vec(f,n+"TFState");C=float(read(f,n+"CtfFrozenFromAcceptedJTE101"))
                result["nativeTFStateClockMatches"]=bool(np.array_equal(tx,t))
                if np.array_equal(tx,t):result["nativeTFStateOutputResidualMax"]=float(np.max(np.abs(y-C*x)))
        else:result["FIRST_EVENT_NATIVE"]="UNAVAILABLE_PRIMARY_EXPORT"
    # Canonical source config evidence: derive bytes from saved declaration, no simulation/parameter update.
    config={"sourceSolver":p["sourceSolver"],"observerSettingNames":p["observerSettingNames"],"observerBefore":p["observerBefore"],"observerAfter":p["observerAfter"],
      "modelSHA":p["profiledModelSHA"],"workspaceSHA":p["workspaceSHA"],"loadSHA":p["loadSHA"],"sourceSHA":p["sourceSLXSHA256"]}
    cfg=root/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_DELIVERY_CONFIG.json");cfg.write_text(json.dumps(config,sort_keys=True,separators=(",",":")))
    result["configEvidenceFileSHA256"]=sha(cfg)
    result["G6_READONLY_AUDIT"]={"sourceRun":"40473995420","status":g["status"],"references":[{k:r[k] for k in ("name","controllerReferenceK","legacySites","intendedSites","deviationDecomposition","coldTieSemantics","referenceEquivalenceLimit")} for r in g["references"]],
      "savedSelections":g["savedSelections"],"newClosedLoopRuns":0,"oldOutcomesEdited":False,
      "caution":"Literal JTE042 descending-order comparison; cold-tie interpretation requires independent clarification. No new sites/scenarios are selected or run."}
    result["NUMERICAL_REFERENCE_DECISION"]="NOT_RUN_NO_SUPPORTED_LOCAL_EVENT_PROVENANCE"
    result["G5_PROVENANCE"]="PASS";result["G5_ACTUATION_EVENT"]="ACTOR_UNPROVEN";result["G5_THERMAL_CONVERGENCE"]="UNPROVEN"
    result["BLOCKER"]="BLOCKED_PROFILER_ACTOR_ACCESS"
    result["requiredCapability"]="Authorized interactive Cloud MATLAB R2024b Solver Profiler / State / Zero-Crossing Explorer of the existing saved session; block IDs and ordered reset/ZC/exception/accepted-rejected step history in event and negative-control windows. No fresh simulation is needed to open the session."
    out=root/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_DELIVERY_AUDIT.json");out.write_text(json.dumps(clean(result),indent=2,allow_nan=False))
    print("JTE103_DELIVERY_RESULT FIRST_EVENT_NATIVE="+result["FIRST_EVENT_NATIVE"]+" PROFILE_SESSION_PRIVATE_SHA=PASS EVENT_BLOCK_ACTOR=NOT_PROVEN BLOCKER=BLOCKED_PROFILER_ACTOR_ACCESS G6_READONLY_LEDGER=PASS G5_PROVENANCE=PASS G5_ACTUATION_EVENT=ACTOR_UNPROVEN G5_THERMAL_CONVERGENCE=UNPROVEN simulationRun=0")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE103_DELIVERY_AUDIT_FAILED"
        print("JTE103_DELIVERY_BLOCKED code="+c+" exceptionClass="+type(e).__name__);sys.exit(1)
