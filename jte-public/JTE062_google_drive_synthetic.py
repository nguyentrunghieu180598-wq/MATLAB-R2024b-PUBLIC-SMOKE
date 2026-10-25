"""JTE062 private Google Drive synthetic upload pilot from a PUBLIC Actions runner.

SYNTHETIC 1 MiB only. Does NOT touch MATLAB study files or public artifacts.
Uses Drive scope drive.file (app-created folder and files only).
Works without third-party packages, stores no long-term tokens on disk.

This is a preflight. BEFORE production full MAT support, separately audit
chunked-resumable uploads, cancel/resume, account quota, and SHA readback.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

EXPECTED_REPO = "nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DRIVE_FOLDER_NAME = "JTE_BTMS_PRIVATE_API_RESULTS"
MIME_FOLDER = "application/vnd.google-apps.folder"
TEST_BYTES = 1048576
API = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id%2Cname%2Csize%2Cmd5Checksum"
TOKEN = "https://oauth2.googleapis.com/token"


def synthetic_payload():
    b = b"JTE062-SYNTHETIC-DRIVE-TRANSPORT-NO-MODEL-DATA\\n"
    return (b * (TEST_BYTES // len(b) + 1))[:TEST_BYTES]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def assert_synthetic_and_manual(event, repository, ref, event_name):
    r = event.get("repository", {})
    if not isinstance(r, dict) or r.get("full_name") != EXPECTED_REPO or repository != EXPECTED_REPO:
        raise PermissionError("WRONG_REPOSITORY")
    if ref != "refs/heads/main" or event_name != "workflow_dispatch":
        raise PermissionError("REQUIRES_TRUSTED_MAIN_MANUAL_DISPATCH")
    if r.get("private") is not False:
        raise PermissionError("UNEXPECTED_VISIBILITY")
    return True


def req(url, *, method="GET", token=None, data=None, extra=None, timeout=60):
    headers = dict(extra or {})
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        # No request body/headers, bearer, refresh token or response text logged.
        raise RuntimeError("GOOGLE_API_HTTP_" + str(e.code)) from None
    except urllib.error.URLError:
        raise RuntimeError("GOOGLE_API_TRANSPORT_FAILED") from None


def access_token(client_id, client_secret, refresh_token):
    params = urllib.parse.urlencode({
        "grant_type":"refresh_token", "client_id":client_id,
        "client_secret":client_secret, "refresh_token":refresh_token,
    }).encode("ascii")
    status, _, data = req(TOKEN, method="POST", data=params,
        extra={"Content-Type":"application/x-www-form-urlencoded"}, timeout=40)
    response = json.loads(data)
    if status != 200 or not response.get("access_token"):
        raise RuntimeError("OAUTH_REFRESH_FAILED")
    # Never print, save or persist this token.
    return response["access_token"]


def ensure_app_folder(token):
    # Scope drive.file returns app-created files, not arbitrary existing folders.
    filt = "name = '" + DRIVE_FOLDER_NAME + "' and mimeType = '" + MIME_FOLDER + "' and trashed = false"
    query=urllib.parse.urlencode({"q":filt,"fields":"nextPageToken,files(id,name,mimeType)",
       "pageSize":"100","spaces":"drive"})
    _, _, body=req(API+"?"+query,token=token)
    payload=json.loads(body)
    files=payload.get("files",[])
    if payload.get("nextPageToken") or len(files)>1:
        raise RuntimeError("AMBIGUOUS_APP_FOLDER")
    if len(files)==1:
        return files[0]["id"]
    metadata=json.dumps({"name":DRIVE_FOLDER_NAME,"mimeType":MIME_FOLDER}).encode()
    _, _, data=req(API+"?fields=id",method="POST",token=token,data=metadata,
        extra={"Content-Type":"application/json; charset=UTF-8"})
    folder=json.loads(data).get("id")
    if not folder:
        raise RuntimeError("FOLDER_CREATE_FAILED")
    return folder


def upload_synthetic(token, parent, binary, run_id):
    # Test-only, one shot 1-MiB resumable upload. No real MAT supported here.
    name="JTE062_INCOMPLETE_SYNTHETIC_"+run_id+".bin"
    metadata=json.dumps({"name":name,"parents":[parent],
        "mimeType":"application/octet-stream",
        "appProperties":{"jte":"synthetic-only","sha256":digest(binary)}}).encode()
    _, headers,_=req(UPLOAD,method="POST",token=token,data=metadata,extra={
        "Content-Type":"application/json; charset=UTF-8",
        "X-Upload-Content-Type":"application/octet-stream",
        "X-Upload-Content-Length":str(len(binary)),
    })
    location=headers.get("Location") or headers.get("location")
    if not location or not location.startswith("https://www.googleapis.com/"):
        raise RuntimeError("RESUMABLE_SESSION_MISSING")
    status,_,body=req(location,method="PUT",data=binary,extra={
        "Content-Type":"application/octet-stream",
        "Content-Length":str(len(binary)),
        "Content-Range":"bytes 0-"+str(len(binary)-1)+"/"+str(len(binary)),
    },timeout=120)
    if status not in (200,201):
        raise RuntimeError("RESUMABLE_NOT_COMMITTED")
    data=json.loads(body)
    if not data.get("id") or int(data.get("size",-1))!=len(binary):
        raise RuntimeError("UPLOAD_SIZE_NOT_VERIFIED")
    return data["id"]


def verify_download(token, file_id, expected):
    _,_,payload=req(API+"/"+urllib.parse.quote(file_id,safe="")+"?alt=media",
        token=token,timeout=120)
    if len(payload)!=len(expected) or digest(payload)!=digest(expected):
        raise RuntimeError("PRIVATE_DRIVE_READBACK_SHA_MISMATCH")
    return digest(payload)


def mark_verified(token, file_id, run_id):
    body=json.dumps({"name":"JTE062_VERIFIED_SYNTHETIC_"+run_id+".bin"}).encode()
    req(API+"/"+urllib.parse.quote(file_id,safe="")+"?fields=id",token=token,
        method="PATCH",data=body,extra={"Content-Type":"application/json"})


def main():
    event_path=os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).is_file():
        raise PermissionError("MISSING_SIGNED_RUN_CONTEXT")
    event=json.loads(Path(event_path).read_text())
    assert_synthetic_and_manual(event,os.environ.get("GITHUB_REPOSITORY",""),
                                os.environ.get("GITHUB_REF",""),
                                os.environ.get("GITHUB_EVENT_NAME",""))
    run_id=os.environ.get("GITHUB_RUN_ID","")
    if not run_id.isdigit():
        raise RuntimeError("INVALID_RUN_ID")
    names=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in names):
        raise RuntimeError("MISSING_ENVIRONMENT_SECRETS")
    token=access_token(*[os.environ[n] for n in names])
    folder=ensure_app_folder(token)
    test=synthetic_payload()
    fid=upload_synthetic(token,folder,test,run_id)
    result=verify_download(token,fid,test)
    mark_verified(token,fid,run_id)
    print("JTE062_SYNTHETIC_PRIVATE_DRIVE_READBACK_PASS bytes="
          +str(len(test))+" sha256="+result+" no_raw_study_data=true")
    # Never log folder ID, file ID, bearer or refresh tokens.


if __name__=="__main__":
    main()
