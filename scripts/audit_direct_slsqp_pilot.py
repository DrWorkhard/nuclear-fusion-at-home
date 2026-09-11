"""Recompute direct pilot accounting and candidate selection without physics calls."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.inequality_audit import audit_inequality_arm
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
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed repeated pilot required")
    records, arms = [], []
    for ref in study["arms"]:
        arm = json.loads(checked(ref).read_text())
        arms.append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
            checks = audit_inequality_arm(arm, data["x"], data["values"])
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
        records.append({"arm": ref, "checks": checks, "pass": all(checks.values())})
    repeated = len(arms) == 2 and len(arms[0]["evaluations"]) == len(arms[1]["evaluations"])
    if repeated:
        repeated = all(
            a["x_sha256"] == b["x_sha256"] and a["values"] == b["values"]
            for a, b in zip(arms[0]["evaluations"], arms[1]["evaluations"], strict=True)
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
            )
        ],
        "arms": records,
        "repeat_histories_match": repeated,
        "all_pass": repeated and all(r["pass"] for r in records),
        "additional_physics_calls": 0,
        "physical_feasibility_certified": False,
    }
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
