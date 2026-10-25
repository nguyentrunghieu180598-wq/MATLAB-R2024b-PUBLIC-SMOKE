"""JTE068 isolated ambient-reference trial, NOT original G5/G6 data."""
import json,os
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified

TRIGGER="JTE068_AUTHORIZE_SEPARATE_20C_AMBIENT_CONTROL_ACTIVATION"

def guard(event,env):
    repo=event.get("repository") or {}
    c=event.get("head_commit") or {}
    if not (repo.get("full_name")==EXPECTED_REPO and repo.get("private") is False
     and env.get("GITHUB_REPOSITORY")==EXPECTED_REPO
     and env.get("GITHUB_REF")=="refs/heads/main" and env.get("GITHUB_EVENT_NAME")=="push"
     and c.get("message")==TRIGGER):
        raise PermissionError("JTE068_DENIED_CONTEXT")

def main():
    ep=os.environ.get("GITHUB_EVENT_PATH")
    if not ep or not Path(ep).is_file():raise PermissionError("JTE068_NO_EVENT")
    guard(json.loads(Path(ep).read_text()),os.environ)
    path=Path("jte068-private/JTE068_ACTIVE_C0_AMBIENT293p15_2400_NATIVE.mat")
    if not path.is_file() or path.is_symlink() or path.stat().st_size<1000:
        raise RuntimeError("JTE068_REAL_MAT_MISSING")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(x) for x in keys):
        raise RuntimeError("JTE068_NO_OAUTH")
    token=access_token(*[os.environ[x] for x in keys])
    folder=ensure_app_folder(token)
    v=upload_verified(token,folder,path,schema="JTE068_ACTIVE_C0_RAW_UNREVIEWED")
    print("JTE068_ACTIVE_C0_PRIVATE_DRIVE_READBACK_PASS bytes="+str(v["size_bytes"])
       +" sha256="+v["sha256"]+" active_status_unreviewed=true")
if __name__=="__main__": main()
