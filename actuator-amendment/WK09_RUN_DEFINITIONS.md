# WK09 D13 0–340 s source contract

Implementation request: PR #77 [Claude approval 6609673672](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/pull/77#issuecomment-6609673672), items 1–4 only. This source PR authorizes no execution. Stop for Claude's independent review.

Base: `5f4222eb8311556f04a122f9fb3be32b758ed6bd`, tree `5affff3162e02815340c049894bee4f51f3db1d2`; branch `codex/wk09-d13-340s`. Historical PR #77 is not rebased/edited and PR #78 and the historical WK08/WK10 gates/workflows/markers/approvals are unchanged.

## Frozen scenario and selector

Every case uses the reviewed six-argument `BTMS_WK08_prepare(...,340,scenario)` path: root Gain=2 on Current demand output 1 → Battery Control input 2, original vendor MAT/hash/timing, 0–340 s and 300 K ambient. The retained graph/controller/plant/initialization and solver remain audited. Only the declared R3/R4 numerical sensitivity exceptions below write actuator/tolerance parameters. Vendor voltage-limit warnings remain warnings; no warning-policy or PASS-criterion change is made.

| Object | SHA-256 of exact bytes |
| --- | --- |
| `WK10_scenario.json` | `372683adc8c45d6c9bc84213619916cf9cee18d03471b9ed4ae7fab3c0bc9f7b` |
| `WK09_selector_D13_200_340.json` (2625 bytes; no final newline) | `cbaf7ede34dee318b1ab3a73cfbc53dbde44bda6700133c864c3dfc8ae148233` |
| Accepted R2 private receipt, run 41659796627 | `7074b363ee0c97b52f5f8d80a4148852c54432b417b8e2dc73024b765b9a0612` |
| Claude's frozen prediction artifact (referenced, not republished/recomputed) | `50f97a1226858944b5cb0088f561959334b59c5efcc51d36d99850555bf2d5a5` |

R2 is an external baseline already accepted by Claude. It is never scheduled and its spent identity is never reused. The committed selector is exactly Claude's supplied projection, with no temperatures: JTE-050 v02 (D13 window), time-weighted mean on [200,340], trapezoids with interpolated endpoints, denominator 140 s, ascending channel-index ties. The resolver checks its exact bytes and full 312-channel permutation, then derives channels from that ranking and the unchanged geometric CSV. There is no per-case ranking, literal channel choice in MATLAB, MAX/v01 fallback or window retuning. The private prediction bytes and reproduction of the baseline analysis were NOT VERIFIED by Codex.

| Case | Sensed channels | Bias and target | Pipeline | Numerical exception |
| --- | --- | --- | --- | --- |
| R3 | 312 | 0 | identity bypass | Ts=5 ms on ZOH/actuator; A=exp(−Ts/.001), B=1−A |
| R4 | 312 | 0 | identity bypass | RelTol/AbsTol=1e−4 |
| R5 | 312 | 0 | ACTIVE C0 | none |
| R6 | 312 | −2 K, rank 1 (202) | ACTIVE | none |
| R7 | 312 | −2 K, rank 156 (288) | ACTIVE | none |
| R8 / R9 | fixed S16 | −2 / −4 K, hottest sensed (168) | ACTIVE | none |
| R10 | fixed S8 | −4 K, hottest sensed (180) | ACTIVE | none |
| R11 | 312 | +2 K, rank 1 (202) | ACTIVE | none |
| R12 / R13 | fixed S16 / S8 | 0 | ACTIVE sparse-only | none |
| R14 (optional) | 312 | −2 K, first three ranked channels (202,203,204) | ACTIVE | none |

Default Ts=10 ms, tau=.001 s, ode23t, MaxStep=.05 s, RelTol/AbsTol=1e−3. All non-R3 cases retain exact archived A/B/SampleTime/ZOH strings; all non-R4 cases retain exact archived tolerance strings. C/D/initial state remain untouched even in R3. The builder records before/after strings and final save/reload fingerprint. It rejects a resolved definition that differs from the registry, selector, scenario, geometric subset or derivation. Vector J is sorted/unique/nonempty/in range; **all** biased channels must be sensed before any graph edit. Existing four-argument scalar/default-neutral behavior is preserved.

## Separate authorization and execution boundaries

| Group | Exact ordered allowlist | Workflow timeout | Identity G |
| --- | --- | --- | --- |
| CONTROLS | R5 → R12 → R13 → R3 → R4 | 210 min | `WK09_D13_CONTROLS_A` |
| CASES | R6 → R7 → R8 → R9 → R10 → R11 | 240 min | `WK09_D13_CASES_A` |
| R14 (optional, separate) | R14 | 35 min | `WK09_D13_R14_A` |

R14 is outside both main allowlists, optional before 20 Nov under D15, and needs its own review, read-only preflight and owner execution approval. No batch approval is inferred. The exact expanded strings and paths are in `jte-public/WK09_runs.json`:

- Group execution message: `G_ONE_SHOT`; marker: `jte-public/G_TRIGGER.txt`; approval: `APPROVE_G_ONCE_AFTER_CLAUDE_GO`.
- CONTROLS/CASES parent intent: `G_JOB_INTENT.json`; child intent, reserved immediately before the case: `G_Ri_ATTEMPT_INTENT.json`; receipt: `G_<GitHubRunID>_Ri_PRIVATE_RECEIPT.json`.
- Optional R14 uses one intent `WK09_D13_R14_A_ATTEMPT_INTENT.json`, binding its sole allowed case; receipt `WK09_D13_R14_A_<GitHubRunID>_PRIVATE_RECEIPT.json`. No extra child reservation or inclusion in another group's grant.
- For L=CONTROLS, CASES or R14, read-only preflight message `WK09_D13_L_PREFLIGHT_A_CHECK`, marker `jte-public/WK09_D13_L_PREFLIGHT_A_TRIGGER.txt`, approval `APPROVE_WK09_D13_L_PREFLIGHT_A_ONCE_AFTER_CLAUDE_GO`; timeout **10 min**.
- Workflows: `wk09-d13-{controls,cases,r14}-{preflight,one-shot}.yml`. All six are default false, source SHA all-zero, and their trigger files are absent.

Each future invocation needs its own reviewed S → workflow-only E → marker-only T. The exact bare T message/marker, push event, public repository, protected environment, hosted runner, attempt=1, full source SHA and two-commit chain are checked before any MATLAB action. The marker must be absent at S. Any restore/delete-marker R push must be separate from E+T, because path filtering compares the net push diff. No force/retry or identity recycling. Owner must independently add the branch to JTE_DRIVE_WRITE's deployment rule and supply the particular approval through its protected `WK09_OWNER_APPROVAL` variable; this source work changes no environment settings.

Preflight is read-only: OAuth refresh and Drive reads, disposable private temp files for verified JSON/workspace bytes, unique owner-only ACLs, verified original M2 source/proof/workspace links, pinned accepted R2 receipt, unused new parent/child intents and worst-case output quota. No vendor checkout, MATLAB action, model preparation, reservation, upload or folder creation. CONTROLS and CASES each need preflight approval then execution approval: four future separately approved invocations. Native success is never Claude's acceptance.

The group runner repeats those checks before reserving its durable parent grant (ordered allowlist, source/registry/code/scenario/selector/prediction/R2 hashes, attempt and global deadline). It starts one isolated worker per case. Each worker verifies that grant against private remote readback, reserves its own child if applicable, downloads a fresh source/workspace, creates a fresh model and launches exactly one supervised MATLAB process with exactly one direct initialization. There is no warm state, restore, overlapping trajectory or automatic retry. `JTE_GOOGLE_*`, GH_TOKEN and GITHUB_TOKEN are removed from MATLAB's environment; the reviewed run-command bundled launcher and `MW_BATCH_LICENSING_ONLINE=true` are retained. Only the dummy license probe can print its fixed success marker; MATLAB study console is private, with its first **2048 bytes** captured in private flags.

The first workflow step starts a never-reset job clock before setup/license probing. CONTROLS/CASES reserve 15 min setup and 5 min final reporting, keep **35 min per-run envelopes**, and refuse a case without its full envelope plus the report reserve. Per-case preparation/launch ≤600 s, external MATLAB ≤1185 s, internal ≤1200 s, ≥300 s delivery time reserve. R14's single 35-minute envelope includes workflow setup, as in the historical single-run budget. Blocking preparation/delivery is bounded by the parent worker watchdog; timeout kills only that identified worker and descendants. RAM (8 GiB before launch; 2 GiB running reserve), disk (10 GiB before launch; 2 GiB running reserve), live Drive refresh/reserve, 1 GiB/file and 2 GiB/case caps remain. Group preflight budgets retained output of every case plus 3 GiB; no cap is raised or native data dropped.

After any failed/unqualified/undelivered Ri, launch no later case; journal each as `SKIPPED_AFTER_Ri_FAILURE` without reserving its child intent. Attempt one bounded private failure delivery. A completed receipt requires full-byte remote SHA readback and owner-only ACL; absent/failed delivery is **NOT VERIFIED**, never a fabricated receipt. The parent intent remains spent even if a child never launches. A later execution needs a new separately reviewed identity, not a retry under this grant.

Private native roles remain `uCore`, `uSampled`, `actuatorY`, `Ttrue312`, `TmaxTrue`, `TmaxMeas`, `pumpPower`, `Ttrue312_1s` (341×312 at 1 s). Each case has its own proof/model/definition/manifest/native files/resource trace/private console/receipt. All ordinary remote payloads are `<GitHubRunID>_Ri_<basename>`; receipt names above also include the run/case identity. Nothing uploads raw data as GitHub artifacts. MATLAB alone derives optional `SUMMARY.json`, labeled DERIVED_NOT_EVIDENCE; Python only copies it. Missing summary/export failure never changes native qualification or control acceptance. SOC intervention remains NOT VERIFIED; no vendor probes are added.

## Frozen control acceptance and CASES/R14 barrier

Claude independently applies these criteria to native logs; neither the runner, SUMMARY nor an exit-zero flag can accept a control:

- R3/R4 still run after R5/R12/R13 and Claude reviews their finite/grid/law evidence (R3 uses its own 5 ms grid; R4 10 ms). They set the numerical band but do not gate CASES/R14. If either is incomplete, Claude determines how to report its numerical band as NOT AVAILABLE; the runner retains stop-on-failure.
- R5: finite 10 ms grid; TmaxMeas=TmaxTrue exactly; uSampled obeys the law at every sample; maximum absolute TmaxTrue difference from accepted R2 ≤1e−6 K; identical level sequence.
- R12/R13: finite 10 ms grid; law applied to TmaxMeas; TmaxMeas≤TmaxTrue at every sample; nonnegative sparse deficit.

**CASES and optional R14 preflight require accepted R5, R12 and R13 only, in that order.** After reviewing their private native evidence, Claude supplies the exact bytes of public, hash-only `jte-public/WK09_CONTROLS_ACCEPTED.json`, committed in the reviewed source S. This file is absent from this PR. Registry `controls_acceptance.file` names it, `required_runs` is `[R5,R12,R13]`, and `sha256` defaults to 64 zeros until Claude supplies the exact digest. A zero/unset digest or absent file fails explicitly with `WK09_CONTROLS_ACCEPTANCE_UNSET`; mismatched bytes fail with `WK09_CONTROLS_ACCEPTANCE_DIGEST`. No acceptance is fabricated by this source delivery.

The gate reads raw file bytes with `git show HEAD~2:jte-public/WK09_CONTROLS_ACCEPTED.json`, hashes those exact bytes against the reviewed registry value, then parses them. It never reads a working-tree substitute or a Drive attestation. No acceptance-SHA/hub-commit repository variables are required or read. Owner setup is the per-invocation `WK09_OWNER_APPROVAL` and adding this branch to the JTE_DRIVE_WRITE deployment rule; source work changes no repository/environment settings or workflow files.

Acceptance fields remain `schema=WK09_D13_CONTROLS_ACCEPTANCE_V1`, `reviewer=Claude`, `decision=ACCEPTED`, a nonzero 40-hex `hub_commit`, `selector_sha256`, `scenario_sha256`, `baseline_receipt_sha256`, `predictions_sha256`; `runs` contains exactly R5, R12, R13 in that order. Every row has `id`, `accepted=true`, exact private `receipt_name` and `receipt_sha256`, and true booleans for every frozen criterion named in registry `controls_acceptance.criteria`. R5 additionally has numeric `max_abs_Tmax_R5_minus_R2_K` in [0,1e−6]. Only booleans, hashes, receipt names and provenance are public; no native arrays, metrics beyond the specified acceptance fields, credentials or private locations are included. The reviewed file hash binds Claude's decision and hub reference; the public runner does not independently fetch the private hub commit.

Each named receipt is still downloaded privately by its exact pinned SHA-256 with verified metadata and owner-only ACL, and group/case/status/scenario/selector/R2 provenance checks remain. Missing/wrong source hash, file, fields, order, criterion or private receipt rejects CASES/R14 before reservation. R3/R4 acceptance entries are not required or accepted in this dependency file. No metric is inferred from SUMMARY.

## Offline checks and remaining verification

`test_WK09_definitions.py` checks exact bytes, derived choices, every case's numerical contract, mutation rejection, vector guard/default behavior, six disabled workflows/absent markers and action order. `test_WK09_group.py` uses mocked transports/processes for all contexts, chain/approval/retry rejection, reviewed-source acceptance hashes/criteria, read-only preflight, spent intents, sealed order, every failure position, persistent global deadline, reserves, secret stripping/private console, worker timeout and per-run private publication. No real Drive or MATLAB call is made by those tests.

`test_BTMS_WK09_guard.m` is **NOT RUN**: synthetic vector/no-edit/default tests and static prepare/save/reload parameter assertions for every case. Its archive test requires the owner's unchanged M2 fixture in `WK09_STATIC_M2_FIXTURE`, with the matching workspace/vendor project already restored on the owner's private machine; absence is an incomplete assumption, never a PASS. No compilation/simulation/initialization is requested by that test.

See `WK09_OFFLINE_VALIDATION.txt` for actual author checks. **NOT VERIFIED:** all MATLAB tests and Update 10 graph/code-generation/runtime behavior; private prediction/native bytes and independent numerical analysis; all R3–R14 scientific outcomes, clocks/equivalence/control acceptance, warning behavior in a real run, wall time/RAM/quota feasibility, environment branch-rule acceptance, future group authorization/delivery against live services, and the reviewed-source acceptance/private-receipt bridge. Offline tests and a static parser do not certify these. Stop for Claude review; no execution is approved here.
