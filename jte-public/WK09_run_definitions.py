"""Immutable D13 definitions/selector. No MATLAB, Drive or run authorization."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
H_SEL = 'cbaf7ede34dee318b1ab3a73cfbc53dbde44bda6700133c864c3dfc8ae148233'
H_R2 = '7074b363ee0c97b52f5f8d80a4148852c54432b417b8e2dc73024b765b9a0612'
H_PRED = '50f97a1226858944b5cb0088f561959334b59c5efcc51d36d99850555bf2d5a5'
H_SCENARIO = '372683adc8c45d6c9bc84213619916cf9cee18d03471b9ed4ae7fab3c0bc9f7b'
ORDERS = {'CONTROLS': ['R3','R4','R5','R12','R13'],
          'CASES': ['R6','R7','R8','R9','R10','R11'], 'R14': ['R14']}


def need(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
    return h.hexdigest()


def selector():
    path = ROOT / 'WK09_selector_D13_200_340.json'
    need(sha(path) == H_SEL, 'WK09_SELECTOR_SHA')
    d = json.loads(path.read_text(encoding='utf-8'))
    need(d['accepted_baseline_receipt_SHA256'] == H_R2 and d['frozen_predictions_SHA256'] == H_PRED
         and d['window_s'] == [200,340] and d['version'] == 'JTE-050 v02 (D13 window)'
         and d['statistic'] == 'time-weighted mean', 'WK09_SELECTOR_PROVENANCE')
    need(sorted(d['ranking_descending']) == list(range(1,313)), 'WK09_SELECTOR_PERMUTATION')
    return d


def definitions():
    d = json.loads((ROOT / 'WK09_runs.json').read_text(encoding='utf-8'))
    need(d['source_only'] is True and d['branch'] == 'codex/wk09-d13-340s', 'WK09_SOURCE_ONLY')
    need(d['baseline']['scheduled'] is False and d['baseline']['receipt_sha256'] == H_R2,
         'WK09_EXTERNAL_R2_ONLY')
    need(d['baseline']['id']=='R2' and d['baseline']['github_run']=='41659796627'
         and d['baseline']['receipt_name']=='WK10_D13_REF_K2_T340_A_41659796627_PRIVATE_RECEIPT_20261103.json',
         'WK09_EXTERNAL_R2_ONLY')
    need((d['selector_sha256'], d['scenario_sha256'], d['predictions_sha256']) ==
         (H_SEL, H_SCENARIO, H_PRED), 'WK09_DIGESTS')
    need(sha(ROOT / 'WK10_scenario.json') == H_SCENARIO, 'WK09_SCENARIO_SHA')
    selector()
    need([r['id'] for r in d['runs']] == [f'R{i}' for i in range(3,15)], 'WK09_RUN_MATRIX')
    for r in d['runs']:
        i = int(r['id'][1:])
        expected = dict(start_s=0, stop_s=340, k=2, tau_s=.001, ambient_K=300,
                        solver='ode23t', MaxStep_s=.05,
                        Ts_s=.005 if i == 3 else .01,
                        RelTol='1e-4' if i == 4 else '1e-3',
                        AbsTol='1e-4' if i == 4 else '1e-3',
                        sensors=16 if i in (8,9,12) else 8 if i in (10,13) else 312,
                        bias_K=-2 if i in (6,7,8,14) else -4 if i in (9,10) else 2 if i == 11 else 0,
                        measurement_pipeline='identity_bypass' if i in (3,4) else 'active',
                        optional=i == 14,
                        channel_rule='top_three' if i == 14 else 'rank_1' if i in (6,11) else
                        'rank_156' if i == 7 else 'hottest_in_subset' if i in (8,9,10) else 'first_sensed')
        need(all(r[k] == v for k,v in expected.items()), 'WK09_CASE_CONTRACT')
    for key, order in ORDERS.items():
        g = d['groups'][key]
        need(g['runs'] == order and g['identity'] == 'WK09_D13_'+key+'_A'
             and g['timeout_minutes'] == {'CONTROLS':210,'CASES':240,'R14':35}[key], 'WK09_SEALED_GROUP')
        identity='WK09_D13_'+key+'_A';pf='WK09_D13_'+key+'_PREFLIGHT_A'
        expected=dict(optional=key=='R14',message=identity+'_ONE_SHOT',
            marker='jte-public/'+identity+'_TRIGGER.txt',approval='APPROVE_'+identity+'_ONCE_AFTER_CLAUDE_GO',
            intent=identity+('_ATTEMPT_INTENT.json' if key=='R14' else '_JOB_INTENT.json'),
            workflow='.github/workflows/wk09-d13-'+key.lower()+'-one-shot.yml',
            preflight_message=pf+'_CHECK',preflight_marker='jte-public/'+pf+'_TRIGGER.txt',
            preflight_approval='APPROVE_'+pf+'_ONCE_AFTER_CLAUDE_GO',
            preflight_workflow='.github/workflows/wk09-d13-'+key.lower()+'-preflight.yml')
        need(all(g[k]==v for k,v in expected.items()),'WK09_SEALED_GROUP')
    return d


def resolve(run_id):
    import csv
    d = definitions()
    need(run_id in {r['id'] for r in d['runs']}, 'WK09_RUN_NOT_SCHEDULED')
    r = next(dict(x) for x in d['runs'] if x['id'] == run_id)
    with (ROOT / 'WK08_sparse_sets.csv').open() as f:
        r['subset'] = [int(x['channel']) for x in csv.DictReader(f) if int(x['sensor_count']) == r['sensors']]
    order = selector()['ranking_descending']
    rule = r['channel_rule']
    J = order[:3] if rule == 'top_three' else [order[155]] if rule == 'rank_156' else [
        next(j for j in order if j in r['subset'])] if rule in ('rank_1','hottest_in_subset') else [r['subset'][0]]
    r.update(bias_channels=sorted(J), selector_sha256=H_SEL, scenario_sha256=H_SCENARIO,
             predictions_sha256=H_PRED, baseline_receipt_sha256=H_R2,
             subset_sha256=sha(ROOT / 'WK08_sparse_sets.csv'))
    need(all(j in r['subset'] for j in J), 'WK09_BIAS_NOT_SENSED')
    return r
