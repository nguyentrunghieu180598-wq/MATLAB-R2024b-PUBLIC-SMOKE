#!/usr/bin/env python3
"""JTE-038: decrypt privately authorized JTE_ENVELOPE_V1 only.

Run in a TRUSTED PRIVATE runtime with filesystem access to a local RSA key.
Never put key, plaintext data, or decrypt logs into public GitHub/CI.
No secret material is printed by this program.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class DecryptError(ValueError):
    pass


def need(condition, msg):
    if not condition:
        raise DecryptError(msg)


def hexdigest_path(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def exact_b64(s):
    need(isinstance(s, str), 'Malformed envelope encoding')
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise DecryptError('Malformed envelope encoding') from e


def load_artifact(artifact_path):
    """Reads only public ciphertext metadata; ZIP entries never extracted here."""
    artifact_path = Path(artifact_path)
    need(artifact_path.is_file(), 'Encrypted artifact archive missing')
    with zipfile.ZipFile(artifact_path, 'r') as z:
        names = z.namelist()
        need(len(names) == 2 and set(names) == {'envelope.json', 'encrypted-results.bin'},
             'Expected precisely two cipher artifact files')
        need(len(names) == len(set(names)), 'Duplicate outer artifact entries')
        need(z.getinfo('envelope.json').file_size <= 16_384,
             'Unexpectedly large envelope')
        envelope = json.loads(z.read('envelope.json'))
        # Encrypted binary is ciphertext, not raw study data.
        payload = z.read('encrypted-results.bin')
    return envelope, payload


def validate_envelope(e, payload, public_key_pem):
    need(isinstance(e, dict) and e.get('version') == 'JTE_ENVELOPE_V1', 'Wrong envelope version')
    need(e.get('cipher') == 'AES-256-GCM' and e.get('keyWrap') == 'RSA-3072-OAEP-SHA256',
         'Unsupported cryptographic construction')
    need(e.get('encryptedContent') == 'zip-archive', 'Unexpected encrypted content type')
    need(isinstance(e.get('ciphertextBytes'), int) and len(payload) == e['ciphertextBytes'],
         'Ciphertext length mismatch')
    need(hashlib.sha256(payload).hexdigest() == e.get('sha256Ciphertext'),
         'Ciphertext checksum mismatch')
    need(hashlib.sha256(public_key_pem).hexdigest() == e.get('publicKeySHA256'),
         'Public-key identity mismatch')
    need(isinstance(e.get('filesCount'), int) and 0 < e['filesCount'] <= 5000,
         'Invalid plaintext file count')
    nonce, tag, wrapped = (exact_b64(e[k]) for k in ('nonceB64', 'gcmTagB64', 'wrappedAESKeyB64'))
    need(len(nonce) == 12 and len(tag) == 16 and len(wrapped) == 384,
         'Malformed nonce, authentication tag or RSA wrapped key')
    return nonce, tag, wrapped


def safe_member_info(info):
    path = PurePosixPath(info.filename)
    need(not path.is_absolute() and not info.filename.startswith('\\') and
         '\\' not in info.filename and '..' not in path.parts and len(path.parts)>0,
         'Unsafe ZIP member path')
    need(not info.is_dir(), 'Directory-only members not in encrypted results manifest')
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    need(not stat.S_ISLNK(unix_mode), 'Symlinks disallowed in research archive')
    need(info.file_size <= 8 * 1024 ** 3, 'Implausibly large uncompressed member')
    return path


def decrypt_archive(artifact, local_private_key, public_key, output_dir, max_uncompressed_gb=20):
    """Fail closed on AES GCM, paths, counts, checksums. Never overwrite output."""
    output_dir = Path(output_dir).resolve()
    need(not output_dir.exists(), 'Refusing to overwrite an existing output directory')
    need(output_dir.parent.is_dir(), 'Destination parent folder missing')
    e, payload = load_artifact(artifact)
    pub_bytes = Path(public_key).read_bytes()
    nonce, tag, wrapped = validate_envelope(e, payload, pub_bytes)
    pem = Path(local_private_key).read_bytes()
    priv = serialization.load_pem_private_key(pem, password=None)
    need(isinstance(priv, rsa.RSAPrivateKey) and priv.key_size == 3072,
         'Expected RSA-3072 private key')
    need(priv.public_key().public_numbers() == serialization.load_pem_public_key(pub_bytes).public_numbers(),
         'Private key is not the intended public-key pair')
    key = priv.decrypt(wrapped, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                               algorithm=hashes.SHA256(), label=None))
    need(len(key) == 32, 'Unexpected AES key length')
    # Authentication MUST succeed before any plaintext ZIP is opened.
    decipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
    try:
        decoded = decipher.update(payload) + decipher.finalize()
    except InvalidTag as ex:
        raise DecryptError('AES-GCM AUTHENTICATION FAILED; no plaintext released') from ex
    need(len(decoded) == e.get('originalZipBytes'), 'Authenticated ZIP length mismatch')
    limit = int(max_uncompressed_gb * 1024**3)
    tmp = Path(tempfile.mkdtemp(prefix='jte038_private_staging_', dir=str(output_dir.parent)))
    try:
        with zipfile.ZipFile(io.BytesIO(decoded)) as z:
            members = z.infolist()
            need(len(members) == e['filesCount'], 'Authenticated archive file count mismatch')
            paths = [safe_member_info(info) for info in members]
            need(all(p.parts[0].casefold() != 'jte038_private_receipt.json'
                     for p in paths), 'Reserved receipt path in authenticated payload')
            need(len(paths) == len(set(paths)), 'Duplicate relative paths')
            need(sum(info.file_size for info in members) <= limit,
                 'Total uncompressed study data exceeds safety limit')
            digests = {}
            for info, rel in zip(members, paths):
                dest = tmp.joinpath(*rel.parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                need(not dest.exists(), 'Duplicate output destination')
                h = hashlib.sha256()
                with z.open(info, 'r') as src, open(dest, 'xb') as dst:
                    while chunk := src.read(1024 * 1024):
                        dst.write(chunk)
                        h.update(chunk)
                digests[str(rel)] = {'sha256': h.hexdigest(), 'bytes': info.file_size}
        receipt = {
            'status': 'CIPHER_AUTHENTICATED_AND_EXTRACTED_PRIVATE',
            'label': e.get('label'),
            'rsaOaepAesGcmAuthenticated': True,
            'publicKeySHA256': e['publicKeySHA256'],
            'ciphertextSHA256': e['sha256Ciphertext'],
            'artifactSHA256': hexdigest_path(artifact),
            'filesCount': len(digests),
            'members': digests,
            'scientificG5Accepted': False,
            'caution': 'Cryptographic authenticity does NOT establish scientific validity.'
        }
        with (tmp / 'JTE038_private_receipt.json').open('x', encoding='utf-8') as receipt_file:
            json.dump(receipt, receipt_file, indent=2)
        os.replace(tmp, output_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return output_dir / 'JTE038_private_receipt.json'


def main():
    ap = argparse.ArgumentParser(description='Private key local file ONLY. No public CI or logs.')
    ap.add_argument('--artifact', required=True, help='ZIP with encrypted-results.bin and envelope.json')
    ap.add_argument('--private-key-file', required=True)
    ap.add_argument('--public-key-file', required=True)
    ap.add_argument('--output', required=True, help='NEW private destination folder, no overwrite')
    args = ap.parse_args()
    try:
        decrypt_archive(args.artifact, args.private_key_file,
                        args.public_key_file, args.output)
        print('JTE038 PRIVATE CRYPTO AUTHENTICATED. STUDY GATES STILL REQUIRE SCIENTIFIC REVIEW.')
    except (DecryptError, OSError, ValueError, zipfile.BadZipFile) as err:
        print('JTE038 BLOCKED: private ciphertext authentication/extraction failed.')
        raise SystemExit(2) from None


if __name__ == '__main__':
    main()
