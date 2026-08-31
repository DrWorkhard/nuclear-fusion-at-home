#!/usr/bin/env python3
"""Audit finite-build tetrahedral meshes against a frozen centerline-volume proxy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import meshio
import numpy as np


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tetra_blocks(mesh: meshio.Mesh) -> list[tuple[np.ndarray, np.ndarray | None]]:
    blocks: list[tuple[np.ndarray, np.ndarray | None]] = []
    physical = mesh.cell_data.get("gmsh:physical", [])
    for index, block in enumerate(mesh.cells):
        if block.type not in {"tetra", "tetra10"}:
            continue
        tags = physical[index] if index < len(physical) else None
        blocks.append((np.asarray(block.data[:, :4], dtype=np.int64), tags))
    return blocks


def audit_mesh(path: Path) -> dict:
    mesh = meshio.read(path)
    blocks = _tetra_blocks(mesh)
    if not blocks:
        raise ValueError(f"No tetrahedra found in {path}")

    cells = np.vstack([block for block, _ in blocks])
    points = np.asarray(mesh.points, dtype=np.float64)
    xyz = points[cells]
    determinants = np.linalg.det(
        np.stack((xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0], xyz[:, 3] - xyz[:, 0]), axis=2)
    )
    volumes = np.abs(determinants) / 6.0
    tags = np.concatenate(
        [
            np.asarray(block_tags, dtype=np.int64)
            if block_tags is not None
            else np.zeros(len(block), dtype=np.int64)
            for block, block_tags in blocks
        ]
    )
    per_tag = {
        str(int(tag)): {
            "tetrahedra": int(np.count_nonzero(tags == tag)),
            "volume_m3": float(np.sum(volumes[tags == tag])),
        }
        for tag in np.unique(tags)
    }
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "points": int(len(points)),
        "tetrahedra": int(len(cells)),
        "physical_tags": [int(tag) for tag in np.unique(tags)],
        "per_physical_tag": per_tag,
        "total_volume_m3": float(np.sum(volumes)),
        "minimum_abs_tetra_volume_m3": float(np.min(volumes)),
        "zero_or_nonfinite_tetrahedra": int(
            np.count_nonzero((volumes <= 0.0) | ~np.isfinite(volumes))
        ),
        "negative_signed_tetrahedra": int(np.count_nonzero(determinants < 0.0)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("meshes", nargs="+", type=Path)
    parser.add_argument("--expected-volume", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    audits = [audit_mesh(path.resolve()) for path in args.meshes]
    for item in audits:
        item["relative_error_vs_centerline_proxy"] = abs(
            item["total_volume_m3"] - args.expected_volume
        ) / args.expected_volume

    finest_two_change = None
    if len(audits) >= 2:
        v_previous = audits[-2]["total_volume_m3"]
        v_finest = audits[-1]["total_volume_m3"]
        finest_two_change = abs(v_finest - v_previous) / abs(v_finest)

    result = {
        "schema_version": 1,
        "expected_centerline_area_volume_m3": args.expected_volume,
        "meshes": audits,
        "finest_two_relative_volume_change": finest_two_change,
        "acceptance": {
            "four_nonempty_physical_tags_all_meshes": all(
                len(item["physical_tags"]) == 4
                and all(value["tetrahedra"] > 0 for value in item["per_physical_tag"].values())
                for item in audits
            ),
            "finite_nonzero_tetrahedra_all_meshes": all(
                item["zero_or_nonfinite_tetrahedra"] == 0 for item in audits
            ),
            "finest_volume_proxy_relative_error_le_0_05": audits[-1][
                "relative_error_vs_centerline_proxy"
            ]
            <= 0.05,
            "finest_two_relative_volume_change_le_0_02": finest_two_change is not None
            and finest_two_change <= 0.02,
        },
    }
    result["accepted"] = all(result["acceptance"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
