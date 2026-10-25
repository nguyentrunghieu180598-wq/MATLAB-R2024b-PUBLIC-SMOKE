"""JTE063 synthetic-only 20 MiB REAL Google Drive multi-chunk preflight.

Guarded main-only and single named commit. No model MAT, no research data,
no public artifact. The fixture is discarded locally on run completion.
"""
from pathlib import Path
import json
import os
import tempfile

from JTE062_google_drive_synthetic import (
    EXPECTED_REPO,access_token,ensure_app_folder,
)
from JTE063_streaming_drive import CHUNK,upload_verified

MAGIC = "JTE063_RUN_ONCE_OWNER_APPROVED_SYNTHETIC_20MIB"
BYTES = 20*1024*1024


def assert_one_shot(event,environ):
    repo=event.get("repository") or {}
    commit=event.get("head_commit") or {}
    if (repo.get("full_name")!=EXPECTED_REPO or repo.get("private") is not False or
        environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        environ.get("GITHUB_REF")!="refs/heads/main" or
        environ.get("GITHUB_EVENT_NAME")!="push" or
        commit.get("message")!=MAGIC):
        raise PermissionError("JTE063_INVALID_ONE_SHOT_RUN_CONTEXT")


def main():
    eventpath=os.environ.get("GITHUB_EVENT_PATH")
    if not eventpath or not Path(eventpath).is_file():
        raise PermissionError("JTE063_MISSING_RUN_EVENT")
    assert_one_shot(json.loads(Path(eventpath).read_text()),os.environ)
    names=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(os.environ.get(x) for x in names):
        raise RuntimeError("JTE063_MISSING_ENVIRONMENT_SECRETS")
    token=access_token(*[os.environ[x] for x in names])
    folder=ensure_app_folder(token)
    with tempfile.TemporaryDirectory(prefix="jte063-") as td:
        file=Path(td)/"JTE063_SYNTHETIC_20MIB.bin"
        block=b"JTE063-SYNTHETIC-CHUNK-TRANSPORT-NO-BATTERY-DATA\n"
        remaining=BYTES
        with file.open("wb") as f:
            while remaining>0:
                data=(block * (min(CHUNK,remaining)//len(block)+1))[:min(CHUNK,remaining)]
                f.write(data);remaining-=len(data)
        info=upload_verified(token,folder,file)
        if info["size_bytes"]!=BYTES:
            raise RuntimeError("JTE063_LARGE_SYNTHETIC_SIZE_MISMATCH")
        print("JTE063_PRIVATE_20MIB_CHUNKED_READBACK_PASS "+
              "bytes="+str(info["size_bytes"])+" sha256="+info["sha256"]+
              " real_model_data=false")
    # Do not print OAuth data, file or folder IDs.


if __name__=="__main__":
    main()
