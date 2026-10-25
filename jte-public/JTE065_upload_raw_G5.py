"""JTE065 strictly gated owner-approved G5 RAW case delivery to PRIVATE Drive.

No GitHub public artifacts; no paper and never mark G5 accepted.
Protected main only, commit-specific one-shot, case/profile allowlist.
"""
import json,os
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified

TRIGGER="JTE065_AUTHORIZE_FOUR_INDEPENDENT_2400_CASES"
CASES=("B0L","C0")
PROFILES=("original","fine")

def guard(event, env, case, profile):
    repo=event.get("repository") or {}
    commit=event.get("head_commit") or {}
    if (case not in CASES or profile not in PROFILES or
        repo.get("full_name")!=EXPECTED_REPO or repo.get("private") is not False or
        env.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        env.get("GITHUB_REF")!="refs/heads/main" or
        env.get("GITHUB_EVENT_NAME")!="push" or
        commit.get("message")!=TRIGGER):
        raise PermissionError("JTE065_G5_GUARD_DENIED")

def main():
    case=os.environ.get("JTE_CASE","")
    profile=os.environ.get("JTE_PROFILE","")
    evpath=os.environ.get("GITHUB_EVENT_PATH")
    if not evpath or not Path(evpath).is_file():
        raise PermissionError("JTE065_G5_EVENT_MISSING")
    guard(json.loads(Path(evpath).read_text()),os.environ,case,profile)
    p=Path("jte065-private")/f"JTE065_{case}_{profile}_2400_NATIVE.mat"
    if not p.is_file() or p.is_symlink() or p.stat().st_size<1000:
        raise RuntimeError("JTE065_NATIVE_MAT_ABSENT")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(x) for x in keys):
        raise RuntimeError("JTE065_MISSING_OAUTH_SECRETS")
    token=access_token(*[os.environ[k] for k in keys])
    folder=ensure_app_folder(token)
    result=upload_verified(token,folder,p,schema="JTE065_G5_RAW_UNREVIEWED")
    print("JTE065_RAW_G5_PRIVATE_DRIVE_READBACK_PASS"
       +" case="+case+" profile="+profile
       +" bytes="+str(result["size_bytes"])+" sha256="+result["sha256"]
       +" G5_ACCEPTED=false BIAS_K=0")
if __name__=="__main__":main()
