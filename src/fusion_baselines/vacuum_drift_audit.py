"""Independent scalar, arithmetic, phase and SI acceptance of stored vacuum cells."""

import math

import numpy as np


def error(a, b):
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("finite vacuum audit values required")
    return abs(a - b) / max(abs(b), 1e-12)


def audit_vacuum_cell(cell, arrays, scalar, differences):
    v, n = cell["values"], cell["nodes"]
    if any(not np.isfinite(arrays[key]).all() for key in arrays):
        raise ValueError("finite saved vacuum arrays required")
    if arrays["points"].shape != (n, 3) or arrays["weights"].shape != (n,):
        raise ValueError("complete fixed quadrature shapes required")
    checks = dict(
        source=all(cell[k] == scalar[k] for k in ("psi", "bstar", "alpha")),
        scalar_complete=scalar["status"] == "completed" and not scalar["warnings"],
        roots=max(abs(a - b) for a, b in zip(cell["roots"], scalar["roots"], strict=True)) <= 1e-12,
        both_fd_scales=[(r["coordinate"], r["step"]) for r in differences]
        == [("psi", 1e-4), ("psi", 1e-5), ("alpha", 1e-4), ("alpha", 1e-5)],
        root_work=cell["work"]["roots_requested"] == cell["work"]["roots_completed"] == 2,
        field_work=cell["work"]["points_requested"] == cell["work"]["points_completed"] == n,
    )
    errors = {}
    for key, target, sign in (
        ("action", "action", 1),
        ("transit_length", "transit_length", 1),
        ("dpsi", "action_alpha", 1),
        ("dalpha", "action_psi", -1),
    ):
        errors[key] = error(v[key], sign * scalar["integrals"][target]["value"])
        checks[f"scalar_{key}"] = errors[key] <= 1e-7
    for i, row in enumerate(differences):
        value = -v["dalpha"] if row["coordinate"] == "psi" else v["dpsi"]
        errors[f"fd_{i}"] = error(value, row["derivative"])
        checks[f"fd_{i}"] = errors[f"fd_{i}"] <= 1e-6
    checks["radial_identity"] = error(v["dpsi"], v["action_alpha"]) <= 1e-8
    checks["angular_identity"] = error(v["dalpha"], -v["action_psi"]) <= 1e-8
    for key, value in v.items():
        measured = math.fsum(
            float(w) * float(f) for w, f in zip(arrays["weights"], arrays[key], strict=True)
        )
        checks[f"sum_{key}"] = abs(measured - value) <= 1e-12 * max(1.0, abs(value))
    x, y, z = arrays["points"].T
    s = 1 + z
    if np.any(s <= 0):
        raise ValueError("vacuum scalar geometry outside S>0")
    field = np.column_stack((-0.7 * x, -0.3 * y, s))
    checks["field"] = bool(np.max(abs(field - arrays["field_B"])) <= 1e-12)
    psi = (x * x * s**1.4 + y * y * s**0.6) / 2
    alpha = np.arctan2(y * s**0.3, x * s**0.7)
    checks["labels"] = bool(
        np.max(abs(psi - cell["psi"])) <= 1e-12 and np.max(abs(alpha - cell["alpha"])) <= 1e-12
    )
    checks["clebsch"] = bool(
        np.max(abs(np.cross(arrays["field_grad_psi"], arrays["field_grad_alpha"]) - field))
        <= 1e-12 * max(1.0, float(np.max(abs(field))))
    )
    checks["cartesian_jacobian"] = bool(
        np.max(abs(arrays["field_jacobian"] - np.diag([-0.7, -0.3, 1.0]))) <= 1e-12
    )
    magnitude = np.sqrt(0.49 * x * x + 0.09 * y * y + s * s)
    unit = field / magnitude[:, None]
    grad = unit * np.array([-0.7, -0.3, 1.0])
    vacuum_drift = (
        np.cross(unit, grad)
        * (1 - magnitude / (2 * cell["bstar"]))[:, None]
        / magnitude[:, None] ** 2
    )
    checks["vacuum_drift"] = bool(
        np.max(abs(arrays["drift_total"] - vacuum_drift))
        <= 1e-12 * max(1.0, float(np.max(abs(vacuum_drift))))
    )
    checks["inside"] = bool(np.all(magnitude < cell["bstar"]))
    for coord in ("psi", "alpha"):
        checks[f"parts_{coord}"] = (
            error(v[f"{coord}_gradient"] + v[f"{coord}_curvature"], v[f"d{coord}"]) <= 1e-12
        )
    phase = 2 * v["dpsi"] / 0.03 + 3 * v["dalpha"]
    for i, c in enumerate((-1, 0, 1)):
        beta = v["dalpha"] - c * v["dpsi"] / 0.03
        action_beta = -v["action_psi"] - c * v["action_alpha"] / 0.03
        checks[f"gauge_{i}_direct"] = error(v[f"gauge_{i}_beta"], beta) <= 1e-8
        checks[f"gauge_{i}_action"] = error(v[f"gauge_{i}_beta"], action_beta) <= 1e-8
        checks[f"gauge_{i}_phase"] = (
            error(v[f"gauge_{i}_phase"], phase) <= 1e-10
            and error(v[f"gauge_{i}_original_phase"], phase) <= 1e-10
        )
    reported_flags = dict(
        radial=checks["radial_identity"],
        angular=checks["angular_identity"],
        identities=max(cell["identity_errors"].values()) <= 1e-12,
    )
    expected_errors = dict(
        radial=error(v["dpsi"], v["action_alpha"]), angular=error(v["dalpha"], -v["action_psi"])
    )
    for i, c in enumerate((-1, 0, 1)):
        expected_errors[f"gauge_{i}_direct"] = error(
            v[f"gauge_{i}_beta"], v["dalpha"] - c * v["dpsi"] / 0.03
        )
        expected_errors[f"gauge_{i}_action"] = error(
            v[f"gauge_{i}_beta"], -v["action_psi"] - c * v["action_alpha"] / 0.03
        )
        expected_errors[f"gauge_{i}_phase"] = error(
            v[f"gauge_{i}_phase"], v[f"gauge_{i}_original_phase"]
        )
        reported_flags[f"gauge_{i}"] = (
            expected_errors[f"gauge_{i}_direct"] <= 1e-8
            and expected_errors[f"gauge_{i}_action"] <= 1e-8
            and expected_errors[f"gauge_{i}_phase"] <= 1e-10
        )
    checks["reported_errors"] = expected_errors == cell["errors"]
    checks["reported_flags"] = reported_flags == cell["checks"] and cell["all_pass"] == all(
        reported_flags.values()
    )
    for name, mass, charge, energy in (
        ("positive", 2e-27, 1.602176634e-19, 1e4 * 1.602176634e-19),
        ("negative", 2e-27, -1.602176634e-19, 1e4 * 1.602176634e-19),
        ("double_energy", 2e-27, 1.602176634e-19, 2e4 * 1.602176634e-19),
        ("double_mass", 4e-27, 1.602176634e-19, 1e4 * 1.602176634e-19),
    ):
        speed = math.sqrt(2 * energy / mass)
        time = v["transit_length"] / speed
        dpsi, dalpha = (math.sqrt(2 * mass * energy) * v[k] / charge for k in ("dpsi", "dalpha"))
        expected = dict(
            speed_m_per_s=speed,
            action_kg_m2_per_s=math.sqrt(2 * mass * energy) * v["action"],
            time_s=time,
            delta_alpha_rad=dalpha,
            omega_alpha_rad_per_s=dalpha / time,
            delta_psi_Wb_per_rad=dpsi,
            psi_rate_Wb_per_rad_s=dpsi / time,
            phase_rate_rad_per_s=(2 * dpsi / 0.03 + 3 * dalpha) / time,
        )
        saved = cell["absolute"][name]
        checks[f"particle_{name}"] = saved["particle"] == dict(
            mass=mass, charge=charge, energy_j=energy
        )
        for key, value in expected.items():
            checks[f"si_{name}_{key}"] = abs(saved[key] - value) / max(abs(value), 1e-300) <= 1e-12
    return dict(checks=checks, errors=errors, all_pass=all(checks.values()))
