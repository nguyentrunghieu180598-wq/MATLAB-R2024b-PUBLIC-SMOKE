"""WK08 R1/CI_5S private prepare/publish. Never launches MATLAB. Default workflow disabled."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

from JTE062_google_drive_synthetic import access_token, ensure_app_folder, API, req, DRIVE_FOLDER_NAME, MIME_FOLDER
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota, query, one, download
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
CI5S = {
    "mode": "CI_5S", "stopTime_s": 5,
    "message": "WK08_CI_5S_ONE_SHOT_20261103E",
    "workflow": ".github/workflows/wk08-ci5s-one-shot.yml",
    "marker": "jte-public/WK08_CI5S_TRIGGER.txt",
    "approval": "APPROVE_WK08_CI5S_E_ONCE_AFTER_CLAUDE_GO",
    "intent": "WK08_CI5S_ATTEMPT_INTENT_20261103E.json",
    "schema": "WK08_CI5S_RAW_UNREVIEWED_NOT_G5",
    "receiptPrefix": "WK08_CI5S_",
    "receiptSuffix": "_PRIVATE_RECEIPT_20261103E.json",
    "flagsPass": "CI_5S_GATES_PASS_NOT_R1",
    "receiptPass": "CI_5S_GATES_AND_PRIVATE_READBACK_PASS_NOT_R1_PENDING_CLAUDE",
}
NATIVE = ("uCore", "uSampled", "actuatorY", "Ttrue312",
          "TmaxTrue", "TmaxMeas", "pumpPower", "Ttrue312_1s")


PREFLIGHT = {
    "workflow": ".github/workflows/wk08-preflight-check.yml",
    "marker": "jte-public/WK08_PREFLIGHT_TRIGGER.txt",
    "message": "WK08_PREFLIGHT_CHECK_20261103",
    "approval": "APPROVE_WK08_PREFLIGHT_ONCE_AFTER_CLAUDE_GO",
}

D13_BRANCH = "codex/wk10-d13-k2-340"
D13_SCENARIO_FILE = Path(__file__).with_name("WK10_scenario.json")
D13 = {
    "mode": "D13_REF", "stopTime_s": 340,
    "message": "WK10_D13_REF_K2_T340_A_ONE_SHOT_20261103",
    "workflow": ".github/workflows/wk10-d13-ref-one-shot.yml",
    "marker": "jte-public/WK10_D13_REF_K2_T340_A_TRIGGER.txt",
    "approval": "APPROVE_WK10_D13_REF_K2_T340_A_ONCE_AFTER_CLAUDE_GO",
    "intent": "WK10_D13_REF_K2_T340_A_ATTEMPT_INTENT_20261103.json",
    "schema": "WK10_D13_RAW_UNREVIEWED_NOT_G5",
    "receiptPrefix": "WK10_D13_REF_K2_T340_A_",
    "receiptSuffix": "_PRIVATE_RECEIPT_20261103.json",
    # Same qualification criteria as the neutral R1; suitability is diagnostic only.
    "flagsPass": "R1_NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK",
    "receiptPass": "R1_GATES_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE",
}
D13_PREFLIGHT = {
    "workflow": ".github/workflows/wk10-d13-preflight-check.yml",
    "marker": "jte-public/WK10_D13_PREFLIGHT_A_TRIGGER.txt",
    "message": "WK10_D13_PREFLIGHT_A_CHECK_20261103",
    "approval": "APPROVE_WK10_D13_PREFLIGHT_A_ONCE_AFTER_CLAUDE_GO",
}


def scenario():
    """Exact approved metadata, not a user-selectable load or horizon."""
    expected = {
        "scenario_id": "D13_K2_T340_V1", "k": 2, "T": 340,
        "model_sha256": "0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0",
        "vendor_mat_sha256": "a6b9e9353cadf2819255e55c1bcaf7beee439345311d2d0de30220e8e36e6986",
        "gain_block_path": "$ROOT/WK10 scenario current scale",
        "expected_edge": {"source": "$ROOT/Current demand", "source_port": 1,
                          "destination": "$ROOT/Battery Control", "destination_port": 2},
    }
    value = json.loads(D13_SCENARIO_FILE.read_text())
    need(json.dumps(value, sort_keys=True) == json.dumps(expected, sort_keys=True),
         "WK08_D13_SCENARIO_MISMATCH")
    return value


def validate_scenario_manifest(manifest):
    need(manifest.get("mode") == "D13_REF" and manifest.get("stopTime_s") == 340
         and json.dumps(manifest.get("scenario"), sort_keys=True) == json.dumps(scenario(), sort_keys=True)
         and manifest.get("scenarioSHA256") == sha(D13_SCENARIO_FILE),
         "WK08_D13_MANIFEST_MISMATCH")


def d13_intents(token, folder):
    """Read-only queries. Historical reservations are never removed or reused."""
    for label, intent, present in (
        ("D13_INTENT_ABSENT", D13["intent"], False),
        ("R1_INTENT_CONSUMED", INTENT, True),
        ("CI_5S_E_INTENT_CONSUMED", CI5S["intent"], True),
    ):
        condition = ("name = 'JTE063_PENDING_" + intent +
                     "' or name = 'JTE063_VERIFIED_" + intent + "'")
        reason = "WK08_D13_PRIOR_EVIDENCE_MISSING" if present else "WK08_ALREADY_RESERVED_NO_RETRY"
        check_step(label, lambda condition=condition, present=present, reason=reason: need(
            bool(query(token, folder, condition)) == present, reason))


def safe_failure_reason(exc):
    # Never stringify exceptions or non-string payloads.
    if isinstance(exc, RuntimeError) and len(exc.args) == 1:
        reason = exc.args[0]
        if type(reason) is str and (
            re.fullmatch(r"(WK08|WK06|WK04|JTE063|JTE101)_[A-Z0-9_]+", reason)
            or re.fullmatch(r"GOOGLE_API_HTTP_[0-9]{3}", reason)
            or reason in {"AMBIGUOUS_APP_FOLDER", "GOOGLE_API_TRANSPORT_FAILED",
                          "OAUTH_REFRESH_FAILED"}
        ):
            return reason
    return None


def report_failure(prefix, exc):
    """Public log: exception type plus one strictly allowlisted machine code."""
    line = prefix + " code=" + type(exc).__name__
    reason = safe_failure_reason(exc)
    if reason is not None:
        line += " reason=" + reason
    print(line)


def config(mode=None):
    mode = os.environ.get("WK08_MODE", "R1") if mode is None else mode
    need(mode in {"R1", "CI_5S", "D13_REF"}, "WK08_MODE_DENIED")
    if mode == "D13_REF":
        return dict(D13)
    if mode == "CI_5S":
        return dict(CI5S)
    return {"mode": "R1", "stopTime_s": 340, "message": MESSAGE,
        "workflow": WORKFLOW, "marker": MARKER,
        "approval": "APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO",
        "intent": INTENT, "schema": SCHEMA, "receiptPrefix": "WK08_",
        "flagsPass": "R1_NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK",
        "receiptPass": "R1_GATES_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE"}


def receipt_name(run):
    p = config()
    return p["receiptPrefix"] + run + p.get("receiptSuffix", "_PRIVATE_RECEIPT.json")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def context(check_only=False):
    p = config()  # validate WK08_MODE even for read-only check
    is_d13 = p["mode"] == "D13_REF"
    if is_d13:
        scenario()
    if check_only:
        p = D13_PREFLIGHT if is_d13 else PREFLIGHT
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY") == REPO
         and event.get("repository", {}).get("full_name") == REPO
         and event.get("repository", {}).get("private") is False
         and os.environ.get("GITHUB_REF") == "refs/heads/" + (D13_BRANCH if is_d13 else BRANCH)
         and os.environ.get("GITHUB_EVENT_NAME") == "push"
         and os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
         and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
         and os.environ.get("WK08_PROTECTED_ENV_NAME") == "JTE_DRIVE_WRITE"
         and os.environ.get("WK08_OWNER_APPROVAL") ==
             p["approval"]
         and (event.get("head_commit") or {}).get("message") == p["message"]
         and (event.get("head_commit") or {}).get("id") == os.environ["GITHUB_SHA"],
         "WK08_CONTEXT_DENIED")
    source = os.environ.get("WK08_REVIEWED_SOURCE_SHA", "")
    need(re.fullmatch("[0-9a-f]{40}", source) and source != "0" * 40,
         "WK08_REVIEWED_SOURCE_UNSET")
    need(git("rev-parse", "HEAD") == os.environ["GITHUB_SHA"]
         and git("rev-parse", "HEAD~2") == source
         and git("diff", "--name-only", "HEAD~2", "HEAD~1") == p["workflow"]
         and git("diff", "--name-only", "HEAD~1", "HEAD") == p["marker"]
         and Path(p["marker"]).read_text().strip() == p["message"], "WK08_CHAIN_DENIED")
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
    result = upload_verified(token, folder, path, schema=config()["schema"])
    meta = one(token, folder, "JTE063_VERIFIED_" + path.name)
    private_acl(token, meta["id"])
    return result


def code_hashes():
    paths = git("ls-files", "jte-public", config()["workflow"]).splitlines()
    result = {p: sha(p) for p in paths if Path(p).suffix in {".m", ".py", ".csv", ".yml"}}
    if config()["mode"] == "D13_REF":
        result["jte-public/WK10_scenario.json"] = sha(D13_SCENARIO_FILE)
    return result


def reserve_one_shot(token, folder, run, commit):
    p = config()
    condition = "name = 'JTE063_PENDING_" + p["intent"] + "' or name = 'JTE063_VERIFIED_" + p["intent"] + "'"
    need(not query(token, folder, condition), "WK08_ALREADY_RESERVED_NO_RETRY")
    ROOT.mkdir(mode=0o700, exist_ok=False)
    intent = ROOT / p["intent"]
    intent.write_text(json.dumps({"run": run, "commit": commit,
        "schema": p["schema"], "MATLAB_STARTED": "NOT_YET_CONFIRMED",
        "exactlyOneInitialize": True, "allowRetry": False}))
    intent.chmod(0o600)
    upload(token, folder, intent)  # persistent reservation BEFORE any model or MATLAB work

def btms_dats_folder(token, parent):
    condition = "name = 'BTMS-DATS' and mimeType = 'application/vnd.google-apps.folder'"
    rows = query(token, parent, condition)
    need(len(rows) <= 1, "WK08_CI5S_RESULTS_FOLDER_AMBIGUOUS")
    if rows:
        folder = rows[0]["id"]
    else:
        _, _, raw = req(API + "?fields=id", method="POST", token=token,
            data=json.dumps({"name": "BTMS-DATS", "parents": [parent],
                "mimeType": "application/vnd.google-apps.folder"}).encode(),
            extra={"Content-Type": "application/json"})
        folder = json.loads(raw)["id"]
    private_acl(token, folder)
    return folder


def check_step(name, action):
    """Print no private values, including when an unexpected exception occurs."""
    try:
        result = action()
    except Exception as exc:
        reason = safe_failure_reason(exc) or "WK08_PREFLIGHT_UNCLASSIFIED"
        print("CHECK " + name + "=FAIL reason=" + reason)
        raise
    print("CHECK " + name + "=PASS reason=WK08_PREFLIGHT_OK")
    return result


def readonly_app_folder(token):
    # ensure_app_folder() may POST a folder; NEVER use it on the check path.
    filt = ("name = '" + DRIVE_FOLDER_NAME + "' and mimeType = '" +
            MIME_FOLDER + "' and trashed = false")
    _, _, raw = req(API + "?" + urllib.parse.urlencode({
        "q": filt, "fields": "nextPageToken,files(id)", "pageSize": "100",
        "spaces": "drive"}), token=token)
    data = json.loads(raw)
    rows = data.get("files", [])
    need(not data.get("nextPageToken") and len(rows) <= 1, "AMBIGUOUS_APP_FOLDER")
    need(len(rows) == 1, "WK08_PREFLIGHT_APP_FOLDER_MISSING")
    return rows[0]["id"]


def check(run, commit):
    """Drive read-only: no ROOT, reservation, upload, vendor checkout or MATLAB."""
    is_d13 = config()["mode"] == "D13_REF"
    if is_d13:
        check_step("D13_SCENARIO", scenario)
    check_step("FRESH_SCRATCH", lambda: need(not ROOT.exists(), "WK08_FRESH_PRIVATE_ROOT"))
    def oauth():
        keys = ("JTE_GOOGLE_CLIENT_ID", "JTE_GOOGLE_CLIENT_SECRET", "JTE_GOOGLE_REFRESH_TOKEN")
        need(all(os.environ.get(k) for k in keys), "WK08_PREFLIGHT_CREDENTIALS_MISSING")
        return access_token(*[os.environ[k] for k in keys])
    token = check_step("OAUTH_REFRESH", oauth)
    folder = check_step("APP_FOLDER", lambda: readonly_app_folder(token))
    check_step("APP_FOLDER_ACL", lambda: private_acl(token, folder))
    check_step("WK06_NEUTRAL_RECEIPT", lambda: require_verified_neutral_preflight(token, folder))
    check_step("DRIVE_QUOTA", lambda: need(
        quota(token)["availableBytes"] > 3 * GiB, "WK08_DRIVE_RESERVE"))
    if is_d13:
        d13_intents(token, folder)
    else:
        # Historical WK08 check semantics are retained.
        intent = config("R1")["intent"]
        condition = ("name = 'JTE063_PENDING_" + intent +
                     "' or name = 'JTE063_VERIFIED_" + intent + "'")
        check_step("R1_INTENT_ABSENT", lambda condition=condition: need(
            not query(token, folder, condition), "WK08_ALREADY_RESERVED_NO_RETRY"))
        intent = config("CI_5S")["intent"]
        condition = ("name = 'JTE063_PENDING_" + intent +
                     "' or name = 'JTE063_VERIFIED_" + intent + "'")
        check_step("CI_5S_E_INTENT_CONSUMED", lambda condition=condition: need(
            query(token, folder, condition), "WK08_CI5S_EVIDENCE_MISSING"))

    prefix = "BTMS_M2_40701917441_"
    assets = (
        ("M2_RECEIPT", prefix + "PRIVATE_RECEIPT.json", "old_receipt.json"),
        ("M2_MODEL", prefix + "B0L_Ref_LOGGER.slx", None),
        ("M2_PROOF", prefix + "B0L_Ref_PROOF.json", "old_proof.json"),
        ("M2_MANIFEST", prefix + "INPUT_MANIFEST.json", "old_manifest.json"),
        ("WORKSPACE", "JTE101_40449421507_PREPARE_WORKSPACE.mat", "source_workspace.mat"),
    )
    metas = {}
    for label, name, local in assets:
        def metadata(name=name):
            meta = one(token, folder, "JTE063_VERIFIED_" + name)
            private_acl(token, meta["id"])
            props = meta.get("appProperties") or {}
            need(props.get("state") == "VERIFIED" and
                 re.fullmatch("[a-f0-9]{64}", props.get("sha256", "")) and
                 0 < int(meta.get("size", -1)) <= 3 * GiB,
                 "WK08_PREFLIGHT_ASSET_METADATA")
            return meta
        metas[name] = check_step(label + "_METADATA_ACL", metadata)

    # Only verified JSON and workspace bytes enter disposable, owner-private temp storage.
    with tempfile.TemporaryDirectory(prefix="wk08-check-") as temporary:
        temp = Path(temporary)
        os.chmod(temp, 0o700)
        for label, name, local in assets:
            if local is None:
                continue  # model bytes stay in Drive; link verified SHA metadata below
            def fetch(name=name, local=local):
                if local.endswith(".json"):
                    need(int(metas[name]["size"]) <= 4 * 1024**2, "WK08_PREFLIGHT_JSON_SIZE")
                return download(token, metas[name], temp / local)
            check_step(label + "_DOWNLOAD_SHA", fetch)

        receipt = check_step("M2_RECEIPT_JSON", lambda: json.loads(
            (temp / "old_receipt.json").read_text()))
        check_step("M2_PROVENANCE", lambda: need(
            receipt["run"] == "40701917441" and receipt["commit"] ==
            "75afa01be55339d20ce5831830a0cacdb0c5d3f4" and receipt["physicalRun"] is False,
            "WK08_M2_PROVENANCE"))
        def receipt_links():
            for label, name, local in assets[1:4]:
                rows = [x for x in receipt["files"] if x["name"] == name]
                need(len(rows) == 1 and rows[0]["sha256"] ==
                     metas[name]["appProperties"]["sha256"] and
                     rows[0]["integrity"] == "FULL_REMOTE_READBACK_VERIFIED",
                     "WK08_RECEIPT_LINK")
        check_step("M2_RECEIPT_LINKS", receipt_links)
        proof = check_step("M2_PROOF_JSON", lambda: json.loads(
            (temp / "old_proof.json").read_text()))
        check_step("M2_PROOF_MODEL_LINK", lambda: need(
            proof["instrumentedModelSHA256"] ==
            metas[prefix + "B0L_Ref_LOGGER.slx"]["appProperties"]["sha256"] and
            proof["period_s"] == .01 and proof["trueT312CompiledWidthVerified"] and
            proof["fullRetainedParametersConfigGraphParity"], "WK08_M2_SOURCE"))
        manifest = check_step("M2_MANIFEST_JSON", lambda: json.loads(
            (temp / "old_manifest.json").read_text()))
        def workspace_link():
            rows = [x for x in manifest["inputs"] if x["local"] == "source_workspace.mat"]
            workspace = metas[assets[-1][1]]["appProperties"]["sha256"]
            need(len(rows) == 1 and rows[0]["sha256"] == workspace and
                 sha(temp / "source_workspace.mat") == workspace, "WK08_WORKSPACE")
        check_step("WORKSPACE_MANIFEST_SHA", workspace_link)
    # No vendor checkout/SHA gate on check; prepare retains the actual vendor byte gate.
    print("WK08_PREFLIGHT_ALL_PASS")


def prepare(run, commit):
    p = config()
    if p["mode"] == "D13_REF":
        scenario()
    need(not ROOT.exists(), "WK08_FRESH_PRIVATE_ROOT")
    token, folder = drive()
    require_verified_neutral_preflight(token, folder)
    need(quota(token)["availableBytes"] > 3 * GiB, "WK08_DRIVE_RESERVE")
    if p["mode"] == "D13_REF":
        d13_intents(token, folder)
    reserve_one_shot(token, folder, run, commit)
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
    if p["mode"] == "D13_REF":
        load_file = vendor / "Scripts_Data/Battery_Pack_Thermal_Management_Ivst.mat"
        need(sha(load_file) == scenario()["vendor_mat_sha256"], "WK08_D13_LOAD_SHA")
    manifest = {"run": run, "commit": commit, "mode": p["mode"], "stopTime_s": p["stopTime_s"],
        "privateRoot": str(ROOT.resolve()), "sourceSHA256": src["sha256"],
        "inputs": assets, "vendorRoot": str(vendor), "vendorSLX": str(vendor_slx),
        "inputCodeSHA256": code_hashes(), "retry": False}
    if p["mode"] == "D13_REF":
        manifest.update(scenario=scenario(), scenarioSHA256=sha(D13_SCENARIO_FILE))
        validate_scenario_manifest(manifest)
    (ROOT / "WK08_MANIFEST.json").write_text(json.dumps(manifest, indent=2))


def publish(run, commit):
    p = config()
    token, folder = drive()
    if p["mode"] in {"CI_5S", "D13_REF"}:
        folder = btms_dats_folder(token, folder)
    manifest_path = ROOT / "WK08_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    if p["mode"] == "D13_REF":
        validate_scenario_manifest(manifest)
    flags_path = ROOT / "WK08_FLAGS.json"
    flags = json.loads(flags_path.read_text()) if flags_path.is_file() else {}
    monitor_path = ROOT / "WK08_SUPERVISOR.json"
    monitor = json.loads(monitor_path.read_text()) if monitor_path.is_file() else {}
    same = all(x.get("run") == run and x.get("commit") == commit
               for x in (manifest, flags, monitor))
    if p["mode"] == "D13_REF":
        same = (same and all(x.get("mode") == "D13_REF" and
                x.get("scenarioSHA256") == manifest["scenarioSHA256"] for x in (flags, monitor)))
    if p["mode"] == "CI_5S":
        same = (same and manifest.get("mode") == "CI_5S"
                and manifest.get("stopTime_s") == 5
                and flags.get("mode") == "CI_5S"
                and monitor.get("mode") == "CI_5S")
    unchanged = manifest.get("inputCodeSHA256") == code_hashes()
    inputs_ok = bool(manifest.get("inputs")) and all(
        sha(ROOT / a["local"]) == a["sha256"] for a in manifest.get("inputs", []))
    receipt = {"run": run, "commit": commit, "schema": p["schema"], "files": [],
        "sameAttempt": same, "sourceCodeUnchanged": unchanged,
        "inputsUnchanged": inputs_ok, "G5Accepted": False,
        "status": "UNQUALIFIED", "rawDataPublic": False}
    # Exclude downloaded inputs and the intent; publish only this attempt's outputs.
    paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and
                   (p.name.startswith("WK08") or p.parent.name == "native") and
                   p.name != config()["intent"])
    need(all(not p.is_symlink() for p in paths), "WK08_SYMLINK")
    need(sum(p.stat().st_size for p in paths) <= 2 * GiB, "WK08_DELIVERY_TOTAL_CAP")
    for path in paths:
        if path.stat().st_size == 0:
            continue  # omitted file prevents complete qualification below
        need(path.stat().st_size <= GiB, "WK08_DELIVERY_FILE_CAP")
        if p["mode"] in {"CI_5S", "D13_REF"}:
            # B3: BTMS-DATS keeps earlier attempts; prefix the run id so names never collide.
            staged = path.with_name(run + "_" + path.name)
            shutil.copyfile(path, staged)
            receipt["files"].append({"name": path.name, **upload(token, folder, staged)})
        else:
            receipt["files"].append({"name": path.name, **upload(token, folder, path)})
    required = {f"WK08_{role}.mat" for role in NATIVE} | {
        "WK08_FLAGS.json", "WK08_PREPARED_PROOF.mat", "WK08R1.slx",
        "WK08_MANIFEST.json", "WK08_SUPERVISOR.json", "WK08_RESOURCES.jsonl"}
    uploaded = {p["name"] for p in receipt["files"]}
    complete = required <= uploaded
    passed = (same and unchanged and inputs_ok and complete
              and flags.get("status") == p["flagsPass"]
              and monitor.get("status") == "PROCESS_EXIT_ZERO"
              and monitor.get("returncode") == 0)
    if p["mode"] == "D13_REF":
        # Derived diagnostic only: neither its presence, values nor export failure
        # changes complete/passed. Never exceed the existing delivery byte budget.
        receipt["summaryDelivery"] = "NOT VERIFIED"
        try:
            summary = ROOT / "SUMMARY.json"
            need(summary.is_file() and not summary.is_symlink() and
                 0 < summary.stat().st_size <= 64 * 1024 and
                 sum(x.stat().st_size for x in paths) + summary.stat().st_size <= 2 * GiB,
                 "WK08_D13_SUMMARY_UNAVAILABLE")
            staged = summary.with_name(run + "_SUMMARY.json")
            shutil.copyfile(summary, staged)
            receipt["files"].append({"name": "SUMMARY.json", **upload(token, folder, staged)})
            receipt["summaryDelivery"] = "DERIVED_NOT_EVIDENCE_PRIVATE_READBACK"
        except Exception as exc:
            receipt["summaryDeliveryErrorType"] = type(exc).__name__
    receipt["requiredPayloadComplete"] = complete
    receipt["status"] = p["receiptPass"] if passed else "UNQUALIFIED"
    receipt_path = ROOT / receipt_name(run)
    receipt_path.write_text(json.dumps(receipt, indent=2))
    upload(token, folder, receipt_path)
    if passed:
        (ROOT / "WK08_DELIVERY_VERIFIED").write_text("PRIVATE_READBACK_COMPLETE")
    need(passed, "WK08_UNQUALIFIED_PRIVATE_DIAGNOSTICS_SAVED")
    print("WK08_" + p["mode"] + "_PRIVATE_RECEIPT_COMPLETE pendingClaudeReview=1 G5_ACCEPTED=false")


if __name__ == "__main__":
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        run, commit = context(check_only=(mode == "check"))
        if mode == "prepare":
            prepare(run, commit)
        elif mode == "publish":
            publish(run, commit)
        elif mode == "check":
            check(run, commit)
        else:
            raise ValueError("WK08_MODE")
    except Exception as exc:
        # No exception text, OAuth values, private IDs, paths or temperatures in logs.
        report_failure("WK08_PRIVATE_GATE_UNQUALIFIED", exc)
        sys.exit(1)
