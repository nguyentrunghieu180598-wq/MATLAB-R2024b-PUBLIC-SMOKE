"""WK09-only authorization and private I/O. check() never writes to Drive.

The historical single-run authorization functions are deliberately not called.
Native success never creates Claude's CONTROLS acceptance record.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from WK09_run_definitions import ROOT as CODE, definitions as legacy_definitions, resolve, sha, need, H_SEL, H_R2, H_PRED, H_SCENARIO
from WK08_private_gate import readonly_app_folder, private_acl, NATIVE
from WK04_private_gate import require_verified_neutral_preflight
from JTE062_google_drive_synthetic import access_token
from JTE101_io import query, one, download, quota
from JTE063_streaming_drive import upload_verified

REPO = 'nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE'
SCHEMA = 'WK09_D13_RAW_UNREVIEWED_NOT_G5'
GiB = 1024**3
ROOT = Path('wk09-private')
ASSETS = (
 ('BTMS_M2_40701917441_PRIVATE_RECEIPT.json', 'old_receipt.json'),
 ('BTMS_M2_40701917441_B0L_Ref_LOGGER.slx', 'M2340Source.slx'),
 ('BTMS_M2_40701917441_B0L_Ref_PROOF.json', 'old_proof.json'),
 ('BTMS_M2_40701917441_INPUT_MANIFEST.json', 'old_manifest.json'),
 ('JTE101_40449421507_PREPARE_WORKSPACE.mat', 'source_workspace.mat'))


def definitions():
    if os.environ.get('WK09_GROUP') == 'PROBE14':
        from WK10_D14_probe import definitions as probe_definitions
        return probe_definitions()
    return legacy_definitions()


def registry_file():
    return 'WK10_D14_probe.json' if os.environ.get('WK09_GROUP') == 'PROBE14' else 'WK09_runs.json'


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        os.chmod(path, 0o600)
        json.dump(value, f, indent=2)


def context(check_only=False):
    d = definitions(); group = os.environ.get('WK09_GROUP')
    need(group in d['groups'], 'WK09_GROUP_DENIED'); g = d['groups'][group]
    prefix = 'preflight_' if check_only else ''
    workflow, marker, message, approval = (g[prefix+k] for k in ('workflow','marker','message','approval'))
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    head = event.get('head_commit') or {}; repo = event.get('repository') or {}
    need(os.environ.get('GITHUB_REPOSITORY') == repo.get('full_name') == REPO
         and repo.get('private') is False and os.environ.get('GITHUB_REF') == 'refs/heads/'+d['branch']
         and os.environ.get('GITHUB_EVENT_NAME') == 'push' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
         and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
         and os.environ.get('WK09_PROTECTED_ENV_NAME') == 'JTE_DRIVE_WRITE'
         and os.environ.get('WK09_OWNER_APPROVAL') == approval
         and head.get('message') == message and head.get('id') == os.environ.get('GITHUB_SHA'),
         'WK09_CONTEXT_DENIED')
    source = os.environ.get('WK09_REVIEWED_SOURCE_SHA','')
    need(re.fullmatch('[a-f0-9]{40}',source) and source != '0'*40, 'WK09_REVIEWED_SOURCE_UNSET')
    need(git('rev-parse','HEAD') == os.environ['GITHUB_SHA'] and git('rev-parse','HEAD~2') == source
         and git('diff','--name-only','HEAD~2','HEAD~1') == workflow
         and git('diff','--name-only','HEAD~1','HEAD') == marker
         and Path(marker).read_text(encoding='utf-8').strip() == message
         and git('ls-tree','HEAD~2','--',marker) == '', 'WK09_CHAIN_DENIED')
    run = os.environ.get('GITHUB_RUN_ID',''); need(run.isdecimal(), 'WK09_RUN_ID')
    result = dict(run=run, commit=os.environ['GITHUB_SHA'], source=source, group=group,
                identity=g['identity'], runs=g['runs'], registrySHA256=sha(CODE/registry_file()),
                selectorSHA256=H_SEL, scenarioSHA256=H_SCENARIO, predictionsSHA256=H_PRED,
                baselineReceiptSHA256=H_R2, automaticRetry=False, G5Accepted=False)
    if group == 'PROBE14':
        result.pop('scenarioSHA256')
        result['scenarioSHA256ByCase'] = {r['id']:r['scenario_sha256'] for r in d['runs']}
    return result


def code_hashes():
    return {p:sha(p) for p in git('ls-files','jte-public').splitlines()
            if Path(p).suffix in {'.m','.py','.csv','.json'}}


def drive():
    token = access_token(*[os.environ[k] for k in
        ('JTE_GOOGLE_CLIENT_ID','JTE_GOOGLE_CLIENT_SECRET','JTE_GOOGLE_REFRESH_TOKEN')])
    folder = readonly_app_folder(token); private_acl(token,folder)
    rows = query(token,folder,"name = 'BTMS-DATS' and mimeType = 'application/vnd.google-apps.folder'")
    need(len(rows) == 1, 'WK09_RESULTS_FOLDER_REQUIRED'); results = rows[0]['id']
    private_acl(token,results)
    return token,folder,results


def metadata(token,folder,name):
    meta = one(token,folder,'JTE063_VERIFIED_'+name); private_acl(token,meta['id'])
    props = meta.get('appProperties') or {}
    need(props.get('state') == 'VERIFIED' and re.fullmatch('[a-f0-9]{64}',props.get('sha256',''))
         and 0 < int(meta.get('size',-1)) < GiB, 'WK09_ASSET_METADATA')
    return meta


def json_asset(token,folder,name,path,digest=None):
    meta = metadata(token,folder,name)
    need(int(meta['size']) <= 4*1024**2, 'WK09_JSON_SIZE')
    if digest is not None:
        need(meta['appProperties']['sha256'] == digest, 'WK09_RECEIPT_DIGEST')
    download(token,meta,path)
    if digest is not None:
        need(sha(path) == digest, 'WK09_RECEIPT_DIGEST')
    return json.loads(path.read_text(encoding='utf-8'))


def absent(token,folder,name):
    need(not query(token,folder,"name = 'JTE063_PENDING_"+name+
                   "' or name = 'JTE063_VERIFIED_"+name+"'"), 'WK09_SPENT_IDENTITY_NO_RETRY')


def child_intent(g,case):
    need(case in g['runs'], 'WK09_CASE_OUTSIDE_ALLOWLIST')
    if g['optional']: return g['intent']
    return g['identity']+'_'+case+'_ATTEMPT_INTENT.json'


def receipt_name(auth,case):
    g=definitions()['groups'][auth['group']]
    need(case in g['runs'],'WK09_CASE_OUTSIDE_ALLOWLIST')
    return g['identity']+'_'+auth['run']+('' if g['optional'] else '_'+case)+'_PRIVATE_RECEIPT.json'


def read_baseline(token,results,temp):
    b = definitions()['baseline']
    r = json_asset(token,results,b['receipt_name'],temp/'R2_receipt.json',H_R2)
    need(r.get('run') == b['github_run'] and r.get('schema') == 'WK10_D13_RAW_UNREVIEWED_NOT_G5'
         and r.get('status') == 'R1_GATES_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE'
         and r.get('G5Accepted') is False and r.get('rawDataPublic') is False, 'WK09_R2_RECEIPT')
    return r


def controls_acceptance(token,results,temp):
    """Hash-only Claude acceptance in reviewed S; native receipts stay private."""
    d = definitions(); criteria = d['controls_acceptance']
    digest = criteria['sha256']
    need(re.fullmatch('[a-f0-9]{64}',digest) and digest != '0'*64, 'WK09_CONTROLS_ACCEPTANCE_UNSET')
    try:
        raw = subprocess.check_output(['git','show','HEAD~2:'+criteria['file']], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise RuntimeError('WK09_CONTROLS_ACCEPTANCE_UNSET') from None
    need(hashlib.sha256(raw).hexdigest() == digest, 'WK09_CONTROLS_ACCEPTANCE_DIGEST')
    a = json.loads(raw)
    hub = a.get('hub_commit','')
    need(a.get('schema') == criteria['schema'] and a.get('reviewer') == 'Claude'
         and a.get('decision') == 'ACCEPTED' and re.fullmatch('[a-f0-9]{40}',hub) and hub != '0'*40
         and a.get('selector_sha256') == H_SEL and a.get('scenario_sha256') == H_SCENARIO
         and a.get('baseline_receipt_sha256') == H_R2 and a.get('predictions_sha256') == H_PRED,
         'WK09_CONTROLS_ATTESTATION')
    entries = a.get('runs',[])
    need([r.get('id') for r in entries] == criteria['required_runs'], 'WK09_CONTROLS_ALLOWLIST')
    for row in entries:
        case = row['id']
        need(row.get('accepted') is True and all(row.get(k) is True for k in criteria['criteria'][case]),
             'WK09_CONTROLS_CRITERIA')
        if case == 'R5':
            x = row.get('max_abs_Tmax_R5_minus_R2_K')
            need(type(x) in (int,float) and 0 <= x <= 1e-6, 'WK09_R5_EQUIVALENCE')
        receipt = json_asset(token,results,row['receipt_name'],temp/(case+'_receipt.json'),
                             row['receipt_sha256'])
        need(receipt.get('case') == case and receipt.get('group') == 'CONTROLS'
             and receipt.get('status') == 'NATIVE_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE'
             and receipt.get('selectorSHA256') == H_SEL and receipt.get('scenarioSHA256') == H_SCENARIO
             and receipt.get('baselineReceiptSHA256') == H_R2, 'WK09_CONTROL_RECEIPT')
    return dict(sha256=digest,hub_commit=hub)


def inputs(token,folder,temp,model=False):
    assets=[]; metas={}
    for name,local in ASSETS:
        meta=metadata(token,folder,name); metas[local]=meta
        if local.endswith('.json'):
            need(int(meta['size']) <= 4*1024**2,'WK09_JSON_SIZE')
        if model or not local.endswith('.slx'):
            assets.append(download(token,meta,temp/local))
    receipt=json.loads((temp/'old_receipt.json').read_text())
    need(receipt['run']=='40701917441' and receipt['commit']=='75afa01be55339d20ce5831830a0cacdb0c5d3f4'
         and receipt['physicalRun'] is False,'WK09_M2_PROVENANCE')
    for name,local in ASSETS[1:4]:
        rows=[r for r in receipt['files'] if r['name']==name]
        need(len(rows)==1 and rows[0]['sha256']==metas[local]['appProperties']['sha256']
             and rows[0]['integrity']=='FULL_REMOTE_READBACK_VERIFIED','WK09_INPUT_RECEIPT_LINK')
    proof=json.loads((temp/'old_proof.json').read_text())
    need(proof['instrumentedModelSHA256']==metas['M2340Source.slx']['appProperties']['sha256']
         and proof['period_s']==.01 and proof['trueT312CompiledWidthVerified'] is True
         and proof['fullRetainedParametersConfigGraphParity'] is True,'WK09_M2_PROOF')
    old=json.loads((temp/'old_manifest.json').read_text())
    rows=[r for r in old['inputs'] if r['local']=='source_workspace.mat']
    need(len(rows)==1 and rows[0]['sha256']==sha(temp/'source_workspace.mat'),'WK09_WORKSPACE_LINK')
    return assets,metas['M2340Source.slx']['appProperties']['sha256']


def check(auth):
    """OAuth refresh + GET only. No intent creation, checkout, subprocess or MATLAB."""
    d=definitions();g=d['groups'][auth['group']]
    need(not ROOT.exists(),'WK09_FRESH_PRIVATE_ROOT')
    token,folder,results=drive();require_verified_neutral_preflight(token,folder)
    need(quota(token)['availableBytes'] > (3+2*len(g['runs']))*GiB,'WK09_GROUP_DRIVE_RESERVE')
    absent(token,results,g['intent'])
    if not g['optional']:
        for case in g['runs']: absent(token,results,child_intent(g,case))
    with tempfile.TemporaryDirectory(prefix='wk09-check-') as temporary:
        temp=Path(temporary);os.chmod(temp,0o700)
        read_baseline(token,results,temp)
        if auth['group'] in {'CASES','R14'}: controls_acceptance(token,results,temp)
        inputs(token,folder,temp,model=False)
    print('WK09_PREFLIGHT_ALL_PASS group='+auth['group']+' MATLAB_STARTED=0')


def upload(token,folder,path):
    result=upload_verified(token,folder,path,schema=SCHEMA)
    private_acl(token,one(token,folder,'JTE063_VERIFIED_'+path.name)['id'])
    return result


def reserve(token,folder,name,path,value):
    absent(token,folder,name);write(path/name,value);upload(token,folder,path/name)


def report(exc):
    # Never echo an exception, path, private ID or console. Strict fixed code family.
    reason=exc.args[0] if isinstance(exc,RuntimeError) and len(exc.args)==1 else None
    suffix=' reason='+reason if type(reason) is str and re.fullmatch('WK09_[A-Z0-9_]+',reason) else ''
    print('WK09_UNQUALIFIED code='+type(exc).__name__+suffix)


if __name__=='__main__':
    import sys
    try:
        if sys.argv[1:]==['check']: check(context(check_only=True))
        elif sys.argv[1:]==['authorize']:
            context();print('WK09_CONTEXT_AUTHORIZED MATLAB_STARTED=0')
        else: need(False,'WK09_MODE_DENIED')
    except Exception as exc:
        report(exc);sys.exit(1)
