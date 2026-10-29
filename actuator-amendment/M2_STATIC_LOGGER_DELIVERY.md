# M2 internal engineering delivery — new file-sink clones

Final actionable decision: **NO_GO_IC_CLOCK_OR_RESOURCE**.
Static sub-gate: **M2_STATIC_LOGGER_CANDIDATE_READY**, four newly instrumented models compiled on actual MATLAB R2024b Update10. This is not approval to execute a battery model, accept amended G5, write a paper or export official research results. JTE058 remains active.

## Actual evidence

[Run40701917441](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40701917441), job122863693243, executed commit75afa01be55339d20ce5831830a0cacdb0c5d3f4. Runtime24.2.0.3361896. Four private SLX/JSON/MAT proofs, full source/model manifests, console, resource data and19 output-file SHA/full remote readbacks are archived privately.

| New logger clone | Full graph/config parity | MATLAB compile | Input widths and types | Added sinks |
|---|---|---|---|---|
| B0L10ms | PASS | PASS | 1/1/1/312, double | exactly4 |
| B0L5ms | PASS | PASS | 1/1/1/312, double | exactly4 |
| C0 10ms | PASS | PASS | 1/1/1/312, double | exactly4 |
| C0 5ms | PASS | PASS | 1/1/1/312, double | exactly4 |

Each clone branches only raw source core, existing ZOH output, existing actuator output and canonical true T312. Actual sink compiled rates are continuous[0,0] for core/T312 and[Ts,0] for sampled input/output. Every logger rate belongs to its actual source block rate set. SampleTime-1, Decimation1 and Timeseries are verified. This is compile-time cadence evidence; no observed file clock, duplicate-row preservation or accepted physical solver checkpoint is inferred.

All retained block/dialog parameters, model workspace, controller chart code, original signal names and original signal/physical connectivity are equal after removing exactly the four new logger branches from the audit comparison. Independent saved-XML checks confirm complete conserving hypernets and full configuration parity for all four models. Source/vendor bytes remain immutable. Both cooling lookup and source-assumed auxiliary electrical paths accepted by M1 remain intact.

Source compiled SI metadata limitations and retained FlwT Unit1/component-K ambiguity remain visible. No new measured-pump-power/energy/temperature claim follows from these taps.

## Existing logging inventory, not an assumed legacy wrapper

B0L retains6 ToWorkspace blocks, including one full Ttrue vector. C0 retains9, including full Ttrue and Tmeas vectors. Each source Scope has DataLogging=false. Saved SaveState, SaveFinalState and SaveOperatingPoint are off. SignalLogging/DSMLogging/SaveOutput remain configured on; the independent XML inventory shows no explicitly marked source ports. Global SDI preferences are UNAVAILABLE and unchanged.

No preexisting history was disabled. Four ToFile taps do not by themselves prove reduced peak RAM. The operations proposal lists a separate logging-only diff for independent review; required measured/vector evidence must not be silently removed.

## What changed in the engineering code

The supplied Chat candidate at995294b89550b8cb044e4b55c802afd57eaa0405 and review52dd009593142a2c59f0eafcd4eb2b226e572622 were read in full and compared to the two attachments.
Work added canonical/new-path guards, absent-existing-ToFile protection, strict frozen coefficient comparison, approved source SHA/receipt enforcement in the wrapper, complete retained graph/workspace/controller/signal-name checks and actual compiled sink rate/type/width extraction. No source law or physical parameter changed.

First run40700792077 at ee926cb0e90f9699f09fb0b41be8863b1a71f788 reached compile of the first clone but failed in Work's metadata wrapper. Constructing a struct with a cell-valued multirate sample time created a struct array; normalRate then received a comma-separated list and raised MATLAB:TooManyInputs. The fix assigns struct fields separately. It changes neither model nor test criteria. Failed artifacts remain immutable/private; no plant trajectory occurred and no completed-case PASS was claimed from that attempt.

## Resource envelope and the remaining gates

The private delivery includes real current RAM/disk/Drive, actual static MATLAB process HWM and measured per-case/all-four static compile wall times. These measurements are not a340s physical process peak or runtime estimate.
At scheduled hits only, T312 values payload is84,866,496 bytes at10ms or169,730,496 bytes at5ms for340s. Adding each vector's timestamp yields85,138,504 or170,274,504 bytes. Per-role scalar clocks, solver extra hits, duplicates, uncompressed MAT metadata/cache and retained workspace copies add cost. These are lower-bound screens, not caps.

The saved clones deliberately preserve source StopTime2400 for configuration parity. They are NOT automatically bounded340s runnable artifacts. A future separately approved runner must explicitly enforce StartTime0/StopTime340, fresh absent output files, one attempt, monitored RAM/disk/time limits and verified private delivery.

The ToFile workaround is viable in R2024b: its pause/Stepper support differs from the pre-R2025a Simulation-object Dataset LoggingToFile restriction. The missing checkpoint combination is not declared permanently unsupported.
No extra file-backed or8/8 actuator toy was run: APIs and inherited rates/type/width are now verified, while a generic toy would not certify this plant's solved IC or physical memory peak. Actual ToFile-native file clocks remain explicitly unobserved.

The attached proposal is actionable but NOT IMPLEMENTED/QUALIFIED:
1. Review the exact redundant observer/buffer changes and checkpoint architecture on a separate clone, with another complete logging-only diff.
2. Qualify actual file/phase behavior only if the selected architecture needs a bounded no-plant canary; do not repeat accepted actuator tests.
3. Define the solved t0/first-completed-major witness, hidden-state coverage and effective340s one-shot resource/stop/readback guards.
4. Only after sufficient evidence and fresh owner scientific authorization, consider one B0L340 feasibility. No full2400 state-history budget is demanded as a precondition for340, and no such run is dispatched here.

Original-source G5 remains rejected for thermal inference; amended physical G5 UNQUALIFIED. Full2400/both windows/fixed-Ts solver refinement/Ts sensitivity/true-temperature uncertainty/paired causal design remain separate gates.
JTE109's negative small-fault result remains specific to archived original states. Recompute feasibility on a newly qualified amended baseline before prospective faults; no forced Tref/load change or favorable case selection.

## Private delivery and stop

Owner-private Drive retains the four new SLX models, code provenance, JSON/MAT proof tables, console and readback receipts. A final read-only delivery packages the resource envelope, inventory, operations proposal and qualification without invoking MATLAB.
No physical simulation, G1-G4 replay, baseline/fault rerun, source modification, paid service, automatic retry, merge or paper export follows. The compile workflow is closed after delivery.

Primary API references: [R2024b ToFile](https://www.mathworks.com/help/releases/R2024b/simulink/slref/tofile.html), [R2024b getSimulinkBlockHandle](https://www.mathworks.com/help/releases/R2024b/simulink/slref/getsimulinkblockhandle.html), [Logging version history](https://www.mathworks.com/help/simulink/gui/logdatatofile.html).

Final read-only packaging completed at [40703751211](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40703751211), job122870198416, executed commitb4f0818c6af5d43d5e7b13608e025c3b46da8774. Six private delivery files and their receipt have full SHA/readback. Final decision remains NO_GO_IC_CLOCK_OR_RESOURCE. Both new execution gates are closed after delivery; no MATLAB/physical execution followed the four static compiles.
