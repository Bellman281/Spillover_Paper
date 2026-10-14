# Administered fuel prices: how much crude reaches the pump?

Elasticity of China's NDRC retail fuel to **BRENT** crude, regressed change-on-change over every price adjustment (2007–2026).

## Headline

- **Gasoline pass-through β = 0.18** — a 10% crude move passes through as about a 2% move at the pump.

| Fuel | pass-through β | robust se | R² | n |
|---|---:|---:|---:|---:|
| gasoline | 0.18 | 0.02 | 0.36 | 291 |
| diesel | 0.20 | 0.02 | 0.37 | 291 |

![fuel pass-through](fig_fuel_passthrough.png)

## Why this explains the decoupling

The pump price tracks crude only partially and with a lag. The NDRC freezes adjustments when crude is below **$40** or above **$130**, skips moves under a small threshold, and sits on top of a roughly 40% fixed tax wedge. So a crude shock is absorbed by the state and the refiners' regulated margin before it reaches households or industrial fuel buyers. With the domestic cost of oil deliberately smoothed, oil-price swings carry little information for Chinese demand, corporate margins, or equity returns — which is exactly why the oil–A-share conditional correlation stays near zero across the sector scan.

---
*Method: OLS of Δln(fuel) on Δln(crude) at each NDRC adjustment, White-robust standard errors. Crude = Yahoo BZ=F/CL=F; fuel = AKShare `energy_oil_hist`.*