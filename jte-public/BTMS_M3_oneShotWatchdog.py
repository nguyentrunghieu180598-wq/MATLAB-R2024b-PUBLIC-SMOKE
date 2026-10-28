#!/usr/bin/env python3
"""Owner-gated, one-shot external watchdog for M3 B0L10ms/340s.
Engineering code ONLY. Never starts without an explicit approval token.
It cannot validate physical states, file clocks or G5 and never retries.
Python 3 stdlib; run command after '--'. All receipts stay owner-private.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

GiB = 1024**3
MiB = 1024**2
APPROVAL = "APPROVE_SINGLE_B0L10MS_0_TO_340"
REPO = "nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def mem_available():
    with open("/proc/meminfo", encoding="ascii") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("HOST_AVAILABLE_RAM_UNAVAILABLE")

def cgroup_free():
    root = Path("/sys/fs/cgroup")
    mx, cur = root / "memory.max", root / "memory.current"
    if not (mx.exists() and cur.exists()):
        return None
    cap = mx.read_text().strip()
    if cap == "max":
        return None
    return int(cap) - int(cur.read_text().strip())

def caps(folder, files, drive_free):
    if mem_available() < 2 * GiB:
        return "HOST_RAM_RESERVE"
    cf = cgroup_free()
    if cf is not None and cf < 2 * GiB:
        return "CGROUP_RAM_RESERVE"
    if shutil.disk_usage(folder).free < 2 * GiB:
        return "SCRATCH_DISK_RESERVE"
    if drive_free < 2 * GiB + 512 * MiB:
        return "DRIVE_DELIVERY_RESERVE"
    sizes = [p.stat().st_size if p.exists() else 0 for p in files]
    if any(s > GiB for s in sizes):
        return "NATIVE_SINGLE_FILE_CAP"
    if sum(sizes) > 2 * GiB:
        return "NATIVE_TOTAL_FILE_CAP"
    return None

def receipt(folder, payload):
    tmp = folder / "m3_watchdog_receipt.json.partial"
    final = folder / "m3_watchdog_receipt.json"
    with open(tmp, "x", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)
    os.replace(tmp, final)

def terminate_group(proc):
    if proc.poll() is not None:
        return
    for sig, grace in ((signal.SIGINT, 5), (signal.SIGTERM, 5), (signal.SIGKILL, 0)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        if not grace:
            break
        try:
            proc.wait(timeout=grace)
            break
        except subprocess.TimeoutExpired:
            continue
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--model-sha256", required=True)
    ap.add_argument("--private-dir", required=True)
    ap.add_argument("--native-file", action="append", required=True)
    ap.add_argument("--drive-free-bytes", type=int, required=True)
    ap.add_argument("--wall-ceiling-s", type=int, default=1200)
    ap.add_argument("command", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
    folder = Path(a.private_dir).resolve(strict=True)
    model = Path(a.model).resolve(strict=True)
    files = [Path(p).resolve() for p in a.native_file]
    if os.environ.get("BTMS_M3_OWNER_APPROVAL", "") != APPROVAL:
        raise RuntimeError("OWNER_PHYSICAL_APPROVAL_REQUIRED")
    if os.environ.get("GITHUB_REPOSITORY") != REPO or \
       os.environ.get("GITHUB_REF") != "refs/heads/codex/jte-tf-constant-input":
        raise RuntimeError("PRIVATE_OWNER_RUNNER_CONTEXT_UNQUALIFIED")
    if len(files) != 4 or len(set(files)) != 4 or not cmd:
        raise RuntimeError("ONE_SHOT_FOUR_FILE_CONTRACT")
    if a.wall_ceiling_s < 1 or a.wall_ceiling_s > 1200:
        raise RuntimeError("WALL_LIMIT_OUTSIDE_APPROVED_CEILING")
    if folder.stat().st_mode & 0o077:
        raise RuntimeError("PRIVATE_FOLDER_PERMISSIONS_NOT_0700")
    if any(p.parent != folder or p.exists() for p in files):
        raise RuntimeError("NATIVE_FILE_PARENT_OR_OVERWRITE")
    if (folder / "m3_watchdog_receipt.json").exists() or \
       (folder / "m3_watchdog_receipt.json.partial").exists() or \
       (folder / "m3_watchdog_child.log").exists():
        raise RuntimeError("NO_SECOND_ATTEMPT_OR_LOG_OVERWRITE")
    if len(a.model_sha256) != 64 or sha256(model).lower() != a.model_sha256.lower():
        raise RuntimeError("SHA_PIN_MISMATCH")
    issue = caps(folder, files, a.drive_free_bytes)
    if issue:
        raise RuntimeError("PREFLIGHT_" + issue)
    t0 = time.monotonic()
    reason = "CHILD_EXITED_NEEDS_INDEPENDENT_DATA_REVIEW"
    proc = None
    max_bytes = 0
    try:
        with open(folder / "m3_watchdog_child.log", "x", encoding="utf-8") as log:
            # The external watchdog is alive before starting MATLAB; do
            # not use shell=True; child has its own killable process group.
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True, cwd=os.getcwd())
            while proc.poll() is None:
                if time.monotonic() - t0 >= a.wall_ceiling_s:
                    reason = "UNQUALIFIED_WALL_CEILING"
                    break
                issue = caps(folder, files, a.drive_free_bytes)
                if issue:
                    reason = "UNQUALIFIED_" + issue
                    break
                total = sum(p.stat().st_size for p in files if p.exists())
                max_bytes = max(max_bytes, total)
                time.sleep(1)
            if reason.startswith("UNQUALIFIED"):
                terminate_group(proc)
    finally:
        if proc is not None and proc.poll() is None:
            terminate_group(proc)
        elapsed = time.monotonic() - t0
        data = dict(status=reason, child_exit_code=None if proc is None else proc.poll(),
                    elapsed_wall_s=round(elapsed, 3), max_observed_native_bytes=max_bytes,
                    model_sha256=a.model_sha256.lower(), files_seen=sum(p.exists() for p in files),
                    owner_approval_token_was_present=True,
                    matlab_model_result="NOT_EVALUATED_BY_WATCHDOG",
                    native_file_clock="NOT_EVALUATED_BY_WATCHDOG",
                    hidden_physical_IC="NOT_EVALUATED_BY_WATCHDOG",
                    private_SHA_readback="NOT_PERFORMED_BY_WATCHDOG",
                    G5_ACCEPTED=False, auto_retry=False, output_is_private=True)
        receipt(folder, data)
        print("BTMS_M3_WATCHDOG_STATUS=" + reason + " G5_ACCEPTED=false")
    return 0 if reason == "CHILD_EXITED_NEEDS_INDEPENDENT_DATA_REVIEW" else 5

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("BTMS_M3_WATCHDOG_FAIL_CLOSED=" + type(exc).__name__ + " G5_ACCEPTED=false", file=sys.stderr)
        sys.exit(4)
