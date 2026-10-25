"""Synthetic guards only, no Drive calls, no MAT data."""
import unittest
from unittest.mock import patch
from JTE062_google_drive_synthetic import EXPECTED_REPO
from JTE065_upload_raw_G5 import guard as g5guard, TRIGGER as G5
from JTE065_private_192MiB_synthetic import guard as capguard,TRIGGER as CAP
import JTE063_streaming_drive as transport
class GateTests(unittest.TestCase):
    def context(self, msg):
        return ({"repository":{"full_name":EXPECTED_REPO,"private":False},
                 "head_commit":{"message":msg}},
                {"GITHUB_REPOSITORY":EXPECTED_REPO,
                 "GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"})
    def test_cap_trigger(self):
        e,v=self.context(CAP);self.assertIsNone(capguard(e,v))
    def test_cap_wrong_event_rejected(self):
        e,v=self.context(CAP);v["GITHUB_EVENT_NAME"]="pull_request"
        with self.assertRaises(PermissionError):capguard(e,v)
    def test_cap_wrong_message_rejected(self):
        e,v=self.context(CAP);e["head_commit"]["message"]=G5
        with self.assertRaises(PermissionError):capguard(e,v)
    def test_cap_fake_repo_rejected(self):
        e,v=self.context(CAP);e["repository"]["full_name"]="attacker/fork"
        with self.assertRaises(PermissionError):capguard(e,v)
    def test_g5_four_scenarios(self):
        e,v=self.context(G5)
        for case in ("B0L","C0"):
            for solver in ("original","fine"):
                self.assertIsNone(g5guard(e,v,case,solver))
    def test_g5_nonzero_bias_or_malformed_denied(self):
        e,v=self.context(G5)
        for case,solver in [("C1","fine"),("C0","biased"),("B0L",""),("C0","unknown")]:
            with self.assertRaises(PermissionError):g5guard(e,v,case,solver)
    def test_g5_wrong_branch_denied(self):
        e,v=self.context(G5);v["GITHUB_REF"]="refs/heads/not-main"
        with self.assertRaises(PermissionError):g5guard(e,v,"C0","original")
    def test_g5_wrong_event_denied(self):
        e,v=self.context(G5);v["GITHUB_EVENT_NAME"]="workflow_dispatch"
        with self.assertRaises(PermissionError):g5guard(e,v,"C0","original")
    def test_g5_wrong_message_denied(self):
        e,v=self.context(CAP)
        with self.assertRaises(PermissionError):g5guard(e,v,"B0L","fine")
    def test_g5_private_repo_denied(self):
        e,v=self.context(G5);e["repository"]["private"]=True
        with self.assertRaises(PermissionError):g5guard(e,v,"B0L","fine")
    def test_schema_not_acceptance(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"synthetic.bin";p.write_bytes(b"test")
            with patch.object(transport,"_session",side_effect=RuntimeError("NO_REMOTE")) as stub:
                with self.assertRaisesRegex(RuntimeError,"NO_REMOTE"):
                    transport.upload_verified("fake","fake",p,schema="JTE065_G5_RAW_UNREVIEWED")
                self.assertEqual(stub.call_args.args[-1],"JTE065_G5_RAW_UNREVIEWED")
    def test_unrecognized_schema_denied(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_SCHEMA"):
            transport.upload_verified("x","x","no.mat",schema="G5_PASS")
if __name__=="__main__":unittest.main()
