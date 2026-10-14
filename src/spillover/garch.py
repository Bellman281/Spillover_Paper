"""Pure-Python DCC-GARCH (no RATS, no Colab).

Two-step DCC (Engle, 2002):

1. Fit a univariate GARCH(1,1) to each return series (via ``arch``) and take the
   standardized residuals and conditional volatilities.
2. Estimate the scalar DCC dynamics (a, b) by quasi-maximum-likelihood on the
   standardized residuals, giving the time-varying correlation matrix R_t.

``conditional_covariances`` combines the two into the full conditional
covariance H_t = D_t R_t D_t, from which hedge ratios and optimal portfolio
weights follow. This is the engine the extension uses to run the *same* method
on both sample periods — a faithful, open approximation of the paper's
multivariate GARCH, not a bit-for-bit match to the RATS estimates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.optimize import minimize


def _uni_garch(returns: pd.DataFrame):
    """Return (standardized residuals, conditional volatilities), both [T, n]."""
    z = np.empty(returns.shape)
    vol = np.empty(returns.shape)
    for j, col in enumerate(returns.columns):
        res = arch_model(returns[col].to_numpy(), mean="Constant", vol="GARCH", p=1, q=1).fit(
            disp="off"
        )
        z[:, j] = res.std_resid
        vol[:, j] = res.conditional_volatility
    return z, vol


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
            _, logdet = np.linalg.slogdet(R)
            Rinv = np.linalg.inv(R)
        except np.linalg.LinAlgError:
            return 1e10
        zt = z[t]
        ll += logdet + float(zt @ Rinv @ zt)
    return 0.5 * ll


def _dcc_correlations(z: np.ndarray):
    """Estimate scalar DCC and return (R_t [T,n,n], a, b)."""
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
    return R_t, float(a), float(b)


def fit_dcc(returns: pd.DataFrame):
    """Return (R_t, labels, a, b): time-varying correlation matrices [T,n,n]."""
    z, _ = _uni_garch(returns)
    R_t, a, b = _dcc_correlations(z)
    return R_t, list(returns.columns), a, b


def conditional_covariances(returns: pd.DataFrame):
    """Return (H_t, R_t, vol, a, b): full conditional covariance H_t = D_t R_t D_t."""
    z, vol = _uni_garch(returns)
    R_t, a, b = _dcc_correlations(z)
    T, n = z.shape
    H_t = np.empty((T, n, n))
    for t in range(T):
        D = np.diag(vol[t])
        H_t[t] = D @ R_t[t] @ D
    return H_t, R_t, vol, a, b
