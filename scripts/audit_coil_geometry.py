"""Independently audit Fourier-coil geometry at increasing sampling resolution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from simsopt import load
from simsopt.geo import SurfaceRZFourier


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def base_fourier(curve):
    while hasattr(curve, "rotmat"):
        curve = curve.curve
    coefficients = np.asarray(curve.local_full_x)
    order = (coefficients.size // 3 - 1) // 2
    if coefficients.size != 3 * (2 * order + 1):
        raise TypeError(f"unsupported curve representation: {type(curve).__name__}")
    return coefficients.reshape(3, 2 * order + 1), order


def curve_points(curve, parameter: np.ndarray) -> np.ndarray:
    if hasattr(curve, "rotmat"):
        return curve_points(curve.curve, parameter) @ np.asarray(curve.rotmat)
    coefficients, order = base_fourier(curve)
    modes = np.arange(1, order + 1)[:, None]
    phase = 2 * np.pi * modes * parameter
    return np.stack(
        [
            coefficients[axis, 0]
            + np.sum(
                coefficients[axis, 2 * modes[:, 0] - 1, None] * np.sin(phase)
                + coefficients[axis, 2 * modes[:, 0], None] * np.cos(phase),
                axis=0,
            )
            for axis in range(3)
        ],
        axis=1,
    )


def length_and_max_curvature(curve, resolution: int) -> tuple[float, float]:
    coefficients, order = base_fourier(curve)
    parameter = np.linspace(0, 1, resolution, endpoint=False)
    modes = np.arange(1, order + 1)[:, None]
    angular_frequency = 2 * np.pi * modes
    phase = angular_frequency * parameter
    first = np.zeros((3, resolution))
    second = np.zeros_like(first)
    for axis in range(3):
        sine = coefficients[axis, 2 * modes[:, 0] - 1, None]
        cosine = coefficients[axis, 2 * modes[:, 0], None]
        first[axis] = np.sum(
            sine * angular_frequency * np.cos(phase)
            - cosine * angular_frequency * np.sin(phase),
            axis=0,
        )
        second[axis] = np.sum(
            -sine * angular_frequency**2 * np.sin(phase)
            - cosine * angular_frequency**2 * np.cos(phase),
            axis=0,
        )
    speed = np.linalg.norm(first.T, axis=1)
    curvature = np.linalg.norm(np.cross(first.T, second.T), axis=1) / speed**3
    return float(np.mean(speed)), float(np.max(curvature))


def minimum_coil_coil(curves, resolution: int) -> tuple[float, tuple[int, int]]:
    parameter = np.linspace(0, 1, resolution, endpoint=False)
    points = [curve_points(curve, parameter) for curve in curves]
    best = (float("inf"), (-1, -1))
    for first_index, first_points in enumerate(points):
        tree = cKDTree(first_points)
        for second_index in range(first_index + 1, len(points)):
            distance = float(tree.query(points[second_index], workers=-1)[0].min())
            if distance < best[0]:
                best = (distance, (first_index, second_index))
    return best


def distance_for_pair(curves, pair: tuple[int, int], resolution: int) -> float:
    parameter = np.linspace(0, 1, resolution, endpoint=False)
    first = curve_points(curves[pair[0]], parameter)
    second = curve_points(curves[pair[1]], parameter)
    return float(cKDTree(first).query(second, workers=-1)[0].min())


def minimum_coil_surface(
    curves,
    surface_path: Path,
    surface_resolution: int,
    curve_resolution: int,
) -> float:
    surface = SurfaceRZFourier.from_vmec_input(
        str(surface_path),
        range="full torus",
        nphi=surface_resolution,
        ntheta=surface_resolution,
    )
    tree = cKDTree(surface.gamma().reshape(-1, 3))
    parameter = np.linspace(0, 1, curve_resolution, endpoint=False)
    return min(
        float(tree.query(curve_points(curve, parameter), workers=-1)[0].min())
        for curve in curves
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coils", type=Path)
    parser.add_argument("surface", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--unique-coils", type=int, required=True)
    args = parser.parse_args()

    field = load(str(args.coils))
    curves = [coil.curve for coil in field.coils]
    unique = curves[: args.unique_coils]
    geometry = {}
    for resolution in [200, 1000, 5000, 20000]:
        values = [length_and_max_curvature(curve, resolution) for curve in unique]
        geometry[str(resolution)] = {
            "lengths_m": [value[0] for value in values],
            "max_curvatures_inverse_m": [value[1] for value in values],
            "maximum_curvature_inverse_m": max(value[1] for value in values),
        }

    coil_coil = {}
    for resolution in [200, 1000]:
        distance, pair = minimum_coil_coil(curves, resolution)
        coil_coil[str(resolution)] = {"distance_m": distance, "coil_pair": list(pair)}
    refined_pair = tuple(coil_coil["1000"]["coil_pair"])
    coil_coil["20000_refined_pair"] = {
        "distance_m": distance_for_pair(curves, refined_pair, 20000),
        "coil_pair": list(refined_pair),
    }

    coil_surface = {
        str(resolution): minimum_coil_surface(curves, args.surface, resolution, 1000)
        for resolution in [64, 128, 256, 512]
    }
    result = {
        "schema_version": 1,
        "method": "direct Fourier differentiation and independent sampled-distance audit",
        "inputs": {
            "coils_sha256": sha256(args.coils),
            "surface_sha256": sha256(args.surface),
            "total_coils": len(curves),
            "unique_coils": len(unique),
        },
        "geometry_resolution_study": geometry,
        "coil_coil_resolution_study": coil_coil,
        "coil_surface_resolution_study": coil_surface,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
