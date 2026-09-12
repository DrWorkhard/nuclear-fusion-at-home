"""Static independent reconstruction of five fixed upstream LPQA fields."""

import argparse
import json
from pathlib import Path

import numpy as np
from audit_coil_geometry import base_fourier, curve_points
from run_jac_scaled_study import require_closed, require_committed
from simsopt import load
from simsopt.field import BiotSavart, coils_via_symmetries
from simsopt.geo import CurveXYZFourier, SurfaceRZFourier
from validate_normalized_candidates import check_candidate

from fusion_baselines.curvature_bounds import derivatives
from fusion_baselines.filament_field import filament_field
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def copy_quadrature(field, n):
    if len(field.coils) != 16:
        raise ValueError("exactly16 physical coils required")
    curves = []
    for coil in field.coils[:4]:
        if hasattr(coil.curve, "rotmat") or np.shape(coil.curve.local_full_x) != (51,):
            raise ValueError("four direct order8 base curves required")
        curve = CurveXYZFourier(n, 8)
        curve.local_full_x = coil.curve.local_full_x.copy()
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


def independent_tangents(curve, parameter):
    if hasattr(curve, "rotmat"):
        return independent_tangents(curve.curve, parameter) @ np.asarray(curve.rotmat)
    return derivatives(base_fourier(curve)[0], parameter)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable output/raw paths required")
    root = Path(__file__).resolve().parents[1]
    previous = root / "evidence/natural-auglag-jac-v1-validation/summary.json"
    prior = json.loads(previous.read_text())
    require_closed(prior)
    require_committed(root, previous)
    require_committed(root, root / "docs/optimization/NATURAL_AUGLAG_JAC_RESULTS.md")
    if prior["study"] != reference(root / "evidence/natural-auglag-jac-v1/summary.json"):
        raise ValueError("closed preceding scaling study required")
    for phase in prior["steps"]:
        checked(phase["result"])
    ipath = root / "evidence/upstream-lpqa-inventory-v1.json"
    apath = root / "evidence/upstream-lpqa-inventory-v1-audit.json"
    inventory, audit = json.loads(ipath.read_text()), json.loads(apath.read_text())
    if audit["all_pass"] is not True or audit["source"] != reference(ipath):
        raise ValueError("passing bound inventory audit required")
    if len(inventory["shortlist"]) != 5:
        raise ValueError("exactly five preregistered endpoints required")
    surface = root / "external/stellcoilbench/plasma_surfaces/input.LandremanPaul2021_QA"
    if sha256_file(surface) != "4c6ba4bc391a69b5b6a5e84ff82df9b0ce92e20c42f2a47f89a9283fd5bc3458":
        raise ValueError("LPQA target changed")
    points = (
        SurfaceRZFourier.from_vmec_input(str(surface), range="half period", nphi=8, ntheta=8)
        .gamma()
        .reshape(-1, 3)
    )
    scale = 10.100286074838271
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        status="running",
        inventory=reference(ipath),
        inventory_audit=reference(apath),
        prior_validation=reference(previous),
        surface=reference(surface),
        a0=scale,
        candidates=[],
        full_engineering_admission=False,
        used_for_optimizer_feedback=False,
        protocol=reference(root / "docs/optimization/UPSTREAM_LPQA_RECONSTRUCTION_PROTOCOL.md"),
        code=[
            reference(root / p)
            for p in (
                "scripts/reconstruct_upstream_lpqa.py",
                "scripts/validate_normalized_candidates.py",
                "scripts/audit_coil_geometry.py",
                "src/fusion_baselines/filament_field.py",
                "src/fusion_baselines/curvature_bounds.py",
                "src/fusion_baselines/flux_metrics.py",
            )
        ],
    )
    try:
        write_json_atomic(args.output, report)
        for number, source_path in enumerate(inventory["shortlist"], 1):
            row = next(r for r in inventory["rows"] if r["source"]["path"] == source_path)
            fields = []
            candidate = dict(
                source_metadata=row["source"],
                source_field=row["selected_field"],
                reported=row["reported"],
                status="running",
                independent_fields=fields,
                native_crosscheck_attempts=0,
                numpy_crosscheck_attempts=0,
                holdout_started=False,
            )
            report["candidates"].append(candidate)
            write_json_atomic(args.output, report)
            checked(row["source"])
            source = checked(row["selected_field"])
            original = load(str(source))
            field = copy_quadrature(original, 200)
            currents = np.array([c.current.get_value() for c in original.coils])
            new_currents = np.array([c.current.get_value() for c in field.coils])
            parameter = np.arange(257) / 257
            a = np.asarray([curve_points(c.curve, parameter) for c in original.coils])
            b = np.asarray([curve_points(c.curve, parameter) for c in field.coils])
            position_error = float(np.max(np.abs(a - b)) / max(1, np.max(np.abs(a))))
            identity = dict(
                positions=position_error <= 1e-12,
                copy_currents=np.array_equal(currents, new_currents),
                reported_base_currents=bool(
                    np.allclose(
                        currents[:4], row["reported"]["final_current_per_coil"], rtol=1e-12, atol=0
                    )
                ),
            )
            candidate.update(
                identity_checks=identity,
                maximum_position_error=position_error,
                original_current_sum=float(currents[:4].sum()),
            )
            if not all(identity.values()):
                raise ValueError(f"source identity failed: {identity}")
            folder = args.raw / f"candidate-{number}"
            folder.mkdir()
            field_path = folder / "field-200.json"
            field.save(str(field_path))
            for n in (200, 800):
                evaluated = field if n == 200 else copy_quadrature(original, n)
                t = np.arange(n) / n
                pos = np.asarray([curve_points(c.curve, t) for c in evaluated.coils])
                vel = np.asarray([independent_tangents(c.curve, t) for c in evaluated.coils])
                candidate["numpy_crosscheck_attempts"] += 1
                own = filament_field(points, pos, vel, currents)
                evaluated.set_points(points)
                candidate["native_crosscheck_attempts"] += 1
                native = evaluated.B().copy()
                error = float(
                    np.max(
                        np.linalg.norm(own - native, axis=1)
                        / np.maximum(1, np.linalg.norm(native, axis=1))
                    )
                )
                arrays = folder / f"field-crosscheck-{n}.npz"
                with arrays.open("xb") as stream:
                    np.savez_compressed(
                        stream,
                        points=points,
                        independent=own,
                        native=native,
                        currents=currents,
                        positions=pos,
                        tangents=vel,
                    )
                fields.append(
                    dict(
                        resolution=n,
                        maximum_normalized_error=error,
                        all_pass=bool(np.isfinite(error) and error <= 1e-12),
                        arrays=reference(arrays),
                    )
                )
                if not fields[-1]["all_pass"]:
                    write_json_atomic(folder / "failed-field-crosscheck.json", fields[-1])
                    raise ValueError("independent field crosscheck failed")
            print(f"Reconstructing selected upstream candidate{number}: {source}", flush=True)
            candidate["holdout_started"] = True
            write_json_atomic(args.output, report)
            result = check_candidate(field_path, surface, scale)
            candidate.update(status="completed", **result)
            write_json_atomic(args.output, report)
        report.update(
            status="completed",
            all_grid_screens_pass=all(
                c["bounded_geometry_flux_screen_pass"] for c in report["candidates"]
            ),
            additional_native_field_grids=30,
            independent_numpy_field_grids=10,
        )
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"all_grid_screens_pass": report["all_grid_screens_pass"]}))


if __name__ == "__main__":
    main()
