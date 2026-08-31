#!/usr/bin/env python3
"""Freeze coils, current grouping, and toroidal flux for a VMEC++ holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from simsopt.field import coils_to_makegrid
from stellcoilbench.path_utils import load_surface_with_range
from stellcoilbench.post_processing import load_bfield_from_coils_json
from stellcoilbench.post_processing._coil_io import _get_coils_from_bfield, get_unique_coils


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coils", type=Path, required=True)
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    bfield = load_bfield_from_coils_json(args.coils)
    all_coils = _get_coils_from_bfield(bfield)
    unique_coils = get_unique_coils(all_coils, nfp=2, stellsym=True)
    if len(all_coils) != 16 or len(unique_coils) != 4:
        raise ValueError(
            f"Expected 16 physical and four unique coils; got {len(all_coils)} and "
            f"{len(unique_coils)}"
        )

    coils_file = args.output_dir / "coils.lpqa-v1p1"
    coils_to_makegrid(
        str(coils_file),
        [coil.curve for coil in unique_coils],
        [coil.current for coil in unique_coils],
        groups=[1] * len(all_coils),
        nfp=2,
        stellsym=True,
    )

    surface = load_surface_with_range(str(args.surface), nphi=64, ntheta=128)
    loop = surface.cross_section(0.0, thetas=2000)
    bfield.set_points(loop)
    vector_potential = bfield.A()
    differential = np.roll(loop, -1, axis=0) - loop
    flux_unsigned = abs(
        float(
            np.sum(
                0.5
                * (vector_potential + np.roll(vector_potential, -1, axis=0))
                * differential
            )
        )
    )
    axis_r = float(np.mean(np.hypot(loop[:, 0], loop[:, 1])))
    bfield.set_points(np.array([[axis_r, 0.0, 0.0]]))
    toroidal_sign = float(np.sign(bfield.B()[0, 1])) or 1.0

    xyz = surface.gamma()
    cylindrical_r = np.hypot(xyz[..., 0], xyz[..., 1])
    metadata = {
        "schema_version": 1,
        "source_coils": str(args.coils.resolve()),
        "source_coils_sha256": _sha256(args.coils),
        "source_surface": str(args.surface.resolve()),
        "source_surface_sha256": _sha256(args.surface),
        "coils_file": str(coils_file.resolve()),
        "coils_file_sha256": _sha256(coils_file),
        "nfp": 2,
        "stellarator_symmetry": True,
        "physical_coils": len(all_coils),
        "unique_coils": len(unique_coils),
        "current_groups": 1,
        "extcur_A": [float(unique_coils[0].current.get_value())],
        "unique_coil_currents_A": [
            float(coil.current.get_value()) for coil in unique_coils
        ],
        "phiedge_Wb": flux_unsigned * toroidal_sign,
        "flux_quadrature_points": len(loop),
        "target_extent_m": {
            "r_min": float(np.min(cylindrical_r)),
            "r_max": float(np.max(cylindrical_r)),
            "z_min": float(np.min(xyz[..., 2])),
            "z_max": float(np.max(xyz[..., 2])),
        },
    }
    metadata_path = args.output_dir / "prepared_case.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
