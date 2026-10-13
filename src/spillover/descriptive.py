"""Descriptive statistics and specification tests (paper Table 1)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.stattools import adfuller

from . import MARKETS, OIL, OIL_NAME


def describe(returns: pd.DataFrame) -> pd.DataFrame:
    """Per-series moments and tests for normality, stationarity, and ARCH."""
    names = {OIL: OIL_NAME, **MARKETS}
    rows = []
    for code, label in names.items():
        x = returns[code].dropna().to_numpy()
        jb_stat, jb_p = stats.jarque_bera(x)
        adf_stat, adf_p = adfuller(x, autolag="AIC")[:2]
        lb = acorr_ljungbox(x, lags=[10], return_df=True)
        arch_stat, arch_p = het_arch(x, nlags=10)[:2]
        rows.append(
            {
                "series": label,
                "code": code,
                "mean": x.mean(),
                "std": x.std(ddof=1),
                "min": x.min(),
                "max": x.max(),
                "skew": stats.skew(x),
                "kurtosis": stats.kurtosis(x, fisher=False),
                "JB": jb_stat,
                "JB_p": jb_p,
                "ADF": adf_stat,
                "ADF_p": adf_p,
                "LB(10)_p": float(lb["lb_pvalue"].iloc[0]),
                "ARCH(10)": arch_stat,
                "ARCH(10)_p": arch_p,
                "N": x.size,
            }
        )
    return pd.DataFrame(rows).set_index("series")
