# WK06 owner/admin preflight — 01/11/2026
**Work evidence:** commit 28ebff562439d0b54a0120c9a008c2b50b82a0ac. Verdict WK06_BLOCKED_PRECONDITION, MATLAB_CALLS=0, ONE_SHOT_CONSUMED=false, G-M3/G5 NOT ACCEPTED. Owner approval already given via Issue #67 comment 6556750820.

## Verified execution-surface mismatch
Work inspected **Codex Desktop on the owner's Windows PC**, where it found local MATLAB R2024b, not an authorized Work Cloud runner. No runnable Cloud configuration was found for this BTMS repository. A desktop discovery of MATLAB is NOT a cloud license/entitlement or permission to use the private PC.

## Existing workflows must NOT be reused
- .github/workflows/m3-logger-probe.yml: job disabled by an always-false if condition; restricted to branch codex/jte-tf-constant-input. NOT the WK05 source.
- .github/workflows/jte116-one-approved.yml: contains an actual guarded **PHYSICAL B0L 0–340s trajectory** after its toy phase. Owner's current grant is strictly **NONBATTERY**; do NOT trigger it.
- .github/workflows/jte-tf-constant-private.yml: private diagnostic on a different branch, NOT a WK06 qualification.
- No current WK06 Actions run was found. GitHub Actions success from 29 October is not evidence of this trial.

## Exact minimum owner/admin checks (never expose secret values)
1. Repo Settings > Environments > JTE_DRIVE_WRITE: inspect access and deployment branch protection for an isolated, reviewed WK06-only nonbattery source. Do not relax general protection.
2. Repo Settings > Secrets and variables > Actions and JTE_DRIVE_WRITE environment secrets: check only **presence/scope** of JTE_GOOGLE_CLIENT_ID, JTE_GOOGLE_CLIENT_SECRET, JTE_GOOGLE_REFRESH_TOKEN. Never copy values to chat or logs.
3. Repo/account Settings > Billing and licensing > Actions: verify current included minutes and spending guard; no incremental paid service, sufficient resource/timeout.
4. From a genuinely authorized GitHub-hosted runner or Work Cloud computer (not local Windows), prove R2024b Update10 exact build and current no-fee entitlement. An old M2 build 24.2.0.3361896 is historical. If proving this requires a MATLAB execution, flag NOT_VERIFIABLE and request a protocol decision; do not consume the authorized one-shot before preflight approval.
5. From that SAME protected execution environment, verify private Drive tiny neutral-byte write and independent byte-readback. Chat's own Drive read permissions cannot be transferred to a runner.
6. Gate a reviewed ONE-TIME nonbattery WK05 fixture on immutable commit and source SHA, unique output path and job ID, retry disabled, independent private publisher, job cleanup, disabled trigger after use.

## Outcome
For EACH check return observed fact, PASS/FAIL/NOT_VERIFIABLE, proof, and required owner action. Any unverified gate => WK06_PRECONDITION_OWNER_ACTION_REQUIRED, no MATLAB call, trial not consumed. All pass => at most ONE owner-approved nonbattery R2024bU10 WK05 trial under the separate written approval; failure after MATLAB starts consumes it. G-M3 physical and G5 stay NOT ACCEPTED after a toy-only qualification; physical battery B0L340 permission untouched. No public private MAT, no secret values, no paid service, no merge, no automatic retry.

This checklist is reviewer documentation only, not an execution trigger.