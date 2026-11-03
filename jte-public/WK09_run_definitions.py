"""Offline WK09 contract resolver. No MATLAB, Drive or workflow launch capability."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def need(value, code):
    if not value:
        raise RuntimeError(code)


def definitions():
    doc = json.loads((ROOT / 'WK09_runs.json').read_text())
    runs = doc['runs']
    need([r['id'] for r in runs] == [f'R{i}' for i in range(2, 14)], 'WK09_RUN_MATRIX')
    for key in ('marker', 'trigger_message', 'intent', 'receipt', 'approval'):
        need(len({r[key] for r in runs}) == 12, 'WK09_UNIQUE_IDENTITIES')
    for r in runs:
        need(r['enabled'] is False and r['owner_approval_required'] is True, 'WK09_SOURCE_ONLY')
        need(r['stop_s'] == 2400 and r['solver'] == 'ode23t' and r['MaxStep_s'] == .05, 'WK09_METHOD')
        need(r['Ts_s'] == (.005 if r['id'] == 'R3' else .01), 'WK09_SAMPLE_TIME')
        need(r['RelTol'] == r['AbsTol'] == ('1e-4' if r['id'] == 'R4' else '1e-3'), 'WK09_TOLERANCES')
    return doc


def resolve(run_id, frozen_selector=None):
    doc = definitions()
    run = next(r.copy() for r in doc['runs'] if r['id'] == run_id)
    path = ROOT / 'WK08_sparse_sets.csv'
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    S = [int(r['channel']) for r in rows if int(r['sensor_count']) == run['sensors']]
    need(len(S) == run['sensors'] and S == sorted(set(S)), 'WK09_FIXED_SUBSET')
    run['subset'] = S
    run['subset_csv_SHA256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    if run['rank_source']:
        if frozen_selector is None:
            run['channel'] = None
            run['resolution'] = 'BLOCKED_PENDING_ACCEPTED_R2_V02_SELECTOR'
            return run
        # This function consumes an independently frozen v02 result. It never
        # estimates ranks from a MAX statistic or silently picks a fallback.
        a = json.loads(Path(frozen_selector).read_text())
        need(a['version'] == 'JTE-050 v02' and a['source_run'] == 'R2', 'WK09_SELECTOR_VERSION')
        need(a['window_s'] == [1800, 2400] and a['statistic'] == 'time-weighted mean', 'WK09_SELECTOR_STATISTIC')
        need(a['accepted_baseline_receipt_SHA256'] and len(a['accepted_baseline_receipt_SHA256']) == 64, 'WK09_SELECTOR_RECEIPT')
        order = a['ranking_descending']
        need(len(order) == 312 and sorted(order) == list(range(1, 313)), 'WK09_SELECTOR_ORDER')
        rule = run['channel_rule']
        run['channel'] = order[155] if rule == 'rank_156' else next(j for j in order if j in S)
        run['selector_SHA256'] = hashlib.sha256(Path(frozen_selector).read_bytes()).hexdigest()
        run['selector_receipt_SHA256'] = a['accepted_baseline_receipt_SHA256']
    else:
        run['channel'] = S[0]  # also required for b=0 C16/C8 by B1 guard
    need(run['channel'] in S, 'WK09_BIAS_NOT_SENSED')
    run['resolution'] = 'SOURCE_CONTRACT_ONLY_NOT_RUN_AUTHORIZATION'
    return run


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', choices=[f'R{i}' for i in range(2, 14)])
    p.add_argument('--selector')
    args = p.parse_args()
    print(json.dumps(resolve(args.run, args.selector), indent=2))
