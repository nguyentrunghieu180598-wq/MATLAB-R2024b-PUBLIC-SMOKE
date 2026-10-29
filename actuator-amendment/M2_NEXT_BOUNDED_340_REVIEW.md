# M2 NEXT — BOUNDED B0L10ms 340s LOGGING REVIEW (28 Oct 2026)

Internal protocol only under JTE058 — no official report, article, physical run, extra paid resources, merge or public private MAT.

## Verified intake
- Work PR62 actual MATLAB R2024b U10 static run [40701917441](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40701917441), four original model-based M2 To File clones B0L/C0×10/5ms, **all compile**, four taps 1/1/1/312 double, original physical/controller and two M1 paths unchanged. Work read-only delivery [40703751211](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40703751211) linked 19 private SHA/readback resources. PhysicalRun=false. M2 static **READY**, M2 dynamic IC/clocks/RAM **NO_GO**.
- 10ms 340s exact SCHEDULED T312 payload 34001×312×8=84,866,496 bytes (time another 272,008 bytes). Continuous source T312 To File uses inherited continuous rate and MAY log many additional accepted/event rows. No schedule-only cost bound.
- Existing B0L: 6 original ToWorkspace, C0: 9; state saving off, Scope data logging off; no observer deletion previously, so separate logger-only derivative is needed.
- Work's old saved source 2400s trajectories are not valid thermal convergence evidence around two recorded events. Original G5 stays scientifically REJECTED. The new 8/8 nonbattery actuator toy checks discrete semantics only.

## Specific new Chat contribution (static code, not MATLAB-validated)
On branch `chat/jte110-g5-math-canary`, `jte-public/BTMS_M2_prepare340NoRun.m`, code commit `04a22d9b060bc677351c97c9f224ebae2cb40d57`:
- Require actual R2024b Update10, SHApinned SOURCE saved logger clone, NEW derivative and private destination.
- Restrict source model to amended 10ms actuator, original `ode23t`/`MaxStep=.05`, `StartTime=0`, `StopTime=2400`.
- Keep exactly four Work-compiled ToFile taps. Rebind to four new absent private MAT targets.
- **Clone-only observer change**: comment out ONLY known duplicate `ToWorkspace` variable names `jteTtrue`, `jteUcore`, `jteFlwR` where present. Keep every unknown sink and all physical/controller nodes. Reject precommented targets, missing canonical Ttrue, duplicate file names or source SHA drift. Original source untouched.
- **Clone-only cap**: set `StopTime=340`, preserve other solver params. Save resulting derivative SLX and SHA. **Function does not compile or simulate.**

## Work scientific audit instructions — DO NOT dispatch physical model
1. READ actual source + new function. Review sink-to-ToFile semantic equivalence against source proven paths, `Commented` behavior, source allstate/Scope/SignalLogging, R2024b `To File` mode and SaveFormat. Do not remove any sink without verifying ToFile replacement rate and signal provenance. If a label mismatch, fail closed and amend review-only code, not run source.
2. Run ONE **STATIC compile-only** check on the derived B0L10ms clone; exact before/after graph diff must allow ONLY (a) StopTime2400→340, (b) four changed ToFile private paths, (c) `Commented='on'` for explicitly duplicated ToWorkspace sink blocks. All physical and signal connections, chart source, initial workspace/IC, converter units and M1 two paths unchanged. Four ToFile taps still 1/1/1/312 at actual source clocks; no explicit sample-time new rate. Document whether commenting out observers changes compiled source rates or solver initialization/observer graph. If any change beyond allowed, **NO_GO_STATIC**.
3. Build a resource/stop procedure with actual current included host RAM/disk/Drive, no-fee cap, one attempt, 340s bound at effective model settings and independently checked output file absence. At runtime, use external cgroup/process RAM and disk/file-growth watchdog; static RAM screen cannot prove future peak. Limit total logging without clipping or sample deletion; overrun -> incomplete NO_GO. Explicitly reserve private byte readback and cleanup. This can be designed statically without a physical run.
4. For the inevitable initial-condition challenge: source-model workspace equality is not solved-IC identity. **A real short run, not another static receipt, is needed to observe the complete operating point.** Propose one owner-approved, fail-closed 0–340 B0L feasibility with t=0/first accepted-major witnesses and actuator state y0 from actual archive. If full hidden Simscape IC cannot be captured, mark that limitation and decide whether thermal correctness could be assessed by independent refinement; never invent equality. R2024b `To File` file clocks are NOT automatically accepted solver state. Logger-only code passing static checks is not permission to run.
5. One single 340s accepted-case outcome then decides: actuator envelope/recurrence and K-valid T312 clean -> FIRST_WINDOW_CONDITIONAL; persistent nonphysical deviation -> STOP, cannot claim full G5; clock/IC/resource unavailable -> UNQUALIFIED. No hidden `MaxStep` change or 'retry until PASS'.
6. Full new-model acceptance later still requires other event [2000,2400], fixed-Ts solver refinement and separate Ts sensitivity (sample clock changes implementation), 312 K thermal numerical uncertainty, and C0/C1 scientific decision causality. JTE109 archive no eligible ≤3 faults −2/−3K only applies to original 300K native states, so new baseline must be re-evaluated before C1. Any proposed highest-RMS source-current segment remains a standalone NOT APPROVED option.

### Engineering finding about M2 blockage
The existing M2 NO_GO for *actual process peak* cannot be converted into a pre-run numerical PASS without a physical run; the proper remedy is **bounded observation with hard stop** after static safety/instrumentation/host budget has been validated, not repeated compilation forever. There is no independent proof yet that this amended thermal model solves G5. Owner explicit new approval required before battery execution.

Official docs:
https://www.mathworks.com/help/simulink/slref/tofile.html
https://www.mathworks.com/help/simulink/ug/connect-blocks-programmatically.html
https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setmodelparameter.html
