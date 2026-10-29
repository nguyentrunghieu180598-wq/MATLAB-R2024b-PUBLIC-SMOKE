"""One conditional JTE115 guard study; secrets confined to private transport."""
import json,os,re,sys,time,shutil
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte115-private");SCHEMA="JTE115_SOURCE_EQUIVALENT_GUARD_NOT_G5"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      (e.get("repository") or {}).get("private") is False and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE115_ASSERT_DIAGNOSTIC_ONLY" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","JTE115_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    return download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/local)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"]
    oldsum=get(t,f,"JTE115_40631027346_PREPARE_SUMMARY.json","prior_harness_summary.json")
    oldrc=get(t,f,"JTE115_40631027346_PREPARE_RECEIPT.json","prior_harness_receipt.json")
    prior=json.loads((ROOT/"prior_harness_summary.json").read_text())
    rc=json.loads((ROOT/"prior_harness_receipt.json").read_text())
    linked=[x for x in rc["files"] if x["name"]==oldsum["name"].removeprefix("JTE063_VERIFIED_")]
    need(len(linked)==1 and linked[0]["sha256"]==oldsum["sha256"] and
      linked[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" and
      prior["failure"]["identifier"]=="MATLAB:error:missingMessageArgument" and
      prior["failure"]["stage"]=="CANARY" and not prior["flags"]["simulationStarted"] and
      not prior["flags"]["CANARY_BITWISE_PASS"],"JTE115_CANARY_DIAGNOSTIC_NOT_QUALIFIED")
    need(not query(t,f,"name = 'JTE063_VERIFIED_JTE115_GUARD375_ODE23T340_ONE_ATTEMPT_INTENT.json'"),
      "JTE115_PLANT_ALREADY_RESERVED")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":[oldsum,oldrc],
      "scope":"PURE_MATLAB_CANARY_ASSERT_REPORTING_ONLY","plantPermanentlyDisabled":True,
      "sourceModelLoaded":False,"simulationAuthorizedThisRun":False}
    (ROOT/("JTE115_"+run+"_INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    print("JTE115_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" phase=CORRECTED_CANARY_ONLY PLANT_DISABLED=1")

def publish(t,f,phase):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE115_"+run+"_"
    suffixes=(["INPUT_MANIFEST.json","CONVERTER_AUDIT.json","CONVERTER_AUDIT.mat","STATIC_AUDIT.mat",
      "STATIC_PROOF.json","PREPARED.mat","GUARDED_MODEL.slx","PREPARE_RECORD.mat","PREPARE_FLAGS.json",
      "PREPARE_SUMMARY.json","PREPARE_CONSOLE.mat","CANARY_PROOF.mat"] if phase=="PREPARE" else
      ["CANDIDATE_RAW.mat","STUDY_RECORD.mat","STUDY_FLAGS.json","STUDY_SUMMARY.json","STUDY_CONSOLE.mat"])
    flag=ROOT/(prefix+phase+"_FLAGS.json")
    if not flag.exists():
        flag.write_text(json.dumps({"DECISION":"UNQUALIFIED_RESOURCE","CANARY_BITWISE_PASS":False,
          "READY_FOR_ONE_SIM":False,"SOURCE_PARITY":False,"simulationStarted":"UNAVAILABLE",
          "G5_ACCEPTED":False,"reason":"No entry completion flags; inspect private console and actual step. No retry.",
          "stepOutcome":os.environ.get("JTE115_STEP_OUTCOME"),"setupOutcome":os.environ.get("JTE115_SETUP_OUTCOME")}))
    paths=[ROOT/(prefix+s) for s in suffixes if (ROOT/(prefix+s)).is_file()]
    need(bool(paths),"JTE115_NO_ARTIFACTS")
    rc={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"phase":phase,"files":[],"G5_ACCEPTED":False}
    for p in paths:
        need(not query(t,f,"name = 'JTE063_VERIFIED_"+p.name+"'"),"JTE115_DUPLICATE_OUTPUT_DENIED")
        rc["files"].append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(prefix+phase+"_RECEIPT.json");p.write_text(json.dumps(rc,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("JTE115_PRIVATE_FULL_SHA_READBACK_PASS phase="+phase+" G5_ACCEPTED=false rawValuesPublished=0")
if __name__=="__main__":
    try:
        t,f=context();mode=sys.argv[1]
        if mode=="fetch":fetch(t,f)
        elif mode=="publish-prepare":publish(t,f,"PREPARE")
        elif mode=="publish-study":publish(t,f,"STUDY")
        else:raise RuntimeError("JTE115_MODE_DENIED")
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE115_RESOURCE_OR_PRIVATE_IO_UNQUALIFIED"
        print("JTE115_UNQUALIFIED_RESOURCE code="+code+" G5_ACCEPTED=false");sys.exit(1)
