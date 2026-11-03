# MATLAB-R2024b-PUBLIC-SMOKE

## WK08 source delivery — R1 and measurement injection

Scope: hub Issue #1; context: public Issue #73. Base: `f7ba843e0101eb8bf94d5f4ec217fea45d4b1ff7`
on `codex/wk06-nonbattery-only-20261101`. Author: Codex. Independent reviewer: Claude.
**SOURCE ONLY — MATLAB/CI not executed; no workflow enabled or triggered.**

Design handoff: `WK08_PHYSICAL_DESIGN_READY_FOR_OWNER_REVIEW`.
This is an author handoff label, not an independent GO, runtime qualification, physical result or G5 PASS.
See [run sheet](actuator-amendment/WK08_R1_DESIGN.md) for provenance, limits and pending gates.

### Every changed file

| File | Purpose |
| --- | --- |
| `README.md` | Delivery inventory and author checklist |
| `actuator-amendment/WK08_R1_DESIGN.md` | R1 contract, geometric rule, t0 decision, resource estimates, owner handoff |
| `jte-public/BTMS_WK08_structFingerprint.m` | WK07 fingerprint extended to physical connectivity, IC workspace, scripts and comments |
| `jte-public/BTMS_WK08_inject.m` | Neutral literal no-op, or single-channel additive bias then committed subset before min-max T |
| `jte-public/BTMS_WK08_sparseSets.m` | Load and validate fixed channel indices |
| `jte-public/WK08_sparse_sets.csv` | 312/16/8 sets, module sizes and geometric positions |
| `jte-public/BTMS_WK08_prepare.m` | Fresh M2 derivative with eight private constant-name To File sinks |
| `jte-public/BTMS_WK08_run.m` | Exact-build/SHA/fingerprint gates, one direct-start initialization and native output validation |
| `jte-public/BTMS_WK08_dryRun5s.m` | Separately approved owner-local 5s entry; never called by workflow |
| `jte-public/WK08_private_gate.py` | S→E→T authorization, private archive provenance, intent, ACL and readback receipt |
| `jte-public/WK08_supervise.py` | One future MATLAB process, external memory/disk/wall monitor and bounded termination |
| `jte-public/test_WK08_guards.py` | Offline authorization and sensor topology checks |
| `jte-public/test_BTMS_WK08_inject_guard.m` | B1 synthetic unsensed-channel rejection and unchanged-graph guard test; not executed |
| `jte-public/JTE063_streaming_drive.py` | One new schema whitelist entry; transport unchanged |
| `.github/workflows/wk08-pack-one-shot.yml` | Disabled R1 workflow; exact future marker only |
| `.github/workflows/wk08-ci5s-one-shot.yml` | Separate disabled CI_5S one-shot workflow (30 minutes) |
| `.github/workflows/wk08-preflight-check.yml` | Disabled read-only preflight; no MATLAB/vendor checkout or reservation |

No existing MATLAB file is modified. The vendor model, original continuous TF, controller law and solver
remain unchanged. R1 uses the already-approved sampled M2 derivative, not an alteration of the vendor TF.
The v01 MAX-based selector is neither imported nor called.

### Author self-check list (not Claude's review)

- [x] New `codex/wk08-*` branch starts at the specified WK06 commit.
- [x] Sensed vector is actually reduced to 312/16/8 elements before MinMax3; no unsensed dummy channels.
- [x] Neutral injection does not add any block/line/workspace variable; extended fingerprint equality is asserted.
- [x] CSV sensor positions are fixed by geometry; no temperature/rank input.
- [x] Four native M2 roles retained plus true max, measured max, pump power, 1s channel observation.
- [x] R1 is B0L, Ts=.01, 0–340s, b=0, S=all; exact runtime/source SHA and output gates in source.
- [x] One-shot intent and protected private full-byte readback; no public MAT/artifact upload.
- [x] New marker path is reserved but marker file is absent in S, preventing a source-push trigger.
- [x] Job remains `if: ${{ false }}`; reviewed SHA is unresolved until independent review.
- [x] Local offline Python checks only; see handoff/PR for actual check output.
- [ ] Owner-local 5s test (separate approval; not performed).
- [ ] Claude independent code/design review.
- [ ] Owner approval and future E/T actions; no run approval exercised by Codex.
- [ ] Physical build/compile, file clocks, hidden Simscape IC, measured time/RAM and 340s completion (unverified).

## CI_5S (D11) — source only, pending Claude review

CI_5S mirrors the R1 neutral sampled-actuator model and exact R2024b Update 10 build,
with a 5s horizon. Its disabled workflow sets `WK08_MODE=CI_5S`; R1 continues to default
to R1. CI_5S requires approval `APPROVE_WK08_CI5S_B_ONCE_AFTER_CLAUDE_GO`, its own marker
`jte-public/WK08_CI5S_TRIGGER.txt` and message `WK08_CI_5S_ONE_SHOT_20261103B`.
The marker remains absent in this source delivery. Both workflows stay disabled.

The separate private intent `WK08_CI5S_ATTEMPT_INTENT_20261103B.json` is reserved alongside
the R1 intent, but queries only its own pending/verified reservation. CI_5S neither consumes
nor blocks R1. The same receipt-verified M2 model/workspace inputs and transport preflight
are reused. CI outputs and `WK08_CI5S_<run>_PRIVATE_RECEIPT_20261103B.json` are uploaded to the owner-only
`BTMS-DATS` subfolder of the existing app-private Drive folder, using
`WK08_CI5S_RAW_UNREVIEWED_NOT_G5`. No raw data goes to public artifacts.

CI-only flags add `prepareWall_s` (builder), `firstStepWall_s`,
`trajectoryWall_s` (remaining steps after paused probes), `majorSteps` (completed step calls,
including first and terminal), and `pausedNativeReadable` (file name/readable/error identifier
for all eight native files). A failed paused read is recorded; if it prevents the three t0
reads, that t0 witness is marked unavailable and execution continues once to the terminal
gates. Any unreadable paused native file keeps the final status `UNQUALIFIED` even if final
files pass. Otherwise CI completion is `CI_5S_GATES_PASS_NOT_R1`, pending private readback
and Claude review. Other finite/clock/model/build/controller/solver gates remain in force.
Timings stay null/unavailable if a stage was never entered; failed entered stages record
elapsed time where possible. No physical performance claim is made from source checks.

The supervisor preserves R1 resource/wall bounds and uses a conservative maximum launch age
of 300s for CI_5S's 30-minute job, leaving delivery time. CI_5S never dispatches R1.
No MATLAB/CI was run, no workflow enabled/triggered. Hub #6 is queued after this review stop.

## Required run order: preflight check → CI_5S → R1

Before each one-shot, Claude follows the hub RUN_CHECKLIST.md and obtains the owner's
separate preflight approval. The read-only workflow uses the same S→E→T structure,
`WK08_PREFLIGHT_CHECK_20261103`, `jte-public/WK08_PREFLIGHT_TRIGGER.txt`,
`APPROVE_WK08_PREFLIGHT_ONCE_AFTER_CLAUDE_GO`, protected JTE_DRIVE_WRITE and a 10-minute
timeout. It is disabled and the trigger marker is absent in this source commit.

`WK08_private_gate.py check` accepts WK08_MODE=R1 or CI_5S. It refreshes OAuth, looks up
the existing app folder without creating one, checks owner-only ACL, WK06 neutral receipt,
quota >3GiB, absence of both pending/verified run intents, unique verified input metadata
and ACL, M2 receipt/proof/manifest linkage and actual workspace SHA. Three JSON files and
the workspace are downloaded to a private temporary directory that is deleted on success
or failure; model SLX SHA is linked through verified metadata, not downloaded. Vendor
checkout/SHA is deliberately skipped here and remains enforced by prepare.

The check path never creates actuator-review-private, reserves an intent, creates a Drive
folder, uploads, installs MATLAB, or starts a simulation. Safe CHECK lines report PASS/FAIL
with allowlisted machine reasons; only complete success prints WK08_PREFLIGHT_ALL_PASS.
The reason allowlist also accepts three-digit GOOGLE_API_HTTP codes, exact
GOOGLE_API_TRANSPORT_FAILED/OAUTH_REFRESH_FAILED and JTE101 codes. No exception text,
private paths, IDs or credentials are printed. A check PASS is a point-in-time prerequisite;
prepare still repeats its own gates before any approved one-shot. No workflow was enabled
or triggered and no live preflight/Drive call was performed for this source delivery.

## B2: licensed launcher and CI_5S-B identity — source only

Both CI_5S and R1 now resolve `matlab-batch` and launch exactly
`[matlab_batch, "addpath('jte-public'); BTMS_WK08_run('actuator-review-private/WK08_MANIFEST.json')"]`.
There is no direct `matlab -batch` fallback or second license-smoke process; the existing exact-build
assert is still first in the single MATLAB entrypoint. Missing launcher fails with
`WK08_MATLAB_BATCH_UNAVAILABLE`, already accepted by the WK08 safe-reason pattern.
The watchdog, termination escalation, resource sampling and no-retry rule remain.
JTE_GOOGLE_* / GH_TOKEN / GITHUB_TOKEN are excluded from the child environment; all other
variables, including GITHUB_* and RUNNER_* licensing context, are passed unchanged.

The private WK08_SUPERVISOR.json captures consoleExcerptBytes, UTF-8 consoleExcerpt
(replacement decoding if necessary) and consoleExcerptBase64 for the exact first 2048 bytes
of WK08_CONSOLE.log, including early license failures. These fields are never printed publicly.

The consumed `WK08_CI5S_ATTEMPT_INTENT_20261103.json` remains historical evidence.
The active CI_5S-B identity uses `WK08_CI5S_ATTEMPT_INTENT_20261103B.json`,
`WK08_CI_5S_ONE_SHOT_20261103B`, `APPROVE_WK08_CI5S_B_ONCE_AFTER_CLAUDE_GO` and
`WK08_CI5S_<run>_PRIVATE_RECEIPT_20261103B.json`. Mode stays CI_5S.
Preflight requires the new B intent and R1 intent absent, and accepts the consumed old intent.
R1 identifiers stay unchanged. The CI_5S-B workflow stays disabled and no trigger marker is added.
Tests use mocked launchers/processes only; no MATLAB, CI, live Drive check or workflow trigger.

## WK09 source-only R2–R13 definitions

See [WK09 run definitions](actuator-amendment/WK09_RUN_DEFINITIONS.md) for the
complete matrix, D10 C16/C8 controls, gates, estimates, changed-file inventory
and pending checks. The machine-readable registry is
[jte-public/WK09_runs.json](jte-public/WK09_runs.json). No run is authorized or
executed; the new workflow is disabled and validates definitions only.
