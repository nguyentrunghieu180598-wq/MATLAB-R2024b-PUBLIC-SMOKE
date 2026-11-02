# postproc/ — two-margin post-processing (hub BTMS-IJEHV-hub issue #5)

Author: Claude. Synthetic data only until reviewed R-runs exist. No MATLAB, no raw data here.

- `margins.py`: controller law (`u_law`), direct corrupted-maximum evaluation, per-step margins (true max, sensed max, sparse deficit s, masking margin M, threshold distance d), the two-margin theorem (`predicted_downshift`), direct command change, interval extraction and `lock_predictions` (JSON + SHA-256 for freezing predictions on the baseline before closed-loop runs).
- `test_margins.py`: inclusive thresholds; a 3-channel hand-worked example; rejection of a bias on an unsensed channel (mirrors WK08 B1); 2×20 000 random states reproducing the hub oracles with 0 mismatches; deterministic lock hash.

Channel indices are 0-based here; `jte-public/WK08_sparse_sets.csv` is 1-based (subtract 1).
Next: native To-File reader for the WK08 log schema, margin-map figures, comparison metrics (ΔT_peak, J_u, ΔE_pump) with the numerical-sensitivity band (R3/R4).
