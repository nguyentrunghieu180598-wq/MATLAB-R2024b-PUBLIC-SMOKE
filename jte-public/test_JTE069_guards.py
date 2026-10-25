import unittest
from JTE069_upload_active_G6 import guard,TRIGGER
from JTE062_google_drive_synthetic import EXPECTED_REPO
import JTE063_streaming_drive as transfer
class GuardTests(unittest.TestCase):
  def test_good_three(self):
    for site in ("hot","middle","cold"):
      self.assertIsNone(guard({"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER}},{"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"},site))
  def test_denied_events(self):
    base={"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER}}
    env={"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"}
    for k,v in (("GITHUB_REF","refs/heads/foreign"),("GITHUB_EVENT_NAME","pull_request"),("GITHUB_REPOSITORY","other/repo")):
      e=dict(env);e[k]=v
      with self.assertRaises(PermissionError):guard(base,e,"hot")
  def test_denied_bad_sites(self):
    event={"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER}}
    e={"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":"refs/heads/main","GITHUB_EVENT_NAME":"push"}
    for x in ("","unknown","C0"):
      with self.assertRaises(PermissionError):guard(event,e,x)
  def test_schema_rejects_accepted_claim(self):
    with self.assertRaises(ValueError):transfer.upload_verified("a","b","missing",schema="JTE069_ACCEPTED_G6")
if __name__=="__main__":unittest.main()
