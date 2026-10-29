# M2/340 — internal engineering delivery
Date:29Oct2026 (owner timezone). Not a manuscript, submission report or official research-results export. JTE058 remains active.

## Final outcome
**M2_340_PREPARED_STATIC_PASS_OWNER_PHYSICAL_APPROVAL_NEEDED**.
This completes the requested one-model static preparation/compile gate. It does NOT approve a physical trajectory, certify solved IC/native clocks/physical memory peak, repair original-source G5 or establish thermal results.

Actual qualifying [run40735694599](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40735694599), job122983488680, executed commitec966eb315a4958b61d089b737286451196b2167, real MATLAB24.2.0.3361896 (R2024b Update10). The qualifying run records compileCalls=1 and physicalRun=false.

## Source and exact permitted derivative
The source is the receipt/SHA-pinned Work B0L10ms four-ToFile SLX from40701917441. Its bytes and the exact vendor SLX remain unchanged (vendor tag24.2.1.5, commitf98d21929a3a269dacd1ee38999cd9773760c6db, public vendor SLX SHA0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0).
Only the separate clone changes:
-StopTime2400->340; original numeric start0 and literal source string0.0 retained.
-Four distinct fresh owner-private MAT targets.
-Commented off->on for JTE Command/jteUcore, JTE Downstream Flow/jteFlwR and JTE Vector True/jteTtrue. The other three workspace observers remain active.

Each retired observer was verified to use the SAME actual output-port handle as its corresponding ToFile replacement, with inherited sample time, Decimation1, Timeseries and no sample-count cap. No label-only equivalence assumption was used.

## Actual proof checks

| Check | Result |
|---|---|
| Nominal block inventory with IncludeCommented on |236 source /236 target; PASS |
| Retained block/dialog/config values after only whitelisted adjustments |PASS |
| Full signal/physical connectivity and original wire names |PASS |
| Model workspace and Stateflow/controller scripts |PASS |
| Independent saved XML: only StopTime config change, same complete physical nets/block SIDs |PASS |
| Saved XML: exactly3 off->on comments,4 target changes |PASS |
| Four private targets distinct/inside fresh private folder/absent after compile |PASS |
| Actual commented-observer CompiledIsActive |off for all3 |
| Included host/cgroup/disk/Drive and bounded-stop policy screen |PASS for proposed bounded observation, not peak prediction |

Actual compiled inputs:
| Role | Width/type | Sink rate |
|---|---|---|
| uCore |1 double |continuous[0,0] |
| uSampled |1 double |[.01,0] |
| actuatorY |1 double |[.01,0] |
| Ttrue312 |312 double |continuous[0,0] |

For every role, both sink AND source-block attributes (type,width,compiled rate,unit metadata) equal the archived actual40701917441 MATLAB proof. The original controller rate set is retained. Source cooling and auxiliary electrical paths remain intact. Actual dynamic event behavior/file timestamps have NOT been observed.
Source compiled SI-label gaps and FlwT Unit1/K ambiguity remain disclosed; source/SSC unit contracts are inherited, not newly measured. No real pump power or energy saving is inferred.

## Reviewed bounded-observation plan
The companion M2_340_WITNESS_AND_STOP_PLAN.md fixes the one-shot scope: original300K/source current/B0L10ms0-340; effective runtime cap check; fresh file absence; no faults,load phase,Tref,physics,solver or coefficient change; one initialization/instance; no retry.
It separates x[k], y[k] and postupdate x[k+1], requires t0/first completed-major and330-338 witnesses with330-334 control, and preserves every native file clock/duplicate actually produced. Callback phase is not an accepted continuous solver step.
Hidden operating-point coverage cannot be established from static workspace equality. It must be observed/qualified at runtime, with missing coverage explicitly retained and no thermal/G5 claim. Actual peak RAM is likewise a measurement of the first approved observation, not an impossible pre-run numerical prerequisite.
The external live watcher must be active before any approved initialization. The reviewed operational policy retains2GiB RAM/disk reserves,1GiB per file/2GiB total native-file ceiling,512MiB Drive delivery reserve,1200s trajectory wall ceiling and300s delivery time reserve. Limits mean stop/incomplete UNQUALIFIED, never dropped samples, clipping or an automatic second attempt. These are operational stop ceilings, not success/runtime predictions.
Actual cgroupv2 is available; where memory.max is unbounded, host-available RAM is the relevant budget. Service cgroup memory.peak includes job/cache activity and is not a physical-plant peak. No watcher or plant was started here. No full2400 all-state history budget is demanded for this340 feasibility.

## Code fixes and retained failure history
The Chat proposal04a22d9.../review7ea3905... were read in full. Work added actual-port redundancy guards, B0L-only/fresh-directory constraints and complete before/after/compile proof.

-40726398454/336ea79: Work omitted the fourth source-SHA argument. Constructor stopped before copy/compile. Fixed to pass the exact receipt SHA.
-40727204019/15e706c: source StartTime is the valid pinned string0.0, whereas the proposal compared text0; an ID-only assert also masked its intended diagnostic. Fixed numeric-zero validation and complete identifier/message assertions while retaining the literal source configuration.
-40728513554/dc65bc8: public flags report static rejection/no physical run, but the publisher failed before preserving the private traceback and cleanup removed that attempt's scratch. Exact private traceback/compile count cannot be reconstructed and is not invented. The later schema diagnosis is independently supported, not retroactively labeled a recovered traceback.
-Read-only40733393884 attempted to find new ToFile rows in the saved prior audit b, which deliberately excluded them. Corrected40733781015/384bc3f verified all4 actual saved-XML Filename fields and4 synthetic schema handling tests, no MATLAB/compile.
-The reader wrongly demanded case-sensitive FileName rather than actual Filename. It now resolves exactly one matching property without relaxing allowed-value differences. The publisher archives raw console/flags/model/proof before deep interpretation, so interpretation errors no longer suppress those existing artifacts.
-40734077464/4d5d7d8 private flags record compileCalls0 and a raw-versus-canonical path comparison defect. The audit replaces a model token with $ROOT; expected paths now receive the identical normalization, with an additional exact raw get_param filename check.
-find_system defaults to excluding commented blocks. A separate nominal auditor explicitly includes them; prior shared JTE096 audit behavior is unchanged. This prevents permitted observer inactivity being mistaken for node deletion. The actual compile separately proves their inactive status.
-Superseded40734657734/df19524 is not accepted evidence; final evidence is40735694599. No failed/skipped/cancelled run is relabeled PASS.

None of these changes modifies the source law,solver/tolerances,physical plant,load,reference or sensor bias. No old G1-G4,accepted actuator8/8 toy,source baseline or fault case was rerun.

## Private delivery and stop
Private Drive contains the new SLX, complete JSON/MAT proof, precompile audit/diff, console, flags, XML parity, host/stop policy, input manifest and witness plan. All13 output files have full remote byte SHA/readback with a private receipt.
The remaining authorization condition is **OWNER_EXPLICIT_PHYSICAL_APPROVAL_REQUIRED**. No further static sweep is proposed to pretend to measure peak RAM/solved IC. A future expressly approved physical run must activate the reviewed guards and collect those runtime witnesses.
A clean340s run can yield FIRST_WINDOW_CONDITIONAL only. Full second-event study,fixed-Ts solver refinement,Ts implementation sensitivity,312-channel thermal uncertainty and C0/C1 causality remain separate scientific gates. Re-evaluate fault feasibility on a qualified amended baseline; JTE109 remains archived-original-state-specific.
Original-source G5 remains thermal-rejected; amended physical model remains unqualified. No merge,paid service,automation,official report export or physical dispatch follows this delivery.

Primary API reference for the commented-block audit: https://www.mathworks.com/help/releases/R2024b/simulink/slref/find_system.html
