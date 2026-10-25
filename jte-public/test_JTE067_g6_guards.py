"""G6 permission, no secrets and no model data."""
import unittest
from unittest.mock import patch
from JTE062_google_drive_synthetic import EXPECTED_REPO
from JTE067_upload_G6 import TRIGGER,guard
import JTE063_streaming_drive as transport

class G6TransportGuards(unittest.TestCase):
 def ev(self):
  return ({"repository":{"full_name":EXPECTED_REPO,"private":False},
           "head_commit":{"message":TRIGGER}},
          {"GITHUB_REPOSITORY":EXPECTED_REPO,"GITHUB_EVENT_NAME":"push",
           "GITHUB_REF":"refs/heads/main"})
 def test_allow_three_only(self):
  e,v=self.ev()
  for kind in ('cold','middle','hot'):self.assertIsNone(guard(e,v,kind))
 def test_deny_wrong_site(self):
  e,v=self.ev()
  for kind in ('all','pack','negative',''):
   with self.assertRaises(PermissionError):guard(e,v,kind)
 def test_deny_untrusted_repo(self):
  e,v=self.ev();e['repository']['full_name']='fake/repo'
  with self.assertRaises(PermissionError):guard(e,v,'hot')
 def test_deny_pr(self):
  e,v=self.ev();v['GITHUB_EVENT_NAME']='pull_request'
  with self.assertRaises(PermissionError):guard(e,v,'hot')
 def test_deny_other_branch(self):
  e,v=self.ev();v['GITHUB_REF']='refs/heads/work'
  with self.assertRaises(PermissionError):guard(e,v,'cold')
 def test_deny_other_commit(self):
  e,v=self.ev();e['head_commit']['message']='other'
  with self.assertRaises(PermissionError):guard(e,v,'middle')
 def test_new_schema_only_raw(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'synthetic.bin';p.write_bytes(b'x'*2048)
   with patch.object(transport,'_session',side_effect=RuntimeError('NO_NETWORK')) as f:
    with self.assertRaisesRegex(RuntimeError,'NO_NETWORK'):
     transport.upload_verified('x','x',p,schema='JTE067_G6_MINUS2K_RAW_UNREVIEWED')
    self.assertEqual(f.call_args.args[-1],'JTE067_G6_MINUS2K_RAW_UNREVIEWED')
 def test_reject_accepted_claim(self):
  with self.assertRaisesRegex(ValueError,'UNKNOWN_SCHEMA'):
   transport.upload_verified('x','x','not-a-file',schema='G6_ACCEPTED')
if __name__=='__main__':unittest.main()
