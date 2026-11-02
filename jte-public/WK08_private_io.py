"""WK08 owner-reviewed, one-shot transport. Never executes MATLAB itself."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.parse

import m2340_io
import WK04_private_gate as prior
from JTE062_google_drive_synthetic import API, req
from JTE063_streaming_drive import upload_verified

ROOT = Path('actuator-review-private')
MESSAGE = 'WK08_PACK_340S_ONE_SHOT_20261102'
REF = 'refs/heads/codex/wk08-pack-design'
INTENT = 'WK08_PACK_340S_ATTEMPT_INTENT_20261102.json'
SCHEMA = 'WK08_R1_PACK_340S_NOT_G5_ACCEPTED'
ROLES = ('uCore', 'uSampled', 'actuatorY', 'Ttrue312',
         'TmaxTrue', 'TmaxMeasured', 'pumpPower')


def context():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    assert os.environ.get('GITHUB_REPOSITORY') == prior.REPO
    assert os.environ.get('GITHUB_REF') == REF
    assert os.environ.get('GITHUB_EVENT_NAME') == 'push'
    assert os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
    assert os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    assert (event.get('head_commit') or {}).get('id') == os.environ['GITHUB_SHA']
    assert (event.get('head_commit') or {}).get('message') == MESSAGE
    return os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_SHA']


def hashes():
    paths = list(Path('jte-public').glob('*.m')) + list(Path('jte-public').glob('*.py'))
    paths += [Path('actuator-amendment/WK08_sparse_sets.csv')]
    return {str(p): prior.sha256(p) for p in sorted(paths)}


def prepare(run, commit):
    assert not ROOT.exists()
    token, folder = prior.drive()
    prior.require_verified_neutral_preflight(token, folder)
    resource = m2340_io.host(token)
    assert resource['effectiveAvailable_bytes'] > 8 * 1024**3
    assert resource['diskFree_bytes'] > 10 * 1024**3
    assert resource['Drive']['availableBytes'] > 3 * 1024**3
    query = urllib.parse.urlencode({'q': "'" + folder + "' in parents and trashed = false and "
        "(name = 'JTE063_VERIFIED_" + INTENT + "' or name = '" + INTENT + "')",
        'fields': 'nextPageToken,files(id)', 'pageSize': '10'})
    _, _, raw = req(API + '?' + query, token=token)
    previous = json.loads(raw)
    assert not previous.get('files') and not previous.get('nextPageToken')
    # Reserve before downloading or launching MATLAB. Any failure consumes this
    # allowance; resuming it requires an independently reviewed NEW intent.
    with tempfile.TemporaryDirectory() as tmp:
        intent = Path(tmp) / INTENT
        intent.write_text(json.dumps({'run': run, 'commit': commit, 'schema': SCHEMA,
                                      'MATLAB_STARTED': False, 'noAutomaticRetry': True}))
        upload_verified(token, folder, intent, schema=SCHEMA)
    # Reuse M2's exact archived B0L source, proof/receipt and workspace linkage.
    m2340_io.fetch(token, folder)
    (ROOT / 'WK08_GATE.json').write_text(json.dumps({
        'run': run, 'commit': commit, 'inputSHA256': hashes(), 'resource': resource}))
    print('WK08_PRIVATE_PREPARE_PASS')


def publish(run, commit):
    token, folder = prior.drive()
    gate_path = ROOT / 'WK08_GATE.json'
    gate = json.loads(gate_path.read_text()) if gate_path.is_file() else {}
    flags_path = ROOT / 'WK08_FLAGS.json'
    flags = json.loads(flags_path.read_text()) if flags_path.is_file() else {}
    paths = sorted(p for p in ROOT.rglob('*') if p.is_file())
    assert sum(p.stat().st_size for p in paths) <= 2 * 1024**3
    receipt = {'schema': SCHEMA, 'run': run, 'commit': commit, 'files': [],
               'G5Accepted': False, 'status': flags.get('status', 'UNQUALIFIED_NO_FLAGS'),
               'sourceUnchanged': gate.get('inputSHA256') == hashes()}
    # All evidence, including partial logs/derivative/proof, is private only.
    for p in paths:
        if p.stat().st_size:
            receipt['files'].append({'path': str(p.relative_to(ROOT)),
                'sha256': prior.sha256(p),
                'remote': upload_verified(token, folder, p, schema=SCHEMA)})
    names = {p.name for p in paths if p.stat().st_size}
    receipt['requiredComplete'] = {f'WK08_R1_{r}.mat' for r in ROLES} <= names
    receipt['sameAttempt'] = gate.get('run') == run and gate.get('commit') == commit
    receipt['transportVerified'] = True
    p = ROOT / 'WK08_PRIVATE_RECEIPT.json'
    p.write_text(json.dumps(receipt, indent=2))
    upload_verified(token, folder, p, schema=SCHEMA)
    assert receipt['sourceUnchanged'] and receipt['sameAttempt']
    assert receipt['requiredComplete'] and flags.get('run') == run and flags.get('commit') == commit
    assert not (ROOT / 'WK08_WATCH_STOP.json').exists()
    assert flags.get('status') == 'R1_GATES_PASS_PENDING_PRIVATE_READBACK_AND_CLAUDE_REVIEW'
    print('WK08_PRIVATE_READBACK_VERIFIED G5_ACCEPTED=0')


if __name__ == '__main__':
    try:
        run, commit = context()
        if sys.argv[1:] == ['prepare']:
            prepare(run, commit)
        elif sys.argv[1:] == ['publish']:
            publish(run, commit)
        else:
            raise ValueError('MODE')
    except Exception as exc:
        print('WK08_PRIVATE_IO_UNQUALIFIED code=' + type(exc).__name__)
        sys.exit(1)
