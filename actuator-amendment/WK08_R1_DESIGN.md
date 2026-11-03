# WK08 R1 source-only run sheet — 03 Nov 2026 (Asia/Bangkok)

**Author handoff:** WK08_PHYSICAL_DESIGN_READY_FOR_OWNER_REVIEW.
All runtime checks below are prospective assertions. No MATLAB, CI, Drive access, pack run,
workflow enable or trigger was performed to produce this source. Claude reviews independently.

## Frozen provenance and R1

- Upstream MathWorks tag 24.2.1.5, commit `f98d21929a3a269dacd1ee38999cd9773760c6db`.
  Vendor SLX SHA-256 `0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0`.
- Public code branch base `f7ba843e0101eb8bf94d5f4ec217fea45d4b1ff7`.
  MATLAB exact string: `24.2.0.3361896 (R2024b) Update 10`.
- Source clone is the private M2 B0L_Ref_LOGGER from run 40701917441 / commit
  `75afa01be55339d20ce5831830a0cacdb0c5d3f4`, using its verified receipt, model SHA,
  compiled-width/retained-graph proof and archived source workspace. No guessed model SHA is substituted.
  Protected prepare must fetch and cross-link those hashes before MATLAB. The new derivative SHA is
  computed only when that fresh SLX exists and is stored in WK08_PREPARED_PROOF.mat / flags / private receipt;
  it cannot truthfully be supplied from this source-only session.
- Reuse BTMS_M2_prepare340NoRun: source 2400s → new clone 340s, rebind output paths, comment only
  its three proven duplicate workspace observers. Three other workspace observers remain.
- R1: B0L, b=0, S=1:312, direct t=0 start; source current/load and ambient=300 K;
  source IC/workspace preserved. ode23t, MaxStep=.05 and source tolerances unchanged.
- Approved sampled assumption: ZOH Ts=.01, discrete x[k+1]=a*x[k]+(1-a)*u[k], y[k]=x[k],
  a=exp(-.01/.001), C=1, D=0. Preserve archived actuator initial output state; never guess it.
  Ts=.005 is a future separately reviewed sensitivity, not a fallback in R1.
- Source controller unchanged:
  q=sat[.001,.95](.1*(Tmax-300)); u=max(q-mod(q,.25),.25).
  Inclusive transitions at 305 and 307.5 K. No favorable-channel, reference, load or solver adjustment.
  G5 continuous-TF acceptance remains rejected; R1 cannot reopen it by itself.

## Measurement layer and identity

BTMS_WK08_inject accepts one fixed j and additive b (either sign), followed by subset S.
It replaces ONLY the vector edge entering Battery Control/min-max T. The plant source and original
T_true observer stay on the unbiased vector. The generated MATLAB Function produces a vector with
exactly |S| elements: unsensed channels never reach MinMax3 (nor its minimum branch). The existing
FlwR_calc/max edge is retained. Non-neutral preparation is delivered for future reviewed cases;
R1 calls only the neutral branch. The sparse cases here still bias one channel j, per hub #1;
this source does not silently reinterpret them as all-sensor common bias.

At b=0, S=all the helper does literally nothing and asserts before/after equality using
BTMS_WK08_structFingerprint. This extends WK07's local structFingerprint design to canonical
physical port connectivity, all retained block dialog parameters, solver/config/IC settings,
model workspace values, chart source and comments. Only To File output paths are normalized.
StopTime and InitialState are retained in the fingerprint. Equality applies to the injection
operation; adding the explicitly declared new logging observers is a separate graph change.
R1 records the final prepared fingerprint and requires identical reload and post-run fingerprints.
No ModelStructuralChecksum equality is asserted: WK07 established that To File names, StopTime and
initial operating state affect it in this build.

## Fixed geometric sensor map (CSV)

VERIFIED from pinned primary source, using static XML/SSC only:

- [parameter file](https://github.com/mathworks/Battery-Pack-Model-Simscape/blob/f98d21929a3a269dacd1ee38999cd9773760c6db/Scripts_Data/Battery_Pack_Thermal_Management_param.m):
  Ns=[12,12,12,16,16,12,12,12], Np=3, hence N=[36,36,36,48,48,36,36,36].
- [vendor SLX](https://github.com/mathworks/Battery-Pack-Model-Simscape/blob/f98d21929a3a269dacd1ee38999cd9773760c6db/Models/Battery_Pack_Thermal_Management.slx):
  system_158 T concatenate (SID98) takes T1..T8 in module order through From/Goto tags.
- [SSC](https://github.com/mathworks/Battery-Pack-Model-Simscape/blob/f98d21929a3a269dacd1ee38999cd9773760c6db/Libraries/%2BbatteryModule/batteryMultiDimModel.ssc):
  detailed outputCellTemp=[battery_thermal.cell_temperature]; pouch conduction connects i to i+1.
  Thus module-local index follows the modeled cell stack, not a simulated temperature ranking.

Rule: normalized cell-center coordinate x=(i-.5)/N along each module's modeled cell stack.
For 16 choose closest cells to x=.25 and .75; for 8 choose closest to x=.5.
Tie → lower index. For these even N this is i=ceil(N*f), giving local 9/27 and 18 for N36,
12/36 and 24 for N48. Module offsets=[0,36,72,108,156,204,240,276].
The CSV contains each explicit channel index plus module, N, local index and target fraction.
No equal-39-cell assumption, pack orientation claim, resistance sorting or temperature data enters the rule.

16 channels: 9,27,45,63,81,99,120,144,168,192,213,231,249,267,285,303.
8 channels: 18,54,90,132,180,222,258,294.
312: all channels. This is a pre-registered simulation geometry rule, not validated physical sensor access.

## Logging and gates

All files are Timeseries To File, constant basenames under a fresh private native/ directory.
Four existing roles stay native, undecimated and inherited; no native clocks are synthesized.

| File/variable | Source | Cadence |
| --- | --- | --- |
| WK08_uCore | unchanged FlwR_calc output, pre-actuator | native |
| WK08_uSampled | existing command ZOH output | native |
| WK08_actuatorY | existing sampled actuator output | native |
| WK08_Ttrue312 | unbiased full vector | native |
| WK08_TmaxTrue | independent max over unbiased 312 | native |
| WK08_TmaxMeas | existing min-max T output 2, after injection | native |
| WK08_pumpPower | existing Pump power calc output | native |
| WK08_Ttrue312_1s | unbiased vector via observer-only ZOH | 0:1:340 s |

File suffix is .mat. Every native series must be nonempty, finite, correct width, nondecreasing clock,
start at 0 and end exactly at 340 (5 for local test). Duplicated native times remain.
uCore and uSampled must belong to {.25,.5,.75}; actuatorY is a state output and is checked finite,
not forced onto command levels. Neutral true/measured max clocks and values must match exactly.
The 1s observer must have precisely 341 rows, each with 312 channels. No filtering/trimming to pass.
Model/vendor/input hashes, exact build, final fingerprint, effective solver and horizon are gates.
Runtime failure, missing/invalid data or a stopped-short resource limit means UNQUALIFIED.

Pump power is the model's gain/saturation demand, not measured electrical pump energy.

## t0 decision and paired direct-start limits

**PARTIAL / NOT QUALIFIED for this Simscape pack:** WK07's toy demonstrates ModelOperatingPoint API
behavior, not full hidden-state restart equivalence for this pack. Do not claim physical ModelOperatingPoint
support on that evidence. R1 does not capture/restore an operating point or run a zero-stop simulation.

Protocol: one Simulation object, one initialize, one initial completed major step, check native true312
and true/measured max t0 values, then continue that same object to 340. When the last step leaves
inactive, use SimulationOutput; only stop explicitly if still paused. Never read nonexistent
ExecutionInfo.StopEventTime; record StopEvent and require file endpoints instead.

Future paired studies must each direct-start at zero from the same pinned IC/load/workspace, with only
the declared measurement change. Compare represented initial plant states and actuator phase before
interpreting differences; missing hidden/algebraic Simscape coverage remains HIDDEN_IC_NOT_CERTIFIED.
No t0 visible-temperature match proves full hidden-state identity. A fresh paired run needs its own
owner approval and is not dispatched by this code. R1 alone provides no paired efficacy conclusion.

## Resources: estimates, screens and stop policy

No measured WK08 wall-time or peak-RAM value exists. Planning estimates below are explicitly assumptions:
initialization 120s and trajectory cost 1–3 wall seconds per simulated second imply
460–1140s for 340s and 2520–7320s (42–122min) for 2400s. The 2400/340 trajectory factor is 7.06;
initialization does not scale with it. The external R1 process ceiling is 1185s, including preparation
and initialization, so even the upper planning scenario is tight. A slower run stops UNQUALIFIED.

Planning RAM allowance: 8–12 GiB total, unmeasured. The observer payload itself at 1s is
341*312*8 = 851,136 bytes (2401*312*8 = 5,992,896 bytes), excluding clocks/container overhead.
Native 312 output, solver states and legacy observers dominate unknown memory and can exceed that
allowance; payload estimates are not process-RAM bounds. Screen ≥8GiB available host/cgroup RAM,
≥10GiB scratch, >3GiB Drive before launch. Keep ≥2GiB live host/cgroup RAM and disk, ≤1GiB per native
file, ≤2GiB total native payload, ≥2.5GiB Drive availability. Monitor every .5s; refresh Drive quota
asynchronously every45s with a10s failure ceiling. Monitor private logs record RAM/RSS/cgroup, elapsed
time and file growth. Reused M3 interrupt→terminate→kill escalation is PID-identity guarded.
Timeout/OOM/killed logs are partial diagnostics, never a successful delivery claim.

Workflow35min, refuse launch after job age600s, reserve ≥300s for publisher/cleanup.
Only complete private full-byte readback permits cleanup. Ephemeral runner loss after failure remains
a preservation risk and must be reported; no raw artifact fallback is provided.
After R1, Claude must replace estimates with actual initialization/trajectory rate, peak RSS/cgroup,
file sizes and extrapolation uncertainty. Six 2400s cases under the planning scenario total
4.2–12.2 hours including initialization, before sensitivity runs and review time.
Whether that fits weeks2–3 is **PARTIAL**, conditional on R1 throughput, quota and available included
runner allocation. No six-case or2400 run is authorized here.

## Workflow and private receipt

Source S contains a disabled job and unresolved reviewed SHA. Future owner/Claude actions only:

1. Claude independently reviews final S and reports GO; owner separately approves the one R1.
2. E changes ONLY .github/workflows/wk08-pack-one-shot.yml: reviewed SHA=S, exact branch/message/
   attempt predicate; configure protected JTE_DRIVE_WRITE approval variable separately.
3. T creates ONLY jte-public/WK08_PACK_TRIGGER.txt, contents and commit message exactly
   WK08_PACK_340S_ONE_SHOT_20261102. That marker does not exist in S.

No workflow_dispatch/schedule/pull_request trigger. HEAD~2=S, E-only workflow diff, T-only marker diff,
attempt=1 and owner approval are checked before private prepare. Prepare verifies owner-only folder/files,
existing neutral transport receipt, input archive receipts and source hashes, then reserves a durable
private one-attempt intent before MATLAB. Pending or verified intent blocks another run even on failure.
One process/one initialize; no automatic simulation retry. Transport's existing bounded network retries
are unchanged and do not launch another simulation. Credentials are stripped from MATLAB's environment.

Publisher uploads raw MAT, proof/model/diagnostics and manifest to private Drive only, checks owner-only
ACL and full-byte SHA readback, then uploads WK08_<run>_PRIVATE_RECEIPT.json. A combined PASS also requires
same run/commit, complete native payload, unchanged code/input hashes, MATLAB gates and supervisor success.
It remains PENDING_CLAUDE, with G5Accepted=false. No public upload-artifact/release/logging of values.

After the attempt Claude/owner must disable the workflow again; this source cannot self-enable/dispatch.
No changes to the prior consumed WK07 workflow or triggers.

## Owner-local 5s dry-run (not executed)

Use a fresh private directory outside the checkout and the same receipt-verified M2 source, workspace,
vendor checkout and inputs. Create WK08_MANIFEST.json there with the same field layout as prepare:
run and commit identifiers, privateRoot absolute path, sourceSHA256, inputs [{local,sha256}],
vendorRoot, vendorSLX, plus mode="OWNER_LOCAL_5S", stopTime_s=5,
ownerApproval="APPROVE_WK08_LOCAL_5S_ONCE". Input locals include M2340Source.slx and source_workspace.mat.
Input source/workspace hashes must be linked to the M2 receipts as above, not guessed.
Keep source StopTime2400; the builder creates the separate5s clone. Do not reuse R1 outputs.

After explicit separate local approval, in owner's pinned MATLAB:
`addpath('jte-public'); BTMS_WK08_dryRun5s('/absolute/private/WK08_MANIFEST.json')`.
This is an actual pack simulation capped at5 simulated seconds. It does not consume R1's CI marker,
does not upload, retry or authorize340s. Keep all outputs private and share the status/receipt with Claude.
Model API/compile/runtime correctness remains unverified until that owner action.
