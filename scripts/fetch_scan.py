#!/usr/bin/env python3
"""Fetch a WIDE Chinese-market universe for the oil-spillover sector scan.

Run in your OWN terminal (the sandboxed shells block the data sites):

    source .venv/bin/activate
    python scripts/fetch_scan.py                 # Brent (default)
    python scripts/fetch_scan.py --oil wti        # WTI instead
    python scripts/fetch_scan.py --refresh        # ignore the cache

Writes ``data/raw/scan_universe.csv``: OilRmb plus every broad index and
Shenwan Level-1 industry index we can pull. This is deliberately broad so the
oil-China link can be *scanned* across the whole sector map rather than the
paper's seven series.

Design notes
------------
- Resilient: if a symbol 404s or AKShare renames it, that series is skipped with
  a warning instead of aborting the whole run.
- Ragged history is fine: the CSV is an OUTER join (NaN-padded). The scan
  (``scripts/scan_sectors.py``) drops NaNs *pairwise* against oil and skips any
  market with < 250 overlapping observations, so short-history sectors (many
  Shenwan L1 codes only backfill to the Dec-2021 reclassification) just fall
  out of the ranking automatically.
- Reuses the cached, column-auto-detecting helpers from ``fetch_data.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from fetch_data import (  # reuse the proven helpers
    OIL_TICKERS,
    cached,
    fetch_broad,
    fetch_oil_rmb,
    fetch_petroleum,
    fetch_shenwan,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "scan_universe.csv"

# Broad market indices (sina stock_zh_index_daily symbols) -------------------
BROAD = {
    "Shanghai_Comp": "sh000001",
    "Shenzhen_Comp": "sz399001",
    "CSI300": "sh000300",
    "CSI500": "sh000905",
    "ChiNext": "sz399006",
    "SSE50": "sh000016",
    "STAR50": "sh000688",
}

# Shenwan Level-1 industry indices (申万一级, modern 2021 codes). -------------
# Many only backfill to 2021-12; the scan auto-skips the short ones.
SHENWAN_L1 = {
    "Agriculture": "801010",
    "Chemicals": "801030",
    "Steel": "801040",
    "NonFerrous": "801050",
    "Electronics": "801080",
    "HomeAppliances": "801110",
    "FoodBev": "801120",
    "Textiles": "801130",
    "LightMfg": "801140",
    "Pharma": "801150",
    "Utilities": "801160",
    "Transport": "801170",
    "RealEstate": "801180",
    "Retail": "801200",
    "SocialServices": "801210",
    "BuildMaterials": "801710",
    "Construction": "801720",
    "PowerEquip": "801730",
    "Defense": "801740",
    "Computers": "801750",
    "Media": "801760",
    "Telecom": "801770",
    "Banks": "801780",
    "NonBankFin": "801790",
    "Autos": "801880",
    "Machinery": "801890",
    "Coal": "801950",
    "Environmental": "801970",
    "BeautyCare": "801980",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oil", choices=list(OIL_TICKERS), default="brent")
    ap.add_argument("--refresh", action="store_true", help="ignore the disk cache")
    args = ap.parse_args()

    print(f"oil benchmark: {args.oil.upper()} ({OIL_TICKERS[args.oil]})")
    series: dict[str, pd.Series] = {}
    skipped: list[str] = []

    def grab(code: str, fetch) -> None:
        try:
            series[code] = cached(code, fetch, args.refresh)
        except Exception as exc:  # noqa: BLE001 - resilience is the point
            skipped.append(f"{code}: {type(exc).__name__}: {exc}")
            print(f"     {code:16s} SKIPPED ({type(exc).__name__})")

    # oil first
    grab("OilRmb", lambda: fetch_oil_rmb(args.oil))
    # petroleum sector (spliced) kept under its paper code for continuity
    grab("Petroleum", fetch_petroleum)
    for name, sym in BROAD.items():
        grab(name, fetch_broad(sym))
    for name, sym in SHENWAN_L1.items():
        grab(name, fetch_shenwan(sym))

    if "OilRmb" not in series:
        raise SystemExit("FATAL: could not fetch OilRmb; nothing to scan against.")

    # outer join -> ragged wide frame; scan aligns each pair itself
    df = pd.concat(series.values(), axis=1, sort=True)
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m/%d/%Y")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"\nwrote {len(df)} rows x {df.shape[1] - 1} series -> {OUT}")
    print(f"series: {', '.join(c for c in df.columns if c != 'date')}")
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
