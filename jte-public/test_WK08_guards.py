"""Author checks only: offline authorization and fixed topology; no MATLAB/CI."""
import csv
import base64
import hashlib
import io
import runpy
from contextlib import redirect_stdout, ExitStack
import json
import os
import re
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import WK08_private_gate as gate
import WK08_supervise as supervisor


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.event = Path(self.tmp.name) / "event.json"
        self.event.write_text(json.dumps({"repository": {"full_name": gate.REPO, "private": False},
            "head_commit": {"message": gate.MESSAGE, "id": "c" * 40}}))
        self.marker = Path(self.tmp.name) / "marker.txt"
        self.marker.write_text(gate.MESSAGE)
        self.env = {"GITHUB_EVENT_PATH": str(self.event), "GITHUB_REPOSITORY": gate.REPO,
            "GITHUB_REF": "refs/heads/" + gate.BRANCH, "GITHUB_EVENT_NAME": "push",
            "GITHUB_RUN_ATTEMPT": "1", "RUNNER_ENVIRONMENT": "github-hosted",
            "WK08_PROTECTED_ENV_NAME": "JTE_DRIVE_WRITE", "GITHUB_SHA": "c" * 40,
            "GITHUB_RUN_ID": "123", "WK08_REVIEWED_SOURCE_SHA": "a" * 40,
            "WK08_OWNER_APPROVAL": "APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO"}

    def invoke(self, changes=None, extra_source=False):
        env = dict(self.env)
        env.update(changes or {})
        workflow = (gate.PREFLIGHT if getattr(self, "check_only", False) else
                    gate.config(env.get("WK08_MODE", "R1")))["workflow"]
        def git(*args):
            return {("rev-parse", "HEAD"): "c" * 40,
                    ("rev-parse", "HEAD~2"): "a" * 40,
                    ("diff", "--name-only", "HEAD~2", "HEAD~1"):
                        workflow + ("\njte-public/BTMS_WK08_run.m" if extra_source else ""),
                    ("diff", "--name-only", "HEAD~1", "HEAD"): str(self.marker)}[args]
        with patch.dict(os.environ, env, clear=True), patch.object(gate, "git", git), \
             patch.object(gate, "MARKER", str(self.marker)), \
             patch.dict(gate.CI5S, {"marker": str(self.marker)}), \
             patch.dict(gate.PREFLIGHT, {"marker": str(self.marker)}):
            return gate.context(check_only=getattr(self, "check_only", False))

    def test_valid_chain(self):
        self.assertEqual(self.invoke(), ("123", "c" * 40))

    def test_reject_unapproved_or_repeated_or_wrong_context(self):
        for changes in ({"GITHUB_RUN_ATTEMPT": "2"}, {"WK08_OWNER_APPROVAL": ""},
                        {"GITHUB_EVENT_NAME": "workflow_dispatch"},
                        {"WK08_PROTECTED_ENV_NAME": ""}, {"GITHUB_REF": "refs/heads/main"},
                        {"WK08_REVIEWED_SOURCE_SHA": "0" * 40}):
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                self.invoke(changes)

    def test_enable_commit_cannot_change_source(self):
        with self.assertRaises(RuntimeError):
            self.invoke(extra_source=True)

    def test_marker_cannot_contain_other_data(self):
        self.marker.write_text("NOT THE APPROVED MESSAGE")
        with self.assertRaises(RuntimeError):
            self.invoke()


class CI5SContextTests(ContextTests):
    def setUp(self):
        super().setUp()
        p = gate.config("CI_5S")
        self.env["WK08_MODE"] = "CI_5S"
        self.env["WK08_OWNER_APPROVAL"] = p["approval"]
        event = json.loads(self.event.read_text())
        event["head_commit"]["message"] = p["message"]
        self.event.write_text(json.dumps(event))
        self.marker.write_text(p["message"])

    def test_consumed_identity_cannot_authorize_ci5s_b(self):
        with self.assertRaises(RuntimeError):
            self.invoke({"WK08_OWNER_APPROVAL": "APPROVE_WK08_CI5S_ONCE_AFTER_CLAUDE_GO"})
        event = json.loads(self.event.read_text())
        event["head_commit"]["message"] = "WK08_CI_5S_ONE_SHOT_20261103"
        self.event.write_text(json.dumps(event))
        with self.assertRaises(RuntimeError):
            self.invoke()

    def test_r1_approval_cannot_authorize_ci5s(self):
        with self.assertRaises(RuntimeError):
            self.invoke({"WK08_OWNER_APPROVAL": gate.config("R1")["approval"]})

    def test_ci5s_message_cannot_authorize_r1(self):
        with self.assertRaises(RuntimeError):
            self.invoke({"WK08_MODE": "R1",
                         "WK08_OWNER_APPROVAL": gate.config("R1")["approval"]})

    def test_r1_trigger_message_rejected(self):
        event = json.loads(self.event.read_text())
        event["head_commit"]["message"] = gate.config("R1")["message"]
        self.event.write_text(json.dumps(event))
        with self.assertRaises(RuntimeError):
            self.invoke()


class IntentSeparationTests(unittest.TestCase):
    def test_each_mode_ignores_other_intent_but_blocks_its_own(self):
        for mode, other_mode in (("CI_5S", "R1"), ("R1", "CI_5S")):
            for own_exists in (False, True):
                with self.subTest(mode=mode, own_exists=own_exists), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp) / "scratch"
                    own = gate.config(mode)["intent"]
                    other = gate.config(other_mode)["intent"]
                    checked = []
                    def remote_query(token, folder, condition):
                        checked.append(condition)
                        self.assertNotIn(other, condition)
                        self.assertIn("JTE063_PENDING_" + own, condition)
                        self.assertIn("JTE063_VERIFIED_" + own, condition)
                        return [{"id": "prior"}] if own_exists else []
                    with patch.dict(os.environ, {"WK08_MODE": mode}, clear=True), \
                         patch.object(gate, "ROOT", root), \
                         patch.object(gate, "query", remote_query), \
                         patch.object(gate, "upload") as upload:
                        if own_exists:
                            with self.assertRaises(RuntimeError):
                                gate.reserve_one_shot("token", "folder", "123", "c"*40)
                            upload.assert_not_called()
                            self.assertFalse(root.exists())
                        else:
                            gate.reserve_one_shot("token", "folder", "123", "c"*40)
                            self.assertTrue((root / own).is_file())
                            self.assertFalse((root / other).exists())
                            payload = json.loads((root / own).read_text())
                            self.assertEqual(payload["schema"], gate.config()["schema"])
                            upload.assert_called_once()
                    self.assertEqual(len(checked), 1)

    def test_receipts_and_horizons_are_separate(self):
        names = {}
        for mode, horizon in (("CI_5S", 5), ("R1", 340)):
            with patch.dict(os.environ, {"WK08_MODE": mode}, clear=True):
                p = gate.config()
                self.assertEqual(p["stopTime_s"], horizon)
                names[mode] = gate.receipt_name("123")
        self.assertNotEqual(names["CI_5S"], names["R1"])
        self.assertNotEqual(gate.config("CI_5S")["schema"], gate.config("R1")["schema"])

    def test_unknown_mode_rejected(self):
        with self.assertRaises(RuntimeError):
            gate.config("CI_340S")


class CI5SPublishTests(unittest.TestCase):
    def test_unreadable_paused_files_cannot_be_upgraded_by_terminal_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scratch"
            (root / "native").mkdir(parents=True)
            manifest = {"run": "123", "commit": "c"*40, "mode": "CI_5S",
                "stopTime_s": 5, "inputCodeSHA256": {"source": "hash"},
                "inputs": [{"local": "source.slx", "sha256": "hash"}]}
            flags = {"run": "123", "commit": "c"*40, "mode": "CI_5S",
                "status": "UNQUALIFIED", "allPausedNativeReadable": False}
            monitor = {"run": "123", "commit": "c"*40, "mode": "CI_5S",
                "status": "PROCESS_EXIT_ZERO", "returncode": 0}
            for name, obj in (("WK08_MANIFEST.json", manifest),
                              ("WK08_FLAGS.json", flags), ("WK08_SUPERVISOR.json", monitor)):
                (root / name).write_text(json.dumps(obj))
            for role in gate.NATIVE:
                (root / "native" / ("WK08_" + role + ".mat")).write_bytes(b"synthetic")
            for name in ("WK08_PREPARED_PROOF.mat", "WK08R1.slx", "WK08_RESOURCES.jsonl"):
                (root / name).write_bytes(b"synthetic")
            with patch.dict(os.environ, {"WK08_MODE": "CI_5S"}, clear=True), \
                 patch.object(gate, "ROOT", root), patch.object(gate, "drive", return_value=("t", "app")), \
                 patch.object(gate, "btms_dats_folder", return_value="private-BTMS-DATS"), \
                 patch.object(gate, "sha", return_value="hash"), \
                 patch.object(gate, "code_hashes", return_value={"source": "hash"}), \
                 patch.object(gate, "upload", return_value={"integrity": "FULL_REMOTE_READBACK_VERIFIED"}) as upload:
                with self.assertRaises(RuntimeError):
                    gate.publish("123", "c"*40)
                receipt = json.loads((root / gate.receipt_name("123")).read_text())
                self.assertTrue(receipt["requiredPayloadComplete"])
                self.assertEqual(receipt["status"], "UNQUALIFIED")
                self.assertEqual(receipt["schema"], gate.CI5S["schema"])
                self.assertFalse((root / "WK08_DELIVERY_VERIFIED").exists())
                self.assertTrue(all(c.args[1] == "private-BTMS-DATS" for c in upload.call_args_list))


class SafeFailureLoggingTests(unittest.TestCase):
    prefixes = ("WK08_PRIVATE_GATE_UNQUALIFIED", "WK08_SUPERVISOR_UNQUALIFIED")

    def test_allowlisted_need_codes_are_printed_exactly(self):
        for reason in ("WK08_DRIVE_RESERVE", "WK08_MATLAB_BATCH_UNAVAILABLE", "WK06_CONTEXT_DENIED",
                       "WK04_INPUT_SHA", "JTE063_REMOTE_SIZE_MISMATCH",
                       "AMBIGUOUS_APP_FOLDER", "GOOGLE_API_HTTP_400", "GOOGLE_API_HTTP_503",
                       "GOOGLE_API_TRANSPORT_FAILED", "OAUTH_REFRESH_FAILED",
                       "JTE101_REFERENCE_NOT_UNIQUE"):
            for prefix in self.prefixes:
                with self.subTest(reason=reason, prefix=prefix):
                    output = io.StringIO()
                    try:
                        gate.need(False, reason)
                    except RuntimeError as exc:
                        with redirect_stdout(output):
                            gate.report_failure(prefix, exc)
                    self.assertEqual(output.getvalue(),
                                     prefix + " code=RuntimeError reason=" + reason + "\n")

    def test_other_payloads_never_enter_public_logs(self):
        class PrivatePayload:
            def __str__(self):
                raise AssertionError("Private payload must never be rendered")
        cases = (
            RuntimeError("WK08_DRIVE_RESERVE /private/source.mat id=private-id token=secret"),
            RuntimeError("WK08_DRIVE_RESERVE\nsecret"),
            RuntimeError("WK08_DRIVE_RESERVE\n"),
            RuntimeError("WK08_lowercase"),
            RuntimeError("WK09_NOT_ALLOWED"),
            RuntimeError("GOOGLE_API_HTTP_40"),
            RuntimeError("GOOGLE_API_HTTP_4000"),
            RuntimeError("GOOGLE_API_HTTP_400 token=secret"),
            RuntimeError("GOOGLE_API_TRANSPORT_FAILED extra"),
            RuntimeError("OAUTH_REFRESH_FAILED secret"),
            RuntimeError("JTE101_lowercase"),
            RuntimeError("WK08_"),
            RuntimeError("AMBIGUOUS_APP_FOLDER extra"),
            RuntimeError("WK08_DRIVE_RESERVE", "secret"),
            RuntimeError(PrivatePayload()),
            ValueError("WK08_DRIVE_RESERVE"),
            KeyError("private-id"),
        )
        for exc in cases:
            for prefix in self.prefixes:
                with self.subTest(kind=type(exc).__name__, prefix=prefix):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        gate.report_failure(prefix, exc)
                    self.assertEqual(output.getvalue(),
                                     prefix + " code=" + type(exc).__name__ + "\n")

    def test_private_gate_entrypoint_uses_safe_reason(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"WK08_MODE": "INVALID"}, clear=True), redirect_stdout(output):
            with self.assertRaises(SystemExit) as exit_code:
                runpy.run_path(str(Path(gate.__file__)), run_name="__main__")
        self.assertEqual(exit_code.exception.code, 1)
        self.assertEqual(output.getvalue(),
            "WK08_PRIVATE_GATE_UNQUALIFIED code=RuntimeError reason=WK08_MODE_DENIED\n")

    def test_supervisor_entrypoint_uses_safe_reason_without_launch(self):
        def denied_context():
            gate.need(False, "WK08_DRIVE_RESERVE")
        output = io.StringIO()
        with patch.object(gate, "context", denied_context), redirect_stdout(output):
            with self.assertRaises(SystemExit) as exit_code:
                runpy.run_path(str(Path(gate.__file__).with_name("WK08_supervise.py")),
                              run_name="__main__")
        self.assertEqual(exit_code.exception.code, 1)
        self.assertEqual(output.getvalue(),
            "WK08_SUPERVISOR_UNQUALIFIED code=RuntimeError reason=WK08_DRIVE_RESERVE\n")


class PreflightContextTests(ContextTests):
    def setUp(self):
        super().setUp()
        self.check_only = True
        self.env["WK08_OWNER_APPROVAL"] = gate.PREFLIGHT["approval"]
        event = json.loads(self.event.read_text())
        event["head_commit"]["message"] = gate.PREFLIGHT["message"]
        self.event.write_text(json.dumps(event))
        self.marker.write_text(gate.PREFLIGHT["message"])

    def test_accepts_both_run_modes(self):
        for mode in ("R1", "CI_5S"):
            with self.subTest(mode=mode):
                self.assertEqual(self.invoke({"WK08_MODE": mode}), ("123", "c"*40))

    def test_run_approval_cannot_authorize_check(self):
        for mode in ("R1", "CI_5S"):
            with self.subTest(mode=mode), self.assertRaises(RuntimeError):
                self.invoke({"WK08_OWNER_APPROVAL": gate.config(mode)["approval"]})


class ReadonlyPreflightTests(unittest.TestCase):
    def invoke(self, fault=None, mode="CI_5S"):
        prefix = "BTMS_M2_40701917441_"
        workspace = b"synthetic private workspace"
        workspace_sha = hashlib.sha256(workspace).hexdigest()
        model_sha = hashlib.sha256(b"synthetic model metadata").hexdigest()
        manifest = {"inputs": [{"local": "source_workspace.mat", "sha256": workspace_sha}]}
        if fault == "workspace":
            manifest["inputs"][0]["sha256"] = "0"*64
        proof = {"instrumentedModelSHA256": model_sha, "period_s": .01,
                 "trueT312CompiledWidthVerified": True,
                 "fullRetainedParametersConfigGraphParity": True}
        payloads = {
            prefix + "B0L_Ref_LOGGER.slx": b"synthetic model metadata",
            prefix + "B0L_Ref_PROOF.json": json.dumps(proof).encode(),
            prefix + "INPUT_MANIFEST.json": json.dumps(manifest).encode(),
            "JTE101_40449421507_PREPARE_WORKSPACE.mat": workspace,
        }
        receipt = {"run": "40701917441",
                   "commit": "75afa01be55339d20ce5831830a0cacdb0c5d3f4",
                   "physicalRun": False, "files": [
                       {"name": n, "sha256": hashlib.sha256(b).hexdigest(),
                        "integrity": "FULL_REMOTE_READBACK_VERIFIED"}
                       for n, b in payloads.items() if n.startswith(prefix)]}
        payloads[prefix + "PRIVATE_RECEIPT.json"] = json.dumps(receipt).encode()
        metas = {n: {"id": "private-id-" + str(i), "name": "JTE063_VERIFIED_" + n,
                     "size": len(b), "md5Checksum": hashlib.md5(b).hexdigest(),
                     "appProperties": {"state": "VERIFIED",
                                       "sha256": hashlib.sha256(b).hexdigest()}}
                 for i, (n, b) in enumerate(payloads.items())}
        requests = []
        def req(url, **kwargs):
            self.assertEqual(kwargs.get("method", "GET"), "GET")
            requests.append(url)
            if "spaces=drive" in url:
                rows = [] if fault == "missing_folder" else [{"id": "private-folder-id"}]
                return 200, {}, json.dumps({"files": rows}).encode()
            return 200, {}, json.dumps({"permissions": [{"type": "user", "role": "owner"}]}).encode()
        def lookup(token, folder, name):
            if fault == "duplicate_asset":
                gate.need(False, "JTE101_REFERENCE_NOT_UNIQUE")
            return metas[name.removeprefix("JTE063_VERIFIED_")]
        queried = []
        def query(token, folder, condition):
            queried.append(condition)
            if fault == "consumed_old":
                return [{"id": "consumed-evidence"}] if "WK08_CI5S_ATTEMPT_INTENT_20261103.json" in condition else []
            return [{"id": "reserved"}] if fault in ("R1", "CI_5S") and (
                gate.config(fault)["intent"] in condition) else []
        by_id = {m["id"]: payloads[n] for n, m in metas.items()}
        downloads = []
        def urlopen(request, **kwargs):
            # JTE101.download verifies real SHA/MD5 against the synthetic response.
            file_id = request.full_url.split("/")[-1].split("?")[0]
            downloads.append(file_id)
            return io.BytesIO(by_id[file_id])
        temporary_paths = []
        real_temporary = tempfile.TemporaryDirectory
        def temporary(*args, **kwargs):
            result = real_temporary(*args, **kwargs)
            temporary_paths.append(Path(result.name))
            return result

        with real_temporary() as base, ExitStack() as stack:
            root = Path(base) / "actuator-review-private"
            env = {"WK08_MODE": mode, "JTE_GOOGLE_CLIENT_ID": "dummy",
                   "JTE_GOOGLE_CLIENT_SECRET": "dummy", "JTE_GOOGLE_REFRESH_TOKEN": "dummy"}
            stack.enter_context(patch.dict(os.environ, env, clear=True))
            stack.enter_context(patch.object(gate, "ROOT", root))
            stack.enter_context(patch.object(gate, "access_token", return_value="private-token"))
            stack.enter_context(patch.object(gate, "req", req))
            stack.enter_context(patch.object(gate, "one", lookup))
            stack.enter_context(patch.object(gate, "query", query))
            stack.enter_context(patch.object(gate, "quota",
                return_value={"availableBytes": 3*gate.GiB if fault == "quota" else 4*gate.GiB}))
            neutral = stack.enter_context(patch.object(gate, "require_verified_neutral_preflight"))
            stack.enter_context(patch("urllib.request.urlopen", urlopen))
            stack.enter_context(patch.object(gate.tempfile, "TemporaryDirectory", temporary))
            forbidden = {}
            for name in ("ensure_app_folder", "drive", "reserve_one_shot", "upload",
                         "upload_verified", "get", "btms_dats_folder"):
                forbidden[name] = stack.enter_context(patch.object(gate, name,
                    side_effect=AssertionError("Write-capable helper must not be used")))
            output = io.StringIO()
            error = None
            with redirect_stdout(output):
                try:
                    gate.check("123", "c"*40)
                except Exception as exc:
                    error = exc
            self.assertFalse(root.exists())
            self.assertTrue(all(not p.exists() for p in temporary_paths))
            for spy in forbidden.values():
                spy.assert_not_called()
            text = output.getvalue()
            for private in ("private-token", "private-folder-id", "private-id-",
                            workspace_sha, model_sha, str(root)):
                self.assertNotIn(private, text)
            if fault != "missing_folder":
                neutral.assert_called_once()
        return text, error, queried, downloads, temporary_paths

    def test_all_checks_pass_readonly_and_temp_is_deleted(self):
        for mode in ("R1", "CI_5S"):
            with self.subTest(mode=mode):
                text, error, queried, downloaded, temporary = self.invoke(mode=mode)
                self.assertIsNone(error)
                self.assertTrue(text.endswith("WK08_PREFLIGHT_ALL_PASS\n"))
                self.assertEqual(len(queried), 2)
                self.assertEqual(len(downloaded), 4)  # 3 JSON + workspace; no model download
                self.assertEqual(len(temporary), 1)

    def test_preflight_accepts_consumed_old_ci5s_intent(self):
        text, error, queried, _, _ = self.invoke(fault="consumed_old")
        self.assertIsNone(error)
        self.assertIn("WK08_PREFLIGHT_ALL_PASS", text)
        self.assertTrue(any("WK08_CI5S_ATTEMPT_INTENT_20261103B.json" in q for q in queried))
        self.assertFalse(any("WK08_CI5S_ATTEMPT_INTENT_20261103.json" in q for q in queried))

    def test_failures_do_not_reserve_upload_or_claim_success(self):
        for fault, reason in (
            ("missing_folder", "WK08_PREFLIGHT_APP_FOLDER_MISSING"),
            ("quota", "WK08_DRIVE_RESERVE"),
            ("R1", "WK08_ALREADY_RESERVED_NO_RETRY"),
            ("CI_5S", "WK08_ALREADY_RESERVED_NO_RETRY"),
            ("duplicate_asset", "JTE101_REFERENCE_NOT_UNIQUE"),
            ("workspace", "WK08_WORKSPACE"),
        ):
            with self.subTest(fault=fault):
                text, error, _, _, _ = self.invoke(fault=fault)
                self.assertIsInstance(error, RuntimeError)
                self.assertIn("=FAIL reason=" + reason, text)
                self.assertNotIn("WK08_PREFLIGHT_ALL_PASS", text)


class B2IdentityTests(unittest.TestCase):
    def test_ci5s_b_identity_and_r1_identity(self):
        p = gate.config("CI_5S")
        self.assertEqual(p["intent"], "WK08_CI5S_ATTEMPT_INTENT_20261103B.json")
        self.assertEqual(p["message"], "WK08_CI_5S_ONE_SHOT_20261103B")
        self.assertEqual(p["approval"], "APPROVE_WK08_CI5S_B_ONCE_AFTER_CLAUDE_GO")
        with patch.dict(os.environ, {"WK08_MODE": "CI_5S"}, clear=True):
            self.assertEqual(gate.receipt_name("123"), "WK08_CI5S_123_PRIVATE_RECEIPT_20261103B.json")
        p = gate.config("R1")
        self.assertEqual(p["intent"], "WK08_R1_ATTEMPT_INTENT_20261102.json")
        self.assertEqual(p["message"], "WK08_PACK_340S_ONE_SHOT_20261102")
        self.assertEqual(p["approval"], "APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO")
        with patch.dict(os.environ, {"WK08_MODE": "R1"}, clear=True):
            self.assertEqual(gate.receipt_name("123"), "WK08_123_PRIVATE_RECEIPT.json")


class SupervisorLauncherTests(unittest.TestCase):
    def run_mocked(self, mode, returncode=0, available=True, limit=None):
        # Popen, OAuth/Drive, clocks and /proc probes are mocked; no launcher runs.
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            (root / "WK08_MANIFEST.json").write_text(json.dumps({
                "mode": mode, "stopTime_s": 5 if mode == "CI_5S" else 340,
                "run": "123", "commit": "c"*40}))
            child_context = {"WK08_MODE": mode, "WK08_JOB_START_EPOCH": "1000",
                "GITHUB_SHA": "c"*40, "GITHUB_RUN_ID": "123",
                "GITHUB_REPOSITORY": gate.REPO, "GITHUB_ACTIONS": "true",
                "RUNNER_TEMP": "/runner/temp", "RUNNER_TOOL_CACHE": "/runner/cache",
                "PATH": "/runner/bin", "CUSTOM_SETTING": "kept",
                "JTE_GOOGLE_CLIENT_ID": "private-client",
                "JTE_GOOGLE_CLIENT_SECRET": "private-secret",
                "JTE_GOOGLE_REFRESH_TOKEN": "private-refresh",
                "GH_TOKEN": "private-gh", "GITHUB_TOKEN": "private-github"}
            stack.enter_context(patch.dict(os.environ, child_context, clear=True))
            stack.enter_context(patch.object(supervisor, "ROOT", root))
            stack.enter_context(patch.object(supervisor, "context", return_value=("123", "c"*40)))
            stack.enter_context(patch.object(supervisor, "drive", return_value=("token", "folder")))
            stack.enter_context(patch.object(supervisor, "quota", return_value={"availableBytes": 8*gate.GiB}))
            stack.enter_context(patch.object(supervisor, "memory",
                return_value={"hostAvailable": 16*gate.GiB, "cgroupAvailable": 16*gate.GiB}))
            stack.enter_context(patch.object(supervisor.shutil, "disk_usage",
                return_value=SimpleNamespace(free=20*gate.GiB)))
            launcher = "/opt/hostedtoolcache/matlab-batch/bin/matlab-batch"
            which = stack.enter_context(patch.object(supervisor.shutil, "which",
                return_value=launcher if available else None))
            stack.enter_context(patch.object(supervisor.time, "time", return_value=1000))
            stack.enter_context(patch.object(supervisor.time, "monotonic", return_value=10))
            stack.enter_context(patch.object(supervisor.time, "sleep"))
            stack.enter_context(patch.object(supervisor, "proc_start", return_value="identity"))
            stack.enter_context(patch.object(supervisor, "proc_rss", return_value=gate.GiB))
            violation = stack.enter_context(patch.object(supervisor, "violation", return_value=limit))
            terminate = stack.enter_context(patch.object(supervisor, "terminate_tree"))
            proc = SimpleNamespace(pid=4321)
            from unittest.mock import Mock
            proc.poll = Mock(side_effect=[None, returncode])
            proc.wait = Mock(return_value=returncode)
            payload = b"License checkout failed. private-console-id\n" + b"x"*2500
            def launch(argv, **kwargs):
                kwargs["stdout"].write(payload)
                kwargs["stdout"].flush()
                return proc
            popen = stack.enter_context(patch.object(supervisor.subprocess, "Popen", side_effect=launch))
            output = io.StringIO()
            error = None
            result = None
            with redirect_stdout(output):
                try:
                    result = supervisor.main()
                except RuntimeError as exc:
                    error = exc
            which.assert_called_once_with("matlab-batch")
            if not available:
                popen.assert_not_called()
                self.assertEqual(gate.safe_failure_reason(error), "WK08_MATLAB_BATCH_UNAVAILABLE")
                return
            self.assertIsNone(error)
            popen.assert_called_once()
            self.assertEqual(popen.call_args.args[0], [launcher,
                "addpath('jte-public'); BTMS_WK08_run('actuator-review-private/WK08_MANIFEST.json')"])
            expected_env = {k: v for k, v in child_context.items()
                            if not k.startswith("JTE_GOOGLE_") and k not in {"GH_TOKEN", "GITHUB_TOKEN"}}
            self.assertEqual(popen.call_args.kwargs["env"], expected_env)
            report = json.loads((root / "WK08_SUPERVISOR.json").read_text())
            self.assertEqual(report["consoleExcerptBytes"], 2048)
            self.assertEqual(base64.b64decode(report["consoleExcerptBase64"]), payload[:2048])
            self.assertEqual(report["consoleExcerpt"], payload[:2048].decode())
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(report["matlabProcessesLaunched"], 1)
            self.assertFalse(report["automaticRetry"])
            violation.assert_called_once()
            self.assertEqual(violation.call_args.kwargs["wall"], 1185)
            if limit:
                terminate.assert_called_once_with(4321, "identity")
                self.assertEqual(result, 1)
            else:
                terminate.assert_not_called()
                self.assertEqual(result, 0 if returncode == 0 else 1)

    def test_matlab_batch_argv_env_and_private_console_for_both_modes(self):
        for mode in ("R1", "CI_5S"):
            for returncode in (0, 1):
                with self.subTest(mode=mode, returncode=returncode):
                    self.run_mocked(mode, returncode=returncode)

    def test_missing_matlab_batch_fails_without_fallback(self):
        self.run_mocked("CI_5S", available=False)

    def test_watchdog_still_terminates_the_single_process(self):
        self.run_mocked("CI_5S", limit="HOST_RAM_RESERVE")


class WorkflowLauncherPreflightTests(unittest.TestCase):
    def test_launcher_check_is_between_setup_and_reservation_in_both_workflows(self):
        root = Path(__file__).resolve().parents[1]
        command = "command -v matlab-batch >/dev/null || { echo WK08_MATLAB_BATCH_UNAVAILABLE; exit 1; }"
        for name in ("wk08-ci5s-one-shot.yml", "wk08-pack-one-shot.yml"):
            with self.subTest(workflow=name):
                source = (root / ".github/workflows" / name).read_text()
                self.assertIn("if: " + "$" + "{{ false }}", source)
                steps = re.split(r"(?m)^      - ", source)[1:]
                setup = [i for i, step in enumerate(steps) if "uses: matlab-actions/setup-matlab@" in step]
                check = [i for i, step in enumerate(steps) if command in step]
                reserve = [i for i, step in enumerate(steps) if "python3 jte-public/WK08_private_gate.py prepare" in step]
                self.assertEqual(len(setup), 1)
                self.assertEqual(len(check), 1)
                self.assertEqual(len(reserve), 1)
                self.assertEqual(check[0], setup[0] + 1)
                self.assertEqual(reserve[0], check[0] + 1)
                self.assertIn("shell: bash", steps[check[0]])


class FixedGeometryTests(unittest.TestCase):
    def test_per_module_counts_and_axial_locations(self):
        with (Path(__file__).parent / "WK08_sparse_sets.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        cells = [36, 36, 36, 48, 48, 36, 36, 36]
        for count, per_module in ((312, None), (16, 2), (8, 1)):
            subset = [r for r in rows if int(r["sensor_count"]) == count]
            self.assertEqual(len(subset), count)
            self.assertEqual(len({r["channel"] for r in subset}), count)
            offset = 0
            for module, n in enumerate(cells, 1):
                selected = [r for r in subset if int(r["module"]) == module]
                self.assertEqual(len(selected), n if per_module is None else per_module)
                local = [int(r["local_cell"]) for r in selected]
                expected = list(range(1, n+1)) if count == 312 else (
                    [n//4, 3*n//4] if count == 16 else [n//2])
                self.assertEqual(local, expected)
                self.assertEqual([int(r["channel"]) for r in selected],
                                 [offset + k for k in expected])
                offset += n


class BiasGuardSourceTests(unittest.TestCase):
    def test_unsensed_bias_rejected_after_neutral_return_before_graph_edits(self):
        # Offline source contract only; MATLAB runtime behavior is tested separately
        # by test_BTMS_WK08_inject_guard.m (not executed by Codex).
        source = (Path(__file__).parent / "BTMS_WK08_inject.m").read_text()
        neutral = re.search(
            r"if\s+b==0\s*&&\s*isequal\(S,1:312\)[\s\S]*?\breturn\s+end",
            source,
        )
        self.assertIsNotNone(neutral, "Neutral identity bypass must remain present")
        tail = source[neutral.end():]
        guard = re.match(
            r"\s*assert\(ismember\(j,S\),'WK08:BiasNotSensed',\s*\.\.\.\s*"
            r"'Biased channel must be in the sensed subset\.'\);",
            tail,
        )
        self.assertIsNotNone(guard, "Reject unsensed biased channels on the non-neutral path")
        mutation = re.search(r"\b(?:add_block|delete_line|add_line|set_param)\s*\(", source)
        self.assertIsNotNone(mutation)
        self.assertLess(neutral.end() + guard.end(), mutation.start(),
                        "The bias guard must reject before the first graph edit")


if __name__ == "__main__":
    unittest.main()
