"""Unthresholded quadrature metrics, independent of the optimizer's clipping."""

import numpy as np


def quadratic_flux(field, normal):
    field, normal = np.asarray(field, dtype=float), np.asarray(normal, dtype=float)
    if field.shape != normal.shape or field.ndim < 2 or field.shape[-1] != 3 or field.size == 0:
        raise ValueError("field and surface normal must have equal nonempty (...,3) shapes")
    if not np.all(np.isfinite(field)) or not np.all(np.isfinite(normal)):
        raise ValueError("nonfinite field or surface normal")
    area = np.linalg.norm(normal, axis=-1)
    if np.any(area <= 0):
        raise ValueError("degenerate surface normal")
    return float(0.5 * np.mean(np.sum(field * normal, axis=-1) ** 2 / area))
