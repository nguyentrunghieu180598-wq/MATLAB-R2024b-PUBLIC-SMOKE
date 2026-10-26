# JTE096 W96-01 technical hotfix scope
No G1-G4, JTE092, 340s, 2400s, prior passed oracles, or rejected numerical sweeps are run.
New tests: selective endpoint cleanup + retained unrelated branch + orphan/parameter
negative controls + test routing, then independently loaded pristine B0L/derivative
static wiring/dialog/declared-IC/solver comparison and headless compile warnings.

Delete exactly five original endpoint pairs BEFORE deleting Mod205/Subtract204,
using documented R2024b delete_line(sys,sourcePort,destinationPort). Preserve Max207,
all ports and legitimate branches; compare complete local endpoint edge delta,
retained block params, PortConnectivity outside the explicit patch, and orphan leaves.
No blanket orphan deletion. Compare source and derivative unconnected-line warnings.

Original rejected assertions remain explicit opt-in under jte-public/rejected,
labelled EXPECTED_FAIL_REJECTED_CANDIDATE. Normal entry points are independent
masking/ideal-TF/evidence tests. JTE096 CI does not rerun these previously passed tests.
The old mixed Work preflight is retired with a typed error, not marked passed.
Historical exact source and MATLAB failures remain in immutable PR48 commits.

derivativeRecordedLawSelfConsistency (formerly recordedLawExact) is a within-trace
check only. Static block targets/model InitialState settings/wiring equality do NOT
prove solved Simscape consistent IC, original-vs-derivative trajectories, or full
physical equivalence. Scope/Display UI-dialog values are excluded explicitly.
No new plant results or causal acceptance; atomic variant already failed to remove
the first anomaly in 40355277420. Preserve that negative finding.

W96-02 requires an authorized interactive Cloud MATLAB R2024b, documented event
inspection, private profiler/trace persistence with SHA/readback, and BOTH event
windows. Without that: BLOCKED_NO_EVENT_CAUSAL_EVIDENCE, no blind solver sweep.
