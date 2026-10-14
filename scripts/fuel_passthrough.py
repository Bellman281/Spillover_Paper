#!/usr/bin/env python3
"""How much of a crude move reaches China's administered pump price?

Regresses the change in NDRC retail fuel on the change in crude, event by event,
to estimate the **pass-through elasticity**. A value well below 1 is the
mechanism behind the weak oil-equity link: the state absorbs crude swings at the
pump (floor/ceiling on crude, skip-small-moves rule, ~40% fixed tax wedge), so
oil shocks don't flow through to domestic demand, margins, or A-share returns.

Usage:
    PYTHONPATH=src python scripts/fuel_passthrough.py --data data/raw/china_fuel.csv

Writes to ``results/fuel/``: passthrough.csv, fig_fuel_passthrough.png, FUEL.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spillover import plots  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def ols(y: np.ndarray, x: np.ndarray) -> dict:
    """Simple OLS y = a + b x with HC0-ish se; returns beta, alpha, r2, se, n."""
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n = len(y)
    r2 = 1.0 - resid.var() / y.var() if y.var() > 0 else float("nan")
    # White heteroskedasticity-robust se for the slope
    XtX_inv = np.linalg.inv(X.T @ X)
    meat = X.T @ (X * (resid**2)[:, None])
    cov = XtX_inv @ meat @ XtX_inv
    se_b = float(np.sqrt(cov[1, 1]))
    return {"alpha": float(beta[0]), "beta": float(beta[1]),
            "r2": float(r2), "se_beta": se_b, "n": n}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "china_fuel.csv"))
    ap.add_argument("--crude", default="brent_usd", choices=["brent_usd", "wti_usd"])
    ap.add_argument("--out", default=str(ROOT / "results" / "fuel"))
    args = ap.parse_args()

    data = Path(args.data)
    if not data.exists():
        raise SystemExit(f"no data at {data} — run scripts/fetch_fuel.py first.")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plots.set_style()

    df = pd.read_csv(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    fuels = [c for c in ("gasoline", "diesel") if c in df.columns]
    crude = args.crude
    rows = []
    for fuel in fuels:
        pair = df[[fuel, crude]].dropna()
        dln_fuel = np.log(pair[fuel]).diff().dropna()
        dln_crude = np.log(pair[crude]).diff().reindex(dln_fuel.index)
        m = np.isfinite(dln_fuel) & np.isfinite(dln_crude)
        res = ols(dln_fuel[m].to_numpy(), dln_crude[m].to_numpy())
        res["fuel"] = fuel
        rows.append(res)
        print(f"{fuel:9s} pass-through beta = {res['beta']:.3f} "
              f"(se {res['se_beta']:.3f}), R2 = {res['r2']:.3f}, n = {res['n']}")

    table = pd.DataFrame(rows).set_index("fuel")[["beta", "se_beta", "r2", "n"]]
    table.round(4).to_csv(out / "passthrough.csv")

    # ---- figure: rebased levels (left) + elasticity scatter for gasoline (right)
    head = fuels[0]
    pair = df[[head, crude]].dropna()
    reb = 100 * pair / pair.iloc[0]
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.8))

    axL.plot(reb.index, reb[crude], color=plots.COPPER, lw=1.8,
             label=f"{crude.split('_')[0].upper()} crude")
    axL.plot(reb.index, reb[head], color=plots.SERIES[0], lw=1.8,
             label=f"NDRC {head}")
    axL.set_title("Crude swings vs the administered pump price (rebased = 100)", loc="left", fontsize=12)
    axL.set_ylabel("level (base 100)")
    axL.legend(fontsize=9)
    axL.margins(x=0.01)

    dln_f = np.log(pair[head]).diff()
    dln_c = np.log(pair[crude]).diff()
    m = np.isfinite(dln_f) & np.isfinite(dln_c)
    b = table.loc[head, "beta"]
    xs = np.linspace(dln_c[m].min(), dln_c[m].max(), 50)
    axR.scatter(100 * dln_c[m], 100 * dln_f[m], s=14, color=plots.MUTED, alpha=0.6)
    axR.plot(100 * xs, 100 * b * xs, color=plots.COPPER, lw=2,
             label=f"pass-through β = {b:.2f}")
    axR.plot(100 * xs, 100 * xs, color=plots.INK, lw=1, ls="--", alpha=0.6,
             label="1:1 (full pass-through)")
    axR.set_title("Per-adjustment elasticity", loc="left", fontsize=12)
    axR.set_xlabel("Δ crude (%)")
    axR.set_ylabel(f"Δ {head} (%)")
    axR.legend(fontsize=9)
    fig.suptitle("China's administered fuel prices damp the crude signal",
                 x=0.07, ha="left", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "fig_fuel_passthrough.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ---- report
    gb = table.loc[head, "beta"]
    lines = [
        "# Administered fuel prices: how much crude reaches the pump?",
        "",
        f"Elasticity of China's NDRC retail fuel to **{crude.split('_')[0].upper()}** crude, "
        "regressed change-on-change over every price adjustment "
        f"({pair.index.min():%Y}–{pair.index.max():%Y}).",
        "",
        "## Headline",
        "",
        f"- **{head.title()} pass-through β = {gb:.2f}** — a 10% crude move passes "
        f"through as about a {10 * gb:.0f}% move at the pump.",
        "",
        "| Fuel | pass-through β | robust se | R² | n |",
        "|---|---:|---:|---:|---:|",
        *(
            f"| {f} | {r['beta']:.2f} | {r['se_beta']:.2f} | {r['r2']:.2f} | {int(r['n'])} |"
            for f, r in table.iterrows()
        ),
        "",
        "![fuel pass-through](fig_fuel_passthrough.png)",
        "",
        "## Why this explains the decoupling",
        "",
        "The pump price tracks crude only partially and with a lag. The NDRC freezes "
        "adjustments when crude is below **$40** or above **$130**, skips moves under a "
        "small threshold, and sits on top of a roughly 40% fixed tax wedge. So a crude "
        "shock is absorbed by the state and the refiners' regulated margin before it "
        "reaches households or industrial fuel buyers. With the domestic cost of oil "
        "deliberately smoothed, oil-price swings carry little information for Chinese "
        "demand, corporate margins, or equity returns — which is exactly why the "
        "oil–A-share conditional correlation stays near zero across the sector scan.",
        "",
        "---",
        "*Method: OLS of Δln(fuel) on Δln(crude) at each NDRC adjustment, White-robust "
        "standard errors. Crude = Yahoo BZ=F/CL=F; fuel = AKShare `energy_oil_hist`.*",
    ]
    (out / "FUEL.md").write_text("\n".join(lines), encoding="utf-8")
    print("\ndone ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
