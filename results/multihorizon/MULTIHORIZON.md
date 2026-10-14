# Multi-horizon hedge: is the weak hedge a daily-frequency artifact?

Same sample (2014–2026); returns aggregated to each horizon before computing the static optimal oil hedge. Brent closes after the Chinese session, so daily same-date returns are non-synchronous and understate the link; longer horizons wash that out.

## Headline

- **Oil (sector)** hedging effectiveness: **1.9% (daily) → 4.4% (weekly) → 5.7% (monthly)**
- **Coal**: **1.7% → 3.0% → 3.8%**
- The broad indices stay weak at every horizon — the horizon effect is specific to the oil-exposed sectors, exactly where a real economic link exists.

![multi-horizon](fig_multihorizon.png)

## Correlation with oil by horizon

| horizon | Shenzhen Composite | Shanghai Composite | CSI 300 | Oil (sector) | Coal | Non-ferrous Metals | Iron |
|---|---|---|---|---|---|---|---|
| daily | 0.078 | 0.096 | 0.092 | 0.138 | 0.131 | 0.078 | 0.073 |
| weekly | 0.043 | 0.074 | 0.076 | 0.209 | 0.172 | 0.064 | 0.030 |
| biweekly | 0.069 | 0.097 | 0.108 | 0.241 | 0.194 | 0.103 | 0.046 |
| monthly | -0.007 | 0.033 | 0.024 | 0.240 | 0.196 | 0.080 | 0.074 |

## Hedging effectiveness by horizon

| horizon | Shenzhen Composite | Shanghai Composite | CSI 300 | Oil (sector) | Coal | Non-ferrous Metals | Iron |
|---|---|---|---|---|---|---|---|
| daily | 0.6% | 0.9% | 0.9% | 1.9% | 1.7% | 0.6% | 0.5% |
| weekly | 0.2% | 0.5% | 0.6% | 4.4% | 3.0% | 0.4% | 0.1% |
| biweekly | 0.5% | 0.9% | 1.2% | 5.8% | 3.8% | 1.1% | 0.2% |
| monthly | 0.0% | 0.1% | 0.1% | 5.7% | 3.8% | 0.6% | 0.5% |

## Weekly dynamic (DCC) hedge ratios

| market | weekly DCC hedge | weekly DCC corr |
|---|---:|---:|
| Shenzhen Composite | 0.038 | 0.056 |
| Shanghai Composite | 0.052 | 0.102 |
| CSI 300 | 0.052 | 0.092 |
| Oil (sector) | 0.171 | 0.245 |
| Coal | 0.178 | 0.204 |
| Non-ferrous Metals | 0.076 | 0.086 |
| Iron | 0.046 | 0.062 |

---
*Static hedge: b = cov(mkt,oil)/var(oil); HE = 1 - var(mkt - b·oil)/var(mkt). Weekly DCC via arch + QMLE. A rising HE with horizon is the signature of non-synchronous daily returns, not a stronger economy-wide link.*