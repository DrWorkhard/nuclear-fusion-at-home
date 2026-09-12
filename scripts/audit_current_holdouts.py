"""Recompute all fixed-current holdout arithmetic from retained Cartesian fields."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.current_diagnostic_audit import error, project
from fusion_baselines.provenance import git_state, write_json_atomic

CODE = (
    "scripts/audit_current_holdouts.py",
    "scripts/current_diagnostic_inputs.py",
    "src/fusion_baselines/current_diagnostic_audit.py",
)


def audit_case(case, original, qualification):
    if (
        case["status"] != "completed"
        or case["source"] != original
        or case["field"] != qualification["field"]
        or len(case["grids"]) != 4
    ):
        raise ValueError("bound complete four-grid current holdout case required")
    checked(case["field"])
    source = json.loads(checked(original["holdouts"]).read_text())
    candidate = json.loads(checked(source["steps"][0]["result"]).read_text())["candidates"][0]
    checks = dict(
        source_grids=case["source_grids"] == candidate["flux"],
        source_field=candidate["field"] == original["field"],
        geometry_inheritance=case["inherited_geometry"] == original["holdouts"],
        no_engineering_admission=case["full_engineering_admission"] is False,
    )
    phi, bmean = [], []
    for i, (resolution, quadrature) in enumerate(((32, 200), (64, 200), (128, 200), (128, 800))):
        row = case["grids"][i]
        if (
            row["status"] != "completed"
            or row["surface_resolution"] != resolution
            or row["coil_quadrature"] != quadrature
        ):
            raise ValueError("all four predeclared ordered grids required")
        with np.load(checked(row["arrays"]), allow_pickle=False) as data:
            if (
                data["B"].shape != (resolution, resolution, 3)
                or data["normal"].shape != data["B"].shape
                or data["points"].shape != (resolution * resolution, 3)
                or not np.isfinite(data["points"]).all()
            ):
                raise ValueError("correct complete finite field/geometry arrays required")
            z = project(data["B"], data["normal"])
            phi.append(0.5 * float(z @ z))
            bmean.append(float(np.mean(np.sqrt(sum(data["B"][..., j] ** 2 for j in range(3))))))
        checks[f"flux_{i}"] = abs(phi[-1] - row["unthresholded_quadratic_flux"]) <= 1e-9 * max(
            phi[-1], 1e-30
        )
        checks[f"Bmean_{i}"] = error(bmean[-1], row["mean_B_magnitude_T"]) <= 1e-12
    physics = dict(
        flux_cut_in=phi[-1] <= 1e-8,
        surface_flux_refinement=abs(phi[2] - phi[1]) <= max(1e-10, 0.01 * phi[1]),
        coil_flux_refinement=abs(phi[3] - phi[2]) <= max(1e-10, 0.01 * phi[2]),
        construction_replay=abs(phi[0] - qualification["fit"]["objective_after"])
        <= 1e-9 * max(qualification["fit"]["objective_after"], 1e-30),
    )
    ratio = phi[-1] / candidate["flux"][-1]["unthresholded_quadratic_flux"]
    checks.update(
        classification=physics == case["checks"]
        and case["field_screen_pass"] == all(physics.values()),
        reported_ratio=error(ratio, case["fine_flux_ratio_to_source"]) <= 1e-12,
    )
    return dict(
        checks=checks,
        all_pass=all(checks.values()),
        physics=physics,
        fine_flux=phi[-1],
        fine_Bmean=bmean[-1],
        fine_flux_ratio_to_source=ratio,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("holdout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable current holdout audit required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.holdout.read_text())
    result = dict(
        repository=git_state(root),
        source=reference(args.holdout),
        code=[reference(root / p) for p in CODE],
        status="running",
        cases=[],
        all_pass=False,
        new_native_calls=0,
        new_fits=0,
    )
    try:
        for ref in [study["protocol"], *study["code"]]:
            checked(ref)
        qualified = json.loads(checked(study["source"]).read_text())
        audit = json.loads(checked(study["audit"]).read_text())
        if (
            study["status"] != "completed"
            or not study["all_eight_grids_completed"]
            or study["used_for_fit_or_selection"] is not False
            or len(study["cases"]) != 2
            or qualified["status"] != "completed"
            or not qualified["all_pass"]
            or audit["status"] != "completed"
            or not audit["all_pass"]
            or audit["source"] != study["source"]
        ):
            raise ValueError("bound completed qualification, audit and all eight holdouts required")
        for row, original, qualification in zip(
            study["cases"], sources(root), qualified["cases"], strict=True
        ):
            result["cases"].append(audit_case(row, original, qualification))
        checks = dict(
            case_audits=all(r["all_pass"] for r in result["cases"]),
            work=study["work"] == dict(B_grid_requests=8, B_points=75776),
            classification=study["all_pass"]
            == all(all(r["physics"].values()) for r in result["cases"]),
            no_engineering_admission=study["full_engineering_admission"] is False,
        )
        result.update(status="completed", checks=checks, all_pass=all(checks.values()))
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
