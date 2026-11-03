# WK09 R2–R13 definitions — 03 Nov 2026, Asia/Bangkok

Source handoff for Claude review; no runtime acceptance or run approval.
Replayed onto final PR #74 head `dd282cb2bddf1c7252d197c927965cbac545fb46`, including B2's
matlab-batch launcher, private console capture and CI_5S-B identity. Earlier WK08
source GO does not substitute for Claude's re-review of this final source. Coordination: BTMS-IJEHV-hub Issue #6, including D10's C16/C8.
No MATLAB, CI, private Drive read/write, enabling, triggering or retry here.

## Matrix

All runs start at0, end at2400 s, ambient300 K, source load/archived IC unchanged.
Use ode23t, MaxStep=.05, RelTol=AbsTol=1e-3 except R4. Ts=10 ms except R3.
All use the approved sampled actuator a=exp(-Ts/.001), B=1-a, C=1, D=0 with
archived initial output state. The rejected continuous-TF G5 is never used.

| Run | Purpose | Ts ms | Sensors | Bias K | Channel | Pipeline | Tolerances |
|---|---|---:|---:|---:|---|---|---|
| R2 | accepted baseline candidate |10|312|0|S(1)|bypass|1e-3 / 1e-3|
| R3 | sample-period sensitivity |5|312|0|S(1)|bypass|1e-3 / 1e-3|
| R4 | tolerance sensitivity |10|312|0|S(1)|bypass|1e-4 / 1e-4|
| R5 | C0 pipeline control |10|312|0|S(1)|active|1e-3 / 1e-3|
| R6 | D1 full negative |10|312|-2|R2 rank1|active|1e-3 / 1e-3|
| R7 | D1 masking control |10|312|-2|R2 rank156|active|1e-3 / 1e-3|
| R8 | D1 sparse negative |10|16|-2|hottest in S|active|1e-3 / 1e-3|
| R9 | D1 sparse stronger negative |10|16|-4|hottest in S|active|1e-3 / 1e-3|
| R10 | D1 sparse negative |10|8|-4|hottest in S|active|1e-3 / 1e-3|
| R11 | D1 positive side case |10|312|+2|R2 rank1|active|1e-3 / 1e-3|
| R12 | D10 C16 sparse-only control |10|16|0|S(1)|active|1e-3 / 1e-3|
| R13 | D10 C8 sparse-only control |10|8|0|S(1)|active|1e-3 / 1e-3|

R4 changes only both scalar tolerances by one decade. It is a predeclared
sensitivity, not a solver adjustment to force a PASS. R3 changes both ZOH and
actuator sample periods/coefficient pair, preserving archived initial output.
For all non-R3 runs, the builder captures the archived A/B/actuator/hold sample-time
strings after the receipt-pinned WK08 copy, reads them again, and asserts exact equality
without rewriting them. Only R3 writes A/B and sample periods. Only R4 writes tolerances;
every other run asserts the archived scalar 1e-3 values and preserves their exact strings.
The before/after actuator and tolerance records are returned in p.parameterAudit.
C0 must use an actual chart at b=0, not the R1 identity bypass. The optional
forcePipeline argument defaults false, leaving the reviewed R1 call unchanged;
WK09 passes true for active cases. C16/C8 use the exact committed WK08 CSV and
j=S(1), even at b=0, satisfying the B1 guard before any graph change.

## Dependencies and frozen selection

R2 waits for accepted R1 and measured resource feasibility. R3/R4/R5/R12/R13
wait for accepted R2. R6/R7/R11 compare against R5; R8/R9 against R12; R10
against R13. Run numbers do not prescribe chronological order. Suggested order:
R2, then sensitivity/controls, then the six fault cases after their controls.
Every trajectory needs its own owner approval; a source GO is not that approval.
The read-only preflight → CI_5S-B P1 → separately approved R1 sequence remains
required; none of those runs is dispatched by these definitions.

Only the accepted R2 supplies JTE-050 v02 time-weighted mean temperatures over
1800–2400 s. Freeze ranks1/156/312 and the entire descending312-channel ranking,
with ascending channel index for exact ties. For sparse faults, filter this
ranking by fixed S and take the first channel. Do not choose a MAX statistic,
new baseline, instantaneous hottest point, favorable channel, or subset based
on temperatures. Rank312 is retained for selector provenance, not an extra run.

The offline resolver consumes a frozen JSON selector with `version`,
`source_run`, `window_s`, `statistic`, `accepted_baseline_receipt_SHA256`, and
`ranking_descending`. The selector file SHA is recorded. This validates the
schema/permutation, not the truth of baseline acceptance: the future protected
transport must verify the receipt bytes, accepted status, R2/source provenance,
and selector/reviewer signatures before execution. The resolver never derives
or fabricates a ranking; unresolved fault cases return channel=null and BLOCKED.
Claude owns the independent selector/postprocessing and frozen predictions.
Prediction digest and accepted control/dependency receipts precede R6–R11.

## Common prospective gates and delivery

Vendor tag24.2.1.5, commit f98d21929a3a269dacd1ee38999cd9773760c6db;
SLX SHA256 0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0;
exact build `24.2.0.3361896 (R2024b) Update 10`. Revalidate archived M2 source SHA,
workspace/IC/load receipts and derived SLX SHA. Record source, definition,
subset, selector and derivative hashes. Retained physical/controller parameters
and graph stay fixed except the declared measurement path and R3/R4 changes.
No initial operating-point restore or claim of identical hidden Simscape states.
Keep direct-start visible t0 checks and readable paused-file precondition.

Require saved/reloaded and pre/post-run fingerprint equality, compiled sensed
width312/16/8, j in S, finite values and timestamps, 0..2400 completion, commands
only {.25,.5,.75}, and unchanged controller thresholds5/7.5 K inclusive. Keep
all eight WK08 To File roles: uCore, uSampled, actuatorY, native Ttrue312,
TmaxTrue, TmaxMeas, modeled pumpPower and Ttrue312_1s. The last has2401x312
values on the1 s grid; native/event rows must not be resampled or silently
trimmed. Constant names become `WK09_Rn_<role>.mat` inside a fresh private root.
No public MAT, raw traces, artifact uploads, secrets or console leakage.
Require complete private SHA readback and per-run receipt before any acceptance.
G5Accepted remains false until independent scientific review.

## One-shot and resource contracts

WK09_runs.json assigns distinct per-run marker, exact message, approval string,
intent and receipt. No marker file is committed. Every future executable run
must retain protected JTE_DRIVE_WRITE, attempt=1, S→E→T (reviewed source S;
workflow-only E with S SHA and enable predicate; single run-marker-only T),
owner approval bound to run/commit, unique durable private intent reserved
before MATLAB, one process/initialization, monitored resource limits, private
failure publication and no retry. A failed attempt consumes that intent.
Do not reuse WK08's R1 allowance or batch twelve runs under one approval.

Expected wall times are conditional estimates, not observations:
R2/R4/R5/R6–R13: approximately accepted R1 trajectory wall *2400/340 (7.06).
R3: screen conservatively at twice that (14.12*R1) for twice the sample hits;
this is an unvalidated planning factor. R4 can take longer with tighter tolerances.
No actual R1 timing was available; every numeric wall estimate stays unresolved
until measured. At10 ms: at least240001 sample hits; at5 ms:480001. Native
312-channel values alone imply599 MB /1198 MB numeric lower bounds before
clock, MAT overhead, events and workspace/state memory. The1 s matrix adds6 MB.
RAM cannot be inferred from those file sizes. Do not simply extend R1's short
1185 s ceiling to approve a2400 s trajectory.

All twelve runs are explicitly BLOCKED if the accepted R1 trajectory wall time exceeds
2700s (~45min): the 2400/340 scaling would leave insufficient conservative room in one
GitHub-hosted job's 21600s (360min) limit. At or below that screen is not automatic GO;
initialization, tighter-tolerance overhead, actual trajectory estimate and delivery must
still fit a measured total job budget <=21600s. This applies to every 2400s run, not just R3.

Before each future run, attach a measured RAM/storage/quota and wall budget,
including >=300 s private delivery reserve, and a reviewed trajectory timeout.
Retain >=8 GiB initial effective headroom,10 GiB scratch,3 GiB Drive, and the
WK08 live2 GiB RAM/disk reserves,1 GiB/file and2 GiB total caps until a separate
review changes them. In particular R3's native thermal lower bound already
exceeds the1 GiB per-file cap: R3 is operationally BLOCKED pending a reviewed
stream segmentation or resource/logging plan. No cap is silently lifted and
no native thermal history silently dropped. Timing/memory/quota overruns,
missing clocks/IC/receipt, nonfinite values or unresolved selection mean STOP /
UNQUALIFIED, never a retry or modified solver/controller to obtain PASS.

## Source entry points and limitations

`python3 jte-public/WK09_run_definitions.py R12` emits a resolved source contract;
R6–R11 require `--selector /private/frozen-selector.json`. Never commit emitted
selector-dependent definitions to the public repository. The static MATLAB
`BTMS_WK09_prepare` takes such a private resolved file and builds a derivative
without compilation or simulation. It retains all eight WK08 logging roles.

The disabled workflow is a **definition authorization gate only**, with no protected
Drive environment. Its explicit need/raise guards remain active under Python -O. It has no
MATLAB launch or Drive mutation. It is not an executable2400 s dispatcher:
that future integration must adapt the WK08 supervisor/runtime/private transport
for these longer horizons, hash-bind receipts, enforce the budgets above and
pass review before a separate executable source S/E/T is permitted. This
handoff defines runs; it does not claim twelve ready-to-execute approvals.

## Changed files and self-check

- README.md: WK09 index.
- actuator-amendment/WK09_RUN_DEFINITIONS.md: matrix/gates/estimates and limits.
- jte-public/WK09_runs.json: machine-readable twelve-run contracts.
- jte-public/WK09_run_definitions.py: offline resolver; no fabricated channels.
- jte-public/WK09_definition_gate.py: per-run marker/context/approval validation.
- jte-public/test_WK09_definitions.py: offline matrix/control/dependency/auth checks.
- jte-public/BTMS_WK09_prepare.m: static-only derivative builder.
- jte-public/BTMS_WK08_inject.m: optional forced zero-bias pipeline, default false.
- .github/workflows/wk09-run-definitions.yml: disabled definition gate, no dispatch.

Author checks: offline Python tests, MATLAB parameter-write source contracts for all
R2–R13 definitions, optimized-Python authorization rejection, and AST/JSON/source checks.
No MATLAB tests or runtime are executed by this handoff.
Pending: Claude review; MATLAB compile/runtime/fingerprint assertions; forced
C0 pipeline validation; accepted baseline/selector/prediction receipts; measured
resource plan; future executable integration. None is represented as a PASS.
Stop for Claude review. No MATLAB/CI or workflow enable/trigger was performed.
