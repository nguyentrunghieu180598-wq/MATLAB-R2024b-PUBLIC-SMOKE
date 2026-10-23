# JTE-036 — Corrections grounded in the MathWorks R2024b model
Source original pinned tag 24.2.1.5 (SHA256 unchanged); JTE034 Work source inspection 23/10/2026.

## Signal dictionary (critical for G5–G7)
- `jteUcore`: `Battery Control/FlwR_calc` OUT1. **PRE** `sensor dynamics 1` TransferFcn, with denominator `[1e-3 1]`. Not the same as the actual FlwR fed to the pack or pump calculation.
- Actual plant flow command: OUT of `sensor dynamics 1`. MUST be separately logged and its unit/semantics verified on a disposable model copy.
- Pump power: OUT of `Pump_power_calc` downstream of plant FlwR, `Saturation [0,500]` following `gain500` in official MathWorks source. Record power output separately and integrate only on audited time base.
- `jteTminTrue`: existing `min-max T` reducer OUT1 `plot T` concatenates two extrema (min,max candidate). This is a two-column diagnostic, not an independently logged Tmin sensor. Verify min Function in compiled source before labeling channel 1.
- `jteAmbient`: upstream `Constant3` sample time `inf`. Single event can be correct; compare scalar resolved values and source/units, not force 2400 dynamic timestamps.

## MATLAB code changes
- `JTE034_metrics` now fails closed on `pumpLinkVerified=true` when only jteUcore is available. It cannot report pump energy by integrating a pre-filter command.
- `JTE036_pumpEnergyFromLoggedPower` requires independently logged physical pump power (W), provenance confirmation, and verified sample-time semantics.
- `JTE036_pump_guard_test` is a synthetic software test only.
- DO NOT change original plant, source SLX, or FlwR_calc; DO NOT merge automatically or run new 2400s jobs for this patch.

## G5 real blocker
Existing eight artifacts are authenticated only at SHA/CRC/envelope level, not decrypted with GCM and independently analyzed. To obtain scientific PASS the team needs a trusted PRIVATE cloud work area authorized to read RSA private key without exposing it in public repo, Chat messages or CI logs. Until then, G5 numeric / solver quantitative review = BLOCKED; G6 pilot results cannot be used to conclude impacts.
