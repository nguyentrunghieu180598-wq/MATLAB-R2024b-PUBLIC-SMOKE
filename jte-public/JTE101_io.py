"""JTE101 private scientific I/O. Reuse accepted access; no ACL/auth preflight."""
from __future__ import annotations
import hashlib,json,os,re,sys,urllib.parse,urllib.request
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,API,access_token,ensure_app_folder,req
from JTE063_streaming_drive import upload_verified
SCHEMA="JTE101_BOUNDED_TF_DIAGNOSTIC_NOT_G5"
DIRECTORY=Path("jte101-private")
TRIGGERS={"a":"JTE101_STAGE_A_NATIVE_SCHEMA_AUDIT","b":"JTE101_STAGE_B_SINGLE_CONSTANT_INPUT_340"}
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if (os.environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        (e.get("repository") or {}).get("full_name")!=EXPECTED_REPO or
        os.environ.get("GITHUB_REF")!="refs/heads/codex/jte-tf-constant-input" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or
        (e.get("head_commit") or {}).get("message") not in TRIGGERS.values() or
        (e.get("head_commit") or {}).get("id")!=os.environ.get("GITHUB_SHA") or
        os.environ.get("GITHUB_RUN_ATTEMPT")!="1"):
        raise PermissionError("JTE101_CONTEXT_DENIED")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):raise RuntimeError("JTE101_ACCEPTED_CREDENTIALS_UNAVAILABLE")
    token=access_token(*[os.environ[k] for k in keys])
    return token,ensure_app_folder(token)
def query(token,folder,condition):
    q="'"+folder+"' in parents and trashed=false and ("+condition+")"
    _,_,b=req(API+"?"+urllib.parse.urlencode({"q":q,"fields":"nextPageToken,files(id,name,size,md5Checksum,appProperties)","pageSize":100}),token=token)
    obj=json.loads(b)
    if obj.get("nextPageToken"):raise RuntimeError("JTE101_AMBIGUOUS_PAGINATION")
    return obj.get("files",[])
def one(token,folder,name):
    rows=query(token,folder,"name = '"+name+"'")
    if len(rows)!=1:raise RuntimeError("JTE101_REFERENCE_NOT_UNIQUE")
    return rows[0]
def download(token,meta,path):
    p=meta.get("appProperties",{});expected=p.get("sha256","")
    if p.get("state")!="VERIFIED" or not re.fullmatch("[a-f0-9]{64}",expected):raise RuntimeError("JTE101_UNVERIFIED_ASSET")
    size=int(meta.get("size",-1))
    if not 0<size<1024**3:raise RuntimeError("JTE101_ASSET_SIZE_GUARD")
    request=urllib.request.Request(API+"/"+urllib.parse.quote(meta["id"],safe="")+"?alt=media",headers={"Authorization":"Bearer "+token})
    sha=hashlib.sha256();md5=hashlib.md5(usedforsecurity=False);n=0
    with urllib.request.urlopen(request,timeout=180) as response,path.open("wb") as out:
        os.chmod(path,0o600)
        while True:
            data=response.read(8*1024**2)
            if not data:break
            n+=len(data)
            if n>size:raise RuntimeError("JTE101_OVERSIZED_DOWNLOAD")
            sha.update(data);md5.update(data);out.write(data)
    if n!=size or sha.hexdigest()!=expected or md5.hexdigest()!=meta.get("md5Checksum"):raise RuntimeError("JTE101_ASSET_INTEGRITY_FAILED")
    return {"fileId":meta["id"],"name":meta["name"],"sha256":expected,"size":size,"local":path.name}
def quota(token):
    _,_,body=req("https://www.googleapis.com/drive/v3/about?fields=storageQuota",token=token)
    q=json.loads(body).get("storageQuota",{})
    limit=int(q.get("limit",0));used=int(q.get("usage",0))
    if limit<=0 or limit-used<512*1024**2:raise RuntimeError("JTE101_STORAGE_QUOTA_NOT_QUALIFIED")
    return {"availableBytes":limit-used,"reservedDiagnosticBytes":512*1024**2,"paidServices":False}
def fetch_a(token,folder):
    DIRECTORY.mkdir(mode=0o700,exist_ok=False)
    manifest={"schema":"JTE101_PRIVATE_INPUT_MANIFEST","quota":quota(token),"references":[],"stateArchives":[],
      "accessReceiptReused":"40441621436","run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"]}
    for case,profile in (("B0L","original"),("C0","original"),("B0L","fine"),("C0","fine")):
        key=case+"_"+profile
        meta=one(token,folder,"JTE063_VERIFIED_JTE065_"+key+"_2400_NATIVE.mat")
        item=download(token,meta,DIRECTORY/(key+".mat"));item["key"]=key
        manifest["references"].append(item)
    archives=query(token,folder,"name contains 'JTE084' or name contains 'JTE088'")
    verified=[m for m in archives if m.get("appProperties",{}).get("state")=="VERIFIED" and re.fullmatch("[a-f0-9]{64}",m.get("appProperties",{}).get("sha256",""))]
    if len(verified)==1:
        manifest["stateArchives"].append(download(token,verified[0],DIRECTORY/"archived_state.mat"))
    manifest["stateArchiveCandidateCount"]=len(verified)
    (DIRECTORY/"input_manifest.json").write_text(json.dumps(manifest,indent=2))
    print("JTE101_EXISTING_MAT_FETCHED integrity=PASS quota=PASS accessPreflight=REUSED simulationRun=0")
def publish(token,folder,phase):
    run=os.environ["GITHUB_RUN_ID"]
    paths=sorted(DIRECTORY.glob("JTE101_"+run+"_"+phase+"*"))
    if not paths:raise RuntimeError("JTE101_OUTPUT_ABSENT")
    receipt={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"phase":phase,"files":[]}
    for p in paths:
        result=upload_verified(token,folder,p,schema=SCHEMA)
        receipt["files"].append({"name":p.name,**result})
    out=DIRECTORY/("JTE101_"+run+"_"+phase+"_RECEIPT.json")
    out.write_text(json.dumps(receipt,indent=2));upload_verified(token,folder,out,schema=SCHEMA)
    print("JTE101_PRIVATE_READBACK_PASS phase="+phase+" rawResearchValuesPublished=0 G5_ACCEPTED=false")

def fetch_b(token,folder):
    run=os.environ.get("JTE101_AUDIT_RUN","")
    if not run.isdigit():raise RuntimeError("JTE101_AUDIT_RUN_UNSET")
    DIRECTORY.mkdir(mode=0o700,exist_ok=False)
    meta=one(token,folder,"JTE063_VERIFIED_JTE101_"+run+"_STAGE_A_AUDIT.mat")
    result=download(token,meta,DIRECTORY/"stage_a_audit.mat")
    m={"stageARun":run,"audit":result,"quota":quota(token),"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"]}
    (DIRECTORY/"stage_b_manifest.json").write_text(json.dumps(m,indent=2))
    print("JTE101_STAGE_A_REUSED privateAuditSHA=PASS schemaAuditRerun=0 accessPreflightRerun=0")
def intent(token,folder,role):
    if role not in {"ORIGINAL340","CONSTANT340"}:raise RuntimeError("JTE101_ROLE_DENIED")
    name="JTE101_"+role+"_INTENT.json"
    prior=query(token,folder,"name = 'JTE063_VERIFIED_"+name+"'")
    if prior:
        if role!="ORIGINAL340" or len(prior)!=1:raise RuntimeError("JTE101_ROLE_ALREADY_AUTHORIZED_NO_REPEAT")
        old_path=DIRECTORY/"prior_original_intent.json"
        download(token,prior[0],old_path);old=json.loads(old_path.read_text())
        if old.get("run")!="40448269062" or old.get("commit")!="1e943934405a465ce158297d1ea27d5ddbe286fc":
            raise RuntimeError("JTE101_RECOVERY_PRIOR_MISMATCH")
        if query(token,folder,"name = 'JTE063_VERIFIED_JTE101_40448269062_ORIGINAL340_RECEIPT.json'"):
            raise RuntimeError("JTE101_PRIOR_RAW_EXISTS_NO_RECOVERY")
        name="JTE101_ORIGINAL340_RESUME_AFTER_40448269062_COMPILE_FAILURE_INTENT.json"
        if query(token,folder,"name = 'JTE063_VERIFIED_"+name+"'"):
            raise RuntimeError("JTE101_COMPILE_RECOVERY_ALREADY_AUTHORIZED")
        one(token,folder,"JTE063_VERIFIED_JTE101_"+os.environ["GITHUB_RUN_ID"]+"_PREPARE_RECEIPT.json")
        p=DIRECTORY/"JTE101_40448269062_COMPILE_FAILURE_RECEIPT.json"
        p.write_text(json.dumps({"schema":SCHEMA,"failedRun":"40448269062","failedCommit":"1e943934405a465ce158297d1ea27d5ddbe286fc",
          "job":"122004630243","evidence":"Compile-time unresolved source base variables ambient/T_vec/AH; no SimulationOutput; constant step skipped",
          "integrationStarted":False,"successful340":False,"priorIntentPreserved":True,
          "repair":"Restore SHA-verified exact source-preload workspace equal to archived resolvedVariables; compile both roles first",
          "recoveryRun":os.environ["GITHUB_RUN_ID"],"recoveryCommit":os.environ["GITHUB_SHA"],"G5_ACCEPTED":False},indent=2))
        upload_verified(token,folder,p,schema=SCHEMA)
        print("JTE101_COMPILE_FAILURE_RECOVERY oldIntegrationStarted=0 priorIntentPreserved=1 successfulSimulationRepeat=0")
    if role=="CONSTANT340":
        one(token,folder,"JTE063_VERIFIED_JTE101_"+os.environ["GITHUB_RUN_ID"]+"_ORIGINAL340_RECEIPT.json")
    p=DIRECTORY/name
    p.write_text(json.dumps({"schema":SCHEMA,"role":role,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "sourceAuditRun":os.environ["JTE101_AUDIT_RUN"],"state":"ONE_SHOT_INTENT_BEFORE_SIMULATION","G5_ACCEPTED":False},indent=2))
    upload_verified(token,folder,p,schema=SCHEMA)
    print("JTE101_ONE_SHOT_INTENT_PRIVATE_RECORDED role="+role+" noRepeat=1")

def main():
    token,folder=context();mode=sys.argv[1]
    if mode=="fetch-a":fetch_a(token,folder)
    elif mode=="publish-a":publish(token,folder,"STAGE_A")
    elif mode=="fetch-b":fetch_b(token,folder)
    elif mode=="intent-original":intent(token,folder,"ORIGINAL340")
    elif mode=="intent-constant":intent(token,folder,"CONSTANT340")
    elif mode=="publish-prepare":publish(token,folder,"PREPARE")
    elif mode=="publish-original":publish(token,folder,"ORIGINAL340")
    elif mode=="publish-constant":publish(token,folder,"CONSTANT340")
    else:raise RuntimeError("JTE101_MODE_NOT_IMPLEMENTED")
if __name__=="__main__":
    try:main()
    except Exception as exc:
        code=str(exc)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE101_PRIVATE_IO_FAILED"
        print("JTE101_BLOCKED code="+code+" G5_ACCEPTED=false");sys.exit(1)
