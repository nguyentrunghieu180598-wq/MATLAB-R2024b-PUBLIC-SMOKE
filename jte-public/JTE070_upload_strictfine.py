"""Owner controlled STRICT FINE B0L/C0 MATLAB native raw to private Drive."""
import json,os
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
TRIGGER="JTE070_AUTHORIZE_STRICT_FINE_B0L_C0_2400S"
def guard(event,e,case):
    r=event.get("repository") or {}; commit=event.get("head_commit") or {}
    if case not in ("B0L","C0") or r.get("private") is not False or r.get("full_name")!=EXPECTED_REPO or e.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or e.get("GITHUB_REF")!="refs/heads/main" or e.get("GITHUB_EVENT_NAME")!="push" or commit.get("message")!=TRIGGER:
        raise PermissionError("JTE070_UNAUTHORIZED")
def main():
    e=os.environ;c=e.get("JTE_CASE","");ev=e.get("GITHUB_EVENT_PATH")
    if not ev or not Path(ev).is_file():raise PermissionError("JTE070_EVENT_MISSING")
    guard(json.loads(Path(ev).read_text()),e,c)
    mat=Path("jte070-private")/f"JTE070_{c}_strictfine_2400_NATIVE.mat"
    if not mat.is_file() or mat.is_symlink() or mat.stat().st_size<1000:raise ValueError("JTE070_NATIVE_MAT_MISSING")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(e.get(k) for k in keys):raise RuntimeError("JTE070_OAUTH_NOT_CONFIGURED")
    token=access_token(*[e[k] for k in keys])
    folder=ensure_app_folder(token)
    d=upload_verified(token,folder,mat,schema="JTE070_G5_STRICT_FINE_RAW_UNREVIEWED")
    print("JTE070_STRICT_FINE_PRIVATE_DRIVE_READBACK_PASS case="+c+" bytes="+str(d["size_bytes"])+" sha256="+d["sha256"]+" G5_ACCEPTED=false")
if __name__=="__main__":main()
