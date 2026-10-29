# M1/M2 internal engineering handoff — 28 October 2026

Review-only technical record. JTE058 remains active; this is not a manuscript, submission report or official research-results export. No toy/battery simulation, model compile, library build, solver sweep or model edit was performed for this request.

## Exact evidence and execution

Pinned vendor commit: f98d21929a3a269dacd1ee38999cd9773760c6db (tag24.2.1.5).
Pinned public source SLX SHA256: 0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0.

Static collection [40692041954](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40692041954), executed commit f3b34e7fb73945bfc0c6d0d9115c29190e17c208: source SLX and four saved amended B0L/C0 x10/5ms model bytes are linked to existing private SHA/readback and prior actual R2024bU10 compile receipts from40659584085. Original graph extraction40691093123 is reused. No model was loaded in MATLAB.

Final path interpretation/certificate: [40693084138](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40693084138), job122832643976, PASS static two-path certificate/private full SHA readback; executed commit f39d580d1d6c98556977ba5e619e6929e5e311ea. Status must be read with the actual run and private receipt, not inferred from CI alone.

## M1 static finding and limits

Both branches originate at the same post-actuator output in source and all four amended models.

1. FlwR -> control bus -> Input Data Split -> Battery Pack FlwR selector -> Flow distribution to different modules -> R1...R8 Goto/From -> FlwR1...FlwR8 Simulink-PS converters -> module frac_b -> thermal LUT. Exact pinned SSC declares frac_b dimensionless and evaluates the mass-flow lookup coordinate as frac*max(Fvec), with Fvec in kg/s. The per-module multipliers are 1,.9,.8,.7,.7,.8,.9,1 in module order. Unity values use the documented R2024b Gain default where the SLX has no override. This is lookup-based heat transfer; the gain vector is not a claim of sum-to-one division or a solved conservative hydraulic network.

2. The same FlwR output -> Pump power calc -> Gain500 -> Saturation[0,500] -> control bus Pump Power -> Input Data Split pump output -> pump Goto/From -> P Simulink-PS converter, UnitJ/s -> source DC Dynamic Load Power physical input. Complete undirected conserving nets connect that load across the two battery terminal nets, alongside the controlled current-source branch. All four amended models preserve these physical nets and retained component parameters.

The 500W full-scale relation is an explicit SOURCE ASSUMPTION. The command is not a measurement of delivered pump power or real EV pump saving. Dynamic Load operating quadrant, supply voltage and actual branch/battery current must be qualified before energy accounting. The documented DC block changes behavior below its minimum supply voltage and under reverse voltage.

The Scope label Battery current traces to filtered current DEMAND on tagDC and the controlled current source. No separate current-sensor block was found on this path; that label cannot establish total battery current including the auxiliary branch.

Replacing the original continuous1ms actuator with the already frozen sampled implementation affects BOTH cooling lookup demand and auxiliary electrical demand, at the declared10/5ms output holds. It is a method amendment, not source continuous-waveform identity. Fault-induced temperature changes cannot be attributed wholly to flow without accounting for the electrical auxiliary path. Static connections establish no actual thermal effect or energy saving.

Prior compile receipts support scalar double actuator/hold,312 true-temperature channels, declared sample times and unchanged retained unit metadata. Actuator/T312 compiled unit strings are empty; metadata parity is not an explicit compiled SI certificate. Source FlwR converter Unit1 and SSC fraction/kg/s contracts support the static normalization interpretation separately. Retained FlwT converter Unit1 versus SSC delT_b K remains disclosed and was not silently changed.

M1 status: PASS for the static two-path graph and four-model preservation; explicit compiled SI-unit labels UNAVAILABLE; physical timing/thermal causality UNQUALIFIED.

## M2 design and NO-GO

The private handoff specifies one-copy Ttrue312 Dataset logging to MAT via R2024b classic batch sim(SimulationInput), separate native clocks/duplicates, scalar raw/held/output/core and explicit discrete pre/post-update ordering. Duplicate legacy ToWorkspace/full-state/Scope/SDI histories would need a reviewed logging-only diff on an isolated instrumentation copy. None was changed or run.

R2024b persistent storage cannot be assumed compatible with Simulation Stepper or fast restart. Logging-to-file support for Simulation objects was added in R2025a. Legacy Timeseries ToWorkspace buffers are not automatically redirected into persistent Dataset storage. A compatible complete solved initial/accepted physical checkpoint path, bounded writer and actual peak memory remain unqualified.

Real host/disk/Drive metadata and the existing rejected-source runtime are archived privately. They are not an amended runtime benchmark, free-time guarantee or peak-RAM proof. Schedule row counts give no upper bound on solver/native records; no fabricated runtime or memory PASS is asserted.

M2 status: design delivered; NO_GO_MINIMAL_LOGGER_RUNTIME_AND_FREE_HEADROOM_UNQUALIFIED. Full2400s also remains NO-GO. No one-shot340s battery execution was dispatched or newly authorized.

## M3 / scientific decisions unchanged

The existing highest-computed-RMS340s source segment remains a proposal only. FromFile interpolation/polarity, complete physical IC and battery SOC/voltage/current/thermal-table domain need qualification. No current-load waveform, faulted group or source controller was changed, no favorable channel was reselected, no new293.15K load was invented.

Original-source G5 remains rejected/unqualified for thermal claims; amended physical G5 UNQUALIFIED. Toy technical pass and JTE109 exploratory baseline results are retained without repetition. Scientific acceptance belongs to Chat/owner.

## Software defects fixed transparently

-40691093123 retained all five graph files and four prior compile proofs, then stopped because initialPackSOC is absent in the saved workspace. The static reader now records that field UNAVAILABLE and preserves actually saved iniSOC1...8; it does not invent a workspace field.
-The original directed edge view omitted physical DEST_DEST nested Src peers. The final certificate uses complete undirected conserving hypernets from raw XML, preserving all Src/Dst peers. The physical source files were not changed.
-40692831279 stopped at an exact edge assertion because its certificate incorrectly reused B0L-created actuator SIDs across C0 model files. The corrected reader resolves the unique block path within each actual model, then verifies its actual local SID and wires. No assertion was weakened and no plant was rerun.
-All failed attempts and private receipts are retained.

## Private evidence and stop

Owner-private Drive contains per-model raw graph supplements, actual source SSC/workspace evidence, reused compile proofs, resource evidence, path certificate, input manifest, design and full SHA/readback receipts. Public contains code/status/run/commit and the pinned public-source facts only. Research values/models/MAT and OAuth credentials remain private.

No merge, paid service, automation, new simulation, G5 acceptance or paper export follows this delivery.

Primary sources:
- [R2024b persistent storage](https://www.mathworks.com/help/releases/R2024b/simulink/ug/log-data-to-persistent-storage-1.html)
- [Logging version history](https://www.mathworks.com/help/simulink/gui/logdatatofile.html)
- [R2024b Gain default](https://www.mathworks.com/help/releases/R2024b/simulink/slref/gain.html)
- [R2024b Dynamic Load behavior](https://www.mathworks.com/help/releases/R2024b/sps/ref/dynamicload.html)
- [Exact vendor battery module SSC](https://github.com/mathworks/Battery-Pack-Model-Simscape/blob/f98d21929a3a269dacd1ee38999cd9773760c6db/Libraries/%2BbatteryModule/batteryMultiDimModel.ssc)
- [Exact vendor thermal LUT SSC](https://github.com/mathworks/Battery-Pack-Model-Simscape/blob/f98d21929a3a269dacd1ee38999cd9773760c6db/Libraries/%2BbatteryModule/batteryCellThermalLUTmodel.ssc)
