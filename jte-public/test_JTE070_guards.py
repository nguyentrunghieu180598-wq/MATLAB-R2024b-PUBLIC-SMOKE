"""JTE070 synthetic permissions/schema tests. No Google credentials or MATLAB."""
import unittest
from JTE070_upload_strictfine import guard,TRIGGER
from JTE062_google_drive_synthetic import EXPECTED_REPO
import JTE063_streaming_drive as uploader
class Cases(unittest.TestCase):
  def e(self):
    return {"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER}},{"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"}
  def test_allowed_both(self):
    x,y=self.e()
    for case in ("B0L","C0"):self.assertIsNone(guard(x,y,case))
  def test_branch_fail(self):
    x,y=self.e();y["GITHUB_REF"]="refs/heads/other"
    with self.assertRaises(PermissionError):guard(x,y,"C0")
  def test_event_fail(self):
    x,y=self.e();y["GITHUB_EVENT_NAME"]="pull_request"
    with self.assertRaises(PermissionError):guard(x,y,"C0")
  def test_wrong_trigger_fail(self):
    x,y=self.e();x["head_commit"]["message"]="wrong"
    with self.assertRaises(PermissionError):guard(x,y,"B0L")
  def test_wrong_repo_fail(self):
    x,y=self.e();x["repository"]["full_name"]="other/repo"
    with self.assertRaises(PermissionError):guard(x,y,"B0L")
  def test_g5_accepted_schema_rejected(self):
    with self.assertRaises(ValueError):uploader.upload_verified("dummy","dummy","missing",schema="JTE070_G5_ACCEPTED")
if __name__=="__main__":unittest.main()
