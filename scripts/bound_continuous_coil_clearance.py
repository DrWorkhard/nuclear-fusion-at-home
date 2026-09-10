"""Supplement existing all-pair grid clearances with a Fourier continuum bound."""

import argparse
import json
from pathlib import Path

import numpy as np
from audit_coil_geometry import base_fourier
from simsopt import load

from fusion_baselines.clearance_bounds import periodic_pair_clearance_bound
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def curve_bounds(curve):
    coefficients, order = base_fourier(curve)
    if not np.all(np.isfinite(coefficients)):
        raise ValueError("nonfinite Fourier coefficients")
    center = coefficients[:, 0].copy()
    transforms = []
    while hasattr(curve, "rotmat"):
        transform = np.asarray(curve.rotmat)
        if transform.shape != (3, 3) or not np.all(np.isfinite(transform)):
            raise ValueError("invalid coil transformation")
        transforms.append(transform)
        curve = curve.curve
    multiplier = 1 + 1e-12
    for rotation in reversed(transforms):
        center = center @ rotation
        multiplier *= float(np.linalg.norm(rotation, ord=2))
    amplitudes = np.linalg.norm(coefficients[:, 1::2], axis=0) + np.linalg.norm(
        coefficients[:, 2::2], axis=0
    )
    omega = 2 * np.pi * np.arange(1, order + 1)
    return {
        "center": center.tolist(),
        "radius_bound": float(amplitudes.sum() * multiplier),
        "speed_bound": float((omega * amplitudes).sum() * multiplier),
        "acceleration_bound": float((omega**2 * amplitudes).sum() * multiplier),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("holdout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("clearance-bound output exists")
    root = Path(__file__).resolve().parents[1]
    data = json.loads(args.holdout.read_text())
    if data["status"] != "completed":
        raise ValueError("completed candidate holdout required")
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "retrospective": True,
        "holdout": reference(args.holdout),
        "protocol": reference(root / "docs/CONTINUOUS_COIL_CLEARANCE_CHECK.md"),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/clearance_bounds.py"),
            reference(root / "scripts/audit_coil_geometry.py"),
        ],
        "candidates": [],
    }
    for candidate in data["candidates"]:
        path = Path(candidate["field"]["path"])
        if sha256_file(path) != candidate["field"]["sha256"]:
            raise ValueError("field hash mismatch")
        bounds = [curve_bounds(c.curve) for c in load(str(path)).coils]
        speed = max(b["speed_bound"] for b in bounds)
        acceleration = max(b["acceleration_bound"] for b in bounds)
        separation = max(
            float(np.linalg.norm(np.asarray(a["center"]) - b["center"]))
            + a["radius_bound"]
            + b["radius_bound"]
            for i, a in enumerate(bounds)
            for b in bounds[i + 1 :]
        )
        scale = candidate["a0"]
        sampled = candidate["coil_coil"]["20000"]["centerline_distance_reactor_m"] / scale
        estimate = periodic_pair_clearance_bound(sampled, 20000, speed, acceleration, separation)
        lower = estimate["continuous_distance_lower_bound"]
        radius = float(np.hypot(0.05, 0.05) / 2)
        result["candidates"].append(
            {
                "method": candidate["method"],
                "field": candidate["field"],
                "curve_bounds": bounds,
                "global_speed_bound": speed,
                "global_acceleration_bound": acceleration,
                "global_separation_bound": separation,
                "sampled_minimum_device_m": sampled,
                **estimate,
                "a0": scale,
                "continuous_centerline_lower_bound_reactor_m": lower * scale,
                "centerline_requirement_pass": lower * scale >= 1.06,
                "idealized_section_enclosing_radius_device_m": radius,
                "different_coil_tube_gap_lower_bound_device_m": lower - 2 * radius,
                "actual_mesh_enclosure_or_self_intersection_certified": False,
            }
        )
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            [
                (
                    c["method"],
                    c["continuous_centerline_lower_bound_reactor_m"],
                    c["centerline_requirement_pass"],
                )
                for c in result["candidates"]
            ]
        )
    )


if __name__ == "__main__":
    main()
