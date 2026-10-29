# CH-01 / CH-02 — JTE scientific scope and evidence register, 29 October 2026
**Status:** INTERNAL SCIENTIFIC METHOD / LITERATURE TRIAGE; NO NEW MATLAB, NO ACCEPTED THERMAL RESULTS, NO JTE SUBMISSION. Internal target 14 Nov 2026. This does NOT supersede the owner’s frozen scientific model, approvals, or JTE-058 restrictions on official report/results export.

## Source-of-truth and boundaries
- MathWorks `Battery-Pack-Model-Simscape` tag 24.2.1.5, frozen source SLX SHA `0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0`, MATLAB/Simulink R2024bU10, source load/IC and 300 K reference; 312 **model temperature channels**, NOT 312 asserted physical sensors.
- Source original G5 is not numerically qualified. The amended B0L/C0 10ms actuator family is a **different sampled implementation** (continuous-TF sampling is not waveform-equivalent); no repaired model can inherit the rejected source's thermal validation. Do not change source plant/solver/controller law, bias index or event thresholds mid-study.
- Work WK-01 completed source-only at commit `e12fc6f02cfbb2b124b52f826b92d833183219c6` with **WK01_M3_NO_GO**. The 30ms toy's terminal `inactive` / missing returned Time cannot be certified without effective SimulationMode and StopEvent metadata, not saved in the old evidence. Four terminal ToFile clocks alone are not completed-major or full hidden-t0 evidence. The one approved B0L340 physical observation is UNUSED.

## CH-01 verified scope of literature inventory (REUSED, not 12 new reviews)
Existing owner Drive `JTE 042 01 MA TRAN TAI LIEU DOI CHUNG VA RESEARCH GAP 24102026.md`:
https://drive.google.com/file/d/1t21nfaJsjbRk5RgURSJRO--hnjJDBp2C/view
It lists exactly 12 prioritized owner PDFs (items 1,2,4,6,7,8,9,17,18,19,23,25) with DOI and evidence grade **A=selected PDF sections assessed**, plus a separate 9-paper directly related fault/control comparison F01–F09 whose C grade is metadata/abstract, B public full text. **Do not report all 12 as independently re-reviewed today or full-figure/experimental-data audited.** Priority NEW gap work: full-text compare F05 (2025 JPS), F06 (2026 JES) and F07 (2026 ATE) plus Dey (2016 IEEE TCST), Bhaskar (2025 IEEE TTE) and Naguib (2025 Communications Engineering) before declaring novelty.
Publisher evidence checked 29 Oct: Dey IEEE DOI 10.1109/TCST.2016.2538200 (observer diagnosis/estimation including temperature); Naguib full open article DOI 10.1038/s44172-025-00409-2 (72-cell **air-cooled** pack; eight sensor inputs, sensor/fan/cooling-flow faults). These prior works prohibit a novelty claim over **sensor-fault modeling/detection itself**. Ref: https://ieeexplore.ieee.org/document/7437404 ; https://www.nature.com/articles/s44172-025-00409-2 .

## CH-02 RQ, hypothesis and falsification framework
RQ1 / H1: For the very same 312-element modeled temperature state, negative offset on a frozen channel or channel set S can be masked by unperturbed channels; report all no-effect frames. Proof oracle: for A=max_{i in S} T_i, B=max_{i notin S}T_i, measured maximum=max(A-delta,B) at fixed T. Crossing a specified ideal control threshold theta downward iff B<theta<=A<theta+delta. Source native quantizer around floating-point ULP boundaries is authoritative, not ideal formula alone.
RQ2 / H2: A reduction in measured maximum need not change the source cooling command because of source saturation and 0.25-step quantization, and command change need not imply temperature change. Verify true source `FlwR_calc` law, including actual Ambient input at port2, separately from sample/hold actuator and coolant mass-flow mapping. Treat source normalized command as dimensionless until verified physical mapping.
RQ3 / H3: On identical source load, initial physical operating point and solver, a bias-case's true temperature trace may differ from zero-bias only if command changes propagate through the physical plant. No-effect cases are scientifically valid. Thermal differences are CLAIMABLE only when above a preregistered, justified numerical uncertainty tolerance.
RQ4: Is the result robust to the second frozen source load, fixed-Ts solver refinement and separately frozen actuator Ts sensitivity? No p-values from consecutive deterministic solver rows.

## Frozen comparison hierarchy and NON-negotiable evidence
A. **Fixed-state / exploratory**: 312-channel archived native T, fixed j, delta, source command switch, channel tie/masking. Do not equate with dynamic closed-loop response.
B. **Matched baseline B0L/C0**: cloned amended models, original source load, same full hidden t0 IC, fixed Ts=0.010 s reference, same solver and terminal provenance. `G-M3`, resource/watchdog+protected Drive delivery must PASS first. This phase cannot be declared true from static compile or 20ms toy.
C. **First physical window 0–340s**: only within existing specific owner approval after all gates revalidated, prior 330–334 s negative control and 330–338 s event; full T312 native outputs and nonterminal accepted-major witnesses; no G5 from first window alone.
D. **Long 0–2400s / C0 / C1**: only after distinct scientific approval and resource gate. Freeze channel selection and severity before outcomes, preserve all null cases; compare fixed-Ts solver sensitivity separately from 10ms/5ms actuator implementation sensitivity, and report unknown uncertainty bounds without fabricated equivalence.
E. **Publication**: planned Abstract/Methods/Results/Discussion restricted to true qualified data; title<=20 words, 150–250 word abstract with results, >=5 keywords, IEEE ordered citations, JTE editable DOCX and ethics disclosures.

## CH-01/CH-02 deliverables and status on 29 Oct
- [x] CH01 inventory of 12 prioritized PDFs + source graded preliminary literature/gap matrix EXISTS from 24 Oct owner Drive and was **verified/reused** today; does not close the higher full-text novelty gate.
- [x] CH02 RQ/Hypothesis hierarchy and three-layer evidence contract drafted HERE for author review; freeze *exact bias values, j selection, second load and numerical tolerances* only AFTER owner/source-based preregistration, not retrospectively.
- [ ] F05–F07 publisher/full-text scientific overlap audit; G-LIT **NOT PASSED**.
- [ ] WK02 technical design signoff (no MATLAB); G-M3 **NOT PASSED**.
- [ ] G-340/G-ZERO/G-NUM/G-FAULT scientific simulation; **NOT PASSED**.

Evidence status is separate from checklist status; no false acceptance, no public private model/thermal MAT or secrets.
