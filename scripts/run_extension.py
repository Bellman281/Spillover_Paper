#!/usr/bin/env python3
"""Compare the published 2004-2014 period with a later period.

Runs the same Python DCC-GARCH on both samples and writes a comparison table,
a figure, and a short REPORT.md with an automatic verdict.

Usage:
    PYTHONPATH=src python scripts/run_extension.py \
        --old data/raw/source.csv \
        --new data/raw/source_extension.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spillover import extension, plots  # noqa: E402


def write_report(path: Path, old, new, cmp) -> None:
    oc = old.table["avg_corr"].mean()
    nc = new.table["avg_corr"].mean()
    ohe = 100 * old.table["hedging_effectiveness"].mean()
    nhe = 100 * new.table["hedging_effectiveness"].mean()
    d = nc - oc
    if nc >= 0.35:
        verdict = (
            "**The conclusion weakens.** Oil is now materially more correlated with "
            "Chinese markets, so its diversification benefit has shrunk."
        )
    elif d < -0.01:
        verdict = (
            "**The conclusion holds, and if anything strengthens.** Oil's conditional "
            "correlation with Chinese markets has *fallen* further over the decade, so "
            "oil is an even better diversifier than in the original sample. Hedging "
            "*effectiveness* is lower, but that is a consequence of the weaker link, not a "
            "contradiction: with oil and Chinese equities barely co-moving, there is little "
            "oil-driven variance left for an oil hedge to remove."
        )
    else:
        verdict = (
            "**The conclusion holds.** Oil remains weakly correlated with Chinese markets "
            "and still works as a diversifier/hedge."
        )
    lines = [
        "# Does the conclusion hold a decade later?",
        "",
        f"Same Python DCC-GARCH engine, two periods — **{old.start:%Y}–{old.end:%Y}** "
        f"({old.n_obs} obs) vs **{new.start:%Y}–{new.end:%Y}** ({new.n_obs} obs).",
        "",
        "## Headline",
        "",
        f"- Average oil–market conditional correlation: **{oc:.3f} → {nc:.3f}**",
        f"- Average hedging effectiveness: **{ohe:.1f}% → {nhe:.1f}%**",
        "",
        verdict,
        "",
        "![comparison](fig_extension_comparison.png)",
        "",
        "## Per-market comparison",
        "",
        "| Market | corr (old → new) | hedge ratio (old → new) | hedging eff. (old → new) |",
        "|---|---|---|---|",
        *(
            f"| {name} | {o['avg_corr']:.2f} → {n['avg_corr']:.2f} "
            f"| {o['avg_hedge_ratio']:.2f} → {n['avg_hedge_ratio']:.2f} "
            f"| {100 * o['hedging_effectiveness']:.1f}% → {100 * n['hedging_effectiveness']:.1f}% |"
            for name, o, n in (
                (name, old.table.loc[name], new.table.loc[name]) for name in old.table.index
            )
        ),
        "",
        "---",
        "*Method: two-step DCC-GARCH (arch + QMLE) on daily log returns. This is a "
        "consistent-method comparison, not a RATS replication; see the main README.*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", default=str(ROOT / "data" / "raw" / "source.csv"))
    ap.add_argument("--new", required=True, help="later-period CSV in the same schema")
    ap.add_argument("--out", default=str(ROOT / "results" / "extension"))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plots.set_style()

    print("fitting DCC-GARCH on the published period...")
    old = extension.analyze(args.old, "published")
    print(f"  {old.start:%Y-%m-%d}..{old.end:%Y-%m-%d}  DCC(a={old.dcc_a:.3f}, b={old.dcc_b:.3f})")
    print("fitting DCC-GARCH on the later period...")
    new = extension.analyze(args.new, "extension")
    print(f"  {new.start:%Y-%m-%d}..{new.end:%Y-%m-%d}  DCC(a={new.dcc_a:.3f}, b={new.dcc_b:.3f})")

    cmp = extension.compare(old, new)
    cmp.round(4).to_csv(out / "comparison.csv")
    old.table.round(4).to_csv(out / "period_published.csv")
    new.table.round(4).to_csv(out / "period_extension.csv")
    plots.fig_compare(old, new, out)
    write_report(out / "REPORT.md", old, new, cmp)
    print("done ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
