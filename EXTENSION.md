# Extension: does the result hold a decade later?

The published study covers **2004–2014**. This branch asks whether its
conclusion — oil is weakly linked to Chinese markets and therefore hedges /
diversifies them — still holds on a later sample, by running the **same**
Python DCC-GARCH engine on both periods and comparing.

## Why Python DCC on both periods

The original estimation ran in RATS (VARMA-CCC), which can't be re-run for a new
period without a RATS licence. So the extension uses the repo's pure-Python
DCC-GARCH on **both** samples — a consistent-method comparison. On the original
data this engine reproduces the RATS hedge ratios closely (e.g. coal 0.320 vs
0.321), so it is a sound basis for the comparison. It is an approximation of the
paper's model, not a bit-for-bit replication (see the main README).

## Step 1 — get the later-period data (run on your own machine)

The sandboxed shells can't reach market-data sites, so fetch locally:

```bash
pip install akshare pandas
python scripts/fetch_data.py        # writes data/raw/source_2014_2025.csv
```

`fetch_data.py` pulls daily closes for the three broad indices (Shanghai,
Shenzhen, CSI 300), four **Shenwan** industry indices as the free stand-in for
the paper's CITIC sectors (oil, coal, non-ferrous, iron), and reconstructs
`OilRmb` as Brent × USD/CNY. AKShare symbols drift between versions — the script
prints what it fetched and flags anything missing. If a series fails, fill it in
or just send the CSVs and they can be assembled by hand. The output must match
the original schema:

```
date, OilRmb, SZ399001, SG000001, HS000300, CI005001, CI005002, CI005003, CI005005
```

## Step 2 — run the comparison

```bash
PYTHONPATH=src python scripts/run_extension.py --new data/raw/source_2014_2025.csv
```

This writes to `results/extension/`:

- `REPORT.md` — headline, an automatic verdict, and a per-market table
- `fig_extension_comparison.png` — grouped bars (correlation, hedge ratio,
  hedging effectiveness) for the two periods
- `comparison.csv`, `period_published.csv`, `period_extension.csv`

The machinery is tested; only the later-period data is pending.

## Step 3 — widen the universe (sector scan)

The paper looks at seven series. To check whether the weak-oil-link result is
specific to those or holds across the market, scan oil against a broad Shenwan
Level-1 industry universe plus the main broad indices:

```bash
python scripts/fetch_scan.py                           # --oil wti for WTI
PYTHONPATH=src python scripts/scan_sectors.py --data data/raw/scan_universe.csv
```

Writes `results/scan/`: `SCAN.md` (ranked table + read), `fig_sector_scan.png`,
`scan.csv`. Each market is fit as a bivariate DCC-GARCH against oil; oil is
aligned pairwise, and any sector with < 250 overlapping observations (many
Shenwan L1 codes only backfill to the Dec-2021 reclassification) is skipped.
You can run the scan on the paper's seven series with no extra fetch by pointing
`--data` at `source_2014_2025.csv`.

## Step 4 — why the link is weak (administered fuel pass-through)

China does not let the pump price float: the NDRC resets retail gasoline/diesel
about every ten working days, but with a $40 floor and $130 ceiling on crude, a
skip-small-moves rule, and a ~40% fixed tax wedge. That damping is the mechanism
behind the decoupling. Measure it directly:

```bash
python scripts/fetch_fuel.py
PYTHONPATH=src python scripts/fuel_passthrough.py --data data/raw/china_fuel.csv
```

Writes `results/fuel/`: `FUEL.md`, `fig_fuel_passthrough.png`, `passthrough.csv`.
It regresses Δln(fuel) on Δln(crude) at each adjustment event; a pass-through
β well below 1 shows how little of a crude shock reaches the Chinese consumer —
and therefore Chinese demand, margins, and equity returns.

## Oil benchmark: Brent or WTI

Every fetcher takes `--oil brent` (default, `BZ=F`) or `--oil wti` (`CL=F`); the
RMB conversion (× `CNY=X`) is the same. Brent/WTI cache separately, so switching
does not clobber the other.

## Note on the 2026 US–Iran / Strait of Hormuz crisis

That shock is **not** in this study. The data ends **2025-10-13**, before the
event. Capturing it would need a data refresh to a 2026 end date and should be
reported as a separate, clearly-dated cut — not folded into these results.
