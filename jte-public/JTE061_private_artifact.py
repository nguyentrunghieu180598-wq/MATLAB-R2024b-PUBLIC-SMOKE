"""JTE061: permission-gated PRIVATE GitHub artifact transport (synthetic only).

Run this only inside a *private* GitHub repository and via manual
workflow_dispatch. Does not read, simulate, encrypt, decrypt, or upload any
battery data. No credentials are read.  No RSA private key exists here.

A private GitHub Actions artifact is a temporary private *transport*,
NOT a substitute for immutable owner-controlled Drive archival and G5 review.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import zipfile

PAYLOAD_NAME = "synthetic_fixture.bin"
MANIFEST_NAME = "manifest.json"
SYNTH_SIZE = 1_048_576


def assert_private_context(event: dict, repository: str, event_name: str, visibility: str | None = None):
    r = event.get("repository", {})
    if event_name != "workflow_dispatch":
        raise PermissionError("PRIVATE_ARTIFACT_NOT_MANUAL_DISPATCH")
    if not isinstance(r, dict) or r.get("private") is not True:
        raise PermissionError("PRIVATE_ARTIFACT_DENIED_PUBLIC_OR_UNKNOWN_REPOSITORY")
    if not repository or r.get("full_name") != repository:
        raise PermissionError("PRIVATE_ARTIFACT_REPOSITORY_IDENTITY_MISMATCH")
    # GitHub sometimes leaves visibility out of events, but if provided it
    # must agree with the boolean private marker.
    if r.get("visibility") not in (None, "private") or visibility not in (None, "", "private"):
        raise PermissionError("PRIVATE_ARTIFACT_VISIBILITY_MISMATCH")
    return True


def synthetic_bytes(size: int = SYNTH_SIZE) -> bytes:
    # Constant deterministic fixture. NOT model data; no user information.
    return (b"JTE061-SYNTHETIC-TRANSPORT-NO-STUDY-DATA\\n" * (size // 43 + 1))[:size]


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def make_fixture(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    payload = synthetic_bytes()
    manifest = {
        "schema": "JTE061_SYNTHETIC_PRIVATE_ARTIFACT_V1",
        "synthetic_only": True,
        "payload": PAYLOAD_NAME,
        "bytes": len(payload),
        "sha256": sha256(payload),
        "no_model_data": True,
        "not_g5": True,
        "no_rsa_scratch_needed": True,
    }
    (directory / PAYLOAD_NAME).write_bytes(payload)
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_extracted(directory: Path) -> dict:
    manifest = json.loads((directory / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("schema") != "JTE061_SYNTHETIC_PRIVATE_ARTIFACT_V1" or manifest.get("synthetic_only") is not True:
        raise ValueError("Unrecognized or non-synthetic artifact")
    if manifest.get("payload") != PAYLOAD_NAME or manifest.get("no_model_data") is not True:
        raise ValueError("Wrong payload contract")
    payload = (directory / PAYLOAD_NAME).read_bytes()
    if len(payload) != manifest["bytes"] or sha256(payload) != manifest["sha256"]:
        raise ValueError("Byte size or SHA256 mismatch")
    return manifest


def verify_zip(artifact_zip: Path) -> dict:
    # GitHub upload-artifact ZIP typically contains files at artifact root.
    with zipfile.ZipFile(artifact_zip) as z:
        if set(z.namelist()) != {PAYLOAD_NAME, MANIFEST_NAME}:
            raise ValueError("Unexpected ZIP payload files")
        if any(i.is_dir() or i.file_size > SYNTH_SIZE * 2 for i in z.infolist()):
            raise ValueError("ZIP archive invalid or oversized")
        m = json.loads(z.read(MANIFEST_NAME))
        if m.get("schema") != "JTE061_SYNTHETIC_PRIVATE_ARTIFACT_V1" or m.get("synthetic_only") is not True:
            raise ValueError("Unrecognized synthetic manifest")
        payload = z.read(PAYLOAD_NAME)
        if len(payload) != m["bytes"] or sha256(payload) != m["sha256"]:
            raise ValueError("ZIP payload size/hash mismatch")
        return m


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["make", "verify"])
    p.add_argument("--dir", default="jte061-artifact-out")
    args = p.parse_args()
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).is_file():
        raise PermissionError("PRIVATE_ARTIFACT_REQUIRES_GITHUB_EVENT")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    assert_private_context(
        event, os.environ.get("GITHUB_REPOSITORY", ""),
        os.environ.get("GITHUB_EVENT_NAME", ""),
        os.environ.get("GITHUB_REPOSITORY_VISIBILITY"),
    )
    root = Path(args.dir)
    result = make_fixture(root) if args.action == "make" else verify_extracted(root)
    # Only synthetic metadata may enter logs; NEVER print future MAT values.
    print("JTE061_PRIVATE_SYNTHETIC_" + args.action.upper() + "_PASS "
          + "bytes=" + str(result["bytes"]) + " sha256=" + result["sha256"] +
          " no_rsa_scratch=true no_study_data=true")


if __name__ == "__main__":
    main()
