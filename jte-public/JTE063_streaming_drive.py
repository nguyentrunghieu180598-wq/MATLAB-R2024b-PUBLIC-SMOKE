"""JTE063 staging: chunked confidential MAT transport into app-owned private Drive.

NO GitHub Actions workflow enables study data yet. This module is offline
testable, and MUST NOT be installed into a public MAT-upload job until:
  (1) OAuth token/Client Secret shown in chat screenshots are revoked/rotated,
  (2) owner explicitly approves that exact credentialed workflow,
  (3) Drive free space and real large-file resumable test pass,
  (4) every source/physics/G5 gate is independently accepted.
Upload is PENDING until streaming Drive readback SHA256 succeeds. A crashed
runner before upload finishes can still lose its scratch result.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from JTE062_google_drive_synthetic import API, access_token, ensure_app_folder

CHUNK = 8 * 1024 * 1024
MAX_BYTES = 4 * 1024**3
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,size,md5Checksum"
TRANSIENT = {408,429,500,502,503,504}
RETRY_LIMIT = 3


def _valid_session(url: str):
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https" and p.hostname == "www.googleapis.com"
        and p.path == "/upload/drive/v3/files"
        and p.username is None and p.password is None
        and p.port is None
    )


def parse_range(range_header: str | None, total: int) -> int:
    """Next byte after Google 308 Range: bytes=0-N, or 0 if absent."""
    if range_header is None:
        return 0
    match = re.fullmatch(r"bytes=0-(\d+)",range_header)
    if not match:
        raise ValueError("JTE063_INVALID_RESUME_RANGE")
    end = int(match.group(1))
    if end < 0 or end >= total:
        raise ValueError("JTE063_RESUME_RANGE_OUT_OF_BOUNDS")
    return end+1


def sha_file(path: Path) -> tuple[int,str,str]:
    path=Path(path)
    if not path.is_file() or path.is_symlink() or not re.fullmatch(r"[A-Za-z0-9_.-]+",path.name):
        raise ValueError("JTE063_INVALID_LOCAL_FILE")
    stat=path.stat()
    if stat.st_size <= 0 or stat.st_size > MAX_BYTES:
        raise ValueError("JTE063_UNSUPPORTED_FILE_SIZE")
    h=hashlib.sha256(); md5=hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        while True:
            data=f.read(CHUNK)
            if not data: break
            h.update(data); md5.update(data)
    if stat.st_size!=path.stat().st_size:
        raise RuntimeError("JTE063_INPUT_CHANGED_WHILE_HASHING")
    return stat.st_size,h.hexdigest(),md5.hexdigest()


def _http(url, *, method="GET", bearer=None, data=None, headers=None, timeout=120):
    reqheaders=dict(headers or {})
    if bearer is not None:
        reqheaders["Authorization"]="Bearer "+bearer
    request=urllib.request.Request(url,method=method,headers=reqheaders,data=data)
    try:
        with urllib.request.urlopen(request,timeout=timeout) as result:
            return result.status,dict(result.headers),result.read()
    except urllib.error.HTTPError as error:
        if error.code in (308,*TRANSIENT):
            return error.code,dict(error.headers),b""
        raise RuntimeError("JTE063_GOOGLE_HTTP_"+str(error.code)) from None
    except urllib.error.URLError:
        return 503,{},b""


def _session(token,folder,name,total,sha256,schema="SYNTHETIC_PREFLIGHT"):
    doc={"name":"JTE063_PENDING_"+name,"parents":[folder],
         "mimeType":"application/octet-stream",
         "appProperties":{"jte_schema":schema,"state":"PENDING","sha256":sha256}}
    status,headers,_=_http(UPLOAD,method="POST",bearer=token,
         data=json.dumps(doc).encode(),headers={
           "Content-Type":"application/json; charset=UTF-8",
           "X-Upload-Content-Type":"application/octet-stream",
           "X-Upload-Content-Length":str(total)})
    url=headers.get("Location",headers.get("location",""))
    if status != 200 or not _valid_session(url):
        raise RuntimeError("JTE063_SESSION_INIT_FAILED")
    return url


def _probe(url,total):
    status,headers,_=_http(url,method="PUT",data=b"",headers={
       "Content-Length":"0","Content-Range":f"bytes */{total}"})
    if status==308:
        return parse_range(headers.get("Range",headers.get("range")),total)
    raise RuntimeError("JTE063_UNCERTAIN_UPLOAD_STATE")


def upload_chunks(path, session_url, total):
    """Streaming upload. Only returns remote metadata after final 200/201."""
    if not _valid_session(session_url):
        raise RuntimeError("JTE063_UNTRUSTED_SESSION")
    offset=0
    with Path(path).open("rb") as f:
        while offset<total:
            f.seek(offset)
            payload=f.read(min(CHUNK,total-offset))
            if not payload:
                raise RuntimeError("JTE063_EARLY_EOF")
            end=offset+len(payload)-1
            done=False
            for trial in range(RETRY_LIMIT):
                status,headers,body=_http(session_url,method="PUT",data=payload,headers={
                    "Content-Type":"application/octet-stream",
                    "Content-Length":str(len(payload)),
                    "Content-Range":f"bytes {offset}-{end}/{total}"})
                if status in (200,201):
                    if end!=total-1:
                        raise RuntimeError("JTE063_PREMATURE_FINAL_COMMIT")
                    result=json.loads(body)
                    if not result.get("id") or int(result.get("size",-1))!=total:
                        raise RuntimeError("JTE063_REMOTE_SIZE_MISMATCH")
                    return result
                if status==308:
                    nextoffset=parse_range(headers.get("Range",headers.get("range")),total)
                    if nextoffset<=offset or nextoffset>end+1:
                        raise RuntimeError("JTE063_RESUME_PROGRESS_INVALID")
                    offset=nextoffset
                    done=True;break
                if status not in TRANSIENT:
                    raise RuntimeError("JTE063_CHUNK_UPLOAD_FAILED")
                # A timeout may have actually written bytes: never blindly resend
                # before querying accepted range from this SAME session.
                time.sleep(min(2**trial,4))
                try:
                    nextoffset=_probe(session_url,total)
                except RuntimeError:
                    continue
                if nextoffset<offset or nextoffset>end+1:
                    raise RuntimeError("JTE063_RESUME_PROGRESS_INVALID")
                if nextoffset>offset:
                    offset=nextoffset;done=True;break
            if not done:
                raise RuntimeError("JTE063_RETRIES_EXHAUSTED")
    raise RuntimeError("JTE063_UPLOAD_NOT_COMMITTED")


def readback_sha(token,file_id,total):
    req=urllib.request.Request(API+"/"+urllib.parse.quote(file_id,safe="")+"?alt=media",
          headers={"Authorization":"Bearer "+token})
    h=hashlib.sha256();n=0
    try:
        with urllib.request.urlopen(req,timeout=180) as response:
            while True:
                data=response.read(CHUNK)
                if not data:break
                h.update(data);n+=len(data)
                if n>total:raise RuntimeError("JTE063_READBACK_OVERSIZED")
    except urllib.error.HTTPError as e:
        raise RuntimeError("JTE063_READBACK_HTTP_"+str(e.code)) from None
    if n!=total:
        raise RuntimeError("JTE063_READBACK_SIZE_MISMATCH")
    return h.hexdigest()


def upload_verified(token,folder,path,*,schema="SYNTHETIC_PREFLIGHT"):
    """Fail closed until content-complete private readback; no stdout secrets."""
    path=Path(path)
    if schema not in {'BTMS_TOY_AND_BASELINE_FEASIBILITY_NOT_G5','BTMS_ACTUATOR_METHOD_AMENDMENT_STATIC_ONLY','JTE116_OWNER_APPROVED_ONE_GUARD025_NOT_G5','SYNTHETIC_PREFLIGHT','JTE056_DIAGNOSTIC20_NOT_G5','JTE065_G5_RAW_UNREVIEWED','JTE067_G6_MINUS2K_RAW_UNREVIEWED','JTE068_ACTIVE_C0_RAW_UNREVIEWED','JTE069_ACTIVE_G6_RAW_UNREVIEWED','JTE070_G5_STRICT_FINE_RAW_UNREVIEWED','JTE072_GROUP3_RAW_UNREVIEWED','TF_CONSTANT_INPUT_DIAGNOSTIC_340_NOT_G5','JTE101_BOUNDED_TF_DIAGNOSTIC_NOT_G5','JTE102_PRIVATE_AUDIT_NOT_G5','JTE103_PROFILER_PATH_NOT_G5','JTE106_NATIVE_CORE_AUDIT_NOT_G5','JTE107_PRIVATE_MECHANISM_LEDGER_NOT_G5','JTE108_PRIVATE_CRITICAL_BIAS_NOT_G5','JTE111_PRIVATE_G5_EVIDENCE_NOT_ACCEPTANCE','JTE112_CONDITIONAL_PHYSICAL_ENVELOPE_NOT_G5','JTE113_ONE_SOURCE_NUMERICAL_DISCRIMINATOR_NOT_G5','JTE115_SOURCE_EQUIVALENT_GUARD_NOT_G5','JTE116_GUARD025_CANARY_STATIC_ONLY_NOT_G5'}:
        raise ValueError('JTE063_UNKNOWN_SCHEMA')
    size,sha,md5=sha_file(path)
    url=_session(token,folder,path.name,size,sha,schema)
    metadata=upload_chunks(path,url,size)
    if metadata.get("md5Checksum")!=md5:
        raise RuntimeError("JTE063_REMOTE_MD5_MISMATCH")
    received=readback_sha(token,metadata["id"],size)
    if received!=sha:
        raise RuntimeError("JTE063_READBACK_SHA_MISMATCH")
    body=json.dumps({"name":"JTE063_VERIFIED_"+path.name,
         "appProperties":{"jte_schema":schema,"state":"VERIFIED","sha256":sha}}).encode()
    status,_,_=_http(API+"/"+urllib.parse.quote(metadata["id"],safe="")+"?fields=id",
         method="PATCH",bearer=token,data=body,headers={"Content-Type":"application/json"})
    if status!=200:
        raise RuntimeError("JTE063_VERIFY_COMMIT_FAILED")
    return {"size_bytes":size,"sha256":sha,"integrity":"FULL_REMOTE_READBACK_VERIFIED"}
