import unittest
from JTE072_upload_group import guard,TRIGGER
from JTE062_google_drive_synthetic import EXPECTED_REPO
import JTE063_streaming_drive as transfer
class GroupAuthorization(unittest.TestCase):
 def context(self):
  return {"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER}},{"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"}
 def test_three_groups_allowed(self):
  for g in ("early","mid","late"):
   event,e=self.context();self.assertIsNone(guard(event,e,g))
 def test_no_bad_group(self):
  event,e=self.context()
  for g in ("hot","middle","random",""):
   with self.assertRaises(PermissionError):guard(event,e,g)
 def test_no_untrusted_events(self):
  event,e=self.context();e["GITHUB_EVENT_NAME"]="pull_request"
  with self.assertRaises(PermissionError):guard(event,e,"mid")
 def test_no_untrusted_branch(self):
  event,e=self.context();e["GITHUB_REF"]="refs/heads/other"
  with self.assertRaises(PermissionError):guard(event,e,"mid")
 def test_no_acceptance_bypass(self):
  with self.assertRaises(ValueError):
   transfer.upload_verified("FAKE","FAKE","none",schema="JTE072_G7_COMPLETE")
if __name__=="__main__":unittest.main()
