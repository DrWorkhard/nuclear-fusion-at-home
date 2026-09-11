"""Frozen physical qualification of an objective-preserving spatial flux factorization."""

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import time
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from simsopt import load
from simsopt._core.derivative import Derivative
from simsopt.field import BiotSavart
from simsopt.objectives import SquaredFlux

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.local_field_jacobian import local_field_jacobian
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)
from fusion_baselines.spatial_flux import lift_flux, normal_weights, spatial_flux


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def error(actual, expected):
    return float(np.max(np.abs(actual - expected)) / max(1.0, float(np.max(np.abs(expected)))))


def spectrum(jacobian):
    s = np.linalg.svd(jacobian, compute_uv=False)
    return {"singular_values": s.tolist(), "rank_relative_1e_10": int(np.sum(s > 1e-10 * s[0]))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--single-point-vjp", action="store_true")
    parser.add_argument("--batched", action="store_true")
    args = parser.parse_args()
    if args.single_point_vjp and args.batched:
        raise ValueError("choose one derivative implementation")
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("qualification outputs must be new")
    root = Path(__file__).resolve().parents[1]
    summary_path = root / "evidence/guarded-feasibility-v1/summary.json"
    study = json.loads(summary_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("completed reproducible guarded study required")
    for source in study["code"]:
        checked(source)
    arm_path = checked(study["arms"][0])
    arm = json.loads(arm_path.read_text())
    field_path = checked(arm["best"]["field"])
    document = json.loads(field_path.read_text())
    # Deliberately instantiate before prepare: mapping must survive runtime ID changes.
    serialized = load(str(field_path))
    report = {
        "schema_version": 1,
        "repository": git_state(root),
        "status": "running",
        "protocol": reference(root / "docs/optimization/SPATIAL_FLUX_FACTORIZATION_PROTOCOL.md"),
        "study": reference(summary_path),
        "arm": reference(arm_path),
        "code": [
            reference(Path(__file__)),
            *study["code"],
            reference(root / "src/fusion_baselines/spatial_flux.py"),
            reference(root / "src/fusion_baselines/serialized_dofs.py"),
        ],
        "installed_sources": [
            reference(Path(inspect.getfile(cls))) for cls in (BiotSavart, SquaredFlux, Derivative)
        ],
        "versions": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "simsopt")},
        "cases": [],
        "all_pass": False,
        "optimization_performed": False,
    }
    if args.single_point_vjp or args.batched:
        prior_path = root / (
            "evidence/spatial-flux-local-vjp-v1.json"
            if args.batched
            else "evidence/spatial-flux-factorization-v1.json"
        )
        prior = json.loads(prior_path.read_text())
        if not prior["all_pass"] or len(prior["cases"]) != 2:
            raise ValueError("original spatial qualification required")
        report["reference_qualification"] = reference(prior_path)
        report["local_vjp_protocol"] = reference(
            root / "docs/optimization/SPATIAL_FLUX_LOCAL_VJP_PROTOCOL.md"
        )
        report["code"].append(reference(root / "src/fusion_baselines/local_field_jacobian.py"))
        if args.batched:
            report["batched_protocol"] = reference(
                root / "docs/optimization/BATCHED_SPATIAL_JACOBIAN_PROTOCOL.md"
            )
            report["code"].append(
                reference(root / "src/fusion_baselines/batched_field_jacobian.py")
            )
    args.raw.mkdir(parents=True)
    try:
        ctx, backend, preparation = prepare(root, args.raw, guarded_curvature=True)
        report["preparation"] = preparation
        backend.scales *= study["normalization"]["factor"]
        source_names = study["preparation"]["degrees_of_freedom"]
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
            archived = arrays["x"].copy()
        if not np.array_equal(named_serialized_values(document, source_names), archived):
            raise ValueError("archived physical parameter identity failed")
        owner_map = {}
        for (curve, leaves), coil in zip(
            base_coil_owners(document), ctx.Jf.field.coils[:4], strict=True
        ):
            pairs = [(curve, coil.curve.name)]
            for path, owner in leaves:
                current = coil.current
                for attribute in path:
                    current = getattr(current, attribute)
                pairs.append((owner, current.name))
            for owner, target in pairs:
                if owner in owner_map and owner_map[owner] != target:
                    raise ValueError("conflicting shared physical owner")
                owner_map[owner] = target
        permutation = dof_permutation(source_names, backend.names, owner_map)
        report["physical_owner_map"] = owner_map
        report["source_indices_in_target_order"] = permutation.tolist()
        x0 = ctx.Jf.x.copy()
        if (
            hashlib.sha256(x0[np.argsort(permutation)].tobytes()).hexdigest()
            != (arm["evaluations"][0]["x_sha256"])
        ):
            raise ValueError("original-point physical hash mismatch")
        normal = ctx.Jf.surface.normal().copy()
        points = ctx.Jf.surface.gamma().reshape(-1, 3).copy()
        weights = normal_weights(normal)
        field = ctx.Jf.field
        if (
            normal.shape != (32, 32, 3)
            or any(len(c.curve.quadpoints) != 200 for c in field.coils)
            or ctx.Jf.definition != "quadratic flux"
            or np.any(ctx.Jf.target)
        ):
            raise ValueError("unsupported flux definition, target or quadrature")
        k, threshold = float(backend.scales[0]), float(ctx.Jf.threshold)
        direction = np.random.default_rng(45).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        direction = direction[permutation]
        for name, x in (("original", x0), ("guarded-trf-best", archived[permutation])):
            started = time.monotonic()
            values, common_jac = backend(x)
            bundle_seconds = time.monotonic() - started
            field.set_points(points)
            b = field.B().reshape(normal.shape).copy()
            z = spatial_flux(b, normal)
            phi = float(z @ z / 2)
            if abs(phi - threshold) <= 0.01 * threshold:
                raise ValueError("qualification state too close to discontinuous cut-in")
            dz = np.empty((len(z), len(x)))
            covector = np.zeros((len(z), 3))
            derivative_started = time.monotonic()
            batch_runs = []
            if args.batched:
                before_points = field.get_points_cart_ref().copy()
                for repeat in range(3):
                    start = time.monotonic()
                    batch_z, batch_dz = batched_field_jacobian(field, ctx.Jf, points, weights)
                    elapsed = time.monotonic() - start
                    if repeat == 0:
                        reference_z, reference_dz = batch_z.copy(), batch_dz.copy()
                    batch_runs.append(
                        {
                            "seconds": elapsed,
                            "same_z": np.array_equal(batch_z, reference_z),
                            "same_dz": np.array_equal(batch_dz, reference_dz),
                        }
                    )
                dz = batch_dz
            elif args.single_point_vjp:
                dz = local_field_jacobian(field, ctx.Jf, points, weights)
            else:
                for i in range(len(z)):
                    covector[i] = weights[i]
                    dz[i] = field.B_vjp(covector)(ctx.Jf)
                    covector[i] = 0
                    if (i + 1) % 128 == 0:
                        print(f"{name}: analytic spatial rows {i + 1}/{len(z)}", flush=True)
            derivative_seconds = time.monotonic() - derivative_started
            r, dr = lift_flux(z, dz, scale=k, threshold=threshold)
            lifted_values = np.concatenate((r, values[1:]))
            lifted_jac = np.vstack((dr, common_jac[1:]))
            metrics = {
                "raw_phi_relative_error": abs(phi - values[0] / k) / abs(values[0] / k),
                "raw_phi_gradient_error": error(z @ dz, common_jac[0] / k),
                "common_merit_relative_error": abs(lifted_values @ lifted_values - values @ values)
                / (values @ values),
                "common_gradient_error": error(lifted_jac.T @ lifted_values, common_jac.T @ values),
            }
            checks = {key: bool(value <= 1e-10) for key, value in metrics.items()}
            if args.batched:
                metrics["batched_projection_error"] = error(batch_z, z)
                metrics["batched_phi_relative_error"] = abs(batch_z @ batch_z / 2 - phi) / phi
                checks["batched_field"] = metrics["batched_projection_error"] <= 1e-10
                checks["batched_phi"] = metrics["batched_phi_relative_error"] <= 1e-10
                checks["field_points_unchanged"] = np.array_equal(
                    before_points, field.get_points_cart_ref()
                )
                checks["batch_repeats"] = all(r["same_z"] and r["same_dz"] for r in batch_runs)
            if args.single_point_vjp or args.batched:
                previous = next(c for c in prior["cases"] if c["name"] == name)
                old_inverse = np.argsort(prior["source_indices_in_target_order"])
                with np.load(checked(previous["arrays"]), allow_pickle=False) as arrays:
                    old_x = arrays["x"][old_inverse][permutation]
                    old_dz = arrays["dz"][:, old_inverse][:, permutation]
                metrics["local_vs_full_vjp_error"] = error(dz, old_dz)
                checks["local_vs_full_vjp"] = metrics["local_vs_full_vjp_error"] <= 1e-10
                checks["same_physical_state"] = np.array_equal(x, old_x)
            if name == "guarded-trf-best":
                checks["serialized_geometry_currents"] = all(
                    np.array_equal(a.curve.gamma(), b.curve.gamma())
                    and a.current.get_value() == b.current.get_value()
                    and a.regularization == b.regularization
                    for a, b in zip(field.coils, serialized.coils, strict=True)
                )
            finite_differences = []
            for eps in (1e-4, 1e-5, 1e-6):
                pairs = []
                for sign in (1, -1):
                    ctx.Jf.x = x + sign * eps * direction
                    field.set_points(points)
                    zz = spatial_flux(field.B().reshape(normal.shape), normal)
                    pairs.append((zz, lift_flux(zz, scale=k, threshold=threshold)[0]))
                finite_differences.append(
                    {
                        "eps": eps,
                        "z_directional_error": error(
                            (pairs[0][0] - pairs[1][0]) / (2 * eps), dz @ direction
                        ),
                        "r_directional_error": error(
                            (pairs[0][1] - pairs[1][1]) / (2 * eps), dr @ direction
                        ),
                    }
                )
            ctx.Jf.x = x
            checks["directional_z"] = finite_differences[-1]["z_directional_error"] <= 1e-6
            checks["directional_r"] = finite_differences[-1]["r_directional_error"] <= 1e-6
            path = args.raw / f"{name}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(
                    stream,
                    x=x,
                    z=z,
                    dz=dz,
                    common_values=values,
                    common_jacobian=common_jac,
                    normal=normal,
                    field=b,
                    direction=direction,
                    scale=k,
                    threshold=threshold,
                )
            checks = {key: bool(value) for key, value in checks.items()}
            record = {
                "name": name,
                "raw_phi": phi,
                "scale": k,
                "threshold": threshold,
                "metrics": metrics,
                "checks": checks,
                "finite_differences": finite_differences,
                "scalar_spectrum": spectrum(common_jac),
                "spatial_spectrum": spectrum(lifted_jac),
                "arrays": reference(path),
                "work": {
                    "full_common_bundles": 1,
                    "additional_B_vjp_calls": 0 if args.batched else len(z),
                    "additional_field_only_requests": 7,
                    "B_vjp_points_per_call": 0
                    if args.batched
                    else (1 if args.single_point_vjp else len(z)),
                    "extra_single_point_B_calls": len(z) if args.single_point_vjp else 0,
                    "batched_runs": batch_runs,
                    "batched_physical_coil_contractions": 48 if args.batched else 0,
                    "batched_geometry_derivative_requests": 96 if args.batched else 0,
                    "batched_current_vjp_calls": 48 if args.batched else 0,
                    "common_bundle_seconds": bundle_seconds,
                    "spatial_jacobian_seconds": derivative_seconds,
                },
                "elapsed_seconds": time.monotonic() - started,
                "pass": all(checks.values()),
            }
            report["cases"].append(record)
            write_json_atomic(args.output, report)
        report.update(status="completed", all_pass=all(c["pass"] for c in report["cases"]))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"all_pass": report["all_pass"]}))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
