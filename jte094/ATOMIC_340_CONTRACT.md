# JTE094 bounded atomic-realization experiment (technical contract, not G5)
Frozen before the new 340s diagnostic:
- Reject the simple three-threshold candidate. R2024b MATLAB and Simulink mod
  have five adjacent-double counterexamples; do not loosen equality to pass.
- Atomic variant uses exactly q-mod(q,step) within original Step Change.
  Keep original final maximum, upstream gain/saturation, all plant blocks,
  load/IC and ode23t settings. Preserve original in/out port configurations.
- Require exact source graph identities and unchanged outside dialog params;
  require exact recorded q/core clocks and pointwise original double law.
  Reject/rollback derivative if the legitimate recorded law changes.
- Use inherited >0.005 normalized departure from .25 only as the existing
  first-window anomaly detector, not a new G5 actuator acceptance tolerance.
- Reuse JTE092's already-run original anomaly evidence; do not rerun JTE092.
  The new run is a derivative-only counterfactual, not a paired thermal
  convergence study. No thermal delta relative to baseline can be claimed.
- Capture saved TF state identity/clock. Do not call a callback or logger
  sample a certified accepted step. Do not infer a reset actor from absence
  of an output anomaly under intervention.
- Only non-sensitive status flags go to public CI. Raw arrays remain transient
  runner memory; no public MAT/artifact, no scientific acceptance from this
  diagnostic. Private archival/second event/2400s remain separate unmet gates.
- If excursion remains, do not keep changing the controller. Continue with
  supported R2024b solver/Simscape event tracing; report missing detailed
  event access explicitly if it cannot be established.
- No G5/G6/G7/G8 pass, physical validation claim, paper, paid service or merge.
