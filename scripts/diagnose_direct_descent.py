"""Frozen replay, derivative screen and bounded linear-model probes, not a new search."""

import argparse
import importlib
import inspect
import json
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from scipy.optimize import linprog
from simsopt import load
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.linear_descent import assess_step, linear_model
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input/code hash mismatch: {path}")
    return path


def discrepancy(a, b):
    return np.abs(np.asarray(a) - b) / np.maximum(1.0, np.abs(b))


def solve_model(values, jacobian, radius, scale):
    c, a, b = linear_model(values, jacobian, scale)
    solution = linprog(
        c,
        A_ub=a,
        b_ub=b,
        bounds=[(-radius, radius)] * len(c),
        method="highs-ds",
        options={
            "presolve": True,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
            "time_limit": 30.0,
        },
    )
    record = {
        "radius": radius,
        "success": bool(solution.success),
        "status": int(solution.status),
        "message": str(solution.message),
        "nit": int(solution.nit),
    }
    if solution.success:
        record.update(
            assess_step(values, jacobian, scale, solution.x, radius),
            solver_objective=float(solution.fun),
            step=solution.x.tolist(),
        )
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new diagnostic outputs required")
    root = Path(__file__).resolve().parents[1]
    summary_path = root / "evidence/direct-slsqp-pilot-v1/summary.json"
    study = json.loads(summary_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed repeated source study required")
    for ref in study["qualified_backend_code"]:
        checked(ref)
    arm_path = checked(study["arms"][0])
    arm = json.loads(arm_path.read_text())
    field_path = checked(arm["best"]["field"])
    doc = json.loads(field_path.read_text())
    stored_field = load(str(field_path))
    report = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(root / "docs/optimization/DIRECT_DESCENT_DIAGNOSTIC_PROTOCOL.md"),
        "study": reference(summary_path),
        "arm": reference(arm_path),
        "status": "running",
        "checks": {},
        "states": [],
        "models": [],
        "nonlinear_design_search_performed": False,
        "code": [
            reference(root / p)
            for p in (
                "scripts/diagnose_direct_descent.py",
                "src/fusion_baselines/linear_descent.py",
            )
        ],
        "qualified_backend_code": study["qualified_backend_code"],
        "solver_sources": [
            reference(Path(inspect.getfile(importlib.import_module(name))))
            for name in (
                "scipy.optimize._linprog_highs",
                "scipy.optimize._highspy._highs_wrapper",
                "scipy.optimize._highspy._core",
            )
        ],
    }
    args.raw.mkdir(parents=True)
    try:
        control = solve_model(np.array([0.0, -1.0]), np.array([[-1.0, 2.0], [1.0, 1.0]]), 1.0, 1.0)
        report["analytic_control"] = control
        report["checks"]["analytic_lp_control"] = bool(
            control["success"]
            and control["primal_pass"]
            and np.allclose(control["step"], [1, 0], rtol=0, atol=1e-10)
        )
        if not report["checks"]["analytic_lp_control"]:
            raise ValueError("linear solver analytic control failed")
        ctx, _, preparation = prepare(root, args.raw, guarded_curvature=True)
        if preparation["thresholds"] != study["preparation"]["thresholds"]:
            raise ValueError("physical setup changed")
        report["preparation"] = preparation
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(preparation["surface"])), range="full torus", nphi=64, ntheta=64
        )
        backend = DirectConstraintBackend(ctx, full, flux_scale=1e-6)
        source_names = study["preparation"]["degrees_of_freedom"]
        owners = {}
        for (curve, leaves), coil in zip(
            base_coil_owners(doc), backend.field.coils[:4], strict=True
        ):
            pairs = [(curve, coil.curve.name)]
            for attributes, owner in leaves:
                current = coil.current
                for attribute in attributes:
                    current = getattr(current, attribute)
                pairs.append((owner, current.name))
            for source, target in pairs:
                if source in owners and owners[source] != target:
                    raise ValueError("conflicting physical owner")
                owners[source] = target
        permutation = dof_permutation(source_names, backend.names, owners)
        original = ctx.Jf.x.copy()
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as saved:
            archived = saved["x"].copy()
            expected_best = saved["values"].copy()
        if not np.array_equal(archived, named_serialized_values(doc, source_names)):
            raise ValueError("source array/field identity mismatch")
        states = []
        for name, x, expected in (
            ("original", original, arm["evaluations"][0]["values"]),
            ("selected119", archived[permutation], expected_best),
        ):
            values, jacobian, metrics = backend.evaluate(x)
            checks = {"source_vector_replay": float(discrepancy(values, expected).max()) <= 1e-10}
            current_indices = [i for i, n in enumerate(backend.names) if n.startswith("Current")]
            currents = {
                "free_parameter_names": [backend.names[i] for i in current_indices],
                "free_parameters": x[current_indices].tolist(),
                "unique_physical_currents_A": [
                    float(c.current.get_value()) for c in backend.field.coils[:4]
                ],
                "flux_gradient_current_block_norm": float(
                    np.linalg.norm(jacobian[0, current_indices])
                ),
                "flux_gradient_geometry_block_norm": float(
                    np.linalg.norm(np.delete(jacobian[0], current_indices))
                ),
            }
            if name == "selected119":
                checks["serialized_field_identity"] = all(
                    np.array_equal(a.curve.gamma(), b.curve.gamma())
                    and a.current.get_value() == b.current.get_value()
                    and a.regularization == b.regularization
                    for a, b in zip(backend.field.coils, stored_field.coils, strict=True)
                )
            path = args.raw / f"{name}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, x=x, values=values, jacobian=jacobian)
            report["states"].append(
                {
                    "name": name,
                    "metrics": metrics,
                    "checks": checks,
                    "currents": currents,
                    "arrays": reference(path),
                }
            )
            states.append((name, x.copy(), values, jacobian))
        report["source_indices_in_target_order"] = permutation.tolist()
        report["checks"]["both_replays"] = all(all(s["checks"].values()) for s in report["states"])
        _, x, values, jacobian = states[1]
        direction = np.random.default_rng(47).normal(size=len(x))
        direction /= np.linalg.norm(direction)
        direction = direction[permutation]
        exact, screens = jacobian @ direction, []
        for eps in (1e-5, 1e-6, 1e-7, 1e-8):
            plus = backend.evaluate(x + eps * direction, derivatives=False)[0]
            minus = backend.evaluate(x - eps * direction, derivatives=False)[0]
            fd = (plus - minus) / (2 * eps)
            err = discrepancy(fd, exact)
            screens.append(
                {
                    "eps": eps,
                    "finite_difference": fd.tolist(),
                    "analytic": exact.tolist(),
                    "normalized_errors": err.tolist(),
                    "maximum_error": float(err.max()),
                }
            )
        report["selected_directional_checks"] = screens
        report["checks"]["selected_gradient"] = screens[-1]["maximum_error"] <= 1e-6
        if all(report["checks"].values()):
            for name, x, values, jacobian in states:
                for index, radius in enumerate((1e-4, 1e-3, 1e-2)):
                    model = {"state": name, **solve_model(values, jacobian, radius, 0.01)}
                    if model["success"] and model["primal_pass"]:
                        proposed = x + 0.01 * np.asarray(model["step"])
                        actual, _, metrics = backend.evaluate(proposed, derivatives=False)
                        path = args.raw / f"{name}-probe-{index}.npz"
                        with path.open("xb") as stream:
                            np.savez_compressed(stream, x=proposed, values=actual)
                        model.update(
                            actual_values=actual.tolist(),
                            metrics=metrics,
                            actual_objective_change=float(actual[0] - values[0]),
                            arrays=reference(path),
                            maximum_model_discrepancy=float(
                                discrepancy(actual, np.asarray(model["linear_values"])).max()
                            ),
                        )
                    report["models"].append(model)
                    print(
                        name,
                        radius,
                        model["status"],
                        model.get("actual_objective_change"),
                        flush=True,
                    )
                    write_json_atomic(args.output, report)
        report["checks"]["successful_model_primals"] = all(
            not model["success"] or model["primal_pass"] for model in report["models"]
        )
        report.update(
            status="completed", work=backend.work, qualification_pass=all(report["checks"].values())
        )
    except Exception as error:
        report.update(
            status="error", qualification_pass=False, error=f"{type(error).__name__}: {error}"
        )
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
