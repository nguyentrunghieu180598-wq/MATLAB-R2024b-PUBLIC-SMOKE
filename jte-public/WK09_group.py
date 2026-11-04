"""WK09 sealed ordered job. One disposable worker/process per case, never retry.

The parent clock covers all cases, preparation and full-byte private readback.
Each worker has its declared per-case envelope; a failed/undelivered case
stops the group. Scientific CONTROLS acceptance remains Claude's separate act.
"""
import base64
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

import WK09_group_gate as gate
from WK09_run_definitions import ROOT as CODE, definitions, resolve, sha, need
from BTMS_M3_oneShotWatchdog import memory, violation, proc_start, proc_rss, terminate_tree

CASE_SECONDS = 35*60
DELIVERY_SECONDS = 300


def remaining(deadline):
    return deadline-time.monotonic()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def case_root(auth,case):
    need(case in definitions()['groups'][auth['group']]['runs'], 'WK09_CASE_OUTSIDE_ALLOWLIST')
    return gate.ROOT/auth['run']/case


def launch_budget(case_start,deadline,matlab_wall_s=1185):
    need(time.monotonic()-case_start <= 600, 'WK09_PREPARE_WALL')
    need(remaining(deadline) >= matlab_wall_s+DELIVERY_SECONDS, 'WK09_DELIVERY_TIME_RESERVE')


def supervisor(auth,root,token,case_start,deadline):
    definition=read(root/'WK09_MANIFEST.json').get('definition',{})
    matlab_wall_s=definition.get('matlab_wall_s',1185)
    launch_budget(case_start,deadline,matlab_wall_s)
    free_drive=gate.quota(token)['availableBytes'];mem=memory()
    need(mem['hostAvailable'] >= 8*gate.GiB and
         (mem['cgroupAvailable'] is None or mem['cgroupAvailable'] >= 8*gate.GiB)
         and shutil.disk_usage(root).free >= 10*gate.GiB and free_drive >= 3*gate.GiB,
         'WK09_PREFLIGHT_RESOURCE')
    launcher=os.environ.get('WK08_RUN_MATLAB_COMMAND','')
    need(launcher and os.path.isfile(launcher) and os.access(launcher,os.X_OK), 'WK09_LAUNCHER_UNAVAILABLE')
    env={k:v for k,v in os.environ.items() if not k.startswith('JTE_GOOGLE_')
         and k not in {'GH_TOKEN','GITHUB_TOKEN'}}
    env['MW_BATCH_LICENSING_ONLINE']='true'
    command="addpath('jte-public'); BTMS_WK09_run('"+(root/'WK09_MANIFEST.json').as_posix()+"')"
    report=dict(auth,case=os.environ['WK09_CASE'],status='UNQUALIFIED',returncode=None,
                matlabProcessesLaunched=0)
    console=root/'WK09_CONSOLE.log';proc=None;identity=None;started=time.monotonic()
    updates=queue.Queue();refresh=None;refreshed=started
    def refresh_quota():
        try: updates.put((True,gate.quota(token)['availableBytes']))
        except Exception: updates.put((False,None))
    try:
        with console.open('xb') as output,(root/'WK09_RESOURCES.jsonl').open('x') as samples:
            proc=subprocess.Popen([launcher,command],env=env,stdout=output,stderr=subprocess.STDOUT)
            report['matlabProcessesLaunched']=1;identity=proc_start(proc.pid)
            while proc.poll() is None:
                now=time.monotonic()
                if refresh is None and now-refreshed >= 45:
                    refresh=threading.Thread(target=refresh_quota,daemon=True);refreshed=now;refresh.start()
                if refresh is not None:
                    if not updates.empty():
                        ok,value=updates.get();need(ok,'WK09_DRIVE_REFRESH_FAILED');free_drive=value;refresh=None
                    else: need(now-refreshed <= 10,'WK09_DRIVE_REFRESH_TIMEOUT')
                sizes=[p.stat().st_size for p in (root/'native').glob('*.mat')]
                mem=memory();reason=violation(mem,shutil.disk_usage(root).free,free_drive,sizes,now-started,wall=matlab_wall_s)
                samples.write(json.dumps(dict(unix=time.time(),memory=mem,matlabRSS_bytes=proc_rss(proc.pid),
                                              nativeBytes=sum(sizes),elapsed_s=now-started))+'\n');samples.flush()
                if reason:
                    report['status']='UNQUALIFIED_'+reason;terminate_tree(proc.pid,identity);break
                need(remaining(deadline) >= DELIVERY_SECONDS,'WK09_DELIVERY_TIME_RESERVE')
                time.sleep(.5)
            report['returncode']=proc.wait(timeout=15)
            if report['returncode']==0 and report['status']=='UNQUALIFIED': report['status']='PROCESS_EXIT_ZERO'
    except Exception as exc:
        report['exceptionType']=type(exc).__name__
        if proc is not None and identity is not None and proc.poll() is None: terminate_tree(proc.pid,identity)
    finally:
        report['elapsed_s']=time.monotonic()-started
        if console.exists():
            with console.open('rb') as f: excerpt=f.read(2048)
            report.update(consoleExcerptBytes=len(excerpt),consoleExcerpt=excerpt.decode('utf-8',errors='replace'),
                          consoleExcerptBase64=base64.b64encode(excerpt).decode('ascii'))
        gate.write(root/'WK09_SUPERVISOR.json',report)
    return report['status']=='PROCESS_EXIT_ZERO'


def prepare(auth,case,root,token,folder):
    assets,source_sha=gate.inputs(token,folder,root,model=True)
    d=definitions();scenario=read(CODE/'WK10_scenario.json');vendor=Path('vendor-pack').resolve()
    need(gate.git('-C',str(vendor),'rev-parse','HEAD')==d['vendor_commit'],'WK09_VENDOR_COMMIT')
    vendor_slx=vendor/'Models/Battery_Pack_Thermal_Management.slx'
    need(sha(vendor_slx)==scenario['model_sha256'] and
         sha(vendor/'Scripts_Data/Battery_Pack_Thermal_Management_Ivst.mat')==scenario['vendor_mat_sha256'],
         'WK09_VENDOR_BYTES')
    definition=resolve(case,auth['group']);definition_file=root/'WK09_DEFINITION.json';gate.write(definition_file,definition)
    manifest=dict(auth,case=case,definition=definition,definitionFile=str(definition_file.resolve()),
                  definitionSHA256=sha(definition_file),scenario=scenario,privateRoot=str(root.resolve()),
                  sourceSHA256=source_sha,inputs=assets,vendorRoot=str(vendor),vendorSLX=str(vendor_slx),
                  inputCodeSHA256=gate.code_hashes())
    gate.write(root/'WK09_MANIFEST.json',manifest)


def payloads(root,case):
    # Never publish downloaded inputs or staging copies, and never follow links.
    names={'WK09_MANIFEST.json','WK09_DEFINITION.json','WK09_PREPARED_PROOF.mat',
           'WK09_FLAGS.json','WK09_SUPERVISOR.json','WK09_RESOURCES.jsonl','WK09_CONSOLE.log','WK09_'+case+'.slx'}
    paths=[root/n for n in sorted(names) if (root/n).is_file()]+sorted((root/'native').glob('*.mat'))
    if (root/'WK09_PREPARE_FAILURE.json').is_file(): paths.append(root/'WK09_PREPARE_FAILURE.json')
    need(all(not p.is_symlink() for p in paths),'WK09_SYMLINK')
    need(all(p.stat().st_size <= gate.GiB for p in paths) and
         sum(p.stat().st_size for p in paths) <= 2*gate.GiB,'WK09_DELIVERY_CAP')
    return paths,names-{'WK09_CONSOLE.log'} | {'WK09_'+case+'_'+role+'.mat' for role in gate.NATIVE}


def publish(auth,case,root,token,results):
    receipt=dict(auth,case=case,schema=gate.SCHEMA,files=[],status='UNQUALIFIED',rawDataPublic=False)
    manifest=read(root/'WK09_MANIFEST.json') if (root/'WK09_MANIFEST.json').is_file() else {}
    flags=read(root/'WK09_FLAGS.json') if (root/'WK09_FLAGS.json').is_file() else {}
    monitor=read(root/'WK09_SUPERVISOR.json') if (root/'WK09_SUPERVISOR.json').is_file() else {}
    same=all(x.get('run')==auth['run'] and x.get('commit')==auth['commit'] and
             x.get('case')==case and x.get('group')==auth['group'] for x in (manifest,flags,monitor))
    unchanged=manifest.get('inputCodeSHA256')==gate.code_hashes()
    inputs_ok=bool(manifest.get('inputs')) and all(sha(root/a['local'])==a['sha256'] for a in manifest.get('inputs',[]))
    paths,required=payloads(root,case);staging=root/'delivery';staging.mkdir(mode=0o700)
    def send(path):
        target=staging/(auth['run']+'_'+case+'_'+path.name);shutil.copyfile(path,target)
        result=gate.upload(token,results,target)
        return dict(name=path.name,remoteName=target.name,**result)
    for path in paths:
        if path.stat().st_size: receipt['files'].append(send(path))
    complete=required <= {x['name'] for x in receipt['files']}
    passed=same and unchanged and inputs_ok and complete and flags.get('status')=='NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK' and monitor.get('status')=='PROCESS_EXIT_ZERO' and monitor.get('returncode')==0
    # Only copy the MATLAB-derived diagnostic; never read or assess its values.
    receipt['summaryDelivery']='NOT VERIFIED'
    try:
        summary=root/'SUMMARY.json'
        need(summary.is_file() and not summary.is_symlink() and 0 < summary.stat().st_size <= 64*1024
             and sum(p.stat().st_size for p in paths)+summary.stat().st_size <= 2*gate.GiB,'WK09_SUMMARY_UNAVAILABLE')
        receipt['files'].append(send(summary));receipt['summaryDelivery']='DERIVED_NOT_EVIDENCE_PRIVATE_READBACK'
    except Exception as exc: receipt['summaryDeliveryErrorType']=type(exc).__name__
    receipt.update(sameAttempt=same,sourceCodeUnchanged=unchanged,inputsUnchanged=inputs_ok,requiredPayloadComplete=complete)
    if passed: receipt['status']='NATIVE_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE'
    name=gate.receipt_name(auth,case)
    path=staging/name;gate.write(path,receipt);gate.upload(token,results,path)
    # Existence is recorded only after the receipt's full-byte remote readback.
    gate.write(root/'WK09_OUTCOME.json',dict(case=case,passed=bool(passed),receipt_name=name,receipt_sha256=sha(path)))
    return bool(passed)


def worker(auth,case,case_start,deadline):
    root=case_root(auth,case);grant=read(root/'WK09_GRANT.json')
    case_seconds=resolve(case,auth['group']).get('case_seconds',CASE_SECONDS)
    need(os.environ.get('WK09_CASE')==case and grant['auth']==auth and grant['case']==case and grant['codeSHA256']==gate.code_hashes()
         and grant['case_start']==case_start and grant['deadline']==deadline,'WK09_GRANT_MISMATCH')
    token,folder,results=gate.drive();g=definitions()['groups'][auth['group']]
    # Parent intent must still match byte-for-byte; no forged/local-only grant.
    remote=gate.json_asset(token,results,g['intent'],root/'WK09_PARENT_READBACK.json')
    need(remote==read(gate.ROOT/auth['run']/g['intent']) and remote['codeSHA256']==grant['codeSHA256']
         and remote['orderedAllowlist']==auth['runs'] and remote['allowRetry'] is False
         and case_start >= remote['job_start']
         and deadline == min(case_start+case_seconds,remote['job_deadline']), 'WK09_PARENT_INTENT_MISMATCH')
    if not g['optional']:
        gate.reserve(token,results,gate.child_intent(g,case),root,dict(auth,case=case,exactlyOneInitialize=True))
    success=False
    try:
        prepare(auth,case,root,token,folder)
        success=supervisor(auth,root,token,case_start,deadline)
    except Exception as exc:
        gate.write(root/'WK09_PREPARE_FAILURE.json',dict(exceptionType=type(exc).__name__))
    finally:
        # Any failure gets one delivery attempt, bounded by the parent envelope.
        success=publish(auth,case,root,token,results) and success
    return 0 if success else 1


def bounded_worker(args,deadline,console,env=None):
    """Bound blocked transport and every descendant as well as MATLAB itself."""
    proc=None;identity=None
    try:
        with console.open('xb') as output:
            proc=subprocess.Popen([sys.executable,'-B',__file__,*args],env=env,
                                  stdout=output,stderr=subprocess.STDOUT)
            identity=proc_start(proc.pid)
            while proc.poll() is None:
                if remaining(deadline) <= 21:
                    terminate_tree(proc.pid,identity);return False
                time.sleep(.5)
            return proc.wait(timeout=15)==0
    finally:
        if proc is not None and identity is not None and proc.poll() is None: terminate_tree(proc.pid,identity)


def sequence(auth,job_start,job_deadline,execute,record):
    """Pure orchestration seam: injected worker/journal, one never-reset clock."""
    stopped=None;success=True;g=definitions()['groups'][auth['group']]
    for case in g['runs']:
        if stopped:
            record(case,'SKIPPED_AFTER_'+stopped+'_FAILURE');continue
        start=job_start if auth['group']=='R14' else time.monotonic()
        case_seconds=resolve(case,auth['group']).get('case_seconds',CASE_SECONDS)
        # Keep the complete declared per-case envelope plus final journal reserve.
        if auth['group']!='R14' and remaining(job_deadline) < case_seconds+DELIVERY_SECONDS:
            record(case,'FAILED_JOB_TIME_RESERVE');stopped=case;success=False;continue
        deadline=min(start+case_seconds,job_deadline)
        try: ok=execute(case,start,deadline)
        except Exception: ok=False
        record(case,'NATIVE_PRIVATE_PASS_PENDING_CLAUDE' if ok else 'FAILED_UNQUALIFIED')
        if not ok: stopped=case;success=False
    return success


def run_group(auth):
    # Clock is exported by workflow's FIRST step, before checkout/setup/license probe.
    elapsed=time.time()-float(os.environ['WK09_JOB_START_EPOCH'])
    need(0 <= elapsed <= 900,'WK09_JOB_SETUP_WALL')
    job_start=time.monotonic()-elapsed;g=definitions()['groups'][auth['group']]
    deadline=job_start+g['timeout_minutes']*60
    gate.check(auth)  # all read-only checks, especially CASES acceptance, BEFORE reservation
    token,folder,results=gate.drive()
    gate.ROOT.mkdir(mode=0o700);root=gate.ROOT/auth['run'];root.mkdir(mode=0o700)
    grant=dict(auth,codeSHA256=gate.code_hashes(),orderedAllowlist=list(g['runs']),
               job_start=job_start,job_deadline=deadline,allowRetry=False,exactlyOneInitializePerCase=True)
    gate.reserve(token,results,g['intent'],root,grant)
    journal=dict(auth,cases=[]);journal_file=root/'WK09_GROUP_JOURNAL.json'
    def record(case,status):
        row=dict(case=case,status=status,receiptDelivery='NOT VERIFIED')
        outcome=case_root(auth,case)/'WK09_OUTCOME.json'
        if outcome.is_file(): row.update(privateReceipt=read(outcome),receiptDelivery='FULL_REMOTE_READBACK_VERIFIED')
        journal['cases'].append(row)
        # Atomic local journal even if the later private upload fails or times out.
        tmp=journal_file.with_suffix('.partial');tmp.write_text(json.dumps(journal,indent=2));os.replace(tmp,journal_file)
    def execute(case,start,limit):
        casepath=case_root(auth,case);casepath.mkdir(mode=0o700)
        gate.write(casepath/'WK09_GRANT.json',dict(auth=auth,case=case,case_start=start,deadline=limit,
                                                 codeSHA256=grant['codeSHA256']))
        env=dict(os.environ,WK09_CASE=case)
        ok=bounded_worker(['worker',case,str(start),str(limit)],limit,casepath/'WORKER_CONSOLE.log',env)
        outcome=casepath/'WK09_OUTCOME.json'
        return ok and outcome.is_file() and read(outcome).get('passed') is True
    success=False
    try: success=sequence(auth,job_start,deadline,execute,record)
    finally:
        journal['status']='ALL_NATIVE_PRIVATE_PENDING_CLAUDE' if success else 'GROUP_UNQUALIFIED'
        journal_file.write_text(json.dumps(journal,indent=2))
        # Final journal upload is also isolated so a blocked request cannot outlive the job.
        delivered=bounded_worker(['journal'],deadline,root/'JOURNAL_UPLOAD_CONSOLE.log')
    need(success and delivered,'WK09_GROUP_UNQUALIFIED_NO_RETRY')
    print('WK09_GROUP_PRIVATE_COMPLETE group='+auth['group']+' pendingClaudeReview=1 G5_ACCEPTED=false')


def journal_upload(auth):
    token,_,results=gate.drive()
    root=gate.ROOT/auth['run'];p=root/(auth['run']+'_'+auth['identity']+'_JOURNAL.json')
    shutil.copyfile(root/'WK09_GROUP_JOURNAL.json',p);gate.upload(token,results,p)


if __name__=='__main__':
    try:
        auth=gate.context()
        if sys.argv[1:]==['run']: run_group(auth)
        elif len(sys.argv)==5 and sys.argv[1]=='worker':
            sys.exit(worker(auth,sys.argv[2],float(sys.argv[3]),float(sys.argv[4])))
        elif sys.argv[1:]==['journal']: journal_upload(auth)
        else: need(False,'WK09_MODE_DENIED')
    except Exception as exc:
        gate.report(exc);sys.exit(1)
