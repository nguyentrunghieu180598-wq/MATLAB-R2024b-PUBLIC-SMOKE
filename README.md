# MATLAB-R2024b-PUBLIC-SMOKE

## WK08 source delivery — R1 and measurement injection

Scope: hub Issue #1; context: public Issue #73. Base: `f7ba843e0101eb8bf94d5f4ec217fea45d4b1ff7`
on `codex/wk06-nonbattery-only-20261101`. Author: Codex. Independent reviewer: Claude.
**SOURCE ONLY — MATLAB/CI not executed; no workflow enabled or triggered.**

Design handoff: `WK08_PHYSICAL_DESIGN_READY_FOR_OWNER_REVIEW`.
This is an author handoff label, not an independent GO, runtime qualification, physical result or G5 PASS.
See [run sheet](actuator-amendment/WK08_R1_DESIGN.md) for provenance, limits and pending gates.

### Every changed file

| File | Purpose |
| --- | --- |
| `README.md` | Delivery inventory and author checklist |
| `actuator-amendment/WK08_R1_DESIGN.md` | R1 contract, geometric rule, t0 decision, resource estimates, owner handoff |
| `jte-public/BTMS_WK08_structFingerprint.m` | WK07 fingerprint extended to physical connectivity, IC workspace, scripts and comments |
| `jte-public/BTMS_WK08_inject.m` | Neutral literal no-op, or single-channel additive bias then committed subset before min-max T |
| `jte-public/BTMS_WK08_sparseSets.m` | Load and validate fixed channel indices |
| `jte-public/WK08_sparse_sets.csv` | 312/16/8 sets, module sizes and geometric positions |
| `jte-public/BTMS_WK08_prepare.m` | Fresh M2 derivative with eight private constant-name To File sinks |
| `jte-public/BTMS_WK08_run.m` | Exact-build/SHA/fingerprint gates, one direct-start initialization and native output validation |
| `jte-public/BTMS_WK08_dryRun5s.m` | Separately approved owner-local 5s entry; never called by workflow |
| `jte-public/WK08_private_gate.py` | S→E→T authorization, private archive provenance, intent, ACL and readback receipt |
| `jte-public/WK08_supervise.py` | One future MATLAB process, external memory/disk/wall monitor and bounded termination |
| `jte-public/test_WK08_guards.py` | Offline authorization and sensor topology checks |
| `jte-public/JTE063_streaming_drive.py` | One new schema whitelist entry; transport unchanged |
| `.github/workflows/wk08-pack-one-shot.yml` | Disabled R1 workflow; exact future marker only |

No existing MATLAB file is modified. The vendor model, original continuous TF, controller law and solver
remain unchanged. R1 uses the already-approved sampled M2 derivative, not an alteration of the vendor TF.
The v01 MAX-based selector is neither imported nor called.

### Author self-check list (not Claude's review)

- [x] New `codex/wk08-*` branch starts at the specified WK06 commit.
- [x] Sensed vector is actually reduced to 312/16/8 elements before MinMax3; no unsensed dummy channels.
- [x] Neutral injection does not add any block/line/workspace variable; extended fingerprint equality is asserted.
- [x] CSV sensor positions are fixed by geometry; no temperature/rank input.
- [x] Four native M2 roles retained plus true max, measured max, pump power, 1s channel observation.
- [x] R1 is B0L, Ts=.01, 0–340s, b=0, S=all; exact runtime/source SHA and output gates in source.
- [x] One-shot intent and protected private full-byte readback; no public MAT/artifact upload.
- [x] New marker path is reserved but marker file is absent in S, preventing a source-push trigger.
- [x] Job remains `if: ${{ false }}`; reviewed SHA is unresolved until independent review.
- [x] Local offline Python checks only; see handoff/PR for actual check output.
- [ ] Owner-local 5s test (separate approval; not performed).
- [ ] Claude independent code/design review.
- [ ] Owner approval and future E/T actions; no run approval exercised by Codex.
- [ ] Physical build/compile, file clocks, hidden Simscape IC, measured time/RAM and 340s completion (unverified).
