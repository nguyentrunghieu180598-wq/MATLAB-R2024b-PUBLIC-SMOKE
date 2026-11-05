"""Offline contracts and mocked sealed execution; no MATLAB or network."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch, Mock

import WK09_run_definitions as D
import WK09_group_gate as A
import WK09_group as G
import WK10_D14_probe as P


class ProbeTests(unittest.TestCase):
    def test_scenarios_only_change_declared_id_and_gain_and_pin_unique_bytes(self):
        original=json.loads((P.ROOT/'WK10_scenario.json').read_text())
        digests={D.sha(P.ROOT/'WK10_scenario.json')}
        for case,(sid,k,digest) in P.SPECS.items():
            self.assertEqual(P.scenario(case),dict(original,scenario_id=sid,k=k))
            self.assertEqual(D.sha(P.ROOT/('WK10_'+sid+'.json')),digest)
            digests.add(digest)
        self.assertEqual(len(digests),3)

    def test_d13_registry_and_scenario_bytes_unchanged(self):
        self.assertEqual(D.sha(P.ROOT/'WK09_runs.json'),
                         '4308c9ed977a0a974c545449ea6a321bb85e656099dab48d9f7090dbf9470936')
        self.assertEqual(D.sha(P.ROOT/'WK10_scenario.json'),D.H_SCENARIO)
        self.assertEqual(D.ORDERS,{'CONTROLS':['R5','R12','R13','R3','R4'],
            'CASES':['R6','R7','R8','R9','R10','R11'],'R14':['R14'],'ROBUST':['R3','R4']})

    def test_exact_order_identity_names_unbiased_active_full_layout_and_walls(self):
        d=P.definitions();g=d['groups']['PROBE14']
        self.assertEqual(g['identity'],'WK10_D14_PROBE_A');self.assertEqual(g['runs'],['P150','P175'])
        self.assertFalse(g['optional']);self.assertEqual(g['timeout_minutes'],90)
        self.assertEqual(g['intent'],'WK10_D14_PROBE_A_JOB_INTENT.json')
        for case in g['runs']:
            r=P.resolve(case,'PROBE14')
            self.assertEqual((r['bias_K'],r['sensors'],r['measurement_pipeline']),(0,312,'active'))
            self.assertEqual((r['Ts_s'],r['stop_s'],r['mode']),(.01,340,'D13_REF'))
            self.assertEqual((r['matlab_wall_s'],r['case_seconds']),(1185,2100))
            self.assertEqual(r['subset'],list(range(1,313)))
        with self.assertRaises(RuntimeError):P.resolve('R5','PROBE14')
        with self.assertRaises(RuntimeError):P.resolve('P150','CASES')

    def test_scenario_and_registry_mutations_are_rejected(self):
        old=Path.read_text
        for mutate in (lambda d:d['groups']['PROBE14']['runs'].reverse(),
                       lambda d:d['runs'][0].update(bias_K=-2),
                       lambda d:d['runs'][0].update(matlab_wall_s=3000)):
            d=copy.deepcopy(P.definitions());mutate(d)
            def read(path,*a,**k):return json.dumps(d) if path.name==P.REGISTRY else old(path,*a,**k)
            with patch.object(Path,'read_text',read),self.assertRaises(RuntimeError):P.definitions()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'WK10_scenario.json').write_bytes((P.ROOT/'WK10_scenario.json').read_bytes())
            sid=P.SPECS['P150'][0];(root/('WK10_'+sid+'.json')).write_text('{}')
            with patch.object(P,'ROOT',root),self.assertRaisesRegex(RuntimeError,'WK09_D14_SCENARIO_SHA'):
                P.scenario('P150')

    def test_both_workflows_disabled_no_markers_and_readonly_preflight(self):
        g=P.definitions()['groups']['PROBE14']
        for pre in ('','preflight_'):
            s=(P.ROOT.parent/g[pre+'workflow']).read_text()
            self.assertIn('if: ${{ false }}',s);self.assertIn('WK09_GROUP: PROBE14',s)
            self.assertIn('codex/wk11-d14-probe',s);self.assertIn(g[pre+'marker'],s)
            self.assertIn("WK09_REVIEWED_SOURCE_SHA: '"+'0'*40+"'",s)
            self.assertFalse((P.ROOT.parent/g[pre+'marker']).exists())
            self.assertNotIn('workflow_dispatch',s);self.assertNotIn('schedule:',s)
            self.assertIn('concurrency:\n  group: wk09-d13-private-exclusive',s)
            if pre:
                self.assertNotIn('matlab-actions/',s);self.assertIn('timeout-minutes: 10',s)
            else:
                self.assertIn('timeout-minutes: 90',s)
                self.assertLess(s.index('WK09_group_gate.py authorize'),s.index('matlab-actions/setup-matlab'))

    def test_context_binds_probe_branch_approvals_chain_and_scenario_map(self):
        g=P.definitions()['groups']['PROBE14'];old=Path.read_text
        for preflight in (False,True):
            pre='preflight_' if preflight else ''
            with tempfile.TemporaryDirectory() as t:
                event=Path(t)/'event.json';event.write_text(json.dumps(dict(repository=dict(full_name=A.REPO,private=False),
                    head_commit=dict(id='a'*40,message=g[pre+'message']))))
                env=dict(WK09_GROUP='PROBE14',WK09_OWNER_APPROVAL=g[pre+'approval'],
                    GITHUB_EVENT_PATH=str(event),GITHUB_REPOSITORY=A.REPO,GITHUB_REF='refs/heads/codex/wk11-d14-probe',
                    GITHUB_EVENT_NAME='push',GITHUB_RUN_ATTEMPT='1',RUNNER_ENVIRONMENT='github-hosted',
                    WK09_PROTECTED_ENV_NAME='JTE_DRIVE_WRITE',GITHUB_SHA='a'*40,GITHUB_RUN_ID='123',
                    WK09_REVIEWED_SOURCE_SHA='b'*40)
                answers={('rev-parse','HEAD'):'a'*40,('rev-parse','HEAD~2'):'b'*40,
                    ('diff','--name-only','HEAD~2','HEAD~1'):g[pre+'workflow'],
                    ('diff','--name-only','HEAD~1','HEAD'):g[pre+'marker'],
                    ('ls-tree','HEAD~2','--',g[pre+'marker']):''}
                def read(path,*a,**k):return g[pre+'message'] if path.as_posix()==g[pre+'marker'] else old(path,*a,**k)
                with patch.dict(os.environ,env,clear=True),patch.object(A,'git',side_effect=lambda *x:answers[x]),patch.object(Path,'read_text',read):
                    auth=A.context(preflight);self.assertEqual(auth['runs'],['P150','P175'])
                    self.assertNotIn('scenarioSHA256',auth)
                    self.assertEqual(auth['scenarioSHA256ByCase'],{c:v[2] for c,v in P.SPECS.items()})
                    with patch.dict(os.environ,GITHUB_RUN_ATTEMPT='2'),self.assertRaises(RuntimeError):A.context(preflight)
                    with patch.dict(os.environ,WK09_OWNER_APPROVAL='APPROVE_OTHER'),self.assertRaises(RuntimeError):A.context(preflight)

    def test_stop_on_first_failure_and_job_time_reserve_no_retry(self):
        now=time.monotonic();auth=dict(group='PROBE14');rows=[];calls=[]
        with patch.dict(os.environ,WK09_GROUP='PROBE14'):
            self.assertFalse(G.sequence(auth,now,now+10000,lambda c,s,d:calls.append(c) or False,
                                        lambda c,s:rows.append((c,s))))
            self.assertEqual(calls,['P150']);self.assertEqual(rows[-1],('P175','SKIPPED_AFTER_P150_FAILURE'))
            rows=[];worker=Mock()
            self.assertFalse(G.sequence(auth,now,now+2399,worker,lambda c,s:rows.append((c,s))))
            worker.assert_not_called();self.assertEqual(rows[0],('P150','FAILED_JOB_TIME_RESERVE'))

    def test_manifests_bind_distinct_case_scenarios(self):
        with patch.dict(os.environ,WK09_GROUP='PROBE14'):
            for case in ['P150','P175']:
                s=P.scenario(case)
                with tempfile.TemporaryDirectory() as t,patch.object(A,'inputs',return_value=([],s['model_sha256'])),\
                     patch.object(A,'git',return_value=P.definitions()['vendor_commit']),patch.object(A,'code_hashes',return_value={}),\
                     patch.object(G,'sha',side_effect=lambda p:s['vendor_mat_sha256'] if p.name.endswith('_Ivst.mat') else s['model_sha256']):
                    G.prepare(dict(group='PROBE14'),case,Path(t),'t','f')
                    m=G.read(Path(t)/'WK09_MANIFEST.json')
                    self.assertEqual(m['scenario'],s);self.assertEqual(m['scenarioSHA256'],P.SPECS[case][2])

    def test_warning_counts_times_and_thresholds_null_when_never_crossed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.assertEqual(P.diagnostics(root)['warning_status'],'NOT VERIFIED')
            console=root/'WK09_CONSOLE.log'
            console.write_text("Warning: At time 196.550000, one or more assertions are triggered. ''Terminal\n"
                "voltage'' must be greater than its lower bound in ''Terminal voltage operating range [Min Max]''.\n"
                "Warning: unrelated warning\nWarning: At time 280.780000, ''Terminal voltage'' outside operating range\n")
            (root/'SUMMARY.json').write_text(json.dumps(dict(label='DERIVED_NOT_EVIDENCE',
                first_logged_Tmax_ge_305_K_s=216.19,first_logged_Tmax_ge_307_5_K_s=None)))
            d=P.diagnostics(root)
            self.assertEqual(d['terminal_voltage_warning_count'],2)
            self.assertEqual((d['terminal_voltage_warning_first_s'],d['terminal_voltage_warning_last_s']),(196.55,280.78))
            self.assertEqual(d['first_logged_Tmax_ge_305_K_s'],216.19)
            self.assertIsNone(d['first_logged_Tmax_ge_307_5_K_s'])
            console.write_text('No warnings\n');d=P.diagnostics(root)
            self.assertEqual(d['terminal_voltage_warning_count'],0);self.assertIsNone(d['terminal_voltage_warning_first_s'])
            console.write_text('Warning: Terminal voltage outside operating range without a timestamp')
            self.assertEqual(P.diagnostics(root)['warning_status'],'NOT VERIFIED')

    def test_diagnostics_are_in_receipt_and_do_not_change_pass_criteria(self):
        s=(P.ROOT/'WK09_group.py').read_text()
        self.assertIn("receipt['probeDiagnostics']=diagnostics(root)",s)
        self.assertNotIn('probeDiagnostics',s[s.index('    passed='):s.index('    # Only copy')])
        run=(P.ROOT/'BTMS_WK09_run.m').read_text()
        self.assertIn("matlab_wall_s=1185;if isfield(D,'matlab_wall_s'),matlab_wall_s=D.matlab_wall_s;end",run)
        self.assertIn("assert(toc(wall)<matlab_wall_s+15",run)
        prepare=(P.ROOT/'BTMS_WK08_prepare.m').read_text()
        for sid,k,_ in P.SPECS.values():
            self.assertIn("strcmp(s.scenario_id,'"+sid+"') && isequal(s.k,"+str(k)+")",prepare)

    def test_receipt_contains_private_diagnostics_and_rejects_wrong_scenario_binding(self):
        for bad in (False,True):
            with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,WK09_GROUP='PROBE14'):
                root=Path(t);(root/'native').mkdir()
                auth=dict(run='123',commit='a'*40,group='PROBE14');digest=P.SPECS['P150'][2]
                common=dict(auth,case='P150',scenarioSHA256=digest)
                manifest=dict(common,inputCodeSHA256={},inputs=[dict(local='input',sha256='a'*64)])
                flags=dict(common,status='NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK')
                if bad:flags['scenarioSHA256']='0'*64
                monitor=dict(common,status='PROCESS_EXIT_ZERO',returncode=0)
                for name,d in [('WK09_MANIFEST.json',manifest),('WK09_FLAGS.json',flags),('WK09_SUPERVISOR.json',monitor)]:
                    (root/name).write_text(json.dumps(d))
                for name in ['input','WK09_DEFINITION.json','WK09_PREPARED_PROOF.mat','WK09_RESOURCES.jsonl','WK09_P150.slx']:
                    (root/name).write_bytes(b'fake')
                for role in A.NATIVE:(root/'native'/('WK09_P150_'+role+'.mat')).write_bytes(b'fake')
                (root/'WK09_CONSOLE.log').write_text('Completed without warnings')
                (root/'SUMMARY.json').write_text(json.dumps(dict(label='DERIVED_NOT_EVIDENCE',
                    first_logged_Tmax_ge_305_K_s=220.0,first_logged_Tmax_ge_307_5_K_s=None)))
                delivered={}
                def upload(token,folder,path):
                    if path.name.endswith('PRIVATE_RECEIPT.json'):delivered.update(json.loads(path.read_text()))
                    return dict(integrity='FULL_REMOTE_READBACK_VERIFIED',sha256='a'*64,size_bytes=path.stat().st_size)
                with patch.object(A,'code_hashes',return_value={}),patch.object(G,'sha',return_value='a'*64),\
                     patch.object(A,'upload',side_effect=upload):
                    self.assertEqual(G.publish(auth,'P150',root,'t','f'),not bad)
                self.assertEqual(delivered['scenarioSHA256'],digest)
                self.assertEqual(delivered['probeDiagnostics']['terminal_voltage_warning_count'],0)
                self.assertEqual(delivered['probeDiagnostics']['first_logged_Tmax_ge_305_K_s'],220.0)
                self.assertFalse(delivered['rawDataPublic'])


if __name__=='__main__':unittest.main()
