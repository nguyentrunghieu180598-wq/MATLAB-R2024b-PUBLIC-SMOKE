"""Synthetic fixtures ONLY. No project key, research artifact, MATLAB or network."""
import base64, hashlib, io, json, os, stat, tempfile, unittest, zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jte038_private_decrypt import decrypt_archive, DecryptError

class ReceiptRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        cls.wrong = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.priv = self.root / 'SYNTHETIC_PRIVATE.pem'
        self.pub = self.root / 'SYNTHETIC_PUBLIC.pem'
        self.priv.write_bytes(self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        self.pb = self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.pub.write_bytes(self.pb)
        self.out = self.root / 'out'
    def artifact(self, names, tamper=False, tag_bad=False, symlink=False):
        b = io.BytesIO()
        with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
            for name in names:
                if symlink:
                    info=zipfile.ZipInfo(name)
                    info.create_system=3
                    info.external_attr=(stat.S_IFLNK | 0o777) << 16
                    z.writestr(info,'target')
                else:
                    z.writestr(name, b'SYNTHETIC ONLY ' * 300)
        raw=b.getvalue()
        key=os.urandom(32); nonce=os.urandom(12)
        enc=Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        cipher=enc.update(raw)+enc.finalize()
        tag=enc.tag
        wrapped=self.key.public_key().encrypt(key,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
        if tamper: cipher=bytes([cipher[0]^1])+cipher[1:]
        if tag_bad: tag=bytes([tag[0]^1])+tag[1:]
        b64=lambda x:base64.b64encode(x).decode('ascii')
        e=dict(version='JTE_ENVELOPE_V1',cipher='AES-256-GCM',keyWrap='RSA-3072-OAEP-SHA256',encryptedContent='zip-archive',
               ciphertextBytes=len(cipher),sha256Ciphertext=hashlib.sha256(cipher).hexdigest(),
               publicKeySHA256=hashlib.sha256(self.pb).hexdigest(),filesCount=len(names),originalZipBytes=len(raw),
               nonceB64=b64(nonce),gcmTagB64=b64(tag),wrappedAESKeyB64=b64(wrapped),label='SYNTHETIC_ONLY')
        p=self.root/'cipher.zip'
        with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('envelope.json',json.dumps(e)); z.writestr('encrypted-results.bin',cipher)
        return p
    def reject(self,p,**kwargs):
        with self.assertRaises(DecryptError):
            decrypt_archive(p,self.priv,self.pub,self.out,**kwargs)
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.root.glob('jte038_private_staging_*')),[])
    def test_valid_nested_file_and_receipt_hashes(self):
        p=self.artifact(['nested/demo.txt','nested/JTE038_private_receipt.json'])
        receipt=decrypt_archive(p,self.priv,self.pub,self.out)
        r=json.loads(receipt.read_text())
        self.assertTrue(r['rsaOaepAesGcmAuthenticated'])
        self.assertFalse(r['scientificG5Accepted'])
        self.assertEqual(r['filesCount'],2)
        for name,entry in r['members'].items():
            content=(self.out/name).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(),entry['sha256'])
            self.assertEqual(len(content),entry['bytes'])
    def test_reserved_root_receipt(self):
        self.reject(self.artifact(['JTE038_private_receipt.json']))
    def test_reserved_case_variant(self):
        self.reject(self.artifact(['jTe038_PRIVATE_RECEIPT.JSON']))
    def test_reserved_directory(self):
        self.reject(self.artifact(['JTE038_private_receipt.json/nested.txt']))
    def test_traversal(self):
        self.reject(self.artifact(['../escape.txt']))
        self.assertFalse((self.root/'escape.txt').exists())
    def test_symlink(self):
        self.reject(self.artifact(['link'],symlink=True))
    def test_duplicate_path(self):
        self.reject(self.artifact(['same.txt','same.txt']))
    def test_bad_tag(self):
        self.reject(self.artifact(['ok.txt'],tag_bad=True))
    def test_tamper_with_updated_checksum(self):
        self.reject(self.artifact(['ok.txt'],tamper=True))
    def test_wrong_key(self):
        p=self.artifact(['ok.txt'])
        self.priv.write_bytes(self.wrong.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        self.reject(p)
    def test_small_uncompressed_limit_rejects_compression_expansion(self):
        self.reject(self.artifact(['compressed.txt']),max_uncompressed_gb=1e-6)
    def test_existing_output_not_overwritten(self):
        p=self.artifact(['ok.txt'])
        self.out.mkdir(); sentinel=self.out/'keep.txt'; sentinel.write_text('KEEP')
        with self.assertRaises(DecryptError):
            decrypt_archive(p,self.priv,self.pub,self.out)
        self.assertEqual(sentinel.read_text(),'KEEP')
        self.assertEqual(list(self.root.glob('jte038_private_staging_*')),[])

if __name__=='__main__':
    unittest.main(verbosity=2)
