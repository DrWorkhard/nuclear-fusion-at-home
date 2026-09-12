"""Natural flux residuals and the classical inequality augmented Lagrangian."""

import numpy as np


def augmented_residual(z, dz, g, dg, multipliers, rho, *, flux_scale=1e-6):
    """g >= 0; omit only the x-independent -||lambda||²/(2 rho) term.

    At a hinge the residual derivative is assigned zero; the squared merit is
    differentiable there. This is a GN model, not the exact merit Hessian.
    """
    z, dz, g, dg, multipliers = [np.asarray(a, dtype=float) for a in (z, dz, g, dg, multipliers)]
    if (
        not np.isfinite(rho)
        or rho <= 0
        or not np.isfinite(flux_scale)
        or flux_scale <= 0
        or z.ndim != 1
        or not z.size
        or g.ndim != 1
        or not g.size
        or dz.ndim != 2
        or dz.shape[0] != z.size
        or not dz.shape[1]
        or dg.shape != (g.size, dz.shape[1])
        or multipliers.shape != g.shape
        or not all(np.isfinite(a).all() for a in (z, dz, g, dg, multipliers))
        or np.any(multipliers < 0)
    ):
        raise ValueError(
            "finite compatible arrays, nonnegative multipliers and positive scales required"
        )
    shifted = g - multipliers / rho
    active = shifted < 0
    residual = np.r_[z / np.sqrt(flux_scale), np.sqrt(rho) * np.minimum(0, shifted)]
    jacobian = np.vstack((dz / np.sqrt(flux_scale), np.sqrt(rho) * active[:, None] * dg))
    return residual, jacobian


def update_multipliers(g, multipliers, rho):
    g, multipliers = np.asarray(g, dtype=float), np.asarray(multipliers, dtype=float)
    if (
        g.ndim != 1
        or not g.size
        or multipliers.shape != g.shape
        or not np.isfinite(g).all()
        or not np.isfinite(multipliers).all()
        or np.any(multipliers < 0)
        or not np.isfinite(rho)
        or rho <= 0
    ):
        raise ValueError("invalid multiplier update")
    result = np.maximum(0, multipliers - rho * g)
    if not np.isfinite(result).all():
        raise ValueError("nonfinite multiplier update")
    return result
