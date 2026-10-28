# JTE116 actual execution — canary and static scope only

**GUARD025_CANARY_STATIC_PASS_AWAIT_OWNER_SIM_AUTHORIZATION**. **G5 remains BLOCKED / NOT ACCEPTED.**

## Actual new MATLAB test
- Run [40633425452](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40633425452), job122634837594, commit a188cd969da0b72e289b051eb2e3333b7ce0d385.
- Unchanged PR56 JTE116_guard025Canary: strict source/guard bitwise PASS; exact subfloor floor output and unchanged above-floor operands PASS on R2024b Update10.
- Existing SHA-verified JTE115 diagnostic was actually read and its mismatch ranges classified. Counterexamples, range counts and scalar data remain owner-private.
- This is the ONLY new JTE116 canary invocation. NumPy and prior JTE094 suites were not rerun.

## Final static proof and delivery
- Run [40635052627](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40635052627), job122639983551, commit26069fa77e5f2089ab0d103538eb271901521361.
- Actual flags: CANARY_BITWISE_PASS=1 (reused exact bytes), STATIC_MODEL_PARITY=1, COMPILED_DOUBLE=1, CONVERTER_TOPOLOGY_AUDIT_COMPLETE=1, PHYSICAL_SIMULATION_STARTED=0, OWNER_NEW_PLANT_AUTHORIZATION=0, G5_ACCEPTED=false.
- Exact retained-block parameters/source config and outside-local-guard graph passed. Original/vendor/load/workspace pin checks passed; complete saved source IC map retained. Solved guarded IC is still unverified without a trajectory.
- Builder differs behaviorally from the inherited version only by Constant Value0.375->0.25. Source final Max/Mod/TF/physical graph and converter settings remain unchanged.
- Compile/term proved double operands without advancing a plant trajectory. Separate private guard025 SLX, static proof, prepared MAT, audit, logs and manifest were saved.
- Owner-private receipt verifies full remote SHA readback for every delivered file. Reused canary MAT SHA equals the original new-canary PASS receipt. No private hashes/IDs/paths or research values are published here.

## Software preparation failures preserved transparently
- Initial literal converter discovery stopped with NoConvertsFound before clone creation.
- Static run40633941887 had a publisher schema bug caused by an overbroad trigger-string replacement. Its private static failure details were not preserved. No physical data existed. Fixed exact schema; private live upload/readback probe now precedes MATLAB.
- Run40634498001/job122638218151 at72a0acea056ec4b53d7b1755a6bf1ec1a857b31c preserved InputPortUnavailable at the read-only source audit. Final discovery normalizes canonical mask/reference LEAF names and records unavailable objects rather than inventing topology. Final complete audit and source/guard report parity passed.
- All static continuations reused the one passed canary, code SHA and range ledger. No second canary, physical simulation, solver comparison or old suite rerun occurred.

## Next gate
The corrected guard025 plant design has not received separate owner simulation authorization under JTE116 item3. The prospective one original-ode23t B0L0–340 diagnostic is frozen in CANARY_STATIC_AND_PROSPECTIVE_PROTOCOL.md and uses saved Original340 instead of rerunning it. Await explicit owner approval before implementing/consuming a plant intent.

Native/callback rows must not be relabeled accepted-major. The prepared normal-driver plan has no independently certified accepted-major provenance; this limitation must remain explicit in any approved conditional diagnostic. No second-event coverage, independent numerical convergence, true-temperature causality or G5 acceptance follows from canary/static PASS.

No merge, payment, automation, new G6 or official manuscript/report export. JTE115 guard375 stays rejected; JTE113 stays UNQUALIFIED before time advancement.
