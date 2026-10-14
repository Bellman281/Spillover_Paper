#!/usr/bin/env python3
"""Zoom in on the oil-China DCC correlation around the biggest crude shocks.

The decade-average correlation can hide a short tail spike. This fits the
Python DCC-GARCH on [oil + broad Chinese indices], tracks the *time-varying*
oil-China correlation, and marks the largest daily crude moves in a focus year
(default 2026, which spans the Strait of Hormuz period) so you can see whether a
real oil-supply scare actually broke the decoupling or the series shrugged it
off.

It is data-driven: it does not assume an event date — it finds the days with the
biggest |oil return| in the focus year and reports what the correlation did
around them, versus the full-sample average.

Usage:
    PYTHONPATH=src python scripts/oil_shock_window.py \
        --data data/raw/source_extension.csv --focus-year 2026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spillover import garch, plots  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

BROAD = ["SG000001", "SZ399001", "HS000300"]  # Shanghai, Shenzhen, CSI 300


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "source_extension.csv"))
    ap.add_argument("--oil-col", default="OilRmb")
    ap.add_argument("--markets", nargs="*", default=BROAD,
                    help="market columns to average for the oil-China line")
    ap.add_argument("--focus-year", type=int, default=2026)
    ap.add_argument("--n-shocks", type=int, default=5, help="top |oil move| days to mark")
    ap.add_argument("--out", default=str(ROOT / "results" / "shock"))
    args = ap.parse_args()

    data = Path(args.data)
    if not data.exists():
        raise SystemExit(f"no data at {data}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plots.set_style()

    df = pd.read_csv(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    cols = [args.oil_col] + [c for c in args.markets if c in df.columns]
    rets = (np.log(df[cols]).diff().dropna()) * 100.0

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        R_t, labels, a, b = garch.fit_dcc(rets)

    # average oil-China correlation path (oil is column 0)
    oil_corr = R_t[:, 0, 1:].mean(axis=1)
    dates = rets.index
    corr = pd.Series(oil_corr, index=dates, name="oil_china_corr")
    full_mean = float(corr.mean())

    # focus-year window + biggest oil moves within it
    oil_ret = rets[args.oil_col]
    fy = oil_ret[oil_ret.index.year == args.focus_year]
    shocks = fy.abs().sort_values(ascending=False).head(args.n_shocks).index.sort_values()
    fy_corr = corr[corr.index.year == args.focus_year]
    fy_mean = float(fy_corr.mean()) if len(fy_corr) else float("nan")
    peak_date = corr[corr.index.year == args.focus_year].idxmax() if len(fy_corr) else None
    peak_val = float(fy_corr.max()) if len(fy_corr) else float("nan")

    # ---- figure: full path (left) + focus-year zoom (right)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13.5, 4.8),
                                   gridspec_kw={"width_ratios": [2, 1]})
    axL.plot(corr.index, corr.values, color=plots.SERIES[0], lw=0.8)
    axL.axhline(full_mean, color=plots.INK, lw=0.9, ls="--", alpha=0.7,
                label=f"full-sample mean {full_mean:.3f}")
    axL.axvspan(pd.Timestamp(f"{args.focus_year}-01-01"), corr.index.max(),
                color=plots.COPPER, alpha=0.10)
    axL.set_title(f"Oil–China conditional correlation, {corr.index.min():%Y}–{corr.index.max():%Y}",
                  loc="left", fontsize=12)
    axL.set_ylabel("avg DCC corr (oil vs broad indices)")
    axL.legend(fontsize=9, loc="upper left")
    axL.margins(x=0.01)

    z = corr[corr.index.year >= args.focus_year - 1]
    axR.plot(z.index, z.values, color=plots.SERIES[0], lw=1.2)
    axR.axhline(full_mean, color=plots.INK, lw=0.9, ls="--", alpha=0.7)
    for d in shocks:
        axR.axvline(d, color=plots.COPPER, lw=1.0, alpha=0.6)
    axR.set_title(f"{args.focus_year} zoom — lines = biggest crude moves", loc="left", fontsize=12)
    axR.margins(x=0.02)
    axR.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    axR.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for lbl in axR.get_xticklabels():
        lbl.set_rotation(30)
        lbl.set_ha("right")
    fig.suptitle("Did the 2026 oil-supply scare break the decoupling?",
                 x=0.07, ha="left", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "fig_oil_shock_window.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ---- report
    shock_rows = [
        f"| {d:%Y-%m-%d} | {oil_ret.loc[d]:+.1f}% | {corr.loc[d]:.3f} |"
        for d in shocks
    ]
    broke = peak_val >= 0.35
    verdict = (
        f"**The correlation spiked to {peak_val:.2f} in {args.focus_year}** "
        f"(around {peak_date:%Y-%m-%d}) — the oil scare did pull Chinese equities "
        "and oil together, at least transiently."
        if broke else
        f"**No break.** Even the {args.focus_year} peak ({peak_val:.2f} on "
        f"{peak_date:%Y-%m-%d}) stays in the weak-link range; the decoupling absorbs "
        "the oil-supply scare rather than reversing."
    )
    lines = [
        f"# Oil shock window — did {args.focus_year} break the oil–China decoupling?",
        "",
        f"Time-varying oil–China DCC correlation (oil vs {', '.join(c for c in cols[1:])}), "
        f"{corr.index.min():%Y-%m-%d} → {corr.index.max():%Y-%m-%d}. DCC(a={a:.3f}, b={b:.3f}).",
        "",
        "## Headline",
        "",
        f"- Full-sample mean correlation: **{full_mean:.3f}**",
        f"- {args.focus_year} mean: **{fy_mean:.3f}**  |  {args.focus_year} peak: "
        f"**{peak_val:.3f}** ({peak_date:%Y-%m-%d})",
        "",
        verdict,
        "",
        "![oil shock window](fig_oil_shock_window.png)",
        "",
        f"## Biggest crude moves in {args.focus_year} and the correlation that day",
        "",
        "| Date | oil daily move | oil–China corr |",
        "|---|---:|---:|",
        *shock_rows,
        "",
        "---",
        "*Data-driven: no event date is assumed; the marked days are simply the "
        f"largest |oil return| days of {args.focus_year}. Method: Python DCC-GARCH "
        "(arch + QMLE), consistent with the rest of the extension.*",
    ]
    (out / "SHOCK.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"full-sample mean corr : {full_mean:.3f}")
    print(f"{args.focus_year} mean / peak      : {fy_mean:.3f} / {peak_val:.3f} ({peak_date:%Y-%m-%d})")
    print(f"biggest {args.focus_year} crude moves:")
    for d in shocks:
        print(f"  {d:%Y-%m-%d}  oil {oil_ret.loc[d]:+6.1f}%   corr {corr.loc[d]:.3f}")
    print("done ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
