"""No-network tests for JTE063 chunked Drive transport. Synthetic-only."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import JTE063_streaming_drive as u


class LargeTransportTests(unittest.TestCase):
    def test_session_host_guard(self):
        self.assertTrue(u._valid_session("https://www.googleapis.com/upload/drive/v3/files?upload_id=abc"))
        self.assertFalse(u._valid_session("https://www.googleapis.com.attacker.invalid/upload/drive/v3/files"))
        self.assertFalse(u._valid_session("https://user@www.googleapis.com/upload/drive/v3/files"))
        self.assertFalse(u._valid_session("http://www.googleapis.com/upload/drive/v3/files"))

    def test_parse_google_resume_range(self):
        self.assertEqual(u.parse_range(None,100),0)
        self.assertEqual(u.parse_range("bytes=0-31",100),32)
        with self.assertRaises(ValueError):u.parse_range("bytes=1-31",100)
        with self.assertRaises(ValueError):u.parse_range("bytes=0-100",100)

    def test_local_file_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"synthetic.bin";p.write_bytes(b"abc"*1024)
            size,sha,md5=u.sha_file(p)
            self.assertEqual(size,3072)
            self.assertEqual(sha,hashlib.sha256(b"abc"*1024).hexdigest())
            self.assertEqual(md5,hashlib.md5(b"abc"*1024,usedforsecurity=False).hexdigest())

    def test_local_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"safe.bin";b=Path(td)/"link.bin"
            a.write_bytes(b"fixture");b.symlink_to(a)
            with self.assertRaises(ValueError):u.sha_file(b)

    def test_chunked_resumable_two_chunks(self):
        payload=b"synthetic"*11
        with tempfile.TemporaryDirectory() as td,patch.object(u,"CHUNK",50):
            path=Path(td)/"synthetic.bin";path.write_bytes(payload)
            calls=[]
            def fake(url,**kw):
                calls.append(kw.get("headers",{}).get("Content-Range"))
                if len(calls)==1:
                    return 308,{"Range":"bytes=0-49"},b""
                return 200,{},b'{"id":"fakeid","size":99}'
            with patch.object(u,"_http",side_effect=fake):
                self.assertEqual(u.upload_chunks(path,"https://www.googleapis.com/upload/drive/v3/files?upload_id=fake",len(payload))["id"],"fakeid")
            self.assertEqual(calls,["bytes 0-49/99","bytes 50-98/99"])

    def test_upload_untrusted_session_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"UNTRUSTED"):
            u.upload_chunks("/unused","https://evil.invalid/upload/drive/v3/files",10)

    def test_upload_308_with_no_progress_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"synthetic.bin";path.write_bytes(b"abc")
            with patch.object(u,"_http",return_value=(308,{},b"")):
                with self.assertRaisesRegex(RuntimeError,"PROGRESS_INVALID"):
                    u.upload_chunks(path,"https://www.googleapis.com/upload/drive/v3/files?upload_id=fake",3)

    def test_upload_transient_probe_advances(self):
        with tempfile.TemporaryDirectory() as td,patch.object(u,"CHUNK",2):
            path=Path(td)/"synthetic.bin";path.write_bytes(b"abcd")
            seq=[
                (503,{},b""),
                (308,{"Range":"bytes=0-1"},b""),
                (200,{},b'{"id":"file123","size":4}'),
            ]
            with patch.object(u,"_http",side_effect=seq) as f,patch.object(u.time,"sleep",return_value=None):
                self.assertEqual(u.upload_chunks(path,"https://www.googleapis.com/upload/drive/v3/files?upload_id=fake",4)["id"],"file123")
                self.assertEqual(f.call_args_list[1].kwargs.get("headers",{}).get("Content-Range"),"bytes */4")

    def test_early_commit_rejected(self):
        with tempfile.TemporaryDirectory() as td,patch.object(u,"CHUNK",3):
            path=Path(td)/"synthetic.bin";path.write_bytes(b"abcdef")
            with patch.object(u,"_http",return_value=(200,{},b'{"id":"f","size":6}')):
                with self.assertRaisesRegex(RuntimeError,"PREMATURE"):
                    u.upload_chunks(path,"https://www.googleapis.com/upload/drive/v3/files?upload_id=fake",6)

    def test_integrity_failure_does_not_mark_complete(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.bin";path.write_bytes(b"abc")
            fake={"id":"file","size":3,"md5Checksum":"0"*32}
            with patch.object(u,"_session",return_value="https://www.googleapis.com/upload/drive/v3/files?upload_id=fake"),patch.object(u,"upload_chunks",return_value=fake),patch.object(u,"_http") as patchcall:
                with self.assertRaisesRegex(RuntimeError,"MD5_MISMATCH"):
                    u.upload_verified("FAKE","folder",path)
                patchcall.assert_not_called()

    def test_good_integrity_commits_only_after_readback(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.bin";path.write_bytes(b"abc")
            md5=hashlib.md5(b"abc",usedforsecurity=False).hexdigest()
            sha=hashlib.sha256(b"abc").hexdigest()
            remote={"id":"file","size":3,"md5Checksum":md5}
            with patch.object(u,"_session",return_value="https://www.googleapis.com/upload/drive/v3/files?upload_id=fake"),patch.object(u,"upload_chunks",return_value=remote),patch.object(u,"readback_sha",return_value=sha),patch.object(u,"_http",return_value=(200,{},b"")) as commit:
                result=u.upload_verified("FAKE","folder",path)
                self.assertEqual(result["integrity"],"FULL_REMOTE_READBACK_VERIFIED")
                commit.assert_called_once()

if __name__=="__main__":unittest.main()
