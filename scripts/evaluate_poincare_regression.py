"""Create a quantitative, repeat-tested coil-field Poincare regression."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
from simsopt import load
from simsopt.field.magneticfieldclasses import InterpolatedField
from simsopt.field.tracing import (
    LevelsetStoppingCriterion,
    compute_fieldlines,
)
from simsopt.geo import SurfaceClassifier, SurfaceRZFourier


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def array_collection_hash(collection: list[np.ndarray]) -> str:
    digest = hashlib.sha256()
    for array in collection:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.shape).encode())
        digest.update(str(contiguous.dtype).encode())
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def start_radii(surface: SurfaceRZFourier, nfieldlines: int) -> np.ndarray:
    gamma = surface.gamma()
    phi_index = int(np.argmin(np.abs(surface.quadpoints_phi)))
    points = gamma[phi_index]
    near_midplane = points[np.abs(points[:, 2]) < 0.01]
    if len(near_midplane) < 2:
        raise ValueError("surface grid does not resolve two Z=0 boundary crossings")
    radii = np.linalg.norm(near_midplane[:, :2], axis=1)
    return np.linspace(float(radii.min()) * 1.01, float(radii.max()) * 0.99, nfieldlines)


def build_interpolant(field, surface: SurfaceRZFourier, classifier, n: int):
    gamma = surface.gamma()
    radii = np.linalg.norm(gamma[:, :, :2], axis=2)
    z = gamma[:, :, 2]
    def skip(rs, phis, zs):
        rphiz = np.asarray([rs, phis, zs]).T.copy()
        return list((classifier.evaluate_rphiz(rphiz) < -0.05).flatten())

    return InterpolatedField(
        field,
        2,
        (float(radii.min()), float(radii.max()), n),
        (0, 2 * np.pi / surface.nfp, 2 * n),
        (0, float(z.max()), n // 2)
        if surface.stellsym
        else (float(z.min()), float(z.max()), n // 2),
        True,
        nfp=surface.nfp,
        stellsym=surface.stellsym,
        skip=skip,
    )


def summarize_hits(hits: list[np.ndarray], nfp: int, nplanes: int) -> dict:
    per_line = []
    for line in hits:
        plane_counts = [int(np.sum(line[:, 1] == plane)) for plane in range(nplanes)]
        termination_count = int(np.sum(line[:, 1] < 0))
        section = line[line[:, 1] == 0, 2:5]
        if len(section) >= 4:
            radii = np.linalg.norm(section[:, :2], axis=1)
            rz = np.column_stack((radii, section[:, 2]))
            center = np.mean(rz, axis=0)
            angles = np.unwrap(
                np.arctan2(rz[:, 1] - center[1], rz[:, 0] - center[0])
            )
            slope = float(np.polyfit(np.arange(len(angles)), angles, 1)[0])
            iota_estimate = slope * nfp / (2 * np.pi)
            section_extent = {
                "R_min": float(radii.min()),
                "R_max": float(radii.max()),
                "Z_min": float(section[:, 2].min()),
                "Z_max": float(section[:, 2].max()),
            }
        else:
            iota_estimate = None
            section_extent = None
        per_line.append(
            {
                "plane_hit_counts": plane_counts,
                "termination_count": termination_count,
                "iota_from_phi0_hits": iota_estimate,
                "phi0_extent": section_extent,
            }
        )
    return {
        "per_line": per_line,
        "all_lines_unterminated": all(x["termination_count"] == 0 for x in per_line),
        "minimum_hits_per_plane": min(
            min(x["plane_hit_counts"]) for x in per_line
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nfieldlines", type=int, default=6)
    parser.add_argument("--nplanes", type=int, default=4)
    parser.add_argument("--tmax", type=float, default=2000.0)
    parser.add_argument("--tol", type=float, default=1e-7)
    parser.add_argument("--surface-grid", type=int, default=64)
    parser.add_argument("--interpolation-n", type=int, default=20)
    parser.add_argument("--direct", action="store_true")
    args = parser.parse_args()

    field = load(str(args.field))
    surface = SurfaceRZFourier.from_vmec_input(
        str(args.surface),
        range="full torus",
        nphi=args.surface_grid,
        ntheta=args.surface_grid,
    )
    radii = start_radii(surface, args.nfieldlines)
    z0 = np.zeros(args.nfieldlines)
    planes = np.arange(args.nplanes) * 2 * np.pi / (args.nplanes * surface.nfp)
    classifier = SurfaceClassifier(surface, h=0.04 * surface.major_radius(), p=2)
    field_to_trace = (
        field
        if args.direct
        else build_interpolant(field, surface, classifier, args.interpolation_n)
    )

    repeats = []
    raw = []
    for _ in range(2):
        started = time.perf_counter()
        trajectories, hits = compute_fieldlines(
            field_to_trace,
            radii,
            z0,
            tmax=args.tmax,
            tol=args.tol,
            phis=planes,
            stopping_criteria=[LevelsetStoppingCriterion(classifier.dist)],
        )
        repeats.append(
            {
                "runtime_seconds": time.perf_counter() - started,
                "trajectory_hash": array_collection_hash(trajectories),
                "poincare_hits_hash": array_collection_hash(hits),
                "trajectory_points_per_line": [len(line) for line in trajectories],
                "poincare_rows_per_line": [len(line) for line in hits],
                "summary": summarize_hits(hits, surface.nfp, args.nplanes),
            }
        )
        raw.append((trajectories, hits))

    record = {
        "schema_version": 1,
        "claim_class": "reproduced_and_repeat_checked",
        "software": {
            "simsopt": version("simsopt"),
            "python": platform.python_version(),
        },
        "inputs": {
            "field_sha256": sha256_file(args.field),
            "surface_sha256": sha256_file(args.surface),
            "nfp": surface.nfp,
            "start_R": radii.tolist(),
            "start_Z": z0.tolist(),
            "section_phi_radians": planes.tolist(),
            "nfieldlines": args.nfieldlines,
            "tmax": args.tmax,
            "tol": args.tol,
            "surface_grid": [args.surface_grid, args.surface_grid],
            "field_evaluation": "direct_biot_savart"
            if args.direct
            else "quadratic_interpolation",
            "interpolation_grid": None
            if args.direct
            else [
                args.interpolation_n,
                2 * args.interpolation_n,
                args.interpolation_n // 2,
            ],
        },
        "repeats": repeats,
        "bit_identical_trajectories": bool(
            all(
                np.array_equal(first, second)
                for first, second in zip(raw[0][0], raw[1][0], strict=True)
            )
        ),
        "bit_identical_poincare_hits": bool(
            all(
                np.array_equal(first, second)
                for first, second in zip(raw[0][1], raw[1][1], strict=True)
            )
        ),
        "interpretation_limits": [
            "This is a deterministic regression of the optimized filament-coil "
            "field, not authoritative W7-X coil validation.",
            "The iota estimate is a diagnostic linear fit to section-hit angles "
            "and is not used as an equilibrium-quality certificate.",
            "Interpolation and tracing resolution require convergence checks "
            "before a physics claim.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
