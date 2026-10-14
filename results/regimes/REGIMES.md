# Regime-switching: the oil–China link wakes up in crises

A 2-state Markov-switching model on daily **CSI 300** returns (2014–2026) splits the sample into a calm regime (σ≈0.9%/day) and a turbulent one (σ≈2.4%/day). The market is in the turbulent regime **21%** of the time; expected spells last ~82 days (calm) and ~22 days (turbulent).

## Oil–market correlation by regime

| market | calm | turbulent | gap |
|---|---:|---:|---:|
| Shanghai Composite | 0.072 | 0.129 | +0.057 |
| CSI 300 | 0.069 | 0.124 | +0.054 |
| Oil (sector) | 0.127 | 0.157 | +0.031 |
| Coal | 0.098 | 0.178 | +0.080 |

![regimes](fig_regimes.png)

## Reading

The flat ~0.09 average is misleading: the oil–China correlation is **state-dependent**. It sits near zero in calm markets and rises in the turbulent regime — oil diversifies right up until a crisis, when the link reappears and the diversification benefit fades exactly when it is most needed. This is the honest refinement of the 'oil is a diversifier' claim, and it is invisible to a single full-sample DCC average.

---
*MarkovRegression (statsmodels), switching mean + variance, 2 regimes; regimes assigned by smoothed P(turbulent) > 0.5; correlations are within-regime Pearson.*