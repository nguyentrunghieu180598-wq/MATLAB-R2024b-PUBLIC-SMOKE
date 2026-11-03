# WK10 D13 k=2 / 340 s source contract

Owner decision D13; design PR #74 comment 6604894521; Claude conditions and
implementation scope: comment 6605006892. Source only, pending independent review.
No simulation, workflow enable/trigger, merge or runtime PASS is requested here.

## Frozen scenario and proof

`jte-public/WK10_scenario.json` is metadata only: scenario `D13_K2_T340_V1`,
k=2, T=340 s, pinned vendor model SHA, vendor MAT SHA, Gain path and exact
original edge. The Python gate compares the entire object against the declared
contract, hashes the exact bytes into `WK08_MANIFEST.json` as `scenarioSHA256`,
and adds that file to `inputCodeSHA256`. Supervisor and publisher reject
metadata/hash/mode/horizon mismatches. MATLAB independently rechecks metadata
and byte SHA, the resolved vendor load SHA, the Gain value and actual wiring.

Only on the D13 derivative, replace the unbranched root edge:

```
Current demand/1 -> Battery Control/2
```

with:

```
Current demand/1 -> WK10 scenario current scale/1 -> Battery Control/2
```

The new block is `simulink/Math Operations/Gain`, `Gain='2'`,
`Multiplication='Element-wise(K.*u)'`. All samples are scaled, including rest,
negative/regenerative values and their existing interpolation. No source MAT
is rewritten or committed. The controller/SOC limit/actuator internals are
unchanged; applied current need not equal scaled demand when SOC gating acts.

The builder compares the full before/after structural fingerprints with only
the added Gain and the two declared endpoint substitutions removed from the
comparison copy. Config, workspace, scripts, comments and all other blocks and
connections must match. The actual saved/reloaded/pre/post-run fingerprint
includes the Gain. Source/vendor SLX and input archives remain immutable.
The synthetic `WK10_SCENARIO_ONLY` builder entry exists for static graph tests;
it cannot initialize or simulate and is not used by the workflows.

b=0, S=1:312, ambient=300 K, original archived IC, ZOH/actuator Ts=.01 and
coefficients, ode23t/MaxStep=.05/source tolerances, 340 s native endpoints and
all original finite/command-level/neutral-max gates are preserved. No summary
metric or temperature threshold is added to qualification. Historical R1 and
CI_5S identities, markers, workflows and approvals retain their exact values.
The reused native-success status spelling includes R1; mode, scenario hash,
new receipt name and new raw-unreviewed schema identify this distinct D13 run.

## Diagnostics and private delivery

Same eight R1 files/variables, under the private native directory:
`WK08_TmaxTrue.mat`, `WK08_TmaxMeas.mat`, `WK08_uSampled.mat`, `WK08_uCore.mat`,
`WK08_actuatorY.mat`, `WK08_pumpPower.mat`, `WK08_Ttrue312_1s.mat`,
`WK08_Ttrue312.mat`. No post-processing interface change is required.

After successful native gates, MATLAB reads logged TmaxTrue, uSampled and
pumpPower and writes private `SUMMARY.json`, labelled `DERIVED_NOT_EVIDENCE`:

- `Tmax_peak_K`, `Tmax_peak_time_s`: maximum and its first logged occurrence.
- `first_logged_Tmax_ge_305_K_s`, `first_logged_Tmax_ge_307_5_K_s`:
  first logged qualifying sample, not an interpolated crossing; NaN encodes as
  JSON null when never observed. No crossing is a diagnostic, not a failure.
- `uSampled_levels=[.25,.5,.75]` and `uSampled_counts` count all recorded rows;
  `uSampled_level_switches` counts adjacent unequal commands. Duplicate times
  are not filtered or resampled.
- `pump_energy_J=trapz(logged_time,logged_pumpPower)`; `N_samples` is the number
  of uSampled rows. `sampleCounts` separately records each used stream's count.
- `SOC_limit_intervention='NOT VERIFIED'`: no demanded/applied current or SOC
  witness exists in these eight logs. No added graph probe or inference from
  temperature is used.

Summary export errors are isolated from native run qualification; a small
NOT VERIFIED diagnostic is attempted instead. Publisher never interprets the
summary and never requires it for PASS. Optional summary upload failures are
recorded as NOT VERIFIED without changing qualification; that upload is capped
at 64 KiB and remains inside the unchanged total delivery byte budget.
Full original logs remain the evidence.
All D13 payloads, including optional summary, are uploaded privately to
owner-only BTMS-DATS using `<run>_<basename>` staging names; receipt names also
contain the run id. Local/native basenames and variables stay unchanged.
No raw public artifacts or console bytes are emitted. The first 2048 real-run
console bytes remain private in the supervisor report. No automatic run retry.

## Attempt A identities (proposed source, not approval)

Branch: `codex/wk10-d13-k2-340`; mode `D13_REF`.

| Field | Probe |
| --- | --- |
| Attempt | `WK10_D13_REF_K2_T340_A_20261103` |
| Workflow | `.github/workflows/wk10-d13-ref-one-shot.yml` |
| Marker (absent) | `jte-public/WK10_D13_REF_K2_T340_A_TRIGGER.txt` |
| Exact bare marker/message | `WK10_D13_REF_K2_T340_A_ONE_SHOT_20261103` |
| Intent | `WK10_D13_REF_K2_T340_A_ATTEMPT_INTENT_20261103.json` |
| Approval value | `APPROVE_WK10_D13_REF_K2_T340_A_ONCE_AFTER_CLAUDE_GO` |
| Receipt | `WK10_D13_REF_K2_T340_A_<run>_PRIVATE_RECEIPT_20261103.json` |
| Schema | `WK10_D13_RAW_UNREVIEWED_NOT_G5` |
| Concurrency | `wk10-d13-ref-k2-t340-a-20261103` |

| Field | Separate read-only preflight |
| --- | --- |
| Workflow | `.github/workflows/wk10-d13-preflight-check.yml` |
| Marker (absent) | `jte-public/WK10_D13_PREFLIGHT_A_TRIGGER.txt` |
| Exact bare marker/message | `WK10_D13_PREFLIGHT_A_CHECK_20261103` |
| Approval value | `APPROVE_WK10_D13_PREFLIGHT_A_ONCE_AFTER_CLAUDE_GO` |
| Concurrency | `wk10-d13-preflight-a-20261103` |

Both workflows remain false with zero reviewed source SHA. After source review,
only Claude/owner may construct each independent S -> workflow-only E ->
marker-only T chain; trigger messages must be bare (no trailers). Existing
WK08 environment key names are retained, with the new distinct approval values.
The protected environment remains JTE_DRIVE_WRITE. An approval is bound to the
exact mode/message/branch/source chain, run id/commit and attempt 1, never a batch.

D13 read-only preflight has 26 CHECK steps: valid scenario, fresh scratch,
OAuth/app folder/ACL/neutral receipt/quota, new D13 intent ABSENT, old R1 and
CI_5S-E intents PRESENT, original source metadata/download/linkage checks.
Pending or verified names count as recorded reservations, not proof of successful
trajectories. It does not reserve/upload/create a Drive folder or launch MATLAB.
Prepare repeats the D13 intent checks before its one new durable reservation;
existing R1 and CI_5S-E intents are never overwritten or deleted. A spent new
intent blocks reuse even on failure; another attempt requires a new reviewed
identity and owner approval.

## Unchanged resources and downstream boundary

Keep the 1185 s external / 1200 s internal process bounds and 35-minute job;
initialization/delivery reserves and memory/disk/Drive/file caps are unchanged.
Higher current may increase adaptive steps and SOC-limit activity. k=2 does not
guarantee either 305 K or 307.5 K; suitability must be reviewed separately from
native qualification. No automatic controller/actuator/solver/cap changes.
The completed 340 s vendor-load R1 remains the historical reference. No edit,
rebase, horizon or rank-window change is made to PR #77/WK09; Claude owns that
separate hub rebaseline before R2–R13 can use the frozen common scenario.

## Files and validation scope

Modified: `BTMS_WK08_prepare.m`, `BTMS_WK08_run.m`, `WK08_private_gate.py`,
`WK08_supervise.py`, `JTE063_streaming_drive.py`, `test_WK08_guards.py` (all
under jte-public), and README.md. Added: this design file, WK10_scenario.json,
test_BTMS_WK10_scenario_guard.m and the two disabled WK10 workflows. No other
public source or historical workflow changes are part of this delivery.

Offline Python checks retain the 37 original test meanings and add D13 metadata,
manifest, context/chain, preflight/no-write, single-launch/secret stripping,
private publication and optional-summary qualification tests. Source checks
inspect MATLAB summary operations and unchanged native PASS assertions.
The new MATLAB test file covers a synthetic Gain/edge delta, signs, fingerprint
reload and malformed/branched inputs, without compile/simulation statements.

NOT VERIFIED until independently authorized execution: MATLAB syntax/API/graph
behavior, synthetic MATLAB test results, SUMMARY numerical/JSON behavior on
actual logs, compile/initialization/trajectory, threshold crossing, physical
validity/IC equivalence, memory/runtime, live Drive and workflow operation.
Local static/offline results are reported in the PR, never as a MATLAB PASS.
