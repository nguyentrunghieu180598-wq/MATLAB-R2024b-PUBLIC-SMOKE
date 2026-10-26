"""Private access gate for authorized TF constant-input diagnostic. No MATLAB."""
from __future__ import annotations
import hashlib,json,os,re,sys,urllib.parse,urllib.request
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,API,access_token,ensure_app_folder,req
from JTE063_streaming_drive import upload_verified
BRANCH="refs/heads/codex/jte-tf-constant-input"
TRIGGER="JTE_TF_CONSTANT_PRIVATE_ACCESS_PREFLIGHT"
REFERENCE="JTE063_VERIFIED_JTE065_B0L_original_2400_NATIVE.mat"
SCHEMA="TF_CONSTANT_INPUT_DIAGNOSTIC_340_NOT_G5"
def guard(event,env,trigger=TRIGGER):
    if (env.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        (event.get("repository") or {}).get("full_name")!=EXPECTED_REPO or
        (event.get("repository") or {}).get("private") is not False or
        env.get("GITHUB_REF")!=BRANCH or env.get("GITHUB_EVENT_NAME")!="push" or
        (event.get("head_commit") or {}).get("message")!=trigger or
        (event.get("head_commit") or {}).get("id")!=env.get("GITHUB_SHA") or
        env.get("GITHUB_RUN_ATTEMPT","1")!="1"):
        raise PermissionError("TF_PRIVATE_CONTEXT_DENIED")
def private_meta(token,file_id):
    fields="id,name,size,md5Checksum,appProperties,permissions(type,role)"
    _,_,body=req(API+"/"+urllib.parse.quote(file_id,safe="")+"?"+urllib.parse.urlencode({"fields":fields}),token=token)
    meta=json.loads(body);permissions=meta.get("permissions",[])
    if not permissions or any(p.get("type")!="user" or p.get("role")!="owner" for p in permissions):
        raise PermissionError("TF_DESTINATION_NOT_OWNER_PRIVATE")
    return meta
def list_reference(token,folder):
    filt="'"+folder+"' in parents and name = '"+REFERENCE+"' and trashed = false"
    _,_,body=req(API+"?"+urllib.parse.urlencode({"q":filt,"fields":"nextPageToken,files(id)","pageSize":100}),token=token)
    data=json.loads(body);rows=data.get("files",[])
    if data.get("nextPageToken") or len(rows)!=1:
        raise RuntimeError("TF_REFERENCE_NOT_UNIQUE_OR_UNAVAILABLE")
    return private_meta(token,rows[0]["id"])
def download_reference(token,meta,target):
    props=meta.get("appProperties",{});sha=props.get("sha256","")
    if props.get("state")!="VERIFIED" or not re.fullmatch("[0-9a-f]{64}",sha):
        raise RuntimeError("TF_REFERENCE_PRIVATE_RECEIPT_UNAVAILABLE")
    size=int(meta.get("size",-1))
    if not (1000<size<1024**3):raise RuntimeError("TF_REFERENCE_SIZE_OUT_OF_SCOPE")
    request=urllib.request.Request(API+"/"+urllib.parse.quote(meta["id"],safe="")+"?alt=media",headers={"Authorization":"Bearer "+token})
    h=hashlib.sha256();md5=hashlib.md5(usedforsecurity=False);n=0
    with urllib.request.urlopen(request,timeout=180) as response,target.open("wb") as out:
        os.chmod(target,0o600)
        while True:
            b=response.read(8*1024**2)
            if not b:break
            n+=len(b)
            if n>size:raise RuntimeError("TF_REFERENCE_OVERSIZED")
            h.update(b);md5.update(b);out.write(b)
    if n!=size or h.hexdigest()!=sha or md5.hexdigest()!=meta.get("md5Checksum"):
        raise RuntimeError("TF_REFERENCE_DOWNLOAD_INTEGRITY_FAILED")
    return {"sha256":sha,"size_bytes":size,"driveFileId":meta["id"],"verification":"PRIVATE_DOWNLOAD_SHA_MD5_MATCH"}
def main():
    guard(json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text()),os.environ)
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):
        raise RuntimeError("BLOCKED_PRIVATE_DRIVE_SECRETS_UNAVAILABLE")
    token=access_token(*[os.environ[k] for k in keys])
    folder=ensure_app_folder(token);private_meta(token,folder)
    meta=list_reference(token,folder)
    directory=Path("tf-constant-private");directory.mkdir(mode=0o700,exist_ok=False)
    ref=download_reference(token,meta,directory/"reference.mat")
    receipt={"schema":SCHEMA,"stage":"ACCESS_PREFLIGHT_ONLY_NO_SIMULATION",
      "run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "sourceSHA256":"0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0",
      "reference":ref,"firstOnly":True,"secondEvent":"NOT_COVERED","G5":"BLOCKED"}
    p=directory/("TF_CONSTANT_ACCESS_"+os.environ["GITHUB_RUN_ID"]+".json")
    p.write_text(json.dumps(receipt,indent=2));os.chmod(p,0o600)
    upload_verified(token,folder,p,schema=SCHEMA)
    print("TF_PRIVATE_ACCESS_PREFLIGHT_PASS ownerPrivate=1 referenceSHAReadback=1 receiptUploadReadback=1 simulationRun=0 W96_RERUN=0")
if __name__=="__main__":
    try:main()
    except Exception as exc:
        safe=str(exc)
        if not re.fullmatch(r"[A-Z0-9_]+",safe):safe="TF_PRIVATE_ACCESS_OR_TRANSPORT_UNAVAILABLE"
        print("TF_PRIVATE_GATE_BLOCKED code="+safe+" simulationRun=0")
        sys.exit(1)
