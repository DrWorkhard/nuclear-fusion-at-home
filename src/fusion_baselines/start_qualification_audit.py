"""Recompute stored all-row directional screens without using the native evaluator."""

import numpy as np


def audit_directions(jacobian, direction, screens):
    jacobian, direction = np.asarray(jacobian), np.asarray(direction)
    if jacobian.shape != (138, 207) or direction.shape != (207,):
        raise ValueError("complete138-by207 qualification required")
    if not np.isfinite(jacobian).all() or not np.isfinite(direction).all():
        raise ValueError("finite directional inputs required")
    if [s["eps"] for s in screens] != [1e-5, 1e-6, 1e-7, 1e-8]:
        raise ValueError("all four preregistered steps required")
    exact = jacobian @ direction
    checks = []
    for screen in screens:
        plus, minus = np.asarray(screen["plus"]), np.asarray(screen["minus"])
        if plus.shape != (138,) or minus.shape != (138,):
            raise ValueError("all138 finite-difference rows required")
        fd = (plus - minus) / (2 * screen["eps"])
        error = np.abs(fd - exact) / np.maximum(1, np.abs(exact))
        checks.append(bool(
            np.isfinite(error).all()
            and np.array_equal(fd, screen["finite_difference"])
            and np.array_equal(error, screen["normalized_errors"])
            and float(error.max()) == screen["maximum_error"]
        ))
    expected_direction = np.random.default_rng(46).normal(size=207)
    expected_direction /= np.linalg.norm(expected_direction)
    return dict(
        all_direction_arithmetic=all(checks),
        finest_direction_screen=bool(error.max() <= 1e-6),
        fixed_direction=np.array_equal(direction, expected_direction),
    )
