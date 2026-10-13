"""Reproducible analysis for Kirkulak-Uludag & Safarzadeh (2018), Physica A 508.

Volatility spillover and hedging between OPEC oil prices and Chinese sectoral
stock returns. This package reproduces, in pure Python, the data preparation,
descriptive statistics, hedging analysis, and figures from the paper's
committed data and RATS conditional-covariance (H-matrix) outputs, and adds a
Python DCC-GARCH re-estimation so the modelling no longer depends on Colab or
RATS.
"""

from __future__ import annotations

__version__ = "1.0.0"

OIL = "OilRmb"

# Series code -> human-readable name. Order matters for the figures.
MARKETS: dict[str, str] = {
    "SZ399001": "Shenzhen Composite",
    "SG000001": "Shanghai Composite",
    "HS000300": "CSI 300",
    "CI005001": "Oil (sector)",
    "CI005002": "Coal",
    "CI005003": "Non-ferrous Metals",
    "CI005005": "Iron",
}

OIL_NAME = "OPEC oil (RMB)"
