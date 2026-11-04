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
to R1. CI_5S requires approval `APPROVE_WK08_CI5S_E_ONCE_AFTER_CLAUDE_GO`, its own marker
`jte-public/WK08_CI5S_TRIGGER.txt` and message `WK08_CI_5S_ONE_SHOT_20261103E`.
The marker remains absent in this source delivery. Both workflows stay disabled.

The separate private intent `WK08_CI5S_ATTEMPT_INTENT_20261103E.json` is reserved alongside
the R1 intent, but queries only its own pending/verified reservation. CI_5S neither consumes
nor blocks R1. The same receipt-verified M2 model/workspace inputs and transport preflight
are reused. CI outputs and `WK08_CI5S_<run>_PRIVATE_RECEIPT_20261103E.json` are uploaded to the owner-only
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
quota >3GiB, absence of the R1 pending/verified intent and presence of the spent CI_5S-E intent (B9), unique verified input metadata
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

## B2: licensed launcher (identity now CI_5S-E, see the 03/11 fixes section) — source only

Both CI_5S and R1 now resolve `matlab-batch` and launch exactly
`[matlab_batch, "addpath('jte-public'); BTMS_WK08_run('actuator-review-private/WK08_MANIFEST.json')"]`.
There is no direct `matlab -batch` fallback. Since B5 (03/11) a separate pre-reservation license probe
(`matlab-batch "disp('WK08_LICENSE_OK')"`) runs in the workflow before the intent is reserved; the
exact-build assert is still first in the single supervised MATLAB entrypoint. Missing launcher fails with
`WK08_MATLAB_BATCH_UNAVAILABLE`, already accepted by the WK08 safe-reason pattern.
The watchdog, termination escalation, resource sampling and no-retry rule remain.
JTE_GOOGLE_* / GH_TOKEN / GITHUB_TOKEN are excluded from the child environment; all other
variables, including GITHUB_* and RUNNER_* licensing context, are passed unchanged, plus
`MW_BATCH_LICENSING_ONLINE=true` (B4).

The private WK08_SUPERVISOR.json captures consoleExcerptBytes, UTF-8 consoleExcerpt
(replacement decoding if necessary) and consoleExcerptBase64 for the exact first 2048 bytes
of WK08_CONSOLE.log, including early license failures. These fields are never printed publicly.

The consumed intents `WK08_CI5S_ATTEMPT_INTENT_20261103.json` (A), `...20261103B.json` (B), `...20261103C.json` (C) and `...20261103D.json` (D) remain historical evidence.
The active CI_5S-E identity uses `WK08_CI5S_ATTEMPT_INTENT_20261103E.json`,
`WK08_CI_5S_ONE_SHOT_20261103E`, `APPROVE_WK08_CI5S_E_ONCE_AFTER_CLAUDE_GO` and
`WK08_CI5S_<run>_PRIVATE_RECEIPT_20261103E.json`. Mode stays CI_5S.
Preflight requires the R1 intent absent and the spent CI_5S-E intent present (evidence that the 5 s run is on record, step `CI_5S_E_INTENT_CONSUMED`); A, B, C and D are not queried.
R1 identifiers stay unchanged. The CI_5S-E workflow stays disabled and no trigger marker is added.
Tests use mocked launchers/processes only; no MATLAB, CI, live Drive check or workflow trigger.

## 03/11 fixes after run 41593851156 (Claude, owner-directed)
- B4: `WK08_supervise.py` sets `MW_BATCH_LICENSING_ONLINE=true` for the MATLAB child. `matlab-actions/run-command@v3` sets the same flag (its `src/index.ts`); without it `matlab-batch` looks for a license file and fails with License Manager Error -1 (runs 41518493411, 41593851156).
- B6 (03/11, after run 41601825131): a bare `matlab-batch` ignored `MW_BATCH_LICENSING_ONLINE` (License Manager Error -1, license path = local files only). `run-command@v3` does not call `matlab-batch`; it runs its bundled `dist/bin/glnxa64/run-matlab-command`. Both one-shot workflows now (1) probe the license with `uses: matlab-actions/run-command@v3` and a static `disp('WK08_LICENSE_OK')` before the reservation, (2) resolve that binary into `WK08_RUN_MATLAB_COMMAND`, and `WK08_supervise.py` launches exactly that binary with the same single MATLAB statement and the same env. Missing/non-executable binary still fails with `WK08_MATLAB_BATCH_UNAVAILABLE`. NOT VERIFIED until a run: whether this binary licenses the supervised process.
- B5 (superseded by B6 for the launcher): both one-shot workflows run a `matlab-batch` license probe in the pre-reservation step. A licensing failure consumes no intent. The probe's own command is a static `disp('WK08_LICENSE_OK')` with no model/run data, so since run 41600733363 (WK08_LICENSE_PROBE_FAILED, root cause still open) its console text is printed to the public log on failure (truncated to 4000 chars) for diagnosis; this is unrelated to the real supervised run's console, which stays private (WK08_SUPERVISOR.json, never printed).
- B3: CI_5S uploads to BTMS-DATS are prefixed with the run id (earlier attempts left fixed names; JTE101_REFERENCE_NOT_UNIQUE). R1 names unchanged.
- Active CI identity is now CI_5S-E (`...20261103E`); A, B, C and D are consumed evidence (C: run 41603841041 licensed and started MATLAB, then `BTMS_WK08_run.m` rejected the approval string because it still expected the pre-rename value; fixed in D, with a test that cross-checks the gate and MATLAB strings).

## 03/11 fix B8 after run 41605643726 (CI_5S-D, Claude, owner-directed)
Licensing and prepare worked; `openProject` failed in `ssc_build batteryModule`: Simscape file namespace
`fluids.thermal_liquid...` not on path, because both WK08 workflows installed only
`Simulink Simscape Simscape_Electrical`. They now install the set every earlier working workflow uses
(`Simulink Simscape Simscape_Battery Simscape_Electrical Simscape_Fluids Stateflow`). Intent D is consumed, so the
active identity is E (message, approval, intent, receipt suffix, concurrency group, MATLAB approval string).
NOT VERIFIED until a run: later stages (initialize, first step, trajectory).

## WK10 D13 source delivery (pending independent Claude review)

This section describes a **new** declared input scenario; the WK08 material above
is the historical vendor-load/CI_5S record. No WK08 workflow, marker or approval
is repurposed. The completed R1 stays the vendor-load reference.

- Scenario `D13_K2_T340_V1`: k=2, T=340 s, b=0, all 312 channels, Ts=10 ms.
  `jte-public/WK10_scenario.json` pins the vendor model/MAT hashes, root Gain
  path and original edge. Its exact byte SHA and full metadata are bound into
  the private manifest and rechecked by gate, supervisor and MATLAB.
- `WK10 scenario current scale` is a root Gain on `Current demand/1` to
  `Battery Control/2`, multiplying every sample including rest and regen.
  Vendor MAT/timing, controller, actuator, solver and native PASS criteria stay
  unchanged. The complete Gain/edge delta is recorded and retained in the saved
  fingerprint; retained config/workspace/scripts/graph must match exactly.
- Private logs keep all eight R1 basenames/variables. `SUMMARY.json` is a small
  MATLAB-derived `DERIVED_NOT_EVIDENCE` diagnostic: peak/time, first logged
  threshold hits (JSON null if absent), command-level counts/switches, trapz
  pump energy and sample counts. It is optional for qualification; no crossing,
  summary field or summary export failure changes PASS. Existing logs cannot
  establish SOC-limit intervention: `NOT VERIFIED`. No extra vendor probe added.
- New read-only preflight: D13 intent absent, spent R1 and CI_5S-E intents
  present and untouched, source metadata/input linkage and quota/ACL checks.
  It cannot reserve an intent or launch MATLAB. Historical WK08 check semantics
  remain unchanged; D13 uses its separate mode and workflow.
- Both new WK10 jobs are `if: ${{ false }}` with zero reviewed SHA placeholders.
  Their trigger files are absent. No MATLAB/CI run, workflow enable/trigger,
  merge or retry is authorized by this source delivery. One separate owner
  approval for preflight, then one separate approval for the probe, after Claude
  independently reviews the final source. PR #77/WK09 is untouched.

See [the complete D13 contract](actuator-amendment/WK10_D13_SCENARIO_DESIGN.md)
for identities, exact files, test scope and NOT VERIFIED items.

## WK09 D13 340 s source implementation

Branch `codex/wk09-d13-340s` re-baselines WK09 on the restored WK10 source. R2 is an accepted external baseline; CONTROLS (R3/R4/R5/R12/R13) and CASES (R6-R11) have separate read-only preflights and execution approvals. Optional R14 has its own identity and is outside both groups. All six new workflows remain false, reviewed-source SHA zero, with no trigger files.

The selector is Claude's exact 2625-byte projection (no final newline), SHA-256 `cbaf7ede34dee318b1ab3a73cfbc53dbde44bda6700133c864c3dfc8ae148233`. CASES is blocked until an owner-pinned private attestation references Claude's CONTROLS acceptance in the hub. New group authorization requires independent review before any invocation.

See the [WK09 source contract](actuator-amendment/WK09_RUN_DEFINITIONS.md) for cases, identities, S-E-T chains, acceptance criteria, private transport and NOT VERIFIED items, and the [offline validation log](actuator-amendment/WK09_OFFLINE_VALIDATION.txt). No MATLAB/CI run, workflow enable/trigger, environment change or merge is authorized by this source delivery.
