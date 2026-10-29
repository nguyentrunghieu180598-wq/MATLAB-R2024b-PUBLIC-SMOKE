"""JTE102 accepted protected-cloud I/O; no ACL/preflight or simulation."""
import json,os,re,sys
from pathlib import Path
from JTE101_io import one,download,quota,query
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte102-private")
SCHEMA="JTE102_PRIVATE_AUDIT_NOT_G5"
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if (os.environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        (e.get("repository") or {}).get("full_name")!=EXPECTED_REPO or
        os.environ.get("GITHUB_REF")!="refs/heads/codex/jte-tf-constant-input" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        (e.get("head_commit") or {}).get("message") not in {"JTE102_PRIVATE_EXISTING_MAT_AUDIT","JTE102_ONE_EQUIVALENT_STATE_SPACE_340","JTE102_EXISTING_CANDIDATE_POST_AUDIT"} or
        (e.get("head_commit") or {}).get("id")!=os.environ.get("GITHUB_SHA") or
        os.environ.get("GITHUB_RUN_ATTEMPT")!="1"):raise RuntimeError("JTE102_CONTEXT_DENIED")
    token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return token,ensure_app_folder(token)
def fetch(token,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"accessReused":"40441621436","quota":quota(token),"files":[]}
    names=[("JTE065_"+c+"_"+p+"_2400_NATIVE.mat",c+"_"+p+".mat") for c,p in (("B0L","original"),("C0","original"),("B0L","fine"),("C0","fine"))]
    for role in ("ORIGINAL340","CONSTANT340"):
        names.extend([("JTE101_40449421507_"+role+"_RAW.mat",role+".mat"),("JTE101_40449421507_"+role+"_MODEL.slx",role+".slx")])
    for name,local in names:
        m["files"].append(download(token,one(token,folder,"JTE063_VERIFIED_"+name),ROOT/local))
    (ROOT/"input_manifest.json").write_text(json.dumps(m,indent=2))
    print("JTE102_FETCH_PASS sixExistingMAT=1 existingModels=1 fullSHAandMD5=1 simulationRun=0 accessPreflightRerun=0")
def publish(token,folder):
    paths=sorted(ROOT.glob("JTE102_"+os.environ["GITHUB_RUN_ID"]+"_*"))
    if not paths:raise RuntimeError("JTE102_NO_OUTPUT")
    receipt={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"simulationRun":False}
    for p in paths:receipt["files"].append({"name":p.name,**upload_verified(token,folder,p,schema=SCHEMA)})
    p=ROOT/("JTE102_"+os.environ["GITHUB_RUN_ID"]+"_RECEIPT.json")
    p.write_text(json.dumps(receipt,indent=2));upload_verified(token,folder,p,schema=SCHEMA)
    print("JTE102_PRIVATE_READBACK_PASS rawValuesPublished=0 simulationRun=0")
def fetch_b(token,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    names=[("JTE102_40462103051_METRICS.json","audit.json"),
      ("JTE102_40462103051_RECEIPT.json","audit_receipt.json"),
      ("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")]
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"quota":quota(token)}
    for name,local in names:m["files"].append(download(token,one(token,folder,"JTE063_VERIFIED_"+name),ROOT/local))
    a=json.loads((ROOT/"audit.json").read_text())
    if a.get("run")!="40462103051" or a.get("commit")!="fba0a1072da00216c7e8910ecc372ee74cd40ff5" or a.get("flags",{}).get("B")!="NEEDS_RUN":
        raise RuntimeError("JTE102_B_NOT_JUSTIFIED")
    (ROOT/"b_manifest.json").write_text(json.dumps(m,indent=2))
    print("JTE102_B_INPUTS_PASS stageAJustifiesOneCandidate=1 existingOriginalReused=1 originalSimulationRerun=0")
def publish_b(token,folder,phase):
    names=sorted(ROOT.glob("JTE102_"+os.environ["GITHUB_RUN_ID"]+"_"+phase+"*"))
    if not names:raise RuntimeError("JTE102_B_OUTPUT_ABSENT")
    r={"schema":SCHEMA,"phase":phase,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"G5_ACCEPTED":False}
    for p in names:r["files"].append({"name":p.name,**upload_verified(token,folder,p,schema=SCHEMA)})
    p=ROOT/("JTE102_"+os.environ["GITHUB_RUN_ID"]+"_"+phase+"_RECEIPT.json")
    p.write_text(json.dumps(r,indent=2));upload_verified(token,folder,p,schema=SCHEMA)
    print("JTE102_B_PRIVATE_READBACK_PASS phase="+phase+" rawValuesPublished=0 G5_ACCEPTED=false")
def intent_b(token,folder):
    name="JTE102_STATESPACE340_INTENT.json"
    if query(token,folder,"name = 'JTE063_VERIFIED_"+name+"'"):raise RuntimeError("JTE102_B_ALREADY_ATTEMPTED_NO_REPEAT")
    one(token,folder,"JTE063_VERIFIED_JTE102_"+os.environ["GITHUB_RUN_ID"]+"_PREPARE_RECEIPT.json")
    a=json.loads((ROOT/"audit.json").read_text())
    if a["flags"]["B"]!="NEEDS_RUN":raise RuntimeError("JTE102_B_NOT_JUSTIFIED")
    p=ROOT/name
    p.write_text(json.dumps({"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "phase":"ONE_NEW_SS340_AFTER_CANARY_AND_PRIVATE_PREPARE","stageARun":"40462103051","sourceReferenceRun":"40449421507",
      "G5_ACCEPTED":False},indent=2))
    upload_verified(token,folder,p,schema=SCHEMA)
    print("JTE102_B_ONE_SHOT_INTENT_RECORDED sourceReferenceRerun=0 noAutoRepeat=1")
def fetch_post(token,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    names=[("JTE102_40462103051_METRICS.json","audit.json"),
      ("JTE101_40449421507_ORIGINAL340_RAW.mat","ORIGINAL340.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","ORIGINAL340.slx"),
      ("JTE102_40464385622_STATESPACE340_RAW.mat","STATESPACE340.mat"),
      ("JTE102_40464385622_STATESPACE340_MODEL.slx","STATESPACE340.slx"),
      ("JTE102_40464385622_STATESPACE340_RECEIPT.json","candidate_receipt.json")]
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"physicalSimulationsInThisJob":0}
    for name,local in names:m["files"].append(download(token,one(token,folder,"JTE063_VERIFIED_"+name),ROOT/local))
    (ROOT/"post_manifest.json").write_text(json.dumps(m,indent=2))
    print("JTE102_POST_FETCH_PASS existingActualCandidateAndSource=1 simulationRun=0 fullSHAandMD5=1")
def main():
    t,f=context()
    if sys.argv[1]=="fetch":fetch(t,f)
    elif sys.argv[1]=="publish":publish(t,f)
    elif sys.argv[1]=="fetch-b":fetch_b(t,f)
    elif sys.argv[1]=="fetch-post":fetch_post(t,f)
    elif sys.argv[1]=="publish-prepare":publish_b(t,f,"PREPARE")
    elif sys.argv[1]=="intent-b":intent_b(t,f)
    elif sys.argv[1]=="publish-full":publish_b(t,f,"STATESPACE340")
    else:raise RuntimeError("JTE102_MODE_DENIED")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE102_PRIVATE_IO_FAILED"
        print("JTE102_BLOCKED code="+c);sys.exit(1)
