"""Read the RATS VARMA-GARCH H-matrices and derive the hedging quantities.

Each ``McAl-<code>-Hmatrix.xls`` is a bivariate (oil, market) model with three
columns of the time-varying conditional covariance matrix H_t. **The column
order is not fixed:** in some files oil is variable 1, in others variable 2
(verified empirically — see ``detect_oil_column``). We therefore detect which
diagonal is oil rather than assuming it, using the fact that oil is the one
series common to all seven bivariate models, so its conditional-variance path
is (nearly) identical across files while each market's is idiosyncratic.

Given the correctly oriented H_t, following Kroner & Ng (1998):

    dynamic conditional correlation  rho_t = H_cov / sqrt(H_oil * H_mkt)
    optimal hedge ratio              beta_t = H_cov / H_oil
    optimal oil portfolio weight     w_t    = (H_mkt - H_cov) / (H_mkt - 2 H_cov + H_oil)

The hedge-ratio formula is verified to reproduce the paper's own
``hedging.xlsx`` exactly (``verify_against_workbook``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import MARKETS

TRADING_DAYS = 252


def load_raw(code: str, hmatrix_dir: str | Path) -> pd.DataFrame:
    """Read one H-matrix file as its three raw columns: d1, cov, d2."""
    path = Path(hmatrix_dir) / f"McAl-{code}-Hmatrix.xls"
    raw = pd.read_excel(path, engine="xlrd")
    raw.columns = ["d1", "cov", "d2"]
    return raw.astype(float).reset_index(drop=True)


def detect_oil_column(raws: dict[str, pd.DataFrame], iters: int = 4) -> dict[str, int]:
    """Return {code: 1 or 2} naming the column that holds oil's variance.

    Oil is the common variable, so its variance series is ~identical across
    files. We iteratively build a consensus oil series and, for each file, pick
    the diagonal whose path correlates best with it.
    """
    length = min(len(df) for df in raws.values())
    oil_col = dict.fromkeys(raws, 1)  # start: assume column 1
    for _ in range(iters):
        stack = []
        for code, df in raws.items():
            col = "d1" if oil_col[code] == 1 else "d2"
            stack.append(df[col].to_numpy()[-length:])
        consensus = np.median(np.vstack(stack), axis=0)
        for code, df in raws.items():
            d1 = df["d1"].to_numpy()[-length:]
            d2 = df["d2"].to_numpy()[-length:]
            c1 = np.corrcoef(d1, consensus)[0, 1]
            c2 = np.corrcoef(d2, consensus)[0, 1]
            oil_col[code] = 1 if c1 >= c2 else 2
    return oil_col


def _derive(df: pd.DataFrame, oil_col: int) -> pd.DataFrame:
    h_oil = df["d1"] if oil_col == 1 else df["d2"]
    h_mkt = df["d2"] if oil_col == 1 else df["d1"]
    h_cov = df["cov"]
    out = pd.DataFrame(index=df.index)
    out["corr"] = h_cov / np.sqrt(h_oil * h_mkt)
    out["hedge_ratio"] = h_cov / h_oil
    denom = h_oil - 2 * h_cov + h_mkt
    out["oil_weight"] = ((h_mkt - h_cov) / denom).clip(0.0, 1.0)
    out["vol_oil"] = np.sqrt(TRADING_DAYS * h_oil)
    out["vol_mkt"] = np.sqrt(TRADING_DAYS * h_mkt)
    return out


def all_markets(hmatrix_dir: str | Path, index: pd.DatetimeIndex | None = None):
    """Return {code: derived DataFrame} for every market, oil-column auto-detected."""
    raws = {code: load_raw(code, hmatrix_dir) for code in MARKETS}
    oil_col = detect_oil_column(raws)
    result: dict[str, pd.DataFrame] = {}
    for code, df in raws.items():
        d = _derive(df, oil_col[code])
        if index is not None:
            d.index = index[-len(d):]
        result[code] = d
    return result


def hedging_effectiveness(returns, derived):
    """Variance reduction from the oil hedge, per market (HE = 1 - Var(hedged)/Var(mkt))."""
    from . import OIL

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


# Sheet name in hedging.xlsx <- CI sector code
_WORKBOOK_SHEETS = {"CI005001": "5001", "CI005002": "5002", "CI005003": "5003", "CI005005": "5005"}


def verify_against_workbook(workbook: str | Path) -> dict[str, float]:
    """Reproduce the paper's `hedging.xlsx` hedge ratios from its own H-columns.

    For each CI-sector sheet, oil is variable 2 (H22); hedge ratio = H21 / H22.
    Returns {sheet: max abs error vs the sheet's 'hedg ratio' column} — all ~0.
    """
    errors = {}
    for sheet in _WORKBOOK_SHEETS.values():
        raw = pd.read_excel(workbook, sheet_name=sheet, header=None)
        d = raw.iloc[1:].apply(pd.to_numeric, errors="coerce")
        h21, h22, hedg = d[1].to_numpy(), d[2].to_numpy(), d[8].to_numpy()
        mask = ~np.isnan(h21) & ~np.isnan(hedg)
        errors[sheet] = float(np.max(np.abs((h21[mask] / h22[mask]) - hedg[mask])))
    return errors
