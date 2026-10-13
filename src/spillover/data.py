"""Load prices and compute log returns — local files only, no Colab/Drive."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import MARKETS, OIL


def load_prices(path: str | Path) -> pd.DataFrame:
    """Load the daily price panel, indexed by date.

    Columns: OilRmb plus the seven Chinese index/sector series.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df = df.set_index("date").sort_index()
    cols = [OIL, *MARKETS.keys()]
    return df[cols].astype(float)


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Continuously-compounded returns in percent (100 * dlog)."""
    return 100.0 * np.log(prices).diff().dropna()
