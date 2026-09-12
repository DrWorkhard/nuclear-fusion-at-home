"""Audit the fixed hybrid construction: named source,2048 ledger and repeat identity."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from audit_direct_slsqp_pilot import checked, reference

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state


def initial_replay_check(arm, expected):
    values = np.asarray(arm["evaluations"][0]["values"])
    error = float(np.max(abs(values - expected) / np.maximum(1, abs(expected))))
    return np.isfinite(error) and error <= 1e-12, error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("immutable new polishing audit required")
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    if study["status"] != "completed" or study["methods"] != ["slsqp"]:
        raise ValueError("completed registered SLSQP construction required")
    source = json.loads(checked(study["source_study"]).read_text())
    source_audit = json.loads(checked(study["source_audit"]).read_text())
    selected = json.loads(checked(study["selected_source"]).read_text())
    qualification = json.loads(checked(source["qualification"]).read_text())
    for ref in [study["protocol"], *study["code"], *study["solver_sources"],
                *qualification["code"], *qualification["installed_sources"]]:
        checked(ref)
    profile = dict(
        protocol=study["protocol"] == reference(
            root / "docs/optimization/SLSQP_POLISH_PROTOCOL.md"),
        source_audit=source_audit["all_pass"] and source_audit["study"] == study["source_study"],
        source_is_first_arm=study["selected_source"] == source["arms"][0],
        fixed_field=selected["best"]["field"]["sha256"] ==
        "6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f",
        fixed_array=selected["best"]["arrays"]["sha256"] ==
        "31dab61fb28d060c9e9f6c21905396cc469dad738c6931928dfe39fa4e250d14",
        options=study["solver_options"] == dict(method="SLSQP", ftol=1e-10, maxiter=100000,
                                                jacobian="analytic", bundle_limit=2048),
        cost=study["source_construction_bundles_per_path"] == 1033
        and study["hybrid_cap_per_path"] == 3081,
        same_physical_problem=all(study["preparation"][k] == source["preparation"][k] for k in
                                 ("surface", "case", "thresholds", "guarded_search_targets",
                                  "canonical_total")),
    )
    source_doc = json.loads(checked(selected["best"]["field"]).read_text())
    initial_doc = json.loads(checked(study["physical_start"]).read_text())
    source_state, initial_state = serialized_state(source_doc), serialized_state(initial_doc)
    profile["complete_physical_state"] = all(np.array_equal(source_state[k], initial_state[k])
                                              for k in source_state)
    named = named_serialized_values(initial_doc, study["preparation"]["degrees_of_freedom"])
    named_hash = hashlib.sha256(named.tobytes()).hexdigest()
    with np.load(checked(selected["best"]["arrays"]), allow_pickle=False) as data:
        expected_values = data["values"].copy()
        original_named = named_serialized_values(source_doc,
                                                 source["preparation"]["degrees_of_freedom"])
        profile["source_array_named"] = np.array_equal(data["x"], original_named)
        permutation = study["source_indices_in_target_order"]
        profile["permutation_bijection"] = sorted(permutation) == list(range(207)) and (
            np.array_equal(named, original_named[permutation]))
    arms, results = [], []
    for ref in study["arms"]:
        arm = json.loads(checked(ref).read_text())
        arms.append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
            checks = audit_inequality_arm(arm, data["x"], data["values"], expected_limit=2048)
            doc = json.loads(checked(arm["best"]["field"]).read_text())
            checks["named_field"] = np.array_equal(data["x"], named_serialized_values(
                doc, study["preparation"]["degrees_of_freedom"]))
        checks["initial_physical_hash"] = arm["evaluations"][0]["x_sha256"] == named_hash
        checks["initial_values"], error = initial_replay_check(arm, expected_values)
        checks["initial_record"] = error == study["initial_replays"][len(arms) - 1]
        n = arm["counters"]["attempts"]
        expected_work = dict(evaluations=n, jacobian_evaluations=n, B_grid_requests=n,
                             B_vjp_requests=n, position_requests=16*n,
                             position_derivative_requests=16*n, curvature_requests=4*n,
                             curvature_derivative_requests=4*n, native_metric_requests=12*n,
                             native_gradient_requests=12*n, coil_pair_samples=4800000*n,
                             plasma_pair_samples=3276800*n)
        checks["all_work"] = arm["work"] == expected_work
        screens = arm["gradient_checks"]
        checks["all_four_directions"] = [r["eps"] for r in screens] == [1e-5, 1e-6, 1e-7, 1e-8]
        for i, screen in enumerate(screens):
            exact, fd = np.asarray(screen["analytic"]), np.asarray(screen["finite_difference"])
            errors = abs(fd - exact) / np.maximum(1, abs(exact))
            # Ledger contains the actual plus/minus values of all nine startup bundles.
            plus, minus = [np.asarray(arm["evaluations"][j]["values"]) for j in (1+2*i, 2+2*i)]
            checks[f"direction_{i}"] = bool(exact.shape == fd.shape == (138,)
                and np.array_equal(fd, (plus - minus) / (2 * screen["eps"]))
                and np.isfinite(errors).all()
                and np.array_equal(errors, screen["normalized_errors"])
                and (i != 3 or errors.max() <= 1e-6))
        checks = {k: bool(v) for k, v in checks.items()}
        results.append(dict(arm=ref, checks=checks, all_pass=all(checks.values())))
    repeated = len(arms) == 2 and len(arms[0]["evaluations"]) == len(arms[1]["evaluations"])
    if repeated:
        a, b = arms
        repeated = all(x["x_sha256"] == y["x_sha256"] and x["values"] == y["values"]
                       for x, y in zip(a["evaluations"], b["evaluations"], strict=True)) and all(
                           a[k] == b[k] for k in ("counters", "status", "stop_reason", "work"))
    profile = {k: bool(v) for k, v in profile.items()}
    result = dict(repository=git_state(root), study=reference(summary),
                  code=reference(Path(__file__)), profile=profile, arms=results,
                  repeated=bool(repeated), additional_physics_calls=0,
                  physical_feasibility_certified=False,
                  all_pass=bool(repeated and all(profile.values()) and all(
                      r["all_pass"] for r in results)))
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
