"""Gauss-Newton prediction and exact residual-remainder bookkeeping, not a solver."""

import numpy as np


def quadratic_flux_model(z, jacobian, step, actual_z, *, flux_scale=1e-6):
    z, jacobian, step, actual_z = [
        np.asarray(a, dtype=float) for a in (z, jacobian, step, actual_z)
    ]
    if (
        z.ndim != 1 or z.size == 0 or actual_z.shape != z.shape
        or step.ndim != 1 or step.size == 0 or jacobian.shape != (z.size, step.size)
        or not all(np.all(np.isfinite(a)) for a in (z, jacobian, step, actual_z))
        or not np.isfinite(flux_scale) or flux_scale <= 0
    ):
        raise ValueError("finite matching residual/Jacobian/step and positive scale required")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        tangent = jacobian @ step
        linear_z = z + tangent
        remainder = actual_z - linear_z
        baseline = float(z @ z / (2 * flux_scale))
        actual = float(actual_z @ actual_z / (2 * flux_scale))
        linear_change = float(z @ tangent / flux_scale)
        curvature = float(tangent @ tangent / (2 * flux_scale))
        quadratic = float(linear_z @ linear_z / (2 * flux_scale))
        # Independently associate the matrix products instead of reusing tangent.
        gradient = jacobian.T @ z / flux_scale
        hessian = jacobian.T @ jacobian / flux_scale
        matrix_value = float(baseline + gradient @ step + step @ hessian @ step / 2)
        rest = float((linear_z @ remainder + remainder @ remainder / 2) / flux_scale)
        linear_error = abs(actual - (baseline + linear_change))
        quadratic_error = abs(actual - quadratic)
        result = {
            "baseline": baseline,
            "actual": actual,
            "actual_change": actual - baseline,
            "linear_change": linear_change,
            "gn_curvature_term": curvature,
            "quadratic_change": quadratic - baseline,
            "linear_absolute_error": linear_error,
            "quadratic_absolute_error": quadratic_error,
            "quadratic_to_linear_error_ratio": quadratic_error / max(linear_error, 1e-300),
            "field_linearization_remainder_norm": float(np.linalg.norm(remainder)),
            "matrix_identity_error": abs(quadratic - matrix_value) / max(1, abs(quadratic)),
            "remainder_identity_error": abs(actual - quadratic - rest) / max(1, abs(actual)),
        }
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("nonfinite quadratic model result")
    result["correct_change_sign"] = bool(
        np.sign(result["quadratic_change"]) == np.sign(result["actual_change"])
    )
    result["usefulness_pass"] = bool(
        result["correct_change_sign"] and quadratic_error <= 0.1 * linear_error
    )
    return result
