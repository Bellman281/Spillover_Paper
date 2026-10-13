# Data dictionary

## `data/raw/source.csv`

Daily closing levels, 31 Dec 2004 – 17 Oct 2014 (2,355 trading days).

| Column     | Meaning                                   |
|------------|-------------------------------------------|
| `date`     | Trading date (`mm/dd/yyyy`)               |
| `OilRmb`   | OPEC reference oil price, in RMB          |
| `SZ399001` | Shenzhen Composite Index                  |
| `SG000001` | Shanghai Composite Index                  |
| `HS000300` | CSI 300 Index                             |
| `CI005001` | Oil sector index                          |
| `CI005002` | Coal sector index                         |
| `CI005003` | Non-ferrous metals sector index           |
| `CI005005` | Iron sector index                         |

All index series are rebased to 1000 on 31 Dec 2004.

## `data/raw/symbols.csv`

Ticker → English name lookup used for labelling.

## `rats/hmatrices/McAl-<code>-Hmatrix.xls`

Per-market bivariate (oil, market) VARMA-GARCH conditional covariance series
from RATS. Three columns:

| Column              | Meaning                                       |
|---------------------|-----------------------------------------------|
| `VARMAHMATRIX(1,1`  | Conditional variance of OPEC oil, H₁₁,ₜ       |
| `VARMAHMATRIX(2,1`  | Conditional covariance oil–market, H₂₁,ₜ      |
| `VARMAHMATRIX(2,2`  | Conditional variance of the market, H₂₂,ₜ     |

These have two fewer rows than `source.csv` (one lost to differencing, one to
the VAR(1) lag); the pipeline aligns them to the last *N* dates.

## `rats/*.RPF`

Original RATS program files for the BEKK, DCC, and VARMA-GARCH estimations.
Reproducing these requires a RATS licence (see the README's reproducibility note).
