# JTE115 execution supplement — conditional diagnostic, not G5

Frozen Chat protocol: PR56, commit 0e91f54e8445ebcc6a97f6f270c449ab7c164329. That protocol is retained verbatim in this change.

JTE113 run40626077321 is CLOSED UNQUALIFIED: original-source ode23tb initialization required unavailable converter input derivatives; no time advancement. This study does not retry it, supply zero derivatives, or filter physical inputs.

## Code review changes

- Canary retains every original boundary/random input and RNG restoration. It requires the original equality AND uint64 bit-pattern equality; no equivalence criterion is relaxed.
- Builder asserts exact multiplicity of both replaced source edges, exact expected replacement graph, no orphans, original file SHA unchanged. Retained blocks/configuration and all connectivity outside the local guard are compared separately. Converter configuration is read-only and unchanged.
- Compile/term checks double arithmetic without advancing simulation time. Compiled double is required before the conditional attempt.
- Converter classification is a private upstream trace. Unresolved classification stays unresolved and never authorizes derivative/filter changes.
- Native source arithmetic is rechecked bitwise against the original law at every recorded study row. Source core and actual TF input must match. Complete saved initial-state map, T312 initial row and TF initial state/output must match the existing original comparator.
- Private preparation full SHA readback precedes a distinct one-shot JTE115 intent. A failed canary/static gate never reserves or enters the study. No automatic retry.

## Clock and driver limits

Use normal sim with source original ode23t/MaxStep/tolerances and identical runtime logging overrides to the archived JTE101 normal-driver comparator. No old source trajectory is rerun. Do not introduce the JTE113 stepping driver as another numerical variable.

Native times, duplicate rows, q/qStar, final core, actual TF input, TF continuous state/output and all312 thermal observations are retained. Native rows and callbacks do not certify accepted steps. Accepted-major provenance remains UNAVAILABLE unless independently documented evidence is present; this implementation makes no accepted-step claim.

The .005 command-gap localization and32ULP conditional envelope are not thermal convergence tolerances. Startup/global flags, first330–338 window and330–334 negative control are kept distinct in the private record. No per-channel thermal contrasts or G5 acceptance are authorized by this diagnostic.

## One-shot decisions

- GUARDED_REJECTED_BITWISE_OR_MODEL_PARITY: failed equivalence, graph, clock or IC qualification; no favorable interpretation.
- GUARDED_EVENT_PERSISTS_STOP: qualified native first-window/control anomaly remains; stop guard and request platform/model numerical-suitability review.
- GUARDED_EVENT_REMOVED_CONDITIONAL: first-window native flags clear only. This does not identify the unique cause, certify accepted events, cover the second event, or establish independent thermal/solver convergence.
- UNQUALIFIED_RESOURCE: runtime/license/free resource/private sink qualification unavailable.

Public outputs are code, execution metadata and safe flags only. All console, converter details, scalar research metrics, native MAT and model derivatives remain owner-private with full SHA readback. No merge, additional solver run, G6, paid service or manuscript/export.

## Harness-only recovery after run40631027346

The first prepare aborted at CANARY with MATLAB:error:missingMessageArgument. It did not establish equivalence/mismatch, reserve the plant intent, build a guarded model, or simulate. All error-ID-only assert calls inherited from the Chat canary/builder/converter audit are corrected to documented assert(condition,identifier,message) syntax. No condition, RNG input, exact equality or bit-pattern comparison changes. This is a code/harness recovery, not a rerun of a successful canary or a second physical attempt. Its prior summary/receipt and absence of the plant intent are enforced in transport. MATLAB error stacks are retained privately for precise diagnostics.

The assertion failure location cannot be assumed benign: the release precondition had already passed in the outer runner. Therefore the recovery workflow is reduced to PURE MATLAB CANARY ONLY, with model loading/compile/plant intent/simulation entirely absent. It saves the unchanged synthetic q/original/guarded vectors and bit mismatch mask privately before asserting with a valid error-message signature. This preserves fail-closed behavior even if the first error masked actual MATLAB floating-point non-equivalence. No conditional plant gate is reachable in the corrected diagnostic workflow.
