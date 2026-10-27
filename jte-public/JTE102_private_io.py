"""JTE102 accepted protected-cloud I/O; no ACL/preflight or simulation."""
import json,os,re,sys
from pathlib import Path
from JTE101_io import one,download,quota,context as unused_context
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
        (e.get("head_commit") or {}).get("message") not in {"JTE102_PRIVATE_EXISTING_MAT_AUDIT","JTE102_ONE_EQUIVALENT_STATE_SPACE_340"} or
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
def main():
    t,f=context()
    if sys.argv[1]=="fetch":fetch(t,f)
    elif sys.argv[1]=="publish":publish(t,f)
    else:raise RuntimeError("JTE102_MODE_DENIED")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE102_PRIVATE_IO_FAILED"
        print("JTE102_BLOCKED code="+c);sys.exit(1)
