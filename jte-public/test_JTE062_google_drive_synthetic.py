"""SYNTHETIC ONLY unit tests; never uses Google OAuth credentials."""
import json
import unittest
from unittest.mock import patch
from JTE062_google_drive_synthetic import (
    EXPECTED_REPO, TEST_BYTES, synthetic_payload, digest,
    assert_synthetic_and_manual, ensure_app_folder, upload_synthetic,
    verify_download
)


class DriveOAuthSecurityFixture(unittest.TestCase):
    def good_event(self):
        return {"repository":{"full_name":EXPECTED_REPO,"private":False}}

    def test_right_context(self):
        self.assertTrue(assert_synthetic_and_manual(self.good_event(),EXPECTED_REPO,
            "refs/heads/main","workflow_dispatch"))

    def test_bad_branch_fails(self):
        with self.assertRaises(PermissionError):
            assert_synthetic_and_manual(self.good_event(),EXPECTED_REPO,
                "refs/heads/untrusted","workflow_dispatch")

    def test_pr_event_fails(self):
        with self.assertRaises(PermissionError):
            assert_synthetic_and_manual(self.good_event(),EXPECTED_REPO,
                "refs/heads/main","pull_request")

    def test_wrong_repo_fails(self):
        with self.assertRaises(PermissionError):
            assert_synthetic_and_manual(self.good_event(),"outsider/wrong",
                "refs/heads/main","workflow_dispatch")

    def test_nonpublic_context_fails(self):
        d=self.good_event();d['repository']['private']=True
        with self.assertRaises(PermissionError):
            assert_synthetic_and_manual(d,EXPECTED_REPO,"refs/heads/main","workflow_dispatch")

    def test_synthetic_size_deterministic(self):
        self.assertEqual(len(synthetic_payload()), TEST_BYTES)
        self.assertEqual(digest(synthetic_payload()),digest(synthetic_payload()))

    def test_existing_app_folder(self):
        with patch("JTE062_google_drive_synthetic.req", return_value=(200,{},
            json.dumps({"files":[{"id":"app-created-test-id"}]}).encode())):
            self.assertEqual(ensure_app_folder("FAKE"),"app-created-test-id")

    def test_ambiguous_folder_fails(self):
        with patch("JTE062_google_drive_synthetic.req",return_value=(200,{},
            json.dumps({"files":[{"id":"A"},{"id":"B"}]}).encode())):
            with self.assertRaisesRegex(RuntimeError,"AMBIGUOUS"):
                ensure_app_folder("FAKE")

    def test_upload_requires_google_location(self):
        with patch("JTE062_google_drive_synthetic.req",return_value=(200,
            {"Location":"https://attacker.example/steal"},b"")):
            with self.assertRaisesRegex(RuntimeError,"SESSION"):
                upload_synthetic("FAKE","folder",b"synthetic","999")

    def test_upload_requires_committed_size(self):
        responses=[
            (200,{"Location":"https://www.googleapis.com/upload/drive/v3/files?upload_id=synthetic"},b""),
            (200,{},json.dumps({"id":"id","size":"9"}).encode())
        ]
        with patch("JTE062_google_drive_synthetic.req",side_effect=responses):
            with self.assertRaisesRegex(RuntimeError,"SIZE"):
                upload_synthetic("FAKE","folder",b"synthetic","999")

    def test_readback_mismatch_fails(self):
        with patch("JTE062_google_drive_synthetic.req",return_value=(200,{},b"corrupt")):
            with self.assertRaisesRegex(RuntimeError,"SHA_MISMATCH"):
                verify_download("FAKE","id",b"synthetic")

    def test_readback_exact_pass(self):
        with patch("JTE062_google_drive_synthetic.req",return_value=(200,{},b"synthetic")):
            self.assertEqual(verify_download("FAKE","id",b"synthetic"),digest(b"synthetic"))

if __name__=="__main__":
    unittest.main()
