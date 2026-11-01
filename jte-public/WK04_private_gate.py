"""WK04 protected nonbattery preflight/publisher. Source only; no workflow enabled.

Future protected CI must invoke `prepare` before MATLAB and `publish` under
`if: always()` afterwards. This module never launches a simulation.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from JTE062_google_drive_synthetic import access_token, ensure_app_folder
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota

ROOT = Path("actuator-review-private")
REPO = "nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"
REF = "refs/heads/codex/wk05-fixture-evidence-gates"
MESSAGE = "WK04_T0_NONBATTERY_ONE_SHOT"
INPUTS = (
    "BTMS_WK04_t0Fixture.m",
    "BTMS_M3_completed.m",
    "BTMS_M3_instrument.m",
    "BTMS_M3_events.m",
    "WK04_private_gate.py",
)
REQUIRED_OUTPUTS = {
    "WK04_PREPARE_GATE.json",
    "WK04_FLAGS.json",
    "WK04_PRIVATE_EVIDENCE.mat",
    "ZERO_PHASE.csv",
    "DIRECT_PHASE.csv",
    "RESTORE_PHASE.csv",
} | {
    f"{run}_NATIVE_{index}.mat"
    for run in ("ZERO", "DIRECT", "RESTORE")
    for index in range(1, 5)
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def context() -> tuple[str, str]:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    assert os.environ.get("GITHUB_REPOSITORY") == REPO
    assert os.environ.get("GITHUB_REF") == REF
    assert os.environ.get("GITHUB_EVENT_NAME") == "push"
    assert os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    assert (event.get("head_commit") or {}).get("id") == os.environ["GITHUB_SHA"]
    assert (event.get("head_commit") or {}).get("message") == MESSAGE
    return os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_SHA"]


def drive():
    token = access_token(
        os.environ["JTE_GOOGLE_CLIENT_ID"],
        os.environ["JTE_GOOGLE_CLIENT_SECRET"],
        os.environ["JTE_GOOGLE_REFRESH_TOKEN"],
    )
    return token, ensure_app_folder(token)


def prepare(run: str, commit: str) -> None:
    token, _ = drive()
    assert quota(token)["availableBytes"] >= 512 * 1024 * 1024
    ROOT.mkdir(mode=0o700, exist_ok=False)
    hashes = {name: sha256(Path("jte-public") / name) for name in INPUTS}
    gate = {
        "sourceKind": "WK04_NONBATTERY",
        "run": run,
        "commit": commit,
        "sourceSHA256": hashes["BTMS_WK04_t0Fixture.m"],
        "inputSHA256": hashes,
        "physicalRun": False,
        "physicalApprovalConsumed": False,
        "outputReadbackVerified": False,
    }
    (ROOT / "WK04_PREPARE_GATE.json").write_text(json.dumps(gate, indent=2))
    print("WK04_PRIVATE_INPUT_SHA_PREFLIGHT_PASS physicalRun=0")


def publish(run: str, commit: str) -> None:
    token, folder = drive()
    assert ROOT.is_dir(), "WK04_PRIVATE_ROOT_MISSING"
    gate_path = ROOT / "WK04_PREPARE_GATE.json"
    gate = json.loads(gate_path.read_text()) if gate_path.is_file() else {}
    post_input_hashes = {
        name: sha256(Path("jte-public") / name) for name in INPUTS
    }
    source_unchanged = gate.get("inputSHA256") == post_input_hashes
    flags_path = ROOT / "WK04_FLAGS.json"
    flags = json.loads(flags_path.read_text()) if flags_path.is_file() else {}
    status = flags.get("status", "UNQUALIFIED_NO_FLAGS")
    same_attempt = (
        gate.get("run") == run
        and gate.get("commit") == commit
        and flags.get("run") == run
        and flags.get("commit") == commit
    )
    matlab_qualified = (
        same_attempt
        and flags.get("MATLAB_API_QUALIFIED") is True
        and status == "MATLAB_API_QUALIFIED_PENDING_PRIVATE_READBACK"
    )
    paths = sorted(p for p in ROOT.iterdir() if p.is_file())
    assert sum(p.stat().st_size for p in paths) <= 128 * 1024 * 1024
    receipt = {
        "run": run,
        "commit": commit,
        "status": status,
        "files": [],
        "emptyPartialFiles": [],
        "physicalRun": False,
        "G5Accepted": False,
        "MATLAB_API_QUALIFIED": matlab_qualified,
        "PRIVATE_TRANSPORT_VERIFIED": False,
        "PHYSICAL_G5_ACCEPTED": False,
        "QUALIFIED_API_FEASIBILITY_ONLY": False,
        "sourceInputsUnchanged": source_unchanged,
        "sameAttempt": same_attempt,
        "requiredPayloadComplete": False,
    }
    for path in paths:
        if path.stat().st_size == 0:
            receipt["emptyPartialFiles"].append(path.name)
            continue
        assert path.stat().st_size <= 64 * 1024 * 1024
        local_sha = sha256(path)
        remote = upload_verified(
            token, folder, path,
            schema="WK04_NONBATTERY_API_ONLY_NOT_G5",
        )
        receipt["files"].append(
            {"name": path.name, "localSHA256": local_sha, "remote": remote}
        )
    receipt["PRIVATE_TRANSPORT_VERIFIED"] = True
    uploaded_names = {item["name"] for item in receipt["files"]}
    receipt["requiredPayloadComplete"] = (
        REQUIRED_OUTPUTS <= uploaded_names
        and not receipt["emptyPartialFiles"]
    )
    receipt["QUALIFIED_API_FEASIBILITY_ONLY"] = bool(
        matlab_qualified
        and source_unchanged
        and same_attempt
        and receipt["requiredPayloadComplete"]
    )
    receipt_path = ROOT / "WK04_PRIVATE_READBACK_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    upload_verified(
        token, folder, receipt_path,
        schema="WK04_NONBATTERY_API_ONLY_NOT_G5",
    )
    assert source_unchanged, "WK04_SOURCE_CHANGED_AFTER_PREFLIGHT"
    assert same_attempt, "WK05_ATTEMPT_PROVENANCE_MISMATCH"
    assert receipt["requiredPayloadComplete"] or not matlab_qualified, (
        "WK05_MATLAB_PASS_WITH_MISSING_PRIVATE_PAYLOAD"
    )
    print(
        "WK05_PRIVATE_TRANSPORT_VERIFIED=1 "
        f"MATLAB_API_QUALIFIED={int(matlab_qualified)} "
        f"QUALIFIED_API_FEASIBILITY_ONLY={int(receipt['QUALIFIED_API_FEASIBILITY_ONLY'])} "
        "PHYSICAL_G5_ACCEPTED=0"
    )


def main() -> None:
    run, commit = context()
    if len(sys.argv) != 2:
        raise ValueError("WK04_MODE_REQUIRED")
    if sys.argv[1] == "prepare":
        prepare(run, commit)
    elif sys.argv[1] == "publish":
        publish(run, commit)
    else:
        raise ValueError("WK04_MODE_DENIED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never print OAuth payloads, private paths, or private MATLAB values.
        print("WK04_PRIVATE_IO_UNQUALIFIED code=" + type(exc).__name__)
        raise SystemExit(1)

