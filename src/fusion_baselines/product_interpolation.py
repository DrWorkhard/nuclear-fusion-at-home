"""Separate interpolated node residuals from products of interpolated factors."""

import numpy as np


def decompose(g, b, h, fraction, psi):
    g, b, h = [np.asarray(v, dtype=float) for v in (g, b, h)]
    if (
        g.shape != b.shape
        or g.shape != h.shape
        or g.ndim < 2
        or g.shape[0] != 2
        or not all(np.isfinite(v).all() for v in (g, b, h))
        or not np.isfinite(fraction)
        or not 0 <= fraction <= 1
        or not np.isfinite(psi)
        or psi == 0
    ):
        raise ValueError("two finite equal-shaped endpoint fields and valid weight/flux required")
    nodes = g * b - psi * h
    averaged = (1 - fraction) * nodes[0] + fraction * nodes[1]
    product_term = -fraction * (1 - fraction) * (g[1] - g[0]) * (b[1] - b[0])
    return nodes, averaged, product_term, averaged + product_term
