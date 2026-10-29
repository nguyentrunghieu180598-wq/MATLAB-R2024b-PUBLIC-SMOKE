"""Final role-clock check of ONE archived toy. No MATLAB or simulation."""
import json,os,sys
from pathlib import Path
import numpy as np
from sampled_actuator_review_io import ROOT,get,need
from sampled_gate_io import SCHEMA,publish
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
MSG="BTMS_SAVED_TOY_ROLE_CLOCK_REVIEW_ONLY"
def context():
    e=json.loads(open(os.environ["GITHUB_EVENT_PATH"]).read())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")==MSG and (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"ROLE_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def main(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);inputs=[]
    def item(name,local,rc=None):
        m=get(t,f,name,local);inputs.append(m)
        if rc:
            a=[x for x in rc["files"] if x["name"]==name]
            need(len(a)==1 and a[0]["sha256"]==m["sha256"] and a[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","ROLE_RECEIPT_LINK")
        return ROOT/local
    p="BTMS_FEASIBILITY_40684987494_"
    rc=json.loads(item(p+"PRIVATE_RECEIPT.json","post_receipt.json").read_text())
    need(rc["run"]=="40684987494" and rc["commit"]=="ae6032671f42e70e5fa2fdc048b88f3af1c1b15b","ROLE_POST_SOURCE")
    prior=json.loads(item(p+"NATIVE_PARTIAL_REVIEW.json","prior_native.json",rc).read_text())
    need(len(prior["branches"])==8 and all(x["nativeTickMath"]=="PASS" for x in prior["branches"]),"ROLE_NATIVE_MATH_CERTIFICATE")
    op="BTMS_FEASIBILITY_40683965769_"
    oc=json.loads(item(op+"PRIVATE_RECEIPT.json","toy_receipt.json").read_text())
    need(oc["run"]=="40683965769" and oc["commit"]=="44ff300275234b169a1461e5b58203a2f1d33c8a","ROLE_TOY_SOURCE")
    summary=json.loads(item(op+"TOY_SUMMARY.json","summary.json",oc).read_text())
    need(summary["simCount"]==1 and summary["flags"]["MATLAB_TOY_COMPLETE"] and summary["failure"]["identifier"]=="Gate:ToyClock","ROLE_HISTORY_PRESERVED")
    reports=[]
    for j,s in enumerate(summary["specs"],1):
        z={}
        for tag in ("raw","hold","actuator","ACTUAL_TICKS"):
            path=item(p+"NATIVE_"+s["id"]+"_"+tag+".csv",s["id"]+"_"+tag+".csv",rc)
            z[tag]=np.loadtxt(path,delimiter=",",ndmin=2)
        raw,hold,y,ticks=[z[k] for k in ("raw","hold","actuator","ACTUAL_TICKS")]
        flags={"NATIVE_TICK_MATH_PRIOR_PASS":True,"RAW_GRID_MATCHES_DECLARED_INPUT":bool(np.array_equal(raw[:,0],s["inputTimes"]) and np.array_equal(raw[:,1],s["inputValues"])),
          "RAW_AND_OUTPUT_NATIVE_CLOCK_EXACT":bool(np.array_equal(raw[:,0],y[:,0])),
          "SAMPLED_INPUT_CLOCK_EXACT":bool(np.array_equal(hold[:,0],ticks[:,1])),
          "SAMPLED_INPUT_VALUE_EXACT":bool(np.array_equal(hold[:,1],ticks[:,2]))}
        ix=np.searchsorted(ticks[:,1],y[:,0],side="right")-1
        flags["ACTUAL_DENSE_OUTPUT_HOLD_MATCH"]=bool(np.all(ix>=0) and np.array_equal(y[:,1],ticks[np.maximum(ix,0),5]))
        between=np.min(abs(y[:,0,None]-ticks[None,:,1]),axis=1)>32*np.spacing(1.)
        flags["BETWEEN_HIT_OBSERVATION_PRESENT"]=bool(np.any(between))
        if s["pattern"]=="MISSED_TWO_MS_PULSE":flags["PULSE_BEHAVIOR"]=bool(np.any(raw[:,1]==.5) and np.all(hold[:,1]==.25) and np.all(y[:,1]==.25))
        elif s["pattern"]=="CAPTURED_TEN_MS_PULSE":flags["PULSE_BEHAVIOR"]=bool(np.any(raw[:,1]==.5) and np.any(hold[:,1]==.5) and np.any(y[:,1]>.25))
        elif s["pattern"]=="TWO_STEP_AND_RETURN":flags["STEP_BEHAVIOR"]=bool(set(hold[:,1])=={.25,.5,.75})
        flags["INITIAL_PRESTATE_MATCH"]=bool(ticks[0,3]==s["x0"])
        ok=all(flags.values())
        reports.append({"branch":j,"Ts_s":s["Ts_s"],"pattern":s["pattern"],"flags":flags,"status":"PASS_NATIVE_ROLE_CLOCK_CRITERIA" if ok else "UNQUALIFIED_NATIVE_ROLE_CLOCK"})
    ok=all(x["status"]=="PASS_NATIVE_ROLE_CLOCK_CRITERIA" for x in reports)
    report={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"sourceToyRun":"40683965769",
      "nativeOracleRun":"40684987494","status":"TOY_TECHNICAL_NATIVE_CRITERIA_PASS_REVIEW_REQUIRED" if ok else "TOY_ROLE_CLOCK_UNQUALIFIED",
      "branches":reports,"inputs":inputs,"originalMATLABSameClockGuard":"Gate:ToyClock UNQUALIFIED retained unchanged",
      "guardDiagnosis":"The original guard wrongly required sampled u[k] and dense y(t) to have identical grids. Actual distinct role clocks are audited separately, with exact timestamps/values and no data interpolation, dedup or replacement.",
      "independentReviewerFinalAcceptance":False,"modelMethodApproved":False,"G5Accepted":False,"newSimulation":False,"noBatteryRun":True,
      "limits":["Toy is discrete implementation evidence only, not continuous actuation waveform identity or plant convergence.",
        "Original dense-clock flag is immutable. This is a separate trace-backed technical review for Chat acceptance.",
        "Source300 baseline feasibility NO_GO and supplementary293.15 ambiguity remain independent; no physical baseline authorized."]}
    out=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_ROLE_CLOCK_REVIEW.json")
    out.write_text(json.dumps(report,indent=2,allow_nan=False))
    print("SAVED_TOY_ROLE_CLOCK_STATUS="+report["status"]+" newSimulation=0 G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context();main(t,f);publish(t,f)
    except Exception:print("SAVED_TOY_ROLE_CLOCK_UNQUALIFIED details=OWNER_PRIVATE_ONLY");sys.exit(1)
