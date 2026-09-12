"""Reconstruct current probe/fit arithmetic without native calls or producer weights."""

import math

import numpy as np

from fusion_baselines.affine_current_audit import qr_fit


def error(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching finite independent current arrays required")
    return float(np.max(abs(a - b) / np.maximum(1, abs(b))))


def project(b, normal):
    """Separate explicit Cartesian sum, normalized surface measure."""
    b, normal = np.asarray(b), np.asarray(normal)
    if b.shape != normal.shape or b.ndim != 3 or b.shape[-1] != 3:
        raise ValueError("matching surface vectors required")
    area = np.sqrt(normal[..., 0] ** 2 + normal[..., 1] ** 2 + normal[..., 2] ** 2)
    if not np.isfinite(b).all() or not np.isfinite(area).all() or np.any(area <= 0):
        raise ValueError("finite field and nondegenerate normals required")
    product = b[..., 0] * normal[..., 0] + b[..., 1] * normal[..., 1] + b[..., 2] * normal[..., 2]
    return (product / np.sqrt(area * area.size)).ravel()


def audit_arrays(data, row):
    """Audit a completed, qualified two-bundle case; unqualified inputs fail closed."""
    if row["status"] != "completed" or not row["all_pass"]:
        raise ValueError("completed qualified case required for minimizer audit")
    x, cols, n = data["x"], data["columns"], data["normal"]
    if (
        x.shape != (207,)
        or cols.shape != (3,)
        or cols.dtype.kind not in "iu"
        or len(set(cols)) != 3
        or np.any((cols < 0) | (cols >= 207))
        or n.shape != (32, 32, 3)
        or data["B_probes"].shape != (3, 2, 32, 32, 3)
        or data["probe_points"].shape != (3, 2, 207)
        or data["before_values"].shape != (138,)
        or data["after_values"].shape != (138,)
        or data["before_jacobian"].shape != (138, 207)
        or data["after_jacobian"].shape != (138, 207)
    ):
        raise ValueError("canonical current diagnostic array dimensions required")
    for value in data.values():
        if not np.isfinite(value).all():
            raise ValueError("nonfinite saved diagnostic array")
    b0, pairs = data["B_before"], data["B_probes"]
    slopes = (pairs[:, 0] - pairs[:, 1]) / 0.002
    a = np.column_stack([project(s, n) for s in slopes])
    z = project(b0, n)
    checks = dict(
        columns=row["columns"] == cols.tolist(),
        slopes=error(slopes, data["B_slopes"]) <= 1e-12,
        matrix=error(a, data["A"]) <= 1e-12,
        residual=error(z, data["z0"]) <= 1e-12,
    )
    probe_errors = []
    expected_calls = [(x, b0)]
    for i, col in enumerate(cols):
        for j, sign in enumerate((1, -1)):
            proposal = x.copy()
            proposal[col] += sign * 0.001
            checks[f"probe_{i}_{j}_geometry"] = np.array_equal(data["probe_points"][i, j], proposal)
            expected_calls.append((proposal, pairs[i, j]))
            probe_errors.append(error(pairs[i, j], b0 + sign * 0.001 * slopes[i]))
    checks["affine_probes"] = max(probe_errors) <= 1e-12
    checks["reported_affine_errors"] = (
        error(np.array(probe_errors).reshape(3, 2), row["affine_errors"]) <= 1e-12
    )
    sigma = np.linalg.svd(a, compute_uv=False)
    rank = int(np.count_nonzero(sigma > 1e-12 * sigma[0]))
    condition = float(sigma[0] / sigma[-1]) if sigma[-1] > 0 else math.inf
    checks["rank_condition"] = (
        rank == 3
        and condition <= 1e10
        and row["fit"]["rank"] == rank
        and error(condition, row["fit"]["condition"]) <= 1e-12
        and error(sigma, data["singular_values"]) <= 1e-12
    )
    if not checks["rank_condition"]:
        return dict(checks={k: bool(v) for k, v in checks.items()}, all_pass=False)
    fit = qr_fit(z, a)
    delta = data["delta"]
    r = z + a @ delta
    normal_error = float(
        np.linalg.norm(a.T @ r) / (np.linalg.norm(a) * max(np.linalg.norm(r), 1e-30))
    )
    phi = 0.5 * math.fsum(float(v * v) for v in r)
    checks.update(
        independent_delta=error(fit["delta"], delta) <= 1e-10,
        recorded_qr_delta=error(fit["delta"], data["qr_delta"]) <= 1e-10,
        recorded_residual=error(r, data["residual"]) <= 1e-12,
        recorded_qr_residual=error(fit["residual"], data["qr_residual"]) <= 1e-12,
        normal_rest=normal_error <= 1e-10 and fit["normal_error"] <= 1e-10,
        reported_normal_rest=error(normal_error, row["fit"]["normal_error"]) <= 1e-12,
        reported_qr_normal_rest=error(fit["normal_error"], row["qr_normal_error"]) <= 1e-12,
        native_gradient=error(a.T @ z / 1e-6, data["before_jacobian"][0, cols]) <= 1e-10,
        before_flux=abs(0.5 * float(z @ z) - data["before_values"][0] * 1e-6)
        <= 1e-9 * max(0.5 * float(z @ z), 1e-30),
        reported_before_flux=abs(0.5 * float(z @ z) - row["fit"]["objective_before"])
        <= 1e-9 * max(0.5 * float(z @ z), 1e-30),
        reported_after_flux=abs(phi - row["fit"]["objective_after"]) <= 1e-9 * max(phi, 1e-30),
        native_flux_prediction=abs(data["after_values"][0] * 1e-6 - phi) <= 1e-9 * max(phi, 1e-30),
        geometry_rows=error(data["after_values"][1:], data["before_values"][1:]) <= 1e-12,
    )
    proposed = x.copy()
    proposed[cols] += delta
    checks["after_proposal"] = np.array_equal(proposed, data["after_x"])
    expected_calls.append((proposed, data["B_after"]))
    for i, (point, field) in enumerate(expected_calls, 1):
        checks[f"call_{i}"] = np.array_equal(
            point, data[f"field_request_{i}_x"]
        ) and np.array_equal(field, data[f"field_request_{i}_B"])
    checks["call_keys"] = {k for k in data if k.startswith("field_request_")} == {
        f"field_request_{i}_{part}" for i in range(1, 9) for part in ("x", "B")
    }
    predicted = b0.copy()
    for i in range(3):
        predicted += delta[i] * slopes[i]
    checks["native_B_prediction"] = error(data["B_after"], predicted) <= 1e-12
    after_z = project(data["B_after"], n)
    checks["saved_after_flux"] = abs(0.5 * float(after_z @ after_z) - phi) <= 1e-9 * max(phi, 1e-30)
    reported_flux_error = float(
        abs(data["after_values"][0] * 1e-6 - row["fit"]["objective_after"])
        / max(row["fit"]["objective_after"], 1e-30)
    )
    checks["reported_native_flux_error"] = (
        error(reported_flux_error, row["native_flux_relative_error"]) <= 1e-12
    )
    for key, field in (("before", b0), ("after", data["B_after"])):
        checks[f"mean_B_{key}"] = (
            error(np.mean(np.linalg.norm(field, axis=-1)), row[f"mean_B_{key}"]) <= 1e-12
        )
    expected_work = dict(
        evaluations=2,
        jacobian_evaluations=2,
        B_grid_requests=2,
        B_vjp_requests=2,
        position_requests=32,
        position_derivative_requests=32,
        curvature_requests=8,
        curvature_derivative_requests=8,
        native_metric_requests=24,
        native_gradient_requests=24,
        coil_pair_samples=9600000,
        plasma_pair_samples=6553600,
    )
    checks["work"] = row["work"] == dict(
        direct=expected_work, additional_B_grid_requests=8, svd_fits=1, qr_fits=1
    )
    checks["reported_qualification"] = (
        row["fit"]["status"] == "completed"
        and row["fit"]["qualified"] is True
        and all(row["checks"].values())
    )
    return dict(
        checks={k: bool(v) for k, v in checks.items()},
        all_pass=all(checks.values()),
        rank=rank,
        condition=condition,
        objective_after=phi,
        normal_error=normal_error,
        independent_qr_normal_error=fit["normal_error"],
        audit_work=dict(native_calls=0, singular_value_checks=1, qr_fits=1),
    )
