"""Recompute direct pilot accounting and candidate selection without physics calls."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.prefix_audit import audit_exact_prefix
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--budget-1024", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    if study["status"] != "completed" or (not args.budget_1024 and not study["qualification_pass"]):
        raise ValueError("completed repeated pilot required")
    records, arms = [], []
    for ref in study["arms"]:
        arm = json.loads(checked(ref).read_text())
        arms.append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
            checks = audit_inequality_arm(
                arm, data["x"], data["values"], expected_limit=1024 if args.budget_1024 else 256
            )
            doc = json.loads(checked(arm["best"]["field"]).read_text())
            checks["named_serialized_parameter_identity"] = bool(
                np.array_equal(
                    data["x"],
                    named_serialized_values(doc, study["preparation"]["degrees_of_freedom"]),
                )
            )
        n = arm["counters"]["attempts"]
        work = arm["work"]
        expected = {
            "evaluations": n,
            "jacobian_evaluations": n,
            "B_grid_requests": n,
            "B_vjp_requests": n,
            "position_requests": 16 * n,
            "position_derivative_requests": 16 * n,
            "curvature_requests": 4 * n,
            "curvature_derivative_requests": 4 * n,
            "native_metric_requests": 12 * n,
            "native_gradient_requests": 12 * n,
            "coil_pair_samples": 4800000 * n,
            "plasma_pair_samples": 3276800 * n,
        }
        checks["logical_work_accounted"] = work == expected
        finest = arm["gradient_checks"][-1]
        exact, actual = np.asarray(finest["analytic"]), np.asarray(finest["finite_difference"])
        errors = np.abs(actual - exact) / np.maximum(1, np.abs(exact))
        checks["independent_gradient_screen"] = bool(
            [r["eps"] for r in arm["gradient_checks"]] == [1e-5, 1e-6, 1e-7, 1e-8]
            and exact.shape == actual.shape == (138,)
            and np.isfinite(errors).all()
            and errors.max() <= 1e-6
            and np.array_equal(errors, finest["normalized_errors"])
        )
        records.append({"arm": ref, "checks": checks, "pass": all(checks.values())})
    repeated = len(arms) == 2 and len(arms[0]["evaluations"]) == len(arms[1]["evaluations"])
    if repeated:
        repeated = all(
            a["x_sha256"] == b["x_sha256"] and a["values"] == b["values"]
            for a, b in zip(arms[0]["evaluations"], arms[1]["evaluations"], strict=True)
        )
        repeated &= all(
            arms[0][k] == arms[1][k] for k in ("counters", "status", "stop_reason", "work")
        )
    prefix_records, old_reference = [], None
    if args.budget_1024:
        old_path = root / "evidence/direct-slsqp-pilot-v1/summary.json"
        old_reference = reference(old_path)
        old_study = json.loads(old_path.read_text())
        if len(old_study["arms"]) != 2 or not old_study["qualification_pass"]:
            raise ValueError("qualified two-arm historical study required")
        for new_arm, old_ref in zip(arms, old_study["arms"], strict=True):
            old_arm = json.loads(checked(old_ref).read_text())
            prefix_records.append(
                audit_exact_prefix(new_arm["evaluations"], old_arm["evaluations"], length=256)
            )
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "study": reference(summary),
        "code": [
            reference(root / p)
            for p in (
                "scripts/audit_direct_slsqp_pilot.py",
                "src/fusion_baselines/inequality_audit.py",
                "src/fusion_baselines/serialized_dofs.py",
                "src/fusion_baselines/prefix_audit.py",
            )
        ],
        "arms": records,
        "repeat_histories_match": repeated,
        "historical_study": old_reference,
        "historical_prefixes": prefix_records,
        "all_pass": bool(
            repeated
            and all(r["pass"] for r in records)
            and all(r["all_pass"] for r in prefix_records)
        ),
        "additional_physics_calls": 0,
        "physical_feasibility_certified": False,
    }
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
