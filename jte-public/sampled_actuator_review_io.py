"""Static/compile-only actuator amendment review. No toy/plant authorization."""
import hashlib,json,os,re,shutil,sys,urllib.parse,urllib.request
from pathlib import Path
from JTE101_io import one,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,API,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("actuator-review-private");SCHEMA="BTMS_ACTUATOR_METHOD_AMENDMENT_STATIC_ONLY"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      (e.get("repository") or {}).get("private") is False and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="BTMS_ACTUATOR_STATIC_EXACT_DIFF" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","ACT_REVIEW_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    m=one(t,f,"JTE063_VERIFIED_"+name);a=m.get("appProperties",{});size=int(m.get("size",-1))
    need(a.get("state")=="VERIFIED" and re.fullmatch("[a-f0-9]{64}",a.get("sha256","")) and 0<size<=3*1024**3,"ACT_REVIEW_INPUT_UNQUALIFIED")
    p=ROOT/local;sha=hashlib.sha256();md5=hashlib.md5(usedforsecurity=False);n=0
    req=urllib.request.Request(API+"/"+urllib.parse.quote(m["id"],safe="")+"?alt=media",headers={"Authorization":"Bearer "+t})
    with urllib.request.urlopen(req,timeout=180) as r,p.open("wb") as out:
        os.chmod(p,0o600)
        while True:
            data=r.read(8*1024**2)
            if not data:break
            n+=len(data);need(n<=size,"ACT_REVIEW_OVERSIZED_INPUT");sha.update(data);md5.update(data);out.write(data)
    need(n==size and sha.hexdigest()==a["sha256"] and md5.hexdigest()==m.get("md5Checksum"),"ACT_REVIEW_INPUT_INTEGRITY")
    return {"fileId":m["id"],"name":m["name"],"size":size,"sha256":a["sha256"],"local":local}
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"]
    probe=ROOT/("ACTUATOR_REVIEW_"+run+"_SINK_PROBE.json")
    probe.write_text(json.dumps({"schema":SCHEMA,"scope":"STATIC_COMPILE_ONLY","toy":False,"physicalSimulation":False}))
    upload_verified(t,f,probe,schema=SCHEMA)
    pairs=[
      ("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat"),
      ("JTE065_C0_original_2400_NATIVE.mat","c0_original.mat"),
      ("JTE116ONE_40645118578_PLANT_RAW.mat","negative_raw.mat"),
      ("JTE116ONE_40645118578_PLANT_RECEIPT.json","negative_receipt.json"),
      ("JTE111_40620218579_PRIVATE_FINDINGS.json","j111_findings.json"),
      ("JTE111_40620218579_PRIVATE_READBACK_RECEIPT.json","j111_receipt.json"),
      ("ACTUATOR_REVIEW_40653849248_SOURCE_C0_TEMPLATE.slx","JTE2026LocalBias.slx"),
      ("ACTUATOR_REVIEW_40653849248_PRIVATE_RECEIPT.json","template_receipt.json")]
    got={local:get(t,f,name,local) for name,local in pairs}
    rc=json.loads((ROOT/"negative_receipt.json").read_text());a=got["negative_raw.mat"]
    rows=[x for x in rc["files"] if x["name"]==a["name"].removeprefix("JTE063_VERIFIED_")]
    need(rc["run"]=="40645118578" and rc["commit"]=="c88f8b673bfba889f6234d1f78cdccbfb7417265" and len(rows)==1 and
      rows[0]["sha256"]==a["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","ACT_REVIEW_NEGATIVE_RECEIPT_LINK")
    rc=json.loads((ROOT/"j111_receipt.json").read_text());a=got["j111_findings.json"]
    rows=[x for x in rc["files"] if x["name"]==a["name"].removeprefix("JTE063_VERIFIED_")]
    need(len(rows)==1 and rows[0]["sha256"]==a["sha256"],"ACT_REVIEW_PRIOR_RECEIPT_LINK")
    refs=json.loads((ROOT/"j111_findings.json").read_text())["inputs"]
    for local in ("original_raw.mat","JTE101Original.slx","source_workspace.mat","c0_original.mat"):
        a=got[local];rows=[x for x in refs if x["name"]==a["name"]]
        if rows:need(len(rows)==1 and rows[0]["sha256"]==a["sha256"],"ACT_REVIEW_SOURCE_PROVENANCE_LINK")
    trc=json.loads((ROOT/"template_receipt.json").read_text());a=got["JTE2026LocalBias.slx"]
    rows=[x for x in trc["files"] if x["name"]==a["name"].removeprefix("JTE063_VERIFIED_")]
    need(trc["run"]=="40653849248" and trc["commit"]=="9112846e2492599e01f6e25621563f5fda798e4c" and
      len(rows)==1 and rows[0]["sha256"]==a["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED",
      "ACT_REVIEW_C0_TEMPLATE_RECEIPT_LINK")
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".");q=quota(t)
    need(mem["MemAvailable_bytes"]>4*1024**3 and disk.free>5*1024**3 and q["availableBytes"]>512*1024**2,"ACT_REVIEW_RESOURCE_UNQUALIFIED")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":list(got.values()),
      "scientificDecision":"PR61 comment6462936805","scope":"REVIEW_STATIC_COMPILE_ONLY",
      "ownerMethodApproval":False,"toyAuthorized":False,"physicalSimulationAuthorized":False,
      "TsReviewPair_s":[.01,.005],"resource":{"RAM":mem,"diskFree_bytes":disk.free,"drive":q,"CPU":os.cpu_count(),
       "repositoryPublicVerifiedFromGithubEvent":True,"runner":"ubuntu-latest_standard_github_hosted","paidServices":False}}
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/("ACTUATOR_REVIEW_"+run+"_INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    print("ACTUATOR_REVIEW_RECEIVED run="+run+" phase=STATIC_COMPILE_ONLY privateInputSHA=PASS toyAuthorized=0 physicalAuthorized=0")
def publish(t,f):
    run=os.environ["GITHUB_RUN_ID"];prefix="ACTUATOR_REVIEW_"+run+"_"
    p=ROOT/(prefix+"FLAGS.json")
    if not p.exists():p.write_text(json.dumps({"DECISION":"STATIC_REVIEW_UNQUALIFIED","TOY_RUN":False,"PHYSICAL_RUN":False,"G5_ACCEPTED":False}))
    paths=sorted(p for p in ROOT.glob(prefix+"*") if p.name!=prefix+"SINK_PROBE.json")
    rc={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":[],"physicalSimulation":False,"toySimulation":False,"G5Accepted":False}
    for p in paths:rc["files"].append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(prefix+"PRIVATE_RECEIPT.json");p.write_text(json.dumps(rc,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("ACTUATOR_REVIEW_PRIVATE_FULL_SHA_READBACK_PASS toyRun=0 physicalRun=0 G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("ACT_REVIEW_MODE_DENIED")
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="ACT_REVIEW_PRIVATE_IO_UNQUALIFIED"
        print("ACTUATOR_REVIEW_UNQUALIFIED code="+c+" toyRun=0 physicalRun=0");sys.exit(1)
