# Oil–China Volatility Spillover & Hedging

Reproducible analysis for:

> **The interactions between OPEC oil price and sectoral stock returns: Evidence from China**
> Berna Kirkulak-Uludağ & **Omid Safarzadeh**, *Physica A: Statistical Mechanics and its Applications*, **508** (2018) 631–641.
> [doi:10.1016/j.physa.2018.02.185](https://doi.org/10.1016/j.physa.2018.02.185)

[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.physa.2018.02.185-ba2649.svg)](https://doi.org/10.1016/j.physa.2018.02.185)

How does the price of **OPEC oil** transmit volatility to **Chinese stock markets**, and can oil hedge a Chinese equity portfolio? Using daily data from Dec 2004 to Oct 2014, the paper fits multivariate GARCH models (BEKK, DCC, VARMA-GARCH) to OPEC oil and seven Chinese series — the Shanghai, Shenzhen and CSI 300 indices and the oil, coal, non-ferrous-metals and iron sector indices — and derives optimal hedge ratios from the time-varying covariances.

This repository makes that analysis **reproducible in pure Python** — data prep, descriptive tests, hedging quantities, and every figure — straight from the committed data and the model outputs. No Google Colab, no Google Drive mounts.

## Key findings, reproduced

**Oil is weakly linked to Chinese markets, and the link is time-varying.** From the DCC-GARCH re-estimation, the conditional correlation with oil sits around 0.1–0.2 for most of the sample and rises during the 2008 global crisis, but never approaches the tight co-movement among the Chinese series.

![Dynamic conditional correlation](results/figures/fig4_dynamic_correlation.png)

(The paper's published McAleer VAR-CCC model holds correlation *constant* by construction, so its time-variation lives entirely in the variances and hedge ratios; the time-varying correlation shown here comes from the Python DCC-GARCH re-estimation.)

The correlation matrix makes the cross-section explicit: the OPEC-oil row stays low through the 2007 run-up, the 2008 crisis, and the later sample, while the Chinese series move tightly together (≈0.7–0.98).

![Conditional correlation matrix at three dates](results/figures/fig7_correlation_matrix.png)

**That weak link makes oil an effective hedge — most for the energy-intensive sectors.** Adding oil to a sector portfolio reduces variance most for coal (4.4%) and non-ferrous metals (3.7%), least for the broad indices.

![Hedging effectiveness](results/figures/fig6_hedging_effectiveness.png)

**The optimal hedge ratio moves over time** — from the VARMA-GARCH conditional covariances, β₍ₜ₎ = H₍oil,mkt₎ / H₍oil₎:

![Time-varying hedge ratios](results/figures/fig5_hedge_ratios.png)

(Price levels, log-return series, and conditional-volatility figures are produced alongside these — see `results/figures/`.)

## Reproduce it

Requires Python 3.10+.

```bash
git clone https://github.com/Bellman281/Spillover_Paper.git
cd Spillover_Paper
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# run everything: tables -> figures -> Python DCC re-estimation -> GIF
PYTHONPATH=src python -m spillover
```

Outputs land in `results/` (`tables/*.csv`, `figures/*.png`, `figures/*.gif`).
Skip the slower DCC re-estimation and GIF with `--no-dcc`.

## What runs in Python vs. RATS

The paper's multivariate GARCH models were estimated in **RATS** (commercial). To keep the repository fully runnable on free tools, the pipeline separates the two:

| Step | Tooling here | Notes |
|------|--------------|-------|
| Data prep, log returns, descriptive stats & tests (Table 1) | **Python** | ADF, Jarque–Bera, Ljung–Box, ARCH-LM via `statsmodels`/`scipy` |
| Hedge ratios, portfolio weights, dynamic correlations, all figures | **Python** | derived from the committed RATS H-matrices (`rats/hmatrices/`) |
| BEKK / DCC / VARMA-GARCH estimation (the published numbers) | **RATS** | original `.RPF` code and `.xls` outputs are in `rats/` |
| DCC-GARCH **re-estimation** (correlation-matrix figure) | **Python** | two-step DCC (`arch` + QMLE) — a faithful, open approximation, **not** identical to the published RATS point estimates |

So the published results are reproduced from their model outputs, and the modelling is *also* demonstrated end-to-end in Python — with the honest caveat that the Python DCC is an approximation of the RATS VARMA-GARCH, not a bit-for-bit match.

## Repository layout

```
data/raw/        source.csv (prices), symbols.csv
rats/            original RATS code (.RPF) and H-matrix outputs (.xls)
src/spillover/   the Python package
  data.py         load prices, log returns
  descriptive.py  Table 1 — moments + specification tests
  hmatrix.py      read H-matrices -> correlations, hedge ratios, effectiveness
  garch.py        pure-Python two-step DCC-GARCH
  plots.py        all static figures
  __main__.py     one-command pipeline
results/         generated tables and figures
docs/            data dictionary
```

## Citation

If you use this, please cite the paper ([`CITATION.bib`](CITATION.bib)):

> Kirkulak-Uludağ, B., & Safarzadeh, O. (2018). The interactions between OPEC oil price and sectoral stock returns: Evidence from China. *Physica A*, 508, 631–641. https://doi.org/10.1016/j.physa.2018.02.185

Analysis code is MIT-licensed. The article is © Elsevier; data are included for replication only.
