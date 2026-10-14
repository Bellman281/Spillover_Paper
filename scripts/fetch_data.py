#!/usr/bin/env python3
"""Fetch 2014-2025 daily data for the oil-China spillover extension.

Run in your OWN terminal (needs open internet; the sandboxed shells block the
data sites):

    python3 -m venv .venv && source .venv/bin/activate
    pip install akshare yfinance -r requirements.txt
    python scripts/fetch_data.py            # add --refresh to re-download

Writes ``data/raw/source_2014_2025.csv`` in the original schema:

    date, OilRmb, SZ399001, SG000001, HS000300, CI005001, CI005002, CI005003, CI005005

Each series is cached under ``data/raw/_cache/`` on first download and reused on
later runs, so re-running does NOT re-hit the data providers (use --refresh to
force). Sources:
- Broad indices: sina ``stock_zh_index_daily`` (sh/sz prefixed).
- Coal / non-ferrous / steel: Shenwan ``index_hist_sw`` (older long-history codes).
- Petroleum (CI005001): spliced Shenwan 采掘 801020 (2014->2021) + 石油石化 801960
  (2021->), handling the Dec-2021 industry reclassification. Free stand-in for
  the paper's CITIC sectors.
- OilRmb: Brent (Yahoo BZ=F) x USD/CNY (Yahoo CNY=X).
"""

from __future__ import annotations

import sys
from pathlib import Path

import akshare as ak
import pandas as pd

START, END = pd.Timestamp("2014-10-18"), pd.Timestamp("2025-10-13")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "source_2014_2025.csv"
CACHE = ROOT / "data" / "raw" / "_cache"
REFRESH = "--refresh" in sys.argv

SCHEMA = ["OilRmb", "SG000001", "SZ399001", "HS000300",
          "CI005001", "CI005002", "CI005003", "CI005005"]
BROAD = {"SG000001": "sh000001", "SZ399001": "sz399001", "HS000300": "sh000300"}
SHENWAN = {"CI005002": "801950", "CI005003": "801050", "CI005005": "801040"}


def _pick(cols, keys):
    for k in keys:
        for c in cols:
            if k.lower() in c.lower():
                return c
    return None


def _series(df: pd.DataFrame, name: str) -> pd.Series:
    cols = [str(c) for c in df.columns]
    df = df.copy()
    df.columns = cols
    date_col = _pick(cols, ("日期", "date", "时间", "trade_date")) or cols[0]
    close_col = _pick(cols, ("收盘价", "收盘", "close", "结算价", "最新价"))
    if close_col is None:
        close_col = next((c for c in cols if "价" in c and not any(x in c for x in "开高低量额")), None)
    if close_col is None:
        raise KeyError(f"no close column in {cols}")
    s = df[[date_col, close_col]].copy()
    s[date_col] = pd.to_datetime(s[date_col])
    s = s.set_index(date_col)[close_col].astype(float).rename(name).sort_index()
    return s[(s.index >= START) & (s.index <= END)]


def cached(code: str, fetch) -> pd.Series:
    """Return the series from disk cache, or fetch + cache it."""
    f = CACHE / f"{code}.csv"
    if f.exists() and not REFRESH:
        s = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0]
        s.name = code
        print(f"     {code:9s} (cached)  {len(s)} rows  {s.index.min():%Y-%m-%d} .. {s.index.max():%Y-%m-%d}")
        return s
    s = fetch().rename(code)
    CACHE.mkdir(parents=True, exist_ok=True)
    s.to_frame().to_csv(f)
    print(f"     {code:9s} {len(s):5d} rows  {s.index.min():%Y-%m-%d} .. {s.index.max():%Y-%m-%d}")
    return s


def fetch_broad(sym):
    return lambda: _series(ak.stock_zh_index_daily(symbol=sym), "x")


def fetch_shenwan(sym):
    return lambda: _series(ak.index_hist_sw(symbol=sym, period="day"), "x")


def fetch_petroleum() -> pd.Series:
    """Splice Shenwan 采掘 (801020, pre-2021) with 石油石化 (801960, 2021+)."""
    old = _series(ak.index_hist_sw(symbol="801020", period="day"), "x")   # 2014 -> 2021-12
    new = _series(ak.index_hist_sw(symbol="801960", period="day"), "x")   # 2021-12 ->
    new = new * (old.iloc[-1] / new.iloc[0])          # rebase to continue from old
    spliced = pd.concat([old, new[new.index > old.index.max()]]).sort_index()
    return spliced


def fetch_oil_rmb() -> pd.Series:
    import yfinance as yf

    s, e = START.strftime("%Y-%m-%d"), (END + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    def close(tk):
        df = yf.download(tk, start=s, end=e, progress=False, auto_adjust=False)["Close"]
        return (df.iloc[:, 0] if isinstance(df, pd.DataFrame) else df).astype(float)

    brent, fx = close("BZ=F"), close("CNY=X")
    oil = (brent * fx.reindex(brent.index).ffill()).dropna()
    oil.index = pd.to_datetime(oil.index)
    return oil.sort_index()


def main() -> None:
    series = {}
    for code, sym in BROAD.items():
        series[code] = cached(code, fetch_broad(sym))
    for code, sym in SHENWAN.items():
        series[code] = cached(code, fetch_shenwan(sym))
    series["CI005001"] = cached("CI005001", fetch_petroleum)
    series["OilRmb"] = cached("OilRmb", fetch_oil_rmb)

    df = pd.concat([series[c].rename(c) for c in SCHEMA], axis=1, sort=True)
    df = df[SCHEMA].dropna()
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = df["date"].dt.strftime("%m/%d/%Y")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {len(df)} rows x {len(SCHEMA)} cols "
          f"({df['date'].iloc[0]} .. {df['date'].iloc[-1]}) -> {OUT}")


if __name__ == "__main__":
    main()
