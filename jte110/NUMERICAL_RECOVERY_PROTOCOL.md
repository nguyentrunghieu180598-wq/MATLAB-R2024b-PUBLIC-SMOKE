# JTE-110 — G5 numerical-recovery canary and evidence gates (INTERNAL)

**Status**: Chat-made technical check only. Synthetic canary is not a MATLAB/Simulink study result and **does not close G5**. No manuscript/report/paper export under JTE-058. No private MAT/secrets, no auto merge or paid services.

## Real source pin and original failure
- MathWorks Battery-Pack-Model-Simscape tag 24.2.1.5, commit f98d21929a3a269dacd1ee38999cd9773760c6db, source SLX SHA256 `0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0`, MATLAB R2024b Update 10.
- 312 model-cell temperature channels (not independently certified physical sensors). Original first-order post-controller block SID 197 is `H(s)=1/(0.001s+1)`; original ode23t recorded MaxStep=0.05s. The *fine* profile only halves RelTol and does not resolve the 1ms filter by reducing MaxStep.
- JTE101: original full-plant 0–340s reproduces first postfilter excursion, constant .25 TF input did not. Controller-path/topology dependency supported, **actor NOT proven**.
- JTE102: equivalent State-Space with original controller wired in did NOT remove excursion; do not repeat filter realization swaps.
- JTE103: source profiler privately archived; Linux headless GUI unavailable. Do not block all science on naming one reset block.
- JTE106–108: 9 archived −2K C1 cases have no native core command-level change; −3K cannot force a change in the *unchanged faulted groups and archived physical states*. Not thermal or continuous-time equality.
- JTE109: existing baseline minimum-fault-group cardinality screening is the pending gate for a scientifically relevant next paired thermal experiment. Do not duplicate that work.

## Independent analytic canary (Chat task completed)
Run `python jte-public/JTE110_filter_reference.py --self-test`. It has **16 deterministic synthetic checks**, no external dependencies, no private archive reads and no physical-model run.
For a verified ZOH interval, the exact response is
`y(t+h)=u+[y(t)-u]*exp(-h/τ)` with `τ=.001s`.
Ideal trapezoid factor `(1-h/(2τ))/(1+h/(2τ))` at h=.05s equals `−12/13`. This can explain slow sign-alternating *ringing after perturbation*; it does **NOT** identify what caused the first original-model state perturbation, or show that ode23t accepted a 50ms step at that event.
The exact-ZOH function is permitted ONLY after independent certification of right-continuous held-input semantics/event times. Standard native-to-workspace rows and solver callback invocations do NOT suffice. Mismatched clocks are rejected.

## NEXT MATLAB-only Work job: CONDITIONAL G5 GATE, NOT A BATCH SWEEP
**A. Read existing SHA-verified owner-private JTE065/101/102/103 evidence, NO simulation.** Inventory original and fine B0L/C0 2400s, two postfilter event windows, 0–340s source state/actual TF input, and saved profiler session. Log as qualified/unqualified which signals represent accepted steps vs callback evaluations, and identify exact missing provenance. Source model/IC/source actual control law untouched. Work need not recalculate JTE106/107/108.

**B. Design ONE short numerical reference only if JTE109 gives an eligible scientific scenario**, or if that reference is needed to determine baseline reliability prior to such scenario. Before run, predeclare physical purpose, file/CI size, available MATLAB license, expected run time/steps and STOP rule. Compare unmodified source ode23t to an independently justified stiff solver option (ode15s or ode23tb) and sufficiently small MaxStep tied to τ, while retaining full source pack physics, original control law, load, initial conditions and traceable signal path. A provisional time-step goal such as τ/10 is **a candidate for feasibility analysis, not an accepted rule or permission for a 3.4-million-step full-plant run**.

**C. One short 0–340s test first**, initial source full state at t0=0; never restart at 330s using only T312 because hidden Simscape states may differ. Log certified controller core, actual TF input, filtered output, calibrated TF state and T312. Retain duplicate timestamps and report event topology. A source 'SUCCESS' job does not mean numerical G5 PASSED.

**D. G5 sign-off requires** that BOTH original postfilter event windows are either physically justified with correct accepted timing or numerically controlled by independent convergent solutions, and that thermal C1–C0 contrasts exceed a prospectively constructed solver/event-time uncertainty envelope. A 0–340s canary validates only the first event. Full 2400s may be proposed only after short event tests and owner resource sign-off. No arbitrary numerical thresholds or 1s interpolations across jumps.

## New physical-study design decision (Chat only)
JTE042 pre-registration requests B0L last 600s descending hot/middle/cold, whereas legacy JTE067/JTE069 cases used C0 full 2400s ascending: label those cases exploratory. `JTE069` changed **controller reference** 300→293.15K at Constant3 SID199, not physical ambient/current load. A valid second load requires a source-grounded current/load scenario with independent matched baseline and locked schedule; no silently changing temperature reference to simulate heat load.

## Three permitted outcomes
1. `PROVEN`: empirically consistent accepted actuator/thermal numerical agreement with receipts and justified bounds.
2. `FALSIFIED`: candidate numerical fix does not repair the first event — stop this candidate, do not repeat.
3. `UNDETERMINED`: report exactly missing event semantics, available/required runner/GUI or budget and required minimal next controlled test; no manufactured PASS.

Links: MathWorks source https://github.com/mathworks/Battery-Pack-Model-Simscape/tree/f98d21929a3a269dacd1ee38999cd9773760c6db ; official solver https://www.mathworks.com/help/simulink/gui/solver.html ; JTE042 registered Methods in owner Drive.