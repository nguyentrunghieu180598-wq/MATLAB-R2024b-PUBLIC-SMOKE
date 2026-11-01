# WK-04 — zero-stop nonbattery adapter, source review only

**Verdict: `WK04_SOURCE_READY_FOR_REVIEW`.** This branch adds a new toy fixture and a protected private I/O gate. Nothing here has run under MATLAB. `G-M3=UNQUALIFIED`, `G5=NOT_ACCEPTED`, and the owner-approved B0L10ms 0–340 s observation remains unused.

## Exact diff and scope

- New `jte-public/BTMS_WK04_t0Fixture.m` creates only `WK04T0Nonbattery`, a 0.5 constant, 10 ms hold/state-space actuator, clock and 312-wide *synthetic* vector. Its `StartTime=StopTime=0` `Simulink.SimulationInput` requests `SaveFinalState=on` and `SaveOperatingPoint=on`; it requires a complete `Simulink.op.ModelOperatingPoint`, `startTime=0`, `snapshotTime=0`, normal-mode metadata and a terminal reason. This is a post-t0-step candidate, not proof of pre-update physical IC.
- The same in-memory model and unchanged literal workspace inputs are then used for direct-start and `setInitialState(op0)` restore runs to 30 ms. Full four To File native series and full phase CSV are checked with duplicates retained; direct and restored series must agree exactly or the result is `UNQUALIFIED`. Toy structural checksums from actual `SimulationMetadata.ModelInfo` must agree. The fixture does not load a battery SLX.
- The direct-start loop **actually calls** a bounded nonterminal witness recorder after each `finalstep=false`. It captures `processedPriorTop`, finite paused next `Time`, role-specific tail clocks and `newEventsSincePriorStep` versus the last persistent phase triplet. At `finalstep=true`, it creates a distinct terminal receipt, never an accepted next-major row. It records raw terminal lifecycle and `ExecutionInfo.StopEvent` when available; missing mode, checksum or stop reason leaves `UNQUALIFIED`.
- `jte-public/WK04_private_gate.py` is a separate protected-process proposal. `prepare` authenticates the GitHub run/branch/message and owner-private Drive access, checks free quota, hashes the source inputs by bytes, and writes an input receipt before MATLAB. `publish` is intended for a distinct `if: always()` protected step after MATLAB; it uploads every nonempty private diagnostic, independently checks remote bytes through existing `upload_verified`, and writes a separate postflight receipt. It never treats a caller Boolean or input receipt as proof of output readback. No OAuth values or private MAT are committed.
- Existing PR #62/#63/#64, vendor source, original solver/controller/actuator parameters, current/300 K frame, workflows and protected rules are untouched. The old 30 ms fixture is not invoked or repeated. The new toy's ode23t settings serve API qualification only and are not a physical solver comparison.

## Trusted boundaries and known limitations

The toy is generated in memory; therefore the independent input SHA covers the versioned fixture/helper `.m` bytes and the private-gate Python bytes, not a nonexistent prebuilt toy SLX. The compiled `ModelStructuralChecksum` binds the three toy trajectories after creation. A later physical-clone qualification must separately hash the actual pinned SLX, workspace/parameter and input bytes before MATLAB; WK-04 never asserts that source clone provenance from the toy. The protected Python gate must be wired only after branch/environment permission and one-shot authorization are independently reviewed. Its future message guard is `WK04_T0_NONBATTERY_ONE_SHOT`; no workflow is enabled in this branch.

The full OP object is saved privately. MathWorks documents that it contains hidden block, solver and execution-engine states even when Simscape internals do not appear in `loggedStates`. The exact R2024b StopTime documentation also says equal start/stop executes one step. Thus a zero-time OP may represent a **post-update t0** state. Strict direct-vs-restored parity and phase order must be observed before any stronger interpretation. The toy has no Simscape physical network and cannot prove hidden pack IC or B0L/C0 parity. `BlockReduction=off` is set on the NEW toy only; the frozen physical clone's value remains to be inspected, not altered.

The adapter reuses the M3 phase and bounded-signal helpers, but its toy-specific recorder is a separate local function. WK-03's source-clone SHA pin is never spoofed to run the toy. Four tail timestamps from bounded Dataset logging are distinguished from the four complete To File clock vectors; the latter are read after each run. If normal-mode final `step` again returns `inactive`, the adapter retains a private terminal diagnostic and fails closed rather than calling it a valid accepted-major event.

## Minimum private evidence schema

`WK04_PREPARE_GATE.json`: GitHub run/commit, exact input `.m` SHA-256 map, nonbattery source kind, quota, `physicalRun=false`. `WK04_FLAGS.json`: terminal classification, stage, safe error identifier and private reason. `WK04_PRIVATE_EVIDENCE.mat` or partial MAT: complete OP object/type/startTime/snapshotTime, configured BlockReduction, metadata structural checksums/mode/StopEvent, direct nonterminal witness array, separate terminal lifecycle, three full phase CSV traces and twelve native To File series (four roles for each of zero/direct/restore). `WK04_PRIVATE_READBACK_RECEIPT.json`: local SHA-256 and independently verified owner-private remote bytes for each file, including partial diagnostics. Sample counts are not durations or physical results. No field can say G5 PASS.

## Static checks and proposed future one-shot command

Static Python `py_compile` of `WK04_private_gate.py` passed on 01 Nov 2026. MATLAB syntax, API behavior, phase callback order, StopTime0 OP capture, checksum parity and replay have **not** been tested. Source files were read back byte-for-byte from the WK-04 commit; no Actions run is evidence for this branch.

After separate authorization, a protected workflow may run the following **one** tiny nonbattery qualification on MATLAB R2024b Update 10, provided its branch/environment access and private publisher are reviewed. These are proposed commands, not executed here:

    python jte-public/WK04_private_gate.py prepare
    matlab -batch "addpath('jte-public'); p=fullfile(pwd,'actuator-review-private'); BTMS_WK04_t0Fixture(p,fullfile(p,'WK04_PREPARE_GATE.json'))"
    python jte-public/WK04_private_gate.py publish  # separate protected if:always() step

The MATLAB command must exit nonzero on every `UNQUALIFIED`; the private publisher runs independently and only reports storage/readback. An API-only toy PASS would authorize a separate review of the exact physical-clone t0/IC method, not a pack run. If the zero-stop OP cannot restore on the same model, or the effective mode/StopEvent/checksum is unavailable, return `WK04_NO_GO` and review a paired direct-start protocol with explicit hidden-IC uncertainty; do not run another toy automatically.

## Documentation basis

- MathWorks R2024b [Stop time](https://www.mathworks.com/help/releases/R2024b/simulink/gui/stoptime.html): equal start/stop runs one step.
- MathWorks R2024b [Save final operating point](https://www.mathworks.com/help/releases/R2024b/simulink/gui/savefinaloperatingpoint.html) and [ModelOperatingPoint](https://www.mathworks.com/help/releases/R2024b/simulink/slref/simulink.op.modeloperatingpoint.html): complete object, timestamp fields, hidden-state scope and Block reduction warning.
- MathWorks R2024b [setInitialState](https://www.mathworks.com/help/releases/R2024b/simulink/slref/simulink.simulationinput.setinitialstate.html) and [step](https://www.mathworks.com/help/releases/R2024b/simulink/slref/simulink.simulation.step.html): restore and completed-major/terminal semantics.

