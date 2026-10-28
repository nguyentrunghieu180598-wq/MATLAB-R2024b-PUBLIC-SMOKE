# M3 | Single owner-approved B0L 10ms, 0–340s physical witness
Internal engineering protocol, 29 Oct 2026. REVIEW ONLY. No actual physical run or owner Work-cloud approval claimed. JTE058 manuscript/export hold remains.

## Frozen and ALREADY PROVEN
Work MATLAB R2024bU10 run 40735694599, PR62, B0L10ms 340s clone STATIC COMPILE PASS. Physical/control/auxiliary-load graph and parameter parity, four ToFile signals uCore, uSampled, actuatorY and Ttrue312 widths 1/1/1/312 double; three redundant ToWorkspace observers commented; fresh private MAT locations and 13 SHA/readback files. Existing model and pinned source must not be regenerated or changed. Sampled actuator toy technical 8/8 PASS from prior Work. Original source G5 continuous-1ms filter is rejected for thermal claims.

## NEW actual Chat engineering, not yet runner-tested
Watchdog source at jte-public/BTMS_M3_oneShotWatchdog.py, Chat branch commit e172ff4df98687ff8423189f20a0d6c9362b1a19. It is an external Python standard-library process supervisor requiring:
- explicit environment BTMS_M3_OWNER_APPROVAL=APPROVE_SINGLE_B0L10MS_0_TO_340
- correct connected GitHub repository/branch/first run, byte SHA pin of approved private SLX
- four absent/private/unique native MAT targets and private 0700 output folder
- verified owner-private Drive free capacity, 2GiB host and cgroup RAM reserve, 2GiB scratch reserve, <=1GiB each native MAT, <=2GiB aggregate, <=1200s trajectory
- no automatic retry, no model change, no G5 PASS from process exit, UNQUALIFIED if terminated/limits reached. Run command must be supplied after '--'; never print paths, credentials or study arrays.
This script has NOT been tested on Work's runner or used to launch MATLAB. Before real use Work must run independent Python lint and synthetic process stop tests, check quota/headroom and establish approved MATLAB one-shot entrypoint and private uploader. Watchdog only guards the process; it does not validate physics, state or output.

## ONE future experiment only after explicit owner consent in Work
Source-preserving amended B0L10ms model, 0–340s, original 300K/current-load/physical IC parameters, ode23t MaxStep .05, source quantized Max law. Do not change current segment, Tref, bias, solver or add PID; do not repeat old models or launch C0/C1. External watcher starts BEFORE MATLAB initialization; verify StopTime 340 and all four target MAT paths absent just before initialize.

Use documented R2024b Simulink.Simulation.initialize/step(PauseTime=330) and completed-major step behavior. At actual t0 and first completed major record original source state/output y0, true T312, physical state evidence where available, plus actuator x[k] prior, output y[k], input u[k], x[k+1] after update. Never confuse callback phase or top-of-next-step time with accepted continuous major-step output. Preserve individually sampled ToFile native clocks, genuine duplicates, all rows 330–334 (control) and 330–338 (event). A full solved hidden Simscape state certificate may be UNAVAILABLE; retain HIDDEN_IC_NOT_CERTIFIED and no physical claim if so.

Watch memory/disk/file growth/wall while MATLAB executes and reserve at least 300s for owner-private upload/cleanup. Pause and close ToFile correctly, never overwrite files; verify actual log coverage, physical variables, model SHA and full remote byte readback before classifying complete. Do NOT call a job-timeout/OOM incomplete file PASS.

## TERMINAL decisions with no auto retry
- AMENDED_FIRST_WINDOW_CONDITIONAL: authentic completed-major/actual-source signals and physical T312 show no nonphysical excursion 330–338, all clocks and available states pass. This is only FIRST-WINDOW, NOT G5.
- AMENDED_EVENT_PERSISTS: genuine excursion -> STOP sampled actuator hypothesis; no more Mod/solver sweeps.
- UNQUALIFIED_IC_CLOCK_OR_RESOURCE: unexpected initial state, missing hidden-state evidence, bad clock, log/Drive/cgroup limit or incomplete run -> STOP and report exact block.

Full G5 requires subsequent pre-registered verification of second 2000–2400 event, fixed-Ts solver numeric sensitivity, Ts implementation sensitivity, 312-channel thermal uncertainty, and paired C0/C1 true effect. Archived JTE109 source300K max-3 negative-bias feasibility remains exploratory at source states only.

GitHub technical handoff is not Work-cloud approval, and user screenshot shows a quota/credit limit in Codex; do not promise that Work can start a new cloud run until quota allows. No paid service, automatic action, merge, raw MAT sharing, JTE058 manuscript or official report.

Official docs: https://www.mathworks.com/help/simulink/slref/simulink.simulation.initialize.html ; https://www.mathworks.com/help/simulink/slref/simulink.simulation.step.html ; https://www.mathworks.com/help/simulink/slref/tofile.html
