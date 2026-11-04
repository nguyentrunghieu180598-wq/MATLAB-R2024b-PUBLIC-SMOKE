"""Offline byte/contract tests; no scientific data, MATLAB or network."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import WK09_run_definitions as D


class DefinitionTests(unittest.TestCase):
    def test_controls_order_and_acceptance_subset_unset(self):
        d=D.definitions();g=d['groups']['CONTROLS'];c=d['controls_acceptance']
        self.assertEqual(g['runs'],['R5','R12','R13','R3','R4'])
        self.assertEqual(D.ORDERS['CONTROLS'],g['runs']);self.assertEqual(g['timeout_minutes'],210)
        self.assertEqual(c['required_runs'],['R5','R12','R13'])
        self.assertEqual(list(c['criteria']),c['required_runs'])
        self.assertEqual(c['sha256'],'0'*64)
        self.assertEqual(c['file'],'jte-public/WK09_CONTROLS_ACCEPTED.json')
        self.assertFalse((D.ROOT.parent/c['file']).exists())

    def test_exact_selector_bytes_and_permutation(self):
        p=D.ROOT/'WK09_selector_D13_200_340.json';b=p.read_bytes()
        self.assertEqual(len(b),2625);self.assertFalse(b.endswith(b'\n'))
        self.assertEqual(D.sha(p),D.H_SEL)
        a=D.selector();self.assertEqual(sorted(a['ranking_descending']),list(range(1,313)))
        self.assertEqual(a['ranking_descending'][0],202);self.assertEqual(a['ranking_descending'][155],288)
        self.assertEqual(a['window_s'],[200,340]);self.assertNotIn('temperatures',a)

    def test_all_frozen_resolved_cases(self):
        expected={'R6':[202],'R7':[288],'R8':[168],'R9':[168],'R10':[180],'R11':[202],'R14':[202,203,204]}
        for row in D.definitions()['runs']:
            with self.subTest(case=row['id']):
                r=D.resolve(row['id']);i=int(r['id'][1:])
                self.assertEqual((r['k'],r['start_s'],r['stop_s']),(2,0,340))
                self.assertEqual(r['Ts_s'],.005 if i==3 else .01)
                self.assertEqual((r['RelTol'],r['AbsTol']),('1e-4','1e-4') if i==4 else ('1e-3','1e-3'))
                self.assertEqual(r['measurement_pipeline'],'identity_bypass' if i in (3,4) else 'active')
                self.assertTrue(set(r['bias_channels']) <= set(r['subset']))
                self.assertEqual(len(r['subset']),r['sensors'])
                if r['id'] in expected:self.assertEqual(r['bias_channels'],expected[r['id']])
        with self.assertRaisesRegex(RuntimeError,'WK09_RUN_NOT_SCHEDULED'):D.resolve('R2')

    def test_byte_change_fails_before_selection(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/'WK09_selector_D13_200_340.json').write_bytes((D.ROOT/'WK09_selector_D13_200_340.json').read_bytes()+b'\n')
            with patch.object(D,'ROOT',root),self.assertRaisesRegex(RuntimeError,'WK09_SELECTOR_SHA'):D.selector()

    def test_registry_mutations_fail_closed(self):
        original=D.definitions()
        mutations=[lambda d:d['groups']['CASES']['runs'].append('R14'),
                   lambda d:d['baseline'].update(scheduled=True),
                   lambda d:d['runs'][2].update(measurement_pipeline='identity_bypass'),
                   lambda d:d['runs'][3].update(Ts_s=.005),
                   lambda d:d['runs'][3].update(RelTol='1e-4')]
        old=Path.read_text
        for mutate in mutations:
            d=copy.deepcopy(original);mutate(d)
            def read(p,*a,**k):return json.dumps(d) if p.name=='WK09_runs.json' else old(p,*a,**k)
            with patch.object(Path,'read_text',read),self.assertRaises(RuntimeError):D.definitions()

    def test_only_declared_parameter_writes(self):
        s=(D.ROOT/'BTMS_WK09_prepare.m').read_text()
        actuator=s[s.index("if strcmp(D.id,'R3')"):s.index("if strcmp(D.id,'R4')")]
        self.assertIn("set_param(act,'A'",actuator);self.assertIn("set_param(hold,'SampleTime'",actuator)
        self.assertEqual(s.count("set_param(act,"),1);self.assertEqual(s.count("set_param(hold,"),1)
        self.assertEqual(s.count("set_param(m,'RelTol'"),1)
        self.assertIn("if ~strcmp(D.id,'R3'),assert(isequaln(finalActuator,archivedActuator)",s)
        self.assertIn("if ~strcmp(D.id,'R4'),assert(isequaln(finalTolerances,archivedTolerances)",s)
        self.assertIn('BTMS_WK08_prepare(source,target,privateDir,sourceSHA,340,S)',s)

    def test_vector_guard_before_first_graph_edit_and_default_bypass(self):
        s=(D.ROOT/'BTMS_WK08_inject.m').read_text()
        self.assertLess(s.index('all(ismember(j,S))'),s.index('add_block('))
        self.assertIn('if nargin<5,forcePipeline=false;end',s)
        self.assertIn('b==0 && isequal(S,1:312) && ~forcePipeline',s)
        self.assertIn('mat2str(j),mat2str(j),b,mat2str(S)',s)

    def test_six_disabled_workflows_and_independent_identities(self):
        repo=D.ROOT.parent;d=D.definitions();seen=set()
        for key,g in d['groups'].items():
            self.assertEqual(g['runs'],D.ORDERS[key])
            for pre in ('','preflight_'):
                s=(repo/g[pre+'workflow']).read_text()
                self.assertIn('if: ${{ false }}',s)
                self.assertIn("WK09_REVIEWED_SOURCE_SHA: '"+'0'*40+"'",s)
                self.assertIn(g[pre+'marker'],s);self.assertFalse((repo/g[pre+'marker']).exists())
                self.assertNotIn(g[pre+'approval'],seen);seen.add(g[pre+'approval'])
                self.assertNotIn('workflow_dispatch',s);self.assertNotIn('schedule:',s)
                if pre:
                    self.assertIn('timeout-minutes: 10',s)
                    self.assertNotIn('matlab-actions/',s);self.assertNotIn('vendor-pack',s)
                    self.assertIn('WK09_group_gate.py check',s)
                else:
                    self.assertIn('timeout-minutes: '+str(g['timeout_minutes']),s)
                    self.assertIn('release: R2024bU10',s)
                    self.assertLess(s.index('WK09_group_gate.py authorize'),s.index('matlab-actions/setup-matlab@v3'))
                    self.assertLess(s.index('matlab-actions/run-command@v3'),s.index('WK09_group.py run'))
                    self.assertIn('persist-credentials: false',s)


if __name__=='__main__':unittest.main()
