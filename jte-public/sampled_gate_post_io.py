"""Postprocess one saved toy only; never repeat simulation, baseline or load scan."""
import json,os,sys
from sampled_actuator_review_io import ROOT,get,need
from sampled_gate_io import SCHEMA,publish
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
MSG="BTMS_READ_SAVED_TOY_NATIVE_CLOCKS_ONLY"
def context():
    e=json.loads(open(os.environ["GITHUB_EVENT_PATH"]).read())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")==MSG and (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"NATIVE_TOY_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);files=[];old="BTMS_FEASIBILITY_40683965769_"
    def item(name,local,rc=None):
        m=get(t,f,name,local);files.append(m)
        if rc:
            a=[x for x in rc["files"] if x["name"]==name]
            need(len(a)==1 and a[0]["sha256"]==m["sha256"] and a[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","NATIVE_TOY_RECEIPT_LINK")
    item(old+"PRIVATE_RECEIPT.json","toy_receipt.json");rc=json.load(open(ROOT/"toy_receipt.json"))
    need(rc["run"]=="40683965769" and rc["commit"]=="44ff300275234b169a1461e5b58203a2f1d33c8a","NATIVE_TOY_SOURCE")
    item(old+"TOY_SUMMARY.json","toy_summary.json",rc);item(old+"TOY_EVENTS.json","toy_events.json",rc)
    item(old+"TOY_RAW.mat","SavedToyRaw.mat",rc)
    s=json.load(open(ROOT/"toy_summary.json"))
    need(s["simCount"]==1 and s["flags"]["MATLAB_TOY_COMPLETE"] and s["failure"]["identifier"]=="Gate:ToyClock","NATIVE_TOY_PRESERVE_FAILED_CLOCK_GATE")
    p=ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_NATIVE_INPUTS.json")
    p.write_text(json.dumps({"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":files,
      "scope":"READ_SAVED_TOY_ONLY_NO_NEW_SIMULATION","originalClockGateRemainsUnqualified":True}))
    print("BTMS_NATIVE_TOY_READ_RECEIVED sourceRun=40683965769 newToy=0 batteryRun=0 baselineRerun=0")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("NATIVE_TOY_MODE_DENIED")
    except Exception:print("BTMS_NATIVE_TOY_READ_BLOCKED details=OWNER_PRIVATE_ONLY");sys.exit(1)
