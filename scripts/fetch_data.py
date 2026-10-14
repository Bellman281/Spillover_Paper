#!/usr/bin/env python3
"""Fetch 2014-2025 daily data for the oil-China spillover extension.

IMPORTANT: run this in your OWN terminal (not inside Claude) — it needs open
internet access to Chinese market-data sites, which the sandboxed shells block.

    pip install akshare pandas
    python scripts/fetch_data.py

It writes ``data/raw/source_2014_2025.csv`` in the SAME schema as the original
``source.csv``:

    date, OilRmb, SZ399001, SG000001, HS000300, CI005001, CI005002, CI005003, CI005005

Notes / things to verify for your data vintage (AKShare symbols drift):
- Sector indices: the original paper used CITIC (中信) industry indices
  (CI005001 oil, CI005002 coal, CI005003 non-ferrous, CI005005 iron). Those are
  not freely available, so this script uses the Shenwan (申万) first-level
  industry indices as the standard free equivalent. Document this substitution.
- OilRmb: reconstructed as Brent (USD/bbl) x USD/CNY, a proxy for the OPEC
  basket in RMB used in the paper.
If any series fails, the script still writes what it got and prints what is
missing, so you can fill the gap (or just send me the CSVs and I'll assemble it).
"""

from __future__ import annotations

from pathlib import Path

import akshare as ak
import pandas as pd

START, END = "20141018", "20251013"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "source_2014_2025.csv"

# Broad A-share indices (AKShare returns Chinese columns: 日期 / 收盘)
BROAD = {"SZ399001": "399001", "SG000001": "000001", "HS000300": "000300"}

# Shenwan first-level industry indices as the free stand-in for the CITIC sectors.
# VERIFY these codes for your AKShare version before trusting the numbers.
SHENWAN = {
    "CI005001": "801960",  # 石油石化  Petroleum & petrochemical  (<- CITIC oil)
    "CI005002": "801950",  # 煤炭      Coal
    "CI005003": "801050",  # 有色金属  Non-ferrous metals
    "CI005005": "801040",  # 钢铁      Steel / iron
}


def _close(df: pd.DataFrame, date_col: str, close_col: str, name: str) -> pd.Series:
    s = df[[date_col, close_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col])
    return s.set_index(date_col)[close_col].rename(name).astype(float)


def fetch_broad(code: str, sym: str) -> pd.Series:
    df = ak.index_zh_a_hist(symbol=sym, period="daily", start_date=START, end_date=END)
    return _close(df, "日期", "收盘", code)


def fetch_shenwan(code: str, sym: str) -> pd.Series:
    df = ak.index_hist_sw(symbol=sym, period="day")
    df = df.rename(columns={c: c.strip() for c in df.columns})
    return _close(df, "日期", "收盘", code)


def fetch_oil_rmb() -> pd.Series:
    # Brent (USD) x USD/CNY. Adjust to your preferred AKShare oil/FX endpoints.
    brent = ak.energy_oil_hist()  # columns incl. 日期 / 收盘 (USD/bbl)
    brent = _close(brent, "日期", "收盘", "brent")
    fx = ak.currency_boc_sina(symbol="美元", start_date=START, end_date=END)
    fx = _close(fx, "日期", "中行汇买价", "usdcny") / 100.0  # BOC quotes per 100 units
    return (brent * fx.reindex(brent.index).ffill()).rename("OilRmb")


def main() -> None:
    series, missing = [], []
    for code, sym in BROAD.items():
        try:
            series.append(fetch_broad(code, sym))
            print(f"ok   {code} <- index_zh_a_hist({sym})")
        except Exception as e:  # noqa: BLE001
            missing.append(code)
            print(f"FAIL {code}: {type(e).__name__}: {str(e)[:90]}")
    for code, sym in SHENWAN.items():
        try:
            series.append(fetch_shenwan(code, sym))
            print(f"ok   {code} <- index_hist_sw({sym})  [Shenwan proxy]")
        except Exception as e:  # noqa: BLE001
            missing.append(code)
            print(f"FAIL {code}: {type(e).__name__}: {str(e)[:90]}")
    try:
        series.append(fetch_oil_rmb())
        print("ok   OilRmb <- Brent x USD/CNY")
    except Exception as e:  # noqa: BLE001
        missing.append("OilRmb")
        print(f"FAIL OilRmb: {type(e).__name__}: {str(e)[:90]}")

    if not series:
        raise SystemExit("nothing fetched — check AKShare install and network")

    df = pd.concat(series, axis=1).dropna(how="all")
    order = ["OilRmb", *BROAD, *SHENWAN]
    df = df[[c for c in order if c in df.columns]].dropna()
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = df["date"].dt.strftime("%m/%d/%Y")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {len(df)} rows -> {OUT}")
    if missing:
        print("MISSING:", ", ".join(missing), "-> fill these in or send me the series")


if __name__ == "__main__":
    main()
