"""Cartesian two-component one-way vacuum drift quadrature."""

import numpy as np
from scipy.special import roots_legendre

from fusion_baselines.analytic_mirror import reduced_drift
from fusion_baselines.vacuum_mirror import (
    gauge_projections,
    turning_points,
    vacuum_field,
    vacuum_line,
    vacuum_units,
)


def normalized_error(a, b):
    return abs(float(a) - float(b)) / max(abs(float(b)), 1e-12)


def vacuum_cell(psi, bstar, alpha, nodes, *, work=None):
    if not isinstance(nodes, int) or nodes < 8:
        raise ValueError("at least eight quadrature nodes required")
    work = {} if work is None else work
    work.update(points_requested=0, points_completed=0)
    roots = turning_points(psi, bstar, alpha, work=work)
    midpoint, halfspan = np.mean(roots), np.diff(roots)[0] / 2
    u, weights = roots_legendre(nodes)
    u, weights = u * np.pi / 2, weights * np.pi / 2
    z = midpoint + halfspan * np.sin(u)
    points = vacuum_line(psi, alpha, z)
    work["points_requested"] += nodes
    f = vacuum_field(points)
    work["points_completed"] += nodes
    drift = reduced_drift(f, bstar)
    q = drift["radicand"]
    if np.any(q <= 0):
        raise ValueError("quadrature must remain strictly between turning points")
    jac, s = halfspan * np.cos(u), 1 + z
    length = f["magnitude"] / s
    measure = length * jac / np.sqrt(q)
    x, y = points[:, 0], points[:, 1]
    bpsi = (0.49 * x * x + 0.09 * y * y) / (2 * psi * f["magnitude"])
    balpha = (
        2 * psi * np.sin(alpha) * np.cos(alpha) * (0.09 * s**-0.6 - 0.49 * s**-1.4) / f["magnitude"]
    )
    partial_measure = (np.sqrt(q) / s - length / (2 * bstar * np.sqrt(q))) * jac
    integrands = dict(
        action=np.sqrt(q) * length * jac,
        transit_length=measure,
        dpsi=drift["psi"] * measure,
        dalpha=drift["alpha"] * measure,
        action_psi=bpsi * partial_measure,
        action_alpha=balpha * partial_measure,
    )
    for coord in ("psi", "alpha"):
        for part in ("gradient", "curvature"):
            integrands[f"{coord}_{part}"] = (
                np.sum(drift[part] * f[f"grad_{coord}"], axis=1) * measure
            )
    for i, row in enumerate(gauge_projections(f, drift)):
        for key in ("beta", "phase", "original_phase"):
            integrands[f"gauge_{i}_{key}"] = row[key] * measure
    values = {key: float(weights @ value) for key, value in integrands.items()}
    vacuum = (
        np.cross(f["unit"], f["grad_magnitude"])
        * (1 - f["magnitude"] / (2 * bstar))[:, None]
        / f["magnitude"][:, None] ** 2
    )
    identities = dict(
        clebsch=float(np.max(abs(np.cross(f["grad_psi"], f["grad_alpha"]) - f["B"])))
        / max(1.0, float(np.max(abs(f["B"])))),
        vacuum_drift=float(np.max(abs(vacuum - drift["total"])))
        / max(1.0, float(np.max(abs(drift["total"])))),
        divergence=float(np.max(abs(f["divergence"]))),
        curl=float(np.max(abs(f["curl"]))),
        psi_label=float(np.max(abs(f["psi"] - psi))) / max(1.0, abs(psi)),
        alpha_label=float(np.max(abs(f["alpha"] - alpha))) / max(1.0, abs(alpha)),
    )
    errors = dict(
        radial=normalized_error(values["dpsi"], values["action_alpha"]),
        angular=normalized_error(values["dalpha"], -values["action_psi"]),
    )
    checks = dict(
        radial=errors["radial"] <= 1e-8,
        angular=errors["angular"] <= 1e-8,
        identities=max(identities.values()) <= 1e-12,
    )
    for i, c in enumerate((-1, 0, 1)):
        expected = values["dalpha"] - c * values["dpsi"] / 0.03
        action = -values["action_psi"] - c * values["action_alpha"] / 0.03
        errors[f"gauge_{i}_direct"] = normalized_error(values[f"gauge_{i}_beta"], expected)
        errors[f"gauge_{i}_action"] = normalized_error(values[f"gauge_{i}_beta"], action)
        errors[f"gauge_{i}_phase"] = normalized_error(
            values[f"gauge_{i}_phase"], values[f"gauge_{i}_original_phase"]
        )
        checks[f"gauge_{i}"] = (
            errors[f"gauge_{i}_direct"] <= 1e-8
            and errors[f"gauge_{i}_action"] <= 1e-8
            and errors[f"gauge_{i}_phase"] <= 1e-10
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
            **vacuum_units(
                values["action"],
                values["transit_length"],
                values["dpsi"],
                values["dalpha"],
                **params,
            ),
        )
        for name, params in variants.items()
    }
    arrays = dict(points=points, u=u, weights=weights, **integrands)
    arrays.update({f"field_{k}": v for k, v in f.items()})
    arrays.update({f"drift_{k}": v for k, v in drift.items()})
    if not all(np.isfinite(v).all() for v in arrays.values()):
        raise ValueError("nonfinite retained vacuum cell")
    return dict(
        psi=psi,
        bstar=bstar,
        alpha=alpha,
        nodes=nodes,
        roots=roots.tolist(),
        values=values,
        absolute=absolute,
        identity_errors=identities,
        errors=errors,
        checks=checks,
        all_pass=all(checks.values()),
    ), arrays
