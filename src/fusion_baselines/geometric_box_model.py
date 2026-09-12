"""Fixed-radius first-order shape models; not nonlinear coil optimization."""

import numpy as np

OPTIONS = dict(
    presolve=True,
    maxiter=10000,
    time_limit=60.0,
    primal_feasibility_tolerance=1e-10,
    dual_feasibility_tolerance=1e-10,
    simplex_dual_edge_weight_strategy="steepest-devex",
)
RADII = (1e-6, 1e-5, 1e-4)


def box_model(gradient, constraints, jacobian, radius):
    h, g, jac = (np.asarray(v, dtype=float) for v in (gradient, constraints, jacobian))
    if (
        h.ndim != 1
        or not len(h)
        or g.ndim != 1
        or not len(g)
        or jac.shape != (len(g), len(h))
        or not np.isscalar(radius)
        or not np.isfinite(radius)
        or radius <= 0
        or not all(np.isfinite(v).all() for v in (h, g, jac))
    ):
        raise ValueError("finite matching geometric model arrays and positive radius required")
    norm = float(np.linalg.norm(h))
    if not np.isfinite(norm):
        raise ValueError("finite geometric gradient norm required")
    if norm == 0:
        return dict(status="zero_gradient", radius=float(radius), gradient_norm=0.0)
    b = g / radius
    if not np.isfinite(b).all():
        raise ValueError("finite scaled geometric right-hand side required")
    return dict(status="ready", c=h / norm, A=-jac, b=b, radius=float(radius), gradient_norm=norm)


def solve_model(model):
    if model["status"] != "ready":
        raise ValueError("nonzero-gradient model required for LP solution")
    from scipy.optimize import linprog

    result = linprog(
        model["c"],
        A_ub=model["A"],
        b_ub=model["b"],
        bounds=(-1.0, 1.0),
        method="highs-ds",
        options=OPTIONS.copy(),
    )
    output = dict(
        success=bool(result.success),
        status=int(result.status),
        message=str(result.message),
        nit=int(result.nit),
        objective=float(result.fun) if result.fun is not None else None,
        method="highs-ds",
        options=OPTIONS.copy(),
    )
    for key, value in (
        ("s", result.x),
        ("slack", result.ineqlin.residual),
        ("inequality_marginals", result.ineqlin.marginals),
        ("lower_marginals", result.lower.marginals),
        ("upper_marginals", result.upper.marginals),
    ):
        output[key] = np.asarray(value).copy() if value is not None else None
    return output
