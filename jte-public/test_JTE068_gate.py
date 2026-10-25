"""JTE068 alternate regime guard tests, no secrets or physics outputs."""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
from JTE062_google_drive_synthetic import EXPECTED_REPO
from JTE068_upload_active_C0 import guard,TRIGGER
import JTE063_streaming_drive as tr

class ActiveGuardTests(unittest.TestCase):
 def context(self):
  return ({"repository":{"full_name":EXPECTED_REPO,"private":False},
            "head_commit":{"message":TRIGGER}},
           {"GITHUB_REF":"refs/heads/main","GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_EVENT_NAME":"push"})
 def test_trusted_context(self):
  e,v=self.context();self.assertIsNone(guard(e,v))
 def test_no_pr(self):
  e,v=self.context();v["GITHUB_EVENT_NAME"]="pull_request"
  with self.assertRaises(PermissionError):guard(e,v)
 def test_no_other_repo(self):
  e,v=self.context();e["repository"]["full_name"]="unauthorized/fork"
  with self.assertRaises(PermissionError):guard(e,v)
 def test_no_other_branch(self):
  e,v=self.context();v["GITHUB_REF"]="refs/heads/other"
  with self.assertRaises(PermissionError):guard(e,v)
 def test_no_other_commit(self):
  e,v=self.context();e["head_commit"]["message"]="forged"
  with self.assertRaises(PermissionError):guard(e,v)
 def test_raw_schema_without_g5_acceptance(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"synthetic.bin";p.write_bytes(b"synthetic")
   with patch.object(tr,"_session",side_effect=RuntimeError("DENIED_ON_PURPOSE")) as f:
    with self.assertRaisesRegex(RuntimeError,"DENIED_ON_PURPOSE"):
     tr.upload_verified("fake","fake",p,schema="JTE068_ACTIVE_C0_RAW_UNREVIEWED")
    self.assertEqual(f.call_args.args[-1],"JTE068_ACTIVE_C0_RAW_UNREVIEWED")
 def test_no_accepted_schema(self):
  with self.assertRaisesRegex(ValueError,"UNKNOWN_SCHEMA"):
   tr.upload_verified("fake","fake","invalid",schema="ACTIVATION_PROVEN")
if __name__=="__main__":unittest.main()
