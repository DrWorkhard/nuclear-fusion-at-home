"""Cartesian analytic Clebsch mirror and first-order drift; not a toroidal QI field."""

import numpy as np


def mirror_field(points, *, b0=1.0, k=0.7):
    points = np.asarray(points, dtype=float)
    if (
        points.ndim < 1
        or points.shape[-1] != 3
        or points.size == 0
        or not np.isfinite(points).all()
        or not np.isfinite([b0, k]).all()
        or min(b0, k) <= 0
    ):
        raise ValueError("finite Cartesian points and positive mirror parameters required")
    x, y, z = np.moveaxis(points, -1, 0)
    r2 = x * x + y * y
    if np.any(r2 <= 0):
        raise ValueError("Clebsch azimuth control excludes the magnetic axis")
    s = 1 + k * z * z
    field = b0 * np.stack((-k * z * x, -k * z * y, s), axis=-1)
    jac = np.zeros((*points.shape[:-1], 3, 3))
    jac[..., 0, 0] = jac[..., 1, 1] = -b0 * k * z
    jac[..., 0, 2], jac[..., 1, 2], jac[..., 2, 2] = -b0 * k * x, -b0 * k * y, 2 * b0 * k * z
    magnitude = np.linalg.norm(field, axis=-1)
    unit = field / magnitude[..., None]
    grad_b = np.einsum("...ij,...i->...j", jac, unit)
    jac_unit = (jac - unit[..., :, None] * grad_b[..., None, :]) / magnitude[..., None, None]
    curvature = np.einsum("...ij,...j->...i", jac_unit, unit)
    grad_psi = b0 * np.stack((s * x, s * y, k * z * r2), axis=-1)
    grad_alpha = np.stack((-y / r2, x / r2, np.zeros_like(z)), axis=-1)
    curl = np.stack(
        (
            jac[..., 2, 1] - jac[..., 1, 2],
            jac[..., 0, 2] - jac[..., 2, 0],
            jac[..., 1, 0] - jac[..., 0, 1],
        ),
        axis=-1,
    )
    result = dict(
        B=field,
        jacobian=jac,
        magnitude=magnitude,
        unit=unit,
        grad_magnitude=grad_b,
        curvature=curvature,
        grad_psi=grad_psi,
        grad_alpha=grad_alpha,
        psi=b0 * s * r2 / 2,
        divergence=np.trace(jac, axis1=-2, axis2=-1),
        curl=curl,
        force_balance_residual=np.cross(curl, field) + k * b0 * grad_psi,
    )
    if not all(np.isfinite(value).all() for value in result.values()):
        raise ValueError("nonfinite analytic mirror geometry")
    return result


def reduced_drift(field, bstar):
    """Return v_d/(m*v²/q), retaining separate gradient and curvature contributions."""
    if not np.isfinite(bstar) or bstar <= 0:
        raise ValueError("positive finite bounce field required")
    radicand = 1 - field["magnitude"] / bstar
    if np.any(radicand < 0):
        raise ValueError("direct drift control requires an accessible trapped interval")
    gradient = np.cross(field["unit"], field["grad_magnitude"]) / (
        2 * bstar * field["magnitude"][..., None]
    )
    curvature = (
        np.cross(field["unit"], field["curvature"])
        * radicand[..., None]
        / field["magnitude"][..., None]
    )
    total = gradient + curvature
    result = dict(
        gradient=gradient,
        curvature=curvature,
        total=total,
        radicand=radicand,
        psi=np.sum(total * field["grad_psi"], axis=-1),
        alpha=np.sum(total * field["grad_alpha"], axis=-1),
    )
    if not all(np.isfinite(value).all() for value in result.values()):
        raise ValueError("nonfinite analytic reduced drift")
    return result


def absolute_quantities(action, transit_length, reduced_delta_alpha, *, mass, charge, energy_j):
    """One-way J, transit time, angle and frequency in SI for explicitly chosen particles."""
    values = np.array(
        [action, transit_length, reduced_delta_alpha, mass, charge, energy_j], dtype=float
    )
    if (
        not np.isfinite(values).all()
        or action <= 0
        or transit_length <= 0
        or mass <= 0
        or energy_j <= 0
        or charge == 0
    ):
        raise ValueError(
            "finite one-way action/time and positive mass/energy, nonzero charge required"
        )
    speed = np.sqrt(2 * energy_j / mass)
    time = transit_length / speed
    delta = mass * speed * reduced_delta_alpha / charge
    result = dict(
        speed_m_per_s=float(speed),
        action_kg_m2_per_s=float(mass * speed * action),
        time_s=float(time),
        delta_alpha_rad=float(delta),
        omega_alpha_rad_per_s=float(delta / time),
    )
    if not np.isfinite(list(result.values())).all():
        raise ValueError("nonfinite absolute drift units")
    return result
