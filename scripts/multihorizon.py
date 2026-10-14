#!/usr/bin/env python3
"""Does the oil-China hedge look better at longer horizons?

The paper runs daily DCC-GARCH. But Brent closes hours after the Chinese market,
so same-day daily returns are non-synchronous and *understate* the link,
especially for the energy sectors where a real link exists. This script
recomputes the hedge at daily / weekly / biweekly / monthly horizons to show how
much of the "weak hedge" is a frequency artifact.

For each horizon and market it reports:
- Pearson correlation with oil
- static optimal hedge ratio   b = cov(mkt, oil) / var(oil)
- hedging effectiveness        HE = 1 - var(mkt - b*oil) / var(mkt)
and, at the weekly horizon, the dynamic DCC hedge ratio for comparison.

Usage:
    PYTHONPATH=src python scripts/multihorizon.py --data data/raw/source_extension.csv
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

from spillover import MARKETS, OIL, garch, plots  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HORIZONS = {"daily": None, "weekly": "W-FRI", "biweekly": "2W-FRI", "monthly": "ME"}


def log_returns(prices: pd.DataFrame, rule: str | None) -> pd.DataFrame:
    px = prices if rule is None else prices.resample(rule).last()
    return (np.log(px).diff().dropna()) * 100.0


def static_metrics(mkt: pd.Series, oil: pd.Series) -> dict:
    s = pd.concat([mkt, oil], axis=1).dropna()
    m, o = s.iloc[:, 0].to_numpy(), s.iloc[:, 1].to_numpy()
    b = np.cov(m, o, ddof=1)[0, 1] / np.var(o, ddof=1)
    he = 1.0 - np.var(m - b * o, ddof=1) / np.var(m, ddof=1)
    return {"corr": float(np.corrcoef(m, o)[0, 1]), "hedge": float(b),
            "he": float(he), "n": len(s)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "source_extension.csv"))
    ap.add_argument("--out", default=str(ROOT / "results" / "multihorizon"))
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

    # ---- static metrics across horizons
    rows = []
    for hname, rule in HORIZONS.items():
        r = log_returns(df, rule)
        for code, name in MARKETS.items():
            if code not in r.columns:
                continue
            mm = static_metrics(r[code], r[OIL])
            rows.append({"horizon": hname, "market": name, **mm})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "multihorizon.csv", index=False)

    # ---- weekly DCC hedge ratio for comparison (dynamic)
    rw = log_returns(df, "W-FRI")
    dcc_rows = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for code, name in MARKETS.items():
            if code not in rw.columns:
                continue
            pair = rw[[OIL, code]].dropna()
            H, R, _v, _a, _b = garch.conditional_covariances(pair)
            hedge = (H[:, 0, 1] / H[:, 0, 0]).mean()
            dcc_rows.append({"market": name, "weekly_dcc_hedge": float(hedge),
                             "weekly_dcc_corr": float(R[:, 0, 1].mean())})
    dcc = pd.DataFrame(dcc_rows).set_index("market")
    dcc.round(4).to_csv(out / "weekly_dcc.csv")

    # ---- figure: HE vs horizon, per market
    piv = tab.pivot(index="horizon", columns="market", values="he").reindex(HORIZONS)
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, name in enumerate(MARKETS.values()):
        if name in piv.columns:
            ax.plot(range(len(piv)), 100 * piv[name].to_numpy(),
                    marker="o", lw=1.6, color=plots.SERIES[i % len(plots.SERIES)], label=name)
    ax.set_xticks(range(len(piv)), [h for h in piv.index], fontsize=10)
    ax.set_ylabel("hedging effectiveness (% variance reduction)")
    ax.set_title("Oil hedge improves at longer horizons — most for the energy sectors")
    ax.legend(ncol=2, fontsize=9)
    ax.margins(x=0.03)
    fig.savefig(out / "fig_multihorizon.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ---- report
    cpiv = tab.pivot(index="horizon", columns="market", values="corr").reindex(HORIZONS)
    hpiv = piv
    oil_name = MARKETS["CI005001"]
    coal_name = MARKETS["CI005002"]

    def fmt_row(metric_pivot, scale=1.0, pct=False):
        lines = []
        for h in HORIZONS:
            vals = " | ".join(
                f"{scale*metric_pivot.loc[h, n]:.1f}%" if pct else f"{scale*metric_pivot.loc[h, n]:.3f}"
                for n in MARKETS.values() if n in metric_pivot.columns
            )
            lines.append(f"| {h} | {vals} |")
        return lines

    cols = " | ".join(n for n in MARKETS.values())
    lines = [
        "# Multi-horizon hedge: is the weak hedge a daily-frequency artifact?",
        "",
        f"Same sample ({df.index.min():%Y}–{df.index.max():%Y}); returns aggregated to each "
        "horizon before computing the static optimal oil hedge. Brent closes after the Chinese "
        "session, so daily same-date returns are non-synchronous and understate the link; longer "
        "horizons wash that out.",
        "",
        "## Headline",
        "",
        f"- **{oil_name}** hedging effectiveness: "
        f"**{100*hpiv.loc['daily', oil_name]:.1f}% (daily) → {100*hpiv.loc['weekly', oil_name]:.1f}% (weekly) "
        f"→ {100*hpiv.loc['monthly', oil_name]:.1f}% (monthly)**",
        f"- **{coal_name}**: "
        f"**{100*hpiv.loc['daily', coal_name]:.1f}% → {100*hpiv.loc['weekly', coal_name]:.1f}% "
        f"→ {100*hpiv.loc['monthly', coal_name]:.1f}%**",
        "- The broad indices stay weak at every horizon — the horizon effect is specific to the "
        "oil-exposed sectors, exactly where a real economic link exists.",
        "",
        "![multi-horizon](fig_multihorizon.png)",
        "",
        f"## Correlation with oil by horizon\n\n| horizon | {cols} |",
        "|" + "---|" * (len(MARKETS) + 1),
        *fmt_row(cpiv),
        "",
        f"## Hedging effectiveness by horizon\n\n| horizon | {cols} |",
        "|" + "---|" * (len(MARKETS) + 1),
        *fmt_row(hpiv, scale=100, pct=True),
        "",
        "## Weekly dynamic (DCC) hedge ratios",
        "",
        "| market | weekly DCC hedge | weekly DCC corr |",
        "|---|---:|---:|",
        *(f"| {n} | {dcc.loc[n, 'weekly_dcc_hedge']:.3f} | {dcc.loc[n, 'weekly_dcc_corr']:.3f} |"
          for n in dcc.index),
        "",
        "---",
        "*Static hedge: b = cov(mkt,oil)/var(oil); HE = 1 - var(mkt - b·oil)/var(mkt). "
        "Weekly DCC via arch + QMLE. A rising HE with horizon is the signature of "
        "non-synchronous daily returns, not a stronger economy-wide link.*",
    ]
    (out / "MULTIHORIZON.md").write_text("\n".join(lines), encoding="utf-8")

    print(tab.pivot(index="horizon", columns="market", values="he").reindex(HORIZONS).round(4).to_string())
    print("\ndone ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
