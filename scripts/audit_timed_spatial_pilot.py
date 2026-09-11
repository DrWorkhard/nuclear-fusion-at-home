"""Independent time-budget, shared-prefix and physical-archive audit for all four arms."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.timed_audit import audit_common_prefix, audit_timed_arm


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
    path = root / "evidence/timed-spatial-pilot-v1/summary.json"
    study = json.loads(path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed common-prefix-qualified study required")
    parent = json.loads(checked(study["parent_study"]).read_text())
    checks = {
        "four_arms": len(study["arms"]) == 4,
        "declared_seconds": study["per_arm_seconds"] == 300,
        "normalization": study["normalization"]["factor"] == parent["normalization"]["factor"],
    }
    for key in (
        "thresholds",
        "guarded_search_targets",
        "degrees_of_freedom",
        "scales",
        "constraint_terms",
        "regularizations_preserved",
    ):
        checks["same_" + key] = study["preparation"][key] == parent["preparation"][key]
    records, groups = [], {}
    for ref in study["arms"]:
        arm_path = checked(ref)
        arm = json.loads(arm_path.read_text())
        groups.setdefault(arm["representation"], []).append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
            ac = audit_timed_arm(arm, arrays["x"], arrays["values"])
            archived = json.loads(checked(arm["best"]["field"]).read_text())
            ac["named_archive_identity"] = np.array_equal(
                arrays["x"],
                named_serialized_values(archived, study["preparation"]["degrees_of_freedom"]),
            )
        ev, common, work = (
            arm["evaluations"],
            arm["original_common_evaluations"],
            arm["representation_work"],
        )
        ac["original_common_count"] = len(common) == len(ev) == work["common_bundles"]
        ac["common_merit_identity"] = len(common) == len(ev) and all(
            a["x_sha256"] == b["x_sha256"]
            and np.isclose(a["merit"], b["merit"], rtol=1e-10, atol=0)
            for a, b in zip(ev, common, strict=True)
        )
        spatial = arm["representation"] == "batched"
        active = sum(c["values"][0] != 0 for c in common) if spatial else 0
        ac["coil_contractions"] = work["batched_coil_contractions"] == 16 * active
        ac["geometry_derivative_requests"] = (
            work["batched_geometry_derivative_requests"] == 32 * active
        )
        ac["current_vjp_calls"] = work["batched_current_vjp_calls"] == 16 * active
        ac["no_single_point_vjp_calls"] = work["extra_single_point_VJP_calls"] == 0
        ac["no_single_point_B_calls"] = work["extra_single_point_B_calls"] == 0
        ac["full_grid_field_requests"] = work["extra_full_field_requests"] == (
            len(ev) if spatial else 0
        )
        ac["gradient_identity"] = arm["maximum_gradient_identity_error"] <= 1e-10
        ac["merit_identity"] = arm["maximum_merit_identity_error"] <= 1e-10
        records.append({"arm": reference(arm_path), "checks": ac, "pass": all(ac.values())})
    checks["two_repeats_each"] = set(groups) == {"scalar", "batched"} and all(
        sorted(a["repeat"] for a in group) == [1, 2] for group in groups.values()
    )
    prefixes = {
        name: audit_common_prefix(*sorted(group, key=lambda a: a["repeat"]))
        for name, group in groups.items()
        if len(group) == 2
    }
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "study": reference(path),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/timed_audit.py"),
            reference(root / "src/fusion_baselines/oracle_audit.py"),
            reference(root / "src/fusion_baselines/serialized_dofs.py"),
        ],
        "checks": checks,
        "arms": records,
        "common_prefix_checks": prefixes,
        "all_pass": all(checks.values())
        and all(r["pass"] for r in records)
        and all(p["pass"] for p in prefixes.values()),
        "additional_physics_calls": 0,
        "physical_feasibility_certified": False,
    }
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
