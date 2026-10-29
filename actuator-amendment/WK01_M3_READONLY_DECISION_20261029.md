# WK-01 — M3 read-only decision and witness contract (29 Oct 2026)

**Decision: WK01_M3_NO_GO.** This is an engineering review, not a MATLAB or battery run. JTE058 remains active.

## Single decisive blocker

The archived 30 ms toy returned `finalstep=true`, terminal `Status=inactive`, and unavailable `Simulation.Time`, while all four native To File clocks reach the toy horizon. The executed source never saved the effective `SimulationMode` or `SimulationOutput.SimulationMetadata.ExecutionInfo.StopEvent`. Both values are **UNAVAILABLE**, not reconstructed. R2024b documentation says a last `step` in normal/accelerator mode ordinarily pauses and a rapid/deployed run stops. Thus the observed inactive lifecycle cannot be classified against a verified effective mode/stop reason. An empty `ErrorMessage` or To File tail is insufficient to close this gap.

The shown fixture creates a new model and does not set or save SimulationMode. Its `StartFcn` installs three read-only phase listeners; these do not call stop/terminate. The explicit `stop(s)` is after the helper that rejected the missing `Time`, so it did not cause that rejection. The saved first-paused operating point does not contain a full t0 proof. These source facts do not establish the effective compiled mode or an internal completion event. The earlier Chat terminal-inactive patch remains an unmerged review candidate.

Evidence reused, not rerun: [protected read-only run 40800167858](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40800167858), job 123206095820; [PR62](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/pull/62); [M2 static run 40735694599](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40735694599); prior watchdog 19/19 [40741741900](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40741741900). No new run/job is claimed for WK-01.

## One alternative witness contract for review

1. **Immutable source and derivative.** Record MathWorks tag24.2.1.5, vendor commit `f98d21929a3a269dacd1ee38999cd9773760c6db`, SLX SHA-256 `0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0`; verify the exact approved B0L10ms 340s clone SHA against its owner-private M2 receipt at job start and after delivery. Freeze source/load/current input, controller reference 300 K, full model/solver/actuator configuration and Start/Stop time. Log both configured and effective `SimulationMode`, callback inventory, source/clone SHA and model checksum privately before initialization.
2. **Nonterminal completed-major witness.** Before each `step`, save `processedPriorTop=s.Time`. After return, accept a major-step witness only when `finalstep=false`, `Status=paused`, a finite nonregressing next `s.Time`, and exact role-specific native signal/phase clocks at the processed prior top. Record core, held command, actual actuator state/output, T312, duplicate timestamps and phase order. A callback phase is supporting state evidence, never an accepted solver step by itself. Predeclare windows 330–334 s negative control and 330–338 s event; preserve their nonterminal completed-major records separately.
3. **Terminal receipt, separate from major-step evidence.** After the last nonterminal witness, continue the *same* simulation to the frozen horizon. Do not invent a next major time from terminal `s.Time`. Save actual `finalstep`, `Status`, returned `Time` availability, `SimulationOutput.ErrorMessage`, `SimulationMetadata.ModelInfo.SimulationMode` and `ExecutionInfo.StopEvent/StopEventTime` if supported in the exact runtime. Independently verify all four To File native clocks and final samples with original duplicates. An inactive normal-mode terminal with unresolved provenance yields `UNQUALIFIED`, even if To File reaches the horizon.
4. **t0 and initial-condition gate.** First-paused OP is not t0. Before any physical interpretation, demonstrate a supported R2024b capture or restore mechanism for the full physical/Simscape continuous and discrete operating point at t0, including an inventory of unavailable hidden states. Compare B0L/C0 from the same complete IC and source configuration. If full t0 cannot be certified, mark thermal/causal claims unqualified. Do not reconstruct hidden states from only T312.
5. **Failure and private delivery.** The MATLAB action must exit nonzero for any `UNQUALIFIED` logger flag. An independent `if: always()` publisher still retains private flags, raw lifecycle, phase trace, four To File streams and error ID. Require fresh owner-private filenames, input/output SHA-256, full remote-byte readback, receipt and cleanup. CI publisher SUCCESS never converts an unqualified MATLAB trajectory into a scientific PASS.

This is a contract for a separately reviewed logger alternative, not an instruction to run it now.

## Current rights/resource checklist, without spending the physical approval

| Gate | Current evidence | Required before any new physical dispatch |
|---|---|---|
| Protected `JTE_DRIVE_WRITE` access and OAuth | PASS at prior run40800167858 / last M3 publisher; current state not revalidated | Protected context, private sink and readback in the actual future job |
| MATLAB R2024b Update10 license | PASS in prior synthetic run40798122691 | Exact runtime/license in future job |
| Static M2 clone parity | PASS at run40735694599 | Exact clone SHA/readback and source pin in future job |
| External watchdog | 19/19 prior PASS at run40741741900 | Running before physical initialization with preserved stop policy |
| RAM/disk/Drive headroom | Historical bounded screen, actual physical peak unavailable | Current cgroup/host and private quota/headroom, one-shot abort margins |
| Logger mode/stop/t0 | **FAIL/UNAVAILABLE** | Independent accepted nonterminal witness, terminal provenance and full t0 plan |
| Owner physical one-shot | Existing exact B0L10ms0–340 approval unused | Verify the existing approval scope still matches the qualified model and gates; do not dispatch under WK-01 |

**Stop state:** No toy, pack, C0/C1, 2400s, solver/actuator rewrite, accepted-suite rerun, paid service, public MAT, merge or official results export. G-M3 is UNQUALIFIED and G5 is NOT ACCEPTED.
