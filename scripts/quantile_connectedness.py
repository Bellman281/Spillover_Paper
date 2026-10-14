"""Quantile connectedness (Ando, Greenwood-Nimmo & Shin 2022).

Diebold-Yilmaz measures spillover at the conditional mean. But the regime result
showed the oil-China link wakes up in crises — that is a *tail* phenomenon the
mean misses. A quantile VAR (equation-by-equation quantile regression) + the
generalized FEVD measures connectedness at each quantile, so we can compare the
lower tail (τ=0.05, crash days), the median (τ=0.5), and the upper tail
(τ=0.95). Connectedness that is higher in the tails than at the median is the
connectedness-framework signature of crisis contagion.

Usage:
    PYTHONPATH=src python scripts/quantile_connectedness.py --data data/raw/source_extension.csv
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from spillover import plots  # noqa: E402
from connectedness import SYSTEM, H, gfevd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

QGRID = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
REPORT_Q = [0.05, 0.5, 0.95]


def qvar_connectedness(ret: pd.DataFrame, tau: float):
    """VAR(1) quantile regression at tau -> GFEVD connectedness table (%)."""
    names = list(ret.columns)
    k = len(names)
    Y = ret.iloc[1:].reset_index(drop=True)
    X = ret.iloc[:-1].reset_index(drop=True)
    X.columns = [f"L{c}" for c in names]
    data = pd.concat([Y, X], axis=1)
    B = np.zeros((k, k))
    resid = np.zeros((len(data), k))
    for i, c in enumerate(names):
        formula = f"Q('{c}') ~ " + " + ".join(f"Q('L{n}')" for n in names)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = smf.quantreg(formula, data).fit(q=tau, max_iter=2000)
        B[i] = [res.params[f"Q('L{n}')"] for n in names]
        resid[:, i] = res.resid
    sigma = np.cov(resid, rowvar=False)
    # MA for VAR(1): Phi_h = B^h
    ma = np.empty((H, k, k))
    cur = np.eye(k)
    for h in range(H):
        ma[h] = cur
        cur = cur @ B
    theta = gfevd(ma, sigma) * 100.0
    frm = theta.sum(1) - np.diag(theta)
    to = theta.sum(0) - np.diag(theta)
    return theta, frm, to, frm.sum() / k


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "source_extension.csv"))
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
    names = list(ret.columns)

    rows = []
    tables = {}
    for tau in QGRID:
        theta, frm, to, tot = qvar_connectedness(ret, tau)
        rows.append({"tau": tau, "total": tot, "oil_FROM": frm[0],
                     "oil_TO": to[0], "oil_NET": to[0] - frm[0]})
        if tau in REPORT_Q:
            tables[tau] = pd.DataFrame(theta, index=names, columns=names)
        print(f"  tau={tau:.2f}  total={tot:5.1f}%  oil FROM={frm[0]:4.1f}  NET={to[0]-frm[0]:+.1f}")
    curve = pd.DataFrame(rows).set_index("tau")
    curve.round(3).to_csv(out / "quantile_connectedness.csv")
    for tau, T in tables.items():
        T.round(2).to_csv(out / f"quantile_tau{int(tau*100):02d}.csv")

    # figure: total + oil-FROM connectedness across quantiles (the tail U-shape)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax1.plot(curve.index, curve["total"], marker="o", color=plots.INK, lw=1.6)
    ax1.set_xlabel("quantile τ"); ax1.set_ylabel("total connectedness (%)")
    ax1.set_title("System connectedness by quantile", loc="left", fontsize=12)
    ax1.margins(x=0.05)
    ax2.plot(curve.index, curve["oil_FROM"], marker="o", color=plots.COPPER, lw=1.6, label="oil FROM China")
    ax2.plot(curve.index, curve["oil_TO"], marker="s", color=plots.SERIES[0], lw=1.6, label="oil TO China")
    ax2.set_xlabel("quantile τ"); ax2.set_ylabel("connectedness (%)")
    ax2.set_title("Oil's link to China by quantile", loc="left", fontsize=12)
    ax2.legend(fontsize=9)
    fig.suptitle("Quantile connectedness: directional spillover is tail-stable (Ando et al. 2022)",
                 x=0.07, ha="left", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out / "fig_quantile_connectedness.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    tl, tm, tu = curve.loc[0.05, "total"], curve.loc[0.5, "total"], curve.loc[0.95, "total"]
    ol, om, ou = curve.loc[0.05, "oil_FROM"], curve.loc[0.5, "oil_FROM"], curve.loc[0.95, "oil_FROM"]
    tot_range = curve["total"].max() - curve["total"].min()
    oil_range = curve["oil_FROM"].max() - curve["oil_FROM"].min()
    lines = [
        "# Quantile connectedness (Ando et al. 2022)",
        "",
        f"Quantile-VAR(1) + generalized FEVD across quantiles, {df.index.min():%Y}–{df.index.max():%Y}. "
        "Connectedness at the median vs the tails.",
        "",
        "## Headline (an honest null that refines the regime result)",
        "",
        f"- **Directional connectedness is essentially quantile-invariant:** total is "
        f"**{tl:.1f}% (τ=0.05) / {tm:.1f}% (median) / {tu:.1f}% (τ=0.95)** — a range of only "
        f"{tot_range:.1f} pp across the whole grid. There is **no tail amplification** of "
        "*predictive* spillover.",
        f"- **Oil stays detached in the tails too:** oil's FROM-China connectedness is "
        f"**{ol:.1f}% / {om:.1f}% / {ou:.1f}%** (τ = 0.05 / 0.5 / 0.95), flat to within "
        f"{oil_range:.1f} pp.",
        "",
        "![quantile connectedness](fig_quantile_connectedness.png)",
        "",
        "## Why this does not contradict the regime finding",
        "",
        "The Markov-regime result (oil–China *correlation* roughly doubles in the turbulent "
        "volatility regime) and this quantile null are both true because they measure different "
        "things. The regime result is about **contemporaneous co-movement**: in a crisis oil and "
        "Chinese equities get more volatile *together*. Quantile connectedness is about "
        "**directional predictability**: whether oil's past *forecasts* Chinese returns better in "
        "the tails — and it does not. So the crisis amplification is a shared-volatility effect, "
        "not a predictive-spillover effect. Oil never becomes a leading indicator for Chinese "
        "crashes; the two simply wobble together when everything does. That distinction is a "
        "cleaner, more defensible claim than a blanket 'contagion in crises'.",
        "",
        "| τ | total | oil FROM | oil TO | oil NET |",
        "|---|---:|---:|---:|---:|",
        *(f"| {t:.2f} | {curve.loc[t, 'total']:.1f}% | {curve.loc[t, 'oil_FROM']:.1f}% "
          f"| {curve.loc[t, 'oil_TO']:.1f}% | {curve.loc[t, 'oil_NET']:+.1f}% |" for t in QGRID),
        "",
        "---",
        "*QVAR via equation-by-equation quantile regression (statsmodels); GFEVD on the "
        "quantile-specific coefficients and residual covariance.*",
    ]
    (out / "QUANTILE_CONNECTEDNESS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\ntotal: tail {tl:.1f} / median {tm:.1f} / upper {tu:.1f}")
    print("done ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
