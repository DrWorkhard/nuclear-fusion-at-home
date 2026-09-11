"""Independent scalar-problem, proposal-budget and extra-derivative work audit."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.oracle_audit import audit_ledger
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    path = root / "evidence/spatial-trf-pilot-v1/summary.json"
    study = json.loads(path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed repeat-qualified pilot required")
    parent = json.loads(checked(study["parent_study"]).read_text())
    old_arm = json.loads(checked(parent["arms"][0]).read_text())
    checks = {
        "four_arms": len(study["arms"]) == 4,
        "normalization": study["normalization"]["factor"] == parent["normalization"]["factor"],
        "unequal_work_disclosed": study["equal_computational_work"] is False,
    }
    for key in (
        "thresholds",
        "guarded_search_targets",
        "degrees_of_freedom",
        "scales",
        "regularizations_preserved",
        "constraint_terms",
    ):
        checks["same_" + key] = study["preparation"][key] == parent["preparation"][key]
    records = []
    for ref in study["arms"]:
        arm_path = checked(ref)
        arm = json.loads(arm_path.read_text())
        field_path = checked(arm["best"]["field"])
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
            ac = {
                k: bool(v) for k, v in audit_ledger(arm, arrays["x"], arrays["values"], 128).items()
            }
            ac["archived_named_field_identity"] = np.array_equal(
                arrays["x"],
                named_serialized_values(
                    json.loads(field_path.read_text()), study["preparation"]["degrees_of_freedom"]
                ),
            )
        ev, common, work = (
            arm["evaluations"],
            arm["original_common_evaluations"],
            (arm["representation_work"]),
        )
        spatial = arm["representation"] == "spatial"
        ac["common_work_count"] = len(common) == len(ev) == work["common_bundles"]
        ac["common_scalar_merit"] = len(common) == len(ev) and all(
            a["x_sha256"] == b["x_sha256"]
            and np.isclose(a["merit"], b["merit"], rtol=1e-10, atol=0)
            for a, b in zip(ev, common, strict=True)
        )
        expected = 1024 * sum(c["values"][0] != 0 for c in common) if spatial else 0
        ac["point_B_count"] = work["extra_single_point_B_calls"] == expected
        ac["point_VJP_count"] = work["extra_single_point_VJP_calls"] == expected
        ac["full_field_count"] = work["extra_full_field_requests"] == (
            len(common) if spatial else 0
        )
        ac["merit_identity"] = arm["maximum_merit_identity_error"] <= 1e-10
        ac["gradient_identity"] = arm["maximum_gradient_identity_error"] <= 1e-10
        if not spatial:
            ac["parent_scalar_prefix"] = all(
                a["x_sha256"] == b["x_sha256"] and a["values"] == b["values"]
                for a, b in zip(ev, old_arm["evaluations"][: len(ev)], strict=True)
            )
        records.append({"arm": reference(arm_path), "checks": ac, "pass": all(ac.values())})
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "study": reference(path),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/oracle_audit.py"),
            reference(root / "src/fusion_baselines/serialized_dofs.py"),
        ],
        "checks": checks,
        "arms": records,
        "all_pass": all(checks.values()) and all(a["pass"] for a in records),
        "additional_physics_calls": 0,
        "physical_feasibility_certified": False,
    }
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
