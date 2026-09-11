"""Objective-preserving spatial factorization of a squared quadratic-flux residual."""

import numpy as np


def normal_weights(normal):
    normal = np.asarray(normal, dtype=float)
    if normal.ndim < 2 or normal.shape[-1] != 3 or normal.size == 0:
        raise ValueError("normal must have nonempty (..., 3) shape")
    flat = normal.reshape(-1, 3)
    area = np.linalg.norm(flat, axis=1)
    if not np.all(np.isfinite(flat)) or not np.all(np.isfinite(area)) or np.any(area <= 0):
        raise ValueError("nonfinite or degenerate normal")
    return flat / np.sqrt(len(flat) * area)[:, None]


def spatial_flux(field, normal):
    field, normal = np.asarray(field, dtype=float), np.asarray(normal, dtype=float)
    if field.shape != normal.shape or not np.all(np.isfinite(field)):
        raise ValueError("field must match finite normal shape")
    result = np.sum(field.reshape(-1, 3) * normal_weights(normal), axis=1)
    if not np.all(np.isfinite(result)):
        raise ValueError("nonfinite spatial flux")
    return result


def lift_flux(z, jacobian=None, *, scale=1.0, threshold=0.0):
    """Return r with ||r||²=(scale*||z||²/2)², with the original cut-in.

    The Jacobian at the discontinuous positive threshold is not a two-sided
    derivative. At exactly zero flux, the unthresholded lift is differentiable.
    """
    z = np.asarray(z, dtype=float)
    if z.ndim != 1 or z.size == 0 or not np.all(np.isfinite(z)):
        raise ValueError("require a nonempty finite spatial vector")
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(threshold) or threshold < 0:
        raise ValueError("positive finite scale and nonnegative finite threshold required")
    if jacobian is not None:
        jacobian = np.asarray(jacobian, dtype=float)
        if (jacobian.ndim != 2 or jacobian.shape[0] != z.size or jacobian.shape[1] == 0
                or not np.all(np.isfinite(jacobian))):
            raise ValueError("invalid spatial Jacobian")
    norm = float(np.linalg.norm(z))
    if not np.isfinite(norm):
        raise ValueError("nonfinite spatial norm")
    if norm == 0 or norm * norm / 2 < threshold:
        return np.zeros_like(z), None if jacobian is None else np.zeros_like(jacobian)
    residual = 0.5 * scale * norm * z
    derivative = None if jacobian is None else 0.5 * scale * (
        norm * jacobian + np.outer(z / norm, z @ jacobian))
    if not np.all(np.isfinite(residual)) or (
            derivative is not None and not np.all(np.isfinite(derivative))):
        raise ValueError("nonfinite lifted output")
    return residual, derivative
