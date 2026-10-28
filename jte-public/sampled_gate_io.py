"""One authorized non-battery toy + one archived baseline map. No battery run."""
import json,os,re,shutil,sys
from pathlib import Path
from sampled_actuator_review_io import ROOT,get,need
from JTE101_io import quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
SCHEMA="BTMS_TOY_AND_BASELINE_FEASIBILITY_NOT_G5"
MSG="BTMS_TOY_AND_BASELINE_READONLY_ONCE"
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
    probe=ROOT/(pre+"SINK.json");probe.write_text(json.dumps({"scope":"ONE_NON_BATTERY_TOY_AND_BASELINE_READ_ONLY","physicalSimulationAuthorized":False}))
    upload_verified(t,f,probe,schema=SCHEMA)
    p106="JTE106_"+R106+"_AUDIT_"
    def item(name,local):
        m=get(t,f,name,local);files.append(m);return m
    cr=item(p106+"RECEIPT.json","source_receipt.json");rc=json.loads((ROOT/"source_receipt.json").read_text())
    need(rc["run"]==R106 and rc["commit"]==C106,"FEASIBILITY_PRIOR_CERTIFICATE")
    def certified(name,local,receipt):
        m=item(name,local);rows=[x for x in receipt["files"] if x["name"]==name]
        need(len(rows)==1 and rows[0]["sha256"]==m["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","FEASIBILITY_PRIOR_RECEIPT_LINK")
        return m
    certified(p106+"RESULTS.json","source_audit.json",rc)
    certified(p106+"SOURCE_LAW.json","source_law.json",rc)
    audit=json.loads((ROOT/"source_audit.json").read_text());law=json.loads((ROOT/"source_law.json").read_text())
    need(audit["run"]==R106 and audit["commit"]==C106 and law["verified"] and
      law["gain"]==.1 and law["lower"]==.001 and law["upper"]==.95 and law["step"]==.25,"FEASIBILITY_SOURCE_LAW")
    refs=[]
    for case,profile,frame in (("B0L","original",300),("C0","original",300),("B0L","fine",300),("C0","fine",300),("ACTIVE_C0","original",293.15)):
        name="JTE068_ACTIVE_C0_AMBIENT293p15_2400_NATIVE.mat" if case=="ACTIVE_C0" else "JTE065_"+case+"_"+profile+"_2400_NATIVE.mat"
        local=case+"_"+profile+".mat";m=item(name,local)
        old=[v for v in audit["manifest"]["references"] if v["name"]==m["name"]]
        need(len(old)==1 and old[0]["sha256"]==m["sha256"],"FEASIBILITY_IMMUTABLE_BASELINE")
        m.update({"caseLabel":case,"profile":profile,"frameK":frame});refs.append(m)
    pr="ACTUATOR_REVIEW_40659584085_"
    item(pr+"PRIVATE_RECEIPT.json","compile_receipt.json");rc=json.loads((ROOT/"compile_receipt.json").read_text())
    need(rc["run"]=="40659584085" and rc["commit"]=="5ebb693c5109fe79c0b32374613637f4beecccd5","FEASIBILITY_COMPILE_RECEIPT")
    for role in ("Ref","Fine"):certified(pr+"B0L_"+role+"_PROOF.json","toy_"+role+".json",rc)
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".")
    need(mem["MemAvailable_bytes"]>6*1024**3 and disk.free>6*1024**3,"FEASIBILITY_RESOURCE_NOT_QUALIFIED")
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":files,"references":refs,
      "resource":{"RAM":mem,"diskFree_bytes":disk.free,"drive":quota(t),"paidServices":False},
      "toyAuthorization":"ONE synthetic non-battery Simulink trajectory containing both frozen Ts, no retry",
      "physicalSimulationAuthorized":False,"sourceG5ThermalAccepted":False,"baselineMap":"EXPLORATORY_FIXED_STORED_STATES",
      "selection":"JTE042 B0L 1800-2400 time integral, descending mean, exact-tie ascending index; duplicate semantics explicit"}
    (ROOT/"gate_manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/(pre+"INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    for p in list(Path("jte-public").glob("sampled_gate*"))+[Path(".github/workflows/sampled-gates.yml"),Path("actuator-amendment/TOY_AND_BASELINE_FEASIBILITY_PROTOCOL.md")]:
        if p.is_file():shutil.copyfile(p,ROOT/(pre+"CODE_"+p.name))
    print("BTMS_FEASIBILITY_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" oneToyAuthorized=1 batterySimulationAuthorized=0 sourceG5Accepted=0")
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
