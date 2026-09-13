"""Replay exactly32 frozen B grids and qualify two complete field matrices."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_curvature_inputs import sources
from qualify_fixed_currents import error, native_setup, versions
from run_jac_scaled_study import require_committed

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.counted_field_views import CountedBatchField, CountedLocalField, increment
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.field_conditioning import conditioning
from fusion_baselines.local_field_jacobian import local_field_jacobian
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.quadratic_flux_model import quadratic_flux_model
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_current_affine import current_map
from fusion_baselines.spatial_flux import spatial_flux

CODE = (
    "scripts/evaluate_geometric_curvature.py",
    "scripts/geometric_curvature_inputs.py",
    "scripts/geometric_descent_inputs.py",
    "scripts/current_diagnostic_inputs.py",
    "scripts/qualify_fixed_currents.py",
    "scripts/prepare_upstream_start.py",
    "src/fusion_baselines/direct_constraints.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_current_affine.py",
    "src/fusion_baselines/spatial_flux.py",
    "src/fusion_baselines/batched_field_jacobian.py",
    "src/fusion_baselines/local_field_jacobian.py",
    "src/fusion_baselines/counted_field_views.py",
    "src/fusion_baselines/quadratic_flux_model.py",
    "src/fusion_baselines/field_conditioning.py",
)


def save(path, **data):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **data)
    return reference(path)


def json_arrays(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: json_arrays(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_arrays(v) for v in value]
    return value


def installed(root):
    path = root / "evidence/spatial-flux-batched-v1-retry1.json"
    old = json.loads(path.read_text())
    if not old["all_pass"] or old["status"] != "completed":
        raise ValueError("previous complete native matrix qualification required")
    require_committed(root, path)
    for ref in old["installed_sources"]:
        checked(ref)
    return dict(qualification=reference(path), sources=old["installed_sources"])


def analyze(z, batch_z, matrix, local, steps, directions, gradient, a, columns, fluxes):
    errors = dict(
        matrix=error(matrix, local),
        projection=error(batch_z, z[0]),
        gradient=error(matrix.T @ z[0] / 1e-6, gradient),
        uncoupled_gradient=error(matrix.T @ batch_z / 1e-6, gradient),
        current=error(matrix[:, columns], a),
        batch_flux=float(abs(float(batch_z @ batch_z / 2) - fluxes[0]) / abs(fluxes[0])),
    )
    checks = {
        key: value <= (1e-12 if key == "current" else 1e-10)
        for key, value in errors.items()
        if key != "uncoupled_gradient"
    }
    trials = []
    for i, (step, direction) in enumerate(zip(steps, directions, strict=True)):
        fd_errors = [
            error((z[1 + 5 * i + 2 * j] - z[2 + 5 * i + 2 * j]) / (2 * eps), matrix @ direction)
            for j, eps in enumerate((1e-7, 1e-8))
        ]
        model = quadratic_flux_model(z[0], matrix, step, z[5 + 5 * i])
        checks[f"direction_{i}_fd"] = max(fd_errors) <= 1e-6
        checks[f"direction_{i}_identities"] = (
            max(model["matrix_identity_error"], model["remainder_identity_error"]) <= 1e-10
        )
        trials.append(dict(fd_errors=fd_errors, model=model))
    return dict(
        errors=errors,
        checks=checks,
        trials=trials,
        conditioning=json_arrays(conditioning(z[0], matrix, columns, steps)),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable curvature study paths required")
    root = Path(__file__).resolve().parents[1]
    selected, frozen, bindings = sources(root)
    protocol = root / "docs/optimization/GEOMETRIC_CURVATURE_PROTOCOL.md"
    for path in [protocol, *(root / p for p in CODE)]:
        require_committed(root, path)
    report = dict(
        status="running",
        all_pass=False,
        physical_admission=False,
        repository=git_state(root),
        protocol=reference(protocol),
        prerequisites=bindings,
        code=[reference(root / p) for p in CODE],
        installed=installed(root),
        versions=versions(),
        disk_preflight=space_check(root, 3 * GIB),
        cases=[],
    )
    args.raw.mkdir(parents=True)
    row = local_view = raw = None
    try:
        for source, frozen_data in zip(selected, frozen, strict=True):
            space_check(root, 2 * GIB)
            raw = args.raw / source["label"]
            raw.mkdir()
            row = dict(source=source, status="preparing", all_pass=False, events=[], work={})
            local_view = None
            report["cases"].append(row)
            write_json_atomic(args.output, report)
            ctx, prep, full = native_setup(root, raw)
            if any(
                prep[k] != source["preparation"][k]
                for k in (
                    "surface",
                    "case",
                    "thresholds",
                    "guarded_search_targets",
                    "canonical_total",
                )
            ):
                raise ValueError("canonical curvature problem changed")
            template = json.loads(checked(prep["normalized_start"]).read_text())
            _, permutation, owners = mapped_start(
                json.loads(checked(source["field"]).read_text()),
                template,
                source["names"],
                prep["degrees_of_freedom"],
                frozen_data["points"][0],
            )
            backend = DirectConstraintBackend(ctx, full)  # setup only; zero evaluate() calls
            points = frozen_data["points"][:, permutation]
            steps = frozen_data["steps"][:, permutation]
            directions = frozen_data["directions"][:, permutation]
            gradient = frozen_data["gradient"][permutation]
            columns = current_map(template, backend.names)["columns"]
            row.update(
                names=backend.names,
                preparation=prep,
                owner_map=owners,
                source_indices_in_target_order=permutation.tolist(),
            )
            row["inputs"] = save(
                raw / "inputs.npz",
                points=points,
                steps=steps,
                rounded_displacements=points[[5, 10, 15]] - points[0],
                directions=directions,
                gradient=gradient,
                A=frozen_data["A"],
                columns=columns,
                fluxes=frozen_data["fluxes"],
                observation_points=backend.points,
                normal=backend.normal,
                weights=backend.weights,
            )
            residuals = []
            for index, point in enumerate(points):
                space_check(root, 2 * GIB)
                event = dict(
                    index=index,
                    kind=frozen_data["kinds"][index],
                    status="running",
                    source_bundle=frozen_data["bundles"][index],
                    x=point.tolist(),
                )
                row["events"].append(event)
                ctx.Jf.x = point.copy()
                backend.field.set_points(backend.points.copy())
                increment(row["work"], "grid_B_requests")
                write_json_atomic(args.output, report)
                b = backend.field.B().reshape(backend.normal.shape).copy()
                increment(row["work"], "grid_B_completed")
                event["field_arrays"] = save(raw / f"field-{index}.npz", B=b, x=point)
                z = spatial_flux(b, backend.normal)
                residuals.append(z)
                event["residual_arrays"] = save(raw / f"residual-{index}.npz", z=z)
                event.update(status="completed", raw_flux=float(z @ z / 2))
                event["flux_replay_error"] = float(
                    abs(event["raw_flux"] - frozen_data["fluxes"][index])
                    / abs(frozen_data["fluxes"][index])
                )
                event["all_pass"] = event["flux_replay_error"] <= 1e-10
                write_json_atomic(args.output, report)
                if index == 0:
                    increment(row["work"], "batch_assembly_requests")
                    write_json_atomic(args.output, report)
                    batch_z, matrix = batched_field_jacobian(
                        CountedBatchField(backend.field, row["work"]),
                        ctx.Jf,
                        backend.points,
                        backend.weights,
                    )
                    increment(row["work"], "batch_assembly_completed")
                    row["batch_arrays"] = save(raw / "batch.npz", z=batch_z, D=matrix)
                    write_json_atomic(args.output, report)
                    local_view = CountedLocalField(backend.field, row["work"])
                    local = local_field_jacobian(
                        local_view, ctx.Jf, backend.points, backend.weights
                    )
                    row["local_arrays"] = save(
                        raw / "local.npz",
                        D=local,
                        observation_points_after=backend.field.get_points_cart_ref().copy(),
                    )
                    row["observation_points_restored"] = bool(
                        np.array_equal(backend.field.get_points_cart_ref(), backend.points)
                    )
                    write_json_atomic(args.output, report)
            row.update(
                analyze(
                    np.asarray(residuals),
                    batch_z,
                    matrix,
                    local,
                    steps,
                    directions,
                    gradient,
                    frozen_data["A"],
                    columns,
                    frozen_data["fluxes"],
                )
            )
            row["checks"].update(
                observation_points_restored=row["observation_points_restored"],
                all_fluxes=all(e["all_pass"] for e in row["events"]),
                current_projection=row["conditioning"]["current_projection_qualified"],
            )
            row.update(
                status="completed",
                all_pass=all(row["checks"].values()),
                usefulness_pass=all(t["model"]["usefulness_pass"] for t in row["trials"]),
            )
            write_json_atomic(args.output, report)
        report.update(
            status="completed",
            all_pass=all(r["all_pass"] for r in report["cases"]),
            usefulness_pass=all(r["usefulness_pass"] for r in report["cases"]),
        )
    except Exception as exc:
        if row is not None:
            row.update(status="error", error=f"{type(exc).__name__}: {exc}")
            if local_view is not None and "local_arrays" not in row:
                row["partial_local_arrays"] = save(
                    raw / "partial-local.npz",
                    rows=np.asarray(local_view.rows),
                    observation_points_after=local_view.get_points_cart_ref().copy(),
                )
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({k: report[k] for k in ("status", "all_pass", "usefulness_pass")}))
    return 0 if report["all_pass"] and report["usefulness_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
