"""Read-only archived MAT -> actual MATLAB-native audit. No simulation."""
import json,os,re,sys
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte106-private");SCHEMA="JTE106_NATIVE_CORE_AUDIT_NOT_G5"
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if (os.environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or (e.get("repository") or {}).get("full_name")!=EXPECTED_REPO or
        os.environ.get("GITHUB_REF")!="refs/heads/codex/jte-tf-constant-input" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        (e.get("head_commit") or {}).get("message")!="JTE106_READONLY_NATIVE_CORE_AUDIT" or
        (e.get("head_commit") or {}).get("id")!=os.environ.get("GITHUB_SHA") or os.environ.get("GITHUB_RUN_ATTEMPT")!="1"):
        raise RuntimeError("JTE106_CONTEXT_DENIED")
    token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return token,ensure_app_folder(token)
def fetch(t,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"references":[],"cases":[],
      "missing":[],"unqualifiedCandidates":[],"support":[],"quota":quota(t),"newSimulationRun":False}
    for case,profile,ref in (("B0L","original",300),("C0","original",300),("B0L","fine",300),("C0","fine",300),("ACTIVE_C0","original",293.15)):
        name=("JTE068_ACTIVE_C0_AMBIENT293p15_2400_NATIVE.mat" if case=="ACTIVE_C0" else "JTE065_"+case+"_"+profile+"_2400_NATIVE.mat")
        rows=query(t,folder,"name = 'JTE063_VERIFIED_"+name+"'")
        if len(rows)!=1:
            m["missing"].append({"name":name,"status":"ABSENT" if not rows else "AMBIGUOUS"});continue
        v=download(t,rows[0],ROOT/(case+"_"+profile+".mat"));v.update({"label":case+"_"+profile,"controllerReferenceK":ref,"profile":profile});m["references"].append(v)
    rows=query(t,folder,"name contains 'C1' and name contains 'NATIVE' and name contains '.mat'")
    for i,meta in enumerate(sorted([z for z in rows if z["name"].lower().endswith(".mat")],key=lambda z:z["name"])):
        p=meta.get("appProperties",{})
        if p.get("state")!="VERIFIED" or not re.fullmatch("[a-f0-9]{64}",p.get("sha256","")):
            m["unqualifiedCandidates"].append({"name":meta["name"],"reason":"NO_VERIFIED_SHA"});continue
        v=download(t,meta,ROOT/("case_"+str(i+1).zfill(3)+".mat"));v["opaqueId"]="ARCHIVED_C1_"+str(i+1).zfill(3);m["cases"].append(v)
    for name,local in (("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
                       ("JTE102_40462103051_METRICS.json","accepted_audit.json"),
                       ("JTE103_40473995420_CAPABILITY_G6_LEDGER.json","selection_ledger.json")):
        m["support"].append(download(t,one(t,folder,"JTE063_VERIFIED_"+name),ROOT/local))
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    p=ROOT/("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT_INPUT_MANIFEST.json");p.write_text(json.dumps(m,indent=2))
    ack={"ack":"JTE106_RECEIVED","executor":"GITHUB_HOSTED_ACTIONS","run":os.environ["GITHUB_RUN_ID"],"jobName":os.environ["GITHUB_JOB"],
      "taskIdKind":"GITHUB_ACTIONS_WORKFLOW_RUN_NOT_CODEX_REMOTE_TASK","commit":os.environ["GITHUB_SHA"],"GUI_required":False,
      "simulationRun":False,"syntheticPythonTestsRepeated":False,"purpose":"Read existing verified MAT only; native MATLAB selector and recorded core-decision audit."}
    (ROOT/("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT_WORK_CLOUD_RECEIPT.json")).write_text(json.dumps(ack,indent=2))
    print("JTE106_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+" archivedInputSHA=PASS simulationRun=0 pythonOracleTestsRepeated=0")
def publish(t,folder):
    paths=sorted(ROOT.glob("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT*"))
    if not paths:raise RuntimeError("JTE106_OUTPUT_ABSENT")
    r={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"simulationRun":False}
    for p in paths:r["files"].append({"name":p.name,**upload_verified(t,folder,p,schema=SCHEMA)})
    p=ROOT/("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT_RECEIPT.json");p.write_text(json.dumps(r,indent=2));upload_verified(t,folder,p,schema=SCHEMA)
    print("JTE106_PRIVATE_READBACK_PASS rawValuesPublished=0 simulationRun=0 G5_NUMERICAL_ACCEPTED=false G6_TEMPERATURE_CLAIM_AUTHORIZED=false")
if __name__=="__main__":
    try:
        t,f=context()
        if sys.argv[1]=="fetch":fetch(t,f)
        elif sys.argv[1]=="publish":publish(t,f)
        else:raise RuntimeError("JTE106_MODE_DENIED")
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE106_PRIVATE_IO_FAILED"
        print("JTE106_BLOCKED code="+c);sys.exit(1)
