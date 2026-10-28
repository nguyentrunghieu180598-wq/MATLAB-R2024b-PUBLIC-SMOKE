"""JTE116 one new pure canary plus archived/static inspection; no plant intent."""
import json,os,re,sys,shutil,time
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte116-private");SCHEMA="JTE116_STATIC_FIX_REUSE_PASSED_CANARY_NOT_G5"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      (e.get("repository") or {}).get("private") is False and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE116_STATIC_FIX_REUSE_PASSED_CANARY" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","JTE116_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    return download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/local)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];files=[]
    for name,local in (
      ("JTE115_40631662726_CANARY_PROOF.mat","j115_canary.mat"),
      ("JTE115_40631662726_PREPARE_RECEIPT.json","j115_receipt.json"),
      ("JTE115_40631662726_PREPARE_SUMMARY.json","j115_summary.json"),
      ("JTE111_40620218579_PRIVATE_FINDINGS.json","j111_findings.json"),
      ("JTE111_40620218579_PRIVATE_READBACK_RECEIPT.json","j111_receipt.json"),
      ("JTE116_40633425452_CANARY_PROOF.mat","j116_prior_canary.mat"),
      ("JTE116_40633425452_SUMMARY.json","j116_prior_summary.json"),
      ("JTE116_40633425452_PRIVATE_RECEIPT.json","j116_prior_receipt.json"),
      ("JTE116_40633425452_JTE115_RANGE_LEDGER.json","j116_prior_range.json")):
        files.append(get(t,f,name,local))
    for prefix,items in (("j115",[files[0],files[2]]),("j111",[files[3]]),("j116_prior",[files[5],files[6],files[8]])):
        rc=json.loads((ROOT/(prefix+"_receipt.json")).read_text())
        for item in items:
            matches=[x for x in rc["files"] if x["name"]==item["name"].removeprefix("JTE063_VERIFIED_")]
            need(len(matches)==1 and matches[0]["sha256"]==item["sha256"] and
              matches[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","JTE116_PRIOR_RECEIPT_LINK")
    prior=json.loads((ROOT/"j116_prior_summary.json").read_text())
    need(prior["flags"]["CANARY_BITWISE_PASS"] is True and prior["canary"]["strictBitwisePass"] is True and
      prior["failure"]["identifier"]=="JTE115:NoConvertsFound" and not prior["flags"]["PHYSICAL_SIMULATION_STARTED"],
      "JTE116_STATIC_RECOVERY_ONLY")
    old=json.loads((ROOT/"j115_summary.json").read_text())
    need(old["failure"]["identifier"]=="JTE115:MATLAB_DOUBLE_NOT_EQUIVALENT" and
      not old["flags"]["simulationStarted"],"JTE116_PRIOR_REJECTION_PROVENANCE")
    a=json.loads((ROOT/"j111_findings.json").read_text())
    for name,local in (
      ("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")):
        meta=get(t,f,name,local);files.append(meta)
        linked=[z for z in a["inputs"] if z["name"]==meta["name"]]
        if linked:need(len(linked)==1 and linked[0]["sha256"]==meta["sha256"],"JTE116_SOURCE_HASH_LINK")
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".");q=quota(t)
    need(mem["MemAvailable_bytes"]>4*1024**3 and disk.free>3*1024**3 and q["availableBytes"]>512*1024**2,
      "JTE116_RESOURCE_NOT_QUALIFIED")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":files,
      "simulationAuthorized":False,"newPlantIntent":False,"resource":{"RAM":mem,"diskFree_bytes":disk.free,
      "drive":q,"CPU":os.cpu_count(),"repositoryPublicVerifiedFromGithubEvent":True,
      "runner":"ubuntu-latest_standard_github_hosted","paidServices":False,
      "includedLicense":"Actual MATLAB checkout still required","timeUnix":time.time()},
      "canarySourceCommit":"d07a4d23ea664544ef8dc9a352ec3023a87dd64e",
      "priorModEvidence":{"standardFixtureRun":"40301939641","standardJob":"121501673756","matchesMATLABMod":True,
        "thresholdReplacementRejected":True,"atomicFixtureRun":"40303063260","atomicJob":"121505386117",
        "scope":"Existing finite fixtures only; not rerun and not all-input/event equivalence"}}
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/("JTE116_"+run+"_INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    print("JTE116_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" phase=STATIC_ONLY_REUSE_CANARY_PASS privateInputSHA=PASS physicalSimulationAuthorized=0")
def publish(t,f):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE116_"+run+"_"
    flag=ROOT/(prefix+"FLAGS.json")
    if not flag.exists():
        flag.write_text(json.dumps({"DECISION":"UNQUALIFIED_RESOURCE","CANARY_BITWISE_PASS":False,
          "PHYSICAL_SIMULATION_STARTED":False,"G5_ACCEPTED":False,
          "setupOutcome":os.environ.get("JTE116_SETUP_OUTCOME"),"executionOutcome":os.environ.get("JTE116_EXECUTION_OUTCOME")}))
    paths=sorted(ROOT.glob(prefix+"*"));need(bool(paths),"JTE116_NO_PRIVATE_ARTIFACTS")
    rc={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":[],"physicalSimulation":False,"G5_ACCEPTED":False}
    for p in paths:
        need(not query(t,f,"name = 'JTE063_VERIFIED_"+p.name+"'"),"JTE116_DUPLICATE_OUTPUT_DENIED")
        rc["files"].append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(prefix+"PRIVATE_RECEIPT.json");p.write_text(json.dumps(rc,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("JTE116_PRIVATE_FULL_SHA_READBACK_PASS physicalSimulationStarted=0 G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context();mode=sys.argv[1]
        if mode=="fetch":fetch(t,f)
        elif mode=="publish":publish(t,f)
        else:raise RuntimeError("JTE116_MODE_DENIED")
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE116_PRIVATE_IO_UNQUALIFIED"
        print("JTE116_UNQUALIFIED_RESOURCE code="+code+" G5_ACCEPTED=false");sys.exit(1)
