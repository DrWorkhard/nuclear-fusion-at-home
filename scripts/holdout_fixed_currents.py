"""All four frozen field holdouts for each current minimizer, without refitting."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.flux_metrics import quadratic_flux
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check

GRIDS = ((32, 200), (64, 200), (128, 200), (128, 800))
CODE = (
    "scripts/holdout_fixed_currents.py",
    "scripts/current_diagnostic_inputs.py",
    "scripts/validate_normalized_candidates.py",
    "src/fusion_baselines/flux_metrics.py",
)


def native_components():
    from simsopt import load
    from simsopt.geo import SurfaceRZFourier
    from validate_normalized_candidates import refined_field

    return load, SurfaceRZFourier, refined_field


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable current holdout paths required")
    root = Path(__file__).resolve().parents[1]
    study, audit = json.loads(args.study.read_text()), json.loads(args.audit.read_text())
    selected = sources(root)
    if (
        study["status"] != "completed"
        or not study["all_pass"]
        or len(study["cases"]) != 2
        or audit["status"] != "completed"
        or not audit["all_pass"]
        or audit["source"] != reference(args.study)
        or [r["source"] for r in study["cases"]] != selected
        or [r["field"] for r in audit["cases"]] != [r["field"] for r in study["cases"]]
    ):
        raise ValueError("audited two-minimizer qualification required")
    for ref in [study["protocol"], *study["code"], *audit["code"]]:
        checked(ref)
    for path in [args.study, args.audit, *(root / p for p in CODE)]:
        require_committed(root, path)
    report = dict(
        repository=git_state(root),
        source=reference(args.study),
        audit=reference(args.audit),
        code=[reference(root / p) for p in CODE],
        protocol=study["protocol"],
        status="running",
        all_pass=False,
        cases=[],
        used_for_fit_or_selection=False,
        full_engineering_admission=False,
        disk_preflight=space_check(root, 3 * GIB),
        work=dict(B_grid_requests=0, B_points=0),
    )
    args.raw.mkdir(parents=True)
    try:
        load, SurfaceRZFourier, refined_field = native_components()
        for row, original in zip(study["cases"], selected, strict=True):
            holdout = json.loads(checked(original["holdouts"]).read_text())
            prior = json.loads(checked(holdout["steps"][0]["result"]).read_text())["candidates"][0]
            if prior["field"] != original["field"] or [
                (r["surface_resolution"], r["coil_quadrature"]) for r in prior["flux"]
            ] != list(GRIDS):
                raise ValueError("same selected source and original four field grids required")
            field = load(str(checked(row["field"])))
            target = dict(
                label=original["label"],
                field=row["field"],
                source=original,
                status="running",
                grids=[],
                source_grids=prior["flux"],
                inherited_geometry=original["holdouts"],
                full_engineering_admission=False,
            )
            report["cases"].append(target)
            for resolution, quadrature in GRIDS:
                space_check(root, 2 * GIB)
                grid = dict(
                    surface_resolution=resolution, coil_quadrature=quadrature, status="running"
                )
                target["grids"].append(grid)
                write_json_atomic(args.output, report)
                surface = SurfaceRZFourier.from_vmec_input(
                    str(checked(row["preparation"]["surface"])),
                    range="half period",
                    nphi=resolution,
                    ntheta=resolution,
                )
                evaluated = refined_field(field) if quadrature == 800 else field
                if len(evaluated.coils) != 16 or any(
                    len(c.curve.quadpoints) != quadrature for c in evaluated.coils
                ):
                    raise ValueError("unchanged16-coil holdout quadrature required")
                normal, points = surface.normal().copy(), surface.gamma().reshape(-1, 3).copy()
                evaluated.set_points(points)
                report["work"]["B_grid_requests"] += 1
                report["work"]["B_points"] += len(points)
                write_json_atomic(args.output, report)
                b = evaluated.B().reshape(normal.shape).copy()
                path = args.raw / f"{original['label']}-n{resolution}-q{quadrature}.npz"
                with path.open("xb") as stream:
                    np.savez_compressed(stream, B=b, normal=normal, points=points)
                grid.update(
                    arrays=reference(path),
                    status="completed",
                    unthresholded_quadratic_flux=quadratic_flux(b, normal),
                    mean_B_magnitude_T=float(np.mean(np.linalg.norm(b, axis=-1))),
                )
                print(
                    original["label"],
                    resolution,
                    quadrature,
                    grid["unthresholded_quadratic_flux"],
                    flush=True,
                )
                write_json_atomic(args.output, report)
            phi = [r["unthresholded_quadratic_flux"] for r in target["grids"]]
            checks = dict(
                flux_cut_in=phi[-1] <= 1e-8,
                surface_flux_refinement=abs(phi[2] - phi[1]) <= max(1e-10, 0.01 * phi[1]),
                coil_flux_refinement=abs(phi[3] - phi[2]) <= max(1e-10, 0.01 * phi[2]),
                construction_replay=abs(phi[0] - row["fit"]["objective_after"])
                <= 1e-9 * max(row["fit"]["objective_after"], 1e-30),
            )
            target.update(
                status="completed",
                checks=checks,
                field_screen_pass=all(checks.values()),
                fine_flux_ratio_to_source=phi[-1]
                / prior["flux"][-1]["unthresholded_quadratic_flux"],
            )
        report.update(
            status="completed",
            all_eight_grids_completed=True,
            all_pass=all(r["field_screen_pass"] for r in report["cases"]),
        )
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
