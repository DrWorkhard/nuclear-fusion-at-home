"""Postmortem only: verify the nine saved startup bundles, never admit the failed study."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from run_direct_slsqp_pilot import checked, reference

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state


def startup_checks(arm, x, labels):
    if len(arm["evaluations"]) != 9 or len(arm["gradient_checks"]) != 4 or len(labels) != 138:
        raise ValueError("exact nine-bundle, four-direction failed startup required")
    direction = np.random.default_rng(46).normal(size=len(x))
    direction /= np.linalg.norm(direction)
    vectors = [x]
    for h in (1e-5, 1e-6, 1e-7, 1e-8):
        vectors.extend((x + h * direction, x - h * direction))
    checks = dict(
        physical_startup_hashes=all(hashlib.sha256(v.tobytes()).hexdigest() == r["x_sha256"]
                                    for v, r in zip(vectors, arm["evaluations"], strict=True)),
        exact_steps=[s["eps"] for s in arm["gradient_checks"]] == [1e-5, 1e-6, 1e-7, 1e-8],
        failed_before_solver=arm["status"] == "error" and arm["stop_reason"] == "error"
        and arm["error"] == "ValueError: initial physical gradient screen failed"
        and "solver" not in arm and arm["gradient_screen_pass"] is False,
    )
    rows = []
    for k, screen in enumerate(arm["gradient_checks"]):
        exact = np.asarray(screen["analytic"])
        plus, minus = (np.asarray(arm["evaluations"][j]["values"]) for j in (1+2*k, 2+2*k))
        fd = (plus - minus) / (2 * screen["eps"])
        error = abs(fd - exact) / np.maximum(1, abs(exact))
        checks[f"step_{k}_arithmetic"] = bool(
            exact.shape == (138,) and np.isfinite(error).all()
            and np.array_equal(fd, screen["finite_difference"])
            and np.array_equal(error, screen["normalized_errors"])
            and np.array_equal(exact, arm["gradient_checks"][0]["analytic"]))
        rows.append(dict(eps=screen["eps"], maximum_error=float(error.max()),
                         worst_label=labels[int(np.argmax(error))],
                         failing_rows=[labels[i] for i in np.flatnonzero(error > 1e-6)],
                         nonpair_maximum_error=float(np.r_[error[:6], error[126:]].max())))
    checks["failed_gate_confirmed"] = rows[-1]["maximum_error"] > 1e-6
    return checks, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable postmortem required")
    root = Path(__file__).resolve().parents[1]
    summary, arm_path = args.study / "summary.json", args.study / "slsqp-1.json"
    study, arm = (json.loads(p.read_text()) for p in (summary, arm_path))
    if (study["status"] != "error" or study["qualification_pass"] is not False
            or study["arms"] or (args.study / "slsqp-2.json").exists()):
        raise ValueError("preserved failed first startup and absent second arm required")
    source = json.loads(checked(study["source_study"]).read_text())
    selected = json.loads(checked(study["selected_source"]).read_text())
    source_audit = json.loads(checked(study["source_audit"]).read_text())
    qualification = json.loads(checked(source["qualification"]).read_text())
    for ref in [study["protocol"], *study["code"], *study["solver_sources"],
                *qualification["code"], *qualification["installed_sources"],
                study["closed_qi"], study["closed_qi_audit"], study["source_holdouts"]]:
        checked(ref)
    doc = json.loads(checked(study["physical_start"]).read_text())
    source_doc = json.loads(checked(selected["best"]["field"]).read_text())
    names = study["preparation"]["degrees_of_freedom"]
    x = named_serialized_values(doc, names)
    checks, screens = startup_checks(arm, x, study["labels"])
    current, original = serialized_state(doc), serialized_state(source_doc)
    checks["complete_physical_state"] = all(np.array_equal(current[k], original[k])
                                             for k in current)
    checks["source_is_selected_first_arm"] = study["selected_source"] == source["arms"][0]
    checks["source_audit"] = source_audit["all_pass"] and source_audit["study"] == study[
        "source_study"]
    with np.load(checked(selected["best"]["arrays"]), allow_pickle=False) as saved:
        source_named = named_serialized_values(source_doc,
                                               source["preparation"]["degrees_of_freedom"])
        permutation = study["source_indices_in_target_order"]
        checks["named_source_permutation"] = np.array_equal(saved["x"], source_named) and (
            sorted(permutation) == list(range(207))
            and np.array_equal(x, source_named[permutation]))
        replay = float(np.max(abs(np.asarray(arm["evaluations"][0]["values"]) - saved["values"])
                              / np.maximum(1, abs(saved["values"]))))
    checks["initial_values"] = np.isfinite(replay) and replay <= 1e-12
    with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as saved:
        ledger = audit_inequality_arm(arm, saved["x"], saved["values"], expected_limit=2048)
        best_doc = json.loads(checked(arm["best"]["field"]).read_text())
        checks["named_saved_best"] = np.array_equal(saved["x"], named_serialized_values(
            best_doc, names))
    # Keep the ordinary study gate failed. This different predicate verifies a postmortem.
    checks["ordinary_admission_remains_failed"] = sorted(k for k, v in ledger.items() if not v) == [
        "correct_stop", "gradient_screen"]
    checks["exact_startup_counters"] = arm["counters"] == dict(
        attempts=9, cache_hits=0, denied=0, failed_attempts=0, limit=2048, requests=9)
    checks["all_work"] = arm["work"] == dict(
        evaluations=9, jacobian_evaluations=9, B_grid_requests=9, B_vjp_requests=9,
        position_requests=144, position_derivative_requests=144, curvature_requests=36,
        curvature_derivative_requests=36, native_metric_requests=108, native_gradient_requests=108,
        coil_pair_samples=43200000, plasma_pair_samples=29491200)
    checks = {k: bool(v) for k, v in checks.items()}
    result = dict(repository=git_state(root), study=reference(summary), arm=reference(arm_path),
                  code=[reference(Path(__file__)), reference(
                      root / "src/fusion_baselines/inequality_audit.py")],
                  checks=checks, ordinary_ledger_checks=ledger, screens=screens,
                  initial_replay_error=replay, all_pass=all(checks.values()),
                  construction_qualified=False, solver_started=False, second_repeat_started=False,
                  additional_physics_calls=0, physical_feasibility_certified=False)
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"], "construction_qualified": False}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
