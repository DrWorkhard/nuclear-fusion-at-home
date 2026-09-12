"""Qualify/replay a raw-flux GN model on all four frozen diagnostic probes."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import time
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from simsopt import load
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.local_field_jacobian import local_field_jacobian
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.quadratic_flux_model import quadratic_flux_model
from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)
from fusion_baselines.spatial_flux import spatial_flux


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input/code hash mismatch: {path}")
    return path


def discrepancy(actual, expected):
    return float(np.max(np.abs(actual - expected) / np.maximum(1, np.abs(expected))))


def matrix_error(actual, expected):
    return float(np.max(np.abs(actual - expected)) / max(1, np.max(np.abs(expected))))


def save_arrays(path, **arrays):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return reference(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable diagnostic paths required")
    root = Path(__file__).resolve().parents[1]
    prior_path = root / "evidence/direct-descent-diagnostic-v2-composite.json"
    prior = json.loads(prior_path.read_text())
    batch_path = root / "evidence/spatial-flux-batched-v1-retry1.json"
    batch = json.loads(batch_path.read_text())
    if not prior["qualification_pass"] or not batch["all_pass"]:
        raise ValueError("passing source qualifications required")
    for ref in prior["qualified_backend_code"] + batch["code"] + batch["installed_sources"]:
        checked(ref)
    study = json.loads(checked(prior["study"]).read_text())
    arm = json.loads(checked(prior["arm"]).read_text())
    field_path = checked(arm["best"]["field"])
    document = json.loads(field_path.read_text())
    serialized = load(str(field_path))  # Intentionally change runtime owner numbering.
    report = {
        "schema_version": 1,
        "repository": git_state(root), "host": host_state(),
        "protocol": reference(root / "docs/optimization/QUADRATIC_FIELD_MODEL_PROTOCOL.md"),
        "source_diagnostic": reference(prior_path),
        "prior_batched_qualification": reference(batch_path),
        "status": "running", "qualification_pass": False,
        "optimization_performed": False, "checks": {}, "states": [], "probes": [],
        "versions": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "simsopt")},
        "thread_environment": {n: os.environ.get(n) for n in (
            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
        "qualified_backend_code": prior["qualified_backend_code"],
        "code": [reference(root / p) for p in (
            "scripts/diagnose_quadratic_field_model.py",
            "src/fusion_baselines/quadratic_flux_model.py",
            "src/fusion_baselines/batched_field_jacobian.py",
            "src/fusion_baselines/local_field_jacobian.py")],
        "additional_work": dict.fromkeys((
            "full_grid_B_requests", "local_point_B_requests", "local_point_VJP_requests",
            "batched_coil_contractions", "batched_geometry_derivative_requests",
            "batched_current_VJP_requests"), 0),
    }
    args.raw.mkdir(parents=True)
    started = time.monotonic()
    try:
        ctx, _, preparation = prepare(root, args.raw, guarded_curvature=True)
        if preparation["thresholds"] != prior["preparation"]["thresholds"]:
            raise ValueError("physical thresholds changed")
        report["preparation"] = preparation
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(preparation["surface"])), range="full torus", nphi=64, ntheta=64)
        backend = DirectConstraintBackend(ctx, full, flux_scale=1e-6)
        source_names = study["preparation"]["degrees_of_freedom"]
        owners = {}
        for (curve, leaves), coil in zip(
            base_coil_owners(document), backend.field.coils[:4], strict=True
        ):
            pairs = [(curve, coil.curve.name)]
            for attributes, owner in leaves:
                current = coil.current
                for attribute in attributes:
                    current = getattr(current, attribute)
                pairs.append((owner, current.name))
            for source, target in pairs:
                if source in owners and owners[source] != target:
                    raise ValueError("conflicting shared owner")
                owners[source] = target
        permutation = dof_permutation(source_names, backend.names, owners)
        old_inverse = np.argsort(prior["source_indices_in_target_order"])
        from_old = old_inverse[permutation]
        report["source_indices_in_target_order"] = permutation.tolist()
        report["physical_owner_map"] = owners
        original = ctx.Jf.x.copy()
        original_sha = hashlib.sha256(original[np.argsort(permutation)].tobytes()).hexdigest()
        if original_sha != arm["evaluations"][0]["x_sha256"]:
            raise ValueError("original physical state hash mismatch")
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
            if not np.array_equal(data["x"], named_serialized_values(document, source_names)):
                raise ValueError("selected serialized/array identity mismatch")

        def native_z(x):
            ctx.Jf.x = x.copy()
            backend.field.set_points(backend.points)
            report["additional_work"]["full_grid_B_requests"] += 1
            return spatial_flux(backend.field.B().reshape(backend.normal.shape), backend.normal)

        states = {}
        for previous in prior["states"]:
            name = previous["name"]
            if name not in ("original", "selected119") or name in states:
                raise ValueError("unexpected or duplicate source state")
            with np.load(checked(previous["arrays"]), allow_pickle=False) as old:
                x = old["x"][from_old].copy()
                expected = old["values"].copy()
                expected_jac = old["jacobian"][:, from_old].copy()
            if name == "original" and not np.array_equal(x, original):
                raise ValueError("source original state mismatch")
            values, jacobian, _ = backend.evaluate(x)
            identity = name == "original" or all(
                np.array_equal(a.curve.gamma(), b.curve.gamma())
                and a.current.get_value() == b.current.get_value()
                and a.regularization == b.regularization
                for a, b in zip(backend.field.coils, serialized.coils, strict=True))
            z = native_z(x)
            before_points = backend.field.get_points_cart_ref().copy()
            start = time.monotonic()
            batch_z, dz = batched_field_jacobian(
                backend.field, ctx.Jf, backend.points, backend.weights)
            batch_seconds = time.monotonic() - start
            report["additional_work"]["batched_coil_contractions"] += 16
            report["additional_work"]["batched_geometry_derivative_requests"] += 32
            report["additional_work"]["batched_current_VJP_requests"] += 16
            unchanged = np.array_equal(before_points, backend.field.get_points_cart_ref())
            start = time.monotonic()
            local_dz = local_field_jacobian(
                backend.field, ctx.Jf, backend.points, backend.weights)
            local_seconds = time.monotonic() - start
            report["additional_work"]["local_point_B_requests"] += len(z)
            report["additional_work"]["local_point_VJP_requests"] += len(z)
            unchanged &= np.array_equal(before_points, backend.field.get_points_cart_ref())
            errors = {
                "value_replay": discrepancy(values, expected),
                "jacobian_replay": discrepancy(jacobian, expected_jac),
                "projection": matrix_error(batch_z, z),
                "matrix_vs_native": matrix_error(dz, local_dz),
                "raw_flux_relative": abs(z @ z / (2e-6) - values[0]) / abs(values[0]),
                "batch_flux_relative": abs(batch_z @ batch_z - z @ z) / (z @ z),
                "scaled_flux_gradient": discrepancy(dz.T @ z / 1e-6, jacobian[0]),
            }
            screens, directions, plus_z, minus_z = [], [], [], []
            for seed in (49, 50):
                direction = np.random.default_rng(seed).normal(size=len(x))
                direction /= np.linalg.norm(direction)
                direction = direction[permutation]
                exact = dz @ direction
                plus, minus, steps = [], [], []
                for h in (1e-4, 1e-5, 1e-6):
                    zp, zm = native_z(x + h*direction), native_z(x - h*direction)
                    plus.append(zp)
                    minus.append(zm)
                    steps.append({"h": h, "maximum_normalized_error":
                                  discrepancy((zp-zm)/(2*h), exact)})
                screens.append({"seed": seed, "steps": steps})
                directions.append(direction)
                plus_z.append(plus)
                minus_z.append(minus)
            checks = {key: bool(value <= 1e-10) for key, value in errors.items()}
            checks.update(
                serialized_identity=bool(identity), field_points_unchanged=bool(unchanged),
                finest_directions=all(s["steps"][-1]["maximum_normalized_error"] <= 1e-6
                                      for s in screens))
            arrays = save_arrays(
                args.raw / f"{name}.npz", x=x, values=values, jacobian=jacobian,
                z=z, dz=dz, local_dz=local_dz, directions=directions,
                plus_z=plus_z, minus_z=minus_z)
            report["states"].append({
                "name": name, "source_arrays": previous["arrays"], "arrays": arrays,
                "errors": errors, "checks": checks, "directional_checks": screens,
                "batched_seconds": batch_seconds, "local_vjp_seconds": local_seconds})
            states[name] = (x, z, dz, values)
            print(name, "qualification", all(checks.values()), errors, flush=True)
            write_json_atomic(args.output, report)
        report["checks"]["both_state_qualifications"] = bool(
            set(states) == {"original", "selected119"}
            and all(all(s["checks"].values()) for s in report["states"]))
        if report["checks"]["both_state_qualifications"]:
            for index, model in enumerate(prior["models"]):
                if not model["success"]:
                    if "arrays" in model:
                        raise ValueError("infeasible source model has a probe")
                    continue
                if not model["primal_pass"]:
                    raise ValueError("source primal failure")
                x, z, dz, values = states[model["state"]]
                with np.load(checked(model["arrays"]), allow_pickle=False) as old:
                    proposed = old["x"][from_old].copy()
                    expected = old["values"].copy()
                if not np.array_equal(proposed, x + 0.01*np.asarray(model["step"])[from_old]):
                    raise ValueError("frozen physical step identity failed")
                actual, _, _ = backend.evaluate(proposed, derivatives=False)
                actual_z = native_z(proposed)
                prediction = quadratic_flux_model(z, dz, proposed-x, actual_z)
                checks = {
                    "source_values": discrepancy(actual, expected) <= 1e-10,
                    "projected_raw_flux": abs(prediction["actual"]-actual[0])
                    / abs(actual[0]) <= 1e-10,
                    "linear_prediction_replay": abs(
                        prediction["linear_change"] - model["predicted_objective_change"])
                    <= 1e-10,
                    "matrix_identity": prediction["matrix_identity_error"] <= 1e-10,
                    "remainder_identity": prediction["remainder_identity_error"] <= 1e-10,
                }
                arrays = save_arrays(args.raw / f"probe-{index}.npz", x=proposed,
                                     values=actual, actual_z=actual_z, step=proposed-x)
                report["probes"].append({
                    "state": model["state"], "radius": model["radius"],
                    "source_arrays": model["arrays"], "arrays": arrays,
                    "prediction": prediction, "checks": {k: bool(v) for k, v in checks.items()}})
                print(model["state"], model["radius"], prediction, flush=True)
                write_json_atomic(args.output, report)
        report["checks"]["four_probe_replays"] = bool(
            len(report["probes"]) == 4 and all(all(p["checks"].values()) for p in report["probes"]))
        report.update(
            status="completed", qualification_pass=all(report["checks"].values()),
            model_usefulness_pass=bool(len(report["probes"]) == 4 and all(
                p["prediction"]["usefulness_pass"] for p in report["probes"])),
            native_backend_work=backend.work)
    except Exception as error:
        report.update(status="error", qualification_pass=False,
                      error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(args.output, report)
    print(json.dumps({k: report[k] for k in ("qualification_pass", "model_usefulness_pass")}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
