"""Two preregistered current-only affine minimizers at exactly frozen coil shapes."""

import argparse
import importlib.metadata
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, predecessor, reference, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.affine_current_audit import qr_fit
from fusion_baselines.affine_current_fit import fit_affine
from fusion_baselines.current_field_probes import central_probes
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.selected_start import initial_error, mapped_start
from fusion_baselines.serialized_current_affine import current_map
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state
from fusion_baselines.spatial_flux import spatial_flux

CODE = (
    "scripts/qualify_fixed_currents.py",
    "scripts/current_diagnostic_inputs.py",
    "scripts/prepare_upstream_start.py",
    "src/fusion_baselines/current_field_probes.py",
    "src/fusion_baselines/affine_current_fit.py",
    "src/fusion_baselines/affine_current_audit.py",
    "src/fusion_baselines/serialized_current_affine.py",
    "src/fusion_baselines/current_normalization.py",
    "src/fusion_baselines/refined_curvature.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_field_state.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/direct_constraints.py",
    "src/fusion_baselines/spatial_flux.py",
)


def error(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching finite current diagnostic arrays required")
    return float(np.max(abs(a - b) / np.maximum(1, abs(b))))


def versions():
    return {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "simsopt")}


def native_setup(root, raw):
    from prepare_upstream_start import prepare
    from simsopt.geo import SurfaceRZFourier

    ctx, prep = prepare(root, raw)
    full = SurfaceRZFourier.from_vmec_input(
        str(checked(prep["surface"])), range="full torus", nphi=64, ntheta=64
    )
    return ctx, prep, full


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable current qualification paths required")
    root = Path(__file__).resolve().parents[1]
    previous, selected = predecessor(root), sources(root)
    protocol = root / "docs/optimization/FIXED_GEOMETRY_CURRENT_PROTOCOL.md"
    for path in [protocol, *(root / p for p in CODE)]:
        require_committed(root, path)
    disk = space_check(root, 3 * GIB)
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        status="running",
        all_pass=False,
        cases=[],
        predecessor=previous,
        protocol=reference(protocol),
        disk_preflight=disk,
        code=[reference(root / p) for p in CODE],
        physical_admission=False,
        versions=versions(),
    )
    active = None
    try:
        for original in selected:
            space_check(root, 2 * GIB)
            raw = args.raw / original["label"]
            raw.mkdir()
            row = dict(source=original, status="preparing", all_pass=False)
            active = dict(row=row, raw=raw, arrays={}, backend=None, requests=0, svd=0, qr=0)
            report["cases"].append(row)
            write_json_atomic(args.output, report)
            ctx, prep, full = native_setup(root, raw)
            if any(
                prep[k] != original["preparation"][k]
                for k in (
                    "surface",
                    "case",
                    "thresholds",
                    "guarded_search_targets",
                    "canonical_total",
                )
            ):
                raise ValueError("original physical problem changed")
            before_doc = json.loads(checked(original["field"]).read_text())
            template = json.loads(checked(prep["normalized_start"]).read_text())
            with np.load(checked(original["arrays"]), allow_pickle=False) as data:
                x, permutation, owners = mapped_start(
                    before_doc, template, original["names"], prep["degrees_of_freedom"], data["x"]
                )
                expected = data["values"].copy()
            backend = DirectConstraintBackend(ctx, full)
            active["backend"] = backend
            mapping = current_map(template, backend.names)
            columns = mapping["columns"]
            before_values, before_jac, _ = backend.evaluate(x)
            active["arrays"].update(
                x=x.copy(), before_values=before_values.copy(), before_jacobian=before_jac.copy()
            )
            checks = dict(source_replay=initial_error(before_values, expected) <= 1e-12)

            def field(proposal, ctx=ctx, backend=backend, active=active):
                active["requests"] += 1
                key = f"field_request_{active['requests']}"
                active["arrays"][key + "_x"] = proposal.copy()
                ctx.Jf.x = proposal.copy()
                backend.field.set_points(backend.points)
                value = backend.field.B().reshape(backend.normal.shape).copy()
                active["arrays"][key + "_B"] = value.copy()
                return value

            probes = central_probes(x, columns, field)
            a = np.stack([spatial_flux(v, backend.normal) for v in probes["slopes"]], axis=1)
            z = spatial_flux(probes["before"], backend.normal)
            active["svd"] += 1
            fit = fit_affine(z, a)
            checks.update(
                affine_probes=probes["affine_pass"],
                rank_condition_stationarity=fit["qualified"],
                native_current_gradient=error(a.T @ z / 1e-6, before_jac[0, columns]) <= 1e-10,
            )
            arrays = active["arrays"]
            arrays.update(
                x=x,
                columns=columns,
                before_values=before_values,
                before_jacobian=before_jac,
                normal=backend.normal,
                points=backend.points,
                B_before=probes["before"],
                B_probes=probes["pairs"],
                probe_points=probes["proposals"],
                B_slopes=probes["slopes"],
                A=a,
                z0=z,
                singular_values=fit["singular_values"],
            )
            row.update(
                preparation=prep,
                source_indices_in_target_order=permutation.tolist(),
                owner_map=owners,
                names=backend.names,
                columns=columns.tolist(),
                checks=checks,
                affine_errors=probes["errors"].tolist(),
                fit={
                    k: v
                    for k, v in fit.items()
                    if k not in ("delta", "residual", "singular_values")
                },
            )
            if all(checks.values()):
                active["qr"] += 1
                independent = qr_fit(z, a)
                checks["qr_delta"] = error(independent["delta"], fit["delta"]) <= 1e-10
                checks["qr_stationarity"] = independent["normal_error"] <= 1e-10
                arrays.update(
                    delta=fit["delta"],
                    residual=fit["residual"],
                    qr_delta=independent["delta"],
                    qr_residual=independent["residual"],
                )
                row["qr_normal_error"] = independent["normal_error"]
                if all(checks.values()):
                    after_x = x.copy()
                    after_x[columns] += fit["delta"]
                    after_values, after_jac, _ = backend.evaluate(after_x)
                    after_b = field(after_x)
                    predicted = probes["before"] + np.tensordot(fit["delta"], probes["slopes"], 1)
                    checks["native_B_prediction"] = error(after_b, predicted) <= 1e-12
                    raw_flux_error = float(
                        abs(after_values[0] * 1e-6 - fit["objective_after"])
                        / max(fit["objective_after"], 1e-30)
                    )
                    checks["native_flux_prediction"] = raw_flux_error <= 1e-9
                    checks["unchanged_geometric_rows"] = (
                        error(after_values[1:], before_values[1:]) <= 1e-12
                    )
                    after_path = raw / "current_minimizer.json"
                    ctx.Jf.field.save(str(after_path))
                    after_doc = json.loads(after_path.read_text())
                    state_before, state_after = (
                        serialized_state(before_doc),
                        serialized_state(after_doc),
                    )
                    checks["geometric_identity"] = all(
                        np.array_equal(state_before[k], state_after[k])
                        for k in ("coefficients", "base_regularizations")
                    )
                    checks["named_after"] = np.array_equal(
                        after_x, named_serialized_values(after_doc, backend.names)
                    )
                    current_map(after_doc, backend.names)
                    checks["after_currents"] = (
                        error(
                            state_after["currents"],
                            mapping["matrix"] @ after_x[columns] + mapping["constant"],
                        )
                        <= 1e-12
                    )
                    arrays.update(
                        after_x=after_x,
                        after_values=after_values,
                        after_jacobian=after_jac,
                        B_after=after_b,
                    )
                    row.update(
                        field=reference(after_path),
                        native_flux_relative_error=raw_flux_error,
                        physical_currents_before=state_before["currents"].tolist(),
                        physical_currents_after=state_after["currents"].tolist(),
                        mean_B_before=float(np.mean(np.linalg.norm(probes["before"], axis=-1))),
                        mean_B_after=float(np.mean(np.linalg.norm(after_b, axis=-1))),
                    )
            arrays_path = raw / "qualification.npz"
            with arrays_path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            row.update(
                status="completed",
                arrays=reference(arrays_path),
                all_pass=all(checks.values()),
                work=dict(
                    direct=backend.work.copy(),
                    additional_B_grid_requests=active["requests"],
                    svd_fits=active["svd"],
                    qr_fits=active["qr"],
                ),
            )
            print(original["label"], row["all_pass"], fit.get("objective_after"), flush=True)
            write_json_atomic(args.output, report)
        report.update(status="completed", all_pass=all(r["all_pass"] for r in report["cases"]))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        if active is not None:
            row = active["row"]
            row.update(
                status="error",
                all_pass=False,
                error=report["error"],
                work=dict(
                    direct=active["backend"].work.copy() if active["backend"] is not None else {},
                    additional_B_grid_requests=active["requests"],
                    svd_fits=active["svd"],
                    qr_fits=active["qr"],
                ),
            )
            arrays_path = active["raw"] / "qualification.npz"
            if active["arrays"] and not arrays_path.exists():
                with arrays_path.open("xb") as stream:
                    np.savez_compressed(stream, **active["arrays"])
                row["arrays"] = reference(arrays_path)
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
