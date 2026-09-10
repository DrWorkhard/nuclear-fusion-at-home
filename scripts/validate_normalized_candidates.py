"""Frozen post-search geometric/flux holdout, with no feedback into optimization."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from audit_coil_geometry import length_and_max_curvature, minimum_coil_coil, minimum_coil_surface
from simsopt import load
from simsopt.field import BiotSavart, coils_via_symmetries
from simsopt.geo import CurveXYZFourier, SurfaceRZFourier

from fusion_baselines.flux_metrics import quadratic_flux
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked_path(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError("input hash mismatch")
    return path


def refined_field(field):
    curves = []
    for coil in field.coils[:4]:
        coefficients = coil.curve.local_full_x.copy()
        order = (len(coefficients) // 3 - 1) // 2
        curve = CurveXYZFourier(800, order)
        curve.local_full_x = coefficients
        curves.append(curve)
    return BiotSavart(
        coils_via_symmetries(
            curves,
            [c.current for c in field.coils[:4]],
            2,
            True,
            regularizations=[c.regularization for c in field.coils[:4]],
        )
    )


def check_candidate(field_path, surface_path, scale):
    started = time.monotonic()
    field = load(str(field_path))
    if len(field.coils) != 16:
        raise ValueError("expected sixteen physical coil copies")
    flux = []
    for resolution, quadrature in [(32, 200), (64, 200), (128, 200), (128, 800)]:
        surface = SurfaceRZFourier.from_vmec_input(
            str(surface_path),
            range="half period",
            nphi=resolution,
            ntheta=resolution,
        )
        evaluated = refined_field(field) if quadrature == 800 else field
        if any(len(c.curve.quadpoints) != quadrature for c in evaluated.coils):
            raise ValueError("unexpected coil quadrature")
        evaluated.set_points(surface.gamma().reshape(-1, 3))
        b = evaluated.B().reshape(surface.normal().shape)
        flux.append(
            {
                "surface_resolution": resolution,
                "coil_quadrature": quadrature,
                "unthresholded_quadratic_flux": quadratic_flux(b, surface.normal()),
                "mean_B_magnitude_T": float(np.mean(np.linalg.norm(b, axis=-1))),
            }
        )
    geometry = {}
    distances = {}
    curves = [c.curve for c in field.coils]
    for resolution in [200, 1000, 5000, 20000]:
        print(f"geometry holdout: {field_path.parent.name} n={resolution}", flush=True)
        values = [length_and_max_curvature(curve, resolution) for curve in curves[:4]]
        geometry[str(resolution)] = {
            "unique_total_length_reactor_m": sum(v[0] for v in values) * scale,
            "maximum_curvature_reactor_inverse_m": max(v[1] for v in values) / scale,
        }
        distance, pair = minimum_coil_coil(curves, resolution)
        distances[str(resolution)] = {
            "centerline_distance_reactor_m": distance * scale,
            "coil_pair": list(pair),
        }
    plasma = {}
    for resolution in [64, 128, 256, 512]:
        plasma[str(resolution)] = (
            minimum_coil_surface(curves, surface_path, resolution, 20000) * scale
        )
    phi_change = abs(
        flux[2]["unthresholded_quadratic_flux"] - flux[1]["unthresholded_quadratic_flux"]
    )
    coil_change = abs(
        flux[3]["unthresholded_quadratic_flux"] - flux[2]["unthresholded_quadratic_flux"]
    )
    checks = {
        "flux_cut_in": flux[-1]["unthresholded_quadratic_flux"] <= 1e-8,
        "surface_flux_refinement": phi_change
        <= max(1e-10, 0.01 * flux[1]["unthresholded_quadratic_flux"]),
        "coil_flux_refinement": coil_change
        <= max(1e-10, 0.01 * flux[2]["unthresholded_quadratic_flux"]),
        "length": geometry["20000"]["unique_total_length_reactor_m"] <= 220,
        "curvature": geometry["20000"]["maximum_curvature_reactor_inverse_m"] <= 1,
        "coil_coil_clearance": distances["20000"]["centerline_distance_reactor_m"] >= 1.06,
        "coil_plasma_clearance": plasma["512"] >= 1.3,
    }
    return {
        "field": reference(field_path),
        "a0": scale,
        "flux": flux,
        "geometry": geometry,
        "coil_coil": distances,
        "coil_plasma": plasma,
        "checks": checks,
        "bounded_geometry_flux_screen_pass": all(checks.values()),
        "full_engineering_admission_pass": False,
        "elapsed_seconds": time.monotonic() - started,
        "work": {
            "B_grid_evaluations": 4,
            "B_points_total": 37888,
            "all_pair_coil_distance_resolutions": [200, 1000, 5000, 20000],
            "plasma_distance_surface_resolutions": [64, 128, 256, 512],
            "plasma_distance_curve_points": 20000,
            "distance_query_workers": -1,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("holdout output exists")
    root = Path(__file__).resolve().parents[1]
    summary_path = args.study / "summary.json"
    study = json.loads(summary_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("require completed, reproducible study before holdout")
    surface = checked_path(study["preparation"]["surface"])
    scale = study["preparation"]["thresholds"]["a0"]
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "study": reference(summary_path),
        "protocol": reference(root / "docs/NORMALIZED_FEASIBILITY_PROTOCOL.md"),
        "code": [
            reference(Path(__file__)),
            reference(root / "scripts/audit_coil_geometry.py"),
            reference(root / "src/fusion_baselines/flux_metrics.py"),
        ],
        "status": "running",
        "candidates": [],
        "used_for_optimizer_feedback": False,
    }
    try:
        for method in study.get("methods", ["lbfgsb", "auglag"]):
            arm_path = args.study / f"{method}-1.json"
            expected = next(r for r in study["arms"] if Path(r["path"]).name == arm_path.name)
            checked_path(expected)
            arm = json.loads(arm_path.read_text())
            candidate = check_candidate(checked_path(arm["best"]["field"]), surface, scale)
            result["candidates"].append({"method": method, "arm": reference(arm_path), **candidate})
            write_json_atomic(args.output, result)
        result["status"] = "completed"
        result["all_pass"] = all(
            c["bounded_geometry_flux_screen_pass"] for c in result["candidates"]
        )
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
