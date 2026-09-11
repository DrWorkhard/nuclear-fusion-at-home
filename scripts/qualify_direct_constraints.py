"""Qualify the frozen raw-flux/smooth-inequality map on two unchanged physical states."""

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import time
from pathlib import Path

import numpy as np
from audit_coil_geometry import curve_points
from qualify_optimization_oracle import prepare
from scipy.spatial import cKDTree
from simsopt import load
from simsopt.geo import CurveCurveDistance, CurveSurfaceDistance, SurfaceRZFourier
from simsopt.objectives import SquaredFlux

from fusion_baselines.curvature_bounds import derivatives as fourier_derivatives
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
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
        raise ValueError(f"input hash mismatch: {path}")
    return path


def errors(actual, expected):
    return np.abs(np.asarray(actual) - expected) / np.maximum(1.0, np.abs(expected))


def metric_crosschecks(backend, full_surface, metrics, jacobian):
    checks = {}
    b = backend
    native_flux = SquaredFlux(b.surface, b.field, definition="quadratic flux", threshold=0.0)
    native_value = float(native_flux.J())
    if native_value <= 1e-10:
        raise ValueError("native derivative comparison below its documented guard")
    checks["native_raw_flux"] = abs(metrics["raw_flux"] / native_value - 1)
    native_gradient = native_flux.dJ(partials=True)(b.global_objective) / b.flux_scale
    checks["native_raw_flux_gradient"] = float(errors(jacobian[0], native_gradient).max())
    lengths, msc, arc, curvature = [], [], [], []
    for c in b.bases:
        coefficients = c.local_full_x.reshape(3, -1)
        v, a, _ = fourier_derivatives(coefficients, np.arange(200) / 200)
        speed = np.linalg.norm(v, axis=1)
        kappa = np.linalg.norm(np.cross(v, a), axis=1) / speed**3
        lengths.append(float(np.mean(speed)))
        msc.append(float(np.mean(kappa**2 * speed) / np.mean(speed)))
        arc.append(float(np.var(speed)))
        v, a, _ = fourier_derivatives(coefficients, np.arange(1600) / 1600)
        curvature.append(
            float(
                np.max(np.linalg.norm(np.cross(v, a), axis=1) / np.linalg.norm(v, axis=1) ** 3)
                / b.scale
            )
        )
    for key, actual, expected in (
        ("length", metrics["lengths_device"], lengths),
        ("msc", metrics["msc_native"], msc),
        ("arc_variance", metrics["arclength_native"], arc),
        ("fine_curvature", [c["sampled_maximum"] for c in metrics["curvature"]], curvature),
    ):
        checks["independent_" + key] = float(errors(actual, expected).max())
    checks["independent_physical_positions"] = max(
        float(errors(c.gamma(), curve_points(c, np.arange(200) / 200)).max()) for c in b.curves
    )
    native_pairs = [
        float(CurveCurveDistance([b.curves[i], b.curves[j]], 0).shortest_distance()) * b.scale
        for i, j in b.pairs
    ]
    checks["native_all_pair_squared_minima"] = float(
        errors(
            [c["sampled_squared_minimum"] for c in metrics["coil_clearance"]],
            np.asarray(native_pairs) ** 2,
        ).max()
    )
    plasma_min = (
        float(CurveSurfaceDistance(b.curves, full_surface, 0).shortest_distance()) * b.scale
    )
    checks["native_all16_plasma_squared_minimum"] = float(
        errors(
            min(p["sampled_squared_minimum"] for p in metrics["plasma_clearance"]), plasma_min**2
        )
    )
    tree = cKDTree(b.plasma_points)
    checks["plasma_sample_symmetry"] = max(
        float(tree.query(b.plasma_points @ c.rotmat)[0].max())
        for c in b.curves
        if hasattr(c, "rotmat")
    )
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable qualification outputs required")
    root = Path(__file__).resolve().parents[1]
    study_path = root / "evidence/spatial-trf-pilot-v1/summary.json"
    study = json.loads(study_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("qualified frozen spatial study required")
    arm_ref = next(r for r in study["arms"] if Path(r["path"]).name == "spatial-1.json")
    arm = json.loads(checked(arm_ref).read_text())
    field_path = checked(arm["best"]["field"])
    document = json.loads(field_path.read_text())
    serialized = load(str(field_path))  # Force runtime IDs across the known 9/10 boundary.
    report = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(
            root / "docs/optimization/DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL.md"
        ),
        "source_study": reference(study_path),
        "source_arm": arm_ref,
        "code": [
            reference(root / p)
            for p in (
                "scripts/qualify_direct_constraints.py",
                "scripts/qualify_optimization_oracle.py",
                "scripts/audit_coil_geometry.py",
                "src/fusion_baselines/direct_constraints.py",
                "src/fusion_baselines/smooth_bounds.py",
                "src/fusion_baselines/serialized_dofs.py",
                "src/fusion_baselines/spatial_flux.py",
                "src/fusion_baselines/curvature_bounds.py",
                "src/fusion_baselines/refined_curvature.py",
            )
        ],
        "versions": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "simsopt")},
        "cases": [],
        "all_pass": False,
        "status": "running",
        "optimization_performed": False,
        "physical_feasibility_certified": False,
    }
    args.raw.mkdir(parents=True)
    try:
        ctx, original_backend, preparation = prepare(root, args.raw, guarded_curvature=True)
        report["preparation"] = preparation
        if preparation["thresholds"] != study["preparation"]["thresholds"]:
            raise ValueError("source physical thresholds changed")
        full_surface = SurfaceRZFourier.from_vmec_input(
            str(checked(preparation["surface"])), range="full torus", nphi=64, ntheta=64
        )
        backend = DirectConstraintBackend(ctx, full_surface, flux_scale=1e-6)
        report["labels"], report["flux_scale"] = backend.labels, backend.flux_scale
        sources = {
            Path(inspect.getfile(type(obj)))
            for obj in [*backend.native, *backend.fine, ctx.Jf, ctx.Jf.field]
        }
        report["installed_sources"] = [reference(p) for p in sorted(sources)]
        source_names = study["preparation"]["degrees_of_freedom"]
        archived = named_serialized_values(document, source_names)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
            if not np.array_equal(archived, arrays["x"]):
                raise ValueError("source field and array disagree")
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
                    raise ValueError("inconsistent physical current owner")
                owners[source] = target
        permutation = dof_permutation(source_names, backend.names, owners)
        x0 = ctx.Jf.x.copy()
        if (
            hashlib.sha256(x0[np.argsort(permutation)].tobytes()).hexdigest()
            != (arm["evaluations"][0]["x_sha256"])
        ):
            raise ValueError("original physical state changed")
        report["owner_map"], report["source_indices_in_target_order"] = owners, permutation.tolist()
        direction = np.random.default_rng(46).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        direction = direction[permutation]
        for name, x in (("original", x0), ("spatial128-best", archived[permutation])):
            started = time.monotonic()
            values, jacobian, metrics = backend.evaluate(x)
            native_errors = metric_crosschecks(backend, full_surface, metrics, jacobian)
            checks = {key: bool(value <= 1e-10) for key, value in native_errors.items()}
            checks["conservative_sampled_extrema"] = bool(
                all(c["smooth_upper"] >= c["sampled_maximum"] for c in metrics["curvature"])
                and all(
                    c["smooth_squared_lower"] <= c["sampled_squared_minimum"]
                    for c in metrics["coil_clearance"] + metrics["plasma_clearance"]
                )
            )
            checks["native_linking_zero"] = bool(ctx.c_list[7].J() == 0)
            if name == "spatial128-best":
                checks["serialized_geometry_currents"] = all(
                    np.array_equal(a.curve.gamma(), b.curve.gamma())
                    and a.current.get_value() == b.current.get_value()
                    and a.regularization == b.regularization
                    for a, b in zip(backend.field.coils, serialized.coils, strict=True)
                )
            finite_differences = []
            exact = jacobian @ direction
            for eps in (1e-5, 1e-6, 1e-7, 1e-8):
                plus = backend.evaluate(x + eps * direction, derivatives=False)[0]
                minus = backend.evaluate(x - eps * direction, derivatives=False)[0]
                fd = (plus - minus) / (2 * eps)
                discrepancy = errors(fd, exact)
                finite_differences.append(
                    {
                        "eps": eps,
                        "finite_difference": fd.tolist(),
                        "normalized_errors": discrepancy.tolist(),
                        "maximum_error": float(discrepancy.max()),
                        "worst_row": backend.labels[int(np.argmax(discrepancy))],
                    }
                )
                print(name, eps, finite_differences[-1]["maximum_error"], flush=True)
            checks["all_directional_rows"] = finite_differences[-1]["maximum_error"] <= 1e-6
            ctx.Jf.x = x.copy()
            path = args.raw / f"{name}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(
                    stream, x=x, values=values, jacobian=jacobian, direction=direction
                )
            report["cases"].append(
                {
                    "name": name,
                    "metrics": metrics,
                    "native_errors": native_errors,
                    "checks": checks,
                    "pass": all(checks.values()),
                    "arrays": reference(path),
                    "values": values.tolist(),
                    "analytic_directional": exact.tolist(),
                    "finite_differences": finite_differences,
                    "elapsed_seconds": time.monotonic() - started,
                }
            )
            write_json_atomic(args.output, report)
        report.update(
            status="completed",
            all_pass=all(c["pass"] for c in report["cases"]),
            work=backend.work,
            extra_crosscheck_work_per_state={
                "native_flux_J": 1,
                "native_flux_dJ": 1,
                "native_pair_minima": 120,
                "native_all16_plasma_minimum": 1,
                "native_linking_J": 1,
                "independent_fourier_curves": 16,
            },
        )
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"all_pass": report["all_pass"]}))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
