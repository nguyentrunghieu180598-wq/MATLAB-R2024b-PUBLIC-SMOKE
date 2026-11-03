# postproc/ — two-margin post-processing (hub BTMS-IJEHV-hub issue #5)

Author: Claude. Synthetic data only until reviewed R-runs exist. No MATLAB, no raw data here.

- `margins.py`: controller law (`u_law`), direct corrupted-maximum evaluation, per-step margins (true max, sensed max, sparse deficit s, masking margin M, threshold distance d), the two-margin theorem (`predicted_downshift`), direct command change, interval extraction and `lock_predictions` (JSON + SHA-256 for freezing predictions on the baseline before closed-loop runs).
- `test_margins.py`: inclusive thresholds; a 3-channel hand-worked example; rejection of a bias on an unsensed channel (mirrors WK08 B1); 2×20 000 random states reproducing the hub oracles with 0 mismatches; deterministic lock hash.

Channel indices are 0-based here; `jte-public/WK08_sparse_sets.csv` is 1-based (subtract 1).
- `margins.predicted_upshift`: positive-bias theorem (R11): higher command iff the inflated reading reaches the next threshold above the true maximum (inclusive). `lock_predictions` now checks theorem = direct evaluation for both signs.
- `runlog.py`: validated reader (finite, t0 = 0, monotone time, role width, horizon) for a PLAIN export (`time` n×1, `data` n×w; MAT v5, MAT v7.3 or NPZ) plus a zero-order-hold aligner. **Dependency:** the native To File logs are `SaveFormat='Timeseries'` (MCOS objects), which Python cannot decode. A reviewed MATLAB export step (after the run, inside the private job) must write the plain arrays; this is a future Codex task, not done here.
- `metrics.py`: T_peak, time above Tamb+5/7.5 K, time-averaged command J_u, number of command switches, pump energy (trapezoid; the left-rectangle value is kept as an integration-rule check) from the LOGGED `pumpPower`; numerical-sensitivity band from R2 vs R3/R4; an effect is RESOLVED only if strictly above the band.
- `figures.py`: margin time series and the (Δ_eff, d) margin map; any synthetic figure carries a visible "SYNTHETIC - NOT A RUN RESULT" watermark.
- `test_pipeline.py`: 2×20 000 random states for the positive-bias theorem (0 mismatches), reader round-trips and six rejection cases, hand-computed metrics, band logic, figure smoke test.

Run: `cd postproc && python3 -m pytest -q -p no:cacheprovider` (numpy, scipy, h5py, matplotlib).

Closed 03/11: oracle equivalence with the hub file is now tested in `test_freeze.py`.
- `selector.py` (03/11): JTE-050 v02 selector from the accepted R2 run (trapezoid time-weighted mean over 1800–2400 s, window ends interpolated, descending, ties by ascending 1-based index). Its JSON is exactly what `jte-public/WK09_run_definitions.resolve()` (PR #77) consumes; checked end to end on synthetic data.
- `freeze.py` (03/11): freezes predictions for R5–R13 on R2 with two references, full sensing and the paired b = 0 control (R6/R7/R11→R5, R8/R9→R12, R10→R13), and returns the SHA-256 to record in the hub before any of R5–R13 runs.
- `test_freeze.py`: 20 000 random states reproduce the hub oracle `tools/two_margin_oracle_static.py` (hub SHA-256 eeb0b06e…, hub @ cace1a7) with 0 mismatches, which closes the open oracle item above; selector window/tie/format tests; freeze determinism, sign checks and rejection of unresolved runs.
