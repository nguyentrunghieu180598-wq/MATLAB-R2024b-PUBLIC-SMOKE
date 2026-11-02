# WK08 physical design — source only, 02 Nov 2026

WK08_PHYSICAL_DESIGN_READY_FOR_OWNER_REVIEW. This labels the source handoff,
not a MATLAB PASS. Claude is the independent reviewer. No MATLAB, CI, pack
simulation, Drive operation, or workflow enabling was performed for this PR.
Base: `f7ba843e0101eb8bf94d5f4ec217fea45d4b1ff7`.

Authority: [WK08 owner decisions](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/blob/claude/wk08-owner-decisions/actuator-amendment/WK08_OWNER_DECISIONS_20261102.md),
[WK07](WK07_OWNER_APPROVAL_20261101.md), and [Issue #73](https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/issues/73).
WK07's consumed synthetic allowance does not authorize a pack run. The owner
conditionally approved ONE amended B0L run after this design passes Claude review.
Issues #62–#70 remain historical. IJEHV is the journal target; G5's continuous
TF result remains rejected. No thermal efficacy or solved-IC result is claimed.

## Measurement path and exact default

`WK08_inject(m,b,j,S)` changes only the vector immediately before
`Battery Control/min-max T`. For nondefault inputs, a MATLAB Function computes
`x=T; x(j)=T(j)+b; y=x(S)`. Bias uses original one-based pack coordinates;
if j is unsensed it has no measured effect. Selection physically reduces vector
width, so excluded values cannot enter MinMax3 (or the min reduction). The plant
vector and its true-temperature taps remain upstream and unbiased.

With b=0 and S=1:312 the builder adds no block, workspace parameter, or wire;
it asserts `isequaln` of the extended structural fingerprint. This is exact
structural identity to the input amended B0L, before explicitly declared logging
and horizon edits. It is not byte identity of a newly serialized SLX or a claim
of trajectory equivalence to the vendor's unamended continuous actuator.
`WK08_structFingerprint` extends the WK04 idea with the canonical-port M2340
audit, model workspace, chart source, comments and writable configuration.
Only To File filenames are masked; StopTime and IC remain in the comparison.
Saved/reloaded and pre/post-run fingerprints must match exactly.

## Fixed sparse geometry

[WK08_sparse_sets.csv](WK08_sparse_sets.csv) commits every index. Module order
is 1 through 8, widths `[36,36,36,48,48,36,36,36]`, offsets
`[0,36,72,108,156,204,240,276]`. These follow the pinned parameter script and
pack temperature Mux. Within each module use series-major cell ordering
`local=3*(s-1)+p`, with p=2, the middle of the three parallel positions.
For 8 sensors choose s=Ns/2 (lower central series position); for 16 choose
s=Ns/4 and 3*Ns/4. This is a fixed lattice-position rule, not a measured physical
coordinate or a thermal optimum. The vendor SSC's detailed temperature output
follows battery_thermal array order; its parallel/series connection equations
use Np-sized groups. No simulated temperatures enter this rule.

`WK08_sparseSet(312|16|8)` reads these indices. Bias channel selection is deferred:
only JTE-050 v02's time-weighted 1800–2400 s baseline ranks 1/156/312 may be used
later after an accepted baseline. No v01 MAX selector is added or invoked.
Sparse sets stay fixed regardless of later bias ranks. The six owner cases and
Ts=5 ms sensitivity still require separate per-run authorization.

## R1 run sheet (future, conditional)

- Source: M2 run40701917441 B0L_Ref_LOGGER, fetched through existing `m2340_io`
  proof/receipt linkage. The input SLX, workspace and receipt hashes are checked.
  Actual source and generated derivative SHA-256 are written to private proof;
  no unbuilt derivative hash is invented here.
- Vendor: tag 24.2.1.5, commit f98d21929a3a269dacd1ee38999cd9773760c6db;
  Models/Battery_Pack_Thermal_Management.slx SHA-256
  0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0.
- Exact build: `24.2.0.3361896 (R2024b) Update 10`.
- B0L, b=0, S=all312, ambient=300 K; archived workspace/IC and vendor current
  demand retained. Existing amended ZOH + discrete state-space uses Ts=.01 s,
  A=exp(-10), B=1-A, C=1, D=0 and the archived initial output state.
  `ode23t`, MaxStep=.05 and source tolerance/configuration retained.
- One direct-start `sim` call from 0 to 340 s; no restore, retry, solver fallback,
  controller edit or continuous-TF substitution. No 2400 s run is defined here.
- Controller stays q=sat[.001,.95](.1*(Tmax-Ambient)),
  u=max(q-mod(q,.25),.25); inclusive changes at 5 K and 7.5 K only.
- Seven constant private filenames `WK08_R1_<role>.mat`: uCore, uSampled,
  actuatorY, Ttrue312, TmaxTrue, TmaxMeasured, pumpPower. The first three retain
  the M2 taps, Ttrue312 samples exactly every 1 s (not every N variable steps),
  and scalar maxima/pump use inherited native clocks. Pump power is the existing
  model calculation, not measured hardware power. All MAT and diagnostics go
  solely to the protected private Drive receipt, never Actions artifacts.
- Gates: input/vendor SHA, exact build, exact default structural identity,
  saved/reloaded and pre/post-run fingerprint, finite data and clocks, initial
  time 0, final timestamp exactly340 for every stream; uCore/uSampled values
  only {.25,.5,.75}; Ttrue312 has312 values per row and exact 0:1:340 clock.
  actuatorY is filtered and is not constrained to those three command levels.
  Private SHA readback must complete; G5Accepted stays false pending review.

## t0 and resources

ModelOperatingPoint restoration at t0 for this exact Simscape pack is NOT
qualified by the WK07 synthetic toy. No unsupported-state claim is made and R1
uses direct initialization. For later paired direct-start comparisons, start
both cases independently from identical frozen IC/workspace/load, compare
visible t0 T and actuator output phases, and disclose that hidden Simscape and
solver/algebraic states are not certified identical. Each member requires its
own owner approval; R1 itself is just one member, not a paired experiment.

No amended runtime/RAM measurement exists. For 340 s at10 ms there are at least
34,001 scheduled sample hits (2400 s:240,001); thermal output after1 s decimation
has341x312 doubles, about0.85 MB (2401x312:about6.0 MB). Three scalar sampled
streams alone have about0.82 MB numeric values at340 s; native event clocks,
solver/Simscape states and retained workspace observers can dominate. These
are numeric lower bounds, not MAT byte or RAM predictions. A linear screening
estimate for2400 s would be measured R1 wall time times2400/340≈7.06, only after
R1; peak RAM cannot safely be extrapolated linearly. Six-case affordability is
UNQUALIFIED until actual amended measurements exist.

Before MATLAB: require >8 GiB effective RAM headroom, >10 GiB scratch and >3 GiB
Drive quota. External watcher records RSS peak, host/cgroup memory, wall time
and total file growth. Stop at <2 GiB RAM/disk reserve, >1 GiB/file, >2 GiB total
payload, or1200 s from MATLAB PID handshake; job ceiling90 min includes setup
and private delivery. The watcher uses bounded SIGINT→SIGTERM→SIGKILL on the
identified process tree; interrupted files remain UNQUALIFIED. Drive quota is
screened before execution; concurrent external Drive consumption can still
make delivery fail. No successful transport is claimed unless readback finishes.
A killed runner/job can prevent publication; timeout/OOM never counts as PASS.

## Workflow and owner-local5 s command

The workflow remains `if: ${{ false }}` and has no manual dispatch. S is the
reviewed source commit; E changes only this workflow (reviewed SHA plus enable
predicate); T changes only WK08_PACK_TRIGGER.txt, with exact commit message
`WK08_PACK_340S_ONE_SHOT_20261102`. It rejects attempts other than1 and mismatched
S→E→T ancestry. Future enabling is outside this PR. Private intent
WK08_PACK_340S_ATTEMPT_INTENT_20261102.json is reserved before MATLAB; failure
consumes the allowance. No automatic retry or reuse of WK07's marker.

Owner-local diagnostic, on his own pinned MATLAB only:

```matlab
addpath('/path/to/repo/jte-public');
WK08_local5('/private/fresh-M2-bundle','/path/to/pinned-vendor');
```

The private bundle contains M2340Source.slx, m2340_manifest.json, the listed
receipt/proof inputs and source_workspace.mat from the existing private M2
transport. Copy it fresh; preserve receipt hashes. The script rebases only the
local log directory to a fresh local5logs, runs exactly5 simulated seconds,
uploads nothing and produces LOCAL_5S_DIAGNOSTIC_ONLY. Never point it at R1's
used output bundle. It needs the same vendor project/dependencies and exact
build. The local5 diagnostic is not R1 or a full physical qualification.

## Every file changed

All files below are new; existing controllers, builders and workflows are untouched.

| File | Purpose |
|---|---|
| .github/workflows/wk08-pack-one-shot.yml | Disabled protected S→E→T one-shot |
| actuator-amendment/WK08_README.md | Design, run sheet and review limitations |
| actuator-amendment/WK08_sparse_sets.csv | Fixed 8/16 geometric channel sets |
| jte-public/WK08_PACK_TRIGGER.txt | Fresh inert marker |
| jte-public/WK08_structFingerprint.m | Extended structural contract |
| jte-public/WK08_inject.m | Exact default bypass; bias then subset |
| jte-public/WK08_sparseSet.m | Read fixed CSV subset |
| jte-public/WK08_prepare.m | Fresh derivative and seven private To File roles |
| jte-public/WK08_run.m | Single R1/local5 simulation definition and gates |
| jte-public/WK08_entry.m | Private CI diagnostics and watchdog handshake |
| jte-public/WK08_local5.m | Owner-only 5 s local entry |
| jte-public/WK08_private_io.py | Private intent/input/readback transport |
| jte-public/WK08_watch.py | External resource limits, no MATLAB launch |

## Short self-check

- [x] Base and owner decisions inspected; vendor SHA checked statically.
- [x] Default injection makes no structural edit; assertion implemented.
- [x] CSV has8/16 unique indices,1/2 per module, in1..312; no temperatures used.
- [x] Only new source/docs/CSV/workflow files; no SLX/MAT/secrets committed.
- [x] Workflow disabled, new marker and intent, no dispatch/auto-retry/public artifacts.
- [x] Python syntax and source-level workflow/CSV checks only.
- [ ] Claude independent review.
- [ ] MATLAB compile, fingerprint assertions, file clocks, t0 and R1 gates executed.

Stop here and wait for Claude. No PASS or run result is fabricated.
