# M2 prospective 340s operations and logging-only review plan
Internal engineering proposal only; no physical execution, official research-results export or G5 acceptance.

The four ToFile taps are an instrumentation candidate. They do not reduce legacy workspace buffers automatically and do not establish complete solved physical IC or accepted-major clocks.
A source StopTime of2400 is deliberately retained in the saved static clone to prove config parity. The word Short in the preparer name is not a run-duration guard.

## Separate logging-only change set, NOT applied
- Inventory each actual ToWorkspace, active Scope logging, marked signal/DSM/SaveOutput history, current SaveState and SDI policy. Do not assume allstate logging is on because old execution wrappers once enabled it.
- Once ToFile clock/readback semantics are qualified, review removal/commenting of only redundant observer branches on an isolated clone. Four new ToFile taps stay at the same original source ports. Preserve original signal names/physics/controller/sensor/IC parameters and complete physical nets.
- Keep one T312 native file, plus separate raw core, ZOH input and actuator output files. Retain all samples actually recorded within330-338 and its330-334 control. Do not interpolate, drop duplicates, cap native rows or turn row counts into duration fractions.
- A bounded in-memory state-tail/checkpoint design would be distinct from full state history. Reuse documented completed-major ordering lessons from JTE116, but do not copy its full-history SaveState+Dataset configuration and claim memory improvement.
- Explicit source units/SSC contracts, blank compiled SI metadata and FlwT Unit1/K ambiguity remain separately disclosed.
- The four taps alone do not log actual auxiliary/battery branch current or voltage; no electrical energy inference follows from modeled pump demand alone.

## API feasibility, not proof of execution
R2024b ToFile supports pause/Stepper with incremental MAT output and closes its file on pause. This is independent of unsupported pre-R2025a Simulation-object Dataset LoggingToFile.
Consequently a future ToFile+documented Simulation stepping design is a viable candidate for bounded completed-major checkpoints. It is not ruled out by the Dataset restriction.
No such physical-state/checkpoint combination has been executed on these new logger clones. No full hidden operating-point equality is inferred from workspace values or visible saved-state maps.
A minimal file/phase canary is reserved only if this specific architecture's cadence or file behavior is actually uncertain; the prior8/8 actuator toy must not be repeated.

## Proposed ONE B0L 340s feasibility, only after independent review and fresh owner approval
Use an explicitly selected saved B0L10ms source under original source load/reference/IC/ode23t policy as a low-cost candidate;10/5ms sensitivity is a future independent gate. No changed current segment/Tref or fault case is introduced.
Allocate a fresh mode0700 private output directory and recheck every target MAT is absent immediately before initialization: ToFile overwrites existing files at simulation start. Set runtime StartTime0/StopTime340 explicitly, assert effective bounds before time advancement, keep one simulation instance and one attempt marker. Never fall back to2400 or retry automatically.
Before processing t>0, qualify a documented t0/first-completed-major0 witness, actual T312 and new actuator state plus all represented retained physical states; disclose absent hidden-state coverage. If initial consistency is unavailable/different, STOP UNQUALIFIED and preserve partial diagnostics.
Use actual recorded inherited file clocks. Callback evaluations, source-rate metadata and completed-major observations have distinct semantics.
After initialization, record real MATLAB/cgroup/host RAM and file growth; the compile-only peak is not a trajectory bound.

Candidate operational limits for owner review (not measured success bounds, not implemented here):
-At least2GiB host-available RAM reserve and2GiB scratch disk reserve must remain. Stop cleanly if either reserve is crossed; a process/cgroup monitor must itself be qualified.
-At most1GiB per native file and2GiB total log payload, with at least512MiB independent Drive delivery reserve. Exceeding a cap means incomplete/UNQUALIFIED, never sample deletion or a truncated PASS.
-At most1200s trajectory wall time plus at least300s remaining for private delivery/cleanup, reusing the earlier bounded-job policy only as an operational ceiling. Neither the old benchmark nor this cap predicts new amended runtime.
-A pause/stop must close files; read only a copied paused file, never alter a live ToFile MAT. Preserve all actual evidence, then full SHA256/MD5 private byte readback and receipt before cleanup. Do not describe timeout/OOM loss as successful readback.
-No full2400 state-history budget is a precondition for this prospective340 feasibility. Conversely, the170MB/85MB one-copy schedule payload is not a RAM/disk upper bound.

No run is dispatched. Final M2 readiness must use actual compile/graph files and retain NO_GO_IC_CLOCK_OR_RESOURCE until the above missing gates have sufficient evidence. Existing JTE109 cardinality<=3 negative result applies to archived original states only; prospective fault feasibility must be recomputed from any newly qualified amended baseline.

Primary sources:
https://www.mathworks.com/help/releases/R2024b/simulink/slref/tofile.html
https://www.mathworks.com/help/simulink/gui/logdatatofile.html
