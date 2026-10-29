"""One authorized non-battery toy + one archived baseline map. No battery run."""
import json,os,re,shutil,sys
from pathlib import Path
from sampled_actuator_review_io import ROOT,get,need
from JTE101_io import quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
SCHEMA="BTMS_TOY_AND_BASELINE_FEASIBILITY_NOT_G5"
MSG="BTMS_FIRST_TOY_AFTER_ZERO_SIM_API_FIX"
R106="40485742742";C106="ceeb8a5590f9361016ad4c69004ffdc9e9223c94"
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and os.environ.get("GITHUB_EVENT_NAME")=="push" and
      os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and (e.get("head_commit") or {}).get("message")==MSG and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","FEASIBILITY_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];pre="BTMS_FEASIBILITY_"+run+"_";files=[]
    def item(name,local):
        m=get(t,f,name,local);files.append(m);return m
    def certified(name,local,rc):
        m=item(name,local);rows=[v for v in rc["files"] if v["name"]==name]
        need(len(rows)==1 and rows[0]["sha256"]==m["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","TOY_CONT_RECEIPT_LINK")
        return m
    old="BTMS_FEASIBILITY_40668084392_"
    item(old+"PRIVATE_RECEIPT.json","prior_receipt.json");rc=json.loads((ROOT/"prior_receipt.json").read_text())
    need(rc["run"]=="40668084392" and rc["commit"]=="05d64995fe857bfd6af9012c4922b67c63c7c0ed","TOY_CONT_SOURCE_RUN")
    certified(old+"TOY_SUMMARY.json","prior_toy_summary.json",rc)
    s=json.loads((ROOT/"prior_toy_summary.json").read_text())
    need(s["simCount"]==0 and not s["flags"]["MATLAB_TOY_COMPLETE"] and
      s["failure"]["identifier"]=="Simulink:Commands:ParamUnknown" and "SignalStorageReuse" in s["failure"]["message"],"TOY_CONT_ZERO_TRAJECTORY_GATE")
    certified(old+"BASELINE_LEDGER.json","prior_baseline_ledger.json",rc)
    q=json.loads((ROOT/"prior_baseline_ledger.json").read_text())
    need(q["decision"]=="NO_ELIGIBLE_SMALL_GROUP_IN_CURRENT_BASELINE" and not q["failures"],"TOY_CONT_BASELINE_REUSE")
    old="ACTUATOR_REVIEW_40659584085_"
    item(old+"PRIVATE_RECEIPT.json","compile_receipt.json");rc=json.loads((ROOT/"compile_receipt.json").read_text())
    need(rc["run"]=="40659584085" and rc["commit"]=="5ebb693c5109fe79c0b32374613637f4beecccd5","TOY_CONT_COMPILE_SOURCE")
    for role in ("Ref","Fine"):certified(old+"B0L_"+role+"_PROOF.json","toy_"+role+".json",rc)
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":files,"priorToyTrajectories":0,
      "toyAttemptAllowed":1,"baselineAuditRepeated":False,"physicalSimulationAuthorized":False,"resource":{"drive":quota(t),"paidServices":False}}
    (ROOT/"gate_manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/(pre+"INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    for p in list(Path("jte-public").glob("sampled_gate*"))+[Path(".github/workflows/sampled-gates.yml"),Path("actuator-amendment/TOY_AND_BASELINE_FEASIBILITY_PROTOCOL.md")]:
        if p.is_file():shutil.copyfile(p,ROOT/(pre+"CODE_"+p.name))
    print("BTMS_TOY_ZERO_SIM_GATE_PASS executor=GITHUB_HOSTED_ACTIONS run="+run+" priorTrajectories=0 baselineReused=1 batterySimulationAuthorized=0")
def publish(t,f):
    run=os.environ["GITHUB_RUN_ID"];pre="BTMS_FEASIBILITY_"+run+"_";out=[]
    for p in sorted(ROOT.glob(pre+"*")):
        if p.name==pre+"SINK.json":continue
        out.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(pre+"PRIVATE_RECEIPT.json")
    p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":out,
      "batterySimulationRun":False,"G5Accepted":False},indent=2))
    upload_verified(t,f,p,schema=SCHEMA)
    print("BTMS_FEASIBILITY_FULL_PRIVATE_READBACK_PASS G5_ACCEPTED=false batteryRun=0")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("FEASIBILITY_MODE_DENIED")
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="FEASIBILITY_PRIVATE_IO_UNQUALIFIED"
        print("BTMS_FEASIBILITY_BLOCKED code="+code);sys.exit(1)
