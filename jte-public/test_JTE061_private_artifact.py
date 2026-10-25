"""Synthetic-only transport security checks. Not battery simulation."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from JTE061_private_artifact import (
    assert_private_context, make_fixture, verify_extracted, verify_zip, synthetic_bytes, SYNTH_SIZE
)


def event(private=True, full_name="tester/JTE-PRIVATE"):
    return {"repository":{"full_name":full_name,"private":private,"visibility":"private" if private else "public"}}


class PrivateTransportTests(unittest.TestCase):
    def test_private_manual_allowed(self):
        self.assertTrue(assert_private_context(event(),"tester/JTE-PRIVATE","workflow_dispatch","private"))

    def test_public_must_be_denied(self):
        with self.assertRaisesRegex(PermissionError,"DENIED_PUBLIC"):
            assert_private_context(event(False),"tester/JTE-PRIVATE","workflow_dispatch","public")

    def test_unknown_visibility_denied(self):
        with self.assertRaises(PermissionError):
            assert_private_context({"repository": {}},"tester/JTE-PRIVATE","workflow_dispatch",None)

    def test_mismatched_repository_denied(self):
        with self.assertRaisesRegex(PermissionError, "MISMATCH"):
            assert_private_context(event(),"wrong/JTE-PRIVATE","workflow_dispatch","private")

    def test_other_event_denied(self):
        with self.assertRaisesRegex(PermissionError,"NOT_MANUAL"):
            assert_private_context(event(),"tester/JTE-PRIVATE","pull_request","private")

    def test_falsely_declared_public_denied(self):
        with self.assertRaises(PermissionError):
            assert_private_context(event(),"tester/JTE-PRIVATE","workflow_dispatch","public")

    def test_exact_synthetic_size(self):
        self.assertEqual(len(synthetic_bytes()), SYNTH_SIZE)

    def test_byte_sha_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            expected=make_fixture(root)
            self.assertEqual(verify_extracted(root)["sha256"],expected["sha256"])
            (root/"synthetic_fixture.bin").write_bytes(b"damaged")
            with self.assertRaisesRegex(ValueError,"SHA256 mismatch|size or"):
                verify_extracted(root)

    def test_private_artifact_zip_roundtrip_and_extra_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            expected=make_fixture(root)
            target=root/"artifact.zip"
            with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.write(root/"manifest.json","manifest.json")
                z.write(root/"synthetic_fixture.bin","synthetic_fixture.bin")
            self.assertEqual(verify_zip(target)["sha256"],expected["sha256"])
            with zipfile.ZipFile(target,"a") as z:
                z.writestr("extra-private-key.pem",b"must not accept")
            with self.assertRaisesRegex(ValueError,"Unexpected ZIP payload"):
                verify_zip(target)

    def test_oversized_zip_entry_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            zipname=root/"artifact.zip"
            with zipfile.ZipFile(zipname,"w") as z:
                z.writestr("manifest.json","{}")
                z.writestr("synthetic_fixture.bin",b"0"*(SYNTH_SIZE*2+1))
            with self.assertRaisesRegex(ValueError,"oversized"):
                verify_zip(zipname)


if __name__=="__main__":
    unittest.main()
