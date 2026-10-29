"""Single first valid toy horizon after SHA-proven pre-execution compile failures."""
import json,os,sys
from sampled_actuator_review_io import ROOT,get,need
from sampled_gate_io import SCHEMA,publish
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
MSG="BTMS_FIRST_VALID_TOY_WITH_COMPILE_GUARD"
def context():
    e=json.loads(open(os.environ["GITHUB_EVENT_PATH"]).read())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and os.environ.get("GITHUB_EVENT_NAME")=="push" and
      os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and (e.get("head_commit") or {}).get("message")==MSG and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","TOY_TAIL_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);files=[]
    def item(name,local,rc=None):
        m=get(t,f,name,local);files.append(m)
        if rc:
            v=[x for x in rc["files"] if x["name"]==name]
            need(len(v)==1 and v[0]["sha256"]==m["sha256"] and v[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","TOY_TAIL_RECEIPT_LINK")
        return m
    old="BTMS_FEASIBILITY_40683303822_"
    item(old+"PRIVATE_RECEIPT.json","diagnostic_receipt.json");rc=json.load(open(ROOT/"diagnostic_receipt.json"))
    need(rc["run"]=="40683303822" and rc["commit"]=="c875f37780629c692bf8ce0d24fd8af5bd4ee3aa","TOY_TAIL_DIAGNOSTIC_SOURCE")
    item(old+"FINAL_READONLY_RESULT.json","diagnostic_result.json",rc);d=json.load(open(ROOT/"diagnostic_result.json"))
    c=d["existingToyCompile"]
    need(c["status"]=="COMPILE_FAILURE_REPRODUCED" and len(c["causes"]["children"])==8 and
      all(x["identifier"]=="Simulink:SimInput:FromwksNoExtrapWithoutInterp" for x in c["causes"]["children"]),"TOY_TAIL_EXACT_COMPILER_CAUSE")
    old="BTMS_FEASIBILITY_40669078761_"
    item(old+"PRIVATE_RECEIPT.json","failed_toy_receipt.json");rc=json.load(open(ROOT/"failed_toy_receipt.json"))
    need(rc["run"]=="40669078761" and rc["commit"]=="c9df69ebee56938faa6f484fb77343841c60aa59","TOY_TAIL_FAILED_TOY_SOURCE")
    item(old+"TOY_SUMMARY.json","failed_toy_summary.json",rc);item(old+"TOY_EVENTS.json","failed_toy_events.json",rc)
    s=json.load(open(ROOT/"failed_toy_summary.json"))
    need(s["simCount"]==1 and not s["flags"]["MATLAB_TOY_COMPLETE"] and not json.load(open(ROOT/"failed_toy_events.json")),"TOY_TAIL_NO_PREVIOUS_VALID_HORIZON")
    old="ACTUATOR_REVIEW_40659584085_"
    item(old+"PRIVATE_RECEIPT.json","compile_receipt.json");rc=json.load(open(ROOT/"compile_receipt.json"))
    need(rc["run"]=="40659584085" and rc["commit"]=="5ebb693c5109fe79c0b32374613637f4beecccd5","TOY_TAIL_PRIMITIVE_SOURCE")
    for role in ("Ref","Fine"):item(old+"B0L_"+role+"_PROOF.json","toy_"+role+".json",rc)
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":files,
      "scope":"ONE_FIRST_VALID_NONBATTERY_TOY_HORIZON_AFTER_DOCUMENTED_COMPILE_FAILURES",
      "baselineRepeated":False,"publicInputRepeated":False,"physicalSimulationAuthorized":False,
      "correction":"FromWorkspace tail hold instead of invalid extrapolation with interpolation off; same samples, patterns, Ts, actuator coefficients, no input interpolation"}
    (ROOT/("BTMS_FEASIBILITY_"+os.environ["GITHUB_RUN_ID"]+"_TOY_TAIL_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    print("BTMS_TOY_COMPILE_CAUSE_GATE_PASS run="+os.environ["GITHUB_RUN_ID"]+" priorValidToyHorizon=0 baselineRerun=0 physicalRun=0")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("TOY_TAIL_MODE_DENIED")
    except Exception:print("BTMS_TOY_TAIL_BLOCKED details=OWNER_PRIVATE_ONLY");sys.exit(1)
