"""Run the whole analysis: `python -m spillover [--data ...] [--out ...]`.

Reproduces tables and figures from the committed data and RATS H-matrices,
then re-estimates a DCC-GARCH in Python and animates it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import MARKETS, OIL
from . import data as datamod
from . import descriptive, garch, hmatrix, plots

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(prog="spillover", description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "source.csv"))
    ap.add_argument("--hmatrices", default=str(ROOT / "rats" / "hmatrices"))
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--no-dcc", action="store_true", help="skip the Python DCC re-estimation + GIF")
    args = ap.parse_args()

    out = Path(args.out)
    figs, tables = out / "figures", out / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    plots.set_style()

    print("[1/6] loading prices and computing log returns")
    prices = datamod.load_prices(args.data)
    returns = datamod.log_returns(prices)
    print(f"      {prices.shape[0]} obs, {prices.index.min():%Y-%m-%d} -> {prices.index.max():%Y-%m-%d}")

    print("[2/6] descriptive statistics (Table 1)")
    desc = descriptive.describe(returns)
    desc.round(4).to_csv(tables / "table1_descriptive.csv")

    print("[3/6] reading RATS H-matrices, deriving hedging quantities")
    derived = hmatrix.all_markets(args.hmatrices, index=returns.index)
    he = hmatrix.hedging_effectiveness(returns, derived)
    he.round(4).to_csv(tables / "table2_hedging.csv")
    print(he.round(3).to_string())

    print("[4/6] static figures")
    plots.fig_prices(prices, figs)
    plots.fig_returns(returns, figs)
    plots.fig_cond_vol(derived, figs)
    plots.fig_dcc(derived, figs)
    plots.fig_hedge(derived, figs)
    plots.fig_effectiveness(he, figs)

    if args.no_dcc:
        print("[5/6] DCC re-estimation skipped")
        print("[6/6] done")
        return 0

    print("[5/6] Python DCC-GARCH re-estimation (no RATS)")
    cols = [OIL, *MARKETS.keys()]
    R_t, _, a, b = garch.fit_dcc(returns[cols])
    print(f"      DCC(a={a:.3f}, b={b:.3f}), persistence a+b={a + b:.3f}")

    print("[6/6] correlation-matrix figure")
    short = {
        "SZ399001": "Shenzhen", "SG000001": "Shanghai", "HS000300": "CSI",
        "CI005001": "OilSec", "CI005002": "Coal", "CI005003": "Non-ferr", "CI005005": "Iron",
    }
    labels = ["OPEC", *[short[c] for c in MARKETS]]
    plots.fig_corr_matrix(R_t, labels, returns.index, figs)
    print("done ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
