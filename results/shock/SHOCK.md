# Oil shock window — did 2026 break the oil–China decoupling?

Time-varying oil–China DCC correlation (oil vs SG000001, SZ399001, HS000300), 2014-10-21 → 2026-09-30. DCC(a=0.032, b=0.955).

## Headline

- Full-sample mean correlation: **0.082**
- 2026 mean: **0.010**  |  2026 peak: **0.344** (2026-02-10)

**No break.** Even the 2026 peak (0.34 on 2026-02-10) stays in the weak-link range; the decoupling absorbs the oil-supply scare rather than reversing.

![oil shock window](fig_oil_shock_window.png)

## Biggest crude moves in 2026 and the correlation that day

| Date | oil daily move | oil–China corr |
|---|---:|---:|
| 2026-03-10 | -11.8% | 0.160 |
| 2026-03-23 | -11.8% | 0.008 |
| 2026-04-01 | -15.9% | 0.164 |
| 2026-04-08 | -14.6% | 0.026 |
| 2026-05-06 | -12.0% | -0.006 |

---
*Data-driven: no event date is assumed; the marked days are simply the largest |oil return| days of 2026. Method: Python DCC-GARCH (arch + QMLE), consistent with the rest of the extension.*