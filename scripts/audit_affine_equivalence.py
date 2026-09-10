"""Post-run audit: physical problem identity and immutable oracle accounting."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked_path(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    old_path = root / "evidence/normalized-feasibility-v1/summary.json"
    new_path = root / "evidence/affine-feasibility-v1/summary.json"
    old, new = (json.loads(path.read_text()) for path in (old_path, new_path))
    if any(d["status"] != "completed" or not d["qualification_pass"] for d in (old, new)):
        raise ValueError("require completed repeat-qualified studies")
    checks = {key: old["preparation"][key] == new["preparation"][key] for key in (
        "degrees_of_freedom", "thresholds", "scales", "constraint_terms",
        "regularizations_preserved", "promotion_relative_B_difference")}
    for key in ("surface", "case"):
        checks[key] = (old["preparation"][key]["sha256"]
                       == new["preparation"][key]["sha256"])
        checked_path(new["preparation"][key])
    for key in ("initial_norm", "factor", "normalized_scales"):
        checks["normalization_" + key] = old["normalization"][key] == new["normalization"][key]
    checks["physical_source_parent"] = (old["preparation"]["source"]["sha256"]
                                        == new["preparation"]["source_parent_sha256"])
    fixture = checked_path(new["preparation"]["source"]).read_bytes()
    checks["fixture_transformation"] = (fixture.endswith(b"\n") and
        hashlib.sha256(fixture[:-1]).hexdigest() == new["preparation"]["source_parent_sha256"])
    arms = []
    for record in new["arms"]:
        path = checked_path(record)
        arm = json.loads(path.read_text())
        prior_record = next(r for r in old["arms"] if Path(r["path"]).name == path.name)
        prior = json.loads(checked_path(prior_record).read_text())
        evaluations = arm["evaluations"]
        counter = arm["counters"]
        ac = {
            "same_seven_physical_probes": len(evaluations) >= 7 and all(
                a["x_sha256"] == b["x_sha256"] and a["values"] == b["values"]
                for a, b in zip(evaluations[:7], prior["evaluations"][:7], strict=True)),
            "exact_proposal_count": counter["attempts"] == len(evaluations),
            "contiguous_attempts": [e["attempt"] for e in evaluations]
                == list(range(1, len(evaluations) + 1)),
            "request_partition": counter["requests"] == counter["attempts"]
                + counter["cache_hits"] + counter["denied"],
            "within_cap": counter["attempts"] <= counter["limit"] == 1500,
            "no_failed_evaluation": counter["failed_attempts"] == 0
                and all(e["status"] == "completed" for e in evaluations),
            "fixed_coordinate_scale": arm["coordinate_map"]["scale"] == 0.01,
            "physical_coordinates_recorded": arm["coordinate_map"][
                "oracle_records_physical_coordinates"],
            "budget_stop_is_exact": arm["status"] != "budget_exhausted" or (
                counter["attempts"] == counter["limit"] and counter["denied"] == 1),
        }
        best = min(evaluations, key=lambda e: e["merit"])
        ac["best_selection"] = all(arm["best"][k] == best[k]
                                   for k in ("attempt", "merit", "x_sha256"))
        with np.load(checked_path(arm["best"]["arrays"])) as arrays:
            ac["best_physical_array_hash"] = (
                hashlib.sha256(arrays["x"].tobytes()).hexdigest() == best["x_sha256"])
            ac["best_values"] = np.array_equal(arrays["values"], best["values"])
            ac["best_merit"] = float(arrays["values"] @ arrays["values"] / 2) == best["merit"]
        checked_path(arm["best"]["field"])
        arms.append({"arm": reference(path), "checks": ac,
                     "best_origin": "physical_gradient_probe" if best["attempt"] <= 7
                     else "solver_proposal", "pass": all(ac.values())})
    result = {"schema_version": 1, "repository": git_state(root),
              "code": reference(Path(__file__)), "old_study": reference(old_path),
              "new_study": reference(new_path), "physical_problem_checks": checks,
              "arms": arms, "all_pass": all(checks.values()) and all(a["pass"] for a in arms),
              "limits": "No new physics calls; this audit does not establish feasibility."}
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
