"""Future protected runner: one MATLAB process, external bounds, no retry."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import queue
import threading

from BTMS_M3_oneShotWatchdog import memory, violation, proc_start, proc_rss, terminate_tree
from JTE101_io import quota
from WK08_private_gate import context, drive, ROOT, GiB


def main():
    run, commit = context()
    manifest = ROOT / "WK08_MANIFEST.json"
    if not manifest.is_file():
        raise RuntimeError("WK08_MANIFEST_REQUIRED")
    token, _ = drive()
    free_drive = quota(token)["availableBytes"]
    job_start = float(os.environ["WK08_JOB_START_EPOCH"])
    if time.time() - job_start > 600:
        raise RuntimeError("WK08_INSUFFICIENT_JOB_DELIVERY_RESERVE")
    mem = memory()
    if (mem["hostAvailable"] < 8 * GiB or
        (mem["cgroupAvailable"] is not None and mem["cgroupAvailable"] < 8 * GiB)
        or shutil.disk_usage(ROOT).free < 10 * GiB or free_drive < 3 * GiB):
        raise RuntimeError("WK08_PREFLIGHT_RESOURCE")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("JTE_GOOGLE_") and k not in {"GH_TOKEN", "GITHUB_TOKEN"}}
    executable = shutil.which("matlab")
    if not executable:
        raise RuntimeError("WK08_MATLAB_UNAVAILABLE")
    console = ROOT / "WK08_CONSOLE.log"
    report = {"run": run, "commit": commit, "status": "UNQUALIFIED", "returncode": None,
              "matlabProcessesLaunched": 0, "automaticRetry": False, "G5Accepted": False}
    proc = None
    identity = None
    started = time.monotonic()
    updates = queue.Queue()
    refresh = None
    refreshed = started
    def refresh_quota():
        try:
            updates.put((True, quota(token)["availableBytes"]))
        except Exception:
            updates.put((False, None))
    try:
        with console.open("xb") as output, (ROOT / "WK08_RESOURCES.jsonl").open("x") as samples:
            proc = subprocess.Popen([executable, "-batch",
                "addpath('jte-public'); BTMS_WK08_run('actuator-review-private/WK08_MANIFEST.json')"],
                env=env, stdout=output, stderr=subprocess.STDOUT)
            report["matlabProcessesLaunched"] = 1
            identity = proc_start(proc.pid)
            while proc.poll() is None:
                now = time.monotonic()
                if refresh is None and now - refreshed >= 45:
                    refresh = threading.Thread(target=refresh_quota, daemon=True)
                    refreshed = now
                    refresh.start()
                if refresh is not None:
                    if not updates.empty():
                        ok, value = updates.get()
                        if not ok:
                            raise RuntimeError("WK08_DRIVE_REFRESH_FAILED")
                        free_drive = value
                        refresh = None
                    elif now - refreshed > 10:
                        raise RuntimeError("WK08_DRIVE_REFRESH_TIMEOUT")
                sizes = [p.stat().st_size for p in (ROOT / "native").glob("*.mat")]
                # Include preparation and log growth in both wall and resource limits.
                mem = memory()
                reason = violation(mem, shutil.disk_usage(ROOT).free, free_drive,
                                   sizes, time.monotonic() - started, wall=1185)
                samples.write(json.dumps({"unix": time.time(), "memory": mem,
                    "matlabRSS_bytes": proc_rss(proc.pid), "nativeBytes": sum(sizes),
                    "elapsed_s": time.monotonic() - started}) + "\n")
                samples.flush()
                if reason:
                    report["status"] = "UNQUALIFIED_" + reason
                    terminate_tree(proc.pid, identity)
                    break
                time.sleep(.5)
            report["returncode"] = proc.wait(timeout=15)
            if report["returncode"] == 0 and report["status"] == "UNQUALIFIED":
                report["status"] = "PROCESS_EXIT_ZERO"
    except Exception as exc:
        report["exceptionType"] = type(exc).__name__
        if proc is not None and identity is not None and proc.poll() is None:
            terminate_tree(proc.pid, identity)
    finally:
        report["elapsed_s"] = time.monotonic() - started
        (ROOT / "WK08_SUPERVISOR.json").write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "PROCESS_EXIT_ZERO" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("WK08_SUPERVISOR_UNQUALIFIED code=" + type(exc).__name__)
        sys.exit(1)
