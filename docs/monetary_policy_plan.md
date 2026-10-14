# PR plan — does PBoC monetary policy modulate the oil–China link?

**Status:** proposal / scoping. Not yet implemented. This doc exists to answer
"how hard is it?" before committing to the work.

## The question

The decoupling story so far is structural (administered fuel prices,
policy-driven A-shares). An open question: does **monetary policy** modulate the
oil–equity relationship? Two concrete hypotheses:

1. **Liquidity swamps oil.** In PBoC easing cycles, A-share rallies are driven by
   domestic liquidity, which should push the oil–equity correlation *down* (oil
   carries even less of the signal). Tightening should let fundamentals — oil
   included — matter more.
2. **Monetary policy is a confounder.** Oil-price shocks feed Chinese CPI/PPI,
   which the PBoC reacts to; so part of what looks like an oil→equity link may
   actually run oil→policy→equity. Controlling for policy could change the
   spillover estimate.

## Honest difficulty assessment

| Part | Difficulty | Why |
|---|---|---|
| Data assembly | **Medium** | AKShare has the series, but they are mixed-frequency, irregular (RRR/LPR are step functions), and the modern LPR regime only starts **Aug 2019**, which truncates the usable window. |
| Coding the models | **Low–Medium** | Interaction regressions and an event study are easy; a DCC-MIDAS is a known but more involved estimator. |
| **Identification** | **Hard** | This is the real obstacle, not the code. Chinese policy is anticipated, uses *many* instruments at once (RRR, OMO, MLF, LPR, window guidance), and is endogenous to the economy — including to oil-driven inflation. Clean causal identification of "the monetary-policy effect" is genuinely difficult and is where a referee will push. |

Bottom line: a **first-cut signal check is ~1–2 days**; a **defensible, publishable
treatment is ~1–2 weeks** and rests on the identification argument, not the
programming.

## Data needed (all via AKShare, to verify at build time)

- **Price of money:** 7-day reverse-repo (OMO) rate, 1-yr MLF rate, LPR 1Y/5Y
  (`ak.macro_china_lpr`), DR007 / SHIBOR (`ak.macro_china_shibor_all`,
  `ak.rate_interbank`).
- **Quantity of money:** RRR level/changes (`ak.macro_china_reserve_requirement_ratio`),
  M2 YoY (`ak.macro_china_m2_yearly`), total social financing.
- **Bond anchor:** 10Y China government bond yield (`ak.bond_china_yield`) — also
  the "did we use gov bonds?" addition, usable on its own as a flight-to-quality
  asset in the diversification frame.

Symbols drift between AKShare versions, so the fetcher must auto-detect columns
and skip-on-fail, like `fetch_scan.py` already does.

## Approaches, cheapest first

1. **Interaction regression (recommended first PR).** Take the Python DCC
   oil–equity correlation series (already produced), aggregate to monthly, and
   regress it on a monetary-stance variable (M2 YoY growth, or the policy-rate
   change) plus controls (VIX/global risk, CNY move). One table, one figure.
   Tells you whether there is *any* signal before investing more. **~1–2 days.**
2. **Event study.** Define RRR/LPR change dates; test whether the oil–equity
   correlation (or a short-window spillover) shifts in a ±N-day window. Easy to
   code; weak identification because changes are anticipated and clustered.
3. **VAR + impulse responses.** A small VAR {oil, policy rate, 10Y CGB, equity}
   with a monetary shock; trace the response of the oil–equity relationship.
   Identification via Cholesky ordering is debatable but standard.
4. **DCC-MIDAS (the rigorous version).** Let the *long-run* component of the
   oil–equity correlation be driven by a monthly macro variable (M2 growth,
   policy rate). This is the state-of-the-art way to ask "do monetary conditions
   drive the slow-moving correlation?" Genuinely novel for this pair; **~1–2
   weeks** and the strongest publishable result.

## Proposed PR structure (for approach 1 + the bond add)

- `scripts/fetch_macro.py` — PBoC rates, RRR, M2, 10Y CGB → `data/raw/macro.csv`
  (cached, skip-on-fail).
- `scripts/monetary_link.py` — monthly DCC-corr-on-stance interaction regression
  + event study → `results/monetary/` (`MONETARY.md`, figure, table).
- Add the 10Y CGB as a fourth asset to the diversification/Sharpe test, so the
  bond data earns its keep regardless of how the monetary result lands.
- README: a short "Monetary conditions" subsection under the decade-later block.

## Recommendation

Do approach **1** as a scoped PR first (cheap, tells you if the signal exists),
and fold in the **10Y CGB** since that data is independently useful. Only escalate
to DCC-MIDAS (approach 4) if the first cut shows a real, robust interaction —
that is where the week-plus of work and the identification defense belong.
