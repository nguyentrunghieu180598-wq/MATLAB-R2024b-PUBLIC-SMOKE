# JTE116 bounded canary and static preparation — not G5

## Authorized execution in this change
Read the SHA-verified archived JTE115 synthetic diagnostic and classify its actual mismatches by q range privately; do not infer or invent specific failing q values. Run the new PR56 JTE116_guard025Canary exactly once on R2024b Update10. Keep source inputs/RNG/strict bit comparison unchanged. Stop if it fails.

If and only if it passes, prepare a separate source-derived guard025 clone and static/compiled-double proof. This workflow contains no sim call, plant intent, actuator trajectory or new solver study. It cannot grant itself permission to run the corrected plant design.

## Existing evidence reused
- Actual standard Mod/Sum/Max fixture run40301939641/job121501673756 logged matchesMATLABMod=1 and matchesThreshold=0. Overall failure was rejection of a naive threshold replacement; it does not reject preservation of original mod arithmetic.
- Atomic original-law fixture run40303063260/job121505386117 logged originalDoubleOutputsExact=1; finite fixture scope, not universal event/solver equivalence.
Neither suite is rerun. JTE115 guard375 remains rejected. JTE113 remains unqualified before time advancement.

## Review scope
Committed PR56 canary source d07a4d23ea664544ef8dc9a352ec3023a87dd64e is used verbatim. The attachment has the same test logic with local naming/comment differences. The supplied Python synthetic test/log were read; NumPy results are not MATLAB evidence and are not rerun.

The builder inherits the corrected JTE115 builder. Beyond renaming its function and precondition comment, its sole behavioral edit is Constant Value 0.375 -> 0.25. Existing JTE115 local guard block names are deliberately retained so that the inherited exact edge-difference assertions stay unchanged.

Source/vendor/model/load/workspace SHA, original ode23t/tolerances/reset/ZC/initialization policy, final Max, mod, TF/tau, converter configuration, retained block parameters and graph outside the two q input edges must be exact. Compile/term checks double operands without advancing simulation time. Solved guarded Simscape consistent IC is not established by a static check.

All scalar ranges/hex counterexamples, models/MAT, logs and manifests remain owner-private with full SHA readback. Public safe flags and execution references only. No paid service, merge, G6 or official manuscript/report export.

## Prospective one-plant proposal — requires separate owner approval
Only after actual canary/static/readback PASS: one original-source-derived B0L guarded025 0–340 normal-driver simulation; source ode23t MaxStep0.05, original RelTol/AbsTol/reset/ZC, exact archived original source workspace/load/300K reference/IC policy and original TF retained. Reuse JTE101 Original340 from run40449421507; never rerun it.

Preserve full native q/qStar, actual TF input, core, continuous state/output and all312 Ttrue; retain duplicate clocks and no interpolation. Require per-row original arithmetic vs actual guarded output bit equality and identical actual input/core. Verify entire saved t0 state map, T312 initial row and TF x0/y0 against original. A failed parity check rejects interpretation.

Predeclare first330–338 anomaly and330–334 negative-control analyses, startup/global separately. Conditional analytic envelope uses actual saved y0 and supported bounded-input/no-reset assumptions;32ULP is interval localization only. Historical .005 core/output gap is localization, not thermal/solver acceptance. No post-hoc sample removal.

Normal-driver native records do NOT certify accepted-major steps. An accepted-major provenance mechanism is UNAVAILABLE in the prepared implementation. Any owner approval must acknowledge this limitation or require a documented mechanism before trajectory execution; do not invent callback/accepted-step equivalence.

Plan current free public GitHub hosted/included MATLAB execution and private sink only, one bounded job with no retry. Recheck current RAM/disk/private capacity, restore frozen initial workspace and consume an explicit one-shot plant intent after approval. Full file upload/readback limit4GiB; initial private original raw is reused, not regenerated. Resource exhaustion returns UNQUALIFIED and never triggers another solver.

Outcomes: event persists -> STOP Mod/solver manipulation and numerical-suitability review; event absent with parity intact -> CONDITIONAL first-window result only, not G5, not second-window/thermal/independent convergence. No physical run is enabled by this document.

## Actual first execution and static-only discovery fix

Actual run40633425452/job122634837594 at a188cd969da0b72e289b051eb2e3333b7ce0d385: ARCHIVE_CLASSIFIED=1, CANARY_BITWISE_PASS=1, PHYSICAL_SIMULATION_STARTED=0. The unchanged committed JTE116 canary passed in real R2024bU10; saved subfloor and unchanged-above-floor gates passed. Private full SHA readback succeeded. Static preparation stopped before the builder at JTE115:NoConvertsFound.

The inherited converter detector used a literal display-name substring; it cannot certify absence of converters when library names contain formatting differences. The corrected read-only detector normalizes mask/reference name formatting and accepts the documented derivative-parameter contract as another discovery predicate. Nonempty discovery and readable FilteringAndDerivatives/UdotUserProvided remain required; no converter setting changes.

The static-only continuation reuses the exact SHA-linked passed canary MAT, code SHA, prior summary/receipt and range ledger. It does not call the canary or recompute the prior range classification, reserve another canary, run old suites or start a plant. No approval is required for this code/static preparation fix; new physical simulation remains separately gated by owner approval.
