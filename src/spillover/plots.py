"""Static figures. One warm accent, muted series palette, quiet axes."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import MARKETS, OIL, OIL_NAME

INK = "#1D2328"
MUTED = "#6B747A"
LINE = "#D6D9DB"
COPPER = "#AF4E26"
PAPER = "#FBFBFA"
# muted qualitative palette for the seven markets
SERIES = ["#2E5A87", "#4C8C7A", "#B07A2E", "#9A4E6E", "#5B6AA0", "#7E9B3C", "#C06A3A"]


def set_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.edgecolor": LINE,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.grid": True,
            "grid.color": LINE,
            "grid.linewidth": 0.6,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_prices(prices: pd.DataFrame, out: Path) -> Path:
    norm = 100 * prices / prices.iloc[0]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(norm.index, norm[OIL], color=COPPER, lw=2.0, label=OIL_NAME, zorder=5)
    for color, (code, name) in zip(SERIES, MARKETS.items()):
        ax.plot(norm.index, norm[code], color=color, lw=1.0, alpha=0.85, label=name)
    ax.set_title("Normalized price levels, 2004–2014  (31 Dec 2004 = 100)")
    ax.set_ylabel("index (base 100)")
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.margins(x=0.01)
    return _save(fig, out, "fig1_prices.png")


def fig_returns(returns: pd.DataFrame, out: Path) -> Path:
    series = [(OIL, OIL_NAME)] + list(MARKETS.items())
    fig, axes = plt.subplots(4, 2, figsize=(10, 9), sharex=True)
    for ax, (code, name) in zip(axes.ravel(), series):
        color = COPPER if code == OIL else SERIES[0]
        ax.plot(returns.index, returns[code], color=color, lw=0.5)
        ax.set_title(name, fontsize=10, loc="left")
        ax.grid(True, axis="y")
        ax.margins(x=0.01)
    fig.suptitle("Daily log returns (%) — volatility clustering", x=0.12, ha="left", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return _save(fig, out, "fig2_returns.png")


def fig_cond_vol(derived: dict[str, pd.DataFrame], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.6))
    any_d = next(iter(derived.values()))
    ax.plot(any_d.index, any_d["vol_oil"], color=COPPER, lw=2.0, label=OIL_NAME, zorder=5)
    for color, (code, name) in zip(SERIES, MARKETS.items()):
        ax.plot(derived[code].index, derived[code]["vol_mkt"], color=color, lw=1.0, alpha=0.85, label=name)
    ax.set_title("Conditional volatility (annualized %), VARMA-GARCH")
    ax.set_ylabel("annualized volatility (%)")
    ax.legend(ncol=2, fontsize=9)
    ax.margins(x=0.01)
    return _save(fig, out, "fig3_conditional_volatility.png")


def fig_dcc(R_t, dates, out: Path) -> Path:
    """Time-varying oil–market conditional correlations from the DCC-GARCH.

    (The paper's McAleer VAR-CCC model holds correlation constant by
    construction; the dynamic view comes from the Python DCC re-estimation.)
    Oil is column 0 of R_t; markets are columns 1..7 in ``MARKETS`` order.
    """
    names = list(MARKETS.values())
    fig, axes = plt.subplots(4, 2, figsize=(10, 9), sharex=True)
    for k, (ax, (color, name)) in enumerate(zip(axes.ravel(), zip(SERIES, names))):
        series = R_t[:, 0, k + 1]
        ax.plot(dates, series, color=color, lw=0.8)
        ax.axhline(series.mean(), color=INK, lw=0.8, ls="--", alpha=0.6)
        ax.set_title(f"oil – {name}", fontsize=10, loc="left")
        ax.set_ylim(-0.3, 0.6)
        ax.margins(x=0.01)
    axes.ravel()[-1].axis("off")
    fig.suptitle(
        "Dynamic conditional correlation with OPEC oil (DCC-GARCH)",
        x=0.12, ha="left", fontsize=13, weight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return _save(fig, out, "fig4_dynamic_correlation.png")


def fig_hedge(derived: dict[str, pd.DataFrame], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for color, (code, name) in zip(SERIES, MARKETS.items()):
        ax.plot(derived[code].index, derived[code]["hedge_ratio"], color=color, lw=1.0, label=name)
    ax.set_title("Optimal time-varying hedge ratio  β = H$_{oil,mkt}$ / H$_{oil}$")
    ax.set_ylabel("oil hedge ratio")
    ax.legend(ncol=2, fontsize=9)
    ax.margins(x=0.01)
    return _save(fig, out, "fig5_hedge_ratios.png")


def fig_corr_matrix(R_t, labels, dates, out: Path) -> Path:
    """Static conditional-correlation matrix at three representative dates.

    Shows that the oil row/column stays low while the Chinese series stay high,
    through the 2007 run-up, the 2008 crisis, and the later calm.
    """
    import numpy as np

    picks = [("2007-10-15", "Oct 2007 — pre-crisis peak"),
             ("2008-10-15", "Oct 2008 — global crisis"),
             ("2013-06-14", "Jun 2013 — later sample")]
    n = len(labels)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8))
    im = None
    for ax, (date, caption) in zip(axes, picks):
        idx = int(np.argmin(np.abs(dates - pd.Timestamp(date))))
        R = R_t[idx]
        im = ax.imshow(R, vmin=-1, vmax=1, cmap="RdYlBu_r")
        ax.set_xticks(range(n), labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(n), labels, fontsize=8)
        ax.set_title(caption, fontsize=10, loc="left")
        for i in range(n):
            for j in range(n):
                v = R[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(v) > 0.55 else INK)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02).set_label("conditional correlation", fontsize=9)
    fig.suptitle("Conditional correlation structure (Python DCC-GARCH re-estimation)",
                 x=0.09, ha="left", fontsize=13, weight="bold")
    p = out / "fig7_correlation_matrix.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_effectiveness(he_table: pd.DataFrame, out: Path) -> Path:
    t = he_table.sort_values("hedging_effectiveness")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(t.index, 100 * t["hedging_effectiveness"], color=COPPER, alpha=0.9, height=0.62)
    for y, v in enumerate(100 * t["hedging_effectiveness"]):
        ax.text(v + 0.3, y, f"{v:.1f}%", va="center", fontsize=9, color=INK)
    ax.set_title("Hedging effectiveness — variance reduction from the oil hedge")
    ax.set_xlabel("portfolio variance reduction (%)")
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    return _save(fig, out, "fig6_hedging_effectiveness.png")
