"""JTE065: 192MiB synthetic streamed Drive endurance preflight.

Permits only exact named owner-authorized push to main, private Drive
environment and no actual study data. Exercises 24 full 8MiB chunks.
"""
import json, os, tempfile
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified,CHUNK

TRIGGER="JTE065_RUN_ONCE_PRIVATE_DRIVE_192MIB_SYNTHETIC_PREFLIGHT"
BYTES=192*1024*1024

def guard(event,env):
    repo=event.get("repository") or {}
    head=event.get("head_commit") or {}
    if not (repo.get("full_name")==EXPECTED_REPO and repo.get("private") is False
        and env.get("GITHUB_REPOSITORY")==EXPECTED_REPO
        and env.get("GITHUB_EVENT_NAME")=="push"
        and env.get("GITHUB_REF")=="refs/heads/main"
        and head.get("message")==TRIGGER):
        raise PermissionError("JTE065_DENIED_CONTEXT")

def main():
    p=os.environ.get("GITHUB_EVENT_PATH")
    if not p or not Path(p).is_file():
        raise PermissionError("JTE065_MISSING_CONTEXT")
    guard(json.loads(Path(p).read_text()),os.environ)
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):
        raise RuntimeError("JTE065_MISSING_SECRETS")
    token=access_token(*[os.environ[k] for k in keys])
    folder=ensure_app_folder(token)
    with tempfile.TemporaryDirectory(prefix="jte065-synth-") as d:
        path=Path(d)/"JTE065_SYNTHETIC_192MIB.bin"
        block=b"JTE065-SYNTHETIC-CAPACITY-PREFLIGHT-NO-MAT-NO-STUDY-DATA\n"
        remaining=BYTES
        with path.open("wb") as out:
            while remaining:
                n=min(CHUNK,remaining)
                out.write((block*(n//len(block)+1))[:n])
                remaining-=n
        receipt=upload_verified(token,folder,path,schema="SYNTHETIC_PREFLIGHT")
        if receipt["size_bytes"]!=BYTES:
            raise RuntimeError("JTE065_PRECHECK_SIZE")
        print("JTE065_192MIB_PRIVATE_DRIVE_PASS bytes="+str(BYTES)
            +" sha256="+receipt["sha256"]+" no_battery_data=true")
if __name__=="__main__":
    main()
