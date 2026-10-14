"""Out-of-sample extension: run the *same* Python DCC-GARCH on two periods.

The published study covers 2004-2014. To ask whether its conclusion — oil is
weakly linked to Chinese markets and so hedges/diversifies them — still holds a
decade later, we run the identical Python DCC-GARCH engine on a second period
and compare. Using one consistent method on both periods is cleaner than
mixing the RATS VARMA-CCC estimates with new Python ones.

Everything here derives from ``conditional_covariances`` (full H_t), so the
hedge ratios, correlations and portfolio weights are internally consistent
across periods.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import MARKETS, OIL
from . import data as datamod
from . import garch


@dataclass
class PeriodResult:
    label: str
    start: pd.Timestamp
    end: pd.Timestamp
    n_obs: int
    dcc_a: float
    dcc_b: float
    table: pd.DataFrame  # per-market averages
    series: dict  # code -> {dates, corr, hedge_ratio}


def analyze(source_csv: str | Path, label: str) -> PeriodResult:
    """Fit the Python DCC-GARCH and derive per-market hedging quantities."""
    prices = datamod.load_prices(source_csv)
    returns = datamod.log_returns(prices)
    cols = [OIL, *MARKETS]
    H, R, _vol, a, b = garch.conditional_covariances(returns[cols])

    rows, series = [], {}
    r_oil = returns[OIL].to_numpy()
    for j, code in enumerate(MARKETS):
        h_oil, h_mkt, h_cov = H[:, 0, 0], H[:, j + 1, j + 1], H[:, 0, j + 1]
        rho = R[:, 0, j + 1]
        hedge = h_cov / h_oil
        w_oil = np.clip((h_mkt - h_cov) / (h_mkt - 2 * h_cov + h_oil), 0.0, 1.0)
        r_mkt = returns[code].to_numpy()
        hedged = r_mkt - hedge * r_oil
        he = 1.0 - hedged.var(ddof=1) / r_mkt.var(ddof=1)
        rows.append(
            {
                "series": MARKETS[code],
                "code": code,
                "avg_corr": float(rho.mean()),
                "avg_hedge_ratio": float(hedge.mean()),
                "avg_oil_weight": float(w_oil.mean()),
                "hedging_effectiveness": float(he),
            }
        )
        series[code] = {"dates": returns.index, "corr": rho, "hedge_ratio": hedge}

    return PeriodResult(
        label=label,
        start=prices.index.min(),
        end=prices.index.max(),
        n_obs=len(prices),
        dcc_a=a,
        dcc_b=b,
        table=pd.DataFrame(rows).set_index("series"),
        series=series,
    )


def compare(old: PeriodResult, new: PeriodResult) -> pd.DataFrame:
    """Side-by-side table of avg correlation / hedge ratio / effectiveness."""
    cols = ["avg_corr", "avg_hedge_ratio", "hedging_effectiveness"]
    a = old.table[cols].add_suffix(f"_{_tag(old)}")
    b = new.table[cols].add_suffix(f"_{_tag(new)}")
    out = a.join(b)
    for c in cols:
        out[f"delta_{c}"] = out[f"{c}_{_tag(new)}"] - out[f"{c}_{_tag(old)}"]
    return out


def _tag(r: PeriodResult) -> str:
    return f"{r.start:%Y}_{r.end:%Y}"
