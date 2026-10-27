# JTE107 — stored-native mechanism explanation only

W107-01 reads the SHA-verified JTE106 receipt, RESULTS.json, SOURCE_LAW.json and exactly the existing per-case EVIDENCE.mat files on the already authorized protected GitHub runner. It does not run MATLAB, reconstruct a controller oracle, regenerate cases, rerun ideal/synthetic tests, inspect GUI/profiler, reload full T312 archives or change any source model, solver, reference, fault or outcome.

## Predeclared classification

Use stored MATLAB double arrays, preserving every raw inequality:
- D: uSameTrue != uSameFault, takes precedence even at a flagged boundary.
- A: observedLoss == 0 and no D.
- B: observedLoss > 0, no D, equal stored commands at the verified floor.
- C: observedLoss > 0, no D, equal stored commands above the verified floor.

Require exhaustive disjoint A/B/C/D coverage of finite qualified rows. No command rounding, resampling, clipping or replacement. ANY_IDEAL_OR_NATIVE_CORE_CHANGE uses actual stored native values only; no new ideal-source predictions or Python/Decimal tests.

NUMERIC_THRESHOLD_AMBIGUOUS is a separate conservative overlay: positive stored Max loss at or below the prior JTE106 temperature-operation8ULP budget (near selector L=0), or within eight double spacings at max(1, absolute input, absolute boundary) for saved true/measured Max near reference+5/reference+7.5 and saved saturated q near .25/.5/.75. q=.25 is a floor/quantizer interface marker, not an output jump. This localizes proximity, not a certified floating-error bound. Report raw categories, their ambiguous subset and counts excluding ambiguity separately. D is never silently reclassified or removed.

Counts and contiguous row-presence runs describe recorded native rows only. Their timestamp endpoints are neither certified accepted-event brackets nor duration/exposure estimates; no row proportions, time fractions, p-values or independent-replicate claims.

## Provenance, protocol and scope

Verify every input against VERIFIED Drive SHA/MD5 and the original complete JTE106 output receipt; link the per-case hash in RESULTS. Reuse its source300 original/fine full B0L/C0 native T312/clock equivalence certificates. Qualify active reference only within its archived C0 frame; do not fabricate a B0L counterpart or hidden Simscape initial-state proof.

Keep inherited JTE042 B0L last600 descending versus saved full-horizon ascending/C0 mismatch explicit. No rankings recalculated or legacy outcomes relabeled. Single-site schema JTE067 (including JTE069-produced active files) and JTE072 fixed groups remain separate strata, never one preregistered three-case estimand.

Private ledger contains counts, row-presence runs, threshold criteria, source frame/design, selection and frame qualifications, input lineage, prior results and dictionary. Upload and fully download the ledger/metadata for SHA verification; upload a private receipt. Public CI/PR contains only the owner-authorized per-case Boolean/category flags, public source reference/design, execution IDs and code — no granular numbers, Drive identifiers, research hashes, MAT contents or credentials.

## Stop

No recorded D -> NO_NEW_PHYSICAL_RUN. Recorded D -> independent Chat review only, never automatic experiment. Accepted bias-caused actuator events and causal physical/solver-resolved thermal effects stay UNPROVEN; G5 numerical acceptance and G6 temperature-claim authorization remain false. JTE058 remains. No merge, paid service, automation or manuscript/report export. Stop after the mechanism explanation.

## Numeric-ambiguity coverage correction
The initial JTE107 run retained exact raw categories but localized control boundaries only. The completion run adds the missing selector small-positive-loss boundary flag using the already declared JTE106 native-K operation budget. This can change ambiguity flags/counts, never raw A/B/C/D labels or raw D visibility. Both ledgers/receipts remain private for traceability. No MATLAB/native-core/ideal tests or physical runs are repeated.
