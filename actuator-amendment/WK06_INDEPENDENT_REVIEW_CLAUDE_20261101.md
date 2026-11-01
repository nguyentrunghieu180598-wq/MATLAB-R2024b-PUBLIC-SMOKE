# WK06 independent source/security review of PR #70 (head 088935b)

Reviewer: Claude (Anthropic), independent of the Codex author. Date: 01 Nov 2026 (ICT).
Scope: the 9 files changed from `codex/wk05-fixture-evidence-gates` (b508de5) to `codex/wk06-nonbattery-only-20261101` (088935b).
Method: full diff read, `py_compile` of the three Python files, YAML parse of both workflows, and a local git simulation of the S→E→T trigger chain. No MATLAB, no Actions run, no Drive access, no secrets read. `MATLAB_CALLS=0`, `ONE_SHOT_CONSUMED=false`, G-M3/G5 unchanged.

**Verdict: `WK06_REVIEW_NO_GO_AS_DELIVERED` → `GO_AFTER_PATCH_B1` (patch below).**

## B1 — BLOCKING: reviewed-parent pin can never be satisfied
The documented enable procedure is: set `WK06_REVIEWED_PARENT_SHA` in the workflow (commit E), then push the marker commit T. The gate checks `git rev-parse HEAD^ == WK06_REVIEWED_PARENT_SHA`. For T, `HEAD^` is E itself, and E cannot contain its own SHA. The check therefore fails on every attempt.

Local simulation: old gate → `FAIL (HEAD^ is the enable commit, not the reviewed commit)`.

Impact: non-destructive (fails in the first step, before `prepare`, so no Drive intent is reserved and the 1/1 allowance is not consumed). It would however burn a run, and the obvious hotfix (relaxing the pin) would remove the protection.

Fix (applied in this branch, workflow file only):
- Rename to `WK06_REVIEWED_SOURCE_SHA` = the reviewed source commit S.
- `fetch-depth: 3`. Require `HEAD~2 == S`, `diff(HEAD~2, HEAD~1) == only .github/workflows/wk06-matlab-one-shot.yml`, `diff(HEAD~1, HEAD) == only jte-public/WK06_MATLAB_TRIGGER.txt`.
- Simulation: new gate PASS on S→E→T; correctly REJECTS an E that also edits a source file.

## R1 — RECOMMENDED (applied): pin the update explicitly
`setup-matlab` with `release: R2024b` installs the **latest** R2024b update ([setup-matlab README](https://github.com/matlab-actions/setup-matlab)). The entry point asserts exactly `24.2.0.3361896 (R2024b) Update 10`. Prior runs (e.g. 40735694599, 40701917441) did receive this build, so this has not failed yet, but any new R2024b update would turn the single allowed attempt into a `WK06:BuildMismatch`. Changed to `release: R2024bU10`, which the action documents as the pinned-update syntax. The exact-build assertion is kept.

## M1 — minor (not patched): intent file is re-uploaded by `publish`
`reserve_one_shot` writes `WK06_MATLAB_ATTEMPT_INTENT_20261101.json` into `actuator-review-private/`; `publish` uploads every file in that folder, producing a second verified intent copy. Harmless for the guard (any copy blocks a repeat) but confusing for the evidence inventory. Optional: skip that filename in `publish`.

## M2 — minor (not patched): entry reads the gate file outside `try`
`WK06_oneShotEntry` decodes `WK04_PREPARE_GATE.json` before `try`. If that file were unreadable, no `WK04_FLAGS.json` would be written. In practice `prepare` writes it in the previous step and the job stops if `prepare` fails, so the path is unreachable. Note only.

## Checked and found correct
- Neutral preflight: context guard (repo/branch/event/attempt/hosted/env/message/SHA), secrets never printed, owner-only ACL on folder and receipt, one-receipt guard, full remote-byte SHA readback. Matches run 41314660334 PASS.
- `prepare`: requires the verified neutral receipt (owner-only, `state=VERIFIED`, size bound, SHA re-read), quota ≥ 512 MiB, then a durable one-shot intent before any MATLAB step. `ROOT.mkdir(exist_ok=False)` moved into `reserve_one_shot` without a second `mkdir`.
- `publish` runs under `if: always()`, keeps MATLAB status as written, binds run/commit, re-hashes inputs, refuses combined qualification on missing payload; `G5`/physical flags hard-false.
- Schema whitelist change is one added label only.
- No physical pack script, JTE116 workflow, B0L/C0/C1, 340 s or 2400 s path is reachable. `if: ${{ false }}` is still in place.

## Remaining owner/Work steps (unchanged in spirit)
1. Merge/push this patch to `codex/wk06-nonbattery-only-20261101` (commit S').
2. Enable commit E: change only the workflow file: predicate → exact branch/message/run-attempt; `WK06_REVIEWED_SOURCE_SHA` = S'.
3. Trigger commit T: only `jte-public/WK06_MATLAB_TRIGGER.txt`, message `WK06_NONBATTERY_ONE_SHOT_20261101`.

A toy PASS remains API feasibility only. It does not reopen G5 (Issue #61) or authorise any physical run.
