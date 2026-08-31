#!/usr/bin/env python3
"""Run the frozen scikit-fem convergence study on caller-provided coil meshes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from stellcoilbench.post_processing import load_bfield_from_coils_json
from stellcoilbench.post_processing._coil_io import _get_coils_from_bfield, get_unique_coils
from stellcoilbench.structural_analysis import run_structural_analysis

METRICS = (
    "max_displacement_m",
    "mean_displacement_m",
    "p95_von_mises_stress_Pa",
    "mean_von_mises_stress_Pa",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_one(coils: list, bfield, mesh: Path, output_dir: Path) -> dict:
    started = time.perf_counter()
    result = run_structural_analysis(
        coils=coils,
        bs=bfield,
        output_dir=output_dir,
        msh_path=mesh,
        width=0.05,
        height=0.05,
        backend="skfem",
        use_spring_bc=False,
        nfp=2,
        stellsym=True,
    )
    result["elapsed_s"] = time.perf_counter() - started
    result["mesh_path"] = str(mesh.resolve())
    result["mesh_sha256"] = _sha256(mesh)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coils", type=Path, required=True)
    parser.add_argument("--mesh-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resolutions", default="0.05,0.04,0.03,0.02")
    parser.add_argument("--repeat-finest", action="store_true")
    args = parser.parse_args()
    resolutions = [float(value) for value in args.resolutions.split(",")]
    bfield = load_bfield_from_coils_json(args.coils)
    coils = get_unique_coils(_get_coils_from_bfield(bfield), nfp=2, stellsym=True)
    if len(coils) != 4:
        raise ValueError(f"Expected four unique coils, found {len(coils)}")

    runs = []
    for resolution in resolutions:
        resolution_name = f"res_{resolution:.3f}".replace(".", "_")
        mesh = args.mesh_root / resolution_name / "coils_structured.msh"
        result = _run_one(coils, bfield, mesh, args.mesh_root / resolution_name / "structural")
        result["target_h_m"] = resolution
        runs.append(result)
        print(json.dumps({key: result.get(key) for key in (*METRICS, "elapsed_s")}, indent=2))

    relative_changes = {
        metric: abs(runs[-1][metric] - runs[-2][metric]) / abs(runs[-1][metric])
        for metric in METRICS
    }
    repeat = None
    repeat_equal = None
    if args.repeat_finest:
        resolution = resolutions[-1]
        resolution_name = f"res_{resolution:.3f}".replace(".", "_")
        mesh = args.mesh_root / resolution_name / "coils_structured.msh"
        repeat = _run_one(
            coils, bfield, mesh, args.mesh_root / resolution_name / "structural_repeat"
        )
        repeat_equal = {
            metric: bool(np.array_equal(runs[-1][metric], repeat[metric])) for metric in METRICS
        }

    finite = all(
        not run.get("skipped", False)
        and all(np.isfinite(float(run[metric])) for metric in METRICS)
        for run in runs
    )
    acceptance = {
        "all_runs_finite": finite,
        "finest_step_relative_change_below_0_10": all(
            value < 0.10 for value in relative_changes.values()
        ),
    }
    evidence = {
        "schema_version": 1,
        "source_coils": str(args.coils.resolve()),
        "source_coils_sha256": _sha256(args.coils),
        "backend": "scikit-fem",
        "backend_version": importlib.metadata.version("scikit-fem"),
        "element": "P1 tetrahedral displacement",
        "support_model_actual": "fixed all components on lowest 15 percent z-range per coil",
        "youngs_modulus_Pa": 100.0e9,
        "poisson_ratio": 0.3,
        "width_m": 0.05,
        "height_m": 0.05,
        "runs": runs,
        "finest_step_relative_changes": relative_changes,
        "finest_repeat": repeat,
        "finest_repeat_metrics_bitwise_equal": repeat_equal,
        "acceptance": acceptance,
        "accepted": all(acceptance.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"relative_changes": relative_changes, "acceptance": acceptance}, indent=2))
    return 0 if evidence["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
