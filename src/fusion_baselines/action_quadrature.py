"""Independent Gaussian integration of a reported piecewise-linear B well."""

import numpy as np

NODES, WEIGHTS = np.polynomial.legendre.leggauss(128)


def quadrature_action(length, field, left, right, bstar):
    length, field = np.asarray(length, dtype=float), np.asarray(field, dtype=float)
    if (length.ndim != 1 or length.shape != field.shape or length.size < 2
            or not np.all(np.isfinite(length)) or not np.all(np.isfinite(field))
            or np.any(np.diff(length) <= 0) or np.any(field <= 0)
            or not np.all(np.isfinite([left, right, bstar])) or bstar <= 0
            or not length[0] <= left < right <= length[-1]):
        raise ValueError("invalid well quadrature input")
    knots = np.r_[left, length[(length > left) & (length < right)], right]
    knot_field = np.interp(knots, length, field)
    if np.min(1 - knot_field / bstar) < -1e-12:
        raise ValueError("well contains a forbidden interval")
    widths = np.diff(knots) / 2
    points = (knots[1:] + knots[:-1])[:, None] / 2 + widths[:, None] * NODES
    sampled = np.interp(points.ravel(), length, field).reshape(points.shape)
    return float(np.sum(widths * (np.sqrt(np.maximum(1 - sampled / bstar, 0)) @ WEIGHTS)))
