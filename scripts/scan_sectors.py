#!/usr/bin/env python3
"""Scan the oil-China link across a wide sector universe (bivariate DCC-GARCH).

For every market series in the input CSV we fit a bivariate DCC-GARCH against
oil and summarise the average conditional correlation, optimal hedge ratio and
hedging effectiveness. This widens the paper's seven-series universe so the
decoupling result can be checked sector by sector.

Usage:
    # full universe (after scripts/fetch_scan.py)
    PYTHONPATH=src python scripts/scan_sectors.py --data data/raw/scan_universe.csv

    # or just the paper's seven series (no extra fetch needed)
    PYTHONPATH=src python scripts/scan_sectors.py --data data/raw/source_extension.csv

Writes to ``results/scan/``:
    scan.csv        ranked table
    fig_sector_scan.png
    SCAN.md         headline + ranked table + short read
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spillover import plots, scan  # noqa: E402


def load_returns(csv: Path) -> pd.DataFrame:
    df = pd.read_csv(csv)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    # log returns in %, drop all-NaN columns, keep ragged NaNs for pairwise use
    rets = np.log(df).diff() * 100.0
    return rets.dropna(how="all").dropna(axis=1, how="all")


def write_report(path: Path, table: pd.DataFrame, oil_label: str,
                 start: pd.Timestamp, end: pd.Timestamp) -> None:
    mean_abs = table["avg_corr"].abs().mean()
    top = table.index[0]
    top_c = table.iloc[0]["avg_corr"]
    bot = table.index[-1]
    bot_c = table.iloc[-1]["avg_corr"]
    n_markets = len(table)
    strong = int((table["avg_corr"].abs() >= 0.30).sum())

    verdict = (
        "**The decoupling result generalises.** Across the whole sector map, the "
        "average absolute conditional correlation with oil is "
        f"**{mean_abs:.3f}** — oil is a weak co-mover with *every* corner of the "
        "Chinese market, not just the paper's seven series. "
        if strong == 0 else
        f"**{strong} of {n_markets} sectors** show a materially stronger oil link "
        "(|corr| ≥ 0.30); the rest remain weakly coupled."
    )
    lines = [
        f"# Sector scan — oil ({oil_label}) vs the Chinese market, {start:%Y}–{end:%Y}",
        "",
        f"Bivariate DCC-GARCH of oil against **{n_markets}** market/sector series "
        f"(the ones with ≥ 250 overlapping daily observations).",
        "",
        "## Headline",
        "",
        f"- Mean |conditional correlation| with oil: **{mean_abs:.3f}**",
        f"- Most oil-linked: **{top}** ({top_c:+.3f})",
        f"- Least oil-linked: **{bot}** ({bot_c:+.3f})",
        "",
        verdict,
        "",
        "![sector scan](fig_sector_scan.png)",
        "",
        "## Ranked table (by |correlation|)",
        "",
        "| Market / sector | obs | avg corr | avg hedge ratio | hedging eff. |",
        "|---|---:|---:|---:|---:|",
        *(
            f"| {name} | {int(r['n_obs'])} | {r['avg_corr']:+.3f} "
            f"| {r['avg_hedge_ratio']:+.3f} | {100 * r['hedging_effectiveness']:.1f}% |"
            for name, r in table.iterrows()
        ),
        "",
        "---",
        "*Method: per-market two-step DCC-GARCH (arch + QMLE) on daily log returns, "
        "oil aligned pairwise to each series. Short-history sectors (many Shenwan L1 "
        "codes backfill only to the Dec-2021 reclassification) are excluded by the "
        "250-obs floor. Consistent-method scan, not a RATS replication — see the main README.*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "scan_universe.csv"))
    ap.add_argument("--oil-col", default="OilRmb")
    ap.add_argument("--oil-label", default="Brent×CNY")
    ap.add_argument("--out", default=str(ROOT / "results" / "scan"))
    args = ap.parse_args()

    data = Path(args.data)
    if not data.exists():
        raise SystemExit(f"no data at {data} — run scripts/fetch_scan.py first.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plots.set_style()

    rets = load_returns(data)
    if args.oil_col not in rets.columns:
        raise SystemExit(f"oil column {args.oil_col!r} not in {list(rets.columns)}")

    span = rets[args.oil_col].dropna()
    print(f"scanning {len(rets.columns) - 1} markets vs {args.oil_col} "
          f"({span.index.min():%Y-%m-%d}..{span.index.max():%Y-%m-%d})")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        table = scan.scan(rets, oil_col=args.oil_col)

    table.round(4).to_csv(out / "scan.csv")
    period = f"{span.index.min():%Y}–{span.index.max():%Y}"
    plots.fig_scan(table, out, oil_label=args.oil_label, period=period)
    write_report(out / "SCAN.md", table, args.oil_label,
                 span.index.min(), span.index.max())
    print(table.round(3).to_string())
    print("\ndone ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
