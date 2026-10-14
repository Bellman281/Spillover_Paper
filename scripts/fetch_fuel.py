#!/usr/bin/env python3
"""Fetch China's *administered* retail fuel prices (NDRC) + matching crude.

China does not let the pump price float: the NDRC resets retail gasoline/diesel
roughly every 10 working days, tracking a lagged crude basket, but with a
**$40 floor and $130 ceiling** on crude and a "skip the move if it's small"
rule. That damping is the mechanism behind the weak oil-equity link, so this
pulls the administered series to measure the pass-through directly.

Run in your OWN terminal (the sandboxed shells block the data sites):

    source .venv/bin/activate
    python scripts/fetch_fuel.py                # add --refresh to re-download

Writes ``data/raw/china_fuel.csv``:

    date, gasoline, diesel, brent_usd, wti_usd

- gasoline / diesel: NDRC adjustment history, ``ak.energy_oil_hist`` (RMB/tonne),
  one row per adjustment event (~every 10 working days).
- brent_usd / wti_usd: Yahoo BZ=F / CL=F daily closes, reindexed onto the
  adjustment dates (last close on/before each reset).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from fetch_data import CACHE, _pick  # reuse helpers

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "china_fuel.csv"
REFRESH = "--refresh" in sys.argv


def fetch_ndrc_fuel() -> pd.DataFrame:
    """NDRC gasoline/diesel adjustment history -> date-indexed RMB/tonne frame."""
    import akshare as ak

    raw = ak.energy_oil_hist()
    cols = [str(c) for c in raw.columns]
    raw = raw.copy()
    raw.columns = cols
    date_col = _pick(cols, ("日期", "date", "调价日期", "时间")) or cols[0]
    gas_col = _pick(cols, ("汽油价格", "汽油", "gasoline", "92", "petrol"))
    die_col = _pick(cols, ("柴油价格", "柴油", "diesel", "0#"))
    if gas_col is None and die_col is None:
        raise KeyError(f"no fuel-price column found in {cols}")
    out = pd.DataFrame(index=pd.to_datetime(raw[date_col]))
    if gas_col:
        out["gasoline"] = pd.to_numeric(raw[gas_col].values, errors="coerce")
    if die_col:
        out["diesel"] = pd.to_numeric(raw[die_col].values, errors="coerce")
    return out.sort_index().dropna(how="all")


def fetch_crude(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Brent + WTI daily closes, reindexed to the last close on/before each date."""
    import yfinance as yf

    start = (dates.min() - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    end = (dates.max() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")

    def close(tk):
        df = yf.download(tk, start=start, end=end, progress=False, auto_adjust=False)["Close"]
        s = df.iloc[:, 0] if isinstance(df, pd.DataFrame) else df
        return s.astype(float)

    brent = close("BZ=F").reindex(dates, method="ffill")
    wti = close("CL=F").reindex(dates, method="ffill")
    return pd.DataFrame({"brent_usd": brent.values, "wti_usd": wti.values}, index=dates)


def main() -> None:
    cache_f = CACHE / "china_fuel_ndrc.csv"
    if cache_f.exists() and not REFRESH:
        fuel = pd.read_csv(cache_f, index_col=0, parse_dates=True)
        print(f"NDRC fuel (cached): {len(fuel)} adjustments "
              f"{fuel.index.min():%Y-%m-%d}..{fuel.index.max():%Y-%m-%d}")
    else:
        fuel = fetch_ndrc_fuel()
        CACHE.mkdir(parents=True, exist_ok=True)
        fuel.to_csv(cache_f)
        print(f"NDRC fuel: {len(fuel)} adjustments "
              f"{fuel.index.min():%Y-%m-%d}..{fuel.index.max():%Y-%m-%d}")

    crude = fetch_crude(fuel.index)
    df = fuel.join(crude).dropna(how="any")
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m/%d/%Y")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {len(df)} rows -> {OUT}")
    print(f"columns: {', '.join(c for c in df.columns if c != 'date')}")


if __name__ == "__main__":
    main()
