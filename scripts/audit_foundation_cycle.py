"""Independent bounded-cycle source, mapping, ledger and iteration acceptance."""

import argparse
import json
from pathlib import Path

import numpy as np
from audit_current_start_gn import audit_arm
from current_diagnostic_inputs import checked, reference
from current_gn_inputs import qualified_source
from run_foundation_cycle import CODE as RUN_CODE
from run_foundation_cycle import solver_sources
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/audit_foundation_cycle.py",
    "scripts/audit_current_start_gn.py",
    "scripts/current_gn_inputs.py",
    "src/fusion_baselines/inequality_audit.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
)


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
    expected_protocol = reference(root / "docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md")
    if (
        study["protocol"] != expected_protocol
        or study["code"] != [reference(root / p) for p in RUN_CODE]
        or study["solver_sources"] != solver_sources()
    ):
        raise ValueError("registered foundation code/protocol/solver sources required")
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
        canonical_problem=all(
            study["preparation"][key] == source["preparation"][key]
            for key in (
                "surface",
                "case",
                "thresholds",
                "guarded_search_targets",
                "canonical_total",
            )
        ),
        mapping=study["source_indices_in_target_order"] == permutation.tolist(),
        owners=study["owner_map"] == owners,
        physical_start=all(np.array_equal(actual[k], expected[k]) for k in expected),
        fixed_budget=study["bundle_limit"] == 24,
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
        dict(arm=ref, checks=audit_arm(arm, names, qualified, budget=24))
        for ref, arm in zip(study["arms"], arms, strict=True)
    ]
    for index, (row, arm) in enumerate(zip(rows, arms, strict=True), start=1):
        points = np.asarray(arm["physical_points"])
        row["checks"].update(
            bounded_attempts=17 <= arm["counters"]["attempts"] <= 24,
            actual_post_startup_step=bool(
                points.shape[0] > 16 and np.any(points[16:] != points[0])
            ),
            repeat_identity=arm["repeat"] == index,
        )
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
    checks["producer_qualification"] = (
        study["qualification_pass"] is True
        and bool(study["checks"])
        and all(study["checks"].values())
    )
    checks["repeated_selection"] = arms[0]["best"]["x_sha256"] == arms[1]["best"]["x_sha256"]
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
