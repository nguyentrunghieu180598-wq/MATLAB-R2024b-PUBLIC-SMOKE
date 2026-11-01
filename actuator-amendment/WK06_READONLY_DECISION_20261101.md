# WK06 read-only decision — 01 Nov 2026

Scope: Issue #67 / #68; source-only and metadata/receipt review. No MATLAB, pack simulation, private MAT export, workflow trigger, new receipt, or scientific G5 acceptance.

## WK06-A: `WK06_BLOCKED_PRECONDITION`

The distinct owner approval required by Issue #67 for exactly one **nonbattery** WK05 fixture trial is not present in this handoff. Earlier B0L340 physical approval is a different scope and remains unused. Therefore no MATLAB trial was dispatched. PR #66 at `b508de5580534593bcac3018f16e1ad04d5c4789` is source-only; its Python syntax and GitHub readback passed, but actual R2024bU10 fixture/API, current license/quota, protected branch/environment permissions, private OAuth/Drive write and remote readback have not been freshly qualified for a WK06 attempt. Minimum next gate: explicit owner approval for ONE nonbattery 0-stop/OP/direct–restore trial, then a fresh protected preflight (branch/environment, pinned runtime/license, no-cost quota, owner-private sink, source SHA and fresh paths) before any execution. A failed preflight stops without spending the trial. G-M3 and G5 remain unaccepted.

## WK06-B: `WK06_B_ACCESS_BLOCKED` for raw-archive verification; metadata triage completed

The connected owner Drive exposes protected engineering reports and M3/M2 receipts, but this review did not obtain the five original G5 B0L/C0 MAT streams or their complete remote-byte receipts. Consequently no independent native-row, 312-vector, clock or SHA recalculation is claimed. Public-safe evidence: PR #57 / run 40620218579 recorded 6 structural PASS, 6 UNAVAILABLE; PR #58 / run 40622268033 recorded conditional filter-envelope flags in five archived streams. PR #55 / run 40549582869 contains the prior nine-case fixed-state feasibility audit. M2 compile run 40701917441 established four 1/1/1/312 double ToFile clones and unchanged source graph, but no physical trajectory. M2 340 static run 40735694599 established a short logger clone, also without battery execution.

| Gate | Decision | Missing science/evidence |
|---|---|---|
| E00 source/runtime pin | PASS as archived metadata | Rebind every candidate raw MAT to its exact case/source SHA before reuse. |
| E01 original B0L/C0 raw existence and SHA | NEEDS-EVIDENCE | Exact owner-private MAT bytes and independent readback not opened here. |
| E02 native 312-vector and 1800–2400 s completeness | NEEDS-EVIDENCE | No independently read original native vector/clock; no confirmatory channel rank. |
| E03 source continuous TF integrity | REJECTED for thermal inference | Historic excursion and missing accepted-event/numerical proof; use source runs as diagnostics only. |
| E04 original/fine solver convergence | NEEDS-EVIDENCE | Independent postfilter, both windows and T312 error budget missing. |
| E05 M2 four-ToFile graph and compiled widths | PASS as static evidence | Native file clocks, solved IC and physical runtime unmeasured. |
| E06 amended model physical baseline | NEEDS-EVIDENCE | M3/hidden t0, first and second windows, numerical refinement, Ts sensitivity. |
| E07 C0/C1 causal contrast and fixed channels | REJECTED as confirmatory with archived cases | B0L final-600-s descending selection, baseline parity, immutable IDs and uncertainty not established. |

Archived original thermal data are quarantined from quantitative G5/G6 thermal conclusions. They can support provenance, anomaly localization and exploratory fixed-state controller audits with their original labels. The prospective amended C0/C1 protocol requires a qualified B0L 0–2400 s baseline and case-matched solver/IC/source frame; the preapproved B0L 0–340 s run, if eventually qualified and used, answers only the first-window feasibility question. No new physical run is justified by this metadata audit alone.

Next read-only action is privileged retrieval of the existing five MAT + receipts and source/clock manifest, without rerun, to close E01/E02/E04 where the bytes allow. Separately, after owner authorization, WK06-A may test only the tiny nonbattery API gate. No numeric sensor IDs, temperatures or time fractions are reported.

## 01 Nov targeted P0 preflight and selector erratum

| Condition | Read-only result | Exact limit |
|---|---|---|
| R2024b Update 10 build/license | HISTORICAL PASS; CURRENT UNKNOWN | Protected M2 run 40701917441 recorded build 24.2.0.3361896 and successful static compile. No present WK06 license entitlement or runner availability queried/executed. |
| GitHub branch/environment | UNKNOWN | WK05 branch and draft PR exist. Public rulesets list is empty; branch-protection read returned 403 `Resource not accessible by integration`. No protected-environment branch eligibility or secret mapping can be inferred. |
| Owner-private Drive | READ PASS; WRITE/READBACK UNKNOWN | Connected owner account read restricted M2 reports/receipts. No fresh OAuth write, free-byte quota or remote-byte round trip was attempted. |
| No-cost resource quota | UNKNOWN | No current MATLAB Actions allowance, Drive free-byte budget or fresh cgroup capacity measurement. Historical static resource logs cannot certify current capacity. |
| Separate authorization | FAIL / ABSENT | Issue #67 explicitly requires distinct owner permission for exactly one nonbattery trial. The B0L340 approval cannot be transferred. |

Required owner wording, after all other gates are reviewable: “Tôi phê duyệt đúng 01 lượt thử **không dùng mô hình pin** WK06-A trên MATLAB R2024b Update 10: zero-stop/ModelOperatingPoint/direct–restore theo WK05 PR #66; chỉ dùng tài nguyên hiện có và Drive riêng, không tự chạy lại.” This is the minimum *scope* of approval, not a claim that preflight passed.

Selector correction: JTE050/054 defines a native-time-weighted **mean**, descending ranks 1/156/312 on original zero-bias B0L 1800–2400 s, with channel-ID ascending ties. The Chat v02 Python candidate implements a trapezoid over native ordered rows and retains duplicate timestamps. The original `JTE050_selectNativeChannels.m` bytes were not found in the connected repo or Drive; JTE050's documented source contract additionally rejects more than two event sides at a timestamp. The v02 code currently has no explicit `>2` duplicate-time rejection, so exact MATLAB parity remains **UNKNOWN**. Neither v01 MAX ranking nor v02 outputs may freeze channels before a G5-qualified baseline and exact source-oracle review. No new selection was computed.

