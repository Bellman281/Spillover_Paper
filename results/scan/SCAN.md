# Sector scan — oil (Brent×CNY) vs the Chinese market, 2014–2026

Bivariate DCC-GARCH of oil against **36** market/sector series (the ones with ≥ 250 overlapping daily observations).

## Headline

- Mean |conditional correlation| with oil: **0.053**
- Most oil-linked: **Petroleum** (+0.116)
- Least oil-linked: **BeautyCare** (-0.005)

**The decoupling result generalises.** Across the whole sector map, the average absolute conditional correlation with oil is **0.053** — oil is a weak co-mover with *every* corner of the Chinese market, not just the paper's seven series. 

![sector scan](fig_sector_scan.png)

## Ranked table (by |correlation|)

| Market / sector | obs | avg corr | avg hedge ratio | hedging eff. |
|---|---:|---:|---:|---:|
| Petroleum | 2624 | +0.116 | +0.084 | 1.8% |
| Coal | 2634 | +0.103 | +0.093 | 3.5% |
| SSE50 | 2650 | +0.084 | +0.048 | 2.9% |
| Banks | 2624 | +0.080 | +0.045 | 1.4% |
| Shanghai_Comp | 2650 | +0.076 | +0.041 | 2.5% |
| NonBankFin | 2624 | +0.074 | +0.058 | 1.6% |
| CSI300 | 2650 | +0.073 | +0.043 | 2.5% |
| Utilities | 2624 | +0.067 | +0.038 | 1.2% |
| Chemicals | 2624 | +0.066 | +0.047 | 0.9% |
| NonFerrous | 2624 | +0.065 | +0.059 | 1.0% |
| Transport | 2624 | +0.062 | +0.036 | 1.1% |
| FoodBev | 2624 | +0.059 | +0.046 | 1.1% |
| Machinery | 2624 | +0.059 | +0.044 | 1.2% |
| CSI500 | 2650 | +0.058 | +0.040 | 1.3% |
| HomeAppliances | 2624 | +0.058 | +0.042 | 1.0% |
| PowerEquip | 2624 | +0.054 | +0.046 | 0.8% |
| Retail | 2624 | +0.053 | +0.038 | 0.7% |
| Shenzhen_Comp | 2650 | +0.052 | +0.036 | 1.4% |
| RealEstate | 2624 | +0.051 | +0.039 | 1.1% |
| Construction | 2624 | +0.050 | +0.036 | 1.5% |
| LightMfg | 2624 | +0.049 | +0.033 | 0.6% |
| Defense | 2624 | +0.047 | +0.045 | 1.8% |
| Autos | 2624 | +0.047 | +0.036 | 1.4% |
| SocialServices | 2624 | +0.045 | +0.038 | 0.8% |
| ChiNext | 2650 | +0.044 | +0.038 | 0.9% |
| Pharma | 2624 | +0.042 | +0.031 | 0.5% |
| Agriculture | 2624 | +0.039 | +0.029 | 0.5% |
| Electronics | 2624 | +0.039 | +0.036 | 0.9% |
| Media | 2624 | +0.036 | +0.031 | 0.8% |
| Computers | 2624 | +0.033 | +0.032 | 1.0% |
| BuildMaterials | 2624 | +0.031 | +0.025 | 1.1% |
| Textiles | 2624 | +0.031 | +0.020 | 0.4% |
| STAR50 | 1491 | +0.024 | +0.021 | 0.8% |
| Telecom | 2624 | +0.022 | +0.021 | 0.5% |
| Environmental | 1046 | +0.016 | +0.010 | 0.1% |
| BeautyCare | 1046 | -0.005 | -0.004 | 0.1% |

---
*Method: per-market two-step DCC-GARCH (arch + QMLE) on daily log returns, oil aligned pairwise to each series. Short-history sectors (many Shenwan L1 codes backfill only to the Dec-2021 reclassification) are excluded by the 250-obs floor. Consistent-method scan, not a RATS replication — see the main README.*