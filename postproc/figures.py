"""Margin-map figures (hub issue #5). Matplotlib, Agg backend, no display.

margin_timeseries: d(t), M(t), s(t) on the baseline with the bias magnitude |b|,
                   shading where the theorem predicts a lower command.
margin_map:        every baseline time step as a point (Delta_eff, d); the region
                   d < Delta_eff is the predicted-downshift region. Colour = case.
Figures built from synthetic data must be labelled as such (the 'synthetic' flag puts
a visible watermark) so they can never be mistaken for run results.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from margins import margins, effective_underreading, predicted_downshift  # noqa: E402


def _mark(fig, synthetic):
    if synthetic:
        fig.text(0.5, 0.5, "SYNTHETIC - NOT A RUN RESULT", ha="center", va="center",
                 fontsize=20, color="0.6", alpha=0.35, rotation=20)


def margin_timeseries(t, T, case, synthetic, path=None):
    mg = margins(T, case)
    pred = predicted_downshift(mg, case)
    fig, ax = plt.subplots(figsize=(7, 3.2), constrained_layout=True)
    ax.plot(t, mg["d"], label="d: distance above active threshold (K)")
    ax.plot(t, np.where(np.isfinite(mg["M"]), mg["M"], np.nan), label="M: masking margin (K)")
    ax.plot(t, mg["s"], label="s: sparse deficit (K)")
    if case.bias_K:
        ax.axhline(abs(case.bias_K), ls="--", lw=1, color="k", label="|b| (K)")
    if pred.any():
        ax.fill_between(t, 0, 1, where=pred, transform=ax.get_xaxis_transform(),
                        alpha=0.15, color="C3", label="predicted lower command")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("margin (K)")
    ax.set_title(case.name)
    ax.legend(fontsize=7, loc="upper right")
    _mark(fig, synthetic)
    if path:
        fig.savefig(path, dpi=200)
    return fig


def margin_map(T, cases, synthetic, path=None):
    fig, ax = plt.subplots(figsize=(4.2, 4), constrained_layout=True)
    top = 0.0
    for k, c in enumerate(cases):
        mg = margins(T, c)
        D = effective_underreading(mg, c)
        ok = np.isfinite(mg["d"])
        ax.scatter(D[ok], mg["d"][ok], s=4, color=f"C{k}", label=c.name)
        if ok.any():
            top = max(top, float(np.nanmax(D[ok])), float(np.nanmax(mg["d"][ok])))
    top = max(top, 1.0) * 1.05
    ax.fill_between([0, top], [0, top], 0, color="C3", alpha=0.1,
                    label="d < Delta_eff: lower command")
    ax.plot([0, top], [0, top], "k-", lw=0.8)
    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_xlabel("effective under-reading Delta_eff (K)")
    ax.set_ylabel("threshold distance d (K)")
    ax.legend(fontsize=7)
    _mark(fig, synthetic)
    if path:
        fig.savefig(path, dpi=200)
    return fig
