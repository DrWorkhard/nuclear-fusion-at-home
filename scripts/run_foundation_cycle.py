"""Bounded foundation demonstration: two 24-bundle repeats, not a design search."""

import argparse
import importlib
import inspect
import json
import os
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from current_gn_inputs import qualified_source
from qualify_fixed_currents import native_setup, versions
from run_current_gn_arm import OPTIONS, control, run_arm
from run_jac_scaled_study import require_committed

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/run_foundation_cycle.py",
    "scripts/run_current_start_gn.py",
    "scripts/run_current_gn_arm.py",
    "scripts/current_gn_inputs.py",
    "scripts/geometric_curvature_inputs.py",
    "scripts/qualify_fixed_currents.py",
    "scripts/prepare_upstream_start.py",
    "src/fusion_baselines/direct_constraints.py",
    "src/fusion_baselines/batched_field_jacobian.py",
    "src/fusion_baselines/counted_field_views.py",
    "src/fusion_baselines/gauss_newton_backend.py",
    "src/fusion_baselines/spatial_flux.py",
    "src/fusion_baselines/affine_coordinates.py",
    "src/fusion_baselines/inequality_oracle.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
)


def solver_sources():
    modules = (
        "scipy.optimize._trustregion_constr.minimize_trustregion_constr",
        "scipy.optimize._trustregion_constr.tr_interior_point",
        "scipy.optimize._trustregion_constr.equality_constrained_sqp",
        "scipy.optimize._trustregion_constr.projections",
        "scipy.optimize._hessian_update_strategy",
    )
    return [reference(Path(inspect.getfile(importlib.import_module(name)))) for name in modules]


def repeat_checks(a, b):
    keys = (
        "counters",
        "work",
        "gn_work",
        "physical_points",
        "gn_identity_checks",
        "startup",
        "iterations",
    )
    result = {"same_" + key: a[key] == b[key] for key in keys}
    result.update(
        start_gates=a["gradient_screen_pass"] and b["gradient_screen_pass"],
        same_stop=(a["status"], a["stop_reason"]) == (b["status"], b["stop_reason"]),
        same_best=a["best"]["x_sha256"] == b["best"]["x_sha256"],
        full_history=len(a["evaluations"]) == len(b["evaluations"])
        and all(
            u["x_sha256"] == v["x_sha256"] and u["values"] == v["values"]
            for u, v in zip(a["evaluations"], b["evaluations"], strict=True)
        ),
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable foundation cycle required")
    root = Path(__file__).resolve().parents[1]
    source, qualified, binding = qualified_source(root)
    protocol = root / "docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md"
    for path in [protocol, *(root / p for p in CODE)]:
        require_committed(root, path)
    environment = versions()
    if environment["scipy"] != "1.18.1":
        raise ValueError("registered SciPy1.18.1 required")
    disk = space_check(root, 3 * GIB)
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        host=host_state(),
        versions=environment,
        protocol=reference(protocol),
        source=source,
        qualification=binding,
        code=[reference(root / p) for p in CODE],
        solver_sources=solver_sources(),
        solver_options=OPTIONS,
        bundle_limit=24,
        flux_scale=1e-6,
        construction_tolerance=1e-8,
        methods=["gn-trust"],
        status="preparing",
        qualification_pass=False,
        arms=[],
        scope="foundation smoke; prior search/qualification work retained separately",
        physical_admission=False,
        disk_preflight=disk,
        thread_environment={
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
    )
    try:
        report["analytic_control"] = control()
        if not report["analytic_control"]["all_pass"]:
            raise ValueError("analytic constrained quadratic control failed")
        ctx, prep, full = native_setup(root, args.raw)
        if any(
            prep[key] != source["preparation"][key]
            for key in (
                "surface",
                "case",
                "thresholds",
                "guarded_search_targets",
                "canonical_total",
            )
        ):
            raise ValueError("canonical physical problem changed")
        document = json.loads(checked(source["field"]).read_text())
        template = json.loads(checked(prep["normalized_start"]).read_text())
        x0, permutation, owners = mapped_start(
            document, template, source["names"], prep["degrees_of_freedom"], qualified["points"][0]
        )
        ctx.Jf.x = x0.copy()
        physical = args.raw / "physical_start.json"
        ctx.Jf.field.save(str(physical))
        actual, expected = (
            serialized_state(json.loads(physical.read_text())),
            serialized_state(document),
        )
        if any(not np.array_equal(actual[k], expected[k]) for k in expected):
            raise ValueError("serialized physical start changed")
        backend = DirectConstraintBackend(ctx, full)
        d = qualified["native_matrix"][:, permutation]
        mapped = dict(
            points=qualified["points"][:, permutation],
            values=qualified["values"],
            jacobian=qualified["jacobian"][:, permutation],
            hessian=d.T @ d / 1e-6,
        )
        report.update(
            status="running",
            preparation=prep,
            labels=backend.labels,
            source_indices_in_target_order=permutation.tolist(),
            owner_map=owners,
            physical_start=reference(physical),
        )
        write_json_atomic(args.study / "summary.json", report)
        arms = []
        for repeat in (1, 2):
            space_check(root, 2 * GIB)
            path = args.study / f"gn-trust-{repeat}.json"
            report["active_arm_path"] = str(path.resolve())
            write_json_atomic(args.study / "summary.json", report)
            try:
                result = run_arm(
                    backend, ctx, mapped, args.raw / path.stem, path, repeat, budget=24
                )
            finally:
                if path.exists():
                    report["arms"].append(reference(path))
                write_json_atomic(args.study / "summary.json", report)
            arms.append(result)
        checks = repeat_checks(*arms)
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
        del report["active_arm_path"]
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    print(
        json.dumps(dict(status=report["status"], qualification_pass=report["qualification_pass"]))
    )
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
