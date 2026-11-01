# WK06 - protected nonbattery infrastructure preflight: source package (01 Nov 2026)

**SOURCE-PREPARED, NEUTRAL PREFLIGHT NOT EXECUTED.** Screenshot provided by the owner confirms GitHub environment JTE_DRIVE_WRITE deployment branches now list 3 rules, including `codex/wk06-nonbattery-only-20261101`. Three environment secret NAMES are present. The account repo is PUBLIC with owner admin permission. This does **not** prove OAuth secret values valid on runner, current MATLAB build/license, or private Drive byte readback.

## Exactly what was created on this isolated branch
- `.github/workflows/wk06-infra-only.yml`: guarded GitHub-hosted standard `ubuntu-latest` public-repo, protected JTE_DRIVE_WRITE, exact branch and commit-message one-shot trigger for **only** the neutral Drive preflight. **Zero MATLAB steps, zero pack steps, no Actions artifacts.**
- `jte-public/WK06_neutral_preflight_20261101.py`: checks run context, protected env marker, 3 secret PRESENCE (never prints them), OAuth refresh, app-owned private folder owner-only ACL, 512MiB Drive available quota, one existing-verified-receipt guard, tiny NEUTRAL owner-private marker upload with full remote byte SHA readback and second owner-only ACL verification. Uses established JTE062/JTE063 transport; never opens or exports study MAT.
- `jte-public/WK04_private_gate.py`: changed legacy WK05 branch/message pins to WK06 isolated branch and future separate `WK06_NONBATTERY_ONE_SHOT_20261101` intent; future protected MATLAB `prepare` additionally **requires independently verified neutral preflight receipt** on owner-private Drive (same OAuth identity). Does **not** schedule MATLAB.
- `jte-public/JTE063_streaming_drive.py`: whitelists narrow `WK04_NONBATTERY_API_ONLY_NOT_G5` label for **future** toy-only private publisher. Previous version would always fail on this missing schema.

## Trigger and execution disposition
- Repository branch exists, has just code/guard modifications. The intentionally non-matching source-commit job on GitHub Actions run [41313608496](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/41313608496) is **SKIPPED**. This is not a successful private readback or a MATLAB trial.
- The attempt to activate the protected neutral preflight from the current Chat integration did NOT complete; **no trial and no neutral Drive probe may be claimed**.
- Existing physical `jte116-one-approved.yml` includes a real pack B0L340 step and MUST NOT be reused. Disabled `m3-logger-probe.yml` is also not the WK06 candidate. No workflow was enabled by changing those files.
- Owner's existing grant: at most ONE **nonbattery** MATLAB R2024b Update10 process after verified license/no-fee/runner/private Drive conditions. Until then `MATLAB_CALLS=0`, `ONE_SHOT_CONSUMED=false`, `G-M3/G5=UNQUALIFIED`. A neutral preflight job is NOT the one MATLAB attempt.

## Work's actual next high-value task
1. Source-security-review the four changed files for no leak, branch/event/attempt guard, no physical MATLAB or auto-retry; report a specific code defect if found. No generic re-triage of old WK01–05.
2. Under an **authorized genuine Work/Actions runtime**, independently verify JTE_DRIVE_WRITE branch admission and prove the NEUTRAL protected preflight end-to-end, or return precise OAuth/ACL/cost blocker; do not claim PASS from skipped CI. Stop if private ACL/credential validity uncertain.
3. If neutral private receipt is actually PASS, review the future WK06 nonbattery-only one-shot MATLAB workflow separately: verify exact pinned Update10 in its only approved process and abort on mismatch (consumes one-shot); confirm full result/partial evidence readback and G-M3/G5 false.
4. Deliver one-page `WK06_NEUTRAL_READBACK_PASS` with exact GitHub run and private SHA receipt, OR `WK06_NEUTRAL_ACCESS_NO_GO` with observable error code. Do not auto-dispatch the user's 1/1 MATLAB opportunity, no pack, no new charges, no public artifacts/secret values.

References: [owner approval and operational gate](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/issues/67), PR #66 WK05 source, PR #69 environment preflight. This note does not confer new runtime permissions.
