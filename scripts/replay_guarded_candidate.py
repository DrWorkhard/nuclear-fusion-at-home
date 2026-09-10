"""Independently reconstruct saved common-vector states and qualify the final gradient."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from simsopt import load

from fusion_baselines.budgeted_oracle import BudgetedOracle
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def spectrum(jacobian):
    singular = np.linalg.svd(jacobian, compute_uv=False)
    return {"singular_values": singular.tolist(),
            "row_norms": np.linalg.norm(jacobian, axis=1).tolist(),
            "effective_rank_relative_1e_10": int(np.sum(singular > 1e-10 * singular[0]))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--map-physical-dofs", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("replay outputs must be new")
    root = Path(__file__).resolve().parents[1]
    summary_path = root / "evidence/guarded-feasibility-v1/summary.json"
    study = json.loads(summary_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed repeat-qualified study required")
    for source in study["code"]:
        checked(source)
    arm_path = checked(study["arms"][0])
    arm = json.loads(arm_path.read_text())
    with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
        best_x, stored_values = arrays["x"].copy(), arrays["values"].copy()
    field_path = checked(arm["best"]["field"])
    document = json.loads(field_path.read_text())
    serialized = load(str(field_path))
    args.raw.mkdir(parents=True)
    ctx, backend, preparation = prepare(root, args.raw, guarded_curvature=True)
    archived_best_x = best_x.copy()
    permutation = np.arange(len(best_x))
    owner_map = {}
    if args.map_physical_dofs:
        source_names = study["preparation"]["degrees_of_freedom"]
        if not np.array_equal(named_serialized_values(document, source_names), best_x):
            raise ValueError("archived named field parameters do not match saved best array")
        for (curve_name, current_name), coil in zip(base_coil_owners(document),
                                                   ctx.Jf.field.coils[:4], strict=True):
            current = coil.current
            while hasattr(current, "current_to_scale"):
                current = current.current_to_scale
            for source, target in ((curve_name, coil.curve.name), (current_name, current.name)):
                if source in owner_map and owner_map[source] != target:
                    raise ValueError("conflicting physical owner mapping")
                owner_map[source] = target
        permutation = dof_permutation(source_names, backend.names, owner_map)
        best_x = archived_best_x[permutation]
    backend.scales *= study["normalization"]["factor"]
    oracle = BudgetedOracle(backend, 8, len(best_x))
    x0 = ctx.Jf.x.copy()
    initial_values, initial_jacobian = oracle.evaluate(x0)
    best_values, best_jacobian = oracle.evaluate(best_x)
    checks = {
        "initial_replay": bool(np.allclose(initial_values, arm["evaluations"][0]["values"],
                                            rtol=1e-10, atol=1e-12)),
        "best_replay": bool(np.allclose(best_values, stored_values, rtol=1e-10, atol=1e-12)),
        "all_sixteen_coils": len(ctx.Jf.field.coils) == len(serialized.coils) == 16,
    }
    if args.map_physical_dofs:
        checks["original_point_hash_after_inverse_map"] = hashlib.sha256(
            x0[np.argsort(permutation)].tobytes()).hexdigest() == arm["evaluations"][0]["x_sha256"]
        checks["archived_best_array_hash"] = hashlib.sha256(
            archived_best_x.tobytes()).hexdigest() == arm["best"]["x_sha256"]
    differences = []
    for expected, actual in zip(ctx.Jf.field.coils, serialized.coils, strict=True):
        differences.append({
            "position_max_abs": float(np.max(np.abs(expected.curve.gamma()-actual.curve.gamma()))),
            "current_abs": abs(float(expected.current.get_value()-actual.current.get_value())),
            "regularization_abs": abs(float(expected.regularization-actual.regularization))})
    checks["serialized_field_matches"] = all(v <= 1e-12 for d in differences for v in d.values())
    direction = np.random.default_rng(44).normal(size=len(best_x))
    direction /= np.linalg.norm(direction)
    direction = direction[permutation]
    exact = best_jacobian @ direction
    gradients = []
    for eps in [1e-4, 1e-5, 1e-6]:
        plus, _ = oracle.evaluate(best_x + eps*direction)
        minus, _ = oracle.evaluate(best_x - eps*direction)
        fd = (plus-minus)/(2*eps)
        gradients.append({"eps": eps, "analytic": exact.tolist(),
            "finite_difference": fd.tolist(), "normalized_errors": (
                np.abs(fd-exact)/np.maximum(1, np.abs(exact))).tolist()})
    checks["best_gradient"] = max(gradients[-1]["normalized_errors"]) <= 1e-6
    with (args.raw / "replayed.npz").open("xb") as stream:
        np.savez_compressed(stream, x0=x0, best_x=best_x, initial_values=initial_values,
            best_values=best_values, initial_jacobian=initial_jacobian, best_jacobian=best_jacobian,
            archived_best_x=archived_best_x, permutation=permutation)
    report = {"schema_version": 1, "repository": git_state(root),
        "protocol": reference(root / "docs/GUARDED_REPLAY_PROTOCOL.md"),
        "remediation_protocol": reference(root / "docs/REPLAY_MAPPING_REMEDIATION.md")
            if args.map_physical_dofs else None,
        "physical_owner_map": owner_map, "source_indices_in_target_order": permutation.tolist(),
        "code": [reference(Path(__file__)),
            reference(root / "src/fusion_baselines/serialized_dofs.py"), *study["code"]],
        "study": reference(summary_path),
        "arm": reference(arm_path), "preparation": preparation, "checks": checks,
        "serialized_field_differences": differences, "gradient_checks": gradients,
        "initial_spectrum": spectrum(initial_jacobian), "best_spectrum": spectrum(best_jacobian),
        "counters": oracle.counters(), "evaluations": oracle.records,
        "arrays": reference(args.raw / "replayed.npz"), "all_pass": all(checks.values()),
        "physical_feasibility_certified": False}
    write_json_atomic(args.output, report)
    print(json.dumps({"all_pass": report["all_pass"], "checks": checks}))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
