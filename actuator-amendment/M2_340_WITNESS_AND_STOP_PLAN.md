# M2/340 witness and stop plan — INTERNAL, PROPOSAL ONLY

This plan supports owner review of ONE future B0L10ms 0-340s feasibility observation under original300K/source current/initial parameter frame. It is not a physical-run authorization, a measured memory guarantee, an original-source repair or G5 acceptance. JTE058 remains active.

## Static gate and intended decision
Use only the SHA-pinned Work B0L10ms four-ToFile model from run40701917441. The new derivative changes exactly: saved StopTime2400->340; four fresh private ToFile filenames; Commented off->on for the actual same-source duplicate ToWorkspace jteTtrue/jteUcore/jteFlwR. Keep the other three workspace observers. Source, controller, Stateflow, sampled coefficients, IC/workspace, physical/electrical paths, original ode23t/MaxStep.05 and source load stay fixed.
Read actual cgroup/host/disk/Drive; screen free headroom and a bounded-stop policy. Actual peak RAM and solved IC are runtime measurements, not static prerequisites. If static/logger/host-policy checks pass, return M2_340_PREPARED_STATIC_PASS_OWNER_PHYSICAL_APPROVAL_NEEDED. Do not keep recompiling to claim these unmeasured dynamic facts.

## Only after explicit owner approval
Use a fresh owner-private mode0700 output directory. Recheck all four MAT paths absent immediately before initialize; ToFile overwrites an existing target when a simulation starts. Rebind paths with a logged-only diff if necessary, verify source/code/model/workspace/load hashes, effective StartTime0/StopTime340, original solver/tolerances/step/Ts/controller and no fault.
One attempt marker, one Simulation instance, one initialization. No auto retry, comparator rerun, changed current phase, sensor fault, reference shift or solver fallback. No 2400s dispatch.

## t0 / first completed-major witness
Record the resolved actuator initial OUTPUT-state from the actual archive-derived source model; never assume a constant. Record its actual initial/preupdate/output/postupdate phases. For the discrete C1/D0 implementation, output x[k] and postupdate x[k+1] are distinct; do not compare x[1] against archived y0.
Use documented initialize/step behavior and reuse the already-qualified completed-major ordering convention: capture previous top time before step returns and separately record next top time. A block PreUpdate/PostUpdate event is a block phase witness, not an accepted continuous solver step.
At the first completed major0, save actual T312, core, held input, actuator x/y and every represented retained physical state needed for IC comparison. Keep same-phase comparisons against the approved initialization parameter/archive map; explicitly exclude the removed continuous-filter state and account for the new discrete output state.
Attempt a documented full model operating-point witness only where the R2024b runtime supports it; do not deserialize private internals or invent an API. A logged-state Dataset is NOT a certificate of all hidden Simscape/algebraic/solver state.
If required visible initial checks or clocks are absent/different, stop before processing later physical times and classify UNQUALIFIED. If complete hidden-state coverage is unavailable, retain HIDDEN_IC_NOT_CERTIFIED and keep any continuation strictly exploratory under the owner's reviewed feasibility scope. No thermal correctness or complete source hidden-IC equality may be inferred. Independent numerical refinement remains necessary for thermal inference.

## Native data and first window
Four Timeseries files retain their own driving clocks and duplicate rows actually produced: uCore, ZOH input, actuator y, full312 true temperature. Inherited ToFile rate is not an accepted-step certificate.
Capture bounded initial and330-338 actuator state/phase witnesses (including330-334 control), with both raw/native file clocks and independent completed-major records clearly labeled. Do not enable full2400 all-state history to obtain this. ToFile y alone is not independent state evidence.
Validate x[k+1]=A*x[k]+B*u[k], y[k]=x[k] using actual phased states and the already-qualified numerical rounding/coefficient budget, not a fresh arbitrary tolerance. Preserve source-law operands and both cooling/auxiliary electrical paths. Keep K source/SSC/converter provenance and missing compiled SI strings/FlwT ambiguity visible. No measured-pump-power claim follows from Gain500.
No resampling, deduplication, output-only time grid, clipping or selective event removal. A clean short observation can at most qualify FIRST_WINDOW_CONDITIONAL, never second-event/full-G5 or thermal efficacy.

## External watch and bounded resources — no monitor started in static job
A live external cgroup/process, host available RAM, disk and file-growth watcher must start before any approved initialization and remain able to act while MATLAB step is blocking. Record selected cgroup path/limits and MATLAB PID, actual RSS/peak and timestamps.
Operational ceilings for review: keep2GiB live RAM headroom (host and finite cgroup limit);2GiB scratch disk reserve;1GiB max per file and2GiB total native payload; at least512MiB independent Drive readback reserve. Check planned private delivery against actual free Drive before starting.
Trajectory wall ceiling1200s, at least300s reserved delivery/cleanup; do not start if remaining job time cannot cover both. These are stop policies, not runtime/row-count predictions.
At a limit, request pause/stop and close files. The external controller must have bounded interrupt/termination fallback if MATLAB is blocked; forced termination can leave incomplete artifacts. Preserve them as diagnostic/incomplete and report UNQUALIFIED, never trim samples to pass or retry. A GitHub job-level timeout remains a final guard, not evidence that files were closed.
A paused ToFile file is closed; inspect/copy it without modifying the live file. After final stop, verify actual full horizon/window coverage and file readability, byte SHA256/MD5 and complete owner-private readback receipts before scratch cleanup. A timeout/OOM cannot be reported as successful data preservation without those receipts.

## Runtime outcome and later science
Persistent nonphysical excursion/recurrence violation -> STOP; no more Mod or solver manipulation. Missing IC/clock/resource evidence -> UNQUALIFIED. Clean data -> FIRST_WINDOW_CONDITIONAL only.
Later, separately reviewed gates still include2000-2400 second window, fixed-Ts solver refinement, Ts implementation sensitivity,312-channel thermal uncertainty and properly controlled C0/C1 design. Recompute fault feasibility on a newly qualified amended baseline; JTE109's archived original-state negative result is neither invalidated nor a guaranteed new-model null. No forced Tref/load/favorable-channel selection.
