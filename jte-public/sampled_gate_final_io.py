"""Read-only existing toy compile diagnostic and bounded public-input screen."""
import json,os,sys
from sampled_actuator_review_io import ROOT,get,need
from sampled_gate_io import SCHEMA,publish
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
MSG="BTMS_SAVED_TOY_COMPILE_AND_BOUNDED_INPUT_ONLY"
def context():
    e=json.loads(open(os.environ["GITHUB_EVENT_PATH"]).read())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")==MSG and (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","FINAL_READONLY_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);files=[]
    def one(name,local,rc=None):
        m=get(t,f,name,local);files.append(m)
        if rc:
            z=[x for x in rc["files"] if x["name"]==name]
            need(len(z)==1 and z[0]["sha256"]==m["sha256"] and z[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","FINAL_READONLY_RECEIPT_LINK")
        return m
    old="BTMS_FEASIBILITY_40669078761_"
    one(old+"PRIVATE_RECEIPT.json","toy_receipt.json");rc=json.load(open(ROOT/"toy_receipt.json"))
    need(rc["run"]=="40669078761" and rc["commit"]=="c9df69ebee56938faa6f484fb77343841c60aa59","FINAL_READONLY_TOY_RECEIPT")
    one(old+"TOY_SUMMARY.json","toy_summary.json",rc);one(old+"TOY_EVENTS.json","toy_events.json",rc)
    s=json.load(open(ROOT/"toy_summary.json"));ev=json.load(open(ROOT/"toy_events.json"))
    need(s["simCount"]==1 and not s["flags"]["MATLAB_TOY_COMPLETE"] and
      s["failure"]["identifier"]=="MATLAB:MException:MultipleErrors" and not ev,"FINAL_READONLY_NO_VALID_TOY_TRAJECTORY")
    one(old+"TOY_MODEL.slx","SavedToy.slx",rc)
    old="BTMS_FEASIBILITY_40668084392_"
    one(old+"PRIVATE_RECEIPT.json","baseline_receipt.json");rc=json.load(open(ROOT/"baseline_receipt.json"))
    need(rc["run"]=="40668084392" and rc["commit"]=="05d64995fe857bfd6af9012c4922b67c63c7c0ed","FINAL_READONLY_BASELINE_RECEIPT")
    one(old+"BASELINE_LEDGER.json","prior_baseline_ledger.json",rc)
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":files,
      "scope":"EXISTING_TOY_COMPILE_ONLY_AND_PUBLIC_INPUT_ONLY","newSimulationAuthorized":False,"baselineRepeated":False}
    (ROOT/"readonly_manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_READONLY_INPUTS.json")).write_text(json.dumps(m,indent=2))
    print("BTMS_FINAL_READONLY_RECEIVED run="+os.environ["GITHUB_RUN_ID"]+" newToy=0 baselineRerun=0 batteryRun=0")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("FINAL_READONLY_MODE_DENIED")
    except Exception:print("BTMS_FINAL_READONLY_BLOCKED details=OWNER_PRIVATE_ONLY");sys.exit(1)
