"""Validation tests behind the README's reproducibility claims.

What is provable, and tested here:

1. Our hedge-ratio formula reproduces the arithmetic in the paper's own
   ``hedging.xlsx`` exactly (``verify_against_workbook`` -> ~0).
2. The oil column is detected correctly per file (oil is variable 2 in the
   CI005001 and CI005005 exports, variable 1 in the other five).
3. For the one sector where the workbook and the McAl H-matrix export cleanly
   correspond (CI005001), the McAl-derived hedge ratio matches the workbook.

What is NOT claimed (and so not tested): bit-for-bit reproduction of the
published paper's tables. The estimation ran in RATS; ``hedging.xlsx`` is a
partial working file (some sheets are duplicated/stale); and this data is the
companion sector specification, not the published paper's main sector set.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from spillover import hmatrix

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "rats" / "hedging.xlsx"
HDIR = ROOT / "rats" / "hmatrices"

_requires_data = pytest.mark.skipif(
    not (WORKBOOK.exists() and HDIR.exists()), reason="RATS artifacts not present"
)


@_requires_data
def test_hedge_ratio_formula_reproduces_workbook() -> None:
    for sheet, err in hmatrix.verify_against_workbook(WORKBOOK).items():
        assert err < 1e-9, f"sheet {sheet}: hedge-ratio formula off by {err:.2e}"


@_requires_data
def test_oil_column_orientation_detected() -> None:
    raws = {c: hmatrix.load_raw(c, HDIR) for c in hmatrix.MARKETS}
    oil_col = hmatrix.detect_oil_column(raws)
    assert oil_col["CI005001"] == 2
    assert oil_col["CI005005"] == 2
    for code in ("CI005002", "CI005003", "HS000300", "SG000001", "SZ399001"):
        assert oil_col[code] == 1, f"{code} oil column misdetected"


@_requires_data
def test_ci005001_matches_workbook() -> None:
    derived = hmatrix.all_markets(HDIR)
    raw = pd.read_excel(WORKBOOK, sheet_name="5001", header=None)
    wb_mean = pd.to_numeric(raw.iloc[1:, 8], errors="coerce").dropna().mean()
    mcal_mean = derived["CI005001"]["hedge_ratio"].mean()
    assert abs(mcal_mean - wb_mean) < 5e-3, f"McAl {mcal_mean:.4f} vs workbook {wb_mean:.4f}"
