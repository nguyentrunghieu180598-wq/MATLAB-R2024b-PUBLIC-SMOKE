#!/usr/bin/env python3
"""Encrypt MATLAB research output for a public CI runner without exposing content.
Uses 3072-bit RSA-OAEP/SHA256 to wrap a random AES-256-GCM file key.
The recipient PRIVATE RSA key MUST NOT enter GitHub/public logs/artifacts.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, os, secrets, tempfile, zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def encrypt_file(src: Path, dest: Path, public_key):
    file_key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    cryptor = Cipher(algorithms.AES(file_key), modes.GCM(nonce)).encryptor()
    sha = hashlib.sha256()
    size = 0
    with open(src, 'rb') as fi, open(dest, 'wb') as fo:
        while chunk := fi.read(1024*1024):
            encrypted = cryptor.update(chunk)
            fo.write(encrypted)
            sha.update(encrypted)
            size += len(encrypted)
        final = cryptor.finalize()
        fo.write(final)
        sha.update(final)
        size += len(final)
    wrapped = public_key.encrypt(file_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return {'cipher':'AES-256-GCM','keyWrap':'RSA-3072-OAEP-SHA256',
        'wrappedAESKeyB64':b64(wrapped),'nonceB64':b64(nonce),'gcmTagB64':b64(cryptor.tag),
        'sha256Ciphertext':sha.hexdigest(), 'ciphertextBytes':size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--dest',required=True)
    parser.add_argument('--key',required=True)
    parser.add_argument('--label',required=True)
    a=parser.parse_args()
    root, dest=Path(a.source),Path(a.dest)
    assert root.is_dir() and any(root.iterdir()), 'No files to encrypt'
    dest.mkdir(parents=True,exist_ok=True)
    key_bytes=Path(a.key).read_bytes()
    public_key=serialization.load_pem_public_key(key_bytes)
    fingerprint=hashlib.sha256(key_bytes).hexdigest()
    # Temporary plaintext ZIP stays within the ephemeral runner, never uploaded.
    with tempfile.TemporaryDirectory(prefix='jte_private_zip_') as tmp:
        zipfile_path=Path(tmp)/'private_numeric_results.zip'
        with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            included=[]
            for p in sorted(root.rglob('*')):
                if p.is_file():
                    rp=p.relative_to(root)
                    assert '..' not in rp.parts
                    z.write(p,arcname=str(rp))
                    included.append(str(rp))
        enc_dest=dest/'encrypted-results.bin'
        envelope=encrypt_file(zipfile_path,enc_dest,public_key)
        envelope.update({'version':'JTE_ENVELOPE_V1','label':a.label,
                         'publicKeySHA256':fingerprint,'filesCount':len(included),
                         'encryptedContent':'zip-archive','originalZipBytes':zipfile_path.stat().st_size})
        (dest/'envelope.json').write_text(json.dumps(envelope,indent=2),encoding='utf-8')
    # Only innocuous metadata printed: NO filenames, numerical results, secrets.
    print(f'JTE_ENCRYPTED_ARTIFACT_READY label={a.label} publicKeySHA256={fingerprint} filesCount={len(included)}')
    print('No plaintext research data has been uploaded.')


if __name__=='__main__':
    main()
