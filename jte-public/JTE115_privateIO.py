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
      (e.get("head_commit") or {}).get("message")=="JTE115_ONE_GUARDED_ODE23T340" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","JTE115_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    return download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/local)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];files=[]
    for name,local in (
      ("JTE111_40620218579_PRIVATE_READBACK_RECEIPT.json","j111_receipt.json"),
      ("JTE111_40620218579_PRIVATE_FINDINGS.json","j111_findings.json"),
      ("JTE113_40626077321_PRIVATE_READBACK_RECEIPT.json","j113_receipt.json"),
      ("JTE113_40626077321_PRIVATE_SUMMARY.json","j113_summary.json")):
        files.append(get(t,f,name,local))
    for prefix,item in (("j111",files[1]),("j113",files[3])):
        rc=json.loads((ROOT/(prefix+"_receipt.json")).read_text())
        matches=[x for x in rc["files"] if x["name"]==item["name"].removeprefix("JTE063_VERIFIED_")]
        need(len(matches)==1 and matches[0]["sha256"]==item["sha256"] and
          matches[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","JTE115_PRIOR_RECEIPT_LINK")
    j113=json.loads((ROOT/"j113_summary.json").read_text())
    need(j113["flags"]["DECISION"]=="UNQUALIFIED" and not j113["simulationStarted"] and
      not j113["failure"]["phaseTimeAdvancementEntered"],"JTE115_JTE113_NOT_CLOSED_UNQUALIFIED")
    a=json.loads((ROOT/"j111_findings.json").read_text())
    for name,local in (("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")):
        meta=get(t,f,name,local);files.append(meta)
        old=[z for z in a["inputs"] if z["name"]==meta["name"]]
        if old:need(len(old)==1 and old[0]["sha256"]==meta["sha256"],"JTE115_SOURCE_HASH_LINK")
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":files,
      "JTE113_closed":"UNQUALIFIED_INPUT_DERIVATIVES_NO_TIME_ADVANCEMENT",
      "resource":{"CPU":os.cpu_count(),"RAM":mem,"diskFree_bytes":disk.free,"drive":quota(t),
        "minuteBalance":"STANDARD_PUBLIC_RUNNER_FREE_UNLIMITED_POLICY",
        "repositoryPublicVerifiedFromGithubEvent":True,"runner":"ubuntu-latest_standard_github_hosted",
        "preflightUnixEpoch":time.time(),"runtimeLimit_s":2100,"simulationStepLimit_s":900,"paidServices":False,
        "policySources":["https://docs.github.com/en/actions/concepts/billing-and-usage",
          "https://github.com/matlab-actions/setup-matlab"]},
      "nativeClockSemantics":"Duplicates retained; no interpolation. No callback/native row relabeled accepted step.",
      "acceptedMajor":"UNAVAILABLE_NORMAL_BATCH_DRIVER_MATCHES_ARCHIVED_COMPARATOR"}
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    p=ROOT/("JTE115_"+run+"_INPUT_MANIFEST.json");p.write_text(json.dumps(m,indent=2))
    probe=ROOT/("JTE115_"+run+"_SINK_PROBE.json")
    probe.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"simulationStarted":False}))
    upload_verified(t,f,probe,schema=SCHEMA)
    print("JTE115_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" phase=PREPARE privateSinkReadback=PASS JTE113=CLOSED_UNQUALIFIED oldOriginalRerun=0")
def publish(t,f,phase):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE115_"+run+"_"
    suffixes=(["INPUT_MANIFEST.json","CONVERTER_AUDIT.json","CONVERTER_AUDIT.mat","STATIC_AUDIT.mat",
      "STATIC_PROOF.json","PREPARED.mat","GUARDED_MODEL.slx","PREPARE_RECORD.mat","PREPARE_FLAGS.json",
      "PREPARE_SUMMARY.json","PREPARE_CONSOLE.mat"] if phase=="PREPARE" else
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
def gate(t,f):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE115_"+run+"_"
    flag=json.loads((ROOT/(prefix+"PREPARE_FLAGS.json")).read_text())
    rcmeta=get(t,f,prefix+"PREPARE_RECEIPT.json","prepare_receipt_readback.json")
    rc=json.loads((ROOT/"prepare_receipt_readback.json").read_text())
    need(rc["run"]==run and rc["commit"]==os.environ["GITHUB_SHA"],"JTE115_PREPARE_RUN_MISMATCH")
    allowed=flag.get("CANARY_BITWISE_PASS") is True and flag.get("READY_FOR_ONE_SIM") is True and flag.get("STATIC_MODEL_PARITY") is True
    if allowed:
        import hashlib
        for suffix in ("PREPARE_FLAGS.json","PREPARED.mat","GUARDED_MODEL.slx","STATIC_PROOF.json"):
            name=prefix+suffix;p=ROOT/name;matches=[x for x in rc["files"] if x["name"]==name]
            need(len(matches)==1 and matches[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" and
              hashlib.sha256(p.read_bytes()).hexdigest()==matches[0]["sha256"],"JTE115_PREPARE_BYTES_NOT_DELIVERED")
        name="JTE115_GUARD375_ODE23T340_ONE_ATTEMPT_INTENT.json"
        need(not query(t,f,"name = 'JTE063_VERIFIED_"+name+"'"),"JTE115_ATTEMPT_ALREADY_RESERVED_NO_REPEAT")
        p=ROOT/name;p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
          "phase":"ONE_ATTEMPT_RESERVED_AFTER_CANARY_AND_STATIC_PRIVATE_READBACK",
          "sourceProtocolCommit":"0e91f54e8445ebcc6a97f6f270c449ab7c164329",
          "candidate":"guard375_original_ode23t_0to340","prepareReceipt":rcmeta,
          "repeatAuthorized":False,"paymentAuthorized":False,"G5_ACCEPTED":False},indent=2))
        upload_verified(t,f,p,schema=SCHEMA)
    with open(os.environ["GITHUB_OUTPUT"],"a") as out:out.write("may_run="+str(allowed).lower()+"\n")
    decision="ONE_GUARD_ATTEMPT_AUTHORIZED" if allowed else flag.get("DECISION","UNQUALIFIED_RESOURCE")
    print("JTE115_GATE "+decision+" G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context();mode=sys.argv[1]
        if mode=="fetch":fetch(t,f)
        elif mode=="publish-prepare":publish(t,f,"PREPARE")
        elif mode=="gate":gate(t,f)
        elif mode=="publish-study":publish(t,f,"STUDY")
        else:raise RuntimeError("JTE115_MODE_DENIED")
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE115_RESOURCE_OR_PRIVATE_IO_UNQUALIFIED"
        print("JTE115_UNQUALIFIED_RESOURCE code="+code+" G5_ACCEPTED=false");sys.exit(1)
