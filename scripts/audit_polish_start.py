"""Independent real-chain-rule and serialized-geometry audit of the fixed start check."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.clearance_chain_rule import chain_rule_rows, loop_positions
from fusion_baselines.coil_coefficient_view import base_arrays, serialized_physical_coefficients
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("source binding mismatch")
    return path


def errors(actual, expected):
    return abs(np.asarray(actual) - expected) / np.maximum(1, abs(np.asarray(expected)))


def verify_arrays(data, source_doc, report, arm):
    shapes = dict(x=(207,), values=(138,), jacobian=(138, 207), directions=(2, 207),
                  coefficients=(16, 3, 17), dcoefficients=(2, 16, 3, 17), anchors=(120,),
                  real=(120,), native_positions=(16, 200, 3), scale=())
    if any(data[k].shape != shape or not np.isfinite(data[k]).all() for k, shape in shapes.items()):
        raise ValueError("complete finite registered arrays required")
    x, jac = data["x"], data["jacobian"]
    names = report["source_names"]
    checks = dict(named_source=np.array_equal(x, named_serialized_values(source_doc, names)),
                  scale=float(data["scale"]) == report["preparation"]["thresholds"]["a0"],
                  original_failed=arm["gradient_screen_pass"] is False
                  and report["original_all_row_fd_pass"] is False)
    coefficients = serialized_physical_coefficients(source_doc, base_arrays(source_doc, names, x))
    checks["serialized_coefficients"] = bool(
        errors(coefficients, data["coefficients"]).max() <= 1e-14)
    directions = []
    for k, seed in enumerate((46, 47)):
        vector = np.random.default_rng(seed).normal(size=207)
        vector /= np.linalg.norm(vector)
        checks[f"seed_{seed}"] = np.array_equal(vector, data["directions"][k])
        direction = serialized_physical_coefficients(
            source_doc, base_arrays(source_doc, names, vector, direction=True))
        directions.append(direction)
        checks[f"serialized_direction_{seed}"] = bool(
            errors(direction, data["dcoefficients"][k]).max() <= 1e-14)
    own, derivative, anchor = chain_rule_rows(coefficients, directions, float(data["scale"]))
    source_error = float(errors(data["values"], arm["evaluations"][0]["values"]).max())
    deriv_error = float(errors(jac @ data["directions"][0], arm["gradient_checks"][0][
        "analytic"]).max())
    checks["source_values"] = source_error == report["initial_replay_error"] <= 1e-12
    checks["source_directional"] = deriv_error == report["derivative_replay_error"] <= 1e-12
    value_error = float(errors(own, data["values"][6:126]).max())
    complex_value_error = float(errors(own, data["real"]).max())
    checks["independent_values"] = value_error <= 1e-10 and complex_value_error <= 1e-10
    checks["anchors"] = bool(errors(anchor, data["anchors"]).max() <= 1e-12)
    points = loop_positions(coefficients)
    position_error = float(errors(points, data["native_positions"]).max())
    checks["positions"] = position_error <= 1e-12
    checks["reported_real_errors"] = np.array_equal(errors(data["real"], data["values"][6:126]),
                                                    report["real_errors"])
    nonpair = np.asarray(arm["gradient_checks"][-1]["normalized_errors"])
    nonpair_max = float(np.r_[nonpair[:6], nonpair[126:]].max())
    checks["original_nonpair"] = nonpair_max == report["original_nonpair_maximum_error"] <= 1e-6
    currents = [i for i, n in enumerate(names) if n.split(":", 1)[0].startswith("Current")]
    checks["current_columns"] = len(currents) == 3 and np.all(jac[6:126, currents] == 0)
    if [d["seed"] for d in report["directions"]] != [46, 47]:
        raise ValueError("both fixed source directions required")
    rows = []
    for k, d in enumerate(report["directions"]):
        expected = jac @ data["directions"][k]
        checks[f"analytic_{k}"] = np.array_equal(expected, d["analytic"])
        if [s["h"] for s in d["steps"]] != [1e-12, 1e-20, 1e-28]:
            raise ValueError("all three complex steps required")
        error = float(errors(derivative[k], expected[6:126]).max())
        cross = []
        for i, step in enumerate(d["steps"]):
            computed = np.asarray(step["derivative"])
            err = errors(computed, expected[6:126])
            stable = errors(computed, d["steps"][0]["derivative"])
            checks[f"step_{k}_{i}_arithmetic"] = bool(
                computed.shape == (120,) and np.isfinite(computed).all()
                and np.array_equal(err, step["errors"])
                and np.array_equal(stable, step["stability"])
                and step["passed"] == bool(err.max() <= 1e-9 and stable.max() <= 1e-10))
            cross.append(float(errors(derivative[k], computed).max()))
        checks[f"independent_derivative_{k}"] = error <= 1e-9 and max(cross) <= 1e-10
        rows.append(dict(seed=d["seed"], real_chain_native_error=error,
                         real_chain_complex_errors=cross))
    checks["qualification_all_checks"] = report["all_pass"] == all(report["checks"].values())
    checks["required_producer_checks"] = set(report["checks"]) == {
        "initial_values", "real_values", "physical_positions", "current_columns",
        "original_nonpair_fd", "same_problem", "original_analytic_replay", "complex_directions"}
    # Do not confuse a consistent negative report with a qualified derivative state.
    checks["producer_is_qualified"] = report["all_pass"] is True
    return {k: bool(v) for k, v in checks.items()}, dict(
        native_value_error=value_error, complex_value_error=complex_value_error,
        independent_position_error=position_error, directions=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable independent audit required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.source.read_text())
    if report["status"] != "completed":
        raise ValueError("complete qualification required")
    for ref in [report["protocol"], *report["code"], *report["qualified_backend_code"],
                *report["installed_sources"]]:
        checked(ref)
    failed = json.loads(checked(report["failed_study"]).read_text())
    arm = json.loads(checked(report["failed_arm"]).read_text())
    postmortem = json.loads(checked(report["failure_audit"]).read_text())
    doc = json.loads(checked(report["source_field"]).read_text())
    with np.load(checked(report["arrays"]), allow_pickle=False) as data:
        checks, results = verify_arrays(data, doc, report, arm)
    checks["bound_postmortem"] = postmortem["all_pass"] and postmortem["study"] == report[
        "failed_study"] and postmortem["arm"] == report["failed_arm"]
    checks["fixed_source"] = report["source_field"] == failed["physical_start"] and (
        report["source_field"]["sha256"] ==
        "65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb")
    checks["same_names"] = report["source_names"] == failed["preparation"]["degrees_of_freedom"]
    checks["same_problem"] = all(report["preparation"][k] == failed["preparation"][k] for k in
                                ("surface", "case", "thresholds", "guarded_search_targets",
                                 "canonical_total"))
    checks["native_work"] = report["work"] == dict(
        evaluations=1, jacobian_evaluations=1, B_grid_requests=1, B_vjp_requests=1,
        position_requests=16, position_derivative_requests=16, curvature_requests=4,
        curvature_derivative_requests=4, native_metric_requests=12, native_gradient_requests=12,
        coil_pair_samples=4800000, plasma_pair_samples=3276800)
    checks["extra_work"] = report["extra_work"] == dict(
        native_position_requests=16, pair_value_evaluations=7, squared_distance_samples=33600000)
    result = dict(repository=git_state(root), source=reference(args.source),
                  code=[reference(root / p) for p in (
                      "scripts/audit_polish_start.py",
                      "src/fusion_baselines/clearance_chain_rule.py",
                      "src/fusion_baselines/coil_coefficient_view.py",
                      "src/fusion_baselines/serialized_dofs.py")],
                  checks=checks, results=results, all_pass=all(checks.values()),
                  new_native_calls=0, complex_value_calls=0,
                  own_work=dict(real_pair_sets=120, squared_distance_samples=4800000,
                                directional_distance_samples=9600000),
                  physical_feasibility_certified=False)
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
