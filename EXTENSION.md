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
