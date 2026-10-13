"""Pure-Python DCC-GARCH re-estimation (no RATS, no Colab).

Two-step DCC (Engle, 2002):

1. Fit a univariate GARCH(1,1) to each return series (via the ``arch``
   package) and take the standardized residuals.
2. Estimate the scalar DCC dynamics (a, b) by quasi-maximum-likelihood on the
   standardized residuals, giving the time-varying correlation matrix R_t.

This is a faithful, runnable approximation of the paper's multivariate GARCH;
point estimates will not be identical to the RATS VARMA-GARCH results, and the
README is explicit about that. It exists so the whole pipeline runs on free,
open tooling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.optimize import minimize


def _standardized_residuals(returns: pd.DataFrame) -> np.ndarray:
    z = np.empty(returns.shape)
    for j, col in enumerate(returns.columns):
        am = arch_model(returns[col].to_numpy(), mean="Constant", vol="GARCH", p=1, q=1)
        res = am.fit(disp="off")
        z[:, j] = res.std_resid
    return z


def _dcc_nll(params: np.ndarray, z: np.ndarray, Qbar: np.ndarray) -> float:
    a, b = params
    if a <= 0 or b <= 0 or a + b >= 0.9999:
        return 1e10
    T, n = z.shape
    Q = Qbar.copy()
    ll = 0.0
    for t in range(T):
        if t > 0:
            e = z[t - 1][:, None]
            Q = (1 - a - b) * Qbar + a * (e @ e.T) + b * Q
        d = np.sqrt(np.diag(Q))
        R = Q / np.outer(d, d)
        R[np.diag_indices(n)] = 1.0
        try:
            sign, logdet = np.linalg.slogdet(R)
            Rinv = np.linalg.inv(R)
        except np.linalg.LinAlgError:
            return 1e10
        zt = z[t]
        ll += logdet + float(zt @ Rinv @ zt)
    return 0.5 * ll


def fit_dcc(returns: pd.DataFrame):
    """Return (R_t, labels, a, b): time-varying correlation matrices [T,n,n]."""
    z = _standardized_residuals(returns)
    Qbar = np.corrcoef(z, rowvar=False)
    res = minimize(
        _dcc_nll,
        x0=np.array([0.02, 0.96]),
        args=(z, Qbar),
        method="L-BFGS-B",
        bounds=[(1e-4, 0.3), (0.5, 0.998)],
    )
    a, b = (res.x if res.success else (0.02, 0.96))

    T, n = z.shape
    R_t = np.empty((T, n, n))
    Q = Qbar.copy()
    for t in range(T):
        if t > 0:
            e = z[t - 1][:, None]
            Q = (1 - a - b) * Qbar + a * (e @ e.T) + b * Q
        d = np.sqrt(np.diag(Q))
        R = Q / np.outer(d, d)
        R[np.diag_indices(n)] = 1.0
        R_t[t] = R
    return R_t, list(returns.columns), float(a), float(b)
