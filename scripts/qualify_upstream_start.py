"""Qualify the fixed alternate physical start before any optimizer is run."""

import argparse
import importlib.metadata
import inspect
import json
from pathlib import Path

import numpy as np
from prepare_upstream_start import prepare
from qualify_direct_constraints import errors, metric_crosschecks
from run_natural_auglag_jac import checked, make_backend, reference
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values

CODE = (
    "scripts/qualify_upstream_start.py", "scripts/prepare_upstream_start.py",
    "scripts/qualify_direct_constraints.py", "scripts/qualify_optimization_oracle.py",
    "scripts/run_natural_auglag_jac.py", "scripts/audit_coil_geometry.py",
    "src/fusion_baselines/current_normalization.py", "src/fusion_baselines/direct_constraints.py",
    "src/fusion_baselines/smooth_bounds.py", "src/fusion_baselines/serialized_field_state.py",
    "src/fusion_baselines/serialized_dofs.py", "src/fusion_baselines/spatial_flux.py",
    "src/fusion_baselines/curvature_bounds.py", "src/fusion_baselines/refined_curvature.py",
    "src/fusion_baselines/natural_flux_backend.py", "src/fusion_baselines/gauss_newton_backend.py",
    "src/fusion_baselines/batched_field_jacobian.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable qualification paths required")
    root = Path(__file__).resolve().parents[1]
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root), host=host_state(), status="running", all_pass=False,
        optimization_performed=False, physical_feasibility_certified=False,
        protocol=reference(root / "docs/optimization/UPSTREAM_START_PROTOCOL.md"),
        code=[reference(root / path) for path in CODE],
        versions={n: importlib.metadata.version(n) for n in ("numpy", "scipy", "simsopt")},
    )
    try:
        ctx, prep = prepare(root, args.raw)
        report["preparation"] = prep
        with np.load(checked(prep["source_field_probe"]), allow_pickle=False) as probe:
            points, source_b = probe["points"].copy(), probe["native"].copy()
        expected_points = SurfaceRZFourier.from_vmec_input(
            str(checked(prep["surface"])), range="half period", nphi=8, ntheta=8
        ).gamma().reshape(-1, 3)
        if not np.array_equal(points, expected_points):
            raise ValueError("fixed source probe points changed")
        ctx.Jf.field.set_points(points)
        new_b = ctx.Jf.field.B().copy()
        expected = prep["current_factor"] * source_b
        b_error = float(np.max(np.linalg.norm(new_b - expected, axis=1) /
                               np.maximum(1, np.linalg.norm(expected, axis=1))))
        field_arrays = args.raw / "normalized_field.npz"
        with field_arrays.open("xb") as stream:
            np.savez_compressed(stream, points=points, source_B=source_b, normalized_B=new_b)
        report.update(field_arrays=reference(field_arrays), field_scale_error=b_error)
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(prep["surface"])), range="full torus", nphi=64, ntheta=64
        )
        direct = DirectConstraintBackend(ctx, full)
        backend = make_backend(direct)
        x0 = ctx.Jf.x.copy()
        values, jacobian, metrics = backend.evaluate(x0)
        z, dz = backend.z.copy(), backend.dz.copy()
        native_errors = metric_crosschecks(direct, full, metrics, jacobian)
        checks = {key: bool(value <= 1e-10) for key, value in native_errors.items()}
        checks.update(
            field_scaling=b_error <= 1e-12,
            prepared_identity=all(prep["identity_checks"].values()),
            named_serialized_state=np.array_equal(
                x0, named_serialized_values(
                    json.loads(checked(prep["normalized_start"]).read_text()), direct.names)),
            native_linking_zero=ctx.c_list[7].J() == 0,
            conservative_sampled_extrema=bool(
                all(c["smooth_upper"] >= c["sampled_maximum"] for c in metrics["curvature"])
                and all(c["smooth_squared_lower"] <= c["sampled_squared_minimum"]
                        for c in metrics["coil_clearance"] + metrics["plasma_clearance"])),
        )
        direction = np.random.default_rng(46).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        exact, screens = jacobian @ direction, []
        for eps in (1e-5, 1e-6, 1e-7, 1e-8):
            plus = backend.evaluate(x0 + eps * direction)[0]
            minus = backend.evaluate(x0 - eps * direction)[0]
            fd = (plus - minus) / (2 * eps)
            discrepancy = errors(fd, exact)
            screens.append(dict(
                eps=eps, plus=plus.tolist(), minus=minus.tolist(),
                finite_difference=fd.tolist(), normalized_errors=discrepancy.tolist(),
                maximum_error=float(discrepancy.max()),
                worst_row=direct.labels[int(np.argmax(discrepancy))],
            ))
            print(eps, screens[-1]["maximum_error"], screens[-1]["worst_row"], flush=True)
        checks["all_directional_rows"] = screens[-1]["maximum_error"] <= 1e-6
        ctx.Jf.x = x0.copy()
        arrays = args.raw / "qualification.npz"
        with arrays.open("xb") as stream:
            np.savez_compressed(stream, x=x0, values=values, jacobian=jacobian,
                                direction=direction, z=z, dz=dz)
        sources = {Path(inspect.getfile(type(obj))) for obj in [*direct.native, *direct.fine,
                                                              ctx.Jf, ctx.Jf.field]}
        report.update(
            status="completed", checks={k: bool(v) for k, v in checks.items()},
            all_pass=bool(all(checks.values())), metrics=metrics, native_errors=native_errors,
            labels=direct.labels, arrays=reference(arrays), finite_differences=screens,
            analytic_directional=exact.tolist(), gn_identities=backend.gn.records,
            work=direct.work, spatial_assemblies=backend.gn.spatial_attempts,
            extra_native_work=dict(field_scaling_B=1, raw_flux_J=1, raw_flux_dJ=1,
                                   pair_minima=120, all16_plasma_minimum=1, linking_J=1),
            installed_sources=[reference(p) for p in sorted(sources)],
        )
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"all_pass": report["all_pass"]}))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
