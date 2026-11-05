"""Sealed smaller-gain probes; D13 definitions and scientific gates stay frozen."""
import json
import math
import re

import WK09_run_definitions as legacy

ROOT = legacy.ROOT
REGISTRY = 'WK10_D14_probe.json'
ORDERS = {'PROBE14': ['P150', 'P175']}
SPECS = {
    'P150': ('D14_K150_T340_V1', 1.5, 'c7c459f95cebd198ee58c73a34d53f233f95984310920baf99244ab6972c281a'),
    'P175': ('D14_K175_T340_V1', 1.75, '36d846335c1e8143437bf87a64af0d8a67f6444e04bbb372c8ac74d099358ec4'),
}


def definitions():
    old = legacy.definitions()
    legacy.need(legacy.sha(ROOT/'WK09_runs.json') ==
        '4308c9ed977a0a974c545449ea6a321bb85e656099dab48d9f7090dbf9470936', 'WK09_D14_D13_BYTES')
    d = json.loads((ROOT/REGISTRY).read_text(encoding='utf-8'))
    identity = 'WK10_D14_PROBE_A'; pf = 'WK10_D14_PROBE_PREFLIGHT_A'
    expected = dict(identity=identity, runs=ORDERS['PROBE14'], timeout_minutes=90, optional=False,
        workflow='.github/workflows/wk10-d14-probe-one-shot.yml', marker='jte-public/'+identity+'_TRIGGER.txt',
        message=identity+'_ONE_SHOT', approval='APPROVE_'+identity+'_ONCE_AFTER_CLAUDE_GO',
        intent=identity+'_JOB_INTENT.json', preflight_workflow='.github/workflows/wk10-d14-probe-preflight.yml',
        preflight_marker='jte-public/'+pf+'_TRIGGER.txt', preflight_message=pf+'_CHECK',
        preflight_approval='APPROVE_'+pf+'_ONCE_AFTER_CLAUDE_GO', matlab_wall_s=1185, case_seconds=2100)
    legacy.need(d['groups'] == {'PROBE14': expected} and d['source_only'] is True and
        d['branch'] == 'codex/wk11-d14-probe' and d['schema'] == 'WK10_D14_PROBE_SOURCE_ONLY_V1',
        'WK09_D14_SEALED_GROUP')
    for key in old.keys()-{'schema','branch','groups','runs','controls_acceptance'}:
        legacy.need(d[key] == old[key], 'WK09_D14_PROVENANCE')
    legacy.need([r['id'] for r in d['runs']] == ORDERS['PROBE14'], 'WK09_D14_ORDER')
    template = next(r for r in old['runs'] if r['id'] == 'R5')
    for row in d['runs']:
        sid, k, digest = SPECS[row['id']]
        expected = dict(template, id=row['id'], k=k, mode='D13_REF', scenario_file='WK10_'+sid+'.json',
                        scenario_sha256=digest, matlab_wall_s=1185, case_seconds=2100)
        legacy.need(row == expected, 'WK09_D14_CASE_CONTRACT')
        scenario(row['id'])
    return d


def scenario(case):
    legacy.need(case in SPECS, 'WK09_D14_CASE_DENIED')
    sid, k, digest = SPECS[case]
    path = ROOT/('WK10_'+sid+'.json')
    legacy.need(legacy.sha(ROOT/'WK10_scenario.json') == legacy.H_SCENARIO and
                legacy.sha(path) == digest, 'WK09_D14_SCENARIO_SHA')
    original = json.loads((ROOT/'WK10_scenario.json').read_text())
    value = json.loads(path.read_text())
    legacy.need(value == dict(original, scenario_id=sid, k=k), 'WK09_D14_SCENARIO')
    return value


def resolve(case, group=None):
    d = definitions()
    legacy.need(group in (None, 'PROBE14') and case in SPECS, 'WK09_CASE_OUTSIDE_ALLOWLIST')
    r = dict(next(r for r in d['runs'] if r['id'] == case))
    old = legacy.resolve('R5')
    for key in ('subset','bias_channels','selector_sha256','predictions_sha256',
                'baseline_receipt_sha256','subset_sha256'):
        r[key] = old[key]
    return r


def diagnostics(root):
    """Private receipt diagnostics only: no suitability/PASS decision or console text."""
    result = dict(label='DERIVED_NOT_EVIDENCE', terminal_voltage_warning_count=None,
        terminal_voltage_warning_first_s=None, terminal_voltage_warning_last_s=None,
        first_logged_Tmax_ge_305_K_s=None, first_logged_Tmax_ge_307_5_K_s=None,
        warning_status='NOT VERIFIED', threshold_status='NOT VERIFIED')
    console = root/'WK09_CONSOLE.log'
    if console.is_file() and not console.is_symlink():
        text = console.read_text(encoding='utf-8', errors='replace')
        warnings = re.split(r'Warning:', text)[1:]
        times = []; valid = True
        for warning in warnings:
            if not re.search(r'Terminal\s+voltage.*?operating\s+range', warning, re.I|re.S):
                continue
            stamp = re.match(r'\s*At time\s+([0-9.eE+-]+)\s*,', warning)
            t = float(stamp[1]) if stamp else float('nan')
            valid = valid and math.isfinite(t) and 0 <= t <= 340
            times.append(t)
        if valid:
            result.update(terminal_voltage_warning_count=len(times),
                terminal_voltage_warning_first_s=min(times) if times else None,
                terminal_voltage_warning_last_s=max(times) if times else None,
                warning_status='CONSOLE_WARNING_RECORDS')
    summary = root/'SUMMARY.json'
    if summary.is_file() and not summary.is_symlink():
        d = json.loads(summary.read_text())
        keys = ('first_logged_Tmax_ge_305_K_s','first_logged_Tmax_ge_307_5_K_s')
        if d.get('label') == 'DERIVED_NOT_EVIDENCE' and all(k in d and
            (d[k] is None or type(d[k]) in (float,int) and math.isfinite(d[k]) and 0 <= d[k] <= 340)
            for k in keys):
            result.update({k:d[k] for k in keys}); result['threshold_status']='MATLAB_LOGGED_SAMPLES'
    return result
