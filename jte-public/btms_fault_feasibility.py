"""Read-only analytical gate for negative temperature bias in a Max/quantizer controller.

Source context: 312 modeled cell-temperature channels, 300 K controller reference;
ideal temperature thresholds 305 K / 307.5 K for the pinned 0.25-step law.
This is a fixed-state theorem, NOT Simulink, plant physics, physical sensors,
a native floating-point controller oracle, a G5 certificate, or thermal output.

No Drive/network/files, no model edits, no source data included.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

CELL_COUNT = 312
REFERENCE_K = 300.0
IDEAL_THRESHOLDS_K = (305.0, 307.5)


@dataclass(frozen=True)
class NegativeBiasEligibility:
    threshold_K: float
    bias_magnitude_K: float
    native_frames: int
    eligible_frames: int
    eligible_frames_with_at_most_three_faults: int
    boundary_ambiguous_frames: int
    min_required_channels_per_frame: np.ndarray
    eligible_mask: np.ndarray
    near_threshold_mask: np.ndarray


def validate_native_temperature_matrix(T_K: np.ndarray, time_s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Validate only dimensions and original row-clock order; never interpolate."""
    T = np.asarray(T_K, dtype=np.float64)
    t = np.asarray(time_s, dtype=np.float64).reshape(-1)
    if T.ndim != 2 or T.shape[1] != CELL_COUNT:
        raise ValueError("EXPECTED_N_BY_312_TEMPERATURE_MATRIX")
    if T.shape[0] != t.size or not t.size or not np.isfinite(T).all():
        raise ValueError("NONFINITE_OR_MISALIGNED_NATIVE_T")
    if not np.isfinite(t).all() or np.any(np.diff(t) < 0):
        raise ValueError("INVALID_UNSORTED_NATIVE_CLOCK")
    return T, t


def fixed_state_negative_bias_eligibility(
    T_K: np.ndarray, time_s: np.ndarray, bias_magnitude_K: float,
    threshold_K: float, max_fault_channels: int = 3,
) -> NegativeBiasEligibility:
    """Prove ideal threshold crossing feasibility for a fixed original T vector.

    At time t, a group S biased by -delta can lower maximum temperature
    across theta iff all originally hot channels (T_i >= theta) are in S
    AND theta <= Tmax < theta + delta.
    Hence minimum eligible |S| = count(T_i >= theta), where the latter
    condition is met; otherwise it is infinity.

    Ties matter. Near exact floating-point boundaries are FLAGGED, not
    silently rounded or interpreted as native Simulink switching.
    """
    delta = float(bias_magnitude_K)
    theta = float(threshold_K)
    if not np.isfinite(delta) or delta <= 0 or not np.isfinite(theta):
        raise ValueError("INVALID_BIAS_OR_THRESHOLD")
    if not 1 <= max_fault_channels < CELL_COUNT:
        raise ValueError("INVALID_FAULT_GROUP_BOUND")
    T, _ = validate_native_temperature_matrix(T_K, time_s)
    Tmax = np.max(T, axis=1)
    hot_count = np.sum(T >= theta, axis=1).astype(np.int64)
    eligible = (hot_count > 0) & (Tmax < theta + delta)
    kmin = np.where(eligible, hot_count, np.inf)
    # Diagnostic ONLY. A complete native MATLAB-law boundary analysis needs
    # actual source arithmetic and its inherited ULP budget.
    budget = 64.0 * np.spacing(max(1.0, abs(theta), abs(theta + delta)))
    boundary = (np.abs(Tmax - theta) <= budget) | (np.abs(Tmax - (theta + delta)) <= budget) | np.any(
        np.abs(T - theta) <= budget, axis=1
    )
    return NegativeBiasEligibility(
        threshold_K=theta, bias_magnitude_K=delta, native_frames=int(T.shape[0]),
        eligible_frames=int(np.count_nonzero(eligible)),
        eligible_frames_with_at_most_three_faults=int(np.count_nonzero(eligible & (kmin <= max_fault_channels))),
        boundary_ambiguous_frames=int(np.count_nonzero(boundary)),
        min_required_channels_per_frame=kmin,
        eligible_mask=eligible, near_threshold_mask=boundary,
    )


def fixed_group_threshold_crossing(
    T_K: np.ndarray, time_s: np.ndarray, group_1based: tuple[int, ...],
    bias_magnitude_K: float, threshold_K: float,
) -> np.ndarray:
    """Fixed GROUP only; return original-row boolean. No dynamic closed loop."""
    T, _ = validate_native_temperature_matrix(T_K, time_s)
    if not group_1based or len(set(group_1based)) != len(group_1based):
        raise ValueError("INVALID_GROUP")
    indices = np.asarray(group_1based, dtype=np.int64)
    if np.any(indices < 1) or np.any(indices > CELL_COUNT):
        raise ValueError("INVALID_GROUP_INDEX")
    delta = float(bias_magnitude_K)
    theta = float(threshold_K)
    if not np.isfinite(delta) or delta <= 0 or not np.isfinite(theta):
        raise ValueError("INVALID_BIAS_OR_THRESHOLD")
    before = np.max(T, axis=1)
    altered = T.copy()
    altered[:, indices - 1] -= delta
    after = np.max(altered, axis=1)
    return (before >= theta) & (after < theta)


def selftest() -> None:
    t = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
    T = np.full((6, CELL_COUNT), 300.0)
    T[0, 0] = 305.6          # one-hot eligible
    T[1, :4] = 305.2         # four hot cells: impossible with max 3
    T[2, 0] = 307.0          # equality of Tmax = theta + 2: NOT eligible
    T[3, 0] = 305.0          # threshold equality: eligible (flag ULP)
    T[4, 0] = 304.9          # below threshold: NOT eligible
    T[5, 0] = 305.2; T[5, 1] = 305.1  # two hot: one-fault masked
    r = fixed_state_negative_bias_eligibility(T, t, 2.0, 305.0, 3)
    assert r.eligible_mask.tolist() == [True, True, False, True, False, True]
    assert r.eligible_frames_with_at_most_three_faults == 3
    assert np.isinf(r.min_required_channels_per_frame[2])
    assert r.min_required_channels_per_frame[1] == 4.0
    assert fixed_group_threshold_crossing(T, t, (1,), 2., 305.).tolist() == [
        True, False, False, True, False, False]
    assert fixed_group_threshold_crossing(T, t, (1, 2), 2., 305.)[-1]
    assert r.near_threshold_mask[2] and r.near_threshold_mask[3]
    try:
        bad = T.copy(); bad[0, 0] = np.nan
        fixed_state_negative_bias_eligibility(bad, t, 2., 305.)
        raise AssertionError("NONFINITE_INPUT_MUST_BE_REJECTED")
    except ValueError:
        pass
    print("FIXED_STATE_SYNTHETIC_THEOREM_SELFTEST_PASS; PHYSICAL_RUN=0; G5_ACCEPTED=false")


if __name__ == "__main__":
    selftest()
