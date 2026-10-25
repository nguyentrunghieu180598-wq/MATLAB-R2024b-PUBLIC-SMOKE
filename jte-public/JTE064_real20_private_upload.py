"""JTE064 one-shot 20-second real R2024b native MAT -> private Drive.

C0 bias=0 diagnostic ONLY, not a G5 result. Runs under protected main
environment; this module NEVER uses public GitHub artifacts or writes tokens
to logs. Requires owner-approved fresh secrets. Self-contained run guard
rejects pull requests and random pushes.
"""
import json
import os
from pathlib import Path

from JTE062_google_drive_synthetic import EXPECTED_REPO, access_token, ensure_app_folder
from JTE063_streaming_drive import upload_verified

TRIGGER = "JTE064_RUN_ONCE_REAL_R2024B_DIAGNOSTIC20_TO_PRIVATE_DRIVE"
FILE = "jte056-private/JTE056_NATIVE_LOGGER_REPAIR_20S.mat"


def guard(event, env):
    repo=event.get("repository") or {}
    commit=event.get("head_commit") or {}
    if (repo.get("full_name")!=EXPECTED_REPO or repo.get("private") is not False
        or env.get("GITHUB_REPOSITORY")!=EXPECTED_REPO
        or env.get("GITHUB_REF")!="refs/heads/main"
        or env.get("GITHUB_EVENT_NAME")!="push"
        or commit.get("message")!=TRIGGER):
        raise PermissionError("JTE064_NOT_TRUSTED_ONE_SHOT_DIAGNOSTIC")


def main():
    evpath=os.environ.get("GITHUB_EVENT_PATH")
    if not evpath or not Path(evpath).is_file():
        raise RuntimeError("JTE064_MISSING_GITHUB_EVENT")
    guard(json.loads(Path(evpath).read_text()),os.environ)
    path=Path(FILE)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>128*1024**2:
        raise RuntimeError("JTE064_DIAGNOSTIC_FILE_MISSING_OR_TOO_LARGE")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):
        raise RuntimeError("JTE064_ENV_SECRETS_MISSING")
    token=access_token(*[os.environ[k] for k in keys])
    folder=ensure_app_folder(token)
    evidence=upload_verified(token,folder,path,schema="JTE056_DIAGNOSTIC20_NOT_G5")
    print("JTE064_REAL_MATLAB_DIAGNOSTIC20_PRIVATE_DRIVE_READBACK_PASS"
        +" bytes="+str(evidence["size_bytes"])+" sha256="+evidence["sha256"]
        +" not_G5=true native_312_verified_by_MATLAB=true")
    # NEVER print Google file IDs, credentials, MAT values, or pin physics claims.


if __name__=="__main__":
    main()
