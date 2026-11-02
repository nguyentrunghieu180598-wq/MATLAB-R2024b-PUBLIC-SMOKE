"""WK08 R1 private prepare/publish. Never launches MATLAB. Default workflow disabled."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse

from JTE062_google_drive_synthetic import access_token, ensure_app_folder, API, req
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota, query, one
from sampled_actuator_review_io import get, need, ROOT
from WK04_private_gate import require_verified_neutral_preflight

REPO = "nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"
BRANCH = "codex/wk08-geometric-injection"
MESSAGE = "WK08_PACK_340S_ONE_SHOT_20261102"
WORKFLOW = ".github/workflows/wk08-pack-one-shot.yml"
MARKER = "jte-public/WK08_PACK_TRIGGER.txt"
SCHEMA = "WK08_R1_RAW_UNREVIEWED_NOT_G5"
INTENT = "WK08_R1_ATTEMPT_INTENT_20261102.json"
GiB = 1024**3
NATIVE = ("uCore", "uSampled", "actuatorY", "Ttrue312",
          "TmaxTrue", "TmaxMeas", "pumpPower", "Ttrue312_1s")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def context():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY") == REPO
         and event.get("repository", {}).get("full_name") == REPO
         and event.get("repository", {}).get("private") is False
         and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
         and os.environ.get("GITHUB_EVENT_NAME") == "push"
         and os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
         and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
         and os.environ.get("WK08_PROTECTED_ENV_NAME") == "JTE_DRIVE_WRITE"
         and os.environ.get("WK08_OWNER_APPROVAL") ==
             "APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO"
         and (event.get("head_commit") or {}).get("message") == MESSAGE
         and (event.get("head_commit") or {}).get("id") == os.environ["GITHUB_SHA"],
         "WK08_CONTEXT_DENIED")
    source = os.environ.get("WK08_REVIEWED_SOURCE_SHA", "")
    need(re.fullmatch("[0-9a-f]{40}", source) and source != "0" * 40,
         "WK08_REVIEWED_SOURCE_UNSET")
    need(git("rev-parse", "HEAD") == os.environ["GITHUB_SHA"]
         and git("rev-parse", "HEAD~2") == source
         and git("diff", "--name-only", "HEAD~2", "HEAD~1") == WORKFLOW
         and git("diff", "--name-only", "HEAD~1", "HEAD") == MARKER
         and Path(MARKER).read_text().strip() == MESSAGE, "WK08_CHAIN_DENIED")
    return os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_SHA"]


def private_acl(token, file_id):
    fields = "id,permissions(type,role)"
    _, _, raw = req(API + "/" + urllib.parse.quote(file_id, safe="") + "?"
                    + urllib.parse.urlencode({"fields": fields}), token=token)
    permissions = json.loads(raw).get("permissions", [])
    need(permissions and all(p.get("type") == "user" and p.get("role") == "owner"
                             for p in permissions), "WK08_OWNER_ONLY_ACL")


def drive():
    token = access_token(*[os.environ[k] for k in (
        "JTE_GOOGLE_CLIENT_ID", "JTE_GOOGLE_CLIENT_SECRET", "JTE_GOOGLE_REFRESH_TOKEN")])
    folder = ensure_app_folder(token)
    private_acl(token, folder)
    return token, folder


def upload(token, folder, path):
    result = upload_verified(token, folder, path, schema=SCHEMA)
    meta = one(token, folder, "JTE063_VERIFIED_" + path.name)
    private_acl(token, meta["id"])
    return result


def code_hashes():
    paths = git("ls-files", "jte-public", WORKFLOW).splitlines()
    return {p: sha(p) for p in paths if Path(p).suffix in {".m", ".py", ".csv", ".yml"}}


def prepare(run, commit):
    need(not ROOT.exists(), "WK08_FRESH_PRIVATE_ROOT")
    token, folder = drive()
    require_verified_neutral_preflight(token, folder)
    need(quota(token)["availableBytes"] > 3 * GiB, "WK08_DRIVE_RESERVE")
    condition = "name = 'JTE063_PENDING_" + INTENT + "' or name = 'JTE063_VERIFIED_" + INTENT + "'"
    need(not query(token, folder, condition), "WK08_ALREADY_RESERVED_NO_RETRY")
    ROOT.mkdir(mode=0o700, exist_ok=False)
    intent = ROOT / INTENT
    intent.write_text(json.dumps({"run": run, "commit": commit,
        "schema": SCHEMA, "MATLAB_STARTED": "NOT_YET_CONFIRMED",
        "exactlyOneInitialize": True, "allowRetry": False}))
    intent.chmod(0o600)
    upload(token, folder, intent)  # persistent reservation BEFORE any model or MATLAB work
    assets = []
    def asset(name, local, receipt=None):
        meta = one(token, folder, "JTE063_VERIFIED_" + name)
        private_acl(token, meta["id"])
        a = get(token, folder, name, local)
        assets.append(a)
        if receipt is not None:
            rows = [x for x in receipt["files"] if x["name"] == name]
            need(len(rows) == 1 and rows[0]["sha256"] == a["sha256"]
                 and rows[0]["integrity"] == "FULL_REMOTE_READBACK_VERIFIED",
                 "WK08_RECEIPT_LINK")
        return a
    prefix = "BTMS_M2_40701917441_"
    asset(prefix + "PRIVATE_RECEIPT.json", "old_receipt.json")
    receipt = json.loads((ROOT / "old_receipt.json").read_text())
    need(receipt["run"] == "40701917441" and receipt["commit"] ==
         "75afa01be55339d20ce5831830a0cacdb0c5d3f4" and
         receipt["physicalRun"] is False, "WK08_M2_PROVENANCE")
    src = asset(prefix + "B0L_Ref_LOGGER.slx", "M2340Source.slx", receipt)
    asset(prefix + "B0L_Ref_PROOF.json", "old_proof.json", receipt)
    proof = json.loads((ROOT / "old_proof.json").read_text())
    need(proof["instrumentedModelSHA256"] == src["sha256"]
         and proof["period_s"] == .01 and proof["trueT312CompiledWidthVerified"]
         and proof["fullRetainedParametersConfigGraphParity"], "WK08_M2_SOURCE")
    asset(prefix + "INPUT_MANIFEST.json", "old_manifest.json", receipt)
    old = json.loads((ROOT / "old_manifest.json").read_text())
    workspace = asset("JTE101_40449421507_PREPARE_WORKSPACE.mat", "source_workspace.mat")
    rows = [x for x in old["inputs"] if x["local"] == "source_workspace.mat"]
    need(len(rows) == 1 and rows[0]["sha256"] == workspace["sha256"], "WK08_WORKSPACE")
    vendor = Path("vendor-pack").resolve()
    need(git("-C", str(vendor), "rev-parse", "HEAD") ==
         "f98d21929a3a269dacd1ee38999cd9773760c6db", "WK08_VENDOR_COMMIT")
    vendor_slx = vendor / "Models/Battery_Pack_Thermal_Management.slx"
    need(sha(vendor_slx) ==
         "0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0",
         "WK08_VENDOR_SHA")
    manifest = {"run": run, "commit": commit, "mode": "R1", "stopTime_s": 340,
        "privateRoot": str(ROOT.resolve()), "sourceSHA256": src["sha256"],
        "inputs": assets, "vendorRoot": str(vendor), "vendorSLX": str(vendor_slx),
        "inputCodeSHA256": code_hashes(), "retry": False}
    (ROOT / "WK08_MANIFEST.json").write_text(json.dumps(manifest, indent=2))


def publish(run, commit):
    token, folder = drive()
    manifest_path = ROOT / "WK08_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    flags_path = ROOT / "WK08_FLAGS.json"
    flags = json.loads(flags_path.read_text()) if flags_path.is_file() else {}
    monitor_path = ROOT / "WK08_SUPERVISOR.json"
    monitor = json.loads(monitor_path.read_text()) if monitor_path.is_file() else {}
    same = all(x.get("run") == run and x.get("commit") == commit
               for x in (manifest, flags, monitor))
    unchanged = manifest.get("inputCodeSHA256") == code_hashes()
    inputs_ok = bool(manifest.get("inputs")) and all(
        sha(ROOT / a["local"]) == a["sha256"] for a in manifest.get("inputs", []))
    receipt = {"run": run, "commit": commit, "schema": SCHEMA, "files": [],
        "sameAttempt": same, "sourceCodeUnchanged": unchanged,
        "inputsUnchanged": inputs_ok, "G5Accepted": False,
        "status": "UNQUALIFIED", "rawDataPublic": False}
    # Exclude downloaded inputs and the intent; publish only this attempt's outputs.
    paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and
                   (p.name.startswith("WK08") or p.parent.name == "native") and
                   p.name != INTENT)
    need(all(not p.is_symlink() for p in paths), "WK08_SYMLINK")
    need(sum(p.stat().st_size for p in paths) <= 2 * GiB, "WK08_DELIVERY_TOTAL_CAP")
    for path in paths:
        if path.stat().st_size == 0:
            continue  # omitted file prevents complete qualification below
        need(path.stat().st_size <= GiB, "WK08_DELIVERY_FILE_CAP")
        receipt["files"].append({"name": path.name, **upload(token, folder, path)})
    required = {f"WK08_{role}.mat" for role in NATIVE} | {
        "WK08_FLAGS.json", "WK08_PREPARED_PROOF.mat", "WK08R1.slx",
        "WK08_MANIFEST.json", "WK08_SUPERVISOR.json", "WK08_RESOURCES.jsonl"}
    uploaded = {p["name"] for p in receipt["files"]}
    complete = required <= uploaded
    passed = (same and unchanged and inputs_ok and complete
              and flags.get("status") == "R1_NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK"
              and monitor.get("status") == "PROCESS_EXIT_ZERO"
              and monitor.get("returncode") == 0)
    receipt["requiredPayloadComplete"] = complete
    receipt["status"] = "R1_GATES_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE" if passed else "UNQUALIFIED"
    receipt_path = ROOT / ("WK08_" + run + "_PRIVATE_RECEIPT.json")
    receipt_path.write_text(json.dumps(receipt, indent=2))
    upload(token, folder, receipt_path)
    if passed:
        (ROOT / "WK08_DELIVERY_VERIFIED").write_text("PRIVATE_READBACK_COMPLETE")
    need(passed, "WK08_UNQUALIFIED_PRIVATE_DIAGNOSTICS_SAVED")
    print("WK08_R1_PRIVATE_RECEIPT_COMPLETE pendingClaudeReview=1 G5_ACCEPTED=false")


if __name__ == "__main__":
    try:
        run, commit = context()
        mode = sys.argv[1]
        if mode == "prepare":
            prepare(run, commit)
        elif mode == "publish":
            publish(run, commit)
        else:
            raise ValueError("WK08_MODE")
    except Exception as exc:
        # No exception text, OAuth values, private IDs, paths or temperatures in logs.
        print("WK08_PRIVATE_GATE_UNQUALIFIED code=" + type(exc).__name__)
        sys.exit(1)
