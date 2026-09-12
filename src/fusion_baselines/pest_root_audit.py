"""Independent scalar Fourier sums and bracketed roots; no vectorized Newton call."""

import math

from scipy.optimize import brentq


def scalar_lambda(theta, phi, m, n, lam):
    shifts, dt, dp = [], [], []
    for a, b, c in zip(m, n, lam, strict=True):
        phase = float(a) * theta - float(b) * phi
        shifts.append(float(c) * math.sin(phase))
        dt.append(float(c) * float(a) * math.cos(phase))
        dp.append(-float(c) * float(b) * math.cos(phase))
    return math.fsum(shifts), math.fsum(dt), math.fsum(dp)


def scalar_root(u, phi, m, n, lam):
    if not all(math.isfinite(float(v)) for v in (u, phi, *m, *n, *lam)):
        raise ValueError("finite scalar Fourier data required")
    if not len(m) or len(set(zip(m, n, strict=True))) != len(m):
        raise ValueError("nonempty unique Fourier modes required")
    if any(float(v) != int(v) for v in (*m, *n)) or any(v < 0 for v in m):
        raise ValueError("integer physical modes required")
    extent = math.fsum(abs(float(v)) for v in lam) + 1

    def equation(theta):
        return theta + scalar_lambda(theta, phi, m, n, lam)[0] - u

    theta = brentq(equation, u - extent, u + extent, xtol=1e-13)
    shift, lt, lp = scalar_lambda(theta, phi, m, n, lam)
    residual = theta + shift - u
    return dict(theta=theta, lam=shift, lt=lt, lp=lp, residual=residual,
                denominator=1 + lt, passed=bool(abs(residual) <= 1e-12 and 1 + lt > 1e-8))
