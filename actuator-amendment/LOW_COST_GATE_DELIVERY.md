# Internal technical delivery — one toy and archived baseline map
Date:28Oct2026. Review-only engineering handoff; not manuscript/submission/official research-results export. JTE058 remains active.

## Closed decisions
Original-source G5 remains FINAL REJECTED/UNQUALIFIED FOR THERMAL CLAIMS. No source solver/Mod/guard/continuous-StateSpace remedy was attempted in this package. No battery simulation, G6/C0/C1 dispatch, cost/secret/protection change or PR merge followed.

The one completed non-battery MATLAB horizon was run40683965769, job122801478535, executed commit44ff300275234b169a1461e5b58203a2f1d33c8a, MATLAB R2024bU10. It contains both frozen10/5ms implementations and four fixed synthetic patterns at each rate. This does not establish continuous waveform identity, hardware timing/flow units or thermal convergence.

Technical native criteria are PASS for8/8 branches by final read-only run40685753141/job122807540459/commitcbb2d66a9729a3d657dca923b221846789bcfff2. Independent scientific/method acceptance belongs to Chat/owner. G5_ACCEPTED=false and modelMethodApproved=false.

## Native-clock guard diagnosis, not edited evidence
The original toy export guard wrongly required raw input, sampled ZOH input and dense actuator output to share an identical clock. Actual sampled input is recorded at its declared10/5ms sample hits; raw input and actuator output have their own common faster observation clock. This is a software assertion defect, not evidence that these distinct role clocks are ambiguous or that the discrete model failed.

The original Gate:ToyClock/UNQUALIFIED flags remain immutable. Read-only run40684987494/job122804911480/commitae6032671f42e70e5fa2fdc048b88f3af1c1b15b extracted exact original clocks/values, preserving duplicates and17-digit CSV precision. It validated actual PostOutputs/PreUpdate/PostUpdate state/input/output staging and continuity against an independent80-digit Decimal ZOH oracle, with gamma3 local arithmetic and separately propagated coefficient representation error.

Final role-clock run40685753141 reuses those native-math receipts and checks each logger on its own recorded clock:
- Raw clock/data exactly match the declared fixed synthetic input.
- Sampled input clock/value exactly match the actual update trace.
- Raw/output native clocks agree; all real between-hit output observations equal the last actual output write.
- Startup x0, double-state recurrence, step/return, captured pulse and missed sub-Ts pulse behavior are supported.
No timestamp was interpolated, deduplicated, replaced or relabeled as an accepted battery solver step. No new trajectory was run for postprocessing. Final status is TOY_TECHNICAL_NATIVE_CRITERIA_PASS_REVIEW_REQUIRED, not independent scientific acceptance.

## Archived baseline JTE109
Run40668084392/job122747609380/commit05d64995fe857bfd6af9012c4922b67c63c7c0ed completed actual native MATLAB source-law/cardinality processing of source300K B0L/C0 original/fine and separately supplementary293.15K C0. All original/fine B0L/C0 full native clock/T312 identities and k_min maps agree.

Primary300K flags: no qualified subset<=1 or<=3 at stored states for delta2/3K; all k_min>3 or infinity; no unresolved threshold ambiguity. Decision NO_ELIGIBLE_SMALL_GROUP_IN_CURRENT_BASELINE. This is fixed-stored-state exploratory control feasibility, not physical null effect, continuous-time safety or thermal truth.

Supplementary293.15K retains its own near-boundary/unresolved flags; it is not combined with the primary verdict and is not a second physical load. No active B0L is invented. No nine-C1 audit or prior simulation/synthetic suite was repeated.

JTE042 ranking is B0L-only1800-2400 time integral, descending mean with exact-tie ascending channel index, literal ranks1/156/312. The output preserves reconstruction assumptions and unqualified source thermal semantics; ranks remain exploratory, not confirmatory protocol reproduction or relabeling of legacy cases.312 model channels are not established as312 physical sensors.

## Exactly one prospective input proposal
Read-only run40683303822/job122799234228/commitc875f37780629c692bf8ce0d24fd8af5bd4ee3aa qualified the public pinned source input encoding and completed a bounded cumulative-panel RMS screen. It proposes only the340s highest-computed-RMS contiguous segment of the existing source current trace, earliest native start for exact score ties. Source amplitudes/polarity are retained; only demand phase changes. All scalar values, interval and source/data hashes remain private.

Status ONE_SOURCE_CURRENT_SEGMENT_PROPOSAL_OWNER_REVIEW_REQUIRED. This is not a validated operating envelope or guaranteed controller activation. Actual FromFile interpolation/polarity, SOC/voltage/charge/table/rating domains, method/Ts/flow-unit interpretation, minimal logger/free resources and independent numerical-reference plan still require review. No input file or physical run was created for this proposal.

Because no informative current-load small-fault case is established, no short battery baseline or confirmatory C0/C1 plan is dispatched. This remains NO-GO until a scientifically informative approved regime exists. Full2400/dual-window/fixed-Ts solver and sampling sensitivity/312-channel thermal uncertainty/causality remain unqualified.

## Failure history and minimal fixes retained
-40668084392: baseline map completed; toy setup rejected invalid SignalStorageReuse before simCount increment (zero calls).
-40669078761/commitc9df69ebee56938faa6f484fb77343841c60aa59: documented OptimizeBlockIOStorage used; toy call rejected before events by conflicting FromWorkspace extrapolation with interpolation off. A later oversized public-input scan was stopped by operational run40670148772/commite60d78ab7b87f8791a48912ae73cef717e35abaa. Existing always-private publication retained all saved files and full readback.
-40683303822: compiling the immutable failed toy without simulation reproduced all nested FromwksNoExtrapWithoutInterp causes. The corrected tail behavior is Holding final value, keeping interpolation off and all in-window inputs/Ts/coefficients unchanged. The input reader was replaced by bounded cumulative-panel integration, not a repeated simulation.
-40683965769: compile guard passed and one complete toy horizon ran. The old common-clock assertion then failed; its evidence is preserved and independently reviewed on the proper role clocks as above.
No completed toy was rerun. All unsuccessful pre-execution attempts, code commits and receipts remain traceable.

## Private delivery and stop
Owner-private Drive holds original MAT/model, complete event traces, scalar native CSVs, update states, independent oracle/math and role-clock checks, baseline row ledgers/lossless subset masks, rankings, input proposal, manifests and full SHA/readback receipts. Public only safe procedural/status metadata, commits/runs and code.

Toy execution workflow gates are closed after this delivery; explicit fresh owner authorization is required for further execution. Temporary own-run cancellation workflow is removed. No new paid service, automation, merge, physical run or JTE058 paper/export is authorized by these technical passes.
