"""Independent fixed-start, composite-gate and complete two-arm construction audit."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from audit_polish_start import checked, reference

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state


def error(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching finite arrays required")
    return float(np.max(abs(a-b) / np.maximum(1, abs(b))))


def audit_start(arm, data, qdata, permutation, original):
    p = np.asarray(permutation)
    if (p.shape != (207,) or not np.issubdtype(p.dtype, np.integer)
            or sorted(p.tolist()) != list(range(207)) or len(arm["evaluations"]) < 9):
        raise ValueError("complete mapping and startup required")
    expected = dict(x=qdata["x"][p], values=qdata["values"], jacobian=qdata["jacobian"][:, p])
    initial = {}
    for k in expected:
        err = error(data[k], expected[k])
        initial[k+"_error"] = err
        initial[k+"_pass"] = bool(np.array_equal(data[k], expected[k]) if k == "x"
                                  else err <= 1e-12)
    checks = dict(reference=initial == arm["initial_reference"]
                  and all(initial[k+"_pass"] for k in expected),
                  direction=np.array_equal(data["direction"], qdata["directions"][0, p]),
                  first_values=np.array_equal(data["values"], arm["evaluations"][0]["values"]),
                  fixed_gate_profile=arm["gradient_gate_profile"] ==
                  "qualified_pairs_plus_original_nonpair_fd")
    # Build all source and target points separately, then check both saved hash lists.
    original_points, target_points = [qdata["x"]], [data["x"]]
    for h in (1e-5, 1e-6, 1e-7, 1e-8):
        original_points.extend((qdata["x"]+h*qdata["directions"][0],
                                qdata["x"]-h*qdata["directions"][0]))
        target_points.extend((data["x"]+h*data["direction"], data["x"]-h*data["direction"]))
    replay = []
    for i, (src, target) in enumerate(zip(original_points, target_points, strict=True)):
        current, old = arm["evaluations"][i], original["evaluations"][i]
        err = error(current["values"], old["values"])
        replay.append(dict(target_hash=hashlib.sha256(target.tobytes()).hexdigest()
                            == current["x_sha256"],
                           source_hash=hashlib.sha256(src.tobytes()).hexdigest() == old["x_sha256"],
                           value_error=err, values_pass=err <= 1e-12))
    checks["nine_bundle_replay"] = replay == arm["startup_replay"] and all(
        r["target_hash"] and r["source_hash"] and r["values_pass"] for r in replay)
    checks["four_steps"] = [r["eps"] for r in arm["gradient_checks"]] == [1e-5, 1e-6, 1e-7, 1e-8]
    exact = data["jacobian"] @ data["direction"]
    for k, s in enumerate(arm["gradient_checks"]):
        plus, minus = [np.asarray(arm["evaluations"][i]["values"]) for i in (1+2*k, 2+2*k)]
        fd = (plus-minus)/(2*s["eps"])
        e = abs(fd-exact) / np.maximum(1, abs(exact))
        checks[f"fd_{k}"] = bool(exact.shape == (138,) and np.isfinite(e).all()
                                  and np.array_equal(exact, s["analytic"])
                                  and np.array_equal(fd, s["finite_difference"])
                                  and np.array_equal(e, s["normalized_errors"]))
    e = np.asarray(arm["gradient_checks"][-1]["normalized_errors"])
    nonpair = float(np.concatenate((e[:6], e[126:])).max())
    checks["explicit_old_fd"] = arm["original_all_row_fd_pass"] == bool(e.max() <= 1e-6) and (
        arm["original_all_row_fd_maximum"] == float(e.max()))
    checks["unchanged_nonpair_gate"] = arm["nonpair_fd_maximum"] == nonpair <= 1e-6
    checks["qualified_gate"] = arm["gradient_screen_pass"] is True and all(checks.values())
    return {k: bool(v) for k, v in checks.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable composite audit required")
    root = Path(__file__).resolve().parents[1]
    sp = args.study / "summary.json"
    study = json.loads(sp.read_text())
    if study["status"] != "completed" or len(study["arms"]) != 2:
        raise ValueError("complete two-arm composite study required")
    q = json.loads(checked(study["qualification"]).read_text())
    qa = json.loads(checked(study["qualification_audit"]).read_text())
    original = json.loads(checked(study["failed_arm"]).read_text())
    failed = json.loads(checked(study["failed_study"]).read_text())
    for ref in [study["protocol"], *study["code"], *study["solver_sources"], *q["code"],
                *q["qualified_backend_code"], *q["installed_sources"], *qa["code"],
                study["source_study"], study["source_audit"], study["source_holdouts"]]:
        checked(ref)
    doc = json.loads(checked(study["physical_start"]).read_text())
    actual = serialized_state(doc)
    expected = serialized_state(json.loads(checked(q["source_field"]).read_text()))
    profile = dict(qualification=q["all_pass"] and qa["all_pass"]
                    and qa["source"] == study["qualification"],
                   protocol=study["protocol"] == reference(
                       root / "docs/optimization/SLSQP_COMPOSITE_PROTOCOL.md"),
                   same_physical_start=all(np.array_equal(actual[k], expected[k]) for k in actual),
                   same_problem=all(study["preparation"][k] == failed["preparation"][k] for k in
                                    ("surface", "case", "thresholds", "guarded_search_targets",
                                     "canonical_total")),
                   bound_failure=study["failed_arm"] == q["failed_arm"]
                   and study["failed_study"] == q["failed_study"],
                   source_cost=study["source_construction_bundles_per_path"] == 1033
                   and study["nominal_hybrid_cap_per_path"] == 3081,
                   solver_options=study["solver_options"] == dict(
                       method="SLSQP", ftol=1e-10, maxiter=100000,
                       jacobian="analytic", bundle_limit=2048))
    profile["fixed_source"] = q["source_field"]["sha256"] == (
        "65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb") and (
        q["arrays"]["sha256"] ==
        "9ee89d4ca82a9d104b8d5bf5e2b814bd12962cdcd1f4bc0385099527879250ad")
    profile["diagnostic_cost"] = study["prior_diagnostic_work"] == dict(
        failed_startup_bundles=9, additional_native_qualification_bundles=1,
        native_position_requests=16, complex_pair_value_evaluations=7,
        complex_squared_distance_samples=33600000, audit_squared_distance_samples=4800000,
        audit_directional_distance_samples=9600000)
    arms, results = [], []
    with np.load(checked(q["arrays"]), allow_pickle=False) as qdata:
        for ref in study["arms"]:
            arm = json.loads(checked(ref).read_text())
            arms.append(arm)
            with np.load(checked(arm["initial_arrays"]), allow_pickle=False) as initial:
                checks = audit_start(arm, initial, qdata, study["source_indices_in_target_order"],
                                     original)
                checks["named_start"] = np.array_equal(initial["x"], named_serialized_values(
                    doc, study["preparation"]["degrees_of_freedom"]))
            with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
                checks.update(audit_inequality_arm(arm, data["x"], data["values"],
                                                   expected_limit=2048))
                best_doc = json.loads(checked(arm["best"]["field"]).read_text())
                checks["named_best"] = np.array_equal(data["x"], named_serialized_values(
                    best_doc, study["preparation"]["degrees_of_freedom"]))
            n = arm["counters"]["attempts"]
            checks["all_work"] = arm["work"] == dict(
                evaluations=n, jacobian_evaluations=n, B_grid_requests=n, B_vjp_requests=n,
                position_requests=16*n, position_derivative_requests=16*n, curvature_requests=4*n,
                curvature_derivative_requests=4*n, native_metric_requests=12*n,
                native_gradient_requests=12*n, coil_pair_samples=4800000*n,
                plasma_pair_samples=3276800*n)
            checks["coordinate_scale"] = arm["coordinate_scale"] == 0.01
            checks = {k: bool(v) for k, v in checks.items()}
            results.append(dict(arm=ref, checks=checks, all_pass=all(checks.values())))
    a, b = arms
    repeat = len(a["evaluations"]) == len(b["evaluations"]) and all(
        u["x_sha256"] == v["x_sha256"] and u["values"] == v["values"]
        for u, v in zip(a["evaluations"], b["evaluations"], strict=True)) and all(
            a[k] == b[k] for k in ("counters", "work", "status", "stop_reason"))
    profile["qualification_summary"] = study["qualification_pass"] is True and all(
        study["checks"].values())
    result = dict(repository=git_state(root), study=reference(sp),
                  code=[reference(Path(__file__)), reference(
                      root / "src/fusion_baselines/inequality_audit.py")],
                  profile=profile, arms=results, repeated=bool(repeat),
                  all_pass=bool(repeat and all(profile.values()) and all(r["all_pass"]
                                                                        for r in results)),
                  additional_physics_calls=0, physical_feasibility_certified=False)
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
