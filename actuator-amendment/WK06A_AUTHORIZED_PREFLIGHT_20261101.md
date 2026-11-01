# WK06-A authorized one-shot: pre-MATLAB decision, 01 Nov 2026

**ACK:** `WK06-A-AUTHORIZED-ONE-NONBATTERY-20261101 RECEIVED`. Owner authorization is independently visible at Issue #67 comment 6556750820. **Verdict:** `WK06_BLOCKED_PRECONDITION`; `MATLAB_CALLS=0`, `ONE_SHOT_CONSUMED=false`, `G_M3_PHYSICAL_QUALIFIED=false`, `G5_ACCEPTED=false`. No workflow dispatched or enabled.

| Mandatory condition | Status | Read-only evidence / exact gap |
|---|---|---|
| Distinct one-trial owner authorization | PASS | Issue #67 owner comment 6556750820 limits scope to one nonbattery WK05 fixture trial. |
| Exact source pin and private-source preflight design | PASS for source identity; runtime source preflight NOT RUN | PR #66 head `b508de5580534593bcac3018f16e1ad04d5c4789` read back byte-for-byte. Local fixture SHA-256 `3A2E1300B29D4DD8B3DE5500AF7EF727CBDEE8DD2B30F0F379C8F01C1BF69900`; private-gate SHA-256 `6A0593D9C7B1BB624F35EF46F7185047076DCDA9645F43032318B1235D09AFD2`. No fresh protected-run prepare receipt or absent-target witness. |
| Exact R2024b U10 build and current license/entitlement | UNKNOWN | Historic M2 run 40701917441 executed build 24.2.0.3361896. No current authorized WK06 MATLAB entitlement/build proof *before a MATLAB call*. Historic success cannot satisfy the fresh gate. |
| GitHub-hosted runner, exact branch/environment and secrets protection | UNKNOWN | Branch/PR source visible. Public rulesets list `[]`; branch-protection read returned 403 `Resource not accessible by integration`. No successful current protected-environment admission or safe secret-name mapping proof for WK06 branch. Secret values were never requested. |
| No-fee duration/quota/resource | UNKNOWN | No current Actions free allocation, host/cgroup capacity or job timeout guarantee. Historical static compiler resource receipts do not attest a new WK06 job. |
| Owner-private Drive authenticated write + independent remote-byte readback | UNKNOWN | Connected owner Drive read of prior private M2 reports passed. No fresh WK06 write/readback, current OAuth write permission or capacity receipt. |
| Single-use trigger disabled/no retry | UNKNOWN | WK05 branch contains no executed WK06 workflow. A reviewed protected one-shot trigger and disable/attempt ledger have not been installed or proven. No new run was launched to test these. |

Because multiple mandatory conditions are UNKNOWN, the owner's explicit stop rule applies **before any MATLAB call**. The minimum non-MATLAB next step is a protected infrastructure preflight that independently records branch/environment admission, current included license entitlement/build availability, no-fee quota/time/cgroup capacity, fresh private Drive write/readback and exact source/output-path SHA/absence, with a one-shot trigger and no public bytes. This action itself must not dispatch the WK05 fixture until every gate is PASS and reviewed. If any condition remains UNKNOWN, retain `WK06_BLOCKED_PRECONDITION`. The separate B0L340 physical authorization is untouched.

