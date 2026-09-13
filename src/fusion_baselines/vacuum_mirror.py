"""Exact non-axisymmetric vacuum field and explicit Clebsch labels; not a torus."""

import numpy as np
from scipy.optimize import brentq

from fusion_baselines.analytic_mirror import absolute_quantities


def vacuum_field(points):
    p = np.asarray(points, dtype=float)
    if p.ndim < 1 or p.shape[-1] != 3 or not p.size or not np.isfinite(p).all():
        raise ValueError("finite Cartesian vacuum points required")
    x, y, z = np.moveaxis(p, -1, 0)
    s = 1 + z
    if np.any(s <= 0) or np.any(x * x + y * y <= 0):
        raise ValueError("vacuum control excludes S<=0 and transverse axis")
    field = np.stack((-0.7 * x, -0.3 * y, s), axis=-1)
    jac = np.broadcast_to(np.diag([-0.7, -0.3, 1.0]), (*p.shape[:-1], 3, 3)).copy()
    magnitude = np.linalg.norm(field, axis=-1)
    unit = field / magnitude[..., None]
    grad_b = unit * np.array([-0.7, -0.3, 1.0])
    jb = np.einsum("...ij,...j->...i", jac, unit)
    curvature = (jb - unit * np.sum(unit * jb, axis=-1)[..., None]) / magnitude[..., None]
    big_x, big_y = x * s**0.7, y * s**0.3
    grad_x = np.stack((s**0.7, np.zeros_like(s), 0.7 * x * s**-0.3), axis=-1)
    grad_y = np.stack((np.zeros_like(s), s**0.3, 0.3 * y * s**-0.7), axis=-1)
    grad_psi = big_x[..., None] * grad_x + big_y[..., None] * grad_y
    grad_alpha = (big_x[..., None] * grad_y - big_y[..., None] * grad_x) / (big_x**2 + big_y**2)[
        ..., None
    ]
    result = dict(
        B=field,
        jacobian=jac,
        magnitude=magnitude,
        unit=unit,
        grad_magnitude=grad_b,
        curvature=curvature,
        grad_psi=grad_psi,
        grad_alpha=grad_alpha,
        psi=(big_x**2 + big_y**2) / 2,
        alpha=np.arctan2(big_y, big_x),
        divergence=np.trace(jac, axis1=-2, axis2=-1),
        curl=np.zeros_like(p),
        force_balance_residual=np.zeros_like(p),
    )
    if not all(np.isfinite(v).all() for v in result.values()):
        raise ValueError("nonfinite vacuum geometry")
    return result


def vacuum_line(psi, alpha, z):
    z = np.asarray(z, dtype=float)
    if (
        not np.isfinite([psi, alpha]).all()
        or psi <= 0
        or not np.isfinite(z).all()
        or np.any(z <= -1)
    ):
        raise ValueError("positive finite flux and finite open-domain field line required")
    r, s = np.sqrt(2 * psi), 1 + z
    return np.stack((r * np.cos(alpha) * s**-0.7, r * np.sin(alpha) * s**-0.3, z), axis=-1)


def turning_points(psi, bstar, alpha, *, work=None):
    if not np.isfinite([psi, bstar, alpha]).all() or psi <= 0 or bstar <= 1:
        raise ValueError("finite positive flux/trapped pitch required")
    work = {} if work is None else work
    work.update(root_calls=0, roots_requested=0, roots_completed=0)

    def equation(s):
        work["root_calls"] += 1
        square = s * s + 2 * psi * (
            0.49 * np.cos(alpha) ** 2 * s**-1.4 + 0.09 * np.sin(alpha) ** 2 * s**-0.6
        )
        return square - bstar * bstar

    roots = []
    for lower, upper in ((1e-6, 1.0), (1.0, bstar)):
        if equation(lower) * equation(upper) >= 0:
            raise ValueError("registered vacuum root bracket does not straddle turning point")
        work["roots_requested"] += 1
        root = brentq(equation, lower, upper, xtol=5e-15, rtol=4 * np.finfo(float).eps)
        roots.append(root - 1.0)
        work["roots_completed"] += 1
    return np.array(roots)


def gauge_projections(field, drift):
    """Direct projections onto relabelled gradients and one fixed physical phase."""
    psi_ref = 0.03
    physical_phase = 2 * field["grad_psi"] / psi_ref + 3 * field["grad_alpha"]
    result = []
    for c in (-1, 0, 1):
        grad_beta = field["grad_alpha"] - c * field["grad_psi"] / psi_ref
        new_phase = (2 + 3 * c) * field["grad_psi"] / psi_ref + 3 * grad_beta
        result.append(
            dict(
                c=c,
                beta=np.sum(drift["total"] * grad_beta, axis=-1),
                phase=np.sum(drift["total"] * new_phase, axis=-1),
                original_phase=np.sum(drift["total"] * physical_phase, axis=-1),
            )
        )
    return result


def vacuum_units(action, transit_length, delta_psi, delta_alpha, *, mass, charge, energy_j):
    if not np.isfinite(delta_psi):
        raise ValueError("finite reduced radial displacement required")
    result = absolute_quantities(
        action, transit_length, delta_alpha, mass=mass, charge=charge, energy_j=energy_j
    )
    physical_delta = np.sqrt(2 * mass * energy_j) * delta_psi / charge
    radial_rate = physical_delta / result["time_s"]
    result.update(
        delta_psi_Wb_per_rad=float(physical_delta),
        psi_rate_Wb_per_rad_s=float(radial_rate),
        phase_rate_rad_per_s=float(2 * radial_rate / 0.03 + 3 * result["omega_alpha_rad_per_s"]),
    )
    if not np.isfinite(list(result.values())).all():
        raise ValueError("nonfinite vacuum absolute units")
    return result
