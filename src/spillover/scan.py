"""Scan many Chinese indices/sectors against oil (bivariate DCC-GARCH).

For each market we fit a bivariate DCC-GARCH (oil, market) and summarise the
average conditional correlation, optimal hedge ratio and hedging effectiveness
over the sample. This widens the paper's seven-series universe so the oil-China
link can be scanned across the whole sector map.
"""

from __future__ import annotations

import pandas as pd

from . import garch


def scan(returns: pd.DataFrame, oil_col: str = "OilRmb") -> pd.DataFrame:
    """Per-market bivariate DCC metrics vs oil, ranked by |correlation|."""
    rows = []
    for col in returns.columns:
        if col == oil_col:
            continue
        pair = returns[[oil_col, col]].dropna()
        if len(pair) < 250:
            continue
        H, R, _vol, _a, _b = garch.conditional_covariances(pair)
        rho = R[:, 0, 1]
        hedge = H[:, 0, 1] / H[:, 0, 0]
        r_mkt = pair[col].to_numpy()
        r_oil = pair[oil_col].to_numpy()
        he = 1.0 - (r_mkt - hedge * r_oil).var(ddof=1) / r_mkt.var(ddof=1)
        rows.append(
            {
                "market": col,
                "n_obs": len(pair),
                "avg_corr": float(rho.mean()),
                "avg_hedge_ratio": float(hedge.mean()),
                "hedging_effectiveness": float(he),
            }
        )
    out = pd.DataFrame(rows).set_index("market")
    return out.reindex(out["avg_corr"].abs().sort_values(ascending=False).index)
