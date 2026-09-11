"""Analytic rows from single-point field VJPs, with explicit cache initialization."""

import numpy as np


def local_field_jacobian(field, objective, points, weights):
    points, weights = np.asarray(points, dtype=float), np.asarray(weights, dtype=float)
    if (points.ndim != 2 or points.shape[1] != 3 or points.shape != weights.shape
            or len(points) == 0 or not np.all(np.isfinite(points))
            or not np.all(np.isfinite(weights))):
        raise ValueError("finite matching nonempty (n,3) point/weight arrays required")
    original_points = field.get_points_cart_ref().copy()
    jac = np.empty((len(points), len(objective.x)))
    try:
        for i in range(len(points)):
            field.set_points(points[i:i+1].copy())
            field.B()  # B_vjp reads the per-current B cache; do not omit this call.
            row = np.asarray(field.B_vjp(weights[i:i+1].copy())(objective), dtype=float)
            if row.shape != (jac.shape[1],) or not np.all(np.isfinite(row)):
                raise ValueError("invalid local field derivative")
            jac[i] = row
    finally:
        field.set_points(original_points)
    return jac
