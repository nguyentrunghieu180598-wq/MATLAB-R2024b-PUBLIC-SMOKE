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

Open: the oracle-equivalence tests re-implement the hub `tools/two_margin_oracle_*.py` logic; a byte-for-byte comparison against those files still has to be run where the hub is reachable.
