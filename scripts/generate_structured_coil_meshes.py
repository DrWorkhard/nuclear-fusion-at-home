#!/usr/bin/env python3
"""Generate periodic structured-sweep tetrahedral meshes for real coil centerlines."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import meshio
import numpy as np
from simsopt.geo import CurveLength
from stellcoilbench.post_processing import load_bfield_from_coils_json
from stellcoilbench.post_processing._coil_io import _get_coils_from_bfield, get_unique_coils


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _periodic_resample(points: np.ndarray, count: int) -> np.ndarray:
    closed = np.vstack((points, points[0]))
    segment_lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    targets = np.linspace(0.0, cumulative[-1], count, endpoint=False)
    indices = np.searchsorted(cumulative, targets, side="right") - 1
    indices = np.clip(indices, 0, len(segment_lengths) - 1)
    fraction = (targets - cumulative[indices]) / segment_lengths[indices]
    return closed[indices] + fraction[:, None] * (closed[indices + 1] - closed[indices])


def _rotate(vector: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    return (
        vector * math.cos(angle)
        + np.cross(axis, vector) * math.sin(angle)
        + axis * np.dot(axis, vector) * (1.0 - math.cos(angle))
    )


def _transport(normal: np.ndarray, tangent: np.ndarray) -> np.ndarray:
    projected = normal - np.dot(normal, tangent) * tangent
    norm = np.linalg.norm(projected)
    if norm < 1e-12:
        raise ValueError("Parallel-transport frame became singular")
    return projected / norm


def _periodic_frames(centers: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tangents = np.roll(centers, -1, axis=0) - np.roll(centers, 1, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    axes = np.eye(3)
    reference = axes[np.argmin(np.abs(axes @ tangents[0]))]
    normals = np.empty_like(tangents)
    normals[0] = np.cross(tangents[0], reference)
    normals[0] /= np.linalg.norm(normals[0])
    for index in range(1, len(tangents)):
        normals[index] = _transport(normals[index - 1], tangents[index])

    transported_end = _transport(normals[-1], tangents[0])
    closure_angle = math.atan2(
        np.dot(tangents[0], np.cross(transported_end, normals[0])),
        np.dot(transported_end, normals[0]),
    )
    for index in range(1, len(tangents)):
        normals[index] = _rotate(
            normals[index], tangents[index], closure_angle * index / len(tangents)
        )
        normals[index] = _transport(normals[index], tangents[index])
    binormals = np.cross(tangents, normals)
    binormals /= np.linalg.norm(binormals, axis=1)[:, None]
    return tangents, normals, binormals


def _mesh_coil(
    sampled_centerline: np.ndarray, width: float, height: float, target_h: float
) -> tuple[np.ndarray, np.ndarray, dict]:
    _, normals, binormals = _periodic_frames(sampled_centerline)
    n_width = max(1, math.ceil(width / target_h))
    n_height = max(1, math.ceil(height / target_h))
    u_values = np.linspace(-width / 2.0, width / 2.0, n_width + 1)
    v_values = np.linspace(-height / 2.0, height / 2.0, n_height + 1)
    rings = (
        sampled_centerline[:, None, None, :]
        + u_values[None, :, None, None] * normals[:, None, None, :]
        + v_values[None, None, :, None] * binormals[:, None, None, :]
    )
    points = rings.reshape(-1, 3)

    def vertex(along: int, width_index: int, height_index: int) -> int:
        along %= len(sampled_centerline)
        return (along * (n_width + 1) + width_index) * (n_height + 1) + height_index

    tetrahedra: list[list[int]] = []
    for along in range(len(sampled_centerline)):
        for width_index in range(n_width):
            for height_index in range(n_height):
                v000 = vertex(along, width_index, height_index)
                v100 = vertex(along + 1, width_index, height_index)
                v010 = vertex(along, width_index + 1, height_index)
                v110 = vertex(along + 1, width_index + 1, height_index)
                v001 = vertex(along, width_index, height_index + 1)
                v101 = vertex(along + 1, width_index, height_index + 1)
                v011 = vertex(along, width_index + 1, height_index + 1)
                v111 = vertex(along + 1, width_index + 1, height_index + 1)
                tetrahedra.extend(
                    [
                        [v000, v100, v110, v111],
                        [v000, v110, v010, v111],
                        [v000, v010, v011, v111],
                        [v000, v011, v001, v111],
                        [v000, v001, v101, v111],
                        [v000, v101, v100, v111],
                    ]
                )
    cells = np.asarray(tetrahedra, dtype=np.int64)
    xyz = points[cells]
    determinants = np.linalg.det(
        np.stack((xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0], xyz[:, 3] - xyz[:, 0]), axis=2)
    )
    negative = determinants < 0.0
    cells[negative, :2] = cells[negative, 1::-1]
    segment_lengths = np.linalg.norm(
        np.roll(sampled_centerline, -1, axis=0) - sampled_centerline, axis=1
    )
    return points, cells, {
        "along_sections": len(sampled_centerline),
        "cross_section_cells": [n_width, n_height],
        "maximum_centerline_segment_m": float(np.max(segment_lengths)),
    }


def generate_mesh(coils: list, width: float, height: float, target_h: float, output: Path) -> dict:
    point_blocks = []
    cell_blocks = []
    physical_blocks = []
    block_metadata = []
    offset = 0
    exact_total_length = 0.0
    for coil_index, coil in enumerate(coils):
        gamma = np.asarray(coil.curve.gamma(), dtype=float).reshape(-1, 3)
        exact_length = float(CurveLength(coil.curve).J())
        along_count = max(16, math.ceil(exact_length / target_h))
        centerline = _periodic_resample(gamma, along_count)
        points, cells, metadata = _mesh_coil(centerline, width, height, target_h)
        point_blocks.append(points)
        cell_blocks.append(("tetra", cells + offset))
        physical_blocks.append(np.full(len(cells), coil_index + 1, dtype=np.int32))
        offset += len(points)
        exact_total_length += exact_length
        block_metadata.append(
            {"coil_index": coil_index, "exact_centerline_length_m": exact_length, **metadata}
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    meshio.write(
        output,
        meshio.Mesh(
            np.vstack(point_blocks),
            cell_blocks,
            cell_data={"gmsh:physical": physical_blocks},
        ),
        file_format="gmsh22",
    )
    return {
        "path": str(output.resolve()),
        "sha256": _sha256(output),
        "target_h_m": target_h,
        "width_m": width,
        "height_m": height,
        "exact_total_centerline_length_m": exact_total_length,
        "expected_centerline_area_volume_m3": exact_total_length * width * height,
        "coils": block_metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coils", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resolutions", default="0.05,0.04,0.03,0.02")
    parser.add_argument("--width", type=float, default=0.05)
    parser.add_argument("--height", type=float, default=0.05)
    parser.add_argument("--nfp", type=int, default=2)
    parser.add_argument("--stellarator-symmetry", action="store_true", default=True)
    args = parser.parse_args()
    resolutions = [float(value) for value in args.resolutions.split(",")]
    bfield = load_bfield_from_coils_json(args.coils)
    coils = get_unique_coils(
        _get_coils_from_bfield(bfield), nfp=args.nfp, stellsym=args.stellarator_symmetry
    )
    if len(coils) != 4:
        raise ValueError(f"Expected four unique coils, found {len(coils)}")
    results = []
    for resolution in resolutions:
        subdir = args.output_dir / f"res_{resolution:.3f}".replace(".", "_")
        result = generate_mesh(
            coils, args.width, args.height, resolution, subdir / "coils_structured.msh"
        )
        results.append(result)
        print(json.dumps(result, indent=2))
    manifest = {
        "schema_version": 1,
        "generator": "periodic_rotation_minimizing_structured_sweep",
        "source_coils": str(args.coils.resolve()),
        "source_coils_sha256": _sha256(args.coils),
        "meshes": results,
    }
    manifest_path = args.output_dir / "structured_mesh_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
