# CHAT peer review of Work WK04 — 01 Nov 2026

**Source inspected:** Work PR [#65](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/pull/65), head `2c4c9a44e60f8f1a7ceefe83a58384303f390b57`, `jte-public/BTMS_WK04_t0Fixture.m`, `jte-public/WK04_private_gate.py`, `actuator-amendment/WK04_SOURCE_REVIEW_20261101.md`.

**Verdict:** `WK04_SOURCE_DELIVERED_REVIEWED_WITH_MAJOR_BLOCKERS`. Work completed its SOURCE delivery; **WK04 has NOT been executed under MATLAB R2024bU10**. No physical run, G-M3 acceptance, G5/340/2400/C0/C1 thermal proof, or approved source-clone parity exists. Do not confuse publisher or Python preflight success with scientific acceptance.

## Findings requiring code response before one authorized synthetic MATLAB try

| ID | Severity | Reviewer finding | Required change/proof |
|---|---|---|---|
| R1 | Major | `terminalReceipt(s,...)` calls `metadata(s.SimulationOutput,'TERMINAL_PRE_STOP')` and later `assert(strcmp(terminal.metadata.stopEvent,'ReachedStopTime'))`, whereas `outD=stop(s)` happens **after** that receipt. If `ExecutionInfo.StopEvent` is finalized only on stop, the code may reject a good trajectory. This is a **source-order risk**, not an observed MATLAB failure. | Save pre-stop status/time diagnostically, then validate final stop reason against post-`stop(s)` `SimulationOutput`; require raw pre/post receipts and fail-closed on missing actual stop reason. Do NOT call an inactive terminal an accepted major. |
| R2 | Major | `sim(in0)` with `StartTime=StopTime=0` still performs a time-step; `snapshotTime=0` does not certify **pre-update** physical state. Restored state with StartTime 0 may process the initial discrete update differently. | Retain full event phase order and direct vs restore parity, declare a post-t0 OP if evidenced, and return NO-GO if replay mismatches. Do not force bitwise equality by modifying source physics. |
| R3 | Major | `metadata()` uses one catch for ModelInfo and ExecutionInfo extraction, losing field-specific diagnostics. Supported fields can differ by lifecycle and installed release. | Record presence/absence of each field separately, distinguish incomplete pre-stop metadata from required final post-stop metadata; any missing mandatory field is explicitly UNAVAILABLE/NO-GO. |
| R4 | Major | The last persistent `BTMS_M3_events('get')` phase triplet is not evidence of **all** discrete updates between major steps. | Independently audit the *complete* native phase CSV: sequences, tick count, repeated timestamp handling, state/output transitions and drop/gap detection. Never infer solver major time from callback time. |
| R5 | Review | MATLAB exact `version` string comparison might fail across build text formats even if R2024b Update10; no actual runtime was queried. | Keep strict release/update pin but report actual observed version/build in protected diagnostics, reject by documented build mismatch rather than silently weakening version controls. |
| R6 | Major | Private publisher can succeed while MATLAB science gate fails; Python reports readback after independently protected upload. | Three independent flags must remain visible: `MATLAB_API_QUALIFIED`, `PRIVATE_TRANSPORT_VERIFIED`, `PHYSICAL_G5_ACCEPTED=false`. No `QUALIFIED_API_FEASIBILITY_ONLY` without first two evidenced on the **same** attempt. |

Current code instantiates a toy `WK04T0Nonbattery` only, not the pack. The full model's `BlockReduction`, complete hidden Simscape t0 and matched B0L/C0 restoration remain independent blockers. The assistant's independent synthetic Python preanalysis selftest was run 01 Nov: `SYNTHETIC_SELECTION_AND_PEAK_SENSITIVITY_SELFTEST_PASS; MATLAB_RUN=0; G5_ACCEPTED=false`; this is unrelated to thermal G5.

## WK05 next bounded Work task
Create an isolated **SOURCE-ONLY** correction branch based on the WK04 head, reply against R1–R6 with patch/commit and return `WK05_SOURCE_READY_FOR_REVIEW` or `WK05_SOURCE_NO_GO`. Show exactly ONE future R2024b U10 nonbattery execution protocol with branch/env/quota/owner-private upload checks, prepared for separate approval. It must never auto-enable workflow, auto-run MATLAB, rerun old toy suites, consume B0L340 permission or run C0/C1/2400. Preserve actual source physics/solver/controller hashes, private MAT and credentials.

If zero-stop OP cannot be proven as a valid **same-model t0 restoration**, an author-reviewed paired direct-start comparison may be proposed as a **protocol amendment**, with all hidden-state equality limitations; it cannot inherit G-M3/G5 acceptance.

**Scientific trajectory:** pre-registered `-2 K` three-channel C1 cases only after a truly qualified 0–2400s zero-bias baseline over selection window 1800–2400s; report no-effect cases. The 14 Nov date is a conditional *internal manuscript* target, not acceptance deadline.
