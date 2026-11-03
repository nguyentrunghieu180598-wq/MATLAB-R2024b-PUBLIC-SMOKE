"""Offline definition/authorization tests; no MATLAB or network."""
import unittest
import json
import tempfile
import re
import subprocess
import sys
from pathlib import Path
from WK09_run_definitions import definitions, resolve
from WK09_definition_gate import validate


class Definitions(unittest.TestCase):
    def test_matrix(self):
        runs = {r['id']: r for r in definitions()['runs']}
        self.assertEqual([runs[f'R{i}']['bias_K'] for i in range(6,12)], [-2,-2,-2,-4,-4,2])
        self.assertEqual([runs[f'R{i}']['sensors'] for i in range(6,12)], [312,312,16,16,8,312])
        self.assertEqual(runs['R4']['RelTol'], '1e-4')
        self.assertEqual(runs['R3']['Ts_s'], .005)

    def test_controls_and_guard(self):
        for name, count in [('R5',312),('R12',16),('R13',8)]:
            r = resolve(name)
            self.assertEqual(r['bias_K'], 0)
            self.assertEqual(r['measurement_pipeline'], 'active')
            self.assertEqual(len(r['subset']), count)
            self.assertEqual(r['channel'], r['subset'][0])

    def test_unavailable_ranking_blocks_fault_cases(self):
        for i in range(6,12):
            r = resolve(f'R{i}')
            self.assertIsNone(r['channel'])
            self.assertTrue(r['resolution'].startswith('BLOCKED'))

    def test_frozen_selector_rules(self):
        a={'version':'JTE-050 v02','source_run':'R2','window_s':[1800,2400],
           'statistic':'time-weighted mean','accepted_baseline_receipt_SHA256':'a'*64,
           'ranking_descending':list(range(312,0,-1))}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'synthetic.json';p.write_text(json.dumps(a))
            self.assertEqual(resolve('R6',p)['channel'],312)
            self.assertEqual(resolve('R7',p)['channel'],157)
            r=resolve('R8',p);self.assertEqual(r['channel'],max(r['subset']))
            a['version']='v01 MAX';p.write_text(json.dumps(a))
            with self.assertRaises(RuntimeError):resolve('R6',p)

    def test_dependencies(self):
        runs={r['id']:r for r in definitions()['runs']}
        for name, dep in [('R6','R5_ACCEPTED'),('R8','R12_ACCEPTED'),('R10','R13_ACCEPTED')]:
            self.assertIn(dep,runs[name]['requires'])
            self.assertIn('PREDICTIONS_FROZEN',runs[name]['requires'])

    def test_auth_rejection(self):
        r=definitions()['runs'][-1]
        e={'head_commit':{'id':'test','message':r['trigger_message']}}
        env={'GITHUB_REPOSITORY':'nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE',
             'GITHUB_REF':'refs/heads/codex/wk09-runs','GITHUB_EVENT_NAME':'push',
             'GITHUB_RUN_ATTEMPT':'1','RUNNER_ENVIRONMENT':'github-hosted',
             'GITHUB_SHA':'test','WK09_OWNER_APPROVAL':r['approval']}
        self.assertEqual(validate(e,env,r['marker'],r['trigger_message']),'R13')
        for key,value in [('GITHUB_RUN_ATTEMPT','2'),('WK09_OWNER_APPROVAL',''),('GITHUB_REF','refs/heads/main')]:
            bad=dict(env);bad[key]=value
            with self.assertRaises(RuntimeError):validate(e,bad,r['marker'],r['trigger_message'])


class ParameterSourceContracts(unittest.TestCase):
    def test_only_r3_actuator_and_r4_tolerance_writes_for_every_run(self):
        source = (Path(__file__).parent / "BTMS_WK09_prepare.m").read_text()
        r3 = re.search(r"if strcmp\(D.id,'R3'\)\n([\s\S]*?)\nelse\n([\s\S]*?)\nend", source)
        r4 = re.search(r"if strcmp\(D.id,'R4'\)\n([\s\S]*?)\nelse\n([\s\S]*?)\nend", source)
        self.assertIsNotNone(r3)
        self.assertIsNotNone(r4)
        self.assertIn("assert(isequaln(currentActuator,archivedActuator)", r3.group(2))
        self.assertIn("assert(isequaln(currentTolerances,archivedTolerances)", r4.group(2))
        calls = list(re.finditer(r"set_param\((act|hold|m),([\s\S]*?)\);", source))
        for run in definitions()["runs"]:
            writes = set()
            for call in calls:
                keys = set(re.findall(r"'(A|B|SampleTime|RelTol|AbsTol)'", call.group(2)))
                if not keys:
                    continue
                inside_r3 = r3.start(1) <= call.start() < r3.end(1)
                inside_r4 = r4.start(1) <= call.start() < r4.end(1)
                executes = ((inside_r3 and run["id"] == "R3") or
                            (inside_r4 and run["id"] == "R4") or
                            (not inside_r3 and not inside_r4))
                if executes:
                    writes.update((call.group(1), k) for k in keys)
            expected = ({("act", "A"), ("act", "B"), ("act", "SampleTime"),
                         ("hold", "SampleTime")} if run["id"] == "R3" else
                        {("m", "RelTol"), ("m", "AbsTol")} if run["id"] == "R4" else set())
            with self.subTest(run=run["id"]):
                self.assertEqual(writes, expected)
                if run["id"] != "R3":
                    self.assertEqual(run["Ts_s"], .01)
                if run["id"] != "R4":
                    self.assertEqual((run["RelTol"], run["AbsTol"]), ("1e-3", "1e-3"))

    def test_exact_archived_values_are_checked_and_before_after_recorded(self):
        source = (Path(__file__).parent / "BTMS_WK09_prepare.m").read_text()
        self.assertLess(source.index("archivedActuator=actuatorParameters(act,hold)"),
                        source.index("p.injection=BTMS_WK08_inject"))
        self.assertIn("str2double(archivedTolerances.RelTol)==1e-3", source)
        self.assertIn("str2double(archivedTolerances.AbsTol)==1e-3", source)
        for name in ("A", "B", "SampleTime"):
            self.assertIn("get_param(act,'" + name + "')", source)
        self.assertIn("get_param(hold,'SampleTime')", source)
        for name in ("actuatorBefore", "actuatorAfter", "tolerancesBefore", "tolerancesAfter"):
            self.assertIn("'" + name + "'", source)
        self.assertRegex(source, r"if ~strcmp\(D.id,'R3'\)\s+assert\(isequaln\(finalActuator,archivedActuator\)")
        self.assertRegex(source, r"if ~strcmp\(D.id,'R4'\)\s+assert\(isequaln\(finalTolerances,archivedTolerances\)")


class ReviewCorrections(unittest.TestCase):
    def test_registry_pins_final_wk08_and_definition_workflow_has_no_drive_env(self):
        self.assertEqual(definitions()["reviewed_WK08_head"],
                         "dd282cb2bddf1c7252d197c927965cbac545fb46")
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/wk09-run-definitions.yml").read_text()
        self.assertIn("if: " + "$" + "{{ false }}", workflow)
        self.assertNotIn("environment:", workflow)
        self.assertEqual(list((root / "jte-public").glob("WK09_R*_TRIGGER.txt")), [])
        doc = (root / "actuator-amendment/WK09_RUN_DEFINITIONS.md").read_text()
        self.assertIn("2700s", doc)
        self.assertIn("21600s", doc)

    def test_authorization_and_selector_stay_fail_closed_under_optimization(self):
        code = """
import json, tempfile
from pathlib import Path
from WK09_definition_gate import validate
from WK09_run_definitions import definitions, resolve
r=definitions()['runs'][-1]
event={'head_commit': {'id':'test', 'message':r['trigger_message']}}
env={'GITHUB_REPOSITORY':'nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE',
 'GITHUB_REF':'refs/heads/codex/wk09-runs','GITHUB_EVENT_NAME':'push',
 'GITHUB_RUN_ATTEMPT':'2','RUNNER_ENVIRONMENT':'github-hosted',
 'GITHUB_SHA':'test','WK09_OWNER_APPROVAL':r['approval']}
try:
 validate(event,env,r['marker'],r['trigger_message'])
except RuntimeError:
 pass
else:
 raise SystemExit(1)
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'selector.json'
 p.write_text(json.dumps({'version':'v01 MAX','source_run':'R2'}))
 try:
  resolve('R6',p)
 except RuntimeError:
  pass
 else:
  raise SystemExit(2)
"""
        result = subprocess.run([sys.executable, "-O", "-c", code],
                                cwd=Path(__file__).parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
