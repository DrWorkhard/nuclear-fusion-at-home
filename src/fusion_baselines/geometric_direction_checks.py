"""Fixed composite derivative gate and descriptive nonlinear trial measurements."""

import numpy as np

EPS = (1e-7, 1e-8)
COMPLEX_STEPS = (1e-12, 1e-20)


def errors(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("finite matching directional arrays required")
    return abs(a - b) / np.maximum(1, abs(b))


def direction_gate(jacobian, direction, fd_values, complex_derivatives):
    jac, p, fd, cd = (np.asarray(v) for v in (jacobian, direction, fd_values, complex_derivatives))
    if (
        jac.shape != (138, 207)
        or p.shape != (207,)
        or fd.shape != (2, 2, 138)
        or cd.shape != (2, 120)
        or not all(np.isfinite(v).all() for v in (jac, p, fd, cd))
        or abs(np.linalg.norm(p) - 1) > 1e-12
    ):
        raise ValueError("full finite unit-direction composite gate arrays required")
    exact = jac @ p
    fd_rows, pairs = [], []
    for i, eps in enumerate(EPS):
        estimate = (fd[i, 0] - fd[i, 1]) / (2 * eps)
        err = errors(estimate, exact)
        maximum = float(np.r_[err[:6], err[126:]].max())
        fd_rows.append(
            dict(
                eps=eps,
                finite_difference=estimate.tolist(),
                errors=err.tolist(),
                maximum_nonpair_error=maximum,
                passed=maximum <= 1e-6,
            )
        )
    for i, h in enumerate(COMPLEX_STEPS):
        err, stable = errors(cd[i], exact[6:126]), errors(cd[i], cd[0])
        pairs.append(
            dict(
                h=h,
                derivative=cd[i].tolist(),
                errors=err.tolist(),
                stability=stable.tolist(),
                passed=bool(err.max() <= 1e-9 and stable.max() <= 1e-10),
            )
        )
    return dict(
        analytic=exact.tolist(),
        finite_differences=fd_rows,
        complex_pairs=pairs,
        all_pass=all(r["passed"] for r in fd_rows + pairs),
    )


def trial_metrics(before, jacobian, step, after):
    before, jac, step, after = (np.asarray(v) for v in (before, jacobian, step, after))
    if (
        before.shape != (138,)
        or after.shape != (138,)
        or jac.shape != (138, 207)
        or step.shape != (207,)
    ):
        raise ValueError("complete trial values and Jacobian required")
    predicted = before + jac @ step
    error = errors(after, predicted)
    predicted_change = float((jac[0] @ step) * 1e-6)
    actual_change = float((after[0] - before[0]) * 1e-6)
    violation = max(0.0, -float(after[1:].min()))
    return dict(
        predicted_flux_change=predicted_change,
        actual_flux_change=actual_change,
        actual_to_predicted_change=actual_change / predicted_change
        if predicted_change != 0
        else None,
        raw_flux=float(after[0] * 1e-6),
        flux_improves=actual_change < 0,
        maximum_geometric_violation=violation,
        construction_screen_pass=violation <= 1e-8,
        geometric_linearization_errors=error[1:].tolist(),
        physical_admission=False,
    )
