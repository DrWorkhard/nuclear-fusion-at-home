"""One-way quadrature in the preregistered analytic Clebsch mirror."""

import numpy as np
from scipy.optimize import brentq
from scipy.special import roots_legendre

from fusion_baselines.analytic_mirror import absolute_quantities, mirror_field, reduced_drift


def bounce_cell(psi, bstar, alpha, nodes, *, work=None):
    work = {} if work is None else work
    work.update(root_calls=0, cartesian_points_requested=0, cartesian_points_completed=0)
    if (
        not np.isfinite([psi, bstar, alpha]).all()
        or psi <= 0
        or bstar <= 1
        or not isinstance(nodes, int)
        or nodes < 8
    ):
        raise ValueError("positive flux, trapped pitch, finite angle and >=8 nodes required")
    k, b0 = 0.7, 1.0
    c = 2 * psi * k / b0

    def polynomial(s):
        work["root_calls"] += 1
        return s**3 + (c - (bstar / b0) ** 2) * s - c

    sb, root = brentq(
        polynomial,
        1.0,
        bstar / b0,
        xtol=5e-15,
        rtol=4 * np.finfo(float).eps,
        full_output=True,
    )
    if not root.converged:
        raise ValueError("mirror turning point did not converge")
    zb = np.sqrt((sb - 1) / k)
    abscissa, weights = roots_legendre(nodes)
    u, weights = abscissa * np.pi / 2, weights * np.pi / 2
    z = zb * np.sin(u)
    s = 1 + k * z**2
    r = np.sqrt(2 * psi / (b0 * s))
    points = np.stack((r * np.cos(alpha), r * np.sin(alpha), z), axis=-1)
    work["cartesian_points_requested"] += nodes
    field = mirror_field(points)
    work["cartesian_points_completed"] += nodes
    drift = reduced_drift(field, bstar)
    q = drift["radicand"]
    if np.any(q <= 0):
        raise ValueError("all quadrature nodes must be strictly inside trapped interval")
    length = field["magnitude"] / (b0 * s)
    dz_du = zb * np.cos(u)
    measure = length * dz_du / np.sqrt(q)
    action_integrand = np.sqrt(q) * length * dz_du
    alpha_gradient = np.sum(drift["gradient"] * field["grad_alpha"], axis=1) * measure
    alpha_curvature = np.sum(drift["curvature"] * field["grad_alpha"], axis=1) * measure
    alpha_integrand = drift["alpha"] * measure
    psi_integrand = drift["psi"] * measure
    b_psi = b0 * k**2 * z**2 / (s * field["magnitude"])
    action_derivative = (
        np.sqrt(q) * b_psi / (b0 * s) - length * b_psi / (2 * bstar * np.sqrt(q))
    ) * dz_du
    integrands = dict(
        action=action_integrand,
        transit_length=measure,
        delta_alpha_reduced=alpha_integrand,
        delta_psi_reduced=psi_integrand,
        alpha_gradient=alpha_gradient,
        alpha_curvature=alpha_curvature,
        action_psi=action_derivative,
    )
    values = {name: float(weights @ value) for name, value in integrands.items()}
    identity_errors = dict(
        clebsch=float(
            np.max(abs(np.cross(field["grad_psi"], field["grad_alpha"]) - field["B"]))
            / max(1.0, float(np.max(abs(field["B"]))))
        ),
        divergence=float(np.max(abs(field["divergence"]))),
        force_balance=float(
            np.max(abs(field["force_balance_residual"]))
            / max(1.0, float(np.max(abs(k * b0 * field["grad_psi"]))))
        ),
        flux_label=float(np.max(abs(field["psi"] - psi)) / max(1.0, abs(psi))),
    )
    action_error = abs(values["delta_alpha_reduced"] + values["action_psi"]) / max(
        abs(values["action_psi"]), 1e-30
    )
    checks = dict(
        action_drift=action_error <= 1e-8,
        radial_zero=abs(values["delta_psi_reduced"]) <= 1e-10,
        field_identities=max(identity_errors.values()) <= 1e-12,
    )
    particle = dict(mass=2e-27, charge=1.602176634e-19, energy_j=1e4 * 1.602176634e-19)
    variants = dict(
        positive=particle,
        negative=dict(particle, charge=-particle["charge"]),
        double_energy=dict(particle, energy_j=2 * particle["energy_j"]),
        double_mass=dict(particle, mass=2 * particle["mass"]),
    )
    absolute = {
        name: dict(
            particle=params,
            **absolute_quantities(
                values["action"], values["transit_length"], values["delta_alpha_reduced"], **params
            ),
        )
        for name, params in variants.items()
    }
    arrays = dict(u=u, weights=weights, points=points, **integrands)
    arrays.update({f"field_{name}": value for name, value in field.items()})
    arrays.update({f"drift_{name}": value for name, value in drift.items()})
    if not all(np.isfinite(v).all() for v in arrays.values()):
        raise ValueError("nonfinite retained mirror arrays")
    return dict(
        psi=psi,
        bstar=bstar,
        alpha=alpha,
        nodes=nodes,
        turning_point_z=float(zb),
        root_calls=root.function_calls,
        root_iterations=root.iterations,
        values=values,
        absolute=absolute,
        identity_errors=identity_errors,
        action_drift_relative_error=float(action_error),
        checks=checks,
        all_pass=all(checks.values()),
    ), arrays


def refinement_checks(cells):
    if len(cells) != 3 or [r["nodes"] for r in cells] != [64, 128, 256]:
        raise ValueError("three ordered registered resolutions required")
    if len({(r["psi"], r["bstar"], r["alpha"]) for r in cells}) != 1:
        raise ValueError("refinement must hold physical line/pitch fixed")
    errors = []
    for lower, upper in zip(cells[:-1], cells[1:], strict=True):
        errors.append(
            {
                key: abs(lower["values"][key] - upper["values"][key])
                / max(abs(upper["values"][key]), 1e-30)
                for key in ("action", "transit_length", "delta_alpha_reduced")
            }
        )
    return dict(errors=errors, all_pass=all(e <= 1e-7 for r in errors for e in r.values()))
