"""Read the RATS VARMA-GARCH H-matrices and derive the hedging quantities.

Each ``McAl-<code>-Hmatrix.xls`` is a bivariate (oil, market) model and holds
three columns of the time-varying conditional covariance matrix H_t:

    VARMAHMATRIX(1,1) = conditional variance of oil
    VARMAHMATRIX(2,1) = conditional covariance of oil and the market
    VARMAHMATRIX(2,2) = conditional variance of the market

From H_t we derive, following Kroner & Ng (1998):

    dynamic conditional correlation  rho_t = H21 / sqrt(H11 * H22)
    optimal hedge ratio              beta_t = H21 / H11
    optimal oil portfolio weight     w_t    = (H22 - H21) / (H11 - 2 H21 + H22)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import MARKETS, OIL

TRADING_DAYS = 252
_COLS = {
    "VARMAHMATRIX(1,1": "H_oil",
    "VARMAHMATRIX(2,1": "H_cov",
    "VARMAHMATRIX(2,2": "H_mkt",
}


def load_hmatrix(code: str, hmatrix_dir: str | Path) -> pd.DataFrame:
    """Read one H-matrix file and return columns H_oil, H_cov, H_mkt."""
    path = Path(hmatrix_dir) / f"McAl-{code}-Hmatrix.xls"
    raw = pd.read_excel(path, engine="xlrd")
    raw = raw.rename(columns=lambda c: _COLS.get(str(c).strip(), str(c)))
    return raw[["H_oil", "H_cov", "H_mkt"]].astype(float).reset_index(drop=True)


def derive(h: pd.DataFrame) -> pd.DataFrame:
    """Dynamic correlation, hedge ratio, oil weight, annualized vols."""
    out = pd.DataFrame(index=h.index)
    out["corr"] = h["H_cov"] / np.sqrt(h["H_oil"] * h["H_mkt"])
    out["hedge_ratio"] = h["H_cov"] / h["H_oil"]
    denom = h["H_oil"] - 2 * h["H_cov"] + h["H_mkt"]
    out["oil_weight"] = ((h["H_mkt"] - h["H_cov"]) / denom).clip(0.0, 1.0)
    out["vol_oil"] = np.sqrt(TRADING_DAYS * h["H_oil"])
    out["vol_mkt"] = np.sqrt(TRADING_DAYS * h["H_mkt"])
    return out


def all_markets(hmatrix_dir: str | Path, index: pd.DatetimeIndex | None = None):
    """Return {code: derived DataFrame} for every market, optionally dated.

    The RATS output has two fewer rows than the price panel (one lost to
    differencing, one to the VAR lag); we align to the last N dates.
    """
    result: dict[str, pd.DataFrame] = {}
    for code in MARKETS:
        h = load_hmatrix(code, hmatrix_dir)
        d = derive(h)
        if index is not None:
            d.index = index[-len(d):]
        result[code] = d
    return result


def hedging_effectiveness(returns: pd.DataFrame, derived: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Variance reduction from the oil hedge, per market.

    HE = 1 - Var(r_mkt - beta_t * r_oil) / Var(r_mkt), using the time-varying
    hedge ratio aligned to the realized returns.
    """
    rows = []
    r_oil_full = returns[OIL]
    for code, name in MARKETS.items():
        d = derived[code]
        common = returns.index.intersection(d.index)
        r_mkt = returns.loc[common, code]
        r_oil = r_oil_full.loc[common]
        beta = d.loc[common, "hedge_ratio"]
        hedged = r_mkt - beta * r_oil
        he = 1.0 - hedged.var(ddof=1) / r_mkt.var(ddof=1)
        rows.append(
            {
                "series": name,
                "code": code,
                "avg_hedge_ratio": float(d["hedge_ratio"].mean()),
                "avg_oil_weight": float(d["oil_weight"].mean()),
                "avg_corr": float(d["corr"].mean()),
                "hedging_effectiveness": float(he),
            }
        )
    return pd.DataFrame(rows).set_index("series")
