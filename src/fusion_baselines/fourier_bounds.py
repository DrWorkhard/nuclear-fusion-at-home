"""Analytical interpolation-error bounds for sampled periodic Fourier scalars."""

import numpy as np


def periodic_bilinear_error_bound(coefficients, modes_theta, modes_zeta, shape):
    """Bound |f - bilinear_interpolant(f)| by pure second derivatives.

    f is a cosine sum on [0,2pi)^2. The 1D linear interpolation error is
    h^2*sup|f''|/8. Tensor interpolation is an L-infinity contraction, so the
    two directional error bounds add. Triangle inequalities bound derivatives
    by sum |coefficient|*mode^2. Ordinary floats, not directed-rounding intervals.
    """
    c, m, n = [np.asarray(value, dtype=float) for value in (coefficients, modes_theta, modes_zeta)]
    if c.ndim != 1 or c.shape != m.shape or c.shape != n.shape or c.size == 0:
        raise ValueError("Fourier coefficients and modes must be equal nonempty vectors")
    if not all(np.all(np.isfinite(a)) for a in (c, m, n)):
        raise ValueError("nonfinite Fourier data")
    if len(shape) != 2 or any(not isinstance(v, (int, np.integer)) or v < 2 for v in shape):
        raise ValueError("expected two integer grid dimensions >=2")
    if np.any(m != np.rint(m)) or np.any(n != np.rint(n)):
        raise ValueError("integer modes required for periodic interpolation")
    return float(
        np.sum(abs(c) * m**2) * (2 * np.pi / shape[0]) ** 2 / 8
        + np.sum(abs(c) * n**2) * (2 * np.pi / shape[1]) ** 2 / 8
    )
