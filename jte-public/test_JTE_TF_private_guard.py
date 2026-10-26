"""New guard tests only, no credentials/network/MATLAB."""
import unittest
from JTE_TF_private_gate import guard,EXPECTED_REPO,BRANCH,TRIGGER
class Guard(unittest.TestCase):
 def setUp(self):
  self.event={"repository":{"full_name":EXPECTED_REPO,"private":False},"head_commit":{"message":TRIGGER,"id":"a"*40}}
  self.env={"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_REF":BRANCH,"GITHUB_EVENT_NAME":"push","GITHUB_SHA":"a"*40,"GITHUB_RUN_ATTEMPT":"1"}
 def test_authorized_context(self):guard(self.event,self.env)
 def test_untrusted_context_denied(self):
  for key,value in (("GITHUB_REF","refs/heads/main"),("GITHUB_REPOSITORY","other/fork"),("GITHUB_EVENT_NAME","pull_request"),("GITHUB_RUN_ATTEMPT","2"),("GITHUB_SHA","b"*40)):
   env=dict(self.env);env[key]=value
   with self.subTest(key=key),self.assertRaises(PermissionError):guard(self.event,env)
 def test_message_denied(self):
  self.event["head_commit"]["message"]="not authorized"
  with self.assertRaises(PermissionError):guard(self.event,self.env)
if __name__=="__main__":unittest.main()
