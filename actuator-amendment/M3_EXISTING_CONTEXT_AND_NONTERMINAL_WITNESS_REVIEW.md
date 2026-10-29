# M3 existing-context audit and alternative witness design

Engineering review only. No MATLAB or battery execution in this change.

## Existing execution context
The actual fixture at commit fc77f201 creates a new toy model with new_system, sets ode23t/MaxStep/StopTime/Refine, and does not explicitly set or save SimulationMode. The only model callback it adds is StartFcn, which installs PostOutputs/PreUpdate/PostUpdate listeners. The listener code reads DWork/input/output and streams phase rows; it has no stop or terminate call. The fixture calls stop(s) only after the helper and final-horizon assertion; the observed M3:Clock rejection occurred inside that helper, before stop(s). onCleanup closes the model when the function exits, not during the failing step. No Stop Simulation block or completion-triggered stop code is created by the fixture.

These source facts rule out an explicit stop call in the shown path before the rejection. They do not prove the compiled runtime's SimulationMode, hidden callbacks in libraries, or solver termination reason. The saved partial lifecycle shows finalstep true, terminal inactive and returned Time unavailable; its four native clocks reached the toy horizon. The run did not save SimulationOutput.SimulationMetadata.ExecutionInfo or a get_param SimulationMode value. Neither can be reconstructed from ToFile or a first-paused operating point.

Official R2024b step documentation says normal/accelerator final step ordinarily pauses; rapid/deployed stop. The observed inactive status is therefore an unresolved mode/runtime discrepancy. An empty ErrorMessage alone cannot explain it. Do not treat the Chat terminal-inactive allowance as qualified solely from this archive.

## Nontermination-dependent future protocol for review
1. Freeze exact model/mode/solver/StartTime/StopTime/callback inventory and source SHA before initialization. Store private SimulationMetadata.ModelInfo.SimulationMode and ExecutionInfo.StopEvent when available. Preserve current hidden-t0 limitation explicitly.
2. Use documented Simulation.step only while the return is nonterminal. Before each step retain the prior top s.Time; after it returns require finalstep=false, Status=paused, finite/nonregressing next s.Time, and a phase-aware native state/output witness at the processed prior top. The accepted-major interpretation is limited to these documented completed, nonterminal steps.
3. For a prospective 340-second physical observation, complete and save major-step witnesses through the event interval 330–338 s while still before the 340 s terminal step. Then resume the same paused simulation to the frozen stop time without asking for a terminal next-top Time. Retain all four independent ToFile native clocks through final time; verify full SHA readback. Do not recast ToFile samples as accepted solver steps.
4. Treat the terminal step as a separate completion receipt using finalstep, frozen horizon, ToFile tail clocks, ExecutionInfo.StopEvent, actual mode, Status and ErrorMessage. If metadata cannot reconcile inactive with the documented mode, terminal lifecycle remains UNQUALIFIED even if saved native samples are complete.
5. Hidden physical t0 requires an independently reviewed operating-point or full-state witness. First-paused OP is not t0; block-reduction restore warning remains unresolved. A clean first event would only be FIRST_WINDOW_CONDITIONAL, not G5.

No new probe, physical run, solver change, G5 acceptance, merge or manuscript is authorized by this design.
