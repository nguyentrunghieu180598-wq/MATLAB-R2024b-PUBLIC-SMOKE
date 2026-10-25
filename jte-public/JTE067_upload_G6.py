"""Private G6 raw MAT transfer only after user-authorized guarded push."""
import json,os
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified

TRIGGER="JTE067_AUTHORIZE_THREE_SINGLE_CHANNEL_MINUS2K_CASES"
POSITIONS=("hot","middle","cold")

def guard(event,env,position):
    repo=event.get("repository") or {}
    head=event.get("head_commit") or {}
    if (position not in POSITIONS or repo.get("private") is not False
        or repo.get("full_name")!=EXPECTED_REPO
        or env.get("GITHUB_REPOSITORY")!=EXPECTED_REPO
        or env.get("GITHUB_REF")!="refs/heads/main"
        or env.get("GITHUB_EVENT_NAME")!="push"
        or head.get("message")!=TRIGGER):
        raise PermissionError("JTE067_UNAUTHORIZED_G6")

def main():
    pos=os.environ.get("JTE_POSITION","")
    eventfile=os.environ.get("GITHUB_EVENT_PATH","")
    if not eventfile or not Path(eventfile).is_file():
        raise PermissionError("JTE067_MISSING_EVENT")
    guard(json.loads(Path(eventfile).read_text()),os.environ,pos)
    mat=Path("jte067-private")/f"JTE067_C1_{pos}_original_2400_NATIVE.mat"
    if not mat.is_file() or mat.is_symlink() or mat.stat().st_size<1000:
        raise RuntimeError("JTE067_G6_MAT_ABSENT")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):
        raise RuntimeError("JTE067_MISSING_OAUTH")
    token=access_token(*[os.environ[k] for k in keys])
    folder=ensure_app_folder(token)
    receipt=upload_verified(token,folder,mat,schema="JTE067_G6_MINUS2K_RAW_UNREVIEWED")
    print("JTE067_G6_PRIVATE_DRIVE_READBACK_PASS pos="+pos
        +" bytes="+str(receipt["size_bytes"])+" sha256="+receipt["sha256"]
        +" accepted=false bias=-2K single_channel=true")
if __name__=="__main__":main()
