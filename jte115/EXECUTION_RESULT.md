# JTE115 actual execution result — internal technical acceptance record only

## Outcome

**GUARDED_REJECTED_BITWISE_OR_MODEL_PARITY** — pure MATLAB source-law canary failed. **G5 remains BLOCKED / NOT ACCEPTED.**

- Actual corrected-canary run: [40631662726](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40631662726), job122629204826.
- Executed commit: 0a50a88c18b09afe7008a889f8616bfc822d7bcf.
- Actual MATLAB exception: JTE115:MATLAB_DOUBLE_NOT_EQUIVALENT, stage CANARY.
- CANARY_BITWISE_PASS=false; READY_FOR_ONE_SIM=false; simulationStarted=false; horizonComplete=false; G5_ACCEPTED=false.
- The version guard preceding the comparison required exact MATLAB R2024b Update10. No Simulink model load, compile or physical simulation was reachable in the corrected workflow.
- Confidential synthetic diagnostic MAT, console, flags and summary were uploaded with full remote SHA readback. The owner-private receipt records the exact bytes; no private artifact identifiers or values are published here.

## Error repaired and interpretation

The first run [40631027346](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40631027346), commit d0ccfdccc6d7d518021c0a536a8c996495bbf147, stopped at CANARY with MATLAB:error:missingMessageArgument. Several inherited assert(condition,errorID) calls lacked message text. Corrected assert(condition,errorID,message) calls reveal the original-vs-guard comparison fails; neither the compared formulas, inputs, RNG nor bit-pattern criteria were changed.

The corrected canary saves the exact synthetic q, original/guarded outputs and mismatch mask before throwing. That is direct evidence rejecting this implementation under the locked strict MATLAB equivalence criterion. It is not a physical TransferFcn result, proof of the first excursion actor, a plant failure or a solver convergence result. No new numerical claim about the detailed floating-point mechanism is inferred without inspecting the stored counterexamples.

CI SUCCESS means correct capture, fail-closed behavior and private delivery. The MATLAB comparison itself is FAIL.

## Gate disposition

| Item | Status | Evidence / limit |
| --- | --- | --- |
| Correct MATLAB assertion reporting | PASS | Real corrected canary reaches the explicit equivalence exception |
| Exact original-vs-guard MATLAB equivalence | FAIL | JTE115:MATLAB_DOUBLE_NOT_EQUIVALENT |
| Private full SHA readback | PASS | Actual Cloud log and owner-private receipt |
| Source converter audit / clone static proof / guarded plant study | BLOCKED_BY_CANARY | Not executed; no derivative/filter/source change |
| TransferFcn actor and solver/thermal convergence | UNPROVEN | No new physical evidence |
| G5 scientific acceptance | BLOCKED | Independent Chat acceptance still required; guard rejected |
| JTE113 | CLOSED_UNQUALIFIED | Initialization compatibility failure, not a time-advanced comparator |

Stop after this audit. No guard plant run, new solver attempt, two-window validation, G6, manuscript/export, payment or merge is authorized by this outcome. The mathematical real-number guard identity is insufficient to authorize a bitwise source-equivalent model on this MATLAB runtime.
