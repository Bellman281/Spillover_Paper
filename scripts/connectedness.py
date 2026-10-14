#!/usr/bin/env python3
"""Diebold-Yilmaz connectedness: directional, time-varying oil-China spillovers.

The bivariate DCC gives one correlation at a time. The Diebold-Yilmaz (2012)
framework is the modern standard for *spillover* studies: a VAR + generalized
forecast-error-variance decomposition yields a full directional connectedness
table (who transmits to whom), a single total-connectedness index, and — rolled
over a moving window — its time variation. This is the natural upgrade for a
paper whose title is about spillover.

- Static table: pairwise, directional TO / FROM others, NET, and total index.
- Returns connectedness (primary) and volatility connectedness (|returns|).
- Rolling total-connectedness index and net-oil connectedness over time.

Generalized FEVD (Koop-Pesaran-Potter / Pesaran-Shin), order-invariant.

Usage:
    PYTHONPATH=src python scripts/connectedness.py --data data/raw/source_extension.csv
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

from spillover import plots  # noqa: E402
from statsmodels.tsa.api import VAR  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# focused system: oil + two broad indices + the two energy sectors
SYSTEM = {"OilRmb": "Oil", "SG000001": "Shanghai", "HS000300": "CSI300",
          "CI005001": "OilSector", "CI005002": "Coal"}
H = 10  # forecast horizon for the FEVD


def gfevd(ma, sigma: np.ndarray) -> np.ndarray:
    """Generalized FEVD connectedness matrix (rows normalised to sum to 1).

    ma: (H, k, k) Wold MA matrices with ma[0] = I. sigma: residual covariance.
    theta[i, j] = share of i's H-step forecast-error variance due to shocks in j.
    """
    k = sigma.shape[0]
    sig_jj = np.diag(sigma)
    num = np.zeros((k, k))
    den = np.zeros(k)
    for A in ma:
        AS = A @ sigma
        num += AS**2            # (e_i' A sigma e_j)^2, elementwise
        den += np.einsum("ij,jk,ik->i", A, sigma, A)  # diag(A sigma A')
    theta = (num / sig_jj[np.newaxis, :]) / den[:, np.newaxis]
    return theta / theta.sum(axis=1, keepdims=True)


def connectedness(df_ret: pd.DataFrame, maxlags: int = 4) -> tuple[pd.DataFrame, float]:
    """Full DY connectedness table (%) + total connectedness index."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        var = VAR(df_ret.to_numpy())
        order = var.select_order(maxlags=maxlags).aic or 1
        res = var.fit(max(order, 1))
    ma = res.ma_rep(maxn=H - 1)          # (H, k, k), ma[0] = I
    theta = gfevd(ma, res.sigma_u) * 100.0
    names = list(df_ret.columns)
    C = pd.DataFrame(theta, index=names, columns=names)
    k = len(names)
    frm = C.values.sum(1) - np.diag(C.values)       # FROM others (row off-diag)
    to = C.values.sum(0) - np.diag(C.values)        # TO others (col off-diag)
    C["FROM"] = frm
    C.loc["TO"] = list(to) + [np.nan]
    C.loc["NET"] = list(to - frm) + [np.nan]
    total = frm.sum() / k
    return C.round(2), float(total)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "source_extension.csv"))
    ap.add_argument("--window", type=int, default=250)
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--out", default=str(ROOT / "results" / "connectedness"))
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
    cols = [c for c in SYSTEM if c in df.columns]
    ret = (np.log(df[cols]).diff().dropna() * 100.0).rename(columns=SYSTEM)

    # static: returns + volatility (|returns|) connectedness
    Cr, total_r = connectedness(ret)
    Cv, total_v = connectedness(ret.abs())
    Cr.to_csv(out / "connectedness_returns.csv")
    Cv.to_csv(out / "connectedness_vol.csv")

    # rolling total index + net-oil connectedness (returns, VAR(1) for stability)
    dates, totals, net_oil = [], [], []
    arr = ret
    for end in range(args.window, len(arr) + 1, args.step):
        win = arr.iloc[end - args.window:end]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = VAR(win.to_numpy()).fit(1)
            theta = gfevd(res.ma_rep(maxn=H - 1), res.sigma_u) * 100.0
            k = theta.shape[0]
            frm = theta.sum(1) - np.diag(theta)
            to = theta.sum(0) - np.diag(theta)
            dates.append(win.index[-1])
            totals.append(frm.sum() / k)
            net_oil.append(to[0] - frm[0])      # oil is column 0
        except Exception:  # noqa: BLE001
            continue
    roll = pd.DataFrame({"total": totals, "net_oil": net_oil}, index=pd.DatetimeIndex(dates))
    roll.round(3).to_csv(out / "rolling.csv")

    # figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax1.plot(roll.index, roll["total"], color=plots.INK, lw=1.2)
    ax1.axhline(total_r, color=plots.COPPER, lw=1.0, ls="--", alpha=0.8,
                label=f"full-sample {total_r:.0f}%")
    ax1.set_ylabel("total connectedness (%)")
    ax1.set_title(f"Total return connectedness of the oil-China system ({args.window}-day window)",
                  loc="left", fontsize=12)
    ax1.legend(fontsize=9, loc="upper left")
    ax1.margins(x=0.01)
    ax2.axhline(0, color=plots.LINE, lw=1.0)
    ax2.fill_between(roll.index, 0, roll["net_oil"],
                     where=(roll["net_oil"] >= 0), color=plots.COPPER, alpha=0.5,
                     label="oil net transmitter")
    ax2.fill_between(roll.index, 0, roll["net_oil"],
                     where=(roll["net_oil"] < 0), color=plots.SERIES[0], alpha=0.5,
                     label="oil net receiver")
    ax2.set_ylabel("net oil connectedness (pp)")
    ax2.set_title("Is oil a net transmitter or receiver vs China?", loc="left", fontsize=12)
    ax2.legend(fontsize=9, loc="upper left")
    ax2.margins(x=0.01)
    fig.tight_layout()
    fig.savefig(out / "fig_connectedness.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # report
    oil_from = Cr.loc["Oil", "FROM"]
    oil_to = Cr.loc["TO", "Oil"]
    oil_net = Cr.loc["NET", "Oil"]
    lines = [
        "# Connectedness (Diebold-Yilmaz): directional oil-China spillovers",
        "",
        f"VAR + generalized FEVD, {H}-step horizon, {df.index.min():%Y}–{df.index.max():%Y}. "
        "System: oil + Shanghai + CSI 300 + the oil and coal sectors. Each cell is the % of "
        "row *i*'s forecast-error variance explained by shocks to column *j*.",
        "",
        "## Headline",
        "",
        f"- **Total return connectedness: {total_r:.1f}%** (volatility connectedness: {total_v:.1f}%). "
        "Most of the system's variance is internal to the Chinese market, not shared with oil.",
        f"- **Oil is a near-isolated node:** it receives only **{oil_from:.1f}%** of its variance "
        f"from the Chinese series and transmits **{oil_to:.1f}%** to them (net **{oil_net:+.1f} pp**). "
        "Compare that to the 60–90% totals typical of integrated asset systems.",
        "",
        "![connectedness](fig_connectedness.png)",
        "",
        "## Static connectedness table — returns (%)",
        "",
        Cr.to_markdown(),
        "",
        "`FROM` = received from others; `TO` = transmitted to others; `NET` = TO − FROM. "
        "A positive NET marks a net transmitter.",
        "",
        "---",
        "*Generalized FEVD (order-invariant). Total connectedness = mean FROM = share of total "
        "forecast-error variance that crosses series. Rolling panel: 250-day window, VAR(1).*",
    ]
    (out / "CONNECTEDNESS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"total return connectedness: {total_r:.1f}%  | volatility: {total_v:.1f}%")
    print(f"oil FROM={oil_from:.1f}  TO={oil_to:.1f}  NET={oil_net:+.1f}")
    print(Cr.to_string())
    print("\ndone ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
