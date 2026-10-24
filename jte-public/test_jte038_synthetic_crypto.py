"""Synthetic-only RSA/OAEP/AES-GCM fixture; never uses user's RSA private key."""
import base64
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jte038_private_decrypt import decrypt_archive, DecryptError


def b64(x):
    return base64.b64encode(x).decode('ascii')


def test():
    with tempfile.TemporaryDirectory() as w:
        root=Path(w)
        private=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        priv=root/'synthetic_private.pem'
        pub=root/'synthetic_public.pem'
        priv.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                             serialization.NoEncryption()))
        public_pem=private.public_key().public_bytes(serialization.Encoding.PEM,
                                                     serialization.PublicFormat.SubjectPublicKeyInfo)
        pub.write_bytes(public_pem)
        outbuf=io.BytesIO()
        with zipfile.ZipFile(outbuf,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('synthetic/demo.txt','THIS IS SYNTHETIC DATA, NOT A STUDY RESULT')
        plaintext=outbuf.getvalue()
        import os
        key=os.urandom(32);nonce=os.urandom(12)
        enc=Cipher(algorithms.AES(key),modes.GCM(nonce)).encryptor()
        ciphertext=enc.update(plaintext)+enc.finalize()
        wrapped=private.public_key().encrypt(key,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                                        algorithm=hashes.SHA256(),label=None))
        envelope=dict(version='JTE_ENVELOPE_V1',cipher='AES-256-GCM',keyWrap='RSA-3072-OAEP-SHA256',
          encryptedContent='zip-archive',ciphertextBytes=len(ciphertext),
          sha256Ciphertext=hashlib.sha256(ciphertext).hexdigest(),
          publicKeySHA256=hashlib.sha256(public_pem).hexdigest(),
          filesCount=1,nonceB64=b64(nonce),gcmTagB64=b64(enc.tag),
          wrappedAESKeyB64=b64(wrapped),originalZipBytes=len(plaintext),label='SYNTHETIC_TEST_ONLY')
        def save_artifact(path, e, cipher):
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('envelope.json',json.dumps(e));z.writestr('encrypted-results.bin',cipher)
        artifact=root/'fake-artifact.zip';save_artifact(artifact,envelope,ciphertext)
        receipt=decrypt_archive(artifact,priv,pub,root/'trusted_out')
        r=json.loads(receipt.read_text())
        assert r['rsaOaepAesGcmAuthenticated'] and not r['scientificG5Accepted']
        assert (root/'trusted_out/synthetic/demo.txt').read_text()=='THIS IS SYNTHETIC DATA, NOT A STUDY RESULT'
        # Changed ciphertext with recomputed non-cryptographic hashes must still fail GCM.
        altered=bytearray(ciphertext);altered[0]^=1
        e2=dict(envelope,sha256Ciphertext=hashlib.sha256(altered).hexdigest())
        t=root/'tampered-artifact.zip';save_artifact(t,e2,altered)
        try:
            decrypt_archive(t,priv,pub,root/'should_not_exist')
            raise AssertionError('GCM must detect tampering')
        except DecryptError:
            assert not (root/'should_not_exist').exists()
        # Correct key pair required.
        wrong=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        wp=root/'wrong_private.pem'
        wp.write_bytes(wrong.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
        try:
            decrypt_archive(artifact,wp,pub,root/'wrong_out')
            raise AssertionError('Mismatched key must be rejected')
        except DecryptError:
            assert not (root/'wrong_out').exists()
        # Plaintext ZIP path traversal must be rejected after authenticated decryption.
        evilbuf=io.BytesIO()
        with zipfile.ZipFile(evilbuf,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('../escape.txt','bad')
        evil=evilbuf.getvalue()
        enc2=Cipher(algorithms.AES(key),modes.GCM(nonce)).encryptor()
        evilc=enc2.update(evil)+enc2.finalize()
        e3=dict(envelope,originalZipBytes=len(evil),sha256Ciphertext=hashlib.sha256(evilc).hexdigest(),
                ciphertextBytes=len(evilc),gcmTagB64=b64(enc2.tag))
        evilarchive=root/'evil.zip';save_artifact(evilarchive,e3,evilc)
        try:
            decrypt_archive(evilarchive,priv,pub,root/'evil_out')
            raise AssertionError('Unsafe ZIP path must be rejected')
        except DecryptError:
            assert not (root/'evil_out').exists()
        print('JTE038 SYNTHETIC PRIVATE CRYPTO TEST PASS; 4 CASES, NO ACTUAL RESEARCH DATA')

if __name__=='__main__':test()
