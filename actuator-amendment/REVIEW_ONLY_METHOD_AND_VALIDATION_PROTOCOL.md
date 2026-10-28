# Review-only method amendment: sampled actuator interface

Status: UNAPPROVED METHOD, STATIC/COMPILE ONLY. No toy, battery trajectory, G6 or paper is authorized here. Scientific decision: PR61 comment6462936805. Original pinned-source G5 is finally REJECTED/UNQUALIFIED FOR THERMAL CLAIMS, not a pending green-CI gate. Immutable original B0L/C0 and guard025 negative evidence stay unchanged.

## Scope of amendment
Retain vendor tag24.2.1.5/MATLAB R2024bU10, genuine pack electrical/thermal/fluid graph, current demand file,300K original controller reference, IC parameters/workspace, quantized source controller arithmetic and existing local sensor-bias mechanism.

For each staged model replace exactly one source continuous TF H(s)=1/(.001s+1) by:
1. A command Zero-Order Hold, explicit Ts, offset0.
2. A discrete state-space actuator: A=exp(-Ts/.001), B=1-A, C=1, D=0; x0=actual archived source TF OUTPUT y0 for that source case.
The new state has actuator-output units; it is not the old internal continuous TF state with its calibration scaling. No clipping, forced output, extra heat, PID, converter filtering/derivative change or source controller replacement.

B0L source is archived JTE101 original340. C0 source template is rebuilt STATICALLY using the existing frozen JTE056/JTE2026 builder, with original jteChannelIndex1/jteBiasK0 and exact localBias(T,j,b): Tm=T; Tm(j)=T(j)+b. Rebuilt C0 is not claimed byte-identical to historical SLX. Its actual archived original C0 y0/base variables/current/initial T312 frame are checked. Original B0L/C0 are not renamed as amended results.

Four clearly named REVIEW models (B0L/C0 x reference/fine) are engineering artifacts, not four physical experiments. Each must pass exact retained-block/solver/IC parameter diff, exact local edge replacement and all other graph connectivity, model-workspace and Stateflow-script equality. Compile-only source and amended models acquire missing before/after rate/unit metadata; no original numerical experiment is replayed. All runtime values/paths/model hashes stay private.

## Frozen review sampling design — not a source or hardware fact
Proposal for owner/scientific review:
- Feasibility design reference Ts_ref=0.010s (100Hz).
- Genuinely finer Ts_fine=0.005s (200Hz), half the period.
- Both offset0, tau retained .001s.

Design rationale: propose a maximum additional command detection-plus-state-output sampling latency below20ms for the review reference, below10ms for the finer design. A source decision can wait less than Ts until input sampling; D=0 adds one sample to the output response. The latency bound applies to a persistent decision that survives until sampling; a sub-Ts decision pulse may be missed entirely. These are declared engineering latency budgets, NOT measured pump/sensor timing, NOT vendor sampling metadata and NOT inferred from original solver MaxStep. Owner and Chat must defend/approve this latency requirement; otherwise NO-GO. No post-result Ts tuning is allowed.

These periods do not resolve the continuous1ms waveform between samples. They define a new sampled implementation, not a source-equivalent repair. The pair is frozen before any numerical comparison; neither is yet a validated numerical reference.

## Exactness, hold behavior and events
Under input u(t)=u[k] on [kTs,(k+1)Ts), the continuous first-order solution has sampled recurrence x[k+1]=A*x[k]+B*u[k]. The proposed physical interface additionally holds y(t)=x[k] between hits. This held OUTPUT is generally different from the continuous exponential between hits, even with held input:
y_cont(kTs+s)-y_hold=(1-exp(-s/.001))*(u[k]-x[k]).
Do not call full continuous-time plant actuation source-equivalent.

Changed timing must be listed explicitly: scheduled input sampling/state updates/output changes at0,kTs; original controller remains unchanged and may still evaluate continuously; global solver grid gains sample hits;1ms continuous integration state is removed; actuator logger/observer inherited rates can become discrete. Existing controller/Simscape event logic remains. ZOH output at0 is sampled u0, while external actuator output at0 is x0 from archived y0; do not force either to .25.

A discrete state log timestamp may refer to pre- or post-update state. The old continuous y=C*x logger/envelope cannot be reused blindly. After owner approval a NEW non-battery MATLAB toy must establish y[k],u[k],post-update x[k+1],sample tick/phase and global completed-major semantics before any physical baseline. Preserve duplicate native rows and each clock separately; no timestamp rounding/interpolation disguised as native, no default row-index alignment.

## Future actuator checks — theorem is not a result
Exact arithmetic with0<=A<=1,B=1-A gives x_next in conv{x,u}; x0 may lie below.25. Use actual sampled original MATLAB-law u, not a naively thresholded/clipped substitute. The ideal bounded-input formulas are L_k=.25+(x0-.25)*A^k,U_k=.75+(x0-.75)*A^k at output index k. Between hits, use the bound indexed by held sample k, NOT the former continuous-time JTE112 envelope. A legitimate sample delay or source command step is not a numerical spike.

For implemented double coefficients, the toy must verify recurrence against an independent high-precision/roundoff-aware oracle. A per-update arithmetic allowance can use gamma3=3u/(1-3u),u=eps(1)/2, times |A*x|+|B*u_cmd| for two multiplies plus addition; coefficient representation is accounted separately when comparing to exact exp. This is dimensionless arithmetic analysis, never a temperature/solver tolerance. No forced coefficient/output clipping. Unexpected between-hit changes, wrong sample phase, or gross recurrence/convex-bound violation stops the amended candidate.

## Conditional next physical study — NOT AUTHORIZED
Only after explicit owner acceptance of this model amendment/Ts and resource/logging plan:
1. Independently verify sample/hold + exact-ZOH toy on real R2024b (no battery). Existing JTE110 Python oracle is prior synthetic evidence, not MATLAB/plant proof; no broad suite replay.
2. If qualified and no-fee resources assured, ONE bounded amended baseline at declared reference Ts, initially0–340 with negative-control330–334 and first-event330–338, startup separate. No automatic second attempt, solver switch or source patch. Stop if invalid actuator/Simscape behavior recurs.
3. Preserve all312 Ttrue, raw/held command, actuator output/state/phase, input/current/reference/IC provenance, clock semantics, model/code SHA, log and private full readback.
4. Only then request separately preregistered second-event/full2400 validation. No current authorization for this stage.

## Before confirmatory C0/C1: thermal/numerical protocol requirements
Freeze same load/reference/IC/sampling phase/injection and source-unit audit. Both full2400 Ts resolutions must include both historical event windows plus startup, all312 channels, Tmax/Tmin/spread and source-law/actuator invariants. A common sample INDEX and event phase must be qualified; keep all duplicates and report unresolved comparisons.

Halving Ts changes the implementation AND the forced integration grid. It measures combined sampling/model discretization effects; it is not an isolated solver-convergence proof. A separately approved fixed-Ts plant integration refinement is also necessary, keeping the actuator clock unchanged. These are validations of the NEW amended family, never historical source G5 acceptance or another source solver remedy.

Preregister thermal error norms/units and scientific tolerances before those results. A two-level difference alone is an empirical discrepancy, not a certified error bound; unresolved asymptotic/reference/time-alignment uncertainty means NO-GO, not an invented thermal envelope. Any needed independent reference/extra level needs separate signoff, no automatic loop. C0/C1 thermal contrasts must reproducibly exceed a justified numerical-uncertainty envelope; zero/tiny contrasts stay null, no pseudo p-values.

Source-condition legacy studies remain exploratory: JTE042 requires descending B0L1800–2400 selection, unlike legacy C0/full-horizon ascending. Future amended selections use validated amended baseline and an approved tie policy before fault cases; no favorable re-selection. Legacy JTE072 groups remain separate; their amended C1 models are not built/tested here. JTE109 baseline kmin remains unverified.312 model channels do not establish312 physical sensors.

## Included-resource feasibility / NO-GO
Static review records actual current RAM/disk/private capacity and uses old negative-run runtime/row counts ONLY for cost screening, never thermal truth or a future performance guarantee.
Minimum sample hits alone:
-340s:34001 at10ms,68001 at5ms.
-2400s:240001 at10ms,480001 at5ms.
T312-only single-copy double arrays are respectively rows*312*8 bytes; all-state/history/measurement copies add cost. Existing global full-state logger is NOT qualified for the full two-resolution program and can exceed the current standard runner RAM. No full thermal GO is issued.

Proposed essential-signal logging/bounded physical-state snapshots would need its own documented initial/state-phase proof, implementation and measured memory/storage/runtime, preserving required native T312/actuator evidence. It is NOT implemented or assumed feasible here. If a complete no-fee2400/independent-reference plan cannot be qualified, FULL thermal claims are unachievable under current infrastructure; paper scope may become controller-decision-only ONLY after explicit owner approval and literature re-review. No paid fallback or forced acceptance.

## Public sources / limits
- Discrete state equations and parameters: https://www.mathworks.com/help/simulink/slref/discretestatespace.html
- Continuous-to-discrete ZOH matching at sample instants: https://www.mathworks.com/help/control/ug/continuous-discrete-conversion-methods.html
- Input hold semantics: https://www.mathworks.com/help/simulink/slref/zeroorderhold.html
- Compiled port types/width/units: https://www.mathworks.com/help/simulink/ug/determine-port-signal-attributes-programmatically.html

No toy/physical automatic run, source solver/tolerance/Mod retry, new JTE-numbered trial, paid tool, merge, public private MAT or JTE058 manuscript/export. Static/compile evidence is software preparation only.
