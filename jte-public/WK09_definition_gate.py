"""Fail-closed definition authorization; no pack/Drive execution capabilities."""
import json
import os
from pathlib import Path
import subprocess
from WK09_run_definitions import definitions, need


def validate(event, env, changed, marker_text):
    need(env['GITHUB_REPOSITORY'] == 'nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE', 'WK09_REPOSITORY')
    need(env['GITHUB_REF'] == 'refs/heads/codex/wk09-runs', 'WK09_BRANCH')
    need(env['GITHUB_EVENT_NAME'] == 'push' and env['GITHUB_RUN_ATTEMPT'] == '1', 'WK09_ATTEMPT')
    need(env['RUNNER_ENVIRONMENT'] == 'github-hosted', 'WK09_RUNNER')
    need(event['head_commit']['id'] == env['GITHUB_SHA'], 'WK09_COMMIT_BINDING')
    matches = [r for r in definitions()['runs'] if r['marker'] == changed]
    need(len(matches) == 1, 'WK09_MARKER')
    r = matches[0]
    need(event['head_commit']['message'] == r['trigger_message'], 'WK09_MESSAGE')
    need(marker_text.strip() == r['trigger_message'], 'WK09_MARKER_TEXT')
    need(env['WK09_OWNER_APPROVAL'] == r['approval'], 'WK09_APPROVAL')
    return r['id']


if __name__ == '__main__':
    try:
        changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], text=True).strip()
        # Resolve path only after allowlisting against the source registry.
        need(changed in {r['marker'] for r in definitions()['runs']}, 'WK09_MARKER')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        run_id = validate(event, os.environ, changed, Path(changed).read_text())
        print(run_id + '_DEFINITION_VALIDATED_NO_RUN_AUTHORIZATION')
    except Exception:
        raise SystemExit('WK09_DEFINITION_GATE_REJECTED')
