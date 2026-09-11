"""Build and independently assess bounded linear models of g(x)>=0 constraints."""

import numpy as np


def linear_model(values, jacobian, scale):
    v, j = np.asarray(values, dtype=float), np.asarray(jacobian, dtype=float)
    if (
        v.ndim != 1
        or len(v) < 2
        or j.ndim != 2
        or j.shape[0] != len(v)
        or j.shape[1] == 0
        or not np.all(np.isfinite(v))
        or not np.all(np.isfinite(j))
        or not np.isscalar(scale)
        or not np.isfinite(scale)
        or scale <= 0
    ):
        raise ValueError("finite objective/inequality Jacobian and positive scale required")
    return scale * j[0], -scale * j[1:], v[1:].copy()


def assess_step(values, jacobian, scale, step, radius, tolerance=1e-8):
    c, a, b = linear_model(values, jacobian, scale)
    p = np.asarray(step, dtype=float)
    if (
        p.shape != c.shape
        or not np.all(np.isfinite(p))
        or not np.isfinite(radius)
        or radius <= 0
        or not np.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("finite model step, positive radius, nonnegative tolerance required")
    margin = b - a @ p
    box_violation = max(0.0, float(np.abs(p).max()) - radius)
    violation = max(0.0, -float(margin.min()))
    return {
        "predicted_objective_change": float(c @ p),
        "minimum_linear_constraint_margin": float(margin.min()),
        "maximum_linear_violation": violation,
        "box_violation": box_violation,
        "primal_pass": violation <= tolerance and box_violation <= tolerance,
        "linear_values": np.r_[values[0] + c @ p, margin].tolist(),
    }
