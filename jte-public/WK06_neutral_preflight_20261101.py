"""WK06 protected one-time neutral Drive readback; NO MATLAB and NO battery."""
from __future__ import annotations
import json, os, re, sys, urllib.parse
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO, API, access_token, ensure_app_folder, req
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota
BRANCH='refs/heads/codex/wk06-nonbattery-only-20261101'
TRIGGER='WK06_INFRA_PREFLIGHT_ONCE_20261101'
MARKER='WK06_NEUTRAL_PREFLIGHT_20261101.json'
NAMES=('JTE_GOOGLE_CLIENT_ID','JTE_GOOGLE_CLIENT_SECRET','JTE_GOOGLE_REFRESH_TOKEN')
def check_context(event, env):
    head=event.get('head_commit') or {}
    repo=event.get('repository') or {}
    if (env.get('GITHUB_REPOSITORY')!=EXPECTED_REPO or repo.get('full_name')!=EXPECTED_REPO or
        repo.get('private') is not False or env.get('GITHUB_REF')!=BRANCH or
        env.get('GITHUB_EVENT_NAME')!='push' or env.get('GITHUB_RUN_ATTEMPT')!='1' or
        env.get('RUNNER_ENVIRONMENT')!='github-hosted' or
        env.get('WK06_PROTECTED_ENV_NAME')!='JTE_DRIVE_WRITE' or
        head.get('message')!=TRIGGER or head.get('id')!=env.get('GITHUB_SHA') or
        not re.fullmatch(r'[0-9]+',env.get('GITHUB_RUN_ID','')) or
        not re.fullmatch(r'[0-9a-f]{40}',env.get('GITHUB_SHA',''))):
        raise PermissionError('WK06_WRONG_PROTECTED_CONTEXT')
    return env['GITHUB_RUN_ID'],env['GITHUB_SHA']
def check_private(token,file_id):
    url=API+'/'+urllib.parse.quote(file_id,safe='')+'?fields=id,permissions(type,role),mimeType'
    _,_,data=req(url,token=token)
    perms=json.loads(data).get('permissions') or []
    if not perms or any(p.get('type')!='user' or p.get('role')!='owner' for p in perms):
        raise PermissionError('WK06_DRIVE_NOT_OWNER_ONLY')
def query_receipts(token,folder):
    q="'"+folder+"' in parents and name = 'JTE063_VERIFIED_"+MARKER+"' and trashed = false"
    p=urllib.parse.urlencode({'q':q,'fields':'nextPageToken,files(id)','pageSize':'10'})
    _,_,raw=req(API+'?'+p,token=token)
    d=json.loads(raw)
    if d.get('nextPageToken'):raise RuntimeError('WK06_RECEIPT_PAGINATION')
    return d.get('files',[])
def main():
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    run,sha=check_context(event,os.environ)
    if not all(os.environ.get(k) for k in NAMES):raise RuntimeError('WK06_SECRET_NAMES_UNRESOLVED')
    token=access_token(*(os.environ[k] for k in NAMES))
    folder=ensure_app_folder(token)
    check_private(token,folder)
    if query_receipts(token,folder):raise RuntimeError('WK06_PREFLIGHT_RECEIPT_EXISTS_NO_RETRY')
    if quota(token)['availableBytes']<512*1024*1024:raise RuntimeError('WK06_DRIVE_QUOTA_TOO_LOW')
    root=Path('wk06-neutral-private')
    root.mkdir(mode=0o700,exist_ok=False)
    target=root/MARKER
    target.write_text(json.dumps({'schema':'WK06_PRE_MATLAB_NEUTRAL_ONLY',
       'commit':sha,'run':run,'branch':BRANCH,'physical':False,'MATLAB_CALLS':0,
       'TRIAL_CONSUMED':False,'G_M3':False,'G5':False},sort_keys=True),encoding='utf-8')
    os.chmod(target,0o600)
    upload_verified(token,folder,target,schema='SYNTHETIC_PREFLIGHT')
    matches=query_receipts(token,folder)
    if len(matches)!=1:raise RuntimeError('WK06_PRIVATE_RECEIPT_NOT_UNIQUE')
    check_private(token,matches[0]['id'])
    print('WK06_PROTECTED_NEUTRAL_PREFLIGHT_PASS remoteBytesSHA=VERIFIED ownerPrivate=TRUE MATLAB_CALLS=0 trialConsumed=false G5=false')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        safe=str(exc)
        if not re.fullmatch(r'WK06_[A-Z0-9_]+',safe):safe=type(exc).__name__
        print('WK06_NEUTRAL_PREFLIGHT_BLOCKED code='+safe+' MATLAB_CALLS=0 trialConsumed=false')
        sys.exit(1)
