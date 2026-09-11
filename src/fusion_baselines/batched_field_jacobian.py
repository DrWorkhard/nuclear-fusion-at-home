"""Analytic ideal-filament projection/Jacobian using per-coil matrix contractions."""

import numpy as np


def projected_filament(points, weights, gamma, tangent, dgamma, dtangent):
    arrays = [
        np.asarray(a, dtype=float) for a in (points, weights, gamma, tangent, dgamma, dtangent)
    ]
    points, weights, gamma, tangent, dgamma, dtangent = arrays
    if (
        points.ndim != 2
        or points.shape[1] != 3
        or len(points) == 0
        or weights.shape != points.shape
        or gamma.ndim != 2
        or gamma.shape[1] != 3
        or len(gamma) == 0
        or tangent.shape != gamma.shape
        or dgamma.ndim != 3
        or dgamma.shape[:2] != gamma.shape
        or dgamma.shape[2] == 0
        or dtangent.shape != dgamma.shape
        or not all(np.all(np.isfinite(a)) for a in arrays)
    ):
        raise ValueError("invalid finite point, weight or geometry derivative arrays")
    r = points[:, None, :] - gamma[None, :, :]
    r2 = np.sum(r * r, axis=2)
    if np.any(r2 <= 0) or not np.all(np.isfinite(r2)):
        raise ValueError("singular or nonfinite observation distance")
    inv3 = r2**-1.5
    f = np.sum(np.cross(tangent[None, :, :], r) * weights[:, None, :], axis=2)
    cg = (
        np.cross(tangent[None, :, :], weights[:, None, :]) * inv3[:, :, None]
        + 3 * (f * inv3 / r2)[:, :, None] * r
    )
    ct = np.cross(r, weights[:, None, :]) * inv3[:, :, None]
    factor = 1e-7 / len(gamma)
    z = factor * np.sum(f * inv3, axis=1)
    jac = factor * (
        cg.reshape(len(points), -1) @ dgamma.reshape(-1, dgamma.shape[2])
        + ct.reshape(len(points), -1) @ dtangent.reshape(-1, dgamma.shape[2])
    )
    if not np.all(np.isfinite(z)) or not np.all(np.isfinite(jac)):
        raise ValueError("nonfinite projected field or derivative")
    return z, jac


def batched_field_jacobian(field, objective, points, weights):
    if getattr(field, "psc_array", None) is not None:
        raise ValueError("passive-current arrays are not qualified")
    names = list(objective.dof_names)
    if len(names) != len(objective.x) or len(names) != len(set(names)):
        raise ValueError("invalid global free-DOF names")
    indices = {name: i for i, name in enumerate(names)}
    z, jac = np.zeros(len(points)), np.zeros((len(points), len(names)))
    if not field.coils:
        raise ValueError("at least one physical coil required")
    for coil in field.coils:
        curve = coil.curve
        full_names = list(curve.full_dof_names)
        if len(full_names) != len(set(full_names)) or not set(curve.dof_names) <= set(names):
            raise ValueError("curve DOFs are not bound to the global basis")
        gamma, tangent = curve.gamma(), curve.gammadash()
        dgamma, dtangent = curve.dgamma_by_dcoeff(), curve.dgammadash_by_dcoeff()
        if len(full_names) != dgamma.shape[2]:
            raise ValueError("full curve derivative labels do not match columns")
        q = np.asarray(curve.quadpoints)
        if q.shape != (len(gamma),) or not np.allclose(
            q, np.arange(len(q)) / len(q), rtol=0, atol=1e-15
        ):
            raise ValueError("require the qualified uniform periodic coil quadrature")
        unit_z, geometry_jac = projected_filament(points, weights, gamma, tangent, dgamma, dtangent)
        current = float(coil.current.get_value())
        current_jac = np.asarray(coil.current.vjp(np.ones(1))(objective), dtype=float)
        if (
            not np.isfinite(current)
            or current_jac.shape != (len(names),)
            or not np.all(np.isfinite(current_jac))
        ):
            raise ValueError("invalid current derivative")
        source = [i for i, name in enumerate(full_names) if name in indices]
        target = [indices[full_names[i]] for i in source]
        z += current * unit_z
        jac[:, target] += current * geometry_jac[:, source]
        jac += np.outer(unit_z, current_jac)
    if not np.all(np.isfinite(z)) or not np.all(np.isfinite(jac)):
        raise ValueError("nonfinite assembled field derivative")
    return z, jac
