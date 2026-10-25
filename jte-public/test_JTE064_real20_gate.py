"""Offline guards for JTE064; no credentials, no MATLAB, no Drive."""
import unittest
from unittest.mock import patch
from JTE064_real20_private_upload import guard, TRIGGER
from JTE062_google_drive_synthetic import EXPECTED_REPO
import JTE063_streaming_drive as transfer

class Real20GuardTests(unittest.TestCase):
    def fixture(self):
        event={"repository":{"full_name":EXPECTED_REPO,"private":False},
               "head_commit":{"message":TRIGGER}}
        env={"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"}
        return event,env
    def test_exact_owner_event_passes(self):
        event,env=self.fixture()
        self.assertIsNone(guard(event,env))
    def test_wrong_branch_denied(self):
        event,env=self.fixture();env["GITHUB_REF"]="refs/heads/feature"
        with self.assertRaises(PermissionError):guard(event,env)
    def test_wrong_message_denied(self):
        event,env=self.fixture();event["head_commit"]["message"]="untrusted"
        with self.assertRaises(PermissionError):guard(event,env)
    def test_pr_event_denied(self):
        event,env=self.fixture();env["GITHUB_EVENT_NAME"]="pull_request"
        with self.assertRaises(PermissionError):guard(event,env)
    def test_public_repository_identity_pinned(self):
        event,env=self.fixture();event["repository"]["full_name"]="attacker/repo"
        with self.assertRaises(PermissionError):guard(event,env)
    def test_private_repository_mismatch_denied(self):
        event,env=self.fixture();event["repository"]["private"]=True
        with self.assertRaises(PermissionError):guard(event,env)
    def test_unexpected_drive_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_SCHEMA"):
            transfer.upload_verified("FAKE","FAKE","missing.mat",schema="G5_ACCEPTED")
    def test_20s_schema_supported_not_g5(self):
        import tempfile
        from pathlib import Path
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"pilot.mat";path.write_bytes(b"synthetic")
            md5=hashlib.md5(b"synthetic",usedforsecurity=False).hexdigest()
            sha=hashlib.sha256(b"synthetic").hexdigest()
            with patch.object(transfer,"_session",return_value="https://www.googleapis.com/upload/drive/v3/files?upload_id=x") as create,patch.object(transfer,"upload_chunks",return_value={"id":"fake","size":9,"md5Checksum":md5}),patch.object(transfer,"readback_sha",return_value=sha),patch.object(transfer,"_http",return_value=(200,{},b"")) as commit:
                a=transfer.upload_verified("FAKE","FAKE",path,schema="JTE056_DIAGNOSTIC20_NOT_G5")
                self.assertEqual(a["size_bytes"],9)
                self.assertEqual(create.call_args.args[-1],"JTE056_DIAGNOSTIC20_NOT_G5")
                self.assertIn("JTE056_DIAGNOSTIC20_NOT_G5",commit.call_args.kwargs["data"].decode())

if __name__=="__main__":
    unittest.main()
