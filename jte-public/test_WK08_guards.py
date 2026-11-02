"""Author checks only: offline authorization and fixed topology; no MATLAB/CI."""
import csv
import json
import os
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
        def git(*args):
            return {("rev-parse", "HEAD"): "c" * 40,
                    ("rev-parse", "HEAD~2"): "a" * 40,
                    ("diff", "--name-only", "HEAD~2", "HEAD~1"):
                        gate.WORKFLOW + ("\njte-public/BTMS_WK08_run.m" if extra_source else ""),
                    ("diff", "--name-only", "HEAD~1", "HEAD"): str(self.marker)}[args]
        with patch.dict(os.environ, env, clear=True), patch.object(gate, "git", git), \
             patch.object(gate, "MARKER", str(self.marker)):
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


if __name__ == "__main__":
    unittest.main()
