"""Author checks only: offline authorization and fixed topology; no MATLAB/CI."""
import csv
import json
import os
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import WK08_private_gate as gate


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
        workflow = gate.config(env.get("WK08_MODE", "R1"))["workflow"]
        def git(*args):
            return {("rev-parse", "HEAD"): "c" * 40,
                    ("rev-parse", "HEAD~2"): "a" * 40,
                    ("diff", "--name-only", "HEAD~2", "HEAD~1"):
                        workflow + ("\njte-public/BTMS_WK08_run.m" if extra_source else ""),
                    ("diff", "--name-only", "HEAD~1", "HEAD"): str(self.marker)}[args]
        with patch.dict(os.environ, env, clear=True), patch.object(gate, "git", git), \
             patch.object(gate, "MARKER", str(self.marker)), \
             patch.dict(gate.CI5S, {"marker": str(self.marker)}):
            return gate.context()

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
