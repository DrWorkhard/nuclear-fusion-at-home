"""Exactly three affine current columns; no coil-shape optimization or admission."""

import numpy as np


def fit_affine(z0, matrix):
    z0, matrix = np.asarray(z0, dtype=float), np.asarray(matrix, dtype=float)
    if (z0.ndim != 1 or len(z0) < 3 or matrix.shape != (len(z0), 3)
            or not np.isfinite(z0).all() or not np.isfinite(matrix).all()):
        raise ValueError("finite residual and three matching current columns required")
    u, sigma, vt = np.linalg.svd(matrix, full_matrices=False)
    rank = int(np.count_nonzero(sigma > 1e-12*sigma[0]))
    condition = float(sigma[0]/sigma[-1]) if sigma[-1] > 0 else None
    result = dict(rank=rank, condition=condition, singular_values=sigma,
                  status="unqualified_rank_or_condition", qualified=False)
    if rank != 3 or condition is None or condition > 1e10:
        return result
    delta = -(vt.T @ ((u.T @ z0)/sigma))
    residual = z0 + matrix @ delta
    normal_error = float(np.linalg.norm(matrix.T @ residual) /
                         (np.linalg.norm(matrix)*max(np.linalg.norm(residual), 1e-30)))
    before, after = float(z0 @ z0/2), float(residual @ residual/2)
    if not all(np.isfinite(v).all() for v in (delta, residual, normal_error, before, after)):
        raise ValueError("nonfinite current fit result")
    result.update(delta=delta, residual=residual, normal_error=normal_error,
                  objective_before=before, objective_after=after,
                  status="completed", qualified=bool(normal_error <= 1e-10))
    return result


def physical_currents(three, total, scale):
    three = np.asarray(three, dtype=float)
    if (three.shape != (3,) or not np.isfinite(three).all()
            or not np.isfinite(total) or total <= 0 or not np.isfinite(scale) or scale <= 0):
        raise ValueError("three finite current parameters, positive total and scale required")
    values = three*scale
    result = np.append(values, total-float(values.sum()))
    if not np.isfinite(result).all():
        raise ValueError("nonfinite scaled currents")
    return result
