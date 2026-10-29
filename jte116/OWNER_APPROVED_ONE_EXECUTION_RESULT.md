# JTE116 ONE owner-approved trajectory — actual negative result

**GUARD025_EVENT_PERSISTS. STOP Mod/solver correction direction. G5 remains BLOCKED / NOT ACCEPTED.**

## Authentic execution
- Actual plant run [40645118578](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40645118578), job122672029125.
- Executed commit c88f8b673bfba889f6234d1f78cdccbfb7417265.
- MATLAB R2024b Update10; pinned MathWorks24.2.1.5 source; original ode23t/MaxStep/tolerances/reset/ZC, physical parameters/current load/300K reference/TF retained.
- Exactly ONE guarded025 B0L trajectory initialized and advanced0–340. Archived JTE101 Original340 reused, never rerun. No second plant attempt, solver variation or new C1.

## Actual safe flags
| Gate | Result |
| --- | --- |
| SOURCE_PARITY | PASS |
| T0_SAVED_STATE_PARITY | PASS |
| Completed-major checkpoint provenance | DOCUMENTED_COMPLETED_MAJOR_CHECKPOINTS_FIRST_WINDOW |
| HORIZON_340_COMPLETE | PASS |
| FIRST_WINDOW_NATIVE_EXCURSION | PRESENT |
| FIRST_WINDOW_MAJOR_EXCURSION | PRESENT |
| Native and major first-window conditional envelope flags | PRESENT |
| Negative-control native/major gap and envelope flags | CLEAR |
| SECOND_EVENT_NOT_COVERED_340 | TRUE |
| G5_ACCEPTED | FALSE |

The observed first-window anomaly persists at returned completed-major checkpoints as well as native records. The guarded025 construction therefore did not remove it in this bounded test. No unique reset/ZC actor or continuous-time physical failure is identified by this result. The analytic envelope remains conditional on bounded-input/no-physical-reset hypotheses; it does not identify a numerical reset actor.

Source arithmetic/output equality at recorded points, native actual-input/core equality, native observer clocks and calibrated TF state/output identity passed the frozen checks. All312 true-temperature channels and TF/input/core/q/qStar/state data were retained privately. No public magnitudes/timestamps/counterexamples or physical cooling/pump-energy claim.

Initialized-output t0 data was unavailable; the complete SAVED state map/T312/TF x0/y0 was compared at first completed major0 before processing further major hits. Unrepresented algebraic variables are not independently certified. Native duplicate rows and returned-major records remain separate. Core and actual-input checkpoint values are explicitly the same statically validated source-port alias; independent native ToWorkspace core was cross-checked.

The archived comparator used a normal driver; candidate used the documented stepping driver. This difference remains a causal limitation. No second-event or independent thermal/numerical convergence acceptance follows.

## Logger qualification history — no hidden test replay
- NEW non-plant toy run40644248712/job122669254355 atce4079477393f3cacbdb744b861d7b42a94af9f2 reached terminal hit, then failed an extra next-top monotonicity assertion. Its original overall FAIL remains preserved. No plant intent/initialization occurred in that run.
- Run40645118578 READ ONLY assessed the SHA-verified saved toy MAT/summary/receipt: actual initial/window completed-major clocks and finite nonterminal next-top fields, full native horizon and independent observer equality qualified. No toy rerun or canary rerun.
- The battery driver retains every first-window clock criterion. Terminal completion uses final-step completion/native horizon, not a fictional future-top checkpoint.
- Full private assessment readback preceded the single signed-runtime intent. The ephemeral Ed25519 signature is execution integrity, not an owner PKI signature; the direct human Work message supplied authority. Key removed immediately; no RSA data pipeline.

## Private delivery verified
The actual Cloud publisher completed full remote SHA readback. Direct connector reread of the PLANT receipt confirms every file verified, including raw MATLAB MAT, completed-major checkpoint MAT, saved t0 checkpoint MAT, logged guarded model SLX, console, flags and summary. Input manifest, saved-toy qualification and signed one-shot intent remain owner-private. No private asset identifiers/hashes or research values are in this public note.

CI SUCCESS is successful execution/capture/delivery. The guard candidate outcome is NEGATIVE.

## Stop and independent Chat review
No further Mod manipulation, tolerance/solver trial, repeated340, second event run,2400 sweep or G6 is started. Preserve original source and this negative evidence. Chat should independently review actual major/native traces, then reassess the original full-model numerical suitability or narrow the research claims under a NEW explicit scientific protocol. Work does not silently replace the physical plant/controller or declare G5 PASS.

No merge, paid service, monitoring automation or official manuscript/report export under JTE058.
