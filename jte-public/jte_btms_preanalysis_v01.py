"""JTE BTMS: source-independent *preanalysis only* (no MATLAB, no G5 PASS).

Methods proposal, not yet owner-approved: select a hot / median / cold modeled
channel deterministically from all eligible 312-channel baseline samples in the
1800-2400 s interval, ranked by per-channel MAXIMUM recorded temperature.
This ranking does not imply 312 physical thermometers. Ties use ascending
1-based channel ID in a descending-temperature order. No interpolation or
native timestamp reordering occurs. All scientific gates require separate
validation of original source files, timing, hidden IC, and event provenance.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

N_CHANNELS = 312
WIN_START_S = 1800.0
WIN_END_S = 2400.0

@dataclass(frozen=True)
class CandidateChannels:
    hot_1based: int
    median_1based: int
    cold_1based: int
    samples_in_window: int
    distinct_times_in_window: int
    duplicate_timestamp_rows_in_window: int
    max_scores_spread_K: float
    ties_at_median_score: int
    classification: str = "PROPOSAL_ONLY_NOT_CERTIFIED_G5"


def proposed_channel_selection(T_K: np.ndarray, t_s: np.ndarray) -> CandidateChannels:
    """Return proposed indices only. DO NOT use on unqualified source for C1.

    Rank channels by max of each modeled channel on 1800 <= time <= 2400.
    Exact native time rows are retained (including duplicates); max is
    invariant to time repetition. No interpolation, statistical replicates,
    or inference about unseen event samples. Externally audit G5 first.
    """
    T = np.asarray(T_K, dtype=np.float64)
    t = np.asarray(t_s, dtype=np.float64)
    if t.ndim != 1 or T.ndim != 2 or T.shape[1] != N_CHANNELS:
        raise ValueError("EXPECTED_NATIVE_N_BY_312_AND_1D_CLOCK")
    if not len(t) or len(t) != T.shape[0] or not np.isfinite(T).all() or not np.isfinite(t).all():
        raise ValueError("MISSING_OR_NONFINITE_DATA")
    if np.any(np.diff(t) < 0):
        raise ValueError("NONMONOTONIC_NATIVE_CLOCK_NO_REORDER_ALLOWED")
    if t[0] > WIN_START_S or t[-1] < WIN_END_S:
        raise ValueError("MISSING_FULL_BASELINE_SPAN")
    mask = (t >= WIN_START_S) & (t <= WIN_END_S)
    tw, Tw = t[mask], T[mask, :]
    if np.unique(tw).size < 2:
        raise ValueError("WINDOW_HAS_INSUFFICIENT_DISTINCT_TIMESTAMPS")
    scores = Tw.max(axis=0)
    if not scores.max() > scores.min():
        raise ValueError("NO_DISTINCT_THERMAL_RANKING")
    ids = np.arange(1, N_CHANNELS + 1)
    ranked = np.lexsort((ids, -scores))
    hot, median, cold = (int(ids[ranked[i]]) for i in (0, (N_CHANNELS - 1)//2, N_CHANNELS - 1))
    return CandidateChannels(
        hot_1based=hot, median_1based=median, cold_1based=cold,
        samples_in_window=int(tw.size),
        distinct_times_in_window=int(np.unique(tw).size),
        duplicate_timestamp_rows_in_window=int(tw.size - np.unique(tw).size),
        max_scores_spread_K=float(scores.max() - scores.min()),
        ties_at_median_score=int(np.count_nonzero(scores == scores[ranked[(N_CHANNELS - 1)//2]])),
    )


@dataclass(frozen=True)
class PeakNumericalScreen:
    delta_peak_reference_K: float
    delta_peak_fine_K: float
    numerical_sensitivity_envelope_K: float
    passes_conservative_screen: bool
    status: str = "NUMERICAL_SENSITIVITY_SCREEN_NOT_SCIENTIFIC_VALIDATION"


def peak_numerical_screen(T0_ref: np.ndarray, Tb_ref: np.ndarray,
                          T0_fine: np.ndarray, Tb_fine: np.ndarray) -> PeakNumericalScreen:
    """Conservative screen, NOT a solver error guarantee or p-value.

    Delta_peak = max_t max_i(Tbias) - max_t max_i(Tzero); not max_t(Tbias-Tzero).
    Estimated numerical sensitivity bound of the contrast is the SUM of
    baseline and bias peak deviations across one finer solver. Does not
    assume equal solver clocks, and cannot qualify clocks/IC/source on its own.
    """
    a = []
    for v in (T0_ref, Tb_ref, T0_fine, Tb_fine):
        z = np.asarray(v, dtype=np.float64)
        if z.ndim != 2 or z.shape[1] != N_CHANNELS or not z.shape[0] or not np.isfinite(z).all():
            raise ValueError("EXPECTED_NONEMPTY_FINITE_N_BY_312")
        a.append(float(z.max()))
    zref, bref, zfine, bfine = a
    contrast_ref = bref-zref
    contrast_fine = bfine-zfine
    envelope = abs(zref-zfine) + abs(bref-bfine)
    passes = abs(contrast_ref) > envelope and contrast_ref*contrast_fine > 0
    return PeakNumericalScreen(contrast_ref, contrast_fine, envelope, bool(passes))


def _selftest() -> None:
    t = np.array([0.0, 1800.0, 2000.0, 2000.0, 2400.0])
    T = np.tile((300.0+0.01*np.arange(N_CHANNELS)), (t.size,1))
    out = proposed_channel_selection(T, t)
    assert (out.hot_1based, out.median_1based, out.cold_1based) == (312, 157, 1)
    assert out.duplicate_timestamp_rows_in_window == 1
    assert out.classification == "PROPOSAL_ONLY_NOT_CERTIFIED_G5"
    try:
        proposed_channel_selection(T, t[::-1]); raise AssertionError('clock rejection missing')
    except ValueError: pass
    try:
        proposed_channel_selection(np.full_like(T,300.), t); raise AssertionError('tie rejection missing')
    except ValueError: pass
    baseline = np.full((4, N_CHANNELS), 300.)
    biased = np.full((4, N_CHANNELS), 300.3)
    fine0 = np.full((7, N_CHANNELS), 300.01)
    fineb = np.full((7, N_CHANNELS), 300.31)
    p = peak_numerical_screen(baseline, biased, fine0, fineb)
    assert p.passes_conservative_screen and abs(p.numerical_sensitivity_envelope_K-0.02)<1e-9
    p2 = peak_numerical_screen(baseline, np.full_like(baseline,300.015), fine0, np.full_like(fineb,300.02))
    assert not p2.passes_conservative_screen
    print('SYNTHETIC_SELECTION_AND_PEAK_SENSITIVITY_SELFTEST_PASS; MATLAB_RUN=0; G5_ACCEPTED=false')

if __name__=='__main__': _selftest()
