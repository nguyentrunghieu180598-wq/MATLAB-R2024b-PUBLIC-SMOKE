"""W113 one reserved conditional attempt. Credentials confined to private I/O."""
import json,os,re,sys,time,shutil
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte113-private");SCHEMA="JTE113_ONE_SOURCE_NUMERICAL_DISCRIMINATOR_NOT_G5"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      (e.get("repository") or {}).get("private") is False and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE113_ONE_GATED_ODE23TB005_340" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","JTE113_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    return download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/local)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    run=os.environ["GITHUB_RUN_ID"]
    files=[]
    for name,local in (("JTE111_40620218579_PRIVATE_READBACK_RECEIPT.json","j111_receipt.json"),
      ("JTE111_40620218579_PRIVATE_FINDINGS.json","j111_findings.json"),
      ("JTE112_40622268033_PRIVATE_READBACK_RECEIPT.json","j112_receipt.json"),
      ("JTE112_40622268033_PRIVATE_ENVELOPE_LEDGER.json","j112_ledger.json")):
        files.append(get(t,f,name,local))
    for prefix in ("j111","j112"):
        rc=json.loads((ROOT/(prefix+"_receipt.json")).read_text())
        item=files[1] if prefix=="j111" else files[3]
        matches=[x for x in rc["files"] if x["name"]==item["name"].removeprefix("JTE063_VERIFIED_")]
        need(len(matches)==1 and matches[0]["sha256"]==item["sha256"] and matches[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED",
          "JTE113_PRIOR_RECEIPT_LINK")
    a=json.loads((ROOT/"j111_findings.json").read_text())
    for name,local in (("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")):
        meta=get(t,f,name,local);files.append(meta)
        old=[z for z in a["inputs"] if z["name"]==meta["name"]]
        if old:need(len(old)==1 and old[0]["sha256"]==meta["sha256"],"JTE113_SOURCE_HASH_LINK")
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":files,
      "resource":{"CPU":os.cpu_count(),"RAM":mem,"diskFree_bytes":disk.free,"drive":quota(t),
        "minuteBalance":"NOT_METERED_STANDARD_PUBLIC_RUNNER_FREE_UNLIMITED_POLICY",
        "repositoryPublicVerifiedFromGithubEvent":True,"runner":"ubuntu-latest_standard_github_hosted",
        "preflightUnixEpoch":time.time(),"runtimeLimit_s":2700,"simulationWallStop_s":1200,"maximumNativeRows":200000,"paidServices":False,
        "policySources":["https://docs.github.com/en/actions/concepts/billing-and-usage",
          "https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job",
          "https://github.com/matlab-actions/setup-matlab"]},
      "acceptedLogger":{"mechanism":"Simulink.Simulation.step completed-major-step output checkpoints, NOT callbacks",
        "docs":"https://www.mathworks.com/help/simulink/slref/simulink.simulation.step.html",
        "warning":"Simulation.Time is next top-of-step. Record last logged output/state timestamp and compare to the explicitly processed priorTime; never relabel currentTime output."}}
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    p=ROOT/("JTE113_"+run+"_PRIVATE_PREFLIGHT.json");p.write_text(json.dumps(m,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("JTE113_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" phase=QUALIFICATION publicStandardRunnerFree=1 privateSinkReadback=PASS oldOriginalRerun=0")
def reserve(t,f):
    name="JTE113_ODE23TB005_340_ONE_ATTEMPT_INTENT.json"
    need(not query(t,f,"name = 'JTE063_VERIFIED_"+name+"'"),"JTE113_ATTEMPT_ALREADY_RESERVED_NO_REPEAT")
    p=ROOT/name;p.write_text(json.dumps({"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "phase":"ONE_ATTEMPT_RESERVED_NOT_PROOF_SIMULATION_STARTED","sourceProtocolCommit":"37ad014883c49686a35c5c78d6611e65472efe0f",
      "candidate":"ode23tb_MaxStep005_0to340","repeatAuthorized":False,"paymentAuthorized":False},indent=2))
    upload_verified(t,f,p,schema=SCHEMA)
    print("JTE113_ONE_ATTEMPT_RESERVED noAutoRetry=1 noOriginalRerun=1")
def publish(t,f):
    run=os.environ["GITHUB_RUN_ID"];paths=sorted(ROOT.glob("JTE113_"+run+"_*"))
    need(bool(paths),"JTE113_NO_ARTIFACTS")
    flag=ROOT/("JTE113_"+run+"_PRIVATE_FLAGS.json")
    if not flag.exists():
        dec="BLOCKED_RESOURCE_NOT_QUALIFIED" if os.environ.get("JTE113_SETUP_OUTCOME")!="success" else "UNQUALIFIED"
        flag.write_text(json.dumps({"DECISION":dec,"SOURCE_PARITY":False,"ENVELOPE_FIRST_WINDOW_CONDITIONAL":"UNAVAILABLE",
          "EXCURSION_PERSISTS":"UNAVAILABLE","ACCEPTED_STEP_PROVENANCE":"UNAVAILABLE",
          "THERMAL_COMPARISON_NOT_AUTHORIZED":True,"G5_ACCEPTED":False,
          "reason":"Entry did not produce completion flags. Inspect actual setup/candidate step outcome; no automatic retry.",
          "setupOutcome":os.environ.get("JTE113_SETUP_OUTCOME"),"candidateOutcome":os.environ.get("JTE113_CANDIDATE_OUTCOME")},indent=2))
        paths=sorted(ROOT.glob("JTE113_"+run+"_*"))
    rc={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":[],"G5_ACCEPTED":False}
    for p in paths:rc["files"].append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/("JTE113_"+run+"_PRIVATE_READBACK_RECEIPT.json");p.write_text(json.dumps(rc,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("JTE113_PRIVATE_FULL_SHA_READBACK_PASS G5_ACCEPTED=false rawValuesPublished=0")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="reserve":reserve(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("JTE113_MODE_DENIED")
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE113_RESOURCE_OR_PRIVATE_IO_UNQUALIFIED"
        print("JTE113_BLOCKED_RESOURCE_NOT_QUALIFIED code="+c);sys.exit(1)
