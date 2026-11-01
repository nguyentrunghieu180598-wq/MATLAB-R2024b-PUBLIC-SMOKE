# CH-03 / CH-04 — JTE claim–evidence matrix and acceptance rules (01 Nov 2026)

**Status: INTERNAL SCIENTIFIC METHODS ONLY. No qualified BTMS thermal results, G-M3 NO-GO, G5 NOT ACCEPTED; do not submit or claim results.** Fixed model MathWorks Battery-Pack-Model-Simscape tag24.2.1.5, MATLAB R2024bU10, 312 modeled temperature channels, NOT 312 certified physical sensors. This file extends JTE-040/042 and the CH03 29 Oct draft, does not replace owner's authorized run gates.

## Predeclared candidate channel selection (author approval needed BEFORE C1)
On a qualified full 0–2400s C0 zero-bias T312 trace, window W=[1800,2400] s, define **candidate** channel score `S_i=max(T_true,i(t_k),t_k in W)`. Rank 312 channels by descending `S_i`, tie break by ascending original one-based index. Proposed hot=rank1, median=rank156, cold=rank312; freeze exact IDs in owner-private manifest with original source/clone/model/clock hashes **before** new C1 outcomes. All-equal scores => reject thermal ranking. Report tied-median count and sensitivity to sampling; per-channel sampled maximum can be sensitive to brief transients. Do not call these commercial sensor positions.

**ACTUAL independently selftested synthetic-only Python implementation** (01 Nov; no MATLAB, no private data):
https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/blob/chat/jte-fault-feasibility-audit-20261029/jte-public/jte_btms_preanalysis_v01.py
Commit `15395cc7fc889f88ed3bb9d0c9bb2d381aa69265`. Tests include out-of-order native clock rejection, duplicate time retention, deterministic 312-element rank, total thermal tie rejection and numerical sensitivity screening. Current code returns only `PROPOSAL_ONLY_NOT_CERTIFIED_G5`; it cannot attest to physical hidden IC, source SHA, logger or complete event coverage. **This ranking is NOT yet frozen by the author.**

## Prespecified manuscript outcome definitions
For matched C0/C1 with true modeled temperature:
- `Tmax,true(t)=max_i T_true,i(t)` (K), `Tmax,meas(t)=max_i (T_true,i(t)+b*1{i=j})`. At a fixed state, a negative bias can be masked by hotter unaffected channels; this algebra does NOT prove a changed closed-loop plant.
- `DeltaTpeak=max_t Tmax,true,C1(t) - max_t Tmax,true,C0(t)` (K) is a **difference of separate peaks**; never replace by `max_t[Tmax,C1(t)-Tmax,C0(t)]`. Show each peak time/horizon and source.
- `J_u=integral |u_core,C1-u_core,C0| dt` has unit **seconds** if normalized u is dimensionless; timestamp event semantics and ZOH/hold logic must be certified before integration.
- Pump energy must come from a verified native output in W, integrated to J/Wh; don't multiply the normalized core command by source-assumed 500W. Thermal threshold excursion requires sourced limit, never invent one.
- Primary `b=-2K` hot/median/cold C1 cases after qualified baseline. Later b=-1/-3 K and second load are conditional Tier B, not claims of performed experiments.

## Conservative numerical screening (NOT certified error bound)
At *fixed actuator Ts*, solver reference and finer solver, let `P0ref,P0fine,Pbref,Pbfine` be individual true temperature peaks. `epsilon_peak = abs(P0ref-P0fine)+abs(Pbref-Pbfine)`; `DeltaTpeak_ref=Pbref-P0ref`. A conservative *sensitivity screen* asks `abs(DeltaTpeak_ref)>epsilon_peak` AND same sign in the finer run. A single solver refinement is not a rigorously guaranteed numerical error bound; required independent checks remain time/event alignment, convergence, t0/IC, model changes and experimental limitations. Null outcomes are valid if reported. Never assign p-values to deterministic time-row pseudo-replicates.

## Claim–evidence gate table
| ID | Scientific claim | Required first-party evidence | 01 Nov state |
|---|---|---|---|
| E00 | Same pinned model/input/IC, documented source amendment | source+clone SHA, controller wiring, signed config, role clocks | M2 static only |
| E01 | Logger/initial state/terminal provenance trusted | accepted-major nonterminal records; full native ToFile + terminal execution info; t0 full-state or independently approved direct-start protocol | **NO-GO** |
| E02 | B0L/C0 zero bias equivalent | full 0–2400s comparison, same load/IC solver, error envelope | NO EVIDENCE |
| E03 | j_hot/j_mid/j_cold not post hoc | accepted full C0 baseline, predeclared ranking + indices and SHA manifest recorded *before bias* | METHOD PROPOSAL ONLY |
| E04 | Bias changes selector/controller | C1 native Ttrue/Tmeas, native core command incl quantizer, event time | NO EVIDENCE |
| E05 | Bias changes *true* pack thermal response | same-horizon full T312 C0/C1, peak/spread/clock | NO EVIDENCE |
| E06 | Thermal impact robust to numerical changes | fixed Ts solver refinement, independent actuator-Ts sensitivity if authorized, explicit uncertainties | NO EVIDENCE |
| E07 | Novelty and discussion grounded | full-text nearest sensor/thermal fault comparison + E00–E06 | PROVISIONAL |

**GO/NO-GO**: A GitHub CI success, unexecuted MATLAB helper, a 30ms toy or a 0–340s first-window *alone* never completes E01–E06. An author-side deadline (14 Nov) does not relax gates. The Work WK03 design at https://github.com/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/pull/64 is ready for source review, but no recorded WK04 MATLAB validation occurred as checked today.

**JTE official checklist checked 01 Nov:** https://jte.edu.vn/index.php/jte/about/submissions ; https://jte.edu.vn/index.php/jte/for-authors . A4 ≤10 pp, 150–250-word abstract with real results, ≥5 keywords, IMRAD, IEEE and editing DOCX; ethics and GenAI disclosure. Draft Introduction/Methods can proceed, but no invented Results/Conclusion.
