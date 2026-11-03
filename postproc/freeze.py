"""Freeze the static predictions for R5..R13 on the accepted R2 trajectory (hub #5, D9 gate).

Input: R2 plain export (t, T with 312 columns) and the resolved WK09 run definitions
(output of WK09_run_definitions.resolve with the frozen v02 selector; 1-based channels).
Two references per run, both pre-registered:
  * full_sensing: command change against the unbiased 312-channel reading (Methods 2.5);
  * paired_control: the bias effect alone, against the matching b = 0 run with the same
    sensor set (R6, R7, R11 -> R5; R8, R9 -> R12; R10 -> R13). Here a command changes iff
    a threshold lies in (lower reading, higher reading] (hub tools/two_margin_oracle_static.py).
Output JSON is hashed (SHA-256); the hash is recorded in the hub before any of R5..R13 runs.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

import margins as P

PAIRED_CONTROL = {"R6": "R5", "R7": "R5", "R11": "R5", "R8": "R12", "R9": "R12", "R10": "R13"}
PREDICTED_RUNS = ["R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "R13"]


def to_case(run):
    if run.get("resolution") != "SOURCE_CONTRACT_ONLY_NOT_RUN_AUTHORIZATION" or run.get("channel") is None:
        raise ValueError(f"FREEZE_UNRESOLVED_{run.get('id')}")
    sensed = tuple(int(c) - 1 for c in run["subset"])
    return P.Case(run["id"], sensed, int(run["channel"]) - 1, float(run["bias_K"]))


def paired_change(T, case, control, tamb=P.TAMB_K):
    r1, r0 = P.measured_max(T, case), P.measured_max(T, control)
    direct = np.sign(P.u_law(r1, tamb) - P.u_law(r0, tamb)).astype(int)
    lo, hi = np.minimum(r0, r1), np.maximum(r0, r1)
    th = np.array(P.THRESHOLDS_K) + tamb
    crossed = ((lo[:, None] < th[None, :]) & (th[None, :] <= hi[:, None])).any(axis=1)
    if not np.array_equal(crossed, direct != 0):
        raise AssertionError(f"oracle/direct mismatch (paired): {case.name}")
    return direct


def freeze(t, T, resolved_runs, selector_sha256, tamb=P.TAMB_K):
    T = np.atleast_2d(np.asarray(T, float))
    if T.shape[1] != 312:
        raise ValueError("FREEZE_WIDTH")
    runs = {r["id"]: r for r in resolved_runs}
    if sorted(runs) != sorted(PREDICTED_RUNS):
        raise ValueError("FREEZE_RUN_SET")
    cases = {k: to_case(runs[k]) for k in PREDICTED_RUNS}
    full, _ = P.lock_predictions(t, T, [cases[k] for k in PREDICTED_RUNS], tamb)
    out = {"selector_SHA256": selector_sha256, "baseline": "R2", "full_sensing": full["cases"],
           "paired_control": {}}
    for k, ref in PAIRED_CONTROL.items():
        ch = paired_change(T, cases[k], cases[ref], tamb)
        out["paired_control"][k] = {"control": ref,
                                    "lower_command_intervals_s": P.intervals(t, ch < 0),
                                    "higher_command_intervals_s": P.intervals(t, ch > 0)}
    blob = json.dumps(out, sort_keys=True, separators=(",", ":")).encode()
    return out, hashlib.sha256(blob).hexdigest()
