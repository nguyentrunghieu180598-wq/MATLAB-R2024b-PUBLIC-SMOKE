"""Offline mocked control/transport/process tests. Never invoke MATLAB or CI."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch,Mock
import WK09_group as G
import WK09_group_gate as A
from WK09_run_definitions import definitions,H_SEL,H_SCENARIO,H_R2,H_PRED


def auth(group='CONTROLS'):
    g=definitions()['groups'][group]
    return dict(run='123',commit='a'*40,group=group,identity=g['identity'],runs=g['runs'],
                selectorSHA256=H_SEL,scenarioSHA256=H_SCENARIO,baselineReceiptSHA256=H_R2,
                predictionsSHA256=H_PRED,automaticRetry=False,G5Accepted=False)


class SequenceTests(unittest.TestCase):
    def test_sensitivity_failure_cannot_skip_dependency_controls(self):
        for bad in ('R3','R4'):
            calls=[];journal=[];now=time.monotonic()
            def execute(c,s,d):calls.append(c);return c!=bad
            self.assertFalse(G.sequence(auth(),now,now+30000,execute,lambda c,s:journal.append((c,s))))
            self.assertEqual(calls[:3],['R5','R12','R13'])
            self.assertEqual(calls[-1],bad)
            if bad=='R3':self.assertEqual(journal[-1],('R4','SKIPPED_AFTER_R3_FAILURE'))

    def test_success_exact_order_fresh_deadlines(self):
        for group in ('CONTROLS','CASES','R14'):
            calls=[];journal=[];now=time.monotonic()
            ok=G.sequence(auth(group),now,now+30000,lambda c,s,d:calls.append((c,s,d)) or True,
                          lambda c,s:journal.append((c,s)))
            self.assertTrue(ok);self.assertEqual([x[0] for x in calls],auth(group)['runs'])
            self.assertTrue(all(abs(d-s-G.CASE_SECONDS)<.001 for _,s,d in calls))
            self.assertTrue(all('PENDING_CLAUDE' in s for _,s in journal))

    def test_every_failure_position_skips_rest_without_retry(self):
        for group in ('CONTROLS','CASES'):
            order=auth(group)['runs']
            for ix,bad in enumerate(order):
                calls=[];journal=[];now=time.monotonic()
                def execute(c,s,d):calls.append(c);return c!=bad
                self.assertFalse(G.sequence(auth(group),now,now+30000,execute,lambda c,s:journal.append((c,s))))
                self.assertEqual(calls,order[:ix+1])
                self.assertEqual(journal[ix+1:],[(c,'SKIPPED_AFTER_'+bad+'_FAILURE') for c in order[ix+1:]])

    def test_worker_exception_and_job_clock_fail_closed(self):
        now=time.monotonic();called=Mock(side_effect=RuntimeError('private text'));journal=[]
        self.assertFalse(G.sequence(auth(),now,now+30000,called,lambda c,s:journal.append((c,s))))
        self.assertEqual(called.call_count,1)
        called=Mock();journal=[]
        self.assertFalse(G.sequence(auth(),now,now+2399,called,lambda c,s:journal.append((c,s))))
        called.assert_not_called();self.assertEqual(journal[0][1],'FAILED_JOB_TIME_RESERVE')

    def test_prepare_and_delivery_reserve(self):
        now=time.monotonic()
        with self.assertRaisesRegex(RuntimeError,'WK09_PREPARE_WALL'):G.launch_budget(now-601,now+3000)
        with self.assertRaisesRegex(RuntimeError,'WK09_DELIVERY_TIME_RESERVE'):G.launch_budget(now,now+1484)
        G.launch_budget(now,now+1600)


class AcceptanceTests(unittest.TestCase):
    def accepted(self):
        d=definitions();a=dict(schema=d['controls_acceptance']['schema'],reviewer='Claude',decision='ACCEPTED',
            hub_commit='b'*40,selector_sha256=H_SEL,scenario_sha256=H_SCENARIO,
            baseline_receipt_sha256=H_R2,predictions_sha256=H_PRED,runs=[])
        for c in d['controls_acceptance']['required_runs']:
            a['runs'].append(dict(id=c,accepted=True,receipt_name=c+'.json',receipt_sha256='d'*64,
                            max_abs_Tmax_R5_minus_R2_K=1e-6,
                            **{k:True for k in d['controls_acceptance']['criteria'][c]}))
        return a

    def run_acceptance(self,a):
        def fetch(token,folder,name,path,digest=None):
            return dict(case=name[:-5],group='CONTROLS',status='NATIVE_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE',
                        selectorSHA256=H_SEL,scenarioSHA256=H_SCENARIO,baselineReceiptSHA256=H_R2)
        raw=json.dumps(a).encode();d=definitions();d['controls_acceptance']['sha256']=hashlib.sha256(raw).hexdigest()
        with patch.dict(os.environ,{},clear=True),patch.object(A,'definitions',return_value=d),\
             patch.object(A.subprocess,'check_output',return_value=raw) as show,patch.object(A,'json_asset',side_effect=fetch) as receipts:
            result=A.controls_acceptance('token','folder',Path('private-temp'))
            show.assert_called_once_with(['git','show','HEAD~2:jte-public/WK09_CONTROLS_ACCEPTED.json'],stderr=A.subprocess.DEVNULL)
            self.assertEqual([c.args[2] for c in receipts.call_args_list],['R5.json','R12.json','R13.json'])
            self.assertTrue(all(c.args[4]=='d'*64 for c in receipts.call_args_list))
            return result

    def test_exact_acceptance_and_frozen_tolerance(self):
        self.assertEqual(self.run_acceptance(self.accepted())['hub_commit'],'b'*40)
        a=self.accepted();a['runs'][0]['max_abs_Tmax_R5_minus_R2_K']=1.00001e-6
        with self.assertRaisesRegex(RuntimeError,'WK09_R5_EQUIVALENCE'):self.run_acceptance(a)

    def test_every_criterion_required_not_native_success(self):
        for ix,row in enumerate(self.accepted()['runs']):
            for criterion in definitions()['controls_acceptance']['criteria'][row['id']]:
                a=self.accepted();a['runs'][ix][criterion]=False
                with self.assertRaisesRegex(RuntimeError,'WK09_CONTROLS_CRITERIA'):self.run_acceptance(a)
        for field,value in [('decision','NATIVE_PASS'),('reviewer','Codex'),('hub_commit','invalid'),('selector_sha256','0'*64)]:
            a=self.accepted();a[field]=value
            with self.assertRaises(RuntimeError):self.run_acceptance(a)

    def test_unset_acceptance_rejected_before_source_or_private_receipt_reads(self):
        with patch.dict(os.environ,{},clear=True),patch.object(A,'json_asset') as fetch,patch.object(A.subprocess,'check_output') as show:
            with self.assertRaisesRegex(RuntimeError,'WK09_CONTROLS_ACCEPTANCE_UNSET'):
                A.controls_acceptance('t','f',Path('private'))
            fetch.assert_not_called();show.assert_not_called()

    def test_missing_or_wrong_source_bytes_fail_before_private_receipts(self):
        d=definitions();d['controls_acceptance']['sha256']='a'*64
        for failure in (A.subprocess.CalledProcessError(128,['git','show']),b'wrong bytes'):
            kwargs={'side_effect':failure} if isinstance(failure,Exception) else {'return_value':failure}
            with patch.object(A,'definitions',return_value=d),patch.object(A.subprocess,'check_output',**kwargs),patch.object(A,'json_asset') as fetch:
                with self.assertRaisesRegex(RuntimeError,'WK09_CONTROLS_ACCEPTANCE_(UNSET|DIGEST)'):
                    A.controls_acceptance('t','f',Path('private'))
                fetch.assert_not_called()

    def test_acceptance_requires_exact_dependency_order_without_sensitivities(self):
        for order in (['R12','R5','R13'],['R5','R12'],['R5','R12','R13','R3','R4']):
            a=self.accepted();byid={r['id']:r for r in a['runs']}
            a['runs']=[byid.get(c,dict(id=c)) for c in order]
            with self.assertRaisesRegex(RuntimeError,'WK09_CONTROLS_ALLOWLIST'):self.run_acceptance(a)

    def test_private_receipt_case_group_status_provenance_still_checked(self):
        a=self.accepted();raw=json.dumps(a).encode();d=definitions()
        d['controls_acceptance']['sha256']=hashlib.sha256(raw).hexdigest()
        good=dict(case='R5',group='CONTROLS',status='NATIVE_AND_PRIVATE_READBACK_PASS_PENDING_CLAUDE',
                  selectorSHA256=H_SEL,scenarioSHA256=H_SCENARIO,baselineReceiptSHA256=H_R2)
        for field in good:
            bad=dict(good);bad[field]='wrong'
            with patch.object(A,'definitions',return_value=d),patch.object(A.subprocess,'check_output',return_value=raw),\
                 patch.object(A,'json_asset',return_value=bad),self.assertRaisesRegex(RuntimeError,'WK09_CONTROL_RECEIPT'):
                A.controls_acceptance('t','f',Path('private'))

    def test_pin_bytes_and_acl_checked(self):
        meta=dict(id='private',size='20',appProperties=dict(state='VERIFIED',sha256='a'*64))
        with patch.object(A,'metadata',return_value=meta),patch.object(A,'download') as download:
            with self.assertRaisesRegex(RuntimeError,'WK09_RECEIPT_DIGEST'):
                A.json_asset('t','f','r.json',Path('private'),'b'*64)
            download.assert_not_called()


class PreflightTests(unittest.TestCase):
    def test_r14_requires_same_acceptance_before_inputs_without_writes_or_launch(self):
        with tempfile.TemporaryDirectory() as t,patch.object(A,'ROOT',Path(t)/'absent'),\
             patch.object(A,'drive',return_value=('t','app','results')),\
             patch.object(A,'require_verified_neutral_preflight'),\
             patch.object(A,'quota',return_value={'availableBytes':100*A.GiB}),patch.object(A,'absent'),\
             patch.object(A,'read_baseline'),patch.object(A,'controls_acceptance',side_effect=RuntimeError('WK09_CONTROLS_ACCEPTANCE_UNSET')) as acceptance,\
             patch.object(A,'inputs') as inputs,patch.object(A,'upload') as upload,\
             patch.object(A,'reserve') as reserve,patch.object(G.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError,'WK09_CONTROLS_ACCEPTANCE_UNSET'):A.check(auth('R14'))
            acceptance.assert_called_once();inputs.assert_not_called()
            upload.assert_not_called();reserve.assert_not_called();popen.assert_not_called()

    def test_check_readonly_and_cases_acceptance_before_inputs(self):
        calls=[]
        with tempfile.TemporaryDirectory() as t,patch.object(A,'ROOT',Path(t)/'absent'),\
             patch.object(A,'drive',return_value=('t','app','results')),\
             patch.object(A,'require_verified_neutral_preflight'),\
             patch.object(A,'quota',return_value={'availableBytes':100*A.GiB}),\
             patch.object(A,'absent',side_effect=lambda *a:calls.append('absent')),\
             patch.object(A,'read_baseline',side_effect=lambda *a:calls.append('baseline')),\
             patch.object(A,'controls_acceptance',side_effect=lambda *a:calls.append('acceptance')),\
             patch.object(A,'inputs',side_effect=lambda *a,**k:calls.append('inputs')),\
             patch.object(A,'upload') as upload,patch.object(A,'reserve') as reserve,\
             patch.object(G.subprocess,'Popen') as popen,contextlib.redirect_stdout(io.StringIO()):
            A.check(auth('CASES'))
            self.assertLess(calls.index('acceptance'),calls.index('inputs'))
            self.assertEqual(calls.count('absent'),7)
            upload.assert_not_called();reserve.assert_not_called();popen.assert_not_called()

    def test_spent_parent_or_child_stops(self):
        with patch.object(A,'query',return_value=[{}]),self.assertRaisesRegex(RuntimeError,'WK09_SPENT_IDENTITY_NO_RETRY'):
            A.absent('t','f','new_intent.json')
        with self.assertRaisesRegex(RuntimeError,'WK09_CASE_OUTSIDE_ALLOWLIST'):
            A.child_intent(definitions()['groups']['CONTROLS'],'R14')

    def test_public_error_never_echoes_text_ids_or_console(self):
        for e in (RuntimeError('secret /private/path id123'),ValueError('WK09_BAD_SECRET'),RuntimeError({'secret':'value'})):
            out=io.StringIO()
            with contextlib.redirect_stdout(out):A.report(e)
            self.assertNotIn('secret',out.getvalue());self.assertNotIn('/private',out.getvalue())
        out=io.StringIO()
        with contextlib.redirect_stdout(out):A.report(RuntimeError('WK09_PREPARE_WALL'))
        self.assertIn('reason=WK09_PREPARE_WALL',out.getvalue())


class ContextTests(unittest.TestCase):
    def setup_context(self,root,group='CONTROLS',check=False):
        d=definitions();g=d['groups'][group];pre='preflight_' if check else ''
        marker=root/g[pre+'marker'];marker.parent.mkdir(parents=True);marker.write_text(g[pre+'message'])
        event=dict(repository=dict(full_name=A.REPO,private=False),
                   head_commit=dict(message=g[pre+'message'],id='a'*40))
        f=root/'event.json';f.write_text(json.dumps(event))
        env=dict(GITHUB_EVENT_PATH=str(f),GITHUB_REPOSITORY=A.REPO,GITHUB_REF='refs/heads/'+d['branch'],
                 GITHUB_EVENT_NAME='push',GITHUB_RUN_ATTEMPT='1',RUNNER_ENVIRONMENT='github-hosted',
                 WK09_PROTECTED_ENV_NAME='JTE_DRIVE_WRITE',WK09_OWNER_APPROVAL=g[pre+'approval'],
                 WK09_GROUP=group,WK09_REVIEWED_SOURCE_SHA='b'*40,GITHUB_SHA='a'*40,GITHUB_RUN_ID='123')
        def git(*args):
            return {('rev-parse','HEAD'):'a'*40,('rev-parse','HEAD~2'):'b'*40,
                    ('diff','--name-only','HEAD~2','HEAD~1'):g[pre+'workflow'],
                    ('diff','--name-only','HEAD~1','HEAD'):g[pre+'marker'],
                    ('ls-tree','HEAD~2','--',g[pre+'marker']):''}[args]
        return env,git

    def test_all_six_contexts_and_exact_ordered_grant(self):
        old=Path.read_text
        for group in ('CONTROLS','CASES','R14'):
            for check in (False,True):
                with tempfile.TemporaryDirectory() as t:
                    root=Path(t);env,git=self.setup_context(root,group,check)
                    def read(p,*a,**k):return old(root/p,*a,**k) if 'TRIGGER' in p.name else old(p,*a,**k)
                    with patch.dict(os.environ,env,clear=True),patch.object(A,'git',side_effect=git),patch.object(Path,'read_text',read):
                        result=A.context(check);self.assertEqual(result['runs'],definitions()['groups'][group]['runs'])

    def test_context_wrong_approval_retry_branch_event_and_zero_source(self):
        old=Path.read_text
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);env,git=self.setup_context(root)
            def read(p,*a,**k):return old(root/p,*a,**k) if 'TRIGGER' in p.name else old(p,*a,**k)
            for key,value in [('WK09_OWNER_APPROVAL','APPROVE_OTHER'),('GITHUB_RUN_ATTEMPT','2'),
                              ('GITHUB_REF','refs/heads/main'),('GITHUB_EVENT_NAME','workflow_dispatch'),
                              ('WK09_REVIEWED_SOURCE_SHA','0'*40)]:
                with patch.dict(os.environ,{**env,key:value},clear=True),patch.object(A,'git',side_effect=git),patch.object(Path,'read_text',read),self.assertRaises(RuntimeError):A.context()

    def test_old_head_marker_or_extra_changed_file_denied(self):
        old=Path.read_text
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);env,git=self.setup_context(root)
            def read(p,*a,**k):return old(root/p,*a,**k) if 'TRIGGER' in p.name else old(p,*a,**k)
            for change in ('old_marker','extra_source'):
                def altered(*a):
                    if change=='old_marker' and a[0]=='ls-tree':return 'present'
                    if change=='extra_source' and a==('diff','--name-only','HEAD~2','HEAD~1'):return 'extra.py'
                    return git(*a)
                with patch.dict(os.environ,env,clear=True),patch.object(A,'git',side_effect=altered),patch.object(Path,'read_text',read),self.assertRaisesRegex(RuntimeError,'WK09_CHAIN_DENIED'):A.context()


class ProcessTests(unittest.TestCase):
    def test_one_launcher_process_secret_stripping_private_2048_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);launcher=root/'launcher';launcher.write_text('not executed');launcher.chmod(0o700)
            fake=Mock(pid=123);fake.poll.return_value=0;fake.wait.return_value=0
            def start(argv,**kwargs):kwargs['stdout'].write(b'PRIVATE_CONSOLE'*300);return fake
            env=dict(WK08_RUN_MATLAB_COMMAND=str(launcher),WK09_CASE='R3',JTE_GOOGLE_CLIENT_ID='secret',
                     JTE_GOOGLE_CLIENT_SECRET='secret',JTE_GOOGLE_REFRESH_TOKEN='secret',GH_TOKEN='secret',GITHUB_TOKEN='secret')
            with patch.dict(os.environ,env),patch.object(G,'memory',return_value={'hostAvailable':20*A.GiB,'cgroupAvailable':20*A.GiB}),\
                 patch.object(G.shutil,'disk_usage',return_value=Mock(free=20*A.GiB)),\
                 patch.object(A,'quota',return_value={'availableBytes':20*A.GiB}),\
                 patch.object(G.subprocess,'Popen',side_effect=start) as popen,patch.object(G,'proc_start',return_value='id'):
                now=time.monotonic();self.assertTrue(G.supervisor(auth(),root,'t',now,now+2100))
            self.assertEqual(popen.call_count,1);args,kwargs=popen.call_args
            self.assertEqual(args[0][0],str(launcher));self.assertEqual(len(args[0]),2)
            childenv=kwargs['env'];self.assertEqual(childenv['MW_BATCH_LICENSING_ONLINE'],'true')
            self.assertFalse(any(k.startswith('JTE_GOOGLE_') or k in {'GH_TOKEN','GITHUB_TOKEN'} for k in childenv))
            report=G.read(root/'WK09_SUPERVISOR.json');self.assertEqual(report['consoleExcerptBytes'],2048)
            self.assertEqual(len(__import__('base64').b64decode(report['consoleExcerptBase64'])),2048)
            self.assertFalse(report['automaticRetry']);self.assertFalse(report['G5Accepted'])

    def test_bounded_worker_kills_tree_without_retry(self):
        fake=Mock(pid=123);fake.poll.return_value=None
        with tempfile.TemporaryDirectory() as t,patch.object(G.subprocess,'Popen',return_value=fake) as popen,\
             patch.object(G,'proc_start',return_value='identity'),patch.object(G,'terminate_tree') as kill:
            self.assertFalse(G.bounded_worker(['worker','R3','0','0'],0,Path(t)/'private.log'))
            kill.assert_called();self.assertEqual(popen.call_count,1)

    def test_per_run_remote_names_and_receipt_readback(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'native').mkdir()
            for role in A.NATIVE:(root/'native'/('WK09_R5_'+role+'.mat')).write_bytes(b'fake native')
            a=auth();m=dict(a,case='R5',inputCodeSHA256={},inputs=[dict(local='input',sha256='a'*64)])
            f=dict(a,case='R5',status='NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK')
            s=dict(a,case='R5',status='PROCESS_EXIT_ZERO',returncode=0)
            for name,value in [('WK09_MANIFEST.json',m),('WK09_FLAGS.json',f),('WK09_SUPERVISOR.json',s)]:
                (root/name).write_text(json.dumps(value))
            for name in ['input','WK09_DEFINITION.json','WK09_PREPARED_PROOF.mat','WK09_RESOURCES.jsonl','WK09_R5.slx']:(root/name).write_bytes(b'fake')
            calls=[]
            def upload(token,folder,p):
                calls.append(p.name);return dict(integrity='FULL_REMOTE_READBACK_VERIFIED',sha256='a'*64,size_bytes=p.stat().st_size)
            with patch.object(A,'code_hashes',return_value={}),patch.object(G,'sha',return_value='a'*64),patch.object(A,'upload',side_effect=upload):
                self.assertTrue(G.publish(a,'R5',root,'t','f'))
            self.assertTrue(all(n.startswith('123_R5_') for n in calls[:-1]))
            self.assertEqual(calls[-1],'WK09_D13_CONTROLS_A_123_R5_PRIVATE_RECEIPT.json')
            self.assertTrue(G.read(root/'WK09_OUTCOME.json')['passed'])
            self.assertFalse((root/'SUMMARY.json').exists()) # diagnostic not required for qualification


if __name__=='__main__':unittest.main()
