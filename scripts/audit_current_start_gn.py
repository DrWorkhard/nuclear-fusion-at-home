"""Independent frozen-start, complete ledger and GN work/iteration audit."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from current_gn_inputs import qualified_source
from geometric_curvature_inputs import arrays
from run_jac_scaled_study import require_committed

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/audit_current_start_gn.py",
    "scripts/current_gn_inputs.py",
    "src/fusion_baselines/inequality_audit.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
)


def error(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching finite GN audit arrays required")
    return float(np.max(abs(a - b) / np.maximum(1, abs(b))))


def expected_work(n):
    direct = dict(
        evaluations=n,
        jacobian_evaluations=n,
        B_grid_requests=n,
        B_vjp_requests=n,
        position_requests=16 * n,
        position_derivative_requests=16 * n,
        curvature_requests=4 * n,
        curvature_derivative_requests=4 * n,
        native_metric_requests=12 * n,
        native_gradient_requests=12 * n,
        coil_pair_samples=4800000 * n,
        plasma_pair_samples=3276800 * n,
    )
    gn = dict(
        assembly_requests=n,
        assembly_completed=n,
        native_covector_B_requests=n,
        native_covector_B_completed=n,
        batch_coil_integrals_completed=16 * n,
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
            gn[f"batch_{name}_{suffix}"] = 16 * n
    return direct, gn


def audit_arm(arm, names, qualified, *, budget=2048):
    best = arrays(arm["best"]["arrays"])
    checks = audit_inequality_arm(arm, best["x"], best["values"], expected_limit=budget)
    physical = named_serialized_values(json.loads(checked(arm["best"]["field"]).read_text()), names)
    n, points, ledger = (
        arm["counters"]["attempts"],
        np.asarray(arm["physical_points"]),
        arm["evaluations"],
    )
    direct, gn = expected_work(n)
    checks.update(
        physical_best=np.array_equal(physical, best["x"]),
        work=arm["work"] == direct,
        gn_work=arm["gn_work"] == gn,
        no_failed=arm["counters"]["failed_attempts"] == 0,
        complete_points=points.shape == (n, 207),
        coordinate_scale=arm["coordinate_scale"] == 0.01,
        gate_profile=arm["gradient_gate_profile"]
        == "closed_geometry_current_matrix_plus_sixteen_event_replay",
    )
    if points.shape != (n, 207):
        return checks
    checks["all_parameter_hashes"] = all(
        hashlib.sha256(p.astype(np.float64).tobytes()).hexdigest() == r["x_sha256"]
        for p, r in zip(points, ledger, strict=True)
    )
    initial = arrays(arm["initial_arrays"])
    checks["initial_arrays"] = bool(
        np.array_equal(initial["x"], qualified["points"][0])
        and error(initial["values"], qualified["values"][0]) <= 1e-12
        and error(initial["jacobian"], qualified["jacobian"]) <= 1e-12
        and error(initial["hessian"], qualified["hessian"]) <= 1e-10
    )
    checks["all_startup_points"] = np.array_equal(points[:16], qualified["points"])
    checks["startup_jacobian_record"] = (
        error(
            arm["startup"][0]["jacobian_error"], error(initial["jacobian"], qualified["jacobian"])
        )
        <= 1e-12
    )
    checks["startup_hessian_record"] = (
        error(arm["startup"][0]["hessian_error"], error(initial["hessian"], qualified["hessian"]))
        <= 1e-10
    )
    checks["startup_complete"] = len(arm["startup"]) == 16
    for i, r in enumerate(arm["startup"]):
        value_error = error(ledger[i]["values"], qualified["values"][i])
        checks[f"startup_{i}"] = bool(
            r["index"] == i
            and r["all_pass"]
            and value_error <= 1e-12
            and error(value_error, r["values_error"]) <= 1e-12
        )
    required = (
        "field_relative_error",
        "gradient_normalized_error",
        "batch_field_relative_error",
        "projection_normalized_error",
    )
    identities = arm["gn_identity_checks"]
    checks["identities"] = len(identities) == n and all(
        np.isfinite(r[k]) and 0 <= r[k] <= 1e-10 for r in identities for k in required
    )
    checks["uncoupled_errors_retained"] = all(
        np.isfinite(r["uncoupled_gradient_normalized_error"]) for r in identities
    )
    checks["hessian_requests"] = 0 < arm["hessian_requests"] <= arm["counters"]["requests"]
    by_hash = {r["x_sha256"]: r for r in ledger}
    aligned = []
    for r in arm["iterations"]:
        evaluated = by_hash.get(r["physical_x_sha256"])
        if evaluated is None:
            aligned.append(False)
            continue
        values = evaluated["values"]
        margin = min(values[1:])
        aligned.append(
            values[0] == r["objective"]
            and margin == r["minimum_margin"]
            and r["construction_target"] == (values[0] <= 0.008 and margin >= 0)
        )
    checks["iterations_bound"] = bool(aligned) and all(aligned)
    targets = [r["construction_target"] for r in arm["iterations"]]
    if arm["stop_reason"] == "construction_target":
        checks["target_stop"] = bool(
            targets
            and targets[-1]
            and not any(targets[:-1])
            and arm["solver"]["status"] == 3
            and not arm["solver"]["success"]
        )
    else:
        checks["no_unreported_target"] = not any(targets)
    return {key: bool(value) for key, value in checks.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable GN audit path required")
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    source, data, binding = qualified_source(root)
    if (
        study["status"] != "completed"
        or len(study["arms"]) != 2
        or study["qualification"] != binding
        or study["source"] != source
    ):
        raise ValueError("closed two-repeat fixed-source GN study required")
    for ref in [study["protocol"], *study["code"], *study["solver_sources"]]:
        checked(ref)
    for path in (root / p for p in CODE):
        require_committed(root, path)
    doc = json.loads(checked(source["field"]).read_text())
    template = json.loads(checked(study["preparation"]["normalized_start"]).read_text())
    names = study["preparation"]["degrees_of_freedom"]
    _, permutation, owners = mapped_start(doc, template, source["names"], names, data["points"][0])
    matrix = data["native_matrix"][:, permutation]
    qualified = dict(
        points=data["points"][:, permutation],
        values=data["values"],
        jacobian=data["jacobian"][:, permutation],
        hessian=np.einsum("ki,kj->ij", matrix, matrix) / 1e-6,
    )
    expected, actual = (
        serialized_state(doc),
        serialized_state(json.loads(checked(study["physical_start"]).read_text())),
    )
    checks = dict(
        mapping=study["source_indices_in_target_order"] == permutation.tolist(),
        owners=study["owner_map"] == owners,
        physical_start=all(np.array_equal(actual[k], expected[k]) for k in expected),
        fixed_budget=study["bundle_limit"] == 2048,
        scale=study["flux_scale"] == 1e-6,
        tolerance=study["construction_tolerance"] == 1e-8,
        fixed_scipy=study["versions"]["scipy"] == "1.18.1",
        analytic_control=study["analytic_control"]["all_pass"],
        no_admission=study["physical_admission"] is False,
    )
    expected_options = dict(
        gtol=1e-12,
        xtol=1e-12,
        barrier_tol=1e-10,
        initial_tr_radius=0.1,
        initial_constr_penalty=1.0,
        initial_barrier_parameter=1e-3,
        initial_barrier_tolerance=1e-3,
        factorization_method="QRFactorization",
        sparse_jacobian=False,
        maxiter=10000,
        verbose=0,
    )
    checks["fixed_solver_options"] = study["solver_options"] == expected_options
    arms = [json.loads(checked(ref).read_text()) for ref in study["arms"]]
    rows = [
        dict(arm=ref, checks=audit_arm(arm, names, qualified))
        for ref, arm in zip(study["arms"], arms, strict=True)
    ]
    for row in rows:
        row["all_pass"] = all(row["checks"].values())
    for key in (
        "physical_points",
        "counters",
        "work",
        "gn_work",
        "gn_identity_checks",
        "iterations",
        "startup",
    ):
        checks["repeated_" + key] = arms[0][key] == arms[1][key]
    checks["repeat_status"] = (arms[0]["status"], arms[0]["stop_reason"]) == (
        arms[1]["status"],
        arms[1]["stop_reason"],
    )
    checks["repeat_all_values"] = [r["values"] for r in arms[0]["evaluations"]] == [
        r["values"] for r in arms[1]["evaluations"]
    ]
    checks["producer_qualification"] = study["qualification_pass"] == all(study["checks"].values())
    report = dict(
        status="completed",
        study=reference(summary),
        repository=git_state(root),
        code=[reference(root / p) for p in CODE],
        checks=checks,
        arms=rows,
        all_pass=all(checks.values()) and all(r["all_pass"] for r in rows),
        additional_physics_calls=0,
        physical_admission=False,
    )
    write_json_atomic(args.output, report)
    print(json.dumps(dict(all_pass=report["all_pass"])))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
