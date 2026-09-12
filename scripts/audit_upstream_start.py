"""Independent stored-source, current, field-scaling and derivative arithmetic audit."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.current_normalization import fixed_serialized_total
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state
from fusion_baselines.start_qualification_audit import audit_directions


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"qualification reference changed: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("qualification", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    record = json.loads(args.qualification.read_text())
    for ref in [record["protocol"], *record["code"], *record["installed_sources"]]:
        checked(ref)
    prep = record["preparation"]
    source = serialized_state(json.loads(checked(prep["source"]).read_text()))
    new_doc = json.loads(checked(prep["normalized_start"]).read_text())
    new = serialized_state(new_doc)
    total = fixed_serialized_total(json.loads(checked(prep["canonical_fixture"]).read_text()))
    factor = total / float(np.sum(source["currents"][:4]))
    expected_currents = factor * source["currents"]
    current_error = float(np.max(abs(new["currents"] - expected_currents) /
                                 np.maximum(1, abs(expected_currents))))
    old = json.loads((root / "evidence/natural-auglag-jac-v1/summary.json").read_text())
    checks = dict(
        completed=record["status"] == "completed" and record["all_pass"] is True,
        no_search=record["optimization_performed"] is False,
        fixed_protocol=record["protocol"] == reference(
            root / "docs/optimization/UPSTREAM_START_PROTOCOL.md"),
        fixed_source=prep["source"]["sha256"] ==
        "40c3abd2c172fdfc94be6a2b5de05ef2e29c3f37c8b4fbd04c6fdb47eef69b4a",
        fixed_total=total == 1250075.624635464 == fixed_serialized_total(new_doc),
        common_scale=factor == prep["current_factor"] and current_error <= 1e-12,
        exact_coefficients=np.array_equal(new["coefficients"], source["coefficients"]),
        exact_regularizations=np.array_equal(
            new["base_regularizations"], source["base_regularizations"]),
        canonical_problem=all(prep[k] == old["preparation"][k] for k in
                              ("surface", "case", "thresholds", "guarded_search_targets")),
        native_metrics=all(np.isfinite(v) and 0 <= v <= 1e-10
                           for v in record["native_errors"].values()),
        execution_checks=all(record["checks"].values()),
        complete_work=record["spatial_assemblies"] == 9 and
        record["work"]["evaluations"] == record["work"]["jacobian_evaluations"] == 9,
    )
    with np.load(checked(record["field_arrays"]), allow_pickle=False) as field:
        with np.load(checked(prep["source_field_probe"]), allow_pickle=False) as old_field:
            checks["original_field_probes"] = (
                np.array_equal(field["points"], old_field["points"])
                and np.array_equal(field["source_B"], old_field["native"]))
        expected = factor * field["source_B"]
        field_error = float(np.max(np.linalg.norm(field["normalized_B"] - expected, axis=1) /
                                   np.maximum(1, np.linalg.norm(expected, axis=1))))
        checks["field_scaling"] = field_error <= 1e-12
        checks["field_error_record"] = field_error == record["field_scale_error"]
    with np.load(checked(record["arrays"]), allow_pickle=False) as data:
        checks.update(audit_directions(data["jacobian"], data["direction"],
                                       record["finite_differences"]))
        checks["named_state"] = np.array_equal(
            data["x"], named_serialized_values(new_doc, prep["degrees_of_freedom"]))
        checks["flux_residual_identity"] = abs(
            data["z"] @ data["z"] / 2e-6 - data["values"][0]) <= 1e-10
        gradient = data["dz"].T @ data["z"] / 1e-6
        checks["native_gradient_identity"] = float(np.max(abs(gradient - data["jacobian"][0]) /
                                                        np.maximum(1, abs(gradient)))) <= 1e-10
        checks["directional_record"] = np.array_equal(
            data["jacobian"] @ data["direction"], record["analytic_directional"])
    checks["all_nine_coupled_guards"] = len(record["gn_identities"]) == 9 and all(
        np.isfinite(r[k]) and 0 <= r[k] <= 1e-10 for r in record["gn_identities"] for k in
        ("field_relative_error", "gradient_normalized_error", "batch_field_relative_error",
         "projection_normalized_error"))
    checks = {k: bool(v) for k, v in checks.items()}
    result = dict(
        repository=git_state(root), source=reference(args.qualification), checks=checks,
        all_pass=all(checks.values()), current_error=current_error, field_error=field_error,
        new_physical_calls=0, physical_feasibility_certified=False,
        code=[reference(root / p) for p in (
            "scripts/audit_upstream_start.py", "src/fusion_baselines/start_qualification_audit.py",
            "src/fusion_baselines/serialized_field_state.py",
            "src/fusion_baselines/current_normalization.py",
            "src/fusion_baselines/serialized_dofs.py")],
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
