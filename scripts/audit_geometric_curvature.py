"""Independent scalar predictions and native-matrix spectra; no new field calls."""

import argparse
import json
from math import fsum, sqrt
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_curvature_inputs import arrays, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_current_affine import current_map

CODE = (
    "scripts/audit_geometric_curvature.py",
    "scripts/geometric_curvature_inputs.py",
    "scripts/geometric_descent_inputs.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_current_affine.py",
)


def dot(a, b):
    return fsum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def product(matrix, vector):
    return np.array([dot(row, vector) for row in matrix])


def deviation(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching finite independent audit arrays required")
    return max(
        abs(float(x) - float(y)) / max(1, abs(float(y)))
        for x, y in zip(a.flat, b.flat, strict=True)
    )


def native_work():
    counts = dict(
        grid_B_requests=16,
        grid_B_completed=16,
        local_B_requests=1024,
        local_B_completed=1024,
        local_VJP_requests=1024,
        local_VJP_completed=1024,
        batch_assembly_requests=1,
        batch_assembly_completed=1,
        batch_coil_integrals_completed=16,
    )
    for name in (
        "position",
        "tangent",
        "position_derivative",
        "tangent_derivative",
        "current_value",
        "current_VJP",
    ):
        for suffix in ("requests", "completed"):
            counts[f"batch_{name}_{suffix}"] = 16
    return counts


def model(z, matrix, step, actual):
    tangent = product(matrix, step)
    linear_z = z + tangent
    rest = actual - linear_z
    baseline, after = dot(z, z) / 2e-6, dot(actual, actual) / 2e-6
    change, curvature = dot(z, tangent) / 1e-6, dot(tangent, tangent) / 2e-6
    quadratic = baseline + change + curvature
    direct = dot(linear_z, linear_z) / 2e-6
    linear_error, quadratic_error = abs(after - baseline - change), abs(after - direct)
    result = dict(
        baseline=baseline,
        actual=after,
        actual_change=after - baseline,
        linear_change=change,
        gn_curvature_term=curvature,
        quadratic_change=direct - baseline,
        linear_absolute_error=linear_error,
        quadratic_absolute_error=quadratic_error,
        quadratic_to_linear_error_ratio=quadratic_error / max(linear_error, 1e-300),
        field_linearization_remainder_norm=sqrt(dot(rest, rest)),
        matrix_identity_error=abs(direct - quadratic) / max(1, abs(direct)),
        remainder_identity_error=abs(
            after - direct - (dot(linear_z, rest) + dot(rest, rest) / 2) / 1e-6
        )
        / max(1, abs(after)),
    )
    result["correct_change_sign"] = bool(np.sign(after - baseline) == np.sign(direct - baseline))
    result["usefulness_pass"] = (
        result["correct_change_sign"] and quadratic_error <= 0.1 * linear_error
    )
    return result


def spectral_projection(z, matrix, columns, steps, reported):
    geometry = [i for i in range(matrix.shape[1]) if i not in set(columns)]
    a, dg = matrix[:, columns], matrix[:, geometry]
    q, r = np.linalg.qr(a, mode="reduced")
    # Independent summation for all projection components, not the producer's contractions.
    qtg = np.array([[dot(q[:, i], dg[:, j]) for j in range(len(geometry))] for i in range(3)])
    projected = dg - np.array(
        [[dot(q[i], qtg[:, j]) for j in range(len(geometry))] for i in range(len(z))]
    )
    spectra = {}
    checks = dict(
        current_columns=reported["current_columns"] == columns.tolist(),
        geometry_columns=reported["geometry_columns"] == geometry,
        orthogonality=deviation(q.T @ q, np.eye(3)) <= 1e-12,
        projected_geometry=deviation(projected, reported["projected_geometry"]) <= 1e-10,
        work=reported["work"] == dict(svd_calls=4, qr_calls=1, step_projections=3),
        current_projection=reported["current_projection_qualified"],
    )
    reported_q, reported_r = np.asarray(reported["Q"]), np.asarray(reported["R"])
    checks["reported_Q_orthogonal"] = deviation(reported_q.T @ reported_q, np.eye(3)) <= 1e-12
    checks["reported_QR_factorization"] = deviation(reported_q @ reported_r, a) <= 1e-10
    checks["reported_orthogonality_error"] = (
        deviation(
            reported["orthogonality_error"], np.max(abs(reported_q.T @ reported_q - np.eye(3)))
        )
        <= 1e-12
    )
    for key, block in dict(
        full=matrix / 1e-3, geometry=dg / 1e-3, current=a, projected_geometry=projected / 1e-3
    ).items():
        singular = np.linalg.svd(block, compute_uv=False)
        rank = int(sum(singular > 1e-12 * singular[0]))
        condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else None
        old = reported["spectra"][key]
        comparison = float(
            np.max(abs(singular - np.asarray(old["singular_values"])))
            / max(1, old["singular_values"][0])
        )
        spectra[key] = dict(
            singular_values=singular.tolist(),
            rank=rank,
            condition=condition,
            normalized_spectrum_error=comparison,
            producer_rank=old["rank"],
            producer_condition=old["condition"],
        )
        checks[key + "_spectrum"] = comparison <= 1e-10
        old_s = np.asarray(old["singular_values"])
        checks[key + "_producer_rank"] = old["rank"] == int(sum(old_s > 1e-12 * old_s[0]))
        checks[key + "_producer_condition"] = (
            old["condition"] is None
            if old_s[-1] == 0
            else deviation(old["condition"], old_s[0] / old_s[-1]) <= 1e-12
        )
    checks["current_rank_condition"] = (
        spectra["current"]["rank"] == 3 and spectra["current"]["condition"] <= 1e10
    )
    projections = []
    for i, step in enumerate(steps):
        tangent = product(matrix, step)
        component = product(q.T, tangent)
        linear = z + tangent
        residual = linear - product(q, product(q.T, linear))
        energy = dot(tangent, tangent)
        fraction = dot(component, component) / energy if energy > 0 else None
        result = dict(
            current_tangent_energy_fraction=fraction,
            projected_linear_residual_norm=sqrt(dot(residual, residual)),
            projected_linear_raw_flux=dot(residual, residual) / 2,
        )
        old = reported["projections"][i]
        for key, value in result.items():
            checks[f"step_{i}_{key}"] = (
                old[key] is None if value is None else deviation(value, old[key]) <= 1e-10
            )
        checks[f"step_{i}_tangent"] = deviation(tangent, old["tangent"]) <= 1e-10
        checks[f"step_{i}_projected"] = deviation(residual, old["projected_residual"]) <= 1e-10
        checks[f"step_{i}_reported_components"] = (
            deviation(product(reported_q.T, tangent), old["current_components"]) <= 1e-10
        )
        projections.append(result)
    return dict(
        checks=checks,
        spectra=spectra,
        projections=projections,
        work=dict(svd_calls=4, qr_calls=1, step_projections=3),
    )


def audit_case(row, source, frozen):
    data = arrays(row["inputs"])
    doc = json.loads(checked(source["field"]).read_text())
    template = json.loads(checked(row["preparation"]["normalized_start"]).read_text())
    _, permutation, owners = mapped_start(
        doc, template, source["names"], row["names"], frozen["points"][0]
    )
    columns = current_map(template, row["names"])["columns"]
    batch, local_data = arrays(row["batch_arrays"]), arrays(row["local_arrays"])
    local = local_data["D"]
    if local.shape != (1024, 207) or batch["D"].shape != local.shape:
        raise ValueError("full1024-by207 field matrices required")
    checks = dict(
        source=row["source"] == source,
        mapping=row["source_indices_in_target_order"] == permutation.tolist(),
        owners=row["owner_map"] == owners,
        points=np.array_equal(data["points"], frozen["points"][:, permutation]),
        steps=np.array_equal(data["steps"], frozen["steps"][:, permutation]),
        directions=np.array_equal(data["directions"], frozen["directions"][:, permutation]),
        gradients=np.array_equal(data["gradient"], frozen["gradient"][permutation]),
        currents=np.array_equal(columns, data["columns"]),
        affine_source=np.array_equal(data["A"], frozen["A"]),
        stored_fluxes=np.array_equal(data["fluxes"], frozen["fluxes"]),
        rounded_displacements=np.array_equal(
            data["rounded_displacements"], data["points"][[5, 10, 15]] - data["points"][0]
        ),
        native_work=row["work"] == native_work(),
        restored=row["observation_points_restored"],
        restored_array=np.array_equal(
            local_data["observation_points_after"], data["observation_points"]
        ),
        batch_matrix=deviation(batch["D"], local) <= 1e-10,
    )
    source_grid = arrays(source["arrays"])
    checks["observation_points"] = np.array_equal(data["observation_points"], source_grid["points"])
    checks["normal"] = np.array_equal(data["normal"], source_grid["normal"])
    n = data["normal"].reshape(-1, 3)
    weights = np.array([v / sqrt(1024 * sqrt(dot(v, v))) for v in n])
    checks["weights"] = deviation(data["weights"], weights) <= 1e-12
    if len(row["events"]) != 16 or len(row["trials"]) != 3:
        raise ValueError("all sixteen field events and three model predictions required")
    residuals = []
    for i, event in enumerate(row["events"]):
        field, z = arrays(event["field_arrays"]), arrays(event["residual_arrays"])["z"]
        projected = np.array(
            [dot(b, w) for b, w in zip(field["B"].reshape(-1, 3), weights, strict=True)]
        )
        raw = dot(z, z) / 2
        replay_error = abs(raw - frozen["fluxes"][i]) / abs(frozen["fluxes"][i])
        checks[f"event_{i}"] = bool(
            event["index"] == i
            and event["kind"] == frozen["kinds"][i]
            and event["source_bundle"] == frozen["bundles"][i]
            and event["status"] == "completed"
            and np.array_equal(field["x"], data["points"][i])
            and np.array_equal(event["x"], field["x"])
            and deviation(projected, z) <= 1e-12
            and replay_error <= 1e-10
            and deviation(event["raw_flux"], raw) <= 1e-12
            and abs(event["flux_replay_error"] - replay_error) <= 1e-12
            and event["all_pass"]
        )
        residuals.append(z)
    z = residuals[0]
    checks.update(
        projection=deviation(batch["z"], z) <= 1e-10,
        native_covector=deviation(product(local.T, z) / 1e-6, data["gradient"]) <= 1e-10,
        current_matrix=deviation(local[:, columns], data["A"]) <= 1e-12,
    )
    independent_errors = dict(
        matrix=deviation(batch["D"], local),
        projection=deviation(batch["z"], z),
        gradient=deviation(product(batch["D"].T, z) / 1e-6, data["gradient"]),
        uncoupled_gradient=deviation(product(batch["D"].T, batch["z"]) / 1e-6, data["gradient"]),
        current=deviation(batch["D"][:, columns], data["A"]),
        batch_flux=abs(dot(batch["z"], batch["z"]) / 2 - frozen["fluxes"][0])
        / abs(frozen["fluxes"][0]),
    )
    for key, value in independent_errors.items():
        checks["reported_error_" + key] = deviation(value, row["errors"][key]) <= 1e-10
        if key != "uncoupled_gradient":
            expected = bool(value <= (1e-12 if key == "current" else 1e-10))
            checks["reported_gate_" + key] = row["checks"][key] == expected
    trials = []
    for i in range(3):
        result = model(z, local, data["steps"][i], residuals[5 + 5 * i])
        fd = [
            deviation(
                (residuals[1 + 5 * i + 2 * j] - residuals[2 + 5 * i + 2 * j]) / (2 * eps),
                product(local, data["directions"][i]),
            )
            for j, eps in enumerate((1e-7, 1e-8))
        ]
        for key, value in result.items():
            old = row["trials"][i]["model"][key]
            checks[f"model_{i}_{key}"] = (
                old == value if isinstance(value, bool) else deviation(value, old) <= 1e-10
            )
        checks[f"model_{i}_fd"] = (
            max(fd) <= 1e-6 and deviation(fd, row["trials"][i]["fd_errors"]) <= 1e-10
        )
        checks[f"model_{i}_identities"] = (
            max(result["matrix_identity_error"], result["remainder_identity_error"]) <= 1e-10
        )
        trials.append(dict(model=result, fd_errors=fd))
    spectral = spectral_projection(z, local, columns, data["steps"], row["conditioning"])
    checks["spectral"] = all(spectral["checks"].values())
    useful = all(t["model"]["usefulness_pass"] for t in trials)
    checks["usefulness_classification"] = row["usefulness_pass"] == useful
    checks["producer_qualification"] = row["all_pass"] == all(row["checks"].values())
    return dict(
        checks=checks,
        errors={key: float(value) for key, value in independent_errors.items()},
        all_pass=all(checks.values()),
        trials=trials,
        conditioning=spectral,
        usefulness_pass=useful,
        native_requests=0,
        lp_calls=0,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit path required")
    root = Path(__file__).resolve().parents[1]
    study = json.loads(args.study.read_text())
    selected, frozen, bindings = sources(root)
    if (
        study["status"] != "completed"
        or len(study["cases"]) != 2
        or study["prerequisites"] != bindings
    ):
        raise ValueError("complete source-bound32-event curvature study required")
    for ref in [study["protocol"], *study["code"], *study["installed"]["sources"]]:
        checked(ref)
    for path in (root / p for p in CODE):
        require_committed(root, path)
    rows = [
        audit_case(row, source, data)
        for row, source, data in zip(study["cases"], selected, frozen, strict=True)
    ]
    checks = dict(
        no_physical_admission=study["physical_admission"] is False,
        qualification=study["all_pass"] == all(r["all_pass"] for r in study["cases"]),
        usefulness=study["usefulness_pass"] == all(r["usefulness_pass"] for r in rows),
    )
    report = dict(
        status="completed",
        source=reference(args.study),
        repository=git_state(root),
        code=[reference(root / p) for p in CODE],
        cases=rows,
        checks=checks,
        all_pass=all(checks.values()) and all(r["all_pass"] for r in rows),
        physical_admission=False,
        native_requests=0,
        lp_calls=0,
    )
    write_json_atomic(args.output, report)
    print(json.dumps(dict(all_pass=report["all_pass"])))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
