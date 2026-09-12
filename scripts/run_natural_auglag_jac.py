"""Separate column-scaled natural-flux AL pilot; no independent-holdout feedback."""

import argparse
import importlib
import inspect
import json
import os
import time
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.jac_scaled_solver import EFFECTIVE_OPTIONS
from fusion_baselines.jac_scaled_solver import jac_scaled_least_squares as least_squares
from fusion_baselines.natural_flux_backend import NaturalFluxBackend
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.spatial_flux import spatial_flux
from fusion_baselines.staged_auglag import solve_stages


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input/code hash mismatch: {path}")
    return path


def analytic_control():
    state, target = {}, np.array([2.0, -1.0])

    def direct(x):
        state["x"] = x.copy()
        z = x - target
        return np.r_[0.5 * z @ z, 1 - x[0], x[1]], np.vstack((z, [-1.0, 0.0], [0.0, 1.0])), {}

    backend = NaturalFluxBackend(
        direct,
        lambda: (state["x"] - target, np.eye(2)),
        lambda: state["x"] - target,
        flux_scale=1.0,
    )
    oracle = InequalityOracle(backend.evaluate, 1033, 2, 2)
    initial, _ = oracle.evaluate([0.0, 0.0])
    stages = []
    reason = solve_stages(
        oracle,
        backend,
        [0.0, 0.0],
        initial,
        minimizer=least_squares,
        stages=stages,
        target_enabled=False,
    )
    last = stages[-1]
    x = np.array([1 - last["selected_values"][1], last["selected_values"][2]])
    return dict(
        x=x.tolist(),
        stages=stages,
        counters=oracle.counters(),
        stop_reason=reason,
        pass_control=bool(
            np.max(np.abs(x - [1, 0])) <= 1e-5
            and last["violation"] <= 1e-8
            and last["lagrangian_gradient_max"] <= 1e-6
        ),
    )


def make_backend(direct):
    def native():
        if not np.array_equal(direct.field.get_points_cart_ref(), direct.points):
            raise ValueError("native field points changed before residual projection")
        return spatial_flux(direct.field.B().reshape(direct.normal.shape), direct.normal)

    return NaturalFluxBackend(
        direct.evaluate,
        lambda: batched_field_jacobian(
            direct.field, direct.global_objective, direct.points, direct.weights
        ),
        native,
    )


def run_arm(direct, ctx, x0, raw, output, repeat):
    raw.mkdir()
    ctx.Jf.x = x0.copy()
    direct.work = dict.fromkeys(direct.work, 0)
    backend = make_backend(direct)
    oracle = InequalityOracle(backend.evaluate, 1033, len(x0), 137, tolerance=1e-8)
    record = dict(
        method="natural-auglag-jac",
        representation="direct",
        repeat=repeat,
        status="running",
        stages=[],
        selection_tolerance=1e-8,
        coordinate_scale=0.01,
        gradient_screen_pass=False,
    )
    started, checkpoint_count = time.monotonic(), 0

    def checkpoint():
        n = len(backend.gn.records)
        record.update(
            counters=oracle.counters(),
            evaluations=oracle.records,
            work=dict(direct.work),
            elapsed_seconds=time.monotonic() - started,
            gn_identity_checks=backend.gn.records,
            gn_work=dict(
                assemblies=n,
                assembly_attempts=backend.gn.spatial_attempts,
                failed_assemblies=backend.gn.spatial_attempts - n,
                native_covector_B_requests=backend.gn.spatial_attempts,
                coil_contractions=16 * n,
                geometry_derivative_requests=32 * n,
                current_VJP_requests=16 * n,
            ),
            residual_compositions=backend.compositions,
        )
        write_json_atomic(output, record)

    def progress():
        nonlocal checkpoint_count
        if len(oracle.records) // 25 > checkpoint_count:
            checkpoint_count = len(oracle.records) // 25
            print(
                f"Jac-scaled natural AL repeat={repeat} stage={len(record['stages'])} "
                f"bundles={len(oracle.records)} best={oracle.best['selection_key']}",
                flush=True,
            )
            checkpoint()

    try:
        initial, jacobian = oracle.evaluate(x0)
        direction = np.random.default_rng(46).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        exact, screens = jacobian @ direction, []
        for eps in (1e-5, 1e-6, 1e-7, 1e-8):
            plus, minus = (
                oracle.evaluate(x0 + eps * direction)[0],
                oracle.evaluate(x0 - eps * direction)[0],
            )
            fd = (plus - minus) / (2 * eps)
            errors = np.abs(fd - exact) / np.maximum(1, np.abs(exact))
            screens.append(
                dict(
                    eps=eps,
                    finite_difference=fd.tolist(),
                    analytic=exact.tolist(),
                    normalized_errors=errors.tolist(),
                )
            )
        record["gradient_checks"] = screens
        record["gradient_screen_pass"] = bool(np.max(screens[-1]["normalized_errors"]) <= 1e-6)
        if not record["gradient_screen_pass"]:
            raise ValueError("initial full physical gradient screen failed")
        reason = solve_stages(
            oracle,
            backend,
            x0,
            initial,
            minimizer=least_squares,
            stages=record["stages"],
            progress=progress,
        )
        record.update(
            status="construction_stopped"
            if reason == "construction_target"
            else "stages_completed",
            stop_reason=reason,
            converged=False,
        )
    except Exception as error:
        record.update(status="error", stop_reason="error", error=f"{type(error).__name__}: {error}")
        if backend.gn.failed_bundle is not None:
            failed = raw / "failed_bundle.npz"
            with failed.open("xb") as stream:
                np.savez_compressed(stream, **backend.gn.failed_bundle)
            field = raw / "failed_field.json"
            ctx.Jf.field.save(str(field))
            record["failed_bundle"] = dict(
                arrays=reference(failed), field=reference(field), metrics=backend.gn.failed_metrics
            )
        raise
    finally:
        if oracle.best is not None:
            best = oracle.best
            ctx.Jf.x = best["x"].copy()
            arrays, field = raw / "best.npz", raw / "best_field.json"
            with arrays.open("xb") as stream:
                np.savez_compressed(stream, x=best["x"], values=best["values"])
            ctx.Jf.field.save(str(field))
            record["best"] = {
                k: best[k]
                for k in (
                    "attempt",
                    "x_sha256",
                    "objective",
                    "maximum_violation",
                    "construction_screen_pass",
                    "selection_key",
                    "metrics",
                )
            }
            record["best"].update(arrays=reference(arrays), field=reference(field))
        checkpoint()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path, nargs="?")
    parser.add_argument("--control-only", action="store_true")
    args = parser.parse_args()
    if args.study.exists() or (args.raw is not None and args.raw.exists()):
        raise FileExistsError("new immutable output paths required")
    root = Path(__file__).resolve().parents[1]
    report = dict(
        schema_version=1,
        repository=git_state(root),
        host=host_state(),
        protocol=reference(root / "docs/optimization/NATURAL_AUGLAG_JAC_PROTOCOL.md"),
        status="running",
        qualification_pass=False,
        methods=["natural-auglag-jac"],
        arms=[],
        flux_scale=1e-6,
        construction_tolerance=1e-8,
        solver_options=EFFECTIVE_OPTIONS,
        code=[
            reference(root / p)
            for p in (
                "scripts/run_natural_auglag_jac.py",
                "src/fusion_baselines/jac_scaled_solver.py",
                "src/fusion_baselines/staged_auglag.py",
                "src/fusion_baselines/natural_auglag.py",
                "src/fusion_baselines/natural_flux_backend.py",
                "src/fusion_baselines/gauss_newton_backend.py",
                "src/fusion_baselines/batched_field_jacobian.py",
                "src/fusion_baselines/inequality_oracle.py",
            )
        ],
        solver_sources=[
            reference(Path(inspect.getfile(importlib.import_module(n))))
            for n in (
                "scipy.optimize._lsq.least_squares",
                "scipy.optimize._lsq.trf",
                "scipy.optimize._lsq.common",
            )
        ],
        thread_environment={
            k: os.environ.get(k)
            for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
    )
    if args.control_only:
        report["analytic_control"] = analytic_control()
        report["status"] = "control_completed"
        report["all_pass"] = report["analytic_control"]["pass_control"]
        write_json_atomic(args.study, report)
        print(json.dumps({"control_pass": report["all_pass"]}))
        return 0 if report["all_pass"] else 2
    if args.raw is None:
        raise ValueError("raw output directory required for physical study")
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    try:
        report["analytic_control"] = analytic_control()
        if not report["analytic_control"]["pass_control"]:
            raise ValueError("analytic constrained solver control failed before physical work")
        qpath = root / "evidence/direct-inequality-qualification-v1.json"
        qualification = json.loads(qpath.read_text())
        gnpath = root / "evidence/gn-trust-native-v1/summary.json"
        gn = json.loads(gnpath.read_text())
        if not qualification["all_pass"] or not gn["qualification_pass"]:
            raise ValueError("qualified direct and native GN backends required")
        for ref in qualification["code"] + qualification["installed_sources"] + gn["code"]:
            checked(ref)
        source = json.loads(checked(qualification["source_study"]).read_text())
        ctx, _, prep = prepare(root, args.raw, guarded_curvature=True)
        if any(
            prep[k] != source["preparation"][k]
            for k in ("thresholds", "degrees_of_freedom", "guarded_search_targets")
        ):
            raise ValueError("original physical setup or named basis changed")
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(prep["surface"])), range="full torus", nphi=64, ntheta=64
        )
        direct, x0 = DirectConstraintBackend(ctx, full), ctx.Jf.x.copy()
        original = next(c for c in qualification["cases"] if c["name"] == "original")
        with np.load(checked(original["arrays"]), allow_pickle=False) as saved:
            permutation = np.argsort(qualification["source_indices_in_target_order"])
            if not np.array_equal(x0, saved["x"][permutation]):
                raise ValueError("qualified original point identity failed")
        report.update(
            preparation=prep,
            qualification=reference(qpath),
            native_gn=reference(gnpath),
            labels=direct.labels,
            qualified_backend_code=qualification["code"],
        )
        runs = []
        for repeat in (1, 2):
            output = args.study / f"natural-auglag-jac-{repeat}.json"
            runs.append(
                run_arm(direct, ctx, x0, args.raw / f"natural-auglag-jac-{repeat}", output, repeat)
            )
            report["arms"].append(reference(output))
            write_json_atomic(args.study / "summary.json", report)
        a, b = runs
        checks = dict(
            gradient_screens=all(r["gradient_screen_pass"] for r in runs),
            same_counters=a["counters"] == b["counters"],
            same_stages=a["stages"] == b["stages"],
            same_stop=a["status"] == b["status"] and a["stop_reason"] == b["stop_reason"],
            identical_complete_histories=len(a["evaluations"]) == len(b["evaluations"])
            and all(
                x["x_sha256"] == y["x_sha256"] and x["values"] == y["values"]
                for x, y in zip(a["evaluations"], b["evaluations"], strict=True)
            ),
            same_best=a["best"]["x_sha256"] == b["best"]["x_sha256"],
            same_work=a["work"] == b["work"] and a["gn_work"] == b["gn_work"],
        )
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
